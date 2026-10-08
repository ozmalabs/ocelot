//! Graph-resident rule loader — bridges the Python `gr.make_rule`
//! convention (Rule node with `match` / `where` / `effect` attrs)
//! to the native Rust `RewriteRule` struct + engine in `rewrite.rs`.
//!
//! Per CLAUDE.md: the agent's rule engine moves into Rust. This module
//! is the one-way reader — Python may still construct Rule nodes
//! (during seed installation), but the matcher + applier are now the
//! Rust ones in `rewrite.rs`. `tick()` (exposed on PySubstrate) walks
//! every Rule node currently in the graph, parses each into a
//! RewriteRule against a per-tick arena, and dispatches them via
//! `rewrite::run_rules`.
//!
//! Rule-node shape (Python convention from `domains/graph_rewrite.py`):
//!
//!   Node{ type="Rule" }.attrs:
//!     id:     str                     diagnostic name
//!     match:  list of [str,str,str]   pattern edges (src_var, edge_type,
//!                                     tgt_var). Substrate stores Python
//!                                     lists as Value::Tuple, so we read
//!                                     them back as nested tuples.
//!     where:  dict | None             JSON-encoded Term tree.
//!     effect: list of effect-tuples   each tuple's first element names
//!                                     the op: "add_edge" / "add_node" /
//!                                     "del_edge" / "del_node" / "set_attr".
//!                                     Trailing args may be literals or
//!                                     {"__term__": …} computed Terms.

use crate::graph::{NodeID, TypedGraph};
use crate::jsonio::term_from_json;
use crate::rewrite::{Effect, EffectArg, MatchEdge, RewriteRule};
use crate::substrate::Substrate;
use crate::sym::{Interner, Sym};
use crate::term::TermArena;
use crate::value::Value;
use serde_json::Value as J;

// --- Value → serde_json::Value (only for Term-JSON-shaped values) ---------

pub(crate) fn value_to_json(v: &Value, interner: &Interner) -> J {
    match v {
        Value::None => J::Null,
        Value::Bool(b) => J::Bool(*b),
        Value::Int(n) => J::Number((*n).into()),
        Value::Float(f) => serde_json::Number::from_f64(*f)
            .map(J::Number)
            .unwrap_or(J::Null),
        Value::Str(sym) => J::String(interner.resolve(*sym).to_string()),
        Value::Tuple(items) | Value::List(items) => {
            J::Array(items.iter().map(|x| value_to_json(x, interner)).collect())
        }
        Value::Set(items) | Value::FrozenSet(items) => J::Array(
            items
                .iter()
                .map(|x| value_to_json(x, interner))
                .collect::<Vec<_>>(),
        ),
        Value::Dict(pairs) => {
            let mut obj = serde_json::Map::new();
            for (k, val) in pairs.iter() {
                let key = match k {
                    Value::Str(s) => interner.resolve(*s).to_string(),
                    _ => format!("{:?}", k),
                };
                obj.insert(key, value_to_json(val, interner));
            }
            J::Object(obj)
        }
        // Node / Surface / Rational aren't Term-JSON shapes this Rule-
        // attr reader expects (a rational program value has no reason
        // to appear in a match/where/effect attr); emit Null and let
        // the downstream parser reject the rule cleanly.
        Value::Node(_) | Value::Surface(_, _) | Value::Rational(_, _) => J::Null,
    }
}

// --- helpers --------------------------------------------------------------

/// Read a nested-tuple `Value` as a sequence, treating both Tuple and
/// Set / FrozenSet uniformly. Substrate stores Python lists as Tuple.
fn as_sequence(v: &Value) -> Option<&[Value]> {
    match v {
        Value::Tuple(items) | Value::List(items) => Some(items.as_slice()),
        Value::Set(items) | Value::FrozenSet(items) => Some(&items[..]),
        _ => None,
    }
}

/// Read a string-*shaped* `Value` as `&str` -- accepts both a frozen
/// `Value::Str(Sym)` and a `Value::Surface(SurfaceKind::Text, ...)`
/// (what `StringConcat` and other text-producing Terms evaluate to).
/// Without the Surface arm, a Rule node whose `id` attr was set from a
/// dynamically-concatenated string would silently read back as
/// `<unnamed>` here (see rule_from_node below) even after the mint-queue
/// push itself accepts it -- keep both readers of a Rule-node name in
/// sync.
fn as_str<'a>(v: &'a Value, interner: &'a Interner) -> Option<&'a str> {
    match v {
        Value::Str(s) => Some(interner.resolve(*s)),
        Value::Surface(crate::value::SurfaceKind::Text, bytes) => std::str::from_utf8(bytes).ok(),
        _ => None,
    }
}

fn intern_str(v: &Value, _interner: &mut Interner) -> Option<Sym> {
    if let Value::Str(s) = v {
        Some(*s)
    } else {
        None
    }
}

// --- match-edge parsing ---------------------------------------------------

fn parse_match_edges(v: &Value, interner: &mut Interner) -> Option<Vec<MatchEdge>> {
    let outer = as_sequence(v)?;
    let mut out = Vec::with_capacity(outer.len());
    for triple in outer {
        let parts = as_sequence(triple)?;
        if parts.len() != 3 {
            return None;
        }
        // Var names + edge type all arrive as strings.
        let src_var = intern_str(&parts[0], interner)?;
        let et = intern_str(&parts[1], interner)?;
        let tgt_var = intern_str(&parts[2], interner)?;
        out.push(MatchEdge {
            src_var,
            edge_type: et,
            tgt_var,
        });
    }
    Some(out)
}

// --- where parsing --------------------------------------------------------

fn parse_where(
    v: &Value,
    arena: &mut TermArena,
    interner: &mut Interner,
) -> Option<Option<crate::term::TermIdx>> {
    match v {
        Value::None => Some(None),
        _ => {
            let json = value_to_json(v, interner);
            // The Term-JSON representation is always an Object; if we
            // got Null (e.g. from a Node/Surface that slipped through),
            // treat as no where-clause rather than parse error.
            if matches!(json, J::Null) {
                return Some(None);
            }
            let idx = term_from_json(&json, arena, interner).ok()?;
            Some(Some(idx))
        }
    }
}

// --- effect parsing -------------------------------------------------------

fn parse_effect_arg(
    v: &Value,
    arena: &mut TermArena,
    interner: &mut Interner,
) -> Option<EffectArg> {
    // A `{"__term__": <term_json>}` dict signals a computed Term.
    // Everything else is a literal Value.
    if let Value::Dict(pairs) = v {
        for (k, val) in pairs.iter() {
            if let Value::Str(s) = k {
                if interner.resolve(*s) == "__term__" {
                    let json = value_to_json(val, interner);
                    let idx = term_from_json(&json, arena, interner).ok()?;
                    return Some(EffectArg::Computed(idx));
                }
            }
        }
    }
    Some(EffectArg::Literal(v.clone()))
}

fn parse_attrs_dict(
    v: &Value,
    arena: &mut TermArena,
    interner: &mut Interner,
) -> Option<Vec<(Sym, EffectArg)>> {
    let pairs = match v {
        Value::Dict(pairs) => pairs,
        _ => return None,
    };
    let mut out = Vec::with_capacity(pairs.len());
    for (k, val) in pairs.iter() {
        let key = match k {
            Value::Str(s) => *s,
            _ => return None,
        };
        out.push((key, parse_effect_arg(val, arena, interner)?));
    }
    Some(out)
}

fn parse_effect_op(v: &Value, arena: &mut TermArena, interner: &mut Interner) -> Option<Effect> {
    let parts = as_sequence(v)?;
    if parts.is_empty() {
        return None;
    }
    // We need the op-name string but the interner sees only `&Value`,
    // not the surrounding ownership. Resolve in two steps to keep the
    // borrow tidy.
    let op_sym = match parts[0] {
        Value::Str(s) => s,
        _ => return None,
    };
    let op = interner.resolve(op_sym).to_string();
    match op.as_str() {
        "add_edge" => {
            if parts.len() < 4 {
                return None;
            }
            let src_var = intern_str(&parts[1], interner)?;
            let et = intern_str(&parts[2], interner)?;
            let tgt_var = intern_str(&parts[3], interner)?;
            let attrs = if parts.len() >= 5 {
                parse_attrs_dict(&parts[4], arena, interner)?
            } else {
                Vec::new()
            };
            Some(Effect::AddEdge {
                src_var,
                edge_type: et,
                tgt_var,
                attrs,
            })
        }
        "del_edge" => {
            if parts.len() < 4 {
                return None;
            }
            let src_var = intern_str(&parts[1], interner)?;
            let et = intern_str(&parts[2], interner)?;
            let tgt_var = intern_str(&parts[3], interner)?;
            Some(Effect::DelEdge {
                src_var,
                edge_type: et,
                tgt_var,
            })
        }
        "add_node" => {
            if parts.len() < 4 {
                return None;
            }
            let new_var = intern_str(&parts[1], interner)?;
            let type_ = intern_str(&parts[2], interner)?;
            let attrs = parse_attrs_dict(&parts[3], arena, interner)?;
            Some(Effect::AddNode {
                new_var,
                type_,
                attrs,
            })
        }
        "add_node_if_absent" => {
            // Find-or-create by the author's attrs as a dedup key (subset
            // semantics in apply). Lets a per-cell rule mint exactly ONE node
            // per distinct key value — e.g. one Region per connected-component
            // label — and bind the witness var to it, with no host join.
            if parts.len() < 4 {
                return None;
            }
            let new_var = intern_str(&parts[1], interner)?;
            let type_ = intern_str(&parts[2], interner)?;
            let attrs = parse_attrs_dict(&parts[3], arena, interner)?;
            Some(Effect::AddNodeIfAbsent {
                new_var,
                type_,
                attrs,
            })
        }
        "del_node" => {
            if parts.len() < 2 {
                return None;
            }
            let var = intern_str(&parts[1], interner)?;
            Some(Effect::DelNode { var })
        }
        "set_attr" => {
            if parts.len() < 4 {
                return None;
            }
            let var = intern_str(&parts[1], interner)?;
            let key = intern_str(&parts[2], interner)?;
            let value = parse_effect_arg(&parts[3], arena, interner)?;
            Some(Effect::SetAttr { var, key, value })
        }
        "set_attr_if_different" => {
            if parts.len() < 4 {
                return None;
            }
            let var = intern_str(&parts[1], interner)?;
            let key = intern_str(&parts[2], interner)?;
            let value = parse_effect_arg(&parts[3], arena, interner)?;
            Some(Effect::SetAttrIfDifferent { var, key, value })
        }
        "set_rule_clause" => {
            if parts.len() < 4 {
                return None;
            }
            Some(Effect::SetRuleClause {
                rule_name: parse_effect_arg(&parts[1], arena, interner)?,
                field: parse_effect_arg(&parts[2], arena, interner)?,
                term: parse_effect_arg(&parts[3], arena, interner)?,
            })
        }
        "apply_rule_patch" => {
            if parts.len() < 2 {
                return None;
            }
            Some(Effect::ApplyRulePatch {
                patch_var: intern_str(&parts[1], interner)?,
            })
        }
        // PERCEPTION-AS-ACTION, same wire shape as py.rs's `parse_effect_json`:
        //   ["fb_sample", <fb_id-or-term>, "<game_var>", <grid_w-or-term>, <grid_h-or-term>]
        "fb_sample" => {
            if parts.len() < 5 {
                return None;
            }
            let game_var = intern_str(&parts[2], interner)?;
            Some(Effect::FbSample {
                fb: parse_effect_arg(&parts[1], arena, interner)?,
                game_var,
                grid_w: parse_effect_arg(&parts[3], arena, interner)?,
                grid_h: parse_effect_arg(&parts[4], arena, interner)?,
            })
        }
        // SELF-TRAINING, same wire shape as py.rs's parse_effect_json:
        //   ["net_collapse", "<reflex_net_var>", <input>, <target>, <eta>]
        "net_collapse" => {
            if parts.len() < 5 {
                return None;
            }
            let reflex_net = intern_str(&parts[1], interner)?;
            Some(Effect::NetCollapse {
                reflex_net,
                input: parse_effect_arg(&parts[2], arena, interner)?,
                target: parse_effect_arg(&parts[3], arena, interner)?,
                eta: parse_effect_arg(&parts[4], arena, interner)?,
            })
        }
        _ => None,
    }
}

pub(crate) fn parse_effects(
    v: &Value,
    arena: &mut TermArena,
    interner: &mut Interner,
) -> Option<Vec<Effect>> {
    let ops = as_sequence(v)?;
    let mut out = Vec::with_capacity(ops.len());
    for op in ops {
        out.push(parse_effect_op(op, arena, interner)?);
    }
    Some(out)
}

// --- public API -----------------------------------------------------------

/// Parse one graph-resident Rule node into a native RewriteRule.
/// Returns None if the node is missing the required attrs or any of
/// them are mis-shaped.
pub fn rule_from_node(
    graph: &TypedGraph,
    rule_id: NodeID,
    arena: &mut TermArena,
    interner: &mut Interner,
) -> Option<RewriteRule> {
    if !graph.has_node(rule_id) {
        return None;
    }
    let attrs = &graph.node(rule_id).attrs;
    let id_sym = interner.intern("id");
    let match_sym = interner.intern("match");
    let where_sym = interner.intern("where");
    let effect_sym = interner.intern("effect");

    let name = attrs
        .get(&id_sym)
        .and_then(|v| as_str(v, interner))
        .unwrap_or("<unnamed>")
        .to_string();
    let name_sym = interner.intern(&name);

    let match_v = attrs.get(&match_sym)?.clone();
    let where_v = attrs.get(&where_sym).cloned().unwrap_or(Value::None);
    let effect_v = attrs.get(&effect_sym)?.clone();

    let match_edges = parse_match_edges(&match_v, interner)?;
    let where_ = parse_where(&where_v, arena, interner)?;
    let effects = parse_effects(&effect_v, arena, interner)?;

    // slice (b): optional scheduling and match-driving attrs off the Rule node.
    let batch_sym = interner.intern("batch");
    let match_type_key = interner.intern("match_type");
    let explicit_batch: Option<bool> = match attrs.get(&batch_sym) {
        Some(Value::Bool(b)) => Some(*b),
        Some(Value::Float(f)) => Some(*f != 0.0),
        Some(Value::Int(n)) => Some(*n != 0),
        _ => None,
    };
    let match_type: Option<Sym> = attrs.get(&match_type_key).and_then(|v| {
        if let Value::Str(s) = v {
            Some(*s)
        } else {
            None
        }
    });
    let scope_anchor_var_key = interner.intern("scope_anchor_var");
    let scope_anchor_type_key = interner.intern("scope_anchor_type");
    let scope_anchor_owner_var_key = interner.intern("scope_anchor_owner_var");
    let scope_anchor_owner_type_key = interner.intern("scope_anchor_owner_type");
    let scope_anchor_owner_edge_key = interner.intern("scope_anchor_owner_edge");
    let scope_anchor_field = |key| {
        attrs.get(&key).and_then(|value| match value {
            Value::Str(sym) => Some(*sym),
            _ => None,
        })
    };
    let scope_anchor = match (
        scope_anchor_field(scope_anchor_var_key),
        scope_anchor_field(scope_anchor_type_key),
        scope_anchor_field(scope_anchor_owner_var_key),
        scope_anchor_field(scope_anchor_owner_type_key),
        scope_anchor_field(scope_anchor_owner_edge_key),
    ) {
        (
            Some(anchor_var),
            Some(anchor_type),
            Some(owner_var),
            Some(owner_type),
            Some(owner_edge),
        ) => Some(crate::rewrite::ScopeAnchor {
            anchor_var,
            anchor_type,
            owner_var,
            owner_type,
            owner_edge,
        }),
        _ => None,
    };

    let mut rule = RewriteRule {
        uid: crate::rewrite::RuleUid(
            interner
                .lookup("rule_uid")
                .and_then(|key| attrs.get(&key))
                .and_then(|v| match v {
                    Value::Int(n) if *n > 0 => Some(*n as u64),
                    _ => None,
                })
                .unwrap_or(0),
        ),
        revision: interner
            .lookup("revision")
            .and_then(|key| attrs.get(&key))
            .and_then(|v| match v {
                Value::Int(n) if *n >= 0 => Some(*n as u64),
                _ => None,
            })
            .unwrap_or(0),
        name: name_sym,
        match_edges,
        where_,
        effects,
        match_type,
        scope_anchor,
        ..Default::default()
    };
    rule.derive_access(arena);
    // slice (b) deferred: only an explicit batch attr enables the fast path
    // (auto-enable from batch_safe is off until the cascade-dirtying lands).
    rule.batch = explicit_batch.unwrap_or(false);
    Some(rule)
}

/// Walk every Rule node in the graph, parse each into a RewriteRule
/// (against a fresh per-tick arena so the substrate's permanent arena
/// doesn't accumulate duplicates), and dispatch via `run_rules`.
/// Returns the number of rule applications that progressed the graph
/// before fixed-point was reached.
pub fn run_graph_rules(substrate: &mut Substrate, max_steps: usize) -> usize {
    run_graph_rules_opts(substrate, max_steps, false)
}

/// `run_graph_rules` with opt-in cycle detection threaded down to
/// `rewrite::run_rules_opts`. `detect_cycles = false` is the committed path
/// verbatim. See `TypedGraph::state_fingerprint` for why the honest
/// termination test for a float relaxation is "have I been in this state
/// before" (exact equality, no tolerance) rather than "did it stop moving"
/// (unsatisfiable over arithmetic that dithers at one ULP).
pub fn run_graph_rules_opts(
    substrate: &mut Substrate,
    max_steps: usize,
    detect_cycles: bool,
) -> usize {
    // Per-tick arena keeps the substrate's `terms` clean; the cost is
    // re-parsing every where-clause per tick, which is cheap compared
    // to the matcher itself.
    let mut arena = TermArena::new();

    // Snapshot the Rule node IDs upfront — `rule_from_node` doesn't
    // mutate the graph, but `run_rules` definitely does, and we don't
    // want the rule list to shift mid-tick if a rule's effect happens
    // to add another Rule.
    let rule_type_sym = substrate.interner.intern("Rule");
    let rule_ids: Vec<NodeID> = substrate.graph.nodes_of_type(rule_type_sym);

    let mut rules: Vec<RewriteRule> = Vec::with_capacity(rule_ids.len());
    let mut audit_ids: Vec<u32> = Vec::with_capacity(rule_ids.len());
    for nid in rule_ids {
        if let Some(rule) =
            rule_from_node(&substrate.graph, nid, &mut arena, &mut substrate.interner)
        {
            rules.push(rule);
            // Graph Rule nodes use a separate audit namespace from the
            // substrate's positional RuleIdx values (high-bit tagged NodeID).
            audit_ids.push(0x8000_0000 | (nid.0 & 0x7fff_ffff));
        }
        // Rules that fail to parse are silently skipped — they
        // remain in the graph and can be inspected for diagnostics.
    }

    let rule_refs: Vec<&RewriteRule> = rules.iter().collect();
    let no_jits: Vec<Option<&crate::jit::CompiledWhere>> = vec![None; rule_refs.len()];
    let steps = crate::rewrite::run_rules_opts_with_audit_ids(
        &rule_refs,
        Some(&audit_ids),
        &mut arena,
        &mut substrate.graph,
        &mut substrate.interner,
        Some(&mut substrate.concepts),
        Some(&substrate.framebuffers),
        None,
        &no_jits,
        max_steps,
        detect_cycles,
    );
    // This path runs the free-standing fixpoint runner directly (no
    // access to `&mut Substrate` mid-loop), so an `Effect::FbSample`
    // fired by a graph-resident Rule node only QUEUES here — drain it
    // now that `&mut substrate` is free again, mirroring how
    // `Substrate::run_rules` drains its own queue between passes.
    if !substrate.graph.pending_fb_samples.is_empty() {
        substrate.apply_pending_fb_samples();
    }
    steps
}

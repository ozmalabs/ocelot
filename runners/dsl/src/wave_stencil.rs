//! WAVE STENCIL FAST PATH — the engine's admissible vectorized application of
//! a regular local stencil, block 134000 (`VISION_STENCIL_SIMD_PREREG.md`).
//!
//! CASHES THE SCALE LEVER 133000 NAMED (`VISION_NET_FIELD_PROPOSAL_RESULTS.md`
//! §4): for a KNOWN local rule the scale lever is EXACT VECTORIZATION of the
//! rule the substrate already holds — byte-identical, ~500× the numpy-exact
//! reference vs the per-cell engine relaxation — NOT a net. This module builds
//! that vectorization IN RUST.
//!
//! THE ARCHITECTURE — a SPECIALIST GATED BY Γ-ADMISSIBILITY (CLAUDE.md's
//! "specialist economy"). The RetinaCell STATE field is a radius-1
//! deterministic CA (`wv_propagate` / `wv_refract` / `wv_recover`); a
//! waves-only `s.tick()` mutates ONLY `RetinaCell.state` and
//! `RetinaCell.fired_at` and nothing else (measured,
//! `scripts/_scratch_tick_mutation_probe.py`). `admissible()` recognises that
//! stencil by STRUCTURALLY MATCHING the three rules' `where`/`effect` ASTs
//! against the stencil templates (NOT by rule name, NOT a hardcode) and reads
//! its parameters from the graph. When the rule set is NOT a recognised uniform
//! local stencil (e.g. the learner rules on Unit/Synapse — a Fold over synapses
//! + winner-take-all Argmax), `admissible()` returns None and the caller falls
//! back to the general per-cell engine path.
//!
//! BYTE-IDENTITY (PROTOCOL §9, NON-NEGOTIABLE): `apply()` reproduces the exact
//! `ca_tick` semantics the numpy control (`scripts/_scratch_ca_verify.py`)
//! proved byte-identical to `s.tick()` — a single synchronous pass with the
//! recover-before-propagate ordering. State literals are written as the SAME
//! interned `Value::Str`, `fired_at` as the SAME `Value::Float(step)`, so the
//! graph state is bit-for-bit what the rules produce. The general per-cell path
//! stays DEFAULT and byte-unchanged; this is opt-in.

use crate::graph::NodeID;
use crate::rewrite::{Effect, EffectArg, RuleKey};
use crate::substrate::Substrate;
use crate::sym::Sym;
use crate::term::{TermIdx, TermNode};
use crate::value::Value;

// State codes — the four RetinaCell states, matching `_scratch_ca_verify.py`.
const REST: u8 = 0;
const ACT: u8 = 1;
const REC: u8 = 2;
const REF: u8 = 3;

/// A recognised stencil program: the parameters the vectorized kernel needs,
/// all READ from the graph / matched AST. `wave_rule_idxs` are the three rules
/// the fast path replaces (deactivated while the "rest" runs, so they are not
/// re-enumerated).
pub struct StencilProgram {
    // interned keys / states, resolved once
    k_state: Sym,
    k_activated_at: Sym,
    k_fired_at: Sym,
    s_rested: Sym,
    s_active: Sym,
    s_recruited: Sym,
    s_refractory: Sym,
    neighbour_et: Sym,
    // parameters read from the graph
    step: f64,
    refractory_steps: f64,
    propagate: bool,
    retina_step_key: Sym,
    // the three wave rules (indices into `sub.rules`)
    pub wave_rule_idxs: Vec<usize>,
}

// ---- small AST accessors (structural, over the substrate's term arena) ----

/// `Attr { node: Var{name}, key }` → `Some((var_name, key))`.
fn as_var_attr(sub: &Substrate, idx: TermIdx) -> Option<(Sym, Sym)> {
    if let TermNode::Attr { node, key } = sub.terms.get(idx) {
        if let TermNode::Var { name } = sub.terms.get(*node) {
            return Some((*name, *key));
        }
    }
    None
}

/// `Attr { node: PickUnique{ NodesOfType(params_type) }, key }` → `Some(key)`.
fn as_singleton_param(sub: &Substrate, idx: TermIdx, params_type: Sym) -> Option<Sym> {
    if let TermNode::Attr { node, key } = sub.terms.get(idx) {
        if let TermNode::PickUnique { source } = sub.terms.get(*node) {
            if let TermNode::NodesOfType { node_type } = sub.terms.get(*source) {
                if *node_type == params_type {
                    return Some(*key);
                }
            }
        }
    }
    None
}

fn as_lit_str(sub: &Substrate, idx: TermIdx) -> Option<Sym> {
    if let TermNode::Lit { value: Value::Str(s) } = sub.terms.get(idx) {
        Some(*s)
    } else {
        None
    }
}

fn and_items(sub: &Substrate, idx: TermIdx) -> Option<Vec<TermIdx>> {
    if let TermNode::And { items } = sub.terms.get(idx) {
        Some(items.clone())
    } else {
        None
    }
}

/// The `SetAttr` effects of a rule, as `(var, key, EffectArg)`.
fn set_attr_effects(rule: &crate::rewrite::RewriteRule) -> Vec<(Sym, Sym, &EffectArg)> {
    rule.effects
        .iter()
        .filter_map(|e| match e {
            Effect::SetAttr { var, key, value } => Some((*var, *key, value)),
            _ => None,
        })
        .collect()
}

/// True iff this rule's ONLY effects are `SetAttr`s (a pure attribute stencil).
fn only_set_attrs(rule: &crate::rewrite::RewriteRule) -> bool {
    !rule.effects.is_empty()
        && rule
            .effects
            .iter()
            .all(|e| matches!(e, Effect::SetAttr { .. }))
}

/// The literal `Sym` a `SetAttr(var, key, Literal(Str))` writes, if that is
/// the shape.
fn set_state_literal(
    rule: &crate::rewrite::RewriteRule,
    k_state: Sym,
) -> Option<Sym> {
    for (_, key, val) in set_attr_effects(rule) {
        if key == k_state {
            if let EffectArg::Literal(Value::Str(s)) = val {
                return Some(*s);
            }
            // Computed state write — not a recognised stencil.
            return None;
        }
    }
    None
}

// ---- the admissibility gate ----------------------------------------------

/// Recognise the RetinaCell state-CA stencil. Returns the program if the three
/// canonical stencil rules are present in canonical structural form AND no
/// OTHER active rule reads or writes the CA's outputs (`state`/`fired_at`) — so
/// the vectorized pass cannot enable or race any non-stencil rule. Otherwise
/// None (⇒ the caller uses the general per-cell path).
pub fn admissible(sub: &Substrate, strict: bool) -> Option<StencilProgram> {
    let lk = |s: &str| sub.interner.lookup(s);
    // Every symbol the stencil needs. `lookup` (never intern — a gate must not
    // mutate the interner). If a name was never interned, no such rule/attr
    // exists, so the stencil is trivially not present.
    let t_cell = lk("RetinaCell")?;
    let t_params = lk("WaveParams")?;
    let t_retina = lk("Retina")?;
    let k_state = lk("state")?;
    let k_activated_at = lk("activated_at")?;
    let k_fired_at = lk("fired_at")?;
    let k_step = lk("step")?;
    let s_rested = lk("rested")?;
    let s_active = lk("active")?;
    let s_recruited = lk("recruited")?;
    let s_refractory = lk("refractory")?;

    // Exactly one WaveParams (PickUnique semantics) and exactly one Retina.
    let params: Vec<NodeID> = sub.graph.nodes_of_type(t_params);
    if params.len() != 1 {
        return None;
    }
    let retinas: Vec<NodeID> = sub.graph.nodes_of_type(t_retina);
    if retinas.len() != 1 {
        return None;
    }
    // Must actually have a field to update.
    if sub.graph.nodes_of_type(t_cell).is_empty() {
        return None;
    }

    // Classify the ACTIVE RetinaCell rules by structure. Each of the three must
    // appear exactly once; any other RetinaCell-typed active rule that WRITES
    // state/fired_at would be an unrecognised state dynamic ⇒ inadmissible.
    let mut idx_propagate: Option<usize> = None;
    let mut idx_refract: Option<usize> = None;
    let mut idx_recover: Option<usize> = None;
    let mut neighbour_et: Option<Sym> = None;

    for (ri, rule) in sub.rules.iter().enumerate() {
        if !rule.active || rule.match_type != Some(t_cell) {
            continue;
        }
        // Only pure-SetAttr rules can be stencil rules. A RetinaCell rule with
        // a non-SetAttr effect that writes state is unrecognised ⇒ reject.
        let writes_state_or_fired = rule.write_set.contains(&RuleKey::Attr(k_state))
            || rule.write_set.contains(&RuleKey::Attr(k_fired_at));
        if !writes_state_or_fired {
            // ch_* drive rules etc. — they write neither state nor fired_at,
            // so they are NOT part of the state dynamics. Left to the general
            // pass (they cannot read the CA's outputs — checked below).
            continue;
        }
        if !only_set_attrs(rule) {
            return None; // writes state via a non-SetAttr effect: unrecognised
        }
        let Some(state_lit) = set_state_literal(rule, k_state) else {
            // writes fired_at but not a literal state (or a computed state) —
            // does not fit any template.
            if set_attr_effects(rule).iter().any(|(_, k, _)| *k == k_state) {
                return None;
            }
            return None;
        };
        let Some(where_idx) = rule.where_ else { return None };
        let Some(conj) = and_items(sub, where_idx) else { return None };

        if state_lit == s_refractory {
            // wv_refract: And[ Eq(Attr(c,state), "active"),
            //                  Lt(Attr(c,activated_at), Attr(r,step)) ]
            //   effects: SetAttr(c,state,"refractory"), SetAttr(c,fired_at,Attr(r,step))
            if !where_has_eq_attr_lit(sub, &conj, k_state, s_active) {
                return None;
            }
            if !where_has_lt_attr_attr(sub, &conj, k_activated_at, k_step) {
                return None;
            }
            // fired_at effect must be a Computed Attr(_, step)
            let ok_fired = set_attr_effects(rule).iter().any(|(_, k, v)| {
                *k == k_fired_at
                    && matches!(v, EffectArg::Computed(t)
                        if as_var_attr(sub, *t).map(|(_, kk)| kk) == Some(k_step))
            });
            if !ok_fired {
                return None;
            }
            if idx_refract.replace(ri).is_some() {
                return None; // two refract-shaped rules: ambiguous
            }
        } else if state_lit == s_rested {
            // wv_recover: And[ Eq(Attr(c,state),"refractory"),
            //   Gte(Minus(Attr(r,step),Attr(c,fired_at)), Param(refractory_steps)) ]
            if !where_has_eq_attr_lit(sub, &conj, k_state, s_refractory) {
                return None;
            }
            if !where_has_recover_gte(sub, &conj, k_step, k_fired_at, t_params) {
                return None;
            }
            if idx_recover.replace(ri).is_some() {
                return None;
            }
        } else if state_lit == s_recruited {
            // wv_propagate: And[ Eq(Attr(c,state),"active"),
            //   Eq(Attr(c,activated_at),Attr(r,step)), Eq(Attr(n,state),"rested"),
            //   Gt(Param(propagate), 0.5) ]  + match-edge [c neighbour n]
            if !where_has_eq_attr_lit(sub, &conj, k_state, s_active) {
                return None;
            }
            if !where_has_eq_attr_lit(sub, &conj, k_state, s_rested) {
                return None;
            }
            if !where_has_eq_attr_attr(sub, &conj, k_activated_at, k_step) {
                return None;
            }
            if !where_has_param_guard(sub, &conj, t_params) {
                return None;
            }
            // the neighbour edge type carrying the radius-1 stencil
            let net = rule
                .match_edges
                .iter()
                .find(|me| me.edge_type != lk("has_cell").unwrap_or(Sym(u32::MAX)))
                .map(|me| me.edge_type)?;
            neighbour_et = Some(net);
            if idx_propagate.replace(ri).is_some() {
                return None;
            }
        } else {
            // writes state to some OTHER literal: unrecognised dynamic.
            return None;
        }
    }

    let (Some(ip), Some(irf), Some(irc)) = (idx_propagate, idx_refract, idx_recover) else {
        return None;
    };
    let neighbour_et = neighbour_et?;
    let wave_rule_idxs = vec![ip, irf, irc];

    // SAFETY CONDITION (b): no OTHER active rule may READ or WRITE the CA's
    // outputs. Then the vectorized pass cannot enable, race, or be raced by any
    // non-stencil rule — so applying the CA before running the rest is exact
    // regardless of interleaving (the rest is independent of what the CA
    // touches). This is the structural certificate the fast path rests on.
    for (ri, rule) in sub.rules.iter().enumerate() {
        if !rule.active || wave_rule_idxs.contains(&ri) {
            continue;
        }
        for k in [k_state, k_fired_at] {
            if rule.read_set.contains(&RuleKey::Attr(k))
                || rule.write_set.contains(&RuleKey::Attr(k))
            {
                return None;
            }
        }
    }

    // STRICT admissibility (for the BARE mode, `run_rest = false`, which SKIPS
    // the general pass entirely): the stencil must be the WHOLE tick dynamics.
    // Condition (b) already proves no non-stencil rule reads/writes the field;
    // strict mode additionally refuses when the learner subgraph is present
    // (Unit/Synapse), whose rules DO fire and mutate during a tick — skipping
    // them would diverge. With learners present the caller must use `run_rest =
    // true`, which runs those rules untouched (byte-identical, measured). This
    // is the structural boundary that makes BARE mode safe: a field-only graph
    // gets the bare specialist; a learner-laden graph is refused it.
    if strict {
        for tname in ["Unit", "Synapse"] {
            if let Some(t) = sub.interner.lookup(tname) {
                if !sub.graph.nodes_of_type(t).is_empty() {
                    return None;
                }
            }
        }
    }

    // Parameters, read from the graph (the SAME source the rules read via
    // PickUnique(NodesOfType(WaveParams))).
    let pnode = params[0];
    let refractory_steps = attr_f64(sub, pnode, lk("refractory_steps")?)?;
    let propagate = attr_f64(sub, pnode, lk("propagate")?).unwrap_or(0.0) > 0.5;
    let step = attr_f64(sub, retinas[0], k_step)?;

    Some(StencilProgram {
        k_state,
        k_activated_at,
        k_fired_at,
        s_rested,
        s_active,
        s_recruited,
        s_refractory,
        neighbour_et,
        step,
        refractory_steps,
        propagate,
        retina_step_key: k_step,
        wave_rule_idxs,
    })
}

fn attr_f64(sub: &Substrate, nid: NodeID, key: Sym) -> Option<f64> {
    sub.graph.node(nid).attrs.get(&key).map(|v| v.as_f64())
}

// where-clause conjunct predicates (order-insensitive; match ANY conjunct)

fn where_has_eq_attr_lit(sub: &Substrate, conj: &[TermIdx], key: Sym, lit: Sym) -> bool {
    conj.iter().any(|&c| {
        if let TermNode::Eq { a, b } = sub.terms.get(c) {
            let (av, bv) = (as_var_attr(sub, *a), as_lit_str(sub, *b));
            if av.map(|(_, k)| k) == Some(key) && bv == Some(lit) {
                return true;
            }
            // symmetric
            let (av2, bv2) = (as_var_attr(sub, *b), as_lit_str(sub, *a));
            if av2.map(|(_, k)| k) == Some(key) && bv2 == Some(lit) {
                return true;
            }
        }
        false
    })
}

fn where_has_eq_attr_attr(sub: &Substrate, conj: &[TermIdx], key_a: Sym, key_b: Sym) -> bool {
    conj.iter().any(|&c| {
        if let TermNode::Eq { a, b } = sub.terms.get(c) {
            let ka = as_var_attr(sub, *a).map(|(_, k)| k);
            let kb = as_var_attr(sub, *b).map(|(_, k)| k);
            return (ka == Some(key_a) && kb == Some(key_b))
                || (ka == Some(key_b) && kb == Some(key_a));
        }
        false
    })
}

fn where_has_lt_attr_attr(sub: &Substrate, conj: &[TermIdx], key_a: Sym, key_b: Sym) -> bool {
    conj.iter().any(|&c| {
        if let TermNode::Lt { a, b } = sub.terms.get(c) {
            return as_var_attr(sub, *a).map(|(_, k)| k) == Some(key_a)
                && as_var_attr(sub, *b).map(|(_, k)| k) == Some(key_b);
        }
        false
    })
}

/// `Gte(Minus(Attr(_,step), Attr(_,fired_at)), Param(WaveParams,_))`.
fn where_has_recover_gte(
    sub: &Substrate,
    conj: &[TermIdx],
    k_step: Sym,
    k_fired: Sym,
    t_params: Sym,
) -> bool {
    conj.iter().any(|&c| {
        if let TermNode::Gte { a, b } = sub.terms.get(c) {
            if let TermNode::Minus { a: ma, b: mb } = sub.terms.get(*a) {
                let step_ok = as_var_attr(sub, *ma).map(|(_, k)| k) == Some(k_step);
                let fired_ok = as_var_attr(sub, *mb).map(|(_, k)| k) == Some(k_fired);
                let param_ok = as_singleton_param(sub, *b, t_params).is_some();
                return step_ok && fired_ok && param_ok;
            }
        }
        false
    })
}

/// A `Gt(Param(WaveParams,_), Lit)` or `Gt(Lit, Param)` propagate guard.
fn where_has_param_guard(sub: &Substrate, conj: &[TermIdx], t_params: Sym) -> bool {
    conj.iter().any(|&c| {
        if let TermNode::Gt { a, b } = sub.terms.get(c) {
            return as_singleton_param(sub, *a, t_params).is_some()
                || as_singleton_param(sub, *b, t_params).is_some();
        }
        false
    })
}

// ---- the vectorized kernel ------------------------------------------------

/// Apply ONE wave relaxation to the WHOLE field in a single synchronous pass
/// over contiguous arrays — the exact `ca_tick` the numpy control proved
/// byte-identical to `s.tick()`. Writes `state`/`fired_at` back only where they
/// change, as the SAME `Value` the rules write.
pub fn apply(sub: &mut Substrate, prog: &StencilProgram) {
    let t_cell = sub.interner.lookup("RetinaCell").expect("RetinaCell interned");
    let cells: Vec<NodeID> = sub.graph.nodes_of_type(t_cell);
    let n = cells.len();
    if n == 0 {
        return;
    }
    // dense index by node-id slot
    let max_slot = cells.iter().map(|c| c.0).max().unwrap_or(0) as usize;
    let mut pos: Vec<u32> = vec![u32::MAX; max_slot + 1];
    for (i, c) in cells.iter().enumerate() {
        pos[c.0 as usize] = i as u32;
    }

    // GATHER — contiguous SoA arrays.
    let mut state = vec![REST; n];
    let mut activated = vec![0.0f64; n];
    let mut fired = vec![0.0f64; n];
    for (i, c) in cells.iter().enumerate() {
        let at = &sub.graph.node(*c).attrs;
        if let Some(Value::Str(s)) = at.get(&prog.k_state) {
            state[i] = if *s == prog.s_active {
                ACT
            } else if *s == prog.s_refractory {
                REF
            } else if *s == prog.s_recruited {
                REC
            } else {
                REST
            };
        }
        activated[i] = at.get(&prog.k_activated_at).map(|v| v.as_f64()).unwrap_or(0.0);
        fired[i] = at.get(&prog.k_fired_at).map(|v| v.as_f64()).unwrap_or(0.0);
    }

    let step = prog.step;
    let refr = prog.refractory_steps;

    // fresh-active mask (from the ORIGINAL state) — the propagation sources.
    let mut fresh = vec![false; n];
    for i in 0..n {
        fresh[i] = state[i] == ACT && activated[i] == step;
    }

    // COMPUTE — refract (old actives) / recover (aged refractories). Disjoint
    // sets, so a single pass with the else-if is order-free (matches ca_tick).
    let mut nstate = state.clone();
    let mut nfired = fired.clone();
    for i in 0..n {
        if state[i] == ACT && activated[i] < step {
            nstate[i] = REF;
            nfired[i] = step;
        } else if state[i] == REF && (step - fired[i]) >= refr {
            nstate[i] = REST;
        }
    }

    // PROPAGATE — a fresh-active cell recruits its RESTED-NOW neighbours
    // (rested after refract/recover). Gated by `propagate` (the noise arm sets
    // it 0 ⇒ no recruitment, exactly like the rule's guard).
    if prog.propagate {
        let mut recruit = vec![false; n];
        for i in 0..n {
            if !fresh[i] {
                continue;
            }
            for nb in sub.graph.neighbours(cells[i], Some(prog.neighbour_et)) {
                let slot = nb.0 as usize;
                if slot < pos.len() {
                    let j = pos[slot];
                    if j != u32::MAX && nstate[j as usize] == REST {
                        recruit[j as usize] = true;
                    }
                }
            }
        }
        for j in 0..n {
            if recruit[j] {
                nstate[j] = REC;
            }
        }
    }

    // SCATTER — write back only the cells that changed, as the SAME Value the
    // rules write (interned Str for state, Float(step) for fired_at).
    let sym_for = |s: u8| match s {
        ACT => prog.s_active,
        REF => prog.s_refractory,
        REC => prog.s_recruited,
        _ => prog.s_rested,
    };
    let _ = prog.retina_step_key; // (documented: step read from Retina)
    for i in 0..n {
        if nstate[i] != state[i] {
            sub.set_attr(cells[i], prog.k_state, Value::Str(sym_for(nstate[i])));
        }
        if nfired[i] != fired[i] {
            sub.set_attr(cells[i], prog.k_fired_at, Value::Float(nfired[i]));
        }
    }
}

// ---- orchestration --------------------------------------------------------

/// The engine's admissible stencil tick. Returns true iff the fast path was
/// admissible and applied (⇒ the caller must NOT also run the general tick);
/// false iff inadmissible (⇒ the caller falls back to `tick`).
///
/// `run_rest = true` (default, SAFE): after the vectorized stencil, run the
/// general rule stores with the three wave rules deactivated, so every NON-wave
/// rule fires exactly as it would in `tick()`. The admissibility gate has
/// certified no non-wave rule reads/writes the CA's outputs, so this is
/// byte-identical to the interleaved fixpoint regardless of order.
///
/// `run_rest = false`: apply ONLY the stencil. Byte-identical whenever the
/// non-wave rules are quiescent during the tick (the measured waves-only case);
/// the safety certificate above guarantees the CA cannot make them non-quiescent.
pub fn stencil_tick(sub: &mut Substrate, max_steps: usize, run_rest: bool) -> bool {
    // BARE mode (run_rest = false) demands STRICT admissibility — the stencil
    // is the whole tick, so no learner subgraph may be present.
    let Some(prog) = admissible(sub, !run_rest) else {
        return false;
    };
    apply(sub, &prog);
    if run_rest {
        // Deactivate the three wave rules so the general pass does not
        // re-enumerate them (their fixpoint is already applied); restore after.
        let idxs = prog.wave_rule_idxs.clone();
        for &ri in &idxs {
            sub.rules[ri].active = false;
        }
        let steps = crate::graph_rules::run_graph_rules_opts(sub, max_steps, false);
        let remaining = max_steps.saturating_sub(steps);
        if remaining > 0 {
            sub.run_rules_opts(remaining, false);
        }
        for &ri in &idxs {
            sub.rules[ri].active = true;
        }
    }
    true
}

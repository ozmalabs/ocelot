//! Graph-resident rewrite rules — Phase 7c.
//!
//! The existing `domains/graph_rewrite.py` lives outside the engine: an
//! agent that "applies a rule" has to call Python machinery, and the
//! rules themselves aren't visible to the substrate as mutable graph
//! data. This module lifts the core — rule struct, backtracking
//! subgraph matcher, applier with undo for backtracking search,
//! fixed-point runner — into Rust so the substrate can hold rules
//! first-class and run them at native speed.
//!
//! Per the paper's Axiom 3 + the user's "Π is the only mutation
//! surface" principle, rewrite operations *could* flow through Π / C
//! for admissibility gating. The Python version bypasses this (rules
//! are "presumed admissible by construction"); we match that posture
//! here so existing rule sets work unmodified. A `gated: bool` flag on
//! `apply_rule` is reserved for future opt-in admissibility checks.

use crate::graph::{EdgeKey, NodeID, TypedGraph};
use crate::sym::{Interner, Sym};
use crate::term::{evaluate, ConceptResolver, Env, EvalCtx, TermArena, TermIdx};
use crate::value::{SurfaceKind, Value};
use rayon::prelude::*;
use rustc_hash::FxHashMap;
use smallvec::SmallVec;

/// One match-edge constraint in a rule's pattern: "there is an edge
/// of type `edge_type` from the node bound to `src_var` to the node
/// bound to `tgt_var`." A rule's pattern is a list of these joined by
/// implicit conjunction.
#[derive(Clone, Debug)]
pub struct MatchEdge {
    pub src_var: Sym,
    pub edge_type: Sym,
    pub tgt_var: Sym,
}

/// R10 (join-index wave, docs/comprehension_decision_ledger.md Wave 3):
/// a DECLARATIVE hint that a match-edge var (`for_var`) can be candidate-
/// pruned via a declared attribute index instead of the matcher's default
/// both-unbound full-`edges_by_type` scan.
///
/// Motivating shape: two match-edges with NO shared variable (e.g.
/// `(agent, knows_concept, c)` and `(m, has_mention, mention)`), joined only
/// by a `where`-clause `Eq(Attr(mention,"text"), Attr(c,"name"))`. The
/// matcher has no way to see that where-clause connection — it treats the
/// two edges as an unrestricted cartesian product (O(concepts × mentions)),
/// filtering the where-clause only AFTER the full product is enumerated.
/// This is `rule_mention_resolves_to_concept`'s measured cost (Wave 3:
/// ~36ms of a 39ms rule budget, growing with conversation length).
///
/// `IndexJoinHint { for_var: "c", probe: BoundAttr { via_var: "mention",
/// via_key: "text" }, node_type: "Concept", this_key: "name" }` tells the
/// matcher to look up `for_var`'s candidates through the declared index once
/// the dynamic `via_var` probe is bound. `Literal(value)` probes are ready
/// immediately. For either probe, when an attr index is declared on
/// `(node_type, this_key)`, look up `for_var`'s candidates via
/// `graph.nodes_where(node_type, this_key, <probe value>)`
/// instead of scanning every edge of `for_var`'s match-edge type. If the
/// source is already bound, indexed target hits are checked using direct
/// edge lookup; the index still prunes the neighbor list without weakening
/// the graph-edge correctness check.
///
/// CORRECTNESS: the index is maintained by TypedGraph and is back-filled on
/// declaration; each hit is checked against the requested attr value and
/// real graph edge before matching. An absent index falls back to adjacency.
/// Completeness relies on TypedGraph's index-maintenance invariant. Keyed by variable
/// NAME (not match-edge position), so it survives `reorder_match_edges`
/// unchanged and is authoring-order-independent.
#[derive(Clone, Debug, PartialEq, Eq, Hash)]
pub struct IndexJoinHint {
    /// The match-edge variable this hint accelerates (must be the src_var
    /// or tgt_var of exactly one of the rule's match_edges).
    pub for_var: Sym,
/// Source of the exact value to probe in the declared attribute index.
    pub probe: IndexProbe,
    /// The node type `for_var` ranges over — must match the type the
    /// attr index is declared against.
    pub node_type: Sym,
    /// The attr key on `for_var`'s nodes the index is declared on.
    pub this_key: Sym,
}

/// Value source for an indexed join hint. Literal probes let the matcher
/// apply an exact positive equality already present in a rule's `where`
/// clause before constructing broad match-edge products.
#[derive(Clone, Debug, PartialEq, Eq, Hash)]
pub enum IndexProbe {
    BoundAttr { via_var: Sym, via_key: Sym },
    LiteralString(Sym),
}

/// An effect argument — either a literal stored at rule-construction
/// time, or a Term that gets evaluated under the current match
/// binding when the rule fires. Mirrors the Python encoding where a
/// `{"__term__": …}` dict signals a computed argument.
#[derive(Clone, Debug)]
pub enum EffectArg {
    Literal(Value),
    Computed(TermIdx),
}

/// One mutation in a rule's effect list. Variables refer to names
/// bound by the match (the `match_edges` patterns) or — for
/// `AddNode` — to a fresh `new_var` whose binding the effect itself
/// produces, available to subsequent effects in the same rule.
#[derive(Clone, Debug)]
pub enum Effect {
    AddEdge {
        src_var: Sym,
        edge_type: Sym,
        tgt_var: Sym,
        attrs: Vec<(Sym, EffectArg)>,
    },
    DelEdge {
        src_var: Sym,
        edge_type: Sym,
        tgt_var: Sym,
    },
    AddNode {
        new_var: Sym,
        type_: Sym,
        attrs: Vec<(Sym, EffectArg)>,
    },
    /// Like `AddNode`, but skip insertion when an existing node already
    /// has the same TYPE and the same (key, value) attrs for every key
    /// in `attrs`. Closes the surveyed "AddNode re-fires forever"
    /// limit — a rule whose match is satisfied each tick but whose
    /// effect should emit a witness node only once was forced to wire
    /// in a guard rule or to mint a unique sentinel attr; now the
    /// effect itself dedupes.
    ///
    /// Semantics:
    ///   - Resolve every effect arg under the binding (same path as
    ///     `AddNode`) so the comparison sees concrete `Value`s, not
    ///     unresolved Terms.
    ///   - Scan all nodes of `type_`. A node MATCHES iff for each
    ///     `(k, v)` in the resolved attrs the node's `attrs.get(k)`
    ///     equals `Some(&v)`. The node may carry ADDITIONAL attrs;
    ///     they don't break the match (an `AddNodeIfAbsent` author
    ///     specifies the dedup key set explicitly via the attrs they
    ///     pass).
    ///   - If a match exists: bind `new_var` to the FIRST match's
    ///     NodeID (so subsequent effects in the rule can still refer
    ///     to the witness), record no progress, emit no UndoStep.
    ///   - Otherwise: insert exactly like `AddNode` and record
    ///     progress + `UndoStep::AddedNode`.
    AddNodeIfAbsent {
        new_var: Sym,
        type_: Sym,
        attrs: Vec<(Sym, EffectArg)>,
    },
    DelNode {
        var: Sym,
    },
    SetAttr {
        var: Sym,
        key: Sym,
        value: EffectArg,
    },
    /// Like `SetAttr`, but skip when the node's current attr value
    /// already equals the resolved new value. Closes the surveyed
    /// "SetAttr re-applies forever" limit at the EFFECT layer rather
    /// than the binding layer: a rule whose match would re-fire each
    /// tick now records no progress AND skips the write so any UndoStep
    /// or hook accounting that downstream code attaches to attr writes
    /// doesn't get triggered for no-ops either.
    ///
    /// `apply_rule_full` already records no-progress when a plain
    /// `SetAttr` lands the same value (the value-equality check before
    /// the `progressed = true` line), but the write still happens —
    /// here we elide the write entirely. Use this when the same
    /// rule's OTHER effects would mistakenly count the SetAttr as a
    /// reason to fire (e.g. paired with a progressing `AddEdge` that's
    /// already a duplicate).
    SetAttrIfDifferent {
        var: Sym,
        key: Sym,
        value: EffectArg,
    },
    /// Replace every incoming edge to `old_var` with one to `new_var`,
    /// preserving edge_type and attrs. The use-rewiring primitive that
    /// LLVM-style transformation passes depend on: "every use of
    /// OldValue is now a use of NewValue." Iterates `in_edges_slice`,
    /// deletes each incoming edge to old, inserts a parallel edge to
    /// new. Records DeletedEdge + AddedEdge undo steps. No-op if
    /// old_var == new_var.
    ReplaceValue {
        old_var: Sym,
        new_var: Sym,
    },
    /// Register a Term-tree as the body of a named concept, mirroring
    /// `Substrate::define_concept(name, term)`. Lets a rule install the
    /// concept its match implies (e.g. observe a pattern, define a
    /// `Holds(concept_name, x)` recursion that resolves to that
    /// pattern's Term).
    ///
    /// `name` is an `EffectArg` so the concept's name can either be a
    /// rule-time literal (`Value::Str(Sym)`) or computed from the match
    /// binding (a Term that evaluates to a `Value::Str`).
    ///
    /// `term` is also an `EffectArg`. Both arms resolve to a
    /// `Value::Dict` shaped like a Term-JSON object (the wire format
    /// `term_from_json` consumes); the applier parses that Value into
    /// a fresh `TermIdx` in the substrate's main `TermArena` at fire
    /// time and registers it.
    ///   - `Literal(Value::Dict(...))` — the term-tree was given at
    ///     rule-construction time (the original path; emitted by
    ///     `parse_effect_json` when the third arg is a plain Term-JSON
    ///     object).
    ///   - `Computed(idx)` — a Term that evaluates to a Dict-shaped
    ///     Value (Term-JSON), letting a rule synthesise the registered
    ///     term-tree from its match binding. Requires the DSL to be
    ///     able to construct that Dict at fire time; if a primitive
    ///     for that doesn't yet exist, rules can still hand-author
    ///     the term via the Literal path.
    ///
    /// The new (name, term) pair is collected on `ApplyOutcome` and
    /// installed into `Substrate::concepts` by the caller after the
    /// rule's effects finish — keeps the borrow of `&ConceptResolver`
    /// (read by `evaluate` / `Holds`) and the eventual write to the
    /// same map cleanly separated.
    DefineConcept {
        name: EffectArg,
        term: EffectArg,
    },
    /// INTRINSIC SELF-REPAIR: rewrite a (struct) rule's `where` or `effect`
    /// clause — a rule editing a rule, from inside the live `run_rules` loop.
    /// `rule_name` resolves to a `Value::Str` naming the target rule; `field`
    /// resolves to `Value::Str` ("where" | "effect"); `term` resolves to a
    /// `Value::Dict`/`Value::Tuple` shaped like the wire JSON for that clause
    /// (a Term tree for "where", an effect list for "effect"). The applier only
    /// holds `&mut graph`, so it QUEUES `(name, field, term_value)` on
    /// `graph.pending_rule_edits`; `Substrate::run_rules` drains + applies it
    /// between passes (swap in place + `derive_access` + invalidate JIT/cursor +
    /// mark dirty), so the rewritten rule runs its new body next pass.
    SetRuleClause {
        rule_name: EffectArg,
        field: EffectArg,
        term: EffectArg,
    },
    /// Transactional self-modification. `patch_var` names a match binding
    /// holding a graph-resident `RulePatch` node. The node carries the stable
    /// target identity and CAS preconditions (`target_uid`,
    /// `expected_revision`, `expected_content_hash`) plus `field` and
    /// `proposed_clause`. The effect only queues the node id; `Substrate`
    /// stages, validates and atomically commits it between rule passes, then
    /// records the result back on the same node.
    ///
    /// This is the preferred self-repair surface. `SetRuleClause` remains as a
    /// compatibility path for old seeds, but name-only edits are necessarily
    /// weaker and are refused when a live name is ambiguous.
    ApplyRulePatch {
        patch_var: Sym,
    },
    /// PERCEPTION-AS-ACTION: a rule triggers a shared-memory framebuffer
    /// sample — the "when to look" decision, made by the agent's own
    /// rules rather than the host. `fb` resolves to the `Int`/`Float`
    /// `fb_id` a prior `fb_attach` call returned; `game_var` names an
    /// already-bound match var holding the `WorldInstance`/game root
    /// `NodeID` `segment_and_track` mints/updates Regions under;
    /// `grid_w`/`grid_h` resolve to the downsample grid dimensions.
    ///
    /// The applier here only holds `&mut TypedGraph` (not `&mut
    /// Substrate`, which owns the attached-framebuffer registry AND the
    /// admissibility-checked node/edge mutation helpers
    /// `segment_and_track` needs for correct dirty-tracking), so —
    /// mirroring `SetRuleClause`'s queue-and-drain-between-passes
    /// pattern exactly — this resolves its args under the binding and
    /// QUEUES `(fb_id, game, grid_w, grid_h)` onto
    /// `graph.pending_fb_samples`. `Substrate::run_rules` drains the
    /// queue once per pass (where `&mut self` is free) by calling
    /// `Substrate::fb_sample` — the SAME internal fn the PyO3
    /// `fb_sample` method calls — so a rule-triggered sample and a
    /// host-triggered sample mint/update identical graph state.
    FbSample {
        fb: EffectArg,
        game_var: Sym,
        grid_w: EffectArg,
        grid_h: EffectArg,
    },
    /// SELF-TRAINING: a rule fires one surprise-driven weight COLLAPSE of a
    /// reflex net, INSIDE the run_rules loop. `reflex_net` is a match var
    /// bound to the `ReflexNet` node (its `-net_assemblage->` net is
    /// collapsed); `input`/`target` resolve to the observed vectors (the
    /// net predicts input, its surprise is target−prediction, its readout
    /// collapses toward reducing it); `eta` is the step. Mirroring
    /// `Effect::FbSample`, the applier only holds `&mut graph`, so it
    /// resolves the args + QUEUES `(reflex_net, input, target, eta)` onto
    /// `graph.pending_net_collapses`; `Substrate::run_rules` drains it via
    /// `net_forward::net_collapse_step` and records the surprise back onto
    /// the net. This runs "collapse and surprise within the net" as part of
    /// the engine's collapse, no Python iteration.
    NetCollapse {
        reflex_net: Sym,
        input: EffectArg,
        target: EffectArg,
        eta: EffectArg,
    },
    /// GRAPH LAW #6 (trans-frame identity): the mutating twin of the
    /// read-only `TermNode::TrackIdentityCorrespondence` — a rule
    /// triggers domain-general "same-thing-across-frames" identity
    /// assignment. `prev`/`cur` resolve to Node collections
    /// (Set/FrozenSet/Tuple); `feature_key`/`category_key`/
    /// `extent_key`/`identity_key` are fixed Syms picked at
    /// rule-authoring time (the attr-key vocabulary, same convention
    /// `AddNode`'s `type_: Sym` uses); `radius` resolves to the max
    /// matchable feature-space distance.
    ///
    /// The applier here only holds `&mut TypedGraph` (not `&mut
    /// Substrate`, which owns the dirty-tracking node/edge mutation
    /// helpers `Substrate::track_identity` needs), so — mirroring
    /// `Effect::FbSample` exactly — this resolves prev/cur/radius
    /// under the binding and QUEUES the resolved NodeID lists onto
    /// `graph.pending_track_identity`; `Substrate::run_rules` drains
    /// the queue once per pass by calling `Substrate::track_identity`
    /// — the SAME fn a direct/PyO3 call uses, so a rule-triggered
    /// identity assignment and a host-triggered one agree exactly.
    TrackIdentity {
        prev: EffectArg,
        cur: EffectArg,
        feature_key: Sym,
        category_key: Option<Sym>,
        extent_key: Option<Sym>,
        identity_key: Sym,
        radius: EffectArg,
    },
}

/// A token in a rule's read/write access set. `Copy` enum so membership /
/// intersection are O(1). `Attr(k)` reads/writes node attr `k`; `Type(t)`
/// reads/mints nodes of type `t`; `Edge(e)` reads/writes edges of type `e`.
/// Imprecise reads/writes set the rule's `reads_any`/`writes_any` flag.
#[derive(Copy, Clone, PartialEq, Eq, Hash, Debug)]
pub enum RuleKey {
    Attr(Sym),
    Type(Sym),
    Edge(Sym),
}

thread_local! {
    /// Set only inside `derive_access`'s third walk: `TypeOf` / `AttrByName`
    /// do not count as opaque there (see `RewriteRule::reads_any_nonlocal`).
    static LOCAL_OPAQUE_OK: std::cell::Cell<bool> = const { std::cell::Cell::new(false) };
}

/// One rewrite rule. Has a name for diagnostics, a pattern (match
/// edges + optional where-clause Term), and an ordered effect list.
#[derive(Clone, Debug, Default)]
pub struct RewriteRule {
    /// Stable identity of this rule slot. Zero means "unassigned" on input;
    /// `Substrate::add_rule` assigns a non-zero UID and checkpoint export
    /// preserves it. Unlike `RuleIdx`, the UID is not positional.
    pub uid: RuleUid,
    /// Monotonic semantic revision. Incremented only after a successfully
    /// committed transactional clause patch.
    pub revision: u64,
    /// Stable 63-bit hash of the canonical semantic rule body. Recomputed by
    /// the substrate on install and commit; never trusted from an author.
    pub content_hash: u64,
    /// Seed-installed priors are not writable through the live RulePatch
    /// transaction surface.  The agent can still supersede them by authoring
    /// new graph rules, but cannot silently rewrite its boot substrate.  Rules
    /// authored after boot default to patchable; the seed loader sets this
    /// boundary bit mechanically for every bundled rule.
    pub mutation_protected: bool,
    pub name: Sym,
    /// Semantic cognitive area. Scheduling metadata only: legacy/global rules
    /// keep the committed global order until an area scheduler is enabled.
    pub area: Sym,
    /// Order on the reflex→deep-cognition continuum (0 = reflex).
    pub order: u32,
    /// Deadline class name (`hard_realtime`, `soft_realtime`, `best_effort`).
    pub latency_class: Sym,
    /// Whether scheduling metadata was explicitly authored. Keeps legacy rule
    /// checkpoint JSON byte-compatible by omitting derived defaults.
    pub schedule_explicit: bool,
    pub match_edges: Vec<MatchEdge>,
    pub where_: Option<TermIdx>,
    pub effects: Vec<Effect>,
    /// R10 join-index hints (see `IndexJoinHint`). Empty for every rule that
    /// doesn't opt in — `Vec::default()` is `vec![]`, so every existing
    /// `..Default::default()` `RewriteRule` construction site is unaffected.
    pub index_hints: Vec<IndexJoinHint>,

    /// PREDICATE PUSHDOWN (measured, 2026-07-17). The where-clause's top-level
    /// `And` conjuncts, each paired with EVERY `Var` name appearing anywhere
    /// inside it. `extend_each` evaluates a conjunct as soon as all its vars
    /// are bound, instead of only at the leaf once every match-edge has been
    /// expanded — pruning the whole subtree under a cell that already failed.
    ///
    /// WHY (the within-Rust attribution, `scripts/rust_attrib_measure.py`):
    /// `wv_propagate` enumerated 65,024 bindings at 128^2 to admit ~1,000
    /// (16,384 cells x ~4 neighbours; only ~254 cells are `active`). 91.5% of
    /// its cost was PER-BINDING work on bindings rejected by a conjunct that
    /// reads ONLY `c` — `Eq(Attr(c,"state"), "active")` — and so could have
    /// been decided before `n` was ever bound. Edge enumeration was 8.3%: the
    /// join index the framing suspected was NOT the win.
    ///
    /// EMPTY = OFF. Derived only for rules with >1 match-edge (a 1-edge rule
    /// has no subtree to prune, so it is byte-identical either way), and only
    /// on the interpreter path (a JIT-compiled where is evaluated whole).
    ///
    /// CORRECTNESS — this FAILS CLOSED. Var collection is the generic
    /// `term::children` walk, so it cannot MISS a `Var` (missing one is the
    /// only unsafe direction: it would let a conjunct be evaluated with an
    /// unbound var). It may OVER-collect — a `Filter`/`Let` lambda's scoped
    /// var looks free — and over-collection is safe: such a var is never in
    /// the binding, so the conjunct is simply never pushed down and is
    /// evaluated at the leaf exactly as before. Reordering a conjunction of
    /// PURE, TOTAL predicates cannot change its value; the DSL's `evaluate`
    /// returns a `Value` for any bound env and has no side effects.
    pub where_conjuncts: Vec<(TermIdx, smallvec::SmallVec<[Sym; 4]>)>,

    /// BINDING PROJECTION (block 188000). `Some(vars)` iff this rule has at
    /// least one match variable referenced by NEITHER the where-clause NOR any
    /// effect, AND every effect is `SetAttr` / `SetAttrIfDifferent`. `vars` is
    /// then the set of match variables that ARE referenced — the projection the
    /// binding set may be deduplicated on.
    ///
    /// WHY it is sound: two bindings that agree on `vars` agree on the truth of
    /// the where-clause (it reads nothing else that is bound) and produce
    /// IDENTICAL effects (same node, same key, same resolved value). The
    /// admissible effects are idempotent, so applying one such binding is
    /// bit-identical to applying all of them. This removes a RE-DERIVATION,
    /// never a DECISION.
    ///
    /// WHY the effect whitelist is this narrow: `AddNode` mints one node PER
    /// BINDING, so projecting it would genuinely change the graph; `AddEdge`
    /// raises edge-multiplicity questions; deletes interact with the undo log.
    /// Only the two attribute writes are provably binding-count-independent.
    ///
    /// Var collection reuses `collect_term_vars`, the generic `term::children`
    /// walk that CANNOT MISS a `Var`. Over-collection is safe — it only
    /// declines the optimisation. Under-collection is the unsafe direction and
    /// the walk makes it impossible.
    ///
    /// DEFAULT-OFF at the engine level (`Substrate::binding_projection`): this
    /// field is derived for every rule but read by nobody unless that flag is
    /// on.
    pub project_vars: Option<smallvec::SmallVec<[Sym; 4]>>,

    // --- access analysis (slice b: batch-apply + write-set dirtying) ---
    /// Over-approx superset of graph keys this rule READS to decide bindings.
    pub read_set: rustc_hash::FxHashSet<RuleKey>,
    /// Typed edge resources read by where/effect terms, distinct from the
    /// match-edge drivers. A write to one of these can change an existing
    /// binding's term result, so its semi-naive cursor must be invalidated.
    pub term_edge_reads: rustc_hash::FxHashSet<Sym>,
    /// Over-approx superset of graph keys this rule WRITES.
    pub write_set: rustc_hash::FxHashSet<RuleKey>,
    /// Conservative "reads something opaque" — forces always-dirty.
    pub reads_any: bool,
    /// `reads_any` WITHOUT the bound-node-local opaque reads (`TypeOf`,
    /// `AttrByName`: the type / a dynamically-named attr of a node the rule
    /// already reached). Only consulted by the isolated-node write exemption
    /// (`Substrate::fresh_node_exempt`); every default path uses `reads_any`.
    pub reads_any_nonlocal: bool,
    /// `read_set` WITHOUT the effects' own write-target reads: the keys read by
    /// the where-clause and by computed effect ARGS only. The idempotence /
    /// dedup look-ups of `AddEdge` (its edge type), `AddNode[IfAbsent]` (its type
    /// and key attrs) and `SetAttr[IfDifferent]` (its key) are excluded: they
    /// decide nothing about WHICH bindings match, they only make re-firing an
    /// already-fired binding a no-op. Only consulted by the own-write exemption
    /// (`Substrate::own_write_exempt`) when deciding whether a write must CLEAR
    /// a consumer's semi-naive cursor; dirtying still uses `read_set`.
    pub read_set_strict: rustc_hash::FxHashSet<RuleKey>,
    /// The typed-edge subset of `read_set_strict` (cf. `term_edge_reads`, which
    /// also holds an `AddEdge` effect's own edge type).
    pub term_edge_reads_strict: rustc_hash::FxHashSet<Sym>,
    /// WRITE-FRONTIER eligibility (`Substrate::write_frontier`): the rule's
    /// effects are add/set only (no fresh `AddNode`), it has a match, it does
    /// not read external state or anything opaque non-locally, and every
    /// dynamically-named attr read (`AttrByName`) is on a match variable outside
    /// any binder. Then a write of attr `k` on node `x` can flip only bindings
    /// that bind `x`, unless `k` is in `wf_nonlocal_keys`.
    pub wf_ok: bool,
    /// Attr keys this rule reads OFF its match frontier: under a binder /
    /// iteration (`Exists`, `Filter`, ...), on a non-match variable, or via
    /// `NodesWhere`. A write of one of these keys must clear the cursor.
    pub wf_nonlocal_keys: rustc_hash::FxHashSet<Sym>,
    /// The rule reads a dynamically-named attr of a match variable, so a write
    /// of ANY key to a bound node may flip it (node-seeded, not cleared).
    pub wf_dyn_local: bool,
    /// The match variables whose dynamically-named attrs are read (`AttrByName`).
    pub wf_dyn_vars: smallvec::SmallVec<[Sym; 2]>,
    /// Edge types this rule's terms read ONLY as `Neighbours(v, E)` /
    /// `InNeighbours(v, E)` of an unshadowed match variable `v`: a new `E` edge
    /// can then flip only bindings that bind its source (out) / target (in).
    pub wf_local_out: rustc_hash::FxHashSet<Sym>,
    pub wf_local_in: rustc_hash::FxHashSet<Sym>,
    /// HOP FRONTIER (`Substrate::hop_frontier`, DEFAULT OFF) variant of the
    /// write-frontier locality above: the pure set / arithmetic operators
    /// (`SetT`, `Pick`, `Union`, `Intersect`, `Difference`, `Plus`, `Minus`) are
    /// transparent, and an `Attr` read of an `Exists` / `Filter` variable whose
    /// source is `Neighbours(v, E)` / `InNeighbours(v, E)` of a match variable
    /// `v` is ONE HOP local (`wf_hop`): a write of that key on node `x` can flip
    /// only bindings of the `E`-neighbours of `x`. `Substrate::set_hop_frontier`
    /// swaps these into the `wf_*` fields above (and back).
    pub wf_hop_alt: Option<Box<WfInfo>>,
    /// One-hop local attr reads `(key, E, out)` of the active variant: `out` =
    /// read through `Neighbours(v, E)` (so `v -E-> x`), else `InNeighbours`.
    pub wf_hop: Vec<(Sym, Sym, bool)>,
    /// The hop variant is the active one (`swap_wf_hop` toggles; install resets).
    pub wf_hop_active: bool,
    /// `AddEdge` effect types with at least one endpoint bound by the match:
    /// deleting such an edge can re-enable only bindings of its endpoints
    /// (`Substrate::delete_frontier`).
    pub own_edge_seedable: rustc_hash::FxHashSet<Sym>,
    /// Matcher traversal only, DEFAULT FALSE (set on the seeded sub-matches of
    /// `Substrate::seeded_join_order`): a match edge whose endpoints are BOTH
    /// bound is checked from its smaller side (the target's in-edges when they
    /// are fewer than the source's out-edges) instead of enumerating every
    /// out-neighbour of the source -- e.g. `agent -received-> m` with both bound
    /// was O(conversation length). Edges are unique per (src, type, tgt), so the
    /// one surviving candidate, and the binding order, are unchanged.
    pub both_bound_probe: bool,
    /// Conservative "writes something opaque" — forces a blanket dirty.
    pub writes_any: bool,
    /// THE gate read by both run-rules paths. When true, the runner uses
    /// `batch_apply_rule` (apply every binding this pass) instead of
    /// one-progressing-binding-per-pass. Set from the rule node's `batch`
    /// attr if present, else from the derived `batch_safe`.
    pub batch: bool,
    /// Derived conservative proof that snapshot-batch == one-per-pass.
    pub batch_safe: bool,
    /// Optional type-indexed driver: enumerate `nodes_of_type(match_type)`
    /// bound to the single match-edge's tgt_var. Falls back to the matcher.
    pub match_type: Option<Sym>,
    /// Tombstone flag — `Substrate::remove_rule` sets this `false` instead
    /// of removing the slot, so `RuleIdx`s handed out by `add_rule` stay
    /// valid (self-modification code and callers may hold one). An
    /// inactive rule is skipped everywhere a rule is matched/applied
    /// (`apply_rule_once`, `run_rules`'s dirty-rule scan); it never fires
    /// again. `#[derive(Default)]` gives `false`, which would make every
    /// freshly-constructed `RewriteRule` inert by default — `add_rule` is
    /// the sole path that pushes into `Substrate::rules`, and it forces
    /// this to `true` on the way in, so only an explicit `remove_rule`
    /// call can ever turn it off.
    pub active: bool,
    /// PERCEPTION-AS-ACTION: true iff this rule's `where`-clause reads
    /// `FbFrameSeq` — an oracle over EXTERNAL state (a shared-memory
    /// writer's `frame_seq`, ticking with no corresponding graph
    /// mutation) rather than graph state. `Substrate::run_rules`'s
    /// dirty-tracking is entirely graph-mutation-driven (a rule is only
    /// re-tried when something it reads gets WRITTEN); an
    /// `FbFrameSeq`-gated rule can flip from false to true with ZERO
    /// graph writes in between (the writer just wrote a new frame), so
    /// that optimisation would silently starve it after its first fire
    /// — the where-clause would stay perpetually stale. `run_rules`
    /// force-dirties every `reads_external` rule every pass instead
    /// (a bounded poll, not a graph-reactive wake), so "did the frame
    /// advance" gets re-asked every tick regardless of what else did or
    /// didn't mutate. Computed by `derive_access`.
    pub reads_external: bool,
}

impl RewriteRule {
    /// Compute read_set / write_set / reads_any / writes_any / batch_safe
    /// from this rule's match_edges, where_, and effects. Idempotent.
    /// Does NOT set `batch` — the caller applies explicit-attr-else-safe.
    pub fn derive_access(&mut self, arena: &TermArena) {
        self.read_set.clear();
        self.term_edge_reads.clear();
        self.write_set.clear();
        self.reads_any = false;
        self.writes_any = false;
        for me in &self.match_edges {
            self.read_set.insert(RuleKey::Edge(me.edge_type));
        }
        let mut reads = std::mem::take(&mut self.read_set);
        let mut writes = std::mem::take(&mut self.write_set);
        let mut reads_any = self.reads_any;
        let mut writes_any = self.writes_any;
        if let Some(w) = self.where_ {
            collect_term_reads(arena, w, &mut reads, &mut reads_any);
        }
        for eff in &self.effects {
            collect_effect_access(
                eff,
                arena,
                &mut reads,
                &mut writes,
                &mut reads_any,
                &mut writes_any,
            );
        }
        // Retain the origin of typed edge reads. The ordinary read_set is a
        // union of pattern drivers and term dependencies; the scheduler needs
        // this narrower distinction to know when a new edge cannot advance a
        // reader's existing match cursor. This second walk runs only when a
        // rule is installed/re-derived, not on the execution hot path.
        let mut term_reads = rustc_hash::FxHashSet::default();
        let mut term_reads_any = false;
        if let Some(w) = self.where_ {
            collect_term_reads(arena, w, &mut term_reads, &mut term_reads_any);
        }
        let mut ignored_writes = rustc_hash::FxHashSet::default();
        let mut ignored_writes_any = false;
        for eff in &self.effects {
            collect_effect_access(
                eff,
                arena,
                &mut term_reads,
                &mut ignored_writes,
                &mut term_reads_any,
                &mut ignored_writes_any,
            );
        }
        self.term_edge_reads = term_reads
            .into_iter()
            .filter_map(|key| match key {
                RuleKey::Edge(edge_type) => Some(edge_type),
                RuleKey::Attr(_) | RuleKey::Type(_) => None,
            })
            .collect();
        // Strict walk (install-time only): where + computed effect args, without
        // the effects' own write-target look-ups (see `read_set_strict`). Effects
        // other than the add/set kinds keep their full (conservative) access.
        {
            let mut strict = rustc_hash::FxHashSet::default();
            let mut sra = false;
            let mut ign_w = rustc_hash::FxHashSet::default();
            let mut ign_wa = false;
            if let Some(w) = self.where_ {
                collect_term_reads(arena, w, &mut strict, &mut sra);
            }
            for eff in &self.effects {
                let args: Option<Vec<&EffectArg>> = match eff {
                    Effect::AddEdge { attrs, .. } if attrs.is_empty() => Some(Vec::new()),
                    Effect::AddNode { attrs, .. } | Effect::AddNodeIfAbsent { attrs, .. } => {
                        Some(attrs.iter().map(|(_, a)| a).collect())
                    }
                    Effect::SetAttr { value, .. } | Effect::SetAttrIfDifferent { value, .. } => {
                        Some(vec![value])
                    }
                    _ => None,
                };
                match args {
                    Some(args) => {
                        for a in args {
                            if let EffectArg::Computed(idx) = a {
                                collect_term_reads(arena, *idx, &mut strict, &mut sra);
                            }
                        }
                    }
                    None => collect_effect_access(
                        eff, arena, &mut strict, &mut ign_w, &mut sra, &mut ign_wa,
                    ),
                }
            }
            self.term_edge_reads_strict = strict
                .iter()
                .filter_map(|key| match key {
                    RuleKey::Edge(edge_type) => Some(*edge_type),
                    RuleKey::Attr(_) | RuleKey::Type(_) => None,
                })
                .collect();
            self.read_set_strict = strict;
        }
        // Third walk (install-time only): reads_any minus the bound-node-local
        // opaque reads, for the isolated-node write exemption.
        {
            LOCAL_OPAQUE_OK.with(|c| c.set(true));
            let mut r2 = rustc_hash::FxHashSet::default();
            let mut w2 = rustc_hash::FxHashSet::default();
            let (mut ra2, mut wa2) = (false, false);
            if let Some(w) = self.where_ {
                collect_term_reads(arena, w, &mut r2, &mut ra2);
            }
            for eff in &self.effects {
                collect_effect_access(eff, arena, &mut r2, &mut w2, &mut ra2, &mut wa2);
            }
            LOCAL_OPAQUE_OK.with(|c| c.set(false));
            self.reads_any_nonlocal = ra2;
        }
        self.read_set = reads;
        self.write_set = writes;
        self.reads_any = reads_any;
        self.writes_any = writes_any;
        // Write-frontier locality walk (install-time only): the committed
        // analysis, then its hop variant (`wf_hop_alt`).
        let match_vars: rustc_hash::FxHashSet<Sym> = self
            .match_edges
            .iter()
            .flat_map(|me| [me.src_var, me.tgt_var])
            .collect();
        for hop_mode in [false, true] {
            let mut st = WfLocality {
                match_vars: &match_vars,
                shadow: smallvec::SmallVec::new(),
                nonlocal: rustc_hash::FxHashSet::default(),
                dyn_local: false,
                dyn_nonlocal: false,
                dyn_vars: smallvec::SmallVec::new(),
                local_out: rustc_hash::FxHashSet::default(),
                local_in: rustc_hash::FxHashSet::default(),
                nonlocal_edges: rustc_hash::FxHashSet::default(),
                hop_mode,
                hop_src: smallvec::SmallVec::new(),
                hop: Vec::new(),
            };
            if let Some(w) = self.where_ {
                st.walk(arena, w);
            }
            let mut effects_ok = true;
            for eff in &self.effects {
                let args: Vec<&EffectArg> = match eff {
                    Effect::AddEdge { attrs, .. } | Effect::AddNodeIfAbsent { attrs, .. } => {
                        attrs.iter().map(|(_, a)| a).collect()
                    }
                    Effect::SetAttr { value, .. } | Effect::SetAttrIfDifferent { value, .. } => {
                        vec![value]
                    }
                    // hop mode: a DelEdge of a type the rule does not match is a
                    // read of that edge at its two bound endpoints only (a new
                    // such edge can re-enable just the binding of its endpoints)
                    Effect::DelEdge { src_var, edge_type, tgt_var }
                        if hop_mode
                            && !self.match_edges.iter().any(|me| me.edge_type == *edge_type)
                            && match_vars.contains(src_var)
                            && match_vars.contains(tgt_var) =>
                    {
                        st.local_out.insert(*edge_type);
                        st.local_in.insert(*edge_type);
                        Vec::new()
                    }
                    _ => {
                        effects_ok = false;
                        Vec::new()
                    }
                };
                for a in args {
                    if let EffectArg::Computed(idx) = a {
                        st.walk(arena, *idx);
                    }
                }
            }
            let info = WfInfo {
                ok: effects_ok
                    && !self.match_edges.is_empty()
                    && !st.dyn_nonlocal
                    && !self.reads_any_nonlocal
                    && !self.writes_any
                    && !self
                        .where_
                        .map(|w| term_reads_fb_frame_seq(arena, w))
                        .unwrap_or(false),
                nonlocal_keys: st.nonlocal,
                dyn_local: st.dyn_local,
                dyn_vars: st.dyn_vars,
                // an edge type every term read of which is local (no non-local read)
                local_out: st.local_out.difference(&st.nonlocal_edges).copied().collect(),
                local_in: st.local_in.difference(&st.nonlocal_edges).copied().collect(),
                hop: st.hop,
            };
            if hop_mode {
                self.wf_hop_alt = Some(Box::new(info));
            } else {
                self.wf_ok = info.ok;
                self.wf_nonlocal_keys = info.nonlocal_keys;
                self.wf_dyn_local = info.dyn_local;
                self.wf_dyn_vars = info.dyn_vars;
                self.wf_local_out = info.local_out;
                self.wf_local_in = info.local_in;
                self.wf_hop = Vec::new();
                self.wf_hop_active = false;
            }
        }
        self.own_edge_seedable = self
            .effects
            .iter()
            .filter_map(|e| match e {
                Effect::AddEdge { src_var, edge_type, tgt_var, .. }
                    if match_vars.contains(src_var) || match_vars.contains(tgt_var) =>
                {
                    Some(*edge_type)
                }
                _ => None,
            })
            .collect();
        let order_safe = self.effects.iter().all(|e| {
            matches!(
                e,
                Effect::AddEdge { .. }
                    | Effect::AddNode { .. }
                    | Effect::AddNodeIfAbsent { .. }
                    | Effect::SetAttr { .. }
                    | Effect::SetAttrIfDifferent { .. }
            )
        });
        self.batch_safe = order_safe
            && !self.reads_any
            && !self.writes_any
            && self.read_set.is_disjoint(&self.write_set);
        self.reads_external = self
            .where_
            .map(|w| term_reads_fb_frame_seq(arena, w))
            .unwrap_or(false);
        self.derive_pushdown(arena);
        self.project_vars = self.derive_projection(arena);
    }

    /// BINDING PROJECTION (block 188000) — see `project_vars`. Returns the
    /// referenced match variables when at least one match variable is
    /// referenced nowhere, and every effect is an attribute write.
    fn derive_projection(&self, arena: &TermArena) -> Option<smallvec::SmallVec<[Sym; 4]>> {
        if self.match_edges.is_empty() {
            return None;
        }
        // (b) Only binding-count-INDEPENDENT effects. Anything else — a mint, an
        // edge, a delete, a rule edit — is excluded outright.
        let mut used: smallvec::SmallVec<[Sym; 4]> = smallvec::SmallVec::new();
        for eff in &self.effects {
            match eff {
                Effect::SetAttr { var, value, .. }
                | Effect::SetAttrIfDifferent { var, value, .. } => {
                    if !used.contains(var) {
                        used.push(*var);
                    }
                    if let EffectArg::Computed(t) = value {
                        collect_term_vars(arena, *t, &mut used);
                    }
                }
                _ => return None,
            }
        }
        if let Some(w) = self.where_ {
            collect_term_vars(arena, w, &mut used);
        }
        // (a) At least one match variable referenced NOWHERE.
        let mut proj: smallvec::SmallVec<[Sym; 4]> = smallvec::SmallVec::new();
        let mut any_unused = false;
        for me in &self.match_edges {
            for v in [me.src_var, me.tgt_var] {
                if used.contains(&v) {
                    if !proj.contains(&v) {
                        proj.push(v);
                    }
                } else {
                    any_unused = true;
                }
            }
        }
        if !any_unused {
            return None;
        }
        Some(proj)
    }

    /// Precompute the predicate-pushdown plan (see `where_conjuncts`).
    /// Only multi-edge rules get one — a 1-edge rule binds every var at
    /// level 0, so pushdown could not prune anything and the plan stays
    /// empty (⇒ byte-identical leaf evaluation).
    fn derive_pushdown(&mut self, arena: &TermArena) {
        self.where_conjuncts.clear();
        // `OZMA_NO_PUSHDOWN=1` restores the pre-change matcher process-wide.
        // NOT a tunable and NOT a behaviour knob (§13): both settings must
        // produce IDENTICAL results — that is the invariant the §9 gate
        // asserts. It exists so "is this failure mine, or pre-existing?" is a
        // question that can be ANSWERED on one build instead of guessed at.
        if std::env::var("OZMA_NO_PUSHDOWN")
            .map(|v| v == "1")
            .unwrap_or(false)
        {
            return;
        }
        if self.match_edges.len() < 2 {
            return;
        }
        let Some(w) = self.where_ else { return };
        // Only a top-level `And` decomposes. Anything else is one predicate
        // and pushing it down is exactly the leaf evaluation we already do.
        let items: Vec<TermIdx> = match arena.get(w) {
            crate::term::TermNode::And { items } => items.clone().into_iter().collect(),
            _ => return,
        };
        if items.len() < 2 {
            return;
        }
        for it in items {
            let mut vars: smallvec::SmallVec<[Sym; 4]> = smallvec::SmallVec::new();
            collect_term_vars(arena, it, &mut vars);
            self.where_conjuncts.push((it, vars));
        }
    }
}

/// Every `Var` name appearing anywhere in a term. Uses the SAME generic
/// `term::children` walk as `collect_term_reads`, so no variant can hide a
/// `Var` from it — under-collection is the only unsafe direction (it would
/// let `extend_each` evaluate a conjunct with an unbound var). Over-collection
/// (e.g. a lambda's scoped var) is safe and merely disables pushdown for that
/// conjunct.
fn collect_term_vars(arena: &TermArena, idx: TermIdx, out: &mut smallvec::SmallVec<[Sym; 4]>) {
    match arena.get(idx) {
        crate::term::TermNode::Var { name } => {
            if !out.contains(name) {
                out.push(*name);
            }
        }
        other => {
            for c in crate::term::children(other) {
                collect_term_vars(arena, c, out);
            }
        }
    }
}

/// Does the Term rooted at `idx` contain an `FbFrameSeq` anywhere in its
/// tree? Used to compute `RewriteRule::reads_external` — see that
/// field's doc comment for why a rule containing this needs different
/// (poll, not graph-reactive) dirty-tracking treatment.
fn term_reads_fb_frame_seq(arena: &TermArena, idx: TermIdx) -> bool {
    use crate::term::TermNode as T;
    match arena.get(idx) {
        T::FbFrameSeq { .. } => true,
        other => crate::term::children(other)
            .iter()
            .any(|&c| term_reads_fb_frame_seq(arena, c)),
    }
}

/// Does this subtree read a node ATTRIBUTE anywhere (`Attr` / `AttrByName` /
/// `NodesWhere`, which filters a whole type by an attr value)? Helper for the
/// predicate-retraction soundness test below — a node-set iteration is only
/// unsafe if it READS AN ATTR off the frontier; iterating for structure (edges,
/// type membership, a count) is fine.
fn subtree_reads_attr(arena: &TermArena, idx: TermIdx) -> bool {
    use crate::term::TermNode as T;
    match arena.get(idx) {
        T::Attr { .. } | T::AttrByName { .. } | T::NodesWhere { .. } => true,
        other => crate::term::children(other)
            .iter()
            .any(|&c| subtree_reads_attr(arena, c)),
    }
}

/// Does this Term read a node ATTRIBUTE *through* a node-set iteration —
/// i.e. an `Attr` read on a node the rule's match never bound?
///
/// Load-bearing for predicate-retraction eligibility (block 292000). The
/// frontier re-evaluator seeds dirty bindings ONLY from nodes incident to a
/// changed node; that is sound iff every attr the rule reads lives on a
/// match-bound node. A node-set-iterating Term (`Neighbours`/`Argmin`/`Sum`/…)
/// that reads an attr INSIDE the iteration (e.g. the nav's `mv_pick_hop` —
/// `Argmin` over `Neighbours(cur, adj)` reading `gdist`) reads attrs on cells
/// the match never bound, so a `gdist` write to one of those cells is
/// UNREACHABLE from the changed-node frontier and the binding goes stale.
///
/// The DISTINCTION that matters (a coarser "any node-set Term" test wrongly
/// excluded the materialized-view staleness guard `Count(Neighbours(src, E))`,
/// regressing block 194000's O(K) gate): a node-set Term that reads only
/// STRUCTURE (`Count` of edges, `NodesOfType` membership) is SAFE — an edge/
/// type change bumps the cursor version and is handled structurally; only an
/// attr read through the iteration escapes the attr-frontier. So the flag is
/// "node-set iteration whose subtree contains an attr read", not "node-set
/// iteration". `Min`/`Max` over a fixed item list are not iterations; the
/// `any_type`/dynamic-name variants already set `reads_any` and are excluded by
/// that guard.
pub fn term_reads_attr_via_node_set(arena: &TermArena, idx: TermIdx) -> bool {
    use crate::term::TermNode as T;
    match arena.get(idx) {
        // `NodesWhere` reads an attr across a whole type — an attr read off the
        // frontier by construction.
        T::NodesWhere { .. } => true,
        // Node-set iterations: unsafe iff the iteration's subtree reads an attr.
        T::Neighbours { .. }
        | T::InNeighbours { .. }
        | T::MapNeighbours { .. }
        | T::SlideNeighbours { .. }
        | T::NodesOfType { .. }
        | T::Count { .. }
        | T::Filter { .. }
        | T::Exists { .. }
        | T::Sum { .. }
        | T::MinOver { .. }
        | T::MaxOver { .. }
        | T::Argmax { .. }
        | T::Argmin { .. }
        | T::Fold { .. }
        | T::EvalSubgraph { .. } => subtree_reads_attr(arena, idx),
        other => crate::term::children(other)
            .iter()
            .any(|&c| term_reads_attr_via_node_set(arena, c)),
    }
}

/// Does ANY Term this rule evaluates (its where-clause or an effect's computed
/// arg) read an attr through a node-set iteration? If so the rule reads attrs
/// off its match frontier and is NOT sound to run through predicate retraction
/// (block 292000). Only the add-only effect kinds are inspected here — a rule
/// with any other effect is already predicate-retraction-ineligible via the
/// `add_only` guard, so this helper is only ever consulted alongside it; a
/// non-add-only effect falls to the conservative `true` (ineligible) just in
/// case the call order ever changes.
pub fn rule_reads_attr_via_node_set(rule: &RewriteRule, arena: &TermArena) -> bool {
    if let Some(w) = rule.where_ {
        if term_reads_attr_via_node_set(arena, w) {
            return true;
        }
    }
    let arg_reads = |a: &EffectArg| {
        matches!(a, EffectArg::Computed(idx)
        if term_reads_attr_via_node_set(arena, *idx))
    };
    rule.effects.iter().any(|eff| match eff {
        Effect::AddEdge { attrs, .. }
        | Effect::AddNode { attrs, .. }
        | Effect::AddNodeIfAbsent { attrs, .. } => attrs.iter().any(|(_, a)| arg_reads(a)),
        Effect::SetAttr { value, .. } | Effect::SetAttrIfDifferent { value, .. } => {
            arg_reads(value)
        }
        // Not an add-only effect — the `add_only` guard already excludes the
        // rule; be conservative (ineligible) regardless of consultation order.
        _ => true,
    })
}

/// One write-frontier locality analysis (see `RewriteRule::wf_hop_alt`).
#[derive(Clone, Debug, Default)]
pub struct WfInfo {
    pub ok: bool,
    pub nonlocal_keys: rustc_hash::FxHashSet<Sym>,
    pub dyn_local: bool,
    pub dyn_vars: smallvec::SmallVec<[Sym; 2]>,
    pub local_out: rustc_hash::FxHashSet<Sym>,
    pub local_in: rustc_hash::FxHashSet<Sym>,
    pub hop: Vec<(Sym, Sym, bool)>,
}

impl RewriteRule {
    /// Make the hop variant (both are computed at install time) the active
    /// write-frontier locality, or restore the committed one.
    pub fn set_wf_hop(&mut self, on: bool) {
        if self.wf_hop_active != on {
            self.swap_wf_hop();
        }
    }

    fn swap_wf_hop(&mut self) {
        let Some(alt) = self.wf_hop_alt.as_mut() else { return };
        self.wf_hop_active = !self.wf_hop_active;
        std::mem::swap(&mut self.wf_ok, &mut alt.ok);
        std::mem::swap(&mut self.wf_nonlocal_keys, &mut alt.nonlocal_keys);
        std::mem::swap(&mut self.wf_dyn_local, &mut alt.dyn_local);
        std::mem::swap(&mut self.wf_dyn_vars, &mut alt.dyn_vars);
        std::mem::swap(&mut self.wf_local_out, &mut alt.local_out);
        std::mem::swap(&mut self.wf_local_in, &mut alt.local_in);
        std::mem::swap(&mut self.wf_hop, &mut alt.hop);
    }
}

/// Write-frontier locality walker (`RewriteRule::wf_ok`). A read is LOCAL when
/// it is of a match variable that no enclosing binder shadows, through only the
/// transparent operators below (`Exists` / `Filter` scope their variable over
/// the predicate; their source is in the outer scope): an `Attr` / `AttrByName`
/// of it, or its out- / in-edges of one type (`Neighbours` / `InNeighbours`).
/// Every other read is NON-LOCAL; any other Term contributes ALL its reads
/// (`collect_term_reads`) as non-local.
struct WfLocality<'a> {
    match_vars: &'a rustc_hash::FxHashSet<Sym>,
    shadow: smallvec::SmallVec<[Sym; 4]>,
    nonlocal: rustc_hash::FxHashSet<Sym>,
    dyn_local: bool,
    dyn_nonlocal: bool,
    dyn_vars: smallvec::SmallVec<[Sym; 2]>,
    local_out: rustc_hash::FxHashSet<Sym>,
    local_in: rustc_hash::FxHashSet<Sym>,
    nonlocal_edges: rustc_hash::FxHashSet<Sym>,
    /// hop mode (see `RewriteRule::wf_hop_alt`)
    hop_mode: bool,
    /// parallel to `shadow`: the binder's one-hop source `(E, out)`, if any
    hop_src: smallvec::SmallVec<[Option<(Sym, bool)>; 4]>,
    hop: Vec<(Sym, Sym, bool)>,
}

impl WfLocality<'_> {
    /// The one-hop source of `idx` when it is a variable whose innermost binder
    /// iterates `Neighbours` / `InNeighbours` of an unshadowed match variable.
    fn hop_var(&self, arena: &TermArena, idx: TermIdx) -> Option<(Sym, bool)> {
        if !self.hop_mode {
            return None;
        }
        let crate::term::TermNode::Var { name } = arena.get(idx) else { return None };
        let pos = self.shadow.iter().rposition(|s| s == name)?;
        self.hop_src[pos]
    }

    fn local_var(&self, arena: &TermArena, idx: TermIdx) -> Option<Sym> {
        match arena.get(idx) {
            crate::term::TermNode::Var { name }
                if self.match_vars.contains(name) && !self.shadow.contains(name) =>
            {
                Some(*name)
            }
            _ => None,
        }
    }

    fn opaque(&mut self, arena: &TermArena, idx: TermIdx) {
        let mut reads = rustc_hash::FxHashSet::default();
        let mut ra = false;
        collect_term_reads(arena, idx, &mut reads, &mut ra);
        for k in reads {
            match k {
                RuleKey::Attr(a) => {
                    self.nonlocal.insert(a);
                }
                RuleKey::Edge(e) => {
                    self.nonlocal_edges.insert(e);
                }
                RuleKey::Type(_) => {}
            }
        }
        if ra {
            self.dyn_nonlocal = true;
        }
    }

    fn walk(&mut self, arena: &TermArena, idx: TermIdx) {
        use crate::term::TermNode as T;
        match arena.get(idx) {
            T::Attr { node, key } => {
                if self.local_var(arena, *node).is_none() {
                    match self.hop_var(arena, *node) {
                        Some((et, out)) => {
                            if !self.hop.contains(&(*key, et, out)) {
                                self.hop.push((*key, et, out));
                            }
                        }
                        None => {
                            self.nonlocal.insert(*key);
                        }
                    }
                }
                self.walk(arena, *node);
            }
            T::AttrByName { node, name } => {
                match self.local_var(arena, *node) {
                    Some(v) => {
                        self.dyn_local = true;
                        if !self.dyn_vars.contains(&v) {
                            self.dyn_vars.push(v);
                        }
                    }
                    None => self.dyn_nonlocal = true,
                }
                self.walk(arena, *node);
                self.walk(arena, *name);
            }
            T::Neighbours { node, edge_type, any_type } | T::InNeighbours { node, edge_type, any_type } => {
                let out = matches!(arena.get(idx), T::Neighbours { .. });
                if *any_type {
                    self.dyn_nonlocal = true;
                } else if self.local_var(arena, *node).is_some() {
                    if out {
                        self.local_out.insert(*edge_type);
                    } else {
                        self.local_in.insert(*edge_type);
                    }
                } else {
                    self.nonlocal_edges.insert(*edge_type);
                }
                self.walk(arena, *node);
            }
            T::Exists { source, var_name, predicate } | T::Filter { source, var_name, predicate } => {
                self.walk(arena, *source);
                let src = match arena.get(*source) {
                    T::Neighbours { node, edge_type, any_type: false }
                        if self.local_var(arena, *node).is_some() => Some((*edge_type, true)),
                    T::InNeighbours { node, edge_type, any_type: false }
                        if self.local_var(arena, *node).is_some() => Some((*edge_type, false)),
                    _ => None,
                };
                self.shadow.push(*var_name);
                self.hop_src.push(src);
                self.walk(arena, *predicate);
                self.shadow.pop();
                self.hop_src.pop();
            }
            T::SetT { .. }
            | T::Pick { .. }
            | T::Union { .. }
            | T::Intersect { .. }
            | T::Difference { .. }
            | T::Plus { .. }
            | T::Minus { .. }
                if self.hop_mode =>
            {
                for c in crate::term::children(arena.get(idx)) {
                    self.walk(arena, c);
                }
            }
            T::Lit { .. } | T::Var { .. } => {}
            T::TypeOf { .. }
            | T::In { .. }
            | T::Eq { .. }
            | T::Lt { .. }
            | T::Lte { .. }
            | T::Gt { .. }
            | T::Gte { .. }
            | T::Count { .. }
            | T::And { .. }
            | T::Or { .. }
            | T::Not { .. }
            | T::IfThenElse { .. } => {
                for c in crate::term::children(arena.get(idx)) {
                    self.walk(arena, c);
                }
            }
            _ => self.opaque(arena, idx),
        }
    }
}

/// Walk a where-clause / effect-arg Term, collecting graph reads.
fn collect_term_reads(
    arena: &TermArena,
    idx: TermIdx,
    reads: &mut rustc_hash::FxHashSet<RuleKey>,
    reads_any: &mut bool,
) {
    use crate::term::TermNode as T;
    match arena.get(idx) {
        T::Attr { node, key } => {
            reads.insert(RuleKey::Attr(*key));
            collect_term_reads(arena, *node, reads, reads_any);
        }
        T::NodesOfType { node_type } => {
            reads.insert(RuleKey::Type(*node_type));
        }
        T::NodesWhere {
            node_type,
            attr_key,
            value,
        } => {
            reads.insert(RuleKey::Type(*node_type));
            reads.insert(RuleKey::Attr(*attr_key));
            collect_term_reads(arena, *value, reads, reads_any);
        }
        T::SlideNeighbours {
            cell,
            slide,
            ground,
        } => {
            collect_term_reads(arena, *cell, reads, reads_any);
            collect_term_reads(arena, *slide, reads, reads_any);
            collect_term_reads(arena, *ground, reads, reads_any);
            *reads_any = true;
        }
        T::ReachableFrom {
            node,
            edge_type,
            any_type,
        }
        | T::Neighbours {
            node,
            edge_type,
            any_type,
        }
        | T::InNeighbours {
            node,
            edge_type,
            any_type,
        } => {
            if *any_type {
                *reads_any = true;
            } else {
                reads.insert(RuleKey::Edge(*edge_type));
            }
            collect_term_reads(arena, *node, reads, reads_any);
        }
        T::Edges {
            node,
            edge_type,
            any_type,
        } => {
            if *any_type {
                *reads_any = true;
            } else {
                reads.insert(RuleKey::Edge(*edge_type));
            }
            collect_term_reads(arena, *node, reads, reads_any);
        }
        T::EdgeAttr { edge, .. } => {
            // RuleKey::Attr denotes node attributes. Edge attributes have a
            // separate storage domain and no access-set key yet, so fail
            // closed until that distinction is represented explicitly.
            *reads_any = true;
            collect_term_reads(arena, *edge, reads, reads_any);
        }
        T::MapNeighbours {
            source,
            edge_type,
            any_type,
        } => {
            if *any_type {
                *reads_any = true;
            } else {
                reads.insert(RuleKey::Edge(*edge_type));
            }
            collect_term_reads(arena, *source, reads, reads_any);
        }
        T::TypeOf { node } => {
            if !LOCAL_OPAQUE_OK.with(|c| c.get()) {
                *reads_any = true;
            }
            collect_term_reads(arena, *node, reads, reads_any);
        }
        T::AttrByName { node, name } => {
            if !LOCAL_OPAQUE_OK.with(|c| c.get()) {
                *reads_any = true;
            }
            collect_term_reads(arena, *node, reads, reads_any);
            collect_term_reads(arena, *name, reads, reads_any);
        }
        // This aggregate scans every live node and inspects each scalar attr
        // key. No finite static resource set can describe its footprint.
        T::ScalarAttrTriples { .. } => {
            *reads_any = true;
        }
        T::HuffmanDecodeStream { .. } | T::HuffmanEncodeStream { .. } | T::Render { .. } => {
            // These terms resolve graph-resident table/render structures at
            // runtime; the actual graph traversal is data-dependent.
            *reads_any = true;
            for child in crate::term::children(arena.get(idx)) {
                collect_term_reads(arena, child, reads, reads_any);
            }
        }
        // These helpers enumerate graph-resident codebooks, registries,
        // mechanisms, cues, or observation populations. Until each helper
        // reports a precise footprint, they are conservative wildcard readers.
        T::ShapeDecode { .. }
        | T::TransformDecode { .. }
        | T::DimInfer { .. }
        | T::GenInfer { .. }
        | T::RatioInduce { .. }
        | T::TimeInfer { .. }
        | T::DepthInfer { .. }
        | T::BlinkBridge { .. }
        | T::GapAbduce { .. }
        | T::GapVerify { .. }
        | T::SupportInfer { .. }
        | T::TransferDecode { .. }
        | T::RecogniseShape { .. }
        | T::MetaShapeMint { .. } => {
            *reads_any = true;
            for child in crate::term::children(arena.get(idx)) {
                collect_term_reads(arena, child, reads, reads_any);
            }
        }
        // These operators can cross the explicit Term-child boundary: Join
        // may invoke graph-backed rendering, ProgEval may decode a program
        // subgraph, Call resolves a derived body dynamically, Holds resolves
        // a concept body dynamically, and UseTool enters an arbitrary
        // reentrant handler. Their complete dependencies are not recoverable
        // from this Term node alone.
        T::Join { .. }
        | T::ProgEval { .. }
        | T::Call { .. }
        | T::Holds { .. }
        | T::UseTool { .. } => {
            *reads_any = true;
            for child in crate::term::children(arena.get(idx)) {
                collect_term_reads(arena, child, reads, reads_any);
            }
        }
        T::MotorCompose { .. }
        | T::FutureManifoldProjection { .. }
        | T::FutureManifoldSelection { .. }
        | T::NetForward { .. }
        | T::EnigmaCrib { .. }
        | T::EnigmaBombe { .. }
        | T::EnigmaBombeWitness { .. }
        | T::TrackIdentityCorrespondence { .. } => {
            // These high-level Terms delegate their graph reads to domain
            // helpers. Their dependencies are dynamic (often edge and
            // attribute scans), so until those helpers report a precise
            // footprint, rule invalidation and frame partitioning must treat
            // them as wildcard readers. Recurse as well: inputs can contain
            // additional explicit Term reads.
            *reads_any = true;
            for child in crate::term::children(arena.get(idx)) {
                collect_term_reads(arena, child, reads, reads_any);
            }
        }
        T::LookaheadValue {
            node,
            child_edge,
            score_key,
            depth,
        } => {
            reads.insert(RuleKey::Edge(*child_edge));
            reads.insert(RuleKey::Attr(*score_key));
            collect_term_reads(arena, *node, reads, reads_any);
            collect_term_reads(arena, *depth, reads, reads_any);
        }
        T::ParetoDominates {
            value_edge,
            measure_edge,
            dimension_key,
            verified_key,
            signed_value_key,
            ..
        } => {
            reads.insert(RuleKey::Edge(*value_edge));
            reads.insert(RuleKey::Edge(*measure_edge));
            reads.insert(RuleKey::Attr(*dimension_key));
            reads.insert(RuleKey::Attr(*verified_key));
            reads.insert(RuleKey::Attr(*signed_value_key));
            for child in crate::term::children(arena.get(idx)) {
                collect_term_reads(arena, child, reads, reads_any);
            }
        }
        T::EvalSubgraph { node } => {
            *reads_any = true;
            collect_term_reads(arena, *node, reads, reads_any);
        }
        // Generic: recurse children (Lit/Var leaves, arithmetic, comparison,
        // boolean, Filter/Sum/MinOver/MaxOver/Count/IfThenElse/Let/Holds/etc.).
        other => {
            for c in crate::term::children(other) {
                collect_term_reads(arena, c, reads, reads_any);
            }
        }
    }
}

/// Collect one effect's writes (+ its computed-arg reads).
fn collect_effect_access(
    eff: &Effect,
    arena: &TermArena,
    reads: &mut rustc_hash::FxHashSet<RuleKey>,
    writes: &mut rustc_hash::FxHashSet<RuleKey>,
    reads_any: &mut bool,
    writes_any: &mut bool,
) {
    let mut read_arg = |a: &EffectArg, r: &mut rustc_hash::FxHashSet<RuleKey>, ra: &mut bool| {
        if let EffectArg::Computed(idx) = a {
            collect_term_reads(arena, *idx, r, ra);
        }
    };
    match eff {
        Effect::AddEdge {
            edge_type, attrs, ..
        } => {
            reads.insert(RuleKey::Edge(*edge_type));
            writes.insert(RuleKey::Edge(*edge_type));
            for (_, a) in attrs {
                read_arg(a, reads, reads_any);
            }
        }
        Effect::DelEdge { edge_type, .. } => {
            reads.insert(RuleKey::Edge(*edge_type));
            writes.insert(RuleKey::Edge(*edge_type));
        }
        Effect::AddNode { type_, attrs, .. } => {
            writes.insert(RuleKey::Type(*type_));
            for (k, a) in attrs {
                writes.insert(RuleKey::Attr(*k));
                read_arg(a, reads, reads_any);
            }
        }
        Effect::AddNodeIfAbsent { type_, attrs, .. } => {
            writes.insert(RuleKey::Type(*type_));
            reads.insert(RuleKey::Type(*type_));
            for (k, a) in attrs {
                reads.insert(RuleKey::Attr(*k));
                writes.insert(RuleKey::Attr(*k));
                read_arg(a, reads, reads_any);
            }
        }
        Effect::SetAttr { key, value, .. } => {
            reads.insert(RuleKey::Attr(*key));
            writes.insert(RuleKey::Attr(*key));
            read_arg(value, reads, reads_any);
        }
        Effect::SetAttrIfDifferent { key, value, .. } => {
            // The effect compares the existing value before deciding whether
            // to write, so this key is both a dependency and a mutation.
            reads.insert(RuleKey::Attr(*key));
            writes.insert(RuleKey::Attr(*key));
            read_arg(value, reads, reads_any);
        }
        Effect::DelNode { .. } | Effect::ReplaceValue { .. } => {
            *reads_any = true;
            *writes_any = true;
        }
        Effect::DefineConcept { name, term } => {
            *writes_any = true;
            read_arg(name, reads, reads_any);
            read_arg(term, reads, reads_any);
        }
        Effect::SetRuleClause {
            rule_name,
            field,
            term,
        } => {
            // mutates the rule list (not the graph) — be conservative for dirtying.
            *reads_any = true;
            *writes_any = true;
            read_arg(rule_name, reads, reads_any);
            read_arg(field, reads, reads_any);
            read_arg(term, reads, reads_any);
        }
        Effect::ApplyRulePatch { .. } => {
            // Reads the bound RulePatch node and mutates both the live rule
            // store and that node's result attrs between passes.
            *reads_any = true;
            *writes_any = true;
        }
        Effect::NetCollapse {
            input, target, eta, ..
        } => {
            // Mutates the net's WeightTensor data (not statically known
            // here) — conservative writes_any like FbSample.
            *writes_any = true;
            read_arg(input, reads, reads_any);
            read_arg(target, reads, reads_any);
            read_arg(eta, reads, reads_any);
        }
        Effect::FbSample {
            fb, grid_w, grid_h, ..
        } => {
            // Queues a sample whose eventual mint/update touches
            // Region + WorldInstance/Cell nodes not statically known
            // here — conservative like DelNode/ReplaceValue/DefineConcept.
            *writes_any = true;
            read_arg(fb, reads, reads_any);
            read_arg(grid_w, reads, reads_any);
            read_arg(grid_h, reads, reads_any);
        }
        Effect::TrackIdentity {
            prev, cur, radius, ..
        } => {
            // Queues an identity assignment whose eventual write set
            // (arbitrary cur nodes' identity_key attr) isn't statically
            // known here — conservative like FbSample.
            *writes_any = true;
            read_arg(prev, reads, reads_any);
            read_arg(cur, reads, reads_any);
            read_arg(radius, reads, reads_any);
        }
    }
}

/// Dense handle for a rule stored in `Substrate::rules`.
#[derive(Copy, Clone, Debug, PartialEq, Eq, Hash)]
pub struct RuleIdx(pub u32);

/// Stable, checkpointed identity for an installed rewrite rule.
///
/// `RuleIdx` remains the dense execution handle and is intentionally preserved
/// for compatibility. `RuleUid` is the address used by self-modification: it
/// survives export/import and never aliases a different rule after tombstoning.
#[derive(Copy, Clone, Debug, Default, PartialEq, Eq, Hash)]
pub struct RuleUid(pub u64);

/// Per-match binding: variable name → resolved NodeID.
pub type Binding = FxHashMap<Sym, NodeID>;

/// One reversible step from applying a rule effect. Stored in the
/// order they were produced so backtracking replays in reverse.
#[derive(Debug)]
pub enum UndoStep {
    /// `apply_rule` added this edge — undo deletes it.
    AddedEdge(EdgeKey),
    /// `apply_rule` replaced attrs on an existing edge — undo restores them.
    EdgeAttrsSet {
        key: EdgeKey,
        old: crate::graph::Attrs,
    },
    /// `apply_rule` deleted an edge — undo re-inserts it with the
    /// original attrs. Used by search algorithms that need to roll
    /// back tentative deletes.
    DeletedEdge {
        src: NodeID,
        edge_type: Sym,
        tgt: NodeID,
        attrs: crate::graph::Attrs,
    },
    /// `apply_rule` added this node — undo deletes it (and any
    /// adjacent edges, via the graph's cascade).
    AddedNode(NodeID),
    /// `apply_rule` overwrote an attr — undo restores the old value
    /// (or removes the attr entirely if it didn't exist before).
    AttrSet {
        nid: NodeID,
        key: Sym,
        old: Option<Value>,
    },
    /// Effect was a `DelNode`. We don't try to restore deleted nodes
    /// — the NodeID would change on re-insertion, so the var-to-NodeID
    /// binding would no longer apply. Marked here for diagnostics; a
    /// caller that wants undoable deletes should mark the node as
    /// retracted via SetAttr instead.
    NodeDeleted,
}

// --- match-edge reorder --------------------------------------------------

/// Greedy cost-based reorder of a rule's match-edges so the matcher
/// always extends from already-bound variables. The "both-unbound first
/// match-edge" case forces a scan over `edges_by_type[edge_type]` —
/// O(all edges of that type) — and is almost always avoidable by
/// picking a different starting edge.
///
/// Algorithm: pick a first edge by lowest `edges_by_type` cardinality
/// (smallest fan-out to scan), then at each subsequent step pick any
/// remaining edge that shares at least one var with the bound set,
/// among ties preferring lower `edges_by_type` cardinality. Falls back
/// to picking any remaining edge (disconnected pattern) if no connection
/// is possible.
///
/// Reorder is structural — it doesn't change the rule's semantics, only
/// the matcher's traversal cost.
pub fn reorder_match_edges(
    edges: &[MatchEdge],
    edges_by_type_card: impl Fn(Sym) -> usize,
) -> Vec<MatchEdge> {
    if edges.len() <= 1 {
        return edges.to_vec();
    }
    let mut remaining: Vec<usize> = (0..edges.len()).collect();
    let mut bound: rustc_hash::FxHashSet<Sym> = Default::default();
    let mut out: Vec<MatchEdge> = Vec::with_capacity(edges.len());

    // Pick the first edge by smallest edges_by_type cardinality — that's
    // the cheapest "both-unbound" scan. If two edges tie, any is fine.
    let first_pos = remaining
        .iter()
        .min_by_key(|&&i| edges_by_type_card(edges[i].edge_type))
        .copied()
        .unwrap();
    let first_idx = remaining.iter().position(|&x| x == first_pos).unwrap();
    let first = remaining.swap_remove(first_idx);
    bound.insert(edges[first].src_var);
    bound.insert(edges[first].tgt_var);
    out.push(edges[first].clone());

    while !remaining.is_empty() {
        // Prefer edges that share at least one var with the bound set.
        // Among connected edges, smallest `edges_by_type` cardinality
        // wins (the matcher's bound-src/bound-tgt path still scans the
        // (node, edge_type) entry, which is bounded by the edge type's
        // global cardinality).
        let connected: Vec<usize> = remaining
            .iter()
            .enumerate()
            .filter(|(_, &i)| {
                bound.contains(&edges[i].src_var) || bound.contains(&edges[i].tgt_var)
            })
            .map(|(rem_idx, _)| rem_idx)
            .collect();
        let pick_rem_idx = if !connected.is_empty() {
            *connected
                .iter()
                .min_by_key(|&&ri| edges_by_type_card(edges[remaining[ri]].edge_type))
                .unwrap()
        } else {
            // Disconnected pattern — pick the smallest cardinality.
            (0..remaining.len())
                .min_by_key(|&ri| edges_by_type_card(edges[remaining[ri]].edge_type))
                .unwrap()
        };
        let pick = remaining.swap_remove(pick_rem_idx);
        bound.insert(edges[pick].src_var);
        bound.insert(edges[pick].tgt_var);
        out.push(edges[pick].clone());
    }

    out
}

/// R10: hint-aware twin of `reorder_match_edges`. When `hints` is empty,
/// delegates to `reorder_match_edges` unchanged (every pre-existing rule,
/// none of which carries a hint, gets byte-identical ordering — this
/// function changes NOTHING for them). When a hint is present, the greedy
/// selection is restricted to "unblocked" edges first: an edge is BLOCKED
/// while it is the `for_var` side of a `BoundAttr` hint whose `via_var` isn't
/// bound yet. This guarantees the edge that binds `via_var` is scheduled
/// before the edge `hinted_candidates` would accelerate — the ordering
/// `IndexJoinHint`'s var-name keying (rather than match-edge position)
/// depends on to actually fire, regardless of authoring order or
/// install-time edge-type cardinality ties. If every remaining edge is
/// blocked (a hint whose `via_var` never appears in another edge, or a
/// genuine cycle), the restriction is dropped for that step so the reorder
/// always terminates — the hint simply won't fire that pass, which is
/// always still CORRECT (falls back to the unindexed scan), only
/// unoptimised.
pub fn reorder_match_edges_with_hints(
    edges: &[MatchEdge],
    hints: &[IndexJoinHint],
    edges_by_type_card: impl Fn(Sym) -> usize,
) -> Vec<MatchEdge> {
    if edges.len() <= 1 || hints.is_empty() {
        return reorder_match_edges(edges, edges_by_type_card);
    }
    let is_blocked = |idx: usize, bound: &rustc_hash::FxHashSet<Sym>| -> bool {
        let e = &edges[idx];
        hints.iter().any(|h| {
            (h.for_var == e.src_var || h.for_var == e.tgt_var)
                && matches!(&h.probe, IndexProbe::BoundAttr { via_var, .. } if !bound.contains(via_var))
        })
    };

    let mut remaining: Vec<usize> = (0..edges.len()).collect();
    let mut bound: rustc_hash::FxHashSet<Sym> = Default::default();
    let mut out: Vec<MatchEdge> = Vec::with_capacity(edges.len());

    while !remaining.is_empty() {
        let unblocked: Vec<usize> = remaining
            .iter()
            .copied()
            .filter(|&i| !is_blocked(i, &bound))
            .collect();
        let pool: Vec<usize> = if unblocked.is_empty() {
            remaining.clone()
        } else {
            unblocked
        };

        let connected: Vec<usize> = pool
            .iter()
            .copied()
            .filter(|&i| bound.contains(&edges[i].src_var) || bound.contains(&edges[i].tgt_var))
            .collect();
        let choice_set: &[usize] = if bound.is_empty() || connected.is_empty() {
            &pool
        } else {
            &connected
        };
        let pick = *choice_set
            .iter()
            .min_by_key(|&&i| edges_by_type_card(edges[i].edge_type))
            .unwrap();
        remaining.retain(|&i| i != pick);
        bound.insert(edges[pick].src_var);
        bound.insert(edges[pick].tgt_var);
        out.push(edges[pick].clone());
    }
    out
}

// --- matcher --------------------------------------------------------------

/// Find one binding satisfying `rule.match_edges` + `rule.where_`, or
/// `None` if no match exists. Backtracking DFS — same algorithm as
/// the Python `_match`, with the same "variables must be distinct
/// nodes" check at the leaf. Convenience wrapper over
/// `match_rule_each` for the common "give me one match" case.
pub fn match_rule(
    rule: &RewriteRule,
    arena: &TermArena,
    graph: &TypedGraph,
    interner: &Interner,
    concepts: Option<&ConceptResolver>,
    framebuffers: Option<&crate::framebuffer::FbRegistry>,
) -> Option<Binding> {
    let mut out: Option<Binding> = None;
    match_rule_each(
        rule,
        arena,
        graph,
        interner,
        concepts,
        framebuffers,
        None,
        None,
        |b| {
            out = Some(b.clone());
            // Stop after the first match.
            false
        },
    );
    out
}

/// Visit every binding satisfying the rule's pattern + where-clause.
/// `visit` returns `true` to keep enumerating, `false` to stop.
/// Used by `run_rules` to walk past no-op bindings until a
/// progressing one is found — the canonical fix for the
/// "transitive-closure rule keeps re-matching the same no-op
/// binding" trap.
pub fn match_rule_each<F>(
    rule: &RewriteRule,
    arena: &TermArena,
    graph: &TypedGraph,
    interner: &Interner,
    concepts: Option<&ConceptResolver>,
    framebuffers: Option<&crate::framebuffer::FbRegistry>,
    cache: Option<&mut crate::term::EvalCache>,
    where_jit: Option<&crate::jit::CompiledWhere>,
    mut visit: F,
) where
    F: FnMut(&Binding) -> bool,
{
    let _access_rule = crate::access_trace::enter_rule(rule.uid.0, graph as *const TypedGraph as usize);
    let mut binding: Binding = FxHashMap::default();
    extend_each(
        rule,
        0,
        &mut binding,
        arena,
        graph,
        interner,
        concepts,
        framebuffers,
        cache,
        where_jit,
        0u64,
        &mut visit,
    );
}

/// Like `match_rule_each` but with a pre-seeded binding. Used by the
/// substrate's semi-naive matcher to drive enumeration from one
/// already-bound match-edge (the "delta" edge): the substrate fills in
/// the driver's vars, then calls this with the rule's REMAINING
/// match-edges. extend_each treats already-bound vars as constraints
/// (it filters candidates by the bound value), so the semantics are
/// "find all bindings extending `initial`."
pub fn match_rule_each_with_initial<F>(
    rule: &RewriteRule,
    initial: &Binding,
    arena: &TermArena,
    graph: &TypedGraph,
    interner: &Interner,
    concepts: Option<&ConceptResolver>,
    framebuffers: Option<&crate::framebuffer::FbRegistry>,
    cache: Option<&mut crate::term::EvalCache>,
    where_jit: Option<&crate::jit::CompiledWhere>,
    mut visit: F,
) where
    F: FnMut(&Binding) -> bool,
{
    let _access_rule = crate::access_trace::enter_rule(rule.uid.0, graph as *const TypedGraph as usize);
    let mut binding: Binding = initial.clone();
    extend_each(
        rule,
        0,
        &mut binding,
        arena,
        graph,
        interner,
        concepts,
        framebuffers,
        cache,
        where_jit,
        0u64,
        &mut visit,
    );
}

/// Join-index fast path for a match edge: if this edge's `src_var` or
/// `tgt_var` is the `for_var` of an index hint and its probe value is
/// available (literal or bound attribute), probe the declared attr index for
/// candidates instead of scanning the full edge neighborhood or edge type.
/// Returns `None` (caller falls back to the full scan) unless
/// EVERY precondition holds: a matching hint exists, a dynamic probe's
/// source node and attribute are available, and the attr index is declared.
/// A rule without an activated index falls back to its ordinary scan.
///
/// CORRECTNESS: every hit is checked for the indexed attr value and every
/// returned pair is verified as a REAL `edge_type` edge via adjacency for
/// unbound endpoints or O(1) `has_edge` for a bound endpoint. A missing
/// index takes the ordinary path; index completeness relies on TypedGraph's
/// insert/update/delete maintenance invariant.
fn hinted_candidates(
    rule: &RewriteRule,
    src_var: Sym,
    edge_type: Sym,
    tgt_var: Sym,
    binding: &Binding,
    graph: &TypedGraph,
) -> Option<Vec<(NodeID, NodeID)>> {
    let hint = rule
        .index_hints
        .iter()
        .find(|h| h.for_var == tgt_var || h.for_var == src_var)?;
    if !graph.has_attr_index(hint.node_type, hint.this_key) {
        return None;
    }
    let probe_value = match &hint.probe {
        IndexProbe::BoundAttr { via_var, via_key } => {
            let via_nid = *binding.get(via_var)?;
            graph.node(via_nid).attrs.get(via_key)?.clone()
        }
        IndexProbe::LiteralString(value) => Value::Str(*value),
    };
    let hits = graph.nodes_where(hint.node_type, hint.this_key, &probe_value);
    let mut out = Vec::with_capacity(hits.len());
    if hint.for_var == tgt_var {
        for t in hits {
            if graph.node(t).type_ != hint.node_type
                || graph.node(t).attrs.get(&hint.this_key) != Some(&probe_value)
            {
                continue;
            }
            if let Some(s) = binding.get(&src_var).copied() {
                if graph.has_edge(s, edge_type, t) {
                    out.push((s, t));
                }
            } else {
                for s in graph.in_neighbours(t, Some(edge_type)) {
                    out.push((s, t));
                }
            }
        }
    } else {
        for s in hits {
            if graph.node(s).type_ != hint.node_type
                || graph.node(s).attrs.get(&hint.this_key) != Some(&probe_value)
            {
                continue;
            }
            if let Some(t) = binding.get(&tgt_var).copied() {
                if graph.has_edge(s, edge_type, t) {
                    out.push((s, t));
                }
            } else {
                for t in graph.neighbours(s, Some(edge_type)) {
                    out.push((s, t));
                }
            }
        }
    }
    Some(out)
}

fn extend_each<F>(
    rule: &RewriteRule,
    i: usize,
    binding: &mut Binding,
    arena: &TermArena,
    graph: &TypedGraph,
    interner: &Interner,
    concepts: Option<&ConceptResolver>,
    framebuffers: Option<&crate::framebuffer::FbRegistry>,
    mut cache: Option<&mut crate::term::EvalCache>,
    where_jit: Option<&crate::jit::CompiledWhere>,
    mut pushed: u64,
    visit: &mut F,
) -> bool
where
    F: FnMut(&Binding) -> bool,
{
    if i == rule.match_edges.len() {
        // Variables must resolve to distinct nodes — drop bindings
        // where two vars collided to the same node.
        let mut seen: SmallVec<[NodeID; 8]> = SmallVec::new();
        for &v in binding.values() {
            if seen.contains(&v) {
                crate::scale_audit::var_collision();
                return true; // continue enumeration
            }
            seen.push(v);
        }
        // Where-clause side condition — JIT fast path if available,
        // interpreter otherwise. Both produce the same true/false answer.
        if let Some(where_idx) = rule.where_ {
            if let Some(cw) = where_jit {
                // JIT: collect NodeIDs from binding in the var-order the
                // JIT expects, pass them as i64 args alongside a ctx that
                // points at the graph for any TypeOf/Attr/Count thunks.
                let mut args: smallvec::SmallVec<[i64; 5]> = smallvec::SmallVec::new();
                for var in &cw.var_order {
                    let v: i64 = binding.get(var).map(|n| n.0 as i64).unwrap_or(0);
                    args.push(v);
                }
                let jit_ctx = crate::jit::JitCtx::from_graph(graph);
                let ok = cw.jit.call_with_ctx(&jit_ctx, args.as_slice()) != 0;
                crate::scale_audit::where_eval(ok);
                if !ok {
                    return true; // continue — where failed
                }
            } else {
                let mut env: Env = SmallVec::new();
                for (&name, &nid) in binding.iter() {
                    env.push((name, Value::Node(nid)));
                }
                let mut ctx = EvalCtx::new(graph, interner);
                if let Some(c) = concepts {
                    ctx = ctx.with_concepts(c);
                }
                if let Some(fb) = framebuffers {
                    ctx = ctx.with_framebuffers(fb);
                }
                if let Some(c) = cache.as_deref_mut() {
                    ctx = ctx.with_cache(c);
                }
                if rule.where_conjuncts.is_empty() {
                    // No pushdown plan — evaluate the where whole, as always.
                    let ok = evaluate(arena, where_idx, &mut env, &mut ctx).truthy();
                    crate::scale_audit::where_eval(ok);
                    if !ok {
                        return true; // continue
                    }
                } else {
                    // Pushdown plan: every conjunct already decided at a
                    // shallower level is TRUE (a false one returned there).
                    // Evaluate exactly the remainder — same conjunction, each
                    // conjunct evaluated exactly once.
                    for (ci, (cidx, _)) in rule.where_conjuncts.iter().enumerate() {
                        if pushed & (1u64 << ci.min(63)) != 0 {
                            continue;
                        }
                        let ok = evaluate(arena, *cidx, &mut env, &mut ctx).truthy();
                        crate::scale_audit::where_eval(ok);
                        if !ok {
                            return true; // continue
                        }
                    }
                }
            }
        }
        // Concrete successful pattern footprint. This is a logical binding
        // trace, separate from the candidate-enumeration counters above.
        for edge in &rule.match_edges {
            if let (Some(&src), Some(&tgt)) =
                (binding.get(&edge.src_var), binding.get(&edge.tgt_var))
            {
                crate::access_trace::note(1, src.0, edge.edge_type.0, tgt.0);
            }
        }
        crate::scale_audit::leaf_visit();
        return visit(binding);
    }
    // PREDICATE PUSHDOWN: decide every conjunct whose vars are ALL bound
    // NOW, before expanding this match-edge — a conjunct that reads only an
    // already-bound var cannot become true by binding more vars, so failing
    // it here prunes the entire subtree. Off unless `derive_pushdown` built a
    // plan (multi-edge + top-level `And`), and off on the JIT path (which
    // evaluates the where whole). See `RewriteRule::where_conjuncts`.
    if where_jit.is_none() && !rule.where_conjuncts.is_empty() {
        for (ci, (cidx, cvars)) in rule.where_conjuncts.iter().enumerate() {
            if pushed & (1u64 << ci.min(63)) != 0 {
                continue; // already decided at a shallower level
            }
            if cvars.is_empty() || !cvars.iter().all(|v| binding.contains_key(v)) {
                continue; // not yet decidable (or has no vars — leave to leaf)
            }
            let mut env: Env = SmallVec::new();
            for (&name, &nid) in binding.iter() {
                env.push((name, Value::Node(nid)));
            }
            let mut ctx = EvalCtx::new(graph, interner);
            if let Some(c) = concepts {
                ctx = ctx.with_concepts(c);
            }
            if let Some(fb) = framebuffers {
                ctx = ctx.with_framebuffers(fb);
            }
            if let Some(c) = cache.as_deref_mut() {
                ctx = ctx.with_cache(c);
            }
            let ok = evaluate(arena, *cidx, &mut env, &mut ctx).truthy();
            crate::scale_audit::pushdown_eval(!ok);
            if !ok {
                return true; // prune: continue enumeration at the caller
            }
            pushed |= 1u64 << ci.min(63);
        }
    }

    let MatchEdge {
        src_var,
        edge_type,
        tgt_var,
    } = &rule.match_edges[i];
    let bound_src = binding.get(src_var).copied();
    let bound_tgt = binding.get(tgt_var).copied();

    // SCALE AUDIT (`scale_audit.rs`): record whether candidates came from
    // local adjacency, an index hint, or a global edge-type scan.
    let mut cand_path = crate::scale_audit::CandPath::Local;
    let candidates: Vec<(NodeID, NodeID)> = match (bound_src, bound_tgt) {
        (Some(s), None) => {
            match hinted_candidates(rule, *src_var, *edge_type, *tgt_var, binding, graph) {
                Some(c) => {
                    cand_path = crate::scale_audit::CandPath::Hinted;
                    c
                }
                None => graph
                    .neighbours(s, Some(*edge_type))
                    .into_iter()
                    .map(|t| (s, t))
                    .collect(),
            }
        }
        (None, Some(t)) => {
            match hinted_candidates(rule, *src_var, *edge_type, *tgt_var, binding, graph) {
                Some(c) => {
                    cand_path = crate::scale_audit::CandPath::Hinted;
                    c
                }
                None => graph
                    .in_neighbours(t, Some(*edge_type))
                    .into_iter()
                    .map(|s| (s, t))
                    .collect(),
            }
        }
        (Some(s), Some(t))
            if rule.both_bound_probe
                && graph.in_edges_slice(t, Some(*edge_type)).len()
                    < graph.out_edges_slice(s, Some(*edge_type)).len() =>
        {
            graph
                .in_neighbours(t, Some(*edge_type))
                .into_iter()
                .filter(|x| *x == s)
                .map(|x| (x, t))
                .collect()
        }
        (Some(s), Some(_)) => graph
            .neighbours(s, Some(*edge_type))
            .into_iter()
            .map(|t| (s, t))
            .collect(),
        // R10: for a both-unbound edge, an active hint avoids the
        // edge-type scan; index-then-verify keeps correctness independent
        // of the index contents.
        (None, None) => {
            match hinted_candidates(rule, *src_var, *edge_type, *tgt_var, binding, graph) {
                Some(c) => {
                    cand_path = crate::scale_audit::CandPath::Hinted;
                    c
                }
                None => {
                    cand_path = crate::scale_audit::CandPath::Scan;
                    // O(matches) via the edges-by-type index — was O(total
                    // edges) before, which made every rule with an unbound
                    // first match clause scan the entire graph each tick.
                    graph
                        .edges_by_type(*edge_type)
                        .iter()
                        .map(|idx| {
                            let key = graph.edge(*idx).key();
                            (key.src, key.tgt)
                        })
                        .collect()
                }
            }
        }
    };
    crate::scale_audit::candidates(candidates.len() as u64, cand_path);

    for (s, t) in candidates {
        crate::scale_audit::cand_tested(i, rule.name.0, rule.match_edges.len());
        if let Some(bs) = bound_src {
            if bs != s {
                crate::scale_audit::cand_reject_bound();
                continue;
            }
        }
        if let Some(bt) = bound_tgt {
            if bt != t {
                crate::scale_audit::cand_reject_bound();
                continue;
            }
        }
        let prev_src = binding.insert(*src_var, s);
        let prev_tgt = binding.insert(*tgt_var, t);
        let keep_going = extend_each(
            rule,
            i + 1,
            binding,
            arena,
            graph,
            interner,
            concepts,
            framebuffers,
            cache.as_deref_mut(),
            where_jit,
            pushed,
            visit,
        );
        match prev_src {
            Some(v) => {
                binding.insert(*src_var, v);
            }
            None => {
                binding.remove(src_var);
            }
        }
        match prev_tgt {
            Some(v) => {
                binding.insert(*tgt_var, v);
            }
            None => {
                binding.remove(tgt_var);
            }
        }
        if !keep_going {
            return false;
        }
    }
    true
}

// --- applier --------------------------------------------------------------

/// Outcome of applying a rule — `progressed` is true iff at least one
/// effect actually changed the graph (an `AddEdge` insertion or attribute
/// replacement, a `SetAttr` that changed the value, an `AddNode` or
/// `DelEdge` or `DelNode`). `run_rules` uses this to terminate the
/// fixed-point loop when a rule keeps matching but is no longer
/// producing change — the canonical termination test for
/// transitive-closure-shaped rewrite systems.
pub struct ApplyOutcome {
    pub undo: Vec<UndoStep>,
    /// Index into `rule.effects` of the effect that produced each `undo` step,
    /// parallel to `undo`. Lets a caller recover a forward delta that preserves
    /// each effect's own semantics — notably whether an inserted node came from
    /// a conditional `AddNodeIfAbsent` or an unconditional `AddNode`.
    pub undo_src: Vec<u32>,
    pub progressed: bool,
    /// Concept definitions produced by `Effect::DefineConcept` during
    /// this apply. The applier collects (name, term) pairs here rather
    /// than mutating `ConceptResolver` directly so its `&` borrow
    /// (consulted by `evaluate` for `Holds` resolution while effects
    /// fire) doesn't clash with the eventual write. The caller (e.g.
    /// `Substrate::apply_rule_once` / `Substrate::run_rules`) installs
    /// these via `define_concept` after the apply returns.
    pub pending_concepts: Vec<(Sym, TermIdx)>,
}

/// Apply a rule's effects under `binding`. New nodes produced by
/// Coerce a string-*shaped* `Value` to an owned `String`, accepting both
/// a frozen `Value::Str(Sym)` (the rule-literal / plain-attr case) and a
/// `Value::Surface(SurfaceKind::Text, ...)` (what `StringConcat` and the
/// other text-producing Terms evaluate to). Mirrors the coercion
/// `TermNode::TextShape` / `MkDict` already use in term.rs so a
/// dynamically-built name (e.g. `StringConcat(["prefix_", Attr(...)])`)
/// is treated the same as a literal one everywhere a rule/field NAME is
/// consumed, instead of being silently rejected because it isn't
/// `Value::Str` exactly. Returns `None` for anything that isn't
/// string-shaped at all (Int, Dict, Node, ...) -- callers are expected to
/// surface that case loudly rather than drop it.
fn value_as_str_like(v: &Value, interner: &Interner) -> Option<String> {
    match v {
        Value::Str(sym) => Some(interner.resolve(*sym).to_string()),
        Value::Surface(SurfaceKind::Text, bytes) => {
            Some(String::from_utf8_lossy(bytes).into_owned())
        }
        _ => None,
    }
}

/// `AddNode` extend the binding so subsequent effects in the same
/// rule can reference them.
///
/// `record_undo: true` collects UndoStep entries so a backtracking
/// search can replay them in reverse (matches `apply_rule_recording`
/// in the Python). `false` runs the effects without bookkeeping —
/// cheaper, what `run_rules` uses for fixed-point rewriting.
pub fn apply_rule(
    rule: &RewriteRule,
    binding: &Binding,
    arena: &mut TermArena,
    graph: &mut TypedGraph,
    interner: &mut Interner,
    concepts: Option<&mut ConceptResolver>,
    framebuffers: Option<&crate::framebuffer::FbRegistry>,
    record_undo: bool,
) -> Vec<UndoStep> {
    apply_rule_full(
        rule,
        binding,
        arena,
        graph,
        interner,
        concepts,
        framebuffers,
        None,
        record_undo,
    )
    .undo
}

/// Same as `apply_rule` but returns the full outcome including
/// whether any effect actually changed the graph. Used by `run_rules`
/// to know when to stop.
pub fn apply_rule_full(
    rule: &RewriteRule,
    binding: &Binding,
    arena: &mut TermArena,
    graph: &mut TypedGraph,
    interner: &mut Interner,
    mut concepts: Option<&mut ConceptResolver>,
    framebuffers: Option<&crate::framebuffer::FbRegistry>,
    cache: Option<&mut crate::term::EvalCache>,
    record_undo: bool,
) -> ApplyOutcome {
    let _access_rule = crate::access_trace::enter_rule(rule.uid.0, graph as *const TypedGraph as usize);
    // Effect values in one rule firing form one atomic explanatory frame.
    // Keep expensive SD reports across sibling field projections, while
    // clearing traversal memo before every effect so ordinary graph reads see
    // mutations made by the previous effect. SD keys fingerprint their typed
    // codebooks, so a codebook grown by an earlier effect is visible
    // immediately while unrelated writes retain the report.
    // Reuse the substrate-owned allocation on the normal path. Batch/direct
    // callers that deliberately provide no cache still get firing-local SD
    // common-subexpression elimination through the fallback.
    let mut fallback_cache = None;
    let mut cache = Some(match cache {
        Some(cache) => cache,
        None => fallback_cache.insert(crate::term::EvalCache::default()),
    });
    cache.as_deref_mut().unwrap().clear_sd_ops();
    let mut b: Binding = binding.clone();
    let mut undo: Vec<UndoStep> = Vec::new();
    // Which EFFECT produced each undo step, parallel to `undo`. A proposal has
    // to know this: `AddNodeIfAbsent` and `AddNode` both emit
    // `UndoStep::AddedNode`, so a forward delta reconstructed from the undo log
    // alone cannot tell a CONDITIONAL insert from an unconditional one and will
    // silently flatten the condition away (`stage_a.rs`).
    //
    // Filled at the TOP of each iteration for the PREVIOUS effect, and once
    // more after the loop — several effect arms `continue`, so attributing at
    // the bottom would desync the two vectors on exactly those paths.
    let mut undo_src: Vec<u32> = Vec::new();
    let mut cur_effect: u32 = 0;
    let mut progressed = false;
    let mut pending_concepts: Vec<(Sym, TermIdx)> = Vec::new();
    for (effect_idx, effect) in rule.effects.iter().enumerate() {
        undo_src.resize(undo.len(), cur_effect);
        cur_effect = effect_idx as u32;
        if let Some(c) = cache.as_deref_mut() {
            c.clear_traversal();
        }
        match effect {
            Effect::AddEdge {
                src_var,
                edge_type,
                tgt_var,
                attrs,
            } => {
                let (Some(&s), Some(&t)) = (b.get(src_var), b.get(tgt_var)) else {
                    continue;
                };
                let mut attr_map: FxHashMap<Sym, Value> = FxHashMap::default();
                for (k, arg) in attrs {
                    let v = resolve_effect_arg(
                        arg,
                        &b,
                        arena,
                        graph,
                        interner,
                        concepts.as_deref(),
                        framebuffers,
                        cache.as_deref_mut(),
                    );
                    attr_map.insert(*k, v);
                }
                let key = EdgeKey {
                    src: s,
                    edge_type: *edge_type,
                    tgt: t,
                };
                crate::access_trace::note(5, s.0, edge_type.0, t.0);
                crate::access_trace::note(28, s.0, edge_type.0, t.0);
                let existing_idx = graph.edge_idx(s, *edge_type, t);
                let pre_exists = existing_idx.is_some();
                let old_attrs = existing_idx.map(|idx| graph.edge_attrs(idx).clone());
                let attrs_changed = old_attrs.as_ref().map_or(true, |old| {
                    old.len() != attr_map.len()
                        || attr_map
                            .iter()
                            .any(|(key, value)| old.get(key) != Some(value))
                });
                // The Result was previously discarded. `insert_edge` fails when
                // an endpoint is absent, which is reachable inside one firing
                // (an earlier effect may have deleted the node this one binds).
                // Discarding it credited `progressed` and pushed an undo step
                // for a mutation that never happened — see `effect_audit.rs`.
                crate::scale_audit::rule_effect_edge_insert_attempt();
                let inserted = graph.insert_edge(s, *edge_type, t, attr_map);
                let failed = inserted.is_err();
                if failed {
                    crate::effect_audit::record_failed_edge_insert(!pre_exists, || {
                        format!(
                            "AddEdge rule={:?} src={:?} edge_type={:?} tgt={:?} err={:?}",
                            rule.name, s, edge_type, t, inserted
                        )
                    });
                }
                // The correction landed opt-in and was enabled by default once
                // the counter measured the path at zero on real workloads; see
                // effect_audit's module note.
                let suppress = failed && crate::effect_audit::correct_failed_effects();
                if !pre_exists && !suppress {
                    progressed = true;
                    if record_undo {
                        undo.push(UndoStep::AddedEdge(key));
                    }
                } else if pre_exists && attrs_changed {
                    progressed = true;
                    if record_undo {
                        undo.push(UndoStep::EdgeAttrsSet {
                            key,
                            old: old_attrs.expect("pre-existing edge must have attrs snapshot"),
                        });
                    }
                }
            }
            Effect::DelEdge {
                src_var,
                edge_type,
                tgt_var,
            } => {
                let (Some(&s), Some(&t)) = (b.get(src_var), b.get(tgt_var)) else {
                    continue;
                };
                crate::access_trace::note(28, s.0, edge_type.0, t.0);
                let Some(idx) = graph.edge_idx(s, *edge_type, t) else {
                    continue;
                };
                crate::access_trace::note(6, s.0, edge_type.0, t.0);
                let pre_attrs = if record_undo {
                    graph.edge_attrs(idx).clone()
                } else {
                    crate::graph::Attrs::new()
                };
                crate::scale_audit::rule_effect_edge_delete();
                graph.delete_edge(idx);
                progressed = true;
                if record_undo {
                    undo.push(UndoStep::DeletedEdge {
                        src: s,
                        edge_type: *edge_type,
                        tgt: t,
                        attrs: pre_attrs,
                    });
                }
            }
            Effect::SetRuleClause {
                rule_name,
                field,
                term,
            } => {
                // INTRINSIC SELF-REPAIR: queue a rule-clause rewrite. We only hold &mut graph here
                // (not the rule list), so resolve the args and stash the edit on graph.pending_rule_edits;
                // Substrate::run_rules drains + applies it between passes where &mut self.rules is free.
                let name_v = resolve_effect_arg(
                    rule_name,
                    &b,
                    arena,
                    graph,
                    interner,
                    concepts.as_deref(),
                    framebuffers,
                    cache.as_deref_mut(),
                );
                let field_v = resolve_effect_arg(
                    field,
                    &b,
                    arena,
                    graph,
                    interner,
                    concepts.as_deref(),
                    framebuffers,
                    cache.as_deref_mut(),
                );
                let term_v = resolve_effect_arg(
                    term,
                    &b,
                    arena,
                    graph,
                    interner,
                    concepts.as_deref(),
                    framebuffers,
                    cache.as_deref_mut(),
                );
                // Accept a `Value::Str` literal OR a `Value::Surface(Text)`
                // (StringConcat / other text Terms) for both the rule name
                // and the field name -- a dynamically-composed mint id must
                // not be rejected just because it wasn't a frozen Sym.
                match (
                    value_as_str_like(&name_v, interner),
                    value_as_str_like(&field_v, interner),
                ) {
                    (Some(name_s), Some(field_s)) => {
                        graph.pending_rule_edits.push((name_s, field_s, term_v));
                        crate::scale_audit::deferred_queue_enqueued("rule_edits");
                        progressed = true;
                    }
                    _ => {
                        // LOUD, never silent: a self-authoring rule tried to
                        // mint/rewrite a rule clause with a name or field
                        // that isn't string-shaped at all (neither Str nor
                        // Surface(Text)) -- e.g. an Int or Dict landed where
                        // a name was expected. Matches the "[self-repair]"
                        // diagnostic convention `apply_pending_rule_edits`
                        // (substrate.rs) already uses for this same queue.
                        eprintln!(
                            "[self-repair] SetRuleClause: rule_name/field did not resolve to a \
                             string-shaped value (name={:?}, field={:?}) -- mint/rewrite skipped",
                            name_v, field_v
                        );
                    }
                }
            }
            Effect::ApplyRulePatch { patch_var } => {
                // The RulePatch node is graph data: the agent authors the
                // target UID, expected revision/hash and proposed clause.
                // Only queue its identity here. The substrate owns the live
                // rule store and performs the CAS transaction between passes.
                if let Some(&patch) = b.get(patch_var) {
                    if !graph.pending_rule_patches.contains(&patch) {
                        graph.pending_rule_patches.push(patch);
                        crate::scale_audit::deferred_queue_enqueued("rule_patches");
                    }
                    progressed = true;
                } else {
                    eprintln!(
                        "[self-repair] ApplyRulePatch: patch var {:?} was not bound",
                        interner.resolve(*patch_var)
                    );
                }
            }
            Effect::NetCollapse {
                reflex_net,
                input,
                target,
                eta,
            } => {
                // SELF-TRAINING: the applier only holds &mut graph (not &mut
                // Substrate), so resolve args under the binding and QUEUE the
                // collapse; Substrate::run_rules drains graph.pending_net_collapses
                // between passes via net_forward::net_collapse_step. Mirrors
                // Effect::FbSample's queue-and-drain exactly.
                let Some(&rn) = b.get(reflex_net) else {
                    continue;
                };
                let in_v = resolve_effect_arg(
                    input,
                    &b,
                    arena,
                    graph,
                    interner,
                    concepts.as_deref(),
                    framebuffers,
                    cache.as_deref_mut(),
                );
                let tg_v = resolve_effect_arg(
                    target,
                    &b,
                    arena,
                    graph,
                    interner,
                    concepts.as_deref(),
                    framebuffers,
                    cache.as_deref_mut(),
                );
                let eta_v = resolve_effect_arg(
                    eta,
                    &b,
                    arena,
                    graph,
                    interner,
                    concepts.as_deref(),
                    framebuffers,
                    cache.as_deref_mut(),
                );
                let to_vec = |v: &Value| -> Vec<f64> {
                    match v {
                        Value::Tuple(t) | Value::List(t) => t
                            .iter()
                            .map(|x| match x {
                                Value::Float(f) => *f,
                                Value::Int(i) => *i as f64,
                                _ => 0.0,
                            })
                            .collect(),
                        Value::Set(s) | Value::FrozenSet(s) => s
                            .iter()
                            .map(|x| match x {
                                Value::Float(f) => *f,
                                Value::Int(i) => *i as f64,
                                _ => 0.0,
                            })
                            .collect(),
                        _ => Vec::new(),
                    }
                };
                let eta_f = match eta_v {
                    Value::Float(f) => f,
                    Value::Int(i) => i as f64,
                    _ => 0.0,
                };
                let inv = to_vec(&in_v);
                let tgv = to_vec(&tg_v);
                if !inv.is_empty() && !tgv.is_empty() && eta_f > 0.0 {
                    graph.pending_net_collapses.push((rn, inv, tgv, eta_f));
                    crate::scale_audit::deferred_queue_enqueued("net_collapses");
                    progressed = true;
                }
            }
            Effect::FbSample {
                fb,
                game_var,
                grid_w,
                grid_h,
            } => {
                // PERCEPTION-AS-ACTION: the applier only holds &mut graph
                // (not &mut Substrate, which owns the framebuffer registry
                // + the dirty-tracking node/edge helpers segment_and_track
                // needs), so resolve args under the binding and QUEUE the
                // sample; Substrate::run_rules drains graph.pending_fb_samples
                // between passes (where &mut self is free) via the same
                // Substrate::fb_sample the PyO3 method calls.
                let Some(&game) = b.get(game_var) else {
                    continue;
                };
                let fb_v = resolve_effect_arg(
                    fb,
                    &b,
                    arena,
                    graph,
                    interner,
                    concepts.as_deref(),
                    framebuffers,
                    cache.as_deref_mut(),
                );
                let gw_v = resolve_effect_arg(
                    grid_w,
                    &b,
                    arena,
                    graph,
                    interner,
                    concepts.as_deref(),
                    framebuffers,
                    cache.as_deref_mut(),
                );
                let gh_v = resolve_effect_arg(
                    grid_h,
                    &b,
                    arena,
                    graph,
                    interner,
                    concepts.as_deref(),
                    framebuffers,
                    cache.as_deref_mut(),
                );
                let fb_id = match fb_v {
                    Value::Int(i) if i >= 0 => Some(i as u32),
                    Value::Float(f) if f >= 0.0 => Some(f as u32),
                    _ => None,
                };
                let gw = match gw_v {
                    Value::Int(i) if i > 0 => Some(i as usize),
                    Value::Float(f) if f > 0.0 => Some(f as usize),
                    _ => None,
                };
                let gh = match gh_v {
                    Value::Int(i) if i > 0 => Some(i as usize),
                    Value::Float(f) if f > 0.0 => Some(f as usize),
                    _ => None,
                };
                if let (Some(fb_id), Some(gw), Some(gh)) = (fb_id, gw, gh) {
                    graph.pending_fb_samples.push((fb_id, game, gw, gh));
                    crate::scale_audit::deferred_queue_enqueued("fb_samples");
                    progressed = true;
                }
            }
            Effect::TrackIdentity {
                prev,
                cur,
                feature_key,
                category_key,
                extent_key,
                identity_key,
                radius,
            } => {
                // GRAPH LAW #6: mirrors Effect::FbSample's queue-and-
                // drain-between-passes pattern exactly — resolve args
                // under the binding, queue onto graph.pending_track_identity;
                // Substrate::run_rules drains it via Substrate::track_identity
                // (where &mut self is free) between passes.
                let prev_v = resolve_effect_arg(
                    prev,
                    &b,
                    arena,
                    graph,
                    interner,
                    concepts.as_deref(),
                    framebuffers,
                    cache.as_deref_mut(),
                );
                let cur_v = resolve_effect_arg(
                    cur,
                    &b,
                    arena,
                    graph,
                    interner,
                    concepts.as_deref(),
                    framebuffers,
                    cache.as_deref_mut(),
                );
                let radius_v = resolve_effect_arg(
                    radius,
                    &b,
                    arena,
                    graph,
                    interner,
                    concepts.as_deref(),
                    framebuffers,
                    cache.as_deref_mut(),
                );
                let prev_ids: Vec<NodeID> = prev_v
                    .iter()
                    .filter_map(|v| match v {
                        Value::Node(n) => Some(*n),
                        _ => None,
                    })
                    .collect();
                let cur_ids: Vec<NodeID> = cur_v
                    .iter()
                    .filter_map(|v| match v {
                        Value::Node(n) => Some(*n),
                        _ => None,
                    })
                    .collect();
                if !cur_ids.is_empty() || !prev_ids.is_empty() {
                    graph.pending_track_identity.push((
                        prev_ids,
                        cur_ids,
                        *feature_key,
                        *category_key,
                        *extent_key,
                        *identity_key,
                        radius_v.as_f64(),
                    ));
                    crate::scale_audit::deferred_queue_enqueued("track_identity");
                    progressed = true;
                }
            }
            Effect::AddNode {
                new_var,
                type_,
                attrs,
            } => {
                let mut attr_map: FxHashMap<Sym, Value> = FxHashMap::default();
                for (k, arg) in attrs {
                    let v = resolve_effect_arg(
                        arg,
                        &b,
                        arena,
                        graph,
                        interner,
                        concepts.as_deref(),
                        framebuffers,
                        cache.as_deref_mut(),
                    );
                    attr_map.insert(*k, v);
                }
                crate::scale_audit::rule_effect_node_insert();
                let nid = graph.insert_node(*type_, attr_map);
                crate::access_trace::note(7, nid.0, type_.0, crate::access_trace::NO_ID);
                b.insert(*new_var, nid);
                progressed = true;
                if record_undo {
                    undo.push(UndoStep::AddedNode(nid));
                }
            }
            Effect::AddNodeIfAbsent {
                new_var,
                type_,
                attrs,
            } => {
                // Resolve the attrs first so the dedup comparison sees
                // concrete Values rather than unresolved Terms.
                let mut attr_pairs: Vec<(Sym, Value)> = Vec::with_capacity(attrs.len());
                for (k, arg) in attrs {
                    let v = resolve_effect_arg(
                        arg,
                        &b,
                        arena,
                        graph,
                        interner,
                        concepts.as_deref(),
                        framebuffers,
                        cache.as_deref_mut(),
                    );
                    attr_pairs.push((*k, v));
                }
                crate::access_trace::note(
                    9,
                    crate::access_trace::NO_ID,
                    type_.0,
                    crate::access_trace::NO_ID,
                );
                // Scan the typed-node index for the first existing node
                // whose attrs include EVERY (k, v) pair we're about to
                // insert. Subset semantics: existing nodes may carry
                // additional attrs the AddNodeIfAbsent author didn't
                // mention; the author's attrs ARE the dedup key.
                let mut found: Option<NodeID> = None;
                for cand in graph.nodes_of_type(*type_) {
                    crate::access_trace::note(10, cand.0, type_.0, crate::access_trace::NO_ID);
                    let cand_attrs = &graph.node(cand).attrs;
                    let mut all_match = true;
                    for (k, v) in &attr_pairs {
                        crate::access_trace::note(17, cand.0, k.0, crate::access_trace::NO_ID);
                        match cand_attrs.get(k) {
                            Some(existing) if existing == v => {}
                            _ => {
                                all_match = false;
                                break;
                            }
                        }
                    }
                    if all_match {
                        found = Some(cand);
                        break;
                    }
                }
                match found {
                    Some(existing) => {
                        // Bind the witness var to the existing node so
                        // downstream effects in the same rule still see
                        // a NodeID — they're addressing the SAME concept
                        // the present node represents, just not a fresh
                        // copy. No progress, no UndoStep.
                        b.insert(*new_var, existing);
                    }
                    None => {
                        let mut attr_map: FxHashMap<Sym, Value> = FxHashMap::default();
                        for (k, v) in attr_pairs {
                            attr_map.insert(k, v);
                        }
                        crate::scale_audit::rule_effect_node_insert();
                        let nid = graph.insert_node(*type_, attr_map);
                        crate::access_trace::note(7, nid.0, type_.0, crate::access_trace::NO_ID);
                        b.insert(*new_var, nid);
                        progressed = true;
                        if record_undo {
                            undo.push(UndoStep::AddedNode(nid));
                        }
                    }
                }
            }
            Effect::DelNode { var } => {
                let Some(&nid) = b.get(var) else {
                    continue;
                };
                crate::scale_audit::rule_effect_node_delete_attempt();
                crate::access_trace::note(
                    8,
                    nid.0,
                    crate::access_trace::NO_ID,
                    crate::access_trace::NO_ID,
                );
                graph.delete_node(nid);
                progressed = true;
                if record_undo {
                    // NodeID changes on re-insertion so we can't
                    // round-trip the binding. Record the marker so
                    // callers can detect it.
                    undo.push(UndoStep::NodeDeleted);
                }
            }
            Effect::SetAttr { var, key, value } => {
                let Some(&nid) = b.get(var) else {
                    continue;
                };
                let v = resolve_effect_arg(
                    value,
                    &b,
                    arena,
                    graph,
                    interner,
                    concepts.as_deref(),
                    framebuffers,
                    cache.as_deref_mut(),
                );
                crate::access_trace::note(17, nid.0, key.0, crate::access_trace::NO_ID);
                let old = graph.node(nid).attrs.get(key).cloned();
                let changed = old.as_ref() != Some(&v);
                crate::access_trace::note(4, nid.0, key.0, crate::access_trace::NO_ID);
                crate::scale_audit::rule_effect_attr_set_attempt();
                graph.set_node_attr(nid, *key, v);
                if changed {
                    progressed = true;
                    if record_undo {
                        undo.push(UndoStep::AttrSet {
                            nid,
                            key: *key,
                            old,
                        });
                    }
                }
            }
            Effect::SetAttrIfDifferent { var, key, value } => {
                let Some(&nid) = b.get(var) else {
                    continue;
                };
                let v = resolve_effect_arg(
                    value,
                    &b,
                    arena,
                    graph,
                    interner,
                    concepts.as_deref(),
                    framebuffers,
                    cache.as_deref_mut(),
                );
                let old = graph.node(nid).attrs.get(key).cloned();
                crate::access_trace::note(17, nid.0, key.0, crate::access_trace::NO_ID);
                // Difference from SetAttr: when equal we SKIP THE WRITE
                // entirely (don't pump set_node_attr's bookkeeping),
                // not just suppress the progress flag. Rules using this
                // variant get exact one-shot semantics even when paired
                // with progressing effects elsewhere in the rule.
                if old.as_ref() != Some(&v) {
                    crate::access_trace::note(4, nid.0, key.0, crate::access_trace::NO_ID);
                    crate::scale_audit::rule_effect_attr_set_attempt();
                    graph.set_node_attr(nid, *key, v);
                    progressed = true;
                    if record_undo {
                        undo.push(UndoStep::AttrSet {
                            nid,
                            key: *key,
                            old,
                        });
                    }
                }
            }
            Effect::ReplaceValue { old_var, new_var } => {
                let (Some(&old_nid), Some(&new_nid)) = (b.get(old_var), b.get(new_var)) else {
                    continue;
                };
                if old_nid == new_nid {
                    continue;
                }
                // Snapshot incoming edge data BEFORE any mutation —
                // EdgeIdxs become stale once we start deleting.
                let incoming: Vec<(NodeID, Sym, crate::graph::Attrs)> = graph
                    .in_edges_slice(old_nid, None)
                    .iter()
                    .copied()
                    .map(|idx| {
                        let e = graph.edge(idx);
                        (e.src, e.edge_type, graph.edge_attrs(idx).clone())
                    })
                    .collect();
                let mut rewired = 0usize;
                for (src, edge_type, attrs) in incoming {
                    // Skip if the (src, edge_type, old_nid) edge has
                    // already been removed (defensive — could happen if
                    // an earlier ReplaceValue in this effect list
                    // touched the same edge).
                    let Some(old_idx) = graph.edge_idx(src, edge_type, old_nid) else {
                        continue;
                    };
                    crate::access_trace::note(11, src.0, edge_type.0, old_nid.0);
                    if record_undo {
                        undo.push(UndoStep::DeletedEdge {
                            src,
                            edge_type,
                            tgt: old_nid,
                            attrs: attrs.clone(),
                        });
                    }
                    crate::scale_audit::rule_effect_replace_edge_delete();
                    graph.delete_edge(old_idx);
                    // Rewiring onto an existing destination edge replaces its
                    // attrs through insert_edge. Preserve those attrs in the
                    // undo log before the overwrite so rollback is exact.
                    let destination_key = EdgeKey {
                        src,
                        edge_type,
                        tgt: new_nid,
                    };
                    let destination_old = graph
                        .edge_idx(src, edge_type, new_nid)
                        .map(|idx| graph.edge_attrs(idx).clone());
                    let was_new = destination_old.is_none();
                    if record_undo {
                        if let Some(old) = destination_old {
                            undo.push(UndoStep::EdgeAttrsSet {
                                key: destination_key,
                                old,
                            });
                        }
                    }
                    crate::scale_audit::rule_effect_replace_edge_insert_attempt();
                    if graph.insert_edge(src, edge_type, new_nid, attrs).is_ok() {
                        if record_undo && was_new {
                            undo.push(UndoStep::AddedEdge(destination_key));
                        }
                        rewired += 1;
                    }
                }
                if rewired > 0 {
                    progressed = true;
                }
            }
            Effect::DefineConcept { name, term } => {
                // Resolve the concept name. Literal path is the common
                // case (rule writes `["define_concept", "name_str", …]`);
                // Computed path lets the rule synthesise a name from
                // the match binding (e.g. `Attr(?n, "label")`).
                let name_val = match name {
                    EffectArg::Literal(v) => v.clone(),
                    EffectArg::Computed(idx) => {
                        let mut env: Env = SmallVec::new();
                        for (&nm, &nid) in b.iter() {
                            env.push((nm, Value::Node(nid)));
                        }
                        let mut ctx = EvalCtx::new(graph, interner);
                        if let Some(c) = concepts.as_deref() {
                            ctx = ctx.with_concepts(c);
                        }
                        if let Some(fb) = framebuffers {
                            ctx = ctx.with_framebuffers(fb);
                        }
                        if let Some(c) = cache.as_deref_mut() {
                            ctx = ctx.with_cache(c);
                        }
                        evaluate(arena, *idx, &mut env, &mut ctx)
                    }
                };
                let name_sym = match name_val {
                    Value::Str(s) => s,
                    _ => {
                        // Name didn't evaluate to a string — skip
                        // silently (no progress, no panic). Matches
                        // the existing applier's tolerance for ill-
                        // typed effect args (e.g. SetAttr with a bad
                        // value just stores whatever evaluate returned).
                        continue;
                    }
                };
                // Resolve the term arg to a Value. Literal carries the
                // Term-JSON pre-decoded as a Dict-shaped Value (what
                // `parse_effect_json` produces via `decode_value` for a
                // bare Term-JSON object); Computed evaluates an
                // arbitrary Term — supported but rules need a DSL way
                // to construct the Dict at fire time, which is the
                // future work the Computed arm exists for.
                let term_val = match term {
                    EffectArg::Literal(v) => v.clone(),
                    EffectArg::Computed(idx) => {
                        let mut env: Env = SmallVec::new();
                        for (&nm, &nid) in b.iter() {
                            env.push((nm, Value::Node(nid)));
                        }
                        let mut ctx = EvalCtx::new(graph, interner);
                        if let Some(c) = concepts.as_deref() {
                            ctx = ctx.with_concepts(c);
                        }
                        if let Some(fb) = framebuffers {
                            ctx = ctx.with_framebuffers(fb);
                        }
                        if let Some(c) = cache.as_deref_mut() {
                            ctx = ctx.with_cache(c);
                        }
                        evaluate(arena, *idx, &mut env, &mut ctx)
                    }
                };
                // Skip silently for shapes that can't denote a Term —
                // empty / None / non-Dict. Matches the applier's
                // tolerance for ill-typed effect args elsewhere
                // (e.g. SetAttr just stores whatever evaluate returned).
                let serde_term = match value_to_serde_json(&term_val, interner) {
                    Some(j) if j.is_object() => j,
                    _ => continue,
                };
                // Parse the Term-JSON into the substrate's main arena.
                // The resulting TermIdx is valid for ConceptResolver
                // consulted via this same arena.
                let term_idx = match crate::jsonio::term_from_json(&serde_term, arena, interner) {
                    Ok(idx) => idx,
                    Err(_) => continue,
                };
                let was_new = match concepts.as_deref() {
                    Some(c) => c.get(&name_sym) != Some(&term_idx),
                    None => true,
                };
                pending_concepts.push((name_sym, term_idx));
                if was_new {
                    progressed = true;
                }
                // Note: no UndoStep is recorded — concept definitions
                // aren't part of graph state, and the backtracking
                // search this applier supports operates on the graph.
                // A rolled-back DefineConcept leaves the concept
                // installed; rules that depend on undo for correctness
                // shouldn't emit DefineConcept inside an undoable
                // probe path.
            }
        }
    }
    // Drain pending concepts into the resolver before returning. We
    // do this here (rather than in the caller) because the borrow on
    // `concepts` is already held — installing them is one mutation
    // we can perform without re-borrowing anything.
    if let Some(c) = concepts.as_deref_mut() {
        for (name_sym, term_idx) in &pending_concepts {
            c.insert(*name_sym, *term_idx);
        }
    }
    undo_src.resize(undo.len(), cur_effect);
    ApplyOutcome {
        undo,
        undo_src,
        progressed,
        pending_concepts,
    }
}

/// Inverse of `apply_rule` with `record_undo: true`. Replays the
/// undo steps in reverse — for backtracking search.
pub fn undo_apply(undo: Vec<UndoStep>, graph: &mut TypedGraph) {
    for step in undo.into_iter().rev() {
        match step {
            UndoStep::AddedEdge(key) => {
                if let Some(idx) = graph.edge_idx(key.src, key.edge_type, key.tgt) {
                    graph.delete_edge(idx);
                }
            }
            UndoStep::EdgeAttrsSet { key, old } => {
                let _ = graph.insert_edge(key.src, key.edge_type, key.tgt, old);
            }
            UndoStep::DeletedEdge {
                src,
                edge_type,
                tgt,
                attrs,
            } => {
                let _ = graph.insert_edge(src, edge_type, tgt, attrs);
            }
            UndoStep::AddedNode(nid) => {
                graph.delete_node(nid);
            }
            UndoStep::AttrSet { nid, key, old } => match old {
                Some(v) => graph.set_node_attr(nid, key, v),
                None => graph.remove_node_attr(nid, key),
            },
            UndoStep::NodeDeleted => {
                // Can't restore — best-effort no-op. Documented limit.
            }
        }
    }
}

/// Convert a `Value` back to a `serde_json::Value` shaped for
/// `term_from_json` — the inverse of the codec that `parse_effect_json`
/// + `persist::decode_value` produces, but TUNED FOR TERM-JSON shape.
///
/// Term-JSON uses bare JSON arrays for tuple-children (e.g. `Plus.items`
/// is `[<term>, <term>]`, not `{"__tuple__": [...]}`). The general
/// `persist::encode_value` round-trip would re-tag tuples as
/// `__tuple__` because that's the round-trippable shape for the
/// persistence layer — fine for graph attrs, wrong for Term-JSON.
/// So this helper:
///   - emits `Value::Tuple` as a bare JSON array (matches Term-JSON
///     child-list shape exactly), recursing on each item;
///   - emits string-keyed `Value::Dict` as a bare JSON object (the
///     Term-JSON object shape `{"type": ..., <field>: ...}`);
///   - falls through to `persist::encode_value` for everything else
///     (scalars, nodes, sets, surfaces). Term-JSON for scalar fields
///     (`Lit.value`, `Var.name`, etc.) is plain JSON scalars, which
///     `encode_value` produces correctly for `Bool/Int/Float/Str/None`.
///
/// Returns `None` if the Value can't denote a Term object (root must
/// be a string-keyed Dict, since every Term-JSON has a `"type"` key).
fn value_to_serde_json(value: &Value, interner: &Interner) -> Option<serde_json::Value> {
    // Root must be a string-keyed Dict (Term-JSON is always an object
    // with a `type` field).
    let pairs = match value {
        Value::Dict(p) => p,
        _ => return None,
    };
    Some(value_to_term_json(value, interner)).filter(|j| {
        // Sanity: the root really is an object (defensive — if a future
        // variant lands a Dict with non-string keys here, `value_to_term_json`
        // would emit a `__dict__` tagged form via the fallthrough, which
        // wouldn't have a `type` field).
        j.is_object() && pairs.iter().any(|(k, _)| matches!(k, Value::Str(_)))
    })
}

/// Inner helper for `value_to_serde_json` — recursively converts
/// Value-shaped data into the Term-JSON wire shape. Splits on
/// container variants:
///   - Tuple → bare JSON array (Term-JSON child-list)
///   - Dict with all-Str keys → bare JSON object
///   - everything else → delegate to `persist::encode_value` (covers
///     scalars + Node + sets + surface payloads)
fn value_to_term_json(value: &Value, interner: &Interner) -> serde_json::Value {
    use serde_json::Map;
    match value {
        Value::Tuple(items) | Value::List(items) => serde_json::Value::Array(
            items
                .iter()
                .map(|v| value_to_term_json(v, interner))
                .collect(),
        ),
        Value::Dict(pairs) => {
            // String-keyed dict → bare JSON object. Mixed-key dict
            // can't denote a Term-JSON object (every field name is a
            // string) so fall back to the persistence-tagged form;
            // term_from_json will error out at the next level, which
            // is the right behaviour — the rule asked us to register
            // something that isn't a Term.
            let all_string_keys = pairs.iter().all(|(k, _)| matches!(k, Value::Str(_)));
            if all_string_keys {
                let mut m = Map::new();
                for (k, v) in pairs.iter() {
                    if let Value::Str(s) = k {
                        m.insert(
                            interner.resolve(*s).to_string(),
                            value_to_term_json(v, interner),
                        );
                    }
                }
                serde_json::Value::Object(m)
            } else {
                crate::persist::encode_value(value, interner)
            }
        }
        // Scalars + Node + Set + FrozenSet + Surface → fall through to
        // the persistence encoder. Term-JSON for `Lit.value` is the
        // raw scalar (Number/Bool/String/Null), which `encode_value`
        // already emits correctly for those Value variants. Sets /
        // Node IDs etc. won't appear inside a well-formed Term-JSON
        // shape — if they do, term_from_json will reject them with a
        // clear error.
        _ => crate::persist::encode_value(value, interner),
    }
}

fn resolve_effect_arg(
    arg: &EffectArg,
    binding: &Binding,
    arena: &TermArena,
    graph: &TypedGraph,
    interner: &Interner,
    concepts: Option<&ConceptResolver>,
    framebuffers: Option<&crate::framebuffer::FbRegistry>,
    cache: Option<&mut crate::term::EvalCache>,
) -> Value {
    match arg {
        EffectArg::Literal(v) => v.clone(),
        EffectArg::Computed(idx) => {
            // Build the env from the binding so the Term sees the
            // matched vars as Value::Node bindings.
            let mut env: Env = SmallVec::new();
            for (&name, &nid) in binding.iter() {
                env.push((name, Value::Node(nid)));
            }
            let mut ctx = EvalCtx::new(graph, interner);
            if let Some(c) = concepts {
                ctx = ctx.with_concepts(c);
            }
            if let Some(fb) = framebuffers {
                ctx = ctx.with_framebuffers(fb);
            }
            if let Some(c) = cache {
                ctx = ctx.with_cache(c);
            }
            evaluate(arena, *idx, &mut env, &mut ctx)
        }
    }
}

// --- fixed-point runner ---------------------------------------------------

/// Apply rules to a fixed point. Each pass walks the rule list in
/// order, applying the first matching rule whose effect actually
/// changes the graph. Stops when no rule advances OR `max_steps` is
/// reached. Returns the number of *progressing* rewrite steps taken.
///
/// Termination via the `progressed` flag closes the canonical
/// transitive-closure trap: a rule that keeps matching the same
/// binding but produces an already-present edge counts as no
/// progress and is skipped, so the outer loop exits cleanly. Match
/// dispatch is also smarter than re-asking the matcher for the same
/// rule on the same graph: once a rule's first match is a no-op, we
/// scan past it to other matches by deferring this rule for the rest
/// of the pass.
pub fn run_rules(
    rules: &[&RewriteRule],
    arena: &mut TermArena,
    graph: &mut TypedGraph,
    interner: &mut Interner,
    concepts: Option<&mut ConceptResolver>,
    framebuffers: Option<&crate::framebuffer::FbRegistry>,
    cache: Option<&mut crate::term::EvalCache>,
    where_jits: &[Option<&crate::jit::CompiledWhere>],
    max_steps: usize,
) -> usize {
    run_rules_opts(
        rules,
        arena,
        graph,
        interner,
        concepts,
        framebuffers,
        cache,
        where_jits,
        max_steps,
        false,
    )
}

/// `run_rules` with opt-in CYCLE DETECTION. See
/// `Substrate::run_rules_opts` and `TypedGraph::state_fingerprint` for the
/// full rationale: `detect_cycles = false` is the committed loop verbatim
/// (no fingerprint computed, no state kept, nothing can move); `true`
/// additionally stops when the graph re-enters a state it has already
/// occupied, which under a deterministic map proves the trajectory is
/// periodic. This is the honest termination test for a float relaxation,
/// whose fixed point is generically NOT exactly representable — it needs
/// exact equality against history and NO tolerance, hence no epsilon.
pub fn run_rules_opts(
    rules: &[&RewriteRule],
    arena: &mut TermArena,
    graph: &mut TypedGraph,
    interner: &mut Interner,
    mut concepts: Option<&mut ConceptResolver>,
    framebuffers: Option<&crate::framebuffer::FbRegistry>,
    mut cache: Option<&mut crate::term::EvalCache>,
    where_jits: &[Option<&crate::jit::CompiledWhere>],
    max_steps: usize,
    detect_cycles: bool,
) -> usize {
    run_rules_opts_with_audit_ids(
        rules, None, arena, graph, interner, concepts, framebuffers, cache,
        where_jits, max_steps, detect_cycles,
    )
}

/// Runner variant for a caller that owns a distinct stable rule identity
/// space (for example graph-resident rules). Audit IDs must be unique within
/// that caller and disjoint from substrate RuleIdx values.
pub fn run_rules_opts_with_audit_ids(
    rules: &[&RewriteRule],
    audit_rule_ids: Option<&[u32]>,
    arena: &mut TermArena,
    graph: &mut TypedGraph,
    interner: &mut Interner,
    mut concepts: Option<&mut ConceptResolver>,
    framebuffers: Option<&crate::framebuffer::FbRegistry>,
    mut cache: Option<&mut crate::term::EvalCache>,
    where_jits: &[Option<&crate::jit::CompiledWhere>],
    max_steps: usize,
    detect_cycles: bool,
) -> usize {
    let mut seen: Option<rustc_hash::FxHashSet<u64>> = if detect_cycles {
        Some(Default::default())
    } else {
        None
    };
    if let Some(s) = seen.as_mut() {
        s.insert(graph.state_fingerprint());
    }
    let mut steps = 0;
    while steps < max_steps {
        let mut any_progress = false;
        for (rule_i, rule) in rules.iter().enumerate() {
            let audit_rule_i = audit_rule_ids.and_then(|ids| ids.get(rule_i).copied()).unwrap_or(rule_i as u32);
            let this_jit = where_jits.get(rule_i).copied().unwrap_or(None);
            // slice (b): batch-safe rules apply EVERY binding this pass (no
            // undo probe, no one-per-pass throttle). `continue` (not break)
            // so other rules still run this pass; the outer while re-loops on
            // progress and a settled batch rule returns false.
            // SCALE AUDIT: declare WHICH rule is about to be enumerated, so the
            // C/R split can be made positionally (prereg §3). A rule's FIRST
            // enumeration this epoch is genuine comparison (C); every LATER one
            // re-derives a binding set the first pass already had (R). That is
            // exactly what the cold path below does — enumerate every binding,
            // apply ONE, `break`, and re-enumerate from scratch.
            crate::scale_audit::begin_rule_enumeration(audit_rule_i);
            crate::scale_audit::register_rule_audit_metadata(
                audit_rule_i, rule.name.0, interner.resolve(rule.name), rule.match_edges.len()
            );
            if rule.batch {
                if batch_apply_rule(
                    rule,
                    arena,
                    graph,
                    interner,
                    concepts.as_deref_mut(),
                    framebuffers,
                    cache.as_deref_mut(),
                    this_jit,
                ) {
                    steps += 1;
                    any_progress = true;
                }
                crate::scale_audit::end_rule_enumeration();
                continue;
            }
            // --- cold path: one progressing binding per pass ---
            let mut found_progressing: Option<Binding> = None;
            let mut bindings: Vec<Binding> = Vec::new();
            match_rule_each(
                rule,
                arena,
                graph,
                interner,
                concepts.as_deref(),
                framebuffers,
                cache.as_deref_mut(),
                this_jit,
                |b| {
                    crate::scale_audit::binding_cloned();
                    bindings.push(b.clone());
                    true // collect all
                },
            );
            for b in bindings {
                // Try the apply but DON'T commit yet — we want to
                // know if it progresses. Cheapest path: do the apply
                // with record_undo=true, check progress, and if it
                // didn't progress, undo. If it did progress, keep it.
                //
                // Bindings were ALL collected above before any apply, so
                // enumeration reads an unmutated graph. The only way a
                // rolled-back probe can reach the next binding is if the undo
                // below is inexact — which `effect_audit::probe_exactness`
                // measures rather than assumes.
                let fp_before = if crate::effect_audit::probe_exactness() {
                    Some(graph.state_fingerprint())
                } else {
                    None
                };
                let outcome = apply_rule_full(
                    rule,
                    &b,
                    arena,
                    graph,
                    interner,
                    concepts.as_deref_mut(),
                    framebuffers,
                    cache.as_deref_mut(),
                    true,
                );
                if outcome.progressed {
                    found_progressing = Some(b);
                    break;
                } else {
                    // No-op binding — undo any state writes (there
                    // shouldn't be many; SetAttr with the same value
                    // is the typical case). Then try the next.
                    crate::scale_audit::apply_probe_rollback();
                    undo_apply(outcome.undo, graph);
                    if let Some(before) = fp_before {
                        crate::effect_audit::record_probe_rollback(
                            before,
                            graph.state_fingerprint(),
                            || interner.resolve(rule.name).to_string(),
                        );
                    }
                }
            }
            if found_progressing.is_some() {
                steps += 1;
                any_progress = true;
                crate::scale_audit::end_rule_enumeration();
                break;
            }
            crate::scale_audit::end_rule_enumeration();
        }
        if !any_progress {
            return steps;
        }
        // Opt-in cycle detection — placed AFTER the no-progress exit so a
        // true fixed point still returns by the committed path.
        if let Some(s) = seen.as_mut() {
            if !s.insert(graph.state_fingerprint()) {
                return steps;
            }
        }
    }
    steps
}

// --- per-Mt SCOPED fixpoint runner (CAN_MT_SCOPED_RULES_PREREG/RESULTS.md) -
//
// ADDITIVE ONLY. Nothing above this point in the file is touched by this
// section, and nothing below it (`batch_apply_rule` and everything after)
// is touched either. `run_rules`/`run_rules_opts` above remain byte-for-byte
// what every existing caller has always seen.

/// The set of nodes considered "owned" by a Microtheory for the purposes of
/// `run_rules_opts_scoped`'s per-Mt binding filter: `mt` itself, plus every
/// node one `has_concept` hop away. This is literally
/// `can_ops.rs::mt_concepts`'s own membership definition
/// (`g.neighbours(mt_id, Some(has_concept))`) — reused, not reinvented, per
/// the task's own directive. `mt` itself is included so a binding that only
/// references the Mt node (no concept var) still counts as in-scope.
pub fn mt_owned_nodes(
    graph: &TypedGraph,
    mt: NodeID,
    has_concept: Sym,
) -> rustc_hash::FxHashSet<NodeID> {
    let mut out: rustc_hash::FxHashSet<NodeID> = Default::default();
    out.insert(mt);
    for c in graph.neighbours(mt, Some(has_concept)) {
        out.insert(c);
    }
    out
}

/// A binding "touches" the scope iff AT LEAST ONE of its bound NodeIDs is a
/// member of `owned`. This remains the generic post-match filter and fallback;
/// `scoped_mt_seed` prunes matching only for the structurally proven
/// one-edge membership pattern. Every real CAN rule today binds a single `mt`
/// var consistently across the whole pattern, so in practice this reduces
/// to an exact `binding["mt"] == target` check; the more general "touches
/// ANY" form is a documented, deliberate generalisation, not an untested
/// guess (see PREREG §1's named limitation: "touches ANY", not "touches
/// ONLY" — a hypothetical cross-Mt-spanning pattern would fire when scoped
/// to either Mt; no rule in either CAN seed does this today).
fn binding_touches_scope(binding: &Binding, owned: &rustc_hash::FxHashSet<NodeID>) -> bool {
    binding.values().any(|nid| owned.contains(nid))
}

fn canonical_binding_key(binding: &Binding) -> smallvec::SmallVec<[(Sym, NodeID); 8]> {
    let mut key: smallvec::SmallVec<[(Sym, NodeID); 8]> =
        binding.iter().map(|(sym, node)| (*sym, *node)).collect();
    key.sort_by_key(|(sym, _)| *sym);
    key
}

/// Prove the common one-edge Microtheory case has an exact scope driver.
/// Binding a rule's `has_concept` source to `scope_mt` is equivalent to the
/// general post-match `touches owned` filter only when no other has_concept
/// edge can touch an owned node and owned member nodes do not themselves act
/// as has_concept sources. Otherwise return None and retain the generic
/// full-match/filter path.
fn scoped_mt_seed(
    rule: &RewriteRule,
    scope_mt: NodeID,
    has_concept: Sym,
    graph: &TypedGraph,
    owned: &rustc_hash::FxHashSet<NodeID>,
) -> Option<Binding> {
    if rule.match_edges.len() != 1 || !owned.contains(&scope_mt) {
        return None;
    }
    let edge = &rule.match_edges[0];
    if edge.edge_type != has_concept || edge.src_var == edge.tgt_var {
        return None;
    }
    for &node in owned {
        if node != scope_mt && !graph.neighbours(node, Some(has_concept)).is_empty() {
            return None;
        }
        if graph
            .in_neighbours(node, Some(has_concept))
            .into_iter()
            .any(|src| src != scope_mt)
        {
            return None;
        }
    }
    let mut seed = Binding::default();
    seed.insert(edge.src_var, scope_mt);
    Some(seed)
}

#[allow(clippy::too_many_arguments)]
fn match_rule_each_for_scope<F>(
    rule: &RewriteRule,
    seed: Option<&Binding>,
    owned: &rustc_hash::FxHashSet<NodeID>,
    arena: &TermArena,
    graph: &TypedGraph,
    interner: &Interner,
    concepts: Option<&ConceptResolver>,
    framebuffers: Option<&crate::framebuffer::FbRegistry>,
    cache: Option<&mut crate::term::EvalCache>,
    mut visit: F,
) where
    F: FnMut(&Binding) -> bool,
{
    if let Some(seed) = seed {
        crate::scale_audit::scoped_match_path(crate::scale_audit::ScopedMatchPath::MicrotheorySeed);
        match_rule_each_with_initial(
            rule,
            seed,
            arena,
            graph,
            interner,
            concepts,
            framebuffers,
            cache,
            None,
            visit,
        );
        return;
    }

    // Exact order-preserving local path for one-edge patterns. EdgeIdx order
    // equals edges_by_type insertion order only before any deletion/reuse of
    // this edge type; the monotone global deletion generation makes that precondition
    // explicit. Gather every match that touches ownership by seeding either
    // endpoint from the owned set, deduplicate bindings, then restore the
    // original global edge order before visiting/effect application.
    let single_edge = rule.match_edges.first();
    if let Some(edge) = single_edge.filter(|edge| {
        rule.match_edges.len() == 1
            && edge.src_var != edge.tgt_var
            && graph.edge_delete_generation() == 0
    }) {
        crate::scale_audit::scoped_match_path(crate::scale_audit::ScopedMatchPath::LocalOwnedEdge);
        let mut scope_nodes: Vec<NodeID> = owned.iter().copied().collect();
        scope_nodes.sort_unstable();
        let mut collected: Vec<(crate::graph::EdgeIdx, Binding)> = Vec::new();
        let mut seen: rustc_hash::FxHashSet<smallvec::SmallVec<[(Sym, NodeID); 8]>> = Default::default();
        let mut cache = cache;
        for node in scope_nodes {
            let outgoing = !graph.out_edges_slice(node, Some(edge.edge_type)).is_empty();
            let incoming = !graph.in_edges_slice(node, Some(edge.edge_type)).is_empty();
            for (var, has_candidates) in [(edge.src_var, outgoing), (edge.tgt_var, incoming)] {
                if !has_candidates { continue; }
                let mut initial = Binding::default();
                initial.insert(var, node);
                match_rule_each_with_initial(
                    rule, &initial, arena, graph, interner, concepts, framebuffers,
                    cache.as_deref_mut(), None, |binding| {
                        if !binding_touches_scope(binding, owned) { return true; }
                        let key = canonical_binding_key(binding);
                        if !seen.insert(key) { return true; }
                        let Some(&src) = binding.get(&edge.src_var) else { return true; };
                        let Some(&tgt) = binding.get(&edge.tgt_var) else { return true; };
                        if let Some(edge_idx) = graph.edge_idx(src, edge.edge_type, tgt) {
                            collected.push((edge_idx, binding.clone()));
                        }
                        true
                    },
                );
            }
        }
        collected.sort_unstable_by_key(|(edge_idx, _)| *edge_idx);
        for (_, binding) in collected {
            if !visit(&binding) { break; }
        }
        return;
    }

    crate::scale_audit::scoped_match_path(crate::scale_audit::ScopedMatchPath::FullFallback);
    match_rule_each(rule, arena, graph, interner, concepts, framebuffers, cache, None, visit);
}

/// SCOPED twin of `run_rules_opts`. Reached ONLY via
/// `Substrate::run_rules_scoped(..., Some(mt))` — that method's `None` arm
/// calls the EXISTING, UNCHANGED `run_rules_opts` directly (never this
/// function), so this code cannot alter behaviour for any pre-existing
/// caller by construction, not merely by intent.
///
/// Deliberately reimplements (rather than calls) the cold-path and
/// batch-path binding collection. It uses a proven `has_concept` source
/// prebinding for the common one-edge Microtheory rule and an ordered,
/// ownership-seeded candidate path for eligible one-edge rules. Unsupported
/// shapes or any prior edge deletion use full matching and filter bindings
/// with `binding_touches_scope` before applying. This is an opt-in path: no
/// incremental cursor reuse (that
/// machinery lives in `Substrate::attempt_one_rule` and is keyed on
/// per-rule state with no per-Mt dimension — retrofitting one is out of
/// scope for this rung, see PREREG §0's blast-radius framing), no JIT
/// where-clause, no rayon parallel collection. The bounded one-edge local
/// candidate path is used only when its order proof holds; unsupported shapes
/// retain full matching. This remains an opt-in path, not a scheduler-level
/// feature.
pub fn run_rules_opts_scoped(
    rules: &[(u32, &RewriteRule)],
    arena: &mut TermArena,
    graph: &mut TypedGraph,
    interner: &mut Interner,
    mut concepts: Option<&mut ConceptResolver>,
    framebuffers: Option<&crate::framebuffer::FbRegistry>,
    mut cache: Option<&mut crate::term::EvalCache>,
    max_steps: usize,
    detect_cycles: bool,
    scope_mt: NodeID,
    has_concept: Sym,
    owned: &rustc_hash::FxHashSet<NodeID>,
) -> usize {
    let mut seen: Option<rustc_hash::FxHashSet<u64>> = if detect_cycles {
        Some(Default::default())
    } else {
        None
    };
    if let Some(s) = seen.as_mut() {
        s.insert(graph.state_fingerprint());
    }
    let mut steps = 0;
    while steps < max_steps {
        let mut any_progress = false;
        for (rule_i, rule) in rules.iter().copied() {
            // Keep optional per-rule scale counters attributable on the
            // scoped path too. `rule_i` is preserved by Substrate as the
            // original stable vector position, including gaps from inactive
            // rules; compacting the active slice here would mislabel audits.
            crate::scale_audit::begin_rule_enumeration(rule_i);
            crate::scale_audit::register_rule_audit_metadata(
                rule_i, rule.name.0, interner.resolve(rule.name), rule.match_edges.len()
            );
            let scope_seed = scoped_mt_seed(rule, scope_mt, has_concept, graph, owned);
            if rule.batch {
                // Batch-safe: collect every binding via a full match,
                // filter to scope, apply each distinct surviving binding
                // exactly once (dedup by canonical key) — the same
                // batch-safety semantics `batch_apply_rule` implements,
                // reproduced here because it needs a filter seam between
                // collect and apply that the shared function doesn't have.
                let mut bindings: Vec<Binding> = Vec::new();
                match_rule_each_for_scope(
                    rule,
                    scope_seed.as_ref(),
                    owned,
                    arena,
                    graph,
                    interner,
                    concepts.as_deref(),
                    framebuffers,
                    cache.as_deref_mut(),
                    |b| {
                        bindings.push(b.clone());
                        true
                    },
                );
                bindings.retain(|b| binding_touches_scope(b, owned));
                let mut seen_b: rustc_hash::FxHashSet<smallvec::SmallVec<[(Sym, NodeID); 8]>> =
                    Default::default();
                let mut progressed_any = false;
                for b in bindings {
                    let mut canon: smallvec::SmallVec<[(Sym, NodeID); 8]> =
                        b.iter().map(|(s, n)| (*s, *n)).collect();
                    canon.sort_by_key(|(s, _)| *s);
                    if !seen_b.insert(canon) {
                        continue;
                    }
                    let outcome = apply_rule_full(
                        rule,
                        &b,
                        arena,
                        graph,
                        interner,
                        concepts.as_deref_mut(),
                        framebuffers,
                        None,
                        false,
                    );
                    if outcome.progressed {
                        progressed_any = true;
                    }
                }
                if progressed_any {
                    steps += 1;
                    any_progress = true;
                }
                crate::scale_audit::end_rule_enumeration();
                continue;
            }
            // Cold path: the live Substrate scheduler snapshots every
            // binding for a rule before mutation, then applies each distinct
            // binding once in order. Preserve that drain semantics after
            // scope filtering. Stopping at the first progressing binding
            // changes multi-binding rules (including non-idempotent effects)
            // relative to `Substrate::attempt_one_rule`.
            let mut bindings: Vec<Binding> = Vec::new();
            match_rule_each_for_scope(
                rule,
                scope_seed.as_ref(),
                owned,
                arena,
                graph,
                interner,
                concepts.as_deref(),
                framebuffers,
                cache.as_deref_mut(),
                |b| {
                    bindings.push(b.clone());
                    true
                },
            );
            bindings.retain(|b| binding_touches_scope(b, owned));
            let mut seen_b: rustc_hash::FxHashSet<smallvec::SmallVec<[(Sym, NodeID); 8]>> =
                Default::default();
            let mut progressed_any = false;
            for b in bindings {
                if !seen_b.insert(canonical_binding_key(&b)) {
                    continue;
                }
                let outcome = apply_rule_full(
                    rule,
                    &b,
                    arena,
                    graph,
                    interner,
                    concepts.as_deref_mut(),
                    framebuffers,
                    // Matching above observed one pre-mutation snapshot;
                    // graph-dependent cache entries cannot be reused while
                    // folding effects over the binding snapshot.
                    None,
                    true,
                );
                if outcome.progressed {
                    progressed_any = true;
                } else {
                    undo_apply(outcome.undo, graph);
                }
            }
            if progressed_any {
                steps += 1;
                any_progress = true;
                crate::scale_audit::end_rule_enumeration();
                break;
            }
            crate::scale_audit::end_rule_enumeration();
        }
        if !any_progress {
            return steps;
        }
        if let Some(s) = seen.as_mut() {
            if !s.insert(graph.state_fingerprint()) {
                return steps;
            }
        }
    }
    steps
}

/// Apply EVERY currently-matching binding of one batch-safe rule in a
/// single pass, with `record_undo = false` — no clone, no undo vec, no
/// per-binding probe-then-rollback. Returns whether any binding was
/// not-already-satisfied (so a settled rule returns false and the outer
/// fixpoint exits). Caller guarantees `rule.batch`. Bindings are
/// snapshotted BEFORE any effect fires, so the rule's own writes don't
/// grow/shrink this pass's binding set — the batch-safety property.
pub fn batch_apply_rule(
    rule: &RewriteRule,
    arena: &mut TermArena,
    graph: &mut TypedGraph,
    interner: &mut Interner,
    mut concepts: Option<&mut ConceptResolver>,
    framebuffers: Option<&crate::framebuffer::FbRegistry>,
    mut cache: Option<&mut crate::term::EvalCache>,
    where_jit: Option<&crate::jit::CompiledWhere>,
) -> bool {
    use rustc_hash::FxHashSet;
    // 1) Snapshot every binding once (apply mutates the graph).
    let mut bindings: Vec<Binding> = Vec::new();
    match (rule.match_type, rule.match_edges.len()) {
        // Type-indexed driver: bind the single match-edge's tgt_var to each
        // node of `match_type`, resolve the rest via the matcher.
        (Some(mt), 1) => {
            let tgt_var = rule.match_edges[0].tgt_var;
            for node in graph.nodes_of_type(mt) {
                let mut initial: Binding = rustc_hash::FxHashMap::default();
                initial.insert(tgt_var, node);
                match_rule_each_with_initial(
                    rule,
                    &initial,
                    arena,
                    graph,
                    interner,
                    concepts.as_deref(),
                    framebuffers,
                    cache.as_deref_mut(),
                    where_jit,
                    |b| {
                        bindings.push(b.clone());
                        true
                    },
                );
            }
        }
        (Some(mt), _) if graph.nodes_of_type(mt).is_empty() => {}
        _ => {
            let worker_capacity = rayon::current_num_threads();
            if let Some(parallel) = collect_batch_bindings_parallel(
                rule,
                arena,
                graph,
                interner,
                concepts.as_deref(),
                framebuffers,
                where_jit,
                worker_capacity,
            ) {
                bindings = parallel;
            } else {
                match_rule_each(
                    rule,
                    arena,
                    graph,
                    interner,
                    concepts.as_deref(),
                    framebuffers,
                    cache.as_deref_mut(),
                    where_jit,
                    |b| {
                        bindings.push(b.clone());
                        true
                    },
                );
            }
        }
    }
    // 2) Apply each distinct binding exactly once, no undo bookkeeping.
    let mut seen: FxHashSet<smallvec::SmallVec<[(Sym, NodeID); 8]>> = Default::default();
    let mut progressed_any = false;
    for b in bindings {
        let mut canon: smallvec::SmallVec<[(Sym, NodeID); 8]> =
            b.iter().map(|(s, n)| (*s, *n)).collect();
        canon.sort_by_key(|(s, _)| *s);
        if !seen.insert(canon) {
            continue;
        }
        let outcome = apply_rule_full(
            rule,
            &b,
            arena,
            graph,
            interner,
            // eval_cache memoises Neighbours/Filter/Holds keyed on graph
            // state — invalid once an effect mutates the graph. Apply with
            // None (like the live engine's other apply sites); the match
            // phase above keeps the cache (it runs pre-mutation, coherent).
            concepts.as_deref_mut(),
            framebuffers,
            None,
            /* record_undo */ false,
        );
        if outcome.progressed {
            progressed_any = true;
        }
    }
    progressed_any
}

/// Enumerate a batch rule's binding forest against one immutable graph
/// snapshot.  The smallest ordered match-prefix with enough bindings becomes
/// the frontier; every complete binding belongs to exactly one frontier
/// subtree. Rayon evaluates those subtrees concurrently and its indexed
/// collect keeps the original DFS order for the later serial effect fold.
///
/// `None` means the serial matcher is the better or required path.  There is
/// no tuned grain constant: parallelism opens only when the graph supplies at
/// least one root candidate per available worker.  A one-worker capacity is
/// therefore the exact serial reduction arm.
fn collect_batch_bindings_parallel(
    rule: &RewriteRule,
    arena: &TermArena,
    graph: &TypedGraph,
    interner: &Interner,
    concepts: Option<&ConceptResolver>,
    framebuffers: Option<&crate::framebuffer::FbRegistry>,
    where_jit: Option<&crate::jit::CompiledWhere>,
    worker_capacity: usize,
) -> Option<Vec<Binding>> {
    if worker_capacity <= 1 || rule.match_edges.is_empty() || where_jit.is_some() {
        return None;
    }
    if !rule
        .match_edges
        .iter()
        .any(|edge| graph.edges_by_type(edge.edge_type).len() >= worker_capacity)
    {
        return None;
    }

    // The common wide-root case needs no serial prefix walk: the matcher's
    // first both-unbound candidate set is already an ordered, non-overlapping
    // frontier.  Construct the identical initial bindings directly so its
    // structural scan is distributed too.
    let first = &rule.match_edges[0];
    let first_candidates: Vec<(NodeID, NodeID)> = graph
        .edges_by_type(first.edge_type)
        .iter()
        .map(|idx| {
            let key = graph.edge(*idx).key();
            (key.src, key.tgt)
        })
        .collect();
    let mut frontier = if first_candidates.len() >= worker_capacity {
        crate::scale_audit::candidates(
            first_candidates.len() as u64,
            crate::scale_audit::CandPath::Scan,
        );
        Some((
            first_candidates
                .into_iter()
                .map(|(src, tgt)| {
                    crate::scale_audit::cand_tested(0, rule.name.0, rule.match_edges.len());
                    let mut binding = Binding::default();
                    binding.insert(first.src_var, src);
                    binding.insert(first.tgt_var, tgt);
                    binding
                })
                .collect(),
            1,
        ))
    } else {
        None
    };

    // Build complete deeper prefix levels in the matcher's own DFS order. The
    // prefix has no where-clause or pushdown: predicates are evaluated exactly
    // once by the full rule inside the worker, so diagnostics and semantics
    // remain identical.  We stop at the first level wide enough to occupy the
    // available workers; no authored grain constant is involved.
    for depth in 2..=rule.match_edges.len() {
        if frontier.is_some() {
            break;
        }
        let mut prefix = rule.clone();
        prefix.match_edges.truncate(depth);
        prefix.where_ = None;
        prefix.where_conjuncts.clear();
        prefix.effects.clear();
        let mut prefixes = Vec::new();
        match_rule_each(
            &prefix,
            arena,
            graph,
            interner,
            None,
            None,
            None,
            None,
            |binding| {
                prefixes.push(binding.clone());
                true
            },
        );
        if prefixes.len() >= worker_capacity {
            frontier = Some((prefixes, depth));
            break;
        }
    }
    let (frontier, frontier_depth) = frontier?;
    let roots_per_partition = frontier.len().saturating_add(worker_capacity - 1) / worker_capacity;
    let traced_rule = crate::fallback_trace::current_rule();
    let audit_rule = crate::scale_audit::current_rule_index();
    let partitions: Vec<(Vec<Binding>, crate::fallback_trace::LocalCounts)> = frontier
        .par_chunks(roots_per_partition)
        .map(|roots| {
            let collect_partition = || {
                crate::fallback_trace::reset();
                crate::fallback_trace::set_current_rule(traced_rule);
                let mut local = Vec::new();
                for initial in roots {
                    let mut binding = initial.clone();
                    extend_each(
                        rule,
                        frontier_depth,
                        &mut binding,
                        arena,
                        graph,
                        interner,
                        concepts,
                        framebuffers,
                        None,
                        None,
                        0,
                        &mut |binding| {
                            local.push(binding.clone());
                            true
                        },
                    );
                }
                (local, crate::fallback_trace::take_local_counts())
            };
            if let Some(rule_i) = audit_rule {
                crate::scale_audit::with_rule_index(rule_i, collect_partition)
            } else {
                collect_partition()
            }
        })
        .collect();
    let mut bindings = Vec::new();
    for (partition, counts) in partitions {
        crate::fallback_trace::merge_local_counts(counts);
        bindings.extend(partition);
    }
    Some(bindings)
}

#[cfg(test)]
mod effect_audit_tests {
    use super::*;

    /// The counters are process-global statics, so these tests must not run
    /// concurrently with one another.
    static AUDIT_LOCK: std::sync::Mutex<()> = std::sync::Mutex::new(());

    /// Build the reachable failure, ISOLATED so the only effect under test is
    /// the failing insert.
    ///
    /// The first version of this test put `DelNode` and `AddEdge` in one
    /// rule and asserted on `out.progressed`. That was wrong: `DelNode` is
    /// itself real progress, so the outcome was true for a reason unrelated
    /// to the insert. Here the deletion happens first, in its own firing, and
    /// the rule under test carries only the `AddEdge` whose target is by then
    /// a dangling `NodeID` — `insert_edge` returns `Err(MissingTgt)` and the
    /// firing has nothing else that could credit progress.
    fn dangling_link() -> (TypedGraph, Interner, TermArena, RewriteRule, Binding) {
        let (mut g, mut i, a) = (TypedGraph::new(), Interner::new(), TermArena::new());
        let ty = i.intern("Thing");
        let link = i.intern("link");
        let src = g.insert_node(ty, FxHashMap::default());
        let doomed = g.insert_node(ty, FxHashMap::default());
        g.delete_node(doomed);
        let s_var = i.intern("s");
        let d_var = i.intern("d");
        let rule = RewriteRule {
            name: i.intern("dangling_link"),
            match_edges: vec![],
            where_: None,
            effects: vec![Effect::AddEdge {
                src_var: s_var,
                edge_type: link,
                tgt_var: d_var,
                attrs: vec![],
            }],
            ..Default::default()
        };
        let mut b: Binding = FxHashMap::default();
        b.insert(s_var, src);
        b.insert(d_var, doomed);
        (g, i, a, rule, b)
    }

    /// RED: the failure is real, is counted, and is counted as false progress.
    #[test]
    fn failed_edge_insert_is_counted_as_false_progress() {
        let _guard = AUDIT_LOCK.lock().unwrap_or_else(|e| e.into_inner());
        crate::effect_audit::reset();
        crate::effect_audit::set_correct_failed_effects(false);
        let (mut g, mut i, mut a, rule, b) = dangling_link();
        let out = apply_rule_full(&rule, &b, &mut a, &mut g, &mut i, None, None, None, true);
        let (failed, false_progress, row) = crate::effect_audit::stats();
        assert_eq!(failed, 1, "the discarded Err must be counted");
        assert_eq!(false_progress, 1, "it must be counted as false progress");
        assert!(row.is_some(), "the first failure must be retained verbatim");
        // With the correction explicitly off, the pre-existing behaviour is
        // preserved exactly: progress is still (wrongly) credited. This pins the
        // old semantics so the flag's two states stay distinguishable.
        assert!(
            out.progressed,
            "correction off must reproduce the old behaviour"
        );
        crate::effect_audit::reset();
    }

    /// GREEN: with the correction enabled, no progress is credited for a
    /// mutation that did not happen.
    #[test]
    fn correction_withholds_progress_for_a_failed_insert() {
        let _guard = AUDIT_LOCK.lock().unwrap_or_else(|e| e.into_inner());
        crate::effect_audit::reset();
        crate::effect_audit::set_correct_failed_effects(true);
        let (mut g, mut i, mut a, rule, b) = dangling_link();
        let out = apply_rule_full(&rule, &b, &mut a, &mut g, &mut i, None, None, None, true);
        let (failed, false_progress, _) = crate::effect_audit::stats();
        assert_eq!(failed, 1);
        assert_eq!(false_progress, 1, "still counted; only the credit changes");
        assert!(
            !out.progressed,
            "a failed insert is not progress when the correction is on"
        );
        crate::effect_audit::set_correct_failed_effects(false);
        crate::effect_audit::reset();
    }

    /// The instrument must not fire on a healthy insert.
    #[test]
    fn healthy_insert_does_not_fire_the_detector() {
        let _guard = AUDIT_LOCK.lock().unwrap_or_else(|e| e.into_inner());
        crate::effect_audit::reset();
        let (mut g, mut i, mut a) = (TypedGraph::new(), Interner::new(), TermArena::new());
        let ty = i.intern("Thing");
        let link = i.intern("link");
        let s = g.insert_node(ty, FxHashMap::default());
        let t = g.insert_node(ty, FxHashMap::default());
        let s_var = i.intern("s");
        let t_var = i.intern("t");
        let rule = RewriteRule {
            name: i.intern("healthy_link"),
            match_edges: vec![],
            where_: None,
            effects: vec![Effect::AddEdge {
                src_var: s_var,
                edge_type: link,
                tgt_var: t_var,
                attrs: vec![],
            }],
            ..Default::default()
        };
        let mut b: Binding = FxHashMap::default();
        b.insert(s_var, s);
        b.insert(t_var, t);
        let out = apply_rule_full(&rule, &b, &mut a, &mut g, &mut i, None, None, None, true);
        let (failed, false_progress, _) = crate::effect_audit::stats();
        assert_eq!(failed, 0, "no failure on a well-formed insert");
        assert_eq!(false_progress, 0);
        assert!(out.progressed);
        assert!(g.has_edge(s, link, t));
        crate::effect_audit::reset();
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::term::TermNode;

    fn setup_graph() -> (TypedGraph, Interner, TermArena) {
        (TypedGraph::new(), Interner::new(), TermArena::new())
    }

    #[test]
    fn match_finds_simple_edge() {
        // Pattern: ?a -[knows]-> ?b. Graph has one such edge.
        let (mut g, mut i, a) = setup_graph();
        let person = i.intern("Person");
        let knows = i.intern("knows");
        let alice = g.insert_node(person, FxHashMap::default());
        let bob = g.insert_node(person, FxHashMap::default());
        g.insert_edge(alice, knows, bob, FxHashMap::default())
            .unwrap();
        let rule = RewriteRule {
            name: i.intern("alice_knows_bob"),
            match_edges: vec![MatchEdge {
                src_var: i.intern("a"),
                edge_type: knows,
                tgt_var: i.intern("b"),
            }],
            where_: None,
            effects: vec![],
            ..Default::default()
        };
        let b = match_rule(&rule, &a, &g, &i, None, None).expect("should match");
        assert_eq!(b[&i.lookup("a").unwrap()], alice);
        assert_eq!(b[&i.lookup("b").unwrap()], bob);
    }

    #[test]
    fn parallel_batch_enumeration_is_order_identical_to_serial() {
        let (mut graph, mut interner, mut arena) = setup_graph();
        let node_type = interner.intern("Node");
        let first_edge = interner.intern("first_edge");
        let second_edge = interner.intern("second_edge");
        let a_var = interner.intern("a");
        let b_var = interner.intern("b");
        let c_var = interner.intern("c");
        let missing_key = interner.intern("missing_key");
        let source = arena.add(TermNode::Var { name: a_var });
        let missing = arena.add(TermNode::Attr {
            node: source,
            key: missing_key,
        });
        let none = arena.add(TermNode::Lit { value: Value::None });
        let missing_is_none = arena.add(TermNode::Eq {
            a: missing,
            b: none,
        });
        let rule = RewriteRule {
            name: interner.intern("parallel_batch_test"),
            match_edges: vec![
                MatchEdge {
                    src_var: a_var,
                    edge_type: first_edge,
                    tgt_var: b_var,
                },
                MatchEdge {
                    src_var: b_var,
                    edge_type: second_edge,
                    tgt_var: c_var,
                },
            ],
            where_: Some(missing_is_none),
            effects: vec![],
            batch: true,
            ..Default::default()
        };
        let worker_capacity = 2;
        let root_count = worker_capacity * (rule.match_edges.len() + 1);
        let a = graph.insert_node(node_type, FxHashMap::default());
        let b = graph.insert_node(node_type, FxHashMap::default());
        graph
            .insert_edge(a, first_edge, b, FxHashMap::default())
            .unwrap();
        for _ in 0..root_count {
            let c = graph.insert_node(node_type, FxHashMap::default());
            graph
                .insert_edge(b, second_edge, c, FxHashMap::default())
                .unwrap();
        }

        let canonical = |binding: &Binding| {
            let mut row: Vec<_> = binding.iter().map(|(sym, node)| (*sym, *node)).collect();
            row.sort_by_key(|(sym, _)| *sym);
            row
        };
        crate::fallback_trace::reset();
        crate::fallback_trace::set_current_rule(Some(rule.name));
        let mut serial = Vec::new();
        match_rule_each(
            &rule,
            &arena,
            &graph,
            &interner,
            None,
            None,
            None,
            None,
            |binding| {
                serial.push(canonical(binding));
                true
            },
        );
        let mut serial_fallback = crate::fallback_trace::defaulted_raw();
        serial_fallback.sort();
        crate::fallback_trace::reset();
        crate::fallback_trace::set_current_rule(Some(rule.name));
        let parallel = collect_batch_bindings_parallel(
            &rule,
            &arena,
            &graph,
            &interner,
            None,
            None,
            None,
            worker_capacity,
        )
        .expect("the graph supplies at least one root per worker");
        let mut parallel_fallback = crate::fallback_trace::defaulted_raw();
        parallel_fallback.sort();

        assert_eq!(parallel.iter().map(canonical).collect::<Vec<_>>(), serial,);
        assert_eq!(parallel_fallback, serial_fallback);
        assert!(collect_batch_bindings_parallel(
            &rule, &arena, &graph, &interner, None, None, None, 1,
        )
        .is_none());
        crate::fallback_trace::reset();
    }

    #[test]
    fn match_distinct_node_constraint() {
        // Pattern: ?a -[knows]-> ?b. Self-loop should NOT match because
        // a and b would resolve to the same node.
        let (mut g, mut i, a) = setup_graph();
        let person = i.intern("Person");
        let knows = i.intern("knows");
        let alice = g.insert_node(person, FxHashMap::default());
        g.insert_edge(alice, knows, alice, FxHashMap::default())
            .unwrap();
        let rule = RewriteRule {
            name: i.intern("a_knows_b"),
            match_edges: vec![MatchEdge {
                src_var: i.intern("a"),
                edge_type: knows,
                tgt_var: i.intern("b"),
            }],
            where_: None,
            effects: vec![],
            ..Default::default()
        };
        assert!(match_rule(&rule, &a, &g, &i, None, None).is_none());
    }

    #[test]
    fn match_with_where_filters() {
        let (mut g, mut i, mut a) = setup_graph();
        let person = i.intern("Person");
        let knows = i.intern("knows");
        let name_key = i.intern("name");
        let alice_str = i.intern("alice");
        let mut alice_attrs = FxHashMap::default();
        alice_attrs.insert(name_key, Value::Str(alice_str));
        let alice = g.insert_node(person, alice_attrs);
        let bob = g.insert_node(person, FxHashMap::default());
        g.insert_edge(alice, knows, bob, FxHashMap::default())
            .unwrap();
        // Where: Attr(?a, "name") == "alice"
        let av = a.add(TermNode::Var {
            name: i.intern("a"),
        });
        let attr = a.add(TermNode::Attr {
            node: av,
            key: name_key,
        });
        let lit = a.add(TermNode::Lit {
            value: Value::Str(alice_str),
        });
        let eq = a.add(TermNode::Eq { a: attr, b: lit });
        let rule = RewriteRule {
            name: i.intern("named_alice"),
            match_edges: vec![MatchEdge {
                src_var: i.intern("a"),
                edge_type: knows,
                tgt_var: i.intern("b"),
            }],
            where_: Some(eq),
            effects: vec![],
            ..Default::default()
        };
        assert!(match_rule(&rule, &a, &g, &i, None, None).is_some());
    }

    #[test]
    fn apply_add_edge_lands_in_graph() {
        let (mut g, mut i, a) = setup_graph();
        let person = i.intern("Person");
        let likes = i.intern("likes");
        let knows = i.intern("knows");
        let alice = g.insert_node(person, FxHashMap::default());
        let bob = g.insert_node(person, FxHashMap::default());
        g.insert_edge(alice, knows, bob, FxHashMap::default())
            .unwrap();
        // Rule: ?a -[knows]-> ?b ⇒ add ?a -[likes]-> ?b
        let rule = RewriteRule {
            name: i.intern("knows_implies_likes"),
            match_edges: vec![MatchEdge {
                src_var: i.intern("a"),
                edge_type: knows,
                tgt_var: i.intern("b"),
            }],
            where_: None,
            effects: vec![Effect::AddEdge {
                src_var: i.intern("a"),
                edge_type: likes,
                tgt_var: i.intern("b"),
                attrs: vec![],
            }],
            ..Default::default()
        };
        let mut interner = i;
        let b = match_rule(&rule, &a, &g, &interner, None, None).unwrap();
        let mut a = a;
        let _undo = apply_rule(&rule, &b, &mut a, &mut g, &mut interner, None, None, false);
        assert!(g.has_edge(alice, likes, bob));
    }

    #[test]
    fn apply_with_undo_round_trips() {
        let (mut g, mut i, mut a) = setup_graph();
        let person = i.intern("Person");
        let label = i.intern("label");
        let likes = i.intern("likes");
        let knows = i.intern("knows");
        let alice = g.insert_node(person, FxHashMap::default());
        let bob = g.insert_node(person, FxHashMap::default());
        g.insert_edge(alice, knows, bob, FxHashMap::default())
            .unwrap();
        // Effects: add likes edge + set_attr(b, label, "friend")
        let lit_friend = a.add(TermNode::Lit {
            value: Value::Str(i.intern("friend")),
        });
        let rule = RewriteRule {
            name: i.intern("friend_tag"),
            match_edges: vec![MatchEdge {
                src_var: i.intern("a"),
                edge_type: knows,
                tgt_var: i.intern("b"),
            }],
            where_: None,
            effects: vec![
                Effect::AddEdge {
                    src_var: i.intern("a"),
                    edge_type: likes,
                    tgt_var: i.intern("b"),
                    attrs: vec![],
                },
                Effect::SetAttr {
                    var: i.intern("b"),
                    key: label,
                    value: EffectArg::Computed(lit_friend),
                },
            ],
            ..Default::default()
        };
        let nodes_before = g.node_count();
        let edges_before = g.edge_count();
        let attr_before = g.node(bob).attrs.get(&label).cloned();
        let mut interner = i;
        let b = match_rule(&rule, &a, &g, &interner, None, None).unwrap();
        let mut a = a;
        let undo = apply_rule(&rule, &b, &mut a, &mut g, &mut interner, None, None, true);
        assert!(g.has_edge(alice, likes, bob));
        assert_eq!(
            g.node(bob).attrs.get(&label),
            Some(&Value::Str(interner.lookup("friend").unwrap()))
        );
        // Roll back; everything restored.
        undo_apply(undo, &mut g);
        assert!(!g.has_edge(alice, likes, bob));
        assert_eq!(g.node(bob).attrs.get(&label).cloned(), attr_before);
        assert_eq!(g.node_count(), nodes_before);
        assert_eq!(g.edge_count(), edges_before);
    }

    #[test]
    fn run_rules_reaches_fixed_point() {
        // Transitive closure rule: ?a -[r]-> ?b -[r]-> ?c ⇒ ?a -[r]-> ?c
        let (mut g, mut i, a) = setup_graph();
        let n = i.intern("N");
        let r = i.intern("r");
        let n1 = g.insert_node(n, FxHashMap::default());
        let n2 = g.insert_node(n, FxHashMap::default());
        let n3 = g.insert_node(n, FxHashMap::default());
        g.insert_edge(n1, r, n2, FxHashMap::default()).unwrap();
        g.insert_edge(n2, r, n3, FxHashMap::default()).unwrap();
        let rule = RewriteRule {
            name: i.intern("transitive"),
            match_edges: vec![
                MatchEdge {
                    src_var: i.intern("a"),
                    edge_type: r,
                    tgt_var: i.intern("b"),
                },
                MatchEdge {
                    src_var: i.intern("b"),
                    edge_type: r,
                    tgt_var: i.intern("c"),
                },
            ],
            where_: None,
            effects: vec![Effect::AddEdge {
                src_var: i.intern("a"),
                edge_type: r,
                tgt_var: i.intern("c"),
                attrs: vec![],
            }],
            ..Default::default()
        };
        let mut interner = i;
        let mut a = a;
        let steps = run_rules(
            &[&rule],
            &mut a,
            &mut g,
            &mut interner,
            None,
            None,
            None,
            &[None],
            100,
        );
        // Should fire once (n1 -r-> n3 was missing, then no more
        // matches because no new ?a -[r]-> ?b -[r]-> ?c chain exists
        // that doesn't already have the transitive edge).
        assert!(steps >= 1);
        assert!(g.has_edge(n1, r, n3));
    }

    #[test]
    fn reorder_prefers_connected_edges() {
        // Original pattern (badly authored): ?a -[r1]-> ?b , ?c -[r2]-> ?d
        // -- two disconnected components, then ?b -[r3]-> ?c connects.
        // The first edge in the input has no connection to anything else
        // yet (?a, ?b new); the second is also disconnected (?c, ?d new);
        // only the third connects ?b<->?c.
        //
        // After reorder, the third edge (the connector) should NOT be
        // last — the reorder picks a starting edge, then prefers edges
        // sharing vars with bound set. Here the reorder should ensure
        // that whichever edge comes second has at least one shared var
        // with the first.
        let mut i = Interner::new();
        let r1 = i.intern("r1");
        let r2 = i.intern("r2");
        let r3 = i.intern("r3");
        let a = i.intern("a");
        let b = i.intern("b");
        let c = i.intern("c");
        let d = i.intern("d");
        let input = vec![
            MatchEdge {
                src_var: a,
                edge_type: r1,
                tgt_var: b,
            },
            MatchEdge {
                src_var: c,
                edge_type: r2,
                tgt_var: d,
            },
            MatchEdge {
                src_var: b,
                edge_type: r3,
                tgt_var: c,
            },
        ];
        // Fake cardinality table: r3 is RARER than r1/r2.
        let card = |et: Sym| -> usize {
            if et == r1 {
                100
            } else if et == r2 {
                100
            } else if et == r3 {
                5
            } else {
                999
            }
        };
        let reordered = reorder_match_edges(&input, card);
        assert_eq!(reordered.len(), 3);
        // First edge is the rarest (r3) — best starting cardinality.
        assert_eq!(reordered[0].edge_type, r3);
        // Subsequent edges share at least one var with bound set so the
        // matcher never hits the both-unbound expensive path.
        let mut bound: rustc_hash::FxHashSet<Sym> = Default::default();
        bound.insert(reordered[0].src_var);
        bound.insert(reordered[0].tgt_var);
        for me in &reordered[1..] {
            assert!(
                bound.contains(&me.src_var) || bound.contains(&me.tgt_var),
                "edge {:?} -> {:?} not connected to bound set {:?}",
                me.src_var,
                me.tgt_var,
                bound
            );
            bound.insert(me.src_var);
            bound.insert(me.tgt_var);
        }
    }

    #[test]
    fn reorder_preserves_single_edge_rules() {
        let mut i = Interner::new();
        let r = i.intern("r");
        let a = i.intern("a");
        let b = i.intern("b");
        let single = vec![MatchEdge {
            src_var: a,
            edge_type: r,
            tgt_var: b,
        }];
        let reordered = reorder_match_edges(&single, |_| 1);
        assert_eq!(reordered.len(), 1);
        assert_eq!(reordered[0].edge_type, r);
    }

    // --- R10 join-index hint tests ------------------------------------

    /// Builds the `rule_mention_resolves_to_concept` SHAPE generically:
    /// `(agent, knows_concept, c)` x `(m, has_mention, mention)`, joined only
    /// by `Eq(Attr(mention,"text"), Attr(c,"name"))` — no shared match var.
    fn build_join_rule(i: &mut Interner, a: &mut TermArena, with_hint: bool) -> RewriteRule {
        let knows = i.intern("knows_concept");
        let has_mention = i.intern("has_mention");
        let text_key = i.intern("text");
        let name_key = i.intern("name");
        let agent_v = i.intern("agent");
        let c_v = i.intern("c");
        let m_v = i.intern("m");
        let mention_v = i.intern("mention");
        let mention_ref = a.add(TermNode::Var { name: mention_v });
        let text_attr = a.add(TermNode::Attr {
            node: mention_ref,
            key: text_key,
        });
        let c_ref = a.add(TermNode::Var { name: c_v });
        let name_attr = a.add(TermNode::Attr {
            node: c_ref,
            key: name_key,
        });
        let eq = a.add(TermNode::Eq {
            a: text_attr,
            b: name_attr,
        });
        RewriteRule {
            name: i.intern("join_rule"),
            match_edges: vec![
                MatchEdge {
                    src_var: agent_v,
                    edge_type: knows,
                    tgt_var: c_v,
                },
                MatchEdge {
                    src_var: m_v,
                    edge_type: has_mention,
                    tgt_var: mention_v,
                },
            ],
            where_: Some(eq),
            effects: vec![],
            index_hints: if with_hint {
                vec![IndexJoinHint {
                    for_var: c_v,
                    probe: IndexProbe::BoundAttr { via_var: mention_v, via_key: text_key },
                    node_type: i.intern("Concept"),
                    this_key: name_key,
                }]
            } else {
                vec![]
            },
            ..Default::default()
        }
    }

    #[test]
    fn hinted_join_finds_same_match_as_unindexed() {
        let (mut g, mut i, mut a) = setup_graph();
        let concept_t = i.intern("Concept");
        let mention_t = i.intern("Mention");
        let name_key = i.intern("name");
        let text_key = i.intern("text");
        let moon_str = i.intern("moon");
        let mars_str = i.intern("mars");

        let mut moon_attrs = FxHashMap::default();
        moon_attrs.insert(name_key, Value::Str(moon_str));
        let moon_c = g.insert_node(concept_t, moon_attrs);
        let mut mars_attrs = FxHashMap::default();
        mars_attrs.insert(name_key, Value::Str(mars_str));
        let mars_c = g.insert_node(concept_t, mars_attrs);

        let agent = g.insert_node(i.intern("Agent"), FxHashMap::default());
        let knows = i.intern("knows_concept");
        g.insert_edge(agent, knows, moon_c, FxHashMap::default())
            .unwrap();
        g.insert_edge(agent, knows, mars_c, FxHashMap::default())
            .unwrap();

        let mut mtn_attrs = FxHashMap::default();
        mtn_attrs.insert(text_key, Value::Str(moon_str));
        let mention_n = g.insert_node(mention_t, mtn_attrs);
        let m = g.insert_node(i.intern("Message"), FxHashMap::default());
        let has_mention = i.intern("has_mention");
        g.insert_edge(m, has_mention, mention_n, FxHashMap::default())
            .unwrap();

        // Declare the index -- the hinted rule's whole point.
        g.declare_attr_index(concept_t, name_key);

        let plain = build_join_rule(&mut i, &mut a, false);
        let hinted = build_join_rule(&mut i, &mut a, true);

        let b_plain = match_rule(&plain, &a, &g, &i, None, None).expect("plain should match");
        let b_hinted = match_rule(&hinted, &a, &g, &i, None, None).expect("hinted should match");
        let c_v = i.lookup("c").unwrap();
        // Both find the SAME concept (moon, not mars) -- correctness parity.
        assert_eq!(b_plain[&c_v], moon_c);
        assert_eq!(b_hinted[&c_v], moon_c);
    }

    #[test]
    fn hinted_join_prunes_bound_source_candidates() {
        let (mut g, mut i, _) = setup_graph();
        let agent_v = i.intern("agent");
        let request_v = i.intern("request");
        let episode_v = i.intern("episode");
        let agent_t = i.intern("Agent");
        let request_t = i.intern("MemoryRetrievalRequest");
        let episode_t = i.intern("Episode");
        let cue_key = i.intern("cue_key");
        let recorded = i.intern("recorded_episode");
        let cue = i.intern("target-cue");
        let agent = g.insert_node(agent_t, FxHashMap::default());
        let request = g.insert_node(request_t, {
            let mut attrs = FxHashMap::default();
            attrs.insert(cue_key, Value::Str(cue));
            attrs
        });
        let mut expected = None;
        for n in 0..128 {
            let mut attrs = FxHashMap::default();
            let value = if n == 73 {
                cue
            } else {
                i.intern(&format!("cue-{n}"))
            };
            attrs.insert(cue_key, Value::Str(value));
            let episode = g.insert_node(episode_t, attrs);
            g.insert_edge(agent, recorded, episode, FxHashMap::default())
                .unwrap();
            if n == 73 {
                expected = Some(episode);
            }
        }
        g.declare_attr_index(episode_t, cue_key);
        let hint = IndexJoinHint {
            for_var: episode_v,
            probe: IndexProbe::BoundAttr { via_var: request_v, via_key: cue_key },
            node_type: episode_t,
            this_key: cue_key,
        };
        let rule = RewriteRule {
            match_edges: vec![MatchEdge {
                src_var: agent_v,
                edge_type: recorded,
                tgt_var: episode_v,
            }],
            index_hints: vec![hint],
            ..Default::default()
        };
        let mut binding = Binding::default();
        binding.insert(agent_v, agent);
        binding.insert(request_v, request);
        let candidates = hinted_candidates(&rule, agent_v, recorded, episode_v, &binding, &g)
            .expect("declared cue index and bound request enable the hint");
        assert_eq!(candidates, vec![(agent, expected.unwrap())]);

        // Index maintenance on an attribute update must immediately move the
        // episode out of the requested cue bucket.
        g.set_node_attr(expected.unwrap(), cue_key, Value::Str(i.intern("changed")));
        assert!(
            hinted_candidates(&rule, agent_v, recorded, episode_v, &binding, &g,)
                .unwrap()
                .is_empty()
        );
    }

    #[test]
    fn literal_index_probe_prunes_exact_attribute_value() {
        let (mut g, mut i, _) = setup_graph();
        let agent_v = i.intern("agent");
        let message_v = i.intern("m");
        let agent_t = i.intern("Agent");
        let message_t = i.intern("Message");
        let from_key = i.intern("from");
        let received = i.intern("received");
        let interlocutor = i.intern("interlocutor");
        let agent = g.insert_node(agent_t, FxHashMap::default());
        let mut expected = None;
        for value in [interlocutor, i.intern("system"), interlocutor] {
            let message = g.insert_node(message_t, {
                let mut attrs = FxHashMap::default();
                attrs.insert(from_key, Value::Str(value));
                attrs
            });
            g.insert_edge(agent, received, message, FxHashMap::default()).unwrap();
            if value == interlocutor { expected = Some(message); }
        }
        g.declare_attr_index(message_t, from_key);
        let rule = RewriteRule {
            match_edges: vec![MatchEdge { src_var: agent_v, edge_type: received, tgt_var: message_v }],
            index_hints: vec![IndexJoinHint {
                for_var: message_v,
                probe: IndexProbe::LiteralString(interlocutor),
                node_type: message_t,
                this_key: from_key,
            }],
            ..Default::default()
        };
        let mut binding = Binding::default();
        binding.insert(agent_v, agent);
        let candidates = hinted_candidates(&rule, agent_v, received, message_v, &binding, &g)
            .expect("declared literal index enables pruning");
        assert_eq!(candidates.len(), 2);
        assert!(candidates.iter().all(|(_, m)| g.node(*m).attrs.get(&from_key) == Some(&Value::Str(interlocutor))));
        assert!(candidates.iter().any(|(_, m)| *m == expected.unwrap()));
    }

    #[test]
    fn hinted_join_falls_back_correctly_when_index_not_declared() {
        // Same graph, but the index is NEVER declared -- hinted_candidates
        // must return None and the matcher must fall back to the exact
        // original (correct) behaviour, not silently find nothing.
        let (mut g, mut i, mut a) = setup_graph();
        let concept_t = i.intern("Concept");
        let mention_t = i.intern("Mention");
        let name_key = i.intern("name");
        let text_key = i.intern("text");
        let moon_str = i.intern("moon");

        let mut moon_attrs = FxHashMap::default();
        moon_attrs.insert(name_key, Value::Str(moon_str));
        let moon_c = g.insert_node(concept_t, moon_attrs);
        let agent = g.insert_node(i.intern("Agent"), FxHashMap::default());
        let knows = i.intern("knows_concept");
        g.insert_edge(agent, knows, moon_c, FxHashMap::default())
            .unwrap();
        let mut mtn_attrs = FxHashMap::default();
        mtn_attrs.insert(text_key, Value::Str(moon_str));
        let mention_n = g.insert_node(mention_t, mtn_attrs);
        let m = g.insert_node(i.intern("Message"), FxHashMap::default());
        let has_mention = i.intern("has_mention");
        g.insert_edge(m, has_mention, mention_n, FxHashMap::default())
            .unwrap();
        // NOTE: no g.declare_attr_index call.

        let hinted = build_join_rule(&mut i, &mut a, true);
        let b = match_rule(&hinted, &a, &g, &i, None, None).expect("should still match");
        assert_eq!(b[&i.lookup("c").unwrap()], moon_c);
    }

    #[test]
    fn hinted_join_no_false_positive_for_mismatched_text() {
        // A mention whose text matches NO held concept must still find no
        // match -- the index only PRUNES candidates, it never invents one
        // (index-then-verify).
        let (mut g, mut i, mut a) = setup_graph();
        let concept_t = i.intern("Concept");
        let mention_t = i.intern("Mention");
        let name_key = i.intern("name");
        let text_key = i.intern("text");
        let moon_str = i.intern("moon");
        let unrelated_str = i.intern("unrelated_word");

        let mut moon_attrs = FxHashMap::default();
        moon_attrs.insert(name_key, Value::Str(moon_str));
        let moon_c = g.insert_node(concept_t, moon_attrs);
        let agent = g.insert_node(i.intern("Agent"), FxHashMap::default());
        let knows = i.intern("knows_concept");
        g.insert_edge(agent, knows, moon_c, FxHashMap::default())
            .unwrap();
        let mut mtn_attrs = FxHashMap::default();
        mtn_attrs.insert(text_key, Value::Str(unrelated_str));
        let mention_n = g.insert_node(mention_t, mtn_attrs);
        let m = g.insert_node(i.intern("Message"), FxHashMap::default());
        let has_mention = i.intern("has_mention");
        g.insert_edge(m, has_mention, mention_n, FxHashMap::default())
            .unwrap();
        g.declare_attr_index(concept_t, name_key);

        let hinted = build_join_rule(&mut i, &mut a, true);
        assert!(match_rule(&hinted, &a, &g, &i, None, None).is_none());
    }

    #[test]
    fn reorder_with_hints_schedules_via_var_edge_first() {
        // Disconnected pattern where the FIRST edge (by cardinality tie)
        // would naturally be the hinted (c) edge -- reorder_match_edges_
        // with_hints must still schedule the mention edge first so
        // hinted_candidates' via_var precondition is met.
        let mut i = Interner::new();
        let agent_v = i.intern("agent");
        let c_v = i.intern("c");
        let m_v = i.intern("m");
        let mention_v = i.intern("mention");
        let knows = i.intern("knows_concept");
        let has_mention = i.intern("has_mention");
        let edges = vec![
            MatchEdge {
                src_var: agent_v,
                edge_type: knows,
                tgt_var: c_v,
            },
            MatchEdge {
                src_var: m_v,
                edge_type: has_mention,
                tgt_var: mention_v,
            },
        ];
        let hints = vec![IndexJoinHint {
            for_var: c_v,
            probe: IndexProbe::BoundAttr { via_var: mention_v, via_key: i.intern("text") },
            node_type: i.intern("Concept"),
            this_key: i.intern("name"),
        }];
        // Tie cardinality -- without hint-awareness the FIRST edge (index 0,
        // the c-edge) would win the tie and be scheduled first.
        let reordered = reorder_match_edges_with_hints(&edges, &hints, |_| 1);
        assert_eq!(
            reordered[0].edge_type, has_mention,
            "the mention edge (which binds via_var) must be scheduled before the hinted c-edge"
        );
        assert_eq!(reordered[1].edge_type, knows);
    }

    #[test]
    fn add_rule_auto_declares_hint_index() {
        // substrate.rs::add_rule must auto-provision the declared index from
        // a rule's index_hints -- no separate Python/world-adapter call
        // needed.
        use crate::checker::ConsistencyChecker;
        use crate::grammar::Grammar;
        let mut s = crate::substrate::Substrate::new(ConsistencyChecker::new(Grammar::new()));
        let concept_t = s.interner.intern("Concept");
        let name_key = s.interner.intern("name");
        assert!(!s.graph.has_attr_index(concept_t, name_key));
        let rule = build_join_rule(&mut s.interner, &mut s.terms, true);
        s.add_rule(rule);
        assert!(
            s.graph.has_attr_index(concept_t, name_key),
            "add_rule should have auto-declared the hint's attr index"
        );
    }

    #[test]
    fn replace_value_rewires_all_uses() {
        // LLVM-style use rewiring: 3 instructions reference the same
        // %result Value; after ReplaceValue, all three reference the
        // new Value instead.
        let (mut g, mut i, a) = setup_graph();
        let instr_t = i.intern("LLVMInstruction");
        let value_t = i.intern("LLVMValue");
        let uses_op0 = i.intern("uses_op0");
        let uses_op1 = i.intern("uses_op1");
        let inst1 = g.insert_node(instr_t, FxHashMap::default());
        let inst2 = g.insert_node(instr_t, FxHashMap::default());
        let inst3 = g.insert_node(instr_t, FxHashMap::default());
        let old_val = g.insert_node(value_t, FxHashMap::default());
        let new_val = g.insert_node(value_t, FxHashMap::default());
        // inst1 uses old_val as op0; inst2 uses it as op1; inst3 as op0.
        g.insert_edge(inst1, uses_op0, old_val, FxHashMap::default())
            .unwrap();
        g.insert_edge(inst2, uses_op1, old_val, FxHashMap::default())
            .unwrap();
        g.insert_edge(inst3, uses_op0, old_val, FxHashMap::default())
            .unwrap();

        // Rule: match a Value node bound to ?old and ?new directly
        // (this test uses a 0-edge match driven by ad-hoc binding —
        // we'll construct the binding manually).
        let rule = RewriteRule {
            name: i.intern("rewire"),
            match_edges: vec![],
            where_: None,
            effects: vec![Effect::ReplaceValue {
                old_var: i.intern("old"),
                new_var: i.intern("new"),
            }],
            ..Default::default()
        };
        let mut interner = i;
        let mut binding: Binding = FxHashMap::default();
        binding.insert(interner.intern("old"), old_val);
        binding.insert(interner.intern("new"), new_val);

        let mut a = a;
        let outcome = apply_rule_full(
            &rule,
            &binding,
            &mut a,
            &mut g,
            &mut interner,
            None,
            None,
            None,
            true,
        );
        assert!(outcome.progressed);

        // Every use is now of new_val; old_val has zero incoming edges.
        assert!(g.has_edge(inst1, uses_op0, new_val));
        assert!(g.has_edge(inst2, uses_op1, new_val));
        assert!(g.has_edge(inst3, uses_op0, new_val));
        assert!(!g.has_edge(inst1, uses_op0, old_val));
        assert!(!g.has_edge(inst2, uses_op1, old_val));
        assert!(!g.has_edge(inst3, uses_op0, old_val));
        assert_eq!(g.in_edges_slice(old_val, None).len(), 0);
        assert_eq!(g.in_edges_slice(new_val, None).len(), 3);

        // Undo restores the original use-graph.
        undo_apply(outcome.undo, &mut g);
        assert!(g.has_edge(inst1, uses_op0, old_val));
        assert!(g.has_edge(inst2, uses_op1, old_val));
        assert!(g.has_edge(inst3, uses_op0, old_val));
        assert_eq!(g.in_edges_slice(new_val, None).len(), 0);
    }

    #[test]
    fn replace_value_noop_on_same_var() {
        let (mut g, mut i, a) = setup_graph();
        let value_t = i.intern("LLVMValue");
        let v = g.insert_node(value_t, FxHashMap::default());
        let rule = RewriteRule {
            name: i.intern("noop"),
            match_edges: vec![],
            where_: None,
            effects: vec![Effect::ReplaceValue {
                old_var: i.intern("x"),
                new_var: i.intern("x"),
            }],
            ..Default::default()
        };
        let mut interner = i;
        let mut binding: Binding = FxHashMap::default();
        binding.insert(interner.intern("x"), v);
        let mut a = a;
        let outcome = apply_rule_full(
            &rule,
            &binding,
            &mut a,
            &mut g,
            &mut interner,
            None,
            None,
            None,
            false,
        );
        assert!(!outcome.progressed);
    }

    // ---- AddNodeIfAbsent ------------------------------------------------

    #[test]
    fn add_node_if_absent_inserts_when_no_match_exists() {
        // First application: no existing CandidateMeaning with
        // (surface="dog", target="dog") — should insert + progress.
        let (mut g, mut i, mut a) = setup_graph();
        let cand_t = i.intern("CandidateMeaning");
        let unknown_t = i.intern("Unknown");
        let evid_e = i.intern("evidence_for");
        let unknown = g.insert_node(unknown_t, FxHashMap::default());
        g.insert_edge(unknown, evid_e, unknown, FxHashMap::default())
            .unwrap();
        let surf_key = i.intern("surface");
        let dog_str = Value::Str(i.intern("dog"));
        let lit_surface = a.add(crate::term::TermNode::Lit {
            value: dog_str.clone(),
        });
        let rule = RewriteRule {
            name: i.intern("emit_once"),
            match_edges: vec![MatchEdge {
                src_var: i.intern("u"),
                edge_type: evid_e,
                tgt_var: i.intern("u"),
            }],
            where_: None,
            effects: vec![Effect::AddNodeIfAbsent {
                new_var: i.intern("cm"),
                type_: cand_t,
                attrs: vec![(surf_key, EffectArg::Computed(lit_surface))],
            }],
            ..Default::default()
        };
        let mut interner = i;
        let mut binding: Binding = FxHashMap::default();
        binding.insert(interner.intern("u"), unknown);
        let outcome = apply_rule_full(
            &rule,
            &binding,
            &mut a,
            &mut g,
            &mut interner,
            None,
            None,
            None,
            true,
        );
        assert!(outcome.progressed, "first apply should progress");
        assert_eq!(g.nodes_of_type(cand_t).len(), 1);
    }

    #[test]
    fn add_node_if_absent_skips_when_match_exists() {
        // Second application against the same dedup key should be a
        // no-op: no new node, no progress.
        let (mut g, mut i, mut a) = setup_graph();
        let cand_t = i.intern("CandidateMeaning");
        let surf_key = i.intern("surface");
        let dog_str = Value::Str(i.intern("dog"));
        // Pre-populate one CandidateMeaning(surface="dog").
        let mut attrs = FxHashMap::default();
        attrs.insert(surf_key, dog_str.clone());
        let existing = g.insert_node(cand_t, attrs);
        // Build a 0-edge rule + manual binding (the matching machinery
        // isn't exercised here; we just want the effect path).
        let lit = a.add(crate::term::TermNode::Lit { value: dog_str });
        let rule = RewriteRule {
            name: i.intern("emit_once"),
            match_edges: vec![],
            where_: None,
            effects: vec![Effect::AddNodeIfAbsent {
                new_var: i.intern("cm"),
                type_: cand_t,
                attrs: vec![(surf_key, EffectArg::Computed(lit))],
            }],
            ..Default::default()
        };
        let mut interner = i;
        let binding: Binding = FxHashMap::default();
        let outcome = apply_rule_full(
            &rule,
            &binding,
            &mut a,
            &mut g,
            &mut interner,
            None,
            None,
            None,
            true,
        );
        assert!(!outcome.progressed, "second apply should NOT progress");
        // Still only one CandidateMeaning.
        let candidates = g.nodes_of_type(cand_t);
        assert_eq!(candidates.len(), 1);
        assert_eq!(candidates[0], existing);
        assert!(outcome.undo.is_empty(), "no UndoStep for a skipped insert");
    }

    #[test]
    fn add_node_if_absent_attrs_are_subset_match() {
        // Existing node carries extra attrs — the AddNodeIfAbsent
        // attrs are the dedup key, not the full equality test.
        let (mut g, mut i, mut a) = setup_graph();
        let cand_t = i.intern("CandidateMeaning");
        let surf_key = i.intern("surface");
        let weight_key = i.intern("weight");
        let dog_str = Value::Str(i.intern("dog"));
        let mut attrs = FxHashMap::default();
        attrs.insert(surf_key, dog_str.clone());
        attrs.insert(weight_key, Value::Float(0.6));
        g.insert_node(cand_t, attrs);
        let lit = a.add(crate::term::TermNode::Lit { value: dog_str });
        let rule = RewriteRule {
            name: i.intern("emit_once"),
            match_edges: vec![],
            where_: None,
            effects: vec![Effect::AddNodeIfAbsent {
                new_var: i.intern("cm"),
                type_: cand_t,
                attrs: vec![(surf_key, EffectArg::Computed(lit))],
            }],
            ..Default::default()
        };
        let mut interner = i;
        let binding: Binding = FxHashMap::default();
        let outcome = apply_rule_full(
            &rule,
            &binding,
            &mut a,
            &mut g,
            &mut interner,
            None,
            None,
            None,
            true,
        );
        assert!(!outcome.progressed);
        assert_eq!(g.nodes_of_type(cand_t).len(), 1);
    }

    // ---- SetAttrIfDifferent --------------------------------------------

    #[test]
    fn set_attr_if_different_progresses_only_on_change() {
        let (mut g, mut i, mut a) = setup_graph();
        let t = i.intern("N");
        let key = i.intern("weight");
        let nid = g.insert_node(t, FxHashMap::default());
        // First write: attr absent → must progress + record undo.
        let lit_06 = a.add(crate::term::TermNode::Lit {
            value: Value::Float(0.6),
        });
        let rule = RewriteRule {
            name: i.intern("delta"),
            match_edges: vec![],
            where_: None,
            effects: vec![Effect::SetAttrIfDifferent {
                var: i.intern("n"),
                key,
                value: EffectArg::Computed(lit_06),
            }],
            ..Default::default()
        };
        let mut interner = i;
        let mut binding: Binding = FxHashMap::default();
        binding.insert(interner.intern("n"), nid);
        let outcome = apply_rule_full(
            &rule,
            &binding,
            &mut a,
            &mut g,
            &mut interner,
            None,
            None,
            None,
            true,
        );
        assert!(outcome.progressed, "first write should progress");
        assert_eq!(outcome.undo.len(), 1);
        assert_eq!(g.node(nid).attrs.get(&key), Some(&Value::Float(0.6)));

        // Re-apply with the same value: no progress, no undo.
        let outcome2 = apply_rule_full(
            &rule,
            &binding,
            &mut a,
            &mut g,
            &mut interner,
            None,
            None,
            None,
            true,
        );
        assert!(
            !outcome2.progressed,
            "same-value re-apply must NOT progress"
        );
        assert!(outcome2.undo.is_empty(), "no UndoStep for skipped write");
    }

    #[test]
    fn set_attr_if_different_writes_on_change() {
        let (mut g, mut i, mut a) = setup_graph();
        let t = i.intern("N");
        let key = i.intern("weight");
        let mut attrs = FxHashMap::default();
        attrs.insert(key, Value::Float(0.3));
        let nid = g.insert_node(t, attrs);
        let lit_09 = a.add(crate::term::TermNode::Lit {
            value: Value::Float(0.9),
        });
        let rule = RewriteRule {
            name: i.intern("delta"),
            match_edges: vec![],
            where_: None,
            effects: vec![Effect::SetAttrIfDifferent {
                var: i.intern("n"),
                key,
                value: EffectArg::Computed(lit_09),
            }],
            ..Default::default()
        };
        let mut interner = i;
        let mut binding: Binding = FxHashMap::default();
        binding.insert(interner.intern("n"), nid);
        let outcome = apply_rule_full(
            &rule,
            &binding,
            &mut a,
            &mut g,
            &mut interner,
            None,
            None,
            None,
            true,
        );
        assert!(outcome.progressed);
        assert_eq!(g.node(nid).attrs.get(&key), Some(&Value::Float(0.9)));
        undo_apply(outcome.undo, &mut g);
        assert_eq!(g.node(nid).attrs.get(&key), Some(&Value::Float(0.3)));
    }

    // ---- perception-as-action: FbFrameSeq in a rule's where-clause ------

    /// Write a valid fb header (no pixel payload needed — the where-clause
    /// under test only reads `frame_seq`) to a `/dev/shm`-backed file and
    /// open it via `FbHandle::open` — the same integration path
    /// `Substrate::fb_attach` uses, kept self-contained like
    /// `term.rs::tests::fb_frame_seq_term_reads_current_seq_when_threaded`
    /// (FbHandle's fields are private, so a real header-shaped file is the
    /// only way to build one from a test).
    fn write_fb_file(tag: &str, seq: u64) -> (String, String) {
        let width: u32 = 1;
        let height: u32 = 1;
        let stride = width * 4;
        let name = format!("/jbw_fb_rewrite_test_{}_{}", tag, std::process::id());
        let path = format!("/dev/shm/{}", name.trim_start_matches('/'));
        use std::io::Write;
        let mut f = std::fs::OpenOptions::new()
            .create(true)
            .write(true)
            .truncate(true)
            .open(&path)
            .expect("write /dev/shm test fb (skip if /dev/shm unavailable)");
        let mut buf = vec![0u8; crate::framebuffer::FB_HEADER_LEN + (height * stride) as usize];
        buf[0..4].copy_from_slice(&crate::framebuffer::FB_MAGIC.to_le_bytes());
        buf[4..8].copy_from_slice(&crate::framebuffer::FB_VERSION.to_le_bytes());
        buf[8..12].copy_from_slice(&width.to_le_bytes());
        buf[12..16].copy_from_slice(&height.to_le_bytes());
        buf[16..20].copy_from_slice(&stride.to_le_bytes());
        buf[20..24].copy_from_slice(&crate::framebuffer::FB_FORMAT_BGRA8888.to_le_bytes());
        buf[24..32].copy_from_slice(&seq.to_le_bytes());
        f.write_all(&buf).unwrap();
        (name, path)
    }

    /// The canonical "look rule" shape: `?g` is a Game node bound via a
    /// `wants_look` match-edge from a trigger node; the where-clause opens
    /// only when the attached framebuffer's `frame_seq` has advanced past
    /// `?g`'s stored `last_looked_seq` watermark. Proves the gate itself —
    /// closed with no `framebuffers` threaded (today's non-rule-engine
    /// call sites), open once threaded AND the frame is newer than the
    /// watermark, closed again once the watermark catches up (the
    /// no-churn property `tests/test_rule_driven_look.py` exercises
    /// end-to-end against a live writer).
    #[test]
    fn fb_frame_seq_gates_where_clause() {
        use rustc_hash::FxHashMap as FxMap;

        let (mut g, mut i, mut a) = setup_graph();
        let trigger_t = i.intern("LookTrigger");
        let game_t = i.intern("Game");
        let wants_look = i.intern("wants_look");
        let last_seq_key = i.intern("last_looked_seq");
        let trigger = g.insert_node(trigger_t, FxHashMap::default());
        let mut game_attrs: FxHashMap<Sym, Value> = FxHashMap::default();
        game_attrs.insert(last_seq_key, Value::Int(3));
        let game = g.insert_node(game_t, game_attrs);
        g.insert_edge(trigger, wants_look, game, FxHashMap::default())
            .unwrap();

        let t_var = i.intern("t");
        let g_var = i.intern("g");
        let g_ref = a.add(TermNode::Var { name: g_var });
        let attr_term = a.add(TermNode::Attr {
            node: g_ref,
            key: last_seq_key,
        });
        let fb_id_lit = a.add(TermNode::Lit {
            value: Value::Int(9),
        });
        let fbseq = a.add(TermNode::FbFrameSeq { fb: fb_id_lit });
        let where_term = a.add(TermNode::Gt {
            a: fbseq,
            b: attr_term,
        });

        let rule = RewriteRule {
            name: i.intern("look_when_frame_advances"),
            match_edges: vec![MatchEdge {
                src_var: t_var,
                edge_type: wants_look,
                tgt_var: g_var,
            }],
            where_: Some(where_term),
            effects: vec![],
            ..Default::default()
        };

        let (name, path) = write_fb_file("gate", 5);
        let handle =
            crate::framebuffer::FbHandle::open(&name).expect("open the /dev/shm file just written");
        let mut fbs: FxMap<u32, crate::framebuffer::FbHandle> = FxMap::default();
        fbs.insert(9, handle);

        // 1) Not threaded (today's non-rule-engine EvalCtx posture, and
        //    what every call site did before this change): FbFrameSeq
        //    evaluates to None, Gt(None, 3) is false -> no match.
        assert!(
            match_rule(&rule, &a, &g, &i, None, None).is_none(),
            "without framebuffers threaded the gate must stay closed"
        );

        // 2) Threaded, current frame_seq (5) > the stored watermark (3)
        //    -> the gate opens.
        assert!(
            match_rule(&rule, &a, &g, &i, None, Some(&fbs)).is_some(),
            "gate must open once the attached frame_seq exceeds the watermark"
        );

        // 3) Advance the watermark to 5 (what the rule's own effect would
        //    do via SetAttr(?g, "last_looked_seq", FbFrameSeq(fb)) after
        //    firing) — the SAME still-unchanged frame_seq no longer opens
        //    the gate: the rule stops firing once caught up (no churn).
        g.set_node_attr(game, last_seq_key, Value::Int(5));
        assert!(
            match_rule(&rule, &a, &g, &i, None, Some(&fbs)).is_none(),
            "gate must close again once the watermark catches up to frame_seq"
        );

        drop(fbs);
        let _ = std::fs::remove_file(&path);
    }

    // -- SetRuleClause: Surface-typed (StringConcat) names must coerce, --
    // -- and a genuinely untypeable name must fail LOUDLY, never silently. --

    #[test]
    fn set_rule_clause_coerces_string_concat_surface_to_pending_edit() {
        // A StringConcat-built rule name evaluates to Value::Surface(Text),
        // NOT Value::Str. This is the fix for the pinned WALL documented in
        // tests/test_rule_minting_dialect.py (module docstring finding 4,
        // formerly test_string_concat_yields_surface_not_str_a_dialect_wall,
        // now test_string_concat_surface_coerces_and_mints): the coerced
        // name must still land on graph.pending_rule_edits as a plain owned
        // String, exactly as a Value::Str literal name would.
        let (mut g, mut i, mut a) = setup_graph();
        let prefix = a.add(TermNode::Lit {
            value: Value::Str(i.intern("prefix_")),
        });
        let suffix = a.add(TermNode::Lit {
            value: Value::Str(i.intern("concat_test")),
        });
        let concat = a.add(TermNode::StringConcat {
            parts: vec![prefix, suffix],
        });

        let rule = RewriteRule {
            name: i.intern("mint_via_concat"),
            match_edges: vec![],
            where_: None,
            effects: vec![Effect::SetRuleClause {
                rule_name: EffectArg::Computed(concat),
                field: EffectArg::Literal(Value::Str(i.intern("where"))),
                term: EffectArg::Literal(Value::Bool(true)),
            }],
            ..Default::default()
        };
        let b: Binding = FxHashMap::default();
        let outcome = apply_rule_full(&rule, &b, &mut a, &mut g, &mut i, None, None, None, false);
        assert!(
            outcome.progressed,
            "SetRuleClause with a Surface-typed name must still progress"
        );
        assert_eq!(
            g.pending_rule_edits.len(),
            1,
            "the coerced name must be queued exactly once"
        );
        let (name_s, field_s, _term_v) = &g.pending_rule_edits[0];
        assert_eq!(name_s, "prefix_concat_test");
        assert_eq!(field_s, "where");
    }

    #[test]
    fn set_rule_clause_untypeable_name_is_rejected_not_silently_dropped() {
        // A name that is genuinely not string-shaped at all (an Int here,
        // neither Value::Str nor Value::Surface(Text)) must never be
        // queued. Per CLAUDE.md's "no silent failure in self-authoring"
        // rule, the applier now also prints a "[self-repair] SetRuleClause:
        // ... did not resolve to a string-shaped value ..." diagnostic on
        // this path (see the Effect::SetRuleClause arm) -- this test
        // exercises exactly that branch (the previous test exercises the
        // sibling success branch of the same match), and pins the
        // behavioural half: no pending edit is queued and no progress is
        // reported.
        let (mut g, mut i, mut a) = setup_graph();
        let rule = RewriteRule {
            name: i.intern("bad_mint"),
            match_edges: vec![],
            where_: None,
            effects: vec![Effect::SetRuleClause {
                rule_name: EffectArg::Literal(Value::Int(42)),
                field: EffectArg::Literal(Value::Str(i.intern("where"))),
                term: EffectArg::Literal(Value::Bool(true)),
            }],
            ..Default::default()
        };
        let b: Binding = FxHashMap::default();
        let outcome = apply_rule_full(&rule, &b, &mut a, &mut g, &mut i, None, None, None, false);
        assert!(
            !outcome.progressed,
            "an untypeable name must not report progress"
        );
        assert!(
            g.pending_rule_edits.is_empty(),
            "an untypeable name must never be queued"
        );
    }

    // --- PREDICATE PUSHDOWN (2026-07-17) --------------------------------
    //
    // THE INVARIANT: pushdown reorders WHEN a conjunct is evaluated, never
    // WHETHER a binding is admitted. Both paths are recomputed LIVE and
    // compared (PROTOCOL §12.3 — never freeze a digest/constant into a gate;
    // two gates rotted the same day they were written by doing that).

    /// Builds `wv_propagate`'s EXACT shape on a real grid:
    ///   match: (r has_cell c), (c neighbour n)
    ///   where: And[ Eq(Attr(c,"state"),"active"),
    ///               Eq(Attr(c,"activated_at"), Attr(r,"step")),
    ///               Eq(Attr(n,"state"),"rested") ]
    /// `active_every` cells are `active` — the real retina is ~1.5% active,
    /// which is exactly why pushdown pays.
    fn build_propagate_shape(
        i: &mut Interner,
        a: &mut TermArena,
        g: &mut TypedGraph,
        side: usize,
        active_every: usize,
    ) -> RewriteRule {
        let retina_t = i.intern("Retina");
        let cell_t = i.intern("RetinaCell");
        let has_cell = i.intern("has_cell");
        let neighbour = i.intern("neighbour");
        let state_k = i.intern("state");
        let act_at_k = i.intern("activated_at");
        let step_k = i.intern("step");
        let row_k = i.intern("row");

        let mut ratrs: FxHashMap<Sym, Value> = FxHashMap::default();
        ratrs.insert(step_k, Value::Int(7));
        let retina = g.insert_node(retina_t, ratrs);

        let mut cells = Vec::new();
        for idx in 0..(side * side) {
            let mut at: FxHashMap<Sym, Value> = FxHashMap::default();
            // Attrs BEFORE `state` so the linear-scan attr map is realistic.
            at.insert(row_k, Value::Int((idx / side) as i64));
            // EVERY conjunct must DISCRIMINATE, or the gate is vacuous — the
            // first cut had all active cells at activated_at == step and all
            // neighbours rested, so dropping conjuncts 1/2 changed nothing and
            // the negative control could not go red. So:
            //   - `active` cells exist (conjunct 0 bites),
            //   - some active cells are STALE (activated_at != step) so the
            //     phase guard, conjunct 1, bites,
            //   - some cells are `refractory`, so conjunct 1's neighbour test
            //     (n.state == "rested"), conjunct 2, bites.
            let active = idx % active_every == 0;
            let refractory = !active && idx % active_every == 1;
            let stale = active && (idx / active_every) % 2 == 1;
            let state = if active {
                "active"
            } else if refractory {
                "refractory"
            } else {
                "rested"
            };
            at.insert(state_k, Value::Str(i.intern(state)));
            // A `refractory` cell carries activated_at == step (it fired THIS
            // step and refracted — exactly what wv_refract leaves behind). So
            // conjunct 1 does NOT imply conjunct 0, and conjunct 0 bites too.
            // Without this, activated_at==step held only for active cells and
            // dropping conjunct 0 changed nothing (caught by this control).
            at.insert(
                act_at_k,
                Value::Int(if refractory {
                    7
                } else if !active {
                    -999
                } else if stale {
                    3
                } else {
                    7
                }),
            );
            let n = g.insert_node(cell_t, at);
            g.insert_edge(retina, has_cell, n, FxHashMap::default());
            cells.push(n);
        }
        // 4-neighbourhood, as `wave_world` wires it.
        for idx in 0..(side * side) {
            let (r0, c0) = (idx / side, idx % side);
            for (dr, dc) in [(-1i64, 0i64), (1, 0), (0, -1), (0, 1)] {
                let (nr, nc) = (r0 as i64 + dr, c0 as i64 + dc);
                if nr < 0 || nc < 0 || nr >= side as i64 || nc >= side as i64 {
                    continue;
                }
                let m = cells[(nr as usize) * side + nc as usize];
                g.insert_edge(cells[idx], neighbour, m, FxHashMap::default());
            }
        }

        let r_v = i.intern("r");
        let c_v = i.intern("c");
        let n_v = i.intern("n");
        let c_ref = a.add(TermNode::Var { name: c_v });
        let c_state = a.add(TermNode::Attr {
            node: c_ref,
            key: state_k,
        });
        let active_lit = a.add(TermNode::Lit {
            value: Value::Str(i.intern("active")),
        });
        let k0 = a.add(TermNode::Eq {
            a: c_state,
            b: active_lit,
        });

        let c_ref2 = a.add(TermNode::Var { name: c_v });
        let c_act = a.add(TermNode::Attr {
            node: c_ref2,
            key: act_at_k,
        });
        let r_ref = a.add(TermNode::Var { name: r_v });
        let r_step = a.add(TermNode::Attr {
            node: r_ref,
            key: step_k,
        });
        let k1 = a.add(TermNode::Eq {
            a: c_act,
            b: r_step,
        });

        let n_ref = a.add(TermNode::Var { name: n_v });
        let n_state = a.add(TermNode::Attr {
            node: n_ref,
            key: state_k,
        });
        let rested_lit = a.add(TermNode::Lit {
            value: Value::Str(i.intern("rested")),
        });
        let k2 = a.add(TermNode::Eq {
            a: n_state,
            b: rested_lit,
        });

        let w = a.add(TermNode::And {
            items: vec![k0, k1, k2],
        });

        let mut rule = RewriteRule {
            name: i.intern("wv_propagate_shape"),
            match_edges: vec![
                MatchEdge {
                    src_var: r_v,
                    edge_type: has_cell,
                    tgt_var: c_v,
                },
                MatchEdge {
                    src_var: c_v,
                    edge_type: neighbour,
                    tgt_var: n_v,
                },
            ],
            where_: Some(w),
            ..Default::default()
        };
        rule.derive_access(a);
        rule
    }

    fn collect_bindings(
        rule: &RewriteRule,
        a: &TermArena,
        g: &TypedGraph,
        i: &Interner,
    ) -> Vec<Vec<(String, u32)>> {
        let mut out = Vec::new();
        match_rule_each(rule, a, g, i, None, None, None, None, |b| {
            let mut row: Vec<(String, u32)> = b
                .iter()
                .map(|(s, n)| (i.resolve(*s).to_string(), n.0))
                .collect();
            row.sort();
            out.push(row);
            true
        });
        out.sort();
        out
    }

    #[test]
    fn pushdown_admits_exactly_the_same_bindings_as_the_whole_where() {
        let mut i = Interner::new();
        let mut a = TermArena::new();
        let mut g = TypedGraph::new();
        let rule = build_propagate_shape(&mut i, &mut a, &mut g, 12, 7);

        // POSITIVE CONTROL on the gate itself: pushdown must actually be
        // armed, or this test proves nothing (§1's 4th clause, applied to a
        // guard: a gate that can only ever pass is not a gate).
        assert_eq!(
            rule.where_conjuncts.len(),
            3,
            "pushdown plan not derived — the comparison below would be vacuous"
        );
        assert!(
            rule.where_conjuncts.iter().any(|(_, v)| v.len() == 1),
            "no single-var conjunct — nothing would ever be pushed down"
        );

        let with_pushdown = collect_bindings(&rule, &a, &g, &i);

        let mut off = rule.clone();
        off.where_conjuncts.clear(); // the PRE-CHANGE path, recomputed live
        let whole_where = collect_bindings(&off, &a, &g, &i);

        // The arms must be ALIVE: an empty binding set is a perfect match
        // between two dead arms (§1.1 — "a dead arm scores a perfect floor").
        assert!(
            !whole_where.is_empty(),
            "no bindings admitted at all — both arms are dead, the equality is vacuous"
        );
        assert_eq!(
            with_pushdown, whole_where,
            "PUSHDOWN CHANGED THE BINDING SET — this is a bug, not an optimisation"
        );
    }

    #[test]
    fn pushdown_gate_bites_when_pushdown_is_wrong() {
        // Proves the gate above can FAIL. We corrupt the plan (drop a
        // conjunct, so pushdown enforces strictly less) and require the
        // binding sets to DIVERGE. A gate never seen red is not a gate.
        let mut i = Interner::new();
        let mut a = TermArena::new();
        let mut g = TypedGraph::new();
        let rule = build_propagate_shape(&mut i, &mut a, &mut g, 12, 7);

        let correct = collect_bindings(&rule, &a, &g, &i);
        assert!(
            !correct.is_empty(),
            "arm is dead — the divergence check below is vacuous"
        );
        let _ = &mut a;

        // EVERY conjunct must be load-bearing: drop each one in turn and the
        // binding set MUST move. If dropping conjunct j changes nothing, the
        // fixture cannot discriminate j and the equality test above is partly
        // vacuous — which is exactly the bug this control caught on its first
        // run (all active cells had activated_at == step, so conjunct 1 was
        // inert and the "gate" could not go red).
        for j in 0..rule.where_conjuncts.len() {
            let mut broken = rule.clone();
            broken.where_conjuncts.remove(j);
            // Rebuild the leaf's where from the REMAINING conjuncts only, so
            // the dropped one is enforced nowhere.
            let items: Vec<TermIdx> = broken.where_conjuncts.iter().map(|(t, _)| *t).collect();
            broken.where_ = Some(a.add(TermNode::And { items }));
            let wrong = collect_bindings(&broken, &a, &g, &i);
            assert_ne!(
                correct, wrong,
                "dropping conjunct {} changed no binding — the fixture cannot \
                        discriminate it, so the equality gate is vacuous for it",
                j
            );
        }
    }

    #[test]
    fn single_edge_rules_get_no_pushdown_plan() {
        // Scope guard: a 1-edge rule has no subtree to prune, so it must be
        // byte-identical (empty plan ⇒ whole-where leaf evaluation).
        let mut i = Interner::new();
        let mut a = TermArena::new();
        let e = i.intern("has_cell");
        let x = i.intern("x");
        let y = i.intern("y");
        let k = i.intern("state");
        let yr = a.add(TermNode::Var { name: y });
        let ys = a.add(TermNode::Attr { node: yr, key: k });
        let lit = a.add(TermNode::Lit {
            value: Value::Str(i.intern("active")),
        });
        let e0 = a.add(TermNode::Eq { a: ys, b: lit });
        let e1 = a.add(TermNode::Eq { a: ys, b: lit });
        let w = a.add(TermNode::And {
            items: vec![e0, e1],
        });
        let mut rule = RewriteRule {
            name: i.intern("one_edge"),
            match_edges: vec![MatchEdge {
                src_var: x,
                edge_type: e,
                tgt_var: y,
            }],
            where_: Some(w),
            ..Default::default()
        };
        rule.derive_access(&a);
        assert!(
            rule.where_conjuncts.is_empty(),
            "a 1-edge rule must get NO pushdown plan (byte-identity scope guard)"
        );
    }
}

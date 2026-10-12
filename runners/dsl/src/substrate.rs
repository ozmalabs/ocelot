//! Π — public mutation surface. The (G, Γ, C) bundle, plus the
//! `Substrate` API and `Transaction`. Edge insertions consult C; node
//! insertions are free (Γ-admissibility is an edge-triple property —
//! the type vocabulary grows via the meta-Γ operations not modelled at
//! this layer).
//!
//! Mirrors `substrate/primitives.py`. Transaction is the closure-based
//! analogue of the Python `with substrate.transform()` context manager:
//! all mutations buffered, rollback on Err, commit on Ok.

use crate::checker::{evaluate_weight, production_admits, CheckOutcome, ConsistencyChecker};
use crate::ext::Counters;
use crate::grammar::ProdIdx;
use crate::graph::{EdgeIdx, EdgeKey, NodeID, TypedGraph};
use crate::sym::{Interner, Sym};
use crate::term::{free_vars, ConceptResolver, TermArena, TermIdx};
use crate::value::Value;
use rustc_hash::{FxHashMap, FxHashSet};
use smallvec::SmallVec;

/// Raised when C rejects a proposed edge. Carries the discriminated
/// Type-1 vs Type-2 information from `CheckOutcome` so callers can
/// surface a precise diagnostic.
#[derive(Debug, Clone)]
pub enum InadmissibleEdge {
    Type1NoProduction {
        src_type: Sym,
        edge_type: Sym,
        tgt_type: Sym,
    },
    Type2VocabAbsent {
        missing: Sym,
    },
}

/// The substrate. Owns G, Γ (in `checker.grammar`), the interner, the
/// Term arena (where production where-clauses and weight expressions
/// live), and the concept resolver (populated by the agent when it
/// uses Holds-shaped recursion).
pub struct Substrate {
    pub graph: TypedGraph,
    pub(crate) interner: Interner,
    pub(crate) checker: ConsistencyChecker,
    pub(crate) terms: TermArena,
    pub(crate) concepts: ConceptResolver,
    /// Phase 7 observability — incremented on every mutation /
    /// admissibility check / eval, queryable via `counters()`.
    pub counters: Counters,
    /// Phase 7c — rewrite rules. Indexed by `RuleIdx`; iterated in
    /// insertion order by `run_rules`. Persistence: rules don't go
    /// through `graph_to_dict` yet — that's an explicit choice, since
    /// rules can reference TermIdx in `self.terms`, and round-tripping
    /// the arena is a Phase-8 concern.
    pub(crate) rules: Vec<crate::rewrite::RewriteRule>,
    /// Monotonic allocator for stable `RuleUid`s. UIDs are checkpointed on
    /// rules; import advances this past the largest restored identity.
    next_rule_uid: u64,
    /// Turn-bounded capture of native rule progress. The adapter opens and
    /// closes this window at conversation boundaries; the committed receipt
    /// itself lives in the graph, not in this transient accumulator.
    rule_firing_capture_active: bool,
    pending_turn_last_progress_rule: Option<Sym>,
    rule_state_trace_config: Option<RuleStateTraceConfig>,
    rule_state_trace_events: Vec<RuleStateTraceEvent>,
    rule_state_trace_dropped: usize,

    /// **Differential rule firing** (Phase: "graph engine acceleration").
    /// Per-rule cached set of edge_types its `match_edges` read. Used to
    /// skip rules whose inputs haven't changed since last attempt.
    rule_edge_type_deps: Vec<rustc_hash::FxHashSet<Sym>>,
    /// Inverse differential index: graph key -> consumers in stable RuleIdx
    /// order. This is the serial, byte-compatible floor for area scheduling.
    rule_readers_by_key: rustc_hash::FxHashMap<crate::rewrite::RuleKey, Vec<usize>>,
    /// Rules whose opaque reads require conservative wake-up.
    rule_reads_any: Vec<usize>,
    /// Per-rule: true iff the rule has a `where_` clause. Conservative
    /// dependence: treat where-clauses as reading every type (any
    /// mutation marks them dirty). A tighter analysis (walking the
    /// Term tree to extract Attr/TypeOf/Neighbours type references)
    /// is a refinement; for now the conservative form is correct.
    rule_has_where: Vec<bool>,
    /// Per-rule dirty bit. True at install. Cleared after run_rules has
    /// given the rule a chance. Set to true by mutation methods when a
    /// rule's read set intersects the mutation's affected types.
    rule_dirty: Vec<bool>,
    /// Per-rule accumulated cost: (micros spent in match+apply, times processed).
    /// The agent's self-instrumentation so it can DIAGNOSE ITSELF — read back which
    /// of its own rules dominates its tick, the observation its surprise/top-cause
    /// faculty needs (prediction_minus_observation). Always-on; per-rule overhead is
    /// one Instant::now() pair (~tens of ns). Reset via `reset_rule_costs`.
    rule_cost_micros: Vec<u64>,
    rule_cost_count: Vec<u64>,
    rule_cost_progress: Vec<u64>,
    /// Set whenever ANY mutation occurs. Conservative rules (those with
    /// where_) become dirty whenever this is set. Cleared at the start
    /// of each `run_rules` outer iteration after fanning out.
    any_mutation: bool,
    /// Tick-level evaluation cache (Filter memoisation, Neighbours
    /// memoisation, Holds memoisation). Persists across rules within a
    /// single `run_rules` call so derivable Term-trees referenced by
    /// multiple rules (e.g. a shared `Holds(is_alive, …)` concept)
    /// pay graph traversal cost once per tick. Cleared whenever the
    /// graph mutates (mutation methods set `any_mutation`; the cache
    /// is wiped at the start of the next outer iteration).
    eval_cache: crate::term::EvalCache,
    /// JIT'd where-clauses, indexed parallel to `rules`. `None` means
    /// the where-clause used a Term variant the JIT doesn't handle yet
    /// — matcher falls back to the interpreter for those rules.
    #[cfg(all(target_arch = "x86_64", target_os = "linux"))]
    rule_where_jit: Vec<Option<crate::jit::CompiledWhere>>,

    /// **Semi-naive matching cursors**. Per-rule, per-edge-type cursor
    /// into the `edges_by_type` Vec — the index past which all edges
    /// are NEW since the last time this rule visited that edge_type.
    /// `(cursor_position, edge_delete_version_at_visit)` — if the
    /// current `edge_delete_version` differs from the stored value,
    /// some intervening delete invalidated the cursor and we full
    /// re-match instead. Only 1-edge rules use this fast path today;
    /// k-edge rules with k≥2 fall through to full re-match.
    rule_cursors: Vec<rustc_hash::FxHashMap<Sym, (usize, u64)>>,
    /// Bumps on every edge deletion (direct or via `delete_node`'s
    /// cascade). Compared against per-rule cursor state to decide
    /// whether the incremental fast path is safe.
    edge_delete_version: u64,

    /// Γ-mutation epoch (Paper 1 Axiom 3). Bumped whenever the
    /// rule store changes (productions added/removed, rewrite rules
    /// added). Realises the `gamma_epoch_counter` component of the
    /// `adaptive_tiered_dispatch` Mt. Sharable via clone with an
    /// L2 `AdaptiveDispatcher` so dispatcher caches invalidate
    /// when the substrate's Γ changes.
    ///
    /// NOTE: G mutations (add_node, add_edge) do NOT bump this.
    /// They mutate data; rule + production additions mutate the
    /// rule store. Only the latter is a Γ change per Paper 1.
    gamma_epoch: crate::l2_adaptive::Epoch,
    /// The `GammaGrammar` root `add_production`'s graph mirror hangs off
    /// (recommendation 2(ii)); lazily created on first mirrored call.
    /// See `grammar_reflect.rs` and `gamma_graph_root()`.
    gamma_graph_root: Option<crate::graph::NodeID>,

    /// `cached_shape` from the function_shape Mt. Per-term Shape
    /// cache — keyed by TermIdx because the arena's indices are
    /// stable per term. Implements
    /// `cached_shape_is_required_by_l6_bounded_coordination_latency`:
    /// shape queries MUST complete within the L6 tick period;
    /// O(1) hash lookup amortises across all uses of the same
    /// Term-tree. Wiped together with eval_cache on any mutation
    /// (a graph mutation can change a Term's evaluated value, but
    /// its STRUCTURAL shape is stable for the term's lifetime in
    /// the arena — so this cache only needs invalidation if the
    /// arena entry is rewritten, which the substrate doesn't do).
    pub shape_cache: crate::shape::ShapeCache,

    /// `active_shape_target` — when Some, rule dispatch prunes rules
    /// whose where-clause Shape is incompatible with this target.
    /// Implements `shape_mismatch_prunes_negative_problem_space`:
    /// rules in the negative problem space (incompatible shape) are
    /// skipped without firing. None = no filter; every rule fires.
    /// Rules without a where-clause always pass the filter (they
    /// have no candidate function to disqualify).
    pub(crate) active_shape_target: Option<crate::shape::Shape>,

    /// Count of rule firings skipped because the active_shape_target
    /// filter pruned them. Resets at the start of run_rules. Reports
    /// the multiplicative savings the pruning earned per tick.
    pub shape_pruned_count: u64,

    /// Attached shared-memory framebuffers (the "live vision on shared
    /// memory" primitive — `framebuffer.rs`), keyed by the `fb_id`
    /// handed back from `fb_attach`. Lives on the core `Substrate`
    /// (not the PyO3 wrapper) so any future graph-resident dispatch
    /// path (Rule effects, `run_rules`) can reach it with the same
    /// `&mut self` it already has, not just direct Python calls.
    pub framebuffers: FxHashMap<u32, crate::framebuffer::FbHandle>,

    // --- DIRTY-PROPAGATION PRECISION (block 187000) ---
    /// **DEFAULT FALSE.** When false the external-mutation dirty path is the
    /// committed BLANKET (`mark_node_mutation`: every where-clause rule, plus a
    /// global `edge_delete_version` bump) and the engine is byte-unchanged.
    ///
    /// When true, `add_node` / `set_attr` / `set_type` / `remove_node` dirty
    /// only the rules whose `read_set` intersects WHAT WAS ACTUALLY WRITTEN,
    /// using EXACTLY the predicate `dirty_by_writeset` already applies to a
    /// rule-effect write (`reads_any ∨ Type-hit ∨ (Attr-hit ∧ has_where)`), and
    /// a `set_attr` whose value EQUALS the stored value is skipped entirely —
    /// it cannot change any binding or any where-clause, so running its
    /// consumers would be a genuine NO-OP. Nothing is frozen and no residual is
    /// deferred (the 185000 lesson): the graph is bit-identical either way.
    pub(crate) precise_dirty: bool,
    /// Telemetry, **default off** (`dirty_telemetry`). Counts dirty-MARKS by the
    /// path that made them. A MARK is one `rule_dirty[j] = true` — counted every
    /// time, because that is the work the path actually does; the `false->true`
    /// TRANSITIONS are counted separately in `[6..9]` so both readings are on
    /// the record (a re-mark of an already-dirty rule is real cost but not new
    /// information).
    /// `[0]` = `dirty_by_writeset` (rule-effect), `[1]` = `mark_edge_type_dirty`,
    /// `[2]` = the external-write path (blanket or precise), `[3]` = attr writes
    /// seen, `[4]` = attr writes whose value was UNCHANGED (no-op writes),
    /// `[5]` = external-write events, `[6..9]` = the transitions for `[0..3]`.
    pub(crate) dirty_marks: [u64; 9],
    /// When true, `dirty_marks` is maintained. Default false so the committed
    /// path pays nothing (the no-op-write comparison in particular).
    pub(crate) dirty_telemetry: bool,
    /// **THE WRONG-PRECISION FALSIFIER, and nothing else.** Only meaningful with
    /// `precise_dirty` on. Two over-aggressions at once, both of them tempting
    /// and both of them WRONG:
    ///   1. the external-write path wakes NOBODY (the maximal skip);
    ///   2. a float write "within 1e-9" is treated as a no-op — precisely
    ///      185000's Branch-B shape, a skip of something not genuinely settled.
    /// It MUST break byte-identity; it exists so the gate is demonstrably
    /// non-vacuous. Never enable it for anything else.
    pub(crate) dirty_overaggressive: bool,
    /// BINDING PROJECTION (block 188000), **DEFAULT FALSE**. When on, a rule
    /// carrying `RewriteRule::project_vars` has its binding set deduplicated on
    /// the projection to the variables its where-clause and effects actually
    /// reference. See that field's doc for the soundness argument. Off ⇒ the
    /// committed code path, byte-unchanged.
    pub(crate) binding_projection: bool,
    /// FALSIFIER for `binding_projection`, **DEFAULT FALSE**. Projects on the
    /// EMPTY variable set — i.e. fires a rule at most ONCE per visit no matter
    /// how many distinct areas/nodes match. That is the tempting-but-wrong
    /// generalisation ("it re-derives the same thing, just do it once"), and it
    /// MUST break byte-identity on a workload with more than one matching hub.
    pub(crate) projection_overaggressive: bool,
    /// EMPTY-MATCH-SET PROOF (block 189000), **DEFAULT FALSE**. When on, a rule
    /// whose match set is PROVABLY empty under the current graph is not
    /// enumerated at all. See `match_set_provably_empty` for the predicate and
    /// its soundness argument. Off ⇒ the committed code path, byte-unchanged.
    ///
    /// ⚠️ THE SOUNDNESS DIRECTION IS THE DANGER. Unlike dirty-marking (where
    /// OVER-approximating is safe), claiming "empty" when a rule COULD match
    /// SILENTLY LOSES WORK. The predicate is therefore the NARROWEST one that
    /// reaches the measured cost, and it reads the very index the matcher
    /// enumerates, so it introduces no new bookkeeping that could go stale.
    pub(crate) empty_match_proof: bool,
    /// FALSIFIER for `empty_match_proof`, **DEFAULT FALSE**. Claims "empty"
    /// when a match edge type has **≤ 1** live edge — i.e. it treats a
    /// SINGLETON edge type as absent. That is unsound: a rule can perfectly
    /// well match through a one-of-a-kind edge (e.g. `retinal_mint_onset_2d`
    /// binds the retina's single `has_onset_params_2d` edge). It MUST break
    /// byte-identity AND the onset stream; it exists so the identity gate is
    /// demonstrably non-vacuous. Never enable it for anything else.
    pub(crate) empty_match_proof_unsound: bool,
    /// Count of enumerations skipped by `empty_match_proof`, per rule index.
    /// Read-only telemetry (`empty_match_skips`); never read by any decision.
    pub(crate) empty_match_skips: Vec<u64>,

    /// INCREMENTAL MATCH (block 192000 — ladder rung A), **DEFAULT FALSE**.
    /// OFF ⇒ the committed engine, byte-unchanged: a semi-naive cursor is valid
    /// only while the single GLOBAL `edge_delete_version` is unchanged, so ANY
    /// delete/external-write anywhere invalidates every cursor and every dirty
    /// rule full-rescans. ON ⇒ a cursor is validated against its edge type's OWN
    /// `graph.edge_delete_version_by_type`, so a delete of a DIFFERENT edge type
    /// no longer forces a full rescan — the append-only rule keeps its O(Δ)
    /// incremental path across the unrelated delete. Retraction stays correct
    /// (a delete of type X still invalidates X-reading cursors → they rescan).
    /// The where-flip-on-stable-edge invalidation `mark_node_mutation` performs
    /// on external attr writes is PRESERVED under ON (it clears the cursors of
    /// the where-rules it dirties), so a rule whose where reads an
    /// externally-mutated attr (the eye's mint rules) still full-rescans —
    /// byte-identical, and the honest coverage boundary. That shape is ladder
    /// rung B's target (per-binding predicate retraction), not this rung.
    pub(crate) incremental_match: bool,
    /// ISOLATED-NODE WRITE EXEMPTION (equilibrium scaling), **DEFAULT FALSE**;
    /// takes effect together with `precise_dirty`. An EXTERNAL `add_node` (and
    /// an external `set_attr` on a node with NO edges) normally dirties and
    /// cursor-clears every where-rule reading one of the written attr keys, and
    /// every `reads_any` rule. A node with no edges is in no existing binding and
    /// no term path reaches it, so with this flag such a write dirties only the
    /// rules that can see it: a `Type` read of its type (`NodesOfType`,
    /// `NodesWhere`, `AddNodeIfAbsent`) or a NON-LOCAL opaque read
    /// (`reads_any_nonlocal`; `TypeOf`/`AttrByName` read nodes already bound).
    /// Its attrs become observable only through an edge added later, so an
    /// external `add_edge` additionally clears the cursor of every rule whose
    /// where/effect terms read that edge type (`term_edge_reads`, the same
    /// invalidation the rule-effect path applies) or that reads non-locally; a
    /// pure match-edge driver keeps its cursor and is handled semi-naively.
    /// Net: an append-only ingest of fresh subgraphs keeps rules on the
    /// incremental path. OFF ⇒ the committed engine, byte-identical.
    pub(crate) fresh_node_exempt: bool,
    /// SEMI-NAIVE FOR BATCH RULES (equilibrium scaling), **DEFAULT FALSE**.
    /// A `batch` rule normally re-enumerates its WHOLE binding set on every
    /// visit (`batch_apply_rule`). With this on, a batch rule first tries the
    /// semi-naive cursor path (`try_incremental_match`: delta-driven, every
    /// distinct new binding evaluated against the pre-apply graph and applied
    /// once — the same snapshot semantics), and only when that bails (cold or
    /// invalidated cursor, repeated match edge type, k==0, reads_external) runs
    /// the committed full batch pass and then installs its cursors at the
    /// pre-apply frontier, exactly as the cold path does for non-batch rules.
    /// Re-firing an old binding is a no-op for idempotent effects, which is
    /// the only case where the two paths can differ; where-flips on stable
    /// bindings are covered by the same cursor invalidation every non-batch
    /// rule relies on. Under this flag the semi-naive path also admits rules
    /// whose match repeats an edge type (dedup by canonical binding key).
    /// OFF ⇒ the committed engine, byte-identical.
    pub(crate) batch_incremental: bool,
    /// OWN-WRITE EXEMPTION (equilibrium scaling), **DEFAULT FALSE**. Deciding
    /// whether a rule-effect write must CLEAR a consumer's semi-naive cursor
    /// (not whether it dirties it) uses the consumer's `read_set_strict` /
    /// `term_edge_reads_strict` -- the keys its where-clause and computed effect
    /// args read -- instead of `read_set` / `term_edge_reads`, which also hold
    /// its effects' own write-target look-ups (`AddEdge`'s edge type,
    /// `AddNodeIfAbsent`'s type + key attrs, `SetAttr`'s key). Those look-ups
    /// only make re-firing an already-fired binding a no-op, so a write to them
    /// cannot flip which bindings match; the committed engine already treats an
    /// effect-only attr read this way for where-LESS rules. Without it every
    /// such rule clears its OWN cursor whenever it fires (e.g. a rule adding an
    /// `eq_neg_next` edge), so its next visit is a full re-match.
    /// OFF ⇒ the committed engine, byte-identical.
    pub(crate) own_write_exempt: bool,
    /// PRECISE RULE-EFFECT EDGE DELETES (equilibrium scaling), **DEFAULT
    /// FALSE**. Under `incremental_match`, a progressing rule with ANY delete
    /// effect clears EVERY rule's cursor (the global-bump equivalent, needed
    /// because a `DelNode` cascade deletes edges of types the effect list does
    /// not name). With this on, a rule whose only delete effects are `DelEdge`
    /// (no `DelNode` / `ReplaceValue`: the deleted types are exactly the named
    /// ones) instead invalidates exactly as an external `remove_edge` does:
    /// the per-type delete version (bumped by the graph) stales every cursor
    /// MATCHING a deleted type, `invalidate_readers_of_deleted_edge_type`
    /// clears every where/term reader of it, and `reads_any_nonlocal` rules are
    /// cleared conservatively. OFF ⇒ the committed engine, byte-identical.
    pub(crate) precise_rule_deletes: bool,
    /// SEEDED JOIN ORDER (equilibrium scaling), **DEFAULT FALSE**. The
    /// semi-naive and node-seeded paths solve the rest of a pattern from a
    /// seed edge with the remaining match edges in their DECLARED order, and
    /// without the rule's index hints; an edge whose endpoints are both still
    /// unbound is then a scan of its whole edge type, once per seed (e.g. a
    /// cue rule driven by a new `eq_next` edge re-scans every `received` edge).
    /// With this on, the remaining edges are ordered greedily by connectivity
    /// to the bound variables (both endpoints bound first, then one, ties in
    /// declared order), the rule's index hints and where-conjunct pushdown are
    /// kept, and a both-bound edge is probed from its smaller side
    /// (`RewriteRule::both_bound_probe`). Matcher traversal only: the binding
    /// SET is unchanged.
    /// OFF ⇒ the committed engine.
    pub(crate) seeded_join_order: bool,
    /// WRITE FRONTIER (equilibrium scaling), **DEFAULT FALSE**. A rule-effect
    /// attr write that would clear a consumer's cursor only because the
    /// consumer's where / computed args read that attr (incl. a dynamically
    /// named attr of a match variable, `AttrByName`) instead SEEDS the written
    /// nodes, when the consumer is `wf_ok` and the key is not one it reads off
    /// its match frontier (`wf_nonlocal_keys`): such a write can flip only
    /// bindings that bind the written node. The consumer's next visit first
    /// re-evaluates the bindings incident to those nodes (the node-seeded pass
    /// of `try_predicate_retraction`, without its unchanged-edges precondition
    /// and leaving the cursor to the semi-naive pass), then takes its usual
    /// semi-naive / full path for new edges. Without it, a mint-once guard
    /// (`eqfire:<rule>` unset) makes every firing rule full-rematch the whole
    /// conversation on its next visit. Arms the graph's attr-write log.
    /// OFF ⇒ the committed engine, byte-identical.
    pub(crate) write_frontier: bool,
    /// HOP FRONTIER (equilibrium scaling stage B), **DEFAULT FALSE**. Refines
    /// `write_frontier`'s locality (`RewriteRule::wf_hop_alt`): pure set /
    /// arithmetic operators are transparent, and an attr read of an `Exists`
    /// variable ranging over `Neighbours(v, E)` / `InNeighbours(v, E)` of a match
    /// variable is one-hop local -- a rule-effect write of that key on node `x`
    /// seeds the `E`-neighbours of `x` (the only `v` it can flip) instead of
    /// clearing the reader's cursor. Without it e.g. "no facet of episode e holds
    /// shape s" full-rematches every episode whenever any facet's shape is
    /// written. OFF ⇒ the committed engine, byte-identical.
    pub(crate) hop_frontier: bool,
    /// DELETE FRONTIER (equilibrium scaling stage B), **DEFAULT FALSE**; needs
    /// `write_frontier` + `precise_rule_deletes`. A rule-effect `DelEdge` of
    /// `(s, E, t)` makes a NON-matching reader of `E` re-check only the bindings
    /// of `s` and `t` (node-seeded, cursor kept) when every read it makes of `E`
    /// is local (`wf_local_out` / `wf_local_in`) or is its own `AddEdge` target
    /// with a match-bound endpoint (`own_edge_seedable`): a delete can re-enable
    /// only a binding whose where reads `E` at `s` / `t`, or one that re-adds the
    /// deleted edge (and so binds `s` or `t`). Readers MATCHING `E` still go stale
    /// through the per-type delete version (full re-match), and every other
    /// reader is cleared as before. Without it a retraction edge (e.g. an open
    /// question's evidence edge, deleted once answered) full-rematches the rule
    /// that adds it. OFF ⇒ the committed engine, byte-identical.
    pub(crate) delete_frontier: bool,
    /// FALSIFIER for `incremental_match`, **DEFAULT FALSE**. Makes cursor
    /// validation MISS a retraction: a cursor is treated as valid w.r.t. deletes
    /// regardless of its edge type's delete version, so a delete of a rule's OWN
    /// edge type no longer invalidates it. The stale (now unsupported) match is
    /// never re-derived, so the graph diverges from the full rescan on any
    /// deleting workload. It exists so the reduction gate is demonstrably
    /// non-vacuous. Never enable it for anything but the falsifier test.
    pub(crate) incremental_match_unsound: bool,
    /// PREDICATE RETRACTION (block 194000, ladder rung B), **DEFAULT FALSE**.
    /// When on, an EXTERNAL attr write to a node does NOT clear a covered
    /// where-rule's whole cursor (forcing an O(cells) full rescan of every
    /// binding); instead the written node is recorded per-rule and, on the
    /// rule's next attempt, ONLY the bindings that TOUCH the written node(s)
    /// are re-evaluated (node-seeded, lean-TREAT). A binding whose predicate
    /// node changed is a partial match that must re-settle; one whose nodes
    /// were untouched keeps its assertion. Covers the stable-edge attr-flip
    /// shape rung A named and fell back on: reduces a K-node attr flip from
    /// O(N) to O(K), byte-identical to the full rescan. OFF ⇒ the committed
    /// path, byte-unchanged (this whole path is unreachable with the flag off).
    pub(crate) predicate_retraction: bool,
    /// FALSIFIER for `predicate_retraction`, **DEFAULT FALSE**. Drops one
    /// dirty node from the node-seeded re-evaluation set, so a binding whose
    /// predicate flipped to TRUE on that node is never re-fired — the graph
    /// diverges from the full rescan (a fired-binding / minted observable
    /// moves). It exists so the reduction gate is demonstrably non-vacuous.
    /// Never enable it for anything but the falsifier test.
    pub(crate) predicate_retraction_unsound: bool,
    /// Per-rule set of EXTERNALLY-written nodes since the rule's last visit,
    /// maintained ONLY when `predicate_retraction` is on. Parallel to
    /// `rule_cursors`. Node ids are unbounded integers (no float bookkeeping).
    pub(crate) rule_dirty_nodes: Vec<rustc_hash::FxHashSet<NodeID>>,
    /// Write frontier: nodes dirtied ONLY by a dynamically-named attr write (see
    /// `write_frontier`); re-checked only at the rule's `AttrByName` variables.
    pub(crate) rule_dirty_dyn_nodes: Vec<rustc_hash::FxHashSet<NodeID>>,
    /// Per-rule static eligibility for the node-seeded path: has a where,
    /// add-only effects, non-repeated edge types, not `reads_external`, k≥1.
    /// Computed once in `add_rule`. Parallel to `rule_cursors`.
    pub(crate) rule_pred_retract_ok: Vec<bool>,

    /// GAMMA RESIDUAL CAPTURE (GAMMA_COLLAPSE_ALGORITHM spike), **DEFAULT
    /// FALSE**. Mirrors the `precise_dirty` / `dirty_telemetry` opt-in
    /// pattern above exactly: OFF ⇒ `add_edge`'s `Type1NoProduction` arm is
    /// byte-unchanged (nothing new executes, nothing new is written). ON ⇒
    /// every Type-1 rejection additionally mints ONE `GammaResidual` node
    /// (mechanical event logging — Rust decides nothing about whether the
    /// triple "recurs"; that decision is left entirely to the seed rule
    /// `note_gamma_production_gap` in `seeds/gamma_residual.json`, which
    /// groups by the triple and applies the `shape_decode.rs` support
    /// discipline: support >= 2 mints, support 1 does not — TWO is not a
    /// swept knob, it is the smallest cardinality at which "recurs" is
    /// defined). This is the collapse-without-residual-capture gap named in
    /// `GAMMA_COLLAPSE_ALGORITHM_PREREG.md` §1: the triple was already a
    /// real, fully-computed Rust value at this point in `add_edge` and was
    /// previously thrown away the instant the `Err` was constructed.
    pub(crate) gamma_residual_capture: bool,
    /// Lazily created once, on first Type-1 rejection with capture on.
    /// Deliberately SEPARATE from `gamma_graph_root` (which anchors live,
    /// admitted `GammaProduction` mirrors written by `add_production`) even
    /// though both live under the same `GammaGrammar`-family vocabulary —
    /// a residual is explicitly NOT a production and must never be
    /// confusable with one by graph shape alone.
    pub(crate) gamma_residual_root: Option<NodeID>,
    /// Next id `fb_attach` will hand out. Monotonic — ids are not
    /// reused after `fb_detach`, so a stale Python-side `fb_id` fails
    /// loudly (KeyError-shaped) instead of silently reattaching to an
    /// unrelated later framebuffer.
    pub next_fb_id: u32,
}

/// Storage strategy selected when an immutable experiment snapshot is captured.
/// Consumers depend on `ExperimentSnapshot::fork`, not on the backing layout.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum ExperimentSnapshotBackend {
    FullCopy,
    SharedSlabs,
    SharedGraphPages,
}

/// O(1) optimistic concurrency token. Semantic stores are exposed read-only;
/// mutations go through APIs that advance the graph revision or Γ epoch.
pub type ExperimentRevision = (u64, u64, usize);

impl ExperimentSnapshotBackend {
    pub fn as_str(self) -> &'static str {
        match self {
            Self::FullCopy => "full_copy",
            Self::SharedSlabs => "shared_slabs",
            Self::SharedGraphPages => "shared_graph_pages",
        }
    }

    fn fork(self, base: &Substrate) -> Result<Substrate, &'static str> {
        match self {
            Self::FullCopy => base.fork_full_copy_experiment(),
            Self::SharedSlabs => base.fork_shared_slab_experiment(),
            Self::SharedGraphPages => base.fork_shared_graph_pages_experiment(),
        }
    }
}

/// Immutable reusable base for isolated substrate branches.
///
/// The snapshot owns a detached semantic base and exposes no mutation API.
/// Forked branches retain their own mutable execution state; dropping a branch
/// or the snapshot releases its storage through ordinary Rust ownership.
pub struct ExperimentSnapshot {
    id: u64,
    source_revision: ExperimentRevision,
    backend: ExperimentSnapshotBackend,
    base: Substrate,
}

impl ExperimentSnapshot {
    pub fn id(&self) -> u64 {
        self.id
    }

    /// Semantic graph/rule revision observed at capture time.
    pub fn source_revision(&self) -> ExperimentRevision {
        self.source_revision.clone()
    }

    pub(crate) fn backend(&self) -> ExperimentSnapshotBackend {
        self.backend
    }

    /// Create an isolated mutable branch from this immutable base.
    pub fn fork(&self) -> Result<Substrate, &'static str> {
        self.backend.fork(&self.base)
    }
}

/// A carved connected-component of grid cells — the unit the eye's
/// cross-frame tracker (`track_comps`) turns into / matches to a `Region`.
/// Hoisted to module scope (it was a local struct in `segment_and_track`)
/// so the value-carve (`segment_and_track`) and the motion-common-fate
/// carve (`segment_motion_and_track`) share ONE `Comp` type and ONE tracker.
/// `value` is the cross-frame identity key the matcher gates on: the grey
/// level for the value carve; {0 = ground/dominant, 1 = figure} for motion.
struct Comp {
    value: i32,
    cells: std::collections::HashSet<usize>,
    count: f64,
    cy: f64,
    cx: f64,
    minr: usize,
    minc: usize,
    maxr: usize,
    maxc: usize,
}

/// Euclidean distance between the motion vectors at grid cells `i` and `j`
/// (`(vy,vx)` per cell) — the common-fate agreement metric the motion carve
/// floods within, the exact `Magnitude(VecSub(..))` the motion-group seed uses.
fn vdist(vy: &[f64], vx: &[f64], i: usize, j: usize) -> f64 {
    let dy = vy[i] - vy[j];
    let dx = vx[i] - vx[j];
    (dy * dy + dx * dx).sqrt()
}

/// Otsu between-class threshold over a dispersion distribution — the tolerance
/// the motion carve floods within, so the threshold FALLS OUT of the field's own
/// structure rather than being picked (§13). FAITHFUL to the graph rule
/// `mo_tol_otsu` in `seeds/vision_motion_group.json`: for each observed value
/// `t`, score = (S_le·N_gt − S_gt·N_le)² / max(N_le·N_gt, 1) where the split is
/// `pd ≤ t` vs `pd > t`; τ is the observed value maximizing it (first-max wins,
/// scanned in cell order — deterministic). On a field with no motion structure
/// (all pd equal) every split scores 0 and τ collapses to that value (0 for a
/// still field ⇒ exact-equality flood ⇒ one region). The inherited honest limit
/// (pre-registered): Otsu has NO null hypothesis — it returns a split on any
/// distribution, so a structured-but-objectless field can still be split.
fn otsu_threshold(pd: &[f64]) -> f64 {
    if pd.is_empty() {
        return 0.0;
    }
    let mut best_t = pd[0];
    let mut best_score = -1.0f64;
    for &t in pd.iter() {
        let mut s_le = 0.0f64;
        let mut n_le = 0.0f64;
        let mut s_gt = 0.0f64;
        let mut n_gt = 0.0f64;
        for &v in pd.iter() {
            if v <= t {
                s_le += v;
                n_le += 1.0;
            } else {
                s_gt += v;
                n_gt += 1.0;
            }
        }
        let num = s_le * n_gt - s_gt * n_le;
        let score = (num * num) / (n_le * n_gt).max(1.0);
        if score > best_score {
            best_score = score;
            best_t = t;
        }
    }
    best_t
}

// --- PER-AREA ASYNC SETTLEMENT accounting (block 186000) -----------------
//
// "You settle for this time, but there is always a residual; you never get to
// 0 unless you stop operating." The committed global fixpoint is CLOSED-ACCOUNT
// settlement: `residual == 0` IS its termination condition. These structures
// carry the OPEN-ACCOUNT reading — what each area settled this round, and what
// it CARRIED forward.

/// One area's ledger for one settlement round.
#[derive(Clone, Debug, Default)]
pub struct AreaSettleRow {
    pub area: Sym,
    /// Dirty active rules this area held when its turn came.
    pub dirty: usize,
    /// How many of them the budget actually reached.
    pub attempted: usize,
    /// How many of the attempts PROGRESSED (settlement work done).
    pub steps: usize,
    /// Dirty rules the budget did NOT reach — CARRIED (bits left set), or
    /// DISCARDED when running the drop-the-residual falsifier arm.
    pub carried: usize,
}

/// One settlement round: one pass over the areas, each spending its budget.
#[derive(Clone, Debug, Default)]
pub struct SettleRound {
    pub rows: Vec<AreaSettleRow>,
    pub steps: usize,
    /// Areas that held ANY dirty rule this round. An area not counted here
    /// did NO work — that is the area-grain "compute ∝ surprise" property.
    pub dirty_areas: usize,
    /// Total dirty active rules still standing at the END of the round: the
    /// account's residual after this settlement event.
    pub residual: usize,
}

#[derive(Clone, Debug, Default)]
pub struct SettleReport {
    pub rounds: Vec<SettleRound>,
    pub steps: usize,
    pub areas: Vec<Sym>,
    pub hit_max_rounds: bool,
}

/// Result of ownership-aware cleanup for a reflected Term child-edge tree.
/// `removed` includes each deleted node and its former type for adapter hooks;
/// `protected` contains owned nodes preserved because they are externally
/// referenced, including their Term descendants.
#[derive(Clone, Debug, Default)]
pub struct TermSubgraphRemoval {
    pub removed: Vec<(NodeID, Sym)>,
    pub protected: Vec<NodeID>,
}

/// Why a global rule-run call returned. This describes the existing
/// pass-boundary progress budget; it is not a wall-time or hard work cap.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum RuleRunStatus {
    /// The runner observed a pass with no progress or no eligible dirty rules.
    FixedPoint,
    /// Opt-in graph-state fingerprinting found a previously visited state.
    /// This is not the same as a fixed point.
    RepeatedGraphState,
    /// The progress budget prevented another outer pass from starting.
    ProgressBudgetReached,
}

/// Structured result for callers that must distinguish settlement from an
/// early return. Legacy runner methods continue returning `progress_steps`.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct RuleRunReport {
    pub status: RuleRunStatus,
    /// Number of progress-producing rule applications; can exceed the
    /// requested budget when several rules progress in the final pass.
    pub progress_steps: usize,
    pub requested_progress_budget: usize,
    pub budget_overshoot: usize,
    /// Number of complete outer passes entered, including a final no-progress
    /// pass when one was needed to establish a fixed point.
    pub passes_completed: usize,
    pub cycle_detection_enabled: bool,
    /// Name of the last rule that produced progress during this settlement
    /// call. This is call-local evidence, not a durable history record.
    pub last_progress_rule: Option<Sym>,
}

/// Snapshot recorded after one successful invocation of a watched rule.
/// This is an opt-in diagnostic trace and is never serialized into graph state.
#[derive(Clone, Debug)]
pub struct RuleStateTraceEvent {
    pub pass_index: usize,
    pub progress_step: usize,
    pub rule_name: String,
    pub node_ids: Vec<u32>,
    pub attr_names: Vec<String>,
    pub values: Vec<Vec<Option<f64>>>,
}

#[derive(Clone, Debug)]
struct RuleStateTraceConfig {
    rule_names: FxHashSet<Sym>,
    node_ids: Vec<NodeID>,
    attr_keys: Vec<Sym>,
    attr_names: Vec<String>,
    max_events: usize,
}

/// Opt-in graph-state delta around a rule settlement call. This is an audit
/// surface: it compares live graph contents before and after settlement, so
/// it includes writes performed by deferred effects that drain during the
/// call. It reports changed node IDs and changed edge keys (including their
/// endpoints); it does not infer frame ownership or cover non-graph state
/// such as rule clauses and concept definitions.
#[derive(Clone, Debug)]
pub struct RuleGraphDeltaReport {
    pub run: RuleRunReport,
    /// Conservative set of node targets that may require dependent-frame
    /// reconsideration. Mutation logging may include no-op mutable accesses.
    pub affected_nodes: Vec<NodeID>,
    /// Conservative set of edge keys touched by graph mutation methods.
    pub affected_edges: Vec<EdgeKey>,
    /// Runtime Microtheories whose currently owned nodes, ownership links,
    /// or roots were touched. These are stable seed IDs, not dependency
    /// connected components; callers may group them into larger frames.
    pub affected_microtheories: Vec<NodeID>,
    /// True only for the full before/after graph-content oracle.
    pub exact_graph_state_diff: bool,
}

/// Write-target report for one Microtheory-scoped settlement. Scoped closure
/// currently shares the existing runner's limitation around deferred effect
/// queues, so callers must inspect `deferred_effects_pending` before treating
/// the scope as fully settled.
#[derive(Clone, Debug)]
pub struct ScopedRuleGraphDeltaReport {
    pub progress_steps: usize,
    pub requested_progress_budget: usize,
    pub hit_progress_budget: bool,
    pub affected_nodes: Vec<NodeID>,
    pub affected_edges: Vec<EdgeKey>,
    pub affected_microtheories: Vec<NodeID>,
    pub deferred_effects_pending: bool,
}

type GraphNodeSnapshot = FxHashMap<NodeID, (Sym, Vec<(Sym, Value)>)>;
type GraphEdgeSnapshot = FxHashMap<EdgeKey, Vec<(Sym, Value)>>;

fn snapshot_graph_content(graph: &TypedGraph) -> (GraphNodeSnapshot, GraphEdgeSnapshot) {
    let mut nodes = FxHashMap::default();
    for (nid, data) in graph.iter_nodes() {
        let mut attrs = data.attrs.0.clone();
        attrs.sort_by_key(|(key, _)| *key);
        nodes.insert(nid, (data.type_, attrs));
    }
    let mut edges = FxHashMap::default();
    for (idx, data) in graph.iter_edges() {
        let mut attrs = graph.edge_attrs(idx).0.clone();
        attrs.sort_by_key(|(key, _)| *key);
        edges.insert(data.key(), attrs);
    }
    (nodes, edges)
}

fn map_affected_microtheories(
    graph: &TypedGraph,
    mt_type: Sym,
    has_concept: Sym,
    nodes: &[NodeID],
    edges: &[EdgeKey],
    prior_types: &FxHashMap<NodeID, Sym>,
) -> Vec<NodeID> {
    let mut affected = rustc_hash::FxHashSet::default();
    for &nid in nodes {
        let prior_is_mt = prior_types.get(&nid) == Some(&mt_type);
        let live_is_mt = graph.has_node(nid) && graph.node(nid).type_ == mt_type;
        if prior_is_mt || live_is_mt {
            affected.insert(nid);
        }
        if graph.has_node(nid) {
            affected.extend(graph.in_neighbours(nid, Some(has_concept)));
        }
    }
    // The source of a has_concept edge is the owner. Keeping this path covers
    // ownership insertion/retraction and deleted owned nodes after their live
    // membership edge has disappeared.
    for key in edges {
        if key.edge_type == has_concept {
            affected.insert(key.src);
        }
    }
    let mut out: Vec<NodeID> = affected.into_iter().collect();
    out.sort_unstable();
    out
}

/// Clause selected by a transactional rule patch.
#[derive(Copy, Clone, Debug, PartialEq, Eq)]
pub enum RulePatchField {
    Where,
    Effects,
}

impl RulePatchField {
    fn parse(field: &str) -> Result<Self, RulePatchError> {
        match field {
            "where" => Ok(Self::Where),
            "effect" | "effects" => Ok(Self::Effects),
            _ => Err(RulePatchError::UnknownField),
        }
    }
}

/// Stable refusal classes written back to graph-native `RulePatch` nodes.
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum RulePatchError {
    TargetNotFound,
    TargetInactive,
    ProtectedTarget,
    StaleRevision { actual: u64 },
    StaleContentHash { actual: u64 },
    UnknownField,
    MalformedClause,
    MalformedPatchNode,
}

impl RulePatchError {
    pub fn code(&self) -> &'static str {
        match self {
            Self::TargetNotFound => "target_not_found",
            Self::TargetInactive => "target_inactive",
            Self::ProtectedTarget => "protected_target",
            Self::StaleRevision { .. } => "stale_revision",
            Self::StaleContentHash { .. } => "stale_content_hash",
            Self::UnknownField => "unknown_field",
            Self::MalformedClause => "malformed_clause",
            Self::MalformedPatchNode => "malformed_patch_node",
        }
    }
}

/// Successful CAS commit receipt. The previous metadata plus inverse clause
/// are sufficient to author a second CAS patch which exactly reverts it.
#[derive(Clone, Debug)]
pub struct RulePatchReceipt {
    pub uid: crate::rewrite::RuleUid,
    pub previous_revision: u64,
    pub previous_content_hash: u64,
    pub revision: u64,
    pub content_hash: u64,
    pub inverse_clause: Value,
}

/// Fully parsed but not yet visible replacement. Staging may append decoded
/// Terms to the arena, but cannot affect any live rule, index, cursor, dirty
/// bit, JIT entry or Γ epoch. Commit rechecks the CAS before one swap.
pub struct StagedRulePatch {
    rule_index: usize,
    uid: crate::rewrite::RuleUid,
    expected_revision: u64,
    expected_content_hash: u64,
    replacement: crate::rewrite::RewriteRule,
    inverse_clause: Value,
}

impl Substrate {
    pub fn new(checker: ConsistencyChecker) -> Self {
        Self {
            graph: TypedGraph::new(),
            interner: Interner::new(),
            checker,
            terms: TermArena::new(),
            concepts: ConceptResolver::default(),
            counters: Counters::new(),
            rules: Vec::new(),
            next_rule_uid: 1,
            rule_firing_capture_active: false,
            pending_turn_last_progress_rule: None,
            rule_state_trace_config: None,
            rule_state_trace_events: Vec::new(),
            rule_state_trace_dropped: 0,
            rule_edge_type_deps: Vec::new(),
            rule_readers_by_key: rustc_hash::FxHashMap::default(),
            rule_reads_any: Vec::new(),
            rule_has_where: Vec::new(),
            rule_dirty: Vec::new(),
            rule_cost_micros: Vec::new(),
            rule_cost_count: Vec::new(),
            rule_cost_progress: Vec::new(),
            any_mutation: false,
            eval_cache: crate::term::EvalCache::default(),
            #[cfg(all(target_arch = "x86_64", target_os = "linux"))]
            rule_where_jit: Vec::new(),
            rule_cursors: Vec::new(),
            edge_delete_version: 0,
            gamma_epoch: crate::l2_adaptive::Epoch::new(),
            gamma_graph_root: None,
            shape_cache: crate::shape::ShapeCache::new(),
            active_shape_target: None,
            shape_pruned_count: 0,
            framebuffers: FxHashMap::default(),
            next_fb_id: 1,
            precise_dirty: false,
            dirty_marks: [0; 9],
            dirty_telemetry: false,
            dirty_overaggressive: false,
            binding_projection: false,
            projection_overaggressive: false,
            empty_match_proof: false,
            empty_match_proof_unsound: false,
            empty_match_skips: Vec::new(),
            incremental_match: false,
            fresh_node_exempt: false,
            batch_incremental: false,
            own_write_exempt: false,
            precise_rule_deletes: false,
            seeded_join_order: false,
            write_frontier: false,
            hop_frontier: false,
            delete_frontier: false,
            incremental_match_unsound: false,
            predicate_retraction: false,
            predicate_retraction_unsound: false,
            rule_dirty_nodes: Vec::new(),
            rule_dirty_dyn_nodes: Vec::new(),
            rule_pred_retract_ok: Vec::new(),
            gamma_residual_capture: false,
            gamma_residual_root: None,
        }
    }

    /// Capture an immutable, reusable base. The backend is selected at capture
    /// time; branch consumers use the same backend-independent `fork` method.
    pub fn snapshot(&self) -> Result<ExperimentSnapshot, &'static str> {
        self.experiment_snapshot_with_backend(ExperimentSnapshotBackend::SharedGraphPages)
    }

    /// Backend-selecting hook for controlled engine measurements. Application
    /// consumers should use `snapshot()` and depend only on `fork()`.
    pub(crate) fn experiment_snapshot_with_backend(
        &self,
        backend: ExperimentSnapshotBackend,
    ) -> Result<ExperimentSnapshot, &'static str> {
        use std::sync::atomic::{AtomicU64, Ordering};
        static NEXT_SNAPSHOT_ID: AtomicU64 = AtomicU64::new(1);

        let source_revision = self.experiment_graph_rule_revision();
        let base = backend.fork(self)?;
        let id = NEXT_SNAPSHOT_ID.fetch_add(1, Ordering::Relaxed);
        Ok(ExperimentSnapshot { id, source_revision, backend, base })
    }

    /// Build a deep-copy experiment control with isolated mutable execution
    /// state. This is intentionally not CoW: it is the semantic control arm
    /// for later fork implementations. External framebuffer handles and
    /// pending graph effects make the source state ineligible for this API.
    pub fn fork_full_copy_experiment(&self) -> Result<Self, &'static str> {
        self.fork_experiment_with_graph_storage(false, false)
    }

    /// Build a branch that shares node/edge slab pages but eagerly clones all
    /// query indexes and the rest of Substrate state. This deliberately partial
    /// CoW route isolates the slab contribution; it is not the final graph COW.
    pub fn fork_shared_slab_experiment(&self) -> Result<Self, &'static str> {
        self.fork_experiment_with_graph_storage(true, false)
    }

    /// Branch with shared record slabs and top-level adjacency pages. Hash
    /// query indexes and other Substrate state are still copied eagerly.
    pub fn fork_shared_graph_pages_experiment(&self) -> Result<Self, &'static str> {
        self.fork_experiment_with_graph_storage(true, true)
    }

    fn fork_experiment_with_graph_storage(
        &self,
        share_slabs: bool,
        share_adjacency: bool,
    ) -> Result<Self, &'static str> {
        self.validate_experiment_fork()?;
        let graph_has_pending_effects = !self.graph.pending_rule_edits.is_empty()
            || !self.graph.pending_rule_patches.is_empty()
            || !self.graph.pending_fb_samples.is_empty()
            || !self.graph.pending_track_identity.is_empty()
            || !self.graph.pending_net_collapses.is_empty();
        if graph_has_pending_effects {
            return Err("cannot fork experiment with pending graph effects");
        }
        if !self.graph.attr_write_log.is_empty() {
            return Err("cannot fork experiment with pending attribute-write observations");
        }
        if !self.framebuffers.is_empty() {
            return Err("cannot fork experiment with attached framebuffer handles");
        }
        if self.rule_firing_capture_active {
            return Err("cannot fork experiment during rule-state capture");
        }

        let mut fork = Self::new(self.checker.clone());
        fork.graph = if share_adjacency {
            self.graph.clone_sharing_graph_pages()
        } else if share_slabs {
            self.graph.clone_sharing_slabs()
        } else {
            self.graph.clone_eager()
        };
        fork.graph.clear_experiment_observers();
        fork.interner = self.interner.clone();
        fork.terms = self.terms.clone();
        fork.concepts = self.concepts.clone();
        fork.rules = self.rules.clone();
        fork.next_rule_uid = self.next_rule_uid;
        fork.rule_state_trace_config = self.rule_state_trace_config.clone();

        // Preserve the current matching configuration and valid rule indexes,
        // while keeping observations, evaluator caches, and compiled artifacts
        // branch-local. Candidate writes will dirty/rebuild those as usual.
        fork.rule_edge_type_deps = self.rule_edge_type_deps.clone();
        fork.rule_readers_by_key = self.rule_readers_by_key.clone();
        fork.rule_reads_any = self.rule_reads_any.clone();
        fork.rule_has_where = self.rule_has_where.clone();
        fork.rule_dirty = self.rule_dirty.clone();
        fork.rule_cursors = self.rule_cursors.clone();
        fork.edge_delete_version = self.edge_delete_version;
        fork.gamma_epoch = self.gamma_epoch.detached();
        fork.gamma_graph_root = self.gamma_graph_root;
        fork.active_shape_target = self.active_shape_target.clone();

        fork.precise_dirty = self.precise_dirty;
        fork.dirty_telemetry = self.dirty_telemetry;
        fork.dirty_overaggressive = self.dirty_overaggressive;
        fork.binding_projection = self.binding_projection;
        fork.projection_overaggressive = self.projection_overaggressive;
        fork.empty_match_proof = self.empty_match_proof;
        fork.empty_match_proof_unsound = self.empty_match_proof_unsound;
        fork.incremental_match = self.incremental_match;
        fork.fresh_node_exempt = self.fresh_node_exempt;
        fork.batch_incremental = self.batch_incremental;
        fork.own_write_exempt = self.own_write_exempt;
        fork.precise_rule_deletes = self.precise_rule_deletes;
        fork.seeded_join_order = self.seeded_join_order;
        fork.write_frontier = self.write_frontier;
        fork.hop_frontier = self.hop_frontier;
        fork.delete_frontier = self.delete_frontier;
        fork.incremental_match_unsound = self.incremental_match_unsound;
        fork.predicate_retraction = self.predicate_retraction;
        fork.predicate_retraction_unsound = self.predicate_retraction_unsound;
        fork.gamma_residual_capture = self.gamma_residual_capture;
        fork.gamma_residual_root = self.gamma_residual_root;
        fork.next_fb_id = self.next_fb_id;

        // Rebuild and trace state is deliberately local to the branch.
        fork.rule_firing_capture_active = false;
        fork.pending_turn_last_progress_rule = None;
        fork.rule_state_trace_events.clear();
        fork.rule_state_trace_dropped = 0;
        fork.rule_cost_micros = vec![0; self.rules.len()];
        fork.rule_cost_count = vec![0; self.rules.len()];
        fork.rule_cost_progress = vec![0; self.rules.len()];
        fork.any_mutation = false;
        fork.eval_cache = crate::term::EvalCache::default();
        fork.shape_cache = crate::shape::ShapeCache::new();
        fork.shape_pruned_count = 0;
        fork.dirty_marks = [0; 9];
        fork.empty_match_skips.clear();
        fork.rule_dirty_nodes = self.rule_dirty_nodes.clone();
        fork.rule_dirty_dyn_nodes = self.rule_dirty_dyn_nodes.clone();
        fork.rule_pred_retract_ok = self.rule_pred_retract_ok.clone();
        #[cfg(all(target_arch = "x86_64", target_os = "linux"))]
        {
            fork.rule_where_jit = std::iter::repeat_with(|| None)
                .take(self.rules.len())
                .collect();
        }
        Ok(fork)
    }

    /// Check that native state is eligible for a fork-based experiment.
    /// This does not inspect Python process threads or wrapper-owned hooks;
    /// callers must apply those guards separately.
    pub fn validate_experiment_fork(&self) -> Result<(), &'static str> {
        if !self.graph.pending_rule_edits.is_empty()
            || !self.graph.pending_rule_patches.is_empty()
            || !self.graph.pending_fb_samples.is_empty()
            || !self.graph.pending_track_identity.is_empty()
            || !self.graph.pending_net_collapses.is_empty()
        {
            return Err("cannot fork experiment with pending graph effects");
        }
        if !self.graph.attr_write_log.is_empty() {
            return Err("cannot fork experiment with pending attribute-write observations");
        }
        if !self.framebuffers.is_empty() {
            return Err("cannot fork experiment with attached framebuffer handles");
        }
        if self.rule_firing_capture_active {
            return Err("cannot fork experiment during rule-state capture");
        }
        if self.rules.iter().any(|rule| rule.reads_external) {
            return Err("cannot fork experiment with native rules that read external state");
        }
        Ok(())
    }

    fn configure_rule_state_trace(
        &mut self,
        rule_names: &[String],
        node_ids: &[u32],
        attr_names: &[String],
        max_events: usize,
    ) {
        let rule_names = rule_names.iter().map(|name| self.interner.intern(name)).collect();
        let attr_keys: Vec<Sym> = attr_names.iter().map(|name| self.interner.intern(name)).collect();
        self.rule_state_trace_events.clear();
        self.rule_state_trace_dropped = 0;
        self.rule_state_trace_config = Some(RuleStateTraceConfig {
            rule_names,
            node_ids: node_ids.iter().copied().map(NodeID).collect(),
            attr_keys,
            attr_names: attr_names.to_vec(),
            max_events: max_events.min(100_000),
        });
    }

    fn record_rule_state_trace(&mut self, rule_name: Sym, pass_index: usize, progress_step: usize) {
        let Some(config) = self.rule_state_trace_config.as_ref() else { return; };
        if !config.rule_names.contains(&rule_name) { return; }
        if self.rule_state_trace_events.len() >= config.max_events {
            self.rule_state_trace_dropped = self.rule_state_trace_dropped.saturating_add(1);
            return;
        }
        let node_ids = config.node_ids.clone();
        let attr_keys = config.attr_keys.clone();
        let attr_names = config.attr_names.clone();
        let values = node_ids.iter().map(|&node_id| {
            if !self.graph.has_node(node_id) { return vec![None; attr_keys.len()]; }
            let attrs = &self.graph.node(node_id).attrs;
            attr_keys.iter().map(|key| match attrs.get(key) {
                Some(Value::Float(value)) => Some(*value),
                Some(Value::Int(value)) => Some(*value as f64),
                Some(Value::Rational(numerator, denominator)) if *denominator != 0 => {
                    Some(*numerator as f64 / *denominator as f64)
                }
                Some(Value::Bool(value)) => Some(if *value { 1.0 } else { 0.0 }),
                _ => None,
            }).collect::<Vec<_>>()
        }).collect();
        self.rule_state_trace_events.push(RuleStateTraceEvent {
            pass_index,
            progress_step,
            rule_name: self.interner.resolve(rule_name).to_owned(),
            node_ids: node_ids.iter().map(|node_id| node_id.0).collect(),
            attr_names,
            values,
        });
    }

    /// Run the exact native `tick` cycle path with an opt-in post-rule observer.
    /// The observer reads selected graph attributes after each successful
    /// invocation of a named rule; normal ticks do not enable this path.
    pub fn tick_with_rule_state_trace(
        &mut self,
        max_steps: usize,
        detect_cycles: bool,
        rule_names: &[String],
        node_ids: &[u32],
        attr_names: &[String],
        max_events: usize,
    ) -> (usize, Vec<RuleStateTraceEvent>, usize) {
        self.configure_rule_state_trace(rule_names, node_ids, attr_names, max_events);
        crate::scale_audit::ffi(1, 0);
        crate::scale_audit::begin_epoch();
        crate::cognitive_cycle::advance_cognitive_epoch(self);
        let steps = crate::cognitive_cycle::execute(
            self,
            crate::cognitive_cycle::CyclePlan::Default,
            max_steps,
            detect_cycles,
            false,
            1,
        ).steps;
        self.rule_state_trace_config = None;
        let events = std::mem::take(&mut self.rule_state_trace_events);
        let dropped = std::mem::take(&mut self.rule_state_trace_dropped);
        (steps, events, dropped)
    }

    /// Set the active shape target. Rule firings whose where-clause
    /// Shape is incompatible with `target` will be skipped (counted in
    /// `shape_pruned_count`). Pass None to clear and let every rule
    /// fire.
    pub fn set_shape_target(&mut self, target: Option<crate::shape::Shape>) {
        if self.active_shape_target != target {
            self.active_shape_target = target;
            self.gamma_epoch.bump();
        }
    }

    /// `negative_problem_space_pruning_combines_cousot_lattice_with_
    /// nelson_narens_control` applied to a candidate list. Returns
    /// only the candidates whose Shape passes the active_shape_target
    /// filter (or all when no target is set). Uses the substrate's
    /// shape_cache — every call is O(1) per candidate on cache hit.
    /// Callers (Filter primitive, custom enumeration) use this for
    /// arbitrary candidate sets without hitting the dispatch path.
    pub fn shape_filter_terms(
        &mut self,
        candidates: &[crate::term::TermIdx],
    ) -> Vec<crate::term::TermIdx> {
        let Some(target) = self.active_shape_target else {
            return candidates.to_vec();
        };
        let mut out = Vec::with_capacity(candidates.len());
        for &idx in candidates {
            let s = self.shape_of_term(idx);
            if crate::shape::shapes_compatible(&s, &target) {
                out.push(idx);
            }
        }
        out
    }

    /// Manually reset the three Shape-pruning counters. Mostly useful
    /// for tests or for callers that drive their own tick boundary
    /// without going through run_rules.
    pub fn reset_shape_counters(&mut self) {
        self.shape_pruned_count = 0;
        self.counters.derivation_shape_pruned = 0;
        self.counters.concept_shape_pruned = 0;
    }

    /// §9/§12.3 GATE HOOK — restore the PRE-pushdown matcher at runtime by
    /// clearing every rule's pushdown plan (an empty plan means `extend_each`
    /// evaluates the where-clause whole at the leaf, exactly as before).
    ///
    /// This exists so the byte-identity gate can compare OLD PATH vs NEW PATH
    /// with BOTH RECOMPUTED LIVE IN ONE PROCESS, rather than freezing a digest
    /// constant into a test. §12.3: a gate pinned to a mutable tree's hash
    /// rots — two did, the same day they were written, by falsely accusing an
    /// innocent rung. The invariant is "pushdown changes no binding", and that
    /// is what gets tested; nothing here is a tunable.
    ///
    /// Returns how many plans were cleared (0 ⇒ pushdown was never armed,
    /// which the gate treats as a FAILED POSITIVE CONTROL — a gate that can
    /// only ever pass is not a gate).
    pub fn clear_pushdown_plans(&mut self) -> usize {
        let mut n = 0;
        for r in self.rules.iter_mut() {
            if !r.where_conjuncts.is_empty() {
                r.where_conjuncts.clear();
                n += 1;
            }
        }
        n
    }

    /// How many active rules currently carry a pushdown plan, and their names.
    /// The positive control for "pushdown is actually engaged on this world".
    pub fn pushdown_armed(&self) -> Vec<String> {
        self.rules
            .iter()
            .filter(|r| r.active && !r.where_conjuncts.is_empty())
            .map(|r| self.interner.resolve(r.name).to_string())
            .collect()
    }

    /// WITHIN-RUST ATTRIBUTION — a MEASURING INSTRUMENT. Changes no behaviour.
    ///
    /// `rule_costs_report` says a rule costs 12.8ms; it does NOT say WHY. This
    /// decomposes ONE rule's MATCH cost into the categories that actually exist
    /// in `extend_each`, by re-running the match with a NO-OP visit (no apply,
    /// no mutation — the graph is untouched, so calling this is byte-identical
    /// to not calling it) under progressively-stripped variants:
    ///
    ///   `scan`   — only match_edges[0], where_=None. Pure edge enumeration of
    ///              the driving edge type + binding insert/remove.
    ///   `enum`   — all match_edges, where_=None. Adds neighbour expansion,
    ///              the full binding construction, and the distinctness check.
    ///   `setup`  — all match_edges, where_= a trivial attr-free `Eq(1,1)`.
    ///              Adds the interpreter's PER-BINDING cost: Env build +
    ///              EvalCtx construction + one evaluate() dispatch.
    ///   `full`   — the real rule, real where-clause. Adds the actual attr-map
    ///              lookups + comparisons (short-circuiting as the real And does).
    ///
    /// The differences attribute the tick:
    ///   enumeration      = scan
    ///   expansion        = enum  - scan
    ///   interp. setup    = setup - enum
    ///   attr match+eval  = full  - setup
    /// and they RECONCILE by construction: they sum to `full`.
    ///
    /// WHY VARIANTS AND NOT PER-OP TIMERS: `scale_wall_measure.py` recorded that
    /// a per-call probe biases exactly the thing it measures (it inflated the
    /// Python side ~1.8x). At ~65k bindings/visit an `Instant::now()` pair per
    /// binding (~20-25ns) would add ~3ms to a ~13ms rule — a ~25% perturbation
    /// concentrated on the hot path. ONE timer pair per VARIANT (4 pairs total)
    /// perturbs nothing measurable.
    ///
    /// The JIT is forced OFF (`where_jit=None`) for EVERY variant, because the
    /// real rule's where-clause does not compile anyway (`cmp_reads_attr` bails
    /// on a Float-valued attr comparison), so the interpreter path IS the live
    /// path. Holding it constant keeps the four variants comparable.
    ///
    /// Returns (variant_name, micros_total, bindings_visited) per variant.
    pub fn profile_rule_match(&mut self, rule_name: &str, reps: usize) -> Vec<(String, u64, u64)> {
        let name_sym = match self.interner.lookup(rule_name) {
            Some(s) => s,
            None => return Vec::new(),
        };
        let rule_idx = match self
            .rules
            .iter()
            .position(|r| r.name == name_sym && r.active)
        {
            Some(i) => i,
            None => return Vec::new(),
        };
        let real = self.rules[rule_idx].clone();

        // A trivial attr-free where: Eq(Lit(1), Lit(1)). Allocated once, in the
        // arena (append-only; adding unreachable Terms changes no rule).
        let lit_a = self.terms.add(crate::term::TermNode::Lit {
            value: crate::value::Value::Int(1),
        });
        let lit_b = self.terms.add(crate::term::TermNode::Lit {
            value: crate::value::Value::Int(1),
        });
        let triv = self
            .terms
            .add(crate::term::TermNode::Eq { a: lit_a, b: lit_b });

        // EVERY stripped variant MUST clear `where_conjuncts`. A clone inherits
        // the pushdown plan, and `extend_each` runs pushdown off the PLAN, not
        // off `where_` — so a variant with `where_=None` but a live plan would
        // still evaluate the real conjuncts and the decomposition would be
        // silently wrong (the `enum` bar would contain where-clause work). This
        // bit me: the categories are only meaningful because of these clears.
        let mut variants: Vec<(String, crate::rewrite::RewriteRule)> = Vec::new();
        {
            let mut r = real.clone();
            r.match_edges = vec![real.match_edges[0].clone()];
            r.where_ = None;
            r.where_conjuncts = Vec::new();
            r.index_hints = Vec::new();
            variants.push(("scan".to_string(), r));
        }
        {
            let mut r = real.clone();
            r.where_ = None;
            r.where_conjuncts = Vec::new();
            variants.push(("enum".to_string(), r));
        }
        {
            let mut r = real.clone();
            r.where_ = Some(triv);
            r.where_conjuncts = Vec::new();
            variants.push(("setup".to_string(), r));
        }
        // The PRE-pushdown path: real where, evaluated whole at the leaf.
        {
            let mut r = real.clone();
            r.where_conjuncts = Vec::new();
            variants.push(("full_nopushdown".to_string(), r));
        }
        // The LIVE path (pushdown as derived).
        variants.push(("full".to_string(), real.clone()));

        let mut out = Vec::new();
        for (label, rule) in variants {
            let mut bindings: u64 = 0;
            let t0 = std::time::Instant::now();
            for _ in 0..reps.max(1) {
                bindings = 0;
                crate::rewrite::match_rule_each(
                    &rule,
                    &self.terms,
                    &self.graph,
                    &self.interner,
                    Some(&self.concepts),
                    Some(&self.framebuffers),
                    None,
                    None,
                    |_b| {
                        bindings += 1;
                        true
                    },
                );
            }
            let micros = t0.elapsed().as_micros() as u64 / (reps.max(1) as u64);
            out.push((label, micros, bindings));
        }
        out
    }

    /// Self-instrumentation: (rule_name, accumulated micros, times processed) per rule.
    /// The observation the agent reads to diagnose its OWN tick — which rule dominates.
    pub fn rule_costs_report(&self) -> Vec<(String, u64, u64, u64)> {
        self.rules
            .iter()
            .enumerate()
            .map(|(i, r)| {
                (
                    self.interner.resolve(r.name).to_string(),
                    self.rule_cost_micros.get(i).copied().unwrap_or(0),
                    self.rule_cost_count.get(i).copied().unwrap_or(0),
                    self.rule_cost_progress.get(i).copied().unwrap_or(0),
                )
            })
            .collect()
    }

    pub fn reset_rule_costs(&mut self) {
        for c in self.rule_cost_micros.iter_mut() {
            *c = 0;
        }
        for n in self.rule_cost_count.iter_mut() {
            *n = 0;
        }
        for p in self.rule_cost_progress.iter_mut() {
            *p = 0;
        }
    }

    /// FALLBACK TRACE / H1 — `(rule_name, attr_key, hits)`: this rule read that
    /// attribute off a LIVE node that did not have it, i.e. it computed on a
    /// value **nobody wrote**. Resolved here because the interner lives on the
    /// Substrate; the tally itself is thread-local in `fallback_trace`.
    pub fn defaulted_reads_report(&self) -> Vec<(String, String, u64)> {
        crate::fallback_trace::defaulted_raw()
            .into_iter()
            .map(|(r, k, n)| {
                (
                    self.interner.resolve(r).to_string(),
                    self.interner.resolve(k).to_string(),
                    n,
                )
            })
            .collect()
    }

    /// FALLBACK TRACE / H2 — `(rule_name, hits)`: this rule's `Not(Exists(..))`
    /// guard passed because its source was EMPTY. The absence-branch hypothesis
    /// offered to the rung, instrumented so it can be measured against H1
    /// rather than assumed.
    pub fn absence_branches_report(&self) -> Vec<(String, u64)> {
        crate::fallback_trace::absence_raw()
            .into_iter()
            .map(|(r, n)| (self.interner.resolve(r).to_string(), n))
            .collect()
    }

    /// `shape_mismatch_prunes_negative_problem_space`: returns true if
    /// the rule is in the negative problem space relative to the
    /// active_shape_target — should be SKIPPED. Returns false when:
    ///  · no target is active (no constraint), OR
    ///  · the rule has no where-clause (no candidate to disqualify), OR
    ///  · the rule's where-clause Shape is compatible with the target.
    /// O(1) per call after first walk: shape_cache hits on every
    /// subsequent call for the same rule.
    pub fn rule_in_negative_space(&mut self, idx: crate::rewrite::RuleIdx) -> bool {
        let Some(target) = self.active_shape_target else {
            return false;
        };
        if (idx.0 as usize) >= self.rules.len() {
            return false;
        }
        let Some(where_idx) = self.rules[idx.0 as usize].where_ else {
            return false;
        };
        let where_shape = self.shape_of_term(where_idx);
        !crate::shape::shapes_compatible(&where_shape, &target)
    }

    /// `shape_keyed_lookup_is_memo_function_cache_hit` — return the
    /// Shape of `idx` from the cache, computing + caching on miss.
    /// O(1) on cache hits per Michie 1968 / L6 bounded_coordination
    /// _latency. The substrate's pruning, rule dispatching, and any
    /// Rule-engine code reading function-shape can call this without
    /// repeating Term-tree walks. See `crate::shape::assess_shape`
    /// for the walker implementation.
    pub fn shape_of_term(&mut self, idx: crate::term::TermIdx) -> crate::shape::Shape {
        self.shape_cache.assess_and_cache(idx, &self.terms)
    }

    /// Cloneable Epoch handle — pass to an `AdaptiveDispatcher`
    /// via `with_shared_epoch` so dispatcher cache invalidates
    /// on Γ changes the substrate emits. Cheap (Arc<AtomicU64>).
    pub fn gamma_epoch(&self) -> crate::l2_adaptive::Epoch {
        self.gamma_epoch.clone()
    }

    /// Cheap revision token for experiment isolation checks over semantic
    /// graph facts and the installed rule/grammar store. Every TypedGraph
    /// writer advances its content version; rule and grammar edits advance
    /// the Γ epoch. This deliberately does not claim to fingerprint caches,
    /// telemetry, or other derived execution state.
    pub fn experiment_graph_rule_revision(&self) -> ExperimentRevision {
        (self.graph.mutation_version(), self.gamma_epoch.current(), self.rules.len())
    }

    /// Read-only views of semantic stores. Mutation goes through tracked APIs
    /// so experiment revisions remain constant-time without content hashing.
    pub fn rules(&self) -> &[crate::rewrite::RewriteRule] { &self.rules }
    pub fn term_arena(&self) -> &TermArena { &self.terms }
    pub fn concept_resolver(&self) -> &ConceptResolver { &self.concepts }
    pub fn consistency_checker(&self) -> &ConsistencyChecker { &self.checker }
    pub fn interner(&self) -> &Interner { &self.interner }
    pub fn intern_symbol(&mut self, text: &str) -> Sym { self.interner.intern(text) }
    pub fn resolve_symbol(&self, sym: Sym) -> &str { self.interner.resolve(sym) }
    pub fn active_shape_target(&self) -> Option<crate::shape::Shape> { self.active_shape_target }

    /// Append one Term node through the revision-tracked substrate owner.
    pub fn add_term_node(&mut self, node: crate::term::TermNode) -> TermIdx {
        let idx = self.terms.add(node);
        self.gamma_epoch.bump();
        idx
    }

    /// Add a production without creating a graph mirror. Persistence replay
    /// uses this when the graph already contains the mirrored representation.
    pub fn add_production_no_mirror(&mut self, production: crate::grammar::Production) -> ProdIdx {
        let idx = self.checker.grammar.add(production);
        self.gamma_epoch.bump();
        idx
    }

    /// Atomically apply an experiment graph-diff receipt to the primary graph.
    /// The receipt must target the exact semantic graph/rule revision from
    /// which its branch was forked. Graph and interner updates are staged by
    /// `persist::apply_graph_delta`; stale or malformed receipts leave primary
    /// state untouched.
    ///
    /// This is a structural merge primitive: it does not classify hypothesis
    /// assumptions, reground conclusions, or invoke `commit_gate`. Callers
    /// must apply their epistemic/authorization policy before using it against
    /// an authoritative graph; speculative graphs may use it directly.
    pub fn apply_experiment_graph_delta(
        &mut self,
        expected_revision: ExperimentRevision,
        delta: &serde_json::Value,
    ) -> Result<(), String> {
        let actual = self.experiment_graph_rule_revision();
        if actual != expected_revision {
            return Err(format!("stale experiment revision: expected {expected_revision:?}, current {actual:?}"));
        }

        let node_mutated = ["nodes_added", "nodes_removed", "nodes_changed"]
            .iter().any(|key| delta.get(*key).and_then(serde_json::Value::as_array)
                .is_some_and(|items| !items.is_empty()));
        let type_changed = delta.get("nodes_changed").and_then(serde_json::Value::as_array)
            .is_some_and(|items| items.iter().any(|item| item.get("type_after").is_some()));
        let mut deleted_edge_types: Vec<String> = Vec::new();
        if let Some(removed) = delta.get("edges_removed").and_then(serde_json::Value::as_array) {
            deleted_edge_types.extend(removed.iter().filter_map(|e|
                e.get("type").and_then(serde_json::Value::as_str).map(str::to_owned)));
        }
        if let Some(removed_nodes) = delta.get("nodes_removed").and_then(serde_json::Value::as_array) {
            for raw in removed_nodes.iter().filter_map(serde_json::Value::as_u64) {
                if let Ok(raw) = u32::try_from(raw) {
                    let nid = NodeID(raw);
                    if self.graph.has_node(nid) {
                        for idx in self.graph.out_edges_slice(nid, None).iter()
                            .chain(self.graph.in_edges_slice(nid, None).iter()) {
                            let name = self.interner.resolve(self.graph.edge(*idx).edge_type).to_owned();
                            if !deleted_edge_types.contains(&name) { deleted_edge_types.push(name); }
                        }
                    }
                }
            }
        }

        let impacts = crate::persist::apply_graph_delta(
            &mut self.graph, &mut self.interner, delta)?;
        if node_mutated { self.mark_node_mutation(); }
        if type_changed {
            // A node retype can change the matchability of every existing
            // incident edge, including rules without where-clauses. Force a
            // complete rematch rather than relying on attr-write invalidation.
            for i in 0..self.rule_dirty.len() {
                self.rule_dirty[i] = true;
                if i < self.rule_cursors.len() { self.rule_cursors[i].clear(); }
            }
        }
        for edge_type in impacts {
            self.mark_edge_type_dirty(edge_type);
        }
        if !deleted_edge_types.is_empty() {
            self.edge_delete_version = self.edge_delete_version.wrapping_add(deleted_edge_types.len() as u64);
            for name in deleted_edge_types {
                let edge_type = self.interner.intern(&name);
                self.mark_edge_type_dirty(edge_type);
                self.invalidate_readers_of_deleted_edge_type(edge_type);
            }
        }
        Ok(())
    }

    /// The `GammaGrammar` root node `add_production`'s graph mirror hangs
    /// off (see `grammar_reflect.rs`), if one has been created yet. `None`
    /// until the first mirrored `add_production` call.
    pub fn gamma_graph_root(&self) -> Option<crate::graph::NodeID> {
        self.gamma_graph_root
    }

    /// JIT self-modification the agent can PERCEIVE: how many of its rule where-clauses
    /// currently run as JIT-compiled native (`CompiledWhere`), out of how many rules, plus
    /// the Γ epoch (bumps on every grammar change → recompiles). This is live binary
    /// self-modification the substrate already does on the agent's own rules.
    pub fn jit_stats(&self) -> (usize, usize, u64) {
        let compiled = self.rule_where_jit.iter().filter(|c| c.is_some()).count();
        (compiled, self.rules.len(), self.gamma_epoch.current())
    }

    /// Add a Γ production. Wraps `checker.grammar.add` with an
    /// epoch bump so installed L2 dispatchers see the change, AND mirrors
    /// the production into the graph as a real `GammaProduction` node
    /// (recommendation 2(ii), `GAMMA_REFLECTION_WIRING_PREREG.md` §1.1):
    /// `where_`/`weight` are routed through `reflect::term_to_subgraph`,
    /// so they become literal `Term.*` subgraphs, not an opaque blob.
    ///
    /// `checker.grammar` (mutated below via `.add`) remains the sole
    /// struct `check_edge` reads — this does not touch that hot path.
    /// The mirror is written from the SAME call, so it cannot drift from
    /// what `checker.grammar` holds for anything added through this one
    /// method (see `grammar_reflect.rs`'s module doc for the honest
    /// boundary: this is a mirror, not yet a single source of truth).
    pub fn add_production(&mut self, p: crate::grammar::Production) -> crate::grammar::ProdIdx {
        let root = match self.gamma_graph_root {
            Some(r) => r,
            None => {
                let type_sym = self
                    .interner
                    .intern(crate::grammar_reflect::GAMMA_GRAMMAR_NODE);
                let r = self
                    .graph
                    .insert_node(type_sym, rustc_hash::FxHashMap::default());
                self.gamma_graph_root = Some(r);
                r
            }
        };
        let production_edge = self.interner.intern("production");
        let index = self.graph.out_edges_idx(root, Some(production_edge)).len() as i64;
        crate::grammar_reflect::production_to_subgraph(
            root,
            index,
            &p,
            &mut self.graph,
            &self.terms,
            &mut self.interner,
        );
        let idx = self.checker.grammar.add(p);
        self.gamma_epoch.bump();
        idx
    }

    /// GAMMA_COLLAPSE_ALGORITHM spike: mint ONE `GammaResidual` node
    /// recording a Type-1 rejection triple. Called ONLY from `add_edge`'s
    /// `Type1NoProduction` arm, ONLY when `gamma_residual_capture` is on
    /// (see the field doc — default off, byte-identical when off).
    ///
    /// Mechanical event logging, deliberately undecided: this method does
    /// NOT check whether the triple has been seen before, does NOT count
    /// occurrences, and does NOT decide anything about recurrence. That
    /// decision belongs to the seed rule `note_gamma_production_gap`
    /// (`seeds/gamma_residual.json`), which groups `GammaResidual` nodes by
    /// their triple attrs via existing `Count`/`Filter`/`Argmin` Terms and
    /// applies the `shape_decode.rs` support discipline (mint at support
    /// >= 2). Rust's only job here is "this happened, and here is what
    /// happened" — the same division of labour `_answer_topic_reply`
    /// already uses for `outcome='resolved'|'unresolved'` (a datum, not a
    /// decision) at the Python/graph boundary; here it is Rust/graph, one
    /// layer further down, for the identical reason: the DSL's own Count/
    /// Filter/Argmin already exist and are the right place for the "does
    /// this recur" decision, not a second, parallel counting mechanism.
    ///
    /// Node insertion goes through `self.add_node` (not a raw
    /// `graph.insert_node`) specifically so the engine's own dirty-tracking
    /// runs (`mark_node_mutation` / `mark_external_write`) — a raw insert
    /// left the new `GammaResidual` invisible to `run_rules()` until some
    /// LATER, unrelated write happened to trigger a full rescan (caught live
    /// by the demonstration script in GAMMA_COLLAPSE_ALGORITHM_RESULTS.md
    /// §5: five same-triple rejections in a row minted nothing, and the
    /// mint only appeared after an unrelated `add_node` elsewhere forced the
    /// blanket dirty path). The anchoring edge is still UNCHECKED
    /// `graph.insert_edge` (never `self.add_edge`) — this is engine-internal
    /// bookkeeping data, not agent-authored semantic graph content, the same
    /// category `add_production`'s own `GammaProduction` mirror already
    /// writes unchecked via `production_to_subgraph` — but its edge TYPE is
    /// explicitly marked dirty afterward via `mark_edge_type_dirty`, the
    /// exact call the checked `add_edge` path makes for an admitted edge
    /// (`substrate.rs`, `CheckOutcome::Admitted` arm), so a rule matching on
    /// that edge type is woken the same way either path would wake it.
    fn record_gamma_residual(&mut self, src_type: Sym, edge_type: Sym, tgt_type: Sym) {
        let root = match self.gamma_residual_root {
            Some(r) => r,
            None => {
                let type_sym = self.interner.intern("GammaResidualRoot");
                let r = self.add_node(type_sym, rustc_hash::FxHashMap::default());
                self.gamma_residual_root = Some(r);
                r
            }
        };
        let residual_type = self.interner.intern("GammaResidual");
        let src_key = self.interner.intern("src_type");
        let edge_key = self.interner.intern("edge_type");
        let tgt_key = self.interner.intern("tgt_type");
        let hit_key = self.interner.intern("hit_count");
        let proposed_key = self.interner.intern("proposed");
        let mut attrs = FxHashMap::default();
        attrs.insert(src_key, Value::Str(src_type));
        attrs.insert(edge_key, Value::Str(edge_type));
        attrs.insert(tgt_key, Value::Str(tgt_type));
        attrs.insert(hit_key, Value::Float(1.0));
        attrs.insert(proposed_key, Value::Float(0.0));
        let residual_id = self.add_node(residual_type, attrs);
        let residual_edge = self.interner.intern("gamma_residual");
        self.graph
            .insert_edge(root, residual_edge, residual_id, FxHashMap::default())
            .expect("freshly-inserted GammaResidual node always connects");
        self.mark_edge_type_dirty(residual_edge);
    }

    /// Mark every rule whose read set includes `edge_type` as dirty.
    /// Uses the inverse RuleKey index while retaining stable RuleIdx order.
    #[inline]
    pub(crate) fn mark_edge_type_dirty(&mut self, edge_type: Sym) {
        self.any_mutation = true;
        // Compatibility floor: the inverse index is built and introspectable,
        // but serial mode retains the proven dependency scan until shadow
        // equality has been measured across the whole suite.
        let tel = self.dirty_telemetry;
        for i in 0..self.rule_edge_type_deps.len() {
            if self.rule_edge_type_deps[i].contains(&edge_type) {
                if tel {
                    self.dirty_marks[1] += 1;
                    if !self.rule_dirty[i] {
                        self.dirty_marks[7] += 1;
                    }
                }
                self.rule_dirty[i] = true;
            }
        }
    }

    /// Block 192000: on a DELETE of edge type `et` under `incremental_match`,
    /// clear the semi-naive cursors of every rule that READS `et` (in a match
    /// edge OR a where-clause). Per-edge-type versioning already invalidates a
    /// cursor whose MATCH edge type was deleted, but a rule that reads `et` only
    /// in its where (matching a DIFFERENT type) can have its where FLIP when an
    /// `et` edge is deleted (negation / `Not Exists`), and the new-edges cursor
    /// would miss that. The committed engine catches it via the global
    /// `edge_delete_version` bump (which invalidates every cursor); this is the
    /// type-local equivalent — sound (a rule not reading `et` cannot be affected
    /// by its deletion) and byte-identical on the deleting path. INSERTS never
    /// call this, so the append-only incremental win is preserved.
    #[inline]
    fn invalidate_readers_of_deleted_edge_type(&mut self, edge_type: Sym) {
        // delete frontier: only rule-effect DelEdges are handled precisely; any
        // other delete path (external / cascade) takes this conservative one
        self.graph.edge_delete_log.clear();
        if !self.incremental_match {
            return;
        }
        // THE UNSOUND-RETRACTION FALSIFIER: skip the where-reader cursor clear
        // entirely, so a delete that FLIPS a `Not Exists` where on a stable edge
        // is silently missed — the observable retraction (a slot that should
        // open when its blocking edge is deleted) never fires. Must diverge from
        // the full rescan. Measurement use only.
        if self.incremental_match_unsound {
            return;
        }
        for i in 0..self.rule_edge_type_deps.len() {
            if !self.rule_edge_type_deps[i].contains(&edge_type) || i >= self.rule_cursors.len() {
                continue;
            }
            // A rule that MATCHES `et` is already handled by the per-edge-type
            // version: its `et` cursor's stored version differs from the bumped
            // one, so it goes stale and full-rescans (RETRACTS) on its own. We
            // must NOT clear its cursor here — leaving the version check as the
            // sole retraction path is exactly what the UNSOUND falsifier defeats,
            // which is what makes the reduction gate non-vacuous. Only a
            // WHERE-ONLY reader (reads `et`, does not match it) needs the cursor
            // cleared, because per-type versioning of its OWN match types would
            // not see `et`'s deletion flip its where.
            let matches_et = self.rules[i]
                .match_edges
                .iter()
                .any(|me| me.edge_type == edge_type);
            if !matches_et {
                self.rule_cursors[i].clear();
            }
        }
    }

    /// DELETE FRONTIER (`delete_frontier`): the precise twin of
    /// `invalidate_readers_of_deleted_edge_type` for the rule-effect `DelEdge`s
    /// in `log`. A reader MATCHING the type is left to the per-type delete
    /// version (stale ⇒ full re-match), exactly as before. A non-matching reader
    /// whose every read of the type is local, or is its own seedable `AddEdge`
    /// target, re-checks the bindings of the deleted edge's endpoints (node-
    /// seeded, cursor kept); any other reader is cleared as before.
    fn invalidate_readers_of_deleted_edges(&mut self, log: &[(NodeID, Sym, NodeID)]) {
        if !self.incremental_match || self.incremental_match_unsound {
            return;
        }
        for &(src, edge_type, tgt) in log {
            for i in 0..self.rule_edge_type_deps.len().min(self.rule_cursors.len()) {
                if !self.rule_edge_type_deps[i].contains(&edge_type) {
                    continue;
                }
                let r = &self.rules[i];
                if r.match_edges.iter().any(|me| me.edge_type == edge_type) {
                    continue;
                }
                // a rule that only DELETES this type (no match / term read, no
                // AddEdge of it) cannot be re-enabled by its deletion: re-firing
                // would delete an absent edge
                let reads_term = r.term_edge_reads_strict.contains(&edge_type);
                let only_del = !reads_term
                    && r.effects.iter().all(|e| match e {
                        crate::rewrite::Effect::AddEdge { edge_type: et, .. } => *et != edge_type,
                        crate::rewrite::Effect::DelEdge { .. }
                        | crate::rewrite::Effect::SetAttr { .. }
                        | crate::rewrite::Effect::SetAttrIfDifferent { .. }
                        | crate::rewrite::Effect::AddNodeIfAbsent { .. } => true,
                        _ => false,
                    })
                    && r.effects.iter().any(|e| matches!(e,
                        crate::rewrite::Effect::DelEdge { edge_type: et, .. } if *et == edge_type));
                if only_del {
                    continue;
                }
                let term_local = !r.term_edge_reads_strict.contains(&edge_type)
                    || r.wf_local_out.contains(&edge_type)
                    || r.wf_local_in.contains(&edge_type);
                // a binding that would RE-ADD the deleted edge binds an endpoint
                let adds = r.effects.iter().any(|e| matches!(e,
                    crate::rewrite::Effect::AddEdge { edge_type: et, .. } if *et == edge_type));
                let own_ok = !adds || r.own_edge_seedable.contains(&edge_type);
                if r.wf_ok && term_local && own_ok && i < self.rule_dirty_nodes.len() {
                    self.rule_dirty_nodes[i].insert(src);
                    self.rule_dirty_nodes[i].insert(tgt);
                    self.rule_dirty[i] = true;
                } else {
                    self.rule_cursors[i].clear();
                }
            }
        }
    }

    /// Fresh-node exemption: an EXTERNAL insert of `edge_type` clears the cursor
    /// of every rule whose where/effect terms read that type (a new edge can
    /// change a term's value on a STABLE binding; a pure match-edge driver keeps
    /// its cursor). Mirrors the rule-effect path's `hits_term_edge`.
    fn invalidate_term_readers_of_edge_type(&mut self, edge_type: Sym, src: NodeID, tgt: NodeID) {
        for j in 0..self.rules.len().min(self.rule_cursors.len()) {
            // write frontier: a term read of `edge_type` that is only ever
            // Neighbours / InNeighbours of a bound variable can flip only the
            // bindings of the new edge's src / tgt -- seed those, keep the cursor
            if self.write_frontier
                && self.rules[j].wf_ok
                && !self.rules[j].reads_any_nonlocal
                && (self.rules[j].wf_local_out.contains(&edge_type)
                    || self.rules[j].wf_local_in.contains(&edge_type))
                && j < self.rule_dirty_nodes.len()
            {
                if self.rules[j].wf_local_out.contains(&edge_type) {
                    self.rule_dirty_nodes[j].insert(src);
                }
                if self.rules[j].wf_local_in.contains(&edge_type) {
                    self.rule_dirty_nodes[j].insert(tgt);
                }
                self.rule_dirty[j] = true;
                continue;
            }
            let ter = if self.own_write_exempt {
                &self.rules[j].term_edge_reads_strict
            } else {
                &self.rules[j].term_edge_reads
            };
            if self.rules[j].reads_any_nonlocal || ter.contains(&edge_type) {
                self.rule_dirty[j] = true;
                self.rule_cursors[j].clear();
            }
        }
    }

    /// Isolated-node write exemption: a write (insert / attr) to a node with NO
    /// edges is observable only by type enumeration (`Type` read key) or by an
    /// opaque non-local read; attrs / type of a bound node are unreachable
    /// because no binding or term path reaches an isolated node.
    fn mark_isolated_write(&mut self, ty: Sym) {
        self.any_mutation = true;
        let key = crate::rewrite::RuleKey::Type(ty);
        for j in 0..self.rules.len().min(self.rule_cursors.len()) {
            let rs = if self.own_write_exempt {
                &self.rules[j].read_set_strict
            } else {
                &self.rules[j].read_set
            };
            if self.rules[j].reads_any_nonlocal || rs.contains(&key) {
                self.rule_dirty[j] = true;
                self.rule_cursors[j].clear();
            }
        }
    }

    /// Mark every rule with a where-clause dirty. Called on node mutations
    /// (insert / delete / attr / type change) because where-clauses may
    /// read those via TypeOf/Attr without us tracking the read tightly.
    #[inline]
    fn mark_node_mutation(&mut self) {
        self.any_mutation = true;
        // An attr/type/node change can flip a where-clause on an ALREADY-matched
        // edge (e.g. `satisfied` going 0→1 makes a satisfy-rule fire on an
        // existing `wants` edge). The semi-naive cursor only re-scans NEW edges,
        // so without invalidating it that flip is silently missed. Bump the
        // version — same signal a delete uses — so dirtied where-rules fall back
        // to a full re-match. Only external (Python) mutations reach here; rule
        // effects mutate the graph directly, so hot fixpoints pay nothing.
        self.edge_delete_version += 1;
        // Block 192000: under `incremental_match`, cursors are validated against
        // PER-EDGE-TYPE delete versions, which an attr/node write does NOT bump
        // (no edge was deleted). So the global bump above no longer invalidates
        // a where-rule's cursor. To PRESERVE the where-flip-on-stable-edge
        // catch (byte-identity with the committed engine), explicitly CLEAR the
        // cursor of every where-rule this write dirties → it takes the full
        // re-match, re-evaluating its where fresh, exactly as it does under OFF
        // where the global bump did the invalidating. Where-LESS rules keep
        // their cursors: a node/attr write adds no edge, so it cannot change any
        // MatchEdge binding of a rule with no where.
        let incr = self.incremental_match;
        let tel = self.dirty_telemetry;
        if tel {
            self.dirty_marks[5] += 1;
        }
        for i in 0..self.rule_has_where.len() {
            if self.rule_has_where[i] {
                if tel {
                    self.dirty_marks[2] += 1;
                    if !self.rule_dirty[i] {
                        self.dirty_marks[8] += 1;
                    }
                }
                self.rule_dirty[i] = true;
                if incr && i < self.rule_cursors.len() {
                    self.rule_cursors[i].clear();
                }
            }
        }
    }

    /// PRECISE EXTERNAL DIRTYING (block 187000). The key-precise replacement for
    /// `mark_node_mutation`'s blanket, used only when `precise_dirty` is on.
    ///
    /// `ty` = the node TYPE this write minted / retyped / deleted (`None` for a
    /// plain attr write, which changes no type). `keys` = the attr keys this
    /// write actually touched.
    ///
    /// The predicate is EXACTLY `dirty_by_writeset`'s (see its comment for the
    /// argument): a Type hit is STRUCTURAL and dirties unconditionally; an Attr
    /// hit can only change which bindings a rule produces THROUGH a where-clause
    /// (`MatchEdge` carries no attr constraints), so it dirties only where-rules;
    /// `reads_any` always dirties. `read_set` is an over-approx SUPERSET of a
    /// rule's true reads, so "not in read_set" ⇒ "provably does not read it" —
    /// the safe direction. A dirtied rule gets its OWN cursor cleared (the
    /// per-rule form of the blanket's `edge_delete_version` bump); the global
    /// bump is retained by callers wherever an actual DELETION occurred.
    fn mark_external_write(&mut self, ty: Option<Sym>, keys: &[Sym]) {
        self.any_mutation = true;
        let tel = self.dirty_telemetry;
        if tel {
            self.dirty_marks[5] += 1;
        }
        if self.dirty_overaggressive {
            return; // THE FALSIFIER: wake nobody. MUST break byte-identity.
        }
        for j in 0..self.rules.len() {
            let has_where = self.rule_has_where[j];
            let (reads_any, type_hit, attr_hit) = {
                let rj = &self.rules[j];
                (
                    rj.reads_any,
                    ty.map_or(false, |t| {
                        rj.read_set.contains(&crate::rewrite::RuleKey::Type(t))
                    }),
                    keys.iter()
                        .any(|k| rj.read_set.contains(&crate::rewrite::RuleKey::Attr(*k))),
                )
            };
            if reads_any || type_hit || (attr_hit && has_where) {
                if tel {
                    self.dirty_marks[2] += 1;
                    if !self.rule_dirty[j] {
                        self.dirty_marks[8] += 1;
                    }
                }
                self.rule_dirty[j] = true;
                self.rule_cursors[j].clear();
            }
        }
    }

    /// GAMMA_COLLAPSE_ALGORITHM spike control. DEFAULT FALSE — see the field doc.
    pub fn set_gamma_residual_capture(&mut self, on: bool) {
        self.gamma_residual_capture = on;
    }

    /// Block 187000 controls. `precise_dirty` DEFAULT FALSE — see the field doc.
    pub fn set_precise_dirty(&mut self, on: bool) {
        self.precise_dirty = on;
    }
    pub fn set_dirty_telemetry(&mut self, on: bool) {
        self.dirty_telemetry = on;
        if !on {
            self.dirty_marks = [0; 9];
        }
    }
    pub fn set_dirty_overaggressive(&mut self, on: bool) {
        self.dirty_overaggressive = on;
    }
    /// Block 188000 controls. Both DEFAULT FALSE — see the field docs.
    pub fn set_binding_projection(&mut self, on: bool) {
        self.binding_projection = on;
    }
    pub fn set_projection_overaggressive(&mut self, on: bool) {
        self.projection_overaggressive = on;
    }

    /// Block 189000 controls. Both DEFAULT FALSE — see the field docs.
    pub fn set_empty_match_proof(&mut self, on: bool) {
        self.empty_match_proof = on;
        if on && self.empty_match_skips.len() < self.rules.len() {
            self.empty_match_skips.resize(self.rules.len(), 0);
        }
    }
    pub fn set_empty_match_proof_unsound(&mut self, on: bool) {
        self.empty_match_proof_unsound = on;
    }

    /// Block 192000 controls. Both DEFAULT FALSE — see the field docs.
    pub fn set_incremental_match(&mut self, on: bool) {
        self.incremental_match = on;
    }
    /// Fresh-node exemption control. DEFAULT FALSE — see the field doc.
    pub fn set_fresh_node_exempt(&mut self, on: bool) {
        self.fresh_node_exempt = on;
    }
    /// Semi-naive for batch rules. DEFAULT FALSE — see the field doc.
    pub fn set_batch_incremental(&mut self, on: bool) {
        self.batch_incremental = on;
    }
    /// Own-write exemption control. DEFAULT FALSE — see the field doc.
    pub fn set_own_write_exempt(&mut self, on: bool) {
        self.own_write_exempt = on;
    }
    /// Precise rule-effect edge deletes control. DEFAULT FALSE — see the field doc.
    pub fn set_precise_rule_deletes(&mut self, on: bool) {
        self.precise_rule_deletes = on;
    }
    /// Seeded join order control. DEFAULT FALSE — see the field doc.
    pub fn set_seeded_join_order(&mut self, on: bool) {
        self.seeded_join_order = on;
    }
    /// Hop frontier control. DEFAULT FALSE — see the field doc.
    pub fn set_hop_frontier(&mut self, on: bool) {
        self.hop_frontier = on;
        for r in self.rules.iter_mut() {
            r.set_wf_hop(on);
        }
    }
    /// Delete frontier control. DEFAULT FALSE — see the field doc.
    pub fn set_delete_frontier(&mut self, on: bool) {
        self.delete_frontier = on;
        self.graph.log_edge_deletes = on;
        if !on {
            self.graph.edge_delete_log.clear();
        }
    }
    /// Write frontier control. DEFAULT FALSE — see the field doc.
    pub fn set_write_frontier(&mut self, on: bool) {
        self.write_frontier = on;
        self.graph.log_attr_writes = on || self.predicate_retraction;
        self.graph.log_edge_writes = on;
        if self.rule_dirty_nodes.len() < self.rules.len() {
            self.rule_dirty_nodes.resize(self.rules.len(), Default::default());
        }
        if self.rule_dirty_dyn_nodes.len() < self.rules.len() {
            self.rule_dirty_dyn_nodes.resize(self.rules.len(), Default::default());
        }
    }
    pub fn set_incremental_match_unsound(&mut self, on: bool) {
        self.incremental_match_unsound = on;
    }

    /// Experimental same-graph memoization for repeated ReachableFrom Terms.
    /// Default off until the source-locked parity/cost panel is complete.
    pub fn set_reachable_cache(&mut self, on: bool) {
        self.eval_cache.set_reachable_enabled(on);
    }

    /// Snapshot experimental ReachableFrom cache activity and live retained
    /// payload accounting. See EvalCache::reachable_stats for byte limits.
    pub fn reachable_cache_stats(&self) -> (u64, u64, u64, u64, u64, u64, u64, u64, u64) {
        self.eval_cache.reachable_stats()
    }

    pub fn reachable_cache_stats_reset(&mut self) {
        self.eval_cache.reset_reachable_stats();
    }

    /// Block 194000 controls (ladder rung B). Both DEFAULT FALSE — see the
    /// field docs. Enabling `predicate_retraction` sizes the per-rule dirty-node
    /// state to the current rule count (idempotent; `add_rule` keeps it in step).
    pub fn set_predicate_retraction(&mut self, on: bool) {
        self.predicate_retraction = on;
        // block 292000: arm the rule-effect attr-write log (graph.rs) in lockstep, so
        // dirty_by_writeset can seed the rung-B frontier from rule-effect SetAttr writes.
        self.graph.log_attr_writes = on;
        if on {
            if self.rule_dirty_nodes.len() < self.rules.len() {
                self.rule_dirty_nodes
                    .resize(self.rules.len(), Default::default());
            }
            if self.rule_pred_retract_ok.len() < self.rules.len() {
                self.rule_pred_retract_ok.resize(self.rules.len(), false);
            }
        }
    }
    pub fn set_predicate_retraction_unsound(&mut self, on: bool) {
        self.predicate_retraction_unsound = on;
    }

    /// The version a semi-naive cursor for edge type `et` is validated against
    /// (block 192000). OFF ⇒ the single global `edge_delete_version` (committed
    /// behaviour, byte-identical). ON ⇒ `et`'s OWN per-type delete version, so a
    /// delete of a different edge type does not invalidate this cursor.
    #[inline]
    fn cursor_version(&self, et: Sym) -> u64 {
        if self.incremental_match {
            self.graph.edge_delete_version_by_type(et)
        } else {
            self.edge_delete_version
        }
    }

    /// THE EMPTY-MATCH-SET PROOF (block 189000).
    ///
    /// Returns `true` only when the rule's match set is **PROVABLY EMPTY** under
    /// the current graph, so that skipping its enumeration entirely is
    /// byte-identical to running it.
    ///
    /// **THE PREDICATE.** A rule with at least one match edge is provably empty
    /// if SOME match edge's `edge_type` has ZERO live edges in the graph.
    /// Nothing else — no node-type population check, no `match_type` check, no
    /// where-clause or attribute reasoning. Deliberately minimal: every widening
    /// of this predicate is a soundness liability, and an unsound predicate that
    /// "wins" is a failed optimisation.
    ///
    /// **THE PROOF.** Every binding assigns, to each match edge
    /// `(src_var, et, tgt_var)`, an actual live edge of type `et`: `extend_each`
    /// only ever draws candidates from `graph.neighbours` / `graph.in_neighbours`
    /// / `graph.edges_by_type`, all of which yield live edges of exactly that
    /// type. So a zero-population `et` ⇒ no binding exists ⇒ the rule cannot
    /// fire ⇒ the enumeration is pure cost.
    ///
    /// **WHY THE BOOKKEEPING CANNOT GO STALE — THERE IS NONE.** This is the
    /// load-bearing property, and it is why this predicate was chosen over every
    /// richer one: it reads `edges_by_type`, **the same index the matcher itself
    /// enumerates.** No new counter, no new invariant, no new write path to
    /// maintain. `insert_edge` pushes into it, `delete_edge` retains it out,
    /// `delete_node` cascades through `delete_edge`; `set_type`, `add_node` and
    /// `set_attr` cannot create or destroy an edge and so cannot affect it —
    /// correctly, since the predicate never mentions node types or attributes.
    /// And the direction of any conceivable error is the SAFE one: a stale extra
    /// entry makes `is_empty()` false ⇒ we enumerate ⇒ committed behaviour. Only
    /// a MISSING live edge could make us wrongly claim empty, and a live edge
    /// missing from this index is one the committed matcher could not find
    /// either.
    ///
    /// **PLACEMENT.** Callers put this check *inside* the enumeration sites, so
    /// every surrounding piece of bookkeeping — cursor re-establishment,
    /// `rule_cost_*`, `dirty_by_writeset`, eval-cache clears — runs exactly as
    /// it does today. The ONLY thing elided is the enumeration that provably
    /// yields zero bindings.
    #[inline]
    fn match_set_provably_empty(&self, rule: &crate::rewrite::RewriteRule) -> bool {
        if !self.empty_match_proof {
            return false;
        }
        // A zero-match-edge rule's match set is the single EMPTY binding, which
        // is NOT the empty set — it is exactly how the engine evaluates a
        // where-only rule. Never claim emptiness for one.
        if rule.match_edges.is_empty() {
            return false;
        }
        // The FALSIFIER's threshold is 2 (a singleton edge type is wrongly
        // treated as absent); the SOUND threshold is 1.
        let floor = if self.empty_match_proof_unsound { 2 } else { 1 };
        rule.match_edges
            .iter()
            .any(|me| self.graph.edges_by_type(me.edge_type).len() < floor)
    }

    /// Telemetry: `(rule_name, enumerations_skipped)` for every rule the
    /// emptiness proof has skipped at least once. Read-only; no decision reads
    /// it. Diagnostic twin of `rule_costs`.
    pub fn empty_match_skips(&self) -> Vec<(String, u64)> {
        let mut out: Vec<(String, u64)> = self
            .empty_match_skips
            .iter()
            .enumerate()
            .filter(|(i, &n)| n > 0 && *i < self.rules.len())
            .map(|(i, &n)| (self.interner.resolve(self.rules[i].name).to_string(), n))
            .collect();
        out.sort();
        out
    }

    pub fn reset_empty_match_skips(&mut self) {
        for v in self.empty_match_skips.iter_mut() {
            *v = 0;
        }
    }

    /// Read-only introspection: which ACTIVE rules are provably empty RIGHT NOW,
    /// as `(name, area, the zero-population edge type that proves it)`. Used by
    /// the gate and the measurement harness to pin WHICH rules the proof
    /// reaches. Evaluates the predicate independently of the flag.
    pub fn provably_empty_rules(&self) -> Vec<(String, String, String)> {
        let mut out: Vec<(String, String, String)> = self
            .rules
            .iter()
            .filter(|r| r.active && !r.match_edges.is_empty())
            .filter_map(|r| {
                r.match_edges
                    .iter()
                    .find(|me| self.graph.edges_by_type(me.edge_type).is_empty())
                    .map(|me| {
                        (
                            self.interner.resolve(r.name).to_string(),
                            self.interner.resolve(r.area).to_string(),
                            self.interner.resolve(me.edge_type).to_string(),
                        )
                    })
            })
            .collect();
        out.sort();
        out
    }

    /// Record one skipped enumeration. Telemetry only.
    #[inline]
    fn note_empty_match_skip(&mut self, rule_idx: usize) {
        if self.empty_match_skips.len() <= rule_idx {
            self.empty_match_skips.resize(rule_idx + 1, 0);
        }
        self.empty_match_skips[rule_idx] += 1;
    }

    /// Read-only introspection: every ACTIVE rule for which binding projection
    /// is admissible, as `(name, area, projected vars)`. Diagnostic only.
    pub fn projectable_rules(&self) -> Vec<(String, String, Vec<String>)> {
        let mut out: Vec<(String, String, Vec<String>)> = self
            .rules
            .iter()
            .filter(|r| r.active)
            .filter_map(|r| {
                r.project_vars.as_ref().map(|pv| {
                    (
                        self.interner.resolve(r.name).to_string(),
                        self.interner.resolve(r.area).to_string(),
                        pv.iter()
                            .map(|s| self.interner.resolve(*s).to_string())
                            .collect(),
                    )
                })
            })
            .collect();
        out.sort();
        out
    }

    /// The dedup key for one binding: the FULL binding normally, the projection
    /// to `project_vars` when `binding_projection` is on and the rule qualifies.
    /// Sorted by `Sym`, exactly as the committed canonical key is.
    #[inline]
    fn binding_key(
        &self,
        rule: &crate::rewrite::RewriteRule,
        b: &crate::rewrite::Binding,
    ) -> smallvec::SmallVec<[(Sym, NodeID); 8]> {
        let mut canon: smallvec::SmallVec<[(Sym, NodeID); 8]> =
            match (self.binding_projection, &rule.project_vars) {
                (true, Some(pv)) if self.projection_overaggressive => {
                    let _ = pv;
                    smallvec::SmallVec::new()
                }
                (true, Some(pv)) => b
                    .iter()
                    .filter(|(s, _)| pv.contains(s))
                    .map(|(s, n)| (*s, *n))
                    .collect(),
                _ => b.iter().map(|(s, n)| (*s, *n)).collect(),
            };
        canon.sort_by_key(|(s, _)| *s);
        canon
    }

    /// Is the projected COLD-path enumeration admissible for this rule?
    /// Restricted to ONE match edge: with k == 1 every binding's variables come
    /// from the driving edge alone, so the where-clause can be stripped for the
    /// enumeration pass without any risk of a cross-product blow-up (which is
    /// exactly what stripping a pruning where-clause off a k-edge join would
    /// cause). Multi-edge rules keep the committed enumeration and only get the
    /// post-match dedup.
    #[inline]
    fn projection_cold_path(&self, rule: &crate::rewrite::RewriteRule) -> bool {
        self.binding_projection && rule.project_vars.is_some() && rule.match_edges.len() == 1
    }
    pub fn dirty_marks(&self) -> [u64; 9] {
        self.dirty_marks
    }
    pub fn reset_dirty_marks(&mut self) {
        self.dirty_marks = [0; 9];
    }
    /// How many ACTIVE rules currently hold a dirty bit — the residual the next
    /// settlement event will face. Read-only introspection.
    pub fn dirty_rule_count(&self) -> usize {
        self.rule_dirty
            .iter()
            .enumerate()
            .filter(|(i, d)| **d && self.rules[*i].active)
            .count()
    }
    /// `(rule name, area)` for every ACTIVE rule currently holding a dirty bit —
    /// so a diagnosis can name WHICH rule keeps an area awake, instead of
    /// reporting a count.
    pub fn dirty_rule_names(&self) -> Vec<(String, String)> {
        self.rules
            .iter()
            .enumerate()
            .filter(|(i, r)| r.active && self.rule_dirty[*i])
            .map(|(_, r)| {
                (
                    self.interner.resolve(r.name).to_string(),
                    if r.area == Sym::default() {
                        "global".to_string()
                    } else {
                        self.interner.resolve(r.area).to_string()
                    },
                )
            })
            .collect()
    }

    /// DIAGNOSTIC ONLY (block 187000): mark EVERY rule dirty and invalidate
    /// every cursor — the maximally conservative wake. Used to PROVE a run that
    /// used a precise dirty path still landed on a genuine fixpoint of the WHOLE
    /// rule system: force everything dirty, run the committed loop, and it must
    /// make ZERO progress. A missed wake would show up here as progress.
    pub fn force_all_dirty(&mut self) {
        for d in self.rule_dirty.iter_mut() {
            *d = true;
        }
        for c in self.rule_cursors.iter_mut() {
            c.clear();
        }
        self.edge_delete_version += 1;
        self.any_mutation = true;
    }

    /// Every ACTIVE rule whose `read_set` contains `Attr(key)`, with its area —
    /// read-only introspection so a diagnosis can NAME the attribute that keeps
    /// an area awake instead of inferring it.
    pub fn rules_reading_attr(&self, key: Sym) -> Vec<(String, String)> {
        self.rules
            .iter()
            .filter(|r| r.active && r.read_set.contains(&crate::rewrite::RuleKey::Attr(key)))
            .map(|r| {
                (
                    self.interner.resolve(r.name).to_string(),
                    if r.area == Sym::default() {
                        "global".to_string()
                    } else {
                        self.interner.resolve(r.area).to_string()
                    },
                )
            })
            .collect()
    }

    /// The set of AREAS holding at least one dirty active rule, in canonical
    /// `area_groups` order. The per-tick "how much of the cortex woke" number.
    pub fn dirty_area_names(&self) -> Vec<String> {
        self.area_groups()
            .into_iter()
            .filter(|(_, idxs)| idxs.iter().any(|&i| self.rule_dirty[i]))
            .map(|(a, _)| self.interner.resolve(a).to_string())
            .collect()
    }

    /// slice (b): after rule `fired` progressed, dirty ONLY the rules whose
    /// read_set intersects `fired`'s write_set — the precise replacement for
    /// the blanket "re-dirty everything". A `writes_any` rule (DelNode/
    /// ReplaceValue/DefineConcept) still fans out to all. Read/write sets are
    /// over-approx supersets (derive_access), so this dirties a superset of the
    /// true consumers — never misses a firing, just wakes fewer rules.
    fn dirty_by_writeset(&mut self, fired: usize) {
        if self.rules[fired].writes_any {
            if self.dirty_telemetry {
                let n = self.rule_dirty.iter().filter(|d| !**d).count() as u64;
                self.dirty_marks[0] += self.rule_dirty.len() as u64;
                self.dirty_marks[6] += n;
            }
            for d in self.rule_dirty.iter_mut() {
                *d = true;
            }
            // An imprecise (writes_any) effect may flip where-clauses on ALREADY-matched edges. The
            // semi-naive cursor only re-scans NEW edges, so invalidate every cursor to force a full
            // re-match — the same correctness guarantee mark_node_mutation gives external writes.
            for c in self.rule_cursors.iter_mut() {
                c.clear();
            }
            self.graph.attr_write_log.clear(); // block 292000: blanket path takes no frontier
            self.graph.edge_write_log.clear();
            return;
        }
        let wset: smallvec::SmallVec<[crate::rewrite::RuleKey; 16]> =
            self.rules[fired].write_set.iter().copied().collect();
        if wset.is_empty() {
            self.graph.attr_write_log.clear();
            self.graph.edge_write_log.clear();
            return;
        }
        for j in 0..self.rules.len() {
            // FIXPOINT-SETTLE FIX. There used to be an
            // `if self.rule_dirty[j] { continue; }` early-out here. It was
            // WRONG, and it made `run_rules` return over unsettled state —
            // see `run_rules_returns_over_unsettled_state_when_attr_write_follows_structural_dirty`.
            //
            // Dirtying a consumer and INVALIDATING ITS CURSOR are two
            // DISTINCT obligations; the early-out discharged only the first.
            // A STRUCTURAL (Edge) write correctly dirties a consumer while
            // LEAVING its semi-naive cursor intact — new edges drive the
            // rescan, so nothing is missed. But if an ATTR write to the same
            // consumer then happens LATER IN THE SAME PASS, the consumer is
            // already dirty, so it was skipped and its cursor was never
            // cleared. It was then tried on the incremental path with a
            // VALID cursor and ZERO new driving edges, enumerated nothing,
            // and could not observe the attribute flip on its stable edges.
            // Every rule reported no progress, `!any_progress` fired, and the
            // engine declared a fixed point over a graph that had not settled.
            //
            // The dirty bit is idempotent (setting it twice is free), so
            // running the intersection unconditionally is correct; the cost
            // is the read_set intersection for consumers already scheduled.
            // `mark_node_mutation`'s blanket cursor-clear was always the
            // stronger guarantee — this brings the rule-effect path in line.
            // `MatchEdge` is purely STRUCTURAL ({src_var, edge_type, tgt_var} — no attr
            // constraints), so an attr VALUE can only change which bindings a rule produces
            // THROUGH A WHERE-CLAUSE. A where-LESS rule's attr reads are effect-only (they
            // compute an emitted value), never a match determinant — re-firing its unchanged
            // bindings on an attr write only DUPLICATES effects (the 300-patch bug). So an
            // Attr-key intersection dirties consumer `j` only when it has a where-clause (or
            // reads_any). Edge/Type writes are STRUCTURAL and dirty unconditionally. A new edge
            // used as a match-edge driver can advance the semi-naive cursor; an edge read by a
            // term may also change outputs for EXISTING bindings, so that cursor must be cleared.
            let has_where = self.rule_has_where[j];
            let rj = &self.rules[j];
            let hits_structural = wset.iter().any(|k| {
                rj.read_set.contains(k)
                    && matches!(
                        k,
                        crate::rewrite::RuleKey::Edge(_) | crate::rewrite::RuleKey::Type(_)
                    )
            });
            let hits_attr = wset
                .iter()
                .any(|k| rj.read_set.contains(k) && matches!(k, crate::rewrite::RuleKey::Attr(_)));
            let hits_term_edge = wset.iter().any(|k| match k {
                crate::rewrite::RuleKey::Edge(edge_type) => {
                    rj.term_edge_reads.contains(edge_type)
                }
                crate::rewrite::RuleKey::Attr(_) | crate::rewrite::RuleKey::Type(_) => false,
            });
            if rj.reads_any || hits_structural || (hits_attr && has_where) {
                // Attr/type changes can flip a where-clause on a stable match;
                // typed edge terms can change computed outputs or predicates on
                // stable bindings even without a where-clause. Those paths need
                // a full rematch. A new edge used ONLY as a match-edge driver is
                // handled incrementally by the cursor and keeps the fast path.
                let type_hit = wset.iter().any(|k| {
                    rj.read_set.contains(k) && matches!(k, crate::rewrite::RuleKey::Type(_))
                });
                let (type_hit, hits_attr, hits_term_edge) = if self.own_write_exempt {
                    // own-write exemption: only where / computed-arg reads can
                    // flip an existing binding (see the field doc)
                    (
                        wset.iter().any(|k| {
                            rj.read_set_strict.contains(k)
                                && matches!(k, crate::rewrite::RuleKey::Type(_))
                        }),
                        wset.iter().any(|k| {
                            rj.read_set_strict.contains(k)
                                && matches!(k, crate::rewrite::RuleKey::Attr(_))
                        }),
                        wset.iter().any(|k| match k {
                            crate::rewrite::RuleKey::Edge(et) => rj.term_edge_reads_strict.contains(et),
                            _ => false,
                        }),
                    )
                } else {
                    (type_hit, hits_attr, hits_term_edge)
                };
                let invalidate_cursor =
                    rj.reads_any || type_hit || (hits_attr && has_where) || hits_term_edge;
                if self.dirty_telemetry {
                    self.dirty_marks[0] += 1;
                    if !self.rule_dirty[j] {
                        self.dirty_marks[6] += 1;
                    }
                }
                self.rule_dirty[j] = true;
                if invalidate_cursor {
                    // block 292000: a PURE attr flip (no structural/type/reads_any change)
                    // on a predicate-retraction-eligible consumer seeds the rung-B frontier
                    // from the rule-effect attr writes (Edit A's log) and KEEPS the cursor —
                    // the exact move mark_node_predicate_dirty makes for external writes, so
                    // try_predicate_retraction re-evaluates only the frontier. Everything else
                    // (structural/type/reads_any/ineligible/flag-off) keeps the committed
                    // cursor-clear ⇒ byte-identical on the default path.
                    let pure_attr_flip = hits_attr
                        && has_where
                        && !type_hit
                        && !rj.reads_any
                        && !hits_term_edge;
                    let covered = self.predicate_retraction
                        && pure_attr_flip
                        && self.rule_pred_retract_ok.get(j).copied().unwrap_or(false);
                    let wf = !covered
                        && self.write_frontier
                        && rj.wf_ok
                        && !type_hit
                        && wset.iter().all(|k| match k {
                            crate::rewrite::RuleKey::Edge(et) => {
                                !rj.term_edge_reads_strict.contains(et)
                                    || rj.wf_local_out.contains(et)
                                    || rj.wf_local_in.contains(et)
                            }
                            _ => true,
                        })
                        && !(rj.reads_any
                            && wset.iter().any(|k| matches!(k, crate::rewrite::RuleKey::Type(_))))
                        && !wset.iter().any(|k| {
                            matches!(k, crate::rewrite::RuleKey::Attr(a) if rj.wf_nonlocal_keys.contains(a))
                        });
                    if covered {
                        if j >= self.rule_dirty_nodes.len() {
                            self.rule_dirty_nodes
                                .resize(self.rules.len(), Default::default());
                        }
                        for &(nid, wkey) in self.graph.attr_write_log.iter() {
                            if rj.read_set.contains(&crate::rewrite::RuleKey::Attr(wkey)) {
                                self.rule_dirty_nodes[j].insert(nid);
                            }
                        }
                    } else if wf {
                        // write frontier: every attr this write can flip lives on a
                        // node the binding binds -- seed those nodes, keep the cursor
                        if j >= self.rule_dirty_nodes.len() {
                            self.rule_dirty_nodes
                                .resize(self.rules.len(), Default::default());
                        }
                        if j >= self.rule_dirty_dyn_nodes.len() {
                            self.rule_dirty_dyn_nodes
                                .resize(self.rules.len(), Default::default());
                        }
                        let dyn_local = rj.wf_dyn_local;
                        for &(nid, wkey) in self.graph.attr_write_log.iter() {
                            if rj.read_set_strict.contains(&crate::rewrite::RuleKey::Attr(wkey)) {
                                self.rule_dirty_nodes[j].insert(nid);
                            } else if dyn_local {
                                self.rule_dirty_dyn_nodes[j].insert(nid);
                            }
                        }
                        // a new edge read only as Neighbours / InNeighbours of a
                        // bound variable can flip only bindings of its src / tgt
                        for &(es, et, eto) in self.graph.edge_write_log.iter() {
                            if rj.wf_local_out.contains(&et) {
                                self.rule_dirty_nodes[j].insert(es);
                            }
                            if rj.wf_local_in.contains(&et) {
                                self.rule_dirty_nodes[j].insert(eto);
                            }
                        }
                        // hop frontier: a one-hop local attr read flips only the
                        // bindings of the written node's E-neighbours
                        if self.hop_frontier && !rj.wf_hop.is_empty() {
                            for &(nid, wkey) in self.graph.attr_write_log.iter() {
                                for &(k, et, out) in rj.wf_hop.iter() {
                                    if k != wkey || !self.graph.has_node(nid) {
                                        continue;
                                    }
                                    if out {
                                        for &ei in self.graph.in_edges_slice(nid, Some(et)) {
                                            self.rule_dirty_nodes[j].insert(self.graph.edge(ei).src);
                                        }
                                    } else {
                                        for &ei in self.graph.out_edges_slice(nid, Some(et)) {
                                            self.rule_dirty_nodes[j].insert(self.graph.edge(ei).tgt);
                                        }
                                    }
                                }
                            }
                        }
                    } else {
                        self.rule_cursors[j].clear();
                    }
                }
            }
        }
        // block 292000: drain the per-fire rule-effect attr-write log. Empty when
        // predicate_retraction is off (nothing was pushed) ⇒ no-op, byte/cost-identical.
        self.graph.attr_write_log.clear();
        self.graph.edge_write_log.clear();
    }

    // --- extend ---

    pub fn add_node(&mut self, type_: Sym, attrs: FxHashMap<Sym, Value>) -> NodeID {
        self.counters.on_node_inserted(type_);
        // 187000: capture the written keys BEFORE `attrs` is moved, and only
        // when the precise path will consume them (the default path pays zero).
        let keys: smallvec::SmallVec<[Sym; 16]> = if self.precise_dirty {
            attrs.keys().copied().collect()
        } else {
            smallvec::SmallVec::new()
        };
        let nid = self.graph.insert_node(type_, attrs);
        if self.precise_dirty && self.fresh_node_exempt {
            // fresh node: no edges, so its attrs are unobservable to any existing
            // binding; only a type enumeration can see it (see the field doc)
            self.mark_isolated_write(type_);
        } else if self.precise_dirty {
            self.mark_external_write(Some(type_), &keys);
        } else {
            self.mark_node_mutation();
        }
        nid
    }

    pub fn add_edge(
        &mut self,
        src: NodeID,
        edge_type: Sym,
        tgt: NodeID,
        attrs: FxHashMap<Sym, Value>,
    ) -> Result<EdgeIdx, InadmissibleEdge> {
        self.counters.on_admissibility_check();
        match self.checker.check_edge(
            &self.graph,
            &self.interner,
            &self.terms,
            Some(&self.concepts),
            src,
            edge_type,
            tgt,
        ) {
            CheckOutcome::Admitted(prods) => {
                for p in &prods {
                    self.counters.on_production_admit(*p);
                }
                self.counters.on_edge_inserted(edge_type);
                let result = self
                    .graph
                    .insert_edge(src, edge_type, tgt, attrs)
                    .expect("admitted edge must connect existing nodes");
                self.mark_edge_type_dirty(edge_type);
                self.graph.edge_write_log.clear(); // external write: the log is rule-effect only
                if self.fresh_node_exempt {
                    self.invalidate_term_readers_of_edge_type(edge_type, src, tgt);
                }
                Ok(result)
            }
            CheckOutcome::Type1NoProduction {
                src_type,
                edge_type,
                tgt_type,
            } => {
                self.counters.on_rejection_type1();
                // Charge a reject to every candidate that failed its
                // where-clause (the candidates exist by definition of
                // Type-1 — vocabulary present but no admission).
                for pi in self
                    .checker
                    .grammar
                    .candidates(src_type, edge_type, tgt_type)
                {
                    self.counters.on_production_reject(*pi);
                }
                // GAMMA_COLLAPSE_ALGORITHM spike (see field doc on
                // `gamma_residual_capture`): DEFAULT FALSE, byte-identical
                // to the committed path when off. On, this is the ONE
                // place the previously-discarded rejection triple is
                // captured as graph data instead of being thrown away the
                // instant this `Err` is constructed.
                if self.gamma_residual_capture {
                    self.record_gamma_residual(src_type, edge_type, tgt_type);
                }
                Err(InadmissibleEdge::Type1NoProduction {
                    src_type,
                    edge_type,
                    tgt_type,
                })
            }
            CheckOutcome::Type2VocabAbsent { missing } => {
                self.counters.on_rejection_type2();
                Err(InadmissibleEdge::Type2VocabAbsent { missing })
            }
        }
    }

    // --- transform ---

    pub fn remove_edge(&mut self, key: EdgeKey) -> bool {
        if let Some(idx) = self.graph.edge_idx(key.src, key.edge_type, key.tgt) {
            let ok = self.graph.delete_edge(idx).is_some();
            if ok {
                self.edge_delete_version += 1;
                self.mark_edge_type_dirty(key.edge_type);
                self.invalidate_readers_of_deleted_edge_type(key.edge_type);
            }
            ok
        } else {
            false
        }
    }

    /// Remove several edges while compacting each affected graph index once.
    /// Result positions correspond to input keys; duplicate keys therefore
    /// report true only for their first occurrence, matching sequential
    /// `remove_edge` calls.
    pub fn remove_edges_batch(&mut self, keys: &[EdgeKey]) -> Vec<bool> {
        let mut removed_once = FxHashSet::default();
        let mut indices = Vec::with_capacity(keys.len());
        let mut outcomes = vec![false; keys.len()];
        for (position, key) in keys.iter().enumerate() {
            if let Some(idx) = self.graph.edge_idx(key.src, key.edge_type, key.tgt) {
                if removed_once.insert(idx) {
                    outcomes[position] = true;
                    indices.push(idx);
                }
            }
        }
        let removed = self.graph.delete_edges_batch(&indices);
        if removed.is_empty() {
            return outcomes;
        }
        self.edge_delete_version += removed.len() as u64;
        let mut affected_types = FxHashSet::default();
        for edge in removed {
            affected_types.insert(edge.edge_type);
        }
        for edge_type in affected_types {
            self.mark_edge_type_dirty(edge_type);
            self.invalidate_readers_of_deleted_edge_type(edge_type);
        }
        outcomes
    }

    pub fn remove_node(&mut self, nid: NodeID) -> bool {
        let had_edges = !self.graph.out_edges_slice(nid, None).is_empty()
            || !self.graph.in_edges_slice(nid, None).is_empty();
        // 187000: a DELETION must never be under-approximated. Snapshot the
        // incident edge types in every mode so deleting a node has the same
        // edge-reader invalidation contract as deleting those edges one by
        // one. Precise mode additionally snapshots node type/attribute keys.
        let edge_types: smallvec::SmallVec<[Sym; 8]> = if self.graph.has_node(nid) {
            let mut ets: smallvec::SmallVec<[Sym; 8]> = smallvec::SmallVec::new();
            for idx in self
                .graph
                .out_edges_slice(nid, None)
                .iter()
                .chain(self.graph.in_edges_slice(nid, None).iter())
            {
                let et = self.graph.edge(*idx).edge_type;
                if !ets.contains(&et) {
                    ets.push(et);
                }
            }
            ets
        } else {
            smallvec::SmallVec::new()
        };
        let (ty, keys): (Option<Sym>, smallvec::SmallVec<[Sym; 16]>) =
            if self.precise_dirty && self.graph.has_node(nid) {
            let n = self.graph.node(nid);
            (Some(n.type_), n.attrs.iter().map(|(k, _)| *k).collect())
        } else {
            (None, smallvec::SmallVec::new())
        };
        let precise = self.precise_dirty;
        let ok = self.graph.delete_node(nid).is_some();
        if ok {
            if had_edges {
                self.edge_delete_version += 1;
            }
            for et in edge_types {
                self.mark_edge_type_dirty(et);
                self.invalidate_readers_of_deleted_edge_type(et);
            }
            if precise {
                self.mark_external_write(ty, &keys);
            } else {
                self.mark_node_mutation();
            }
        }
        ok
    }

    /// Remove a reflected Term tree while preserving descendants that have
    /// incoming references from outside that tree. Ordinary `remove_node`
    /// remains node-only. Traversal and cycle/type validation complete before
    /// mutation, so malformed child structure fails without partial deletion.
    pub fn remove_term_subgraph(
        &mut self,
        root: NodeID,
    ) -> Result<TermSubgraphRemoval, String> {
        const TERM_PREFIX: &str = "Term.";
        const CHILD_PREFIX: &str = "child.";

        if !self.graph.has_node(root) {
            return Err("term_subgraph_root_missing".to_string());
        }

        let is_term = |this: &Self, nid: NodeID| {
            this.interner
                .resolve(this.graph.node(nid).type_)
                .starts_with(TERM_PREFIX)
        };
        if !is_term(self, root) {
            return Err("term_subgraph_root_not_term".to_string());
        }

        // Iterative DFS builds a post-order deletion list and rejects cycles
        // or child edges that escape the reflected Term vocabulary before any
        // graph mutation occurs.
        let mut color: rustc_hash::FxHashMap<NodeID, u8> = Default::default();
        let mut children: rustc_hash::FxHashMap<NodeID, Vec<NodeID>> = Default::default();
        let mut postorder = Vec::new();
        let mut stack = vec![(root, false)];
        while let Some((nid, expanded)) = stack.pop() {
            if expanded {
                color.insert(nid, 2);
                postorder.push(nid);
                continue;
            }
            match color.get(&nid).copied() {
                Some(1) => return Err("term_subgraph_child_cycle".to_string()),
                Some(2) => continue,
                _ => {}
            }
            if !self.graph.has_node(nid) || !is_term(self, nid) {
                return Err("term_subgraph_child_not_term".to_string());
            }
            color.insert(nid, 1);
            stack.push((nid, true));
            let edge_ids = self.graph.out_edges_slice(nid, None).to_vec();
            for edge_idx in edge_ids.into_iter().rev() {
                let edge = self.graph.edge(edge_idx);
                if self.interner.resolve(edge.edge_type).starts_with(CHILD_PREFIX) {
                    if !self.graph.has_node(edge.tgt) || !is_term(self, edge.tgt) {
                        return Err("term_subgraph_child_not_term".to_string());
                    }
                    children.entry(nid).or_default().push(edge.tgt);
                    stack.push((edge.tgt, false));
                }
            }
        }

        let owned: rustc_hash::FxHashSet<NodeID> = color.keys().copied().collect();
        let mut protected: rustc_hash::FxHashSet<NodeID> = Default::default();
        let mut protect_stack = Vec::new();
        for nid in owned.iter().copied() {
            for edge_idx in self.graph.in_edges_slice(nid, None) {
                let source = self.graph.edge(*edge_idx).src;
                if !owned.contains(&source) {
                    protect_stack.push(nid);
                    break;
                }
            }
        }
        while let Some(nid) = protect_stack.pop() {
            if !protected.insert(nid) {
                continue;
            }
            if let Some(descendants) = children.get(&nid) {
                protect_stack.extend(descendants.iter().copied());
            }
        }

        let mut report = TermSubgraphRemoval::default();
        report.protected = postorder
            .iter()
            .copied()
            .filter(|nid| protected.contains(nid))
            .collect();
        for nid in postorder {
            if protected.contains(&nid) {
                continue;
            }
            let former_type = self.graph.node(nid).type_;
            if self.remove_node(nid) {
                report.removed.push((nid, former_type));
            }
        }
        Ok(report)
    }

    pub fn set_attr(&mut self, nid: NodeID, key: Sym, value: Value) {
        // 187000, VALUE-LEVEL: a write that does not change the stored value
        // leaves the graph BIT-IDENTICAL — `set_node_attr` re-inserts the same
        // value and removes-then-re-adds the same attr-index bucket entry — so
        // no rule's bindings and no where-clause's truth can change, and running
        // its consumers would be a GENUINE NO-OP. Skipping it is therefore not a
        // deferral (nothing is frozen; 185000's Branch B froze an adapted floor
        // and manufactured onsets — this freezes nothing).
        if (self.precise_dirty || self.dirty_telemetry) && self.graph.has_node(nid) {
            let old = self.graph.node(nid).attrs.get(&key);
            let mut unchanged = old == Some(&value);
            if self.dirty_overaggressive && !unchanged {
                // THE FALSIFIER'S SECOND HALF, and the point of it: the
                // TEMPTING wrong version of the no-op rule — "the value barely
                // moved, call it settled". This is EXACTLY 185000's Branch-B
                // failure shape (a receptor deferred against a frozen reference
                // manufactured onsets, carve precision 0.978 -> 0.0). A skip is
                // admissible ONLY when re-running would be a genuine no-op, and
                // "within 1e-9" is not that. It MUST break byte-identity.
                if let (Some(Value::Float(a)), Value::Float(b)) = (old, &value) {
                    unchanged = (a - b).abs() < 1e-9;
                }
            }
            if self.dirty_telemetry {
                self.dirty_marks[3] += 1;
                if unchanged {
                    self.dirty_marks[4] += 1;
                }
            }
            if unchanged && self.precise_dirty {
                return;
            }
        }
        if self.precise_dirty && self.fresh_node_exempt && self.graph.has_node(nid)
            && self.graph.out_edges_slice(nid, None).is_empty()
            && self.graph.in_edges_slice(nid, None).is_empty()
        {
            let ty = self.graph.node(nid).type_;
            self.graph.set_node_attr(nid, key, value);
            if self.write_frontier && !self.predicate_retraction {
                self.graph.attr_write_log.clear(); // external write: the log is rule-effect only
            }
            self.mark_isolated_write(ty);
            return;
        }
        self.graph.set_node_attr(nid, key, value);
        if self.write_frontier && !self.predicate_retraction {
            self.graph.attr_write_log.clear(); // external write: the log is rule-effect only
        }
        // PREDICATE RETRACTION (block 194000): an external attr write records
        // the written node against the covered where-rules that read this key
        // (node-seeded re-eval next visit) instead of clearing their whole
        // cursor. Uncovered where-rules keep the committed precise fallback
        // (cursor clear → full rescan), byte-identical to `mark_external_write`.
        if self.predicate_retraction {
            self.mark_node_predicate_dirty(nid, key);
            return;
        }
        if self.precise_dirty {
            self.mark_external_write(None, &[key]);
        } else {
            self.mark_node_mutation();
        }
    }

    /// Block 194000. The predicate-retraction twin of `mark_external_write` for
    /// an EXTERNAL attr write of `key` to node `nid`. Byte-identical to
    /// `mark_external_write(None, &[key])` for every UNCOVERED where-rule
    /// (dirty + cursor clear → full rescan), and for a COVERED where-rule
    /// (`rule_pred_retract_ok`) it instead records `nid` and KEEPS the cursor,
    /// so the rule's next attempt re-evaluates only the bindings that touch the
    /// written node. It bumps NO global version (no edge was deleted) — the
    /// per-type cursor version is unchanged, which is exactly what lets a
    /// covered rule stay on the node-seeded path across a pure attr flip.
    fn mark_node_predicate_dirty(&mut self, nid: NodeID, key: Sym) {
        self.any_mutation = true;
        for j in 0..self.rules.len() {
            let has_where = self.rule_has_where[j];
            let (reads_any, attr_hit) = {
                let rj = &self.rules[j];
                (
                    rj.reads_any,
                    rj.read_set.contains(&crate::rewrite::RuleKey::Attr(key)),
                )
            };
            if !(reads_any || (attr_hit && has_where)) {
                continue;
            }
            self.rule_dirty[j] = true;
            let covered = self.rule_pred_retract_ok.get(j).copied().unwrap_or(false) && !reads_any; // a reads_any rule cannot be node-scoped soundly
            if covered {
                if j >= self.rule_dirty_nodes.len() {
                    self.rule_dirty_nodes
                        .resize(self.rules.len(), Default::default());
                }
                self.rule_dirty_nodes[j].insert(nid);
                // KEEP the cursor: no edge changed, so the node-seeded path
                // (not the new-edges cursor) is what re-checks the flip.
            } else {
                self.rule_cursors[j].clear();
            }
        }
    }

    pub fn set_type(&mut self, nid: NodeID, new_type: Sym) {
        let old_type = if self.precise_dirty && self.graph.has_node(nid) {
            Some(self.graph.node(nid).type_)
        } else {
            None
        };
        self.graph.set_node_type(nid, new_type);
        if self.precise_dirty {
            // A retype changes membership of BOTH type buckets; wake readers of
            // each. Structural, so unconditional (no where-clause requirement).
            if let Some(t) = old_type {
                if t != new_type {
                    self.mark_external_write(Some(t), &[]);
                }
            }
            self.mark_external_write(Some(new_type), &[]);
        } else {
            self.mark_node_mutation();
        }
    }

    /// Buffered mutation. The closure receives a `Transaction`; if it
    /// returns `Err`, everything the transaction added is rolled back
    /// in LIFO order. On `Ok` the buffered mutations are kept (they
    /// were already applied to the graph — Π just records them so it
    /// can undo).
    pub fn transform<F, E, R>(&mut self, f: F) -> Result<R, E>
    where
        F: FnOnce(&mut Transaction<'_>) -> Result<R, E>,
        E: From<InadmissibleEdge>,
    {
        let mut tx = Transaction {
            substrate: self,
            inserted_nodes: Vec::new(),
            inserted_edges: Vec::new(),
            committed: false,
        };
        match f(&mut tx) {
            Ok(r) => {
                tx.committed = true;
                Ok(r)
            }
            Err(e) => {
                tx.rollback();
                Err(e)
            }
        }
    }

    // --- probes / queries ---

    /// Probe: would an edge from `src` to a freshly-materialised node
    /// of `(candidate_tgt_type, candidate_tgt_attrs)` be admissible
    /// under the current Γ?
    ///
    /// Fast path: if no matching production's where-clause references
    /// the tgt binding, evaluate where-clauses with only src bound and
    /// avoid materialising a scratch tgt. This is the same fast path
    /// the Python `is_edge_admissible` runs via `collect_vars`.
    pub fn is_edge_admissible(
        &mut self,
        src: NodeID,
        edge_type: Sym,
        candidate_tgt_type: Sym,
        candidate_tgt_attrs: FxHashMap<Sym, Value>,
    ) -> bool {
        let src_type = self.graph.node(src).type_;
        let cand = self
            .checker
            .grammar
            .candidates(src_type, edge_type, candidate_tgt_type);
        if cand.is_empty() {
            return false;
        }

        // Snapshot the candidate productions' relevant info so we can
        // release the borrow and try the scratch-tgt path if needed.
        let prod_indexes: SmallVec<[ProdIdx; 4]> = cand.iter().copied().collect();
        let all_tgt_unreferenced = prod_indexes.iter().all(|pi| {
            let prod = &self.checker.grammar.productions[pi.0 as usize];
            match prod.where_ {
                None => true,
                Some(w) => !free_vars(&self.terms, w, None).contains(&prod.tgt.var),
            }
        });

        if all_tgt_unreferenced {
            // No scratch needed: evaluate each where-clause with only
            // src bound. Substitute Value::None for the (unreferenced)
            // tgt var to keep the env shape constant.
            for pi in prod_indexes.iter() {
                let prod = &self.checker.grammar.productions[pi.0 as usize];
                let dummy_tgt = src; // never used since tgt var unreferenced
                if production_admits(
                    prod,
                    src,
                    dummy_tgt,
                    &self.graph,
                    &self.interner,
                    &self.terms,
                    Some(&self.concepts),
                ) {
                    return true;
                }
            }
            return false;
        }

        // Slow path: materialise a scratch node, run the full check,
        // remove it. Matches Python's `_insert_node`-then-delete probe.
        let scratch = self
            .graph
            .insert_node(candidate_tgt_type, candidate_tgt_attrs);
        let result = self.checker.check_edge(
            &self.graph,
            &self.interner,
            &self.terms,
            Some(&self.concepts),
            src,
            edge_type,
            scratch,
        );
        self.graph.delete_node(scratch);
        result.admits()
    }

    /// Filter `candidates` to tgt nodes for which `(src, edge_type, tgt)`
    /// is admissible.
    pub fn admissible_edges_from(
        &self,
        src: NodeID,
        edge_type: Sym,
        candidates: impl IntoIterator<Item = NodeID>,
    ) -> Vec<NodeID> {
        candidates
            .into_iter()
            .filter(|&tgt| {
                self.checker
                    .check_edge(
                        &self.graph,
                        &self.interner,
                        &self.terms,
                        Some(&self.concepts),
                        src,
                        edge_type,
                        tgt,
                    )
                    .admits()
            })
            .collect()
    }

    /// Enumerate (tgt_type, attrs, weight_total) candidates that admit
    /// under at least one production. Materialises a scratch tgt for
    /// each candidate so where-clauses + weight Terms that reference
    /// tgt attrs work; the scratch is removed before returning.
    ///
    /// Weight semantics match Paper §1.2 Definition 2: per-production
    /// weights add (the Python's `admissible_moves` did the same —
    /// "multiple matching productions contribute their weights
    /// additively"). The caller picks via softmax over these weights
    /// if it wants the Boltzmann selection of Theorem D.
    pub fn admissible_moves(
        &mut self,
        src: NodeID,
        edge_type: Sym,
        candidates: impl IntoIterator<Item = (Sym, crate::graph::Attrs)>,
    ) -> Vec<(Sym, crate::graph::Attrs, f64)> {
        let src_type = self.graph.node(src).type_;
        let mut out = Vec::new();
        for (tgt_type, tgt_attrs) in candidates {
            let scratch = self.graph.insert_node(tgt_type, tgt_attrs.clone());
            let mut total = 0.0;
            let mut admitted = false;
            let cand_indexes: SmallVec<[ProdIdx; 4]> = self
                .checker
                .grammar
                .candidates(src_type, edge_type, tgt_type)
                .iter()
                .copied()
                .collect();
            for pi in cand_indexes {
                let prod = &self.checker.grammar.productions[pi.0 as usize];
                if production_admits(
                    prod,
                    src,
                    scratch,
                    &self.graph,
                    &self.interner,
                    &self.terms,
                    Some(&self.concepts),
                ) {
                    admitted = true;
                    total += evaluate_weight(
                        prod,
                        src,
                        scratch,
                        &self.graph,
                        &self.interner,
                        &self.terms,
                        Some(&self.concepts),
                    );
                }
            }
            self.graph.delete_node(scratch);
            if admitted {
                out.push((tgt_type, tgt_attrs, total));
            }
        }
        out
    }

    /// Convenience: register a concept Term for `Holds(concept, x)` to
    /// resolve. Maps directly to the Python `env['_resolve_concept']`
    /// callback.
    pub fn define_concept(&mut self, name: Sym, def: TermIdx) {
        if self.concepts.get(&name).copied() != Some(def) {
            self.concepts.insert(name, def);
            self.gamma_epoch.bump();
        }
    }

    /// Phase 7b: declare a secondary index on `(node_type, attr_key)`.
    /// Subsequent `NodesWhere(node_type, attr_key, value)` Terms hit
    /// it in O(1+result).
    pub fn declare_attr_index(&mut self, node_type: Sym, attr_key: Sym) {
        self.graph.declare_attr_index(node_type, attr_key);
    }

    /// Direct (non-DSL) indexed lookup. Mirror of `TypedGraph::nodes_where`.
    pub fn nodes_where(&self, node_type: Sym, attr_key: Sym, value: &Value) -> Vec<NodeID> {
        self.graph.nodes_where(node_type, attr_key, value)
    }

    // --- THE SALIENT-SHAPE EDGE (one relation among many) ---------------
    //
    // A memory/percept is a NODE held by MANY edges at once. The salient
    // order-N SHAPE is ONE of those relations — additive alongside the
    // graph's existing audio/video/lexicon/follows/... edges, NOT a single
    // cluster key. Two nodes that carry an order-N shape SIGNATURE become
    // `shares_shape` NEIGHBOURS when their signatures are close (the held
    // `shape_distance` over the gain-invariant rank key) — so an
    // accelerando-crescendo cartoon "tada" and Grieg's Mountain King are
    // linked by a REAL graph edge, across maximal surface difference. Recall
    // + analogy = SPREADING ACTIVATION across whichever edges a cue matches.

    /// Read a SalientShape node's stored signature back as `Vec<i64>`.
    /// The signature lives in the `signature` attr as a Tuple of Ints.
    fn read_shape_signature(&self, nid: NodeID) -> Option<Vec<i64>> {
        let sig_key = self.interner.lookup("signature")?;
        let v = self.graph.node(nid).attrs.get(&sig_key)?;
        match v {
            Value::Tuple(t) | Value::List(t) => Some(t.iter().map(|x| x.as_f64() as i64).collect()),
            _ => None,
        }
    }

    /// Declare the `shares_shape` production so the edge type is admissible
    /// in Γ: (SalientShape) -[shares_shape]-> (SalientShape). Idempotent-ish
    /// (adding the same production twice just adds a redundant candidate).
    /// This is ONE edge type added to the grammar — the existing edge types
    /// (audio/video/lexicon/follows/...) are untouched.
    pub fn declare_shares_shape(&mut self) {
        let shape_t = self.interner.intern("SalientShape");
        let edge_t = self.interner.intern("shares_shape");
        let src_var = self.interner.intern("a");
        let tgt_var = self.interner.intern("b");
        let weight = crate::grammar::Grammar::default_weight(&mut self.terms);
        let provenance = self
            .interner
            .intern("shares_shape (salient order-N shape neighbour)");
        let prod = crate::grammar::Production {
            src: crate::grammar::NodePattern {
                type_: shape_t,
                var: src_var,
            },
            edge_type: edge_t,
            tgt: crate::grammar::NodePattern {
                type_: shape_t,
                var: tgt_var,
            },
            where_: None,
            weight,
            provenance,
        };
        self.add_production(prod);
    }

    /// Add a SalientShape node carrying the order-N shape SIGNATURE of a
    /// clip/event (the held `shape_signature` over its pitch/rhythm
    /// trajectory), then WIRE `shares_shape` edges to every existing
    /// SalientShape node that is a shape-NEIGHBOUR (signature distance below
    /// the scale-derived threshold). This is a graph operation: the salient
    /// shape as ONE relation, added bidirectionally. Returns the new node id
    /// and the list of (neighbour, distance) it linked to.
    ///
    /// Linking is SELECTED, not all-to-all: only signatures of EQUAL length
    /// within `shape_neighbour_threshold(n)` are linked, so it cannot
    /// over-link a flat/unrelated control into the shape cluster.
    pub fn add_salient_shape(
        &mut self,
        label: &str,
        signature: &[i64],
    ) -> (NodeID, Vec<(NodeID, i64)>) {
        let shape_t = self.interner.intern("SalientShape");
        let label_key = self.interner.intern("label");
        let sig_key = self.interner.intern("signature");
        let len_key = self.interner.intern("sig_len");
        let label_sym = self.interner.intern(label);

        let mut attrs: FxHashMap<Sym, Value> = FxHashMap::default();
        attrs.insert(label_key, Value::Str(label_sym));
        let sig_tuple: smallvec::SmallVec<[Value; 4]> =
            signature.iter().map(|&x| Value::Int(x)).collect();
        attrs.insert(sig_key, Value::Tuple(std::sync::Arc::new(sig_tuple)));
        attrs.insert(len_key, Value::Int(signature.len() as i64));
        let new_id = self.add_node(shape_t, attrs);

        // Ensure the edge type is admissible (declare once; cheap if
        // already declared).
        if !self
            .checker
            .grammar
            .knows_edge_type(self.interner.intern("shares_shape"))
        {
            self.declare_shares_shape();
        }
        let edge_t = self.interner.intern("shares_shape");

        let thr = crate::memory::shape_neighbour_threshold(signature.len());
        let mut linked: Vec<(NodeID, i64)> = Vec::new();
        let existing = self.graph.nodes_of_type(shape_t);
        for other in existing {
            if other == new_id {
                continue;
            }
            let Some(other_sig) = self.read_shape_signature(other) else {
                continue;
            };
            let d = crate::memory::shape_distance(signature, &other_sig);
            if d < thr {
                // additive, bidirectional: a real graph edge both ways.
                let _ = self.add_edge(new_id, edge_t, other, FxHashMap::default());
                let _ = self.add_edge(other, edge_t, new_id, FxHashMap::default());
                linked.push((other, d));
            }
        }
        (new_id, linked)
    }

    // --- MULTI-RELATIONAL EDGES (timbre / affect / function) ------------
    //
    // The SAME SalientShape node is held by MANY relations at once: its
    // order-N SHAPE (shares_shape, above) is ONE; its TIMBRE (spectral-
    // envelope profile), its AFFECT (arousal/valence acoustic proxy), and
    // its FUNCTION (structural/narrative role) are three more. Each relation
    // gets its OWN per-node signature (stored under its own attr key, so a
    // node can carry all four), its OWN Γ-declared edge type, and its OWN
    // neighbour-linking by signature distance — but ALL reuse the held
    // ordinal-rank `shape_distance` metric + the scale-derived threshold
    // (NOT tuned). `spread()` already walks every edge type, so the new
    // edges surface automatically, each labelled with the relation that
    // reached the node. The proof of "multiple relations, not one cluster":
    // the same node has DIFFERENT neighbours under DIFFERENT edge types.

    /// Read a node's signature for an arbitrary relation back as `Vec<i64>`.
    /// The signature lives under `sig_attr` as a Tuple of Ints. Generalises
    /// `read_shape_signature` to any relation's signature attr.
    fn read_relation_signature(&self, nid: NodeID, sig_attr: Sym) -> Option<Vec<i64>> {
        let v = self.graph.node(nid).attrs.get(&sig_attr)?;
        match v {
            Value::Tuple(t) | Value::List(t) => Some(t.iter().map(|x| x.as_f64() as i64).collect()),
            _ => None,
        }
    }

    /// Declare one relation edge type admissible in Γ:
    /// (SalientShape) -[edge_type]-> (SalientShape). Generalises
    /// `declare_shares_shape` to any relation. Idempotent-ish (a redundant
    /// candidate is harmless). This adds ONE edge type to the grammar; the
    /// existing edge types (shares_shape / audio / video / ...) are untouched.
    pub fn declare_relation_edge(&mut self, edge_type: &str, provenance: &str) {
        let shape_t = self.interner.intern("SalientShape");
        let edge_t = self.interner.intern(edge_type);
        let src_var = self.interner.intern("a");
        let tgt_var = self.interner.intern("b");
        let weight = crate::grammar::Grammar::default_weight(&mut self.terms);
        let prov = self.interner.intern(provenance);
        let prod = crate::grammar::Production {
            src: crate::grammar::NodePattern {
                type_: shape_t,
                var: src_var,
            },
            edge_type: edge_t,
            tgt: crate::grammar::NodePattern {
                type_: shape_t,
                var: tgt_var,
            },
            where_: None,
            weight,
            provenance: prov,
        };
        self.add_production(prod);
    }

    /// Attach a relation SIGNATURE (under `sig_attr`) to an EXISTING
    /// SalientShape node, then WIRE `edge_type` edges to every other
    /// SalientShape node that carries a `sig_attr` signature within the
    /// scale-derived neighbour threshold. The same node can carry many
    /// relation signatures at once (shape, timbre, affect, function), each
    /// under its own attr key. Returns the list of (neighbour, distance)
    /// linked. Linking is SELECTED (equal length, distance < threshold),
    /// so it cannot over-link an unrelated control into the relation.
    ///
    /// This is the generic multi-relational wiring: one held metric
    /// (`shape_distance` over ordinal-rank signatures) applied per relation,
    /// bidirectionally, additive to whatever edges the node already has.
    pub fn wire_relation(
        &mut self,
        node: NodeID,
        edge_type: &str,
        sig_attr: &str,
        signature: &[i64],
        provenance: &str,
    ) -> Vec<(NodeID, i64)> {
        let shape_t = self.interner.intern("SalientShape");
        let sig_key = self.interner.intern(sig_attr);

        // Store the relation signature on the node under its own attr key.
        let sig_tuple: smallvec::SmallVec<[Value; 4]> =
            signature.iter().map(|&x| Value::Int(x)).collect();
        self.set_attr(node, sig_key, Value::Tuple(std::sync::Arc::new(sig_tuple)));

        // Ensure the edge type is admissible (declare once; cheap if known).
        if !self
            .checker
            .grammar
            .knows_edge_type(self.interner.intern(edge_type))
        {
            self.declare_relation_edge(edge_type, provenance);
        }
        let edge_t = self.interner.intern(edge_type);

        let thr = crate::memory::shape_neighbour_threshold(signature.len());
        let mut linked: Vec<(NodeID, i64)> = Vec::new();
        let existing = self.graph.nodes_of_type(shape_t);
        for other in existing {
            if other == node {
                continue;
            }
            let Some(other_sig) = self.read_relation_signature(other, sig_key) else {
                continue;
            };
            let d = crate::memory::shape_distance(signature, &other_sig);
            if d < thr {
                let _ = self.add_edge(node, edge_t, other, FxHashMap::default());
                let _ = self.add_edge(other, edge_t, node, FxHashMap::default());
                linked.push((other, d));
            }
        }
        linked
    }

    /// AFFECT relation wiring with the PROPER metric: per-feature normalised
    /// L2 (NOT ordinal rank). Takes the RAW heterogeneous affect vectors for a
    /// set of nodes (parallel arrays: `nodes[i]` carries `raw[i]`), normalises
    /// each FEATURE across the population (z-score, fixed-point milli-z),
    /// stores the normalised signature on each node under `sig_attr`, then
    /// wires `edge_type` edges between every pair within the scale-derived
    /// affect threshold (`affect_neighbour_threshold`). Bidirectional, additive.
    ///
    /// Why batch: per-feature normalisation needs the POPULATION (mean/std per
    /// feature over the clip set being linked). The world adapter hands the raw
    /// vectors; normalisation + distance + threshold are all here in the core.
    /// Returns, per node index, the list of (neighbour, distance) linked.
    pub fn wire_relation_affect(
        &mut self,
        nodes: &[NodeID],
        edge_type: &str,
        sig_attr: &str,
        raw: &[Vec<f64>],
        provenance: &str,
    ) -> Vec<Vec<(NodeID, i64)>> {
        let sig_key = self.interner.intern(sig_attr);
        // PER-FEATURE z-score normalisation across the population (core).
        let normed = crate::memory::affect_normalize(raw);

        // Store each node's normalised signature under its own attr key.
        for (i, &node) in nodes.iter().enumerate() {
            let sig_tuple: smallvec::SmallVec<[Value; 4]> =
                normed[i].iter().map(|&x| Value::Int(x)).collect();
            self.set_attr(node, sig_key, Value::Tuple(std::sync::Arc::new(sig_tuple)));
        }

        // Ensure the edge type is admissible.
        if !self
            .checker
            .grammar
            .knows_edge_type(self.interner.intern(edge_type))
        {
            self.declare_relation_edge(edge_type, provenance);
        }
        let edge_t = self.interner.intern(edge_type);

        let n_feat = normed.first().map(|v| v.len()).unwrap_or(0);
        let thr = crate::memory::affect_neighbour_threshold(n_feat);

        let mut out: Vec<Vec<(NodeID, i64)>> = vec![Vec::new(); nodes.len()];
        for i in 0..nodes.len() {
            for j in (i + 1)..nodes.len() {
                let d = crate::memory::l2_distance(&normed[i], &normed[j]);
                if d < thr {
                    let _ = self.add_edge(nodes[i], edge_t, nodes[j], FxHashMap::default());
                    let _ = self.add_edge(nodes[j], edge_t, nodes[i], FxHashMap::default());
                    out[i].push((nodes[j], d));
                    out[j].push((nodes[i], d));
                }
            }
        }
        out
    }

    /// FUNCTION relation wiring with the PROPER metric: CATEGORICAL match
    /// (Hamming distance on the bucketed role vector), NOT ordinal rank. Stores
    /// the role-bucket signature on the node under `sig_attr`, then wires
    /// `edge_type` to every other node whose role category matches within the
    /// categorical threshold (`categorical_neighbour_threshold`, i.e. Hamming
    /// <= 1). function-neighbours = SAME structural role. Bidirectional,
    /// additive. Returns the list of (neighbour, distance) linked.
    pub fn wire_relation_categorical(
        &mut self,
        node: NodeID,
        edge_type: &str,
        sig_attr: &str,
        signature: &[i64],
        provenance: &str,
    ) -> Vec<(NodeID, i64)> {
        let shape_t = self.interner.intern("SalientShape");
        let sig_key = self.interner.intern(sig_attr);

        let sig_tuple: smallvec::SmallVec<[Value; 4]> =
            signature.iter().map(|&x| Value::Int(x)).collect();
        self.set_attr(node, sig_key, Value::Tuple(std::sync::Arc::new(sig_tuple)));

        if !self
            .checker
            .grammar
            .knows_edge_type(self.interner.intern(edge_type))
        {
            self.declare_relation_edge(edge_type, provenance);
        }
        let edge_t = self.interner.intern(edge_type);

        let thr = crate::memory::categorical_neighbour_threshold(signature.len());
        let mut linked: Vec<(NodeID, i64)> = Vec::new();
        let existing = self.graph.nodes_of_type(shape_t);
        for other in existing {
            if other == node {
                continue;
            }
            let Some(other_sig) = self.read_relation_signature(other, sig_key) else {
                continue;
            };
            let d = crate::memory::categorical_distance(signature, &other_sig);
            if d < thr {
                let _ = self.add_edge(node, edge_t, other, FxHashMap::default());
                let _ = self.add_edge(other, edge_t, node, FxHashMap::default());
                linked.push((other, d));
            }
        }
        linked
    }

    /// SPREADING-ACTIVATION recall. From a cue node, traverse edges of
    /// MULTIPLE types (shares_shape + co-occurrence + whatever the node
    /// carries) up to `max_hops`, surfacing the activated set. NOT a
    /// single-key descent — a memory is held by many edges and recall
    /// spreads along whichever ones the cue matches. Returns, for each
    /// reached node, the edge_type that FIRST surfaced it and the hop
    /// distance, so shape-analogues are distinguishable from co-occurrence
    /// neighbours.
    pub fn spread(&self, cue: NodeID, max_hops: usize) -> Vec<(NodeID, Sym, usize)> {
        use std::collections::VecDeque;
        let mut seen: rustc_hash::FxHashSet<NodeID> = Default::default();
        seen.insert(cue);
        let mut out: Vec<(NodeID, Sym, usize)> = Vec::new();
        let mut q: VecDeque<(NodeID, usize)> = VecDeque::new();
        q.push_back((cue, 0));
        while let Some((node, hop)) = q.pop_front() {
            if hop >= max_hops {
                continue;
            }
            // Traverse ALL edge types out of this node (plus incoming, since
            // shares_shape is wired both ways but other relations may be
            // directed). Group by edge_type so each surfaced node records
            // the relation that reached it.
            for eidx in self.graph.out_edges_idx(node, None) {
                let ed = self.graph.edge(eidx);
                let tgt = ed.tgt;
                if seen.insert(tgt) {
                    out.push((tgt, ed.edge_type, hop + 1));
                    q.push_back((tgt, hop + 1));
                }
            }
            for eidx in self.graph.in_edges_idx(node, None) {
                let ed = self.graph.edge(eidx);
                let src = ed.src;
                if seen.insert(src) {
                    out.push((src, ed.edge_type, hop + 1));
                    q.push_back((src, hop + 1));
                }
            }
        }
        out
    }

    // --- Phase 7c: rewrite rules ----------------------------------------

    fn rebuild_rule_reader_index(&mut self) {
        self.rule_readers_by_key.clear();
        self.rule_reads_any.clear();
        for (idx, rule) in self.rules.iter().enumerate() {
            let mut keys: Vec<_> = rule.read_set.iter().copied().collect();
            keys.sort_by_key(|k| match k {
                crate::rewrite::RuleKey::Attr(s) => (0u8, s.0),
                crate::rewrite::RuleKey::Type(s) => (1u8, s.0),
                crate::rewrite::RuleKey::Edge(s) => (2u8, s.0),
            });
            for key in keys {
                self.rule_readers_by_key.entry(key).or_default().push(idx);
            }
            if rule.reads_any {
                self.rule_reads_any.push(idx);
            }
        }
    }

    /// Canonical semantic hash used by rule-patch CAS. Runtime-only state
    /// (`active`) and identity metadata are removed before hashing. The JSON
    /// codec is already the exact checkpoint inverse, including every Term
    /// and Effect variant, so the hash is stable across export/import rather
    /// than depending on arena-local `TermIdx` values.
    fn rule_content_hash(&self, rule: &crate::rewrite::RewriteRule) -> u64 {
        let mut j = crate::py::rule_to_json(rule, &self.terms, &self.interner);
        if let Some(obj) = j.as_object_mut() {
            obj.remove("active");
            obj.remove("rule_uid");
            obj.remove("revision");
            obj.remove("content_hash");
            obj.remove("mutation_protected");
        }
        // FNV-1a, kept in the positive i64 range so graph-native RulePatch
        // nodes can carry it as Value::Int without a lossy representation.
        let mut hash = 0xcbf29ce484222325u64;
        for byte in serde_json::to_vec(&j).expect("rule JSON is serialisable") {
            hash ^= byte as u64;
            hash = hash.wrapping_mul(0x100000001b3);
        }
        let hash = hash & (i64::MAX as u64);
        if hash == 0 {
            1
        } else {
            hash
        }
    }

    fn rule_clause_value(&mut self, rule_index: usize, field: RulePatchField) -> Value {
        let j = match field {
            RulePatchField::Where => self.rules[rule_index]
                .where_
                .map(|idx| crate::jsonio::term_to_json(&self.terms, idx, &self.interner))
                .unwrap_or(serde_json::Value::Null),
            RulePatchField::Effects => serde_json::Value::Array(
                self.rules[rule_index]
                    .effects
                    .iter()
                    .map(|effect| crate::py::effect_to_json(effect, &self.terms, &self.interner))
                    .collect(),
            ),
        };
        crate::persist::decode_value(&j, &mut self.interner)
    }

    fn rule_index_by_uid(&self, uid: crate::rewrite::RuleUid) -> Option<usize> {
        self.rules.iter().position(|rule| rule.uid == uid)
    }

    /// Return stable identity metadata for a rule slot.
    pub fn rule_metadata(
        &self,
        idx: crate::rewrite::RuleIdx,
    ) -> Option<(crate::rewrite::RuleUid, u64, u64, bool)> {
        self.rules
            .get(idx.0 as usize)
            .map(|rule| (rule.uid, rule.revision, rule.content_hash, rule.active))
    }

    fn stage_rule_patch(
        &mut self,
        uid: crate::rewrite::RuleUid,
        expected_revision: u64,
        expected_content_hash: u64,
        field: RulePatchField,
        proposed_clause: &Value,
    ) -> Result<StagedRulePatch, RulePatchError> {
        let rule_index = self
            .rule_index_by_uid(uid)
            .ok_or(RulePatchError::TargetNotFound)?;
        let current = &self.rules[rule_index];
        if !current.active {
            return Err(RulePatchError::TargetInactive);
        }
        if current.mutation_protected {
            return Err(RulePatchError::ProtectedTarget);
        }
        if current.revision != expected_revision {
            return Err(RulePatchError::StaleRevision {
                actual: current.revision,
            });
        }
        if current.content_hash != expected_content_hash {
            return Err(RulePatchError::StaleContentHash {
                actual: current.content_hash,
            });
        }

        let inverse_clause = self.rule_clause_value(rule_index, field);
        let terms_before = self.terms.nodes.len();
        let mut replacement = self.rules[rule_index].clone();
        let parsed = match field {
            RulePatchField::Where => {
                let j = crate::graph_rules::value_to_json(proposed_clause, &self.interner);
                match crate::jsonio::term_from_json(&j, &mut self.terms, &mut self.interner) {
                    Ok(idx) => {
                        replacement.where_ = Some(idx);
                        true
                    }
                    Err(_) => false,
                }
            }
            RulePatchField::Effects => {
                match crate::graph_rules::parse_effects(
                    proposed_clause,
                    &mut self.terms,
                    &mut self.interner,
                ) {
                    Some(effects) => {
                        replacement.effects = effects;
                        true
                    }
                    None => false,
                }
            }
        };
        if !parsed {
            // Parsing can append a prefix of a malformed tree. A refused patch
            // is observationally exact: even the append-only Term arena returns
            // to its pre-stage length.
            self.terms.nodes.truncate(terms_before);
            return Err(RulePatchError::MalformedClause);
        }
        replacement.derive_access(&self.terms);
        replacement.revision = expected_revision + 1;
        replacement.content_hash = self.rule_content_hash(&replacement);
        Ok(StagedRulePatch {
            rule_index,
            uid,
            expected_revision,
            expected_content_hash,
            replacement,
            inverse_clause,
        })
    }

    fn refresh_rule_slot_after_patch(&mut self, i: usize) {
        let hop = self.hop_frontier;
        self.rules[i].set_wf_hop(hop);
        let mut deps: rustc_hash::FxHashSet<Sym> = Default::default();
        for key in &self.rules[i].read_set {
            if let crate::rewrite::RuleKey::Edge(edge_type) = key {
                deps.insert(*edge_type);
            }
        }
        self.rule_edge_type_deps[i] = deps;
        self.rule_has_where[i] = self.rules[i].where_.is_some();
        self.rule_pred_retract_ok[i] = {
            let rule = &self.rules[i];
            let mut seen: rustc_hash::FxHashSet<Sym> = Default::default();
            let no_repeat = rule
                .match_edges
                .iter()
                .all(|edge| seen.insert(edge.edge_type));
            let add_only = rule.effects.iter().all(|effect| {
                matches!(
                    effect,
                    crate::rewrite::Effect::AddEdge { .. }
                        | crate::rewrite::Effect::AddNode { .. }
                        | crate::rewrite::Effect::AddNodeIfAbsent { .. }
                        | crate::rewrite::Effect::SetAttr { .. }
                        | crate::rewrite::Effect::SetAttrIfDifferent { .. }
                )
            });
            rule.where_.is_some()
                && !rule.match_edges.is_empty()
                && no_repeat
                && !rule.reads_external
                && add_only
        };
        self.rebuild_rule_reader_index();
        #[cfg(all(target_arch = "x86_64", target_os = "linux"))]
        if i < self.rule_where_jit.len() {
            self.rule_where_jit[i] = None;
        }
        self.rule_cursors[i].clear();
        self.rule_dirty_nodes[i].clear();
        self.rule_dirty[i] = true;
        self.rule_cost_micros[i] = 0;
        self.rule_cost_count[i] = 0;
        self.rule_cost_progress[i] = 0;
        self.any_mutation = true;
        self.gamma_epoch.bump();
    }

    fn commit_rule_patch(
        &mut self,
        staged: StagedRulePatch,
    ) -> Result<RulePatchReceipt, RulePatchError> {
        let current = &self.rules[staged.rule_index];
        // Recheck immediately before the swap. This matters even in the
        // single-writer engine: several RulePatch nodes may have been queued
        // from one snapshot and only the first may validly consume its CAS.
        if !current.active {
            return Err(RulePatchError::TargetInactive);
        }
        if current.mutation_protected {
            return Err(RulePatchError::ProtectedTarget);
        }
        if current.uid != staged.uid {
            return Err(RulePatchError::TargetNotFound);
        }
        if current.revision != staged.expected_revision {
            return Err(RulePatchError::StaleRevision {
                actual: current.revision,
            });
        }
        if current.content_hash != staged.expected_content_hash {
            return Err(RulePatchError::StaleContentHash {
                actual: current.content_hash,
            });
        }
        let receipt = RulePatchReceipt {
            uid: staged.uid,
            previous_revision: staged.expected_revision,
            previous_content_hash: staged.expected_content_hash,
            revision: staged.replacement.revision,
            content_hash: staged.replacement.content_hash,
            inverse_clause: staged.inverse_clause,
        };
        // The only semantic mutation: one whole-rule swap after every
        // fallible operation and both CAS checks have completed.
        self.rules[staged.rule_index] = staged.replacement;
        self.refresh_rule_slot_after_patch(staged.rule_index);
        Ok(receipt)
    }

    /// Preferred direct transaction API. Graph rules use the same operation
    /// through a `RulePatch` node and `ApplyRulePatch` effect.
    pub fn apply_rule_patch(
        &mut self,
        uid: crate::rewrite::RuleUid,
        expected_revision: u64,
        expected_content_hash: u64,
        field: &str,
        proposed_clause: Value,
    ) -> Result<RulePatchReceipt, RulePatchError> {
        let field = RulePatchField::parse(field)?;
        let staged = self.stage_rule_patch(
            uid,
            expected_revision,
            expected_content_hash,
            field,
            &proposed_clause,
        )?;
        self.commit_rule_patch(staged)
    }

    /// Store a rewrite rule. Returns its [`RuleIdx`] for `apply_rule`
    /// / `run_rules`. Rules are kept in insertion order; `run_rules`
    /// scans them in that order to pick the first match per step.
    pub fn add_rule(&mut self, rule: crate::rewrite::RewriteRule) -> crate::rewrite::RuleIdx {
        self.add_rule_with_match_order_policy(rule, true)
    }

    /// Install a rule while preserving the caller's clause sequence. This is
    /// an explicit control surface for source-authored ordering and benchmark
    /// comparisons; production callers should use `add_rule`, which keeps the
    /// default selectivity heuristic.
    pub fn add_rule_preserving_match_order(
        &mut self,
        rule: crate::rewrite::RewriteRule,
    ) -> crate::rewrite::RuleIdx {
        self.add_rule_with_match_order_policy(rule, false)
    }

    fn add_rule_with_match_order_policy(
        &mut self,
        mut rule: crate::rewrite::RewriteRule,
        auto_reorder_match_edges: bool,
    ) -> crate::rewrite::RuleIdx {
        if rule.uid.0 == 0 || self.rules.iter().any(|installed| installed.uid == rule.uid) {
            while self
                .rules
                .iter()
                .any(|installed| installed.uid.0 == self.next_rule_uid)
            {
                self.next_rule_uid += 1;
            }
            rule.uid = crate::rewrite::RuleUid(self.next_rule_uid);
            self.next_rule_uid += 1;
        } else {
            self.next_rule_uid = self.next_rule_uid.max(rule.uid.0.saturating_add(1));
        }
        // `add_rule` is the sole path that pushes into `self.rules`, so it
        // owns making a newly-installed rule live regardless of how the
        // caller built the `RewriteRule` value (struct-literal callers
        // typically spread `..Default::default()`, which would otherwise
        // leave `active: false` — see the field's doc comment).
        rule.active = true;
        // Cost-based match-edge reorder at install time. Uses current
        // `edges_by_type` cardinality as a selectivity proxy — graph
        // mutates after install, but the structural shape (which
        // edge_types are rare vs. common) is usually stable enough
        // that this proxy beats fixed authoring order. Rule semantics
        // are unchanged; only matcher traversal cost differs.
        let g = &self.graph;
        if auto_reorder_match_edges {
            rule.match_edges = crate::rewrite::reorder_match_edges_with_hints(
                &rule.match_edges,
                &rule.index_hints,
                |et| g.edges_by_type(et).len(),
            );
        }
        // R10 (join-index wave): a rule that ships an `IndexJoinHint` is
        // declaring its own dependency on a live attr index. Auto-provision
        // it here so the hint is self-contained — no separate world-adapter
        // `declare_attr_index` call needed. Idempotent (declare_attr_index
        // no-ops if already declared) and always safe: the index is
        // incrementally maintained by every subsequent node insert/
        // set_attr/delete (see graph.rs), so it can never go stale, and
        // `hinted_candidates` falls back to the exact original unindexed
        // scan whenever `has_attr_index` is false.
        for hint in &rule.index_hints {
            self.graph.declare_attr_index(hint.node_type, hint.this_key);
        }
        // slice (b) deferred: derive the access sets (kept for the future
        // dirty_by_writeset), but do NOT auto-enable batch — the fast path
        // is off until the whole-slice cascade-dirtying lands.
        rule.derive_access(&self.terms);
        // Never trust a persisted/author-supplied digest. Its only authority is
        // the exact body installed in this runtime.
        rule.content_hash = self.rule_content_hash(&rule);
        // Differential firing: cache the set of edge_types this rule reads
        // ANYWHERE — match clause AND where-clause — so an external edge write
        // (mark_edge_type_dirty) wakes a rule that reads that edge type only in
        // its where-clause (e.g. a `Count(Neighbours(src, E))` staleness guard on
        // a materialized-view recompute rule that MATCHES on `depends_on`).
        // derive_access already computed the full read_set above; building deps
        // from `match_edges` alone left where-clause edge reads out of the
        // external dirty path -> silent staleness on external edge add/delete,
        // while `dirty_by_writeset` (the rule-effect path) already consults the
        // where-inclusive read_set. This makes the two dirty paths symmetric (the
        // external-path UNDER-fire mirror of RUN 27's rule-effect over-fire).
        // read_set already contains every match-edge type (derive_access inserts
        // them), so this is a superset of the old match-only deps: strictly more
        // waking, never less — correctness-preserving.
        let mut deps: rustc_hash::FxHashSet<Sym> = Default::default();
        for k in &rule.read_set {
            if let crate::rewrite::RuleKey::Edge(et) = k {
                deps.insert(*et);
            }
        }
        let idx_usize = self.rules.len();
        let mut read_keys: Vec<_> = rule.read_set.iter().copied().collect();
        read_keys.sort_by_key(|k| match k {
            crate::rewrite::RuleKey::Attr(s) => (0u8, s.0),
            crate::rewrite::RuleKey::Type(s) => (1u8, s.0),
            crate::rewrite::RuleKey::Edge(s) => (2u8, s.0),
        });
        for key in read_keys {
            self.rule_readers_by_key
                .entry(key)
                .or_default()
                .push(idx_usize);
        }
        if rule.reads_any {
            self.rule_reads_any.push(idx_usize);
        }
        self.rule_edge_type_deps.push(deps);
        self.rule_has_where.push(rule.where_.is_some());
        self.rule_dirty.push(true);
        self.rule_cost_micros.push(0);
        self.rule_cost_count.push(0);
        self.rule_cost_progress.push(0);
        self.rule_cursors.push(rustc_hash::FxHashMap::default());
        // PREDICATE RETRACTION (block 194000): per-rule dirty-node set +
        // static eligibility for the node-seeded path. Eligible iff the rule
        // has a where (an attr flip can only change bindings THROUGH a where),
        // has ≥1 match edge, no repeated edge type (same dedup constraint the
        // incremental path imposes), does NOT read external framebuffers, and
        // its effects are ADD-ONLY (no DelEdge/DelNode/ReplaceValue/…): the
        // fire direction only, no derived-tuple retraction — that is the next
        // rung. All computed once, read only when the flag is on.
        self.rule_dirty_nodes.push(rustc_hash::FxHashSet::default());
        self.rule_dirty_dyn_nodes.push(rustc_hash::FxHashSet::default());
        let ok = {
            let k = rule.match_edges.len();
            let mut seen: rustc_hash::FxHashSet<Sym> = Default::default();
            let no_repeat = rule.match_edges.iter().all(|me| seen.insert(me.edge_type));
            let add_only = rule.effects.iter().all(|e| {
                matches!(
                    e,
                    crate::rewrite::Effect::AddEdge { .. }
                        | crate::rewrite::Effect::AddNode { .. }
                        | crate::rewrite::Effect::AddNodeIfAbsent { .. }
                        | crate::rewrite::Effect::SetAttr { .. }
                        | crate::rewrite::Effect::SetAttrIfDifferent { .. }
                )
            });
            // SOUNDNESS (block 292000): the node-seeded re-evaluator only wakes
            // bindings incident to a CHANGED node, which is correct iff every
            // attr the rule reads lives on a match-bound node. A rule that reads
            // attrs through a node-set-iterating Term (Neighbours/Argmin/Count/…
            // — e.g. the nav's `mv_pick_hop`, an Argmin over Neighbours reading
            // `gdist` on cells its match never bound) would go stale under the
            // frontier path, since a write to one of those cells is unreachable
            // from the changed-node frontier. Exclude such rules; they fall back
            // to the cursor-clear full re-scan (byte-identical), while a purely
            // local rule (the flood's `mv_relax`) keeps the fast frontier path.
            let local_reads = !crate::rewrite::rule_reads_attr_via_node_set(&rule, &self.terms);
            rule.where_.is_some()
                && k >= 1
                && no_repeat
                && !rule.reads_external
                && add_only
                && local_reads
        };
        self.rule_pred_retract_ok.push(ok);
        // JIT compile the where-clause if all its Terms are kernel
        // shape. Falls back to interpreter at match time for rules
        // with where-clauses that use Filter, Sum, Float, etc.
        #[cfg(all(target_arch = "x86_64", target_os = "linux"))]
        {
            let compiled = rule.where_.and_then(|where_idx| {
                // Var order = match-edge vars in insertion order
                // (each MatchEdge introduces up to 2 vars; dedupe).
                let mut seen: rustc_hash::FxHashSet<Sym> = Default::default();
                let mut order: Vec<Sym> = Vec::new();
                for me in &rule.match_edges {
                    for v in [me.src_var, me.tgt_var] {
                        if seen.insert(v) {
                            order.push(v);
                        }
                    }
                }
                crate::jit::CompiledWhere::try_compile(&self.terms, where_idx, &order)
            });
            self.rule_where_jit.push(compiled);
        }
        let idx = crate::rewrite::RuleIdx(idx_usize as u32);
        let mut rule = rule;
        rule.set_wf_hop(self.hop_frontier);
        self.rules.push(rule);
        // Γ has changed — bump the epoch so any installed L2
        // dispatcher's compiled-artefact cache treats prior
        // entries as stale on next lookup.
        self.gamma_epoch.bump();
        idx
    }

    /// Retract a rule installed by `add_rule` — it never matches/fires
    /// again in `apply_rule_once` / `run_rules` / `tick`.
    ///
    /// Semantics: **tombstone the slot, not swap-remove**. `self.rules`
    /// stays exactly the length it was; `idx` is never reused and every
    /// OTHER rule keeps the exact `RuleIdx` it always had. This is a
    /// deliberate choice over compacting the Vec: `RuleIdx`s are held
    /// outside this call (Python world adapters, the self-repair
    /// `SetRuleClause` path which looks a rule up by name but every other
    /// consumer that cached an index, agent-authored rule composers) and a
    /// swap-remove would silently repoint whichever rule used to sit at
    /// the freed slot — invisible index corruption for a self-modifying
    /// agent. `rule_count()` therefore reports the number of SLOTS
    /// (`self.rules.len()`), including tombstoned ones, matching the
    /// index space `add_rule` hands out — not the number of live rules.
    ///
    /// Returns `true` iff this call actually deactivated a previously-live
    /// rule; `false` for an out-of-range `idx` OR a rule that was already
    /// removed (double-remove is a safe, idempotent no-op).
    pub fn remove_rule(&mut self, idx: crate::rewrite::RuleIdx) -> bool {
        let i = idx.0 as usize;
        if i >= self.rules.len() || !self.rules[i].active {
            return false;
        }
        self.rules[i].active = false;
        // A tombstoned rule must never look dirty again: once it's
        // filtered out of run_rules's `to_try` scan, nothing will ever
        // clear a stale `true` bit for it (mark_edge_type_dirty /
        // mark_node_mutation / dirty_by_writeset don't know about
        // removal). Clearing it here, plus filtering by `active` at every
        // scheduling point, keeps run_rules's fast "nothing dirty" exit
        // working after a removal.
        self.rule_dirty[i] = false;
        // Drop cached per-rule state that only makes sense for a live
        // rule — harmless to leave, but stale state on a dead slot is
        // just confusion waiting to happen if the rule is ever inspected.
        self.rule_cursors[i].clear();
        #[cfg(all(target_arch = "x86_64", target_os = "linux"))]
        {
            if i < self.rule_where_jit.len() {
                self.rule_where_jit[i] = None;
            }
        }
        // Γ has changed (a production left the grammar) — bump the epoch,
        // mirroring add_rule's bump for the reverse edit.
        self.gamma_epoch.bump();
        true
    }

    /// Find one match for the rule at `idx` and apply its effects.
    /// Returns true iff a match was found and applied. The mutations
    /// land in the graph directly — no admissibility check; matches
    /// the Python `graph_rewrite.run` posture.
    ///
    /// `shape_mismatch_prunes_negative_problem_space`: if the substrate
    /// has an `active_shape_target` set + the rule's where-clause Shape
    /// is incompatible, the rule is SKIPPED WITHOUT EVALUATION. The
    /// substrate's pruning path lives here — Cousot abstract domain
    /// admissibility + Ashby variety match at the rule dispatch level.
    pub fn apply_rule_once(&mut self, idx: crate::rewrite::RuleIdx) -> bool {
        let work_scope = &self.graph as *const crate::graph::TypedGraph as usize;
        let _work_operation = crate::access_trace::begin_work_operation_kind(work_scope, 2);
        if (idx.0 as usize) >= self.rules.len() || !self.rules[idx.0 as usize].active {
            return false;
        }
        if self.rule_in_negative_space(idx) {
            self.shape_pruned_count = self.shape_pruned_count.saturating_add(1);
            return false;
        }
        crate::scale_audit::begin_rule_enumeration(idx.0);
        let rule = self.rules[idx.0 as usize].clone();
        crate::scale_audit::register_rule_audit_metadata(idx.0, rule.name.0, self.interner.resolve(rule.name), rule.match_edges.len());
        let Some(b) = crate::rewrite::match_rule(
            &rule,
            &self.terms,
            &self.graph,
            &self.interner,
            Some(&self.concepts),
            Some(&self.framebuffers),
        ) else {
            crate::scale_audit::end_rule_enumeration();
            return false;
        };
        crate::rewrite::apply_rule(
            &rule,
            &b,
            &mut self.terms,
            &mut self.graph,
            &mut self.interner,
            Some(&mut self.concepts),
            Some(&self.framebuffers),
            false,
        );
        // A single one-shot apply has no fixpoint loop to drain the
        // perception-as-action queue from — drain it here so a rule
        // fired via apply_rule_once (not just the run_rules/tick
        // fixpoint) still sees its fb_sample take effect immediately.
        self.apply_pending_fb_samples();
        crate::scale_audit::end_rule_enumeration();
        true
    }

    /// `apply_rule_once` at the WHOLE-BINDING-SET grain, for rules that opt
    /// in via their `batch` flag. A rule WITHOUT the flag is delegated to
    /// `apply_rule_once` unchanged, so this method is byte-identical to it
    /// except on rules that asked for batching.
    ///
    /// WHY THIS IS A SEPARATE METHOD rather than a `batch` test inside
    /// `apply_rule_once` (`VISION_BATCH_APPLY_PREREG.md` §4A): two seed rules
    /// already set `batch` (`seeds/vision_settle.json`'s `st_settle` /
    /// `st_commit`). Putting the dispatch in `apply_rule_once` would silently
    /// change their behaviour for every existing Python caller that drives
    /// them that way — a scope widening disguised as a one-line fix. With a
    /// separate entry point, every path that does not call it is unchanged BY
    /// CONSTRUCTION, which is what makes the §9 "defaults preserve committed
    /// results" claim structural rather than merely tested.
    ///
    /// THE CALLER OWNS THE EVAL CACHE. `batch_apply_rule` matches with the
    /// cache live (correct — the match phase runs pre-mutation) and applies
    /// with `None`, so its `Neighbours`/`Filter`/`Holds` entries are stale the
    /// instant an effect lands. `run_rules_opts` clears them after its own
    /// batch dispatch for exactly this reason; so does this. `ch_sustained`'s
    /// `Sum`/`Count` over `Neighbours` is precisely such a cached term, and
    /// the pre-registration named a missing clear here as the single most
    /// likely source of a byte-identity failure.
    pub fn apply_rule_batch(&mut self, idx: crate::rewrite::RuleIdx) -> bool {
        if (idx.0 as usize) >= self.rules.len() || !self.rules[idx.0 as usize].active {
            return false;
        }
        if !self.rules[idx.0 as usize].batch {
            return self.apply_rule_once(idx);
        }
        let work_scope = &self.graph as *const crate::graph::TypedGraph as usize;
        let _work_operation = crate::access_trace::begin_work_operation_kind(work_scope, 3);
        if self.rule_in_negative_space(idx) {
            self.shape_pruned_count = self.shape_pruned_count.saturating_add(1);
            return false;
        }
        crate::scale_audit::begin_rule_enumeration(idx.0);
        let rule = self.rules[idx.0 as usize].clone();
        crate::scale_audit::register_rule_audit_metadata(idx.0, rule.name.0, self.interner.resolve(rule.name), rule.match_edges.len());
        // CLEAR ON THE WAY IN AS WELL AS OUT. The fallback path
        // (`apply_rule_once`) passes no cache at all, so it can neither
        // populate nor read one — but `run_rules` / `tick` CAN leave entries
        // behind, and this method is called immediately after `tick()` on the
        // drive path. Without this the batch match phase could read a
        // `Neighbours` entry `tick` computed against a since-mutated graph,
        // which is a difference from the one-at-a-time path that has nothing
        // to do with batching. Clearing here makes the batch path AT LEAST as
        // fresh as the path it replaces; five clears per tick is not a cost
        // worth reasoning about.
        self.eval_cache.clear_graph_dependent();
        let progressed = crate::rewrite::batch_apply_rule(
            &rule,
            &mut self.terms,
            &mut self.graph,
            &mut self.interner,
            Some(&mut self.concepts),
            Some(&self.framebuffers),
            Some(&mut self.eval_cache),
            None,
        );
        self.eval_cache.clear_graph_dependent();
        // Same reason `apply_rule_once` drains here: a one-shot apply has no
        // fixpoint loop to drain the perception-as-action queue from.
        self.apply_pending_fb_samples();
        crate::scale_audit::end_rule_enumeration();
        progressed
    }

    /// Apply every rule to a fixed point. Returns step count.
    ///
    /// **Differential firing**: only rules whose read sets intersect
    /// recent mutations are attempted each outer iteration. A rule's
    /// dirty bit is set by `mark_edge_type_dirty` / `mark_node_mutation`,
    /// and cleared after the rule has been given a chance to fire (or
    /// found no progressing binding). When no rule is dirty AND no
    /// rule progressed this iteration, the loop terminates.
    /// Semi-naive matching for k-edge rules. For each match-edge
    /// position, drive enumeration from edges new since this rule last
    /// visited that edge_type. The rest of the pattern is solved by the
    /// existing matcher with the driver's vars pre-bound.
    ///
    /// Returns `Some(progressed)` if the incremental path applies;
    /// `None` if we must fall through to full re-match:
    ///   - any cursor invalidated by an intervening edge delete
    ///   - rule has repeated edge_types in match_edges (the lex-order
    ///     dedup the textbook semi-naive does isn't implemented yet;
    ///     conservative full re-match keeps the answer correct)
    ///
    /// For rules without repeated edge_types, no two "driving positions"
    /// can produce the same binding (each binding has at most one new
    /// edge in any single edge_type slot, so the position that brings
    /// the new edge is uniquely determined). Without that property
    /// we'd double-apply.
    /// Debug: is this rule the one named by $SUBSTRATE_TRACE_RULE? Env-gated so normal runs/tests pay only a
    /// cheap failed env lookup. Used to trace exactly WHY a specific rule does/doesn't fire across the fixpoint.
    #[inline]
    fn dbg_traced(&self, rule_idx: usize) -> bool {
        match std::env::var("SUBSTRATE_TRACE_RULE") {
            Ok(want) => self.interner.resolve(self.rules[rule_idx].name) == want,
            Err(_) => false,
        }
    }

    /// PREDICATE RETRACTION (block 194000, ladder rung B). The node-seeded
    /// re-evaluation path: when an external attr write flipped a covered
    /// where-rule's predicate on STABLE edges, re-evaluate ONLY the bindings
    /// that touch the written node(s) — O(K) — instead of the committed whole-
    /// cursor clear + O(N) full rescan. Returns `Some(progressed)` when it took
    /// the node-seeded path, `None` to fall through to `try_incremental_match`
    /// (which, with the cursor left as this method set it, does the correct
    /// thing: cold full rescan when a structural change invalidated the cursor).
    ///
    /// SOUNDNESS. Engages ONLY when every match-edge cursor is present, its
    /// per-type version is unchanged (no delete of that type), AND its position
    /// equals the current `edges_by_type` length (no NEW edge of that type) —
    /// i.e. the edges are provably unchanged since the cursor was set, so the
    /// only thing that can have flipped a where is an attr, and every external
    /// attr write recorded its node here. A binding becomes newly TRUE only if
    /// an attr it reads changed, i.e. one of its nodes is in the dirty set;
    /// seeding the matcher from each dirty node across every match var therefore
    /// re-derives exactly the bindings whose truth can have changed. Effects are
    /// add-only (checked at `add_rule`), so there is no derived-tuple retraction
    /// to miss — the fire direction only.
    fn try_predicate_retraction(&mut self, rule_idx: usize) -> Option<bool> {
        self.try_predicate_retraction_mode(rule_idx, false)
    }

    /// `frontier = true` is the write-frontier pre-pass (`write_frontier`): the
    /// same node-seeded re-evaluation, but new edges may exist (the semi-naive
    /// pass that follows handles them and owns the cursor), so the cursor is
    /// only version-checked and is neither required unchanged nor re-stored.
    fn try_predicate_retraction_mode(&mut self, rule_idx: usize, frontier: bool) -> Option<bool> {
        if frontier {
            if !self.write_frontier || !self.rules[rule_idx].wf_ok {
                return None;
            }
        } else {
        if !self.predicate_retraction {
            return None;
        }
        if !self
            .rule_pred_retract_ok
            .get(rule_idx)
            .copied()
            .unwrap_or(false)
        {
            return None;
        }
        }
        let no_dyn = !frontier
            || self.rule_dirty_dyn_nodes.get(rule_idx).map_or(true, |d| d.is_empty());
        if rule_idx >= self.rule_dirty_nodes.len()
            || (self.rule_dirty_nodes[rule_idx].is_empty() && no_dyn)
        {
            return None;
        }
        let rule_clone = self.rules[rule_idx].clone();
        // Validate cursors: every match-edge type must be UNCHANGED since the
        // cursor was set (version match AND no new edges). Any structural change
        // ⇒ clear this rule's dirty-node set + cursor and fall through to the
        // cold full rescan, which re-derives everything correctly.
        for me in &rule_clone.match_edges {
            let cur_len = self.graph.edges_by_type(me.edge_type).len();
            let expected_ver = self.cursor_version(me.edge_type);
            match self.rule_cursors[rule_idx].get(&me.edge_type).copied() {
                Some((c, dv)) if dv == expected_ver && (frontier || c == cur_len) => {}
                _ => {
                    self.rule_dirty_nodes[rule_idx].clear();
                    if frontier {
                        self.rule_dirty_dyn_nodes[rule_idx].clear();
                    }
                    if !frontier {
                        self.rule_cursors[rule_idx].clear();
                    }
                    return None;
                }
            }
        }
        // Dirty nodes, sorted by id for a DETERMINISTIC seeding order (and so
        // the unsound falsifier drops a well-defined node).
        if frontier && self.match_set_provably_empty(&rule_clone) {
            // no binding exists now; any later one needs a new match edge, which
            // the semi-naive pass drives against the full graph
            self.rule_dirty_nodes[rule_idx].clear();
            self.rule_dirty_dyn_nodes[rule_idx].clear();
            return Some(false);
        }
        let mut dirty: Vec<NodeID> = self.rule_dirty_nodes[rule_idx].iter().copied().collect();
        dirty.sort();
        // write frontier: nodes dirtied only by a dynamically-named attr write
        // re-check only the bindings that bind them to an `AttrByName` variable
        let mut dyn_only: Vec<NodeID> = if frontier {
            let full = &self.rule_dirty_nodes[rule_idx];
            self.rule_dirty_dyn_nodes[rule_idx]
                .iter()
                .copied()
                .filter(|n| !full.contains(n))
                .collect()
        } else {
            Vec::new()
        };
        dyn_only.sort();
        let n_full = dirty.len();
        dirty.extend(dyn_only);
        if self.predicate_retraction_unsound && !dirty.is_empty() {
            // FALSIFIER: silently drop one dirty node ⇒ a binding that flipped
            // to TRUE on it is never re-fired ⇒ diverges from the full rescan.
            dirty.remove(0);
        }

        #[cfg(all(target_arch = "x86_64", target_os = "linux"))]
        let jit_for_this = self.rule_where_jit.get(rule_idx).and_then(|j| j.as_ref());
        #[cfg(not(all(target_arch = "x86_64", target_os = "linux")))]
        let jit_for_this: Option<&crate::jit::CompiledWhere> = None;

        // MATCH PHASE — for each dirty node `d`, drive from the edges INCIDENT
        // to `d` (its own out/in adjacency, O(degree(d)) — NOT a scan of the
        // whole edge population), seeding BOTH endpoints and solving the rest of
        // the pattern with that match edge removed. This is the semi-naive
        // driver of `try_incremental_match`, but the driving set is "edges
        // touching a dirty node" instead of "edges new since last visit". A
        // binding whose where flipped to true on `d` contains an edge incident
        // to `d` at some match position, so every such binding is reached.
        // Borrows mirror `try_incremental_match` (immutable self + &mut cache).
        let mut bindings: Vec<crate::rewrite::Binding> = Vec::new();
        for (di, &d) in dirty.iter().enumerate() {
            let dyn_d = di >= n_full;
            for drive_i in 0..rule_clone.match_edges.len() {
                let drive_me = rule_clone.match_edges[drive_i].clone();
                let src_ok = !dyn_d || rule_clone.wf_dyn_vars.contains(&drive_me.src_var);
                let tgt_ok = !dyn_d || rule_clone.wf_dyn_vars.contains(&drive_me.tgt_var);
                if !src_ok && !tgt_ok {
                    continue;
                }
                // Incident edges of this type at d, as SRC (d = src_var) and as
                // TGT (d = tgt_var). Collect endpoints first (releases the graph
                // adjacency borrow before the match call takes &self.graph).
                let mut seeds: smallvec::SmallVec<[(NodeID, NodeID); 8]> =
                    smallvec::SmallVec::new();
                if src_ok {
                for &ei in self.graph.out_edges_slice(d, Some(drive_me.edge_type)) {
                    let e = self.graph.edge(ei);
                    seeds.push((e.src, e.tgt));
                }
                }
                if tgt_ok && drive_me.tgt_var != drive_me.src_var {
                    for &ei in self.graph.in_edges_slice(d, Some(drive_me.edge_type)) {
                        let e = self.graph.edge(ei);
                        seeds.push((e.src, e.tgt));
                    }
                }
                let mut sub_edges = rule_clone.match_edges.clone();
                sub_edges.remove(drive_i);
                let seeded = self.seeded_join_order;
                if seeded {
                    sub_edges = seeded_join_order(sub_edges, drive_me.src_var, drive_me.tgt_var);
                }
                let sub_rule = crate::rewrite::RewriteRule {
                    name: rule_clone.name,
                    match_edges: sub_edges,
                    where_: rule_clone.where_,
                    effects: rule_clone.effects.clone(),
                    index_hints: if seeded { rule_clone.index_hints.clone() } else { Vec::new() },
                    // pushdown is order-independent (a conjunct runs once its vars are bound)
                    where_conjuncts: if seeded { rule_clone.where_conjuncts.clone() } else { Vec::new() },
                    both_bound_probe: seeded,
                    ..Default::default()
                };
                for (e_src, e_tgt) in seeds {
                    // Rule matching requires distinct bound variables to
                    // resolve to distinct nodes. Match the full check here,
                    // before seeding the incremental matcher.
                    if e_src == e_tgt && drive_me.src_var != drive_me.tgt_var {
                        continue;
                    }
                    let mut initial: crate::rewrite::Binding = rustc_hash::FxHashMap::default();
                    initial.insert(drive_me.src_var, e_src);
                    if drive_me.src_var != drive_me.tgt_var {
                        initial.insert(drive_me.tgt_var, e_tgt);
                    }
                    crate::rewrite::match_rule_each_with_initial(
                        &sub_rule,
                        &initial,
                        &self.terms,
                        &self.graph,
                        &self.interner,
                        Some(&self.concepts),
                        Some(&self.framebuffers),
                        Some(&mut self.eval_cache),
                        jit_for_this,
                        |b| {
                            crate::scale_audit::binding_cloned();
                            bindings.push(b.clone());
                            true
                        },
                    );
                }
            }
        }

        // APPLY PHASE — dedup by canonical binding key, apply add-only effects
        // once each, undo genuine no-ops (so the engine's no-progress detection
        // is intact — an already-fired / still-false binding leaves no trace).
        let mut seen: rustc_hash::FxHashSet<smallvec::SmallVec<[(Sym, NodeID); 8]>> =
            Default::default();
        let mut progressed_any = false;
        for b in bindings {
            let canon = self.binding_key(&rule_clone, &b);
            if !seen.insert(canon) {
                continue;
            }
            let outcome = crate::rewrite::apply_rule_full(
                &rule_clone,
                &b,
                &mut self.terms,
                &mut self.graph,
                &mut self.interner,
                Some(&mut self.concepts),
                Some(&self.framebuffers),
                None,
                true,
            );
            if outcome.progressed {
                progressed_any = true;
            } else {
                crate::rewrite::undo_apply(outcome.undo, &mut self.graph);
            }
        }

        // Consumed this rule's dirty-node set. Re-store cursors at the current
        // (unchanged) lengths + versions so the next visit is valid.
        self.rule_dirty_nodes[rule_idx].clear();
        if frontier {
            self.rule_dirty_dyn_nodes[rule_idx].clear();
            return Some(progressed_any);
        }
        let ets: Vec<Sym> = rule_clone
            .match_edges
            .iter()
            .map(|me| me.edge_type)
            .collect();
        for et in ets {
            let len = self.graph.edges_by_type(et).len();
            let ver = self.cursor_version(et);
            self.rule_cursors[rule_idx].insert(et, (len, ver));
        }
        Some(progressed_any)
    }

    fn try_incremental_match(&mut self, rule_idx: usize) -> Option<bool> {
        use rustc_hash::{FxHashMap, FxHashSet};
        let rule_clone = self.rules[rule_idx].clone();
        let tr = self.dbg_traced(rule_idx);
        let k = rule_clone.match_edges.len();
        if k == 0 {
            if tr {
                eprintln!(
                    "[TRACE-IM] {}: bail k==0 (no match edges) -> None (full re-match)",
                    self.interner.resolve(rule_clone.name)
                );
            }
            return None;
        }
        // PERCEPTION-AS-ACTION: a `reads_external` rule's where-clause can
        // flip truth value with ZERO graph mutation (a live shared-memory
        // writer bumped `frame_seq`) — the semi-naive incremental path
        // only re-scans EDGES NEW since the rule's last visit, so a rule
        // whose match-edges are otherwise stable (e.g. a static
        // `?t -[wants_look]-> ?g` wiring) would see `new_edges_per_pos`
        // permanently empty and NEVER re-evaluate the where-clause again
        // after its cursor is first established — silently starving it
        // even though `run_rules` force-dirties it every pass (see
        // `RewriteRule::reads_external`'s doc comment). Bail to the full
        // re-match path every time instead, same as the k==0 case above:
        // cheap for the tiny match patterns these look-rules actually
        // have, and it re-evaluates the where-clause fresh every call.
        if rule_clone.reads_external {
            if tr {
                eprintln!("[TRACE-IM] {}: bail reads_external (FbFrameSeq-gated) -> None (full re-match, polled every pass)",
                              self.interner.resolve(rule_clone.name));
            }
            return None;
        }
        // Defer rules whose match-edges repeat an edge_type — would need
        // lex-order semi-naive to avoid double-counting bindings.
        {
            // A repeated match edge type makes two driving positions find the
            // same binding; `seen_bindings` below dedups by the canonical binding
            // key across ALL positions, so under `batch_incremental` the repeat
            // costs duplicates only (each binding with >= 1 new edge is found by
            // driving from that edge's slot against the full other slots).
            let mut seen: FxHashSet<Sym> = Default::default();
            for me in &rule_clone.match_edges {
                if !seen.insert(me.edge_type) && !self.batch_incremental {
                    return None;
                }
            }
        }

        // Validate cursors for every edge_type the rule reads. If any
        // is stale (delete since visit), bail and re-establish from
        // the full re-match.
        //
        // Block 192000: the version a cursor is validated against is PER EDGE
        // TYPE when `incremental_match` is on (`cursor_version` → the graph's
        // `edge_delete_version_by_type[et]`), and the single global counter
        // otherwise (committed behaviour, byte-identical). So a delete of a
        // DIFFERENT edge type leaves this cursor valid. The UNSOUND falsifier
        // (incremental_match_unsound) accepts a stale cursor regardless of its
        // delete version — it MISSES the retraction and must diverge.
        let unsound_accept = self.incremental_match && self.incremental_match_unsound;
        let mut cursor_starts: FxHashMap<Sym, usize> = Default::default();
        for me in &rule_clone.match_edges {
            let expected = self.cursor_version(me.edge_type);
            match self.rule_cursors[rule_idx].get(&me.edge_type).copied() {
                Some((c, dv)) if dv == expected || unsound_accept => {
                    cursor_starts.insert(me.edge_type, c);
                }
                other => {
                    if tr {
                        eprintln!("[TRACE-IM] {}: cursor for edge_type '{}' is {} (expected_dv={}) -> None (full re-match)",
                        self.interner.resolve(rule_clone.name), self.interner.resolve(me.edge_type),
                        match other { Some((c, dv)) => format!("STALE(c={},dv={})", c, dv), None => "MISSING".into() },
                        expected);
                    }
                    return None;
                }
            }
        }

        // Snapshot the new-edges range at each driving position BEFORE
        // we start applying effects (which mutate edges_by_type).
        let new_edges_per_pos: Vec<Vec<crate::graph::EdgeIdx>> = rule_clone
            .match_edges
            .iter()
            .map(|me| {
                let edges = self.graph.edges_by_type(me.edge_type);
                let start = *cursor_starts.get(&me.edge_type).unwrap();
                if start >= edges.len() {
                    Vec::new()
                } else {
                    edges[start..].to_vec()
                }
            })
            .collect();

        // Pre-compute the lengths we'll write back to cursors at the
        // end. Using lengths captured BEFORE any applied effects means
        // newly-inserted edges from this rule's own effects will be
        // processed on the next visit, matching the existing engine's
        // fixed-point semantics.
        // Block 192000: also capture each type's cursor-VERSION here, BEFORE any
        // effect fires. If THIS rule's own effects delete edges of `et`, the
        // graph's per-type version bumps during apply, so the pre-apply version
        // we store below will differ from the post-apply version the next visit
        // reads → the cursor is correctly STALE → the delete-effecting rule
        // full-rescans, exactly as the committed engine does (via its post-hoc
        // global `edge_delete_version` bump). Under OFF this equals the committed
        // store value (global, constant across try_incremental_match).
        let lengths_before: Vec<(Sym, usize, u64)> = rule_clone
            .match_edges
            .iter()
            .map(|me| {
                (
                    me.edge_type,
                    self.graph.edges_by_type(me.edge_type).len(),
                    self.cursor_version(me.edge_type),
                )
            })
            .collect();

        // EMPTY-MATCH PROOF (block 189000), site 3 of 3. The driver loops below
        // would run the matcher once per NEW edge at each position and every one
        // of those sub-matches would fail at the zero-population join. Skipping
        // the loops leaves `progressed_any = false` and falls straight through
        // to the cursor advance to `lengths_before` — the identical exit the
        // loops would have reached, since a rule that cannot bind cannot apply
        // an effect and therefore cannot change any `edges_by_type` length.
        // (Evaluated HERE, before the `rule_where_jit` borrow, so the telemetry
        // write does not fight the JIT reference the loops hold.)
        let provably_empty = self.match_set_provably_empty(&rule_clone);
        if provably_empty {
            self.note_empty_match_skip(rule_idx);
        }

        #[cfg(all(target_arch = "x86_64", target_os = "linux"))]
        let jit_for_this = self.rule_where_jit.get(rule_idx).and_then(|j| j.as_ref());
        #[cfg(not(all(target_arch = "x86_64", target_os = "linux")))]
        let jit_for_this: Option<&crate::jit::CompiledWhere> = None;

        if tr {
            let counts: Vec<usize> = new_edges_per_pos.iter().map(|v| v.len()).collect();
            eprintln!(
                "[TRACE-IM] {}: cursors VALID -> INCREMENTAL path; new_edges_per_pos={:?} {}",
                self.interner.resolve(rule_clone.name),
                counts,
                if counts.iter().all(|&n| n == 0) {
                    "*** ALL ZERO: no new driving edges -> nothing scanned -> rule CANNOT fire this pass even if its where is now true (the stable-edge attr-gated bug) ***"
                } else {
                    ""
                }
            );
        }

        let mut progressed_any = false;
        let mut seen_bindings: FxHashSet<smallvec::SmallVec<[(Sym, NodeID); 8]>> =
            Default::default();
        // BINDING PROJECTION (block 188000), incremental path. With k == 1 the
        // driving edge binds EVERY match variable, so a driver whose projection
        // has already been processed can be skipped BEFORE the matcher runs —
        // which is where the where-clause is evaluated, and therefore where the
        // cost is. Same soundness argument as the cold path: equal projection ⇒
        // equal where-truth ⇒ equal (idempotent) effects.
        let project_drivers = self.projection_cold_path(&rule_clone);
        let mut seen_driver_proj: FxHashSet<smallvec::SmallVec<[(Sym, NodeID); 8]>> =
            Default::default();

        for drive_i in (0..k).take_while(|_| !provably_empty) {
            let drive_me = rule_clone.match_edges[drive_i].clone();
            let new_edges = &new_edges_per_pos[drive_i];

            for &edge_idx in new_edges {
                let (e_src, e_tgt) = {
                    let e = self.graph.edge(edge_idx);
                    (e.src, e.tgt)
                };
                // Distinct match variables must bind distinct nodes, as
                // enforced by the full matcher. Avoid seeding a binding that
                // the full matcher would immediately reject.
                if e_src == e_tgt && drive_me.src_var != drive_me.tgt_var {
                    continue;
                }
                let mut initial: crate::rewrite::Binding = FxHashMap::default();
                initial.insert(drive_me.src_var, e_src);
                if drive_me.src_var != drive_me.tgt_var {
                    initial.insert(drive_me.tgt_var, e_tgt);
                }
                if project_drivers
                    && !seen_driver_proj.insert(self.binding_key(&rule_clone, &initial))
                {
                    continue;
                }

                // Sub-rule = rule without the driving match_edge. The
                // driver's vars are pre-bound; remaining positions
                // resolve via the standard matcher.
                let mut sub_edges = rule_clone.match_edges.clone();
                sub_edges.remove(drive_i);
                let seeded = self.seeded_join_order;
                if seeded {
                    sub_edges = seeded_join_order(sub_edges, drive_me.src_var, drive_me.tgt_var);
                }
                let sub_rule = crate::rewrite::RewriteRule {
                    name: rule_clone.name,
                    match_edges: sub_edges,
                    where_: rule_clone.where_,
                    effects: rule_clone.effects.clone(),
                    index_hints: if seeded { rule_clone.index_hints.clone() } else { Vec::new() },
                    // pushdown is order-independent (a conjunct runs once its vars are bound)
                    where_conjuncts: if seeded { rule_clone.where_conjuncts.clone() } else { Vec::new() },
                    both_bound_probe: seeded,
                    ..Default::default()
                };

                // Collect bindings before applying — apply mutates the
                // graph and could invalidate the matcher's iteration.
                let mut bindings: Vec<crate::rewrite::Binding> = Vec::new();
                crate::rewrite::match_rule_each_with_initial(
                    &sub_rule,
                    &initial,
                    &self.terms,
                    &self.graph,
                    &self.interner,
                    Some(&self.concepts),
                    Some(&self.framebuffers),
                    Some(&mut self.eval_cache),
                    jit_for_this,
                    |b| {
                        crate::scale_audit::binding_cloned();
                        bindings.push(b.clone());
                        true
                    },
                );

                for b in bindings {
                    // Canonical binding key for dedup (sorted by Sym) — the
                    // PROJECTED key when block 188000's flag is on and the rule
                    // qualifies, the full binding otherwise.
                    let canon = self.binding_key(&rule_clone, &b);
                    if !seen_bindings.insert(canon) {
                        continue;
                    }
                    let outcome = crate::rewrite::apply_rule_full(
                        &rule_clone,
                        &b,
                        &mut self.terms,
                        &mut self.graph,
                        &mut self.interner,
                        Some(&mut self.concepts),
                        Some(&self.framebuffers),
                        None,
                        true,
                    );
                    if outcome.progressed {
                        // Multi-spec fan-out fix: keep draining the
                        // bindings list rather than returning after the
                        // first progressing apply. The previous
                        // behaviour advanced the per-edge-type cursor
                        // here and returned — N admissible bindings
                        // for N wired specs were therefore handled
                        // one-per-tick, never multiple per tick (see
                        // domains/phase3_rules.py docstring under
                        // "multi-spec fan-out" for the original
                        // observation).
                        //
                        // Termination still holds because:
                        //   (a) `bindings` was snapshotted ABOVE before
                        //       any effects fired, so the iteration is
                        //       bounded by the new-edge set at entry —
                        //       a rule whose effects insert NEW edges
                        //       won't grow this loop, those new edges
                        //       are picked up on the next visit (the
                        //       fixed-point semantics preserved by
                        //       `lengths_before`).
                        //   (b) `seen_bindings` dedups, so a rule whose
                        //       multiple drivers produce the same
                        //       canonical binding fires it once.
                        //   (c) per-binding `apply_rule_full` still
                        //       returns `progressed=false` on no-ops
                        //       and we undo them, keeping the engine's
                        //       no-progress detection intact.
                        progressed_any = true;
                        // DON'T return here — continue to the next
                        // binding for this driver, then to the next
                        // driver, draining every admissible match in
                        // this pass.
                    } else {
                        crate::rewrite::undo_apply(outcome.undo, &mut self.graph);
                    }
                }
            }
        }

        // Drained every admissible binding across every driver.
        // Advance every cursor to `lengths_before` (the snapshot
        // captured before any apply). This is the same advance the
        // pre-fix code did at this exit point AND was duplicating
        // inside the loop on first progress.
        for (et, len, ver) in lengths_before {
            self.rule_cursors[rule_idx].insert(et, (len, ver));
        }
        if tr {
            eprintln!(
                "[TRACE-IM] {}: INCREMENTAL done, progressed={}",
                self.interner.resolve(rule_clone.name),
                progressed_any
            );
        }
        Some(progressed_any)
    }

    /// Drain graph-native `RulePatch` transactions queued by
    /// `ApplyRulePatch`. The patch node is both request and durable receipt:
    /// the agent can inspect a stable refusal code or the committed revision,
    /// content hash and exact inverse clause without host interpretation.
    fn apply_pending_rule_patches(&mut self) {
        let drain_started = crate::scale_audit::enabled().then(std::time::Instant::now);
        let pending = std::mem::take(&mut self.graph.pending_rule_patches);
        let drained_items = pending.len();
        let target_uid_key = self.interner.intern("target_uid");
        let expected_revision_key = self.interner.intern("expected_revision");
        let expected_hash_key = self.interner.intern("expected_content_hash");
        let field_key = self.interner.intern("field");
        let proposed_key = self.interner.intern("proposed_clause");
        let status_key = self.interner.intern("status");
        let reason_key = self.interner.intern("reason");
        let result_revision_key = self.interner.intern("result_revision");
        let result_hash_key = self.interner.intern("result_content_hash");
        let previous_revision_key = self.interner.intern("previous_revision");
        let previous_hash_key = self.interner.intern("previous_content_hash");
        let inverse_key = self.interner.intern("inverse_clause");
        let committed = self.interner.intern("committed");
        let refused = self.interner.intern("refused");
        let ok = self.interner.intern("ok");

        for patch_node in pending {
            if !self.graph.has_node(patch_node) {
                continue;
            }
            let parsed = {
                let attrs = &self.graph.node(patch_node).attrs;
                let uid = match attrs.get(&target_uid_key) {
                    Some(Value::Int(n)) if *n > 0 => Some(crate::rewrite::RuleUid(*n as u64)),
                    _ => None,
                };
                let revision = match attrs.get(&expected_revision_key) {
                    Some(Value::Int(n)) if *n >= 0 => Some(*n as u64),
                    _ => None,
                };
                let hash = match attrs.get(&expected_hash_key) {
                    Some(Value::Int(n)) if *n > 0 => Some(*n as u64),
                    _ => None,
                };
                let field = attrs.get(&field_key).and_then(|value| match value {
                    Value::Str(sym) => Some(self.interner.resolve(*sym).to_string()),
                    _ => None,
                });
                let clause = attrs.get(&proposed_key).cloned();
                match (uid, revision, hash, field, clause) {
                    (Some(uid), Some(revision), Some(hash), Some(field), Some(clause)) => {
                        Some((uid, revision, hash, field, clause))
                    }
                    _ => None,
                }
            };

            let result = match parsed {
                Some((uid, revision, hash, field, clause)) => {
                    self.apply_rule_patch(uid, revision, hash, &field, clause)
                }
                None => Err(RulePatchError::MalformedPatchNode),
            };
            match result {
                Ok(receipt) => {
                    self.set_attr(patch_node, status_key, Value::Str(committed));
                    self.set_attr(patch_node, reason_key, Value::Str(ok));
                    self.set_attr(
                        patch_node,
                        previous_revision_key,
                        Value::Int(receipt.previous_revision as i64),
                    );
                    self.set_attr(
                        patch_node,
                        previous_hash_key,
                        Value::Int(receipt.previous_content_hash as i64),
                    );
                    self.set_attr(
                        patch_node,
                        result_revision_key,
                        Value::Int(receipt.revision as i64),
                    );
                    self.set_attr(
                        patch_node,
                        result_hash_key,
                        Value::Int(receipt.content_hash as i64),
                    );
                    self.set_attr(patch_node, inverse_key, receipt.inverse_clause);
                }
                Err(error) => {
                    let reason = self.interner.intern(error.code());
                    self.set_attr(patch_node, status_key, Value::Str(refused));
                    self.set_attr(patch_node, reason_key, Value::Str(reason));
                    match error {
                        RulePatchError::StaleRevision { actual } => self.set_attr(
                            patch_node,
                            result_revision_key,
                            Value::Int(actual as i64),
                        ),
                        RulePatchError::StaleContentHash { actual } => {
                            self.set_attr(patch_node, result_hash_key, Value::Int(actual as i64))
                        }
                        _ => {}
                    }
                }
            }
        }
        if let Some(started) = drain_started {
            crate::scale_audit::deferred_queue_drained(
                "rule_patches", drained_items,
                started.elapsed().as_nanos().min(u64::MAX as u128) as u64,
            );
        }
    }

    /// INTRINSIC SELF-REPAIR: drain + apply the rule-clause rewrites queued by `SetRuleClause`
    /// effects. For each `(rule_name, field, clause_value)`: find the live struct rule by name,
    /// decode the clause Value to wire JSON, parse it into the target arena, swap the rule's
    /// `where_`/`effects` IN PLACE (index preserved), recompute its access set, drop its stale
    /// compiled-where JIT + incremental cursor, and mark it dirty so it re-matches its NEW body.
    /// A rule editing a rule — graph-native self-modification of the live engine.
    fn apply_pending_rule_edits(&mut self) {
        let drain_started = crate::scale_audit::enabled().then(std::time::Instant::now);
        let pending = std::mem::take(&mut self.graph.pending_rule_edits);
        let drained_items = pending.len();
        for (name, field, val) in pending {
            // SELF-BUILD: MINT a brand-new live struct rule from a Rule NODE the agent composed (the
            // create-twin of the clause rewrite, riding the SAME pending queue — the jabberwock's choice:
            // one engine, JIT'd + access-derived like every seed rule, not the dormant graph_rules path).
            // The agent builds a type="Rule" node (id/match/where/effect attrs) via its synthesis, then
            // emits set_rule_clause(<id>, "__mint__", <that node>); here we compile it via the load-path
            // rule_from_node + add_rule so it runs live on the next pass. Name-guarded -> idempotent.
            if field == "__mint__" {
                if let Value::Node(nid) = val {
                    match crate::graph_rules::rule_from_node(
                        &self.graph,
                        nid,
                        &mut self.terms,
                        &mut self.interner,
                    ) {
                        Some(mut rule) => {
                            // A Rule node compiled by the live graph is newly
                            // authored even if its JSON originated as a copy
                            // of a protected prior.
                            rule.mutation_protected = false;
                            if self.rules.iter().any(|r| r.name == rule.name) {
                                // already minted -> idempotent skip (like teach)
                            } else {
                                let nm = self.interner.resolve(rule.name).to_string();
                                let idx = self.add_rule(rule);
                                if let Some((uid, revision, content_hash, _)) =
                                    self.rule_metadata(idx)
                                {
                                    let uid_key = self.interner.intern("rule_uid");
                                    let revision_key = self.interner.intern("revision");
                                    let hash_key = self.interner.intern("content_hash");
                                    self.set_attr(nid, uid_key, Value::Int(uid.0 as i64));
                                    self.set_attr(nid, revision_key, Value::Int(revision as i64));
                                    self.set_attr(nid, hash_key, Value::Int(content_hash as i64));
                                }
                                self.any_mutation = true;
                                eprintln!("[self-build] minted live rule '{}'", nm);
                            }
                        }
                        None => eprintln!("[self-build] MintRule: rule node {:?} mis-shaped", nid),
                    }
                } else {
                    eprintln!("[self-build] MintRule: payload is not a Rule node");
                }
                continue;
            }
            let name_sym = self.interner.intern(&name);
            let matches: Vec<usize> = self
                .rules
                .iter()
                .enumerate()
                .filter_map(|(i, rule)| (rule.active && rule.name == name_sym).then_some(i))
                .collect();
            if matches.is_empty() {
                eprintln!("[self-repair] SetRuleClause: no live rule named '{}'", name);
                continue;
            }
            if matches.len() != 1 {
                eprintln!(
                    "[self-repair] SetRuleClause: ambiguous live rule name '{}' ({} matches); \
                     use RulePatch target_uid + revision/hash CAS",
                    name,
                    matches.len(),
                );
                continue;
            }
            let i = matches[0];
            let target = &self.rules[i];
            match self.apply_rule_patch(
                target.uid,
                target.revision,
                target.content_hash,
                &field,
                val,
            ) {
                Ok(_) => {
                    eprintln!(
                        "[self-repair] legacy name rewrite committed for unique rule '{}' clause '{}'",
                        name, field
                    );
                }
                Err(error) => {
                    eprintln!(
                        "[self-repair] SetRuleClause: '{}' refused ({})",
                        name,
                        error.code()
                    );
                }
            }
        }
        if let Some(started) = drain_started {
            crate::scale_audit::deferred_queue_drained(
                "rule_edits", drained_items,
                started.elapsed().as_nanos().min(u64::MAX as u128) as u64,
            );
        }
    }

    /// PERCEPTION-AS-ACTION: drain `graph.pending_fb_samples` — the queue
    /// an `Effect::FbSample` populates from inside `apply_rule_full`
    /// (which only holds `&mut graph`, not `&mut Substrate` — the owner
    /// of the attached-framebuffer registry and the dirty-tracking
    /// node/edge mutation helpers `segment_and_track` needs). Called
    /// between passes (mirrors `apply_pending_rule_edits` immediately
    /// above), where `&mut self` is free, by calling `Substrate::
    /// fb_sample` itself — the SAME internal fn the PyO3 `fb_sample`
    /// method calls, so a rule-triggered sample mints/updates identical
    /// graph state (Region/Cell nodes) to a host-triggered one. Each
    /// `fb_sample` call already does its own dirty-marking internally
    /// (`add_node`/`set_attr`/`add_edge` inside `segment_and_track`), so
    /// downstream rules reading the fresh Region/Cell state wake
    /// normally on the next pass.
    pub(crate) fn apply_pending_fb_samples(&mut self) {
        let drain_started = crate::scale_audit::enabled().then(std::time::Instant::now);
        let pending = std::mem::take(&mut self.graph.pending_fb_samples);
        let drained_items = pending.len();
        for (fb_id, game, grid_w, grid_h) in pending {
            if let Err(e) = self.fb_sample(fb_id, game, grid_w, grid_h) {
                eprintln!("[perception] rule-queued fb_sample(fb_id={fb_id}) failed: {e}");
            }
        }
        if let Some(started) = drain_started {
            crate::scale_audit::deferred_queue_drained(
                "fb_samples", drained_items,
                started.elapsed().as_nanos().min(u64::MAX as u128) as u64,
            );
        }
    }

    /// SELF-TRAINING: drain `graph.pending_net_collapses` — the queue an
    /// `Effect::NetCollapse` populates from inside `apply_rule_full`. For
    /// each `(reflex_net, input, target, eta)`: find the net's assemblage
    /// (`-net_assemblage->`), run one surprise-driven weight collapse
    /// (`net_forward::net_collapse_step`, the WeightTensor twin of
    /// `hebbian_update_J`), and record an EMA of the surprise back onto the
    /// reflex net's `surprise` attr — the convergence signal the
    /// `reflex_self_train_converged` rule reads. This is how "collapse and
    /// surprise within the net" runs as part of the engine's run_rules loop.
    pub(crate) fn apply_pending_net_collapses(&mut self) {
        let drain_started = crate::scale_audit::enabled().then(std::time::Instant::now);
        let pending = std::mem::take(&mut self.graph.pending_net_collapses);
        let drained_items = pending.len();
        let na_edge = self.interner.intern("net_assemblage");
        let surprise_key = self.interner.intern("surprise");
        for (rn, input, target, eta) in pending {
            if !self.graph.has_node(rn) {
                continue;
            }
            let Some(&asm) = self.graph.neighbours(rn, Some(na_edge)).first() else {
                continue;
            };
            let surprise = crate::net_forward::net_collapse_step(
                &mut self.graph,
                &self.interner,
                asm,
                &input,
                &target,
                eta,
            );
            // EMA of surprise (smoother than the raw per-step value) — the
            // rolling signal the convergence rule gates on.
            let prev = match self.graph.node(rn).attrs.get(&surprise_key) {
                Some(crate::value::Value::Float(f)) => *f,
                Some(crate::value::Value::Int(i)) => *i as f64,
                _ => surprise,
            };
            let ema = 0.85 * prev + 0.15 * surprise;
            self.graph
                .set_node_attr(rn, surprise_key, crate::value::Value::Float(ema));
        }
        if let Some(started) = drain_started {
            crate::scale_audit::deferred_queue_drained(
                "net_collapses", drained_items,
                started.elapsed().as_nanos().min(u64::MAX as u128) as u64,
            );
        }
    }

    /// ONE rule attempt, with every piece of the committed bookkeeping that
    /// surrounds it -- this is the body of `run_rules_opts`'s inner
    /// `for rule_idx in to_try` loop, EXTRACTED VERBATIM (block 186000) so
    /// the per-area settlement runner can reuse the committed semantics
    /// instead of duplicating them and drifting. The ONLY statements removed
    /// from the extraction are the caller's two accumulators
    /// (`steps += 1; any_progress = true;`), which are now expressed by the
    /// returned bool. Returns whether this rule PROGRESSED.
    fn attempt_one_rule(&mut self, rule_idx: usize) -> bool {
        // SCALE AUDIT: declare WHICH rule is about to be enumerated, so
        // the C/R split can be made positionally (prereg §3): a rule's
        // FIRST enumeration this epoch is genuine comparison (C), every
        // LATER one re-derives a set an earlier pass already had (R).
        // This is THE fixpoint that runs the seed-installed rules; the
        // twin hook in `rewrite::run_rules_opts` covers the graph-Rule
        // store, which the vision seeds do not use.
        crate::scale_audit::begin_rule_enumeration(rule_idx as u32);
        let audit_rule = &self.rules[rule_idx];
        crate::scale_audit::register_rule_audit_metadata(rule_idx as u32, audit_rule.name.0, self.interner.resolve(audit_rule.name), audit_rule.match_edges.len());
        let __cost_t0 = std::time::Instant::now();
        // FALLBACK TRACE: bind the running rule by NAME so defaulted
        // reads and absence-branch firings are attributed to it. Name,
        // not index — the redundancy audit established that rule
        // INDICES shift under ablation (a withheld rule never occupies
        // a RuleIdx), so an index-keyed tally is not comparable across
        // arms. Cleared after the attempt so that reflex / production /
        // bare-evaluate reads are never mis-attributed to it.
        crate::fallback_trace::set_current_rule(Some(self.rules[rule_idx].name));
        // Semi-naive fast path: 1-edge rules with a valid cursor
        // process only edges new since last visit. Falls back to
        // full re-match for k-edge rules and for rules whose
        // cursor was invalidated by an intervening delete.
        let wf_pre = self.write_frontier
            && (self.rule_dirty_nodes.get(rule_idx).map_or(false, |d| !d.is_empty())
                || self.rule_dirty_dyn_nodes.get(rule_idx).map_or(false, |d| !d.is_empty()))
            && self.try_predicate_retraction_mode(rule_idx, true).unwrap_or(false);
        let progressed = if self.rules[rule_idx].batch && self.batch_incremental {
            if let Some(p) = self.try_incremental_match(rule_idx) {
                p
            } else {
                let rule = self.rules[rule_idx].clone();
                let mut frontier: FxHashMap<Sym, (usize, u64)> = FxHashMap::default();
                for me in &rule.match_edges {
                    frontier.entry(me.edge_type).or_insert_with(|| {
                        (self.graph.edges_by_type(me.edge_type).len(), self.cursor_version(me.edge_type))
                    });
                }
                let p = if self.match_set_provably_empty(&rule) {
                    self.note_empty_match_skip(rule_idx);
                    false
                } else {
                    crate::rewrite::batch_apply_rule(
                        &rule,
                        &mut self.terms,
                        &mut self.graph,
                        &mut self.interner,
                        Some(&mut self.concepts),
                        Some(&self.framebuffers),
                        Some(&mut self.eval_cache),
                        None,
                    )
                };
                self.eval_cache.clear_graph_dependent();
                for (et, lv) in frontier {
                    self.rule_cursors[rule_idx].insert(et, lv);
                }
                p
            }
        } else if self.rules[rule_idx].batch {
            // slice (b): batch-safe rule — apply EVERY binding this pass
            // (no per-binding undo/clone/restart). Collapses per-cell
            // perception rules from O(cells^2) passes to O(cells).
            let rule = self.rules[rule_idx].clone();
            // EMPTY-MATCH PROOF (block 189000), site 1 of 3. `batch_apply_rule`
            // with an empty match set snapshots zero bindings, applies nothing
            // and returns false — so returning false without calling it is
            // byte-identical. The eval-cache clears below still run, exactly as
            // they do on the committed path.
            let p = if self.match_set_provably_empty(&rule) {
                self.note_empty_match_skip(rule_idx);
                false
            } else {
                crate::rewrite::batch_apply_rule(
                    &rule,
                    &mut self.terms,
                    &mut self.graph,
                    &mut self.interner,
                    Some(&mut self.concepts),
                    Some(&self.framebuffers),
                    Some(&mut self.eval_cache),
                    None,
                )
            };
            // batch_apply mutated edges/attrs mid-pass; the run_rules loop
            // only clears the eval_cache at iteration TOP, but later rules
            // in THIS iteration (the next batch rule, the avatar cascade)
            // would read its now-stale Neighbours/Filter/Holds entries.
            // Clear it here so they see the live post-batch graph.
            self.eval_cache.clear_graph_dependent();
            p
        } else if let Some(p) = self.try_predicate_retraction(rule_idx) {
            // Block 194000: node-seeded per-binding re-eval (rung B). Only
            // engages for a covered rule with recorded dirty nodes + unchanged
            // edges; otherwise returns None and we fall through unchanged.
            p
        } else if let Some(p) = self.try_incremental_match(rule_idx) {
            p
        } else {
            let rule = self.rules[rule_idx].clone();
            #[cfg(all(target_arch = "x86_64", target_os = "linux"))]
            let jit_for_this = self.rule_where_jit.get(rule_idx).and_then(|j| j.as_ref());
            #[cfg(not(all(target_arch = "x86_64", target_os = "linux")))]
            let jit_for_this: Option<&crate::jit::CompiledWhere> = None;
            // Multi-spec fan-out fix (cold-cursor fallback).
            //
            // This path runs on a rule's FIRST visit (no cursor
            // yet) and after a delete invalidates its cursor. It
            // must fire every DISTINCT admissible binding exactly
            // ONCE this tick — the same snapshot semantics
            // `try_incremental_match` uses on the warm path — and
            // it must NOT run to a fixed point.
            //
            // The earlier fix here called `rewrite::run_rules`
            // with `usize::MAX`, trusting its no-progress
            // detection to halt. But that detection only halts
            // on IDEMPOTENT effects ("produces an already-present
            // edge counts as no progress"). A non-idempotent
            // effect — `Effect::AddNode` always mints a fresh
            // node, so it always "progresses" — has no fixed
            // point, so the same bindings re-fired forever,
            // allocating without bound. That was the multi-spec
            // fan-out OOM.
            //
            // Snapshot-drain instead: collect every binding once,
            // dedup by canonical key, apply each a single time.
            // Cascading rules (effects that enable further
            // matches) still complete — the next outer iteration
            // takes the warm incremental path on the newly-added
            // edges (cursor advanced to current length below), so
            // the closure is computed one layer per tick rather
            // than in one unbounded call. Termination holds
            // because each layer fires only NEW bindings and an
            // idempotent re-fire produces no progress.
            let mut bindings: Vec<crate::rewrite::Binding> = Vec::new();
            // EMPTY-MATCH PROOF (block 189000), site 2 of 3 — THE ONE THAT
            // MATTERS. 189000's §1.4 trace shows the three every-tick /
            // progressed-0 accel rules take THIS path on every tick (a dirtied
            // rule's own cursor is cleared, so the incremental cursor is never
            // valid), and the enumeration is a full `edges_by_type` scan of
            // 19,200 edges that backtracks at a join whose edge type has ZERO
            // population. The skip leaves `bindings` empty — which is exactly
            // what the enumeration would have produced — so the dedup/apply loop
            // below and the cursor re-establishment after it run UNCHANGED.
            if self.match_set_provably_empty(&rule) {
                self.note_empty_match_skip(rule_idx);
            } else if self.projection_cold_path(&rule) {
                // BINDING PROJECTION (block 188000), cold path. The committed
                // enumeration evaluates the where-clause once per binding, at
                // the leaf — which is where `ct_area_effort_tracks_live_salience`
                // spends 67% of the per-tick rule time, re-deriving the SAME
                // O(tasks) `MaxOver` for every one of its O(tasks) bindings.
                //
                // Enumerate WITHOUT the where (k == 1, so this is a single edge
                // scan and cannot blow up), keep ONE representative binding per
                // distinct projection, and then evaluate the where on the
                // representatives only — via a zero-match-edge rule with the
                // representative pre-bound, the same shape the incremental path
                // already uses when it removes its driving edge.
                let enum_rule = crate::rewrite::RewriteRule {
                    name: rule.name,
                    match_edges: rule.match_edges.clone(),
                    where_: None,
                    effects: Vec::new(),
                    ..Default::default()
                };
                let mut raw: Vec<crate::rewrite::Binding> = Vec::new();
                crate::rewrite::match_rule_each(
                    &enum_rule,
                    &self.terms,
                    &self.graph,
                    &self.interner,
                    Some(&self.concepts),
                    Some(&self.framebuffers),
                    Some(&mut self.eval_cache),
                    None,
                    |b| {
                        crate::scale_audit::binding_cloned();
                        raw.push(b.clone());
                        true
                    },
                );
                let mut seen_proj: rustc_hash::FxHashSet<smallvec::SmallVec<[(Sym, NodeID); 8]>> =
                    Default::default();
                let mut reps: Vec<crate::rewrite::Binding> = Vec::new();
                for b in raw {
                    if seen_proj.insert(self.binding_key(&rule, &b)) {
                        reps.push(b);
                    }
                }
                let check_rule = crate::rewrite::RewriteRule {
                    name: rule.name,
                    match_edges: Vec::new(),
                    where_: rule.where_,
                    effects: Vec::new(),
                    ..Default::default()
                };
                for rep in reps {
                    crate::rewrite::match_rule_each_with_initial(
                        &check_rule,
                        &rep,
                        &self.terms,
                        &self.graph,
                        &self.interner,
                        Some(&self.concepts),
                        Some(&self.framebuffers),
                        Some(&mut self.eval_cache),
                        jit_for_this,
                        |b| {
                            bindings.push(b.clone());
                            true
                        },
                    );
                }
            } else {
                crate::rewrite::match_rule_each(
                    &rule,
                    &self.terms,
                    &self.graph,
                    &self.interner,
                    Some(&self.concepts),
                    Some(&self.framebuffers),
                    Some(&mut self.eval_cache),
                    jit_for_this,
                    |b| {
                        crate::scale_audit::binding_cloned();
                        bindings.push(b.clone());
                        true
                    },
                );
            }
            // Snapshot every matched edge population BEFORE applying the
            // cold-drain bindings. A recursive rule can write one of its own
            // match edge types (e.g. reach(x,y) + link(y,z) -> reach(x,z)).
            // Advancing its cursor to the post-drain length below would mark
            // those newly-created edges as already consumed; dirty_by_writeset
            // correctly wakes the rule, but its next incremental visit would
            // then see zero new drivers and falsely settle before closure.
            // Keep the pre-apply frontier so self-produced edges are examined
            // on the next visit. For non-recursive rules this equals the old
            // cursor position and preserves the ordinary incremental path.
            let mut cursor_frontier_before_apply: FxHashMap<Sym, (usize, u64)> =
                FxHashMap::default();
            for me in &self.rules[rule_idx].match_edges {
                cursor_frontier_before_apply
                    .entry(me.edge_type)
                    .or_insert_with(|| {
                        (self.graph.edges_by_type(me.edge_type).len(),
                         self.cursor_version(me.edge_type))
                    });
            }
            if self.dbg_traced(rule_idx) {
                eprintln!("[TRACE-FULL] {}: FULL re-match (cold/invalidated cursor); bindings found = {} {}",
                    self.interner.resolve(rule.name), bindings.len(),
                    if bindings.is_empty() { "*** ZERO: the WHERE filtered every binding (where is FALSE) — NOT a cursor problem ***" } else { "(where passed for some binding -> will apply)" });
            }
            let mut res = false;
            // How many bindings this drain actually COMMITS. Two or more means
            // later bindings evaluated against earlier ones' writes — the
            // same-round visibility Stage A would remove. See
            // `effect_audit::record_multi_binding_drain`.
            let mut progressed_here: u64 = 0;
            // STAGE A staging area — empty and untouched when the flag is off.
            let compare_here = crate::stage_a::compare_mode()
                && crate::stage_a::rule_is_derivable(&rule, &self.terms);
            let stage_a_here =
                crate::stage_a::enabled() && crate::stage_a::rule_is_derivable(&rule, &self.terms);
            if crate::stage_a::enabled() && !stage_a_here {
                crate::stage_a::note_excluded_drain();
            }
            let mut proposals: Vec<crate::stage_a::Proposal> = Vec::new();
            let mut committed: Vec<crate::stage_a::Proposal> = Vec::new();
            // STAGE A: derive the whole drain against the untouched base, then
            // ask whether the resulting proposals are jointly applicable. If two
            // of them write the same place they were each computed blind to the
            // other, so the set is NOT independent and the sequential committed
            // path below runs instead. Deriving first and undoing leaves the
            // graph exactly where it started either way.
            let mut stage_a_committed = false;
            if stage_a_here {
                let mut derived: Vec<crate::stage_a::Proposal> = Vec::new();
                let mut seen: rustc_hash::FxHashSet<smallvec::SmallVec<[(Sym, NodeID); 8]>> =
                    Default::default();
                for b in &bindings {
                    if !seen.insert(self.binding_key(&rule, b)) {
                        continue;
                    }
                    let out = crate::rewrite::apply_rule_full(
                        &rule,
                        b,
                        &mut self.terms,
                        &mut self.graph,
                        &mut self.interner,
                        Some(&mut self.concepts),
                        Some(&self.framebuffers),
                        None,
                        true,
                    );
                    if out.progressed {
                        derived.push(crate::stage_a::capture(
                            &rule,
                            &out.undo,
                            &out.undo_src,
                            &self.graph,
                            true,
                        ));
                    }
                    crate::rewrite::undo_apply(out.undo, &mut self.graph);
                }
                if crate::stage_a::conflicts(&derived) {
                    crate::stage_a::note_conflict_fallback();
                } else if !derived.is_empty() {
                    for proposal in &derived {
                        crate::stage_a::commit(proposal, &mut self.graph);
                    }
                    progressed_here += derived.len() as u64;
                    res = true;
                    stage_a_committed = true;
                }
            }
            // Compare mode derives the Stage A proposals FIRST, against the
            // untouched base, undoes them, and then lets the committed loop run
            // normally below — so the graph ends up exactly where it would have.
            if compare_here {
                let mut derived: Vec<crate::stage_a::Proposal> = Vec::new();
                let mut seen: rustc_hash::FxHashSet<smallvec::SmallVec<[(Sym, NodeID); 8]>> =
                    Default::default();
                for b in &bindings {
                    if !seen.insert(self.binding_key(&rule, b)) {
                        continue;
                    }
                    let out = crate::rewrite::apply_rule_full(
                        &rule,
                        b,
                        &mut self.terms,
                        &mut self.graph,
                        &mut self.interner,
                        Some(&mut self.concepts),
                        Some(&self.framebuffers),
                        None,
                        true,
                    );
                    if out.progressed {
                        derived.push(crate::stage_a::capture(
                            &rule,
                            &out.undo,
                            &out.undo_src,
                            &self.graph,
                            true,
                        ));
                    }
                    crate::rewrite::undo_apply(out.undo, &mut self.graph);
                }
                proposals = derived;
            }
            let mut seen_bindings: rustc_hash::FxHashSet<smallvec::SmallVec<[(Sym, NodeID); 8]>> =
                Default::default();
            for b in bindings {
                if stage_a_committed {
                    break;
                }
                let canon = self.binding_key(&rule, &b);
                if !seen_bindings.insert(canon) {
                    continue;
                }
                // See `effect_audit::probe_exactness`. This is the LIVE drain
                // path (the `rewrite.rs` cold path is the other one), and it is
                // the stronger case: on progress it does not break, so a later
                // binding evaluates against earlier bindings' COMMITTED writes.
                // The fingerprint pair below measures only the rolled-back
                // probes — whether a non-progressing binding leaves the graph
                // exactly as it found it.
                let fp_before = if crate::effect_audit::probe_exactness() {
                    Some(self.graph.state_fingerprint())
                } else {
                    None
                };
                let outcome = crate::rewrite::apply_rule_full(
                    &rule,
                    &b,
                    &mut self.terms,
                    &mut self.graph,
                    &mut self.interner,
                    Some(&mut self.concepts),
                    Some(&self.framebuffers),
                    None,
                    true,
                );
                // STAGE A: derive against ONE immutable base. Capture the
                // firing's forward delta, then undo it so the NEXT binding
                // evaluates against the same graph this one did; the collected
                // proposals are applied together after the loop. When the flag
                // is off, or the rule can delete a node (undo cannot restore
                // one), this branch is skipped entirely and the committed
                // drain below runs byte-unchanged.
                if outcome.progressed {
                    if compare_here {
                        // Committed path: capture what THIS firing produced with
                        // earlier bindings' writes visible, and leave it applied.
                        committed.push(crate::stage_a::capture(
                            &rule,
                            &outcome.undo,
                            &outcome.undo_src,
                            &self.graph,
                            true,
                        ));
                    }
                    res = true;
                    progressed_here += 1;
                } else {
                    crate::scale_audit::apply_probe_rollback();
                    crate::rewrite::undo_apply(outcome.undo, &mut self.graph);
                    if let Some(before) = fp_before {
                        let after = self.graph.state_fingerprint();
                        let name = self.interner.resolve(rule.name).to_string();
                        crate::effect_audit::record_probe_rollback(before, after, || name);
                    }
                }
            }
            if compare_here {
                let name = self.interner.resolve(rule.name).to_string();
                crate::stage_a::record_comparison(&name, &proposals, &committed);
                proposals.clear();
            }
            // The single application boundary: every proposal derived above was
            // derived against the same base, and they land here in order.
            for proposal in &proposals {
                crate::stage_a::commit(proposal, &mut self.graph);
            }
            if progressed_here >= 2 {
                let name = self.interner.resolve(rule.name).to_string();
                crate::effect_audit::record_multi_binding_drain(&name, progressed_here);
            }
            // Re-establish each cursor at the pre-apply frontier captured
            // above. This is normally the full-rescan length; if the rule
            // wrote a matched edge type, retaining the earlier position is
            // required for recursive closure. Deletes change the version and
            // intentionally invalidate this cursor on the next visit.
            let edge_types: Vec<Sym> = self.rules[rule_idx]
                .match_edges
                .iter()
                .map(|me| me.edge_type)
                .collect();
            for et in edge_types {
                let (len, ver) = cursor_frontier_before_apply
                    .get(&et)
                    .copied()
                    .unwrap_or_else(|| {
                        (self.graph.edges_by_type(et).len(), self.cursor_version(et))
                    });
                self.rule_cursors[rule_idx].insert(et, (len, ver));
            }
            res
        };
        let progressed = progressed || wf_pre;
        if self.write_frontier && !progressed {
            // a non-progressing attempt left the graph unchanged (undone writes)
            self.graph.attr_write_log.clear();
            self.graph.edge_write_log.clear();
        }
        crate::fallback_trace::set_current_rule(None);
        if let Some(c) = self.rule_cost_micros.get_mut(rule_idx) {
            *c += __cost_t0.elapsed().as_micros() as u64;
        }
        if let Some(n) = self.rule_cost_count.get_mut(rule_idx) {
            *n += 1;
        }
        if progressed {
            if let Some(p) = self.rule_cost_progress.get_mut(rule_idx) {
                *p += 1;
            }
            // slice (b): wake only the rules that read what `rule_idx`
            // wrote, not every rule. Over-approx write-set ⇒ a superset
            // of true consumers ⇒ correct (never misses), just fewer.
            self.dirty_by_writeset(rule_idx);
            self.any_mutation = true;
            // Effect::DelNode/DelEdge/ReplaceValue go through
            // graph.delete_* directly — bypass Substrate's
            // remove_* which is where edge_delete_version
            // normally gets bumped. Without this nudge, other
            // rules' cursors stay valid and their eval_cache
            // stays poisoned with stale InNeighbours results —
            // where-clause flips driven by deletion (e.g. DCE
            // cascading when a use-count drops to 0) get missed.
            // Bumping here + clearing the relevant eval cache
            // makes the next rule attempt see the fresh post-
            // mutation graph. Only triggered for rules that
            // actually delete; add-only rules keep the fast
            // incremental-cursor path intact.
            let deletes = self.rules[rule_idx].effects.iter().any(|e| {
                matches!(
                    e,
                    crate::rewrite::Effect::DelNode { .. }
                        | crate::rewrite::Effect::DelEdge { .. }
                        | crate::rewrite::Effect::ReplaceValue { .. }
                )
            });
            if deletes {
                self.edge_delete_version += 1;
                // Block 192000: a DelNode cascade can delete edges of edge types
                // this effect list does not name, and a delete can flip a
                // where-clause on a STABLE edge of a rule that reads the deleted
                // type only in its where (not its match) — which per-edge-type
                // versioning alone would not invalidate. The committed engine
                // catches every such case with the global bump above (it
                // invalidates ALL cursors). Match that EXACTLY under ON by
                // clearing every cursor here — conservative and byte-identical.
                // Add-only rules (no delete effect) never reach this block, so
                // they keep the incremental fast path; only a tick containing a
                // delete-effecting rule pays the full invalidation, as it does
                // under OFF.
                if self.incremental_match {
                    let edge_only = self.precise_rule_deletes
                        && self.rules[rule_idx].effects.iter().all(|e| {
                            !matches!(
                                e,
                                crate::rewrite::Effect::DelNode { .. }
                                    | crate::rewrite::Effect::ReplaceValue { .. }
                            )
                        });
                    if edge_only {
                        // DelEdge-only: the deleted types are exactly the named
                        // ones (no cascade). Match-edge readers go stale through
                        // the per-type delete version the graph bumped; clear the
                        // where/term readers and the non-local opaque readers.
                        let ets: smallvec::SmallVec<[Sym; 4]> = self.rules[rule_idx]
                            .effects
                            .iter()
                            .filter_map(|e| match e {
                                crate::rewrite::Effect::DelEdge { edge_type, .. } => Some(*edge_type),
                                _ => None,
                            })
                            .collect();
                        if self.delete_frontier && self.write_frontier {
                            let log = std::mem::take(&mut self.graph.edge_delete_log);
                            self.invalidate_readers_of_deleted_edges(&log);
                        } else {
                            for et in ets {
                                self.invalidate_readers_of_deleted_edge_type(et);
                            }
                        }
                        for j in 0..self.rules.len().min(self.rule_cursors.len()) {
                            if self.rules[j].reads_any_nonlocal {
                                self.rule_dirty[j] = true;
                                self.rule_cursors[j].clear();
                            }
                        }
                    } else {
                        self.graph.edge_delete_log.clear();
                        for c in self.rule_cursors.iter_mut() {
                            c.clear();
                        }
                    }
                }
            }
            // This rule has completed all of its binding evaluations. Its
            // effects may have changed a typed edge read by a later rule in
            // the same pass, so waiting for the next pass boundary leaves
            // graph-dependent Terms (including ReachableFrom) stale for that
            // later rule. Drop the memo now; the next rule must see the graph
            // state it is scheduled against. The per-pass clear remains as a
            // conservative guard for mutations outside this attempt path.
            self.eval_cache.clear_graph_dependent();
        }
        crate::scale_audit::end_rule_enumeration();
        progressed
    }

    /// The area partition, in the CANONICAL order: areas ordered by their
    /// FIRST active rule index, rules within an area in ascending index
    /// order. Identical ordering discipline to `area_scheduler::derive`
    /// (which additionally derives read/write dependencies and SCCs — this
    /// is the O(rules) grouping alone, recomputed each round so a rule
    /// added or tombstoned mid-run is honoured). NEVER hash iteration order.
    fn area_groups(&self) -> Vec<(Sym, Vec<usize>)> {
        let mut pos: FxHashMap<Sym, usize> = FxHashMap::default();
        let mut out: Vec<(Sym, Vec<usize>)> = Vec::new();
        for (idx, rule) in self.rules.iter().enumerate() {
            if !rule.active {
                continue;
            }
            let p = match pos.get(&rule.area) {
                Some(&p) => p,
                None => {
                    out.push((rule.area, Vec::new()));
                    pos.insert(rule.area, out.len() - 1);
                    out.len() - 1
                }
            };
            out[p].1.push(idx);
        }
        out
    }

    /// PER-AREA ASYNC SETTLEMENT (block 186000). **Built ALONGSIDE the global
    /// fixpoint and DEFAULT OFF** — nothing in the committed tree calls this;
    /// `run_rules` / `run_rules_opts` above are UNCHANGED and remain both the
    /// default and the correctness oracle.
    ///
    /// THE AXIOM, MADE MECHANICAL. A cortex tick is a SETTLEMENT EVENT that
    /// CARRIES a residual. One ROUND is one pass over the areas in canonical
    /// order; each area settles as much of its OWN accumulated surprise as its
    /// BUDGET affords, then yields, carrying the rest forward. There is no
    /// global barrier over rules: an area's dirty set is read LIVE when its
    /// turn comes, so surprise a neighbour just wrote is visible in the SAME
    /// round rather than deferred to the next global pass.
    ///
    /// An area's turn processes the dirty set it holds AT THE MOMENT ITS TURN
    /// COMES (its own snapshot, taken on its own clock — not a barrier read of
    /// a global state), up to `budget_per_area` PROGRESSING steps. Work the
    /// budget did not reach, and work re-dirtied during its own turn, both
    /// carry to the next round. `budget_per_area == 0` means UNBOUNDED — settle
    /// the whole of this round's dirty set. That is THE REDUCTION arm: with an
    /// unbounded budget the mechanism must reproduce the global fixpoint's
    /// final state, which is what makes it a generalisation rather than a
    /// different system. Note this is NOT a run-to-local-fixed-point: an area
    /// yields after its snapshot, exactly as the committed loop yields after
    /// its `to_try` snapshot, so a self-re-dirtying non-idempotent rule cannot
    /// spin inside one area's turn.
    ///
    /// COMPUTE ∝ SURPRISE AT THE AREA GRAIN. An area holding no dirty rule is
    /// skipped by a single `is_empty()` test — it does no matching, no
    /// where-evaluation, no apply. Cross-area surprise propagation is the
    /// committed `dirty_by_writeset` (writer's over-approximated write-set ∩
    /// reader's read-set), i.e. event-causal and per-rule; it is NOT a
    /// barrier and NOT a whole-graph scan.
    ///
    /// THE RESIDUAL IS CARRIED, NEVER FROZEN. Block 185000's Branch-B negative
    /// established that shedding a residual by FREEZING its reference
    /// FABRICATES surprise (a deferred retina cell departing from a frozen
    /// adapted floor manufactured spurious onsets). Here a budget-deferred
    /// rule keeps its dirty bit and nothing whatsoever about the graph it will
    /// later read is altered — the deferral is in the SCHEDULE, never in the
    /// state. `drop_residual = true` is the FALSIFIER arm: it discards the
    /// unreached bits instead, and must diverge.
    pub fn run_rules_settle(
        &mut self,
        budget_per_area: usize,
        max_rounds: usize,
        drop_residual: bool,
        snapshot_round: bool,
    ) -> SettleReport {
        // Same per-tick counter reset as the committed fixpoint.
        self.shape_pruned_count = 0;
        self.counters.derivation_shape_pruned = 0;
        self.counters.concept_shape_pruned = 0;

        let mut report = SettleReport::default();
        let cap = if budget_per_area == 0 {
            usize::MAX
        } else {
            budget_per_area
        };

        for _round in 0..max_rounds {
            // Between-pass drains — identical to `run_rules_opts`'s, and for
            // the identical reason: these queues are filled by effects and can
            // only be applied where `&mut self.rules` is freely borrowable.
            if !self.graph.pending_rule_edits.is_empty() {
                self.apply_pending_rule_edits();
            }
            if !self.graph.pending_rule_patches.is_empty() {
                self.apply_pending_rule_patches();
            }
            if !self.graph.pending_fb_samples.is_empty() {
                self.apply_pending_fb_samples();
            }
            if !self.graph.pending_track_identity.is_empty() {
                self.apply_pending_track_identity();
            }
            if !self.graph.pending_net_collapses.is_empty() {
                self.apply_pending_net_collapses();
            }
            // Externally-fed rules re-arm every round (see `reads_external`).
            for i in 0..self.rules.len() {
                if self.rules[i].reads_external && self.rules[i].active {
                    self.rule_dirty[i] = true;
                }
            }
            if self.any_mutation {
                self.eval_cache.clear_graph_dependent();
            }
            self.any_mutation = false;

            // THE ONE REMAINING CHOICE ABOUT SYNCHRONY, MADE EXPLICIT.
            //
            // `snapshot_round = false` (the ASYNC form): each area reads its
            // own dirty set at the moment ITS turn comes, so surprise a
            // neighbour wrote earlier THIS round is visible to it now. There is
            // no barrier anywhere.
            //
            // `snapshot_round = true` (the BARRIER form): every area's dirty
            // set is read ONCE at round start, so a round attempts exactly the
            // rule multiset one committed global pass would, merely permuted
            // into area-major order. Work dirtied DURING the round carries to
            // the next round. This is the arm that can be byte-identical to the
            // committed fixpoint; the difference between the two arms is the
            // honest measure of how much of the fixpoint's answer depends on
            // the barrier.
            let snap: Option<Vec<bool>> = if snapshot_round {
                let s: Vec<bool> = (0..self.rules.len())
                    .map(|i| self.rule_dirty[i] && self.rules[i].active)
                    .collect();
                for (i, &d) in s.iter().enumerate() {
                    if d {
                        self.rule_dirty[i] = false;
                    }
                }
                Some(s)
            } else {
                None
            };

            let groups = self.area_groups();
            if report.areas.is_empty() {
                report.areas = groups.iter().map(|(a, _)| *a).collect();
            }

            let mut round = SettleRound::default();
            let mut any_progress = false;
            for (area, rule_indices) in groups.iter() {
                // THE AREA-GRAIN DIRTY TEST. A quiet area's ENTIRE cost is
                // this scan of its own rule-index list; it never touches the
                // graph. "An area with NO dirty input does NO work."
                let dirty_now: Vec<usize> = match &snap {
                    Some(s) => rule_indices.iter().copied().filter(|&i| s[i]).collect(),
                    None => rule_indices
                        .iter()
                        .copied()
                        .filter(|&i| self.rule_dirty[i] && self.rules[i].active)
                        .collect(),
                };
                if dirty_now.is_empty() {
                    continue;
                }
                round.dirty_areas += 1;
                let mut spent = 0usize;
                let mut attempted = 0usize;
                let mut idx = 0usize;
                while idx < dirty_now.len() && spent < cap {
                    let ri = dirty_now[idx];
                    idx += 1;
                    // Clear BEFORE the attempt, exactly as the committed loop
                    // clears its whole `to_try` snapshot before firing: a rule
                    // that re-dirties itself via `dirty_by_writeset` then
                    // re-enters the residual honestly rather than being
                    // silently retired.
                    self.rule_dirty[ri] = false;
                    attempted += 1;
                    if self.attempt_one_rule(ri) {
                        spent += 1;
                        report.steps += 1;
                        round.steps += 1;
                        any_progress = true;
                    }
                }
                // THE RESIDUAL — what the budget did not reach.
                let mut carried = 0usize;
                while idx < dirty_now.len() {
                    let ri = dirty_now[idx];
                    idx += 1;
                    if drop_residual {
                        // FALSIFIER ARM: shed it. The work is LOST.
                        self.rule_dirty[ri] = false;
                    } else {
                        // CARRIED: the bit is (re-)set so the next round sees
                        // it. Nothing about the graph this rule will read is
                        // frozen — the deferral is in the SCHEDULE, never in
                        // the state. (Under the barrier form the bit was
                        // cleared at the round snapshot, so carrying is an
                        // explicit re-set; under the async form it was never
                        // cleared and this is a no-op. Both are "carried".)
                        self.rule_dirty[ri] = true;
                        carried += 1;
                    }
                }
                round.rows.push(AreaSettleRow {
                    area: *area,
                    dirty: dirty_now.len(),
                    attempted,
                    steps: spent,
                    carried,
                });
            }
            // The account's residual AFTER this settlement event: every dirty
            // active rule still standing, whatever set it.
            round.residual = self
                .rule_dirty
                .iter()
                .enumerate()
                .filter(|&(i, &d)| d && self.rules[i].active)
                .count();
            report.rounds.push(round);
            if !any_progress {
                return report;
            }
        }
        report.hit_max_rounds = true;
        report
    }

    /// Relabel one rule's AREA. Scheduling metadata only: no committed code
    /// path reads `rule.area` (the default fixpoint iterates rule INDICES),
    /// so this cannot move any default behaviour — it changes only which
    /// group `run_rules_settle` settles the rule in. Mechanical, so a
    /// measurement can split an existing seed's rules across areas without
    /// editing committed seed data. Returns whether a rule was found.
    pub fn set_rule_area(&mut self, name: Sym, area: Sym) -> bool {
        let mut found = false;
        let mut changed = false;
        for r in self.rules.iter_mut() {
            if r.name == name && r.active {
                changed |= r.area != area || !r.schedule_explicit;
                r.area = area;
                r.schedule_explicit = true;
                found = true;
            }
        }
        // Area assignment affects `run_rules_settle` scheduling, so it is a
        // semantic rule-store edit for experiment revision/conflict checks.
        if changed { self.gamma_epoch.bump(); }
        found
    }

    /// The committed fixpoint runner. UNCHANGED SEMANTICS — runs to an
    /// exact fixed point (or the cap), exactly as every seed has always
    /// seen it. PROTOCOL §9: the new termination semantics ships OFF by
    /// default, so every committed result reproduces byte-identically.
    pub fn run_rules(&mut self, max_steps: usize) -> usize {
        self.run_rules_opts(max_steps, false)
    }

    /// Structured, additive variant of [`Substrate::run_rules`]. Unlike the
    /// legacy integer result, this distinguishes an observed fixed point, an
    /// opt-in repeated graph state, and a pass-boundary progress-budget exit.
    pub fn run_rules_report(
        &mut self,
        max_steps: usize,
        detect_cycles: bool,
    ) -> RuleRunReport {
        self.run_rules_opts_report_filtered(max_steps, detect_cycles, None)
    }

    /// Begin a conversation-scoped capture of the last rule that progresses.
    /// Reopening intentionally discards an uncommitted prior window.
    pub fn begin_turn_rule_firing_capture(&mut self) {
        self.rule_firing_capture_active = true;
        self.pending_turn_last_progress_rule = None;
    }

    fn capture_turn_rule_progress(&mut self, rule: Option<Sym>) {
        if self.rule_firing_capture_active {
            if let Some(rule) = rule {
                self.pending_turn_last_progress_rule = Some(rule);
            }
        }
    }

    /// Commit the last native rule-progress fact from the open conversation
    /// into a bounded, graph-resident latest-event ledger. This direct
    /// telemetry write deliberately does not schedule another cognition pass:
    /// the next inbound utterance is the event that makes query rules eligible.
    pub fn commit_turn_rule_firing_capture(
        &mut self,
        inbound: NodeID,
        agent: NodeID,
    ) -> Option<NodeID> {
        self.rule_firing_capture_active = false;
        let rule = self.pending_turn_last_progress_rule.take()?;
        let ledger_type = self.interner.intern("RuleFiringHistory");
        let nodes = self.graph.nodes_of_type(ledger_type);
        let ledger = nodes.first().copied().unwrap_or_else(|| {
            self.graph
                .insert_node(ledger_type, FxHashMap::default())
        });
        let name_key = self.interner.intern("last_rule_name");
        let turn_key = self.interner.intern("last_inbound_message_id");
        let seq_key = self.interner.intern("settlement_sequence");
        let schema_key = self.interner.intern("schema");
        let last_rule_name = self.interner.resolve(rule).to_owned();
        let last_rule_name = self.interner.intern(&last_rule_name);
        let schema_value = self.interner.intern("rule_firing_history.v1");
        let sequence = match self.graph.node(ledger).attrs.get(&seq_key) {
            Some(Value::Int(value)) => value.saturating_add(1),
            _ => 1,
        };
        self.graph.set_node_attr(
            ledger,
            schema_key,
            Value::Str(schema_value),
        );
        self.graph.set_node_attr(
            ledger,
            name_key,
            Value::Str(last_rule_name),
        );
        self.graph
            .set_node_attr(ledger, turn_key, Value::Int(inbound.0 as i64));
        self.graph
            .set_node_attr(ledger, seq_key, Value::Int(sequence));
        if self.graph.has_node(agent) {
            let history_edge = self.interner.intern("has_rule_firing_history");
            if !self.graph.has_edge(agent, history_edge, ledger) {
                let _ = self.graph.insert_edge(
                    agent,
                    history_edge,
                    ledger,
                    FxHashMap::default(),
                );
            }
        }
        Some(ledger)
    }

    /// Collect conservative graph write targets at mutation sites. This
    /// observer covers graph mutations performed directly and by deferred
    /// effects drained inside settlement. Mutable accessors may over-report
    /// no-op writes; all reported IDs are safe candidates for notification.
    pub fn run_rules_delta_report(
        &mut self,
        max_steps: usize,
        detect_cycles: bool,
    ) -> RuleGraphDeltaReport {
        self.graph.begin_mutation_log();
        let run = self.run_rules_report(max_steps, detect_cycles);
        let log = self.graph.finish_mutation_log();
        let prior_types = log.node_types;
        let mut affected_nodes: Vec<NodeID> = log.changed_nodes.into_iter().collect();
        affected_nodes.sort_unstable();
        let mut affected_edges: Vec<EdgeKey> = log.changed_edges.into_iter().collect();
        affected_edges.sort_unstable_by_key(|key| (key.src, key.edge_type, key.tgt));
        let mt_type = self.interner.intern("Microtheory");
        let has_concept = self.interner.intern("has_concept");
        let affected_microtheories = map_affected_microtheories(
            &self.graph,
            mt_type,
            has_concept,
            &affected_nodes,
            &affected_edges,
            &prior_types,
        );
        RuleGraphDeltaReport {
            run,
            affected_nodes,
            affected_edges,
            affected_microtheories,
            exact_graph_state_diff: false,
        }
    }

    /// Rule settlement with an EXACT net edge change, restricted to
    /// `edge_types`, plus the touched nodes restricted to `node_types`.
    /// The graph keeps the first-seen state of every touched edge (edge
    /// before-images only, O(touched edges)); an edge whose existence after
    /// the run differs from its first-seen state is reported as
    /// `(key, exists_now)`. Edges added and deleted within the run, and
    /// attr-only rewrites of an existing edge, are not net changes.
    /// Touched nodes are conservative (as `run_rules_delta_report`).
    pub fn run_rules_edge_delta(
        &mut self,
        max_steps: usize,
        detect_cycles: bool,
        edge_types: &[String],
        node_types: &[String],
    ) -> (RuleRunReport, Vec<(NodeID, Sym)>, Vec<(EdgeKey, bool)>) {
        self.graph.begin_edge_before_log();
        let run = self.run_rules_report(max_steps, detect_cycles);
        let log = self.graph.finish_mutation_log();
        // resolved AFTER the run: a type first interned by the run is included
        let edge_types: Vec<Sym> = edge_types.iter().filter_map(|t| self.interner.lookup(t)).collect();
        let node_types: Vec<Sym> = node_types.iter().filter_map(|t| self.interner.lookup(t)).collect();
        let mut nodes: Vec<(NodeID, Sym)> = log
            .changed_nodes
            .into_iter()
            .filter_map(|nid| {
                let ty = if self.graph.has_node(nid) {
                    Some(self.graph.node(nid).type_)
                } else {
                    log.node_types.get(&nid).copied()
                };
                ty.filter(|t| node_types.contains(t)).map(|t| (nid, t))
            })
            .collect();
        nodes.sort_unstable();
        let mut edges: Vec<(EdgeKey, bool)> = log
            .before_edges
            .unwrap_or_default()
            .into_iter()
            .filter(|(key, _)| edge_types.contains(&key.edge_type))
            .filter_map(|(key, before)| {
                let now = self.graph.has_edge(key.src, key.edge_type, key.tgt);
                (now != before.is_some()).then_some((key, now))
            })
            .collect();
        edges.sort_unstable_by_key(|(key, _)| (key.src, key.edge_type, key.tgt));
        (run, nodes, edges)
    }

    /// Exact graph-content diff oracle for validating the mutation-site
    /// observer. This is O(V+E) and intentionally separate from the report
    /// method used to collect candidate notifications.
    pub fn run_rules_snapshot_delta_report(
        &mut self,
        max_steps: usize,
        detect_cycles: bool,
    ) -> RuleGraphDeltaReport {
        let (before_nodes, before_edges) = snapshot_graph_content(&self.graph);
        let run = self.run_rules_report(max_steps, detect_cycles);
        let (after_nodes, after_edges) = snapshot_graph_content(&self.graph);

        let mut changed_nodes = rustc_hash::FxHashSet::default();
        let node_ids: rustc_hash::FxHashSet<NodeID> = before_nodes
            .keys()
            .chain(after_nodes.keys())
            .copied()
            .collect();
        for nid in node_ids {
            if before_nodes.get(&nid) != after_nodes.get(&nid) {
                changed_nodes.insert(nid);
            }
        }

        let edge_keys: rustc_hash::FxHashSet<EdgeKey> = before_edges
            .keys()
            .chain(after_edges.keys())
            .copied()
            .collect();
        let mut changed_edges = Vec::new();
        for key in edge_keys {
            if before_edges.get(&key) != after_edges.get(&key) {
                changed_nodes.insert(key.src);
                changed_nodes.insert(key.tgt);
                changed_edges.push(key);
            }
        }
        let mut affected_nodes: Vec<NodeID> = changed_nodes.into_iter().collect();
        affected_nodes.sort_unstable();
        changed_edges.sort_unstable_by_key(|key| (key.src, key.edge_type, key.tgt));
        let prior_types: FxHashMap<NodeID, Sym> = before_nodes
            .iter()
            .map(|(&nid, (node_type, _))| (nid, *node_type))
            .collect();
        let mt_type = self.interner.intern("Microtheory");
        let has_concept = self.interner.intern("has_concept");
        let affected_microtheories = map_affected_microtheories(
            &self.graph,
            mt_type,
            has_concept,
            &affected_nodes,
            &changed_edges,
            &prior_types,
        );
        RuleGraphDeltaReport {
            run,
            affected_nodes,
            affected_edges: changed_edges,
            affected_microtheories,
            exact_graph_state_diff: true,
        }
    }

    /// Apply one graph-resident, integer trajectory-control feedback step.
    ///
    /// `TrajectoryControlState` is deliberately a small native scheduling
    /// seam rather than a Python callback. A graph rule (or the world
    /// adapter's mechanical observation ingest) publishes the current
    /// `deviation_count`; this method performs the discrete controller update
    /// during the native cycle and clamps the tangent width to its envelope.
    /// Missing control state is a no-op, preserving ordinary substrate
    /// semantics.
    pub fn apply_trajectory_control(&mut self) -> usize {
        let state_type = self.interner.intern("TrajectoryControlState");
        let enabled_key = self.interner.intern("enabled");
        let deviation_key = self.interner.intern("deviation_count");
        let wide_key = self.interner.intern("deviation_wide_quanta");
        let converge_key = self.interner.intern("deviation_converge_quanta");
        let width_key = self.interner.intern("tangent_width");
        let legacy_width_key = self.interner.intern("width");
        let min_key = self.interner.intern("min_tangent_width");
        let max_key = self.interner.intern("max_tangent_width");
        let legacy_max_key = self.interner.intern("max_width");
        let widen_key = self.interner.intern("widen_step");
        let narrow_key = self.interner.intern("narrow_step");
        let previous_key = self.interner.intern("previous_tangent_width");
        let adjustment_key = self.interner.intern("tangent_width_adjustment");
        let epoch_key = self.interner.intern("trajectory_control_epoch");

        let enabled = |value: Option<&Value>| match value {
            None => true,
            Some(Value::Bool(v)) => *v,
            Some(Value::Int(v)) => *v != 0,
            Some(Value::Float(v)) => *v != 0.0,
            _ => false,
        };
        let integer = |attrs: &crate::graph::Attrs, key: Sym, fallback: i64| match attrs.get(&key) {
            Some(Value::Int(v)) => *v,
            Some(Value::Float(v)) if v.is_finite() => *v as i64,
            _ => fallback,
        };

        let mut updates = Vec::new();
        for state in self.graph.nodes_of_type(state_type) {
            let attrs = &self.graph.node(state).attrs;
            if !enabled(attrs.get(&enabled_key)) {
                continue;
            }
            let Some(deviation) = attrs.get(&deviation_key).and_then(|value| match value {
                Value::Int(v) => Some(*v),
                Value::Float(v) if v.is_finite() => Some(*v as i64),
                _ => None,
            }) else {
                continue;
            };
            let width = integer(attrs, width_key, integer(attrs, legacy_width_key, 0));
            let min_width = integer(attrs, min_key, 0);
            let max_width =
                integer(attrs, max_key, integer(attrs, legacy_max_key, 2)).max(min_width);
            let widen = integer(attrs, widen_key, 1).max(1);
            let narrow = integer(attrs, narrow_key, 1).max(1);
            let wide_threshold = integer(attrs, wide_key, 1);
            let converge_threshold = integer(attrs, converge_key, 0);
            let next = if deviation >= wide_threshold {
                width.saturating_add(widen)
            } else if deviation <= converge_threshold {
                width.saturating_sub(narrow)
            } else {
                width
            }
            .clamp(min_width, max_width);
            let adjustment = next.saturating_sub(width);
            if adjustment == 0 {
                continue;
            }
            updates.push((state, width, next, adjustment));
        }

        for (state, previous, next, adjustment) in &updates {
            self.set_attr(*state, width_key, Value::Int(*next));
            self.set_attr(*state, previous_key, Value::Int(*previous));
            self.set_attr(*state, adjustment_key, Value::Int(*adjustment));
            let epoch = self
                .graph
                .node(*state)
                .attrs
                .get(&epoch_key)
                .and_then(|value| match value {
                    Value::Int(v) => Some(*v),
                    Value::Float(v) if v.is_finite() => Some(*v as i64),
                    _ => None,
                })
                .unwrap_or(0);
            self.set_attr(*state, epoch_key, Value::Int(epoch.saturating_add(1)));
        }
        updates.len()
    }

    /// Settle only rules in one authored deadline class.
    ///
    /// This is the scheduling primitive used by the dual-process cognitive
    /// cycle: `hard_realtime` rules constitute the continuously available
    /// System-1 sheet.  Rules outside the requested class retain their dirty
    /// bits; the scheduler has deferred them, not discarded their residual.
    /// A later unfiltered pass therefore sees exactly the work that was held
    /// back.  The ordinary `run_rules[_opts]` path passes no filter and keeps
    /// its committed semantics.
    pub fn run_rules_latency_opts(
        &mut self,
        latency_class: Sym,
        max_steps: usize,
        detect_cycles: bool,
    ) -> usize {
        self.run_rules_opts_filtered(max_steps, detect_cycles, Some(latency_class))
    }

    /// `run_rules` with CYCLE DETECTION optionally enabled.
    ///
    /// `detect_cycles = false` is byte-for-byte the committed loop: the
    /// fingerprint is never computed and no state is kept, so a seed that
    /// does not opt in pays NOTHING and cannot move.
    ///
    /// `detect_cycles = true` additionally stops when the graph re-enters a
    /// state it has already been in. Rationale (see
    /// `TypedGraph::state_fingerprint`): rule application is a DETERMINISTIC
    /// map on graph state, so a repeated state proves the trajectory is
    /// periodic and can never reach a new state — continuing to the cap
    /// cannot discover anything. Terminating there returns the same answer
    /// the cap would, only sooner and without burning 200,000 applications
    /// on a sheet that settled to 1e-16.
    ///
    /// WHAT THIS DOES AND DOES NOT CHANGE. A run that currently ends on
    /// no-progress is a TRUE fixed point (period 1); `!any_progress` fires
    /// first and returns before any fingerprint is ever compared, so such a
    /// run is untouched even with detection ON. Only a run that currently
    /// BURNS THE CAP can end anywhere new — and those runs are already
    /// returning an arbitrary phase of an orbit.
    ///
    /// SOUNDNESS CAVEAT, STATED RATHER THAN ASSUMED: determinism is the
    /// premise. The engine's only randomness is a SEEDED xorshift (`apc.rs`),
    /// which is deterministic per seed. An effect that read genuinely
    /// external mutable state (a live framebuffer via `reads_external`)
    /// between passes could revisit a graph state and still have somewhere
    /// new to go — so detection is opt-in per call, never global.
    pub fn run_rules_opts(&mut self, max_steps: usize, detect_cycles: bool) -> usize {
        self.run_rules_opts_filtered(max_steps, detect_cycles, None)
    }

    fn run_rules_opts_filtered(
        &mut self,
        max_steps: usize,
        detect_cycles: bool,
        latency_filter: Option<Sym>,
    ) -> usize {
        self.run_rules_opts_report_filtered(max_steps, detect_cycles, latency_filter)
            .progress_steps
    }

    fn run_rules_opts_report_filtered(
        &mut self,
        max_steps: usize,
        detect_cycles: bool,
        latency_filter: Option<Sym>,
    ) -> RuleRunReport {
        let work_scope = &self.graph as *const crate::graph::TypedGraph as usize;
        let _work_operation = crate::access_trace::begin_work_operation(work_scope);
        // Per-tick Shape-pruning counters: cleared at run_rules start
        // so callers can read the savings earned during this tick rather
        // than cumulative. Vocabulary: every tick is the
        // L6 bounded_coordination_latency loop; per-tick measurement
        // matches the substrate's natural reporting cadence.
        self.shape_pruned_count = 0;
        self.counters.derivation_shape_pruned = 0;
        self.counters.concept_shape_pruned = 0;

        // Visited-state fingerprints. Allocated ONLY when detection is on,
        // so the default path pays not even an empty set's construction.
        let mut seen: Option<rustc_hash::FxHashSet<u64>> = if detect_cycles {
            Some(Default::default())
        } else {
            None
        };
        if let Some(s) = seen.as_mut() {
            // The ENTRY state counts: a loop that returns to where it
            // started is a cycle like any other.
            s.insert(self.graph.state_fingerprint());
        }

        let mut steps = 0;
        let mut passes_completed = 0;
        let mut last_progress_rule = None;
        while steps < max_steps {
            passes_completed += 1;
            crate::scale_audit::scheduler_pass_started();
            // INTRINSIC SELF-REPAIR: apply any rule-clause rewrites a SetRuleClause effect queued
            // last pass. Done HERE, between passes, where &mut self.rules is freely borrowable; a
            // rewritten rule is marked dirty so it runs its NEW body this iteration.
            if !self.graph.pending_rule_edits.is_empty() {
                self.apply_pending_rule_edits();
            }
            if !self.graph.pending_rule_patches.is_empty() {
                self.apply_pending_rule_patches();
            }
            // PERCEPTION-AS-ACTION: apply any fb_sample an FbSample effect
            // queued last pass — same "drain between passes" spot as the
            // rule-clause edits just above.
            if !self.graph.pending_fb_samples.is_empty() {
                self.apply_pending_fb_samples();
            }
            // GRAPH LAW #6: apply any trans-frame identity match an
            // Effect::TrackIdentity queued last pass — same "drain
            // between passes" spot as the fb_sample queue just above.
            if !self.graph.pending_track_identity.is_empty() {
                self.apply_pending_track_identity();
            }
            // SELF-TRAINING: apply any surprise-driven weight collapse an
            // Effect::NetCollapse queued last pass — same "drain between
            // passes" spot. The net trains itself INSIDE the collapse loop.
            if !self.graph.pending_net_collapses.is_empty() {
                self.apply_pending_net_collapses();
            }
            let scheduler_audit_on = crate::scale_audit::enabled();
            let scheduler_work_trace_on =
                crate::access_trace::work_capture_enabled_for_scope(work_scope);
            let scheduler_started = scheduler_audit_on.then(std::time::Instant::now);
            let count_fixedpoint_probe = scheduler_audit_on || scheduler_work_trace_on;
            // PERCEPTION-AS-ACTION: force-dirty every rule whose where-clause
            // reads FbFrameSeq. Every OTHER dirty bit here is graph-reactive
            // (set because something the rule reads got WRITTEN); an
            // FbFrameSeq-gated rule's truth value can flip from a live
            // shared-memory writer with ZERO graph mutations in between, so
            // graph-reactive tracking alone would starve it after its first
            // fire (see `RewriteRule::reads_external`'s doc comment). This
            // is a bounded poll (O(rules), only the ones that opted into
            // FbFrameSeq), not a re-introduction of host-decided "when to
            // look" — the RULE still decides whether the poll opens the
            // gate; only the "is it worth re-checking" scheduling is host
            // machinery, exactly like `tick()` itself already is.
            for i in 0..self.rules.len() {
                if self.rules[i].reads_external
                    && self.rules[i].active
                    && latency_filter
                        .map(|class| self.rules[i].latency_class == class)
                        .unwrap_or(true)
                {
                    self.rule_dirty[i] = true;
                }
            }
            // Fast exit: no ACTIVE rule is dirty. A tombstoned rule
            // (`remove_rule`) has its dirty bit cleared at removal time,
            // but a later blanket re-dirty (mark_edge_type_dirty /
            // mark_node_mutation / a writes_any rule firing) doesn't know
            // about removal and can set it again — guard with `active`
            // here too so a removed rule can never stall this exit.
            let mut fixedpoint_probe_slots = 0usize;
            let has_active_dirty = if count_fixedpoint_probe {
                let mut found = false;
                for (i, &dirty) in self.rule_dirty.iter().enumerate() {
                    fixedpoint_probe_slots += 1;
                    if dirty
                        && self.rules[i].active
                        && latency_filter
                            .map(|class| self.rules[i].latency_class == class)
                            .unwrap_or(true)
                    {
                        found = true;
                        break;
                    }
                }
                found
            } else {
                self.rule_dirty.iter().enumerate().any(|(i, &d)| {
                    d && self.rules[i].active
                        && latency_filter
                            .map(|class| self.rules[i].latency_class == class)
                            .unwrap_or(true)
                })
            };
            if !has_active_dirty {
                if scheduler_started.is_some() || scheduler_work_trace_on {
                    let elapsed_ns = scheduler_started.map(|started| {
                        started.elapsed().as_nanos().min(u64::MAX as u128) as u64
                    }).unwrap_or(0);
                    crate::scale_audit::scheduler_plan_completed(
                        self.rules.len(), fixedpoint_probe_slots, 0, 0,
                        elapsed_ns,
                    );
                }
                self.capture_turn_rule_progress(last_progress_rule);
                return RuleRunReport {
                    status: RuleRunStatus::FixedPoint,
                    progress_steps: steps,
                    requested_progress_budget: max_steps,
                    budget_overshoot: steps.saturating_sub(max_steps),
                    passes_completed,
                    cycle_detection_enabled: detect_cycles,
                    last_progress_rule,
                };
            }
            // If any mutation was recorded since the last clean pass,
            // the eval_cache (Filter/Neighbours/Holds memoisation) is
            // stale — drop it. Cheap: hashmap clear amortises across
            // many rule firings that would otherwise miss.
            if self.any_mutation {
                self.eval_cache.clear_graph_dependent();
            }
            // Snapshot dirty bits for this iteration. Rules marked dirty
            // BY this iteration's effects fire next iteration. Tombstoned
            // rules are excluded — never scheduled, never applied.
            let to_try: Vec<usize> = self
                .rule_dirty
                .iter()
                .enumerate()
                .filter_map(|(i, &d)| {
                    if d && self.rules[i].active
                        && latency_filter
                            .map(|class| self.rules[i].latency_class == class)
                            .unwrap_or(true)
                    {
                        Some(i)
                    } else {
                        None
                    }
                })
                .collect();
            if scheduler_started.is_some() || scheduler_work_trace_on {
                let elapsed_ns = scheduler_started.map(|started| {
                    started.elapsed().as_nanos().min(u64::MAX as u128) as u64
                }).unwrap_or(0);
                crate::scale_audit::scheduler_plan_completed(
                    self.rules.len(),
                    fixedpoint_probe_slots,
                    self.rule_dirty.len(),
                    to_try.len(),
                    elapsed_ns,
                );
            }
            // TRACE: is the watched rule even DIRTY this pass? (if it never appears, it's never tried —
            // its read-set didn't see the mutation; if it appears but doesn't progress, the match/where fails.)
            if std::env::var("SUBSTRATE_TRACE_RULE").is_ok() {
                for i in 0..self.rules.len() {
                    if self.dbg_traced(i) {
                        eprintln!(
                            "[TRACE-RR] step {}: {} dirty={} has_where={} reads_any={}",
                            steps,
                            self.interner.resolve(self.rules[i].name),
                            self.rule_dirty[i],
                            self.rule_has_where.get(i).copied().unwrap_or(false),
                            self.rules[i].reads_any
                        );
                    }
                }
            }
            // Clear bits — they'll be re-set if this iteration's effects
            // mutate types those rules read. Without this clear, a fired
            // rule would re-mark itself perpetually.
            for &i in &to_try {
                self.rule_dirty[i] = false;
            }
            self.any_mutation = false;

            let mut any_progress = false;
            for rule_idx in to_try {
                if self.attempt_one_rule(rule_idx) {
                    steps += 1;
                    any_progress = true;
                    let rule_name = self.rules[rule_idx].name;
                    last_progress_rule = Some(rule_name);
                    self.record_rule_state_trace(rule_name, passes_completed, steps);
                }
            }
            if !any_progress {
                // No dirty rule progressed; further iterations would
                // re-check the same clean state. Exit.
                self.capture_turn_rule_progress(last_progress_rule);
                return RuleRunReport {
                    status: RuleRunStatus::FixedPoint,
                    progress_steps: steps,
                    requested_progress_budget: max_steps,
                    budget_overshoot: steps.saturating_sub(max_steps),
                    passes_completed,
                    cycle_detection_enabled: detect_cycles,
                    last_progress_rule,
                };
            }
            // CYCLE DETECTION (opt-in). This pass progressed, so the
            // committed loop would iterate again. If the state it landed on
            // is one we have ALREADY been in, the map — being deterministic —
            // will now replay the identical sequence forever. Stop.
            //
            // Placed AFTER the `!any_progress` exit so a true fixed point
            // still returns by the committed path, byte-identically.
            if let Some(s) = seen.as_mut() {
                if !s.insert(self.graph.state_fingerprint()) {
                    self.capture_turn_rule_progress(last_progress_rule);
                    return RuleRunReport {
                        status: RuleRunStatus::RepeatedGraphState,
                        progress_steps: steps,
                        requested_progress_budget: max_steps,
                        budget_overshoot: steps.saturating_sub(max_steps),
                        passes_completed,
                        cycle_detection_enabled: detect_cycles,
                        last_progress_rule,
                    };
                }
            }
        }
        self.capture_turn_rule_progress(last_progress_rule);
        RuleRunReport {
            status: RuleRunStatus::ProgressBudgetReached,
            progress_steps: steps,
            requested_progress_budget: max_steps,
            budget_overshoot: steps.saturating_sub(max_steps),
            passes_completed,
            cycle_detection_enabled: detect_cycles,
            last_progress_rule,
        }
    }

    /// PER-MT SCOPED fixpoint (CAN_MT_SCOPED_RULES_PREREG/RESULTS.md).
    /// **ADDITIVE ONLY — nothing above this method in the file is touched
    /// by this rung.**
    ///
    /// `scope_mt = None` calls the EXISTING `run_rules_opts` directly — the
    /// SAME call `run_rules`/`run_rules_opts` callers have always made, so
    /// this arm cannot diverge from committed behaviour by construction
    /// (not merely "should match": it IS the same code path). This is the
    /// single most important correctness property this method has to hold,
    /// per the task's own framing, and it holds trivially here because
    /// there is no new code on this path at all.
    ///
    /// `scope_mt = Some(mt)` restricts the fixpoint to bindings that TOUCH
    /// `mt`'s owned nodes (`mt` itself + every node one `has_concept` hop
    /// away — `can_ops.rs::mt_concepts`'s own membership definition,
    /// reused). This calls `rewrite::run_rules_opts_scoped`, a SEPARATE,
    /// freshly-written loop that does NOT reuse `attempt_one_rule`'s
    /// incremental-cursor / predicate-retraction / projection-cold-path
    /// machinery (see PREREG §0 for why: that machinery is keyed on
    /// per-rule state with no per-Mt dimension today, and retrofitting one
    /// is out of scope for this rung's blast-radius discipline). Every rule
    /// is fully re-matched every pass — slower than the incremental engine,
    /// but correct, and it shares zero mutable state with the existing
    /// dirty-bit scheduler, so it cannot desynchronise it either.
    ///
    /// Active rules only (tombstoned rules are excluded, matching
    /// `run_rules_opts_filtered`'s own `self.rules[i].active` guard).
    /// The scoped runner receives borrowed rule references while disjoint
    /// graph/Term/concept fields are mutably borrowed. This avoids cloning
    /// every active rule on every scoped call without retaining a cache whose
    /// invalidation would be unsound while `rules` is publicly mutable.
    pub fn run_rules_scoped(
        &mut self,
        max_steps: usize,
        detect_cycles: bool,
        scope_mt: Option<NodeID>,
    ) -> usize {
        let mt = match scope_mt {
            None => return self.run_rules_opts(max_steps, detect_cycles),
            Some(mt) => mt,
        };
        let has_concept = self.interner.intern("has_concept");
        let owned = crate::rewrite::mt_owned_nodes(&self.graph, mt, has_concept);
        let rule_refs: Vec<(u32, &crate::rewrite::RewriteRule)> = self
            .rules
            .iter()
            .enumerate()
            .filter(|(_, r)| r.active)
            .map(|(i, rule)| (i as u32, rule))
            .collect();
        let has_concept = self.interner.intern("has_concept");
        crate::rewrite::run_rules_opts_scoped(
            &rule_refs,
            &mut self.terms,
            &mut self.graph,
            &mut self.interner,
            Some(&mut self.concepts),
            Some(&self.framebuffers),
            Some(&mut self.eval_cache),
            max_steps,
            detect_cycles,
            mt,
            has_concept,
            &owned,
        )
    }

    /// Diagnostic microbenchmark for the former active-rule snapshot used by
    /// scoped closure. It performs the same enumerate/filter/clone collection
    /// and drops each result; timing therefore includes allocation/destruction
    /// with cloning. The scoped runner now borrows live rules and does not call
    /// this counterfactual profiler. It neither executes rules nor changes state.
    pub fn profile_scoped_rule_snapshot(&self, iterations: usize) -> (usize, usize, u128) {
        let active_count = self.rules.iter().filter(|rule| rule.active).count();
        let started = std::time::Instant::now();
        let mut copied_total = 0usize;
        for _ in 0..iterations {
            let cloned_rules: Vec<(u32, crate::rewrite::RewriteRule)> = self
                .rules.iter().enumerate().filter(|(_, rule)| rule.active)
                .map(|(index, rule)| (index as u32, rule.clone())).collect();
            copied_total += cloned_rules.len();
            std::hint::black_box(&cloned_rules);
        }
        (active_count, copied_total, started.elapsed().as_nanos())
    }

    /// Opt-in Microtheory-scoped closure with native graph write-target
    /// reporting. This shares `run_rules_scoped`'s matching semantics and
    /// current deferred-queue limitation; a nonempty deferred queue is
    /// surfaced explicitly so callers cannot treat it as a settled frame.
    pub fn run_rules_scoped_delta_report(
        &mut self,
        max_steps: usize,
        detect_cycles: bool,
        scope_mt: NodeID,
    ) -> ScopedRuleGraphDeltaReport {
        let work_scope = &self.graph as *const crate::graph::TypedGraph as usize;
        let _work_operation = crate::access_trace::begin_work_operation(work_scope);
        self.graph.begin_mutation_log();
        let has_concept = self.interner.intern("has_concept");
        let owned = crate::rewrite::mt_owned_nodes(&self.graph, scope_mt, has_concept);
        let rule_refs: Vec<(u32, &crate::rewrite::RewriteRule)> = self
            .rules
            .iter()
            .enumerate()
            .filter(|(_, r)| r.active)
            .map(|(i, rule)| (i as u32, rule))
            .collect();
        let progress_steps = crate::rewrite::run_rules_opts_scoped(
            &rule_refs,
            &mut self.terms,
            &mut self.graph,
            &mut self.interner,
            Some(&mut self.concepts),
            Some(&self.framebuffers),
            Some(&mut self.eval_cache),
            max_steps,
            detect_cycles,
            scope_mt,
            has_concept,
            &owned,
        );
        let log = self.graph.finish_mutation_log();
        let prior_types = log.node_types;
        let mut affected_nodes: Vec<NodeID> = log.changed_nodes.into_iter().collect();
        affected_nodes.sort_unstable();
        let mut affected_edges: Vec<EdgeKey> = log.changed_edges.into_iter().collect();
        affected_edges.sort_unstable_by_key(|key| (key.src, key.edge_type, key.tgt));
        let mt_type = self.interner.intern("Microtheory");
        let has_concept = self.interner.intern("has_concept");
        let affected_microtheories = map_affected_microtheories(
            &self.graph,
            mt_type,
            has_concept,
            &affected_nodes,
            &affected_edges,
            &prior_types,
        );
        let deferred_effects_pending = !self.graph.pending_fb_samples.is_empty()
            || !self.graph.pending_track_identity.is_empty()
            || !self.graph.pending_net_collapses.is_empty()
            || !self.graph.pending_rule_edits.is_empty()
            || !self.graph.pending_rule_patches.is_empty();
        ScopedRuleGraphDeltaReport {
            progress_steps,
            requested_progress_budget: max_steps,
            hit_progress_budget: progress_steps >= max_steps,
            affected_nodes,
            affected_edges,
            affected_microtheories,
            deferred_effects_pending,
        }
    }

    // --- native EYE: segmentation + cross-frame identity tracking ------
    //
    // Factored out of the old `py.rs::segment` PyO3 method body (byte-
    // for-byte the same algorithm — union-find CC over equal-value
    // neighbours, cell-overlap + value-preserving nearest-centroid
    // cross-frame matching, ground-conserved/figure-repointed `within`
    // membership, birth/death) so `fb_sample` can reuse it instead of
    // duplicating it. `py.rs::segment` is now a thin wrapper that calls
    // this.

    /// Segment `values` (row-major `h*w`, one entry per grid cell) into
    /// connected-component Regions AND track identity against whatever
    /// Regions `game` already has (matched by cell-overlap, falling back
    /// to nearest-same-value-centroid for small fast movers), updating
    /// persistent `Region` nodes in place. `cell_ids[r*w+c]` must be the
    /// `.0` of the Cell/WorldInstance node backing that grid position —
    /// callers own minting/reusing those cell nodes (`segment`'s caller
    /// is `world_adapter.py`; `fb_sample`'s caller is this file, via the
    /// `fb_cell_ids` cache on `FbHandle`).
    pub fn segment_and_track(
        &mut self,
        game_nid: NodeID,
        h: usize,
        w: usize,
        values: &[i32],
        cell_ids: &[i64],
    ) {
        // The VALUE carve. Union-find over 4-connected equal-value cells,
        // then hand the components to the shared cross-frame tracker
        // (`track_comps`). Byte-identical to the historical single-method
        // body: the carve is unchanged and the tracking phases moved
        // verbatim into `track_comps` (which the motion carve now reuses).
        use std::collections::{HashMap, HashSet};

        fn find(parent: &mut Vec<usize>, mut x: usize) -> usize {
            while parent[x] != x {
                parent[x] = parent[parent[x]];
                x = parent[x];
            }
            x
        }

        let n = h * w;
        if n == 0 || values.len() != n || cell_ids.len() != n {
            return;
        }

        // --- SEGMENT: union-find 4-connectivity over equal-value neighbours ---
        let mut parent: Vec<usize> = (0..n).collect();
        for idx in 0..n {
            let c = idx % w;
            let r = idx / w;
            if c + 1 < w && values[idx] == values[idx + 1] {
                let a = find(&mut parent, idx);
                let b = find(&mut parent, idx + 1);
                if a != b {
                    parent[a] = b;
                }
            }
            if r + 1 < h && values[idx] == values[idx + w] {
                let a = find(&mut parent, idx);
                let b = find(&mut parent, idx + w);
                if a != b {
                    parent[a] = b;
                }
            }
        }
        let mut groups: HashMap<usize, Vec<usize>> = HashMap::new();
        for idx in 0..n {
            let root = find(&mut parent, idx);
            groups.entry(root).or_default().push(idx);
        }

        let mut comps: Vec<Comp> = Vec::new();
        for (_root, idxs) in groups.into_iter() {
            let value = values[idxs[0]];
            let count = idxs.len() as f64;
            let mut sy = 0.0f64;
            let mut sx = 0.0f64;
            let mut minr = usize::MAX;
            let mut minc = usize::MAX;
            let mut maxr = 0usize;
            let mut maxc = 0usize;
            let mut cells: HashSet<usize> = HashSet::with_capacity(idxs.len());
            for &i in &idxs {
                sy += (i / w) as f64;
                sx += (i % w) as f64;
                if i / w < minr {
                    minr = i / w;
                }
                if i % w < minc {
                    minc = i % w;
                }
                if i / w > maxr {
                    maxr = i / w;
                }
                if i % w > maxc {
                    maxc = i % w;
                }
                cells.insert(i);
            }
            comps.push(Comp {
                value,
                cells,
                count,
                cy: sy / count,
                cx: sx / count,
                minr,
                minc,
                maxr,
                maxc,
            });
        }
        if comps.is_empty() {
            return;
        }
        let mut ground_i = 0usize;
        for (i, cmp) in comps.iter().enumerate() {
            if cmp.count > comps[ground_i].count {
                ground_i = i;
            }
        }

        self.track_comps(game_nid, &comps, ground_i, cell_ids);
    }

    /// SHARED cross-frame tracker. Given the frame's carved `comps` (from
    /// EITHER the value carve `segment_and_track` OR the motion-common-fate
    /// carve `segment_motion_and_track`) and which one is ground, match them
    /// against `game`'s existing `Region`s (overlap -> nearest-same-value
    /// centroid -> velocity-predicted) and update/birth/reap in place. This is
    /// the historical tracking body of `segment_and_track`, moved VERBATIM so
    /// both carves reuse the identical, already-gated machinery.
    fn track_comps(&mut self, game_nid: NodeID, comps: &[Comp], ground_i: usize, cell_ids: &[i64]) {
        use std::collections::{HashMap, HashSet};

        fn num(v: Option<&Value>) -> f64 {
            match v {
                Some(Value::Float(f)) => *f,
                Some(Value::Int(i)) => *i as f64,
                _ => 0.0,
            }
        }

        let s = self;
        let region_t = s.interner.intern("Region");
        let has_region = s.interner.intern("has_region");
        let within = s.interner.intern("within");
        let k_rvalue = s.interner.intern("rvalue");
        let k_count = s.interner.intern("count");
        let k_cy = s.interner.intern("cy");
        let k_cx = s.interner.intern("cx");
        let k_drow = s.interner.intern("drow");
        let k_dcol = s.interner.intern("dcol");
        let k_rid = s.interner.intern("rid");
        let k_changed = s.interner.intern("changed_frame");
        let k_ground = s.interner.intern("is_ground");
        let k_minr = s.interner.intern("minr");
        let k_minc = s.interner.intern("minc");
        let k_maxr = s.interner.intern("maxr");
        let k_maxc = s.interner.intern("maxc");
        let k_frame = s.interner.intern("frame");

        let frame = num(s.graph.node(game_nid).attrs.get(&k_frame));
        let n = cell_ids.len();
        let mut id_to_index: HashMap<i64, usize> = HashMap::with_capacity(n);
        for idx in 0..n {
            id_to_index.insert(cell_ids[idx], idx);
        }

        struct Prior {
            nid: NodeID,
            value: i32,
            cells: HashSet<usize>,
            cy: f64,
            cx: f64,
            count: f64,
            drow: f64,
            dcol: f64,
        }
        let mut priors: Vec<Prior> = Vec::new();
        for r in s.graph.neighbours(game_nid, Some(has_region)) {
            let nd = s.graph.node(r);
            let pval = num(nd.attrs.get(&k_rvalue)) as i32;
            let pcy = num(nd.attrs.get(&k_cy));
            let pcx = num(nd.attrs.get(&k_cx));
            let pcount = num(nd.attrs.get(&k_count));
            // the prior's own last per-frame displacement — the velocity the
            // predictive fallback (Phase B) extrapolates to a predicted centroid.
            let pdrow = num(nd.attrs.get(&k_drow));
            let pdcol = num(nd.attrs.get(&k_dcol));
            let mut pcells: HashSet<usize> = HashSet::new();
            for cnid in s.graph.in_neighbours(r, Some(within)) {
                if let Some(&i) = id_to_index.get(&(cnid.0 as i64)) {
                    pcells.insert(i);
                }
            }
            priors.push(Prior {
                nid: r,
                value: pval,
                cells: pcells,
                cy: pcy,
                cx: pcx,
                count: pcount,
                drow: pdrow,
                dcol: pdcol,
            });
        }

        // ── PHASE A: existing cross-frame matching, DECISION-ONLY ──────────
        //   Byte-identical to the historical single-pass matcher (overlap
        //   first, then nearest-same-value-centroid within `span+2`), except
        //   it only RECORDS each comp's assigned prior (or leaves it None) and
        //   does NOT yet mutate the graph. Deferring mutation lets the
        //   velocity-predictive fallback (Phase B) run AFTER every comp has had
        //   its existing chance — so predictive can ONLY ever claim a prior no
        //   comp matched under the old rules. That makes the whole change
        //   ADDITIVE: any comp that matched a prior before matches the SAME
        //   prior now, and the deferred mutation is byte-identical.
        let mut used: HashSet<usize> = HashSet::new();
        let mut assigned: Vec<Option<usize>> = vec![None; comps.len()];
        for (ci, cmp) in comps.iter().enumerate() {
            let mut best: Option<usize> = None;
            let mut best_ov = 0usize;
            for (pi, p) in priors.iter().enumerate() {
                if used.contains(&pi) || p.value != cmp.value {
                    continue;
                }
                let ov = cmp.cells.intersection(&p.cells).count();
                if ov > best_ov {
                    best_ov = ov;
                    best = Some(pi);
                }
            }
            let mut matched = best.map_or(false, |pi| {
                let m = if cmp.count < priors[pi].count {
                    cmp.count
                } else {
                    priors[pi].count
                };
                2.0 * (best_ov as f64) >= m
            });
            if !matched {
                let span = ((cmp.maxr - cmp.minr).max(cmp.maxc - cmp.minc) + 1) as f64;
                let radius = span + 2.0;
                let mut bc: Option<usize> = None;
                let mut bd = f64::INFINITY;
                for (pi, p) in priors.iter().enumerate() {
                    if used.contains(&pi) || p.value != cmp.value {
                        continue;
                    }
                    let d = (cmp.cy - p.cy).abs() + (cmp.cx - p.cx).abs();
                    if d < bd {
                        bd = d;
                        bc = Some(pi);
                    }
                }
                if let Some(pi) = bc {
                    if bd <= radius {
                        best = Some(pi);
                        matched = true;
                    }
                }
            }
            if matched {
                let pi = best.unwrap();
                used.insert(pi);
                assigned[ci] = Some(pi);
            }
        }

        // ── PHASE B: VELOCITY-PREDICTIVE fallback (additive rescue) ────────
        //   An accelerating object's per-frame centroid jump grows without
        //   bound and eventually exceeds the fixed `span+2` nearest-centroid
        //   radius; Phase A then loses it (death+birth) and the trajectory
        //   fragments. Here, for every comp Phase A left UNMATCHED, match
        //   against each still-unused prior's PREDICTED centroid
        //   (`prior.centroid + prior.per-frame displacement`) instead of its
        //   last centroid. The quantity that must fall within `span+2` is then
        //   no longer the object's full VELOCITY (which grows unboundedly) but
        //   only its ACCELERATION — the residual a constant-velocity prediction
        //   leaves — which for smooth motion is small and roughly constant, so
        //   a smoothly-accelerating object stays associated. FIRST-ORDER
        //   (constant-velocity) prediction only; the acceleration it leaves is
        //   exactly what the radius must absorb.
        //
        //   Guards against FALSE association: (1) Phase A already claimed every
        //   prior any comp matches by overlap or last-centroid, so predictive
        //   can only adopt a genuinely-unclaimed (about-to-die) prior; (2) a
        //   prior with NO established displacement (drow==dcol==0 — a just-born
        //   / first-frame / static object) has NO prediction and is skipped, so
        //   it never over-reaches; (3) the predicted match must still fall
        //   within the same `span+2` radius — clearly better than birth.
        for (ci, cmp) in comps.iter().enumerate() {
            if assigned[ci].is_some() {
                continue;
            }
            let span = ((cmp.maxr - cmp.minr).max(cmp.maxc - cmp.minc) + 1) as f64;
            let radius = span + 2.0;
            let mut bc: Option<usize> = None;
            let mut bd = f64::INFINITY;
            for (pi, p) in priors.iter().enumerate() {
                if used.contains(&pi) || p.value != cmp.value {
                    continue;
                }
                if p.drow == 0.0 && p.dcol == 0.0 {
                    continue;
                }
                let pred_cy = p.cy + p.drow;
                let pred_cx = p.cx + p.dcol;
                let d = (cmp.cy - pred_cy).abs() + (cmp.cx - pred_cx).abs();
                if d < bd {
                    bd = d;
                    bc = Some(pi);
                }
            }
            if let Some(pi) = bc {
                if bd <= radius {
                    used.insert(pi);
                    assigned[ci] = Some(pi);
                }
            }
        }

        // ── PHASE C: apply the assignment — update matched priors in place,
        //   birth the rest, then reap the unmatched (dead) priors. Mutation
        //   only; the set_attr / edge / birth blocks below are byte-identical
        //   to the historical matcher, so a comp assigned its old prior yields
        //   the identical graph (same node id, same drow/dcol, same edges).
        for (ci, cmp) in comps.iter().enumerate() {
            let is_ground = ci == ground_i;
            if let Some(pi) = assigned[ci] {
                let nid = priors[pi].nid;
                s.set_attr(nid, k_rvalue, Value::Float(cmp.value as f64));
                s.set_attr(nid, k_count, Value::Float(cmp.count));
                s.set_attr(nid, k_cy, Value::Float(cmp.cy));
                s.set_attr(nid, k_cx, Value::Float(cmp.cx));
                s.set_attr(nid, k_minr, Value::Float(cmp.minr as f64));
                s.set_attr(nid, k_minc, Value::Float(cmp.minc as f64));
                s.set_attr(nid, k_maxr, Value::Float(cmp.maxr as f64));
                s.set_attr(nid, k_maxc, Value::Float(cmp.maxc as f64));
                let drow = cmp.cy - priors[pi].cy;
                let dcol = cmp.cx - priors[pi].cx;
                s.set_attr(nid, k_drow, Value::Float(drow));
                s.set_attr(nid, k_dcol, Value::Float(dcol));
                let changed = drow != 0.0
                    || dcol != 0.0
                    || cmp.count != priors[pi].count
                    || cmp.value != priors[pi].value;
                if changed {
                    s.set_attr(nid, k_changed, Value::Float(frame));
                }
                s.set_attr(
                    nid,
                    k_ground,
                    Value::Float(if is_ground { 1.0 } else { 0.0 }),
                );
                if is_ground {
                    for &idx in cmp.cells.difference(&priors[pi].cells) {
                        let _ = s.add_edge(
                            NodeID(cell_ids[idx] as u32),
                            within,
                            nid,
                            FxHashMap::default(),
                        );
                    }
                } else {
                    for &idx in priors[pi].cells.difference(&cmp.cells) {
                        s.remove_edge(EdgeKey {
                            src: NodeID(cell_ids[idx] as u32),
                            edge_type: within,
                            tgt: nid,
                        });
                    }
                    for &idx in cmp.cells.difference(&priors[pi].cells) {
                        let _ = s.add_edge(
                            NodeID(cell_ids[idx] as u32),
                            within,
                            nid,
                            FxHashMap::default(),
                        );
                    }
                }
            } else {
                let mut attrs: FxHashMap<Sym, Value> = FxHashMap::default();
                attrs.insert(k_rid, Value::Float((cmp.minr * 10000 + cmp.minc) as f64));
                attrs.insert(k_rvalue, Value::Float(cmp.value as f64));
                attrs.insert(k_count, Value::Float(cmp.count));
                attrs.insert(k_cy, Value::Float(cmp.cy));
                attrs.insert(k_cx, Value::Float(cmp.cx));
                attrs.insert(k_minr, Value::Float(cmp.minr as f64));
                attrs.insert(k_minc, Value::Float(cmp.minc as f64));
                attrs.insert(k_maxr, Value::Float(cmp.maxr as f64));
                attrs.insert(k_maxc, Value::Float(cmp.maxc as f64));
                attrs.insert(k_drow, Value::Float(0.0));
                attrs.insert(k_dcol, Value::Float(0.0));
                let nid = s.add_node(region_t, attrs);
                let _ = s.add_edge(game_nid, has_region, nid, FxHashMap::default());
                for &idx in &cmp.cells {
                    let _ = s.add_edge(
                        NodeID(cell_ids[idx] as u32),
                        within,
                        nid,
                        FxHashMap::default(),
                    );
                }
                s.set_attr(
                    nid,
                    k_ground,
                    Value::Float(if is_ground { 1.0 } else { 0.0 }),
                );
            }
        }
        for (pi, p) in priors.iter().enumerate() {
            if !used.contains(&pi) {
                s.remove_node(p.nid);
            }
        }
    }

    /// MOTION-COMMON-FATE carve (the object-notion carve, block 144000) — the
    /// FIX the real-video probe named. Instead of grouping cells by EXACT EQUAL
    /// grey value (`segment_and_track`, which has no object notion and shatters
    /// natural texture), group the cells that MOVE TOGETHER: a per-cell motion
    /// field (`vy`,`vx`, computed by the caller's block-match SENSOR
    /// `motion_group_world.vector_field` and handed in as mechanical I/O),
    /// flooded by common fate within a tolerance that FALLS OUT of the field's
    /// own dispersion (Otsu), with the STATIC/dominant background as one region.
    /// The resulting components go through the SAME `track_comps` tracker the
    /// value carve uses (persistent Region ids, velocity-predictive matching).
    /// ADDITIVE: the value carve is untouched and remains the default; this is a
    /// separate, opt-in method.
    ///
    /// `value` on each carved Region is the tracker's cross-frame identity key:
    /// 1 for a FIGURE group (moves differently from the dominant motion by more
    /// than the derived tolerance — mo_mint's contrast test), 0 otherwise; the
    /// largest group is ground. The derived tolerance + dominant vector are
    /// written on `game` (`mtol`/`dom_vy`/`dom_vx`) for read-back and the §13
    /// falls-out audit.
    pub fn segment_motion_and_track(
        &mut self,
        game_nid: NodeID,
        h: usize,
        w: usize,
        vy: &[f64],
        vx: &[f64],
        cell_ids: &[i64],
    ) {
        use std::collections::HashMap;

        fn find(parent: &mut Vec<usize>, mut x: usize) -> usize {
            while parent[x] != x {
                parent[x] = parent[parent[x]];
                x = parent[x];
            }
            x
        }

        let n = h * w;
        if n == 0 || vy.len() != n || vx.len() != n || cell_ids.len() != n {
            return;
        }

        // --- per-cell motion dispersion pd = max |v - v_neighbour| over the 4-nbhd
        let mut pd = vec![0.0f64; n];
        for idx in 0..n {
            let c = idx % w;
            let r = idx / w;
            let mut mx = 0.0f64;
            if c + 1 < w {
                let d = vdist(vy, vx, idx, idx + 1);
                if d > mx {
                    mx = d;
                }
            }
            if c > 0 {
                let d = vdist(vy, vx, idx, idx - 1);
                if d > mx {
                    mx = d;
                }
            }
            if r + 1 < h {
                let d = vdist(vy, vx, idx, idx + w);
                if d > mx {
                    mx = d;
                }
            }
            if r > 0 {
                let d = vdist(vy, vx, idx, idx - w);
                if d > mx {
                    mx = d;
                }
            }
            pd[idx] = mx;
        }

        // --- TOLERANCE FALLS OUT (§13): Otsu between-class split over the field's
        //     OWN pd distribution — the same criterion the graph rules in
        //     seeds/vision_motion_group.json (`mo_tol_otsu`) apply. No motion
        //     constant appears in this method.
        let tol = otsu_threshold(&pd);

        // --- COMMON FATE: union-find; merge 4-neighbours whose motion vectors
        //     agree within the derived tolerance. Structurally the value carve's
        //     union-find with `values[a]==values[b]` replaced by `|v_a-v_b|<=tol`.
        let mut parent: Vec<usize> = (0..n).collect();
        for idx in 0..n {
            let c = idx % w;
            let r = idx / w;
            if c + 1 < w && vdist(vy, vx, idx, idx + 1) <= tol {
                let a = find(&mut parent, idx);
                let b = find(&mut parent, idx + 1);
                if a != b {
                    parent[a] = b;
                }
            }
            if r + 1 < h && vdist(vy, vx, idx, idx + w) <= tol {
                let a = find(&mut parent, idx);
                let b = find(&mut parent, idx + w);
                if a != b {
                    parent[a] = b;
                }
            }
        }
        let mut groups: HashMap<usize, Vec<usize>> = HashMap::new();
        for idx in 0..n {
            let root = find(&mut parent, idx);
            groups.entry(root).or_default().push(idx);
        }

        // components carrying their MEAN motion vector
        struct MComp {
            idxs: Vec<usize>,
            mvy: f64,
            mvx: f64,
            count: f64,
        }
        let mut mcomps: Vec<MComp> = Vec::new();
        for (_root, idxs) in groups.into_iter() {
            let count = idxs.len() as f64;
            let mut sy = 0.0f64;
            let mut sx = 0.0f64;
            for &i in &idxs {
                sy += vy[i];
                sx += vx[i];
            }
            mcomps.push(MComp {
                mvy: sy / count,
                mvx: sx / count,
                count,
                idxs,
            });
        }
        if mcomps.is_empty() {
            return;
        }

        // --- REFERENCE FRAME FALLS OUT: the dominant motion is the largest
        //     group's vector (mo_dominant). Order is preserved into `comps`.
        let mut ground_i = 0usize;
        for (i, m) in mcomps.iter().enumerate() {
            if m.count > mcomps[ground_i].count {
                ground_i = i;
            }
        }
        let dom_vy = mcomps[ground_i].mvy;
        let dom_vx = mcomps[ground_i].mvx;

        // --- build shared Comp units. value = 1 (FIGURE) iff the group moves
        //     differently from the dominant motion by more than the SAME
        //     tolerance (one scale binds and separates — mo_mint); else 0.
        let mut comps: Vec<Comp> = Vec::new();
        for m in mcomps.into_iter() {
            let dy = m.mvy - dom_vy;
            let dx = m.mvx - dom_vx;
            let contrast = (dy * dy + dx * dx).sqrt();
            let value = if contrast > tol { 1 } else { 0 };
            let mut sy = 0.0f64;
            let mut sx = 0.0f64;
            let mut minr = usize::MAX;
            let mut minc = usize::MAX;
            let mut maxr = 0usize;
            let mut maxc = 0usize;
            let mut cells: std::collections::HashSet<usize> =
                std::collections::HashSet::with_capacity(m.idxs.len());
            for &i in &m.idxs {
                sy += (i / w) as f64;
                sx += (i % w) as f64;
                if i / w < minr {
                    minr = i / w;
                }
                if i % w < minc {
                    minc = i % w;
                }
                if i / w > maxr {
                    maxr = i / w;
                }
                if i % w > maxc {
                    maxc = i % w;
                }
                cells.insert(i);
            }
            comps.push(Comp {
                value,
                cells,
                count: m.count,
                cy: sy / m.count,
                cx: sx / m.count,
                minr,
                minc,
                maxr,
                maxc,
            });
        }

        // record the DERIVED tolerance + dominant vector on the game node (for
        // read-back and the §13 falls-out audit — never read back into a decision)
        let k_mtol = self.interner.intern("mtol");
        let k_domvy = self.interner.intern("dom_vy");
        let k_domvx = self.interner.intern("dom_vx");
        self.set_attr(game_nid, k_mtol, Value::Float(tol));
        self.set_attr(game_nid, k_domvy, Value::Float(dom_vy));
        self.set_attr(game_nid, k_domvx, Value::Float(dom_vx));

        self.track_comps(game_nid, &comps, ground_i, cell_ids);
    }

    // --- GRAPH LAW #6: domain-general trans-frame identity --------------
    //
    // `segment_and_track` above answers "same thing across frames" for
    // ONE domain (visual regions: pixel cells + 2D centroids). This is
    // the domain-general sibling: the SAME two-phase matching shape
    // (overlap-first, nearest-feature-vector fallback within a radius,
    // greedy no-reuse, birth/death for the leftovers) generalised to an
    // arbitrary feature space read off graph node attrs — see
    // `crate::term::track_identity_correspondence` (the pure matching
    // core, shared with the READ-ONLY `TrackIdentityCorrespondence`
    // Term so a rule's `where`-clause and this mutating method never
    // disagree on what counts as a match) for the algorithm itself.
    // `segment_and_track` is NOT rewritten in terms of this — it stays
    // byte-identical (the visual eye depends on its exact behaviour);
    // what's shared is the SHAPE, not the code.

    /// Mint/persist an `identity_key` attr across two frames' worth of
    /// nodes: for every matched (prev, cur) pair, `cur` inherits `prev`'s
    /// current `identity_key` value (so identity threads through a whole
    /// chain of frames, not just one hop) — if `prev` has never been
    /// stamped yet (the very first frame pair), it's backfilled too, so
    /// BOTH sides of a first-ever match resolve to the same identity
    /// after one call, not only the cur side; for every birth (an
    /// unmatched `cur` item), a fresh globally-unique identity is minted
    /// (`Value::Int(cur_nid.0)`). Deaths (unmatched `prev` items) are
    /// reported but never deleted here — same "the fn only WRITES what
    /// its name says" boundary `SetAttr` keeps; a caller (rule effect or
    /// direct script) decides what a death MEANS for its domain.
    pub fn track_identity(
        &mut self,
        prev_ids: &[NodeID],
        cur_ids: &[NodeID],
        feature_key: Sym,
        category_key: Option<Sym>,
        extent_key: Option<Sym>,
        identity_key: Sym,
        radius: f64,
    ) -> TrackIdentityResult {
        let m = crate::term::track_identity_correspondence(
            &self.graph,
            prev_ids,
            cur_ids,
            feature_key,
            category_key,
            extent_key,
            radius,
        );
        for &(prev_nid, cur_nid) in &m.matched {
            let id_v = match self.graph.node(prev_nid).attrs.get(&identity_key).cloned() {
                Some(v) => v,
                None => {
                    // `prev_nid` has never been stamped (e.g. this is the
                    // very first frame pair ever tracked) — backfill its
                    // OWN identity too, not just the cur node's, so both
                    // sides of the match are resolvable after one call
                    // instead of only the cur side.
                    let fresh = Value::Int(prev_nid.0 as i64);
                    self.set_attr(prev_nid, identity_key, fresh.clone());
                    fresh
                }
            };
            self.set_attr(cur_nid, identity_key, id_v);
        }
        for &cur_nid in &m.births {
            self.set_attr(cur_nid, identity_key, Value::Int(cur_nid.0 as i64));
        }
        TrackIdentityResult {
            matched: m.matched,
            births: m.births,
            deaths: m.deaths,
        }
    }

    /// PERCEPTION-AS-ACTION twin for trans-frame identity: drain
    /// `graph.pending_track_identity` — the queue an
    /// `Effect::TrackIdentity` populates from inside `apply_rule_full`
    /// (which only holds `&mut graph`, not `&mut Substrate`) — between
    /// passes, calling `Substrate::track_identity` itself. Same
    /// "queue + drain between passes" pattern `apply_pending_fb_samples`
    /// established for `Effect::FbSample`.
    pub(crate) fn apply_pending_track_identity(&mut self) {
        let drain_started = crate::scale_audit::enabled().then(std::time::Instant::now);
        let pending = std::mem::take(&mut self.graph.pending_track_identity);
        let drained_items = pending.len();
        for (prev_ids, cur_ids, feature_key, category_key, extent_key, identity_key, radius) in
            pending
        {
            self.track_identity(
                &prev_ids,
                &cur_ids,
                feature_key,
                category_key,
                extent_key,
                identity_key,
                radius,
            );
        }
        if let Some(started) = drain_started {
            crate::scale_audit::deferred_queue_drained(
                "track_identity", drained_items,
                started.elapsed().as_nanos().min(u64::MAX as u128) as u64,
            );
        }
    }

    // --- shared-memory framebuffer vision primitive ---------------------

    /// Attach a reader-only mapping to the POSIX shm object `shm_name`
    /// (see `framebuffer::FbHandle::open` for the wire contract). On
    /// success, registers the handle and returns its `fb_id`; on
    /// failure (bad magic/version/format, short/missing shm object),
    /// returns the precise validation error as `Err` — nothing is
    /// registered.
    pub fn fb_attach(&mut self, shm_name: &str) -> Result<u32, String> {
        let handle = crate::framebuffer::FbHandle::open(shm_name)?;
        let id = self.next_fb_id;
        self.next_fb_id = self.next_fb_id.saturating_add(1);
        self.framebuffers.insert(id, handle);
        Ok(id)
    }

    /// Detach + drop the mapping for `fb_id`. Returns false if no such
    /// framebuffer is attached (already detached, or never valid).
    pub fn fb_detach(&mut self, fb_id: u32) -> bool {
        self.framebuffers.remove(&fb_id).is_some()
    }

    /// Sample the CURRENT frame of `fb_id`, quantize it to a
    /// `grid_w x grid_h` value grid, and run it through
    /// `segment_and_track` for `game` — minting/reusing the grid's
    /// Cell/WorldInstance nodes itself (there is no pre-ingested world
    /// graph behind a live framebuffer, unlike `segment`'s ARC caller).
    /// Fast-paths to a no-op when `frame_seq` hasn't advanced since the
    /// last sample of this `fb_id` (`unchanged: true` in the result).
    pub fn fb_sample(
        &mut self,
        fb_id: u32,
        game: NodeID,
        grid_w: usize,
        grid_h: usize,
    ) -> Result<FbSampleResult, String> {
        let Some(handle) = self.framebuffers.get(&fb_id) else {
            return Err(format!(
                "fb_sample: no framebuffer attached with fb_id {fb_id}"
            ));
        };
        let current_seq = handle.current_seq();
        let cache_valid = handle
            .cell_cache
            .as_ref()
            .map(|c| c.grid_w == grid_w && c.grid_h == grid_h && c.game == game)
            .unwrap_or(false);
        if cache_valid && current_seq == handle.last_sampled_seq {
            return Ok(FbSampleResult {
                fb_id,
                frame_seq: current_seq,
                unchanged: true,
                torn: false,
                grid_w,
                grid_h,
            });
        }

        let (payload, seq, torn) = handle.read_frame(crate::framebuffer::DEFAULT_MAX_RETRIES);
        let header = handle.header;
        let values = crate::framebuffer::downsample_quantize(
            &payload,
            header.width,
            header.height,
            header.stride,
            grid_w,
            grid_h,
            4,
        );

        // Mint (first call) or reuse (subsequent calls, cache still
        // valid for this grid_w/grid_h/game) the Cell/WorldInstance
        // nodes `segment_and_track` addresses by cell_id. Mirrors
        // `worlds/arc.py` + `world_adapter.ensure_world_instance`'s
        // node shape so downstream perception rules that pattern-match
        // `WorldInstance` + `world_type == "Cell"` work unchanged.
        let need_new_cells = !cache_valid;
        let cell_ids: Vec<i64> = if need_new_cells {
            let world_type_k = self.interner.intern("world_type");
            let world_id_k = self.interner.intern("world_id");
            let row_k = self.interner.intern("row");
            let col_k = self.interner.intern("col");
            let value_k = self.interner.intern("value");
            let n_obs_k = self.interner.intern("n_observations");
            let world_instance_t = self.interner.intern("WorldInstance");
            let cell_kind = self.interner.intern("Cell");
            let mut ids = Vec::with_capacity(grid_w * grid_h);
            for gy in 0..grid_h {
                for gx in 0..grid_w {
                    let idx = gy * grid_w + gx;
                    let mut attrs: FxHashMap<Sym, Value> = FxHashMap::default();
                    attrs.insert(world_type_k, Value::Str(cell_kind));
                    attrs.insert(
                        world_id_k,
                        Value::Str(self.interner.intern(&format!("{gy}_{gx}"))),
                    );
                    attrs.insert(row_k, Value::Float(gy as f64));
                    attrs.insert(col_k, Value::Float(gx as f64));
                    attrs.insert(value_k, Value::Float(values[idx] as f64));
                    attrs.insert(n_obs_k, Value::Float(0.0));
                    let nid = self.add_node(world_instance_t, attrs);
                    ids.push(nid.0 as i64);
                }
            }
            ids
        } else {
            self.framebuffers[&fb_id]
                .cell_cache
                .as_ref()
                .unwrap()
                .cell_ids
                .clone()
        };

        if !need_new_cells {
            // Update `value` on the existing cells in place.
            let value_k = self.interner.intern("value");
            for idx in 0..cell_ids.len() {
                self.set_attr(
                    NodeID(cell_ids[idx] as u32),
                    value_k,
                    Value::Float(values[idx] as f64),
                );
            }
        }

        // Stamp the game's `frame` attr with the fb's frame_seq so
        // `segment_and_track`'s `changed_frame` bookkeeping means
        // something for a live framebuffer (mirrors `worlds/arc.py`
        // stamping `frame` on its Game node every ingest).
        let frame_k = self.interner.intern("frame");
        self.set_attr(game, frame_k, Value::Float(seq as f64));

        self.segment_and_track(game, grid_h, grid_w, &values, &cell_ids);

        if let Some(handle) = self.framebuffers.get_mut(&fb_id) {
            handle.last_sampled_seq = seq;
            handle.cell_cache = Some(crate::framebuffer::CellCache {
                grid_w,
                grid_h,
                game,
                cell_ids,
            });
        }

        Ok(FbSampleResult {
            fb_id,
            frame_seq: seq,
            unchanged: false,
            torn,
            grid_w,
            grid_h,
        })
    }
}

/// Result of `Substrate::fb_sample` — the metadata `fb_sample`'s PyO3
/// wrapper stamps into the returned dict. The graph EFFECT (Region
/// mint/update, Cell mint/update) is the same side-channel `segment`
/// uses; this struct is only the "which frame did you just perceive"
/// receipt a caller needs to reason about staleness/tearing.
#[derive(Clone, Copy, Debug)]
pub struct FbSampleResult {
    pub fb_id: u32,
    pub frame_seq: u64,
    pub unchanged: bool,
    pub torn: bool,
    pub grid_w: usize,
    pub grid_h: usize,
}

/// Result of `Substrate::track_identity` — GRAPH LAW #6, the
/// domain-general trans-frame identity primitive. `matched` pairs
/// are `(prev_nid, cur_nid)` where `cur_nid` now carries the SAME
/// `identity_key` value `prev_nid` did; `births` are `cur` nodes
/// that got a freshly-minted identity; `deaths` are `prev` nodes with
/// no `cur` match this frame (reported, not deleted — see
/// `Substrate::track_identity`'s doc).
pub struct TrackIdentityResult {
    pub matched: Vec<(NodeID, NodeID)>,
    pub births: Vec<NodeID>,
    pub deaths: Vec<NodeID>,
}

/// Buffered mutation. The substrate exposes this via `transform()` so
/// the closure return value drives commit/rollback. Reads see the
/// uncommitted state — same semantics as the Python Transaction.
pub struct Transaction<'a> {
    substrate: &'a mut Substrate,
    inserted_nodes: Vec<NodeID>,
    inserted_edges: Vec<EdgeKey>,
    committed: bool,
}

impl<'a> Transaction<'a> {
    pub fn add_node(&mut self, type_: Sym, attrs: FxHashMap<Sym, Value>) -> NodeID {
        let nid = self.substrate.graph.insert_node(type_, attrs);
        self.inserted_nodes.push(nid);
        nid
    }

    pub fn add_edge(
        &mut self,
        src: NodeID,
        edge_type: Sym,
        tgt: NodeID,
        attrs: FxHashMap<Sym, Value>,
    ) -> Result<EdgeIdx, InadmissibleEdge> {
        let result = self.substrate.add_edge(src, edge_type, tgt, attrs);
        if let Ok(idx) = &result {
            self.inserted_edges
                .push(self.substrate.graph.edge(*idx).key());
        }
        result
    }

    pub fn substrate(&self) -> &Substrate {
        self.substrate
    }

    fn rollback(&mut self) {
        // Delete in reverse insertion order so edges are removed before
        // the nodes they reference.
        for key in self.inserted_edges.drain(..).rev() {
            if let Some(idx) = self
                .substrate
                .graph
                .edge_idx(key.src, key.edge_type, key.tgt)
            {
                self.substrate.graph.delete_edge(idx);
            }
        }
        for nid in self.inserted_nodes.drain(..).rev() {
            self.substrate.graph.delete_node(nid);
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::grammar::{Grammar, NodePattern, Production};
    use crate::term::TermNode;
    use rustc_hash::FxHashMap;

    fn empty_substrate() -> Substrate {
        Substrate::new(ConsistencyChecker::new(Grammar::new()))
    }

    fn term_clause(s: &mut Substrate, json: serde_json::Value) -> Value {
        crate::persist::decode_value(&json, &mut s.interner)
    }

    fn inert_rule(s: &mut Substrate, name: &str) -> crate::rewrite::RewriteRule {
        let true_term = s.terms.add(TermNode::Lit {
            value: Value::Bool(true),
        });
        crate::rewrite::RewriteRule {
            name: s.interner.intern(name),
            where_: Some(true_term),
            ..Default::default()
        }
    }

    #[test]
    fn rule_patch_cas_commits_and_inverse_exactly_reverts() {
        let mut s = empty_substrate();
        let rule = inert_rule(&mut s, "repair_target");
        let idx = s.add_rule(rule);
        let (uid, rev0, hash0, active) = s.rule_metadata(idx).unwrap();
        assert!(active);
        assert_ne!(uid.0, 0);
        assert_ne!(hash0, 0);
        let epoch0 = s.gamma_epoch.current();

        let false_clause = term_clause(&mut s, serde_json::json!({"type": "Lit", "value": false}));
        let receipt = s
            .apply_rule_patch(uid, rev0, hash0, "where", false_clause)
            .expect("fresh CAS patch must commit");
        assert_eq!(receipt.previous_revision, 0);
        assert_eq!(receipt.revision, 1);
        assert_ne!(receipt.content_hash, hash0);
        assert_eq!(s.gamma_epoch.current(), epoch0 + 1);
        assert!(s.rule_dirty[idx.0 as usize]);
        assert!(s.rule_cursors[idx.0 as usize].is_empty());
        #[cfg(all(target_arch = "x86_64", target_os = "linux"))]
        assert!(s.rule_where_jit[idx.0 as usize].is_none());
        assert!(matches!(
            s.terms.get(s.rules[idx.0 as usize].where_.unwrap()),
            TermNode::Lit {
                value: Value::Bool(false)
            }
        ));

        let receipt2 = s
            .apply_rule_patch(
                uid,
                receipt.revision,
                receipt.content_hash,
                "where",
                receipt.inverse_clause,
            )
            .expect("authoritative inverse must be a valid next CAS patch");
        assert_eq!(receipt2.revision, 2);
        assert_eq!(
            receipt2.content_hash, hash0,
            "content hash excludes revision and must return to the exact original body"
        );
        assert!(matches!(
            s.terms.get(s.rules[idx.0 as usize].where_.unwrap()),
            TermNode::Lit {
                value: Value::Bool(true)
            }
        ));
    }

    #[test]
    fn refused_rule_patches_change_no_runtime_state() {
        let mut s = empty_substrate();
        let rule = inert_rule(&mut s, "repair_target");
        let idx = s.add_rule(rule);
        let (uid, revision, content_hash, _) = s.rule_metadata(idx).unwrap();

        let where_before = s.rules[idx.0 as usize].where_;
        let terms_before = s.terms.nodes.len();
        let epoch_before = s.gamma_epoch.current();
        let dirty_before = s.rule_dirty.clone();
        let stale_clause = term_clause(&mut s, serde_json::json!({"type": "Lit", "value": false}));
        // Account for the test-side Value construction: it interns strings but
        // appends no Terms. The transaction itself must append none on stale CAS.
        let terms_before_stale = s.terms.nodes.len();
        assert!(matches!(
            s.apply_rule_patch(
                uid,
                revision + 1,
                content_hash,
                "where",
                stale_clause,
            ),
            Err(RulePatchError::StaleRevision { actual }) if actual == revision
        ));
        assert_eq!(s.terms.nodes.len(), terms_before_stale);
        assert_eq!(s.rules[idx.0 as usize].where_, where_before);
        assert_eq!(
            s.rule_metadata(idx).unwrap(),
            (uid, revision, content_hash, true)
        );
        assert_eq!(s.gamma_epoch.current(), epoch_before);
        assert_eq!(s.rule_dirty, dirty_before);

        assert!(matches!(
            s.apply_rule_patch(uid, revision, content_hash, "where", Value::Int(7),),
            Err(RulePatchError::MalformedClause)
        ));
        assert_eq!(
            s.terms.nodes.len(),
            terms_before_stale,
            "partial parser allocations must roll back on malformed clauses"
        );
        assert_eq!(s.rules[idx.0 as usize].where_, where_before);
        assert_eq!(
            s.rule_metadata(idx).unwrap(),
            (uid, revision, content_hash, true)
        );
        assert_eq!(s.gamma_epoch.current(), epoch_before);
        assert!(terms_before <= terms_before_stale);
    }

    #[test]
    fn protected_rule_refuses_patch_without_any_runtime_change() {
        let mut s = empty_substrate();
        let mut rule = inert_rule(&mut s, "boot_prior");
        rule.mutation_protected = true;
        let idx = s.add_rule(rule);
        let (uid, revision, content_hash, _) = s.rule_metadata(idx).unwrap();
        let terms_before = s.terms.nodes.len();
        let epoch_before = s.gamma_epoch.current();
        let dirty_before = s.rule_dirty.clone();
        let clause = term_clause(&mut s, serde_json::json!({"type": "Lit", "value": false}));
        let terms_after_clause_value = s.terms.nodes.len();

        assert!(matches!(
            s.apply_rule_patch(uid, revision, content_hash, "where", clause),
            Err(RulePatchError::ProtectedTarget)
        ));
        assert_eq!(s.terms.nodes.len(), terms_after_clause_value);
        assert_eq!(s.gamma_epoch.current(), epoch_before);
        assert_eq!(s.rule_dirty, dirty_before);
        assert!(terms_before <= terms_after_clause_value);
        assert!(matches!(
            s.terms.get(s.rules[idx.0 as usize].where_.unwrap()),
            TermNode::Lit {
                value: Value::Bool(true)
            }
        ));
    }

    #[test]
    fn legacy_name_only_edit_refuses_ambiguous_live_rules() {
        let mut s = empty_substrate();
        let first = inert_rule(&mut s, "duplicate");
        let second = inert_rule(&mut s, "duplicate");
        let a = s.add_rule(first);
        let b = s.add_rule(second);
        let before_a = s.rule_metadata(a).unwrap();
        let before_b = s.rule_metadata(b).unwrap();
        let epoch = s.gamma_epoch.current();
        let clause = term_clause(&mut s, serde_json::json!({"type": "Lit", "value": false}));
        s.graph
            .pending_rule_edits
            .push(("duplicate".to_string(), "where".to_string(), clause));
        s.apply_pending_rule_edits();
        assert_eq!(s.rule_metadata(a).unwrap(), before_a);
        assert_eq!(s.rule_metadata(b).unwrap(), before_b);
        assert_eq!(s.gamma_epoch.current(), epoch);
        assert!(matches!(
            s.terms.get(s.rules[a.0 as usize].where_.unwrap()),
            TermNode::Lit {
                value: Value::Bool(true)
            }
        ));
        assert!(matches!(
            s.terms.get(s.rules[b.0 as usize].where_.unwrap()),
            TermNode::Lit {
                value: Value::Bool(true)
            }
        ));
    }

    #[test]
    fn graph_rule_patch_node_receives_durable_commit_receipt() {
        let mut s = empty_substrate();
        let rule = inert_rule(&mut s, "graph_patch_target");
        let idx = s.add_rule(rule);
        let (uid, revision, content_hash, _) = s.rule_metadata(idx).unwrap();
        let patch_type = s.interner.intern("RulePatch");
        let target_uid_key = s.interner.intern("target_uid");
        let expected_revision_key = s.interner.intern("expected_revision");
        let expected_hash_key = s.interner.intern("expected_content_hash");
        let field_key = s.interner.intern("field");
        let proposed_key = s.interner.intern("proposed_clause");
        let status_key = s.interner.intern("status");
        let reason_key = s.interner.intern("reason");
        let result_revision_key = s.interner.intern("result_revision");
        let inverse_key = s.interner.intern("inverse_clause");
        let where_sym = s.interner.intern("where");
        let mut attrs = FxHashMap::default();
        attrs.insert(target_uid_key, Value::Int(uid.0 as i64));
        attrs.insert(expected_revision_key, Value::Int(revision as i64));
        attrs.insert(expected_hash_key, Value::Int(content_hash as i64));
        attrs.insert(field_key, Value::Str(where_sym));
        attrs.insert(
            proposed_key,
            term_clause(&mut s, serde_json::json!({"type": "Lit", "value": false})),
        );
        let patch = s.add_node(patch_type, attrs);
        let agent_type = s.interner.intern("Agent");
        let agent = s.add_node(agent_type, FxHashMap::default());
        let has_patch = s.interner.intern("has_patch");
        s.graph
            .insert_edge(agent, has_patch, patch, FxHashMap::default())
            .unwrap();
        let agent_var = s.interner.intern("agent");
        let patch_var = s.interner.intern("patch");
        let dispatch_name = s.interner.intern("dispatch_patch");
        let dispatch = s.add_rule(crate::rewrite::RewriteRule {
            name: dispatch_name,
            match_edges: vec![crate::rewrite::MatchEdge {
                src_var: agent_var,
                edge_type: has_patch,
                tgt_var: patch_var,
            }],
            effects: vec![crate::rewrite::Effect::ApplyRulePatch { patch_var }],
            ..Default::default()
        });
        assert!(s.apply_rule_once(dispatch));
        assert_eq!(s.graph.pending_rule_patches, vec![patch]);
        s.apply_pending_rule_patches();

        let node = s.graph.node(patch);
        assert_eq!(
            node.attrs.get(&status_key),
            Some(&Value::Str(s.interner.lookup("committed").unwrap()))
        );
        assert_eq!(
            node.attrs.get(&reason_key),
            Some(&Value::Str(s.interner.lookup("ok").unwrap()))
        );
        assert_eq!(node.attrs.get(&result_revision_key), Some(&Value::Int(1)));
        assert!(node.attrs.contains_key(&inverse_key));
        assert_eq!(s.rule_metadata(idx).unwrap().1, 1);
    }

    #[test]
    fn stable_rule_identity_round_trips_through_checkpoint_codec() {
        let mut original = empty_substrate();
        let first = inert_rule(&mut original, "same_name");
        let second = inert_rule(&mut original, "same_name");
        original.add_rule(first);
        original.add_rule(second);
        let metadata: Vec<_> = (0..original.rules.len())
            .map(|i| {
                original
                    .rule_metadata(crate::rewrite::RuleIdx(i as u32))
                    .unwrap()
            })
            .collect();
        assert_ne!(metadata[0].0, metadata[1].0);
        let exported: Vec<_> = original
            .rules
            .iter()
            .map(|rule| crate::py::rule_to_json(rule, &original.terms, &original.interner))
            .collect();

        let mut restored = empty_substrate();
        for json in &exported {
            let rule =
                crate::py::parse_rule_json_pub(json, &mut restored.terms, &mut restored.interner)
                    .unwrap();
            restored.add_rule(rule);
        }
        let restored_metadata: Vec<_> = (0..restored.rules.len())
            .map(|i| {
                restored
                    .rule_metadata(crate::rewrite::RuleIdx(i as u32))
                    .unwrap()
            })
            .collect();
        assert_eq!(restored_metadata, metadata);
    }

    fn build_alive_grammar() -> Substrate {
        // A minimal admissibility grammar from learner.py:
        //   AliveCell -[adjacent_to]-> AliveCell   (no where-clause)
        // Models the "two cells can be adjacent" rule.
        let mut s = empty_substrate();
        let alive = s.interner.intern("AliveCell");
        let adj = s.interner.intern("adjacent_to");
        let src_var = s.interner.intern("src");
        let tgt_var = s.interner.intern("tgt");
        let prov = s.interner.intern("test:alive_adj");
        let w = Grammar::default_weight(&mut s.terms);
        s.checker.grammar.add(Production {
            src: NodePattern {
                type_: alive,
                var: src_var,
            },
            edge_type: adj,
            tgt: NodePattern {
                type_: alive,
                var: tgt_var,
            },
            where_: None,
            weight: w,
            provenance: prov,
        });
        s
    }

    #[test]
    fn add_node_unchecked() {
        let mut s = empty_substrate();
        let t = s.interner.intern("Anything");
        let n = s.add_node(t, FxHashMap::default());
        assert!(s.graph.has_node(n));
    }

    // -------- L2 integration: gamma_epoch on Γ-mutation --------

    /// `gamma_change_must_bump_epoch` (Mt rule). Adding a rule is a
    /// Γ mutation; the epoch must bump.
    #[test]
    fn add_rule_bumps_gamma_epoch() {
        let mut s = empty_substrate();
        let start = s.gamma_epoch().current();
        let name = s.interner.intern("noop");
        let et = s.interner.intern("e");
        let a = s.interner.intern("a");
        let b = s.interner.intern("b");
        s.add_rule(crate::rewrite::RewriteRule {
            name,
            match_edges: vec![crate::rewrite::MatchEdge {
                src_var: a,
                edge_type: et,
                tgt_var: b,
            }],
            where_: None,
            effects: vec![],
            ..Default::default()
        });
        assert_eq!(s.gamma_epoch().current(), start + 1);
    }

    /// Adding a production via `Substrate::add_production` bumps
    /// the epoch — wired path that an installed dispatcher
    /// observes for cache invalidation.
    #[test]
    fn add_production_bumps_gamma_epoch() {
        let mut s = build_alive_grammar();
        let start = s.gamma_epoch().current();
        let alive = s.interner.lookup("AliveCell").unwrap();
        let adj = s.interner.intern("excluded");
        let src_var = s.interner.intern("src");
        let tgt_var = s.interner.intern("tgt");
        let prov = s.interner.intern("test:added");
        let w = Grammar::default_weight(&mut s.terms);
        s.add_production(Production {
            src: NodePattern {
                type_: alive,
                var: src_var,
            },
            edge_type: adj,
            tgt: NodePattern {
                type_: alive,
                var: tgt_var,
            },
            where_: None,
            weight: w,
            provenance: prov,
        });
        assert_eq!(s.gamma_epoch().current(), start + 1);
    }

    /// GAMMA_REFLECTION_WIRING_PREREG.md §1.3 bar 5, end-to-end through the
    /// REAL `Substrate::add_production` path (not just the isolated
    /// `grammar_reflect` unit tests): after adding productions the normal
    /// way, `grammar_from_graph` on `gamma_graph_root()` reconstructs a
    /// `Grammar` that is content-equal to `checker.grammar` itself — the
    /// live proof that the graph mirror and the Rust-side struct are the
    /// SAME data for everything added through this one call site, not two
    /// copies that can (yet) drift. Compares via `jsonio::grammar_to_json`
    /// so the check exercises the SAME wire format bar 3 protects.
    #[test]
    fn graph_mirror_is_content_equal_to_checker_grammar() {
        // `empty_substrate()`, not `build_alive_grammar()` — the latter
        // seeds one production via `s.checker.grammar.add(...)` DIRECTLY
        // (bypassing `add_production`, same pre-existing pattern as the
        // PyO3 binding, PREREG §0.3/§2 point 4's named desync boundary),
        // which would make `checker.grammar.len()` legitimately exceed the
        // mirror's count for a reason unrelated to what this test checks.
        let mut s = empty_substrate();
        let alive = s.interner.intern("AliveCell");
        let w1 = Grammar::default_weight(&mut s.terms);
        let (v_a, v_b, et1, prov1) = (
            s.interner.intern("a"),
            s.interner.intern("b"),
            s.interner.intern("mirror_check_1"),
            s.interner.intern("test:mirror_1"),
        );
        s.add_production(Production {
            src: NodePattern {
                type_: alive,
                var: v_a,
            },
            edge_type: et1,
            tgt: NodePattern {
                type_: alive,
                var: v_b,
            },
            where_: None,
            weight: w1,
            provenance: prov1,
        });
        let v_c = s.interner.intern("c");
        let lhs = s.terms.add(TermNode::Var { name: v_c });
        let rhs = s.terms.add(TermNode::Lit {
            value: Value::Int(3),
        });
        let where2 = s.terms.add(TermNode::Gt { a: lhs, b: rhs });
        let w2 = Grammar::default_weight(&mut s.terms);
        let (v_d, et2, prov2) = (
            s.interner.intern("d"),
            s.interner.intern("mirror_check_2"),
            s.interner.intern("test:mirror_2"),
        );
        s.add_production(Production {
            src: NodePattern {
                type_: alive,
                var: v_c,
            },
            edge_type: et2,
            tgt: NodePattern {
                type_: alive,
                var: v_d,
            },
            where_: Some(where2),
            weight: w2,
            provenance: prov2,
        });

        let root = s
            .gamma_graph_root()
            .expect("mirror root should exist after add_production");
        let mut mirror_arena = TermArena::new();
        let rebuilt = crate::grammar_reflect::grammar_from_graph(
            &s.graph,
            root,
            &mut mirror_arena,
            &s.interner,
        )
        .expect("grammar_from_graph should reconstruct the mirror written by add_production");

        assert_eq!(
            rebuilt.productions.len(),
            s.checker.grammar.productions.len()
        );
        for (from_struct, from_graph) in s
            .checker
            .grammar
            .productions
            .iter()
            .zip(rebuilt.productions.iter())
        {
            assert_eq!(
                s.interner.resolve(from_struct.src.type_),
                s.interner.resolve(from_graph.src.type_)
            );
            assert_eq!(
                s.interner.resolve(from_struct.src.var),
                s.interner.resolve(from_graph.src.var)
            );
            assert_eq!(
                s.interner.resolve(from_struct.edge_type),
                s.interner.resolve(from_graph.edge_type)
            );
            assert_eq!(
                s.interner.resolve(from_struct.tgt.type_),
                s.interner.resolve(from_graph.tgt.type_)
            );
            assert_eq!(
                s.interner.resolve(from_struct.tgt.var),
                s.interner.resolve(from_graph.tgt.var)
            );
            assert_eq!(
                s.interner.resolve(from_struct.provenance),
                s.interner.resolve(from_graph.provenance)
            );
            let struct_where = from_struct
                .where_
                .map(|w| crate::jsonio::term_to_json(&s.terms, w, &s.interner));
            let graph_where = from_graph
                .where_
                .map(|w| crate::jsonio::term_to_json(&mirror_arena, w, &s.interner));
            assert_eq!(struct_where, graph_where);
            let struct_weight =
                crate::jsonio::term_to_json(&s.terms, from_struct.weight, &s.interner);
            let graph_weight =
                crate::jsonio::term_to_json(&mirror_arena, from_graph.weight, &s.interner);
            assert_eq!(struct_weight, graph_weight);
        }

        // §1.3 bar 3's own arbiter: grammar_to_json on the struct is
        // untouched by any of this — the wire format this test's own
        // comparisons above are keyed on is exactly what seed persistence
        // reads/writes, unmodified by the mirror's existence.
        let wire = crate::jsonio::grammar_to_json(&s.checker.grammar, &s.terms, &s.interner);
        assert_eq!(wire["productions"].as_array().unwrap().len(), 2);
    }

    /// G mutations (add_node, add_edge) MUST NOT bump the Γ
    /// epoch. Adding/removing data isn't a rule-store change;
    /// JIT'd code for unchanged Γ remains valid.
    #[test]
    fn node_and_edge_mutations_do_not_bump_gamma_epoch() {
        let mut s = build_alive_grammar();
        let start = s.gamma_epoch().current();
        let alive = s.interner.lookup("AliveCell").unwrap();
        let a = s.add_node(alive, FxHashMap::default());
        let b = s.add_node(alive, FxHashMap::default());
        let adj = s.interner.lookup("adjacent_to").unwrap();
        let _ = s.add_edge(a, adj, b, FxHashMap::default());
        assert_eq!(
            s.gamma_epoch().current(),
            start,
            "G mutations are not Γ mutations"
        );
    }

    /// Dispatcher created with `with_shared_epoch(substrate.gamma_epoch())`
    /// observes the substrate's Γ-mutation bumps end-to-end.
    #[test]
    fn dispatcher_with_shared_epoch_sees_substrate_mutations() {
        use crate::code_cache::{CodeCacheConfig, CodeSize};
        use crate::l2_adaptive::{AdaptiveDispatcher, TierUpPolicy};
        use crate::l2_dispatch::Scheduler;

        struct FakeJit {
            size: usize,
        }
        impl CodeSize for FakeJit {
            fn code_size_bytes(&self) -> usize {
                self.size
            }
        }

        let mut s = empty_substrate();
        let dispatcher: AdaptiveDispatcher<FakeJit> = AdaptiveDispatcher::with_shared_epoch(
            Scheduler::new(1),
            TierUpPolicy::default(),
            CodeCacheConfig { max_bytes: 1024 },
            s.gamma_epoch(),
        );

        let kind = s.interner.intern("rule_a");
        dispatcher.install_compiled(kind, FakeJit { size: 100 });
        assert!(dispatcher.has_fresh_cached(kind));

        // Substrate-side Γ mutation.
        let name = s.interner.intern("r");
        let et = s.interner.intern("e");
        let x = s.interner.intern("x");
        let y = s.interner.intern("y");
        s.add_rule(crate::rewrite::RewriteRule {
            name,
            match_edges: vec![crate::rewrite::MatchEdge {
                src_var: x,
                edge_type: et,
                tgt_var: y,
            }],
            where_: None,
            effects: vec![],
            ..Default::default()
        });

        // Dispatcher cache invalidated through shared Epoch.
        assert!(
            !dispatcher.has_fresh_cached(kind),
            "shared epoch bump from substrate must invalidate \
                 dispatcher cache"
        );
        dispatcher.shutdown();
    }

    #[test]
    fn admitted_edge_inserts() {
        let mut s = build_alive_grammar();
        let alive = s.interner.lookup("AliveCell").unwrap();
        let adj = s.interner.lookup("adjacent_to").unwrap();
        let a = s.add_node(alive, FxHashMap::default());
        let b = s.add_node(alive, FxHashMap::default());
        let r = s.add_edge(a, adj, b, FxHashMap::default());
        assert!(r.is_ok());
        assert!(s.graph.has_edge(a, adj, b));
    }

    #[test]
    fn type1_no_production_when_no_grammar_rule() {
        let mut s = build_alive_grammar();
        let alive = s.interner.lookup("AliveCell").unwrap();
        let dead = s.interner.intern("DeadCell");
        let adj = s.interner.lookup("adjacent_to").unwrap();
        let a = s.add_node(alive, FxHashMap::default());
        // dead-type node exists but the grammar has no Alive→adj→Dead
        // production. Since DeadCell isn't in the vocabulary either,
        // we expect a Type-2 error first (vocab checked before triple).
        let b = s.add_node(dead, FxHashMap::default());
        match s.add_edge(a, adj, b, FxHashMap::default()) {
            Err(InadmissibleEdge::Type2VocabAbsent { missing }) => {
                assert_eq!(missing, dead);
            }
            other => panic!("expected Type-2 for absent vocabulary; got {:?}", other),
        }
    }

    #[test]
    fn type1_when_vocab_present_but_no_admitting_production() {
        // Build a grammar that knows about DeadCell as a node type
        // (via a production referencing it) but has no Alive→adj→Dead
        // production. Should give Type-1, not Type-2.
        let mut s = build_alive_grammar();
        let alive = s.interner.lookup("AliveCell").unwrap();
        let dead = s.interner.intern("DeadCell");
        let adj = s.interner.lookup("adjacent_to").unwrap();
        let src_var = s.interner.lookup("src").unwrap();
        let tgt_var = s.interner.lookup("tgt").unwrap();
        let prov = s.interner.intern("test:dead_only");
        let w = Grammar::default_weight(&mut s.terms);
        // Add Dead→adj→Dead so Dead is in vocab.
        s.checker.grammar.add(Production {
            src: NodePattern {
                type_: dead,
                var: src_var,
            },
            edge_type: adj,
            tgt: NodePattern {
                type_: dead,
                var: tgt_var,
            },
            where_: None,
            weight: w,
            provenance: prov,
        });
        let a = s.add_node(alive, FxHashMap::default());
        let b = s.add_node(dead, FxHashMap::default());
        match s.add_edge(a, adj, b, FxHashMap::default()) {
            Err(InadmissibleEdge::Type1NoProduction {
                src_type,
                edge_type,
                tgt_type,
            }) => {
                assert_eq!(src_type, alive);
                assert_eq!(edge_type, adj);
                assert_eq!(tgt_type, dead);
            }
            other => panic!(
                "expected Type-1 for known-vocab/no-production; got {:?}",
                other
            ),
        }
    }

    // -------- GAMMA_COLLAPSE_ALGORITHM spike: residual capture --------

    /// **THE SAFETY-CRITICAL TEST.** `gamma_residual_capture` DEFAULT FALSE
    /// must leave `add_edge`'s `Type1NoProduction` arm byte-unchanged: same
    /// `Err` value, same counters, and — the part a naive re-read of the
    /// counters wouldn't catch — NO new node minted anywhere in the graph.
    #[test]
    fn gamma_residual_capture_off_leaves_graph_unchanged() {
        let mut s = build_alive_grammar();
        let alive = s.interner.lookup("AliveCell").unwrap();
        let dead = s.interner.intern("DeadCell");
        let adj = s.interner.lookup("adjacent_to").unwrap();
        let src_var = s.interner.intern("src2");
        let tgt_var = s.interner.intern("tgt2");
        let prov = s.interner.intern("test:dead_only2");
        let w = Grammar::default_weight(&mut s.terms);
        s.checker.grammar.add(Production {
            src: NodePattern {
                type_: dead,
                var: src_var,
            },
            edge_type: adj,
            tgt: NodePattern {
                type_: dead,
                var: tgt_var,
            },
            where_: None,
            weight: w,
            provenance: prov,
        });
        let a = s.add_node(alive, FxHashMap::default());
        let b = s.add_node(dead, FxHashMap::default());
        let nodes_before = s.graph.node_count();
        assert!(!s.gamma_residual_capture, "must default to false");
        match s.add_edge(a, adj, b, FxHashMap::default()) {
            Err(InadmissibleEdge::Type1NoProduction {
                src_type,
                edge_type,
                tgt_type,
            }) => {
                assert_eq!(src_type, alive);
                assert_eq!(edge_type, adj);
                assert_eq!(tgt_type, dead);
            }
            other => panic!("expected Type-1; got {:?}", other),
        }
        assert_eq!(
            s.graph.node_count(),
            nodes_before,
            "capture off must mint NOTHING — the committed default path is byte-unchanged"
        );
        assert!(
            s.gamma_residual_root.is_none(),
            "root must not be lazily created when capture is off"
        );
    }

    /// Capture ON: two rejections of the SAME triple mint two `GammaResidual`
    /// nodes (Rust does event logging only — the recurrence DECISION is the
    /// seed rule's job, not Rust's; see `seeds/gamma_residual.json`), both
    /// carrying the correct triple attrs, anchored under one shared root via
    /// the `gamma_residual` edge type.
    #[test]
    fn gamma_residual_capture_on_logs_one_node_per_rejection() {
        let mut s = build_alive_grammar();
        let alive = s.interner.lookup("AliveCell").unwrap();
        let dead = s.interner.intern("DeadCell");
        let adj = s.interner.lookup("adjacent_to").unwrap();
        let src_var = s.interner.intern("src3");
        let tgt_var = s.interner.intern("tgt3");
        let prov = s.interner.intern("test:dead_only3");
        let w = Grammar::default_weight(&mut s.terms);
        s.checker.grammar.add(Production {
            src: NodePattern {
                type_: dead,
                var: src_var,
            },
            edge_type: adj,
            tgt: NodePattern {
                type_: dead,
                var: tgt_var,
            },
            where_: None,
            weight: w,
            provenance: prov,
        });
        s.set_gamma_residual_capture(true);
        let a = s.add_node(alive, FxHashMap::default());
        let b1 = s.add_node(dead, FxHashMap::default());
        let b2 = s.add_node(dead, FxHashMap::default());
        assert!(s.add_edge(a, adj, b1, FxHashMap::default()).is_err());
        assert!(s.add_edge(a, adj, b2, FxHashMap::default()).is_err());

        let residual_type = s.interner.lookup("GammaResidual").unwrap();
        let residuals = s.graph.nodes_of_type(residual_type);
        assert_eq!(
            residuals.len(),
            2,
            "one GammaResidual node per rejection, no Rust-side dedup"
        );

        let src_key = s.interner.lookup("src_type").unwrap();
        let edge_key = s.interner.lookup("edge_type").unwrap();
        let tgt_key = s.interner.lookup("tgt_type").unwrap();
        for r in &residuals {
            let attrs = &s.graph.node(*r).attrs;
            assert_eq!(attrs.get(&src_key), Some(&Value::Str(alive)));
            assert_eq!(attrs.get(&edge_key), Some(&Value::Str(adj)));
            assert_eq!(attrs.get(&tgt_key), Some(&Value::Str(dead)));
        }

        // Both anchored under the SAME lazily-created root.
        let root = s
            .gamma_residual_root
            .expect("root must be created once capture is on");
        let residual_edge = s.interner.lookup("gamma_residual").unwrap();
        let anchored = s.graph.out_edges_idx(root, Some(residual_edge));
        assert_eq!(anchored.len(), 2);
    }

    /// Two DIFFERENT triples produce two residual nodes with DIFFERING
    /// attrs — a regression guard against a grouping-key bug (the exact
    /// failure class `SHAPE_AUDIT.md` §3.1 documents for `CapabilityAxis`'s
    /// truncated identity: here there is no truncation to get wrong, but a
    /// copy-paste of the wrong Sym into the wrong attr key would silently
    /// conflate two distinct triples).
    #[test]
    fn gamma_residual_capture_distinguishes_different_triples() {
        let mut s = build_alive_grammar();
        let alive = s.interner.lookup("AliveCell").unwrap();
        let dead = s.interner.intern("DeadCell");
        let adj = s.interner.lookup("adjacent_to").unwrap();
        let far = s.interner.intern("far_edge");
        let src_var = s.interner.intern("src4");
        let tgt_var = s.interner.intern("tgt4");
        let w1 = Grammar::default_weight(&mut s.terms);
        s.checker.grammar.add(Production {
            src: NodePattern {
                type_: dead,
                var: src_var,
            },
            edge_type: adj,
            tgt: NodePattern {
                type_: dead,
                var: tgt_var,
            },
            where_: None,
            weight: w1,
            provenance: s.interner.intern("test:dead_only4"),
        });
        let w2 = Grammar::default_weight(&mut s.terms);
        s.checker.grammar.add(Production {
            src: NodePattern {
                type_: dead,
                var: src_var,
            },
            edge_type: far,
            tgt: NodePattern {
                type_: dead,
                var: tgt_var,
            },
            where_: None,
            weight: w2,
            provenance: s.interner.intern("test:dead_only5"),
        });
        s.set_gamma_residual_capture(true);
        let a = s.add_node(alive, FxHashMap::default());
        let b1 = s.add_node(dead, FxHashMap::default());
        let b2 = s.add_node(dead, FxHashMap::default());
        assert!(s.add_edge(a, adj, b1, FxHashMap::default()).is_err());
        assert!(s.add_edge(a, far, b2, FxHashMap::default()).is_err());

        let residual_type = s.interner.lookup("GammaResidual").unwrap();
        let residuals = s.graph.nodes_of_type(residual_type);
        assert_eq!(residuals.len(), 2);
        let edge_key = s.interner.lookup("edge_type").unwrap();
        let edges_seen: std::collections::HashSet<Sym> = residuals
            .iter()
            .filter_map(|r| match s.graph.node(*r).attrs.get(&edge_key) {
                Some(Value::Str(sym)) => Some(*sym),
                _ => None,
            })
            .collect();
        assert!(edges_seen.contains(&adj));
        assert!(edges_seen.contains(&far));
    }

    #[test]
    fn transform_rollback_undoes_inserts() {
        let mut s = build_alive_grammar();
        let alive = s.interner.lookup("AliveCell").unwrap();
        let adj = s.interner.lookup("adjacent_to").unwrap();
        let nodes_before = s.graph.node_count();
        let edges_before = s.graph.edge_count();

        let r: Result<(), InadmissibleEdge> = s.transform(|tx| {
            let a = tx.add_node(alive, FxHashMap::default());
            let b = tx.add_node(alive, FxHashMap::default());
            tx.add_edge(a, adj, b, FxHashMap::default())?;
            // Force a rollback by returning Err.
            let dead = tx
                .substrate
                .interner
                .lookup("DeadCell")
                .unwrap_or_else(|| tx.substrate.interner.intern("DeadCell"));
            let c = tx.add_node(dead, FxHashMap::default());
            tx.add_edge(a, adj, c, FxHashMap::default()).map(|_| ())
        });
        assert!(r.is_err());
        assert_eq!(s.graph.node_count(), nodes_before);
        assert_eq!(s.graph.edge_count(), edges_before);
    }

    #[test]
    fn transform_commit_keeps_inserts() {
        let mut s = build_alive_grammar();
        let alive = s.interner.lookup("AliveCell").unwrap();
        let adj = s.interner.lookup("adjacent_to").unwrap();
        let r: Result<NodeID, InadmissibleEdge> = s.transform(|tx| {
            let a = tx.add_node(alive, FxHashMap::default());
            let b = tx.add_node(alive, FxHashMap::default());
            tx.add_edge(a, adj, b, FxHashMap::default())?;
            Ok(a)
        });
        assert!(r.is_ok());
        assert_eq!(s.graph.node_count(), 2);
        assert_eq!(s.graph.edge_count(), 1);
    }

    #[test]
    fn weighted_admissible_moves_sums_per_production() {
        // Two productions match the same triple; their weights add.
        let mut s = build_alive_grammar();
        let alive = s.interner.lookup("AliveCell").unwrap();
        let adj = s.interner.lookup("adjacent_to").unwrap();
        let src_var = s.interner.lookup("src").unwrap();
        let tgt_var = s.interner.lookup("tgt").unwrap();
        let prov = s.interner.intern("test:second_alive_adj");
        // Second production with weight 2.5.
        let two_five = s.terms.add(TermNode::Lit {
            value: Value::Float(2.5),
        });
        s.checker.grammar.add(Production {
            src: NodePattern {
                type_: alive,
                var: src_var,
            },
            edge_type: adj,
            tgt: NodePattern {
                type_: alive,
                var: tgt_var,
            },
            where_: None,
            weight: two_five,
            provenance: prov,
        });
        let a = s.add_node(alive, FxHashMap::default());
        let moves = s.admissible_moves(a, adj, vec![(alive, crate::graph::Attrs::new())]);
        assert_eq!(moves.len(), 1);
        // Default 1.0 + explicit 2.5 = 3.5.
        let (_, _, w) = &moves[0];
        assert!((w - 3.5).abs() < 1e-9, "weight total = {}", w);
    }

    // --- differential rule firing ---

    #[test]
    fn differential_firing_skips_clean_rules() {
        // Two rules over disjoint edge_types. Touch only edge_type A.
        // Rule for A should fire; rule for B should NOT be re-evaluated
        // (its dirty bit was cleared after a previous tick and no
        // mutation touched B since).
        let mut s = empty_substrate();
        let a = s.interner.intern("A");
        let b = s.interner.intern("B");
        let n = s.interner.intern("N");
        let x = s.interner.intern("x");
        let y = s.interner.intern("y");
        // Vocabulary: N nodes can have A or B edges between them.
        // Vocabulary additions via the unchecked path.
        let n1 = s.graph.insert_node(n, FxHashMap::default());
        let n2 = s.graph.insert_node(n, FxHashMap::default());
        // Open vocabulary — empty grammar admits unchecked through tests.
        // Inject one A edge directly into the graph.
        s.graph
            .insert_edge(n1, a, n2, FxHashMap::default())
            .unwrap();

        // Two rules: one over A, one over B. Each effect is a no-op
        // (re-add the same edge) so they never progress; we only care
        // about WHICH ones get matched.
        let rule_a = crate::rewrite::RewriteRule {
            name: s.interner.intern("rule_A"),
            match_edges: vec![crate::rewrite::MatchEdge {
                src_var: x,
                edge_type: a,
                tgt_var: y,
            }],
            where_: None,
            effects: vec![],
            ..Default::default()
        };
        let rule_b = crate::rewrite::RewriteRule {
            name: s.interner.intern("rule_B"),
            match_edges: vec![crate::rewrite::MatchEdge {
                src_var: x,
                edge_type: b,
                tgt_var: y,
            }],
            where_: None,
            effects: vec![],
            ..Default::default()
        };
        s.add_rule(rule_a);
        s.add_rule(rule_b);

        // Both rules start dirty.
        assert_eq!(s.rule_dirty, vec![true, true]);

        // First tick: both rules evaluated (neither progresses because
        // effects are empty); bits clear after.
        s.run_rules(100);
        assert_eq!(
            s.rule_dirty,
            vec![false, false],
            "after a clean fixed-point pass, both rules clean"
        );

        // Now mutate via the substrate (so dirty tracking fires) — add
        // another A edge. Rule A should be marked dirty; rule B not.
        let n3 = s.graph.insert_node(n, FxHashMap::default());
        // bypass admissibility (test scaffold) but use add_edge for
        // dirty-tracking — set up an open grammar first.
        let prov = s.interner.intern("test:open");
        let weight = s.terms.add(crate::term::TermNode::Lit {
            value: Value::Float(1.0),
        });
        s.checker.grammar.add(crate::grammar::Production {
            src: crate::grammar::NodePattern { type_: n, var: x },
            edge_type: a,
            tgt: crate::grammar::NodePattern { type_: n, var: y },
            where_: None,
            weight,
            provenance: prov,
        });
        s.add_edge(n1, a, n3, FxHashMap::default()).unwrap();
        assert_eq!(
            s.rule_dirty[0], true,
            "rule_A should be dirty after A-edge insert"
        );
        assert_eq!(s.rule_dirty[1], false, "rule_B should remain clean");
    }

    #[test]
    #[cfg(all(target_arch = "x86_64", target_os = "linux"))]
    fn jit_compiles_kernel_where_clauses_on_install() {
        // A rule whose where-clause is pure kernel (Eq(TypeOf, Lit Str))
        // should compile to a JittedFn at install time. A rule whose
        // where-clause uses Filter/Sum should NOT compile (interpreter
        // fallback).
        let mut s = empty_substrate();
        let cell = s.interner.intern("Cell");
        let alive = s.interner.intern("AliveCell");
        let adj = s.interner.intern("adjacent_to");
        let x = s.interner.intern("x");
        let y = s.interner.intern("y");
        // Open vocabulary for the test rule.
        let prov = s.interner.intern("test:open");
        let weight = s.terms.add(crate::term::TermNode::Lit {
            value: Value::Float(1.0),
        });
        s.checker.grammar.add(crate::grammar::Production {
            src: crate::grammar::NodePattern {
                type_: cell,
                var: x,
            },
            edge_type: adj,
            tgt: crate::grammar::NodePattern {
                type_: cell,
                var: y,
            },
            where_: None,
            weight,
            provenance: prov,
        });

        // Kernel where: TypeOf(x) == AliveCell
        let x_var = s.terms.add(crate::term::TermNode::Var { name: x });
        let tof = s.terms.add(crate::term::TermNode::TypeOf { node: x_var });
        let alive_lit = s.terms.add(crate::term::TermNode::Lit {
            value: Value::Str(alive),
        });
        let eq = s.terms.add(crate::term::TermNode::Eq {
            a: tof,
            b: alive_lit,
        });
        let alive_name = s.interner.intern("alive_test");
        s.add_rule(crate::rewrite::RewriteRule {
            name: alive_name,
            match_edges: vec![crate::rewrite::MatchEdge {
                src_var: x,
                edge_type: adj,
                tgt_var: y,
            }],
            where_: Some(eq),
            effects: vec![],
            ..Default::default()
        });
        assert!(
            s.rule_where_jit[0].is_some(),
            "kernel where-clause should JIT compile"
        );

        // Non-kernel where: Sum over neighbours (Filter/source-of-source)
        // The JIT doesn't handle Sum yet → expect None.
        let nbrs = s.terms.add(crate::term::TermNode::Neighbours {
            node: x_var,
            edge_type: adj,
            any_type: false,
        });
        let n_var = s.interner.intern("n");
        let n_t = s.terms.add(crate::term::TermNode::Var { name: n_var });
        let sum = s.terms.add(crate::term::TermNode::Sum {
            source: nbrs,
            var_name: n_var,
            value: n_t,
        });
        let zero = s.terms.add(crate::term::TermNode::Lit {
            value: Value::Int(0),
        });
        let gt = s.terms.add(crate::term::TermNode::Gt { a: sum, b: zero });
        let sum_name = s.interner.intern("sum_test");
        s.add_rule(crate::rewrite::RewriteRule {
            name: sum_name,
            match_edges: vec![crate::rewrite::MatchEdge {
                src_var: x,
                edge_type: adj,
                tgt_var: y,
            }],
            where_: Some(gt),
            effects: vec![],
            ..Default::default()
        });
        assert!(
            s.rule_where_jit[1].is_none(),
            "Sum-using where-clause should NOT JIT compile (interpreter fallback)"
        );
    }

    /// Microbenchmark: Conway-style tick latency. Run with
    /// `cargo test --release --lib substrate::tests::bench_conway_tick -- --nocapture --ignored`.
    /// Builds a 50×50 grid, installs N rules over disjoint edge_types
    /// (only one is "active"), and measures run_rules() latency. With
    /// differential firing the inactive rules should be cheap to skip;
    /// without it every tick re-evaluates every rule from scratch.
    #[test]
    #[ignore]
    fn bench_conway_tick() {
        use std::time::Instant;
        let mut s = empty_substrate();
        let cell = s.interner.intern("Cell");
        let adj = s.interner.intern("adjacent_to");
        let active_et = s.interner.intern("active_edge");
        // Make the grammar open for all edge types we'll use.
        let prov = s.interner.intern("bench:open");
        let weight = s.terms.add(crate::term::TermNode::Lit {
            value: Value::Float(1.0),
        });
        let src_var = s.interner.intern("src");
        let tgt_var = s.interner.intern("tgt");
        for et in [adj, active_et] {
            s.checker.grammar.add(crate::grammar::Production {
                src: crate::grammar::NodePattern {
                    type_: cell,
                    var: src_var,
                },
                edge_type: et,
                tgt: crate::grammar::NodePattern {
                    type_: cell,
                    var: tgt_var,
                },
                where_: None,
                weight,
                provenance: prov,
            });
        }

        // 50×50 grid: 2500 cells, 4 adj edges each (toroidal).
        let n = 50;
        let mut grid: Vec<Vec<NodeID>> = Vec::with_capacity(n);
        for _ in 0..n {
            let mut row = Vec::with_capacity(n);
            for _ in 0..n {
                row.push(s.add_node(cell, FxHashMap::default()));
            }
            grid.push(row);
        }
        for i in 0..n {
            for j in 0..n {
                let me = grid[i][j];
                for (di, dj) in [(-1i32, 0), (1, 0), (0, -1), (0, 1)] {
                    let ni = ((i as i32 + di).rem_euclid(n as i32)) as usize;
                    let nj = ((j as i32 + dj).rem_euclid(n as i32)) as usize;
                    let _ = s.add_edge(me, adj, grid[ni][nj], FxHashMap::default());
                }
            }
        }

        // Install N "irrelevant" rules over the active_edge type which
        // has zero edges in the graph — they should NEVER fire and never
        // be re-evaluated after their first clean pass.
        let x = s.interner.intern("x");
        let y = s.interner.intern("y");
        for k in 0..20 {
            let name_str = format!("noop_{}", k);
            let name = s.interner.intern(&name_str);
            s.add_rule(crate::rewrite::RewriteRule {
                name,
                match_edges: vec![crate::rewrite::MatchEdge {
                    src_var: x,
                    edge_type: active_et,
                    tgt_var: y,
                }],
                where_: None,
                effects: vec![],
                ..Default::default()
            });
        }

        eprintln!(
            "\n=== Conway bench ({} cells, {} edges, {} rules) ===",
            s.graph.node_count(),
            s.graph.edge_count(),
            s.rules.len()
        );

        // First run: every rule starts dirty so we expect full evaluation.
        let t0 = Instant::now();
        let steps = s.run_rules(100);
        let dt0 = t0.elapsed();
        eprintln!("first run_rules: {} steps, {:?}", steps, dt0);

        // Subsequent runs: no mutations, so rules are clean → instant exit.
        let mut total = std::time::Duration::ZERO;
        const N_TICKS: u32 = 1000;
        for _ in 0..N_TICKS {
            let t = Instant::now();
            let _ = s.run_rules(100);
            total += t.elapsed();
        }
        eprintln!(
            "{} clean-tick run_rules avg: {:?}",
            N_TICKS,
            total / N_TICKS
        );
        eprintln!("(should be sub-microsecond if differential firing works)");

        // Mutating run: insert a new edge, re-tick.
        let center = grid[n / 2][n / 2];
        let other = grid[0][0];
        let t = Instant::now();
        let _ = s.add_edge(center, adj, other, FxHashMap::default());
        let _ = s.run_rules(100);
        let dt_mut = t.elapsed();
        eprintln!("mutation + 1 tick: {:?}", dt_mut);
        eprintln!();
    }

    /// Real-workload profile: multi-type graph, mixed rule shapes,
    /// mutations interspersed across ticks. Validates that the wins
    /// shipped (Roaring, differential firing, JIT, cache, snapshot
    /// pattern, slice adjacency) hold up beyond the toy Conway shape.
    ///
    /// Run with `cargo test --release --lib substrate::tests::profile_real_workload -- --nocapture --ignored`.
    #[test]
    #[ignore]
    fn profile_real_workload() {
        use std::time::Instant;
        let mut s = empty_substrate();

        // --- Graph setup: 5 node types, 3 edge types, 5000 nodes, ~15K edges.
        let types: Vec<Sym> = ["Concept", "Frame", "Microtheory", "Mention", "Sign"]
            .iter()
            .map(|n| s.interner.intern(n))
            .collect();
        let edge_types: Vec<Sym> = ["evokes", "denotes", "isa"]
            .iter()
            .map(|n| s.interner.intern(n))
            .collect();

        // Open grammar for all (type, edge_type, type) triples we'll use.
        let prov = s.interner.intern("profile:open");
        let weight = s.terms.add(crate::term::TermNode::Lit {
            value: Value::Float(1.0),
        });
        let src_v = s.interner.intern("src");
        let tgt_v = s.interner.intern("tgt");
        for &et in &edge_types {
            for &t_from in &types {
                for &t_to in &types {
                    s.checker.grammar.add(crate::grammar::Production {
                        src: crate::grammar::NodePattern {
                            type_: t_from,
                            var: src_v,
                        },
                        edge_type: et,
                        tgt: crate::grammar::NodePattern {
                            type_: t_to,
                            var: tgt_v,
                        },
                        where_: None,
                        weight,
                        provenance: prov,
                    });
                }
            }
        }

        // Declare an attr index — exercises the Roaring path.
        let salience_key = s.interner.intern("salience");
        s.graph.declare_attr_index(types[0], salience_key);

        // 5000 nodes, distributed by type. Some with salience attr.
        let mut nodes: Vec<NodeID> = Vec::with_capacity(5000);
        for i in 0..5000 {
            let ty = types[i % types.len()];
            let mut attrs: FxHashMap<Sym, Value> = Default::default();
            if i % 7 == 0 {
                attrs.insert(salience_key, Value::Int((i % 10) as i64));
            }
            nodes.push(s.add_node(ty, attrs));
        }

        // Edges — sparse cross-type connectivity. Each node gets 3 outgoing
        // edges of varying types to nodes ~k away in the slab.
        let mut rng_state: u32 = 0xC0FFEE;
        let mut next_rand = || {
            rng_state = rng_state.wrapping_mul(1664525).wrapping_add(1013904223);
            rng_state
        };
        let mut edges_added: usize = 0;
        for i in 0..nodes.len() {
            for _ in 0..3 {
                let j = (next_rand() as usize) % nodes.len();
                let et = edge_types[(next_rand() as usize) % edge_types.len()];
                if s.add_edge(nodes[i], et, nodes[j], FxHashMap::default())
                    .is_ok()
                {
                    edges_added += 1;
                }
            }
        }

        // --- Rules: 30 across 4 shape categories.

        let x = s.interner.intern("x");
        let y = s.interner.intern("y");
        let z = s.interner.intern("z");

        // (a) 10 simple "always match" rules with no where-clause
        //     — exercises pure matching cost. Empty effects so they don't
        //     progress (we measure matching, not application).
        for k in 0..10 {
            let name = s.interner.intern(&format!("always_{}", k));
            s.add_rule(crate::rewrite::RewriteRule {
                name,
                match_edges: vec![crate::rewrite::MatchEdge {
                    src_var: x,
                    edge_type: edge_types[k % edge_types.len()],
                    tgt_var: y,
                }],
                where_: None,
                effects: vec![],
                ..Default::default()
            });
        }

        // (b) 10 TypeOf-eq where-clauses — JIT-compilable.
        for k in 0..10 {
            let name = s.interner.intern(&format!("type_eq_{}", k));
            let x_var = s.terms.add(crate::term::TermNode::Var { name: x });
            let tof = s.terms.add(crate::term::TermNode::TypeOf { node: x_var });
            let lit = s.terms.add(crate::term::TermNode::Lit {
                value: Value::Str(types[k % types.len()]),
            });
            let eq = s.terms.add(crate::term::TermNode::Eq { a: tof, b: lit });
            s.add_rule(crate::rewrite::RewriteRule {
                name,
                match_edges: vec![crate::rewrite::MatchEdge {
                    src_var: x,
                    edge_type: edge_types[k % edge_types.len()],
                    tgt_var: y,
                }],
                where_: Some(eq),
                effects: vec![],
                ..Default::default()
            });
        }

        // (c) 5 Count(Neighbours) where-clauses — JIT-compilable graph access.
        for k in 0..5 {
            let name = s.interner.intern(&format!("nbr_count_{}", k));
            let x_var = s.terms.add(crate::term::TermNode::Var { name: x });
            let nbrs = s.terms.add(crate::term::TermNode::Neighbours {
                node: x_var,
                edge_type: edge_types[k % edge_types.len()],
                any_type: false,
            });
            let cnt = s.terms.add(crate::term::TermNode::Count { source: nbrs });
            let two = s.terms.add(crate::term::TermNode::Lit {
                value: Value::Int(2),
            });
            let gt = s.terms.add(crate::term::TermNode::Gt { a: cnt, b: two });
            s.add_rule(crate::rewrite::RewriteRule {
                name,
                match_edges: vec![crate::rewrite::MatchEdge {
                    src_var: x,
                    edge_type: edge_types[k % edge_types.len()],
                    tgt_var: y,
                }],
                where_: Some(gt),
                effects: vec![],
                ..Default::default()
            });
        }

        // (d) 5 multi-edge rules (3 match-edges) — exercises cost-based
        //     reorder + the matcher's recursion. No JIT yet for these.
        for k in 0..5 {
            let name = s.interner.intern(&format!("multi_edge_{}", k));
            s.add_rule(crate::rewrite::RewriteRule {
                name,
                match_edges: vec![
                    crate::rewrite::MatchEdge {
                        src_var: x,
                        edge_type: edge_types[0],
                        tgt_var: y,
                    },
                    crate::rewrite::MatchEdge {
                        src_var: y,
                        edge_type: edge_types[1],
                        tgt_var: z,
                    },
                    crate::rewrite::MatchEdge {
                        src_var: x,
                        edge_type: edge_types[2],
                        tgt_var: z,
                    },
                ],
                where_: None,
                effects: vec![],
                ..Default::default()
            });
            let _ = k;
        }

        // --- Report install-time state.
        let total_rules = s.rules.len();
        #[cfg(all(target_arch = "x86_64", target_os = "linux"))]
        let jit_count = s.rule_where_jit.iter().filter(|j| j.is_some()).count();
        #[cfg(not(all(target_arch = "x86_64", target_os = "linux")))]
        let jit_count: usize = 0;
        let with_where = s.rule_has_where.iter().filter(|&&w| w).count();

        eprintln!("\n=== Real-workload profile ===");
        eprintln!(
            "graph: {} nodes, {} edges (added {})",
            s.graph.node_count(),
            s.graph.edge_count(),
            edges_added
        );
        eprintln!(
            "rules: {} total ({} with where-clause; {} JIT-compiled)",
            total_rules, with_where, jit_count
        );

        // --- Phase 1: a single full tick from cold state.
        let t = Instant::now();
        let first_steps = s.run_rules(1000);
        let dt_first = t.elapsed();
        eprintln!(
            "\nfirst tick (all rules dirty): {} steps, {:?}",
            first_steps, dt_first
        );

        // --- Phase 2: 100 idle ticks (no mutation between).
        let mut total = std::time::Duration::ZERO;
        const N_IDLE: u32 = 1000;
        for _ in 0..N_IDLE {
            let t = Instant::now();
            let _ = s.run_rules(100);
            total += t.elapsed();
        }
        let avg_idle = total / N_IDLE;
        eprintln!("idle tick × {} avg: {:?}", N_IDLE, avg_idle);

        // --- Phase 3: 100 ticks each preceded by 1 edge mutation.
        let mut total_mut = std::time::Duration::ZERO;
        let mut mut_steps_total = 0usize;
        const N_MUT: u32 = 100;
        for i in 0..N_MUT {
            let src = nodes[(i as usize * 31) % nodes.len()];
            let tgt = nodes[(i as usize * 17 + 5) % nodes.len()];
            let et = edge_types[(i as usize) % edge_types.len()];
            let t = Instant::now();
            let _ = s.add_edge(src, et, tgt, FxHashMap::default());
            mut_steps_total += s.run_rules(100);
            total_mut += t.elapsed();
        }
        let avg_mut = total_mut / N_MUT;
        eprintln!(
            "mutate+tick × {} avg: {:?} ({:.1} steps/tick)",
            N_MUT,
            avg_mut,
            mut_steps_total as f64 / N_MUT as f64
        );

        // --- Cache stats at the end.
        eprintln!("\neval_cache at end:");
        eprintln!("  filter:     {} entries", s.eval_cache.filter.len());
        eprintln!("  neighbours: {} entries", s.eval_cache.neighbours.len());
        eprintln!("  holds:      {} entries", s.eval_cache.holds.len());

        eprintln!();
    }

    /// Multi-spec fan-out regression test. Before the
    /// `try_incremental_match` fix, a 1-edge rule wired against N
    /// PrimitiveSpec-equivalent nodes via the same edge_type advanced
    /// the per-edge-type cursor after the FIRST progressing binding
    /// and returned — so a single `run_rules` call applied the rule
    /// once total instead of N times. After the fix, every admissible
    /// binding fires in a single tick.
    #[test]
    fn try_incremental_match_drains_all_admissible_bindings_in_one_tick() {
        let mut s = empty_substrate();
        let trigger_t = s.interner.intern("PhaseTrigger");
        let spec_t = s.interner.intern("PrimitiveSpec");
        let patch_t = s.interner.intern("DesignedPatch");
        let edge_et = s.interner.intern("has_primitive_spec");
        let src_var = s.interner.intern("trig");
        let tgt_var = s.interner.intern("spec");

        // Open productions: trigger -[has_primitive_spec]-> spec; and
        // patch nodes (no edges between them needed for this test).
        let prov = s.interner.intern("test:multi_spec");
        let w = crate::grammar::Grammar::default_weight(&mut s.terms);
        s.add_production(crate::grammar::Production {
            src: crate::grammar::NodePattern {
                type_: trigger_t,
                var: src_var,
            },
            edge_type: edge_et,
            tgt: crate::grammar::NodePattern {
                type_: spec_t,
                var: tgt_var,
            },
            where_: None,
            weight: w,
            provenance: prov,
        });

        // One trigger + THREE specs, all wired before any rule fires —
        // exactly the shape the language inference refactor produced.
        let trigger = s.add_node(trigger_t, FxHashMap::default());
        let mut specs = Vec::with_capacity(3);
        for i in 0..3 {
            let key = s.interner.intern("spec_id");
            let mut attrs = FxHashMap::default();
            attrs.insert(key, Value::Int(i));
            let spec = s.add_node(spec_t, attrs);
            s.add_edge(trigger, edge_et, spec, FxHashMap::default())
                .unwrap();
            specs.push(spec);
        }

        // Rule: for every spec wired to the trigger, emit one
        // DesignedPatch node carrying the spec's spec_id.
        let spec_var_t = s.terms.add(crate::term::TermNode::Var { name: tgt_var });
        let spec_id_key = s.interner.intern("spec_id");
        let spec_id_term = s.terms.add(crate::term::TermNode::Attr {
            node: spec_var_t,
            key: spec_id_key,
        });
        let patch_name = s.interner.intern("emit_patch");
        let patch_var = s.interner.intern("p");
        s.add_rule(crate::rewrite::RewriteRule {
            name: patch_name,
            match_edges: vec![crate::rewrite::MatchEdge {
                src_var,
                edge_type: edge_et,
                tgt_var,
            }],
            where_: None,
            effects: vec![crate::rewrite::Effect::AddNode {
                new_var: patch_var,
                type_: patch_t,
                attrs: vec![(
                    spec_id_key,
                    crate::rewrite::EffectArg::Computed(spec_id_term),
                )],
            }],
            ..Default::default()
        });

        // Single tick — should fan out across all 3 specs.
        let _ = s.run_rules(100);
        let n_patches = s.graph.nodes_of_type(patch_t).len();
        assert_eq!(
            n_patches, 3,
            "multi-spec fan-out: 3 specs, 1 tick, expected 3 \
                    patches; got {}",
            n_patches
        );
    }

    // --- remove_rule (tombstone semantics) ------------------------------

    #[test]
    fn remove_rule_stops_firing_but_index_stays_valid() {
        let mut s = empty_substrate();
        let src_t = s.interner.intern("Trigger");
        let tgt_t = s.interner.intern("Target");
        let minted_t = s.interner.intern("Minted");
        let et = s.interner.intern("triggers");
        let src_var = s.interner.intern("src");
        let tgt_var = s.interner.intern("tgt");
        let new_var = s.interner.intern("m");

        let a = s.add_node(src_t, FxHashMap::default());
        let b = s.add_node(tgt_t, FxHashMap::default());
        s.graph.insert_edge(a, et, b, FxHashMap::default()).unwrap();

        let mint_on_trigger = s.interner.intern("mint_on_trigger");
        let idx = s.add_rule(crate::rewrite::RewriteRule {
            name: mint_on_trigger,
            match_edges: vec![crate::rewrite::MatchEdge {
                src_var,
                edge_type: et,
                tgt_var,
            }],
            where_: None,
            effects: vec![crate::rewrite::Effect::AddNode {
                new_var,
                type_: minted_t,
                attrs: vec![],
            }],
            ..Default::default()
        });

        // Fires while active.
        assert!(s.apply_rule_once(idx), "rule should fire while active");
        assert_eq!(s.graph.nodes_of_type(minted_t).len(), 1);

        // Remove it — first call reports success.
        assert!(
            s.remove_rule(idx),
            "first remove_rule call deactivates a live rule"
        );

        // Never fires again, even though the same admissible binding
        // still exists in the graph (removal isn't "consume the match
        // once", it's "this rule is gone").
        assert!(
            !s.apply_rule_once(idx),
            "tombstoned rule must not match/apply"
        );
        assert_eq!(
            s.graph.nodes_of_type(minted_t).len(),
            1,
            "no new node minted by a removed rule"
        );

        // Double-remove is safe / idempotent (no panic, reports no-op).
        assert!(!s.remove_rule(idx), "second remove_rule call is a no-op");

        // Out-of-range index is safe too.
        assert!(!s.remove_rule(crate::rewrite::RuleIdx(9999)));

        // The slot is tombstoned, not compacted — the index space is stable.
        assert_eq!(
            s.rules.len(),
            1,
            "remove_rule must not shrink/reindex the rule store"
        );
    }

    #[test]
    fn remove_rule_leaves_other_rules_unaffected() {
        let mut s = empty_substrate();
        let n = s.interner.intern("N");
        let a_et = s.interner.intern("A");
        let b_et = s.interner.intern("B");
        let x = s.interner.intern("x");
        let y = s.interner.intern("y");
        let minted_a = s.interner.intern("MintedA");
        let minted_b = s.interner.intern("MintedB");
        let new_var = s.interner.intern("m");

        let n1 = s.graph.insert_node(n, FxHashMap::default());
        let n2 = s.graph.insert_node(n, FxHashMap::default());
        s.graph
            .insert_edge(n1, a_et, n2, FxHashMap::default())
            .unwrap();
        s.graph
            .insert_edge(n1, b_et, n2, FxHashMap::default())
            .unwrap();

        let rule_a_name = s.interner.intern("rule_A");
        let idx_a = s.add_rule(crate::rewrite::RewriteRule {
            name: rule_a_name,
            match_edges: vec![crate::rewrite::MatchEdge {
                src_var: x,
                edge_type: a_et,
                tgt_var: y,
            }],
            where_: None,
            effects: vec![crate::rewrite::Effect::AddNode {
                new_var,
                type_: minted_a,
                attrs: vec![],
            }],
            ..Default::default()
        });
        let rule_b_name = s.interner.intern("rule_B");
        let _idx_b = s.add_rule(crate::rewrite::RewriteRule {
            name: rule_b_name,
            match_edges: vec![crate::rewrite::MatchEdge {
                src_var: x,
                edge_type: b_et,
                tgt_var: y,
            }],
            where_: None,
            effects: vec![crate::rewrite::Effect::AddNode {
                new_var,
                type_: minted_b,
                attrs: vec![],
            }],
            ..Default::default()
        });

        assert!(s.remove_rule(idx_a));

        s.run_rules(100);
        assert_eq!(
            s.graph.nodes_of_type(minted_a).len(),
            0,
            "removed rule_A must not fire"
        );
        assert_eq!(
            s.graph.nodes_of_type(minted_b).len(),
            1,
            "sibling rule_B must still fire normally after rule_A is removed"
        );
    }

    /// Regression guard for the exact hazard `remove_rule`'s doc comment
    /// calls out: `mark_edge_type_dirty` / `mark_node_mutation` don't know
    /// a rule was removed, so a later unrelated mutation CAN re-set a
    /// tombstoned rule's dirty bit. `run_rules` must still never schedule
    /// it — the `active` filter is what actually enforces "removed means
    /// removed", not the one-time dirty-bit clear at removal time.
    #[test]
    fn remove_rule_stays_inert_even_if_its_dirty_bit_is_later_reset() {
        let mut s = empty_substrate();
        let n = s.interner.intern("N");
        let et = s.interner.intern("E");
        let x = s.interner.intern("x");
        let y = s.interner.intern("y");
        let minted = s.interner.intern("Minted");
        let new_var = s.interner.intern("m");

        let n1 = s.graph.insert_node(n, FxHashMap::default());
        let n2 = s.graph.insert_node(n, FxHashMap::default());
        s.graph
            .insert_edge(n1, et, n2, FxHashMap::default())
            .unwrap();

        let mint_on_e = s.interner.intern("mint_on_e");
        let idx = s.add_rule(crate::rewrite::RewriteRule {
            name: mint_on_e,
            match_edges: vec![crate::rewrite::MatchEdge {
                src_var: x,
                edge_type: et,
                tgt_var: y,
            }],
            where_: None,
            effects: vec![crate::rewrite::Effect::AddNode {
                new_var,
                type_: minted,
                attrs: vec![],
            }],
            ..Default::default()
        });

        s.run_rules(100);
        assert_eq!(s.graph.nodes_of_type(minted).len(), 1);

        assert!(s.remove_rule(idx));

        // Open production so the CHECKED `add_edge` (which drives
        // `mark_edge_type_dirty`) is admissible for edge_type `et`.
        let prov = s.interner.intern("test:open_remove_rule");
        let weight = s.terms.add(crate::term::TermNode::Lit {
            value: Value::Float(1.0),
        });
        s.checker.grammar.add(crate::grammar::Production {
            src: crate::grammar::NodePattern { type_: n, var: x },
            edge_type: et,
            tgt: crate::grammar::NodePattern { type_: n, var: y },
            where_: None,
            weight,
            provenance: prov,
        });
        let n3 = s.graph.insert_node(n, FxHashMap::default());
        s.add_edge(n1, et, n3, FxHashMap::default()).unwrap();
        assert_eq!(
            s.rule_dirty[idx.0 as usize], true,
            "mark_edge_type_dirty doesn't know about removal — the bit CAN be re-set"
        );

        // But run_rules's `active` filter must still keep it from firing.
        s.run_rules(100);
        assert_eq!(
            s.graph.nodes_of_type(minted).len(),
            1,
            "tombstoned rule must not fire even with a fresh new edge on its own edge_type"
        );
    }

    // --- FIXPOINT SETTLE: run_rules must not return over unsettled state ---

    /// Build the three-rule graph both settle tests share.
    ///
    /// SHAPE (this is the motion-rung / cut-mint shape, minimised):
    ///
    ///   chain:  s1 -[step]-> s2 -[step]-> s3     (drives `churn` for 2 passes)
    ///   gate:   s3 -[gate]-> n1                  (drives `open_gate`, late)
    ///   link:   n1 -[link]-> n2                  (STABLE — never added to)
    ///
    ///   churn     (idx 0): ?a -[step]-> ?b  where ?a.on == 1
    ///                      => ?b.on = 1 ; add ?b -[tag]-> ?b
    ///   open_gate (idx 1): ?p -[gate]-> ?q  where ?p.on == 1
    ///                      => ?q.go = 1                     (the ATTR write)
    ///   consume   (idx 2): ?x -[link]-> ?y  where ?x.go == 1 && |tag(?x)| == 0
    ///                      => mint Marker                   (the STARVED rule)
    ///
    /// `consume` reads Edge(tag) — so `churn` dirties it STRUCTURALLY (which by
    /// design does NOT clear its cursor) — and reads Attr(go), which only
    /// `open_gate` writes. `open_gate` fires in the SAME pass, AFTER churn has
    /// already set consume's dirty bit.
    fn settle_repro(pre_open_gate: bool) -> (Substrate, Sym, crate::graph::NodeID) {
        let mut s = empty_substrate();
        let node_t = s.interner.intern("N");
        let marker_t = s.interner.intern("Marker");
        let step = s.interner.intern("step");
        let gate = s.interner.intern("gate");
        let link = s.interner.intern("link");
        let tag = s.interner.intern("tag");
        let k_on = s.interner.intern("on");
        let k_go = s.interner.intern("go");

        // Open production for `tag` — the only edge type a rule EFFECT creates.
        let v_a = s.interner.intern("a");
        let v_b = s.interner.intern("b");
        let prov = s.interner.intern("test:settle");
        let w = crate::grammar::Grammar::default_weight(&mut s.terms);
        s.add_production(crate::grammar::Production {
            src: crate::grammar::NodePattern {
                type_: node_t,
                var: v_a,
            },
            edge_type: tag,
            tgt: crate::grammar::NodePattern {
                type_: node_t,
                var: v_b,
            },
            where_: None,
            weight: w,
            provenance: prov,
        });

        let mut on1 = FxHashMap::default();
        on1.insert(k_on, Value::Int(1));
        let s1 = s.graph.insert_node(node_t, on1);
        let s2 = s.graph.insert_node(node_t, FxHashMap::default());
        let s3 = s.graph.insert_node(node_t, FxHashMap::default());
        // R2 arm: the gate attribute is present BEFORE the first binding is
        // ever evaluated — the motion rung's actual fix, reproduced here.
        let mut n1_attrs = FxHashMap::default();
        if pre_open_gate {
            n1_attrs.insert(k_go, Value::Int(1));
        }
        let n1 = s.graph.insert_node(node_t, n1_attrs);
        let n2 = s.graph.insert_node(node_t, FxHashMap::default());

        s.graph
            .insert_edge(s1, step, s2, FxHashMap::default())
            .unwrap();
        s.graph
            .insert_edge(s2, step, s3, FxHashMap::default())
            .unwrap();
        s.graph
            .insert_edge(s3, gate, n1, FxHashMap::default())
            .unwrap();
        s.graph
            .insert_edge(n1, link, n2, FxHashMap::default())
            .unwrap();

        let one = s.terms.add(crate::term::TermNode::Lit {
            value: Value::Int(1),
        });
        let zero = s.terms.add(crate::term::TermNode::Lit {
            value: Value::Int(0),
        });

        let nm_churn = s.interner.intern("churn");
        // churn (idx 0)
        let a_var = s.terms.add(crate::term::TermNode::Var { name: v_a });
        let a_on = s.terms.add(crate::term::TermNode::Attr {
            node: a_var,
            key: k_on,
        });
        let churn_where = s.terms.add(crate::term::TermNode::Eq { a: a_on, b: one });
        s.add_rule(crate::rewrite::RewriteRule {
            name: nm_churn,
            match_edges: vec![crate::rewrite::MatchEdge {
                src_var: v_a,
                edge_type: step,
                tgt_var: v_b,
            }],
            where_: Some(churn_where),
            effects: vec![
                crate::rewrite::Effect::SetAttrIfDifferent {
                    var: v_b,
                    key: k_on,
                    value: crate::rewrite::EffectArg::Literal(Value::Int(1)),
                },
                crate::rewrite::Effect::AddEdge {
                    src_var: v_b,
                    edge_type: tag,
                    tgt_var: v_b,
                    attrs: vec![],
                },
            ],
            ..Default::default()
        });

        let nm_open_gate = s.interner.intern("open_gate");
        // open_gate (idx 1)
        let v_p = s.interner.intern("p");
        let v_q = s.interner.intern("q");
        let p_var = s.terms.add(crate::term::TermNode::Var { name: v_p });
        let p_on = s.terms.add(crate::term::TermNode::Attr {
            node: p_var,
            key: k_on,
        });
        let gate_where = s.terms.add(crate::term::TermNode::Eq { a: p_on, b: one });
        s.add_rule(crate::rewrite::RewriteRule {
            name: nm_open_gate,
            match_edges: vec![crate::rewrite::MatchEdge {
                src_var: v_p,
                edge_type: gate,
                tgt_var: v_q,
            }],
            where_: Some(gate_where),
            effects: vec![crate::rewrite::Effect::SetAttrIfDifferent {
                var: v_q,
                key: k_go,
                value: crate::rewrite::EffectArg::Literal(Value::Int(1)),
            }],
            ..Default::default()
        });

        let nm_consume = s.interner.intern("consume");
        // consume (idx 2) — the rule that gets starved.
        let v_x = s.interner.intern("x");
        let v_y = s.interner.intern("y");
        let x_var = s.terms.add(crate::term::TermNode::Var { name: v_x });
        let x_go = s.terms.add(crate::term::TermNode::Attr {
            node: x_var,
            key: k_go,
        });
        let go_is_1 = s.terms.add(crate::term::TermNode::Eq { a: x_go, b: one });
        let x_tags = s.terms.add(crate::term::TermNode::Neighbours {
            node: x_var,
            edge_type: tag,
            any_type: false,
        });
        let n_tags = s.terms.add(crate::term::TermNode::Count { source: x_tags });
        let no_tags = s
            .terms
            .add(crate::term::TermNode::Eq { a: n_tags, b: zero });
        let consume_where = s.terms.add(crate::term::TermNode::And {
            items: vec![go_is_1, no_tags],
        });
        let v_m = s.interner.intern("m");
        s.add_rule(crate::rewrite::RewriteRule {
            name: nm_consume,
            match_edges: vec![crate::rewrite::MatchEdge {
                src_var: v_x,
                edge_type: link,
                tgt_var: v_y,
            }],
            where_: Some(consume_where),
            effects: vec![crate::rewrite::Effect::AddNodeIfAbsent {
                new_var: v_m,
                type_: marker_t,
                attrs: vec![(k_go, crate::rewrite::EffectArg::Literal(Value::Int(1)))],
            }],
            ..Default::default()
        });

        (s, marker_t, n1)
    }

    /// **THE DEFECT.** `run_rules` returns reporting a fixed point while
    /// `consume`'s where-clause is TRUE on an admissible binding that was
    /// never applied.
    ///
    /// MECHANISM (`dirty_by_writeset`, the `if self.rule_dirty[j] { continue; }`
    /// early-out): dirtying a consumer and INVALIDATING ITS CURSOR are two
    /// distinct obligations, and that early-out discharges only the first. When
    /// `churn` dirties `consume` STRUCTURALLY (Edge(tag)) — which correctly
    /// leaves the semi-naive cursor intact, since new edges drive the rescan —
    /// and `open_gate` then writes Attr(go) LATER IN THE SAME PASS, `consume`
    /// is already dirty, so it is skipped and its cursor is never cleared.
    /// `consume` is then tried on the incremental path with a VALID cursor and
    /// ZERO new `link` edges, enumerates nothing, and cannot observe the
    /// attribute flip on its stable edge. Every rule reports no progress, so
    /// `!any_progress` returns a "fixed point" over unsettled state.
    ///
    /// This is the engine's own named `stable-edge attr-gated bug`
    /// (`try_incremental_match`'s trace string), reached through a path the
    /// `dirty_by_writeset` mitigation was written to close.
    #[test]
    fn run_rules_returns_over_unsettled_state_when_attr_write_follows_structural_dirty() {
        // n1 comes back from `settle_repro` rather than a hard-coded
        // `NodeID(3)` literal: `add_production` (called inside
        // `settle_repro`, before n1 is created) now also mirrors the
        // production into the graph (`grammar_reflect.rs`), which
        // allocates its own NodeIDs first and shifts every
        // insertion-order-derived ID that follows. The FIXPOINT-SETTLE
        // behaviour this test is actually about is unaffected — only
        // the ID literal was ever load-bearing on insertion order.
        let (mut s, marker_t, n1) = settle_repro(false);
        let k_go = s.interner.intern("go");

        let steps = s.run_rules(1000);

        // The precondition the assertion below is ABOUT: the attribute write
        // DID land, so `consume`'s where-clause is genuinely true.
        assert_eq!(
            s.graph.node(n1).attrs.get(&k_go),
            Some(&Value::Int(1)),
            "precondition: open_gate must have written go=1 on n1"
        );

        let markers = s.graph.nodes_of_type(marker_t).len();

        // A second, INDEPENDENT run must be a no-op if the first really
        // reached a fixed point. This is the settle check, in the reader.
        let extra = s.run_rules(1000);

        assert_eq!(
            markers, 1,
            "run_rules({steps}) reported a fixed point, but `consume`'s \
                    where-clause is TRUE on n1 -[link]-> n2 and was never \
                    applied: {markers} Markers minted, expected 1. A further \
                    run_rules made {extra} more steps — a fixed point that is \
                    not a fixed point."
        );
    }

    /// **R2 — the motion rung's fix, reproduced.** The identical graph and the
    /// identical rules settle completely when the gating attribute is present
    /// BEFORE the first binding is evaluated. This is what isolates the defect
    /// to the SCHEDULING of the attribute write rather than to the rule set,
    /// the where-clause, or the graph shape — all three are held constant.
    #[test]
    fn settle_repro_settles_when_the_attribute_is_present_before_the_first_pass() {
        let (mut s, marker_t, _n1) = settle_repro(true);
        let _ = s.run_rules(1000);
        assert_eq!(
            s.graph.nodes_of_type(marker_t).len(),
            1,
            "control: with go=1 present up front, consume MUST fire"
        );
    }
}

/// Greedy connectivity order for a seeded sub-match (`seeded_join_order`): from
/// the seed's bound variables, repeatedly take the remaining edge with the most
/// bound endpoints (2 = an O(1) membership test, 1 = an adjacency walk, 0 = a
/// type scan), ties in declared order. Traversal only -- same binding set.
pub(crate) fn seeded_join_order(
    edges: Vec<crate::rewrite::MatchEdge>,
    a: Sym,
    b: Sym,
) -> Vec<crate::rewrite::MatchEdge> {
    let mut bound: smallvec::SmallVec<[Sym; 8]> = smallvec::smallvec![a, b];
    let mut rest = edges;
    let mut out = Vec::with_capacity(rest.len());
    while !rest.is_empty() {
        let mut best = 0usize;
        let mut best_score = -1i32;
        for (i, me) in rest.iter().enumerate() {
            let sc = bound.contains(&me.src_var) as i32 + bound.contains(&me.tgt_var) as i32;
            if sc > best_score {
                best_score = sc;
                best = i;
            }
        }
        let me = rest.remove(best);
        for v in [me.src_var, me.tgt_var] {
            if !bound.contains(&v) {
                bound.push(v);
            }
        }
        out.push(me);
    }
    out
}

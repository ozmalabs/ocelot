# Per-Mt scoped rule fixpoint — closing the `run_rules()`-orchestration blocker — PREREG

Base `main @ d9edae8` ("Merge can-final-migration: wire the three closed
primitives, find the real reason 4/6 stay blocked, GO"), verified via
`git log --oneline -1 main` before branching. Worktree
`/home/matt/ozmadev/ocelot-worktrees/can-mt-scoped-rules`, branch
`can-mt-scoped-rules`.

This rung executes the exact thing `CAN_FINAL_MIGRATION_RESULTS.md` named as
the real, unifying blocker for its own remaining four consumers (§0 of that
document, quoted in the task): `run_rules()` has **no per-Mt scope** — every
native CAN rule in both seeds (`can_native_reimplementation.json`,
`can_decay_identity.json`) matches `[mt, has_concept, ...]` unscoped, so
calling `run_rules()` "for" one Microtheory silently mutates a completely
unrelated Microtheory's state. That prior rung's own live probe (quoted
verbatim in its §0) is this rung's starting fact, not re-derived.

## 0. Blast-radius framing (read before any code)

`runners/dsl/src/rewrite.rs::run_rules`/`run_rules_opts` (`:2116-2148`,
confirmed by direct read) is the free-function fixpoint matcher every rule
engine entry point ultimately composes with. The PRODUCTION entry point
actually reached from Python is `Substrate::run_rules`/`run_rules_opts`
(`substrate.rs:4114-4166`, delegating to `run_rules_opts_filtered` at
`:4168-4326`) — a SEPARATE, much larger dirty-bit-tracked incremental engine
(`attempt_one_rule`, `substrate.rs:3606+`) with per-rule cursors, predicate
retraction, and a projection cold path. **This PREREG's core design decision
is to add scoping WITHOUT touching that incremental machinery at all**: the
new scoped runner is a freshly-written, always-full-rematch loop (no
incremental cursor reuse), reached only via a brand-new `Substrate` method
(`run_rules_scoped`) whose `scope_mt=None` arm does not call any new code —
it calls the existing `self.run_rules_opts(...)` directly, unchanged, so
"None reproduces exact behaviour" holds by construction (same code path, not
a re-implementation that merely intends to match it) rather than by
after-the-fact comparison alone (which we ALSO run, per house discipline).

This keeps the additive property trivially provable for the highest-traffic
path (every existing seed, every existing caller) at the cost of the new
`Some(mt)` path being unoptimised (full re-match every pass, no incremental
cursor, no JIT where-clause). That trade is explicitly accepted: this rung's
job is a correctness-first orchestration primitive for a handful of CAN
consumer call sites, not a scheduler-level feature.

## 1. Where the scope filter goes: POST-match, not pre-match — decided and justified

Two places a filter could go (per the task's own framing):

- **Pre-match (candidate narrowing).** Restrict the node set a rule's first
  match-edge scans to `owned(mt)` before the backtracking matcher runs at
  all. Cheaper (prunes the search), but requires knowing WHICH match-edge
  variable denotes "the Mt" per rule — not declared anywhere in
  `RewriteRule`, and a generic "narrow candidates to `owned(mt)`" restriction
  applied to every match-edge could silently miss a valid binding whose
  Mt-defining edge is not the first-enumerated one (rule-authoring-order
  dependent — fragile).
- **Post-match (binding filter).** Let `match_rule_each` enumerate exactly as
  it does today (unchanged matcher, zero risk of missing a valid binding),
  then discard any binding that does not TOUCH the target Mt's owned node
  set: `binding.values().any(|nid| owned.contains(nid))`. Safe regardless of
  which variable in the pattern carries the Mt reference; costs the pruning
  the pre-match option would have bought.

**Decision: post-match.** House priority for this rung is explicitly
correctness over performance (task: "the one thing that must NOT be partial
or approximate is the core correctness property"). All six real CAN rules
across both seeds (`can_native_update_3state/_2state`,
`can_native_hebbian_mint/_reweight`, `can_native_identity_evidence_sample/
_decay`) bind an `mt` variable directly as the src of a `has_concept`
match-edge — confirmed by direct read of both seed JSONs — so in every real
case today the post-match filter reduces to an exact `binding["mt"] ==
target_mt` check; the more general "touches owned(mt)" form is a documented,
deliberate generalisation for rules that don't literally bind a var named
`mt` (or that reference concepts without re-binding the Mt var itself), not
an untested guess.

**Ownership definition reused, not invented**: `owned(mt) = {mt} ∪
neighbours(mt, has_concept)` — literally `can_ops.rs::mt_concepts`'s own
definition (`g.neighbours(mt_id, Some(has_concept))`, `can_ops.rs:156-158`),
plus the Mt node itself so a binding that only touches `mt` (no concept var)
still counts as in-scope.

**Named limitation, not silently swept under the post-match choice**: this
is a "touches ANY" filter, not "touches ONLY" — a hypothetical rule whose
pattern spans two different Mts (one shared Concept) would fire when scoped
to EITHER Mt. No rule in either CAN seed does this today (every real pattern
re-binds a single `mt` var across all its concept references), and the
two-Mt isolation demo below uses fully disjoint Mts, so this does not affect
today's correctness claim — but it is not "touches ALL", and is reported as
such rather than glossed.

## 2. The additive API — registered exactly, before writing it

New, free functions in `rewrite.rs` (nothing existing edited):

```rust
pub fn mt_owned_nodes(graph: &TypedGraph, mt: NodeID, has_concept: Sym)
    -> rustc_hash::FxHashSet<NodeID>;

pub fn run_rules_opts_scoped(
    rules: &[&RewriteRule], arena: &mut TermArena, graph: &mut TypedGraph,
    interner: &mut Interner, concepts: Option<&mut ConceptResolver>,
    framebuffers: Option<&crate::framebuffer::FbRegistry>,
    cache: Option<&mut crate::term::EvalCache>,
    max_steps: usize, detect_cycles: bool,
    owned: &rustc_hash::FxHashSet<NodeID>,
) -> usize;
```

New `Substrate` method (`substrate.rs`, nothing existing edited):

```rust
pub fn run_rules_scoped(&mut self, max_steps: usize, detect_cycles: bool,
                         scope_mt: Option<NodeID>) -> usize {
    match scope_mt {
        None => self.run_rules_opts(max_steps, detect_cycles), // SAME call, unedited
        Some(mt) => { /* build owned(mt), call run_rules_opts_scoped */ }
    }
}
```

New PyO3 method (`py.rs`, alongside the existing `run_rules`/`run_rules_settle`
wrappers, nothing existing edited):

```rust
#[pyo3(signature = (max_steps=100_000, detect_cycles=false, scope_mt=None))]
fn run_rules_scoped(&mut self, py: Python<'_>, max_steps: usize,
                     detect_cycles: bool,
                     scope_mt: Option<PyRef<'_, PyNodeID>>) -> usize;
```

## 3. Backward-compatibility proof scenario (registered before code)

Reuse `tests/test_can_native_reimplementation.py`'s own core 3-state
convergence scenario (a small hub-and-spoke `Microtheory` with
`discrete_mode="3state"`, external fields driving an asynchronous
threshold-update convergence). Procedure:

1. Build the scenario, call the EXISTING `substrate.run_rules(max_steps)`
   (unmodified path). Record final `state` for every Concept + step count.
2. Rebuild the identical scenario from scratch, call the NEW
   `substrate.run_rules_scoped(max_steps, False, None)`. Record the same.
3. Assert byte-identical: same step count, same final `state` per node, same
   intermediate convergence trace if the test captures one. `None` must not
   merely "look the same" — it is required to be produced by literally the
   same code path (see §0), and this test is the empirical cross-check on
   top of that structural guarantee.

## 4. Two-Mt isolation demonstration scenario (registered before code)

Build TWO independent `Microtheory` nodes in the SAME graph:

- **Mt A**: `discrete_mode="3state"`, `update_policy="adaptive"`, 2-3
  Concepts, a `causal_influence` coupling, external fields chosen so
  `can_native_update_3state` has at least one pending (non-fixed-point)
  update available.
- **Mt B**: `discrete_mode="3state"`, `update_policy="adaptive"`, a
  DISJOINT set of 2-3 Concepts (no shared node, no cross edge), its own
  coupling, its own external fields, ALSO with a pending update available.

Procedure:

1. Snapshot every Concept's `state` in both Mts.
2. Call `run_rules_scoped(max_steps, False, Some(mt_a))`.
3. Assert: Mt A's Concepts show real, non-trivial state change (at least one
   flip); every Mt B Concept's `state` is byte-identical to its step-1
   snapshot (untouched, unlike the OLD `run_rules()` global-scope behaviour
   this rung's base commit already demonstrated flips it).
4. Reset, repeat symmetrically for `Some(mt_b)`: B advances, A stays
   byte-identical.
5. Report the real recorded state dicts before/after both directions — not
   a pass/fail assertion alone.

## 5. Consumer migration plan (four named consumers)

Per `CAN_FINAL_MIGRATION_RESULTS.md`'s own operation-by-operation table,
using the SAME `Mt.discrete_mode`-gated dual-path pattern already
established for `drive_curiosity.py`/`insight_seeking.py`:

- `self_improvement_loop.py::relax` — native branch calls
  `run_rules_scoped(mt)` to let `can_native_update_3state/_2state` settle
  that Mt only; continuous branch (`mt_relax_to_marginal`) byte-unchanged.
- `self_improvement_loop.py::maybe_hebbian` — native branch calls
  `run_rules_scoped(mt)` to let `can_native_hebbian_mint/_reweight` fire
  (both already carry their own `mt_allows`-equivalent policy gate inside
  the rule's own `where`, confirmed by direct read — no double-gating
  needed); continuous branch (`mt_hebbian_update_J`) byte-unchanged.
- `self_improvement_loop.py::maybe_decay_J`/`maybe_decay_h` — investigate
  live whether `can_decay_identity.json` actually has a native J/h DECAY
  rule (its own rule set, read live: `can_native_evidence_decay`,
  `can_native_identity_evidence_sample/_decay` — names suggest EVIDENCE
  counter decay, not direct `causal_influence`/`external_field` decay; this
  PREREG does not assume the mapping and the RESULTS doc reports exactly
  what was found before wiring anything).
- `self_improvement_loop.py`'s `mt_audit_basin`/`mt_distance_to_target`
  calls — per `CAN_FINAL_MIGRATION_RESULTS.md` §0's own finding, these are
  NOT a separate gap; a native branch can read `state` directly (no relax)
  and feed `mt_energy`/`mt_frustration_given_state`/`mt_target`'s
  representation-agnostic math, now that scoping removes the reason using
  `run_rules()` per-Mt was unsafe to begin with. Build the small
  "native-marginal-from-state" composition this PREREG names.
- `self_improvement_loop.py::maybe_update_identity` /
  `nudge_identity_on_flipped` — investigated for point 4 below
  (identity-feedback). If confirmed still genuinely unbuilt (independent of
  scoping), these STAY BLOCKED and that is reported as the correct, honest
  outcome, not a shortfall.
- `insight_detection.py::consolidate_insight` — native branch calls
  `run_rules_scoped(mt)` instead of `mt_hebbian_update_J(mt, eta)`; the
  native Hebbian mechanism has no continuous `eta` knob (mint/reweight are
  threshold- and counter-based), so the native branch's return value is
  reported as "edges touched" rather than an eta-scaled quantity — a
  genuine simplification, in the same spirit as the prior rung's
  `predict_perturbation_impact` migration, reported with real before/after
  numbers rather than assumed equivalent.
- `insight_propagation.py::propagate_insight` — native branch for
  `other_mt` calls `run_rules_scoped(other_mt)` in place of
  `mt_relax_to_marginal(other_mt)`, and the native-marginal-from-state
  composition in place of `mt_audit_basin(other_mt)`.
- `sparseness_signal.py` — re-confirm zero `can_ops` calls (inherits #6's
  status per the prior rung); if still true, zero lines touched, as before.

## 6. Identity-feedback investigation (point 4) — the question to answer, not the answer

`CAN_DECAY_IDENTITY_RESULTS.md` names the READING half of identity dynamics
as built (log-odds render) and the FEEDBACK half — `identity_field`
participating in `can_native_update_3state`'s own local-field sum — as
explicitly deferred. This PREREG's prediction, to be confirmed or falsified
by direct read of the rule bodies before any wiring: scoping is an
ORCHESTRATION fix (which Mt a rule pass is allowed to touch); identity
feedback is a MATH/RULE-BODY fix (whether `identity_field` is summed into
the local field `can_native_update_3state` computes and whether any rule
WRITES `identity_field` from the evidence counters
`can_native_identity_evidence_sample/_decay` already maintain). These look
independent on inspection — scoping does not add or remove any term from
the local-field computation — but the RESULTS doc reports this from a
direct read of the rule effects, not from this prediction alone.

## 7. Regression plan (elevated, per task)

Full Rust suite (`cargo test --release --lib -- --test-threads=1`, paired
failing-test-name lists if anything regresses, never bare counts); every
CAN-adjacent Python test file named in the task; a broad `pytest tests/ -k
migrated` sweep. Baseline run BEFORE any code change, per house discipline,
so "unchanged" claims are comparisons, not assumptions.

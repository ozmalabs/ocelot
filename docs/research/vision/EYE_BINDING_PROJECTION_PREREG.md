# SHIP THE LINEAR EYE — enable `binding_projection` on the committed eye path (PRE-REGISTRATION)

**Block 195000.** Committed **ALONE**, BEFORE any number of this rung is produced.
Base `main` @ `c27209943b370448a52d5a0d368ac60c786cde74` (the 194000 ledger).

---

## §0 The rung this closes

Block **188000** built the `binding_projection` engine flag (`set_binding_projection`,
DEFAULT OFF) — a droppable, byte-identical *mirror* that deduplicates a rule's binding
set on the variables its where-clause and effects actually reference. It proved the
eye's most expensive scheduler rule, `ct_area_effort_tracks_live_salience`
(`seeds/cognitive_scheduler.json`), is **projectable to `["area"]`**: its match is
`area -has_task-> task`, and `task` is referenced in NEITHER the where-clause NOR the
effects. 188000 left the flag DEFAULT OFF because its **raw `graph_to_dict` md5** gate
failed on a non-observable edge-insertion-order scatter — so the eye shipped QUADRATIC.

This rung SHIPS the fix: it turns the flag ON on the committed eye path, and gates on the
OBSERVABLE MANIFOLD instead of raw byte-identity.

## §1 The diagnosis (reproduced before this prereg, on the committed engine)

The per-tick `run_rules()` of the 2-D retina is ~O(cells²), and it is ONE rule. The match
enumerates O(tasks) `(area, task)` candidates (`cand_enum` LINEAR), but the where-guard
recomputes `MaxOver(Neighbours(area, has_task), salience)` for EVERY candidate → O(tasks·T)
`Attr` evals = O(cells²). `cand_enum` is an INCOMPLETE work count; `term_evals_total` is the
complete one. Measured (moving-bar retina, committed engine, scales 180→1280 cells):

| flag | `cand_enum` exp | `term_eval:Attr` exp | `term_evals_total` exp | wall exp |
|---|---|---|---|---|
| binding_projection OFF | 0.999 | **1.878** | 1.793 | 1.628 |
| binding_projection ON  | 0.999 | **1.000** | 0.999 | 1.033 |

Onsets IDENTICAL OFF≡ON at every scale (863 / 1593 / 3716 / 6706). The flag collapses the
per-candidate guard re-evaluation to once per AREA (the projection) — the observable output
is unchanged.

## §2 THE FIX (mechanical adapter config — NO agent logic, NO Rust change)

`GraphEye` gains one context option, mirroring how it opts into `retina_accel` / `nav_repr`:

* `context["binding_projection"]` — **DEFAULT TRUE for the eye**. When true the adapter
  calls `inner.set_binding_projection(True)` in BOTH build paths (`build`, `_build_2d`),
  after the substrate/inner is created and before any tick. When false, the adapter leaves
  the flag at the engine default (OFF) — the **gate ORACLE**.
* `context["binding_projection_wrong"]` — the FALSIFIER. When true the adapter ALSO calls
  `inner.set_projection_overaggressive(True)` (188000's unsound-projection knob: it projects
  on the EMPTY variable set — one fire per visit regardless of how many areas match).

**`term.rs` diff MUST be EMPTY** vs base `c27209943b`, and in fact the ENTIRE `runners/dsl`
Rust diff is empty: `set_binding_projection` and `set_projection_overaggressive` already
exist in the c272 engine (188000). This rung is the eye adapter opt-in + the manifold gate.
The engine is a `shared` build (Rust source byte-identical to canonical).

## §3 THE GATE — the OBSERVABLE MANIFOLD, explicitly NOT `graph_to_dict` byte-identity

I will **NOT** gate on raw `graph_to_dict` md5. That check fails on non-observable
edge-insertion-order scatter — which is exactly why this fix sat unshipped for two rungs.
Justification: the manifold is what the agent perceives and acts on; the serialization
list-order of edges is not an observable, and gating on it discards a sound, free reduction.
To keep this from being a loophole I also §5-identify what actually scatters and prove it is
NON-observable (order, not value or set).

I gate on **≥4 orthogonal observable projections**, required byte-identical OFF≡ON:

1. **onset signature** — sorted `(column_index, row_index)` of every `RetinalOnsetEvent`;
2. **carve polygon set** — sorted canonical-attr tuples of every `VisionPolygon`
   (row/col min/max, n_events, coherence, speed, direction);
3. **`area.effort`** — the value on every `CognitiveArea`, keyed by `name`;
4. **node-type counts** — the count of every eye node type.

Proven byte-identical OFF≡ON across **≥3 scales** AND on the **landed 160×120 Doom carve
crop** (which produces 3 polygons + 71 onsets — a non-vacuous carve manifold).

## §4 WORK-COUNT REDUCTION (headline, count-based)

**Claim:** `term_eval:Attr` exponent (measured across **≥4 scales**, moving-bar retina)
drops from **~1.88 (OFF)** to **~1.00 (ON)**; `term_evals_total` likewise ~1.79 → ~1.00.
Corroborated by wall-clock exponent ~1.63 → ~1.05. Reported as exponents (a log-log slope
fit), not a single ratio. Counter: `term_eval:Attr` (complete work) and `term_evals_total`;
`cand_enum` stays ~1.0 in BOTH arms (it is the incomplete count and does not move — that is
the point).

## §5 UNSOUND-PROJECTION FALSIFIER (non-vacuity)

**Claim:** projecting away a variable that IS used breaks an observable. Concretely,
`set_projection_overaggressive(True)` (empty-var projection — it projects away `area`, which
IS used in the guard and effect) MUST DIVERGE the observable manifold on a workload with more
than one matching hub. Predicted break: `area.effort` values and/or the onset/carve signature
differ from the sound (`binding_projection` ON) arm. If overaggressive did NOT diverge, the
manifold gate would be vacuous.

## §6 NON-OBSERVABLE-SCATTER IDENTIFICATION (the evidence the gate is sound, not a loophole)

**Claim:** the ONLY difference between the OFF and ON `graph_to_dict` is **edge-insertion
order** — a serialization artifact. I will demonstrate:
* the raw `graph_to_dict` md5 DIFFERS OFF vs ON (the 188000 caveat, reproduced);
* the NODE set is identical (as a sorted multiset of `(type, sorted-attrs)`) — no node
  added, removed, or changed in any attribute VALUE;
* the EDGE set is identical (as a sorted multiset of `(src_type, edge_type, tgt_type)` /
  endpoint-identified tuples) — no edge added or removed;
* the difference localizes to the ORDER of the edge list (and/or node list), not any
  member — i.e. sorting both lists makes the dumps byte-identical.

## §7 C1 — the default path is the oracle

With `context["binding_projection"] = False`, the eye is byte-identical (raw `graph_to_dict`)
to the current committed main eye. The pre-fix path is retained and is the oracle.

## §8 Discipline

* SEPARATE prereg commit (this file), before any number.
* `term.rs` diff EMPTY vs `c27209943b` (verified); whole `runners/dsl` Rust diff empty.
* Engine-semantics gate set green in ONE synchronous session: `test_incremental_match_migrated`,
  `test_empty_match_proof_migrated`, `test_dirty_precision_migrated`,
  `test_per_sensor_epoch_migrated` (incl. its projection gates — a mechanism this rung turns
  ON, not changes), `test_per_area_settlement_migrated`, `test_predicate_retraction_migrated`,
  plus the eye suite.
* Measure module IMPORT-INERT: the flag is toggled ONLY inside scoped calls, never at module
  top level.
* Oracle `bash scripts/rung7_vision_bench.sh` BEFORE==AFTER (identical pass/fail counts).
* Canonical `.so` (`793ce09e…`) md5 UNTOUCHED before/after (engine is a `shared` symlink).
* `source_match` own/shared, never a pinned hash. Commit before report.

## §9 seed_claim (verbatim)

```
SEED CLAIM 195000-195999: CLEAN -- no collision DETECTED.
  Scope: 895 files with seed sinks; 609 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

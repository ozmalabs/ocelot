# SHIP THE LINEAR EYE — RESULTS (block 195000)

**Prereg:** `EYE_BINDING_PROJECTION_PREREG.md`, committed ALONE at `54ddf46a18` before any
number. Base `main` @ `c27209943b`. Engine: **`shared`** build (Rust source byte-identical to
canonical `793ce09e…`; NO Rust change this rung — `term.rs` and the whole `runners/dsl` Rust
diff are EMPTY vs base). Raw numbers: `results/eye_binding_projection.json`.

## Headline

The committed eye shipped **QUADRATIC**. Its per-tick `run_rules()` was dominated by one
scheduler rule, `ct_area_effort_tracks_live_salience`, whose where-guard recomputes a
`MaxOver` over all tasks-on-area for EVERY `(area, task)` candidate — O(cells²)
`term_eval:Attr`, even though `cand_enum` is only O(cells). The rule binds `task` and
references it NOWHERE, so it is projectable to `["area"]`. Turning ON the 188000
`binding_projection` flag on the committed eye path fires that guard once per AREA:
**`term_eval:Attr` exponent 1.878 → 1.000**, wall-clock 1.602 → 1.001, and the OBSERVABLE
MANIFOLD is byte-identical.

## The fix (mechanical adapter config, NO agent logic)

`domains/photon_eye.py`: one context option `binding_projection` (**DEFAULT TRUE**) →
`inner.set_binding_projection(True)` in both build paths, via `_apply_binding_projection`.
`binding_projection=False` retains the committed (quadratic) path as the gate oracle;
`binding_projection_wrong` sets the unsound falsifier (`set_projection_overaggressive`).
No Rust change: the flag and its falsifier already exist in the c272 engine (188000).

## §1 Diagnosis reproduced (moving-bar retina, committed engine)

| flag | `cand_enum` exp | `term_eval:Attr` exp | `term_evals_total` exp | wall exp |
|---|---|---|---|---|
| OFF | 0.999 | **1.878** | 1.793 | 1.602 |
| ON  | 0.999 | **1.000** | 0.999 | 1.001 |

`cand_enum` (the INCOMPLETE work count) is ~linear in BOTH arms — it does not move; the
complete count (`term_eval:Attr` / `term_evals_total`) is what the projection collapses.
Per-scale (cells → `term_eval:Attr`, OFF vs ON):

| cells | OFF Attr | ON Attr | OFF wall ms | ON wall ms | onsets (both) |
|---|---|---|---|---|---|
| 180  | 43 262    | 10 683 | 1.73  | 0.74 | 869  |
| 320  | 121 719   | 19 000 | 3.36  | 1.37 | 1621 |
| 720  | 561 847   | 42 728 | 13.64 | 2.95 | 3650 |
| 1280 | 1 715 673 | 75 994 | 38.33 | 5.39 | 6720 |

Onsets IDENTICAL OFF≡ON at every scale.

## §2 THE GATE — observable manifold, OFF ≡ ON (NOT graph_to_dict byte-identity)

Four orthogonal observable projections, required byte-identical OFF≡ON: onset signature
(sorted `(column_index, row_index)`), carve `VisionPolygon` set, `area.effort` per area, and
every eye node-type count. Digests (blake2b-12 of the combined manifold):

| workload | onsets | polys | OFF digest | ON digest | identical |
|---|---|---|---|---|---|
| moving_bar 8×10   | 426  | 0 | `5d264945…` | `5d264945…` | ✅ |
| moving_bar 12×15  | 1019 | 0 | `3470221…`  | `3470221…`  | ✅ |
| moving_bar 16×20  | 1865 | 0 | `305662c…`  | `305662c…`  | ✅ |
| **doom_carve 160×120** | 71 | **3** | `7bf64059…` | `7bf64059…` | ✅ |

≥3 scales + the landed 160×120 Doom carve crop (3 polygons — non-vacuous). All identical.

## §3 WHAT SCATTERS in graph_to_dict — MEASURED, proven non-observable

The prereg (§6) predicted, following the supervisor's framing, an **edge-insertion-order**
scatter. **Measurement REFUTED that mechanism and found a cleaner one** (honest correction,
conclusion unchanged and strengthened):

* The raw `graph_to_dict` md5 DIFFERS OFF vs ON — **and also differs between two identical
  OFF runs** (`raw_md5_differs_off_vs_off = True`). So the raw difference is run-to-run
  nondeterminism, NOT caused by the projection flag.
* The node list, edge list, and their ORDER are all byte-identical OFF vs ON. The ONLY
  differing attributes are **exactly two wall-clock timing measurements**:
  `AreaLoad.service_wall_micros` and `TaskResult.wall_micros` — the same pair 188000 already
  declared nondeterministic. They differ OFF-vs-OFF too (they are literal elapsed-µs).
* **Stripping those two attributes makes the FULL graph byte-identical** OFF ≡ ON ≡
  run-to-run (`295ec645…`). No node, edge, edge order, or any other attribute VALUE differs.

This is the evidence the manifold-gate is sound, not a loophole: nothing the agent perceives
or acts on differs; the raw md5 difference is a timing measurement that is nondeterministic
regardless of the flag. (188000's raw byte-gate failed on exactly this and left the flag
default-OFF — shipping the eye quadratic.)

## §4 Work-count reduction (headline)

`term_eval:Attr` exponent **1.878 (OFF) → 1.000 (ON)** across 4 scales; `term_evals_total`
1.793 → 0.999; wall-clock 1.602 → 1.001 (109 ms → 13 ms extrapolated, gap growing without
bound). Reported as log-log exponents (§1), not a single ratio.

## §5 Unsound-projection falsifier (non-vacuity)

Projecting away `area` — the var that IS used in the guard AND the effect
(`set_projection_overaggressive`, the empty-var projection) — MUST break an observable when
more than one hub matches. The eye is structurally ONE task-bearing area (`retina`), so sound
and unsound projection observably COINCIDE there (recorded: `eye_single_hub_sound_eq_wrong =
True` — which is also why the fix is trivially safe on the eye). Non-vacuity is witnessed on
the 3-area scheduler running the SAME rule:

| arm | `test0` | `test1` | `test2` |
|---|---|---|---|
| OFF (committed)        | 0.9 | 0.9 | 0.9 |
| SOUND (projection ON)  | 0.9 | 0.9 | 0.9 |
| **WRONG (empty-var)**  | 0.9 | **0.0** | **0.0** |

The empty-var projection fires ONCE and leaves 2 of 3 areas' `effort` STALE — the
`area.effort` observable diverges. SOUND is byte-identical to OFF. The gate is non-vacuous.

## §6 C1 — the OFF path is the committed oracle

With `binding_projection=False` the eye's wall-clock-stripped graph_to_dict is deterministic
and BYTE-IDENTICAL to the ON path (== committed main); the ONLY raw difference OFF-vs-ON is
the wall-clock scatter (which is present OFF-vs-OFF too), and the manifold is identical.

## §7 Gate results

**Engine-semantics gate set + eye gate — ONE synchronous pytest session: 76 passed, 0 failed
(255.6s).** Files (all green): `test_incremental_match_migrated`, `test_empty_match_proof_migrated`,
`test_dirty_precision_migrated`, `test_per_sensor_epoch_migrated` (incl. its 188000 projection
gates — the mechanism this rung turns ON), `test_per_area_settlement_migrated`,
`test_predicate_retraction_migrated`, `test_eye_binding_projection_migrated` (this rung's gate),
`test_vision_graph_eye`.

**Oracle `bash scripts/rung7_vision_bench.sh` — BEFORE == AFTER:**

| | result |
|---|---|
| BEFORE (base eye, `photon_eye.py` @ `c27209943b`) | 214 passed, 10 skipped, 0 failed |
| AFTER  (fix, `binding_projection` default ON)      | 214 passed, 10 skipped, 0 failed |

Identical (214/10/0 — the data-less worktree signature). Enabling the projection changes NO
vision-bench result: the eye's output is unchanged.

## §8 Discipline ledger

* Prereg committed ALONE at `54ddf46a18`; seed_claim 195000-195999 CLEAN (verbatim in prereg §9).
* `term.rs` diff EMPTY vs `c27209943b`; whole `runners/dsl` Rust diff EMPTY. Engine `shared`.
* Canonical `.so` md5 `793ce09ed498a749abb79aeaea44b92e` UNTOUCHED before/after (symlink, read-only).
* Measure module IMPORT-INERT: every flag toggled only inside functions, on a freshly-built eye.
* `source_match`: shared (Rust source identical to canonical — CANONICAL NEEDS NO REBUILD, no Rust change).

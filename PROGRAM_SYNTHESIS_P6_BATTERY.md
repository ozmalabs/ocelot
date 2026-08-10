# PROGRAM SYNTHESIS P6 — track A: the POWERED battery (results)

**Date:** 2026-07-31. Companion to `PROGRAM_SYNTHESIS_PLAN.md` §4-P6 and
`PROGRAM_SYNTHESIS_PREREG.md` §8 (H6) / §9 (the registered null reading),
run under the §0 standing rules: **power the gate before the endgame**
(n ≥ 100/arm, Wilson 95% CIs, deltas within ~3× the per-episode step are
not results); a baseline is a list of identities; eval-subset coverage is
part of every claim. Deliverables:
`tests/fixtures/prog_synthesis_battery/tasks.json` (the frozen 125-task
instrument + its `build_tasks.py` provenance),
`scripts/prog_synthesis_battery.py` (the measurement driver),
`results/prog_synthesis_battery.json` (the artifact — per-task rows are
the baseline; every aggregate derives from them),
`tests/test_prog_synthesis_battery_migrated.py` (11 gates, green, 0.3 s).

## 0. Instrument + protocol (the conditions every number below carries)

- **Task set:** N = 125, six strata — expression 30 / single_statement 25 /
  loop_accumulation 30 / branching 25 / error_handling 5 /
  multi_statement 10. Each task = NL request + 3–5 example rows + 2–3
  held-out rows (never shown to the pipeline). **Scope pin:** integer /
  list-of-integer inputs, SCALAR outputs (ProgEval's value space; the row
  verdict records `got` only for scalars, so list outputs are out of the
  honest current scope). Reference lambdas in `build_tasks.py` guarantee
  example/held-out consistency; DSL Div semantics (true division,
  div-by-zero → 0.0) are mirrored where division is asked for.
- **Contamination guard** (enforced at run time AND by the gate): no
  request text is copied from the P4 gate fixtures
  (`tests/test_program_synthesis_migrated.py` — the mechanism's own dev
  set) or from the frozen 26-item C-BATTERY. Trigger *words* necessarily
  overlap (the codebook's trigger vocabulary IS the capability under
  test); request *strings* do not.
- **Not tuned to pass:** strata deliberately include tasks beyond every
  rung (no `Mod` in the enumerator → parity/remainder; closed forms past
  the size bound; list folds no rung can build), decoy-trigger tasks (a
  trigger word matching a WRONG template → the CEGIS path), and three
  naturally-phrased requests outside the imperative-lead cue vocabulary
  (recognition failure is a real outcome, counted in the denominator).
- **Arms:** MAIN = the boot ladder exactly as `ensure_program_synthesis`
  installs it (8 starter shapes + the seed's spine shape + boarded P3
  bigrams + SynthEnumerate + gap). FROZEN = **C-CODEBOOK-FROZEN**
  (prereg §2): codebook stripped to the 8 held starter shapes (no spine,
  no taught/minted entries), ConstructionBigram rows removed. One fresh
  substrate per task (batch size 1), sorted-id order.
- **Score (primary, binary):** the pipeline accepts a Program AND ProgEval
  of the accepted IR agrees on ALL held-out rows.
- **Determinism:** the MAIN arm ran twice end-to-end — outcome lists
  **byte-identical** (hash `f346204d5d78e220…` recorded for both runs in
  the artifact; the gate re-derives it from the stored rows). Runtime:
  MAIN 2.1 s + 2.1 s, FROZEN
  2.3 s, whole battery incl. toolchains + C-BATTERY **8.2 s** — far
  inside the timebox, so no N cut was needed.

## 1. THE POWERED TABLE (primary score, Wilson 95% CIs)

| stratum | n | MAIN k/n (p, CI) | FROZEN k/n (p, CI) | Δ (Newcombe CI) |
|---|---|---|---|---|
| branching | 25 | 16/25 (.640 [.445, .798]) | 16/25 (.640 [.445, .798]) | 0 [−.251, +.251] |
| error_handling | 5 | 3/5 (.600 [.231, .882]) | 3/5 (.600 [.231, .882]) | 0 [−.465, +.465] |
| expression | 30 | 19/30 (.633 [.455, .781]) | 19/30 (.633 [.455, .781]) | 0 [−.232, +.232] |
| loop_accumulation | 30 | 6/30 (.200 [.095, .373]) | 3/30 (.100 [.035, .256]) | +.100 [−.088, +.285] |
| multi_statement | 10 | 5/10 (.500 [.237, .763]) | 4/10 (.400 [.168, .687]) | +.100 [−.290, +.451] |
| single_statement | 25 | 16/25 (.640 [.445, .798]) | 16/25 (.640 [.445, .798]) | 0 [−.251, +.251] |
| **overall** | **125** | **65/125 (.520 [.433, .606])** | **61/125 (.488 [.402, .575])** | **+.032 [−.091, +.153]** |

**Delta verdict (the prereg §8 decision rule, applied):** MAIN − FROZEN =
+3.2 pp. That exceeds 3× the per-episode step (2.4 pp) but the arms are
**inside each other's CIs** (delta CI spans zero) — so the honest headline
is **NO CI-SEPARATED CAPABILITY GAIN from the learned layer** at this
grain. H6 is NOT confirmed. The entire measured delta is exactly the four
spine-trigger (tally) tasks the FROZEN arm loses
(`la_03_running_sum`, `la_04_accumulate_all`, `la_05_tally_up`,
`ms_01_fold_sum`) — an identity list, not a count.

**Where capability actually sits (rung provenance of the 77 MAIN accepts,
incl. 12 held-out-failed):** rung-1 codebook templates **10**, rung-1.5
spine+lattice **4**, rung-3 **SynthEnumerate 63**. The proposal mass is
the ENGINE's enumerator, not the learned codebook — precisely the §9
registered null shape: *corpus statistics did not convert to generation
capability at this grain*; the verdict layer (ProgEval + held-out rows)
is doing the deciding. Recognition failures: **3/125** in both arms
(`ex_29_helpful_hint` declarative, `ex_30_polite_ask` "please"-headed,
`br_25_make_choice` "make" is seeded non-imperative) — counted in the
denominator, reported separately.

## 2. Failure taxonomy (MAIN; identities in the artifact)

| class | n | what it is |
|---|---|---|
| accepted_holdout_ok | 65 | the primary successes |
| gapped:enumerate_failed | 29 | honest gaps: list folds / parity / large closed forms beyond every rung; ALL 29 filed a `SelfConcern{kind:code_write}` (30 gapped total incl. no_shape — 30/30 filed, deduped) |
| **stalled:evaluated** | **15** | **a REAL P4 mechanism defect the powered battery surfaced** (below) |
| accepted_holdout_fail | 12 | accepted on examples, caught by held-out rows (overfit enumerations — below) |
| not_recognized | 3 | failed-at-goal (cue machinery; counted, listed above) |
| gapped:no_shape | 1 | `br_13_is_even_num` (no trigger, and its bool rows give the enumerator no purchase) |

### 2.1 The stall (named defect, 15/125 = 12% of the battery)

`br_14_max_or_zero, br_22_abs_min, ex_17_gap_size, ex_18_add_three,
ex_21_sum_sq_pair, ex_24_span_pair, la_15_sum_to_n, la_19_sum_evens_to_n,
ms_05_span_plus_one, ss_06_double_sum, ss_10_negate_sum, ss_11_abs_sum,
ss_12_mean_shift, ss_15_double_abs, ss_25_norm1` — identical set in both
arms.

Mechanism, diagnosed: when a **codebook decoy consumes attempt 1** (e.g.
"sum of the whole numbers…" triggers `sum_of_two`, rows fail, CEGIS
excludes it) **and the enumerate rung then runs**, `run_enumerate` builds
the IR at the SAME attempt number the decoy consumed; the example rows'
`verdict_attempt` already equals `ps_attempts`, so
`ps_row_pass`/`ps_row_fail`'s `verdict_attempt < eval_attempt` guard never
re-arms, and the goal parks on the non-terminal `evaluated` status — no
accept, no gap, **no SelfConcern filed**. The P4 gates never saw it
because their enumerate case had no prior codebook attempt. Most of these
15 carried enumerable solutions (`Max(a,0)`, `Abs(Minus(a,b))`,
`n(n+1)/2`, …), so this is the single largest recoverable blocker mass in
the battery (up to ~12 pp if all would verify — a hypothesis for the next
prereg, not a claim). Per prereg §6's own null language this is a
fixpoint-convergence defect to be fixed IN THE RULES (seed owned by the
P4 track) — the battery records it and does NOT ship a crutch.

### 2.2 Held-out catches (12) — the verdict layer working

Three-example specs underdetermine: `br_10_top_of_three` accepted
`Max(a,b)` (fits all examples, "of three" is invisible to the spec),
`br_16/17/23/21` found degenerate comparison forms, `ex_25/26/27/28`,
`ss_21`, `eh_04`, `ex_22` overfit small terms — every one caught by the
held-out rows. Notable: the enumerator actively exploits the DSL's
div-by-zero → 0.0 (e.g. `br_21` returned `Eq(a, 1/(1/a))` — a
"defined-at-zero" reciprocal trick). Strictness is the signal, again.

### 2.3 Semantics coincidences (error_handling, declared in advance)

`eh_01_safe_div` and `eh_02_safe_recip` are accepted_holdout_ok **because
DSL Div-by-zero → 0.0 coincides with the requested fallback** — a
documented coincidence, NOT a try/except capability; no rung can
synthesize `ProgTryOr` (`eh_04`/`eh_05` gap honestly;
`eh_03_checked_sub` is a genuine `Max(Minus,0)` find). The stratum
measures spec-level fallback behaviour only.

## 3. Render / toolchain validity (secondary; accepted MAIN tasks)

**Python (all 77 accepted):** render_ok **56/77 = .727 [.619, .814]**;
of the rendered, exec ≡ ProgEval on held-out inputs **53/56 = .946
[.854, .982]**.

- The 21 render gaps are ALL one finding: **the enumerator/codebook emit
  expression heads outside the P5 render closure** — `Abs` ×11, `Max` ×5,
  `Min` ×4, `Fold` ×2 (the P5 rule set covers the 23 `Prog*` variants +
  the P2 expression closure, which never contained Abs/Min/Max/Fold).
  A render-gap files through the established convention; nothing renders
  wrongly.
- The 3 exec disagreements are ALL the **Div-by-zero cross-frame
  divergence**: rendered Python raises `ZeroDivisionError` where ProgEval
  yields 0.0 (`eh_01`, `eh_02`, `br_21`). The frame doctrine's point,
  measured: the IR's execution semantics and the python frame's disagree
  exactly at the partiality boundary.

**Toolchain subsample (deterministic rule: sorted accepted ids, stride
len//15, first 15 — ids in the artifact; rustc 1.95.0 / lua5.4 / luajit /
gcc all present):**

| frame | agree | disagree | render_gap | other |
|---|---|---|---|---|
| rust | 11 | **0** | 4 (`Max`/`Min` ×2 tasks, `Div`, `Fold`) | — |
| lua | 12 | **0** | 3 (`Max`/`Min`, `Min`, `Fold`) | — |
| llvm→x86-64 (chain) | 10 | **0** | 0 | 2 emit_refusal (`unsupported_expr:Min`), 3 scope_out_non_int (float mean; list params — i32 ABI) |

**Zero disagreements anywhere a surface actually built and ran** — where
the renderers and the LLVM chain have coverage, toolchain truth agrees
with ProgEval on every held-out call. The validity story is a *coverage*
story (the same Abs/Min/Max/Fold closure gap, per frame), not a
correctness one.

## 4. C-BATTERY — the continuity control (prereg §2, byte-identical)

- Frozen baseline: **7/26** (`results/code_synthesis_baseline.json`).
- Live re-run at this commit through the PINNED path
  (`run_write_battery → write_function_from_request`, fully-booted
  `WorldAdapter` + `load_all_seeds`): **7/26, zero ok→fail regressions,
  zero flips either way** — per-item rows in the artifact. The control
  holds; the phase is not blocked.
- The same 26 requests VERBATIM through the NEW pipeline (no example rows
  — the battery text is never extended): all 26 land gapped
  (`no_shape` ×18, `no_examples` ×8) **by design** — the P4 verdict layer
  is execution agreement
  with example rows, and the P0 battery carries none. This is the
  structural difference between the two instruments, reported as such;
  the 26-item arm remains the continuity instrument, the 125-task battery
  the capability instrument. The two are never conflated.

## 5. Honest scope statement (what these numbers are OF)

1. **Languages:** the primary score is verdict-layer pass on the hub IR
   under **ProgEval** (python-frame execution semantics). rust / lua /
   llvm-x86 enter as render+toolchain validity on the accepted subsample
   — NOT as independent synthesis arms (one IR, cross-frame surfaces; the
   prereg's ×{languages} reading is realised as the frame table in §3).
2. **Domain:** integer / list-of-integer inputs, scalar outputs. String /
   float-input / list-output programs are outside this battery.
3. **Recognition** failures count in the denominator (3/125).
4. **error_handling** measures fallback specs, not try/except mechanism
   (§2.3).
5. The learned-layer delta is measured against THIS boot's learned layer
   (spine + boarded bigrams — what `ensure_program_synthesis` actually
   installs); a battery against a post-scan taught codebook would be a
   different (larger) learned layer and must re-run both arms.
6. Per the standing rule: mechanism results (determinism, zero toolchain
   disagreement, stall diagnosis) and the benchmark value (52.0%) are
   both reported; neither substitutes for the other.

## 6. Verdict against the prereg

- **H6 (CI-separated above both controls): NOT confirmed.** MAIN 65/125
  [.433, .606] vs C-CODEBOOK-FROZEN 61/125 [.402, .575]; Δ +3.2 pp CI
  [−9.1, +15.3]. Headline: **no measured capability gain from the
  learned layer**; the §9 null reading applies — proposal capability
  currently lives in the enumerator + the execution verdict, and the next
  prereg starts from the per-stratum failure lists (the stall fix, the
  render-closure gap, list-fold proposal coverage), not a parameter
  search.
- **C-BATTERY holds** (7/26, no flips). **C-BENCH:** neighbor suites
  green at this commit (`test_program_synthesis` 14,
  `test_code_synthesis_baseline` 11, `test_render_python` 52,
  `test_render_rust_lua` 47 — 124 passed).
- Gates shipped: `tests/test_prog_synthesis_battery_migrated.py` — 11
  passed, 0.29 s (schema/derivation honesty, contamination, determinism,
  C-BATTERY regression block, 3-task live re-verification + the
  frozen-arm strip mechanism re-verified live).
- Gap-pipeline seam: all 30 gapped MAIN tasks filed
  `SelfConcern{kind:'code_write'}` (per-row `gap_filed` in the artifact);
  the stall class files nothing — part of the named defect. The
  end-to-end promote/experiment leg is the concurrent P6-B track's
  deliverable.

## 7. P6.5 — the stall FIXED in the rules, re-measured (arm MAIN-POSTFIX)

**Date:** 2026-07-31 (same day, after the P6 run above). The §2.1 defect was
fixed where §2.1 said it must be — IN THE SEED RULES (the P4 track's file),
not in the battery — and the battery re-measured. **The frozen MAIN/FROZEN
rows above are UNTOUCHED**; the artifact gained an appended arm
`arms.main_postfix` (+ `determinism_postfix`, `delta_postfix`,
`postfix_recovery`, `failure_taxonomy.main_postfix`) with full provenance.

### 7.1 The fix (seed v1.1.0 — ONE new rule, `ps_enumerate_fresh_attempt`)

Design chosen: **the enumerate rung's evaluation gets a FRESH attempt
number**, keyed on the exact collision that defines the defect. On
`status == enumerate_pending`, iff some example row's `eval_attempt` equals
the goal's CURRENT `ps_attempts` (i.e. a codebook attempt already consumed
this attempt number), the rule bumps `ps_attempts += 1` (in-frame integer
step). Consequences, all verified:

- the `verdict_attempt < eval_attempt` guard re-arms, the per-row verdicts
  re-issue at the fresh number, and the goal reaches a TERMINAL status
  (accepted, or gapped via the standing `ps_no_shape` Or-arm /
  `ps_ce_exhausted`) — never the non-terminal `evaluated` park;
- budget honesty intact: `ps_enumerate_mark` still requires
  `attempts < budget`, so `attempts <= budget` after the bump; exhaustion
  rules unchanged; integers throughout;
- self-extinguishing: the bump falsifies its own Exists guard, and the mark
  is once-guarded (`ps_rung_enumerate`) — at most one bump per goal;
- **non-colliding paths byte-unchanged**: a fresh enumerate at attempts 0
  (rows still at the −1 sentinels) does not fire the rule — the pinned
  live-reverify tasks (`ex_01_pick_larger`, `la_03_running_sum`,
  `ms_10_collatz_next`) reproduce their frozen rows exactly, and gate 5 of
  `tests/test_prog_synthesis_battery_migrated.py` stayed green with ZERO
  edits (no gate adjustment was needed);
- every status transition is still a rule; the adapter is unchanged except
  the seed-version marker; the no-Python-decision audit still passes.

Regression gate:
`tests/test_program_synthesis_migrated.py::test_stall_regression_decoy_then_enumerate_reaches_terminal`
reproduces the exact stall shape (decoy consumes attempt 1 → CEGIS
CounterExample + Excluded → enumerate rung finds a term → verdict re-arms →
accepted on attempt 2, non-colliding control at attempts 0). Counterfactual
verified by a stash-free seed-body flip: on the v1.0.0 body the test FAILS
with `status == 'evaluated'` (the park); on v1.1.0 it passes. Suite: 15
passed (14 prior + this gate).

### 7.2 THE RE-MEASURED TABLE (MAIN-POSTFIX vs the frozen MAIN)

Same 125 tasks, same scoring, same protocol (one fresh substrate per task,
sorted-id order); twin-run determinism **byte-identical** (hash
`ccce37913b76a30e…` both runs; 2.1 s + 2.0 s).

| stratum | n | MAIN-POSTFIX k/n (p, CI) | MAIN k/n (p, CI) | Δ (Newcombe CI) |
|---|---|---|---|---|
| branching | 25 | 17/25 (.680 [.484, .828]) | 16/25 (.640 [.445, .798]) | +.040 [−.211, +.285] |
| error_handling | 5 | 3/5 (.600 [.231, .882]) | 3/5 (.600 [.231, .882]) | 0 [−.465, +.465] |
| expression | 30 | 23/30 (.767 [.591, .882]) | 19/30 (.633 [.455, .781]) | +.133 [−.097, +.346] |
| loop_accumulation | 30 | 7/30 (.233 [.118, .409]) | 6/30 (.200 [.095, .373]) | +.033 [−.175, +.238] |
| multi_statement | 10 | 6/10 (.600 [.313, .832]) | 5/10 (.500 [.237, .763]) | +.100 [−.290, +.451] |
| single_statement | 25 | 21/25 (.840 [.653, .936]) | 16/25 (.640 [.445, .798]) | +.200 [−.044, +.417] |
| **overall** | **125** | **77/125 (.616 [.528, .697])** | **65/125 (.520 [.433, .606])** | **+.096 [−.026, +.214]** |

**Standing delta rule applied:** +9.6 pp exceeds 3× the per-episode step
(2.4 pp) but the delta CI spans zero — as an UNPAIRED aggregate this is
`inside_ci_above_3x_step`, NOT a CI-separated result. The claim that IS
CI-free and exact is the PAIRED identity list: the machinery is
deterministic, and **the changed-row set equals the stalled set exactly —
all 15, nothing else** (`postfix_recovery.changed_task_ids_vs_main`). The
fix moved precisely the diagnosed class; no other row flipped in either
direction.

### 7.3 Stalled count and where the 15 landed

**Stalled: 15 → 0** (`n_stalled_postfix = 0`; the taxonomy row
`stalled:evaluated` is GONE). Post-fix taxonomy (MAIN-POSTFIX):
accepted_holdout_ok 77, gapped:enumerate_failed 29, accepted_holdout_fail
15, not_recognized 3, gapped:no_shape 1 — every row terminal.

The 15, individually (all rung-3 accepts after the CEGIS-excluded decoys;
attempts now 2 or 3 — decoy attempt(s) + the fresh enumerate attempt):

- **12 → accepted_holdout_ok** (the recoverable mass §2.1 hypothesised —
  measured at 12/15, i.e. +9.6 pp of the up-to-12 pp bound):
  `br_14_max_or_zero, ex_17_gap_size, ex_18_add_three, ex_21_sum_sq_pair,
  ex_24_span_pair, la_15_sum_to_n, ms_05_span_plus_one, ss_06_double_sum,
  ss_10_negate_sum, ss_11_abs_sum, ss_12_mean_shift, ss_15_double_abs`.
- **3 → accepted_holdout_fail** — the verdict layer catching overfit
  enumerations, exactly the §2.2 class (a success of the fix too: an
  honest terminal verdict instead of a park): `br_22_abs_min` accepted
  `Min(3, Abs(a))` (fits the examples, misses held-out),
  `la_19_sum_evens_to_n` accepted `IfThenElse(n, 6, n)` (a
  truthiness-coincidence on the examples), `ss_25_norm1` accepted
  `Abs(a − b)` (|a|+|b| ≠ |a−b| off the example diagonal).
- **0 → gapped** on this battery (recovery-to-honest-gap was an accepted
  outcome of the fix; it did not occur — every stalled task's enumerate
  candidate reached a verdict).

### 7.4 Conditions this section carries

1. MAIN-POSTFIX vs **FROZEN** is +12.8 pp `[+0.5, +24.6]` — numerically
   CI-separated, but it CONFLATES the stall repair with the learned layer
   (the frozen FROZEN arm still contains its own 15 pre-fix stalls). It is
   NOT an H6 verdict. A fair learned-layer re-test needs a FROZEN-POSTFIX
   arm under the fixed seed — next prereg if the H6 question is reopened;
   the §6 H6 reading above stands as measured on its own conditions.
2. The recovered accepts' row `construction` field carries the LAST
   codebook (excluded decoy) name with `rungs.enumerate = 1` — read the
   rung markers, not the construction name, for provenance of these rows.
3. Battery gate: `tests/test_prog_synthesis_battery_migrated.py` — **11
   passed, unmodified** over the appended artifact (the frozen-row pins and
   the live re-verification both hold; no schema assertion needed
   adjustment).

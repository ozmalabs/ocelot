# PROGRAM SYNTHESIS ARC 2 — Q0 track A: the FROZEN ZERO-SHOT external baseline

**Date:** 2026-07-31. Companion to `PROGRAM_SYNTHESIS_ARC2_PLAN.md` §2 (Q0).
Deliverables: `scripts/mbpp_zero_shot_baseline.py` (the measurement driver),
`results/mbpp_zero_shot_baseline.json` (the artifact — per-task rows are the
baseline, every aggregate derives from them), `tests/test_mbpp_baseline_
migrated.py` (schema + 3-task live re-verification + assert-parser unit
gates, 40 passed), `tests/test_mbpp_contamination_migrated.py` (the
list-gate, 7 passed) — both suites 0.47 s combined.

## 0. What ran, unmodified

The arc-1 synthesis stack **AS-IS**, byte-identical to the P7-D `MAIN-P7`
boot (`PROGRAM_SYNTHESIS_P7D.md` §1): `seeds/program_synthesis.json` v1.3.0
(43 rules — codebook → lattice → descend → enumerate → gap, CEGIS + local
repair live) + the starter-8 write codebook + the spine shape + boarded P3
`ConstructionBigram` statistics + the 15 mined P7-C chunks
(`install_mined_chunks`). **Zero code changes for MBPP** — no new Term, no
new rule, no new codebook entry, nothing MBPP-specific in the engine or
seeds. The only new artifact is the measurement driver + its output.

Every task ran through `domains.prog_synthesis.synthesize_from_request`
exactly as the internal battery calls it: one fresh substrate per task
(`ensure_program_synthesis` + `install_mined_chunks`), sorted task_id order,
`request_text` = the MBPP `prompt` field verbatim, example rows built from
parsed asserts (below). Twin full-battery run: **byte-identical**
(hash `d08b13c9b3698f9d…`, 1.14 s + 1.11 s, whole run 2.26 s — far inside
the ~25 min box; no time-box prefix cut was needed, the measured elapsed
time made that branch of the driver dead code this run).

## 1. Split (provenance.json's rule, on the 427-task VENDORED subset)

| split | task_id band | n |
|---|---|---|
| few_shot | [1,10] | 7 |
| **test** | **[11,510]** | **257** |
| validation | [511,600] | 43 |
| train | [601,∞) | 120 |
| **total** | | **427** |

(The vendored `sanitized-mbpp.json` subset is sparse over the canonical
1–974 id range — 427 of the ~974 canonical ids are present at all; the
counts above are exact over what was actually vendored, not the full
canonical MBPP.)

## 2. Assert parseability (the example-row extraction floor)

Every `test_list` entry was classified by `classify_assert` (ast-based:
`ast.parse` + `ast.literal_eval` on constant sub-nodes ONLY — no
`eval`/`exec` of any test-split text, ever). Per-**assert** taxonomy across
the 257 test tasks (771 individual assert statements):

| unsupported form | n asserts | n tasks |
|---|---|---|
| `math_isclose` | 39 | 13 |
| `set_wrapper` (`set(f(...)) == set(...)`) | 9 | 3 |
| `set_literal_value` (a raw `{...}` set literal in an arg or the expected value — distinct from the wrapper form above; downgrading a set to a list would silently misrepresent set-equality as list-equality, so this is named and excluded rather than coerced) | 4 | 2 |

No other unsupported forms occurred in this subset (no `sorted`/`list`/
`tuple` wrappers, no boolean-expression asserts, no chained compares, no
kwargs, no starred args, no non-literal args/expected, no attribute calls —
all covered classes in `classify_assert` with zero hits here; the parser
unit-tests each of them synthetically since the corpus itself didn't
exercise every branch).

**Per-task split rule (this runner's own registered convention — see the
honest caveat below):** among a task's PARSEABLE asserts, in their original
`test_list` order, the FIRST is the **revealed** example row; every
remaining parseable assert is a **held-out** row, never shown to the loop.
A task needs ≥1 revealed AND ≥1 held-out parseable assert to be RUNNABLE:

| category | n tasks |
|---|---|
| **runnable** (≥2 parseable asserts) | **240** |
| `assert_unparseable` (0 parseable asserts) | 17 |
| `protocol_excluded:insufficient_holdout` (exactly 1 parseable assert) | 0 |
| **total test tasks** | **257** |

**Honest caveat on the split rule:** the task card names this "Q0-B's
prereg pins it arc-wide" — Q0-B's `PROGRAM_SYNTHESIS_ARC2_PREREG.md` is a
sibling track's file this agent did not touch (concurrent, file-ownership
separated). If Q0-B's pinned rule differs from "1 revealed, N-1 held-out"
above, the two must be reconciled explicitly at Q5; this document states
its own rule plainly so that reconciliation is checkable.

## 3. THE ZERO-SHOT NUMBER

| denominator | k | n | p | Wilson 95% CI |
|---|---|---|---|---|
| **pass / runnable** | 1 | 240 | **0.42%** | [0.07%, 2.32%] |
| **pass / all test tasks** | 1 | 257 | **0.39%** | [0.07%, 2.17%] |

**Comparison to the internal battery:** MAIN-P7 scored **80/125 = 64.0%
[55.3%, 71.9%]** on the arc-1 self-authored battery (`PROGRAM_SYNTHESIS_
P7D.md`). On MBPP zero-shot the SAME stack scores **≈0.4%** — a collapse of
essentially the entire measured capability. This is the arc's own
predicted result (§0 of the plan: *"expect: most tasks refused at the
value-domain wall or the request-recognition step"*) landing almost
exactly as severely as a self-authored-battery-vs-external-benchmark
delta of this shape would predict — the internal battery's 125 tasks were
themselves hand-written in the codebook's own vocabulary (two-arg
integer arithmetic, `Write a function <name> that <predicate>`); MBPP was
not.

**The one pass, and why it does not mean what it looks like:** task 404,
*"Write a python function to find the minimum of two numbers"*. The
enumerate rung found `Var(a)` — literally "return the first argument" —
which happens to satisfy both held-out rows only because neither one had
`a > b` (`(-5,-4)→-5`, `(0,0)→0`, and the one revealed row was also an
`a ≤ b` case). This is the SAME phenomenon the internal battery already
documented (`PROGRAM_SYNTHESIS_P6_BATTERY.md` §2.2: *"the enumerator
actively exploits..."*) — with only one revealed row the verdict layer's
strictness has almost no examples to be strict ABOUT. The honest reading:
**this baseline's true zero-shot capability count is arguably 0/257, not
1/257** — the "1" is a coincidental pass, not a genuine `min` synthesis;
it is reported literally per protocol (the verdict layer is execution
agreement, not intent-matching) rather than hand-adjusted.

## 4. THE FULL TAXONOMY, ranked by mass (240 runnable + 17 excluded = 257)

| rank | class | n | share of 257 | what it is |
|---|---|---|---|---|
| 1 | `accepted_holdout_fail` | 146 | 56.8% | accepted on the ONE revealed row, caught by held-out rows |
| 2 | `gapped:enumerate_failed` | 90 | 35.0% | honest gap: no codebook/lattice/descend/enumerate rung found anything (the value-domain wall + the enumerator's int/list-of-int reach) |
| 3 | `assert_unparseable` | 17 | 6.6% | every assert used an unsupported form (§2) |
| 4 | `gapped:exhausted` | 2 | 0.8% | CEGIS/attempt budget exhausted before any rung verified |
| 5 | `not_recognized` | 1 | 0.4% | the cue machinery never minted a Goal (declarative/non-imperative phrasing) |
| 6 | `pass` | 1 | 0.4% | see §3 — a coincidental pass, not genuine synthesis |

**Top 8 refusal/blocker classes, by mass (merging the taxonomy above with
the rung-provenance breakdown of the two largest classes):**

1. **`accepted_holdout_fail` overall — 146 (56.8%)**
2. **`gapped:enumerate_failed` — 90 (35.0%)**
3. `accepted_holdout_fail` via bare `SynthEnumerate` (no codebook/lattice/
   descend involved) — **91** of the 146 (the single largest sub-mass in
   the whole run: the enumerator alone, overfitting one example)
4. `accepted_holdout_fail` via a codebook DECOY + enumerate (`sum_of_two`
   ×22, `count_of_list` ×15, others) — **22**
5. `accepted_holdout_fail` via a codebook decoy caught by DESCENT
   (`codebook`+`descend` rungs) — **22** — P7-A's descent rung inherits the
   same one-example overfitting weakness, at the sub-goal grain
6. `assert_unparseable` — **17** (13 tasks `math_isclose`, 3 tasks
   `set_wrapper`, 2 tasks `set_literal_value`)
7. `accepted_holdout_fail` via a mined P7-C chunk decoy
   (`ck_prog_if_stmt_n1_q1` ×11 within the lattice/enumerate combos) — a
   measurable footprint of the chunk layer, entirely on the WRONG side of
   the ledger here (chunk-cued accepts that then fail held-out)
8. `gapped:exhausted` + `not_recognized` — **3** combined (the smallest,
   genuinely rare classes)

**The dominant finding this baseline adds beyond the plan's own
prediction:** the plan expected the value-domain wall and `not_recognized`
to dominate. Measured, `gapped:enumerate_failed` (the value-domain wall, as
predicted, 35.0%) is real but is NOT the largest class — **`accepted_
holdout_fail` (56.8%) is**, and it is not a value-domain phenomenon at all:
it is **single-example overfitting**, a direct consequence of MBPP
offering only 3 asserts per task where this runner's split rule reveals
just 1. Every rung that can accept (codebook, lattice, descend, enumerate)
overfits a 1-example spec at roughly its own base rate — this is a NEW,
Q0-measured blocker class the arc-1 internal battery (3–5 revealed rows
per task) never surfaced at this mass, because it was never starved this
hard. `not_recognized` is essentially absent (1/257) — MBPP's `"Write a
[python] function to..."` phrasing lands squarely in the imperative-lead
cue vocabulary the stack already holds; recognition was never the
bottleneck this measurement predicted it would be.

## 5. Contamination

Enforced mechanically, not by promise: `task["code"]` is deleted for every
test-split task the instant it is read off disk (`_strip_code`), before
any further processing — `assert "code" not in t` is asserted on the whole
test-split list in `main()`. Assert parsing uses `ast.parse` +
`ast.literal_eval` on constant sub-nodes only (no `eval`/`exec` of any
test-split text). Every substrate is a fresh, `OZMA_SEED_PERSIST_DISABLED`
boot with no `domains.teach.teach` call anywhere in the runner — nothing
this run does can reach a seed file or codebook artifact on disk. A seed
rule MAY mint an in-memory self-teach chunk on an accepted Program (P7-C's
normal, unmodified behaviour) but it dies with that task's throwaway
substrate.

`tests/test_mbpp_contamination_migrated.py` is the independent list-gate:
it scans every codebook-bearing seed/results artifact currently on disk
(`seeds/code_write_constructions.json`, `seeds/code_write_gap.json`,
`seeds/code_write_request_cues.json`, `seeds/prog_chunk_growth.json`,
`seeds/program_synthesis.json`, `seeds/compositional_chunking.json`,
`results/prog_chunk_mine.json`, `results/prog_construction_scan.json`,
`results/code_synthesis_baseline.json`) for any normalized test-split
prompt substring or code-field line — **zero hits** on the current tree —
and proves the scan actually bites via two self-tests that inject a real
test-split prompt substring / code line into a tmp file and confirm the
gate flags it. This track's own eval log
(`results/mbpp_zero_shot_baseline.json`) is deliberately excluded from the
scan targets and the exclusion is itself gated: an eval log legitimately
records which prompt was tested (that is the artifact's job), and is not a
codebook, cue vocabulary, bigram table, or taught shape.

## 6. What this baseline sets up for Q1–Q5

- **Q1 (value-domain floor)** should expect its biggest single lever to be
  the `gapped:enumerate_failed` 90-task mass — string/list/dict/float
  operations the current `ProgEval`/`SynthEnumerate` simply cannot express
  — but per this measurement, closing that gap ALONE will not move the
  headline number much unless the single-example overfitting problem (the
  actual largest class) is also addressed; a task that gains reach in Q1
  but is still shown only 1 revealed row will very plausibly move from
  `gapped:enumerate_failed` into `accepted_holdout_fail`, not `pass`.
- **Q2 (spec comprehension)** has almost nothing to fix at the recognition
  step — 256/257 tasks were recognized as write requests zero-shot; MBPP's
  own imperative phrasing already matches the held cue vocabulary. Q2's
  real work is signature/example extraction quality (this baseline's own
  `classify_assert`), not request recognition.
- **Q3 (the paired diet)** — the `math_isclose`/`set_wrapper`/
  `set_literal_value` unparseable mass (17 tasks) and the value-domain wall
  are exactly the kind of "content in the asked-about domain" the paired
  diet targets; the train split (120 tasks, same corpus) is the natural
  mining source, already split off and untouched by this track.
- **Named lever for whoever owns the split-rule reconciliation:** revealing
  only 1 example per task is very plausibly UNDER the internal battery's
  own operating point (3–5 revealed rows) by design of MBPP's 3-assert
  convention, and §4 shows this alone produces a 56.8% overfit-accept mass.
  If Q1–Q4's gains are to be measured fairly against this Q0 floor, the
  revealed/held-out split rule must stay FIXED across every later phase
  (this document's rule, or Q0-B's, whichever is finally pinned) — a
  phase that also loosens the split (e.g. reveals 2 of 3 asserts) would be
  measuring two changes at once.

## 7. Files

- `scripts/mbpp_zero_shot_baseline.py` — the measurement driver.
- `results/mbpp_zero_shot_baseline.json` — the frozen artifact (per-task
  rows under `runnable_rows` / `excluded_rows`, both denominators'
  aggregates, the taxonomy, determinism hashes, environment, provenance).
- `tests/test_mbpp_baseline_migrated.py` — 40 passed (schema/derivation
  honesty, 3-task live re-verification, assert-parser unit gates).
- `tests/test_mbpp_contamination_migrated.py` — 7 passed (the list-gate +
  its own self-test proving it bites).
- Both suites: **47 passed, 0.47 s combined.**

# PROGRAM SYNTHESIS ARC 2 — Q0 → Q5 (reviewer's entry point)

**Dates:** 2026-07-31/08-01. **Read this first**; every claim below is backed
by a phase document + a gated artifact, in the pattern of
`PROGRAM_SYNTHESIS_ARC_SUMMARY.md` (arc 1's own summary, the model for this
one). Arc 2's own plan and preregistration were written before the code at
every phase (`PROGRAM_SYNTHESIS_ARC2_PLAN.md`, `PROGRAM_SYNTHESIS_ARC2_
PREREG.md`).

**The question in one sentence:** arc 1 measured three powered nulls, all
localized to the PROPOSE half's diet (domain mismatch, trigger poverty,
value-domain wall) — arc 2 asks whether feeding the proposer real,
in-domain, NL-paired content (not a bigger mechanism) finally moves it, on
a genuinely external benchmark (MBPP), measured with the same discipline
arc 1 used throughout.

## 1. Commit ledger

| phase | commit | what landed |
|---|---|---|
| PLAN | `9456ddbe82` | arc 2 scoped as content-not-mechanism: Q0 MBPP baseline + histogram picks scope; Q1 the one Rust phase; Q2 spec extraction; Q3 THE PAIRED DIET (train chunks+triggers+bigrams, in-domain, with prompts); Q4 descent/repair widening; Q5 the powered endgame — HQ3 decisive, a third null prereg'd as a FORK (retrieval-shaped proposal = arc 3), not a surprise |
| Q0 | `0dfeded7e1` | MBPP vendored (427 tasks); zero-shot **0.42%** [0.07,2.32] (STRESS protocol); dominant blocker `accepted_holdout_fail` 56.8% (single-example overfit, NOT the predicted value-domain wall) → the THREE-WAY PRIMARY/OFFICIAL/STRESS protocol fix; the joint-curve op-set recommendation (55%-mark scope) |
| Q1 | `752ff82933` | ProgEval+SynthEnumerate widened (str/float/bool/None/dict/set/tuple, bitwise int+set dual dispatch, math_native, ProgSlice, method-form oracles, general_builtins, container ctors, the `exclude` param); HQ1 LIVE unchanged (34.4%) — the emitter (Python, out of this phase's ownership) still blocks the shapes the engine can now run; honest split verdict named for Q1.5 |
| Q1.5+Q2 | `ca802ef59f` | Q1.5: the emitter TAUGHT the Q1 shapes (`_dotted_name` receiver-ambiguity fix); **HQ1 VERDICT 235/427 = 55.0%**, exceeding the projected 52.9% ceiling. Q2: `domains/mbpp_spec.py` (strict superset spec layer, 0 disagreements/1324 asserts); PRIMARY-runnable 240→**257/257 = 100%**; 50 train-only cue Concepts |
| Q3+Q4 | `c175cab21c` | Q3: the train diet mined (15 `mck_` chunks, 6/15=40% cueable vs arc-1's 2/15, 30 `mbpp_train` bigrams, leave-20-out probe: 11/20 mechanism engagement). Q4: scalar-loop descent, branch-arm holes, exclude-powered retry iteration, tol/unordered row verdicts (seed v1.3.0→v1.4.0, 43→49 rules) |
| **Q5** | this rung (uncommitted) | the POWERED ENDGAME: **FULL 18/257 = 7.00%** [4.48%,10.80%] (4.22% [2.68%,6.56%] over the 427-corpus denominator); **HQ3 NULLS A THIRD TIME** (−0.39pp, CI spans zero) with a sharp mechanistic attribution (a proposal-layer decoy tax, not "content doesn't matter"); HQ4 green (21/21, zero regressions); the migration matrix vs Q0; the arc-3 fork activated |

## 2. Headline capabilities as landed (all gated, all graph-native)

Unchanged from arc 1's own list (`PROGRAM_SYNTHESIS_ARC_SUMMARY.md` §2) —
arc 2 adds NO new mechanism to that list (per its own PLAN framing:
"content-not-mechanism"). What arc 2 adds on top:

1. **A widened value domain + op set** (Q1/Q1.5): strings, floats, bools,
   None, dicts, sets, tuples, slicing, method-form oracles, general
   builtins, container constructors — all live in `ProgEval`/
   `SynthEnumerate`, and the Python emitter (`emit_prog_ir`) now RECOGNIZES
   the shapes that produce them (55.0% of the 427-task corpus representable
   + predictable, up from 34.4%).
2. **A spec-extraction layer for benchmark prose** (Q2): `domains/mbpp_
   spec.py` turns MBPP's asserts into typed example rows (including
   float-tolerance and set-equality rows) and its prompts into normalized
   request facts — zero prose ever drives a decision, only facts a rule
   reads.
3. **A mined, in-domain, NL-paired content diet** (Q3): 15 chunks mined
   from the MBPP TRAIN split, cued from co-occurring TRAIN prompts (not
   arc-1's code-derived triggers) — the exact fix arc-1's H7c named as the
   missing ingredient.
4. **Descent + repair widened to two more structural classes** (Q4):
   scalar-loop (range-sourced) folds and two-arm branch conditions now
   descend and hole-fill, on top of arc-1's list-input-only descent.
5. **A three-way benchmark protocol, registered once and never drifted**
   (Q0/prereg): PRIMARY (the arc's anchor), OFFICIAL (protocol-distinct,
   never merged into a primary aggregate), STRESS (Q0-A's frozen
   zero-shot row, cited not re-run).

## 3. The powered numbers — the trajectory, and every HQ verdict

| moment | instrument | number |
|---|---|---|
| Q0-A zero-shot (STRESS, 1 revealed row) | 240 runnable / 257 test | **0.42%** [0.07%, 2.32%] |
| Q1 (engine widened, emitter not yet taught) | 427 corpus, representable+predictable | 34.4% (unchanged — the honest split verdict) |
| Q1.5 (emitter taught the Q1 shapes) | 427 corpus | **55.0%** — HQ1 VERDICT, bar ≥45% cleared by 10pp |
| Q2 (spec extraction) | 257 test, PRIMARY-runnable | **100%** — HQ2's anti-overfit denominator now covers the whole split |
| Q3 (train-internal mechanism probe, NOT a benchmark number) | 20 holdout train tasks | 55.0% (11/20) diet-content-used, mechanism only |
| **Q5 FULL (the arc's external number)** | 257 runnable / 257 test | **7.00%** [4.48%, 10.80%] |
| Q5 FULL, 427-corpus coverage denominator | 427 corpus | 4.22% [2.68%, 6.56%] |
| Q5 CONTENT-STRIPPED (the HQ3 control) | 257 runnable / 257 test | 7.39% [4.78%, 11.26%] |
| Q5 OFFICIAL (protocol-distinct, pass@1 analog) | 257 runnable / 257 test | 16.34% [12.32%, 21.35%] |

**HQ1 — value-domain + op-set coverage:** **CONFIRMED, 235/427 = 55.0%**,
exceeding the prereg's own 52.9% projected ceiling by 2.1pp (a receiver-
ambiguity fix the projection couldn't anticipate). A representability/
predictability fact, not an accept rate — necessary, nowhere near
sufficient (see HQ3/§6 below).

**HQ2 — spec-extraction quality:** **CONFIRMED, 100% PRIMARY-runnable**
(≥95% bar), 100% arg-count-correct, 99.6% recognized. Reframed correctly at
Q0 (recognition was never the bottleneck) and delivered exactly as scoped.

**HQ3 — the decisive retest, FULL vs CONTENT-STRIPPED:** **NOT CONFIRMED —
the THIRD null on this exact hypothesis shape** (after arc-1's H6 and
H7c), even with in-domain, NL-paired, TRAIN-mined content. Delta =
−0.39pp, 95% CI [−5.01pp, +4.22pp] (spans zero). The identity-list evidence
is sharper than a bare CI: **FULL's 18 passes are a strict SUBSET of
CONTENT-STRIPPED's 19** — content bought zero exclusive passes and cost
exactly one. The mechanism is now understood, not just measured: **every
one of FULL's 24 `gapped:exhausted` rows (a class ABSENT from
CONTENT-STRIPPED, 0/257) carries a chunk- or codebook-cued construction** —
a proposal that gets cued, turns out wrong, and consumes the fixed attempt
budget the enumerator (which does nearly all of the real work in this
domain) needed. **Per the prereg's own registered rule, this activates the
arc-3 fork:** retrieval-shaped proposal (decode against whole held TRAIN
PROGRAMS, not chunk shapes) is the next hypothesis, not a surprise.

**HQ4 — internal-battery non-regression:** **CONFIRMED, 21/21 green**
(`tests/test_prog_synthesis_battery_migrated.py`), frozen arms
byte-untouched. Broader neighbor sweep (15 suites, 422 tests spanning
mbpp/histogram/spec/diet/battery/descent/repair/value-domain/prog-ir) —
**422 passed, 0 failed, 9.0s** — zero flips anywhere in the arc-2 tree at
this moment.

## 4. Every null and registered deviation, honestly listed

- **Q0 — the plan's own prediction missed the dominant blocker.** The
  value-domain wall (`gapped:enumerate_failed`, 35.0%) was real but was NOT
  the largest class; single-example overfitting (`accepted_holdout_fail`,
  56.8%) was — a PROTOCOL artifact interacting with a real mechanism
  weakness, fixed by registering PRIMARY rather than by adding capability.
- **Q1 — HQ1's live number was UNCHANGED (34.4%) at Q1 itself.** The
  engine widened but the Python emitter (out of Q1's file-ownership scope)
  still didn't recognize the shapes that would produce the new value types
  — an honest "capability ≠ coverage until the emitter is taught" split
  verdict, resolved one phase later (Q1.5) exactly as named.
- **Q1.5 — the repo corpus (unrelated to MBPP) moved BOTH ways
  honestly.** Representability dropped 56.4%→50.0% (mutating `.append()`-
  style calls correctly reclassified as genuinely unrepresentable, not
  silently "representable but useless") while predictability rose
  9.2%→13.5%. Reported as a genuine trade-off, not hidden behind the MBPP
  headline.
- **Q3 — zero starter-shape affinity matches (0/8), a clean, informative
  null**, not a mining defect: real MBPP one-liners essentially never
  coincide exactly with the 8 hand-authored starter templates' grammar;
  `Fold`-based starters can never match emitted code at all (the emitter
  never emits `Fold`). Also: trigger vocabulary is real but noisy at
  support=2 per cueable chunk (honestly named, not smoothed over).
- **Q4 — one live-reverify pin drifted in the IMPROVEMENT direction**
  (`br_10`, `gapped`→`accepted_holdout_ok` under `repair_oracle` — the
  retry lane converging in the wild) and one bookkeeping-only drift on a
  neighboring team's file (task 267's interim `construction` label, same
  final verdict). Neither is a regression under the arc's own standing
  rule (only a currently-passing row flipping to failing is a STOP-defect).
- **Q5 — HQ3 nulls a THIRD time.** This is the registered outcome named in
  the PLAN itself (§4 risk #1) — not absorbed as "no measured gain," but
  used to trigger the pre-committed fork. Three tasks (115, 124, 237) hit
  `runner_exception:TypeError` — real, reproducible, engine/pipeline-level
  JSON-safety gaps this MEASURE-only phase names but does not fix (a raw
  `set` nested in an example row's inputs; a literal complex-number arg;
  a dict-typed expected value with tuple keys that is, additionally,
  ARM-DEPENDENT — reachable only via a codebook/chunk comparison path).

## 5. The arc's central empirical fact — restated and sharpened

Arc 1 established: *"constructions propose, execution decides" is
currently carried by the DECIDE half* — the verdict layer never miscarried
once, while the PROPOSE half's learned content never paid a CI-separated
premium (H6, P7-A diagnostic, H7c). **Arc 2 asked whether feeding the
proposer real content would change this, and it did not — with a sharper
answer than arc 1 had:** the proposal layer is not merely NEUTRAL, it
actively COSTS attempt budget when it cues wrong (§HQ3 above), and on
MBPP's actual solution shapes (single native-oracle calls, comprehensions)
the arc's 2-4-statement idiom-chunk grain is largely the wrong grain to
propose at. The representability ceiling (55.0%, HQ1) and the end-to-end
accept rate (7.00%, Q5 FULL) sit far apart — the gap between them IS the
propose/search half, quantified precisely for the first time this arc:
`gapped:enumerate_failed` (55.3% of all outcomes) and `accepted_holdout_
fail` (26.8%) together account for 82.1% of FULL's outcomes on tasks the
representability floor does not, in the main, forbid.

## 6. Consolidated residual ledger (named levers, deduped Q0→Q5)

1. **`RecvMethod:append` / mutating-method write-back** — 22 blocker
   occurrences at Q1.5, MBPP's single largest structural blocker; no
   lvalue write-back path for `xs.append(v)`-shaped mutation (named Q1
   follow-on, not landed).
2. **`comprehension_advanced` / `CompTargetComplex`** — 18 occurrences;
   non-trivial comprehension targets/multi-clause, named Q1 stretch, not
   landed.
3. **`map`/`lambda`** — 15 occurrences; no first-class callable/closure
   value exists in the DSL's value model.
4. **`kwargs`** — 13 occurrences; plumbing, excluded since P1.
5. **`regex`** — 28 tasks representable-but-not-predictable; explicitly
   out of the plan's scope (a genuinely new object model).
6. **Same-corpus helper-function externs** — a declared-oracle/multi-
   function synthesis concern, Q3+ territory, not an emitter gap.
7. **The proposal-layer decoy tax** (Q5's own new finding) — a wrong
   chunk/codebook cue consumes the fixed attempt budget the enumerator
   needs; a round-budget or exclude-on-decoy-detection mechanism is the
   named lever, distinct from "add more content."
8. **Retrieval-shaped proposal — the ACTIVATED arc-3 fork.** Decode
   against whole held TRAIN PROGRAMS (nearest-neighbour over
   structural/embedded similarity), not chunk-grain shapes — the
   registered next hypothesis now that shape-grain content has nulled
   three times (H6, H7c, HQ3).
9. **3 `runner_exception` residuals** (tasks 115, 124, 237) — a nested
   `set` in example-row inputs, a literal complex-number arg, and an
   arm-dependent dict-tuple-key PyO3 boundary error; named, not
   hand-patched (this arc's MEASURE-only phases never touch engine code
   to chase them).
10. **Carried from arc 1, still open:** the Rust `SynthEnumerate` `exclude`
    parameter now landed and USED (Q4 closed this one — the sole arc-1
    lever this arc actually retired); render-closure gaps (Abs/Min/Max/
    Fold into python/llvm); repair's multi-round oracle instrument; LLVM
    `call` still outside the lift dialect.

## 7. Standing-rules compliance note

- **Power the gate before the endgame:** Q5's every number is Wilson/
  Newcombe-CI'd on the full 257-task test split (no prefix cut fired); the
  HQ3 delta is reported with its CI, its per-episode step, and its 3×-step
  threshold, never a bare percentage.
- **A baseline is a list:** every artifact in the arc (`results/mbpp_
  zero_shot_baseline.json`, `results/mbpp_blocker_histogram.json`,
  `results/mbpp_train_diet.json`, `results/mbpp_endgame.json`) stores
  per-task rows; every aggregate in this document and in Q5's own doc is
  re-derived from those rows, gated by each phase's own test suite.
- **Synthetic-proven mechanism ≠ benchmark value:** Q3's train-internal
  55.0% mechanism-engagement number was explicitly never claimed as a
  benchmark result; Q5 is the benchmark-level retest, and it reports BOTH
  the mechanism attribution (§HQ3) and the aggregate delta, separately.
- **Eval-subset coverage is part of every claim:** every Q5 number carries
  both denominators (257 runnable / 427 corpus); the 427 line is
  explicitly labelled a coverage statement, never a claim about untested
  tasks.
- **No silent caps:** N was never cut anywhere in the arc; Q5's time-box
  mechanism is documented and recorded as NOT triggered
  (`condition.time_box.official_prefix_cut: null`).
- **Protocol boundaries are labelled in the data:** OFFICIAL rows carry
  `protocol: "official"` on every row and are excluded from the HQ3 delta
  by construction, gated (`test_official_arm_never_enters_a_primary_
  aggregate`) — the arc-1 REPAIR-ORACLE precedent, carried through
  verbatim.
- **A registered null is a fork, not a shrug:** HQ3's third null triggers
  the PRE-COMMITTED arc-3 hypothesis (retrieval-shaped proposal) exactly as
  the PLAN named it before this phase ran — the outcome was anticipated in
  writing, not rationalized after the fact.

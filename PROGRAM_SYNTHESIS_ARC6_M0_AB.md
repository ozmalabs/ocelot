# PROGRAM SYNTHESIS ARC 6 M0 — CEILINGS A and B (measurement only)

**Date:** 2026-08-01. Companion to `PROGRAM_SYNTHESIS_ARC6_PLAN.md` sec 1
(Seams A/B) and sec 3 (M0). Scope: measure two of the four M0 ceiling probes
before anything is built. **No engine/seed/adapter source was touched.**
Files created: `scripts/arc6_ceiling_ab.py`, `results/arc6_ceiling_ab.json`,
this document.

**Discipline honoured:** contamination (MBPP test-split `code` read for
measurement classification only, never merged into a codebook/cue table);
OEIS ground truth never entered MBPP scoring; every id-list claim is a list,
not a count; every estimate is labelled as an estimate; twin-run determinism
is checked and reported.

---

## 0. Current state, re-derived live (not `results/mbpp_endgame.json`)

`results/mbpp_endgame.json` (`measured 2026-08-01T03:10`) predates arc5's
exact-first rung (commit `ec41d3001c`) and arc5's MOVES build (commit
`4509632994`), both landed later the same day — using it would have
undercounted `pass` by at least 9 ids. Instead this M0 imports and calls the
**standing measurement driver unmodified**
(`scripts.mbpp_endgame_battery.boot_full` / `run_arm`, the same driver arc5's
own MOVES document used for its own before/after) against the **current
working tree**, full 257-task MBPP TEST split, PRIMARY protocol, twin-run
internally for determinism.

| | value |
|---|---|
| pass | **35 / 257** (13.6%, Wilson CI [9.96%, 18.35%]) |
| unreached (everything else) | **222 / 257** |
| determinism | **identical across both internal twin runs**, and reproduced identically on a full independent second script run (`cross_run_id_hash = eaeb284f…`, byte-identical both times) |
| elapsed | ~46s per full pass |

`pass_ids = [16, 20, 58, 59, 69, 82, 84, 85, 89, 90, 127, 132, 135, 138, 139,
142, 145, 227, 233, 234, 266, 276, 278, 281, 309, 312, 394, 404, 406, 410,
433, 443, 458, 472, 477]` — this includes exact-first's six geometry ids
(82/85/139/233/276/312) and MOVES's three ids (58/59/404), confirming this
run's 35 agrees with `PROGRAM_SYNTHESIS_ARC5_MOVES.md`'s own live-derived
35/257 headline (a useful cross-check: two independent measurement sessions,
same code state, same number).

Outcome taxonomy over the 222 unreached: `gapped:enumerate_failed` 117,
`accepted_holdout_fail` 79, `gapped:structural_verdict_reject` 14,
`gapped:no_shape` 6, `runner_exception:TypeError` 3, `gapped:exhausted` 2,
`not_recognized` 1.

---

## 1. CEILING A — the kernel import list

### 1.1 What was read (not paraphrased from the audit)

`domains/reason.py` (48 top-level functions, read via `ast.parse` + direct
inspection, not the audit's prose), `domains/comprehend_theorem.py` (16
functions), `domains/compute_grounding.py` (13 functions),
`domains/construction_grammar.py`'s `extract_function`/`comprehend_recursive`,
`domains/oeis_local.py` (5 functions), and all nine
`domains/construct_compute_*.py` modules (enumerations/betti/chain/gendef/
graphs/group_orders/homotopy/physchem/pi1/subgroups — 113 functions
combined). Also read directly: `seeds/math_prose_constructions.json` (the
grammar's actual data — clauses, member_forms, value_maps, filters,
aggregators, operators) and `reason.py`'s `CAPABILITIES` dict (line ~884),
the tower's own **declared-oracle table** — structurally the same shape Seam
A proposes to build on top of `ProgEval`.

**A correction found by reading the source instead of the audit:**
`reason.py` has more elementary number-theory kernels than the audit's prose
inventory named — `_isprime`, `_is_probably_prime` (Miller-Rabin),
`_is_perfect_square` (uses `math.isqrt`), and, critically, `math.comb` is
**already imported and called** inside `reason.py` itself
(`_steenrod_square_poly_coeff`, `math.comb(j, i) % 2`) for an unrelated
Steenrod-algebra purpose — meaning a general nCr oracle is a **zero-cost
registration**, not an import, for any task needing one.

### 1.2 Kernel inventory (31 entries; full detail in the JSON)

| kernel | module | computes | exact |
|---|---|---|---|
| `CAPABILITIES['prime']` (`_isprime`) | reason.py | primality test | yes |
| `CAPABILITIES['gcd'/'lcm']` | reason.py | math.gcd/lcm | yes |
| `CAPABILITIES['largest_prime_factor'/'prime_factors']` | reason.py | from `_factorize` | yes |
| `CAPABILITIES['divisor_count'/'divisor_sum'/'totient']` | reason.py | d(n)/σ(n)/φ(n) | yes |
| `CAPABILITIES[arithmetic/comparison set]` | reason.py | plus/minus/times/**exact** div/mod/gt/lt/ge/le | yes |
| `CAPABILITIES[collection ops]` | reason.py | range_incl/cardinality/member/is_empty/intersection/are_disjoint | yes |
| `_is_perfect_square` | reason.py | perfect-square test via `math.isqrt` | yes |
| `_is_probably_prime` | reason.py | Miller-Rabin, n<3.3e14 | yes (probabilistic but deterministic-bound) |
| `math.comb` (already called in this file) | reason.py | nCr | yes |
| `count_where`/`sum_where`/`chain_sum`/`chain_bind` | reason.py | binder evaluators (fold/filter/map over a Term-tree) | yes |
| `_matrix_rank_gf2`/`_matrix_rank_q`/`_smith_normal_form_factors` | reason.py | matrix rank / SNF | yes |
| `_integral_homology`, Steenrod/BG2/spin-bordism family | reason.py | graduate topology | yes (far outside MBPP) |
| `comprehend_theorem` | comprehend_theorem.py | prose theorem → checkable `ImplicationClause`, self-verified | yes, one family (group invariants over free products) |
| `comprehend_computational_definition` | compute_grounding.py | prose definition → Term-tree over held primitives, executed | yes |
| `extract_function` (3 routes: flat clause / embedded `=` / `comprehend_recursive`) | construction_grammar.py | OEIS-style sequence prose → closed-form/composed Term | yes |
| `construct_compute_*` (9 modules) | domains/construct_compute_*.py | bounded exact enumeration, one family per module, family **recognised by hand-authored regex** | yes per family, zero MBPP overlap (HLE-grade objects: Grassmannians, twist-spun branched covers, Grigorchuk subgroup counts) |
| `oeis_local.present`/`definition` | oeis_local.py | real downloaded OEIS parquet dump | verification oracle, not a solving kernel |

### 1.3 Match — id lists, reported honestly as two passes

**Coarse pass** (keyword regex over prompt+code, full 222-task unreached
population): `sqrt_trig_geometry` 9, `sequence_series` 5,
`number_theory_elementary` 5, `combinatorics_counting` 3,
`matrix_linear_algebra` 2, `group_or_abstract_algebra` 1,
`no_math_shape_detected` 197.

**Hand audit** (every one of the 25 coarse hits read against its real
prompt AND reference code — the 197 no-hit tasks were not individually
re-read, named as an explicit scope limit, not hidden):

| verdict | n | ids |
|---|---|---|
| `false_positive` (regex hit a substring, not the concept) | 13 | 12, 14, 17, 74, 100, 129, 171, 245, 255, 308, 414, 440, 441 |
| `no_kernel_named_gap` (no kernel on either side) | 3 | 124, 163, 293 |
| `adjacent_match` (primitive exists, needs composition) | 3 | 244, 256, 453 |
| `adjacent_missing_primitive` (math.comb registration) | 2 | 274, 300 |
| `adjacent_different_object` | 1 | 67 |
| **`genuine_match`** (a kernel already computes this exactly) | **1** | **96** |
| `adjacent_pattern` (hardcoded special case exists) | 1 | 260 |
| **`genuine_match_seam_b_named_gap`** | **1** | **420** |

Two named false-positive mechanisms, worth stating for anyone reusing this
regex: task 440's `.group(0)` (a `re.Match` method call in the reference
code) collides with the "group theory" keyword; task 308's "selecting one
**factor** from each list" (ordinary English "factor" = list element)
collides with "number theory factorisation."

**The honest headline for part (3): 2/222 unreached tasks are GENUINELY
expressed by an existing tower/grammar kernel today** (96 via
`reason.CAPABILITIES['divisor_count']`; 420 via the compositional aggregator
grammar, one value-map short — see 2.2 below). This is a small number.
**Per the plan's own framing, a small (3) is not a negative result — it is
the specification for (4).** The other 23 hits split into 6 "adjacent"
(primitive or pattern exists, composition/generalisation is the missing
piece) and 3 "no kernel exists on either side," with the remaining 13 being
confirmed keyword-collision noise.

### 1.4 The import list, ranked by tasks-unlocked per unit of import work

| rank | missing kernel | tasks unlocked | import cost |
|---|---|---|---|
| 1 | register `_isprime`/`math.isqrt`/`_divisor_count`/`_factorize` as oracles + one filtered-sum composition | 96, 244, 256, 453 (**4**) | **LOWEST** — pure registration, zero new math; every primitive is already written and (for divisor functions) OEIS-verified |
| 2 | add ONE value-map (`cubes_of`) to `seeds/math_prose_constructions.json` | 420 (1) | **LOWEST** — the seed's own `_doc_no_cubes` key already names this exact gap and its acquisition path |
| 3 | register `math.comb` (nCr) as an oracle | 274, 300 (2) | **LOWEST** — `math.comb` is stdlib and already imported+called in `reason.py` for an unrelated purpose |
| 4 | generic bounded linear-recurrence evaluator (generalise `_nth_fibonacci`) | 260 (1) | LOW — standard algorithm, one new function |
| 5 | Bell-number (set-partition) DP | 67 (1) | LOW — standard algorithm, same style as `_partition_count` |
| 6 | trig functions (`tan` at minimum) | 163 (1) | MEDIUM — no existing kernel on either side; exactness is only partial (cross-frame) |
| 7 | sqrt-of-composite-argument ExactFamily | 293 (1) | MEDIUM — same shape as rank 6 |
| 8 | complex-number support (`atan2`) | 124 (1) | MEDIUM, worst tasks-per-cost ratio (n=1, new representation) |
| — (not ranked) | group-theory invariants via `comprehend_theorem` | 0 (measured, not assumed) | **N/A — no matching task; the one coarse hit was a confirmed false positive.** Importing this would be speculative content against a measured-zero target, exactly the scoping risk the plan warns against. |
| — (not ranked) | a new `construct_compute_*`-style enumeration family | 0 | **N/A** — every existing family targets HLE-grade objects (Grassmannians, branched covers, Grigorchuk groups) with zero overlap in the unreached population |

**Ranks 1–3 unlock 7/222 (3.2%) of the unreached population at effectively
zero implementation cost** (registration of already-written, already-tested
functions, or one JSON entry the authors already flagged as deferred).
Ranks 4–8 unlock one task each at LOW–MEDIUM cost. The two "not ranked"
entries are recorded specifically to show that a plausible-looking class
(group theory, matching a coarse keyword hit) was checked and correctly
excluded once the false positive was found — the ranking is honest about
zero, not just about wins.

---

## 2. CEILING B — `extract_function`'s real reach

### 2.1 Live reproduction

`scripts/oeis_extract_verify.py`'s own mechanism was reproduced live in this
session (not merely cited): `extract_function` → `comprehend_computational_
definition` → `reason.solve`, against the real downloaded OEIS parquet dump.
**Result: 8/8 target sequences extracted from prose and verified against
real ground-truth values** (A000005/A000010/A000203/A000027/A000217/
A005843/A000290/A000142), plus the documented honest frontier (A000045
Fibonacci, A000040 primes — both correctly return no extraction, named not
faked). This confirms the propose-from-NL → verify-by-execution loop still
works before reasoning about its reach.

### 2.2 A vocabulary correction, found by reading the seed instead of the plan

The plan quotes "~10 clause constructions, 5 member forms, 4 aggregators, 4
filters, 27 operators" as `extract_function`'s vocabulary. Reading
`seeds/math_prose_constructions.json` directly: **the 27 "operators" are a
different construction family entirely.** Every one of the 27 has
`"held_runnable": false` and is a group-theory/topology invariant-naming
operator (`kernel_of`, `image_of`, `rank_of`, `euler_characteristic_of`,
`homology_of`, `betti_number_of`, `dimension_of`, `fundamental_group_of`,
`genus_of`) — this is `comprehend_theorem`'s asked-invariant-typing
vocabulary for HLE-style theorem prose, sharing this JSON file with, but
structurally unrelated to, the sequence-arithmetic grammar. **The actual
composable arithmetic surface for a sequence-in-`n` is: 10 clauses + 5
member-forms + 2 value-maps + 4 filters + 4 aggregators** — and only ONE of
the two value-maps (`squares_of`) is non-trivial; **`cubes_of` is
deliberately absent**, and the seed's own `_doc_no_cubes` key names both the
gap and its intended acquisition path
(`construction_grammar.acquire_construction`). This directly explains
task 420 (2.4 below) and materially narrows what "widening the grammar"
would mean — it is NOT "add more of the 27 operators" (those are inert for
arithmetic), it is "add more value-maps/member-forms/filters to the small
arithmetic core."

### 2.3 (i) / (ii) / (iii), measured over the 257 MBPP test prompts

| bucket | n | method |
|---|---|---|
| **(i) parses TODAY** | **3** (task ids 160, 267, 270) | MEASURED — `extract_function(prompt)` called live, non-empty candidate list |
| **(ii) would parse after a mechanical bedrock retarget** (index `n` → the function's own named parameters) | **101** | ESTIMATED — labelled heuristic (aggregator/member-form/filter/operator textual cues present AND reference-solution arity ≤3) |
| **(iii) needs genuine new vocabulary** | **153** | MEASURED classification into named missing-construction buckets |

**Honest caveat on (i), found by hand-checking all 3 hits, not just
counting them:** none of the 3 is a genuine correct extraction. Task 160's
prompt contains a literal `"ax + by = n"`; the embedded-`=`-segment route
grabs the trailing `n` as a bogus one-token "formula." Task 267 ("sum of the
squares of the first n odd natural numbers") partially matches the
`squares_of` value-map but the surrounding aggregator+member-form
composition fails, leaving the bare fragment `n*n` — wrong (it drops "sum
of," "first n," and "odd" entirely). Task 270 similarly yields the
fragment `2*n`. **The honestly reported number is: 3 non-empty parses, 0
genuine ones.** Both figures are given because the plan's own question
("how many are within the clause grammar") is about parsing, and a
degenerate non-empty parse is a real (if weak) data point about where the
grammar's regexes fire, distinct from correctness.

**(ii) is an estimate, explicitly**, built from textual cues
(aggregator/member-form/filter/operator vocabulary words in the prompt) plus
a reference-solution arity check (read via `ast`, MEASUREMENT-only per the
contamination rule) — not a built or run retargeted parser. It is stated to
be an over-estimate in some cases (a prompt can say "sum of" without the
underlying computation actually being a clean fold — e.g. task 267 above)
and an under-estimate in others (an aggregator-shaped task with no cue
word). The direction of the bias is NOT resolved by this measurement; it is
flagged, not corrected.

### 2.4 (iii) — missing constructions, ranked by frequency

| missing construction | n (of the 153) |
|---|---|
| unclassified (no single dominant cue) | 68 |
| dict/tuple construction (build/merge a record, not a scalar aggregate) | 34 |
| conditional selection (branch on a whole-input predicate, not a per-element filter) | 26 |
| string manipulation (concat/substring/case/split/replace) | 25 |
| sort/ranking (order a collection, kth-largest, no closed aggregator) | 13 |
| multi-step procedure (mutated state across loop iterations, not a pure fold) | 10 |
| regex/pattern match | 2 |

The single most concretely named gap in this whole measurement is **task
420** ("cube sum of first n even natural numbers"): this is EXACTLY the
`aggregator ∘ value-map ∘ member-form ∘ filter` shape the grammar already
composes for "squares of" — it fails today **only** because `cubes_of` is
the one deliberately unseeded value-map, and the seed file names its own
fix. Every other (iii) task needs a genuinely new construction family
(dict/tuple, whole-input conditionals, string ops, sorting, stateful loops)
— none of these are small additions to the existing single-index-sequence
grammar; each is closer to a new grammar the way `comprehend_theorem` or
`extract_function` itself was, per the audit's own honest comparison.

---

## 3. What was verified live vs analysed (summary)

**Verified live, this session:**
- The full 257-task PRIMARY-protocol MBPP battery via the unmodified
  `mbpp_endgame_battery` driver, twin-run internally identical, and
  reproduced byte-identically on a second independent full script run
  (`cross_run_id_hash = eaeb284f357d08099e86efb8a19bd9f459e3bee051e440b70eefaf9cae01903b`).
- `scripts/oeis_extract_verify.py`'s mechanism, 8/8, against the real OEIS
  parquet dump.
- Every kernel_inventory entry, by reading `reason.py`/`comprehend_theorem.py`/
  `compute_grounding.py`/`construction_grammar.py`/`oeis_local.py`/the nine
  `construct_compute_*.py` modules and `seeds/math_prose_constructions.json`
  directly (not the audit's prose).
- `extract_function(prompt)` called directly against all 257 test prompts
  for ceiling B's (i).
- Every one of the 25 hand-audit rows, by reading the task's real prompt AND
  reference code.

**Estimated/analysed, explicitly labelled:**
- Ceiling B's (ii) bucket (101 ids) — a textual-cue + arity heuristic, not a
  built retargeted parser.
- The 197 no-coarse-hit unreached tasks were not individually hand-read
  (named as a scope limit).

## 4. Honest limits

- Ceiling A's genuine-match count (2/222) is small; per the plan's own
  framing this is the specification for the import list, not a verdict on
  the seam. The import list itself is short and cheap at its top (ranks
  1–3, 7 tasks, near-zero cost) and thins quickly (ranks 6–8, one task each,
  real new machinery, no existing kernel on either side).
- Ceiling B's (i) is honestly closer to zero genuine parses once hand-
  checked; the loose (non-empty-candidate) count of 3 is reported alongside
  this, not instead of it.
- The plan's own "27 operators" figure is corrected here: those operators
  are inert (`held_runnable: false`) group-theory/topology invariant names
  for a DIFFERENT construction family (comprehend_theorem's), not part of
  extract_function's usable arithmetic vocabulary.
- Neither ceiling's numbers were used to build anything; per the task's
  scope, nothing in `domains/`, `seeds/`, or the Rust engine was touched.

# PROGRAM SYNTHESIS ARC 5 — SHAPE-CONSTRAINT CEILING PROBE: a null, precisely measured

**Date:** 2026-08-01. Answers the question posed before any build: *can shape
recognition + analogical transfer supply the DISCRIMINATING CONSTRAINT that
revealed rows cannot?* Driver: `scripts/arc5_shape_constraint_probe.py`.
Artifact: `results/arc5_shape_constraint_probe.json`. Gate:
`tests/test_arc5_shape_probe_migrated.py`, 22/22 passed. No synthesis/
engine/seed/spec code touched anywhere in this phase — measurement only.

**Headline: no.** Not "not yet" — measured directly, four independent ways,
against the real machinery (`RecogniseShape`, `TransferDecode`,
`SynthEnumerate`), and every one comes back negative or null. The reasons
are precise and mechanistic, not a shrug, and they are recorded below so a
future phase does not re-attempt the same dead ends.

---

## 0. The hypothesis, restated precisely

`PROGRAM_SYNTHESIS_ARC4_S6_NOTES.md` proved that excluding a structural trap
supplies **zero** of the 26 rejected candidates a passing accept, because a
trap satisfies every revealed row by definition — excluding it removes a
wrong answer but adds no new discriminating information. The hypothesis
under test here: recognising a goal's **shape** (e.g. "top of three" is an
N-ary extremum) yields a constraint no example row supplies — "the solution
must be symmetric in all three arguments" — that could (a) reject the trap
for a principled reason and (b) **prune the search** toward the correct
program.

---

## 1. Q1 — Recognition coverage: 23/257 (8.9%), and every one is spurious

| | value |
|---|---|
| MBPP test tasks probed | 257 |
| Recognised (RecogniseShape fires) | **23 (8.9%)** |
| Genuine algorithmic true positives among those 23 | **0** |
| Algorithmic-shape keywords held in `shape_vocabulary.json` (largest/max/min/sum/median/...) | **0** (verified: `algorithmic_keywords_held == []`) |

`shape_vocabulary.json` (the vocabulary `RecogniseShape` — the exact Term
the agent's own `categorise_by_shape` faculty runs — reads) holds 11
MetaShapes / 13 ShapePrinciples / 17 FunctionalRoles, and every one is
**systems/cognition-flavoured**: `scheduler`, `memory_store`, `gating`,
`regulate`, `predict`, `synchronize`, `homeostasis`, `winner_take_all`, ...
Not one keyword names an algorithmic/mathematical operation. This is a
statement about the vocabulary, not the mechanism — the mechanism itself is
exercised live and works exactly as designed (it is the SAME scorer
`domains/teach.py::categorise_by_shape` and `TransferDecode` both use).

Every one of the 23 hits is traced, mechanically (`matched_keywords`, a
literal substring audit), to an accidental collision with ordinary MBPP
prose, never a genuine semantic match:

| task | shape | matched keyword(s) | why |
|---|---|---|---|
| 11 | spatial_dynamics | `spatial_motion:move` | "re**move** first and last occurrence" |
| 58 | spatial_dynamics | `spatial_motion:posit` | "op**posit**e sign" |
| 299 | selective_gating | `integrate:aggregate` | "**aggregate**" (unrelated FunctionalRole `integrate`) |
| 308 | competitive_inhibition | (scheduler/winner_take_all `select`) | "**select**ing one factor" |
| 21 more | spatial_dynamics | `input_output:io` (near-universal, matches any "-io-" substring) plus `posit`/`move`/`convert` | prose collisions |

21 of the 23 land on the SAME shape (`spatial_dynamics`) via the
near-universal `io` substring (`input_output` role) — a further sign this is
noise, not signal: a vocabulary with genuine algorithmic coverage would not
funnel 91% of its hits into one unrelated bucket.

**Scope note on the analogical n=0..4 dial** (`domains/analogical_
thinking.py`): it operates over `Concept` nodes carrying name/category/
definition text; MBPP tasks are Goal/Message + IR subgraphs in this
pipeline, not Concept nodes, so the dial has no native input here without
an adapter step that does not exist. Not a separate measured channel;
`RecogniseShape`/`TransferDecode` is the one existing mechanism this
measurement can honestly drive against MBPP goals.

---

## 2. Q2 — Constraint yield: the catalogue, and what each assumes

| constraint | assumption | applicable (n/76) | violated | overlap with D3/D4 | NEW mass |
|---|---|---|---|---|---|
| **total dependence** | declared arity == read arity; an unread, revealed-varying param is a defect regardless of its value | 76 (always checkable) | **22** | **EXACT — this constraint IS D3+D4, reused verbatim** | 0 (it's the same detector) |
| **argument symmetry** | an N-ary extremum/sum/product/average over *unordered* quantities is invariant under permutation of which declared arg receives which value; checked using ONLY each revealed row's own values, re-assigned across args — no new magnitude is ever introduced | **3** (126, 164, 432 — arity≥2 AND prompt names a symmetric-shape word) | **1** (432) | 432 already caught by D3 | **0** |
| **arity from prompt** | a numeral word next to a quantity noun in the PROMPT ("...of three numbers") entails that declared arity | 4 (58, 126, 164, 292) | **0** | n/a (compares prompt to IR, not to D6's row-count check) | n/a — honest empty null |
| **monotonicity / idempotence / boundedness** | requires ≥2 revealed rows differing in EXACTLY one numeric variable to pose a directional question at all | precondition met by 33/76, but not implemented further | — | — | **reported INAPPLICABLE IN PRACTICE, not smoothed into a positive** |

**The sharp finding is the middle row.** Argument symmetry is the
constraint the hypothesis is built on (br_10's own shape). Applied to the
*entire* 76-trap population with an honestly-stated eligibility gate (arity
≥ 2 AND the prompt actually names a symmetric-shape word — itself a
vocabulary this measurement had to invent, since `shape_vocabulary.json`
holds none of it: `largest, greatest, maximum, max, smallest, least,
minimum, min, median, sum, total, product, average, mean`), it is
**applicable to only 3 of 76 traps**, violated by only 1, and that 1 was
**already caught by D3** (total dependence). **Zero new mass.** The
constraint this measurement built to test the hypothesis does not expand
the killable population at all over what the existing structural detectors
already reach.

`PROGRAM_SYNTHESIS_ARC4_STRUCTURAL_NOTES.md`'s own `check_swap_arity2`
(`scripts/arc4_failure_anatomy.py`) already probes a *weaker* neighbour of
this idea — swapping two same-typed arguments should not newly **crash** —
and deliberately declines to assume commutativity of *value*. Argument
symmetry is precisely the stronger semantic commitment that probe stopped
short of; measuring it directly shows why it stopped there: the population
where it would even apply is tiny, and where it applies it adds nothing.

---

## 3. Q3 — Would a constraint have converted a trap?

### (a) Principled rejection

| population | n | principled-reject (D1–D7 union OR argument-symmetry violation) |
|---|---|---|
| the 26 (S6-rejected) | 26 | **26/26 — tautological.** "The 26" *is* the set S2/S6's own structural detectors already caught; this is a self-consistency check, not new evidence. |
| the 36 (honest residual) | 36 | **0/36.** The new catalogue (argument symmetry, on top of the D1–D7 union) adds nothing to the population specifically defined as "nothing catches these." |

### (b) Pruning — the load-bearing measurement

Driven live against the real `SynthEnumerate` Rust engine (never
reimplemented) for all 12 non-retrieval-sourced S6 ids (`REOPENED_12` — the
only ids that ever actually reach the reopen lane in production;
`RETRIEVAL_SOURCED_14` never attempt reopening at all, so testing pruning
on them would be counterfactual) plus `br_10_top_of_three` (the sharpest,
already-characterised instance):

| task_id | probe found? | halt_reason | held-out verified correct? |
|---|---|---|---|
| 14 | False | budget | — |
| 58 | **True** | solved | **False** |
| 103 | False | max_size | — |
| 125 | False | max_size | — |
| 126 | False | budget | — |
| 164 | **True** | solved | **False** |
| 228 | **True** | solved | **False** |
| 304 | False | max_size | — |
| 396 | False | max_size | — |
| 414 | **True** | solved | **False** |
| 430 | False | budget | — |
| 432 | **True** | solved | **False** |
| br_10_top_of_three | False | budget | — |

**`pruning_succeeded_ids = []`. 0 of 13.**

Exclusion (the *only* search-restriction lever `SynthEnumerate` exposes)
either finds nothing (8/13: the trap and the correct program share the
exact same output vector on revealed rows, so excluding the trap's
signature excludes the correct answer too — the same wall
`PROGRAM_SYNTHESIS_ARC4_S6_NOTES.md` §4 proved for br_10, reproduced here
for 7 more MBPP tasks), or it finds *something* (5/13 — task 58's
accepted trap ignores `b`, task 432's ignores `a`/`b`, etc.; each escapes
the exclusion wall only because its runtime output TYPE differs from the
row's declared type, e.g. `int 0/1` vs `bool True/False`, and
`SynthEnumerate`'s own canon treats `bool ≠ 1` — a type-canon accident, not
new information). **Every one of the 5 "found" candidates is verified
WRONG against the held-out row** (measurement-only read, never fed back
into search — see §4). Examples of what MDL search hands back once freed
from the exclusion wall with no new constraint to guide it:

- task 58 ("opposite sign"): `1 - (abs(a) > 1)` — doesn't read `b` at all.
- task 164: `(a > a)` — a candidate that is trivially always `False`,
  which happens to match both sparse revealed rows.
- task 432 ("median length of a trapezium"): `15 * (-1 + (c / 15))` = `c -
  15` — doesn't read `a` or `b`; the true relation is `(a+b)/2` and doesn't
  read `c`. (Neither total dependence nor argument symmetry would have
  discriminated this pair — both are *partial*-dependence formulas on
  *different* variable subsets, a texture worth naming honestly rather
  than folding into the catalogue as a clean win.)

**The mechanism, stated once, generally:** `SynthEnumerate`'s equivalence-
pruning keys candidates by their **observed output signature over the
example rows**. A structural trap, by definition, reproduces every revealed
row's expected value — so its signature over those rows literally *equals*
the target signature. Any genuinely correct completion must *also*
reproduce that target signature, so it necessarily shares the trap's
signature, and excluding the trap prunes the correct answer alongside it.
This is not a per-task accident; it is a property of what "trap" means
combined with how the *only* existing pruning primitive works. A shape
constraint that could reject the trap for a principled reason (§2) still
cannot be turned into a *search restriction* through this engine's
existing hooks, because the hooks operate on behavior, and behavioral
identity on revealed rows is exactly the trap's defining property.

---

## 4. Q4 — Analogical transfer: nothing to transfer from

| | value |
|---|---|
| Held `Mechanism` entries (`seeds/mechanism_index.json`) | 2 (`spatial_foveation`/`selective_gating`, `homeostatic_regulation`/`feedback_control`) |
| Algorithmic among them | **0** |
| Held math `ShapeSignature` entries (`seeds/math_capability_shapes.json`, kind=math) | 17 (fractal, phi-bounded-recursion, self-similarity, symmetry, curvature, topology) |
| Algorithmic among them | **0** — these bridge math CONCEPTS to the agent's own faculties via `AntiUnify`/structure-mapping, a *different* mechanism from `TransferDecode`'s `meta_shape` retrieval, and are not indexed by it at all |
| Live `TransferDecode`/`retrieve_and_transfer_mechanism` probes against algorithmic goals (top_of_three, median_of_three, volume_triangular_prism, sum_two_numbers) | **4/4 honest walls** (`meta_shape: null`, `transferred: null`) |

This reproduces, live, exactly what `tests/test_mechanism_transfer_
migrated.py` already established structurally: the transfer mechanism
itself works (it is exercised end-to-end elsewhere with real transfers for
systems-shaped goals), but the codebook it reads from has never been
seeded with anything program-synthesis-shaped. Recognition fails *before*
retrieval is even attempted — `RecogniseShape` never matches an algorithmic
goal (same root cause as Q1), so `TransferDecode` never reaches the point
of having a candidate mechanism to try.

**What would have to be seeded**, named exactly:

1. An `extremum` / `total_function_of_declared_args` `MetaShape` +
   `ShapePrinciple` + `FunctionalRole` keyword set (`largest`, `max`,
   `min`, `sum`, `median`, ...) so `RecogniseShape` fires on
   program-synthesis goals at all.
2. A `Mechanism` entry under that shape with abstract steps like
   `["compare", "PART", "with", "PART"]` / `["fold", "winner", "over",
   "REMAINING"]` that `TransferDecode` could re-instantiate at arity N.

Neither exists today. This is the honest, specific gap — not "the
mechanism doesn't work," but "the codebook is empty in this direction."

---

## 5. CONSTRAINT vs. PROPOSAL — the verdict this whole probe was designed to force

Four prior arcs (S0-A through S6) measured that *better proposals* are
worth approximately nothing once a candidate already satisfies every
revealed row — the bottleneck is discriminating information, not search
breadth. This probe asked whether shape math is a genuinely different
mechanism: **constraint from structure**, not another proposal source.

**Measured answer: in this codebase, today, shape recognition supplies
proposals at best, and only rarely even that — it does not supply
constraint that prunes.**

- Q1: the vocabulary that would need to recognise a shape is not
  algorithm-shaped at all (0 genuine hits/257).
- Q2: even the ONE constraint this measurement built specifically to test
  the hypothesis (argument symmetry) is applicable to 3/76 traps and adds
  **zero** discriminating mass beyond what the existing D1–D7 detectors
  already reach.
- Q3(a): trivially confirms the 26 (tautological) and confirms the 36
  gains nothing (the real test).
- **Q3(b), the number that matters: 0/13 pruning successes, live, against
  the real engine.** Where the exclusion mechanism finds *anything* at all
  (5/13), it is a *proposal* with no more warrant than the trap it
  replaced — every one is wrong on held-out data. This is the clean
  empirical line between "found a candidate" (proposal) and "found the
  right candidate for a principled reason" (constraint): the artifact
  never conflates the two (`pruning_succeeded_ids` requires BOTH
  `found=True` AND a held-out-verified-correct check, gated by
  `tests/test_arc5_shape_probe_migrated.py::
  test_found_is_not_conflated_with_correct`).
- Q4: the one place a *cross-domain* constraint could plausibly enter
  (transferred mechanism steps) is architecturally sound but empty in the
  algorithmic direction — a seeding gap, not a mechanism failure.

**This is a NULL, and it should be reported as one before anything is
built.** The reason is not that shape recognition is a bad idea in
general — `TransferDecode`/`RecogniseShape` demonstrably work for the
systems-shaped goals they were seeded for (`test_mechanism_transfer_
migrated.py`, 4/4 green). It is that (1) the vocabulary is pointed at the
wrong domain (systems/cognition, not algorithms), and (2) even granting a
hand-built, on-hypothesis algorithmic constraint, the ENGINE's only
search-restriction primitive (`SynthEnumerate`'s `exclude`) is
behavior-keyed, and a structural trap's behavioral identity with the
correct answer on revealed rows — the very thing that makes it a trap — is
exactly what makes behavior-keyed exclusion unable to separate them.
Closing this would require either (a) a genuinely new engine primitive —
an admissibility filter applied at candidate-CONSTRUCTION time (e.g. "may
not compile if it fails to read all N args" or "may not compile unless
permutation-invariant"), not a post-hoc behavioral exclusion — combined
with (b) seeding an actual algorithmic shape vocabulary (§4's two items).
Neither is attempted here; this measurement's job was to establish,
honestly and empirically, whether it was worth building before doing so.

---

## 6. Discipline notes

- **Revealed rows only** for every SEARCH-side function
  (`check_total_dependence`, `check_argument_symmetry`,
  `check_arity_from_prompt`, `check_monotonicity_precondition`,
  `run_exclude_probe`) — mechanically audited (no function's source
  contains the literal substring `held_out`,
  `test_search_functions_never_reference_held_out`). Exactly one function
  (`verify_found_program_against_held_out`) reads held-out data, for
  MEASUREMENT ONLY (the sanctioned pattern `domains/mbpp_spec.py`'s own
  contamination_rule and `PROGRAM_SYNTHESIS_ARC4_STRUCTURAL_NOTES.md`'s
  hand-witness verification already establish), and its result is never
  threaded back into any search call — confirmed by construction (§3(b)'s
  probe loop calls it strictly *after* the search result is already
  final) and gated live.
- **Twin-run determinism.** `scripts/arc5_shape_constraint_probe.py`
  computes the full result twice per invocation and asserts a SHA-256
  match (excluding the two live-clock fields) before writing the artifact;
  `tests/test_arc5_shape_probe_migrated.py::
  test_determinism_fresh_two_pass_reproduces_live` reproduces this
  independently.
- **IDs never hand-typed twice differently.** `THE_26` /
  `RETRIEVAL_SOURCED_14` / `REOPENED_12` are quoted verbatim from
  `tests/test_reject_informs_repair_migrated.py` (S6's own gate); the 36
  is read live from `results/arc4_structural_verdicts.json`. Both are
  re-derived from their frozen sources and compared in
  `tests/test_arc5_shape_probe_migrated.py`
  (`test_the_26_matches_frozen_arc4_endgame`,
  `test_residual_36_matches_frozen_structural_verdicts`).
- **Frozen artifacts stay frozen.** `results/mbpp_arc3_endgame.json`,
  `results/arc4_endgame.json`, `results/arc4_structural_verdicts.json` are
  read-only citations throughout; nothing in this phase re-runs FULL-R3 or
  the S0-A/S6 batteries.

---

## 7. Files

`scripts/arc5_shape_constraint_probe.py` (driver — Q1–Q4, twin-run
determinism, held-out isolation audit; reads the frozen artifacts above
plus `seeds/shape_vocabulary.json` / `seeds/mechanism_index.json` /
`seeds/math_capability_shapes.json`, and drives the real `RecogniseShape` /
`TransferDecode` / `SynthEnumerate` Rust Terms live; touches no synthesis/
engine/seed/spec code).

`results/arc5_shape_constraint_probe.json` (the artifact — per-task Q1
recognition rows for all 257 test tasks; Q2 catalogue with per-constraint
id lists over the 76-trap population; Q3(a) principled-rejection id lists
for the 26 and the 36, Q3(b) 13-entry empirical pruning table with
held-out verification; Q4 live transfer probes; determinism hash;
environment).

`tests/test_arc5_shape_probe_migrated.py` (22 passed, ~1.5s: schema; 4
population-continuity cross-checks against frozen sources; held-out
isolation gate (search functions clean, verify function is the one
sanctioned exception); 3 pinned live re-verifications (Q1 count + named
false positive, Q3(b) task-14 exclude probe, Q4 transfer honest wall);
determinism (artifact-recorded + independently reproduced); the
constraint-vs-proposal discipline gate on `pruning_succeeded_ids`; the
tautology-vs-real-finding split for Q3(a)).

This file.

---

## 8. Residuals — named, not hidden

- **The argument-symmetry catalogue entry is hand-built, not agent-native.**
  It lives in the probe script as a measurement instrument, not as a Rule
  or seeded `ShapeSignature` — deliberately, since the brief is a ceiling
  measurement, not a build. If a future phase wants this as agent
  capability, it needs to become graph data (a `ShapeSignature`/rule),
  per this repo's architecture rule.
- **The engine primitive gap is named but not built.** §5 states precisely
  what a construction-time admissibility filter would need to look like;
  none is implemented, per this phase's "no engine changes" scope.
- **The trapezium case (task 432) shows partial-dependence-on-different-
  subsets, a texture neither total-dependence nor argument-symmetry
  catches cleanly** — recorded honestly in §3(b) rather than smoothed into
  the catalogue's clean cases.
- **Monotonicity/idempotence/boundedness was scoped to a precondition
  check only** (does the population even have the row-pairs needed), not
  a full directional-comparison implementation — 33/76 meet the
  precondition, but no further claim is made about whether the check
  itself would discriminate anything; reported as inapplicable in
  practice, not built out further under this phase's time-box.

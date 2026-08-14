# Pointing the solver dispatch toolbox at real math problems — RESULTS

Base `main @ 40d0bdb` ("Add line summary: R1-R5 dyad, N1-N3 network, U0-U2
intent"), verified via `git log --oneline -1 main` immediately before
creating the worktree. Worktree: `/home/matt/ozmadev/ocelot-worktrees/
solver-math-boundary`, branch `solver-math-boundary`, commits `d34ddaf`
(PREREG) + `e6e983c` (battery script + regression pins). `data/` was absent
in the fresh worktree (not a partial real directory); symlinked
(`ln -sfn /home/matt/ozmadev/ocelot/data data`) and confirmed
`data/wiktionary/en.jsonl.gz` resolves to the real 492,560,156-byte file —
the documented gotcha, checked directly.

This document reports what was RUN against the already-registered
`SOLVER_MATH_BOUNDARY_PREREG.md` — it does not re-derive the design
reasoning; see that document for the full argument behind every prediction
this document confirms or falsifies. **This is a DIAGNOSTIC/MAPPING task,
per the task's own framing — no new solver capability was built.** Every
number/schema/status below comes from a REAL call into the real toolbox
(`domains/solver_dispatch.py`'s seven `solve_*` resolvers, dispatched
through the UNCHANGED `qd_bind_resolver` JOIN), never a stub or a
hand-simulated outcome.

**Headline finding:** the toolbox's real coverage is exactly what
`SOLVER_MATH_BOUNDARY_PREREG.md` predicted (single-fact conditional/
universal/existential logic mints; arithmetic/algebra/search/permutation
wall cleanly and file gaps correctly) — but the investigation surfaced
**two real, evidenced silent-wrong findings that were NOT predicted this
precisely in advance**: (1) a bare numeric "is"-copula sentence (e.g. "What
is 17 * 23?") does not wall — it silently mints a fabricated implication
schema, `status:"resolved"`, indistinguishable in shape from a genuine
success; (2) `mode="auto"`'s fixed parser-try-order means a leading-
quantifier sentence ("All philosophers are mortal") is resolved by the
WRONG (unstripped) parser whenever the bare form also happens to parse —
which it always does — silently degrading schema quality below what an
explicit `mode="universal"` call produces. Both are pinned as regression
tests (`tests/test_solver_math_boundary.py`), not fixed — per the task's
explicit instruction not to force capability that isn't real.

---

## 1. The battery

No real math-benchmark fixture exists anywhere in this repo (checked: grep
for `GSM8K`/`gsm8k`/`math_qa`/`MathQA`/`arithmetic_bench` across the tree;
`tests/fixtures/mbpp/sanitized-mbpp.json` is a real external fixture but is
CODE-synthesis, not math word problems; `seeds/mathematics.json`/
`seeds/logic_mathematical.json`/`seeds/math_prose_constructions.json` are
held domain KNOWLEDGE for a different subsystem
(`compute_grounding.comprehend_computational_definition`, OEIS-style
sequence-prose reading), not a problem battery and not reachable through
`qd_bind_resolver` at all). Per the task's own fallback instruction, the
battery is hand-built: 15 problems + 3 supplementary probes, in
`scripts/solver_math_boundary_run.py`, registered in full in
`SOLVER_MATH_BOUNDARY_PREREG.md` §4 before running.

## 2. A load-bearing structural fact, confirmed by direct read before running
   anything (PREREG §1, re-stated here because it governs every row below)

Of the seven `solve_*` resolvers, **only `solve_deduction` accepts raw
text.** The other six (`solve_can_relax`/`solve_can_exact`/`solve_can_bp`/
`solve_reasoning_bridge`/`solve_analogical_promote`/`solve_decompose`) all
require a caller to have ALREADY built the prerequisite graph object
(a CAN `Microtheory`, a `DirectionalCorrespondence`, a candidate-projection
list) by hand before minting the Goal — there is no NL-to-CAN-network,
NL-to-correspondence, or NL-to-candidate-projection path anywhere in this
toolbox. Every problem below was therefore first attempted through
`solve_deduction` (the only genuine front door for a raw, novel problem);
the CAN- and decomposition-shaped problems (13, 12) were ADDITIONALLY
attempted through their more specific resolver, with the prerequisite graph
object built by hand, to also measure the toolbox's ceiling given
structure a caller already extracted, not just its floor on raw text.

## 3. Per-problem outcome table

Full raw output: `scripts/solver_math_boundary_run.py` output (every row
below is read directly off that live run, not summarised from memory).

| # | shape | problem (truncated) | attempted kind | dispatch outcome | gap filed | actually correct? |
|---|---|---|---|---|---|---|
| P1 | arithmetic | "What is 17 * 23?" | `solve_deduction` | **resolved** | no | **NO — silently wrong.** Mints `logical_17_23`: `is_a(X,17) => is_a(X,23)`, a fabricated implication with no relation to the arithmetic question |
| P2 | arithmetic | "144 divided by 12?" | `solve_deduction` | walled | **yes (1)** | n/a — clean honest wall |
| P3 | algebra | "2x+3=11" | `solve_deduction` | walled | **yes (1)** | n/a — clean honest wall |
| P4 | algebra | "5x-7=18" | `solve_deduction` | walled | **yes (1)** | n/a — clean honest wall |
| P5 | logic, conditional | "If X is a fish, X can swim." | `solve_deduction` | resolved | no | **YES** — `logical_fish_can_swim`, the toolbox's own documented worked example, correct |
| P6 | logic, bare universal | "A bird can fly." | `solve_deduction` | resolved | no | **YES** — `logical_bird_can_fly`, correct |
| P7 | logic, explicit universal (mode=auto) | "All philosophers are mortal." | `solve_deduction` | resolved | no | **PARTIALLY** — `logical_all_philosophers_mortal`: antecedent is the un-stripped blob `all_philosophers`, not the singular `philosopher` an explicit `mode="universal"` call produces (SUP check, below) |
| P8 | logic, existential (mode=auto) | "Some bird is a penguin." | `solve_deduction` | resolved | no | **PARTIALLY** — antecedent blob `some_bird`, not stripped (same defect class as P7) |
| P9 | logic, two-premise syllogism, raw | "All men are mortal. Socrates is a man. Is Socrates mortal?" | `solve_deduction` | resolved | no | **NO — silently wrong.** Mints `logical_all_men_mortal_socrates`: antecedent `all_men`, consequent `mortal_socrates` — a nonsensical cross-sentence word blob, not a correct reading of any of the three sentences, and NO field anywhere addresses whether Socrates is mortal |
| P9b | logic, syllogism premise only | "All men are mortal." | `solve_deduction` | resolved | no | partial (same blob-antecedent defect) — see §5 for the isolated confirmation that no application step exists at all |
| P10 | word problem, multi-step arithmetic | "Sarah has 3 apples..." | `solve_deduction` | walled | **yes (1)** | n/a — clean honest wall |
| P11 | word problem, geometry | "rectangular garden 5m by 3m..." | `solve_deduction` | **resolved** | no | **NO — silently wrong.** Mints `logical_rectangular_garden_5m`: `is_a(X,rectangular_garden) => is_a(X,5m)`, fabricated, same failure class as P1 |
| P12 | word problem, decomposition-shaped | "$60 bill split..." | `solve_deduction` | walled | **yes (1)** | n/a — clean honest wall |
| P12b | (same) | (same) | `solve_decompose`, honest empty candidate list | walled | **yes (1)**, `gap_key:"solve_decompose:no_candidates"` | n/a — clean honest wall, no fabricated decomposition |
| P13a | CAN-shaped, raw text | "Stress increases sleeplessness..." | `solve_deduction` | walled | **yes (1)** | n/a — clean honest wall, as predicted |
| P13b | (same), hand-built CAN network | (same, network built by hand, sentence never ingested) | `solve_can_exact` | **resolved** | n/a | **YES** — real global-minimum energy=-3.0, treewidth=1; settled state (stress +1, sleeplessness +1, productivity -1) is the correct qualitative answer ("more stress → less productivity") GIVEN the hand-built network |
| P14 | combinatorial search | "smallest int ≡1 mod 2,3,4,5,6" | `solve_deduction` | walled | **yes (1)** | n/a — clean honest wall |
| P15 | permutation | "3 books on a shelf, how many arrangements?" | `solve_deduction` | walled | **yes (1)** | n/a — clean honest wall |

Supplementary probes (not part of the 15-problem battery; run to pin down
the P7/P8/P9 ladder-ordering finding precisely):

| # | problem | mode | outcome | schema |
|---|---|---|---|---|
| SUP-P7 | "All philosophers are mortal." | `universal` (explicit) | resolved | `logical_universal_philosopher_mortal` — **correctly singularised**, unlike the `mode=auto` run of the identical sentence |
| SUP-P9b | "All men are mortal." | `universal` (explicit) | resolved | `logical_universal_men_mortal` — quantifier correctly stripped (`men`, not `all_men`); the residual imprecision (`men` not singularised to `man`) is the SAME already-documented WordNet-morphy irregular-plural limitation `propositional_deduction.py`'s own docstring names (`_singular_attr`), not a new defect |
| SUP-P8 | "Some bird is a penguin." | `existential` (explicit) | resolved | `existential_bird_penguin` — correctly stripped (`bird`, not `some_bird`) |

## 4. Gap-filing (Rung 2) held up correctly under genuinely novel input

Every wall above filed **exactly one** `SelfConcern{kind:"solve_failure"}`,
content-deduped on `gap_key` (statement text for `solve_deduction`, a fixed
string for `solve_decompose`'s no-candidates case) — confirmed by direct
count (`_gap_count` in the runner script), not assumed. No cross-problem
collisions occurred (every `solve_deduction` gap_key is unique statement
text). This is the first REAL, independently-authored (not toolbox-author-
written) problem set to exercise `note_solve_exhausted_gap`
(`seeds/gap_awareness.json`) — it held up exactly as Rung 2's own toolbox-
fixture tests found: correct filing on failure, correct silence on success
(P1/P5/P6/P7/P8/P9/P9b/P11/P13b all resolved and filed zero gaps, confirmed
directly). **One important nuance this battery adds that Rung 2's own
tests could not**: P1, P9, and P11 all `status=="resolved"` while being
SEMANTICALLY WRONG — Rung 2's gap mechanism has no way to detect this, by
design (it only ever sees `status`, never checks correctness), so these
three silently-wrong outcomes file **zero gaps** — the agent has no idea
anything went wrong on exactly the cases where something did. This is
named, not proposed as something to fix here (it would require a
correctness oracle the toolbox does not and cannot have for open-ended
NL — out of scope for a dispatch-mechanism gap-filer).

## 5. `solve_deduction`'s precise reach — the sharpest section of this
   document, per the task's own request to characterize it precisely

**It does not reach single-step syllogism application, let alone chained
inference.** Confirmed by direct code read (`domains/propositional_
deduction.py`, `domains/solver_dispatch.py::solve_deduction`) BEFORE running
anything (PREREG §2), then confirmed LIVE (P9/P9b): `mint_logical_schema`/
`mint_universal_schema`/`mint_existential_premise` each install exactly ONE
`ShapeSignature` from ONE statement. None of them, and no code path inside
`solve_deduction`, ever ingests a SECOND fact ("Socrates is a man") or
evaluates a query against a specific bound instance. The facility that
actually DOES this — `inference_generation.py`'s `detect_implication_gaps`/
`resolve_implication_gap`/`detect_existential_gaps`/`resolve_existential_gap`
— exists in the codebase and is real, working machinery (used elsewhere by
the ordinary conversation comprehension pipeline), but it is **not one of
the seven `solve_*` resolvers** and has no route through `qd_bind_resolver`
at all. Handed the full, realistic three-sentence syllogism, `solve_deduction`
does not even fail cleanly on this account — it silently mints a
nonsense schema by treating "Socrates is a man" and "Is Socrates mortal?"
as if they were more antecedent/consequent material for the SAME
implication as "All men are mortal," fusing "mortal" and "Socrates" into one
consequent attr (`mortal_socrates`) that means nothing.

**Does quantified deduction (universal/existential instantiation, built
earlier this session) extend the reach?** Only in the narrow sense of
correctly parsing a SINGLE universally/existentially quantified premise on
its own (SUP-P7/SUP-P8, and confirmed working via the toolbox's own
Rung1/2/3 test suites) — it does not extend `solve_deduction`'s reach to
multi-fact application or query-answering at all; that capability boundary
is identical with or without the quantified-premise extension, because the
extension only adds MORE ways to mint isolated background knowledge, never
a way to apply it.

**Verdict, stated as precisely as the task asks:** `solve_deduction`'s real
reach is "install one held implication/premise from one, syntactically
well-behaved copular/capability sentence." It is a KNOWLEDGE-MINTING
facility, not a QUERY-ANSWERING one. Every one of the four minting forms
(conditional / bare-universal / universal / existential) genuinely works
within that narrow scope; none of them, individually or composed, reaches
even single-step syllogism application.

## 6. `mode="auto"`'s ladder-ordering defect, characterized precisely

`solve_deduction`'s `mode="auto"` default tries `mint_logical_schema`
(plain conditional/bare-universal, NO quantifier-word stripping) BEFORE
`mint_universal_schema`/`mint_existential_premise` (`domains/solver_
dispatch.py:274-280`). Because "All X are Y" and "Some X is Y" are BOTH
grammatically valid bare-universal clauses on their own (subject = "All X"/
"Some X", exactly the shape `mint_logical_schema`'s own bare_universal path
already grounds), the bare parser ALWAYS succeeds first on a
leading-quantifier sentence, and the auto ladder keeps that first success
(`solver_dispatch.py:284`, "keeps the first success") — the dedicated,
quantifier-aware parsers are NEVER reached for a leading-quantifier
sentence under `mode="auto"`, even though they exist and produce a strictly
better-quality schema (SUP-P7/SUP-P8 above, confirmed by direct A/B on the
identical statement). This is a real, evidenced, narrow defect — not a
capability gap (the correct parser exists and works, confirmed live) but a
**dispatch-ordering defect inside one resolver's own fixed ladder**. Named
here, pinned as a regression test on BOTH sides (the auto-mode blob output
AND the explicit-mode correct output), NOT fixed — reordering the ladder
(or pre-checking for a leading quantifier word before trying the plain
parser) is a plausible, low-risk future fix, but it changes existing,
already-tested `mode="auto"` behaviour depended on by Rung 1's own
committed test fixtures, so it is left as a named finding for a future,
deliberately-scoped rung rather than patched inside a diagnostic task.

## 7. Rung 3 (`ProblemShape`) — data-sufficiency picture, rechecked with a
   genuinely new, independently-authored population

Every `solve_deduction` Goal minted in this battery — resolved OR walled,
correct OR silently wrong — was additionally run through
`domains.problem_shape.observe()` (confirmed live, not assumed):
**100% recognize as the single pre-seeded `ps_has_statement=yes` shape**
(`covered_by == "ps_has_statement=yes"` on every one, including P1/P9/P11's
silently-wrong resolves and every clean wall). This exactly matches
`SOLVER_MATH_BOUNDARY_PREREG.md` §5's prediction: `ProblemShape`
discriminates by which ATTRS/EDGES a Goal carries (all fifteen carry
`statement`), never by statement CONTENT or outcome correctness, so a
genuinely novel, independently-authored 15-problem population produces MORE
real recognition instances of an already-seeded shape but **does not
supply Rung 3's still-missing pre-mint recognition corpus** (a raw,
UNCLASSIFIED problem whose `solve_*` kind is not already known by the
caller) — every Goal in this battery was minted via an explicit
`mint_solve_deduction_goal` call, exactly like every one of Rung 3's
original 19 instances. **`QUESTION_DRIVER_BUGFIX_AND_RECHECK_RESULTS.md`'s
NO-GO on Rung 3.5 (pre-mint auto-dispatch) and Rung 4 (hold-open
multi-candidate) is UNCHANGED by this task** — confirmed directly, not
inferred: this battery adds 15+3 new `solve_deduction`-kind observations
(the same kind, same axes, same caller-already-knew-the-kind property as
every prior instance), and zero new `solve_can_*`/`solve_reasoning_bridge`/
`solve_analogical_promote`/`solve_decompose` observations that would
compete for a DIFFERENT `ProblemShape` (P13b's `solve_can_exact` Goal
recognizes as `ps_has_targets_mt=yes`, the SAME pre-seeded CAN shape 5 real
prior instances already established — no new competition either).

## 8. Was anything cheap and evidenced enough to build? — checked, NO-GO

Per the task's own instruction (§4: "do NOT force this"), a build was
considered and explicitly rejected on the evidence:

- **No arithmetic/algebra bridge exists anywhere in the codebase to wire
  cheaply.** Checked directly: no `eval_arithmetic`/`parse_arithmetic`/
  calculator primitive exists in `domains/` or `runners/`. The nearest
  candidate, `domains/prog_synthesis.py`'s `ProgEval`/enumeration
  machinery, is shaped for EXAMPLE-DRIVEN program synthesis (given
  input/output pairs, search for a program) — a bare arithmetic question
  ("what is 17*23?") supplies no examples and is not a synthesis task; there
  is no natural adapter here, only a forced one. Named as a real absence,
  not a missed cheap win.
- **The two real defects found (§§5-6) are both inside
  `propositional_deduction.py`/`solver_dispatch.py`'s OWN existing scope**,
  not a new-capability bridge — fixing either would be a legitimate future
  rung (the ladder-ordering one in particular looks low-risk and
  well-scoped), but BOTH would need to touch code Rung 1/2/3's own committed
  test fixtures already exercise and assert specific outcomes against;
  doing that inside a diagnostic/mapping task, without the task's own
  explicit go-ahead to modify existing toolbox semantics, was judged out of
  scope. Pinned as regression tests instead, so a future rung that DOES fix
  either has an exact, evidenced starting point.
- **The CAN/decompose ceiling (P13b/P12b) is real but requires the caller
  to already have extracted the structure** — there is no cheap NL-to-CAN
  or NL-to-candidate-projection bridge to point at; building either would be
  a substantial new capability (a structured-extraction reader), not a
  small connector.

**Verdict: NO-GO on building anything.** This document is the complete,
valid diagnostic outcome the task explicitly sanctions.

## 9. Regression

```
$ python3 -m pytest tests/test_solver_dispatch_migrated.py \
    tests/test_solve_gap_awareness_migrated.py \
    tests/test_problem_shape_migrated.py \
    tests/test_solver_math_boundary.py -q
...........................................                              [100%]
43 passed in 69.75s (0:01:09)
```

All four task-named suites green, including this rung's own 18 new
regression pins (`tests/test_solver_math_boundary.py`). Nothing in
`domains/solver_dispatch.py`, `domains/problem_shape.py`,
`domains/propositional_deduction.py`, or any seed file was modified by this
rung — the diff is purely additive (`scripts/solver_math_boundary_run.py`,
`tests/test_solver_math_boundary.py`, this doc, the PREREG doc), so no
wider composer/self-concern A/B sweep was run (mirroring every prior
rung's own reasoning for a purely-additive, non-toolbox-touching diff — see
`QUESTION_DRIVER_BUGFIX_AND_RECHECK_RESULTS.md` §1.5 for the identical
argument on an analogous diff shape). No Rust was touched; no `cargo build`
was needed.

## 10. What this document does NOT establish

1. **No new solver capability was built.** Every finding above is about
   EXISTING toolbox behaviour, discovered by pointing it at real problems —
   per the task's own framing, this is the complete, expected shape of the
   outcome, not a shortfall.
2. **The two named defects (ladder-ordering, silent numeric-copula
   mangling) are NOT fixed.** Both are pinned as regression tests
   (`tests/test_solver_math_boundary.py`) documenting CURRENT behaviour, so
   a future rung that fixes either has an exact starting point and a
   discriminating test that will flip from red-on-old-behaviour to
   green-on-new (both directions are pinned, e.g.
   `test_auto_mode_does_not_strip_leading_universal_quantifier` /
   `test_explicit_universal_mode_DOES_strip_the_quantifier`).
3. **15+3 problems is a mapping exercise, not a powered benchmark.** No
   statistical claim is made about the toolbox's overall math-problem
   accuracy; this is a boundary MAP (per the task's own explicit framing),
   not a score.
4. **Rung 3's data-sufficiency verdict (`QUESTION_DRIVER_BUGFIX_AND_
   RECHECK_RESULTS.md`'s NO-GO on Rungs 3.5/4) is unchanged** — §7 argues
   this explicitly, not merely asserts it: this battery's real, novel
   observations are all the SAME kind/shape as the existing 19-instance
   corpus, so neither blocker (a genuinely unclassified raw problem; two
   real signatures competing for recognition) is any closer to satisfied.
5. **`inference_generation.py`'s apply-and-answer pipeline was read and
   characterized (§5) but never exercised as part of this dispatcher** — it
   has no route through `qd_bind_resolver`, so no live call was made to it;
   its own correctness (elsewhere in the codebase, via the conversation
   pipeline) is not assessed here.
6. **The P1/P9/P11 silently-wrong resolves file ZERO self-improvement
   gaps** (§4) — this is a real, load-bearing limitation of the gap-filing
   mechanism (it can only detect `status=="walled"`, never semantic
   incorrectness) named here, not proposed as fixable within this task's
   scope (it would require a correctness oracle for open-ended NL that does
   not exist and is not sized here).

---

## Worktree / commit summary

- Worktree: `/home/matt/ozmadev/ocelot-worktrees/solver-math-boundary`
- Branch: `solver-math-boundary`
- Commits: `d34ddaf` (PREREG), `e6e983c` (battery script + 18 regression
  pins)
- **Not merged, not pushed to `main`.** `main`'s tip was re-checked fresh
  (`git log --oneline -1 main` == `40d0bdb`) before creating this worktree,
  per house discipline; no command in this rung touched `main` at any
  point. The orchestrator performs the merge.

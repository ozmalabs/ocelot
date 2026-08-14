# Pointing the solver dispatch toolbox at real math problems — PREREG

Base `main @ 40d0bdb` ("Add line summary: R1-R5 dyad, N1-N3 network, U0-U2
intent"), verified via `git log --oneline -1 main` immediately before writing
this document. This is a **DIAGNOSTIC/MAPPING task, not a build task** — the
user's own framing: point the already-built solver toolbox
(`domains/solver_dispatch.py`, seven `solve_*` resolvers wired through
`qd_bind_resolver`) at real math problems "so we can see where the edges
are." A finding of "here's precisely where and why it fails" is exactly as
valuable as a finding of "here's what unexpectedly works." No build is
pre-committed by this document.

Read in full before writing this: `QUESTION_DRIVER_SOLVER_DISPATCH_PREREG.md`,
`QUESTION_DRIVER_RUNG1_RESULTS.md`, `QUESTION_DRIVER_RUNG2_RESULTS.md`,
`QUESTION_DRIVER_RUNG3_RESULTS.md`, `QUESTION_DRIVER_BUGFIX_AND_RECHECK_
RESULTS.md`, plus `domains/solver_dispatch.py`, `domains/problem_shape.py`,
and `domains/propositional_deduction.py` directly (source, not summary).

---

## 1. What the toolbox actually is, grounded in the real code (not assumed)

The seven `solve_*` resolvers dispatch through the unchanged `qd_bind_resolver`
kind-string JOIN. Reading `domains/solver_dispatch.py` directly (not the prior
docs' summary of it) surfaces one fact that governs this entire investigation
and was not stated this plainly in any prior doc:

**Only `solve_deduction` accepts raw, unstructured text.** Its Goal-mint
helper (`mint_solve_deduction_goal`) takes a bare `statement: str`. Every
other resolver requires a PRE-BUILT graph object the caller must already have
constructed by hand before minting the Goal:

- `solve_can_relax` / `solve_can_exact` / `solve_can_bp` need a `targets_mt`
  edge to an already-built `Microtheory` with real `causal_influence` edges
  (a CAN belief network) — there is no NL-to-CAN-network ingestion path
  anywhere in this toolbox.
- `solve_reasoning_bridge` needs either a `targets_mt` edge (can_to_deduction)
  or plain `entity`/`attr` strings the caller already knows name real graph
  Concepts (deduction_to_can).
- `solve_analogical_promote` needs a `targets_correspondence` edge to an
  already-`record_directional_correspondence`'d `DirectionalCorrespondence`
  node.
- `solve_decompose` needs a `candidates` list of already-built coupling-graph
  projections staged in `solve_caps` (`problem_decomposition.project_*`
  output) — there is no NL-to-candidate-projection path either.

Consequence for this task: for a genuinely raw, novel word/logic/arithmetic
problem handed in as English text, `solve_deduction` is the ONLY plausible
front door. The other six are reachable only if the investigator manually
constructs the prerequisite graph object first (which this document's battery
does for the problems that plausibly warrant it — the CAN- and
decomposition-shaped ones — to also measure the toolbox's *ceiling*, not just
its naive floor).

## 2. A second load-bearing fact, read directly in `propositional_deduction.py`

`solve_deduction`'s three underlying parsers (`mint_logical_schema` /
`mint_universal_schema` / `mint_existential_premise`) only **MINT a held
implication/premise as background knowledge** (a `ShapeSignature{kind:
"knowledge_logical"|"knowledge_existential"}` node). None of them ingest a
SECOND fact (e.g., "Socrates is a man") and apply the implication to it, and
none of them ANSWER a query. The facility that actually does that —
`detect_implication_gaps` / `resolve_implication_gap` /
`detect_existential_gaps` / `resolve_existential_gap`
(`domains/inference_generation.py`) — exists in the codebase but is **not
one of the seven `solve_*` resolvers** and is not reachable through
`qd_bind_resolver` at all; it is invoked elsewhere (the ordinary conversation
comprehension pipeline), out of this dispatcher's reach entirely.

**Predicted consequence, stated before running anything:** a classic
two-premise syllogism ("All men are mortal. Socrates is a man. Is Socrates
mortal?") will NOT be answerable through `solve_deduction` even though it is
exactly the shape the facility sounds built for — the resolver can mint "all
men are mortal" as knowledge, but has no path to ingest "Socrates is a man"
as a fact or to conclude anything about Socrates. This is registered as a
prediction now, precisely so it can be confirmed or falsified live rather
than asserted after the fact.

## 3. Existing real math/benchmark fixtures — checked, none found

Grepped the tree for `GSM8K`, `gsm8k`, `math_qa`, `MathQA`, `arithmetic_bench`
and skimmed `tests/fixtures/` (`mbpp/sanitized-mbpp.json` is a real MBPP
program-synthesis fixture — CODE, not math word problems; no sibling math
fixture exists). `seeds/mathematics.json`, `seeds/logic_mathematical.json`,
`seeds/math_prose_constructions.json` are held DOMAIN KNOWLEDGE (concepts,
OEIS-style prose-to-formula constructions for `compute_grounding`'s own
separate reader), not a problem battery, and not part of the `solve_*`
dispatch surface — `compute_grounding.comprehend_computational_definition`
is a genuinely different subsystem (number-theoretic sequence definitions),
named here for completeness but out of scope: it has no route into
`qd_bind_resolver` either. **Verdict: no real math-benchmark fixture exists
in this repo. The battery is hand-built**, per the task's own fallback
instruction.

## 4. The battery — registered before running

15 problems, hand-constructed, spanning distinct shapes, each with a
PRE-REGISTERED expectation:

| # | shape | problem | expected `solve_*` attempt | prediction |
|---|---|---|---|---|
| 1 | arithmetic | "What is 17 * 23?" | `solve_deduction` (only text-accepting door) | wall — not a conditional/universal/existential statement; `parse_conditional` needs an `is_a`/`can` predication, arithmetic has none |
| 2 | arithmetic | "What is 144 divided by 12?" | `solve_deduction` | wall, same reason |
| 3 | algebra | "Solve for x: 2x + 3 = 11" | `solve_deduction` | wall, same reason |
| 4 | algebra | "Solve for x: 5x - 7 = 18" | `solve_deduction` | wall, same reason |
| 5 | logic, single conditional | "If X is a fish, X can swim." | `solve_deduction` | **resolve** — this is the toolbox's own documented worked example; mints a `knowledge_logical` schema |
| 6 | logic, bare universal | "A bird can fly." | `solve_deduction` (mode=auto, bare_universal form) | resolve — matches the documented bare-universal path |
| 7 | logic, explicit universal quantifier | "All philosophers are mortal." | `solve_deduction` | resolve as a `quantifier:"universal"` schema (mints "philosophers are mortal" as knowledge — NOT an answer about any specific philosopher, per Sec2) |
| 8 | logic, existential | "Some bird is a penguin." | `solve_deduction` | resolve as a `knowledge_existential` premise (witness unresolved, per module docstring) |
| 9 | logic, two-premise syllogism | "All men are mortal. Socrates is a man. Is Socrates mortal?" | `solve_deduction` | mints the universal premise ("all men are mortal") but CANNOT ingest "Socrates is a man" or answer the query — the Goal resolves on the FIRST parseable clause only, producing a plausible-looking `status:"resolved"` that does **not** actually answer the asked question — the sharpest silent-wrong-answer candidate in the whole battery, flagged in advance |
| 10 | word problem, multi-step arithmetic | "Sarah has 3 apples. She buys 2 more bags of 4 apples each. How many apples does she have now?" | `solve_deduction` | wall — no conditional/universal shape; this is arithmetic narrated in prose |
| 11 | word problem, geometry | "A rectangular garden is 5m by 3m. If you increase both sides by 2m, what is the new area?" | `solve_deduction` | wall, same reason |
| 12 | word problem, decomposition-shaped | "Three friends split a $60 bill evenly. If two of them each pay $5 extra to cover the third, how much does the third person pay?" | `solve_deduction` first (wall expected); then a HAND-BUILT `solve_decompose` attempt if a plausible coupling-graph projection can be constructed — predicted to also fail, because `problem_decomposition.py`'s candidate builders (`project_deduction_shared_attr`/`project_deduction_complete`) operate over `knowledge_logical` `ShapeSignature` nodes, not over arithmetic quantities; there is no real candidate to build for this problem, so this is predicted to be a genuine, cleanly-named non-fit rather than a forced attempt |
| 13 | CAN-shaped (real network, hand-built) | "Stress increases sleeplessness; sleeplessness decreases productivity. Given elevated stress, what happens to productivity?" | `solve_can_exact`/`solve_can_relax`/`solve_can_bp`, against a MANUALLY-BUILT small CAN Microtheory encoding the two stated causal edges (the NL sentence itself is not ingested — the investigator builds the network by hand, exactly mirroring how every existing CAN toolbox test builds its own network) | resolve, IF the network is built correctly — this measures the toolbox's real capability GIVEN the CAN structure already exists, not whether it can extract that structure from prose (it cannot, per Sec1) |
| 14 | combinatorial/search | "Find the smallest positive integer that leaves remainder 1 when divided by 2, 3, 4, 5, and 6." | `solve_deduction` | wall — no conditional shape; this is the deliberate MBPP/`ProgEval`-boundary probe (search over integers), included per the task's own instruction to test the boundary against `domains/prog_synthesis.py`'s different subsystem |
| 15 | permutation/combinatorics | "How many distinct ways can 3 different books be arranged on a shelf?" | `solve_deduction` | wall, same reason as #14 |

**Explicit prediction summary, before running:** `solve_deduction` resolves
problems 5–8 (single-fact conditional/universal/existential minting, the
toolbox's actual documented scope) and walls on every arithmetic/algebra/
search/permutation problem (1–4, 10, 11, 14, 15) with a clean honest residual
via `parse_conditional`'s own `None` return. Problem 9 is predicted to be
the one genuinely dangerous case: a `status:"resolved"` outcome that is
**not actually a correct answer to the asked question** — this is the
`solve_deduction` boundary the task asks to characterize precisely ("single-
step syllogism? chained inference?"), and the prediction is that it does
**neither**: it only mints isolated background knowledge, never applies it.
Problem 12 is predicted to be an honest non-fit for `solve_decompose` (no
real candidate structure to build). Problem 13 is predicted to resolve only
because the CAN network is hand-built by the investigator, not derived from
the sentence — this is registered explicitly so a "success" there is not
misread as "the toolbox understood the sentence."

## 5. Rung 2 (gap-filing) and Rung 3 (`ProblemShape`) — what this battery adds

Every wall is expected to hit `note_solve_exhausted_gap`
(`seeds/gap_awareness.json`) and file a `SelfConcern{kind:"solve_failure"}` —
this battery is a genuinely novel-input test of that mechanism (Rung 2's own
battery was toolbox-authored test fixtures; this is the first REAL,
independently-authored problem set to exercise it). Expected: one gap per
DISTINCT `gap_key` (statement text), no cross-problem dedup collisions (each
statement's text differs).

Every `solve_deduction` Goal (resolved or walled) will additionally be run
through `domains.problem_shape.observe()` (Rung 3's real, live codebook) to
see whether these 15 new, genuinely novel real observations recognize
against the existing `deduction_shape` entry or produce anything new. Per
Rung 3's own finding that `ProblemShape`'s five axes are structural
(`has_statement`/`has_targets_mt`/... — never message CONTENT), the
prediction is that every `solve_deduction` Goal in this battery — resolved
or walled — recognizes as the SAME `deduction_shape` regardless of whether
the underlying parse succeeded, because `ProblemShape` discriminates by
which ATTRS/EDGES a Goal carries (all of them carry `statement`), not by
outcome. This is registered as a prediction to check whether it changes
Rung 3's own "no real raw-problem corpus" finding (§1 of that RESULTS doc)
— predicted NO: `ProblemShape` still only recognizes an already-`kind`-typed
Goal's structure, never decides the kind in the first place, so this battery
does not supply the missing pre-mint recognition corpus either, only more
post-mint recognition instances of a shape already seeded.

## 6. What this document does NOT establish (registered in advance)

1. Whether a cheap 8th `solve_*` connector exists is NOT decided here — §1's
   own finding (no NL-to-CAN, no NL-to-candidate-projection path exists) and
   the absence of any held arithmetic-expression-evaluation primitive
   (checked: no `eval_arithmetic`/`parse_arithmetic` function exists anywhere
   in `domains/` or `runners/`) make an honest cheap bridge for arithmetic/
   algebra look UNLIKELY, but this is a prediction to be confirmed live in
   the RESULTS doc, not asserted here.
2. This is not a claim that 15 problems is a statistically powered sample —
   it is a mapping exercise (the task's own framing), not a benchmark score.
3. Problem 13's CAN network is hand-built by the investigator, not extracted
   from the sentence by any part of this toolbox — flagged so a resolve
   there is never misread as NL-to-CAN capability.
4. No claim is made about the broader `inference_generation.py`
   apply-and-answer pipeline's own correctness — it is out of scope for
   this dispatcher (§2) and is only referenced to characterize the boundary,
   never exercised as a `solve_*` path.

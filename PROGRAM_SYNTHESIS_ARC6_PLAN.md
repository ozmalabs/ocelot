# ARC 6 — ONE MATHEMATICS, ONE PROGRAM: integrating the math faculty and the synthesis pipeline

**Date:** 2026-08-01
**Launches from:** arc 5 (exact-first rung, orbit/decomposition moves, rational
domain, the float and FPGA measurements) and `RESEARCH_MATH_CAPABILITY_AUDIT.md`.
**Status:** PLAN.

## 0. The gap, measured not asserted

The math-capability audit established by **import-graph grep, zero
cross-references in either direction**, that this repo contains three disjoint
systems:

1. `seeds/mathematics.json` — 117 prose concepts, pure recitation, feeding the
   code-authoring cortex rather than problem-solving.
2. **A real computation tower** — `domains/reason.py`, `comprehend_theorem.py`,
   `compute_grounding.py`, nine `construct_compute_*` modules, `oeis_local.py`:
   matrix rank, Smith normal form, homology, Steenrod squares, spin bordism,
   hook-length representation theory, exact enumeration. Live-reproduced: 8/8
   OEIS sequences extracted from prose and verified against a real dump; the
   Aztec-dominoes conviction certified by two independent routes against an
   official key that is provably wrong. **Five wrong HLE answer keys caught.**
3. **The synthesis pipeline** — `seeds/program_synthesis.json` v1.10.0 (70
   rules), `prog_synthesis.py`, `prog_exact.py`, `prog_moves.py`, hub IR,
   `ProgEval`, `SynthEnumerate`, the verdict layer. **It imports nothing from
   (1) or (2).**

Math answers by *composing held primitives into one Term-tree* — derivation.
Synthesis answers by *enumerating and rejecting candidates against rows* —
search. Same substrate, same mathematics underneath, never wired together.

**Arc 5's own evidence that this is the right seam:** every win in the code
domain came from a *mathematical* move — group orbit, dimension induction,
exact rationals, factorisation — and never from software-engineering knowledge.
The synthesis pipeline has been rediscovering, badly and by hand, capabilities
the tower already holds and verifies.

## 1. The five seams, ranked by measured expected value

### Seam A — math kernels as `ProgEval` oracles *(highest value, lowest risk)*
`ProgEval`'s `CallExtern` already takes a declared-oracle table and traps
honestly on anything undeclared. The tower is a large, exact, **already
verified** op inventory. Registering its kernels as oracles raises the
enumerator's *reach* without touching its search.

Why it should pay: `PROGRAM_SYNTHESIS_ARC4_S4_NOTES.md` classified the 60/85
unreached tasks as folds, combinatorics, number theory, and sqrt/trig
composites — which is largely what the tower does. And this is **operator
transfer, not content**: a kernel is a mechanism, and operator transfer is the
one move that has worked every time here.

**Correction to an earlier framing in this document (2026-08-01, from the
author).** An earlier draft called the tower "a spike, not a plateau" and
treated its 1.9% HLE coverage as a limitation bounding this seam. That is
wrong. **The HLE work was an existence proof, and its coverage is the
deliberate scope of one.** Extending coverage requires importing a large body
of complex mathematical reasoning — content — which was never needed to
demonstrate possibility. Capability and coverage are different jobs; only
capability was the question.

What that work actually established is not a percentage but this: **five wrong
official HLE answer keys caught**, one certified by two independent routes. A
wrong answer key cannot be caught by pattern-matching a benchmark — only by
genuinely deriving and then trusting the derivation over the label. That is a
stronger proof than any score, because a score is compatible with fitting and
catching the grader's error is not.

**Consequence for this seam, and it inverts the earlier reading:** a small
measured A-ceiling does NOT mean "the approach does not reach here." It means
"the return is proportional to kernels imported, and here is the import list."
Kernel import is a bounded mechanical job, not a research risk. That makes
Seam A *more* attractive than the earlier draft implied, and makes M0's job
producing an import list rather than a go/no-go verdict.

### Seam B — `extract_function` retargeted to hub IR
`construction_grammar.extract_function` + `comprehend_recursive` is already a
**closed propose-from-NL → verify-by-execution loop**, proven against real OEIS
ground truth, using order-N compositional slot recursion — structurally the same
move as descent's hole-filling. It emits into `compute_grounding`'s formula
surface. Retarget it to emit hub IR and it becomes a proposal rung whose
verifier is `ProgEval` and the standing verdict layer.

### Seam C — math `ShapeSignature`s as the recognition codebook
`PROGRAM_SYNTHESIS_ARC5_SHAPE_PROBE.md` measured **0 genuine algorithmic
recognitions**, root-caused to `shape_vocabulary.json` being systems-flavoured
(scheduler, memory_store, gating). Meanwhile `seeds/math_capability_shapes.json`
holds **17 `ShapeSignature{kind:"math"}` with real relational signatures**.
Point `RecogniseShape` at the math codebook for synthesis goals.

**This seam is CONTENT and carries the fourth-null rule.** Five content bets
have nulled. It is included because the claimed difference is testable: a shape
is not a proposal to be tried but a representation a program is *rendered from*,
and rendering measured 277 candidates against unreachable-at-any-size.

### Seam D — `comprehend_theorem` → `RequiredProperty` *(highest ceiling, least mature)*
The synthesis wall is provable: with 2–4 rows the version space is enormous and
excluding a candidate yields **zero bits** (Mitchell; Angluin's L*). Only more
data or a hypothesis-space restriction shrinks it. `comprehend_theorem` already
turns prose into a checkable `ImplicationClause` — a *property*, which is
exactly a hypothesis-space restriction. Wiring it to mint `RequiredProperty`
facts the moves' refutation/constraint layer consumes is the piece the math
audit named as missing piece (1).

### Seam E — shared exact numbers *(mostly already true)*
The rational domain landed today; the tower is exact. Verify they agree at the
boundary rather than assume it.

## 2. Hypotheses

- **HM1 (Seam A):** registering tower kernels as declared oracles converts
  tasks in the 60/85 unreached classes, CI-uncertain but **paired-id exact**,
  with zero coincidental fits.
- **HM2 (Seam B):** `extract_function` retargeted to hub IR converts tasks on
  the compositional-definitional subset, verified by `ProgEval` + held-out +
  constructed witness.
- **HM3 (Seam C):** math shape recognition yields a **non-zero** genuine
  algorithmic recognition rate (the probe measured 0) *and* those recognitions
  select correct relaxations. **Carries the fourth-null rule.**
- **HM4 (Seam D):** a theorem-derived property refutes at least one trap that
  neither rows nor structural detectors catch — i.e. it reaches into the
  measured **36/76 honest residual**.
- **Registered null readings.** If HM1 nulls, the tower's coverage does not
  overlap this corpus and that is a statement about MBPP, not about the tower.
  If HM3 nulls, the acquisition line ends with the proposal line — six bets,
  and the conclusion is that structures must be supplied, with the ceiling set
  by how many a person writes.

## 3. Phases — measure the ceiling before building, every time

*(The discipline that killed S3 before it was built, re-aimed S4, and corrected
HA2's ceiling upward.)*

### M0 — the prereg + four ceiling probes (build nothing)
- **A-ceiling — an IMPORT LIST, not a go/no-go.** For each unreached task
  class: (i) does a tower kernel already exist that expresses it (id lists);
  and (ii) where none exists, **what kernel would be needed, and what does
  importing it cost?** A low (i) is not a negative result — it is the
  specification for (ii). Rank the missing kernels by tasks-unlocked per unit
  of import work.
- **B-ceiling:** how many MBPP prompts are within `extract_function`'s clause
  grammar *after* retargeting — and how far does its vocabulary (10 clauses,
  5 member forms, 4 aggregators, 4 filters) actually reach?
- **C-ceiling:** run `RecogniseShape` against the **math** codebook on all 257
  test prompts. The probe measured 0 with the systems vocabulary; what does the
  math vocabulary give, and are the hits *genuine* (not substring collisions —
  the probe's 23 hits were all spurious)?
- **D-ceiling:** of the 36/76 honest-residual traps, how many admit a
  `comprehend_theorem`-expressible property that refutes them?
- `PROGRAM_SYNTHESIS_ARC6_PREREG.md` with every bar derived from these numbers.
  **Arc 5 had no prereg; this one does.**

### M1 — Seam A (oracles). M2 — Seam B (retarget). M3 — Seam C (recognition). M4 — Seam D (properties).
Each built only if its ceiling justifies it, each landing as **rules + a
mechanical adapter**, each verified by the **unchanged** verdict layer, each
reporting paired id lists with constructed witnesses.

### M5 — powered endgame
Arms: FULL / NO-ORACLES / NO-RECOGNITION / arc-5 continuity. Both denominators,
Wilson CIs, paired attribution per id, mechanism-first reporting (§A4).

## 4. Boundaries and risks

- **Contamination:** OEIS and HLE data must never enter MBPP evaluation. The
  list-gate discipline applies from M0.
- **The decoy tax is the live risk.** A math oracle that *almost* fits proposes
  a plausible wrong program. Every proposal from every seam enters the existing
  **execution screen** and the structural detectors before it may spend an
  attempt. No seam may bypass the verdict layer.
- **A fifth coincidental fit.** Four have been caught (two in arc 4, two in
  arc 5 — the most recent by *constructed witness*, not held-out rows). Every
  claimed conversion needs a witness.
- **Seam A's ceiling is an import cost, not a capability limit.** The tower's
  1.9% HLE coverage is the deliberate scope of an existence proof (see §1,
  Seam A). If current kernels cover little of MBPP's unreached classes, the
  finding is an import list with a cost estimate — not a reason to abandon the
  seam. The genuine risk here is a *scoping* one: importing kernels
  indefinitely is unbounded work, so M0 must rank by tasks-unlocked per unit
  of import and the arc must take only the top of that ranking.
- **Operator vs content, kept explicit:** Seams A, B, D are operator/mechanism
  transfer. Seam C is content and carries the null rule. Do not let the four
  blur into one claim.

## 5. Why this is the right next arc

The synthesis pipeline has been re-deriving mathematics it does not know it
already owns — by hand, badly, one family at a time. The tower holds verified
exact kernels, an NL→formal→verify loop proven against external ground truth,
and real algorithmic shape signatures. They are the same mathematics, in the
same substrate, in the same process, connected by nothing.

The measured claim to settle: **does an embodied mathematics compound when its
parts are connected** — or is the tower a spike whose reach simply does not
overlap this corpus? Either answer is worth the arc, and only one of them is a
disappointment.

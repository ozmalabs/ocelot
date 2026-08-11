# PROGRAM SYNTHESIS ARC 3 — RETRIEVAL-SHAPED PROPOSAL

**Date:** 2026-08-01
**Launches from:** arc 2 complete (Q5 `2a1d83ce94`). This arc IS the fork arc 2's
prereg registered on a third HQ3 null: *"the architecture's proposal grain is
wrong, not its diet — retrieval-shaped proposal (decode against WHOLE held
train programs, not chunk shapes)."*

## 0. Why retrieval, stated from the measurements

Three powered nulls (H6, H7c, HQ3) and one decoy-tax mechanism all say the same
thing: **abstracting held programs into shape-grain codebook entries destroys
the information that made them useful, and the abstracted residue actively
misleads** (Q5: FULL's passes a strict subset of stripped's; every
`gapped:exhausted` row chunk-cued — a wrong proposal spends the budget before
the enumerator runs). Meanwhile every mechanism that keeps programs WHOLE and
verifies by execution works flawlessly.

So: stop quantizing the exemplars. Keep the 120 train programs whole, retrieve
the nearest by paired-prompt + signature + row-shape similarity, and ADAPT —
run-as-is, permute args, delta a constant/operator, or use the retrieved
program AS the descent skeleton with the failing statement re-opened (the
existing repair machinery, unchanged). This is case-based reasoning on the
substrate's own terms: TransformDecode's law ("a transform is a quantum delta
on a dimension") applied at program grain, and it is also the more LLM-like
design — LLMs interpolate stored exemplars; they do not consult an abstracted
grammar.

**The decoy-tax fix is architectural and general:** every proposal (retrieved
OR codebook) gets a budget-free EXECUTION SCREEN on the revealed rows before it
may consume an attempt. Screening is one ProgEval call — nearly free — and
Q5 measured exactly what not having it costs (24 exhausted rows).

## 1. Hypotheses

- **HR1 (the fourth try at making held content pay, now extensional):**
  FULL-R − NO-RETRIEVAL on MBPP test (PRIMARY protocol) CI-separated > 0.
  The bar is set by R0's oracle ceiling, not ambition.
- **HR2 (decoy tax eliminated):** the cued `gapped:exhausted` class → ~0 under
  universal screening; attempts-per-accept does not rise.
- **HR3 (non-regression):** internal battery + arc-2 endgame continuity rows
  green/unchanged where frozen.
- Null readings: if HR1 nulls even at the oracle ceiling's grain, the honest
  conclusion is that 120 exemplars are below retrieval's useful density — the
  next lever is corpus scale (more paired exemplars), not another proposal
  mechanism; register it now.

## 2. Phases

### R0 — The oracle ceiling (measure before building)
For every MBPP test task: does there EXIST a train program that passes its
revealed rows (a) as-is, (b) under arg permutation, (c) under a bounded
constant/operator delta (enumerate the delta at the divergent leaf, exclude-
powered), (d) as a skeleton with ONE re-opened hole solved from derived rows?
Pure sweep — train programs run against test rows is evaluation-time use,
contamination-legal (rule re-stated in the prereg). Output: the ceiling per
adaptation rung, the per-task nearest-oracle table, and the prereg with HR1's
bar derived from rung (a)-(c) mass (rung (d) discounted by repair's measured
conversion rate). Twin-run determinism; artifact is the list.

### R1 — The exemplar store + ranked retrieval + universal screen
Train programs as whole graph-resident Exemplar nodes (IR subgraph + paired
prompt facts + signature facts + provenance). Ranking = mechanical scoring
facts (prompt-token tf-idf overlap, signature type match, row-shape match);
SELECTION is a rule (Argmax over recorded scores, top-k bounded). The
**screening lane**: a rule-guarded pre-attempt phase — every candidate
(retrieved or codebook) is ProgEval'd on revealed rows; only a screen-passing
candidate may occupy an attempt; screen results are facts. Codebook/chunk
proposals enter the same lane (the R3 generalization folded in here — one
lane, not two).

### R2 — The adaptation ladder (Occam, rules)
exact-pass → arg-permutation (bounded, signature-compatible only) →
leaf-delta (constant/operator at the FIRST divergent position, exclude-powered
enumerate, bounded) → retrieved-as-skeleton (the repair machinery verbatim:
localize on the retrieved program's trace, re-open one hole, derived rows) →
fall through to the arc-2 stack unchanged. Every rung a rule; integer budgets;
screen before spend at every rung; provenance records which exemplar and which
rung served each accept.

### R3 — Powered endgame + arc summary
Arms: FULL-R / NO-RETRIEVAL (arc-2 stack, screening ON — so HR1 isolates
retrieval, not the screen; the screen's own effect is measured by a third arm
NO-SCREEN diagnostic if cheap) / RETRIEVAL-ONLY (no enumerate fallback —
attribution). HR1/HR2/HR3 verdicts, migration matrix vs Q5, both denominators,
protocol unchanged (PRIMARY; OFFICIAL row for comparability). Arc summary in
the standing pattern.

## 3. Boundaries (unchanged)
Decisions in rules/Terms; adapters mechanical; no Rust unless a genuine engine
wall (none anticipated — ProgEval/exclude/TransformDecode/repair all exist);
frozen artifacts append-only; contamination list-gate green at every phase;
every claim carries its denominator.

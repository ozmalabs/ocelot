# Harvest Qwen3 into Jabberwock — Plan A — RESULTS

**Blocks**: 330000–333000. Pre-reg: `HARVEST_QWEN38_PREREG.md`. Plan B (a
`qwen3_5` numpy MECHANISM reader) deferred:
`HARVEST_QWEN38_PLAN_B_MECHANISM_READER.md`.

**Plan A complete. A CURRENT model's (empero-ai/Qwen3.8-4B-Distill) relational
KNOWLEDGE was extracted into a native CAN graph seed and ingested into the
entity's own grounding as a CALIBRATED, PROVENANCED witness. The entity gains
capability — it derives held-out entailment it could not before — while the
existing epistemic machinery keeps the LLM a corroborate-before-assert source it
can OUTGROW, not an oracle it distills. The harvest is scoped to the tier the
model EARNED in calibration (knowledge); concept and process were not earned and
were not reaped.**

## The four blocks

| block | what | result |
|---|---|---|
| 330 | bring-up + calibration | HFForward shim runs the extraction arc on the hybrid `qwen3_5` model; knowledge is-a **1.00** held-out (0 self-loops), concept AUC 0.59 ≈ control, process control-FAILED |
| 331 | seed `qwen3` as a source | `generative_source → source` + `qwen3` concept; epistemic band **0.50 self_published**, strictly below Wikipedia's 0.90 attested |
| 332 | harvest knowledge at scale | 59 is-a edges, held-out transitive entailment **1.00** (65/65), shuffle 0.54; `seeds/generated/qwen3_reaped_knowledge.json`, every edge `source: qwen3` + trust |
| 333 | ingest + verify | capability delta + provenance + outgrow-the-witness guard, all on the substrate (no LLM at query) |

## Block 333 — the capability delta and the guard

1. **Capability delta.** A held-out ≥2-hop entailment ("poodle → animal") that
   the BARE graph cannot answer becomes answerable AFTER ingesting the reaped
   qwen3 edges — the substrate DERIVES it by traversal (and it is NOT a stored
   edge; the anti-lookup check holds). The entity can now reason over relations
   it did not hold.
2. **Provenance.** The answer is stamped `source=qwen3, status=self_published,
   epistemic_weight=0.50`, read off the held `qwen3` concept (not a Python
   constant); every reaped edge carries `source: qwen3` + trust.
3. **Outgrow-the-witness (the Goodhart guard).** A qwen3-only claim (0.50) sits
   BELOW the fusion solo-assert bar (S ≥ 0.8), so it cannot assert alone — it
   must be corroborated. An attested source (wikipedia, 0.90) clears the bar and
   OUTWEIGHS a contrary qwen3 edge (0.90 > 0.50): the entity overrides a wrong
   reaped edge. The LLM is a witness the entity can outgrow.

## Why this is the right integration (and not distillation)

The entity already holds an understanding of what a SOURCE is
(`source_provenance.py` + the source taxonomy in `communication_concepts.json`),
with genre conventions and an epistemic weight distinct from a self-derived
fact. An LLM is simply a NEW source in that taxonomy — a `generative_source`, a
confident crowd-compression — seeded at a calibrated band below an attested
reference. Reaped content enters the SAME grounding/fusion path as Wikipedia or
ConceptNet: it widens the entity's witness pool (more relations to verify) while
the trust weights, the "corroborate before assert" bar, and the demotion-on-
contradiction keep it a witness the entity can outgrow. The capability increase
is real; the autopoiesis is intact — the LLM proposes, the entity disposes.

## Honest scope / deferred

- **KNOWLEDGE only.** Concept (opposite) and process (negate) did NOT earn trust
  in the block-330 calibration (AUC 0.59 ≈ control; process control-failed), so
  they were NOT reaped — reaping an unearned tier is exactly what the calibrated
  source band exists to prevent. Named follow-ups: a better concept
  representation (layer/template, or the crisp substrate negative-coupling
  signature from block 328), a tighter process readout (output-config valence,
  or a non-negation process).
- **Flat-band, not temporal.** `qwen3` is seeded with a flat `reliability` band.
  The richer design — dated calibration EVENTS composed into the band via
  `source_provenance.context_for` — needs the `communication_concepts` INSTALLER
  (materialises a `timeline` into `SourceEvent` nodes) and the
  `SourceEvent`/`has_event` grammar, NEITHER present in this checkout. Deferred +
  documented, not faked.
- **Mechanism arc (native-graph, 318-326) deferred for this model.** The numpy
  reader does not support `qwen3_5`; Plan B scopes that separate effort.

## Anti-faking / method

- Every tier: elicitation vs held-out (entailment / transfer / application)
  disjoint; controls (shuffle / random / identity) reported; NO LLM at the
  substrate-query step; provenance + trust on every reaped edge.
- The mixed calibration (knowledge earned, concept/process not) is reported
  plainly and ENFORCED (only the earned tier is reaped).
- **default == today**: `.so` md5 stays `7efe75eba05b006cafd15dbb4b7da246`;
  protected CAN internals untouched; `communication_concepts.json` /
  `source_provenance.py` are non-protected in-tree; reaped seed in
  `seeds/generated/` (tracked); model + venv under `/applications`, NOT
  committed.

## Where this lands the whole line of work

Two arcs now stand:
- **Mechanism recovery** (318-326): the LLM's FFN structure recovers to a native
  multi-layer graph that composes on the substrate's own BP, residual a named
  discretisation constant.
- **Content extraction** (327-329) + **entity integration** (330-333): the LLM's
  knowledge/concepts/processes extract into native CAN seeds, and — for the
  earned knowledge tier — a CURRENT model's content is harvested and ingested
  into Jabberwock as a calibrated, provenanced, outgrowable source that measurably
  increases the entity's capability.

The user's framing is delivered: an LLM turned into a graph-cognition contribution
the entity reasons over on its own substrate, weighed as a witness it can
outgrow — reaped data increasing the entity's capability without collapsing its
autopoiesis into distillation.

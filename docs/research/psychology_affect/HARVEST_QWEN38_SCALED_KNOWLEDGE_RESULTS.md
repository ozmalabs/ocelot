# Harvest Qwen3.8 — Earned Knowledge Tier at Scale (block 336000)

## What this run does

Extracts the **earned** knowledge tier (is-a) at scale from the `qwen3` source
(`empero-ai/Qwen3.8-4B-Distill`), using the batched elicitation from block 335.
Only is-a is harvested: block 330 calibration EARNED it (held-out transitive
1.00, shuffle 0.54) while concept (opposite, AUC 0.59) and process (negate,
control failed) did not — harvesting those would reap unearned tiers.

- Taxonomy: **186 chains, 213 subjects, 217 candidate hypernyms** (multi-domain:
  living things, plants, materials, artifacts, food, body).
- Elicitation: **213 subjects in 64.9 s = 11,813 edges/hr** (batched bs=32),
  matching the block-335 projection.
- Extracted: **202 is-a edges** (11 self-loops dropped), 210 nodes.
- Query time: **pure substrate, no LLM** (elicitation is oracle-only).

## Results (measured)

| metric | value | reading |
|---|---|---|
| adjacent elicitation vs gold | **0.859** (183/213) | LLM-source fidelity at scale |
| held-out transitive accuracy | **1.000** (285/285 pos, 285/285 neg) | substrate derives the closure of the graph it was given |
| direct-edge-only baseline (pos recall) | **0.000** | traversal, not lookup, carries the entailment |
| shuffled-graph control | **0.498** | entailment collapses to chance — structure, not node set, carries it |

The two controls both land: the direct-edge baseline recalls **none** of the
dist≥2 held-out pairs (so the 1.00 is genuine multi-hop inference, not stored
lookup), and the shuffled graph collapses to chance (so it is the real is-a
structure doing the work). This reproduces block 332's finding at ~3× the
held-out scale and adds the direct-edge baseline block 332 did not run.

## The honest finding: fidelity, not entailment, is where the noise lives

The substrate entails the closure of *whatever* graph it holds **perfectly**
(1.00). The noise is upstream, in the **86% adjacent fidelity** — the LLM source
is not a clean oracle at scale. Breaking down the 30 gold-disagreements + 11
self-loops:

- **True but skip-level** (~half): `dog→animal`, `cat→animal`, `frog→animal`,
  `sunflower→plant`, `bean→plant` — still true is-a edges, just not the immediate
  parent in the (arbitrary) gold chain. The disagreement is with gold
  granularity, not the model.
- **Defensible / arguable**: `axolotl→salamander`, `mallet→hammer`, `sedan→car`,
  `toe→foot`, `pea→fruit` (botanically true).
- **Genuine errors**: `boa→fish`, `ash→rock`, `marble→object`, `table→object`.
- **Self-loops (11)**: e.g. "A boxer is a kind of boxer" — the constrained read
  degenerating; correctly detected and dropped.

## Why this is safe to ingest anyway

Every reaped edge carries `source=qwen3`, `trust=0.5` — the calibrated
self-published band (block 331/334), **below** an attested reference and under
**corroborate-before-assert**. So the genuine errors (`boa→fish`, `ash→rock`)
**cannot assert alone**: they need corroboration, and the agent's own witnesses
override/demote them (the block-333 outgrow-the-witness guard). The harvest does
not launder LLM confidence into fact — it enters as a weighted witness whose
per-edge trust is exactly the calibration this tier earned.

## Scaling read-through

The forward-pass rate (11,813 edges/hr) held as projected — throughput is not the
binding cost. The binding cost is **fidelity per relation**: 86% adjacent
correctness on a single well-behaved relation (is-a) with a constrained candidate
set. Noisier relations (part-of, located-in) will be lower and need their own
held-out control before their edges earn the band. "Extract everything" remains
gated by per-relation re-calibration, not wall-clock.

## Artifacts

- `scripts/llm_harvest_knowledge_scaled.py` (the run)
- `seeds/generated/qwen3_reaped_knowledge_scaled.json` (202 edges, source=qwen3,
  trust=0.5, full calibration block)

## Guardrails

- `.so` md5 unchanged: `7efe75eba05b006cafd15dbb4b7da246` (python/JSON only).
- Protected READ-ONLY files untouched.
- Model/venv under `/applications` not committed; run log under `var/` (ignored).
- Committed block-336 only, add-by-name.

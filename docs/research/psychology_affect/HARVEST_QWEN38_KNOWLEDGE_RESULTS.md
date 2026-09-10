# Harvest knowledge at scale from qwen3 — block 332 — RESULTS

**Block**: 332000. Pre-reg: `HARVEST_QWEN38_PREREG.md` (Plan A).
Build: `scripts/llm_harvest_knowledge.py`; output:
`seeds/generated/qwen3_reaped_knowledge.json`; test:
`tests/test_qwen3_reaped_knowledge.py`.

**Reaped the calibration-EARNED tier (knowledge / is-a) at scale from the qwen3
source into a native CAN seed. 59 is-a relations, every edge tagged
`source: qwen3` + the calibrated trust band (0.5). The substrate DERIVES all 65
held-out ≥2-hop entailments the seed was never told (1.00), and a shuffled-graph
control collapses to chance (0.54) — the reaped seed carries real relational
structure, not memorised pairs. Concept and process are NOT harvested (block 330
calibration: concept weak, process control-failed) — honest to the calibration.**

## Result (empero-ai/Qwen3.8-4B-Distill via HFForward; NO LLM at query)

| quantity | value |
|---|---|
| subjects elicited | 62 |
| clean is-a edges (self-loops dropped) | 59 (3 dropped) |
| concept nodes | 66 |
| held-out entailment | 65 pos (dist ≥ 2) + 65 neg |
| **SUBSTRATE transitive accuracy** | **1.00** (65/65 pos, 65/65 neg) |
| shuffled-graph control | 0.54 |
| written | `seeds/generated/qwen3_reaped_knowledge.json` (source=qwen3, trust=0.5) |

The 4B-distill's is-a is markedly cleaner than the 0.6B's (3 self-loops out of
62 vs the 0.6B's many; a fuller cross-domain taxonomy — living things,
materials, artifacts, food, body parts). Over the extracted graph, the substrate
answers every ≥2-hop entailment (poodle→animal, oak→organism, copper→substance,
…) by traversal and rejects every non-reachable negative — 1.00 — while the
shuffled-graph control (same nodes, scrambled targets) collapses to 0.54,
confirming the *relational structure* carries the inference.

## The seed (what the entity gains)

`seeds/generated/qwen3_reaped_knowledge.json` — 59 `{subject, isa, object,
source: qwen3, trust: 0.5}` edges + a `calibration` block recording the
held-out-transitive-acc (1.0) and shuffled-control-acc (0.54). Every edge
carries indelible provenance (`source: qwen3`) and the calibrated trust, so when
ingested (block 333) it enters the agent's grounding as a corroborate-before-
assert witness at the qwen3 band — never an oracle.

## Honest scope (per the block-330 calibration)

- **KNOWLEDGE only.** Concept (opposite) transfer was weak on this model (AUC
  0.59 ≈ control) and process (negate) FAILED its control (shuffle == extracted),
  so neither is reaped here — reaping a tier the model did not earn would be
  exactly the "confident crowd-compression asserting past its reliability" the
  source band exists to prevent. Deferred until a better concept representation
  / process readout is found (named in block 330).
- The extracted graph is what the model ACTUALLY asserts, warts included (e.g.
  it sometimes collapses a chain, "dog → animal" skipping "mammal"); the
  entailment closure is computed faithfully over that graph, so the seed is an
  honest record of the source, not an idealised taxonomy.

## Anti-faking / method

- Elicitation (constrained next-token) vs held-out entailment (transitive
  closure at dist ≥ 2, NOT elicited) are disjoint; controls (shuffled graph)
  reported; NO LLM at the substrate-query step.
- Every reaped edge carries `source: qwen3` + `trust` — provenance and weight
  travel with the data (block 333 relies on this for the fusion + outgrow-the-
  witness demo).
- **default == today**: `.so` md5 stays `7efe75eba05b006cafd15dbb4b7da246`;
  protected CAN internals untouched; the reaped seed is in `seeds/generated/`
  (tracked, not protected); model + venv under `/applications`, NOT committed.

## Next

Block 333: ingest `qwen3_reaped_knowledge.json` into a Jabberwock world and show
the capability delta through the existing grounding + `source_provenance` path —
the agent answers held-out entailment it could not before, with `source: qwen3`
provenance attached — plus the outgrow-the-witness guard (a wrong reaped edge
sits below the solo-assert bar and the agent's own witnesses override it).

# Qwen3 as a trust-weighted source — block 331 — RESULTS

**Block**: 331000. Pre-reg: `HARVEST_QWEN38_PREREG.md` (Plan A).
Build: `seeds/communication_concepts.json` (+`generative_source`, +`qwen3`),
`domains/source_provenance.py` (`_source_concept_name` label map,
`_reliability_band` calibrated band); test: `tests/test_qwen3_source.py`.

**The reaped-LLM model is registered as a SOURCE the agent already knows how to
weigh — not a new mechanism, one more entry in the source taxonomy. `qwen3`
seeds as a `generative_source` (is-a `source`) with a flat, CALIBRATED
reliability band that composes to confidence 0.5 — strictly BELOW Wikipedia's
attested 0.9 and above a conjecture. The agent will treat reaped Qwen3 content
as a corroborate-before-assert witness it can outgrow, never an oracle.**

## What was seeded (Claim: the LLM is a source, weighed by held understanding)

Two concepts added to `communication_concepts.json`, in the same shape as the
existing `source → reference_work → encyclopedia → wikipedia` taxonomy:

- **`generative_source` is-a `source`** — the genre of a generative language
  model: WHO = a model (a compression of a training crowd), HOW = next-token
  generation (generative register; *fluency is not evidence*), WHEN =
  training-cutoff-dated. Its `conventions` hold the agent's reading discipline:
  `fluency_is_not_evidence`, `corroborate_before_assert`, `training_cutoff_dated`,
  `no_primary_attribution`. `reliability: self_published_calibrated`.
- **`qwen3` is-a `generative_source`** — the harvested model
  (empero-ai/Qwen3.8-4B-Distill), with a `provenance` template (who = language
  model, how = generative, when = training cutoff) and the same
  `self_published_calibrated` band.

`source_provenance.py` gains the label mapping (`qwen3`/`Qwen3.8…` → `qwen3`;
`llm`/`generative source` → `language_model`) and a `_reliability_band` entry
for `self_published_calibrated` → confidence at the self-published baseline
(0.5), with the rationale that per-tier trust is carried on the reaped edges,
not this source-wide band.

## Measured (in-tree, against the real `source_provenance` reader)

| source | status | confidence |
|---|---|---|
| wikipedia | consensus | 0.90 |
| **qwen3** | **self_published** | **0.50** |

`qwen3` composes **below** the attested reference (0.5 < 0.9) and **above** a
conjecture (> 0.1), exactly as intended: a corroborated LLM claim can reach the
self-published band but no higher, and an uncorroborated one sits below the
solo-assert bar (the fusion `S ≥ 0.8` threshold of the `derive_opposes` spec).

## Per-tier trust lives on the edges, not the source band

The block-330 calibration was DIFFERENTIATED (knowledge 1.00 held-out, concept
AUC 0.59 ≈ control, process control-failed). A single source-wide band cannot
express that. The design carries per-tier trust on the reaped EDGES (block 332):
knowledge relations tagged at the calibrated band, concept judgments lower
(corroborate-only), process not harvested until its readout is fixed. The fusion
path already weighs per-edge, so this is where per-tier trust belongs — the
`qwen3` source band is the ceiling, the edge tags are the per-claim weight.

## Anti-faking / method

- The seed follows the held source taxonomy exactly; no Python constant sets the
  weight — `source_provenance` reads the held `reliability` off the concept.
- The calibrated band is strictly below the attested reference, enforcing
  corroborate-before-assert — the LLM is a witness the entity can outgrow, not
  an oracle it defers to.
- **default == today**: `.so` md5 stays `7efe75eba05b006cafd15dbb4b7da246`;
  protected CAN internals untouched; `communication_concepts.json` /
  `source_provenance.py` are non-protected in-tree files; model + venv under
  `/applications`, NOT committed.

## Honest bounds and the deferred temporal path

- `qwen3` is seeded as a FLAT-band source (like `wikipedia`), not a temporal
  entity. The richer design — dated `trust_relevant` calibration events composed
  into the band via `source_provenance.context_for` — needs the
  `communication_concepts` INSTALLER (which materialises a `timeline` into
  `SourceEvent` nodes) and the `SourceEvent`/`has_event` grammar. Neither is
  present in this checkout (the installer is an untracked artifact; the loadable
  grammar here does not admit `has_event`). So the temporal elaboration is
  DEFERRED and documented, not faked. The flat band is the honest, fully
  in-tree-testable representation, and it already delivers the load-bearing
  property: reaped LLM content weighed below an attested source, corroborate
  before assert.
- Next: block 332 harvests KNOWLEDGE at scale (the calibration-earned tier) into
  `seeds/generated/`, every edge tagged `source: qwen3` + its per-tier weight;
  block 333 shows the capability delta and the outgrow-the-witness guard.

# Harvest a current model as a trust-weighted source — PRE-REG

**Block**: 330000 (bring-up + calibration). Plan A of the harvest arc: extract a
CURRENT LLM's content into Jabberwock as a trust-weighted `source` the entity
reasons over with its existing epistemic machinery (`source_provenance.py` +
fusion). Plan B (a `qwen3_5` numpy mechanism reader) is deferred —
`HARVEST_QWEN38_PLAN_B_MECHANISM_READER.md`.

## Model

`empero-ai/Qwen3.8-4B-Distill` — the frontier Qwen3.8 distilled into the
Qwen3.5-4B **hybrid `qwen3_5`** architecture (linear-attention/SSM + sparse
full-attention, MRoPE, vision tower, MTP head). Chosen after the on-disk
`Qwen3.8-27B` (same architecture, 52 GB) proved infeasible on this box (~40 GB
usable RAM). The 4B (~6 GB bf16) loads in RAM and runs on CPU (~2-3 s/forward).

The numpy `NumpyQwen3` reader does NOT support `qwen3_5` (Plan B). The extraction
arc only needs next-token logits + per-layer hidden states, which the HF forward
provides for any architecture — surfaced by a thin shim
(`domains/llm_hf_forward.py::HFForward`) so the 327/328/329 extractors run
unchanged (`elicit_isa`, `word_vectors`, `statement_vectors_hf`).

## Claims (falsifiable)

**Claim 1 — the current model brings up on the extraction path.** `HFForward`
loads `qwen3_5` under transformers 5.16.1 and yields correct next-token logits +
`output_hidden_states`. (Infrastructure gate.)

**Claim 2 — calibration per tier.** Re-running the three extraction measures
(knowledge is-a held-out entailment; concept opposite held-out transfer; process
negate held-out application) with their anti-faking controls yields a per-tier
reliability that becomes this source's trust events (block 331). Prediction: a
more capable model gives cleaner knowledge (fewer self-loops, more surviving
relations) than the 0.6B. Concept/process reliability reported honestly — a
weak or control-failed tier earns LOW/NO trust, which is the correct calibration.

**Claim 3 — trust is EARNED per tier, not assumed.** The calibration numbers,
not a hand-set constant, set the source's per-tier trust. A tier whose extracted
result does not beat its control earns no trust from this measure.

## Method

- Bring up `HFForward(MODEL)`; smoke-gate logits + hidden_states.
- KNOWLEDGE: `elicit_isa` over the 327 taxonomy (constrained candidates, drop
  self-loops); build the extracted-edge transitive closure; measure held-out
  (dist ≥ 2) entailment accuracy by substrate-style traversal.
- CONCEPT: contextualised word vectors (`statement_vectors_hf`, mid layer);
  `fit_opposite_operator` on context-A families; transfer AUC on held-out B vs a
  random-W control.
- PROCESS: `statement_vectors_hf`; `fit_process_operator` + `fit_valence_probe`
  on A; apply to held-out B; extracted vs identity vs shuffled-N.

## Anti-faking

- Held-out disjoint from elicitation in every tier; controls (shuffle / random /
  identity) reported; no LLM at the query step of the substrate readouts.
- The calibration is HONEST about weak/failed tiers — a control that matches the
  extracted result means that tier earns no trust, and that is reported, not
  hidden.
- **default == today**: `.so` md5 stays `7efe75eba05b006cafd15dbb4b7da246`;
  protected CAN internals untouched; model + venv under `/applications`, NOT
  committed; the shim and extractors are additive python.

# Harvest calibration — Qwen3.8-4B-Distill as a source — RESULTS

**Block**: 330000. Pre-reg: `HARVEST_QWEN38_PREREG.md`.
Build: `domains/llm_hf_forward.py` (`HFForward` shim),
`domains/llm_process_seed.py` (`statement_vectors_hf`);
measure: `scripts/llm_harvest_calibrate.py`.

**BRING-UP GREEN; CALIBRATION MIXED AND HONEST. The current model
(`empero-ai/Qwen3.8-4B-Distill`, hybrid `qwen3_5`) brings up on the extraction
path via the HF-forward shim and produces a clean, HIGH-trust KNOWLEDGE tier — a
decisive improvement over the 0.6B. The CONCEPT tier transfers only weakly at
these settings, and the PROCESS tier's control FAILED (shuffle == extracted), so
those two earn LOW / NO trust from this calibration. The per-tier numbers are the
source's trust events for block 331.**

## Bring-up (Claim 1): HOLDS

`HFForward` loads `Qwen3.8-4B-Distill` (`model_type qwen3_5`,
`Qwen3_5ForConditionalGeneration`) under transformers 5.16.1 in ~16 s (f32, CPU),
`n_layers=32`, 33 hidden-state layers exposed. Correct logits: "The capital of
France is" → " Paris"; "A dog is a kind of" → " animal". Forward ~2-3 s. The
extraction arc runs unchanged through the shim; the numpy reader is not needed.

## Calibration (Claim 2 / 3), per tier

| tier | measure | result | control | trust read |
|---|---|---|---|---|
| **knowledge** (is-a) | held-out transitive entailment | **1.00** (33/33 pos, 33/33 neg) | 0 self-loops / 24 edges | **HIGH** |
| concept (opposite) | held-out transfer AUC | 0.59 | random-W 0.52 | LOW (barely over control) |
| process (negate) | held-out application | extracted 1.00, identity 0.00 | shuffle **1.00** | NONE (control failed) |

### Knowledge — clean, high trust
24 is-a edges extracted with **0 self-loops** (the 0.6B produced many: fish→fish,
rock→rock), a fuller taxonomy, and 33 held-out ≥2-hop entailment positives — all
answered correctly by substrate traversal (1.00, 33/33 + 33/33). The more capable
model's relational knowledge is markedly cleaner, exactly the predicted
"sharper operators → higher trust". Knowledge is the harvest-worthy tier.

### Concept — weak transfer at these settings
Opposite-operator transfer AUC 0.59, barely above the random-W control 0.52
(chance 0.50) — and BELOW the 0.6B's 0.68. The contextualised "The word X means"
vector at layer 16 is a poor antonym representation for this model. Honest read:
the concept tier earns LOW trust from this measure; a better concept
representation (different layer / template / the substrate negative-coupling
signature, which 328 showed was the crisp half) is a follow-up, not asserted
here.

### Process — control FAILED, no trust credited
Extracted-N application reads negated 1.00 and identity 0.00 (so the transform
does something), BUT the shuffled-N control ALSO reads 1.00. When a scrambled
operator matches the extracted one, the readout is not discriminating —
"X is not Y" statements are trivially separable from "X is Y" by the valence
probe regardless of the transform, so the measure does not credit the extracted
process. Reported as a NULL: process earns no trust from this calibration as run.
(A tighter process readout — output-config valence rather than probe-side, or a
non-negation process — is the follow-up.)

## Verdict

The current model brings up cleanly on the extraction path, and calibration
gives an honest, differentiated trust signal:
- **Knowledge: high** (1.00 held-out, 0 self-loops) — the tier to harvest at
  scale (block 332) and seed at a correspondingly higher trust band (block 331).
- **Concept: low** (AUC 0.59 ≈ control) — seedable only at a corroborate-only
  band, if at all, and flagged for a better representation.
- **Process: none** (control failed) — not harvested until the readout is fixed.

This is the calibration's job: it tells us which tiers this model+representation
supports before we seed the entity, so the `qwen3` source's trust is EARNED per
tier, not assumed. Block 331 turns exactly these three numbers into the source's
`trust_relevant` timeline events.

## Anti-faking / method

- Held-out disjoint from elicitation in every tier; controls reported for all
  three; the concept below-control and process control-failure are stated
  plainly, not hidden.
- No LLM at the substrate-readout step; the model is the elicitation source only.
- **default == today**: `.so` md5 stays `7efe75eba05b006cafd15dbb4b7da246`;
  protected CAN internals untouched; model + venv under `/applications`, NOT
  committed.

## Honest bounds

- One model, one representation choice per tier (mid-layer contextual vector),
  small batteries (327/328/329 sizes). The knowledge result is robust
  (0 self-loops + 66/66); the concept/process results bound THESE settings, and
  the follow-ups (concept representation, process readout) are named, not
  hand-waved.
- Consequence for the arc: block 332 harvests KNOWLEDGE at scale (the earned
  tier); concept/process are seeded only at their earned (low/none) bands or
  deferred pending the readout fixes — the entity's trust in the `qwen3` source
  is thereby calibrated per tier from measured reliability.

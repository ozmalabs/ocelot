# Thoughtexperiment all-domain selector surface v1 results

**Outcome:** the measurement-only all-domain source surface matches all four audited mechanism labels in all three workers.

The panel scans 806 Python modules under `domains/*.py`. It closes both implemented cases: speaker scale normalization (matching `domains/agent_frontend.py`) and reliability-weighted cue fusion (matching `domains/combinatorial_recognizer.py`). It leaves the denoising-diffusion image-generation and VAE reconstruction controls open. All three workers produce identical verdicts, use the same 806-file surface and boot identity, and pass source-stability checks.

| Mechanism case | Expected | All-domain selector | Source match |
|---|---|---|---|
| Speaker scale normalization | covered | covered | `domains/agent_frontend.py` |
| Reliability-weighted cue fusion | covered | covered | `domains/combinatorial_recognizer.py` |
| Denoising diffusion image generation | open | open | — |
| Variational autoencoder latent image reconstruction | open | open | — |

This supports widening implementation lookup for these distinctive mechanism keys. It is not enough to change production policy: the panel has only four selected cases. The reliability-weighted fusion match proves that this operation exists for the represented channels; it does not show that a visual front end or a full vision-language model exists. `is_gap` accepts one matching `name_key` as sufficient to close an implication whose `name_keys` may contain several candidate descriptions, so whole-gap closure must be audited separately from sub-mechanism coverage.

Next expand the source-audited calibration set across domains and include partial-implementation cases. Then test an explicit domain-aware scope or whole-domain default against both false-open and false-covered outcomes before changing synthesis behavior. See [preregistration](THOUGHTEXPERIMENT_SELECTOR_DOMAIN_SURFACE_V1_PREREG_20261001.md), [runner](../../../evaluation/substrate_capability/thoughtexperiment_selector_domain_surface_v1.py), and [raw capture](../../../evaluation/reports/thoughtexperiment_selector_domain_surface_v1_raw_20261001.json).

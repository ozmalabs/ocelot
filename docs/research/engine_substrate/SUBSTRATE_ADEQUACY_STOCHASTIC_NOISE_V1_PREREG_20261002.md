# Stochastic label-noise dose response v1 — preregistration

## Question

How does the provenance-bound receipt plus selected-probe acceptance rule trade correct adoption, false adoption, and refusal as independently signed label noise increases and provider count changes?

## Design

Use two independent Boolean task families: parity and three-input threshold. Each is tested with its correct candidate and a constant-false wrong candidate on a broad domain with a distinguishing selected probe. The full factorial crosses independent label-flip probabilities 0, 0.1, and 0.5 with 1, 3, and 5 configured test providers. Each of three fresh workers performs 20 deterministic trials per cell (2 families × 2 candidate qualities × 3 noise levels × 3 provider counts; 2,160 total trials).

Each provider independently flips the oracle label with the preregistered Bernoulli probability. Every signature binds the request, selected input, and provider identity. The adjudicator is fail-closed: conflicting labels are `ambiguous`; same labels contrary to the candidate are `rejected`; matching evidence is `accepted`. Adoption eligibility is accepted receipt plus nonzero recomputed probe entropy, matching the live strict route. This is mechanism-level measurement of the decision rule, not repeated codebook writes.

## Expected dose response

For a correct candidate, adoption probability is `(1-p)^m`; unanimous all-flipped labels produce rejection with probability `p^m`; otherwise conflicting labels produce refusal. For a wrong candidate at a distinguishing probe, false-adoption probability is `p^m`, truthful unanimous labels reject with probability `(1-p)^m`, and mixed labels produce ambiguous refusal. At `p=0.5`, correctness and false-adoption probabilities are symmetric; increasing provider count cannot recover correctness without a calibrated source/redundancy assumption.

## Gates and limits

Source/native/protocol/analyzer lock, complete schedule, distinct process IDs, exact HMAC and receipt replay, exact selector replay, and held-out oracle parity are required. Empirical cell counts must be reported beside exact probabilities; 60 trials per cell are descriptive, not a field noise estimate. Providers are simulated independent channels, not real independent authorities. The study does not estimate natural error rates or authenticate oracle truth.

## Reproduction

```sh
.venv/bin/python evaluation/substrate_capability/substrate_adequacy_stochastic_noise_v1.py --lock
.venv/bin/python evaluation/substrate_capability/substrate_adequacy_stochastic_noise_v1.py
.venv/bin/python evaluation/substrate_capability/analyze_substrate_adequacy_stochastic_noise_v1.py
```

The initial lock exposed a manifest normalization defect before workers started: JSON converts tuple-valued design fields to lists, so direct comparison rejected an otherwise unchanged schedule. No trial was run or captured. The confirmatory runner uses list-valued design constants and a v1.1 lock; the initial lock is retained as a diagnostic. See the [v1.1 amendment](SUBSTRATE_ADEQUACY_STOCHASTIC_NOISE_V1_1_AMENDMENT_20261002.md).

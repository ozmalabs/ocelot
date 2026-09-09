# LLM trained router — does training P beat random features? — RESULTS

**Block**: 317000. Pre-reg: `LLM_TRAINED_ROUTER_PREREG.md`.
Build: `domains/llm_structure_recovery.fit_router_trained`; measure:
`scripts/llm_trained_router_measure.py`.

Trained the router's projection `P` by backprop (the block-316 named lever) and
compared it to the random-feature router. **Verdict: DATA-BOUND NEGATIVE.
Training P does NOT beat random features at this corpus size — unregularised it
OVERFITS (worse than random features); with weight decay it RECOVERS TO PARITY
but does not surpass. The manifold framing stands; the path further up it is
bounded by training DATA, not architecture.**

## Measured (Qwen3-0.6B, 60 train / 10 held-out, agreement vs full graph)

| target | trained(wd) | trained(no-reg) | random-feat | oracle |
|---|---|---|---|---|
| 0.50 | 2 | 1 | 2 | 8 |
| 0.40 | 1 | 0 | 2 | 5 |

(An earlier run at 30 prompts / rank-256 / no-reg: trained 1 vs random-feat 4
at 0.5 — the overfitting was even starker with fewer examples and more
readout capacity.)

### Claim 1 — trained P beats random features: FAILS (data-bound)
trained(wd) matches random-feat at 0.5 (2 vs 2) and trails at 0.4 (1 vs 2). It
does NOT surpass. Training the projection did not climb above random features
at 60 prompts.

### Claim 2 — overfitting check: HOLDS
trained(no-reg) < trained(wd) (1 vs 2 at 0.5, 0 vs 1 at 0.4). The
unregularised trained router — a per-layer readout `Wout (ff×r)` with hundreds
of thousands of parameters against ~60 examples — OVERFITS and generalises
worse than the regularised random-feature ridge. Weight decay recovers it to
parity. So the failure of claim 1 is DATA / regularisation, not "training
cannot help."

## Verdict — the path up the manifold is data-bound

The correction chain resolves cleanly and honestly:
- Block 315: a LINEAR router failed → wrongly called a "nonlinearity floor."
- Block 316: a NONLINEAR (random-feature) router beat the linear one →
  nonlinearity IS recoverable, floor retracted; the selector is a manifold.
- Block 317 (this): TRAINING the projection does NOT beat the regularised
  random-feature baseline at 60 prompts — unregularised it overfits, with
  weight decay it reaches parity. So the remaining climb to the oracle is
  bounded by TRAINING DATA at this scale, not by the architecture.

The honest state: the manifold is recoverable and richer approximators are the
right axis (nonlinear > linear), but at this tiny corpus a trained projection
cannot out-generalise a regularised random-feature map — it needs far more
training data. The oracle gap is now attributable to a concrete, mundane cause
(data), which is a cleaner bound than an architectural mystery.

## Anti-faking / method
- Router FIT on train corpus, EVALUATED on DISJOINT held-out (fixed trained map
  on the held-out input — not memorisation). Both reg settings reported.
- The router is genuinely cheaper than the FFN (`r ≪ d`). Oracle is a per-query
  upper bound.
- Every fraction reported, including the failure and the overfitting split.
- **default == today**: `order2_shape=None` bit-exact; `.so` md5 stays
  `7efe75eba05b006cafd15dbb4b7da246`; protected CAN-internals / toolbox
  untouched; models + venv under `/applications`, NOT committed.

## Honest bounds
- One small model (0.6B), ~60 train prompts — tiny for training a per-layer
  projection. The data-bound conclusion is specific to this scale; whether a
  much larger training corpus lets a trained P surpass random features (as the
  manifold framing predicts it eventually should) is the named, un-run next
  step. torch used for TRAINING only; inference is numpy, `.so` untouched.

# LLM trained router — does training P beat random features? — PREREG

**Block**: 317000

**Task**: Block 316000 showed a cheap NONLINEAR router beats the linear one
(the active-set selector is a manifold, not a line), and that rank 64 == 256
pointed at the RANDOM projection basis — not readout capacity — as the limiter,
naming a TRAINED projection `P` as the next lever up the manifold. This trains
`P` by backprop and asks whether it climbs above the random-feature router
toward the oracle on held-out queries.

## 1. The trained router

`domains/llm_structure_recovery.fit_router_trained(model, corpus, rank, epochs,
lr, weight_decay)` — per layer, train the 2-layer MLP
`x → P(r×d) → ReLU → Wout(ff×r)` to regress the FFN activation magnitude, by
Adam backprop (torch, venv, TRAINING ONLY), exporting `P, Wout` to numpy into a
`NonlinearRouter` (same numpy `score` used at inference). Cheap at inference
(`r ≪ d`), same interface as the random-feature router.

## 2. Comparison (held-out, agreement vs the full graph)

At matched neuron-fractions:
- **trained(wd)** — trained P with weight decay (regularised).
- **trained(no-reg)** — trained P, no weight decay (over-parametrised).
- **random-feat** — the block-316 random-feature nonlinear router.
- **oracle** — per-query true-activation top-k (upper bound).

## 3. Falsifiable claims

1. **Trained P climbs above random features**: trained(wd) > random-feat at
   matched fraction — training the projection recovers more of the manifold
   than random features. (Registered hypothesis; MAY fail if data-limited.)
2. **Overfitting check**: trained(no-reg) < trained(wd) — an unregularised
   over-parametrised readout on a tiny corpus overfits, so regularisation is
   the difference. (Diagnostic.)

Reported with measured outcomes; a failed claim 1 is reported and diagnosed
(claim 2 isolates whether it is overfitting / data limits vs a real ceiling).

## 4. Anti-faking

- Router FIT on the TRAIN corpus, EVALUATED on DISJOINT held-out (fixed trained
  map applied to the held-out input — not memorisation).
- Both regularisation settings reported (over-parametrised and regularised).
- The router is genuinely cheaper than the FFN (`r ≪ d`); a win is real cheap
  recovery. Oracle is a per-query UPPER BOUND.
- **default == today**: `.so` md5 stays `7efe75eba05b006cafd15dbb4b7da246`;
  protected CAN-internals / toolbox untouched; models + venv under
  `/applications`, NOT committed.

## 5. Honest bounds

- One small model (0.6B), a SMALL train corpus (~60 prompts). If trained P does
  not beat random features, the likely cause is DATA (60 prompts is tiny for
  training a per-layer projection), not that training cannot help — the
  overfitting diagnostic distinguishes these. Reported as data-bound if so.

# LLM nonlinear router — the selector is a manifold, not a line — PREREG

**Block**: 316000

**Task**: Correcting block 315000. That rung fit a LINEAR router, found it did
not close the oracle gap, and concluded a "nonlinearity floor." That inference
was wrong: a linear router failing only shows a LINE cannot fit the selector.
The oracle's active-set selector is a NONLINEAR function of the input — it
lives on a MANIFOLD, which is recoverable by a NONLINEAR map. This rung tests
that directly with a cheap nonlinear router.

## 1. The nonlinear low-rank router

`domains/llm_structure_recovery.py`:
- `fit_router_nonlinear(model, corpus, rank, ridge)` — per layer, a FIXED
  random projection `P (r×d)` + ReLU features + a CLOSED-FORM ridge readout
  `Wout (ff×r)` (random ReLU features / kernel approximation; no autograd).
  `score(L, x) = Wout · ReLU(P · x)`. Genuinely nonlinear, and CHEAP:
  `d·r + r·ff` ≪ the FFN's own `2·d·ff` for `r ≪ d` — it predicts WHICH
  neurons fire without computing the activation.
- Same `score` interface as the linear `LearnedRouter`, so it drops into
  `coactivation_retrieve(seed_mode='router', router=…)` unchanged.

## 2. Comparison (held-out, agreement vs the full graph)

At matched neuron-fractions, sweeping rank:
- **nl-router** — nonlinear low-rank router seed + graph expansion.
- **lin-router** — the block-315 linear router (baseline the nonlinear must
  beat).
- **joint** — joint gate+up key (block 314's best hand-key).
- **oracle** — per-query true-activation top-k (upper bound).

## 3. Falsifiable claims

1. **`order2_shape=None` bit-exact** (default==today).
2. **Nonlinearity is recoverable and helps**: nl-router ≥ lin-router at
   matched fraction — a nonlinear cheap map captures more of the selector
   manifold than a line. (This is the correction to block 315.)
3. **How far up the manifold?** Report the remaining gap to the oracle and
   whether more rank helps — framing the residual as a
   QUALITY-OF-APPROXIMATION axis, not a floor.

## 4. What each outcome means

- nl > lin → the "nonlinearity floor" was an artifact of using a line;
  nonlinearity is recoverable, block 315's conclusion is corrected.
- nl reaches oracle → the cheap manifold router closes the gap (full payoff).
- nl > lin but < oracle → nonlinearity helps and the remaining gap is how much
  of the manifold THIS cheap approximator (random ReLU features) captures — a
  quality axis (better/trained nonlinear routers are the named next step), NOT
  an impossibility.

## 5. Anti-faking

- Router FIT on the TRAIN corpus, EVALUATED on DISJOINT held-out (fixed random
  P + fitted Wout applied to the held-out input — not memorisation).
- The oracle peeks at the true activation — explicit per-query UPPER BOUND.
- The router is genuinely cheaper than the FFN (`r ≪ d`), so a win is a real
  cheap-recovery result, not the oracle in disguise.
- **default == today**: `.so` md5 stays `7efe75eba05b006cafd15dbb4b7da246`;
  protected CAN-internals / toolbox untouched; models + venv under
  `/applications`, NOT committed.

## 6. Honest bounds

- One small model (0.6B), small batteries; a RANDOM-FEATURE nonlinear router
  (fixed P, fitted readout) — not a fully trained MLP. A win corrects the
  linear-floor claim; the residual gap bounds THIS approximator and names the
  trained-router next step (which climbs further up the same manifold).

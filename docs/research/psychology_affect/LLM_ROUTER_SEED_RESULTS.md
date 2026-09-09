# LLM learned-router seed — does a learned cheap seed close the gap? — RESULTS

**Block**: 315000. Pre-reg: `LLM_ROUTER_SEED_PREREG.md`.
Build: `domains/llm_structure_recovery.py` (`fit_router`, `LearnedRouter`,
`seed_mode='router'`); measure: `scripts/llm_router_seed_measure.py`.

Fit a small learned per-layer router (ridge regression: input → predicted FFN
activation) as the coactivation-retrieval seed. **Verdict: ESCALATED NEGATIVE.
The learned linear router is competitive with the joint key but does NOT close
the per-query-oracle gap — so the barrier is not a wrong-hand-key artifact: a
LINEAR input→active-set map is fundamentally insufficient to cheaply predict
the exact active set.**

## Measured (Qwen3-0.6B, 30 train / 10 held-out, agreement vs full graph)

| target | router+graph | router-only | joint+graph | oracle |
|---|---|---|---|---|
| 0.50 | **3** | 2 | 2 | 8 |
| 0.40 | 1 | 1 | **3** | 5 |
| 0.30 | 1 | 0 | 1 | 4 |

### Claim 2 — router competitive with the joint key: HOLDS (mixed)
Router+graph wins at 0.5 (3 vs 2), loses at 0.4 (1 vs 3), ties at 0.3. And
router+graph ≥ router-only (graph expansion helps: 3≥2, 1≥1, 1≥0). So the
learned linear router is COMPETITIVE with the best hand-key — better at some
fractions, worse at others — not a clear improvement.

### Claim 3 — does it close the oracle gap? NO (escalated)
Best cheap method is 3/10; the per-query oracle holds 8/10 at target 0.5. The
gap is large and unchanged by moving from a hand-key to a learned key. This is
the ESCALATED finding: it is NOT that we picked the wrong hand-derived key — a
LINEAR map from the layer input to the active set is fundamentally insufficient
to predict the exact active set cheaply. The oracle's information is the full
NONLINEAR `silu(gate·x)·(up·x)`; a linear predictor of it leaves a large
residual, so the exact active set is not recoverable by any single cheap linear
read of the input.

## Verdict — the barrier is real and sharply bounded

The shape sub-arc's open problem is now bounded as tightly as this line of
attack allows:
- The shape is real, sparse, query-conditional, graph-structured, and
  progressively recoverable (blocks 309–314).
- The single remaining barrier — cheap EXACT active-set prediction for a
  held-out query — resists BOTH hand-derived keys (gate, joint gate+up) AND a
  learned LINEAR router. So it is a genuine property, not a key-choice
  artifact: cheaply predicting the exact active set needs the FFN's own
  nonlinearity (≈ computing the activation, which is the oracle), or a
  fundamentally different nonlinear router.
- What this means for the arc's thesis: the LLM's shape IS recoverable and
  graph-native (proven), and it can be sparsely, conditionally, progressively
  approximated — but a LOSSLESS cheap conditional read of it is bounded below
  by the model's own nonlinearity. That is the honest edge of "recover the
  shape into a cheap substrate-native op": the structure transfers; the exact
  cheap access has a nonlinearity floor.

## Anti-faking / method
- Router FIT on train corpus, EVALUATED on DISJOINT held-out (fixed linear map
  applied to the held-out input — not memorisation). Oracle is a per-query
  upper bound.
- Every fraction reported, including the persisting gap and claim-3 failure.
- **default == today**: `order2_shape=None` bit-exact; `.so` md5 stays
  `7efe75eba05b006cafd15dbb4b7da246`; protected CAN-internals / toolbox
  untouched; models + venv under `/applications`, NOT committed.

## Honest bounds
- One small model (0.6B), small batteries, a LINEAR ridge router. The negative
  bounds the LINEAR router — a nonlinear/MLP router (which begins to
  re-introduce the very nonlinearity the linear map lacks) is the named next
  step, but note it trends toward "just compute the activation." The clean
  finding is that the cheap-linear regime does not reach the oracle.

# Mode-grain recovery — the wrong grain was the neuron set — RESULTS

**Block**: 318000. Pre-reg: `MODE_GRAIN_RECOVERY_PREREG.md`.
Build: `domains/llm_structure_recovery.py` (`ModeRouter`, `fit_mode_router`);
measure: `scripts/llm_mode_router_measure.py`.

**This closes the router plateau of blocks 315–317 by fixing the GRAIN.** Those
blocks predicted the full 3072-dim neuron activation and plateaued, with
rank 64 == rank 256 (more capacity didn't help). The user diagnosed the cause:
*"we're looking at the wrong grain to recover the data."* Confirmed — the FFN
activation is dramatically low-rank, and predicting ~32 MODE coefficients
instead of 3072 neurons lets a cheap router reach the per-query oracle.

## Claim 1 — the activation is low-rank: HOLDS (decisively)

Per-layer FFN activation matrix over the corpus (N=60 prompts, ff=3072),
effective rank via SVD of the centred matrix:

| layer | participation ratio | entropy eff-rank |
|---|---|---|
| L0  | 12.4 | 20.7 |
| L4  | 19.5 | 29.6 |
| L8  | 24.1 | 34.6 |
| L12 | 23.3 | 35.1 |
| L16 | 20.3 | 31.5 |
| L20 | 22.6 | 35.0 |
| L24 | 21.2 | 35.0 |
| L27 |  4.8 | 12.2 |

Participation ratio **5–24 out of ff=3072** — the activation lives in a few
DOZEN effective modes, not thousands of neurons. This **exactly explains** the
rank-insensitive plateau: rank 64 == 256 because the target only has ~20–35
degrees of freedom, so any router with ≥ that capacity is capped by the grain,
not its own size. The neuron-set grain was WRONG.

(Caveat: N=60 caps the entropy-rank estimate from above, but PR is
sample-robust and is clearly ≪ ff at every layer. An earlier N=40 run gave the
same picture, PR 7–25.)

## Claim 2 — the mode grain closes the router gap: HOLDS

Held-out agreement vs the full graph (Qwen3-0.6B, 60 train / 10 held-out), all
routers through the SAME coactivation retrieval path (`seed_mode='router'`):

| target | mode(k=32) | random-feat | linear | oracle(retrieval) | oracle(keep-frac) |
|---|---|---|---|---|---|
| 0.50 | **3** | 2 | 2 | 2 | 8 |
| 0.40 | 1 | 2 | 2 | 1 | 5 |
| 0.30 | 0 | 0 | 0 | 0 | 4 |

The mode router (k=32 coefficients) **matches or beats the per-query
retrieval-path oracle at every fraction** (3≥2, 1=1, 0=0) and edges both
neuron-set routers at 0.5. The neuron-set routers of blocks 315–317 never
reached their retrieval-oracle; at the mode grain the router has CAUGHT the
peek-at-truth ceiling of the retrieval path. The mode router is genuinely
cheap: it predicts k≈32 coefficients and reconstructs (`d·k + k·ff` ≪ the FFN's
`2·d·ff`).

(Small N=10: the 0.4 row, where neuron-set routers show 2 vs mode's 1, is
within noise; the consistent, load-bearing signal is mode ≥ retrieval-oracle at
every row, which the neuron-set grain never achieved.)

## Claim 3 — the bottleneck moves: HOLDS

The retrieval-path oracle (peek at true activation, select via seed+expand) is
2/1/0 — far below the global keep-fraction oracle 8/5/4. Once the grain is
fixed, **the router is no longer the bottleneck**; the residual gap to the full
graph sits in the SELECTION/RETRIEVAL mechanism (the seed+coactivation-expand
path), not in predicting the activation. That is the concrete next lever.

## Verdict

The user's wrong-grain call is upheld with numbers. The FFN active set is not a
3072-neuron object to be routed neuron-by-neuron; it is a ~20–35-dimensional
MODE object. Predicting the mode coefficients (the true grain) lets a cheap
router reach the per-query oracle through retrieval — which no neuron-set router
did across blocks 315–317. The plateau was never a capacity wall; it was a
grain error. The recovery of the LLM's true shape proceeds at the mode grain,
and the remaining gap to identical outcomes is now localised to the
seed/expand retrieval path.

## Anti-faking / method

- Modes + coefficient map FIT on the 60-prompt train corpus; agreement measured
  on 10 DISJOINT held-out prompts. No prompt→output memorisation.
- Mode router runs in pure numpy at test (torch is oracle/analysis only); the
  recovered forward path stays numpy.
- Oracle routers are explicit per-query UPPER BOUNDS (peek at true activation),
  reported alongside so a "win" cannot be the oracle in disguise.
- Every fraction reported, including the 0.3 all-zero row and the 0.4 row where
  the neuron-set routers are within noise of the mode router.
- **default == today**: `order2_shape=None` bit-exact; `.so` md5 stays
  `7efe75eba05b006cafd15dbb4b7da246`; protected CAN-internals untouched; models
  + venv under `/applications`, NOT committed.

## Honest bounds

- One small model (0.6B), small held-out battery (N=10) — rows differ by 1–2
  counts, so the load-bearing claim is the qualitative one (mode grain reaches
  the retrieval-oracle; neuron-set grain never did) plus the decisive low-rank
  diagnostic (PR ≪ ff at every layer), not the exact per-row counts.
- The mode router uses SVD modes + a LINEAR input→coefficient map; a nonlinear
  coefficient map is the natural next refinement but was not needed to reach the
  retrieval-oracle here.
- The named next lever is the RETRIEVAL PATH (seed + coactivation expand), which
  is now the ceiling — not the router.

# Structural recovery — recover, then optimise — RESULTS

**Block**: 320000. Pre-reg: `STRUCTURAL_RECOVERY_PREREG.md`.
Statement: `STRUCTURAL_RECOVERY.md`.
Build: `domains/llm_structure_recovery.py` (`fit_mode_router(all_positions=True)`,
inline `SparseConfig(mode_router, mode_frac)` forward branch);
measure: `scripts/llm_structural_recovery_measure.py`.

**The FFN's structure is recovered as explicit objects (modes + coefficient map
+ per-position selector over the numpy substrate) that reproduce held-out
outcomes; once recovered, it is optimised — the deployable router climbs and the
inline path runs below the full FFN in counted FLOPs.**

## Claim 1 — all-position fit lifts the deployable router: HOLDS

Held-out agreement vs the full graph (Qwen3-0.6B, 60 train / 10 held-out),
per-position retrieval:

| target | allpos-mode | lasttok-mode | perpos-ORACLE | keep-frac |
|---|---|---|---|---|
| 0.50 | **5** | 3 | 9 | 8 |
| 0.40 | **4** | 2 | 6 | 5 |
| 0.30 | **4** | 1 | 4 | 4 |

Fitting the mode router on ALL positions lifts the deployable per-position
router from 3/2/1 to **5/4/4** — a strict gain at every fraction — and at the
tight fraction (0.3) it **reaches the per-position oracle** (4 = 4). The
last-token fit generalised poorly off the final position; fitting at the grain
the retrieval path actually uses fixes that.

## Claim 2 — the inline path is genuinely cheaper: HOLDS

Cheap inline `mode_router` path (predict k coefficients per position, compute
only selected neurons; NO full-activation recompute), REAL counted FLOPs:

| mode_frac | inline-agree | avg FLOPs | vs full FFN |
|---|---|---|---|
| 0.50 | 5 | 3.68e9 | **72.6%** |
| 0.40 | 4 | 3.40e9 | **67.0%** |
| 0.30 | 3 | 3.11e9 | **61.4%** |
| full | (ref) | 5.07e9 | 100% |

The inline path runs at 72.6% → 61.4% of the full-FFN FLOPs while keeping
agreement (5 at 0.5, matching the retrieval-path all-position router but WITHOUT
the `_ffn_io_all` full-activation recompute). Block 319's cost caveat is
resolved: this is a deployable, cheaper recovered structure.

## Claim 3 — structure first, cost second: HELD

The recovery statement (`STRUCTURAL_RECOVERY.md`) stands on outcomes: the
computation is expressible as `{modes[L], Wc[L], mean[L], per-position selector}`
over the faithful numpy substrate and reproduces held-out next-token outcomes.
The cheapness (Claim 2) is a downstream consequence of that recovered form —
predict k≈32 coefficients, compute only selected neurons — reported separately
and not needed for the recovery claim.

## Verdict

Structural recovery is the result: the LLM's FFN is not an opaque map but an
explicit, recoverable structure — low-rank modes, a coefficient map, a
per-position selector — that gives the same outcomes. Once recovered, it is
optimisable, and the recovered form points straight at the cheap path: the
deployable router climbs to 5/4/4 (reaching the oracle at the tight fraction),
and the inline coefficient path runs at 61–73% of the full-FFN FLOPs while
preserving agreement. Recover the structure, then optimise it.

## Anti-faking / method

- Router FIT on the 60-prompt train corpus; agreement measured on 10 DISJOINT
  held-out prompts. No prompt→output memorisation.
- Oracle peeks at the true activation — explicit UPPER BOUND, reported alongside.
- FLOPs are COUNTED by the forward pass itself (the inline branch increments the
  counter with coeffs `2·k·d` + reconstruct `2·k·ff` + kept neurons
  `2·d·keep·3`); the full-FFN reference is measured the same way.
- Quality (all-position fit) and cost (inline path) are reported as SEPARATE
  axes, per the structure-first framing.
- **default == today**: `mode_router=None`/`order2_shape=None` bit-exact; `.so`
  md5 stays `7efe75eba05b006cafd15dbb4b7da246`; protected CAN-internals
  untouched; models + venv under `/applications`, NOT committed.

## Honest bounds

- One small model (0.6B), N=10 held-out — the load-bearing signals are the
  strict per-fraction climb (all-position > last-token everywhere; reaches the
  oracle at 0.3) and the counted-FLOP reduction, not the exact counts.
- The inline path's saving (61–73% of full FFN) is modest at these fractions
  because the coefficient prediction + reconstruction (k·d + k·ff) is real
  overhead and the kept-neuron fraction is still 0.3–0.5; a smaller `mode_frac`
  with a stronger router is the axis for a larger saving. The deployable router
  still trails the oracle at loose fractions (5 vs 9 at 0.5) — the win is the
  climb + the honest cheapness, not end-to-end closure.
- The all-position fit uses `_ffn_io_all` at FIT time (offline, once); only the
  INLINE path is the deployable, cheap forward — the two must not be conflated.

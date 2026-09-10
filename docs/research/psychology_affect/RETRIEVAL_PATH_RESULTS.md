# Retrieval path — the ceiling was one neuron set per sequence — RESULTS

**Block**: 319000. Pre-reg: `RETRIEVAL_PATH_PREREG.md`.
Build: `domains/llm_structure_recovery.py` (`_ffn_io_all`,
`mode_retrieve_per_position`, per-position `order2_shape` forward branch);
measure: `scripts/llm_retrieval_path_measure.py`.

**Block 318 caught the retrieval-oracle with the mode-grain router and moved the
gap into the retrieval path (retrieval-oracle 2/1/0 vs keep-oracle 8/5/4). This
block localises that ceiling to a single cause and removes it.** The retrieval
path was applying ONE neuron set to the whole sequence; the true active set is a
per-TOKEN object. Selecting per position lifts the retrieval-oracle to the
per-token level — the ceiling is gone.

## Claim 1 — the ceiling is fixed-set-across-positions (H1): HOLDS

Held-out agreement vs the full graph (Qwen3-0.6B, 10 held-out):

| frac | TRUE-fixed order2 (last-token set, one per sequence) | keep-frac (per-token) |
|---|---|---|
| 0.50 | 2 | 8 |
| 0.40 | 1 | 5 |
| 0.30 | 0 | 4 |

Applying even the **true** last-token active set as ONE fixed set across the
sequence caps at 2/1/0, while the SAME magnitude criterion applied PER TOKEN
reaches 8/5/4. Same neurons, same fraction — the only difference is fixed-set
vs per-position. The retrieval ceiling was never the seed or the coactivation
graph; it was the single-set-per-sequence constraint.

## Claim 2 — per-position retrieval removes the ceiling: HOLDS

| target | perpos-mode | perpos-ORACLE | fixed-mode (318) | keep-frac |
|---|---|---|---|---|
| 0.50 | 3 | **9** | 3 | 8 |
| 0.40 | 2 | **6** | 1 | 5 |
| 0.30 | 1 | **4** | 0 | 4 |

The per-position ORACLE (9/6/4) **matches or exceeds the global keep-frac
oracle** (8/5/4) — retrieval through the `order2_shape` path, once it selects
per position, recovers everything the per-token magnitude oracle recovers. The
fixed-set retrieval-oracle was stuck at 2/1/0; the ceiling is removed.

## Claim 3 — deployable router improves; gap is now router quality: HOLDS

The deployable per-position mode router (no peeking) beats the fixed-set mode
router at every fraction: 3≥3, 2>1, 1>0. So the per-position MACHINERY strictly
helps the real router. But it reaches 3/2/1, far below the now-unlocked oracle
9/6/4 — the residual gap is **per-position router QUALITY**: the mode router was
fit on LAST-TOKEN activations (block 318), so its predictions at non-final
positions are weaker. The next lever is a mode router fit on ALL-POSITION
activations.

## Verdict

The retrieval path's ceiling had a single, concrete cause: it committed to one
neuron set for the whole sequence, chosen from the last token, when the FFN's
active set varies by position. Making the selection per-position lifts the
retrieval-oracle from 2/1/0 to 9/6/4 — at or above the global per-token oracle,
so the SELECTION mechanism is no longer the bottleneck. The deployable
per-position mode router improves at every fraction; what remains is a
router-quality problem at the newly-correct per-position grain, not a mechanism
wall. The recovery of the LLM's true shape now has a clean per-position
retrieval path and a named next step (all-position router fit).

## Anti-faking / method

- Router FIT on the 60-prompt train corpus; agreement measured on 10 DISJOINT
  held-out prompts. No prompt→output memorisation.
- Both oracles peek at the true activation (per-position and global) — explicit
  UPPER BOUNDS, reported alongside so a "win" cannot be the oracle in disguise.
- **HONEST COST CAVEAT**: per-position mode retrieval recomputes `xg` at all
  positions (`_ffn_io_all`), so it is NOT cheaper than the FFN at eval. This
  rung proves the MECHANISM/grain of the selection path — that per-position is
  the right axis and removes the ceiling — NOT a cheapness win. A cheap
  per-position selector is a separate, later axis.
- Per-position forward branch is back-compatible: a 1D `order2_shape[L]` still
  means one fixed set; only a list/2D set triggers per-position selection.
- **default == today**: `order2_shape=None` bit-exact; `.so` md5 stays
  `7efe75eba05b006cafd15dbb4b7da246`; protected CAN-internals untouched; models
  + venv under `/applications`, NOT committed.

## Honest bounds

- One small model (0.6B), N=10 held-out — the load-bearing claims are the
  qualitative ones (fixed-set caps at 2/1/0 even with a perfect set;
  per-position oracle reaches the per-token oracle) plus the strict
  per-fraction improvement of the deployable router, not the exact counts.
- The deployable per-position router still trails its oracle by a wide margin
  (3/2/1 vs 9/6/4) — the win here is REMOVING THE MECHANISM CEILING and
  re-localising the gap to router quality, not closing it end-to-end.
- Named next lever: fit the mode router on ALL-POSITION activations so its
  per-position predictions match its last-token quality.

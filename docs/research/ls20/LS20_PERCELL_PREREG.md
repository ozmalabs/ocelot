# LS20 PER-CELL LIVE MECHANIC — PRE-REGISTRATION (block 222000)

**Committed ALONE, before any measurement code is trusted. Block `222000`
claimed via `scripts/seed_claim.py 222000 222999` → CLEAN (no collision
detected; verbatim `check_claim` report pasted in the commit).**

## THE RESIDUAL THIS RUNG ATTACKS (221000's honest flag)

221000 built an understanding-driven ls20 agent, but its LIVE per-action model
(`arc_ls20_understanding_live.py`) converged **trivially**: it modelled the
aggregate CHANGE-MAGNITUDE (`_changed_fraction`, ~52 of 4096 cells ≈ 1.3% per
action, ~uniform). Predicting "≈52 cells change" is always right and says
NOTHING about the mechanic — it never predicts WHICH cells or to WHAT value.
221000 flagged this in its own RESULTS §LIVE: *"a richer per-cell live model is
future work."* THIS rung is that model: `action × current-frame → per-cell
next-frame`.

## THE METRIC TRAP (pre-committed — the whole point of the rung)

On ls20-shaped 64×64 frames only a handful of cells change per action (≈0.2–1.3%).
**RAW per-cell accuracy is NOT a gate**: a "predict no change" (persistence) null
scores ≈99% and has learned nothing. The HEADLINE metric is scored on the
**CHANGE-SET**, never on raw accuracy:

- **change-set location F1** — precision/recall of predicted-changed-cells vs
  actually-changed-cells.
- **value-accuracy on the changed cells** — over the actually-changed cells, the
  fraction whose predicted new VALUE matches the truth.
- **strict changed-cell F1** — a predicted-changed cell is a TP only if it is an
  actually-changed cell AND its predicted value matches truth (location AND
  value in one number). This is the pre-registered HEADLINE.
- **exact next-frame-match rate** — fraction of triples whose predicted grid
  equals the true next grid cell-for-cell.

Raw per-cell accuracy is REPORTED for every arm to EXHIBIT the trap (all arms
≈99%, indistinguishable), but it is never the gate.

## THE MODEL (graph-native; assembled from 217000 + 221000)

The mechanic is per-**action** `Hypothesis` graph nodes:
`action → (region_colour, Transform)`, reusing the general 217000
`TransformDecode`/`DimInfer` `Transform{dim,delta}` verbatim:

- **PREDICT** — apply the hypothesised Transform to the current frame's region
  (the cells of `region_colour`) → a full predicted next frame, per-cell.
- **RESIDUAL** — per-cell mismatch predicted-vs-observed on the CHANGE-SET is the
  surprise.
- **LEARN** — a confirmed Transform compresses (conf += 1); a mismatch
  mints/revises a `Hypothesis` via the sd-loop. The action→Transform map is
  **DISCOVERED** by `TransformDecode` solving `G(object_before, object_after)`
  per action — never given (no hardcoded action→transform table anywhere).
- **CURIOSITY** — the pick rule routes to the LEAST-observed action
  (`Argmin(visits)`, NO win/goal term — the 221000 `uh_probe_pick` pattern over
  ACTIONS).

Winning is a NON-objective here — this rung is about the MODEL. In-frame per-cell
values are INTEGER (the integer lattice); the `Transform` is the CROSS-FRAME map
(a float — a shift delta / rotation — belongs in the map, never in a frame's
cells: the base-as-dimension invariant).

### How the general sd-loop supplies the full `Transform{dim,delta}` (verified)

Running `TransformDecode` on the two SEEN objects' `cells_to_signature`
signatures (216000 pixel eye → `["cell", r, c, "v<idx>"]`) exposes, on the
`has_transform` node, a COMPLETE applicable spec for every ls20 action family
(measured in the prereg pilot):

| family | `generator` | `k` | `transforms` (per-dim) |
|---|---|---|---|
| translate (move) | `None` | — | `shift` on dims (1,2), `deltas`=(dr,dc) |
| rotate | `rotation90` | k | (anchor shift on dims 1,2) |
| reflect | `reflection_c` / `reflection_r` | — | (anchor shift) |
| recolour | `None` | — | `subst` on dim 3, `delta`=((v_a,v_b),) |

This is the GENERAL op (dimension-arbitrary; the same `TransformDecode` that
serves Omniglot / ARC-transform), NOT an ls20 hack. Nothing ls20-special is added.

## THE TWO NULLS (pre-committed — the richer model MUST beat BOTH, CI-separated)

1. **persistence** — predict next = current. Predicts NO changed cells →
   change-set recall 0 → F1 0; value-acc on changed cells 0.
2. **aggregate-count (the 221000 model)** — learns the per-action mean CHANGED-CELL
   COUNT (the `_changed_fraction` × total), predicts THAT MANY cells changing at
   UNINFORMED (seeded-random) locations, to an uninformed value. Right count,
   wrong locations → low F1. This is the honest change-set instantiation of the
   221000 aggregate model.

A model that only beats persistence on RAW accuracy has proven nothing (the trap).

## GATES (pre-registered; measure-first; powered n fixed here)

- **G-percell-teeth (HEADLINE, OFFLINE powered).** On held-out ls20-shaped
  scenarios with rich per-cell dynamics, the learned per-cell model's **strict
  changed-cell F1** (and location-F1 and value-accuracy) is **CI-separated ABOVE
  both nulls** (learned 95%-bootstrap lower bound > each null's upper bound).
  Powered: **N_eval = 200 held-out scenes × 10 actions = 2000 triples**, 95% CI by
  **1000-resample bootstrap** over triples. This is the teeth 221000's live model
  lacked.
- **G-mechanic-discovered.** The agent confirms **all 10** per-action Transform
  hypotheses it was NOT given (4 translate directions with distinct deltas + 3
  rotations + 2 reflections + 1 recolour), each discovered by investigation
  (sd-loop recognition of the observed object before/after). SOURCE-AUDIT: NO
  hardcoded action→transform table in Python or seed constants (an audit script
  asserts the map is read from `Hypothesis` graph nodes minted from observation).
- **G-convergence.** Per-cell change-set surprise DROPS as the model learns — a
  real staircase over the 10 investigation cycles (unmodelled action ⇒ persistence
  fallback ⇒ high change-set error; modelled ⇒ ≈0), not a flat line.
- **G-live (the real number, HONEST).** Run on REAL ARC-AGI-3 ls20 (bounded
  n = 40 steps, budget stated). Report the per-cell model's change-set F1 vs the
  persistence null ON REAL FRAMES. If the per-cell model beats persistence's
  change-set score → the mechanic is learnable live. **If it does NOT converge in
  the budget, report the null STRAIGHT** (an honest fact about the live data
  budget, not a hidden failure). Auth verified BEFORE measuring; `ARC_API_KEY` from
  `/home/matt/ozma/internal/.env`, NEVER printed/committed. API unreachable/
  rejected/rate-limited ⇒ STOP and report; NEVER fabricate/cherry-pick/estimate.
- **G-graph-native.** The per-cell model is `Hypothesis` + `Transform` graph data;
  predict-and-residual (mint/confirm/revise) + the curiosity pick are RULES
  (`seeds/ls20_percell.json`, `pc_*`); the adapter is mechanical (ingest frame,
  read the graph-held Transform, apply it to render the predicted frame, compare,
  log). Source-audit clean.
- **G-discipline.** Integer-native in-frame. **Default-OFF byte-identical**: the
  221000/220000/218000 ls20 migrated tests unchanged with the new flag absent.
  **Canonical `.so` md5 `793ce09ed498a749abb79aeaea44b92e` UNCHANGED** (reuse
  `TransformDecode`; if a new Rust Term were truly needed, STOP + report — do NOT
  add one silently). `runners/dsl` diff EMPTY (`term.rs` included). Oracle
  `rung7_vision_bench` BEFORE == AFTER. 34-file
  `per_area_settlement_regression.sh` failing NODE-ID SET IDENTICAL before/after.
  `source_match` reported.

## FALSIFICATION BAR

The per-cell transform machinery is the GENERAL 217000 `TransformDecode`/`DimInfer`
(dimension-arbitrary; the same op that serves Omniglot / ARC-transform — not an
ls20 hack); the hypotheses are EXPLICIT graph nodes; and the action→Transform map
is DISCOVERED by investigation (sd-loop recognition), with a source audit proving
no hardcoded mechanic. A model that scores the change-set only via raw accuracy,
or whose map is a Python/seed constant, FAILS this rung.

## STRUCTURE

Build + power the change-set-F1 teeth OFFLINE first (2000 triples — the powered
headline), THEN run the LIVE half on real ls20 for the honest real-world number
(possibly partial). If the API is down, the OFFLINE teeth result is the deliverable.

## FILES (to be created)

- `LS20_PERCELL_PREREG.md` — this file (committed alone).
- `domains/ls20_percell_seed.py` → `seeds/ls20_percell.json` — the `pc_*`
  curiosity/predict-residual/hypothesis rules.
- `worlds/arc_ls20_percell.py` — the mechanical adapter: scene + world physics,
  `discover_spec` (sd-loop), `apply_spec` (render a graph-held Transform),
  per-cell metrics, the investigate/evaluate drivers.
- `scripts/arc_ls20_percell_measure.py` — the powered offline teeth + nulls +
  convergence + discovered-hypotheses + source_match audit.
- `scripts/arc_ls20_percell_live.py` — the bounded per-cell LIVE half.
- `tests/test_ls20_percell_migrated.py` — the gate tests.
- `results/arc_ls20_percell_{powered,live}.json` — the measured numbers.

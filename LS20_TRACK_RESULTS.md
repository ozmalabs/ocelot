# LS20 OBJECT-PERMANENCE TRACK — RESULTS (block 224000)

**RE-LAND of the "richer object model" that converts 222000's LIVE NULL — now
under a pre-committed gate.** Object permanence via connected-component tracking
+ centroid shift; the per-action shift is an EXPLICIT graph `Hypothesis`;
prediction TRANSLATES the tracked object per-cell.

Pre-registered in `LS20_TRACK_PREREG.md` (committed ALONE, SHA **`24940e8b69`**),
BEFORE any number here. Block `224000` claimed via `seed_claim.py 224000 224999`
→ **CLEAN** (verbatim `check_claim` recorded in the prereg; NOT a permanent
pytest — avoids the 223000 ledger-inversion mistake).

## WHY A RE-LAND (the process gap closed)

222000 proved the per-cell TRANSFORM mechanism OFFLINE (strict changed-cell F1
**1.0** vs ~0 nulls, CI-separated) but its LIVE half returned the pre-registered
NULL: **0.0 == persistence 0.0**, because its whole-frame-colour region selector
could not isolate the real ls20 avatar (nested fields + multi-colour avatar +
move/trail dynamic). An autonomous continuation (`percell-222000-cont` @
`ec8c18215a`) built the object-permanence fix and measured live **≈0.964** — but
WITHOUT a prereg commit. This rung re-lands that code under a gate committed
first, and RE-MEASURES the live number post-prereg.

## THE HEADLINE — G-live: CHANGE-SET STRICT-F1 vs PERSISTENCE on REAL ls20

`arc_ls20_percell_live_tracked.py --game ls20-9607627b --steps 300 --n-field 2
--cap 150` (`results/arc_ls20_percell_live_tracked.json`), **n = 120 scored real
transitions**, 1000-resample bootstrap 95% CI:

| metric (CHANGE-SET, REAL frames) | tracked model | persistence null |
|---|---|---|
| **strict changed-cell F1** | **0.9639 [0.9394, 0.9804]** | **0.0000 [0, 0]** |

- **CI-SEPARATED above persistence** (learned lower bound 0.9394 > persistence
  upper 0.0000) — `learned_beats_persistence = True`. The 222000 live NULL is
  CONVERTED.
- **Live provenance — FRESH API RUN against the DETERMINISTIC ls20 game.** The
  frames come from the real ARC-AGI-3 public API (`X-Api-Key` from the gitignored
  `.env`, never printed/committed; RESET returned `state=NOT_FINISHED`,
  `available=[ACTION1..4]`). The ls20 game (`ls20-9607627b`) is DETERMINISTIC, so
  cycling actions in the same order reproduces identical frames run-to-run: THIS
  re-land's fresh API run reproduced the continuation's number BYTE-FOR-BYTE
  (`mean = 0.963895173453997`), confirming both determinism and the earlier
  measurement. Auth verified BEFORE measuring; the run is a live API call
  sequence that is reproducible ("deterministic replay" in that sense).
- `final_state = GAME_OVER` at step 129 (win/lose is a SIDE EFFECT of blind
  action-cycling, never optimised; `levels_completed = 0`), `n_scored = 120`,
  `n_no_prior_or_untracked = 9`, `median_tracked_object_size = 25`.

## G-mechanic-discovered — the per-action shifts, DISCOVERED not given

Each real action moves the ~25-cell avatar by a fixed **5-cell** step, learned
purely from whole-object centroid displacement across tracked frames (no
hardcoded shift/action map anywhere in the agent path):

| real action | discovered shift (dr, dc) |
|---|---|
| ACTION1 | (-5, 0)  (up) |
| ACTION2 | (+5, 0)  (down) |
| ACTION3 | (0, -5)  (left) |
| ACTION4 | (0, +5)  (right) |

SOURCE-AUDIT **PASS**: the shifts are computed in `LiveObjectTracker.observe`
from `centroid(obj_after) − centroid(obj_before)` (integer-rounded), read back
for prediction via `agent.hypothesis(action)["dr"/"dc"]`. `grep` for a hardcoded
shift table (`_MOVE`/`_XFORM`/`±5`) in `worlds/arc_ls20_percell_track.py` and
`scripts/arc_ls20_percell_live_tracked.py` → **NONE**. The true action→shift map
lives only on the deterministic game server; the agent never reads it.

## G-track-teeth (OFFLINE powered synthetic) — the exact number is EARNED

Synthetic dense move+trail scenes (real ls20 palette; nested field + static
figure contamination — the honest twin of the live mechanic),
`tests/test_ls20_percell_track_migrated.py`:

| scenario | tracked strict-F1 | persistence | pre-committed bar |
|---|---|---|---|
| **rigid move** | **1.0000 EXACT** | 0.0000 | `> 0.99` ✓ |
| **with trail** | **0.8598** | 0.0000 | `> 0.7` AND `< 1.0` ✓ |
| **WRONG shift estimator (extent)** | **0.3091** | — | `< 0.5` ✓ (teeth bite) |

- On the rigid scene the discovered unit shifts are the TRUE translations
  `(-1,0)/(1,0)/(0,-1)/(0,1)` — not the object extent.
- **INSTRUMENT TEETH (the gate has teeth against a wrong shift estimator):** the
  buggy extent-not-displacement estimator (the one caught+fixed in the original
  build — it read the appeared-vs-vacated edge gap, over-reporting the shift as
  the object's extent `±3` instead of `±1`) scores **0.3091 < 0.5** on the SAME
  scene the centroid estimator aces at **1.0**. A metric that could not tell them
  apart would be toothless; the exact number is EARNED. (`shift_mode="extent"`
  exists ONLY to power this gate.)

## THE STANDING RESIDUAL — the honest ~0.036 gap (NAMED, not attacked here)

The live 0.9639 sits ~0.036 below 1.0. This is the honest **trail/consume**
residual: a rigid-translate model cannot predict the dropped trail cells (the
synthetic trail run predicted exactly this — 0.86 with a trail vs 1.0 rigid). It
is the STANDING residual, and the flash-consume-marking fold that attacks it is
the NAMED next rung **225000** — deliberately OUT of scope here (this rung is the
object-permanence re-land only).

## G-graph-native + SOURCE-AUDIT

- Tracking = mechanical perception (`field_colours` = dominant colour(s);
  `connected_figure_blob` = 4-neighbour BFS over non-field cells; centroid
  displacement). NO decision (no `if/else` over graph state choosing the model).
- The shift = a graph `Hypothesis` on the Percell agent, minted/confirmed/revised
  by 222000's existing `pc_*` RULES via the new optional `spec=` path on
  `Percell.observe` (default `None` = offline discovery unchanged).
- Predict = a rule-held `Transform` translating the tracked object → per-cell
  frame; the adapter reads `h["dr"/"dc"]` and renders (mechanical).

## DISCIPLINE

- **Canonical `.so` md5 `793ce09ed498a749abb79aeaea44b92e` UNCHANGED** (no Rust;
  reuses connected components + 222000's `Transform`/`Hypothesis`).
- **`runners/dsl` diff EMPTY** (`term.rs` included) — no tracked Rust file
  modified.
- **Default-OFF byte-identical:** `spec=None` default keeps the offline path
  unchanged. Base 222000 percell gates (8) + tracker gates (4) + planning +
  mapnav + flash migrated suites = **31 passed**.
- **Oracle `rung7_vision_bench`:** BEFORE **214 passed, 10 skipped** == AFTER
  **214 passed, 10 skipped**.
- **34-file `per_area_settlement_regression.sh`:** failing NODE-ID SET IDENTICAL
  before/after (**23 ids, 277 passed, 5 skipped**; `diff` empty;
  `results/track_regress_before.txt`, matching the 222000 23-id baseline).
- **New gates:** `tests/test_ls20_percell_track_migrated.py` **4 passed**
  (rigid-exact, trail-residual, shift-stored-in-graph, wrong-shift-estimator
  teeth).
- **Integer-native in-frame:** cell values are the integer lattice; the shift
  `Transform` is the CROSS-FRAME map (the base-as-dimension invariant).

## SCOPE HONESTY (synthetic-proven + benchmark value, both reported)

The synthetic G-track-teeth prove the object-permanence MECHANISM decisively
(rigid 1.0, trail 0.86, both vs 0.0; the exact number earned against a wrong
estimator). The LIVE half re-measures the real ls20 number under the
pre-committed gate: **0.9639 [0.9394, 0.9804] vs persistence 0.0, CI-separated**
— the 222000 live NULL is converted. Both reported. The ~0.036 trail/consume gap
is the named 225000 frontier.

## FILES

- `LS20_TRACK_PREREG.md` — pre-registration (committed alone, SHA `24940e8b69`).
- `worlds/arc_ls20_percell_track.py` — `LiveObjectTracker` (field / connected
  figure blob / centroid-shift → graph Hypothesis / translate-predict) + the
  `shift_mode` teeth hook.
- `worlds/arc_ls20_percell.py` — the small optional `spec=` path on
  `Percell.observe` (default None = offline byte-identical).
- `scripts/arc_ls20_percell_live_tracked.py` — the bounded LIVE half.
- `tests/test_ls20_percell_track_migrated.py` — 4 gate tests (incl. the teeth).
- `results/arc_ls20_percell_live_tracked.json` — the measured live number.
- `results/track_regress_before.txt` — the 23-id regression baseline.

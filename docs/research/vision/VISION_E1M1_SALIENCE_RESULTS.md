# E1M1 + SALIENCE WIRING — RESULTS (block 156000-156999)

`SEED CLAIM 156000-156999 CLEAN` (verbatim `check_claim` in
`VISION_E1M1_SALIENCE_PREREG.md`, committed before the run).

A **WIRING** rung: no new perception mechanism. Existing pieces connected and
scored against VizDoom's labels-buffer ground truth. **No Rust added, no seed
consumed, no default moved — new files only** (`scripts/e1m1_salience_probe.py`,
`tests/test_e1m1_salience_migrated.py`, this doc + the prereg), so the shipped
carve path is byte-identical by construction.

- Engine: `source_match = shared`, source fingerprint `3a66c0636a98e950…`
  (recorded in `results/e1m1_salience.json`, `engine_preamble()` refused a
  diverged/stale binary in the measuring process). NO Rust change → the engine
  is a build of this tree's unchanged Rust source.
- Oracle `scripts/rung7_vision_bench.sh` (data/ symlinked): **222 passed / 0
  failed BEFORE**, **222 passed / 0 failed AFTER** (both recorded below).
- Gate `tests/test_e1m1_salience_migrated.py`: **4/4**; the three synthetic
  headline assertions **3/3 stable across fresh pytest processes**.
- Determinism: VizDoom seed 156000 + a FIXED scripted walk (forward + a
  right-turn burst into the courtyard tics 40–60 + a dwell scan 78–160); skill 3;
  RES 320×240 → down=2 → **120×160**; L=4; flow block 8. All declared residuals.

---

## W1 — E1M1 runs end-to-end; complexity FRAGMENTS the carve (as predicted)

The eye now carves from `vision_screen` on the **real E1M1 map** (real
`DOOM.WAD`, scripted walk), scored per-object vs the downsampled labels buffer.
Value carve = the EXISTING `native.segment` (L=4), reused byte-for-byte.

| condition (down=2, 120×160, L=4) | monster IoU | item IoU | apparatus IoU | fp regions/frame | ms/frame |
|---|---|---|---|---|---|
| **E1M1 walk** (160 frames) | **0.009** (n=4) | 0.026 (n=357) | 0.168 (n=153) | **276.4** | 87.6 |
| `defend_the_center` (same grid) | 0.254 | — | — | 25.2 | — |
| `defend_the_center` committed (down=4, 80×60) | 0.243 (turning) | — | 0.246 | 5.7 | 1.2 |

**Read:** the pipeline runs end-to-end on the real map and the carve **degrades
massively, exactly as pre-registered.** E1M1's many wall textures / doors /
corridors / decorations over-segment the value carve — **276 false-positive
regions/frame vs `defend_the_center`'s 25 at the identical grid** (an 11× rise in
fragmentation). Enemy IoU collapses from 0.254 (defend) to 0.009 (E1M1), because
E1M1's live enemy on this walk is a distant **DoomImp of 1–9 px** → sub-pixel at
down=2. The `defend_the_center` value-carve at down=2 (0.254) reproduces the
committed down=4 baseline (0.243), confirming the pipeline is the 152000 one.
Timing: **87.6 ms/frame** at down=2 — **3× over Doom's 28.6 ms/frame budget**;
the carve alone is not real-time on the real map at this grid (a declared
residual: real-time needs a coarser grid or the accelerator).

## W2 — salience wiring: it DEMOTES the fixed apparatus, but raw magnitude lets the walking background dominate (HONEST MIXED)

Carved regions tracked across frames (mechanical nearest-overlap, no GT);
per-track salience = `max(shape_salience(cx), shape_salience(cy),
shape_salience(area))` using the EXISTING
`substrate_rs._native.Substrate.shape_salience` (Rust
`memory::order_n_shape_salience`). 1827 tracks (len≥3) scored.

| GT category | salience mean | **median** | max | n tracks |
|---|---|---|---|---|
| item (looms as agent approaches) | 4.62 | **3.24** | 13.3 | 37 |
| apparatus (view-fixed weapon) | 3.11 | **1.49** | 144.7 | 153 |
| background (walls/floor) | 7.42 | **2.55** | 2256.5 | 1637 |
| monster (live imp) | — | — | — | **0** |

- **AUC(foreground=item∪monster vs apparatus) = 0.717** — the clean, falsifiable
  win: salience ranks the **looming foreground objects ABOVE the view-fixed
  apparatus** (item median 3.24 vs apparatus median 1.49). The apparatus is
  large and central (it has the highest single-object IoU, 0.168) yet **least
  salient by rank**, precisely because it does not move — the operator's intended
  "looming vs fixed" contrast fires on real ink.
- **AUC(foreground vs background) = 0.588** — only weakly above chance, and
  **salience@k (k=1,2,3,5,8) is ALL background**: the top-K most-salient tracks
  are big walls. **Diagnosed:** `order_n_shape_salience` carries an *unbounded
  magnitude factor* (`magnitude = √var(trajectory)`), and during the WALK the
  textured background flows under egomotion, so a large background region's
  centroid/area trajectory has enormous absolute magnitude (top track: area swing
  → salience 2256 on a ~1800-cell wall region). Raw, unnormalised salience thus
  ranks by "how big × how much it moved", and the walking wall is the loudest
  thing in the view.
- **The live enemy could not be salience-ranked here: 0 monster tracks of
  length≥3.** At down=2 the imp is 0–2 cells and never persists as a trackable
  carved region (`auc_monster_vs_background = None`).
- The cutoff is the existing mechanism, not a magic number: fraction above the
  effort dial's own `salience_threshold` (0.02) is item 1.00, apparatus 0.94,
  background 0.90 — 0.02 is far below every category's mass, so the *dial's
  shipped threshold does not itself separate these classes*; separation is by
  rank (AUC), reported for a swept k with no fitted threshold.

**W2 verdict:** the salience wiring works as the operator intends on the *fixed
vs looming* axis (foreground > apparatus, AUC 0.717) — but **it does not put the
GT enemy in the top-K**, because (a) unnormalised magnitude lets the
egomotion-swung background dominate and (b) the imp is sub-pixel at down=2. This
is the honest headline: *salience demotes the self-apparatus; on a moving
platform the un-cancelled background is what it ranks highest.* That is exactly
the seam W3 addresses.

## W3 — egomotion is now SENSOR-VISIBLE on textured corridors (155000's scope condition met), but the median-gain estimator does not yet convert it

155000 found egomotion cancellation a NO-OP on `defend_the_center` (bare arena →
block-SAD gain (0,0), ~0 % nonzero flow). On the E1M1 textured walk:

| quantity | defend_the_center (155000) | **E1M1 walk** |
|---|---|---|
| nonzero-flow fraction (mean) | ≈ 0 % | **42 %** |
| dominant moving-flow vector | — | **(0, −1)** (horizontal, turning) |
| calibrated gain (median over ALL cells) | (0, 0) | **(0, 0)** |
| raw→efference monster IoU | (no-op) | 0.0000 → 0.0000 (n=4) |

- **Egomotion IS now visible** — 42 % of the view carries trackable flow (vs
  ~0 % on the bare arena) with a coherent horizontal dominant vector during
  turns. **155000's scope condition — "textured corridors, walked, produce
  visible egomotion" — is MET.** This is the free win 155000 predicted, confirmed.
- **But cancellation stays a no-op**, for a precise, honest reason: 155000's
  `calibrate_gain` takes the **median flow over ALL cells**, and with nonzero
  flow at 42 % (< 50 %), the median cell is still zero → gain (0,0) → the
  efference subtraction cancels nothing. Egomotion is visible in the *fraction*
  and the *dominant mode*, but not in the *median*. Converting it needs a
  >50 %-coverage scene or a **dominant-mode (not median) gain estimator** — a new
  mechanism, hence a new pre-registration, **not bolted on here** (§5).
- Independently, the imp is sub-pixel at down=2, so both raw and efference
  monster IoU are 0.0000 — the motion carve cannot catch a 1–2 cell mover
  regardless of cancellation.

**W3 verdict:** the scope condition 155000 set is satisfied (egomotion is now
observable on the real textured map); the cancellation is not yet converted
because the median-based gain estimator needs the dominant mode, not the median,
below 50 % coverage — diagnosed, not patched.

## Composition — the three deliverables tell one story

On a real textured walk the **background's egomotion is the dominant signal**:
W3 measures it (42 % of the view flows), W2 shows it dominates raw salience (the
top-K salient tracks are walls), and cancelling it is the needed-but-not-yet-
converted next step (W3 gain still (0,0) below 50 % coverage). Salience already
does the easy half — it demotes the view-fixed self-apparatus (AUC 0.717); the
hard half (demoting the egomotion-carried background) is gated on the egomotion
cancellation that W3 shows is now *visible* but not yet *estimated*.

## Timing / real-time

Value carve **87.6 ms/frame** at down=2 (120×160) — **≈3× over Doom's 28.6
ms/frame**. Not real-time on the real map at this grid; a declared residual (the
committed down=4 arena carve was 1.2 ms/frame). Timing measured in the same
process as the carve, no other timed rung running concurrently.

## Architecture audit (CLAUDE.md — the agent is Rust)

- **The carve** is the EXISTING Rust `native.segment` / `native.segment_motion`
  via `falling_world` — byte-for-byte the shipped eye. Reused, not rebuilt.
- **The salience** is the EXISTING Rust `memory::order_n_shape_salience`, called
  through the already-exposed `Substrate.shape_salience` staticmethod. The gate
  proves `track_salience` *delegates* to it (equal to the native value on a known
  input) and that the probe defines no `shape_salience` of its own. NO Rust added.
- **The tracker** is a mechanical position association (cell-overlap / centroid
  nearest-neighbour) over carved regions — the peer of `vector_field` /
  `quantize`, no conditional over graph state, no agent decision.
- **The scripted walk** is a known world-adapter fact (a fixed action sequence
  the agent issues), not a decision read from graph state. `capture_e1m1` is a
  pure I/O adapter over the real WAD (ingest frames; no interpretation).
- **The labels buffer** is the SCORING ORACLE, never fed to the eye. Scoring is
  IoU by POSITION and salience *ranking*, never cross-process region-id.
- **The cutoff** is the existing effort-dial `salience_threshold` (0.02, which
  falls out of the dial) — reported, not tuned; separation is by swept-k rank.

No Python agent decision anywhere. NO seed consumed for graph data; block
156000-156999 reserved for the VizDoom seed + RNG base only.

## WHAT I GOT WRONG

- **I fed un-normalised area into a magnitude-sensitive operator.**
  `order_n_shape_salience` multiplies by `√var(trajectory)`, so a 1800-cell wall
  region's area trajectory (magnitude in the thousands) buries a 5-cell item's
  centroid drift (magnitude ~10). I predicted background would be "modestly"
  separable; in fact background *dominates* salience@k outright. The rank-based
  AUC (0.717 vs apparatus) survived because it ignores magnitude, but **salience@k
  is worthless as built** — the fix is a scale-controlled trajectory (z-scored /
  shape-signature-normalised input), which is a NEW mechanism hypothesis for a
  future pre-registration, not a swap-in here.
- **I over-weighted the live enemy in the design.** The headline is framed around
  "GT enemies", but E1M1's opening has ONE distant imp (1–9 px) and many larger
  looming items. At down=2 the imp forms zero trackable tracks, so the enemy-
  specific claim is untestable on this walk/grid — the honest foreground signal is
  the *looming items*, and I should have said so up front. A finer grid (down=1)
  or a walk that closes on a nearer enemy is the obvious next rung.
- **I assumed "egomotion visible" would imply "gain estimable".** It does not:
  visibility is a *fraction/mode* property, but 155000's gain is a *median*, and
  the two diverge below 50 % flow coverage. The visibility win (42 %) is real; the
  cancellation win is not, and conflating them would have overclaimed.

## Bounds (§8)

- One map (E1M1), one skill (3), one seed, one scripted walk, one grid (down=2).
- The salience ranking is over CARVED regions of the value carve; a different
  carve (motion / depth / expansion) would track different regions.
- "foreground > apparatus (AUC 0.717)" is the only CI-free positive; "foreground
  > background" (0.588) is weak and the enemy-in-top-K claim FAILS.
- Synthetic-proven mechanism ≠ benchmark value: the gate proves the operator
  ranks directed > static; the E1M1 numbers show real-data confounds. Both
  reported (the arc's standing rule).

## Proposed VISION_PROTOCOL.md ledger row

- **THE EYE RUNS ON THE REAL MAP AND SALIENCE DEMOTES THE SELF-APPARATUS — BUT
  THE UN-CANCELLED WALKING BACKGROUND IS WHAT IT RANKS HIGHEST (2026-07-23,
  `VISION_E1M1_SALIENCE_PREREG.md` / `VISION_E1M1_SALIENCE_RESULTS.md`, rung
  commit `<HASH>`, NO seeds consumed, engine `3a66c0636a98e950…` shared/NO-Rust,
  base `main` HEAD `dc739d89e8`).** WIRING rung: `defend_the_center` → real
  **E1M1** (real WAD, scripted walk, down=2) + the EXISTING salience operator
  (`Substrate.shape_salience` = `memory::order_n_shape_salience`) wired to rank
  carved-region trajectories, scored vs the labels buffer. **W1:** end-to-end on
  the real map; complexity fragments the carve (276 fp regions/frame vs
  `defend_the_center`'s 25 at the same grid; enemy IoU 0.254→0.009 — a 1–9 px
  imp; 87.6 ms/frame, 3× over budget). **W2 (headline):** salience ranks looming
  foreground above the view-fixed apparatus (AUC 0.717, item median 3.24 vs
  apparatus 1.49) — but is magnitude-dominated, so salience@k is all background
  (big egomotion-swung walls) and the sub-pixel imp forms 0 trackable tracks
  (foreground-vs-background AUC 0.588). **W3:** egomotion is now sensor-visible on
  textured corridors (42% nonzero-flow vs `defend_the_center`'s ~0%,
  155000's scope condition MET) but the median-over-all-cells gain estimator
  stays (0,0) below 50% coverage, so cancellation is not yet converted.
  Gate `tests/test_e1m1_salience_migrated.py` 4/4 (constructed moving > static,
  able to fail; wiring reads the native operator; E1M1 end-to-end runs or skips
  explicitly if WAD/VizDoom absent), 3/3 stable across fresh processes. **§9:
  vision bench 222/0 both sides; NO Rust, NO seed, no default moved.**
  `SEED CLAIM 156000-156999 CLEAN`.

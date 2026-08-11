# RESIDUAL-SALIENCE — RESULTS (block 157000-157999)

`SEED CLAIM 157000-157999 CLEAN` (verbatim `check_claim` in
`VISION_RESIDUAL_SALIENCE_PREREG.md`, committed before the run).

THE ONE COUPLED FIX — **efference → residual → salience**. surprise = residual:
salience must run on the self-cancelled residual, not the raw signal. A general
ATTENTION ranking that should work even over a noisy carve.

- **New files only** (`scripts/residual_salience_probe.py`,
  `tests/test_residual_salience_migrated.py`, this doc + the prereg). NO Rust
  added, NO seed consumed, NO default moved — the shipped carve path and
  155000's median-gain path are byte-identical BY CONSTRUCTION (the dominant-mode
  gain is an ADDITIVE new function; `calibrate_gain` is untouched).
- Engine: `source_match = shared`, source fingerprint
  `3a66c0636a98e9500a73ac0acbe46d53db3fab79c6231c6c0ecdb7482f54fe60` (recorded in
  `results/residual_salience.json`; asserted, NEVER a pinned build hash). No Rust
  change → the engine is a build of this tree's unchanged Rust source.
- Oracle `scripts/rung7_vision_bench.sh` (data/ symlinked): **222 passed / 0
  failed BEFORE**, **222 passed / 0 failed AFTER**.
- Gate `tests/test_residual_salience_migrated.py`: **8/8**; the three H1 headline
  assertions **3/3 stable across fresh pytest processes**.
- Determinism: VizDoom seed 156000 + 156000's FIXED scripted walk (verbatim,
  imported); skill 3; RES 320×240 → down=2 → 120×160; L=4; flow block 8; the
  "moving cell" cutoff is the block-matcher's one-pixel step (`ZERO_FLOOR=0.5`).
  All declared residuals, reused from 156000 — not tuned to the score.

---

## H1 — SYNTHETIC (ideal oracle): the mechanism is PROVEN

### Dominant-mode gain recovers egomotion where the median reads (0,0)

Known egomotion `E=(0,6)`; a flow field where a `cov` fraction of cells carry
`E` and the rest are static (the exact 156000 <50%-coverage regime).

| coverage | nonzero-flow | **dominant MODE** | median-over-all (155000) |
|---|---|---|---|
| 0.42 | 42% | **(0, 6)** ✓ | **(0, 0)** ✗ |
| 0.30 | 30% | **(0, 6)** ✓ | **(0, 0)** ✗ |
| 0.55 | 55% | (0, 6) ✓ | (0, 6) ✓ |

**The mode recovers the true egomotion at 30% and 42% coverage, exactly where
the all-cell median (155000's `calibrate_gain`) reads (0,0).** The peak falls
OUT of the flow histogram (§13); it is not a tuned threshold. (Otsu-on-magnitude
cross-check of the "moving cell" cutoff = 0.143, well below the one-pixel step,
so the step and Otsu agree that the moving cells are the movers.)

### Residual salience ranks the mover above the background where RAW fails

Synthetic walk: uniform egomotion `E=(0,6)` + an independently-moving object
(own motion `(0,−3)`, so observed `(0,3)`) + a view-fixed apparatus (flat) + 12
fragmented background regions (each swung by `E` + jitter). Per-frame egomotion
ESTIMATED by the dominant-mode gain (able to fail), then cancelled; apparatus
folded (155000's zero-observed-flow readout).

| track class | RAW salience | RESIDUAL salience |
|---|---|---|
| **mover** (independent) | 10.36 | **10.36** |
| background (mean / max) | 28.89 / 31.37 | **0.10 / 0.17** |
| apparatus (view-fixed) | 0.00 | 0.00 |

| statistic | RAW | RESIDUAL |
|---|---|---|
| AUC(mover > background) | **0.00** | **1.00** |
| AUC(mover > apparatus) | 1.00 | **1.00** |
| mover rank (by salience) | 13th | **1st** |

**RAW salience ranks ALL 12 egomotion-swung backgrounds ABOVE the mover
(AUC 0.00) — the mover is 13th.** Cancelling the self-predicted flow collapses
the background to ~0 (its motion WAS the egomotion) while the mover keeps its own
residual motion → **AUC 1.00, mover top-1, apparatus stays demoted.** The
mechanism does exactly what it claims against an ideal oracle.

### Controls (all pass)

- **No egomotion.** `E=(0,0)` → mode all-zero → residual == raw → **ranking
  byte-identical, values identical**. The OFF path is a no-op.
- **Static + egomotion.** Background swung by egomotion, no mover → all residuals
  ~0 → **max residual salience 0.18** (flat/low everywhere).
- **Mover + no egomotion.** `E=(0,0)`, one mover → **mover top-1 with AND without
  cancellation, raw == residual** (nothing to cancel).

---

## H2 — E1M1 (real WAD, 156000 walk/seed/grid): the HONEST SPLIT

160 frames, 1840 tracks (len≥3) scored against the labels buffer.

### The SUB-MECHANISM WIN — egomotion is now CAPTURED

| quantity | 155000 median-over-all | **157000 dominant-mode** |
|---|---|---|
| frames with a nonzero egomotion estimate | **1 / 159** | **154 / 159** |
| nonzero-flow fraction (mean) | 42% | 42% |

**The dominant-mode gain captures the egomotion in 154/159 motion frames, where
155000's median-over-all-cells reads (0,0) in all but one.** This is 156000's W3
no-op, fixed: the median is zero at 42% coverage; the mode is not. The pipeline's
first stage does exactly what it was designed to.

### The end-to-end ranking DID NOT improve — the named DEGRADE

Per-category salience (raw → residual medians) and the AUCs:

| category | n | raw median | residual median | raw max | residual max |
|---|---|---|---|---|---|
| item (foreground) | 37 | 2.59 | **4.34** ↑ | 12.6 | 26.9 |
| apparatus | 149 | 1.36 | **3.42** ↑ (promoted) | 143.3 | **47.3** ↓ |
| background | 1654 | 2.57 | 2.99 | **2256** | **60.2** ↓ |

| AUC | RAW | RESIDUAL | 156000 |
|---|---|---|---|
| foreground vs background | 0.550 (W2) / **0.585** (centroid-only) | **0.563** | 0.588 |
| foreground vs apparatus | **0.679** | **0.519** | 0.717 |
| monster vs background | — (0 tracks) | — (0 tracks) | — |

What the residual cancellation DID do, measured:
- **It killed the extreme egomotion-swung background outlier** (background
  salience max **2256 → 60**) — the loudest wall in 156000's view is cancelled.
- **It lifted the foreground items** (item median **2.59 → 4.34**).
- Net, residual fg-vs-bg (0.563) edges the 156000 W2 raw (0.550/0.588) but is
  **BELOW** the apples-to-apples centroid-only raw (0.585): **the ranking did not
  improve.**
- **Apparatus demotion COLLAPSED** (0.679 → 0.519, ≈chance): residual salience
  PROMOTES the apparatus (median 1.36 → 3.42).

Both pre-registered H2 win conditions FAIL (fg-vs-bg did not clear the raw
centroid baseline; apparatus demotion fell below 0.70). **This is a DEGRADE, and
it is diagnosed, not tuned (§5/§7).**

### Diagnosis (why capturing the egomotion did not convert)

Measured directly on the E1M1 tracks:

1. **The apparatus fold mis-fires on a jittery carve.** The apparatus (weapon
   sprite) carve centroids jitter with **mean observed step 1.24 cells**
   (median 0.84); only **37%** of apparatus steps fall below the one-pixel fold
   floor. For the other 63%, cancellation subtracts the egomotion vector and
   ADDS `−egomotion` motion → the view-fixed apparatus is PROMOTED. The
   one-pixel floor (which correctly falls out for a clean field) is too tight for
   a fragmented real carve.
2. **E1M1 is a FORWARD walk → depth-dependent translational flow.** Background
   observed-step magnitudes span **median 1.68, p90 4.61** (near walls swing
   fast, far walls slow), but the dominant-mode gain is a **single global vector**
   (median magnitude 1.00). One uniform vector cannot cancel depth-dependent
   flow, so the bulk background keeps a large residual → stays salient. 155000's
   efference model is grounded in ROTATION (depth-independent, uniform) — which
   is exactly the H1 case it proves; the forward-translation case violates its
   uniform-field assumption.
3. **The live imp is sub-pixel** at down=2 → **0 trackable monster tracks** (the
   156000 wall, unchanged). Enemy-promotion is UNTESTABLE on this walk/grid — a
   SEPARATE persistent wall (needs foveation / a finer grid), named, not fixed
   here.

**salience@k (top-8):** raw = all background; residual = mostly background with
apparatus intruding (the promotion). Neither ranking surfaces the (sub-pixel)
enemy.

---

## Timing / real-time

The residual pipeline is a cheap post-pass over the existing carve (a histogram
peak + arithmetic + the shape_salience call over ~1840 short trajectories);
it adds negligible cost to 156000's 87.6 ms/frame value carve, which itself
remains ≈3× over Doom's 28.6 ms/frame budget at down=2 (a declared 156000
residual, unchanged here).

## Architecture audit (CLAUDE.md — the agent is Rust)

- **The dominant-mode gain** is a mechanical flow-histogram peak (numpy
  `np.unique`/`argmax` over an array the world adapter extracted) — the peer of
  `vector_field` / `quantize`. No conditional over graph state, no agent
  decision.
- **The cancellation** is arithmetic (`observed − egomotion`); **the apparatus
  fold** is 155000's mechanical zero-observed-flow readout.
- **The salience** is the EXISTING Rust `memory::order_n_shape_salience`, called
  through `Substrate.shape_salience`. NO Rust added, NO re-implementation.
- **The tracker** is the EXISTING mechanical `_collect_tracks` (nearest-overlap),
  reused verbatim from 156000.
- **The carve** is 156000's `run_value_carve` (= the shipped `native.segment`),
  reused verbatim.
- **`capture_e1m1`** is a world adapter (mechanical I/O over the real WAD); the
  scripted walk is a known world-adapter fact (imported from 156000).
- **The labels buffer** is the SCORING ORACLE, never fed to the eye. Scoring is
  IoU/position + salience rank, never cross-process region-id.

No Python agent decision anywhere. No seed consumed for graph data; block
157000-157999 reserved for the VizDoom seed + RNG base only.

## WHAT I GOT WRONG

- **I predicted the E1M1 fg-vs-bg AUC would IMPROVE over 0.588. It did not
  (0.563).** I under-weighted that E1M1's walk is FORWARD, not a pure turn.
  Forward translation makes optic flow DEPTH-DEPENDENT, and a single dominant-mode
  vector — however robustly captured — cannot cancel a depth-varying field. The
  egomotion-capture stage works perfectly; it is the uniform-cancellation
  assumption (inherited from 155000's rotation model) that does not hold on a
  translating walk. The right next mechanism is a depth-parameterised / per-region
  flow model, which is a NEW pre-registration, not a tune of this one.
- **I predicted the apparatus would STAY demoted (AUC ≥ 0.70). It collapsed to
  0.519.** I assumed the view-fixed apparatus would keep a flat trajectory the
  fold protects. On the real carve its centroid JITTERS (mean step 1.24), so the
  one-pixel fold fires only 37% of the time and cancellation actively PROMOTES it.
  The fold threshold that falls out for a clean field is wrong for a fragmented
  one — the carve noise, not the egomotion model, is the culprit here.
- **My synthetic raw AUC came out 0.00, not the predicted 0.5–0.6.** The proviso
  broke in the "helpful" direction (a STRONGER reproduction of the failure)
  because my synthetic mover moves SLOWER than the egomotion background; in E1M1
  the two are comparable, so E1M1's raw sits at ~0.55. The synthetic proves the
  mechanism but is not perfectly E1M1-faithful in the raw-baseline magnitude — I
  should have matched the mover/egomotion speed ratio to E1M1's.
- **The honest lesson (the arc's standing rule, re-earned): synthetic-proven
  mechanism ≠ benchmark value.** The pipeline is CORRECT for uniform (rotational)
  egomotion (H1: AUC 0.00 → 1.00) and its first stage WINS on E1M1 (egomotion
  captured, extreme outlier cancelled 2256 → 60, items lifted), but the
  end-to-end attention ranking does not improve on E1M1's forward-walk carve.
  Both reported.

## Bounds (§8)

- H1 is a constructed ideal oracle (uniform egomotion), not a sampled effect —
  it proves the mechanism is correct, not that it is valuable on real data.
- H2 is one map (E1M1), one skill (3), one seed (156000), one scripted walk, one
  grid (down=2). The AUCs are over the carved-region tracks of the VALUE carve; a
  different carve would track different regions.
- The residual demotes the LOUDEST background (outlier max 2256 → 60) and lifts
  the foreground items, but does not clear the centroid-only raw fg-vs-bg
  baseline and breaks apparatus demotion — no CI-free positive on E1M1.
- The sub-pixel imp (0 tracks at down=2) makes enemy-promotion untestable — a
  separate, named wall.

## Proposed VISION_PROTOCOL.md ledger row

- **THE EFFERENCE→RESIDUAL→SALIENCE ATTENTION PIPELINE IS PROVEN ON UNIFORM
  EGOMOTION AND ITS GAIN-CAPTURE STAGE WINS ON E1M1, BUT THE FORWARD-WALK
  DEPTH-DEPENDENT FLOW DEFEATS A SINGLE-VECTOR CANCELLATION (2026-07-23,
  `VISION_RESIDUAL_SALIENCE_PREREG.md` / `VISION_RESIDUAL_SALIENCE_RESULTS.md`,
  rung commit `<HASH>`, NO seeds consumed, engine
  `3a66c0636a98e9500a73ac0acbe46d53db3fab79c6231c6c0ecdb7482f54fe60`
  shared/source-matched/NO-Rust, base `main` HEAD `f38863faba`).** GENERAL
  capability: attend to the world's surprise AFTER cancelling the self —
  surprise = residual, so salience runs on the efference-cancelled residual. THE
  FIX composes existing pieces: a DOMINANT-MODE egomotion gain (flow-histogram
  peak over the moving cells) → cancel (155000's efference carve + apparatus
  fold) → the EXISTING `Substrate.shape_salience`. **H1 (synthetic, ideal
  oracle):** the mode recovers `E=(0,6)` at 30%/42% coverage where the median
  reads (0,0); RESIDUAL salience lifts fg-vs-bg AUC **0.00 → 1.00**, mover 13th →
  **top-1**, apparatus demoted — mechanism PROVEN; all three controls (no-ego
  no-op, static→flat, mover-no-ego unchanged) pass. **H2 (E1M1, GT-scored):** the
  dominant-mode gain CAPTURES the egomotion (**154/159 frames nonzero vs
  155000's median 1/159**) and cancels the loudest background outlier (max **2256
  → 60**) and lifts items (median 2.59 → 4.34) — but the end-to-end ranking does
  NOT improve (fg-vs-bg 0.585 centroid-raw → **0.563**) and apparatus demotion
  COLLAPSES (0.679 → **0.519**), a diagnosed DEGRADE: E1M1 is a FORWARD walk
  (depth-dependent translational flow, bg step median 1.68 / p90 4.61 vs a single
  global mode) that a uniform vector cannot cancel, and the jittery carve (app
  step mean 1.24) defeats the one-pixel apparatus fold; the sub-pixel imp is 0
  tracks (the named separate wall). Gate `tests/test_residual_salience_migrated.py`
  **8/8** (H1 gain-recovery + mover-above-bg able-to-fail; three controls; H2
  egomotion-captured + sub-pixel degrade; skips if WAD/VizDoom absent), 3/3 H1
  headline stable across fresh processes. **§9: vision bench 222/0 both sides; NO
  Rust, NO seed, no default moved.** `SEED CLAIM 157000-157999 CLEAN`.

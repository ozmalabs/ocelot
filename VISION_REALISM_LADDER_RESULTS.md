# THE REALISM-DEGRADATION LADDER — is real-video free-fall physics blocked by the CLIP or the METHOD?

**Block 150000-150999.** Base `main` HEAD `132b1aa8b3`, branch
`gamma-substrate/realism-degradation-ladder`. Engine `64dbce1e7f47`,
`source_match: shared` (NO Rust added), `ambiguous: false`.

`SEED CLAIM 150000-150999 CLEAN`

## §3 pre-registration + `check_claim` verdict (verbatim, clause 8)

```
SEED CLAIM 150000-150999: CLEAN -- no collision DETECTED.
  Scope: 851 files with seed sinks; 571 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

**Hypothesis (two-sided).** The chain 145000-149000 proved every mechanism
synthetically but the real free-fall clip never recovered a physical
acceleration; 149000's killer diagnostic was two overlapping windows of the same
real fall recovering OPPOSITE-SIGN acceleration (+1 vs −2). This rung isolates
WHICH realism property breaks the method by degrading the ideal sub-cell oracle
one axis at a time to its breaking point, then locating the real clip on each
axis. Predicted (in advance) suspects, unordered: motion blur, ruler occlusion,
short trajectory (7 frames), noisy carve anchor, low contrast.

**Statistic (the PHYSICS criterion — §13-clean, = 149000's replication test).**
A genuine free fall has ONE constant acceleration of ONE SIGN. The method
"recovers physical acceleration" on a degraded oracle IFF (binding, tolerance-free):
- **P1 (order+sign):** the full run mints order-2 with nonzero graph coeff of the
  correct sign (downward ⇒ `target_fine > 0`);
- **P2 (replication):** TWO overlapping windows (frames `[0:N-1]` and `[1:N]`)
  each mint order-2 with nonzero coeff and AGREE IN SIGN — the exact test that
  killed 149000.

`PASS = P1 ∧ P2` (tolerance-free). A magnitude corroboration **P3**
(`|coeff_full − target_fine| ≤ TOL_FINE`) is reported alongside; `TOL_FINE = 2`
finer units **falls out** (§13), it is not tuned: the position stream is INTEGER
finer units, so each true position rounds to ±0.5 finer unit and a single second
difference `d2 = [1,−2,1]·p` has worst-case rounding error `0.5·(1+2+1) = 2`
finer units. The break point on an axis = the smallest degradation level at which
`P1 ∧ P2` first fails.

**Decision rule.** Report the per-axis break point (the swept level at which the
oracle stops recovering single-sign physics), then measure the real clip's actual
value on each axis and name the axis/axes it is PAST the break on. A null (no axis
past the break in range) would mean the wall is a compound / interaction effect.

**Declared §13 residuals (swept, never tuned):** finer unit `S=10`, residual
half-window `search_cells=3` (both inherited UNCHANGED from 149000);
`a_cell=0.2` (⇒ `target_fine=2.0`), `base_n=8`, `texseed=150000`,
`seed_noise=150100`, `seed_jitter=150200`; the level lists below. Nothing tuned
against the answer — the success criterion is physics (single-sign), not a
threshold.

## Oracle unmoved (§9)

| bench | result |
|---|---|
| `rung7_vision_bench.sh` BEFORE | **222 passed, 0 failed** (169.2s) |
| `rung7_vision_bench.sh` AFTER  | **222 passed, 0 failed** (169.2s) |

`data/` symlinked. **New-files-only** (`git status`: zero modified/staged tracked
files) ⇒ the coarse carve / physics / seed / Rust path is **byte-identical by
construction**; the oracle, sub-cell registration and robust witness are all
imported UNCHANGED from the 149000 modules.

## PRIMARY — the per-axis break-point ladder (the deliverable)

The ideal sub-cell oracle (`render_subcell_fall`, a known sub-cell parabola the
method solves EXACTLY: clean recovers `coeff = 2 = target_fine`) degraded toward
the real clip along ONE axis at a time. `full`/`A`/`B` are the graph-minted order-2
coefficients (finer units) for the full run and the two overlapping windows.

| axis | swept levels (unit) | break point (first `P1∧P2` fail) | reading |
|---|---|---|---|
| **A. trajectory length** | 12,10,8,7,**6**,5 frames | **N = 5** (6+ pass) | needs ≥ 6 frames; coeff drifts 2→3 at N=6-7 |
| **B. motion blur** | 0,1,2,3,4,6 rows | **none in range** | most ROBUST — symmetric blur cancels (both frames blurred) |
| **C. occlusion** | 0,**2**,4,6,8,12 rows | **2 rows** (smallest nonzero) | MOST SENSITIVE — any static occluder in the template breaks window-B |
| **D. contrast / noise** | 0,10,20,40,80,**120** σ | **σ = 120** | robust to σ ≤ 80; σ=120 flips window-B sign (−1) — 149000's exact failure |
| **E. carve-anchor jitter** | 0,1,2,**3** cells | **none in range** | absorbed by `search_cells=3`; coeff drifts 2→1 at ±3 |

Full per-level rows are in `results/realism_ladder_measure.json`. The two-window
SIGN disagreement (149000's killer) is what fails on C and D; short-N (A) fails by
window-B not minting order-2 at all (`winB=None`).

**Occlusion is the most sensitive axis by a wide margin** — it breaks at the
smallest nonzero level tested, while blur and anchor-jitter do not break at all in
range, and noise only breaks at an extreme σ=120.

### Occluder-model residual (declared, honest)

The occluder is a STATIC bar of value 255 the ball passes behind — brighter than
the texture (64-255), so the `count`-brightest template locks onto it, corrupting
the SAD match wherever the ball reaches the bar. This is the worst-case occluder;
a darker ruler would break at a larger width. The *qualitative* finding — a static
occluder intruding on the tracked template breaks the two-window replication — is
robust to occluder contrast; the *exact* break level (2 rows) is contrast-dependent.

## PRIMARY — locating the REAL 149000 clip on each axis (the answer)

Real clip `gravity_freefall_ruler_E6jv9WTcgEQ.mp4`, 149000's primary config
(128×640, block 6, 2 fps). Carve ids are a cross-process HashMap artifact, so this
block is **informational**; the ladder headline above is the deterministic
anchor-given oracle.

| axis | real-clip value | its break | PAST the break? |
|---|---|---|---|
| **A. trajectory** | **7 frames** | 5 | **No** (2 above — but MARGINAL; coeff already drifting at 6-7) |
| **B. blur / velocity** | 6.3 mean / **8.0 max** cells·f⁻¹ | none ≤ 6 | **under-swept** — real velocity exceeds the max swept blur (6), but blur showed ZERO in-range degradation trend ⇒ unlikely primary |
| **C. occlusion** | **RULER PRESENT** (named clip; carve-count CV = 0.131) | 2 rows | **YES** — the clip contains a ruler; occlusion breaks at the smallest nonzero level |
| **D. contrast** | **0.414** (high) | σ=120 | **No** (contrast is high; break needs extreme noise) |
| **E. anchor jitter** | **0.78** cells std (1.40 max) | > 3 | **No** (well inside the residual window) |

**Real-clip replication test (149000's killer, reproduced):**
`coeff_full = None`, `winA = +1`, `winB = None`, `P1 = P2 = False`, **PASS = False**
— the full run and window B mint no order-2 at all while window A mints a weak +1;
i.e. the windows DISAGREE, the registration-noise signature.

### The identified culprit

**The real clip is PAST the break point on OCCLUSION (the ruler)** — the axis that
breaks at the smallest degradation, and the one physical feature the clip is named
for. Trajectory length (7 frames) is a **secondary margin-eroder**: it is only 2
frames above its own break of 5, and the oracle coeff is already drifting (2→3) at
N=6-7, so a 7-frame fall has almost no redundancy for the robust witness to reject
the occlusion-induced registration noise. Contrast (0.414), anchor jitter (0.78
cells) and motion blur (no in-range degradation) are each comfortably NOT past
their breaks.

**Cross-check with 149000's sign-flip (required):** consistent. Occlusion breaks by
corrupting the tracked template ⇒ registration noise ⇒ an unstable order-2 that is
absent in some windows and sign-flipped in others (my occlusion axis kills window-B;
my noise axis flips window-B to −1; the real clip shows full=None/winA=+1/winB=None).
149000's +1/−2 opposite-sign windows are the same registration-noise disease this
occluded, 7-frame clip produces — an unstable coefficient, not physical g.

### Fix verdict

The primary culprit — **occlusion by the ruler** — is fixable by **CLEANER
FOOTAGE** (a fall with no occluder), NOT a new mechanism. The secondary
margin-eroder (short trajectory) is also a footage property (a longer clean fall /
higher fps). **So the indicated fix is cleaner footage, not appearance-tracking or
a new mechanism — with the caveat the secondary run below establishes.**

## SECONDARY (best-effort) — one cleaner real clip

PRE-REGISTERED: report whatever is acquired, at most 2 candidates chosen by
description, no cherry-picking. Two acquired via `yt-dlp`:

- **Candidate 1 `WcS8gyPrRCA` — REJECTED as unclean** on inspection: a
  "shutterstock" watermark sits across the fall path and the ball is HIT by a hand
  (lateral, not a clean vertical free fall). Frame saved:
  `results/clean_clip_frames/cand1_rejected_watermark_hand.png`.
- **Candidate 2 `1yT0hxplVBg` — the clean one:** a bright yellow tennis ball on a
  plain black background, static camera, single object, NO ruler, slow-motion
  bounce (the downward approach to impact IS a genuine free fall). Frame saved:
  `results/clean_clip_frames/cand2_clean_tennisball_black_bg.png`.

Ran the FULL pipeline (carve + track + sub-cell registration + robust witness) on
the longest strictly-downward monotonic run (the free-fall phase) across 3
pre-declared decode framings.

| trial | grid/fps | longest track run | free-fall (downward) run | physics |
|---|---|---|---|---|
| 0 | 160×90 @30 | 2 | 1 | — (run < 6) |
| 1 | 214×120 @30 | 3 | 1 | — (run < 6) |
| 2 | 160×90 @30 (ss=4) | 5 | **5** | — (run < 6, by ONE frame) |

**Outcome: the clean clip did NOT land real free-fall physics — and the reason is
NOT the ruler.** The occlusion culprit is gone (no ruler, contrast 0.41+), but the
common-fate carve+track FRAGMENTED the slow-motion bounce into runs of ≤ 5 frames,
below the 6-frame witness floor. **Cleaner footage removes the occlusion wall and
exposes the NEXT wall: carve/track robustness on a slow-mo single object.** So the
honest synthesis is: cleaner footage is NECESSARY (it removes the measured
culprit) but NOT SUFFICIENT on the one clip acquired — landing real free-fall
physics needs clean footage AND a carve/track that yields a long-enough monotonic
run. n = 1 clean clip; this is not a claim about clean footage in general.

## Invariant audit (§ frame/continuum) — PASS

- Sub-cell precision lives ONLY in the cross-frame integer offset:
  `register_residual_offset` returns `cdr*S + bsy` / `cdc*S + bsx` — **finer-unit
  INTEGERS** (`domains/subcell_register.py`, unchanged).
- NO float is written into any in-frame coordinate: given anchors are
  `float(round(true_top))` (integer-valued); `jitter_anchors` is
  `float(int(round(cy)) + j)` (integer); `cx = float(GW//2)` (integer). The
  degradation renderers (blur / occlusion / noise) operate on GREY VALUES (pixels),
  never coordinates. `carve_cy_float` in the real-clip block is a reported datum,
  never fed to the witness (the witness gets the finer-unit integer position stream).
- No agent decision in Python: `grep` over both new scripts shows zero
  `add_node`/`add_edge`/`make_rule`/`.run(`/`_match`/`_apply`; every order-N verdict
  comes from `graph_mint` (the seed rule) read via `accel_coeff` (the graph mint).

## Gate (§ discipline 8)

`tests/test_realism_ladder_migrated.py` — 6 tests, asserting the break-point
STRUCTURE on the deterministic anchor-given oracle (never the carve): clean N=8
PASSES the single-sign replication (positive control); occlusion=12, noise σ=120
and N=5 each FAIL (negative controls, able to fail if the method became robust);
N=6 still passes (pins the break at 5); blur=6 and jitter=±3 still pass (the
robust axes). Every verdict reads the GRAPH-MINTED coeff via `accel_coeff` — no
exact-`d2`-constancy assertion (148000's flaky-gate lesson).

**Cross-process stability:** run in **3 fresh `python3 -m pytest` processes** →
**6/6, 6/6, 6/6** (identical; the ladder headline is anchor-given, so no carve-id
HashMap artifact enters).

## WHAT I GOT WRONG

- **149000 concluded "the wall moves to trajectory length." That is not the primary
  culprit.** On the ideal oracle a 7-frame fall PASSES cleanly (the break is at
  N=5); the real clip's 7 frames is 2 above its break, a margin-eroder, not the
  wall. The wall is **occlusion** — a suspect 149000 named but did not isolate. The
  degradation ladder was needed to separate "close to the break" (trajectory) from
  "past the break" (occlusion).
- **I would have guessed motion blur was a prime suspect** (the real ball moves
  6-8 cells/frame). The ladder INVERTS this: symmetric motion blur is the single
  most ROBUST axis (no break through 6 rows) because both frames are blurred
  equally and the SAD template match is largely blur-invariant.
- **"Cleaner footage fixes it" was too strong.** The clean clip I acquired removed
  the occlusion culprit and STILL did not land physics — the carve/track fragmented
  it. Cleaner footage is necessary but exposed the next wall; the naive expectation
  that one clean clip would land real free-fall physics was wrong.
- **Occluder-model honesty:** my occluder is a worst-case bright bar; the exact
  break level (2 rows) is contrast-dependent (declared above), though the direction
  of the finding is robust.

## Proposed VISION_PROTOCOL.md ledger row (do NOT merge — for the merge to add)

- **THE REAL FREE-FALL CLIP IS PAST THE BREAK POINT ON *OCCLUSION* (THE RULER), NOT
  TRAJECTORY LENGTH — AND A CLEAN CLIP EXPOSES THE NEXT WALL, CARVE/TRACK
  FRAGMENTATION (2026-07-23, `VISION_REALISM_LADDER_RESULTS.md`, block
  150000-150999, engine `64dbce1e7f47` shared/NO-Rust `source_match`, base `main`
  HEAD `132b1aa8b3`).** The 149000 ideal sub-cell oracle was degraded one axis at a
  time to its breaking point under the single-sign replication test (149000's
  killer): **occlusion breaks at the SMALLEST nonzero level (2 rows — most
  sensitive), trajectory at N=5 (6+ pass), sensor noise only at σ=120, and motion
  blur (≤6 rows) + carve-anchor jitter (≤±3 cells) DO NOT break.** The real 149000
  clip sits at trajectory 7 (2 above break — marginal, NOT past), contrast 0.414
  (high, not past), anchor jitter 0.78 cells (not past), velocity 6-8 cells·f⁻¹
  (blur under-swept but zero in-range trend) — and it CONTAINS A RULER (occlusion,
  break-at-2, carve-count CV 0.131): **the culprit is OCCLUSION, fixable by CLEANER
  FOOTAGE, not a new mechanism.** The replication test reproduces
  (real full=None/winA=+1/winB=None, PASS=False; the +1/−2 sign-flip is the same
  registration-noise disease). **SECONDARY (n=1):** a clean bright-ball-on-black clip
  (no ruler, contrast 0.41, static camera) did NOT land physics — carve+track
  fragmented the slow-mo bounce into ≤5-frame runs (below the 6-frame witness
  floor), exposing carve/track as the next wall (cleaner footage necessary, not
  sufficient). **INVARIANT:** sub-cell precision only in the cross-frame integer
  offset, no float in any in-frame coordinate (audited). Gate
  `tests/test_realism_ladder_migrated.py` **6/6, cross-process stable 6/6 in 3
  fresh processes**. §9: vision bench **222/0 both sides**, new-files-only ⇒
  coarse/physics path byte-identical. `SEED CLAIM 150000-150999 CLEAN`.

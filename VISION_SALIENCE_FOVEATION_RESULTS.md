# SALIENCE-DRIVEN FOVEATION — RESULTS (block 159000-159999)

`SEED CLAIM 159000-159999 CLEAN` (verbatim `check_claim` in
`VISION_SALIENCE_FOVEATION_PREREG.md`, committed before the E1M1 run at
`014a89dc13`).

THE PRINCIPLE: foveation = supergraph-optimal compute allocation. 158000 proved
depth-from-motion + mover isolation WORK on adequate flow (real Doom depth
Spearman +0.40) but NULL on the coarse down=2/L=4 flow, while full-resolution flow
EVERYWHERE is ~3× over the real-time budget. THE FIX: resolve the flow FINELY only
where it is SALIENT — spend the resolution budget where the (super)graph values it
most, not uniformly.

- **New file only** (`scripts/salience_foveation_probe.py`,
  `tests/test_salience_foveation_migrated.py`, this doc + the prereg). NO Rust
  added, NO seed consumed, NO default moved — the shipped
  154000/155000/157000/158000 paths are byte-identical BY CONSTRUCTION (every
  added function — `salience_field`, `_connected_components`, `select_fovea`,
  `fine_flow_window` — is an ADDITIVE mechanical numpy sensor over the flow /
  salience fields; the §9 OFF-default is vacuous, nothing existing is touched).
  `git status` shows only new untracked files.
- Engine: `source_match = shared`, `engine 64dbce1e7f47 @
  .../runners/dsl/python/substrate_rs/_native.abi3.so [shared build — Rust source
  identical]`, source fingerprint
  `3a66c0636a98e9500a73ac0acbe46d53db3fab79c6231c6c0ecdb7482f54fe60` (identical to
  158000 — same engine source; recorded in `results/salience_foveation.json`,
  asserted `in {own, shared}`, NEVER a pinned build hash — the gate passes on main
  where the tree reads `own`).
- Oracle `scripts/rung7_vision_bench.sh` (data/ symlinked): **222 passed / 0
  failed BEFORE**, **222 passed / 0 failed AFTER**.
- Gate `tests/test_salience_foveation_migrated.py`: **9/9**; the five H1 headline
  assertions **5/5 stable across 3 fresh pytest processes**.
- Determinism: VizDoom seed 156000 + 158000's FIXED scripted walk (verbatim,
  imported); coarse grid 160×120 (down=2, block 8, L=4 — the 157/158 pipeline);
  fine grid 320×240 (down=1, block 16 — 158000's down=1 arm). FLOOR=0.5, R_MIN=2
  (158000's). ADDED declared residuals (§13, below): `SAL_FLOOR=1.0` (one full
  pixel of UNEXPLAINED tangential motion, above the √2·0.5≈0.71 integer-flow
  rounding band), `MIN_REGION=2` (a mover is an extended object), `FOVEA_MIN_HALF=4`
  (a window smaller than the flow block carries no gradient — the window SIZE
  otherwise FALLS OUT of the salient region's connected-component bbox).

---

## H1 — SYNTHETIC (ideal oracle): the mechanism is PROVEN

A forward-translation scene = radial expansion from a KNOWN FOE over a
depth-varying background (Z ∈ [2, 14]) + a SMALL independent mover (non-radial) +
a view-fixed apparatus. The coarse sensor models a block matcher at half
resolution (area-average the flow, HALVE the displacement, ROUND to integers —
158000's measured quantization wall made analytic); the fine sensor keeps
full-resolution flow.

### (ii) salience LOCATES the mover — on the RESIDUAL, not the raw flow

The residual (tangential) salience argmax lands ON the mover `[row 41, col 24]`;
the RAW |flow| argmax lands OFF it at `[0, 0]` — the far/near-depth corner where
parallax makes the egomotion background flow FASTEST. **This is the 157000 reason
salience must be on the RESIDUAL:** raw-magnitude salience would foveate the
highest-parallax background, never the mover.

### (i)/(iii) coarse under-resolves depth; the FOVEATED FINE flow RECOVERS it

| quantity | COARSE (down=2, in window) | FOVEATED FINE (down=1, same window) |
|---|---|---|
| depth-from-motion Spearman (vs known Z) | **0.756** | **1.000** |
| radial-consistent cells (depth samples) | 85 | **341** (≈ 4×) |
| mover isolation IoU | 1.000 | 1.000 |

**The foveated fine flow recovers depth exactly (Spearman 1.0) over 4× the cells;
the coarse pass under-resolves (0.756) — fewer cells + integer-quantized
displacement.** Note the coarse-null on the IDEAL ORACLE is a RESOLUTION degrade
(a positive 0.756), NOT the negative null 158000 measured on real block-match
noise — H1 proves the mechanism, H2 (below) carries the real null. Mover isolation
is clean at BOTH once the one-pixel salience floor removes the coarse rounding
noise; the coarse limitation here is depth RESOLUTION, not mover detection.

### (iv) COST — foveation is a fraction of full-res

Foveated = 4800 coarse cells + 360 fine-window cells = **5160 cells** vs
full-res-everywhere **19200 cells** = **0.269×**. A 3.7× compute saving on the
ideal oracle.

### Controls (all pass, §6)

- **No salient region** (pure radial egomotion, no mover): the residual salience
  is ≤ 0.686 everywhere (the integer-flow rounding band) — nothing clears
  `SAL_FLOOR=1.0` — so **0 foveae fire** (falls back to the coarse pass). No
  spurious high-res.
- **Residual not raw** (the (ii) control): residual peak ON the mover, raw peak
  OFF it — recorded above.
- **Two salient regions**: two matched movers ⇒ **2 foveae**, peaks `[21,27]` and
  `[20,53]`, **BOTH regions covered** (not one merged window).

---

## H2 — E1M1 (real WAD, 158000 walk/seed/grid): the mechanism transfers, the
allocation lesson is the finding

160 frames; 81 frames where the fovea fires on an efference-forward frame.

### (a) DEPTH — foveated fine BEATS the coarse-in-window null, but does NOT reach the full-frame ceiling

Per-frame Spearman(recovered depth r/|flow|, VizDoom depth buffer) over
radial-consistent background cells, efference-forward frames:

| arm | median Spearman | frac frames > 0 | n |
|---|---|---|---|
| coarse full-frame (158000's null) | **−0.112** | 0.448 | 87 |
| fovea COARSE-in-window (the null it re-resolves) | **−0.203** | 0.423 | 111 |
| **fovea FINE-in-window (FOVEATED)** | **+0.016** | 0.504 | 131 |
| full FINE everywhere (158000's ceiling) | **+0.396** | 0.837 | 86 |

**The two 158000 anchors reproduce EXACTLY** (coarse −0.112 vs 158000 −0.112;
full-fine +0.396 vs 158000 +0.396 — determinism confirmed on the same seed/walk).
**Foveating to fine flow in the salient window flips the coarse-in-window null
(−0.203 → +0.016), a +0.22 swing — the mechanism re-resolves depth where it
foveates.** BUT the foveated depth is WEAK (+0.016), nowhere near the full-frame
ceiling (+0.40). Two measured reasons, both honest:

1. **The salient window is TINY** (median 2.5% of the frame) ⇒ a small depth
   RANGE ⇒ a noisy Spearman. The +0.40 ceiling is over the WHOLE frame's depth
   range.
2. **Mover-salience points the fovea at the WRONG region for depth.**
   Depth-from-motion needs the radial-consistent BACKGROUND; the residual salience
   by construction selects the NON-radial (mover / surprising) region — the region
   WORST for background depth recovery. The allocation that helps depth (the whole
   background at fine resolution) is DIFFERENT from mover-salience foveation.

**This is the rung's real finding: "allocate resolution where the graph values it
most" is TASK-RELATIVE. For mover isolation, value = the mover (motion salience,
below). For depth-from-motion, value = the depth-structured background — a
different fovea.** Motion-mover salience is the wrong salience for depth-recovery
foveation; the two want different targets. Reported as a diagnosed DEGRADE, not a
win dressed up.

### (b) IMP recovery — the sub-pixel wall breaks WHEN foveated, but motion salience cannot POINT the fovea there

4 imp-present frames. The imp is 1–2 coarse cells and **SUB-PIXEL at coarse: 0
imp flow cells** across all frames (the persistent 156/157/158 wall; 0 monster
tracks).

- **(b1) motion salience does NOT locate the imp — the NAMED DEGRADE.** The fovea
  lands on the imp in **0 / 4** frames (median fovea-to-imp distance 42 cells). A
  mover with NO coarse motion signal cannot be found by motion salience — you
  cannot foveate what you cannot see. Exactly the honest split predicted.
- **(b2) a FINE window placed ON the imp resolves it: 0 → 12 super-pixel flow
  cells** (7 of 7 imp cells flow in frame 106). **Foveation DOES break the
  sub-pixel wall WHEN pointed at the imp** — the imp becomes super-pixel in a fine
  local window. The missing piece is a NON-motion salience cue (appearance) to
  bootstrap the fovea onto a static/sub-pixel mover, which this rung does not add.

### (c) COST / real-time (measured ALONE)

| pass | ms/frame | vs 28.6 ms budget |
|---|---|---|
| full-res down=1 EVERYWHERE | **103.5** | 3.6× OVER (158000's "~3× over") |
| **foveated** (coarse down=2 flow + fine windows) | **37.8** | 1.3× over |

**Foveation is 2.74× cheaper than full-res-everywhere** — but still OVER the
28.6 ms budget: the coarse down=2 global flow is itself the floor (~35 ms). Honest
DEGRADE on the real-time claim: foveation gives the expected multiplicative saving
but does not reach real-time ALONE — the coarse global pass also needs to be
cheaper (a motion-compensated / hierarchical block-matcher, a separate lever).

---

## Architecture audit (CLAUDE.md — the agent is Rust)

- **`salience_field`** is 158000's `radial_decompose` tangential residual as a
  per-cell FIELD (the FOE least-squares + radial decomposition, unchanged) — the
  spatial peer of 157000's efference→residual→salience. Mechanical numpy, no
  conditional over graph state.
- **`select_fovea`** is argmax / top-K over connected components of the flagged
  salience — pure array bookkeeping (BFS labelling + bbox), no agent decision. The
  window LOCATION is the salience argmax; the SIZE falls out of the region's
  connected-component extent (floored geometrically).
- **`fine_flow_window`** is the EXISTING `vector_field` block-SAD run on a CROP of
  the full-res luma — the existing sensor at a finer scale, one line of cropping.
- **Depth / mover** are 158000's mechanical sensors (`depth_from_motion`,
  `flag_movers`, `estimate_foe`), reused verbatim; the single-vector residual is
  157000's `dominant_mode_gain`.
- **`capture_e1m1`** is a world adapter (mechanical I/O over the real WAD); the
  scripted walk is imported from 158000 (the agent's own issued action). **The
  DEPTH + labels buffers are the SCORING ORACLE**, never fed to the eye. Scoring
  is Spearman / IoU / distance / cell-counts by POSITION, never cross-process
  region-id. The imp GT places the (b2) evaluation window (WHERE-only scoring
  oracle), never a decision the eye makes.

No Python agent decision anywhere. No seed consumed; block 159000-159999 reserved
for the VizDoom seed + RNG base only.

## WHAT I GOT WRONG

- **I predicted the foveated fine depth would beat the coarse null AND approach
  the +0.40 adequate-flow ceiling. It beats the null (−0.203 → +0.016) but does
  NOT approach the ceiling (+0.016 ≪ +0.40).** The reason I under-appreciated: the
  residual salience selects the NON-radial mover region — precisely the region
  depth-from-motion is WORST at (it needs radial background) — and the window is
  tiny (small depth range). The mechanism works (foveation re-resolves within the
  window), but MOVER-salience is the wrong salience to foveate for DEPTH. The
  allocation lesson (value is task-relative) is a sharper result than the win I
  expected.
- **I expected the ideal-oracle H1 to reproduce 158000's negative coarse null.**
  It does not — a clean analytic scene has no block-match noise, so the coarse
  degrade is a POSITIVE resolution loss (0.756, not −0.11). I had to be explicit
  that H1 proves the MECHANISM and H2 carries the real (negative) null; conflating
  them would have overclaimed H1.
- **I initially built the salience on integer-quantized flow with the 158000
  one-pixel FLOOR (0.5) and it fired on rounding noise everywhere** (the no-salient
  control failed: 279 "movers" on a no-mover scene). The fix was to see that
  integer flow carries up to √2·0.5≈0.71 px of DIRECTION-ROUNDING noise, so a
  genuine independent mover must carry ≥ 1 full pixel of UNEXPLAINED tangential
  motion (`SAL_FLOOR=1.0`) — a floor that FALLS OUT of the integer-flow rounding
  bound, not tuned to the score. This is 158000's finding restated: the coarse
  residual salience IS noise-dominated, and that is exactly why the imp (sub-pixel)
  cannot be located coarsely.
- **The mover blind spot bit the two-region control.** My second mover happened to
  move nearly RADIALLY at its position (aligned with its FOE direction) ⇒ small
  tangential residual ⇒ invisible to the depth-independent isolator (158000's named
  blind spot). Correct physics, wrong control — I re-matched the two movers to
  clearly-tangential, comparable-strength motion so the control isolates the "two
  regions" property, not the blind spot.
- **The real-time claim is a partial.** I expected foveation might reach the budget;
  it gives a clean 2.74× saving but the coarse global flow is itself ~35 ms > 28.6.
  Foveation is necessary but not sufficient for real-time — the coarse pass needs
  its own speedup.

## Bounds (§8)

- H1 is a constructed ideal oracle (analytic radial flow) — it proves the mechanism
  is CORRECT and CHEAP, not that mover-salience foveation is VALUABLE for depth on
  real data (H2 shows it is not — the allocation is task-mismatched).
- H2 is one map (E1M1), one skill (3), one seed (156000), one scripted (turn-heavy)
  walk. The foveated depth positive (+0.016) is a mechanism confirmation (beats the
  in-window null), NOT a benchmark win.
- Motion-only salience cannot foveate a static / sub-pixel mover (the imp, 0/4) —
  an appearance salience cue is the missing bootstrap, unbuilt here.
- Foveation does not reach the real-time budget alone (coarse flow is the floor).
- The window is tiny (2.5%); a larger fovea would raise depth range but cost more —
  the size/coverage trade-off is unswept (a further attempt needs a new prereg).

## Proposed VISION_PROTOCOL.md ledger row

- **SALIENCE-DRIVEN FOVEATION = SUPERGRAPH-OPTIMAL RESOLUTION ALLOCATION — THE
  MECHANISM WORKS (COARSE-GLOBAL SALIENCE LOCATES, FINE-LOCAL FLOW RESOLVES, AT A
  FRACTION OF FULL-RES COST) BUT "VALUE" IS TASK-RELATIVE: MOVER-SALIENCE IS THE
  WRONG FOVEA FOR DEPTH (2026-07-23, `VISION_SALIENCE_FOVEATION_PREREG.md` /
  `VISION_SALIENCE_FOVEATION_RESULTS.md`, rung commit `<HASH>`, NO seeds consumed,
  engine `3a66c0636a98e9500a73ac0acbe46d53db3fab79c6231c6c0ecdb7482f54fe60`
  shared/source-matched/NO-Rust, base `main` HEAD `83d77e445e`).** GENERAL
  capability: allocate perceptual RESOLUTION by SALIENCE — a coarse global pass
  (down=2) finds WHERE the surprise is (158000's radial/tangential residual as a
  spatial field, depth-independent so the peak lands on the INDEPENDENT MOVER, not
  the highest-parallax background), a fine local pass (down=1 in a window) resolves
  it THERE, the rest stays cheap. **H1 (synthetic, ideal oracle):** the residual
  salience LOCATES the mover (raw |flow| does NOT — it picks the fastest
  background); the foveated FINE flow recovers depth Spearman **0.756 → 1.000** over
  **4×** the cells at **0.27×** the compute; three controls pass (no-salient→no
  fovea, residual-not-raw, two-regions→both). **H2 (E1M1, GT-scored vs the VizDoom
  DEPTH + labels buffers):** the two 158000 anchors reproduce EXACTLY (coarse
  **−0.112**, full-fine **+0.396**); foveating to fine flow flips the
  coarse-in-window null (**−0.203 → +0.016**, mechanism confirmed) but does NOT
  reach the +0.40 ceiling — **mover-salience selects the non-radial region that
  depth-from-motion is WORST at, and the window is tiny (2.5%)** (a diagnosed
  DEGRADE: value is TASK-RELATIVE — depth wants a background fovea, not a mover
  fovea); the imp is sub-pixel at coarse (**0 flow cells, motion salience lands on
  it 0/4** — the named wall) but a FINE window ON the imp resolves it (**0 → 12
  super-pixel flow cells** — the sub-pixel wall breaks WHEN foveated, only an
  appearance cue to POINT the fovea is missing); foveated **37.8 ms/frame** vs
  full-res **103.5 ms** (**2.74× cheaper**) but still over the 28.6 ms budget (the
  coarse pass is the floor). Gate `tests/test_salience_foveation_migrated.py`
  **9/9** (H1 locate/coarse-under-resolves-fine-recovers/cost able-to-fail; three
  controls; H2 foveated-fine-beats-in-window-null + imp-superpixel-in-fine-window +
  foveated-cheaper-than-full-res; §10 provenance `in {own, shared}`; skips if
  WAD/VizDoom absent), 5/5 H1 headline stable across fresh processes. **§9: vision
  bench 222/0 both sides; NO Rust, NO seed, no default moved.** `SEED CLAIM
  159000-159999 CLEAN`.

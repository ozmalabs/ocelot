# BBOX + LABEL OVERLAY — PRE-REGISTRATION (seed block 119000–119999)

*Committed BEFORE any gate number. This rung EXTENDS the eye-view splat rung
(118000, `VISION_EYEVIEW_RESULTS.md`, `scripts/eyeview_render.py`) with a
**bbox + label overlay** that renders BOTH channels of the architecture in one
frame: splat = SEEING (the carved surface), bbox = the surface's TRUE carved
extent, label = NAMING (a grounded name, attaching ONLY to an already-carved
percept). It adds the KILLER FRAME: the eye's honest-holes output beside an
ILLUSTRATION of a can't-refuse net-style selection head.*

## Discipline / provenance (fixed before the run)

- **Branch** `worktree-agent-a39b3d0a592db5a18`; **base SHA** `da113ec4af81`
  (contains `VISION_EYEVIEW_RESULTS.md`, `VISION_SPLATTING_SCIENCE.md`,
  `VISION_REFUSAL_CAPACITY_RESULTS.md`, the parallax carve, and the
  `ArgminRefusal` Term at enum index 180).
- **NO Rust, NO Term, NO seed rule** — a pure MECHANICAL EMIT-ADAPTER (read
  graph / measurement state → external image), architecture-permitted. Engine
  built in-tree by `scripts/engine_build.sh`: **`7041d2e6a7dd`**; re-verified
  after measurement. Provenance gate its own step FIRST (`7 passed`);
  `ArgminRefusal` confirmed at index 180 on the base.
- **Oracle** `bash scripts/rung7_vision_bench.sh` (`data/` symlinked, §10.2):
  BEFORE **222 passed / 0 failed**; AFTER re-run. §9 is trivial (no Rust, no
  Term, no seed) — the oracle only confirms it.
- **Seeds:** block 119000–119999 ALLOCATED; the rung DRAWS NO SEED in-block —
  the held state reuses the parallax rung's already-burned seed **116000** (as
  the eye-view rung did), the naming-channel grounding is deterministic (a
  fixed local teacher payload, no RNG), and every positive control removes a
  FIXED cell set / a FIXED edge (no RNG). `check_claim(119000,119999)` recorded
  verbatim below. Term enum index 180 remains UNUSED.
- **CPU** ≤2 workers (`OMP_NUM_THREADS=2`); `os.getloadavg()` recorded; NO
  wall-clock quantity is a verdict — every gate number is an exact/counted
  quantity.

```
SEED CLAIM 119000-119999: CLEAN -- no collision DETECTED.
  Scope: 824 files with seed sinks; 513 UNRESOLVED sink sites tree-wide (counted, not discarded).
```

## What the eye HOLDS (recovered by re-running the deterministic seeded carve — the parallax rung's numbers, NOT this rung's gates)

Seed 116000, `shifts=[0,3,6]`, `block=8`, `grid=144`, `ref_idx=1`, `τ=√5`. The
18×18 = 324-cell field carves into **3 surfaces + 9 hole cells** (right-edge
column, the aperture-corner confabulation). Per-surface carved footprint
(measured — held state, same standing as the eye-view rung's recovery):

| surface | residual v (= rel. depth) | image band | n cells | axis-aligned bbox | solid rectangle? |
|---|---|---|---|---|---|
| FAR | −3 | x∈[0,5] | 108 | y0–17 × x0–5 (area 108) | **yes** |
| REF / fixated | 0 (space constancy) | x∈[6,11] | 91 | y0–17 × x6–11 (area 108) | **no** (ragged) |
| NEAR | +3 | x∈[11,17] | 116 | y0–17 × x11–17 (area 126) | **no** (ragged; bbox spills into the hole column) |

This geometry MATTERS for Gate A: a tidied axis-aligned RECTANGLE is LARGER
than the true carve for REF (108 vs 91) and NEAR (126 vs 116). The faithful box
is therefore the surface's exact carved-cell FOOTPRINT, never a rectangle.

## The naming channel (fixed before the run)

The eye has grounded **ZERO object names** — the parallax scene is synthetic
TEXTURE, not objects. The ONE identity the eye genuinely holds is its
**fixation reference**: the middle surface at residual velocity **exactly 0**
(from the efference copy — space constancy; memory: the centre of gaze is the
origin). So the naming channel grounds **exactly one** concept — `reference` —
through the real teacher chain (`WorldAdapter.learn_from_teacher`, a fixed local
payload = the teacher's decision) and attaches it via a `Mention -refers_to->
Concept` edge to the surface the eye ALREADY carved as its reference plane. The
other two surfaces get a `Mention` with **NO** `refers_to` (seen-but-unknown —
the residual grounding acts on). Grounding an EXTERNAL object name onto texture
would be INVENTING a name (forbidden); the fixation reference is the only
honest grounding available, and it is marked as such in the frame.

## THE FOUR PRE-REGISTERED GATES + DERIVED TOLERANCES

**Gate A — BBOX = TRUE CARVED EXTENT.** Statistic: for each carved surface,
IoU(drawn-box cell-set, carved cell-set). The drawn box is the surface's exact
carved-cell FOOTPRINT. **Derived tolerance: IoU == 1.0 EXACT** (tolerance 0 —
the box IS the carved cells; the strongest §13 no-number outcome). TEETH:
(i) a tidied axis-aligned RECTANGLE box scores IoU = n/bbox_area < 1.0 on any
non-solid surface (predicted REF 91/108 = 0.843, NEAR 116/126 = 0.921) and
FAILS — a tidier box is caught; (ii) SHRINK — deterministically remove a fixed
half (even columns) of a surface's carved cells; the re-derived footprint box
covers exactly the shrunk cells (IoU 1.0 to the shrunk carve) and its cell-count
drops. **Prediction:** footprint PASS (1.0/1.0/1.0); tidy-rect FAILS on
REF/NEAR; shrink tracks.

**Gate B — LABEL ONLY WHERE GROUNDED.** Statistic: a label renders for surface
s IFF s's `Mention` `refers_to` a `Concept`. **Derived tolerance: rendered-label
count == grounded-surface count == 1 EXACT** (no number). TEETH: (i) the 2
un-grounded surfaces render NO label; (ii) the grounded surface renders its
Concept's grounded FORM (`reference`); (iii) REMOVE the `refers_to` edge → label
count 0; ADD a second → label count 2 — the label tracks the GRAPH edge, not the
renderer. A label on an un-grounded surface or on a hole ⇒ FAIL. **Prediction:**
PASS — exactly 1 label (`reference`) on the fixated surface; 0 on the 2 unknown;
0 on the hole.

**Gate C — NO BOX ON A HOLE.** Statistic: (# of the 9 hole cells covered by any
drawn box, # boxes on the hole, # labels on the hole). **Derived tolerance: 0
EXACT** on all three (composes with the eye-view Gate-1 hole-preservation, splat
coverage 0.000). TEETH: the net-style panel covers all 9 hole cells with a box
(predicted 9/9). **Prediction:** eye 0/9 boxed, 0 boxes, 0 labels on the hole.

**Gate D — THE NET-CONTRAST IS HONEST.** Statistic: box-coverage fraction and
label-coverage fraction of the 324-cell field, EYE vs NET-STYLE. The net-style
panel is an explicit ILLUSTRATION of a can't-refuse discriminative SELECTION
head (`VISION_REFUSAL_CAPACITY_RESULTS.md`: *a comparison can be false, a
selection cannot*) — NOT a measured baseline. **Derived tolerance: net
box-coverage == 1.000 AND net label-coverage == 1.000** (a selection cannot
refuse — by construction it fills every cell with a box and a confident label,
including the hole and the unknown surfaces); **eye box-coverage < 1.0** (holes
uncovered) **AND eye label-coverage < eye box-coverage** (unknown surfaces
unlabelled). Report both coverage DIFFERENCES. **Prediction:** eye box-coverage
315/324 = 97.22%, eye label-coverage 91/324 = 28.09%; net 100%/100%; box Δ =
9/324 = 2.78%, label Δ = 233/324 = 71.91%.

## Decision rule

All four gates PASS ⇒ the two-channel picture is faithful: a name attaches only
to a carved percept (B), the box is the true carved extent not a tidy rectangle
(A), the hole carries neither box nor label (C), and the eye's honest gaps are
seeable against a selection head that structurally never has them (D). Any FAIL
is reported as a FAIL, not rescued (§5). A null on the net-contrast (eye
coverage == net coverage) would refute the headline.

## Prediction provisos (§3 clause 7)

- If any surface's carve were a clean solid rectangle for ALL three, the
  tidy-rect teeth for Gate A would be vacuous — the measured geometry above
  says REF/NEAR are ragged, so the teeth bite. If they did not, I would report
  the footprint==rect coincidence, not claim a caught prettification.
- The box coverage Δ (2.78%) is SMALL because the parallax carve labels almost
  every cell (only the 9-cell hole is refused) — the sharp contrast is the
  LABEL Δ (71.9%), which is the number that makes the refusal law seeable. I
  report both; I do not inflate the box Δ.

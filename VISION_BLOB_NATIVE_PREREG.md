# BLOB-NATIVE SAMPLING — pre-registration

Seed block **80000–80999**. Engine pinned at build time; provenance run as its
own step before any number. Oracle: `scripts/rung7_vision_bench.sh`.

This rung was commissioned on three premises. **Step 0 measured all three
before any building, and two of them are false.** The pre-registration is
written around what was measured, not around what was assumed — and the
corrections are recorded here, BEFORE any headline, so that the rung cannot
later be read as having predicted them.

---

## 0. STEP 0 — what the pipeline actually does

### 0.1 The retina is NOT already producing blob-shaped output

The commissioning note raised the possibility that the retina stage computes
centre-surround responses (blob-shaped by construction) and then flattens them
into a 24×24 array because downstream code expects a raster — in which case the
raster would be an adapter artifact and the fix would be to stop discarding
structure that already exists.

**It is not that.** There is exactly one centre-surround stage,
`domains/lateral_world.py` + `seeds/vision_lateral.json`. It computes **one
`HCell` graph node per retinal cell** — per PIXEL, not per blob — and
`lateral_world.residuals()` (`:169`) flattens those nodes into
`np.zeros((h, w))`. So a raster does appear, but what precedes it is a
per-pixel node field, not a set of blob records. There is **no** peak-finding,
no scale selection, no `(x, y, σ, response)` record anywhere in the tree.
`substrate_rs/vision.py`'s `dog` / `lgn_pair` build dense convolution kernels
and are explicitly rejected by `lateral_world.py:28-30` as the "bolt-on error
PROTOCOL §0 names"; they are not on any measured path.

Consequence for this rung: **blob sampling is new work, not recovered
structure.** The cheap fix does not exist. This is recorded as a cost the rung
pays, not as a finding in its favour.

A second fact, recorded because it bears on any claim about the eye's output:
the assembled eye's percept **terminates in a scalar** —
`float(np.mean(r > floor))` (`scripts/video_probe_measure.py:189`). Nothing
downstream consumes the residual field as a field.

### 0.2 The read-back cost is the OUTSIDE REFERENCE, not the raster

The commissioning note attributed the ~10× read-back cost to "paying to convert
between two representations every frame, one of which nothing needs" — i.e. to
serialising a named grid.

**Measured, on the same adapter (`domains/verdict_comparator_world.py`), and it
is not the raster.** Splitting `VerdictWorld.read()` into its components:

| verdict | n_regions | ρ | graph s | read s | read/graph | ref frac of read | name-parse / graph |
|---|---|---|---|---|---|---|---|
| hamming | 16  | 2 | 1.981   | 0.036 | 0.018 | 0.95 | 1.0e-5 |
| hamming | 36  | 2 | 19.54   | 0.176 | 0.009 | 0.98 | 3.7e-6 |
| hamming | 64  | 2 | 106.96  | 0.569 | 0.005 | 1.00 | 1.1e-6 |
| **ncc** | 16  | 2 | 0.0040  | 0.026 | **6.5**  | 0.96 | 7.2e-3 |
| **ncc** | 36  | 2 | 0.0161  | 0.128 | **7.9**  | 0.97 | 2.6e-3 |
| **ncc** | 64  | 2 | 0.0416  | 0.444 | **10.7** | 0.97 | 3.8e-3 |

(Synthetic frames, one probe per region, this tree's engine. Exploratory —
recorded as an instrument reading, not as a corpus result.)

The ~10× reproduces **exactly**, and its cause is now pinned:

1. The concurrent rung's arm is `ncc`, whose graph-side score is a single
   `Dot` — so **graph time is very small** (0.042 s at 64 regions).
2. `read()` recomputes **two** Python references per group: the arm's verdict
   AND a fixed `hamming` V0 tie statistic (`verdict_comparator_world.py:403`),
   held across arms because *a diagnostic must not be computed by the component
   it checks*. Hamming is a set-overlap over 36 tuples × n_codebook × 25 orbit
   members, in pure Python — and it is **97% of read-back**.
3. The **name parse is ~1e-3 to 1e-5 of graph time**, i.e. ~1e-4 of read-back.

So: read-back is the **verification instrument**, and it is dominated by a tie
diagnostic that the protocol deliberately requires. **Removing the named grid
cannot reduce it.** Under `hamming` the ratio inverts entirely (read-back is
0.5–1.8% of graph and *falls* with scale), which shows the "10×" is a property
of the ARM, not of the representation.

**Pre-registered consequence:** this rung will NOT claim a read-back saving from
removing the raster. It reports the read-back split (parse vs reference) and
states plainly that the raster was not the cost. Gate 1 is therefore assessed on
**graph** cost, with read-back reported beside it and attributed.

### 0.3 Proto-objects never see the region grid

`stage_s3` (`scripts/video_probe_measure.py:352-363`) calls `boot_core()`
**fresh**, loads only `vision_border_ownership`, and feeds
`bow.add_field(s, _quantize(raw_frame, k))`. It does not call `boot_eye`, does
not load `vision_lateral`, and never touches `REGION`/`GRID`/`regions_of`.
`stage_s4` independently confirms the disconnection: *"STRUCTURAL ABSENCE — no
ProtoObject reaches the identity layer"* (`:462`).

So the 0-protos-on-7/7-frames result **cannot** be caused by 6×6 region seams:
there are none in that path. The proto stage does have a raster — `add_field`
builds an H×W `Cell` lattice with 4-neighbour edges — but it is the raw
quantized luminance lattice, and the gates that must pass are **value-flood**
conditions, not tile-boundary conditions (`seeds/vision_border_ownership.json`,
`bo_mint_enclosed`): (2) `bg < 0.5`, where `bg` floods inward from the frame
border along **equal-value 4-adjacency**; and (5) single-ground closure, refusing
any figure bordered by two ground cells with different `glabel`.

This does not make the sharpest test vacuous — a blob decomposition changes the
adjacency graph those floods run on, so it is a real intervention — but it does
change what a null would mean, and that is fixed here in advance (§H3).

---

## 1. Hypotheses

**H1 (cost).** At matched field size and matched sample count, blob-native
sampling reduces **graph** time per frame relative to the square-grid baseline.
Read-back is reported beside it, split into parse and reference, and is NOT
claimed as a saving (§0.2).

**H2 (recognition).** Blob-native recognition does not degrade against a
**re-earned** square-grid baseline. Nothing transfers by assumption: the noise
floors (G2c, G2t) and the A3 arrangement floor are **re-measured** under the
blob representation, because floors move with codebook size and will move with
representation.

**H3 (the sharpest test — proto-objects).** Feeding border-ownership a **blob
adjacency field** instead of the pixel lattice changes the proto count from its
byte-identical 0-on-7/7.

- **Predicted outcome: NULL** (protos stay 0), on the §0.3 reasoning: the
  failing gates are value-flood conditions and a blob field re-runs the same
  floods on a coarser graph.
- **This prediction is registered so that a null is not retrofitted as
  expected.** If protos DO appear, H3 is a positive and the sampling geometry
  was load-bearing after all.
- Either way the result is reported prominently, and the **mechanism** is
  measured, not inferred: the run records, per frame, the fraction of cells with
  `bg = 0` (enclosed at all) and the number of figure components refused by the
  single-ground gate. §0.3's attribution of the null to gates 2 and 5 is
  currently *inferred from rule comments*, and this rung converts it to a
  measurement.

---

## 2. The density profile, and its derivation (§13)

The profile must FALL OUT. It is derived from a **stated principle**, and the
derivation is written here before the code so that it cannot be fitted.

**Principle** (already recorded in this project): *grounding radiates outward
and decays with eccentricity*; and *in-frame is INTEGER* — the sampling limit is
one pixel, because that is what grounding IS.

**Derivation.** Require the sampling to be **self-similar**: a blob at
eccentricity `e` has radius `r(e) = e / κ`, a constant fraction of its own
eccentricity. This is the only scale-free choice; any other exponent introduces
a preferred scale, which the principle forbids.

Impose **isotropy** — radial spacing equals tangential spacing. Then:

- radial: consecutive rings satisfy `e_{n+1} = e_n + 2 r(e_n) = e_n (1 + 2/κ)`,
  so ring eccentricities are **geometric**;
- tangential: blobs per ring `N_θ = 2π e_n / (2 r(e_n)) = π κ`, **constant across
  rings** — which is what self-similarity means.

**Boundary condition** (the sampling limit): the innermost blob cannot be finer
than one pixel, `r(e_1) = 1`, giving `e_1 = κ`. The outer limit is the field
radius `R`.

This leaves **exactly one constant, κ**, and it is **not free**: it is consumed
by the matched-sample-count constraint that gate 1 and gate 2 both require
(blob count N must equal the baseline's region count at matched field size).
Given `(R, N)`, κ is determined; nothing is tuned for performance, and no
per-corpus or per-resolution adjustment is permitted.

### 2.1 CORRECTION to §2, found in implementation (recorded, not silently fixed)

The paragraph above says κ "is consumed by the matched-sample-count constraint".
**That is wrong, and the error is arithmetic, not judgement.** The square arm is
a *complete pixel partition*: 16 regions × 36 cells = 576 = 24², i.e. its sample
count IS the pixel count. Matching total samples therefore means placing one
blob per pixel, which is precisely the uniform sampling the rung exists to
remove. `solve_kappa` cannot reach it (max ≈ 64 blobs at R=11.5), and it should
not.

The honest position, which replaces it:

- What **falls out** (§13 satisfied) is the profile's **SHAPE**: geometric ring
  spacing `e_{n+1} = e_n(1+2/κ)`, constant per-ring count `N_θ = πκ`, and
  `r ∝ e`, all three *forced* by self-similarity + isotropy, with the foveal
  radius pinned at the one-pixel sampling limit. None of that is chosen, and
  none of it is fitted.
- What does **not** fall out is the **SCALE**, κ. Coverage cannot pin it —
  radial and tangential spacing touch by construction at every κ. **κ is the
  blob arm's resolution parameter, exactly as `(GRID, REGION)` is the square
  arm's**, and it is declared, swept, and matched across arms — not derived.
  Claiming otherwise would be a magic number wearing a derivation.

Consequently the gate is assessed at **matched FIELD SIZE and matched TASK**
(the same N-way identification over the same N region footprints), with blob
count M as the swept independent variable, reported as a CURVE against the
square baseline rather than a single matched point. The saving, if any, is that
M ≪ pixels.

**Verdict for the headline comparison is `hamming`**, for two stated reasons:
its set-overlap `covered_count` handles the **variable-length** signatures that
foveation necessarily produces (a central footprint receives more blobs than a
peripheral one — that is the whole point, and a fixed-length `Dot` verdict would
forbid it); and §0.2 shows read-back is only 0.5–1.8% of graph under hamming, so
a graph-cost claim is not confounded by the reference instrument.

**Cost is NOT part of this derivation.** The coordinator supplied measured
scaling from the concurrent rung (scale ≈ n_regions^1.7, grain ≈ cells^0.4 on
C1 only, and unconfirmed on C2). That is noted as *consistent with* spending
resolution centrally and coarseness peripherally, and it is recorded **here,
separately and after the fact**, precisely so it cannot be mistaken for the
derivation. Fitting a density curve to a cost table is the hand-tuning §13
forbids. The profile above would be unchanged had the cost table said the
opposite.

**Blob support** is circular and **overlapping** (neighbouring blobs at spacing
`2r` with radius `r` touch; the overlap comes from the Gaussian tail being
truncated at `r`, so support is not a tiling). Membership weights are computed
in the map (continuous), and the emitted per-blob value is **stepped back onto
the integer lattice** — the frame/continuum invariant: continuous in the map,
integer in the frame.

---

## 3. Construction, and the parser defect

The blob signature is `["blob", i, "v<q>"]` where `i` is the blob's **integer
index**, not a name. There is **no fixed-width name field to overflow**: the
codebook entry's identity is carried as an integer attribute and read back as an
integer, so the r143→14 class of defect is **gone by construction**, not
patched. The gate for this is a run at N ≥ 100 blobs whose read-back answers are
checked to be in range and non-`None` — the exact condition the old parser
failed silently.

Blob sampling is **input construction**: mechanical pixel→tuple translation
before anything reaches the graph, the same admissible class as quantizing a
frame or building an orbit. No decision over graph state.

---

## 4. Bounds, declared in advance

- **Blob counts:** matched to baseline region counts, N ∈ {16, 64, 144}.
- **Field sizes:** GRID ∈ {24, 48, 72}, matched between arms.
- **Corpora:** C1 (cartoon, episode_index 0, pin
  `08630d4b7b215c469df19b9c42d7b617`) and C2 (live-action, episode_index 3, pin
  `119eca433329b36b19e5d69fef84966e`). **Reported per corpus, never pooled** —
  they have disagreed five times in this arc. An episode PIN mismatch VOIDS the
  run.
- **Verdict:** reported under BOTH `hamming` and `ncc`, because §0.2 shows the
  read/graph ratio is a property of the arm.
- **BSDS300 is absent from this tree** (0 images; 10 oracle tests skip for it).
  No BSDS claim will be made.
- Deltas, orbit radius ρ, and K_LEVELS inherited unchanged from the incumbent.

## 5. What would falsify each claim

- H1 falsified if graph time per frame at matched N is not lower.
- H2 falsified if blob accuracy falls below the re-earned square baseline's
  interval, or if a floor is not re-measured.
- H3's registered prediction (null) is falsified if protos > 0 appear.
- The rung reports whichever of the three honest outcomes occurs: blobs cheaper
  and protos work; blobs cheaper and protos still fail; blobs not cheaper and
  the raster was not the cost. **§0.2 already establishes the last clause for
  read-back specifically.**

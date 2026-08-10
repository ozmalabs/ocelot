# DOES THE PARALLAX CARVE SURVIVE REAL PHOTOMETRY? — RESULTS: **CONFIRM. THE FEW-AND-LARGE KNEE HOLDS ON REAL BSDS TEXTURE (DEPTH eff_surfaces 3.13, THREE ≈1/3 SURFACES; FLAT ONE BLOB), CI-SEPARATED, WITHIN 0.05 OF THE SYNTHETIC FLOOR AT THE SAME DEPTH/SHIFT GEOMETRY — WITH A BOUNDED, INHERITED-SENSOR DEGRADE: SPACE CONSTANCY 3→11 px, AND A LOW-CONTRAST TAIL (confab 7.3→10.2 %, FLAT eff 1.00→1.16) THE PARTICIPATION RATIO ABSORBS SO THE DEPTH KNEE NEVER BREAKS. THE CATASTROPHIC <0.4 CLIFF IS UNREACHABLE IN BSDS (0/80). REAL PHOTOMETRY IS NOT A BLOCKER; REAL MOTION REMAINS THE DEFERRED ONE.**

*Pre-registration `VISION_PARALLAX_REAL_PREREG.md`, committed **`eedf4945d9`** BEFORE
any confirmatory number (only the pilot on already-burned parallax seeds
116000–116019 had been computed — the §3-clause-3 power analysis). Nothing in it was
edited after the first confirmatory number.*

## THE ONE VARIABLE

The eye's parallax carve is CONFIRMED on **synthetic** input (`VISION_PARALLAX_RESULTS.md`):
a known self-shift + efference-copy subtraction + common-fate grouping carves a depth
scene into 3 few-and-large surfaces where a byte-identical static frame gives 1 blob.
It is **mechanism-proven, not capability-proven**, and its first named breaking
condition is **synthetic input**. Real MOTION is a data problem (no real 3-D-motion
video in the tree — a flat photo under self-motion is uniform shift = the FLAT case),
so it is deferred. **The one variable this rung changes is PHOTOMETRY: real natural
BSDS300 texture instead of synthetic Fourier texture, at the SAME controlled
depth/shift geometry** (shifts `[0,3,6]`, block 8, grid 144, ref 1). The carve
machinery is REUSED byte-for-byte (`parallax_char.group_common_fate` /
`vector_field`); only the source of `a` changes.

**The honest real analog of the toroidal roll (no fabrication).** The synthetic
texture wraps exactly, so `np.roll(a,s)` is a rigid translation. A real photo does not
wrap; a toroidal roll would inject a false wrap-seam that is a NEW confound, not
"photometry". The faithful analog reproduces `b[:,x] = a[:,x−s]` EXACTLY without wrap
by sourcing displaced pixels from a crop wider than the grid (`off0=max(shifts)`):
`a=src[:,off0:off0+grid]`, `b_depth[:,x∈band i]=src[:,x+off0−s_i]`,
`b_flat[:,x]=src[:,x+off0−s_ref]`. Every displaced pixel is a real scene neighbour;
`a` is byte-identical DEPTH-vs-FLAT; owner / edges / ground-truth / Δ_ref are identical
to the synthetic geometry. **Gated** (`tests/test_parallax_real_migrated.py`, 5 passed,
positive-controlled: a toroidal fabrication FAILS the exact-shift gate).

## ENGINE PROVENANCE (§10)

- Branch **`worktree-agent-a7dc10c29ca12814e`**; base SHA **`c5bf33582d`** (contains
  the parallax carve machinery + the three required docs). Prereg commit **`eedf4945d9`**.
- Engine **`7041d2e6a7dd`**, built IN THIS TREE by `scripts/engine_build.sh` (**`own`**).
  Printed from INSIDE the measuring process into `results/parallax_real.json`, asserted
  `== EXPECT_ENGINE` at start / mid / end, and re-verified AFTER the measurement:
  `engine 7041d2e6a7dd @ <this worktree>/…/_native.abi3.so` — **unchanged**
  (`provenance_stable == True`, asserted in the artifact). **THIS RUNG ADDS NO RUST**
  (Rust source byte-identical to canonical; a shared build would have been legitimate,
  built in-tree anyway); Term enum index 180 remains UNUSED.
- Migrated provenance gate as its OWN step, FIRST: **7 passed**; re-run AFTER: **7 passed**.
- **ORACLE `bash scripts/rung7_vision_bench.sh` (with `data/` symlinked, §10.2):**
  BEFORE **222 passed / 0 failed**; AFTER **222 passed / 0 failed** (§9 trivial — no
  Rust, no seed, no edit to any committed file; new script + new gate only).
- **LOAD:** `os.getloadavg()` in the artifact — confirm run start `[1.81, 2.75, 2.18]`,
  end `[1.58, 2.63, 2.16]`; wall **18.1 s** (all three arms, n=80). ≤2 workers
  (`OMP_NUM_THREADS=2`). **No wall-clock quantity is a verdict** — every statistic is a
  bootstrap over the 80 seeds or an exact/counted quantity.
- **SEED CLAIM 124000–124999 (verbatim, §3 clause 8, post-run):**
  ```
  SEED CLAIM 124000-124999: CLEAN -- no collision DETECTED.
    Scope: 827 files with seed sinks; 515 UNRESOLVED sink sites tree-wide (counted, not discarded).
  ```
  Reads CLEAN because the confirmatory seeds are `range(124000, 124080)` — a `range`
  the static tool does not resolve to integers (the disclosed CLI blind spot;
  `seed_audit` reports **2 unknown sinks** for `parallax_real_measure.py`, the
  `default_rng(sd)`/`default_rng(k)` sites). The block IS genuinely drawn by THIS
  rung's confirmatory arm (124000–124079); pilot on burned 116000–116019; bootstrap
  CIs use fixed `default_rng(0..999)` resampling generators (the parallax rung's exact
  `_ci`), not scene seeds. **`unknown_sinks: 2` (the CLI blind spot), none outside the
  block; 515 unresolved sinks tree-wide (counted, not discarded).**

---

## 1. THE HEADLINE — THE SIZE DISTRIBUTION, DEPTH vs FLAT, ON REAL TEXTURE

Primary arm **real_random** (a random BSDS crop per seed — the natural rate), n=80
fresh confirmatory seeds 124000–124079, unit = SEED, 95% bootstrap CI. The synthetic
floor is reproduced ON THE SAME SEEDS as the exact baseline.

| statistic (τ=√5) | SYNTHETIC (floor) | **REAL random** | FLAT (real) | verdict |
|---|---|---|---|---|
| **eff_surfaces** `1/Σpᵢ²` | 3.11 [3.09, 3.12] | **3.13 [3.11, 3.15]** | **1.00 [—]** | in band, ≈synthetic, CI-sep ✓ |
| **largest_frac** | 0.361 | **0.355 [0.353, 0.358]** | **0.998** | < 0.5; FLAT one blob ✓ |
| **top-3 fractions** | [.361,.333,.284] | **[.355,.333,.287]** | [.998, —, —] | 3 ≈1/3 surfaces vs 1 blob |
| FLAT field discontinuity (GT) | 0.00 | — | **0.00** (null exposed) | — |

| statistic (τ=0) | SYNTHETIC | **REAL random** | FLAT (real) |
|---|---|---|---|
| eff_surfaces | 3.12 [3.11, 3.13] | **3.16 [3.14, 3.18]** | 1.00 |
| largest_frac | 0.359 | 0.352 | 0.998 |

**All five pre-registered CONFIRM criteria are met on the primary arm** (both τ):
DEPTH eff ⊂ [2.5, 3.5]; largest_frac < 0.5; FLAT eff ⊂ [0.9, 1.2] with largest > 0.9;
DEPTH-vs-FLAT CI-separated on both statistics at both τ; real DEPTH eff within **0.05**
of the synthetic floor (≤ the 0.25 same-knee bracket). **⇒ PRE-REGISTERED VERDICT:
CONFIRM.** The eye still carves a real-textured depth scene into three surfaces of ≈⅓
the frame each, exactly the number of depth planes, while the byte-identical static
frame's FLAT twin stays one blob — **the carve survives real photometry.**

**The participation ratio is load-bearing, exactly as in the parallax rung.** The RAW
group count on real texture is **9.8** (τ=√5) / **11.8** (τ=0) — the sensor's
confabulation-speck tail (the 84000 trap) — but `eff_surfaces = 1/Σpᵢ²` reads the **3**
real surfaces because the specks carry `pᵢ² → 0` weight. The raw median (6.9 / 2.8) is
NOT the discriminator; the speck-robust participation ratio and largest_frac are (as
pre-registered).

**The byte-identical-static-frame control holds on real texture.** DEPTH and FLAT share
ONE real crop `a`; the depth bands sit at fixed columns unrelated to image content, so
their boundary-column gradient (**9.689**) is indistinguishable from the within-frame
gradient (**9.680**), ratio 1.001 — a static carver has nothing special to key on at a
depth boundary and carves `a` identically in both conditions. The whole DEPTH-vs-FLAT
difference is parallax vs uniform motion, on real pixels.

---

## 2. THE DEGRADE, QUANTIFIED — AND IT NEVER BREAKS THE KNEE (both stated, §5/§7/§8)

The knee CONFIRMS, but three registered quantities move under real photometry. Per the
prereg's §5 co-holding rule, they are reported as a **DEGRADE on the inherited-sensor
quantities**, alongside the CONFIRM on the size-distribution knee.

| quantity | synthetic | real random | real low-contrast probe | reading |
|---|---|---|---|---|
| **space constancy** (sensed ref-band residual max) | **3 px** | **11 px** | 11 px | DEGRADE: the efference copy is exact (GT residual 0), but the SAD sensor confabulates on the reference band up to 11 px on real texture |
| **confab rate** (sensed ≠ GT cells) | 7.4 % | **7.3 %** | **10.2 %** | NATURAL real texture ≈ synthetic; only the flat tail lifts it |
| **eff_surfaces τ=0** | 3.12 [3.11,3.13] | **3.16 [3.14,3.18]** | 3.23 [3.19,3.26] | a small (+0.04) CI-separated spurious-surface bump at exact τ; absorbed by τ=√5 |
| **FLAT eff / largest** | 1.00 / 1.000 | 1.00 / 0.998 | **1.16 / 0.951** | the one-blob null FRAGMENTS at low contrast (specks), still ≥0.95 dominant |
| **DEPTH eff (knee)** | 3.11 | **3.13** | **3.11 [3.04, 3.16]** | the knee HOLDS even at the flat tail — never out of band |

**The clean reading:** at NATURAL contrast, real BSDS texture costs the sensor nothing
(confab 7.3 % ≈ synthetic 7.4 %) and the carve is indistinguishable from synthetic on
the knee. The degradation is (a) space constancy 3→11 px (a sensor-confab fact, not the
efference copy — which stays exact), and (b) a low-contrast tail where confab lifts to
10.2 % and the FLAT one-blob fragments — but **the participation ratio down-weights the
confab specks so the DEPTH few-and-large knee never breaks**, even at the flattest
reachable band.

---

## 3. WHERE IT DEGRADES vs LOCAL CONTRAST — AND THE BOUND THE CARVE INHERITS

The antagonist (rung 94000) is the SAD sensor's block-std cliff: below **mean block std
0.4** (one 8-bit step) it falls off a cliff (silent miss 0.0003→0.0641, confidently
wrong 0.0166→0.0544). **That cliff is essentially unreachable in BSDS at 48-px band
width:** a corpus-wide scan finds **1/200** train images with any band < 0.4, 35/200
below 1.0, 70/200 below 2.0. In the confirmatory arms **0/80** random crops and **0/80**
adversarially-hunted low-contrast crops reached < 0.4 (random min_band_std 1.02, lowcon
min 0.43 — the cliff EDGE). So on natural texture the carve inherits only the MILD
confab regime, never the >99 %-wrong catastrophe.

**The degradation localises to the low-contrast tail, shown at the ARM level, not
per-crop.** Pushing the crop selection toward the corpus-flat tail (random
min_band_std median 13.97 → lowcon median 2.63; lowcon has 16/80 crops < 1.0, 35/80 <
2.0) monotonically raises confab 7.3 %→10.2 %, FLAT eff 1.00→1.16, and DEPTH-τ=0 eff
3.16→3.23. **The per-crop correlation of |eff−3| with min_band_std is WEAK and
inconsistent** (+0.24 random, −0.10 lowcon at τ=√5) — a proviso that partially broke
(pilot suggested −0.41). The honest cause: `eff_surfaces` is so speck-robust that DEPTH
eff barely tracks contrast per-crop; the degradation shows in **confab rate and FLAT
fragmentation**, not in the DEPTH knee. That is itself a finding — **the DEPTH carve is
MORE robust to real-texture confab than the sensor's error rate would suggest, because
the participation ratio absorbs the specks.**

> **THE BOUND THE CARVE INHERITS FROM THE SENSOR ON REAL BSDS TEXTURE:** at natural
> contrast the carve is synthetic-clean (confab ~7.3 %, knee intact, FLAT one blob,
> space constancy sensed ≤11 px vs exact 0); down to the flattest reachable band
> (mean block std ≈ 0.43, the cliff edge) confab rises to ~10 % and the FLAT null
> fragments (eff 1.00→1.16, largest ≥0.95), **but the DEPTH few-and-large knee never
> leaves the object band (eff 3.11–3.23).** The catastrophic <0.4 cliff is not
> reachable in BSDS at this band width, so the carve never enters the sensor's
> >99 %-wrong regime on natural photometry. **The mechanism works on real BSDS
> texture at every reachable local contrast; real photometry is not a blocker.**

---

## 4. WHICH REGISTERED OUTCOME OCCURRED

| criterion (§5 — CONFIRM, co-holding at BOTH τ) | measured | met? |
|---|---|---|
| real DEPTH eff CI ⊂ [2.5, 3.5] | 3.11–3.18 | ✓ |
| real DEPTH largest_frac < 0.5 | 0.352–0.355 | ✓ |
| FLAT eff ⊂ [0.9,1.2] AND largest > 0.9 | 1.00 / 0.998 | ✓ |
| DEPTH-vs-FLAT CI-separated on both, both τ | yes | ✓ |
| real DEPTH eff within 0.25 of synthetic floor | within 0.05 | ✓ |
| FLAT field discontinuity = 0 (null exposed) | 0.00 | ✓ |
| static-frame band gradient ≈ within (control) | 9.689 ≈ 9.680 | ✓ |

Clean **CONFIRM** on the primary knee; **DEGRADE** on the named inherited-sensor
quantities (space constancy 3→11 px; low-contrast tail confab 7.3→10.2 %, FLAT
fragmentation; +0.04 τ=0 spurious bump), both stated. My prediction (§6:
~55 % DEGRADE-leaning-CONFIRM; space constancy degrades 3→~11 px; cliff nearly
unreachable; degradation at low contrast) held in every particular EXCEPT the per-crop
correlation, which I over-predicted (see §5).

---

## 5. WHAT I GOT WRONG — in full

1. **I OVER-PREDICTED THE PER-CROP CONTRAST CORRELATION.** The prereg (from the n=20
   burned pilot) said corr(|eff−3|, min_band_std) ≈ −0.41. On the n=80 confirmatory it
   is WEAK and sign-inconsistent (+0.24 random, −0.10 lowcon). The pilot value was a
   small-n artefact. The honest signal is at the ARM level (random vs low-contrast
   pool), not per-crop — because the participation ratio is too speck-robust for DEPTH
   eff to track contrast cell-by-cell. Reported as the finding it is, not smoothed over.
2. **THE "NO FABRICATION" ADVANTAGE OF WINDOWING IS PARTLY MOOT FOR THIS GEOMETRY.**
   Because the leftmost band has the smallest shift (0) and the other bands start at
   columns ≫ max_shift, no depth-band column wraps — so `b_depth` equals a plain
   toroidal roll of `a`. Windowing only differs (and only matters) for the FLAT frame's
   leftmost `s_ref` columns, where it correctly sources real src neighbours instead of
   a's wrapped right edge. The construction is still exact and fabrication-free; the
   gate's positive control bites on exactly those FLAT columns. Disclosed rather than
   overclaimed.
3. **THE CLIFF IS UNREACHABLE, SO THE PROBE TESTS THE CLIFF EDGE, NOT THE CLIFF.** I
   could drive min_band_std only to 0.43 (1/200 corpus images dips below 0.4). The
   catastrophic <0.4 regime is therefore CHARACTERISED FROM rung 94000, not
   re-measured here on the carve. What I measured is the approach to it; the >99 %
   regime on the carve is un-run (and un-runnable on BSDS at this band width).
4. **THE LOW-CONTRAST PROBE REUSES SOURCE IMAGES.** Only ~35–70 BSDS images have a
   sufficiently flat band, so 80 lowcon seeds draw from a flat-image pool with reuse —
   the lowcon seeds are not fully independent. It is a SECONDARY probe (not the primary
   confirmatory statistic); disclosed, and the primary random arm has no such reuse.
5. **THE SENSED SPACE-CONSTANCY (11 px) IS THE SENSOR'S, NOT THE EFFERENCE COPY'S.** As
   in the parallax rung: the ground-truth reference residual is exactly 0 (the
   efference copy is known); the 11 px is the SAD sensor confabulating on the reference
   band of real texture. Both stated, so space constancy is not oversold as broken.

---

## 6. WHAT IS NOT SHOWN (§8)

- **REAL MOTION IS STILL NOT TESTED.** Only photometry changed. A flat photo under
  self-motion gives a uniform shift = the FLAT case; genuine real 3-D-motion video is a
  data problem, deferred. This rung retires the SYNTHETIC-PHOTOMETRY condition, not the
  synthetic-motion one.
- **NOTHING SAYS THE SURFACES ARE OBJECTS** (inherited): the 3 DEPTH surfaces are the 3
  depth planes by construction, not inspected for content.
- **NO OCCLUSION / DISOCCLUSION.** Fronto-parallel bands, horizontal parallax, N=3, one
  SAD aperture family — all inherited from the parallax rung.
- **THE <0.4 CLIFF ON THE CARVE IS UN-RUN** (unreachable in BSDS); the catastrophic
  regime is characterised from rung 94000, not re-measured on the carve.
- **NO TIMING CLAIM.** Every quantity is a bootstrap over the 80 seeds or exact/counted.

---

## 7. LEDGER ROW (for the supervisor to merge into `VISION_PROTOCOL.md`)

*Written here, not there — `VISION_PROTOCOL.md` is not this rung's file.*

| range | used for |
|---|---|
| **124000–124999 (confirmatory 124000–124079 + pilot on BURNED parallax 116000–116019; unknown_sinks 2 — the `range()` CLI blind spot, none outside block; NO Rust, NO seed, Term index 180 UNUSED — a measurement reusing the parallax carve)** | **PARALLAX CARVE SURVIVES REAL PHOTOMETRY — CONFIRM.** Reproduces the parallax rung's carve (116000) EXACTLY, changing ONLY the pixel source: synthetic Fourier texture (floor re-earned on the same seeds) vs REAL BSDS300 crops, at the SAME depth/shift geometry (shifts [0,3,6], block 8, grid 144, ref 1). Real analog of the exact toroidal roll = an exact WINDOWED SLIDE from a wider real crop (`b[:,x]=a[:,x−s]` exactly, no wrap, no fabrication — gated 5/5, positive-controlled: a toroidal fabrication FAILS the exact-shift gate). Byte-identical static frame `a` shared DEPTH-vs-FLAT (band-boundary gradient 9.689 ≈ within 9.680 — bands leave no static trace on real pixels). **PRIMARY (real_random, n=80, unit=SEED): DEPTH eff_surfaces 3.13 [3.11,3.15] (τ=√5) / 3.16 [3.14,3.18] (τ=0), largest_frac 0.355, top-3 [.355,.333,.287] — three ≈⅓ surfaces; FLAT eff 1.00, largest 0.998, field discontinuity 0.00 (null exposed) — CI-SEPARATED on both stats at both τ, WITHIN 0.05 of the synthetic floor. ALL FIVE CONFIRM CRITERIA MET. CONFIRM.** Participation ratio load-bearing (raw count 9.8–11.8 confab specks; eff reads the 3 real surfaces — the 84000 trap avoided). **DEGRADE on inherited-sensor quantities (both stated): space constancy sensed reference residual 3 px (synth) → 11 px (real) — the efference copy is EXACT (GT residual 0), the 11 px is SAD confab on the reference band; confab rate 7.4 % (synth) ≈ 7.3 % (real natural) → 10.2 % (adversarial low-contrast probe); FLAT one-blob null FRAGMENTS at the flat tail (eff 1.00→1.16, largest 0.998→0.951); a +0.04 CI-separated spurious-surface bump at exact τ. THE DEPTH KNEE NEVER BREAKS (eff 3.11–3.23 across every arm and contrast) — the participation ratio absorbs the confab specks.** THE BOUND THE CARVE INHERITS: the sensor's <0.4 block-std cliff is UNREACHABLE in BSDS at 48-px band width (1/200 corpus images, 0/80 confirmatory crops; random min-band-std 1.02, lowcon 0.43 = cliff EDGE), so the carve never enters the >99 %-wrong regime on natural texture; the mechanism works at every reachable local contrast. Degradation localises to the low-contrast tail at the ARM level; the per-crop corr(|eff−3|, min-band-std) is WEAK (+0.24 / −0.10) — the DEPTH knee is MORE robust than the sensor error rate suggests. **Real photometry is NOT a blocker; real MOTION remains the deferred one.** WHAT IT GOT WRONG: over-predicted the per-crop contrast correlation (−0.41 pilot artefact → weak on n=80); the "no-fabrication" windowing advantage is partly moot for this geometry (only FLAT's left `s_ref` columns wrap); the cliff is unreachable so the probe tests the cliff EDGE not the cliff; the lowcon probe reuses source images (secondary, disclosed); the 11 px space-constancy is the SENSOR's confab, not the efference copy. Provenance its OWN step (7 passed, re-verified 7041d2e6a7dd post-run, provenance_stable True); oracle rung7_vision_bench 222/0 BEFORE and AFTER; own gate 5 passed; loadavg [1.81→1.58], ≤2 workers, wall 18.1 s; engine 7041d2e6a7dd `own` — NO RUST, NO SEED, index 180 UNUSED. |

---

## 8. NAMED NEXT LEVERS (each its own pre-registration)

1. **REAL MOTION — the deferred variable.** This rung retires synthetic PHOTOMETRY;
   the standing status still names synthetic MOTION. A short real-video clip with
   known/estimated camera motion (or the codec motion-vector field, memory
   CODEC↔EYE) over real 3-D structure would test whether the carve survives real
   parallax, not just real texture.
2. **A MULTI-SCALE SENSOR TO BEAT THE APERTURE BOUND ON REAL EDGES.** Real texture's
   long edges are where the SAD sensor silent-misses (aperture problem). A coarse-to-
   fine motion sensor ("bins propose, continuous decides" in the motion domain) would
   test whether the low-contrast/edge tail closes.
3. **SPACE CONSTANCY WITH A ROBUST REFERENCE MATCH.** The 3→11 px sensed-residual
   degradation is the SAD sensor confabulating on the reference band. A normalised or
   gradient objective for the reference-plane match (its own pre-registration, a
   mechanism-level hypothesis, not a sweep) is the obvious follow-up.

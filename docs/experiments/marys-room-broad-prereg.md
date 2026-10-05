# Mary's Room: broad-spectrum identification and prediction (PREREGISTRATION)

Phase 3 of the Mary's Room empirical paper plan. This supersedes the two-stimulus
red/green pilot (`marys-room-red-green-prereg.md`) as the confirmatory study for
RQ1 (pre-exposure identification) and RQ2 (prediction of sensory state). It is
registered **before** running the eye arm. The pilot is retained as a feasibility
run only; the `48→28` compression number is retired (see
`docs/experiments/pilot-limits.md` once written), not carried forward.

## Questions (preregistered)

- **RQ1:** Can a theory-only decoder, fixed from CIE 2006 2° cone fundamentals
  and the opponent axes, classify a broad stimulus set above chance **before**
  running the eye — including held-out wavelengths and conditions?
- **RQ2:** How closely do the eye's opponent vectors match the theory-derived
  predictions, as a function of distance from the RG opponent boundary and of
  illuminant/observer assumptions? Where do predictions fail?

"Experienced" means the eye's computed opponent signal; it is not a measure of
phenomenal experience. This is a model-level study (see scope decision: human
psychophysics is future work).

## Fixed apparatus and sources (declared before running)

- **Photon source:** `domains/spectral_forward.py` per
  `docs/research/spectral-forward-model-spec.md`, passing its four unit tests.
- **Theory fundamentals:** CIE 2006 LMS cone fundamentals, 2° field, energy
  units, CIE 170-1:2006 table 6.7. Same λ grid as the forward model.
- **Opponent axes (both arms):** `RG = L − M`, `BY = S − 0.5·(L + M)`.
- **Theory decoder (fixed sign rule, no fit on eye data):**
  red iff `RG > 0`, green iff `RG < 0`. For the multi-category readout, a
  nearest-prototype rule over declared hue anchors (below) — anchors fixed from
  CIE before any eye run.
- **Eye:** fresh `GraphEye` instances, documented provenance line recorded per
  run. No labels inserted into the eye graph; column→stimulus mapping kept in the
  external scoring record only.
- **λ grid:** 390–780 nm at Δλ = 1 nm (CIE/ISO 11664-3 reference summation
  interval); 5 nm (ASTM E308 abridged) as a declared ablation.
- **Photon anchor `k`:** fixed so a reference white (equal-energy E) at ~100 td
  (cone-mediated photopic) sets the per-column quanta budget, with the budget
  chosen so monochromatic 610/530 nm reproduce the pilot output within rounding
  (regression anchor). Every stimulus reports its retinal illuminance in td.

> **Pointer — Amendment A0 (pre-run, forward model, 2026-10-04):** see
> `docs/research/spectral-forward-model-spec.md` § "Amendment A0". In brief:
> (a) quantisation default is deterministic cumulative rounding (per-bin
> rounding is an ablation); (b) photon anchor declared as
> `QUANTA_SCALE = 1891.2408486093182` (E at 100 td → 1000 model quanta/column,
> quantal λ/560 nm weighting), pilot packets reproduced exactly; (c) the
> eyelid's eye-response sign is a prediction measured in Arm B, not a unit
> test; declared eyelid ambient levels 100/1000/10⁴ td. CIE 2° L−M crosses
> zero at 409.16 and 554.08 nm; S−0.5(L+M) at 488.29 nm. Finding: declared
> eyelid OD params give ~0.14 td behind the lid at 100 td ambient (mean OD
> 2.89), not the spec's "~1 td"; params unchanged.

## Stimulus set (frozen before the eye arm)

Partitioned into TRAIN (decoder/anchor construction, theory arm only) and
HELD-OUT (never used to set any rule or anchor). The eye never informs any
decoder parameter.

1. **Monochromatic sweep:** 400–700 nm. TRAIN at 10 nm spacing; HELD-OUT at the
   intervening 5 nm offsets. Multiple intensities (≥3, spanning ~0.1×–10× the
   anchor) to probe the Naka-Rushton nonlinearity.
2. **Boundary-dense sweep:** fine 1 nm sampling in a ±20 nm window around the
   measured RG zero-crossing (the unique-hue-yellow / green-red neutral region),
   where the nonlinearity and Gaussian-vs-CIE mismatch diverge most. HELD-OUT.
3. **Illuminants:** each broadband stimulus rendered under ≥3 declared
   illuminants (equal-energy E, D65, incandescent A). Illuminant is a condition
   factor, not a decoder input.
4. **Broadband / reflected colours:** a declared reflectance set (≥12 surfaces)
   × illuminants, producing polychromatic packet lists per column.
5. **Metamer pairs:** ≥6 pairs constructed metameric under CIE (identical
   `(L,M,S)`) but spectrally distinct — the explicit RQ5 test that the eye's
   Gaussian sensitivities break CIE metamerism.
6. **Wrong-observer / wrong-optics conditions:** pre-receptoral filter `T(λ)`
   ON, and a deliberately mismatched assumed observer, to probe where theory
   predictions fail (RQ5). HELD-OUT, flagged as adversarial.
7. **Closed eyelid (embodied-Mary condition):** `T_eyelid(λ)` (long-pass,
   hemoglobin-shaped; see forward-model spec) × broadband ambient illuminant
   `E(λ)`, producing a long-weighted at-retina SPD. This is the light an
   embodied observer receives through closed lids. Rendered at ≥3 ambient
   intensities and across the declared `OD_long ∈ {1.0,1.3,1.6}` ablation.

## Procedure

1. Build and freeze the stimulus set and all decoder anchors from the theory arm
   **only**. Commit this file and the frozen stimulus manifest first.
2. **Arm A (theory, pre-exposure):** for every stimulus, integrate `Φ'(λ)`
   against CIE fundamentals → `(L,M,S)` → `(RG,BY)` → predicted label. Record
   predictions and the decoder's confidence/margin. No eye involved.
3. **Arm B (eye, post-exposure):** quantise each `Φ'(λ)` to integer packets,
   submit to a fresh `GraphEye`, read `red_green`/`blue_yellow`. One column per
   stimulus instance; **repeats across columns are deterministic duplicates and
   are labelled as such** (they contribute no variance — mechanism audit §
   determinism). The optional Poisson photon-noise variant, if run, is a
   separate declared arm with recorded seed.
4. Score Arm A vs ground-truth labels; score Arm B labels vs ground-truth; and
   compare Arm A predictions vs Arm B vectors.

## Primary metrics (report without threshold pass/fail claims)

1. **RQ1 — theory-only accuracy / balanced accuracy** on TRAIN and HELD-OUT
   separately, with a chance baseline and a binomial CI. Pilot RQ1 (2 stimuli)
   is **not** cited as evidence; this set is.
2. **RQ2 — angular error in degrees** between theory `(RG,BY)` and eye `(RG,BY)`,
   reported **as the primary direction metric**. The 0–100 "direction score" is
   demoted/dropped (it compresses the informative range). Report cosine too for
   continuity with the pilot.
3. **Error vs boundary distance:** angular error and label agreement as a
   function of `|RG|` and of distance (nm) from the RG zero-crossing.
4. **Calibration:** predicted vs observed opponent magnitude; residual vs
   intensity (the nonlinearity signature).
5. **Metamerism (RQ5):** per metamer pair, CIE opponent gap (≈0 by construction)
   vs eye opponent gap (predicted > 0). This isolates the sensitivity mismatch.
6. **Failure conditions (RQ5):** accuracy/angular-error under wrong-observer /
   pre-receptoral-filter-ON conditions, reported as scope limits, not excluded.
7. **Embodied-Mary result (closed eyelid):** the eye's opponent vector
   `(red_green, blue_yellow)` for the eyelid-filtered ambient flux, across
   intensities and the `OD_long` ablation. Reported as a named result: the
   long-wavelength retinal flux an embodied observer has already received,
   demonstrating the literal premise "Mary has never been exposed to red" is
   false for any eye with blood-perfused lids and L-cones. Report `red_green`
   sign and magnitude vs. a clearly-red monochromatic stimulus for calibration.
8. Engine provenance and all raw per-stimulus values.

## Preregistered predictions

- Arm A beats chance on HELD-OUT monochromatic and reflected stimuli; accuracy
  degrades gracefully approaching the RG zero-crossing.
- Arm B labels agree with Arm A on the clearly-chromatic stimuli; agreement
  **drops near the boundary** and the angular error there is dominated by the
  Naka-Rushton nonlinearity + Gaussian-vs-CIE mismatch (documented sources, not
  free parameters).
- The eye **breaks** at least some CIE metamers by a measurable opponent gap.
- Theory predictions degrade under wrong-observer/wrong-optics conditions; this
  is reported as a boundary of the model, not tuned away.
- The closed-eyelid stimulus drives the eye to **positive `red_green`** at every
  tested ambient intensity and across the `OD_long` ablation — i.e. the embodied
  observer has already received red-side opponent signal. The qualitative sign
  is predicted to be robust to the eyelid-slope choice.
- A failure of any prediction counts against the stated scope and is reported.

## Discipline

No stimulus, sign rule, decoder anchor, Gaussian centre, `k`, or `Δλ` may change
after seeing eye outputs. A dead eye arm, a degenerate category, or a failed
unit test on the forward model is a measured failure and is reported. The forward
model's four unit tests and the monochromatic pilot-regression anchor must pass,
and provenance must be recorded, before confirmatory scoring.

## Interpretation boundary

Success supports the narrow computational claim that research-held physical
knowledge predicts the eye's post-exposure opponent state, and that exposure
instantiates a sensory vector in the **same** coordinate system — a state change,
not a new representational kind. It does **not** establish a human quale, nor
that phenomenal experience is exhausted by this model. All phenomenological
language is confined to the Discussion and marked as interpretation.

### On the embodied-Mary result specifically

The closed-eyelid result defeats the **literal, embodied** Mary (an observer
with eyes, L-cones, and blood-perfused lids has already received red-side retinal
flux), not an **idealised** Mary stipulated to have no such exposure (opaque
lids, enucleation until release, or congenital achromatopsia later cured). The
paper must state this explicitly and not overclaim. The retreat to an idealised
Mary is itself informative: it survives only by stipulating away the body, which
concedes the physicalist's point that the remaining gap concerns **access,
attention, and representational format** — the labelled, attended, nameable
instance — rather than the sensory state itself. The eyelid delivers the opponent
*vector*; what the room withholds is the *named/attended* instance, which is
exactly the separable thing tested by the representation/compression arm (Arm C)
and discussed by Kind (2024) and Morris (2025). The claim is therefore bounded:
"here is the red Mary has already seen, as an opponent vector," not "there is no
epistemic gain on release."

## Amendment A1 (pre-eye-run) — 2026-10-04

Written **before any Arm B stimulus is submitted to an eye** and before Arm A
scoring code was run. It declares everything the sections above left open. The
frozen stimulus manifest (`results/marys_room_broad_stimuli.json`), the Arm A
result (`results/marys_room_broad_armA.json`), and the hash lock
(`results/marys_room_broad_freeze.json`) are built by
`scripts/marys_room_broad_theory.py`, which never imports `domains.photon_eye`
and never builds an eye. Nothing below may change after eye outputs are seen.

### A1-1 Ground-truth labels (independent of every decoder)

- **Dominant wavelength / excitation purity** in CIE 2012 2° xy chromaticity
  (`domains/spectral_forward.py::dominant_wavelength`, CIE 170-2 cone-fundamental
  XYZ CMFs), computed on the **at-retina SPD that the eye receives**.
- **White point:** equal-energy E for spectral lights, emissive mixtures,
  metamers of E white, and E-illuminated surfaces; the illuminant's own white
  for D65/A renderings (surfaces, bare illuminants, metamers of D65/A bases);
  the **ambient illuminant's** white for eyelid stimuli; the **unfiltered**
  illuminant's white for wrong-optics stimuli (the filter is not discounted).
  Consequence (declared): bare illuminants are achromatic by construction.
  Caveat: the XYZ CMFs are a linear transform of the CIE 2006 LMS fundamentals,
  so truth is decoder-independent but not observer-independent.
- **Unique-hue loci** (Kuehni 2004, *Variability in unique hue selection: a
  surprising phenomenon*, Color Res. Appl. 29(2):158–162, doi
  10.1002/col.10237, Table I; verified against the PDF at
  sites.socsci.uci.edu/~kjameson/KuehniCRA.pdf on 2026-10-04).
  Observer-weighted means of the six **spectral-light** data sets (Ayama n=19,
  Schefrin & Werner n=50, Nerger n=4, Jordan & Mollon n=97 [UG only],
  Volbrecht n=100 [UG only], Pridmore n=7):
  - unique blue **UB = 478.0 nm** (474·19+480·50+471·4+479·7)/80
  - unique green **UG = 514.8 nm** (506·19+509·50+510·4+512·97+522·100+517·7)/277
  - unique yellow **UY = 576.3 nm** (574·19+577·50+575·4+578·7)/80
  - unique red: extraspectral, **complementary 495.2 nm** (497.5c·2+494.6c·7)/9
    (Ayama, Pridmore — the only spectral-light red data).
  - spectral-side red locus used **only** for the yellow|red category
    boundary: **605 nm** (Webster IIA, object colours, n=175, the only
    non-"end-of-spectrum" spectral-side unique-red mean in Table I).
  Kuehni's own conclusion is that mean unique hues (esp. green, red) are poorly
  representative of individuals; the loci are therefore a declared
  population-mean convention, and the UG range 487–567 nm is reported as a
  caveat, not used.
- **4-category hue truth** (midpoints between adjacent loci): `blue` if
  spectral dominant λ < 496.4 nm; `green` if 496.4 ≤ λ < 545.55; `yellow` if
  545.55 ≤ λ < 590.65; `red/purple` if λ ≥ 590.65 **or** non-spectral (purple,
  complementary) dominant wavelength. There is no violet category: spectral
  λ < 496.4 nm is `blue`.
- **Binary perceptual truth:** `reddish` if dominant λ < UB (478.0) or
  > UY (576.3) or purple; `greenish` if 478.0 ≤ λ ≤ 576.3.
- **Achromatic exclusion:** excitation purity **< 0.05** ⇒ `achromatic`,
  excluded from all hue scoring (counts reported per family).

### A1-2 Decoders (theory-only, fixed now)

- **(i) Binary sign rule (preregistered, not redesigned):** `red` iff
  `RG = L−M > 0`, `green` iff `RG < 0`, `undecided` (scored as an error) iff
  `RG == 0`. Applied to every stimulus including 400–409 nm, where CIE 2° L−M
  is positive (A0-e). Disagreements with perceptual truth (cone-opponent L−M
  zero 554.08 nm ≠ UY 576.3 nm; 409.16 nm ≠ UB 478.0 nm) are findings.
  Margin = `|RG|/(L+M)`.
- **(ii) Multi-category nearest-anchor decoder:** opponent direction
  `u = (RG,BY)/‖(RG,BY)‖`; label = anchor with the smallest angle to `u`;
  margin = angular gap (deg) between nearest and second-nearest anchor.
  Anchors (CIE 2° theory only, TRAIN side only): `blue`, `green`, `yellow` =
  direction of the CIE LMS of a monochromatic light at UB/UG/UY, obtained by
  **linear interpolation in λ of the per-unit-energy LMS of the two bracketing
  TRAIN wavelengths** (10 nm grid: 470/480, 510/520, 570/580);
  `red/purple` = direction of an energy mixture of the TRAIN 400 nm and 700 nm
  lights whose E-referenced dominant wavelength is complementary 495.2 nm
  (mixture fraction found by deterministic bisection on xy, recorded).
- Neither decoder discounts the illuminant (prereg: illuminant is a condition
  factor, not a decoder input) nor models any pre-receptoral filter.

### A1-3 Splits and stimulus families

TRAIN = family 1 at the 10 nm grid (400–700 nm, 31 λ × 3 intensities) plus the
four anchor-construction items (not scored). **Everything else is HELD-OUT.**

1. `mono_sweep` — equal-quanta monochromatic lights, **100 / 1000 / 10 000
   model quanta** (0.1×/1×/10× the pilot budget; the TRAIN/HELD-OUT λ rule of
   §1). 61 λ × 3.
2. `boundary_dense` — 1 nm, λ ∈ [534.08, 574.08] (±20 nm about the CIE 2° L−M
   zero 554.08 nm), **excluding multiples of 5** (already in family 1, so no
   duplicates); 3 intensities as family 1. Boundary analysis pools 2 ∪ 1 in the
   window.
3. `illuminant` — bare E, D65, A (white diffuser) at 10 / 100 / 1000 td.
4. `reflectance` — all 24 BabelColor ColorChecker patches × E / D65 / A; the
   illuminant is scaled so a perfect white diffuser is **100 td**.
5. `metamer` — 8 pairs (base, `metamer(base, amplitude=0.8, cycles=3,
   phase=0)`, CIE 2° null space): bases E, D65, A whites at 100 td and
   ColorChecker red, green, blue, yellow, dark skin under D65 (100 td diffuser).
6. `wrong_optics` — 24 patches × D65 (100 td diffuser) with a pre-receptoral
   filter ON in the eye input only: `lens` = 10^−D, D = Stockman, Sharpe &
   Fach (1999) lens density (CVRL `lensss_1.csv`, 1.765 at 400 nm); `macular` =
   10^−D, D = Stockman, Sharpe & Fach macular density (CVRL `macss_1.csv`,
   peak 0.352 at 458 nm). Theory integrates the **unfiltered** SPD; truth uses
   the filtered at-retina SPD. `wrong_observer` — theory with CIE 2006 **10°**
   fundamentals (CVRL `linss10e_1_8dp.csv`), decoded with the frozen 2°
   anchors, eye input identical to its base stimulus (family 1 at 1000 quanta,
   61; family 4 × D65, 24); entries reference the base and are **not** new eye
   inputs. Both flagged adversarial.
7. `eyelid` — ambient E / D65 / A at **100 / 1000 / 10 000 td** ×
   `OD_long ∈ {1.0, 1.3, 1.6}` (`OD_short = 3.0`), at-retina = ambient × T_eyelid.

Extra declared families (all HELD-OUT, reported separately from the
confirmatory RQ1 pools):
- `adaptation` (RQ5) — per test column: **20 adapting epochs** of an adapting
  field, then **1 test epoch** whose percept is read (no gap, no other
  input on that column). Adapting fields: 610 nm 1000 q, 530 nm 1000 q, E white
  100 td. Test stimuli: monochromatic 1000 q at 450, 480, 510, 530, 550, 554,
  560, 570, 580, 600, 610, 630 nm, and E white 100 td (13 × 3 = 39). Arm A
  predicts with **no adaptation model** (the unadapted test-stimulus theory);
  truth = the test stimulus's physical label.
- `poisson` — genuine independent trials: `quantize(method='poisson')`, 10
  trials per stimulus, seed = 20261004 + 1000·k + trial (k = subset index, trial
  0–9), for k = 0..11: monochromatic 1000 q at 450, 500, 530, 550, 554, 570,
  610, 650 nm; E white 100 td; eyelid D65 OD_long 1.3 at 100 / 1000 / 10 000 td.
  Packets are stored explicitly. Theory uses the expected SPD.
- `pilot_regression` — 610 nm (col 0) and 530 nm (col 1), 1000 q; expected eye
  smoke values recorded; split `regression`, not scored.
- `ablation_grid5` — 24 patches × D65 on the 5 nm grid (ASTM abridged
  ablation); secondary.

All packets use the A0 default (cumulative rounding, quantal conversion,
`QUANTA_SCALE` from A0-b, 1 nm grid unless stated). Identical eye inputs are
marked `duplicate_of` (deterministic duplicates contribute no variance); pooled
metrics count each distinct eye input once (the first-built entry; build order
= family order above), per-family metrics include all members.

### A1-4 Metrics and intervals

Per prereg "Primary metrics". RQ1 is scored for both decoders on the
hue-scored (non-achromatic) stimuli of: TRAIN; HELD-OUT core (families 1
HELD-OUT, 2, 3, 4, 5, 7); and separately per family, adversarial (6), adaptation
and poisson. Accuracy with **Wilson 95% interval**; balanced accuracy (mean
per-class recall over truth classes present) with **stratified percentile
bootstrap, 10 000 resamples, numpy `default_rng(20261004)`**; chance baselines =
majority-class rate and 1/K; exact one-sided binomial p vs 0.5 (binary) and vs
the majority rate. The set is a designed, non-random sample and theory repeats
across intensities are deterministic duplicates, so intervals are descriptive;
counts of theory-distinct conditions are reported alongside. Angular error in
degrees remains the primary RQ2 metric (Arm B stage).

### A1-5 Lock

Locked by sha256 hash in `results/marys_room_broad_freeze.json` (this file,
the forward-model spec, `domains/spectral_forward.py`,
`scripts/marys_room_broad_theory.py`, the manifest, the Arm A result and every
`data/colour` file). No git commit was made (not requested); the hash freeze is
the preregistration lock. Check with
`python -m scripts.marys_room_broad_theory --verify` before and after Arm B.

## Amendment A2 (Arm C protocol, pre-analysis) — 2026-10-04

Written **before any Arm C quantity is computed**. The Arm B eye outputs
(`results/marys_room_broad.json`) already exist, and their RQ1/RQ2 summaries
have been read. No representation, quantiser, codebook, rate or distortion has
been computed on them yet. Arm C replaces the retired `48→28` proxy
(`docs/experiments/pilot-limits.md`). It is implemented by
`scripts/marys_room_rate_distortion.py`, which never builds an eye: it reads
the eye outputs from the Arm B result file. The bytes of this file up to the
end of A1 are unchanged; their sha256 is the A1 freeze hash. The lock entry
`amendment_A2` in `results/marys_room_broad_freeze.json` records that prefix
check and the new hash of this file. Nothing below may change after Arm C
outputs are seen. Any failed prediction is reported, not tuned away.

### A2-1 Data model (labels kept separate)

- **Sensory vectors** come from `results/marys_room_broad.json::per_stimulus[*].eye`:
  - `x_LMS = (l.activation, m.activation, s.activation)` from `eye.receptors`. The rod is excluded because it is not on either opponent axis.
  - `x_opp = (red_green, blue_yellow)` as emitted by the eye.
- **Declared consistency check:** `|RG − (L−M)| ≤ 1e-12` and `|BY − (S − ½(L+M))| ≤ 1e-12` for every row. It is reported; a failure is reported, not repaired.
- **Labels** are the manifest `truth.hue4` and `hue_scored`. They live in a separate array and are passed **only** to the scoring function, never to any fit, encoder or minter.
- **TRAIN (fit set):** `split == "train"`. These are the 93 rows of the 10 nm monochromatic sweep at 100/1000/10 000 q, all distinct eye inputs.
- **HO_core (primary evaluation pool):** `split == "heldout"`, family ∈ {mono_sweep, boundary_dense, illuminant, reflectance, metamer, eyelid}, `duplicate_of is None`. This is identical to Arm B's `HELDOUT_core`.
  - Rate is amortised over **all** HO_core rows N, including achromatic ones.
  - Task accuracy is computed on the hue-scored rows.
  - Angular error is computed on rows whose original eye `x_opp` is non-zero.
- **HO_all (secondary pool):** every held-out row with its own eye output and `duplicate_of is None`. That is HO_core ∪ wrong_optics ∪ adaptation ∪ poisson ∪ ablation_grid5. `wrong_observer` is excluded because those rows reuse their base's eye output.
- **HO_core_dup (secondary, minter only):** HO_core including deterministic duplicates. It is used to show what exact repeats do. Duplicates are never counted as independent samples; only the poisson rows are independent trials.

### A2-2 Task and distortion

- **Task decoder:** the frozen A1-2(ii) nearest-anchor decoder, using `scripts/marys_room_broad_theory.decode` with the anchors stored in `results/marys_room_broad_armA.json`. It is applied to the *decoded* opponent vector. A zero decoded vector is labelled `undecided` and scored wrong.
- **Task accuracy** is accuracy against truth `hue4`. Balanced accuracy and label fidelity (agreement with the decoder on the unquantised eye vector) are also reported.
- **Reference accuracy:** `A0` is the decoder's accuracy on the unquantised eye vectors of the same pool.
- **Secondary task:** the A1-2(i) sign rule (binary truth) on the decoded vectors. This is the category-rule ablation.
- **Distortion:** measured in opponent space against the unquantised eye `x_opp`.
  - Angular error is in degrees. A decoded zero vector counts as 90°. Rows with a zero original vector are excluded from the angular metric and counted.
  - Euclidean error is in opponent units.
  - Mean, median and p90 are reported for both.
  - Codes in LMS space are decoded to LMS and then mapped through the fixed opponent formulas `RG = L−M`, `BY = S−½(L+M)`.

### A2-3 Representations and rate accounting (explicit fixed-length codes, bits)

- **Uniform scalar quantiser (USQ):**
  - It is midrise with `2^b` cells per dimension over the TRAIN `[min, max]` of that dimension.
  - `idx = clip(floor((x−lo)/(hi−lo)·2^b), 0, 2^b−1)` and reconstruction is `lo + (idx+½)(hi−lo)/2^b`.
  - Held-out values outside the TRAIN range are clipped. The clip fraction is reported.
  - `b ∈ {1,…,10}`.
- **(a) raw LMS (3-D):** USQ per cone, giving `3b` bits/sample. The model cost is 3 ranges × 2 × 32 = 192 bits.
- **(b) fixed opponent (RG, BY):** USQ per axis, giving `2b` bits/sample. The model cost is 128 bits; the basis is fixed by the prereg and costs nothing.
- **(c) PCA:**
  - Fitted by SVD on the TRAIN LMS matrix centred at the TRAIN mean. Each component's sign is fixed so that its largest-|loading| entry is positive.
  - `p ∈ {1,2,3}` components are kept. Scores are USQ-coded per component over the TRAIN score range at `b ∈ {1..10}`, giving `p·b` bits/sample.
  - The model cost is (3 mean + 3p loadings + 2p ranges) × 32 bits.
  - Decoding is `mean + scores·components`, then the opponent formulas.
- **(d) k-means VQ, d1 (primary):** fitted on TRAIN `x_opp` (2-D). **d2 (secondary):** fitted on TRAIN `x_LMS` (3-D).
  - `k ∈ {2,4,8,16,32,64}`.
  - Initialisation is k-means++ with `numpy.random.default_rng(20261004 + k)`. There are 10 restarts, drawn in sequence from that generator.
  - Lloyd iterations run until assignments are unchanged or 300 iterations are reached. An empty cluster is re-seeded at the point farthest from its assigned centroid.
  - The restart with the lowest TRAIN SSE is kept. Argmin ties go to the lowest index.
  - Encoding is the nearest centroid (Euclidean, in the fitted space), giving `log2 k` bits/sample.
  - The codebook cost is `k·d·32` bits.
- **(e) substrate minter:** `seeds/vision_colour_identity` through `domains/colour_identity_world`.
  - It uses the same boot as `scripts/marys_room_red_green.py::compress_field`: `boot_core(seeds=())`, `load_seeds_into([vision_colour_identity])`, the `qualia_space` manifest, `set_flag(identity=1)`, and the bound at its shipped default (armed).
  - **Declared integer scaling:** `cRG = rint(s·RG)` and `cBY = rint(s·BY)` (numpy round-half-even). The cells are `cL = cRG + s`, `cM = s`, `cS = cBY + 2s + cRG`, all integers, so the seed's own `ci_opponent` gives `crg = cRG` and `cby = cBY` exactly. `rrow`/`rcol` give the row order (TRAIN rows on `rrow = 0`, held-out rows on `rrow = 1`).
  - **Primary scale:** `s = 100`, a lattice step of 0.01 opponent units. Secondary scales are `s ∈ {10, 1000}`.
  - The minter sees no labels. It mints only on exact lattice-value clusters with count ≥ 3.
  - **Protocol e-T (RD-scored):**
    1. Mint on the TRAIN field and tick.
    2. Add the HO_core cells with `add_region` and tick again.
    3. Report categories minted on TRAIN, categories newly minted when held-out cells arrive (transductive, reported), and each held-out cell's assignment or refusal.
  - **Protocol e-H (counts only):** the held-out field alone on a fresh substrate, run for HO_core, HO_core_dup and HO_all.
  - **Code for e-T, per held-out sample:**
    - 1 flag bit.
    - If the substrate assigned the sample to a category: `ceil(log2 k)` bits, decoded at the prototype divided by `s`.
    - If refused, or `k = 0`: `B_s = Σ_dim ceil(log2(hi_int − lo_int + 1))` bits for the integer lattice coordinate over the TRAIN integer range (clipped), decoded at the lattice value divided by `s`.
    - The model cost is `k·2·32 + 128` bits.
- **Ablations:**
  - Opponent USQ coding only RG (`b` bits, decoded BY = 0) or only BY (decoded RG = 0).
  - The same axis drops applied to the unquantised eye vectors.
  - The sign rule as an alternative category rule (A2-2).
- **Label-leak check:**
  1. Every fit and encode function takes only a float array or integer cells.
  2. Every fitted model is refitted with the label array randomly permuted (`default_rng(20261004)`); the sha256 of the model parameters must be identical.
  3. The decoder anchors are the frozen theory-only A1 anchors, which are never fitted here.
- **Secondary rate column:** the empirical entropy of the held-out code indices is reported as a proxy. It is labelled as such, because it is not a realisable code without a transmitted model.

### A2-4 Operating point and the compression prediction (P6)

- **Total rate:** `R_total = fixed-length bits/sample + model bits / N_HO_core`.
- **Operating point:** for each representation, `R*` is the smallest `R_total` on its declared grid at which HO_core task accuracy is **≥ 0.95 · A0**. If no grid point reaches it, `R*` is undefined.
- **P6** (the plan's prediction: "a learned compact code will improve held-out description length over raw coordinates at a specified accuracy level"):
  - **Supported** iff `R*(VQ d1) < R*(raw LMS a)`, or `R*(raw)` is undefined while `R*(VQ d1)` is defined.
  - **Not supported** otherwise, including when `R*(VQ d1)` is undefined.
- **Secondary results, reported but not part of the verdict:**
  - The same comparison without model cost.
  - The comparison with PCA, VQ d2 or minter e-T (s = 100) as the learned code, and against (b).
  - A distortion operating point: the smallest `R_total` with HO_core mean angular error ≤ 5.0°.
  - The same operating points on HO_all.
  - A matched-rate table at total code lengths of 1–12 bits.
- **Intervals:** Wilson 95% for accuracy at each operating point. These are descriptive, for the reasons given in A1-4.
- **Determinism:** the script is fully seeded. It is run twice, and the sha256 of the result payload, excluding timestamps, must match.
- **Compression thesis criterion:** the minter's compression thesis counts as supported at the operating point only if e-T reaches the accuracy target at a rate below raw. It is expected to mint little or nothing except exact lattice repeats; if so, that is reported as is.

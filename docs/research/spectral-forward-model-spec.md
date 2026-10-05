# Spectral forward model specification (Phase 2)

Phase 2 of the Mary's Room empirical paper plan. This spec defines a **photon
source**: a generator that turns a scene description into the
`{column, wavelength_nm, count}` photon packets the `GraphEye` already consumes.
It changes nothing in the eye.

## Framing: the eye consumes photons, not reflectance

The eye's native input is a photon flux at the retina — a list of
`(wavelength_nm, count)` packets per retinal column
(`domains/photon_eye.py:submit_photons`, line 1688). Reflectance and illuminant
spectra are **not** inputs to the eye; they are the generative story that
produces the photon flux. The forward model therefore lives entirely *upstream*
of the eye and emits the same packet contract already in use. The eye stays
byte-unchanged; nothing in `cognitive_tasks.rs` or `photon_retina.json` is
touched.

This also fixes paper-plan review problem #5 (metamers/broadband) **without a
capability change to the eye**: the eye already accepts multiple wavelength
packets per column and the capture kernel sums `count·exp(−0.5·z²)` over all of
them (`cognitive_tasks.rs:386–389`). A broadband or metameric stimulus is just a
packet list with many wavelengths on one column. What was missing is only the
generator that produces that list from a scene — which is this spec.

## The eye's packet contract (verified, do not break)

From `submit_photons` (`photon_eye.py:1688–1708`):

- Each packet is `{"column": int, "wavelength_nm": float, "count": int}`.
- `column` is dropped if outside `[0, n_az)`.
- `count = max(0, int(count))` — **integer, non-negative**. The forward model
  must quantise to integer photon counts.
- Multiple packets may share a column; the capture kernel sums over all of them.
  **This is the mechanism that makes broadband and metameric stimuli
  representable.**
- Capture is `caught = dark_current + Σ count·exp(−0.5·z²)`,
  `z = (λ − center)/bandwidth`, over the four receptor Gaussians
  (`cognitive_tasks.rs:379–390`).

## Generative chain (scene → photon packets)

The forward model composes the standard colour-formation chain and then
discretises to packets. Each stage is explicit graph-external Python (a "photon
source" adapter), declared before any eye run.

```
reflectance R(λ)  ──┐
                    ├─►  radiance  Φ(λ) = E(λ)·R(λ)        (illuminant × surface)
illuminant E(λ) ────┘
                       │
   pre-receptoral  T(λ) │  (optional, OFF by default)
                       ▼
   at-retina SPD  Φ'(λ) = Φ(λ)·T(λ)
                       │
   scale to photons   │  N(λ) = round( k · Φ'(λ) · Δλ )   per sampled λ bin
                       ▼
   packets: for each λ bin with N(λ) > 0 ⇒ {column, wavelength_nm: λ, count: N(λ)}
```

### Stage definitions

1. **Reflectance / emission `R(λ)`** — per surface. Monochromatic lights are a
   degenerate `R` (a single bin). Munsell/natural reflectance sets may be loaded
   as tabulated spectra. For emissive stimuli, `R(λ)` is the emission SPD and the
   illuminant is omitted.
2. **Illuminant `E(λ)`** — declared SPD (e.g. equal-energy E, D65, incandescent
   A). For the pilot's monochromatic lights, `E` is a flat/unit SPD so the chain
   reduces to the current behaviour.
3. **Pre-receptoral filter `T(λ)`** — lens + macular transmittance, **and
   (optionally) the closed eyelid**. **OFF (T≡1) by default** so Phase 3
   baselines match the pilot; turned on for the "wrong-observer/wrong-optics"
   boundary conditions (RQ5) and for the **closed-eyelid stimulus** (below).

### Eyelid transmittance `T_eyelid(λ)` (the embodied-Mary filter)

The closed human eyelid is a real, measured instance of `T(λ)`: a strong
long-pass filter. This matters for the thought experiment, not just the model —
any embodied observer with blood-perfused eyelids and functioning L-cones has
received long-wavelength ("red") retinal flux through closed lids her whole life
(ambient light, pressure phosphenes aside). The classic premise "Mary has never
been exposed to red" is physically false for an embodied eye; the room cannot
close the eyelid's own filter.

Quantitative anchors (do not invent a curve):

- Bierman, Figueiro & Rea (2011), *Measuring and predicting eyelid spectral
  transmittance*, Ophthalmic Physiol Opt — mean eyelid optical density ≈ **2.1**
  (transmittance ≈ 0.8%) across 450–650 nm, with **substantially higher OD at
  short wavelengths**, i.e. the eyelid passes long wavelengths preferentially.
  [source](https://pubmed.ncbi.nlm.nih.gov/21309786/) Content rephrased for
  licensing compliance.
- Hemoglobin optics explain the shape: oxy/deoxy-haemoglobin absorb strongly
  below ~600 nm and absorption falls off sharply past ~600 nm, so transmittance
  climbs steeply through 600–650 nm and is highest in the deep red (650–700 nm).
  This is the same mechanism behind the characteristic red field seen through
  closed lids in bright light.

Declared parameterisation (frozen before any eye run; `T_eyelid` ∈ [0,1]):

```
OD(λ) = OD_short                                   for λ ≤ 600 nm
OD(λ) = OD_short − (OD_short − OD_long)·(λ−600)/100 for 600 < λ < 700 nm
OD(λ) = OD_long                                    for λ ≥ 700 nm
T_eyelid(λ) = 10^(−OD(λ))
```

with declared `OD_short = 3.0` (blue/green, ~0.1% transmittance) and
`OD_long = 1.3` (deep red, ~5% transmittance). These anchor to the 2.1 mean OD
and the long-pass direction of Bierman et al.; the exact slope is a declared
modelling choice, not fitted to eye output, and is subject to the same no-tuning
rule as the Gaussian centres. A sensitivity ablation over `OD_long ∈ {1.0,1.3,
1.6}` is declared to show the qualitative result (positive `red_green`) is not
knife-edge on the slope.
4. **Photon scaling `k`** — converts at-retina spectral radiance into expected
   quanta per bin. Anchored to retinal illuminance in trolands; see
   "Photon scaling `k`" below for the declared anchor.
5. **Quantisation** — `N(λ) = round(k·Φ'(λ)·Δλ)`, integer, ≥ 0. Deterministic
   rounding by default (no Poisson sampling), to preserve the eye's determinism
   and keep per-stimulus repeats identical. A **Poisson photon-noise variant** is
   an explicit, separately-declared option for a shot-noise boundary study; if
   used, the seed is recorded and repeats become genuine independent trials.

### Wavelength sampling (CIE/ISO standard practice)

Follows the colorimetry standard rather than an arbitrary grid:

- Range **390–780 nm** — inside the CIE/ISO reference range (360–830 nm;
  practical 380–780 nm) and covering the deep-red eyelid transmittance tail.
- **Default bin width Δλ = 1 nm**, the CIE/ISO 11664-3 reference summation
  interval. [CIE Colorimetry Part 3](https://cie.co.at/publications/colorimetry-part-3-cie-tristimulus-values-1),
  [ISO/CIE 11664-3:2019](https://knowledge.bsigroup.com/products/colorimetry-cie-tristimulus-values)
- **Δλ = 5 nm** as a declared ablation — the standard abridged interval
  (ASTM E308). Content rephrased for licensing compliance.
- The same λ grid is used for `R`, `E`, `T`, the CIE fundamentals (theory arm),
  and the packet emission, so the theory decoder and the photon source are
  commensurable.

### Photon scaling `k` — anchored to retinal illuminance (trolands)

Pure colorimetry (XYZ/LMS tristimulus) is scale-free and never fixes absolute
photon counts. A photon model needs an absolute anchor, and the convention in
retinal/photoreceptor modelling is **retinal illuminance in trolands**, with
well-established regime landmarks: rods-only ≈ 0.002–0.2 td, mesopic ≈ 2–20 td,
**cones-only ≈ 200 td**, typical daylight ≈ 10²–10⁴ td.
[retinal-illuminance regimes](https://pmc.ncbi.nlm.nih.gov/articles/PMC2063471/)
The troland → retinal irradiance → photoisomerisations-per-cone (quantal catch)
conversion is standard, using pupil area and the ~0.67 isomerisation quantum
yield. [quantal catch / isomerisation](https://pmc.ncbi.nlm.nih.gov/articles/PMC3265841/)
Content rephrased for licensing compliance.

Declared anchor (frozen before any eye run):

- `k` is set so a **reference white (equal-energy E) at a declared photopic
  level of ~100 td** (squarely cone-mediated) produces the per-column quanta
  budget. The absolute level is thus a named, physically meaningful photopic
  value, not an arbitrary count.
- **Pilot regression:** the budget is chosen so a monochromatic 610/530 nm
  column reproduces the pilot's 1000-quanta behaviour within rounding, so the
  pilot remains a valid anchor.
- Every reported stimulus states its retinal illuminance in trolands. The
  closed-eyelid stimulus (OD ≈ 2, ~100× attenuation) therefore lands at ~1 td —
  low mesopic/low-photopic but still a defined, reportable level, which is itself
  an honest fact about how dim the eyelid-filtered field is.

## Two consumers, one source (keeps Arm A↔B honest)

The same `Φ'(λ)` feeds both arms, which is what makes the agreement *earned*
rather than definitional (mechanism audit, problem #2):

- **Theory arm (Arm A):** integrate `Φ'(λ)` against the **CIE 2006 2° cone
  fundamentals** to get `(L,M,S)`, then `RG = L−M`, `BY = S−0.5(L+M)`. No
  photons, no quantisation, no saturation. This is Mary's pre-exposure
  prediction.
- **Eye arm (Arm B):** quantise `Φ'(λ)` to integer packets, submit to a fresh
  `GraphEye`, read `red_green`/`blue_yellow`. The eye applies **Gaussian capture
  (centres 564/534/420 nm ≠ CIE fundamentals) + Naka-Rushton saturation** before
  the same opponent formula.

The angular residual between the two is therefore attributable to exactly two
documented sources: (i) the saturating nonlinearity, (ii) the Gaussian-vs-CIE
sensitivity mismatch. The forward model must **not** tune the Gaussian centres,
`k`, or `Δλ` to shrink that residual against eye outputs — those are declared
before any eye run.

## Validation of the forward model itself (before any Mary claim)

Unit tests the generator must pass, independent of the Mary experiment:

1. **Monochromatic reproduction:** a single-wavelength `R` at `k`-anchored
   intensity reproduces the pilot's packets and the pilot's eye output for
   610 nm and 530 nm, within rounding.
2. **CIE recovery:** integrating a monochromatic `Φ'` against CIE 2006
   fundamentals returns the published `(L,M,S)` for that wavelength (the values
   already hard-coded in the pilot: 610 nm → (0.7057,0.2053,8.03e-6);
   530 nm → (0.7706,0.9357,0.0126)) within tabulated tolerance.
3. **Metamer construction:** two distinct `Φ'(λ)` can be built that integrate to
   the **same** CIE `(L,M,S)` (metameric under the standard observer). The eye,
   using *different* (Gaussian) sensitivities, is predicted to **break** that
   metamerism by a measurable opponent-vector gap — this is a concrete RQ5
   prediction and a direct test that the eye's sensitivities differ from CIE.
4. **Energy monotonicity / determinism:** scaling `k` scales total quanta;
   fixed inputs give identical packets (no RNG unless the Poisson variant is
   explicitly selected).
5. **Eyelid long-pass:** applying `T_eyelid(λ)` to a broadband ambient
   illuminant must (a) attenuate short/medium wavelengths far more than long
   (monotone transmittance rise across 600–700 nm), and (b) produce an at-retina
   SPD whose CIE integration gives **positive `L−M`** and whose quantised packets
   drive the eye to **positive `red_green`**. This is the embodied-Mary result as
   a passing test, not a rhetorical aside.

## Deliverable

`domains/spectral_forward.py` (photon source; graph-external, pure Python/NumPy)
plus `tests/test_spectral_forward.py` covering the four checks above. No edit to
`photon_eye.py`, `cognitive_tasks.rs`, or `photon_retina.json`.

## Amendment A0 (pre-run, forward model) — 2026-10-04

Written after implementing `domains/spectral_forward.py` and **before any Mary
experiment run** (no Arm A scoring, no Arm B stimulus has been submitted to an
eye; the only eye contact was the 610/530 nm pilot-regression unit test, whose
outputs were already known). Numbers below are from
`python -m scripts.spectral_forward_a0_report` → `results/spectral_forward_a0.json`
(provenance `engine b6a41e3bbba6`), computed from the forward model and the
documented capture formula (`caught = dark + Σ count·exp(−0.5 z²)`,
`act = caught/(caught + half_sat + adaptation)`, adaptation 0 on a fresh eye)
only. Data sources: `data/colour/PROVENANCE.md`.

### A0-a Quantisation: cumulative rounding is the default

Per-bin `round(k·Φ'·Δλ)` at 1 nm destroys dim/broadband stimuli (expected
counts ~0–3 per bin). **Default** is deterministic cumulative rounding:
`N_i = r(C_i) − r(C_{i−1})`, `C_i = Σ_{j≤i} q_j`, `r(x) = ⌊x + 0.5⌋`. It
conserves the total (`ΣN = r(Σq)`), keeps every running total within 0.5
quantum of the continuous one (so spectral shape is preserved), and is
deterministic. Naive per-bin rounding is a declared **ablation**
(`method='per_bin'`); Poisson (`method='poisson'`, explicit seed) is the
declared noise arm.

Capture error, eye-replica `caught` (quantised − continuous expected), L/M/S,
default OD params:

| Stimulus | Δλ | td at retina | E[quanta] | continuous L/M/S caught | cumulative: ΣN; ΔL/ΔM/ΔS | per-bin: ΣN; ΔL/ΔM/ΔS |
|---|---|---|---|---|---|---|
| reference white E, 100 td | 1 | 100 | 1000.00 | 259.586/210.665/112.983 | 1000; −0.020/−0.036/−0.053 | 991; −3.854/−16.768/+8.017 |
| eyelid, E ambient 100 td | 1 | 0.1455 | 17.22 | 0.417/0.219/0.113 | 17; +0.164/−0.128/−0.113 | **0**; −0.417/−0.219/−0.113 |
| eyelid, E ambient 1000 td | 1 | 1.455 | 172.24 | 4.171/2.194/1.130 | 172; +0.004/+0.003/+0.087 | 189; −3.590/−2.188/−1.130 |
| eyelid, E ambient 10⁴ td | 1 | 14.55 | 1722.39 | 41.707/21.940/11.298 | 1722; +0.000/−0.009/−0.013 | 1679; −21.821/−20.692/−11.298 |
| eyelid, D65 ambient 100 td | 1 | 0.1373 | 11.98 | 0.385/0.228/0.109 | 12; +0.201/−0.126/−0.109 | **0**; −0.385/−0.228/−0.109 |
| eyelid, D65 ambient 1000 td | 1 | 1.373 | 119.81 | 3.846/2.282/1.093 | 120; −0.003/−0.014/+0.109 | 103; −3.484/−2.279/−1.093 |
| eyelid, D65 ambient 10⁴ td | 1 | 13.73 | 1198.07 | 38.459/22.822/10.934 | 1198; +0.013/−0.019/+0.016 | 1148; −22.617/−21.859/−10.934 |
| reference white E, 100 td | 5 | 100 | 1010.22 | 259.585/210.664/114.824 | 1010; −0.243/−0.229/−0.052 | 1012; −0.359/−0.489/+0.801 |
| eyelid, E ambient 100 td | 5 | 0.1454 | 17.58 | 0.417/0.219/0.115 | 18; +0.208/−0.111/−0.115 | 19; −0.383/−0.219/−0.115 |
| eyelid, E ambient 1000 td | 5 | 1.454 | 175.81 | 4.170/2.194/1.148 | 176; +0.044/+0.081/+0.042 | 169; −2.575/−2.131/−1.148 |
| eyelid, E ambient 10⁴ td | 5 | 14.54 | 1758.12 | 41.699/21.937/11.482 | 1758; +0.041/+0.117/−0.026 | 1755; −3.527/−2.819/+0.834 |
| eyelid, D65 ambient 100 td | 5 | 0.1373 | 12.21 | 0.385/0.228/0.110 | 12; +0.215/−0.120/−0.110 | 13; −0.370/−0.228/−0.110 |
| eyelid, D65 ambient 1000 td | 5 | 1.373 | 122.10 | 3.845/2.282/1.104 | 122; +0.049/+0.039/+0.105 | 118; −2.670/−2.242/−1.104 |
| eyelid, D65 ambient 10⁴ td | 5 | 13.73 | 1220.97 | 38.450/22.819/11.037 | 1221; +0.070/+0.032/+0.100 | 1218; −3.765/−3.949/+0.716 |

At 100 td ambient the eyelid stimulus is only ~12–17 quanta total, so even
cumulative rounding has relative capture errors of order 30–100 % per cone
(irreducible at that count); per-bin rounding at 1 nm emits **no photons at
all**. Poisson (seed 0) errors are in the JSON.

### A0-b Quanta anchor (one declared constant)

The eye's quanta are model units, not calibrated isomerisations. Declared:

- Absolute SPDs are spectral radiance × pupil area, so
  `td = K_m,F · Σ Φ'(λ) V_F(λ) Δλ`, `K_m,F = 683/V_F(555.016) = 683.36265 lm/W`.
- **Energy → quanta (new, A0-d):** expected quanta per bin
  `q_i = QUANTA_SCALE · Φ'_i · Δλ · (λ_i / 560 nm)`. Photon number per unit
  energy ∝ λ; the spec's `k·Φ'·Δλ` omitted this. Energy-proportional
  conversion (`photon_conversion='energy'`) is kept as a declared ablation.
  The theory arm is unaffected (CIE fundamentals are energy-based and
  integrated against the energy SPD).
- **`QUANTA_SCALE = 1891.2408486093182`**, defined by: equal-energy E at
  **100 td** on the 1 nm grid yields **1000 expected model quanta per column**,
  i.e. the reference white carries exactly the pilot's per-column budget.
  Monochromatic stimuli specified as Q quanta bypass the constant
  (`monochromatic(λ, Q)`), and `monochromatic_spd(λ, Q)` → `quantize`
  reproduces the pilot packets `{column, 610.0|530.0, 1000}` exactly (unit
  test; the eye regression through the forward model returns the smoke
  values bit-exactly).
- Justification (capture formula + pilot operating point only; no opponent
  output was used): the pilot's 1000-quanta budget puts the L cone at 549 caught
  / activation 0.517 at 610 nm, i.e. near the Naka-Rushton semi-saturation
  point where the response is most sensitive to log intensity. Giving the
  reference white the same total budget keeps it on the same mid-range
  operating point without saturating:

| Reference white | L caught / act | M caught / act | S caught / act | rod caught / act |
|---|---|---|---|---|
| E 10 td | 26.0 / 0.048 | 21.1 / 0.040 | 11.3 / 0.022 | 23.0 / 0.022 |
| **E 100 td (anchor)** | **259.6 / 0.336** | **210.7 / 0.292** | **113.0 / 0.181** | 228.5 / 0.182 |
| E 1000 td | 2595.9 / 0.835 | 2106.6 / 0.804 | 1129.8 / 0.688 | 2283.8 / 0.690 |
| D65 100 td | 256.2 / 0.333 | 220.7 / 0.301 | 109.3 / 0.176 | 247.9 / 0.195 |
| A 100 td | 273.2 / 0.348 | 177.1 / 0.257 | 28.1 / 0.052 | 143.6 / 0.123 |

  Activations at the anchor stay well below 1; a 10× (1000 td) white reaches
  0.69–0.84 (strongly compressive but unsaturated), so the prereg's 0.1×–10×
  sweep spans ~0.05–0.84 L activation.
- Derived retinal illuminance of the pilot stimuli (1000 quanta):
  **610 nm → 185.2 td; 530 nm → 327.4 td.**
- Closed-eyelid stimulus, declared open-eye ambient levels **100, 1000,
  10 000 td** (spanning the spec's "typical daylight 10²–10⁴ td"); td behind
  the lid / expected quanta:

| OD_long | Ambient | 100 td amb. | 1000 td amb. | 10⁴ td amb. |
|---|---|---|---|---|
| 1.0 | E | 0.170 td / 32.9 q | 1.70 / 329 | 16.95 / 3289 |
| 1.0 | D65 | 0.157 / 22.6 | 1.57 / 226 | 15.66 / 2261 |
| 1.0 | A | 0.217 / 69.5 | 2.17 / 695 | 21.71 / 6950 |
| **1.3** | E | 0.145 / 17.2 | 1.45 / 172 | 14.55 / 1722 |
| **1.3** | D65 | 0.137 / 12.0 | 1.37 / 120 | 13.73 / 1198 |
| **1.3** | A | 0.175 / 35.9 | 1.75 / 359 | 17.54 / 3585 |
| 1.6 | E | 0.130 / 9.2 | 1.30 / 92 | 12.96 / 920 |
| 1.6 | D65 | 0.125 / 6.5 | 1.25 / 65 | 12.45 / 652 |
| 1.6 | A | 0.148 / 18.7 | 1.48 / 187 | 14.84 / 1869 |

  Eye-replica L activation behind the lid (OD_long 1.3, D65): 0.00075 /
  0.0075 / 0.070 at the three ambient levels — the eyelid field is very dim
  for this eye.

**Finding (not a parameter change):** the spec's statement "OD ≈ 2, ~100×
attenuation → ~1 td" is inconsistent with its own declared parameters. With
`OD_short = 3.0, OD_long = 1.3` the mean OD over 450–650 nm is 2.89 (not the
Bierman et al. 2.1), and attenuation of a luminance-weighted ambient is ~690× (E) to ~730× (D65)
(100 td → 0.14 td), not ~100×. The parameters are left unchanged (frozen); the
eyelid result must be reported with this caveat.

### A0-c Eyelid eye-response sign is a prediction, not a unit test

Spec test #5 is amended: the unit test checks **forward-model properties only**
— (a) `T_eyelid` strictly increasing across 600–700 nm, 10⁻³ ≤600 nm, 10⁻¹·³
≥700 nm; (b) at-retina SPD (E, D65, A × OD_long ∈ {1.0, 1.3, 1.6}) gives CIE
2° `L − M > 0`. Result: **CIE L−M > 0 in all 9 cases** (L−M/(L+M) = 0.19–0.50;
dominant wavelength 638–645 nm). The eye's `red_green` sign for the eyelid
stimulus is the preregistered Arm B prediction and is not asserted by any test.

### A0-e Opponent zero-crossings (CIE 2006 fundamentals, linear interpolation)

| Fundamentals | L − M = 0 | S − 0.5(L+M) = 0 |
|---|---|---|
| 2°, CVRL 1 nm (default) | **409.16 nm** and **554.08 nm** | **488.29 nm** |
| 2°, CIE table 5 nm | 408.24, 554.01 | 488.38 |
| 10°, CVRL 1 nm | 410.00, 551.75 | 482.46 |

L−M is positive below 409 nm (short-wavelength L̄ tail exceeds M̄), negative
409–554 nm, positive above 554 nm. The prereg's "boundary-dense sweep around
the RG zero-crossing" refers to the **554.08 nm** crossing (unique-yellow
region); the 409 nm crossing is a second, low-sensitivity boundary that the
`RG > 0 ⇒ red` rule will label "red" — Phase 3 must state how it is handled
before Arm B. (For reference only, not used to set anything: the eye's
Gaussians have equal linear L/M capture at 547.85 nm.)

### Other implementation notes

- Default 2° fundamentals: CVRL 1 nm 8-decimal tabulation; agrees with the CIE
  170-1 table 6.7 (the pilot's values) within 1.0e-5 absolute. The CIE 5 nm
  table is available as `source='cie_table'` (exact pilot values).
- 5 nm grid = exact subsample of the 1 nm tables; `QUANTA_SCALE` is not
  re-derived on 5 nm, so the 5 nm reference white carries 1010.2 quanta
  (Riemann-sum difference), reported, not corrected.
- Reflectances: ColorChecker 380–730 nm @10 nm, linear interpolation, 730 nm
  value held to 780 nm.
- Metamers: `metamer(base)` adds a null-space projection (w.r.t. the 3×N CIE
  2° LMS matrix incl. Δλ) of a smooth sinusoid, scaled to `amplitude` × the
  largest non-negativity-preserving step; CIE LMS identical to ≤ 2.3e-15
  relative; the SPDs differ by up to `amplitude` × max(base).

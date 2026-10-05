# Mary's Room: broad-spectrum identification, prediction and compression — RESULTS

This is the confirmatory study for the Mary's Room empirical paper plan
(`docs/research/marys-room-empirical-paper-plan.md`). It covers RQ1 (pre-exposure
identification), RQ2 (prediction of the eye's opponent state), RQ4 (compression)
and RQ5 (boundary conditions).

- Preregistration: `docs/experiments/marys-room-broad-prereg.md`, with amendments A0 (forward model), A1 (stimuli, decoders, truth, splits, metrics) and A2 (Arm C).
- Runners:
  - `scripts/marys_room_broad_theory.py` (Arm A plus the freeze)
  - `scripts/marys_room_broad.py` (Arm B, the eye)
  - `scripts/marys_room_rate_distortion.py` (Arm C)
  - `scripts/marys_room_broad_audit.py` (Phase 5 audit)
  - `scripts/marys_room_broad_boundary.py` (Phase 5 post-hoc analysis)
  - `scripts/marys_room_broad_review_fixes.py` (review response: errata and post-hoc baselines; no eye)

"Experienced", "red" and "green" refer only to the model eye's computed opponent
signals and the declared truth labels. None of the results below is a
measurement of phenomenal experience, and none is a claim about human qualia.

## Provenance and integrity

- Engine: `b6a41e3bbba6` (`/tmp/ocelot-marys-room/runners/dsl/python/substrate_rs/_native.abi3.so`, 1 other tree build shadowed). This is recorded in every result file.
- git HEAD is `3649fb17…` on branch `experiment/marys-room-eye-qualia`. No commits were made, so the hash lock below is the preregistration lock.
- Pilot regression: exact. 610 nm on column 0 gives (0.3436120168296669, −0.3456013062040921), and 530 nm on column 1 gives (−0.07537232767138446, −0.6214367610772381).
- Fidelity of the eye to its documented model:
  - On all 682 unadapted inputs, the eye equals the documented capture + Naka-Rushton formula recomputed from the stored packets (max |Δ| = 7.2e-16).
  - On all 39 adaptation inputs, the eye equals a replay of the 20-epoch adaptation recursion (max |Δ| = 5.0e-16).
  - Batched and fresh-eye runs were byte-identical on 15 probe stimuli.
- Repeat structure:
  - The 10 manifest duplicates are deterministic duplicates and are counted once in pooled metrics.
  - `wrong_observer` rows reuse their base stimulus's eye output.
  - Only the 120 `poisson` rows are independent trials.
  - All intervals describe this designed stimulus set; they are not sampling intervals over a population of stimuli.

### Freeze status (re-verified in Phase 5, `results/marys_room_broad_audit.json`)

| Item | Status |
|---|---|
| 24 A1-frozen non-prereg files (spec, forward model, theory script, manifest, Arm A, `PROVENANCE.md`, 18 raw/derived data files) | all match the 11:36:33 UTC freeze |
| Prereg, first 20 335 bytes (A1 text) | matches the A1 freeze hash `9e6344b6…` |
| Prereg, full file (A1 + A2) | matches the A2 lock `ecf2366a…` (11:55:47 UTC) |
| Arm B result `marys_room_broad.json` | sha `cac59dc4…`, identical to the hash Arm C recorded as its input |
| git HEAD | unchanged from the freeze |

`python -m scripts.marys_room_broad_theory --verify` prints `FREEZE VIOLATED`
for the prereg. This is expected: A2 was appended after the A1 freeze, and the
lock records it. The A1 content is verified by the prefix hash above. The theory
script itself is frozen, so its `--verify` path was not edited.

### Audit of headline numbers

`scripts/marys_room_broad_audit.py` recomputes numbers independently. Truth comes
from the frozen manifest. Theory LMS is recomputed from each recipe through the
forward model. Decoders, angles, Wilson intervals, the eye formula and the raw-LMS
quantiser are re-implemented from their written definitions.

**Result: 19/19 checks match within tolerance. No discrepancies were found.**

Scope of the audit: it checks scoring, decoding, the eye formula and Arm C
rate accounting. It is not independent of the colorimetry, because theory is
recomputed through the same `domains.spectral_forward`. It is also not
independent of the truth labels, which it reads from the manifest. The review's
spot-checks partly cover that gap: integration, V\*, K_m,F, the quanta anchor,
metamers, the eyelid OD and the anchors (`marys-room-broad-review.md`, "Verified
correct").

Checks:

- HO-core n = 272.
- Eye anchor accuracy 0.7684 (Wilson lower bound 0.7147).
- Eye sign accuracy 0.5551.
- Theory sign accuracy 0.6360 and theory anchor accuracy 0.7022.
- Median and mean theory↔eye angle: 3.6424° and 8.2079°.
- Eye equals the documented formula.
- Eyelid stimuli with RG > 0: 27/27, minimum RG 6.43e-4.
- Metamer pairs broken: 8/8, maximum gap 0.04474.
- The eye's RG zero matches the analytic Gaussian L=M crossing: 547.846 nm against 547.845 nm reported.
- Arm C: A0 = 0.7684; raw-LMS b=6 has accuracy 0.7537 and rate 18.636 bits; VQ k=64 has rate 19.563 bits; R\*(raw) re-derived from the RD rows.

## Deviations and stage-level declarations

These were declared before the eye outputs or Arm C quantities they govern were
seen, and are not part of A1.

- **A0-d.** Energy is converted to quanta with quantal weighting (λ/560 nm). The original spec omitted this factor. Energy-proportional conversion is kept as an ablation.
- **A0 eyelid finding.** The declared eyelid parameters (OD_short 3.0, OD_long 1.3) give a mean OD of 2.89 over 450–650 nm, not the cited 2.1. At 100 td ambient that leaves about 0.14 td behind the lid, not about 1 td. The parameters were left unchanged.
- **A0-e.** CIE 2° L−M has a second zero at 409.16 nm, so the sign rule calls 400–405 nm "red". This was declared before Arm B, and the rule was not redesigned.
- **Arm B analysis rules: stage-declared, not registered, timing unverifiable.** The Arm B stage declared these in `scripts/marys_room_broad.py` (`ARM_B_DECLARATIONS`, recorded in the result as `arm_b_declarations`): bins, the clear-chromatic margins, the metamer gap threshold (1e-6), the P1–P5 verdict rules, a bootstrap CI for angular error, and the eyelid reference stimuli.
  - They are not part of the A1 registration. The prereg (`:101`) asked for the primary metrics "without threshold pass/fail claims", so the pass/fail thresholds in the verdict table (0.90 agreement, ±20 nm, 10° and 0.10 margins, 1e-6 gap) go beyond it.
  - The Arm B script was not hashed into the freeze, and `marys_room_broad.json` does not record its sha256.
  - The script's mtime (11:48:08Z) is one second before Arm B's in-run freeze check (11:48:09Z). That is consistent with a single run, but it cannot exclude earlier runs or edits. So it **cannot be independently verified** that these rules were fixed before any eye output was seen.
  - The verdicts below are therefore stage-declared operationalisations of the registered predictions, not registered tests.
  - The script's hash now (review response) is `f06f87f5…`. It is recorded in `results/marys_room_broad_review_fixes.json` for future reference only; it certifies nothing about timing.
  - Arm C, by contrast, recorded its script hash (`53f10377…`) in its result, and that still matches the file.
  - For future stages, analysis scripts are to be hashed into the freeze before any eye contact.
- **Arm C.** The whole protocol is in A2, written after the Arm B outputs had been read but before any Arm C quantity was computed.
- **Post-hoc analyses.** Everything in the section "Boundary and failure analysis (RQ5) — POST-HOC" below. It changes no frozen quantity and no verdict.
- **Review response (2026-10-04).** The errata and post-hoc additions requested by the review (`marys-room-broad-review.md`) are listed under "Errata (review response)" below. Their numbers come from `scripts/marys_room_broad_review_fixes.py` → `results/marys_room_broad_review_fixes.json`.
  - That script runs no eye and changes no frozen item.
  - No frozen script, stimulus, decoder, anchor, split, threshold, quanta anchor or OD parameter was changed. So `post_freeze_changes` in the freeze file is not needed and was not added.

### Errata (review response, 2026-10-04)

- **E1 — Arm A pseudo-replication (accounting erratum, A1-4).** Prereg A1-4 required counts of theory-distinct conditions next to every Arm A statistic, and this doc omitted them. Arm A is scale-invariant, so a monochromatic λ at three intensities gives one theory prediction and one truth label, not three.
  - The Arm A tables below now report the distinct count n_d, using Arm A's own key: normalised theory LMS plus truth labels. This reproduces `n_theory_distinct_scored = 125`.
  - Accuracy, Wilson intervals and binomial p are recomputed at that level, and **the distinct-level numbers are the ones to cite**.
  - The row-level numbers are kept for traceability only. Their p-values and Wilson widths are wrong for the stated n.
  - For the eye, intensities are distinct inputs but strongly correlated. The eye accuracies and angles therefore also get a cluster bootstrap and a cluster majority-vote binomial:
    - Clusters are a recipe with its intensity removed: 130 hue-scored clusters, and 154 including achromatic ones.
    - The cluster bootstrap resamples clusters (B = 10 000, `default_rng(20261004)`).
    - The binomial counts a cluster as correct if more than half of its rows are correct, and tests against the row-level majority rate.
  - No verdict changes.
- **E2 — the P5 registered criterion is non-diagnostic.** See "Embodied-Mary result" below.
- **E3 — consistency checks, not empirical support.** P2(c) and P3, and the claim that the documented sources "account for" the theory↔eye difference, follow from the fact that the eye is deterministic code implementing the documented formula. They can fail only through a bug. They are relabelled as consistency checks.
- **E4 — forward-model and spec errata.** The frozen files are unchanged; the corrections are recorded here.
  - *"Hemoglobin-shaped" is wrong.* The eyelid filter (`spectral_forward.py:268`) is a declared piecewise-linear long-pass OD ramp: OD 3.0 up to 600 nm, linear to OD_long at 700 nm, then flat. It has no oxy-Hb band structure. "Hemoglobin-shaped" in prereg `:80` should be read as "declared long-pass ramp".
  - *The OD anchor is wrong.* The spec's "these anchor to the 2.1 mean OD" (`spectral-forward-model-spec.md:109`) is false as written: the parameters give a mean OD of 2.89 over 450–650 nm (A0).
  - *The citation is probably wrong.* The spec (`:88`) cites Bierman, Figueiro & Rea (2011) as *Ophthalmic Physiol Opt*. It is most likely *J. Biomed. Opt.* 16(6):067011. I have not verified this online, because network use in this study is restricted to datasets, so check it before the paper cites it.
  - *Dominant wavelength above about 660 nm.* `dominant_wavelength` uses the CIE 2012 xy locus up to 780 nm, and that locus folds at its long end. A post-hoc recomputation with the locus truncated at its x-maximum (703 nm) checked 612 recipes:
    - It changes dominant wavelength by more than 0.5 nm for 9 stimuli, all in `mono_sweep` above 660 nm.
    - It changes 0 `hue4` labels and 0 `binary` labels.
    - Raw dominant wavelengths above about 660 nm should not be quoted. No reported number here does so; the eyelid values are 638–645 nm.
  - *5 nm ablation convention.* Rectangle integration with both endpoints on the 5 nm grid over-counts quanta. At 100 td the counts are E 1010.2 vs 1000 (+1.0%), A 1356.6 vs 1339.7 (+1.3%) and D65 879.7 vs 873.5 (+0.7%). Trapezoid end-weights would give 997.4, 1335.6 and 871.9. This affects `ablation_grid5` only, and is documented as the convention rather than changed.
- **E5 — the Arm C label-permutation check is a signature guarantee, not a test.** `_permuted_labels` is computed but deliberately never passed to any fit, so the matching model hash is bound to match. The real guarantee is that no fit function has a label parameter (`fit_signatures` in the Arm C result).

## Pilot vs confirmatory

The v2 red/green pilot (`marys-room-red-green-results.md`) is feasibility
evidence only. Its 2/2 RQ1 result, its 0–100 direction score and its `48→28`
compression number are not cited as confirmatory evidence
(`docs/experiments/pilot-limits.md`).

Pilot vs confirmatory, by item:

- The pilot's earned angles (2.86° and 4.19°) are reproduced exactly by the pilot-regression stimuli.
- The pilot's 2/2 sign-rule success does not generalise: on the broad held-out set the theory sign rule does not beat the majority rate (below).
- The frozen four-category anchor decoder, which is not the pilot's decoder, labels the pilot's 610 nm stimulus **yellow** in both arms. The truth for that stimulus is red/purple, because 610 nm lies above the yellow|red midpoint of 590.65 nm, but the opponent direction falls nearer the yellow anchor.

## Stimulus set

There are 721 manifest entries and 626 distinct eye inputs. The set covers:

- monochromatic sweep 400–700 nm at 5 nm and 3 intensities (TRAIN at 10 nm)
- 1 nm boundary-dense sweep over 535–574 nm
- E, D65 and A illuminants
- 24 ColorChecker patches under each of 3 illuminants
- 8 CIE metamer pairs
- lens and macular wrong-optics conditions
- a 10° wrong-observer condition
- 27 eyelid stimuli
- 39 adaptation stimuli
- 120 Poisson trials
- a 5 nm grid ablation

HELD-OUT core contains 302 distinct inputs, 272 of them hue-scored; 30 are
achromatic (excitation purity < 0.05).

## RQ1 — theory-only identification (Arm A) and eye identification (Arm B)

| Pool | Decoder | Arm A (theory) | Arm B (eye) | Majority rate |
|---|---|---|---|---|
| TRAIN (n=93; theory-distinct n_d=31) | sign, binary | n_d: 22/31 = 0.710 [0.534, 0.839]; p vs majority 0.43 | 0.645 [0.544, 0.735] | 0.677 |
| TRAIN | anchor, 4-class | n_d: 28/31 = 0.903 [0.751, 0.967] | 0.860 (bal 0.888) | 0.355 |
| HELD-OUT core (n=272; n_d=125; 130 eye clusters) | sign, binary | **n_d: 81/125 = 0.648 [0.561, 0.726]; p vs majority (0.528) 0.0044** | 0.555; cluster-boot [0.461, 0.649]; cluster vote 75/130, p = 0.18 | 0.533 (rows) |
| HELD-OUT core | anchor, 4-class | **n_d: 81/125 = 0.648 [0.561, 0.726]; p vs majority (0.384) 2.2e-9** | 0.768; cluster-boot [0.700, 0.832]; cluster vote 92/130, p = 4.0e-13 | 0.393 (rows) |

Arm A intervals are Wilson 95% at the theory-distinct level (erratum E1). Eye
intervals are cluster bootstraps over intensity-condition clusters.

The superseded row-level values were:

| Pool | Arm A sign | Arm A anchor | Eye sign | Eye anchor |
|---|---|---|---|---|
| HELD-OUT core | 0.636 [0.577, 0.691]; bal 0.646; p 3.8e-4 | 0.702 [0.645, 0.753]; bal 0.722 | Wilson [0.496, 0.613]; p 0.25 | Wilson [0.715, 0.815]; p 2.7e-36 |
| TRAIN | 0.710 [0.611, 0.792] | 0.903 | — | — |

They treat deterministic theory repeats, and correlated eye intensity
triplicates, as independent, so they should not be cited.

An intensity-only collapse of Arm A, which merges rows sharing a recipe up to
intensity (130 conditions), gives sign 0.638 (p 0.0085) and anchor 0.654
(p 1.5e-9).

Per family, as theory sign / theory anchor / eye sign / eye anchor:

| Family (rows; theory-distinct n_d) | Theory sign (n_d) | Theory anchor (n_d) | Eye sign | Eye anchor |
|---|---|---|---|---|
| mono held-out (90; 30) | 20/30 = 0.667 | 27/30 = 0.900 | 0.633 | 0.811 |
| boundary_dense (96; 32) | 16/32 = 0.500 | 24/32 = 0.750 | 0.312 | 0.906 |
| reflectance (54; 54) | 0.667 | 0.519 | 0.648 | 0.574 |
| reflectance under A (18; 18) | 0.667 | 0.278 | — | 0.333 |
| metamer (10; 5) | 2/5 = 0.40 | 4/5 = 0.80 | 0.40 | 0.90 |
| eyelid (27; 9) | 9/9 = 1.00 | 2/9 = 0.22 | 1.00 | 0.48 |

Theory accuracy partly measures self-consistency (A1-1). Truth is the CIE 2012
xy chromaticity, which is a linear transform of the CIE 2006 LMS that Arm A
decodes, so theory and truth share an observer.

Truth is also illuminant-discounted: the white is A for scenes under A. The
decoders are not, because their anchors are fixed and E-referenced. That
mismatch is the whole explanation of the 0.278 for reflectance under A. It is
not a failure of physical prediction.

## RQ2 — theory↔eye agreement (primary metric: angle between the (RG, BY) vectors)

| Pool | Median angle [boot 95%] | Mean angle [boot 95%] | p90 | Max | Mean cosine | Label agreement, sign / anchor |
|---|---|---|---|---|---|---|
| HELD-OUT core (302) | 3.64° [2.88, 4.10]; cluster-boot [2.87, 4.13] | 8.21° [6.64, 9.94]; cluster-boot [6.02, 11.01] | 16.6° | 101.3° | 0.962 | 0.921 / 0.864 |
| TRAIN | 3.80° | 12.44° | — | — | 0.923 | — |

The first bracket is the stage-declared row bootstrap, which resamples correlated
intensity triplicates as if they were independent. The cluster bootstrap resamples
154 intensity-condition clusters instead (erratum E1). The median CI barely moves;
the mean CI widens from 3.3° to 5.0°.

- **By intensity (mono + boundary, median):** 4.31° at 100 q, 2.64° at 1000 q, 7.30° at 10⁴ q.
- **Calibration:**
  - The through-origin slope of eye RG on theory (L−M)/(L+M) is 0.052, 0.255 and 0.487 at the three intensities (Spearman 0.76, 0.87, 0.97).
  - A linear eye would give the same slope at every intensity, so the change in slope is the saturation signature.
- **Distance from the CIE L−M zero (554.08 nm), mono + boundary, pooled over intensities:**

| \|Δλ\| (nm) | n | Theory sign accuracy | Eye sign accuracy | Sign agreement | Anchor agreement | Median angle |
|---|---|---|---|---|---|---|
| 0–5 | 30 | 0.50 | 0.00 | 0.50 | 0.53 | 2.57° |
| 5–10 | 30 | 0.50 | 0.30 | 0.80 | 0.90 | 3.42° |
| 10–20 | 60 | 0.50 | 0.50 | 1.00 | 1.00 | 4.55° |
| 20–50 | 36 | 0.92 | 0.92 | 1.00 | 0.97 | 7.95° |
| 50–100 | 60 | 0.75 | 0.75 | 1.00 | 0.72 | 14.15° |
| 100–200 | 63 | 0.57 | 0.48 | 0.90 | 1.00 | 2.33° |

Label agreement collapses within about 10 nm of the boundary. The angular error
does not: it is smallest there.

## Preregistered predictions — verdicts

The predictions P1–P5 are registered in the prereg. The **verdict rules and
thresholds are not**: the Arm B stage declared them in `scripts/marys_room_broad.py`,
and it cannot be independently verified that they were fixed before any eye
output was seen (see "Deviations"). The prereg asked for these metrics to be
reported without threshold pass/fail claims, so read each verdict as the result
of a stage-declared rule. P6's rule is registered (A2).

| # | Prediction | Verdict (stage-declared rule) | Key numbers |
|---|---|---|---|
| P1 | Arm A beats chance on held-out monochromatic and reflected stimuli; accuracy degrades gracefully toward the RG zero | **Mixed** | At the theory-distinct level (E1): the sign rule does not beat majority (mono 20/30 = 0.667 vs 0.667, p = 0.59; reflectance 36/54 = 0.667 vs 0.685, p = 0.68). The anchor decoder does (mono 27/30 = 0.900, p = 1.9e-9, superseding the row-level 6e-26; reflectance 28/54 = 0.519 vs 0.370, p = 0.019). Sign accuracy over distance bins (1000 q) is 0.5, 0.5, 0.5, 0.92, 0.75, 0.57, which is not monotone. |
| P2 | Arm B agrees with Arm A on clearly chromatic items; agreement drops near the boundary; the error there comes from the documented sources | **Supported on (a) and (b) under the stage rule; (c) is a consistency check, not evidence** (E3), with a caveat | (a) Clear-chromatic agreement: sign 233/233, anchor 284/306 = 0.928. (b) Within ±20 nm: sign 0.825, anchor 0.858. (c) The documented formula reproduces the eye exactly, and quantisation contributes about 0° near the boundary, because those items are single-bin integer packets. Both facts hold by construction. Caveat: the angular error is *not* higher near the boundary (median 3.7° near vs 4.1° far); only label agreement drops. |
| P3 | The eye breaks at least some CIE metamers | **Holds: a consistency check** (E3) | 8/8 pairs broken. The CIE 2° gap is ≤2e-16; the eye gap is 0.003–0.045 (1.4–14.8°). This is guaranteed once the eye's sensitivities are not CIE fundamentals, so it is a readout of the sensitivity mismatch, not an independent test. |
| P4 | Theory predictions degrade under wrong-observer and wrong-optics conditions | **Not supported** (a failed prediction) | 10° theory is *closer* to the eye than 2° theory (median 2.52° vs 3.10°). Theory accuracy is equal by coincidence: 4/79 anchor labels and 2/79 sign labels differ between 10° and 2°, with offsetting effects (anchor 67/79 both; sign 53/79 both). Lens: median 5.77° vs 5.86° base, with the mean worse (30.5° vs 13.5°). Macular: median 3.02° vs 5.86°. Under the declared rule neither condition degrades. |
| P5 | The closed-eyelid stimulus gives positive eye `red_green` at every ambient level and every OD_long | **Holds as registered, but the registered criterion is non-diagnostic** (E2) | 27/27 positive. But 30/30 achromatic held-out stimuli are also positive (eye and theory), so the criterion would hold with no lid. For the discriminating measures, see the embodied-Mary section. Poisson: D65, OD 1.3, 100 td gives 9/10 red. |
| P6 (A2) | A learned compact code beats raw coordinates on held-out description length at the declared accuracy | **Not supported** (primary accounting, registered rule) | R\*(VQ, opponent) = 19.56 bits (k=64) against R\*(raw LMS) = 18.64 bits (b=6), target accuracy 0.730. The verdict is set by codebook amortisation: VQ wins only for N > 325.3, and HO-core has N = 302. |

### Embodied-Mary result (closed eyelid)

| Ambient (E / D65 / A) | td behind the lid | Quanta per column | Eye `red_green` | Eye (L−M)/(L+M) | Eyelid RG ÷ 640 nm RG at matched td |
|---|---|---|---|---|---|
| 100 td | 0.13–0.22 | 7–69 | 6.4e-4 – 1.1e-3 | 0.69–0.88 | 0.79–1.35 |
| 1000 td | 1.2–2.2 | 65–695 | 2.2e-3 – 9.6e-3 | 0.20–0.56 | 0.31–0.78 |
| 10⁴ td | 12–22 | 652–6949 | 0.020–0.082 | 0.19–0.53 | 0.30–0.75 |

- All three OD_long values (1.0, 1.3, 1.6) are pooled in each row.
- The pilot's 610 nm stimulus at 1000 q gives RG 0.344. The eyelid RG is 0.2%–24% of that.
- Truth (dominant wavelength) is red/purple, at 638–645 nm, for all 27 stimuli.
- The CIE theory sign is also positive for all 27.
- The frozen anchor decoder labels 13 of the eye vectors red/purple and 14 yellow. The 14 yellow cases are the brighter conditions with OD_long 1.3/1.6 (and D65 at OD 1.0). The theory anchor decoder labels only 6/27 red/purple.

**What this result shows (revised per review B1 / erratum E2).** The registered
criterion, positive eye `red_green`, does not separate eyelid light from
ordinary white light. In this eye, positive RG is the default response to
broadband light:

- All 30 achromatic held-out stimuli give eye RG > 0, from 0.0021 to 0.099. The theory gives RG > 0 for 30/30 as well.
- Bare E at 100 td gives RG 0.045, which is larger than 24/27 eyelid values. Bare A at 100 td gives 0.091, which is larger than all 27.
- The sign rule labels every white "red".

So P5 "holds as registered" without showing anything specific to the eyelid.
Measures that do discriminate, from `results/marys_room_broad_review_fixes.json`,
section `B1`:

| Measure | Eyelid (27) | White baseline | Separates? |
|---|---|---|---|
| Dominant wavelength / purity of the at-retina light (colorimetric, eye-independent) | 638–645 nm, purity 0.22–0.63 | achromatic (purity < 0.05) | **yes, cleanly** |
| Eye (L−M)/(L+M), expected-value replica (no rounding) | E 0.24–0.56, D65 0.19–0.53, A 0.39–0.56 | same illuminant, at matched at-retina td or at ambient: E ≤ 0.104, D65 ≤ 0.074, A ≤ 0.213 | **yes within illuminant**: 27/27 eyelid > matched white, minimum ratio 1.9×. Across illuminants the ranges touch: eyelid D65 OD 1.6 gives 0.190, below bare A at 10 td (0.204) |
| Eye (L−M)/(L+M) as submitted (quantised) | 100 td: 0.69–0.88; 1000/10⁴ td: 0.19–0.56 | matched-td white at 1–3 quanta: up to 0.68 | at 100 td it is **rounding-dominated**: expected value 0.20–0.56, and matched whites at 1–3 quanta reach 0.68 |
| Eye anchor decoder | 13/27 red/purple as submitted; **6/27 at expected value** (OD_long 1.0 under E and A only); rest yellow | 0/30 achromatic eye vectors red/purple (all yellow); 0/9 replica bare whites; 1/27 matched-td whites as quantised | partly: 9 of the 13 red/purple calls are at 100 td, where they rest on rounding |

- The bare whites "at matched at-retina td" are replica-eye computations of E, D65 and A whites scaled to each eyelid stimulus's at-retina td. They are post-hoc and involve no eye run; the replica equals the eye to 7e-16 on every unadapted input.
- At 100 td the matched whites carry only 1–3 quanta, and 2/27 of them even give RG < 0.

What the defensible statement is:

- Behind the declared lid, the light reaching the retina is long-wavelength dominant (638–645 nm). That is a colorimetric fact about the stimulus.
- Relative to white of the same illuminant and retinal illuminance, it pushes the model eye's L−M contrast toward the red side by at least 1.9×.
- The eye's own four-category read-out mostly calls it "yellow". It calls it "red/purple" robustly only for OD_long 1.0 under E and A.
- So the embodied Mary has had L−M-biased, long-wavelength-dominant retinal input. Whether her eye "has seen red" in the categorical sense is mostly *not* supported by this eye's decoder.
- The prereg's "demonstrating the literal premise … is false" (`:120–123`) does not follow from P5 as registered. The prereg is frozen, so it is not edited; this paragraph supersedes it.

**What it does not show.** It is not the same as "the eye has seen red":
- A positive RG is also what the eye produces for all monochromatic light from 548 to 576 nm, which is yellowish-green, and for every white. Most eyelid vectors are nearest the yellow anchor: 14/27 as submitted, 21/27 at expected value.
- At 100 td each condition delivers 7–69 quanta and L catches about 0.6 quanta. The deterministic RG lies at z = 1.5 above the Poisson mean, and Poisson noise flips the sign in 1/10 trials. The 640 nm references at matched td are 1–4 quanta.
  - The ratio "eyelid RG ≈ matched-td 640 nm RG" at 100 td (0.79–1.35 in the table above) is a comparison of single quanta and is **withdrawn as evidence**.
  - The expected-value capture keeps L > M, so the sign is right on average.
- It is a property of this model eye with these declared lid parameters. The filter is a declared long-pass OD ramp, not a hemoglobin spectrum (E4), and it attenuates more than the cited literature value (mean OD 2.89 vs 2.1).

Per the prereg's interpretation boundary, it bears on the literal, embodied Mary.
It does not bear on an idealised Mary, and it does not address the attended,
named instance.

### Arm C — rate–distortion (P6)

The table gives total bits per sample including model cost, at the
operating point accuracy ≥ 0.95·A0 = 0.730, on HO-core (N = 302).

| Representation | R\* | Configuration | Accuracy | Mean / median angle |
|---|---|---|---|---|
| (a) raw LMS | 18.64 | b=6 | 0.754 | 3.4° / 0.9° |
| (b) fixed opponent | **12.42** | b=6 | 0.735 | 13.5° / 1.0° |
| (c) PCA, p=3 | 25.91 | b=8 | 0.761 | — |
| (d1) VQ on opponent | 19.56 (6.0 without codebook) | k=64 | 0.776 | 10.4° / 3.4° |
| (d2) VQ on LMS | 26.34 | k=64 | 0.750 | — |
| (e) substrate minter, s=100 | undefined | best 0.699 at 17.8 bits | — | — |

- **P6 (primary): not supported.**
- **The verdict is set by codebook amortisation, not by an absence of compact codes.**
  - Raw LMS b=6 costs 18 + 192/N bits and VQ k=64 costs 6 + 4096/N, so VQ wins only for N > 3904/12 ≈ 325.3.
  - HO-core has N = 302 and loses. HO_all has N = 533 and wins.
  - VQ k=64 is fitted on only 93 TRAIN points, and it is the only VQ size that reaches the target (k=16: 0.643, k=32: 0.596).
  - The cleaner learned-vs-fixed comparison is VQ against the fixed opponent code (b). The fixed code wins with model cost (12.42 vs 19.56 bits; crossover N > 661). VQ wins without it (6 vs 12 bits).
  - Raw vs opponent mixes a theory-given drop from 3 to 2 dimensions with learning.
- Supported only under the secondary accountings: without model cost (6 vs 18 bits), and on the HO_all pool (13.68 vs 15.36 bits; without model cost, 6 vs 15).
- The largest saving at the operating point comes from the fixed, theory-given opponent projection, which needs no learning.
- The minter mints only on exact lattice repeats:
  - With unscaled floats there are no exact-value clusters with count ≥ 3, so it mints nothing.
  - At s=100 it mints 1 category on TRAIN, at (0,0), and 27 more transductively. These come from lattice coarseness, saturation and the dense sampling design; they are not hue categories.
- Ablations: neither axis alone supports the task (RG-only 0.426, BY-only 0.257).
- Per A2, the compression thesis is not supported at the declared operating point.

## Boundary and failure analysis (RQ5) — POST-HOC

**Everything in this section was chosen after the eye outputs were seen.** It
explains frozen results and changes no verdict. It uses no new eye runs. The
counterfactual "eyes" are computed from the forward model and the documented
eye parameters, and that replica is exact against the real eye (see
Provenance). Source: `results/marys_room_broad_boundary.json`.

### 1. Decomposing the theory↔eye angle: sensitivity mismatch vs nonlinearity

The design is 2×2, crossing sensitivity {CIE 2006 2°, eye Gaussians} with
transduction {linear, Naka-Rushton (half_sat 512, unadapted)}:

- T = CIE linear (the Arm A direction)
- CN = CIE + Naka-Rushton
- GL = Gaussian linear
- EY = the eye

CIE catch is expressed in eye-quanta units as QUANTA_SCALE·(Arm A LMS). Median angles:

| Pool | T→CN (NR on CIE) | GL→EY (NR on Gaussian) | T→GL (sensitivity, linear) | CN→EY (sensitivity under NR) | T→EY total | Shapley-style attribution, sensitivity / NR |
|---|---|---|---|---|---|---|
| HELD-OUT core (302) | 1.42° | 2.22° | 4.04° | 2.98° | 3.64° | 3.51° / 1.82° |
| mono+boundary ±20 nm (120) | 2.23° | 4.33° | 7.52° | 1.55° | 3.68° | 4.53° / 3.28° |
| mono+boundary, 100 q | 0.68° | 0.90° | 4.86° | 4.88° | 4.31° | 4.87° / 0.79° |
| mono+boundary, 1000 q | 3.81° | 5.32° | 4.86° | 3.12° | 2.64° | 3.99° / 4.57° |
| mono+boundary, 10⁴ q | 7.76° | 11.71° | 4.86° | 1.10° | 7.30° | 2.98° / 9.73° |

- **Which factor dominates depends on intensity.**
  - At 100 q the residual is almost all sensitivity mismatch.
  - At 10⁴ q the nonlinearity dominates.
  - At the 1000 q anchor the two partly cancel, so the total (2.64°) is smaller than either leg.
- Angles do not add, so the attribution is descriptive only.
- **Robustness:** renormalising the CIE per-quantum sensitivities to peak 1 per cone gives the same pattern. For HELD-OUT core, attribution is 3.32° / 1.86° and the total is 3.27°.
- **Every label disagreement on the RG sign comes from the sensitivity mismatch.** The NR leg never changes the RG sign (CN vs T: 302/302 equal; GL vs EY: 302/302 equal).
  - This is necessary for unadapted inputs: L and M share half_sat 512, so NR is the same monotone map on both, and L_act = M_act if and only if L_caught = M_caught.
  - Consequently the RG zero is 554.08 nm under both CIE-linear and CIE+NR, and 547.85 nm under both Gaussian-linear and the eye, at all three intensities.
  - NR does move the BY zero. On CIE it goes from 488.29 to 488.79 nm as intensity rises; on the Gaussians from 473.0 to 474.3 nm.
- **This refines the Arm B sequential decomposition**, which ran theory → Gaussian → NR and gave 7.5° then 4.3° near the boundary. That ordering overstates the sensitivity leg there: applied after NR, the sensitivity leg near the boundary is only 1.55°.

### 2. Metamer breaking comes from the sensitivity mismatch

| Pair | CIE linear gap | CIE+NR gap | Gaussian linear gap (angle) | Eye gap (angle) |
|---|---|---|---|---|
| white E | 0 | 0 | 0.286 (14.6°) | 0.318 (14.8°) |
| white D65 | 0 | 0 | 0.195 (8.5°) | 0.218 (8.1°) |
| white A | 0 | 0 | 0.087 (4.1°) | 0.112 (4.1°) |
| red / D65 | 0 | 0 | 0.065 (3.6°) | 0.067 (3.7°) |
| green / D65 | 0 | 0 | 0.060 (1.6°) | 0.063 (1.4°) |
| blue / D65 | 0 | 0 | 0.197 (7.6°) | 0.197 (7.7°) |
| yellow / D65 | 0 | 0 | 0.035 (1.5°) | 0.042 (1.4°) |
| dark skin / D65 | 0 | 0 | 0.144 (7.1°) | 0.143 (6.9°) |

Gaps are relative opponent-vector gaps; angles are in brackets.

A CIE-sensitivity eye with the same Naka-Rushton stage would keep every CIE
metamer, because identical catches produce identical activations. The Gaussian
catch alone already produces about the eye's full gap. The metamer result (P3)
is therefore a direct readout of the Gaussian-vs-CIE sensitivity mismatch.

### 3. Sign rule vs perceptual truth (cone-opponent zero ≠ unique hue)

At 1000 q, on 400–700 nm at 5 nm plus 1 nm samples over 535–574 nm:

- **Theory sign rule wrong at:** 410–475 nm and 555–575 nm.
- **Eye sign rule wrong at:** 400–475 nm and 548–575 nm.
- **The relevant loci:**
  - The CIE L−M zeros are at 409.16 and 554.08 nm; the eye's L−M zero is at 547.85 nm.
  - The declared unique blue is 478.0 nm and unique yellow is 576.3 nm.
  - The sign rule therefore inherits a gap of about 22 nm (theory) or about 28 nm (eye) between the cone-opponent zero and unique yellow, plus the whole violet–blue band.
- The theory's correct "red" at 400–405 nm is a coincidence of the 409 nm CIE zero; the eye's Gaussians have no violet zero.
- This failure is the expected one. It shows that L−M sign is not perceptual redness, and it holds for both arms, so it is not an eye defect.
- **Anchor-decoder failures:**
  - Theory: 490–495, 546–554 and 595–605 nm.
  - Eye: 475–495, 546–548 and 595–610 nm.
  - These sit at the declared category midpoints, which is where nearest-anchor decoding is fragile.

### 4. Adaptation

- **The mechanism is confirmed.** Replaying the documented recursion (adaptation += 0.12·(caught − adaptation) for 20 epochs, then the test epoch) reproduces the eye's adaptation state (max |Δ| 3.1e-13) and the test percepts (max |Δ| 5.0e-16).
- **The six RG sign flips are all from red to green.** The 610 nm field flips the tests at 550, 554, 560 and 570 nm and the E white; the E-white field flips 550 nm.
  - The five flipped chromatic tests are truth-greenish. Adaptation to red-side light therefore moved the eye's effective RG zero toward longer wavelengths and *corrected* those eye labels.
  - The unadapted theory cannot follow this, which is why theory↔eye angle rises from 3.15° unadapted to 7.23° adapted.
- **Post-hoc: CIE fundamentals with the same gain-control model.** This raises sign agreement with the adapted eye from 0.846 to 0.949 (37/39) and lowers the median angle from 7.23° to 6.37°.
  - Its sign accuracy against truth is 0.722, the same as the eye's; the unadapted theory's is 0.750.
  - Most of the adaptation failure is therefore the absence of an adaptation model in Arm A, which was declared. It is not unpredictable eye behaviour.

### 5. Wrong observer and wrong optics (why P4 failed)

- **10° observer.** The 10° fundamentals put the L−M zero at 551.75 nm, between CIE 2° (554.08 nm) and the eye (547.85 nm). The "wrong" observer is therefore closer to this eye's Gaussians (median 2.52° vs 3.10°).
  - P4 assumed the 2° observer is the right model of the eye. It is not: the eye has its own, non-CIE sensitivities. The failure of P4 is informative, and it was not tuned away.
- **Pre-receptoral filters.** The lens and macular filters change the at-retina SPD, and therefore the truth, as much as they change the eye. Theory accuracy against the filtered truth stays equal.
  - The lens shows its effect only in the heavy tail: mean angle 30.5° vs 13.5°, with 62.5% of pairs worse.
  - Under the median-based rule this counts as no degradation.

### 6. Quantisation method and Poisson variance

These are replica outputs from alternative packetisations of the same frozen
SPDs, on HELD-OUT core. The reference is the frozen eye (cumulative rounding,
quantal conversion), whose anchor accuracy is 0.768. The Poisson seeds are
post-hoc (77 000 000 + 1000·r + stimulus index) and disjoint from the A1 seeds.

| Packetisation | Zero vectors | Anchor label changes / 302 | RG sign changes | Anchor accuracy |
|---|---|---|---|---|
| per-bin rounding | 18 | 57 | 25 | 0.794 |
| energy-proportional conversion (A0 ablation) | 0 | 15 | 4 | 0.743 |
| Poisson, 5 independent realisations | 0 | 17–20 | 2–5 | 0.765–0.776 |

- The headline anchor accuracy is stable to within about ±0.03 across packetisation choices.
- Per-bin rounding deletes every photon from the dimmest eyelid and reflectance inputs; those return zero vectors, which the decoders score as undecided.
- The frozen Arm B Poisson trials (10 per subset) agree with this:
  - Monochromatic and white stimuli are 10/10 label-stable, with RG SD between 1e-4 and 4.4e-3.
  - The eyelid at D65 OD 1.3, 100 td (about 12 quanta) gives RG 2.5e-4 ± 4.6e-4 and 1/10 sign flips. The deterministic value (9.4e-4) lies at z = 1.5, so cumulative rounding at that photon count is biased toward red.
  - Eyelid results at 100 td therefore rest on single-quantum statistics.

## Interpretation (model-level only)

- **Prediction before exposure is partial.**
  - Theory alone predicts the eye's opponent direction to a median of 3.6° on held-out stimuli (cluster-bootstrap 95% [2.9°, 4.1°]).
  - With a four-anchor decoder, theory classifies held-out hues above chance: 81/125 theory-distinct conditions = 0.648 vs majority 0.384. That accuracy is partly self-consistency, because truth uses the same CIE observer (A1-1).
  - The preregistered L−M sign rule is a poor model of perceptual red/green in either arm, because the cone-opponent zero is not unique yellow.
- **Where theory and eye differ, the difference decomposes into** two documented, non-free sources: the Gaussian-vs-CIE sensitivity mismatch and Naka-Rushton saturation. Their balance depends on intensity.
  - That the documented sources reproduce the eye exactly is a consistency check (E3): the eye *is* that formula. It is not an empirical finding about the eye.
  - The informative part is the post-hoc attribution of *which* source matters where.
  - All sign disagreements and all metamer breaks trace to the sensitivity mismatch.
  - Adaptation errors trace to the declared absence of an adaptation model.
- **The post-exposure state lies in the same two-axis opponent coordinate system as the prediction.** This is the RQ3 sense of "same kind". It holds by design of the shared opponent read-out, and is not an independent finding.
- **The compression thesis is not supported** at the declared operating point, once codebook cost is charged. The failure comes from codebook amortisation at N = 302, against a crossover at about 325.
- **The prereg's interpretation-boundary argument is not a finding.** It says retreating to an idealised Mary "concedes the physicalist's point" (prereg `:167–176`), but that is a philosophical argument. The study's test of the representational-format leg (Arm C) came back negative, so the paper must not present that passage as a result.
- None of this measures or establishes anything about human phenomenal experience.

## Raw outputs

| Content | File |
|---|---|
| Manifest | `results/marys_room_broad_stimuli.json` |
| Arm A | `results/marys_room_broad_armA.json` |
| Arm B | `results/marys_room_broad.json`, `results/marys_room_broad_per_stimulus.csv` |
| Arm C | `results/marys_room_rate_distortion.json`, `results/marys_room_rate_distortion_csv/` |
| Freeze | `results/marys_room_broad_freeze.json` |
| Audit | `results/marys_room_broad_audit.json` |
| Post-hoc | `results/marys_room_broad_boundary.json` |
| Review response (errata, white baseline, distinct-level statistics) | `results/marys_room_broad_review_fixes.json` (from `scripts/marys_room_broad_review_fixes.py`) |

`data/` and `results/` are gitignored, so committing these needs `git add -f`.

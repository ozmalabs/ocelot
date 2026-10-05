# Review: Mary's Room broad confirmatory study (Arms A/B/C, Phase 5 write-up)

Scope: the uncommitted work listed in the request. The `.so`/`build.json` changes
are ignored. No eye was run for this review. Every spot-check used the frozen
manifest and result files, plus `domains/spectral_forward.py`, run under
`/home/matt/ozmadev/ocelot/.venv/bin/python`.

The pipeline is sound and the freeze held. I found no label or eye-output
leakage into any decoder, anchor, split, threshold, quanta anchor or codebook,
and the forward-model numerics check out. The problems are with what the
headline results are said to show.

The P5 eyelid result is the main one. The eye's `red_green` is positive for
every white and grey stimulus in the set, so "positive RG behind the lid" does
not separate eyelid light from ordinary white light. Separately, Arm A's
inferential statistics count deterministic theory repeats as independent.
Finally, the P1–P5 verdict rules sit in an Arm B script that was never
hash-locked before it ran.

Watch for:
- P5 cannot discriminate as stated (confirmed).
- Arm A p-values and intervals are pseudo-replicated (confirmed).
- There is no way to check that the verdict rules were fixed before the eye run (confirmed).
- P6's failure depends on the pool size, N = 302 against a crossover of 326 (confirmed).

**Verdict: ACCEPT-WITH-FIXES** (NEEDS_CHANGES until B1–B3 are addressed in the
results doc; no re-run is required).

## High-level view

**Freeze.** All 24 non-prereg A1 files match the freeze hashes. In the prereg,
the A1 prefix (20 335 bytes) matches the A1 hash, and the full file matches the
A2 lock. HEAD is unchanged. Arm B checked the freeze before it ran (11:48:09Z)
and again after (11:48:22Z). Arm C records the sha of the Arm B result it read.
Nothing frozen changed after eye outputs were seen. The two analysis layers that
were not frozen are the Arm B verdict rules and the A2 protocol. A2 was written
after the Arm B summaries had been read, and the docs say so.

**Leakage.** The decoders and anchors come only from CIE values and Kuehni's
loci. Truth comes only from the CIE 2012 xy chromaticity of the at-retina SPD.
`QUANTA_SCALE` is defined from E at 100 td. The Arm C quantiser ranges, PCA and
k-means are fitted on TRAIN eye vectors, and labels reach only the scorer. The
one place a held-out quantity sets a threshold is the operating-point target,
0.95·A0, where A0 is the eye's held-out accuracy. That is declared, it applies
to every representation equally, and it is a reporting rule rather than a fit.

**Scientific claims.** Three claims are stronger than the evidence:
- **The eyelid.** RG > 0 is the eye's default response to broadband light.
- **"Documented sources account for the difference."** This is an identity: the eye *is* the documented formula.
- **Compression.** P6 is lost on codebook amortisation just below the crossover N.

The results doc is otherwise careful about phenomenal experience and the
idealised Mary.

<details>
<summary>Issues (14)</summary>

1. **P5 sign is non-diagnostic** (blocking): every white or grey stimulus gives RG > 0. Report the white baseline and rest the eyelid claim on dominant wavelength, rg_rel and anchor labels.
2. **Arm A pseudo-replication** (blocking): 272 rows contain 125 theory-distinct conditions. Report distinct n, and give p-values and CIs at the distinct level.
3. **Verdict rules not locked** (blocking): the Arm B script was not hashed before the run. Reword the "fixed before the first eye submit" claim as stage-declared and unverifiable.
4. **P6 depends on N**: the crossover is N ≈ 326 against HO_core's 302. State this, and add the VQ-vs-opponent comparison.
5. **Identity presented as evidence**: P2(c), "accounted for" and P3 hold by construction. Label them consistency checks.
6. **Truth shares the CIE observer and discounts the illuminant**: repeat the caveat at `:344` and `:134`.
7. **Dominant wavelength above 660 nm**: the long end of the locus folds. Truncate it, or don't quote those values.
8. **5 nm grid over-counts quanta by about 1%**: use trapezoid end-weights or document the convention.
9. **Vacuous label-permutation check**: describe it as a signature guarantee, not a test.
10. **"Hemoglobin-shaped" and the 2.1 OD anchor**: rename the filter, correct the spec line, and check the Bierman citation.
11. **100 td eyelid rests on single quanta**: qualify or drop the matched-640 nm ratio at 100 td.
12. **Prereg "concedes the physicalist's point"**: keep it out of the findings, since Arm C was negative.
13. **Audit scope**: say that it does not independently check the forward model or the truth.
14. **Minor**: the equal 10°/2° accuracies are a coincidence of offsetting changes.

</details>

## BLOCKING

1. **P5 eyelid sign cannot discriminate (confirmed).**

   Where the claim is made:
   - `docs/experiments/marys-room-broad-results.md:171` (verdict row)
   - `:188–191` ("What this result shows")
   - `docs/experiments/marys-room-broad-prereg.md:120–123, 138–141`

   What the data show:
   - All 30 achromatic HELD-OUT core stimuli give eye `red_green` > 0, and so does the CIE theory (30/30).
   - Bare E at 100 td gives RG 0.045. Bare A at 100 td gives 0.091.
   - Both exceed many eyelid values (eyelid 10⁴ td: 0.020–0.082) and the whole 100 td eyelid range (6.4e-4 to 1.1e-3).
   - The sign rule labels every white "red".

   So "positive RG at every level" would hold with no lid at all. The prereg's
   "demonstrating the literal premise … is false" does not follow from P5. The
   "What it does not show" list names the yellow confound but not this one.

   Fix:
   - State the white baseline next to P5.
   - Move the evidential weight to the measures that do discriminate. The at-retina light has dominant wavelength 638–645 nm (a colorimetric fact that does not depend on the eye). The eye's (L−M)/(L+M) is 0.69–0.88 at 100 td and 0.19–0.56 brighter, against 0.013–0.20 for bare E/D65/A. The eye's own anchor decoder calls 13/27 red/purple.
   - Downgrade the P5 wording to "supported as registered, but the registered sign criterion is non-diagnostic".

2. **Arm A reports deterministic theory repeats as independent trials (confirmed).**

   Where:
   - Results doc `:122` (p vs majority 3.8e-4, Wilson intervals on n = 272) and `:167` (P1 "mono 0.900, p=6e-26").
   - Computed in `scripts/marys_room_broad_theory.py:581–613` (`score`) over pools built at `:658–678`.

   Why it matters: Arm A is scale-invariant, so each monochromatic λ appears three
   times with an identical theory prediction, once per intensity. Illuminants
   across td, eyelid ambient levels and metamer bases repeat in the same way.
   Arm A's own record counts 125 theory-distinct conditions in HELD-OUT core,
   not 272.

   Recomputed with the intensity triplicates collapsed:

   | Quantity | As reported | Collapsed |
   |---|---|---|
   | HELD-OUT core sign rule: accuracy (p vs majority) | 0.636 (3.8e-4) | 0.682 (0.011), n = 148 |
   | HELD-OUT core anchor decoder accuracy | 0.702 | 0.601 |
   | Mono held-out anchor, P1 (p) | 6e-26 | 27/30 (1.9e-9) |

   No verdict changes, but the reported p-values and Wilson widths are wrong for
   the stated n. Prereg A1-4 required theory-distinct counts to be reported next
   to these numbers, and the results doc omits them.

   The eye pools are less affected, because NR makes the three intensities
   distinct inputs, but they are still strongly correlated. The eye p = 2.7e-36 (`:123`)
   and the angle bootstrap CIs in the RQ2 table resample those correlated
   triplicates too.

   Fix:
   - Add n_theory_distinct to every Arm A row.
   - Report Arm A p-values and CIs at the distinct-condition level, or drop the p-values.
   - Note that the angle bootstrap resamples correlated intensity triplicates.

3. **No checkable record that the verdict rules came before the eye run (confirmed).**

   Where:
   - Results doc `:80` asserts the rules were "fixed … before the first eye submit".
   - The rules live in `scripts/marys_room_broad.py:47–101` (`ARM_B_DECLARATIONS`).

   Why it matters:
   - The script is not in `marys_room_broad_freeze.json`.
   - `marys_room_broad.json` does not record the script's sha256.
   - The file's mtime (11:48:08Z) is one second before the run's freeze check (11:48:09Z). That is consistent with a single run, but it cannot exclude earlier runs or edits.

   Prereg `:101` also says the primary metrics are reported "without threshold
   pass/fail claims". The verdict table adds thresholds of 0.90 agreement, 10°
   and 0.10 margins, and 1e-6 metamer gap.

   Fix: change `:80` and the verdict-table header to say that the rules are
   stage-declared, are not part of the registration, and that their timing
   cannot be verified independently. For future stages, hash the analysis script
   into the freeze before any eye contact.

## NON-BLOCKING

4. **P6 hinges on N (confirmed).**
   - Raw LMS costs `18 + 192/N` bits and VQ k=64 costs `6 + 4096/N`, so VQ wins for N > 3904/12 ≈ 325.3.
   - HO_core has N = 302 and loses. HO_all has N = 533 and wins.
   - The rule is applied correctly, but "the compression thesis is not supported" (`:223`, `:350`) should state that the verdict is set by codebook amortisation just below the crossover. It is not evidence against compact codes as such.
   - VQ k=64 is fitted on 93 TRAIN points, close to memorising them, and it is the only VQ size that reaches the target (k=16 scores 0.643, k=32 scores 0.596).
   - "Raw vs opponent" mixes a theory-given drop from 3 dimensions to 2 with learning. The cleaner learning comparison, VQ d1 against (b), is 19.56 vs 12.42 bits with model cost and 6 vs 12 without.

5. **"Accounted for by documented sources" is an identity (confirmed).**
   - Results `:346` and the P2(c) clause depend on two facts: the replica equals the eye to 7e-16, and the near-boundary quantisation leg is 0.
   - The eye is deterministic code implementing that formula, so (c) can fail only through a bug.
   - The near-boundary items are all single-bin integer packets, so their quantisation error is zero by construction.
   - P3 (metamer breaking) is guaranteed too: the eye's sensitivities are not CIE, so CIE metamers cannot all stay metamers.
   - Present both as consistency checks, not empirical support.

6. **Truth shares the observer with Arm A (confirmed, declared in A1-1).** The
   CIE 2012 XYZ used for truth is a linear transform of the CIE 2006 LMS used by
   Arm A. Arm A accuracy is therefore partly self-consistency, and "well above
   chance (0.702)" (`:344`) needs the A1-1 caveat repeated. Truth is also
   discounted for the illuminant (the white is A for scenes under A) while the
   decoders are not. That mismatch, by definition, explains the 0.278 figure for
   reflectance under A (`:134`), and it should be said there.

7. **Dominant wavelength above 660 nm is wrong (confirmed, no label impact).**
   `dominant_wavelength` (`domains/spectral_forward.py:347–390`) uses the CIE 2012
   xy locus up to 780 nm. That locus folds and jitters at the long end, so
   11 of the monochromatic stimuli between 661 and 686 nm return 702–775 nm
   (for example 661 → 774.7 and 686 → 717.4). Across 395–780 nm, 54 λ are off by
   more than 0.5 nm. Every affected λ is above 590.65 nm, so
   `hue4` and `binary` are unaffected. Do not quote raw dominant wavelengths
   above about 660 nm. The fix is to truncate the locus at its extreme point
   (about 700 nm).

8. **The 5 nm ablation over-counts quanta (confirmed).** Rectangle integration
   with both endpoints inside 390–780 nm spans 395 nm on the 5 nm grid against
   391 nm on the 1 nm grid. E at 100 td therefore gives 1010.2 quanta instead of
   1000, and A gives 1356.6 instead of 1339.7. The td normalisation does not
   absorb the difference, because V* is about 0 at the ends. LMS changes by less
   than 1e-4 relative. This affects `ablation_grid5` only. Use trapezoid
   end-weights, or document the convention.

9. **The label-leak check is vacuous (confirmed).** In
   `scripts/marys_room_rate_distortion.py:487–496`, `_permuted_labels` is
   computed but deliberately never used, so the hash after "permutation" is
   bound to match. The fit functions' signatures are the real guarantee.
   Describe the check that way rather than as a test.

10. **The eyelid model is not hemoglobin-shaped, and its citation is likely wrong.**
    - Prereg `:80` and results `:188` call the lid filter "hemoglobin-shaped". It is a piecewise-linear OD ramp (`spectral_forward.py:268`) with no oxy-Hb band structure (confirmed). Call it a declared long-pass ramp.
    - The parameters give a mean OD of 2.89, not the cited 2.1. This is disclosed, but the spec's "anchor to the 2.1 mean OD" (`spectral-forward-model-spec.md:109`) is false as written.
    - The citation, "Bierman, Figueiro & Rea (2011) … Ophthalmic Physiol Opt" (spec `:88`), is likely *J. Biomed. Opt.* 16(6) 067011. Check the journal and the PubMed ID.

11. **The 100 td eyelid result rests on rounding (confirmed, partly disclosed).**
    - Each condition has 7–69 quanta, and L catches about 0.6 quanta.
    - The deterministic RG sits at z = 1.5 above the Poisson mean.
    - The 640 nm references are 1–4 quanta.
    - The expected-value capture keeps L > M, so the sign holds on average, but "about as large as matched-td 640 nm light" is a comparison of single quanta. Say so, or drop the 100 td ratio.

12. **The interpretation boundary in the prereg goes beyond what the study tests (likely).**
    - Prereg `:167–176` argues that retreating to an idealised Mary "concedes the physicalist's point that the remaining gap concerns access, attention, and representational format".
    - That is a philosophical argument, not a result. Arm C, the declared test of the representational-format leg, came back negative (the minter mints only lattice repeats).
    - The results doc handles this correctly at `:198–200`. The paper should not lift the prereg passage as a finding.

13. **The audit is not independent of the forward model or of truth (confirmed).**
    - `marys_room_broad_audit.py` recomputes theory through `domains.spectral_forward` and takes truth from the manifest. It therefore checks scoring, not colorimetry or truth.
    - My spot-checks partly cover that gap (see below), but say so in the "Audit" paragraph.

14. **Minor.**
    - The 10° and 2° theory accuracies are equal by coincidence: 4/85 labels differ and the changes offset. "Theory accuracy is equal" should not be read as "no change".
    - `theory_for_spd` returns `sign_margin_rel = 0.0` when L+M = 0. Harmless.

## Verified correct

- **Freeze:**
  - `sha256sum` re-run: all 24 non-prereg A1 entries match.
  - Prereg: the first 20 335 bytes match the A1 hash `9e6344b6…`, and the full file matches the A2 lock `ecf2366a…`.
  - Arm B's in-run freeze checks (before and after) pass.
  - The Arm C input sha equals the current `marys_room_broad.json`.
  - Arm C's two-run payload hashes are identical.
- **No eye import in Arm A:** `marys_room_broad_theory.py` and `_boundary.py` both assert it.
- **Anchors:**
  - The blue, green and yellow anchors are built only from linear interpolation between TRAIN brackets of the CIE table.
  - The red anchor is a bisection on E-referenced xy.
  - Kuehni weighted means re-derived: UB 478.04, UG 514.75, UY 576.28, UR complementary 495.24. The hue4 midpoints 496.4, 545.55 and 590.65 follow.
  - I could not verify the Kuehni table entries against the source.
- **CIE integration:** Δλ is applied (`spd @ lms · step`). V* equals 0.68990272 L + 0.34832189 M to 5e-8. K_m,F = 683/V_F(555.016) = 683.363.
- **Quanta anchor:** E at 100 td gives 100.000 td and 1000.000 quanta. `derive_quanta_scale()` reproduces `QUANTA_SCALE` exactly. The quantal λ/560 weighting is correct.
- **Cumulative rounding:** non-negative counts, and the total equals round(Σq) (A: 1340 vs 1339.74). Implemented as declared.
- **Metamers:** CIE LMS relative difference 1.1e-15, minimum SPD > 0, spectral difference about 47% of the base peak.
- **Eyelid formula:** OD = 3.0 up to 600 nm, a linear ramp to OD_long over 600–700 nm, then OD_long. Mean OD over 450–650 nm is 2.892, matching A0. T(600) = 1e-3 and T(700) = 0.050.
- **Metric code:**
  - The Wilson formula and exact binomial tail are correct.
  - The stratified bootstrap for balanced accuracy is implemented as declared.
  - The angle uses a clipped acos on 2-vectors, with zero vectors excluded (Arm B) or set to 90° (Arm C), as declared.
- **Arm C rate arithmetic:**
  - Raw b=6: 18 + 192/302 = 18.636.
  - VQ k=64: 6 + 4096/302 = 19.563.
  - Opponent b=6: 12 + 128/302 = 12.424.
  - The raw operating point (b=5 fails at 0.706 and b=6 passes at 0.754 against the 0.730 target) matches the CSV rows.
- **Repeat handling:** the 10 manifest duplicates are excluded from pooled metrics, the wrong-observer rows reuse their base's eye output, and only the Poisson rows are called independent trials. The pseudo-replication in item 2 is about theory repeats across intensities, which A1-4 asked to be reported.
- **Unadapted Naka-Rushton cannot change the RG sign** (L and M share half_sat 512 with zero dark current). The post-hoc claim that every sign disagreement comes from the sensitivity mismatch follows.
- **Tests:** `tests/test_spectral_forward.py` gives 38 passed.

## Response to review (2026-10-04)

All three blocking issues are fixed in `docs/experiments/marys-room-broad-results.md`.
The new numbers come from `scripts/marys_room_broad_review_fixes.py`, which writes
`results/marys_room_broad_review_fixes.json`. That script builds no eye and
does not import `domains.photon_eye`.

Nothing frozen was changed: no stimulus, decoder, anchor, split, threshold,
quanta anchor, OD parameter, frozen script or result file. So no
`post_freeze_changes` entry was needed. Re-verification after the edits:
- Audit: 19/19 checks match.
- The 24 non-prereg A1 files match their freeze hashes.
- Prereg: the A1 prefix and the A2 lock both match.
- `marys_room_broad.json` sha is still `cac59dc4…`.
- HEAD is still `3649fb17`.
- `tests/test_spectral_forward.py`: 38 passed.

### Blocking

| # | Resolution |
|---|---|
| B1 P5 non-diagnostic | **Accepted, with corrections to the suggested fix.** P5 is now worded "holds as registered, but the registered criterion is non-diagnostic" (erratum E2). The white baseline is reported next to it: 30/30 achromatic stimuli have RG > 0, bare E at 100 td gives 0.045 and bare A gives 0.091. The prereg sentence "demonstrating the literal premise … is false" is explicitly superseded. The evidence now rests on measures that discriminate. Two of the review's suggested measures are weaker than stated: (i) The 100 td eye (L−M)/(L+M) of 0.69–0.88 is a rounding artefact. The expected value is 0.20–0.56, and replica whites at the matched at-retina td, which carry 1–3 quanta, reach 0.68. The comparison is now made at expected value against white of the same illuminant and at matched td. Under that comparison, 27/27 eyelid stimuli exceed their matched white, with a minimum ratio of 1.9×. Across illuminants the ranges touch: eyelid D65 OD 1.6 gives 0.190, against bare A at 10 td of 0.204. (ii) Of the eye-anchor "13/27 red/purple", 9 calls are at 100 td and rest on rounding. At expected value the count is 6/27 (OD_long 1.0 under E and A); the rest decode as yellow. The cleanly separating fact is colorimetric: the at-retina dominant wavelength is 638–645 nm at purity 0.22–0.63. The revised statement is that the light behind the lid is long-wavelength dominant and shifts L−M contrast toward red by ≥1.9× relative to matched white, while this eye's categorical read-out mostly calls it yellow. Item 11 is folded in here: the matched-640 nm ratio at 100 td is withdrawn as evidence. |
| B2 pseudo-replication | **Accepted (accounting erratum E1).** Every Arm A row now reports n_d, using Arm A's own theory-distinct key (normalised LMS plus truth), which reproduces `n_theory_distinct_scored = 125`. The distinct-level numbers are the ones to cite; the row-level values are kept only for traceability and marked superseded. Eye accuracies and angles now carry cluster-bootstrap CIs over intensity-condition clusters (130 hue-scored, 154 overall) and a cluster majority-vote binomial. No verdict changes. The review's collapsed figures (sign 0.682 at n = 148, anchor 0.601) could not be reproduced. Arm A's distinct key gives n = 125 and 0.648 / 0.648. A recipe-up-to-intensity collapse gives n = 130 and 0.638 / 0.654. Both are reported; the mono P1 figure, 27/30 with p = 1.9e-9, matches the review exactly. |
| B3 verdict-rule timing | **Accepted.** The "Deviations" bullet and the verdict-table header now say the P1–P5 rules and thresholds are stage-declared, are not part of the registration, go beyond the prereg's "without threshold pass/fail claims", and have timing that cannot be independently verified. The mtime evidence is stated. The current sha256 of `scripts/marys_room_broad.py` (`f06f87f5…`) is recorded in the review-fixes result for the record only. Arm C's own recorded script hash (`53f10377…`) still matches its file. The doc also requires future stages to hash analysis scripts into the freeze before eye contact. |

### Changed numbers (old → new)

| Quantity | Old | New |
|---|---|---|
| HO-core theory sign, accuracy [CI], p vs majority | 0.636 [0.577, 0.691], 3.8e-4 (n=272) | 0.648 [0.561, 0.726], 0.0044 (n_d=125, majority 0.528) |
| HO-core theory anchor accuracy [CI], p | 0.702 [0.645, 0.753], 6.7e-25 | 0.648 [0.561, 0.726], 2.2e-9 (majority 0.384) |
| TRAIN theory sign [CI] | 0.710 [0.611, 0.792] (n=93) | 0.710 [0.534, 0.839] (n_d=31), p vs majority 0.43 |
| Mono held-out theory anchor p (P1) | 6e-26 (90 rows) | 1.9e-9 (27/30) |
| Mono / reflectance theory sign p (P1) | rows | 0.59 (20/30) / 0.68 (36/54; already distinct) |
| HO-core eye anchor CI, p | Wilson [0.715, 0.815], 2.7e-36 | cluster-boot [0.700, 0.832]; cluster vote 92/130, p 4.0e-13 |
| HO-core eye sign CI, p | Wilson [0.496, 0.613], 0.25 | cluster-boot [0.461, 0.649]; cluster vote 75/130, p 0.18 |
| HO-core median angle CI | [2.88, 4.10] | cluster-boot [2.87, 4.13] |
| HO-core mean angle CI | [6.64, 9.94] | cluster-boot [6.02, 11.01] |
| Eyelid eye-anchor red/purple | 13/27 | 13/27 as submitted; 6/27 at expected value |
| P2 verdict wording | Supported | Supported on (a) and (b) under the stage rule; (c) is a consistency check |
| P3 verdict wording | Supported | Holds: a consistency check |
| P5 verdict wording | Supported (deterministic arm) | Holds as registered; the criterion is non-diagnostic |

### Non-blocking

| # | Resolution |
|---|---|
| 4 P6 depends on N | Done. The crossover is stated (N > 325.3, against N = 302), along with VQ k=64 fitted on 93 TRAIN points and k=16/32 missing the target. VQ against the fixed opponent code is 19.56 vs 12.42 bits, with crossover N > 661. Without model cost it is 6 vs 12. |
| 5 identity as evidence | Done (E3). P2(c), P3 and "accounted for" are relabelled as consistency checks, and the Interpretation section is reworded. |
| 6 shared observer / illuminant | Done. The caveat now sits under the RQ1 tables and in the Interpretation section, and the 0.278 for reflectance under A is attributed to the illuminant-discount mismatch. |
| 7 dominant wavelength > 660 nm | Documented (E4), with a post-hoc truncated-locus recomputation that leaves the frozen truth unchanged. The locus is truncated at its x-maximum, 703 nm, across 612 recipes. 9 mono stimuli above 660 nm shift by more than 0.5 nm; 0 `hue4` and 0 `binary` labels change. My count of shifted stimuli (9) is lower than the review's 11, which used a different construction. |
| 8 5 nm over-count | Documented as a convention (E4). At 100 td: E +1.0%, A +1.3%, D65 +0.7%, with trapezoid alternatives given. The frozen forward model is unchanged, and only `ablation_grid5` is affected. |
| 9 vacuous label-permutation check | Done (E5). It is now described as a signature guarantee. |
| 10 "hemoglobin-shaped", 2.1 OD, citation | Done in the results doc (E4). The spec and prereg are frozen, so they were not edited. The journal is stated as most likely *J. Biomed. Opt.* 16(6):067011. **This was not verified online**, because the network was restricted to datasets. It must be checked before the paper cites it. |
| 11 100 td single quanta | Folded into B1: the 100 td 640 nm ratio is withdrawn as evidence, and the quanta counts and z = 1.5 are stated. |
| 12 prereg "concedes" passage | Done. The Interpretation section now says this is an argument, not a finding, and must not be lifted into the paper. |
| 13 audit scope | Done. The Audit paragraph states that the audit does not check the colorimetry or the truth labels independently. |
| 14 equal 10°/2° accuracy | Done in the P4 row. 4/79 anchor labels and 2/79 sign labels differ, the effects offset, and correctness is 67/79 and 53/79 for both observers. The review's denominator of 85 includes the 6 achromatic rows; the 4 differing labels are the same. |

### Unresolved

- The Bierman et al. journal and PubMed ID still need checking against the source.
- The Kuehni unique-hue table entries have not been checked against the source.
- The timing of the Arm B verdict rules cannot be established after the fact. This is disclosed, not fixed.
- `scripts/marys_room_broad_theory --verify` still prints the expected prereg mismatch caused by A2. The script is frozen, so it was left unchanged.

# Mechanism-to-code audit: GraphEye colour transduction

Phase 1 of the Mary's Room empirical paper plan. This table documents, stage by
stage, where each computation in the photon → opponent-colour pipeline actually
lives, what biological mechanism it corresponds to, and whether it is realistic,
simplified, or absent. Every formula below was read directly from source (not
inferred); file/line anchors are given so the paper's Methods and the Arm D.1
"biological grounding" section can cite them.

## Scope and the one claim that matters most

The research (theory-only) arm computes opponent coordinates
`RG = L − M`, `BY = S − 0.5·(L + M)` on **raw CIE 2006 cone fundamentals**.
The eye computes the **same opponent formula** but on **post-saturation receptor
activations**, where each activation has already passed through (a) a Gaussian
spectral-capture stage whose sensitivity centres (L 564 nm, M 534 nm, S 420 nm)
differ from the CIE tabulated fundamentals, and (b) a Naka-Rushton saturating
nonlinearity with light adaptation.

Consequence for the paper: the ~99.9 direction match / 2.86°–4.19° angular
residual in the pilot is **not** a tautology from shared axes. The opponent
*formula* is shared, but the *inputs to that formula* are produced by an
independent forward model (Gaussian capture + saturation) that is not the CIE
fundamentals. The angular residual is precisely the footprint of (nonlinearity +
Gaussian-vs-CIE sensitivity mismatch). This is the real content of RQ2
("prediction of sensory state") and must be foregrounded, with dense sampling
near the RG zero-crossing where the nonlinearity bends hardest.

## Where the math lives (three files only)

| Concern | File | Anchor |
|---|---|---|
| Capture, saturation, adaptation (arithmetic) | `runners/dsl/src/cognitive_tasks.rs` | kernel `photon_transduce`, lines 372–406 |
| Opponent recombination + intensity + salience | `seeds/photon_retina.json` | rule `photon_column_synthesizes_retinal_percept`, line 289; `red_green` at 481, `blue_yellow` at 507 |
| Human-readable generator of that seed | `scripts/build_photon_retina_seed.py` | `RULES`, lines 30–90 |
| Payload assembly + live adaptation feedback | `domains/photon_eye.py` | `submit_photons`, lines 1688–1731 |
| Receptor/percept node construction + params | `domains/photon_eye.py` | lines 586–607; `_RECEPTORS` dict (l=564, m=534, s=420, rod=498) |
| Opponent-sign regression test | `tests/test_photon_grapheye_migrated.py` | lines 93–94 |

Python does **no** colour math. The opponent recombination exists only as a seed
rule (confirmed: `red_green`/`blue_yellow` appear in Python, scripts, and JSON
seeds, never in any `.rs`). The pipeline is deterministic given fixed photon
inputs — no RNG in the colour path.

## Stage-by-stage table

| # | Stage | Formula (verified in source) | Location | Biological referent | Status |
|---|---|---|---|---|---|
| 1 | Spectral capture | `caught = dark_current + Σ_packets count·exp(−0.5·z²)`, `z = (λ − center)/bandwidth` | `cognitive_tasks.rs:379–390` | Photoreceptor spectral sensitivity (quantal catch) | **Simplified.** Gaussian in λ, unnormalised (peak 1.0 at centre). Not the Govardovskii/Dartnall nomogram shape; symmetric where real curves are skewed. No lens/macular pre-filtering, no optical density self-screening. |
| 2 | Transduction / saturation | `activation = caught / (caught + half_saturation + adaptation)` | `cognitive_tasks.rs:400` | Phototransduction response compression (Naka-Rushton) | **Realistic in form.** Canonical Naka-Rushton; adaptation added to the half-saturation term is a legitimate Weber-like light-adaptation gain shift. `dark_current` entering via `caught` rather than as a separate leak is a simplification. Output bounded [0,1). |
| 3 | Light adaptation | `next_adaptation = adaptation + adapt_rate·(caught − adaptation)` (adapt_rate=0.12 default, clamped [0,1]); adaptation is graph-resident, fed back each epoch | `cognitive_tasks.rs:401`; feedback at `photon_eye.py:1719` | Retinal light adaptation (gain control) | **Simplified.** Single first-order leaky integrator; one time constant. No separate fast neural vs. slow pigment-bleaching stages, no rod/cone-specific kinetics. |
| 4 | Receptor write-back | copy `output[0]→activation`, `[1]→adaptation`, `[2]→caught_quanta`; copy old activation → `prev_activation`; gate `task.status==done ∧ retina_applied≠1`, then set `retina_applied=1` (fire once) | `seeds/photon_retina.json:129`; generator `build_photon_retina_seed.py:30–50` | n/a (bookkeeping) | Mechanical. |
| 5 | Opponent — red/green | `red_green = L.activation − M.activation` | `seeds/photon_retina.json:481`; generator `:76–77` | L–M (parvocellular / Hering red-green) opponent axis | **Simplified-canonical.** Textbook linear cone-opponent axis with unit weights. Real LGN weights are not exactly unit and vary by cell type. Computed on activations, so it inherits stages 1–3. |
| 6 | Opponent — blue/yellow | `blue_yellow = S.activation − 0.5·(L.activation + M.activation)` | `seeds/photon_retina.json:507`; generator `:78–81` | S–(L+M) (koniocellular / blue-yellow) opponent axis | **Simplified-canonical.** Same caveat; the 0.5 weighting is a clean choice, not fitted. |
| 7 | Intensity | `intensity = 0.4·(L.act + M.act) + 0.2·rod.act` | `seeds/photon_retina.json` (~300–340); generator `:72–75` | Luminance (L+M dominated, S excluded, rod scotopic contribution) | **Simplified but sensible.** S excluded from luminance matches biology; weights are not calibrated photometric luminous-efficiency values. |
| 8 | Salience | `salience = Σ_receptors |act − prev_act|` over {rod,L,M,S} | `seeds/photon_retina.json` (~554+); generator `:82–87` | Transient / change detection | **Heuristic.** Summed temporal-difference energy; not a specific retinal circuit. Not used by the colour-identity arm. |
| — | Normalisation of opponent outputs | **none** — `red_green`/`blue_yellow` written raw | — | — | No explicit normalisation. Because activations ∈ [0,1), both opponent signals lie in (−1, 1) implicitly. |

## Absent stages (must bound every human-relevance claim)

The following are entirely absent and are the main gaps between this model and a
human visual system. The paper's Limits section must enumerate them:

- **Pre-receptoral optics:** no lens transmittance, no macular pigment, no
  age-dependent lens yellowing. (Directly affects S-cone input and metamerism.)
- **Spectral forward model:** the pipeline takes discrete (wavelength, count)
  packets. There is no illuminant SPD × surface-reflectance integration, so
  **broadband/reflected colours and metamers cannot currently be represented**
  (this is a capability gap, not just a sampling gap — see paper-plan review
  problem #5). Phase 2 must add this.
- **Chromatic adaptation / colour constancy:** adaptation here is per-receptor
  gain only; there is no von-Kries-style channel balancing or white-point
  normalisation.
- **Post-receptoral / cortical colour:** no second-stage (cortical) opponent
  remapping, no categorical colour naming beyond the external
  `colour_identity_world` category minter, no hue cancellation.
- **Spatial/temporal receptive-field structure for colour:** opponent signals
  are per-column point values; no centre-surround chromatic organisation.
- **Rod intrusion into colour, photopic/scotopic regime switching:** rod feeds
  intensity/salience only, never the opponent channels.

## Determinism

Confirmed deterministic in the colour path: `photon_transduce` is pure
arithmetic (exp, divide, multiply-add) over the payload — no RNG, no clock
reads. The opponent rule is pure arithmetic over graph attrs. The only ordering
sensitivity is epoch-gating (`input_epoch` comparisons), which is deterministic.
Implication for the analysis plan: per-stimulus repeats (the pilot's 12 columns
per colour) are **identical by construction** and contribute zero variance.
Error intervals must come from variation across the stimulus / illuminant /
observer-perturbation manifold, not from repeats.

Caveat on verification: the kernel source read is
`runners/dsl/src/cognitive_tasks.rs`; the artifact actually loaded is the
compiled `substrate_rs` `.abi3.so`. Source and binary are expected to agree but
were not byte-verified by disassembly. The seed JSON (`photon_retina.json`) is
the shipped manifest and was confirmed to encode the same AST as the generator.

## Implications for the forward model (Phase 2 input)

To make Arm A↔B agreement *earned* rather than definitional, the Phase 2
spectral forward model must reproduce stages 1–6 independently from an SPD:
SPD → (optional pre-receptoral filter) → Gaussian capture per cone →
Naka-Rushton saturation → `L−M`, `S−0.5(L+M)`. The theory decoder can then be
run on CIE fundamentals and shown to generalise to this forward model's outputs,
with the angular residual attributed to the two documented sources
(nonlinearity, Gaussian-vs-CIE sensitivity mismatch) rather than left unexplained.

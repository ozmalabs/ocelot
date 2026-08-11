# Cross-field signal-processing survey — synthesis

Four parallel surveys (super-resolution spectral; time-frequency/tracking; source-separation/array; inverse-
problems/phase-retrieval/limits) assessed for the formant front-end limiter (cross-speaker FSDD via formant-
trajectory + order-N dynamics stuck 58.9% vs 83.5% exemplar) and the general solve-for-N structure extractor.
Discipline: owned DSP (no net/.fit/gradient-training); trained nets flagged sense-only.

## 1. The immediate front-end fix — TWO defects, continuity dominates
Survey 2's reframe: (A) noisy per-frame candidates, (B) NO CONTINUITY constraint (independent frames jump/swap).
B dominates — order-N dynamics AMPLIFY per-frame discontinuity (differencing a jumpy track manufactures noise).
- **TOP PICK — Viterbi / dynamic-programming formant tracking**: per-frame root candidates + a transition cost
  penalising jumps, global min-cost path assigning one pole per formant. The Snack/Praat/Talkin lineage. DONKEY-
  CLEAN and the cleanest fit — it's DTW/Viterbi over a trellis, which the agent ALREADY owns as native graph
  primitives (DtwTo/MinOver/Argmin). The dominant defect, the most-owned method.
- **Better candidates to feed it**: harden LPC first (order 12-14 + ridge + bandwidth/Q root pruning — cheap,
  attacks the named failure); then QCP-FB weighted linear prediction (best owned per-frame estimator) and/or
  ESPRIT/matrix-pencil or CLEAN-on-frequency for the merged F2/F3.
- **Frication**: separate it, don't sharpen it — HPSS (median-filter spectrogram: time->harmonic/formants,
  frequency->percussive/frication). The frication cluster (six/seven/eight) is FUNDAMENTALLY non-line-spectral
  (broadband noise); NO super-resolution method rescues it (they assume a resonant line model frication violates).

## 2. Structure-extractor engine upgrades (adopt into solve-for-N)
- **The weighted-admissibility IS POCS / a robust MAP log-posterior** (survey 4). The agent already built the
  right object (soft excluders intersected = product of robust likelihood factors = sum of log-admissibilities =
  POCS intersection). Adopt POCS convergence theory + Fienup HIO's anti-stagnation feedback. The cosmic
  non-negativity anchor (arXiv 2503.20434) is a POCS positivity projection — adopt the PATTERN: find the one
  physically-guaranteed constraint and make it a hard projection.
- **CLEAN == matching pursuit** (survey 3): the agent's own sinusoid super-resolver IS CLEAN, the radio workhorse,
  named from the radio side. Upgrade to NOMP/RELAX (Newton-refined off-grid) to kill grid-mismatch/over-subtraction.
- **Local-minima escape (Kepler)**: GNC (graduated non-convexity — deterministic homotopy from a smoothed convex
  misfit to the true one; beats RANSAC/multi-start) + spectral initialization (Wirtinger-flow lesson: data-driven
  eigenvector init beats random starts) + LM refiner wrapped in basin-hopping.
- **THE LIMIT TOOLS (most important for discipline)**: Cramer-Rao Lower Bound + Fisher-matrix conditioning, both
  nearly free given the LM Jacobian. PROTOCOL at every KILL: Fisher singular -> non-identifiable -> REPARAMETERIZE
  (fundamental-but-fixable; Kepler near-circular = omega/M0 degenerate at e->0, use equinoctial elements);
  well-conditioned but far above CRLB -> search failure -> GNC; well-conditioned and at CRLB -> genuine
  noise-limited KILL, STOP. This makes the ladder's "fundamental vs fixable" rigorous.

## 3. Honest corrections (where the framing over-reaches)
- **"Ear as a radio telescope" needs a MIC ARRAY.** Van Cittert-Zernike / aperture synthesis / MVDR / spatial
  MUSIC all require spatially-separated sensors; a single mic has NO baseline, NO aperture — confirmed zero
  auditory literature for VCZ. The array toolkit is a FUTURE-array program, useless single-channel now. BUT the
  frequency-axis versions (CLEAN/MUSIC/ESPRIT on the frequency axis, not space) DO transfer and ARE usable now —
  the same algorithms — so building them now transfers directly to the array later.
- **Traps**: zoom-FFT/CZT (refines the grid not the resolution — cannot split merged formants); atomic-norm SDP
  (right theory, wrong signal model, too expensive); Wigner-Ville (cross-terms wreck multicomponent speech); EMD
  (mode-mixing, fragile); NMF/K-SVD (a .fit = sense-only); PhaseLift (O(n^2), toy-scale only).

## 4. The meta-finding
The structure extractor IS the established inverse-problem machine: weighted-admissibility = POCS/robust-MAP,
sinusoid super-resolution = CLEAN/matching-pursuit, the refine step = LM, the escape = GNC, the stop-sign =
CRLB/Fisher. The agent built the right objects; the literature supplies the convergence theory, the best escape
move, and the rigorous stop-sign. This is "the perspective unifies and inherits the toolbox" made concrete.

## Recommended next build
**Viterbi-DP formant tracker (continuity) over hardened-LPC/QCP-FB candidates + HPSS frication split** — donkey-
clean, native-graph, aimed at the dominant defect order-N was amplifying. **And adopt CRLB + Fisher conditioning**
as the KILL-vs-fundamental test, run at every future KILL.

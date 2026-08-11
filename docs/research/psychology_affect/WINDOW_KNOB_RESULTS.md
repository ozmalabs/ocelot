# WINDOW-AS-A-KNOB — RESULTS (block 241000)

Pre-registration: `WINDOW_KNOB_PREREG.md` (committed BEFORE any measurement).
Full-power numbers: `results/window_knob.json` (N = 60). Gate:
`tests/test_window_knob_migrated.py` (9/9 green at N = 20). Every number below was
produced AFTER the prereg commit, on this worktree's OWN engine
(`source_match == own`), riding the REAL `AffectiveState.arousal` +
239000's `WindowOfTolerance`. **NO Rust, NO new Term.**

## Headline
The window of tolerance is now a **FORMAL, settable, inspectable window-WIDTH
knob**: the stressor MAGNITUDE at which the infant dysregulates is a strictly
monotone, CI-separated function of window WIDTH — a measured dose-response the
clinical models (Siegel; Porges) never had — and the SAME knob, placed on the
caregiver, governs two-agent co-regulation capacity in a BIDIRECTIONAL dyad. One
parameter, both scales.

## Base / discipline
- Base SHA: `ecdcd8dbad143c12586ed3b0d886f76cfcb35d53` (origin/main).
- Seed block 241000–241999: `seed_claim.py` → CLEAN (no collision detected; two
  load-bearing caveats reproduced in the prereg).
- Engine: `source_match == own` (this worktree built its own byte-identical
  engine); canonical `.so` md5 `e75bc65021b6be0740abeee63662e21b` UNCHANGED;
  `runners/dsl` working-tree diff EMPTY (no Rust).
- Seed `window_knob_coreg` v1.0.0: `self_load_only` (default-OFF),
  `depends_on: [affective_state_core]`, 11 named rules. Source audit clean (no
  Python rule-engine call; no reward/punishment token).

## G-knob (HEADLINE) — the formal settable window — PASS
Onset threshold measured by bisecting the stressor magnitude over fresh infants
(the GRAPH decides onset; `in_episode` latches at `wk_infant_dysreg_onset_*`);
caregiver absent (SINGLE-agent tolerance). N = 60 per width, half-width ~ N(μ, 2).

| window half-width (knob) | onset threshold (mean) | 95% CI | predicted |
|---|---|---|---|
| 15 | **15.69** | [15.14, 16.24] | [14, 16] ✓ |
| 30 | **30.06** | [29.57, 30.54] | [29, 31] ✓ |
| 45 | **45.24** | [44.69, 45.79] | [44, 46] ✓ |

Strictly monotone increasing, all three CI-separated (`monotone_ci_separated =
True`). The onset threshold tracks the width itself (threshold ≈ hi = half-width)
— **the window rendered as a measurable number.**

**Failable control — the placebo axis (PASS).** Sweeping the self-reg gain
`k_self` at FIXED width leaves the onset threshold FLAT (overlapping CIs), proving
the knob is the WIDTH, not just any parameter:

| k_self (placebo) | onset threshold | 95% CI |
|---|---|---|
| 0.05 | 29.73 | [29.19, 30.26] |
| 0.15 | 30.02 | [29.51, 30.53] |
| 0.30 | 30.19 | [29.69, 30.69] |

`placebo_flat = True`. A monotone placebo would have meant the width result was an
artefact; it is flat, so the dose-response is the width's.

## G-bidirectional — mutual entrainment + the single↔two-agent unification — PASS
The infant's arousal PULLS the caregiver's (`wk_caregiver_pull_by_infant`, the
same `sd_blend` leaky-EMA pull, now mutual); the caregiver has its OWN dynamic
arousal + window + `regulated` flag that flips when its arousal leaves its own
band (`wk_caregiver_dysreg_onset`). N = 60 per arm; infant half-width ~ N(30, 3),
stress ~ N(100, 8).

| caregiver window half-width | return_ticks (mean, CI) | caregiver_dysreg_frac | caregiver_peak_arousal |
|---|---|---|---|
| **narrow = 10** | **6.83** [6.65, 7.01] | **1.00** | 49.0 |
| mid = 30 | 1.33 [1.21, 1.45] | 0.00 | 18.1 |
| **wide = 90** | **1.40** [1.27, 1.53] | **0.00** | 18.0 |

- **Mutual entrainment (both arms):** the caregiver's peak arousal is > 8 in BOTH
  the wide (18.0) and narrow (49.0) arms — the infant's distress measurably moves
  the caregiver. `mutual_entrainment_both_arms = True`. (239000 held the caregiver
  fixed; this is the residual closed.)
- **A NARROW-window caregiver is pulled into CO-DYSREGULATION** (dysreg fraction
  1.00) and FAILS to co-regulate — the infant is reduced to self-regulation and
  returns CI-slower (6.83) than with a wide caregiver (1.40).
  `narrow_slower_than_wide_ci_separated = True`, `narrow_pulled_in = True`.
- **Failable control — a WIDE (well-regulated) caregiver is NOT pulled in**
  (dysreg fraction 0.00, CI-separated below the narrow arm) and co-regulates fast.
  `wide_not_pulled_in = True`, `codysreg_frac_separated = True`. If a wide
  caregiver dysregulated as often as a narrow one, or the narrow one co-regulated
  as fast as the wide one, the link would be false — neither holds.
- **The unification (the delta):** the SAME `half_width` knob sets the
  single-agent onset threshold (G-knob) AND the two-agent co-regulation capacity
  (G-bidirectional). One parameter, both scales, on ONE substrate.

## G-glass-box — PASS
One narrow-caregiver episode reconstructs entirely from `graph_to_dict`: both
arousals, both window bands `[lo,hi]` (infant WIDTH 60, caregiver WIDTH 20), the
caregiver's `regulated`/`dysregulated` flags, and the single `attended_by`
coupling edge. Every regulation/coupling decision is a named rule; the co-dysreg
("who is regulating whom, and who got pulled in") is READ off graph state, not
inferred from a cross-correlation of physiological time series.

## Honest scope — synthetic mechanism, NOT a clinical number
This is a **synthetic** model of the window-of-tolerance / co-regulation
frameworks (grounded in the creator's in-vivo experience with 21 foster children).
Mechanism-proven ≠ clinically valid — reported separately, per the standing rule.

**Prior art, conceded up front (per `PRIOR_ART_SOCIAL_EXPERIMENTS.md` §RUNG 5).**
Co-regulation-the-mechanism — dyadic arousal coupling — is NOT ours: coupled-
oscillator dyads (Butner, Diamond & Hicks 2007; Reed et al. 2013), the arousal-
caregiver robot (Hiolle & Cañamero), and the active-inference parent-infant model
(Tsubamoto & Horii 2026) all model inter-agent arousal coupling mechanistically.
We do not claim to be first to couple two agents' arousal.

**The delta claimed, and only this:** (1) the window of tolerance rendered as a
FORMAL, settable, inspectable window-WIDTH knob with a measured onset-vs-width
dose-response — the clinical construct has NO formal computational model; (2) the
single-agent tolerance and the two-agent co-regulation capacity UNIFIED behind
that ONE knob on ONE substrate. Bins/settable-priors as an IV that neither the
clinical (verbal) nor the classical coupled-oscillator camps run behind a
watch-it-narrow/widen inspectable window.

**Honest residuals (recorded, not patched):**
- Arousal is still a SCALAR (not the multi-branch polyvagal autonomic state).
- The window is a SYMMETRIC band about a fixed setpoint (0); no asymmetric
  hyper/hypo widths.
- The mutual update is sequential (Gauss-Seidel within the `run_rules` fixpoint),
  not simultaneous — documented, and the leaky contraction is robust to it.
- The narrow-caregiver failure is a REDUCTION-to-self-regulation (return 6.83,
  NOT censored) — co-regulation capacity lost, not a permanent lock. This is
  within the pre-registered [6, 40] interval and reported straight; a fixed
  external high anchor (239000's dysregulated-caregiver control) is what produced
  censoring there, and a purely bidirectional dyad has no such anchor, so the
  self-regulation floor always eventually returns the infant.
- The caregiver-width → capacity transition is a THRESHOLD (step) at the
  caregiver's peak arousal (~18), not a smooth slope: mid (30) behaves like wide
  (90) because the peak stays inside both; only the narrow (10) window is
  breached. The two-agent "dose-response" is a capacity BOUNDARY, not a graded
  curve — the graded dose-response lives on the single-agent onset axis (G-knob).
- Still no long-term developmental trajectory (that was 239000's plasticity gate;
  this rung is about the knob and the bidirectional coupling).

## Files (all additive, `window_knob_` / `WINDOW_KNOB`-prefixed)
- `WINDOW_KNOB_PREREG.md`, `WINDOW_KNOB_RESULTS.md`
- `seeds/window_knob_coreg.json` (11 rules; self_load_only; depends_on
  affective_state_core)
- `scripts/window_knob_seed_build.py` (authoring tool — emits the seed)
- `worlds/window_knob_dyad_world.py` (world adapter)
- `scripts/window_knob_run.py` (runner)
- `tests/test_window_knob_migrated.py` (gate, 9/9)
- `results/window_knob.json` (full-power N=60 measurements)

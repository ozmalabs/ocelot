# WINDOW-AS-A-KNOB — PRE-REGISTRATION (block 241000)

**This document is committed BEFORE any measurement.** It states the design, the
frozen constants, the predicted intervals, and the failable controls. No number
below is a measurement — every interval is a PREDICTION. This rung DEEPENS block
239000 (arousal / window-of-tolerance with co-regulation, on main) into its
genuine prior-art delta.

## Base
- Base SHA: `ecdcd8dbad143c12586ed3b0d886f76cfcb35d53` (origin/main — it carries
  239000's `WindowOfTolerance` node + `worlds/coreg_dyad_world.py`).
- Seed block: **241000–241999**. `python scripts/seed_claim.py 241000 241999` →
  `CLEAN — no collision DETECTED` (961 files with seed sinks; 672 unresolved
  sink sites tree-wide, counted not discarded; two load-bearing caveats
  reproduced verbatim in the results).
- A sibling agent builds block 240000 (`marshmallow_` files) in a separate
  worktree; this rung touches none of its files.

## What 239000 left open (the residuals this rung attacks)
Block 239000 built the arousal / window / co-regulation dyad and named two
residuals: (1) the caregiver's regulation was held FIXED — a real dyad is
BIDIRECTIONAL (the infant's distress also dysregulates the caregiver); (2) the
window was a passive band, not a settable, dose-measurable parameter. This rung
makes the window WIDTH a first-class **settable, inspectable KNOB** with a
measured dose-response, and makes the dyad BIDIRECTIONAL — reusing 239000's
`WindowOfTolerance` node, the REAL `AffectiveState.arousal`, and the same
`sd_blend` leaky-EMA pull form (`x <- x + k·(target − x)`).

## The prior-art delta being claimed (honest, per PRIOR_ART_SOCIAL_EXPERIMENTS.md §RUNG 5)
- **CONCEDED as prior art (NOT claimed):** co-regulation-the-mechanism — dyadic
  arousal coupling — is already modelled (coupled-oscillator dyads: Butner,
  Diamond & Hicks 2007; Reed et al. 2013; the arousal-caregiver robot of Hiolle &
  Cañamero; the active-inference parent-infant model of Tsubamoto & Horii 2026).
  We do not claim to be first to couple two agents' arousal.
- **The ONLY delta claimed here:** (a) the window of tolerance rendered as a
  FORMAL, settable, inspectable window-WIDTH knob with a measured onset-vs-width
  dose-response — the clinical construct (Siegel; Porges) has NO formal
  computational model; (b) the SINGLE-agent tolerance and the TWO-agent
  co-regulation capacity UNIFIED behind that ONE width knob on ONE substrate.

## Architecture
Agents are GRAPHS in Rust; Python is a mechanical world adapter. Every regulation
/ coupling / dysregulation-onset decision is a graph RULE in
`seeds/window_knob_coreg.json` (self_load_only, default-OFF), riding the REAL
`AffectiveState.arousal` (`seeds/affective_state_core.json`) and 239000's
`WindowOfTolerance` node. Window WIDTH is a settable node attr — the knob;
setting it factorially is mechanical world setup in
`worlds/window_knob_dyad_world.py`. **NO Rust, NO new Term** (all rules use Terms
already present in 239000: Plus / Times / Minus / Attr / Var / Lit / Eq / Gt / Lt
/ And / Not). **NO reward / punishment** anywhere — dysregulation is a STATE, not
a badness (Greene: "kids do well if they can").

### Why a new seed rather than `depends_on` 239000's rules
239000's `coreg_pull` and `selfreg_pull` are UNCONDITIONAL (fire regardless of
the caregiver's own regulation) and its caregiver arousal is FIXED. A
BIDIRECTIONAL dyad requires the caregiver's arousal to be DYNAMIC, its `regulated`
flag to flip when its OWN arousal leaves its OWN window, and the co-regulation
pull to be GATED on that flag — none of which can be obtained by loading 239000's
unconditional rules on top. So `window_knob_coreg` re-expresses the pulls (reusing
the identical `sd_blend` leaky-EMA Term form and 239000's `WindowOfTolerance`
node + onset semantics) with the bidirectional + gated extension, and
`depends_on: [affective_state_core]` only (loading 239000's rule set would
double-apply the pulls). This is the honest "extend" — the extension REQUIRES new
rule bodies because the caregiver is now a dynamic, windowed agent.

### Graph-resident state (all readable via graph_to_dict)
- Infant `AffectiveState`: `arousal` (REAL), `k_self`, `k_co`, `setpoint`,
  `dysregulated`, `dysreg_kind`, `in_episode`, per-rule epoch guards
  (`tick_epoch`, `sr_epoch`, `cr_epoch`).
- Infant `WindowOfTolerance`: `lo`, `hi`, `half_width`, `min_half_width`
  (the WIDTH knob: width = `hi − lo` = 2·`half_width`).
- Caregiver `AffectiveState`: `arousal` (REAL, now DYNAMIC), `regulated`,
  `dysregulated`, `k_cg` (pull-by-infant gain), `k_cg_self` (self-reg gain),
  `setpoint`, epoch guards (`tick_epoch`, `cp_epoch`, `cs_epoch`).
- Caregiver `WindowOfTolerance`: its OWN `lo`, `hi`, `half_width` (the SAME knob,
  now governing co-regulation capacity).
- `Stressor`: `magnitude`, `armed`.

### The eleven rules (all named, all in seeds/window_knob_coreg.json)
INFANT: `wk_arousal_stressor_push`, `wk_infant_dysreg_onset_hyper`,
`wk_infant_dysreg_onset_hypo`, `wk_infant_coreg_pull` (GATED on caregiver
`regulated==1`), `wk_infant_selfreg_pull`, `wk_infant_return_to_window`,
`wk_infant_episode_close`.
CAREGIVER: `wk_caregiver_pull_by_infant` (BIDIRECTIONAL — the mutual entrainment),
`wk_caregiver_selfreg_pull` (GATED on `regulated==1`), `wk_caregiver_dysreg_onset`
(fires when the caregiver's arousal leaves its OWN `[lo,hi]` → `regulated=0` —
CO-DYSREGULATION), `wk_caregiver_reregulate`.

## Frozen constants (pre-registered)
- Setpoint = 0.0 (both agents); infant `k_self` = 0.15; infant `k_co` = 0.50.
- Caregiver `k_cg` (pull toward infant) = 0.25; caregiver `k_cg_self` = 0.30.
- Rule order (load-bearing): push(2) → dysreg onsets + caregiver reregulate(3) →
  caregiver_pull_by_infant(4) → caregiver_dysreg_onset(5) → caregiver_selfreg(6),
  infant_coreg(6), infant_selfreg(7) → infant_return + episode_close(8). The
  caregiver's pull-then-onset ordering means a caregiver whose window is too
  NARROW dysregulates on the FIRST tick, BEFORE the infant's co-regulation pull
  can read `regulated==1` — so co-regulation never engages (the failure mode).
- **G-knob widths** (infant half-width levels, the IV): `{15, 30, 45}`, each
  jittered ~ N(μ, 2). Window WIDTH = 2·half-width = `{30, 60, 90}`.
- **G-knob placebo axis** (failable control): infant `k_self` ∈ `{0.05, 0.15,
  0.30}` at FIXED half-width = 30 — a knob that must NOT move the onset threshold.
- **G-bidirectional caregiver widths** (half-width levels): NARROW = 10, MID = 30,
  WIDE = 90; infant stress ~ N(100, 8), infant half-width ~ N(30, 3).
- Onset-threshold search: bisection over stressor magnitude in [0, 200],
  12 iterations, tolerance 0.05.
- N = 60 per arm; return cap = 40 ticks (an episode that never returns is censored
  at 40). SEED_BASE = 241000.

## Metrics
- **onset_threshold** = the stressor MAGNITUDE (found by bisection, the GRAPH
  deciding onset) at which a fresh infant first dysregulates. Rides
  `wk_infant_dysreg_onset_*`; equals the infant's `hi` mechanistically.
- **return_ticks** = ticks from the stress tick to the RETURN TO THE WINDOW
  (`dysregulated` back to 0); censored → cap = 40.
- **caregiver_dysreg_frac** = fraction of episodes in which the caregiver's
  arousal left its OWN window (`regulated` flipped to 0) = co-dysregulation rate.
- **caregiver_peak_arousal** = max caregiver arousal over the episode (the mutual
  entrainment signal — the infant's distress moving the caregiver).
- 95% CIs (t≈1.96); "CI-separated" = one arm's CI lower bound strictly above the
  other's CI upper bound.

## Gates and PREDICTED intervals (predictions, NOT measurements)

### G-knob (HEADLINE — the formal settable window)
The stressor MAGNITUDE at which the infant dysregulates is a MONOTONIC function
of window WIDTH — a dose-response across ≥3 widths, CI-separated.
- **Predicted onset_threshold — half-width 15:** interval **[14.0, 16.0]**.
- **Predicted onset_threshold — half-width 30:** interval **[29.0, 31.0]**.
- **Predicted onset_threshold — half-width 45:** interval **[44.0, 46.0]**.
- **Predicted separation:** threshold(15) CI-upper < threshold(30) CI-lower <
  threshold(45) — strictly monotone increasing, all three CI-separated.
- **FAILABLE CONTROL (placebo axis — the "is the knob fake?" test):** sweeping
  infant `k_self` at FIXED width leaves the onset threshold FLAT — predicted
  onset_threshold **[29.0, 31.0]** at every `k_self` level, CIs OVERLAPPING (NOT
  separated). If the width sweep is flat/non-monotone, OR the placebo axis is
  itself monotone, the knob is fake and the gate FAILS — reported straight.

### G-bidirectional (mutual entrainment + the single↔two-agent unification)
(1) A dysregulated infant PULLS the caregiver's arousal (mutual); (2) the
caregiver's OWN window WIDTH predicts co-regulation capacity.
- **Mutual entrainment:** predicted caregiver_peak_arousal **> 8** in BOTH the
  wide and narrow arms (the infant's distress measurably moves the caregiver —
  the coupling is bidirectional, not one-way).
- **WIDE-window caregiver (half-width 90):** stays regulated and co-regulates —
  predicted return_ticks **[1, 4]**, caregiver_dysreg_frac **[0.0, 0.10]**.
- **MID-window caregiver (half-width 30):** predicted return_ticks **[1, 5]**,
  caregiver_dysreg_frac **[0.0, 0.20]** (peak ≈ 20 < 30 → stays regulated).
- **NARROW-window caregiver (half-width 10):** gets pulled into CO-DYSREGULATION
  and FAILS — predicted caregiver_dysreg_frac **[0.90, 1.0]**, and return_ticks
  **[6, 40]**, CI-SEPARATED ABOVE the wide arm (co-regulation capacity lost;
  reduced to self-regulation, no better than being alone).
- **FAILABLE CONTROL:** a wide-window (well-regulated) caregiver is NOT pulled in
  (caregiver_dysreg_frac CI-below the narrow arm). If a wide caregiver
  dysregulates as often as a narrow one, OR the narrow caregiver co-regulates as
  fast as the wide one, the width→capacity link is FALSE and the gate FAILS.
- **The unification (the delta):** the SAME `half_width` knob sets the
  single-agent onset threshold (G-knob) AND the two-agent co-regulation capacity
  (G-bidirectional) — one parameter, both scales, on one substrate.

### G-glass-box
Both arousals, both window bands `[lo,hi]`, the dysregulation-onset flags, and the
bidirectional coupling edges (`attended_by`, `has_window`) all reconstruct from
`graph_to_dict`; every regulation/coupling decision is a named rule; source-audit
clean (no Python decision, no reward/punishment token).

### G-discipline
Rides the REAL `AffectiveState.arousal` + 239000's `WindowOfTolerance`; the
bidirectional pulls reuse the identical `sd_blend` leaky-EMA Term form; default-OFF
(self_load_only); NO Rust (`runners/dsl` diff EMPTY, canonical `.so` md5
UNCHANGED); own engine (`source_match == own`); oracle BEFORE == AFTER; per-area
zero new reds.

## Honest scope
This is a **synthetic** model of the window-of-tolerance / co-regulation
frameworks (grounded in the creator's in-vivo experience with 21 foster children),
NOT a clinical-outcome number. Mechanism-proven ≠ clinically valid; the two are
reported separately. Known residuals to be recorded in the results: arousal is
still a SCALAR (not the multi-branch polyvagal autonomic state); the window is a
SYMMETRIC band about a fixed setpoint; the mutual update is sequential
(Gauss-Seidel within the run_rules fixpoint), not simultaneous; the caregiver
width→capacity transition is a THRESHOLD (step) at the caregiver's peak-arousal,
not a smooth curve, so the two-agent "dose-response" is a capacity boundary rather
than a graded slope; no long-term developmental trajectory. A null gate IS a
result and will be reported straight.

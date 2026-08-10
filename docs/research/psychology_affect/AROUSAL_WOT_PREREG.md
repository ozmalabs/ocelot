# AROUSAL / WINDOW-OF-TOLERANCE with CO-REGULATION — PRE-REGISTRATION (block 239000)

**This document is committed BEFORE any measurement.** It states the design, the
frozen constants, the predicted intervals, and the failable controls. No number
below is a measurement — every interval is a PREDICTION. The first rung of the
developmental-emotion line.

## Base
- Base SHA: `9c5172d697d031ac613a36e5bc98b7edfb373723` (origin/main).
- Seed block: **239000–239999**. `python scripts/seed_claim.py 239000 239999` →
  `CLEAN — no collision DETECTED` (959 files with seed sinks; 667 unresolved
  sink sites, counted not discarded; caveats reproduced verbatim in the results).

## The clinical models being instantiated (synthetically)
- **Arousal** = the substrate's REAL `AffectiveState.arousal`
  (`seeds/affective_state_core.json`), the same attribute the Harlow rung (block
  233000) read. Not a new quantity.
- **Window of tolerance** (Siegel; Porges polyvagal; van der Kolk) = a tolerated
  band `[lo, hi]` of arousal centred on the homeostatic setpoint. WITHIN →
  regulated. ABOVE `hi` → hyperarousal (fight/flight). BELOW `lo` → hypoarousal
  (freeze/shutdown). Both are dysregulated STATES.
- **Co-regulation** = an EXTERNAL regulated caregiver whose arousal entrains the
  infant's back into its window (the infant borrows the caregiver's regulation —
  the altricial / Harlow bond made mechanistic). Modelled as a leaky coupling
  (`sd_blend`'s Kalman/EMA pull, `x <- x + k·(target − x)`, constant gain).
- **Development / healing** = repeated successful co-regulation WIDENS the window
  and raises the safety prior (internalised regulation). **Trauma** = repeated
  stress WITHOUT co-regulation NARROWS the window and lowers the safety prior.
- **DESIGN INVARIANT — "kids do well if they can" (Greene):** dysregulation is a
  STATE to be regulated, never a badness. **No reward / punishment anywhere.**

## Architecture
Agents are GRAPHS in Rust; Python is a mechanical world adapter. Every regulation
decision (push, dysreg onset, return, co-regulate, self-regulate, widen, narrow)
is a graph RULE in `seeds/arousal_window_coreg.json` (self_load_only, default-OFF,
`depends_on: [affective_state_core]`), riding the REAL `AffectiveState.arousal`.
The adapter (`worlds/coreg_dyad_world.py`) only delivers world facts (stress tick;
caregiver present/absent; caregiver regulated/dysregulated) and reads graph state.
**NO Rust, NO new Term.**

### Graph-resident state (all readable)
- Infant `AffectiveState`: `arousal` (real), `k_self`, `k_co`, `setpoint`,
  `dysregulated`, `dysreg_kind` (+1 hyper / −1 hypo), `in_episode`, `got_coreg`,
  per-rule epoch guards (`tick_epoch`, `sr_epoch`, `cr_epoch`).
- Infant `WindowOfTolerance`: `lo`, `hi`, `half_width`, `widen_delta`,
  `narrow_delta`, `min_half_width`, `safety_prior`, `safety_step`,
  `widen_count`, `narrow_count`.
- Caregiver `AffectiveState`: its own `arousal`, `regulated`.
- `Stressor`: `magnitude`, `armed`.

### The nine rules
`arousal_stressor_push`, `dysreg_onset_hyper`, `dysreg_onset_hypo`, `coreg_pull`,
`selfreg_pull`, `mark_coreg_support`, `dysreg_return_to_window`,
`episode_resolve_widen`, `episode_resolve_narrow`.

## Frozen constants (pre-registered)
- Setpoint = 0.0; `k_self` = 0.15; `k_co` = 0.50.
- Regulated caregiver arousal = 0.0; dysregulated caregiver arousal = 120.0.
- Initial window half-width `half_width0` ~ U(20, 40); stressor magnitude ~ U(80, 140).
- `widen_delta` = 2.0; `narrow_delta` = 2.0; `min_half_width` = 5.0 (floor).
- `safety_prior0` = 0.5; `safety_step` = 0.03 (cap 1.0, floor 0.0).
- Return cap = 40 ticks (an episode that never returns is censored at 40).
- N = 60 infants per arm; N_episodes = 15 for the plasticity gates. SEED_BASE = 239000.

## Metric
- **return_ticks** = ticks from the stress tick to the RETURN TO THE WINDOW
  (`dysregulated` back to 0). Censored episodes report return_ticks = cap = 40.
- **half_width** before vs after N_episodes; **safety_prior** before vs after.
- 95% CIs (t≈1.96); "CI-separated" = one arm's CI lower bound strictly above the
  other's CI upper bound.

## Gates and PREDICTED intervals (predictions, NOT measurements)

### G-co-regulation (HEADLINE)
A dysregulated infant returns to its window FASTER with a REGULATED caregiver
present than ALONE, CI-separated.
- **Predicted return_ticks — co-regulation (regulated present):** mean ≈ 1–2,
  interval **[1, 3]**.
- **Predicted return_ticks — ALONE (caregiver absent, failable control):** mean
  ≈ 7–8, interval **[6, 10]**.
- **Predicted return_ticks — DYSREGULATED caregiver present (failable control):**
  CENSORED (the high-arousal caregiver pulls the infant the WRONG way; arousal
  converges ≈ 104, never returns), interval **[35, 40]**, ~100% censored.
- **Predicted separation:** co-reg CI-upper < alone CI-lower (faster);
  alone < dysregulated-caregiver (a dysregulated caregiver is no better, and
  worse, than being alone). If co-regulation does NOT speed the return, the gate
  FAILS — reported straight.

### G-window-widens (development / healing)
Repeated co-regulation WIDENS the window.
- **Predicted half_width after 15 co-reg episodes:** ≈ half_width0 + 30, interval
  **[55, 65]**; **initial** half_width interval **[20, 40]** → grows, CI-separated
  above initial.
- **Failable control (repeated stress, caregiver ABSENT):** does NOT widen — it
  NARROWS to the floor, predicted final half_width **[5, 5]**, CI-separated BELOW
  initial and below the co-reg arm.

### G-trauma-narrows (pathology direction)
Repeated stress without co-regulation NARROWS the window and lowers the safety
prior → the traumatised profile (small window, easily dysregulated).
- **Predicted half_width after 15 unsupported episodes:** floor **[5, 5]**;
  **safety_prior:** ≈ 0.5 − 15·0.03 = 0.05, interval **[0.02, 0.10]**.
- **CI-separated below the co-reg arm** (half_width ≈ 60, safety_prior ≈ 0.95).
- Ties to the safety axis of the three foundational priors (`safety_prior`).

### G-glass-box
`arousal`, the window band `[lo,hi]`, the caregiver's arousal, and the coupling
are all readable graph state; every regulation decision is a named rule;
source-audit clean (no Python decision, no reward/punishment token).

### G-discipline
Agents = graphs on the real emotion framework; world = mechanical adapter;
default-OFF (self_load_only); NO Rust (`runners/dsl` diff EMPTY, canonical `.so`
md5 UNCHANGED); own engine `own`, `source_match == own`; oracle BEFORE == AFTER;
per-area zero new reds.

## Honest scope
This is a **synthetic** model of the co-regulation / window-of-tolerance
frameworks (grounded in the creator's in-vivo experience with 21 foster
children), NOT a clinical-outcome number. Mechanism-proven ≠ clinically valid;
the two are reported separately. Known residuals to be recorded in the results
(arousal dynamics fidelity; window as a scalar band vs a richer polyvagal state;
no long-term developmental trajectory; the caregiver's regulation held fixed;
arousal driven directly rather than through the full drive→modulator→PSI
projection). A null gate IS a result and will be reported straight.

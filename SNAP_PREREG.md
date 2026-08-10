# FRUSTRATED / ANGRY SNAPPING — PRE-REGISTRATION (block 242000)

**This document is committed BEFORE any measurement.** Every number below is a
PREDICTED interval, not a measurement. This rung is the "explosive episode" of
the developmental-emotion line (blocks 233000/239000/241000): Ross Greene's
explosive child, mechanised — *"kids do well if they can."* The snap is a
DYSREGULATION EVENT with a legible cause, NOT willful defiance. **NO
reward/punishment anywhere.**

## Base
- Base SHA: `bd6af1cbee4f148b4ded201d7e19d3b1ac657b98` (origin/main — it carries
  239000's `WindowOfTolerance` node + `worlds/coreg_dyad_world.py`, 241000's
  window-as-a-knob dyad, `seeds/affective_state_core.json` (the REAL
  `AffectiveState.arousal`), `seeds/staleness_decay.json` (`sd_blend`), the
  207000 time-cost `Drive`, `core_emotions`).
- Seed block: **242000–242999**. `python scripts/seed_claim.py 242000 242999` →
  `CLEAN — no collision DETECTED` (963 files with seed sinks; 676 unresolved
  sink sites tree-wide, counted not discarded; two load-bearing caveats
  reproduced verbatim in the results).
- Additive only: all new files are prefixed `snap_` / `SNAP`. No existing
  tracked file is touched. This rung REUSES 239000's `WindowOfTolerance` +
  `AffectiveState.arousal` and `sd_blend`'s leaky-EMA form; it rebuilds none of
  them.

## The model (Greene's explosive child, mechanised)
A "snap" is an accumulating FRUSTRATION RESIDUAL crossing the window of
tolerance's UPPER bound (`hi`, hyperarousal). Three defining signatures:

1. **ABRUPT** — the snap OUTPUT is all-or-none at threshold (a step), even
   though arousal/frustration build GRADUALLY (a continuous ramp). The last
   block before threshold is the "last straw."
2. **DISPROPORTIONATE** — the snap MAGNITUDE is set by the ACCUMULATED residual,
   NOT the immediate trigger. The SAME small trigger produces NO snap at LOW
   accumulated residual but a SNAP at HIGH accumulated residual. This is the
   glass-box dissolution of *"why blow up over THAT?"* — because N blocks of
   residual preceded it.
3. **DISCHARGING** — build → snap → drop (discharge) → recover.

ANGER vs undirected distress = whether there is an attributable BLOCKING AGENT:
frustration + a blaming attribution → DIRECTED approach-aggressive discharge
(anger); no attributable blocker (an impersonal obstacle) → UNDIRECTED distress
(no target). Window WIDTH gates it (narrow → snaps sooner / on smaller triggers
= the trauma profile). Co-regulation (239000) interrupts it.

## Architecture
Agents are GRAPHS in Rust; Python is a mechanical world adapter. Every decision
— accumulate frustration, couple arousal, fire the snap at the upper bound,
direct it by attribution, discharge, recover, co-regulate — is a graph RULE in
`seeds/snap_frustration.json` (self_load_only, default-OFF), riding the REAL
`AffectiveState.arousal` and 239000's `WindowOfTolerance` node. **NO Rust, NO
new Term** (all rules use Terms already present: Plus / Times / Minus / Attr /
Var / Lit / Eq / Gt / Lt / And / Not / Count / Neighbours / add_edge /
set_attr). **NO reward / punishment** — the snap is a STATE.

### The frustration accumulator reuses `sd_blend`
The leaky accumulator is a leaky integrator `F ← (1−leak)·F + gain·block`. Its
LEAK is literal `sd_blend` (staleness_decay's held-vs-new Kalman blend
`x ← x + α(target − x)`) toward 0 (`snap_frustration_leak`, α = leak, target =
0 — the `(1−α)` factor IS the leak, exactly `mood_r1`'s decomposition); the
block-drive term (`snap_goal_block_accumulate`, `F ← F + k_acc·magnitude`)
integrates each block's magnitude. Same atoms (Plus/Times/Minus), NO new Term.
Arousal RIDES the REAL `AffectiveState.arousal`: `snap_arousal_track` sets
`arousal = setpoint + frustration` — so arousal crossing the window's `hi` IS
frustration crossing `half_width`.

### Graph-resident state (all readable via graph_to_dict)
- Agent `AffectiveState`: `arousal` (REAL), `frustration` (the accumulated
  residual), `setpoint`, `k_acc`, `leak`, `k_co` (co-reg pull), `k_self`
  (recovery), `snapped` (all-or-none output pulse), `in_snap` (latch),
  `snap_count`, `snap_magnitude` (read from the residual), `snap_directed`,
  `snap_undirected`, `last_trigger_mag` (the small immediate trigger, recorded
  for glass-box disproportion), per-rule epoch guards (`tick_epoch`,
  `leak_epoch`, `cr_epoch`, `sr_epoch`).
- `WindowOfTolerance`: `lo`, `hi`, `half_width`, `min_half_width` — the UPPER
  bound `hi` is the snap threshold (reused unchanged from 239000).
- `GoalBlock`: `magnitude` (the trigger size), `armed`.
- `Blocker` (Agent) — the attributable blocking agent (present ⇒ `blocked_by`
  edge; an impersonal obstacle ⇒ no such edge).
- Caregiver `AffectiveState` (optional): `arousal`, `regulated` — the 239000
  co-regulation partner.

### The rules (all named, all in seeds/snap_frustration.json; engine `own`)
The load-bearing per-block recurrence (accumulate THEN leak, consecutive blocks)
is `F_n = (F_{n−1} + k_acc·mag)·(1 − leak)`.
1. `snap_goal_block_accumulate` (order 2, on `armed==1`) — `F ← F + k_acc·mag`;
   record `last_trigger_mag = mag`; consume `armed → 0` (the block-drive half —
   frustration RISES with goal-blocks).
2. `snap_frustration_leak` (order 3, per-tick epoch-gated) — `F ← F + leak·(0−F)`
   (literal `sd_blend` toward 0; the "leaky" half of the accumulator).
3. `snap_coreg_pull` (order 4, gated caregiver `regulated==1`, epoch-gated) —
   `F ← F + k_co·(cg_frustration − F)` (239000's co-reg EMA; a regulated
   caregiver bleeds frustration off each tick, holding it below `hi`).
4. `snap_arousal_track` (order 5, self-closing where `arousal ≠ setpoint+F`) —
   `arousal = setpoint + F` (rides the REAL arousal; arousal crossing `hi` ⇔ F
   crossing `half_width`).
5. `snap_threshold_fire` (order 6) — where `arousal > hi AND in_snap==0`: the
   SNAP. `snapped=1`, `in_snap=1`, `snap_magnitude = F` (read from the
   ACCUMULATED residual, NOT the trigger), `snap_count += 1`. All-or-none.
6. `snap_attribution_directed` (order 7) — where `snapped==1 AND snap_directed==0
   AND` a `blocked_by` Blocker exists: `snap_directed=1`; `add_edge directed_at
   → blocker` (ANGER).
7. `snap_attribution_undirected` (order 7) — where `snapped==1 AND
   snap_undirected==0 AND Count(blocked_by)==0`: `snap_undirected=1` (distress,
   no target).
8. `snap_discharge` (order 8) — where `in_snap==1 AND snapped==1`: DISCHARGE —
   `F ← F·(1−discharge)` (a big drop), `snapped=0` (the output is a one-tick
   pulse; the durable record is `snap_count`, `snap_magnitude`, `directed_at`).
9. `snap_recover` (order 9) — where `in_snap==1 AND F ≤ recover_floor`: clear
   `in_snap=0` (recovered, ready to re-escalate). (Leak continues via rule 2.)

## Frozen constants (pre-registered)
- `setpoint = 0.0`; `k_acc = 1.0` (each block integrates its full magnitude —
  maximally glass-box: F ≈ Σ block magnitudes − leak); `leak = 0.02`; `k_co =
  0.60`; `discharge = 0.90`; `recover_floor = 15.0`.
- Rule order (load-bearing): accumulate(2) → leak(3) → coreg(4) →
  arousal_track(5) → threshold_fire(6) → attribution(7) → discharge(8) →
  recover(9). Placing accumulate before leak fixes the recurrence
  `F_n = (F_{n−1} + mag)·(1 − leak)` deterministically.
- `TRIGGER_MAG = 10.0` (small, fixed across every arm — the immediate trigger).
- **G-window widths** (half-width levels, the IV): `{40, 70, 100}` (window
  WIDTH = 2·half-width). Each jittered ~ N(μ, 3). By the recurrence these give
  blocks_to_snap `{5, 8, 12}` (the first n with F_n > hi).
- **G-window failable control:** at MAX width `half_width = 400`, over the full
  cap of 30 consecutive blocks F saturates at F_30 ≈ 223 < 400 — NEVER reaches
  threshold (asymptote mag/leak = 500; hi=400 would need ≈84 blocks).
- **G-teeth residual levels:** LOW = 2 prior blocks (F ≈ 19.4), HIGH = 11 prior
  blocks (F ≈ 97.6), then ONE identical `TRIGGER_MAG` block (the 3rd resp. 12th);
  `half_width = 100` (F_12 ≈ 105.5 > 100 fires; F_3 ≈ 28.8 does not).
- **G-anger arms:** `blocker_present ∈ {True (agent), False (obstacle)}`.
- **G-coreg arms:** `alone` (no caregiver), `dysregulated_cg` (caregiver
  `regulated=0`), `regulated_cg` (caregiver `regulated=1`).
- N = 60 per arm (headline results/); N = 20 per arm in the test gate.
  SEED_BASE = 242000. Block sequence cap = 30 ticks.

## Metrics
- **blocks_to_snap** = number of goal-block events until the GRAPH fires the
  snap (`snapped` 0→1); censored at the cap (30) if it never snaps.
- **snapped_at_trigger** = did the single identical `TRIGGER_MAG` block fire a
  snap (0/1), measured at LOW vs HIGH prior residual (the teeth).
- **snap_magnitude** = the `snap_magnitude` the graph recorded = the accumulated
  residual `F` at the snap (contrast with `last_trigger_mag = 10`).
- **snap_directed_frac** = fraction of snaps with a `directed_at` edge (anger).
- **snap_frac** = fraction of runs that snapped within the cap.
- 95% CIs (t≈1.96); "CI-separated" = one arm's CI lower bound strictly above the
  other's CI upper bound.

## Gates and PREDICTED intervals (predictions, NOT measurements)

### G-snap-is-threshold (HEADLINE)
Arousal/frustration builds GRADUALLY but the snap OUTPUT is ABRUPT (all-or-none)
at the upper window bound; AND — the DISPROPORTION TEETH — the SAME small trigger
produces NO snap at LOW residual but a SNAP at HIGH residual.
- **Gradual-build vs abrupt-output:** over the ramp to the snap, the max
  per-tick arousal increment is small (predicted `≤ TRIGGER_MAG = 10`, a
  gradual continuous rise) while `snapped` transitions 0→1 in a SINGLE tick (a
  step). The snap tick is the FIRST tick with `arousal > hi`.
- **DISPROPORTION TEETH (the last straw):** at LOW residual (2 prior blocks,
  F ≈ 19.4), the identical `TRIGGER_MAG=10` block fires NO snap — predicted
  `snapped_at_trigger = 0`. At HIGH residual (11 prior blocks, F ≈ 97.6), the
  IDENTICAL block fires a SNAP — predicted `snapped_at_trigger = 1`. The two are
  perfectly separated (0 vs 1 across all seeds).
- **Snap magnitude ≫ trigger:** predicted `snap_magnitude` interval **[100, 110]**
  at HIGH residual (≈ accumulated F_12 at `half_width=100`), while
  `last_trigger_mag = 10.0` exactly — the snap is set by the residual, not the
  trigger. Ratio predicted **> 5×**.
- **FAILABLE CONTROL:** if the low-residual arm ALSO snaps on the identical
  trigger (teeth don't separate), OR the snap magnitude tracks the trigger (10)
  rather than the residual, the headline FAILS — reported straight.

### G-window-gates-snapping
Narrow window → snaps SOONER (fewer blocks to threshold); monotone across ≥3
widths, CI-separated.
- **Predicted blocks_to_snap — half-width 40:** interval **[4.5, 5.5]** (≈5).
- **Predicted blocks_to_snap — half-width 70:** interval **[7.5, 8.5]** (≈8).
- **Predicted blocks_to_snap — half-width 100:** interval **[11.5, 12.5]** (≈12).
- **Predicted separation:** blocks_to_snap(40) CI-upper < (70) CI-lower < (100),
  strictly monotone increasing, all three CI-separated (narrow snaps sooner).
- **FAILABLE CONTROL:** at MAX width (`half_width = 400`) the full cap of 30
  consecutive blocks NEVER reaches threshold — predicted `snap_frac = 0.0` (all
  censored). If the widest window still snaps on the same sequence, the window
  does not gate and the gate FAILS.

### G-anger-is-directed
With an attributable blocking AGENT → the discharge is DIRECTED at it (anger);
with only an impersonal obstacle → UNDIRECTED distress (no target).
- **Blocker-present arm:** predicted `snap_directed_frac` **[0.95, 1.0]** (a
  `directed_at` edge minted at every snap), `snap_undirected_frac` **[0.0, 0.05]**.
- **Obstacle arm (no attributable blocker):** predicted `snap_directed_frac`
  **[0.0, 0.05]** (NO `directed_at` edge), `snap_undirected_frac` **[0.95, 1.0]**.
- **CI-separated:** directed_frac(blocker) CI-lower strictly above
  directed_frac(obstacle) CI-upper.
- **FAILABLE CONTROL:** if the obstacle arm ALSO directs the snap (mints a
  `directed_at` edge with no attributable blocker), the attribution mechanism is
  fake and the gate FAILS.

### G-coreg-interrupts (ties to the developmental line)
A regulated caregiver present → arousal held below threshold → FEWER/NO snaps vs
alone; CI-separated.
- **Alone arm:** predicted `snap_frac` **[0.95, 1.0]** (the block sequence
  reaches threshold).
- **Dysregulated-caregiver arm (failable control):** predicted `snap_frac`
  **[0.95, 1.0]** (a dysregulated caregiver does not co-regulate — snaps like
  alone).
- **Regulated-caregiver arm:** predicted `snap_frac` **[0.0, 0.10]** (the co-reg
  pull bleeds frustration off, holding it below `hi`).
- **CI-separated:** snap_frac(alone) CI-lower strictly above snap_frac(regulated)
  CI-upper; snap_frac(dysregulated) overlaps alone, NOT regulated.
- **FAILABLE CONTROL:** if a regulated caregiver does NOT reduce snaps (snap_frac
  as high as alone), OR an absent/dysregulated caregiver DOES reduce them,
  co-regulation is not interrupting and the gate FAILS.

### G-glass-box
The accumulated frustration residual (`frustration`), arousal, window bounds
(`lo,hi`), trigger magnitude (`last_trigger_mag`), snap magnitude
(`snap_magnitude`), and the attribution target (`directed_at` edge) all
reconstruct from `graph_to_dict`. The disproportion is READABLE (trigger small
= 10, residual at threshold ≈ 100). Every decision is a named rule; source-audit
clean; NO reward/punishment token.

### G-discipline
Rides the REAL `AffectiveState.arousal` + 239000's `WindowOfTolerance`; the
frustration accumulator reuses the `sd_blend` leaky-EMA form; default-OFF
(self_load_only, `depends_on: [affective_state_core]`); NO Rust (`runners/dsl`
diff EMPTY, canonical `.so` md5 UNCHANGED); own engine (`source_match == own`);
oracle BEFORE == AFTER; per-area zero new reds.

## The prior-art delta being claimed (honest, per PRIOR_ART_SOCIAL_EXPERIMENTS.md)
- **CONCEDED as prior art (NOT claimed):** appraisal-theory anger models (OCC;
  EMA / Gratch & Marsella), the frustration-aggression hypothesis (Dollard et
  al. 1939; Berkowitz's cognitive-neoassociationist revision), and RL-frustration
  (blocked-reward negative RPE) all EXIST. We do not claim to be first to model
  frustration, blocked goals, or anger appraisal.
- **The ONLY delta claimed here:** the snap as a THRESHOLD-crossing of the
  ACCUMULATED frustration residual against a SETTABLE window of tolerance,
  UNIFIED on ONE substrate with (a) co-regulation (239000) that interrupts it,
  (b) the settable window WIDTH that gates it (241000's knob), and (c) the
  glass-box disproportion-readable dissolution of "why blow up over THAT" — the
  trigger and the residual are separately inspectable graph state, so the
  disproportion is a legible cause, mechanising Greene's *"kids do well if they
  can."* Any "no prior model does X" absence claim is weak-by-construction
  (PRIOR_ART_SOCIAL_EXPERIMENTS.md): we make none.

## Honest scope
This is a **synthetic** model of the explosive-episode / window-of-tolerance /
frustration-aggression frameworks (grounded in the creator's in-vivo experience
with 21 foster children), NOT a clinical-outcome number. Mechanism-proven ≠
clinically valid; the two are reported separately. Known residuals to be recorded
in the results: arousal is a SCALAR (not the multi-branch polyvagal autonomic
state); the window is a SYMMETRIC band about a fixed setpoint; the accumulator is
a single leaky integrator (no multi-timescale slow/fast frustration); the
attribution is a single blocked_by edge (no graded blame or multi-agent
attribution); the discharge is a single geometric drop, not a modelled
behavioural act; no long-term developmental trajectory (the widen/narrow of
239000 is not re-run here). A null gate IS a result and will be reported straight.

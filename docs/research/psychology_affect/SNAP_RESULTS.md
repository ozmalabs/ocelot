# FRUSTRATED / ANGRY SNAPPING — RESULTS (block 242000)

Measured against the pre-registration in `SNAP_PREREG.md` (committed BEFORE any
number). Full-power run N=60: `results/snap.json`; gate: `tests/test_snap_migrated.py`
(12/12 green). The explosive episode of the developmental-emotion line, Ross
Greene's explosive child mechanised — *"kids do well if they can."* The snap is a
STATE with a legible cause; NO reward/punishment anywhere.

- Base SHA: `bd6af1cbee4f148b4ded201d7e19d3b1ac657b98`.
- Engine: `source_match == own` (this worktree's build; canonical `.so`
  UNCHANGED; `runners/dsl` diff EMPTY; NO Rust, NO new Term).
- Seed: `seeds/snap_frustration.json`, `self_load_only`, `depends_on:
  [affective_state_core]`, nine `snap_*` rules. Rides the REAL
  `AffectiveState.arousal` + 239000's `WindowOfTolerance`; the frustration
  accumulator's leak is literal `sd_blend` toward 0.

## Headline — G-snap-is-threshold (PASS)
The accumulated frustration residual crossing the window's UPPER bound.

| quantity | predicted | MEASURED (N=60) |
|---|---|---|
| teeth — snapped_on_trigger at LOW residual (2 prior blocks) | 0 | **0.000 [0.000, 0.000]** |
| teeth — snapped_on_trigger at HIGH residual (11 prior blocks) | 1 | **1.000 [1.000, 1.000]** |
| teeth separated (CI) | yes | **yes** (1.0 vs 0.0) |
| snap_magnitude at HIGH residual | [100, 110] | **105.489** |
| last_trigger_mag | 10.0 | **10.000** |
| magnitude / trigger ratio | > 5× | **10.55×** |
| max per-tick arousal increment (the gradual ramp) | ≤ 10 | **9.604** |
| snap output all-or-none (integer steps) + magnitude > hi | yes | **yes** |

**THE DISPROPORTION TEETH (the "last straw").** The SAME small trigger (magnitude
10) fires NO snap at low accumulated residual and a SNAP at high accumulated
residual — the ONLY difference is the number of prior goal-blocks. This is the
glass-box dissolution of *"why blow up over THAT?"*: the trigger is trivial (10);
the snap magnitude (105) is the accumulated residual, read straight off the graph.
Arousal builds GRADUALLY (per-tick increment ≤ the trigger magnitude, a continuous
ramp: 9.8 → 19.4 → … → 97.6) while the snap OUTPUT is ABRUPT — `snap_count` steps
0→1 in a single tick when arousal first exceeds `hi`, and the recorded magnitude
(105.49) exceeds `hi` (100), i.e. arousal crossed the upper bound.

**Failable control:** if the low-residual arm ALSO snapped on the identical
trigger, or the magnitude tracked the trigger (10) not the residual, the headline
would fail. It did not.

## G-window-gates-snapping (PASS)
A narrow window snaps SOONER (fewer blocks to threshold) — the trauma profile.

| half-width | predicted blocks_to_snap | MEASURED (N=60) |
|---|---|---|
| 40 | [4.5, 5.5] (≈5) | **4.750 [4.630, 4.870]** |
| 70 | [7.5, 8.5] (≈8) | **8.183 [8.074, 8.293]** |
| 100 | [11.5, 12.5] (≈12) | **11.917 [11.775, 12.059]** |

Monotone increasing, all three CI-separated. **Failable control:** at MAX width
(half-width 400) the full 30-block sequence NEVER reached threshold —
`snap_frac = 0.0`. (The means fall a little below the integer because half-width
is jittered ~N(μ, 3); a narrower draw crosses one block sooner.)

## G-anger-is-directed (PASS)
Anger vs undirected distress = whether an attributable blocking AGENT is present.

| arm | predicted directed_frac | MEASURED (N=60) |
|---|---|---|
| attributable blocking AGENT (`blocked_by` edge) | [0.95, 1.0] | **1.000 [1.000, 1.000]** |
| impersonal obstacle (no `blocked_by` edge) | [0.0, 0.05] | **0.000 [0.000, 0.000]** |

CI-separated. With an attributable blocker the graph mints a `directed_at` edge at
every snap (ANGER, directed at the blocker); with only an obstacle the snap is
UNDIRECTED distress (`snap_undirected=1`, no target). **Failable control:** the
obstacle arm never directed the snap — the attribution reads a real graph edge, it
is not fabricated.

## G-coreg-interrupts (PASS) — ties to the 239000 developmental line
A regulated caregiver holds arousal below threshold.

| arm | predicted snap_frac | MEASURED (N=60) |
|---|---|---|
| alone (no caregiver) | [0.95, 1.0] | **1.000 [1.000, 1.000]** |
| dysregulated caregiver (`regulated=0`) | [0.95, 1.0] | **1.000 [1.000, 1.000]** |
| regulated caregiver (`regulated=1`) | [0.0, 0.10] | **0.000 [0.000, 0.000]** |

The regulated arm is CI-separated below alone (co-regulation INTERRUPTS the snap:
the co-reg pull bleeds frustration off each tick, saturating it at ≈6.5 ≪ 100).
**Failable control:** a dysregulated caregiver does NOT interrupt — it snaps like
alone (overlaps alone, CI-separated above the regulated arm). If a dysregulated
caregiver had reduced snaps, co-regulation would not be the mechanism.

## G-glass-box (PASS)
Reconstructed from `graph_to_dict` alone: `frustration` residual, `arousal`, the
window bounds `[lo,hi] = [-100, 100]`, `last_trigger_mag = 10.0`, `snap_magnitude
= 105.49` (> `hi`), `snap_count`, and the `directed_at` attribution target edge.
`disproportion_readable = true` (trigger small, residual at threshold);
`magnitude_from_residual_not_trigger = true` (105 > 5×10). Every decision is a
named `snap_*` rule; source-audit clean (no Python rule-engine call, NO
reward/punishment token).

## G-discipline (PASS)
`source_match == own`; canonical `.so` md5 UNCHANGED
(`e75bc65021b6be0740abeee63662e21b`); `runners/dsl` diff EMPTY (NO Rust, NO new
Term — Plus/Times/Minus/Attr/Var/Lit/Eq/Gt/Lt/And/Not/Count/Neighbours/add_edge/
set_attr all pre-exist); seed `self_load_only`, default-OFF; nine `snap_*` rules.
Oracle `rung7_vision_bench.sh` BEFORE == AFTER (214 passed / 10 skipped, `data/`
absent); `per_area_settlement_regression.sh` fail-set identical BEFORE == AFTER
(23 pre-existing reds, `data/` absent — ZERO new reds; the additive `snap_` files
are in neither oracle's explicit file list).

## Prior art (honest) — conceded vs claimed
- **CONCEDED as prior art (NOT claimed):** appraisal-theory anger (OCC; EMA /
  Gratch & Marsella), the frustration-aggression hypothesis (Dollard et al. 1939;
  Berkowitz's cognitive-neoassociationist revision), RL-frustration (blocked-reward
  negative RPE). We are not first to model frustration, blocked goals, or anger
  appraisal.
- **The delta claimed:** the snap as a THRESHOLD-crossing of the ACCUMULATED
  frustration residual against a SETTABLE window of tolerance, UNIFIED on ONE
  substrate with (a) co-regulation (239000) that interrupts it, (b) the settable
  window WIDTH (241000's knob) that gates it, and (c) the glass-box
  disproportion-readable dissolution of *"why blow up over THAT"* — trigger and
  residual are separately inspectable graph state, so the disproportion is a
  legible cause. Greene's explosive child, mechanised. Any "no prior model does X"
  absence claim is weak-by-construction (per `PRIOR_ART_SOCIAL_EXPERIMENTS.md`);
  we make none.

## Honest scope / residuals
SYNTHETIC mechanism, NOT a clinical-outcome number (mechanism-proven ≠ clinically
valid). Residuals, as pre-registered: arousal is a SCALAR (not the multi-branch
polyvagal autonomic state); the window is a SYMMETRIC band about a fixed setpoint;
the accumulator is a single leaky integrator (no multi-timescale slow/fast
frustration); the attribution is a single `blocked_by` edge (no graded blame or
multi-agent attribution); the discharge is a single geometric drop, not a modelled
behavioural act; no long-term developmental trajectory (239000's widen/narrow of
the window is not re-run here). Every gate came out as predicted — no null this
run; a null would have been reported straight.

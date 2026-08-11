# AROUSAL / WINDOW-OF-TOLERANCE with CO-REGULATION — RESULTS (block 239000)

Pre-registration: `AROUSAL_WOT_PREREG.md` (committed first, `602d9f5d`). Machine
record: `results/arousal_wot.json`. Test gate: `tests/test_arousal_wot_migrated.py`
(10/10). N = 60 infants per arm, N_episodes = 15, SEED_BASE = 239000. Base SHA
`9c5172d697d031ac613a36e5bc98b7edfb373723`.

**Every gate landed, every prediction fell inside its pre-registered interval.**

## G-co-regulation (HEADLINE)
Return-to-window time (ticks; censored at 40).

| arm | return_ticks (mean [95% CI]) | censored | predicted |
|---|---|---|---|
| **co-regulation** (regulated caregiver present) | **1.12 [1.03, 1.20]** | 0% | [1, 3] |
| ALONE (caregiver absent) — *failable control* | 7.65 [7.26, 8.04] | 0% | [6, 10] |
| DYSREGULATED caregiver present — *failable control* | 40.00 [40.00, 40.00] | **100%** | [35, 40] |

- Co-regulation returns the infant to its window **CI-separated faster** than
  alone (1.20 < 7.26). ✓
- A **dysregulated caregiver** (own arousal 120, above the band) couples the
  infant the WRONG way — arousal converges ≈ 104 and **never returns** (100%
  censored), strictly worse than being alone. ✓ Both failable controls behaved
  as predicted; neither could have passed by construction.

## G-window-widens (development / healing)
Window half-width before vs after 15 episodes.

| | initial | final | predicted final |
|---|---|---|---|
| **co-regulation arm** | 30.11 [28.58, 31.65] | **60.11 [58.58, 61.65]** | [55, 65] |
| control (no co-reg) | 30.11 [28.58, 31.65] | 5.70 [5.35, 6.05] | narrows, not widen |

Repeated co-regulation **widens** the window, CI-separated above initial (58.58 >
31.65). ✓ The failable control (repeated stress, caregiver absent) does **not**
widen — it narrows to the floor. ✓

## G-trauma-narrows (pathology direction)
| | traumatised (no co-reg) | healed (co-reg) | separated |
|---|---|---|---|
| window half-width | 5.70 [5.35, 6.05] | 60.11 [58.58, 61.65] | yes |
| safety_prior | 0.05 [0.05, 0.05] | 0.95 [0.95, 0.95] | yes |

Repeated stress without co-regulation **narrows** the window and **lowers the
safety prior**, CI-separated below the co-regulated arm — the traumatised profile
(small window, easily dysregulated, low safety prior). ✓

## G-glass-box
`AffectiveState.arousal` (infant + caregiver), the `WindowOfTolerance` band
`[lo, hi]` + `safety_prior`, and the `attended_by` co-regulation coupling edge
all reconstruct from `graph_to_dict` alone. Every regulation decision is a named
rule (nine): `arousal_stressor_push`, `dysreg_onset_hyper`, `dysreg_onset_hypo`,
`coreg_pull`, `selfreg_pull`, `mark_coreg_support`, `dysreg_return_to_window`,
`episode_resolve_widen`, `episode_resolve_narrow`.

## G-discipline
- Agents = graphs on the REAL emotion framework: the infant/caregiver `arousal`
  IS `seeds/affective_state_core.json`'s `AffectiveState.arousal`; the seed
  `depends_on: [affective_state_core]`.
- World = mechanical adapter (`worlds/coreg_dyad_world.py`) — delivers stress /
  caregiver presence/regulation, reads graph state. Source audit **clean**: no
  Python rule-engine call, **no reward/punishment token** (dysregulation is a
  STATE, never a badness — Greene, "kids do well if they can").
- default-OFF: `self_load_only: true`. **NO Rust** (`runners/dsl` diff empty).
- Own engine: `source_match == own`; own `.so` md5 `e75bc65021b6be0740abeee63662e21b`
  (byte-identical to the canonical shared engine; canonical unchanged).
- Oracle `rung7_vision_bench.sh`: 224 == 224 (with `data/` symlinked).
  `per_area_settlement_regression.sh`: 306/0 == 306/0; zero new reds from these
  files.

## The coupling reuses sd_blend's leak
`coreg_pull` / `selfreg_pull` are the leaky Kalman/EMA pull from
`sd_blend` (`seeds/staleness_decay.json`): `arousal ← arousal + k·(target −
arousal)` — co-regulation targets the caregiver's arousal (k_co = 0.50),
self-regulation targets the setpoint (k_self = 0.15). A constant-gain
(degenerate-freshness) instance of the same primitive.

## Honest scope — synthetic mechanism vs clinical validity
This is a **synthetic** instantiation of the window-of-tolerance (Siegel;
Porges polyvagal; van der Kolk) and co-regulation frameworks, grounded in the
creator's in-vivo experience (21 foster children, many traumatised, healed). The
numbers above are **mechanism-proven, NOT clinical-outcome numbers**. What the
model does NOT capture (recorded residuals):

1. **Arousal-dynamics fidelity** — a single scalar with a constant-gain leak; real
   autonomic arousal is multi-channel with nonlinear vagal braking.
2. **Window as a scalar band** — a symmetric `[−hw, hw]` interval, not the richer
   polyvagal state (ventral-vagal / sympathetic / dorsal-vagal are collapsed to
   hyper/hypo sign).
3. **No long-term developmental trajectory** — plasticity is a per-episode
   increment; no consolidation, sensitive periods, or forgetting.
4. **Caregiver regulation held fixed** — the "regulated caregiver" sits at a
   constant arousal; a real dyad is bidirectional (the infant's distress also
   dysregulates the caregiver).
5. **Arousal driven directly** — the stressor writes/rules push `AffectiveState.
   arousal` directly rather than through the full drive→modulator→PSI projection
   the Harlow rung exercised; a deliberate simplification to isolate the
   window/co-regulation mechanism.

The mechanism — window, dysregulation as a state, external co-regulation
entrainment, plasticity in both directions — is exactly the clinical model, made
graph-native and glass-box. Whether these dynamics quantitatively match a real
infant is a separate, unmeasured question.

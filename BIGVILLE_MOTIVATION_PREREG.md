# PREREG — block 325000: the motivational core — drives + modulators (C1)

`BIGVILLE_COGNITIVE_CAPABILITIES_PLAN.md` C1 — the MAEM keystone. Generalize bigville's
single hunger drive into a grounded **drive set** whose deficits select goals, plus **Psi
modulators** that shape cognition. Grounded in Dörner's Psi theory / Bach's MicroPsi
(urges + modulators) and Self-Determination Theory (Deci & Ryan: innate psychological
needs — competence, relatedness/affiliation, plus a certainty/uncertainty-reduction urge).

## The capability

Each agent holds a set of `Drive{kind, level, setpoint, weight}` nodes (extensible — the
set is data, not a hardcoded count). Two grounded families: **physiological** (sustenance)
and **psychological** (competence, affiliation, certainty). Dynamics:

- **`mv_urge`** — each drive's `urge = weight · max(0, setpoint − level)`: the deficit,
  scaled by how much this agent cares (its weight). The weight profile is the agent's
  *personality of motivation* — the held params its choice reads.
- **`mv_arousal`** — the agent's `arousal` = its most pressing (max) urge, and the **Psi
  modulators** derive from it: `resolution_level = max(0, 1 − res_gain·arousal)` (high
  arousal → shallow/narrow processing) and `selection_threshold = thr_gain·arousal` (high
  arousal → high goal-commitment/persistence).
- **`mv_bootstrap` / `mv_refresh` / `mv_switch`** — the agent **pursues** the drive with
  the greatest urge (an Argmax collapse over its own drives), but only **switches** goal
  when a challenger's urge exceeds the incumbent's by more than the **selection
  threshold** (hysteresis). This is the modulator doing real cognitive work: a highly
  aroused agent perseverates; a calm one re-plans freely.

Different agents diverge on the same world because the choice reads each agent's own drive
weights — the collapse principle, applied to motivation.

## Gates (pass/fail, pre-registered) — signatures, not tuned numbers

1. **G-drive-profiles-diverge (HEADLINE):** two agents with the same drive *kinds* but
   different *weights*, at the same levels, pursue **different** goals — motivation is the
   agent's own, not a global.
2. **G-dominant-urge-selects-the-goal:** the pursued goal is the max-weighted-urge drive;
   **satisfying** it (raising its level) flips the pursuit to the next-most-urgent drive.
3. **G-modulators-track-arousal:** an agent with large unmet urges has high arousal → low
   resolution + high selection threshold; a satisfied agent has the opposite.
4. **G-selection-threshold-is-load-bearing (HEADLINE):** with a high threshold the agent
   **persists** with its current goal though a challenger slightly out-urges it; with
   threshold 0 it **switches immediately** (thrashes). Proves the modulator shapes cognition.
5. **G-uniform-drives-collapse-divergence (falsifier):** identical drive profiles → agents
   pursue the **same** goal — divergence comes from the held profile, not noise.
6. **G-no-python-decision (source audit):** urge/arousal/select/switch are the seed rules;
   the goal selection is an Argmax collapse in the seed; the adapter mints drives, sets
   levels (world I/O), ticks, and reads.

## Scope / honesty
- Drives, modulators, arousal, and pursuit are the agent's **own held state** its collapse
  reads — no global tick drives them; drive *depletion over time* is a world-fact metabolic
  pulse the adapter issues (bodies get hungry), separated from the selection this rung gates.
- Autonomy (SDT's third need) and the Yerkes–Dodson arousal→performance link are deferred
  (the latter is C2). This rung is motivation + modulators; C2/C3/C4 build on it.
- `arousal = max urge` is the dominant-need proxy for total activation (the DSL has no
  sum-over-node-set); a weighted sum is a later refinement.
- Isolated demonstrator (`self_load_only`); no Rust; `.so` untouched (`a8a9012c`).

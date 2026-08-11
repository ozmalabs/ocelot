# Next session — start here

Paste the block below as the opening prompt.

---

Continue the F-16 fault-tolerant-control work in
`/home/matt/ozma/internal-worktrees/gamma-embodied-adaptation/research/experiments/gamma-substrate`
(branch `gamma-substrate/embodied-adaptation`, everything uncommitted).

**Read first:** `docs/regime_pareto_frontier_results.md` (both powered
blocks and the mechanism), `docs/regime_pareto_frontier_prereg.md` (the
design, the falsified first prediction, the four defects, and every
prediction committed before its block),
`docs/metastable_regime_escalation.md` (how the ladder was built and what
each variant measured), `docs/embodied_pareto_profiles.md` (the Pareto
primitive and its "no smuggled scalar" law), and `CLAUDE.md` (THE
ARCHITECTURE RULE — the agent is a graph in Rust; Python is only a world
adapter; edit `scripts/gen_*_seed.py` and regenerate, never hand-edit
`seeds/*.json`).

**Where it stands.** The nominal regression is FIXED and gated at power:
n=100 nominal is 0.00 crash, altitude RMSE 324.2 ft (v3: 377.8, gate
floor 352), settled 0.81, and **0/100 escalations** — on the base seed
the controller is byte-identical to the pre-regime-machinery native
MotorCompose baseline. Four defects were behind the 88/100 nominal
escalations; all four are fixed and gated
(`control_regime_escalation` v3.1.0, `f16_flight_path_control` v2.1.0).

The fault side is a **measured negative with the full corner set**, and
a **clean null once the two new corners are removed**. Both blocks are
powered, n=100 x 4, and both were prereg'd:

| scenario | v3 | ceiling 5 (all corners) | ceiling 2 (v3-era corners) |
|---|---:|---:|---:|
| nominal | 0.00 / 377.8 ft | 0.00 / **324.2 ft** | 0.00 / **324.2 ft** |
| jammed rudder | 0.04 | **0.65** worse | 0.01 null |
| saturated elevator | 0.16 | **0.73** worse | 0.17 null |
| damaged wing | 0.42 | **0.73** worse | 0.50 null |

The recommended configuration is the fixed machinery at
`regime_max_ordinal = 2`: v3-neutral on faults, better on nominal. It is
a null with a free improvement attached, not a win. **The two new
regimes the reframe called for remain UNVALIDATED** — they engage
(93/100 and 79/100) and they lose.

**The measured cause, and the open question.** Every Pareto axis is read
off the aircraft AS IT IS NOW, under the regime that is failing, and then
attributed to corners that would change that situation. In a jam both
heading and altitude read negative — but the sink is negative BECAUSE the
unwinnable heading fight is bleeding lift, and retiring heading (orbit)
restores altitude, which is exactly what v3 measured. So the corner that
surrenders BOTH dominates the corner that surrenders heading alone: orbit
was adopted 3/100 in the jam block, roll priority 91/100.

The availability ablation isolates it at power — same seeds, same
machinery, only `regime_max_ordinal` changed so the two new corners are
never proposed, and every fault returns to a CI-overlapping null. The
rewritten selection machinery is not what broke the faults; the new
corners' scoring is.

**The candidate next rung, in the project's own established pattern:**
score a corner by RENDERING it, not by reading the failing regime's
telemetry. This is the same move the Omniglot arc landed ("bins propose,
continuous decides") and the same move `MotorCompose` already makes at
the motor grain — propose from held structure, then evaluate the proposal
against a predicted rollout rather than against the present. Concretely:
a candidate's altitude axis should be evaluated under THAT corner's own
attitude assumption (wings-level for orbit / roll priority), which is the
one thing the current instrument cannot express.

Two smaller, cheaper things that are worth measuring first, in this
order:

1. **A sixth declared axis (lateral / sideslip).** With five axes the
   sideslip-trim corner is Pareto-IDENTICAL to hold — it surrenders zero
   sideslip, which is not one of the five — so under the
   strict-improvement policy it is not independently selectable. v3
   adopted trim in 98/100 jam episodes before orbit. The axis is
   observable (`state_sideslip` is stamped every action); what it needs
   is a declared authority to be measured against, the way heading has
   `g tan(max bank) / V`. Both fault blocks show trim and orbit adopted
   in exactly the same episodes — that identity, visible.
2. **The damaged wing is the scenario most likely to move.** In the
   ceiling-2 block it has no corner addressing its inversion and carries
   the worst point estimate (0.50 vs v3's 0.42, CI-overlapping). If
   per-corner evaluation gets built, gate it there first.

Do NOT re-litigate the surrender-scores-0.0 convention without a
measurement: it is the prereg'd named risk, it is now measured twice, and
the honest fix is a per-corner evaluation, not a different constant.

**Standing method rules, learned the hard way in this line:**
- POWER THE GATE BEFORE THE ENDGAME. Never tune against named failing
  seeds — that produced the arch4 null already recorded in the prereg doc
  (four rescued seeds, zero generalisation).
- Report nulls as nulls; overlapping CIs are not an improvement.
- Prereg the prediction before the powered run, and hold the result to
  it. Both blocks in `docs/regime_pareto_frontier_results.md` were.
- A 10-seed pre-flight before any powered block. It caught two separate
  showstoppers this session that single seeds hid.
- Version-bump regenerated seeds and update pins in
  `tests/test_control_regime_escalation_migrated.py` and
  `tests/test_jsbsim_f16_paper_replication_migrated.py`.
- **Four red tests are NOT yours** (node ids, not a count — see the
  retraction note in `CLAUDE.md`):
  `tests/test_jsbsim_f16_coupled_migrated.py::test_factorized_system1_and_system2_meet_their_planning_horizons`
  (System-1 p99 <1000us, environmentally borderline),
  `tests/test_jsbsim_f16_departure_recovery_migrated.py::test_graph_recovers_deep_stall_without_scripted_surface_commands`
  (30 m altitude-loss bound),
  `tests/test_jsbsim_f16_departure_recovery_migrated.py::test_motor_seed_contains_departure_gating_and_alpha_recovery`
  (stale `embodied_motor_program` pin: asserts 1.5.0, seed is 1.8.0), and
  `tests/test_humanoid_motor_program_migrated.py::test_recovery_basin_composes_compatible_effectors_and_sweeps_hold`
  (secondary token motor_a vs motor_c, from the v1.8.0 native composer).
  The last two are pre-existing residue from the MotorCompose session and
  are worth fixing or re-pinning deliberately, not ignoring.

**Run commands:** `PYTHONPATH=runners/dsl/python:. ../../../.venv-jsbsim/bin/python <script>`;
tests with `-m pytest tests/<file> -q`. Regime diagnostics:
`GAMMA_REGIME_DIAGNOSTICS=1` puts the escalation contract's own attrs into
every trace row (`scripts/jabberwock_fixed_wing_jet.py`) — that is what
found all four defects. Block comparison:
`python scripts/analyse_f16_gate_block.py --baseline <dir> --candidate <dir>`
prints Wilson intervals and corner adoption. Availability ablation:
`python scripts/ablate_f16_regime_ceiling.py --scenario <name>
--base-seed <seed> --max-ordinal <n> --episodes <n> --output <path>`.

Run scenarios in parallel with nohup, one process each; a block is
35-100 min depending on how many run at once.

**Current best config: v3** (deliberation architecture,
`results/..._matrix_v3/`) — jam 0.04, elevator 0.16, wing 0.42, nominal
0.00 at 377.8 ft. The Pareto line's only surviving gain so far is
nominal: 324.2 ft with zero escalations.

---

## Wider context (unchanged from the previous handoff)

- **The paper comparison ran and stands**: 8 scenarios x 100 episodes x
  100 s in `results/..._matrix_v1/`, six of eight matching the paper's
  claimed 0.00 crash rate (Wilson upper bound 3.7%), documented in
  `docs/jsbsim_f16_paper_replication.md`. That result predates the
  relativization work and is not affected by it.
- **Native MotorCompose** (`runners/dsl/src/motor_compose.rs`, engine
  term, `embodied_motor_program` v1.8.0): the search composer's exact
  selection in Rust, System-2 p99 600 ms -> ~40 ms, alphabet-flat, exact
  parity gated. Solid; leave alone.
- **Async System-2 publication** (v1.7.0) is implemented, correct, and
  DISABLED — measured negative on a single-threaded engine. Waits on an
  engine scheduler that can run synthesis off the action boundary.
- **Wings-off terminal recovery** (`docs/f16_wings_off_terminal_recovery.md`,
  `scripts/jabberwock_f16_wings_off_terminal.py`): eject window reached
  10/10, hardware survivability 0/10 both arms. Blocked on attitude
  authority at low q; the identified fix is compressor-bleed pulsed RCS,
  deliberately NOT simulated. Do not resume unless asked.

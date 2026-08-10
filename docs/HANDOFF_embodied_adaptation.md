# Handoff — F-16 fault-tolerant control, embodied-adaptation line

Paste the **Prompt** section below to resume. Everything above it is the state
that prompt assumes.

---

## OPEN REGRESSION FROM THE MERGE — read this first

Merging this line into `main` (`c9cb553539`) surfaced **5 failures in
`tests/test_control_regime_escalation_migrated.py`** that pass on the branch:

```
test_no_projected_transition_routes_to_recalibration  KeyError: 'regime_recalibration_requested'
test_a_lost_fixpoint_admits_the_full_corner_set       assert 0.0 == 5.0
test_restoring_the_basin_is_admissible_only_while_the_reserve_lasts
(+2 more)
```

**Already ruled out, so do not re-check these:**

* the seeds — `control_regime_escalation.json`, `f16_flight_path_control.json`
  and `embodied_motor_program.json` are byte-identical between the branch
  worktree and `main`, and regenerating them changes nothing;
* the test file — byte-identical (the merge took the branch's version; `main`
  had zero commits touching it);
* the Rust runtime — `main`'s own build loads every Term with no
  `UnknownTermType` warnings, and swapping the branch-built `.so` in does not
  change the result either way.

**What is left:** `substrate/world_adapter.py` and `substrate/boot_core.py`
BOTH DIFFER between the branch and `main`. `main` changed them (via the
humanoid-language line) and this branch did not, so the merge took `main`'s
versions, and the F-16 regime rules behave differently under them. The symptom
is that `f16_recalibrate_on_no_projected_transition` does not produce
`regime_recalibration_requested`. Start by diffing those two files and looking
at rule installation / seed reconciliation.

The branch `gamma-substrate/embodied-adaptation` is preserved and is the
working reference where all 32 of these tests pass.

## Where the tree stands

**1/9 ground contact** over three faults (damaged_wing, saturated_elevator,
jammed_rudder) at three episodes each — the control. Every piece of the last
sequence that measured neutral-or-better is ON; every piece that measured worse
is gated OFF and retained with its number.

| piece | state | measured |
|---|---|---|
| margin price in `program_cost` | **ON** | deciding path (976/977 admissions) |
| attribution / credit assignment | **ON** | exactly neutral; 1 member exercised → 31 |
| surprise index + condensation + reflexes | **ON** | 27 engine firings/episode, no cost |
| shape-change recalibration trigger | reverted | +3 episodes |
| adaptation rate from shape | gated off | +3 episodes |
| regime-local models (fork) | gated off | +2 episodes |

Gate suites, all green: `test_margin_price_migrated`,
`test_attribution_price_migrated`, `test_adaptation_rate_migrated`,
`test_reflex_condensation_migrated`, `test_regime_local_models_migrated`,
`test_fork_token_regression`, `test_control_regime_escalation_migrated`,
`test_fixed_wing_jet_control_migrated`.

## What was built, and what each thing is for

* **`margin_price`** (`runners/dsl/src/motor_compose.rs`) — `program_cost` can
  say "take this one because it buys more time". Urgency is
  `margin_reference_actions / margin_actions`, a hyperbola in time-to-go. The
  margin is a min over regions to **avoid** only (`region_sense < 0`); ground
  contact is a crash for a plane and the point for a kinetic payload, and only
  the declared sense separates them. **There is no margin of zero** — at zero it
  is too late, which is a different state and the escape path answers there.
* **`attribution_price`** — prices staleness in the singleton open, because
  231 of 231 late exercises were landing on one member. Rotating the primary IS
  the composition variation the learners need, so it belongs in the cost rather
  than in a scheduler.
* **Surprise index** (`EmbodiedSurpriseShape`) — the residual quantised as a LOG
  bucket, `IDiv(Log(1 + |relative error|), quantum)`. Condensation collapses
  order 1 → order 0 after N unvarying encounters; release re-opens it when the
  response varies. Reflexes fire in the engine cycle (`fire_autonomous` in
  `cognitive_cycle::execute`), and their response is a rule reading the firing
  stamp, not a Python callable.

## The open thread, stated as a hypothesis and NOT built

The model fork keys on the **instantaneous** residual bucket, recomputed every
action from a noisy quantity, so model identity can flicker and the composer
switches between fork and parent — chatter exactly where a jammed effector makes
the residual erratic. That is the leading explanation for the fork's
`jammed_rudder` 0/3 → 2/3.

`stable_run` and condensation already say when a shape is ESTABLISHED rather
than merely current. **The fork should key on a condensed shape, not on this
action's bucket.** Not built, deliberately.

## Standing rules this line learned the hard way

1. **`P0` is `Plus(Attr, 0.0)` — the absence idiom for NUMBERS.** On a String it
   silently yields 0.0. Written three times in one day (reflex response
   signature, condensation comparison, fork token). `tests/test_fork_token_regression.py`
   now walks every rule's AST for it. **Read a String attr with `A`.**
2. **Deltas within ~3× the per-episode step are not results.** At n=3 per
   scenario, one episode is noise.
3. **Isolate before attributing.** Four blocks were read as "this change cost N
   episodes" when nothing had been isolated; a 2×2 then showed the rate owned
   the regression and credit was exactly neutral. Removing a suspected cause and
   re-measuring taught more than three additions did.
4. **A baseline is a codebase, not a number.** The 1/9 control was measured three
   minutes before two unmeasured changes landed, and every comparison for the
   next five blocks was drawn against code that no longer existed. It happened to
   survive; that was luck.
5. **Hysteresis is a sign you scaled wrong.** A budget suppressing a trigger that
   fires 93% of the time is hysteresis. Fix the scale, delete the budget.
6. **A fixed absolute constant against a multi-scale quantity is the recurring
   bug.** It appeared in the surprise ordinal (linear over 7 orders of
   magnitude), the margin (a linear ramp), and the recalibration trigger (a
   threshold below the signal's median). Ratios and log buckets, not constants.
7. **Assert on every anchored edit.** A `.replace()` with no assert silently
   no-oped and cost a run.
8. **Never `pkill -f`** on this host — the pattern matches the invoking shell.

## Reproduction

```
cd research/experiments/gamma-substrate
cargo build --release --manifest-path runners/dsl/Cargo.toml
cp runners/dsl/target/release/libsubstrate_rs.so \
   runners/dsl/python/substrate_rs/_native.abi3.so

# gates
PYTHONPATH=runners/dsl/python:. ../../../.venv-jsbsim/bin/python -m pytest \
  tests/test_margin_price_migrated.py tests/test_attribution_price_migrated.py \
  tests/test_regime_local_models_migrated.py tests/test_reflex_condensation_migrated.py -q

# the block (~25 min, 9 episodes)
PYTHONPATH=runners/dsl/python:. GAMMA_REGIME_DIAGNOSTICS=1 \
  ../../../.venv-jsbsim/bin/python scripts/jabberwock_jsbsim_f16_paper_replication.py \
  --scenarios damaged_wing saturated_elevator jammed_rudder --episodes 3 \
  --output /tmp/block.json
```

Probes: `probe_selection_attribution.py` (which path decides),
`probe_damaged_wing_descent.py` (trajectory + trigger scaling),
`probe_credit_assignment.py` (what the effector layer learns),
`probe_margin_price.py`, `probe_reflex_condensation.py`.

The full record is `docs/regime_pareto_frontier_results.md` (blocks CU–DG) and
`docs/regime_pareto_frontier_prereg.md`.

---

## Prompt

> Resume the F-16 fault-tolerant-control line in
> `research/experiments/gamma-substrate`. Read
> `docs/HANDOFF_embodied_adaptation.md` first, then blocks CU–DG of
> `docs/regime_pareto_frontier_results.md`.
>
> The tree is at 1/9 ground contact over three faults at three episodes — the
> control. Do not take a number as a result unless it clears ~3× the
> per-episode step, and do not compare against a baseline measured on different
> code.
>
> The open hypothesis is that the model fork keys on the instantaneous residual
> bucket and so flickers; it should key on a CONDENSED shape (`stable_run`),
> which the tree already computes. Measure before building: instrument how
> often the regime ordinal changes per action during `jammed_rudder`, and
> whether the composer's selected member changes with it. If the flicker is
> real, key the fork on the condensed shape and re-run the block against the
> 1/9 control. If it is not real, say so and stop — the last four blocks were
> plausible things built before they were measured.

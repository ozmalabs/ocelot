# held_self_worth from the real CAN self_worth belief — PREREG

**Task**: user, immediately after wiring `attribution_locus` as a residual:
*"wire held_self_worth into the real CAN self_worth belief."*
`ATTRIBUTION_LOCUS_AS_RESIDUAL_RESULTS.md` §3 named this explicitly:
`held_self_worth` was supplied data, not sourced from
`worlds/bigville_can_beliefs.py`'s real, live, per-resident CAN belief
network. This rung sources it for real.

## 1. What "real" means here, confirmed empirically before registering

`worlds/bigville_can_beliefs.py::build_resident_can_mt` mints a resident's
own `self_worth` Concept with `identity_field = 2*(prior_self_worth-0.5)`
(a fixed personality prior, `[-1,1]`) plus `causal_influence` couplings to
the other 4 CAN topics. `seeds/can_native_reimplementation.json`'s
`can_native_update_3state` rule then relaxes every Concept's `state`
(discrete, `{-1,0,+1}`) toward a stable basin under `run_rules()` — the
SAME discrete-asynchronous Hopfield-style update this whole CAN arc has
tested since `CAN_NATIVE_REIMPLEMENTATION_RESULTS.md`. Probed directly:

```
Confident (prior_self_worth=0.90, identity_field=0.800) -> converged state=1  in 5 steps
Insecure  (prior_self_worth=0.10, identity_field=-0.800) -> converged state=-1 in 5 steps
```

Two different personality draws converge to genuinely different, fast
(5-step) `self_worth` states. `state` is already on the exact `[-1,1]`-ish
scale (`{-1,0,+1}`) `SelfPattern.held_self_worth` already uses — no
rescaling needed.

## 2. Design

**A Python world-adapter function** (`domains/can_self_worth_bridge.py`),
NOT a graph rule change — CLAUDE.md's own architecture rule: sourcing WHERE
a value comes from is mechanical I/O; the DECISION that consumes it
(attribution-locus sign-agreement) is already the engine's, unchanged, in
`rule_dispute_self_conscious_bridge.json`. The function:

1. Builds a resident's real CAN Microtheory (`bcb.install_productions` +
   `bcb.build_resident_can_mt`), initializing `state`/`external_field` on
   every Concept (mirroring `test_can_native_reimplementation.py`'s own
   `_build_draw` convention exactly — `build_resident_can_mt` itself does
   not set these, confirmed by reading it directly).
2. Sets `discrete_mode="3state"`, `can_tick=0` on the Microtheory.
3. Calls `run_rules()` to relax to a stable basin.
4. Reads `self_worth`'s converged `state` back — this becomes
   `SelfPattern.held_self_worth` directly, no transformation.

**No seed is edited.** `can_native_reimplementation.json`,
`rule_dispute_escalation.json`, `self_conscious_emotions.json`, and
`rule_dispute_self_conscious_bridge.json` all stay exactly as they are —
this rung only changes WHERE the demo/test harnesses SOURCE
`held_self_worth` from, exactly as `HeldBelief.pred` was already sourced
from caller-supplied data before it.

## 3. Predictions

1. **Two residents with opposite `prior_self_worth` produce opposite
   converged `self_worth` states** (`+1` vs `-1`) via the REAL relaxation,
   not a hand-picked pair of scalars.
2. **End to end**: feeding each resident's REAL converged state through
   the unchanged dispute→self-conscious chain, for the IDENTICAL dispute,
   produces the theoretically-expected emotion split — the confident
   resident's failure contradicts their positive pattern → `guilt`; the
   insecure resident's SAME failure confirms their negative pattern →
   `shame`. The same qualitative claim `ATTRIBUTION_LOCUS_AS_RESIDUAL_
   RESULTS.md` already tested with hand-picked scalars, now tested with a
   real, ticking CAN network supplying the value.
3. **A resident whose CAN network relaxes to a neutral `state=0`** (an
   evenly-balanced prior/coupling draw) still counts as HAVING a pattern
   (a `SelfPattern` edge exists) — distinct from having NO pattern at all
   (the `circumstance` case) — and, per the existing sign-agreement rule
   (product with 0 is never `>0`), resolves to `specific_act`. Named
   honestly as an edge-case consequence of the existing rule, not
   re-designed here.

## 4. Scope boundaries

- Does not wire live evidence application (`apply_scenario_evidence`) or
  Hebbian growth into this bridge — a resident's `self_worth` reflects
  their STATIC personality-drawn prior relaxed against the OTHER 4 fixed
  topics, not an evolving history of many real interactions over time
  (that would require the resident's CAN network to persist and update
  across many real ticks, a genuinely separate, larger integration).
- `resolution_bins`/`arousal` and the other `_PARAM_SPEC` draws stay
  synthetic representative values for the demo/tests (the SAME honesty
  class as every prior rung's synthetic population), not real bigville
  cast100 residents — wiring an actual `bigville_cast100.json` resident
  through this bridge is a real, named, smaller follow-on.

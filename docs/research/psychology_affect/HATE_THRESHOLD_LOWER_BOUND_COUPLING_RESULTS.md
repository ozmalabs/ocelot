# Hate threshold lower-bound × arousal coupling — RESULTS

Registered design: `HATE_THRESHOLD_LOWER_BOUND_COUPLING_PREREG.md`. **All
4 predictions confirmed.** Building this rung surfaced and fixed a real
ordering bug in `record_hate_incident` — reported honestly in Sec3, not
smoothed over.

## 1. Live run (`scripts/hate_threshold_lower_bound_coupling_demo.py`)

```
=== Prediction 1: at zero arousal, the gate matches the base constant ===
streak=2.9 (below base 3): crystallized=False
streak=3.0 (== base 3): crystallized=True

=== Prediction 2: elevated arousal crystallizes a streak that stays cold at zero arousal ===
cold (arousal=0): streak=2.0 crystallized=False
hot (arousal=1.0, effective_threshold=1.50): streak=2.0 crystallized=True

=== Prediction 3: both couplings crystallize sooner than the increment coupling alone ===
live engine (both couplings): crystallized after 2 incidents
simulated, both couplings: 2 incidents
simulated, increment coupling ALONE (fixed base threshold): 3 incidents

=== Prediction 4: per-target isolation ===
Alex (arousal=2.0, effective_threshold=1.0): streak=1.5 crystallized=True
Sam (own arousal=0, same streak=1.5): crystallized=False
```

## 2. Predictions

1. **At zero arousal, `effective_threshold` equals the base constant** —
   `PASS`. `streak=2.9` stays uncrystallized, `streak=3.0` crystallizes —
   identical to the pre-this-rung behavior, exact boundary.
2. **Elevated arousal lowers `effective_threshold` below the base
   constant** — `PASS`. The IDENTICAL `streak=2.0` (which would need
   `>=3.0` to crystallize cold) crystallizes once arousal reaches `1.0`
   (`effective_threshold=1.5`), holding the streak value fixed to
   isolate this rung's own effect from the already-landed increment
   coupling.
3. **Compounding, measured honestly** — `PASS`. With BOTH couplings
   active, the live engine crystallizes after **2** incidents; a
   pure-arithmetic simulation of the SAME recurrence but comparing
   against the FIXED base threshold (increment coupling alone) needs
   **3** — and the live engine's own count matches the "both couplings"
   simulation exactly, cross-validating the simulation baseline used for
   the comparison rather than asserting it blind.
4. **Per-target isolation holds** — `PASS`. Alex's arousal-lowered gate
   (`effective_threshold=1.0`) crystallizes at `streak=1.5`; Sam, holding
   the SAME `streak=1.5` but Sam's own zero arousal, does not — Alex's
   arousal never leaks into Sam's own gate.

## 3. A real bug found and fixed before finalizing

Landing this rung's `effective_threshold` Term initially broke 3 of the
existing hate tests in a way that was NOT the expected "crystallizes
sooner" ripple this arc has now seen twice (`HATE_STABILITY_AROUSAL_
COUPLING_RESULTS.md` Sec3) — instead, a "cold" test run (arousal
manually decayed toward zero between incidents, to isolate the
increment coupling from this rung's effect) showed `confirm_streak`
climbing PAST the base threshold (`3.0019` at incident 3) while
`crystallized` stayed `False` for that call, only flipping `True` on a
LATER, unrelated call — a genuine detection bug, not a design
consequence.

**Root cause**: `record_hate_incident` updated `TargetArousal.level`
(the "update after" half of the read-before/update-after convention)
*before* its own SECOND `force_all_dirty()`+`run_rules()` call (needed
to relax the `regard_for`/`removal_desire_for` evidence just applied).
Once `crystallize_hate`'s gate itself depended on `arousal.level`, that
second `run_rules()` call could re-fire `crystallize_hate` using THIS
incident's own freshly-bumped arousal instead of the pre-incident value
every coupling in this arc reads by design — and because
`crystallized_this_call` was computed from a `has_hate`-edge-count
snapshot taken BETWEEN the two `run_rules()` calls, a crystallization
that happened to land in the second pass was silently missed by the
return value while still being visible on the next call's
`pat_attrs["crystallized"]` read.

**Fixed** by moving the arousal update to strictly AFTER both
`run_rules()` calls for the incident have completed — `crystallize_hate`
now only ever evaluates using genuinely pre-incident arousal, in a
single pass, matching every other coupling's own read-before/update-
after convention exactly. This was a real latent bug in the PRIOR
(`v1.2.0`) rung too — it happened not to manifest there because a fixed
`Lit(3)` threshold never depended on `arousal.level`, so the second
`run_rules()` pass had nothing new to re-trigger `crystallize_hate` with.
It surfaced only once THIS rung made the gate itself arousal-dependent.

## 4. Honesty notes

**Does establish**: hate crystallization now has TWO independent,
additive channels by which Sternberg's passion accelerates it — a
faster-climbing streak (`v1.2.0`) and a lower bar to clear (`v1.3.0`) —
both grounded in the same Slovic et al. 2007 affect-heuristic citation's
two distinct claims, measured to compound rather than merely coexist
(2 incidents vs 3, cross-validated between live engine and independent
simulation). Also surfaced and fixed a real ordering bug in the shared
read-before/update-after convention this whole arc depends on, which had
been silently latent in the previous rung.

**Does NOT establish**: the `1/(1+level)` functional form of the
threshold-lowering against real psychological data beyond the citation's
structural claim — an un-fitted functional shape, same honesty class as
every other coupling here. Does NOT change `HATE_STABILITY_THRESHOLD`'s
role as the documented AT-REST constant. Does NOT touch `specific_act`'s
reset behavior.

## 5. Files

- `docs/research/psychology_affect/HATE_THRESHOLD_LOWER_BOUND_COUPLING_PREREG.md`
- `docs/research/psychology_affect/HATE_THRESHOLD_LOWER_BOUND_COUPLING_RESULTS.md` (this file)
- `domains/hate_attribution.py` (edited: moved the arousal update to after both run_rules() calls -- bug fix)
- `scripts/_build_hate_attribution_seed.py` (edited: `_effective_threshold_term`, `DivT`, v1.3.0)
- `seeds/hate_attribution.json` (regenerated)
- `scripts/hate_threshold_lower_bound_coupling_demo.py` (new)
- `tests/test_hate_threshold_lower_bound_coupling.py` (5/5, new)
- `tests/test_hate_attribution.py` (1 test renamed/rewritten to check the effective threshold instead of the bare constant; 9/9 still green)

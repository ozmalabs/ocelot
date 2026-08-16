# Persistent held_self_worth — RESULTS

Registered design: `PERSISTENT_SELF_WORTH_PREREG.md`. Built:
`find_or_build_resident_can` + `record_incident_outcome` in
`domains/can_self_worth_bridge.py`, demonstrated by
`scripts/persistent_self_worth_demo.py`, regressed by
`tests/test_persistent_self_worth.py` (8/8 green). No seed edited
(git-status-gated test across all four seeds this arc has touched).

## 1. What this answers

User: *"make it properly persistent."* The prior rung relaxed a resident's
CAN `self_worth` from a static prior ONCE per call, fresh — no belief
carried forward across repeated incidents. This rung makes it a genuinely
history-accumulating belief: a resident's real network is reused (not
rebuilt) across appraisals, and each self-attributed episode feeds back as
`concept_apply_evidence`, letting the belief drift — and even flip basins —
from accumulated experience.

## 2. A real engine gotcha, found live, before registering

`concept_apply_evidence` writes `external_field` OUTSIDE the rule-effect
path. Probed directly: applying it — even at a massive, unambiguous
magnitude (`alpha=5.0`) — and immediately calling `run_rules()` reported
`steps=0` and left `state` completely unchanged. Confirmed the underlying
mechanism was correct (forcing `state` away from its stable value via
`set_attr` before re-running correctly re-converged in 3 steps) — the real
cause was `run_rules()`'s incremental dirty-tracking never re-examining a
Concept whose only change came from a raw PyO3 attribute write, not a rule
effect. Fix: `inner.force_all_dirty()` immediately before every
evidence-then-relax call. **This would have been a silent, permanent no-op
in production** — every incident "recorded" would have done nothing,
forever, with no error — had it not been checked directly before writing
any code that depended on it.

## 3. Predictions — all 5 registered, all 5 held

```
PREDICTION 1: force_all_dirty() is necessary
massive evidence applied, run_rules() WITHOUT force_all_dirty(): steps=0 state=1 (the gotcha)
SAME evidence, NOW with force_all_dirty():                        steps=3 state=-1

PREDICTION 2: repeated incidents flip a resident's basin
incident 1-3 (standard_met=False, global_self): self_worth=1  (unmoved)
incident 4:                                     self_worth=0  (neutral)
incident 6-7:                                   self_worth=-1 (flipped)

PREDICTION 3: a circumstance-attributed incident does NOT move it
self_worth before 5 circumstance-attributed incidents: 1
self_worth after:                                      1  (unchanged)

PREDICTION 4: the SAME resident, appraised twice, persists
is_new on second lookup: False
same node: True

PREDICTION 5: drift changes a LATER, otherwise identical dispute's outcome
before any incidents:        self_worth=1  -> guilt
after 6 repeated failures:   self_worth=-1 -> shame
```

1. **`force_all_dirty()` is necessary** — regression-tested directly
   (`test_evidence_without_force_all_dirty_is_a_silent_noop`), so a future
   refactor that drops the call breaks a named test instead of silently
   reintroducing the gotcha.
2. **Repeated confirming incidents flip a resident's basin** — a
   `Confident` resident does NOT flip on the first incident alone (real,
   not instant overreaction); flips by the 6th-7th of repeated
   `standard_met=False`/`global_self` incidents.
3. **Circumstance-attributed incidents never move `self_worth`** —
   confirmed across 5/10 repeated circumstance incidents in the demo/test:
   the theoretical gate (Lewis 1971; Miller 1996: an outcome not attributed
   to the self shouldn't move the self-concept) is load-bearing, not
   decorative — genuinely tested by trying hard to move it and failing.
4. **The same resident reuses their drifted network** — a second
   `find_or_build_resident_can` call returns `is_new=False` and the
   IDENTICAL `self_worth` Concept node, carrying the drift forward. A
   genuinely new resident name still builds fresh
   (`test_a_genuinely_new_resident_name_builds_fresh`).
5. **End to end**: the IDENTICAL later dispute (same severity, band,
   witnesses) reads the SAME resident's CURRENT (now-drifted) `self_worth`
   and produces a DIFFERENT emotion than it would have before the
   incidents — `guilt` before, `shame` after 6 repeated failures. This is
   the actual point of persistence: identity genuinely accumulates and
   changes future appraisals, not just a per-call snapshot.

No null. Every registered prediction held.

## 4. Honesty notes

**Does establish**: a resident's self-conscious appraisal is now
genuinely stateful across repeated incidents on one live substrate, with
the theoretically-motivated circumstance-gate empirically confirmed
load-bearing, and a real, previously-silent engine defect found and fixed
before it could corrupt anything downstream.

**Does NOT establish**: persistence across process restarts / disk
serialization — "persistent" here means across multiple calls on the SAME
live substrate (PREREG Sec4), matching how the real agent's own substrate
is meant to be long-running, not a new save/load mechanism. The specific
`alpha=0.3` learning rate and the 6-7-incident flip threshold are measured
facts about THIS resident's particular coupling structure
(`identity_field=0.8`, one `+0.6`-weighted neighbour), not a general claim
about how quickly any resident's identity should shift. Whether a REAL
`bigville_cast100.json` resident population shows a meaningfully varied
distribution of flip-thresholds — not tested, a real, smaller, named
follow-on (carried over from `HELD_SELF_WORTH_FROM_CAN_RESULTS.md`).

## 5. Files

- `docs/research/psychology_affect/PERSISTENT_SELF_WORTH_PREREG.md`
- `docs/research/psychology_affect/PERSISTENT_SELF_WORTH_RESULTS.md` (this file)
- `domains/can_self_worth_bridge.py` (extended: `find_or_build_resident_can`, `record_incident_outcome`)
- `scripts/persistent_self_worth_demo.py`
- `tests/test_persistent_self_worth.py` (8/8)

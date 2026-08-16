# Envy — PREREG

**Task**: Phase F of the expanded emotional+preference system build plan
(`/home/matt/.claude/plans/distributed-frolicking-waterfall.md`) —
extends `relative_self_worth` (`RELATIVE_SELF_WORTH_PREREG.md`, already
built: `peer_log_odds = ln((confirm+1)/(disconfirm+1))`, `relative_
self_worth = domain_state - peer_log_odds`) with the ONE component it
was always missing for envy specifically: whether the disparity feels
DESERVED.

## 1. Theoretical grounding

- **Smith & Kim (2007), "Comparative Envy," a review in *Psychological
  Bulletin*** — envy requires upward social comparison (already built:
  a negative `relative_self_worth` IS exactly "I am worse off than my
  reference group") PLUS an appraisal of whether the advantage is
  deserved. Comparison alone does not determine hostility.
- **Van de Ven, Zeelenberg & Pieters (2009), "Leveling Up and Down: The
  Experiences of Benign and Malicious Envy," *Emotion*** — the standard
  citation for the split this rung implements directly: BENIGN envy
  (the disparity is seen as deserved/legitimate — motivates self-
  improvement, no hostility toward the advantaged party) versus
  MALICIOUS envy (the disparity is seen as undeserved/unfair — motivates
  hostility, wanting the other's advantage diminished). The SAME upward
  comparison produces qualitatively different outcomes depending purely
  on this ONE appraisal.

## 2. Design

**Reuses `relative_self_worth` entirely, unchanged** — no new
comparison mechanism. `read_relative_self_worth` (`domains/can_self_
worth_bridge.py`, already built and tested) supplies the upward-
comparison half directly.

**One new, domain-scoped, fresh/uncoupled CAN belief** (mirrors `self_
efficacy_for`'s own shape — a resident's OWN appraisal, not a ToM belief
about a specific other, since "is this disparity fair" is a judgment
about the SITUATION, not about one target's mind):

```
deservingness_belief_for:<domain>   -- do I believe my peers' relative advantage here is fair
record_deservingness_incident(concept, deserved: bool, alpha=0.3)   -- flat evidence, same shape as every belief update in this arc
```

**`read_envy` is a PURE classification function** over two already-
computed floats — no graph access, no new accumulator:

```
read_envy(relative_self_worth, deservingness_value):
    relative_self_worth >= 0                                  -> "none"      (no disadvantage, nothing to envy)
    relative_self_worth <  0  AND  deservingness_value >= 0    -> "benign"    (disadvantaged, but the gap is seen as fair)
    relative_self_worth <  0  AND  deservingness_value <  0    -> "malicious" (disadvantaged AND the gap is seen as unfair)
```

## 3. Predictions

1. **No disadvantage means no envy** — `relative_self_worth >= 0`
   returns `"none"` REGARDLESS of the deservingness belief's value.
2. **A deserved disadvantage produces benign envy** — `relative_self_
   worth < 0` with a non-negative deservingness belief returns
   `"benign"`.
3. **An undeserved disadvantage produces malicious envy** — the SAME
   negative `relative_self_worth` with a negative deservingness belief
   returns `"malicious"`.
4. **The deservingness belief is the ONLY thing that changes the
   verdict** — holding `relative_self_worth` FIXED at the same negative
   value, flipping only the deservingness belief flips `"benign"` to
   `"malicious"` — isolating the injustice appraisal's own causal role,
   the central claim of Van de Ven et al.'s split.
5. **Domain isolation** — a deservingness belief accumulated in one
   domain does not affect a different domain's own reading.

## 4. Scope boundaries

- Does not build any downstream consequence Concept (a hostility-toward-
  the-advantaged-peer motivation for malicious envy, a self-improvement
  motivation for benign envy) — `read_envy`'s classification IS this
  rung's full scope; a consequence layer is a real, named, deferred
  follow-on (the same shape `SELF_CONSCIOUS_CONSEQUENCE_PREREG.md`
  eventually built for shame/guilt, not attempted here).
- `deservingness_belief_for` is domain-scoped, not peer-target-scoped —
  a genuine design choice (the appraisal is about the SITUATION's
  fairness, not a ToM belief about one specific peer's mind); a
  target-specific variant is a real, separate, un-built refinement.
- The `>=0`/`<0` boundaries are documented, un-fitted thresholds, same
  honesty class as every other boundary in this arc.

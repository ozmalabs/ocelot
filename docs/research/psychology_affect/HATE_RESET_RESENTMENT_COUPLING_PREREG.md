# Hate reset × arousal coupling (resentment) — PREREG

**Task**: user, immediately after `HATE_THRESHOLD_LOWER_BOUND_COUPLING_
RESULTS.md` landed: *"couple the confirm_streak reset on specific_act to
arousal too - also what about resentment."* The reset was explicitly
scoped OUT of every prior rung (`HATE_STABILITY_AROUSAL_COUPLING_PREREG.md`
Sec4: *"`specific_act`'s full reset to 0 is UNCHANGED... this rung does
not soften that reset"*; `HATE_THRESHOLD_LOWER_BOUND_COUPLING_PREREG.md`
Sec4, same line). This document builds exactly that, and answers the
second half directly: **resentment is what this coupling produces.**

## 0. What resentment is, and why this mechanism is the answer

Resentment is the everyday case a full reset cannot represent: a person
does something genuinely kind (a `specific_act`, disconfirming the
pattern), and the aggrieved party does not actually forgive — some of the
grievance persists anyway. A hard reset to `0` (every prior rung's
behavior) cannot produce that residue at all; it says every exception is
processed with equal, complete credit regardless of emotional state at
the time. **Resentment is precisely the case where that credit is
discounted** — the exception happened, but it did not fully clear the
account, because the discounting itself is arousal-dependent. This rung
makes THAT the mechanism, not a separate subsystem: no new `Resentment`
node is minted; the observable IS `confirm_streak`'s own residual value
immediately after a `specific_act`, which this design makes non-zero
exactly when arousal was elevated at the moment of the exception.

## 1. Theoretical grounding

- **Bodenhausen (1993), "Emotion, Arousal, and Stereotypic Judgment: A
  Heuristic Model of Affect and Stereotyping"** — angry/aroused
  individuals process disconfirming information more heuristically,
  giving it LESS weight against an already-held judgment than they would
  cold. This is the SAME affect-heuristic family already cited for the
  increment and threshold couplings (Slovic et al. 2007), applied here to
  its natural third consequence: arousal doesn't just make confirmations
  count for more and lower the bar to commit — it also makes
  DISCONFIRMATIONS count for LESS.
- **This IS resentment's structure**, not an analogy to it: a grievance
  that persists despite an act that should have resolved it, because the
  act was discounted under the SAME emotional state the grievance itself
  produced — a self-reinforcing loop (arousal from the pattern discounts
  the evidence that would break the pattern), which is exactly the
  everyday, folk-psychological shape of resentment as distinct from
  ordinary forgiveness.

## 2. Design

**The base case (`level==0`) is an EXACT full reset, unchanged** — this
rung is a strict generalization, not a redefinition, matching the same
backward-compatibility property every prior coupling in this arc has:

```
retained_fraction = arousal_level / (1 + arousal_level)   [READ, same point every other coupling reads at -- current, pre-this-incident arousal]
new_confirm_streak = IfThenElse(locus == global_other,
                                 confirm_streak + streak_increment,       [unchanged, v1.2.0]
                                 confirm_streak * retained_fraction)      [NEW -- was Lit(0)]
```

At `level==0`, `retained_fraction == 0`, so `confirm_streak * 0 == 0` —
byte-identical to the pre-this-rung hard reset. No new constant: reuses
the SAME `X/(1+X)` shape family `HATE_THRESHOLD_LOWER_BOUND_COUPLING_
PREREG.md`'s own formula already established, applied to the SAME
`arousal_level` read `derive_hate_attribution` already performs for the
increment term — one more Term inside the SAME rule, zero new Rust, zero
new Python decisions, zero new constants.

## 3. Predictions

1. **At zero arousal, `specific_act` still fully resets `confirm_streak`
   to `0`** — backward compatibility.
2. **At elevated arousal, `specific_act` leaves a strictly positive
   residue** — the resentment case: `confirm_streak` after the exception
   is `> 0` given a nonzero pre-exception streak.
3. **The residue matches the formula exactly**:
   `new_streak == old_streak * (level/(1+level))`.
4. **A resented (partially-forgiven) pattern's `confirm_streak` stays
   strictly ahead of a fully-forgiven (cold-reset) one at a matched
   number of subsequent confirming incidents** — the behavioral trace of
   the residue: from the SAME pre-exception streak, an aroused
   (resented) exception followed by one resumed confirming incident
   leaves a measurably higher `confirm_streak` than a cold (genuinely
   forgiven) exception followed by the identical confirming incident.
   (Checked empirically, not merely asserted: with this arc's already-
   landed increment and threshold-lowering couplings compounding as
   aggressively as they now do, the residue's marginal effect on the
   INTEGER incident count needed to cross the gate is often invisible —
   both paths can cross on the very next confirmation regardless of the
   residue, because post-exception arousal alone, from `AROUSAL_
   INTENSITY` applied unconditionally every incident, is frequently
   already enough. The residue's effect on the streak VALUE itself,
   which this prediction measures instead, is the claim that survives
   that compounding.)
5. **Per-target isolation holds** — target A's arousal-dampened reset
   does not affect target B's own reset.

## 4. Scope boundaries

- Does not mint a new `Resentment` node or Concept — the residue IS
  `confirm_streak`'s own post-exception value; adding a separate marker
  would duplicate state this rung already exposes directly.
- Does not change `global_other`'s own increment formula (`v1.2.0`,
  unchanged) or the crystallization gate's own threshold-lowering
  (`v1.3.0`, unchanged) — purely the reset branch.
- Does not model active forgiveness-seeking, apology, or repair dynamics
  — only the passive discount-under-arousal effect on how much credit one
  disconfirming act receives.

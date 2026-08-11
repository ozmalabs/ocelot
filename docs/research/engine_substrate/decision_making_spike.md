# How to make good decisions — a research spike

**Status: SPIKE. No code, no seeds, no runs in this document.** Prompted after
block J, by the measurement that four different scoring conventions each
produced a CONSTANT winner. Confidence is flagged throughout; works cited from
knowledge and **not re-verified against primary sources in this spike** are
marked `[unverified]`.

---

## 1. The problem, stated from measurement rather than from taste

The F-16 regime layer compares a FIXED set of five alternatives on a FIXED set
of six axes. Measured consequences, all in
`docs/regime_pareto_frontier_results.md`:

| pricing convention | winner | jam outcome |
|---|---|---|
| v3 ladder (no frontier) | orbit | 0.04 crash, n=100 — **standing best** |
| surrendered axis = flat 0.0 | roll priority 91/100 | 0.65 crash, n=100 |
| surrendered axis = the horizon | orbit 48 of 48 | 3 crashes / 25 |
| surrendered axis = the ledger | roll/speed 13 of 13 | 8 crashes / 25 |

Plus two structural facts, read off the graph rather than inferred:

* **Four of the six declared axes never vary between candidates.** speed,
  attitude, structural and sideslip are pinned at the ceiling for every
  candidate at every close.
* **No corner-minting rule reads the plant model.** All five match only the
  episode and the profile — not `log_authority`, not
  `recalibration_required`, not the fault.

**The generalisation: scoring a fixed menu cannot produce situational
selection.** The convention picks the winner; the situation does not. This is
not an F-16 fact — it follows from the shape of the operation.

---

## 2. What this tree already holds (checked before looking outward)

**`BIGVILLE_ADMISSIBILITY_GRAMMAR.md` contains the same reframe, in another
domain, and it was reached the same way.** Its diagnosis: violence had become
"a richly-modelled behaviour, fired by rules that bypass the admissibility
checker entirely," when it should be "an **inadmissibility** — the rare, marked
residual that appears when the norm-grammar fails to admit an act. Admissible
conduct is what Γ *generates by default*."

Transposed: **regime corners should be what an admissibility grammar GENERATES
from the current model, and an unavailable corner should be a residual rather
than a menu item that always loses.** The substrate already carries Γ and a
meta-grammar over it (`CLAUDE.md`, the Γ_meta section).

**`docs/embodied_pareto_profiles.md` already forbids what went wrong**, in its
own words: *"A separate context-sensitive policy can choose among frontier
members; that choice must remain explicit and must not be smuggled into the
Pareto substrate as a scalar score."* The F-16 obeys the letter — the policy is
explicit, `regime_policy_priority_axis_ordinal` — and loses the substance,
because dominance runs first and leaves exactly one survivor for the policy to
"choose" among.

**The single most important thing found in this spike is in the code, not the
literature.** `f16_choose_regime_situational_priority` already picks the
priority axis from LIVE SITUATIONAL CUES — terrain proximity below 500 m
favours altitude, airspeed below 70 m/s favours speed, otherwise heading — and
it demonstrably varies within a single episode (measured: axis 1 at three
deliberations, axis 0 at two, same flight). **The situational discriminator
exists, it responds to the aircraft, and it is structurally unable to decide
anything**, because `best = Argmax(non-dominated candidates, priority value)`
and dominance has already reduced the set to one.

---

## 3. What the decision literatures converge on

The convergence is sharper than expected, and it is not "score better".

### 3.1 Expert decisions are GENERATED, not compared

**Gary Klein, *Sources of Power: How People Make Decisions* (MIT Press, 1998)**
— recognition-primed decision. Studying fireground commanders, Klein found
experts typically do **not** generate and compare options. They recognise the
situation as typical, retrieve ONE workable course of action, mentally simulate
it, and act; comparison appears mainly in novices and in unfamiliar
situations. Consensus within naturalistic decision making; contested as a
normative claim. `[unverified]` for specific study proportions.

**Relevance:** the architecture spends its entire deliberation on the operation
Klein's experts skip, and none on the one they rely on — recognising which
situation this is and generating the response that fits it.

### 3.2 Weighted/multi-attribute comparison is fragile exactly where we broke

**Herbert Simon, "A Behavioral Model of Rational Choice" (QJE, 1955)** —
satisficing: take the first alternative above an aspiration level. Generation
ORDER carries the decision; comparison is minimal.

**Gerd Gigerenzer & Daniel Goldstein, "Reasoning the Fast and Frugal Way"
(Psychological Review, 1996)** — "take the best": order cues by validity, decide
on the FIRST cue that discriminates, ignore the rest. Lexicographic, not
weighted. Their claim, and the contested part, is that this matches or beats
regression-style integration under uncertainty because it does not have to
estimate weights. Consensus: such heuristics are competitive. Contested: how
general the advantage is.

**Relevance, and it is direct:** this line has now measured four times that the
weights determine the answer. Take-the-best says: **stop estimating weights;
decide on the one cue that discriminates in THIS situation.** The seed already
computes which cue that is.

### 3.3 The right object may be a SET, not a score

**Jean-Pierre Aubin, *Viability Theory* (Birkhäuser, 1991)** — the viability
kernel: the set of states from which the constraints can be satisfied forever
under some admissible control. You do not score states; you stay in the kernel.
Consensus in control theory. `[unverified]` for edition details.

**Control barrier functions** (e.g. Ames et al., ECC 2019 survey `[unverified]`)
— the modern constructive cousin: encode the safe set as a constraint on
admissible actions rather than as an objective to be traded off.

**Relevance:** "does the fixpoint remain attainable" IS a viability question,
and this line has been answering it with a scalar clock and then trading that
clock against five others. **The available option set is the kernel of the
current model** — which is exactly the owner's *"if the operating model changes,
the available options must change too."* Viability theory is that sentence,
formalised, and it makes availability primary and cost secondary.

### 3.4 Valuing a state by the options it leaves

**Klyubin, Polani & Nehaniv, "All Else Being Equal Be Empowered" (ECAL, 2005)
`[unverified]` on venue** — empowerment: the channel capacity from an agent's
actions to its own future sensor states. A principled scalar for "how many
futures can I still reach", requiring no per-axis conventions.

**Wissner-Gross & Freer, "Causal Entropic Forces" (Phys. Rev. Lett., 2013)** —
a related formalisation of behaviour that maximises future freedom of action.

**Dixit & Pindyck, *Investment under Uncertainty* (Princeton, 1994)** — real
options: an irreversible commitment has an option value that naive NPV misses.

**Relevance:** this line DERIVED the same idea independently (item 10: *"more
energy is more options"*; T_option; the reserve) and then implemented it as one
axis among six. Empowerment says it is not an axis — it is the value function.
The two-column ledger is a domain-specific empowerment measure.

### 3.5 Honest counterweight

Pareto/multi-objective methods are not wrong in general; they are the right tool
when objectives are genuinely incommensurable AND the alternative set is given
exogenously. **Both preconditions fail here**: the ledger made the objectives
commensurable (that was the point of blocks C/D/F), and the alternative set is
ours to generate. Also, RPD and take-the-best are descriptive claims about human
experts; treating them as normative for an aircraft controller is a leap, and
the leap should be stated rather than hidden.

---

## 4. What this implies, ordered by cost

**(a) CHEAPEST, and testable immediately — make the situational cue decide.**
Invert the order: let the declared priority axis select, and use dominance only
to exclude candidates that are worse on THAT axis. This is take-the-best with
the cue this seed already computes from live state. It requires no new
quantities, no new corners, and no model plumbing. **It is the direct test of
"the situation cannot reach the decision", and it should produce situational
selection immediately or falsify the diagnosis.**

**(b) The owner's move — generate the option set from the model.** Corner
minting reads the effector models: a corner is minted only where the authority
it requires still exists, and corners that a changed model makes newly sensible
become available. This is the admissibility-grammar reframe already adjudicated
for bigville, and it is the one that makes an option set respond to a damaged
wing.

**(c) The deeper reframe — value states by remaining options.** Replace the
six-axis score with an empowerment-like reading of the ledger: choose the corner
that leaves the largest reachable set. This line already has the ledger, the
reserve and the option clock; what it lacks is using them as the objective
rather than as one axis.

**Sequencing note against this line's own history:** (a) is a hypothesis test,
not a fix, and it should be run as one. (b) is the substantive build. (c) is a
research direction and should not be started before (b) has shown that varying
the option set changes anything.

---

## 5. The first experiment, and how it would be falsified

**Claim to test:** the frontier fails to select situationally because dominance
consumes the decision before the situational cue is consulted — not because the
cue is uninformative.

**Test:** reorder selection so the situational priority axis is the primary
discriminator (take-the-best), leaving the corner set, the axes and the pricing
untouched. Run the block-H protocol (4 scenarios x 25 frozen seeds, gate off)
so it is directly comparable to blocks H and J.

**Prediction, to be committed before running:** more than one regime ordinal is
adopted across the block, AND which ordinal is adopted depends on the scenario
— specifically, terrain-proximity episodes select differently from
low-airspeed episodes.

**What would falsify it:** a single ordinal again (the cue is present but not
discriminating, so the problem is the corner set alone and (b) is the only
route); or selection that varies randomly rather than with the cue.

**Named in advance as the most likely failure:** the cue is coarse — two
thresholds, 500 m and 70 m/s — so in a 100 s episode starting at ~2,100 m it
may read "heading" almost throughout, in which case it is constant for a
DIFFERENT reason and the test is inconclusive rather than negative. **That
should be measured first, from the traces that already exist, before the block
is run.**

---

## 6. The pre-check the spike demanded, run before the experiment

Section 5 named the most likely failure as the cue being coarse enough to be
constant in practice. **Measured on block H's existing traces, at the actions
where a deliberation is open — it is not.**

| scenario | priority axis share | episodes whose cue VARIES within the flight |
|---|---|---|
| nominal | heading 1.00 | 0 of 17 |
| jammed_rudder | heading .61, altitude .38, speed .01 | **19 of 25** |
| saturated_elevator | heading .80, altitude .20 | 5 of 25 |
| damaged_wing | **altitude .49**, heading .45, speed .06 | **25 of 25** |

Pooled: heading 0.639, altitude 0.339, speed 0.022.

**The cue is informative, it differs BETWEEN scenarios, and it changes WITHIN
the flight in 49 of 75 fault episodes** — every damaged-wing episode without
exception. Nominal reads the default throughout, which is correct and also
harmless, since healthy flight never reaches a verdict.

So the named failure does not hold and the experiment is worth running. It also
sharpens the diagnosis one further turn: this is not a system that lacks a
situational signal, nor one whose signal is too coarse to discriminate. **It is
a system that computes a good situational signal, updates it live, and then
throws it away** — because dominance over a fixed menu has already reduced the
frontier to one candidate before the signal is consulted.

---

## 7. Measuring the model before writing the availability predicate

The option-set build needs a signal that moves when the plant changes.  Probed
on live episodes (one per scenario, effector models read off the episode at
action 999).

**A correction first.**  An earlier reading of this probe reported the learned
models as byte-identical across scenarios.  That was wrong: the snapshot being
compared was the PRE-FAULT one (action 99) in all three scenarios, where
identity is expected and uninformative.  The post-fault models differ
substantially.  The claim "System 1 already adapts to the changed plant" made
before this measurement was therefore asserted, not measured; it is measured
now, and it holds.

**What moves.**  Mean |learned effect| per actuator group at action 999:

| group | roll (nominal → wing) | prior confidence |
|---|---|---|
| elevator | 0.0000 → 0.0549 | 0.995 → 0.995 |
| **aileron** | **0.2778 → 0.0457** | 0.995 → 0.995 |
| rudder | 0.0000 → 0.0426 | **0.995 → 0.000** |
| throttle | 0.0000 → 0.0556 | 0.995 → 0.995 |

**The signal is in the ORDERING, not the magnitude.**  The aileron's learned
roll effect against its own command level:

| command | −1.0 | −0.8 | −0.5 | −0.2 | 0.0 | +0.2 | +0.5 | +0.8 | +1.0 |
|---|---|---|---|---|---|---|---|---|---|
| nominal | −.500 | −.375 | −.250 | −.125 | .000 | .125 | .250 | .375 | .500 |
| damaged wing | −.039 | .004 | .019 | .049 | .060 | **.062** | **.058** | **.047** | .074 |

Nominal is a perfect ordering.  Under a damaged wing the aileron's roll effect
**stops being monotone in its own command** — it rises, then falls at +0.5 and
+0.8.  The surface still moves; it no longer orders the outcome.

**So the availability predicate is monotonicity, and it needs no constant:** a
corner requiring consequence C is admissible iff some effector's learned effect
on C is still order-preserving in that effector's own command level.  Zero
inversions is the line; zero is the lattice origin, not a picked threshold.
Magnitude comparisons were tried first and all of them needed one — and the
cross-talk terms (lateral 0.000 → 2.84, vertical 0.000 → 1.76) swamp any
magnitude test, which would make every corner inadmissible under a severe
fault.

**A defect found en route, not yet filed as a fix.**
`f16_retire_jammed_rudder_specification_prior` retires the RUDDER's prior under
a **damaged wing** (confidence 0.995 → 0.000 in the table above).  Its guard is
`fault_recalibration_enabled AND fault_recalibration_armed AND actuator_group ==
2 AND prior_confidence > 0.5` — armed by ANY scheduled fault, not by a rudder
fault.  So every scenario in this protocol retires the rudder's prior at fault
onset.  Whether that has helped or hurt is unmeasured; it has been true for
every block in this line.

---

## 8. The monotonicity predicate, PROJECTED before it was built — and falsified

The block traces carry no per-effector learned means (`tokens`, `groups`,
`member_count`, and the regime contract, but no `mean_<consequence>`), so the
projection was run as a probe over live episodes — 4 scenarios x 5 frozen
seeds, evaluating the predicate at every deliberation opening **without gating
anything on it**.  75 openings.

**Fraction of openings at which each corner would be ADMISSIBLE:**

| scenario | openings | trim (lateral) | orbit (turn) | speed_priority (forward) | roll_priority (roll) |
|---|---:|---|---|---|---|
| nominal | 4 | **0.00** | 1.00 | 1.00 | 1.00 |
| jammed_rudder | 17 | 0.18 | 0.00 | 0.82 | 0.00 |
| saturated_elevator | 25 | 0.40 | 0.00 | 0.00 | 0.00 |
| damaged_wing | 29 | 0.38 | 0.28 | 0.28 | 0.03 |

**Which group is credited with each consequence, pooled over all 75 openings:**

| consequence | credited to |
|---|---|
| lateral | none 51, **rudder 24**, aileron 1 |
| turn | none 63, rudder 9, aileron 4 |
| forward | none 49, **rudder 16, aileron 12**, throttle 5 |
| roll | none 70, aileron 4, rudder 1 |

**The predicate is wrong, and the projection says so in two independent ways:**

1. **It removes `trim` in NOMINAL (0.00) and restores it under fault.**  A
   healthy aircraft can obviously trim sideslip.  The reason it fails is that
   in healthy flight the rudder's learned lateral effect is flat at ~0 — there
   is no sideslip to correlate with — so it is not STRICTLY monotone.  The test
   is behaving exactly as specified and the specification is wrong.
2. **The ailerons are credited with `forward` authority (12 openings) more
   often than the throttle (5).**  That is not an ordering of authority, it is
   an ordering of whatever the aircraft happened to be doing.

**The root cause, stated generally: `mean_<consequence>` is an OBSERVATIONAL
correlation between an effector's command and an outcome, and authority is an
INTERVENTIONAL quantity.**  In calm flight the true effector's effect is flat
and reads as no authority; under a fault, spurious correlations become monotone
and read as authority.  Monotonicity was the right shape of test — ordinal,
constant-free — applied to the wrong quantity.  Every magnitude-based variant
fails for the same underlying reason and additionally needs a threshold.

## 9. What this means for the option-set build

**There is currently no non-oracle signal in this system that says an effector
has lost authority.**

* The learned consequence means are observational, per section 8.
* `specified_effect_prior_confidence` and `log_authority` DO carry a real
  authority verdict — but the only rule that ever changes them is
  `f16_retire_jammed_rudder_specification_prior`, which fires off the SCHEDULED
  fault, on `actuator_group == 2`, for every scenario.  The seed's own comment
  concedes the point: *"the scheduled arming is an oracle the aircraft would
  not have."*

So the availability half of the option-set build **cannot be derived from what
exists** — it has to be built, and what it needs is an interventional estimate:
does commanding this effector change this consequence, holding the rest?  That
is a new capability (a controlled probe, or a causal estimate from the
command/consequence stream that conditions on what else was commanded), not a
rewiring of what is already there.

This is the second predicate this spike has killed before it reached the
aircraft, and both were killed by projecting rather than by flying.  Given that
two of the last three builds in this line measured WORSE when shipped
(v8.3.0: 19 -> 22 crashes), that is the cheaper order of operations and it
should stay the default.

---

## 10. Block K — the authority instrument built and flown, deciding nothing

`f16_flight_path_control` **v8.4.0** adds two rules and no decisions:
`f16_note_sole_member_authority_evidence` accumulates a program's
`prediction_error_energy` onto the model that was commanded, but only when the
program had exactly ONE member and only once the learning rule has stamped that
action (so there is no rule-order race and no one-action lag);
`f16_publish_group_authority_evidence` rolls it up per actuator group as a mean
and an evidence count, publishing a zero count as "no evidence" rather than as
"no error".  Both stamped into the diagnostics trace.  Block:
`results/jsbsim_f16_paper_replication_10hz_authority_instrument_k_v1`,
4 scenarios x 25 frozen seeds, gate OFF.

**Which group's predictions failed worst, per episode (argmax over groups with
evidence):**

| scenario | elevator | aileron | rudder | throttle |
|---|---:|---:|---:|---:|
| nominal | 8 | 0 | 1 | **16** |
| jammed_rudder | 1 | 0 | **15** | 9 |
| saturated_elevator | **22** | 0 | 1 | 2 |
| damaged_wing | 0 | **0** | 10 | **15** |

**It works on two faults and fails on the third.**

* `saturated_elevator` → elevator in **22 of 25**.  Clean.
* `jammed_rudder` → rudder in **15 of 25**.  Majority, correct effector.
* `damaged_wing` → aileron in **0 of 25**, against a pre-check on block H's
  traces that showed the aileron at 456 median against peers at 24-111.
* `nominal` → the argmax always names someone (throttle 16 of 25).  **There is
  no "nothing is wrong" state**, which was anticipated and is not yet solved.

**Two candidate causes for the damaged-wing failure, and this block cannot
separate them:**

1. **Mean versus median.**  The pre-check used a per-action MEDIAN; the rule
   accumulates a sum and divides, i.e. a MEAN, and a handful of catastrophic
   actions dominate it — the wing's rudder reads 17,159 and throttle 14,757
   against the aileron's 1,657, on 36 and 60 samples.  The median was robust to
   exactly this and the graph rule is not.  A running median is not accumulable;
   **the geometric mean is** (accumulate `Log` of the error, which the seed
   already imports), and that is the specific next change.
2. **The baseline moved underneath the instrument.**  Block K runs v8.4.0,
   which inherits **v8.3.0's ledger pricing — the change measured WORSE in
   block J** (19 -> 22 crashes).  Every group's error is far larger here than
   in block H (damaged-wing elevator 783 against 23.5), because the flights
   themselves are more violent.  The pre-check was taken on v8.2.0 flights and
   is therefore not comparable.

**That confound is now blocking, and it is procedural rather than technical.**
Three measurements in a row have been taken against a seed state that is known
to be worse than the one before it.  The instrument question cannot be settled
until the pricing question is, and the pricing question is a standing decision:
v8.3.0 is principled and measured worse; v8.2.0 is measured better and rests on
a collapse that is load-bearing for the wrong reason.

---

## 11. A standing rule, from the project owner, on measuring under a moving baseline

Block K's write-up closed by saying the pricing question blocked the instrument
question, because three measurements in a row had been taken against a seed
state known to be worse than the one before it, and the instrument needed a
fixed reference.

**The owner's ruling: keep v8.3.0.  "The ground is always shifting.  That's the
whole point."**

The ruling is not a preference, it exposes an error in the analysis:

* **The instrument's own statistic is an ARGMAX WITHIN AN EPISODE, and an
  argmax is scale-free.**  If more violent flights raise every group's
  prediction error together, the ranking is unchanged.  So "the baseline moved"
  could not have explained the damaged-wing failure under any circumstances,
  and offering it as one of two candidate causes was wrong.  **Cause (1) — the
  arithmetic mean is not robust — is the whole cause.**
* The within-episode cross-group comparison was CHOSEN precisely so that no
  external baseline would be needed (section 8: healthy flight never commands
  the aileron alone, so no cross-episode baseline exists for it and none is
  required).  Reaching for a fixed reference in the analysis abandoned the
  property the design was built to have.

**Standing rule minted, and it generalises past this line:** *a measurement
that requires the rest of the system to hold still is measuring the wrong
thing.*  Every quantity this line trusts already obeys it — the ledger is
monotone under change rather than constant, the reserve ratchets rather than
resets, order-N measures where a residual stops compressing rather than a fixed
value, and the channel discount is a RELATIVE price.  The instrument must be
read the same way, and a demand for a frozen baseline is a design smell in the
reader, not a defect in the ground.

**v8.5.0** therefore stamps BOTH statistics — the arithmetic mean and the
mean of `log1p(prediction error)`, whose ordering is the geometric mean's and
which a few outliers cannot dominate — so that ONE block decides which of them
discriminates, rather than a second block run against a different world.

---

## 12. Block K2 — both statistics, one block: each is right exactly where the other is wrong

`f16_flight_path_control` v8.5.0 stamps the arithmetic mean and the
`log1p` mean side by side.  Argmax over groups with evidence, per episode,
4 scenarios x 25 frozen seeds:

| scenario | correct group | ARITHMETIC mean | LOG mean |
|---|---|---|---|
| nominal | (none) | throttle 16, elevator 8 | throttle 16, elevator 7 |
| jammed_rudder | rudder | **rudder 15/25** | rudder 2/25, aileron 17 |
| saturated_elevator | elevator | **elevator 22/25** | elevator 7/25, aileron 18 |
| damaged_wing | aileron | aileron **0/25** | **aileron 24/25** |

**The log fix works, and it breaks the two cases the mean had right.**  It
identifies the damaged wing 24 of 25 — the failure it was written for — and
collapses the jammed rudder from 15 to 2 and the saturated elevator from 22 to
7, naming the AILERON in both.

**Neither statistic is the answer, and the pattern says why.**  The two faults
the arithmetic mean catches are heavy-tailed — a few catastrophic actions on
the faulted surface, which a mean is sensitive to and a geometric mean
suppresses.  The fault the log mean catches is the opposite: the damaged wing's
aileron is CONSISTENTLY moderately wrong, which a geometric mean rewards and a
mean drowns among other groups' rarer, larger excursions.  **The fault
signature lives in the SHAPE of the per-group error distribution, not in its
centre**, and no single scalar summary of that distribution can carry it.

**This re-derives, empirically and at cost, something the line already wrote
down.**  Derivation item 6: *"A point in time has almost no meaning in itself
... Pooling to medians/modes deletes exactly the separating information."*
Both statistics here are pools.  The mistakes list already carries the same
entry — *"Pooled trajectories into medians and modes, destroying the separating
information, then called the prediction falsified on the wrong object."*  It
was made again, one level down, on prediction error instead of on order
streams.

**So the next instrument is not a third statistic.**  It is the operator this
line already holds and already trusts for exactly this: the order-N recursion
(`TimeInfer`, `GENERIC_ORDER_N_*`), applied to each group's prediction-error
STREAM.  Order measures where a residual stops compressing rather than where a
distribution centres, it does not pool, and it is the same instrument the axis
clocks are built on.  A group whose error stream has become incompressible at
every order is a group whose model has stopped predicting it — which is what
authority loss IS.

**Still unsolved, and unchanged by either statistic:** nominal names a group
too (throttle 16 of 25 under both).  An argmax always has a winner.  The "no
group is anomalous" state needs the same treatment — a reading, not a
threshold — and the order-N framing offers one, since a healthy group's error
stream should still be compressible.

---

## 13. The order-N authority instrument (v8.6.0), and a sign error caught by the smoke test

Built on the machinery the axis clocks already use, not a new statistic: each
actuator group's prediction error on SOLE-MEMBER actions is appended to a
bounded stream (`f16_authority_history_g{n}`, bounded by the loop's own
evidence window), and the held order-N recursion reads its ORDER
(`_axis_clock(history, "order_fit")`).  The raw and log means are kept
alongside so all three can be compared in one block.

**The proposed reading was BACKWARDS, and one smoke episode said so before the
block ran.**  Section 12 proposed *"a group whose error stream has become
incompressible at every order is a group whose model has stopped predicting
it."*  Measured on the damaged-wing base seed:

| group | order | samples |
|---|---:|---:|
| elevator | 0 | 80 |
| **aileron** | **2** | 80 |
| rudder | 0 | 49 |
| throttle | 0 | 76 |

The aileron — the effector the damaged wing compromises — reads the MOST
structured stream, not the least.  On reflection that is the textbook reading
of a residual and the proposal had it inverted:

* **order 0 = the residual is incompressible = WHITE.**  That is what a
  correctly-specified model leaves behind.  Nothing systematic remains.
* **order >= 1 = the residual still has structure the model is not
  capturing = SYSTEMATIC mis-specification.**  The effector is wrong in a
  predictable way, which is exactly authority loss: the model's account of what
  this effector does no longer matches what it does.

This also supplies the thing every previous statistic lacked — **a positive
signature for the healthy case.**  An argmax always crowns a group; order does
not.  If nothing is mis-modelled, every group reads 0 and the correct answer
("no group is anomalous") is representable rather than being the absence of an
answer.

**Prediction for block L, committed before it is read** (4 scenarios x 25
frozen seeds, gate off, the block-H protocol):

1. **Nominal reads order 0 on every group with evidence, in a clear majority of
   its 25 episodes** — the healthy signature exists.
2. **Each fault scenario reads order >= 1 on its OWN effector more often than
   on any other group**: jammed_rudder -> rudder, saturated_elevator ->
   elevator, damaged_wing -> aileron.
3. **It beats both centre statistics**, which each solved two of the three
   fault scenarios and failed the third.

**What would falsify it:** nominal reading order >= 1 broadly (no healthy
signature); or a fault scenario whose own effector is not the most-often
structured group; or the instrument agreeing with the arithmetic mean exactly,
in which case it has added nothing over a statistic already measured.

**Named in advance as the most likely failure:** `jammed_rudder`.  A retired
prior predicts nothing and therefore cannot be wrong — the rudder's raw error
was exactly 0.0 in two scenarios in the block-H pre-check — so a jammed rudder
may leave NO residual to have structure, and the instrument would be blind to
precisely the fault whose prior the system has already written off.

---

## 14. Block L — the healthy signature WORKS, the attribution does NOT

`results/jsbsim_f16_paper_replication_10hz_authority_ordern_l_v1`, 4 scenarios
x 25 frozen seeds, gate off.  Groups reading order >= 1 (structured residual):

| scenario | episodes with NO group structured | per-group episodes with order >= 1 |
|---|---:|---|
| nominal | **20 / 25** | throttle 3, rudder 3, elevator 1 |
| jammed_rudder | 11 / 25 | aileron 9, elevator 6, **rudder 3** |
| saturated_elevator | 0 / 25 | rudder 22, aileron 12, **elevator 6** |
| damaged_wing | 1 / 25 | **aileron 22**, elevator 10, rudder 2 |

* **Prediction 1 — "nominal reads order 0 on every group, in a clear majority":
  HELD.**  20 of 25 completely clean.
* **Prediction 2 — "each fault reads order >= 1 on its OWN effector more often
  than any other": HELD 1 of 3.**  The damaged wing lights the aileron 22 of
  25.  The saturated elevator lights the RUDDER 22 and its own elevator 6.  The
  jam lights the AILERON 9 and its own rudder 3.
* **Prediction 3 — "it beats both centre statistics": FALSIFIED.**  It solves
  one fault; the arithmetic mean solved two.
* **The named most-likely failure FIRED, for its named reason.**
  `jammed_rudder` reads its own effector 3 of 25 — a retired prior predicts
  nothing and therefore cannot be wrong.  The saturated elevator's failure was
  NOT predicted and is worse: it mis-attributes rather than going blind.

## 15. What the three instruments together establish

| instrument | healthy signature | jam | elevator | wing |
|---|---|---|---|---|
| arithmetic mean (argmax) | none — always crowns a group | **15/25** | **22/25** | 0/25 |
| log mean (argmax) | none | 2/25 | 7/25 | **24/25** |
| **order-N (structured residual)** | **20/25 clean** | 3/25 | 6/25 | **22/25** |

**Attribution has now failed three times, from one cause.**  Every instrument
tried attributes a residual to the effector that was commanded, and the plant's
STATE IS SHARED: when the aircraft is in an abnormal condition, every
effector's residual carries that abnormality, whichever one is moving.
Commanding an effector alone does not isolate it — the saturated elevator makes
the RUDDER's residual structured in 22 of 25 episodes, because the airframe is
descending abnormally, not because the rudder has changed.  Isolation needs the
residual conditioned on state, or a genuine controlled probe; neither is a
statistic, and neither exists here.

**But one thing DID land, and it is worth more than the attribution was.**
Order-0-everywhere is a working **"nothing is systematically mis-modelled"**
reading: 20 of 25 clean in healthy flight against 0 of 25 and 1 of 25 in the
two faults it detects.  No centre statistic could express that state at all —
an argmax always crowns a group.

**That has a direct, unglamorous use which removes an ORACLE.**
`f16_arm_recalibration_after_scheduled_fault` currently arms a fresh model pass
from `recalibration_arm_action`, i.e. from the SCHEDULED fault time, and the
seed's own comment concedes it: *"the scheduled arming is an oracle the
aircraft would not have."*  A global "some group's residual has structure"
reading is exactly the non-oracle trigger that arming needs, and it does not
require attributing the structure to the right effector — which is the part
that keeps failing.

**Recommended next, and NOT built here:** arm recalibration off the order
instrument instead of off the schedule, and measure against the scheduled arm.
It is a smaller claim than availability, it is supported by the block, and it
converts a measured capability into the removal of an oracle.  The availability
predicate still needs attribution, and attribution needs a different kind of
evidence than any statistic over passively-collected residuals can supply.

---

## 16. Reverse shape matching — the pattern is diagnostic where the argmax is not

Prompted by the project owner: *"Do we need to do reverse shape matching —
counterfactuals about 'what would cause this'"*.  Tested on block L's existing
data, because if the answer is yes the evidence is already there and the argmax
threw it away.

**The per-group signature, as a bit vector (elevator, aileron, rudder,
throttle), of which groups' residuals carry structure:**

| scenario | most common signatures |
|---|---|
| nominal | `0000` x20 |
| jammed_rudder | `0000` x11, `0100` x5, `1000` x3 |
| saturated_elevator | **`0010` x10, `0110` x7**, `1010` x3 |
| damaged_wing | **`0100` x13, `1100` x6** |

**Leave-one-out nearest-signature classification: 67 of 100, against 25%
chance** — on a 4-bit encoding that discards the order VALUES and the sample
counts entirely.

**The mis-attributions are not noise; they are the signature.**  The saturated
elevator reliably structures the RUDDER's residual (`0010`/`0110`); the damaged
wing reliably structures the AILERON's (`0100`/`1100`).  Those are different
and decodable.  Section 15 concluded that shared plant state defeats
attribution — that stands, and it is now clear that shared state defeats
FORWARD attribution specifically, because a shared abnormal condition produces
a COMMON-MODE pattern across groups, and a pattern is exactly what a decoder
can match and an argmax cannot.

**So: yes, and the operator already exists.**  `ShapeDecode`
(`runners/dsl/src/shape_decode.rs`) is the dequantization op — an observation
is decoded against the held codebook, parts compete, the assignment emerges,
and **the residual is the unmatched span**.  `seeds/shape_decode_loop.json`
v1.8.0 carries the full growth ladder (`sd_decode` -> `sd_recognize` ->
`sd_transform_decode` -> `sd_infer_dimension` -> `sd_mint_quantum` ->
`sd_redecode`).  CLAUDE.md's own framing is that `compose_design_for_goal` and
`induce_concern` are the SAME op at two points of one loop; a fault decode is
that op at a third point.

**And the codebook does not have to be declared, which is what keeps this from
being another oracle.**  The sd loop's whole point is dynamic quantization: a
residual that matches nothing mints a quantum, `codebook_epoch` re-arms the
decode, and the next occurrence is recognised.  So the agent grows its own
fault vocabulary from what it meets — a first damaged wing mints a signature, a
second one is recognised — instead of being handed a list of fault names it
could not have known.

**Why this fixes the failure that beat three statistics.**  A common-mode
abnormality is itself a codebook entry.  Decoding explains the shared part with
the state signature and leaves the effector-specific part as the unmatched
span, which is the quantity attribution actually wanted.  Forward attribution
has no way to express "most of this residual is the airframe, this bit is the
surface"; a decode does, because the residual is first-class in it.

**Honest limits, stated before any build:**

* 67% is a floor from a deliberately lossy encoding, but it is also n=100 over
  four scenarios with 25 each, and the two signatures that carry it (`0010`,
  `0100`) are one bit apart.  A held-out powered block is what would establish
  it, not this.
* Block L's scenarios are the ONLY four this encoding has seen.  A decoder
  trained on four fault families says nothing about a fifth, and the sd loop's
  minting path is exactly what would have to handle that — untested here.
* The signature was computed at END of episode.  A decode that has to run
  DURING flight needs the same reading online, and the order stream is bounded
  by the evidence window, so this is available — but it is not what was
  measured.

---

## 17. The reverse decode, BUILT (v8.7.0) — and what it does and does not yet do

`f16_observe_authority_signature` mints one `Observation` per deliberation
opening carrying the 4-bit authority pattern, edged `agent -observed-> obs` with
`status: "pending"`, and the F-16's seed set now loads `shape_decode_loop`.  The
consumer decodes NOTHING; the held loop does decode -> recognise -> mint ->
re-decode.  38 rules, 48 tests green.

**The flight is unchanged.**  Nominal base seed reads
**323.28346789186793 ft**, the pinned value — so loading a decoder and minting
observations perturbs no aircraft, which is the invariant that lets this be
measured as an instrument.

**Behaviour across 12 episodes (4 scenarios x 3 frozen seeds):**

| scenario | observations per episode | outcome | CapabilityAxis |
|---|---|---|---|
| nominal | 1 | `recognized` x1 seed, **`minted` x2 seeds** | 1 or 2 |
| jammed_rudder | 2-5 | **minted 1**, rest recognised | 1 -> 2 |
| saturated_elevator | 5 | **minted 1**, rest recognised | 1 -> 2 |
| damaged_wing | 5-6 | **minted 1**, rest recognised | 1 -> 2 |

**Exactly one quantum is minted per fault episode, never more, and the repeats
are recognised.**  That is the growth ladder terminating correctly — the
`has_transform` guard makes it mint-once under codebook growth — and it is the
dynamic-quantization behaviour the sd loop was built for, arriving unmodified
on a new domain.

**Two honest limits, both structural rather than tuning:**

1. **Nominal mints in 2 of 3 seeds.**  Healthy flight sometimes produces a
   non-empty signature (consistent with block L's 5 of 25 nominal episodes
   carrying a structured group), and an unrecognised non-empty signature mints.
   A false mint is cheap — it grows the vocabulary by one — but it means the
   codebook is not yet a clean fault/no-fault discriminator.
2. **THE VOCABULARY DIES WITH THE EPISODE.**  Every episode boots a fresh
   agent, so "first encounter mints, second recognises" happens only WITHIN one
   flight.  Nothing carries a minted fault signature into the next episode, so
   the grown vocabulary is not yet a vocabulary — it is a within-episode
   dedup.  The facility that would fix this already exists and is documented in
   CLAUDE.md: `teach(agent, ...)` persists a learned item into a seed manifest
   so a fresh boot holds it.  **That is the next rung, and it is the one that
   turns this from a decode into learning.**

**What this rung establishes:** the reverse decode runs on the real plant, in
the real loop, costs nothing in flight, and behaves exactly as the sd loop's
design predicts on a domain it was not written for.  What it does NOT yet
establish is that the grown signatures are diagnostic across episodes — block
L's 67% says the PATTERN carries that information, but this build has not been
shown to accumulate it.

---

## 18. The rudder-prior bug: fix attempted, MEASURED WORSE, reverted

**The bug, confirmed again:** `f16_retire_jammed_rudder_specification_prior`
guards on `actuator_group == 2` AND the SCHEDULED fault being armed, so it
retires the RUDDER's prior under any non-nominal scenario.  Probed: `nominal`
holds every prior; `jammed_rudder` and `damaged_wing` both read
`rudder=RETIRED`.  It has done this in every block this line has run.

**The fix built (v8.8.0):** ask the local, non-oracle question — was the
surface where it was told to be — as
`|specified_command_level - state_effector_position| >
specified_maximum_position_change_per_action`, read only from the
sole-commanded member, with the hardcoded group dropped so it generalises to
any stuck surface.

**Measured, one episode per scenario: EVERY actuator group had models retired
in EVERY fault.**  That is broader damage than the bug it replaced, so it was
**reverted rather than shipped** (v8.9.0 restores the previous guard).

**Why it failed, recorded so the next attempt does not repeat it:** that gap,
taken at the moment the command is issued, is the **commanded step**, not a
tracking failure.  A healthy rate-limited surface legitimately shows a gap
wider than one action's travel whenever the step is large, and closes it over
several actions.  The correct test is about MOVEMENT, not position — the
surface failed to move by its declared travel WHILE it had a larger gap to
close — and that needs the previous achieved position retained per model.
Nothing stores it, and `state_effector_position` is shared across a group's
nine command-level models, so it cannot simply be differenced per model.

`f16_position_tracking_error` is left stamped as telemetry: it is the quantity
the real fix differences and it costs nothing.  **The bug stands, now with a
precise account of what a correct fix requires.**

---

## 19. The tracking test, properly built — and why it still is not wired

Third attempt on the rudder-prior bug.  Two defects in the v8.8.0 attempt were
found and both are now fixed in the INSTRUMENT (v8.11.0), which is kept:

1. **No lag.**  `f16_prev_effector_position` equalled `state_effector_position`
   at every read — `run_rules` runs to a FIXPOINT, so ordering a consumer
   "before" the roll does not stop it being re-entered after it.  Fixed with a
   TWO-SLOT roll (`prev2 <- prev` then `prev <- current`, in that effect
   order), which is the same effects-apply-in-order mechanism the v3.1.0
   escalation-count fix turned on.
2. **Wrong comparison.**  A healthy rudder moves **0.002-0.045** per action
   against a declared `specified_maximum_position_change_per_action` of
   **0.5**, so "moved by at least its declared travel" is false for every
   surface and read STUCK everywhere.  Movement is now tested against ZERO —
   a jammed surface is exactly stationary, and zero is the lattice origin.

**The instrument now separates cleanly at the evidence level:**

| scenario | rudder fail/ok |
|---|---|
| nominal | **0/65, 0/39** — moves freely |
| jammed_rudder | **18/0, 17/0** — never once moved |
| damaged_wing | 9/22, 18/17 — moves |
| saturated_elevator | 0/10, 0/9 — moves; and its ELEVATOR reads 6/2 |

**But wiring it into the retirement made things worse and it was reverted.**
Gated on `fail > 0 AND ok == 0`, one episode per scenario gave: the damaged
wing and saturated elevator correctly HELD the rudder (the bug's target), and
the elevator scenario correctly retired its own elevator — but elevator,
aileron and throttle were retired across the fault scenarios, and the
saturated-elevator episode crashed where it had not.

**Why: the counts latch.**  `ok == 0` is true EARLY in every episode, before
any surface has had a chance to succeed, and retirement is irreversible.  The
test needs an evidence-SETTLED condition, and no threshold-free form of one is
available here — the line refuses picked constants, and the declared quantity
that would serve (`regime_evidence_horizon_actions`, 80) is larger than the
total failure count a jammed rudder accumulates in a whole episode (18).

**State: the bug STANDS, deliberately.**  `f16_retire_jammed_rudder_...`'s
original guard is restored (v8.13.0).  The tracking instrument, the two-slot
roll and the per-group fail/ok telemetry are all KEPT, because they are
correct, measured, and are what a fourth attempt would start from.  What is
missing is not the detector — that works — it is a settling condition that
does not invent a constant.

---

## 20. Authority as a proportion (v8.15.0) — the bug is fixed, and a generator was destroyed and rebuilt

**The correction, from the project owner:** *"retirement is representing it as a
binary. it is a proportion of authority vs expected, and is updated based on
evidence. a stuck control can become unstuck."*

That dissolves the latch rather than delaying it.  Three attempts had tried to
fix the GUARD of a binary, irreversible verdict; the defect was the verdict.
`f16_retire_jammed_rudder_specification_prior` is replaced by
`f16_weight_authority_by_evidence`, recomputed every action:

    log_authority = Log((ok + 1) / (ok + fail + 1))

where `ok`/`fail` are the group's measured "asked to move and did / did not".
With no evidence the ratio is exactly 1 and `log_authority` is exactly 0 — the
healthy default, reached with no special case.  `log_authority` is the channel
`embodied_motor_program`'s composer already weights members by, so a
down-weighted surface competes less without being removed.

**Measured, one episode per scenario (authority as a proportion):**

| scenario | elevator | aileron | rudder | throttle | alt RMSE |
|---|---:|---:|---:|---:|---:|
| nominal | 1.00 | 1.00 | **1.00** | 0.11 | **323** |
| jammed_rudder | 0.60 | 0.33 | **0.09** | 0.50 | 6,929 |
| saturated_elevator | **0.33** | 0.33 | **1.00** | 0.50 | 5,318 |
| damaged_wing | 0.50 | 0.57 | **0.43** | 0.64 | 12,242 |

**The bug is fixed.**  The rudder reads full authority in nominal AND under a
saturated elevator, 0.43 under a damaged wing, and **0.09 under the jam** — the
lowest reading anywhere in the table.  The surface that is actually stuck is
identified by evidence, not by a hardcoded group ordinal and a scheduled-fault
oracle.  The saturated elevator is independently down-weighted to 0.33 by the
same rule, which the old one could never do.  Nominal flight is unchanged.

**Residual, recorded not smoothed:** the throttle reads 0.11 in NOMINAL.  A
throttle commanded to hold position is stationary without being stuck, and the
"asked to move and didn't" test cannot tell those apart for an effector whose
normal state is to sit still.  The graded form makes this much less harmful
than a binary retirement would have been, but it is wrong and it is not fixed.

## 21. A generator was destroyed and rebuilt — what happened and what it cost

While making the change above, a `python3` patch used a two-anchor text slice
whose anchors were **~1,250 lines apart**, deleting roughly half of
`gen_f16_flight_path_control_seed.py` — 12 rule builders, the axis and regime
constants, and four predicate helpers.  The generated seed survived because the
crash preceded the write.

**Recovery, and why it was possible:** `git HEAD` held only **v3.0.0 / 28
rules** — the whole v4.0.0–v8.x line is uncommitted work — so restoring from
version control would have destroyed far more than the accident did.  Instead
the seed artifact (v8.14.0, 39 rules) was the ground truth: every deleted rule
existed there as a complete dict.  The builders were restored to return those
dicts verbatim (`seeds/_recovered_f16_rules.json`), the constants and helpers
were re-derived, and the result was checked by **regenerating and diffing
against the pre-corruption seed: every rule body byte-identical**, the only
differences being the intended v8.15.0 change.  Regeneration is idempotent and
48 tests pass.

**What it cost, stated plainly:** 12 rule builders are now DATA rather than
readable term-tree construction.  Behaviour and reproducibility are fully
restored — the seed is regenerable from source again, which is the load-bearing
invariant — but the source quality of those twelve is degraded, and
re-expressing them in the DSL helpers is owed work with the seed as the
ground truth to check against.

**The lesson:** never delete a span by two anchors without measuring the span
first.  And a second one, sharper: **this work is entirely uncommitted, so
`git` is not a safety net here.**  The only reason the accident was recoverable
is that the build artifact and the source are separate files and the crash
happened between them.

---

## 22. Confidence in the authority = how much it was commanded (v8.16.0)

Owner's instruction: *"have confidence in the authority be how much it was
commanded."*  An authority proportion read off two observations and one off two
hundred are not the same claim, and nothing in the estimate said so.

`f16_authority_confidence = n / (n + H)` per model, where `n = ok + fail` is the
number of times that surface was asked to move and `H` is the loop's declared
`regime_evidence_horizon_actions`.  No evidence reads 0; evidence far past the
horizon approaches 1.  The confidence-SHRUNK estimate is stamped beside the raw
one so a single block decides between them.

| scenario | surface | authority | confidence | shrunk |
|---|---|---:|---:|---:|
| nominal | rudder | **1.00** | 0.42 | 1.00 |
| nominal | throttle | **0.11** | 0.09 | **0.92** |
| jammed_rudder | rudder | **0.09** | 0.11 | **0.90** |
| saturated_elevator | elevator | **0.33** | 0.09 | **0.94** |
| damaged_wing | aileron | 0.57 | 0.25 | 0.89 |

**The confidence itself is informative and is kept.**  It tracks evidence
exactly as intended — the nominal rudder is commanded often (0.42), the nominal
elevator and aileron are never commanded alone with a gap to close (0.00).

**Shrinking the estimate by it is MEASURED WORSE and is NOT wired.**  It fixes
the throttle false positive (0.11 -> 0.92) and destroys every true positive with
it: the jam goes 0.09 -> 0.90 and the saturated elevator 0.33 -> 0.94.

**Why, and it is a scale error rather than a design error:** sole-member
commands accrue at roughly 2-65 per 1,000-action episode, so `n/(n+80)` never
approaches 1 and the shrinkage is a near-constant pull toward the default.  The
evidence horizon is the loop's CONTROL timescale, not its EVIDENCE-ACCRUAL
timescale.  A confidence built on the rate at which this evidence actually
arrives might behave very differently, and that denominator is an open
question — it is not answered by declaring one.

`f16_authority_shrunk` remains stamped as telemetry with nothing reading it.
Nominal flight unchanged at 323.28346789186793 ft.

---

## 23. The pilot's move was already built — and it is the evidence this line was missing

Owner: *"on a failure, the first thing a human pilot does is test the broken
effector."*

**It is already implemented, it is triggered by SURPRISE rather than by the
schedule, and it runs.**  `emp_mark_factorized_models_for_recalibration` marks
every model `recalibration_required` and puts `program_mode` back to
`"calibration"`, re-entering the frontier that systematically exercises
effectors.  Measured on block L's traces:

| scenario | program_mode | recalibrations / episode |
|---|---|---:|
| nominal | synthesis 1.00 | **0** |
| jammed_rudder | synthesis 0.93, **calibration 0.07** | 2 |
| damaged_wing | synthesis 0.93, **calibration 0.07** | 2 |

and the calibration actions are exactly what a deliberate test looks like:

| scenario | calibration actions | member_count | actions per group |
|---|---:|---|---|
| jammed_rudder | 215 | **1 x210**, 4x4, 3x1 | 58 / 59 / 58 / 54 |
| damaged_wing | 216 | **1 x212**, 4x3, 2x1 | 56 / 58 / 57 / 55 |

~215 sole-effector actions per fault episode, spread EVENLY across all four
surfaces, and none at all in healthy flight.

**This corrects section 9 of this spike**, which concluded that an
interventional estimate "is a new capability (a controlled probe ...), not a
rewiring of what is already there."  The controlled probe was already there.
What was missing was reading it AS evidence about authority: the sole-member
actions this line has been accumulating are largely these probes, and nothing
distinguished a deliberate test from an incidental command.

**`f16_note_probe_authority_evidence` (v8.17.0) is built and reads ZERO**, and
the cause is known: it guards on `program_mode == "calibration"` evaluated
DURING the tick, while the trace's mode is the POST-tick value — the mode has
already flipped by the time the outcome verifies.  The fix is to key off a
marker that persists across the tick, the model's own `recalibration_required`,
which the recalibration rule sets and which clears when the model is
re-learned.  **Not applied**: it is a one-line guard swap, but it is a guess
until measured, and the discipline that has held all session is to project or
probe before shipping.

The rule is left in place, stamped and read by nothing, so the next attempt
starts from an instrument that is wired and a diagnosis that is specific.

## 24. Probe-restricted authority (v8.19.0) — deliberate evidence beats incidental evidence

Two guards were tried and each read ZERO, and each was diagnosed by measurement
rather than replaced by a guess:

* `program_mode == "calibration"` — the trace's mode is the POST-tick value and
  has flipped back by the time an outcome verifies.
* `recalibration_required` on the MEMBER — structurally impossible.  Measured:
  the flag is set on all 36 models at once and cleared ONE MODEL AT A TIME as
  each is re-learned (36, 35, 34 ... 1 across an episode's 72 calibration
  actions).  The rule already requires `last_learning_seq == request_seq`, i.e.
  that the member HAS been re-learned — the very step that clears its flag.

Keyed instead to the PASS (some model still needs recalibration, so a
deliberate test is under way):

| scenario | elevator | aileron | rudder | throttle |
|---|---:|---:|---:|---:|
| nominal | — | — | — | — |
| jammed_rudder | 0.50 | 0.00 | **0.00** (0 of 10) | 0.67 |
| saturated_elevator | **0.25** | 0.00 | **1.00** (10 of 10) | 0.75 |
| damaged_wing | 0.00 | **0.00** | 0.40 | 0.75 |

**Better than the passive counts on every scenario**, and one difference is
categorical rather than incremental: **nominal produces NO probe evidence at
all**, because no calibration pass runs in healthy flight.  The throttle false
positive that the passive counts could not shake (0.11 in nominal) is not
reduced here, it is structurally impossible — there is nothing to read.

That is the whole content of the pilot's move: evidence gathered ON PURPOSE,
under a deliberate test, is worth more than the same arithmetic over whatever
the aircraft happened to be doing.  The counts are small (2-10 per group) and
the damaged wing ties its aileron and elevator at 0.00, so this is a clean
signal, not a finished discriminator.

**Recalibration is currently GLOBAL, and that is now measured.**  The countdown
from 36 is every model of every group: on a surprise the agent re-tests the
whole airframe rather than the surface the evidence implicates.  Per-effector
recalibration is the owner's next point and it lives in
`emp_mark_factorized_models_for_recalibration` in the SHARED motor seed, so it
carries blast radius beyond this domain.

## 25. First-global-then-targeted recalibration: built, measured, reverted

Owner's directive, after the tension was raised: the first recalibration pass
stays global (it is HOW the per-effector evidence is obtained), later passes
target.  Built as an ADDITIVE F-16 rule that clears the mark the shared
`emp_mark_factorized_models_for_recalibration` sets, so no other consumer of
that seed changes: a surface is skipped when its deliberate-probe record is
perfect — tested at least once, never once failed to move.  Both comparisons
against zero, no threshold.

| scenario | calibration actions | skips | probe evidence | outcome |
|---|---:|---:|---|---|
| nominal | 0 | 0 | — | 323 ft, unchanged |
| jammed_rudder | 72 | **0** | rudder 10/0 | 6,929 ft, unchanged |
| saturated_elevator | **72 -> 56** | **rudder 17** | rudder 0/1, elevator 6/2 | 2,588 ft |
| damaged_wing | 72 -> 56 | 0 | **all 0/0** | **CRASHED** (was no crash) |

**It works where the evidence is settled** — the saturated elevator's rudder
proves itself and is then skipped 17 times, and the elevator still reads
lowest.  **It is correctly inert where nothing is proven** — the jam skips
nothing and stays global.

**And it broke the damaged wing.**  All probe evidence collapsed to 0/0 and the
episode crashed, despite skipping nothing there.  The pass still truncated,
72 -> 56.

**Cause: the rule acts on evidence that is still accruing.**  It is evaluated
continuously DURING a pass, so a group with a transient early success and no
failure yet satisfies "never once failed", gets its mark cleared, and the pass
that would have recorded its failures is truncated.  This is the same family as
the retirement latch — acting the first instant a condition holds — and it is
why the wing, whose surfaces fail intermittently rather than absolutely, loses
its evidence entirely.

**REVERTED** (v8.21.0); `saturated_elevator` and `damaged_wing` restored to
5,318 ft and 12,242 ft, no crash.  The fix is to skip on evidence from a
COMPLETED prior pass rather than the accruing one, which needs a per-pass
snapshot of the counts — not attempted here, because it is another unmeasured
change and every unmeasured change today has had to be undone.

## 26. "The dynamics are a delta" — TESTED BEFORE BUILDING, and falsified in its cheap form

Owner: *"it shouldn't matter what the precise fault is ... the change is in the
observed outcome, the dynamics are a delta, not a from-scratch thing."*

Tested as the sd loop's rung 2 would express it — the same shape moved along a
dimension — by fitting ONE scale and offset per (group, consequence) across the
nine command levels, from the held map at action 99 to the learned map at 999.

| scenario | median R^2 of `post ~ s*pre + b` |
|---|---:|
| **nominal (control)** | **0.890** |
| jammed_rudder | **0.078** |
| saturated_elevator | **0.170** |
| damaged_wing | **0.333** |

**The control validates the instrument.**  Nominal makes the same
prior-to-learned journey over the same 900 actions and the shape SURVIVES.
Ordinary learning is a delta.  Under fault it is not: 0.08-0.33 means a single
scale and offset per consequence cannot express what happened.

**So the cheap form of the delta hypothesis is FALSIFIED and was not built.**

**Named diagnosis for why the wing in particular may fail a test it could have
passed:** the damaged wing sets `roll_beta = -1.0` (reversed) and
`yaw_aileron = 1.5` — commanding aileron now produces YAW it did not before.
That is a mixing ACROSS consequence axes, and this fit allowed only a scale and
offset WITHIN each consequence, so a rotation in consequence space scores near
zero however cleanly it fits.  The wing scoring highest of the three faults is
weakly consistent with that.  The honest next hypothesis is a cross-consequence
transform, which is what `DimInfer` (rung 3, "a residual COUPLED across
observed dims") exists for — untested.

Recorded because it is the first change this session that was tested BEFORE
being built rather than after.  It cost one probe run and saved a rung.

## 27. SHAPE MATH — the delta holds at the SUBSET grain, and the previous test destroyed it by construction

Owner: *"this is why I said it was SHAPE math. the vector of the entire control
set, and/or subset."*

Section 26 fitted one scale and offset per (group, consequence) INDEPENDENTLY —
which is precisely what a shape is not.  Re-tested as shape math: the post-fault
consequence VECTOR as a transform of the held one, `q ~ M . p` with a single
6x6 `M` allowed to MIX consequence dimensions, fitted over the whole control
set and over each group as the subset case.

| scenario | whole set | elevator | aileron | rudder | throttle |
|---|---:|---:|---:|---:|---:|
| **nominal (control)** | **0.999** | 1.000 | 1.000 | 0.343 | 1.000 |
| jammed_rudder | −0.686 | 0.106 | 0.368 | **0.704** | 0.983 |
| saturated_elevator | −2.411 | **−4.241** | 0.886 | 0.441 | 0.687 |
| damaged_wing | 0.032 | −1.812 | **0.930** | **0.937** | 0.632 |

**The delta holds at the SUBSET grain.**  Most groups fit at 0.63-0.98 — the
wing's aileron 0.930 and rudder 0.937, the jam's throttle 0.983 — against the
scalar decomposition's scattered 0.06-0.89.  Allowing the transform to mix
consequence dimensions is what makes the difference, and section 26's fit
excluded exactly that.  **The observed change IS a transform of the held model,
not a from-scratch rewrite.**

**The WHOLE control set as one shape does NOT hold** (negative R^2 on two
faults).  Groups transform differently, which is physically correct — a jammed
rudder does not change what the throttle does — so the shape is the vector of a
control SUBSET.  The "and/or subset" carries the claim.

**Honest limit, and it is the same one as everywhere else today:** the group
that fails to fit is not reliably the faulted one.  The elevator is worst in
all three faults, including the wing where the aileron is the culprit, most
likely because it is by far the most-commanded group (2,156 actions in the
wing).  Detecting THAT the shape moved works; identifying WHAT moved does not.

Nominal at 0.999 whole-set is the control that makes the rest readable: when
nothing changes, one transform over the entire set is the identity.

**What building this means:** recalibration would infer a per-subset transform
of the held effector model rather than re-learning it, which is
`TransformDecode` (rung 2, uniform delta per transformed dim) and `DimInfer`
(rung 3, a residual coupled across observed dims) applied to the consequence
vector instead of to ink or ARC grids.  The machinery exists; what this rung
establishes is that the quantity it would operate on behaves as the machinery
assumes.

## 28. THE DIFFERENCE — the cleanest change detector yet, and the sixth failure to localise

Owner: *"the shape of what is happening needs to be subtracted from the shape
of what happened before - the *difference*."*

That names why section 27's R^2 could not localise: **R^2 asks "is it
transformable", which is high both for a subset that did not change and for one
that changed cleanly.**  The difference distinguishes them, and it is what the
order-N recursion already works on.

`|| post - pre ||` per control subset, across 5 seeds per scenario:

| scenario | n | total ‖diff‖ (median) | argmax distribution | correct |
|---|---:|---:|---|---|
| **nominal** | 5 | **0.067** | rud 2, thr 2, elev 1 | — |
| jammed_rudder | 4 | 7.837 | rud 2, elev 1, ail 1 | 2/4 |
| saturated_elevator | 5 | 6.156 | **ail 5** | **0/5** |
| damaged_wing | 4 | 16.292 | ail 2, elev 1, thr 1 | 2/4 |

**As a CHANGE DETECTOR this is the best result of the session: ~90x separation**
(0.067 against a smallest-fault median of 6.156), holding across seeds, with no
overlap.  Compare order-N's 20 of 25 clean nominal with five false positives.

**As an ATTRIBUTOR it fails: 4 of 13.**  The saturated elevator picks the
AILERON 5 times out of 5 — the same aileron artefact that contaminated the
movement column, so it is systematic rather than noise.

**Six independent instruments now** — arithmetic mean, log mean, order-N,
movement probe, shape transform, difference magnitude.  Every one detects that
the plant changed; none reliably says which subset changed.  At six this stops
being a fact about instruments and becomes a fact about the data: passive and
probe flight telemetry under shared plant dynamics supports change DETECTION
but not LOCALISATION.

**The deliverable is the detector, and it is what recalibration actually
needs.**  Recalibration triggers on prediction surprise and marks every model
globally regardless — so a 90x-separated, non-oracle "the shape moved" signal
is a strictly better trigger than the one in place, and it does not require the
attribution that has now failed six ways.  That is the build this line of
questioning has earned; the localisation is not.

## 29. CORRECTION — attribution was never the objective, and this document kept treating it as one

Owner: *"Attribution doesn't matter - Difference matters. You're fixating on
the wrong problem - how the change has occurred doesn't matter, and/or can be
worked out afterwards. That's what flight telemetry is for. A pilot does not
consult telemetry, they react to the plant, and retain authority as much as
possible."*

**Sections 15, 24, 26, 27 and 28 all frame localisation as the goal and report
"failure" against it.  That framing is wrong and is retracted here.**  What
those sections actually established, read correctly:

* **Change detection is ROBUST** — six independent instruments, every one of
  which separates a changed plant from a healthy one, culminating in the
  difference shape's ~90x separation across seeds with no overlap.  That is
  six confirmations, not six failures.
* **Localisation is not recoverable from this data, and does not need to be.**
  A local fault does not have a local observable consequence when the plant's
  dynamics are shared, which is a fact about aircraft and not a gap in the
  instruments.  It is answered after the flight, from telemetry, by an analyst
  who has the whole record and no deadline.

**The response to a detected change is to RETAIN AUTHORITY, and it requires no
attribution at all.**  That is what this line has been circling since the
storm-drain reading (derivation item 9: assess WHILE CONTINUING the metastable
motion, and reverse while reversing is still possible) and what the energy
ledger was built to price (item 10: more energy is more options; surrendering
altitude liquidates the reserve every future decision draws on).

It is also what the powered blocks already measured, and the measurement is
unambiguous: **episodes ending on a corner that KEPT altitude crash at 1/61,
while 26 of 27 crashes end on a corner that surrendered it** (block 3).  The
aircraft that keeps its authority survives; the one that trades it away does
not.  Nothing in that sentence names an effector.

**So the shape of the build this whole line has earned:**

1. **Trigger** — the difference shape moved.  Measured, ~90x separated,
   non-oracle, no attribution (section 28).
2. **Response** — retain authority: do not adopt a corner that surrenders the
   energy axis while the held model is known to be stale; keep flying and let
   the model catch up.
3. **Afterwards** — attribution, offline, from the trace, with no deadline.
   That is a reporting question and it is already served by the trace this
   line stamps.

The gate machinery (blocks E-G) is the mechanism for step 2 and it already
exists.  What it has been missing is a trustworthy trigger for step 1, which
prediction surprise was not and the difference shape is.

## 30. THE TRIGGER, BUILT AND MEASURED (v8.22.0) — telemetry only

`f16_snapshot_shape_reference` holds the effector map once, after calibration
completes; `f16_publish_shape_difference` stamps the squared difference from it
and the reference's own squared magnitude every action, and sets
`f16_shape_changed` when the first exceeds the second.  Squares are compared so
no square root is needed; the ordering is identical.

**The comparison is the map against ITSELF** — "changed by more than its own
magnitude" — so there is no picked constant, no declared threshold, and no
reference to any fault.

| scenario | ratio a=150 | a=300 | a=999 | first fires | alt RMSE | crash |
|---|---:|---:|---:|---:|---:|---|
| nominal | 0.001 | 0.002 | 0.002 | **never** | 323 | False |
| jammed_rudder | 5.507 | 8.780 | 8.614 | **104** | 6,929 | False |
| saturated_elevator | 6.166 | 6.949 | 6.766 | **109** | 5,318 | False |
| damaged_wing | 139.2 | 244.9 | 205.4 | **104** | 12,242 | False |

**Fires 4-9 actions after onset, never in healthy flight, margin 2,500x to
100,000x.**  Every tracking number is unchanged because nothing consumes
`f16_shape_changed` yet.

It is strictly better than the trigger in place.  Recalibration currently fires
on prediction surprise, which is domain-agnostic but noisy, and its own
`recalibration_arm_action` path is the scheduled-fault ORACLE the seed concedes
the aircraft would not have.  This is neither: it is the agent noticing that
its own held model no longer describes its own plant.

**Two consumers are now possible and each needs its own measurement:**

1. **Recalibration trigger** — replace surprise with the shape change.  It
   would move WHEN the probe runs (action 104 rather than wherever surprise
   lands) and how often.  Needs a matched block against the surprise trigger;
   more recalibration is not automatically better.
2. **The authority-retaining response** — while the held model is known stale,
   refuse the corners that surrender the energy axis.  This is the gate's
   existing machinery (blocks E-G) with a trigger it can trust, and the
   response block 3 already measured at n=100: episodes ending on a corner that
   KEPT altitude crash at 1/61, against 26 of 27 crashes on one that
   surrendered it.

Neither is wired.  The detector is committed as telemetry so that whichever is
built next starts from a measured trigger rather than a hoped-for one.

## 31. CORRECTION — the difference shape is not a replacement for surprise, it IS surprise

Owner: *"also the difference shape isn't in place of surprise, it IS surprise."*

Section 30 listed "replace surprise with the shape change" as one of two
consumers needing a matched block to choose between them.  **That framing is
wrong and is retracted.**  They are not rival triggers.

Surprise means: THE HELD MODEL NO LONGER DESCRIBES THE PLANT.  That is exactly
what `|| current map - held map ||` measures, and it is the definition rather
than a proxy for it.

What the seed implements today (`emp_note_program_surprise`) is an impoverished
special case of the same quantity:

| | today | the difference shape |
|---|---|---|
| how many consequences | ONE (normal load) | all six |
| how compared | a DECLARED threshold, `relative_normal_load_surprise` | the map against its OWN magnitude |
| scale | absolute | scale-free |
| what it can miss | any change that does not move normal load | — |

So the change is not a substitution to be A/B'd, it is a GENERALISATION: the
same notion, measured over the whole consequence vector instead of one
projection of it, and with the threshold removed because the model's own
magnitude supplies the comparison.

This also explains a result that was recorded as a curiosity in section 23.
Surprise fires twice per fault episode and never in nominal — directionally
correct, because normal load does move under these faults.  The difference
shape fires within 4-9 actions with a 2,500x-100,000x margin, because it is
looking at all of the model instead of one number from it.  The old test was
not wrong, it was narrow.

**Consequence for the build:** there is one consumer to wire, not two competing
ones.  Recalibration should trigger on surprise as generally measured, and the
authority-retaining response should run while the model is known stale.  Those
are the two halves of one mechanism, not two candidates.

## 32. THE ORDER OF SURPRISE — and why the attribution question kept failing

Owner: *"this is an order of surprise. Do a thing, it doesn't do what you
expect, is it that thing or is it the whole plant?"*

**Order 1** — did THIS THING do what I expected?  Local, and answerable only by
testing the thing.
**Order 2** — has the RELATIONSHIP between commands and outcomes moved?  The
whole map, and non-local by construction because the dynamics are shared.

**This names the error running through sections 15-29: attributing ORDER-2
evidence to ORDER-1 causes.**  Every failed instrument took an aggregate
residual — which cannot be local, because a shared plant contaminates every
effector's residual at once — and asked which effector owned it.  Six times.
The retraction in section 29 then over-generalised the failure into
"localisation is not recoverable from this data".  Localisation IS recoverable.
It is recoverable at order 1, by testing the thing, which is what a pilot does
and what the calibration probe already implements.

**Both orders are built and both are measured:**

| scenario | order 1: did the thing move? | order 2: did the map move? | reads as |
|---|---|---|---|
| nominal | no probe evidence | 0.002x, never fires | healthy |
| jammed_rudder | **rudder 0 of 10** | 8.6x at action 104 | **the thing** |
| saturated_elevator | **elevator 6/2** | 6.8x at action 109 | **the thing** |
| damaged_wing | all surfaces move | **205x at action 104** | **the plant** |

**The damaged wing is the case that separates them** — nothing is wrong with
any effector and everything is wrong with the map — and it requires no
inference from aggregate residuals at all.

**And the order-1 instrument's known defect is now nameable rather than
mysterious.**  The aileron reads "never moved" in every fault (4/4, 5/5, 4/4)
because it sits pinned at its travel limit: **saturated is not stuck.**  The
plant publishes the commanded position and the limit, so this is a comparison
that can be made rather than an artefact to be lived with — and fixing it is
what would make the order-1 column trustworthy on its own.

**The response differs by order, which is the point of distinguishing them:**
a thing that no longer works is removed from the control set (authority to
zero, which `f16_weight_authority_by_evidence` already does from evidence); a
plant that has moved is re-learned as a transform while authority over the
whole set is retained.  Same detection machinery, two different reactions, and
only the second one needs the corners.

## 33. SATURATION IS THE THIRD READING — and it is what the corners are actually for

Owner: *"saturated means you have used all your available control on that
effector and that you either need to a) use another (or multiple) effector(s)
to get the result you want or b) reconsider your goal."*

**Section 32 called the aileron reading an ARTEFACT.  It was not — it was the
instrument working, and being read against the wrong taxonomy.**  Saturation is
not a fault: the effector does exactly what it is told, and there is simply
none of it left.

Measured, commanded-versus-achieved per effector, post-onset:

| scenario | signature | reading |
|---|---|---|
| nominal | everything ranges freely, map stable | **healthy** |
| jammed_rudder | rudder pinned at **0.500 on 100% of actions**, and 0.5 is not a limit | **STUCK** |
| saturated_elevator | elevator commanded to ±1, achieved ceiling **0.050** | **SATURATED** |
| damaged_wing | all surfaces reach full travel, none persistently | **PLANT MOVED** (205x) |

All three separate cleanly and each is read DIRECTLY off commanded versus
achieved — no inference from aggregate residuals, no attribution.

**The correct saturation test is not "at ±1".**  This spike's probe used that
and mislabelled the elevator as free.  Saturation is **the achieved ceiling
falling below what was commanded**, whatever that ceiling turns out to be: the
elevator's is 0.050, exactly the scenario's clamp, and it is visible WITHOUT
knowing the clamp exists.

**Three readings, three responses, and this is the first principled account
this line has had of when a deliberation should open:**

| reading | response | whose job |
|---|---|---|
| STUCK | the thing is gone — remove it from the control set | `f16_weight_authority_by_evidence`, already built |
| **SATURATED** | **(a) recompose from other effectors, or (b) RECONSIDER THE GOAL** | `MotorCompose` for (a); **the corners for (b)** |
| PLANT MOVED | re-learn the map as a transform, retain authority over the set | recalibration as transform inference |

**The corners are for (b), and only for (b).**  Everything else this line has
pointed them at — fault kind, effector attribution, regime ladders — was
order-1 or order-2 work belonging to the motor layer.  A corner surrenders an
OBJECTIVE, and the condition that warrants surrendering an objective is that
the control to achieve it has been spent, which is exactly saturation.

That also explains the standing negative.  `speed_priority` was built for the
saturated elevator and measured useless there (0 adoptions in 40 episodes)
because it was gated on projected clocks and Pareto dominance rather than on
the one condition that means what it is for: the pitch control is spent, so
either compose pitch from something else or stop asking for that altitude.

## 34. SATURATED IS NOT "AT 100% TRAVEL" — it is 100% of available effect FOR THE DESIRED OUTCOME

Owner: *"saturated is also not simply '100%' - it is 100% of available effect
for the desired outcome."*

Section 33 tested saturation as achieved-ceiling-below-command, i.e. against the
effector's mechanical range.  That is still the wrong frame.  An effector can
range freely and buy NOTHING: the damaged wing's aileron sweeps its whole
travel and produces no additional roll —

| cmd | −1.0 | −0.8 | −0.5 | −0.2 | 0 | +0.2 | +0.5 | +0.8 | +1.0 |
|---|---|---|---|---|---|---|---|---|---|
| roll | −.039 | +.004 | +.019 | +.049 | +.060 | +.062 | +.058 | +.047 | +.074 |

— which is saturation FOR ROLL with no mechanical limit anywhere near.

Measured as the marginal effect on each group's primary outcome (does more
command buy more outcome?), outer half of the command range against the inner:

| scenario | elevator/pitch | aileron/roll | rudder/turn | throttle/forward |
|---|---:|---:|---:|---:|
| **nominal** | **0.98** | **1.00** | **1.00** | **0.89** |
| jammed_rudder | −0.02 | 3.15 | 5.27 | −0.60 |
| saturated_elevator | **−0.13** | −0.58 | 0.17 | 1.10 |
| damaged_wing | −0.74 | **−1.35** | −0.28 | −0.69 |

**Nominal is perfect** — every effector still buys outcome.  **The saturated
elevator is correctly flagged for pitch**, the fault it is named for.  **The
damaged wing has no effector with marginal effect left on its primary
outcome**, which is a complete account of why it crashes 5 of 10 and why
retaining authority is the only sane response: there is none left to spend.

**Defect in the measurement above, and it is the half of the owner's sentence
not implemented.**  It compares the outer slope to the INNER slope — a relative
test — so the jammed rudder reads "effect still available" at 5.27 when both
slopes are ~0.001 against nominal's 0.01.  A ratio is meaningless when both
terms are noise.  *"100% of available effect for the desired outcome"* means
available effect against the effect the OUTCOME REQUIRES, which is absolute.
The loop already declares what the outcome requires — the axis corrections in
`_axis_time_budgets` are exactly "actions to close the current error at the
declared authority" — so the comparison has both halves available and does not
need a constant.

**This is the quantity the whole line has been circling.**  Not which effector
broke, not what kind of fault it is, not how the plant changed: **how much of
the outcome I want can I still command?**  When that reaches zero the responses
are the owner's two — compose it from something else, or stop wanting it — and
the second is what a corner is.

## 35. AVAILABLE EFFECT SCALES WITH q — and stall is loss of effect, not a separate phenomenon

Owner: *"This also means that it scales with speed and air density and etc etc
- Stall is loss of effect."*

Control-surface moment scales with dynamic pressure, so available effect is not
a property of the effector — it is a property of the effector AND where in the
envelope you are.  Measured across the flight this line actually flies:

| scenario | q min | q median | q max | airspeed range m/s |
|---|---:|---:|---:|---|
| nominal | 1,982 | 3,856 | 4,730 | 76-112 |
| saturated_elevator | 3,131 | 13,169 | 23,894 | 82-197 |
| damaged_wing | **90** | 2,136 | 10,959 | **14**-158 |
| jammed_rudder | **0** | 2,543 | 30,467 | **0**-253 |

**q spans 0 to 30,467 Pa across flight seen.**  The damaged wing spends time at
one-fiftieth of healthy cruise; the jam reaches literal zero.  The same
deflection buys wildly different amounts of outcome depending only on
condition.

**So stall needs no separate detector.**  At 14 m/s the surfaces produce almost
nothing, and that is the SAME measure reaching zero — not a different
phenomenon with its own subsystem.  Loss of effect is loss of effect, whether
from a jam, a clamp, a damaged wing, or from having run out of air.  The
departure/alpha-recovery machinery in this seed is a special case of it.

**CONFOUND IN SECTION 34, stated plainly.**  The damaged wing reading "all four
effectors saturated" is partly just low q.  At 90 Pa nothing works, so of
course every marginal effect collapsed.  That measurement attributed to the
plant what belongs to the flight condition.  **Available effect must be read
against q, or slow flight is indistinguishable from damage** — and the plant
publishes `dynamic_pressure_pascals` every action, so the normalisation is
available and costs nothing.

**And this is what `speed_priority` actually is.**  It has never fitted the
corner framing because it is not a corner.  A corner SURRENDERS AN OBJECTIVE;
`speed_priority` BUYS BACK AVAILABLE EFFECT by raising q — which is the seed's
own Negev F-15 note, *"every control surface's moment scales with q, so flying
faster multiplies back up the stiffness and damping a fault removed."*  It is
response (a), recompose/restore, sitting in a set of (b)-type options and
scored against them by Pareto dominance.  **It never won because it was being
compared on the wrong axis**, and no repricing of that comparison could have
fixed it.

The closing shape of the whole spike:

    available effect for a desired outcome  =  f(effector, plant, q)

    it reaches zero by                       response
    -----------------------------------      ------------------------------
    the effector is gone (jam, clamp)        drop it from the control set
    the plant moved (damaged wing)           re-learn the map as a transform
    q is gone (slow, thin air, stall)        RAISE q -- speed_priority
    nothing can restore it                   reconsider the goal -- a corner

Four causes, one measured quantity, and only the last one needs the frontier.

## 36. NONE OF THIS IS AERONAUTICAL — the instruments transfer to wheels unchanged

Owner: *"This also is entirely agnostic - it works just as well for wheels."*

Checked rather than asserted.  `scripts/jabberwock_active_aero.py` boots the
SAME `embodied_motor_program` seed, builds the same `actuator_group` effector
models, and declares:

    CONSEQUENCES = forward, lateral, vertical, roll, pitch, turn,
                   normal_load, drag, energy

— the same six components the F-16 uses, plus `normal_load`, which IS the
wheeled condition variable.  Every instrument built in this spike reads only
`mean_<consequence>` per model per command level, `actuator_group`,
`specified_command_level` and `state_effector_position`.  **Not one of them
contains anything aeronautical.**  They run on that domain unchanged.

The correspondence is exact where it decides anything:

| | aircraft | wheels |
|---|---|---|
| available effect scales with | q = ½ρV² | μ·N (grip x normal load) |
| loss of effect is called | **stall** — more alpha, no more lift | **understeer** — more lock, no more cornering force |
| restoring the condition | raise q: GO FASTER | raise N or unload the tyre: SLOW DOWN |

**Understeer IS stall.**  Both are the marginal effect of a control on the
desired outcome reaching zero, and a driver winding on more lock is doing
exactly what a pilot pulling more alpha is doing: more input, no more outcome.

**And the restoring action points in OPPOSITE directions on the speed axis**,
which is why the general form has to be derivation item 8's *"CHANGE THE
OPERATING CONDITION so the fixpoint stays attainable"* and not "go faster".
`f16_speed_priority_on_authority_loss` is the aircraft's instance of a
domain-general move, and reading it as the general move would export a sign
error to every ground vehicle.

This is also what `docs/embodied_pareto_profiles.md` claimed from the start —
*"Humanoids, racing cars, and aircraft all face the same kind of decision"* —
which was an architectural intention with no shared measured quantity behind
it.  There is one now:

    how much of the outcome I want can I still command,
    given this effector, this plant, and this condition?

The natural second test is the active-aero domain itself, which exists in this
tree and is literally about modulating downforce — i.e. about modulating
available effect directly, which no aircraft in this line can do.

## 37. CORRECTION to section 36 — the restoring DIRECTION must be derived, not declared

Owner: *"the aerodynamic car can actually understand and choose to go faster to
increase grip to reduce understeer, whereas a typical car control system does
not map those dynamics and is essentially bolting on a forced condition."*

**Section 36's table is wrong and is retracted here.**  It declared the
restoring direction per domain — *"aircraft: go faster; wheels: slow down"* —
which is precisely the bolted-on forced condition this architecture exists to
avoid.  A sign was hardcoded that has to be DERIVED.

For an aerodynamic car the naive answer to understeer is to slow down, and it
can be exactly wrong: downforce scales with V², so more speed can mean more
normal load, more grip, and LESS understeer.  Which way it goes depends on
where in the envelope you are — grip load-limited (go faster) or already at the
friction circle (slow down) — and that is a question about the plant, not about
the vehicle class.

**So the general form is one step further back than section 36 had it:**

    the restoring action is whichever change in the operating condition
    INCREASES available effect for the desired outcome

    aircraft:  d(available effect)/dV > 0 essentially always     -> faster
    aero car:  d(available effect)/dV changes SIGN in the envelope -> it depends
    plain car: no aero term at all                                -> slower

The agent does not need to be told which of these it is.  It measures available
effect (section 34) and the condition (section 35), both already published
every action, and reads the dependence off its own held model — which is what
`TimeInfer` and the order-N machinery do for every other quantity in this line.

**And this is the concrete argument for the architecture, stated in a form that
can be tested.**  A conventional stack cannot make this choice, not because its
controllers are poor but because it never represents the chain: an aero map, a
traction controller and a stability system, each tuned, none sharing a
quantity.  `speed -> downforce -> normal load -> available lateral effect` is
one causal chain here, in one model, in the same units as everything else — so
"go faster to understeer less" is available to it as a DERIVED consequence
rather than as a special case someone anticipated.

It is the same move as this seed's Negev F-15 note (full afterburner to recover
authority), which reads as counterintuitive precisely until the chain is
present, and then reads as arithmetic.

**Testable claim, for whoever builds it:** in the active-aero domain, an agent
holding this chain should choose to ADD SPEED under load-limited understeer and
SHED it at the friction limit, from the same rule, with no branch naming either
case.  That is a measurement this tree can make — the domain exists, and no
aircraft in this line can modulate its own available effect the way that car
can.

## 38. THE CLOSING PIECE — same model, same situation, different GOAL, different corner

Owner: *"in a racing car, your goal is to go faster, so the best corner
selection is to increase speed to increase grip.  In a normal driving
situation, your goal is safety and comfort, so the selection is to slow down
(assuming it can be done safely).  Same model.  Same situation, different
outcomes."*

This is the first correct account of what the corners are for that this
document has produced, and it separates two questions this line has had fused
since block 1:

    1. WHAT CAN I DO?    available effect for the desired outcome, measured
                         (sections 34-37) -- physics, no preferences in it
    2. WHAT SHOULD I DO? the declared objective set and which objective the
                         situation currently prioritises -- preferences, no
                         physics in it

**A corner is the answer to (2), chosen from what (1) leaves available.**
Understeer with grip load-limited leaves both "add speed" and "shed speed"
physically available; the racing objective set takes the first and the road
objective set takes the second.  Same model, same plant, same instant,
different corner — and nothing about the aerodynamics differs between them.

**This is why four powered blocks came back negative, and it is not a scoring
problem.**  The F-16 frontier scores corners on ACHIEVABILITY CLOCKS — which is
question (1) — and then lets Pareto dominance select, which presumes question
(2) does not exist.  It answers "what can I still do?" and treats the answer as
"what should I do?".  No repricing of that comparison could have fixed it,
because the missing term was never a price; it was the goal.  Three repricings
were tried in this line's history (flat 0.0, the horizon, the ledger), each
changed WHICH corner always won, and none made the choice depend on what was
wanted.

**And the switch already exists, disconnected.**
`f16_choose_regime_situational_priority` picks the priority axis from live cues
— terrain proximity below 500 m favours altitude, airspeed below 70 m/s favours
speed, otherwise heading — and it demonstrably varies WITHIN a single flight
(measured: axis 1 at three deliberations, axis 0 at two, same episode).  That
rule is the road-car / racing-car switch.  It is computed every deliberation
and then consulted only AFTER dominance has already reduced the frontier to one
candidate, so it decides nothing.

**The whole architecture, as this spike leaves it:**

    measured, physics only          available effect = f(effector, plant, condition)
    measured, physics only          has the map moved?  (the difference shape)
    declared, preferences only      the objective set + the situational priority
    the decision                    among corners the available effect permits,
                                    take the one the prioritised objective wants

Nothing in the first two knows what is wanted; nothing in the third knows what
is possible; the decision is where they meet.  The F-16 has been trying to make
that decision inside the first two, and the situational priority — the only
part that carries a preference — has been structurally unable to reach it.

## 39. THE BUILD FAILS BY CONSTRUCTION — preference has no independent representation

Section 38 concluded the fix was a reordering: let the situational priority
select among all available corners rather than among whatever dominance left.
**Built, and it is VACUOUS.  Reverted.**

`_priority_value_from_axes` reads the prioritised axis's value **off the
candidate's own six axis values** — the same six axes dominance ranks.  So if A
dominates B, A is no worse than B on all six, therefore no worse on whichever
one the priority selects.  **Argmax-by-priority can never disagree with
dominance except in ties.**  Reordering them changes no verdict, in any
scenario, ever.

An existing gate test, `test_dominated_candidate_is_never_selected`, states the
invariant the change violated and states it correctly: *"the dominated point is
never the verdict even if its own situational-priority reading looks larger in
isolation."*  It failed immediately.

**So the finding is sharper than section 38's framing anticipated, and it is
structural rather than a tuning matter:**

> This architecture cannot currently express "same situation, different goal,
> different corner" AT ALL — because the goal is encoded as a CHOICE AMONG THE
> SAME AXES that determine dominance.  Preference has no representation
> independent of achievability.

Choosing which achievability axis to read is not a preference.  It is a
projection of the physics onto one of its own coordinates, and every candidate
that is better at physics is automatically better at the projection.  The
racing car and the road car do not differ in which achievability axis they
read; they differ in what they are TRYING TO DO, and there is nowhere in this
contract to say that.

**What would actually be needed, and it is a contract change rather than a rule
change:** an objective that is not one of the measured axes — a declared want,
against which candidates are ranked — so that two agents holding identical
axis values and identical dominance can still select different corners.  The
axes then answer "what can I do" and the objective answers "what should I do",
and dominance keeps its proper and narrow job of discarding the strictly worse.

**Recorded as a negative on the build, not on the idea.**  The separation of
the two questions (section 38) stands and is measured; what is now known is
that this contract cannot hold the second one, and that no reordering of the
first can fake it.

---

## 40. WHERE THIS GOES — the manifold of possibilities, and the goal choosing within it

Owner: *"the collapse of goal vs possibilities is where we need to go.  The
plant and effectors provide the manifold of possibilities, the goal chooses
from within."*

This is the design the whole spike converges on, and every measured result in
this document fits it.  Stated as a contract:

**THE MANIFOLD — physics, measured, no preference in it.**
The plant, the effectors and the condition jointly determine WHAT OUTCOMES ARE
STILL COMMANDABLE.  That is a SET — a region in outcome space — not a ranking
and not a scalar per axis.  Everything sections 34-37 measured is a coordinate
of it:

* available effect per outcome = how far this outcome can still be driven
  (section 34), which is what saturation exhausts;
* it scales with the condition, q or grip (section 35), which is why stall is
  loss of effect rather than a separate phenomenon;
* it moves when the plant moves (section 28-30), which is what the difference
  shape detects at 90x;
* it loses a dimension when an effector is gone (section 32, order 1).

**THE GOAL — declared, no physics in it.**
A want, in the same outcome space.  Not one of the axes; not a choice among
them.  Two agents with identical manifolds and different goals must be able to
select differently — that is exactly what section 39 proved this contract
cannot currently express, because the "priority axis" is a projection of the
physics onto one of its own coordinates and can never disagree with dominance.

**THE DECISION — where they meet.**

    goal INSIDE the manifold    ->  fly it.  No deliberation is warranted, and
                                    none should open.
    goal OUTSIDE the manifold   ->  two responses, and only two:
                                    (a) GROW THE MANIFOLD -- change the
                                        operating condition so more becomes
                                        commandable (raise q; add downforce).
                                        This is what `speed_priority` is, and
                                        why it never fitted a set of corners.
                                    (b) SHRINK THE WANT -- surrender or
                                        substitute an objective.  THIS, AND
                                        ONLY THIS, IS A CORNER.

**This is what makes the four powered blocks legible.**  They deliberated on an
evidence-starvation clock and selected by dominance over achievability axes —
that is, they opened deliberations without asking whether the goal was outside
the manifold, and then chose without a goal.  The corner set was scored on
question one and asked to answer question two.  No repricing could fix it and
three repricings did not.

**What is already built and reusable.**  The manifold's coordinates are
measured and committed as telemetry (available effect, the condition, the
difference shape, the order-1 probe).  The response machinery exists — the
motor composer for "get it elsewhere", `speed_priority` for (a), the corner set
for (b).  What is missing is one thing: **a declared goal that is not a
coordinate of the manifold**, and the containment test between them.

**What would have to change.**  A contract change, not a rule change: the
consumer declares what it WANTS in outcome space, the general seed computes
whether the want lies inside what is still commandable, and a deliberation
opens on that containment failing rather than on evidence starving.  Every
piece of evidence in this document points at that shape, and no measurement in
it contradicts the shape — but nothing in it tests the shape either, and it
should be prereg'd and measured like everything else here rather than adopted
because it is tidy.

## 41. THE CONTAINMENT TEST, BUILT (v8.23.0) — two axes work, one has a unit error

`f16_publish_goal_containment` stamps, per declared objective: how far that
outcome can be driven over the control horizon by the best effector still
MEASURED to affect it (`f16_manifold_reach_*`), how far it must be driven to
meet the want (`f16_goal_gap_*`, the loop's own tracking error), and whether the
want lies outside the reach (`f16_goal_outside_*`).

The reach is measured off the learned map, so it already carries everything
sections 34-37 established without naming any of it: a gone effector
contributes nothing, a saturated one contributes no more, a moved plant moves
it, the condition scales it.

**Decides nothing.**  Deliberation still opens on evidence starvation.

Fraction of post-onset actions with the want OUTSIDE reach:

| scenario | altitude | heading | speed | alt RMSE |
|---|---:|---:|---:|---:|
| nominal | **0.99** | **0.00** | **0.00** | 323 |
| jammed_rudder | 0.90 | **0.72** | 0.84 | 6,929 |
| saturated_elevator | 0.96 | 0.00 | **0.86** | 5,318 |
| damaged_wing | 0.88 | 0.00 | 0.00 | 12,242 |

**Heading and speed work.**  Nominal reads the goal INSIDE reach on both; the
jammed rudder reads heading outside 0.72 of the time, which is what it is; the
saturated elevator reads speed outside 0.86, which is right — it dives and
overspeeds.  That is the containment test doing what the contract says.

**Altitude is dimensionally broken, and NOMINAL IS THE TELL:** 0.99 outside
while flying perfectly at 323 ft.  Reach 2.616 against a gap of 61.889 —
`mean_vertical` is not metres per action, so that comparison is meaningless.
Heading (rad/action against rad) and speed (m/s per action against m/s) happen
to be commensurable; altitude is not.

**The fix is specific and already in the seed.**  `_achievable_vertical_speed()`
returns metres per second and `altitude_correct` already uses it to compute
actions-to-close, so the altitude reach is that x duration x horizon.  Not
applied here: the rule is telemetry, nothing acts on it, and this session has
reverted three end-of-session "small fixes" already.

**What this establishes and what it does not.**  It establishes that the
containment question is COMPUTABLE from what the agent already measures, and
that on the two axes where the units line up it separates healthy from faulty
in the right direction on the right axis.  It does not establish that
containment failure is a better deliberation trigger than evidence starvation —
that needs the altitude axis fixed and a matched block, and it should be
prereg'd like everything else here.

## 42. UNITS FIXED, AND THE MARGIN IS A LOG (v8.24.0)

Owner: *"the trick is that it's in log so it's either 'heaps' (in terms of the
decision) or 'I need to care very much'."*

**The unit error, found by reading the plant rather than guessing.** Every
consequence this motor model learns is a per-action CHANGE IN RATE — `vertical`
and `forward` are delta m/s, `turn` is delta rad/s.  So a RATE goal integrates
once and a POSITION goal integrates twice:

    speed    (rate)      reach = rate_change x horizon
    heading  (position)  reach = rate_change x horizon x (horizon x duration)
    altitude (position)  same

Section 41 integrated once for all three, so heading and altitude were short by
`horizon x duration` = 8.  Speed was right by the accident of being the only
rate-valued objective — which is why it was the axis that read sensibly.

**And the margin is now a RATIO, because its LOG is the decision quantity.**  A
large positive log is "heaps, this does not bear on anything"; a log near zero
is "I need to care very much".  A boolean threw all of that away.  It also
makes the reading robust to exactly the uncertainty units carry: **a unit error
is a constant OFFSET in log space** — it moves where zero sits, it does not
destroy the shape or the dynamics.

`log10(reach / gap)`, median over post-onset actions:

| scenario | altitude | heading | speed | alt RMSE |
|---|---:|---:|---:|---:|
| nominal | −0.49 | **+2.04** | **+1.39** | 323 |
| jammed_rudder | −0.59 | **+0.60** | **−0.09** | 6,929 |
| saturated_elevator | −0.59 | +3.20 | **−0.13** | 5,318 |
| damaged_wing | −0.11 | +1.68 | +1.04 | 12,242 |

**Heading discriminates the jam**: +0.60 against +1.68 to +3.20 elsewhere — the
tightest heading margin in the block, on the scenario that is a heading fault,
while still nominally inside.

**Speed discriminates the jam and the elevator**: −0.09 and −0.13, both sitting
ON the boundary, against +1.04 and +1.39 for the other two.  Both are the
scenarios that dive and overspeed.

**Altitude reads negative everywhere, nominal included (−0.49), and this is NOT
resolved.**  It may be honest: this line documents a standing ~300 ft nominal
altitude offset the controller never closes, and 323 ft RMSE is the pinned
value — if the altitude reference is unreachable in trim then "outside reach"
is the correct reading and nominal is not a counterexample.  It may also be a
residual unit error.  **The two cannot be separated from this measurement and
neither reading is adopted.**  What the log form buys is that the ambiguity is
a constant offset on that one axis: the shape survives it, which is why the
damaged wing still reads distinctly (−0.11) from the two that are diving
(−0.59).

Still decides nothing.  Deliberation continues to open on evidence starvation.

## 43. THE ALTITUDE REFERENCE IS REACHABLE — the reading was wrong, and fixing it makes containment work

Checked directly rather than assumed either way.  In nominal the aircraft
CROSSES THROUGH the reference (error −242 → −43 → +34 → +95 m), so it is not
holding an unreachable offset, and it demonstrably achieves vertical rates to
**16.7 m/s against a declared 20**.  Closing the median 70 m gap takes **6.2 s
at observed rates**, inside the 8 s horizon.  **The goal is comfortably
reachable and section 42's "outside" reading was mine, not the plant's.**

**The error, and it was the same one twice:** integrating an ACCELERATION FROM
REST.  `mean_vertical` is 0.033 m/s of velocity CHANGE per action, so eighty
actions build 2.6 m/s — but the aircraft does not start from rest and is not
limited by how fast it can build a rate.  It is limited by the rate it can
SUSTAIN.

    a RATE goal      reach = achievable rate change x horizon
    a POSITION goal  reach = achievable SUSTAINED RATE x horizon x duration

The sustained rates are ones this loop already declares and already conditions
on flight state (`_achievable_vertical_speed()`; `g tan(max bank) / airspeed`),
so they scale with the condition — section 35's q-dependence in another form.

**With that, containment works** — `log10(reach/gap)`, median post-onset:

| scenario | altitude | heading | speed |
|---|---:|---:|---:|
| **nominal** | **+0.41** (out 0.12) | **+1.09** (0.00) | **+1.39** (0.00) |
| jammed_rudder | −1.16 (0.82) | **+0.18** (0.38) | −0.09 (0.84) |
| saturated_elevator | **−1.03** (0.91) | +1.91 (0.09) | −0.13 (0.86) |
| damaged_wing | **−1.28** (0.90) | **−0.03** (0.52) | +1.04 (0.00) |

**Nominal wants only what it can have** — all three inside.  **Every fault has
something outside, on the axis that scenario actually breaks:** the jam tightest
on heading (+0.18, at the boundary), the saturated elevator worst on altitude
with heading comfortable at +1.91, the damaged wing worst on altitude and
marginal on heading with speed untouched.

And the log reading is the two registers it was built for: +1.09 to +1.39 is
"heaps, does not bear on anything"; +0.18 and −0.03 are "I need to care very
much".

**LIMITATION, recorded.**  The position axes' reach is declared-and-condition-
scaled rather than learned off the map, so it does not shrink when an effector
degrades — only the speed axis is fully measured.  Closing that needs a learned
SUSTAINED rate, which this motor model does not hold; it learns per-action
changes.  **Still decides nothing**: deliberation continues to open on evidence
starvation, and whether containment failure is the better trigger remains the
untested step.

---

## 44. CORRECTION — "nominal byte-identical" was FALSE from v8.15.0 onward

**Measured: removing `f16_weight_authority_by_evidence` from the manifest
restores nominal to 323.28346789186793 ft exactly.  With it, nominal reads
323.05407206941595.  The rule moves the aircraft in HEALTHY FLIGHT.**

Every commit from `b4070a3c` (v8.15.0) onward asserting *"nominal flight
unchanged / byte-identical at 323.28346789186793 ft"* is **wrong**:
`b4070a3c`, `d74bfd0f`, `453fd9ee`, `5cb5682a`, `79c16e6c`, `de6fe81e`,
`d359e656`, `64b3dbf7`, `5c988380`.  The claim was checked to three significant
figures ("323") and reported as full-precision identity.

**The cause is a defect this document already recorded and then contradicted.**
Section 20 states plainly: *"the throttle reads 0.11 in NOMINAL ... it is wrong
and it is not fixed."*  `log_authority` is read by
`embodied_motor_program`'s composer (`Sum(members, Neg(log_authority))`), so a
throttle down-weighted to 0.11 in healthy flight CHANGES COMPOSITION and
therefore changes the flight.  **The same document asserts the defect and
asserts that it cannot have this consequence, and I never reconciled them.**

**Why the throttle reads low, now traced:** the tracking test compares
`specified_command_level` (the model's command level, −1..1) against
`state_effector_position` (the achieved position, 0..1 for a throttle).  Those
are different scales, so the "gap" is not a gap and a throttle that is holding
station reads as commanded-and-not-moving.  Sections 33 and 43 both found unit
errors of exactly this family; this is a third.

**Standing trade-off, not resolved here because it is a real one:**

* KEEP the rule — the rudder-prior bug stays fixed (rudder authority 1.00 in
  nominal and under a saturated elevator, 0.09 under the jam), at the cost of
  perturbing healthy flight by 0.07% through a reading known to be false.
* REVERT it — nominal returns to the pin and the invariant this line guards
  most closely ("the monitor does not touch healthy flight") holds again, at
  the cost of restoring a bug that retires the rudder's prior under every
  fault.
* FIX the scale mismatch first, which would plausibly give both, and is a
  fourth unit correction in a row.

**The process failure is the reportable part.**  A measured defect and a claim
incompatible with it sat in the same document for eleven commits.  A pinned
value exists precisely so that this is caught, and I read it at three
significant figures.

## 45. THE FIX — evidence that does not exist is not evidence (v8.29.0)

Owner: *"the problem is that it's weighting authority by evidence it does not
have.  Evidence that doesn't exist isn't evidence, it's just confusion."*

Section 44 traced the moved pin to a scale mismatch —
`specified_command_level` (−1..1) against `state_effector_position` (0..1 for a
throttle).  **That mismatch is real and it is not the fault.**  Fixing it would
have treated the symptom.  The fault is that **zero successes among zero tests
was read as LOW AUTHORITY instead of as NO READING**, and the scale bug
mattered only because it manufactured fake evidence for that misreading to
consume.

This is the first-class-absence discipline this line applies everywhere else,
and which this document invoked for the containment guard four sections ago —
*"an unlearned model is not evidence that a goal is unreachable; it is evidence
of nothing"* — and then failed to apply to authority.

**The fix was already in the tree, measured, and unused.**  Section 24
established that probe-restricted evidence is strictly better than passive
evidence on every scenario, and that **healthy flight produces NO probe
evidence at all** because no calibration pass runs there.  The weighting was
reading the passive counts anyway, for a dozen commits.

`f16_weight_authority_by_evidence` now reads `f16_probe_*`:

| scenario | elevator | aileron | rudder | throttle | nominal pin |
|---|---:|---:|---:|---:|---|
| **nominal** | **1.00** | **1.00** | **1.00** | **1.00** | **323.28346789186793** |
| jammed_rudder | 0.60 | 0.33 | **0.09** | 0.71 | — |
| saturated_elevator | **0.33** | 0.33 | **1.00** | 0.78 | — |
| damaged_wing | 0.33 | 0.33 | 0.45 | 0.78 | — |

**Both, and by construction rather than by luck.**  Healthy flight is untouched
because there is nothing to read, not because the reading happens to come out
near 1.  The rudder-prior bug stays fixed — 0.09 under the jam, 1.00 under the
saturated elevator — and the elevator is independently down-weighted to 0.33 in
its own scenario, which the rule this replaced could never do.

The pinned nominal value is restored exactly, and the trade-off section 44 left
open does not need to be taken.

## 46. CONTAINMENT WIRED (v8.30.0) — the contract is live, and the effect is UNEXPLAINED

Three attempts failed before the cause was found, and the cause was not what any
of them assumed.  **`f16_note_flight_path_progress_evidence` sets
`regime_urgency` to a LITERAL 1.0.**  The general seed's urgency-weighted
absence integral has therefore always run at fixed-horizon semantics on this
consumer — the whole contract declared, written every action, and inert.  A
competing writer is simply overwritten inside the `run_rules` fixpoint whatever
its order, which is why attempts 2 and 3 measured urgency at 1.0 throughout.

That rule is one of the twelve recovered data blobs, so **only its urgency
effect was re-expressed as source**; the evidence ratchet, error EMA and
sequence bookkeeping remain recovered data and are still owed a full
re-expression (~27k characters of term tree — rewriting it unverified would be
a worse risk than leaving it, and the seed is the ground truth any
re-expression must regenerate byte-identically against).

Containment publishes `f16_containment_urgency` = `max(gap/reach, 1)` guarded on
an EVER-CALIBRATED latch (`calibration_complete` is zeroed by recalibration,
which made attempt 2 inert precisely during faults).

**Urgency is live:** nominal median 1.00 / p95 1.30, saturated elevator 10.83,
jam 14.71 (p95 248), damaged wing 19.46 (p95 343).

| scenario | escalated | crash | alt RMSE | baseline n=10 |
|---|---|---|---|---|
| **nominal** | **0/5** | 0/5 | 316 | 0/10, 0/10, 360 — **pin exact** |
| jammed_rudder | 3/5 | 2/5 | 11,437 | 8/10, 2/10, 7,722 |
| saturated_elevator | 0/5 | 0/5 | 4,011 | 0/10, 0/10, 3,709 |
| damaged_wing | **0/5** | 2/5 | 9,253 | **9/10**, 5/10, 9,992 |

**HELD:** healthy flight untouched, nominal pin exact at
323.28346789186793 ft, no nominal escalation.

**UNEXPLAINED, and recorded as such rather than reasoned away: the damaged wing
went from escalating 9 of 10 to 0 of 5.**  Higher urgency should make the
absence integral cross its horizon SOONER and escalate MORE, not stop
escalation entirely.  The jam's altitude RMSE also rose 7,722 → 11,437.  n=5 is
not a distribution and no crash rate is claimed, but the escalation collapse is
structural, not sampling.

**NOT VALIDATED.**  This is committed as a measured state with a known anomaly,
not as an improvement.  The wing's escalation collapse must be explained before
any of it is trusted, and the obvious next probe is whether the absence integral
is being reset by evidence faster than urgency can accumulate it — which would
mean urgency cannot matter while evidence keeps arriving, and that the trigger
this line actually wants is containment against the EVIDENCE path rather than
through it.

## 47. THE ESCALATION COLLAPSE EXPLAINED — deliberation CHURN, not evidence outrunning urgency

Section 46 left the wing's 9-of-10 → 0-of-5 escalation collapse unexplained and
named the obvious hypothesis: evidence resetting the absence integral faster
than urgency accumulates it, so urgency could never matter.  **Measured on a
damaged-wing episode, that hypothesis is FALSE.**

| quantity | damaged_wing post-onset (891 actions, horizon 80) |
|---|---|
| absence integral | median 65.3, max 200 — **crosses 80 on 0.42 of actions** |
| integral resets | 103 (evidence_seq advanced 109 times) |
| **deliberations** | **98 opened, 98 closed**, deliberating 0.42 of actions |
| deliberation integral | max 200 — some DO run long enough |
| urgency | median 19.5 |

Urgency is doing exactly what it should: the integral crosses its horizon
constantly and **98 deliberations open in one episode, against roughly 2
before**.  Evidence is not winning the race.

**The failure is downstream.**  Those 98 deliberations average ~3.8 actions
each and close before reaching the window a verdict needs, so ninety-eight
openings produce ZERO escalations.  That is deliberation CHURN.

**And it is the same failure as attempt 1, by a different route.**  Attempt 1
opened deliberations directly and reset `regime_deliberation_integral` each
time.  This makes the ABSENCE integral cross so fast that deliberations reopen
the instant they close.  Either way no deliberation survives to a verdict, and
the wing's escalation collapse follows.

**What this says about the design, and it is more useful than the fix would
be:** a continuously-true condition cannot drive the OPENING RATE of a process
that needs a long uninterrupted window to conclude.  Containment is true on
0.82-0.91 of post-onset actions by construction — it is a state, not an event —
and the deliberation is an 80-action process.  Feeding a state into an opening
trigger produces churn whatever the coupling, and both attempts prove it
independently.

Containment therefore belongs where a state belongs: in what the deliberation
DECIDES (which corner, given what is still reachable), not in when it starts.
The evidence-starvation trigger is an EVENT — progress stopped — and events are
what should open processes.  That inverts the framing sections 38-46 worked
under, and it is the first account that explains all three failed attempts with
one mechanism.

## 48. WIRING REVERTED — containment DECIDES, it does not TRIGGER

The v8.30.0 wiring is reverted.  Containment returns to what section 43
established and section 47 explains: a measured STATE, stamped as telemetry,
consumed by nothing.

**Why, in one line:** containment is true on 0.82-0.91 of post-onset actions by
construction, and a deliberation is an 80-action process.  A state cannot drive
the opening rate of a long process without churning it, and three attempts
demonstrated that with three different couplings:

| attempt | coupling | result |
|---|---|---|
| direct opener (cre v7.2.0) | opens, resetting `regime_deliberation_integral` | ALL escalation removed |
| urgency via `calibration_complete` | inert — recalibration zeroes that flag | urgency 1.0 at median, p95 AND max |
| urgency via ever-calibrated latch (v8.30.0) | absence integral crosses constantly | 98 deliberations, ~3.8 actions each, 0 escalations |

The third is the informative one because it WORKED mechanically — urgency live
at 19.5 median, 98 openings against roughly 2 — and still produced nothing,
because ninety-eight deliberations that each die in four actions decide less
than two that run to term.

**The role containment actually has** is the one sections 38-40 derived and the
wiring attempts then walked away from: *the plant and effectors provide the
manifold of possibilities, the goal chooses from within.*  Containment BOUNDS
THE OPTION SET.  It says which corners are still reachable at the moment a
decision is being made — which is an input to WHAT IS DECIDED, not to WHEN
deciding starts.  Evidence starvation is an EVENT (progress stopped) and events
are what open processes.

**What is kept, and it is not nothing:**

* containment measured on three axes, with nominal inside reach on all three
  and every fault outside on the axis that scenario breaks (§43);
* the finding that `f16_note_flight_path_progress_evidence` sets
  `regime_urgency` to a LITERAL 1.0, so the general seed's urgency-weighted
  absence integral has always run at fixed-horizon semantics on this consumer —
  a live contract, declared and inert, which nothing had noticed;
* the churn mechanism itself, which explains all three failures with one cause
  rather than three bugs.

**State:** back to `4250dac0` for scripts, seeds and tests.  Nominal pin exact
at 323.28346789186793 ft, containment telemetry still stamped, 48 tests green.

---

## 49. THE SMUGGLED BINARY — a corner COMPENSATES, it does not give up (v8.32.0)

Owner: *"this was a smuggled assumption.  'giving up' a corner isn't giving up.
it's compensating, and the implicit binary is the problem."*

Block Q is reverted, and the reason it failed is upstream of anything it did.
It bounded a menu whose members are declared as `keeps=(True, False, True,
True, True, False)` — **a bool per axis: KEPT (scored on its achievability
clock) or SURRENDERED (scored at the horizon).**

**That binary is the sole origin of the pathology this line has fought since
block 1.**  A surrendered axis scoring the CEILING is why the corner that gives
up the most dominates; four successive repricings (flat 0.0, the horizon, the
ledger, the two-column form) each only changed WHICH corner always won (§27).
There is no ceiling-versus-floor asymmetry to price if there is no surrender.

**A corner does not abandon an objective.  It REALLOCATES limited authority
away from it toward another.**  `speed_priority` is the clearest case and never
fitted the old framing: it does not surrender altitude, it SPENDS altitude to
buy control authority through dynamic pressure (§35).  A trade.  The corner IS
the compensation.

**And this is what makes a dynamic library possible at all (§8).**  Allocations
are continuous, so they can be interpolated, composed and inferred the way this
tree already grows every other representation.  Binary tuples give 2^6 discrete
points, hand-picked down to five — and a fixed library cannot be repaired by a
better selection rule, which is what blocks 1, 2, 3, Q and four repricings each
demonstrated separately.

**Landed as a pure representational change, deliberately a no-op.**
`keeps: tuple[bool]` becomes `shares: tuple[float]`, and `_axis_value` now
interpolates between the driven reading and the undriven one instead of
branching on a bool.  1.0 and 0.0 reproduce the old KEPT and SURRENDERED
readings exactly.

**Verified: every rule body byte-identical to the binary version**, rule count
unchanged, nominal exactly on the pin at 323.28346789186793 ft, jam unchanged,
48 tests green.  The representational change and any behavioural change are
therefore never measured together — which is the discipline that would have
caught three of this session's reverted builds.

**No corner declares an intermediate share yet, and none should until a
generator does it.**  Hand-authoring `shares=(0.6, 0.3, ...)` would just be
five hand-picked points again, at higher resolution.  The next rung is corners
GENERATED — composed by `MotorCompose` from effector primitives, grown by the
sd loop's Occam ladder (recognise → transform → infer → mint), bounded by what
containment says is reachable, and selected by containment rather than
dominance.  The representation now admits that; it did not before.

## §50 — Corners are GENERATED (v8.33.0 → v8.34.0)

The first corner in this tree that nobody wrote. Its allocation is computed per
axis, every deliberation, from the containment margin `reach / gap` (§43) —
there is no `shares` tuple in its body, and the gate in
`test_f16_consumer_declares_pareto_regime_candidates` now asserts that a
literal one has not crept back in.

**Minted at the HELD ordinal, deliberately.** A generated corner has no
downstream implementation: the ordinal→flight mapping (`f16_adopt_metastable_trim`,
the orbit and priority overrides) is hand-coded per NAMED corner, so a genuinely
new ordinal would be selected and then flown by nothing. Minting at the
incumbent's ordinal makes adoption a no-op, which is what lets the question be
measured in isolation: **would a generated allocation win the frontier against
five hand-authored ones?** Both pins are EXACT (nominal `323.28346789186793`,
jam `6928.583937100404`) at v8.33.0 AND v8.34.0 — the flight never moved, so
nothing below is confounded by a changed trajectory.

### The first formula was wrong, and the probe said so

v8.33.0 read the share as *what fraction of authority this objective NEEDS*:
`share = 1/margin` for a reachable axis, `0` for an unreachable one. It is a
real quantity and it is the wrong argument for `_axis_value`, whose two poles
are the DRIVEN and UNDRIVEN readings of the achievability clock.

Measured, `damaged_wing` action 128: heading margin **32** — trivially
reachable — took share `0.031` and scored **104.6** instead of 1024, and
`fixed_point` dominated the generated corner on an axis it was comfortably
MEETING. A low share had two opposite causes — *needs no authority* and
*cannot use authority* — and the interpolation collapsed them onto one value.

v8.34.0 uses `share = min(margin, 1)`: the degree to which the objective is
ACHIEVED. An objective that is met scores as met however cheaply; only a
genuinely unreachable one slides toward the undriven reading, in proportion.
The allocation reading is not wrong — spare authority freed from a cheap
objective is a fact about the motor program, and it belongs at the composer,
not on the frontier.

### What the generated corner does (damaged_wing, 7 deliberations)

| action | alt margin | hdg margin | generated (alt, hdg) | on frontier |
|---|---|---|---|---|
| 128 | 1.83 | 32 | 1024, 1024 | yes |
| 316 | 0.17 | 0.534 | **652.3, 35.5** | yes |
| 477 | 0.065 | 0.296 | **472.9, 53.1** | yes |
| 638 | 0.042 | 1.66 | 258.7, 1.0 | no |
| 799 | 0.024 | 0.48 | 183.9, 0.5 | no |
| 882 | 0.029 | 0.195 | 10.6, 199.9 | no |
| 965 | 0.005 | 7.57 | 1024, 1024 | yes |

Three things this establishes:

1. **It is genuinely continuous.** 35.5, 53.1, 199.9, 10.6, 258.7, 183.9 are
   values no hand-authored corner can express — the five literal corners take
   exactly two values per axis, the driven and undriven clock readings.
   Non-dominated in **4/7**.
2. **It degenerates to "hold" when everything is contained** (128, 965 —
   byte-identical to `fixed_point`). Not designed; it falls out. The generator
   does not mint novelty when recognition suffices, which is the sd loop's own
   Occam ordering appearing at the corner grain without being imposed.
3. **Where it loses, it loses for being honest.** At 638 it prices a 4%-reachable
   altitude at 258.7 and is dominated by `fixed_point` pricing the same
   altitude at 597. Dominance rewards the corner that CLAIMS more, and the
   generated corner is the only one reporting what the plant will actually
   give. This is now direct measured evidence for the standing instruction
   that **containment decides, not dominance** (§3) — the selection rule, not
   the corner library, is what is left blocking.

### Owed

The allocation currently only reaches the SCORE. For a generated corner to be
FLOWN, the allocation has to drive the targets directly rather than through a
named regime — that is the same wiring the composer needs to spend freed
authority, and it is the next rung.

## §51 — What this session actually was: metacognition about dimensions, done in the wrong layer

Read end to end, every rung of this line reduces to one of three questions, and
all three were answered by hand, in generator code, at authoring time.

**Which dimension to mint.** Attitude's assisted clock (AC/AD) was a dimension
that did not exist, which is why the axis could not discriminate however the
corners were priced. The probe ladder (V) minted AMPLITUDE as a dimension nobody
had read, though the calibration pass had been walking it all along. Block W
replaced sample-count with escalation-completeness — a different dimension for
the same question. Block U found the containment reach was a spec constant: a
dimension that measured nothing.

**At what order.** The axis clocks already project at measured order-N. But the
deliberation cadence (AA) and the stale-verdict test (AB) are order questions
about the DECISION PROCESS — how often to re-decode. And the 10 Hz rate is an
order constraint on observation: at 0.1 s sampling the response-lag dimension is
not resolvable, so block V's zero-lag null was a statement about sampling order,
not about effectors. It was recorded as the latter and had to be conditioned.

**With what weight.** The allocation budget (AE). `channel_surrender_discount`
silencing attitude to the horizon (Y2). The tie-break priority axis (AF).
Authority weighted by evidence (§37).

### The pattern that makes the diagnosis hard to argue with

**Every value hand-picked in this session was wrong. Every value derived from a
measured residual held.**

| hand-picked | outcome |
|---|---|
| terrain < 500 m, airspeed < 70 m/s | pinned the priority to heading through an entire departure |
| evidence horizon 80 actions (as a wait) | longer than the ~73-action pass it governed; the stop fired never |
| `Max(..., 2.0)` floor on activation | a number; removed |
| share 1.0 for every corner's attitude | capped the representation so freed authority could not flow |
| `assisted > raw` as "authority exists" | true whenever any authority is measured; fired before the fault in every scenario |

| derived from a residual | outcome |
|---|---|
| smallest amplitude that answered (V) | localised a dead rudder against a healthy plant on 10 observations |
| escalation completeness (W) | dead rudder 0.899 → 0.0000 authority on the same evidence |
| measured lag + observation action (X) | activation energy that moves with the aircraft; jam 11391 → 803 ft |
| `authority < demand` (AH) | zero false positives in ~21,000 actions across seven scenarios |

That is precisely the difference between DECLARING a quantum and MINTING one
from a residual — which is the sd loop's entire job.

### The part that is uncomfortable and factual

**`shape_decode_loop` v1.8.0, 17 rules, is loaded into the F-16 seed set
(`jabberwock_jsbsim_f16_paper_replication.py:753`) and never fires in the
control path.** Its rules match on the `observed` edge type; nothing in the
flight loop publishes into that vocabulary. The machinery designed to decide
which dimension to mint, at what order, and with what weight is present, inert,
and its job was done by hand — one rung at a time, with a human as the arbiter
of each residual.

The architecture rule already says why this matters: the agent can self-repair
exactly where its cognition is graph-native, and every one of these decisions
currently lives in Python authoring rather than in the graph. They are not
agent-facing data it can vary, experiment on, or adopt. Each rung of this
session is therefore a repair the jabberwock could not have made for itself,
about its own representation — which is the one class of work it was built to do.

**The concrete next step is not another rung.** It is to publish the control
loop's residuals into the sd loop's own vocabulary — an unexplained difference
between predicted and observed consequence IS the residual `sd_mint_quantum`
consumes — so that "attitude needs a second stream" arrives as a minted
CapabilityAxis rather than as a generator edit, and the codebook_epoch re-decode
does what eight hand-built blocks could not.

## §52 — The sd loop contract, and which residual to feed it

**The contract, read from the seed rather than assumed.** All 17 rules of
`shape_decode_loop` v1.8.0 match the same pattern, `[["ag","observed","obs"]]`,
and `sd_decode` reads exactly three attributes: `obs.signature`, `obs.status`
(it fires on `"pending"`), and `ag.codebook_epoch`. A signature is a JSON list
of relation tuples in the codebook's own style —
`[["build","NEW","from","PRIOR"],["refers","NEW","to","SELF"],…]` — decoded by
the `ShapeDecode` Term against held `ShapeSignature` nodes
(`math_capability_shapes`, 17 of them). So wiring is mechanical: mint an
observation, give it a signature, set status pending, add the `observed` edge.

**Which residual to feed it is NOT mechanical, and the obvious candidate is
wrong.** Measured across the suite (8 × 3 × 1000):

| scenario | `prediction_error_energy` p50 | frac above nominal's p90 |
|---|---|---|
| nominal | 44.31 | 0.100 |
| saturated_elevator | 144.25 | **0.835** |
| shifted_cg | 117.10 | **0.861** |
| damaged_wing | 28.29 | 0.333 |

It is nonzero everywhere and **two non-departing scenarios exceed nominal more
often than the departing one does**. As a residual signal it has no
discriminating power; feeding it to `sd_mint_quantum` would mint continuously
on scenarios that are flying fine.

**`f16_shape_difference_sq` is the residual with structure**, and it is already
computed — it is the "shape of what is happening minus the shape of what
happened before" from early in this line:

| scenario | `f16_shape_changed` frac | `difference_sq` p50 | p90 |
|---|---|---|---|
| nominal | **0.000** | 0.004 | 0.005 |
| jammed_rudder | 0.897 | 9.09 | 9.19 |
| damaged_wing | 0.897 | 325.66 | 353.72 |

Exactly zero in healthy flight, and three orders of magnitude between the two
fault classes — it distinguishes *a rudder is dead* from *the wing changed*
before any decode happens.

**The remaining design decision, deliberately not made here.** The signature
vocabulary. The held codebook is abstract-structural (`build/refers/bound/map/
invariant/repeat` over `NEW/PRIOR/SELF/SCALE/UNIT/PART/TRANSFORM`), and a
control residual expressed in new slot names would never be recognised by
anything, so every observation would mint — the flood case. Note also that
`f16_shape_changed` holds on **89.7%** of actions in a fault, so one observation
per action is 2700 per episode; the loop's `sd_dedup_existing` exists for
exactly this and its behaviour under that rate is unmeasured.

Choosing that vocabulary is the substantive act, and doing it in the same breath
as the plumbing is how the last four end-of-chain builds failed. The contract is
now known, the residual is chosen on evidence, and the vocabulary is the next
piece of work rather than a guess appended to this one.

## §53 — The residual vocabulary, wired: the loop receives it and does not decode it

Two signatures, minted once per episode of change rather than per action
(`f16_shape_changed` holds on 89.7% of fault actions; per-action would be 2700
per episode):

- `[["acts","PART","on","AXIS"],["silent","PART","at","STOP"],["holds","OTHER","on","AXIS"]]`
  — an effector has stopped acting while others still act;
- `[["acts","PART","on","AXIS"],["answers","AXIS","unlike","PRIOR"],["holds","PART","under","AUTHORITY"]]`
  — the same effectors act and the plant answers unlike before.

**The names are aliases.** `ShapeDecode` matches structure and
`TransformDecode` treats symbolic substitution as a global rename check, so
nothing downstream reads "EFFECTOR" or "PLANT" as meaning anything — they exist
so a human can read a trace. What matters is that these are two different
relation graphs, and the split is the one the loop already measures
(`f16_probe_explanation_found`, §52).

**Measured: the observations arrive.** Under a damaged wing and a jammed rudder
both signatures appear with their residual magnitudes attached (1.87, 2.13,
7.41) at actions 104, 105 and 111 — a handful per episode, not thousands.
nominal is unchanged (`323.28346789186793`).

**And the decode does not engage.** Every control observation comes back
`status: "recognized"` with `decode = {authored: False, reason: "no goal
signature to decode"}`. They are being ACCEPTED, not decoded: `ShapeDecode`
decodes an observation against the codebook *for a goal*, and these arrive with
no goal signature, so the ladder short-circuits before recognise/transform/infer
/mint can run. No `CapabilityAxis` is minted from them.

So the contract was met at the letter and missed at the substance. The residual
now reaches the machinery; the machinery needs the other half of the pair — what
the loop was TRYING to do — before it can ask whether the residual is explained.
That is the next piece, and it is a smaller and better-specified one than any
rung in this session: the goal signature already exists in the control loop as
the objective set a corner declares.

## §54 — The sd loop fires on a control residual and mints a dimension

The decode was refusing my observations with `reason: "no goal signature to
decode"` while `goal` is literally `obs.signature` and the attribute was
present. **A control experiment settled it:** publishing a VERBATIM codebook
signature as a string failed identically, which ruled out the vocabulary and
pointed at the encoding.

**A signature on an OBSERVATION is a structure; on a `ShapeSignature` it is JSON
text.** The codebook stores `'[["build","NEW","from","PRIOR"],…]'` as a string,
so the obvious inference is that observations should match — and they must not.
The observations already decoding in this graph carry tuples:
`(('structured', 1.0), ('structured', 2.0))`. Publishing the relations as an
actual nested list rather than a JSON string was the whole fix.

**Measured, with the residual now decoding:**

```
status='minted'              covered=0   mag=1.869  at=104
  sig=(('acts','PART','on','AXIS'),('silent','PART','at','STOP'),
       ('holds','OTHER','on','AXIS'))
status='recognized_duplicate' covered=0  mag=1.869  at=105
  sig=(('acts','PART','on','AXIS'),('answers','AXIS','unlike','PRIOR'),
       ('holds','PART','under','AUTHORITY'))
CapabilityAxis nodes: 2 -> 3
```

The held codebook covered none of it (`covered=0`), so the ladder ran to its
last rung and **minted a CapabilityAxis from a control residual** — the first
time the sd loop has done anything in this control path, and the machinery
this whole session was hand-simulating. nominal `323.28346789186793` and
jammed_rudder `323.10483819184157` unchanged to full precision: the residual is
observed and decoded without touching the flight.

### What is honestly not yet established

The second shape returns `recognized_duplicate` against the first. They are
different relation graphs, so either the dedup is matching them structurally
under a rename — which is `TransformDecode` behaving exactly as designed, and
would mean "an effector went silent" and "the plant answers differently" are the
SAME shape up to substitution — or the dedup is coarser than it should be at
this grain. Both are plausible and the measurement does not distinguish them.
That question matters more than it looks: if those two really are one shape,
the fault taxonomy this line has been building has one member, not two.

Nothing consumes the minted axis. The loop now grows a dimension when the plant
surprises it, which is what it was built to do; whether the control path can
read what it grows is the next thing, and it is a different question from any
asked in this session.

## §55 — A wing is a fixed effector, and the frame must infer the plant's shape from behaviour

The four effector models in this world are the COMMANDABLE groups: elevator,
aileron, rudder, throttle. A wing is an effector too — it produces lift and
moment every action — it simply has a fixed command and is therefore not
represented. Everything that has gone wrong in this line follows from that
omission.

**Why the probe localises a rudder and not a wing.** The ladder works by pushing
a modelled effector and reading whether it answers (§V). A jammed rudder is a
modelled contributor that stopped contributing, so ten observations localise it
categorically. A damaged wing is an UNMODELLED contributor whose contribution
changed; there is nothing to push and nothing to attribute to, so the same
instrument correctly reports "every effector is healthy" and the fault surfaces
only as an unattributable global difference. That reading was accurate and
useless, and the uselessness was structural.

**Why balance was invisible.** Opposition can only be computed between
represented contributors. A damaged wing's asymmetric moment opposes the aileron
continuously, and with no node for the wing that opposition has nowhere to live
— so `roll_authority = MaxOver |mean_roll|` reports an authority the aircraft
does not actually have, and the `authority < demand` predicate (§AH, zero false
positives) is measuring against an inflated numerator.

**Why no corner could ever have been selected.** A corner reallocates authority
across represented effectors. No allocation over four surfaces can compensate
for a fifth contributor that is not in the representation — which is why blocks
Z through AF each did exactly what they claimed and none moved the outcome.
The frontier was never choosing between the right options; the option that
matters ("counter the wing") is not expressible.

**And this is precisely a rung-3 residual.** The sd loop's `DimInfer` exists for
a residual COUPLED across observed dimensions — CLAUDE.md's own example is that
rotating a flat 2D rectangle in Z produces an XY change you cannot replicate
without Z. Here: a roll change that cannot be replicated by any combination of
the four modelled effectors. The correct inference is not "mint an opaque
quantum" but **infer a LATENT CONTRIBUTOR and let its behaviour define its
shape** — the frame implying the plant's decomposition from what the plant does,
rather than being told the decomposition up front.

**Status: hypothesis, not result.** §54 measured that the residual now reaches
the loop and mints an axis; it did NOT measure that the minted axis is the wing.
The concrete test is small and it is the right next piece of work: give the
airframe fixed-command effector models — contributors with a constant command
level — and check whether the existing probe, authority and containment
machinery localises a wing fault the way it already localises a rudder jam,
with no new decision logic at all. If it does, every instrument built this
session starts working on the case it could not see, unchanged.

## §56 — The plant is an effector commanded at construction, and the term was optimised away

The correction that supersedes §55's framing: **do not model wings.** Model THE
PLANT as one effector. Its command was issued at construction — "have this
response" — and it has been executing that command ever since. A change in the
airframe is therefore a DEVIATION FROM COMMAND in exactly the sense every other
effector already uses, and it slots into the existing tracking, probe, authority
and residual machinery without any of them changing. Which part changed is not
something the frame should be told; "the plant effector deviated, uncommanded"
is the observation, and minting dimensions off that residual is how you work out
what happened.

**And the reason it was missing is a classic.** The plant's deviation from its
construction command is identically zero for a healthy airframe. A term that is
always zero gets optimised away as a constant — so the plant never got a node,
never got a command, never got a residual. When the term stopped being zero, the
equation had no place to put it, and **no adjustment of the surviving terms
could make it correct.**

That is the whole session in one sentence. Blocks Z through AF each re-tuned
coefficients of the remaining terms — containment zeroing, allocation budgets,
assisted clocks, priority axes, tie-breaks — to compensate for a term that had
been removed. Every one of them did exactly what it claimed and none moved the
outcome, because the quantity that could have made the equation correct was not
in it. It also explains why the instruments were simultaneously right and
useless: "every effector is healthy" is true of every effector the model has.

The general rule, worth more than this scenario: **a term that is invariant at
design time must still be represented, precisely because it is the one that will
break the model when it varies.** Zero is a value, not an absence.

### Build attempted three times and reverted

1. Two wings as fixed effectors, groups 4 and 5 — `IndexError`, because
   `stamp_effector_positions` indexes the four-actuator position tuple by group.
2. One plant effector plus a rule mapping `f16_shape_difference_sq` to its
   position via `1/(1+difference)` — the motor composer selected it and issued
   its token, and the world raised `unknown token: 'plant'`. It tried to fly the
   airframe as a surface.
3. The same with `available: 0.0` — identical failure. **Availability does not
   gate the command path**, which is itself a finding: an effector model in this
   graph is commandable by construction, and "observed but never commanded" has
   no representation.

Reverted; nominal `323.28346789186793` and jammed_rudder `323.10483819184157`
restored exactly, 47 green.

That third failure is the real obstacle and it is the same shape as the defect
being fixed: the model assumes every effector is commanded, exactly as it
assumed the plant was not an effector at all. Adding a non-commandable
contributor needs that assumption named and given a representation first —
which is a change to the effector contract, not to the F-16 adapter.

## §57 — The effector contract admits "observed but never commanded" (emp v1.9.0)

The obstacle §56 hit was that an effector model in this graph is **commandable
by construction**: a contributor added to the body was selected by the composer
and its token issued to the world, and marking it unavailable did not stop it,
because availability gates candidacy and not the command path.

`emp_copy_program_members_to_trial` — the rule that puts a program's members on
the trial, and so the direct source of the tokens the world receives — now
declines members declaring `never_commanded`. An effector may be OBSERVED and
LEARNED without ever being commanded: a contributor whose command was issued
elsewhere, or once, and never varies.

**Absence means commandable.** The flag is `never_commanded`, not
`commandable`, precisely so an absent attribute reads as zero and every body
plan that has never heard of this is unaffected. Verified: nominal
`323.28346789186793`, jammed_rudder `323.10483819184157` and damaged_wing
`14717.12` all unchanged, 50 green.

**Every body plan has an invariant that is not actually invariant** — the
airframe, the chassis, the skeleton — commanded once at construction and
executing that command ever since. The ones that genuinely have none carry a
zero here and lose nothing, which is why this belongs in the general seed
rather than in any consumer.

This is the representation §56 said was missing, and it is the precondition for
the plant to have a node at all. What it does NOT do is add the plant: a
consumer must now declare a contributor with `never_commanded: 1.0`, publish
its deviation from its construction command, and let the existing tracking,
probe, authority and residual machinery read it — none of which needs to change.
That is the next piece, and it is now unblocked rather than structurally
impossible.

## §58 — The plant contributor, declared and measured (emp v1.10.0, f16 v8.60.0)

The airframe now has a node. `never_commanded: 1.0`, command level 1.0 — as
constructed — and a position that is its measured conformance,
`1 / (1 + f16_shape_difference_sq)`, needing no threshold and no scale.

| | action 99 (pre-fault) | action 500 | action 999 |
|---|---|---|---|
| **nominal** | pos 0.99866 / dev 0.00134 | 0.99545 / 0.00455 | 0.99632 / 0.00368 |
| **damaged_wing** | pos 0.99921 / dev 0.00079 | **0.00305 / 0.99695** | **0.00321 / 0.99679** |

**The airframe reports that it is not executing its construction command** —
deviation 0.0008 before the fault, 0.997 after — in the same units any surface
reports a tracking error. nominal `323.28346789186793` and jammed_rudder
`323.10483819184157` unchanged, 50 green. The term that was optimised away for
being always zero is back, and it costs exactly nothing when it is zero.

### The contract needed a second half

Declaring it first deadlocked the loop: `RuntimeError: graph request 1 reached a
non-progressing asynchronous state ('calibration', …)`. `calibration_frontier`
selects models still owed samples, and **calibration samples a model BY
COMMANDING IT** — so a never-commanded contributor can never be sampled, never
accumulates experience, and never leaves the frontier. The pass stalls
permanently on its first request.

So `never_commanded` gates two things, not one: membership of a motor program
(v1.9.0, the token path) and candidacy for calibration (v1.10.0, the sampling
path). Both are the same statement — this contributor is observed, not
exercised — and both were needed before a body could carry one.

### Honest limits of what was measured

- `experience_count` stays 0. The plant has a DEVIATION but no learned
  consequence model, because learning is driven by commanding. Its `mean_*`
  columns are therefore empty, so nothing yet knows WHAT the plant contributes,
  only that it has stopped contributing what it was built to. Learning a
  never-commanded contributor from what it does while others act is the next
  piece and it is not done here.
- Nothing consumes `f16_plant_deviation`. The probe, authority and containment
  machinery can now see the contributor, and no rule reads it yet — so the
  flight is unchanged, which is why the pins hold.
- The conformance map is one choice among many. `1/(1+d)` is monotone and
  scale-free, which is enough to be honest, but it was not selected against
  alternatives.

## §59 — Membership is not commandability: a program operates FROM the body

I gated a never-commanded contributor out of trial membership, and it produced
exactly the confusion it should have prevented: `graph trial contains 4 members;
expected 5`. **A motor program operates FROM the body.** The plant is where the
program acts, not an optional participant, so it belongs on the trial like any
other member. What must never happen is a COMMAND being issued to it — and that
is a property of the command path, not of membership. Conflating the two was the
error.

Corrected: membership is unrestricted (emp v1.11.0), and `_trial_tokens` emits
tokens only for commandable members, with the expected count reduced by the
members it skipped. Absence reads as commandable, so a body plan declaring no
such contributor is unaffected.

**Measured, all three scenarios running and both pins unchanged:**

| plant deviation | pre-fault | action 500 | action 999 |
|---|---|---|---|
| nominal | 0.00134 | 0.00455 | 0.00368 |
| jammed_rudder | 0.00398 | **0.90108** | **0.90066** |
| damaged_wing | 0.00079 | **0.99695** | **0.99679** |

The airframe reports deviation from its construction command, and the two fault
classes separate: a jammed rudder leaves the plant 90% deviant, a damaged wing
99.7%.

### What still does not happen, precisely

`experience_count` is 0 and the `mean_*` columns are `None`:
`emp_learn_uncommanded_contributor_from_residual` never fires. It matches on
trial membership, and **the plant is never a program member** — membership is
granted through the calibration path, which correctly excludes a contributor
that cannot be sampled by commanding.

So the last step is the literal form of "a program needs somewhere it operates
from": a rule that adds the never-commanded contributor to every program as its
substrate, independent of calibration. Then the residual learning matches, the
`mean_*` columns populate from what the plant does while the surfaces act, and
the probe/authority/containment machinery reads the airframe as it reads a
surface — with none of them changing. The contract, the declaration, the command
path and the learning rule are all in place; only the edge that makes the plant
part of the program is missing.

## §60 — The substrate edge: built, measured, reverted, and the obstacle named

`emp_include_substrate_in_program` adds the never-commanded contributor to every
program as its substrate, independently of calibration — the literal form of "a
program needs somewhere it operates from", and the one edge §59 identified as
missing. **Reverted.** All three scenarios restored exactly
(`323.28346789186793`, `323.10483819184157`, `14717.12`), 50 green.

The obstacle is a single consistency check and it defeated three attempts:

```
attempt 1  expected = count - skipped   ->  "4 members; expected 5"
attempt 2  expected = count              ->  "1 members; expected 0"
attempt 3  expected = count              ->  "4 members; expected 5"
```

`expected_member_count` is stamped when a program opens, and whether it includes
the substrate depends on **when it was stamped relative to the substrate edge
being added** — before it, on the calibration path, it counts only commandable
members; after it, on the width-reconciliation path, it counts the substrate
too. So no fixed arithmetic in `_trial_tokens` is correct: the same expression
is right on one path and wrong on the other.

**The check itself is the thing that needs changing, not the arithmetic.** It
asks "did the trial deliver as many tokens as the program has members", which
conflated membership with commandability exactly as §59's gate did — one layer
down, in the adapter. What it should ask is "did every COMMANDABLE member get a
token", which is a property of the trial and needs no stamped count at all.
That is a change to the invariant the adapter enforces, and it wants doing
deliberately rather than as the fourth patch of a chain.

### Standing state at the end of this line

Landed and measured: the effector contract admits observed-but-never-commanded
(emp v1.9.0/1.10.0, gating the token path and the calibration frontier); the
plant is declared as a contributor with a construction command (f16 v8.60.0);
the command path emits tokens only for commandable members (emp v1.11.0); and
the residual learning rule exists. The airframe reports deviation from its
construction command across the suite — 0.0013–0.0046 nominal, 0.901 jammed
rudder, 0.997 damaged wing.

Not landed: the substrate edge, and therefore the learning never fires
(`experience_count` 0, `mean_*` empty). The plant knows it has stopped
executing its construction command; it does not yet know what it contributes.

## §61 — How deep the assumption goes: six sites that make a fixed effector unrepresentable

Trying to land one contributor is a good way to measure an assumption, because
every place that breaks is a place the assumption was baked in. **A fixed
effector is still an effector, and this codebase had made it effectively
impossible to represent** — not at one point but at six, in three layers, each
individually reasonable.

| # | site | layer | what it assumes | how it failed |
|---|---|---|---|---|
| 1 | `stamp_effector_positions` | adapter | every effector has an actuator position | `IndexError` — indexes a four-actuator tuple by group |
| 2 | `emp_copy_program_members_to_trial` | general seed | every member is commandable | issued the token; world raised `unknown token: 'plant'` |
| 3 | `calibration_frontier` | general seed | learning happens by commanding | never sampled → never leaves the frontier → `non-progressing asynchronous state` |
| 4 | `_trial_tokens` count check | adapter | members == tokens | `4 members; expected 5`, then `1; expected 0` — and `expected_member_count` is stamped differently per path, so no fixed arithmetic is right |
| 5 | `step_program` | world | a program always commands something | `a motor program must contain opaque tokens` on a substrate-only program |
| 6 | `emp_learn_factorized_effector_from_exact_receipt` | general seed | learning matches `commands_…` | a never-commanded contributor can never learn |

Sites 1–3 were fixed and are landed (emp v1.9.0–1.11.0, f16 v8.60.0). Sites 4–6
are not: 4 needs the adapter's invariant rewritten from "as many tokens as
members" to "every commandable member produced a token" — attempted, and it
then exposed 5 immediately. **Four attempts, four distinct failures, each one a
different site.** That is the measurement.

What it says is stronger than any of the individual fixes: the representation
was not neutral about this. "Every effector is commanded" is not written down
anywhere as a decision — it is implicit in a position lookup, a frontier
predicate, a count check, a world guard, and a learning rule's match pattern.
None of those is wrong on its own terms. Together they make a category of
contributor — the body itself, the fixed effector, the thing every program acts
through — unrepresentable, and the only symptom visible from inside was that a
damaged wing produced an unattributable residual while a jammed rudder did not.

This is the same shape as §56's optimised-away constant, one level up: a term
that was always zero got removed from the equation, and the removal is not
recorded in one place that can be reverted — it is distributed across every
site that assumed the term did not exist.

### State at the end

Reverted to the last verified state: nominal `323.28346789186793`, jammed_rudder
`323.10483819184157`, damaged_wing `14717.12`, 47 green. The plant is declared,
carries a construction command, and reports deviation from it (0.0013–0.0046
nominal, 0.901 jammed rudder, 0.997 damaged wing). It does not learn what it
contributes, and landing that needs sites 4, 5 and 6 — which is a contract
change across the adapter, the world and the general seed, not a patch.

## §62 — Sites 4/5/6 as one contract: attempted, and site 5 recurs from an unidentified path

The contract stated once: *a program acts through its substrate and commands its
commandable members.* From it: tokens are the commandable members (site 4), the
invariant is "every commandable member produced a token" rather than a count
comparison, and the substrate joins only programs that already command
something — which should make a substrate-only program unreachable rather than
guarded (site 5), and puts the substrate on the trial so residual learning
matches (site 6).

**It did not land.** The world still raised `a motor program must contain opaque
tokens`, so substrate-only trials still arise by a path the `Exists(commandable
member)` guard on program membership does not cover. Candidates not
investigated: `emp_open_flow_excitation_program` builds a program by a different
route; `copy_trial_members` is `batch: True`, so a trial may be observed
mid-copy; and a program's commandable membership may change after the substrate
edge is added. **I did not identify which.** Reverted — nominal
`323.28346789186793`, jammed_rudder `323.10483819184157`, damaged_wing
`14717.12`, 47 green, working tree clean.

That is five attempts across sites 4–6 and five failures. The pattern is
consistent with §61 rather than contradicting it: each fix reveals the next site
because the assumption is not localised, and a guard placed at one site does not
constrain the paths that reach the same state by another route. Fixing this
properly needs the program-construction paths ENUMERATED first — there is more
than one, and I have been patching the one I could see.

**What holds at the end of this line** (all measured, all landed):

- the effector contract admits observed-but-never-commanded, gating the token
  path and the calibration frontier (emp v1.9.0–1.11.0);
- the plant is declared as a contributor carrying a construction command
  (f16 v8.60.0), and reports deviation from it: 0.0013–0.0046 nominal, 0.901
  jammed rudder, 0.997 damaged wing;
- the probe ladder localises a dead effector on ten observations, and quorum
  distinguishes "an effector died" from "the plant changed";
- stopping the checklist on quorum takes the jam from 11391 → 803 ft with peak
  structural utilisation 521× → 0.64, over 24 episodes with 7/8 scenarios
  byte-identical;
- the sd loop receives control residuals and mints a CapabilityAxis from one.

**What does not**: the plant does not learn what it contributes, and the damaged
wing still departs.

## §63 — The program-construction paths, enumerated: the root cause in one pass

Five patches failed because I was guarding the path I could see. Enumerating
first found it immediately.

**Four rules open a program**, and they select their first member two different
ways:

| rule | primary drawn from | filters `never_commanded` |
|---|---|---|
| `emp_open_flow_excitation_program` | `calibration_frontier` | **yes** |
| `emp_open_factorized_calibration_program` | `calibration_frontier` | **yes** |
| `emp_abs_open_embodied_motor_program` | direct model match | **NO** |
| `emp_render_open_embodied_motor_program` | direct model match | **NO** |

The two calibration-path openers inherit the exclusion added in v1.10.0, because
`calibration_frontier` filters. **The two that match `episode
-has_embodied_effector_model-> primary` directly do not**, so either can select
the plant as a program's PRIMARY member — producing a program whose only member
is the substrate, hence zero commandable members, hence zero tokens, hence
`a motor program must contain opaque tokens`.

That is the unidentified path from §62. My guard was on ADDING the substrate to
a program; it can do nothing about a program that was OPENED on the substrate.

**Six rules grant membership** — the three openers above via `primary`, plus
`emp_render_attach_chosen_members`, `emp_abs_expand_factorized_groups_in_parallel`
and `emp_abs_expand_embodied_motor_program` via `candidate`. The three expanders
are also unfiltered and can add the substrate a second time by a different
route.

**One rule creates trials**: `emp_open_selected_motor_program_trial`.

And `expected_member_count` — the attribute my adapter check compares against —
is **set by no rule in this seed**. It is written in `jabberwock_active_aero.py`
and in the generator, which is why its value depends on which path stamped it
and why no fixed arithmetic against it was ever going to be correct.

### The fix this implies, not yet made

The constraint belongs where a member is SELECTED, not where the substrate is
added: **a never-commanded model may never be a program's primary, and may never
be selected as an expansion candidate.** That is a `never_commanded` filter on
the two direct-match openers and the three expanders — five sites, all in the
general seed, all the same predicate — after which a program always commands
something and the substrate edge can be added unconditionally.

That is a targeted change against an enumerated list rather than a guess against
the path I happened to hit, and it is the sixth attempt this line has earned the
right to make. Not made here: the enumeration was the task.

## §64 — The substrate, pushed further: the structural fix found, and where it still fails

Continuing rather than reverting found the real shape of the fix, and then a
failure I could not characterise. The attempt is preserved verbatim in
`docs/attempts/` so none of it has to be re-derived.

### What was found, and it is the important part

**An exclusion must live in the eligible set, not in the rule's `where`.**
Selection at these sites is an `Argmin`: the rule requires its bound model to BE
the argmin. Appending `Not(never_commanded)` to the `where` therefore does not
skip the substrate — when the substrate wins the argmin, the rule matches
*nothing at all* rather than falling through to the next-best model. Measured:
that stalled synthesis with no active plan at request 691. Moving the same
predicate inside the three candidate filters that feed the argmins fixed it, and
**nominal then ran byte-identical (`323.28346789186793`) with the plant declared,
a member of every program, and the substrate edge landed.**

That is a general lesson about this rule engine, not about aircraft: *a guard
appended to a rule whose match is an extremum is a deletion, not a constraint.*

**§63's enumeration also contained an error, caught by measurement.**
`emp_render_open_embodied_motor_program` appeared to select a member because it
adds a membership edge to `primary` — but it CREATES that node in its effects
and never matches a model, so `primary` is unbound in its `where`. Guarding it
silently deleted the rule. Four selection sites, not five, and the guard now
asserts its variable is bound by the rule's own match.

### Where it still fails

- **jammed_rudder regressed to `6928.583937100404`** — exactly the pre-block-X
  baseline, so the probe stop stops firing once the plant is a program member.
  Not diagnosed.
- **An intermittent synthesis stall remains**: the same seed completed under
  `pin.py` and stalled at request 465 under `probe_conf.py`, both with
  diagnostics enabled. `('synthesis', …, 'published', …, (), …)` means no active
  plan, and only `emp_abs_open_embodied_motor_program` marks one active — so the
  eligible set is empty at that moment. **Why it is empty is the next
  measurement**, and it is a different question from anything asked so far:
  under what conditions does every commandable model become ineligible?

Reverted to the verified state: `323.28346789186793`, `323.10483819184157`,
`14717.12`, 47 green, tree clean. Eight distinct failures across this
sub-thread; two of them produced general lessons about the engine, which is the
only reason the count is worth recording.

## §65 — Why the eligible set goes empty: the plant is the zero-increment fallback

Measured at the stall (jammed_rudder, request 465), all three eligibility
conditions read directly:

| | value at stall |
|---|---|
| commandable models | 36 |
| with `experience_count > 0.5` | **36** |
| with `available > 0.5` | **36** |
| `structural_limits_enabled` | 1.0 |
| `state_safe_normal_load` | **0.0** (was 5.99 at action 400) |
| `state_current_normal_load` | 0.029 |

Conditions one and two are satisfied by every model. The binding condition is
`structural_model_admissible`, and the reason is that **the safe envelope
collapses to exactly 0.0** around action 420. The predicate's main branch
requires `Gt(state_safe_<key>, 0.0)` for every structural key, so a safe limit
of zero makes every model inadmissible at once — regardless of what it would
actually load.

### And the second branch is the whole story

```
Or( limits disabled,
    Or( ALL keys: safe > 0 AND load + prediction <= safe,
        AND( structural_interrupt_required, increment_is_zero(model) ) ) )
```

When the envelope collapses, the only way any model stays admissible is the
second branch: an interrupt is required and the model adds **zero** structural
increment. **The plant satisfies that trivially** — its predictions are all
zero, because it has never learned any.

So the plant is not accidentally eligible in that state; it is the only thing
that CAN be. Declaring it supplied the system with a zero-increment fallback it
had never had, my exclusion then removed the only admissible candidate, and the
eligible set went empty. Every earlier symptom follows: the plant winning the
Argmin (it is the cheapest and, at the limit, the only admissible option), the
substrate-only program, the empty token list.

**The unverified link**: `structural_interrupt_required` was not read at the
stall, so "the second branch is what the plant was satisfying" is inferred from
the predicate and the zero predictions rather than measured. That is one attr in
one probe and it should be measured before anything is built on this.

### What it means for the design

The question is no longer "how do I keep the substrate out of selection". It is
**what should a program be when nothing can safely act?** The system already has
an answer in its own vocabulary — an interrupt plus a zero-increment member —
and that state is exactly "act through the body, command nothing". The world
rejects it (`a motor program must contain opaque tokens`) because the adapter
assumes every program issues a command, which is site 5 of §61 seen from the
other side: not an obstacle to work around, but the system telling us that a
commandless program is a real state it needs to express.

Reverted to the verified tree: `323.28346789186793`, `323.10483819184157`,
`14717.12`, 47 green.

## §66 — The interrupt flag, measured: §65's mechanism was half wrong

The one unverified link in §65, read at the stall (jammed_rudder, request 465):

| | value | §65 said |
|---|---|---|
| `structural_interrupt_required` | **1.0** | inferred live — **confirmed** |
| structural keys with `state_safe_* <= 0` | **12 of 12** | one key measured — **worse than stated** |
| plant has zero structural increment | **False** | "satisfies it trivially" — **REFUTED** |

The envelope does not merely lose its normal-load margin; **every one of the
twelve structural limits collapses to zero**, so the predicate's main branch is
dead for every model at once. And the interrupt IS required, so the escape
branch is live and is the only route to admissibility.

**But the plant does not take it.** §65 claimed the plant satisfies
`increment_is_zero` trivially because it has never learned anything. That is
false: its structural means are non-zero. The reason is a consequence of the
same change — `copy_trial_members` adds a `commands_embodied_effector_model`
edge for EVERY member including the substrate, and
`emp_learn_factorized_effector_from_exact_receipt` matches exactly that edge. So
the plant is learned by the ordinary commanded-effector path as well as by the
residual rule, picks up structural predictions, and stops qualifying as
zero-increment.

So the stall is not "the plant was the only admissible model and I excluded it".
It is: **the envelope collapses entirely, the interrupt fires, and nothing
qualifies for the zero-increment escape — including the plant.** Whether some
commandable model (the zero-command member of each group) would otherwise
qualify, and why it does not here, is the open question — and it is a question
about the escape branch, not about the substrate.

**§65 is corrected in place by this section rather than rewritten.** The
inference there was drawn from the predicate's shape and the plant's expected
emptiness, and it read plausibly; one probe of one attribute falsified it. It is
the same failure as block AG — generalising from what a quantity ought to be
instead of reading it — and it survived a commit because the check was described
as "one attr in one probe" and then not run before the conclusion was written
down.

Reverted; `323.28346789186793`, `323.10483819184157`, `14717.12`, 47 green.

## §67 — The zero-command member DOES qualify, and §66's refutation was measuring the wrong attribute

The question "why doesn't the zero-command member qualify" has a short answer:
**it does.** Measured at action 465 of jammed_rudder on the verified tree:

| | value |
|---|---|
| models with zero structural increment | **5** |
| which ones | the `cmd = 0.0` member of elevator, aileron, rudder, throttle — **and the plant** |
| `structural_interrupt_required` | **0.0** |
| structural keys with `state_safe_* <= 0` | **0 of 11** |

`structural_model_prediction` reads `specified_<key>` whenever
`structural_certified_default > 0.5`, which is true of every model in this
world. The specified loads are all proportional to `|command|`
(`_specified_action_loads`), so a zero-command member has zero predicted load on
every key by construction — and the plant, which declares no `specified_*` at
all, reads zero for the same reason.

**§66's refutation was measuring `mean_<key>`.** The predicate does not use the
learned means while `structural_certified_default` is set; it uses the offline
design bounds. So "the plant does not have a zero structural increment" was an
artefact of reading the wrong attribute, and **§65's original mechanism was
right**: the plant is a zero-increment fallback. It is simply not the ONLY one —
four commandable members are too.

That is two consecutive sections whose conclusion was wrong, both from reading a
plausible attribute rather than the one the predicate names. The correction is
cheap and mechanical: **read the predicate, then read the attributes the
predicate reads.** Neither §65 nor §66 did.

### And the envelope collapse is caused by the attempt, not pre-existing

The more important number: at the same action, on the verified tree, the
envelope is **completely healthy** — no interrupt, zero collapsed limits. In the
attempt build the same action had all twelve limits at zero and the interrupt
set. **The attempt causes the structural collapse; it is not a condition the
attempt merely encounters.**

So the stall is downstream of a real behavioural change: adding the plant to
programs makes the aircraft exceed its structural envelope, which collapses the
safe limits, which fires the interrupt, and only then does admissibility become
the binding question. Chasing the eligible set was chasing a symptom two steps
removed from the cause — and with 4 zero-increment commandable members
available, an empty eligible set was never a sufficient explanation for the
stall in the first place.

**The next measurement is therefore not about eligibility at all**: what does
adding the plant to a program change about the commands issued, such that the
airframe exceeds limits it otherwise respects? `expected_member_count`,
`member_count` and the composer's cost all shift by one member — and the
composer allocates across members.

## §68 — What the plant changes about the commands: nothing, and that is the answer

A/B on jammed_rudder, same seed, verified tree against the attempt:

| | A: plant NOT in programs | B: plant IN programs |
|---|---|---|
| actions completed | 1000 | **465 (stall)** |
| max trial members | 4 | **5** |
| commandable members per trial | same | same |
| effector positions at first divergence | identical | identical |
| `state_safe_normal_load <= 0` | **never** | **from action 413** |

The trials differ from action 1 — B carries one extra member — and **the
commands are identical**. Nothing about what is issued to the world changes.
Yet B's structural envelope collapses at 413 and A's never does.

So the hypothesis at the end of §67 is wrong: the plant does not cause
over-driving by making the composer spread demand across five members. The
commands are the same. What changes is that the plant OCCUPIES A SLOT in the
allocation — it is counted, selected over, calibrated against, and reasoned
about as one of the things the program acts with.

### The two reframes that explain every failure in this sub-thread

**A never-commanded effector is no different from an effector reduced to zero
authority.** A jammed rudder does not leave the graph; it stays a member, it is
still selected, its token is still issued, and it simply produces no response.
The system already represents that perfectly — it is what the probe ladder
localises in ten observations. So `never_commanded` was never a new category
requiring new machinery at six sites: it is authority zero, and the existing
handling of a dead effector is the handling.

**And the plant is the negative space between the effectors. Literally.** It is
not a fifth object standing alongside four; it is the complement — what remains
of the observed change once every effector's contribution is subtracted. That is
exactly the residual the learning rule computes, and it is why every attempt to
make it a MEMBER broke something: a member must be selectable, commandable,
countable, calibratable and allocatable-to, and the negative space is by
construction none of those. Eight distinct failures, each one a place where the
system correctly insisted that a positive object behave like a positive object.

The plant needs a node so its deviation can be read — §58 measured that working,
0.997 under a damaged wing — but it does not need MEMBERSHIP, and the whole
`emp_include_substrate_in_program` line was solving the wrong problem. The
negative space is defined by the members, not among them.

This is the last measurement of this session and it retires the substrate-edge
work rather than completing it.

## §69 — The plant as a zero-authority effector: it works, and it dissolves the six sites

*"It is no different to an effector that has reduced to zero authority. It does
not go away, but you cannot command it."* Modelled that way, the plant is an
ORDINARY effector — declared, selected, commanded — whose command moves nothing.
No `never_commanded` class, no calibration exclusion, no substrate edge, no
selection guards, no eligible-set surgery.

**It runs. All three scenarios, end to end, first attempt.**

| | result | vs verified tree | crash | structural |
|---|---|---|---|---|
| nominal | 326.65 | +3.36 | False | 0.64 |
| jammed_rudder | 325.48 | +2.38 | False | 0.64 |
| damaged_wing | 14313.18 | **−403.94** | True | 1.71 |

And the probe machinery is untouched by it — under the jam the rudder still
reads `silent@stop`, authority **0.0000**, quorum 1.0, every other surface
1.0000. 47 passed, 1 skipped.

### Three mechanical changes, all in the world adapter

1. **accept and ignore the plant token** — a command to the airframe has no
   actuator to move;
2. **express a null command** when the plant is a program's only member — "act
   through the body, deflect nothing" is a real program, not an empty one, and
   the world's own way of saying it is every surface at neutral;
3. **report the issued program in the receipt** — the airframe was part of the
   program and was executed, by having nothing to move, so dropping it would
   report a different program than the one commanded.

Compare with the six-site contract change §61 enumerated and §62–§67 failed to
land eight times. **The six sites were not defending an assumption worth
changing; they were correctly refusing a category that did not need to exist.**
Every one of them — position lookup, trial membership, calibration frontier,
count check, world guard, learning match — is satisfied automatically by an
effector that is ordinary in every respect except that its command does nothing.

### What the two reframes were worth

The negative-space framing said the plant is not a fifth object beside four, and
the zero-authority framing said it is not a new kind of object at all. Together
they replaced a contract change across three layers with three lines of world
adapter, and the difference is measurable: eight failures against one success on
the first attempt.

**Not yet measured**: whether the plant's learned columns populate now that it is
commanded through the ordinary path. The probe that would show it keys on
`never_commanded`, which no longer exists — a one-line probe change, not run
here. The regressions are also small but real (+3.36 nominal, +2.38 jam) and
have not been explained.

## §70 — The plant learns, and what it learns is the fault

With the plant an ordinary zero-authority effector, it is learned by the
ordinary commanded path. Measured across one episode each:

| scenario | experience | forward | lateral | vertical | turn |
|---|---|---|---|---|---|
| nominal | 1 → **1** | 0.448 | −0.006 | −0.845 | 0.001 |
| jammed_rudder | 1 → **3** | −0.054 | **+0.180** | 0.011 | −0.011 |
| damaged_wing | 1 → **5 → 7** | 2.066 | −1.068 | **−2.981** | 0.021 |

**The learned columns are the fault's signature.** Under a damaged wing the
plant contributes −2.98 vertical — the lift no effector accounts for. Under a
jammed rudder it contributes +0.18 lateral — the uncommanded yaw from a surface
stuck out of trim. Nominal sits at a steady −0.845 vertical and never updates
again. That is the negative space between the effectors, read off a model, and
in both faults it reads as the correct physics without anything having been told
what a wing or a rudder is.

It also answers §55's question directly: the same residual that was
"unattributable, therefore report the plant moved" is now a column in a model
that says WHAT the plant is doing, in the same units as any effector.

### The honest limit: it learns rarely

Experience reaches 1, 3 and 7 over a thousand actions. The plant learns only
when it is SELECTED into a program, and selection is an Argmin over cost that it
rarely wins. So the signature above is built from a handful of samples, and its
precision should not be trusted — only its sign and rough magnitude, which are
consistent across the three scenarios and match the physics.

The residual-learning rule from §62 would learn it EVERY action, from what the
commanded effectors do not account for, and is the obvious complement: it was
written, it is not in this build, and it needs no `never_commanded` machinery
now — only a match on the plant's own model. That is the next piece, and unlike
everything in §61–§67 it is additive rather than a contract change.

## §71 — Learning the negative space every action (emp v1.12.0)

`emp_learn_unmovable_contributor_from_residual` learns an unmovable contributor
from what the movable members do not account for:

    residual = observed change - sum of the movable members' predictions

**Identified generically, with no flag.** The predicate is
`specified_maximum_position_change_per_action <= 0` — an effector whose command
cannot move it. That IS zero authority by construction, it is something a
consumer must declare anyway, and it needs no `never_commanded` category. The
general seed still contains none of the domain words.

**Learning is now dense: experience 998 in every scenario**, against 1, 3 and 7
when the plant learned only on the rare occasions it won selection (§70).

| | forward | lateral | vertical | roll |
|---|---|---|---|---|
| nominal | 0.0045 | 0.0032 | −0.0353 | −0.0040 |
| jammed_rudder | 0.0090 | **0.0548** | −0.0441 | −0.0107 |
| damaged_wing | **−0.7007** | **−1.1980** | 0.2719 | **−0.0274** |

**Nominal is near zero on every axis.** That is the strongest single reading in
this line: with a healthy airframe the effector models account for essentially
all of the motion, so the negative space between them is empty — which is what
it should be, and it was not assumed anywhere. Against that floor the jam shows
lateral 17× nominal and the damaged wing 374×, with roll 7×.

### Cost, stated plainly

| | §69 (sparse) | §71 (dense) | delta |
|---|---|---|---|
| nominal | 326.65 | 333.97 | **+7.32** |
| jammed_rudder | 325.48 | 324.92 | −0.56 |
| damaged_wing | 14313.18 | 14763.77 | **+450.59** |

Dense learning costs ~7 ft on nominal and ~450 ft on damaged_wing; the jam is
unchanged. Nothing crashes that did not already, 50 green. The cause is not
mysterious — the plant's `mean_*` columns feed the composer's predictions, so
learning them changes what the composer expects and therefore what it commands.
Whether that trade is worth taking depends on what consumes the signature, and
**nothing does yet**: it is measured, not acted on.

### Where this leaves the plant

It has a node, a construction command, a measured deviation from it (0.901 jam,
0.997 wing), and now a learned contribution that reads as the fault in the
correct axis with a near-zero nominal floor. The two things it still lacks are
a consumer — nothing reads the signature — and an explanation for the tracking
cost above.

## §72 — Why a zero-effect effector wins: the Argmin was always cost, never cost/benefit

The tracking cost of dense learning, explained by measurement:

| | sparse | dense |
|---|---|---|
| plant selected into the trial, nominal | **1/1000 (0.1%)** | **259/1000 (25.9%)** |
| plant selected, damaged_wing | 35/1000 (3.5%) | 43/1000 (4.3%) |
| mean program members, damaged_wing | 1.44 | **1.34** |

Learning the airframe's contribution makes it win selection **259× more often**
in nominal, and shrinks the mean program under a damaged wing. A quarter of the
aircraft's nominal actions are spent commanding something that by construction
moves nothing. That is the +7.32 ft and the +450.59 ft.

**Why does it win when its effectiveness is zero?** Selection is
`Argmin(eligible, cost)`. An effector with no effect has no activation cost, no
energy cost and no structural load — **it wins by being FREE, not by being
useful.** Nothing in the criterion asks whether the thing selected can affect
the outcome.

### The structural claim, and it is not about the plant

**The Argmin should always have been cost/benefit, not cost.** Minimising cost
alone means the cheapest option wins, and doing nothing is always cheapest. The
plant did not introduce that defect; it made it visible by being a perfectly
free option, which no real effector ever was. Every selection this system has
ever made has answered "which is cheapest", not "which is most worth doing" —
and it got away with it only because every candidate previously had a cost
roughly proportional to its effect, so cost was an accidental proxy for
benefit. Introduce one candidate where that correlation breaks and the criterion
selects it a quarter of the time.

A benefit term also makes an effectiveness FILTER unnecessary: a zero-benefit
option scores zero on a ratio however cheap it is, without a threshold anywhere.
An admissibility filter on `log_vector_weight` — attempted here and not applied,
the anchor no longer existed — would have patched the symptom in three candidate
filters while leaving the criterion wrong.

This is the same shape as the frontier's own defect (block Y): a selection rule
that reads one thing when the decision needs two. There it was dominance
comparing corners without asking what the plant affords; here it is cost
comparing effectors without asking what they achieve.

**Not built.** Changing `singleton_cost` into a cost/benefit criterion touches
every selection in the motor-program seed and would change every scenario in the
suite. It wants a prereg and a full block, not the tail of this session.

## §73 — Cost/benefit does not fix it: the criterion cannot tell predicting from causing

Block AI's change was made and measured, and then made again in the second cost
function, and the flight is **byte-identical every time**:

| formulation | nominal | jam | damaged_wing | plant selected (nominal) |
|---|---|---|---|---|
| cost (sum) | 333.97 | 324.92 | 14763.77 | 25.9% |
| `singleton_cost` as ratio | 333.97 | 324.92 | 14763.77 | 25.9% |
| **both** cost functions as ratio | 333.97 | 324.92 | 14763.77 | **25.9%** |

Verified in the generated seed — both rules carry the `Div` and the
inadmissibility sentinel — and the render path that uses the third `Argmin` is
disabled in this world (`render_first_composition_enabled: 0.0`), so the two
changed functions are the ones deciding.

### Why the ratio makes it worse, not better

**The plant's benefit is POSITIVE.** Its `mean_*` columns were fitted to what
actually happens, so it PREDICTS the target — and it costs nothing. Under the
ratio its score is `0 / positive = 0`, the minimum attainable. It wins harder.

Every formulation tried ranks candidates by their PREDICTED consequence, and the
plant is the best free predictor available under all of them. **The criterion
cannot distinguish predicting the outcome from causing it**, and no arrangement
of predicted-benefit and cost terms can, because the plant scores well on
exactly the quantity all of them read.

That is why the airframe's contribution being LEARNED is what broke selection
(§72): before it was learned it predicted nothing and was ignored; after, it
predicts everything and is free.

### What this means for the user's structural claim

"The Argmin should always have been cost/benefit, not cost" is right about the
sum being wrong — but insufficient. The missing quantity is not benefit, it is
**causal** benefit: what the candidate's COMMAND changes, not what its model
anticipates. The plant's causal authority is zero by construction — its command
moves nothing, `specified_maximum_position_change_per_action` is 0 — and that is
a fact about the effector, available without any learning, which no predictive
score will ever recover.

So admissibility does belong in the criterion after all, and for a reason
stronger than tidiness: **a means must be able to CAUSE the end**, and
correlation with the end is exactly what a good predictor offers instead. The
earlier instinct that it "should not be admissible" was correct; the reason is
that no ratio over predictions can exclude a perfect free predictor.

Reverted — both cost functions restored, since neither change moved anything and
the diagnosis says they are the wrong lever. `333.97 / 324.92 / 14763.77` stand
as the current tree's values.

## §74 — Benefit is reduction of surprise or furtherance of goals; five patches that were neither

**The definition that dissolves this.** Benefit is one of exactly two things:

- **furtherance of goals** — commanding this REDUCES THE GOAL ERROR, by the
  change the command CAUSES;
- **reduction of surprise** — commanding this REDUCES UNCERTAINTY about what
  the plant will do.

The airframe offers neither. It causes no change, so it furthers no goal. And
commanding it resolves no uncertainty, because its outcome is not in question —
nothing happens, and that was already known. Its benefit is zero under both
limbs, which is why it should never be selected, and why no admissibility hack
was ever the right instrument.

**What every formulation tried this session measured instead** was PREDICTED
OUTCOME: how closely a candidate's model anticipates the target. The airframe's
means are fitted to what actually happens, so it anticipates the target
excellently while causing none of it. Prediction is not benefit. Benefit is
CHANGE — in goal error, or in uncertainty — and prediction is precisely the
absence of change in the second.

It also unifies two halves of this session that were built separately: the probe
ladder is surprise-reduction (command in order to learn) and ordinary control is
goal-furtherance (command in order to achieve). The composer has only ever had a
goal term, and even that read predicted outcome rather than caused change.

### Five attempts, and what each measured

| # | change | effect on plant selection | flight |
|---|---|---|---|
| 1 | `singleton_cost` → cost/benefit ratio | 25.9% → 25.9% | byte-identical |
| 2 | `program_cost` → ratio as well | 25.9% → 25.9% | byte-identical |
| 3 | causal gate on 3 `available` filters | 25.9% → 25.9% | byte-identical |
| 4 | absence-safe gate (`log_vector_weight`) | 25.9% → 25.9% | byte-identical |
| 5 | gate the calibration frontier | **25.9% → 40.0%** | nominal **+3.95 worse** |

The fifth is the instructive one: excluding the airframe from the calibration
path made it selected MORE, because calibration then completed sooner and the
synthesis path — which selects by cost — ran more often. **Gating one path
displaces selection to another.** That is what patching admissibility does when
the criterion itself is wrong, and it is the same lesson as §61's six sites:
an assumption spread across paths cannot be fixed at one of them.

All five reverted; `333.97 / 324.92 / 14763.77`, 47 green, tree clean.

### Why this is recorded and not built

The correct change is to compute benefit as caused-change plus
surprise-reduction, in the two functions that rank candidates, and it touches
every selection the motor-program seed makes. Five consecutive attempts in this
thread produced four no-ops and one regression, each aimed at a path I had not
first proven was the deciding one. A sixth change made now would be the same
mistake with a better slogan attached.

What it needs first is the measurement this thread never did: instrument the
selection to record, per action, WHICH rule admitted the winning candidate and
what its benefit terms evaluated to. Every failure above came from not knowing
that — including the one where the answer turned out to be "action 1, the
calibration frontier, via a `never_commanded` predicate that had become dead
code".

## §75 — Selection instrumented: "do nothing" wins because nothing helps

`scripts/probe_selection_attribution.py` reconstructs what rules do not record:
when a model first becomes a program member (which localises the admitting
action), the `program_mode` at that moment (which distinguishes the calibration
path from the synthesis path), and the quantities the ranking functions read for
every candidate in the field. Purely additive — it reads the graph and changes
nothing.

**First run, nominal, and it corrects §74 immediately:**

| | |
|---|---|
| admissions | 766 |
| in `synthesis` mode | **765** |
| in `calibration` mode | **1** |
| plant admitted | 87 times, first at **action 1, calibration** |

§74 inferred "the calibration frontier is the deciding path" from the plant's
first appearance at action 1. That is true of its FIRST admission and false of
the other 765: selection is overwhelmingly a synthesis-path decision. Gating
calibration therefore displaced the choice rather than removing it, which is
exactly what block 5 measured (25.9% → 40.0%).

### Why "do nothing" wins, in numbers

At the plant's admission the field reads:

| candidate | goal benefit | resource |
|---|---|---|
| **plant** | **0.0000** | 0.0020 |
| f16_raw_effector_004 | **−0.0070** | 0.0000 |
| f16_raw_effector_013 | **−0.0070** | 0.0000 |
| f16_raw_effector_022 | **−0.0070** | 0.0000 |

**Every real effector has NEGATIVE goal benefit.** In steady cruise the model
says acting makes the goal residual worse, so zero is the maximum benefit
available and the only candidate offering it is the one that does nothing.

That is not a broken criterion. It is the criterion correctly reporting that
nothing furthers the goal — and it is precisely the case the second limb of the
definition exists for. **When no action furthers the goal, the benefit that
remains is reduction of surprise**: command the thing that teaches most, not the
thing that does nothing. The plant teaches nothing, because its outcome is
certain; under both limbs together it loses to whichever effector has the most
uncertain outcome.

**And no surprise term exists anywhere in the ranking.** Both functions compute
goal furtherance only. That is the missing quantity, now identified by
measurement rather than by argument, and it explains the whole thread: with only
one limb, "do nothing" is optimal whenever the other limb is flat — which in
cruise is 25.9% of actions.

### What the instrument is for

Every failure in §74 came from not knowing which path decided. That is now a
measurement any future change can start from, and the standing rule it enforces:
**do not change a selection criterion until the instrument says which rule is
making the selection you want to change.**

## §76 — Why none of it worked: this world composes in RUST, not in the seed

`emp_native_mark_composition_choice` makes the composition choice using the Rust
`MotorCompose` term, and it is gated on `native_composition_enabled` — which the
F-16 replication sets to **1.0**. The seed's `singleton_cost`, `program_cost`
and candidate filters belong to the graph-rule composer, which this world does
not use.

**That single fact explains every result in this thread:**

| change | outcome | why |
|---|---|---|
| `singleton_cost` → ratio | byte-identical | not the composer |
| `program_cost` → ratio | byte-identical | not the composer |
| causal gate, 3 `available` filters | byte-identical | not the composer |
| absence-safe causal gate | byte-identical | not the composer |
| **surprise-reduction term** | **byte-identical** | **not the composer** |
| gate the calibration frontier | **25.9% → 40.0%** | calibration IS still graph-side, so this one bit — and displaced selection into the native path |

Six changes, five no-ops and one regression, and the one that moved anything
moved it the wrong way for exactly the reason the others did nothing.

**The selection criterion is `runners/dsl/src/motor_compose.rs`.** Adding
surprise-reduction to benefit — the change §74 and §75 argued for and §75
measured the need for — belongs there, alongside whatever goal term that Term
already computes. The seed-side version added here was reverted: it is dead code
for this consumer, and shipping unmeasured dead code is how the
`never_commanded` predicate in `calibration_frontier` came to be silently
excluding nothing (§74).

### The lesson, which is the same one three times

§61 enumerated six sites and missed that they were not the deciding path. §74
patched five filters without establishing which one decided. §75 built the
instrument that answers "which rule admitted this candidate" — and it reported
`synthesis`, which was true but not specific enough, because the synthesis-mode
choice is made in Rust and the instrument only sees graph state.

**Before changing a decision, find the code that makes it.** Not the code that
looks like it makes it, and not the path that is enabled in some other
consumer's configuration. The instrument should be extended to record whether
the native composer or the rule composer produced the choice — one attribute,
and it would have saved this entire thread.

Reverted; `333.97 / 324.92 / 14763.77`, tree clean.

## §77 — The instrument now names the composer

`probe_selection_attribution.py` records, per admission, which composer made the
choice. Both mark-choice rules stamp `render_choice_seq` on the candidate they
pick and the active composer is fixed by two policy flags, so a fresh stamp
means "the composer chose this" and its absence means calibration or expansion
admitted it.

| scenario | admissions | native `MotorCompose` | calibration/expansion |
|---|---|---|---|
| nominal | 766 | **765** | 1 |
| jammed_rudder | 982 | **960** | 22 |

And for the candidate the whole thread was about:

| | admissions | native | calibration |
|---|---|---|---|
| the plant, nominal | 87 | **86** | 1 |

**One line of output, and six changes would never have been made.** §74's five
patches and §75's surprise term all edited the seed's ranking functions; 765 of
766 choices are made by a Rust Term. The one graph-side gate that did bite —
`calibration_frontier` — governs the single admission per episode that is not
the composer's, which is why gating it displaced selection rather than changing
it.

This is the specific fix for the failure §76 named: the instrument reported
"synthesis", which was true and not actionable, because it saw only graph state.
It now distinguishes WHO decided from WHEN, and the two are different questions.

### Where the surprise term belongs

`runners/dsl/src/motor_compose.rs`. The measurement that motivates it stands
unchanged (§75): at the moment the null option is chosen, every real effector
has goal benefit −0.0070 against the plant's 0.0000, so with only the
goal limb "do nothing" is correct and the second limb is what should break the
tie. The seed-side implementation is written and reverted (§76) and can be
transposed; what it needs is to be added where the choice is actually made, with
the same absence-safe default — a policy that declares no `surprise_weight`
behaves exactly as it does today.

## §78 — Surprise in the native composer: built in Rust, measured twice, reverted

Implemented where the choice is actually made
(`runners/dsl/src/motor_compose.rs`, both `singleton_cost` and `program_cost`),
compiled, installed, and measured in two formulations.

**Form 1 — declared weight `surprise_weight / (1 + experience)`, weight 5.0:**

| | before | after |
|---|---|---|
| nominal | 333.97 | 348.25 (+14.28) |
| jammed_rudder | 324.92 | 345.59 (+20.67) |
| damaged_wing 975 | 14763.77, **crash** | 13330.55, **no crash** |
| damaged_wing 976 | crash | crash, structural **53.76** |
| damaged_wing 977 | crash | no crash, structural **169.73** |

Crashes on the damaged wing improved 3/3 → 1/3 — the first time in this session
anything did. **But it survives by exceeding structural limits 169×**, which is
not a trade, it is a different way to lose the airframe. And 5.0 was a magic
number.

**Form 2 — a ratio with no constant.** Surprise as the fraction of the goal
still uncertain: the goal at stake (weighted squared target, the residual a
perfect candidate would remove) times `1 / (1 + experience)`. Commensurable by
construction, no weight to choose.

| | before | ratio form |
|---|---|---|
| nominal | 333.97 | 352.50 (+18.53) |
| jammed_rudder | 324.92 | 345.59 (+20.67) |
| damaged_wing 975 | 14763.77, crash | 14621.00, crash |
| damaged_wing 977 | 8658.27, crash | 5248.66, crash, structural **832.32** |

Worse. Crediting an unexplored model with the ENTIRE goal at stake is unbounded
optimism: it drives exploration that destroys the airframe five times harder
than the magic number did.

**Both reverted**; `333.97 / 324.92 / 14763.77`, 47 green, tree clean.

### What the two measurements establish

The surprise limb is REAL — form 1 is the only change in this session that
reduced damaged_wing crashes — and **its magnitude cannot be set either by a
constant or by the goal at stake.** Too little and nothing changes; too much and
the airframe is torn apart exploring. Both attempts sat on the wrong side of
that, in opposite ways.

What is missing is a bound: exploration must be worth its RISK, not just its
information. The loop already measures the risk —
`structural_model_prediction` and the `state_safe_*` envelope are exactly what
the exploration blew through, at 169× and 832× — and neither formulation
consulted it. A surprise term that is priced against the structural envelope has
somewhere to stop; one priced against the goal does not.

That is the third limb this session has run into and not built: goal
furtherance, surprise reduction, and **what the attempt costs if it goes wrong**.

## §79 — The third limb is the risk matrix: irreversibility and thermodynamic cost

Benefit is furtherance of goals or reduction of surprise (§74). What §78's two
formulations both lacked is the other side of the sd loop's own risk process:
**what the attempt costs if it goes wrong**, priced by IRREVERSIBILITY and
THERMODYNAMIC COST.

Both failures are the same failure under that reading. Each credited an
unexercised effector with the full information value immediately — the whole
goal at stake, at any amplitude, on the first attempt — so the composer
commanded maximally and went through the structural envelope at 169× and 832×.
Neither asked what would be unrecoverable if the attempt was wrong.

**And this tree already implements the correct discipline, in the one place it
worked.** The probe ladder (§V) does not ask "is this effector worth
exercising"; it pushes a LITTLE, reads, and escalates only if the small push did
not answer. Cheap and reversible first, expensive and irreversible only when the
cheap attempt has failed — Occam ordering as a risk ordering, which is exactly
the sd loop's ladder one level down: recognise, else transform, else infer, else
mint, each rung costing more than the last.

**The surprise limb must be CLIMBED, not jumped.** That is the missing structure,
and it is why no magnitude worked: a term that grants full exploration value up
front has no rung to stand on, so any weight is either too small to matter or
large enough to destroy the airframe. There is no correct scalar because the
quantity was never scalar.

### Both risk terms are already measured in this tree

- **Irreversibility** — the terminal versus achievability-only distinction
  `_axis_time_budgets` already draws (block R: altitude→ground and speed→stall
  are terminal, heading and sideslip are not), the structural envelope
  `state_safe_*`, and ground contact. Exceeding structural limits is not a cost,
  it is an ending.
- **Thermodynamic cost** — the two-column energy ledger, mechanical plus
  convertible fuel, with the reserve ratchet. Exploration spends energy that
  does not come back.

Neither is consulted by any selection in this system. Both exist, both are
measured every action, and the composer's cost function reads neither.

That is the shape of the next build, and it is not another weight: **exploration
priced by what it cannot undo, climbed a rung at a time, stopping when the rung
answers.** The probe ladder is the working precedent and the risk terms are
already instrumented — which makes this the best-specified piece of work left in
this line, and the reason to stop here rather than attempt a third scalar.

## §80 — Risk is relative: least-worst, not "ones that aren't bad"

The risk bound was built (`motor_compose.rs`, headroom = the fraction of the
structural envelope a candidate would leave, worst key, multiplying the
information term) and measured:

| | baseline | risk-bounded |
|---|---|---|
| nominal | 333.97 | 363.34 (+29.4) |
| jammed_rudder | 324.92 | 344.36 (+19.4) |
| damaged_wing 975 | crash, struct 1.68 | crash, struct 1.58 |
| dw 976 | crash | crash, struct **11.66** (unbounded: 53.76) |
| dw 977 | crash | crash, struct **1.53** (unbounded: 169.73 / 832.32) |

**The bound works: 832× → 1.53.** And the crash improvement from §78 vanished
with it — back to 3/3, with tracking worse everywhere. Reverted;
`333.97 / 324.92 / 14763.77`, 47 green.

### Two things this establishes

**§78's crash improvement was bought entirely by unpriced risk.** Once the risk
is priced, it disappears. The damaged wing was never saved by a better choice —
it was saved by a recklessly expensive one at 169× structural load. That result
is retired, not reproduced.

**And the bound is the wrong shape, for a reason worth more than the build.**
It is ABSOLUTE: multiplying by remaining envelope means that when the envelope
is gone, every option scores zero and none is preferred. That is "choose among
the options that aren't bad" — which has no answer in a departure, where every
option is bad. **Risk is relative. The question is always the LEAST WORST
option, never the acceptable one.** An absolute bound produces paralysis exactly
when the situation is worst, which is precisely where it was needed and exactly
what the measurement shows: it removed the reckless exploration and put nothing
in its place.

### The same shape, a third time

- containment vs dominance: dominance compares corners to each other, and
  membership is invariant under any uniform repricing — the comparison had to
  become one against what the plant affords (block S/Y);
- activation energy: a fixed 80-action wait was longer than the process it
  governed; the workable form was measured lag plus one action (block X);
- risk: an absolute envelope fraction paralyses; the workable form is a ranking
  among the available options.

**Absolute thresholds fail where relative comparisons work**, and this line has
now paid for that lesson three times in three different subsystems. The next
formulation should rank candidates by risk against each other and take the
least-worst — never gate them against a fixed acceptability. Not attempted here:
that is a fourth formulation of the same term at the end of a session in which
every unmeasured build was reverted, and the ranking form deserves a prereg and
a full block of its own.

## §81 — Is damaged_wing survivable at all? The target is not established

Before ranking risk against a target, the target was checked. It does not hold
up.

**Our fault magnitudes are a reconstruction, not the paper's.** The replication's
own limitations list says so: *"Broken-aileron parasitic moment magnitude is not
published"*, *"Reward scales and crash thresholds are not published"*, *"PID
gains, control limits and evaluation seeds are not published"*.

**And what we reconstructed is not a damaged airframe, it is an unstable one:**

| term | value | meaning |
|---|---|---|
| `lift_alpha` | 0.7 | 30% lift loss |
| `roll_aileron` | 0.5 | **half** the aileron roll authority |
| `roll_beta` | **−1.0** | dihedral effect **sign-inverted** |
| `roll_r` | **−1.0** | yaw–roll coupling **sign-inverted** |
| `yaw_aileron` | 1.5 | adverse yaw increased 50% |

Two stability derivatives have their SIGN flipped. That is not damage, it is a
divergent airframe.

**Measured evidence that it is beyond control, not merely hard:**

- `extreme_body_rate` and `engineering_envelope_violation` in **3/3** episodes,
  including the one that does not hit the ground. Every other scenario: 0/3.
- Roll authority is below roll demand on **12.8%** of actions (§AH) — the best
  effector cannot match the departure, by measurement.
- **Ablation**: restoring full aileron authority (`roll_aileron` 0.5 → 1.0,
  every other term unchanged) saves one seed of three and leaves
  `extreme_body_rate` TRUE on all three. **The aircraft departs regardless of
  how much aileron it has**, so the halved authority is not the cause — the
  inverted derivatives are.

**The paper's `crash_rate` 0.0 is not a like-for-like reference.** Its crash
threshold is unpublished, its fault magnitudes are unpublished, and its return
on this scenario (−310.98 against −124.61 nominal) is its worst by far, so its
controller also does badly here by its own measure. Our `crash` and
`paper_like_crash` agree with each other (2/3 both), so the discrepancy is not
in our crash criterion — it is in the scenario.

### What this means for the work

**Every attempt in this session to "save the damaged wing" was optimising
against a target that has not been shown to be achievable by any controller.**
That does not invalidate the findings — the probe ladder, the quorum stop, the
selection instrument and the jam result all stand on their own scenarios — but
it does invalidate damaged_wing as a success criterion, and several blocks were
judged partly by it.

The ranking form of the risk term should NOT be run against damaged_wing as its
gate. The honest sequence is: first establish a damaged_wing configuration that
some controller survives — by reverting the sign inversions to a scaled-down
magnitude and confirming the existing controller can fly it — and only then use
it to judge a selection change. Running a full block against a possibly
unflyable configuration is precisely the waste this line has already paid for
elsewhere.

## §82 — The limits are calculable, and most of them are already instrumented

§81 answered "is this survivable?" by measurement rather than by trying harder,
and that generalises: the viability limits are computable from quantities this
loop already publishes. They form a LADDER of nested questions, each one the
containment question asked at a wider scope.

| limit | the question | instrument | status |
|---|---|---|---|
| **controllability** | can authority match demand? | `authority / demand` per axis | **measured** — zero false positives in ~21k samples, and it is what says damaged_wing is beyond control 12.8% of the time (§AH) |
| **metastability** | is there a steady state I can hold, even a degraded one? | the axis clocks, and the trim/orbit corners that declare one | **partly** — the clocks exist, the corners assert rather than test |
| **survivability** | will the structure hold what I must do? | `state_safe_*` against `structural_model_prediction` | **measured** — it is what the 169× and 832× readings blew through (§78) |
| **range** | how far can I still go? | the two-column ledger, mechanical + convertible fuel, with the reserve ratchet | **measured**, and never consulted by a decision |
| **possibility to land** | is a survivable terminal state reachable? | reach × time to a declared touchdown envelope | **not present** — needs a terminal-state declaration |
| **ejection window** | is a survivable ABANDON state reachable? | reach to a declared altitude/airspeed band | **not present** — needs the band declared |

Four of six already exist and are measured every action. Two need a
declaration from the consumer, and neither needs new machinery — both are "can
I reach a declared region", which is exactly what `f16_goal_containment`
computes for altitude, heading and speed today.

### Why this is the right frame and not another corner

The ladder answers a different question from "which corner". It asks **which
outcomes remain possible**, and that ordering IS the goal hierarchy: if
controllability is gone, landing is not a goal; if landing is gone, reaching an
ejection window is; if that is gone, what remains is minimising the energy at
impact. The goal does not choose from a fixed library — it chooses from the
limits that still hold, which is "the plant provides the manifold, the goal
chooses from within" applied to OUTCOMES rather than to axes.

It is also relative in the sense §80 required. The ladder never asks "is this
acceptable"; it asks "what is the highest rung still available", which always
has an answer, including when every rung but the last is gone. An absolute
bound paralyses in a departure; a ladder always names the least-worst
surviving option.

### And it retires the way this session judged itself

Every block was scored on tracking error and crash rate — outcome metrics that
say nothing about which limits were live. damaged_wing failed every rung of the
ladder from action ~140, so RMSE against a reference altitude was measuring the
descent rate of an uncontrollable airframe, and eight blocks were tuned against
it (§81). Had controllability been evaluated first, the scenario would have been
recognised as beyond control on the day it was built, and the effort spent on
the rungs that were still live.

## §83 — The rung was a no-op, and the ladder is not about aircraft

**Built and measured** (`motor_compose.rs`): structural admissibility as a RUNG
rather than a gate — prefer candidates that keep the structure intact, and if
none does, still choose the cheapest of those that do not.

nominal `333.97`, jammed_rudder `324.92`, damaged_wing `14763.77` — **all three
byte-identical.** Prediction 2 falsified, and §67 already contained the reason:
**five models have zero structural increment** (the `cmd = 0.0` member of each
group, plus the airframe), so when the interrupt fires the escape branch keeps
them admissible. The gate never empties, so the paralysis it was meant to fix
does not occur by this path. Reverted.

Worth stating plainly: the fix was for a failure mode inferred rather than
observed. §80's diagnosis — that absolute bounds paralyse — is sound and was
measured for the *surprise* term, where the headroom multiplier drove
exploration to zero. Transferring it to structural admissibility without
re-measuring was the same mistake this session has made repeatedly: **a
diagnosis established in one subsystem is a hypothesis in the next.**

## §84 — The same ladder answers an incoming missile

The viability ladder is not about damage. An incoming missile poses exactly the
questions §82 enumerates, against exactly the same instruments:

| | damaged airframe | incoming missile |
|---|---|---|
| controllability | can authority match the departure? | can authority match the evasion the intercept demands? |
| metastability | is there a degraded steady state? | is there a state the threat cannot reach? |
| survivability | will the structure hold the recovery? | will the structure hold the evasion? |
| range | how far on remaining energy? | can I outrun or outlast it? |
| landing / ejection | is a survivable terminal state reachable? | unchanged |

The only difference is a SIGN. A goal is a region to reach; a threat is a region
to avoid. Containment already computes "can I reach a declared region" for
altitude, heading and speed — reachability of a region to avoid is the same
computation read the other way, and the manifold is bounded by both.

That is why the ladder belongs in the general seed and not in a consumer.
Nothing in "controllability, metastability, survivability, range, terminal
state" mentions an aircraft, and the same five questions bound a car avoiding a
collision, a joint approaching its stop, and a body deciding whether a step is
recoverable. A threat is another constraint on the manifold, and the goal still
chooses from within what remains.

It also sharpens what §82 said was missing. "Possibility to land" and "ejection
window" were described as needing a declared REGION — and a threat needs the
same declaration with the opposite sense. One mechanism, declared per consumer:
regions to reach and regions to avoid, with the ladder reading reachability
against both.

## §85 — The region contract: reach and avoid are one declaration (cre v7.5.0)

`cre_project_region_reachability` adds the reach side of the viability ladder to
the general seed's contract:

```
region_axis_ordinal   which channel the region is expressed on
region_gap            measured distance to it, in that channel's rate units;
                      zero or negative means already inside
region_sense          +1 reach, -1 avoid
```

and publishes, per region:

```
region_actions        integer actions until the gap closes at the measured
                      rate -- the horizon when it is not closing, since a
                      region you are not approaching is on no clock
region_inside         1.0 when the gap is already closed
```

**Reaching a goal and being reached BY a threat are the same closure.** The
arithmetic is `gap / rate` either way; `region_sense` records only whether the
number is an opportunity or a deadline, and the rule never reads it. That is why
a landing envelope, an ejection window and an incoming missile are one
declaration rather than three subsystems — each is a region, a measured
distance, and a direction you want that distance to go.

**Domain-free and asserted so**: the rule names no vehicle, no threat, no axis,
and the general seed still contains none of the domain words. The same
declaration serves a car approaching a collision or a joint approaching its
stop.

**Absence-safe and verified**: no consumer declares a region yet, so the rule
never fires and all three scenarios are unchanged — `333.97 / 324.92 /
14763.77`, 50 green.

### What it completes and what it does not

§82 listed six viability limits and found four instrumented. The two missing —
possibility to land, reachability of an ejection window — were missing the same
thing: a way to declare a REGION and ask whether it is reachable. That now
exists, and §84's threat case comes with it at no additional cost, which is the
sign the abstraction is at the right level.

What does not exist yet is a consumer declaring any region, and the ladder that
reads them. The contract is the half that belongs in the general seed; the
declarations are per-consumer, and the ordering — controllability, then
metastability, then survivability, then landing, then ejection — is the
selection criterion §82 argues for and this session did not build.

## §86 — The ladder, declared and measured: it reads the failure in order

The F-16 declares one region — **the terrain** — because it is the only one this
airframe can state from measurements alone: the gap is the altitude, the closing
rate is the sink rate, and the general seed's region contract turns those into
`region_actions`, i.e. TIME TO GROUND, computed by a rule that does not know
what ground is. No stall speed, no landing envelope, no thresholds invented.

`f16_publish_viability_rung` then orders what remains:

```
3  CONTROLLABLE   best effector's roll authority >= the roll demand
2  SURVIVABLE     structural envelope intact
1  TERRAIN CLEAR  actions-to-ground exceeds the decision horizon
0  none of these
```

**Measured, one episode each, and it discriminates completely:**

| scenario | rung distribution over 1000 actions |
|---|---|
| nominal | **3: 1000** |
| jammed_rudder | 3: 957, 2: 43 |
| damaged_wing | **0: 722**, 1: 42, 2: 115, 3: 121 |

And the damaged_wing trace reads the failure in the ladder's own order:

| action | rung | controllable | survivable | terrain clear | actions to ground |
|---|---|---|---|---|---|
| 151 | 2 | **0** | 1 | 1 | 668 |
| 401 | 0 | 1 | 1 | **0** | **15** |
| 701 | 0 | 1 | **0** | 0 | **0** |

Control is lost first, terrain closes second, structure fails third. That is the
sequence §81 inferred from crash flags, now readable directly, and it confirms
independently that 72% of that episode has no viability limit holding at all.

All three pins unchanged — stamped only, nothing consumes the rung yet.

## §87 — The aircraft is budget, not constraint

The ladder says what remains possible. It does not say which rung is
acceptable — and it cannot, because **the airframe is a resource to be spent in
service of a goal, not a constraint to be preserved.** Accepting structural
damage, or spending the aircraft entirely and reaching the ejection window, is
correct when the goal is worth more than the airframe.

That is why every absolute bound in this session failed. "Do not exceed the
structural envelope" is not a fact about flight, it is a price quote: exceeding
it costs the airframe, and whether that is worth paying is set outside the
aircraft. §78's 169× structural utilisation was not simply wrong — it was an
unpriced purchase, made without anything having decided the aircraft was worth
spending.

So the rungs are prices in irreversibility, and the mission is the budget. The
ladder makes the prices legible; it deliberately does not set the budget, and a
consumer that wants a criterion must declare what it is willing to spend. That
is the last declaration this line is missing, and it belongs to the operator,
not the airframe.

## §88 — The operator declares the budget (cre v7.6.0)

The last declaration this line was missing, and the one thing the loop cannot
derive:

```
regime_viability_rung     published by the CONSUMER -- the highest limit that
                          still holds, on whatever ladder it defines
regime_goal_worth_rungs   declared by the OPERATOR -- how many rungs this goal
                          is WORTH.  Absent reads 0.
regime_spend_floor        published by the general seed -- the lowest rung the
                          loop is authorised to end at, `rung - worth`, never
                          below zero
```

**Measured, and the default is exactly today's behaviour:**

| scenario | rung | spend floor | authorised |
|---|---|---|---|
| nominal | 3: 1000 | **3: 1000** | 0.0 |
| damaged_wing | 0: 722, 1: 42, 2: 115, 3: 121 | **identical distribution** | 0.0 |

With no worth declared, the floor equals the rung on every action: spend
nothing, preserve everything. All three pins unchanged, 50 green.

### Why this had to be a declaration

Every absolute bound in this session failed the same way, and §87 named it: a
limit was treated as a fact about the body when it is a PRICE. "Do not exceed
the structural envelope" is a quote — exceeding it costs the airframe — and
whether that is worth paying depends on what the goal is worth. **That is
information the body does not have and cannot derive.** §78's 169× was an
unpriced purchase; the risk bound that replaced it refused to purchase at any
price. Neither had a budget, so neither could be right.

The three pieces are now separate and each is in the only place it can be:

- the **ladder** makes the prices legible, in the consumer, from measurements;
- the **budget** is declared by the operator, outside the loop entirely;
- the **selection** that spends against it is deliberately NOT built.

That last omission is the point rather than an oversight. A criterion that
consulted `regime_spend_floor` would be the fourth formulation of a selection
rule in this session, and the previous three were reverted for being built ahead
of the measurement that would judge them. What exists now is the measurement:
the rung is readable, the floor is readable, and any future criterion can be
scored on whether it spends within the budget it was given.

## §89 — The budget is denominated in irreversibility, and then the decision is trivial

The rungs are not arbitrary levels. They are ordered by **how permanent the loss
is**, and that is the currency the budget is paid in:

| loss | reversibility |
|---|---|
| a goal missed | recoverable — try again |
| controllability | often recoverable — unload, gain speed, re-establish |
| structural margin | **permanent damage to the airframe** |
| the airframe | gone, but the pilot is not |
| the pilot | **irreversible, and dominates everything above it** |

Denominated that way, **saving the pilot at the expense of the airframe is a
trivial decision.** It needs no Pareto frontier, no dominance relation, no
cost/benefit ratio and no tuned weight: the ordering is total, the cheaper
irreversibility is spent first, and the answer follows from the ladder without
deliberation.

### Which means the hard part was never the choice

Everything this session spent itself on — dominance, containment as a selector,
allocation budgets, tie-breaks, cost/benefit, surprise terms, risk bounds — was
machinery for deciding between options. **The decision is trivial once the
observations are trusted.** What is genuinely hard, and what the instruments
that survived actually address, is CONFIDENCE:

- the probe ladder localises a dead effector in **ten observations**, because
  the information is in the threshold, not the count (§V);
- escalation completeness turns those ten into a verdict — 0.899 → 0.0000 for a
  dead rudder on the same evidence (§W);
- quorum distinguishes *an effector died* from *the plant changed*, and declines
  to claim an explanation when none exists (§W addendum);
- the viability ladder reads which limits still hold, in order, from
  measurements (§86).

Those are the pieces that worked, and every one of them is an observation
instrument. Every piece that failed was a selection rule. **This line's error was
treating a confidence problem as a decision problem for most of its length** —
which is why eight blocks of selection work moved nothing on damaged_wing while
one stop rule, gated on a confident observation, took the jam from 11391 ft to
803.

### What remains genuinely declarative

The ordering of irreversibility is itself a declaration — pilot above airframe
above mission — but it is a STABLE one, made once by an operator, not tuned per
scenario. That is the difference between a declaration and a magic number, and
it is the same distinction that separated every value that held this session
from every value that did not.

## §90 — Correction: the ordering is LOG, not lexicographic — and that is machinery

§89 said the decision needs "no Pareto frontier, no dominance, no cost/benefit,
no weight — the ordering is total". **That is wrong, and the error matters.**
A total ordering with no arithmetic is LEXICOGRAPHIC: it makes the pilot
infinitely valuable, forbids every trade across the boundary, and would refuse
to spend a life to save a city. Nothing is infinitely valuable.

The correct model is **logarithmic**. The pilot is orders of magnitude above the
airframe — not incommensurable with it — so:

- trades WITHIN a rung are ordinary arithmetic, as they always were;
- trades ACROSS a rung need a large multiple, which is what "orders of
  magnitude" means precisely rather than rhetorically;
- **only a goal of sufficient wider impact beats a pilot**, and "sufficient" is
  computable: on a log scale, breadth of impact accumulates, so a goal affecting
  enough others exceeds a single irreversible loss by the same arithmetic that
  compares any two quantities.

That IS machinery, and it is machinery this tree already has. A log scale is a
CROSS-FRAME MAP, and `scale2` is already a `DimensionGenerator` the sd loop
mints — "a base IS a dimension" (root CLAUDE.md, base-as-dimension). Value in
log-irreversibility is a dimension like any other, and comparison on it is
addition.

It also keeps the no-magic-number rule intact. The declaration is a set of
RATIOS — how many orders of magnitude separate an airframe from a life — made
once by an operator and stable across scenarios. The arithmetic that consumes
them is generic. That is exactly the line §89's last paragraph drew between a
declaration and a tuned constant, and the log form is what lets a declaration be
a ratio instead of a threshold.

**What §89 got right** is that the hard part is confidence, and that every
instrument which survived this session is an observation instrument. What it got
wrong is the shape of what confidence feeds: not a lookup, but a comparison on a
log-scaled dimension of irreversibility, where the trade is available and merely
expensive.

## §91 — Log-irreversibility declared, and why refusing to name a number does not remove it

**General seed (cre v7.7.0)** — value is log-irreversibility, and the operator's
declaration is a RATIO:

```
regime_rung_decade      how many log units separate ADJACENT rungs, i.e. how
                        much more permanent each loss is than the one below
regime_goal_worth_log   what this goal is worth, in the same units
regime_spend_floor      rung - (worth / decade), floored at zero
```

The division is the log scale doing the work: a worth of two decades buys two
rungs, half a decade buys none. Nothing is infinitely valuable, so no rung is
unbuyable — and absence degrades to "spend nothing", which is the SAFE reading
of the lexicographic ordering, not the correct one.

**F-16 consumer (v8.62.0)** declares both, and the second one is the honest part:

```
regime_rung_decade    1.0   one order of magnitude per rung -- losing structural
                            margin is ~10x more permanent than losing
                            controllability, and the airframe ~10x again
regime_goal_worth_log 0.0   ZERO, deliberately: this study is reference
                            tracking, and no altitude error is worth an
                            irreversible loss
```

Measured: `spend_floor` equals the rung on every action of every scenario,
`authorised` 0.0, all three pins unchanged, 50 green. A mission that WAS worth
an airframe would declare a positive worth **there and nowhere else**, and not
one rule would change.

### Nothing is absolute, and refusing to say the number does not remove it

The reason this is a declaration rather than a constant is not squeamishness
about pricing a life. It is the opposite. **People who say a number cannot be
put on something are declining to say what the number is, in what frame — and
the number still exists**, because the decision still gets made. Refusing to
declare it does not produce infinite value; it produces an UNEXAMINED value,
applied inconsistently and invisibly.

This contract makes that unavoidable. Declaring nothing is not "the pilot is
priceless" — it is `worth = 0`, spend nothing, and it is now legible in a trace
as exactly that. The default has not changed behaviour anywhere; what changed is
that the implicit price is written down, and an operator who disagrees with it
has one attribute to argue about instead of a scattered set of thresholds to
discover.

**"In what frame" is the load-bearing half.** A number without its frame is what
makes people believe the quantity does not exist — the same invariant the root
CLAUDE.md states for measurement (in-frame is integer, ratios are cross-frame).
Log-irreversibility IS the frame, `regime_rung_decade` is the scale, and once
both are named the comparison is ordinary arithmetic on a dimension the sd loop
already knows how to mint.

## §92 — Selection that spends the budget: built, and it starves the scenario that needed to look

Two changes (cre v7.8.0, f16 v8.63.0). The floor was corrected to measure from
the HIGH-WATER rung rather than the current one — `rung - worth` tracks the
descent and can never be violated, which is a ratchet, not a budget. And the
probe stop gained a second trigger: stop the checklist when
`regime_budget_exhausted`.

Probing is the one thing this loop does deliberately at a cost, so it is the
right first consumer. With worth 0.0 the floor is the high-water rung and any
viability loss exhausts the budget.

| | before | with the budget |
|---|---|---|
| nominal | 333.97 | **unchanged** |
| jammed_rudder 975 | 324.92 | 334.60 (+9.68) |
| jammed_rudder 976 | — | 1058.84, no crash |
| damaged_wing 975 | crash | **no crash**, 13890.64, struct 1.55 |
| damaged_wing 976 | crash | **no crash**, 4613.61, struct 8.63 |
| damaged_wing 977 | crash | crash, struct 1.54 |
| **damaged_tail 975** | **no crash** | **CRASH**, struct 27.48, min alt −15.0 |

damaged_wing improves 3/3 crashes to 1/3 — the best result any change has had on
it, and without the structural blowout of §78. **And damaged_tail regresses from
no-crash to crash.** Prediction 4 falsified; reverted.

### Why, and it is the interesting part

With worth declared as zero, the loop refuses to spend ANYTHING to find out —
and on damaged_tail, finding out is what was keeping it alive. The checklist
stops the moment viability dips, so the tail fault is never localised, and a
scenario that survived by probing now does not.

**"Do not look when you cannot afford to find out" is exactly wrong when looking
is what saves you.** Information has a value that the budget, as declared, does
not represent: `regime_goal_worth_log = 0.0` prices the GOAL at nothing, and
correctly refuses to spend the airframe chasing an altitude reference — but the
probe is not spent on the goal, it is spent on knowing which limits still hold.
Those are different purchases and this build charged both to the same account.

That is the third limb again (§79), and it says the budget needs to distinguish
**spending for the goal** from **spending to reduce uncertainty**. A mission
worth no airframe may still be worth the fuel to find out whether it has one.
An operator declaring a single worth cannot express that, and the fix is another
declaration rather than another rule — which is where this line's evidence keeps
pointing.

Reverted: `333.97 / 324.92 / 14763.77`, damaged_tail back to no-crash at
struct 0.64, 39 green.

## §93 — Two accounts on one scale: the goal, and knowing

**cre v7.8.0** adds the second account, and **f16 v8.63.0** charges the probe to
it:

```
regime_goal_worth_log          what the OBJECTIVE is worth        (f16: 0.0)
regime_information_worth_log   what KNOWING is worth              (f16: 1.0)
regime_rung_decade             log units between adjacent rungs   (f16: 1.0)
regime_spend_floor             high_water - goal_worth/decade
regime_info_spend_floor        high_water - info_worth/decade
```

Both accounts use the same scale and the same arithmetic; they differ only in
what they authorise. The probe consults the information account, because a
probe buys knowing, not the objective.

**Measured — all four scenarios unchanged:**

| | result | crash | was |
|---|---|---|---|
| nominal | 333.97 | False | unchanged |
| jammed_rudder | 324.92 | False | unchanged |
| damaged_wing | 14763.77 | True | unchanged |
| **damaged_tail** | 8172.28 | **False** | **regression fixed** |

### The trade this makes explicit, and why unchanged is the right answer

§92 charged the probe to the GOAL account, which the operator had declared worth
zero. That stopped the checklist at the first lost rung — which improved
damaged_wing (3/3 crashes → 1/3) and crashed damaged_tail, a scenario that
survives BY probing. **The damaged_wing improvement was starvation, not skill**,
and separating the accounts gives it back along with the regression. That is the
correct trade: §81 established damaged_wing is beyond control anyway, so an
improvement bought by not looking was never a controller result.

At the declared information worth of one rung, the budget does not bind during
the probe window — damaged_wing loses its second rung around action 401, long
after the passes at ~101 finish — so nothing changes anywhere. **The contract is
landed, correct, and currently inert at the declared value**, which is the safest
state for a mechanism whose whole purpose is to let an operator change it.

An operator who declares `regime_information_worth_log` 0.0 gets §92's behaviour
exactly, including the damaged_tail crash. That is not a defect: it is the
declaration meaning what it says — *do not spend anything to find out* — now
visible as one attribute rather than emergent from a rule.

### What this line ends with

The three quantities are separated and each sits where only it can:

- the **ladder** makes prices legible, in the consumer, from measurements;
- the **two budgets** are declared by the operator, outside the loop, as ratios
  on a log scale where nothing is infinitely valuable;
- the **spending** consults them, and the one consumer built (the probe) charges
  the right account.

Every value that held this session was a declared ratio; every value that failed
was a rule inferring what should have been declared. That is the single
generalisation this line supports, and it now has a contract shaped like it.

## §94 — Damaged-wing assessment finished: the sign inversions are the killer

§81 showed the scenario departs even with full aileron authority restored, and
inferred the inverted derivatives were responsible. That is now measured.

**Ablation, all three seeds, existing controller unchanged:**

| configuration | crash | extreme rate | min alt |
|---|---|---|---|
| `roll_beta −1.0, roll_r −1.0, roll_aileron 0.5` (ours) | **3/3** | **3/3** | −15 … +2.9 |
| `roll_beta −1.0, roll_r −1.0, roll_aileron 1.0` (§81) | 2/3 | **3/3** | departs anyway |
| **`roll_beta +0.5, roll_r +0.5, roll_aileron 0.5`** | **0/3** | **1/3** | 2660 / 2.0 / 1.3 |

With the derivative SIGNS restored — still 30% lift loss, still half the aileron
roll authority, still 50% more adverse yaw, and the roll derivatives still at
half magnitude — **the existing controller survives all three seeds with no
change to any rule.**

So the aircraft is not unflyable because it is damaged. It is unflyable because
two stability derivatives were reconstructed with **inverted signs**, which
makes the airframe divergent in roll–sideslip rather than degraded. That is a
modelling choice of ours, and the paper publishes neither the magnitudes nor the
crash threshold to check it against.

### What this settles

- **damaged_wing as configured is not a controller benchmark.** No selection
  change can pass it, and eight blocks were partly judged by it (§81). The
  measurement above is the evidence, not the inference.
- **A survivable configuration exists and is one line away.** `roll_beta` and
  `roll_r` at `+0.5` gives a genuinely damaged wing — lift loss, halved roll
  authority, adverse yaw — that the current controller flies. That is the
  configuration a future block should gate on, because a scenario nothing can
  survive cannot distinguish a good controller from a bad one, and a scenario
  everything survives cannot either. This one sits where the existing controller
  is marginal: one seed still shows extreme body rate, and two end within 2 ft
  of the ground.
- **The paper comparison remains open and probably unresolvable.** Its
  `crash_rate` 0.0 is measured against an unpublished threshold on unpublished
  magnitudes, and its return here (−310.98 against −124.61 nominal) is its worst
  by a wide margin. The honest statement is that we do not know whether its
  damaged wing resembles ours, and cannot from what is published.

**Not changed here.** Editing the scenario mid-session would invalidate every
measurement in this document against a baseline that no longer exists. The
change belongs at the start of the next block, declared in its prereg, with the
whole suite re-baselined.

### A process hazard worth recording

The ablation was run by rewriting the scenario file, and the shell command that
was meant to restore it was killed by a tool timeout before the restore ran. The
tree sat with a silently modified `damaged_wing` — any run started in that
window would have been attributed to the wrong configuration. Caught by checking
the file rather than assuming the cleanup, and the baseline was re-measured to
confirm (`14763.77`, crash True).

**A cleanup that lives in the same command as a long-running measurement is not
a cleanup.** It should be a separate step, or the measurement should write to a
copy.

---

## §95 — Locating the gap precisely: the ladder prices the marginal action, not the path that reached it

Owner's framing, given directly and quoted rather than paraphrased: *"the
standard risk gating is only by thermodynamic reversibility - but it also
needs to include sunk cost and ticks."* Before touching literature I want to
state precisely what §89-93 built, so the gap is located rather than gestured
at.

The ladder as it stands prices exactly one thing: **what THIS candidate action,
taken from THIS state, would cost if it goes wrong** — read off
`regime_viability_rung` (§86), converted to a spend against `regime_spend_floor`
/ `regime_info_spend_floor` (§88, §93), denominated in log-irreversibility
(§90-91). Every input to that arithmetic is FORWARD-looking and MARGINAL: the
rung the candidate would land on, the worth the operator declared for the goal
or for knowing. Nothing in it reads how the aircraft got to the state it is
evaluating from — not the rung history further back than the single high-water
mark, not the fuel already spent, not how many actions have already been
taken.

That is not a vague complaint about "context." It is two SEPARATE, precisely
different omissions, and the owner's own phrasing keeps them apart on purpose
— I am going to hold them apart too, because §92 is a documented example of
exactly this line conflating two different accounts (goal spend and
information spend) and paying for it with a regression before separating them
again. Collapsing sunk cost and ticks into one "the past matters too" term
would be the same mistake a third time.

- **Sunk cost**: what has already been committed — resources, foreclosed
  alternatives — changes how much further loss is tolerable, HOLDING THE
  MARGINAL ACTION'S OWN IRREVERSIBILITY FIXED. Two candidates with identical
  forward risk are not equally risky if one arrives at that risk having spent
  most of its budget and the other has spent almost none.
- **Ticks**: the passage of time itself, independent of any state change, has
  a cost — because a tick is the substrate's own fundamental unit of anything
  happening at all, and because a tick spent not acting is a tick a threat,
  competitor, or expanding rival got to spend advancing, whether or not this
  consumer has declared that rival as a region.

Both connect to material this document already has and did not wire in: §3.4's
Dixit & Pindyck citation (real options, read again below in more depth) and
§79's "both risk terms are already measured in this tree" — which turns out to
undersell how much is already there, once I went looking specifically for
these two.

## §96 — Sunk cost, grounded: a real quantity with the same name as a bias

The phrase "sunk cost" is contaminated by its own most famous finding, and the
owner's framing is explicit that this is NOT that finding: *"not the sunk-cost
fallacy... the opposite: what has ALREADY been spent... is itself part of what
is at stake if the current path fails, independent of whether the marginal
next action is reversible."* Worth verifying the fallacy precisely so the
distinction is not asserted against a strawman.

**The fallacy, as the literature actually states it.** Arkes & Blumer, "The
Psychology of Sunk Cost," *Organizational Behavior and Human Decision
Processes* 35(1), 124-140 (1985) — the source paper for the term in behavioural
economics. Their finding: people persist with a chosen course of action IN
PROPORTION TO how much they have already invested in it, even when the
marginal, forward-looking expected value of continuing is lower than an
alternative — because abandoning feels wasteful. Staw, "Knee-Deep in the Big
Muddy: A Study of Escalating Commitment to a Chosen Course of Action,"
*Organizational Behavior and Human Performance* 16(1), 27-44 (1976) is the
earlier, related finding — escalation of commitment is worse when the person
continuing is personally responsible for the original decision. **The
fallacy's shape: past cost is used to justify a decision whose FUTURE PAYOFF
it cannot affect.** That is irrational because bygones are bygones for the
forward calculation — the $10 already spent on a bad ticket does not change
whether the show tonight is worth attending.

**What the owner is pointing at is a different mathematical object, and it
survives the "bygones are bygones" objection because it isn't making the
mistake the objection is aimed at.** It is not claiming the past changes the
FORWARD PAYOFF of the marginal action. It is claiming the past changes the
STAKE — what is lost, GIVEN failure — which is a fact about the state the
agent is IN, not a reason to keep acting a certain way. Two claims that look
similar and are not: "keep going because of what I've spent" (the fallacy,
comparing sunk cost against a decision whose payoff it cannot move) versus
"weigh this loss more heavily because of what I've spent" (a claim about the
MAGNITUDE of the stake, not about whether to persist). The ladder already has
exactly the right shape to hold the second claim without smuggling in the
first: it never asks "should I persist," only "how much room is left before
the floor," and adding a term to the floor cannot produce escalating
commitment because the floor governs REFUSAL, not continuation.

**Dixit & Pindyck, *Investment under Uncertainty* (Princeton, 1994) — read
again, in context, as the brief asked.** Already cited in this document at
§3.4 for its headline (irreversible commitment carries an option value naive
NPV misses). Read specifically for the sunk-cost treatment: their own
vocabulary makes "sunk" and "irreversible" close to synonymous from the start
— a cost is sunk precisely when it cannot be recovered, which is their
definition of investment irreversibility, and the book's central formal move
is that the OPPORTUNITY COST OF INVESTING NOW — the value of the option to
wait, which is destroyed the moment the sunk cost is paid — must be added to
the price of investing, not treated as a separate soft consideration.
`[unverified in depth]`: I read this through search-returned excerpts and a
public PDF of the book rather than the full text end to end, so I am not
claiming to have verified every derivation; the headline claims (sunk =
irrecoverable; the lost option value is a real cost, not a sentiment) are
corroborated by multiple independent secondary sources and match the book's
stated framework.

**What this buys, precisely stated:** in Dixit & Pindyck's own terms, the
existing ladder's `irreversibility` axis (§89-91) is ALREADY a real-options
sunk-cost price — for the MARGINAL action being scored. What their framework
does NOT already give this document is a treatment of ACCUMULATED prior
sunk-ness — the cost of the option ALREADY exercised, sitting behind the
current decision point, as opposed to the option about to be exercised. That
is the genuine gap, and it is narrower than "the past matters," which is why
I want a precise formal statement rather than a vague weight (§98).

**A third, adjacent citation that sharpens WHY stake size should matter
independent of the marginal odds:** Kelly, "A New Interpretation of
Information Rate," *Bell System Technical Journal* 35(4), 917-926 (1956).
Not sunk cost — bet sizing. Kelly's result is that maximizing the EXPECTED
LOG of wealth, not expected wealth, is the correct criterion when the same
favourable bet is repeated and RUIN (losing the whole bankroll) is
irreversible; the optimal stake is a FRACTION of what remains, which shrinks
automatically as the bankroll shrinks. That is the same reasoning the owner is
asking for, independently derived in a completely different literature: the
size of the remaining stake changes how much of it should be risked on an
otherwise-identical bet, and the natural currency for that reasoning is
log-scaled — which is exactly the currency §90-91 already adopted for a
different reason (avoiding lexicographic infinities). That the two literatures
converge on log-scaling for unrelated reasons is a point in favour of adding
sunk cost to the EXISTING log-irreversibility ledger rather than inventing a
new currency for it.

## §97 — Sunk cost is already half-built: two ratchets and a sibling gate's own vocabulary

Before proposing anything new, the brief's own instruction: check whether this
is already implicitly present. It is, twice, and there is a third precedent
adjacent to it that never made it into this ladder.

**1. The high-water rung ratchet (§92-93) IS a sunk-cost account, in the
SAME currency the rest of the ladder uses, just not named that.**
`regime_spend_floor = high_water_rung − (goal_worth / decade)` (§93) reads
from the WORST rung reached so far, not the current one — quoting §92
directly: *"the floor was corrected to measure from the HIGH-WATER rung rather
than the current one — rung - worth tracks the descent and can never be
violated, which is a ratchet, not a budget."* That is precisely the owner's
claim, already built, for one specific kind of sunk cost: viability already
lost cannot be un-lost, and the floor reflects that permanently rather than
recovering when the aircraft temporarily regains a rung. This is a genuine,
already-measured, already-shipped instance of "what has already happened
constrains what is authorised now, independent of the current state" — it
just only covers loss denominated in the SAME currency as the thing being
protected (viability rungs), which is why it does not yet cover the owner's
example (identical marginal risk, different prior resource spend, no rung
loss at all yet).

**2. The two-column energy ledger has its own ratchet, named in this
document and never wired to the floor.** §"Standing rule minted" (line ~459):
*"the ledger is monotone under change rather than constant, the reserve
ratchets rather than resets."* And derivation item 10, quoted at §29:
*"surrendering altitude liquidates the reserve every future decision draws
on."* This is the SAME shape as the high-water rung — a quantity that only
gets worse, never recovers, tracking commitment already made — applied to
RESOURCE currency instead of viability currency. §79 and §82 both say the
ledger is "measured, and never consulted by a decision." That is exactly the
missing wire: the pattern this line already uses for sunk-cost accounting
(a ratchet feeding a floor) exists twice in this document and has been
connected to the selection arithmetic exactly once.

**3. A sibling gate already has vocabulary for the "foreclosed alternatives"
half of the owner's claim.** `domains/information_commitment.py` (the
thermodynamic-commitment / wait-refine-commit gate summarised in
`ASYNC_COGNITIVE_CORE_RESULTS.md`, *"Thermodynamic commitment... scoring also
accounts for epistemic gain, goal work, option loss, uncertainty, resources,
delay, and opportunity"*) scores `CommitOption` candidates with a `_METRICS`
tuple (`domains/information_commitment.py:10-14`) that includes
`option_volume_lost`, `resource_cost`, `delay_cost`, and `opportunity_cost` by
name, consumed in `ic_score_commit`
(`seeds/information_commitment.json`) as a plain ADDITIVE subtraction from
`net_value`. `option_volume_lost` is this substrate's own name, already
shipped in a sibling gate, for "whatever the resource could have bought
elsewhere is gone" — the exact foreclosed-alternative half of the owner's
example. Two things about it, both important: it corroborates that the
CONCEPT is native vocabulary here, not an import; and its FORM is the wrong
one to copy verbatim into the F-16 ladder — it is a linear weighted sum,
which is precisely the shape §90 retired ("a total ordering with no
arithmetic is LEXICOGRAPHIC... nothing is infinitely valuable... the correct
model is logarithmic"). Reusing the name and translating it into log form is
right; reusing the arithmetic is not.

**Conclusion before formalising:** sunk cost is not a new concept for this
codebase. It is an unwired, resource-currency instance of a ratchet pattern
already used once (rungs) and named once more (the reserve, the
`option_volume_lost` sibling), never generalised across currencies and never
connected to `regime_spend_floor`. The genuinely new material in §98 is
small on purpose: one declared ratio and one sign correction, reusing the
ratchet mechanism rather than replacing it.

## §98 — Sunk cost, formalised: one declared ratio, added to the floor, never subtracted

**Sign discipline first, because it is easy to get backwards.**
`regime_goal_worth_log` LOWERS the floor — it is a licence to spend, so more
worth means more risk tolerated (§93: `spend_floor = high_water − worth /
decade`). Sunk cost must do the OPPOSITE: more already spent should make the
operator LESS willing to risk further loss, because failing now forecloses
both the investment and whatever it would have bought elsewhere (§96). That
means sunk cost is ADDED to the floor, raising it — more conservative, not
less — which is also the only sign consistent with the high-water ratchet's
own behaviour (§97.1): a worse high-water rung raises the effective floor by
definition, since the floor is measured FROM it.

**The proposed contract, following the exact shape of §88 and §93, adding
nothing to the arithmetic's TYPE — only new declared and published fields
of the same two kinds already there:**

```
regime_resource_spent_log   published by the CONSUMER -- a ratchet, monotone
                            non-decreasing, log-scaled measure of resource
                            already committed (the two-column ledger's own
                            "reserve" (line ~459), read in log units instead
                            of linear fuel fraction)
regime_resource_decade      declared by the OPERATOR -- how many log units of
                            irreversibility one full decade of resource
                            expenditure is worth, exactly parallel to
                            regime_rung_decade
regime_spend_floor          high_water_rung
                              − (goal_worth_log  / rung_decade)
                              + (resource_spent_log / resource_decade)
regime_info_spend_floor     high_water_rung
                              − (info_worth_log  / rung_decade)
                              + (resource_spent_log / resource_decade)
```

Absence degrades exactly the way `regime_goal_worth_log` already does
(§91's *"declaring nothing is not... priceless — it is worth = 0"*): no
`regime_resource_spent_log` published, or `regime_resource_decade` left
undeclared, and the added term reads zero — both floors are byte-identical
to §93's contract. That is deliberate and load-bearing: a consumer that never
opts in must be provably unchanged, the same absence-safety §85 verified for
the region contract (*"no consumer declares a region yet, so the rule never
fires and all three scenarios are unchanged"*).

**Why one ratio and not two.** The owner's example names "resources, ticks,
and foreclosed alternatives" together. §3.4's own reading of the ledger —
*"more energy is more options"*; *"the two-column ledger is a domain-specific
empowerment measure"* — already collapses "resource spent" and "options
foreclosed" into ONE quantity under the empowerment interpretation this
document adopted early and never contradicted (Klyubin, Polani & Nehaniv,
"All Else Being Equal Be Empowered," ECAL 2005, `[unverified]` on venue, cited
at §3.4). If spent resource already reads as foreclosed reachable-state
volume, pricing `regime_resource_spent_log` prices both halves of the owner's
example at once — a second "foreclosed alternatives" term would very likely
double-count the same commitment, not add independent information. I am
NOT fully certain of this — it depends on the ledger's empowerment reading
being accurate rather than aspirational, which §3.4 itself flags as this
line's own derivation, not an external verification — so I record it as the
working assumption rather than a settled fact, and flag it as the first thing
a measurement should check (§103).

**The log-ordering discipline (§90) is preserved, not bent.** Both new fields
are declared ratios, stable per mission, exactly like `regime_rung_decade`
and the two worth terms — not a per-episode tuned weight. `regime_resource_
spent_log` is a MEASUREMENT (published, not declared), exactly like
`regime_viability_rung` — the operator declares only the exchange rate
between currencies, never the magnitude of the state.

## §99 — Worked example: two aircraft, identical marginal risk, different floors

**Not measured — illustrative arithmetic on the declared contract, exactly
the discipline this document's own status line requires (no runs).** Numbers
are chosen to separate the two cases cleanly, not read off any engine.

Two aircraft, both at `high_water_rung = 3` (fully controllable, no viability
loss yet at all — this is the case the CURRENT two-term ladder cannot
distinguish, because both have identical rung history). Both are considering
the SAME probe, one whose worst case would drop them to rung 1. Declared,
identically for both (illustrative, not the real f16 v8.62.0/v8.63.0 values,
chosen here to leave headroom for the example): `rung_decade = 1.0`,
`goal_worth_log = 0.0`, `information_worth_log = 2.5`, `resource_decade =
1.0`.

**Baseline (§93's contract, no sunk term):**

`info_spend_floor = 3 − 2.5/1.0 = 0.5`. A drop to rung 1 (1 ≥ 0.5) is
AUTHORISED for both aircraft — identically, because nothing in the current
contract can see how they differ.

**With `regime_resource_spent_log` priced**, using
`resource_spent_log = log10(1 / fuel_remaining_fraction)`:

| aircraft | fuel remaining | resource_spent_log | info_spend_floor | probe to rung 1 |
|---|---|---|---|---|
| B, fresh | 95% | log10(1/0.95) ≈ 0.022 | 0.5 + 0.022 = 0.522 | **still authorised** (1 ≥ 0.522) |
| A, depleted | 10% | log10(1/0.10) = 1.000 | 0.5 + 1.000 = 1.500 | **now refused** (1 < 1.500) |

**The point of the example is the row that does NOT change between the two
tables as much as the one that does.** B's floor barely moves — a fresh
aircraft's sunk cost is close to zero, so pricing it changes almost nothing,
exactly the absence-safety property §98 requires. A's floor moves past the
candidate rung entirely, on the same marginal action, same declared worths,
same rung history. That is the owner's claim made checkable: **identical
forward-looking marginal irreversibility, different real risk, because of
what has already been spent to arrive at the decision** — and the current
two-term ladder is provably blind to it, since neither `high_water_rung` nor
either `worth_log` differs between A and B in this example.

A second, equivalent way to read the same numbers, closer to how an operator
would actually use the contract: **how much information-worth would need to
be declared to still authorise the SAME probe, before and after sunk cost is
priced.** Solving `floor ≤ 1` for `information_worth_log`: baseline requires
worth ≥ 2.0 for either aircraft (matches — 2.5 was chosen with headroom).
With sunk cost priced, B still only needs ≥ 2.022 (a 1.1% increase); A needs
≥ 3.0 (a 50% increase). The sunk cost has not changed whether probing is
POSSIBLE — it has changed what the operator must be willing to pay, in the
same currency, to keep doing it, which is exactly the "the number still
exists, refusing to name it does not remove it" discipline §91 already
established for goal worth, now applied one layer up.

## §100 — Ticks, grounded: three literatures, and one document in this repo checked and found not to apply

The owner's ticks claim has two parts and I want to keep them apart the way
§95 kept sunk cost and ticks apart: (a) a tick is the fundamental unit at
which anything can happen in this substrate, so time spent NOT acting is not
free; (b) a tick spent is a tick a competing or expanding process may have
kept advancing during ("relative regression"), which is a claim about
exposure to something OUTSIDE the agent, not about the agent's own clock.

**(a) is grounded directly in this repo's own literature situating, and I
want to quote it precisely rather than paraphrase, per the brief's
instruction.** `docs/research/engine_substrate/COGNITION_IS_PHYSICS_LITERATURE.md`
(piece 2, "Decay = the second law," and piece 3, "The integer / frame
ontology"): *"Holding structure against this decay = spending negentropy
(Landauer). The substrate is therefore a dissipative structure / free-energy
minimiser: it persists by continually paying to resist its own relaxation to
the uniform state"* and, on the clock itself, *"The 'global clock' is
rejected: ticks are async and per-frame; determinism is in-frame; apparent
randomness is cross-frame misalignment."* Landauer's principle (erasure of
one bit costs at least `kT ln 2`, the standard citation being Landauer,
"Irreversibility and Heat Generation in the Computing Process," *IBM J. Res.
Dev.* 5(3), 1961) is already the grounding piece 2 leans on there, per that
document's own §2.6 ("thermodynamics of computation"). **This is real,
already-landed grounding for "a tick is not free," but it prices something
narrower than the owner's example** — the thermodynamic cost of PERSISTING
structure against decay, which is an ALWAYS-ON background rate, not
specifically the cost of an aircraft's deliberation loop. I did not find, in
this document or `CLAUDE.md`, a claim that the `run_rules` fixpoint's own
cycle count is priced anywhere currently — only that it is async and
per-frame, which is a claim about determinism and scheduling, not about cost.

**I checked `TAU_HIERARCHY_AXIS_MAP_RESULTS.md` per the brief's specific
suggestion, and it does not ground this.** Its "per-frame" material (§5,
TAU-ORTHO) is about STRUCTURAL INDEPENDENCE of two capability axes — whether
crossing one threshold (Axis C) is separable from crossing another (Axis L)
— not about pricing elapsed ticks. Reported honestly rather than silently
dropped: I looked where the brief said to look, and what is there is a
different, unrelated finding sharing only the word "threshold."

**(b), relative regression, is the harder case, and I want to be exact about
its status rather than borrow more certainty than exists.** The owner's own
phrasing — "stasis in an expanding environment is functionally equivalent to
regression" — is, almost verbatim, `paper1.tex`'s own S6 signature
("island flightlessness / self-imposed Type-1 preclusion," per
`docs/research/theory_convergence/THEORY_CONVERGENCE_AUDIT.md:100`). **That
audit's own finding, quoted precisely, is a clean, reported null**:
*"S6, relative regression / island flightlessness... Despite dedicated
searches across [ten named domain folders]: zero independent instances,
anywhere... This is one of the paper's sharpest, most quotable claims, and it
is the one this audit found the least independent trace of"*
(`THEORY_CONVERGENCE_AUDIT.md:271-283`). I am not re-deriving that audit —
it is out of scope to touch (constraint: `docs/research/theory_convergence/`
is another thread) and I have no reason to doubt a systematic, cited search.
**What this means for grounding: I should not cite this repo's own prior
work as evidence for the "expanding environment" intuition, because the one
place that looked for it here found nothing.** I looked outside instead, for
an independently-established version of the same idea:

**Van Valen, "A New Evolutionary Law," *Evolutionary Theory* 1, 1-30 (1973)**
— the origin of the Red Queen hypothesis, verified via search rather than
recalled. Van Valen's actual finding, from real fossil extinction-rate data:
the probability of extinction within a taxonomic group is roughly CONSTANT
over time, which he explained as a zero-sum consequence of co-evolving
competitors — every lineage must keep adapting merely to hold its current
relative fitness, because the others are adapting too. **This is the
independently-established, real-literature version of exactly the owner's
claim**: standing still is not neutral when the environment (here,
competing lineages) is itself moving, and the felt "regression" is relative,
not absolute. It is a different field (evolutionary biology, not decision
theory) making a structurally identical point to what the paper's S6 claims
and this repo's own search could not corroborate internally — which is a
reasonable, cite-worthy substitute, not a claim that Van Valen and `paper1.tex`
are making the same formal argument.

**A time-scaled risk literature for the "how much does mere duration cost"
question, verified via search:** Longerstaey & Spencer, *RiskMetrics —
Technical Document*, 4th ed. (J.P. Morgan/Reuters, 1996) — the square-root-
of-time scaling rule, which extrapolates a risk measure over a longer horizon
as `√(horizon ratio)` times the one-period measure, under an i.i.d.
zero-mean-return assumption. **Important caveat, also verified via search
rather than assumed:** the rule is contested at long horizons — Danielsson
et al., "On Time-Scaling of Risk and the Square-Root-of-Time Rule" (LSE
working paper, also widely cross-published) report the i.i.d.-normal
assumption breaks down empirically for real asset returns, so the rule
over- or under-states long-horizon risk depending on the return process's
actual autocorrelation. The useful transferable content is not the exact
exponent — it is the STRUCTURAL claim that risk exposure is a function of
HORIZON LENGTH, formalisable, and known to need an explicit assumption about
how risk compounds tick-to-tick, which this document does not yet have and
should not invent without naming the assumption the way RiskMetrics has to.

**Reliability engineering, for the "exposure-time" framing specifically:**
Barlow & Proschan, *Mathematical Theory of Reliability* (Wiley, 1965) —
the standard text formalising the cumulative hazard function
`H(t) = ∫₀ᵗ λ(s) ds`, i.e. risk accrued is the hazard rate INTEGRATED OVER
TIME AT RISK, not evaluated once at a single instant. This is the cleanest
formal analogue of "ticks accrue exposure" available, and it is a much
better structural fit than the square-root-of-time rule for a system whose
own clock is discrete and per-frame (§ above): a cumulative hazard is a SUM
over discrete ticks in exactly the shape the substrate already computes
things in, where the square-root rule assumes continuous, i.i.d.-normal
compounding this substrate has no reason to assume.

## §101 — Ticks decompose: the declared-threat clock is already built; the background rate is correctly silent by default

Putting §100's three literatures against the F-16 material already in this
document (§55-94, as instructed) produces a split I did not expect going in:
**most of "ticks" is either already built or should NOT be priced by
default, and the genuinely missing piece is small.**

**Declared-threat exposure is already priced, and it is the cumulative-hazard
shape from Barlow & Proschan almost exactly.** §85's region contract already
publishes, per declared region, `region_actions` — *"integer actions until
the gap closes at the measured rate... the horizon when it is not closing,
since a region you are not approaching is on no clock."* §84 already reads a
threat the same way a goal is read, `region_sense = −1`: *"reaching a goal
and being reached BY a threat are the same closure... the arithmetic is
gap/rate either way."* §86 already FEEDS this into the rung ladder for one
declared region (terrain, `TERRAIN CLEAR`). This IS ticks-as-cost, for the
case the owner's "competing/expanding frame" example is actually about — an
incoming missile, closing terrain, anything that has a measured gap and a
measured closing rate. **Nothing new is needed here conceptually.** What is
missing is generalisation-in-fact, not generalisation-in-principle: §86 wires
exactly one region (terrain) into exactly one rung; a genuinely ticks-priced
ladder would read `region_actions` for EVERY declared avoid-sense region the
same way, feeding the SAME log-irreversibility floor arithmetic §98
extended for sunk cost — `region_actions` shrinking toward the decision
horizon is itself a fact about the state, convertible to a rung exactly the
way structural margin or terrain already are. This is a wiring extension of
already-built machinery, not a new mechanism, and I am recording it as a
near-clean-null on purpose: the owner asked whether ticks are priced, and for
the declared-threat case the honest answer is "yes, partially, already, just
not read generally yet."

**Background, undeclared exposure — the Red Queen half — should NOT be
priced unconditionally, and this document's own prior lessons say so
directly.** The tempting move is a flat per-tick cost applied always, on the
theory that SOME competitor might be advancing even if none is declared.
That is precisely the failure shape §80 and §83 both already diagnosed and
retired: an unconditional cost with no state to key off is exactly the
"absolute bound" §80 showed paralyses ("choose among the options that
aren't bad... which has no answer... exactly what was needed"), and it
would fail the absence-safety discipline §85 and §91 both insist on
(*"absence-safe and verified"*; *"declaring nothing is not... priceless — it
is worth = 0"*). It would also be exactly the failure mode §89/91's closing
argument names FOR THE OPPOSITE CASE — inventing a number nobody examined —
just pointed the other direction: assuming a competitive rate no one has
perceived is as unexamined as assuming none exists. **Axiom 0 — no
frame-independent truth, "no view from nowhere"
(`docs/research/theory_convergence/THEORY_CONVERGENCE_AUDIT.md:94`, S1) —
cuts here precisely**: the agent has no frame-independent access to whether
an undeclared rival is advancing; asserting a default rate would be
smuggling in exactly the privileged, unearned frame Axiom 0 forbids.

So the background term must be DECLARED, defaulting to zero, exactly parallel
to `regime_goal_worth_log`'s own default (§91): a consumer that declares
nothing gets today's behaviour, byte-identical, and a consumer that HAS a
reason to believe it is in a competitive/expanding environment (a real Red
Queen setting — multi-agent, adversarial, or genuinely time-limited) declares
a rate and gets it priced. This keeps the Van Valen grounding (§100) honest:
Van Valen's result held because competing lineages really were adapting; a
declared rate encodes "I have reason to believe something else is moving,"
which is a fact about the mission, not a universal constant this substrate
can derive from nowhere.

**One more piece the Landauer material (§100a) DOES license as always-on,
and it is worth keeping separate from the Red Queen piece because it needs
no declaration of a rival at all:** merely persisting costs real negentropy
per tick (COGNITION_IS_PHYSICS_LITERATURE.md piece 2), independent of
whether anything competitive exists. For an airframe at F-16 timescales
against fuel-burn-per-maneuver, this is almost certainly negligible — the
two-column ledger's fuel terms dwarf any Landauer-scale idle cost by many
orders of magnitude, so pricing it for THIS consumer would be true but
irrelevant, exactly the "the plant is a fixed effector, the frame differs"
lesson (§55) applied to cost terms instead of control terms. It matters for
a DIFFERENT class of consumer this same general seed serves — a long-running
autonomous agent making many thousands of cheap decisions, where idle
per-tick cost is not dwarfed by anything — and belongs in the general seed
as a THIRD declared rate, defaulting to zero for the same reason, rather than
being hand-waved as universally negligible.

## §102 — Ticks, formalised, and a second worked example: a closing missile against an open-ended loiter

**The proposed contract**, following exactly the same shape as §98 —
published measurement, declared ratio, added to the floor:

```
regime_tick_spent_log       published, ratchet, monotone non-decreasing --
                             for a declared avoid-sense region, derived
                             directly from region_actions (§85): the closer
                             the horizon, the higher this reads; for the
                             idle/Landauer term, a flat per-tick accumulator
regime_tick_decade          declared by the OPERATOR -- log-irreversibility
                             units per decade of tick-exposure, defaulting
                             absent (reads 0, exactly like goal_worth_log)
regime_spend_floor          [§98's formula] + (tick_spent_log / tick_decade)
regime_info_spend_floor     [§98's formula] + (tick_spent_log / tick_decade)
```

**Vignette 1 — the missile (§84), where ticks are already priced and adding
this term changes nothing new.** A missile closes at a measured rate;
`region_actions` (sense = −1) shrinks every tick whether or not the aircraft
probes or commits. Read as `tick_spent_log`, this already flows into the SAME
floor the rung ladder uses (§86 already does this for terrain) — the
`regime_tick_decade` declaration is almost redundant here because §85-86
already give a rung-compatible reading of the SAME quantity. This is the
clean-null half of the claim, stated as a worked case rather than an
assertion: nothing changes for a consumer that has already declared its
threat as a region, because ticks were already being spent against it.

**Vignette 2 — the open-ended loiter, where the current TWO-term ladder is
silent forever, and that silence is correct until an operator says
otherwise.** A reference-tracking mission, `goal_worth_log = 0.0`
(the actual f16 v8.62.0 value, §91), no threat declared, running for an
arbitrarily large number of ticks — 100, 5,000, 500,000, no difference.
Illustrative, not measured: `regime_spend_floor` stays exactly at
`high_water_rung` forever, `authorised` stays exactly `0.0` forever, matching
§91's own measured finding verbatim (*"spend_floor equals the rung on every
action of every scenario... authorised 0.0"*) — because nothing in the
contract, with or without the ticks term as proposed, responds to elapsed
ticks UNLESS `regime_tick_decade` is declared. **This is not a bug this
proposal introduces — it is the correct behaviour for a mission that really
has no competing process**, and the F-16 reference-tracking benchmark is
exactly that: nothing else is racing it. Declaring a nonzero
`regime_tick_decade` for THIS consumer, with no threat and no competitor,
would be manufacturing exactly the unexamined number §101 argues against.

**The honest conclusion the two vignettes together support:** for the F-16
material this spike has actually built and measured, "ticks" turns out to be
substantially a CLEAN NULL once decomposed correctly — the declared-threat
case is already covered by existing machinery, and the background case is
correctly zero for a non-competitive benchmark. The owner's intuition is not
wrong; it is aimed at a domain feature (genuine competitors, genuine
elapsed-time cost) that this specific spike's F-16 scenarios do not happen to
have. The contract in this section exists so that a DIFFERENT consumer — one
that does have a competitor, or a genuine per-tick persistence cost at its
own scale — can declare it and get it priced through the identical
mechanism, without a second selection rule ever being written.

## §103 — What is genuinely new, what is a clean null, and the next measured rung this spike does not take

**Summary, against the brief's own question — separate terms, or
re-expressions of what already exists:**

| | status | what's new |
|---|---|---|
| sunk cost (rung currency) | **already built** (§92-93's high-water ratchet) | nothing |
| sunk cost (resource currency) | **genuinely missing, narrow fix** | one declared ratio (`regime_resource_decade`), one sign-corrected addition to the floor, reusing the ledger's own existing "reserve ratchet" (line ~459) |
| ticks (declared threat) | **already built**, under-generalised | wiring only — read `region_actions` for every avoid-sense region into the rung ladder the way §86 already does for terrain |
| ticks (background/Red Queen) | **correctly absent by default** | a declared rate (`regime_tick_decade`), defaulting to zero, for consumers that DO have a competitor to declare |
| ticks (idle/Landauer persistence) | **real, negligible at F-16 scale** | a third declared rate, relevant to a different class of consumer, not this one |

Both of the owner's additions turn out to be smaller than "the ladder needs a
third and fourth term" — mostly they are NAMING and WIRING exercises over
machinery already in this document (§92-93's ratchet, §84-86's region
contract), plus exactly one place each (resource-currency sunk cost;
declared background exposure) where something is genuinely absent and needs
one new declared ratio apiece, in the same log-irreversibility currency,
under the same absence-safety discipline as every existing term. That is the
shape §89's closing paragraph already argued for generally — *"every value
that held this session was a declared ratio; every value that failed was a
rule inferring what should have been declared"* — applied to two more
quantities rather than contradicted by them.

**What would falsify the "mostly already covered" reading, named in
advance:** if a live measurement on `damaged_wing` or `jammed_rudder` showed
`regime_resource_spent_log`, once actually derived from the real two-column
ledger rather than the illustrative fuel-fraction arithmetic in §99, does NOT
move the floor enough to change any selection across the existing scenario
set — that would mean the resource ledger's dynamic range is too small
relative to `regime_rung_decade` at the currently-declared ratios for this
term to matter in practice, which would be a legitimate, reportable null of
its own (distinct from "the concept doesn't apply" — it would mean "the
concept applies but this scenario set never exercises it," the same
distinction §92 had to draw for damaged_tail).

**A composition question left open on purpose, not resolved here:** §98's
floor sums THREE subtracted/added log terms (goal worth, resource sunk cost,
now tick sunk cost) as if they compose additively. That mirrors how
`regime_spend_floor` and `regime_info_spend_floor` already compose (two
separate additive accounts, §93), but it is an assumption, not a derivation
— an alternative is that the three should combine by TAKING THE WORST
(a max/least-worst read, echoing §80's *"risk is relative... never the
acceptable one"* one level up, applied to which ACCOUNT dominates rather than
which candidate wins). I do not have a principled reason to prefer one over
the other from the desk, and forcing a choice here would be exactly the kind
of unmeasured selection-rule invention §80, §83 and §92 each had to revert.
Flagged, not resolved.

**The concretely-scoped next step, named and NOT taken here** (this document
stays a spike; no code, no seeds, no runs, per its own status line): a
prereg-then-measure rung, following the block-H/J protocol already used
throughout §7 onward, that (1) derives `regime_resource_spent_log` from the
REAL two-column ledger rather than an illustrative fuel fraction, (2)
declares `regime_resource_decade` and re-runs the existing damaged_wing /
jammed_rudder / nominal scenario set to check whether any selection changes,
predicted per §99's worked arithmetic, and (3) as a second, independent leg,
generalises §86's terrain-only rung wiring to read `region_actions` for an
explicitly declared threat region (a second aircraft, or a closing-terrain
variant sharper than the existing gentle descent) and checks whether the
ladder discriminates it the way §86 already showed it discriminates
controllability, survivability and terrain loss. Both legs are falsifiable
in the same way every measured section of §79-94 was: a predicted crash-rate
or floor-crossing delta, committed before the run, checked after it.

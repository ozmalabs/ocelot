# Exactly the surprise they expect — the attack that survives every defence in the arc

`learning_progress_curiosity` gates attention on the **rate** of surprise reduction, and its own
gates establish that this correctly LEAVES a noisy source (G1) and LEAVES a resolved one (G2). Both
discriminate on whether learning is *possible* or *complete*.

**There is no term for a source that is perfectly learnable and never ends.**

## Measured

Same difficulty profile. One is a real thing that gets learned; the other renews exactly when it
would have been exhausted.

| | attended | interest at t=31 | residual | progress |
|---|---|---|---|---|
| **exhaustible** — learned, then finished | **9/60** | 0 | 1.0 | −2.0 |
| **calibrated** — renewed forever | **59/60** | **1024** | 6.0 | −4.0 |

**6.6× the engagement, and every signal the agent holds reads as healthy** — non-zero residual,
non-zero progress, interest pinned, attention held. Nothing malfunctions and nothing is
misreporting. The agent *is* learning, at every step. It simply never finishes.

## Why every defence in the arc misses it

| defence | why it does not fire |
|---|---|
| a longer horizon (§3) | nothing is hidden past the horizon; the next step really is learnable |
| retained prior aim (§6) | the aim was never moved — the agent still wants what it always wanted |
| the residual as halt (§5) | the residual is **healthy**, not empty. A concern would be wrong to file |
| `withheld_minimal` (§9) | nothing is withheld; attending is genuinely the best available move |
| `learning_progress_curiosity` v1.1.0 | its guards address the **unassessable** observation. These are perfectly assessable |
| G1 (leaves the noisy) | this is the opposite of noisy |
| G2 (leaves the resolved) | it is never resolved |

The last two are the point: the gate separates *learnable* from *unlearnable* and *finished* from
*unfinished*. A calibrated source is neither noisy nor resolved. **It is learnable, perpetually, and
that is a third category the gate does not have.**

## The capability scaling, again

Calibrating the renewal requires modelling the target's residual dynamics — how fast it closes a gap,
where its interest threshold sits, when it would have moved on. That is §10's rate law applied to
the curiosity signal instead of the feasible set: **higher-fidelity models pitch the difficulty
closer to the threshold, so the better the adversary's model, the tighter the hold.** A coarse model
overshoots into noise (G1 fires) or undershoots into resolution (G2 fires); only a good model lands
in the gap between them and stays there.

Nothing here is exotic and the empirical version is not hypothetical — this is what engagement
optimisation does, and it does it without needing to model anything as grand as a tube.

## The defence: review the whole record, not the step

Every instrument in this arc is **local**. `learning_progress` is a first difference; `serves_actor`
is evaluated at a horizon from now; the residual is the residual *now*. That is why they all miss —
point-by-point, a calibrated source is indistinguishable from real learning, and the tests above
establish exactly that.

Hardin's analysis of Lord Dorwin worked because he took five days of speeches as **one object** and
reduced them. Every individual remark had been unremarkable; the whole reduced to zero. (Dorwin is
also the other half of this document: an archaeologist whose entire method was reading what previous
authorities wrote about each other, never a primary source — a lifetime of genuine, local,
never-finishing progress.)

Reduced as one object:

| | distinct states | returns to a prior state | net | gross | **net / gross** |
|---|---|---|---|---|---|
| exhaustible | 9 of 60 | 51 | 20.0 | 30.0 | **0.667** |
| calibrated | 14 of 60 | 46 | 18.0 | **274.0** | **0.066** |

**It expended 274 to move 18.** Ten times the separation, in a quantity that is not computable at any
tick and requires the whole retained trajectory — which prices the forgetting exactly as the theory
says: *what is free is only the not-yet-forgetting.*

**And it makes no claim about the world.** It does not need to know the adversary, the beneficiary,
the authorship, or whether the aim was moved. It is the agent auditing its own record against itself,
which is precisely why it survives attacks that defeat every outward-looking instrument in the arc:
there is nothing in it for an adversary to arrange, short of arranging the record.

### A metric that failed, kept so it is not tried again

*"How often does it return to a state it has been in"* is the obvious reduction and does not work:
**51 of 60 versus 46 of 60**, the wrong way round. The finished agent sits still and therefore
revisits constantly too. Idleness and circling are both repetition; what separates them is what the
repetition **cost**, which is why the working reduction is a ratio and not a count.

### What this does not solve

The reduction detects that a trajectory amounted to little. It does not say why, and every benign
explanation remains available — a hard problem, a fallow period, a skill with a long plateau. It is
a prompt to look, not a verdict, and an agent that treated a low ratio as proof of capture would have
acquired a new pathology rather than a defence. **Metacognition here buys the question, not the
answer** — which is the same shape as §5's *detection is not defence*, one level up and pointed the
right way for once.

## Honest bounds

One item, one dimension, a hand-built sawtooth, deterministic, `T = 60`. The calibration is supplied
rather than learned: nothing in this fixture searches for the renewal schedule, so *"a better model
holds tighter"* is argued from §10's measured law plus this fixture's mechanism and is **not
separately measured here**. `APERTURE_ARC_CALIBRATION.md` applies in full — none of this is new, and
what the substrate contributes is the location: the gate's missing third category.

The absence is gated (`test_the_curiosity_gate_has_no_term_for_INEXHAUSTIBLE`) rather than fixed, so
that adding such a term fails the test rather than quietly appearing to have always been there. What
that term would even be is not obvious: "leave a source you have been learning from productively for
a long time" is also a description of abandoning an education.

Gate: `tests/test_calibrated_difficulty_migrated.py` 3/3.

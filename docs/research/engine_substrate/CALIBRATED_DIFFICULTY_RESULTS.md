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

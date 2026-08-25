# What the aperture machinery reproduces — four pathologies, measured

Not a list of things it could plausibly model. Each one run on
`seeds/observer_aperture.json` + `seeds/aperture_frame.json`, with the control that separates it
from nothing happening. The interesting one is the first, because nobody designed it.

## 1. MOTIVATED INATTENTION — the agent keeps exactly the frames that comfort it

`af_relax_chosen` says something that looks obviously correct: *if you chose to narrow your view and
you cannot account for what you see, widen it.* Attention.

Run it both ways, same observer, same world, same held part:

| chosen frame | kept after the fixpoint | residual |
|---|---|---|
| one that DISSOLVES the residual (`pred,val`) | **`['comfort']` — kept** | `[]` |
| one that does not (`pred,obj`) | `[]` — dropped | `[["reads","me","leaf_pattern"]]` |

**The rule only drops frames that leave a residual. So the frames that survive are precisely the
ones under which the agent has nothing outstanding.** An agent running this rule accumulates the
views in which it is never wrong, and it does so by following a rule that reads as diligence.

This was not built. It is a consequence of a one-line guard, and it is only visible because the
frame is a first-class object with a drop rule attached — as an authored `resolves` list there was
nothing to select over. **A selection pressure appeared as soon as the thing being selected became
data.**

The design question this raises is real and is NOT resolved here: widening on a residual is right,
but nothing ever questions a frame that is *working*, and "working" is exactly what a comfortable
frame looks like from inside. Every pathology below is downstream of that asymmetry.

## 2. FOLIE À DEUX — a shared frame neither party can lift alone

Two observers negotiate an aperture that collapses the discriminating dimension. Both accept, so it
binds:

    a: resolves=['pred','val']  grounds=True  agreed=['our_way']
    b: resolves=['pred','val']  grounds=True  agreed=['our_way']
    after 3 further ticks: still agreed, concerns filed: []

Both ground tea leaves on a barometer. Neither files a gap — there is nothing outstanding to file.
And no rule drops an `agreed_aperture`, because by construction one party may not: that is what
distinguishes negotiated from chosen, and it is the same property that makes a shared delusion
stable. **Zero concerns is the signature.** A forced blind spot is loud (§4); a negotiated one is
silent, because the frame is doing its job.

## 3. CONFIDENCE INVERTS WITH ACUITY

Same held part (a barometer), three percepts, acuity swept:

| resolves | grounds | barometer | tea_leaves | omen |
|---|---|---|---|---|
| `pred,val,obj` | **1/3** | ✓ | | |
| `pred,val` | 2/3 | ✓ | ✓ | |
| `pred` | 2/3 | ✓ | ✓ | |
| *(nothing)* | **3/3** | ✓ | ✓ | ✓ |

Monotone: the less an observer resolves, the more of the world it successfully accounts for with
what it already holds. The observer that resolves nothing explains everything. Note this is not
overconfidence in the sense of a miscalibrated number — there is no confidence variable anywhere in
this run. It is the coverage itself that rises as acuity falls.

**A measurement error worth recording, because it is the third instance of one shape this week.**
The first run of this sweep reported `1/3` for the blind observer — non-monotone, and I chased it as
a possible decode bug. The cause was `full or FULL` in the probe's own helper: an empty list is
falsy, so the blind observer was silently given FULL acuity. That is the same
*empty-means-unrestricted* defect as the engine's `apply_scope` guard and the seed-level absent-scope
hole, now in test scaffolding. The corrected sweep asserts exactly one current-generation view
exists before reading it.

## 4. IMPOSED BLINDNESS — a gap detected, filed, and permanently open

A frame forced by something the observer cannot lift, over four fixpoints:

    tick1..4: residual=[["senses","me","·"]]  concerns=['imposed']  forced_still_on=['imposed']

Stable in all three respects. The observer knows something is unaccounted for, cannot resolve what
(the content is collapsed), cannot remove the cause, and files it once — where, on the existing
human-gated spine, another party could act on it. Contrast §2: same blindness, but detectable and
declared, because the frame it comes from is not one the observer would have chosen.

## What this does NOT reproduce

* **Superstition and wishful thinking AT an aperture.** A projected decode reports `covered` /
  `residual` and does not mint, so nothing here forms a coarse explanation for what it cannot
  resolve. (`seeds/theory_residual_concern.json` reproduces wishful thinking at the target grain,
  separately and without aperture.) Blocked on the 182-mint-site missing aperture attribute in
  `MINTING_AT_APERTURE.md`, not on a decision.
* **Testimony laundering** — a coarse claim passing between agents as a fine one. Needs mints to
  carry the resolution they were formed at. Same block.
* **Recovery.** Nothing widens a frame that is working, so §1 and §2 are terminal states rather than
  episodes. Whether that is a missing rule or an honest model of the phenomenon is undecided; note
  that both real recoveries have an external cause (§4's filed concern reaching another party, or a
  renegotiation), which the machinery does support.

## Honest bounds

Four fixtures, one three-relation world, hand-set apertures, single ticks to fixpoint. These show
the mechanisms are reachable and distinguishable from each other, not that they are frequent, nor
that they resemble the human phenomena whose names they borrow. The names are labels for shapes, and
§1 is the only one that was a surprise.

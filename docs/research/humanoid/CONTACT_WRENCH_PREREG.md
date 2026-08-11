# A CONTACT IS A DIRECTION, A MAGNITUDE, AND AN ADMISSIBLE WRENCH SET — prereg

**Status:** design recorded, nothing built. Registered 2026-08-09 before
implementation so the gates below cannot be chosen after seeing results.

**Supersedes `CONTACT_CONTINUUM_PREREG.md`**, which was superseded before any of
it ran. That document replaced the support CATEGORY with a support LOAD — right,
and one scalar projection of the object. This one states the object.

## The claim

**Support is not "up", not a count, not a category, and not necessarily
compression.**

Gravity picks out a direction in *this world*; it does not privilege one in the
body's own account of what is holding it. A surface can be a floor, a wall, a
ramp, an overhang or a ceiling. A hold can push (contact), pull (a sucker pad),
or constrain (a hook). What every one of them has in common is that it can
transmit some set of forces and torques and not others.

So a contact is a **direction**, a **magnitude**, and an **admissible wrench
set** — a friction cone about a normal for pure contact, a cone plus tension for
adhesion, a constraint manifold for a hook. Stability is whether the wrench
required to keep the body's trajectory viable lies inside the sum of what the
current contacts can supply. No gravity direction, no nominated links, no
horizontal plane, no thresholds, and no counting.

Support polygons, capture points and "how many feet are down" are the degenerate
case of that when every contact is a point, compression-only, and gravity is
uniform and normal to a flat floor.

## What is measured, before any of this is built

### The boundary already publishes the whole object

Per contact, `PyBulletHumanoidWorld.observe()` computes and publishes:

```
normal_on_b            the contact NORMAL DIRECTION (3-vector)
normal_force           its magnitude
lateral_friction_1/2   two friction magnitudes
lateral_direction_1/2  their DIRECTIONS (two 3-vectors)
position_on_a / _b     where the contact is
link_a / link_b        what is touching what
```

That is a contact wrench basis. **Nothing in the tree consumes any of the
directions.** The only other occurrence of `normal_on_b` anywhere is a second
boundary re-publishing it (`pybullet_robot_world.py`).

`whole_body_support_contacts` — every contacting link with its force-weighted
world position — is consumed **exactly once**, to take `len()` of it:

```python
"active_support_count": float(sum(1 for _row in observation.get("whole_body_support_contacts", ())))
```

Force and position discarded; a count survives.

### Direction is not merely unexercised

```
flat ground plane   228 contacts sampled, ALL within 0-5 deg of vertical, links {13, 22}
the desk box          2 contacts sampled, BOTH non-vertical (30-60 deg, 60-120 deg), links {25, 27}
```

On a flat floor with only feet touching, vertical normals are a TAUTOLOGY, not
evidence — the first probe measured the world, not the body. Add one box and
**100% of contacts are non-vertical, on arm links the support path does not
look at**.

### Support in tension is unrepresentable, not merely discarded

```
body hung from a fixed constraint, fully held:  reaction 400.68 N ~ body weight
getContactPoints:                               0 contacts
minimum normal_force ever observed:             0.000000   (never negative)
```

Contacts are unilateral by construction. A fully supported body reports **zero
support** by every measure in the stability path. A sucker pad has no expressible
form as a contact; a hook must be a `constraint`, reported through
`getConstraintState`, a channel nothing in this tree reads. **This differs in
kind from every other gap found in this arc: the others were measured and thrown
away, this one is never measured.**

### The supported set is an arbitrary pair

```python
self._support_link_indices = tuple(sorted(distal_links[:2]))     # line 289
def _support_code(observation):
    if len(support) != 2: raise RuntimeError("expected two support sensors")
```

The first two distal links are nominated as "the supports"; the encoder RAISES
on any body that is not bipedal.

### And the count says nothing about stability anyway

```
action   0   "double_support"   load split  76 N / 318 N   (already almost single)
action 275   "single_support"   total load  612 N          (MORE than the double case)
```

Carried forward from the superseded document, still valid: total load spans
**0 to 3.26 body weights with 15 of 20 histogram bins occupied**; `support_0`
alone spans 0.022 to 2.172 mg; `current_support_phase` tracks its code with
**zero error on 600/600 actions** while filing 24 flight actions alongside 468
double-support ones. The tracker is flawless and the category is the defect.

## The design

1. **Publish the wrench basis.** Each contact reaches the graph as its normal
   direction, normal magnitude, two friction directions and magnitudes, position
   and the pair of links involved — the quantities the boundary already computes.
2. **Publish constraint reactions as support.** `getConstraintState` is the only
   channel that can express tension. Without it, "held by a hook" and "in free
   fall" are the same reading.
3. **No nominated links.** Support is whatever is in contact, from the whole-body
   channel, with its forces and positions intact.
4. **The stability measure is a wrench margin**, not a distance to a polygon:
   how much of the required wrench the available set can supply. Defined in every
   phase, on every surface orientation, for push, pull and constraint alike.

### Site enumeration, carried forward and extended

The first attempt at the superseded design failed because it was partial; that
enumeration is still binding and is not repeated here — see
`CONTACT_CONTINUUM_PREREG.md`, eleven sites. This design adds:

| # | site | what |
|---|---|---|
| 12 | `pybullet_humanoid_world.observe()` | already publishes the basis — no change, but it must reach the graph |
| 13 | walk harness `whole_body_support_contacts` use | stop reducing to `len()` |
| 14 | `_support_link_indices` / `_support_code` | the nominated pair and the bipedal assertion |
| 15 | constraint channel | `getConstraintState` is currently unread anywhere |

## BLOCK 0 — the null distribution, FIRST, and now of the right quantities

Unchanged in necessity, changed in content. **No before/after comparison means
anything until the spread is known**, and the superseded document's motivating
figure for this was itself wrong (it compared a trace-derived count with an
episode-derived one; corrected in place there).

Run the unmodified experiment **N >= 8 times**, changing nothing, recording per
run the distribution of: contact normal directions, per-contact magnitudes,
number of distinct links in contact, and the existing summary metrics. This also
answers a question the earlier Block 0 could not have asked — **how often does
this body contact anything other than its two nominated links, and at what
angles.**

If the answer is "never, and always vertical", then on THIS protocol the wrench
representation is unexercised and the case for building it rests on the desk box
and on bodies with other morphologies — which is a finding, and must be reported
as one rather than worked around.

## Registered predictions

1. **On the flat-ground walking protocol, contact normals are all vertical and
   only the two nominated links touch.** Predicted from the probe above. If other
   links contact during falls, the current representation is losing information
   on the protocol as it stands, not only in principle.
2. **On any protocol containing an obstacle, non-vertical normals appear
   immediately** — measured 2/2 against the desk box. A representation carrying
   direction must distinguish those from floor contacts; the current one cannot.
3. **A hung body reads as fully unsupported** under every current measure, and
   as fully supported once the constraint channel is published. This is the
   cheapest possible test of the tension half and requires no locomotion at all.
4. **Direction is NOT predicted to improve walking.** The flat-ground protocol
   may exercise none of it. "The walk does not improve" does NOT falsify the
   representation claim.
5. **Cost.** The whole-body contact channel is O(contacts) per action rather than
   O(2). No estimate is registered because none has been measured; it must be
   measured before it is claimed to be cheap.

## What would falsify it

* **Prediction 3 fails** — if a constraint-held body somehow already registers
  support, the tension gap does not exist and the strongest claim here is wrong.
* **Direction turns out to be recoverable from magnitude alone** on the bodies
  actually studied. If every non-vertical contact in practice co-occurs with a
  distinguishable force magnitude, the direction adds nothing operational and
  the representation is more expensive without being more expressive.
* **The wrench margin is dominated by one term**, exactly as the load term
  threatened to dominate `context_distance` in the superseded design. Report
  per-term contributions; a measure with one live component has replaced one
  category with another.

### Named in advance: the most likely falsifier

**That this is a representation the current worlds cannot exercise.** A flat
plane and a bipedal body with two nominated feet may never produce a case where
direction or tension changes a decision. If so, the honest outcome is that the
representation is right and the EXPERIMENTS are the limiting factor — and the
next work is a world with walls, ramps or holds, not more machinery against a
floor.

## Honest scope, declared in advance

* **This does not claim to make the body walk, stand, or stop falling.** It
  claims the representation discards direction, tension and identity of contact.
  Gate 7 of `EFFECTOR_COMPENSATION_PREREG.md` remains unanswered.
* **Adhesion is not modelled by the simulator.** Sucker pads would have to be
  constraints or applied forces; nothing here makes PyBullet's contact solver
  bilateral, and no claim is made about simulating adhesion faithfully.
* **The friction cone published is a linearised two-direction basis**, which is
  what the simulator reports — not the true cone.
* **One body, one asset, two protocols.** The desk box is the only non-flat
  geometry measured. Nothing here establishes anything about climbing, walls or
  ceilings; those are named as the cases the representation is FOR, not as cases
  it has been tested on.
* **`motor_compose.rs` is shared with the F-16 branch** (byte-identical before
  this arc's reverted attempt), so any change to the deciding path is a change
  there and must be assumed so until measured otherwise.

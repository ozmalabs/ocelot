# PLASTIC COMPENSATION CAPACITY IS THE SECOND AXIS — prereg

**Status:** design recorded, nothing built. Registered 2026-08-07 before
implementation so the gates below cannot be chosen after seeing results.

Continues `HUMANOID_LIMB_AUTHORITY_CONTINUATION.md` §3 (replace alignment's
abstention with an inferred default) and §4 (compensation capacity as a second,
incomparable axis). Lands on `EFFECTOR_AUTHORITY_COLLAPSE_PREREG.md`'s gate 4
(no scalar) and gate 5 (provenance), both of which constrain what follows.

## The claim

**Alignment is a CONVERSION, not a bonus.** A joint near its travel stop loads
that stop, so force passes into structure rather than across the actuator — high
authority, and by the same token nothing left to give. A joint with travel in
hand can yield plastically — lower authority, real capacity to absorb.

One inference yields both, anti-correlated, and they are INCOMPARABLE: separate
Pareto axes, dominance axis-by-axis, the goal picks which to read. Summing them
would be gate 4's failure, and it would also be physically false — a limb is not
"better" for being braced.

## What was measured before any of this was designed

Probe of the standing MJCF humanoid via `observe()`, 2026-08-07:

* **All 21 joints declare finite travel.** None unlimited. So an inferred
  alignment default is available for every actuator, not a subset.
* **Ordinals 6 and 12 — joint indices 9 and 18, range `[-2.793, -0.035]`, a
  symmetric pair — stand at `position = -0.035`, exactly their upper stop.
  Headroom 0.000 rad.** That is the locked knee, and it is already present in
  the very pose the desk gate ran in. The headline case needs no rig.
* **`_write_twitches` already clamps every command to `lower`/`upper`**
  (`pybullet_humanoid_world.py:1264`). The body has been obeying its travel
  limits since it was written; the graph has never been told. A twitch commanded
  at a stop produces less displacement than it declares, so **the declared
  authority is already a lie at the stop** — publishing the bounds does not add
  a mechanism, it reveals one that has been running silently.
* **`maximum_force` and `maximum_velocity` from `getJointInfo` are 0.0 on every
  joint.** The MJCF declares neither. So the §6 residual — one force constant
  across all 43 actuators — is NOT fixable from the asset, and this prereg does
  not claim to fix it.

### The unit trap, recorded because it would have been a silent scale error

`declared_position_change` is `abs(twitch[1])` = 1.0, quantised ×1000 to **1000
units**. But `twitch[1]` is a DIRECTION FRACTION multiplying
`joint_twitch_radians`, so its physical meaning is 0.15 rad. The number is
dimensionless and published on the displacement scale.

`elb_settle_effective_authority_over_reaction_paths` takes a `Max` over
`specified_maximum_position_change_per_action` and
`structural_alignment_authority_units`. **Therefore alignment must be expressed
on that same 0..1000 declared-change scale, never in milliradians.** Publishing
alignment as an angle would have made a braced joint's authority read ~1571
against a declared 1000 and win every `Max` for the wrong reason. Compensation
capacity, being a separate axis that is never combined with anything, keeps its
own honest unit (milliradians of travel).

## The design

### One published quantity, two derived axes

The boundary publishes, per affordance token:

| published | provenance | what it is |
|---|---|---|
| `declared_joint_travel_span_units` | declared, `_measured = 0` | `upper - lower`, milliradians |
| `command_direction_travel_headroom_units` | measured, `_measured = 1` | travel remaining in THIS token's own command direction, milliradians |

**Polarity stays opaque.** The transducer's standing discipline is that command
polarity is not published (`_directed_local_effector_relations`: "left to
graph-side consequence-driven synthesis"). Headroom respects it: the graph
learns how far this token can still go, never which way "further" points. That
is the same discipline as the rest of this boundary — publish the quantity, not
the label.

Rules then derive, in the `run_rules` fixpoint:

```
structural_alignment_authority_units
    = declared_change × (span − headroom) / span      [0 .. declared_change]

plastic_compensation_capacity_units
    = headroom                                        [milliradians]
```

Integer division throughout: both operands are in-frame integers, so this stays
on the integer lattice per the frame/continuum invariant. Anti-correlation is
structural — one number, read two ways — not a fitted relationship.

At a stop: headroom 0 → alignment = full declared authority, compensation 0.
At the far end of travel: alignment 0, compensation = full span.

### Why this replaces the abstention rather than defaulting to zero

`elb_settle` currently reads `structural_alignment_authority_units` only where
declared, on the stated ground that an unmeasured alignment must read neither as
zero (wrongly capping a braced limb) nor as unbounded (wrongly freeing an
unbraced one). That was right while nothing could infer it. It is over-strict
now: **the dark-channel defect was a value read as a MEASURED zero; an INFERRED
value carrying honest provenance is what `*_measured = 0` exists for.**

No change to `effector_limbs` is required. The settle rule already reads the
attribute where present; this seed makes something declare it. That is the test
of whether the abstention was written correctly.

### Damage becomes excess over capacity

The desk gate's damage axis is raw `−peak_N`. Harm is force **in excess of
available compensation capacity**: the same peak absorbed by a flexed limb and
transmitted by a braced one are not the same event. Today's desk data is already
an instance — the stiff arm had maximum authority and no capacity, so the
surplus went into the trunk and the body was thrown (2245 N, base_z 1.205 →
0.12); the compliant arm absorbed it (1394 N, upright).

Comparing a force to a travel needs a conversion, and the only declared one
available is `declared_joint_force_units × headroom` — an absorbable-work term.
That constant is uniform across all 43 actuators (above), so **this axis will
distinguish postures but not joints**, and the gate below is written to expect
exactly that and no more.

### Walking and running are the same knob at two settings

This is why the axis pays for itself beyond the desk:

* **Stance.** The knee at extension has headroom 0 → full structural authority,
  no compensation. Weight goes through the stop, not the actuator. That is how
  standing is cheap, and it is the measured standing pose above.
* **Landing.** Absorbing a footfall requires spending headroom. A knee with
  travel in hand has low authority and high capacity; it yields, and the peak
  never reaches the trunk.
* **The fall / the catch.** A locked arm transmits rather than absorbs — how
  wrists break. Catching yourself requires compensation RESERVE, which makes it
  spendable, which puts it under the energy ledger's affordability test. A body
  with no reserve cannot afford the catch. That is true of a fatigued human and
  it is `EFFECTOR_AUTHORITY_COLLAPSE_PREREG.md` gate 3d arriving from the other
  direction.

Bracing to smash through a wall and staying compliant for an unplanned desk are
the same knob at two settings. **A gait phase detector, a stance rule, a landing
rule, or a knee anywhere in the implementation is a design failure, not a
feature** — the same standard the desk gate held itself to.

## Gates, registered before building

1. **Anti-correlation from one inference.** Across the body's actual joint
   configurations, `structural_alignment_authority_units` and
   `plastic_compensation_capacity_units` move in opposite directions, and both
   trace to a single published headroom. Two independently published numbers
   that happen to correlate fail this gate.
2. **The standing knee reads braced.** Ordinals 6 and 12 derive full structural
   alignment authority and zero compensation capacity from the standing pose,
   with no rule naming a knee, a leg, or a stance. Every other joint derives
   something strictly less than full.
3. **No scalar.** No rule combines the two into one number, and neither enters
   dominance folded with the other. Inherited from gate 4; restated because this
   is the first place two axes are genuinely anti-correlated and summing them
   would look reasonable.
4. **Provenance survives the derivation.** Span carries `_measured = 0`,
   headroom `_measured = 1`, and both derived quantities carry which they came
   from. A derived value that cannot say whether its inputs were declared or
   observed fails.
5. **Unit safety in the `Max`.** Alignment authority read into
   `elb_settle_effective_authority_over_reaction_paths` is on the declared-change
   scale. A braced joint must not exceed its own declared authority via this
   path — it is uncapped BY it, not raised ABOVE it.
6. **Ordering, verified not assumed.** `elb_settle` fires once per member
   (`Not(declared(...))`). Alignment must be declared before it fires, or the
   inference silently never reaches the settle. This is measured on a real
   fixpoint, not argued from rule-eligibility.
7. **Damage as excess.** With the damage axis replaced, the desk gate's turn
   case still eliminates `hold_arm` by dominance. If the verdict flips, that is
   reported as a result, not repaired — the axis is a claim about harm, and the
   desk case is its test.
8. **No gait vocabulary.** Grep the implementation: no knee, no stance, no
   landing, no gait phase, no leg. The stance/landing contrast must fall out of
   headroom alone.

## Honest scope, declared in advance

* **The force constant is uniform.** `declared_joint_force_units` is one config
  value for all 43 actuators, so the excess-over-capacity axis distinguishes
  posture but never differential joint strength. Gate 7 is a posture test only.
* **Headroom is instantaneous.** It is read at the moment it is published and
  carries no rate. A joint approaching its stop fast and one resting at it read
  the same. Nothing here anticipates; that is prereg route (b), still unfired.
* **The emit end stays open.** As with the desk gate, whether the agent APPLIES
  the adopted authority to a live body is not addressed. The compensation axis
  can be read and adopted; nothing here closes that loop.
* **One body, one asset.** The MJCF humanoid's travel limits are the asset's.
  A body with unlimited joints would derive no alignment at all, and this design
  says nothing about what should happen there.
* **Yield is not modelled as plastic.** "Plastic compensation capacity" names
  available travel under load. Whether the joint actually absorbs energy across
  that travel depends on damping this design does not read.

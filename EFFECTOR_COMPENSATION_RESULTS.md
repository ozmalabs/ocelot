# PLASTIC COMPENSATION CAPACITY — results

Measured 2026-08-07 against `EFFECTOR_COMPENSATION_PREREG.md`, whose gates were
registered before any of this existed.

Artifacts: `scripts/gen_effector_compensation_seed.py` →
`seeds/effector_compensation.json` **v1.2.0**, `seeds/effector_limbs.json`
**v1.3.0**, `domains/pybullet_humanoid_world.py` (`_travel_bounds`,
`_declared_actuator_gears`, `_compute_joint_force_limits`, `actuator_options`),
`domains/pybullet_humanoid_trial_transducer.py`,
`tests/test_effector_compensation_migrated.py` (**20/20**),
`scripts/jabberwock_humanoid_compensation_posture.py` →
`results/compensation_posture_gate.json`.

**Headline: the derivation gates PASS on the live body; the posture gate is a
NULL, and the null is the instrument's, not the axis's.** Every derived-reading
gate (1, 2, 3, 4, 5, 6, 8) is answered. Gate 7 is NOT answered, for a reason
that was measured rather than argued — see §5.

## 1. What the boundary was throwing away

Three findings, all from the live standing body before anything was built.

**Every joint declares finite travel, and one pair stands on its stop.** All 21
joints carry real `lower`/`upper`. Ordinals 6 and 12 — indices 9 and 18, range
`[-2.793, -0.035]`, a symmetric pair — stand at `position = -0.035`, exactly
their upper limit, headroom 0.000 rad. The locked joint was already in the pose
the desk gate ran in.

**The host has been clamping to those limits all along.**
`_write_twitches` (`pybullet_humanoid_world.py:1264`) has bounded every
commanded target to `lower`/`upper` since it was written. A twitch commanded at
a stop delivers less than it declares, so **the declared authority was already a
lie at the stop** and the graph was never told. Publishing the bounds did not
add a mechanism; it revealed one that had been running silently.

**The MJCF declares no PER-JOINT force or velocity limits** —
`getJointInfo[10]` and `[11]` are 0.0 on every joint.

> **CORRECTED IN §11.** The conclusion drawn here — *"so §6's residual (one force
> constant across all 43 actuators) is NOT fixable from the asset"* — was too
> narrow and was wrong. MuJoCo declares actuator authority in the `<actuator>`
> block as a per-motor `gear` (100 / 200 / 400 / 600 on this body), which
> PyBullet's loader ignores. **Absence from the channel I checked was read as
> absence from the asset.** The residual was fixable, and §11 fixes it.

### The unit trap, which would have been a silent scale error

`declared_position_change` is `abs(twitch[1])` = 1.0 → 1000 units. But
`twitch[1]` is a dimensionless DIRECTION FRACTION multiplying
`joint_twitch_radians`; its physical size is 0.15 rad. The number is published on
the displacement scale and means neither a metre nor a radian.

`elb_settle_effective_authority_over_reaction_paths` takes a `Max` over that
value and `structural_alignment_authority_units`. Publishing alignment as an
ANGLE would have made a braced joint read ~1571 against a declared 1000 and win
every `Max` for the wrong reason. Travel therefore gets its own declared scale
(`_ANGLE_UNITS_PER_RADIAN`), and alignment is expressed as a fraction OF the
declared change. Gate 5 holds by construction, not by a clamp.

## 2. One reading, two axes — gates 1, 2, 4, 5

The boundary publishes two numbers per token: `declared_joint_travel_span_units`
(declared, `_measured = 0`) and `command_direction_travel_headroom_units`
(measured, `_measured = 1`). **Polarity stays opaque** — the graph learns how far
this token can still go, never which way "further" points, which is the
transducer's standing discipline.

```
alignment = declared_authority x (span - headroom) / span  [0 .. authority]
capacity  = headroom                                       [milliradians]

(the declared authority was the uniform 1000 twitch fraction when this was
 measured; §11 replaces it with the per-actuator gear, and the numbers below
 are on the old scale)
```

On the live standing body, through the seeded rules with nothing hand-fed:

```
tokens deriving both readings : 42 of 43     (the 43rd is the tonic option)
tokens at a stop (capacity 0)  : groups 6 and 12
    group  6   alignment=1000  capacity=0
    group 12   alignment=1000  capacity=0
```

Every other token derives alignment strictly below 1000 and capacity strictly
above 0. **The two tokens of one joint read oppositely**: group 6 `dir=+1` has
headroom 0.000 and group 6 `dir=-1` has 2.758. The locked joint and the
compliant joint are the same joint, and nothing in the seed names either.

The tonic option — which names no joint and commands no displacement — derives
NEITHER reading. Absent, not zero: a headroom of zero means "at the stop", and
reading a blind channel as that would hand a tonic hold the full structural
authority of a braced limb.

Anti-correlation is checked as an exceptionless ordering within each travel
span, not as a correlation coefficient — a fitted relationship tolerates
exceptions and a structural one cannot have any.

## 3. THE SILENT LATCH — gate 6, and the reason it was written

Gate 6 failed on first run, and it failed the way it was written to catch.

With both seeds loaded in one `run_rules`, a braced child read
`effective_authority_units = 50` — the released carrier's cap — while the
correct `structural_alignment_authority_units = 1000` sat on the node beside it.

Diagnosed by distinguishing measurement, not by naming a suspect (§5.3): declare
the alignment in its own fixpoint first, and the same child reads 1000. Pre-set
the attribute by hand with only the limb seed loaded, and it reads 1000. So the
blocker was ORDERING, and the settle term was never at fault.

**Mechanism:** `boot_core.boot` resolves `depends_on` topologically and loads
dependencies FIRST, so **`depends_on` IS rule order**. The whole limb chain
(open → extend → seed root → carrier path → settle) completes in the first pass,
and `elb_settle` latches on `Not(declared(effective_authority_units))`. An
alignment arriving one pass later is present, correct, and never read.

I had declared `effector_compensation depends_on effector_limbs` — the arrow
backwards. A CONSUMER DEPENDS ON ITS PRODUCER. `effector_limbs` is now v1.1.0
with `depends_on: ["effector_compensation"]`, and the gate asserts the manifest
declares it, so the ordering is a property of the seed data rather than of the
test.

**The general form, worth carrying:** a rule that reads an attribute produced
outside its seed's dependency closure is an ordering bug, and a fire-once latch
makes it a SILENT one. Nothing errors; a correct value is simply ignored.

With the arrow the right way round, §1's measured table extends cleanly:

```
  no reaction path, compliant   carrier cap binds       50
  no reaction path, BRACED      stop is the path      1000
```

**No rule in `effector_limbs` changed** — only its dependency list. The
abstention was written correctly; the seed's declaration of what it depends on
was incomplete.

## 4. Not summed — gates 3 and 8

Source audit over the emitted rule data: the two attribute names never appear in
one term, and no rule writes both (which would let one be derived from the
other). This is the one place in the tree where two axes are genuinely
anti-correlated, which is exactly the situation in which adding them looks
reasonable and is wrong — a limb is not "better" for being braced.

No gait vocabulary anywhere in the seed: no knee, stance, landing, gait, leg,
foot, ankle or step. The harness finds the braced set by ASKING THE BOUNDARY
which tokens publish zero headroom; on this body that finds the knee pair, and
on another body it would find whatever that body stands on.

## 5. THE POSTURE GATE IS A NULL, AND THE NULL IS THE RIG'S

Gate 7 asked whether spending travel BEFORE an event changes what arrives.
Identical drop clearance (measured from the body's own lowest point, so a
shorter posture does not fall a shorter distance), identical hold force,
identical goal — only the starting travel differs.

```
 flex  capacity     peak N   base z
  0.0         0    11447.1    1.205
 0.05        50    12748.8    0.793
  0.1       100    11951.0    1.192
  0.2       200    12029.8    0.122
  0.3       300    13554.4    0.107
 0.45       450     9301.5    0.311
  0.6       600     8875.8    0.319
```

Peak is NOT monotone in spent travel — it rises over the upright branch and
falls only where the body collapses. Base height is wildly non-monotone (0.793 at
flex 0.05, 1.192 at 0.10, 0.122 at 0.20). Both goals adopt `braced`; the
compliant candidate is never dominated (capacity rescues it from elimination)
but is never selected either.

**Why, measured.** Instrumenting the joints that stand against a stop through
the drop:

```
  group  6:  -0.035 -> -0.035    travel used 0.000 rad of 2.758 available
  group 12:  -0.035 -> -0.033    travel used 0.002 rad
```

**The joints never move.** At this hold force the landing load never drives them
appreciably through their travel, so travel AVAILABILITY cannot matter — the
compensation mechanism is never engaged in either condition. The flex sweep
therefore varies POSE, and the peak and base-height scatter is fall geometry, not
absorption.

This corrects an explanation I had drafted and not yet written down: that the
standing joint is compliant to a landing because its stop is on the
hyperextension side. That is geometrically true, and it is NOT why the gate
nulled. The measurement named a different cause than the reasoning did — the
third time this session's chain has recorded that (§5.3 of the continuation).

The prereg's own honest scope anticipated the shape of this: *"whether the joint
actually absorbs energy across that travel depends on damping this design does
not read."* A valid rig must drive the load past the joint's holding torque so
the joint actually traverses its travel. That is a load-scale condition, and it
is unmet here.

**No tuning was applied to rescue the gate.** The sweep, the null and the
non-monotonicity stand as measured.

Two rig bugs found and fixed en route, both mine, both worth recording because
each silently produced a legitimate-looking result:

* **Float zero is not zero.** A joint resting on its stop publishes a headroom of
  a few parts in 1e17, not `0.0`. An exact float comparison found NOTHING, so the
  flex never happened and both conditions ran as the same trial — byte-identical
  numbers that looked like a clean null. Zero must mean zero at the declared
  resolution the graph reads.
* **Both conditions must fall the same distance.** Release clearance is measured
  from the body's own lowest point, or a shorter posture falls less far and the
  posture axis measures the rig.

## 6. THE DESK GATE CANNOT TEST THIS AXIS — a premise correction

§4 of the continuation proposed replacing the desk gate's raw `-peak_N` damage
axis with force in excess of available compensation. That is not buildable from
the desk data, for two reasons.

**The desk candidates share a pose, so they share their headroom exactly.**
`hold_arm` and `yield_arm` differ in commanded FORCE and both start from the
same standing configuration, so compensation capacity at the moment of the
decision is identical across them. The axis is constant and cannot discriminate.
That is a property of the instrument, not of the axis — which is why the posture
contrast was built instead.

**The conversion is not identified.** Comparing a force to a travel needs a
conversion, and the desk gives n=2. The one candidate conversion — that a joint
with travel acts as a force limiter at its own declared force — is contradicted
by the data: the measured peak was **2245.8 N under a 120 N holding force**, an
18.7× excess, so the actuator's declared force plainly does not bound the contact
force. Fitting a conversion from two points would be exactly the metric surgery
the Omniglot arc records as never having moved a frontier.

**So the axis was ADDED rather than the damage axis replaced**, and harm as
"force in excess of compensation" is expressed RELATIONALLY by dominance over
the pair rather than arithmetically by subtraction. That is the tree's own
discipline — incomparable quantities stay separate — applied to the one case
where it was tempting to break it.

The desk gate reproduces byte-identically under the boundary change (2245.8 /
1394.3 N, base_z 0.12 / 1.205, both verdicts unchanged).

## 7. HONEST SCOPE

* **Gate 7 is unanswered, not passed and not failed.** No rig here engages the
  mechanism. The walking/running claim in the prereg — stance braces, landing
  absorbs, same knob — remains a DESIGN claim with no physical measurement
  behind it.
* **n=1, deterministic, one body, one asset, one drop height, one hold force.**
  No variance, no seeds, and the sweep's non-monotonicity suggests the fall is
  chaotic enough that n=1 is not sufficient even for the null.
* **Headroom is instantaneous** and carries no rate. A joint approaching its stop
  fast and one resting at it read the same. Nothing here anticipates; prereg
  route (b) is still unfired.
* **The uniform force constant stands.** One config value across 43 actuators,
  unfixable from the asset (§1).
* **The emit end is still open.** Both readings can be derived and adopted;
  nothing applies them to a live body.
* **`grounded_contact_count` and `opposed_effector_engaged` remain dark.** The
  settle rule reads both, and nothing in the tree writes either — so two of its
  four reaction paths are still unreachable in a live graph. Alignment is now the
  only inferred one of the four.

## 8. LOAD DIRECTION IS PUBLISHED — the residual closed (v1.1.0)

The residual this section used to open with: capacity is meaningful only in the
direction the load pushes, and nothing said which direction that was, so a joint
resting on its stop published BOTH readings at once — braced one way, fully
compliant the other — and choosing between them was the harness's guess.

**The channel.** `getJointState[3]` (the actuator's applied motor torque) is lit
on all 21 joints even at bind. Its neighbour `reaction_forces` is identically
zero because joint force-torque sensors are never enabled on this body, so the
applied torque is the ONLY load channel the asset offers. The boundary publishes
`command_direction_load_units`: the load — the negation of the actuator's own
effort — projected onto this token's command direction and floored at zero.

**Provenance is `_inferred = 1`, `_measured = 0`.** The torque is measured; the
negation to a load holds exactly only quasi-statically. A measured torque must
not launder itself into a measured load.

**Polarity stays opaque**, as with headroom: the graph learns that a token bears
load and how much, never which way the load points.

**Exactly one token per joint can bear it**, because the projection is floored —
measured on the live body, 21 of 21 joints have exactly one and none have two.

**Why this could not have been derived from posture.** The two joints standing
on their stop are loaded at 4651 and 2771 milli-newton-metres AT BIND, both on
the zero-headroom token — genuinely braced. After 240 held steps the same pair
reads −0.638 and **+0.022** N·m: one still braced into its stop, the other
relaxed onto the free-travel side. **The same joint in the same posture is
loaded differently at different moments**, and a "symmetric" pair is not
symmetrically loaded. Any rule inferring bracing from geometry would have been
wrong about one of them.

**What the graph now does with it** (`effector_compensation` v1.1.0, three
rules): `ecp_mark_load_bearing_effector` marks the token the load is actually
spending; `ecp_read_loaded_compensation_capacity` and
`ecp_read_loaded_structural_alignment` restrict the two readings to it. The
loaded readings are the unloaded ones RESTRICTED, never different numbers — the
restriction is the whole content. On an unloaded token they are ABSENT, not zero:
zero capacity would read as "nothing to give", which is the opposite claim.

Both the capability reading (near a stop, load-independent) and the loaded
reading (the load goes INTO that stop) are kept, because they answer different
questions.

Ordering was gated by measurement, not by argument — the previous rung's lesson
applied to this one. The mark is registered before the two rules that guard on
it, all three are fire-once, and the gate asserts all 21 loaded readings exist
after ONE fixpoint.

Live: 21 of 43 tokens marked, 21 loaded capacities, 21 loaded alignments. On the
pair standing on their stop, the loaded token reads
`loaded_alignment = 1000, loaded_capacity = 0` and the opposite token of the same
joint reads neither. Gates: `tests/test_effector_compensation_migrated.py` 20/20;
40/40 across the directly-affected suites.

## 9. THE SETTLE, POINTED AT THE LOADED ALIGNMENT AND RE-MEASURED (v1.2.0)

`elb_settle_effective_authority_over_reaction_paths` now reads
`loaded_structural_alignment_authority_units` instead of the capability reading.
**A reaction path you are not reacting against is not a path**, and granting the
full declared authority to a token that is merely NEAR a stop would repeat this
rule's own original error one level up — scoring a STATE as though it were a
reaction. The abstention discipline is unchanged: where the loaded reading is
absent, the path contributes nothing rather than defaulting.

**Gated, and the new case is the point.** Three children of one released carrier
(declared 50), differing only in published channels:

```
  at a stop, load INTO it        effective 1000   the stop is the path
  travel in hand, loaded         effective   50   carrier is the only path
  AT A STOP, BEARING NOTHING     effective   50   braced against nothing
```

The first and third have IDENTICAL posture and identical capability alignment
(1000). Only the load tells them apart, and under v1.1.0 they were
indistinguishable. 20/20.

### The re-measurement on the live body is a NULL, and the cause is the uniform constant

Built the standing body exactly as the transducer's bind does — every
affordance, every channel, and the directed `carried_by` tree — then ran both
semantics over it and diffed:

```
  tokens whose effective authority differs between the two semantics:  0 of 43
  distinct effective authorities across all 32 members:                [1000]
```

**The change moves nothing here.** Every actuator declares the same 1000 and no
carrier is released, so `carrier_path = min(1000, 1000) = 1000` and the `Max` is
1000 whatever the alignment term says. The discrimination is real and gated, but
INERT on this body — and the cause is precisely §6's standing residual, one
config constant across all 43 actuators. **The settle cannot distinguish any two
members of this body in any pose**, which is a sharper statement of that residual
than "thinner than the F-16" was.

### Two pre-existing defects this measurement exposed

Neither is caused by the v1.2.0 change; both were found by finally reading the
settle over real carriage chains instead of a three-node rig. Neither is fixed
here — each changes limb semantics and needs its own gate.

* **5 of 21 groups are in NO carriage chain at all: 2, 6, 12, 17, 20 — including
  BOTH joints standing on their stop.** `_carried_by_effector_relations` emits an
  edge only where a joint's parent LINK is itself an actuated joint; a knee's
  parent link is an unactuated intermediate, so the edge is never emitted. Nine
  `carried_by` pairs for twenty-one joints. **The headline case of this whole arc
  — the joint standing on its stop — never reaches the settle at all.**
* **7 tokens carry `limb_chain_depth = 0` with ZERO incoming `has_limb_member`
  edges**, one per root group, so `elb_seed_root_effective_authority` (which
  matches on the membership edge) never fires for them and they hold no effective
  authority. Mechanism: both tokens of a root group open a limb,
  `elb_retire_duplicate_limb_for_one_chain` deletes one, and the deleted limb
  takes its membership edge with it — **leaving the depth attribute the retracted
  membership had justified.** That is the same class as
  `A DERIVED RELATION MUST NOT OUTLIVE ITS PREMISE` (4347e98b60), recurring: a
  retraction cleaned up the relation and left the attribute derived from it.

## 10. THE CARRIAGE GAP IS CLOSED — carriage passes through a weld

The first of §9's two defects, fixed. A rigid weld moves exactly with its
parent, so a joint beyond one is carried by the nearest ACTUATED ancestor; the
walk stops at anything that is not rigid, because a free hinge genuinely
decouples and treating every unactuated joint as transparent would claim a
carriage relation the mechanism does not provide.

| | before | after |
|---|---|---|
| carriage pairs | 9 | **18** |
| limbs | 7 | **3** (= the 3 true roots) |
| members | 32 / 43 | **42 / 43** |
| groups in NO chain | **5** | **0** |
| depths | ≤ 2 | **0..8** |

**Both joints standing on their stop now reach the settle** — depth 6, loaded
alignment 1000. That is the arc's headline case, previously unreachable by the
rule built to describe it.

`distinct effective authorities` is **still `[1000]`**. Closing the carriage gap
did NOT make the settle discriminate, because with uniform declared authority
the carrier cap never binds. The bottleneck named in §9 is unmoved.

### This retracts a measurement recorded twice

`effector_limbs`' own docstring and the continuation's §1 both read: *"seven
chains of depth <= 2, because co-located multi-DOF joints (abdomen x/y/z, hip
x/y/z) are genuinely NOT carried by one another and correctly do not nest."*

**The number was an artefact and the REASON was wrong.** Carriage was being
severed by welded links, not by co-location. The tell was already visible in the
old output and went unread: it was INCONSISTENT — abdomen_z carried abdomen_y
(adjacent, no weld) while abdomen_y did not carry abdomen_x (weld between).
Co-location cannot explain a difference between two co-located pairs. Serial
revolute joints carry one another whether or not a weld sits between them, and
they now nest.

Whether a co-located 3-DOF cluster SHOULD nest for authority purposes is a
modelling question this does not settle — releasing one axis of a ball joint
reorients the others rather than translating them. What is settled is that the
old answer was decided by where the asset happened to put a weld.

Gates: five unit gates on the walk — weld transparent, free hinge opaque, a run
of welds, no published type falls back to the original direct-parent reading,
and a cycle in the declared parent table cannot hang the boundary.

### One red found while sweeping, and it is NOT this change

`tests/test_embodied_motor_bootstrap_migrated.py::test_real_pybullet_two_receipts_keep_43_motor_pool_stable_and_revision_causal`
fails with `assert [] == [1]` — zero `EmbodiedMotorProgramRevision` nodes.

Enumerated rather than characterised, and established as pre-existing by two
independent checks, because a status line that merely CALLS a red pre-existing is
the failure mode this tree has already been bitten by:

1. **Stash test.** With the transducer change removed the test fails identically,
   same assertion, same line.
2. **The seeds are never loaded there.** That test builds
   `WorldAdapter(seeds=())` with four explicit manifests — `cognitive_pareto`,
   `counterfactual_experiment`, the session seed and the bootstrap seed. Neither
   `effector_limbs` nor `effector_compensation` is among them, so no rule from
   this arc runs in that graph at all.

It is `HUMANOID_LIMB_AUTHORITY_CONTINUATION.md` §2 verbatim — *"ordinal 1 still
does not release"*, `emb_enact_receipt_grounded_motor_program_revision` binding
revisions whose first conjunct kills them — which was recorded as the open next
task before this arc began. `results/failure_baseline.json` cannot adjudicate it:
that baseline was measured at head `0e61f60e8d` on 2026-07-21 under "no data/
symlink", and this test file was last modified after it (`c1353648fd`).

## 11. DIFFERENTIAL DECLARED AUTHORITY — the settle finally discriminates

The bottleneck named in §9 and §10, removed. `distinct effective authorities`
goes from **`[1000]`** to **`[100, 128, 200, 507, 514]`**.

### The asset declared it all along; PyBullet drops it

`getJointInfo[10]` (maximum force) is 0.0 on every joint, which is what made
this look unfixable from the asset — and that reading was too narrow. **MuJoCo
declares actuator authority in the `<actuator>` block, as a per-motor `gear`,**
and this body spans **100 / 200 / 400 / 600** across its 21 joints (8 / 9 / 2 /
2). PyBullet's MJCF loader ignores that block entirely, so the number was
sitting unread in the file the world already loads. Same shape of boundary
discard as `twitch[1]`, `maximum_joint_force` and `parent_for_joint` before it.
Joined on the joint NAME, which never crosses into the graph — what is published
is an ordinal and a magnitude.

### The body had to fly by it, not just declare it

Publishing the gear while continuing to cap every joint identically would have
been **strictly worse than the uniform constant it replaces**: the graph would
reason about differential authority the simulated body does not have. So
`configuration.maximum_joint_force` stops being a flat value and becomes the
anchor for the WEAKEST actuator, with the rest scaled by the asset's own ratio
(`force_j = maximum_joint_force × gear_j / min(gear)`). A body configured at 100
keeps 100 on its weakest joints and gains the asset's 2× / 4× / 6× elsewhere.
Bodies whose asset declares no gears fall back to the flat value exactly as
before.

### The currency was the real defect

The settle's `min` chain read `specified_maximum_position_change_per_action` —
`abs(twitch[1])` quantised, which is **1000 for every actuator by
construction.** It carried no information, so `min(own, carrier)` reduced to
`min(x, x)` and the whole chain was vacuous. The currency is now
`declared_joint_force_units`, the body's only per-actuator authority
declaration; alignment is scaled by it too, so the `Max` stays force-against-
force and gate 5 is preserved on a new scale.

### What the live body now shows

Roots take their own declared authority (200 / 100 / 100). Distal members are
capped by their carriers (100, 200). And **the structural path does real work**:
groups 5 and 11 — gear 600, partially braced, bearing load — reach **507 and
514, above their carrier cap of 200.** That is the alignment path lifting an
effector past what its carrier alone could give, which is the behaviour the
whole reaction-path design was built for and which had never once been visible.

Deterministic across repeated runs.

### THE LOAD MOVED, AND IT REVERSES A HEADLINE OF §8

Re-capturing the standing fixture under the new physics: groups 6 and 12 still
stand ON their stop (headroom 0), but now carry **ZERO** load there — the load
sits on the FREE-TRAVEL token (6798 and 7355). Under the uniform force they were
loaded INTO the stop (4651 and 2771).

**The same posture, the opposite reading, decided by how the body is actuated.**
§8 argued that posture cannot say braced because a joint's load flips between
moments; this is the stronger version — it flips between actuation regimes on an
otherwise identical body. The v1.2.0 loaded-alignment change is independently
vindicated by a measurement taken for another purpose, and the braced-at-a-stop
case is now asserted only in the explicit settle gate, never read off the
standing pose.

### Physics impact, measured not assumed

The desk gate moves and its verdicts do not: peak 2245.8 → **2292.8 N**, yield
1394.3 → **1424.6 N**, arm deflection 0.726 → **0.592 rad**, base_z 0.12 →
0.124. Both goals adopt what they adopted before, and `hold_arm` is still
DOMINATED in the turn case. The gate's conclusion is robust to a change that
moved every number in it.

### A defect this exposed, not fixed

**A carrier's two tokens can now hold DIFFERENT effective authority** (alignment
is direction-dependent), and `elb_carrier_path_authority` matches
`[child, carried_by, carrier]` per token pair while firing once per child — so
it caps against whichever of the carrier's two tokens it happens to bind.
Measured on group 6: carrier hip_y has tokens at 507 and 200, and the knee's
carrier path came out 200, so the knee is capped by its carrier's WEAKER
direction. Deterministic, but arbitrary — nothing chooses. Whether a carrier
should be read at its best direction, or at the one opposing the load, is a
design question this does not settle.

## 12. THE VERIFICATION WAS BROKEN, AND IT HID A RED

Three commits in this arc (`88152fea78`, `2fb62e73e2`, `d9c7628fe2`) carried a
claim of the form *"`test_humanoid_walking_migrated` + `test_humanoid_motor_program_migrated`
21/21 ON THIS TREE."* **That claim is false and is retracted here.**

The runs were invoked as `timeout N pytest … | tail -15`. **A pipeline reports
the LAST command's status, so the exit code read was `tail`'s, not pytest's.**
Every one of those runs was killed at its timeout partway through and recorded
as a pass.

The counts make it plain: `walking` collects 23 and `motor_program` 37, so the
run reported as "21/21" had **60** tests to run and emitted **21** progress
marks. Two later sweeps collected **91** and also emitted 21.

**THE STALL WAS NOT RANDOM.** The walking file's first 21 tests finish in
seconds; test #22 takes ~55-60 minutes AND IS THE ONE THAT FAILS. So the broken
piping did not merely under-verify — **it stopped one test short of the only
failing test in the file, every single time.** The suite was never green at any
point in this arc.

Two further misreadings of the same family, recorded because the root cause is
one thing:

* A partially-written progress line was read as "stuck", and a `ps | grep -c`
  was counting the grep's own shell.
* A parent process at 1 second of CPU was read as "blocked" — it was a
  `ProcessPoolExecutor` manager correctly idle on a futex while a worker child
  burned 30 CPU-minutes.

**The root cause is one habit: reading a PROXY and inferring the state, where
every proxy here is systematically misleading.** The reliable signals are the
SUMMARY LINE in the output (`N passed in Xs`), and aggregate CPU across the
process TREE. Never a pipeline's exit code, never a partial artifact, never a
single PID. This is `HUMANOID_LIMB_AUTHORITY_CONTINUATION.md` §5.3 ("do not
predict the blocker — measure, then say") reproduced three times in one session,
on the measuring apparatus rather than on the subject.

### The red, enumerated

`tests/test_humanoid_walking_migrated.py::test_graph_walks_with_alternating_support_and_bounded_aerial_phases`

**PRE-EXISTING**, established by a matched A/B on a `git worktree` at HEAD
`d9c7628fe2` with the flat force restored — same test, same invocation:

| flag | baseline @ HEAD | with differential authority |
|---|---|---|
| `upright` | False (expected True) | False |
| `bounded_lateral_drift` | False (expected True) | False |
| `bounded_aerial_occupancy` | False (expected True) | False |
| `directed_progress` | False (expected False) ✓ | **True** ← the only difference |

Baseline: `1 failed, 22 passed in 3323.93s`. Three of the four failing flags are
pre-existing and this change is not their cause.

**The fourth flag IS this change's doing, and it is NOT an improvement.** The
gate pins an exact dict plus `walking_passed is False` — it is a frozen record
of *"the agent does not yet walk"*: upright, alternating support, no drift, no
aerial phase, no forward progress. That pinned state was already lost at HEAD.
Differential authority adds forward motion **on top of an already-uncontrolled
body** — it moves while falling. Reporting `directed_progress` flipping to True
as progress would be scoring one axis of a failing regime, which is the same
error `EFFECTOR_AUTHORITY_COLLAPSE_RESULTS.md` records under "scoring a STATE as
though it were an OBJECTIVE".

### What is actually verified, every figure from a summary line

| run | result |
|---|---|
| directly-affected fast suites | **45 passed** |
| `test_effector_compensation_migrated` | **20 passed** |
| `test_humanoid_motor_program_migrated` | **37 passed in 17.56s** |
| walking + control_regime + energetics + body_ingest, with change | **35 passed, 1 failed** |
| walking file, baseline @ `d9c7628fe2` | **22 passed, 1 failed** |
| desk gate | verdicts unchanged; every number moved (§11) |

`motor_program` was never slow — it runs in 17.56 s. The whole apparent slowness
of this arc's verification was one test.

## 13. Standing residuals

* **The orphaned root tokens are still open** (§9): 3 now rather than 7, one per
  root group, each holding a `limb_chain_depth` its retracted membership had
  justified.
* **A carrier's weaker token can cap a child arbitrarily** (§11) — the one
  defect the differential-authority work exposed.
* **Load is instantaneous, like headroom**, and published at bind. The
  240-held-step measurement above shows it genuinely moves, so a decision reading
  it is reading one moment. Nothing carries a rate; prereg route (b) is still
  unfired.
* **Gate 7 remains unanswered.** The load channel does not fix the posture rig —
  the joints still never traverse their travel under this hold force.
* **Limb-level aggregation is not built.** All readings are per affordance. A
  chain's compliance is presumably some composition along it; nothing here claims
  which, and `Sum`-in-`where` is a known-bad idiom in this engine.
* **Nothing consumes the capacity axis outside the posture harness**, exactly as
  `carried_by` was consumed only by `effector_limbs` when it landed.

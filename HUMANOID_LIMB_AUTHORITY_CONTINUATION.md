# Limb authority — where to pick up

Written 2026-08-07 at the end of a long session. Everything below is either
MEASURED (with the number) or explicitly marked as not yet measured. Nothing
here is inferred-and-stated-as-fact; that failure mode cost three wrong calls
today and the corrections are recorded in §5.

## 1. What is landed and verified

**The desk gate passes** (`EFFECTOR_AUTHORITY_COLLAPSE_RESULTS.md`, commit
2ca959249b). Same rules, same candidates, same physics; only the goal's declared
demand differs and the outcome inverts — turning releases the hand and the body
stays upright, reaching-through drives into the obstruction. The turn case is
decided by DOMINANCE (the stiff option is strictly worse on damage and posture),
not merely deprioritised.

**Three boundary discards found and fixed.** Each was a quantity the host
computed and dropped at the graph edge, which a rule downstream then read as a
measured zero:

| discarded | now published as | was |
|---|---|---|
| `twitch[1]` | `specified_maximum_position_change_per_action` | 7,196 reads / 0 writes |
| `maximum_joint_force` | `declared_joint_force_units` | dark |
| `parent_for_joint` | `carried_by` edges | symmetrised away by `tuple(sorted(...))` |

All carry `*_measured = 0` provenance, after the F-16 pattern.

**Limbs derive from `carried_by`** (`seeds/effector_limbs.json`). No rule names
an arm, a leg or a joint — a limb is whatever maximal chain the edges form.

> **CORRECTED 2026-08-07 (see §4c): the shape reported here was an ARTEFACT.**
> It read "7 acyclic chains, one per carriage root, depths <= 2. Co-located
> multi-DOF joints (abdomen x/y/z, hip x/y/z) correctly do NOT nest." Measured
> after the carriage fix: **3 trees, depths 0..8, 42 of 43 tokens members.**
> Carriage was being severed by rigidly WELDED links, not by co-location — and
> the old reading was self-inconsistent (abdomen_z carried abdomen_y, adjacent;
> abdomen_y did not carry abdomen_x, weld between), which co-location cannot
> explain. **The stated REASON was wrong, not just the number.**

**Authority is a MAXIMUM over reaction paths, not a minimum down the chain.**
Measured, carrier released to 50:

```
  no reaction path          {3:1000, 4:50, 5:  50}   carrier cap binds
  grounded contact          {3:1000, 4:50, 5:1000}   closed chain, uncapped
  opposed effector engaged  {3:1000, 4:50, 5:1000}   co-contraction, uncapped
```

**The proposer chain is unblocked.** Two stacked blockers, both measured by
cumulative prefix scan on a live 71k-node checkpoint:
1. `causal_yield_units == 0` — a stricter test than the hold rules ever applied.
   BOTH `cs_hold_zero_yield_...` and `cs_hold_marginally_dominated_...` mint the
   same residual kind, so a process held for INEFFICIENCY could never satisfy a
   proposer demanding it produced nothing. Ordinal 1 had succeeded 7 of 22
   attempts; succeeding is what disqualified it.
2. The episode-wide selection guard on the two PROPOSE rules — a suspended
   capability runs no trials, so it never sees the momentary gap between one
   selection retiring and the next binding. Scoped to the residual's own
   capability. (SELECT and both ENACT rules keep the episode-wide guard.)

Result: proposer 0 -> 1 survivors, revisions 4 -> 5.

## 2. The immediate next task — ordinal 1 still does not release

`emb_enact_receipt_grounded_motor_program_revision` binds 2 revisions and its
FIRST conjunct `revision.status == "proposed"` kills both. Base profile:
`enum 546 -> 2, full_nopushdown 30 -> 0`.

Hypothesis (NOT measured): the two that bind are the already-`enacted` ones, and
the newly minted revision fails the 20-clause match structurally, so it never
reaches the guard. **Read the new revision's actual status and edges. Do not
infer them.**

Method that works: cumulative PREFIX scan, never isolated-conjunct bisect — see
§5.

## 3. Alignment — infer a default, do not abstain

Making alignment abstain until measured was over-strict. The dark-channel
defect was a value read as a MEASURED zero; an INFERRED value with honest
provenance is not that failure mode, it is what `*_measured = 0` exists for.

Cheap inference, no moment arm needed: **a joint at the end of its declared
travel is loading its stop, so force passes into structure rather than across
the actuator** — the locked knee. PyBullet already exposes `lower`/`upper` per
joint (e.g. `abdomen_z: +-0.785`); publishing them is one more boundary value of
the same shape as the three above. `|angle| / range -> 1` gives a serviceable
alignment default.

Two more near-free signals: chain depth (a distal member with grounded contact
is in a closed chain by construction), and whether the commanded direction
opposes the measured load (an actuator being back-driven is not bearing
structurally).

`structural_alignment_authority_units` currently contributes to
`elb_settle_effective_authority_over_reaction_paths` ONLY where declared, and is
absent otherwise. Replace the abstention with the inferred default.

## 4. PLASTIC FORCE COMPENSATION CAPACITY — the second axis

Alignment is a CONVERSION between two quantities, not a bonus:

* **aligned / braced** — high authority, ~zero capacity to absorb; failure is
  brittle and structural.
* **flexed / off-axis** — lower authority, real capacity to yield plastically.

One inference (angle vs range) yields both, anti-correlated. They are
INCOMPARABLE objectives and must never be summed — separate Pareto axes,
dominance axis-by-axis, goal picks which to read.

**Today's desk data is already an instance.** The stiff arm had maximum
authority and zero compensation, so the surplus went into the trunk and the body
was thrown: 2245 N, base_z 1.205 -> 0.12. The compliant arm absorbed it: 1394 N,
upright. The RESULTS file writes this up as "damage weighed"; the mechanism is
sharper — the arm ran out of compensation capacity.

Consequences to build:
* **Replace the damage axis.** It is currently raw `-peak_N`. Harm is force in
  EXCESS OF AVAILABLE COMPENSATION CAPACITY — the same peak absorbed by a flexed
  limb and transmitted by a braced one are not the same event.
* **The fall case.** A locked arm transmits rather than absorbs (how wrists
  break). Catching yourself needs compensation RESERVE, making it spendable and
  putting it under the energy ledger's affordability test — a body with no
  reserve cannot afford the catch, which is true of a fatigued human.
* Bracing to smash through a wall and staying compliant for an unplanned desk
  are THE SAME KNOB at two settings. No case-specific rule for either.

## 4b. §3 AND §4 ARE BUILT — what landed, and what did not (2026-08-07, later)

`EFFECTOR_COMPENSATION_PREREG.md` / `EFFECTOR_COMPENSATION_RESULTS.md`,
`seeds/effector_compensation.json` v1.0.0, `seeds/effector_limbs.json` v1.1.0,
`tests/test_effector_compensation_migrated.py` 15/15.

**The abstention in §3 is replaced.** One published quantity per token — travel
headroom in that token's own command direction, plus the declared span — yields
BOTH axes, anti-correlated by construction:
`alignment = declared_change x (span - headroom) / span`, `capacity = headroom`.
On the live standing body 42 of 43 tokens derive both (the tonic option derives
NEITHER — absent, not zero), and exactly the two joints standing on their stop
read alignment 1000 / capacity 0. **The two tokens of one joint read oppositely**
(headroom 0.000 one way, 2.758 the other), so the locked joint and the compliant
joint are the same joint. No rule in `effector_limbs` changed.

**Three things the boundary was hiding.** All 21 joints declare finite travel;
`_write_twitches` has been clamping every command to those limits since it was
written, so **the declared authority was already a lie at the stop**; and the
MJCF declares NO joint force or velocity limits at all, so §6's uniform-force
residual is not fixable from the asset.

**The unit trap, avoided.** `specified_maximum_position_change_per_action` = 1000
is a dimensionless direction FRACTION (physical size 0.15 rad), not an angle.
Publishing alignment in milliradians would have made a braced joint read ~1571
against a declared 1000 and win `elb_settle`'s `Max` for the wrong reason.
Travel got its own declared scale.

**The new method correction — the SILENT LATCH.** `boot_core.boot` resolves
`depends_on` topologically, so **`depends_on` IS rule order.** With the arrow
declared backwards, the entire limb chain completed in pass 1 and `elb_settle`
latched on `Not(declared(effective_authority_units))` BEFORE the alignment
existed: a braced child read 50 with the correct 1000 sitting on the node beside
it. Nothing errored. **A rule reading an attribute produced outside its seed's
dependency closure is an ordering bug, and a fire-once latch makes it silent.**
A consumer depends on its producer.

**§4's damage-axis replacement is a premise correction, not a build.** The desk
candidates share a pose, so they share headroom exactly — the axis TIES there and
the desk cannot test it. And the conversion is unidentified: peak was 2245.8 N
under a 120 N holding force (18.7x), so declared actuator force does not bound
contact force, and fitting a conversion from n=2 is metric surgery. The axis was
ADDED; harm-as-excess is expressed RELATIONALLY by dominance over the pair.

**The posture/walking gate is a NULL and it is the rig's.** Flex sweep
non-monotone in peak; instrumenting the drop, the joints traverse **0.000 and
0.002 rad of the 2.758 available** — they never move, so travel availability
cannot matter and the sweep varies pose, not compliance. A valid rig must drive
the load past the joint's holding torque. **The walking/running claim has no
physical measurement behind it yet.** Not tuned, not rescued.

Two rig bugs worth carrying: a joint resting on its stop publishes headroom of a
few parts in 1e17, **not `0.0`**, so an exact float comparison silently made both
conditions the same trial and produced a clean-looking null; and both conditions
must be released from the same clearance measured from the body's own lowest
point, or a shorter posture falls less far and the posture axis measures the rig.

**LOAD DIRECTION IS NOW PUBLISHED (v1.1.0)** — the residual above, closed.
`getJointState[3]` (applied motor torque) is lit on all 21 joints at bind, and
`reaction_forces` is identically zero (force sensors never enabled), so it is the
only load channel this asset has. The boundary publishes
`command_direction_load_units` = the load (the negation of the actuator's own
effort) projected onto the token's command direction and floored, so **exactly
one of a joint's two tokens can bear it** — 21 of 21, none with two. Provenance
`_inferred = 1`, `_measured = 0`: the torque is measured, the negation to a load
is quasi-static only. Polarity stays opaque.

**Why posture could never have given this.** The pair standing on their stop
read loads of 4651 / 2771 at bind (both braced INTO the stop) and −0.638 /
**+0.022** N·m after 240 held steps — one still braced, the other relaxed onto
the free-travel side. **The same joint in the same posture is loaded differently
at different moments**, so a "symmetric" pair is not symmetrically loaded and any
geometric inference of bracing is wrong about one of them.

Three rules: `ecp_mark_load_bearing_effector` marks the token the load is
spending; `ecp_read_loaded_compensation_capacity` / `..._structural_alignment`
restrict the readings to it (RESTRICTED, never different numbers; ABSENT on an
unloaded token, since zero capacity is the opposite claim). The capability
reading is kept alongside — they answer different questions. Ordering gated by
measurement: the mark registers before the rules guarding on it, all 21 loaded
readings present after ONE fixpoint. 20/20, 40/40 affected.

**`elb_settle` NOW READS THE LOADED ALIGNMENT (effector_limbs v1.2.0)** — a
reaction path you are not reacting against is not a path. Gated on three children
of one released carrier: at a stop with the load INTO it → 1000; travel in hand →
50; **AT A STOP BEARING NOTHING → 50**. The first and third have identical posture
and identical capability alignment; only the load separates them, and under
v1.1.0 they were indistinguishable.

**The live re-measurement is a NULL, and it names the real bottleneck.** Built
the standing body as the transducer's bind does (all channels + the directed
`carried_by` tree) and diffed both semantics: **0 of 43 tokens differ**, and the
distinct effective authorities across all 32 members are `[1000]`. Every actuator
declares the same 1000 and no carrier is released, so `carrier_path = min(1000,
1000)` and the `Max` is 1000 regardless. **The settle cannot distinguish any two
members of this body in any pose** — a sharper statement of §6's uniform-constant
residual than "thinner than the F-16".

**TWO PRE-EXISTING DEFECTS the measurement exposed** (neither caused by v1.2.0,
neither fixed — each changes limb semantics and needs its own gate):

* **5 of 21 groups are in NO carriage chain: 2, 6, 12, 17, 20 — including BOTH
  joints standing on their stop.** `_carried_by_effector_relations` emits an edge
  only where a joint's parent LINK is itself actuated; a knee's parent link is an
  unactuated intermediate. Nine pairs for twenty-one joints. **The headline case
  of this whole arc never reaches the settle at all.**
* **7 tokens hold `limb_chain_depth = 0` with ZERO incoming `has_limb_member`**,
  one per root group, so root authority never fires for them. Both root tokens
  open a limb, `elb_retire_duplicate_limb_for_one_chain` deletes one, and the
  deleted limb takes its membership edge — **leaving the depth the retracted
  membership had justified.** Same class as `A DERIVED RELATION MUST NOT OUTLIVE
  ITS PREMISE` (4347e98b60), recurring.

## 4c. THE CARRIAGE GAP IS CLOSED — carriage passes through a weld (2026-08-07)

`_carried_by_effector_relations` mapped a joint's parent LINK straight to a
channel and gave up when that link was not itself actuated, so **a rigidly
welded intermediate SEVERED the chain.** 12 of this body's 33 links are FIXED and
they sit between actuated joints throughout.

A rigid weld moves exactly with its parent, so a joint beyond one is carried by
the nearest ACTUATED ancestor — a fact about the body, not an approximation. The
walk stops at anything that is not rigid: **a free hinge genuinely decouples**,
and treating any unactuated joint as transparent would claim a carriage relation
the mechanism does not provide. Reaching the base without an actuated ancestor
means a true root.

| | before | after |
|---|---|---|
| carriage pairs | 9 | **18** |
| limbs | 7 | **3** (= the 3 true roots) |
| members | 32 / 43 | **42 / 43** (43rd is the tonic option) |
| groups in NO chain | **5** — incl. both stop-standing joints | **0** |
| depths | ≤ 2 | **0..8** |
| orphaned root tokens | 7 | 3 (one per root; defect still open) |

**Both joints standing on their stop now reach the settle** (depth 6, loaded
alignment 1000) — the arc's headline case, previously unreachable by the rule
built to describe it.

`distinct effective authorities` is **still `[1000]`**: with uniform declared
authority the carrier cap never binds, so closing the carriage gap did not make
the settle discriminate. That remains the next lever.

Gates: 5 new unit gates on the walk (weld transparent; free hinge opaque; run of
welds; no published type ⇒ original direct-parent reading; cycle-safe).

## 4d. DIFFERENTIAL DECLARED AUTHORITY — the settle finally discriminates

`distinct effective authorities` goes from **`[1000]`** to
**`[100, 128, 200, 507, 514]`**.

**The asset declared it all along.** §1 above concluded the uniform-force
residual was "NOT fixable from the asset" because `getJointInfo[10]` is 0.0 on
every joint. **That read absence from the channel I checked as absence from the
asset, and it was wrong.** MuJoCo declares actuator authority in the
`<actuator>` block as a per-motor `gear` — **100 / 200 / 400 / 600** across this
body's 21 joints — and PyBullet's MJCF loader ignores it. Same shape of boundary
discard as `twitch[1]`, `maximum_joint_force` and `parent_for_joint`.

**The body must FLY by it, not just declare it.** Publishing the gear while
capping every joint identically would be strictly worse than the uniform
constant: the graph would reason about differential authority the simulated body
does not have. `maximum_joint_force` becomes the anchor for the WEAKEST actuator
(`force_j = maximum_joint_force × gear_j / min(gear)`); assets with no gears fall
back to the flat value unchanged.

**The currency was the real defect.** The settle's `min` chain read
`specified_maximum_position_change_per_action` = `abs(twitch[1])` quantised =
**1000 for every actuator by construction.** `min(x, x)` is vacuous, which is
why nothing ever discriminated. The currency is now `declared_joint_force_units`;
alignment is scaled by it too, so the `Max` stays force-against-force.

**The structural path does real work at last:** groups 5 and 11 (gear 600,
partially braced, bearing load) reach **507 / 514, ABOVE their carrier cap of
200** — an effector lifted past what its carrier alone could give, the behaviour
the reaction-path design was built for and which had never once been visible.

**THE LOAD MOVED, reversing a §4b headline.** Groups 6 and 12 still stand ON
their stop, but now carry **ZERO** load there — it sits on the free-travel token
(6798 / 7355), where under uniform force it was INTO the stop (4651 / 2771).
Same posture, opposite reading, decided by how the body is actuated. POSTURE
DOES NOT SAY BRACED — now measured twice on one body, and the v1.2.0
loaded-alignment change is vindicated by a measurement taken for another purpose.
The braced-at-a-stop case is asserted only in the explicit settle gate now, never
read off the standing pose.

**Physics impact, measured:** the desk gate moves and its verdicts do not — peak
2245.8 → 2292.8 N, yield 1394.3 → 1424.6 N, arm deflection 0.726 → 0.592, base_z
0.12 → 0.124; both goals adopt what they adopted before and `hold_arm` is still
DOMINATED in the turn case.

**A defect exposed, not fixed:** a carrier's two tokens can now hold DIFFERENT
effective authority (alignment is direction-dependent), and
`elb_carrier_path_authority` fires once per child against whichever carrier token
it binds. Measured: hip_y holds 507 and 200, and the knee was capped at 200 — its
carrier's WEAKER direction. Deterministic but arbitrary; nothing chooses.

**THE VERIFICATION IN THIS ARC WAS BROKEN — see RESULTS §12.** Three commits
claimed "walking + motor_program 21/21"; those runs were `pytest … | tail`, so
the exit code read was TAIL'S, and each was killed at its timeout after 21 of 60
(or 91) tests. Retracted. Worse: the walking file's first 21 tests take seconds
and **test #22 is both the ~55-minute one and the only failing one**, so the
broken pipe stopped one test short of the only red, every time.

**The red, enumerated and matched-A/B'd as PRE-EXISTING:**
`tests/test_humanoid_walking_migrated.py::test_graph_walks_with_alternating_support_and_bounded_aerial_phases`.
At HEAD with the flat force restored: `1 failed, 22 passed`. `upright`,
`bounded_lateral_drift`, `bounded_aerial_occupancy` are False in BOTH arms.
The ONE difference is `directed_progress` False → **True** under differential
authority — and that is NOT an improvement: the gate pins "does not yet walk",
that pinned state was already lost, and the change adds forward motion to an
already-uncontrolled body. It moves while falling.

**Reliable signals from now on:** the SUMMARY LINE (`N passed in Xs`) and
aggregate CPU across the process TREE. Never a pipeline exit code, never a
partial artifact, never one PID. (`motor_program` is 37 passed in 17.56s — it
was never slow; one test was.)

**Next, in order:** that carrier-token ambiguity (read the carrier at its best
direction, or at the one opposing the load — a design question); the orphaned
root tokens (a retraction left a stale derived attribute); then a rig whose load
exceeds holding torque, since gate 7 is still unanswered.
`grounded_contact_count` and `opposed_effector_engaged` are still dark, so two of
`elb_settle`'s four reaction paths remain unreachable live.

## 5. Method corrections earned today — read before diagnosing

1. **Cumulative prefix scan, not isolated bisect.** Testing each `where`
   conjunct alone tells you whether that conjunct admits SOME binding; it does
   not tell you the conjunction is satisfiable, because survivors of different
   conjuncts can be disjoint. Isolated bisect named conjunct [14]; the prefix
   scan showed the conjunction already died at [2]. Cost one wrong fix.
2. **A prefix scan localises the FIRST blocker, not the only one.** After
   removing blocker 1 the scan ran further and died at [13] — the guard I had
   just declared "never the blocker". Cost one wrong retraction.
3. **Do not predict the blocker.** Three times today I named one from reasoning
   and the measurement named a different one. Measure, then say.
4. **Check the type name.** "CognitiveCheckin: 0" was a typo for
   `CognitiveCheckIn` (131 of them) and briefly derailed the diagnosis.
5. `WorldAdapter.load(path)` resumes a checkpoint; `profile_rule_match(name)`
   returns `[(stage, count, survivors)]` and is read-only. `run_rules()` on a
   71k-node graph takes ~8 minutes — background it.
6. **Retract rather than prevent** when a mint guard will not take. The limb
   count was fixed by `Argmin` survivor + delete-the-rest
   (`retire_duplicate_gap` pattern), after a same-pass uniqueness guard failed
   twice. Unresolved: whether `batch: False` does not sequence, or
   `NodesOfType` does not see same-pass mints. Worth establishing.

## 6. Standing residuals

* Nothing consumes `carried_by` outside `effector_limbs`. The desk axes still
  treat joints as peers — "release at the shoulder to free the hand" is now
  EXPRESSIBLE but no rule expresses it.
* The desk gate tests the DECISION layer only. Candidates are measured post-hoc;
  nothing predicts them, so prereg route (b) — the forward model projecting a
  crossing BEFORE contact — has still never fired live.
* The loop is open at the emit end: `arm_authority_units` is read back but not
  applied to a live body by the agent.
* `declared_joint_force_units` is one config constant across all 43 actuators,
  so the axis distinguishes demand but never differential authority between
  joints — thinner than the F-16, where each loop declares its own clamp.
* growth10 (port 8820) was healthy at 6h49m: 71k nodes, 1.7 GB, ord 3 at
  1147 attempts / 514 successes, imagination trace flat at ~5.8k.

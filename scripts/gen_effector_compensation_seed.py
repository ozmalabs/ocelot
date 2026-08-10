#!/usr/bin/env python3
"""ALIGNMENT IS A CONVERSION, NOT A BONUS — one travel reading, two axes.

`EFFECTOR_COMPENSATION_PREREG.md`, gates 1-6. Continues
`HUMANOID_LIMB_AUTHORITY_CONTINUATION.md` §3 and §4.

THE PHYSICAL FACT. A joint near its travel stop loads that stop, so force passes
into structure rather than across the actuator: high authority, and by the same
token nothing left to give. A joint with travel in hand can yield: lower
authority, real capacity to absorb. **One reading gives both, anti-correlated.**

  aligned / braced   -> high authority, ~zero capacity; failure is structural
  flexed / off-axis  -> lower authority, real plastic compensation

They are INCOMPARABLE and are never summed. Separate axes, dominance
axis-by-axis, the goal picks which to read — the same refusal to scalarise that
`effector_authority_axis` holds, applied to the one place where two axes are
genuinely anti-correlated and adding them would look reasonable.

WHY THIS REPLACES AN ABSTENTION. `elb_settle_effective_authority_over_reaction_
paths` reads `structural_alignment_authority_units` only where declared, because
nothing could infer it and an unmeasured alignment must read neither as zero
(wrongly capping a braced limb) nor as unbounded (wrongly freeing an unbraced
one). That was right while no channel carried travel. It is over-strict now: the
dark-channel defect was a value read as a MEASURED zero, and an INFERRED value
carrying honest provenance is exactly what the `*_measured = 0` flag exists for.

NOTHING IN `effector_limbs` CHANGES. The settle rule already reads the attribute
where present; this seed makes something declare it. That the fix needs no edit
there is the test of whether the abstention was written correctly.

NOTHING HERE NAMES A KNEE, A STANCE, A LANDING OR A GAIT PHASE. Standing cheaply
on an extended knee and absorbing a footfall on a flexed one are THE SAME KNOB at
two settings, and the knob is travel headroom. On the standing MJCF humanoid the
knee pair already sits at headroom 0.000 in the extending direction and 2.758 in
the flexing one — the locked knee and the compliant knee are the two tokens of
one joint, and neither is a special case.

THE UNIT TRAP, recorded because it would have been a silent scale error.
Travel is published on its own angle scale (milliradians), and alignment must
NOT be expressed there: `elb_settle` takes a `Max` over it against the
effector's declared authority, and an angle would win that `Max` for the wrong
reason. Alignment is therefore a FRACTION OF THE DECLARED AUTHORITY, so a braced
joint is uncapped BY its own authority and never raised ABOVE it -- by
construction, not by a clamp.

THE AUTHORITY CURRENCY IS `declared_joint_force_units` (v1.2.0), not the twitch
fraction it used to be. `specified_maximum_position_change_per_action` is
`abs(twitch[1])` quantised, which is 1000 for EVERY actuator by construction: it
carried no information, and scaling by it made every joint's alignment
identically scaled. The declared force is the body's only per-actuator authority
declaration -- 100 / 200 / 400 / 600 on this asset -- so it is what "this
effector's authority" can mean at all.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def V(n): return {"type": "Var", "name": n}
def L(v): return {"type": "Lit", "value": v}
def A(n, k): return {"type": "Attr", "node": V(n), "key": k}
def P0(n, k): return {"type": "Plus", "items": [A(n, k), L(0)]}
def Eq(a, b): return {"type": "Eq", "a": a, "b": b}
def Gt(a, b): return {"type": "Gt", "a": a, "b": b}
def And(*i): return {"type": "And", "items": list(i)}
def Not(a): return {"type": "Not", "arg": a}
def Minus(a, b): return {"type": "Minus", "a": a, "b": b}
def Times(*i): return {"type": "Times", "items": list(i)}
def IDiv(a, b): return {"type": "IDiv", "a": a, "b": b}
def T(t): return {"__term__": t}


def declared(n, k):
    """PRESENT, not present-and-zero.

    Load-bearing twice over here. An absent HEADROOM read as zero means "at the
    stop", which would hand full structural authority to a channel nobody
    measured — the most consequential possible misreading of a blind channel in
    this file. An absent SPAN read as zero is a division by zero. The boundary
    publishes both as ABSENT for the tonic option, which names no joint.
    """
    return Not(Eq(A(n, k), L(None)))


def infer_structural_alignment_rule():
    """ALIGNMENT INFERRED FROM TRAVEL — §3's default, replacing the abstention.

        alignment = declared_authority x (span - headroom) / span

    At a stop (headroom 0) this is the full declared authority: the load goes
    into the stop, so the carrier cap does not bind and the effector is uncapped
    BY its own declared authority. At the far end of travel (headroom = span) it is
    zero: nothing is braced, and the rule contributes nothing to the `Max`
    rather than pretending to.

    IN-FRAME AND THEREFORE INTEGER. Span, headroom and the declared authority
    are all integers on the graph's own lattice, and `IDiv` keeps the quotient
    there. The multiplication comes FIRST so the quantisation happens once, at
    the end, instead of collapsing a ratio to 0 or 1 before it is scaled.

    PROVENANCE. This is neither measured nor declared: it is INFERRED from a
    declared span and a measured headroom. It carries `_measured = 0` so it can
    never be mistaken for an observation, and `_inferred = 1` so it is not
    mistaken for configuration either.

    RANGE SAFETY BY CONSTRUCTION, not by a clamp: the boundary already floors
    headroom at 0 and it cannot exceed span, so `(span - headroom) / span` lies
    in [0, 1] and the result lies in [0, declared authority]. Gate 5 holds
    without a guard that could hide a unit error.
    """
    return {
        "name": "ecp_infer_structural_alignment_from_travel",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "batch": True,
        "comment": "A joint near its travel stop loads the stop, so force "
        "passes into structure rather than across the actuator. Inferred from "
        "published travel, on the declared-change scale, never as an angle.",
        "match": [
            ["body", "has_opaque_embodied_actuator_affordance", "affordance"],
        ],
        "where": And(
            declared("affordance", "declared_joint_travel_span_units"),
            declared("affordance", "command_direction_travel_headroom_units"),
            declared("affordance",
                     "declared_joint_force_units"),
            Gt(P0("affordance", "declared_joint_travel_span_units"), L(0)),
            Not(declared("affordance", "structural_alignment_authority_units")),
        ),
        "effects": [
            ["set_attr", "affordance", "structural_alignment_authority_units",
             T(IDiv(
                 Times(
                     P0("affordance",
                        "declared_joint_force_units"),
                     Minus(
                         P0("affordance", "declared_joint_travel_span_units"),
                         P0("affordance",
                            "command_direction_travel_headroom_units"),
                     ),
                 ),
                 P0("affordance", "declared_joint_travel_span_units"),
             ))],
            ["set_attr", "affordance",
             "structural_alignment_authority_units_measured", 0],
            ["set_attr", "affordance",
             "structural_alignment_authority_units_inferred", 1],
        ],
    }


def read_plastic_compensation_rule():
    """PLASTIC COMPENSATION CAPACITY — §4's second axis, the same reading.

    Capacity to absorb IS the travel still available in the direction the
    actuator is pushing. A joint at its stop can give nothing and transmits
    whatever arrives (this is how wrists break); a joint with travel in hand
    yields, and the peak never reaches what carries it.

    NOT A CONVERSION OF THE ALIGNMENT — the SAME published headroom, read as
    itself. That is what makes the anti-correlation structural rather than
    fitted, and it is why gate 1 can be checked at all: two independently
    published numbers that merely happened to correlate would prove nothing.

    Kept in its own honest unit (milliradians of travel) rather than rescaled to
    match the alignment. Nothing ever combines the two, so they never need a
    common scale — the same consequence of refusing to scalarise that bought
    `effector_authority_axis` its integer frame.

    PROVENANCE `_measured = 1`: the number is a measured travel, and it moves as
    the body moves. Only its READING as capacity is a claim, and that claim is
    this rule's name.
    """
    return {
        "name": "ecp_read_plastic_compensation_capacity_from_travel",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "batch": True,
        "comment": "What this effector can still give. The anti-correlated "
        "reading of the same travel the alignment rule consumes; never summed "
        "with it, never folded into it.",
        "match": [
            ["body", "has_opaque_embodied_actuator_affordance", "affordance"],
        ],
        "where": And(
            declared("affordance", "command_direction_travel_headroom_units"),
            Not(declared("affordance", "plastic_compensation_capacity_units")),
        ),
        "effects": [
            ["set_attr", "affordance", "plastic_compensation_capacity_units",
             T(P0("affordance", "command_direction_travel_headroom_units"))],
            ["set_attr", "affordance",
             "plastic_compensation_capacity_units_measured", 1],
        ],
    }


def mark_load_bearing_rule():
    """WHICH TOKEN IS ACTUALLY BEARING THE LOAD — the graph picking, not the
    harness guessing.

    THE RESIDUAL THIS CLOSES. Headroom and its two readings are published PER
    COMMAND DIRECTION, and until now nothing said which direction the load
    pushes. So a joint resting on its stop published BOTH readings at once —
    braced one way, fully compliant the other — and choosing between them was
    the harness's guess. It is now the graph's, from a channel the boundary
    publishes.

    MEASURED ON THE STANDING BODY (2026-08-07), and it is not a formality: the
    two joints standing on their stop are loaded in OPPOSITE directions
    (applied torque -0.638 and +0.022 N*m). One is braced against its stop and
    the other is unloaded and free to give. A "symmetric" pair is not
    symmetrically loaded, so a rule that assumed either reading applied to both
    would have been wrong about one of them every time.

    Exactly one of a joint's two tokens can be marked: the boundary floors the
    projection at zero, so the token pointing away from the load reports none.
    """
    return {
        "name": "ecp_mark_load_bearing_effector",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "batch": True,
        "comment": "The token whose headroom the load is actually spending. "
        "Zero load is not 'no reading' — it is the honest statement that this "
        "direction is not the loaded one.",
        "match": [
            ["body", "has_opaque_embodied_actuator_affordance", "affordance"],
        ],
        "where": And(
            declared("affordance", "command_direction_load_units"),
            Gt(P0("affordance", "command_direction_load_units"), L(0)),
            Not(declared("affordance", "bearing_load")),
        ),
        "effects": [["set_attr", "affordance", "bearing_load", 1]],
    }


def loaded_compensation_rule():
    """The capacity that MATTERS: travel in hand where the load is spending it.

    A copy of `plastic_compensation_capacity_units`, restricted to the token the
    rule above marked. The restriction IS the content — an unloaded token's
    capacity is real but irrelevant, and a decision that read it would be
    answering about a direction nothing is pushing.
    """
    return {
        "name": "ecp_read_loaded_compensation_capacity",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "batch": True,
        "match": [
            ["body", "has_opaque_embodied_actuator_affordance", "affordance"],
        ],
        "where": And(
            declared("affordance", "bearing_load"),
            declared("affordance", "plastic_compensation_capacity_units"),
            Not(declared("affordance", "loaded_compensation_capacity_units")),
        ),
        "effects": [
            ["set_attr", "affordance", "loaded_compensation_capacity_units",
             T(P0("affordance", "plastic_compensation_capacity_units"))],
        ],
    }


def loaded_alignment_rule():
    """Structural authority AGAINST THE LOAD THAT IS THERE.

    `structural_alignment_authority_units` is a CAPABILITY: it says this token
    is near its stop, which is true whether or not anything is pushing. This
    says the load is going INTO that stop, which is the case where the stop is
    actually a reaction path.

    Both are kept, because they answer different questions and collapsing them
    would lose one. `elb_settle_effective_authority_over_reaction_paths` still
    reads the capability — pointing it at this reading is the next rung and
    needs the settle gate re-measured, so it is NOT done here.
    """
    return {
        "name": "ecp_read_loaded_structural_alignment",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "batch": True,
        "match": [
            ["body", "has_opaque_embodied_actuator_affordance", "affordance"],
        ],
        "where": And(
            declared("affordance", "bearing_load"),
            declared("affordance", "structural_alignment_authority_units"),
            Not(declared("affordance",
                         "loaded_structural_alignment_authority_units")),
        ),
        "effects": [
            ["set_attr", "affordance",
             "loaded_structural_alignment_authority_units",
             T(P0("affordance", "structural_alignment_authority_units"))],
        ],
    }


def manifest() -> dict:
    return {
        "id": "effector_compensation",
        "version": "1.2.0",
        # NOTHING. This seed reads only what the boundary publishes on an
        # affordance, and `effector_limbs` is its CONSUMER, not its dependency
        # -- it declares `depends_on: [effector_compensation]` for the reason
        # recorded there. Declaring the arrow the other way round was measured
        # to break the settle silently; see that manifest's comment.
        "depends_on": [],
        "productions": [],
        # ORDER IS LOAD-BEARING, and this seed learned that the hard way one
        # rung ago: registration order decides producer-vs-consumer inside one
        # fixpoint, and a fire-once latch makes losing that race silent. The
        # mark is registered BEFORE the two readings that guard on it. Verified
        # by measurement in the gate, not by this comment.
        "rules": [
            infer_structural_alignment_rule(),
            read_plastic_compensation_rule(),
            mark_load_bearing_rule(),
            loaded_compensation_rule(),
            loaded_alignment_rule(),
        ],
    }


def main() -> int:
    out = ROOT / "seeds" / "effector_compensation.json"
    out.write_text(json.dumps(manifest(), indent=1) + "\n", encoding="utf-8")
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

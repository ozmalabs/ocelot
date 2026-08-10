#!/usr/bin/env python3
"""Generate the effector authority axis — the desk gate's decision layer.

WHAT THIS IS NOT. It is not a contact reflex. Nothing here reads "was there a
collision"; the prereg calls a contact reflex, a fall handler or a smash mode
appearing in the implementation a design failure rather than a feature. What is
read is whether the DEMAND on an effector exceeded the authority that effector
is declared to have -- a quantity that is just as meaningful with no obstacle in
the world, and which the desk merely happens to make large.

THE AXIS FORM IS THE F-16's, AND IT WAS EARNED THERE THE HARD WAY. Scoring an
axis by tracking error made SURRENDERING the axis dominate: measured at n=100
nominal plus a 10-seed pre-flight, `1 - error/band` read -9 on a healthy
aircraft with its full pitch envelope untouched, because the F-16's honest
steady-state altitude offset is ~300 ft = 3 band units, and a corner that gave
up altitude (flat 0.0) beat the status quo in ordinary cruise. The correction:

    "A tracking error out of band is not an unachievable objective;
     a demand past the loop's own declared authority is."

so every axis here is read against a DECLARED authority the body already flies
by (`specified_maximum_position_change_per_action`, published on each actuator
affordance) and introduces no constant of its own.

INTEGER, NOT A RATIO. The F-16 divides because it is a float-native airframe.
This tree is integer-native and in-frame quantities are integers, so the axis is
the SHORTFALL in declared units rather than a ratio. Nothing is lost: Pareto
dominance compares axis-by-axis and never across axes, so the axes never need a
common scale. That is a consequence of refusing to scalarise, not a workaround.

TWO STAGES, AND THE GOAL ENTERS ONLY THE SECOND -- also the F-16's shape:

  1. `cp_recognize_relational_dominance` (existing, unmodified) prunes the
     frontier over all axes. GOAL-BLIND.
  2. `eaa_choose_priority_axis_from_goal` picks WHICH axis ordinal the current
     goal prioritises, and selection reads that ONE axis off the survivors.

`_priority_value_from_axes` in the F-16 seed states the discipline exactly: "a
single declared axis's own reading, never a weighted sum, never folded into
dominance." So gate 4 (no scalar) holds by construction -- there is nowhere in
this file where two axes are combined into one number.

WHY THE SAME RULES GIVE OPPOSITE ANSWERS. The goal declares which effector group
it is INSTRUMENTALLY about (`goal_instrument_group_ordinal`). Turning is about
the torso; reaching through is about the arm. That selects the priority axis, and
the identical candidate set then selects differently. No case in this file names
a desk, an arm, or a collision.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Axis ordinals. Every axis is SIGNED so that HIGHER IS ALWAYS BETTER, which is
# what `ParetoDominates` assumes via `signed_value_key`.
AXIS_TURN = 0        # -shortfall of the torso group's demanded displacement
AXIS_REACH = 1       # -shortfall of the arm group's demanded displacement
AXIS_DAMAGE = 2      # -peak contact load
AXIS_POSTURE = 3     # +retained base height (postural authority)
DIMENSION_COUNT = 4


def V(name): return {"type": "Var", "name": name}
def L(v): return {"type": "Lit", "value": v}
def A(n, k): return {"type": "Attr", "node": V(n), "key": k}
def P0(n, k): return {"type": "Plus", "items": [A(n, k), L(0)]}
def Eq(a, b): return {"type": "Eq", "a": a, "b": b}
def Gt(a, b): return {"type": "Gt", "a": a, "b": b}
def And(*i): return {"type": "And", "items": list(i)}
def Or(*i): return {"type": "Or", "items": list(i)}
def Not(a): return {"type": "Not", "arg": a}
def If(c, t, o): return {"type": "IfThenElse", "cond": c, "then": t, "other": o}
def Neighbours(n, e): return {"type": "Neighbours", "node": V(n), "edge_type": e}
def Count(s): return {"type": "Count", "source": s}
def Argmin(source, var, value, default): return {
    "type": "Argmin", "source": source, "var_name": var,
    "value": value, "default": default}
def Neg(a): return {"type": "Neg", "arg": a}
def T(t): return {"__term__": t}


def declared(name, key):
    """PRESENT, not present-and-zero. An authority nobody declared must not read
    as an authority of zero -- that would make every demand infinitely
    unachievable and hand the frontier to whichever candidate surrenders most."""
    return Not(Eq(A(name, key), L(None)))


def choose_priority_axis_rule():
    """WHICH AXIS THIS GOAL PRIORITISES — the only place the goal enters.

    Derived from the goal's own declaration of what it is instrumentally about,
    never from its name. A goal whose instrument is the arm group prioritises
    the reach axis; anything else prioritises the turn axis. This never enters
    dominance -- it only selects, later, among whatever relational dominance
    already left on the frontier (the F-16's
    `f16_choose_regime_situational_priority` states the same separation).
    """
    return {
        "name": "eaa_choose_priority_axis_from_goal",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": "The situation's declared priority axis, read off the goal's "
        "own instrument declaration. Never folded into dominance.",
        "match": [
            ["agent", "has_effector_authority_profile", "profile"],
            ["profile", "deliberates_for_goal", "goal"],
        ],
        "where": And(
            declared("goal", "goal_instrument_group_ordinal"),
            declared("profile", "arm_group_ordinal"),
            Not(declared("profile", "priority_axis_ordinal")),
        ),
        "effects": [
            ["set_attr", "profile", "priority_axis_ordinal", T(If(
                Eq(A("goal", "goal_instrument_group_ordinal"),
                   A("profile", "arm_group_ordinal")),
                L(AXIS_REACH),
                L(AXIS_TURN),
            ))],
        ],
    }


def read_priority_value_rule():
    """Read the ALREADY-DECLARED priority axis back off each candidate's own
    values. One axis's own reading -- never a weighted sum, never folded into
    dominance (`_priority_value_from_axes`, F-16 seed)."""
    value_of = Argmin(
        Neighbours("candidate", "has_pareto_value"), "pv",
        If(Eq(P0("pv", "dimension_ordinal"),
              P0("profile", "priority_axis_ordinal")),
           L(0), L(1)),
        L(None),
    )
    return {
        "name": "eaa_read_priority_axis_value_off_candidate",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "batch": True,
        "comment": "A single declared axis's own reading on this candidate.",
        "match": [
            ["agent", "has_effector_authority_profile", "profile"],
            ["profile", "has_pareto_candidate", "candidate"],
        ],
        "where": And(
            declared("profile", "priority_axis_ordinal"),
            Not(declared("candidate", "priority_axis_value")),
        ),
        "effects": [
            ["set_attr", "candidate", "priority_axis_value", T(
                {"type": "Attr", "node": value_of, "key": "signed_value"}
            )],
        ],
    }


def adopt_regime_rule():
    """Adopt the surviving candidate that reads best on the priority axis.

    Scoped to the NON-DOMINATED frontier: dominance has already run, goal-blind,
    and this only chooses among what it left. Argmin over the negated value, so
    the best reading on the one declared axis wins.
    """
    # ELIGIBILITY IS A PRESENCE TEST, NOT A COALESCED ZERO. Both attributes
    # below would read as 0 if absent, and 0 is the ELIGIBLE value for each --
    # so a candidate dominance had not yet judged, or whose priority axis had
    # not yet been read, would silently compete and could win. That is the same
    # ordering hazard that let an unmeasured trial be booked as a failed one
    # (`ed_learn_capability_from_causally_closed_receipt`, fixed 2026-08-07).
    # Requiring both PRESENT means an unevaluated candidate is excluded rather
    # than assumed fine.
    eligible = And(
        declared("c", "dominated"),
        declared("c", "priority_axis_value"),
        Eq(P0("c", "dominated"), L(0)),
    )
    best = Argmin(
        Neighbours("profile", "has_pareto_candidate"), "c",
        If(eligible, Neg(P0("c", "priority_axis_value")), L(1000000)),
        L(None),
    )
    return {
        "name": "eaa_adopt_authority_regime_on_priority_axis",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": "Select among the surviving frontier by the one axis the "
        "goal declared. The regime's own authority allocation is then what the "
        "body is flown by until the condition that chose it changes.",
        "match": [
            ["agent", "has_effector_authority_profile", "profile"],
        ],
        "where": And(
            declared("profile", "priority_axis_ordinal"),
            Gt(Count(Neighbours("profile", "has_pareto_candidate")), L(0)),
            Not(declared("profile", "adopted_regime")),
            Not(Eq(best, L(None))),
        ),
        # `add_edge` takes a bound VAR NAME, never a computed Term, so the edge
        # is bound by a separate rule below rather than smuggled in here.
        "effects": [
            ["set_attr", "profile", "adopted_regime", T(
                {"type": "Attr", "node": best, "key": "identity"}
            )],
            ["set_attr", "profile", "adopted_arm_authority_units", T(
                {"type": "Attr", "node": best, "key": "arm_authority_units"}
            )],
        ],
    }


def bind_adopted_candidate_rule():
    """Bind the edge to whichever candidate the adoption named, by its own
    identity. Separate from the adoption because `add_edge` needs a bound var."""
    return {
        "name": "eaa_bind_adopted_authority_candidate",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "batch": True,
        "match": [
            ["agent", "has_effector_authority_profile", "profile"],
            ["profile", "has_pareto_candidate", "candidate"],
        ],
        "where": And(
            declared("profile", "adopted_regime"),
            Eq(A("candidate", "identity"), A("profile", "adopted_regime")),
            Eq(Count(Neighbours("profile", "adopted_authority_candidate")), L(0)),
        ),
        "effects": [
            ["add_edge", "profile", "adopted_authority_candidate", "candidate"],
        ],
    }


def manifest() -> dict:
    return {
        "id": "effector_authority_axis",
        "version": "1.0.0",
        "depends_on": ["cognitive_pareto"],
        "productions": [
            {"provenance": "seed:effector_authority_axis:profile-1",
             "src": {"type": "Agent", "var": "s"},
             "edge_type": "has_effector_authority_profile",
             "tgt": {"type": "ParetoProfile", "var": "t"}},
            {"provenance": "seed:effector_authority_axis:goal-1",
             "src": {"type": "ParetoProfile", "var": "s"},
             "edge_type": "deliberates_for_goal",
             "tgt": {"type": "Goal", "var": "t"}},
            {"provenance": "seed:effector_authority_axis:adopted-1",
             "src": {"type": "ParetoProfile", "var": "s"},
             "edge_type": "adopted_authority_candidate",
             "tgt": {"type": "ParetoCandidate", "var": "t"}},
        ],
        "rules": [
            choose_priority_axis_rule(),
            read_priority_value_rule(),
            adopt_regime_rule(),
            bind_adopted_candidate_rule(),
        ],
    }


def main() -> int:
    out = ROOT / "seeds" / "effector_authority_axis.json"
    out.write_text(json.dumps(manifest(), indent=1) + "\n", encoding="utf-8")
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

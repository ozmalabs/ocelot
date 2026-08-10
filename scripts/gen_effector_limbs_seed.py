#!/usr/bin/env python3
"""Derive limbs from `carried_by`, and make authority INHERIT down them.

THE PHYSICAL FACT THIS ENCODES, measured on the desk trials (2026-08-07): in
every condition the elbow deflected 0.000 rad while the shoulder deflected
0.726. The forearm is a rigid pendulum carried by the shoulder, so yielding the
hand is something only the SHOULDER can do — the hand's own actuator is
irrelevant to whether the hand gives.

  AN EFFECTOR CANNOT HAVE MORE EFFECTIVE AUTHORITY THAN THE THING CARRYING IT.

That is the whole content. A limp shoulder means the forearm's own stiffness
cannot hold the hand in place, however much the forearm declares. So effective
authority is `min(own declared, parent's effective)` — releasing a parent
releases everything distal to it, and releasing a child does nothing about the
parent carrying it. A flat peer model cannot state either half.

NOTHING HERE NAMES A LIMB. No rule mentions an arm, a leg, a hand or a joint. A
limb is whatever maximal chain the `carried_by` edges happen to form; the host
publishes which link carries which, and the shape falls out.

  MEASURED 2026-08-07, AFTER THE CARRIAGE FIX: THREE trees on the MJCF
  humanoid, depths 0..8, with 42 of 43 tokens members (the 43rd is the tonic
  option, which names no joint).

  THIS SUPERSEDES THIS FILE'S OWN EARLIER READING of "seven chains of depth
  <= 2, because co-located multi-DOF joints (abdomen x/y/z, hip x/y/z) are
  genuinely NOT carried by one another and correctly do not nest." That was an
  ARTEFACT and the reason given for it was wrong. Carriage was being severed by
  rigidly WELDED intermediate links, not by co-location: the old code mapped a
  joint's parent LINK straight to a channel and gave up when that link was not
  itself actuated, and 12 of this body's 33 links are FIXED. The tell was that
  it was INCONSISTENT -- abdomen_z carried abdomen_y (adjacent, no weld between)
  while abdomen_y did not carry abdomen_x (weld between), which co-location
  cannot explain. Serial revolute joints carry one another whether or not a weld
  sits between them, and they now nest.

  Whether a co-located 3-DOF cluster SHOULD nest for authority purposes is a
  modelling question this does not settle -- releasing one axis of a ball joint
  reorients the others rather than translating them. What is settled is that the
  old answer was decided by where the asset happened to put a weld.

Depth is the fixpoint's own ordering: a member is admitted only once its carrier
is a member, and inherits authority only once its carrier's effective authority
is DECLARED. So the `run_rules` fixpoint walks each chain root-first without any
iteration in Python.
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
def N(n, e): return {"type": "Neighbours", "node": V(n), "edge_type": e}
def IN(n, e): return {"type": "InNeighbours", "node": V(n), "edge_type": e}
def Count(s): return {"type": "Count", "source": s}
def NodesOfType(t): return {"type": "NodesOfType", "node_type": t}
def Exists(src, var, pred): return {"type": "Exists", "source": src, "var_name": var, "predicate": pred}
def Filter(src, var, pred): return {"type": "Filter", "source": src, "var_name": var, "predicate": pred}
def Argmin(src, var, val, default): return {"type": "Argmin", "source": src, "var_name": var, "value": val, "default": default}
def Min(*i): return {"type": "Min", "items": list(i)}
def Max(*i): return {"type": "Max", "items": list(i)}
def Plus(*i): return {"type": "Plus", "items": list(i)}
def T(t): return {"__term__": t}


def declared(n, k):
    """PRESENT, not present-and-zero. An undeclared authority must not read as
    an authority of zero: that would silently release every effector distal to
    it, which is the most consequential possible misreading of a blind channel."""
    return Not(Eq(A(n, k), L(None)))


def open_limb_at_root_rule():
    """A carriage ROOT opens a limb: it carries something, and nothing carries
    it. `carried_by` points child -> parent, so a root has no OUTGOING edge and
    at least one INCOMING one."""
    return {
        "name": "elb_open_limb_at_carriage_root",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        # NOT batched: a carriage root has one affordance token PER COMMAND
        # DIRECTION, and every one of them is a root. Batched, they all pass the
        # uniqueness guard against the same pre-state and each opens its own
        # limb -- 14 limbs for 7 chains, measured. Sequencing lets the first
        # token's limb exist before the second is judged.
        "batch": False,
        "comment": "A maximal carriage chain, opened once per root GROUP. "
        "Nothing here decides what a limb is called or which joints are in one.",
        "match": [
            ["body", "has_opaque_embodied_actuator_affordance", "affordance"],
        ],
        "where": And(
            Eq(Count(N("affordance", "carried_by")), L(0)),
            Gt(Count(IN("affordance", "carried_by")), L(0)),
            Eq(Count(IN("affordance", "has_limb_member")), L(0)),
            # One limb per chain, not one per command direction.
            Not(Exists(NodesOfType("EmbodiedLimb"), "known",
                       Eq(P0("known", "root_group_ordinal"),
                          P0("affordance", "opaque_group_ordinal")))),
        ),
        "effects": [
            ["add_node", "limb", "EmbodiedLimb", {
                "root_group_ordinal": T(P0("affordance", "opaque_group_ordinal")),
                "grounded": 1, "integer_native": 1, "output_authority": 0,
            }],
            ["add_edge", "limb", "has_limb_member", "affordance"],
            ["set_attr", "affordance", "limb_chain_depth", 0],
        ],
    }


def extend_limb_rule():
    """Whatever a member carries is in the same limb, one step deeper."""
    return {
        "name": "elb_extend_limb_to_carried_member",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "batch": True,
        "match": [
            ["limb", "has_limb_member", "carrier"],
            ["child", "carried_by", "carrier"],
        ],
        "where": And(
            declared("carrier", "limb_chain_depth"),
            Eq(Count(IN("child", "has_limb_member")), L(0)),
        ),
        "effects": [
            ["add_edge", "limb", "has_limb_member", "child"],
            ["set_attr", "child", "limb_chain_depth", T(Plus(
                P0("carrier", "limb_chain_depth"), L(1)
            ))],
        ],
    }


def seed_root_authority_rule():
    """A root's effective authority is simply its own declared authority —
    nothing carries it, so nothing can cap it.

    THE CURRENCY IS `declared_joint_force_units` (v1.2.0). It used to be
    `specified_maximum_position_change_per_action`, which is `abs(twitch[1])`
    quantised and therefore 1000 for EVERY actuator by construction. With the
    declared authority equal everywhere, `min(own, carrier)` reduced to
    `min(x, x)` and THE WHOLE CHAIN WAS VACUOUS -- measured: every member of the
    live body settled to the same 1000, in every pose, whatever the alignment
    said. The declared force is the body's only per-actuator authority
    declaration (100 / 200 / 400 / 600 on this asset), so it is the only thing
    `min` down a chain can mean.
    """
    return {
        "name": "elb_seed_root_effective_authority",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "batch": True,
        "match": [
            ["limb", "has_limb_member", "affordance"],
        ],
        "where": And(
            Eq(Count(N("affordance", "carried_by")), L(0)),
            declared("affordance", "declared_joint_force_units"),
            Not(declared("affordance", "effective_authority_units")),
        ),
        "effects": [
            ["set_attr", "affordance", "effective_authority_units", T(
                P0("affordance", "declared_joint_force_units")
            )],
        ],
    }


def carrier_path_authority_rule():
    """The CARRIER path: what this effector can do reacting against its carrier.

    This is the free-space case and it is a real cap -- a limp shoulder means the
    forearm cannot position the hand, because there is nothing else to push
    against. It is NOT the whole story, and writing it as the whole story was
    wrong: see `settle_effective_authority_rule`.
    """
    return {
        "name": "elb_carrier_path_authority",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "batch": True,
        "match": [["child", "carried_by", "carrier"]],
        "where": And(
            declared("carrier", "effective_authority_units"),
            declared("child", "declared_joint_force_units"),
            Not(declared("child", "carrier_path_authority_units")),
        ),
        "effects": [
            ["set_attr", "child", "carrier_path_authority_units", T(Min(
                P0("child", "declared_joint_force_units"),
                P0("carrier", "effective_authority_units"),
            ))],
        ],
    }


def settle_effective_authority_rule():
    """EFFECTIVE AUTHORITY IS THE BEST AVAILABLE REACTION PATH — a MAXIMUM over
    paths, not a minimum down the chain.

    THE CORRECTION THIS ENCODES (2026-08-07): an effector CAN exceed its
    carrier's authority, but only where the load does not route through the
    carrier. Three such paths, all graph-visible today:

      * OPPOSED EFFECTOR -- the antagonist token of its own joint group. The two
        affordance tokens per `opaque_group_ordinal` are the +/- command
        directions on one joint; co-contraction stiffens the joint without
        borrowing anything from the carrier.
      * EXTERNAL CONTACT -- a grounded support contact closes the kinematic
        chain, so the reaction goes through the world. A HAND ON A DESK IS A
        CLOSED CHAIN: the desk is the reaction surface, and a limp shoulder does
        not cap what the hand can press with. The first version of this rule
        would have under-estimated authority in exactly the case the desk gate
        exists to test -- it stated a law that failed in its own headline case.
      * ALIGNMENT / BRACING -- a limb positioned so the load passes through the
        linkage rather than across the actuator. A locked knee carries weight
        through structure, not the quadriceps; a straight arm pushed axially
        loads bone, not the elbow flexor. Formally the actuator only resists the
        MOMENT the load makes about its axis, so as the moment arm goes to zero
        the actuator is unloaded and authority is bounded by structure instead.

    THE THIRD PATH IS NOW LIVE, AND IT READS THE **LOADED** ALIGNMENT (v1.2.0).
    `effector_compensation` infers alignment from published travel, and it
    publishes TWO readings that must not be confused:

      * `structural_alignment_authority_units` -- a CAPABILITY. This token is
        near its stop. True whether or not anything is pushing on it.
      * `loaded_structural_alignment_authority_units` -- the load is going INTO
        that stop, so the stop is ACTUALLY A REACTION PATH right now.

    This rule reads the SECOND, because a reaction path you are not reacting
    against is not a path. **A TOKEN AT ITS STOP WITH NO LOAD ON IT IS BRACED
    AGAINST NOTHING**, and granting it the full declared authority would repeat
    this rule's own original error one level up -- scoring a STATE as though it
    were a reaction. Measured on the standing body: a joint's two tokens are
    loaded oppositely, and the same joint's load flips sides between moments, so
    the capability reading alone cannot say which of the two is bearing.

    The abstention discipline is UNCHANGED and still load-bearing: where the
    loaded reading is absent -- nothing pushing, or the load channel dark -- this
    path contributes nothing rather than defaulting. An unmeasured alignment must
    not silently read as zero (that would wrongly cap a braced limb) NOR as
    unbounded (that would wrongly free an unbraced one).
    """
    opposed_engaged = Exists(
        IN("group_peer", "has_opaque_embodied_actuator_affordance"), "ignored",
        L(True),
    )
    return {
        "name": "elb_settle_effective_authority_over_reaction_paths",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "batch": True,
        "comment": "Max over reaction paths: carrier, opposed effector, "
        "grounded contact, structural alignment. The carrier cap binds only "
        "when the carrier is the ONLY path.",
        "match": [
            ["limb", "has_limb_member", "child"],
            ["child", "carried_by", "carrier"],
        ],
        "where": And(
            declared("child", "carrier_path_authority_units"),
            declared("child", "declared_joint_force_units"),
            Not(declared("child", "effective_authority_units")),
        ),
        "effects": [
            ["set_attr", "child", "effective_authority_units", T(Max(
                # always available: react against the carrier
                P0("child", "carrier_path_authority_units"),
                # opposed effector engaged -> own declared authority, uncapped
                {"type": "IfThenElse",
                 "cond": Gt(P0("child", "opposed_effector_engaged"), L(0)),
                 "then": P0("child", "declared_joint_force_units"),
                 "other": L(0)},
                # grounded contact closes the chain -> own declared, uncapped
                {"type": "IfThenElse",
                 "cond": Gt(P0("child", "grounded_contact_count"), L(0)),
                 "then": P0("child", "declared_joint_force_units"),
                 "other": L(0)},
                # alignment/bracing: the LOADED reading, and only where the load
                # is actually going into the stop. Braced against nothing is not
                # a reaction path.
                {"type": "IfThenElse",
                 "cond": declared(
                     "child", "loaded_structural_alignment_authority_units"),
                 "then": P0(
                     "child", "loaded_structural_alignment_authority_units"),
                 "other": L(0)},
            ))],
        ],
    }


def retire_duplicate_limb_rule():
    """One limb per carriage chain — duplicates retired, not prevented.

    A root joint has one affordance token PER COMMAND DIRECTION and every one of
    them is a carriage root, so the mint rule fires once per token: 14 limbs for
    7 chains, measured. Guarding the mint on "no limb with this root group
    exists yet" did NOT work even un-batched, so rather than keep guessing at
    same-pass visibility this uses the RETRACTION pattern that is already proven
    in this tree (`retire_duplicate_gap`, gap_awareness v1.2.0): let them mint,
    then keep exactly one.

    Batch-safe with no node ids: the survivor is `Argmin` over the same-root
    limbs, which returns exactly one element from a fixed snapshot within a
    pass, and a limb is deleted iff it is not identity-`Eq` to that survivor
    (`Eq` compares `Value::Node` by id). Deleting the duplicate takes its own
    `has_limb_member` edges with it and leaves the survivor's intact.
    """
    same_root = Filter(
        NodesOfType("EmbodiedLimb"), "peer",
        Eq(P0("peer", "root_group_ordinal"), P0("limb", "root_group_ordinal")),
    )
    survivor = Argmin(same_root, "chosen", L(0), L(None))
    return {
        "name": "elb_retire_duplicate_limb_for_one_chain",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": "A carriage chain is one limb however many command "
        "directions its root exposes.",
        "match": [["limb", "has_limb_member", "member"]],
        "where": And(
            declared("limb", "root_group_ordinal"),
            Not(Eq(survivor, L(None))),
            Not(Eq(V("limb"), survivor)),
        ),
        "effects": [["del_node", "limb"]],
    }

def manifest() -> dict:
    return {
        "id": "effector_limbs",
        "version": "1.3.0",
        # A CONSUMER DEPENDS ON ITS PRODUCER, and `boot_core.boot` resolves
        # `depends_on` topologically, so this list IS rule order.
        # `settle_effective_authority_rule` READS
        # `structural_alignment_authority_units`, which `effector_compensation`
        # declares. MEASURED 2026-08-07: with the arrow the other way round, the
        # whole limb chain (open -> extend -> seed root -> carrier path ->
        # settle) completes in the first pass, before the compensation rules run
        # at all -- and settle latches on `Not(declared(effective_authority_
        # units))`, so the alignment arrives one pass too late and is silently
        # never read. A braced child read 50 instead of 1000 with the correct
        # alignment sitting on the node beside it.
        #
        # THE GENERAL FORM: a rule that reads an attribute produced outside its
        # seed's dependency closure is an ordering bug, and a fire-once latch
        # makes it a SILENT one. The value is present, correct, and ignored.
        "depends_on": ["effector_compensation"],
        "productions": [
            {"provenance": "seed:effector_limbs:member-1",
             "src": {"type": "EmbodiedLimb", "var": "s"},
             "edge_type": "has_limb_member",
             "tgt": {"type": "EmbodiedOpaqueActuatorAffordance", "var": "t"}},
            {"provenance": "seed:effector_limbs:carried-1",
             "src": {"type": "EmbodiedOpaqueActuatorAffordance", "var": "s"},
             "edge_type": "carried_by",
             "tgt": {"type": "EmbodiedOpaqueActuatorAffordance", "var": "t"}},
        ],
        "rules": [
            open_limb_at_root_rule(),
            retire_duplicate_limb_rule(),
            extend_limb_rule(),
            seed_root_authority_rule(),
            carrier_path_authority_rule(),
            settle_effective_authority_rule(),
        ],
    }


def main() -> int:
    out = ROOT / "seeds" / "effector_limbs.json"
    out.write_text(json.dumps(manifest(), indent=1) + "\n", encoding="utf-8")
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

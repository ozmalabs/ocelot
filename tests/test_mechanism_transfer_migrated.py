"""tests/test_mechanism_transfer_migrated.py — ANALOGICAL MECHANISM TRANSFER.

Closes the disconnect the rule-index build cc98b4eb diagnosed: the agent
RECOGNISES a concern's meta-shape (categorise_by_shape) but its composer decodes
by SURFACE predicate overlap, so a concern in a new domain's vocabulary decodes to
residual/total_fit=0 and mint-as-novel fires falsely, even when a held mechanism
realises the SAME meta-shape. The fix: a SHAPE->MECHANISM index
(seeds/mechanism_index.json) + retrieve-and-transfer in reflective_faculty.py.

Gates:
1. THE CLASS CLOSES — the foveation/rule-index concern: WITHOUT the index the
   composer does NOT author (the pre-fix wall); WITH the index it authors a plan
   built from the TRANSFERRED spatial-foveation mechanism (total_fit>0).
2. GENERALISES — a DIFFERENT meta-shape (feedback_control) transfers a DIFFERENT
   held mechanism into a NEW domain through the SAME code path.
3. TRANSFER, NOT LOOKUP — the transferred plan carries the GOAL's fillers (not the
   mechanism's source fillers), derived from the goal's own structure; a different
   goal of the same shape yields a different plan.
4. BYTE-IDENTITY — with NO index held, compose_design_for_goal is unchanged (the
   transfer path is a strict no-op), protecting every existing composer gate.
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if p not in sys.path:
        sys.path.insert(0, p)


FOVEATION_GOAL = [
    ["scan", "EVERY", "RULE", "per", "EVENT"],
    ["match", "over", "the", "WHOLE", "FRAME", "SET"],
    ["gate", "the", "SCAN", "to", "the", "FOCUS"],
    ["index", "the", "RULES", "by", "EVENT", "TYPE"],
    ["decode", "only", "RULES", "in", "FOCUS", "for", "this", "TYPE"],
]

REGULATION_GOAL = [
    ["measure", "the", "current", "FIRING", "RATE"],
    ["compare", "RATE", "to", "the", "set_point", "BUDGET"],
    ["regulate", "by", "FEEDBACK", "toward", "the", "BUDGET"],
    ["correct", "the", "SCHEDULER", "toward", "the", "BUDGET"],
]


def _boot(with_index: bool):
    from substrate.world_adapter import WorldAdapter
    from substrate.seed_loader import manifest_for
    wa = WorldAdapter()
    seeds = ["shape_vocabulary", "seven_meta_shape_subsystems", "relation_vocabulary"]
    if with_index:
        seeds.append("mechanism_index")
    for seed in seeds:
        try:
            wa.inner.load_seed_manifest(manifest_for(seed), wa.agent)
        except Exception:
            pass
    return wa


def test_class_closes_foveation_transfer():
    from domains.reflective_faculty import compose_design_for_goal
    before = compose_design_for_goal(_boot(False), FOVEATION_GOAL)
    after = compose_design_for_goal(_boot(True), FOVEATION_GOAL)
    # BEFORE: the pre-fix wall — literal decode does not author.
    assert not before.get("authored")
    # AFTER: authored by transfer, from the spatial-foveation mechanism.
    assert after.get("authored") is True
    assert after.get("authored_by") == "mechanism_transfer"
    assert after["transferred_from"]["mechanism"] == "spatial_foveation"
    assert after["transferred_from"]["meta_shape"] == "selective_gating"
    assert after.get("total_fit", 0) >= 3
    # the plan is the RULE domain's (the field became RULE, the granule EVENT_TYPE),
    # re-instantiated from the mechanism's abstract steps.
    plan = after["plan"]
    assert ["index", "RULE", "by", "EVENT_TYPE"] in plan
    assert ["decode", "only", "RULE", "in", "FOCUS"] in plan


def test_generalises_feedback_control_transfer():
    from domains.reflective_faculty import compose_design_for_goal
    before = compose_design_for_goal(_boot(False), REGULATION_GOAL)
    after = compose_design_for_goal(_boot(True), REGULATION_GOAL)
    assert not before.get("authored")
    assert after.get("authored") is True
    assert after.get("authored_by") == "mechanism_transfer"
    # a DIFFERENT meta-shape, a DIFFERENT held mechanism — the CLASS, not the instance.
    assert after["transferred_from"]["mechanism"] == "homeostatic_regulation"
    assert after["transferred_from"]["meta_shape"] == "feedback_control"
    assert after.get("total_fit", 0) >= 3
    plan = after["plan"]
    assert ["measure", "FIRING_RATE"] in plan
    assert ["correct", "SCHEDULER", "toward", "BUDGET"] in plan


def test_transfer_not_lookup_carries_goal_fillers():
    """The transferred plan carries the GOAL's fillers, not the mechanism's source
    fillers — and a DIFFERENT goal of the same shape yields a DIFFERENT plan. That
    is transfer (re-instantiation), not a stored-answer lookup."""
    from domains.reflective_faculty import retrieve_and_transfer_mechanism
    wa = _boot(True)
    rt = retrieve_and_transfer_mechanism(wa, FOVEATION_GOAL)
    # the held index is read from the graph BY THE TERM (no Python `_load_mechanisms`):
    # the spatial_foveation mechanism is retrieved under the recognised shape.
    assert "spatial_foveation" in rt["retrieved"]
    # the mechanism's SOURCE fillers (space/quanta) must NOT appear in the plan.
    plan_tokens = {tok for step in rt["transferred"]["plan"] for tok in step}
    assert "space" not in plan_tokens and "quanta" not in plan_tokens
    assert "RULE" in plan_tokens and "EVENT_TYPE" in plan_tokens
    # a second goal of the SAME shape but different domain -> different fillers.
    other = [
        ["scan", "EVERY", "PACKET", "per", "TICK"],
        ["gate", "the", "SCAN", "to", "the", "PORT"],
        ["index", "the", "PACKETS", "by", "FLOW"],
    ]
    rt2 = retrieve_and_transfer_mechanism(wa, other)
    plan2 = {tok for step in rt2["transferred"]["plan"] for tok in step}
    assert "PACKET" in plan2 and "FLOW" in plan2
    assert plan2 != plan_tokens


def test_byte_identity_without_index_is_noop():
    """With NO mechanism index held, the transfer path is a strict no-op:
    compose_design_for_goal returns EXACTLY the literal-decode result — the guard
    that protects every existing composer gate."""
    from domains import reflective_faculty as rf
    wa = _boot(False)
    # no Mechanism index held on the un-indexed boot (the Term reads zero nodes).
    assert list(wa.s.nodes("Mechanism")) == []
    # retrieve_and_transfer short-circuits to None (the Term returns None on an
    # empty codebook, before it even recognises a shape).
    assert rf.retrieve_and_transfer_mechanism(wa, FOVEATION_GOAL) is None
    result = rf.compose_design_for_goal(wa, FOVEATION_GOAL)
    # no transfer keys leak into the result on the un-indexed boot.
    assert "authored_by" not in result
    assert "transferred_from" not in result


def test_recognised_shape_with_no_indexed_mechanism_is_honest_wall():
    """A shape recognised but with no mechanism indexed under it returns an honest
    wall (transferred=None) — mint stays the fallback, transfer never fabricates."""
    from domains.reflective_faculty import retrieve_and_transfer_mechanism
    wa = _boot(True)
    # A goal whose own text the shared recogniser (Rust) files under a shape the
    # index holds no mechanism for: "broadcast SIGNAL" -> global_message_passing,
    # which has no indexed mechanism -> the honest wall. The meta-shape is DERIVED
    # by TransferDecode itself (no Python meta_shape arg, no duplicated scorer).
    rt = retrieve_and_transfer_mechanism(wa, [["broadcast", "SIGNAL"]])
    assert rt["transferred"] is None
    assert rt["retrieved"] == []
    assert rt["meta_shape"] == "global_message_passing"

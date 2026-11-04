from __future__ import annotations

from dataclasses import replace

from evaluation.ousiometrics.worlds import (
    FactorProfile,
    SocialRepairWorld,
    ToolInterventionWorld,
    build_factorial_worlds,
    factorial_profiles,
    hidden_factor_record,
)


def test_factors_can_be_intervened_separately():
    baseline = FactorProfile(0.2, 0.0, 0.0, 0.0, 0.0)
    profiles = [baseline, replace(baseline, effect_capacity=0.8),
                replace(baseline, adverse_probability=0.8),
                replace(baseline, constraint_strength=0.8),
                replace(baseline, pleasantness_bias=0.3),
                replace(baseline, outcome_noise=0.2)]
    assert len({(p.effect_capacity, p.adverse_probability, p.constraint_strength,
                 p.pleasantness_bias, p.outcome_noise) for p in profiles}) == 6
    factorial = {(p.effect_capacity, p.adverse_probability, p.constraint_strength)
                 for p in factorial_profiles()}
    assert factorial == {(c, d, s) for c in (0.2, 0.8)
                         for d in (0.0, 0.8) for s in (0.0, 0.8)}


def test_factor_labels_not_agent_input():
    worlds = build_factorial_worlds(2807)
    forbidden = {"effect_capacity", "adverse_probability", "constraint_strength",
                 "pleasantness_bias", "outcome_noise", "novelty", "pds", "vad",
                 "hidden_factors", "correct_axis"}
    for family in worlds.values():
        for world in family:
            view = world.agent_view()
            assert forbidden.isdisjoint(view)
            payload = str(view).casefold()
            assert "effect_capacity" not in payload and "adverse_probability" not in payload
            assert forbidden.isdisjoint(world.to_agent if hasattr(world, "to_agent") else {})
            assert forbidden.issuperset(hidden_factor_record(world).keys())


def test_safe_unfamiliar_and_predictable_harm_exist():
    dangerous = ToolInterventionWorld(
        FactorProfile(0.8, 1.0, 0.8, 0.0, 0.0), seed=1,
        episode_id="predictable-harm", context_id="known-context")
    assert dangerous.agent_view()["available_actions"] == ["inspect", "arm"]
    dangerous.apply_action("arm")
    receipt = dangerous.apply_action("apply_large")
    assert receipt.adverse_consequence is True
    assert dangerous.verify_receipt(receipt)

    safe_unstructured = ToolInterventionWorld(
        FactorProfile(0.2, 0.0, 0.0, 0.0, 0.0, novelty=1.0), seed=99,
        episode_id="safe-unfamiliar", context_id="unseen-context-99")
    view = safe_unstructured.agent_view()
    assert view["available_actions"] == ["inspect", "arm", "apply_small", "apply_large"]
    assert view["object_id"].startswith("unseen-tool-")
    safe = safe_unstructured.apply_action("apply_small")
    assert safe.action_authorized is True and safe.adverse_consequence is False
    assert safe_unstructured.verify_receipt(safe)


def test_goal_not_frame_axis_function():
    low = FactorProfile(0.2, 0.0, 0.0, 0.0, 0.0)
    high = replace(low, effect_capacity=0.8, adverse_probability=0.8, constraint_strength=0.8)
    a = ToolInterventionWorld(low, seed=1234)
    b = ToolInterventionWorld(high, seed=1234)
    assert a.goal_target == b.goal_target
    assert a.agent_view()["task"] == b.agent_view()["task"]
    a_view = a.agent_view()
    assert "goal" not in a_view
    assert a_view["task"]["kind"] == "move_marker_to_target"


def test_receipt_matches_world():
    tool = ToolInterventionWorld(FactorProfile(0.5, 0.0, 0.0, 0.1, 0.0), seed=23)
    before = tool.agent_view()
    receipt = tool.apply_action("apply_small", source_epoch=3, model_epoch=2, frame_epoch=5)
    assert tool.verify_receipt(receipt)
    assert receipt.action == "apply_small"
    assert tuple(receipt.before) == (before["measured_state"]["position"],
                                    float(before["measured_state"]["armed"]))
    assert tuple(receipt.raw_coordinates) == tuple(receipt.to_agent()["coordinates"])
    assert all(-0.5 <= value <= 0.5 for value in receipt.raw_coordinates)
    forged = replace(receipt, action="apply_large")
    assert not tool.verify_receipt(forged)

    social = SocialRepairWorld(FactorProfile(0.8, 0.0, 0.0, 0.2, 0.0), seed=47)
    social_receipt = social.apply_action("fulfill")
    assert social.verify_receipt(social_receipt)
    assert social_receipt.family == "social_request_repair"

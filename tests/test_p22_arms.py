import pytest

from evaluation.process_mastery.p22_arms import configure_p22_arm
from substrate.boot_profiles import boot_cognition_on


@pytest.mark.parametrize("arm,curriculum,invention", [
    ("unchanged", False, False),
    ("adaptive_only", True, False),
    ("invention_only", False, True),
    ("full", True, True),
])
def test_p22_arm_switches_one_native_policy_closure_and_shared_budget(
        arm, curriculum, invention):
    agent = boot_cognition_on()
    try:
        configured = configure_p22_arm(agent, arm, budget_capacity=32.0)
        assert configured["arm"] == arm
        assert configured["shared_budget_count"] == 1
        assert configured["budget_remaining"] == 32.0
        expected = {
            "ProcessCurriculumPolicy": curriculum,
            "CurriculumLearningBridgePolicy": curriculum,
            "OpenProcessSearchPolicy": invention,
            "IndependentImprovementPolicy": invention,
            "OpenProcessAdoptionPolicy": invention,
        }
        assert {kind: state["enabled"]
                for kind, state in configured["policy_state"].items()} == expected
        assert len(agent.inner.neighbours(agent.agent, "has_thinking_budget")) == 1
    finally:
        agent.close()


def test_p22_arm_setup_rejects_unknown_arm_and_overbudget_capacity():
    agent = boot_cognition_on()
    try:
        with pytest.raises(ValueError, match="unknown P22 arm"):
            configure_p22_arm(agent, "adaptive-invention", budget_capacity=32.0)
        with pytest.raises(ValueError, match="exceeds native"):
            configure_p22_arm(agent, "unchanged", budget_capacity=1e9)
    finally:
        agent.close()

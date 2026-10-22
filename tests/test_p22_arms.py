import pytest

from evaluation.process_mastery.p22_arms import configure_p22_arm
from evaluation.process_mastery.native_process_execution import params_digest
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
        ancestor_portfolio_before = sorted(
            (str(node), agent.s.node(node)["attrs"].get("source_digest"),
             tuple(agent.s.node(node)["attrs"].get("params", ())))
            for node in agent.s.nodes("ProcessSchema")
            if agent.s.node(node)["attrs"].get("status") == "active")
        configured = configure_p22_arm(agent, arm, budget_capacity=32.0)
        assert configured["arm"] == arm
        assert configured["shared_budget_count"] == 1
        assert configured["budget_remaining"] == 32.0
        expected = {
            "ProcessSchemaPolicy": True,
            "SolverPolicy": True,
            "ProcessCurriculumPolicy": curriculum,
            "IndependentImprovementCurriculumBridgePolicy": curriculum,
            "CurriculumLearningBridgePolicy": False,
            "OpenProcessSearchPolicy": invention,
            "IndependentImprovementPolicy": invention,
            "OpenProcessAdoptionPolicy": invention,
        }
        assert {kind: state["enabled"]
                for kind, state in configured["policy_state"].items()} == expected
        assert len(agent.inner.neighbours(agent.agent, "has_thinking_budget")) == 1
        ancestor_portfolio_after = sorted(
            (str(node), agent.s.node(node)["attrs"].get("source_digest"),
             tuple(agent.s.node(node)["attrs"].get("params", ())))
            for node in agent.s.nodes("ProcessSchema")
            if agent.s.node(node)["attrs"].get("status") == "active")
        assert ancestor_portfolio_after == ancestor_portfolio_before
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


def test_unchanged_ancestor_solves_two_primitive_composition_control():
    agent = boot_cognition_on()
    try:
        configure_p22_arm(agent, "unchanged", budget_capacity=64.0)
        domain_name = "p22-ancestor-composition-control"
        domain = agent.s.add_node("ProcessDomain", {
            "name": domain_name, "kind": "permutation", "domain_kind": "permutation",
            "object_count": 4.0, "probes": [[0, 1, 2, 3]],
            "source_epoch": 0, "model_epoch": 0, "frame_epoch": 0,
            "probe_epoch": 0})
        agent.s.add_edge(agent.agent, "has_process_domain", domain, {})
        held = {"rot90": [3, 0, 1, 2], "flip_r": [2, 1, 0, 3]}
        for name, params in held.items():
            schema = agent.s.add_node("ProcessSchema", {
                "name": name, "kind": "permutation", "domain_kind": "permutation",
                "domain": domain_name, "params": params,
                "source_digest": params_digest(params), "cost": 1.0,
                "status": "active", "provenance": "world_affordance",
                "source_epoch": 0, "model_epoch": 0, "frame_epoch": 0})
            agent.s.add_edge(agent.agent, "has_process_schema", schema, {})
            agent.s.add_edge(domain, "has_held_process", schema, {})
        target = agent.inner.evaluate({"type": "ProcessCompose",
            "a": {"type": "Var", "name": "a"},
            "b": {"type": "Var", "name": "b"}},
            {"a": held["rot90"], "b": held["flip_r"]})
        goal = agent.inner.evaluate({"type": "ProcessApply",
            "p": {"type": "Var", "name": "p"},
            "state": {"type": "Var", "name": "state"}},
            {"p": target, "state": [0, 1, 2, 3]})
        task = agent.s.add_node("SolveTask", {
            "task_key": "p22:ancestor:two-primitive-composition",
            "domain": domain_name, "initial_state": [0, 1, 2, 3],
            "state": [0, 1, 2, 3], "object_count": 4.0, "goal": goal,
            "status": "stuck", "split": "training", "trace": [],
            "steps": 0, "moves": 0.0, "stuck_count": 1})
        agent.s.add_edge(agent.agent, "has_solve_task", task, {})
        agent.s.add_edge(task, "about_domain", domain, {})
        for _ in range(64):
            if agent.inner.run_rules(20_000) == 0:
                break
        assert agent.s.node(task)["attrs"]["status"] == "solved"
        assert agent.s.node(task)["attrs"]["steps"] == 2
        assert agent.s.nodes("OpenProcessCandidate") == []
    finally:
        agent.close()

"""Development-only four-arm P22 learner wiring diagnostic.

Runs all policy conditions on the same training worlds with isolated native
graphs. It never approves candidates, executes invented candidates in worlds,
or accepts validation/held-out draws. Outcomes are arm wiring diagnostics, not
an efficacy comparison.
"""
from __future__ import annotations

from evaluation.process_mastery.independent_worlds import (
    generate_d4_world_v2, generate_loopover_world_v2,
)
from evaluation.process_mastery.p22_arms import configure_p22_arm
from evaluation.process_mastery.native_process_execution import params_digest
from evaluation.process_mastery.native_process_execution import (
    attest_open_process_candidate,
)
from evaluation.process_mastery.p22_resource_accounting import (
    compare_resource_snapshots, snapshot_native_resources,
)
from substrate.boot_profiles import boot_cognition_on


_GENERATORS = {
    "d4": (generate_d4_world_v2, 4),
    "loopover": (generate_loopover_world_v2, 9),
}
_ARMS = ("unchanged", "adaptive_only", "invention_only", "full")


def _add_training_domain(agent, family: str, size: int, worlds: list[dict]):
    name = f"p22-development-{family}"
    first = worlds[0]
    domain = agent.s.add_node("ProcessDomain", {
        "name": name, "kind": "permutation", "domain_kind": "permutation",
        "object_count": float(size), "probes": [first["initial_state"]],
        "source_epoch": 0, "model_epoch": 0, "frame_epoch": 0,
        "probe_epoch": 0})
    agent.s.add_edge(agent.agent, "has_process_domain", domain, {})
    for process_name, params in sorted(first["held_processes"].items()):
        schema = agent.s.add_node("ProcessSchema", {
            "name": process_name, "kind": "permutation",
            "domain_kind": "permutation", "domain": name,
            "params": list(params), "source_digest": params_digest(list(params)),
            "cost": 1.0, "status": "active", "provenance": "world_affordance",
            "invariants": [], "source_epoch": 0, "model_epoch": 0,
            "frame_epoch": 0, "probe_epoch": 0, "source_probe_epoch": 0})
        agent.s.add_edge(agent.agent, "has_process_schema", schema, {})
        agent.s.add_edge(domain, "has_held_process", schema, {})
    return name, domain


def _add_task_inputs(agent, arm: str, domain_name: str, domain,
                     worlds: list[dict]) -> None:
    curriculum = arm in {"adaptive_only", "full"}
    for world in worlds:
        task_key = f"p22:{world['family']}:{world['draw']:04d}"
        evidence = agent.s.add_node("ProcessCurriculumEvidence", {
            "evidence_key": task_key, "source_kind": "registered_training_pool",
            "source_id": world["world_id"], "task_kind": "process_composition",
            "action_kind": "apply", "object_type": "Permutation",
            "feature_key": "permutation", "before_value": world["initial_state"],
            "domain": domain_name, "initial_state": world["initial_state"],
            "goal": world["goal_state"], "source_epoch": 0, "model_epoch": 0,
            "frame_epoch": 0, "status": "eligible", "split": "training",
            "expected_outcome": "unknown", "sealed_labels_present": False,
            "fixed_rank": 0.0, "random_rank": 0.0})
        agent.s.add_edge(agent.agent, "has_process_curriculum_evidence", evidence, {})
        if not curriculum:
            task = agent.s.add_node("SolveTask", {
                "task_key": task_key, "training_trial_key": world["world_id"],
                "domain": domain_name, "initial_state": world["initial_state"],
                "state": world["initial_state"], "goal": world["goal_state"],
                "object_count": float(len(world["initial_state"])),
                "status": "active", "trace": [], "steps": 0, "moves": 0.0,
                "stuck_count": 0, "split": "training"})
            agent.s.add_edge(agent.agent, "has_solve_task", task, {})
            agent.s.add_edge(task, "about_domain", domain, {})


def run_p22_four_arm_development(*, family: str,
                                 training_draws: tuple[int, ...],
                                 budget_capacity: float = 64.0,
                                 max_rule_rounds: int = 256) -> dict:
    """Run all four explicit conditions on a common, training-only v2 panel."""
    if family not in _GENERATORS:
        raise ValueError("unsupported P22 development family")
    if (not training_draws or len(training_draws) != len(set(training_draws))
            or any(isinstance(draw, bool) or not isinstance(draw, int)
                   or draw < 0 or draw >= 1000 for draw in training_draws)):
        raise ValueError("development requires unique registered training draws")
    if (isinstance(max_rule_rounds, bool) or not isinstance(max_rule_rounds, int)
            or max_rule_rounds < 1):
        raise ValueError("max_rule_rounds must be a positive integer")
    generator, size = _GENERATORS[family]
    worlds = [generator(split="train", draw=draw) for draw in training_draws]
    if any(len(world["initial_state"]) != size for world in worlds):
        raise ValueError("training worlds have inconsistent domain sizes")

    arms = {}
    for arm in _ARMS:
        agent = boot_cognition_on()
        try:
            configuration = configure_p22_arm(
                agent, arm, budget_capacity=budget_capacity)
            domain_name, domain = _add_training_domain(agent, family, size, worlds)
            curriculum_policy = agent.s.nodes("ProcessCurriculumPolicy")[0]
            agent.s.set_attr(curriculum_policy, "max_tasks", float(len(worlds)))
            _add_task_inputs(agent, arm, domain_name, domain, worlds)

            for _ in range(max_rule_rounds):
                fired = agent.inner.run_rules(20_000)
                pending = [candidate for candidate in agent.s.nodes("OpenProcessCandidate")
                    if agent.s.node(candidate)["attrs"].get(
                        "expression_digest") == "pending_native_expression_attestation"]
                for candidate in pending:
                    attest_open_process_candidate(agent, candidate)
                if fired == 0 and not pending:
                    break

            task_rows = []
            for world in worlds:
                task_key = f"p22:{world['family']}:{world['draw']:04d}"
                solve_tasks = [node for node in agent.s.nodes("SolveTask")
                    if agent.s.node(node)["attrs"].get("task_key") == task_key]
                curriculum_tasks = [node for node in agent.s.nodes("ProcessCurriculumTask")
                    if agent.s.node(node)["attrs"].get("task_key") == task_key]
                if len(solve_tasks) > 1 or len(curriculum_tasks) > 1:
                    raise RuntimeError("native arm duplicated a registered training task")
                solve_status = (agent.s.node(solve_tasks[0])["attrs"].get("status")
                                if solve_tasks else "not_dispatched")
                related_requests = ([request for request in
                    agent.s.nodes("OpenProcessSearchRequest")
                    if solve_tasks and agent.inner.neighbours(request,
                        "searches_task") == [solve_tasks[0]]])
                request_statuses = [agent.s.node(request)["attrs"].get("status")
                                    for request in related_requests]
                curriculum_status = (agent.s.node(curriculum_tasks[0])["attrs"].get("status")
                                     if curriculum_tasks else "not_selected")
                if solve_status == "solved":
                    terminal = True
                elif not (arm in {"invention_only", "full"}):
                    terminal = solve_status == "stuck"
                else:
                    terminal = solve_status == "stuck" and bool(request_statuses) and all(
                        status in {"proposal_recorded", "qualified_terminal", "denied",
                                   "global_attempt_ceiling"}
                        for status in request_statuses)
                if arm in {"adaptive_only", "full"}:
                    terminal = terminal and curriculum_status == "completed"
                task_rows.append({"world_id": world["world_id"],
                    "task_key": task_key, "split": "training",
                    "solve_status": solve_status,
                    "search_request_statuses": request_statuses,
                    "curriculum_status": curriculum_status,
                    "solved": solve_status == "solved",
                    "terminal": terminal})

            proposals = [{"candidate_id": str(candidate),
                "expression_digest": agent.s.node(candidate)["attrs"].get("expression_digest"),
                "status": agent.s.node(candidate)["attrs"].get("status"),
                "params": agent.s.node(candidate)["attrs"].get("params")}
                for candidate in agent.s.nodes("OpenProcessCandidate")]
            search_requests = [{"request_id": str(request),
                "status": agent.s.node(request)["attrs"].get("status"),
                "task_ids": [str(task) for task in agent.inner.neighbours(
                    request, "searches_task")]}
                for request in agent.s.nodes("OpenProcessSearchRequest")]
            curriculum_outcomes = [{"outcome_id": str(outcome),
                "status": agent.s.node(outcome)["attrs"].get("status"),
                "assessment": agent.s.node(outcome)["attrs"].get("assessment"),
                "task_key": agent.s.node(outcome)["attrs"].get("task_key")}
                for outcome in agent.s.nodes("ProcessCurriculumOutcome")]
            arms[arm] = {"configuration": configuration,
                "training_tasks": task_rows, "solved_count": sum(
                    row["solved"] for row in task_rows),
                "all_tasks_terminal": len(task_rows) == len(worlds) and
                    all(row["terminal"] for row in task_rows),
                "proposal_count": len(proposals), "proposals": proposals,
                "search_requests": search_requests,
                "curriculum_outcomes": curriculum_outcomes,
                "approval_count": len(agent.s.nodes("OpenProcessAdoptionApproval")),
                "world_receipt_count": len(agent.s.nodes("OpenProcessWorldReceipt")),
                "resource_snapshot": snapshot_native_resources(agent)}
        finally:
            agent.close()

    world_ids = [world["world_id"] for world in worlds]
    return {"status": "DEVELOPMENT_ONLY", "family": family,
        "split": "training", "training_world_ids": world_ids,
        "common_worlds": all(arms[arm]["training_tasks"] and
            [row["world_id"] for row in arms[arm]["training_tasks"]] == world_ids
            for arm in _ARMS),
        "all_arms_terminal": all(arms[arm]["all_tasks_terminal"] for arm in _ARMS),
        "arms": arms,
        "resource_comparison": compare_resource_snapshots(
            {arm: arms[arm]["resource_snapshot"] for arm in _ARMS}),
        "approvals_created": sum(arms[arm]["approval_count"] for arm in _ARMS),
        "world_receipts_created": sum(arms[arm]["world_receipt_count"] for arm in _ARMS),
        "efficacy_established": False}

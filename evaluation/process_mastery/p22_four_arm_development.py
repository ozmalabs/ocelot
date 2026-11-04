"""Development-only four-arm P22 learner wiring diagnostic.

Runs all policy conditions on the same training worlds with isolated native
graphs. It never approves candidates, executes invented candidates in worlds,
or accepts validation/held-out draws. Outcomes are arm wiring diagnostics, not
an efficacy comparison.
"""
from __future__ import annotations

import math
import resource
import sys
import time
from dataclasses import asdict

from evaluation.process_mastery.independent_worlds import (
    agent_view, generate_d4_world_v2, generate_loopover_world_v2,
)
from evaluation.process_mastery.p22_arms import configure_p22_arm
from evaluation.process_mastery.native_process_execution import params_digest
from evaluation.process_mastery.native_process_execution import (
    attest_open_process_candidate,
)
from evaluation.process_mastery.checkpoint_world_adapter import (
    capture_held_process_checkpoint, score_unapproved_candidate_validation_panel,
)
from evaluation.process_mastery.p22_resource_accounting import (
    NativeRuleWorkCapture, compare_resource_snapshots, snapshot_native_resources,
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


def _process_peak_rss_bytes() -> int:
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return int(peak if sys.platform == "darwin" else peak * 1024)


def run_p22_four_arm_development(*, family: str,
                                 training_draws: tuple[int, ...],
                                 validation_draws: tuple[int, ...] = (),
                                 budget_capacity: float = 64.0,
                                 search_attempt_ceiling: int = 64,
                                 max_rule_rounds: int = 256,
                                 selected_arms: tuple[str, ...] = _ARMS,
                                 measure_process_peak_rss: bool = False,
                                 measure_native_rule_work: bool = False,
                                 capture_checkpoints: bool = False) -> dict:
    """Run selected explicit conditions on a training-only v2 panel."""
    if family not in _GENERATORS:
        raise ValueError("unsupported P22 development family")
    if (not training_draws or len(training_draws) != len(set(training_draws))
            or any(isinstance(draw, bool) or not isinstance(draw, int)
                   or draw < 0 or draw >= 1000 for draw in training_draws)):
        raise ValueError("development requires unique registered training draws")
    if (len(validation_draws) != len(set(validation_draws))
            or not set(training_draws).isdisjoint(validation_draws)
            or any(isinstance(draw, bool) or not isinstance(draw, int)
                   or draw < 0 or draw >= 1000 for draw in validation_draws)):
        raise ValueError("validation requires unique development draws disjoint from training")
    if (isinstance(max_rule_rounds, bool) or not isinstance(max_rule_rounds, int)
            or max_rule_rounds < 1):
        raise ValueError("max_rule_rounds must be a positive integer")
    if (isinstance(search_attempt_ceiling, bool)
            or not isinstance(search_attempt_ceiling, int)
            or search_attempt_ceiling < 1 or search_attempt_ceiling > 30_000):
        raise ValueError("search attempt ceiling must be an integer in [1, 30000]")
    if (not selected_arms or len(selected_arms) != len(set(selected_arms))
            or any(arm not in _ARMS for arm in selected_arms)):
        raise ValueError("selected arms must be unique registered P22 conditions")
    if not isinstance(measure_process_peak_rss, bool):
        raise ValueError("process RSS measurement flag must be boolean")
    if not isinstance(measure_native_rule_work, bool):
        raise ValueError("native rule-work measurement flag must be boolean")
    if not isinstance(capture_checkpoints, bool):
        raise ValueError("checkpoint capture flag must be boolean")
    if capture_checkpoints and (len(selected_arms) != 1
            or not measure_process_peak_rss or not measure_native_rule_work):
        raise ValueError("checkpoint capture requires one isolated arm and complete runtime/native-work measurement")
    generator, size = _GENERATORS[family]
    worlds = [generator(split="train", draw=draw) for draw in training_draws]
    validation_worlds = [agent_view(generator(split="validation", draw=draw))
                          for draw in validation_draws]
    if any(len(world["initial_state"]) != size for world in worlds):
        raise ValueError("training worlds have inconsistent domain sizes")

    arms = {}
    for arm in selected_arms:
        arm_started = time.perf_counter()
        agent = boot_cognition_on()
        rule_capture = None
        try:
            if measure_native_rule_work:
                rule_capture = NativeRuleWorkCapture(agent.inner).start()
            configuration = configure_p22_arm(
                agent, arm, budget_capacity=budget_capacity)
            search_policies = agent.s.nodes("OpenProcessSearchPolicy")
            if len(search_policies) != 1:
                raise RuntimeError("four-arm graph must have exactly one open-search policy")
            agent.s.set_attr(search_policies[0], "max_attempts",
                             float(search_attempt_ceiling))
            agent.s.set_attr(search_policies[0], "max_attempts_per_request",
                             float(search_attempt_ceiling))
            domain_name, domain = _add_training_domain(agent, family, size, worlds)
            curriculum_policy = agent.s.nodes("ProcessCurriculumPolicy")[0]
            agent.s.set_attr(curriculum_policy, "max_tasks", float(len(worlds)))
            _add_task_inputs(agent, arm, domain_name, domain, worlds)

            native_rule_steps = 0
            rule_rounds = 0
            for _ in range(max_rule_rounds):
                fired = agent.inner.run_rules(20_000)
                rule_rounds += 1
                native_rule_steps += fired
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
            candidate_validation_panels = []
            for candidate in agent.s.nodes("OpenProcessCandidate"):
                if agent.s.node(candidate)["attrs"].get("status") != "unapproved_candidate":
                    continue
                if not validation_worlds:
                    continue
                candidate_validation_panels.append(
                    score_unapproved_candidate_validation_panel(
                        agent, candidate, validation_worlds))
            arms[arm] = {"configuration": configuration,
                "training_tasks": task_rows, "solved_count": sum(
                    row["solved"] for row in task_rows),
                "all_tasks_terminal": len(task_rows) == len(worlds) and
                    all(row["terminal"] for row in task_rows),
                "proposal_count": len(proposals), "proposals": proposals,
                "search_requests": search_requests,
                "curriculum_outcomes": curriculum_outcomes,
                "candidate_validation_panels": candidate_validation_panels,
                "approval_count": len(agent.s.nodes("OpenProcessAdoptionApproval")),
                "world_receipt_count": len(agent.s.nodes("OpenProcessWorldReceipt")),
                "rule_rounds": rule_rounds,
                "resource_snapshot": None}
            search_policies = agent.s.nodes("OpenProcessSearchPolicy")
            if len(search_policies) != 1:
                raise RuntimeError("four-arm graph must have exactly one open-search policy")
            reserved = agent.s.node(search_policies[0])["attrs"].get("attempts_reserved")
            if (isinstance(reserved, bool) or not isinstance(reserved, (int, float))
                    or not math.isfinite(reserved) or reserved < 0
                    or not float(reserved).is_integer()):
                raise RuntimeError("open-search reservation counter is invalid")
            attempts_created = len(agent.s.nodes("OpenProcessSearchAttempt"))
            if int(reserved) != attempts_created:
                raise RuntimeError("native attempt reservations differ from created attempts")
            counters = {"native_rule_steps": native_rule_steps,
                        "native_model_calls": 0,
                "search_attempts_reserved": int(reserved),
                "native_candidate_validation_evaluations": sum(
                    panel["world_count"] for panel in candidate_validation_panels)}
            arm_wall_time = time.perf_counter() - arm_started
            counters["wall_time_seconds"] = arm_wall_time
            if measure_process_peak_rss:
                counters["process_peak_rss_bytes"] = _process_peak_rss_bytes()
            native_rule_work = (rule_capture.finish()
                                if rule_capture is not None else None)
            arms[arm]["resource_snapshot"] = snapshot_native_resources(agent,
                runtime_counters=counters, native_rule_work=native_rule_work)
            arms[arm]["wall_time_seconds"] = arm_wall_time
            if capture_checkpoints:
                ancestor_schemas = [node for node in agent.s.nodes("ProcessSchema")
                    if agent.s.node(node)["attrs"].get("domain") == domain_name
                    and agent.s.node(node)["attrs"].get("status") == "active"
                    and agent.s.node(node)["attrs"].get("provenance")
                        == "world_affordance"]
                if not ancestor_schemas:
                    raise RuntimeError("checkpoint capture requires a registered active domain ancestor")
                ancestor_schemas.sort(key=lambda node: (
                    agent.s.node(node)["attrs"].get("name", ""), str(node)))
                cumulative = arms[arm]["resource_snapshot"]["cumulative_resources"]
                cumulative_primitive = (cumulative.get("native_solver_primitive_work", 0.0)
                    + cumulative.get("search_declared_primitive_work", 0.0))
                if (isinstance(cumulative_primitive, bool)
                        or not isinstance(cumulative_primitive, (int, float))
                        or not math.isfinite(cumulative_primitive)
                        or cumulative_primitive < 0
                        or not float(cumulative_primitive).is_integer()):
                    raise RuntimeError("measured cumulative primitive work is invalid")
                checkpoint = capture_held_process_checkpoint(agent,
                    ancestor_schemas[0],
                    checkpoint_id=f"p22-{family}-{arm}-g0",
                    declared_primitive_work=int(cumulative_primitive),
                    runtime_counters=counters, native_rule_work=native_rule_work)
                arms[arm]["generation_zero_checkpoint"] = asdict(checkpoint)
        finally:
            if rule_capture is not None:
                rule_capture.close()
            agent.close()

    world_ids = [world["world_id"] for world in worlds]
    return {"status": "DEVELOPMENT_ONLY", "family": family,
        "split": "training", "training_world_ids": world_ids,
        "validation_world_ids": [world["world_id"] for world in validation_worlds],
        "search_attempt_ceiling": search_attempt_ceiling,
        "common_worlds": all(arms[arm]["training_tasks"] and
            [row["world_id"] for row in arms[arm]["training_tasks"]] == world_ids
            for arm in selected_arms),
        "all_arms_terminal": all(arms[arm]["all_tasks_terminal"]
                                 for arm in selected_arms),
        "arms": arms,
        "resource_comparison": (compare_resource_snapshots(
            {arm: arms[arm]["resource_snapshot"] for arm in selected_arms})
            if len(selected_arms) >= 2 else None),
        "approvals_created": sum(arms[arm]["approval_count"] for arm in selected_arms),
        "world_receipts_created": sum(arms[arm]["world_receipt_count"]
                                       for arm in selected_arms),
        "efficacy_established": False}

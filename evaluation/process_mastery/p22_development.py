"""Reproducible P22 training-proposal probes on non-held-out worlds."""
from __future__ import annotations

import hashlib
import json
import math
import os
import resource
import sys
import time
from dataclasses import asdict

from evaluation.process_mastery.checkpoint_world_adapter import (
    CheckpointExpression, CheckpointWorldAdapter,
    capture_adopted_checkpoint, capture_held_process_checkpoint,
    restore_native_checkpoint_graph,
    score_unapproved_candidate_validation_panel,
)
from evaluation.process_mastery.harness import Agent
from evaluation.process_mastery.independent_worlds import (
    agent_view, generate_d4_world_v2, generate_loopover_world_v2,
)
from evaluation.process_mastery.native_process_execution import (
    attest_open_process_candidate, execute_open_process_candidate, params_digest,
)
from evaluation.process_mastery.p22_resource_accounting import (
    NativeRuleWorkCapture, merge_native_rule_work_snapshots,
    native_rule_work_digest_valid, snapshot_native_resources,
)
from substrate.seed_loader import manifest_for


_FAMILIES = {
    "d4": (generate_d4_world_v2, 4),
    "loopover": (generate_loopover_world_v2, 9),
}


def _process_peak_rss_bytes() -> int:
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return int(peak if sys.platform == "darwin" else peak * 1024)


def _process_peak_rss_observations(parent_runtime: dict) -> tuple[int, list[dict]]:
    """Keep cumulative peak RSS with the process identity that measured it.

    Older checkpoints stored only the maximum value. Preserve that value as an
    explicitly unattributed observation so a later process cannot silently
    make it appear to have measured the inherited peak itself.
    """
    inherited = int(parent_runtime.get("process_peak_rss_bytes", 0))
    observations = list(parent_runtime.get("process_peak_rss_observations", []))
    if inherited and not observations:
        observations.append({"pid": None, "observed_at_unix_ns": None,
            "peak_rss_bytes": inherited,
            "scope": "inherited_legacy_unattributed"})
    current = _process_peak_rss_bytes()
    observations.append({"pid": os.getpid(), "observed_at_unix_ns": time.time_ns(),
        "peak_rss_bytes": current,
        "scope": "resource.getrusage(RUSAGE_SELF).ru_maxrss"})
    return max(inherited, current), observations


def _search_attempts_reserved(agent) -> int:
    values = [agent.attrs(request).get("attempts_reserved", 0)
        for request in agent.nodes("OpenProcessSearchRequest")]
    if any(isinstance(value, bool) or not isinstance(value, (int, float))
            or not math.isfinite(value) or value < 0
            or not float(value).is_integer() for value in values):
        raise RuntimeError("search reservations must be finite nonnegative integers")
    return sum(int(value) for value in values)


def _digest(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True,
        separators=(",", ":"), default=list).encode("utf-8")).hexdigest()


def _qualification_is_valid(agent, proposal, qualification) -> bool:
    """Apply the typed, digest-bound training-evidence contract to a receipt."""
    attrs = agent.attrs(qualification)
    proposal_attrs = agent.attrs(proposal)
    if (attrs.get("status") != "qualified_for_candidate_specific_approval"
            or attrs.get("qualification_kind") not in {
                "independent_native_trials", "independent_goal_composition"}
            or attrs.get("trial_count") != 2.0
            or attrs.get("split") != "training"
            or attrs.get("expression_digest") != proposal_attrs.get("expression_digest")
            or attrs.get("criteria_digest") != proposal_attrs.get("criteria_digest")):
        return False
    witness_tasks = {}
    for attempt in agent.native.neighbours(qualification, "counts_native_trial"):
        if agent.attrs(attempt).get("status") != "verified":
            continue
        tasks = agent.native.neighbours(attempt, "about_task")
        if len(tasks) != 1:
            continue
        task = tasks[0]
        task_attrs = agent.attrs(task)
        key = task_attrs.get("training_trial_key")
        if task_attrs.get("split") == "training" and isinstance(key, str) and key:
            witness_tasks[key] = task_attrs
    if len(witness_tasks) < 2:
        return False
    if attrs.get("qualification_kind") == "independent_goal_composition":
        if attrs.get("independent_goal_count") != 2.0:
            return False
        goals = {json.dumps(task.get("goal"), sort_keys=True, default=list)
                 for task in witness_tasks.values()}
        if len(goals) < 2:
            return False
    return True


def _select_approved_qualification(qualifications: list[dict],
                                  binding: dict) -> dict:
    """Resolve one exact training qualification for a candidate approval.

    Graph node IDs can shift when a seed is regenerated. If the source ID is
    absent from an exact replay, resolve by the already-bound witness pair and
    qualification kind; never substitute a different trial pair.
    """
    requested_id = binding.get("qualification_id")
    if requested_id is None:
        if len(qualifications) != 1:
            raise RuntimeError(
                "candidate with multiple qualifications requires an exact qualification_id")
        selected = qualifications[0]
    else:
        if not isinstance(requested_id, str) or not requested_id:
            raise RuntimeError("qualification_id must be a nonempty string")
        matches = [qualification for qualification in qualifications
                   if qualification.get("qualification_id") == requested_id]
        if len(matches) > 1:
            raise RuntimeError("qualification_id identifies multiple qualified records")
        if matches:
            selected = matches[0]
        else:
            expected = binding.get("training_trial_keys")
            expected_kind = binding.get("qualification_kind")
            if (not isinstance(expected, list)
                    or any(not isinstance(key, str) or not key for key in expected)
                    or len(expected) != len(set(expected))):
                raise RuntimeError("qualification ID replay requires exact unique training witnesses")
            replay_matches = [qualification for qualification in qualifications
                if sorted(qualification.get("training_trial_keys", [])) == sorted(expected)
                and (expected_kind is None or qualification.get("kind") == expected_kind)]
            if len(replay_matches) != 1:
                raise RuntimeError(
                    "qualification_id does not replay to exactly one record with the bound witnesses")
            selected = dict(replay_matches[0])
            selected["requested_qualification_id"] = requested_id
    witnesses = selected.get("training_trial_keys")
    expected = binding.get("training_trial_keys")
    if (not isinstance(witnesses, list) or not isinstance(expected, list)
            or sorted(set(witnesses)) != sorted(expected)
            or len(expected) != len(set(expected))):
        raise RuntimeError("candidate qualification witnesses differ from approval")
    return selected


def run_p22_training_proposal_probe(*, family: str,
                                    training_draws: tuple[int, ...],
                                    validation_draws: tuple[int, ...],
                                    training_goal_relation: str = "same",
                                    search_ticks: int = 30,
                                    per_request_attempt_ceiling: int = 5000,
                                    global_attempt_ceiling: int = 30000,
                                    measure_native_rule_work: bool = False,
                                    approved_candidate_binding: dict | None = None,
                                    parent_checkpoint: CheckpointExpression | None = None,
                                    candidate_transfer_depth: int | None = None,
                                    discovery_attempt_limit_per_request: int | None = None,
                                    transfer_reserve_per_request: int = 0,
                                    effect_dedup_enabled: bool = False,
                                    export_attempt_details: bool = False) -> dict:
    """Run native search on two training worlds and score every proposal.

    The default ``same`` mode reproduces the original qualification probe.
    ``distinct`` uses independently generated v2 goals. Every graph candidate
    is evaluated; candidate-specific approval is permitted only when the exact
    reviewer binding is supplied. A digest-valid parent checkpoint restores
    graph state for a later training generation. There is no held-out input
    path.
    """
    if family not in _FAMILIES:
        raise ValueError("unsupported P22 development family")
    generator, size = _FAMILIES[family]
    if (not 2 <= len(training_draws) <= 8
            or len(set(training_draws)) != len(training_draws)
            or len(set(validation_draws)) != len(validation_draws)
            or any(isinstance(draw, bool) or not isinstance(draw, int)
                   or draw < 0 or draw >= 1000
                   for draw in (*training_draws, *validation_draws))
            or isinstance(search_ticks, bool) or not isinstance(search_ticks, int)
            or search_ticks <= 0):
        raise ValueError("probe requires 2–8 unique training draws and unique validation draws")
    if (isinstance(per_request_attempt_ceiling, bool)
            or not isinstance(per_request_attempt_ceiling, int)
            or not 1 <= per_request_attempt_ceiling <= 30000):
        raise ValueError("per-request attempt ceiling must be in [1, 30000]")
    if (isinstance(global_attempt_ceiling, bool)
            or not isinstance(global_attempt_ceiling, int)
            or not 1 <= global_attempt_ceiling <= 120000):
        raise ValueError("global attempt ceiling must be in [1, 120000]")
    if (isinstance(transfer_reserve_per_request, bool)
            or not isinstance(transfer_reserve_per_request, int)
            or transfer_reserve_per_request < 0):
        raise ValueError("transfer reserve must be a nonnegative integer")
    if discovery_attempt_limit_per_request is not None:
        if (isinstance(discovery_attempt_limit_per_request, bool)
                or not isinstance(discovery_attempt_limit_per_request, int)
                or discovery_attempt_limit_per_request < 1):
            raise ValueError("discovery attempt limit must be a positive integer")
        if discovery_attempt_limit_per_request + transfer_reserve_per_request > per_request_attempt_ceiling:
            raise ValueError("discovery plus transfer reserve exceeds the per-request ceiling")
    elif transfer_reserve_per_request:
        raise ValueError("a transfer reserve requires an explicit discovery attempt limit")
    if not isinstance(effect_dedup_enabled, bool) or not isinstance(export_attempt_details, bool):
        raise ValueError("P26 search flags must be boolean")
    if export_attempt_details and (validation_draws or training_goal_relation != "distinct"):
        raise ValueError("attempt-detail export is restricted to training-only distinct-goal probes")
    if not isinstance(measure_native_rule_work, bool):
        raise ValueError("native rule-work measurement flag must be boolean")
    if (approved_candidate_binding is not None
            and not isinstance(approved_candidate_binding, dict)):
        raise ValueError("approved candidate binding must be an object")
    approved_transfer_depth = (approved_candidate_binding.get(
        "candidate_transfer_depth", 1) if approved_candidate_binding is not None else 2)
    if (isinstance(approved_transfer_depth, bool)
            or approved_transfer_depth not in (1, 2, 3)):
        raise ValueError("candidate transfer depth must be 1, 2, or 3")
    if candidate_transfer_depth is None:
        candidate_transfer_depth = approved_transfer_depth
    elif (isinstance(candidate_transfer_depth, bool)
            or candidate_transfer_depth not in (1, 2, 3)):
        raise ValueError("candidate transfer depth must be 1, 2, or 3")
    elif (approved_candidate_binding is not None
            and candidate_transfer_depth != approved_transfer_depth):
        raise ValueError("candidate transfer depth differs from approval request")
    parent_runtime = {}
    parent_rule_work = None
    inherited_global_attempt_ceiling = None
    inherited_solver_policy_count = None
    if parent_checkpoint is not None:
        if not CheckpointWorldAdapter._checkpoint_digest_valid(parent_checkpoint):
            raise ValueError("continuation requires an intact parent checkpoint")
        if parent_checkpoint.native_graph_snapshot_json is None:
            raise ValueError("continuation requires a native graph checkpoint")
        if not measure_native_rule_work:
            raise ValueError("checkpoint continuation requires native rule-work measurement")
        if len(parent_checkpoint.params) != size:
            raise ValueError("parent checkpoint permutation domain differs from this family")
        parent_snapshot = json.loads(parent_checkpoint.resource_snapshot_json)
        parent_runtime = parent_snapshot.get("runtime_counters") or {}
        parent_rule_work = parent_snapshot.get("native_rule_work")
        try:
            parent_graph = json.loads(parent_checkpoint.native_graph_snapshot_json)
            search_policies = [node["attrs"] for node in parent_graph["nodes"]
                if isinstance(node, dict) and node.get("type") == "OpenProcessSearchPolicy"
                and isinstance(node.get("attrs"), dict)]
            if len(search_policies) != 1:
                raise ValueError("parent graph must contain one search policy")
            inherited_global_attempt_ceiling = search_policies[0].get("max_attempts")
            if (isinstance(inherited_global_attempt_ceiling, bool)
                    or not isinstance(inherited_global_attempt_ceiling, (int, float))
                    or not math.isfinite(inherited_global_attempt_ceiling)
                    or inherited_global_attempt_ceiling < 1):
                raise ValueError("parent search policy has an invalid global ceiling")
        except (TypeError, KeyError, ValueError) as exc:
            raise ValueError("parent checkpoint lacks a valid global search ceiling") from exc
        required_runtime = ("native_rule_steps", "native_model_calls",
            "search_attempts_reserved", "process_peak_rss_bytes", "wall_time_seconds")
        if (not native_rule_work_digest_valid(parent_rule_work)
                or parent_rule_work.get("rule_identity_coverage") != "COMPLETE"
                or any(key not in parent_runtime for key in required_runtime)):
            raise ValueError("continuation requires complete cumulative parent resource counters")
    if approved_candidate_binding is not None:
        if (not isinstance(approved_candidate_binding, dict)
                or approved_candidate_binding.get("family") != family
                or not isinstance(approved_candidate_binding.get("expression_digest"), str)):
            raise ValueError("approved candidate binding must name this family and exact digest")
        review_seconds = approved_candidate_binding.get("human_review_seconds")
        if (isinstance(review_seconds, bool)
                or not isinstance(review_seconds, (int, float))
                or not math.isfinite(review_seconds) or review_seconds < 0):
            raise ValueError("candidate-specific adoption requires reviewer-reported human_review_seconds")
        if not measure_native_rule_work:
            raise ValueError("approved checkpoint capture requires native rule-work measurement")
        if validation_draws:
            raise ValueError("approved candidate checkpoint capture is training-only")
    if training_goal_relation not in {"same", "distinct"}:
        raise ValueError("training goal relation must be 'same' or 'distinct'")
    training_worlds = [generator(split="train", draw=draw) for draw in training_draws]
    goals_match = all(world["goal_state"] == training_worlds[0]["goal_state"]
                      for world in training_worlds[1:])
    same_target = all(world["hidden_target_params"]
                      == training_worlds[0]["hidden_target_params"]
                      for world in training_worlds[1:])
    relation_invalid = (
        (training_goal_relation == "same" and not same_target)
        or (training_goal_relation == "distinct"
            and len({tuple(world["goal_state"]) for world in training_worlds})
                != len(training_worlds)))
    if relation_invalid:
        raise ValueError(f"training draws must generate {training_goal_relation} goals")
    validation_worlds = [agent_view(generator(split="validation", draw=draw))
                         for draw in validation_draws]
    held = training_worlds[0]["held_processes"]
    if len(training_worlds[0]["initial_state"]) != size:
        raise ValueError("registered world has an unexpected state size")

    started = time.perf_counter()
    agent = Agent(track_i=False, extra_seeds=("open_process_search",),
        policy_overrides={
            "OpenProcessSearchPolicy": {"enabled": 1.0,
                "max_attempts": float(global_attempt_ceiling),
                "max_attempts_per_request": float(per_request_attempt_ceiling),
                "max_candidates": 16.0},
            "ProcessSchemaPolicy": {"enabled": 1.0}},
        budget={"enabled": 1.0, "remaining": 100000.0,
            "capacity": 100000.0, "last_refill_epoch": 0.0,
            "refill_per_epoch": 0.0})
    rule_capture = None
    measured_native_rule_work = None
    adoption_resource_snapshot = None
    try:
        if parent_checkpoint is not None:
            restore_native_checkpoint_graph(agent, parent_checkpoint)
            solver_policies = agent.nodes("SolverPolicy")
            if len(solver_policies) > 1:
                raise RuntimeError("restored checkpoint must contain at most one SolverPolicy")
            inherited_solver_policy_count = len(solver_policies)
            # This runner isolates native proposal search by putting each new
            # task into an observed impasse. A restored executable solver can
            # otherwise solve the task or exhaust its primitive-work ceiling
            # before OpenProcessSearch sees it. The scoring adapter installs
            # its own fixed SolverPolicy when it later evaluates a checkpoint.
            for policy in solver_policies:
                agent.s.set_attr(policy, "enabled", 0.0)
        search_policies = agent.nodes("OpenProcessSearchPolicy")
        if len(search_policies) != 1:
            raise RuntimeError("P22 graph must contain exactly one open-search policy")
        candidate_transfer_depth = float(candidate_transfer_depth)
        agent.s.set_attr(search_policies[0], "candidate_transfer_depth",
                         candidate_transfer_depth)
        # For a continuation this may raise the declared cap, but does not
        # reset attempts already charged in the restored graph.
        agent.s.set_attr(search_policies[0], "max_attempts",
                         float(global_attempt_ceiling))
        # Checkpoint restoration replaces the policy with its parent snapshot,
        # so restore the caller-bound per-request ceiling too. Leaving the
        # parent's value here silently ignored higher continuation ceilings.
        agent.s.set_attr(search_policies[0], "max_attempts_per_request",
                         float(per_request_attempt_ceiling))
        agent.s.set_attr(search_policies[0], "effect_dedup_enabled",
                         float(effect_dedup_enabled))
        agent.s.set_attr(search_policies[0], "discovery_attempt_limit_per_request",
                         float(discovery_attempt_limit_per_request or 0))
        agent.s.set_attr(search_policies[0], "transfer_reserve_per_request",
                         float(transfer_reserve_per_request))
        if measure_native_rule_work:
            rule_capture = NativeRuleWorkCapture(agent.native).start()
        if parent_checkpoint is None:
            domain_name = "p22-development"
            domain = agent.add_domain(domain_name, "permutation",
                [training_worlds[0]["initial_state"]], held)
        else:
            domains = [node for node in agent.nodes("ProcessDomain")
                if agent.attrs(node).get("name") in {
                    f"p22-development-{family}", "p22-development"}]
            if len(domains) != 1:
                raise RuntimeError(
                    "restored checkpoint must contain one family-specific development domain")
            domain = domains[0]
            domain_name = agent.attrs(domain).get("name")
            if agent.attrs(domain).get("kind") == "permutation":
                agent.s.set_attr(domain, "identity_effect_digest",
                                 [list(range(size))])
            agent.domains[domain_name] = domain
            prior_training_ids = {agent.attrs(task).get("training_trial_key")
                for task in agent.nodes("SolveTask")
                if agent.attrs(task).get("split") == "training"}
            if prior_training_ids.intersection(world["world_id"]
                                               for world in training_worlds):
                raise ValueError("continuation training worlds overlap prior lineage exposure")
        for schema in agent.nodes("ProcessSchema"):
            if agent.attrs(schema).get("domain") == domain_name:
                agent.s.add_edge(domain, "has_held_process", schema, {})
        agent.native.load_seed_manifest(manifest_for("open_process_adoption"), agent.ag)
        agent.native.load_seed_manifest(manifest_for("independent_improvement"), agent.ag)
        agent.s.set_attr(agent.nodes("IndependentImprovementPolicy")[0], "enabled", 1.0)
        for policy in agent.nodes("OpenProcessAdoptionPolicy"):
            agent.s.set_attr(policy, "enabled", 1.0)

        rule_progress = []
        native_rule_steps = int(parent_runtime.get("native_rule_steps", 0))
        first_trial_candidate_missing = False
        training_task_rows = []
        for trial, world in enumerate(training_worlds, start=1):
            task = agent.add_solve_task(domain_name, world["initial_state"],
                world["goal_state"], training_trial_key=world["world_id"],
                split="training")
            # The task pool contains an observed impasse so this probe begins
            # at generic native invention, with no host-selected operator.
            agent.s.set_attr(task, "status", "stuck")
            for _ in range(search_ticks):
                report = agent.native.run_rules_report(4000, False)
                native_rule_steps += int(report["progress_steps"])
                if report.get("last_progress_rule"):
                    rule_progress.append(report["last_progress_rule"])
            if trial == 1:
                candidates = [candidate for candidate in agent.nodes("OpenProcessCandidate")
                    if agent.attrs(candidate).get("status") == "unapproved_candidate"]
                if not candidates:
                    first_trial_candidate_missing = True
                for candidate in candidates:
                    attest_open_process_candidate(agent, candidate)
            related_requests = [request for request in agent.nodes("OpenProcessSearchRequest")
                if task in agent.native.neighbours(request, "searches_task")]
            training_task_rows.append({
                "world_id": world["world_id"],
                "goal_digest": _digest(world["goal_state"]),
                "task_status": agent.attrs(task).get("status"),
                "search_requests": [{
                    "status": agent.attrs(request).get("status"),
                    "max_attempts": agent.attrs(request).get("max_attempts"),
                    "attempt_count": len(agent.native.neighbours(
                        request, "has_search_attempt")),
                    "reserved_attempts": agent.attrs(request).get("attempts_reserved"),
                } for request in related_requests],
            })

        for candidate in agent.nodes("OpenProcessCandidate"):
            if (agent.attrs(candidate).get("status") == "unapproved_candidate"
                    and agent.attrs(candidate).get("expression_digest_status") != "verified"):
                attest_open_process_candidate(agent, candidate)
        for _ in range(8):
            report = agent.native.run_rules_report(4000, False)
            native_rule_steps += int(report["progress_steps"])
            if report.get("last_progress_rule"):
                rule_progress.append(report["last_progress_rule"])

        search_attempts_reserved = _search_attempts_reserved(agent)
        root_checkpoint = parent_checkpoint
        if parent_checkpoint is None and measure_native_rule_work:
            identity_params = list(range(size))
            identity = agent.s.add_node("ProcessSchema", {
                "name": f"p22-{family}-generation-zero-identity",
                "kind": "permutation", "domain_kind": "permutation",
                "domain": domain_name, "params": identity_params,
                "source_digest": params_digest(identity_params), "cost": 1.0,
                "status": "active", "provenance": "p22_generation_zero_ancestor",
                "invariants": [], "source_epoch": 0, "model_epoch": 0,
                "frame_epoch": 0, "probe_epoch": 0, "source_probe_epoch": 0})
            agent.s.add_edge(agent.ag, "has_process_schema", identity, {})
            agent.s.add_edge(domain, "has_held_process", identity, {})
            root_peak_rss, root_peak_observations = _process_peak_rss_observations(
                parent_runtime)
            root_runtime = {"native_rule_steps": native_rule_steps,
                "native_model_calls": int(parent_runtime.get("native_model_calls", 0)),
                "search_attempts_reserved": search_attempts_reserved,
                "process_peak_rss_bytes": root_peak_rss,
                "process_peak_rss_observations": root_peak_observations,
                "wall_time_seconds": float(parent_runtime.get("wall_time_seconds", 0.0))
                    + time.perf_counter() - started}
            root_rule_work = rule_capture.snapshot() if rule_capture else None
            if parent_rule_work is not None:
                root_rule_work = merge_native_rule_work_snapshots(
                    parent_rule_work, root_rule_work)
            root_snapshot = snapshot_native_resources(agent,
                runtime_counters=root_runtime, native_rule_work=root_rule_work)
            root_primitive = (root_snapshot["cumulative_resources"].get(
                "native_solver_primitive_work", 0.0)
                + root_snapshot["cumulative_resources"].get(
                    "search_declared_primitive_work", 0.0))
            if not float(root_primitive).is_integer():
                raise RuntimeError("generation-zero primitive work is not integral")
            root_identity = _digest({"family": family,
                "training_world_ids": [world["world_id"] for world in training_worlds]})[:12]
            root_checkpoint = capture_held_process_checkpoint(agent, identity,
                checkpoint_id=f"p22-{family}-g0-{root_identity}",
                declared_primitive_work=int(root_primitive),
                runtime_counters=root_runtime, native_rule_work=root_rule_work)

        simulated_adoption = None
        if approved_candidate_binding is not None:
            expected_digest = approved_candidate_binding["expression_digest"]
            matches = [candidate for candidate in agent.nodes("OpenProcessCandidate")
                if agent.attrs(candidate).get("expression_digest") == expected_digest
                and agent.attrs(candidate).get("status") == "unapproved_candidate"]
            if len(matches) != 1:
                raise RuntimeError("approved digest did not reconstruct as one unapproved candidate")
            candidate = matches[0]
            attrs = agent.attrs(candidate)
            exact_fields = ("expression_digest", "expression_key", "expression_tree",
                "effect_digest", "params", "guard_state", "domain", "kind",
                "source_epoch", "model_epoch", "frame_epoch")
            mismatched = [key for key in exact_fields
                          if attrs.get(key) != approved_candidate_binding.get(key)]
            # Native graph literals can retain Surface(Text) wrappers while a
            # JSON artifact necessarily renders those leaves as strings. The
            # candidate digest attests the complete native tree; copy that
            # graph value into the approval so native equality remains exact.
            if "expression_tree" in mismatched:
                from evaluation.process_mastery.native_process_execution import (
                    open_process_candidate_digest,
                )
                if open_process_candidate_digest(agent, candidate) == expected_digest:
                    mismatched.remove("expression_tree")
            if mismatched:
                raise RuntimeError("reconstructed candidate binding differs from approval: "
                                   + ", ".join(mismatched))
            quals = [q for proposal in agent.nodes("IndependentImprovementProposal")
                if agent.native.neighbours(proposal, "proposes_native_candidate") == [candidate]
                for q in agent.native.neighbours(proposal, "has_native_qualification")
                if _qualification_is_valid(agent, proposal, q)]
            qualification_records = [{
                "qualification_id": str(q),
                "kind": agent.attrs(q).get("qualification_kind"),
                "declared_trial_count": agent.attrs(q).get("trial_count"),
                "training_trial_keys": sorted({key
                    for attempt in agent.native.neighbours(q, "counts_native_trial")
                    for task in agent.native.neighbours(attempt, "about_task")
                    if agent.attrs(task).get("split") == "training"
                    for key in [agent.attrs(task).get("training_trial_key")]
                    if isinstance(key, str) and key}),
            } for q in quals]
            selected_qualification = _select_approved_qualification(
                qualification_records, approved_candidate_binding)
            expected_witnesses = sorted(selected_qualification["training_trial_keys"])
            if root_checkpoint is None:
                raise RuntimeError("approved candidate capture requires a measured parent checkpoint")
            approval_context = {key: attrs[key] for key in exact_fields}
            approval = agent.s.add_node("OpenProcessAdoptionApproval", {
                "status": "approved", "approval_kind": "human",
                "human_review_seconds": float(
                    approved_candidate_binding["human_review_seconds"]),
                "human_review_cost_source": "reviewer_self_report",
                "qualification_id": selected_qualification["qualification_id"],
                "requested_qualification_id": approved_candidate_binding.get(
                    "qualification_id"),
                "qualification_training_trial_keys": expected_witnesses,
                **approval_context})
            agent.s.add_edge(agent.ag, "has_open_process_adoption_approval", approval, {})
            agent.s.add_edge(approval, "approves_open_process_candidate", candidate, {})
            for _ in range(64):
                fired = agent.native.run_rules(10000)
                native_rule_steps += fired
                if fired == 0:
                    break
            world = training_worlds[0]
            accepted = {"count": 0}
            def authorize(proposal):
                if (accepted["count"] != 0 or proposal.get("candidate_id") != candidate
                        or proposal.get("expression_digest") != expected_digest
                        or proposal.get("state") != world["initial_state"]
                        or proposal.get("action") != attrs["params"]):
                    return False
                accepted["count"] += 1
                return True
            def transition(params):
                state = list(world["initial_state"])
                observed = [None] * len(params)
                for source, destination in enumerate(params):
                    observed[destination] = state[source]
                return {"status": "verified", "observed_state": observed,
                        "simulator": "p22-registered-finite-permutation-v2",
                        "world_id": world["world_id"]}
            result = execute_open_process_candidate(agent, candidate,
                state=list(world["initial_state"]), authorize=authorize,
                world_transition=transition)
            increment_rule_work = rule_capture.finish()
            rule_capture = None
            native_rule_work = (merge_native_rule_work_snapshots(
                parent_rule_work, increment_rule_work) if parent_rule_work is not None
                else increment_rule_work)
            measured_native_rule_work = native_rule_work
            approval_nodes = agent.native.neighbours(
                candidate, "approved_by_open_process_adoption")
            approval_attrs = (agent.attrs(approval_nodes[0])
                              if len(approval_nodes) == 1 else {})
            simulated_adoption = {"candidate_id": str(candidate),
                "qualification_id": selected_qualification["qualification_id"],
                "requested_qualification_id": approved_candidate_binding.get(
                    "qualification_id"),
                "expression_digest": expected_digest,
                "training_trial_keys": expected_witnesses,
                "approval_id": (str(approval_nodes[0])
                                if len(approval_nodes) == 1 else None),
                "approval_status": approval_attrs.get("status"),
                "approval_kind": approval_attrs.get("approval_kind"),
                "approval_binding": {key: approval_attrs.get(key)
                    for key in exact_fields},
                "approval_count": len(agent.nodes("OpenProcessAdoptionApproval")),
                "status": result.get("status"),
                "reason": result.get("reason"),
                "receipt_id": (str(result["evidence_node"])
                               if result.get("evidence_node") is not None else None),
                "receipt": result.get("receipt"),
                "receipt_status": (agent.attrs(result["evidence_node"]).get("status")
                                   if result.get("evidence_node") is not None else None),
                "world_transition_count": accepted["count"]}
            if (result.get("status") != "COMPLETED"
                    or simulated_adoption["receipt_status"] != "verified"
                    or approval_attrs.get("status") != "consumed"
                    or approval_attrs.get("approval_kind") != "human"
                    or accepted["count"] != 1):
                raise RuntimeError("approved simulated adoption did not complete exactly once: "
                    + json.dumps(simulated_adoption, sort_keys=True, default=str))
            final_peak_rss, final_peak_observations = _process_peak_rss_observations(
                parent_runtime)
            final_runtime = {"native_rule_steps": native_rule_steps,
                "native_model_calls": int(parent_runtime.get("native_model_calls", 0)),
                "search_attempts_reserved": search_attempts_reserved,
                "native_candidate_validation_evaluations": 0,
                "process_peak_rss_bytes": final_peak_rss,
                "process_peak_rss_observations": final_peak_observations,
                "wall_time_seconds": float(parent_runtime.get("wall_time_seconds", 0.0))
                    + time.perf_counter() - started}
            final_snapshot = snapshot_native_resources(agent,
                runtime_counters=final_runtime, native_rule_work=native_rule_work)
            cumulative_primitive = (final_snapshot["cumulative_resources"].get(
                "native_solver_primitive_work", 0.0)
                + final_snapshot["cumulative_resources"].get(
                    "search_declared_primitive_work", 0.0))
            incremental_primitive = cumulative_primitive - root_checkpoint.cumulative_primitive_work
            if (not float(incremental_primitive).is_integer()
                    or incremental_primitive < 0):
                raise RuntimeError("generation-one primitive work delta is not a nonnegative integer")
            child_generation = root_checkpoint.generation + 1
            generation_one = capture_adopted_checkpoint(agent, candidate,
                checkpoint_id=f"p22-{family}-g{child_generation}-{expected_digest[:12]}",
                parent=root_checkpoint, generation=child_generation,
                declared_primitive_work=int(incremental_primitive),
                runtime_counters=final_runtime, native_rule_work=native_rule_work)
            adoption_resource_snapshot = final_snapshot
            simulated_adoption["parent_checkpoint"] = asdict(root_checkpoint)
            simulated_adoption["child_checkpoint"] = asdict(generation_one)
            simulated_adoption[f"generation_{child_generation}_checkpoint"] = asdict(
                generation_one)
            if child_generation == 1:
                simulated_adoption["generation_one_checkpoint"] = asdict(
                    generation_one)
            if root_checkpoint.generation == 0:
                simulated_adoption["generation_zero_ancestor"] = asdict(root_checkpoint)

        candidate_rows = []
        for candidate in agent.nodes("OpenProcessCandidate"):
            attrs = agent.attrs(candidate)
            if attrs.get("status") != "unapproved_candidate":
                continue
            proposals = [proposal for proposal in agent.nodes("IndependentImprovementProposal")
                if agent.native.neighbours(proposal, "proposes_native_candidate") == [candidate]]
            all_qualifications = [qualification
                for proposal in proposals
                for qualification in agent.native.neighbours(proposal, "has_native_qualification")]
            qualifications = [qualification for proposal in proposals
                for qualification in agent.native.neighbours(
                    proposal, "has_native_qualification")
                if _qualification_is_valid(agent, proposal, qualification)]
            qualification_rows = []
            for proposal in proposals:
                for qualification in agent.native.neighbours(proposal, "has_native_qualification"):
                    if not _qualification_is_valid(agent, proposal, qualification):
                        continue
                    trial_attempts = agent.native.neighbours(qualification, "counts_native_trial")
                    trial_tasks = [agent.native.neighbours(attempt, "about_task")
                                   for attempt in trial_attempts]
                    qualification_rows.append({
                        "qualification_id": str(qualification),
                        "status": agent.attrs(qualification).get("status"),
                        "kind": agent.attrs(qualification).get("qualification_kind"),
                        "declared_trial_count": agent.attrs(qualification).get("trial_count"),
                        "attempt_ids": [str(attempt) for attempt in trial_attempts],
                        "task_ids": [str(tasks[0]) if len(tasks) == 1 else None
                                     for tasks in trial_tasks],
                        "training_trial_keys": sorted({
                            agent.attrs(tasks[0]).get("training_trial_key")
                            for tasks in trial_tasks if len(tasks) == 1
                            and agent.attrs(tasks[0]).get("split") == "training"
                            and isinstance(agent.attrs(tasks[0]).get("training_trial_key"), str)
                            and agent.attrs(tasks[0]).get("training_trial_key")}),
                    })
            independent_trial_rows = []
            for trial_attempt in agent.native.neighbours(
                    candidate, "has_independent_trial_attempt"):
                trial_tasks = agent.native.neighbours(trial_attempt, "about_task")
                trial_requests = [request for request in agent.nodes("OpenProcessSearchRequest")
                    if trial_attempt in agent.native.neighbours(request, "has_search_attempt")]
                trial_candidates = [derived for derived in agent.nodes("OpenProcessCandidate")
                    if agent.native.neighbours(derived, "derived_from_attempt") == [trial_attempt]]
                independent_trial_rows.append({
                    "attempt_id": str(trial_attempt),
                    "expression_key": agent.attrs(trial_attempt).get("expression_key"),
                    "operator_kind": agent.attrs(trial_attempt).get("operator_kind"),
                    "depth": agent.attrs(trial_attempt).get("depth"),
                    "status": agent.attrs(trial_attempt).get("status"),
                    "task_key": (agent.attrs(trial_tasks[0]).get("training_trial_key")
                                 if len(trial_tasks) == 1 else None),
                    "goal_state": (agent.attrs(trial_tasks[0]).get("goal")
                                   if len(trial_tasks) == 1 else None),
                    "trial_request_statuses": [agent.attrs(request).get("status")
                                               for request in trial_requests],
                    "parent_candidate_ids": [str(parent) for parent in
                        agent.native.neighbours(trial_attempt, "extends_candidate")],
                    "parent_process_sources": [{
                        "name": agent.attrs(parent).get("name"),
                        "source_digest": agent.attrs(parent).get("source_digest"),
                        "params": agent.attrs(parent).get("params"),
                    } for parent in agent.native.neighbours(
                        trial_attempt, "uses_parent_process")],
                    "derived_candidate_ids": [str(derived) for derived in trial_candidates],
                    "derived_candidate_statuses": [agent.attrs(derived).get("status")
                                                    for derived in trial_candidates],
                })
            panel = (score_unapproved_candidate_validation_panel(
                agent, candidate, validation_worlds) if validation_worlds else None)
            source_attempts = agent.native.neighbours(candidate, "derived_from_attempt")
            source_attempt = source_attempts[0] if len(source_attempts) == 1 else None
            source_tasks = (agent.native.neighbours(source_attempt, "about_task")
                            if source_attempt is not None else [])
            source_task = source_tasks[0] if len(source_tasks) == 1 else None
            source_requests = [request for request in agent.nodes("OpenProcessSearchRequest")
                if source_attempt is not None and source_attempt in
                   agent.native.neighbours(request, "has_search_attempt")]
            candidate_rows.append({
                "candidate_id": str(candidate),
                "expression_digest": attrs.get("expression_digest"),
                "expression_key": attrs.get("expression_key"),
                "params": attrs.get("params"),
                "status": attrs.get("status"),
                "approval_binding": {key: attrs.get(key) for key in (
                    "expression_digest", "expression_key", "expression_tree",
                    "effect_digest", "params", "guard_state", "domain",
                    "kind", "source_epoch", "model_epoch", "frame_epoch",
                    "status", "expression_digest_status")},
                "proposal_count": len(proposals),
                "proposals": [{"proposal_id": str(proposal),
                    "status": agent.attrs(proposal).get("status"),
                    "source_attempt_ids": [str(attempt) for attempt in
                        agent.native.neighbours(proposal, "derived_from_trial")]}
                    for proposal in proposals],
                "qualification_count": len(qualifications),
                "qualifications": qualification_rows,
                "pending_qualification_slot_count": sum(
                    agent.attrs(qualification).get("status")
                    == "awaiting_native_qualification"
                    for qualification in all_qualifications),
                "invalid_qualification_receipt_count": sum(
                    agent.attrs(qualification).get("status")
                        == "qualified_for_candidate_specific_approval"
                    and not _qualification_is_valid(agent, proposal, qualification)
                    for proposal in proposals
                    for qualification in agent.native.neighbours(
                        proposal, "has_native_qualification")),
                "independent_goal_trials": independent_trial_rows,
                "qualification_inputs": {
                    "source_attempt_status": (agent.attrs(source_attempt).get("status")
                                               if source_attempt is not None else None),
                    "source_task_split": (agent.attrs(source_task).get("split")
                                          if source_task is not None else None),
                    "source_task_goal": (agent.attrs(source_task).get("goal")
                                         if source_task is not None else None),
                    "source_request_statuses": [agent.attrs(request).get("status")
                                                for request in source_requests],
                    "candidate_domain": attrs.get("domain"),
                    "candidate_kind": attrs.get("kind"),
                    "candidate_epochs": [attrs.get("source_epoch"), attrs.get("model_epoch"),
                                         attrs.get("frame_epoch")],
                    "digest_receipts": [{"status": agent.attrs(receipt).get("status"),
                        "expression_digest": agent.attrs(receipt).get("expression_digest"),
                        "effect_digest": agent.attrs(receipt).get("effect_digest")}
                        for receipt in agent.native.neighbours(candidate,
                            "has_expression_digest_receipt")],
                },
                "panel": panel,
            })
        if rule_capture is not None:
            increment_rule_work = rule_capture.finish()
            measured_native_rule_work = (merge_native_rule_work_snapshots(
                parent_rule_work, increment_rule_work) if parent_rule_work is not None
                else increment_rule_work)
        final_resource_snapshot = adoption_resource_snapshot
        if final_resource_snapshot is None:
            final_peak_rss, final_peak_observations = _process_peak_rss_observations(
                parent_runtime)
            runtime_counters = {
                "native_rule_steps": native_rule_steps,
                "native_model_calls": int(parent_runtime.get("native_model_calls", 0)),
                "search_attempts_reserved": _search_attempts_reserved(agent),
                "native_candidate_validation_evaluations": sum(
                    row["panel"]["world_count"] for row in candidate_rows
                    if row.get("panel") is not None) + int(
                        parent_runtime.get("native_candidate_validation_evaluations", 0)),
                "process_peak_rss_bytes": final_peak_rss,
                "process_peak_rss_observations": final_peak_observations,
                "wall_time_seconds": float(parent_runtime.get("wall_time_seconds", 0.0))
                    + time.perf_counter() - started,
            }
            final_resource_snapshot = snapshot_native_resources(agent,
                runtime_counters=runtime_counters,
                native_rule_work=measured_native_rule_work)
        return {"status": ("NO_CANDIDATE_FIRST_TRIAL" if first_trial_candidate_missing
                           else "COMPLETED"),
            "failure_reasons": (["native_search_no_candidate_first_training_task"]
                                if first_trial_candidate_missing else []),
            "family": family,
            "training_world_ids": [world["world_id"] for world in training_worlds],
            "training_goals_match": goals_match,
            "training_goal_relation": training_goal_relation,
            "global_attempt_ceiling": global_attempt_ceiling,
            "inherited_global_attempt_ceiling": inherited_global_attempt_ceiling,
            "inherited_solver_policy_count": inherited_solver_policy_count,
            "proposal_search_solver_disabled": bool(
                parent_checkpoint is not None and inherited_solver_policy_count == 1),
            "per_request_attempt_ceiling": per_request_attempt_ceiling,
            "candidate_transfer_depth": candidate_transfer_depth,
            "native_rule_work": measured_native_rule_work,
            "training_goal_states": [world["goal_state"] for world in training_worlds],
            "validation_world_ids": [world["world_id"] for world in validation_worlds],
            "last_progress_rule_sequence": rule_progress,
            "training_task_rows": training_task_rows,
            "search_requests": [{
                "request_id": str(request),
                "status": agent.attrs(request).get("status"),
                "task_keys": [agent.attrs(task).get("training_trial_key")
                    for task in agent.native.neighbours(request, "searches_task")],
                "task_statuses": [agent.attrs(task).get("status")
                    for task in agent.native.neighbours(request, "searches_task")],
                "task_splits": [agent.attrs(task).get("split")
                    for task in agent.native.neighbours(request, "searches_task")],
                "task_goals": [agent.attrs(task).get("goal")
                    for task in agent.native.neighbours(request, "searches_task")],
                "attempt_count": len(agent.native.neighbours(request, "has_search_attempt")),
                "max_attempts": agent.attrs(request).get("max_attempts"),
                "reserved_attempts": agent.attrs(request).get("attempts_reserved"),
                "request_kind": agent.attrs(request).get("request_kind"),
                "discovery_attempt_limit": agent.attrs(request).get(
                    "discovery_attempt_limit"),
                "discovery_attempts_reserved": agent.attrs(request).get(
                    "discovery_attempts_reserved"),
                "transfer_attempt_reserve": agent.attrs(request).get(
                    "transfer_attempt_reserve"),
                "transfer_attempts_reserved": agent.attrs(request).get(
                    "transfer_attempts_reserved"),
                "transfer_candidate_ids": [str(candidate) for candidate in
                    agent.native.neighbours(request, "qualifies_candidate")],
                "transfer_source_task_keys": [agent.attrs(task).get("training_trial_key")
                    for attempt in agent.native.neighbours(request, "has_transfer_source_attempt")
                    for task in agent.native.neighbours(attempt, "about_task")],
            } for request in agent.nodes("OpenProcessSearchRequest")],
            "candidate_independent_goal_trials": {
                str(candidate): [str(attempt) for attempt in agent.native.neighbours(
                    candidate, "has_independent_trial_attempt")]
                for candidate in agent.nodes("OpenProcessCandidate")},
            "candidate_count": len(candidate_rows), "candidates": candidate_rows,
            "generation_zero_ancestor": (asdict(root_checkpoint)
                if root_checkpoint is not None and root_checkpoint.generation == 0
                else None),
            "parent_checkpoint": (asdict(parent_checkpoint)
                if parent_checkpoint is not None else None),
            "approval_count": len(agent.nodes("OpenProcessAdoptionApproval")),
            "simulated_adoption": simulated_adoption,
            "world_receipt_count": len(agent.nodes("OpenProcessWorldReceipt")),
            "resource_snapshot": final_resource_snapshot,
            "p26_search_configuration": {
                "effect_dedup_enabled": effect_dedup_enabled,
                "discovery_attempt_limit_per_request": discovery_attempt_limit_per_request,
                "transfer_reserve_per_request": transfer_reserve_per_request,
                "global_attempt_ceiling_unchanged": global_attempt_ceiling,
            },
            **({"attempt_detail_export": __import__(
                "evaluation.process_mastery.search_attempt_export",
                fromlist=["export_attempt_details"]).export_attempt_details(
                    {"graph": agent.native.graph_to_dict()})}
               if export_attempt_details else {})}
    finally:
        if rule_capture is not None:
            rule_capture.close()
        del agent

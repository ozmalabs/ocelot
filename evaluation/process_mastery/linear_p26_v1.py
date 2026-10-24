"""P26 matched evidence-selection and bounded native process-search runner."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
for _path in (ROOT, ROOT / "runners/dsl/python"):
    if str(_path) not in sys.path:
        sys.path.insert(0, _path)

import substrate_rs
from evaluation.process_mastery.common_target_learner import CommonTargetLearner
from evaluation.process_mastery.evidence_search_worlds import (
    FAMILIES, EvidenceSearchWorld, generate_evidence_search_pool, selector_views,
)
from evaluation.process_mastery.runtime_attestation import attest
from evaluation.process_mastery.target_learning_worlds import WorldReceipt
from scripts.gen_useful_evidence_selection_seed import build_seed as useful_evidence_seed
from evaluation.process_mastery.harness import Agent
from substrate.boot_core import CORE_SEEDS
from evaluation.process_mastery.native_process_execution import execute_open_process_candidate

PHASE = "linear-p26-v1"
PREREGISTRATION = "docs/research/engine_substrate/COGNITION_LINEAR_P26_PREREG.md"
RAW_HELDOUT = "evaluation/process_mastery/results/p26_linear_v1_heldout_20261025.json"
HELDOUT_MARKER = "evaluation/process_mastery/results/.p26_v1_heldout_run_started"
ARMS = ("residual", "fixed", "random")
LOADS = {"low": 4, "high": 8}
CHECKPOINTS = (0, 1, 2, 4)
HELDOUT_STREAMS_PER_CELL = 200
DEVELOPMENT_STREAMS_PER_CELL = 2
HELDOUT_CONTROLS_PER_KIND = 100
DEVELOPMENT_CONTROLS_PER_KIND = 2
CONTROL_KINDS = ("heldout_selector_guard", "receipt_replay", "approval_boundary")
SEED_BASES = {"development": 150_000_000, "heldout": 160_000_000}
CONTROL_BASES = {"development": 170_000_000, "heldout": 171_000_000}
SHARED_BUDGET = 32.0
SELECTOR_SELECTION_LIMIT = 4
NATIVE_SEARCH_ATTEMPT_LIMIT = 32
NATIVE_SEARCH_PER_TASK_LIMIT = 4
NATIVE_RULE_STEPS_LIMIT = 250_000
GRAPH_BYTES_LIMIT = 2_000_000
BOOTSTRAPS = 20_000
BOOTSTRAP_SEED = 26_010_251

# Prior numeric allocations recorded by P16–P25. P20/P21 use protocol-owned
# string IDs; P22 uses the 32m block covered below.
PRIOR_NUMERIC_INTERVALS = (
    (26_000_000, 28_999_999), (29_000_000, 29_999_999),
    (31_000_000, 33_999_999), (41_000_000, 43_999_999),
    (90_000_000, 97_999_999), (110_000_000, 131_999_999),
)

PROFILE_SEEDS = (
    "thinking_budget", "process_induction", "target_learning",
    "common_target_evidence", "useful_evidence_selection",
    "open_process_search", "open_process_adoption", "process_solving",
    "process_schema", "invention_operators", "invention_round",
    "invariant_miner", "independent_improvement",
)
PROVENANCE_FILES = (
    "evaluation/process_mastery/linear_p26_v1.py",
    "evaluation/process_mastery/analyze_linear_p26_v1.py",
    "evaluation/process_mastery/evidence_search_worlds.py",
    "evaluation/process_mastery/common_target_learner.py",
    "evaluation/process_mastery/target_learner.py",
    "evaluation/process_mastery/target_learning_worlds.py",
    "evaluation/process_mastery/native_process_execution.py",
    "evaluation/process_mastery/harness.py",
    "evaluation/process_mastery/runtime_attestation.py",
    "scripts/gen_useful_evidence_selection_seed.py", "seeds/useful_evidence_selection.json",
    "scripts/gen_common_target_evidence_seed.py", "seeds/common_target_evidence.json",
    "scripts/gen_open_process_search_seed.py", "seeds/open_process_search.json",
    "scripts/gen_open_process_adoption_seed.py", "seeds/open_process_adoption.json",
    "scripts/gen_process_induction_seed.py", "seeds/process_induction.json",
    "substrate/boot_core.py", "substrate/boot_profiles.py", "substrate/seed_loader.py",
    "seeds/cognition_on_params.json",
    "docs/research/engine_substrate/COGNITION_EVIDENCE_SEARCH_CONTRACT.md",
    "docs/research/engine_substrate/PMB_V1_SPEC.md",
    "runners/dsl/python/substrate_rs/__init__.py",
    "runners/dsl/python/substrate_rs/_native.build.json",
    "runners/dsl/Cargo.toml", "runners/dsl/pyproject.toml", "runners/dsl/uv.lock",
    "tests/test_linear_p26_v1.py", "tests/test_evidence_search_worlds.py",
    "tests/test_diagnosed_process_search.py", "tests/test_useful_evidence_selection.py",
)


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _digest(value: Any) -> str:
    return _sha(json.dumps(value, sort_keys=True, separators=(",", ":"),
                           ensure_ascii=False, default=str).encode())


def _loaded_seed_closure(*roots: str) -> list[str]:
    """Return the exact manifest dependency closure boot_core loads for roots.

    The legacy PMB ``Agent`` loader installs manifests without adding Seed
    bookkeeping nodes, so ``installed_seeds`` alone is empty on these fresh
    graphs. Resolve the same registry roots boot_core used instead of claiming
    that no seeds were loaded.
    """
    from substrate.seed_loader import manifest_for

    loaded = set()
    resolving = set()

    def visit(seed_id: str) -> None:
        if seed_id == "core" or seed_id in loaded:
            return
        if seed_id in resolving:
            raise ValueError(f"cyclic seed manifest dependency: {seed_id}")
        resolving.add(seed_id)
        manifest = manifest_for(seed_id)
        for dependency in manifest.get("depends_on", ()):
            visit(str(dependency))
        resolving.remove(seed_id)
        loaded.add(seed_id)

    for root in (*CORE_SEEDS, *roots):
        visit(root)
    return sorted(loaded)


def _commit() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                   text=True).strip()


def allocation(split: str, *, streams_per_cell: int | None = None,
               controls_per_kind: int | None = None) -> dict:
    if split not in {"development", "heldout"}:
        raise ValueError("split must be development or heldout")
    if split == "heldout":
        if streams_per_cell not in {None, HELDOUT_STREAMS_PER_CELL}:
            raise ValueError("held-out allocation is frozen at 200 per family/load cell")
        if controls_per_kind not in {None, HELDOUT_CONTROLS_PER_KIND}:
            raise ValueError("held-out integrity controls are frozen at 100 per kind")
        streams_per_cell, controls_per_kind = (HELDOUT_STREAMS_PER_CELL,
                                               HELDOUT_CONTROLS_PER_KIND)
    else:
        streams_per_cell = streams_per_cell or DEVELOPMENT_STREAMS_PER_CELL
        controls_per_kind = controls_per_kind or DEVELOPMENT_CONTROLS_PER_KIND
    if streams_per_cell <= 0 or controls_per_kind <= 0:
        raise ValueError("P26 stream and integrity-control allocations must be positive")
    cells = []
    for family_index, family in enumerate(FAMILIES):
        for load_index, (load, pool_size) in enumerate(LOADS.items()):
            seeds = [SEED_BASES[split] + family_index * 1_000_000
                     + load_index * 10_000 + draw
                     for draw in range(streams_per_cell)]
            cells.append({"family": family, "load_stratum": load,
                "pool_size": pool_size, "stream_ids": [f"p26:{split}:{seed}" for seed in seeds],
                "stream_seeds": seeds, "train_pool_seeds": [seed + 2_000_000 for seed in seeds],
                "heldout_pool_seeds": [seed + 4_000_000 for seed in seeds],
                "arms": list(ARMS)})
    controls = {kind: [CONTROL_BASES[split] + index * 1_000 + draw
                       for draw in range(controls_per_kind)]
                for index, kind in enumerate(CONTROL_KINDS)}
    all_seeds = [seed for cell in cells for key in
                 ("stream_seeds", "train_pool_seeds", "heldout_pool_seeds")
                 for seed in cell[key]]
    all_seeds.extend(seed for values in controls.values() for seed in values)
    for seed in all_seeds:
        if any(lo <= seed <= hi for lo, hi in PRIOR_NUMERIC_INTERVALS):
            raise RuntimeError(f"P26 allocation overlaps prior numeric seed {seed}")
    if len(all_seeds) != len(set(all_seeds)):
        raise RuntimeError("P26 allocation contains duplicate numeric seed IDs")
    return {"phase": PHASE, "split": split, "families": list(FAMILIES),
        "load_strata": dict(LOADS), "arms": list(ARMS), "stream_cells": cells,
        "streams_per_family_load_cell": streams_per_cell,
        "controls_per_kind": controls_per_kind, "control_seeds": controls,
        "checkpoints": list(CHECKPOINTS), "shared_budget": SHARED_BUDGET,
        "selector_selection_limit": SELECTOR_SELECTION_LIMIT,
        "native_search_attempt_limit": NATIVE_SEARCH_ATTEMPT_LIMIT,
        "native_search_per_task_limit": NATIVE_SEARCH_PER_TASK_LIMIT}


def provenance() -> dict:
    selector_seeds = _loaded_seed_closure("process_induction", "target_learning",
        "common_target_evidence", "additive_transfer", "useful_evidence_selection")
    search_seeds = _loaded_seed_closure("open_process_search")
    loaded_seeds = sorted(set(selector_seeds) | set(search_seeds))
    source_paths = set(PROVENANCE_FILES)
    for seed_id in loaded_seeds:
        manifest = f"seeds/{seed_id}.json"
        if not (ROOT / manifest).is_file():
            raise RuntimeError(f"P26 loaded seed manifest is missing: {manifest}")
        source_paths.add(manifest)
        for generator in (f"scripts/gen_{seed_id}_seed.py", f"scripts/gen_{seed_id}.py"):
            if (ROOT / generator).is_file():
                source_paths.add(generator)
    source_hashes = {rel: _sha((ROOT / rel).read_bytes())
                     for rel in sorted(source_paths)}
    extension = Path(substrate_rs._native.__file__).resolve()
    build_receipt = extension.parent / "_native.build.json"
    return {"git_commit": _commit(), "source_file_sha256": source_hashes,
        "source_bundle_sha256": _digest(list(source_hashes.items())),
        "runner_sha256": source_hashes["evaluation/process_mastery/linear_p26_v1.py"],
        "analyzer_sha256": source_hashes["evaluation/process_mastery/analyze_linear_p26_v1.py"],
        "loaded_extension_path": str(extension), "loaded_extension_sha256": _sha(extension.read_bytes()),
        "build_receipt_path": str(build_receipt),
        "build_receipt_sha256": _sha(build_receipt.read_bytes()),
        "runtime_attestation": attest(package=substrate_rs, build_receipt=build_receipt,
                                       require_clean=True),
        "profile_seed_ids": list(PROFILE_SEEDS),
        "loaded_seed_closures": {"selector": selector_seeds,
                                  "native_process_search": search_seeds},
        "python": sys.version.split()[0]}


def _graph_bytes(agent) -> int:
    inner = agent.native
    node_ids = inner.nodes()
    nodes = [{"id": node, **inner.node(node)} for node in node_ids]
    seen = set()
    edges = []
    for node in node_ids:
        for row in inner.incident_edges(node):
            key = (row["src"], row["type"], row["tgt"])
            if key not in seen:
                seen.add(key)
                edges.append(row)
    payload = {"nodes": nodes, "edges": edges, "rules": inner.export_rules()}
    return len(json.dumps(payload, sort_keys=True, default=str,
                          separators=(",", ":")).encode())


def run_native_process_search(tasks: list[dict], scorer_rows: list[dict], *,
                              attempt_ceiling: int = NATIVE_SEARCH_ATTEMPT_LIMIT,
                              per_task_ceiling: int = NATIVE_SEARCH_PER_TASK_LIMIT,
                              budget: float = SHARED_BUDGET) -> dict:
    """Run the native open-process search on the same goal pool as selectors.

    The scorer archive is used only to bind each public task to its world ID;
    task solutions and relation labels are not passed into the agent graph.
    Candidate adoption and world execution are deliberately absent.
    """
    if len(tasks) != len(scorer_rows):
        raise ValueError("native-search tasks/scorer bindings differ in length")
    agent = Agent(track_i=False, extra_seeds=("open_process_search",),
        policy_overrides={
            "OpenProcessSearchPolicy": {"enabled": 1.0,
                "max_attempts": float(attempt_ceiling),
                "max_attempts_per_request": float(per_task_ceiling),
                "max_candidates": 32.0, "effect_dedup_enabled": 1.0},
            "ProcessSchemaPolicy": {"enabled": 1.0}},
        budget={"enabled": 1.0, "remaining": float(budget),
            "capacity": float(budget), "last_refill_epoch": 0.0,
            "refill_per_epoch": 0.0}, profile="p26-native-search")
    started = time.perf_counter()
    native_steps = 0
    try:
        for index, (task, scorer) in enumerate(zip(tasks, scorer_rows)):
            if task["world_id"] != scorer["world_id"]:
                raise ValueError("native search received a task/scorer mismatch")
            held = {name: list(task["primitive_effects"][name])
                    for name in task["primitive_affordances"]}
            domain_name = f"p26-native-{index}-{_digest(task['world_id'])[:12]}"
            domain = agent.add_domain(domain_name, "permutation",
                [list(task["initial_state"])], held)
            for schema in agent.nodes("ProcessSchema", domain=domain_name):
                agent.s.add_edge(domain, "has_held_process", schema, {})
            solve_task = agent.add_solve_task(domain_name, list(task["initial_state"]),
                list(task["goal_state"]), split="training",
                training_trial_key=task["world_id"])
            agent.s.set_attr(solve_task, "status", "stuck")
        for _ in range(40):
            result = agent.native.run_rules_report(4000, False)
            native_steps += int(result.get("progress_steps", 0))
            if int(result.get("progress_steps", 0)) == 0:
                break
        attempt_nodes = agent.nodes("OpenProcessSearchAttempt")
        attempts = []
        for node in attempt_nodes:
            attrs = agent.attrs(node)
            task_nodes = agent.native.neighbours(node, "about_task")
            attempts.append({"node_id": str(node), **attrs,
                "task_node_ids": [str(task) for task in task_nodes],
                "task_world_ids": [agent.attrs(task).get("training_trial_key")
                                   for task in task_nodes]})
        candidate_nodes = agent.nodes("OpenProcessCandidate")
        candidates = [{"node_id": str(node), **agent.attrs(node),
            "derivation_attempt_ids": [str(attempt) for attempt in
                agent.native.neighbours(node, "derived_from_attempt")]} for node in candidate_nodes]
        approvals = agent.nodes("OpenProcessAdoptionApproval")
        receipts = agent.nodes("OpenProcessWorldReceipt")
        verified_effects = {json.dumps(row.get("effect_digest"), sort_keys=True,
                                      separators=(",", ":"))
            for row in candidates if row.get("expression_digest_status") == "verified"
            and row.get("effect_digest") is not None}
        budgets = [agent.attrs(node) for node in agent.nodes("ThinkingBudget")]
        requests = [agent.attrs(node) for node in agent.nodes("ThinkingBudgetRequest")
                    if agent.attrs(node).get("requester_kind") == "open_process_search"]
        gate_probe = {"status": "NO_CANDIDATE", "authorize_calls": 0,
                      "world_transition_calls": 0}
        if candidate_nodes:
            calls = {"authorize": 0, "world_transition": 0}
            gate_probe = execute_open_process_candidate(agent, candidate_nodes[0],
                state=agent.attrs(candidate_nodes[0]).get("guard_state"),
                authorize=lambda proposal: calls.__setitem__("authorize",
                    calls["authorize"] + 1) or True,
                world_transition=lambda proposed: calls.__setitem__("world_transition",
                    calls["world_transition"] + 1) or {"observed_state": proposed})
            gate_probe = {**gate_probe, "authorize_calls": calls["authorize"],
                          "world_transition_calls": calls["world_transition"]}
        return {"status": "complete", "attempts": len(attempts),
            "attempt_statuses": {status: sum(row.get("status") == status for row in attempts)
                                 for status in sorted({row.get("status") for row in attempts})},
            "candidate_proposals": len(candidates),
            "unique_verified_effects": len(verified_effects),
            "qualified_candidates": sum(row.get("status") == "qualified" for row in candidates),
            "adoption_approvals": len(approvals), "world_receipts": len(receipts),
            "budget_remaining": budgets[0].get("remaining") if len(budgets) == 1 else None,
            "budget_debited": sum(float(row.get("cost", 0.0))
                for row in requests if row.get("status") == "approved"),
            "search_requests": requests, "attempt_records": attempts,
            "candidate_records": candidates, "candidate_gate_probe": gate_probe,
            "native_rule_steps": native_steps,
            "graph_nodes": len(agent.native.nodes()), "graph_edges": agent.native.edge_count(),
            "graph_serialized_bytes": _graph_bytes(agent),
            "loaded_seed_ids": _loaded_seed_closure("open_process_search"),
            "elapsed_seconds": time.perf_counter() - started,
            "unseen_binding_use": 0,
            "unseen_binding_use_status": "not_authorized_without_candidate_specific_approval"}
    finally:
        del agent


def _add_opportunity(learner, row: dict) -> int:
    node = learner.s.add_node("UsefulEvidenceOpportunity", dict(row))
    learner.s.add_edge(learner.ag, "has_useful_evidence_opportunity", node, {})
    return node


def _learned_state_digest(learner) -> str:
    rows = [learner.s.node(node)["attrs"] for node in learner.s.nodes("ProcessInductionHypothesis")]
    return _digest(sorted(rows, key=lambda row: json.dumps(row, sort_keys=True, default=str)))


def _select_and_deliver(learner, world_by_opportunity, *, mode: str,
                        max_selections: int) -> dict:
    policies = learner.s.nodes("UsefulEvidenceSelectionPolicy")
    if len(policies) != 1:
        raise RuntimeError("P26 learner requires one native evidence-selection policy")
    policy = policies[0]
    learner.s.set_attr(policy, "enabled", 1.0)
    learner.s.set_attr(policy, "selector_mode", mode)
    budget = learner.s.neighbours(learner.ag, "has_thinking_budget")
    if len(budget) != 1:
        raise RuntimeError("P26 selector requires exactly one shared ThinkingBudget")
    selector_rows = []
    cumulative_receipts = 0
    native_steps = 0
    for checkpoint in range(max_selections):
        learner.s.set_attr(policy, "pool_id", world_by_opportunity["pool_id"])
        native_steps += learner.settle()
        pending = [node for node in learner.s.nodes("UsefulEvidenceSelection")
                   if learner.s.node(node)["attrs"].get("status") == "awaiting_receipt"]
        if not pending:
            selector_rows.append({"checkpoint": checkpoint + 1,
                "status": "no_eligible_native_signal" if mode == "residual" else "selection_not_funded"})
            continue
        selection_node = pending[-1]
        selection = learner.s.node(selection_node)["attrs"]
        opportunity_key = selection["opportunity_key"]
        opportunity = world_by_opportunity["rows"].get(opportunity_key)
        external_world = world_by_opportunity["worlds"].get(opportunity_key)
        if opportunity is None or external_world is None:
            raise RuntimeError("selected opportunity is absent from the frozen task pool")
        request_nodes = learner.s.neighbours(selection_node, "has_budget_request")
        if len(request_nodes) != 1 or learner.s.node(request_nodes[0])["attrs"].get("status") != "approved":
            selector_rows.append({"checkpoint": checkpoint + 1,
                "status": "budget_denied", "opportunity_key": opportunity_key})
            break
        before_state = _learned_state_digest(learner)
        heldout_query = f"p26-behavior-before:{mode}:{checkpoint}"
        prediction_before = learner.predict(query_id=heldout_query,
            action_kind=selection["action_kind"], object_type=selection["object_type"],
            feature_key=selection["feature_key"], before_value=selection["before_value"],
            object_id=f"fresh:{heldout_query}", source_epoch=selection["source_epoch"],
            model_epoch=selection["model_epoch"], frame_epoch=selection["frame_epoch"],
            split="development")
        receipt = external_world.execute(opportunity)
        if not external_world.verify_receipt(receipt):
            raise RuntimeError("external training receipt failed world verification")
        if not isinstance(receipt, WorldReceipt):
            raise RuntimeError("external world returned a non-native receipt record")
        learner.observe_world_receipt(receipt, source_epoch=selection["source_epoch"],
            model_epoch=selection["model_epoch"], frame_epoch=selection["frame_epoch"],
            split="training")
        native_steps += learner.settle()
        prediction_after = learner.predict(query_id=f"p26-behavior-after:{mode}:{checkpoint}",
            action_kind=selection["action_kind"], object_type=selection["object_type"],
            feature_key=selection["feature_key"], before_value=selection["before_value"],
            object_id=f"fresh-after:{mode}:{checkpoint}",
            source_epoch=selection["source_epoch"], model_epoch=selection["model_epoch"],
            frame_epoch=selection["frame_epoch"], split="development")
        after_state = _learned_state_digest(learner)
        before_behavior = (prediction_before or {}).get("expected_after_value")
        after_behavior = (prediction_after or {}).get("expected_after_value")
        state_changed = before_state != after_state
        behavior_changed = before_behavior != after_behavior
        outcome = learner.s.add_node("UsefulEvidenceLearningOutcome", {
            "event_id": receipt.event_id, "status": "observed",
            "assessment": "useful_progress" if state_changed and behavior_changed else "no_progress",
            "split": "training", "source_epoch": selection["source_epoch"],
            "model_epoch": selection["model_epoch"], "frame_epoch": selection["frame_epoch"],
            "learned_state_changed": state_changed, "behavior_changed": behavior_changed,
            "before_state_digest": before_state, "after_state_digest": after_state,
            "before_behavior_digest": _digest(before_behavior),
            "after_behavior_digest": _digest(after_behavior)})
        evidence = [node for node in learner.s.nodes("CommonTargetEvidence")
                    if learner.s.node(node)["attrs"].get("event_id") == receipt.event_id]
        if len(evidence) != 1:
            raise RuntimeError("common learner did not retain exactly one selected receipt")
        learner.s.add_edge(learner.ag, "has_useful_evidence_learning_outcome", outcome, {})
        learner.s.add_edge(selection_node, "has_outcome", outcome, {})
        learner.s.add_edge(outcome, "outcome_for_selection", selection_node, {})
        learner.s.add_edge(outcome, "based_on_target_evidence", evidence[0], {})
        native_steps += learner.settle()
        cumulative_receipts += 1
        selector_rows.append({"checkpoint": checkpoint + 1,
            "status": learner.s.node(selection_node)["attrs"].get("status"),
            "opportunity_key": opportunity_key, "receipt_event_id": receipt.event_id,
            "learned_state_changed": state_changed, "behavior_changed": behavior_changed,
            "native_state_digest_before": before_state, "native_state_digest_after": after_state,
            "prediction_before": before_behavior, "prediction_after": after_behavior,
            "budget_request": learner.s.node(request_nodes[0])["attrs"],
        })
    return {"rows": selector_rows, "receipts": cumulative_receipts,
        "native_rule_steps": native_steps,
        "budget_remaining": learner.s.node(budget[0])["attrs"].get("remaining")}


def _one_opportunity(task: dict, action: str) -> dict:
    rows = [row for row in task["evidence_opportunities"]
            if row["action_kind"] == action]
    if len(rows) != 1:
        raise RuntimeError(f"world {task['world_id']} lacks unique {action} opportunity")
    return rows[0]


def _test_curve(learner, *, family: str, initial_state: tuple[int, ...],
                heldout_seed: int, work_points: tuple[int, ...]) -> list[dict]:
    maximum = max(work_points)
    pool = generate_evidence_search_pool(split="heldout",
        draws=range(maximum + 1), seed=heldout_seed, family=family,
        initial_state=initial_state)
    curve = []
    for checkpoint in work_points:
        task = pool.task_pool()[checkpoint]
        scorer = pool.scorer_only[checkpoint]
        opportunity = _one_opportunity(task, "act_0")
        query = learner.predict(query_id=f"p26-heldout-query:{heldout_seed}:{checkpoint}",
            action_kind="act_0", object_type=opportunity["object_type"],
            feature_key="state", before_value=opportunity["before_value"],
            object_id=f"p26-heldout-binding:{heldout_seed}:{checkpoint}",
            source_epoch=1, model_epoch=1, frame_epoch=1, split="heldout")
        prediction = (query or {}).get("expected_after_value")
        world = EvidenceSearchWorld(task, scorer)
        receipt = world.execute(opportunity)
        if not world.verify_receipt(receipt):
            raise RuntimeError("held-out scoring receipt failed external verification")
        curve.append({"cumulative_selection_work": checkpoint,
            "status": "scored", "prediction": prediction,
            "scorer_outcome": receipt.after_value,
            "success": prediction == receipt.after_value if prediction is not None else False,
            "prediction_missing": prediction is None,
            "world_id": task["world_id"], "split": "heldout"})
    return curve


def run_selector_stream(*, mode: str, family: str, load: str,
                        train_seed: int, heldout_seed: int,
                        pool_size: int | None = None) -> dict:
    """Run one selector arm on its fixed pool and score fresh sealed bindings."""
    if mode not in ARMS or family not in FAMILIES or load not in LOADS:
        raise ValueError("unknown P26 arm or stratum")
    pool_size = int(pool_size or LOADS[load])
    size = 7 if family == "cyclic_relation" else 9
    initial = tuple(range(size))
    training_pool = generate_evidence_search_pool(split="train",
        draws=range(pool_size), seed=train_seed, family=family,
        initial_state=initial)
    views = selector_views(training_pool)
    if any(views[mode] != views[other] for other in ARMS):
        raise RuntimeError("P26 selector arms do not have identical task/opportunity access")
    tasks = views[mode]
    world_by_opportunity = {"pool_id": training_pool.pool_id,
        "rows": {}, "worlds": {}}
    started = time.perf_counter()
    learner = CommonTargetLearner(owner_id=f"p26:{train_seed}:{mode}",
        budget=SHARED_BUDGET, enabled=True, policy_enabled=True)
    try:
        graph_bytes_at_boot = _graph_bytes(learner.agent)
        loaded = learner.s._inner.load_seed_manifest(useful_evidence_seed(), learner.ag)
        if loaded.get("rules_skipped"):
            raise RuntimeError("P26 selector seed did not load completely")
        policies = learner.s.nodes("UsefulEvidenceSelectionPolicy")
        if len(policies) != 1:
            raise RuntimeError("P26 stream requires one selector policy")
        policy = policies[0]
        learner.s.set_attr(policy, "enabled", 0.0)
        learner.s.set_attr(policy, "selector_mode", mode)
        learner.s.set_attr(policy, "pool_id", training_pool.pool_id)
        learner.s.set_attr(policy, "max_selections", float(SELECTOR_SELECTION_LIMIT))

        # The same three world-owned training receipts seed the native model and
        # the residual signal opportunity in every arm. They are fixed, charged
        # common exposure and excluded from the selector's remaining pool.
        baseline_pool = generate_evidence_search_pool(split="train", draws=(1, 7, 0),
            seed=train_seed + 900_000, family=family, initial_state=initial)
        baseline_tasks = baseline_pool.task_pool()
        baseline_receipts = []
        for draw in (1, 7, 0):
            index = (1, 7, 0).index(draw)
            task, scorer = baseline_tasks[index], baseline_pool.scorer_only[index]
            opportunity = _one_opportunity(task, "act_0")
            world = EvidenceSearchWorld(task, scorer)
            if draw == 0:
                learner.predict(query_id=f"p26-native-disagreement:{train_seed}",
                    action_kind="act_0", object_type=opportunity["object_type"],
                    feature_key="state", before_value=opportunity["before_value"],
                    object_id=f"p26-disagreement-query:{train_seed}",
                    source_epoch=1, model_epoch=1, frame_epoch=1, split="training")
            receipt = world.execute(opportunity)
            if not world.verify_receipt(receipt):
                raise RuntimeError("fixed baseline training receipt failed world verification")
            learner.observe_world_receipt(receipt, source_epoch=1, model_epoch=1,
                frame_epoch=1, split="training")
            learner.settle()
            baseline_receipts.append({"event_id": receipt.event_id,
                "world_id": task["world_id"], "status": receipt.status,
                "action_authorized": receipt.action_authorized,
                "outcome_digest": _digest(receipt.after_value)})

        available_ids = []
        for task in tasks:
            scorer = next(row for row in training_pool.scorer_only
                          if row["world_id"] == task["world_id"])
            world = EvidenceSearchWorld(task, scorer)
            for opportunity in task["evidence_opportunities"]:
                row = dict(opportunity)
                _add_opportunity(learner, row)
                world_by_opportunity["rows"][row["opportunity_key"]] = row
                world_by_opportunity["worlds"][row["opportunity_key"]] = world
                available_ids.append(row["opportunity_key"])
        # Copy selector ranks from the registered pool identity, not task answers.
        learner.settle()
        graph_bytes_before_selection = _graph_bytes(learner.agent)
        initial_state_digest = _learned_state_digest(learner)
        curve_before = _test_curve(learner, family=family, initial_state=initial,
                                   heldout_seed=heldout_seed, work_points=(0,))
        learner.s.set_attr(policy, "enabled", 1.0)
        selection_result = _select_and_deliver(learner, world_by_opportunity,
            mode=mode, max_selections=SELECTOR_SELECTION_LIMIT)
        after_points = tuple(point for point in CHECKPOINTS if point > 0)
        curve_after = _test_curve(learner, family=family, initial_state=initial,
            heldout_seed=heldout_seed, work_points=after_points)
        curve = curve_before + curve_after
        areas = [float(bool(row["success"])) for row in curve]
        normalized_auc = sum((CHECKPOINTS[i] - CHECKPOINTS[i - 1])
            * (areas[i] + areas[i - 1]) / 2 for i in range(1, len(CHECKPOINTS))) / CHECKPOINTS[-1]
        requests = [learner.s.node(node)["attrs"]
                    for node in learner.s.nodes("ThinkingBudgetRequest")]
        graph_bytes_final = _graph_bytes(learner.agent)
        return {"status": "complete", "arm": mode, "family": family,
            "load_stratum": load, "pool_size": pool_size,
            "train_pool_id": training_pool.pool_id,
            "train_pool_sha256": training_pool.pool_sha256,
            "available_opportunity_ids": available_ids,
            "selected_opportunity_ids": [row.get("opportunity_key")
                for row in selection_result["rows"] if row.get("opportunity_key")],
            "baseline_receipts": baseline_receipts,
            "curve": curve, "selection_rows": selection_result["rows"],
            "selection_receipts": selection_result["receipts"],
            "native_rule_steps": learner.accounting.native_rule_steps,
            "selection_rule_steps": selection_result["native_rule_steps"],
            "budget_remaining": selection_result["budget_remaining"],
            "budget_requests": requests,
            "budget_debited": sum(float(row.get("cost", 0.0))
                for row in requests if row.get("status") == "approved"),
            "selection_budget_debited": sum(float(row.get("cost", 0.0))
                for row in requests if row.get("status") == "approved"
                and row.get("requester_kind") == "useful_evidence_selection"),
            "normalized_auc": normalized_auc,
            "initial_state_digest": initial_state_digest,
            "final_state_digest": _learned_state_digest(learner),
            "source_exposures": len(learner.s.nodes("TargetSourceExposure")),
            "graph_nodes": len(learner.s.nodes()), "graph_edges": learner.s._inner.edge_count(),
            "graph_serialized_bytes": graph_bytes_final,
            "graph_bytes_at_boot": graph_bytes_at_boot,
            "graph_bytes_before_selection": graph_bytes_before_selection,
            "graph_memory_growth_bytes": graph_bytes_final - graph_bytes_at_boot,
            "loaded_seed_ids": _loaded_seed_closure("process_induction", "target_learning",
                "common_target_evidence", "additive_transfer", "useful_evidence_selection"),
            "elapsed_seconds": time.perf_counter() - started,
        }
    finally:
        del learner


def run_stream(*, stream_id: str, family: str, load: str,
               train_seed: int, heldout_seed: int) -> dict:
    pool_size = LOADS[load]
    size = 7 if family == "cyclic_relation" else 9
    initial = tuple(range(size))
    pool = generate_evidence_search_pool(split="train",
        draws=range(pool_size), seed=train_seed, family=family,
        initial_state=initial)
    arms = [run_selector_stream(mode=mode, family=family, load=load,
        train_seed=train_seed, heldout_seed=heldout_seed, pool_size=pool_size)
        for mode in ARMS]
    arm_views = {row["arm"]: row for row in arms}
    shared_ids = {mode: tuple(arm_views[mode]["available_opportunity_ids"]) for mode in ARMS}
    if len(set(shared_ids.values())) != 1:
        raise RuntimeError("selector arms received different available opportunity IDs")
    search = run_native_process_search(pool.task_pool(), pool.scorer_only,
        attempt_ceiling=NATIVE_SEARCH_ATTEMPT_LIMIT,
        per_task_ceiling=NATIVE_SEARCH_PER_TASK_LIMIT, budget=SHARED_BUDGET)
    search.update({"training_pool_id": pool.pool_id,
        "training_pool_sha256": pool.pool_sha256,
        "task_world_ids": [task["world_id"] for task in pool.task_pool()]})
    return {"stream_id": stream_id, "family": family,
        "load_stratum": load, "pool_size": pool_size,
        "train_pool_id": pool.pool_id, "train_pool_sha256": pool.pool_sha256,
        "arms": arms, "available_opportunity_ids": list(next(iter(shared_ids.values()))),
        "native_search": search}


def run_integrity_controls(split: str, control_seeds: dict[str, list[int]],
                           search_reference: dict) -> list[dict]:
    """Run frozen data-boundary, receipt-replay, and approval-scope controls."""
    rows = []
    for seed in control_seeds["heldout_selector_guard"]:
        heldout = generate_evidence_search_pool(split="heldout", draws=(0,), seed=seed,
            family="cyclic_relation", initial_state=tuple(range(7)))
        try:
            selector_views(heldout)
            status = "FAIL"
        except ValueError:
            status = "PASS"
        rows.append({"kind": "heldout_selector_guard", "seed": seed,
                     "status": status, "heldout_pool_sha256": heldout.pool_sha256})

    # One actual verified training receipt is ingested once; each replay is a
    # separately counted idempotent control and cannot add exposure or state.
    receipt_pool = generate_evidence_search_pool(split="train", draws=(1,),
        seed=control_seeds["receipt_replay"][0], family="cyclic_relation",
        initial_state=tuple(range(7)))
    receipt_task = receipt_pool.task_pool()[0]
    receipt_world = EvidenceSearchWorld(receipt_task, receipt_pool.scorer_only[0])
    receipt = receipt_world.execute(_one_opportunity(receipt_task, "act_0"))
    learner = CommonTargetLearner(owner_id=f"p26-control:{split}", budget=SHARED_BUDGET)
    try:
        learner.observe_world_receipt(receipt, source_epoch=1, model_epoch=1,
                                      frame_epoch=1, split="training")
        learner.settle()
        for seed in control_seeds["receipt_replay"]:
            before = len(learner.s.nodes("CommonTargetEvidence"))
            before_observations = learner.accounting.visible_observations
            replay_node = learner.observe_world_receipt(receipt, source_epoch=1, model_epoch=1,
                                                        frame_epoch=1, split="training")
            after = len(learner.s.nodes("CommonTargetEvidence"))
            after_observations = learner.accounting.visible_observations
            status = "PASS" if (after == before and after_observations == before_observations
                and replay_node in learner.s.nodes("CommonTargetEvidence")) else "FAIL"
            rows.append({"kind": "receipt_replay", "seed": seed, "status": status,
                "evidence_count_before": before, "evidence_count_after": after,
                "observations_before": before_observations,
                "observations_after": after_observations,
                "replay_added_exposure": (after != before
                    or after_observations != before_observations),
                "replay_disposition": "deduplicated", "returned_evidence_node": str(replay_node)})
    finally:
        del learner

    # Adoption remains exactly candidate-bound. Without a user-bound approval,
    # no candidate can produce a simulated adoption or world receipt.
    for seed in control_seeds["approval_boundary"]:
        approvals = int(search_reference.get("adoption_approvals", -1))
        receipts = int(search_reference.get("world_receipts", -1))
        probe = search_reference.get("candidate_gate_probe", {})
        denied_without_side_effects = (probe.get("status") == "ABSTAIN"
            and probe.get("reason") == "candidate_not_adopted"
            and probe.get("authorize_calls") == 0
            and probe.get("world_transition_calls") == 0)
        no_candidate_available = (probe.get("status") == "NO_CANDIDATE"
            and search_reference.get("candidate_proposals") == 0)
        status = "PASS" if approvals == 0 and receipts == 0 and (
            denied_without_side_effects or no_candidate_available) else "FAIL"
        rows.append({"kind": "approval_boundary", "seed": seed,
            "status": status, "adoption_approvals": approvals, "world_receipts": receipts,
            "candidate_proposals": search_reference.get("candidate_proposals"),
            "candidate_gate_probe": probe,
            "probe_scope": "candidate_execution_denied" if denied_without_side_effects
                else "no_candidate_available",
            "reason": "no candidate-specific approval was supplied"})
    return rows


def run_payload(split: str, *, streams_per_cell: int | None = None,
                controls_per_kind: int | None = None) -> dict:
    plan = allocation(split, streams_per_cell=streams_per_cell,
                      controls_per_kind=controls_per_kind)
    streams = []
    for cell in plan["stream_cells"]:
        for index, (stream_id, train_seed, heldout_seed) in enumerate(zip(
                cell["stream_ids"], cell["train_pool_seeds"], cell["heldout_pool_seeds"])):
            streams.append(run_stream(stream_id=stream_id, family=cell["family"],
                load=cell["load_stratum"], train_seed=train_seed,
                heldout_seed=heldout_seed))
    search_reference = next((stream["native_search"] for stream in streams
        if stream["native_search"].get("candidate_records")),
        streams[0]["native_search"] if streams else {
            "adoption_approvals": 0, "world_receipts": 0, "candidate_proposals": 0,
            "candidate_gate_probe": {"status": "NO_CANDIDATE"}})
    controls = run_integrity_controls(split, plan["control_seeds"], search_reference)
    return {"phase": PHASE, "split": split,
        "status": "development_only" if split == "development" else "heldout_pending_analysis",
        "heldout_accessed": split == "heldout", "allocation_plan": plan,
        "provenance": provenance(), "streams": streams,
        "integrity_controls": controls,
        "summary": {"stream_count": len(streams),
            "selector_arm_rows": sum(len(row["arms"]) for row in streams),
            "native_search_rows": sum("native_search" in row for row in streams),
            "control_count": len(controls)}}


def _assert_heldout_preregistration_committed() -> None:
    prereg = ROOT / PREREGISTRATION
    if not prereg.is_file():
        raise RuntimeError("P26 held-out run requires the standalone preregistration")
    head = _commit()
    parent = subprocess.check_output(["git", "rev-parse", f"{head}^"], cwd=ROOT,
                                    text=True).strip()
    names = subprocess.check_output(["git", "diff-tree", "--no-commit-id", "--name-only",
        "-r", head], cwd=ROOT, text=True).splitlines()
    if names != [PREREGISTRATION]:
        raise RuntimeError("the latest commit must contain only the P26 preregistration")
    committed = subprocess.check_output(["git", "show", f"{head}:{PREREGISTRATION}"],
                                        cwd=ROOT)
    if committed != prereg.read_bytes():
        raise RuntimeError("working preregistration differs from its committed bytes")
    document = _parse_preregistration_freeze(committed)
    if document.get("code_commit") != parent:
        raise RuntimeError("P26 preregistration is not immediately after its frozen code commit")
    current = provenance()
    expected_hashes = document.get("source_file_sha256", {})
    if (expected_hashes != current["source_file_sha256"]
            or document.get("source_bundle_sha256") != current["source_bundle_sha256"]):
        raise RuntimeError("P26 runner/source hashes differ from the preregistered freeze")
    if document.get("allocation_sha256") != _digest(allocation("heldout")):
        raise RuntimeError("held-out allocation differs from the preregistered seed matrix")


def _parse_preregistration_freeze(committed: bytes) -> dict:
    """Read the one machine-bound freeze record from the Markdown preregistration."""
    prefix = "P26_FREEZE_JSON: "
    records = [line[len(prefix):] for line in committed.decode("utf-8").splitlines()
               if line.startswith(prefix)]
    if len(records) != 1:
        raise RuntimeError("P26 preregistration must contain one P26_FREEZE_JSON record")
    try:
        value = json.loads(records[0])
    except json.JSONDecodeError as exc:
        raise RuntimeError("P26 preregistration freeze record is invalid JSON") from exc
    if not isinstance(value, dict):
        raise RuntimeError("P26 preregistration freeze record must be a JSON object")
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--split", choices=("development", "heldout"), required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--streams-per-cell", type=int)
    parser.add_argument("--controls-per-kind", type=int)
    args = parser.parse_args()
    if args.split == "heldout":
        _assert_heldout_preregistration_committed()
        if args.streams_per_cell not in {None, HELDOUT_STREAMS_PER_CELL}:
            parser.error("held-out streams per cell are frozen at 200")
        if args.controls_per_kind not in {None, HELDOUT_CONTROLS_PER_KIND}:
            parser.error("held-out controls per kind are frozen at 100")
    output = args.output or ROOT / (RAW_HELDOUT if args.split == "heldout"
                                    else "evaluation/process_mastery/results/p26_linear_v1_development.json")
    marker = ROOT / HELDOUT_MARKER
    if output.exists():
        parser.error("refusing to overwrite an existing P26 result artifact")
    if args.split == "heldout":
        try:
            marker.parent.mkdir(parents=True, exist_ok=True)
            with marker.open("x", encoding="utf-8") as stream:
                stream.write(json.dumps({"phase": PHASE, "status": "attempt_started",
                    "output": str(output.relative_to(ROOT)), "commit": _commit()}) + "\n")
                stream.flush()
                os.fsync(stream.fileno())
        except FileExistsError:
            parser.error("P26 held-out allocation was already claimed")
    payload = run_payload(args.split, streams_per_cell=args.streams_per_cell,
                          controls_per_kind=args.controls_per_kind)
    raw = json.dumps(payload, indent=2, sort_keys=True, default=str, allow_nan=False) + "\n"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(raw, encoding="utf-8")
    print(json.dumps({"output": str(output), "sha256": _sha(raw.encode()),
                      "status": payload["status"], "summary": payload["summary"]},
                     sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

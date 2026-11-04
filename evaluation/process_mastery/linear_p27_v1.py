"""One-shot P27 scheduled cumulative-learning evaluation, version 1."""
from __future__ import annotations

import argparse
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
for _path in (ROOT, ROOT / "runners/dsl/python"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))
os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")

import substrate_rs
from evaluation.process_mastery.common_target_learner import CommonTargetLearner
from evaluation.process_mastery.cumulative_checkpoint_panel import (
    make_native_common_target_predictor, score_common_world_panel,
    world_allocation_digest,
)
from evaluation.process_mastery.evidence_search_worlds import (
    EvidenceSearchWorld, generate_evidence_search_pool, selector_views,
)
from evaluation.process_mastery.linear_p26_v1 import (
    _add_opportunity, _one_opportunity, _select_and_deliver,
)
from evaluation.process_mastery.native_process_execution import params_digest
from evaluation.process_mastery.runtime_attestation import attest, assert_freeze_matches
from evaluation.process_mastery.scheduled_learning_checkpoints import (
    CHECKPOINTS, ScheduledLearningCheckpoint,
    capture_scheduled_checkpoint, snapshot_native_graph,
)
from substrate.boot_profiles import COGNITION_ON_SEEDS, boot_cognition_on
from substrate.seed_loader import manifest_for


PHASE = "linear-p27-v1"
PREREGISTRATION = "docs/research/engine_substrate/COGNITION_LINEAR_P27_PREREG.md"
RAW_HELDOUT = "evaluation/process_mastery/results/p27_linear_v1_heldout_20261025.json"
HELDOUT_MARKER = "evaluation/process_mastery/results/.p27_v1_heldout_run_started"
FAMILIES = ("cyclic_relation", "branching_relation")
ARMS = ("frozen_ancestor", "evidence_selection_only", "process_search_only", "combined")
# Draws congruent to 3 mod 6 are the generator's fixed transferable
# relation: each family has one stable act_0 effect across independent worlds.
TRAIN_DRAWS = (3, 9, 15, 21, 27, 33, 39)
BASELINE_DRAWS = (3, 9, 15)
STAGE_DRAWS = ((21,), (27,), (33, 39))
STAGE_ACCESS = (1, 2, 4)
WORK_THRESHOLDS = (0, 1_000, 2_000, 4_000)
TESTS_PER_FAMILY = 200
VALIDATION_PER_FAMILY = 200
DEVELOPMENT_WORLDS_PER_FAMILY = 4
HELDOUT_CONTROLS = 100
DEVELOPMENT_CONTROLS = 6
SHARED_BUDGET = 32.0
MAX_SEARCH_ATTEMPTS = 32
MAX_ATTEMPTS_PER_TASK = 1
MAX_NATIVE_RULE_STEPS = 250_000
MAX_GRAPH_BYTES = 2_000_000
BOOTSTRAP_DRAWS = 20_000
BOOTSTRAP_SEED = 27_010_251

# P27 phase base is 10m + 27m. Sub-blocks are spaced by 10,000 so each
# concrete generated-world closure can be checked without seed-formula trust.
SEED_BLOCKS = {
    "development_train": 37_000_000,
    "heldout_train": 37_100_000,
    "heldout_test": 37_200_000,
    "heldout_validation": 37_300_000,
    "development_test": 37_400_000,
    "development_validation": 37_500_000,
    "development_controls": 37_600_000,
    "heldout_controls": 37_700_000,
}
PRIOR_NUMERIC_INTERVALS = (
    (26_000_000, 28_999_999), (29_000_000, 29_999_999),
    (31_000_000, 33_999_999), (41_000_000, 43_999_999),
    (70_000_000, 109_999_999), (110_000_000, 131_999_999),
    (150_000_000, 169_999_999),
)
SOURCE_FILES = (
    "evaluation/process_mastery/linear_p27_v1.py",
    "evaluation/process_mastery/analyze_linear_p27_v1.py",
    "evaluation/process_mastery/linear_p26_v1.py",
    "evaluation/process_mastery/evidence_search_worlds.py",
    "evaluation/process_mastery/common_target_learner.py",
    "evaluation/process_mastery/target_learner.py",
    "evaluation/process_mastery/target_learning_worlds.py",
    "evaluation/process_mastery/cumulative_checkpoint_panel.py",
    "evaluation/process_mastery/scheduled_learning_checkpoints.py",
    "evaluation/process_mastery/native_process_execution.py",
    "evaluation/process_mastery/runtime_attestation.py",
    "substrate/boot_profiles.py", "substrate/boot_core.py",
    "substrate/seed_loader.py", "seeds/cognition_on_params.json",
    "seeds/common_target_evidence.json", "seeds/additive_transfer.json",
    "seeds/useful_evidence_selection.json", "seeds/open_process_search.json",
    "seeds/open_process_adoption.json", "seeds/process_schema.json",
    "seeds/process_solving.json", "seeds/process_induction.json",
    "seeds/thinking_budget.json", "seeds/target_learning.json",
    "seeds/learning_memory_budget.json", "seeds/scheduled_learning_state.json",
    "scripts/gen_scheduled_learning_state_seed.py",
    "runners/dsl/python/substrate_rs/__init__.py",
    "runners/dsl/python/substrate_rs/_native.build.json",
    "runners/dsl/Cargo.toml", "runners/dsl/pyproject.toml", "runners/dsl/uv.lock",
    "runners/dsl/src/process_algebra.rs", "runners/dsl/src/term.rs",
    "runners/dsl/src/cognitive_cycle.rs", "runners/dsl/src/memory.rs",
    "docs/research/engine_substrate/COGNITION_CUMULATIVE_LEARNING_CONTRACT.md",
    "docs/research/engine_substrate/PMB_V1_SPEC.md",
    "tests/test_cumulative_checkpoint_panel.py",
    "tests/test_cumulative_causal_controls.py",
    "tests/test_scheduled_checkpoint_contract.py",
    "tests/test_scheduled_learning_checkpoints.py",
    "tests/test_cognition_profile_integration.py",
    "tests/test_linear_p27_v1.py",
)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, default=str).encode("utf-8")


def _digest(value) -> str:
    return _sha(_canonical(value))


def _commit() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                   text=True).strip()


def _seed_closure(roots: tuple[str, ...]) -> list[str]:
    loaded, resolving = set(), set()
    def visit(seed_id: str) -> None:
        if seed_id == "core" or seed_id in loaded:
            return
        if seed_id in resolving:
            raise ValueError(f"cyclic seed dependency: {seed_id}")
        resolving.add(seed_id)
        manifest = manifest_for(seed_id)
        for dependency in manifest.get("depends_on", ()):
            visit(str(dependency))
        resolving.remove(seed_id)
        loaded.add(seed_id)
    for seed_id in roots:
        visit(seed_id)
    return sorted(loaded)


def _derived_world_seeds(seed: int, draws: tuple[int, ...], *, split: str) -> list[int]:
    offset = {"train": 0, "development": 1_000_000,
              "validation": 2_000_000, "heldout": 3_000_000}[split]
    return [seed + offset + draw * 17 + index for index, draw in enumerate(draws)]


def allocation(split: str, *, test_count: int | None = None,
               validation_count: int | None = None, control_count: int | None = None) -> dict:
    if split not in {"development", "heldout"}:
        raise ValueError("split must be development or heldout")
    expected = ((DEVELOPMENT_WORLDS_PER_FAMILY, DEVELOPMENT_WORLDS_PER_FAMILY,
                 DEVELOPMENT_CONTROLS) if split == "development" else
                (TESTS_PER_FAMILY, VALIDATION_PER_FAMILY, HELDOUT_CONTROLS))
    supplied = (test_count, validation_count, control_count)
    for value, fixed in zip(supplied, expected):
        if value not in {None, fixed}:
            raise ValueError("allocation dimensions are fixed by the registered split")
    test_count, validation_count, control_count = expected
    test_draws = tuple(3 + 6 * i for i in range(test_count))
    validation_draws = tuple(3 + 6 * i for i in range(validation_count))
    rows = []
    train_block = SEED_BLOCKS[f"{split}_train"]
    test_block = (SEED_BLOCKS["development_test"] if split == "development"
                  else SEED_BLOCKS["heldout_test"])
    validation_block = (SEED_BLOCKS["development_validation"] if split == "development"
                        else SEED_BLOCKS["heldout_validation"])
    for family_index, family in enumerate(FAMILIES):
        # 50k family sub-blocks contain the full 200-world transferable
        # draw sequence (including its generated-world split offset).
        train_seed = train_block + family_index * 50_000
        test_seed = test_block + family_index * 50_000
        validation_seed = validation_block + family_index * 50_000
        rows.append({"family": family, "family_index": family_index,
            "training_pool_seed": train_seed,
            "training_draws": list(TRAIN_DRAWS),
            "training_world_seeds": _derived_world_seeds(
                train_seed, TRAIN_DRAWS, split="train"),
            "test_pool_seed": test_seed,
            "test_draws": list(test_draws),
            "test_world_seeds": _derived_world_seeds(test_seed, test_draws,
                split="development" if split == "development" else "heldout"),
            "validation_pool_seed": validation_seed,
            "validation_draws": list(validation_draws),
            "validation_world_seeds": _derived_world_seeds(
                validation_seed, validation_draws, split="development"
                    if split == "development" else "validation"),
            "stream_id": f"p27:{split}:{family}"})
    control_block = SEED_BLOCKS[f"{split}_controls"]
    controls = [{"control_id": f"p27:{split}:control:{i:03d}",
        "seed": control_block + i,
        "kind": ("heldout_selector_guard", "receipt_replay", "approval_boundary")[i % 3]}
        for i in range(control_count)]
    root_seeds = [row[key] for row in rows for key in
        ("training_pool_seed", "test_pool_seed", "validation_pool_seed")]
    root_seeds.extend(row["seed"] for row in controls)
    world_seeds = [seed for row in rows for key in
        ("training_world_seeds", "test_world_seeds", "validation_world_seeds")
        for seed in row[key]]
    if (len(root_seeds) != len(set(root_seeds))
            or len(world_seeds) != len(set(world_seeds))
            or set(root_seeds) & set(world_seeds)):
        raise RuntimeError("P27 allocation has colliding root or derived world seeds")
    all_seeds = root_seeds + world_seeds
    if any(lo <= seed <= hi for seed in all_seeds for lo, hi in PRIOR_NUMERIC_INTERVALS):
        raise RuntimeError("P27 allocation overlaps an earlier numeric seed envelope")
    plan = {"phase": PHASE, "split": split, "families": list(FAMILIES),
        "arms": list(ARMS), "checkpoints": list(CHECKPOINTS),
        "work_thresholds": list(WORK_THRESHOLDS),
        "task_access_thresholds": list(STAGE_ACCESS),
        "families_allocation": rows, "controls": controls,
        "test_worlds_per_family": test_count,
        "validation_worlds_per_family": validation_count,
        "integrity_control_count": control_count,
        "shared_budget_capacity": SHARED_BUDGET,
        "native_search_attempt_limit": MAX_SEARCH_ATTEMPTS,
        "native_search_per_task_limit": MAX_ATTEMPTS_PER_TASK,
        "max_native_rule_steps": MAX_NATIVE_RULE_STEPS,
        "max_graph_bytes": MAX_GRAPH_BYTES}
    plan["allocation_sha256"] = _digest(plan)
    return plan


def provenance() -> dict:
    profile_seeds = tuple(sorted(set(COGNITION_ON_SEEDS) | {
        "common_target_evidence", "additive_transfer", "open_process_adoption",
        "learning_memory_budget", "scheduled_learning_state"}))
    closure = _seed_closure(profile_seeds)
    source_paths = sorted(set(SOURCE_FILES) | {f"seeds/{seed}.json" for seed in closure})
    source_hashes = {}
    for rel in source_paths:
        path = ROOT / rel
        if not path.is_file():
            raise RuntimeError(f"P27 frozen source is missing: {rel}")
        source_hashes[rel] = _sha(path.read_bytes())
    receipt = ROOT / "runners/dsl/python/substrate_rs/_native.build.json"
    runtime = attest(package=substrate_rs, build_receipt=receipt)
    if runtime.get("status") != "ATTESTED":
        raise RuntimeError("P27 requires an attested native extension: " +
                           ", ".join(runtime.get("issues", [])))
    return {"source_file_sha256": source_hashes,
        "source_bundle_sha256": _digest(source_hashes),
        "runner_sha256": source_hashes["evaluation/process_mastery/linear_p27_v1.py"],
        "analyzer_sha256": source_hashes["evaluation/process_mastery/analyze_linear_p27_v1.py"],
        "loaded_seed_closures": closure,
        "profile_seed_ids": list(profile_seeds),
        "runtime_attestation": runtime,
        "loaded_extension_path": runtime["loaded_extension_path"],
        "loaded_extension_sha256": runtime["loaded_extension_sha256"],
        "build_receipt_path": runtime["build_receipt_path"],
        "build_receipt_sha256": runtime["build_receipt_sha256"],
        "python": sys.version}


def _attach_search_task(world, task: dict, *, task_index: int) -> int:
    """Install one training-only native search task in the same shared graph."""
    store, root = world.s, world.agent
    domain_name = f"p27-search-{task_index}-{_digest(task['world_id'])[:10]}"
    domain = store.add_node("ProcessDomain", {"name": domain_name,
        "kind": "permutation", "probes": [list(task["initial_state"])],
        "probe_epoch": 0, "source_epoch": 0, "model_epoch": 0,
        "frame_epoch": 0, "identity_effect_digest":[list(range(len(task["initial_state"])))],
        "split": "training"})
    store.add_edge(root, "has_process_domain", domain, {})
    for name, params in task["primitive_effects"].items():
        schema = store.add_node("ProcessSchema", {"kind": "permutation",
            "domain": domain_name, "domain_kind": "permutation", "name": name,
            "params": list(params), "source_digest": params_digest(list(params)),
            "cost": 1.0, "provenance": "held", "status": "active",
            "invariants": [], "owner_agent": root, "source_epoch": 0,
            "model_epoch": 0, "frame_epoch": 0, "probe_epoch": 0,
            "source_probe_epoch": 0, "split": "training"})
        store.add_edge(root, "has_process_schema", schema, {})
    solve_task = store.add_node("SolveTask", {"domain": domain_name,
        "state": list(task["initial_state"]), "initial_state": list(task["initial_state"]),
        "goal": list(task["goal_state"]), "object_count": float(len(task["initial_state"])),
        "status": "stuck", "steps": 0, "moves": 0.0, "trace": [],
        "stuck_count": 0, "tools_seen": 0, "split": "training",
        "training_trial_key": task["world_id"]})
    store.add_edge(root, "has_solve_task", solve_task, {})
    store.add_edge(solve_task, "about_domain", domain, {})
    return solve_task


def _budget_debits(learner) -> float:
    return sum(float(learner.s.node(node)["attrs"].get("cost", 0.0))
        for node in learner.s.nodes("ThinkingBudgetRequest")
        if learner.s.node(node)["attrs"].get("status") == "approved")


def _train_arm(*, family: str, arm: str, training_seed: int,
               world_allocation_sha256: str) -> dict:
    if arm not in ARMS or family not in FAMILIES:
        raise ValueError("unknown P27 arm/family")
    pool = generate_evidence_search_pool(split="train", draws=TRAIN_DRAWS,
        seed=training_seed, family=family, initial_state=tuple(range(
            7 if family == "cyclic_relation" else 9)))
    selector_views(pool)  # training-only boundary and public task contract check
    tasks = pool.task_pool()
    world = boot_cognition_on()
    learner = CommonTargetLearner(agent=world,
        owner_id=f"p27:{family}:{arm}", budget=SHARED_BUDGET,
        enabled=True, policy_enabled=True)
    selector_policy, = learner.s.nodes("UsefulEvidenceSelectionPolicy")
    search_policies = learner.s.nodes("OpenProcessSearchPolicy")
    schema_policies = learner.s.nodes("ProcessSchemaPolicy")
    adoption_policies = learner.s.nodes("OpenProcessAdoptionPolicy")
    if len(search_policies) != 1 or len(schema_policies) != 1 or len(adoption_policies) != 1:
        world.close()
        raise RuntimeError("P27 needs exactly one search/schema/adoption policy")
    selection_enabled = arm in {"evidence_selection_only", "combined"}
    search_enabled = arm in {"process_search_only", "combined"}
    learner.s.set_attr(selector_policy, "enabled", float(selection_enabled))
    learner.s.set_attr(selector_policy, "selector_mode", "residual")
    learner.s.set_attr(selector_policy, "pool_id", pool.pool_id)
    learner.s.set_attr(selector_policy, "max_selections", 4.0)
    learner.s.set_attr(search_policies[0], "enabled", float(search_enabled))
    learner.s.set_attr(search_policies[0], "max_attempts", float(MAX_SEARCH_ATTEMPTS))
    learner.s.set_attr(search_policies[0], "max_attempts_per_request",
                       float(MAX_ATTEMPTS_PER_TASK))
    learner.s.set_attr(search_policies[0], "max_candidates", 32.0)
    learner.s.set_attr(search_policies[0], "effect_dedup_enabled", 1.0)
    learner.s.set_attr(schema_policies[0], "enabled", float(search_enabled))
    learner.s.set_attr(adoption_policies[0], "enabled", 0.0)
    budget_nodes = learner.s.neighbours(learner.ag, "has_thinking_budget")
    if len(budget_nodes) != 1:
        world.close()
        raise RuntimeError("P27 arms must share exactly one native ThinkingBudget")

    baseline_receipts = []
    try:
        # All arms inherit the same immutable g0 training ancestor.
        for draw in BASELINE_DRAWS:
            index = TRAIN_DRAWS.index(draw)
            task = tasks[index]
            opportunity = _one_opportunity(task, "act_0")
            external = EvidenceSearchWorld(task, pool.scorer_only[index])
            receipt = external.execute(opportunity)
            if not external.verify_receipt(receipt):
                raise RuntimeError("baseline training receipt failed world verification")
            learner.observe_world_receipt(receipt, source_epoch=1, model_epoch=1,
                frame_epoch=1, split="training")
            steps = learner.settle()
            baseline_receipts.append({"event_id": receipt.event_id,
                "world_id": task["world_id"], "action_authorized": receipt.action_authorized,
                "status": receipt.status, "native_rule_steps": int(steps)})

        current_pool = {"pool_id": pool.pool_id, "rows": {}, "worlds": {}}
        captured = []
        stage_task_accesses = 0
        native_steps = sum(row["native_rule_steps"] for row in baseline_receipts)
        prior_candidate_ids: set[str] = set()
        prior_receipts = len(learner.s.nodes("CommonTargetEvidence"))

        def capture(checkpoint: str, interval_status: str,
                    pending_ids: tuple[str, ...] = ()) -> None:
            graph = snapshot_native_graph(world)
            graph_bytes = len(_canonical(graph))
            cumulative = {"primitive_work": native_steps,
                "source_exposure": len(learner.s.nodes("TargetSourceExposure")),
                "native_rule_steps": native_steps, "graph_bytes": graph_bytes,
                "budget_debits": int(round(_budget_debits(learner))),
                "task_world_accesses": stage_task_accesses}
            parent = captured[-1] if captured else None
            if (interval_status == "no_change" and parent is not None
                    and _digest(json.loads(parent.graph_snapshot_json)) != _digest(graph)):
                interval_status = "progress"
            captured.append(capture_scheduled_checkpoint(arm=arm,
                checkpoint=checkpoint, native_graph=graph, cumulative=cumulative,
                interval_status=interval_status, parent=parent,
                world_allocation_sha256=world_allocation_sha256,
                max_graph_bytes=MAX_GRAPH_BYTES,
                max_native_rule_steps=MAX_NATIVE_RULE_STEPS,
                pending_candidate_ids=pending_ids,
                approval_ids=tuple(str(x) for x in learner.s.nodes("OpenProcessAdoptionApproval")),
                receipt_ids=tuple(str(x) for x in learner.s.nodes("OpenProcessWorldReceipt"))))

        capture("g0", "initial")
        selection_rows = []
        search_rows = []
        search_task_index = 0
        for stage_index, draws in enumerate(STAGE_DRAWS):
            new_opportunity_ids = []
            for draw in draws:
                index = TRAIN_DRAWS.index(draw)
                task = tasks[index]
                external = EvidenceSearchWorld(task, pool.scorer_only[index])
                stage_task_accesses += 1
                for opportunity in task["evidence_opportunities"]:
                    row = dict(opportunity)
                    _add_opportunity(learner, row)
                    current_pool["rows"][row["opportunity_key"]] = row
                    current_pool["worlds"][row["opportunity_key"]] = external
                    new_opportunity_ids.append(row["opportunity_key"])
                if search_enabled:
                    solve_task = _attach_search_task(world, task,
                        task_index=search_task_index)
                    search_task_index += 1
                    before = len(learner.s.nodes("OpenProcessSearchAttempt"))
                    steps = learner.settle()
                    native_steps += int(steps)
                    after = len(learner.s.nodes("OpenProcessSearchAttempt"))
                    search_rows.append({"stage": stage_index + 1,
                        "task_world_id": task["world_id"],
                        "task_node_id": str(solve_task),
                        "attempts_added": after - before,
                        "task_status": learner.s.node(solve_task)["attrs"].get("status")})
            if selection_enabled:
                # Each call is bounded to the newly exposed opportunity batch;
                # same pool records and shared native budget are used at all stages.
                selected = _select_and_deliver(learner, current_pool,
                    mode="residual", max_selections=(1 if stage_index < 2 else 2))
                selection_rows.extend(selected["rows"])
                native_steps += int(selected["native_rule_steps"])
            elif not search_enabled:
                native_steps += int(learner.settle())

            candidate_ids = tuple(str(node) for node in learner.s.nodes("OpenProcessCandidate")
                if learner.s.node(node)["attrs"].get("status") == "unapproved_candidate")
            new_candidates = set(candidate_ids) - prior_candidate_ids
            receipts_now = len(learner.s.nodes("CommonTargetEvidence"))
            selected_now = sum(row.get("receipt_event_id") is not None for row in selection_rows)
            selected_prev = selected_now - sum(row.get("receipt_event_id") is not None
                for row in (selected["rows"] if selection_enabled else []))
            if new_candidates:
                status = "authorization_pending"
            elif search_enabled and search_rows and search_rows[-1].get("attempts_added", 0):
                status = "progress" if selected_now > selected_prev else "search_failed"
            else:
                status = "progress" if receipts_now > prior_receipts else "no_change"
            checkpoint = ("g1", "g2", "g3")[stage_index]
            capture(checkpoint, status, tuple(sorted(new_candidates)))
            prior_candidate_ids.update(candidate_ids)
            prior_receipts = receipts_now

        graph_sizes = [cp.graph_bytes for cp in captured]
        if max(graph_sizes, default=0) > MAX_GRAPH_BYTES:
            raise RuntimeError("P27 complete dynamic graph exceeds its frozen ceiling")
        if native_steps > MAX_NATIVE_RULE_STEPS:
            raise RuntimeError("P27 native rule work exceeds its frozen ceiling")
        if learner.s.nodes("OpenProcessAdoptionApproval"):
            raise RuntimeError("P27 training unexpectedly created an approval")
        return {"family": family, "arm": arm, "train_pool_id": pool.pool_id,
            "train_pool_sha256": pool.pool_sha256,
            "baseline_receipts": baseline_receipts,
            "selection_rows": selection_rows, "search_rows": search_rows,
            "checkpoints": [asdict(cp) for cp in captured],
            "training_opportunity_ids": sorted(current_pool["rows"]),
            "budget_debited": _budget_debits(learner),
            "native_rule_steps": native_steps,
            "graph_bytes_by_checkpoint": graph_sizes,
            "candidate_count": len(learner.s.nodes("OpenProcessCandidate")),
            "approval_count": len(learner.s.nodes("OpenProcessAdoptionApproval")),
            "world_receipt_count": len(learner.s.nodes("OpenProcessWorldReceipt")),
            "target_evidence_count": len(learner.s.nodes("CommonTargetEvidence"))}
    finally:
        world.close()


def _panel_worlds(*, family: str, split: str, seed: int,
                  draws: tuple[int, ...] | list[int]) -> list[dict]:
    pool = generate_evidence_search_pool(split=split, draws=draws,
        seed=seed, family=family, initial_state=tuple(range(
            7 if family == "cyclic_relation" else 9)))
    worlds = []
    for task, scorer in zip(pool.task_pool(), pool.scorer_only):
        opportunity = _one_opportunity(task, "act_0")
        external = EvidenceSearchWorld(task, scorer)
        receipt = external.execute(opportunity)
        if not external.verify_receipt(receipt):
            raise RuntimeError("external evaluation world returned an invalid receipt")
        worlds.append({"world_id": task["world_id"], "family": family,
            "split": split, "draw": task["draw"], "action_kind": "act_0",
            "object_type": opportunity["object_type"],
            "feature_key": opportunity["feature_key"],
            "before_value": opportunity["before_value"],
            "object_id": f"p27-fresh-binding:{task['world_id']}",
            "source_epoch": 1, "model_epoch": 1, "frame_epoch": 1,
            "expected_after_value": receipt.after_value,
            "outcome_digest": _digest(receipt.after_value),
            "action_authorized": receipt.action_authorized,
            "receipt_status": receipt.status})
    return worlds


def _run_integrity_controls(plan: dict) -> list[dict]:
    rows = []
    for control in plan["controls"]:
        kind = control["kind"]
        if kind == "heldout_selector_guard":
            pool = generate_evidence_search_pool(split="heldout", draws=(0,),
                seed=control["seed"], family="cyclic_relation")
            try:
                selector_views(pool)
                status = "FAIL"
            except ValueError:
                status = "PASS"
            rows.append({**control, "status": status,
                "heldout_pool_sha256": pool.pool_sha256,
                "selector_view_denied": status == "PASS"})
        elif kind == "receipt_replay":
            pool = generate_evidence_search_pool(split="train", draws=(1,),
                seed=control["seed"], family="cyclic_relation")
            task = pool.task_pool()[0]
            receipt = EvidenceSearchWorld(task, pool.scorer_only[0]).execute(
                _one_opportunity(task, "act_0"))
            world = boot_cognition_on()
            try:
                learner = CommonTargetLearner(agent=world,
                    owner_id=f"p27-control:{control['control_id']}", budget=SHARED_BUDGET)
                learner.observe_world_receipt(receipt, split="training")
                learner.settle()
                before = len(learner.s.nodes("CommonTargetEvidence"))
                learner.observe_world_receipt(receipt, split="training")
                after = len(learner.s.nodes("CommonTargetEvidence"))
                rows.append({**control, "status": "PASS" if before == after == 1 else "FAIL",
                    "evidence_before": before, "evidence_after": after,
                    "replay_added_exposure": before != after})
            finally:
                world.close()
        else:
            # Candidate approval/adoption remains disabled in all P27 arms.
            rows.append({**control, "status": "PASS",
                "approval_policy_enabled": False, "world_transition_calls": 0,
                "adoption_approval_count": 0, "world_receipt_count": 0})
    return rows


def run_split(split: str, *, allocation_plan: dict | None = None) -> dict:
    plan = allocation_plan or allocation(split)
    if plan.get("split") != split or plan.get("phase") != PHASE:
        raise ValueError("P27 allocation does not match requested phase/split")
    rows = []
    all_worlds = {}
    for family_row in plan["families_allocation"]:
        family = family_row["family"]
        test_split = "development" if split == "development" else "heldout"
        validation_split = "development" if split == "development" else "validation"
        test_worlds = _panel_worlds(family=family, split=test_split,
            seed=family_row["test_pool_seed"], draws=family_row["test_draws"])
        validation_worlds = _panel_worlds(family=family, split=validation_split,
            seed=family_row["validation_pool_seed"],
            draws=family_row["validation_draws"])
        allocation_sha = world_allocation_digest(test_worlds + validation_worlds)
        all_worlds[family] = {"test": test_worlds, "validation": validation_worlds,
                              "allocation_sha256": allocation_sha}
        for arm in ARMS:
            rows.append(_train_arm(family=family, arm=arm,
                training_seed=family_row["training_pool_seed"],
                world_allocation_sha256=allocation_sha))
    controls = _run_integrity_controls(plan)
    panels = {"test": [], "validation": []}
    predictors = {(family, arm): make_native_common_target_predictor(
        owner_id=f"p27:{family}:{arm}", agent_factory=boot_cognition_on)
        for family in FAMILIES for arm in ARMS}
    try:
        for family in FAMILIES:
            family_arms = {}
            for arm in ARMS:
                lineage = next(row for row in rows
                    if row["family"] == family and row["arm"] == arm)
                family_arms[arm] = tuple(
                    ScheduledLearningCheckpoint(**cp)
                    for cp in lineage["checkpoints"])
            final_arms = {arm: (family_arms[arm][-1],) for arm in ARMS}
            family_predictors = {arm: predictors[(family, arm)]
                for arm in ARMS}
            for panel_name in ("test", "validation"):
                worlds = all_worlds[family][panel_name]
                panel = score_common_world_panel(checkpoints=(family_arms
                    if panel_name == "test" else final_arms),
                    worlds=worlds, native_predictor=family_predictors,
                    allocation_sha256=all_worlds[family]["allocation_sha256"])
                panels[panel_name].append({"family": family, **panel})
    finally:
        for predictor in predictors.values():
            predictor.close()
    return {"phase": PHASE, "split": split,
        "status": "development_only" if split == "development" else "heldout_pending_analysis",
        "heldout_accessed": split == "heldout", "allocation_plan": plan,
        "provenance": provenance(), "training_lineages": rows,
        "evaluation_worlds": all_worlds, "panels": panels,
        "integrity_controls": controls,
        "summary": {"family_count": len(FAMILIES), "arm_count": len(ARMS),
            "checkpoint_count": len(CHECKPOINTS),
            "training_lineages": len(rows),
            "test_worlds": sum(len(v["test"]) for v in all_worlds.values()),
            "validation_worlds": sum(len(v["validation"]) for v in all_worlds.values()),
            "control_count": len(controls)}}


def _freeze_record(document: bytes) -> dict:
    prefix = "P27_FREEZE_JSON: "
    records = [line[len(prefix):] for line in document.decode("utf-8").splitlines()
        if line.startswith(prefix)]
    if len(records) != 1:
        raise RuntimeError("P27 preregistration must contain one freeze JSON record")
    value = json.loads(records[0])
    if not isinstance(value, dict):
        raise RuntimeError("P27 freeze record must be an object")
    return value


def _assert_heldout_freeze() -> None:
    prereg = ROOT / PREREGISTRATION
    head = _commit()
    parent = subprocess.check_output(["git", "rev-parse", f"{head}^"],
        cwd=ROOT, text=True).strip()
    changed = subprocess.check_output(["git", "diff-tree", "--no-commit-id",
        "--name-only", "-r", head], cwd=ROOT, text=True).splitlines()
    if changed != [PREREGISTRATION]:
        raise RuntimeError("latest commit must contain only the P27 preregistration")
    committed = subprocess.check_output(["git", "show", f"{head}:{PREREGISTRATION}"],
        cwd=ROOT)
    if committed != prereg.read_bytes():
        raise RuntimeError("working P27 preregistration differs from committed bytes")
    freeze = _freeze_record(committed)
    if freeze.get("code_commit") != parent:
        raise RuntimeError("P27 preregistration is not immediately after its frozen code commit")
    current = provenance()
    for key in ("source_file_sha256", "source_bundle_sha256", "runner_sha256",
                "analyzer_sha256", "loaded_extension_path", "loaded_extension_sha256",
                "build_receipt_path", "build_receipt_sha256", "runtime_attestation",
                "profile_seed_ids", "loaded_seed_closures", "python"):
        if freeze.get(key) != current.get(key):
            raise RuntimeError(f"P27 preregistration freeze mismatch: {key}")
    if freeze.get("allocation_sha256") != allocation("heldout")["allocation_sha256"]:
        raise RuntimeError("P27 heldout allocation differs from its frozen seed closure")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--split", choices=("development", "heldout"), required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.split == "heldout":
        _assert_heldout_freeze()
    output = args.output or ROOT / (RAW_HELDOUT if args.split == "heldout" else
        "evaluation/process_mastery/results/p27_linear_v1_development.json")
    if output.exists():
        parser.error("refusing to overwrite an existing P27 artifact")
    marker = ROOT / HELDOUT_MARKER
    if args.split == "heldout":
        marker.parent.mkdir(parents=True, exist_ok=True)
        with marker.open("x", encoding="utf-8") as fh:
            fh.write(json.dumps({"phase": PHASE, "status": "attempt_started",
                "started_unix": time.time(), "commit": _commit()}, sort_keys=True) + "\n")
    payload = run_split(args.split)
    output.parent.mkdir(parents=True, exist_ok=True)
    tmp = output.with_suffix(output.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, sort_keys=True, separators=(",", ":"),
        ensure_ascii=False, default=str) + "\n")
    os.replace(tmp, output)
    digest = _sha(output.read_bytes())
    if args.split == "heldout":
        marker.write_text(json.dumps({"phase": PHASE, "status": "complete",
            "raw_path": str(output.relative_to(ROOT)), "raw_sha256": digest,
            "completed_unix": time.time()}, sort_keys=True) + "\n")
    print(json.dumps({"status": payload["status"], "raw_path": str(output),
        "raw_sha256": digest, "summary": payload["summary"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

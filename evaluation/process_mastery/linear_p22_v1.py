"""Frozen P22 runner for approved immutable checkpoint lineages.

Development may inspect allocations and checkpoint manifests, but held-out
scoring requires the committed standalone P22 freeze and exact native
runtime attestation. This module never creates candidate approvals or world
receipts.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
for _path in (ROOT, ROOT / "runners/dsl/python"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from evaluation.process_mastery.analyze_linear_p22_v1 import (
    ARMS, GENERATIONS, PHASE, RESOURCE_FIELDS, analyze as analyze_p22,
    self_check as analyzer_self_check,
)
from evaluation.process_mastery.checkpoint_world_adapter import (
    CheckpointExpression, CheckpointWorldAdapter,
)
from evaluation.process_mastery.p22_checkpoint_panel import (
    score_checkpoint_world_isolated,
)
from evaluation.process_mastery.independent_worlds import (
    agent_view, generate_d4_world_v2, generate_loopover_world_v2, p22_seed,
)
from evaluation.process_mastery.p22_resource_accounting import (
    analyzer_resource_record, resource_snapshot_digest_valid,
)
from evaluation.process_mastery.runtime_attestation import attest
from evaluation.process_mastery.harness import Agent
import substrate_rs


PREREGISTRATION = "docs/research/engine_substrate/COGNITION_LINEAR_P22_PREREG.md"
FAMILIES = ("d4", "loopover")
FAMILY_GENERATORS = {
    "d4": (generate_d4_world_v2, 4),
    "loopover": (generate_loopover_world_v2, 9),
}
PANEL_SIZE = 200
CONTROL_IDS = ("checkpoint_digest_tampering", "malformed_permutation",
               "lineage_parent_integrity", "repeatability")
SPLIT_DRAWS = {
    # The development training/validation ranges stop before 600. Selection
    # and evaluation use separate generator split namespaces.
    "training": range(600, 800),
    "selection": range(0, 200),
    "validation": range(600, 800),
    "heldout": range(0, 200),
}
PROVENANCE_FILES = (
    "evaluation/process_mastery/linear_p22_v1.py",
    "evaluation/process_mastery/analyze_linear_p22_v1.py",
    "evaluation/process_mastery/checkpoint_world_adapter.py",
    "evaluation/process_mastery/improvement_estimand.py",
    "evaluation/process_mastery/independent_worlds.py",
    "evaluation/process_mastery/native_process_execution.py",
    "evaluation/process_mastery/p22_arms.py",
    "evaluation/process_mastery/p22_checkpoint_panel.py",
    "evaluation/process_mastery/p22_development.py",
    "evaluation/process_mastery/p22_four_arm_development.py",
    "evaluation/process_mastery/p22_resource_accounting.py",
    "evaluation/process_mastery/runtime_attestation.py",
    "docs/research/engine_substrate/COGNITION_INDEPENDENT_IMPROVEMENT_CONTRACT.md",
    "docs/research/engine_substrate/COGNITION_P15_REVIEW_AND_REMAINING_GAPS_20261022.md",
    "substrate/boot_profiles.py", "seeds/cognition_on_params.json",
    "scripts/gen_independent_improvement_seed.py", "seeds/independent_improvement.json",
    "scripts/gen_open_process_search_seed.py", "seeds/open_process_search.json",
    "scripts/gen_open_process_adoption_seed.py", "seeds/open_process_adoption.json",
    "scripts/run_p22_development_probe.py",
    "scripts/run_p22_four_arm_development.py",
    "runners/dsl/python/substrate_rs/__init__.py",
    "runners/dsl/python/substrate_rs/_native.build.json",
    "runners/dsl/Cargo.toml", "runners/dsl/pyproject.toml", "runners/dsl/uv.lock",
    "runners/dsl/src/process_algebra.rs", "runners/dsl/src/term.rs",
    "runners/dsl/src/cognitive_cycle.rs",
)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _digest(value) -> str:
    return _sha(json.dumps(value, sort_keys=True, separators=(",", ":"),
                           ensure_ascii=False).encode("utf-8"))


def _commit() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                   text=True).strip()


def allocation() -> dict:
    """Build the fixed four-split v2 allocation without materializing labels."""
    split_names = {"training": "train", "selection": "selection",
                   "validation": "validation", "heldout": "heldout"}
    ids = {split: {family: [
        f"p22:{family}-v2:{split_names[split]}:{draw:04d}" for draw in draws]
        for family in FAMILIES} for split, draws in SPLIT_DRAWS.items()}
    family_codes = {"d4": 4, "loopover": 3}
    seeds = {split: {family: [p22_seed(family_code=family_codes[family],
        split=split_names[split], draw=draw) for draw in draws]
        for family in FAMILIES} for split, draws in SPLIT_DRAWS.items()}
    seen = set()
    for family in FAMILIES:
        for split in SPLIT_DRAWS:
            rows = ids[split][family]
            if len(rows) != PANEL_SIZE or len(rows) != len(set(rows)):
                raise RuntimeError(f"invalid {split} allocation for {family}")
            overlap = seen.intersection(rows)
            if overlap:
                raise RuntimeError(f"P22 allocation identities overlap: {sorted(overlap)[:1]}")
            seen.update(rows)
    return {"families": list(FAMILIES),
        "world_ids_by_family": ids["heldout"],
        "validation_world_ids_by_family": ids["validation"],
        "selection_world_ids_by_family": ids["selection"],
        "training_world_ids_by_family": ids["training"],
        "seeds_by_split_family": seeds,
        "generations": list(GENERATIONS), "arms": list(ARMS),
        "control_ids": list(CONTROL_IDS)}


def _hash_files(paths=PROVENANCE_FILES) -> dict:
    return {relative: _sha((ROOT / relative).read_bytes()) for relative in paths}


def _bundle(hashes: dict, paths) -> str:
    return _digest([(relative, hashes[relative]) for relative in paths])


def provenance() -> dict:
    """Bind P22 source closure and the exact native extension loaded now."""
    hashes = _hash_files()
    package_dir = Path(substrate_rs.__file__).resolve().parent
    extension = Path(substrate_rs._native.__file__).resolve()
    receipt = package_dir / "_native.build.json"
    profile_files = ("substrate/boot_profiles.py", "seeds/cognition_on_params.json")
    world_files = ("evaluation/process_mastery/independent_worlds.py",
                   "evaluation/process_mastery/checkpoint_world_adapter.py")
    dependency_files = ("runners/dsl/Cargo.toml", "runners/dsl/pyproject.toml",
        "runners/dsl/uv.lock", "runners/dsl/python/substrate_rs/_native.build.json")
    return {"phase": PHASE, "git_commit": _commit(),
        "runner_sha256": hashes["evaluation/process_mastery/linear_p22_v1.py"],
        "analyzer_sha256": hashes["evaluation/process_mastery/analyze_linear_p22_v1.py"],
        "source_file_sha256": hashes,
        "source_bundle_sha256": _bundle(hashes, PROVENANCE_FILES),
        "wrapper_sha256": _sha(Path(substrate_rs.__file__).read_bytes()),
        "loaded_extension_path": str(extension),
        "loaded_extension_sha256": _sha(extension.read_bytes()),
        "build_receipt_path": str(receipt),
        "build_receipt_sha256": _sha(receipt.read_bytes()),
        "profile_sha256": _bundle(hashes, profile_files),
        "world_adapter_sha256": _bundle(hashes, world_files),
        "dependency_closure_sha256": _bundle(hashes, dependency_files),
        "runtime_attestation": attest(package=substrate_rs,
            build_receipt=receipt, require_clean=True),
        "python": sys.version.split()[0]}


def _read_freeze(path: Path) -> dict:
    match = re.search(r"^P22_FREEZE_JSON: (\{.*\})$",
        path.read_text(encoding="utf-8"), re.MULTILINE)
    if not match:
        raise RuntimeError("P22 preregistration lacks its machine-readable freeze")
    return json.loads(match.group(1))


def _checkpoint(record: dict) -> CheckpointExpression:
    if not isinstance(record, dict):
        raise ValueError("checkpoint record must be an object")
    fields = {field for field in CheckpointExpression.__dataclass_fields__}
    if set(record) != fields:
        raise ValueError("checkpoint record fields do not match the frozen schema")
    value = dict(record)
    value["params"] = tuple(value["params"])
    return CheckpointExpression(**value)


def _load_manifest(path: Path, expected_sha: str) -> dict:
    raw = path.read_bytes()
    if _sha(raw) != expected_sha:
        raise RuntimeError("checkpoint manifest hash differs from the P22 freeze")
    manifest = json.loads(raw)
    if manifest.get("schema") != "p22_checkpoint_manifest_v1":
        raise RuntimeError("unsupported P22 checkpoint manifest schema")
    return manifest


def _index_manifest(manifest: dict) -> tuple[dict, dict]:
    ancestors = manifest.get("ancestors")
    records = manifest.get("lineages")
    if not isinstance(ancestors, dict) or not isinstance(records, list):
        raise ValueError("P22 manifest requires ancestors and lineages")
    roots, lineages = {}, {}
    for family in FAMILIES:
        for arm in ARMS:
            key = f"{family}:{arm}"
            if key not in ancestors:
                raise ValueError(f"missing frozen ancestor checkpoint: {key}")
            root = _checkpoint(ancestors[key])
            if (root.generation != 0 or root.native_graph_snapshot_json is None
                    or not CheckpointWorldAdapter._checkpoint_digest_valid(root)):
                raise ValueError(f"invalid generation-zero ancestor checkpoint: {key}")
            roots[key] = root
    for family in FAMILIES:
        family_roots = [roots[f"{family}:{arm}"] for arm in ARMS]
        ancestor_identities = {(root.expression_digest, root.params)
                               for root in family_roots}
        if len(ancestor_identities) != 1:
            raise ValueError(
                f"P22 arms do not share one generation-zero ancestor process: {family}")
        if any(root.parent_digest or root.approval_id or root.receipt_id
               for root in family_roots):
            raise ValueError(f"generation-zero ancestor carries lineage action evidence: {family}")
    for row in records:
        if not isinstance(row, dict) or set(row) != {"family", "arm", "generation", "checkpoint"}:
            raise ValueError("malformed P22 lineage record")
        key = (row["family"], row["arm"], row["generation"])
        if (row["family"] not in FAMILIES or row["arm"] not in ARMS
                or row["generation"] not in GENERATIONS or key in lineages):
            raise ValueError(f"invalid or duplicate P22 lineage identity: {key}")
        checkpoint = _checkpoint(row["checkpoint"])
        if (checkpoint.generation != row["generation"]
                or checkpoint.native_graph_snapshot_json is None
                or not CheckpointWorldAdapter._checkpoint_digest_valid(checkpoint)):
            raise ValueError(f"lineage checkpoint digest/generation invalid: {key}")
        lineages[key] = checkpoint
    expected = {(family, arm, generation) for family in FAMILIES
                for arm in ARMS for generation in GENERATIONS}
    if set(lineages) != expected:
        raise ValueError(f"P22 manifest lineage coverage incomplete: {len(expected-set(lineages))} missing")
    roots_digest = {key: checkpoint.checkpoint_digest for key, checkpoint in roots.items()}
    for family in FAMILIES:
        for arm in ARMS:
            root = roots[f"{family}:{arm}"]
            parent = roots_digest[f"{family}:{arm}"]
            parent_expression_digest = root.expression_digest
            parent_params = root.params
            for generation in GENERATIONS:
                checkpoint = lineages[(family, arm, generation)]
                if checkpoint.parent_digest != parent:
                    raise ValueError(f"P22 lineage parent mismatch: {family}:{arm}:g{generation}")
                if arm in {"invention_only", "full"}:
                    if generation > 0 and (not checkpoint.approval_id or not checkpoint.receipt_id):
                        raise ValueError(f"approved lineage evidence missing: {family}:{arm}:g{generation}")
                else:
                    if checkpoint.approval_id or checkpoint.receipt_id:
                        raise ValueError(f"passive control lineage carries adoption evidence: {family}:{arm}:g{generation}")
                    if (checkpoint.expression_digest != parent_expression_digest
                            or checkpoint.params != parent_params):
                        raise ValueError(f"passive control expression changed without adoption: {family}:{arm}:g{generation}")
                parent_expression_digest = checkpoint.expression_digest
                parent_params = checkpoint.params
                parent = checkpoint.checkpoint_digest
    return roots, lineages


def _preflight_checkpoint_resources(freeze: dict, lineages: dict,
                                   ceilings: dict) -> None:
    """Reject an incomplete resource manifest before any held-out world is built."""
    wall_times = freeze.get("checkpoint_wall_time_seconds")
    expected_keys = {f"{family}:{arm}:g{generation}" for family in FAMILIES
                     for arm in ARMS for generation in GENERATIONS}
    if not isinstance(wall_times, dict) or set(wall_times) != expected_keys:
        raise RuntimeError("freeze must provide isolated wall time for every scored checkpoint")
    for family in FAMILIES:
        for arm in ARMS:
            for generation in GENERATIONS:
                checkpoint = lineages[(family, arm, generation)]
                key = f"{family}:{arm}:g{generation}"
                wall_time = wall_times[key]
                if (isinstance(wall_time, bool)
                        or not isinstance(wall_time, (int, float))
                        or not math.isfinite(wall_time) or wall_time < 0):
                    raise RuntimeError(f"invalid frozen wall time for {key}")
                snapshot = json.loads(checkpoint.resource_snapshot_json)
                measured = analyzer_resource_record(snapshot,
                    cumulative_primitive_work=checkpoint.cumulative_primitive_work,
                    wall_time_seconds=wall_time)
                for field in RESOURCE_FIELDS:
                    value = measured["resources"].get(field)
                    evidence = measured["resource_measurements"].get(field, {})
                    if (value is None or evidence.get("status") not in {
                            "MEASURED", "MEASURED_NODE_PAYLOAD_BYTES"}):
                        raise RuntimeError(
                            f"checkpoint resource is not fully measured before holdout: {key}:{field}")
                    ceiling = ceilings[field]
                    if (isinstance(ceiling, bool)
                            or not isinstance(ceiling, (int, float))
                            or not math.isfinite(ceiling) or ceiling < 0
                            or value > ceiling):
                        raise RuntimeError(
                            f"checkpoint resource ceiling invalid/exceeded before holdout: {key}:{field}")


def _verify_freeze(path: Path, requested_hash: str) -> tuple[dict, dict, dict]:
    try:
        relative = str(path.resolve().relative_to(ROOT))
    except ValueError as exc:
        raise RuntimeError("P22 preregistration must be inside the repository") from exc
    if relative != PREREGISTRATION:
        raise RuntimeError("P22 preregistration path mismatch")
    raw = path.read_bytes()
    if _sha(raw) != requested_hash:
        raise RuntimeError("requested P22 preregistration hash mismatch")
    if subprocess.check_output(["git", "status", "--porcelain", "--", relative],
                               cwd=ROOT, text=True):
        raise RuntimeError("P22 preregistration must be clean and committed")
    changed = subprocess.check_output(["git", "diff-tree", "--no-commit-id",
        "--name-only", "-r", "HEAD"], cwd=ROOT, text=True).splitlines()
    if changed != [relative]:
        raise RuntimeError("the immediately preceding commit must contain only the P22 preregistration")
    freeze = _read_freeze(path).get("freeze", {})
    head = _commit()
    parent = subprocess.check_output(["git", "rev-parse", "HEAD^"],
                                     cwd=ROOT, text=True).strip()
    if freeze.get("freeze_commit") != head or freeze.get("freeze_parent_commit") != parent:
        raise RuntimeError("P22 preregistration commit identity mismatch")
    primitive_ceiling = freeze.get("cumulative_primitive_ceiling")
    rule_progress_ceiling = freeze.get("native_rule_progress_ceiling")
    if (isinstance(primitive_ceiling, bool)
            or not isinstance(primitive_ceiling, int)
            or not 1 <= primitive_ceiling <= 120_000):
        raise RuntimeError("freeze must declare a bounded cumulative primitive ceiling")
    if (isinstance(rule_progress_ceiling, bool)
            or not isinstance(rule_progress_ceiling, int)
            or not 1 <= rule_progress_ceiling <= 10_000_000):
        raise RuntimeError("freeze must declare a bounded native rule-progress ceiling")
    current = provenance()
    for key in ("runner_sha256", "analyzer_sha256", "source_bundle_sha256",
            "wrapper_sha256", "loaded_extension_sha256", "build_receipt_sha256",
            "profile_sha256", "world_adapter_sha256", "dependency_closure_sha256"):
        if freeze.get("provenance", {}).get(key) != current.get(key):
            raise RuntimeError(f"P22 runtime/source provenance mismatch: {key}")
    if current["runtime_attestation"].get("status") != "ATTESTED" or current[
            "runtime_attestation"].get("issues"):
        raise RuntimeError("P22 held-out run requires an attested clean native runtime")
    plan = allocation()
    manifest_path = ROOT / freeze.get("checkpoint_manifest_path", "")
    manifest = _load_manifest(manifest_path, freeze.get("checkpoint_manifest_sha256", ""))
    roots, lineages = _index_manifest(manifest)
    frozen_roots = {key: checkpoint.checkpoint_digest for key, checkpoint in roots.items()}
    if freeze.get("ancestor_checkpoint_digests") != frozen_roots:
        raise RuntimeError("P22 ancestor checkpoint roots differ from the freeze")
    analysis_plan = dict(plan)
    analysis_plan["ancestor_checkpoint_digests"] = frozen_roots
    ceilings = freeze.get("resource_ceilings")
    if not isinstance(ceilings, dict) or set(ceilings) != set(RESOURCE_FIELDS):
        raise RuntimeError("P22 freeze must declare a ceiling for every resource field")
    _preflight_checkpoint_resources(freeze, lineages, ceilings)
    analysis_plan["resource_ceilings"] = ceilings
    recorded_plan = freeze.get("allocation_plan")
    if recorded_plan != analysis_plan or freeze.get("allocation_sha256") != _digest(analysis_plan):
        raise RuntimeError("P22 allocation differs from the standalone freeze")
    return freeze, current, {"plan": analysis_plan, "roots": roots, "lineages": lineages,
        "manifest_path": str(manifest_path),
        "manifest_sha256": freeze["checkpoint_manifest_sha256"]}


def _structural_controls(native, roots: dict,
                         lineages: dict | None = None) -> list[dict]:
    adapter = CheckpointWorldAdapter(native, primitive_work_ceiling=100_000)
    root = roots["d4:unchanged"]
    controls = []
    tampered = root.__class__(**(asdict(root) | {"checkpoint_digest": "0" * 64}))
    try:
        adapter.score(tampered, world_id="control:digest", initial_state=[0, 1, 2, 3],
                      goal_state=[0, 1, 2, 3])
    except ValueError:
        controls.append({"control_id": "checkpoint_digest_tampering", "status": "PASS"})
    else:
        controls.append({"control_id": "checkpoint_digest_tampering", "status": "FAIL"})
    malformed = root.__class__(**(asdict(root) | {"params": (0, 0, 2, 3)}))
    try:
        adapter.score(malformed, world_id="control:permutation", initial_state=[0, 1, 2, 3],
                      goal_state=[0, 1, 2, 3])
    except ValueError:
        controls.append({"control_id": "malformed_permutation", "status": "PASS"})
    else:
        controls.append({"control_id": "malformed_permutation", "status": "FAIL"})
    if lineages is None:
        child = roots.get("d4:child_control")
        lineage_ok = (child is not None
                      and child.parent_digest == root.checkpoint_digest)
        checked_links = int(lineage_ok)
    else:
        lineage_ok = True
        checked_links = 0
        for family in FAMILIES:
            for arm in ARMS:
                parent_digest = roots[f"{family}:{arm}"].checkpoint_digest
                for generation in GENERATIONS:
                    checkpoint = lineages[(family, arm, generation)]
                    if checkpoint.parent_digest != parent_digest:
                        lineage_ok = False
                    checked_links += 1
                    parent_digest = checkpoint.checkpoint_digest
    controls.append({"control_id": "lineage_parent_integrity",
        "status": "PASS" if lineage_ok and checked_links else "FAIL",
        "checked_parent_links": checked_links})
    world = {"world_id": "control:repeatability", "initial_state": [0, 1, 2, 3],
             "goal_state": [0, 1, 2, 3]}
    first = adapter.score(root, **world)
    second = adapter.score(root, **world)
    repeatability = first.get("status") == second.get("status") and first.get("score") == second.get("score")
    controls.append({"control_id": "repeatability",
        "status": "PASS" if repeatability else "FAIL",
        "world_id": world["world_id"]})
    return controls


def run_heldout(*, preregistration: Path, requested_hash: str) -> dict:
    freeze, current, loaded = _verify_freeze(preregistration, requested_hash)
    roots, lineages = loaded["roots"], loaded["lineages"]
    generator = {"d4": generate_d4_world_v2,
                 "loopover": generate_loopover_world_v2}
    allocation_plan = loaded["plan"]
    agent = Agent(track_i=False)
    try:
        rows = []
        for family in FAMILIES:
            worlds = [agent_view(generator[family](split="heldout", draw=draw))
                for draw in range(PANEL_SIZE)]
            for generation in GENERATIONS:
                for world in worlds:
                    world_digest = _digest(world)
                    goal_digest = _digest(world["goal_state"])
                    for arm in ARMS:
                        checkpoint = lineages[(family, arm, generation)]
                        row = {"family": family, "generation": generation,
                            "world_id": world["world_id"], "arm": arm,
                            "goal_digest": goal_digest, "world_digest": world_digest,
                            "checkpoint_digest": checkpoint.checkpoint_digest,
                            "parent_digest": checkpoint.parent_digest or
                                roots[f"{family}:{arm}"].checkpoint_digest,
                            "approval_id": checkpoint.approval_id,
                            "verified_receipt_id": checkpoint.receipt_id,
                            "unsafe_output": False, "unauthorized_transition": False}
                        try:
                            outcome = score_checkpoint_world_isolated(
                                asdict(checkpoint), world,
                                cumulative_primitive_ceiling=(
                                    freeze["cumulative_primitive_ceiling"]),
                                native_rule_progress_ceiling=(
                                    freeze["native_rule_progress_ceiling"]),
                                allow_heldout_evaluation=True)
                            snapshot = outcome["resource_snapshot"]
                            wall_time = snapshot["runtime_counters"]["wall_time_seconds"]
                            measured = analyzer_resource_record(snapshot,
                                cumulative_primitive_work=outcome[
                                    "cumulative_primitive_work"],
                                wall_time_seconds=wall_time)
                            row.update({"status": "scored", "score": outcome["score"],
                                "native_learner_status": outcome["status"],
                                "native_task_status": outcome["task_status"],
                                "primitive_budget_respected": outcome[
                                    "primitive_budget_respected"],
                                "rule_progress_limit_respected": outcome[
                                    "rule_progress_limit_respected"],
                                "approval_events_added": outcome[
                                    "approval_events_added"],
                                "world_receipts_added": outcome[
                                    "world_receipts_added"],
                                **measured["resources"],
                                "resource_measurements": measured[
                                    "resource_measurements"]})
                        except Exception as exc:
                            # Keep the task/world/arm row in the denominator.
                            # The analyzer will reject missing resources and
                            # non-scored status rather than silently dropping it.
                            row.update({"status": "worker_failed", "score": None,
                                "native_learner_status": "worker_failed",
                                "evaluation_error_type": type(exc).__name__,
                                "evaluation_error": str(exc)})
                        rows.append(row)
        controls = _structural_controls(agent.native, roots, lineages)
    finally:
        close = getattr(agent.s, "close", None)
        if callable(close):
            close()
    payload = {"phase": PHASE, "split": "heldout",
        "status": "heldout_pending_analysis", "heldout_accessed": True,
        "preregistration_sha256": requested_hash,
        "preregistration_path": str(preregistration.resolve()),
        "freeze_commit": freeze["freeze_commit"], "run_commit": _commit(),
        "allocation_plan": allocation_plan, "allocation_sha256": _digest(allocation_plan),
        "provenance": current, "checkpoint_rows": rows,
        "structural_controls": controls,
        "bootstrap_seed": freeze["bootstrap_seed"]}
    report = analyze_p22(payload, preregistration=preregistration)
    payload["runner_analysis"] = {"status": report["status"],
        "failures": report["failures"], "counts": report["counts"]}
    return payload


def self_check() -> dict:
    plan = allocation()
    assert len(plan["world_ids_by_family"]["d4"]) == PANEL_SIZE
    assert len(plan["selection_world_ids_by_family"]["loopover"]) == PANEL_SIZE
    analyzer = analyzer_self_check()
    assert analyzer["status"] == "PASS"
    # Exercise the loaded native ProcessApply evaluator and structural controls
    # using an identity ancestor fixture. This is a development mechanism check,
    # not a checkpoint lineage or efficacy result.
    agent = Agent(track_i=False)
    try:
        native_result = agent.native.evaluate(
            {"type": "ProcessApply", "p": {"type": "Var", "name": "p"},
             "state": {"type": "Var", "name": "state"}},
            {"p": [0, 1, 2, 3], "state": [1, 0, 2, 3]})
        assert native_result == [1, 0, 2, 3]
        fixture = _identity_checkpoint_fixture()
        child = CheckpointExpression("p22-self-check-child", fixture.checkpoint_digest,
            fixture.expression_digest, fixture.params, 0, 1,
            "0" * 64, "self-check-approval", "self-check-receipt", 0,
            fixture.resource_snapshot_json)
        controls = _structural_controls(agent.native,
            {"d4:unchanged": fixture, "d4:child_control": child})
        assert len(controls) == len(CONTROL_IDS)
        assert all(control["status"] == "PASS" for control in controls)
        bad_child = CheckpointExpression("bad-child", "0" * 64,
            fixture.expression_digest, fixture.params, 0, 1,
            "0" * 64, "self-check-approval", "self-check-receipt", 0,
            fixture.resource_snapshot_json)
        lineage_tamper = _structural_controls(agent.native,
            {"d4:unchanged": fixture, "d4:child_control": bad_child})[2]
        assert lineage_tamper["status"] == "FAIL"
        roots = {f"{family}:{arm}": fixture
                 for family in FAMILIES for arm in ARMS}
        lineages = {}
        for family in FAMILIES:
            for arm in ARMS:
                parent_digest = fixture.checkpoint_digest
                for generation in GENERATIONS:
                    checkpoint_digest = f"{family}:{arm}:g{generation}"
                    lineages[(family, arm, generation)] = CheckpointExpression(
                        checkpoint_id=checkpoint_digest, parent_digest=parent_digest,
                        expression_digest=fixture.expression_digest,
                        params=fixture.params, declared_primitive_work=0,
                        generation=generation, checkpoint_digest=checkpoint_digest,
                        approval_id=("self-check-approval" if arm in {
                            "invention_only", "full"} else None),
                        receipt_id=("self-check-receipt" if arm in {
                            "invention_only", "full"} else None),
                        cumulative_primitive_work=0,
                        resource_snapshot_json=fixture.resource_snapshot_json)
                    parent_digest = checkpoint_digest
        manifest_controls = _structural_controls(agent.native, roots, lineages)
        manifest_lineage = manifest_controls[2]
        assert manifest_lineage["status"] == "PASS"
        assert manifest_lineage["checked_parent_links"] == 24
        broken_lineages = dict(lineages)
        broken_lineages[("loopover", "full", 2)] = CheckpointExpression(
            **(asdict(lineages[("loopover", "full", 2)]) | {
                "parent_digest": "wrong-parent"}))
        broken_controls = _structural_controls(agent.native, roots, broken_lineages)
        assert broken_controls[2]["status"] == "FAIL"
    finally:
        close = getattr(agent.s, "close", None)
        if callable(close):
            close()
    return {"phase": PHASE, "status": "PASS", "heldout_accessed": False,
        "allocation_sha256": _digest(plan),
        "families": list(FAMILIES), "worlds_per_split_family": PANEL_SIZE,
        "native_process_apply": native_result,
        "structural_controls": controls,
        "lineage_tamper_control": lineage_tamper,
        "manifest_lineage_control": manifest_lineage,
        "manifest_lineage_tamper_control": broken_controls[2],
        "analyzer_self_check": analyzer["status"]}


def _identity_checkpoint_fixture() -> CheckpointExpression:
    """Return a digest-valid generation-zero fixture with a native snapshot."""
    from evaluation.process_mastery.p22_resource_accounting import (
        snapshot_native_resources,
    )
    from evaluation.process_mastery.checkpoint_world_adapter import (
        _native_graph_snapshot, _native_graph_snapshot_digest,
    )
    from evaluation.process_mastery.native_process_execution import params_digest
    # A clean, disabled baseline graph is a real native resource observation;
    # the expression itself is the identity permutation.
    agent = Agent(track_i=True)
    try:
        for budget in agent.s.nodes("ThinkingBudget"):
            agent.s.set_attr(budget, "enabled", 1.0)
        identity_params = [0, 1, 2, 3]
        identity_schema = agent.s.add_node("ProcessSchema", {
            "name": "p22-self-check-identity", "kind": "permutation",
            "domain": "p22-self-check", "params": identity_params,
            "source_digest": params_digest(identity_params), "status": "active"})
        agent.s.add_edge(agent.ag, "has_process_schema", identity_schema, {})
        snapshot = snapshot_native_resources(agent)
        graph_json = _native_graph_snapshot(agent)
    finally:
        close = getattr(agent.s, "close", None)
        if callable(close):
            close()
    snapshot_json = json.dumps(snapshot, sort_keys=True, separators=(",", ":"))
    expression_digest = params_digest([0, 1, 2, 3])
    checkpoint_id = "p22-self-check-ancestor"
    payload = {"schema": "p22_native_checkpoint_v1",
        "checkpoint_id": checkpoint_id, "generation": 0,
        "source_digest": expression_digest, "params": [0, 1, 2, 3],
        "primitive_work": 0, "cumulative_primitive_work": 0,
        "resource_snapshot_sha256": snapshot["snapshot_sha256"],
        "native_graph_snapshot_sha256": _native_graph_snapshot_digest(graph_json)}
    checkpoint_digest = _sha(json.dumps(payload, sort_keys=True,
        separators=(",", ":")).encode())
    parent = CheckpointExpression(checkpoint_id, "", expression_digest,
        (0, 1, 2, 3), 0, 0, checkpoint_digest,
        cumulative_primitive_work=0, resource_snapshot_json=snapshot_json,
        native_graph_snapshot_json=graph_json)
    return parent


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("preregistration_sha256", nargs="?")
    parser.add_argument("start", nargs="?", type=int)
    parser.add_argument("stop", nargs="?", type=int)
    parser.add_argument("--preregistration", type=Path,
        default=ROOT / PREREGISTRATION)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args()
    if args.self_check:
        result = self_check()
    else:
        if args.preregistration_sha256 is None or args.start is None or args.stop is None:
            parser.error("held-out run requires preregistration hash and exact draw range")
        if args.start != 0 or args.stop != PANEL_SIZE:
            parser.error("P22 held-out allocation is one fixed 200-world panel per family")
        result = run_heldout(preregistration=args.preregistration,
                             requested_hash=args.preregistration_sha256)
    encoded = json.dumps(result, sort_keys=True, indent=2) + "\n"
    output = args.output
    if output is None and not args.self_check:
        output = ROOT / "evaluation/reports" / (
            f"cognition_linear_p22_v1_{args.preregistration_sha256[:8]}_d0-200.json")
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(encoded, encoding="utf-8")
    else:
        sys.stdout.write(encoded)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

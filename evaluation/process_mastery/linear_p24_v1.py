"""Frozen P24 additive-transfer orchestration and allocation guards."""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for _path in (ROOT, ROOT / "runners/dsl/python"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

import substrate_rs
from evaluation.process_mastery.runtime_attestation import attest
from evaluation.process_mastery.common_target_learner import CommonTargetLearner
from evaluation.process_mastery.target_learning_curve import DOMAIN_PAIRS
from evaluation.process_mastery.target_learning_curve_v2 import (
    ARMS, _attempted_map_verification, _auc, _run_stream,
)
from evaluation.process_mastery.target_learning_worlds import ThermalWorld

PHASE = "linear-p24-v1"
PREREGISTRATION = "docs/research/engine_substrate/COGNITION_LINEAR_P24_PREREG.md"
HELDOUT_STREAMS_PER_PAIR = 200
DEVELOPMENT_STREAMS_PER_PAIR = 8
CONTROL_KINDS = ("duplicate_receipt", "stale_map", "wrong_source_map")
HELDOUT_CONTROLS_PER_KIND = 100
DEVELOPMENT_CONTROLS_PER_KIND = 2
SEED_BASE = 90_000_000
SPLIT_BLOCK = {"development": 0, "heldout": 3_000_000}
FAMILY_CODES = {"heat_to_thermal": 1, "lever_to_latch": 2}
CONTROL_BASE = 94_000_000
RESOURCE_LIMITS = {"target_actions_per_arm": 2,
                   "source_actions_for_source_arms": 2,
                   "external_model_queries": 0,
                   "native_rule_steps_per_learner": 80_000,
                   "graph_bytes_per_target_learner": 100_000,
                   "requested_shared_budget": 100.0,
                   "native_budget_capacity": 16.0,
                   "native_budget_capacity_ceiling": 64.0,
                   "approved_budget_debits_by_arm": {
                       "fresh": 2, "compatible_source": 4,
                       "wrong_source": 4, "same_target_map_work": 4}}

PROVENANCE_FILES = (
    "evaluation/process_mastery/linear_p24_v1.py",
    "evaluation/process_mastery/analyze_linear_p24_v1.py",
    "evaluation/process_mastery/target_learning_curve_v2.py",
    "evaluation/process_mastery/target_learning_curve.py",
    "evaluation/process_mastery/common_target_learner.py",
    "evaluation/process_mastery/target_learner.py",
    "evaluation/process_mastery/target_learning_worlds.py",
    "evaluation/process_mastery/harness.py",
    "evaluation/process_mastery/runtime_attestation.py",
    "evaluation/process_mastery/scorecard.py",
    "scripts/gen_common_target_evidence_seed.py", "seeds/common_target_evidence.json",
    "scripts/gen_additive_transfer_seed.py", "seeds/additive_transfer.json",
    "scripts/gen_target_learning_seed.py", "seeds/target_learning.json",
    "scripts/gen_process_induction_seed.py", "seeds/process_induction.json",
    "substrate/boot_profiles.py", "substrate/boot_core.py",
    "substrate/world_adapter.py", "substrate/seed_loader.py",
    "seeds/cognition_on_params.json",
    "docs/research/engine_substrate/COGNITION_ADDITIVE_TRANSFER_CONTRACT.md",
    "docs/research/engine_substrate/PMB_V1_SPEC.md",
    "runners/dsl/python/substrate_rs/__init__.py",
    "runners/dsl/python/substrate_rs/_native.build.json",
    "runners/dsl/Cargo.toml", "runners/dsl/pyproject.toml", "runners/dsl/uv.lock",
)

# Prior frozen numeric allocation envelopes from P16–P19 and P22. P20/P21
# use disjoint string namespaces and are checked separately below.
PRIOR_NUMERIC_INTERVALS = ((26_000_000, 28_999_999),
                           (29_000_000, 29_999_999),
                           (31_000_000, 33_999_999),
                           (41_000_000, 43_999_999))
PRIOR_STRING_NAMESPACES = ("dev:", "heldout:", "p22:", "development:",
                           "p16:", "p17:", "p18:", "p19:")


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _digest(value) -> str:
    return _sha(json.dumps(value, sort_keys=True, separators=(",", ":"),
                           ensure_ascii=False).encode("utf-8"))


def _commit() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                   text=True).strip()


def _profile_seed_paths() -> list[str]:
    from substrate.boot_profiles import COGNITION_ON_SEEDS
    from substrate.boot_core import CORE_SEEDS
    from substrate.seed_loader import manifest_for

    pending = list(dict.fromkeys((*CORE_SEEDS, *COGNITION_ON_SEEDS)))
    seen = set()
    while pending:
        seed_id = pending.pop()
        if seed_id in seen:
            continue
        seen.add(seed_id)
        try:
            manifest = manifest_for(seed_id)
        except FileNotFoundError:
            # `core` is the built-in substrate root installed by boot_core;
            # it has no JSON seed manifest. All other referenced profile
            # manifests must be present and are hash-bound below.
            if seed_id == "core":
                continue
            raise
        pending.extend(manifest.get("depends_on", ()))
    # The built-in substrate root is installed by boot_core and is not a JSON
    # seed artifact; its source is already bound in PROVENANCE_FILES.
    return sorted(f"seeds/{seed_id}.json" for seed_id in seen if seed_id != "core")


def provenance() -> dict:
    paths = list(PROVENANCE_FILES) + _profile_seed_paths()
    hashes = {relative: _sha((ROOT / relative).read_bytes()) for relative in paths}
    package_dir = Path(substrate_rs.__file__).resolve().parent
    extension = Path(substrate_rs._native.__file__).resolve()
    receipt = package_dir / "_native.build.json"
    profile_paths = ("substrate/boot_profiles.py", "seeds/cognition_on_params.json")
    profile_bundle = [(path, hashes[path]) for path in profile_paths]
    seed_bundle = [(path, hashes[path]) for path in _profile_seed_paths()]
    source_bundle = [(path, hashes[path]) for path in paths]
    return {
        "git_commit": _commit(), "python": sys.version.split()[0],
        "runner_sha256": hashes["evaluation/process_mastery/linear_p24_v1.py"],
        "analyzer_sha256": hashes["evaluation/process_mastery/analyze_linear_p24_v1.py"],
        "source_file_sha256": hashes,
        "source_bundle_sha256": _digest(source_bundle),
        "wrapper_path": str(Path(substrate_rs.__file__).resolve()),
        "wrapper_sha256": hashes["runners/dsl/python/substrate_rs/__init__.py"],
        "loaded_extension_path": str(extension),
        "loaded_extension_sha256": _sha(extension.read_bytes()),
        "build_receipt_path": str(receipt),
        "build_receipt_sha256": _sha(receipt.read_bytes()),
        "profile_sha256": _digest(profile_bundle),
        "profile_seed_bundle_sha256": _digest(seed_bundle),
        "profile_seed_files": _profile_seed_paths(),
        "dependency_closure_sha256": _digest([
            (path, hashes[path]) for path in PROVENANCE_FILES
            if path in {"runners/dsl/Cargo.toml", "runners/dsl/pyproject.toml",
                        "runners/dsl/uv.lock",
                        "runners/dsl/python/substrate_rs/_native.build.json"}]),
        "runtime_attestation": attest(package=substrate_rs, build_receipt=receipt,
                                      require_clean=True),
    }


def allocation(split: str, *, streams_per_pair: int | None = None,
               controls_per_kind: int | None = None) -> dict:
    if split not in {"development", "heldout"}:
        raise ValueError("P24 split must be development or heldout")
    fixed_streams = (DEVELOPMENT_STREAMS_PER_PAIR if split == "development"
                     else HELDOUT_STREAMS_PER_PAIR)
    fixed_controls = (DEVELOPMENT_CONTROLS_PER_KIND if split == "development"
                      else HELDOUT_CONTROLS_PER_KIND)
    if streams_per_pair is not None and streams_per_pair != fixed_streams:
        raise ValueError(f"P24 {split} allocation is fixed at {fixed_streams} streams per pair")
    if controls_per_kind is not None and controls_per_kind != fixed_controls:
        raise ValueError(f"P24 {split} controls are fixed at {fixed_controls} per kind")
    streams, controls = [], []
    for family in FAMILY_CODES:
        for index in range(fixed_streams):
            seed = SEED_BASE + SPLIT_BLOCK[split] + FAMILY_CODES[family] * 10_000 + index
            streams.append({"family": family, "index": index, "seed": seed,
                            "stream_id": f"p24:{split}:{family}:{seed}",
                            "arms": list(ARMS), "context_epoch": 5 + seed % 2})
    for kind_index, kind in enumerate(CONTROL_KINDS):
        for index in range(fixed_controls):
            seed = CONTROL_BASE + SPLIT_BLOCK[split] + kind_index * 1_000 + index
            controls.append({"kind": kind, "index": index, "seed": seed,
                             "control_id": f"p24:{split}:control:{kind}:{seed}"})
    result = {"phase": PHASE, "split": split, "streams_per_pair": fixed_streams,
              "controls_per_kind": fixed_controls, "families": list(FAMILY_CODES),
              "arms": list(ARMS), "checkpoints": [0, 1, 2],
              "resource_limits": dict(RESOURCE_LIMITS),
              "streams": streams, "controls": controls,
              "seed_base": SEED_BASE + SPLIT_BLOCK[split],
              "control_seed_base": CONTROL_BASE + SPLIT_BLOCK[split]}
    audit_allocation_disjointness(result)
    return result


def audit_allocation_disjointness(plan: dict) -> dict:
    seeds = [row["seed"] for row in (*plan["streams"], *plan["controls"])]
    if len(seeds) != len(set(seeds)):
        raise RuntimeError("P24 allocation contains duplicate seeds")
    overlaps = [(seed, lo, hi) for seed in seeds for lo, hi in PRIOR_NUMERIC_INTERVALS
                if lo <= seed <= hi]
    if overlaps:
        raise RuntimeError(f"P24 allocation overlaps prior numeric seed range: {overlaps[0]}")
    names = [row.get("stream_id") or row["control_id"]
             for row in (*plan["streams"], *plan["controls"])]
    if any(any(name.startswith(prefix) for prefix in PRIOR_STRING_NAMESPACES)
           for name in names):
        raise RuntimeError("P24 allocation collides with prior string namespace")
    # Explicit source-range ledger, frozen with the allocation. P20/P21 use
    # event namespaces rather than numeric world seeds.
    return {"status": "DISJOINT", "prior_numeric_intervals": [list(x)
            for x in PRIOR_NUMERIC_INTERVALS],
            "prior_string_namespaces": list(PRIOR_STRING_NAMESPACES),
            "p24_seed_min": min(seeds), "p24_seed_max": max(seeds),
            "unique_seed_count": len(seeds)}


def _check_observed_disjointness() -> dict:
    """Check current P20/P21/P22 public allocation identities against P24."""
    from evaluation.process_mastery.linear_p20_v1 import allocation as p20_allocation
    from evaluation.process_mastery.linear_p21_v1 import allocation as p21_allocation
    from evaluation.process_mastery.linear_p22_v1 import allocation as p22_allocation

    p24 = allocation("heldout")
    p24_ids = {row["stream_id"] for row in p24["streams"]}
    p24_ids.update(row["control_id"] for row in p24["controls"])
    prior_ids = set()
    p20 = p20_allocation("heldout")
    prior_ids.update(row["stream_id"] for row in p20["target"])
    prior_ids.update(row["stream_id"] for row in p20["social"])
    prior_ids.update(row["control_id"] for row in p20["controls"])
    prior_ids.update(p20["explanations"])
    prior_ids.update(stream for row in p21_allocation("heldout")["sleep_streams"]
                     for stream in row["stream_ids"])
    prior_ids.update(stream for row in p21_allocation("heldout")["curriculum_streams"]
                     for stream in row["stream_ids"])
    prior_ids.update(p21_allocation("heldout")["control_ids"])
    p22 = p22_allocation()
    for split in ("training_world_ids_by_family", "selection_world_ids_by_family",
                  "validation_world_ids_by_family", "world_ids_by_family"):
        for values in p22[split].values():
            prior_ids.update(values)
    overlap = p24_ids & prior_ids
    if overlap:
        raise RuntimeError(f"P24 world IDs overlap an earlier frozen protocol: {sorted(overlap)[:1]}")
    return {"status": "DISJOINT", "prior_protocols_checked": ["P20", "P21", "P22"],
            "prior_world_id_count": len(prior_ids), "p24_world_id_count": len(p24_ids),
            "overlap_count": 0}


def _control(row: dict) -> dict:
    from evaluation.process_mastery.target_learning_worlds import (
        HeatSourceWorld, InconsistentHeatSourceWorld, InconsistentLeverSourceWorld,
        ThermalWorld, WorldReceipt,
    )
    kind, seed = row["kind"], row["seed"]
    if kind == "duplicate_receipt":
        learner = CommonTargetLearner(owner_id=row["control_id"])
        receipt = ThermalWorld(object_ids=(f"p24-control:{seed}",)).apply(
            f"p24-control:{seed}", "warm")
        learner.observe_world_receipt(receipt)
        learner.observe_world_receipt(receipt)
        learner.settle()
        observations = [n for n in learner.s.nodes("TransitionObservation")
                        if learner.s.node(n)["attrs"].get("event_id") == receipt.event_id]
        passed = len(observations) == 1 and learner.accounting.target_actions == 1
        return {**row, "status": "PASS" if passed else "FAIL",
                "observations": len(observations), "target_actions": learner.accounting.target_actions,
                "duplicate_rejected_or_idempotent": passed}
    family = DOMAIN_PAIRS[(seed // 1000) % len(DOMAIN_PAIRS)]
    target = family.target_factory((f"p24-control:{seed}:a", f"p24-control:{seed}:b"))
    if kind == "stale_map":
        source = family.source_factory((f"p24-control:{seed}:source-a",
                                        f"p24-control:{seed}:source-b"))
        source_step = family.source_step
        source_epochs = (3, 4)
    else:
        source = family.mismatch_source_factory((f"p24-control:{seed}:source-a",
                                                 f"p24-control:{seed}:source-b"))
        source_step = family.mismatch_source_step
        source_epochs = (3, 3)
    learner = CommonTargetLearner(owner_id=row["control_id"],
                                  additive_transfer_enabled=True)
    target_receipts, source_receipts = [], []
    for i, (target_id, source_id) in enumerate((
            (f"p24-control:{seed}:a", f"p24-control:{seed}:source-a"),
            (f"p24-control:{seed}:b", f"p24-control:{seed}:source-b"))):
        target_receipt = family.target_step(target, target_id)
        source_receipt = source_step(source, source_id)
        target_receipts.append(target_receipt)
        source_receipts.append(source_receipt)
        learner.observe_world_receipt(target_receipt, map_view={
            "pair_id": f"{row['control_id']}:pair:{i}", "source_receipt": source_receipt,
            "source_epoch": source_epochs[i]})
    learner.settle()
    candidates = [learner.s.node(n)["attrs"] for n in learner.s.nodes("RepresentationMap")
                  if learner.s.node(n)["attrs"].get("mapping_kind") == "induced_categorical_effect"]
    verification = _attempted_map_verification(
        family, source_receipts, target_receipts, frame_epoch=5)
    ordinary = learner.hypotheses()
    map_observations = [learner.s.node(n)["attrs"]
                        for n in learner.s.nodes("TargetMapObservation")]
    map_rejected = (not candidates if kind == "stale_map" else
                    verification.get("status") == "rejected")
    passed = map_rejected and bool(ordinary) and all(
        learner.s.node(n)["attrs"].get("status") == "observed_pair"
        for n in learner.s.nodes("TargetMapObservation"))
    return {**row, "status": "PASS" if passed else "FAIL",
            "target_events": [r.event_id for r in target_receipts],
            "source_events": [r.event_id for r in source_receipts],
            "map_candidate_count": len(candidates),
            "ordinary_hypothesis_count": len(ordinary),
            "map_pairs_retained": len(learner.s.nodes("TargetMapObservation")),
            "map_candidate_statuses": [row.get("status") for row in candidates],
            "map_observation_statuses": [row.get("status") for row in map_observations],
            "explicit_verification_status": verification.get("status"),
            "map_rejection_expected": kind}


def _run_panel(plan: dict) -> tuple[list[dict], list[dict]]:
    streams = []
    for item in plan["streams"]:
        pair = next(row for row in DOMAIN_PAIRS if row.name == item["family"])
        rows = _run_stream(pair, item["stream_id"], context_epoch=item["context_epoch"])
        shared_elapsed = rows["_meta"]["elapsed_seconds"]
        for arm in ARMS:
            row = rows[arm]
            row["normalized_auc"] = _auc(row["curve"])
            row["seed"] = item["seed"]
            row["allocation_split"] = plan["split"]
            row["shared_stream_elapsed_seconds"] = shared_elapsed
            row["resource_limits"] = dict(plan["resource_limits"])
            if row["target_actions"] > plan["resource_limits"]["target_actions_per_arm"]:
                raise RuntimeError("P24 target action ceiling exceeded")
            if row["native_rule_work"] > plan["resource_limits"]["native_rule_steps_per_learner"]:
                raise RuntimeError("P24 target learner native-work ceiling exceeded")
            if row["source_native_rule_work"] > plan["resource_limits"]["native_rule_steps_per_learner"]:
                raise RuntimeError("P24 source learner native-work ceiling exceeded")
            if row["graph"]["bytes"] > plan["resource_limits"]["graph_bytes_per_target_learner"]:
                raise RuntimeError("P24 target learner graph-byte ceiling exceeded")
            if (row["shared_budget"].get("capacity")
                    != plan["resource_limits"]["native_budget_capacity"]
                    or row["shared_budget"].get("capacity_ceiling")
                    != plan["resource_limits"]["native_budget_capacity_ceiling"]):
                raise RuntimeError("P24 native budget differs from frozen limits")
            expected_debits = plan["resource_limits"]["approved_budget_debits_by_arm"][arm]
            if row["shared_budget_debits"] != expected_debits:
                raise RuntimeError("P24 native shared-budget debits differ from frozen arm limits")
            streams.append(row)
    controls = [_control(row) for row in plan["controls"]]
    return streams, controls


def run_development(*, self_check=False) -> dict:
    control_count = 2 if self_check else DEVELOPMENT_CONTROLS_PER_KIND
    plan = allocation("development", controls_per_kind=control_count)
    provenance_record = provenance()
    streams, controls = _run_panel(plan)
    return {"phase": PHASE, "split": "development", "status": "development_only",
            "heldout_accessed": False, "self_check": bool(self_check),
            "provenance": provenance_record, "allocation": plan,
            "allocation_sha256": _digest(plan),
            "disjointness": audit_allocation_disjointness(plan),
            "observed_disjointness": _check_observed_disjointness(),
            "streams": streams, "controls": controls,
            "structural_status": "PASS" if all(x["status"] == "PASS" for x in controls)
            else "FAIL"}


def _read_freeze(path: Path) -> dict:
    match = re.search(r"^P24_FREEZE_JSON: (\{.*\})$",
                      path.read_text(encoding="utf-8"), re.MULTILINE)
    if not match:
        raise RuntimeError("P24 preregistration lacks its machine-readable freeze record")
    return json.loads(match.group(1))


def _verify_preregistration(path: Path) -> tuple[dict, dict, dict]:
    relative = str(path.resolve().relative_to(ROOT))
    if relative != PREREGISTRATION:
        raise RuntimeError("P24 preregistration path mismatch")
    dirty = subprocess.check_output(["git", "status", "--porcelain", "--", relative],
                                    cwd=ROOT, text=True)
    if dirty:
        raise RuntimeError("P24 preregistration must be committed before held-out access")
    changed = subprocess.check_output(["git", "diff-tree", "--no-commit-id", "--name-only",
                                       "-r", "HEAD"], cwd=ROOT, text=True).splitlines()
    if changed != [relative]:
        raise RuntimeError("the immediately preceding commit must contain only the P24 preregistration")
    frozen = _read_freeze(path)
    parent = subprocess.check_output(["git", "rev-parse", "HEAD^"], cwd=ROOT,
                                     text=True).strip()
    if frozen.get("freeze_parent_commit") != parent:
        raise RuntimeError("P24 preregistration parent commit mismatch")
    current = provenance()
    for key in ("runner_sha256", "analyzer_sha256", "source_bundle_sha256",
                "wrapper_sha256", "loaded_extension_sha256", "build_receipt_sha256",
                "profile_sha256", "profile_seed_bundle_sha256",
                "dependency_closure_sha256"):
        if frozen.get(key) != current.get(key):
            raise RuntimeError(f"P24 provenance mismatch: {key}")
    development = allocation("development")
    heldout = allocation("heldout")
    development_sha, heldout_sha = _digest(development), _digest(heldout)
    if frozen.get("development_allocation_sha256") != development_sha:
        raise RuntimeError("P24 development allocation digest mismatch")
    if frozen.get("heldout_allocation_sha256") != heldout_sha:
        raise RuntimeError("P24 held-out allocation digest mismatch")
    if frozen.get("primary") != {"metric": "normalized_learning_curve_auc",
                                  "comparison": "compatible_minus_stronger_source_free",
                                  "minimum_gain": 0.10}:
        raise RuntimeError("P24 primary estimand mismatch")
    runtime = current["runtime_attestation"]
    if runtime.get("status") != "ATTESTED" or runtime.get("issues"):
        raise RuntimeError("P24 held-out execution requires attested runtime")
    return frozen, current, heldout


def run_heldout(*, preregistration: str | Path, output: str | Path) -> dict:
    path, output = Path(preregistration).resolve(), Path(output).resolve()
    if output.exists():
        raise RuntimeError("P24 held-out output already exists; the frozen run is single-use")
    frozen, provenance_record, plan = _verify_preregistration(path)
    marker = ROOT / "evaluation/process_mastery/results/.p24_heldout_run_started"
    try:
        with marker.open("x", encoding="utf-8") as handle:
            handle.write(json.dumps({"phase": PHASE,
                                     "preregistration_sha256": _sha(path.read_bytes()),
                                     "allocation_sha256": _digest(plan)}) + "\n")
    except FileExistsError as exc:
        raise RuntimeError("P24 held-out draw was already started") from exc
    streams, controls = _run_panel(plan)
    result = {"phase": PHASE, "split": "heldout", "status": "heldout_pending_analysis",
              "heldout_accessed": True,
              "preregistration_path": str(path.relative_to(ROOT)),
              "preregistration_sha256": _sha(path.read_bytes()),
              "freeze_commit": _commit(), "run_commit": _commit(),
              "provenance": provenance_record, "allocation": plan,
              "allocation_sha256": _digest(plan),
              "disjointness": audit_allocation_disjointness(plan),
              "observed_disjointness": _check_observed_disjointness(),
              "streams": streams, "controls": controls,
              "structural_status": "PASS" if all(x["status"] == "PASS" for x in controls)
              else "FAIL"}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", choices=("development", "heldout"), default="development")
    parser.add_argument("--self-check", action="store_true")
    parser.add_argument("--preregistration", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.split == "development":
        result = run_development(self_check=args.self_check)
        args.output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n",
                               encoding="utf-8")
    else:
        if not args.preregistration:
            raise RuntimeError("P24 held-out run requires --preregistration")
        result = run_heldout(preregistration=args.preregistration, output=args.output)
    print(args.output)
    if result["structural_status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()

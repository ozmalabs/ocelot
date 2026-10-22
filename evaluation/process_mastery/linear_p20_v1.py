"""P20 development orchestrator for target transfer and social acquisition.

Held-out execution is deliberately unavailable until the complete protocol,
analyzer, allocation and runtime attestation are frozen in the standalone
P20 preregistration. This runner currently exposes only development checks.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for _path in (ROOT, ROOT / "runners/dsl/python"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from evaluation.process_mastery.social_sequence_development import (
    run_development_controls, run_development_panel as run_social_panel,
)
from evaluation.process_mastery.explanation_development import (
    run_development_panel as run_explanation_panel,
)
from evaluation.process_mastery.target_learning_curve import (
    run_development_panel as run_target_panel,
)
from evaluation.process_mastery.runtime_attestation import attest
import substrate_rs

PHASE = "linear-p20-v1"
TARGET_ARMS = ("fresh", "mapped_source", "mismatched_source")
SOCIAL_ARMS = ("observation", "demonstration", "instruction", "reward_only")
CONTROL_KINDS = ("wrong_frame", "missing_step", "body_mismatch", "false_description")
HELDOUT_STREAMS_PER_PAIR = 200
HELDOUT_SOCIAL_STREAMS_PER_ARM = 200
HELDOUT_CONTROLS_PER_KIND = 25
HELDOUT_EXPLANATION_STREAMS = 200
PREREGISTRATION = "docs/research/engine_substrate/COGNITION_LINEAR_P20_PREREG.md"
PROVENANCE_FILES = (
    "evaluation/process_mastery/linear_p20_v1.py",
    "evaluation/process_mastery/analyze_linear_p20_v1.py",
    "evaluation/process_mastery/target_learning_curve.py",
    "evaluation/process_mastery/target_learner.py",
    "evaluation/process_mastery/target_learning_worlds.py",
    "evaluation/process_mastery/social_sequence_development.py",
    "evaluation/process_mastery/observed_sequence_inputs.py",
    "evaluation/process_mastery/observed_sequence_execution.py",
    "evaluation/process_mastery/explanation_development.py",
    "evaluation/process_mastery/explanation_rebuild.py",
    "evaluation/process_mastery/harness.py",
    "evaluation/process_mastery/runtime_attestation.py",
    "domains/language_world.py", "domains/language_production.py",
    "domains/process_explanation_language.py", "scripts/language_test.py",
    "substrate/boot_profiles.py", "seeds/cognition_on_params.json",
    "scripts/gen_target_learning_seed.py", "seeds/target_learning.json",
    "scripts/gen_observed_sequence_learning_seed.py", "seeds/observed_sequence_learning.json",
    "scripts/gen_process_explanation_seed.py", "seeds/process_explanation.json",
    "docs/research/engine_substrate/COGNITION_LEARNING_TRANSFER_CONTRACT.md",
    "runners/dsl/python/substrate_rs/__init__.py",
    "runners/dsl/python/substrate_rs/_native.build.json",
    "runners/dsl/Cargo.toml", "runners/dsl/pyproject.toml", "runners/dsl/uv.lock",
    "runners/dsl/src/process_algebra.rs", "runners/dsl/src/term.rs",
    "runners/dsl/src/cognitive_cycle.rs",
)


def _commit():
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                       text=True).strip()
    except Exception:
        return "unavailable"


def _bundle(paths, hashes):
    items = [(path, hashes[path]) for path in paths]
    return hashlib.sha256(json.dumps(items, sort_keys=True,
                                     separators=(",", ":")).encode()).hexdigest()


def _provenance():
    hashes = {}
    source = hashlib.sha256()
    for relative in PROVENANCE_FILES:
        data = (ROOT / relative).read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        hashes[relative] = digest
        source.update(relative.encode() + b"\0" + data + b"\0")
    package_dir = Path(substrate_rs.__file__).resolve().parent
    extension = Path(substrate_rs._native.__file__).resolve()
    receipt = package_dir / "_native.build.json"
    profile_paths = ("substrate/boot_profiles.py", "seeds/cognition_on_params.json")
    world_paths = ("evaluation/process_mastery/target_learning_worlds.py",
                   "evaluation/process_mastery/social_sequence_development.py",
                   "evaluation/process_mastery/explanation_development.py",
                   "domains/language_world.py", "domains/language_production.py",
                   "domains/process_explanation_language.py")
    dependency_paths = ("runners/dsl/Cargo.toml", "runners/dsl/pyproject.toml",
                        "runners/dsl/uv.lock",
                        "runners/dsl/python/substrate_rs/_native.build.json")
    return {
        "git_commit": _commit(), "python": sys.version.split()[0],
        "runner_sha256": hashes["evaluation/process_mastery/linear_p20_v1.py"],
        "analyzer_sha256": hashes["evaluation/process_mastery/analyze_linear_p20_v1.py"],
        "source_bundle_sha256": source.hexdigest(), "source_file_sha256": hashes,
        "wrapper_path": str(Path(substrate_rs.__file__).resolve()),
        "wrapper_sha256": hashes["runners/dsl/python/substrate_rs/__init__.py"],
        "loaded_extension_path": str(extension),
        "loaded_extension_sha256": hashlib.sha256(extension.read_bytes()).hexdigest(),
        "build_receipt_path": str(receipt),
        "build_receipt_sha256": hashlib.sha256(receipt.read_bytes()).hexdigest(),
        "runtime_attestation": attest(package=substrate_rs, build_receipt=receipt,
                                      require_clean=True),
        "profile_sha256": _bundle(profile_paths, hashes),
        "world_adapter_sha256": _bundle(world_paths, hashes),
        "dependency_closure_sha256": _bundle(dependency_paths, hashes),
    }


def allocation(split, *, target_streams_per_pair=4, social_streams_per_arm=2,
               social_controls_per_kind=1, explanation_streams=2):
    """Enumerate exact split rows without consulting learned operators."""
    if split == "heldout":
        fixed = (HELDOUT_STREAMS_PER_PAIR, HELDOUT_SOCIAL_STREAMS_PER_ARM,
                 HELDOUT_CONTROLS_PER_KIND, HELDOUT_EXPLANATION_STREAMS)
        supplied = (target_streams_per_pair, social_streams_per_arm,
                    social_controls_per_kind, explanation_streams)
        if supplied not in {fixed, (4, 2, 1, 2)}:
            raise ValueError("held-out allocation counts are frozen")
        target_streams_per_pair, social_streams_per_arm, social_controls_per_kind, explanation_streams = fixed
    elif split != "development":
        raise ValueError("split must be development or heldout")
    prefix = "dev" if split == "development" else "heldout"
    control_prefix = "dev-control" if split == "development" else "heldout-control"
    pairs = ("heat_to_thermal", "lever_to_latch")
    return {
        "split": split,
        "target": [{"domain_pair": pair, "stream_id": f"{prefix}:{pair}:{index:04d}",
                    "arms": list(TARGET_ARMS)}
                   for pair in pairs for index in range(target_streams_per_pair)],
        "social": [{"stream_id": f"{prefix}:{arm}:{index:04d}", "arm": arm}
                   for arm in SOCIAL_ARMS for index in range(social_streams_per_arm)],
        "controls": [{"control_id": f"{control_prefix}:{kind}:{index:04d}", "kind": kind}
                     for kind in CONTROL_KINDS for index in range(social_controls_per_kind)],
        "explanations": [f"{prefix}:explanation:{index:04d}"
                         for index in range(explanation_streams)],
        "primary": {"metric": "normalized_learning_curve_auc",
                    "comparison": "mapped_source_minus_fresh",
                    "minimum_gain": 0.20},
        "secondary_interaction_rule": {"enabled": False,
                                       "minimum_reduction": 0.25,
                                       "maximum_success_loss": 0.02},
    }


def _frozen_record(path):
    import re
    match = re.search(r"^P20_FREEZE_JSON: (\{.*\})$", path.read_text(), re.MULTILINE)
    if not match:
        raise RuntimeError("P20 preregistration lacks its machine-readable freeze record")
    return json.loads(match.group(1))


def _verify_preregistration(path):
    relative = str(path.resolve().relative_to(ROOT))
    if relative != PREREGISTRATION:
        raise RuntimeError("P20 preregistration path mismatch")
    dirty = subprocess.check_output(["git", "status", "--porcelain", "--", relative],
                                    cwd=ROOT, text=True)
    if dirty:
        raise RuntimeError("P20 preregistration must be committed before held-out access")
    changed = subprocess.check_output(["git", "diff-tree", "--no-commit-id", "--name-only",
                                       "-r", "HEAD"], cwd=ROOT, text=True).splitlines()
    if changed != [relative]:
        raise RuntimeError("the immediately preceding commit must contain only the P20 preregistration")
    frozen = _frozen_record(path)
    current = _provenance()
    for key in ("runner_sha256", "analyzer_sha256", "source_bundle_sha256",
                "wrapper_sha256", "loaded_extension_sha256", "build_receipt_sha256",
                "profile_sha256", "world_adapter_sha256", "dependency_closure_sha256"):
        if frozen.get(key) != current.get(key):
            raise RuntimeError(f"P20 preregistration provenance mismatch: {key}")
    dev = allocation("development", target_streams_per_pair=8,
                     social_streams_per_arm=8, social_controls_per_kind=25,
                     explanation_streams=8)
    heldout = allocation("heldout")
    dev_sha = hashlib.sha256(json.dumps(dev, sort_keys=True,
                                        separators=(",", ":")).encode()).hexdigest()
    heldout_sha = hashlib.sha256(json.dumps(heldout, sort_keys=True,
                                             separators=(",", ":")).encode()).hexdigest()
    if frozen.get("development_allocation_sha256") != dev_sha:
        raise RuntimeError("P20 development allocation digest mismatch")
    if frozen.get("heldout_allocation_sha256") != heldout_sha:
        raise RuntimeError("P20 held-out allocation digest mismatch")
    if frozen.get("primary") != heldout["primary"]:
        raise RuntimeError("P20 primary criterion mismatch")
    if frozen.get("secondary_interaction_rule") != heldout["secondary_interaction_rule"]:
        raise RuntimeError("P20 secondary criterion mismatch")
    runtime = current["runtime_attestation"]
    if runtime.get("status") != "ATTESTED" or runtime.get("issues"):
        raise RuntimeError("P20 held-out execution requires attested runtime")
    return frozen, current, heldout, heldout_sha


def run_development(*, target_streams_per_pair=4, social_streams_per_arm=2,
                    social_controls_per_kind=1, explanation_streams=2):
    """Run all current P20 development panels without a held-out allocation."""
    target = run_target_panel(streams_per_pair=target_streams_per_pair)
    social = run_social_panel(streams_per_arm=social_streams_per_arm)
    controls = run_development_controls(per_kind=social_controls_per_kind)
    explanations = run_explanation_panel(streams=explanation_streams)
    provenance = _provenance()
    allocation_plan = allocation(
        "development", target_streams_per_pair=target_streams_per_pair,
        social_streams_per_arm=social_streams_per_arm,
        social_controls_per_kind=social_controls_per_kind,
        explanation_streams=explanation_streams)
    allocation_sha = hashlib.sha256(json.dumps(
        allocation_plan, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return {
        "phase": PHASE, "split": "development", "status": "development_only",
        "heldout_accessed": False, "development_commit": _commit(),
        "python": platform.python_version(),
        "provenance": provenance,
        "allocation_plan": allocation_plan,
        "allocation_sha256": allocation_sha,
        "allocation": {
            "target_streams_per_pair": target_streams_per_pair,
            "target_domain_pairs": target["domain_pairs"],
            "social_streams_per_arm": social_streams_per_arm,
            "social_arms": social["arms"],
            "social_controls_per_kind": social_controls_per_kind,
            "social_control_count": len(controls),
            "explanation_streams": explanation_streams,
            "primary_metric": "normalized_learning_curve_auc",
            "primary_comparison": "mapped_source_minus_fresh",
            "primary_minimum_gain": 0.20,
        },
        "target_learning": target,
        "social_acquisition": social,
        "explanation_rebuild": explanations,
        "structural_controls": controls,
        "structural_status": "PASS" if all(row["status"] == "PASS"
                                              for row in controls) else "FAIL",
    }


def run_heldout(*, preregistration):
    path = Path(preregistration).resolve()
    frozen, provenance, allocation_plan, allocation_sha = _verify_preregistration(path)
    target = run_target_panel(streams_per_pair=HELDOUT_STREAMS_PER_PAIR,
                              stream_prefix="heldout")
    social = run_social_panel(streams_per_arm=HELDOUT_SOCIAL_STREAMS_PER_ARM,
                              stream_prefix="heldout")
    controls = run_development_controls(per_kind=HELDOUT_CONTROLS_PER_KIND,
                                        control_prefix="heldout-control")
    explanations = run_explanation_panel(streams=HELDOUT_EXPLANATION_STREAMS,
                                         stream_prefix="heldout")
    if any(row["status"] != "PASS" for row in controls):
        raise RuntimeError("P20 held-out structural control failed")
    return {
        "phase": PHASE, "split": "heldout", "status": "heldout_pending_analysis",
        "heldout_accessed": True, "preregistration_path": str(path),
        "preregistration_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "freeze_commit": frozen.get("freeze_commit"), "run_commit": _commit(),
        "provenance": provenance, "allocation_plan": allocation_plan,
        "allocation_sha256": allocation_sha,
        "allocation": {
            "target_streams_per_pair": HELDOUT_STREAMS_PER_PAIR,
            "target_domain_pairs": target["domain_pairs"],
            "social_streams_per_arm": HELDOUT_SOCIAL_STREAMS_PER_ARM,
            "social_arms": social["arms"],
            "social_controls_per_kind": HELDOUT_CONTROLS_PER_KIND,
            "social_control_count": len(controls),
            "explanation_streams": HELDOUT_EXPLANATION_STREAMS,
            "primary_metric": "normalized_learning_curve_auc",
            "primary_comparison": "mapped_source_minus_fresh",
            "primary_minimum_gain": 0.20,
        },
        "target_learning": target, "social_acquisition": social,
        "explanation_rebuild": explanations, "structural_controls": controls,
        "structural_status": "PASS",
    }


def run(split, *, preregistration=None, **kwargs):
    if split == "development":
        return run_development(**kwargs)
    if split == "heldout":
        if preregistration is None:
            raise RuntimeError("held-out P20 requires --preregistration")
        if kwargs:
            raise ValueError("held-out allocation counts are fixed")
        return run_heldout(preregistration=preregistration)
    raise ValueError("split must be development or heldout")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", choices=("development", "heldout"),
                        default="development")
    parser.add_argument("--target-streams-per-pair", type=int, default=4)
    parser.add_argument("--social-streams-per-arm", type=int, default=2)
    parser.add_argument("--social-controls-per-kind", type=int, default=1)
    parser.add_argument("--explanation-streams", type=int, default=2)
    parser.add_argument("--preregistration", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = run(args.split,
                 target_streams_per_pair=args.target_streams_per_pair,
                 social_streams_per_arm=args.social_streams_per_arm,
                 social_controls_per_kind=args.social_controls_per_kind,
                 explanation_streams=args.explanation_streams,
                 preregistration=args.preregistration)
    encoded = json.dumps(result, sort_keys=True, indent=2) + "\n"
    if args.output:
        args.output.write_text(encoded, encoding="utf-8")
    else:
        print(encoded)
    if result["structural_status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()

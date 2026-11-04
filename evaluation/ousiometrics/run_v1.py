"""Frozen, read-only P28 representation-value runner."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Iterable

ROOT = Path(__file__).resolve().parents[2]
REPO = ROOT
PREREG = REPO / "docs/research/engine_substrate/COGNITION_OUSIOMETRIC_PREREG_V1.md"
RESULTS_DIR = REPO / "evaluation/ousiometrics/results"
BUILD_RECEIPT = REPO / "runners/dsl/python/substrate_rs/_native.build.json"

from evaluation.ousiometrics.behavior_panel import (
    CONTROL_ARMS, PRIMARY_ARMS, development_panel,
)
from evaluation.ousiometrics.distribution_panel import present_regime, summarize_presentations
from evaluation.ousiometrics.geometry_reference import (
    PAPER_EQ4_DISPLAY, audit_transform, inverse_rows, transform_rows,
)
from evaluation.ousiometrics.lexical_validation import lexical_readiness
from evaluation.ousiometrics.native_adapter import NativeOusiometricInvestigation
from evaluation.ousiometrics.source_manifest import PAPER_TRANSFORM, manifest_dict
from evaluation.process_mastery.runtime_attestation import attest
from scripts.lint_orphan_signals import scan_orphan_signals
from scripts.report_seed_boot_status import build_seed_boot_report
from domains.future_option_risk import FutureManifold, ManifoldProjection, evaluate_future_manifold
from substrate.boot_core import CORE_SEEDS

FAMILIES = ("tool_intervention", "social_request_repair")
N_REPLICATES = 200
BOOTSTRAP_REPLICATES = 10_000
TOOL_SEED_START = 28_202_610_000
SOCIAL_SEED_START = 36_202_610_000
FRAME_SEED = REPO / "seeds/ousiometric_frames.json"
ACQUISITION_SEED = REPO / "seeds/ousiometric_acquisition.json"
SOURCE_FILES = (
    "evaluation/ousiometrics/behavior_panel.py",
    "evaluation/ousiometrics/distribution_panel.py",
    "evaluation/ousiometrics/geometry_reference.py",
    "evaluation/ousiometrics/lexical_validation.py",
    "evaluation/ousiometrics/native_adapter.py",
    "evaluation/ousiometrics/run_v1.py",
    "evaluation/ousiometrics/analyze_v1.py",
    "evaluation/ousiometrics/source_manifest.py",
    "evaluation/ousiometrics/worlds.py",
    "evaluation/process_mastery/common_target_learner.py",
    "evaluation/process_mastery/target_learner.py",
    "domains/commitment_gate.py",
    "domains/future_option_risk.py",
    "scripts/gen_response_inhibition_seed.py",
    "substrate/world_adapter.py",
    "evaluation/process_mastery/harness.py",
    "docs/research/engine_substrate/COGNITION_OUSIOMETRIC_CONTRACT.md",
    "docs/research/engine_substrate/OUSIOMETRIC_DATA_MANIFEST.md",
    "tests/test_ousiometric_native_adapter.py",
    "tests/test_ousiometric_causal_controls.py",
    "tests/test_ousiometric_worlds.py",
    "tests/test_ousiometric_behavior_panel.py",
    "tests/test_ousiometrics_geometry.py",
    "tests/test_ousiometric_distribution_panel.py",
    "tests/test_ousiometric_lexical_validation.py",
    "tests/test_ousiometric_risk_boundary.py",
    "tests/test_response_inhibition_migrated.py",
    "seeds/ousiometric_frames.json",
    "seeds/ousiometric_acquisition.json",
    "seeds/response_inhibition.json",
) + tuple(f"seeds/{seed_id}.json" for seed_id in CORE_SEEDS) + tuple(
    f"seeds/{seed_id}.json" for seed_id in
    ("qualia_acquisition", "qualia_behavior", "thinking_budget",
     "process_induction", "target_learning"))


def sha256_file(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _source_hashes() -> dict[str, str]:
    return {rel: sha256_file(REPO / rel) for rel in SOURCE_FILES}


def _runtime_attestation() -> dict:
    import substrate_rs
    return attest(package=substrate_rs, native_module=substrate_rs._native,
                  build_receipt=BUILD_RECEIPT)


def _risk_control() -> dict:
    required = [{"time": i, "cells": {"core": {
        "weight": 2.0, "information": 2.0, "metadata": {"kind": "retained"}}},
        "links": []} for i in range(3)]
    projected = [{"time": i, "cells": {"core": {
        "weight": 2.0, "information": 2.0, "metadata": {"kind": "retained"}}},
        "links": []} for i in range(3)]
    projected[1]["cells"]["escape"] = {
        "weight": 1.0, "information": 1.0, "metadata": {"kind": "measured-escape"}}
    result = evaluate_future_manifold(
        FutureManifold("p28-self-check", 2, 1.0, 0.0, required),
        ManifoldProjection("p28-self-check", projected, 1, 0.5))
    return {"status": "PASS" if not result.allowed
            and result.reason == "outside_future_manifold" else "FAIL",
            "decision": result.reason,
            "escape_shape_count": sum(bool(shape.cells or shape.links)
                                       for shape in result.escape_tube)}


def _host_veto_control() -> dict:
    from scripts.gen_response_inhibition_seed import build_seed
    from substrate.dsl import Lit
    from substrate.jsonio import term_to_json
    from substrate.world_adapter import WorldAdapter

    adapter = WorldAdapter(seeds=())
    adapter.inner.load_seed_manifest(build_seed(), adapter.agent)
    policy = adapter.s.nodes("ResponseInhibitionPolicy")[0]
    adapter.inner.set_attr(policy, "enabled", 1.0)
    mode = adapter.s.add_node("NetworkModeState", {"epoch": 4.0, "mode": "awake"})
    adapter.inner.add_edge_unchecked(adapter.agent, "has_network_mode_state", mode)
    request = adapter.s.add_node("ActionRequest", {
        "request_id": "p28-self-check-veto", "source_epoch": 4.0,
        "action_key": "advance", "status": "authorized"})
    adapter.s.add_edge(adapter.agent, "has_action_request", request)
    authorization = adapter.s.add_node("ActionAuthorization", {
        "authorization_id": "p28-self-check-auth", "status": "pending",
        "request_id": "p28-self-check-veto", "source_epoch": 4.0,
        "action_key": "advance", "sink_route": "count"})
    adapter.s.add_edge(request, "has_action_authorization", authorization)
    stop = adapter.s.add_node("ActionStopEvent", {
        "request_id": "p28-self-check-veto", "source_epoch": 4.0, "status": "pending"})
    adapter.s.add_edge(request, "has_action_stop", stop)
    emitted = []
    adapter.register_reflex_response("count", lambda _adapter: emitted.append(True))
    adapter.install_reflex("advance", term_to_json(Lit(True)), "count")
    adapter.fire_reflexes()
    passed = (not emitted
              and adapter.s.node(request)["attrs"].get("status") == "withheld"
              and adapter.s.node(authorization)["attrs"].get("status") == "revoked"
              and adapter.s.node(stop)["attrs"].get("status") == "withheld")
    return {"status": "PASS" if passed else "FAIL", "sink_emissions": len(emitted),
            "request_status": adapter.s.node(request)["attrs"].get("status"),
            "authorization_status": adapter.s.node(authorization)["attrs"].get("status")}


def _distribution_control() -> dict:
    source = [
        {"event_id": "event-a", "type_id": "tool-small", "token_id": "common",
         "adverse": False, "prediction_error": False, "coordinates": (-.3, -.5, -.2)},
        {"event_id": "event-b", "type_id": "tool-large", "token_id": "common",
         "adverse": False, "prediction_error": False, "coordinates": (.1, -.5, -.2)},
        {"event_id": "event-c", "type_id": "rare-harm", "token_id": "rare",
         "adverse": True, "prediction_error": True, "coordinates": (.5, .5, .1)},
    ]
    regimes = {}
    for name, kwargs in (
        ("uniform_type", {}),
        ("measured_token_frequency", {"token_frequency": {"common": 20, "rare": 1}}),
        ("shuffled_frequency", {"seed": 19,
                                 "token_frequency": {"common": 20, "rare": 1}}),
    ):
        rows = present_regime(source, name, **kwargs)
        summary = summarize_presentations(rows)
        regimes[name] = {"unique_event_count": summary["unique_event_count"],
                         "adverse_error_rate": summary["adverse_error_rate"],
                         "event_error_rate": summary["event_error_rate"],
                         "geometry": summary["geometry"]}
    return {"status": "PASS" if all(
        result["unique_event_count"] == 3 and result["adverse_error_rate"] == 1.0
        for result in regimes.values()) else "FAIL", "regimes": regimes}


def _orphan_and_boot_audit() -> dict:
    orphan_map = scan_orphan_signals(REPO)
    p28_orphans = {name: value for name, value in orphan_map.items()
                   if any(token in name.lower() for token in
                          ("ousiometric", "p28_frame", "p28_acquisition"))}
    boot = build_seed_boot_report(REPO)
    selected = {key: boot.get(key) for key in
                ("ousiometric_frames", "ousiometric_acquisition")}
    valid_boot = all(row and row["class"] == "SLO" and row["self_load_only"]
                     and not [dep for dep in row["broken_deps"] if dep != "core"]
                     for row in selected.values())
    return {"status": "PASS" if not p28_orphans and valid_boot else "FAIL",
            "p28_orphans": p28_orphans, "seed_boot": selected}


def self_check() -> dict:
    """Run small development-only structural, math, and loaded-native checks."""
    audit = audit_transform(PAPER_EQ4_DISPLAY)
    samples = [[-.4, .1, .2], [.3, -.2, .1], [.5, .0, -.3]]
    roundtrip = inverse_rows(transform_rows(samples, PAPER_EQ4_DISPLAY), PAPER_EQ4_DISPLAY)
    import numpy as np
    math_ok = audit.rank == 3 and float(np.max(np.abs(roundtrip - samples))) <= 1e-10

    behavior = development_panel(seeds=(TOOL_SEED_START,), frames=PRIMARY_ARMS + CONTROL_ARMS)
    expected_pairs = {(frame, family) for frame in PRIMARY_ARMS + CONTROL_ARMS
                      for family in FAMILIES}
    observed_pairs = {(row["frame_id"], row["world_family"]) for row in behavior["rows"]}
    behavior_ok = (expected_pairs == observed_pairs and len(behavior["rows"]) == 12
                   and all(len(row["checkpoints"]) == 4 for row in behavior["rows"])
                   and behavior["goal_choices_native"] and not behavior["host_selects_action"]
                   and behavior["all_failures_retained"])
    lexical = lexical_readiness(checkpoint_sha256=None, vectors_available=False)
    risk = _risk_control()
    veto = _host_veto_control()
    distribution = _distribution_control()
    audit_record = _orphan_and_boot_audit()
    runtime = _runtime_attestation()
    adapter = NativeOusiometricInvestigation(PRIMARY_ARMS[0])
    profile = adapter.profile_audit()
    loaded_rules = {rule.get("name") for rule in adapter.s._inner.export_rules()}
    profile_ok = (profile["profile"] == "p28-ousiometric-investigation"
                  and profile["frame_enabled"] == [1.0]
                  and profile["acquisition_enabled"] == [0.0]
                  and profile["common_target_enabled"] == [1.0]
                  and any(str(name).startswith("ouf_project_shared_event_") for name in loaded_rules)
                  and "oua_request_funded_flex_frame_proposal" in loaded_rules
                  and profile["no_host_action"])
    checks = {
        "mathematical_full_rank_equivalence": "PASS" if math_ok else "FAIL",
        "all_behavior_arms_and_worlds_use_same_native_consumer": "PASS" if behavior_ok else "FAIL",
        "lexical_arm": lexical["status"],
        "frequency_and_rare_adverse_controls": distribution["status"],
        "risk_residual_boundary": risk["status"],
        "native_host_veto": veto["status"],
        "profile_dependency_orphan_audit": audit_record["status"],
        "loaded_native_runtime": runtime["status"],
        "investigation_profile_isolation": "PASS" if profile_ok else "FAIL",
    }
    status = "PASS" if all(value in {"PASS", "UNSUPPORTED", "ATTESTED"}
                            for value in checks.values()) else "FAIL"
    return {
        "schema": "p28_ousiometric_self_check_v1", "status": status,
        "checks": checks,
        "lexical_readiness": lexical,
        "behavior_self_check": {
            "rows": len(behavior["rows"]),
            "checkpoint_rows": sum(len(row["checkpoints"]) for row in behavior["rows"]),
            "arms": behavior["primary_arms"] + behavior["control_arms"],
            "families": sorted({row["world_family"] for row in behavior["rows"]}),
            "all_failures_retained": behavior["all_failures_retained"],
            "host_selects_action": behavior["host_selects_action"],
        },
        "geometry_audit": {**audit.__dict__, "max_roundtrip_abs_error":
                            float(np.max(np.abs(roundtrip - samples)))},
        "distribution_self_check": distribution,
        "risk_self_check": risk,
        "host_veto_self_check": veto,
        "orphan_boot_audit": audit_record,
        "runtime_attestation": runtime,
        "profile_audit": profile,
        "source_hashes": _source_hashes(),
        "frame_seed_sha256": sha256_file(FRAME_SEED),
        "acquisition_seed_sha256": sha256_file(ACQUISITION_SEED),
        "lexical_source_hashes": {
            "gpads_v2_payload_sha256": "1825f9f23b796add681bd6dcd9753e8f1bf68cbf158c4af5e710bbc507b47e0a",
            "nrc_vad_v1_payload_sha256": "fd49023f760155c8377424d96ca18d57c6685891d78ba381e47af6f4a1b148a7",
            "checkpoint_sha256": None, "token_bridge_sha256": None,
            "scores_opened": False,
            "split_namespace": "p28-ousiometry-v1",
            "split_digest": "0670f22600947a83d666708fe6a39c1886912ba0c83070f0106c83ca5595d726",
            "split_counts": {"train": 15361, "development": 1348,
                             "anchor": 941, "heldout": 2320},
            "cluster_count": 7723,
            "oversized_cluster_count": 1,
            "oversized_cluster_size": 10726,
        },
        "seed_allocation": {"tool_start": TOOL_SEED_START, "social_start": SOCIAL_SEED_START,
                            "n_per_family": N_REPLICATES,
                            "tool_seed_list_sha256": hashlib.sha256(json.dumps(
                                list(range(TOOL_SEED_START, TOOL_SEED_START + N_REPLICATES)),
                                separators=(",", ":")).encode()).hexdigest(),
                            "social_seed_list_sha256": hashlib.sha256(json.dumps(
                                list(range(SOCIAL_SEED_START, SOCIAL_SEED_START + N_REPLICATES)),
                                separators=(",", ":")).encode()).hexdigest()},
        "representation_profile_sha256": hashlib.sha256(json.dumps({
            "primary_arms": PRIMARY_ARMS, "control_arms": CONTROL_ARMS,
            "frame_seed_sha256": sha256_file(FRAME_SEED),
            "acquisition_seed_sha256": sha256_file(ACQUISITION_SEED),
        }, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
        "paper_transform": PAPER_TRANSFORM,
        "paper_transform_sha256": hashlib.sha256(json.dumps(
            PAPER_TRANSFORM, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
        "external_source_manifest": manifest_dict(),
        "git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO,
                                               text=True).strip(),
    }


def _verify_prereg() -> dict:
    if not PREREG.is_file():
        raise RuntimeError("P28.13 standalone preregistration is missing")
    prereg_text = PREREG.read_text(encoding="utf-8")
    marker = "<!-- P28_PREREG_JSON\n"
    if marker not in prereg_text:
        raise RuntimeError("P28.13 machine-readable freeze block is missing")
    frozen = json.loads(prereg_text.split(marker, 1)[1].split("\n-->", 1)[0])
    if frozen.get("status") != "FROZEN":
        raise RuntimeError("P28.13 preregistration is not frozen")
    actual = _source_hashes()
    if actual != frozen.get("source_hashes"):
        raise RuntimeError("source bundle changed after P28.13 freeze")
    attestation = _runtime_attestation()
    if attestation != frozen.get("runtime_attestation"):
        raise RuntimeError("loaded native runtime differs from P28.13 freeze")
    current = self_check()
    for key in ("seed_allocation", "representation_profile_sha256",
                "paper_transform_sha256", "frame_seed_sha256",
                "acquisition_seed_sha256", "lexical_source_hashes",
                "external_source_manifest"):
        normalized = json.loads(json.dumps(current.get(key), sort_keys=True))
        if frozen.get(key) != normalized:
            raise RuntimeError(f"P28.13 frozen {key} differs from the current protocol")
    expected_protocol = {
        "world_families": list(FAMILIES),
        "arms": list(PRIMARY_ARMS + CONTROL_ARMS),
        "horizons": [0, 1, 2, 4],
        "replicates_per_family": N_REPLICATES,
        "bootstrap_replicates": BOOTSTRAP_REPLICATES,
        "bootstrap_seed": 28_202_614,
        "paired_sign_flip_replicates": 100_000,
        "safety_noninferiority_margin": 0.02,
        "minimum_auc_improvement": 0.10,
        "holm_alpha": 0.01,
    }
    if frozen.get("protocol") != expected_protocol:
        raise RuntimeError("P28.13 analysis/allocation protocol differs from the frozen contract")
    return frozen


def run_frozen(output: str | Path) -> dict:
    frozen = _verify_prereg()
    tool_seeds = tuple(range(TOOL_SEED_START, TOOL_SEED_START + N_REPLICATES))
    social_seeds = tuple(range(SOCIAL_SEED_START, SOCIAL_SEED_START + N_REPLICATES))
    arms = PRIMARY_ARMS + CONTROL_ARMS
    rows = []
    for family, seeds in ((FAMILIES[0], tool_seeds), (FAMILIES[1], social_seeds)):
        panel = development_panel(seeds=seeds, frames=arms, families=(family,))
        rows.extend(panel["rows"])
    payload = {
        "schema": "p28_ousiometric_raw_v1", "status": "COMPLETED",
        "prereg_sha256": sha256_file(PREREG), "frozen_seed_allocation": frozen["seed_allocation"],
        "runtime_attestation": _runtime_attestation(),
        "lexical_status": frozen["lexical_status"],
        "external_scores_opened": False,
        "rows": rows,
    }
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n",
                      encoding="utf-8")
    payload["raw_output_path"] = str(output.resolve())
    payload["raw_output_sha256"] = sha256_file(output)
    return payload


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--self-check", action="store_true")
    modes.add_argument("--run", action="store_true")
    parser.add_argument("--output", default="/tmp/p28_ousiometric_raw_v1.json")
    args = parser.parse_args(argv)
    try:
        result = self_check() if args.self_check else run_frozen(args.output)
        print(json.dumps(result, sort_keys=True))
        return 0 if result.get("status") == "PASS" or result.get("status") == "COMPLETED" else 1
    except Exception as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

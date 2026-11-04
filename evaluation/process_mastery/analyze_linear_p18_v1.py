"""Integrity, native provenance and efficacy analysis for P18."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
import sys
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
PREREG = ROOT / "docs/research/engine_substrate/COGNITION_LINEAR_P18_PREREG.md"
FAMILIES = ("object_mechanism", "temporal_latent")
ARMS = ("learned_model", "held_vocabulary_search", "passive", "fixed_probe")
CONTROL_KINDS = ("ambiguous", "missing", "irregular")
ARTIFACT_KEYS = ("source_bundle_sha256", "runner_sha256", "analyzer_sha256",
    "wrapper_sha256", "loaded_extension_sha256", "build_receipt_sha256",
    "profile_sha256", "world_adapter_sha256", "dependency_closure_sha256",
    "engine_source_sha256")


def _json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=list)


def _digest(value):
    return hashlib.sha256(_json(value).encode()).hexdigest()


def _contract():
    if not PREREG.is_file():
        raise ValueError("P18 standalone preregistration is missing")
    match = re.search(r"```json\s*(\{.*?\})\s*```", PREREG.read_text(), re.S)
    if not match:
        raise ValueError("P18 preregistration lacks its machine-readable contract")
    return json.loads(match.group(1))


def _check_provenance(metadata):
    actual = metadata.get("artifact_provenance", {})
    missing = [key for key in ARTIFACT_KEYS if not actual.get(key)]
    if missing:
        raise ValueError(f"P18 artifact provenance missing {missing}")
    runtime = actual.get("runtime_attestation", {})
    if (runtime.get("status") != "ATTESTED" or runtime.get("native_symbols_bound") is not True
            or runtime.get("build_sources_match") is not True
            or runtime.get("loaded_extension_sha256") != actual["loaded_extension_sha256"]
            or runtime.get("wrapper_sha256") != actual["wrapper_sha256"]
            or runtime.get("build_receipt_sha256") != actual["build_receipt_sha256"]):
        raise ValueError("P18 runtime attestation does not bind the loaded native artifact")
    if metadata.get("split") == "heldout":
        frozen = _contract()
        mismatch = {k: (actual.get(k), frozen.get("artifacts", {}).get(k))
                    for k in ARTIFACT_KEYS if actual.get(k) != frozen.get("artifacts", {}).get(k)}
        runtime_keys = ("wrapper_sha256", "loaded_extension_sha256", "build_receipt_sha256",
                        "build_source_fingerprint")
        runtime_mismatch = {k: (runtime.get(k), frozen.get("runtime", {}).get(k))
                            for k in runtime_keys if runtime.get(k) != frozen.get("runtime", {}).get(k)}
        if mismatch or runtime_mismatch:
            raise ValueError(f"P18 artifact mismatch: source={mismatch}, runtime={runtime_mismatch}")


def _verify_world_receipts(row):
    from evaluation.process_mastery.observed_worlds import ObservedWorld
    world = ObservedWorld.create(row["family"], int(row["seed"]))
    receipts = row.get("world_receipts", [])
    if row["family"] == "object_mechanism":
        for receipt in receipts:
            observation = world.observe(receipt["object_id"])
            replay = world.execute(observation, receipt["action"])
            if replay != receipt or not world.verify_receipt(receipt):
                return False
    else:
        for receipt in receipts:
            observation = world.observe_temporal(int(receipt["sample_id"].split("-")[-1]))
            replay = world.execute_temporal(observation)
            if replay != receipt or not world.verify_temporal_receipt(receipt):
                return False
    return True


def _validate(payload):
    meta = payload.get("metadata", {})
    if meta.get("phase") != "linear-p18-v1" or meta.get("split") not in {"development", "heldout"}:
        raise ValueError("P18 scorecard phase/split mismatch")
    _check_provenance(meta)
    split = meta["split"]
    self_check = bool(meta.get("self_check"))
    expected_n = 2 if self_check else (8 if split == "development" else 200)
    expected_controls = 2 if self_check else (10 if split == "development" else 100)
    offset = 0 if split == "development" else 2_000_000
    if meta.get("n_per_family_per_arm") != expected_n or meta.get("control_n_per_kind") != expected_controls:
        raise ValueError("P18 allocation size mismatch")
    if meta.get("split_offset") != offset:
        raise ValueError("P18 split offset mismatch")
    if meta.get("families") != list(FAMILIES) or meta.get("arms") != list(ARMS):
        raise ValueError("P18 registered families/arms mismatch")

    failures = defaultdict(int)
    summaries = defaultdict(lambda: {"n": 0, "success": 0, "refinements": 0,
        "interactions": 0, "probes": 0, "graph_nodes": 0, "seconds": 0.0})
    paired = defaultdict(dict)
    allocated = defaultdict(int)
    for row in payload.get("records", []):
        family, arm, seed = row.get("family"), row.get("arm"), row.get("seed")
        if family not in FAMILIES or arm not in ARMS:
            failures["invalid_family_arm"] += 1
            continue
        f_ix = FAMILIES.index(family)
        expected_seed = 41_000_000 + offset + f_ix * 10_000 + allocated[(family, arm)]
        allocated[(family, arm)] += 1
        if seed != expected_seed:
            failures["seed_allocation"] += 1
        if arm in paired[(family, seed)]:
            failures["duplicate_arm"] += 1
        paired[(family, seed)][arm] = row
        if row.get("status") != "COMPLETED":
            failures["execution_status"] += 1
        audit = row.get("input_audit", {})
        if (audit.get("answer_fields_absent") is not True or
                audit.get("hidden_solution_absent") is not True or
                audit.get("equations_absent") is not True):
            failures["input_audit"] += 1
        forbidden = {"truth", "hidden_truth", "expected_outcome", "target_feature", "transition_equation"}
        if forbidden.intersection(row):
            failures["target_field_leak"] += 1
        if not _verify_world_receipts(row):
            failures["world_receipt"] += 1
        trace = row.get("decision_trace", {})
        actual = row.get("world_receipts", [])[-1].get(
            "observed_state" if family == "object_mechanism" else "observed_outcome") if row.get("world_receipts") else None
        if family == "object_mechanism":
            predictions = trace.get("predicted_outcomes", [])
            if arm == "learned_model":
                derived = (trace.get("receipt_verified") is True
                    and trace.get("action") == "heat"
                    and trace.get("resolution_statuses", []).count("supports") == 1
                    and trace.get("resolution_statuses", []).count("disconfirms") == 1)
            elif arm == "held_vocabulary_search":
                derived = (trace.get("receipt_verified") is True and trace.get("action") == "heat"
                    and len(set(predictions)) > 1 and actual in predictions)
            else:
                derived = False
        else:
            if arm == "learned_model":
                derived = trace.get("candidate_status") == "validated" and trace.get("receipt_verified") is True
            elif arm == "held_vocabulary_search":
                derived = trace.get("predicted_outcome") == actual and trace.get("receipt_verified") is True
            else:
                derived = False
        if row.get("success") is not derived:
            failures["decision_trace_outcome"] += 1
        resources = row.get("resource_counts", {})
        if resources.get("interactions", 999) > 5 or resources.get("probe_count", 999) > 1:
            failures["resource_limit"] += 1
        elapsed = row.get("task_seconds")
        if not isinstance(elapsed, (int, float)) or not math.isfinite(elapsed) or elapsed < 0:
            failures["invalid_elapsed"] += 1
        summary = summaries[(family, arm)]
        summary["n"] += 1
        summary["success"] += int(row.get("success") is True)
        summary["refinements"] += int(row.get("refinement") is True)
        summary["interactions"] += resources.get("interactions", 0)
        summary["probes"] += resources.get("probe_count", 0)
        summary["graph_nodes"] += resources.get("graph_nodes", 0)
        summary["seconds"] += elapsed if isinstance(elapsed, (int, float)) and math.isfinite(elapsed) else 0
    if len(payload.get("records", [])) != len(FAMILIES) * expected_n * len(ARMS):
        failures["row_count"] += 1
    for key, arms in paired.items():
        if len(key) != 2 or set(arms) != set(ARMS):
            failures["unpaired_world"] += 1

    controls = meta.get("controls", [])
    if len(controls) != len(CONTROL_KINDS) * expected_controls:
        failures["control_count"] += 1
    control_summary = {}
    for kind_index, kind in enumerate(CONTROL_KINDS):
        rows = [row for row in controls if row.get("kind") == kind]
        passed = sum(row.get("passed") is True for row in rows)
        for draw, row in enumerate(rows):
            if row.get("seed") != 41_020_000 + offset + kind_index * 1_000 + draw:
                failures["control_seed_allocation"] += 1
        control_summary[kind] = {"n": len(rows), "passed": passed, "failed": len(rows) - passed}
        if len(rows) != expected_controls or passed != expected_controls:
            failures[f"control:{kind}"] += abs(expected_controls - passed)

    efficacy = {}
    for family in FAMILIES:
        rates = {arm: summaries[(family, arm)]["success"] / max(1, summaries[(family, arm)]["n"])
                 for arm in ARMS}
        efficacy[family] = {"success_rate": rates,
            "gain_vs": {arm: rates["learned_model"] - rates[arm]
                        for arm in ARMS if arm != "learned_model"}}
    learned_refinements = sum(summaries[(family, "learned_model")]["refinements"] for family in FAMILIES)
    efficacy_pass = all(min(value["gain_vs"].values()) >= 0.20 for value in efficacy.values())
    integrity = not failures
    minimum_refinements = 100 if split == "heldout" else min(8, len(FAMILIES) * expected_n)
    conformance = integrity and all(x["failed"] == 0 for x in control_summary.values()) and learned_refinements >= minimum_refinements
    return {"phase": "linear-p18-v1", "split": split,
        "rows": len(payload.get("records", [])), "paired_worlds": len(paired),
        "integrity_status": "PASS" if integrity else "FAIL",
        "registered_conformance_status": "PASS" if conformance else "FAIL",
        "registered_efficacy_status": "PASS" if efficacy_pass else "NOT_ESTABLISHED",
        "efficacy": efficacy, "families": {f: {a: summaries[(f, a)] for a in ARMS} for f in FAMILIES},
        "controls": control_summary, "actual_result_linked_refinements": learned_refinements,
        "failures": dict(failures),
        "claim_boundary": "finite categorical object mechanism and partial temporal continuation worlds only"}


def analyze(payload):
    report = _validate(payload)
    cases = []
    mutations = (
        ("world_receipts", lambda p: p["records"][0]["world_receipts"][0].__setitem__("receipt_sha256", "tampered")),
        ("input_audit", lambda p: p["records"][0]["input_audit"].__setitem__("hidden_solution_absent", False)),
        ("arm", lambda p: p["records"][0].__setitem__("arm", "forged")),
        ("seed", lambda p: p["records"][0].__setitem__("seed", -1)),
        ("success", lambda p: p["records"][0].__setitem__("success", not p["records"][0]["success"])),
    )
    for field, mutate in mutations:
        altered = json.loads(json.dumps(payload))
        mutate(altered)
        try:
            detected = _validate(altered)["integrity_status"] != "PASS"
        except (ValueError, KeyError, TypeError):
            detected = True
        cases.append({"field": field, "tampering_detected": detected})
    report["analyzer_tampering_controls"] = {"n": len(cases),
        "passed": sum(c["tampering_detected"] for c in cases),
        "failed": sum(not c["tampering_detected"] for c in cases), "cases": cases}
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("scorecard", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = analyze(json.loads(args.scorecard.read_text()))
    output = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(output)
    else:
        print(output)


if __name__ == "__main__":
    main()

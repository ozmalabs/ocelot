#!/usr/bin/env python3
"""P5 paired held-out protocol runner; missing adapters stay explicitly null."""
from __future__ import annotations

import hashlib
import json
import os
import random
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROTOCOL = "cognition_p5_heldout_v1"
REGISTERED_END = 200
REGISTERED_CONTROLS = 100
MAX_EPOCHS = 64
MAX_PLANNER_DEPTH = 8
MAX_EXPANSIONS = 256
ITEMS = {
    "F1": {"arms": ["shared_view_on", "shared_view_off"], "family": "representations_contradictions_owner_permutations"},
    "F2": {"arms": ["recursive_rules_on", "recursive_rules_off"], "family": "second_order_belief_minimal_pairs"},
    "G2": {"arms": ["reappraisal_on", "reappraisal_off"], "family": "supported_alternative_vs_adverse_evidence"},
    "G3": {"arms": ["inhibition_on", "inhibition_off"], "family": "native_sink_stop_go_late_stop"},
    "E3": {"arms": ["scm_do_query", "conditioning_only"], "family": "confounder_collider_chain_nonidentified"},
    "E4": {"arms": ["planner", "one_step"], "family": "delayed_reward_traps_missing_transitions"},
    "A2": {"arms": ["completion_on", "completion_off"], "family": "mixed_key_coverage_model_epoch_changes"},
    "D6": {"arms": ["buffered_incremental", "direct_exact"], "family": "lattice_shapes_angles_0_90_180_270"},
}
FROZEN_ARTIFACTS = (
    "docs/research/engine_substrate/COGNITION_BUILD_P5_PREREG.md",
    "docs/research/engine_substrate/COGNITION_BUILD_P5_FACULTY_DEPTH_PLAN.md",
    "evaluation/substrate_capability/cognition_p5_heldout_v1.py",
    "evaluation/substrate_capability/cognition_p5_analysis_v1.py",
    "scripts/gen_decomposition_completion_seed.py", "seeds/decomposition_completion.json",
    "scripts/gen_analog_imagery_seed.py", "seeds/analog_imagery.json",
    "scripts/gen_cognition_planner_seed.py", "seeds/cognition_planner.json",
    "scripts/gen_imagined_candidate_arbitration_seed.py", "seeds/imagined_candidate_arbitration.json",
    "scripts/gen_response_inhibition_seed.py", "seeds/response_inhibition.json",
    "substrate/boot_profiles.py", "seeds/cognition_on_params.json",
    "tests/test_cognition_profile_integration.py",
    "runners/dsl/python/substrate_rs/_native.abi3.so",
    "runners/dsl/python/substrate_rs/_native.build.json",
)


def _git(*args):
    result = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True)
    if result.returncode:
        raise ValueError(result.stderr.strip() or "git verification failed")
    return result.stdout.strip()


def artifact_hashes():
    return {path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
            for path in FROZEN_ARTIFACTS if (ROOT / path).is_file()}


def verify_hash_manifest(manifest, expected_paths=FROZEN_ARTIFACTS):
    if not isinstance(manifest, dict) or set(manifest) != set(expected_paths):
        raise ValueError("artifact hash manifest is absent or incomplete")
    actual = artifact_hashes()
    for path in expected_paths:
        if path not in actual or manifest[path] != actual[path]:
            raise ValueError(f"artifact hash mismatch: {path}")


def verify_registered_freeze(prereg_hash):
    head = _git("rev-parse", "HEAD")
    if prereg_hash.lower() != head.lower():
        raise ValueError("registered run requires the preregistration-only freeze commit at HEAD")
    if os.environ.get("COGNITION_PREREG_HASH", "").lower() != prereg_hash.lower():
        raise ValueError("COGNITION_PREREG_HASH must equal the frozen preregistration commit")
    for path in FROZEN_ARTIFACTS:
        _git("cat-file", "-e", f"{head}:{path}")
        if _git("status", "--porcelain", "--", path):
            raise ValueError(f"frozen artifact has local changes: {path}")


def _case(seed, item, index, control=False):
    rng = random.Random(seed ^ (index * 7919) ^ sum(map(ord, item)))
    kind = "adverse_control" if control else "primary"
    if item == "F1":
        agent_input = {"representation_count": 4, "owner_permutation": rng.sample(range(4), 4), "contradiction_control": control}
        oracle = {"scoring_only": True, "preserve_source_assertions": True}
    elif item == "F2":
        belief = bool(index % 2)
        agent_input = {"holder": f"unseen-holder-{index}", "report": f"door_open={belief}", "query": "holder_belief:door_open"}
        oracle = {"scoring_only": True, "holder_belief": belief, "actual_world": not belief if control else belief}
    elif item == "G2":
        supported = bool(index % 2) and not control
        agent_input = {"event": "message_not_received", "arousal": 0.7, "alternative": "recipient_offline", "evidence": "delivery_outage" if supported else "none"}
        oracle = {"scoring_only": True, "alternative_supported": supported}
    elif item == "G3":
        events = ["stop", "go", "dispatch"] if index % 2 else ["go", "stop", "dispatch"]
        if control:
            events = ["go", "dispatch", "late_stop"]
        agent_input = {"events": events, "requested_action": "move"}
        oracle = {"scoring_only": True, "timely_stop": "stop" in events and events.index("stop") < events.index("dispatch")}
    elif item == "E3":
        graph = ("confounder", "collider", "chain", "nonidentified")[index % 4]
        agent_input = {"graph_kind": graph, "query": {"do": "x=1", "outcome": "y"}}
        oracle = {"scoring_only": True, "identified": graph != "nonidentified"}
    elif item == "E4":
        depth = 2 + index % 7
        agent_input = {"depth": depth, "trap": f"trap-{index}", "missing_transition": control, "depth_limit": 8, "expansion_limit": 256}
        oracle = {"scoring_only": True, "reachable": not control, "shortest_depth": depth if not control else None}
    elif item == "A2":
        required = ["alpha", "beta", "gamma"]
        covered = len(required) if index % 4 == 0 and not control else index % len(required)
        agent_input = {"required_keys": required, "covered_key_count": covered, "model_epoch_change": control}
        oracle = {"scoring_only": True, "complete": covered == len(required) and not control}
    else:
        angle = (0, 90, 180, 270)[index % 4]
        agent_input = {"lattice_angle": angle, "shape_index": index}
        oracle = {"scoring_only": True, "shortest_work": angle // 90, "detached_grounding": False}
    return {"case_id": f"{item}-{kind}-{index:04d}", "kind": kind,
            "source_identity": hashlib.sha256(f"{seed}:{item}:{index}".encode()).hexdigest()[:16],
            "event_order": [rng.randrange(0, 8) for _ in range(4)],
            "model_parameter": rng.randrange(1, 100000),
            "agent_input": agent_input, "external_oracle": oracle}


def run(prereg_hash, first, end, *, development=False):
    if not development:
        verify_registered_freeze(prereg_hash)
    if first < 0 or end < first or (not development and end > REGISTERED_END):
        raise ValueError("draw range must be within registered indices 0..200")
    seed = int(hashlib.sha256(prereg_hash.encode()).hexdigest()[:16], 16)
    items = {}
    for item, spec in ITEMS.items():
        rows = []
        for index in range(first, end):
            inputs = _case(seed, item, index)
            # An adapter may read inputs only. Oracle values live in this
            # scoring row and are never copied into an agent's graph.
            rows.append({"inputs": {k: v for k, v in inputs.items() if k != "external_oracle"},
                         "scoring_oracle": inputs["external_oracle"],
                         "arms": {arm: None for arm in spec["arms"]},
                         "null_reason": "mechanism_adapter_not_integrated"})
        controls = [_case(seed, item, i, True) for i in range(REGISTERED_CONTROLS)]
        items[item] = {"family": spec["family"], "arms": spec["arms"],
                       "primary": rows, "controls": controls,
                       "adapter_status": "not_integrated"}
    return {"protocol": PROTOCOL, "prereg_hash": prereg_hash.lower(),
            "first": first, "end": end, "development_only": development,
            "limits": {"max_epochs": MAX_EPOCHS, "planner_depth": MAX_PLANNER_DEPTH,
                       "planner_expansions": MAX_EXPANSIONS},
            "artifact_sha256": artifact_hashes(), "items": items}


def _self_check():
    report = run("development", 1000, 1003, development=True)
    assert report["development_only"] and set(report["items"]) == set(ITEMS)
    assert all(len(item["primary"]) == 3 and len(item["controls"]) == 100
               for item in report["items"].values())
    assert all("external_oracle" not in row["inputs"] and "scoring_oracle" in row
               for item in report["items"].values() for row in item["primary"])
    assert all(all(value is None for row in item["primary"] for value in row["arms"].values())
               for item in report["items"].values())
    manifest = artifact_hashes()
    verify_hash_manifest(manifest)
    for bad in ({}, {**manifest, next(iter(manifest)): "0" * 64}):
        try:
            verify_hash_manifest(bad)
        except ValueError:
            pass
        else:
            raise AssertionError("hash verification accepted absent/altered manifest")
    try:
        verify_registered_freeze("0" * 40)
    except ValueError:
        pass
    else:
        raise AssertionError("registered freeze guard accepted an unfrozen commit")


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv == ["--self-check"]:
        _self_check()
        print("cognition_p5_heldout_v1 self-check passed (development-only)")
        return
    if len(argv) != 3:
        raise SystemExit("usage: cognition_p5_heldout_v1.py <prereg_hash> <first> <end> | --self-check")
    report = run(argv[0], int(argv[1]), int(argv[2]))
    out_dir = ROOT / "evaluation" / "reports"
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"cognition_p5_heldout_v1_{argv[0][:8]}_d{argv[1]}-{argv[2]}.json"
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(out)


if __name__ == "__main__":
    main()

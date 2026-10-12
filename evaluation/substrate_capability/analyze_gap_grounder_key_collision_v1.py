#!/usr/bin/env python3
"""Validate and cross-tab shared-gap grounding outcomes against isolated controls."""
from __future__ import annotations

import collections
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CAPTURE = ROOT / "evaluation/reports/gap_grounder_key_collision_v1/capture.json"
LOCK = ROOT / "evaluation/substrate_capability/gap_grounder_key_collision_v1_lock_20260929.json"
OUT = ROOT / "evaluation/reports/gap_grounder_key_collision_v1/analysis.json"
EXPECTED = {
    "isolated_A": ["A"], "isolated_B": ["B"],
    "repeat_A": ["A", "A"], "repeat_B": ["B", "B"],
    "A_then_B": ["A", "B"], "B_then_A": ["B", "A"],
}


def event_summary(event: dict) -> dict:
    observation = event["new_observations"][-1]["attrs"] if event["new_observations"] else {}
    result = event["result"]
    verified = result.get("verified") or {}
    return {
        "case": event["case"],
        "name_hint": event["derived_name_hint"],
        "observation_status": observation.get("status"),
        "observation_key": observation.get("key"),
        "concern_key": result.get("concern_key"),
        "outcome": result.get("outcome"),
        "path": result.get("path"),
        "composition": result.get("composition"),
        "n_rules": result.get("n_rules"),
        "accepted": result.get("accepted"),
        "verification_accepted": verified.get("accepted"),
        "primitive_request": result.get("primitive_request"),
        "built_primitive": result.get("name") if result.get("outcome") == "built_primitive" else None,
        "axis_delta": event["axis_delta"],
        "primitive_request_delta": event["primitive_request_delta"],
        "held_primitive_delta": event["held_primitive_delta"],
        "codebook_epoch": event["after"]["codebook_epoch"],
        "native_steps": event["after"]["latest_native_steps"],
        "wall_seconds": event["wall_seconds"],
        "cpu_seconds": event["cpu_seconds"],
        "new_axis_attrs": [row["attrs"] for row in event["after"]["nodes"]["CapabilityAxis"]
                            if row["id"] not in {old["id"] for old in event["before"]["nodes"]["CapabilityAxis"]}],
    }


def main() -> None:
    capture = json.loads(CAPTURE.read_text())
    lock = json.loads(LOCK.read_text())
    assert capture["input_lock"] == lock == capture["post_run_input_lock"]
    runs = {run["id"]: run for run in capture["sequences"]}
    assert set(runs) == set(EXPECTED)
    assert sum(len(run["events"]) for run in runs.values()) == 10
    for sequence_id, labels in EXPECTED.items():
        run = runs[sequence_id]
        assert [e["case"] for e in run["events"]] == labels
        assert all(e["derived_name_hint"] == "gap_shared_family" for e in run["events"])

    def obs_sig(event: dict) -> str:
        observations = event["new_observations"]
        assert len(observations) == 1
        return json.dumps(observations[0]["attrs"].get("signature"),
                          sort_keys=True, separators=(",", ":"))

    A, B = runs["isolated_A"]["events"][0], runs["isolated_B"]["events"][0]
    assert obs_sig(A) != obs_sig(B)
    assert A["gap_attrs"]["observation"] != B["gap_attrs"]["observation"]

    event_rows = []
    result_patterns = collections.Counter()
    for sequence_id in sorted(runs):
        for event in runs[sequence_id]["events"]:
            summary = event_summary(event)
            summary["sequence_id"] = sequence_id
            event_rows.append(summary)
            result_patterns[(sequence_id, summary["case"], summary["observation_status"],
                             summary["outcome"], summary["axis_delta"])] += 1

    compare = {}
    for sequence_id, index, label in (("isolated_A", 0, "A"), ("isolated_B", 0, "B"),
                                       ("A_then_B", 1, "B"), ("B_then_A", 1, "A"),
                                       ("repeat_A", 1, "A"), ("repeat_B", 1, "B")):
        run = runs[sequence_id]
        e = run["events"][index]
        compare[f"{sequence_id}:{label}"] = event_summary(e)

    analysis = {
        "schema_version": 1,
        "capture_sha256": hashlib.sha256(CAPTURE.read_bytes()).hexdigest(),
        "source_lock_matches_pre_and_post_run": True,
        "sequence_count": len(runs), "extend_for_gap_calls": len(event_rows),
        "A_B_same_hint": True,
        "A_B_distinct_observation_signatures": True,
        "outcome_patterns": {
            " | ".join(map(str, key)): value
            for key, value in sorted(result_patterns.items())
        },
        "isolated_and_shared_second_call_comparison": compare,
        "event_rows": event_rows,
        "claim_boundary": (
            "This describes the fixed A/B gap fixtures under the current caller and key policy. "
            "Different outcomes demonstrate fixture-specific interference; matching outcomes "
            "do not prove key collisions are harmless on other gap families."),
    }
    OUT.write_text(json.dumps(analysis, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"analysis": str(OUT.relative_to(ROOT)),
                      "sequences": len(runs), "calls": len(event_rows),
                      "patterns": analysis["outcome_patterns"]}, indent=2))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Validate and summarize the locked predicate-key recurrence replay."""
from __future__ import annotations

import collections
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CAPTURE = ROOT / "evaluation/reports/polyomino_concern_key_recurrence_v1/capture.json"
LOCK = ROOT / "evaluation/substrate_capability/polyomino_concern_key_recurrence_v1_lock_20260929.json"
OUT = ROOT / "evaluation/reports/polyomino_concern_key_recurrence_v1/analysis.json"


def signature(event: dict) -> str:
    return json.dumps(event["signature"], sort_keys=True, separators=(",", ":"))


def norm(coords: set[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    min_r = min(r for r, _ in coords)
    min_c = min(c for _, c in coords)
    return tuple(sorted((r - min_r, c - min_c) for r, c in coords))


def d4_orbit_key(event: dict) -> tuple[tuple[int, int], ...]:
    coords = {(int(rel[1]), int(rel[2])) for rel in event["signature"]}
    forms = (
        {(r, c) for r, c in coords}, {(r, -c) for r, c in coords},
        {(-r, c) for r, c in coords}, {(-r, -c) for r, c in coords},
        {(c, r) for r, c in coords}, {(c, -r) for r, c in coords},
        {(-c, r) for r, c in coords}, {(-c, -r) for r, c in coords},
    )
    return min(norm(form) for form in forms)


def main() -> None:
    capture = json.loads(CAPTURE.read_text())
    lock = json.loads(LOCK.read_text())
    assert capture["input_lock"] == lock == capture["post_run_input_lock"]
    sequences = capture["sequences"]
    assert len(sequences) == 15
    assert sum(len(s["events"]) for s in sequences) == 30

    all_keys = set()
    target_orbits: dict[str, tuple[tuple[int, int], ...]] = {}
    pattern = collections.Counter()
    order_outcomes = {}
    for seq in sequences:
        first, second = seq["events"]
        assert [first["ordinal"], second["ordinal"]] == [1, 2]
        assert first["capability_key"] == second["capability_key"]
        all_keys.add(first["capability_key"])
        assert len(first["signature"]) == len(second["signature"]) == 7
        assert all(relation[0] == "cell" for e in (first, second)
                   for relation in e["signature"])
        assert first["signature_sha256"] == hashlib.sha256(
            signature(first).encode()).hexdigest()
        assert second["signature_sha256"] == hashlib.sha256(
            signature(second).encode()).hexdigest()
        if seq["condition"] == "exact_repeat":
            assert signature(first) == signature(second)
        else:
            assert signature(first) != signature(second)
        for event in (first, second):
            prior = target_orbits.setdefault(event["shape_id"], d4_orbit_key(event))
            assert prior == d4_orbit_key(event)
        pattern[(seq["condition"], first["status"], second["status"],
                 first["axis_delta"], second["axis_delta"])] += 1
        order_outcomes[seq["id"]] = {
            "condition": seq["condition"],
            "shapes": [first["shape_id"], second["shape_id"]],
            "statuses": [first["status"], second["status"]],
            "axis_deltas": [first["axis_delta"], second["axis_delta"]],
            "keys": [first["capability_key"], second["capability_key"]],
        }
    assert len(all_keys) == 1
    key = next(iter(all_keys))
    expected_key = "induced_" + "_".join(["cell"] * 7)
    assert key == expected_key
    assert len(target_orbits) == 5
    assert len(set(target_orbits.values())) == 5

    summary = {
        "schema_version": 1,
        "capture_sha256": hashlib.sha256(CAPTURE.read_bytes()).hexdigest(),
        "source_lock_matches_pre_and_post_run": True,
        "sequence_count": len(sequences), "observation_count": 30,
        "exact_repeat_sequences": sum(s["condition"] == "exact_repeat" for s in sequences),
        "distinct_same_key_sequences": sum(s["condition"] == "distinct_same_key" for s in sequences),
        "distinct_capability_keys": len(all_keys), "shared_key": key,
        "distinct_target_d4_orbits": len(set(target_orbits.values())),
        "outcome_pattern_counts": {
            " | ".join(map(str, key_tuple)): count
            for key_tuple, count in sorted(pattern.items())
        },
        "sequence_outcomes": order_outcomes,
        "claim_boundary": (
            "This measures the current predicate-derived identity on the frozen "
            "polyomino sequences. It does not decide whether this identity is "
            "appropriate for every caller or measure downstream task impact."),
    }
    OUT.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Validate pairing and summarize the locked identity-key comparison."""
from __future__ import annotations

import collections
import hashlib
import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CAPTURE = ROOT / "evaluation/reports/polyomino_concern_key_identity_comparison_v1/capture.json"
LOCK = ROOT / "evaluation/substrate_capability/polyomino_concern_key_identity_comparison_v1_lock_20260929.json"
OUT = ROOT / "evaluation/reports/polyomino_concern_key_identity_comparison_v1/analysis.json"


def canon(signature: list) -> tuple[tuple[int, int], ...]:
    points = {(int(row[1]), int(row[2])) for row in signature}
    forms = (
        points, {(r, -c) for r, c in points}, {(-r, c) for r, c in points},
        {(-r, -c) for r, c in points}, {(c, r) for r, c in points},
        {(c, -r) for r, c in points}, {(-c, r) for r, c in points},
        {(-c, -r) for r, c in points},
    )
    normalized = []
    for form in forms:
        mr, mc = min(r for r, _ in form), min(c for _, c in form)
        normalized.append(tuple(sorted((r - mr, c - mc) for r, c in form)))
    return min(normalized)


def digest_json(value) -> str:
    return hashlib.sha256(json.dumps(value, separators=(",", ":")).encode()).hexdigest()


def main() -> None:
    capture = json.loads(CAPTURE.read_text())
    lock = json.loads(LOCK.read_text())
    assert capture["input_lock"] == lock == capture["post_run_input_lock"]
    arms = capture["arms"]
    assert len(arms) == 30 and sum(len(arm["events"]) for arm in arms) == 60
    paired = collections.defaultdict(dict)
    for arm in arms:
        assert arm["variant"] in {"predicate", "shape_d4"}
        paired[arm["id"]][arm["variant"]] = arm

    status_counts = collections.Counter()
    axis_counts = collections.Counter()
    predicate_keys = set()
    d4_keys_by_shape = collections.defaultdict(set)
    key_times = collections.defaultdict(list)
    call_times = collections.defaultdict(list)
    outcome_rows = {}
    for seq_id, variants in paired.items():
        assert set(variants) == {"predicate", "shape_d4"}
        pred = variants["predicate"]["events"]
        shape = variants["shape_d4"]["events"]
        assert len(pred) == len(shape) == 2
        for i in range(2):
            p, s = pred[i], shape[i]
            assert p["shape_id"] == s["shape_id"]
            assert p["signature_sha256"] == s["signature_sha256"]
            assert p["signature"] == s["signature"]
            expected_canon = canon(s["signature"])
            assert tuple(map(tuple, s["d4_canonical"])) == expected_canon
            expected_shape_key = "shape_d4_" + digest_json(expected_canon)
            assert s["effective_key"] == [expected_shape_key]
            assert p["effective_key"] == ["induced_" + "_".join(["cell"] * 7)]
            predicate_keys.add(p["effective_key"][0])
            d4_keys_by_shape[p["shape_id"]].add(s["effective_key"][0])
            for variant, event in (("predicate", p), ("shape_d4", s)):
                key = (variant, variants[variant]["condition"], i + 1, event["status"])
                status_counts[key] += 1
                axis_counts[(variant, variants[variant]["condition"], i + 1,
                             event["axis_delta"])] += 1
                key_times[variant].append(event["key_compute_seconds"])
                call_times[variant].append(event["wall_seconds"])
        if variants["predicate"]["condition"] == "exact_repeat":
            assert pred[0]["signature"] == pred[1]["signature"]
            assert shape[0]["effective_key"] == shape[1]["effective_key"]
        else:
            assert pred[0]["signature"] != pred[1]["signature"]
            assert shape[0]["effective_key"] != shape[1]["effective_key"]
        outcome_rows[seq_id] = {
            "condition": variants["predicate"]["condition"],
            "shapes": [pred[0]["shape_id"], pred[1]["shape_id"]],
            "predicate_statuses": [e["status"] for e in pred],
            "predicate_axis_deltas": [e["axis_delta"] for e in pred],
            "structure_statuses": [e["status"] for e in shape],
            "structure_axis_deltas": [e["axis_delta"] for e in shape],
            "keys": {"predicate": [e["effective_key"][0] for e in pred],
                     "shape_d4": [e["effective_key"][0] for e in shape]},
        }
    assert len(paired) == 15
    assert len(predicate_keys) == 1
    assert len(d4_keys_by_shape) == 5
    assert all(len(keys) == 1 for keys in d4_keys_by_shape.values())
    assert len({next(iter(keys)) for keys in d4_keys_by_shape.values()}) == 5

    summarize_counter = lambda counter: {
        " | ".join(map(str, key)): value for key, value in sorted(counter.items())
    }
    summary = {
        "schema_version": 1,
        "capture_sha256": hashlib.sha256(CAPTURE.read_bytes()).hexdigest(),
        "locked_inputs_match_pre_and_post_run": True,
        "paired_sequences": len(paired), "variants": 2,
        "observation_count": 60,
        "predicate_key_cardinality": len(predicate_keys),
        "structure_key_cardinality": len({next(iter(k)) for k in d4_keys_by_shape.values()}),
        "status_counts_by_variant_condition_ordinal": summarize_counter(status_counts),
        "axis_delta_counts_by_variant_condition_ordinal": summarize_counter(axis_counts),
        "key_computation_seconds_median": {
            variant: statistics.median(vals) for variant, vals in key_times.items()
        },
        "key_computation_seconds_max": {
            variant: max(vals) for variant, vals in key_times.items()
        },
        "induce_concern_wall_seconds_median": {
            variant: statistics.median(vals) for variant, vals in call_times.items()
        },
        "sequence_outcomes": outcome_rows,
        "claim_boundary": (
            "The structure-key arm supplies an explicit D4 canonical name_hint. "
            "It tests key identity effects on this frozen panel; it is not an "
            "engine-native canonicalizer or evidence about other callers."),
    }
    OUT.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

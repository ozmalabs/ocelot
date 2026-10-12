#!/usr/bin/env python3
"""Cross-tabulate the sealed v1 graph replay against its source capture."""
from __future__ import annotations

import collections
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "evaluation/reports/heldout_polyomino_transform_transfer_v1/capture.json"
REPLAY = ROOT / "evaluation/reports/heldout_polyomino_transform_transfer_v1_graph_replay/graph_replay.json"
LOCK = ROOT / "evaluation/substrate_capability/heldout_polyomino_transform_transfer_v1_graph_replay_lock_20260929.json"
OUT = ROOT / "evaluation/reports/heldout_polyomino_transform_transfer_v1_graph_replay_analysis.json"


def main() -> None:
    raw = json.loads(RAW.read_text())
    replay = json.loads(REPLAY.read_text())
    lock = json.loads(LOCK.read_text())
    assert replay["input_lock"] == lock == replay["post_run_input_lock"]
    assert replay["raw_capture_sha256"] == lock["raw_capture"]["sha256"]

    expected = {}
    for group in raw["groups"]:
        specs = [("clean", None, None, group["clean"])]
        for sigma, rows in group["noisy"].items():
            specs.extend(("noisy", int(sigma), rep, row)
                         for rep, row in enumerate(rows, 1))
        for arm, sigma, rep, row in specs:
            ident = (group["group_id"], arm, sigma, rep)
            seen = json.dumps(row["seen_signatures"], sort_keys=True,
                              separators=(",", ":"))
            expected[ident] = (group["case_type"], row["recognized_key"],
                               hashlib.sha256(seen.encode()).hexdigest())

    rows = replay["rows"]
    assert len(rows) == replay["observation_count"] == 756
    assert len(expected) == len(rows)
    actual = {}
    for row in rows:
        ident = (row["group_id"], row["arm"], row["sigma"], row["replicate"])
        assert ident not in actual
        actual[ident] = row
    assert set(actual) == set(expected)
    for ident, (case_type, adapter_key, sig_hash) in expected.items():
        row = actual[ident]
        assert row["case_type"] == case_type
        assert row["adapter_key"] == adapter_key
        assert row["signature_pair_sha256"] == sig_hash

    def cross(rows):
        out = collections.Counter()
        for row in rows:
            out[(row["case_type"], row["graph"]["status"],
                 "key_returned" if row["adapter_key"] is not None else "no_key",
                 tuple(sorted(t.get("generator", "<none>")
                              for t in row["graph"]["has_transform"])))] += 1
        return {" | ".join((case, status, adapter, ",".join(gens))): count
                for (case, status, adapter, gens), count in sorted(out.items())}

    arms = {}
    for arm in ("clean", "noisy_8", "noisy_12"):
        selected = [r for r in rows if r["arm"] == ("clean" if arm == "clean" else "noisy")
                    and (arm == "clean" or r["sigma"] == int(arm.split("_")[1]))]
        arms[arm] = cross(selected)
    adapter_misses = [r for r in rows if r["adapter_key"] is None]
    summary = {
        "schema_version": 1,
        "raw_capture_sha256": lock["raw_capture"]["sha256"],
        "graph_replay_sha256": hashlib.sha256(REPLAY.read_bytes()).hexdigest(),
        "lock_matches_pre_and_post_run": True,
        "observation_count": len(rows),
        "unique_signature_pairs": replay["unique_signature_pairs"],
        "graph_status_by_case_and_adapter_key": cross(rows),
        "graph_status_by_arm_case_adapter_and_generator": arms,
        "adapter_miss_count": len(adapter_misses),
        "adapter_miss_statuses": dict(collections.Counter(
            r["graph"]["status"] for r in adapter_misses)),
        "adapter_miss_selected_generators": dict(collections.Counter(
            ",".join(sorted(t.get("generator", "<none>")
                             for t in r["graph"]["has_transform"])) or "<none>"
            for r in adapter_misses)),
        "negative_control_graph_statuses": dict(collections.Counter(
            r["graph"]["status"] for r in rows if r["case_type"] == "negative")),
        "negative_control_adapter_key_returns": sum(
            r["adapter_key"] is not None for r in rows if r["case_type"] == "negative"),
        "claim_boundary": (
            "Descriptive exact-signature replay. Graph status is not by itself a semantic "
            "correctness judgment; selected-generator equivalence outside the independently "
            "audited H06_C alias is not established."),
    }
    OUT.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

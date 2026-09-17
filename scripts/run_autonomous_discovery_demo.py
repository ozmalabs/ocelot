#!/usr/bin/env python3
"""Execute the fixed preregistered graph-native autonomous-discovery demo.

The runner accepts only the preregistered fixture and output root. It has no
trajectory, policy, target-axis, semantic-routing, or answerer option: it
submits raw graph facts, invokes native fixpoints, and writes observed facts.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT, ROOT / "runners" / "dsl" / "python"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from domains.autonomous_discovery import (  # noqa: E402
    boot_native, graph_snapshot, load_fixture, rule_inventory, settle_native,
    submit_held_out_operation, submit_preregistered_case,
)
from substrate.boot_core import load_seeds_into  # noqa: E402


def _write(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, default=str) + "\n")


def _actual(substrate, episode, held_out) -> dict:
    candidates = list(substrate.neighbours(episode, "has_predicate_recurrence_candidate"))
    return {
        "evidence": len(list(substrate.neighbours(episode, "has_residual_segment_evidence"))),
        "candidates": len(candidates),
        "persistence": sorted(substrate.node(candidate)["attrs"].get("persistence") for candidate in candidates),
        "offers": len(list(substrate.neighbours(episode, "has_mint_offer"))),
        "new_axes": len(list(substrate.neighbours(episode, "minted_axis"))),
        "held_out_licensed": bool(substrate.node(held_out)["attrs"].get("admissible")),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    fixture = load_fixture(args.fixture)
    failures = []
    for case_name, case in fixture["cases"].items():
        output = args.output / case_name
        output.mkdir(parents=True, exist_ok=True)
        substrate, agent = boot_native()
        state = submit_preregistered_case(substrate, agent, case_name=case_name, fixture=fixture)
        _write(output / "seed_manifest.json", {
            "seed": "autonomous_discovery", "version": "1.0.0",
            "depends_on": ["minting_recurrence_ledger", "minting_recurrence_semantic_demo"],
        })
        _write(output / "initial_graph.json", graph_snapshot(substrate))
        settle_native(substrate)
        _write(output / "settled_graph.json", graph_snapshot(substrate))
        held_out = submit_held_out_operation(substrate, agent, state)
        settle_native(substrate)
        _write(output / "rerun_graph.json", graph_snapshot(substrate))
        inventory = rule_inventory(substrate)
        _write(output / "adapter_audit.json", state["audit"])
        _write(output / "rule_inventory.json", inventory)
        episode = substrate.nodes("DiscoveryEpisode")[0]
        actual = _actual(substrate, episode, held_out)
        expected = case["expected"]
        passed = all(actual[key] == expected.get(key, [] if key == "persistence" else actual[key]) for key in actual)
        if case_name == "precovered_no_new_axis":
            offers = list(substrate.neighbours(episode, "has_mint_offer"))
            actual["offer_status"] = substrate.node(offers[0])["attrs"].get("offer_status") if offers else None
            passed = passed and actual["offer_status"] in {"recognized", "recognized_transformed"}
        if case_name == "idempotence_and_seed_reload":
            before = graph_snapshot(substrate)
            settle_native(substrate)
            load_seeds_into(substrate, agent, ["autonomous_discovery"])
            settle_native(substrate)
            actual["idempotent"] = graph_snapshot(substrate) == before
            passed = passed and actual["idempotent"] is expected["idempotent"]
        report = {"case": case_name, "expected": expected, "actual": actual, "passed": passed}
        _write(output / "assertions.json", report)
        if not passed:
            failures.append(case_name)
    if failures:
        raise SystemExit(f"preregistered assertions failed: {', '.join(failures)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

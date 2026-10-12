#!/usr/bin/env python3
"""Source-locked test of predecessor interface retention for discourse carry.

Run --lock once, then run without arguments to write the deterministic capture.
This is a small rule-level capability experiment, not a natural-task or
production-scope evaluation. It compares a retained predecessor interface to
controls that break one required relation or the interface itself.
"""
from __future__ import annotations

import hashlib
import json
import os
import platform
import statistics
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "runners" / "dsl" / "python")]
LOCK = ROOT / "evaluation/substrate_capability/thoughtexperiment_predecessor_interface_v1_lock_20261003.json"
OUT = ROOT / "evaluation/reports/thoughtexperiment_predecessor_interface_v1_20261003.json"
SOURCE_PATHS = (
    "evaluation/substrate_capability/thoughtexperiment_predecessor_interface_v1.py",
    "domains/discourse_state.py",
    "seeds/communication_intent_arbitration.json",
    "substrate/world_adapter.py",
    "substrate/seed_loader.py",
    "runners/dsl/python/substrate_rs/__init__.py",
    "runners/dsl/src/graph_rules.rs",
    "runners/dsl/src/rewrite.rs",
)
CASES = ("retained_interface", "wrong_speaker", "intervening_topic_event",
         "topicless_chain", "missing_predecessor_edge", "omitted_target_interface")
REPEATS = 10


def digest(data) -> str:
    return hashlib.sha256(json.dumps(data, sort_keys=True, separators=(",", ":"),
                            default=str).encode()).hexdigest()


def source_hashes() -> dict:
    from substrate_rs import _native
    result = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
              for name in SOURCE_PATHS}
    result["native_extension"] = hashlib.sha256(Path(_native.__file__).resolve().read_bytes()).hexdigest()
    result["native_build_manifest"] = hashlib.sha256(
        (ROOT / "runners/dsl/python/substrate_rs/_native.build.json").read_bytes()).hexdigest()
    result["commit"] = subprocess.check_output(["git", "rev-parse", "HEAD"],
                                                cwd=ROOT, text=True).strip()
    return result


def build_case(case: str, replicate: int) -> dict:
    from substrate.seed_loader import manifest_for
    from substrate.world_adapter import WorldAdapter

    world = WorldAdapter(seeds=())
    # This seed is present as a JSON manifest but currently absent from the
    # Python Seed registry; explicit manifest loading keeps the measured rule
    # under test while surfacing that integration gap in the report.
    world.inner.load_seed_manifest(manifest_for("communication_intent_arbitration"),
                                   world.agent)
    state = world.s.add_node("DiscourseState", {
        "schema": "discourse_state.v1", "conversation_id": f"te-{case}-{replicate}",
        "event_index": 0,
    })
    world.inner.add_edge_unchecked(world.agent, "has_discourse_state", state, {})
    speaker = world.s.add_node("Person", {"name": "speaker-a"})
    other = world.s.add_node("Person", {"name": "speaker-b"})
    interpretation = world.s.add_node("CommunicationInterpretation", {
        "schema": "communication_interpretation.v1",
        "grounding_status": "candidate_grounded",
        "language_action_target_head": "open_calendar",
    })

    def event(index, kind, mode, topic, speaker_id):
        node = world.s.add_node("DiscourseEvent", {
            "schema": "discourse_event.v1", "event_index": index,
            "kind": kind, "interaction_mode": mode, "topic": topic,
        })
        for relation, target in (("from_speaker", speaker_id),
                                 ("to_addressee", world.agent)):
            world.inner.add_edge_unchecked(node, relation, target, {})
        world.inner.add_edge_unchecked(state, "has_event", node, {})
        return node

    prior = event(0, "instruction", "turn_compatible", "calendar", speaker)
    world.inner.add_edge_unchecked(prior, "has_interpretation", interpretation, {})
    world.inner.run_rules()
    target_indexed = world.inner.has_edge(prior, "has_scoped_action_target", interpretation)

    if case in ("intervening_topic_event", "topicless_chain"):
        middle_topic = "weather" if case == "intervening_topic_event" else None
        middle = event(1, "observation", "non_turn", middle_topic, speaker)
        world.inner.add_edge_unchecked(middle, "follows_event", prior, {})
        current = event(2, "observation", "non_turn", None, speaker)
        world.inner.add_edge_unchecked(current, "follows_event", middle, {})
        predecessor = middle
    else:
        current_speaker = other if case == "wrong_speaker" else speaker
        current = event(1, "observation", "non_turn", None, current_speaker)
        predecessor = prior
        if case != "missing_predecessor_edge":
            world.inner.add_edge_unchecked(current, "follows_event", prior, {})
        if case == "omitted_target_interface":
            world.inner.remove_edge(prior, "has_interpretation", interpretation)
            world.inner.remove_edge(prior, "has_scoped_action_target", interpretation)

    before = world.inner.graph_to_dict()
    started = time.perf_counter_ns()
    firings = int(world.inner.run_rules())
    elapsed = time.perf_counter_ns() - started
    after = world.inner.graph_to_dict()
    return {
        "case": case, "replicate": replicate,
        "target_indexed_before_current": target_indexed,
        "target_interface_available_at_closure": world.inner.has_edge(
            predecessor, "has_scoped_action_target", interpretation),
        "predecessor_edge_present": world.inner.has_edge(current, "follows_event", predecessor),
        "speaker_matches_predecessor": (case not in ("wrong_speaker",)),
        "carried_target": world.inner.has_edge(current, "has_scoped_action_target", interpretation),
        "firings": firings, "wall_ns": elapsed,
        "before_graph_sha256": digest(before), "after_graph_sha256": digest(after),
        "graph_delta_nodes": len(after["nodes"]) - len(before["nodes"]),
        "graph_delta_edges": len(after["edges"]) - len(before["edges"]),
    }


def main() -> None:
    if sys.argv[1:] == ["--lock"]:
        if LOCK.exists():
            raise SystemExit(f"refusing to overwrite {LOCK}")
        LOCK.write_text(json.dumps({"schema": "ThoughtexperimentPredecessorInterfaceLockV1",
                                    "locked_inputs": source_hashes()}, indent=2,
                                   sort_keys=True) + "\n")
        print(LOCK.relative_to(ROOT))
        return
    locked = source_hashes()
    if not LOCK.exists() or json.loads(LOCK.read_text()).get("locked_inputs") != locked:
        raise SystemExit("missing or stale source lock; run --lock for a new preregistration")
    rows = [build_case(case, repeat) for case in CASES for repeat in range(REPEATS)]
    post = source_hashes()
    positives = [r for r in rows if r["case"] == "retained_interface"]
    expected_carries = {"retained_interface", "topicless_chain"}
    checks = {
        "source_stable": post == locked,
        "all_positive_carries": all(r["carried_target"] for r in positives),
        "carry_matches_condition_semantics": all(
            r["carried_target"] == (r["case"] in expected_carries) for r in rows),
        "retained_positive_target_was_indexed": all(
            r["target_indexed_before_current"] for r in positives),
        "omitted_interface_absent_at_closure": all(
            not r["target_interface_available_at_closure"]
            for r in rows if r["case"] == "omitted_target_interface"),
    }
    summary = {}
    for case in CASES:
        group = [r for r in rows if r["case"] == case]
        summary[case] = {
            "n": len(group), "carry_rate": sum(r["carried_target"] for r in group) / len(group),
            "median_firings": statistics.median(r["firings"] for r in group),
            "median_wall_us": statistics.median(r["wall_ns"] for r in group) / 1000.0,
            "median_graph_delta_edges": statistics.median(r["graph_delta_edges"] for r in group),
        }
    report = {
        "schema": "ThoughtexperimentPredecessorInterfaceV1",
        "claim_boundary": "Rule-level evidence that this authored carry rule uses an immediately retained predecessor target with same-speaker/addressee continuity, propagates through chains of eligible topicless events, and stops at a topic-bearing event. It does not establish copy-on-write execution, scope projection semantics, broad frame locality, natural-task prevalence, or autonomous self-improvement.",
        "environment": {"python": sys.version, "platform": platform.platform(),
                        "seed_loading": "explicit manifest load; seed absent from domains.seed_registry"},
        "configuration": {"cases": CASES, "repeats_per_case": REPEATS,
                          "rule": "carry_scoped_action_target_across_topicless_event"},
        "locked_inputs": locked, "post_run_inputs": post, "checks": checks,
        "summary": summary, "rows": rows,
    }
    if OUT.exists():
        raise SystemExit(f"refusing to overwrite {OUT}")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"capture": OUT.relative_to(ROOT).as_posix(), "checks": checks,
                      "summary": summary}, indent=2))
    if not all(checks.values()):
        raise SystemExit("experiment checks failed")


if __name__ == "__main__":
    main()

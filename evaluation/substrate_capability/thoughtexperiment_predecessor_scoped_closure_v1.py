#!/usr/bin/env python3
"""Compare monolithic and Microtheory-scoped predecessor carry closure."""
from __future__ import annotations

import hashlib
import json
import platform
import statistics
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "runners" / "dsl" / "python")]
LOCK = ROOT / "evaluation/substrate_capability/thoughtexperiment_predecessor_scoped_closure_v1_lock_20261003.json"
OUT = ROOT / "evaluation/reports/thoughtexperiment_predecessor_scoped_closure_v1_20261003.json"
SOURCES = (
    "evaluation/substrate_capability/thoughtexperiment_predecessor_scoped_closure_v1.py",
    "evaluation/substrate_capability/thoughtexperiment_predecessor_interface_v1.py",
    "domains/seed_registry.py", "domains/discourse_state.py",
    "seeds/communication_intent_arbitration.json",
    "substrate/world_adapter.py", "substrate/boot_core.py",
    "runners/dsl/python/substrate_rs/__init__.py",
    "runners/dsl/src/substrate.rs", "runners/dsl/src/rewrite.rs",
)
REPEATS = 10
CASES = ("monolithic_retained", "scoped_retained", "scoped_wrong_speaker",
         "scoped_topic_interruption", "scoped_omitted_interface")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def locked_inputs() -> dict:
    from substrate_rs import _native
    result = {p: sha(ROOT / p) for p in SOURCES}
    result["native_extension"] = sha(Path(_native.__file__).resolve())
    result["native_build_manifest"] = sha(ROOT / "runners/dsl/python/substrate_rs/_native.build.json")
    result["commit"] = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    return result


def signature(world, event, target):
    carried = world.inner.has_edge(event, "has_scoped_action_target", target)
    return {"carry_edge": carried,
            "scoped_action_target_edges": sum(
                1 for e in world.inner.graph_to_dict()["edges"]
                if e.get("type") == "has_scoped_action_target")}


def run_case(case: str, repeat: int) -> dict:
    from substrate.boot_core import load_seeds_into
    from substrate.world_adapter import WorldAdapter

    world = WorldAdapter(seeds=())
    loaded = load_seeds_into(world.s, world.agent, ["communication_intent_arbitration"])
    state = world.s.add_node("DiscourseState", {"schema": "discourse_state.v1",
                                                "conversation_id": f"scoped-{case}-{repeat}",
                                                "event_index": 0})
    world.inner.add_edge_unchecked(world.agent, "has_discourse_state", state, {})
    speaker = world.s.add_node("Person", {"name": "speaker-a"})
    other = world.s.add_node("Person", {"name": "speaker-b"})
    target = world.s.add_node("CommunicationInterpretation", {
        "schema": "communication_interpretation.v1",
        "grounding_status": "candidate_grounded",
        "language_action_target_head": "open_calendar"})
    prior = world.s.add_node("DiscourseEvent", {
        "schema": "discourse_event.v1", "event_index": 0, "kind": "instruction",
        "interaction_mode": "turn_compatible", "topic": "calendar"})
    for src, rel, dst in ((state, "has_event", prior),
                          (prior, "from_speaker", speaker),
                          (prior, "to_addressee", world.agent),
                          (prior, "has_interpretation", target)):
        world.inner.add_edge_unchecked(src, rel, dst, {})
    seed_index_work = int(world.inner.run_rules())
    target_indexed = world.inner.has_edge(prior, "has_scoped_action_target", target)

    current_speaker = other if case == "scoped_wrong_speaker" else speaker
    current_topic = "weather" if case == "scoped_topic_interruption" else None
    current = world.s.add_node("DiscourseEvent", {
        "schema": "discourse_event.v1", "event_index": 1,
        "predecessor_event_index": 0, "kind": "observation",
        "interaction_mode": "non_turn", "topic": current_topic})
    for src, rel, dst in ((state, "has_event", current),
                          (current, "from_speaker", current_speaker),
                          (current, "to_addressee", world.agent),
                          (current, "follows_event", prior)):
        world.inner.add_edge_unchecked(src, rel, dst, {})
    if case == "scoped_omitted_interface":
        world.inner.remove_edge(prior, "has_interpretation", target)
        world.inner.remove_edge(prior, "has_scoped_action_target", target)

    mt = world.s.add_node("Microtheory", {"name": f"current-frame-{repeat}"})
    world.inner.add_edge_unchecked(mt, "has_concept", current, {})
    before = signature(world, current, target)
    started = time.perf_counter_ns()
    if case == "monolithic_retained":
        work = int(world.inner.run_rules())
        arm = "monolithic"
    else:
        work = int(world.inner.run_rules_scoped(100_000, False, mt))
        arm = "microtheory_scoped"
    elapsed = time.perf_counter_ns() - started
    after = signature(world, current, target)
    return {"case": case, "replicate": repeat, "arm": arm,
            "installed_seed_ids": sorted(loaded), "seed_index_work": seed_index_work,
            "target_indexed": target_indexed,
            "predecessor_in_scope": False,
            "current_event_in_scope": True,
            "predecessor_edge_visible": world.inner.has_edge(current, "follows_event", prior),
            "predecessor_target_interface_visible": world.inner.has_edge(
                prior, "has_scoped_action_target", target),
            "before": before, "after": after, "work": work,
            "wall_ns": elapsed}


def main() -> None:
    if sys.argv[1:] == ["--lock"]:
        if LOCK.exists():
            raise SystemExit(f"refusing to overwrite {LOCK}")
        LOCK.write_text(json.dumps({"schema": "ThoughtexperimentPredecessorScopedClosureLockV1",
                                    "locked_inputs": locked_inputs()}, indent=2, sort_keys=True) + "\n")
        print(LOCK.relative_to(ROOT))
        return
    locked = locked_inputs()
    if not LOCK.exists() or json.loads(LOCK.read_text()).get("locked_inputs") != locked:
        raise SystemExit("missing or stale source lock; preregister with --lock")
    rows = [run_case(case, i) for case in CASES for i in range(REPEATS)]
    post = locked_inputs()
    by_case = {case: [r for r in rows if r["case"] == case] for case in CASES}
    expected = {"monolithic_retained": True, "scoped_retained": True,
                "scoped_wrong_speaker": False, "scoped_topic_interruption": False,
                "scoped_omitted_interface": False}
    checks = {
        "source_stable": post == locked,
        "all_seed_loads_registered": all("communication_intent_arbitration" in r["installed_seed_ids"] for r in rows),
        "prior_target_indexed_before_partition": all(r["target_indexed"] for r in rows),
        "scoped_cases_own_current_not_predecessor": all(
            r["current_event_in_scope"] and not r["predecessor_in_scope"]
            for r in rows if r["arm"] == "microtheory_scoped"),
        "carry_matches_condition": all(
            r["after"]["carry_edge"] is expected[r["case"]] for r in rows),
        "retained_interface_visible_when_expected": all(
            r["predecessor_target_interface_visible"]
            for c in ("monolithic_retained", "scoped_retained", "scoped_wrong_speaker", "scoped_topic_interruption")
            for r in by_case[c]),
        "omitted_interface_not_visible": all(
            not r["predecessor_target_interface_visible"]
            for r in by_case["scoped_omitted_interface"]),
        "monolithic_scoped_positive_parity": all(
            a["after"]["carry_edge"] == b["after"]["carry_edge"]
            for a, b in zip(by_case["monolithic_retained"], by_case["scoped_retained"])),
    }
    summary = {}
    for case, group in by_case.items():
        summary[case] = {"n": len(group), "carry_rate": sum(r["after"]["carry_edge"] for r in group) / len(group),
                         "median_work": statistics.median(r["work"] for r in group),
                         "median_wall_us": statistics.median(r["wall_ns"] for r in group) / 1000.0}
    report = {"schema": "ThoughtexperimentPredecessorScopedClosureV1",
              "claim_boundary": "Tests a one-rule, tiny-graph comparison of monolithic and Microtheory-scoped fixpoints. The predecessor node remains globally readable through the shared graph; this is not physical partitioning, Cow isolation, general closure parity, or a scaling result.",
              "environment": {"python": sys.version, "platform": platform.platform()},
              "configuration": {"cases": CASES, "repeats_per_case": REPEATS,
                                "scope_policy": "own only the current event; predecessor is outside membership but remains in shared graph"},
              "locked_inputs": locked, "post_run_inputs": post, "checks": checks,
              "summary": summary, "rows": rows}
    if OUT.exists():
        raise SystemExit(f"refusing to overwrite {OUT}")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"capture": OUT.relative_to(ROOT).as_posix(), "checks": checks,
                      "summary": summary}, indent=2))
    if not all(checks.values()):
        raise SystemExit("scoped closure gates failed")


if __name__ == "__main__":
    main()

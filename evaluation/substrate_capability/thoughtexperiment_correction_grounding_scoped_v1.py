#!/usr/bin/env python3
"""Cross-frame scoped closure panel for definite-correction grounding."""
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
LOCK = ROOT / "evaluation/substrate_capability/thoughtexperiment_correction_grounding_scoped_v1_lock_20261003.json"
OUT = ROOT / "evaluation/reports/thoughtexperiment_correction_grounding_scoped_v1_20261003.json"
SOURCES = (
    "evaluation/substrate_capability/thoughtexperiment_correction_grounding_scoped_v1.py",
    "domains/seed_registry.py", "seeds/communication_intent_arbitration.json",
    "substrate/boot_core.py", "substrate/world_adapter.py",
    "runners/dsl/src/substrate.rs", "runners/dsl/src/rewrite.rs",
    "runners/dsl/python/substrate_rs/__init__.py",
)
CASES = ("monolithic_retained", "scoped_retained", "scoped_wrong_speaker",
         "scoped_wrong_head", "scoped_missing_edge", "scoped_intervening_topic",
         "scoped_omitted_target")
REPEATS = 10
EXPECTED = {name: name in ("monolithic_retained", "scoped_retained") for name in CASES}
EVIDENCE = "CommunicationInterpretation -> discourse-scoped DiscourseState -> prior grounded DiscourseEvent -> matching action-target head"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def lock_inputs() -> dict:
    from substrate_rs import _native
    values = {p: sha(ROOT / p) for p in SOURCES}
    values["native_extension"] = sha(Path(_native.__file__).resolve())
    values["native_build_manifest"] = sha(ROOT / "runners/dsl/python/substrate_rs/_native.build.json")
    values["commit"] = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    return values


def run_case(case: str, repeat: int) -> dict:
    from substrate.boot_core import load_seeds_into
    from substrate.world_adapter import WorldAdapter

    world = WorldAdapter(seeds=())
    loaded = load_seeds_into(world.s, world.agent, ["communication_intent_arbitration"])
    state = world.s.add_node("DiscourseState", {"schema": "discourse_state.v1",
                                                "conversation_id": f"correction-{case}-{repeat}",
                                                "event_index": 0})
    world.inner.add_edge_unchecked(world.agent, "has_discourse_state", state, {})
    speaker = world.s.add_node("Person", {"name": "speaker-a"})
    other = world.s.add_node("Person", {"name": "speaker-b"})
    prior_i = world.s.add_node("CommunicationInterpretation", {
        "schema": "communication_interpretation.v1",
        "grounding_status": "candidate_grounded",
        "language_action_target_head": "open_calendar"})
    prior = world.s.add_node("DiscourseEvent", {
        "schema": "discourse_event.v1", "event_index": 0,
        "kind": "instruction", "interaction_mode": "turn_compatible",
        "topic": "calendar"})
    for src, rel, dst in ((state, "has_event", prior),
                          (prior, "has_interpretation", prior_i),
                          (prior, "from_speaker", speaker),
                          (prior, "to_addressee", world.agent)):
        world.inner.add_edge_unchecked(src, rel, dst, {})
    prior_work = int(world.inner.run_rules())
    indexed = world.inner.has_edge(prior, "has_scoped_action_target", prior_i)

    predecessor = prior
    current_index = 1
    if case == "scoped_intervening_topic":
        predecessor = world.s.add_node("DiscourseEvent", {
            "schema": "discourse_event.v1", "event_index": 1,
            "predecessor_event_index": 0, "kind": "observation",
            "interaction_mode": "non_turn", "topic": "weather"})
        for src, rel, dst in ((state, "has_event", predecessor),
                              (predecessor, "follows_event", prior),
                              (predecessor, "from_speaker", speaker),
                              (predecessor, "to_addressee", world.agent)):
            world.inner.add_edge_unchecked(src, rel, dst, {})
        world.inner.run_rules()
        current_index = 2

    current_speaker = other if case == "scoped_wrong_speaker" else speaker
    referential_head = "close_calendar" if case == "scoped_wrong_head" else "open_calendar"
    current_i = world.s.add_node("CommunicationInterpretation", {
        "schema": "communication_interpretation.v1",
        "language_definite_nominal_reference": 1.0,
        "language_discourse_relation": "correction",
        "interaction_relation": "response",
        "parsed_subject_pos": "noun",
        "grounding_status": "unresolved",
        "grounding_evidence_path": "",
        "language_referential_head": referential_head})
    current = world.s.add_node("DiscourseEvent", {
        "schema": "discourse_event.v1", "event_index": current_index,
        "predecessor_event_index": current_index - 1,
        "kind": "statement", "interaction_mode": "turn_compatible"})
    for src, rel, dst in ((state, "has_event", current),
                          (current, "has_interpretation", current_i),
                          (current, "from_speaker", current_speaker),
                          (current, "to_addressee", world.agent),
                          (current, "follows_event", predecessor)):
        world.inner.add_edge_unchecked(src, rel, dst, {})
    if case == "scoped_missing_edge":
        world.inner.remove_edge(current, "follows_event", predecessor)
    if case == "scoped_omitted_target":
        world.inner.remove_edge(prior, "has_interpretation", prior_i)
        world.inner.remove_edge(prior, "has_scoped_action_target", prior_i)

    frame = world.s.add_node("Microtheory", {"name": f"correction-frame-{repeat}"})
    world.inner.add_edge_unchecked(frame, "has_concept", current, {})
    world.inner.add_edge_unchecked(frame, "has_concept", current_i, {})
    before_attrs = dict(world.s.node(current_i)["attrs"])
    started = time.perf_counter_ns()
    if case == "monolithic_retained":
        work = int(world.inner.run_rules())
        arm = "monolithic"
    else:
        work = int(world.inner.run_rules_scoped(100_000, False, frame))
        arm = "microtheory_scoped"
    elapsed_ns = time.perf_counter_ns() - started
    after_attrs = dict(world.s.node(current_i)["attrs"])
    return {
        "case": case, "repeat": repeat, "arm": arm,
        "loaded_seed_ids": sorted(loaded), "prior_index_work": prior_work,
        "prior_action_target_indexed": indexed,
        "current_event_owned": True, "current_interpretation_owned": True,
        "predecessor_owned": False,
        "predecessor_link_present": world.inner.has_edge(current, "follows_event", predecessor),
        "predecessor_target_present": world.inner.has_edge(predecessor, "has_scoped_action_target", prior_i),
        "before_grounding_status": before_attrs.get("grounding_status"),
        "after_grounding_status": after_attrs.get("grounding_status"),
        "after_evidence_path": after_attrs.get("grounding_evidence_path"),
        "grounded": after_attrs.get("grounding_status") == "candidate_grounded",
        "work": work, "wall_ns": elapsed_ns,
    }


def main() -> None:
    if sys.argv[1:] == ["--lock"]:
        if LOCK.exists():
            raise SystemExit(f"refusing to overwrite {LOCK}")
        LOCK.write_text(json.dumps({"schema": "ThoughtexperimentCorrectionGroundingScopedLockV1",
                                    "locked_inputs": lock_inputs()}, indent=2, sort_keys=True) + "\n")
        print(LOCK.relative_to(ROOT))
        return
    locked = lock_inputs()
    if not LOCK.exists() or json.loads(LOCK.read_text()).get("locked_inputs") != locked:
        raise SystemExit("missing or stale lock; create a fresh preregistration with --lock")
    rows = [run_case(case, repeat) for case in CASES for repeat in range(REPEATS)]
    post = lock_inputs()
    groups = {case: [r for r in rows if r["case"] == case] for case in CASES}
    checks = {
        "source_stable": post == locked,
        "registered_seed_loads": all("communication_intent_arbitration" in r["loaded_seed_ids"] for r in rows),
        "prior_action_target_indexed": all(r["prior_action_target_indexed"] for r in rows),
        "scope_owns_current_effect_target_only": all(
            r["current_event_owned"] and r["current_interpretation_owned"] and not r["predecessor_owned"]
            for r in rows if r["arm"] == "microtheory_scoped"),
        "grounding_matches_semantic_controls": all(r["grounded"] is EXPECTED[r["case"]] for r in rows),
        "exact_evidence_string_on_positives": all(
            r["after_evidence_path"] == EVIDENCE for r in rows if r["grounded"]),
        "monolithic_scoped_positive_parity": all(
            a["grounded"] == b["grounded"]
            for a, b in zip(groups["monolithic_retained"], groups["scoped_retained"])),
        "topic_interruption_has_no_predecessor_target": all(
            not r["predecessor_target_present"] for r in groups["scoped_intervening_topic"]),
    }
    summary = {}
    for case, group in groups.items():
        summary[case] = {"n": len(group), "grounding_rate": sum(r["grounded"] for r in group) / len(group),
                         "median_work": statistics.median(r["work"] for r in group),
                         "median_wall_us": statistics.median(r["wall_ns"] for r in group) / 1000.0}
    report = {
        "schema": "ThoughtexperimentCorrectionGroundingScopedV1",
        "claim_boundary": "One seeded correction-grounding rule was compared on a tiny synthetic graph with monolithic and current-frame-scoped closure. The predecessor is outside ownership but globally readable; this does not demonstrate graph isolation, CoW, general partition parity, or scaling.",
        "environment": {"python": sys.version, "platform": platform.platform()},
        "configuration": {"cases": CASES, "repeats_per_case": REPEATS,
                          "current_frame_owns": ["current_event", "current_interpretation"],
                          "prior_event_and_target_outside_frame": True},
        "locked_inputs": locked, "post_run_inputs": post,
        "checks": checks, "summary": summary, "rows": rows,
    }
    if OUT.exists():
        raise SystemExit(f"refusing to overwrite {OUT}")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"capture": OUT.relative_to(ROOT).as_posix(), "checks": checks,
                      "summary": summary}, indent=2))
    if not all(checks.values()):
        raise SystemExit("correction grounding gates failed")


if __name__ == "__main__":
    main()

"""Deterministic memory/learning probe supplemental to the frozen Phase 8 set.

The fixed 74-event corpus has no teacher-learning or repeated-memory sequence,
so those scorecard dimensions are explicitly unavailable there. This probe
tests a controlled teacher -> grounded answer -> intervening turn -> recall
path using only native graph evidence and released production receipts.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


SCHEMA = "phase8_memory_learning_probe.v2"
PROTOCOL = "phase8b-multi-topic-teacher-interference-repeat-v2"
PROBE_CASES = (
    ("qzxmemorybeacon", "qzxmemorybeacon is green and stable."),
    ("jvrfocusrelay", "jvrfocusrelay is warm and humming."),
    ("nplarchivekey", "nplarchivekey is silver and notched."),
    ("wmkharborpanel", "wmkharborpanel stays open until sunrise."),
    ("cxdistanceflag", "cxdistanceflag is beside the eastern arch."),
)


def _held_answer_evidence(agent, topic: str) -> dict[str, Any] | None:
    for held in agent.inner.neighbours(agent.agent, "holds_answer"):
        if not agent.s.has_node(held):
            continue
        attrs = dict(agent.s.node(held)["attrs"])
        if attrs.get("topic") != topic:
            continue
        evidence = next((node for node in agent.inner.neighbours(
            held, "grounded_by")
            if agent.s.has_node(node)
            and agent.s.node(node)["type"] == "TopicGroundingEvidence"
            and agent.s.node(node)["attrs"].get("kind") == "topic_answer"
            and agent.s.node(node)["attrs"].get("referent") == topic
            and agent.s.node(node)["attrs"].get("status") == "supported"
            and agent.s.node(node)["attrs"].get("evidence_path")), None)
        if evidence is not None:
            return {
                "held_answer_id": int(held.value),
                "evidence_id": int(evidence.value),
                "evidence_path": str(agent.s.node(evidence)["attrs"][
                    "evidence_path"]),
            }
    return None


def _turn_evidence(agent, reply: str) -> dict[str, Any]:
    inbound = agent._last_turn_inbound
    trace = agent.reply_turn_trace(agent.last_turn_inbound_id()) or {}
    envelope = agent.production_turn_evidence(inbound)
    commitment = trace.get("answer_commitment") or {}
    receipts = envelope.get("production_gate_receipts") or []
    released = next((item for item in receipts
                     if item.get("status") == "released"), None)
    return {
        "reply": str(reply or ""),
        "answer_commitment_kind": commitment.get("kind"),
        "answer_graph_linked": commitment.get("graph_linked_to_turn") is True,
        "held_answer_id": commitment.get("held_answer_id"),
        "grounding_evidence_id": commitment.get("grounding_evidence_id"),
        "receipt_status": released.get("status") if released else None,
        "receipt_id": released.get("node_id") if released else None,
        "grounded_answer": commitment.get("kind")
            == "supported_event_bound_topic_answer",
    }


def run_probe() -> dict[str, Any]:
    """Measure multiple topic bindings through intervening graph activity."""
    from substrate.boot_all import load_all_seeds
    from substrate.world_adapter import WorldAdapter

    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)

    cases: dict[str, dict[str, Any]] = {}
    for topic, answer in PROBE_CASES:
        absent = agent.answer_about(topic, release=False) is None
        taught = agent.learn_from_teacher(topic, {
            "answer": answer,
            "learn": [{"phrase": topic, "answer": answer}],
        })
        cases[topic] = {
            "topic": topic,
            "answer": answer,
            "prelearning_answer_absent": absent,
            "teacher_payload_matches": taught == answer,
            "source_evidence": _held_answer_evidence(agent, topic),
        }

    # Initial retrievals are interleaved across five separately taught
    # topics. The recall phase follows two unrelated turns, testing both
    # cross-topic binding and persistence beyond the immediate teaching step.
    for topic, answer in PROBE_CASES:
        question = f"What do you know about {topic}?"
        reply = agent.converse(question, speech_act="question")
        cases[topic]["first_answer"] = _turn_evidence(agent, reply)

    middle_turns = []
    for signal, speech_act in (
            ("How are you organised?", "question"),
            ("The sky is blue.", "statement")):
        reply = agent.converse(signal, speech_act=speech_act)
        middle_turns.append(_turn_evidence(agent, reply))

    for topic, answer in PROBE_CASES:
        question = f"What do you know about {topic}?"
        reply = agent.converse(question, speech_act="question")
        cases[topic]["delayed_repeat"] = _turn_evidence(agent, reply)

    learning_passes = []
    memory_passes = []
    for topic, answer in PROBE_CASES:
        item = cases[topic]
        first = item["first_answer"]
        repeated = item["delayed_repeat"]
        learning_passes.append(bool(
            item["prelearning_answer_absent"]
            and item["teacher_payload_matches"]
            and item["source_evidence"]
            and first["grounded_answer"] and first["answer_graph_linked"]
            and answer.casefold() in first["reply"].casefold()
            and first["receipt_status"] == "released"
        ))
        memory_passes.append(bool(
            repeated["grounded_answer"] and repeated["answer_graph_linked"]
            and answer.casefold() in repeated["reply"].casefold()
            and repeated["receipt_status"] == "released"
            and first["receipt_id"] != repeated["receipt_id"]
            and first["held_answer_id"] == repeated["held_answer_id"]
            and first["grounding_evidence_id"]
            == repeated["grounding_evidence_id"]
        ))

    learning_successes = sum(learning_passes)
    memory_successes = sum(memory_passes)
    all_absent = all(item["prelearning_answer_absent"]
                     for item in cases.values())
    all_teacher_match = all(item["teacher_payload_matches"]
                            for item in cases.values())
    all_sources_grounded = all(item["source_evidence"]
                               for item in cases.values())
    return {
        "schema": SCHEMA,
        "protocol_id": PROTOCOL,
        "status": "measured",
        "scores": {
            "learning": {"successes": learning_successes,
                         "n": len(PROBE_CASES),
                         "mean": learning_successes / len(PROBE_CASES)},
            "memory": {"successes": memory_successes,
                       "n": len(PROBE_CASES),
                       "mean": memory_successes / len(PROBE_CASES)},
        },
        "controls": {
            "prelearning_answers_absent": all_absent,
            "teacher_payloads_match": all_teacher_match,
            "typed_grounding_evidence_present": all_sources_grounded,
            "distinct_held_answers": len({
                item["source_evidence"]["held_answer_id"]
                for item in cases.values() if item["source_evidence"]
            }) == len(PROBE_CASES),
        },
        "cases": cases,
        "intervening_turns": middle_turns,
        "limitations": [
            "Five controlled target-system cases; not a population estimate.",
            "No reference model has been run under this probe protocol.",
            "Frozen Phase 8 corpus and its scores are unchanged.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    result = run_probe()
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return int(not all(result["scores"][key]["successes"] == 1
                       for key in ("learning", "memory")))


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

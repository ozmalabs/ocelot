from __future__ import annotations

import random
import json
import subprocess
import sys

import pytest

from evaluation.phase8_blinded_annotation_packet import (
    BEHAVIOR_DIMENSIONS,
    build_blinded_packet,
)
from evaluation.phase8_corpus_runner import CONTEXT_AWARE_PROTOCOL_ID


def _llm_run(system, rows):
    return {
        "system": system,
        "protocol_id": CONTEXT_AWARE_PROTOCOL_ID,
        "input_profile": "event_context_v5_history8",
        "session_history_limit": 8,
        "observations": [
            {"case_id": case_id,
             "response": {"stdout": response}}
            for case_id, response in rows
        ],
    }


def test_blinded_packet_hides_labels_and_keeps_key_separate():
    corpus = {"events": [
        {"id": "case_one", "signal": "Can you inspect the sensor?",
         "event_mode": "turn_compatible", "interaction_relation": "standalone",
         "communicative_force": "request_action", "expected_state": "act",
         "grounding_status": "grounded", "setup": {"held_answers": []}},
        {"id": "case_two", "signal": "Did it work?",
         "event_mode": "turn_compatible", "interaction_relation": "continuation",
         "communicative_force": "request_information", "expected_state": "repair",
         "grounding_status": "unresolved_reference", "setup": {
             "held_answers": [{"topic": "sensor", "answer": "nominal"}]}},
    ]}
    target = {
        "protocol_id": CONTEXT_AWARE_PROTOCOL_ID,
        "observations": [
            {"id": "case_one", "reply": "I can inspect the sensor."},
            {"id": "case_two", "reply": "What does it refer to?"},
        ],
    }
    eliza = {
        "protocol_id": CONTEXT_AWARE_PROTOCOL_ID,
        "input_profile": "event_context_v5_history8",
        "session_history_limit": 8,
        "observations": [
            {"case_id": "case_one", "output": "Please tell me more."},
            {"case_id": "case_two", "output": "Why do you ask?"},
        ],
    }
    gemma = _llm_run("small_llm", [
        ("case_one", "I can inspect it."), ("case_two", "Yes."),
    ])
    gemma_repeat = _llm_run("small_llm", [
        ("case_one", "I can inspect it."), ("case_two", "Yes."),
    ])
    qwen = _llm_run("modern_llm", [
        ("case_one", "I will inspect the sensor."),
        ("case_two", "What did you mean by it?"),
    ])
    qwen_repeat = _llm_run("modern_llm", [
        ("case_one", "I can check the sensor now."),
        ("case_two", "Could you clarify what ‘it’ means?"),
    ])

    packet, key = build_blinded_packet(
        corpus, target,
        {"eliza_floor": eliza, "small_llm": [gemma, gemma_repeat],
         "modern_llm": [qwen, qwen_repeat]},
        rng=random.Random(13),
    )

    assert packet["corpus_event_count"] == 2
    assert len(packet["annotation_rows"]) == 10
    serialized = repr(packet)
    for hidden in ("case_one", "communicative_force", "expected_state",
                   "grounding_status", "small_llm", "gemma", "qwen"):
        assert hidden not in serialized
    assert all(row["scores"] == {dimension: None
                                for dimension in BEHAVIOR_DIMENSIONS}
               for row in packet["annotation_rows"])
    assert key["cases"][0]["case_id"] == "case_one"
    assert sorted((v["system"], v["run_index"])
                  for v in key["cases"][0]["response_aliases"].values()) == [
        ("conversational_manifold", None), ("eliza_floor", None),
        ("modern_llm", 0), ("modern_llm", 1), ("small_llm", None),
    ]
    second = next(item for item in packet["cases"]
                  if item["case_code"] == "case_002")
    sample_with_context = next(sample for sample in second["samples"]
                               if sample["context"]["held_facts"])
    assert sample_with_context["context"]["held_facts"] == [
        {"topic": "sensor", "answer": "nominal"}
    ]
    assert len(sample_with_context["context"]["history"]) == 1
    assert key["source_provenance"]["small_llm"]["run_count"] == 2
    assert key["source_provenance"]["modern_llm"]["repeat_outputs_identical"] is False


def test_blinded_packet_requires_gemma_repeat_outputs_to_match():
    corpus = {"events": [{"id": "case_one", "signal": "Hello."}]}
    target = {"protocol_id": CONTEXT_AWARE_PROTOCOL_ID,
              "observations": [{"id": "case_one", "reply": "Hello."}]}
    eliza = {"protocol_id": CONTEXT_AWARE_PROTOCOL_ID,
             "input_profile": "event_context_v5_history8",
             "session_history_limit": 8,
             "observations": [{"case_id": "case_one", "output": "Hello."}]}
    small_a = _llm_run("small_llm", [("case_one", "Hi.")])
    small_b = _llm_run("small_llm", [("case_one", "Hello there.")])
    modern = _llm_run("modern_llm", [("case_one", "Hello.")])

    with pytest.raises(ValueError, match="Gemma repeated run responses differ"):
        build_blinded_packet(
            corpus, target,
            {"eliza_floor": eliza, "small_llm": [small_a, small_b],
             "modern_llm": [modern, modern]},
        )


def test_blinded_packet_includes_supplied_human_sessions_without_exposing_identity():
    corpus = {"events": [{"id": "case_one", "signal": "Hello."}]}
    target = {"protocol_id": CONTEXT_AWARE_PROTOCOL_ID,
              "observations": [{"id": "case_one", "reply": "Hello."}]}
    eliza = {"protocol_id": CONTEXT_AWARE_PROTOCOL_ID,
             "input_profile": "event_context_v5_history8",
             "session_history_limit": 8,
             "observations": [{"case_id": "case_one", "output": "Hello."}]}
    small = _llm_run("small_llm", [("case_one", "Hi there.")])
    modern = _llm_run("modern_llm", [("case_one", "Good day.")])
    human_run = lambda system, response: {
        "system": system,
        "protocol_id": CONTEXT_AWARE_PROTOCOL_ID,
        "input_profile": "event_context_v5_history8",
        "run_id": f"private-{system}",
        "observations": [{"case_id": "case_one", "response": response}],
    }

    packet, key = build_blinded_packet(
        corpus, target,
        {"eliza_floor": eliza, "small_llm": [small, small],
         "modern_llm": [modern, modern],
         "base_human": human_run("base_human", "Hello!"),
         "advanced_human": human_run("advanced_human", "Hello there.")},
        rng=random.Random(8),
    )

    assert len(packet["annotation_rows"]) == 7
    assert "base_human" not in repr(packet)
    assert "advanced_human" not in repr(packet)
    assert "private-base_human" not in repr(packet)
    assert {item["system"] for item in key["cases"][0]["response_aliases"].values()} >= {
        "base_human", "advanced_human"
    }
    assert key["source_provenance"]["base_human"]["run_ids"] == [
        "private-base_human"
    ]


def test_packet_cli_accepts_optional_human_run_files(tmp_path):
    corpus = {"protocol_id": CONTEXT_AWARE_PROTOCOL_ID,
              "events": [{"id": "case_one", "signal": "Hello."}]}
    target = {"protocol_id": CONTEXT_AWARE_PROTOCOL_ID,
              "observations": [{"id": "case_one", "reply": "Hello."}]}
    eliza = {"protocol_id": CONTEXT_AWARE_PROTOCOL_ID,
             "input_profile": "event_context_v5_history8",
             "session_history_limit": 8,
             "observations": [{"case_id": "case_one", "output": "Hi."}]}
    small = _llm_run("small_llm", [("case_one", "Hi.")])
    modern = _llm_run("modern_llm", [("case_one", "Hello there.")])
    base_human = {
        "protocol_id": CONTEXT_AWARE_PROTOCOL_ID,
        "input_profile": "event_context_v5_history8",
        "observations": [{"case_id": "case_one", "response": "Hello!"}],
    }
    files = {}
    for name, value in {
        "corpus": corpus, "target": target, "eliza": eliza,
        "small": small, "small_repeat": small,
        "modern": modern, "modern_repeat": modern,
        "base_human": base_human,
    }.items():
        path = tmp_path / f"{name}.json"
        path.write_text(json.dumps(value), encoding="utf-8")
        files[name] = path
    packet_path, key_path = tmp_path / "packet.json", tmp_path / "key.json"

    result = subprocess.run([
        sys.executable, "-m", "evaluation.phase8_blinded_annotation_packet",
        "--corpus", str(files["corpus"]), "--target", str(files["target"]),
        "--eliza", str(files["eliza"]),
        "--small-llm", str(files["small"]),
        "--small-llm", str(files["small_repeat"]),
        "--modern-llm", str(files["modern"]),
        "--modern-llm", str(files["modern_repeat"]),
        "--base-human", str(files["base_human"]),
        "--packet-out", str(packet_path), "--key-out", str(key_path),
    ], capture_output=True, text=True, check=False)

    assert result.returncode == 0, result.stderr
    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    key = json.loads(key_path.read_text(encoding="utf-8"))
    assert len(packet["annotation_rows"]) == 6
    assert {entry["system"] for entry in
            key["cases"][0]["response_aliases"].values()} >= {"base_human"}

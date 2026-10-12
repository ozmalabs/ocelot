import json
from types import SimpleNamespace

import pytest

import evaluation.reference_adapters.ollama_local as adapter
from evaluation.reference_adapters.ollama_local import collect_raw_observations


def _corpus():
    return {"schema": "communication_event_corpus.v1", "events": [
        {"id": "case-a", "signal": "Can you inspect it?"},
        {"id": "case-b", "signal": "The gate is open."},
    ]}


def test_local_adapter_records_raw_requests_without_scoring():
    calls = []

    def fake_run(command, **kwargs):
        calls.append((command, kwargs))
        return SimpleNamespace(stdout="raw answer", stderr="", returncode=0)

    envelope = collect_raw_observations("small_llm", corpus=_corpus(), transport="cli", run=fake_run)
    assert envelope["collection_status"] == "measured"
    assert len(calls) == 2
    assert all(item["annotation_status"] == "unavailable" for item in envelope["observations"])
    assert all(item["status"] == "unavailable" for item in envelope["scorecard"]["measurements"])


def test_local_adapter_preserves_failed_raw_collection_as_unavailable():
    def fake_run(command, **kwargs):
        return SimpleNamespace(stdout="", stderr="model failed", returncode=1)

    envelope = collect_raw_observations("modern_llm", corpus=_corpus(), transport="cli", run=fake_run)
    assert envelope["collection_status"] == "unavailable"
    assert len(envelope["collection_failures"]) == 2
    assert envelope["observations"][0]["response"]["stderr"] == "model failed"


def test_local_adapter_rejects_non_llm_reference_classes():
    with pytest.raises(ValueError):
        collect_raw_observations("eliza_floor", corpus=_corpus(), transport="cli", run=lambda *a, **k: None)


def test_http_transport_keeps_raw_json_provenance(monkeypatch):
    calls = []

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return b'{"response":"raw http answer","done":true,"eval_count":4}'

    def fake_urlopen(request, timeout):
        calls.append(json.loads(request.data.decode("utf-8")))
        return FakeResponse()

    monkeypatch.setattr(adapter.urllib.request, "urlopen", fake_urlopen)
    envelope = collect_raw_observations(
        "small_llm", corpus={"events": [{"id": "one", "signal": "Hello."}]},
        transport="http", num_predict=12, num_gpu=0, seed=17,
        temperature=0.0,
    )
    item = envelope["observations"][0]
    assert envelope["collection_status"] == "measured"
    assert item["response"]["stdout"] == "raw http answer"
    assert item["request"]["response_json"]["eval_count"] == 4
    assert calls[0]["options"] == {
        "num_predict": 12, "num_gpu": 0, "seed": 17, "temperature": 0.0,
    }
    assert item["request"]["num_gpu"] == 0
    assert envelope["inference_options"]["seed"] == 17


def test_cpu_only_option_rejects_cli_transport():
    with pytest.raises(ValueError, match="only enforceable through Ollama HTTP"):
        collect_raw_observations(
            "small_llm", corpus=_corpus(), transport="cli", num_gpu=0,
            run=lambda *args, **kwargs: None,
        )


def test_matched_session_input_carries_context_without_reference_labels():
    calls = []

    def fake_run(command, **kwargs):
        calls.append((command, kwargs))
        return SimpleNamespace(stdout=f"response {len(calls)}", stderr="",
                               returncode=0)

    corpus = {"schema": "communication_event_corpus.v1", "events": [
        {"id": "case-a", "signal": "The gate is open.",
         "event_mode": "turn_compatible", "interaction_relation": "response",
         "expected_state": "learn", "literal_form": "declarative"},
        {"id": "case-b", "signal": "Is it still open?",
         "event_mode": "turn_compatible", "interaction_relation": "continuation",
         "setup": {"held_answers": [
             {"topic": "gate", "answer": "The gate is open."}]},
         "expected_state": "answer", "communicative_force": "request_information"},
    ]}
    envelope = collect_raw_observations(
        "small_llm", corpus=corpus, transport="cli", run=fake_run,
        session_context=True,
    )

    first = envelope["observations"][0]["request"]["prompt"]
    second = envelope["observations"][1]["request"]["prompt"]
    assert envelope["protocol_id"] == adapter.CONTEXT_AWARE_PROTOCOL_ID
    assert envelope["scorecard"]["protocol_id"] == envelope["protocol_id"]
    assert envelope["input_profile"] == "event_context_v5_history8"
    assert envelope["session_history_limit"] == 8
    assert "mode: turn_compatible" in first
    assert "expected_state" not in first and "learn" not in first
    assert "Facts already held before this event" in second
    assert "gate: The gate is open." in second
    assert "User: The gate is open." in second
    assert "Assistant: response 1" in second
    assert "expected_state" not in second
    assert "communicative_force" not in second


def test_matched_session_history_is_bounded_to_recent_eight_turns():
    calls = []

    def fake_run(command, **kwargs):
        calls.append(command[-1])
        return SimpleNamespace(stdout=f"response {len(calls)}", stderr="",
                               returncode=0)

    corpus = {"events": [
        {"id": f"case-{index}", "signal": f"signal {index}",
         "event_mode": "turn_compatible",
         "interaction_relation": "turn_compatible"}
        for index in range(10)
    ]}
    envelope = collect_raw_observations(
        "small_llm", corpus=corpus, transport="cli", run=fake_run,
        session_context=True,
    )
    last_prompt = envelope["observations"][-1]["request"]["prompt"]
    assert "User: signal 0\n" not in last_prompt
    assert "User: signal 1\n" in last_prompt
    assert "User: signal 8\n" in last_prompt
    assert "Current message: signal 9" in last_prompt

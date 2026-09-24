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
    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return b'{"response":"raw http answer","done":true,"eval_count":4}'

    monkeypatch.setattr(adapter.urllib.request, "urlopen", lambda request, timeout: FakeResponse())
    envelope = collect_raw_observations(
        "small_llm", corpus={"events": [{"id": "one", "signal": "Hello."}]},
        transport="http", num_predict=12,
    )
    item = envelope["observations"][0]
    assert envelope["collection_status"] == "measured"
    assert item["response"]["stdout"] == "raw http answer"
    assert item["request"]["response_json"]["eval_count"] == 4

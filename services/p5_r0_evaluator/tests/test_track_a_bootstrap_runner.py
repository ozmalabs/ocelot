from __future__ import annotations

import json
from pathlib import Path

import pytest

from services.p5_r0_evaluator.canonical import digest
from services.p5_r0_evaluator.deploy import track_a_bootstrap_runner as runner_module
from services.p5_r0_evaluator.deploy.track_a_bootstrap_runner import (
    APPROVAL_018_CHILD_APPROVAL_PATH,
    APPROVAL_018_REQUEST_DIGEST,
    APPROVAL_018_REQUEST_PATH,
    ATTEMPT_ID,
    BootstrapRunnerError,
    CHILD_APPROVAL_PATH,
    ReviewedBootstrapRunner,
    _load_canonical_request,
    _validate_child_approval_artifact,
    _validate_request_shape,
    prepare_bootstrap,
)


@pytest.fixture(autouse=True)
def _fixed_verifier_clock(monkeypatch):
    monkeypatch.setattr(runner_module, "_verifier_now", lambda: 1_800_000_000)


def _read_request() -> dict:
    return json.loads(APPROVAL_018_REQUEST_PATH.read_text())


def test_approval_018_loader_accepts_exact_packet_and_child_path():
    request = _load_canonical_request(APPROVAL_018_REQUEST_PATH)

    assert request["request_digest"] == APPROVAL_018_REQUEST_DIGEST
    assert request["approval"]["approval_id"] == "P5-MASTER-001/APPROVAL-018"
    assert request["approval"]["dispatch_id"] == "P5-MASTER-001/DISPATCH-077"
    assert request["child_approval"]["path"] == str(
        APPROVAL_018_CHILD_APPROVAL_PATH.relative_to(runner_module.REPOSITORY_ROOT)
    )
    assert APPROVAL_018_CHILD_APPROVAL_PATH.is_file()
    assert CHILD_APPROVAL_PATH == str(APPROVAL_018_CHILD_APPROVAL_PATH)


def test_runner_rejects_historical_packet_before_loader_or_launcher(monkeypatch):
    calls: list[str] = []
    monkeypatch.setattr(
        runner_module,
        "_load_canonical_request",
        lambda _path: calls.append("loader") or _read_request(),
    )
    launcher_calls: list[str] = []
    monkeypatch.setattr(
        runner_module,
        "ReviewedConfidentialSpaceAdapterFactory",
        lambda: launcher_calls.append("factory"),
    )

    with pytest.raises(BootstrapRunnerError, match="packet path"):
        ReviewedBootstrapRunner().run(
            mode="validate",
            request_path=runner_module.HISTORICAL_REQUEST,
            bindings=None,  # type: ignore[arg-type]
            child_approval=None,  # type: ignore[arg-type]
        )

    assert calls == []
    assert launcher_calls == []


def test_altered_packet_digest_is_rejected_before_bindings_or_launcher():
    request = _read_request()
    request["classification"] = "historical-packet"

    with pytest.raises(BootstrapRunnerError, match="request digest"):
        _validate_request_shape(request)


def test_historical_approval_identity_is_rejected_even_if_digest_is_recomputed():
    request = _read_request()
    request["approval"] = dict(request["approval"])
    request["approval"]["approval_id"] = "P5-MASTER-001/APPROVAL-016"
    request["request_digest"] = digest(
        {key: value for key, value in request.items() if key != "request_digest"}
    )

    with pytest.raises(BootstrapRunnerError, match="identity"):
        _validate_request_shape(request)


def test_child_approval_path_mismatch_is_rejected_even_if_packet_is_rehashed():
    request = _read_request()
    request["child_approval"] = dict(request["child_approval"])
    request["child_approval"]["path"] = "services/p5_r0_evaluator/deploy/old-child-approval.json"
    request["request_digest"] = digest(
        {key: value for key, value in request.items() if key != "request_digest"}
    )

    with pytest.raises(BootstrapRunnerError, match="child approval path"):
        _validate_request_shape(request)


def test_altered_child_approval_artifact_is_rejected_after_rehash():
    child = json.loads(APPROVAL_018_CHILD_APPROVAL_PATH.read_text())
    child["request_digest"] = digest("different-request")
    child["artifact_digest"] = digest(
        {key: value for key, value in child.items() if key != "artifact_digest"}
    )

    with pytest.raises(BootstrapRunnerError, match="request digest"):
        _validate_child_approval_artifact(child)


def test_missing_binding_objects_fail_closed_with_typed_error():
    request = _load_canonical_request()

    with pytest.raises(BootstrapRunnerError, match="bindings|required|preflight") as exc_info:
        prepare_bootstrap(
            request,
            bindings=None,  # type: ignore[arg-type]
            child_approval=None,  # type: ignore[arg-type]
        )

    assert not isinstance(exc_info.value.__cause__, AttributeError)


def test_missing_nested_binding_objects_fail_closed_with_typed_error():
    request = _load_canonical_request()
    with pytest.raises(BootstrapRunnerError, match="bindings|required|preflight"):
        prepare_bootstrap(
            request,
            bindings=object(),  # type: ignore[arg-type]
            child_approval=None,  # type: ignore[arg-type]
        )


def test_validate_does_not_construct_factory_or_call_launcher_on_blocked_packet(monkeypatch):
    factory_calls: list[str] = []
    launcher_calls: list[str] = []

    class UnexpectedFactory:
        def __init__(self):
            factory_calls.append("factory")

        def build(self, _prepared):
            launcher_calls.append("build")
            raise AssertionError("launcher boundary must not be reached")

    monkeypatch.setattr(runner_module, "ReviewedConfidentialSpaceAdapterFactory", UnexpectedFactory)
    monkeypatch.setattr(runner_module, "LauncherTokenSource", lambda: launcher_calls.append("launcher"))

    with pytest.raises(BootstrapRunnerError, match="bindings|required|preflight"):
        ReviewedBootstrapRunner().run(
            mode="validate",
            bindings=None,  # type: ignore[arg-type]
            child_approval=None,  # type: ignore[arg-type]
        )

    assert factory_calls == []
    assert launcher_calls == []


def test_effectful_mode_requires_local_ledger_after_typed_preflight(monkeypatch):
    monkeypatch.setattr(runner_module, "_load_canonical_request", lambda _path: _read_request())

    with pytest.raises(BootstrapRunnerError, match="bindings|required|preflight"):
        ReviewedBootstrapRunner().run(
            mode="effectful",
            bindings=None,  # type: ignore[arg-type]
            child_approval=None,  # type: ignore[arg-type]
        )

    assert ATTEMPT_ID.endswith("ATTEMPT-001")

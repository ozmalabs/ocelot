"""test_dev_session_migrated — the replayable dev-session state graph.

The session is dev tooling, not agent runtime: it records a development task as
a typed graph and reads the next action from a declarative transition table.
These tests use a temporary root so no real checkout state is touched.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.ocelot_dev_session import (
    DevSession,
    DevSessionError,
    list_sessions,
    load_session,
    load_workflow,
)


def _start(tmp_path: Path, task: str = "demo task",
           max_attempts: int = 3) -> DevSession:
    return DevSession.start(task, max_attempts=max_attempts, root=tmp_path)


def _session_path(tmp_path: Path, session: DevSession) -> Path:
    return tmp_path / "var" / "ocelot_dev_sessions" / f"{session.session_id}.json"


def _prepare_step(tmp_path: Path, *, steps: list[str] | None = None) -> DevSession:
    session = _start(tmp_path)
    session.record("plan", steps=steps or ["one"])
    session.record("step")
    return session


def test_start_orients(tmp_path: Path) -> None:
    session = _start(tmp_path, "fix the stale reply rule")

    state = session.state()
    assert state["ok"] is True
    assert state["status"] == "open"
    assert state["counts"]["Session"] == 1
    assert state["counts"]["Task"] == 1
    assert any(e["type"] == "has_task" for e in state["edges"])
    task = [n for n in state["nodes"] if n["type"] == "Task"][0]
    assert task["title"] == "fix the stale reply rule"
    assert _session_path(tmp_path, session).is_file()

    action = session.next_action()
    assert action["action"] == "orient"
    assert "plan" in action["reason"].lower()
    assert "step_id" not in action


def test_plan_then_plan_step(tmp_path: Path) -> None:
    session = _start(tmp_path)
    plan = session.record("plan", summary="two-part change",
                          steps=["read the rule", "fix the seed"])

    assert plan["type"] == "Plan"
    assert [s["id"] for s in plan["steps"]] == ["ps1", "ps2"]
    assert plan["steps"][1]["title"] == "fix the seed"
    state = session.state()
    assert state["counts"]["Plan"] == 1
    assert any(e["type"] == "has_plan" and e["tgt"] == plan["id"]
               for e in state["edges"])
    assert state["summary"]["plan"]["steps"][0]["title"] == "read the rule"

    action = session.next_action()
    assert action["action"] == "plan_step"
    assert "0/2" in action["reason"]


def test_edit_then_verify_and_attempt_edges(tmp_path: Path) -> None:
    session = _prepare_step(tmp_path)

    action = session.next_action()
    assert action["action"] == "act"
    assert action["step_id"] == session.state()["summary"]["current_step_id"]

    edit = session.record("edit", files=["domains/foo.py"],
                          summary="touch foo")
    assert edit["type"] == "Edit"
    state = session.state()
    attempts = [n for n in state["nodes"] if n["type"] == "Attempt"]
    assert len(attempts) == 1
    assert attempts[0]["n"] == 1
    assert any(e["type"] == "attempt" and e["tgt"] == attempts[0]["id"]
               for e in state["edges"])
    assert any(e["type"] == "edit" and e["tgt"] == edit["id"]
               for e in state["edges"])
    assert any(e["type"] == "has_step" and e["tgt"] == edit["step_id"]
               for e in state["edges"])
    assert edit["attempt_id"] == attempts[0]["id"]

    action = session.next_action()
    assert action["action"] == "verify"
    assert action["step_id"] == edit["step_id"]


def test_failed_verification_diagnoses(tmp_path: Path) -> None:
    session = _prepare_step(tmp_path)
    step = session.state()["summary"]["current_step_id"]
    session.record("edit", files=["domains/foo.py"])
    failed = session.record("verification", passed=False,
                            command="pytest tests/test_foo.py -q",
                            exit_code=1)

    assert failed["type"] == "Verification"
    assert any(e["type"] == "verification" and e["tgt"] == failed["id"]
               for e in session.state()["edges"])
    action = session.next_action()
    assert action["action"] == "diagnose"
    assert action["step_id"] == step
    assert "1/3" in action["reason"]
    with pytest.raises(DevSessionError):
        session.record("edit", files=["domains/foo.py"])

    # An explicit retry opens a new attempt, so the next action is act again.
    attempt = session.record("attempt", summary="try a narrower change")
    assert attempt["n"] == 2
    assert session.next_action()["action"] == "act"

    session.record("edit", files=["domains/foo.py"],
                   summary="second try")
    assert session.next_action()["action"] == "verify"


def test_pass_advances_then_finishes(tmp_path: Path) -> None:
    session = _start(tmp_path)
    session.record("plan", steps=["one", "two"])
    first = session.record("step")
    session.record("edit", files=["domains/foo.py"])
    session.record("verification", passed=True,
                   command="pytest tests/test_foo.py -q", exit_code=0)

    action = session.next_action()
    assert action["action"] == "plan_step"
    assert "two" in action["reason"]
    assert "step_id" not in action

    second = session.record("step")
    assert second["plan_index"] == 2
    assert second["title"] == "two"
    assert any(e["type"] == "next" and e["src"] == first["id"]
               and e["tgt"] == second["id"]
               for e in session.state()["edges"])
    assert session.next_action()["action"] == "act"
    session.record("edit", files=["domains/foo.py"])
    session.record("verification", passed=True)
    assert session.next_action()["action"] == "finish"

    closed = session.finish("completed")
    assert closed["status"] == "closed"
    assert closed["outcome"] == "completed"
    assert any(e["type"] == "decision" for e in closed["edges"])
    assert session.next_action()["action"] == "done"
    with pytest.raises(DevSessionError):
        session.record("edit", files=["domains/foo.py"])


def test_max_attempts_blocks(tmp_path: Path) -> None:
    session = _start(tmp_path, max_attempts=2)
    session.record("plan", steps=["one"])
    session.record("step")

    session.record("edit", files=["domains/foo.py"])
    session.record("verification", passed=False)
    assert session.next_action()["action"] == "diagnose"

    session.record("attempt", summary="retry")
    session.record("edit", files=["domains/foo.py"])
    session.record("verification", passed=False)
    action = session.next_action()
    assert action["action"] == "blocked"
    assert "all 2 attempts" in action["reason"]
    assert action["step_id"] == session.state()["summary"]["current_step_id"]
    assert session.state()["summary"]["failed_attempts"] == 2
    assert session.state()["summary"]["current_step_status"] == "blocked"

    # The cap is mechanical: another edit is refused, not silently accepted.
    with pytest.raises(DevSessionError):
        session.record("edit", files=["domains/foo.py"])


def test_persistence_reload_is_stable(tmp_path: Path) -> None:
    session = _start(tmp_path)
    session.record("plan", steps=["one", "two"])
    step = session.record("step")
    session.record("edit", files=["domains/foo.py"])
    session.record("verification", passed=False)

    path = _session_path(tmp_path, session)
    assert path.is_file()
    assert not list(path.parent.glob(".*.tmp"))

    before = session.state()
    reloaded = load_session(session.session_id, root=tmp_path)
    assert reloaded.session_id == session.session_id
    assert reloaded.state()["nodes"] == before["nodes"]
    assert reloaded.state()["edges"] == before["edges"]
    assert reloaded.next_action() == session.next_action()

    new_attempt = reloaded.record("attempt", summary="resume after reload")
    old_ids = {n["id"] for n in before["nodes"]}
    assert new_attempt["id"] not in old_ids

    again = load_session(session.session_id + ".json", root=tmp_path)
    assert [n["id"] for n in again.state()["nodes"]] == \
        [n["id"] for n in reloaded.state()["nodes"]]
    assert again.next_action() == reloaded.next_action()
    json.dumps(again.state())  # every stored value is plain JSON
    assert again.state()["summary"]["current_step_id"] == step["id"]


def test_list_sessions(tmp_path: Path) -> None:
    first = _start(tmp_path, "alpha")
    second = _start(tmp_path, "beta")
    first.finish("completed")

    items = list_sessions(root=tmp_path)
    by_id = {item["session_id"]: item for item in items}
    assert set(by_id) == {first.session_id, second.session_id}
    assert by_id[first.session_id]["ok"] is True
    assert by_id[first.session_id]["status"] == "closed"
    assert by_id[first.session_id]["outcome"] == "completed"
    assert by_id[second.session_id]["status"] == "open"
    assert by_id[second.session_id]["task"] == "beta"
    assert all(item["ok"] for item in items)
    assert list_sessions(root=tmp_path / "empty") == []


def test_unknown_transition_is_honest(tmp_path: Path) -> None:
    session = _start(tmp_path)
    path = _session_path(tmp_path, session)
    raw = json.loads(path.read_text(encoding="utf-8"))
    raw["status"] = "mystery"
    path.write_text(json.dumps(raw), encoding="utf-8")

    loaded = load_session(session.session_id, root=tmp_path)
    action = loaded.next_action()
    assert action["action"] == "blocked"
    assert "unknown session status" in action["reason"].lower()
    with pytest.raises(DevSessionError):
        loaded.record("plan", steps=["one"])

    with pytest.raises(DevSessionError):
        session.record("nonsense")


def test_evaluator_fallback_is_honest(tmp_path: Path) -> None:
    session = _start(tmp_path)
    workflow = json.loads(json.dumps(load_workflow()))
    workflow["rules"] = [{
        "id": "never_matches",
        "when": {"plan_count": {"gt": 999}},
        "action": "orient",
        "reason": "this rule cannot match",
        "include_step": False,
    }]
    detached = DevSession(session.data, tmp_path, workflow=workflow)
    action = detached.next_action()
    assert action["action"] == "blocked"
    assert "unknown transition" in action["reason"]


def test_human_gate_and_workflow_shape(tmp_path: Path) -> None:
    session = _start(tmp_path)
    session.record("decision", choice="wait", summary="needs a human")
    assert session.next_action()["action"] == "wait"

    session.record("decision", choice="resume", summary="human approved")
    assert session.next_action()["action"] == "orient"

    workflow = load_workflow()
    assert workflow["version"] == 1
    assert {"orient", "plan_step", "act", "verify", "diagnose",
            "blocked", "finish"} <= set(workflow["actions"])
    assert workflow["fallback"]["action"] == "blocked"
    assert {rule["id"] for rule in workflow["rules"]} >= {
        "orient", "plan_step", "act", "verify", "diagnose", "blocked",
        "more_steps", "finish",
    }

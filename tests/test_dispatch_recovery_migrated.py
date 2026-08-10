"""Wave 6 gate: DISPATCH RECOVERY — a restarted dispatcher recovers its
children from the GRAPH, not from the lost in-memory cache.

`domains/experiment_dispatch.py`'s `_INFLIGHT` dict is host bookkeeping only;
a dispatcher restarted in a fresh process loses it (documented). Since Wave 6:

  * `_spawn` persists `child_pid` + `result_path` onto the Experiment node
    (mechanical attrs, graph state);
  * `scan_and_dispatch` has a recovery branch for an Experiment left
    `running` with no `_INFLIGHT` entry: ingest `result.json` once the child
    finished; keep waiting while the pid is alive; mark a dead-with-no-result
    child `failed` with an "orphaned" error.

Simulated here exactly as prescribed: spawn a real child, then CLEAR
`_INFLIGHT` (that IS the restart — the graph is all that survives one).
"""
from __future__ import annotations

import os
import subprocess
import sys
import time

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "scripts"))

from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds

from domains.experiment_dispatch import (            # noqa: E402
    scan_and_dispatch, mint_experiment, _INFLIGHT, _pid_alive)


@pytest.fixture()
def agent():
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    return a


def _dead_pid() -> int:
    p = subprocess.Popen([sys.executable, "-c", "pass"])
    p.wait()
    return p.pid


def test_pid_alive_probe():
    assert _pid_alive(os.getpid()) is True
    assert _pid_alive(0) is False and _pid_alive(-1) is False
    assert _pid_alive(_dead_pid()) is False


def test_restarted_dispatcher_recovers_finished_child(agent, tmp_path):
    # a real corpus so the conversation child has something to replay
    assert (agent.converse("Hello.", speech_act="greeting") or "").strip()
    assert (agent.converse("What are you?", speech_act="question") or "").strip()

    exp = mint_experiment(agent, "recovery probe (no-op delta)", "conversation")
    _INFLIGHT.clear()
    scan_and_dispatch(agent, str(tmp_path / "runs"))
    at = agent.s.node(exp)["attrs"]
    assert at.get("status") == "running"
    # spawn persisted the recovery bookkeeping into the GRAPH
    assert int(at.get("child_pid") or 0) > 0
    assert str(at.get("result_path") or "").endswith("result.json")
    run_dir = at.get("run_dir")

    # THE RESTART: the in-memory cache is gone; only the graph remains.
    _INFLIGHT.clear()

    t0 = time.time()
    while time.time() - t0 < 300.0:
        scan_and_dispatch(agent, str(tmp_path / "runs"))   # recovery branch each call
        status = agent.s.node(exp)["attrs"].get("status")
        if status not in ("requested", "running"):
            break
        time.sleep(0.5)
    at = agent.s.node(exp)["attrs"]
    assert at.get("status") == "done", at
    assert at.get("run_dir") == run_dir, "recovery must not re-spawn into a new run_dir"
    runs = [r for r in agent.inner.neighbours(exp, "produced") if agent.s.has_node(r)]
    assert len(runs) == 1, "exactly one Run ingested (no double-ingest, no re-spawn)"
    ra = agent.s.node(runs[0])["attrs"]
    assert ra["status"] == "done" and int(ra["frames"]) == 2

    # idempotent: a further scan does nothing more to this experiment
    scan_and_dispatch(agent, str(tmp_path / "runs"))
    assert len([r for r in agent.inner.neighbours(exp, "produced")
                if agent.s.has_node(r)]) == 1


def test_orphaned_running_experiment_marked_failed(tmp_path):
    # a light agent suffices: the recovery branch only reads Experiment attrs
    a = WorldAdapter(seeds=())
    run_dir = tmp_path / "orphan-run"
    run_dir.mkdir()
    exp = a.s.add_node("Experiment", {
        "hypothesis": "orphan probe", "game": "conversation",
        "status": "running", "run_dir": str(run_dir),
        "child_pid": _dead_pid(),
        "result_path": str(run_dir / "result.json"),
    })
    scan_and_dispatch(a, str(tmp_path / "runs"))
    at = a.s.node(exp)["attrs"]
    assert at.get("status") == "failed", at
    assert "orphaned" in str(at.get("error") or "")
    # the Experiment -produced-> Run contract holds even for the orphan
    runs = [r for r in a.inner.neighbours(exp, "produced") if a.s.has_node(r)]
    assert len(runs) == 1 and a.s.node(runs[0])["attrs"]["status"] == "failed"


def test_alive_recovered_child_is_waited_on_not_reingested(tmp_path):
    """While the (recovered) pid is alive and result.json is absent, the scan
    must neither fail the experiment nor ingest anything — it waits."""
    a = WorldAdapter(seeds=())
    run_dir = tmp_path / "alive-run"
    run_dir.mkdir()
    p = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"])
    try:
        exp = a.s.add_node("Experiment", {
            "hypothesis": "alive probe", "game": "conversation",
            "status": "running", "run_dir": str(run_dir), "child_pid": p.pid,
        })
        scan_and_dispatch(a, str(tmp_path / "runs"))
        at = a.s.node(exp)["attrs"]
        assert at.get("status") == "running", "an alive child must be left alone"
        assert not list(a.inner.neighbours(exp, "produced"))
    finally:
        p.kill()
        p.wait()

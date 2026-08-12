"""test_experiment_dispatch — end-to-end (offline) exercise of the experiment-dispatch
MECHANISM: mint an Experiment, dispatch it as a child process, and verify the child's
result lands back in the parent graph as Run + RunObservation nodes, per the node
vocabulary in domains/experiment_dispatch.py's docstring.

Slow (boots two full seed-loaded agents + spawns two subprocesses that each boot their
own agent) — marked `slow`. Uses `arc3_env`'s OFFLINE `navigate` game (no ARC_API_KEY
needed, no network): the live env needs a key this environment doesn't have.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
from domains.experiment_dispatch import mint_experiment, scan_and_dispatch, _INFLIGHT

# OPTIONAL DEPENDENCIES (red-test triage 2026-08-12): absent 'cv2' is a SKIP with a
# named reason on the tests that need it, never a red. See tests/optional_deps.py.
from optional_deps import requires as _requires_optional  # noqa: E402


pytestmark = pytest.mark.slow

TIMEOUT_S = 90


def _boot_parent():
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    return agent


def _wait_for(agent, exp, runs_dir, timeout=TIMEOUT_S):
    """Poll scan_and_dispatch (the real, non-blocking API) until `exp`'s status
    leaves requested/running, or fail on timeout. Mirrors how a real host loop
    would drive this (e.g. call scan_and_dispatch once per tick)."""
    t0 = time.time()
    while time.time() - t0 < timeout:
        scan_and_dispatch(agent, runs_dir)
        status = agent.s.node(exp)["attrs"].get("status")
        if status not in ("requested", "running"):
            return status
        time.sleep(0.5)
    raise TimeoutError(f"experiment {exp} still {agent.s.node(exp)['attrs'].get('status')!r} after {timeout}s")


@pytest.fixture(autouse=True)
def _clear_inflight():
    _INFLIGHT.clear()
    yield
    _INFLIGHT.clear()


def test_scan_and_dispatch_is_non_blocking(tmp_path):
    agent = _boot_parent()
    runs_dir = tmp_path / "runs"
    exp = mint_experiment(agent, "does a trivial delta run cleanly?", "navigate",
                          skip_seeds=[], add_rules=[])
    assert agent.s.node(exp)["attrs"]["status"] == "requested"

    t0 = time.time()
    touched = scan_and_dispatch(agent, runs_dir)
    elapsed = time.time() - t0
    assert elapsed < 5.0, f"scan_and_dispatch blocked for {elapsed:.1f}s — should return immediately"
    assert len(touched) == 1
    assert agent.s.node(exp)["attrs"]["status"] == "running"
    run_dir = Path(agent.s.node(exp)["attrs"]["run_dir"])
    assert run_dir.exists()
    assert (run_dir / "parent_snapshot.json").exists()
    assert (run_dir / "delta.json").exists()

    # calling again while the child is still running must not re-spawn or block
    t0 = time.time()
    scan_and_dispatch(agent, runs_dir)
    assert time.time() - t0 < 5.0
    assert len(_INFLIGHT) == 1

    status = _wait_for(agent, exp, runs_dir)
    assert status == "done", f"experiment ended {status!r}"


def test_trivial_delta_end_to_end(tmp_path):
    """skip_seeds=[] -> SNAPSHOT boot mode. Verifies Run + RunObservation land in the
    PARENT graph with the attrs the vocabulary contract promises, and that the child's
    trace.jsonl / final_graph.json / result.json all exist."""
    agent = _boot_parent()
    runs_dir = tmp_path / "runs"
    exp = mint_experiment(agent, "trivial delta, offline navigate, 5 actions", "navigate",
                          skip_seeds=[], add_rules=[])
    scan_and_dispatch(agent, runs_dir)
    status = _wait_for(agent, exp, runs_dir)
    assert status == "done"

    run_dir = Path(agent.s.node(exp)["attrs"]["run_dir"])
    result = json.loads((run_dir / "result.json").read_text())
    assert result["status"] == "done", result
    assert result["boot_mode"] == "snapshot"
    assert (run_dir / "trace.jsonl").exists()
    assert (run_dir / "final_graph.json").exists()
    trace_lines = [json.loads(l) for l in (run_dir / "trace.jsonl").read_text().splitlines() if l.strip()]
    assert len(trace_lines) == result["frames"] > 0
    for rec in trace_lines:
        assert set(rec.keys()) == {"frame", "action", "score", "reasoning", "self_report"}

    S, I = agent.s, agent.inner
    runs = [r for r in I.neighbours(exp, "produced") if I.has_node(r)]
    assert len(runs) == 1, runs
    run = runs[0]
    ra = S.node(run)["attrs"]
    assert ra["game"] == "navigate"
    assert ra["status"] == "done"
    assert int(ra["frames"]) == result["frames"]

    obs = [o for o in I.neighbours(run, "observed") if I.has_node(o)]
    assert len(obs) == len(trace_lines)
    frames_seen = sorted(int(S.node(o)["attrs"]["frame"]) for o in obs)
    assert frames_seen == sorted(int(r["frame"]) for r in trace_lines)
    for o in obs:
        a = S.node(o)["attrs"]
        assert "action" in a and "reasoning" in a and "self_report" in a and "score" in a


@_requires_optional('cv2')
def test_seed_delta_skip_seeds_forces_fresh_boot(tmp_path):
    """skip_seeds non-empty -> FRESH+SKIP boot mode (documented: a snapshot can't unload a
    seed). Skips an unrelated seed (astronomy_foundation) so the episode itself is
    unaffected; verifies the mechanism completes and reports the fresh+skip boot mode."""
    agent = _boot_parent()
    runs_dir = tmp_path / "runs"
    exp = mint_experiment(agent, "withhold astronomy_foundation, does play still work?", "navigate",
                          skip_seeds=["astronomy_foundation"], add_rules=[])
    scan_and_dispatch(agent, runs_dir)
    status = _wait_for(agent, exp, runs_dir)

    run_dir = Path(agent.s.node(exp)["attrs"]["run_dir"])
    result = json.loads((run_dir / "result.json").read_text())
    assert result.get("boot_mode") == "fresh+skip", result
    assert status == "done", result

    S, I = agent.s, agent.inner
    runs = [r for r in I.neighbours(exp, "produced") if I.has_node(r)]
    assert len(runs) == 1

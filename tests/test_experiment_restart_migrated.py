"""Restart failed experiments — mechanical re-queue + dispatch."""
from __future__ import annotations

import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from substrate.world_adapter import WorldAdapter
from domains.experiment_dispatch import restart_experiment, scan_and_dispatch, _INFLIGHT


@pytest.fixture()
def agent():
    return WorldAdapter(seeds=())


def test_restart_failed_experiment(agent, tmp_path):
    _INFLIGHT.clear()
    exp = agent.s.add_node("Experiment", {
        "status": "failed", "game": "navigate", "hypothesis": "test", "error": "boom",
    })
    exp_id = exp.value if hasattr(exp, "value") else exp
    result = restart_experiment(agent, str(exp_id))
    assert result["ok"]
    assert result["status"] == "requested"
    assert agent.s.node(exp)["attrs"]["status"] == "requested"
    touched = scan_and_dispatch(agent, str(tmp_path))
    assert touched, "dispatch should spawn child for re-queued experiment"


def test_restart_rejects_running(agent):
    exp = agent.s.add_node("Experiment", {"status": "running", "game": "navigate"})
    exp_id = exp.value if hasattr(exp, "value") else exp
    result = restart_experiment(agent, str(exp_id))
    assert not result["ok"]

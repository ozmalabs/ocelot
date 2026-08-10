"""Experiment session detail includes failure diagnostics."""
from __future__ import annotations

import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "scripts"))

from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds

import jabberwock_daemon as jbd


@pytest.fixture()
def agent():
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    return a


def test_session_detail_reads_failed_log(agent, tmp_path):
    run_dir = tmp_path / "99-0"
    run_dir.mkdir()
    (run_dir / "log.txt").write_text("ModuleNotFoundError: No module named 'requests'\n")
    (run_dir / "delta.json").write_text('{"skip_seeds":[],"add_rules":[],"remove_rules":[]}')
    exp = agent.s.add_node("Experiment", {
        "status": "failed", "game": "navigate", "hypothesis": "test", "run_dir": str(run_dir),
    })
    run = agent.s.add_node("Run", {"status": "failed", "frames": 0, "score": 0})
    agent.inner.add_edge_unchecked(exp, "produced", run)
    axis = agent.s.add_node("CapabilityAxis", {
        "capability_keys": ["promoted_self_concern_42"], "is_axis": 1.0,
    })
    agent.inner.add_edge_unchecked(axis, "tested_by", exp)
    session, trace = jbd.session_detail(agent, str(exp.value))
    assert session["error"] and "requests" in session["error"]
    assert session["self_concern_id"] == 42
    assert session["delta"]["skip_seeds"] == []
    assert trace == []

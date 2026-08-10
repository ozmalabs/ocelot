"""test_autonomous_cycle — the AUTONOMY GATE, as a regression test.

Wraps `scripts/autonomous_improvement_gate.py`'s `run_gate` (see that module's
docstring for the full account of what this proves and how). Boots the agent
exactly as `scripts/jabberwock_daemon.py` boots it (`--seeds full`, fresh
checkpoint dir), then runs a bounded loop of `tick()` calls interleaved with
ONLY the daemon's own mechanical hooks (`_world_tick`, `_concern_tick`,
`_dispatch_tick`, `_close_tick`) -- no `induce_concern`/`ground_concern`/
hand-minted Experiment call happens anywhere in this test after boot.

Slow (boots a full seed-loaded agent, plays a real offline-ARC episode, and
spawns real child processes via `domains.experiment_dispatch.scan_and_dispatch`)
-- marked `slow`, mirroring `tests/test_experiment_dispatch.py` /
`tests/test_experiment_composer.py`'s own pattern. Uses `arc3_env`'s OFFLINE
`navigate` game throughout (no ARC_API_KEY needed, no network).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
for p in (str(ROOT), str(ROOT / "runners" / "dsl" / "python"), str(ROOT / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

import autonomous_improvement_gate as gate            # noqa: E402
from domains.experiment_dispatch import _INFLIGHT      # noqa: E402

pytestmark = pytest.mark.slow

_CONCLUSIONS_SEED = str(ROOT / "seeds" / "experiment_conclusions.json")
_STANDING_CONCERN_SEED = str(ROOT / "seeds" / "standing_self_improvement_concern.json")


# ---------------------------------------------------------------------------
# guard: close_experiment_loop's teach() persists REAL data into a seed file
# this test suite doesn't own (same shape as tests/test_self_delta.py's own
# `_experiment_conclusions_seed_guard`) -- the gate genuinely closes the loop,
# which genuinely calls teach(), which genuinely appends to this file; snapshot
# + restore its exact bytes so a full-suite run leaves no residue. The standing
# -concern seed itself is NOT mutated by this test (StandingConcern.status only
# changes on the in-memory `WorldAdapter` this test boots, never on disk), but
# it's guarded too out of the same caution the task brief calls for.
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def _seed_guard():
    paths = [_CONCLUSIONS_SEED, _STANDING_CONCERN_SEED]
    before = {}
    for p in paths:
        before[p] = open(p).read() if os.path.exists(p) else None
    try:
        yield
    finally:
        for p in paths:
            if before[p] is not None:
                with open(p, "w") as f:
                    f.write(before[p])
            elif os.path.exists(p):
                os.unlink(p)


def test_autonomous_self_improvement_cycle_closes_without_a_human(tmp_path):
    """The full chain -- StandingConcern (seed data) -> induce_concern/ground_concern
    (_concern_tick) -> a genuinely-minted CapabilityAxis -> the agent's OWN
    author_experiment_from_residual_* rule mints an Experiment -> _dispatch_tick
    spawns + ingests a real child -> the agent's OWN judge_experiment_outcome_*
    rule writes an outcome -> close_experiment_loop teaches the verdict (and
    adopts if genuinely supported) -- closes with ZERO calls to induce_concern,
    ground_concern, or any hand-minted Experiment/CapabilityAxis/Goal after boot.
    An inconclusive/refuted-but-taught outcome passes just as a supported-and-
    adopted one does (see gate module docstring): the assertion is that the
    cycle CLOSED autonomously, not that it improved on cue."""
    _INFLIGHT.clear()
    runs_dir = tmp_path / "runs"
    ckpt_dir = tmp_path / "ckpt"
    runs_dir.mkdir()
    ckpt_dir.mkdir()

    rc = gate.run_gate(
        max_ticks=4000, wall_budget_s=240.0,
        world_every=20, concern_every=5, dispatch_every=1, close_every=5,
        world_actions=6, runs_dir=runs_dir, ckpt_dir=ckpt_dir, seeds="full")

    assert rc == 0, "autonomy gate FAILED -- see the [FAIL] lines in captured output for the exact link"

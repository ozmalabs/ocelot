"""Frame-layer self-introspection + rust-runner fallback — slice 4c (partial),
on the seed-booted WorldAdapter.

The agent answers about its OWN engine through the same Frame layer: instrumented
paths (recognise_frame) self-profile via _record_op onto the agent node; the
aggregates surface as runtime_capabilities; the performance_analysis Frames route
"mean cost of <op>" / "call count of <op>" through answer_within. The autonomous
impasse-resolution reflex is graph-resident. The Rust-runner delegation is opt-in
and degrades gracefully when the .so isn't built.
"""
from __future__ import annotations

import pytest

pytest.importorskip("substrate_rs")

from domains.reason import answer_within
from substrate.boot_core import CORE_SEEDS
from substrate.world_adapter import WorldAdapter

_FRAMES = CORE_SEEDS + ("frames",)


def _agent():
    return WorldAdapter(seeds=_FRAMES)


def test_auto_resolve_reflex_lives_in_the_graph():
    a = _agent()
    rid = a.reflex("auto_resolve_impasse")
    assert rid is not None
    assert a.s.node(rid)["attrs"]["response"] == "resolve_impasse"


def test_agent_introspects_its_own_engine_through_the_frame_layer():
    a = _agent()
    for q in ("What is the largest prime divisor of 8139881",
              "What is the determinant of M", "Is 17 prime",
              "What is the gcd of 12 and 18"):
        try:
            answer_within(q, {}, 1e8, agent=a)
        except Exception:
            pass
    attrs = a.s.node(a.agent)["attrs"]
    assert "op_recognise_frame_count" in attrs
    assert int(attrs["op_recognise_frame_count"]) >= 4
    mean, _, strategy = answer_within(
        "What is the mean cost of recognise_frame", {}, 1e8, agent=a)
    assert isinstance(mean, float) and mean > 0
    assert strategy == "default"
    count, _, strategy = answer_within(
        "What is the call count of recognise_frame", {}, 1e8, agent=a)
    assert isinstance(count, int) and count >= 5
    assert strategy == "default"


def test_introspection_frames_live_in_performance_analysis_mt():
    a = _agent()
    perf = a.microtheory("performance_analysis")
    for f_name in ("op_mean_cost_inquiry", "op_count_inquiry", "op_total_cost_inquiry"):
        fid = a.frame(f_name)
        assert fid is not None, f"missing {f_name}"
        assert perf in set(a.inner.neighbours(fid, "holds_in"))


def test_master_tick_resolves_impasses_via_reflex():
    from domains.reason import UnknownShape
    a = _agent()
    calls = []

    def self_teacher(q):
        calls.append(q)
        if "alpha" in q:
            return {"answer": "1", "learn": [{"phrase": "alpha",
                    "binding_pattern": "function_of_subject"}]}
        if "beta" in q:
            return {"answer": "2", "learn": [{"phrase": "beta",
                    "binding_pattern": "function_of_subject"}]}
        return None

    a.set_self_teacher(self_teacher)
    a._self_teacher = None        # accumulate impasses without resolving them
    for q in ("Compute the alpha of M.", "Compute the beta of M."):
        with pytest.raises(UnknownShape):
            answer_within(q, {}, 1e8, agent=a)
    assert len(a.unresolved_impasses()) == 2

    a.set_self_teacher(self_teacher)
    a.master_tick()                       # spawn for impasse 1
    a.master_tick()                       # drain + spawn for impasse 2
    a.drain_all_taught_threads()          # block until both teacher threads land
    a._drain_completed_teacher_threads()
    assert len(a.unresolved_impasses()) == 0
    assert len(calls) == 2
    assert a.frame("taught_alpha_inquiry") is not None
    assert a.frame("taught_beta_inquiry") is not None


def test_master_tick_does_not_block_on_teacher():
    import time
    from domains.reason import UnknownShape
    a = _agent()
    a._self_teacher = None
    with pytest.raises(UnknownShape):
        answer_within("Compute the gamma of M.", {}, 1e8, agent=a)

    def slow_teacher(q):
        time.sleep(0.20)
        return {"answer": "X", "learn": [{"phrase": "gamma",
                "binding_pattern": "function_of_subject"}]}

    a.set_self_teacher(slow_teacher)
    t0 = time.monotonic()
    a.master_tick()
    assert time.monotonic() - t0 < 0.10, "master_tick blocked on the teacher"
    assert len(a.unresolved_impasses()) == 1
    a.drain_all_taught_threads(timeout=1.0)
    assert len(a.unresolved_impasses()) == 0


def test_use_rust_runner_returns_false_when_so_missing(monkeypatch):
    from domains import rust_runner
    monkeypatch.setattr(rust_runner, "is_available", lambda: False)
    a = _agent()
    assert a.use_rust_runner() is False
    assert a._rust_runner_enabled is False
    fid, _, _ = a.recognise_frame("What is the largest prime divisor of 8139881")
    assert fid is not None


def test_rust_runner_delegation_when_so_available():
    from domains import rust_runner
    if not rust_runner.is_available():
        pytest.skip("librecognise_frame.so not built")
    a_py, a_rs = _agent(), _agent()
    assert a_rs.use_rust_runner() is True
    for q in ("What is the largest prime divisor of 8139881", "Is 17 prime",
              "Compute the gcd of 48 and 18", "What is the determinant of M",
              "Compute the reduced 12-th dimensional Spin bordism of G2."):
        py_fid, py_slots, _ = a_py.recognise_frame(q)
        rs_fid, rs_slots, _ = a_rs.recognise_frame(q)
        assert (py_fid is None) == (rs_fid is None), q
        if py_fid is not None:
            assert py_slots == rs_slots, q

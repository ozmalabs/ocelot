"""Funded regular-window bridge into the existing TimeInfer seed."""
import json

from substrate.boot_core import CORE_SEEDS
from substrate.world_adapter import WorldAdapter
from scripts.gen_temporal_escalation_seed import OUT, build_seed


BASE = [["cell", 0, 0, "red"], ["cell", 1, 0, "red"],
        ["cell", 2, 0, "red"], ["cell", 2, 1, "red"]]
DT = ["pred", "coord:r", "coord:c", "val"]


def _translate(frames=5):
    out = [BASE]
    for ix in range(1, frames):
        out.append([["cell", row[1] + ix, row[2], row[3]] for row in BASE])
    return out


def _boot(enabled=True, remaining=4.0):
    seeds = CORE_SEEDS + ("thinking_budget", "time_axis", "temporal_escalation")
    a = WorldAdapter(seeds=seeds)
    pol = a.s.nodes("TemporalEscalationPolicy")[0]
    budget = a.s.nodes("ThinkingBudget")[0]
    a.s.set_attr(pol, "enabled", 1.0 if enabled else 0.0)
    a.s.set_attr(budget, "enabled", 1.0)
    a.s.set_attr(budget, "remaining", remaining)
    a.s.set_attr(budget, "refill_per_epoch", 0.0)
    a.s.set_attr(budget, "last_refill_epoch", 1.0)
    a.s.set_attr(a.agent, "time_infer_enabled", 0.0)
    modes = a.s.nodes("NetworkModeState")
    if not modes:
        mode = a.s.add_node("NetworkModeState", {"epoch": 2.0, "mode": "awake"})
        a.inner.add_edge_unchecked(a.agent, "has_network_mode_state", mode)
    else:
        for mode in modes:
            a.s.set_attr(mode, "epoch", 2.0)
    a.s.add_node("ShapeSignature", {"name": "base_L", "signature": json.dumps(BASE),
                  "kind": "faculty", "faculty": "base_L", "dim_types": DT})
    return a, budget


def _window(a, window_id="w1", *, frames=None, regular=True, epoch=2):
    source = a.s.add_node("Observation", {"key": f"source:{window_id}", "status": "decoded",
                         "dim_checked": 1, "dim_explained": 0, "decoded_epoch": epoch})
    a.inner.add_edge_unchecked(a.agent, "observed", source)
    win = a.s.add_node("TemporalSequenceWindow", {
        "window_id": window_id, "owner_id": "agent-root", "source_epoch": epoch,
        "first_event_id": f"event:{window_id}:0", "last_event_id": f"event:{window_id}:n",
        "frames": _translate() if frames is None else frames, "dim_types": DT,
        "regular_sampling": regular, "status": "ready",
    })
    a.inner.add_edge_unchecked(a.agent, "has_temporal_window", win)
    a.inner.add_edge_unchecked(win, "escalates_observation", source)
    return win, source


def _tick(a):
    for _ in range(40):
        if not a.inner.run_rules(10000):
            break
    else:
        raise AssertionError("temporal escalation did not reach a fixpoint")


def test_acceleration_infers_and_predicts_only_after_funding():
    a, budget = _boot()
    win, source = _window(a)
    _tick(a)
    assert a.s.node(source)["attrs"]["dim_explained"] == 0
    motion = a.s.nodes("Observation")
    bridge = next(n for n in motion if a.s.node(n)["attrs"].get("temporal_bridge"))
    assert a.s.node(bridge)["attrs"]["status"] == "time_inferred"
    assert a.s.node(bridge)["attrs"].get("predicted") is not None
    req = a.s.nodes("ThinkingBudgetRequest")[0]
    assert a.s.node(req)["attrs"]["status"] == "consumed"
    assert a.s.node(req)["attrs"]["debited_epoch"] == 2.0
    assert a.s.node(budget)["attrs"]["remaining"] == 3.0
    lease = a.s.nodes("TemporalEscalationLease")[0]
    assert a.s.node(lease)["attrs"]["status"] == "restored"
    assert a.s.node(a.agent)["attrs"]["time_infer_enabled"] == 0.0
    assert a.s.node(win)["attrs"]["status"] == "time_inferred"
    a.close()


def test_disabled_profile_budget_is_not_used_for_temporal_request():
    a, budget = _boot()
    disabled = a.s.add_node("ThinkingBudget", {
        "enabled": 0.0, "remaining": 0.0, "capacity": 0.0,
        "refill_per_epoch": 0.0, "last_refill_epoch": 2.0,
    })
    a.inner.add_edge_unchecked(a.agent, "has_thinking_budget", disabled)
    _window(a)
    _tick(a)
    requests = [node for node in a.s.nodes("ThinkingBudgetRequest")
                if a.s.node(node)["attrs"].get("requester_kind") == "temporal_escalation"]
    assert len(requests) == 1
    assert a.s.neighbours(requests[0], "draws_on_thinking_budget") == [budget]
    assert a.s.node(requests[0])["attrs"]["status"] == "consumed"
    a.close()


def test_no_frames_no_time_rung():
    a, _ = _boot()
    win, _ = _window(a, frames=[])
    _tick(a)
    assert a.s.node(win)["attrs"]["status"] == "insufficient_witness"
    assert a.s.nodes("ThinkingBudgetRequest") == []
    assert not any(a.s.node(n)["attrs"].get("temporal_bridge") for n in a.s.nodes("Observation"))
    a.close()


def test_single_frame_cannot_escalate():
    a, _ = _boot()
    win, _ = _window(a, frames=[BASE])
    _tick(a)
    assert a.s.node(win)["attrs"]["status"] == "insufficient_witness"
    assert a.s.nodes("ThinkingBudgetRequest") == []
    a.close()


def test_dependency_closure_and_generator_reproduction():
    assert json.loads(OUT.read_text()) == build_seed()
    a, _ = _boot(enabled=False)
    assert len(a.s.nodes("TemporalEscalationPolicy")) == 1
    assert a.s.nodes("TemporalSequenceWindow") == []
    a.close()


def test_shuffled_measured_events_are_assembled_by_sequence_index():
    a, _ = _boot()
    source = a.s.add_node("Observation", {
        "key": "orbit-source", "status": "decoded", "dim_checked": 1,
        "dim_explained": 0, "decoded_epoch": 2.0,
    })
    a.inner.add_edge_unchecked(a.agent, "observed", source)
    for index in (2, 0, 3, 1):
        event = a.s.add_node("TemporalFrameEvent", {
            "owner_id": "agent-root", "window_id": "orbit-1", "source_epoch": 2,
            "event_id": f"ev-{index}", "sequence_index": index,
            "timestamp": index * 10.0,
            "frame": [["cell", index, 0, "red"]], "dim_types": DT,
            "status": "observed",
        })
        a.inner.add_edge_unchecked(a.agent, "has_temporal_frame_event", event)
    seal = a.s.add_node("TemporalFrameWindowSeal", {
        "owner_id": "agent-root", "window_id": "orbit-1", "source_epoch": 2,
        "expected_frame_count": 4, "dim_types": DT, "status": "closed",
    })
    a.inner.add_edge_unchecked(a.agent, "has_temporal_frame_window_seal", seal)
    a.inner.add_edge_unchecked(seal, "seals_temporal_observation", source)
    _tick(a)
    win = next(n for n in a.s.nodes("TemporalSequenceWindow")
               if a.s.node(n)["attrs"].get("window_id") == "orbit-1")
    attrs = a.s.node(win)["attrs"]
    assert attrs["event_ids"] == ["ev-0", "ev-1", "ev-2", "ev-3"]
    assert attrs["timestamps"] == [0.0, 10.0, 20.0, 30.0]
    assert attrs["frames"] == [[ ["cell", 0, 0, "red"]],
                                [["cell", 1, 0, "red"]],
                                [["cell", 2, 0, "red"]],
                                [["cell", 3, 0, "red"]]]
    assert attrs["regular_sampling"] in (True, 1.0)
    assert attrs["source_epoch"] == 2
    a.close()


def test_incomplete_sealed_event_window_is_refused_without_partial_frames():
    a, _ = _boot()
    source = a.s.add_node("Observation", {"key": "partial", "dim_checked": 1,
                         "dim_explained": 0, "decoded_epoch": 2.0})
    a.inner.add_edge_unchecked(a.agent, "observed", source)
    for index in range(3):
        event = a.s.add_node("TemporalFrameEvent", {
            "owner_id": "agent-root", "window_id": "partial", "source_epoch": 2,
            "event_id": f"partial-{index}", "sequence_index": index,
            "timestamp": index * 10.0, "frame": [BASE], "dim_types": DT,
            "status": "observed",
        })
        a.inner.add_edge_unchecked(a.agent, "has_temporal_frame_event", event)
    seal = a.s.add_node("TemporalFrameWindowSeal", {
        "owner_id": "agent-root", "window_id": "partial", "source_epoch": 2,
        "expected_frame_count": 4, "dim_types": DT, "status": "closed",
    })
    a.inner.add_edge_unchecked(a.agent, "has_temporal_frame_window_seal", seal)
    a.inner.add_edge_unchecked(seal, "seals_temporal_observation", source)
    _tick(a)
    assert a.s.node(seal)["attrs"]["status"] == "incomplete"
    assert a.s.nodes("TemporalSequenceWindow") == []
    assert a.s.nodes("ThinkingBudgetRequest") == []
    a.close()


def test_irregular_and_oversized_sealed_event_streams_are_refused():
    a, _ = _boot()
    for window_id, count in (("irregular-events", 3), ("large-events", 65)):
        source = a.s.add_node("Observation", {
            "key": f"source:{window_id}", "dim_checked": 1,
            "dim_explained": 0, "decoded_epoch": 2.0,
        })
        a.inner.add_edge_unchecked(a.agent, "observed", source)
        for index in range(count):
            event = a.s.add_node("TemporalFrameEvent", {
                "owner_id": "agent-root", "window_id": window_id, "source_epoch": 2,
                "event_id": f"{window_id}:{index}", "sequence_index": index,
                "timestamp": (index * 10.0) + (1.0 if window_id == "irregular-events" and index == 2 else 0.0),
                "frame": [["cell", index, 0, "red"]], "dim_types": DT,
                "status": "observed",
            })
            a.inner.add_edge_unchecked(a.agent, "has_temporal_frame_event", event)
        seal = a.s.add_node("TemporalFrameWindowSeal", {
            "owner_id": "agent-root", "window_id": window_id, "source_epoch": 2,
            "expected_frame_count": count, "dim_types": DT, "status": "closed",
        })
        a.inner.add_edge_unchecked(a.agent, "has_temporal_frame_window_seal", seal)
        a.inner.add_edge_unchecked(seal, "seals_temporal_observation", source)
    _tick(a)
    seals = {a.s.node(n)["attrs"]["window_id"]: a.s.node(n)["attrs"]["status"]
             for n in a.s.nodes("TemporalFrameWindowSeal")}
    assert seals == {"irregular-events": "closed",
                     "large-events": "unsupported_window_size"}
    assert a.s.nodes("ThinkingBudgetRequest") == []
    windows = {a.s.node(n)["attrs"]["window_id"]: a.s.node(n)["attrs"]["status"]
               for n in a.s.nodes("TemporalSequenceWindow")}
    assert windows == {"irregular-events": "unsupported_irregular"}
    a.close()


def test_irregular_time_refused():
    a, _ = _boot()
    win, _ = _window(a, regular=False)
    _tick(a)
    assert a.s.node(win)["attrs"]["status"] == "unsupported_irregular"
    assert a.s.nodes("ThinkingBudgetRequest") == []
    a.close()


def test_denied_request_does_not_infer():
    a, budget = _boot(remaining=0.0)
    win, _ = _window(a)
    _tick(a)
    req = a.s.nodes("ThinkingBudgetRequest")[0]
    assert a.s.node(req)["attrs"]["status"] == "denied"
    assert a.s.node(budget)["attrs"]["remaining"] == 0.0
    assert not any(a.s.node(n)["attrs"].get("temporal_bridge") for n in a.s.nodes("Observation"))
    assert a.s.node(win)["attrs"]["status"] == "ready"
    a.close()


def test_window_identity_prevents_duplicate_charge():
    a, budget = _boot()
    first, _ = _window(a, "same-window")
    _tick(a)
    second, _ = _window(a, "same-window")
    _tick(a)
    assert len(a.s.nodes("ThinkingBudgetRequest")) == 1
    assert a.s.node(budget)["attrs"]["remaining"] == 3.0
    assert a.s.node(second)["attrs"]["status"] == "ready"
    a.close()


def test_window_growth_is_bounded():
    a, _ = _boot()
    win, _ = _window(a, frames=_translate(65))
    _tick(a)
    assert a.s.nodes("ThinkingBudgetRequest") == []
    assert a.s.nodes("TemporalEscalationLease") == []
    assert a.s.node(win)["attrs"]["status"] == "unsupported_window_size"
    a.close()


def test_approved_request_without_same_epoch_debit_cannot_bypass_budget():
    a, _ = _boot(remaining=0.0)
    win, _ = _window(a)
    _tick(a)
    req = a.s.nodes("ThinkingBudgetRequest")[0]
    a.s.set_attr(req, "status", "approved")
    _tick(a)
    assert not any(a.s.node(n)["attrs"].get("temporal_bridge") for n in a.s.nodes("Observation"))
    assert a.s.nodes("TemporalEscalationLease") == []
    a.close()


def test_shuffled_stream_remains_unexplained_and_restores_lease():
    a, _ = _boot()
    frames = _translate()
    frames = [frames[ix] for ix in (0, 2, 1, 4, 3)]
    win, _ = _window(a, frames=frames)
    _tick(a)
    bridge = next(n for n in a.s.nodes("Observation")
                  if a.s.node(n)["attrs"].get("temporal_bridge"))
    assert a.s.node(bridge)["attrs"]["status"] == "time_none"
    assert a.s.node(win)["attrs"]["status"] == "time_none"
    assert a.s.node(a.agent)["attrs"]["time_infer_enabled"] == 0.0
    assert a.s.node(a.s.nodes("TemporalEscalationLease")[0])["attrs"]["status"] == "restored"
    a.close()


def test_world_adapter_measured_ingestion_is_idempotent_and_requires_explicit_seal():
    a, _budget = _boot(enabled=False)
    source = a.s.add_node("Observation", {
        "key": "adapter-source", "status": "decoded", "dim_checked": 1,
        "dim_explained": 0, "decoded_epoch": 2.0,
    })
    event_ids = []
    for index in range(4):
        event_id = f"adapter-window:{index}"
        result = a.ingest_temporal_frame_event(
            source, window_id="adapter-window", event_id=event_id,
            sequence_index=index, timestamp=index * 10.0,
            frame=_translate(4)[index], dim_types=DT,
            source_epoch=2.0,
            close_window=index == 3,
            expected_frame_count=4 if index == 3 else None,
        )
        event_ids.append(result["event"])
        assert len(a.s.nodes("NetworkModeState")) == 1
        assert a.s.node(a.s.nodes("TemporalEscalationPolicy")[0])["attrs"]["enabled"] == 0.0
        if index == 1:
            replay = a.ingest_temporal_frame_event(
                source, window_id="adapter-window", event_id=event_id,
                sequence_index=index, timestamp=index * 10.0,
                frame=_translate(4)[index], dim_types=DT,
                source_epoch=2.0,
            )
            assert replay["event"] == result["event"]
            try:
                a.ingest_temporal_frame_event(
                    source, window_id="adapter-window", event_id=event_id,
                    sequence_index=index, timestamp=index * 11.0,
                    frame=_translate(4)[index], dim_types=DT,
                    source_epoch=2.0,
                )
            except ValueError as exc:
                assert "conflicting measured data" in str(exc)
            else:
                raise AssertionError("conflicting event replay was accepted")
    assert len(a.s.nodes("TemporalFrameEvent")) == 4
    assert len(a.s.nodes("TemporalFrameWindowSeal")) == 1
    policy = a.s.nodes("TemporalEscalationPolicy")[0]
    a.s.set_attr(policy, "enabled", 1.0)
    _tick(a)
    assembled = [n for n in a.s.nodes("TemporalSequenceWindow")
                 if a.s.node(n)["attrs"].get("window_id") == "adapter-window"]
    assert len(assembled) == 1
    assert a.s.node(assembled[0])["attrs"]["event_ids"] == [
        "adapter-window:0", "adapter-window:1", "adapter-window:2", "adapter-window:3"]
    motion = next(n for n in a.s.nodes("Observation")
                  if a.s.node(n)["attrs"].get("temporal_bridge"))
    assert a.s.node(motion)["attrs"]["status"] == "time_inferred"
    request = next(n for n in a.s.nodes("ThinkingBudgetRequest")
                   if a.s.node(n)["attrs"].get("requester_kind") == "temporal_escalation")
    assert a.s.node(request)["attrs"]["status"] == "consumed"
    assert a.s.node(request)["attrs"]["debited_epoch"] == 2.0
    a.close()


def test_world_adapter_does_not_infer_a_seal_or_window():
    a, _budget = _boot(enabled=True)
    source = a.s.add_node("Observation", {
        "key": "unclosed-source", "status": "decoded", "dim_checked": 1,
        "dim_explained": 0, "decoded_epoch": 2.0,
    })
    for index in range(4):
        a.ingest_temporal_frame_event(
            source, window_id="unclosed-window", event_id=f"unclosed:{index}",
            sequence_index=index, timestamp=index * 10.0,
            frame=[["cell", index, 0, "red"]], dim_types=DT, source_epoch=2.0,
        )
    _tick(a)
    assert a.s.nodes("TemporalFrameWindowSeal") == []
    assert a.s.nodes("TemporalSequenceWindow") == []
    assert a.s.nodes("ThinkingBudgetRequest") == []
    a.close()

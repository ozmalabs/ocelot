import pytest
import json

from evaluation.process_mastery.scheduled_learning_checkpoints import (
    capture_scheduled_checkpoint, checkpoint_ready,
    verify_common_world_allocation, verify_scheduled_checkpoint,
)


WORLD_SHA = "a" * 64


def _counts(work, *, exposures=0, rules=0, graph_bytes=100, budget=0, access=0):
    return {"primitive_work": work, "source_exposure": exposures,
            "native_rule_steps": rules, "graph_bytes": graph_bytes,
            "budget_debits": budget, "task_world_accesses": access}


def _capture(arm, checkpoint, graph, counters, status, parent=None, **kwargs):
    counters["graph_bytes"] = len(json.dumps(graph, sort_keys=True,
        separators=(",", ":"), ensure_ascii=False, default=str).encode())
    return capture_scheduled_checkpoint(arm=arm, checkpoint=checkpoint,
        native_graph=graph, cumulative=counters, interval_status=status,
        parent=parent, world_allocation_sha256=WORLD_SHA, **kwargs)


def test_fixed_budget_captures_failed_interval_and_preserves_actual_state():
    g0 = _capture("combined", "g0", {"nodes": [1]}, _counts(0), "initial")
    g1 = _capture("combined", "g1", {"nodes": [1, 2]}, _counts(0, access=1, rules=3),
                  "search_failed", g0, pending_candidate_ids=("candidate-7",))
    assert verify_scheduled_checkpoint(g1)
    assert g1.captured_state_changed
    assert g1.interval_delta["native_rule_steps"] == 3
    assert g1.pending_candidate_ids == ("candidate-7",)


def test_pending_operator_is_retained_without_execution_or_approval():
    g0 = _capture("combined", "g0", {"nodes": []}, _counts(0), "initial")
    pending = _capture("combined", "g1", {"nodes": []}, _counts(0, access=1),
        "authorization_pending", g0, pending_candidate_ids=("c-1",))
    assert not pending.actionable
    assert pending.approval_ids == ()
    assert pending.receipt_ids == ()
    assert not pending.captured_state_changed


def test_same_world_access_across_arms_and_checkpoints():
    a = _capture("frozen_ancestor", "g0", {"nodes": []}, _counts(0), "initial")
    b = _capture("combined", "g0", {"nodes": []}, _counts(0), "initial")
    assert verify_common_world_allocation((a, b))
    different = capture_scheduled_checkpoint(arm="combined", checkpoint="g0",
        native_graph={"nodes": []}, cumulative=_counts(0, graph_bytes=12), interval_status="initial",
        world_allocation_sha256="b" * 64)
    assert not verify_common_world_allocation((a, different))


def test_cumulative_counters_include_restored_branch_work_and_cannot_regress():
    g0 = _capture("combined", "g0", {"nodes": []}, _counts(0, rules=7), "initial")
    with pytest.raises(ValueError, match="native_rule_steps regressed"):
        _capture("combined", "g1", {"nodes": []}, _counts(0, access=1, rules=6),
                 "no_change", g0)
    g1 = _capture("combined", "g1", {"nodes": []}, _counts(0, access=1, rules=7),
                  "no_change", g0)
    assert g1.interval_delta["native_rule_steps"] == 0


def test_restart_preserves_schedule_and_checkpoint_hash():
    assert checkpoint_ready(0, "g0")
    assert not checkpoint_ready(999, "g1")
    assert checkpoint_ready(1000, "g1")
    assert checkpoint_ready(0, "g1", cumulative_task_world_accesses=1)
    g0 = _capture("combined", "g0", {"nodes": ["state"]}, _counts(0), "initial")
    assert verify_scheduled_checkpoint(g0)
    assert not verify_scheduled_checkpoint(type(g0)(**{**g0.__dict__,
        "checkpoint_sha256": "0" * 64}))


def test_complete_graph_and_native_work_ceilings_are_enforced():
    with pytest.raises(ValueError, match="memory ceiling"):
        capture_scheduled_checkpoint(arm="combined", checkpoint="g0",
            native_graph={"nodes": []}, cumulative=_counts(0),
            interval_status="initial", world_allocation_sha256=WORLD_SHA,
            max_graph_bytes=1)
    with pytest.raises(ValueError, match="native-rule work exceeds"):
        _capture("combined", "g0", {"nodes": []},
                 _counts(0, rules=250_001), "initial")


def test_auxiliary_native_search_snapshot_is_hash_bound_and_charged():
    primary = {"nodes": []}
    search = {"nodes": [{"type": "OpenProcessCandidate", "id": 4}], "edges": []}
    import json
    primary_bytes = len(json.dumps(primary, sort_keys=True,
        separators=(",", ":")).encode())
    aux = {"native_process_search": search}
    aux_bytes = len(json.dumps(aux, sort_keys=True,
        separators=(",", ":")).encode())
    cp = capture_scheduled_checkpoint(arm="process_search_only", checkpoint="g0",
        native_graph=primary, auxiliary_native_graphs=aux,
        cumulative=_counts(0, graph_bytes=primary_bytes + aux_bytes),
        interval_status="initial", world_allocation_sha256=WORLD_SHA)
    assert verify_scheduled_checkpoint(cp)
    assert "OpenProcessCandidate" in cp.auxiliary_snapshots_json
    assert cp.graph_bytes == primary_bytes + aux_bytes

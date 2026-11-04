import pytest
import time

from evaluation.process_mastery.independent_worlds import (
    agent_view, generate_d4_world_v2,
)
from evaluation.process_mastery.p22_checkpoint_panel import (
    _seal_isolated_measurements, _worker, run_isolated_checkpoint_panel,
)
from evaluation.process_mastery.checkpoint_world_adapter import (
    capture_held_process_checkpoint,
)
from evaluation.process_mastery.native_process_execution import params_digest
from evaluation.process_mastery.p22_resource_accounting import (
    resource_snapshot_digest_valid, snapshot_native_resources,
)
from substrate.boot_profiles import boot_cognition_on


def test_isolated_worker_measurements_are_bound_into_snapshot_digest():
    agent = boot_cognition_on()
    try:
        snapshot = snapshot_native_resources(agent, runtime_counters={
            "native_rule_steps": 0, "native_model_calls": 0})
        outcome = {"resource_snapshot": snapshot}
        sealed = _seal_isolated_measurements(outcome, wall_seconds=0.25,
            peak_rss_bytes=123456, parent_runtime={
                "wall_time_seconds": 1.5, "process_peak_rss_bytes": 100000})
        measured = sealed["resource_snapshot"]
        assert resource_snapshot_digest_valid(measured)
        assert measured["runtime_counters"]["wall_time_seconds"] == 1.75
        assert measured["runtime_counters"]["process_peak_rss_bytes"] == 123456
        assert measured["resource_measurement_coverage"][
            "wall_time_seconds"]["source"] == "p22_isolated_worker.perf_counter"
        assert measured["resource_measurement_coverage"][
            "process_peak_rss_bytes"]["source"] == "p22_isolated_worker.ru_maxrss"
    finally:
        agent.close()


def test_isolated_panel_rejects_heldout_world_before_checkpoint_loading():
    heldout = dict(agent_view(generate_d4_world_v2(split="train", draw=0)),
        split="heldout", world_id="fixture:d4:heldout:rejected")
    checkpoints = {arm: {} for arm in
        ("unchanged", "adaptive_only", "invention_only", "full")}
    with pytest.raises(ValueError, match="registered training views"):
        run_isolated_checkpoint_panel(checkpoints, [heldout])


def test_worker_wall_time_includes_fresh_learner_boot(monkeypatch):
    world = agent_view(generate_d4_world_v2(split="train", draw=18))
    source = boot_cognition_on()
    try:
        for policy_type in ("SolverPolicy", "ProcessSchemaPolicy"):
            for policy in source.s.nodes(policy_type):
                source.s.set_attr(policy, "enabled", 1.0)
        domain = source.s.add_node("ProcessDomain", {"name": "worker-timing",
            "kind": "permutation", "domain_kind": "permutation",
            "probes": [world["initial_state"]], "source_epoch": 0,
            "model_epoch": 0, "frame_epoch": 0, "probe_epoch": 0})
        source.s.add_edge(source.agent, "has_process_domain", domain, {})
        params = world["held_processes"]["rot90"]
        schema = source.s.add_node("ProcessSchema", {"name": "rot90",
            "kind": "permutation", "domain": "worker-timing",
            "domain_kind": "permutation", "params": params,
            "source_digest": params_digest(params), "status": "active",
            "provenance": "held", "cost": 1.0, "owner_agent": source.agent,
            "invariants": [], "source_epoch": 0, "model_epoch": 0,
            "frame_epoch": 0, "probe_epoch": 0})
        source.s.add_edge(source.agent, "has_process_schema", schema, {})
        source.s.add_edge(domain, "has_held_process", schema, {})
        checkpoint = capture_held_process_checkpoint(source, schema,
            checkpoint_id="worker-timing-root")
    finally:
        source.close()

    from evaluation.process_mastery import p22_checkpoint_panel as panel_module
    real_boot = boot_cognition_on
    def delayed_boot():
        time.sleep(0.05)
        return real_boot()
    monkeypatch.setattr(panel_module, "boot_cognition_on", delayed_boot)
    outcome = _worker({"checkpoint": checkpoint.__dict__, "world": world,
        "cumulative_primitive_ceiling": 30_000,
        "native_rule_progress_ceiling": 20_000})
    assert outcome["isolated_worker_wall_time_seconds"] >= 0.05
    assert outcome["resource_snapshot"]["runtime_counters"][
        "wall_time_seconds"] >= 0.05
    assert resource_snapshot_digest_valid(outcome["resource_snapshot"])

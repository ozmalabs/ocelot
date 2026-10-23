import pytest

from evaluation.process_mastery.independent_worlds import (
    agent_view, generate_d4_world_v2,
)
from evaluation.process_mastery.p22_checkpoint_panel import (
    _seal_isolated_measurements, run_isolated_checkpoint_panel,
)
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
    heldout = agent_view(generate_d4_world_v2(split="heldout", draw=0))
    checkpoints = {arm: {} for arm in
        ("unchanged", "adaptive_only", "invention_only", "full")}
    with pytest.raises(ValueError, match="registered training views"):
        run_isolated_checkpoint_panel(checkpoints, [heldout])

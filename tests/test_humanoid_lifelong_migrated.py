from __future__ import annotations

import inspect
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "protocols" / "humanoid_lifelong_improvement_v1.json"


def _row(progress, lateral=0.0, fall=None):
    return {
        "directed_progress": progress,
        "lateral_offset": lateral,
        "first_fall_action": fall,
        "support_alternations": 10,
        "aerial_samples": 0,
        "compound_action_count": 1,
    }


def test_lifelong_protocol_has_paired_behavioral_discriminator():
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))

    assert protocol["arms"] == ["accumulating", "fresh_control"]
    assert protocol["lifetimes"] >= 4
    discriminator = protocol["primary_discriminator"]
    assert all(discriminator.values())


def test_lifelong_runner_only_transports_graph_minted_library():
    from scripts import jabberwock_humanoid_lifelong as runner

    source = inspect.getsource(runner.run_experiment)
    assert "_run_arm(" in source
    assert "motor_library=motor_library" in source
    assert "motor_library_out=library_path" in source
    assert "json.loads" in source
    assert "selected_token" not in source
    assert "motor_tokens" not in source
    assert "memory_eligible" not in source


def test_assessment_refuses_counter_only_flat_curve():
    from scripts.jabberwock_humanoid_lifelong import _assess

    accumulating = [_row(1.0) for _ in range(4)]
    fresh = [_row(1.0) for _ in range(4)]

    assessment = _assess(accumulating, fresh)
    assert assessment["verdict"] == "DEGRADE"
    assert assessment["fresh_control_deterministic"]
    assert not assessment["final_progress_improved"]
    assert not assessment["late_progress_improved"]


def test_assessment_confirms_safe_late_behavioral_improvement():
    from scripts.jabberwock_humanoid_lifelong import _assess

    accumulating = [
        _row(1.0),
        _row(1.1),
        _row(1.3),
        _row(1.4),
    ]
    fresh = [_row(1.0) for _ in range(4)]

    assessment = _assess(accumulating, fresh)
    assert assessment["verdict"] == "CONFIRM"
    assert assessment["final_progress_improved"]
    assert assessment["late_progress_improved"]
    assert assessment["no_new_fall"]
    assert assessment["final_lateral_safe"]


def test_assessment_falsifies_a_new_fall_or_lateral_regression():
    from scripts.jabberwock_humanoid_lifelong import _assess

    fresh = [_row(1.0, lateral=0.1) for _ in range(4)]
    accumulating = [
        _row(1.0, lateral=0.1),
        _row(1.1, lateral=0.1),
        _row(1.3, lateral=0.1),
        _row(1.4, lateral=0.2, fall=10),
    ]

    assessment = _assess(accumulating, fresh)
    assert assessment["verdict"] == "FALSIFY"
    assert not assessment["no_new_fall"]
    assert not assessment["final_lateral_safe"]

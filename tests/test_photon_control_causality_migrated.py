"""Causal gates from physical photon evidence to graph-selected controls."""
from __future__ import annotations

import math

import numpy as np
import pytest

pytest.importorskip("substrate_rs")

from domains import doom_photon_world as dpw  # noqa: E402
from domains.control_bundle import ControlBundleAdapter  # noqa: E402
from substrate.seed_loader import manifest_for  # noqa: E402
from substrate.world_adapter import WorldAdapter  # noqa: E402


MOTION_CALIBRATION = {
    "retina_2d": True,
    "retina_n_az": 16,
    "retina_n_el": 12,
    "synchronous": True,
    "retina_accel": True,
    "event_native": True,
    "visual_motion": True,
    "visual_salience": True,
    "event_window_epochs": 8,
    "adapt_rate": 0.4,
    "onset_threshold_db": 6.0,
    "onset_refractory_epochs": 0.0,
}

HELD_CALIBRATION = {
    "retina_2d": True,
    "retina_n_az": 20,
    "retina_n_el": 15,
    "synchronous": True,
    "retina_accel": True,
    "event_native": True,
    "visual_motion": False,
    "visual_salience": False,
    "held_prediction": "decay",
}


def _load_attention(adapter, *, held=False):
    seeds = ["fovea_salience_bridge", "retinal_attention_graph"]
    if held:
        seeds.append("held_prediction_attention")
    for seed in seeds:
        adapter.inner.load_seed_manifest(
            manifest_for(seed), adapter.agent)


def _angular_controls(adapter):
    game = adapter.s.add_node("WorldInstance", {})
    step = math.radians(5.0)
    controls = ControlBundleAdapter(adapter, game, [{
        "axis": "angular",
        "role": "motor",
        "controls": [
            {"token": "turn_left", "dtheta_ema": -step},
            {"token": "turn_right", "dtheta_ema": step},
        ],
    }])
    adapter.inner.set_attr(adapter.agent, "my_angle", 0.0)
    return game, controls


def _authorize(_tokens):
    return {"expected_goal_work": 2.0, "recoverability": 1.0}


def _read_control(adapter, game, controls, tick):
    intent = controls.deliberate(tick, _authorize)
    action = controls.enact(intent, tick)
    return action, adapter.s.node(game)["attrs"]


def _motion_arm(residual_columns):
    adapter = WorldAdapter(seeds=())
    try:
        _load_attention(adapter)
        game, controls = _angular_controls(adapter)

        # Real GraphEye projection: adapt a dark field and then generate the
        # canonical coherent sweep used by the interactive Doom photon gate.
        for epoch in range(1, 5):
            adapter.update_vision(
                calibration=MOTION_CALIBRATION,
                photon_packets=[],
                photon_counts=np.zeros((12, 16), dtype=np.int64),
                photon_epoch=epoch,
            )
        for column in range(2, 10):
            counts = np.zeros((12, 16), dtype=np.int64)
            counts[5, column] = 4096
            adapter.update_vision(
                calibration=MOTION_CALIBRATION,
                photon_packets=[{
                    "col": column,
                    "row": 5,
                    "wavelength_nm": 498.0,
                    "count": 4096,
                }],
                photon_counts=counts,
                photon_epoch=column + 3,
            )

        projected = adapter.inner.neighbours(
            adapter.agent, "perceives_salience")
        assert len(projected) == 8
        # Controlled ablation at the graph/native boundary: the coherent sweep
        # is explained, so mark only the nominated projected photon cells as
        # unexplained. Direction remains GraphEye's measured gaze, not a host
        # action label.
        for node in projected:
            column = adapter.s.node(node)["attrs"]["column_index"]
            adapter.inner.set_attr(
                node, "residual_salience",
                2.0 if column in residual_columns else 0.0,
            )
        adapter.master_tick()
        adapter.inner.run_rules()
        attention = dict(adapter.s.node(adapter.agent)["attrs"])
        action, game_attrs = _read_control(adapter, game, controls, 12)
        return attention, action, game_attrs
    finally:
        adapter.close()


@pytest.mark.parametrize(
    ("columns", "expected"),
    [((2,), ("turn_left",)), ((9,), ("turn_right",))],
)
def test_photon_residual_side_changes_the_enacted_motor_action(columns, expected):
    attention, action, game = _motion_arm(columns)
    assert attention["attention_refused"] == 0.0
    assert attention["attention_salience"] == pytest.approx(8.0)
    assert action == expected
    assert game["chosen_source"] == "retinal_attention"
    assert game["attention_control_epoch"] == 12


@pytest.mark.parametrize("columns", [(), (2, 9)])
def test_zero_and_tied_photon_fields_refuse_the_attention_control_route(columns):
    attention, action, game = _motion_arm(columns)
    assert attention["attention_refused"] == 1.0
    assert attention["attention_salience"] == 0.0
    assert "attention_control_epoch" not in game
    # Refusal is specific to unsupported perception. Generic graph curiosity
    # remains live and uses the apparatus ordinal, never photon iteration order.
    assert game["chosen_source"] == "curiosity"
    assert action == ("turn_left",)


def _held_arm(changed_columns):
    adapter = WorldAdapter(seeds=())
    try:
        _load_attention(adapter, held=True)
        game, controls = _angular_controls(adapter)
        baseline = np.full((15, 20), 30, dtype=np.int64)
        adapter.update_vision(
            calibration=HELD_CALIBRATION,
            photon_packets=dpw.packets_from_counts(baseline),
            photon_counts=baseline,
            photon_epoch=1,
        )
        adapter.inner.run_rules()

        changed = baseline.copy()
        for column in changed_columns:
            changed[7, column] = 200
        adapter.update_vision(
            calibration=HELD_CALIBRATION,
            photon_packets=dpw.packets_from_counts(changed),
            photon_counts=changed,
            photon_epoch=2,
        )
        adapter.inner.run_rules()
        attention = dict(adapter.s.node(adapter.agent)["attrs"])
        action, game_attrs = _read_control(adapter, game, controls, 2)
        return attention, action, game_attrs
    finally:
        adapter.close()


@pytest.mark.parametrize(
    ("columns", "expected"),
    [((3,), ("turn_left",)), ((16,), ("turn_right",))],
)
def test_held_photon_prediction_side_changes_the_enacted_action(columns, expected):
    attention, action, game = _held_arm(columns)
    assert attention["attention_refused"] == 0.0
    assert attention["attention_evidence_kind"] == "held_prediction_residual"
    assert attention["attention_salience"] > 2.0
    assert action == expected
    assert game["chosen_source"] == "retinal_attention"


@pytest.mark.parametrize("columns", [(), (3, 16)])
def test_zero_and_tied_held_prediction_refuse_attention_control(columns):
    attention, action, game = _held_arm(columns)
    assert attention["attention_refused"] == 1.0
    assert attention["attention_salience"] == 0.0
    assert "attention_control_epoch" not in game
    assert game["chosen_source"] == "curiosity"
    assert action == ("turn_left",)


def test_static_no_salience_curiosity_is_live_and_covers_every_control():
    """Graph-data ordinal breaks the initial n_trials tie without world policy."""
    adapter = WorldAdapter(seeds=())
    try:
        game = adapter.s.add_node("WorldInstance", {})
        controls = ControlBundleAdapter(adapter, game, [{
            "axis": "opaque",
            "controls": ["alpha", "beta", "gamma"],
        }])
        adapter.inner.set_attr(adapter.agent, "attention_refused", 1.0)
        adapter.inner.set_attr(adapter.agent, "attention_salience", 0.0)

        actions = []
        for tick in range(1, 9):
            action, attrs = _read_control(
                adapter, game, controls, tick)
            assert attrs["chosen_source"] == "curiosity"
            assert action
            actions.extend(action)

        assert set(actions) == {"alpha", "beta", "gamma"}
        assert {
            adapter.s.node(node)["attrs"]["control_ordinal"]
            for node in controls.controls.values()
        } == {0, 1, 2}
    finally:
        adapter.close()


def test_persistent_attention_composes_with_exploration_and_reaches_use():
    """Salience may orient vision, but must not monopolise the other axes."""
    adapter = WorldAdapter(seeds=())
    try:
        game = adapter.s.add_node("WorldInstance", {})
        step = math.radians(5.0)
        controls = ControlBundleAdapter(adapter, game, [
            {"axis": "longitudinal", "controls": ["forward", "backward"]},
            {"axis": "lateral",
             "controls": ["strafe_left", "strafe_right"]},
            {"axis": "angular", "controls": [
                {"token": "turn_left", "dtheta_ema": -step},
                {"token": "turn_right", "dtheta_ema": step},
            ]},
            {"axis": "weapon", "role": "operate",
             "controls": ["attack"]},
            {"axis": "interaction", "role": "operate",
             "controls": ["use"]},
        ])
        for key, value in {
            "attention_refused": 0.0,
            "attention_salience": 8.0,
            "attention_sensor_epoch": 1,
            "my_angle": 0.0,
            "attention_x": 0.0,
            "attention_y": 1.0,
        }.items():
            adapter.inner.set_attr(adapter.agent, key, value)

        actions = [
            _read_control(adapter, game, controls, tick)[0]
            for tick in range(1, 7)
        ]

        assert all("turn_right" in action for action in actions)
        assert [next(token for token in action
                     if token != "turn_right") for action in actions] == [
            "forward", "backward", "strafe_left", "strafe_right",
            "attack", "use",
        ]
        assert all(
            adapter.s.node(control)["attrs"]["n_trials"] >= 1.0
            for token, control in controls.controls.items()
            if token != "turn_left"
        )
    finally:
        adapter.close()

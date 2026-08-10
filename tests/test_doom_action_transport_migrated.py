"""Mechanical guarantees at the graph-authored Doom actuator boundary."""
from __future__ import annotations

from collections import deque
import inspect
import os
import queue
import sys
import threading

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(ROOT, "scripts")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

import jabberwock_plays_doom as runner  # noqa: E402
from domains.photon_eye import fovea_logpolar_receptor_layout  # noqa: E402


def _fifo(*pulses):
    channel = queue.Queue()
    for pulse in pulses:
        channel.put(pulse)
    pending = deque()
    runner._drain_action_fifo(channel, pending, world_tick=1)
    return pending


def test_authored_nonnoop_pulses_remain_fifo_events():
    pending = _fifo(
        runner._action_pulse(
            ("forward",), authored_world_tick=1, expires_world_tick=5),
        runner._action_pulse(
            ("turn_left",), authored_world_tick=1, expires_world_tick=5),
    )

    first, expired = runner._take_action_for_world_tick(pending, 1)
    second, expired_later = runner._take_action_for_world_tick(pending, 2)

    assert first == ("forward",)
    assert second == ("turn_left",)
    assert expired == expired_later == 0
    assert not pending


def test_stale_head_expires_before_next_live_pulse_is_applied():
    pending = _fifo(
        runner._action_pulse(
            ("forward",), authored_world_tick=1, expires_world_tick=4),
        runner._action_pulse(
            ("turn_right",), authored_world_tick=2, expires_world_tick=8),
    )

    action, expired = runner._take_action_for_world_tick(pending, 5)

    assert action == ("turn_right",)
    assert expired == 1
    assert not pending


def test_future_authored_pulse_waits_for_its_world_tick():
    pending = _fifo(
        runner._action_pulse(
            ("attack",), authored_world_tick=6, expires_world_tick=8))

    action, expired = runner._take_action_for_world_tick(pending, 5)
    assert action == ("noop",)
    assert expired == 0
    assert len(pending) == 1

    action, expired = runner._take_action_for_world_tick(pending, 6)
    assert action == ("attack",)
    assert expired == 0
    assert not pending


def test_eye_commands_remain_latest_state_not_an_event_history():
    channel = queue.Queue(maxsize=1)
    runner._replace(channel, {"eye_motor_source_epoch": 3})
    runner._replace(channel, {"eye_motor_source_epoch": 4})

    assert runner._latest(channel) == {"eye_motor_source_epoch": 4}
    assert runner._latest(channel) is None


def test_world_reports_ticks_applied_and_expired_independently(monkeypatch):
    applied = []
    eye_commands_seen = []

    class FakeWorld:
        def __init__(self, **_config):
            pass

        def reset(self):
            return object(), {}

        def is_running(self):
            return True

        def apply_eye_motor_command(self, command):
            eye_commands_seen.append(command)

        def apply_action(self, substrate, _context, action):
            applied.append(action)
            return substrate, {}

        def release_action(self):
            pass

        def close(self):
            pass

    monkeypatch.setattr(runner.dw, "DoomWorld", FakeWorld)
    monkeypatch.setattr(
        runner.dw, "observation_packet",
        lambda _substrate, _context, tic: {"tic": tic})

    actions = queue.Queue()
    actions.put(runner._action_pulse(
        ("stale",), action_id=10,
        authored_world_tick=0, expires_world_tick=0))
    actions.put(runner._action_pulse(
        ("forward",), action_id=11,
        authored_world_tick=1, expires_world_tick=3))
    actions.put(runner._action_pulse(
        ("turn_left",), action_id=12,
        authored_world_tick=1, expires_world_tick=4))
    eyes = queue.Queue(maxsize=1)
    runner._replace(eyes, {"eye_motor_source_epoch": 7})
    frames = queue.Queue(maxsize=1)
    result = queue.Queue()
    receipts = queue.Queue()

    runner._doom_process(
        {"tics": 4, "record_path": "", "ticrate": 35},
        actions, eyes, frames, result, threading.Event(), receipts)

    telemetry = result.get_nowait()
    assert telemetry["doom_ticks"] == 4
    assert telemetry["applied_actions"] == 2
    assert telemetry["expired_actions"] == 1
    assert telemetry["expired_stale_actions"] == 1
    assert telemetry["expired_world_end_actions"] == 0
    assert applied == [
        ("forward",), ("turn_left",), ("noop",), ("noop",)]
    assert eye_commands_seen == [
        {"eye_motor_source_epoch": 7}, None, None, None]
    observed_receipts = runner._drain_action_receipts(receipts)
    assert [(row["action_id"], row["status"]) for row in observed_receipts] == [
        (10, "expired_stale"), (11, "applied"), (12, "applied")]
    assert [row["applied_world_tick"] for row in observed_receipts] == [
        -1, 1, 2]


def test_sender_side_terminal_pulses_are_honestly_counted_world_ended():
    telemetry = runner._reconcile_transport_telemetry(
        authored=5, applied=1, expired_stale=2, expired_world_end=1)

    assert telemetry == {
        "expired_stale_actions": 2,
        "expired_world_end_actions": 2,
        "expired_actions": 4,
    }
    assert 1 + telemetry["expired_actions"] == 5


def test_runner_uses_fifo_actions_and_a_sparse_native_foveated_eye():
    source = inspect.getsource(runner.main)
    assert "_replace(actions" not in source
    assert "actions.put(_action_pulse(" in source
    assert '"expires_tick"' in source
    assert "eye_commands=mp.Queue(maxsize=1)" in source

    assert runner.FOVEATED_RETINA_WIDTH == 96
    assert runner.FOVEATED_FOVEA_WIDTH == 96
    assert runner.FOVEATED_FOVEA_HEIGHT == 72
    assert runner.FOVEATED_PERIPHERAL_RECEPTORS == 96
    assert runner.FOVEATED_RETINA_HEIGHT == 73

    layout = fovea_logpolar_receptor_layout(
        runner.FOVEATED_RETINA_WIDTH,
        runner.FOVEATED_RETINA_HEIGHT,
        fovea_width=runner.FOVEATED_FOVEA_WIDTH,
        fovea_height=runner.FOVEATED_FOVEA_HEIGHT,
        peripheral_rings=4,
        peripheral_spokes=24,
        source_width=320,
        source_height=240,
    )
    assert sum(record["pathway"] == "fovea" for record in layout) == 6912
    assert sum(
        record["pathway"] == "log_polar_periphery"
        for record in layout
    ) == 96

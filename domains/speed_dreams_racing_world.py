"""Policy-free Speed Dreams 2.4.2 process and UDP transduction boundary."""
from __future__ import annotations

import math
import os
from pathlib import Path
import socket
import struct
import subprocess
from typing import Any


class _SpeedDreamsRates:
    control_hz = 50.0
    physics_hz = 500.0


TELEMETRY_MAGIC = 0x4A57544D
COMMAND_MAGIC = 0x4A57434D
PROTOCOL_VERSION = 2
TELEMETRY_STRUCT = struct.Struct("<IHHQ36d6i")
COMMAND_STRUCT = struct.Struct("<IHHQ14d2i")

DOUBLE_FIELDS = (
    "simulation_time_s",
    "delta_time_s",
    "speed_m_s",
    "body_vx_m_s",
    "body_vy_m_s",
    "yaw_rate_rad_s",
    "slip_angle_rad",
    "longitudinal_accel_m_s2",
    "lateral_accel_m_s2",
    "track_progress_m",
    "track_length_m",
    "track_lateral_m",
    "track_half_width_m",
    "heading_error_rad",
    "curvature_now_inv_m",
    "curvature_near_inv_m",
    "curvature_middle_inv_m",
    "curvature_far_inv_m",
    "curvature_envelope_near_inv_m",
    "curvature_envelope_middle_inv_m",
    "curvature_envelope_far_inv_m",
    "surface_grip",
    "front_slip_rad",
    "rear_slip_rad",
    "front_normal_load_n",
    "rear_normal_load_n",
    "tyre_temperature_mean_c",
    "tyre_condition_mean",
    "brake_temperature_mean",
    "fuel_l",
    "damage",
    "nearest_opponent_ahead_m",
    "nearest_opponent_lateral_m",
    "nearest_opponent_speed_m_s",
    "nearest_opponent_closing_m_s",
    "engine_rpm",
)
INTEGER_FIELDS = (
    "gear",
    "laps",
    "race_position",
    "collision_count",
    "pit_stops",
    "total_laps",
)


def decode_telemetry(payload: bytes) -> dict[str, float | int]:
    """Decode one ABI-checked packet without interpreting driving state."""
    if len(payload) != TELEMETRY_STRUCT.size:
        raise ValueError(
            f"telemetry packet has {len(payload)} bytes; "
            f"expected {TELEMETRY_STRUCT.size}"
        )
    values = TELEMETRY_STRUCT.unpack(payload)
    magic, version, byte_count, sequence = values[:4]
    if magic != TELEMETRY_MAGIC:
        raise ValueError("telemetry packet magic does not match")
    if version != PROTOCOL_VERSION:
        raise ValueError("telemetry protocol version does not match")
    if byte_count != TELEMETRY_STRUCT.size:
        raise ValueError("telemetry packet byte count does not match")
    doubles = values[4:4 + len(DOUBLE_FIELDS)]
    integers = values[4 + len(DOUBLE_FIELDS):]
    return {
        "sequence": int(sequence),
        **dict(zip(DOUBLE_FIELDS, map(float, doubles), strict=True)),
        **dict(zip(INTEGER_FIELDS, map(int, integers), strict=True)),
    }


def encode_command(
    sequence: int,
    action: dict[str, float | int],
) -> bytes:
    """Encode the exact graph command; no control transformation occurs."""
    return COMMAND_STRUCT.pack(
        COMMAND_MAGIC,
        PROTOCOL_VERSION,
        COMMAND_STRUCT.size,
        sequence,
        float(action["steering"]),
        float(action["throttle"]),
        float(action["brake"]),
        float(action.get("clutch", 0.0)),
        float(action["front_wing"]),
        float(action["rear_wing"]),
        float(action["drive_front_left"]),
        float(action["drive_front_right"]),
        float(action["drive_rear_left"]),
        float(action["drive_rear_right"]),
        float(action["brake_front_left"]),
        float(action["brake_front_right"]),
        float(action["brake_rear_left"]),
        float(action["brake_rear_right"]),
        int(action["gear"]),
        int(action["pit_request"]),
    )


class SpeedDreamsRacingWorld:
    """A blocking observation/action boundary around the text-only simulator."""

    def __init__(
        self,
        *,
        app_run: Path,
        local_directory: Path,
        race_name: str = "jabberwockrace",
        command_port: int = 31001,
        telemetry_port: int = 31002,
        timeout_s: float = 10.0,
    ) -> None:
        self.backend = "speed_dreams_2.4.2"
        self.config = _SpeedDreamsRates()
        self.track_length_m = 0.0
        self.app_run = app_run.resolve()
        self.local_directory = local_directory.resolve()
        self.race_name = race_name
        self.command_address = ("127.0.0.1", command_port)
        self.timeout_s = timeout_s
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._socket.bind(("127.0.0.1", telemetry_port))
        self._socket.settimeout(timeout_s)
        self._process: subprocess.Popen[bytes] | None = None
        self._latest: dict[str, float | int] | None = None
        self._offtrack_time_s = 0.0
        self._last_action: dict[str, float | int] = {
            "steering": 0.0,
            "throttle": 0.0,
            "brake": 1.0,
            "drive_front_left": 0.0,
            "drive_front_right": 0.0,
            "drive_rear_left": 0.0,
            "drive_rear_right": 0.0,
            "brake_front_left": 1.0,
            "brake_front_right": 1.0,
            "brake_rear_left": 1.0,
            "brake_rear_right": 1.0,
            "front_wing": 0.0,
            "rear_wing": 0.0,
            "gear": 1,
            "pit_request": 0,
        }

    def __enter__(self) -> "SpeedDreamsRacingWorld":
        self.reset()
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def close(self) -> None:
        if self._process is not None and self._process.poll() is None:
            self._process.terminate()
            try:
                self._process.wait(timeout=3.0)
            except subprocess.TimeoutExpired:
                self._process.kill()
                self._process.wait(timeout=3.0)
        self._process = None
        self._socket.close()

    def _receive_newer(
        self,
        previous_sequence: int,
    ) -> dict[str, float | int]:
        while True:
            payload, _ = self._socket.recvfrom(TELEMETRY_STRUCT.size)
            telemetry = decode_telemetry(payload)
            if int(telemetry["sequence"]) > previous_sequence:
                return telemetry

    def reset(self) -> dict[str, Any]:
        if self._process is not None:
            raise RuntimeError("Speed Dreams world is already running")
        self.local_directory.mkdir(parents=True, exist_ok=True)
        environment = os.environ.copy()
        environment["JABBERWOCK_SD_COMMAND_PORT"] = str(
            self.command_address[1]
        )
        environment["JABBERWOCK_SD_TELEMETRY_PORT"] = str(
            self._socket.getsockname()[1]
        )
        self._process = subprocess.Popen(
            [
                str(self.app_run),
                "--localdir",
                str(self.local_directory),
                "--startrace",
                self.race_name,
                "--textonly",
                "--norandom",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            env=environment,
        )
        self._latest = self._receive_newer(-1)
        self.track_length_m = float(self._latest["track_length_m"])
        self._offtrack_time_s = 0.0
        return self.observe()

    def step(self, action: dict[str, float | int]) -> dict[str, Any]:
        if self._latest is None:
            raise RuntimeError("Speed Dreams world has not been reset")
        sequence = int(self._latest["sequence"])
        self._socket.sendto(
            encode_command(sequence, action),
            self.command_address,
        )
        self._last_action = dict(action)
        self._latest = self._receive_newer(sequence)
        if (
            abs(float(self._latest["track_lateral_m"]))
            > float(self._latest["track_half_width_m"])
        ):
            self._offtrack_time_s += float(self._latest["delta_time_s"])
        return self.observe()

    def observe(self) -> dict[str, Any]:
        if self._latest is None:
            raise RuntimeError("Speed Dreams world has no telemetry")
        state = self._latest
        total_distance = (
            int(state["total_laps"]) * float(state["track_length_m"])
        )
        completed_distance = (
            int(state["laps"]) * float(state["track_length_m"])
            + float(state["track_progress_m"])
        )
        tyre_temperature = float(state["tyre_temperature_mean_c"])
        return {
            "time_s": float(state["simulation_time_s"]),
            "speed_m_s": float(state["speed_m_s"]),
            "body_vx_m_s": float(state["body_vx_m_s"]),
            "body_vy_m_s": float(state["body_vy_m_s"]),
            "yaw_rate_rad_s": float(state["yaw_rate_rad_s"]),
            "slip_angle_rad": float(state["slip_angle_rad"]),
            "longitudinal_accel_m_s2": float(
                state["longitudinal_accel_m_s2"]
            ),
            "lateral_accel_m_s2": float(
                state["lateral_accel_m_s2"]
            ),
            "track_progress_m": float(state["track_progress_m"]),
            "track_length_m": float(state["track_length_m"]),
            "track_lateral_m": float(state["track_lateral_m"]),
            "track_half_width_m": float(state["track_half_width_m"]),
            "track_heading_error_rad": float(state["heading_error_rad"]),
            "track_curvature_now_inv_m": float(
                state["curvature_now_inv_m"]
            ),
            "track_curvature_near_inv_m": float(
                state["curvature_near_inv_m"]
            ),
            "track_curvature_middle_inv_m": float(
                state["curvature_middle_inv_m"]
            ),
            "track_curvature_far_inv_m": float(
                state["curvature_far_inv_m"]
            ),
            "track_curvature_envelope_near_inv_m": float(
                state["curvature_envelope_near_inv_m"]
            ),
            "track_curvature_envelope_middle_inv_m": float(
                state["curvature_envelope_middle_inv_m"]
            ),
            "track_curvature_envelope_far_inv_m": float(
                state["curvature_envelope_far_inv_m"]
            ),
            "surface_grip": float(state["surface_grip"]),
            "surface_wet": 0.0,
            "front_slip_rad": float(state["front_slip_rad"]),
            "rear_slip_rad": float(state["rear_slip_rad"]),
            "front_normal_load_n": float(state["front_normal_load_n"]),
            "rear_normal_load_n": float(state["rear_normal_load_n"]),
            "tyre_temperature_mean_c": tyre_temperature,
            "tyre_condition_mean": float(state["tyre_condition_mean"]),
            "brake_temperature_mean_c": float(
                state["brake_temperature_mean"]
            ),
            "fuel_l": float(state["fuel_l"]),
            "damage": float(state["damage"]),
            "laps": int(state["laps"]),
            "race_total_laps": int(state["total_laps"]),
            "race_total_distance_m": total_distance,
            "race_remaining_distance_m": max(
                0.0,
                total_distance - completed_distance,
            ),
            "offtrack_time_s": self._offtrack_time_s,
            "collisions": int(state["collision_count"]),
            "pit_stops": int(state["pit_stops"]),
            "pit_service_active": 0.0,
            "nearest_opponent_ahead_m": float(
                state["nearest_opponent_ahead_m"]
            ),
            "nearest_opponent_lateral_m": float(
                state["nearest_opponent_lateral_m"]
            ),
            "nearest_opponent_speed_m_s": float(
                state["nearest_opponent_speed_m_s"]
            ),
            "nearest_opponent_closing_m_s": float(
                state["nearest_opponent_closing_m_s"]
            ),
            "engine_rpm": float(state["engine_rpm"]),
            "gear": int(state["gear"]),
            "race_position": int(state["race_position"]),
            "damage_active": 0.0,
            "receipt_steering_retention": 1.0,
            "receipt_power_retention": 1.0,
            "receipt_front_brake_retention": 1.0,
            "receipt_rear_brake_retention": 1.0,
            "receipt_aero_retention": 1.0,
            "last_action": dict(self._last_action),
        }


__all__ = [
    "COMMAND_STRUCT",
    "SpeedDreamsRacingWorld",
    "TELEMETRY_STRUCT",
    "decode_telemetry",
    "encode_command",
]

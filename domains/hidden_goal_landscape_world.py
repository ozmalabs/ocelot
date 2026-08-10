"""Mechanical hidden-goal landscape boundary for an aerial search mission."""
from __future__ import annotations

import math
from typing import Any


class HiddenGoalLandscapeWorld:
    """A deterministic terrain-masked search route with opaque actions."""

    _TOKENS = (
        "landscape_effector_000",
        "landscape_effector_001",
        "landscape_effector_002",
        "landscape_effector_003",
    )

    def __init__(self, *, target_route_index: int = 17) -> None:
        self.route = tuple(
            (float(x), float(y), 42.0 + 2.0 * math.sin(x * 0.7))
            for row, y in enumerate(range(0, 25, 4))
            for x in (
                range(0, 25, 2)
                if row % 2 == 0
                else range(24, -1, -2)
            )
        )
        if target_route_index not in range(len(self.route)):
            raise ValueError("target_route_index must lie on the search route")
        self._target_index = target_route_index
        self.reset()

    def actuator_options(self) -> tuple[dict[str, Any], ...]:
        return tuple(
            {"token": token, "ordinal": float(index)}
            for index, token in enumerate(self._TOKENS)
        )

    def reset(self) -> dict[str, Any]:
        self._route_index = 0
        self._flare_count = 0
        self._goal_marked = False
        return self.observe()

    @staticmethod
    def terrain_height(x: float, y: float) -> float:
        return (
            13.0
            + 8.0 * math.sin(x * 0.28)
            + 6.0 * math.cos(y * 0.34)
            + 12.0 * math.exp(-((x - 12.0) ** 2 + (y - 8.0) ** 2) / 30.0)
        )

    def _signal(self) -> float:
        x, y, z = self.route[self._route_index]
        tx, ty, _tz = self.route[self._target_index]
        distance = math.hypot(tx - x, ty - y)
        if distance > 5.0:
            return 0.0
        samples = 12
        for sample in range(1, samples):
            fraction = sample / samples
            sx = x + (tx - x) * fraction
            sy = y + (ty - y) * fraction
            sight_height = z - 7.0 * fraction
            if self.terrain_height(sx, sy) >= sight_height:
                return 0.0
        return max(0.0, 1.0 - distance / 6.0)

    def step(self, token: str) -> dict[str, Any]:
        if token not in self._TOKENS:
            raise ValueError(f"unknown landscape action {token!r}")
        if token == self._TOKENS[0]:
            self._route_index = min(self._route_index + 1, len(self.route) - 1)
        elif token == self._TOKENS[1]:
            self._route_index = max(self._route_index - 1, 0)
        elif token == self._TOKENS[3]:
            self._flare_count += 1
            if self._signal() > 0.0:
                self._goal_marked = True
        return self.observe()

    def observe(self) -> dict[str, Any]:
        position = self.route[self._route_index]
        return {
            "position": position,
            "route_progress": float(self._route_index),
            "terrain_height": self.terrain_height(position[0], position[1]),
            "signal_strength": self._signal(),
            "payload_emission_count": float(self._flare_count),
            "goal_marked": float(self._goal_marked),
        }


__all__ = ["HiddenGoalLandscapeWorld"]

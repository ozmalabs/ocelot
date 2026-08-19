"""Small deterministic helpers for binary active-goal manifold payloads."""
from __future__ import annotations


def goal_manifold(manifold_id: str) -> dict:
    return {
        "manifold_id": manifold_id,
        "required_horizon": 0,
        "minimum_width": 1.0,
        "maximum_information_loss": 0.0,
        "required_tube": [{
            "time": 0,
            "cells": {"goal": {
                "weight": 1.0, "information": 1.0,
                "metadata": {"goal": manifold_id},
            }},
            "links": [],
        }],
    }


def goal_projection(manifold_id: str, *, active: bool, action_count: int,
                    intervention_magnitude: float) -> dict:
    return {
        "manifold_id": manifold_id,
        "projected_tube": ([{
            "time": 0,
            "cells": {"goal": {
                "weight": 1.0, "information": 1.0,
                "metadata": {"goal": manifold_id},
            }},
            "links": [],
        }] if active else [{"time": 0, "cells": {}, "links": []}]),
        "action_count": action_count,
        "intervention_magnitude": intervention_magnitude,
    }


__all__ = ["goal_manifold", "goal_projection"]

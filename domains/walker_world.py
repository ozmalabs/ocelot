"""1D walker world — body with two joints, items in space, local observation.

The body is at position ``x``. It has two joints, each with a discrete angle
in {0.0, 0.5, 1.0}. The body's *velocity* is the magnitude of joint angle
difference — coordinated (alternating) joints produce velocity; synchronized
(both same angle) joints produce nothing.

Items are scattered at fixed positions along x. Local observation: only
items within ``observation_radius`` of the body appear in the substrate.
Items further away are *not yet sensed* — the agent must move closer.

Continuous attributes (position, angles) are also exposed as *binned*
discrete attrs (``x_bin``, ``angle_bin``) so the agent's
co-occurrence-based discovery has something stable to count over.

Implementation note: ``apply_action`` is *stateless* (returns a fresh
substrate + ctx without mutating the world). This is critical because
``choose_action`` previews candidate actions during search.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from substrate import (
    ConsistencyChecker,
    Grammar,
    Substrate,
    TypedGraph,
)


@dataclass
class WalkerWorld:
    """A 1D world. World identity carries only the items + observation radius
    (immutable config). Mutable state — body position, joint angles, touched
    items — lives in ctx, threaded by the driver."""

    item_positions: tuple[float, ...] = (3.0, 7.0, 12.0, 18.0, 25.0, 33.0)
    observation_radius: float = 3.0
    n_angle_bins: int = 3   # discrete angles: 0.0, 0.5, 1.0
    move_increment: float = 1.0

    def reset(self) -> tuple[Any, dict]:
        ctx = {
            "body_x": 0.0,
            "joint1": 0.5,
            "joint2": 0.5,
            "touched_items": frozenset(),
            "tick": 0,
        }
        substrate = self._build(ctx)
        return substrate, ctx

    def _build(self, ctx: dict) -> Any:
        """Build a fresh substrate reflecting ctx state.

        Locality: items further than ``observation_radius`` are excluded
        from the substrate — the agent literally doesn't see them yet."""
        g = TypedGraph()
        body_id = g._insert_node("Body", {
            "x": round(ctx["body_x"], 3),
            "x_bin": int(ctx["body_x"] // 1.0),
        })
        j1_id = g._insert_node("Joint", {
            "id": 1,
            "angle": ctx["joint1"],
            "angle_bin": int(ctx["joint1"] * (self.n_angle_bins - 1)),
        })
        j2_id = g._insert_node("Joint", {
            "id": 2,
            "angle": ctx["joint2"],
            "angle_bin": int(ctx["joint2"] * (self.n_angle_bins - 1)),
        })
        g._insert_edge(body_id, "has_joint", j1_id)
        g._insert_edge(body_id, "has_joint", j2_id)
        # Items within local observation radius become distinct node-types
        # so the agent treats them as different things.
        for i, ipos in enumerate(self.item_positions):
            if abs(ctx["body_x"] - ipos) <= self.observation_radius:
                item_id = g._insert_node(f"Item{i}", {
                    "id": i,
                    "position": ipos,
                    "distance_bin": int(abs(ctx["body_x"] - ipos)),
                    "touched": i in ctx["touched_items"],
                })
                g._insert_edge(body_id, "near", item_id)
        substrate = Substrate(graph=g, checker=ConsistencyChecker(Grammar([])))
        return substrate

    def legal_actions(self, ctx: dict, agent_id: str, agent) -> list:
        """All combinations of joint angles. With 3 bins each = 9 actions."""
        actions = []
        angles = [i / (self.n_angle_bins - 1) for i in range(self.n_angle_bins)]
        for j1 in angles:
            for j2 in angles:
                actions.append(("set_joints", j1, j2))
        return actions

    def interpret_acts_on(self, ctx: dict, action) -> list[str]:
        """What body-types does this action touch?"""
        _, j1, j2 = action
        velocity = abs(j1 - j2) * self.move_increment
        touched: list[str] = []
        if velocity > 0:
            touched.extend(["Body", "Joint"])
            new_x = ctx["body_x"] + velocity
            for i, ipos in enumerate(self.item_positions):
                old_dist = abs(ctx["body_x"] - ipos)
                new_dist = abs(new_x - ipos)
                if new_dist < 0.5 and i not in ctx["touched_items"]:
                    touched.append(f"Item{i}")
        return touched

    def apply_action(self, ctx: dict, action) -> tuple[Any, dict]:
        """Stateless: returns future (substrate, ctx). Does NOT mutate world
        or ctx — choose_action previews candidate actions via this method
        and must not corrupt state."""
        _, j1, j2 = action
        velocity = abs(j1 - j2) * self.move_increment
        new_x = ctx["body_x"] + velocity
        new_touched = set(ctx["touched_items"])
        for i, ipos in enumerate(self.item_positions):
            if abs(new_x - ipos) < 0.5:
                new_touched.add(i)
        new_ctx = {
            "body_x": new_x,
            "joint1": j1,
            "joint2": j2,
            "touched_items": frozenset(new_touched),
            "tick": ctx["tick"] + 1,
        }
        substrate = self._build(new_ctx)
        return substrate, new_ctx


def walker_world_handle(world: WalkerWorld, agent) -> dict:
    """World handle for a CuriousAgent."""
    def reset():
        return world.reset()

    def legal_actions(s, ctx):
        return world.legal_actions(ctx, "agent", agent)

    def apply_action(s, ctx, action):
        return world.apply_action(ctx, action)

    def interpret_acts_on(s, ctx, action):
        return world.interpret_acts_on(ctx, action)

    return {
        "name": "walker",
        "reset": reset,
        "legal_actions": legal_actions,
        "apply_action": apply_action,
        "interpret_acts_on": interpret_acts_on,
    }

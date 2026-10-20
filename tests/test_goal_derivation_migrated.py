"""Tests for seeds/goal_derivation.json direction rules (P1.H7.4)."""
from __future__ import annotations

from substrate.world_adapter import WorldAdapter


def test_goal_derivation_direction_rules():
    w = WorldAdapter(seeds=("goal_derivation",))
    game = w.s.add_node("WorldInstance", {"world_type": "Game"})
    up = w.s.add_node("WorldInstance", {"world_type": "ActionKind", "akid": "Up"})
    down = w.s.add_node("WorldInstance", {"world_type": "ActionKind", "akid": "Down"})
    left = w.s.add_node("WorldInstance", {"world_type": "ActionKind", "akid": "Left"})
    right = w.s.add_node("WorldInstance", {"world_type": "ActionKind", "akid": "Right"})
    select = w.s.add_node("WorldInstance", {"world_type": "ActionKind", "akid": "Select"})

    for ak in (up, down, left, right, select):
        w.inner.add_edge_unchecked(game, "has_action_kind", ak)

    w.inner.run_rules()

    up_attrs = w.s.node(up)["attrs"]
    assert up_attrs.get("d_row") == -1.0
    assert up_attrs.get("d_col") == 0.0
    assert up_attrs.get("is_move") == 1.0

    down_attrs = w.s.node(down)["attrs"]
    assert down_attrs.get("d_row") == 1.0
    assert down_attrs.get("d_col") == 0.0
    assert down_attrs.get("is_move") == 1.0

    left_attrs = w.s.node(left)["attrs"]
    assert left_attrs.get("d_row") == 0.0
    assert left_attrs.get("d_col") == -1.0
    assert left_attrs.get("is_move") == 1.0

    right_attrs = w.s.node(right)["attrs"]
    assert right_attrs.get("d_row") == 0.0
    assert right_attrs.get("d_col") == 1.0
    assert right_attrs.get("is_move") == 1.0

    select_attrs = w.s.node(select)["attrs"]
    assert select_attrs.get("d_row") == 0.0
    assert select_attrs.get("d_col") == 0.0
    assert select_attrs.get("is_move") == 0.0
    assert select_attrs.get("act_at_point") == 1.0

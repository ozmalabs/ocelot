"""Tests for seeds/compositional_plan.json (P1.H7.1)."""
from __future__ import annotations

from substrate.world_adapter import WorldAdapter


def test_compositional_plan_prescribe_and_flag_wrong_form():
    w = WorldAdapter(seeds=("compositional_plan",))
    piece = w.s.add_node(
        "Piece",
        {
            "prescribed": 0.0,
            "applicability": 0.5,
            "current_is_failed": 1,
        },
    )
    law = w.s.add_node(
        "Principle",
        {
            "prescribed_action": "X",
            "payoff": 2.0,
        },
    )
    w.inner.add_edge_unchecked(piece, "governed_by", law)

    w.inner.run_rules()
    attrs = w.s.node(piece)["attrs"]
    assert attrs.get("prescribed_form") == "X"
    assert attrs.get("expected_gain") == 1.0
    assert attrs.get("prescribed") == 1.0
    assert attrs.get("reframe_needed") == 1.0

    # Second tick changes nothing.
    snapshot = dict(attrs)
    w.inner.run_rules()
    assert dict(w.s.node(piece)["attrs"]) == snapshot


def test_compositional_plan_absent_prescribed_attr():
    """Record actual engine behaviour when `prescribed` is absent on Piece:
    `Attr(piece, "prescribed")` evaluates to Value::None, so `Eq(None, 0.0)`
    is false and `prescribe` does not fire; `flag_wrong_form` still fires
    when `current_is_failed > 0.0`.
    """
    w = WorldAdapter(seeds=("compositional_plan",))
    piece = w.s.add_node(
        "Piece",
        {
            "applicability": 0.5,
            "current_is_failed": 1,
        },
    )
    law = w.s.add_node(
        "Principle",
        {
            "prescribed_action": "X",
            "payoff": 2.0,
        },
    )
    w.inner.add_edge_unchecked(piece, "governed_by", law)

    w.inner.run_rules()
    attrs = w.s.node(piece)["attrs"]
    assert "prescribed_form" not in attrs
    assert "expected_gain" not in attrs
    assert "prescribed" not in attrs
    assert attrs.get("reframe_needed") == 1.0

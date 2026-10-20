"""Tests for seeds/modality_tom.json (P1.H7.2)."""
from __future__ import annotations

import pytest

from substrate.world_adapter import WorldAdapter


@pytest.mark.parametrize(
    ("modality", "expected_entailed"),
    [
        ("fact", 1),
        ("necessary", 1),
        ("possible", 0),
        ("obligation", 0),
    ],
)
def test_modal_entailment_gate(modality: str, expected_entailed: int):
    w = WorldAdapter(seeds=("modality_tom",))
    prop = w.s.add_node("Prop", {"modality": modality, "is_prop": 1})
    w.inner.add_edge_unchecked(prop, "is_prop", prop)

    w.inner.run_rules()
    assert w.s.node(prop)["attrs"].get("entailed") == expected_entailed

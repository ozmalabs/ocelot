"""the live loop, migrated — the curiosity loop runs as mechanical orchestration
of seeded faculties on the WorldAdapter (no CuriousAgent). `live()` sequences
reset → observe → (seeded choose → register acts_on → log → step → observe) →
discover over a world's callables; every DECISION is a seeded Term/Rule.

This is CuriousAgent.live MINUS dynamic-grammar growth (grow_representation /
gamma_dynamic) — genuine Γ-extension reasoning, not orchestration — which stays
in the bench for the tests that assert production growth.
"""
from __future__ import annotations

from substrate.world_adapter import WorldAdapter
from domains.number_world import NumberWorld, number_world_handle


def test_live_accumulates_senses_and_instances():
    wa = WorldAdapter()
    wa.live(number_world_handle(NumberWorld(max_n=25), None), n_games=2, max_plies=15)
    assert "Body" in wa.senses()
    assert "Number" in wa.senses()
    assert len(wa.instances("Number")) > 0


def test_live_registers_acts_on_relations():
    wa = WorldAdapter()
    wa.live(number_world_handle(NumberWorld(max_n=25), None), n_games=1, max_plies=12)
    # counting acts on the Body (cursor) and the Numbers it moves along
    assert "Body" in wa.acts_on_set()


def test_live_logs_activity_events():
    wa = WorldAdapter()
    wa.live(number_world_handle(NumberWorld(max_n=25), None), n_games=1, max_plies=10)
    assert wa._n_events > 0


def test_live_runs_a_dict_world_without_crashing():
    """chess_world is the dict-of-callables shape; the loop drives it and
    perceives its piece types (seeded faculties over a non-trivial world)."""
    from domains.worlds import chess_world
    wa = WorldAdapter()
    wa.live(chess_world(), n_games=1, max_plies=8)
    assert len(wa.senses()) > 0
    assert any(t.startswith("Black") or t.startswith("White") for t in wa.senses())

"""The receiver model — theory of mind over a participation framework.

A set of modeled minds (addressee, overhearers, third-party targets), each with
a believed-knowledge state. The first instrumental capability is per-party
NOVELTY (what's new vs. held), computed for ANY party — so the objective can
target a third party, not just the addressee. The know-judgement is graph-resident.
"""
from __future__ import annotations

from domains import audience as aud


def _scene():
    g = aud.new_graph()
    s = aud.make_scene(g)
    expert = aud.add_party(g, s, "expert", {"trace", "product", "A", "B"}, level=3)
    novice = aud.add_party(g, s, "novice", {"A", "B"}, level=1)
    observer = aud.add_party(g, s, "observer", {"trace"}, role="overhearer", level=2)
    return g, expert, novice, observer


_MEANING = {"force": "tell", "trace": {"of": {"product": {"a": "A", "b": "B"}}}}


def test_theory_of_mind_knows():
    g, expert, novice, _ = _scene()
    assert aud.knows(g, expert, "product") is True
    assert aud.knows(g, novice, "product") is False


def test_novelty_differs_per_party():
    g, expert, novice, _ = _scene()
    assert aud.novelty(g, _MEANING, expert)["new"] == []
    assert aud.novelty(g, _MEANING, novice)["new"] == ["product", "trace"]


def test_third_party_is_targetable():
    # the overhearer (not the addressee) gets its own novelty — the objective
    # may be defined over this party
    g, _, _, observer = _scene()
    assert aud.novelty(g, _MEANING, observer) == {
        "known": ["trace"], "new": ["A", "B", "product"]}

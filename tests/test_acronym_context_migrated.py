"""The agent expands a technical ACRONYM by CONTEXT: it reads Wikipedia's
disambiguation senses and picks the one whose words overlap the acronym's prose
context ('AAC', in audio/coding prose, -> 'Advanced Audio Coding' -> 'coding'),
then grounds via that head noun. High-precision: a wrong-domain sense sharing a
single word is refused (domains/acronym_context)."""
from __future__ import annotations

from collections import Counter

import pytest

from domains import acronym_context as ac, wiki_local as wl

pytestmark = pytest.mark.skipif(
    not wl.present(), reason="local Wikipedia dump not installed")


def test_context_picks_the_domain_right_expansion():
    audio = Counter({"audio": 3, "coding": 3, "compression": 2, "waveform": 2})
    assert ac.expand_acronym("aac", audio, min_score=3) == "coding"


def test_unmatched_context_refuses_to_expand():
    """An acronym whose disambiguation senses don't overlap the (alien) context
    is NOT grounded — an honest miss beats a wrong meaning."""
    alien = Counter({"banana": 5, "elephant": 4, "guitar": 3})
    assert ac.expand_acronym("aac", alien, min_score=3) is None


def test_expanded_acronym_grounds_via_its_head():
    import domains.seed_registry  # noqa: F401
    from substrate.boot_core import CORE_SEEDS, load_seeds_into
    from substrate.world_adapter import WorldAdapter
    from domains.read_and_ground import read_and_ground
    from domains import web_world
    web_world.set_local_only(True)
    wa = WorldAdapter(seeds=CORE_SEEDS)
    load_seeds_into(wa.s, wa.agent, ["lexical_ontology_roots", "relations", "psychology"])
    res = read_and_ground(wa.s, "tcp", conversation=ac.AcronymReader("tcp", "protocol"),
                          max_depth=25)
    assert res["grounded"] is True

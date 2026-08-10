"""The agent grounds an EPONYM by reading its own prose: a technical name in no
dictionary ('Ackermann function', "Amdahl's law", 'Anfinsen dogma') denotes the
PERSON it is named after, attested by the prose shape (a Capitalized name
modifying a technical concept). It grounds AS a person -> … -> entity
(domains/eponym_grounding)."""
from __future__ import annotations

import domains.seed_registry  # noqa: F401
from substrate.boot_core import CORE_SEEDS, load_seeds_into
from substrate.world_adapter import WorldAdapter
from domains.read_and_ground import read_and_ground
from domains import eponym_grounding as eg, web_world, wordnet_genus as wg


def _agent():
    web_world.set_local_only(True)
    wa = WorldAdapter(seeds=CORE_SEEDS)
    load_seeds_into(wa.s, wa.agent, ["lexical_ontology_roots", "relations", "psychology"])
    return wa


def test_detect_eponyms_from_prose_shape():
    prose = [
        "the Ackermann function grows faster than any primitive recursive function",
        "Anfinsen's dogma: the native structure is the free-energy minimum",
        "the Nyquist limit is half the sampling rate",
        "This rule fires when the function saturates",         # NOT an eponym
        "a modern algorithm beats the standard transform",     # NOT eponyms
    ]
    eps = eg.detect_eponyms(prose)
    assert {"ackermann", "anfinsen", "nyquist"} <= eps
    # sentence-start common words / determiners are NOT eponyms
    assert "this" not in eps and "modern" not in eps and "standard" not in eps


def test_eponym_grounds_as_a_person():
    # ONE agent for all names: each name is independent on the substrate, and a
    # single agent avoids the cross-WorldAdapter, name-keyed grounding cache that
    # multiple fresh agents in one process collide on.
    wa = _agent()
    for name in ("ackermann", "anfinsen", "nyquist", "kalman"):
        res = read_and_ground(wa.s, name, conversation=eg.EponymReader(name),
                              max_depth=25)
        # the eponym grounds (read as a person -> … -> entity)
        assert res["grounded"] is True, (name, res["reason"])


def test_non_eponym_still_grounds_normally():
    """The eponym reader is only used for detected eponyms; a real word grounds
    through the ordinary hybrid reader unchanged."""
    wa = _agent()
    res = read_and_ground(wa.s, "enzyme", conversation=wg.HybridChainReader("enzyme"),
                          max_depth=25)
    assert res["grounded"] is True

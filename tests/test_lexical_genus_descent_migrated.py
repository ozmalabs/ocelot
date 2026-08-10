"""The jabberwock grounds everyday concepts THROUGH A DICTIONARY — the WordNet
lexical-genus descent, on the seed-booted WorldAdapter. The second slice of the
encyclopedic read-and-ground campaign (docs/encyclopedic_seeds_reading_plan.md):
the first slice proved the faculty grounds prose to a SEEDED primitive; this one
closes the BEDROCK gap — everyday concepts (`agriculture`, `volcano`, …) don't
ground because their genus chain bottoms out below the math/psychology seeds.

The fix is the creator's: "if only it had a dictionary." It does — WordNet:
  • `seeds/lexical_ontology_roots.json` (the BEDROCK) — WordNet's unique-beginners
    (entity / abstraction / physical_entity / psychological_feature / attribute /
    object / group) as basis-primitive Concepts, is-a (built_from) edges mirroring
    WordNet hypernymy so every chain bottoms out at the single root `entity`.
    depends_on `grounding` (its built_from edges need the opened Γ productions).
  • `domains/wordnet_genus.py` — the dictionary reader. `hypernym_chain` walks
    WordNet's hypernym POINTERS from the dominant sense (sense-CONSISTENT: it
    carries the synset, so it never hops senses — `act` stays the action sense,
    not `legal_document`); `ChainReader` stages that ladder as a `_definition_feed`
    the agent reads. WordNet names the genus + the pointers; no meaning decision.

The agent reads the staged ladder, comprehends each genus, and its own grounding
recursion climbs `built_from` to the seeded root. No Python decides meaning.

Sense-consistency matters: naive per-word re-lookup (`read_definition` each link)
hops senses and ~20% wander past all 7 roots; pointer-following grounds the lot.

Multi-word lemmas (`body_of_water`) ground too: a WordNet lemma is ONE lexical
unit, so the reader keeps its underscore form and the genus tokenizer keeps
underscore INSIDE a token — the compound is read whole, not split on `of` (a
differentia marker) into the head `body`. The comprehension was already there
(the acquired-construction tokenizer kept `_`); the genus path was the
inconsistent one, now aligned.
"""
from __future__ import annotations

import pytest

import domains.seed_registry  # noqa: F401 — populates REGISTRY
from substrate.boot_core import CORE_SEEDS, load_seeds_into
from substrate.seeds import REGISTRY
from substrate.world_adapter import WorldAdapter
from domains.read_and_ground import read_and_ground, _is_held
from domains import grounded_representation as gr
from domains import wordnet_genus as wg


pytestmark = pytest.mark.skipif(
    not wg.present(), reason="WordNet corpus not installed")

_ROOTS = ["lexical_ontology_roots", "relations", "psychology"]


def _agent(*, with_roots: bool = True):
    wa = WorldAdapter(seeds=CORE_SEEDS)
    load_seeds_into(wa.s, wa.agent,
                    _ROOTS if with_roots else ["grounding", "relations", "psychology"])
    return wa


# ---------------------------------------------------------------------------
# the bedrock seed installs the WordNet roots as held basis primitives
# ---------------------------------------------------------------------------

def test_roots_seed_installs_held_primitives():
    wa = _agent()
    idx = gr._concept_by_name(wa.s)
    # entity is the single basis primitive (built_from nothing)
    eid = gr._find_concept(wa.s, "entity", idx)
    assert eid is not None and gr.is_primitive(wa.s, eid)
    assert _is_held(wa.s, "entity", index=idx)
    # the other tops are held via their built_from cone to entity
    for top in ("abstraction", "physical_entity", "attribute", "object", "group"):
        assert _is_held(wa.s, top, index=idx), top


def test_roots_seed_resolves_in_registry():
    closure = [s.id for s in REGISTRY.resolve(["lexical_ontology_roots"])]
    assert "lexical_ontology_roots" in closure
    assert "grounding" in closure          # the declared dependency is pulled


# ---------------------------------------------------------------------------
# the dictionary reader's sense-consistent ladder always reaches `entity`
# ---------------------------------------------------------------------------

def test_hypernym_chain_is_sense_consistent_to_entity():
    for word in ("agriculture", "volcano", "telescope", "democracy", "music"):
        chain = wg.hypernym_chain(word)
        assert chain and chain[0] == word
        assert chain[-1] == "entity", (word, chain)


def test_chain_feed_keys_both_surface_forms():
    feed = wg.chain_definition_feed("agriculture")
    # multi-word genera are keyed by BOTH space and underscore form (the descent
    # re-reads each genus by the underscore-normalised name the grounding minted)
    assert "commercial enterprise" in feed
    assert "commercial_enterprise" in feed


# ---------------------------------------------------------------------------
# end-to-end: everyday concepts ground to the seeded root via the dictionary
# ---------------------------------------------------------------------------

def test_everyday_concepts_ground_to_entity():
    wa = _agent()
    for word in ("agriculture", "volcano", "telescope", "democracy",
                 "photosynthesis", "engine", "music", "gravity"):
        res = read_and_ground(wa.s, word,
                              conversation=wg.ChainReader(word), max_depth=40)
        assert res["grounded"] is True, (word, res["reason"])
        assert "entity" in res["structure"]["primitives"], word


def test_multiword_of_genus_grounds_as_a_lexical_unit():
    """`river` / `ocean` climb through `body_of_water` — a WordNet lemma that is
    ONE lexical unit. It grounds whole (kept underscore, tokenizer keeps `_`),
    not split on `of` into the head `body` (which would wander off-chain)."""
    wa = _agent()
    # the chain carries the compound as a single token
    assert "body_of_water" in wg.hypernym_chain("river")
    for word in ("river", "ocean"):
        res = read_and_ground(wa.s, word,
                              conversation=wg.ChainReader(word), max_depth=40)
        assert res["grounded"] is True, (word, res["reason"])
        assert "entity" in res["structure"]["primitives"], word


def test_adjectives_ground_via_the_nominalization_bridge():
    """An adjective has no noun hypernym ladder; WordNet's own cross-references
    bridge it to its nominalization NOUN ('accurate' -> 'accuracy' -> 'quality'
    -> 'attribute' -> … -> entity), which the chain then climbs. So adjectives
    ground too — not just common nouns."""
    for word in ("accurate", "abundant", "random", "symmetric"):
        chain = wg.hypernym_chain(word)
        assert chain and chain[0] == word and chain[-1] == "entity", (word, chain)
    wa = _agent()
    for word in ("accurate", "abundant", "random", "symmetric"):
        res = read_and_ground(wa.s, word,
                              conversation=wg.ChainReader(word), max_depth=40)
        assert res["grounded"] is True, (word, res["reason"])
        assert "entity" in res["structure"]["primitives"], word


def test_lemmatization_and_verb_adverb_bridges_ground():
    """Inflected forms lemmatise ('enzymes' -> 'enzyme'); a VERB bridges to a
    derivationally-related noun ('observe' -> 'detection'); an ADVERB bridges
    through its adjective to a noun ('accurately' -> 'accuracy'). All then climb
    to entity, so they ground too — not only base-form nouns/adjectives."""
    for word in ("enzymes", "observe", "transmit", "accurately", "achieved"):
        chain = wg.hypernym_chain(word)
        assert chain and chain[0] == word and chain[-1] == "entity", (word, chain)
    wa = _agent()
    for word in ("enzymes", "observe", "transmit", "accurately", "achieved"):
        res = read_and_ground(wa.s, word,
                              conversation=wg.ChainReader(word), max_depth=40)
        assert res["grounded"] is True, (word, res["reason"])


def test_adjectives_without_a_direct_nominalisation_ground():
    """Adjectives WordNet can't bridge directly still ground: via a derivational
    VERB ('adaptive' -> 'adapt' -> 'adaptation'), a PERTAINYM noun
    ('administrative' -> 'administration'), or MORPHOLOGICAL de-suffixing to a
    held noun ('additional' -> 'addition', 'adversarial' -> 'adversary' — the
    latter not even in WordNet as an adjective)."""
    for word in ("adaptive", "additional", "administrative", "adversarial"):
        chain = wg.hypernym_chain(word)
        assert chain and chain[0] == word and chain[-1] == "entity", (word, chain)
    wa = _agent()
    for word in ("adaptive", "additional", "administrative", "adversarial"):
        res = read_and_ground(wa.s, word,
                              conversation=wg.ChainReader(word), max_depth=40)
        assert res["grounded"] is True, (word, res["reason"])


def test_bedrock_seed_is_load_bearing():
    """Without the roots seed the SAME dictionary descent comprehends the chain
    but never bottoms out at a held primitive — the seed is the floor."""
    word = "volcano"
    with_roots = read_and_ground(_agent(with_roots=True).s, word,
                                 conversation=wg.ChainReader(word), max_depth=40)
    without = read_and_ground(_agent(with_roots=False).s, word,
                              conversation=wg.ChainReader(word), max_depth=40)
    assert with_roots["grounded"] is True
    assert without["grounded"] is False

"""Gate for relation_grounding.ground_relations — the ANTI-HALLUCINATION
relation-derivation pass.

Domain concepts hold NO telic/constitutive/agentive edges (those qualia axes are
DARK). Their functional/part/causal meaning is written in the author-supplied
`definition` + `why` prose. `ground_relations` reads that prose, finds a relation
CUE (used for / part of / causes / …), extracts the object phrase, and RESOLVES
it to a REAL HELD Concept — emitting the typed edge ONLY when the object grounds.

The load-bearing property is the GATE: an object that does not resolve to a held
Concept is DROPPED (no edge, no invented node). A prior general extractor grounded
args to the nearest RAW TOKEN ('CPUs constitutes wide') — fabrication these gates
forbid. Copula 'is/are' => genus => `genls` (FORMAL role), NEVER `constitutes`.

These gates pin exactly that:
  1. an edge is emitted ONLY when the object grounds to a held Concept;
  2. an object that does NOT ground is dropped — no edge, no new node minted;
  3. the copula genus routes to `genls` (formal), never to `constitutes`;
  4. the predicate -> edge_type map lands on the seeded lexical roles
     (used_for->telic, part_of->constitutive, causes->agentive);
  5. the pass is idempotent (re-running adds no duplicate edge);
  6. `mt_name` scopes the pass to one microtheory;
  7. a bare adjective genus ('shared') does NOT leap to a held compound whose
     tail it matches ('false_sharing') — the resolver refuses that fabrication;
  8. the emitted edge becomes an edge-derived lexical:telic/constitutive/agentive
     coordinate in the concept's qualia signature.
"""
from __future__ import annotations

import json
import pathlib

from substrate_rs import _native

import domains.analogical_thinking as at
import domains.analogy_search as asr
import domains.relation_grounding as rg

ROOT = pathlib.Path(at.__file__).resolve().parent.parent
VOCAB = ROOT / "seeds" / "shape_vocabulary.json"
QUALIA = ROOT / "seeds" / "qualia_space.json"

_NT = ("Agent", "Concept", "Microtheory", "QualiaDimension",
       "DimensionEdgeRole")
# every relational edge the pass may emit + the grounding/support edges.
_ET = tuple(set(rg.RELATION_EDGE_TYPES) | {
    "has_concept", "genls", "is_a", "built_from", "depends_on", "grounds"})


def _open(s):
    for a in _NT:
        for b in _NT:
            for et in _ET:
                s.add_production({"src": {"type": a, "var": "x"},
                                  "edge_type": et, "tgt": {"type": b, "var": "y"},
                                  "where": None,
                                  "weight": {"type": "Lit", "value": 1.0},
                                  "provenance": "test:open"})


def _substrate(*, with_qualia: bool = False):
    s = _native.Substrate()
    for cache in (at._CONCEPT_READING_CACHE, at._VOCAB_KEYS_CACHE,
                  at._METASHAPE_COUNT_CACHE, asr._QUALIA_SCHEMA_CACHE):
        cache.clear()
    ag = s.add_node("Agent", {})
    _open(s)
    if with_qualia:
        for path in (VOCAB, QUALIA):
            s.load_seed_manifest(json.load(open(path)), ag)
    return s, ag


def _mt(s, name):
    return s.add_node("Microtheory", {"name": name})


def _concept(s, mt, name, **attrs):
    a = {"name": name}
    a.update(attrs)
    c = s.add_node("Concept", a)
    s.add_edge(mt, "has_concept", c)
    return c


def _emitted(res):
    return set(res["emitted"])


# ---------------------------------------------------------------------------
# 1. an edge is emitted ONLY when the object grounds to a held concept
# ---------------------------------------------------------------------------
def test_edge_emitted_when_target_grounds():
    s, _ag = _substrate()
    mt = _mt(s, "m")
    # 'refresh' resolves (head noun) to the held DRAM_refresh concept.
    dram = _concept(s, mt, "DRAM",
                    definition="Main memory that requires periodic refresh.")
    _concept(s, mt, "DRAM_refresh", definition="Rewrites each row to keep data.")

    res = rg.ground_relations(s, "m")
    # 'requires' -> depends_on (agentive); object 'periodic refresh' -> DRAM_refresh.
    assert ("DRAM", "depends_on", "DRAM_refresh") in _emitted(res)
    tgt = rg._concept_by_name(s)["DRAM_refresh"]
    assert tgt in set(s.neighbours(dram, "depends_on"))
    assert res["agentive"] >= 1


# ---------------------------------------------------------------------------
# 2. an object that does NOT ground is dropped — no edge, no new node minted
# ---------------------------------------------------------------------------
def test_ungrounded_object_dropped_and_no_node_minted():
    s, _ag = _substrate()
    mt = _mt(s, "m")
    isa = _concept(s, mt, "instruction_set_architecture",
                   definition="ISA is the contract.",
                   why="Different ISAs require recompilation or emulation.")

    names_before = set(rg._concept_by_name(s).keys())
    node_count_before = s.node_count()

    res = rg.ground_relations(s, "m")
    # 'requires' cue with object 'recompilation' — NOT a held concept => dropped.
    assert res["edges_added"] == 0
    assert _emitted(res) == set()
    # the dropped candidate is recorded (honest ledger), object phrase kept raw.
    assert any(et == "depends_on" and "recompilation" in obj
               for (_src, et, obj) in res["dropped"])
    # NO new concept node was minted for the ungrounded object.
    assert s.node_count() == node_count_before
    assert set(rg._concept_by_name(s).keys()) == names_before
    # the concept gained NO outgoing relational edge.
    assert list(s.neighbours(isa, "depends_on")) == []


# ---------------------------------------------------------------------------
# 3. copula genus routes to genls (formal), NEVER to constitutes
# ---------------------------------------------------------------------------
def test_copula_genus_routes_to_genls_not_constitutes():
    s, _ag = _substrate()
    mt = _mt(s, "m")
    # 'A cache is a memory ...' — genus 'memory' is a HELD concept.
    cache = _concept(s, mt, "cache",
                     definition="A cache is a memory holding recently-used data.")
    _concept(s, mt, "memory", definition="Storage for data.")

    res = rg.ground_relations(s, "m")
    assert ("cache", "genls", "memory") in _emitted(res)
    mem = rg._concept_by_name(s)["memory"]
    assert mem in set(s.neighbours(cache, "genls"))
    # the copula must NOT have produced a constitutes/has_part edge.
    assert list(s.neighbours(cache, "constitutes")) == []
    assert list(s.neighbours(cache, "has_part")) == []
    # no emitted edge is ever 'constitutes'.
    assert all(et != "constitutes" for (_s, et, _t) in res["emitted"])


# ---------------------------------------------------------------------------
# 4. predicate -> edge_type lands on the seeded lexical roles
# ---------------------------------------------------------------------------
def test_predicate_maps_to_correct_lexical_role():
    s, _ag = _substrate()
    mt = _mt(s, "m")
    # TELIC: 'used for' -> used_for
    _concept(s, mt, "widget", definition="A widget used for buffering.")
    _concept(s, mt, "buffering", definition="Holding data in transit.")
    # CONSTITUTIVE: 'contains' -> contains
    _concept(s, mt, "unit", definition="The unit contains a latch.")
    _concept(s, mt, "latch", definition="A storage element.")
    # AGENTIVE: 'causes' -> causes
    _concept(s, mt, "hazard", definition="A hazard causes a stall.")
    _concept(s, mt, "stall", definition="A pipeline bubble.")

    res = rg.ground_relations(s, "m")
    em = _emitted(res)
    assert ("widget", "used_for", "buffering") in em     # telic
    assert ("unit", "contains", "latch") in em           # constitutive
    assert ("hazard", "causes", "stall") in em           # agentive
    assert res["telic"] >= 1
    assert res["constitutive"] >= 1
    assert res["agentive"] >= 1


# ---------------------------------------------------------------------------
# 5. idempotent
# ---------------------------------------------------------------------------
def test_pass_is_idempotent():
    s, _ag = _substrate()
    mt = _mt(s, "m")
    hazard = _concept(s, mt, "hazard", definition="A hazard causes a stall.")
    _concept(s, mt, "stall", definition="A pipeline bubble.")

    first = rg.ground_relations(s, "m")
    assert first["edges_added"] >= 1
    again = rg.ground_relations(s, "m")
    assert again["edges_added"] == 0  # no duplicate edges
    # exactly one 'causes' edge.
    assert len(set(s.neighbours(hazard, "causes"))) == 1


# ---------------------------------------------------------------------------
# 6. mt_name scopes the pass to one microtheory
# ---------------------------------------------------------------------------
def test_mt_scope_restricts_the_pass():
    s, _ag = _substrate()
    m1, m2 = _mt(s, "m1"), _mt(s, "m2")
    h1 = _concept(s, m1, "hazard", definition="A hazard causes a stall.")
    _concept(s, m1, "stall", definition="A bubble.")
    h2 = _concept(s, m2, "fault", definition="A fault causes a trap.")
    _concept(s, m2, "trap", definition="An exception.")

    res = rg.ground_relations(s, "m1")
    assert res["mt"] == "m1"
    assert set(s.neighbours(h1, "causes"))          # m1 wired
    assert list(s.neighbours(h2, "causes")) == []   # m2 untouched


# ---------------------------------------------------------------------------
# 7. a bare adjective genus does not leap to a compound whose tail it matches
# ---------------------------------------------------------------------------
def test_adjective_genus_does_not_fabricate_head_noun_target():
    s, _ag = _substrate()
    mt = _mt(s, "m")
    # 'execute units are shared' -> genus 'shared'. There is a held 'false_sharing'
    # whose head noun stems to 'share'. The genus must NOT resolve to it.
    smt = _concept(s, mt, "smt",
                   definition="Execute units are shared.")
    _concept(s, mt, "false_sharing", definition="Two cores share a line.")

    res = rg.ground_relations(s, "m")
    # no genls edge to false_sharing was fabricated.
    assert ("smt", "genls", "false_sharing") not in _emitted(res)
    fs = rg._concept_by_name(s)["false_sharing"]
    assert fs not in set(s.neighbours(smt, "genls"))


# ---------------------------------------------------------------------------
# 8. emitted edge becomes an edge-derived lexical:telic coordinate
# ---------------------------------------------------------------------------
def test_edge_enriches_lexical_qualia_signature():
    s, _ag = _substrate(with_qualia=True)
    mt = _mt(s, "m")
    widget = _concept(s, mt, "widget", definition="A widget used for buffering.")
    _concept(s, mt, "buffering", definition="Holding data in transit.")

    before = asr.concept_signature(s, widget)
    assert not any(pred == "used_for" for _dim, pred, _val in before)

    rg.ground_relations(s, "m")
    asr._QUALIA_SCHEMA_CACHE.clear()
    after = asr.concept_signature(s, widget)
    # a used_for edge coordinate, on the TELIC lexical dimension.
    assert ("lexical:telic", "used_for", "concept") in after
    assert len(after) > len(before)



# ---------------------------------------------------------------------------
# 9. an acronym<->expansion name-variant object RESOLVES to the held concept
#    (a FAITHFUL false-negative recovery — the object names an ALREADY-HELD
#    concept under a variant the earlier ladder missed, minting nothing new).
# ---------------------------------------------------------------------------
def test_acronym_expansion_variant_resolves_and_emits():
    s, _ag = _substrate()
    mt = _mt(s, "m")

    # (a) acronym-COMPOUND held; prose names its EXPANSION as the object.
    #     'contains the memory management unit' -> the held
    #     'MMU_memory_management_unit' (contains => constitutive).
    cpu = _concept(s, mt, "cpu",
                   definition="A processor that contains the memory management unit.")
    _concept(s, mt, "MMU_memory_management_unit",
             definition="Hardware doing virtual-to-physical translation.")

    # (b) plain EXPANSION held; prose names it by its ACRONYM (initialism).
    #     'depends on the TLB' -> the held 'translation_lookaside_buffer'
    #     (depends on => agentive). Neither the object 'the TLB' nor the
    #     expansion order the earlier exact/stem/head ladder resolved.
    walk = _concept(s, mt, "page_walk",
                    definition="Address translation. The walk depends on the TLB.")
    _concept(s, mt, "translation_lookaside_buffer",
             definition="A cache of address translations.")

    names_before = set(rg._concept_by_name(s).keys())
    node_count_before = s.node_count()

    res = rg.ground_relations(s, "m")
    em = _emitted(res)
    # both acronym<->expansion variants recovered onto their HELD concept.
    assert ("cpu", "contains", "MMU_memory_management_unit") in em
    assert ("page_walk", "depends_on", "translation_lookaside_buffer") in em
    # the edges land on the real held nodes.
    idx = rg._concept_by_name(s)
    assert idx["MMU_memory_management_unit"] in set(s.neighbours(cpu, "contains"))
    assert idx["translation_lookaside_buffer"] in set(
        s.neighbours(walk, "depends_on"))
    # STILL FAITHFUL: no new node minted, held name set unchanged.
    assert s.node_count() == node_count_before
    assert set(rg._concept_by_name(s).keys()) == names_before


# ---------------------------------------------------------------------------
# 10. an AMBIGUOUS acronym / expansion variant (claimed by 2+ held concepts) and
#     an UNGROUNDED variant (no held concept) both still DROP — the acronym step
#     never loosens the gate into a fabrication.
# ---------------------------------------------------------------------------
def test_ambiguous_or_ungrounded_acronym_variant_still_drops():
    s, _ag = _substrate()
    mt = _mt(s, "m")

    # AMBIGUOUS: two held plain expansions share the initialism 'mmu'. An object
    # 'the MMU' must NOT resolve to either — an alias claimed by 2+ held concepts
    # is dropped from the acronym map, so the candidate drops.
    ref = _concept(s, mt, "reference",
                   definition="A reference. It depends on the MMU.")
    _concept(s, mt, "memory_management_unit", definition="Address translation HW.")
    _concept(s, mt, "multi_media_unit", definition="A media coprocessor.")

    # UNGROUNDED: an acronym whose expansion is not a held concept at all.
    _concept(s, mt, "widget",
             definition="A widget. It requires the flux capacitor coil.")

    node_count_before = s.node_count()
    names_before = set(rg._concept_by_name(s).keys())

    res = rg.ground_relations(s, "m")
    em = _emitted(res)
    # neither ambiguous claimant was wired.
    assert ("reference", "depends_on", "memory_management_unit") not in em
    assert ("reference", "depends_on", "multi_media_unit") not in em
    idx = rg._concept_by_name(s)
    assert idx["memory_management_unit"] not in set(s.neighbours(ref, "depends_on"))
    assert idx["multi_media_unit"] not in set(s.neighbours(ref, "depends_on"))
    # the ambiguous + ungrounded candidates are recorded as honest drops.
    assert any("mmu" in obj.lower() for (_s, _et, obj) in res["dropped"])
    # gate held: nothing minted.
    assert s.node_count() == node_count_before
    assert set(rg._concept_by_name(s).keys()) == names_before

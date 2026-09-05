"""Gate for relation_grounding.mint_referents_from_relations — the OTHER half of
the sparse-relational-witness problem.

ground_relations DROPS an object phrase whose referent is genuinely NOT a held
Concept, even when it is a real, nameable thing the corpus talks about ('a cache
requires periodic refresh', 'IOMMU used for VM passthrough'). If those referents
WERE held, the relation would ground and the relational qualia axes would light
up. The FAITHFUL move (mirroring grounded_representation.ground_categories, which
mints category:<value> hubs and wires genls to them): MINT the missing referent
as a real Concept when it passes a REAL-REFERENT test, then let the SAME relation
cue wire the edge to it — so the target IS held and ground_relations' gate is
satisfied HONESTLY, not bypassed.

The load-bearing property is the MINT GATE: a clean short noun phrase (head is a
noun) gets minted + wired (the edge now grounds); a clause / verb-led / stopword
/ adjective-genus phrase is REFUSED (not minted, still dropped) — the refusal is
the gate refusing to fabricate a garbage 'concept'. And the pass is idempotent.

These gates pin exactly that:
  1. a clean NP object gets minted as a Concept + the relation edge is wired
     (the edge now grounds; the minted concept carries minted_referent + a
     definition);
  2. a clause / verb-led object is REFUSED — not minted, still dropped, no node;
  3. a bare stopword / pronoun object is REFUSED;
  4. an adjective-genus / verb-dominant single word is REFUSED (a quality/action,
     not a thing);
  5. the copula-genus (genls) route is NEVER minted (a genus is an is-a parent,
     not a relation object — minting from it would inject a false taxonomy);
  6. an object that ALREADY resolves to a held concept is not re-minted (that is
     ground_relations' job) — the pass mints only the genuinely-unheld referent;
  7. the pass is idempotent — a second run mints nothing new and adds no edge;
  8. mint-vs-refuse counts are reported (the refusal proves the gate is real);
  9. after mint, re-running ground_relations GROUNDS the edge to the now-held
     referent (the whole point: previously-ungroundable is now grounded);
 10. the minted referent lights the SOURCE's relational qualia axis (the edge is
     an edge-derived lexical:telic/agentive coordinate).
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


def _names(s):
    return set(rg._concept_by_name(s).keys())


# ---------------------------------------------------------------------------
# 1. a clean NP object gets minted + the relation edge is wired
# ---------------------------------------------------------------------------
def test_clean_np_object_is_minted_and_wired():
    s, _ag = _substrate()
    mt = _mt(s, "m")
    # 'VM passthrough' is a clean 2-word NP (head 'passthrough' is a noun) that is
    # NOT a held concept -> ground_relations drops it -> the mint pass mints it.
    iommu = _concept(s, mt, "IOMMU",
                     definition="An IOMMU is used for VM passthrough.")

    before = _names(s)
    res = rg.mint_referents_from_relations(s, "m")

    assert res["minted"] >= 1
    # a Concept named for the normalised phrase now exists.
    assert "vm_passthrough" in _names(s)
    assert "vm_passthrough" not in before
    ref = rg._concept_by_name(s)["vm_passthrough"]
    a = s.node(ref)["attrs"]
    assert a.get("minted_referent") is True
    assert a.get("definition") == "vm passthrough"
    # the used_for edge is wired from IOMMU to the minted referent (grounds now).
    assert ref in set(s.neighbours(iommu, "used_for"))
    assert ("IOMMU", "used_for", "vm_passthrough") in res["wired"]


# ---------------------------------------------------------------------------
# 2. a clause / verb-led object is REFUSED — not minted, still dropped, no node
# ---------------------------------------------------------------------------
def test_clause_object_is_refused_and_no_node_minted():
    s, _ag = _substrate()
    mt = _mt(s, "m")
    # 'enables programs to use more virtual memory' -> object span is a CLAUSE
    # ('programs use more virtual memory'); its head is verb-led -> REFUSE.
    pf = _concept(s, mt, "page_fault",
                  definition="A page fault enables programs use more virtual memory.")

    before = _names(s)
    node_count_before = s.node_count()
    res = rg.mint_referents_from_relations(s, "m")

    # nothing minted for the clause; the phrase is recorded as refused.
    assert "virtual_memory" not in (_names(s) - before)
    assert s.node_count() == node_count_before
    assert _names(s) == before
    assert any(et == "enables" and "virtual memory" in ph
               for (_src, et, ph) in res["refused_phrases"])
    # page_fault gained no outgoing enables edge.
    assert list(s.neighbours(pf, "enables")) == []


# ---------------------------------------------------------------------------
# 3. a bare stopword / pronoun object is REFUSED
# ---------------------------------------------------------------------------
def test_stopword_object_is_refused():
    s, _ag = _substrate()
    mt = _mt(s, "m")
    # 'depends on this' -> object 'this' is a pronoun -> never a referent.
    c = _concept(s, mt, "thing", definition="A thing depends on this.")

    before = _names(s)
    res = rg.mint_referents_from_relations(s, "m")

    assert _names(s) == before                 # nothing minted
    assert list(s.neighbours(c, "depends_on")) == []
    assert res["minted"] == 0


# ---------------------------------------------------------------------------
# 4. an adjective-genus / verb-dominant single word is REFUSED
# ---------------------------------------------------------------------------
def test_verb_dominant_single_word_is_refused():
    s, _ag = _substrate()
    mt = _mt(s, "m")
    # 'depends on refresh' -> 'refresh' is verb-DOMINANT (a quality/action name),
    # so the bright-line noun-dominant-head rule refuses it. Contrast test 1's
    # 'passthrough' (noun-dominant).
    c = _concept(s, mt, "gadget", definition="A gadget depends on refresh.")

    before = _names(s)
    res = rg.mint_referents_from_relations(s, "m")

    assert "refresh" not in (_names(s) - before)
    assert list(s.neighbours(c, "depends_on")) == []
    assert any(et == "depends_on" and "refresh" in ph
               for (_src, et, ph) in res["refused_phrases"])


# ---------------------------------------------------------------------------
# 5. the copula-genus (genls) route is NEVER minted
# ---------------------------------------------------------------------------
def test_copula_genus_is_never_minted():
    s, _ag = _substrate()
    mt = _mt(s, "m")
    # 'A decode_stage is complex' -> genus 'complex' (an adjective) drops in
    # ground_relations as a genls candidate. The mint pass must NOT mint it: a
    # genus is an is-a parent, not a relation object.
    ds = _concept(s, mt, "decode_stage", definition="A decode_stage is complex.")

    before = _names(s)
    res = rg.mint_referents_from_relations(s, "m")

    assert "complex" not in (_names(s) - before)
    assert list(s.neighbours(ds, "genls")) == []
    # no minted name is 'complex'; no wired edge is a genls edge.
    assert "complex" not in res["minted_names"]
    assert all(et != "genls" for (_src, et, _n) in res["wired"])


# ---------------------------------------------------------------------------
# 6. an object that ALREADY resolves to a held concept is not re-minted
# ---------------------------------------------------------------------------
def test_already_held_object_is_not_reminted():
    s, _ag = _substrate()
    mt = _mt(s, "m")
    # 'a hazard causes a stall' — 'stall' IS a held concept, so ground_relations
    # already wires it; the mint pass must not mint a duplicate.
    hazard = _concept(s, mt, "hazard", definition="A hazard causes a stall.")
    _concept(s, mt, "stall", definition="A pipeline bubble.")

    before = _names(s)
    res = rg.mint_referents_from_relations(s, "m")

    assert "stall" not in res["minted_names"]
    assert _names(s) == before                       # no new node
    # ground_relations (run inside the pass) grounded the causes edge to stall.
    stall = rg._concept_by_name(s)["stall"]
    assert stall in set(s.neighbours(hazard, "causes"))


# ---------------------------------------------------------------------------
# 7. idempotent — a second run mints nothing new and adds no edge
# ---------------------------------------------------------------------------
def test_mint_pass_is_idempotent():
    s, _ag = _substrate()
    mt = _mt(s, "m")
    iommu = _concept(s, mt, "IOMMU",
                     definition="An IOMMU is used for VM passthrough.")

    first = rg.mint_referents_from_relations(s, "m")
    assert first["minted"] >= 1
    names_after_first = _names(s)
    node_count_after_first = s.node_count()

    second = rg.mint_referents_from_relations(s, "m")
    assert second["minted"] == 0
    assert second["edges_added"] == 0
    assert _names(s) == names_after_first
    assert s.node_count() == node_count_after_first
    # exactly one used_for edge to the referent.
    ref = rg._concept_by_name(s)["vm_passthrough"]
    assert list(s.neighbours(iommu, "used_for")).count(ref) == 1


# ---------------------------------------------------------------------------
# 8. mint-vs-refuse counts are reported (the refusal proves the gate is real)
# ---------------------------------------------------------------------------
def test_mint_and_refuse_counts_reported():
    s, _ag = _substrate()
    mt = _mt(s, "m")
    # one clean NP (minted) + one clause (refused).
    _concept(s, mt, "IOMMU", definition="An IOMMU is used for VM passthrough.")
    _concept(s, mt, "page_fault",
             definition="A page fault enables programs use more virtual memory.")

    res = rg.mint_referents_from_relations(s, "m")
    assert res["minted"] >= 1
    assert res["refused"] >= 1
    total = res["minted"] + res["refused"]
    assert res["refusal_rate"] == res["refused"] / total
    assert 0.0 < res["refusal_rate"] < 1.0


# ---------------------------------------------------------------------------
# 9. after mint, re-running ground_relations GROUNDS the edge to the referent
# ---------------------------------------------------------------------------
def test_reground_after_mint_grounds_previously_dropped_edge():
    s, _ag = _substrate()
    mt = _mt(s, "m")
    _concept(s, mt, "IOMMU", definition="An IOMMU is used for VM passthrough.")

    # BEFORE mint: ground_relations drops the object (no held concept).
    gr_before = rg.ground_relations(s, "m")
    assert ("IOMMU", "used_for", "vm_passthrough") not in set(gr_before["emitted"])
    assert any(et == "used_for" and "passthrough" in ph.lower()
               for (_src, et, ph) in gr_before["dropped"])

    rg.mint_referents_from_relations(s, "m")

    # AFTER mint: the referent is held, so ground_relations now GROUNDS the edge.
    gr_after = rg.ground_relations(s, "m")
    assert ("IOMMU", "used_for", "vm_passthrough") in set(gr_after["emitted"])
    assert gr_after["telic"] >= 1


# ---------------------------------------------------------------------------
# 10. the minted referent lights the SOURCE's relational qualia axis
# ---------------------------------------------------------------------------
def test_minted_edge_enriches_source_relational_qualia():
    s, _ag = _substrate(with_qualia=True)
    mt = _mt(s, "m")
    iommu = _concept(s, mt, "IOMMU",
                     definition="An IOMMU is used for VM passthrough.")

    before = asr.concept_signature(s, iommu)
    assert not any(pred == "used_for" for _dim, pred, _val in before)

    rg.mint_referents_from_relations(s, "m")
    asr._QUALIA_SCHEMA_CACHE.clear()
    after = asr.concept_signature(s, iommu)
    # a used_for edge coordinate on the TELIC lexical dimension of the SOURCE.
    assert ("lexical:telic", "used_for", "concept") in after
    assert len(after) > len(before)



# ===========================================================================
# MINT GATE POLICY — the gate's strictness is a GRAPH-RESIDENT, tuneable knob
# (a singleton MintPolicy node), not a hard-coded Python constant. These pin:
#   · the DEFAULT policy (minted-if-absent, or absent entirely) reproduces
#     TODAY's behaviour EXACTLY — a clause still refused, a clean NP still minted;
#   · a PERMISSIVE policy (require_noun_dominant_head=False) admits a genuine
#     verb-DOMINANT-but-nominal referent ('periodic refresh') the default refuses;
#   · a STRICTER policy (min_recurrence=2 / max_content_words=1) refuses something
#     the default accepts;
#   · ensure_mint_policy is idempotent + off-by-default-equivalent (a fresh graph
#     with no node, and a graph with a freshly-minted default node, behave the
#     SAME as today — the auto_approve off-by-default discipline).
# ===========================================================================


# ---------------------------------------------------------------------------
# 11. ensure_mint_policy is idempotent AND its defaults == today
# ---------------------------------------------------------------------------
def test_ensure_mint_policy_idempotent_and_defaults_equal_today():
    s, _ag = _substrate()

    # a FRESH graph has NO MintPolicy node — the mint pass reads it as all-safe-
    # defaults WITHOUT minting one (off-by-default: nothing added to the graph).
    assert list(s.nodes("MintPolicy")) == []
    # the non-minting read still yields the safe defaults == today.
    assert rg.mint_gate_params(s, ensure=False) == {
        "min_recurrence": 1, "max_content_words": 3,
        "require_noun_dominant_head": True,
    }
    # still no node minted by a non-ensure read.
    assert list(s.nodes("MintPolicy")) == []

    # ensure mints exactly ONE node, with the safe defaults (== today).
    n1 = rg.ensure_mint_policy(s)
    assert n1 is not None
    assert len(list(s.nodes("MintPolicy"))) == 1
    params = rg.mint_gate_params(s)
    assert params == {"min_recurrence": 1, "max_content_words": 3,
                      "require_noun_dominant_head": True}
    assert params == dict(rg.MINT_POLICY_DEFAULTS)

    # idempotent: a second ensure returns the SAME node, mints no second one.
    n2 = rg.ensure_mint_policy(s)
    assert n2 == n1
    assert len(list(s.nodes("MintPolicy"))) == 1


# ---------------------------------------------------------------------------
# 12. the DEFAULT policy reproduces today: clean NP minted, clause refused,
#     and minting adds NO MintPolicy node (off-by-default graph shape invariant)
# ---------------------------------------------------------------------------
def test_default_policy_reproduces_today_and_mints_no_policy_node():
    s, _ag = _substrate()
    mt = _mt(s, "m")
    iommu = _concept(s, mt, "IOMMU",
                     definition="An IOMMU is used for VM passthrough.")
    _concept(s, mt, "page_fault",
             definition="A page fault enables programs use more virtual memory.")

    node_count_before = s.node_count()
    res = rg.mint_referents_from_relations(s, "m")

    # clean NP minted, clause refused — exactly as before the gate was tuneable.
    assert "vm_passthrough" in _names(s)
    ref = rg._concept_by_name(s)["vm_passthrough"]
    assert ref in set(s.neighbours(iommu, "used_for"))
    assert any(et == "enables" and "virtual memory" in ph
               for (_src, et, ph) in res["refused_phrases"])
    # the reported effective gate is the safe default (== today).
    assert res["gate"] == {"min_recurrence": 1, "max_content_words": 3,
                           "require_noun_dominant_head": True}
    # OFF-BY-DEFAULT graph invariant: a default run mints the referent Concept
    # but NO MintPolicy node — the only new node is the minted referent, so the
    # graph shape is identical to the pre-policy behaviour save the real mint.
    assert list(s.nodes("MintPolicy")) == []
    assert s.node_count() == node_count_before + 1   # just the vm_passthrough Concept


# ---------------------------------------------------------------------------
# 13. a PERMISSIVE policy admits a verb-DOMINANT-but-nominal referent that the
#     default refuses ('periodic refresh' — head 'refresh' is verb-dominant)
# ---------------------------------------------------------------------------
def test_permissive_policy_admits_verb_dominant_nominal_referent():
    # DEFAULT: 'a cache requires periodic refresh' -> object 'periodic refresh',
    # head 'refresh' is VERB-dominant -> the bright-line noun-dominance rule
    # REFUSES it (today's behaviour).
    s_def, _ = _substrate()
    mt = _mt(s_def, "m")
    _concept(s_def, mt, "cache",
             definition="A cache requires periodic refresh.")
    before = _names(s_def)
    res_def = rg.mint_referents_from_relations(s_def, "m")
    assert "periodic_refresh" not in (_names(s_def) - before)
    assert any(et == "depends_on" and "periodic refresh" in ph
               for (_src, et, ph) in res_def["refused_phrases"])

    # PERMISSIVE: tune the graph-resident MintPolicy to relax noun-dominance to
    # 'noun in head_pos'. The SAME phrase is now ADMITTED (a genuine nominal
    # referent — the DRAM periodic-refresh operation — recovered).
    s_perm, _ = _substrate()
    mt2 = _mt(s_perm, "m")
    cache2 = _concept(s_perm, mt2, "cache",
                      definition="A cache requires periodic refresh.")
    # tune via the graph-resident policy writer (mint-if-absent + set attr).
    params = rg.set_mint_gate(s_perm, require_noun_dominant_head=False)
    assert params["require_noun_dominant_head"] is False
    # the tuned value is graph-resident: a fresh read sees it.
    assert rg.mint_gate_params(s_perm)["require_noun_dominant_head"] is False

    res_perm = rg.mint_referents_from_relations(s_perm, "m")
    assert "periodic_refresh" in _names(s_perm)
    ref = rg._concept_by_name(s_perm)["periodic_refresh"]
    a = s_perm.node(ref)["attrs"]
    assert a.get("minted_referent") is True
    assert a.get("definition") == "periodic refresh"
    # the depends_on edge is wired from cache to the newly-held referent.
    assert ref in set(s_perm.neighbours(cache2, "depends_on"))
    assert ("cache", "depends_on", "periodic_refresh") in res_perm["wired"]
    # the reported gate reflects the tuned policy.
    assert res_perm["gate"]["require_noun_dominant_head"] is False
    # the dial genuinely moved recall: permissive minted MORE than default.
    assert res_perm["minted"] > res_def["minted"]


# ---------------------------------------------------------------------------
# 14. a STRICTER policy (max_content_words=1) refuses a clean 2-word NP the
#     default accepts
# ---------------------------------------------------------------------------
def test_stricter_max_content_words_refuses_what_default_accepts():
    # DEFAULT accepts the clean 2-word NP 'VM passthrough'.
    s_def, _ = _substrate()
    mt = _mt(s_def, "m")
    _concept(s_def, mt, "IOMMU",
             definition="An IOMMU is used for VM passthrough.")
    res_def = rg.mint_referents_from_relations(s_def, "m")
    assert "vm_passthrough" in _names(s_def)
    assert res_def["minted"] >= 1

    # STRICTER: max_content_words=1 -> a 2-word NP is now 'too long' -> REFUSED.
    s_strict, _ = _substrate()
    mt2 = _mt(s_strict, "m")
    iommu = _concept(s_strict, mt2, "IOMMU",
                     definition="An IOMMU is used for VM passthrough.")
    rg.set_mint_gate(s_strict, max_content_words=1)
    before = _names(s_strict)
    res_strict = rg.mint_referents_from_relations(s_strict, "m")
    assert "vm_passthrough" not in (_names(s_strict) - before)
    assert list(s_strict.neighbours(iommu, "used_for")) == []
    assert res_strict["gate"]["max_content_words"] == 1
    assert any(et == "used_for" and "passthrough" in ph.lower()
               for (_src, et, ph) in res_strict["refused_phrases"])


# ---------------------------------------------------------------------------
# 15. a STRICTER policy (min_recurrence=2) refuses a referent seen only once
# ---------------------------------------------------------------------------
def test_stricter_min_recurrence_refuses_single_sighting():
    # DEFAULT (min_recurrence=1) accepts 'VM passthrough' on first sight.
    s_def, _ = _substrate()
    mt = _mt(s_def, "m")
    _concept(s_def, mt, "IOMMU",
             definition="An IOMMU is used for VM passthrough.")
    assert rg.mint_referents_from_relations(s_def, "m")["minted"] >= 1

    # STRICTER: min_recurrence=2 -> a referent seen ONCE fails the recurrence
    # gate and is refused.
    s_strict, _ = _substrate()
    mt2 = _mt(s_strict, "m")
    iommu = _concept(s_strict, mt2, "IOMMU",
                     definition="An IOMMU is used for VM passthrough.")
    rg.set_mint_gate(s_strict, min_recurrence=2)
    before = _names(s_strict)
    res = rg.mint_referents_from_relations(s_strict, "m")
    assert "vm_passthrough" not in (_names(s_strict) - before)
    assert list(s_strict.neighbours(iommu, "used_for")) == []
    assert res["gate"]["min_recurrence"] == 2


# ---------------------------------------------------------------------------
# 16. a per-call gate_params override tunes strictness without touching the node,
#     and the back-compat min_recurrence= kwarg still overrides that one knob
# ---------------------------------------------------------------------------
def test_per_call_override_and_backcompat_min_recurrence():
    # per-call gate_params override (permissive) admits 'periodic refresh'
    # WITHOUT minting/tuning a MintPolicy node.
    s, _ = _substrate()
    mt = _mt(s, "m")
    _concept(s, mt, "cache", definition="A cache requires periodic refresh.")
    res = rg.mint_referents_from_relations(
        s, "m", gate_params={"require_noun_dominant_head": False})
    assert "periodic_refresh" in _names(s)
    assert res["gate"]["require_noun_dominant_head"] is False
    assert list(s.nodes("MintPolicy")) == []      # override did not mint a node

    # back-compat: the long-standing min_recurrence= kwarg still overrides just
    # that knob (a single sighting fails at min_recurrence=2).
    s2, _ = _substrate()
    mt2 = _mt(s2, "m")
    _concept(s2, mt2, "IOMMU", definition="An IOMMU is used for VM passthrough.")
    before = _names(s2)
    res2 = rg.mint_referents_from_relations(s2, "m", min_recurrence=2)
    assert "vm_passthrough" not in (_names(s2) - before)
    assert res2["gate"]["min_recurrence"] == 2

"""Gates for THE SCHEMA OF QUALIA SPACE (seeds/qualia_space.json +
domains/analogy_search.concept_signature/crystallize).

The creator's directive: "what are the edge and shape of things — is the
current representation useful — a schema of Qualia space", and "humans don't
have two qualia spaces — 'I'm not sure how I feel about this' doesn't mean that
at all. Implementing a genuine thought and consciousness model is the goal."

These gates pin the model that answers it:

  1. a concept's signature is its COORDINATES on typed qualia DIMENSIONS — not a
     flat relation bag. The dimension tag makes the space a schema.
  2. ONE SPACE: the lexical axes (what a thing IS/for/made-of) and the dynamical
     axes (what it is LIKE, read off the CAN fields) are coordinates in the same
     signature.
  3. the CRYSTALLISED vs LIVE-OVERLAY split is the engine's own h_eff = external
     + identity, read as coordinates.
  4. THE UNSETTLED POINT — "I'm not sure how I feel about this" — is a real
     position in the space: live pull present, no crystallised commitment. The
     GAP between the overlay and the standing signature, not a missing reading.
  5. CRYSTALLISATION — experience becoming character: sustained felt state
     settles into the standing signature via the existing CAN identity rule.
  6. matching is PER-DIMENSION: a constitutive shape never matches a telic one
     just because they mention the same thing; and a cross-family analogy
     (shared felt valence + shared function) is findable because it is one
     space.
"""
from __future__ import annotations

import json
import pathlib

import substrate_rs as sr
from substrate_rs import _native

import domains.analogical_thinking as at
import domains.analogy_search as asr

ROOT = pathlib.Path(at.__file__).resolve().parent.parent
VOCAB = ROOT / "seeds" / "shape_vocabulary.json"
QUALIA = ROOT / "seeds" / "qualia_space.json"
SEARCH = ROOT / "seeds" / "analogy_search.json"

_NT = ("Agent", "Concept", "Microtheory", "AnalogyProbe", "ConceptShape",
       "Analogy", "QualiaDimension", "DimensionEdgeRole", "FunctionalRole",
       "ShapePrinciple", "MetaShape")
_ET = ("observed_probe", "emitted_analogy", "has_concept", "implements",
       "has_principle", "gates", "regulates", "made_of", "used_for")


def _open(s):
    for a in _NT:
        for b in _NT:
            for et in _ET:
                s.add_production({"src": {"type": a, "var": "x"},
                                  "edge_type": et,
                                  "tgt": {"type": b, "var": "y"},
                                  "where": None,
                                  "weight": {"type": "Lit", "value": 1.0},
                                  "provenance": "test:open"})


def _substrate():
    s = _native.Substrate()
    for cache in (at._CONCEPT_READING_CACHE, at._VOCAB_KEYS_CACHE,
                  at._METASHAPE_COUNT_CACHE, asr._QUALIA_SCHEMA_CACHE):
        cache.clear()
    ag = s.add_node("Agent", {})
    _open(s)
    for path in (VOCAB, QUALIA, SEARCH):
        summ = s.load_seed_manifest(json.load(open(path)), ag)
        assert not summ.get("rules_skipped"), (path.name, summ)
    return s, ag


def _mt(s, name):
    return s.add_node("Microtheory", {"name": name})


def _concept(s, mt, name, **attrs):
    a = {"name": name}
    a.update(attrs)
    c = s.add_node("Concept", a)
    s.add_edge(mt, "has_concept", c)
    return c


def _dims(sig):
    return {t[0] for t in sig}


def _pair(results, sc, tc):
    for r in results:
        if r["source_concept"] == sc and r["target_concept"] == tc:
            return r
    return None


# ---------------------------------------------------------------------------
# 1. the seed is pure codebook data — installs with nothing skipped
# ---------------------------------------------------------------------------
def test_qualia_seed_installs_clean():
    s = _native.Substrate()
    ag = s.add_node("Agent", {})
    s.load_seed_manifest(json.load(open(VOCAB)), ag)
    summ = s.load_seed_manifest(json.load(open(QUALIA)), ag)
    assert summ.get("rules_skipped") == []
    # the dimensional backbone is present
    dims = {s.node(n)["attrs"]["name"] for n in s.nodes("QualiaDimension")}
    assert {"lexical:formal", "lexical:telic", "lexical:constitutive",
            "lexical:agentive", "dynamical:valence", "dynamical:commitment",
            "dynamical:pull", "dynamical:activation"} <= dims


# ---------------------------------------------------------------------------
# 2. a signature is dimension-tagged coordinates, one space
# ---------------------------------------------------------------------------
def test_signature_is_dimension_tagged_one_space():
    s, _ag = _substrate()
    mt = _mt(s, "m")
    t = _concept(s, mt, "flow", category="process")
    valve = _concept(s, mt, "valve", category="device",
                     identity_field=0.8, state=1.0, external_field=0.6)
    s.add_edge(valve, "gates", t)

    cryst = asr.concept_signature(s, valve)
    # lexical AND dynamical coordinates co-reside in ONE signature
    assert ("lexical:formal", "category", "device") in cryst
    assert ("lexical:telic", "gates", "concept") in cryst  # gates -> telic role
    assert ("dynamical:valence", "field", 1) in cryst      # committed +
    assert any(d == "dynamical:commitment" for d, _, _ in cryst)  # identity_field
    # every coordinate carries a dimension tag (3-tuple)
    assert all(isinstance(t_, tuple) and len(t_) == 3 for t_ in cryst)


# ---------------------------------------------------------------------------
# 3. crystallised vs live overlay — h_eff = external + identity as coordinates
# ---------------------------------------------------------------------------
def test_overlay_adds_live_axes_over_crystallised():
    s, _ag = _substrate()
    mt = _mt(s, "m")
    valve = _concept(s, mt, "valve", category="device",
                     identity_field=0.8, state=1.0, external_field=0.6)
    cryst = asr.concept_signature(s, valve)
    over = asr.concept_signature(s, valve, overlay=True)
    added = _dims(over) - _dims(cryst)
    # the overlay is a SUPERSET adding the LIVE axes; crystallised is stable
    assert "dynamical:pull" in added        # external_field, live
    assert "dynamical:activation" in added  # current state, live
    assert "dynamical:pull" not in _dims(cryst)


# ---------------------------------------------------------------------------
# 4. THE UNSETTLED POINT — "I'm not sure how I feel about this"
# ---------------------------------------------------------------------------
def test_unsettled_point_is_a_position_not_a_missing_reading():
    """A concept being actively pulled on (external_field != 0) but with no
    crystallised commitment (identity_field = 0) is exactly 'I'm not sure how I
    feel'. It is a real POSITION: the live overlay carries the pull, the
    standing signature carries NO commitment — the GAP between them IS the
    uncertainty, not an absent value."""
    s, _ag = _substrate()
    mt = _mt(s, "m")
    # pulled on RIGHT NOW, but never settled: identity_field = 0
    c = _concept(s, mt, "the_offer", category="proposal",
                 identity_field=0.0, state=0.0, external_field=0.9)
    cryst = asr.concept_signature(s, c)
    over = asr.concept_signature(s, c, overlay=True)
    # the standing signature has NO settled feeling about it...
    assert "dynamical:commitment" not in _dims(cryst)
    # ...yet it is being felt right now (live pull present in the overlay).
    assert "dynamical:pull" in _dims(over)
    # the gap is non-empty: that gap is the "not sure how I feel".
    assert _dims(over) - _dims(cryst)


# ---------------------------------------------------------------------------
# 5. CRYSTALLISATION — experience becoming character
# ---------------------------------------------------------------------------
def test_sustained_feeling_crystallises_into_the_standing_signature():
    """A sustained same-sign felt state settles into `identity_field` via the
    existing CAN identity rule, so `dynamical:commitment` — absent while
    unsettled — APPEARS in the CRYSTALLISED signature. Experience became
    character; the decision is the graph rule's, crystallize() only ticks it."""
    s = sr.Substrate()
    inner = s._inner
    for cache in (asr._QUALIA_SCHEMA_CACHE,):
        cache.clear()
    ag = inner.add_node("Agent", {})
    from domains.can_self_worth_bridge import ensure_can_seed
    ensure_can_seed(inner)
    for path in (VOCAB, QUALIA):
        inner.load_seed_manifest(json.load(open(path)), ag)
    # an ADAPTIVE Mt (allow_h_drift) so identity feedback is permitted.
    mt = inner.add_node("Microtheory",
                        {"name": "m", "temperature": 1.0,
                         "discrete_mode": "static", "can_tick": 0,
                         "update_policy": "adaptive"})
    c = inner.add_node("Concept", {"name": "trust", "state": 1.0,
                                   "external_field": 1.0, "identity_field": 0.0})
    inner.add_edge_unchecked(mt, "has_concept", c)

    class _A:
        pass
    a = _A()
    a.s = inner
    a.agent = ag

    before = asr.concept_signature(inner, c)
    assert "dynamical:commitment" not in _dims(before)  # unsettled

    for i in range(40):
        inner.set_attr(mt, "can_tick", i + 1)   # strictly-later epoch
        inner.set_attr(c, "state", 1.0)          # sustain the feeling
        asr.crystallize(a)

    after = asr.concept_signature(inner, c)
    assert inner.node(c)["attrs"]["identity_field"] != 0.0
    assert "dynamical:commitment" in _dims(after)   # became character


# ---------------------------------------------------------------------------
# 6a. matching is PER-DIMENSION — no cross-dimension false match
# ---------------------------------------------------------------------------
def test_constitutive_does_not_match_telic_on_the_same_filler():
    """A concept MADE OF a switch (constitutive) and a concept USED TO switch
    (telic) both involve a 'switch', but they are NOT analogous on it — the
    dimension tag keeps the constitutive coordinate from intersecting the telic
    one. This is the schema doing its job: what a thing is made of is not what
    it is for."""
    s, _ag = _substrate()
    src, tgt = _mt(s, "a"), _mt(s, "b")
    sw1 = _concept(s, src, "switchbox")
    made = _concept(s, src, "switch_unit")
    s.add_edge(sw1, "made_of", made)          # constitutive: made_of -> switch
    sw2 = _concept(s, tgt, "controller")
    used = _concept(s, tgt, "switch_unit")
    s.add_edge(sw2, "used_for", used)         # telic: used_for -> switch

    # both edges point at a "switch_unit"-typed neighbour (same Concept type),
    # but on DIFFERENT qualia dimensions, so the coordinates differ:
    s1 = asr.concept_signature(s, sw1)
    s2 = asr.concept_signature(s, sw2)
    shared = s1 & s2
    disc = {t for t in shared if t[1] != "is_a"}
    # the constitutive coordinate of sw1 and the telic coordinate of sw2 do NOT
    # collide — no shared DISCRIMINATIVE coordinate from the switch relation.
    assert not any(t[0] in ("lexical:constitutive", "lexical:telic")
                   for t in disc), disc


# ---------------------------------------------------------------------------
# 6b. CROSS-FAMILY analogy — one space, lexical + phenomenal together
# ---------------------------------------------------------------------------
def test_cross_family_analogy_shares_felt_valence_and_function():
    """'Debt is like a toxin': found across unrelated fields on a SHARED felt
    valence (both standingly negative — a phenomenal/dynamical axis) AND a
    shared function (both regulate — a lexical/telic axis). Only findable
    because lexical and phenomenal are ONE space."""
    s, _ag = _substrate()
    econ, bio = _mt(s, "econ"), _mt(s, "bio")
    debt = _concept(s, econ, "debt", category="burden",
                    identity_field=-0.8, state=-1.0)
    s.add_edge(debt, "regulates", _concept(s, econ, "ledger", category="record"))
    toxin = _concept(s, bio, "toxin", category="burden",
                     identity_field=-0.7, state=-1.0)
    s.add_edge(toxin, "regulates", _concept(s, bio, "cell", category="unit"))

    res = at.find_analogies(s, "econ", ["bio"], order_n=4)
    r = _pair(res, "debt", "toxin")
    assert r is not None, res
    dims = set(r["aligned_dimensions"])
    # the match spans BOTH families — felt valence AND lexical function.
    assert any(d.startswith("dynamical:") for d in dims), dims
    assert any(d.startswith("lexical:") for d in dims), dims
    assert "dynamical:valence" in dims       # shared negative feeling
    assert "lexical:telic" in dims           # shared regulatory function

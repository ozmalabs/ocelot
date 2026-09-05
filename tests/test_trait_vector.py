"""Gates for the COGNITIVE PERSONALITY VECTOR (layer 1 — CORE): the single
`disposition` scalar generalised to N NAMED traits, each its own CAN-produced /
crystallising / seeded dynamical qualia axis on its own distribution
(domains/disposition.TRAIT_REGISTRY + the dynamical:<trait> axes in
seeds/qualia_space.json).

The premise: a personality is not one dial. People sit on a distribution across
MANY cognitive-style traits simultaneously, each moving with state. This layer
generalises the mechanism WITHOUT forking it — all traits share the SAME
relaxation + crystallisation + mirror machinery, each is its OWN CAN Concept
(so they move INDEPENDENTLY), and `openness` IS the old `disposition` (so every
existing caller is unchanged).

These gates pin exactly that:

  1. ensure_traits is idempotent and mints the WHOLE vector with each trait's
     SEEDED default (openness -1 = today; abstraction/skepticism 0 = neutral).
  2. INDEPENDENCE: relaxing one trait moves ONLY that trait — the others are
     separate CAN Concepts with separate fields, no cross-talk.
  3. trait_vector reads the whole personality at once; each trait grades under
     its own evidence.
  4. DISTINCT PERSONALITIES: two seed vectors => two distinct multi-axis
     signatures (distinct points in qualia space).
  5. BACK-COMPAT (critical): disposition_level == trait_level(openness), old
     set_disposition_seed still works, and a default agent's MintPolicy gate
     params + mint/refuse DECISIONS are unchanged (decision-equivalence).
  6. The seed declares the new dynamical:<trait> axes with the graded quantum.
"""
from __future__ import annotations

import json
import pathlib

from substrate_rs import _native

import domains.analogy_search as asr
import domains.disposition as disp
import domains.relation_grounding as rg

ROOT = pathlib.Path(disp.__file__).resolve().parent.parent
QUALIA = ROOT / "seeds" / "qualia_space.json"
VOCAB = ROOT / "seeds" / "shape_vocabulary.json"

TODAY = {"min_recurrence": 1, "max_content_words": 3,
         "require_noun_dominant_head": True}

_NT = ("Agent", "Concept", "Microtheory", "QualiaDimension", "DimensionEdgeRole")
_ET = tuple(set(rg.RELATION_EDGE_TYPES) | {"has_concept", "genls", "is_a",
            "built_from", "depends_on", "grounds"})


def _open(s):
    for a in _NT:
        for b in _NT:
            for et in _ET:
                s.add_production({"src": {"type": a, "var": "x"},
                                  "edge_type": et, "tgt": {"type": b, "var": "y"},
                                  "where": None,
                                  "weight": {"type": "Lit", "value": 1.0},
                                  "provenance": "test:open"})


class Agent:
    """A `.s` substrate + `.agent` hub — the shape disposition.py accepts."""
    def __init__(self, *, open_prods=False):
        asr._QUALIA_SCHEMA_CACHE.clear()
        self.s = _native.Substrate()
        self.agent = self.s.add_node("Agent", {})
        if open_prods:
            _open(self.s)


def _mt(s, name):
    return s.add_node("Microtheory", {"name": name})


def _concept(s, m, name, **attrs):
    a = {"name": name}
    a.update(attrs)
    c = s.add_node("Concept", a)
    s.add_edge(m, "has_concept", c)
    return c


def _names(s):
    return set(rg._concept_by_name(s).keys())


# ===========================================================================
# 1. ensure_traits — idempotent + the whole vector at seeded defaults
# ===========================================================================
def test_registry_has_the_three_starting_traits():
    assert disp.trait_names() == ["openness", "abstraction", "skepticism"]
    r = disp.TRAIT_REGISTRY
    assert r["openness"].seed == disp.DEFAULT_DISPOSITION_SEED == -1.0
    assert r["openness"].axis == "dynamical:disposition"
    assert r["openness"].concept_name == disp.DISPOSITION_CONCEPT_NAME
    assert r["openness"].field_attr == disp.DISPOSITION_FIELD_ATTR
    assert r["abstraction"].seed == 0.0
    assert r["abstraction"].axis == "dynamical:abstraction"
    assert r["skepticism"].seed == 0.0
    assert r["skepticism"].axis == "dynamical:skepticism"


def test_ensure_traits_idempotent_and_seeded_defaults():
    a = Agent()
    v1 = disp.ensure_traits(a)
    v2 = disp.ensure_traits(a)
    assert set(v1) == set(disp.TRAIT_REGISTRY)
    assert v1 == v2, "ensure_traits must be idempotent (first-found per trait)"

    # exactly ONE shared disposition Mt and exactly ONE Concept per trait.
    s = a.s
    mts = [m for m in s.nodes("Microtheory")
           if s.node(m)["attrs"].get("name") == disp.DISPOSITION_MT_NAME]
    assert len(mts) == 1, "all traits share ONE agent_disposition Mt"
    for spec in disp.TRAIT_REGISTRY.values():
        cs = [n for n in s.nodes("Concept")
              if s.node(n)["attrs"].get("name") == spec.concept_name]
        assert len(cs) == 1, (spec.name, cs)

    # each trait reads its SEEDED default level.
    assert disp.trait_level(a, "openness") == -1
    assert disp.trait_level(a, "abstraction") == 0
    assert disp.trait_level(a, "skepticism") == 0


def test_trait_vector_reads_the_whole_personality():
    a = Agent()
    disp.ensure_traits(a)
    vec = disp.trait_vector(a)
    assert vec == {"openness": -1, "abstraction": 0, "skepticism": 0}


def test_trait_vector_ensure_false_mints_nothing():
    """A default vector read with ensure=False adds nothing to the graph and
    returns the seeded defaults (off-by-default discipline)."""
    a = Agent()
    vec = disp.trait_vector(a, ensure=False)
    assert vec == {"openness": -1, "abstraction": 0, "skepticism": 0}
    mts = [m for m in a.s.nodes("Microtheory")
           if a.s.node(m)["attrs"].get("name") == disp.DISPOSITION_MT_NAME]
    assert mts == []


# ===========================================================================
# 2. INDEPENDENCE — separate CAN Concepts, separate fields, no cross-talk
# ===========================================================================
def test_relaxing_one_trait_does_not_move_another():
    a = Agent()
    for t in disp.trait_names():
        disp.set_trait_seed(a, t, 0.0)
    assert disp.trait_vector(a) == {"openness": 0, "abstraction": 0, "skepticism": 0}

    # drive ONLY openness.
    disp.relax_trait(a, "openness", +1.0, ticks=3)
    v = disp.trait_vector(a)
    assert v["openness"] > 0
    assert v["abstraction"] == 0 and v["skepticism"] == 0, v

    # drive ONLY skepticism — openness stays where it was, abstraction untouched.
    open_before = v["openness"]
    disp.relax_trait(a, "skepticism", +1.0, ticks=4)
    v = disp.trait_vector(a)
    assert v["skepticism"] > 0
    assert v["openness"] == open_before, v
    assert v["abstraction"] == 0, v


def test_each_trait_grades_independently_in_opposite_directions():
    """Drive openness UP and skepticism DOWN in the same agent: each follows its
    own evidence to its own coordinate, proving they are distinct fields."""
    a = Agent()
    for t in disp.trait_names():
        disp.set_trait_seed(a, t, 0.0)
    for _ in range(5):
        disp.relax_trait(a, "openness", +1.0, ticks=1)
        disp.relax_trait(a, "skepticism", -1.0, ticks=1)
    v = disp.trait_vector(a)
    assert v["openness"] > 0, v
    assert v["skepticism"] < 0, v
    assert v["abstraction"] == 0, v          # never driven -> stays neutral


def test_trait_concepts_are_distinct_nodes():
    a = Agent()
    cs = disp.ensure_traits(a)
    ids = set(cs.values())
    assert len(ids) == len(cs), "each trait is its OWN Concept node"


# ===========================================================================
# 3. DISTINCT PERSONALITIES — two seed vectors => two distinct signatures
# ===========================================================================
def _sig_point(agent):
    """The personality as a comparable point: trait -> (axis, k) or None."""
    return {t: (c[0], c[2]) if c else None
            for t, c in disp.personality_signature(agent).items()}


def test_two_seed_vectors_give_two_distinct_personality_signatures():
    A = Agent()
    disp.set_trait_seed(A, "openness", +2.0)
    disp.set_trait_seed(A, "abstraction", +3.0)
    disp.set_trait_seed(A, "skepticism", -2.0)

    B = Agent()
    disp.set_trait_seed(B, "openness", -3.0)
    disp.set_trait_seed(B, "abstraction", -2.0)
    disp.set_trait_seed(B, "skepticism", +3.0)

    va, vb = disp.trait_vector(A), disp.trait_vector(B)
    assert va == {"openness": 2, "abstraction": 3, "skepticism": -2}
    assert vb == {"openness": -3, "abstraction": -2, "skepticism": 3}
    assert va != vb

    pa, pb = _sig_point(A), _sig_point(B)
    assert pa != pb, (pa, pb)
    # each trait's coordinate is on its OWN named axis
    assert pa["openness"] == ("dynamical:disposition", 2)
    assert pa["abstraction"] == ("dynamical:abstraction", 3)
    assert pa["skepticism"] == ("dynamical:skepticism", -2)
    assert pb["openness"] == ("dynamical:disposition", -3)


def test_trait_signature_places_each_trait_on_its_own_axis():
    a = Agent()
    disp.set_trait_seed(a, "abstraction", +2.0)
    sig = disp.trait_signature(a, "abstraction")
    dims = {t[0] for t in sig}
    assert "dynamical:abstraction" in dims, sig
    # abstraction's coordinate does NOT appear on openness's axis
    assert "dynamical:disposition" not in dims, sig


# ===========================================================================
# 4. BACK-COMPAT — openness IS the old disposition (exact)
# ===========================================================================
def test_openness_is_the_old_disposition_same_level():
    a = Agent()
    disp.ensure_disposition(a)          # old API
    assert disp.disposition_level(a) == disp.trait_level(a, "openness") == -1
    # and moving via the old API moves the openness trait.
    disp.set_disposition_seed(a, +2.0)
    assert disp.trait_level(a, "openness") == 2
    assert disp.disposition_level(a) == 2


def test_old_and_new_api_share_one_concept():
    """ensure_disposition and ensure_trait(openness) return the SAME node — not
    two parallel disposition Concepts."""
    a = Agent()
    c_old = disp.ensure_disposition(a)
    c_new = disp.ensure_trait(a, "openness")
    assert c_old == c_new
    # only ONE disposition Concept exists.
    cs = [n for n in a.s.nodes("Concept")
          if a.s.node(n)["attrs"].get("name") == disp.DISPOSITION_CONCEPT_NAME]
    assert len(cs) == 1


def test_relax_disposition_equivalent_to_relax_trait_openness():
    a = Agent()
    disp.set_disposition_seed(a, 0.0)
    disp.relax_disposition(a, +1.0, ticks=3)
    la = disp.trait_level(a, "openness")

    b = Agent()
    disp.set_trait_seed(b, "openness", 0.0)
    disp.relax_trait(b, "openness", +1.0, ticks=3)
    lb = disp.trait_level(b, "openness")

    assert la == lb, (la, lb)


# --- the critical safe-default invariant: MintPolicy gate is unchanged ------
def test_seeded_default_vector_keeps_mint_gate_params_today():
    """A fresh agent that mints the WHOLE trait vector still derives EXACTLY
    today's MintPolicy params — the new traits are behaviourally neutral/inert,
    and openness's seeded default (-1) maps to today's gate."""
    a = Agent(open_prods=True)
    disp.ensure_traits(a)               # mint the whole vector
    assert disp.trait_level(a, "openness") == -1
    assert rg._disposition_derived_gate(a) == TODAY
    assert rg.mint_gate_params(a) == TODAY


def test_decision_equivalence_full_vector_matches_today():
    """DECISION-equivalence: an agent carrying the full seeded-default trait
    vector makes the SAME mint/refuse decisions as a graph with no disposition
    at all — a clean NP minted, a clause refused. The new traits change nothing
    (they have no consumer this layer)."""
    # baseline: no disposition at all.
    base = Agent(open_prods=True)
    mb = _mt(base.s, "m")
    _concept(base.s, mb, "IOMMU", definition="An IOMMU is used for VM passthrough.")
    _concept(base.s, mb, "page_fault",
             definition="A page fault enables programs use more virtual memory.")
    res_base = rg.mint_referents_from_relations(base.s, "m")

    # with the FULL seeded-default trait vector minted on the agent.
    a = Agent(open_prods=True)
    disp.ensure_traits(a)               # openness -1 (=today) + neutral inert traits
    m = _mt(a.s, "m")
    _concept(a.s, m, "IOMMU", definition="An IOMMU is used for VM passthrough.")
    _concept(a.s, m, "page_fault",
             definition="A page fault enables programs use more virtual memory.")
    res = rg.mint_referents_from_relations(a.s, "m")

    assert res["gate"] == res_base["gate"] == TODAY
    assert "vm_passthrough" in _names(a.s)
    assert res["minted"] == res_base["minted"]
    assert any(et == "enables" and "virtual memory" in ph
               for (_s, et, ph) in res["refused_phrases"])


def test_inert_traits_do_not_touch_the_mint_gate():
    """Moving abstraction/skepticism to extremes does NOT change the derived mint
    gate — they have no consumer this layer (INERT). Only openness drives it."""
    a = Agent(open_prods=True)
    disp.ensure_traits(a)
    # slam the inert traits to their clamps; the gate must not budge.
    disp.set_trait_seed(a, "abstraction", +4.0)
    disp.set_trait_seed(a, "skepticism", -4.0)
    assert rg.mint_gate_params(a) == TODAY, "inert traits must not move the gate"
    # only openness moving changes it.
    disp.set_trait_seed(a, "openness", +2.0)
    assert rg.mint_gate_params(a)["require_noun_dominant_head"] is False


# ===========================================================================
# 5. the seed declares the new dynamical:<trait> axes with the graded quantum
# ===========================================================================
def test_seed_declares_the_trait_axes():
    s = _native.Substrate()
    ag = s.add_node("Agent", {})
    s.load_seed_manifest(json.load(open(VOCAB)), ag)
    summ = s.load_seed_manifest(json.load(open(QUALIA)), ag)
    assert summ.get("rules_skipped") == []

    dims = {s.node(n)["attrs"]["name"]: s.node(n)["attrs"]
            for n in s.nodes("QualiaDimension")}
    # every registry trait has a crystallised axis + an overlay pull axis.
    for spec in disp.TRAIT_REGISTRY.values():
        assert spec.axis in dims, spec.axis
        assert spec.pull_axis in dims, spec.pull_axis
        d = dims[spec.axis]
        assert d["source"] == f"field:{spec.field_attr}"
        assert float(d["quantum"]) == 1.0
        assert float(d["half_width"]) == 4.0
        assert not d.get("overlay"), (spec.axis, "standing axis is crystallised")
        p = dims[spec.pull_axis]
        assert p["source"] == f"field:{spec.external_attr}"
        assert p.get("overlay"), (spec.pull_axis, "pull axis is overlay")

"""Gate for the CROSS-FAMILY analogy (qualia gap 3) — the payoff of the
one-space thesis.

A genuine cross-family match aligns two concepts from UNRELATED fields on BOTH
a RELATIONAL / lexical axis (lexical:telic/constitutive/agentive — what a thing
FUNCTIONS like) AND a DYNAMICAL / felt axis (dynamical:valence/commitment — what
it FEELS like) AT ONCE. It is findable only because the lexical and phenomenal
coordinates are ONE space, intersected in the same frozenset.

The discipline these gates pin (a real demonstration, not a rigged one):

  * the RELATIONAL edge is DERIVED from the concept's own prose by the gap-1
    machinery `relation_grounding.ground_relations` — grounded ONLY to a HELD
    Concept (the anti-hallucination gate), never asserted;
  * the DYNAMICAL coordinate is PRODUCED by the real native CAN relaxation
    (relax + crystallize) — state/identity_field are NEVER hand-written;
  * the match itself is emitted by `analogy_search.find_analogies` over the two
    fields' Microtheories (the graph fixpoint), and we assert its
    `aligned_dimensions` intersects BOTH a lexical:{telic,constitutive,agentive}
    axis AND a dynamical:* axis.

Companion demo: scripts/qualia_cross_family_demo.py (adds the single-family
contrast + narration). Kept minimal here; the contrast lives in the demo.
"""
from __future__ import annotations

import json
import pathlib

from substrate_rs import _native

import domains.analogical_thinking as at
import domains.analogy_search as asr
import domains.relation_grounding as rg
from domains.can_self_worth_bridge import ensure_can_seed
from domains.self_improvement_loop import relax

ROOT = pathlib.Path(at.__file__).resolve().parent.parent
SEEDS = ROOT / "seeds"

_LEXICAL_RELATIONAL = {"lexical:telic", "lexical:constitutive", "lexical:agentive"}

# native identity-rule bookkeeping ledger (as tests/test_can_identity_feedback.py
# / scripts/qualia_felt_demo.py) — required by the identity feedback rule; the
# felt coordinate itself starts at 0.0 and is PRODUCED.
_LEDGER = {
    "identity_evidence_confirm": 0, "identity_evidence_disconfirm": 0,
    "identity_evidence_tick": -1, "identity_decay_tick": -1,
    "identity_field_tick": -1,
}


class _Agent:
    def __init__(self, sub):
        self.s = sub
        self.agent = sub.nodes("Agent")[0]


def _boot():
    for cache in (at._CONCEPT_READING_CACHE, at._VOCAB_KEYS_CACHE,
                  at._METASHAPE_COUNT_CACHE, asr._QUALIA_SCHEMA_CACHE):
        cache.clear()
    s = _native.Substrate()
    ag = s.add_node("Agent", {})
    for name in ("shape_vocabulary", "qualia_space", "analogy_search"):
        s.load_seed_manifest(json.load(open(SEEDS / f"{name}.json")), ag)
    ensure_can_seed(s)
    # open productions for has_concept + CAN coupling + every relation edge
    # ground_relations may emit + genls.
    node_types = ("Agent", "Concept", "Microtheory")
    edge_types = ("has_concept", "causal_influence") + rg.RELATION_EDGE_TYPES + ("genls",)
    for a in node_types:
        for b in node_types:
            for et in edge_types:
                s.add_production({"src": {"type": a, "var": "x"},
                                  "edge_type": et,
                                  "tgt": {"type": b, "var": "y"},
                                  "where": None,
                                  "weight": {"type": "Lit", "value": 1.0},
                                  "provenance": "test:open"})
    return s, ag


def _can_concept(s, mt, name, *, definition, category, external_field=0.0):
    """A CAN Concept carrying prose; state/identity_field start at ZERO (the
    felt coordinate is PRODUCED by relaxation, never asserted)."""
    attrs = {"name": name, "category": category, "definition": definition,
             "state": 0.0, "external_field": float(external_field),
             "identity_field": 0.0}
    attrs.update(_LEDGER)
    c = s.add_node("Concept", attrs)
    s.add_edge_unchecked(mt, "has_concept", c)
    return c


def _couple(s, a, b, w):
    s.add_edge(a, "causal_influence", b, {"weight": float(w)})
    s.add_edge(b, "causal_influence", a, {"weight": float(w)})


def _relax(s, mt, *, ticks=16):
    steps = relax(s, mt)
    for i in range(ticks):
        s.set_attr(mt, "can_tick", i + 1)
        asr.crystallize(_Agent(s))
    return steps


def _pair(results, sc, tc):
    for r in results:
        if r["source_concept"] == sc and r["target_concept"] == tc:
            return r
    return None


# ---------------------------------------------------------------------------
# THE GATE — a found analogy spans BOTH families at once.
# ---------------------------------------------------------------------------
def test_cross_family_analogy_spans_lexical_and_dynamical():
    """debt ~ toxin, across econ vs biology: the telic edge DERIVED from prose
    by ground_relations, the negative valence PRODUCED by native relaxation. The
    emitted analogy's aligned_dimensions intersects BOTH a lexical relational
    axis (telic/constitutive/agentive) AND a dynamical (felt) axis."""
    s, _ag = _boot()

    econ = s.add_node("Microtheory", {"name": "econ", "category": "economics",
                                      "temperature": 1.0, "discrete_mode": "3state",
                                      "can_tick": 0, "update_policy": "adaptive"})
    ledger = _can_concept(s, econ, "ledger", category="record",
                          definition="A ledger is a record of accounts.")
    debt = _can_concept(s, econ, "debt", category="burden", external_field=-5.0,
                        definition="Debt is a burden that regulates the ledger.")
    _couple(s, debt, ledger, +0.4)

    bio = s.add_node("Microtheory", {"name": "bio", "category": "biology",
                                     "temperature": 1.0, "discrete_mode": "3state",
                                     "can_tick": 0, "update_policy": "adaptive"})
    cell = _can_concept(s, bio, "cell", category="unit",
                        definition="A cell is the basic unit of an organism.")
    toxin = _can_concept(s, bio, "toxin", category="burden", external_field=-5.0,
                         definition="A toxin is a burden that regulates the cell.")
    _couple(s, toxin, cell, +0.4)

    # (1) DERIVE the telic edges from prose — grounded to HELD targets only.
    rep_e = rg.ground_relations(s, "econ")
    rep_b = rg.ground_relations(s, "bio")
    assert ("debt", "regulates", "ledger") in rep_e["emitted"], rep_e
    assert ("toxin", "regulates", "cell") in rep_b["emitted"], rep_b
    assert rep_e["telic"] >= 1 and rep_b["telic"] >= 1

    # (2) PRODUCE the felt coordinate by native relaxation (never hand-written).
    _relax(s, econ)
    _relax(s, bio)
    assert s.node(debt)["attrs"]["state"] < -0.5     # settled negative
    assert s.node(toxin)["attrs"]["state"] < -0.5
    assert s.node(debt)["attrs"]["identity_field"] < 0   # crystallised negative
    assert s.node(toxin)["attrs"]["identity_field"] < 0

    # (3) MATCH across the two fields, DIRECTLY on the real relaxed
    #     Microtheories. No 'clean view' scaffolding is needed: concept_signature
    #     now excludes the native CAN bookkeeping counters (identity/evidence
    #     ledgers + tick/epoch gates) at the source, so the real concepts carry
    #     no non-discriminative attr:* noise.
    results = at.find_analogies(s, "econ", ["bio"], order_n=4,
                                min_score=1)
    r = _pair(results, "debt", "toxin")
    assert r is not None, results

    dims = set(r["aligned_dimensions"])
    # THE ASSERTION: the match spans BOTH families at once.
    assert dims & _LEXICAL_RELATIONAL, ("no lexical relational axis", dims)
    assert any(d.startswith("dynamical:") for d in dims), ("no dynamical axis", dims)
    # concretely: shared regulatory function AND shared negative feeling.
    assert "lexical:telic" in dims, dims
    assert "dynamical:valence" in dims, dims
    # and NO native CAN bookkeeping leaked into the aligned dimensions.
    assert not any(d.startswith("attr:") for d in dims), ("bookkeeping leak", dims)


def test_derived_edge_is_grounded_not_fabricated():
    """The relational axis comes through the anti-hallucination gate: a relation
    cue whose object does NOT name a held concept is DROPPED (no edge, no
    invented node), so a cross-family match cannot be manufactured from prose
    that names nothing held."""
    s, _ag = _boot()
    mt = s.add_node("Microtheory", {"name": "m"})
    # 'regulates the bloodstream' — bloodstream is NOT a held concept here.
    c = s.add_node("Concept", {"name": "hormone", "category": "burden",
                               "definition": "A hormone regulates the bloodstream."})
    s.add_edge_unchecked(mt, "has_concept", c)
    rep = rg.ground_relations(s, "m")
    # nothing grounded → no regulates edge emitted, the candidate was dropped.
    assert rep["edges_added"] == 0, rep
    assert not any(et == "regulates" for _, et, _ in rep["emitted"]), rep
    assert any(obj for _, et, obj in rep["dropped"] if et == "regulates"), rep



def test_relaxed_concept_signature_excludes_can_bookkeeping():
    """CORE of qualia gap 3: after a concept goes through the native CAN field,
    the identity/evidence-LEDGER counters and per-rule TICK/EPOCH gates the CAN
    rules write onto it (identity_evidence_confirm/_disconfirm/_tick,
    identity_decay_tick, external_field_decay_tick, identity_field_tick, …) must
    NOT appear as `attr:*` coordinates in concept_signature — they are
    non-discriminative mechanism noise. The felt content the field PRODUCED must
    still be there as the DYNAMICAL axes, and genuine content attrs
    (name/definition) must be KEPT."""
    s, _ag = _boot()
    mt = s.add_node("Microtheory", {"name": "m", "category": "affect",
                                    "temperature": 1.0, "discrete_mode": "3state",
                                    "can_tick": 0, "update_policy": "adaptive"})
    a = _can_concept(s, mt, "good_news", category="event", external_field=+5.0,
                     definition="good news arrived")
    b = _can_concept(s, mt, "feeling_safe", category="affect", external_field=+4.0,
                     definition="a sense of safety")
    _couple(s, a, b, +1.0)
    _relax(s, mt)

    # sanity: the CAN rules really did write the bookkeeping counters onto the
    # raw node (otherwise this test would pass vacuously).
    raw = s.node(a)["attrs"]
    assert "identity_evidence_confirm" in raw and "identity_field_tick" in raw, raw

    sig = asr.concept_signature(s, a)
    attr_keys = {pred for dim, pred, _ in sig if dim.startswith("attr:")}

    # NONE of the CAN bookkeeping counters survive into attr:* coordinates.
    for leak in ("identity_evidence_confirm", "identity_evidence_disconfirm",
                 "identity_evidence_tick", "identity_decay_tick",
                 "external_field_decay_tick", "identity_field_tick",
                 "state", "external_field", "identity_field"):
        assert leak not in attr_keys, (leak, sorted(attr_keys))
    assert not any(k.endswith("_tick") or k.endswith("_epoch") for k in attr_keys), \
        sorted(attr_keys)

    # the PRODUCED felt content is still present, on the dynamical axes.
    dims = {d for d, _, _ in sig}
    assert "dynamical:valence" in dims, sorted(dims)
    assert "dynamical:commitment" in dims, sorted(dims)

    # genuine content attrs are KEPT (name + definition), and formal category.
    assert "name" in attr_keys and "definition" in attr_keys, sorted(attr_keys)
    assert ("lexical:formal", "category", "event") in sig, sorted(sig)


def test_two_relaxed_concepts_align_without_bookkeeping_noise():
    """Two independently-relaxed concepts (separate fields) must align on their
    real dynamical/lexical axes with NO spurious `attr:*` in aligned_dimensions
    — the identical ledger values across all relaxed concepts no longer leak in
    as a shared coordinate. Run DIRECTLY on the real relaxed concepts, no clean
    views."""
    s, _ag = _boot()
    src = s.add_node("Microtheory", {"name": "src", "category": "affect",
                                     "temperature": 1.0, "discrete_mode": "3state",
                                     "can_tick": 0, "update_policy": "adaptive"})
    tgt = s.add_node("Microtheory", {"name": "tgt", "category": "affect",
                                     "temperature": 1.0, "discrete_mode": "3state",
                                     "can_tick": 0, "update_policy": "adaptive"})
    joy = _can_concept(s, src, "joy", category="affect", external_field=+5.0,
                       definition="a bright joy")
    delight = _can_concept(s, tgt, "delight", category="affect", external_field=+5.0,
                           definition="a keen delight")
    _relax(s, src)
    _relax(s, tgt)

    results = at.find_analogies(s, "src", ["tgt"], order_n=2, min_score=1)
    r = _pair(results, "joy", "delight")
    assert r is not None, results
    dims = set(r["aligned_dimensions"])
    assert any(d.startswith("dynamical:") for d in dims), ("no dynamical axis", dims)
    assert not any(d.startswith("attr:") for d in dims), ("bookkeeping leak", dims)

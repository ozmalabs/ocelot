"""Gates for the PERSONALITY-VECTOR CONSUMERS (layer 2): the two inert traits
from layer 1 now drive two REAL, pre-existing analogy-search knobs.

  · ABSTRACTION -> the analogy ORDER FLOOR (domains/analogy_search.find_analogies
    filters emitted analogies below the abstraction-derived order; think_harder's
    start_n / order_used reflect it). "Reach for higher-order matches first."
  · SKEPTICISM  -> the analogy ACCEPTANCE FLOOR (find_analogies min_score, the
    floor on shared DISCRIMINATIVE structure). "Demand more support."

The invariants this suite pins:
  1. DECISION-EQUIVALENCE — a NEUTRAL (seed-0) trait, or NO trait vector at all,
     reproduces TODAY's behaviour EXACTLY (order floor 2 = the minimum order ever
     emitted, filters nothing; min_score 1 = today's default). The trait read is
     NON-MINTING (a bare call never mints a trait Mt).
  2. HIGH ABSTRACTION => a higher order floor (find_analogies drops surface
     matches; think_harder reports a higher start_n).
  3. HIGH SKEPTICISM => a higher min_score AND a monotone drop in accepted
     analogies (fewer, better-supported matches).
  4. EXPLICIT caller args (order_n / min_score / start_n) OVERRIDE the trait-
     derived defaults — the mint gate's explicit-pin-wins precedence.
  5. HONEST INDEPENDENCE — the three knobs are driven by three INDEPENDENT traits.
     A permissive-openness + high-skepticism agent has a LOOSE mint gate BUT a
     HIGH analogy floor, verified on REAL find_analogies + mint calls.

The trait MAPPINGS (trait_level in [-4,+4] -> knob), asserted directly against
the derivation helpers so a mapping regression is caught precisely:
    abstraction  <=0 -> order floor 2   1..2 -> 3   >=3 -> 4
    skepticism   <=0 -> min_score 1     1..2 -> 2   >=3 -> 3
"""
from __future__ import annotations

import json
import pathlib

from substrate_rs import _native

import domains.analogical_thinking as at
import domains.analogy_search as asr
import domains.relation_grounding as rg
import domains.disposition as disp
from domains.can_self_worth_bridge import ensure_can_seed
from domains.self_improvement_loop import relax

ROOT = pathlib.Path(at.__file__).resolve().parent.parent
SEEDS = ROOT / "seeds"

_LEDGER = {
    "identity_evidence_confirm": 0, "identity_evidence_disconfirm": 0,
    "identity_evidence_tick": -1, "identity_decay_tick": -1,
    "identity_field_tick": -1,
}


class _Agent:
    """The agent wrapper domains/disposition + analogy_search accept."""

    def __init__(self, sub, ag):
        self.s = sub
        self.agent = ag


# --------------------------------------------------------------------------- #
# Fixtures — the SAME corpus every personality runs over. A mix of HIGH-ORDER
# (shared ShapePrinciple => order 4) and SURFACE (order 2) analogies, plus a
# mint field whose objects have verb-dominant heads (refused by the strict gate,
# minted by the permissive one). This mirrors scripts/qualia_personality_demo.py.
# --------------------------------------------------------------------------- #
_CS = {
    "scheduler": dict(category="control", ext=-4.0,
        definition="A scheduler regulates the queue to balance load with a set_point."),
    "arbiter":   dict(category="control", ext=-4.0,
        definition="An arbiter selects a winner by lateral_inhibit competition among cores."),
    "cache":     dict(category="control", ext=+4.0,
        definition="A cache regulates memory access and serves the cpu."),
    "queue":     dict(category="unit", definition="A queue is a buffer of tasks."),
    "cpu":       dict(category="unit", definition="A cpu is a processor."),
    "cores":     dict(category="unit", definition="cores are processing units."),
    "memory":    dict(category="unit", definition="memory is storage."),
}
_BIO = {
    "hormone":  dict(category="control", ext=-4.0,
        definition="A hormone regulates the gland to balance level with a set_point homeostas."),
    "cortex":   dict(category="control", ext=-4.0,
        definition="The cortex selects a winner by lateral_inhibit competition among neurons."),
    "membrane": dict(category="control", ext=+4.0,
        definition="A membrane regulates ion access and serves the neuron."),
    "gland":    dict(category="unit", definition="A gland is an organ of tasks."),
    "neuron":   dict(category="unit", definition="A neuron is a cell."),
    "neurons":  dict(category="unit", definition="neurons are cells."),
    "ion":      dict(category="unit", definition="ion is storage."),
}
_CS_COUPLE = (("scheduler", "queue"), ("arbiter", "cores"), ("cache", "memory"))
_BIO_COUPLE = (("hormone", "gland"), ("cortex", "neurons"), ("membrane", "ion"))
_MINT_HW = {
    "raster": "A raster drives the periodic refresh and controls the screen coordinate.",
    "clock":  "A clock enables the timed rollover and gates the frequent update.",
    "buffer": "A buffer serves the pending transfer and holds the eventual result.",
}


def _boot():
    for cache in (at._CONCEPT_READING_CACHE, at._VOCAB_KEYS_CACHE,
                  at._METASHAPE_COUNT_CACHE, asr._QUALIA_SCHEMA_CACHE):
        cache.clear()
    s = _native.Substrate()
    ag = s.add_node("Agent", {})
    for name in ("shape_vocabulary", "qualia_space", "analogy_search"):
        s.load_seed_manifest(json.load(open(SEEDS / f"{name}.json")), ag)
    ensure_can_seed(s)
    node_types = ("Agent", "Concept", "Microtheory")
    edge_types = (("has_concept", "causal_influence")
                  + rg.RELATION_EDGE_TYPES + ("genls",))
    for a in node_types:
        for b in node_types:
            for et in edge_types:
                s.add_production({"src": {"type": a, "var": "x"}, "edge_type": et,
                                  "tgt": {"type": b, "var": "y"}, "where": None,
                                  "weight": {"type": "Lit", "value": 1.0},
                                  "provenance": "test:open"})
    return s, ag


def _concept(s, mt, name, *, definition, category, ext=0.0):
    attrs = {"name": name, "category": category, "definition": definition,
             "state": 0.0, "external_field": float(ext), "identity_field": 0.0}
    attrs.update(_LEDGER)
    c = s.add_node("Concept", attrs)
    s.add_edge_unchecked(mt, "has_concept", c)
    return c


def _field(s, name, spec, couples):
    mt = s.add_node("Microtheory", {"name": name, "temperature": 1.0,
                                    "discrete_mode": "3state", "can_tick": 0,
                                    "update_policy": "adaptive"})
    nodes = {n: _concept(s, mt, n, **kw) for n, kw in spec.items()}
    for a, b in couples:
        s.add_edge(nodes[a], "causal_influence", nodes[b], {"weight": 0.4})
        s.add_edge(nodes[b], "causal_influence", nodes[a], {"weight": 0.4})
    return mt, nodes


def _build(s):
    cs, _ = _field(s, "cs", _CS, _CS_COUPLE)
    bio, _ = _field(s, "bio", _BIO, _BIO_COUPLE)
    rg.ground_relations(s, "cs")
    rg.ground_relations(s, "bio")
    ag = s.nodes("Agent")[0]
    for mt in (cs, bio):
        relax(s, mt)
        for i in range(12):
            s.set_attr(mt, "can_tick", i + 1)
            asr.crystallize(_Agent(s, ag))
    hw = s.add_node("Microtheory", {"name": "hw", "temperature": 1.0,
                                    "discrete_mode": "static", "can_tick": 0})
    for n, d in _MINT_HW.items():
        c = s.add_node("Concept", {"name": n, "definition": d, "category": "device"})
        s.add_edge_unchecked(hw, "has_concept", c)


def _agent(traits=None):
    s, ag = _boot()
    _build(s)
    a = _Agent(s, ag)
    for t, v in (traits or {}).items():
        disp.set_trait_seed(a, t, v)
    return a


def _orders(res):
    return sorted(r["order_n"] for r in res)


# =========================================================================== #
# 0. THE MAPPINGS — asserted directly on the derivation helpers.
# =========================================================================== #
def test_abstraction_mapping_is_monotone_and_neutral_is_two():
    """abstraction level -> order floor: <=0 -> 2 (today), 1..2 -> 3, >=3 -> 4."""
    a = _agent()
    disp.set_trait_seed(a, "abstraction", 0.0)
    assert asr._abstraction_min_order(a) == 2   # neutral == today
    disp.set_trait_seed(a, "abstraction", -3.0)
    assert asr._abstraction_min_order(a) == 2   # concrete still 2 (never below)
    disp.set_trait_seed(a, "abstraction", +1.0)
    assert asr._abstraction_min_order(a) == 3
    disp.set_trait_seed(a, "abstraction", +2.0)
    assert asr._abstraction_min_order(a) == 3
    disp.set_trait_seed(a, "abstraction", +4.0)
    assert asr._abstraction_min_order(a) == 4


def test_skepticism_mapping_is_monotone_and_neutral_is_one():
    """skepticism level -> min_score: <=0 -> 1 (today), 1..2 -> 2, >=3 -> 3."""
    a = _agent()
    disp.set_trait_seed(a, "skepticism", 0.0)
    assert asr._skepticism_min_score(a) == 1    # neutral == today
    disp.set_trait_seed(a, "skepticism", -4.0)
    assert asr._skepticism_min_score(a) == 1    # credulous still 1
    disp.set_trait_seed(a, "skepticism", +1.0)
    assert asr._skepticism_min_score(a) == 2
    disp.set_trait_seed(a, "skepticism", +2.0)
    assert asr._skepticism_min_score(a) == 2
    disp.set_trait_seed(a, "skepticism", +3.0)
    assert asr._skepticism_min_score(a) == 3


def test_no_trait_vector_derives_nothing_and_never_mints():
    """A graph with NO personality vector: the derivation helpers return None
    (=> caller keeps today's defaults) and the read NEVER mints a trait Mt."""
    s, ag = _boot()
    _build(s)
    a = _Agent(s, ag)
    assert asr._abstraction_min_order(a) is None
    assert asr._skepticism_min_score(a) is None
    # off-by-default discipline: no disposition Mt was minted by the bare read.
    assert disp._find_disposition_mt(s, ag) is None


# =========================================================================== #
# 1. DECISION-EQUIVALENCE — neutral trait == today exactly.
# =========================================================================== #
def test_neutral_abstraction_leaves_find_analogies_unchanged():
    """A neutral (seed-0) abstraction reproduces the SAME analogy set as a graph
    with no trait vector at all — decision-equivalence on the real search."""
    base = _agent()                                   # no traits
    res_base = at.find_analogies(base.s, "cs", ["bio"])
    neu = _agent({"abstraction": 0.0})                # explicitly neutral
    res_neu = at.find_analogies(neu.s, "cs", ["bio"])
    key = lambda res: sorted((r["source_concept"], r["target_concept"],
                              r["order_n"]) for r in res)
    assert key(res_base) == key(res_neu)
    # and the neutral order floor keeps EVERY order (2s present).
    assert 2 in _orders(res_neu) and 4 in _orders(res_neu)


def test_neutral_skepticism_leaves_min_score_at_default():
    """A neutral (seed-0) skepticism reads min_score 1 — today's default — and
    the analogy set is identical to the no-trait baseline."""
    base = _agent()
    res_base = at.find_analogies(base.s, "cs", ["bio"])
    neu = _agent({"skepticism": 0.0})
    assert asr._skepticism_min_score(neu) == 1
    res_neu = at.find_analogies(neu.s, "cs", ["bio"])
    assert len(res_base) == len(res_neu)


def test_neutral_think_harder_start_n_is_one():
    """think_harder with a neutral/absent abstraction reports start_n == 1 —
    today's value exactly (decision-equivalence)."""
    base = _agent()
    th = at.think_harder(base.s, "cs", ["bio"])
    assert th["start_n"] == 1


# =========================================================================== #
# 2. HIGH ABSTRACTION => higher order floor.
# =========================================================================== #
def test_high_abstraction_raises_the_order_floor():
    """A high abstraction (=+3 -> floor 4) drops the surface (order-2) matches,
    keeping only the deepest meta-shape ones — 'reach for higher-order first'."""
    neu = _agent({"abstraction": 0.0})
    hi = _agent({"abstraction": +3.0})
    res_neu = at.find_analogies(neu.s, "cs", ["bio"])
    res_hi = at.find_analogies(hi.s, "cs", ["bio"])
    # neutral keeps surface matches; high-abstraction keeps ONLY order >= 4.
    assert 2 in _orders(res_neu)
    assert res_hi, "expected at least one high-order match to survive the floor"
    assert all(r["order_n"] >= 4 for r in res_hi), _orders(res_hi)
    # strictly FEWER (the surface matches were filtered out).
    assert len(res_hi) < len(res_neu)


def test_high_abstraction_raises_think_harder_start_n():
    """think_harder with a high abstraction starts higher up the order ladder."""
    hi = _agent({"abstraction": +3.0})
    th = at.think_harder(hi.s, "cs", ["bio"])
    assert th["start_n"] == 4
    # and every returned analogy respects the floor.
    assert all(a["order_n"] >= 4 for a in th["analogies"]), th["analogies"]


# =========================================================================== #
# 3. HIGH SKEPTICISM => higher min_score AND fewer accepted analogies.
# =========================================================================== #
def test_high_skepticism_raises_min_score_and_prunes_analogies():
    """A skeptical temperament (=+3 -> min_score 3) demands more shared
    discriminative structure, returning FEWER, better-supported matches."""
    neu = _agent({"skepticism": 0.0})
    hi = _agent({"skepticism": +3.0})
    assert asr._skepticism_min_score(hi) == 3
    res_neu = at.find_analogies(neu.s, "cs", ["bio"])
    res_hi = at.find_analogies(hi.s, "cs", ["bio"])
    assert len(res_hi) < len(res_neu)          # skepticism pruned the weak ones
    assert res_hi, "the strongly-supported matches must survive"
    # every surviving match clears the skeptical floor (checked on the graph's
    # own discriminative-structure count, the SAME quantity the gate uses).
    for r in res_hi:
        assert asr._discriminative_struct(r["transform_key"]) >= 3


# =========================================================================== #
# 4. EXPLICIT caller args OVERRIDE the trait-derived defaults.
# =========================================================================== #
def test_explicit_order_n_pins_the_abstraction_floor_off():
    """An explicit legacy `order_n` (as every historical caller passes) pins the
    abstraction floor OFF, so a high-abstraction agent keeps ALL matches — the
    explicit-pin-wins precedence the mint gate established."""
    hi = _agent({"abstraction": +3.0})
    res_traited = at.find_analogies(hi.s, "cs", ["bio"])          # floor active
    res_explicit = at.find_analogies(hi.s, "cs", ["bio"], order_n=4)  # pinned off
    assert all(r["order_n"] >= 4 for r in res_traited)
    assert 2 in _orders(res_explicit)               # surface matches back
    assert len(res_explicit) > len(res_traited)


def test_explicit_min_score_overrides_skepticism():
    """An explicit `min_score=1` beats a high-skepticism agent's derived floor."""
    hi = _agent({"skepticism": +3.0})
    res_traited = at.find_analogies(hi.s, "cs", ["bio"])
    res_explicit = at.find_analogies(hi.s, "cs", ["bio"], min_score=1)
    assert len(res_explicit) > len(res_traited)


def test_explicit_start_n_overrides_think_harder_floor():
    """An explicit start_n pins think_harder's abstraction floor off."""
    hi = _agent({"abstraction": +3.0})
    th_traited = at.think_harder(hi.s, "cs", ["bio"])
    th_explicit = at.think_harder(hi.s, "cs", ["bio"], start_n=1)
    assert th_traited["start_n"] == 4
    assert th_explicit["start_n"] == 1
    # pinning the floor off returns the surface matches too.
    assert th_explicit["n_found"] > th_traited["n_found"]


# =========================================================================== #
# 5. HONEST INDEPENDENCE — three traits, three knobs, no single 'strictness'.
# =========================================================================== #
def test_three_traits_drive_three_independent_knobs():
    """THE HEADLINE. A PERMISSIVE-openness + HIGH-skepticism agent (abstraction
    neutral) has a LOOSE mint gate BUT a HIGH analogy floor — verified on REAL
    find_analogies + mint_referents_from_relations calls. Permissive-minting yet
    skeptical-matching: a real personality shape, not one global dial."""
    neutral = _agent()
    mixed = _agent({"openness": +3.0, "skepticism": +3.0, "abstraction": 0.0})

    # --- the MINT knob (openness) — loosened. ---
    mint_neu = rg.mint_referents_from_relations(neutral.s, "hw")
    mint_mix = rg.mint_referents_from_relations(mixed.s, "hw")
    # openness=+3 flips the noun-dominant bright line + widens the phrase cut.
    assert mint_mix["gate"]["require_noun_dominant_head"] is False
    assert mint_neu["gate"]["require_noun_dominant_head"] is True
    # so the permissive agent MINTS strictly MORE referents than the neutral one.
    assert mint_mix["minted"] > mint_neu["minted"], (mint_mix, mint_neu)
    assert mint_mix["refused"] < mint_neu["refused"]

    # --- the ANALOGY knob (skepticism) — tightened, INDEPENDENTLY. ---
    ana_neu = at.find_analogies(neutral.s, "cs", ["bio"])
    ana_mix = at.find_analogies(mixed.s, "cs", ["bio"])
    # the SAME agent whose mint gate is LOOSE has a HIGH analogy floor: FEWER
    # analogies than the neutral agent (skepticism raised min_score to 3).
    assert asr._skepticism_min_score(mixed) == 3
    assert len(ana_mix) < len(ana_neu), (len(ana_mix), len(ana_neu))
    # and abstraction stayed neutral, so surface (order-2) matches are still
    # present (the order floor did NOT move) — the third knob is untouched.
    assert asr._abstraction_min_order(mixed) == 2
    assert 2 in _orders(ana_mix)


def test_permissive_openness_does_not_loosen_the_analogy_floor():
    """Openness drives ONLY the mint gate: a purely-permissive agent (openness up,
    skepticism/abstraction neutral) returns the SAME analogies as neutral — the
    mint knob and the analogy floor are genuinely independent."""
    neutral = _agent()
    open_only = _agent({"openness": +3.0})
    res_neu = at.find_analogies(neutral.s, "cs", ["bio"])
    res_open = at.find_analogies(open_only.s, "cs", ["bio"])
    # openness moved the mint gate but NOT the analogy floor/score. The
    # skepticism/abstraction trait Concepts were never minted (set_trait_seed
    # mints only the named trait), so the derivation reads None => the caller
    # uses today's defaults (min_score 1, order floor 2) — same as neutral.
    assert asr._skepticism_min_score(open_only) is None
    assert asr._abstraction_min_order(open_only) is None
    assert len(res_open) == len(res_neu)


def test_skepticism_does_not_touch_the_mint_gate():
    """Skepticism drives ONLY the analogy floor: a purely-skeptical agent
    (skepticism up, openness/abstraction neutral) leaves the mint gate at today's
    conservative defaults — no cross-talk into the mint knob."""
    a = _agent({"skepticism": +3.0})
    mint = rg.mint_referents_from_relations(a.s, "hw")
    # openness is at its seeded default (-1, conservative) => strict gate.
    assert mint["gate"]["require_noun_dominant_head"] is True
    assert mint["gate"]["max_content_words"] == 3

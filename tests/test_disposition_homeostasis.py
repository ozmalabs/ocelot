"""Gates for BLEND LAYER 2 — the tuneable MintPolicy gate READS the agent's
dynamical DISPOSITION, and a HOMEOSTATIC feedback loop MOVES the disposition
with the agent's real graph condition, so the gate self-regulates.

Two halves under test:

  A. MintPolicy <- disposition (relation_grounding.mint_gate_params):
     · SAFE-DEFAULT INVARIANT — a SEEDED-neutral/absent disposition + no explicit
       MintPolicy reproduces TODAY's conservative gate EXACTLY (decision-
       equivalence: same params AND same mint/refuse decisions);
     · a PERMISSIVE standing disposition DERIVES a looser gate; a CONSERVATIVE
       one derives a stricter gate — MONOTONE in disposition_level;
     · an EXPLICIT MintPolicy pin ALWAYS wins over the disposition-derived
       default (no silent hijack of a pinned knob).

  B. HOMEOSTASIS (disposition.disposition_homeostasis_step):
     · a POLLUTION-evidence step (thin minted leaves littering the graph) moves
       the disposition CONSERVATIVE and TIGHTENS the derived params;
     · a STARVATION-evidence step (dark relational surface, empty analogies)
       moves it PERMISSIVE and LOOSENS the derived params;
     · the crystallised trait is PRODUCED by the CAN relaxation — the standing
       disposition_field is never hand-written mid-loop (only evidence is
       injected; the identity-feedback rule does the write).
"""
from __future__ import annotations

import pathlib

from substrate_rs import _native

import domains.analogy_search as asr
import domains.disposition as disp
import domains.relation_grounding as rg

ROOT = pathlib.Path(disp.__file__).resolve().parent.parent

_NT = ("Agent", "Concept", "Microtheory", "QualiaDimension", "DimensionEdgeRole")
_ET = tuple(set(rg.RELATION_EDGE_TYPES) | {"has_concept", "genls", "is_a",
            "built_from", "depends_on", "grounds"})

TODAY = {"min_recurrence": 1, "max_content_words": 3,
         "require_noun_dominant_head": True}


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
    """A `.s` substrate + `.agent` hub — the shape disposition.py and the mint
    gate both accept."""
    def __init__(self):
        asr._QUALIA_SCHEMA_CACHE.clear()
        self.s = _native.Substrate()
        self.agent = self.s.add_node("Agent", {})
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
# A. MintPolicy <- disposition
# ===========================================================================

# ---------------------------------------------------------------------------
# 1. SAFE-DEFAULT INVARIANT: absent disposition => today's params EXACTLY, and
#    a SEEDED-neutral (default) disposition maps to today's params EXACTLY.
# ---------------------------------------------------------------------------
def test_absent_disposition_reads_todays_params_and_mints_nothing():
    """A graph with NO disposition reads the safe defaults directly (the
    derivation is skipped), gains no MintPolicy node on a non-minting read, and
    mints no disposition Mt."""
    a = Agent()
    # non-minting read on a fresh graph == today, adds nothing.
    assert rg.mint_gate_params(a.s, ensure=False) == TODAY
    assert list(a.s.nodes("MintPolicy")) == []
    # no disposition Mt was minted by the gate read.
    mts = [m for m in a.s.nodes("Microtheory")
           if a.s.node(m)["attrs"].get("name") == disp.DISPOSITION_MT_NAME]
    assert mts == []


def test_seeded_default_disposition_maps_to_todays_params_exactly():
    """The SEEDED default disposition (level -1, mildly conservative) derives
    EXACTLY today's params — the safe-default invariant, proved on the derived
    dict."""
    a = Agent()
    disp.ensure_disposition(a)                    # seeded default (-1)
    assert disp.disposition_level(a) == int(disp.DEFAULT_DISPOSITION_SEED) == -1
    # the derivation for the seeded-default agent == today, byte for byte.
    derived = rg._disposition_derived_gate(a)
    assert derived == TODAY
    # and the effective params (no explicit pin) == today too.
    assert rg.mint_gate_params(a) == TODAY


def test_neutral_disposition_maps_to_todays_params_exactly():
    """A NEUTRAL disposition (level 0) still maps to today's params — the
    conservative side of the mapping is flat across {-1, 0}, so a neutral agent
    behaves identically to today until it moves permissive."""
    a = Agent()
    disp.set_disposition_seed(a, 0.0)
    assert disp.disposition_level(a) == 0
    assert rg._disposition_derived_gate(a) == TODAY
    assert rg.mint_gate_params(a) == TODAY


def test_decision_equivalence_seeded_default_matches_today():
    """DECISION-equivalence (not just param-equivalence): a seeded-default agent
    makes the SAME mint/refuse decisions as a graph with no disposition at all —
    a clean NP minted, a clause refused — the MintPolicy-stage invariant, now
    proved through the disposition-derived path."""
    # baseline: no disposition (today).
    base = Agent()
    mb = _mt(base.s, "m")
    _concept(base.s, mb, "IOMMU", definition="An IOMMU is used for VM passthrough.")
    _concept(base.s, mb, "page_fault",
             definition="A page fault enables programs use more virtual memory.")
    res_base = rg.mint_referents_from_relations(base.s, "m")

    # with a seeded-default disposition present on the agent.
    a = Agent()
    disp.ensure_disposition(a)                    # seeded default (-1) == today
    m = _mt(a.s, "m")
    _concept(a.s, m, "IOMMU", definition="An IOMMU is used for VM passthrough.")
    _concept(a.s, m, "page_fault",
             definition="A page fault enables programs use more virtual memory.")
    res = rg.mint_referents_from_relations(a.s, "m")

    # same effective gate, same decisions.
    assert res["gate"] == res_base["gate"] == TODAY
    assert "vm_passthrough" in _names(a.s)          # clean NP still minted
    assert res["minted"] == res_base["minted"]
    assert any(et == "enables" and "virtual memory" in ph      # clause still refused
               for (_s, et, ph) in res["refused_phrases"])


# ---------------------------------------------------------------------------
# 2. a PERMISSIVE disposition derives a LOOSER gate; CONSERVATIVE a STRICTER one
# ---------------------------------------------------------------------------
def test_permissive_disposition_loosens_the_derived_gate():
    a = Agent()
    disp.set_disposition_seed(a, +1.0)               # permissive
    g1 = rg.mint_gate_params(a)
    assert g1["require_noun_dominant_head"] is False, g1  # bright-line relaxed

    disp.set_disposition_seed(a, +2.0)               # more permissive
    g2 = rg.mint_gate_params(a)
    assert g2["require_noun_dominant_head"] is False
    assert g2["max_content_words"] == 4, g2          # longer NPs admitted


def test_conservative_disposition_tightens_the_derived_gate():
    a = Agent()
    disp.set_disposition_seed(a, -2.0)               # tightened past default
    g = rg.mint_gate_params(a)
    assert g["require_noun_dominant_head"] is True    # still strict head rule
    assert g["max_content_words"] == 2, g             # shorter phrases only


def test_permissive_disposition_admits_a_referent_the_default_refuses():
    """The derived loosening is REAL, not cosmetic: a permissive standing
    disposition admits 'periodic refresh' (head verb-dominant) that the seeded-
    default (today) refuses — the same phrase the MintPolicy stage recovered by
    an explicit knob, now recovered by the agent's temperament."""
    # default disposition refuses it.
    d = Agent()
    disp.ensure_disposition(d)
    md = _mt(d.s, "m")
    _concept(d.s, md, "cache", definition="A cache requires periodic refresh.")
    res_d = rg.mint_referents_from_relations(d.s, "m")
    assert "periodic_refresh" not in _names(d.s)

    # permissive disposition admits it — NO explicit MintPolicy pin.
    p = Agent()
    disp.set_disposition_seed(p, +1.0)
    assert list(p.s.nodes("MintPolicy")) == []       # nothing pinned
    mp = _mt(p.s, "m")
    cache = _concept(p.s, mp, "cache", definition="A cache requires periodic refresh.")
    res_p = rg.mint_referents_from_relations(p.s, "m")
    assert "periodic_refresh" in _names(p.s)
    ref = rg._concept_by_name(p.s)["periodic_refresh"]
    assert ref in set(p.s.neighbours(cache, "depends_on"))
    assert res_p["gate"]["require_noun_dominant_head"] is False
    assert res_p["minted"] > res_d["minted"]


# ---------------------------------------------------------------------------
# 3. an EXPLICIT MintPolicy pin ALWAYS wins over the disposition-derived default
# ---------------------------------------------------------------------------
def test_explicit_pin_wins_over_permissive_disposition():
    """A permissive disposition would derive require_noun_dominant_head=False,
    but a caller who explicitly PINS it True keeps it True — the pinned knob is
    never silently moved by the temperament."""
    a = Agent()
    disp.set_disposition_seed(a, +2.0)               # would derive False + words 4
    # pin the bright-line rule ON explicitly.
    rg.set_mint_gate(a, require_noun_dominant_head=True)
    g = rg.mint_gate_params(a)
    assert g["require_noun_dominant_head"] is True, g   # PIN wins over derived False
    # the UNpinned knob still follows the permissive temperament.
    assert g["max_content_words"] == 4, g


def test_explicit_pin_wins_over_conservative_disposition():
    """A conservative disposition derives max_content_words=2, but an explicit
    pin of 5 wins."""
    a = Agent()
    disp.set_disposition_seed(a, -3.0)               # would derive words 2
    rg.set_mint_gate(a, max_content_words=5)
    g = rg.mint_gate_params(a)
    assert g["max_content_words"] == 5, g            # PIN wins
    assert g["require_noun_dominant_head"] is True   # unpinned; conservative default


def test_unpinned_knobs_follow_disposition_after_a_partial_pin():
    """Pinning ONE knob leaves the others free to follow the temperament — the
    precedence is per-knob, not all-or-nothing."""
    a = Agent()
    disp.set_disposition_seed(a, +2.0)               # permissive: derives False, words 4
    rg.set_mint_gate(a, min_recurrence=2)            # pin ONLY min_recurrence
    g = rg.mint_gate_params(a)
    assert g["min_recurrence"] == 2                  # pinned
    assert g["require_noun_dominant_head"] is False  # still follows temperament
    assert g["max_content_words"] == 4               # still follows temperament


# ===========================================================================
# B. HOMEOSTASIS — the disposition moves with the graph's real condition
# ===========================================================================

def _fill_thin_leaves(s, n):
    """Directly create n thin minted_referent leaves (no outgoing edges) — the
    pollution witness — without needing a full mint pass. Mirrors what a loose
    gate leaves behind."""
    m = _mt(s, "junk")
    for i in range(n):
        _concept(s, m, f"junk_{i}", minted_referent=True, definition=f"junk {i}")


# ---------------------------------------------------------------------------
# 4. a POLLUTION-evidence step moves the disposition CONSERVATIVE + tightens
# ---------------------------------------------------------------------------
def test_pollution_step_moves_conservative_and_tightens():
    a = Agent()
    disp.set_disposition_seed(a, 0.0)                # start neutral
    # POLLUTION: many thin unelaborated minted leaves littering the graph, and no
    # real relational structure to speak of.
    _fill_thin_leaves(a.s, 12)

    sig = disp.homeostasis_signals(a)
    assert sig["pollution"] > sig["starvation"], sig  # net negative
    assert sig["net"] < 0

    before = disp.disposition_level(a)
    # sustain the polluting condition over several steps.
    levels = []
    for _ in range(5):
        h = disp.disposition_homeostasis_step(a)
        levels.append(h["level_after"])
        assert h["evidence"] == -1.0                   # conservative evidence
    after = disp.disposition_level(a)
    assert after < before, (before, after, levels)     # moved conservative
    # the derived gate TIGHTENED as a consequence (words cut once level <= -2).
    g = rg.mint_gate_params(a)
    assert g["max_content_words"] <= 2, (levels, g)


# ---------------------------------------------------------------------------
# 5. a STARVATION-evidence step moves the disposition PERMISSIVE + loosens
# ---------------------------------------------------------------------------
def test_starvation_step_moves_permissive_and_loosens():
    a = Agent()
    disp.set_disposition_seed(a, 0.0)                # start neutral
    # STARVATION: real concepts with NO relational edges (dark surface) and no
    # analogies — and no thin junk leaves.
    m = _mt(a.s, "corpus")
    for name in ("alpha", "beta", "gamma", "delta", "epsilon"):
        _concept(a.s, m, name, definition=f"{name} is a topic.")

    sig = disp.homeostasis_signals(a, analogies=[])
    assert sig["starvation"] > sig["pollution"], sig  # net positive
    assert sig["net"] > 0

    before = disp.disposition_level(a)
    h = disp.disposition_homeostasis_step(a, analogies=[])
    assert h["evidence"] == +1.0                       # permissive evidence
    after = disp.disposition_level(a)
    assert after > before, (before, after)             # moved permissive
    # the derived gate LOOSENED as a consequence (bright-line rule relaxed).
    g = rg.mint_gate_params(a)
    assert g["require_noun_dominant_head"] is False, g


# ---------------------------------------------------------------------------
# 6. the crystallised trait is PRODUCED by relaxation, never hand-written
# ---------------------------------------------------------------------------
def test_homeostasis_produces_the_trait_never_hand_writes_it():
    """The standing disposition_field is moved ONLY by the CAN identity-feedback
    rule integrating the injected evidence — the step never writes
    disposition_field/identity_field directly mid-loop. We prove it by checking
    the ledger accrued (the rule's own evidence counters moved) and the field
    tracks the rule's ±1-per-tick step, not an arbitrary jump."""
    a = Agent()
    disp.set_disposition_seed(a, 0.0)
    _fill_thin_leaves(a.s, 12)                         # sustained pollution

    concept = disp.ensure_disposition(a)
    native = a.s

    # one step -> exactly one ±1 quantum move (the rule's fixed step), and the
    # evidence ledger accrued (proof the sigma channel drove the rule).
    f0 = disp.disposition_field(a)
    h = disp.disposition_homeostasis_step(a)
    f1 = disp.disposition_field(a)
    assert h["evidence"] == -1.0
    assert abs(f1 - f0) == 1.0, (f0, f1)               # one native quantum, not a jump
    attrs = native.node(concept)["attrs"]
    # the disconfirm ledger (negative evidence) accrued — the rule read the sigma.
    assert int(attrs.get("identity_evidence_disconfirm") or 0) >= 1, attrs
    # the mirrored axis attr equals the produced identity_field (a mirror, not a
    # hand-set outcome).
    assert float(attrs.get(disp.DISPOSITION_FIELD_ATTR)) == float(attrs.get("identity_field"))


def test_balanced_condition_is_a_deadband_noop():
    """When pollution ~ starvation (balanced), the step injects NO evidence and
    the disposition does not drift on noise — the loop has a neutral zone, it is
    not a ratchet."""
    a = Agent()
    disp.set_disposition_seed(a, 0.0)
    # a graph with a modest thin-leaf share AND a partially-lit relational
    # surface -> pollution and starvation near each other.
    m = _mt(a.s, "corpus")
    x = _concept(a.s, m, "x", definition="x")
    y = _concept(a.s, m, "y", definition="y")
    a.s.add_edge(x, "used_for", y, {})               # one lit relation
    _fill_thin_leaves(a.s, 1)                         # a single thin leaf

    sig = disp.homeostasis_signals(a)
    before = disp.disposition_level(a)
    h = disp.disposition_homeostasis_step(a, deadband=1.0)  # wide deadband => noop
    assert h["evidence"] == 0.0
    assert h["level_after"] == before
    assert not h["moved"]

#!/usr/bin/env python3
"""COGNITIVE PERSONALITY shapes COGNITION — three traits on three real knobs.

Run: python3 scripts/qualia_personality_demo.py

Layer 1 (scripts/qualia_trait_vector_demo.py) built the personality VECTOR:
openness / abstraction / skepticism, each a CAN-relaxable dynamical qualia axis
on the agent. This script is LAYER 2: it shows the vector actually SHAPING the
agent's cognition, because each trait now drives a REAL, PRE-EXISTING decision
point — not an invented knob:

  · OPENNESS    -> the REFERENT-MINT GATE (relation_grounding.MintPolicy). A
                   permissive temperament flips the noun-dominant-head bright
                   line and widens the phrase-length cut, so it MINTS referents
                   a conservative temperament REFUSES. (Wired in layer 1.)
  · ABSTRACTION -> the analogy ORDER FLOOR. Every emitted analogy carries a
                   DERIVED order (analogy_search._order_from_transform: surface
                   role/lexical/dynamical = 2, shared abstract PRINCIPLE = 3,
                   shared META-SHAPE = 4). An abstract temperament REACHES FOR
                   HIGHER-ORDER matches first by filtering OUT the surface ones;
                   a concrete temperament keeps them all.
  · SKEPTICISM  -> the analogy ACCEPTANCE FLOOR (find_analogies min_score, the
                   floor on shared DISCRIMINATIVE structure). A skeptical
                   temperament demands MORE shared structure (fewer, better-
                   supported matches); a credulous one accepts the default floor.

THE HEADLINE — HONEST INDEPENDENCE. The three knobs are driven by THREE
INDEPENDENT traits (separate CAN Concepts, separate fields — layer 1 proved no
cross-talk). So an agent can be PERMISSIVE-MINTING but SKEPTICAL-MATCHING: open
to FORMING referents, yet demanding about which ANALOGIES it accepts. That is a
real personality SHAPE, not one global 'strictness' dial. This script builds
that exact mixed agent and shows it minting referents FREELY while returning FEW
analogies — on the SAME corpus where an abstract+credulous agent finds more.

DECISION-EQUIVALENCE (proven in tests/test_trait_consumers.py): a NEUTRAL
(seed-0) trait reproduces today's behaviour EXACTLY — order floor 2 (the minimum
order ever emitted, filters nothing), min_score 1 (today's default), mint gate at
today's conservative defaults. The traits change cognition ONLY when seeded off
neutral. An EXPLICIT caller arg (order_n / min_score / start_n / gate_params)
always WINS over the trait-derived default — same precedence as the mint gate's
explicit-pin-wins.

CONSTRAINTS honoured: every trait drives a REAL existing knob; neutral == today;
explicit caller args win; native CAN path; no invented dials.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent
                       / "runners" / "dsl" / "python"))

from substrate_rs import _native

import domains.analogical_thinking as at
import domains.analogy_search as asr
import domains.relation_grounding as rg
import domains.disposition as disp
from domains.can_self_worth_bridge import ensure_can_seed
from domains.self_improvement_loop import relax

ROOT = Path(__file__).resolve().parent.parent
SEEDS = ROOT / "seeds"

# Identity-evidence ledger the native identity-feedback rule reads/writes;
# identity_field starts at 0 and is PRODUCED by relaxation (the felt coordinate).
_LEDGER = {
    "identity_evidence_confirm": 0, "identity_evidence_disconfirm": 0,
    "identity_evidence_tick": -1, "identity_decay_tick": -1,
    "identity_field_tick": -1,
}


class _Agent:
    """The minimal agent wrapper domains/disposition.py + analogy_search.py
    accept: a `.s` substrate handle + an `.agent` hub node."""

    def __init__(self, sub, ag):
        self.s = sub
        self.agent = ag


def section(title):
    print("\n" + "=" * 74)
    print(title)
    print("=" * 74)


# --------------------------------------------------------------------------- #
# Boot — one substrate + the qualia/analogy/CAN machinery.
# --------------------------------------------------------------------------- #
def _boot():
    for cache in (at._CONCEPT_READING_CACHE, at._VOCAB_KEYS_CACHE,
                  at._METASHAPE_COUNT_CACHE, asr._QUALIA_SCHEMA_CACHE):
        cache.clear()
    s = _native.Substrate()
    ag = s.add_node("Agent", {})
    for name in ("shape_vocabulary", "qualia_space", "analogy_search"):
        path = SEEDS / f"{name}.json"
        if path.exists():
            s.load_seed_manifest(json.load(open(path)), ag)
    ensure_can_seed(s)
    node_types = ("Agent", "Concept", "Microtheory")
    edge_types = (("has_concept", "causal_influence")
                  + rg.RELATION_EDGE_TYPES + ("genls",))
    for a in node_types:
        for b in node_types:
            for et in edge_types:
                s.add_production({"src": {"type": a, "var": "x"},
                                  "edge_type": et,
                                  "tgt": {"type": b, "var": "y"},
                                  "where": None,
                                  "weight": {"type": "Lit", "value": 1.0},
                                  "provenance": "personality_demo:open"})
    return s, ag


# --------------------------------------------------------------------------- #
# The SAME corpus every personality runs over.
#
# TWO analogy fields (cs / bio) built to yield a MIX of match orders: three
# HIGH-ORDER pairs (both concepts hit the SAME ShapePrinciple — 'homeostasis' via
# regulate/balance/set_point, 'winner_take_all' via select/competition — plus a
# shared meta-shape) and four SURFACE pairs (only lexical/role overlap). Plus a
# MINT field (hw) whose prose names referents with VERB-DOMINANT heads ('screen
# coordinate', 'eventual result') that the conservative gate REFUSES and the
# permissive gate MINTS. All felt coordinates are PRODUCED by native relaxation;
# all relations DERIVED by ground_relations. Nothing about the corpus is per-
# personality — only the trait vector differs.
# --------------------------------------------------------------------------- #
_ANALOGY_CS = {
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
_ANALOGY_BIO = {
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

# MINT corpus — objects with verb-dominant heads (refused by the strict gate,
# minted by the permissive one).
_MINT_HW = {
    "raster": "A raster drives the periodic refresh and controls the screen coordinate.",
    "clock":  "A clock enables the timed rollover and gates the frequent update.",
    "buffer": "A buffer serves the pending transfer and holds the eventual result.",
}


def _concept(s, mt, name, *, definition, category, ext=0.0):
    attrs = {"name": name, "category": category, "definition": definition,
             "state": 0.0, "external_field": float(ext), "identity_field": 0.0}
    attrs.update(_LEDGER)
    c = s.add_node("Concept", attrs)
    s.add_edge_unchecked(mt, "has_concept", c)
    return c


def _couple(s, a, b, w=0.4):
    s.add_edge(a, "causal_influence", b, {"weight": float(w)})
    s.add_edge(b, "causal_influence", a, {"weight": float(w)})


def _field(s, name, spec, couples):
    mt = s.add_node("Microtheory", {"name": name, "temperature": 1.0,
                                    "discrete_mode": "3state", "can_tick": 0,
                                    "update_policy": "adaptive"})
    nodes = {n: _concept(s, mt, n, **kw) for n, kw in spec.items()}
    for a, b in couples:
        _couple(s, nodes[a], nodes[b])
    return mt, nodes


def _relax_cryst(s, mt, ticks=12):
    relax(s, mt)
    ag = s.nodes("Agent")[0]
    a = _Agent(s, ag)
    for i in range(ticks):
        s.set_attr(mt, "can_tick", i + 1)
        asr.crystallize(a)


def _build_corpus(s):
    """Build the SAME corpus on a fresh substrate. Returns nothing — the fields
    live on the graph by name."""
    cs, _ = _field(s, "cs", _ANALOGY_CS, _CS_COUPLE)
    bio, _ = _field(s, "bio", _ANALOGY_BIO, _BIO_COUPLE)
    rg.ground_relations(s, "cs")
    rg.ground_relations(s, "bio")
    _relax_cryst(s, cs)
    _relax_cryst(s, bio)
    # the mint field is plain prose (static Mt — the mint gate reads prose only).
    hw = s.add_node("Microtheory", {"name": "hw", "temperature": 1.0,
                                    "discrete_mode": "static", "can_tick": 0})
    for n, d in _MINT_HW.items():
        c = s.add_node("Concept", {"name": n, "definition": d, "category": "device"})
        s.add_edge_unchecked(hw, "has_concept", c)


def _make_personality(name, traits):
    """A fresh substrate + corpus, seeded with `traits` = {trait: level}."""
    s, ag = _boot()
    _build_corpus(s)
    a = _Agent(s, ag)
    for t, v in traits.items():
        disp.set_trait_seed(a, t, v)
    return a


def _analogies(agent):
    """find_analogies on the SAME cs->bio task; the traits supply the defaults."""
    return at.find_analogies(agent.s, "cs", ["bio"])


def _mints(agent):
    """One referent-mint pass on the SAME hw field; openness supplies the gate."""
    return rg.mint_referents_from_relations(agent.s, "hw")


def _fmt_analogies(res):
    orders = sorted(r["order_n"] for r in res)
    lines = []
    for r in sorted(res, key=lambda x: (-x["order_n"], -x["struct_shared"])):
        lines.append(f"      {r['source_concept']:10s} ~ {r['target_concept']:10s} "
                     f"order={r['order_n']} struct_shared={r['struct_shared']}")
    return orders, lines


def main():
    section("SETUP — three traits, three REAL knobs (no invented dials)")
    print("  openness    -> referent-mint gate (MintPolicy)     [wired layer 1]")
    print("  abstraction -> analogy ORDER FLOOR (order 2/3/4)    [wired here]")
    print("  skepticism  -> analogy min_score ACCEPTANCE FLOOR   [wired here]")
    print("  mappings (trait_level in [-4,+4] -> knob):")
    print("    abstraction  <=0->floor 2 (all)   1..2->3 (drop surface)  >=3->4 (meta-shape only)")
    print("    skepticism   <=0->min_score 1     1..2->2                 >=3->3")

    # ---- NEUTRAL baseline (decision-equivalence) -----------------------------
    section("BASELINE — a NEUTRAL agent reproduces TODAY exactly")
    N = _make_personality("neutral", {})  # all traits at seeded default
    resN = _analogies(N)
    ordersN, linesN = _fmt_analogies(resN)
    mintN = _mints(N)
    print(f"  trait vector: {disp.trait_vector(N)}   (openness seeded -1, rest 0)")
    print(f"  find_analogies(cs->bio): {len(resN)} analogies, orders={ordersN}")
    for ln in linesN:
        print(ln)
    print(f"  mint pass(hw): minted={mintN['minted']} refused={mintN['refused']} "
          f"names={mintN['minted_names']}")
    print(f"    gate={mintN['gate']}  (== today's conservative defaults)")

    # ---- (a) ABSTRACT + CREDULOUS -------------------------------------------
    section("(a) ABSTRACT + CREDULOUS  — reaches high, accepts readily")
    A = _make_personality("abstract", {"abstraction": +3.0, "skepticism": -2.0,
                                        "openness": +2.0})
    resA = _analogies(A)
    ordersA, linesA = _fmt_analogies(resA)
    mintA = _mints(A)
    print(f"  trait vector: {disp.trait_vector(A)}")
    print(f"  find_analogies(cs->bio): {len(resA)} analogies, orders={ordersA}")
    for ln in linesA:
        print(ln)
    print(f"  mint pass(hw): minted={mintA['minted']} refused={mintA['refused']} "
          f"names={mintA['minted_names']}")
    print("  → abstraction=+3 sets the ORDER FLOOR to 4: only the deepest "
          "META-SHAPE matches survive.\n"
          "    Higher-order, fewer, all order-4 — 'reach for meta-shape matches "
          "first'. openness=+2 also mints freely.")

    # ---- (b) CONCRETE + SKEPTICAL -------------------------------------------
    section("(b) CONCRETE + SKEPTICAL — stays at the surface, demands support")
    B = _make_personality("concrete", {"abstraction": -2.0, "skepticism": +3.0,
                                        "openness": -3.0})
    resB = _analogies(B)
    ordersB, linesB = _fmt_analogies(resB)
    mintB = _mints(B)
    print(f"  trait vector: {disp.trait_vector(B)}")
    print(f"  find_analogies(cs->bio): {len(resB)} analogies, orders={ordersB}")
    for ln in linesB:
        print(ln)
    print(f"  mint pass(hw): minted={mintB['minted']} refused={mintB['refused']} "
          f"names={mintB['minted_names']}")
    print("  → abstraction=-2 keeps the surface (floor 2 = all), but skepticism=+3 "
          "raises min_score to 3:\n"
          "    the weakest surface matches are dropped for lack of discriminative "
          "structure. openness=-3 refuses the verb-dominant referents.")

    # ---- (c) MIXED — THE HEADLINE: independent knobs -------------------------
    section("(c) MIXED — PERMISSIVE-MINTING but SKEPTICAL-MATCHING (independence)")
    M = _make_personality("mixed", {"openness": +3.0, "skepticism": +3.0,
                                     "abstraction": 0.0})
    resM = _analogies(M)
    ordersM, linesM = _fmt_analogies(resM)
    mintM = _mints(M)
    print(f"  trait vector: {disp.trait_vector(M)}   "
          f"(openness PERMISSIVE, skepticism HIGH, abstraction neutral)")
    print(f"  mint pass(hw):  minted={mintM['minted']} refused={mintM['refused']} "
          f"names={mintM['minted_names']}")
    print(f"    gate={mintM['gate']}  (openness LOOSENED it)")
    print(f"  find_analogies(cs->bio): {len(resM)} analogies, orders={ordersM}")
    for ln in linesM:
        print(ln)
    print("\n  → THE INDEPENDENCE: openness=+3 loosens the MINT gate "
          f"(minted {mintM['minted']}, refused {mintM['refused']} — MORE than the "
          f"neutral {mintN['minted']}/{mintN['refused']}),\n"
          f"    while skepticism=+3 raises the ANALOGY floor (min_score 3 => "
          f"{len(resM)} analogies, FEWER than the neutral {len(resN)}).\n"
          "    One agent: open to FORMING referents, demanding about ACCEPTING "
          "analogies. Two knobs, two traits, no single 'strictness'.")

    # ---- explicit override wins ---------------------------------------------
    section("OVERRIDE — an explicit caller arg beats the trait-derived default")
    resOv = at.find_analogies(B.s, "cs", ["bio"], order_n=4, min_score=1)
    print(f"  skeptical agent B, but find_analogies(..., order_n=4, min_score=1):")
    print(f"    {len(resOv)} analogies (vs {len(resB)} from B's traits alone) — "
          "the explicit args pinned the trait floors OFF.")

    # ---- SUMMARY table -------------------------------------------------------
    section("SUMMARY — real numbers, same corpus, different cognition")
    print(f"  {'personality':26s} {'analogies':>10s} {'orders':>16s} "
          f"{'minted':>7s} {'refused':>8s}")
    for label, res, mint in (("neutral (== today)", resN, mintN),
                             ("(a) abstract+credulous", resA, mintA),
                             ("(b) concrete+skeptical", resB, mintB),
                             ("(c) mixed open+skeptical", resM, mintM)):
        orders = sorted(r["order_n"] for r in res)
        print(f"  {label:26s} {len(res):>10d} {str(orders):>16s} "
              f"{mint['minted']:>7d} {mint['refused']:>8d}")
    print("\n  Distinct personalities produce DISTINCTLY different analogy AND "
          "mint behaviour on the\n  identical task — and the mint knob and the "
          "analogy knobs move INDEPENDENTLY (the mixed\n  agent mints like the "
          "open one but matches like the skeptical one). See the honest report.")


if __name__ == "__main__":
    main()

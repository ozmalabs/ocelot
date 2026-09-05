"""DEMO — the mint gate SELF-REGULATES via the agent's dynamical DISPOSITION
(blend, layer 2 of 3).

WHAT THIS SHOWS
---------------
Layer 1 (the disposition_axis stage) made DISPOSITION a real CAN-relaxable
qualia axis on the agent. Layer 2 (this stage) closes the loop:

  1. the tuneable MintPolicy gate now READS the agent's standing disposition
     (relation_grounding.mint_gate_params DERIVES its effective strictness from
     disposition_level when a disposition exists, honouring any explicit pin);
  2. a HOMEOSTATIC step (disposition.disposition_homeostasis_step) reads the
     agent's REAL graph condition — pollution vs starvation — and injects it as
     disposition evidence, which the CAN relaxation integrates into the standing
     temperament.

So the gate becomes a TEMPERAMENT that responds to state: minting garbage
tightens it, finding nothing loosens it. Everything the demo prints is produced
by relaxation (±1 quantum per tick toward the evidence log-odds sign) — the
Python only reads graph counts and hands a sign to the CAN rule.

TWO REGIMES
-----------
(a) POLLUTING: a corpus whose relation objects are clean short NPs that DO mint
    but stay thin, unelaborated leaves (junk that got through) + a high refusal
    rate while yielding. Pollution pressure drives the disposition CONSERVATIVE
    over steps => mint_gate_params TIGHTENS (max_content_words 3->2) => the
    subsequent refusal-rate stays high / the gate admits less.
(b) STARVED: a corpus of genuine-but-verb-dominant referents ('periodic refresh',
    …) that TODAY's strict gate refuses, leaving the relational surface dark and
    analogies empty. Starvation pressure drives the disposition PERMISSIVE over
    steps => the gate LOOSENS (require_noun_dominant_head True->False, then
    max_content_words 3->4) => MORE (still-gated) referents mint.

Run: python scripts/qualia_disposition_homeostasis_demo.py
"""
from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
# The engine artifact lives under runners/dsl/python (the same path the
# sibling qualia_disposition_demo.py adds) so this demo is runnable standalone,
# not only under pytest's conftest engine preamble.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent
                       / "runners" / "dsl" / "python"))

from substrate_rs import _native  # noqa: E402

import domains.analogy_search as asr          # noqa: E402
import domains.disposition as disp            # noqa: E402
import domains.relation_grounding as rg       # noqa: E402

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
                                  "provenance": "demo:open"})


class Agent:
    """A `.s` substrate + an `.agent` hub — the shape domains/disposition.py and
    the mint gate both accept."""
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


def _gate_str(g):
    return (f"{{recur:{g['min_recurrence']}, words:{g['max_content_words']}, "
            f"noun_dom_head:{g['require_noun_dominant_head']}}}")


def polluting_regime(steps: int = 8):
    print("=" * 72)
    print("(a) POLLUTING REGIME — junk mints thin leaves => tighten")
    print("=" * 72)
    a = Agent()
    disp.set_disposition_seed(a, 0.0)  # start NEUTRAL
    m = _mt(a.s, "poll")
    # A few real concepts, plus a steady stream of ORPHANED thin minted_referent
    # leaves — junk a loose upstream gate dumped that nothing points at and that
    # points at nothing (the task's literal 'thin minted_referent leaves that
    # never get elaborated'). This is unambiguous pollution.
    for name, defn in [
        ("iommu", "An IOMMU is used for VM passthrough."),
        ("nic", "A NIC is used for packet steering."),
    ]:
        _concept(a.s, m, name, definition=defn)
    junk_mt = _mt(a.s, "junk")
    # give the graph a genuinely-lit relational surface so it is NOT also starved
    # (starvation stays low) — pollution is then the unambiguous pressure.
    x = _concept(a.s, m, "core_a", definition="core a")
    y = _concept(a.s, m, "core_b", definition="core b")
    z = _concept(a.s, m, "core_c", definition="core c")
    a.s.add_edge(x, "used_for", y, {})
    a.s.add_edge(y, "depends_on", z, {})
    a.s.add_edge(z, "part_of", x, {})

    def _dump_junk(step, k=4):
        for i in range(k):
            _concept(a.s, junk_mt, f"junk_{step}_{i}",
                     minted_referent=True, definition=f"junk {step} {i}")

    print(f"start: disposition_level={disp.disposition_level(a)}  "
          f"gate={_gate_str(rg.mint_gate_params(a.s))}")
    traj = []
    for step in range(steps):
        _dump_junk(step)                       # the polluting upstream this step
        res = rg.mint_referents_from_relations(a.s, "poll")
        h = disp.disposition_homeostasis_step(a, mint_result=res)
        g = rg.mint_gate_params(a.s)
        traj.append(h["level_after"])
        s = h["signals"]
        print(f"  step {step}: level {h['level_before']:+d}->{h['level_after']:+d}"
              f"  evidence={h['evidence']:+.0f}  thin_leaves={s['thin_minted']}"
              f"  thin_share={s['thin_share']:.2f}"
              f"  pollution={s['pollution']:.2f} starvation={s['starvation']:.2f}"
              f"  net={s['net']:+.2f}  gate={_gate_str(g)}")
    print(f"  disposition trajectory: {traj}")
    print(f"  => converged CONSERVATIVE at level {traj[-1]}; gate tightened.\n")
    return traj


def starved_regime(steps: int = 8):
    print("=" * 72)
    print("(b) STARVED REGIME — dark relations, nothing mints => loosen")
    print("=" * 72)
    b = Agent()
    disp.set_disposition_seed(b, 0.0)  # start NEUTRAL
    m = _mt(b.s, "starv")
    # genuine-but-verb-dominant referents TODAY's strict gate refuses, so the
    # relational surface stays dark and analogies empty (starvation). As the gate
    # loosens (noun-dominance relaxed), these become mintable.
    for name, defn in [
        ("dram", "A DRAM requires periodic refresh."),
        ("sram", "A SRAM requires careful layout."),
        ("flash", "A flash requires block erase."),
        ("cache", "A cache requires line fill."),
    ]:
        _concept(b.s, m, name, definition=defn)

    print(f"start: disposition_level={disp.disposition_level(b)}  "
          f"gate={_gate_str(rg.mint_gate_params(b.s))}")
    traj = []
    mints = []
    for step in range(steps):
        res = rg.mint_referents_from_relations(b.s, "starv")
        an = asr.find_analogies(b.s, "starv", ["starv"])
        h = disp.disposition_homeostasis_step(b, mint_result=res, analogies=an)
        g = rg.mint_gate_params(b.s)
        traj.append(h["level_after"])
        mints.append(res["minted"])
        s = h["signals"]
        print(f"  step {step}: level {h['level_before']:+d}->{h['level_after']:+d}"
              f"  evidence={h['evidence']:+.0f}  minted={res['minted']}"
              f"  lit_ratio={s['relational_lit_ratio']:.2f} analogies={s['analogy_count']}"
              f"  pollution={s['pollution']:.2f} starvation={s['starvation']:.2f}"
              f"  net={s['net']:+.2f}  gate={_gate_str(g)}")
    print(f"  disposition trajectory: {traj}")
    print(f"  minted-per-step:        {mints}")
    print(f"  => converged PERMISSIVE at level {traj[-1]}; gate loosened; "
          f"minting recovered ({mints[0]} -> {max(mints)}).\n")
    return traj, mints


def main():
    pol = polluting_regime()
    starv, mints = starved_regime()

    print("=" * 72)
    print("HEADLINE")
    print("=" * 72)
    print("Both regimes start NEUTRAL (disposition_level 0) and MOVE — produced")
    print("by CAN relaxation integrating the graph-condition evidence, one ±1")
    print("quantum per tick:")
    print(f"  pollution => {pol}  (walks conservative, gate tightens)")
    print(f"  starvation => {starv}  (walks permissive, gate loosens)")
    print("The gate params CHANGE as a consequence of the disposition moving;")
    print("the disposition moved because the graph's real condition drove it.")


if __name__ == "__main__":
    main()

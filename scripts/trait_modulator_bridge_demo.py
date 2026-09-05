"""trait_modulator_bridge_demo — a live probe of the BIDIRECTIONAL trait<->modulator
bridge (domains/trait_modulator_bridge.py). Produces (not hand-writes) three
demonstrations against the real engine:

  (A) TRAIT -> MODULATOR: a seeded HIGH-abstraction agent writes a NONZERO
      abstraction_bias that SHIFTS the modulator's resolution set-point (the
      urgency/arousal drive terms unchanged — the delta IS exactly the bias).

  (B) MODULATOR -> TRAIT: a sustained HIGH-resolution modulator crystallises the
      abstraction trait UPWARD via disposition.relax_trait — the trait is PRODUCED
      by the CAN identity-feedback rule, one ±1 quantum per tick, never hand-set.

  SAFE DEFAULT: an agent with the seeded DEFAULT traits (openness -1, abstraction
      0, skepticism 0) writes 0 to ALL THREE bias attrs, so the modulator vector
      is BYTE-IDENTICAL to a no-bridge build => emergent emotion is UNCHANGED.

  NO RUNAWAY: the full A<->B loop saturates at the trait ceiling (level +4 => a
      fixed maximal bias) and stays bounded — the SLOW crystallised trait vs the
      FAST modulator gives the timescale separation that prevents positive
      feedback from diverging.

Run:  .venv/bin/python scripts/trait_modulator_bridge_demo.py
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from substrate_rs import _native

import domains.analogy_search as asr
import domains.disposition as disp
import domains.relation_grounding as rg
import domains.trait_modulator_bridge as tmb

_NT = ("Agent", "Concept", "Microtheory", "QualiaDimension", "DimensionEdgeRole")
_ET = tuple(set(rg.RELATION_EDGE_TYPES) | {"has_concept", "genls", "is_a",
            "built_from", "depends_on", "grounds"})


class _Agent:
    """A `.s` substrate + `.agent` hub — the shape the bridge + disposition accept
    (identical to tests/test_disposition_homeostasis.py's Agent)."""

    def __init__(self):
        asr._QUALIA_SCHEMA_CACHE.clear()
        self.s = _native.Substrate()
        self.agent = self.s.add_node("Agent", {})
        for a in _NT:
            for b in _NT:
                for et in _ET:
                    self.s.add_production({
                        "src": {"type": a, "var": "x"}, "edge_type": et,
                        "tgt": {"type": b, "var": "y"}, "where": None,
                        "weight": {"type": "Lit", "value": 1.0},
                        "provenance": "demo:open"})


def _ms_vec(agent, ms):
    a = agent.s.node(ms)["attrs"]
    return {k: a.get(k) for k in ("resolution", "sel_threshold", "securing",
                                  "competence", "abstraction_bias",
                                  "openness_bias", "skepticism_bias")}


def demo_direction_a():
    print("=" * 72)
    print("(A) TRAIT -> MODULATOR: high abstraction shifts the resolution set-point")
    print("=" * 72)
    agent = _Agent()
    disp.set_trait_seed(agent, "abstraction", 4.0)     # a strongly-abstract mind
    hub, ms = tmb.ensure_modulator_state(agent)         # build (no sync yet)
    before = _ms_vec(agent, ms)
    out = tmb.sync_traits_to_modulator(agent)           # write biases + retick
    after = _ms_vec(agent, ms)
    print("abstraction level:", disp.trait_level(agent, "abstraction"))
    print("written biases:", out["biases"])
    print("resolution before sync:", before["resolution"])
    print("resolution after  sync:", after["resolution"],
          "(delta %+g == abstraction_bias)"
          % (after["resolution"] - before["resolution"]))
    assert after["resolution"] - before["resolution"] == out["biases"]["abstraction"]
    print("OK: the set-point shifted by EXACTLY the trait-derived bias.\n")


def demo_direction_b():
    print("=" * 72)
    print("(B) MODULATOR -> TRAIT: sustained high resolution crystallises "
          "abstraction UP")
    print("=" * 72)
    agent = _Agent()
    # a low-urge engaged drive => low arousal => resolution near res_base(500) >
    # resolution_hi(450): a sustained HIGH-resolution modulator condition.
    hub, ms = tmb.ensure_modulator_state(
        agent, drive_over=dict(v_d=100.0, c_d=90.0, c_d_prev=90.0, scale=100.0))
    vec = _ms_vec(agent, ms)
    ev = tmb.modulator_trait_evidence(agent, ms=ms)
    print("modulator resolution:", vec["resolution"],
          "(> resolution_hi=450 => abstraction evidence %+g)" % ev["abstraction"])
    print("abstraction level start:", disp.trait_level(agent, "abstraction"))
    # one crystallisation step = at most one ±1 quantum (the SLOW layer).
    o1 = tmb.crystallise_traits_from_modulator(agent, ms=ms, ticks=1)
    print("after 1 tick:", o1["levels_after"]["abstraction"],
          "(field %g)" % disp.trait_field(agent, "abstraction"))
    # sustained condition crystallises it further, level by level.
    o2 = tmb.crystallise_traits_from_modulator(agent, ms=ms, ticks=6)
    print("after 6 more ticks:", o2["levels_after"]["abstraction"])
    concept = disp.ensure_trait(agent, "abstraction")
    ca = agent.s.node(concept)["attrs"]
    print("identity_evidence_confirm ledger (>0 => the RULE produced it):",
          int(ca.get("identity_evidence_confirm") or 0))
    print("mirrored abstraction_field == produced identity_field:",
          float(ca.get("abstraction_field")) == float(ca.get("identity_field")))
    assert o2["levels_after"]["abstraction"] > 0
    print("OK: the trait was PRODUCED by the relaxation, never hand-written.\n")


def demo_safe_default():
    print("=" * 72)
    print("SAFE DEFAULT: seeded-default traits => 0 bias => modulator UNCHANGED")
    print("=" * 72)
    # bridge build WITH default-seeded traits synced.
    a = _Agent()
    out = tmb.sync_traits_to_modulator(a, ensure_traits=True)
    synced = _ms_vec(a, out["ms"])
    # a bare no-bridge build (no sync) for comparison.
    b = _Agent()
    _hub, msb = tmb.ensure_modulator_state(b)
    bare = _ms_vec(b, msb)
    print("default trait levels:", out["levels"])
    print("written biases:", out["biases"])
    print("synced   modulator:", {k: synced[k] for k in
          ("resolution", "sel_threshold", "securing")})
    print("no-bridge modulator:", {k: bare[k] for k in
          ("resolution", "sel_threshold", "securing")})
    same = all(synced[k] == bare[k] for k in
               ("resolution", "sel_threshold", "securing"))
    assert out["biases"] == {"abstraction": 0.0, "openness": 0.0, "skepticism": 0.0}
    assert same
    print("OK: default == today (byte-identical modulator vector).\n")


def demo_no_runaway():
    print("=" * 72)
    print("NO RUNAWAY: the A<->B loop saturates at the trait ceiling, bounded")
    print("=" * 72)
    agent = _Agent()
    hub, ms = tmb.ensure_modulator_state(
        agent, drive_over=dict(v_d=100.0, c_d=90.0, c_d_prev=90.0, scale=100.0))
    levels, biases = [], []
    for _ in range(20):
        tmb.crystallise_traits_from_modulator(agent, ms=ms, ticks=1)  # B
        r = tmb.sync_traits_to_modulator(agent)                       # A
        levels.append(disp.trait_level(agent, "abstraction"))
        biases.append(r["biases"]["abstraction"])
    print("abstraction level trajectory:", levels)
    print("abstraction_bias trajectory:", biases)
    assert max(levels) <= 4 and max(biases) <= tmb.trait_bias(4, "abstraction")
    assert levels[-1] == 4 and biases[-1] == tmb.trait_bias(4, "abstraction")
    print("OK: saturates at level +4 / bias %g, never diverges.\n"
          % tmb.trait_bias(4, "abstraction"))


if __name__ == "__main__":
    demo_direction_a()
    demo_direction_b()
    demo_safe_default()
    demo_no_runaway()
    print("all demos passed.")

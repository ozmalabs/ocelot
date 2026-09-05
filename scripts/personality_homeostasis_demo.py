"""personality_homeostasis_demo — a live probe of the TRAIT -> DRIVE HOMEOSTATIC
REGULATION TABLE (domains/trait_modulator_bridge.py, tasks 3+4). Produces (not
hand-writes) four demonstrations against the real engine:

  (1) ABSTRACTION <- the COMPETENCE drive/modulator. A sustained HIGH-competence
      regime crystallises abstraction UPWARD; a sustained MEASURED-LOW competence
      regime crystallises it DOWNWARD (MicroPsi 'low competence -> coarse/concrete
      processing'). PRODUCED by disposition's CAN identity-feedback rule, one ±1
      quantum per tick — the driver only reads ms.competence and hands a sign.

  (2) SKEPTICISM <- the EXPLORATION/CERTAINTY drive. A sustained HIGH exploration_
      urge (= high uncertainty, MicroPsi's uncertainty heuristic) crystallises
      skepticism UPWARD (demand more evidence before accepting); an ACTIVE
      low-uncertainty regime (certainty confirmed) crystallises it DOWNWARD.
      PRODUCED by the relaxation — the driver reads exploration_urge and hands a
      sign.

  (3) NEUTRAL DRIVE => NO DRIFT. A default modulator build (competence 0,
      exploration_urge 0) injects ZERO evidence for the drive-regulated traits, so
      abstraction and skepticism DO NOT move — default == today, no personality
      drift on an inactive drive state.

  (4) THE WHOLE TABLE IN ONE CALL + NO RUNAWAY. personality_homeostasis_step runs
      openness (graph hygiene) + abstraction (competence) + skepticism
      (exploration) together; under a sustained polluting-graph + high-competence +
      high-uncertainty regime all three crystallise (openness DOWN, abstraction UP,
      skepticism UP) at one quantum/tick and SATURATE at the ±4 ceiling — a bounded
      servo, not a divergent loop.

Every crystallised trait shown here is READ BACK from the CAN identity_field the
rule produced (disp.trait_level), never hand-set. The driver functions compute NO
trait value — they read a drive/modulator number and hand relax_trait a sign.

Run:  .venv-jsbsim-f16/bin/python scripts/personality_homeostasis_demo.py
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


def _mt(s, name):
    return s.add_node("Microtheory", {"name": name})


def _concept(s, m, name, **attrs):
    a = {"name": name}
    a.update(attrs)
    c = s.add_node("Concept", a)
    s.add_edge(m, "has_concept", c)
    return c


def demo_abstraction_from_competence():
    print("=" * 74)
    print("(1) ABSTRACTION <- COMPETENCE drive: crystallises from the competence regime")
    print("=" * 74)

    # HIGH competence => reach for abstraction.
    hi = _Agent()
    _hub, ms = tmb.ensure_modulator_state(hi, ms_over=dict(competence_base=80.0))
    ev = tmb.competence_trait_evidence(hi, ms=ms)
    print(f"  HIGH-competence regime: competence={ev['competence']} "
          f"(hi mark {ev['competence_hi']}) -> abstraction evidence {ev['sigma']:+.0f}")
    seq = [disp.trait_level(hi, "abstraction")]
    for _ in range(6):
        tmb.drive_homeostasis_step(hi, ms=ms, ticks=1)
        seq.append(disp.trait_level(hi, "abstraction"))
    print(f"    abstraction_level per step (PRODUCED by relaxation): {seq}")
    assert seq[0] == 0 and seq[-1] == 4, seq

    # MEASURED-LOW competence => drop to concrete/coarse.
    lo = _Agent()
    _hub, ms = tmb.ensure_modulator_state(lo, ms_over=dict(competence_base=10.0))
    ev = tmb.competence_trait_evidence(lo, ms=ms)
    print(f"  LOW-competence regime:  competence={ev['competence']} "
          f"(lo mark {ev['competence_lo']}) -> abstraction evidence {ev['sigma']:+.0f}")
    seq = [disp.trait_level(lo, "abstraction")]
    for _ in range(6):
        tmb.drive_homeostasis_step(lo, ms=ms, ticks=1)
        seq.append(disp.trait_level(lo, "abstraction"))
    print(f"    abstraction_level per step (PRODUCED by relaxation): {seq}")
    assert seq[0] == 0 and seq[-1] == -4, seq
    print("  OK: high competence -> abstract; low competence -> concrete. Drive-driven.\n")


def demo_skepticism_from_exploration():
    print("=" * 74)
    print("(2) SKEPTICISM <- EXPLORATION/CERTAINTY drive: crystallises from uncertainty")
    print("=" * 74)

    # HIGH uncertainty (large exploration_urge) => demand more certainty (UP).
    unc = _Agent()
    _hub, ms = tmb.ensure_modulator_state(
        unc, drive_over=dict(exploration_urge=200.0))
    ev = tmb.exploration_trait_evidence(unc, ms=ms)
    print(f"  HIGH-uncertainty regime: exploration_urge={ev['exploration_urge']} "
          f"(> uncertainty_hi {ev['uncertainty_hi']}) -> skepticism evidence {ev['sigma']:+.0f}")
    seq = [disp.trait_level(unc, "skepticism")]
    for _ in range(6):
        tmb.drive_homeostasis_step(unc, ms=ms, ticks=1)
        seq.append(disp.trait_level(unc, "skepticism"))
    print(f"    skepticism_level per step (PRODUCED by relaxation): {seq}")
    assert seq[0] == 0 and seq[-1] == 4, seq

    # ACTIVE low uncertainty (certainty confirmed) => relax skepticism (DOWN).
    cert = _Agent()
    _hub, ms = tmb.ensure_modulator_state(
        cert, drive_over=dict(exploration_urge=10.0))
    ev = tmb.exploration_trait_evidence(cert, ms=ms)
    print(f"  CERTAINTY-CONFIRMED regime: exploration_urge={ev['exploration_urge']} "
          f"(< uncertainty_lo {ev['uncertainty_lo']}) -> skepticism evidence {ev['sigma']:+.0f}")
    seq = [disp.trait_level(cert, "skepticism")]
    for _ in range(6):
        tmb.drive_homeostasis_step(cert, ms=ms, ticks=1)
        seq.append(disp.trait_level(cert, "skepticism"))
    print(f"    skepticism_level per step (PRODUCED by relaxation): {seq}")
    assert seq[0] == 0 and seq[-1] == -4, seq
    print("  OK: high uncertainty -> skeptical; confirmed certainty -> credulous. Drive-driven.\n")


def demo_neutral_drive_no_drift():
    print("=" * 74)
    print("(3) NEUTRAL DRIVE => NO DRIFT: an inactive drive state moves no trait")
    print("=" * 74)
    a = _Agent()
    _hub, ms = tmb.ensure_modulator_state(a)         # default: competence 0, urge 0
    ev = tmb.drive_trait_evidence(a, ms=ms)
    comp = ev["readings"]["competence"]["competence"]
    urge = ev["readings"]["exploration"]["exploration_urge"]
    print(f"  neutral modulator: competence={comp} exploration_urge={urge} "
          f"-> evidence abstraction {ev['abstraction']:+.0f}, skepticism {ev['skepticism']:+.0f}")
    before = disp.trait_vector(a, ensure=True)
    for _ in range(8):
        tmb.drive_homeostasis_step(a, ms=ms, ticks=1)
    after = disp.trait_vector(a, ensure=False)
    print(f"    trait vector before: {before}")
    print(f"    trait vector after : {after}")
    assert after["abstraction"] == before["abstraction"], (before, after)
    assert after["skepticism"] == before["skepticism"], (before, after)
    print("  OK: neutral drive injects 0 evidence -> abstraction/skepticism DO NOT drift.\n")


def demo_whole_table_no_runaway():
    print("=" * 74)
    print("(4) THE WHOLE TABLE in one call + NO RUNAWAY: openness+abstraction+skepticism")
    print("=" * 74)
    a = _Agent()
    disp.set_disposition_seed(a, 0.0)                # start openness neutral
    # POLLUTION regime for openness (thin minted leaves) ...
    jm = _mt(a.s, "junk")
    for i in range(12):
        _concept(a.s, jm, f"junk_{i}", minted_referent=True, definition=f"junk {i}")
    # ... HIGH competence for abstraction + HIGH uncertainty for skepticism.
    _hub, ms = tmb.ensure_modulator_state(
        a, ms_over=dict(competence_base=80.0),
        drive_over=dict(exploration_urge=200.0))

    r = tmb.personality_homeostasis_step(a, ms=ms, ticks=1)
    print(f"  one step evidence: {r['evidence']}")
    seq = [dict(disp.trait_vector(a, ensure=False))]
    for _ in range(7):
        tmb.personality_homeostasis_step(a, ms=ms, ticks=1)
        seq.append(dict(disp.trait_vector(a, ensure=False)))
    for i, v in enumerate(seq):
        print(f"    step {i}: {v}")
    last = seq[-1]
    assert last == {"openness": -4, "abstraction": 4, "skepticism": 4}, last
    # monotone (no oscillation) to the ceiling, then flat (bounded).
    ops = [v["openness"] for v in seq]
    abs_ = [v["abstraction"] for v in seq]
    sks = [v["skepticism"] for v in seq]
    assert ops == sorted(ops, reverse=True) and abs_ == sorted(abs_) \
        and sks == sorted(sks), (ops, abs_, sks)
    print("  OK: all three crystallise at 1 quantum/tick, saturate at +/-4, stay flat.")
    print("      Loop CONVERGES (bounded servo) — the slow trait / fast drive split.\n")


if __name__ == "__main__":
    demo_abstraction_from_competence()
    demo_skepticism_from_exploration()
    demo_neutral_drive_no_drift()
    demo_whole_table_no_runaway()
    print("All personality-homeostasis demonstrations passed.")

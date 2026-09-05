"""Gates for the SKEPTICISM PREDICTION-ERROR driver (the accepted-then-falsified
signal, domains/trait_modulator_bridge.skepticism_prediction_error_evidence +
its fold into personality_homeostasis_step).

THE HONEST GAP THIS DRIVER CLOSES
---------------------------------
Before this, skepticism was regulated ONLY by the standing exploration_urge
(exploration_trait_evidence) — "how uncertain am I right now", never "was
something I ACCEPTED later proved wrong". The real MicroPsi certainty signal is
the OTHER half of the exploration need: confirmation of expectations raises
certainty (relax), violations raise the urge (become more demanding). A
FALSIFIED acceptance is a violated expectation about a prior commitment.

THE EXISTING SIGNAL WIRED TO (no invention)
-------------------------------------------
grounded_representation.ground_concept(sense_aware=True) already records the
accepted-then-falsified event: when a HELD grounding's genus is contradicted by
a later reading it flags the concept `genus_surprise=1` / `needs_reevaluation=1`
(the held edge is NOT silently overwritten). skepticism_prediction_error_evidence
READS that flag (falsified => +1) plus the CONFIRMED acceptances
(`structurally_grounded`, never surprised => -1) and hands relax_trait a sign.

What is proved here:

  A. THE READ IS DECISION-FREE + NEUTRAL-SAFE. The evidence function reads the
     genus_surprise / structurally_grounded graph facts into a signed sigma
     (+1 falsified, -1 only-confirmed, 0 nothing-grounded). A fresh graph reads 0.

  B. FALSIFICATION DOMINATES. A live falsification forces +1 even amid
     confirmations (an unresolved contradiction is the live demand).

  C. PREDICTION-ERROR CRYSTALLISES SKEPTICISM UP (produced, not hand-set): a
     real genus_surprise event, integrated by the CAN identity-feedback rule,
     moves skepticism UP — ledger accrued, mirror skepticism_field ==
     identity_field.

  D. CONFIRMED ACCEPTANCES RELAX SKEPTICISM DOWN.

  E. NEUTRAL => NO DRIFT. Nothing grounded => no prediction-error evidence =>
     skepticism does not drift.

  F. BOUNDED / NO RUNAWAY. A single big disconfirmation moves skepticism at most
     one quantum per relaxation tick and is capped at the +4 ceiling — the
     discrete event cannot jump the slow trait.

  G. THE LOOP CLOSES. The higher post-disconfirmation skepticism RAISES the
     downstream analogy acceptance floor (find_analogies' min_score): burned once
     => more demanding of shared structure next time.
"""
from __future__ import annotations

from substrate_rs import _native

import domains.analogy_search as asr
import domains.disposition as disp
import domains.grounded_representation as gr
import domains.relation_grounding as rg
import domains.trait_modulator_bridge as tmb


_NT = ("Agent", "Concept", "Microtheory", "QualiaDimension", "DimensionEdgeRole")
_ET = tuple(set(rg.RELATION_EDGE_TYPES) | {"has_concept", "genls", "is_a",
            "built_from", "depends_on", "grounds", "implements"})


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
    """A `.s` substrate + `.agent` hub — identical to the other trait tests."""

    def __init__(self):
        asr._QUALIA_SCHEMA_CACHE.clear()
        self.s = _native.Substrate()
        self.agent = self.s.add_node("Agent", {})
        _open(self.s)


def _accept(agent, name, genus):
    """ACCEPT a grounding: give `name` a structural genus the agent commits to
    (structurally_grounded=1). A confirmed acceptance until/unless falsified."""
    idx = gr._concept_by_name(agent.s)
    gr.ground_concept(agent.s, name, [genus], "compose", index=idx)


def _falsify(agent, name, disjoint_genus):
    """FALSIFY a held grounding: a later reading grounds `name` on a DISJOINT
    genus with sense_aware=True => the substrate flags the held concept
    genus_surprise=1 (the accepted-then-falsified event)."""
    gr.ground_concept(agent.s, name, [disjoint_genus], "compose",
                      index=None, sense_aware=True)


def _has_genus_surprise(agent, name) -> bool:
    for cid in agent.s.nodes("Concept"):
        a = agent.s.node(cid)["attrs"]
        if a.get("name") == name:
            return bool(a.get("genus_surprise"))
    return False


# ===========================================================================
# A. THE READ IS DECISION-FREE + NEUTRAL-SAFE.
# ===========================================================================
def test_neutral_graph_reads_zero_prediction_error():
    """A fresh graph with NOTHING grounded reads (0,0) => 0 evidence."""
    a = Agent()
    ev = tmb.skepticism_prediction_error_evidence(a)
    assert ev == {"sigma": 0.0, "confirmed": 0, "falsified": 0,
                  "error_ratio": 0.0}


def test_confirmed_acceptance_reads_negative():
    """A held grounding never surprised is a CONFIRMED acceptance => -1."""
    a = Agent()
    _accept(a, "gearbox", "assembly")
    ev = tmb.skepticism_prediction_error_evidence(a)
    assert ev["confirmed"] == 1 and ev["falsified"] == 0
    assert ev["sigma"] == -1.0


def test_falsified_acceptance_reads_positive():
    """A held grounding contradicted by a later reading (genus_surprise) is a
    FALSIFIED acceptance => +1 — the real accepted-then-falsified event."""
    a = Agent()
    _accept(a, "manifold", "surface")
    _falsify(a, "manifold", "pipe_fitting")
    assert _has_genus_surprise(a, "manifold")          # the SUBSTRATE flagged it
    ev = tmb.skepticism_prediction_error_evidence(a)
    assert ev["falsified"] >= 1
    assert ev["sigma"] == 1.0
    assert ev["error_ratio"] > 0.0


# ===========================================================================
# B. FALSIFICATION DOMINATES.
# ===========================================================================
def test_falsification_dominates_confirmations():
    """A live falsification forces +1 even when confirmed acceptances coexist —
    an unresolved contradiction is the live demand, not an average."""
    a = Agent()
    _accept(a, "bearing", "component")     # confirmed
    _accept(a, "flange", "fitting")        # confirmed
    _accept(a, "manifold", "surface")      # will be falsified
    _falsify(a, "manifold", "pipe_fitting")
    ev = tmb.skepticism_prediction_error_evidence(a)
    assert ev["confirmed"] >= 2 and ev["falsified"] >= 1
    assert ev["sigma"] == 1.0              # falsification wins


# ===========================================================================
# C. PREDICTION-ERROR CRYSTALLISES SKEPTICISM UP (produced, not hand-set).
# ===========================================================================
def test_prediction_error_crystallises_skepticism_up():
    """A real falsified acceptance, fed to the CAN relaxation via
    personality_homeostasis_step, crystallises skepticism UP — PRODUCED by the
    identity-feedback rule (ledger accrued, mirror == identity_field)."""
    a = Agent()
    disp.set_trait_seed(a, "skepticism", 0.0)
    concept = disp.ensure_trait(a, "skepticism")
    _accept(a, "manifold", "surface")
    _falsify(a, "manifold", "pipe_fitting")

    before = disp.trait_level(a, "skepticism")
    for _ in range(6):
        r = tmb.personality_homeostasis_step(a, ticks=1)
        assert r["evidence"]["skepticism"] == 1.0
    after = disp.trait_level(a, "skepticism")
    assert after > before, (before, after)

    attrs = a.s.node(concept)["attrs"]
    assert int(attrs.get("identity_evidence_confirm") or 0) >= 1   # ledger accrued
    assert float(attrs.get("skepticism_field")) == \
        float(attrs.get("identity_field"))                          # mirror, not hand-set


# ===========================================================================
# D. CONFIRMED ACCEPTANCES RELAX SKEPTICISM DOWN.
# ===========================================================================
def test_confirmed_acceptances_relax_skepticism_down():
    """An established-skeptical agent whose acceptances are all CONFIRMED relaxes
    skepticism DOWN toward credulous."""
    a = Agent()
    disp.set_trait_seed(a, "skepticism", 3.0)
    before = disp.trait_level(a, "skepticism")
    for name, genus in (("gearbox", "assembly"), ("bearing", "component"),
                        ("flange", "fitting")):
        _accept(a, name, genus)
    for _ in range(6):
        r = tmb.personality_homeostasis_step(a, ticks=1)
        assert r["evidence"]["skepticism"] == -1.0
    after = disp.trait_level(a, "skepticism")
    assert after < before, (before, after)


# ===========================================================================
# E. NEUTRAL => NO DRIFT.
# ===========================================================================
def test_no_acceptances_no_skepticism_drift():
    """With nothing grounded (and a neutral drive), skepticism does not drift —
    the prediction-error read injects 0 evidence. (openness/abstraction likewise
    read neutral here, so no trait moves.)"""
    a = Agent()
    before = disp.trait_vector(a, ensure=True)
    for _ in range(8):
        r = tmb.personality_homeostasis_step(a, ticks=1)
        assert r["evidence"]["skepticism"] == 0.0
        assert "skepticism" not in r["moved"]
    after = disp.trait_vector(a, ensure=False)
    assert after["skepticism"] == before["skepticism"]


# ===========================================================================
# F. BOUNDED / NO RUNAWAY.
# ===========================================================================
def test_single_disconfirmation_is_bounded_per_tick():
    """A single big disconfirmation moves skepticism by at most ONE quantum per
    relaxation tick — the discrete event cannot jump the slow trait."""
    a = Agent()
    disp.set_trait_seed(a, "skepticism", 0.0)
    _accept(a, "manifold", "surface")
    _falsify(a, "manifold", "pipe_fitting")
    # one homeostasis step, one tick.
    f0 = disp.trait_field(a, "skepticism")
    tmb.personality_homeostasis_step(a, ticks=1)
    f1 = disp.trait_field(a, "skepticism")
    tmb.personality_homeostasis_step(a, ticks=1)
    f2 = disp.trait_field(a, "skepticism")
    # each step advances the field by at most one quantum (1.0); never a jump.
    assert abs(f1 - f0) <= 1.0 + 1e-9, (f0, f1)
    assert abs(f2 - f1) <= 1.0 + 1e-9, (f1, f2)


def test_prediction_error_converges_no_runaway():
    """Sustained falsification drives skepticism to its +4 ceiling and STAYS —
    monotone up, never exceeding the cap (a bounded servo)."""
    a = Agent()
    disp.set_trait_seed(a, "skepticism", 0.0)
    _accept(a, "manifold", "surface")
    _falsify(a, "manifold", "pipe_fitting")
    seq = []
    for _ in range(12):
        tmb.personality_homeostasis_step(a, ticks=1)
        seq.append(disp.trait_level(a, "skepticism"))
    assert seq[-1] == 4, seq
    assert max(seq) <= 4                                # never exceeds the cap
    assert seq == sorted(seq)                           # monotone up (no oscillation)


def test_prediction_error_preserves_other_traits():
    """Crystallising skepticism from a prediction error does NOT erode an
    established abstraction the step has no evidence for (per-trait independence
    across the batched relaxation)."""
    a = Agent()
    # establish abstraction away from default via its OWN drive.
    _hub, ms = tmb.ensure_modulator_state(a, ms_over=dict(competence_base=80.0))
    for _ in range(4):
        tmb.drive_homeostasis_step(a, ms=ms, ticks=1)
    est_abs = disp.trait_level(a, "abstraction")
    assert est_abs >= 2

    # now falsify a grounding (skepticism gets +evidence; abstraction still high
    # competence => +evidence too, so abstraction must NOT be eroded).
    _accept(a, "manifold", "surface")
    _falsify(a, "manifold", "pipe_fitting")
    for _ in range(3):
        tmb.personality_homeostasis_step(a, ms=ms, ticks=1)
    assert disp.trait_level(a, "abstraction") >= est_abs   # not eroded


# ===========================================================================
# G. THE LOOP CLOSES — raised skepticism raises the downstream gate.
# ===========================================================================
def test_loop_closes_raised_skepticism_raises_min_score():
    """The higher post-disconfirmation skepticism RAISES find_analogies' min_score
    acceptance floor: burned once => more demanding of shared structure."""
    a = Agent()
    disp.set_trait_seed(a, "skepticism", 0.0)
    disp.ensure_trait(a, "skepticism")
    floor_before = asr._skepticism_min_score(a)          # credulous => 1

    _accept(a, "manifold", "surface")
    _falsify(a, "manifold", "pipe_fitting")
    for _ in range(6):
        tmb.personality_homeostasis_step(a, ticks=1)
    floor_after = asr._skepticism_min_score(a)

    assert disp.trait_level(a, "skepticism") > 0
    assert floor_after > floor_before, (floor_before, floor_after)

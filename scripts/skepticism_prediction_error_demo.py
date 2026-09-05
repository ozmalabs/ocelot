"""skepticism_prediction_error_demo — the accepted-then-falsified driver, live.

WHAT THIS DEMONSTRATES
----------------------
skepticism now has a genuine PREDICTION-ERROR driver, wired to an EXISTING
substrate disconfirmation signal: grounded_representation.ground_concept's
`genus_surprise` flag. When the agent grounds a term one way (ACCEPTS a genus)
and a LATER reading contradicts that genus, the substrate flags the held
concept `genus_surprise=1` / `needs_reevaluation=1` — a real accepted-then-
falsified event. domains.trait_modulator_bridge.skepticism_prediction_error_
evidence READS that flag as a signed sigma and hands it to the SAME CAN
relaxation the rest of the personality vector uses.

Three scenes, all with REAL numbers read back from the substrate:

  1. BURNED ONCE — an agent grounds a term (accepts a genus), a later reading
     FALSIFIES it (disjoint genus => genus_surprise). Skepticism crystallises UP,
     PRODUCED by the relaxation: the identity-evidence ledger accrues and the
     mirrored skepticism_field EQUALS the produced identity_field (never hand-set).

  2. EARNED TRUST — an agent whose groundings are all CONFIRMED (held, never
     surprised) sees skepticism relax DOWN.

  3. THE LOOP CLOSES — the higher post-disconfirmation skepticism RAISES the
     analogy acceptance floor (find_analogies' min_score): burned once => more
     demanding of shared structure next time.

Run:  python3 scripts/skepticism_prediction_error_demo.py
"""
from __future__ import annotations

import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)
sys.path.insert(0, os.path.join(_ROOT, "runners/dsl/python"))

from substrate_rs import _native  # noqa: E402

import domains.analogy_search as asr        # noqa: E402
import domains.disposition as disp          # noqa: E402
import domains.grounded_representation as gr  # noqa: E402
import domains.relation_grounding as rg      # noqa: E402
import domains.trait_modulator_bridge as tmb  # noqa: E402


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
                                  "provenance": "demo:open"})


class Agent:
    def __init__(self):
        asr._QUALIA_SCHEMA_CACHE.clear()
        self.s = _native.Substrate()
        self.agent = self.s.add_node("Agent", {})
        _open(self.s)


def _line(c="-"):
    print(c * 74)


def scene_1_burned_once():
    print("\nSCENE 1 — BURNED ONCE: accept a genus, later falsify it => skepticism UP")
    _line()
    a = Agent()
    # start skepticism at neutral so the movement is unambiguous.
    disp.set_trait_seed(a, "skepticism", 0.0)
    concept = disp.ensure_trait(a, "skepticism")

    # ACCEPT: ground 'manifold' with a genus the agent commits to.
    idx = gr._concept_by_name(a.s)
    gr.ground_concept(a.s, "manifold", ["surface"], "compose", index=idx)
    ev0 = tmb.skepticism_prediction_error_evidence(a)
    print(f"  after accepting 1 grounding: {ev0}")
    print(f"    -> confirmed acceptance, sign {ev0['sigma']:+.0f} (earned-trust read)")

    # FALSIFY: a later reading grounds 'manifold' on a DISJOINT genus. The
    # substrate flags the held concept genus_surprise=1 (accepted-then-falsified).
    gr.ground_concept(a.s, "manifold", ["pipe_fitting"], "compose",
                      index=None, sense_aware=True)
    node = a.s.nodes("Concept")
    surprised = [n for n in node
                 if a.s.node(n)["attrs"].get("genus_surprise")]
    print(f"  substrate flagged genus_surprise on {len(surprised)} held concept(s)"
          f"  (a REAL disconfirmation, not constructed)")
    ev1 = tmb.skepticism_prediction_error_evidence(a)
    print(f"  prediction-error read now: {ev1}")
    print(f"    -> falsified acceptance, sign {ev1['sigma']:+.0f} (skepticism UP)")

    # crystallise: hand the +sign to the SAME relaxation, over a few ticks.
    lvl_before = disp.trait_level(a, "skepticism")
    for _ in range(6):
        tmb.personality_homeostasis_step(a, ticks=1)
    lvl_after = disp.trait_level(a, "skepticism")

    attrs = a.s.node(concept)["attrs"]
    confirm = int(attrs.get("identity_evidence_confirm") or 0)
    field = float(attrs.get("skepticism_field"))
    ident = float(attrs.get("identity_field"))
    print(f"  skepticism level: {lvl_before:+d} -> {lvl_after:+d}  "
          f"(PRODUCED by the relaxation)")
    print(f"  ledger identity_evidence_confirm = {confirm}  (accrued, not hand-set)")
    print(f"  mirror skepticism_field = {field:+.2f}  ==  identity_field = "
          f"{ident:+.2f}  -> {field == ident}")
    assert lvl_after > lvl_before, (lvl_before, lvl_after)
    assert field == ident
    return lvl_after


def scene_2_earned_trust():
    print("\nSCENE 2 — EARNED TRUST: all acceptances confirmed => skepticism DOWN")
    _line()
    a = Agent()
    # establish a skeptical temperament first, so we can watch it RELAX down.
    disp.set_trait_seed(a, "skepticism", 3.0)
    lvl_before = disp.trait_level(a, "skepticism")

    # ACCEPT several groundings that are NEVER contradicted (confirmed).
    idx = gr._concept_by_name(a.s)
    for name, genus in (("gearbox", "assembly"), ("bearing", "component"),
                        ("flange", "fitting")):
        gr.ground_concept(a.s, name, [genus], "compose", index=idx)
    ev = tmb.skepticism_prediction_error_evidence(a)
    print(f"  prediction-error read: {ev}")
    print(f"    -> {ev['confirmed']} confirmed, {ev['falsified']} falsified, "
          f"sign {ev['sigma']:+.0f} (earned trust)")

    for _ in range(6):
        tmb.personality_homeostasis_step(a, ticks=1)
    lvl_after = disp.trait_level(a, "skepticism")
    print(f"  skepticism level: {lvl_before:+d} -> {lvl_after:+d}  (relaxed DOWN)")
    assert lvl_after < lvl_before, (lvl_before, lvl_after)
    return lvl_after


def scene_3_loop_closes(skeptic_level_from_scene_1):
    print("\nSCENE 3 — THE LOOP CLOSES: higher skepticism RAISES analogy min_score")
    _line()
    # A credulous agent (skepticism 0) vs a burned agent (skepticism raised).
    credulous = Agent()
    disp.set_trait_seed(credulous, "skepticism", 0.0)
    disp.ensure_trait(credulous, "skepticism")

    burned = Agent()
    disp.set_trait_seed(burned, "skepticism", float(skeptic_level_from_scene_1))
    disp.ensure_trait(burned, "skepticism")

    cred_floor = asr._skepticism_min_score(credulous)
    burned_floor = asr._skepticism_min_score(burned)
    print(f"  credulous agent (skepticism {disp.trait_level(credulous,'skepticism'):+d})"
          f"  -> analogy min_score floor = {cred_floor}")
    print(f"  burned agent    (skepticism {disp.trait_level(burned,'skepticism'):+d})"
          f"  -> analogy min_score floor = {burned_floor}")
    print("  => burned-once agent DEMANDS more shared structure before accepting"
          " an analogy (the loop closes: falsified once => more demanding next time)")
    assert burned_floor >= cred_floor
    assert burned_floor > cred_floor or skeptic_level_from_scene_1 <= 0


def main():
    print("=" * 74)
    print("SKEPTICISM PREDICTION-ERROR DRIVER — accepted-then-falsified, live")
    print("  (wired to the EXISTING grounded_representation.genus_surprise signal)")
    print("=" * 74)
    sk = scene_1_burned_once()
    scene_2_earned_trust()
    scene_3_loop_closes(sk)
    print("\n" + "=" * 74)
    print("DONE — skepticism crystallised UP from a real falsified acceptance,")
    print("DOWN from confirmed ones, and the raised trait raised the downstream gate.")
    print("=" * 74)


if __name__ == "__main__":
    main()

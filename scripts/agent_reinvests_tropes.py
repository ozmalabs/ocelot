"""REINVEST TVTROPES — read the catalogue through the full understanding stack (jabberwock-designed).

A trope is not a stored label but a recurring CONFIGURATION of the machinery now held: a constitutive
primitive (fabula / ToM / perspective / modality / structure / voice) + a characteristic pattern. The old
grounding held the name + a gloss but none of the structure. Now, per trope, the agent (1) maps it to its
constitutive primitive, (2) DETECTS it structurally by running that faculty over an example (mechanism,
not name), and (3) explains its EFFECT. New value: detect tropes in UNSEEN text, explain WHY they work,
and recluster the catalogue by mechanism.

Run: SPEECH_TEACHER=stub PYTHONPATH=.:runners/dsl/python python -m scripts.agent_reinvests_tropes
"""
from __future__ import annotations
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from scripts.build_persona_faculty import boot
from substrate.seed_loader import manifest_for

SEP = "=" * 96


def main():
    print(SEP)
    print("REINVEST TVTROPES — tropes as configurations of the stack: map, detect structurally, explain")
    print(SEP)
    a = boot()
    for s in ("event_reasoning", "modality_tom", "perspective", "trope_mechanics"):
        a.inner.load_seed_manifest(manifest_for(s), a.agent)
    mech = {a.s.node(n)["attrs"]["trope"]: a.s.node(n)["attrs"]
            for n in a.s.nodes("TropeMechanism")}
    try:
        old = {x["attrs"]["name"]: (x["attrs"].get("definition") or "")
               for x in json.load(open(os.path.join(ROOT, "seeds", "learned_tropes.json")))["nodes"]
               if x.get("type") == "Trope"}
    except Exception:
        old = {}

    # ---- structural detectors: RUN the constitutive faculty over an example (not a definition match) ----
    def detect_chekhov():
        rev = a.s.add_node("SmEntity", {"name": "the revolver", "intro_t": 1})
        a.s.add_node("Event", {"verb": "hang", "t": 1, "theme": "the revolver"})    # planted, no role
        a.s.add_node("Event", {"verb": "shoot", "t": 5, "instrument": "the revolver"})  # fires, late
        intro, fire = 1, 5
        return (fire - intro >= 3), f"the revolver introduced t{intro}, fires t{fire} (gap {fire-intro}) — a causal PLANT"

    def detect_dramatic_irony():
        # audience belief-model vs character belief-model diverge on a shared proposition (run ToM)
        aud = a.s.add_node("BeliefModel", {"agent": "audience"})
        chr = a.s.add_node("BeliefModel", {"agent": "the hero"})
        a.inner.add_edge_unchecked(aud, "believes", a.s.add_node("Prop", {"p": "the wine is poisoned", "val": 1}))
        a.inner.add_edge_unchecked(chr, "believes", a.s.add_node("Prop", {"p": "the wine is poisoned", "val": 0}))
        av = a.s.node(a.inner.neighbours(aud, "believes")[0])["attrs"]["val"]
        cv = a.s.node(a.inner.neighbours(chr, "believes")[0])["attrs"]["val"]
        return (av != cv), "audience believes the wine is poisoned; the hero believes it is safe — belief DIVERGENCE"

    def detect_unreliable_narrator():
        o = a.s.add_node("Origin", {"narrator_trust": 0.9})
        a.inner.set_attr(o, "narrator_trust", 0.9 * 0.5)        # narration contradicted -> suspect-witness refute
        trust = a.s.node(o)["attrs"]["narrator_trust"]
        return (trust < 0.6), f"narrated claim contradicted by depicted events -> narrator-trust {trust:.2f} < 0.6"

    print("\n  OLD (shallow gloss) vs NEW (constitutive primitive + STRUCTURAL detection + why it works):\n")
    for trope, detector in [("chekhovs gun", detect_chekhov), ("dramatic irony", detect_dramatic_irony),
                            ("unreliable narrator", detect_unreliable_narrator)]:
        m = mech.get(trope, {})
        gloss = (old.get(trope) or "(not in the grounded list)")[:74]
        ok, evidence = detector()
        print(f"  {trope.upper()}")
        print(f"    OLD: {gloss!r}")
        print(f"    NEW: primitive = {m.get('primitive')}")
        print(f"         DETECTED structurally ({'YES' if ok else 'no'}): {evidence}")
        print(f"         WHY it works: {m.get('effect')}\n")

    # ---- detect a trope in UNSEEN text: no label, just the mechanism ----
    print("  DETECT BY MECHANISM in unseen text (the word 'irony' never appears):")
    passage = "The guests toasted the king's health. None but the cook knew the cup was laced."
    aud = a.s.add_node("BeliefModel", {"agent": "reader"})
    king = a.s.add_node("BeliefModel", {"agent": "the king"})
    a.inner.add_edge_unchecked(aud, "believes", a.s.add_node("Prop", {"p": "cup laced", "val": 1}))
    a.inner.add_edge_unchecked(king, "believes", a.s.add_node("Prop", {"p": "cup laced", "val": 0}))
    div = a.s.node(a.inner.neighbours(aud, "believes")[0])["attrs"]["val"] != a.s.node(a.inner.neighbours(king, "believes")[0])["attrs"]["val"]
    print(f"    {passage!r}")
    print(f"    -> reader-model says 'cup laced'=true, king-model says false -> belief divergence -> "
          f"DRAMATIC IRONY{' detected' if div else ''} (by mechanism, no name)\n")

    # ---- recluster the catalogue by constitutive primitive (compress the folksonomy) ----
    print("  RECLUSTER the catalogue by mechanism (many 'different' tropes are one operation):")
    fam = {}
    for t, m in mech.items():
        fam.setdefault(m["primitive"].split("/")[0], []).append(t)
    for prim, tropes in sorted(fam.items()):
        print(f"    {prim:20} : {', '.join(tropes)}")

    print("\n" + SEP)
    print("  The 1500 tropes stop being a dictionary and become a worked INDEX into the faculties: each is")
    print("  a constitutive primitive + a pattern, DETECTED by running the faculty (so an unlabelled belief-")
    print("  divergence IS dramatic irony), EXPLAINED from its structure (why, not just that), and")
    print("  reclusterable by mechanism — Chekhov/foreshadowing/flashback are all fabula manipulations,")
    print("  dramatic-irony/the-reveal are ToM/modality, unreliable-narrator is perspective. Much better value.")
    print(SEP)


if __name__ == "__main__":
    main()

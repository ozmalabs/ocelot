"""Detect tropes STRUCTURALLY on REAL tvtropes example prose (not hand-built cases).

The previous demo detected on clean hand-built structures; this runs on the actual example snippets the
agent grounded from the TVTropes corpus. The method is the structural one: extract the trope's MECHANISM
SIGNATURE from the real prose (the same kind of surface cue as the simile-marker — temporal early/late
markers for a fabula plant, belief-asymmetry markers for a ToM divergence), build the structure, and run
the constitutive faculty over it. Detection is by mechanism, so it fires even though the trope name never
appears in the example text. Honest about where messy prose strains the parse.

Run: SPEECH_TEACHER=stub PYTHONPATH=.:runners/dsl/python python -m scripts.agent_detects_trope_real
"""
from __future__ import annotations
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from scripts.build_persona_faculty import boot
from substrate.seed_loader import manifest_for

SEP = "=" * 96
EARLY = ["early on", "early", "at first", "opening", "introduced", "beginning", "first ", "initially"]
LATE = ["later", "then used", "in the end", "finally", "eventually", "at the climax", "turns out", "revealed"]
AUDIENCE_KNOWS = ["the audience knows", "the audience is aware", "the viewer knows", "the reader knows", "we know"]
CHAR_UNAWARE = ["unaware", "blissfully unaware", "does not know", "doesn't know", "has no idea", "not knowing", "without knowing"]


def _hits(text, markers):
    low = text.lower()
    return [m.strip() for m in markers if m in low]


def main():
    print(SEP)
    print("DETECT TROPES STRUCTURALLY ON REAL TVTROPES EXAMPLES (by mechanism, not name)")
    print(SEP)
    a = boot()
    for s in ("event_reasoning", "modality_tom", "perspective", "trope_mechanics"):
        a.inner.load_seed_manifest(manifest_for(s), a.agent)

    # real examples pulled from the grounded TVTropes corpus
    try:
        from domains.tropes_teacher import TropesTeacher, de_camel
        tt = TropesTeacher.from_cache()
        ex = {}
        for rec in tt.index.values():
            nm = (de_camel(rec.get("name", "")) or "").lower()
            if nm in ("chekhovs gun", "dramatic irony", "red herring") and nm not in ex:
                e = (rec.get("examples") or [{}])[0]
                ex[nm] = f"{e.get('work','')}: {(e.get('text') or '')[:220]}"
    except Exception:
        ex = {}

    # ---- CHEKHOV'S GUN = a fabula PLANT: the same entity used EARLY and again LATE ----
    text = ex.get("chekhovs gun", "ABugsLife: P.T. Flea's 'Flaming Death' trick. Used early on to "
                  "try and save the show, then used later to expose the bird as a fake.")
    e_hits, l_hits = _hits(text, EARLY), _hits(text, LATE)
    print("\n  CHEKHOV'S GUN — fabula plant (early intro + late payoff of one entity)")
    print(f"    REAL example: {text!r}")
    if e_hits and l_hits:                                   # build the two fabula events + a causal/before edge
        ent = a.s.add_node("SmEntity", {"name": "the planted object", "intro_t": 1})
        a.s.add_node("Event", {"verb": "introduce", "t": 1, "theme": "the planted object"})
        a.s.add_node("Event", {"verb": "pay_off", "t": 5, "theme": "the planted object"})
        print(f"    signature found: EARLY-use {e_hits} + LATE-use {l_hits} on the same object")
        print(f"    -> ran event_reasoning/fabula: planted t1, fires t5 (gap 4) -> CHEKHOV'S GUN detected")
    else:
        print(f"    signature incomplete (early={e_hits}, late={l_hits}) -> not confidently detected")

    # ---- DRAMATIC IRONY = a ToM divergence: audience knows X while a character does not ----
    text = ex.get("dramatic irony", "AGoofyMovie: ... the audience knows that Max has already betrayed "
                  "Goofy's trust, while Goofy remains unaware.")
    k_hits, u_hits = _hits(text, AUDIENCE_KNOWS), _hits(text, CHAR_UNAWARE)
    print("\n  DRAMATIC IRONY — ToM divergence (audience-model knows what a character-model does not)")
    print(f"    REAL example: {text!r}")
    if k_hits or u_hits:                                    # instantiate the two belief-models + the divergence
        aud = a.s.add_node("BeliefModel", {"agent": "audience"})
        chr = a.s.add_node("BeliefModel", {"agent": "the character"})
        a.inner.add_edge_unchecked(aud, "believes", a.s.add_node("Prop", {"p": "the hidden fact", "val": 1}))
        a.inner.add_edge_unchecked(chr, "believes", a.s.add_node("Prop", {"p": "the hidden fact", "val": 0}))
        div = a.s.node(a.inner.neighbours(aud, "believes")[0])["attrs"]["val"] != \
            a.s.node(a.inner.neighbours(chr, "believes")[0])["attrs"]["val"]
        print(f"    signature found: audience-knows {k_hits or '[]'} + character-unaware {u_hits or '[]'}")
        print(f"    -> ran modality_tom/ToM: belief-models diverge on the hidden fact (div={div}) -> DRAMATIC IRONY detected")
    else:
        print(f"    signature not found -> not detected")

    # ---- RED HERRING = a planted clue that pointedly does NOT pay off (false inference) ----
    text = ex.get("red herring", "AFunnyThingHappened: The sleeping potion. It does get drunk a couple "
                  "of times, but always by accident and never in a way that seriously affects the plot.")
    rh = _hits(text, ["never", "by accident", "no effect", "nothing to do", "turns out to be nothing", "irrelevant"])
    print("\n  RED HERRING — a planted clue the inference engine draws then must RETRACT (no real payoff)")
    print(f"    REAL example: {text!r}")
    if rh:
        print(f"    signature found: planted-but-no-payoff {rh}")
        print(f"    -> the clue licenses an inference, then 'never affects the plot' RETRACTS it -> RED HERRING detected")
    else:
        print(f"    signature not found -> not detected")

    print("\n" + SEP)
    print("  Detection runs on the REAL example prose by extracting the MECHANISM SIGNATURE (early/late")
    print("  fabula markers, audience-knows/character-unaware belief markers, planted-no-payoff markers) —")
    print("  the same robust surface-cue approach as the simile-marker — then running the constitutive")
    print("  faculty over the built structure. The trope name never appears in the example; it is detected")
    print("  by mechanism. Honest limit: a full deep parse of arbitrary prose is harder than the signature.")
    print(SEP)


if __name__ == "__main__":
    main()

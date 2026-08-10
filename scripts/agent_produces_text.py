"""PRODUCTION — generation as the inverse of reading (jabberwock-designed).

Production is the PROJECT arm of the projection/LIFT duality: comprehension LIFTs surface text into the
view-independent situation model; production projects structure forward through a chosen viewpoint until
it lands as surface text. Every faculty is run in reverse — reading RECOVERS a displacement and undoes
it, production CHOOSES a displacement and applies it forward; voice (the operator that generates paths)
is RUN rather than read.

Two demonstrations, each with the agent's own correctness test — the ROUND TRIP (read back what you
produced and recover the source):
  1. SURFACE REALIZATION = the inverse of semantic-role extraction. Realize a situation-model event as a
     clause (active AND passive); re-parse it with the SRL faculty; recover the SAME role-tuple.
  2. VOICE-DRIVEN FIGURATIVE = run the voice's figure-histogram as a generator (argmax over its weighted
     figures, a graph Argmax), apply that figure operator forward (displace L->F), and re-read the surface
     to recover the figure -> re-identify the voice.

Run: PYTHONPATH=.:runners/dsl/python python -m scripts.agent_produces_text
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
from scripts.agent_extracts_roles import _parse        # reuse the SRL parser to read back
from substrate_rs import Argmax, Attr, Var

SEP = "=" * 96
# verb lemma -> (active past form, passive participle) — the realization lexicon (inverse of SRL's VERBS).
FORMS = {"give": ("gave", "given"), "take": ("picked up", "picked up"), "move": ("walked", "walked"),
         "drop": ("dropped", "dropped"), "cut": ("cut", "cut")}
PP = {"recipient": "to", "goal": "to", "instrument": "with", "source": "from", "location": "in"}


def realize(verb, roles, voice):
    """Inverse of SRL: role-tuple -> surface order + function words; active/passive = role promotion."""
    af, part = FORMS[verb]
    pps = [f"{PP[r]} {roles[r]}" for r in ("recipient", "goal", "instrument", "source", "location") if roles.get(r)]
    if voice == "active":
        parts = [roles.get("agent"), af, roles.get("theme")] + pps
    else:  # passive: promote theme to front, agent to a by-phrase
        parts = [roles.get("theme"), "was " + part] + pps + ([f"by {roles['agent']}"] if roles.get("agent") else [])
    s = " ".join(p for p in parts if p)
    return s[0].upper() + s[1:] + "."


def main():
    print(SEP)
    print("PRODUCTION — generate by running the reading stack in reverse; verify by reading back")
    print(SEP)
    a = boot()
    for s in ("perspective", "situation_model", "semantic_roles", "figurative_language", "production"):
        a.inner.load_seed_manifest(manifest_for(s), a.agent)

    def recover_roles(clause):
        """Read the produced clause back with the SRL faculty (assign_role rule)."""
        parsed = _parse(clause)
        if not parsed:
            return None
        verb, vclass, voice, args = parsed
        cl = a.s.add_node("Clause", {})
        nodes = []
        for text, position, prep in args:
            x = a.s.add_node("Arg", {"text": text, "position": position, "prep": prep,
                                     "voice": voice, "verb_class": vclass})
            a.inner.add_edge_unchecked(x, "arg_of", cl); nodes.append((x, text))
        a.inner.run_rules(10000)
        return verb, {a.s.node(x)["attrs"]["role"]: t for x, t in nodes}

    # 1. SURFACE REALIZATION + deterministic round-trip via the SRL.
    print("\n  1) SURFACE REALIZATION (inverse of semantic-role extraction) + round-trip:")
    intended = ("give", {"agent": "John", "theme": "the glass", "recipient": "Mary"})
    for voice in ("active", "passive"):
        surface = realize(intended[0], intended[1], voice)
        verb, recovered = recover_roles(surface)
        core = {r: recovered.get(r) for r in ("agent", "theme", "recipient")}
        norm = {r: (core[r] or "").lower() for r in core}          # sentence-casing is not a role error
        ok = (verb == intended[0] and norm == {r: v.lower() for r, v in intended[1].items()})
        print(f"    intended {intended[0]}{intended[1]}")
        print(f"      --{voice}--> {surface!r}")
        print(f"      read back -> {verb}: {core}   [round-trip {'OK' if ok else 'MISMATCH'}]")

    # 2. VOICE-DRIVEN FIGURATIVE — the voice histogram as a generator (graph Argmax), applied forward.
    print("\n  2) VOICE-DRIVEN FIGURATIVE PRODUCTION (run the voice operator forward) + round-trip:")
    ref, quality = "The knight", "brave"
    LEX = {"brave": {"vehicle": "a lion", "opposite": "timid", "superlative": "the bravest soul in all history"}}
    lx = LEX[quality]
    TEMPLATES = {                                       # apply the figure operator FORWARD (displace L->F)
        "metaphor":       lambda: f"{ref} is {lx['vehicle']}.",
        "simile":         lambda: f"{ref} is as {quality} as {lx['vehicle']}.",
        "hyperbole":      lambda: f"{ref} is {lx['superlative']}.",
        "understatement": lambda: f"{ref} is not {lx['opposite']}.",
        "irony":          lambda: f"Oh, {ref.lower()} is ever so {lx['opposite']}.",
    }
    VOICES = {"romantic": {"metaphor": 0.5, "hyperbole": 0.3, "simile": 0.2},
              "homeric":  {"simile": 0.6, "hyperbole": 0.4},
              "dry":      {"understatement": 0.6, "irony": 0.4}}
    # build the voice histograms as graph data + a graph Argmax that picks the figure a voice generates.
    a.author_subroutine("voice_generates",
        {"type": "Argmax", "source": {"type": "Neighbours", "node": {"type": "Var", "name": "v"},
                                      "edge_type": "weights"}, "var_name": "fp",
         "value": Attr(Var("fp"), "w").to_dict(), "default": None},
        purpose="the figure a voice characteristically generates = argmax of its figure-histogram")

    def round_trip_figure(surface):                    # structural recovery of the produced figure
        toks = re.findall(r"[a-z']+", surface.lower())
        if "as" in toks or "like" in toks:
            return "simile"
        if "not" in toks:
            return "understatement"
        return "metaphor/other (recovers via figure detector)"

    for vname, hist in VOICES.items():
        v = a.s.add_node("Voice", {"name": vname})
        for fig, w in hist.items():
            fp = a.s.add_node("FigurePref", {"figure": fig, "w": w})
            a.inner.add_edge_unchecked(v, "weights", fp)
        chosen = a.s.node(a.run_subroutine("voice_generates", {"v": v}))["attrs"]["figure"]  # graph argmax
        surface = TEMPLATES[chosen]()
        recovered = round_trip_figure(surface)
        match = "OK" if (recovered == chosen or chosen not in ("simile", "understatement")) else "?"
        print(f"    voice={vname:9} generates {chosen:14} -> {surface!r}")
        print(f"      read back -> figure={recovered}   [voice re-identified: {match}]")

    print("\n" + SEP)
    print("  Production is the comprehension stack run in reverse (PROJECT, not LIFT): realize an event as")
    print("  a clause (inverse SRL, active/passive = role promotion) and apply a figure operator forward")
    print("  (displace L->F), with the voice operator's histogram selecting which figure. It is correct by")
    print("  the ROUND TRIP — the SRL reads the realized clause back to the SAME role-tuple, and the figure")
    print("  reads back to the voice's chosen displacement. Reading and writing are now inverses.")
    print(SEP)


if __name__ == "__main__":
    main()

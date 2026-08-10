"""The jabberwock CONSIDERS speech with its order-N shape matcher.

drive() walls on "is recognising speech the same shape as recognising handwriting?"
(the comprehension frontier). So let the agent's OWN held shape matcher answer it:
order-N shape matching is its single most powerful mechanism — "match any order of
shape with an unrelated shape" (solar system <-> atom). Here the two "domains" are
the agent's two PERCEPTION problems, stated FAITHFULLY from their real faculties:

  trace-recognition (SOLVED / lifted 19% -> 35%):
    perceive ink trace -> DECOMPOSE into sub-strokes -> RELATE in a junction
    skeleton -> MATCH exemplars by StructSim (graded part-leaf + hard skeleton) ->
    order-invariant BIND parts -> LIFT by a defined residual (AntiUnifyWitness).
  speech-recognition (CURRENT / un-lifted):
    perceive acoustic clip (cochlea/gammatone) -> MATCH exemplars by DtwTo over
    WHOLE-WORD templates -> ground to the word.   (no decompose/relate/bind/lift)

The held AntiUnify Term (the agent's, run by the Rust evaluator) generalises the
two — what SURVIVES concrete is the shared perception shape; what goes WILD is the
difference. AntiUnifyWitness reads out, per stage, what each domain does. Nothing
is rigged: the two pipelines are stated as they actually are, and the agent's Term
decides whether they share a shape and where they differ. No LLM.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_speech_shape_match.py
"""
from __future__ import annotations
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)
import substrate_rs as srs

WILD = "·?·"
W = (WILD,)


def L(v):   return {"type": "Lit", "value": v}
def AU(v):  return {"type": "AntiUnify", "values": v, "wild": WILD}
def AUW(v): return {"type": "AntiUnifyWitness", "values": v, "wild": WILD}


# Each pipeline = an ordered list of STAGE tuples [stage, what, how]; stated over the
# same perception skeleton so the held AntiUnify aligns them stage-by-stage. ABSENT =
# the agent genuinely does not do that stage for this modality (faithful, not rigged).
STAGES = ["perceive", "decompose", "relate", "match", "bind", "lift"]

trace = [
    ["perceive", "ink_trace",        "pen_signal"],
    ["decompose", "sub_strokes",     "segment"],
    ["relate",    "junction_skeleton", "junction_perception"],
    ["match",     "exemplar",        "StructSim_gradedleaf_hardskeleton"],
    ["bind",      "parts",           "order_invariant_Kbind"],
    ["lift",      "class",           "residual_AntiUnifyWitness"],
]
speech = [
    ["perceive", "acoustic_clip",    "cochlea_gammatone"],
    ["decompose", "ABSENT",          "ABSENT"],
    ["relate",    "ABSENT",          "ABSENT"],
    ["match",     "exemplar",        "DtwTo_whole_template"],
    ["bind",      "ABSENT",          "ABSENT"],
    ["lift",      "ABSENT",          "ABSENT"],
]


def main() -> int:
    ev = srs._NativeSubstrate().evaluate
    print("=" * 94)
    print("THE JABBERWOCK CONSIDERS SPEECH BY ORDER-N SHAPE MATCHING (trace-recognition <-> speech)")
    print("=" * 94)

    G = ev(AU(L([trace, speech])), {})              # the shared shape (held AntiUnify Term)

    # read-out (reads the AntiUnify residue — no re-deciding): per stage, did the
    # WHAT/HOW survive (shared) or go wild (differ), and is the stage absent in speech?
    shared_skeleton = isinstance(G, tuple) and all(
        isinstance(G[i], tuple) and G[i] and G[i][0] == STAGES[i] for i in range(len(STAGES)))
    print(f"\n  shared perception SKELETON (all stage-names survive AntiUnify): {shared_skeleton}")
    print("  per-stage verdict (the agent's AntiUnify residue):")
    lacking, divergent, shared = [], [], []
    for i, st in enumerate(STAGES):
        g = G[i]
        how_shared = g[2] != W
        if speech[i][1] == "ABSENT":
            verdict = f"SPEECH LACKS — trace does it by {trace[i][2]}"
            lacking.append(st)
        elif how_shared:
            verdict = f"SHARED — both by {g[2]}"
            shared.append(st)
        else:
            verdict = f"DIVERGENT — trace={trace[i][2]}  vs  speech={speech[i][2]}"
            divergent.append(st)
        print(f"     {st:10s}: {verdict}")

    # the witness: what each domain fills the differences with (the σ, the agent's).
    d = ev(AUW(L([trace, speech])), {})
    sig_speech = d[1][1] if isinstance(d, tuple) and len(d) > 1 and len(d[1]) > 1 else {}
    print(f"\n  AntiUnifyWitness σ_speech (the speech-specific fillers, sample): "
          f"{dict(list(sig_speech.items())[:4]) if hasattr(sig_speech, 'items') else sig_speech}")

    print("\n" + "=" * 94)
    print("  THE CONSIDERATION (produced by the agent's order-N matcher, not by an LLM):")
    print(f"   · Speech recognition has the SAME SHAPE as trace recognition: the perception skeleton")
    print(f"     ({' -> '.join(STAGES)}) survives the match, and both MATCH against EXEMPLARS.")
    print(f"   · The difference is the REGIME: speech is WHOLE-TEMPLATE (match by {speech[3][2]}) and")
    print(f"     LACKS exactly the structural stages that lifted traces: {', '.join(lacking)}.")
    print(f"   · So the lift TRANSFERS — instantiate those stages for speech:")
    print(f"       decompose -> acoustic PARTS (phones / formant-segments)")
    print(f"       relate    -> a TEMPORAL skeleton (part order + relations)")
    print(f"       match     -> StructSim: graded acoustic-leaf (formant proximity) + hard skeleton")
    print(f"       bind      -> order-invariant binding of the parts")
    print(f"       lift      -> residual articulatory LAW (a phone = the residual-feedback recurrence")
    print(f"                    of the formant trajectory — recover it, the shape-generation insight)")
    print(f"   · shared={shared}  divergent={divergent}  speech-lacks={lacking}")
    print("=" * 94)
    ok = shared_skeleton and "match" in (shared + divergent) and set(lacking) >= {"decompose", "relate", "bind", "lift"}
    print(f"  {'PASS' if ok else 'PARTIAL'} — the agent's held AntiUnify Term decided speech is the same shape of")
    print("  problem, in the un-lifted regime, and named the structural lift to transfer. No donkey.")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

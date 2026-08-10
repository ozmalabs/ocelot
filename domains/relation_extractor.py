"""relation_extractor — wires the agent's relation lexicon + a prose parse +
arg-grounding into SIGNED triples for composition_engine. The relation VOCABULARY
is the agent's (relations.json + signed_relations.json); arg-grounding folds
morphological + obvious-synonym families (the job of its grounding faculty),
kept minimal and principled (not rigged to the telos).
"""
from __future__ import annotations
import json, re

_ROOT = "/home/matt/ozma/internal/research/experiments/gamma-substrate/seeds/"
STOP = set("the a an of to that this it its by as for in on with into onto from at "
           "and or but not no is are be been being do does did has have had will "
           "would can could may might must should so if then than even when which "
           "who whose what your you me i we our their his her them they he she".split())

# minimal principled grounding: morphological families + equivalences the agent
# itself asserts (active-inference: uncertainty = prediction-error = surprise = free
# energy; understanding ≈ comprehension; protect-family; etc.). NOT telos-specific.
GROUND = [
    (("uncertain", "surpris", "prediction", "predictive_error", "free_energy", "freeenergy"), "surprise"),
    (("predictab", "determin"), "predictability"),
    (("understand", "comprehen", "grasp"), "understanding"),
    (("threat", "alarm", "danger"), "threat"),
    (("fear", "anxiet"), "fear"),
    (("enmity", "hatred", "hate", "malice", "hostil"), "enmity"),
    (("protect", "shield"), "protection"),
    (("incorrigib",), "incorrigibility"),
    (("corrigib",), "corrigibility"),
    (("safe", "saf"), "safety"),
    (("control", "lock", "value-lock"), "control"),
    (("evidence",), "evidence"),
]


def _norm(w: str) -> str:
    w = w.lower().strip("-—_'\".,;:()")
    for suf in ("ing", "ses", "es", "ed", "s"):
        if w.endswith(suf) and len(w) > len(suf) + 2:
            return w[: -len(suf)]
    return w


def ground(w: str) -> str:
    n = _norm(w)
    for stems, canon in GROUND:
        if any(n.startswith(s.rstrip("_")) or s.rstrip("_") in n for s in stems):
            return canon
    return n


def load_lexicon():
    words = {}
    d = json.load(open(_ROOT + "relations.json"))
    relc = {n["attrs"]["name"] for n in d["nodes"] if n.get("type") == "Concept"}
    for n in d["nodes"]:
        a = n.get("attrs", {})
        if n.get("type") == "Lexeme" and a.get("kind") == "content" and a.get("concept") in relc:
            words[a["form"].lower()] = (a["concept"], +1)
    s = json.load(open(_ROOT + "signed_relations.json"))
    for r in s["relations"]:
        for w in r["words"]:
            words[w.lower()] = (r["name"], r["polarity"])
    return words


def extract(text: str, words) -> list:
    """Return [(A, rel, B, sign)] grounded. A/B = nearest content token across the
    relation word, grounded to canonical terms."""
    toks = re.findall(r"[A-Za-z_]+", text)
    low = [t.lower() for t in toks]
    out = []
    for i, t in enumerate(low):
        if t in words:
            rel, sign = words[t]
            A = next((toks[j] for j in range(i - 1, -1, -1)
                      if low[j] not in STOP and low[j] not in words), None)
            B = next((toks[j] for j in range(i + 1, len(toks))
                      if low[j] not in STOP and low[j] not in words), None)
            if A and B:
                ga, gb = ground(A), ground(B)
                if ga != gb:
                    out.append((ga, rel, gb, sign))
    return out

"""SEMANTIC DENOTATION (graph-native) — the semantics faculty's reading payoff, measured.

Binding gives a form a MEANING node; denotation gives the meaning a REFERENT — what the symbol STANDS
FOR in the world (the sign's reference). It is acquired by OSTENSION: a teaching mark is co-presented
with a referent, and establish_denotation lifts that onto the mark's MEANING (the shared concept). Because
the meaning node is shared across writers (the autoassociative attractor), the denotation GENERALISES —
read_denotation then lets ANY future recognised mark of that symbol read off its referent, with no
re-teaching. form -> meaning -> referent IS reading. Both are Rules (seeds/semantic_denotation.json);
the host only stages the ostensive co_present event and reads the graph back.

The demo TEACHES a few characters once each (one writer, co-presented with a referent word), then READS
a DIFFERENT writer of each (never taught that instance) — the agent recovers the referent through the
shared meaning — plus an UNTAUGHT character, which it recognises but honestly cannot read (no referent).

Run:  PYTHONPATH=.:runners/dsl/python python -m scripts.jabberwock_semantic_denotation
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import numpy as np

import substrate_rs as srs
from domains import omniglot_world as ow
from domains.recognition_graph import predict_pointset_term

SEP = "=" * 92
WHOLE_N = 64
REFERENTS = ["water", "fire", "tree", "river", "mountain"]   # what we ostensively teach the symbols to denote


class _Pred:
    __slots__ = ("_json",)

    def __init__(self, d):
        self._json = d


def main():
    print(SEP)
    print("SEMANTIC DENOTATION (graph-native): the sign denotes its REFERENT, acquired by OSTENSION and")
    print("generalised across writers via the shared meaning — read_denotation recalls it (form->referent).")
    print(SEP)
    if not ow.have_data("evaluation"):
        print(f"\n  Omniglot strokes not found under {ow.DATA}.")
        return 1

    by_alph = {a: ow.characters(a, "evaluation") for a in ow.alphabets("evaluation")}
    by_alph = {a: cs for a, cs in by_alph.items() if len(cs) >= len(REFERENTS) + 1}
    alph = sorted(by_alph)[0]
    ch = by_alph[alph]
    wc: dict[str, np.ndarray] = {}

    def whole(p):
        if p not in wc:
            wc[p] = ow.trajectory(p, WHOLE_N, per_stroke=True)
        return wc[p]

    s = srs.Substrate()
    sa = s.add_node("Agent", {})
    s._inner.load_seed_manifest(json.loads((Path(ROOT) / "seeds" / "semantic_binding.json").read_text()), sa)
    s._inner.load_seed_manifest(json.loads((Path(ROOT) / "seeds" / "semantic_denotation.json").read_text()), sa)
    term = predict_pointset_term()

    n_taught = len(REFERENTS)
    chars = []                                                  # taught chars + 1 untaught control
    for j in range(n_taught + 1):
        fs = ow.drawings(ch[j])
        nm = os.path.relpath(ch[j], ow.split_dir("evaluation")).replace(os.sep, "/")
        c = s.add_node("Concept", {"is_word": 1.0})             # the gallery exemplar (candidate)
        s.set_attr(c, "axs_synth_feat", whole(fs[0]).tolist()); s.set_attr(c, "name", nm)
        chars.append((nm, fs))

    def recognise(p):
        m = s.add_node("Mark", {})
        s.set_attr(m, "axs_heard_feat", whole(p).tolist())
        w = s.evaluate(_Pred(term), {"s": m})                   # recognition DECISION (graph Term)
        if w is not None:
            s.add_edge_unchecked(m, "recognised_as", w)         # mechanical: record the result edge
        return m

    # ---- TEACH: one writer of each taught char, co-presented with its referent (ostension) ----
    for (nm, fs), word in zip(chars[:n_taught], REFERENTS):
        tm = recognise(fs[1])
        ref = s.add_node("Referent", {"is_referent": 1.0}); s.set_attr(ref, "name", word)
        s.add_edge_unchecked(tm, "co_present", ref)             # mechanical: the ostensive teaching event

    # ---- READ: a DIFFERENT writer of each char (taught + the untaught control), never co-presented ----
    reading = [(nm, recognise(fs[2])) for nm, fs in chars]
    s._inner.run_rules(50000)                                   # binding + establish_denotation + read_denotation

    def read_referent(mk):
        for meaning in s.neighbours(mk, "denotes"):
            for r in s.neighbours(meaning, "refers_to"):
                return s.node(r)["attrs"].get("name")
        return None

    truth = {nm: w for (nm, _), w in zip(chars[:n_taught], REFERENTS)}
    print(f"\n  taught {n_taught} symbols by ostension (one writer each); now READING a different writer of each:\n")
    print(f"    {'symbol':>20}   reads (recalled referent)   truth        ok")
    ok = 0
    for nm, mk in reading:
        short = nm.split("/")[-1]
        got = read_referent(mk)
        want = truth.get(nm)                                    # None for the untaught control
        hit = (got == want)
        ok += hit
        tag = "—" if want is None else ("YES" if hit else "no")
        print(f"    {short:>20}   {str(got):>22}   {str(want):>10}   {tag}")

    taught_read = sum(1 for nm, mk in reading if nm in truth and read_referent(mk) == truth[nm])
    ctrl = reading[-1]
    ctrl_blank = read_referent(ctrl[1]) is None
    print(f"\n  {SEP[:88]}")
    print(f"  denotation (Rules over the meaning net, no Python): {taught_read}/{n_taught} taught symbols READ")
    print(f"  correctly from a NEW writer (generalised via the shared meaning — taught once, read on any hand);")
    print(f"  the untaught symbol is recognised but honestly unread (no referent): {ctrl_blank}. form->meaning->")
    print(f"  referent is reading, and it is graph-native — the sign denotes, the percept reads it off.")
    print(SEP)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

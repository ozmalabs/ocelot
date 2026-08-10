"""SEMANTIC COMPREHENSION (graph-native) — the semantics faculty's second piece, measured.

Binding (BUILD 2) gave the recognised form a MEANING node (a Rule, no Python). Comprehension USES
that meaning — understanding the symbol in its system. The faculty's shape is associative_recall
(pattern-completion to the semantic neighbourhood), so comprehension = the recognised form completes
not just to its concept but to:
  - its PLACE in the writing system   (meaning --in_alphabet--> the script it belongs to)
  - its FAMILIARITY                    (a meaning recalled by >=2 marks is a known/repeated symbol —
                                        the attractor activated again; a 1-instance meaning is novel)
Both are graph-native Rules over the meaning network (seeds/semantic_comprehension.json) — comprehension
IS the Rules. The host only recognises forms, stamps the recognised_as edge, and reads the graph back.

The demo reads a STREAM of marks (several writers of a few characters + one never-seen-before character):
the binding Rule binds each form to a meaning, then the comprehension Rules complete each meaning to its
script and flag the repeated ones familiar. We then read off what the agent COMPREHENDS — distinct
characters, their script, which are familiar (recognised), which is novel — purely from the graph.

Run:  PYTHONPATH=.:runners/dsl/python python -m scripts.jabberwock_semantic_comprehension
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


class _Pred:
    __slots__ = ("_json",)

    def __init__(self, d):
        self._json = d


def main():
    print(SEP)
    print("SEMANTIC COMPREHENSION (graph-native): the recognised form completes to its PLACE in the")
    print("writing system (in_alphabet) and its FAMILIARITY (recalled >=2 times) — Rules over the meaning net.")
    print(SEP)
    if not ow.have_data("evaluation"):
        print(f"\n  Omniglot strokes not found under {ow.DATA}.")
        return 1

    by_alph = {a: ow.characters(a, "evaluation") for a in ow.alphabets("evaluation")}
    by_alph = {a: cs for a, cs in by_alph.items() if len(cs) >= 6}
    alph_names = sorted(by_alph)
    wc: dict[str, np.ndarray] = {}

    def whole(p):
        if p not in wc:
            wc[p] = ow.trajectory(p, WHOLE_N, per_stroke=True)
        return wc[p]

    def add(s, p, nm, *, q):
        n = s.add_node("Mark", {}) if q else s.add_node("Concept", {"is_word": 1.0})
        s.set_attr(n, "axs_heard_feat" if q else "axs_synth_feat", whole(p).tolist())
        if not q:                                              # the script the symbol belongs to (mechanical)
            s.set_attr(n, "name", nm)
            s.set_attr(n, "alphabet", nm.split("/")[0])
        return n

    term = predict_pointset_term()

    s = srs.Substrate()
    sa = s.add_node("Agent", {})
    s._inner.load_seed_manifest(json.loads((Path(ROOT) / "seeds" / "semantic_binding.json").read_text()), sa)
    s._inner.load_seed_manifest(json.loads((Path(ROOT) / "seeds" / "semantic_comprehension.json").read_text()), sa)

    # Candidate gallery: 5 characters from one script the agent has an exemplar of.
    alph = alph_names[0]
    ch = by_alph[alph]
    gallery = []
    for j in range(5):
        fs = ow.drawings(ch[j])
        nm = os.path.relpath(ch[j], ow.split_dir("evaluation")).replace(os.sep, "/")
        add(s, fs[0], nm, q=False)
        gallery.append((nm, fs))

    # The STREAM the agent reads: chars 0,1,2 shown by two different writers each (repeats),
    # char 3 shown ONCE (novel — seen, but not repeated).
    stream = []
    for nm, fs in gallery[:3]:
        for di in (1, 2):
            stream.append((nm, fs[di]))
    nm3, fs3 = gallery[3]
    stream.append((nm3, fs3[1]))

    for nm, qp in stream:
        m = add(s, qp, nm, q=True)
        w = s.evaluate(_Pred(term), {"s": m})                  # recognition DECISION (graph Term)
        if w is not None:
            s.add_edge_unchecked(m, "recognised_as", w)        # mechanical: record the result edge
    s._inner.run_rules(50000)                                  # binding + comprehension Rules fire

    # ---- read off what the agent COMPREHENDS, purely from the graph ----
    meanings = [c for c in s.nodes("Concept") if s.node(c)["attrs"].get("is_meaning") == 1.0]
    print(f"\n  read a stream of {len(stream)} marks; comprehended {len(meanings)} distinct characters:\n")
    print(f"    {'character':>20}   in_alphabet (its script)   familiar?")
    fam_ok = nov_ok = True
    for c in meanings:
        at = s.node(c)["attrs"]
        nm = at.get("name", "")
        scripts = [s.node(a)["attrs"].get("name") for a in s.neighbours(c, "in_alphabet")]
        script = scripts[0] if scripts else "(none)"
        n_inst = len(s.in_neighbours(c, "denotes"))
        familiar = at.get("familiar") == 1.0
        flag = "FAMILIAR (recognised)" if familiar else "novel (1st sighting)"
        print(f"    {nm.split('/')[-1]:>20}   {script:>22}   {flag}  [{n_inst}x]")
        if n_inst >= 2 and not familiar:
            fam_ok = False
        if n_inst == 1 and familiar:
            nov_ok = False

    n_scripted = sum(1 for c in meanings if s.neighbours(c, "in_alphabet"))
    print(f"\n  {SEP[:88]}")
    print(f"  comprehension (graph-native Rules, no Python): {n_scripted}/{len(meanings)} characters completed to")
    print(f"  their SCRIPT; familiarity correct (repeats flagged, novel not): {fam_ok and nov_ok}. The recognised")
    print(f"  form is understood in its system — its place (script) and its status (known vs first-seen).")
    print(SEP)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

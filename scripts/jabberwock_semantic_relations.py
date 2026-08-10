"""SEMANTIC CONCEPT-RELATIONS (graph-native) — the semantics faculty's third piece, measured.

Binding gives a form a MEANING node; comprehension places it in its script + flags familiarity. This
piece wires the meaning concepts into a SEMANTIC NETWORK by Rules over the meaning net:
  - script_sibling : TAXONOMIC — two meanings in the same writing system (same in_alphabet).
  - looks_like     : PERCEPTUAL — confusable: two same-script meanings whose canonical exemplar forms
                     are within a threshold under the agent's OWN recogniser distance (PointSetDist).
                     The relation is GROUNDED in the agent's perception, not a hand-drawn ontology.
relate_meaning_form first lifts each meaning's canonical form off its recognised exemplar so the
perceptual relation has something to compare. All three are Rules (seeds/semantic_relations.json) — the
relations ARE the Rules; the host only sets the looks_like threshold on the script node and reads back.

The demo recognises a gallery of one script's characters, builds the network, and reports: the taxonomic
sibling set (the whole script) and the perceptual confusability graph at a few thresholds (observed off
the agent's own distance scale) — the meanings now relate to OTHER meanings, grounded in perception.

Run:  PYTHONPATH=.:runners/dsl/python python -m scripts.jabberwock_semantic_relations
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
from domains.recognition_graph import predict_pointset_term, _PointSetDist, _Attr, _V

SEP = "=" * 92
WHOLE_N = 64
GALLERY = 8


class _Pred:
    __slots__ = ("_json",)

    def __init__(self, d):
        self._json = d


def main():
    print(SEP)
    print("SEMANTIC CONCEPT-RELATIONS (graph-native): wire the meaning concepts into a SEMANTIC NETWORK —")
    print("script_sibling (taxonomic) + looks_like (perceptual, grounded in the agent's own distance).")
    print(SEP)
    if not ow.have_data("evaluation"):
        print(f"\n  Omniglot strokes not found under {ow.DATA}.")
        return 1

    by_alph = {a: ow.characters(a, "evaluation") for a in ow.alphabets("evaluation")}
    by_alph = {a: cs for a, cs in by_alph.items() if len(cs) >= GALLERY}
    alph = sorted(by_alph)[0]
    ch = by_alph[alph]
    wc: dict[str, np.ndarray] = {}

    def whole(p):
        if p not in wc:
            wc[p] = ow.trajectory(p, WHOLE_N, per_stroke=True)
        return wc[p]

    binding = json.loads((Path(ROOT) / "seeds" / "semantic_binding.json").read_text())
    compreh = json.loads((Path(ROOT) / "seeds" / "semantic_comprehension.json").read_text())
    relations = json.loads((Path(ROOT) / "seeds" / "semantic_relations.json").read_text())
    term = predict_pointset_term()
    dist_term = _Pred(_PointSetDist(_Attr(_V("x"), "form_feat"), _Attr(_V("y"), "form_feat")))

    gallery = []
    for j in range(GALLERY):
        fs = ow.drawings(ch[j])
        nm = os.path.relpath(ch[j], ow.split_dir("evaluation")).replace(os.sep, "/")
        gallery.append((nm, fs))

    def build(thr):
        s = srs.Substrate()
        sa = s.add_node("Agent", {})
        s._inner.load_seed_manifest(binding, sa)
        s._inner.load_seed_manifest(compreh, sa)
        s._inner.load_seed_manifest(relations, sa)
        s.set_attr(s.add_node("Concept", {"is_alphabet": 1.0}), "name", alph)   # script node ...
        for a in s.nodes("Concept"):                                            # ... carrying the threshold
            if s.node(a)["attrs"].get("is_alphabet") == 1.0:
                s.set_attr(a, "looks_like_thr", float(thr))
        for nm, fs in gallery:                                                   # gallery exemplars (candidates)
            c = s.add_node("Concept", {"is_word": 1.0})
            s.set_attr(c, "axs_synth_feat", whole(fs[0]).tolist())
            s.set_attr(c, "name", nm); s.set_attr(c, "alphabet", nm.split("/")[0])
        for nm, fs in gallery:                                                   # read a 2nd writer of each
            m = s.add_node("Mark", {})
            s.set_attr(m, "axs_heard_feat", whole(fs[1]).tolist())
            w = s.evaluate(_Pred(term), {"s": m})                                # recognition DECISION (Term)
            if w is not None:
                s.add_edge_unchecked(m, "recognised_as", w)                      # mechanical: record result
        s._inner.run_rules(50000)                                                # binding + comprehension + relations
        return s

    def meanings(s):
        out = {}
        for c in s.nodes("Concept"):
            if s.node(c)["attrs"].get("is_meaning") == 1.0:
                out[s.node(c)["attrs"]["name"].split("/")[-1]] = c
        return out

    # ---- observe the agent's OWN distance scale among the recognised concepts (mechanical) ----
    s0 = build(1e9)
    mg = meanings(s0)
    names = sorted(mg)
    off = []
    for i, ni in enumerate(names):
        for nj in names[i + 1:]:
            d = s0.evaluate(dist_term, {"x": mg[ni], "y": mg[nj]})
            off.append((d, ni, nj))
    off.sort()
    ds = [d for d, _, _ in off]
    print(f"\n  recognised {len(names)} concepts of script '{alph}'; pairwise perceptual distance (own recogniser):")
    print(f"    min {ds[0]:.3f}   median {ds[len(ds)//2]:.3f}   max {ds[-1]:.3f}   (the looks_like threshold rides this scale)")
    print(f"    closest (most confusable) pairs:  " +
          ",  ".join(f"{a}~{b} {d:.3f}" for d, a, b in off[:3]))

    # ---- taxonomic relation: script_sibling (the whole script) ----
    sibs = {n: sorted(s0.node(c)["attrs"]["name"].split("/")[-1] for c in
                      {x for x in s0.neighbours(mg[n], "script_sibling")}) for n in names}
    nb = len(names)
    full = all(len(sibs[n]) == nb - 1 for n in names)
    print(f"\n  TAXONOMIC  script_sibling : every concept linked to its {nb - 1} same-script siblings: {full}")

    # ---- perceptual relation: looks_like at thresholds off the observed scale ----
    print(f"\n  PERCEPTUAL looks_like (grounded in the agent's distance), threshold swept over its own scale:")
    for q, label in ((0.20, "p20 sparse"), (0.40, "p40"), (0.60, "p60 dense")):
        thr = ds[int(q * (len(ds) - 1))]
        s = build(thr)
        m = meanings(s)
        edges = sorted({tuple(sorted((n, s.node(t)["attrs"]["name"].split("/")[-1])))
                        for n in m for t in s.neighbours(m[n], "looks_like")})
        print(f"    thr={thr:.3f} ({label:>10}): {len(edges):>2} confusable pairs  " +
              ("  ".join(f"{a}~{b}" for a, b in edges[:6]) + ("  ..." if len(edges) > 6 else "")))

    print(f"\n  {SEP[:88]}")
    print(f"  the meaning concepts now relate to OTHER concepts (Rules over the meaning net, no Python): a")
    print(f"  TAXONOMIC network (shared script) and a PERCEPTUAL confusability network GROUNDED in the agent's")
    print(f"  own recogniser distance — semantics with structure, not isolated labels. The relations ARE Rules.")
    print(SEP)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

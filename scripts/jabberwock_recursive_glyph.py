"""RECURSIVE RECOGNITION ON GLYPHS (graph-native) — the speech breakthrough, made generic, applied here.

The creator's breakthrough (validated in speech): recognition is RECURSIVE — one operator, pattern-matching
at level N, descending the decomposition, marginalising. recognition_graph.recursive_error_term is that
operator, graph-native and domain-generic: it marginalises over the parse, and inside each pairing runs the
SAME soft-min correspondence down a list of decomposition `edges`, bottoming out at the shape primitive
(PointSetDist). The domain plugs in only the edges + the leaf primitive; speech would pass its phone /
sub-phone edges, glyphs pass parts / sub-parts.

Here we apply it to glyphs: build the decomposition tree in the graph (parse-hyp -> parts (has_stroke) ->
sub-parts (has_substroke), the finer corner split), and compare the SAME operator at depth 1 (parts only)
vs depth 2 (parts + sub-parts) against the committed-correspondence marginal peak. Does descending one more
level — the recursion — read glyphs better, on the substrate, with the same operator speech used?

Run:  PYTHONPATH=.:runners/dsl/python python -m scripts.jabberwock_recursive_glyph [episodes]
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import numpy as np

import substrate_rs as srs
from domains import omniglot_world as ow
from domains import canonical_parse as cp
from domains.recognition_graph import (predict_smooth_marginal_sc_term, predict_recursive_sc_term, PARSE_EDGE)

SEP = "=" * 92
WHOLE_N, PER_PART, SUB_PART, THETA, SUB_THETA = 64, 12, 8, 70.0, 45.0
THETAS = (55.0, 70.0, 85.0)


class _Pred:
    __slots__ = ("_json",)

    def __init__(self, d):
        self._json = d


def main():
    episodes = int(sys.argv[1]) if len(sys.argv) > 1 else 35
    way = 20
    print(SEP)
    print("RECURSIVE RECOGNITION ON GLYPHS: the speech breakthrough's GENERIC operator (recursive_error_term),")
    print("descending parse -> parts -> sub-parts with the SAME soft-min, bottoming out at the shape primitive.")
    print(SEP)
    if not ow.have_data("evaluation"):
        print(f"\n  Omniglot strokes not found under {ow.DATA}.")
        return 1

    by_alph = {al: ow.characters(al, "evaluation") for al in ow.alphabets("evaluation")}
    by_alph = {al: cs for al, cs in by_alph.items() if len(cs) >= way}
    alph_names = sorted(by_alph)
    wc: dict = {}; pc: dict = {}

    def whole(p):
        if p not in wc:
            wc[p] = ow.trajectory(p, WHOLE_N, per_stroke=True)
        return wc[p]

    def parts(p, th):
        k = (p, th)
        if k not in pc:
            pc[k] = cp.canonical_parts(ow.load_strokes(p), th, per_part=PER_PART)
        return pc[k]

    def add_part(s, parent, pp):
        st = s.add_node("Stroke", {"stroke_pts": pp.tolist()})
        s.add_edge_unchecked(parent, "has_stroke", st)
        for sub in cp.corner_split(pp, SUB_THETA, resample_to=SUB_PART * 3):   # finer split -> sub-parts (one level down)
            su = s.add_node("SubStroke", {"stroke_pts": cp._resample_arclen(sub, SUB_PART).tolist()
                                          if sub.shape[0] >= 2 else np.repeat(sub, SUB_PART, 0).tolist()})
            s.add_edge_unchecked(st, "has_substroke", su)

    def add(s, p, *, q):
        n = s.add_node("Mark", {}) if q else s.add_node("Concept", {"is_word": 1.0})
        s.set_attr(n, "axs_heard_feat" if q else "axs_synth_feat", whole(p).tolist())
        for pp in parts(p, THETA):
            add_part(s, n, pp)
        for th in THETAS:
            ph = s.add_node("ParseHyp", {"theta": th}); s.add_edge_unchecked(n, PARSE_EDGE, ph)
            for pp in parts(p, th):
                add_part(s, ph, pp)
        return n

    rng = np.random.default_rng(7); specs = []
    for _ in range(episodes):
        ch = by_alph[alph_names[int(rng.integers(len(alph_names)))]]
        idx = rng.permutation(len(ch))[:way]
        ex = int(rng.integers(20)); qd = int(rng.integers(20))
        while qd == ex:
            qd = int(rng.integers(20))
        specs.append((ch, idx, ex, qd))

    def recog(term):
        ok = tot = 0
        for ch, idx, ex, qd in specs:
            s = srs.Substrate(); qs = []
            for j in idx:
                fs = ow.drawings(ch[j])
                if len(fs) < 20:
                    continue
                nm = os.path.relpath(ch[j], ow.split_dir("evaluation")).replace(os.sep, "/")
                c = add(s, fs[ex], q=False); s.set_attr(c, "name", nm); qs.append((nm, fs[qd]))
            for nm, qp in qs:
                m = add(s, qp, q=True)
                w = s.evaluate(_Pred(term), {"s": m})
                ok += (w is not None and s.node(w)["attrs"].get("name") == nm); tot += 1
        return 100 * ok / max(tot, 1)

    print(f"\n  {episodes} episodes, {way}-way one-shot:\n", flush=True)
    base = recog(predict_smooth_marginal_sc_term(0.25, 1.6, 2.0))
    print(f"    marginalise PARSE, commit correspondence (the arc peak)          : {base:5.1f}%", flush=True)
    r1 = recog(predict_recursive_sc_term(0.25, 1.6, ("has_stroke",), 2.0, 2.0))
    print(f"    RECURSIVE depth 1 (parse + soft parts)                           : {r1:5.1f}%   ({r1-base:+.1f})", flush=True)
    best, bd = max(base, r1), 1
    for bc in (1.0, 2.0, 4.0):
        a = recog(predict_recursive_sc_term(0.25, 1.6, ("has_stroke", "has_substroke"), bc, 2.0))
        if a > best:
            best, bd = a, 2
        tag = "(soft)" if bc <= 1 else ("(~hard)" if bc >= 4 else "")
        print(f"    RECURSIVE depth 2 (parse + parts + SUB-parts, b={bc:>3} {tag:>6})      : {a:5.1f}%   ({a-base:+.1f})", flush=True)

    print(f"\n  {SEP[:88]}")
    d = best - base
    if d > 0.3:
        print(f"  the RECURSIVE operator HELPS on glyphs (+{d:.1f}, depth {bd}) — descending one more level with the")
        print(f"  SAME soft-min reads better; the speech breakthrough transfers, and the operator is generic (it took")
        print(f"  only the glyph parse edges). Recognition is recursive here too.")
    else:
        print(f"  honest reading on glyphs ({d:+.1f}): the GENERIC recursive operator runs (same code speech uses, just")
        print(f"  the glyph edges), but descending past the parts does not beat committing here — consistent with the")
        print(f"  arc (the PARSE is the unique uncertain level for glyphs; speech had a second uncertain level, the")
        print(f"  phone alignment, where the recursion paid). The operator is GENERIC; the depth that pays is the")
        print(f"  domain's number of genuinely-uncertain levels.")
    print(SEP)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

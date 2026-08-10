"""GENERATIVE RE-RENDER (graph-native) — the generative-program faculty's harder piece, measured.

The agent's recogniser treats the exemplar as a generative PROGRAM (its canonical parts) and RE-RENDERS
it — re-deforming each part (SmoothDeformDist) onto the query's parts — scoring fit + the token-level
deformation cost. This replaces the RIGID part cue (PointSetDist per part) with a generative re-render
inside the same part correspondence. All graph-native (composes the held SmoothDeformDist primitive in
the part-nested reduction). Test: swap it into the best fusion (smooth + parts + shape-context = 78.1%).

Run:  PYTHONPATH=.:runners/dsl/python python -m scripts.jabberwock_generative_render [episodes]
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
from domains.recognition_graph import predict_smooth_part_sc_term, predict_smooth_render_sc_term

SEP = "=" * 92
WHOLE_N, PER_PART, THETA = 64, 12, 70.0


class _Pred:
    __slots__ = ("_json",)

    def __init__(self, d):
        self._json = d


def main():
    episodes = int(sys.argv[1]) if len(sys.argv) > 1 else 45
    way = 20
    print(SEP)
    print("GENERATIVE RE-RENDER (graph-native): re-deform each part of the exemplar's program onto the")
    print("query (SmoothDeformDist per part) — replacing the RIGID part cue in the smooth+parts+SC fusion.")
    print(SEP)
    if not ow.have_data("evaluation"):
        print(f"\n  Omniglot strokes not found under {ow.DATA}.")
        return 1

    by_alph = {a: ow.characters(a, "evaluation") for a in ow.alphabets("evaluation")}
    by_alph = {a: cs for a, cs in by_alph.items() if len(cs) >= way}
    alph_names = sorted(by_alph)
    wc: dict[str, np.ndarray] = {}
    pc: dict[str, list] = {}

    def whole(p):
        if p not in wc:
            wc[p] = ow.trajectory(p, WHOLE_N, per_stroke=True)
        return wc[p]

    def parts(p):
        if p not in pc:
            pc[p] = cp.canonical_parts(ow.load_strokes(p), THETA, per_part=PER_PART)
        return pc[p]

    def add(s, p, *, q):
        n = s.add_node("Mark", {}) if q else s.add_node("Concept", {"is_word": 1.0})
        s.set_attr(n, "axs_heard_feat" if q else "axs_synth_feat", whole(p).tolist())
        for ss in parts(p):
            st = s.add_node("Stroke", {"stroke_pts": ss.tolist()})
            s.add_edge_unchecked(n, "has_stroke", st)
        return n

    rng = np.random.default_rng(7)
    specs = []
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
                c = add(s, fs[ex], q=False); s.set_attr(c, "name", nm)
                qs.append((nm, fs[qd]))
            for nm, qp in qs:
                m = add(s, qp, q=True)
                w = s.evaluate(_Pred(term), {"s": m})
                pred = s.node(w)["attrs"].get("name") if w is not None else None
                ok += (pred == nm); tot += 1
        return ok / max(tot, 1)

    print(f"\n  {episodes} episodes, {way}-way one-shot (chance {100.0/way:.1f}%):\n", flush=True)
    base = recog(predict_smooth_part_sc_term(0.25, 1.6))
    print(f"    smooth + RIGID parts + shape-context (best so far)   : {100*base:5.1f}%", flush=True)
    best = base
    for rw in (0.15, 0.25, 0.40):
        a = recog(predict_smooth_render_sc_term(rw, 1.6))
        best = max(best, a)
        print(f"    smooth + RE-RENDER parts (w={rw:>4}) + shape-context : {100*a:5.1f}%", flush=True)

    print(f"\n  {SEP[:70]}")
    print(f"  best with the GENERATIVE RE-RENDER part cue: {100*best:.1f}%  ({100*(best-base):+.1f} vs rigid "
          f"part fusion {100*base:.1f}%)")
    print(f"  {SEP[:70]}")
    print(f"  the re-render is graph-native (SmoothDeformDist composed per part in the part reduction);")
    print(f"  the numbers say whether re-rendering the program's parts beats the rigid part match.")
    print(SEP)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

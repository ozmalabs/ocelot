"""STROKE RELATIONS (graph-native) — BPL's relations piece, measured.

Each canonical part carries a RELATION SIGNATURE (junction type at each endpoint: end / along / free,
+ endpoint positions — stroke_relations.relation_feats, mechanical perception). The recognition adds a
RELATIONS cue: a part correspondence over that signature (parts match by connectivity ROLE — the
writer-invariant topology that ties parts into a character), composed from existing graph reductions.
Test: add it to the best fusion (smooth + parts + shape-context = 78.1%).

Run:  PYTHONPATH=.:runners/dsl/python python -m scripts.jabberwock_stroke_relations [episodes]
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
from domains import stroke_relations as sr
from domains.recognition_graph import predict_smooth_part_sc_term, predict_smooth_part_sc_rel_term

SEP = "=" * 92
WHOLE_N, PER_PART, THETA = 64, 12, 70.0


class _Pred:
    __slots__ = ("_json",)

    def __init__(self, d):
        self._json = d


def main():
    episodes = int(sys.argv[1]) if len(sys.argv) > 1 else 55
    way = 20
    print(SEP)
    print("STROKE RELATIONS (graph-native): match parts by their JUNCTION signature (end/along/free) —")
    print("the topology that ties parts into a character — added to the smooth+parts+shape-context fusion.")
    print(SEP)
    if not ow.have_data("evaluation"):
        print(f"\n  Omniglot strokes not found under {ow.DATA}.")
        return 1

    by_alph = {a: ow.characters(a, "evaluation") for a in ow.alphabets("evaluation")}
    by_alph = {a: cs for a, cs in by_alph.items() if len(cs) >= way}
    alph_names = sorted(by_alph)
    wc: dict[str, np.ndarray] = {}
    pc: dict[str, list] = {}
    rc: dict[str, list] = {}

    def whole(p):
        if p not in wc:
            wc[p] = ow.trajectory(p, WHOLE_N, per_stroke=True)
        return wc[p]

    def parts(p):
        if p not in pc:
            pc[p] = cp.canonical_parts(ow.load_strokes(p), THETA, per_part=PER_PART)
        return pc[p]

    def rels(p):
        if p not in rc:
            rc[p] = sr.relation_feats(parts(p))
        return rc[p]

    def add(s, p, *, q):
        n = s.add_node("Mark", {}) if q else s.add_node("Concept", {"is_word": 1.0})
        s.set_attr(n, "axs_heard_feat" if q else "axs_synth_feat", whole(p).tolist())
        for ss, rf in zip(parts(p), rels(p)):
            st = s.add_node("Stroke", {"stroke_pts": ss.tolist(), "rel_feat": rf})
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
    print(f"    smooth + parts + shape-context (best so far)      : {100*base:5.1f}%", flush=True)
    best = base
    for rw in (0.2, 0.4, 0.8):
        a = recog(predict_smooth_part_sc_rel_term(0.25, 1.6, rw))
        best = max(best, a)
        print(f"    + RELATIONS cue (junction signature, w={rw:>4})     : {100*a:5.1f}%", flush=True)

    print(f"\n  {SEP[:70]}")
    print(f"  best with the RELATIONS cue: {100*best:.1f}%  ({100*(best-base):+.1f} vs {100*base:.1f}%)")
    print(f"  {SEP[:70]}")
    print(f"  the relations are graph-native (junction signature per Stroke, matched by a part-")
    print(f"  correspondence Term); the numbers say whether topology adds over the metric cues.")
    print(SEP)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

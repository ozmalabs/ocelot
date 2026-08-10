"""SMOOTH DEFORMATION FIELD vs the global-affine DeformDist — the LOOOS "distortable canvas".

The jabberwock read "Learning from One and Only One Shot" and named the acquire target: its global-
affine DeformDist (54%, a wrong-class over-flexes uniformly) should be replaced by a SMOOTH non-rigid
deformation FIELD whose distortion COST is the metric (the paper's distortable canvas + transformation
multi-flows + multi-level optimisation). SmoothDeformDist is that Rust primitive. Here we measure it
head-to-head against the no-deform holistic match (PointSetDist, 66.6%) and the global affine
(DeformDist, 54%) on the same Omniglot one-shot episodes — whole-figure (the canvas), training-free.

Run:  PYTHONPATH=.:runners/dsl/python python -m scripts.jabberwock_smooth_deform [episodes] [way]
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import numpy as np

import substrate_rs as srs
from domains import glyph_motor_world as gm
from domains import omniglot_world as ow
from domains.recognition_graph import (predict_pointset_term, predict_deform_term,
                                        predict_smoothdeform_term, predict_tps_term,
                                        predict_shapecontext_term, predict_sctps_term)

SEP = "=" * 92
WHOLE_N = 64


class _Pred:
    __slots__ = ("_json",)

    def __init__(self, d):
        self._json = d


def main():
    episodes = int(sys.argv[1]) if len(sys.argv) > 1 else 80
    way = int(sys.argv[2]) if len(sys.argv) > 2 else 20

    print(SEP)
    print("SMOOTH DEFORMATION FIELD (LOOOS 'distortable canvas') vs the global-affine DeformDist, on Omniglot.")
    print(SEP)

    if not ow.have_data("evaluation"):
        print(f"\n  Omniglot stroke data not found under {ow.DATA} (see scripts/omniglot_one_shot.py).")
        return 1

    by_alph = {a: ow.characters(a, "evaluation") for a in ow.alphabets("evaluation")}
    by_alph = {a: cs for a, cs in by_alph.items() if len(cs) >= way}
    alph_names = sorted(by_alph)
    cache: dict[str, np.ndarray] = {}

    def traj(path):
        t = cache.get(path)
        if t is None:
            t = ow.trajectory(path, WHOLE_N, per_stroke=True)
            cache[path] = t
        return t

    rng = np.random.default_rng(7)
    specs = []
    for _ in range(episodes):
        alph = alph_names[int(rng.integers(len(alph_names)))]
        chars = by_alph[alph]
        idx = rng.permutation(len(chars))[:way]
        ex = int(rng.integers(20)); q = int(rng.integers(20))
        while q == ex:
            q = int(rng.integers(20))
        specs.append((chars, idx, ex, q))

    def recog(term):
        ok = tot = 0
        for chars, idx, ex, q in specs:
            s = srs.Substrate()
            queries = []
            for j in idx:
                files = ow.drawings(chars[j])
                if len(files) < 20:
                    continue
                name = os.path.relpath(chars[j], ow.split_dir("evaluation")).replace(os.sep, "/")
                c = s.add_node("Concept", {"name": name, gm.WORD_ATTR: 1.0})
                s.set_attr(c, gm.SYNTH_ATTR, traj(files[ex]).tolist())
                queries.append((name, files[q]))
            for name, qpath in queries:
                m = s.add_node("Mark", {gm.MARK_ATTR: traj(qpath).tolist()})
                w = s.evaluate(_Pred(term), {"s": m})
                pred = s.node(w)["attrs"].get("name") if w is not None else None
                ok += (pred == name); tot += 1
        return ok / max(tot, 1)

    print(f"\n  {episodes} episodes, {way}-way one-shot (chance {100.0/way:.1f}%), whole-figure point sets:\n", flush=True)
    rows = [
        ("no deform        (PointSetDist)", predict_pointset_term()),
        ("smooth FFD field (SmoothDeformDist)", predict_smoothdeform_term()),
        ("TPS + NN corresp (TpsDeformDist)", predict_tps_term()),
        ("shape context    (ShapeContextDist)", predict_shapecontext_term()),
        ("SC corresp + TPS (ScTpsDist)", predict_sctps_term()),
    ]
    res = {}
    for label, term in rows:
        a = recog(term)
        res[label] = a
        print(f"    {label:>38} : {100*a:5.1f}%", flush=True)

    sd = res["smooth FFD field (SmoothDeformDist)"]
    tn = res["TPS + NN corresp (TpsDeformDist)"]
    st = res["SC corresp + TPS (ScTpsDist)"]
    print(f"\n  {SEP[:70]}")
    print(f"  SC+TPS vs TPS+NN: {100*(st-tn):+.1f} pts   |   SC+TPS vs smooth field: {100*(st-sd):+.1f} pts")
    print(f"  {SEP[:70]}")
    print(f"  reference: canonical-parse fusion 73.5%; humans ~95.5%, BPL ~96.7%.")
    print(f"  The smooth non-rigid field is the paper's distortable canvas: a local warp the true class")
    print(f"  needs little of and a wrong class pays for (distortion cost = metric) — replacing the global")
    print(f"  affine that over-flexed every class uniformly. The numbers say whether the replacement earns it.")
    print(SEP)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

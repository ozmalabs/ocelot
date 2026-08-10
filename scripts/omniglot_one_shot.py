"""OMNIGLOT ONE-SHOT BY MOTOR ANALYSIS-BY-SYNTHESIS — the writing recogniser on REAL handwriting.

Scales scripts/glyph_motor_abs.py from synthetic stroke programs to REAL human online handwriting
(Omniglot stroke data). The canonical within-alphabet 20-way ONE-SHOT task: shown ONE drawing of
each of 20 novel characters (the candidates) and a query drawing of one of them by a DIFFERENT
person, name the character. The agent treats each candidate's real pen trajectory as its "how to
write" that character (axs_synth_feat) and reads the query as the character whose written form best
matches — argmax over candidates of -DtwTo(query, candidate). That is the SAME graph Term the speech
recogniser and the synthetic glyph recogniser use (domains/recognition_graph.predict_synth_term):
one analysis-by-synthesis principle, now on real handwriting. Training-free (no fit, no net): the
trajectory match IS the recogniser.

Honest framing: this is a 1-nearest-exemplar-by-trajectory-DTW one-shot — a simple, training-free
baseline, not BPL. We report the real number against the known reference spread and name the residual.

Run:  PYTHONPATH=.:runners/dsl/python python -m scripts.omniglot_one_shot [episodes] [way] [n_points]
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
from domains.recognition_graph import (predict_synth_term, predict_pointset_term,
                                        predict_deform_term)

SEP = "=" * 92


class _Pred:
    __slots__ = ("_json",)

    def __init__(self, d):
        self._json = d


def main():
    episodes = int(sys.argv[1]) if len(sys.argv) > 1 else 250
    way = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    n = int(sys.argv[3]) if len(sys.argv) > 3 else 64

    print(SEP)
    print("OMNIGLOT ONE-SHOT BY MOTOR ANALYSIS-BY-SYNTHESIS — the writing recogniser on REAL handwriting.")
    print("Shown ONE drawing of each of 20 novel characters + a query by a DIFFERENT person, name it:")
    print("argmax over candidates of -DtwTo(query, candidate) — the SAME graph Term as speech & synthetic")
    print("glyphs. Each candidate's real pen trajectory IS its 'how to write'. Training-free.")
    print(SEP)

    if not ow.have_data("evaluation"):
        print(f"\n  Omniglot stroke data not found under {ow.DATA}. Download once:")
        print("    mkdir -p /tmp/omniglot && cd /tmp/omniglot && \\")
        print("    curl -sSL -O https://github.com/brendenlake/omniglot/raw/master/python/strokes_evaluation.zip && \\")
        print("    unzip -q strokes_evaluation.zip")
        return 1

    alphs = ow.alphabets("evaluation")
    # precompute character dirs per alphabet; keep alphabets with >= `way` characters.
    by_alph = {a: ow.characters(a, "evaluation") for a in alphs}
    by_alph = {a: cs for a, cs in by_alph.items() if len(cs) >= way}
    alph_names = sorted(by_alph)
    print(f"\n  evaluation split: {len(alph_names)} alphabets with >= {way} characters "
          f"(novel scripts: {', '.join(alph_names[:6])}, ...)")
    print(f"  {way}-way one-shot, {episodes} episodes, trajectory resampled to {n} points. "
          f"chance = {100.0/way:.1f}%.\n")

    dtw_term = predict_synth_term()              # ordered warp (DtwTo)
    ps_term = predict_pointset_term()            # order-invariant point set (PointSetDist)
    df_term = predict_deform_term()              # BPL token model: deformable fit (DeformDist)
    traj_cache: dict[tuple, np.ndarray] = {}

    def traj(path, per_stroke):
        key = (path, per_stroke)
        t = traj_cache.get(key)
        if t is None:
            t = ow.trajectory(path, n, per_stroke=per_stroke)
            traj_cache[key] = t
        return t

    # precompute the episode specs ONCE so every config is scored on the SAME episodes (fair).
    rng = np.random.default_rng(7)
    specs = []
    for _ep in range(episodes):
        alph = alph_names[int(rng.integers(len(alph_names)))]
        chars = by_alph[alph]
        idx = rng.permutation(len(chars))[:way]
        ex = int(rng.integers(20))
        q = int(rng.integers(20))
        while q == ex:
            q = int(rng.integers(20))
        specs.append((chars, idx, ex, q))

    def evaluate(per_stroke: bool, fold_angles, term):
        """Score all episodes under a conditioning (whole/per-stroke), optional rotation fold, and
        a recognition term (ordered DtwTo or order-invariant PointSetDist)."""
        ok = tot = 0
        ep_accs = []
        for chars, idx, ex, q in specs:
            s = srs.Substrate()
            queries = []
            for j in idx:
                cdir = chars[j]
                files = ow.drawings(cdir)
                if len(files) < 20:
                    continue
                name = os.path.relpath(cdir, ow.split_dir("evaluation")).replace(os.sep, "/")
                ext = traj(files[ex], per_stroke)
                if fold_angles is None:
                    c = s.add_node("Concept", {"name": name, gm.WORD_ATTR: 1.0})
                    s.set_attr(c, gm.SYNTH_ATTR, ext.tolist())
                else:                                # fold rotation into the forward model
                    for a in fold_angles:
                        c = s.add_node("Concept", {"name": name, gm.WORD_ATTR: 1.0})
                        s.set_attr(c, gm.SYNTH_ATTR, gm.rotate_traj(ext, a).tolist())
                queries.append((name, traj(files[q], per_stroke)))
            ep_ok = 0
            for name, qt in queries:
                m = s.add_node("Mark", {gm.MARK_ATTR: qt.tolist()})
                w = s.evaluate(_Pred(term), {"s": m})
                pred = s.node(w)["attrs"].get("name") if w is not None else None
                ep_ok += (pred == name)
            ok += ep_ok; tot += len(queries)
            ep_accs.append(ep_ok / max(len(queries), 1))
        return ok / max(tot, 1), ok, tot, float(np.std(ep_accs))

    configs = [
        ("per-stroke,  ordered DTW",         dict(per_stroke=True,  fold_angles=None, term=dtw_term)),
        ("per-stroke,  order-inv point-set", dict(per_stroke=True,  fold_angles=None, term=ps_term)),
        ("per-stroke,  deformable (token)",  dict(per_stroke=True,  fold_angles=None, term=df_term)),
    ]
    print(f"  {'recogniser (conditioning, match)':>34}  {'one-shot acc':>13}")
    print(f"  {'-'*34}  {'-'*13}")
    best = (0.0, "")
    for label, kw in configs:
        acc, ok, tot, sd = evaluate(**kw)
        print(f"  {label:>34}  {100*acc:7.1f}%  ({ok}/{tot})")
        if acc > best[0]:
            best = (acc, label)

    print(f"\n  {SEP[:70]}")
    print(f"  BEST: {100*best[0]:.1f}%  via {best[1]}   (chance {100.0/way:.1f}%, {episodes} episodes)")
    print(f"  {SEP[:70]}")
    print(f"  reference spread (Lake et al. 2015, 20-way within-alphabet one-shot):")
    print(f"    humans ~95.5%   |   BPL (programs) ~96.7%   |   image Modified-Hausdorff baseline ~38%")
    print(f"  Training-free 1-nearest-exemplar; the agent reads a novel character from ONE example by")
    print(f"  matching how it would be WRITTEN — the SAME analysis-by-synthesis decision as speech and")
    print(f"  synthetic glyphs, on REAL handwriting. Progression of the FORWARD MODEL's richness:")
    print(f"    ordered DTW -> order-invariant point-set (absorbs stroke ORDER) -> deformable TOKEN")
    print(f"    model (DeformDist: affine-ICP fit + a penalty on non-rigidity = BPL's 'deformations")
    print(f"    allowed but COST'). Each step is a new graph Term; the recognition decision is unchanged.")
    print(SEP)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

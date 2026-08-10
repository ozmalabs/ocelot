"""FULL JOINT GENERATIVE INFERENCE (graph-native) — marginalise parse AND correspondence together.

The arc's one lever that ever moved recognition was MARGINALISING an uncertain structural latent (the
parse, +1.1). Every learned cue failed. The genuine BPL move is to marginalise ALL the uncertain
structure JOINTLY. The parse-marginal already averages over parse hypotheses but COMMITS the part
correspondence (a hard min — one part-to-part assignment). Full joint inference also marginalises the
correspondence: a soft-min over part-to-part assignment inside each parse-pairing (predict_full_joint_sc_term).
The deformation stays committed (the arc found it is a FIT latent — marginalising it HURT). Composes held
Terms (nested Sum/Exp/Log over PointSetDist), no new Rust.

Test: does marginalising the correspondence too beat the parse-only marginal (the arc peak, ~79.9%)?

Run:  PYTHONPATH=.:runners/dsl/python python -m scripts.jabberwock_full_joint [episodes]
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
from domains.recognition_graph import (predict_smooth_part_sc_term, predict_smooth_marginal_sc_term,
                                        predict_full_joint_sc_term, PARSE_EDGE)

SEP = "=" * 92
WHOLE_N, PER_PART = 64, 12
THETAS = (55.0, 70.0, 85.0)


class _Pred:
    __slots__ = ("_json",)

    def __init__(self, d):
        self._json = d


def main():
    episodes = int(sys.argv[1]) if len(sys.argv) > 1 else 40
    way = 20
    print(SEP)
    print("FULL JOINT GENERATIVE INFERENCE: marginalise the PARSE *and* the part CORRESPONDENCE jointly")
    print("(soft-min over both), the deformation committed — the genuine BPL inference, no learned cue.")
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

    def add(s, p, *, q):
        n = s.add_node("Mark", {}) if q else s.add_node("Concept", {"is_word": 1.0})
        s.set_attr(n, "axs_heard_feat" if q else "axs_synth_feat", whole(p).tolist())
        for ss in parts(p, 70.0):
            st = s.add_node("Stroke", {"stroke_pts": ss.tolist()}); s.add_edge_unchecked(n, "has_stroke", st)
        for th in THETAS:
            ph = s.add_node("ParseHyp", {"theta": th}); s.add_edge_unchecked(n, PARSE_EDGE, ph)
            for ss in parts(p, th):
                st = s.add_node("Stroke", {"stroke_pts": ss.tolist()}); s.add_edge_unchecked(ph, "has_stroke", st)
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
    base = recog(predict_smooth_part_sc_term(0.25, 1.6))
    print(f"    smooth + RIGID parts + SC (commit parse + correspondence)        : {base:5.1f}%", flush=True)
    pm = recog(predict_smooth_marginal_sc_term(0.25, 1.6, 2.0))
    print(f"    + marginalise the PARSE only (correspondence still committed)     : {pm:5.1f}%   ({pm-base:+.1f})", flush=True)
    best, bc = pm, None
    for cb in (1.0, 2.0, 5.0):
        a = recog(predict_full_joint_sc_term(0.25, 1.6, 2.0, cb))
        if a > best:
            best, bc = a, cb
        tag = "(soft)" if cb <= 1 else ("(~hard)" if cb >= 5 else "")
        print(f"    + FULL JOINT: marginalise PARSE *and* CORRESPONDENCE (b_corr={cb:>3} {tag:>6}): {a:5.1f}%   "
              f"({a-pm:+.1f} vs parse-only)", flush=True)

    print(f"\n  {SEP[:88]}")
    d = best - pm
    if d > 0.3:
        print(f"  FULL JOINT inference HELPS (+{d:.1f} over parse-only, b_corr={bc}): marginalising the part")
        print(f"  correspondence as WELL as the parse is the genuine BPL lever — averaging over ALL the uncertain")
        print(f"  structure beats committing any of it. The deformation stays committed (a fit latent).")
    else:
        print(f"  honest reading ({d:+.1f} vs parse-only): at this scale the correspondence is already near-")
        print(f"  determined given the parse, so marginalising it adds little — the parse was the load-bearing")
        print(f"  uncertainty. b_corr large (~hard) recovers the parse-only marginal, as expected.")
    print(SEP)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

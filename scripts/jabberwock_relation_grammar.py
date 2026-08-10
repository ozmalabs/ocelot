"""PHASE 2 — THE RELATION GRAMMAR: score the marginalised relations under a LEARNED prior (no teacher).

Phase 1 found relations don't pay because the junction signature is NOISY (junction detection is writer-
inconsistent) and its discriminative content (endpoint positions) is already in the part match. The agent's
plan, Phase 2: a learned generative GRAMMAR -- here its first, cheapest form, a learned per-dimension
relation PRECISION estimated from BACKGROUND (which signature dims are stable vs noise). The relation match
is then scored under that precision (mahal leaf, PRIM_MODEL = [rel_feat ++ inv_std]) instead of raw SqEuclid
-- the noisy junction-type dims down-weighted, the stable geometry up. Does the grammar make relations PAY
where the raw signature did not? Learning is in Rust (kmeans + cluster_deform_stats); Python only adapts I/O.

Run:  PYTHONPATH=.:runners/dsl/python python -m scripts.jabberwock_relation_grammar [episodes]
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import numpy as np

import substrate_rs as srs
from substrate_rs import _native
from domains import omniglot_world as ow
from domains import canonical_parse as cp
from domains import stroke_relations as sr
from domains.recognition_graph import (predict_recursive_sc_term, predict_recursive_rel_term, PARSE_EDGE,
                                        REL_PARSE_EDGE, REL_PART_EDGE, REL_FEAT_ATTR, REL_FEAT_N_ATTR,
                                        PRIM_MODEL_ATTR)

SEP = "=" * 94
WHOLE_N, PER_PART, THETA = 64, 12, 70.0
THETAS = (55.0, 70.0, 85.0)
JUNC_THRESHES = (0.20, 0.30, 0.42)
REL_D = 10                                                       # relation signature dim (2 endpoints x 5)
RIDGE = 0.05


class _Pred:
    __slots__ = ("_json",)

    def __init__(self, d):
        self._json = d


def learn_relation_precision(by_alph_bg, alph_bg, parts_fn, relfeats_fn, rng, n_chars=240):
    """LEARN (in Rust) the per-dimension relation precision from BACKGROUND relation signatures: kmeans(k=1)
    for the global mean, cluster_deform_stats for per-dim std -> inv_std. The grammar's cheapest form: which
    junction-signature dims are stable across writers (trust them) vs noise (down-weight)."""
    feats = []
    for al in alph_bg:
        for ch in by_alph_bg[al]:
            fs = ow.drawings(ch)
            for p in fs[: min(4, len(fs))]:
                for jt in JUNC_THRESHES:
                    feats.extend(relfeats_fn(p, THETA, jt))
            if len(feats) >= n_chars * 8:
                break
        if len(feats) >= n_chars * 8:
            break
    data = np.asarray(feats, dtype=np.float64)                   # (N, 10)
    n = data.shape[0]
    cent = _native.kmeans(data.reshape(-1).tolist(), n, REL_D, 1, 25)
    std = _native.cluster_deform_stats(data.reshape(-1).tolist(), n, REL_D, cent, 1, RIDGE)
    inv_std = [1.0 / (s if s > 1e-6 else 1e-6) for s in std]
    mean = list(cent[:REL_D])
    return mean, inv_std, n


def main():
    episodes = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    way = 20
    print(SEP)
    print("PHASE 2 — THE RELATION GRAMMAR: the marginalised relations scored under a LEARNED per-dimension")
    print("precision (background), not a raw signature. Does the learned prior make relations PAY?")
    print(SEP)
    if not (ow.have_data("evaluation") and ow.have_data("background")):
        print(f"\n  Omniglot strokes (evaluation+background) not found under {ow.DATA}.")
        return 1

    by_alph = {al: ow.characters(al, "evaluation") for al in ow.alphabets("evaluation")}
    by_alph = {al: cs for al, cs in by_alph.items() if len(cs) >= way}
    alph_names = sorted(by_alph)
    by_bg = {al: ow.characters(al, "background") for al in ow.alphabets("background")}
    alph_bg = sorted(by_bg)
    pc: dict = {}; rc: dict = {}; wc: dict = {}

    def whole(p):
        if p not in wc:
            wc[p] = ow.trajectory(p, WHOLE_N, per_stroke=True)
        return wc[p]

    def parts(p, th):
        k = (p, th)
        if k not in pc:
            pc[k] = cp.canonical_parts(ow.load_strokes(p), th, per_part=PER_PART)
        return pc[k]

    def relfeats(p, th, jt):
        k = (p, th, jt)
        if k not in rc:
            rc[k] = sr.relation_feats(parts(p, th), junc_thresh=jt)
        return rc[k]

    rng = np.random.default_rng(7)
    print("\n  learning the relation precision from BACKGROUND (Rust kmeans + cluster_deform_stats)...", flush=True)
    mean, inv_std, n_bg = learn_relation_precision(by_bg, alph_bg, parts, relfeats, rng)
    print(f"    {n_bg} background relation signatures; per-dim inv_std (junction-type dims vs geometry):")
    print(f"    {[round(v, 2) for v in inv_std]}", flush=True)

    def add(s, p, *, q):
        n = s.add_node("Mark", {}) if q else s.add_node("Concept", {"is_word": 1.0})
        s.set_attr(n, "axs_heard_feat" if q else "axs_synth_feat", whole(p).tolist())
        for pp in parts(p, THETA):
            s.add_edge_unchecked(n, "has_stroke", s.add_node("Stroke", {"stroke_pts": pp.tolist()}))
        for th in THETAS:
            ph = s.add_node("ParseHyp", {"theta": th}); s.add_edge_unchecked(n, PARSE_EDGE, ph)
            for pp in parts(p, th):
                s.add_edge_unchecked(ph, "has_stroke", s.add_node("Stroke", {"stroke_pts": pp.tolist()}))
        for jt in JUNC_THRESHES:
            rh = s.add_node("RelHyp", {"jt": jt}); s.add_edge_unchecked(n, REL_PARSE_EDGE, rh)
            for rf in relfeats(p, THETA, jt):
                rf = list(map(float, rf))
                rp = s.add_node("RelPart", {})
                s.set_attr(rp, REL_FEAT_ATTR, rf)                          # flat (SqEuclid)
                s.set_attr(rp, REL_FEAT_N_ATTR, [rf[:5], rf[5:]])         # nested endpoint-frames (mahal)
                s.set_attr(rp, PRIM_MODEL_ATTR, rf + inv_std)            # [mean=this signature ++ learned inv_std]
                s.add_edge_unchecked(rh, REL_PART_EDGE, rp)
        return n

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
                c = add(s, fs[ex], q=False); s.set_attr(c, "name", nm); qs.append((nm, fs[qd]))
            for nm, qp in qs:
                m = add(s, qp, q=True)
                w = s.evaluate(_Pred(term), {"s": m})
                ok += (w is not None and s.node(w)["attrs"].get("name") == nm); tot += 1
        return 100 * ok / max(tot, 1)

    print(f"\n  {episodes} episodes, {way}-way one-shot:\n", flush=True)
    base = recog(predict_recursive_sc_term(0.25, 1.6, ("has_stroke",), 6.0, 2.0, leaf="pointset"))
    print(f"    recursive recogniser, NO relations (the peak)                       : {base:5.1f}%", flush=True)
    p1 = recog(predict_recursive_rel_term(0.25, 1.6, 0.05, 6.0, 2.0, 2.0, 2.0, rel_leaf="relfeat"))
    print(f"    Phase 1: marginalised RAW relation signature (rel_w=0.05)           : {p1:5.1f}%   ({p1-base:+.1f})", flush=True)
    best, bw = base, None
    for rw in (0.05, 0.15, 0.4):
        a = recog(predict_recursive_rel_term(0.25, 1.6, rw, 6.0, 2.0, 2.0, 2.0, rel_leaf="mahal"))
        if a > best:
            best, bw = a, rw
        print(f"    Phase 2: GRAMMAR-weighted relations (learned precision, rel_w={rw:<4})  : {a:5.1f}%   ({a-base:+.1f})", flush=True)

    print(f"\n  {SEP[:90]}")
    d = best - base
    gain_over_p1 = best - p1
    if d > 0.3:
        print(f"  THE GRAMMAR MAKES RELATIONS PAY (+{d:.1f} over peak, rel_w={bw}; +{gain_over_p1:.1f} over the raw Phase-1")
        print(f"  signature). The learned per-dim precision down-weights the noisy junction-type dims so the")
        print(f"  relational match adds signal the part shape did not -- relations finally contribute, as a")
        print(f"  learned generative prior. Phase 2 (the grammar) is where the compositional gain begins.")
    else:
        print(f"  honest reading ({d:+.1f} vs peak, {gain_over_p1:+.1f} vs raw Phase 1): the learned per-dim precision")
        print(f"  is the grammar's CHEAPEST form (reweight signature dims) and it does {'beat' if gain_over_p1 > 0.3 else 'not beat'} the raw signature, but")
        print(f"  still does not lift the peak. A diagonal reweighting cannot manufacture discriminative")
        print(f"  relational signal the part match lacks: the gain needs the STRUCTURED grammar -- relation")
        print(f"  distributions CONDITIONED on the composing primitives (P(relation | prim_i, prim_j)), used")
        print(f"  generatively -- not a global dim-reweighting. That conditioning is the real Phase-2 build.")
    print(SEP)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

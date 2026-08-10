"""MARGINALISING JOINT INFERENCE (graph-native) — the culmination the agent reasoned its way to.

The parse is uncertain (writer-inconsistent — every committed parse/relation piece failed). So instead
of committing to ONE parse, each drawing carries K PARSE HYPOTHESES (canonical parts at K thresholds,
drawing --has_parse--> ParseHyp --has_stroke--> Stroke), and the part distance MARGINALISES over the
parse-pairings via a soft-min (log-sum-exp at temperature beta): large beta -> commit to the best parse
(MAP); finite beta -> AVERAGE over plausible parses (the Bayesian marginalisation). Graph-native
(Sum/Exp/Log over the held part distance). Test: the marginal part cue in the best fusion (smooth +
parts + shape-context = 78.1%), swept over beta — does marginalising over the uncertain parse beat
committing to the single tuned one?

Run:  PYTHONPATH=.:runners/dsl/python python -m scripts.jabberwock_marginal_inference [episodes]
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
                                        predict_marginal_all_sc_term, PARSE_EDGE)

SEP = "=" * 92
WHOLE_N, PER_PART = 64, 12
THETAS = (55.0, 70.0, 85.0)          # the parse hypotheses to marginalise over


class _Pred:
    __slots__ = ("_json",)

    def __init__(self, d):
        self._json = d


def main():
    episodes = int(sys.argv[1]) if len(sys.argv) > 1 else 45
    way = 20
    print(SEP)
    print("MARGINALISING JOINT INFERENCE (graph-native): average the part match over K parse hypotheses")
    print(f"(thetas {[int(t) for t in THETAS]}) via a soft-min (log-sum-exp) instead of committing to one parse.")
    print(SEP)
    if not ow.have_data("evaluation"):
        print(f"\n  Omniglot strokes not found under {ow.DATA}.")
        return 1

    by_alph = {a: ow.characters(a, "evaluation") for a in ow.alphabets("evaluation")}
    by_alph = {a: cs for a, cs in by_alph.items() if len(cs) >= way}
    alph_names = sorted(by_alph)
    wc: dict[str, np.ndarray] = {}
    pc: dict[tuple, list] = {}

    def whole(p):
        if p not in wc:
            wc[p] = ow.trajectory(p, WHOLE_N, per_stroke=True)
        return wc[p]

    def parts(p, th):
        key = (p, th)
        if key not in pc:
            pc[key] = cp.canonical_parts(ow.load_strokes(p), th, per_part=PER_PART)
        return pc[key]

    def add(s, p, *, q):
        n = s.add_node("Mark", {}) if q else s.add_node("Concept", {"is_word": 1.0})
        s.set_attr(n, "axs_heard_feat" if q else "axs_synth_feat", whole(p).tolist())
        for ss in parts(p, 70.0):                              # baseline single parse: node has_stroke
            st = s.add_node("Stroke", {"stroke_pts": ss.tolist()})
            s.add_edge_unchecked(n, "has_stroke", st)
        for th in THETAS:                                      # marginal: K parse hypotheses
            ph = s.add_node("ParseHyp", {"theta": th})
            s.add_edge_unchecked(n, PARSE_EDGE, ph)
            for ss in parts(p, th):
                st = s.add_node("Stroke", {"stroke_pts": ss.tolist()})
                s.add_edge_unchecked(ph, "has_stroke", st)
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
    print(f"    single tuned parse, committed deformation (best fusion) : {100*base:5.1f}%", flush=True)
    parse_marg = recog(predict_smooth_marginal_sc_term(0.25, 1.6, 2.0))
    print(f"    + MARGINALISE the PARSE (soft, beta=2)                  : {100*parse_marg:5.1f}%   "
          f"({100*(parse_marg-base):+.1f})", flush=True)
    best = max(base, parse_marg)
    for db in (1.0, 3.0, 10.0):
        a = recog(predict_marginal_all_sc_term(0.25, 1.6, 2.0, db))
        best = max(best, a)
        tag = "(~MAP)" if db >= 10 else ("(soft)" if db <= 1 else "")
        print(f"    + MARGINALISE PARSE *and* DEFORMATION (d-beta={db:>4} {tag:>6}) : {100*a:5.1f}%   "
              f"({100*(a-parse_marg):+.1f} vs parse-only)", flush=True)

    print(f"\n  {SEP[:70]}")
    print(f"  best (marginalise parse + deformation): {100*best:.1f}%  ({100*(best-base):+.1f} vs committed {100*base:.1f}%)")
    print(f"  {SEP[:70]}")
    print(f"  graph-native (Sum/Exp/Log over held distances). BPL's posture on BOTH uncertain latents:")
    print(f"  average over the uncertain PARSE and the uncertain DEFORMATION rather than committing.")
    print(SEP)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

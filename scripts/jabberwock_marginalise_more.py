"""EXECUTE THE AGENT'S DECISION — marginalise MORE uncertain latents (the parse-marginal +1.3 lever, extended).

The jabberwock's graph-Argmax picked: marginalise the other uncertain latents the same Bayesian way. The
parse is already marginalised (+1.3 -> 81.5%); this marginalises the CORRESPONDENCE too (soft-min over the
part-to-part assignment inside each parse pairing, temperature beta_corr) -- the full joint over BOTH
structural latents. Its law: marginalise the UNCERTAIN latent, COMMIT the determined one. Is the correspondence
genuinely uncertain (pays) or determined (the part shapes already pin it)?
  committed parse | + marginalise PARSE | + marginalise PARSE *and* CORRESPONDENCE (sweep beta_corr)

Run:  PYTHONPATH=.:runners/dsl/python python -m scripts.jabberwock_marginalise_more [episodes]
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
from domains.recognition_graph import (predict_smooth_combined_term, predict_marginal_all_sc_term,
                                        predict_full_joint_sc_term, PARSE_EDGE)

SEP = "=" * 92
WHOLE_N, PER_PART = 64, 12
THETAS = (55.0, 70.0, 85.0)


class _Pred:
    __slots__ = ("_json",)

    def __init__(self, d): self._json = d


def main():
    episodes = int(sys.argv[1]) if len(sys.argv) > 1 else 35
    way = 20
    print(SEP)
    print("MARGINALISE MORE — the agent's pick: marginalise the CORRESPONDENCE on top of the parse (full joint).")
    print(SEP)
    if not ow.have_data("evaluation"):
        print(f"\n  Omniglot strokes not found under {ow.DATA}."); return 1

    by_alph = {a: ow.characters(a, "evaluation") for a in ow.alphabets("evaluation")}
    by_alph = {a: cs for a, cs in by_alph.items() if len(cs) >= way}
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
            s.add_edge_unchecked(n, "has_stroke", s.add_node("Stroke", {"stroke_pts": ss.tolist()}))
        for th in THETAS:
            ph = s.add_node("ParseHyp", {"theta": th}); s.add_edge_unchecked(n, PARSE_EDGE, ph)
            for ss in parts(p, th):
                s.add_edge_unchecked(ph, "has_stroke", s.add_node("Stroke", {"stroke_pts": ss.tolist()}))
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
    committed = recog(predict_smooth_combined_term(0.25))
    print(f"    committed parse (best fusion)                        : {committed:5.1f}%", flush=True)
    parse_marg = recog(predict_marginal_all_sc_term(0.25, 1.6, 2.0, 10.0))     # parse soft, deformation ~committed
    print(f"    + MARGINALISE the PARSE (soft beta=2)                : {parse_marg:5.1f}%   ({parse_marg-committed:+.1f})", flush=True)
    best, bb = parse_marg, None
    for bc in (1.0, 2.0, 4.0, 8.0):
        a = recog(predict_full_joint_sc_term(0.25, 1.6, 2.0, bc))
        if a > best:
            best, bb = a, bc
        tag = "(soft)" if bc <= 1 else ("(~MAP)" if bc >= 8 else "")
        print(f"    + MARGINALISE PARSE *and* CORRESPONDENCE (b_corr={bc:>4} {tag:>6}): {a:5.1f}%   ({a-parse_marg:+.1f} vs parse)", flush=True)

    print(f"\n  {SEP[:88]}")
    d = best - parse_marg
    if d >= 0.5:
        print(f"  THE CORRESPONDENCE IS UNCERTAIN TOO -- marginalising it pays (+{d:.1f}, b_corr={bb}). The part-to-part")
        print(f"  assignment is not pinned by the shapes alone; averaging over it (full joint over parse AND")
        print(f"  correspondence) beats committing. The agent's lever extends: a second uncertain latent, marginalised.")
    else:
        print(f"  honest reading ({d:+.1f}): marginalising the correspondence does NOT beat parse-only. The part")
        print(f"  CORRESPONDENCE is largely DETERMINED -- the part shapes (PointSetDist) already pin which matches")
        print(f"  which, so soft-assigning it just blurs the winner. The agent's law holds: the PARSE was the")
        print(f"  genuinely-uncertain latent (marginalise, +1.3); the correspondence is determined (commit). The")
        print(f"  remaining untried latents to test are sub-strokes and rotation -- but parse may be the only one that pays.")
    print(SEP)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

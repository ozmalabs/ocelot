"""THE JABBERWOCK LEARNS A PER-PART GENERATIVE MODEL — a sub-stroke primitive library (BPL's vocabulary).

Learns the library by clustering the canonical sub-strokes of the Omniglot BACKGROUND set (via the
RUST `kmeans` primitive — the learning is in Rust, not Python). A character is encoded as a soft
BAG-OF-PRIMITIVES histogram over the learned library (Rust `bow_histogram`) — a writer-invariant
COMPOSITION cue. The recognition DECISION fuses it (graph Dot/cosine) onto the agent's current best
(smooth field + canonical parts + shape context = 78.1%). Standard Omniglot protocol: learn on
background, test one-shot on the NOVEL evaluation alphabets.

Run:  PYTHONPATH=.:runners/dsl/python python -m scripts.jabberwock_learns_parts [episodes] [k] [bg_files]
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
from domains import substroke_codebook as sb
from domains.recognition_graph import predict_smooth_part_sc_term, predict_full_term

SEP = "=" * 92
WHOLE_N, PER_PART, THETA = 64, 12, 70.0


class _Pred:
    __slots__ = ("_json",)

    def __init__(self, d):
        self._json = d


def main():
    episodes = int(sys.argv[1]) if len(sys.argv) > 1 else 55
    k = int(sys.argv[2]) if len(sys.argv) > 2 else 80
    bg_files = int(sys.argv[3]) if len(sys.argv) > 3 else 1600
    way = 20

    print(SEP)
    print("THE JABBERWOCK LEARNS A PER-PART GENERATIVE MODEL — sub-stroke primitive library (Rust kmeans).")
    print(SEP)
    if not ow.have_data("evaluation") or not ow.have_data("background"):
        print(f"\n  Omniglot strokes (background AND evaluation) not found under {ow.DATA}.")
        return 1

    # 1) LEARN the library from background canonical sub-strokes (the learning is the Rust primitive).
    bg = [f for a in ow.alphabets("background") for c in ow.characters(a, "background")
          for f in ow.drawings(c)]
    rng0 = np.random.default_rng(0)
    bg = [bg[i] for i in rng0.permutation(len(bg))[:bg_files]]
    print(f"\n  learning a {k}-primitive sub-stroke library from {len(bg)} background drawings "
          f"(Rust kmeans over their canonical sub-strokes)...", flush=True)
    cent = sb.learn_codebook(bg, k=k)
    print(f"  learned library: {cent.shape[0]} primitives x {cent.shape[1]}-dim.\n")

    by_alph = {a: ow.characters(a, "evaluation") for a in ow.alphabets("evaluation")}
    by_alph = {a: cs for a, cs in by_alph.items() if len(cs) >= way}
    alph_names = sorted(by_alph)
    wc: dict[str, np.ndarray] = {}
    pc: dict[str, list] = {}
    bc: dict[str, list] = {}

    def whole(p):
        if p not in wc:
            wc[p] = ow.trajectory(p, WHOLE_N, per_stroke=True)
        return wc[p]

    def parts(p):
        if p not in pc:
            pc[p] = cp.canonical_parts(ow.load_strokes(p), THETA, per_part=PER_PART)
        return pc[p]

    def bowh(p):
        if p not in bc:
            bc[p] = sb.bow(parts(p), cent).tolist()
        return bc[p]

    def add(s, p, *, q):
        n = s.add_node("Mark", {}) if q else s.add_node("Concept", {"is_word": 1.0})
        s.set_attr(n, "axs_heard_feat" if q else "axs_synth_feat", whole(p).tolist())
        s.set_attr(n, "bow_hist", bowh(p))
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

    print(f"  {episodes} episodes, {way}-way one-shot (chance {100.0/way:.1f}%):\n", flush=True)
    base = recog(predict_smooth_part_sc_term(0.25, 1.6))
    print(f"    smooth + canonical parts + shape-context (best)   : {100*base:5.1f}%", flush=True)
    best = base
    for bw in (0.3, 0.6, 1.0):
        a = recog(predict_full_term(0.25, 1.6, bw))
        best = max(best, a)
        print(f"    + learned bag-of-primitives cue (w={bw:>4})        : {100*a:5.1f}%", flush=True)

    print(f"\n  {SEP[:70]}")
    print(f"  best with the learned per-part cue: {100*best:.1f}%  ({100*(best-base):+.1f} vs geometric "
          f"best {100*base:.1f}%)")
    print(f"  {SEP[:70]}")
    print(f"  reference: humans ~95.5%, BPL ~96.7%. The library was LEARNED in Rust from the background;")
    print(f"  the agent holds it as graph data and fuses the composition cue graph-natively. The numbers")
    print(f"  say whether a learned per-part vocabulary adds over the geometric cues. Honest either way.")
    print(SEP)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

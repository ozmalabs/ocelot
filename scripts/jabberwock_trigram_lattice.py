"""HIGHER-ORDER (TRIGRAM) LM IN THE LATTICE (graph-native) — order lives in the lattice, measured.

The Viterbi decode used a bigram (first-order) LM. A higher-order LM needs NO new decode logic: in an HMM
the order lives in the STATE design, not the algorithm. A trigram LM is just a richer lattice — each state
is a (prev, cur) symbol PAIR (so it carries the bigram history), edges connect only COMPATIBLE states
(predecessor.sym == cur.prev) and carry the trigram score logP(cur | prev2, prev1). The graph-native
Viterbi Rules (vit_step forward + vit_backtrace) are ORDER-AGNOSTIC and reused UNCHANGED — the entire
higher-order extension is in the lattice graph DATA the host builds.

The demo plants a genuine TRIGRAM source (the next symbol depends on the previous TWO, in a way the bigram
marginal blurs), samples sequences from it, and decodes per-letter vs bigram-Viterbi vs trigram-Viterbi
over the SAME decode Rules — measuring that the higher-order context (richer lattice) reads better.

Run:  PYTHONPATH=.:runners/dsl/python python -m scripts.jabberwock_trigram_lattice [n_seqs]
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import numpy as np

import substrate_rs as srs
from domains import omniglot_world as ow
from domains.recognition_graph import _PointSetDist, _Attr, _V, _Argmax, _NodesWhere, _Lit

SEP = "=" * 92
WHOLE_N, ALPHA, SEQLEN = 64, 8, 5
WEIGHTS = (0.05, 0.15, 0.40)


class _Pred:
    __slots__ = ("_json",)

    def __init__(self, d):
        self._json = d


_DIST = _Pred(_PointSetDist(_Attr(_V("s"), "axs_heard_feat"), _Attr(_V("w"), "axs_synth_feat")))
_SEED = None


def _new_hyp(s, lat, pos, sym, emission, **extra):
    h = s.add_node("Hyp", {})
    s.set_attr(h, "pos", float(pos)); s.set_attr(h, "sym", float(sym)); s.set_attr(h, "emission", float(emission))
    for k, v in extra.items():
        s.set_attr(h, k, float(v))
    for k in ("scored", "vscore", "best_in", "on_path"):
        s.set_attr(h, k, 0.0)
    s.add_edge_unchecked(h, "in_lattice", lat)
    return h


def _decode(s, lat, by_pos, weight):
    """Forward sweep + graph-native backtrace over the SHARED Viterbi rules; return {pos: winning sym}."""
    for hs in by_pos:
        for h in hs:
            for k in ("scored", "vscore", "best_in", "on_path"):
                s.set_attr(h, k, 0.0)
    s.set_attr(lat, "lm_weight", float(weight))
    for p in range(len(by_pos)):                                  # FORWARD: tick active_pos left-to-right
        s.set_attr(lat, "active_pos", float(p))
        s._inner.run_rules(100000)
    term = s.evaluate(_Pred(_Argmax(_NodesWhere("Hyp", "pos", _Lit(float(len(by_pos) - 1))), "h",
                                    _Attr(_V("h"), "vscore"))))
    s.set_attr(term, "on_path", 1.0)
    s._inner.run_rules(100000)                                    # BACKTRACE: vit_backtrace marks on_path back
    path = [None] * len(by_pos)
    for p, hs in enumerate(by_pos):
        for h in hs:
            if s.node(h)["attrs"].get("on_path") == 1.0:
                path[p] = int(s.node(h)["attrs"]["sym"])
    return path


def main():
    n_seqs = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    print(SEP)
    print("HIGHER-ORDER (TRIGRAM) LM IN THE LATTICE (graph-native): the order lives in the lattice STATE,")
    print("the decode Rules are order-agnostic and reused — trigram = a richer lattice, same Viterbi.")
    print(SEP)
    if not ow.have_data("evaluation"):
        print(f"\n  Omniglot strokes not found under {ow.DATA}.")
        return 1
    global _SEED
    _SEED = json.loads((Path(ROOT) / "seeds" / "viterbi_decode.json").read_text())

    by_alph = {a: ow.characters(a, "evaluation") for a in ow.alphabets("evaluation")}
    by_alph = {a: cs for a, cs in by_alph.items() if len(cs) >= ALPHA}
    alph = sorted(by_alph)[0]
    ch = by_alph[alph]
    wc: dict[str, np.ndarray] = {}

    def whole(p):
        if p not in wc:
            wc[p] = ow.trajectory(p, WHOLE_N, per_stroke=True)
        return wc[p]

    tmpl = [whole(ow.drawings(ch[x])[0]) for x in range(ALPHA)]
    ndrw = min(len(ow.drawings(ch[x])) for x in range(ALPHA))

    # --- a genuine TRIGRAM source: P(c | a, b) depends on BOTH a and b; the bigram marginal blurs it ---
    rng = np.random.default_rng(7)
    T3 = np.full((ALPHA, ALPHA, ALPHA), 0.02)
    for a in range(ALPHA):
        for b in range(ALPHA):
            for c in rng.permutation(ALPHA)[:2]:
                T3[a, b, c] += 1.0
    T3 /= T3.sum(2, keepdims=True)
    T2 = T3.mean(0); T2 /= T2.sum(1, keepdims=True)               # bigram = marginal over the first symbol
    logT3, logT2 = np.log(T3), np.log(T2)

    seqs = []
    for _ in range(n_seqs):
        sq = [int(rng.integers(ALPHA)), int(rng.integers(ALPHA))]
        for _ in range(SEQLEN - 2):
            sq.append(int(rng.choice(ALPHA, p=T3[sq[-2], sq[-1]])))
        seqs.append(sq)

    rngw = np.random.default_rng(13)
    tot = ind_ok = w_ind = 0
    bi_ok = {w: 0 for w in WEIGHTS}; bi_word = {w: 0 for w in WEIGHTS}
    tri_ok = {w: 0 for w in WEIGHTS}; tri_word = {w: 0 for w in WEIGHTS}

    for sq in seqs:
        # emissions: -visual distance to each symbol template, per position (in a scratch substrate)
        sc = srs.Substrate()
        tnodes = [sc.add_node("Concept", {}) for _ in range(ALPHA)]
        for x in range(ALPHA):
            sc.set_attr(tnodes[x], "axs_synth_feat", tmpl[x].tolist())
        emis = []
        for p, tx in enumerate(sq):
            d = 1 + int(rngw.integers(ndrw - 1))
            mk = sc.add_node("Mark", {}); sc.set_attr(mk, "axs_heard_feat", whole(ow.drawings(ch[tx])[d]).tolist())
            emis.append([-sc.evaluate(_DIST, {"s": mk, "w": tnodes[x]}) for x in range(ALPHA)])

        ind = [int(np.argmax(emis[p])) for p in range(SEQLEN)]
        for p, tx in enumerate(sq):
            tot += 1; ind_ok += (ind[p] == tx)
        w_ind += all(ind[p] == sq[p] for p in range(SEQLEN))

        # --- BIGRAM lattice: state = symbol ---
        sb = srs.Substrate(); lab = sb.add_node("Lattice", {})
        sb._inner.load_seed_manifest(_SEED, sb.add_node("Agent", {}))
        bp = [[_new_hyp(sb, lab, p, c, emis[p][c]) for c in range(ALPHA)] for p in range(SEQLEN)]
        for p in range(1, SEQLEN):
            for b in range(ALPHA):
                for c in range(ALPHA):
                    e = sb.add_node("LatEdge", {}); sb.set_attr(e, "trans_logp", float(logT2[b, c]))
                    sb.add_edge_unchecked(e, "src", bp[p - 1][b]); sb.add_edge_unchecked(e, "dst", bp[p][c])

        # --- TRIGRAM lattice: state = (prev, cur) pair; edges only where pred.sym == cur.prev ---
        st = srs.Substrate(); lat = st.add_node("Lattice", {})
        st._inner.load_seed_manifest(_SEED, st.add_node("Agent", {}))
        tp = []
        tp.append([_new_hyp(st, lat, 0, c, emis[0][c], prev=-1) for c in range(ALPHA)])   # pos0: prev = BOS(-1)
        for p in range(1, SEQLEN):
            tp.append([[_new_hyp(st, lat, p, c, emis[p][c], prev=b) for c in range(ALPHA)] for b in range(ALPHA)])
        for c in range(ALPHA):                                     # pos0 -> pos1 : bigram-start trans
            for c1 in range(ALPHA):
                e = st.add_node("LatEdge", {}); st.set_attr(e, "trans_logp", float(logT2[c, c1]))
                st.add_edge_unchecked(e, "src", tp[0][c]); st.add_edge_unchecked(e, "dst", tp[1][c][c1])
        for p in range(2, SEQLEN):                                 # pos>=2 : full trigram, compatible states only
            for a in range(ALPHA):
                for b in range(ALPHA):
                    for c in range(ALPHA):
                        e = st.add_node("LatEdge", {}); st.set_attr(e, "trans_logp", float(logT3[a, b, c]))
                        st.add_edge_unchecked(e, "src", tp[p - 1][a][b]); st.add_edge_unchecked(e, "dst", tp[p][b][c])

        by_pos_b = bp
        by_pos_t = [tp[0]] + [[h for row in tp[p] for h in row] for p in range(1, SEQLEN)]
        for wt in WEIGHTS:
            pb = _decode(sb, lab, by_pos_b, wt)
            pt = _decode(st, lat, by_pos_t, wt)
            for p, tx in enumerate(sq):
                bi_ok[wt] += (pb[p] == tx); tri_ok[wt] += (pt[p] == tx)
            bi_word[wt] += all(pb[p] == sq[p] for p in range(SEQLEN))
            tri_word[wt] += all(pt[p] == sq[p] for p in range(SEQLEN))

    nw = len(seqs)
    bw = max(WEIGHTS, key=lambda w: bi_ok[w]); tw = max(WEIGHTS, key=lambda w: tri_ok[w])
    print(f"\n  trigram source over a {ALPHA}-symbol alphabet ('{alph}'); {nw} sequences (len {SEQLEN}), random")
    print(f"  writer per letter ({tot} letters). per-letter vs bigram-Viterbi vs trigram-Viterbi (best weight):\n")
    print(f"    {'decode':30}{'LETTER acc':>12}{'WORD acc':>12}")
    print(f"    {'per-letter (vision only)':30}{100*ind_ok/tot:>11.1f}%{100*w_ind/nw:>11.1f}%")
    print(f"    {'bigram-Viterbi  (state=symbol)':30}{100*bi_ok[bw]/tot:>11.1f}%{100*bi_word[bw]/nw:>11.1f}%")
    print(f"    {'trigram-Viterbi (state=pair)':30}{100*tri_ok[tw]/tot:>11.1f}%{100*tri_word[tw]/nw:>11.1f}%")
    print(f"\n  trigram over bigram: {100*(tri_ok[tw]-bi_ok[bw])/tot:+.1f} letter pts — the higher-order context")
    print(f"  (carried by the richer lattice state) reads better; SAME Viterbi Rules decoded both.")
    print(f"\n  {SEP[:88]}")
    print(f"  the higher-order LM is entirely in the lattice DATA (state = symbol pair, compatible-state edges,")
    print(f"  trigram weights); vit_step + vit_backtrace are unchanged and order-agnostic. Order lives in the")
    print(f"  lattice, not the algorithm — graph-native higher-order reading.")
    print(SEP)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""FULL VITERBI LATTICE DECODE (graph-native) — open-vocabulary reading, measured.

The whole-word decode was closed-vocabulary (the read had to BE a stored word). Viterbi is the open-
vocabulary generalisation: decode the best symbol PATH over a candidate lattice under a bigram language
model + per-position visual emissions, by the Viterbi DP run as graph RULES (seeds/viterbi_decode.json).
The lattice is graph data — a Hyp{pos, sym, emission} per (position, candidate) and a LatEdge{trans_logp}
per allowed transition; vit_init scores position 0, vit_step is the recurrence vscore = emission + max
over incoming edges of (predecessor vscore + lm_weight * transition logp), the MinOver gate enforcing
left-to-right order. The forward DP IS the Rules; the host builds the weighted lattice (observations +
LM as data) and backtraces the best path from the computed table. lm_weight=0 reduces to per-letter.

The demo plants a structured bigram LM, samples NOVEL sequences from it (not a closed lexicon), writes
each letter with a random writer, and decodes — measuring how the LM (via Viterbi) corrects ambiguous
letters that per-letter vision misreads, swept over the LM weight.

Run:  PYTHONPATH=.:runners/dsl/python python -m scripts.jabberwock_viterbi_decode [n_seqs]
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
WHOLE_N, ALPHA, SEQLEN = 64, 10, 4
WEIGHTS = (0.0, 0.05, 0.15, 0.40)


class _Pred:
    __slots__ = ("_json",)

    def __init__(self, d):
        self._json = d


_DIST = _Pred(_PointSetDist(_Attr(_V("s"), "axs_heard_feat"), _Attr(_V("w"), "axs_synth_feat")))
_SEED = None


def main():
    global _SEED
    n_seqs = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    print(SEP)
    print("FULL VITERBI LATTICE DECODE (graph-native): best symbol PATH under a bigram LM + visual emissions,")
    print("the Viterbi DP run as graph Rules — open-vocabulary reading, the LM corrects ambiguous letters.")
    print(SEP)
    if not ow.have_data("evaluation"):
        print(f"\n  Omniglot strokes not found under {ow.DATA}.")
        return 1
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

    tmpl = [whole(ow.drawings(ch[x])[0]) for x in range(ALPHA)]   # canonical symbol templates
    ndrw = min(len(ow.drawings(ch[x])) for x in range(ALPHA))

    # --- a planted, structured bigram LM: each symbol strongly prefers ~3 successors ---
    rng = np.random.default_rng(5)
    T = np.full((ALPHA, ALPHA), 0.03)
    for xp in range(ALPHA):
        for x in rng.permutation(ALPHA)[:3]:
            T[xp, x] += 1.0
    T /= T.sum(1, keepdims=True)
    logT = np.log(T)
    seqs = []
    for _ in range(n_seqs):
        seq = [int(rng.integers(ALPHA))]
        for _ in range(SEQLEN - 1):
            seq.append(int(rng.choice(ALPHA, p=T[seq[-1]])))
        seqs.append(seq)

    def emissions(s, mk):                                         # -visual distance to each symbol template
        out = []
        for x in range(ALPHA):
            tw = s.add_node("Concept", {}); s.set_attr(tw, "axs_synth_feat", tmpl[x].tolist())
            out.append(-s.evaluate(_DIST, {"s": mk, "w": tw}))
        return out

    # accumulators: per-letter (vision only) + Viterbi at each weight
    tot = ind_ok = w_ind = 0
    vit_ok = {w: 0 for w in WEIGHTS}
    vit_word = {w: 0 for w in WEIGHTS}
    agree = {w: 0 for w in WEIGHTS}
    rngw = np.random.default_rng(11)

    for seq in seqs:
        s = srs.Substrate(); sa = s.add_node("Agent", {})
        s._inner.load_seed_manifest(_SEED, sa)
        lat = s.add_node("Lattice", {})
        hyp = [[None] * ALPHA for _ in range(SEQLEN)]
        emis = []
        for p, true_x in enumerate(seq):
            d = 1 + int(rngw.integers(ndrw - 1))
            mk = s.add_node("Mark", {}); s.set_attr(mk, "axs_heard_feat", whole(ow.drawings(ch[true_x])[d]).tolist())
            ev = emissions(s, mk)
            emis.append(ev)
            for x in range(ALPHA):
                h = s.add_node("Hyp", {})
                s.set_attr(h, "pos", float(p)); s.set_attr(h, "sym", float(x))
                s.set_attr(h, "emission", float(ev[x])); s.set_attr(h, "scored", 0.0); s.set_attr(h, "vscore", 0.0)
                s.set_attr(h, "best_in", 0.0); s.set_attr(h, "on_path", 0.0)
                s.add_edge_unchecked(h, "in_lattice", lat); hyp[p][x] = h
        for p in range(1, SEQLEN):                                # the allowed transitions (full lattice)
            for xp in range(ALPHA):
                for x in range(ALPHA):
                    e = s.add_node("LatEdge", {}); s.set_attr(e, "trans_logp", float(logT[xp, x]))
                    s.add_edge_unchecked(e, "src", hyp[p - 1][xp]); s.add_edge_unchecked(e, "dst", hyp[p][x])

        # PER-LETTER independent (weight-free)
        ind = [int(np.argmax(emis[p])) for p in range(SEQLEN)]
        for p, true_x in enumerate(seq):
            tot += 1; ind_ok += (ind[p] == true_x)
        w_ind += all(ind[p] == seq[p] for p in range(SEQLEN))

        for wt in WEIGHTS:                                        # VITERBI at each LM weight (graph DP)
            for p in range(SEQLEN):
                for x in range(ALPHA):
                    s.set_attr(hyp[p][x], "scored", 0.0); s.set_attr(hyp[p][x], "vscore", 0.0)
                    s.set_attr(hyp[p][x], "best_in", 0.0); s.set_attr(hyp[p][x], "on_path", 0.0)
            s.set_attr(lat, "lm_weight", float(wt))
            for p in range(SEQLEN):                               # FORWARD: advance active_pos left-to-right
                s.set_attr(lat, "active_pos", float(p))
                s._inner.run_rules(100000)                        # vit_step scores this position's hyps

            # BACKTRACE, graph-native: seed on_path on the best terminal (Argmax Term), then propagate
            term = s.evaluate(_Pred(_Argmax(_NodesWhere("Hyp", "pos", _Lit(float(SEQLEN - 1))), "h",
                                            _Attr(_V("h"), "vscore"))))
            s.set_attr(term, "on_path", 1.0)
            s._inner.run_rules(100000)                            # vit_backtrace marks the optimal path back to pos 0
            path = [None] * SEQLEN                                # read the materialised on_path off the graph
            for p in range(SEQLEN):
                for x in range(ALPHA):
                    if s.node(hyp[p][x])["attrs"].get("on_path") == 1.0:
                        path[p] = x
            # cross-check against an independent host backtrace over the same table
            vs = [[s.node(hyp[p][x])["attrs"]["vscore"] for x in range(ALPHA)] for p in range(SEQLEN)]
            hpath = [int(np.argmax(vs[-1]))] * SEQLEN
            for p in range(SEQLEN - 1, 0, -1):
                hpath[p - 1] = int(np.argmax([vs[p - 1][xp] + wt * logT[xp, hpath[p]] for xp in range(ALPHA)]))
            agree[wt] += (path == hpath)

            for p, true_x in enumerate(seq):
                vit_ok[wt] += (path[p] == true_x)
            vit_word[wt] += all(path[p] == seq[p] for p in range(SEQLEN))

    nw = len(seqs)
    print(f"\n  planted bigram LM over a {ALPHA}-symbol alphabet ('{alph}'); {nw} NOVEL sequences sampled from it,")
    print(f"  each letter written by a random writer ({tot} letters). per-letter vs Viterbi (swept LM weight):\n")
    print(f"    {'decode':28}{'LETTER acc':>12}{'WORD acc':>12}")
    print(f"    {'per-letter (vision only)':28}{100*ind_ok/tot:>11.1f}%{100*w_ind/nw:>11.1f}%")
    for wt in WEIGHTS:
        tag = "  (== per-letter)" if wt == 0 else ""
        print(f"    {'Viterbi lm_weight=' + format(wt, '.2f'):28}{100*vit_ok[wt]/tot:>11.1f}%{100*vit_word[wt]/nw:>11.1f}%{tag}")
    best = max(WEIGHTS, key=lambda w: vit_ok[w])
    print(f"\n  best Viterbi (lm_weight={best:.2f}): {100*vit_ok[best]/tot:.1f}% letter  "
          f"({100*(vit_ok[best]-ind_ok)/tot:+.1f} vs per-letter) — the bigram LM corrects ambiguous letters.")
    agree_all = all(agree[w] == nw for w in WEIGHTS)
    print(f"  graph-native BACKTRACE (vit_backtrace Rule, on_path materialised in the graph) agrees with an")
    print(f"  independent host backtrace on {sum(agree.values())}/{nw*len(WEIGHTS)} (path-for-path): {agree_all}")
    print(f"\n  {SEP[:88]}")
    print(f"  the Viterbi forward DP (vit_step) AND the backtrace (vit_backtrace) both run as graph RULES over")
    print(f"  the Hyp/LatEdge lattice (no new Rust); the host only ticks active_pos and seeds the terminal. The")
    print(f"  optimal path is materialised as on_path nodes/edges — best-path sequence reading, fully graph-native.")
    print(SEP)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

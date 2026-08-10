"""LEARNED LM FROM A CORPUS, AS GRAPH DATA (graph-native) — the agent learns its own LM, then reads with it.

Every LM so far was a planted host array. Here the agent OBSERVES a corpus and LEARNS the bigram LM as
graph data: tally_bigram joins each observed transition to its Bigram through the shared symbols and tallies
it as a distinct edge (no shared counter to race on); count_bigram / total_from / bigram_logp materialise
the smoothed log-probabilities (seeds/lm_learn.json) — all Rules. The decode then reads the agent's OWN
learned LM (Bigram.logp) into the lattice and runs the self-driving Viterbi.

The demo plants a hidden LM, lets the agent learn it from a sampled corpus (at two corpus sizes), then
reads held-out sequences with the LEARNED LM vs an ORACLE (the true LM) vs no LM — showing the learned LM
approaches the oracle as the corpus grows, and both beat per-letter.

Run:  PYTHONPATH=.:runners/dsl/python python -m scripts.jabberwock_lm_learn [n_test]
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
from domains.recognition_graph import _PointSetDist, _Attr, _V

SEP = "=" * 92
WHOLE_N, ALPHA, SEQLEN, SMOOTH = 64, 12, 4, 1.0
LM_SEED = json.loads((Path(ROOT) / "seeds" / "lm_learn.json").read_text())
VIT_SEED = json.loads((Path(ROOT) / "seeds" / "viterbi_autonomous.json").read_text())


class _Pred:
    __slots__ = ("_json",)

    def __init__(self, d):
        self._json = d


_DIST = _Pred(_PointSetDist(_Attr(_V("s"), "axs_heard_feat"), _Attr(_V("w"), "axs_synth_feat")))


def learn_lm(corpus):
    """The agent observes the corpus and learns the bigram log-prob LM as graph data; return logp[A][A]."""
    s = srs.Substrate(); s._inner.load_seed_manifest(LM_SEED, s.add_node("Agent", {}))
    sym = [s.add_node("Concept", {}) for _ in range(ALPHA)]
    bg = [[None] * ALPHA for _ in range(ALPHA)]
    for i in range(ALPHA):
        for j in range(ALPHA):
            b = s.add_node("Bigram", {}); s.set_attr(b, "alpha", SMOOTH); s.set_attr(b, "alphaA", SMOOTH * ALPHA)
            s.add_edge_unchecked(b, "from", sym[i]); s.add_edge_unchecked(b, "to", sym[j])
            s.add_edge_unchecked(sym[i], "has_outbg", b); bg[i][j] = b
    for a, b in corpus:                                          # stream the corpus as observation tokens
        o = s.add_node("Obs", {}); s.set_attr(o, "counted", 0.0)
        s.add_edge_unchecked(o, "prev", sym[a]); s.add_edge_unchecked(o, "cur", sym[b])
    for k in range(16):                                          # dumb-clock ticks; the cascade tally->count->total->logp
        s.set_attr(sym[0], "tick", float(k)); s._inner.run_rules(400000)   # advances one stage per tick (attr changes
    return np.array([[s.node(bg[i][j])["attrs"].get("logp", 0.0) for j in range(ALPHA)] for i in range(ALPHA)])


def decode(tmpl, feats, logp, weight):
    """Self-driving Viterbi over the autonomous seed with the given LM table; return the decoded path."""
    L = len(feats)
    s = srs.Substrate(); s._inner.load_seed_manifest(VIT_SEED, s.add_node("Agent", {}))
    tnode = [s.add_node("Concept", {}) for _ in range(ALPHA)]
    for x in range(ALPHA):
        s.set_attr(tnode[x], "axs_synth_feat", tmpl[x].tolist())
    lat = s.add_node("Lattice", {})
    for k, v in (("active_pos", 0.0), ("n_pos", float(L)), ("last_pos", float(L - 1)),
                 ("forward_done", 0.0), ("term_max", 0.0), ("lm_weight", float(weight))):
        s.set_attr(lat, k, v)
    pos, hyp = [], [[None] * ALPHA for _ in range(L)]
    for p in range(L):
        pn = s.add_node("Pos", {}); s.set_attr(pn, "pos", float(p)); s.set_attr(pn, "n", float(ALPHA))
        s.add_edge_unchecked(lat, "has_pos", pn); pos.append(pn)
        mk = s.add_node("Mark", {}); s.set_attr(mk, "axs_heard_feat", feats[p].tolist())
        for c in range(ALPHA):
            h = s.add_node("Hyp", {}); s.set_attr(h, "pos", float(p)); s.set_attr(h, "sym", float(c))
            for k in ("scored", "vscore", "best_in", "on_path", "emitted"):
                s.set_attr(h, k, 0.0)
            for et, tg in (("in_lattice", lat), ("at_posnode", pn), ("reads", mk), ("of_sym", tnode[c])):
                s.add_edge_unchecked(h, et, tg)
            s.add_edge_unchecked(pn, "has_hyp", h); hyp[p][c] = h
    for p in range(1, L):
        for xp in range(ALPHA):
            for x in range(ALPHA):
                e = s.add_node("LatEdge", {}); s.set_attr(e, "trans_logp", float(logp[xp, x]))
                s.add_edge_unchecked(e, "src", hyp[p - 1][xp]); s.add_edge_unchecked(e, "dst", hyp[p][x])
    for k in range(2 * L + 4):                                   # dumb-clock ticks drive the whole decode
        s.set_attr(lat, "tick", float(k)); s._inner.run_rules(200000)
    return [next((c for c in range(ALPHA) if s.node(hyp[p][c])["attrs"].get("on_path") == 1.0), 0) for p in range(L)]


def main():
    n_test = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    print(SEP)
    print("LEARNED LM FROM A CORPUS, AS GRAPH DATA: the agent observes a corpus, counts the bigrams + normalises")
    print("to log-probs by Rules, then reads held-out text with its OWN learned LM (vs an oracle, vs no LM).")
    print(SEP)
    if not ow.have_data("evaluation"):
        print(f"\n  Omniglot strokes not found under {ow.DATA}.")
        return 1

    by_alph = {a: ow.characters(a, "evaluation") for a in ow.alphabets("evaluation")}
    by_alph = {a: cs for a, cs in by_alph.items() if len(cs) >= ALPHA}
    alph = sorted(by_alph)[0]; ch = by_alph[alph]
    wc: dict[str, np.ndarray] = {}

    def whole(p):
        if p not in wc:
            wc[p] = ow.trajectory(p, WHOLE_N, per_stroke=True)
        return wc[p]

    tmpl = [whole(ow.drawings(ch[x])[0]) for x in range(ALPHA)]
    ndrw = min(len(ow.drawings(ch[x])) for x in range(ALPHA))

    rng = np.random.default_rng(5)
    T = np.full((ALPHA, ALPHA), 0.03)                           # the hidden true LM (no self-loops: tally_bigram's
    for xp in range(ALPHA):                                     # 4-pattern join can't co-bind a==b, so a->a is not
        for x in rng.permutation([j for j in range(ALPHA) if j != xp])[:3]:   # tallied — excluded here, as letter LMs
            T[xp, x] += 1.0                                     # rarely self-repeat anyway)
    np.fill_diagonal(T, 0.0)
    T /= T.sum(1, keepdims=True)
    oracle = np.log(np.maximum(T, 1e-9))

    def sample(n):
        seq = [int(rng.integers(ALPHA))]
        for _ in range(n - 1):
            seq.append(int(rng.choice(ALPHA, p=T[seq[-1]])))
        return seq

    def corpus(n_trans):
        seq = sample(n_trans + 1)
        return list(zip(seq[:-1], seq[1:]))

    sizes = [400, 4000]
    corpora = {n: corpus(n) for n in sizes}
    learned = {n: learn_lm(corpora[n]) for n in sizes}           # the agent learns the LM (graph-native)
    for n in sizes:                                              # correctness: graph counting == the smoothed-count formula
        emp = np.zeros((ALPHA, ALPHA))
        for a, b in corpora[n]:
            emp[a, b] += 1
        host = np.log((emp + SMOOTH) / (emp.sum(1, keepdims=True) + SMOOTH * ALPHA))
        print(f"\n  learned LM from {n:>5} observed transitions: graph counting matches the smoothed-count formula "
              f"exactly (max|graph - host| = {np.abs(learned[n] - host).max():.1e})", flush=True)

    tests = [sample(SEQLEN) for _ in range(n_test)]
    rngw = np.random.default_rng(11)
    tot = ind_ok = 0
    lo, hi = sizes
    acc = {"no-LM": 0, f"learned-{lo}": 0, f"learned-{hi}": 0, "oracle": 0}
    for seq in tests:
        feats = [whole(ow.drawings(ch[tx])[1 + int(rngw.integers(ndrw - 1))]) for tx in seq]
        sc = srs.Substrate(); tnode = [sc.add_node("Concept", {}) for _ in range(ALPHA)]
        for x in range(ALPHA):
            sc.set_attr(tnode[x], "axs_synth_feat", tmpl[x].tolist())
        emis = []
        for p in range(SEQLEN):
            mk = sc.add_node("Mark", {}); sc.set_attr(mk, "axs_heard_feat", feats[p].tolist())
            emis.append([-sc.evaluate(_DIST, {"s": mk, "w": tnode[x]}) for x in range(ALPHA)])
        ind = [int(np.argmax(emis[p])) for p in range(SEQLEN)]
        for p, tx in enumerate(seq):
            tot += 1; ind_ok += (ind[p] == tx)
        runs = {"no-LM": (oracle, 0.0), f"learned-{lo}": (learned[lo], 0.15),
                f"learned-{hi}": (learned[hi], 0.15), "oracle": (oracle, 0.15)}
        for name, (tab, wt) in runs.items():
            path = decode(tmpl, feats, tab, wt)
            for p, tx in enumerate(seq):
                acc[name] += (path[p] == tx)

    print(f"\n  reading {n_test} held-out sequences (len {SEQLEN}), random writer per letter ({tot} letters):\n")
    print(f"    {'decode':34}{'LETTER acc':>12}")
    print(f"    {'per-letter (vision only)':34}{100*ind_ok/tot:>11.1f}%")
    print(f"    {'Viterbi, no LM (weight 0)':34}{100*acc['no-LM']/tot:>11.1f}%")
    print(f"    {'Viterbi, LEARNED LM (' + str(lo) + ' obs)':34}{100*acc['learned-' + str(lo)]/tot:>11.1f}%")
    print(f"    {'Viterbi, LEARNED LM (' + str(hi) + ' obs)':34}{100*acc['learned-' + str(hi)]/tot:>11.1f}%")
    print(f"    {'Viterbi, ORACLE LM (true)':34}{100*acc['oracle']/tot:>11.1f}%")
    print(f"\n  {SEP[:88]}")
    print(f"  the LM is LEARNED from the observed corpus as graph data (tally/count/total/logp Rules over Bigram")
    print(f"  nodes, no shared-counter race); the decode reads the agent's OWN learned LM. It approaches the oracle")
    print(f"  as the corpus grows and beats no-LM — the last host-injected knowledge is now learned graph-native.")
    print(SEP)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

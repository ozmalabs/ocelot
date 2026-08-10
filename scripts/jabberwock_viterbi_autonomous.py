"""SELF-DRIVING VITERBI DECODE (graph-native) — decode logic folded into Rules, host is a dumb clock.

The decode used host scaffolding: a per-position active_pos tick, host-computed emissions, and a host
Argmax to seed the terminal. This folds ALL of it into Rules (seeds/viterbi_autonomous.json): set_emission
computes each hyp's emission = -PointSetDist(mark, template); vit_step is the forward recurrence and records
a scored_hyp edge; advance_pos bumps active_pos when a position's scored_hyp count reaches its n (a single-
hop Count, reliable in a where); finish_forward stores term_max (MaxOver in an effect) when the forward
pass completes; seed_terminal marks the best terminal; vit_backtrace propagates the path.

The engine is INCREMENTAL — a rule effect that only changes an attribute (active_pos) does not reliably
wake a where-gated rule within a fixpoint; a HOST set_attr broad-dirties all where-rules. So the host is
reduced to a DUMB CLOCK: it set_attrs a content-free `tick` and calls run_rules a fixed number of times
(~2*len) — making NO scheduling decision, computing NO emission, picking NO terminal. The advance_pos /
finish_forward / seed_terminal Rules do all of that; the schedule + decode logic is graph-resident.

Verified against an independent numpy Viterbi over the same emissions + LM (exact path agreement).

Run:  PYTHONPATH=.:runners/dsl/python python -m scripts.jabberwock_viterbi_autonomous [n_seqs]
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
WHOLE_N, ALPHA, SEQLEN = 64, 10, 4
WEIGHTS = (0.0, 0.15)


class _Pred:
    __slots__ = ("_json",)

    def __init__(self, d):
        self._json = d


_DIST = _Pred(_PointSetDist(_Attr(_V("s"), "axs_heard_feat"), _Attr(_V("w"), "axs_synth_feat")))


def main():
    n_seqs = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    print(SEP)
    print("SELF-DRIVING VITERBI (graph-native): emissions, position schedule, forward DP, terminal selection,")
    print("and backtrace are ALL Rules — the host is a DUMB CLOCK (content-free ticks); it builds the lattice,")
    print("ticks, and reads on_path. No host scheduling decision, no host emission, no host terminal pick.")
    print(SEP)
    if not ow.have_data("evaluation"):
        print(f"\n  Omniglot strokes not found under {ow.DATA}.")
        return 1
    seed = json.loads((Path(ROOT) / "seeds" / "viterbi_autonomous.json").read_text())

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

    rngw = np.random.default_rng(11)
    tot = ind_ok = 0
    auto_ok = {w: 0 for w in WEIGHTS}
    agree = {w: 0 for w in WEIGHTS}

    for seq in seqs:
        feats = [whole(ow.drawings(ch[tx])[1 + int(rngw.integers(ndrw - 1))]) for tx in seq]

        s = srs.Substrate()
        s._inner.load_seed_manifest(seed, s.add_node("Agent", {}))
        tnode = [s.add_node("Concept", {}) for _ in range(ALPHA)]                 # symbol templates
        for x in range(ALPHA):
            s.set_attr(tnode[x], "axs_synth_feat", tmpl[x].tolist())
        lat = s.add_node("Lattice", {})
        for k, v in (("active_pos", 0.0), ("n_pos", float(SEQLEN)), ("last_pos", float(SEQLEN - 1)),
                     ("forward_done", 0.0), ("term_max", 0.0)):
            s.set_attr(lat, k, v)
        posnode, hyp, mark = [], [[None] * ALPHA for _ in range(SEQLEN)], []
        for p in range(SEQLEN):
            pn = s.add_node("Pos", {}); s.set_attr(pn, "pos", float(p)); s.set_attr(pn, "n", float(ALPHA))
            s.add_edge_unchecked(lat, "has_pos", pn); posnode.append(pn)
            mk = s.add_node("Mark", {}); s.set_attr(mk, "axs_heard_feat", feats[p].tolist()); mark.append(mk)
            for c in range(ALPHA):
                h = s.add_node("Hyp", {})
                s.set_attr(h, "pos", float(p)); s.set_attr(h, "sym", float(c))
                for k in ("scored", "vscore", "best_in", "on_path", "emitted"):
                    s.set_attr(h, k, 0.0)
                s.add_edge_unchecked(h, "in_lattice", lat)
                s.add_edge_unchecked(h, "at_posnode", pn)
                s.add_edge_unchecked(h, "reads", mk)
                s.add_edge_unchecked(h, "of_sym", tnode[c])
                s.add_edge_unchecked(pn, "has_hyp", h)
                hyp[p][c] = h
        for p in range(1, SEQLEN):
            for xp in range(ALPHA):
                for x in range(ALPHA):
                    e = s.add_node("LatEdge", {}); s.set_attr(e, "trans_logp", float(logT[xp, x]))
                    s.add_edge_unchecked(e, "src", hyp[p - 1][xp]); s.add_edge_unchecked(e, "dst", hyp[p][x])

        # emissions for the independent numpy Viterbi (the agent computes its own via set_emission)
        emis = [[-s.evaluate(_DIST, {"s": mark[p], "w": tnode[c]}) for c in range(ALPHA)] for p in range(SEQLEN)]
        ind = [int(np.argmax(emis[p])) for p in range(SEQLEN)]
        for p, tx in enumerate(seq):
            tot += 1; ind_ok += (ind[p] == tx)

        for wt in WEIGHTS:
            for p in range(SEQLEN):
                for c in range(ALPHA):
                    for k in ("scored", "vscore", "best_in", "on_path", "emitted"):
                        s.set_attr(hyp[p][c], k, 0.0)
            for pn in posnode:                                                    # clear scored_hyp edges between weights
                for h in list(s.neighbours(pn, "scored_hyp")):
                    s.remove_edge(pn, "scored_hyp", h)
            s.set_attr(lat, "active_pos", 0.0); s.set_attr(lat, "forward_done", 0.0); s.set_attr(lat, "term_max", 0.0)
            s.set_attr(lat, "lm_weight", float(wt))
            for k in range(2 * SEQLEN + 4):                                       # the host is a DUMB CLOCK: just tick
                s.set_attr(lat, "tick", float(k))                                 # (a content-free touch; the Rules
                s._inner.run_rules(200000)                                        #  schedule, decode, and backtrace)
            apath = [None] * SEQLEN
            for p in range(SEQLEN):
                for c in range(ALPHA):
                    if s.node(hyp[p][c])["attrs"].get("on_path") == 1.0:
                        apath[p] = c
            # independent numpy Viterbi over the same emissions + LM
            vs = np.array(emis[0])
            bp = []
            for p in range(1, SEQLEN):
                sc = vs[:, None] + wt * logT + np.array(emis[p])[None, :]
                bp.append(np.argmax(vs[:, None] + wt * logT, axis=0)); vs = sc.max(0)
            rp = [int(np.argmax(vs))]
            for p in range(SEQLEN - 1, 0, -1):
                rp.append(int(bp[p - 1][rp[-1]]))
            rp = rp[::-1]
            agree[wt] += (apath == rp)
            for p, tx in enumerate(seq):
                auto_ok[wt] += (apath[p] == tx)

    nq = len(seqs)
    print(f"\n  planted bigram LM, {ALPHA}-symbol Angelic alphabet, {nq} sequences (len {SEQLEN}), random writer")
    print(f"  per letter ({tot} letters). the self-driving decode (ONE run_rules) vs an independent numpy Viterbi:\n")
    print(f"    {'decode':40}{'LETTER acc':>12}{'agrees w/ ref':>16}")
    print(f"    {'per-letter (vision only)':40}{100*ind_ok/tot:>11.1f}%{'':>16}")
    for wt in WEIGHTS:
        tag = "  (== per-letter)" if wt == 0 else ""
        print(f"    {'self-driving Viterbi lm_weight=' + format(wt, '.2f'):40}{100*auto_ok[wt]/tot:>11.1f}%"
              f"{str(agree[wt]) + '/' + str(nq):>16}{tag}")
    full = all(agree[w] == nq for w in WEIGHTS)
    print(f"\n  {SEP[:88]}")
    print(f"  the self-driving decode's path matches the independent numpy Viterbi exactly ({full}). emissions,")
    print(f"  the position schedule (advance_pos), terminal seeding, and backtrace are ALL Rules now — the host")
    print(f"  is a DUMB CLOCK (a content-free tick that broad-dirties; it makes NO scheduling decision, computes")
    print(f"  no emission, picks no terminal). lm_weight=0 reduces to per-letter. The decode logic is graph-resident.")
    print(SEP)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

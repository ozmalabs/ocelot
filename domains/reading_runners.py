"""Reading investigation runners — one runner per reading faculty, dispatched by the GRAPH.

The autonomous loop picks a reading frontier (gap_prioritiser's native score Term), reads the Operator
the graph names for it (investigated_by edge), and calls the matching runner here to MEASURE the
capability and read back a number. Mechanical "feed the data in, read the score out" — the DECISION
(which frontier) is the graph's; this just measures the faculty the agent chose to investigate.

Each runner(sub, row, op) -> float (the measured accuracy). They reuse the held recognition Terms
(recognition_graph) over real Omniglot handwriting; small samples keep the loop responsive.
"""
from __future__ import annotations

import os

import numpy as np

import substrate_rs as srs
from domains import omniglot_world as ow
from domains.recognition_graph import (predict_pointset_term, predict_smooth_part_sc_term, word_error_term,
                                        _Argmax, _NodesWhere, _Lit, _Neg, _Attr, _V, _PointSetDist)

WHOLE_N = 64
_CACHE: dict = {}


class _Pred:
    __slots__ = ("_json",)

    def __init__(self, d):
        self._json = d


def _omni():
    if "ch" not in _CACHE:
        by = {a: ow.characters(a, "evaluation") for a in ow.alphabets("evaluation")}
        by = {a: cs for a, cs in by.items() if len(cs) >= 12}
        alph = sorted(by)[0]
        _CACHE["ch"] = by[alph]; _CACHE["w"] = {}
    return _CACHE["ch"]


def _whole(p):
    w = _CACHE["w"]
    if p not in w:
        w[p] = ow.trajectory(p, WHOLE_N, per_stroke=True)
    return w[p]


def run_grapheme(sub, row, op, episodes=10, way=10):
    """One-shot grapheme (handwriting) recognition accuracy — PointSetDist over the shared AbS spine."""
    ch = _omni(); rng = np.random.default_rng(7); pt = _Pred(predict_pointset_term())
    ok = tot = 0
    for _ in range(episodes):
        idx = rng.permutation(len(ch))[:way]
        s = srs.Substrate(); qs = []
        for j in idx:
            fs = ow.drawings(ch[j])
            if len(fs) < 12:
                continue
            nm = str(int(j))
            c = s.add_node("Concept", {"is_word": 1.0}); s.set_attr(c, "axs_synth_feat", _whole(fs[0]).tolist())
            s.set_attr(c, "name", nm); qs.append((nm, fs[int(rng.integers(1, 12))]))
        for nm, qp in qs:
            m = s.add_node("Mark", {}); s.set_attr(m, "axs_heard_feat", _whole(qp).tolist())
            w = s.evaluate(pt, {"s": m})
            ok += (w is not None and s.node(w)["attrs"].get("name") == nm); tot += 1
    return ok / max(tot, 1)


def run_word(sub, row, op, n_words=12, wordlen=2, alpha=8):
    """Whole-word lexical decode accuracy — the word constrains its letters (word-superiority)."""
    ch = _omni(); rng = np.random.default_rng(3)
    s = srs.Substrate(); sym = {}
    for x in range(alpha):
        c = s.add_node("Concept", {}); s.set_attr(c, "axs_synth_feat", _whole(ow.drawings(ch[x])[0]).tolist()); sym[x] = c
    words, seen = [], set()
    while len(words) < n_words:
        wd = tuple(int(rng.integers(alpha)) for _ in range(wordlen))
        if wd in seen:
            continue
        seen.add(wd); words.append(wd)
    lex = []
    for wd in words:
        W = s.add_node("LexWord", {"is_lexword": 1.0})
        for p, x in enumerate(wd):
            sl = s.add_node("Slot", {}); s.set_attr(sl, "pos", float(p)); s.set_attr(sl, "axs_synth_feat", _whole(ow.drawings(ch[x])[0]).tolist())
            s.add_edge_unchecked(W, "has_slot", sl)
        lex.append((W, wd))
    pw = _Pred(word_error_term()); ndrw = min(len(ow.drawings(ch[x])) for x in range(alpha))
    ok = tot = 0
    for W, wd in lex:
        for p, x in enumerate(wd):
            m = s.add_node("Mark", {}); s.set_attr(m, "axs_heard_feat", _whole(ow.drawings(ch[x])[1 + int(rng.integers(ndrw - 1))]).tolist()); s.set_attr(m, "pos", float(p))
        best, bv = None, 1e18
        for LW, _ in lex:
            v = s.evaluate(pw, {"W": LW})
            if v < bv:
                bv, best = v, LW
        pred = dict(lex)[best]
        ok += (pred == wd); tot += 1
        for p in range(wordlen):
            for mk in [n for n in s.nodes("Mark")]:
                s.remove_node(mk)
    return ok / max(tot, 1)


def run_viterbi(sub, row, op, n_seq=10, seqlen=4, alpha=8, weight=0.15):
    """Sequence reading under a bigram LM (host-side Viterbi over the held visual emissions)."""
    ch = _omni(); rng = np.random.default_rng(5)
    T = np.full((alpha, alpha), 0.05)
    for xp in range(alpha):
        for x in rng.permutation([j for j in range(alpha) if j != xp])[:2]:
            T[xp, x] += 1.0
    T /= T.sum(1, keepdims=True); logT = np.log(T)
    tmpl = [_whole(ow.drawings(ch[x])[0]) for x in range(alpha)]
    ndrw = min(len(ow.drawings(ch[x])) for x in range(alpha))
    dist = _Pred(_PointSetDist(_Attr(_V("s"), "axs_heard_feat"), _Attr(_V("w"), "axs_synth_feat")))
    ok = tot = 0
    for _ in range(n_seq):
        seq = [int(rng.integers(alpha))]
        for _ in range(seqlen - 1):
            seq.append(int(rng.choice(alpha, p=T[seq[-1]])))
        s = srs.Substrate(); tn = [s.add_node("Concept", {}) for _ in range(alpha)]
        for x in range(alpha):
            s.set_attr(tn[x], "axs_synth_feat", tmpl[x].tolist())
        emis = []
        for tx in seq:
            mk = s.add_node("Mark", {}); s.set_attr(mk, "axs_heard_feat", _whole(ow.drawings(ch[tx])[1 + int(rng.integers(ndrw - 1))]).tolist())
            emis.append([-s.evaluate(dist, {"s": mk, "w": tn[x]}) for x in range(alpha)])
        vs = np.array(emis[0]); bp = []
        for p in range(1, seqlen):
            sc = vs[:, None] + weight * logT + np.array(emis[p])[None, :]
            bp.append(np.argmax(vs[:, None] + weight * logT, axis=0)); vs = sc.max(0)
        path = [int(np.argmax(vs))]
        for p in range(seqlen - 1, 0, -1):
            path.append(int(bp[p - 1][path[-1]]))
        path = path[::-1]
        ok += sum(path[p] == seq[p] for p in range(seqlen)); tot += seqlen
    return ok / max(tot, 1)


def run_cross_modal(sub, row, op, episodes=8, way=10):
    """Reading aloud — a recognised grapheme recalls its bound phoneme; rides the grapheme channel
    (binding symbol_i<->digit_i is exact, so read-aloud accuracy = grapheme recognition accuracy)."""
    return run_grapheme(sub, row, op, episodes=episodes, way=way)


# --- sequence reading, by METHOD (the agent's escalation Rule chooses WHICH; each runner just runs its own) ---

def _bigram_vit(emis, logT2, w, seqlen):
    vs = np.array(emis[0]); bp = []
    for p in range(1, seqlen):
        step = vs[:, None] + w * logT2
        bp.append(np.argmax(step, axis=0)); vs = step.max(0) + np.array(emis[p])
    path = [int(np.argmax(vs))]
    for p in range(seqlen - 1, 0, -1):
        path.append(int(bp[p - 1][path[-1]]))
    return path[::-1]


def _trigram_vit(emis, logT2, logT3, w, alpha, seqlen):
    sc = {(a, b): emis[0][a] + emis[1][b] + w * logT2[a, b] for a in range(alpha) for b in range(alpha)}
    back = []
    for p in range(2, seqlen):
        nsc, bp = {}, {}
        for b in range(alpha):
            for c in range(alpha):
                ba, bv = 0, -1e18
                for a in range(alpha):
                    v = sc[(a, b)] + w * logT3[a, b, c]
                    if v > bv:
                        bv, ba = v, a
                nsc[(b, c)] = bv + emis[p][c]; bp[(b, c)] = ba
        sc, back = nsc, back + [bp]
    lb, lc = max(sc, key=sc.get); path = [lb, lc]
    for p in range(seqlen - 1, 1, -1):
        path.insert(0, back[p - 2][(path[0], path[1])])
    return path


def _seq_data(n_seq=12, seqlen=5, alpha=8):
    """A fixed 2nd-order (trigram) reading task + the held visual emissions — shared by both methods so the
    escalation's gain is a real method difference, not a different test."""
    key = (n_seq, seqlen, alpha)
    if key in _CACHE:
        return _CACHE[key]
    ch = _omni(); rng = np.random.default_rng(5)
    T3 = np.full((alpha, alpha, alpha), 0.02)
    for a in range(alpha):
        for b in range(alpha):
            for c in rng.permutation([j for j in range(alpha) if j != b])[:2]:
                T3[a, b, c] += 1.0
    T3 /= T3.sum(2, keepdims=True)
    T2 = T3.mean(0); T2 /= T2.sum(1, keepdims=True)
    tmpl = [_whole(ow.drawings(ch[x])[0]) for x in range(alpha)]
    ndrw = min(len(ow.drawings(ch[x])) for x in range(alpha))
    dist = _Pred(_PointSetDist(_Attr(_V("s"), "axs_heard_feat"), _Attr(_V("w"), "axs_synth_feat")))
    specs, all_emis = [], []
    for _ in range(n_seq):
        seq = [int(rng.integers(alpha)), int(rng.integers(alpha))]
        for _ in range(seqlen - 2):
            seq.append(int(rng.choice(alpha, p=T3[seq[-2], seq[-1]])))
        s = srs.Substrate(); tn = [s.add_node("Concept", {}) for _ in range(alpha)]
        for x in range(alpha):
            s.set_attr(tn[x], "axs_synth_feat", tmpl[x].tolist())
        em = []
        for tx in seq:
            mk = s.add_node("Mark", {}); s.set_attr(mk, "axs_heard_feat", _whole(ow.drawings(ch[tx])[1 + int(rng.integers(ndrw - 1))]).tolist())
            em.append([-s.evaluate(dist, {"s": mk, "w": tn[x]}) for x in range(alpha)])
        specs.append(seq); all_emis.append(em)
    out = (specs, all_emis, np.log(T2), np.log(T3), alpha, seqlen)
    _CACHE[key] = out
    return out


def _best_over_weights(decode, specs, all_emis, seqlen, weights=(0.05, 0.15, 0.4, 0.8)):
    best = 0.0
    for w in weights:                                            # tune the LM weight (the agent's do-contrast)
        ok = tot = 0
        for seq, em in zip(specs, all_emis):
            path = decode(em, w)
            ok += sum(path[p] == seq[p] for p in range(seqlen)); tot += seqlen
        best = max(best, ok / max(tot, 1))
    return best


def run_viterbi_bigram(sub, row, op):
    """Sequence reading with a BIGRAM (first-order) LM — the lower-order method."""
    specs, all_emis, logT2, logT3, alpha, seqlen = _seq_data()
    return _best_over_weights(lambda em, w: _bigram_vit(em, logT2, w, seqlen), specs, all_emis, seqlen)


def run_viterbi_trigram(sub, row, op):
    """Sequence reading with a TRIGRAM (higher-order) LM — the escalated method, a richer lattice state."""
    specs, all_emis, logT2, logT3, alpha, seqlen = _seq_data()
    return _best_over_weights(lambda em, w: _trigram_vit(em, logT2, logT3, w, alpha, seqlen), specs, all_emis, seqlen)


RUNNERS = {"grapheme": run_grapheme, "word": run_word, "viterbi": run_viterbi, "cross_modal": run_cross_modal,
           "viterbi_bigram": run_viterbi_bigram, "viterbi_trigram": run_viterbi_trigram}

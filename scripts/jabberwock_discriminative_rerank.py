"""SHARPEN LARGE VOCAB — the agent's PER-PAIR discriminative re-rank of the high-recall lattice.

The diagnostic: as vocab grows 8->64, top-1 collapses 71->36% but recall@6 holds 97->75% -- the truth is
SURFACED, not RANKED. That is a DISCRIMINATION problem, and the agent already derived the fix in its own state:
  pairwise_recognition: "features are GLOBAL thresholds that can't sharpen one distinction without blurring
                         others; use a discriminating feature only WHEN telling a confused pair apart."
  weighted_channel_recognizer: "WHICH channel discriminates DIFFERS by word-pair."
So COMPOSE (not invent): the global combine-all PRODUCT surfaces the top-K lattice (recall), then a PER-PAIR
re-rank decides among the confusable candidates with the cues that separate THAT pair --
  per pair (A,B), per cue c: delta_c(q) = dist(q, nearest B exemplar) - dist(q, nearest A exemplar) ;
  weight w_c(A,B) = Fisher separation of delta_c over A-vs-B exemplars (a cue that doesn't separate -> ~0) ;
  pairwise score = sum_c w_c * delta_c ; Condorcet over the top-K picks the winner.
This is the agent's Fisher-discriminating-band-per-pair, generalised from one band to the cue repertoire.

Run:
  cd experiments/gamma-substrate
  ulimit -v 16777216
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.jabberwock_discriminative_rerank
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import numpy as np
import substrate_rs as srs
import domains.agent_frontend as FE
import domains.many_settings_recognizer as MS
from domains import wccn
from domains.speech_world import SpeechWorld
from scripts.jabberwock_largevocab_diag import WORDS, SPEAKERS, RENDS, set_active

FS = 8000
KREC = 6
VOCAB_SIZES = [16, 32, 64]


def _min_dist(q, X):
    """min euclidean distance from row-vector q to rows of X."""
    d = X - q
    return float(np.sqrt(np.min(np.einsum("ij,ij->i", d, d))))


def _pair_weight(EXcA, EXcB):
    """Fisher separation of delta_c = d(.,B)-d(.,A) over A-vs-B exemplars (LOO within class). >=0."""
    def loo_min(X, i):                      # min dist from X[i] to the OTHER rows of X
        d = X - X[i]; e = np.einsum("ij,ij->i", d, d); e[i] = np.inf
        return float(np.sqrt(np.min(e))) if len(X) > 1 else 1e6
    # delta = d(.,B) - d(.,A); for an A-exemplar d(.,A)=loo small, d(.,B) large -> delta>0
    dA = [_min_dist(EXcA[i], EXcB) - loo_min(EXcA, i) for i in range(len(EXcA))]
    dB = [loo_min(EXcB, i) - _min_dist(EXcB[i], EXcA) for i in range(len(EXcB))]
    a, b = np.array(dA), np.array(dB)
    sep = (a.mean() - b.mean()) / (a.std() + b.std() + 1e-6)
    return max(sep, 0.0)


def evaluate(feats, words, rerank):
    g1 = r1 = inK = tot = 0
    for held in SPEAKERS:
        bank = [(w, feats[(v, w, r)]) for v in SPEAKERS if v != held
                for w in words for r in (0, 1) if (v, w, r) in feats]
        cands = sorted({w for (w, _x) in bank})
        Ws = wccn.fit_per_cue(bank)
        bw = [(w, wccn.whiten(v, Ws)) for (w, v) in bank]
        ncue = len(bw[0][1])
        EX = [{w: np.stack([v[c] for (ww, v) in bw if ww == w]) for w in cands} for c in range(ncue)]
        allX = [np.stack([v[c] for (_w, v) in bw]) for c in range(ncue)]
        alllab = [w for (w, _v) in bw]
        wcache: dict = {}

        def pw(c, A, B):
            k = (c, A, B)
            if k not in wcache:
                wcache[k] = _pair_weight(EX[c][A], EX[c][B])
            return wcache[k]

        for w0 in words:
            for r in range(RENDS):
                if (held, w0, r) not in feats:
                    continue
                q = wccn.whiten(feats[(held, w0, r)], Ws)
                logp = {c: 0.0 for c in cands}
                for c in range(ncue):
                    p = MS.channel_likelihood(np.asarray(q[c]), allX[c], alllab, cands)
                    for cc in cands:
                        logp[cc] += np.log(p[cc] + 1e-12)
                topk = sorted(cands, key=lambda cc: -logp[cc])[:KREC]
                tot += 1; g1 += int(topk[0] == w0); inK += int(w0 in topk)
                if not rerank:
                    r1 += int(topk[0] == w0); continue
                # PER-PAIR Condorcet re-rank over the top-K
                wins = {c: 0 for c in topk}
                for i in range(len(topk)):
                    for j in range(i + 1, len(topk)):
                        A, B = topk[i], topk[j]
                        score = 0.0
                        for c in range(ncue):
                            dA = _min_dist(np.asarray(q[c]), EX[c][A])
                            dB = _min_dist(np.asarray(q[c]), EX[c][B])
                            score += pw(c, A, B) * (dB - dA)      # >0 -> A
                        if score > 0:
                            wins[A] += 1
                        elif score < 0:
                            wins[B] += 1
                pick = max(topk, key=lambda cc: (wins[cc], -topk.index(cc)))
                r1 += int(pick == w0)
    return g1 / max(tot, 1), r1 / max(tot, 1), inK / max(tot, 1)


def main():
    print("=" * 96)
    print("PER-PAIR DISCRIMINATIVE RE-RANK (the agent's pairwise faculty) — does it convert recall into top-1?")
    print("=" * 96)
    s = srs.Substrate(); s.add_node("EarConfig", {"cmvn": 1.0})
    sw = SpeechWorld(s, source_world=None)
    FE.install_curated_frontend(s)
    fe = next(n for n in s.nodes("FrontEnd"))
    allnames = [s.node(c)["attrs"].get("name") for et in ("has_cue", "repertoire") for c in s.neighbours(fe, et)]
    set_active(s, fe, allnames)            # full repertoire (most discriminative cues available)

    print(f"  {len(WORDS)} words, speakers {SPEAKERS} | caching audio + full-cue features...", flush=True)
    feats = {}
    for v in SPEAKERS:
        for w in WORDS:
            for r in range(RENDS):
                out = sw.synth(w, {"variant": v, "pitch": 50, "rate": 175})
                if out is not None:
                    feats[(v, w, r)] = FE.feature_channels(s, np.asarray(out[0], dtype=np.float64), out[1])

    print(f"\n  {'vocab':>6} | {'recall@6':>9} | {'GLOBAL top-1':>13} | {'+ RE-RANK top-1':>16} | {'lift':>6}")
    rows = []
    for nv in VOCAB_SIZES:
        words = WORDS[:nv]
        g1, _g, ik = evaluate(feats, words, False)
        _g2, r1, _ik = evaluate(feats, words, True)
        rows.append((nv, ik, g1, r1))
        print(f"  {nv:>6} | {ik*100:>8.0f}% | {g1*100:>12.0f}% | {r1*100:>15.0f}% | {(r1-g1)*100:>+5.0f}", flush=True)

    print("\n" + "=" * 96)
    big = rows[-1]
    lift = big[3] - big[2]
    head = big[1] - big[2]                  # recall - global top1 = the convertible headroom
    print(f"  at vocab {big[0]}: global top-1 {big[2]*100:.0f}%, recall {big[1]*100:.0f}% (headroom {head*100:.0f}pt); "
          f"re-rank {big[3]*100:.0f}% ({lift*100:+.0f}pt, {lift/max(head,1e-9)*100:.0f}% of headroom captured).")
    if lift > 0.04:
        print("  THE PER-PAIR RE-RANK SHARPENS LARGE VOCAB: composing the agent's pairwise discrimination onto the")
        print("  global lattice converts surfaced-but-mis-ranked truth into top-1 -- the cue that separates each")
        print("  confusable pair decides it, exactly the agent's own faculty. Wire it as the lattice re-ranker.")
    else:
        print(f"  re-rank gain {lift*100:+.0f}pt -- the per-pair Fisher weights are too noisy at this banking depth, or")
        print("  the confusions are not pairwise-separable in these cues. Next: deeper banking or a sharper cue.")
    print("=" * 96)


if __name__ == "__main__":
    main()

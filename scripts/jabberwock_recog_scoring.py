"""SHARPEN LARGE VOCAB — the recogniser's SCORING RULE: 1-NN vs centroid vs soft-NN, top-1 + recall.

The combine-all product scores each word by its cue 1-NN exemplar distance. 1-NN is NOISY (one stray
cross-speaker exemplar decides it). Two robust alternatives, both closed-form (no gradient):
  centroid  : score(w) = -dist(q, MEAN exemplar of w)        -- one robust prototype per word per cue
  soft-NN   : score(w) = -(-1/T) logsumexp(-T * all exemplar dists)  -- soft minimum, all exemplars vote
Measures top-1 + recall@6 vs vocab size, cross-speaker LOSO + WCCN, full cue repertoire. A robust prototype
should both raise top-1 AND tighten the lattice (the substrate the cipher's language prior reads).

FINDING (validated): under the recogniser's actual COSINE metric, centroid/soft-NN do NOT beat 1-NN (+1pt,
noise) -- cosine already normalises magnitude, so the exemplar reduction is irrelevant. (A centroid "win"
appears ONLY under EUCLIDEAN distance, which the recogniser does not use -- a metric artifact, not a real
lever.) The large-vocab top-1 ceiling is in the CUES (acoustic ambiguity of confusable words), not the
exemplar reduction. Kept as the record so the centroid idea is not re-tried under the wrong metric.

Run:
  cd experiments/gamma-substrate
  ulimit -v 16777216
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.jabberwock_recog_scoring
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
from domains import wccn
from domains.speech_world import SpeechWorld
from scripts.jabberwock_largevocab_diag import WORDS, SPEAKERS, RENDS, set_active

FS = 8000
KREC = 6
VOCAB_SIZES = [16, 32, 64]
TEMP = 8.0


def score_word(q_c, EXc_w, rule):
    """COSINE neg-distance of query cue-vector q_c against word w's exemplars (matches the recogniser's
    _channel_distances). nn = 1-NN min cosine distance; centroid = cosine to the mean exemplar DIRECTION;
    softnn = soft-min over exemplar cosine distances (all vote, robust to a stray)."""
    q = q_c / (np.linalg.norm(q_c) + 1e-9)
    Xn = EXc_w / (np.linalg.norm(EXc_w, axis=1, keepdims=True) + 1e-9)
    dd = 1.0 - (Xn @ q)                      # cosine distances to each exemplar
    if rule == "nn":
        return -float(dd.min())
    if rule == "centroid":
        m = Xn.mean(0); m = m / (np.linalg.norm(m) + 1e-9)
        return -float(1.0 - (m @ q))         # cosine to the mean exemplar direction
    return -float((-1.0 / TEMP) * np.logaddexp.reduce(-TEMP * dd))   # soft-min cosine distance


def evaluate(feats, words, rule):
    t1 = inK = tot = 0
    for held in SPEAKERS:
        bank = [(w, feats[(v, w, r)]) for v in SPEAKERS if v != held
                for w in words for r in (0, 1) if (v, w, r) in feats]
        cands = sorted({w for (w, _x) in bank})
        Ws = wccn.fit_per_cue(bank)
        bw = [(w, wccn.whiten(v, Ws)) for (w, v) in bank]
        ncue = len(bw[0][1])
        EX = [{w: np.stack([v[c] for (ww, v) in bw if ww == w]) for w in cands} for c in range(ncue)]
        for w0 in words:
            for r in range(RENDS):
                if (held, w0, r) not in feats:
                    continue
                q = wccn.whiten(feats[(held, w0, r)], Ws)
                sc = {cc: 0.0 for cc in cands}
                for c in range(ncue):
                    qc = np.asarray(q[c])
                    for cc in cands:
                        sc[cc] += score_word(qc, EX[c][cc], rule)
                rank = sorted(cands, key=lambda cc: -sc[cc])
                tot += 1; t1 += int(rank[0] == w0); inK += int(w0 in rank[:KREC])
    return t1 / max(tot, 1), inK / max(tot, 1)


def main():
    print("=" * 96)
    print("RECOGNISER SCORING RULE — 1-NN vs centroid vs soft-NN, top-1 + recall@6 (cross-speaker, full cues)")
    print("=" * 96)
    s = srs.Substrate(); s.add_node("EarConfig", {"cmvn": 1.0})
    sw = SpeechWorld(s, source_world=None)
    FE.install_curated_frontend(s)
    fe = next(n for n in s.nodes("FrontEnd"))
    allnames = [s.node(c)["attrs"].get("name") for et in ("has_cue", "repertoire") for c in s.neighbours(fe, et)]
    set_active(s, fe, allnames)

    print(f"  {len(WORDS)} words, speakers {SPEAKERS} | caching audio + full-cue features...", flush=True)
    feats = {}
    for v in SPEAKERS:
        for w in WORDS:
            for r in range(RENDS):
                out = sw.synth(w, {"variant": v, "pitch": 50, "rate": 175})
                if out is not None:
                    feats[(v, w, r)] = FE.feature_channels(s, np.asarray(out[0], dtype=np.float64), out[1])

    rules = [("1-NN (today)", "nn"), ("centroid", "centroid"), ("soft-NN", "soft")]
    print(f"\n  {'vocab':>6} |" + "".join(f"{nm+' t1/recall':>22}" for nm, _ in rules))
    best_rule = None; best_top1 = -1
    for nv in VOCAB_SIZES:
        words = WORDS[:nv]
        cells = []
        res = {}
        for nm, rk in rules:
            t1, ik = evaluate(feats, words, rk)
            res[rk] = (t1, ik)
            cells.append(f"{t1*100:>9.0f}%/{ik*100:.0f}%")
        print(f"  {nv:>6} |" + "".join(f"{c:>22}" for c in cells), flush=True)
        if nv == VOCAB_SIZES[-1]:
            for nm, rk in rules:
                if res[rk][0] > best_top1:
                    best_top1, best_rule = res[rk][0], nm
            base = res["nn"]

    print("\n" + "=" * 96)
    print(f"  at vocab {VOCAB_SIZES[-1]}: best scoring = {best_rule} (top-1 {best_top1*100:.0f}% vs 1-NN {base[0]*100:.0f}%, "
          f"+{(best_top1-base[0])*100:.0f}pt).")
    if best_top1 > base[0] + 0.04:
        print(f"  A ROBUST PROTOTYPE SHARPENS LARGE VOCAB: {best_rule} beats 1-NN by averaging out the stray cross-speaker")
        print("  exemplar that mis-ranks confusable words. Swap the recogniser's per-cue score -- a one-line, no-gradient")
        print("  change to the combine-all product (mean/soft-min instead of hard-min).")
    else:
        print(f"  scoring rule barely moves it (+{(best_top1-base[0])*100:.0f}pt) -- the ambiguity is in the CUES, not the")
        print("  exemplar reduction. The large-vocab top-1 ceiling is acoustic; the cipher's language prior is the ranker.")
    print("=" * 96)


if __name__ == "__main__":
    main()

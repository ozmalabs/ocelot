"""STRONG-EAR ROUTING CONFIDENCE — a TEACHER-FREE trust gate that the weak ear couldn't give (jabberwock test (c)).

The cross-cue agreement gate COLLAPSED before on a speaker-matched ear (confidence rode speaker identity, not correctness).
The borrowed-midpoint ear is speaker-invariant BY CONSTRUCTION, so a confidence read off its OWN output may now predict
per-token correctness ACROSS held-out speakers — a teacher-free "should I act on this?" signal (act on high-confidence,
defer on low). That is the bridge from recognition to SELECTIVE action, and its value is DISTINCT from the recognition number.

Teacher-free confidence (gold used ONLY to score, never to gate):
  - DTW margin  m = (d2 - d1) / (d2 + d1)   (top-2 distances; bigger gap = more confident)
  - cross-cue agreement: coarse pooled-prototype top-1 == fine DTW top-1
Metrics: margin-AUROC vs correctness; selective-accuracy @50%/@25% coverage (keep most-confident); agree-subset precision.
Control: identical gate on STRONG (raw wav2vec ~80%) vs WEAK (cochleagram ~13%) ear — the delta the weak ear can't produce.

PRE-COMMITTED BAR (jabberwock): UNLOCKED iff strong AUROC >= 0.70 AND strong sel@50% >= base+11, AND weak AUROC <= 0.60
AND weak sel@50% <= weak_base+3. If strong AUROC < 0.70 -> routing-confidence also dead -> LAND (recognition is the win).

Run:
  cd experiments/gamma-substrate
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.strong_ear_routing_confidence
"""
from __future__ import annotations

import os
import pickle
import sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import numpy as np

from scripts.phase0_learned_latent import dtw, fit_pca, pca_apply, KMAX, NWAY, PRUNE
from scripts.earn_strong_ear_rescore import _l2, build_ear

CACHE = "/tmp/p0lat_cache_L6.pkl"


def conf_tokens(words_feat, bank, vocab, vset, PW):
    """Per in-vocab token: (correct, margin, agree). Teacher-free reads off the ear's own output."""
    out = []
    for (w, sp, uid, tr) in words_feat:
        if w not in vset:
            continue
        pv = tr.mean(0); pv = pv / (np.linalg.norm(pv) + 1e-9)
        sims = PW @ pv
        coarse_top1 = vocab[int(np.argmax(sims))]
        top = np.argsort(-sims)[:PRUNE]
        scored = sorted(((vocab[i], min(dtw(tr, e) for e in bank[vocab[i]])) for i in top), key=lambda x: x[1])
        (w1, d1), (w2, d2) = scored[0], scored[1]
        margin = (d2 - d1) / (d2 + d1 + 1e-9)
        out.append((int(w1 == w), float(margin), int(coarse_top1 == w1)))
    return out


def auroc(score, label):
    score = np.asarray(score, np.float64); label = np.asarray(label, np.int32)
    n_pos = int(label.sum()); n_neg = len(label) - n_pos
    if n_pos == 0 or n_neg == 0:
        return float("nan")
    order = np.argsort(score, kind="mergesort")
    ranks = np.empty(len(score), np.float64); ranks[order] = np.arange(1, len(score) + 1)
    # average ties
    return (ranks[label == 1].sum() - n_pos * (n_pos + 1) / 2) / (n_pos * n_neg)


def sel_acc(correct, margin, cov):
    correct = np.asarray(correct); margin = np.asarray(margin)
    k = max(1, int(len(correct) * cov))
    keep = np.argsort(-margin)[:k]
    return 100 * correct[keep].mean()


def report(name, toks):
    cor = np.array([t[0] for t in toks]); mar = np.array([t[1] for t in toks]); agr = np.array([t[2] for t in toks])
    base = 100 * cor.mean()
    au = auroc(mar, cor)
    s50 = sel_acc(cor, mar, 0.50); s25 = sel_acc(cor, mar, 0.25)
    agree_prec = 100 * cor[agr == 1].mean() if agr.sum() else float("nan")
    agree_cov = 100 * agr.mean()
    print(f"  {name}:  base {base:.1f}  margin-AUROC {au:.3f}  sel@50% {s50:.1f} (+{s50-base:.1f})  sel@25% {s25:.1f} (+{s25-base:.1f})  "
          f"agree-prec {agree_prec:.1f} @cov {agree_cov:.0f}%")
    return base, au, s50


def main():
    print("=" * 100)
    print("STRONG-EAR ROUTING CONFIDENCE — teacher-free trust gate (strong vs weak ear)")
    print("=" * 100)
    with open(CACHE, "rb") as fh:
        data = pickle.load(fh)
    train, test = data["train"], data["test"]
    tr_spk = sorted({t[1] for t in train})
    bank_rows = [t for t in train]

    mu_p, V_p = fit_pca([t[4] for t in bank_rows])           # raw wav2vec PCA (strong ear ~80%)
    def strong_words(rows):
        return [(t[0], t[1], t[2], pca_apply(t[4], mu_p, V_p)) for t in rows]
    def weak_words(rows):
        return [(t[0], t[1], t[2], _l2(t[3])) for t in rows]

    print("  building strong (raw wav2vec) + weak (cochleagram) ears...", flush=True)
    s_bank, s_vocab, s_vset, s_PW = build_ear(strong_words(bank_rows))
    w_bank, w_vocab, w_vset, w_PW = build_ear(weak_words(bank_rows))

    print("  computing teacher-free confidence on test (both ears)...\n", flush=True)
    s_tok = conf_tokens(strong_words(test), s_bank, s_vocab, s_vset, s_PW)
    w_tok = conf_tokens(weak_words(test), w_bank, w_vocab, w_vset, w_PW)

    s_base, s_au, s_s50 = report("STRONG ear (raw wav2vec)", s_tok)
    w_base, w_au, w_s50 = report("WEAK   ear (cochleagram) ", w_tok)

    print("\n" + "=" * 100)
    strong_ok = (s_au >= 0.70) and (s_s50 >= s_base + 11)
    weak_fails = (w_au <= 0.60) and (w_s50 <= w_base + 3)
    print(f"  strong: AUROC {s_au:.3f} (>=0.70? {s_au>=0.70})  sel@50 +{s_s50-s_base:.1f} (>=+11? {s_s50-s_base>=11})")
    print(f"  weak:   AUROC {w_au:.3f} (<=0.60? {w_au<=0.60})  sel@50 +{w_s50-w_base:.1f} (<=+3? {w_s50-w_base<=3})")
    print("-" * 100)
    if strong_ok and weak_fails:
        print(f"  UNLOCKED — teacher-free trust gate: the strong ear's OWN confidence (margin) ranks its correct recognitions")
        print(f"  (AUROC {s_au:.2f}, selective acc {s_base:.0f}->{s_s50:.0f}@50%), while the weak ear's confidence is near-chance")
        print("  (it collapsed on the speaker confound). The speaker-invariant ear gives a 'should I act on this?' signal the")
        print("  weak ear could not — selective action (act high-confidence / defer low). Justifies the graph-native gate.")
    elif s_au >= 0.70:
        print(f"  PARTIAL — strong confidence separates (AUROC {s_au:.2f}) but a control clause missed; real signal, not a clean")
        print("  clear of the full bar. Confidence is usable; the cross-ear story needs a tighter read.")
    else:
        print(f"  ROUTING-CONFIDENCE DEAD too (strong AUROC {s_au:.2f} < 0.70) — the ear recognises well but its confidence does")
        print("  NOT separate right from wrong across speakers. LAND: recognition IS the win — reliable speech->word (80-95 from")
        print("  20-25), to be wired as perception, acting on all recognitions; no teacher-free gate on top.")
    print("=" * 100)


if __name__ == "__main__":
    main()

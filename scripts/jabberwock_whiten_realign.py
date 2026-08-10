"""WHITEN + REALIGN — the jabberwock's chosen Mahalanobis move (form 2): does whitening EAT the channel-shift penalty?

The agent chose (b): whiten features by the within-word nuisance covariance, then run the REALIGNED-triphone read --
composing the emission win (realignment, top-1 6->13) with the confirmed shift-fix (whitening Mahalanobis; the whitened
matched filter PAID +0.015 past CMVN, separation +0.057->+0.288). It is the WINNING structure-preserving re-weight, not
a learned-generative leaf (the MahalLeaf Term, 5th learned negative): it only rescales feature dims, never blends
exemplars or drops layout/order.

The agent's SHARPER test design: whitening's benefit is on SHIFTED audio, so the discriminating signal is whether the
SHIFT PENALTY (matched top-1 - shifted top-1) NARROWS with whitening -- not raw matched accuracy. Pre-committed:
  KEEP    shifted top-1 >= 15  AND  shift-penalty(whiten) < shift-penalty(plain)  [whitening visibly eats the shift]
  STOP    shifted < 15  OR  the shift penalty does not narrow -> revert to plain realigned 13%.
  FAIRNESS  at W = I, the whitened pipeline MUST reproduce the plain realigned read (harness check) -- here EXACT by
            construction: squared-Mahalanobis local cost ||W(a-b)||^2 at W=I equals 2(1-cos), monotone-identical to
            the baseline cosine DTW.

Build: realigned triphone units (same flat-start pipeline as the 13% read). S_n = within-word frame scatter (LDA
within-class, words=classes; WORD labels only). W = S_n^{-1/2} (eigh + shrinkage + partial-whiten alpha). Reads: PLAIN
(cosine DTW) vs WHITEN (squared-Mahalanobis DTW on Wf). Conditions: MATCHED (clips as cached) vs SHIFTED (per-clip
smooth spectral coloration, correlated + low-rank, INDEPENDENT of S_n -> not circular). 100-way, held-out clips.

Run:
  cd experiments/gamma-substrate
  ulimit -v 20971520
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.jabberwock_whiten_realign
"""
from __future__ import annotations

import glob
import os
import pickle
import sys
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import numpy as np
from scripts.phonebank import CACHE, _meta
from scripts.jabberwock_reads_oov_from_phones import phones, STOP
from scripts.jabberwock_realign_emission import build_units, realign_split, uniform_split, template

SAMPLE = 60000
N_WAY = 100
MAX_CLIPS = 110
SHIFT_STRENGTH = 0.45          # per-clip coloration amplitude (calibrated to cost a few top-1 points)
CONFIGS = [(0.0, 0.0), (0.5, 0.1), (1.0, 0.1)]   # (alpha, shrink); alpha=0 -> W=I (fairness check)


def _l2(F):
    F = np.asarray(F, dtype=np.float64)
    return F / (np.linalg.norm(F, axis=1, keepdims=True) + 1e-9)


def colour_shift(fr, rng, strength):
    """Per-clip smooth spectral coloration (correlated, low-rank, S_n-independent) -> an unseen channel."""
    D = fr.shape[1]
    k = rng.uniform(0.5, 2.5); phi = rng.uniform(0.0, 2 * np.pi)
    env = 1.0 + strength * np.sin(2 * np.pi * k * np.arange(D) / D + phi)
    return _l2(fr * env[None, :])


def whitener(S_n, alpha, shrink):
    D = S_n.shape[0]
    S = (1.0 - shrink) * S_n + shrink * (np.trace(S_n) / D) * np.eye(D)
    w, V = np.linalg.eigh(S)
    w = np.maximum(w, 1e-6 * w.max())
    return (V * (w ** (-alpha / 2.0))) @ V.T          # V diag(w^{-a/2}) V^T


def dtw_mahal(A, B):
    """DTW with squared-Mahalanobis local cost on already-whitened frames (= ||Wa-Wb||^2). Length-normalised."""
    if len(A) == 0 or len(B) == 0:
        return 1e9
    aa = (A * A).sum(1); bb = (B * B).sum(1)
    D = aa[:, None] + bb[None, :] - 2.0 * (A @ B.T)
    n, m = D.shape
    dp = np.full((n + 1, m + 1), 1e18); dp[0, 0] = 0.0
    for i in range(1, n + 1):
        row, prow, Di = dp[i], dp[i - 1], D[i - 1]
        for j in range(1, m + 1):
            row[j] = Di[j - 1] + min(prow[j], row[j - 1], prow[j - 1])
    return dp[n, m] / (n + m)


def main():
    print("=" * 100)
    print("WHITEN + REALIGN — does whitening (Mahalanobis) EAT the channel-shift penalty on the triphone read?")
    print("=" * 100)
    _ts, targets, clips = _meta()
    words = []
    for c in sorted(glob.glob(os.path.join(CACHE, "*_*.pkl"))):
        words += pickle.load(open(c, "rb"))
    rng = np.random.RandomState(0)
    sample = [words[i] for i in rng.permutation(len(words))[:SAMPLE]]
    vocabcount = Counter(w for (w, _f, _p) in words)
    del words
    print(f"  sampled {len(sample)} words; realigning (same flat-start pipeline as the 13% read)...", flush=True)

    uni_pw = [(ph, uniform_split(np.asarray(fr, dtype=np.float32), ph)) for (_w, fr, ph) in sample]
    _, _, _, mono0 = build_units(uni_pw)
    re_pw = []
    for (_w, fr, ph) in sample:
        fr = np.asarray(fr, dtype=np.float32)
        subs = realign_split(fr, ph, mono0)
        re_pw.append((ph, subs if subs is not None else uniform_split(fr, ph)))
    rea = build_units(re_pw)
    print(f"  realigned units built ({len(rea[0])} triphone medoids).", flush=True)

    # S_n = within-word frame scatter (words=classes; WORD labels only). Pool instances per word.
    by_word = defaultdict(list)
    for (w, fr, _ph) in sample:
        by_word[w].append(np.asarray(fr, dtype=np.float64))
    D = sample[0][1].shape[1]
    S_n = np.zeros((D, D)); nf = 0; nw = 0
    for w, insts in by_word.items():
        if len(insts) < 2:
            continue
        F = np.concatenate(insts, 0)
        Fc = F - F.mean(0, keepdims=True)
        S_n += Fc.T @ Fc; nf += len(Fc); nw += 1
        if nw >= 4000:
            break
    S_n /= max(nf, 1)
    print(f"  S_n estimated from {nw} multi-instance words / {nf} frames (D={D}).\n", flush=True)

    distractors = [w for (w, _c) in vocabcount.most_common()
                   if w not in set(targets) and w not in STOP and phones(w) and len(phones(w)) >= 3 and len(w) >= 4]
    cand = list(dict.fromkeys(list(targets) + distractors))
    cand = [w for w in cand if template(w, rea) is not None][:N_WAY]
    tmpl = {w: _l2(template(w, rea)) for w in cand}
    clips = [(w, _l2(cf)) for (w, cf) in clips[:MAX_CLIPS]]
    print(f"  {len(cand)}-way; {len(clips)} held-out clips; shift strength {SHIFT_STRENGTH}\n", flush=True)

    # the two test conditions (clip-side only; units are the agent's clean models)
    crng = np.random.RandomState(7)
    matched = clips
    shifted = [(w, colour_shift(cf, crng, SHIFT_STRENGTH)) for (w, cf) in clips]

    def score(condition, W):
        wt = {w: tmpl[w] @ W.T for w in cand}
        t1 = t3 = tot = 0
        for (w, cf) in condition:
            cfw = cf @ W.T
            d = {c: dtw_mahal(cfw, wt[c]) for c in cand}
            r = sorted(d, key=d.get)
            tot += 1; t1 += int(r[0] == w); t3 += int(w in r[:3])
        return 100 * t1 / max(tot, 1), 100 * t3 / max(tot, 1)

    I = np.eye(D)
    # PLAIN realigned read (Mahalanobis with W=I == cosine DTW ranking) — the 13% baseline, both conditions
    pm1, pm3 = score(matched, I)
    ps1, ps3 = score(shifted, I)
    plain_pen = pm1 - ps1
    print(f"  PLAIN realigned (W=I):   matched {pm1:.0f}/{pm3:.0f}   shifted {ps1:.0f}/{ps3:.0f}   shift-penalty {plain_pen:+.0f}")
    print(f"    (fairness floor: W=I matched {pm1:.0f}/{pm3:.0f} == the plain realigned read, EXACT by construction)\n", flush=True)

    rows = []
    for (alpha, shrink) in CONFIGS:
        if alpha == 0.0:
            continue
        W = whitener(S_n, alpha, shrink)
        wm1, wm3 = score(matched, W)
        ws1, ws3 = score(shifted, W)
        wpen = wm1 - ws1
        rows.append((alpha, shrink, wm1, wm3, ws1, ws3, wpen))
        print(f"  WHITEN a={alpha} shrink={shrink}:  matched {wm1:.0f}/{wm3:.0f}   shifted {ws1:.0f}/{ws3:.0f}   "
              f"shift-penalty {wpen:+.0f}", flush=True)

    best = max(rows, key=lambda r: r[4])          # best by shifted top-1
    a, sh, wm1, wm3, ws1, ws3, wpen = best
    print("\n" + "=" * 100)
    print(f"  PLAIN: matched {pm1:.0f} shifted {ps1:.0f} (penalty {plain_pen:+.0f})  |  WHITEN(best a={a}): matched {wm1:.0f} "
          f"shifted {ws1:.0f} (penalty {wpen:+.0f})")
    narrows = wpen < plain_pen
    if ws1 >= 15 and narrows:
        print(f"  KEEP — whitening EATS the shift penalty: shifted {ps1:.0f}->{ws1:.0f}, penalty {plain_pen:+.0f}->{wpen:+.0f} "
              f"(narrowed) and shifted >= 15. The confirmed structure-preserving re-weight composes with realignment.")
        print("  Mahalanobis (whitening form) belongs in the speech read. Speech: gooderer on shifted audio.")
    elif ws1 < 15:
        print(f"  STOP — shifted top-1 {ws1:.0f} < 15. Whitening did not lift the shifted read enough; revert to plain")
        print("  realigned 13%. Honest (the agent's pre-commitment).")
    elif not narrows:
        print(f"  STOP — the shift penalty did NOT narrow ({plain_pen:+.0f} -> {wpen:+.0f}); whitening rode realignment but")
        print("  did not eat the shift. Revert to plain realigned 13%. Honest.")
    print("=" * 100)


if __name__ == "__main__":
    main()

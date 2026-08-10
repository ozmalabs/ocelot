"""SEGMENTATION CHECK — the gatekeeper before a WER test: is WER bounded by RECOGNITION or by SEGMENTATION?

A whisper-free continuous WER needs the agent to segment connected speech into words ITSELF. This decomposes the WER:
  WER_ORACLE  = recognise TRUE-segmented words (MMS_FA word boundaries) with the trajectory read -> the RECOGNITION
                ceiling (perfect segmentation). If this is already terrible, recognition is the wall, not segmentation.
  WER_AGENT   = run a whisper-free SEGMENTER (spectral-novelty boundaries on the cochleagram) -> recognise each
                predicted segment -> WER. The GAP (WER_agent - WER_oracle) = the WER lost to SEGMENTATION.
Plus boundary F1 (predicted vs true word boundaries, 50 ms tolerance) and #segments vs #true-words.

Tells us, with numbers, whether a WER test would be meaningful yet and which wall to fix.

Run:
  cd experiments/gamma-substrate
  ulimit -v 24000000
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.jabberwock_segmentation_check
"""
from __future__ import annotations

import glob
import os
import sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import numpy as np
from scripts.jabberwock_reads_oov_from_phones import frames, dtw
from scripts.phonebank import align_utt
from scripts.librispeech_wer import load_flac
from scripts.jabberwock_harvest_exemplars import transcripts, DEV, MINW

N_BANK = 160
K = 3
NWAY = 600
N_TEST = 30
TOL = 0.05        # boundary-match tolerance (s)


def wer(ref, hyp):
    n, m = len(ref), len(hyp)
    dp = np.zeros((n + 1, m + 1), dtype=np.int32)
    dp[:, 0] = np.arange(n + 1); dp[0, :] = np.arange(m + 1)
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            c = 0 if ref[i - 1] == hyp[j - 1] else 1
            dp[i, j] = min(dp[i - 1, j] + 1, dp[i, j - 1] + 1, dp[i - 1, j - 1] + c)
    return dp[n, m] / max(n, 1)


def segment_novelty(F, fps, thr_k=0.8, min_frames=5):
    """whisper-free segmenter: boundaries at spectral-novelty peaks (frame-to-frame change) above a data-driven
    threshold, min word duration enforced. Returns list of (i0, i1) frame ranges + boundary times."""
    if len(F) < 2 * min_frames:
        return [(0, len(F))], []
    d = 1.0 - np.sum(F[1:] * F[:-1], axis=1)          # cosine novelty per frame gap
    k = np.ones(3) / 3.0
    d = np.convolve(d, k, mode="same")
    thr = d.mean() + thr_k * d.std()
    cand = [i for i in range(1, len(d) - 1) if d[i] > thr and d[i] >= d[i - 1] and d[i] >= d[i + 1]]
    bnds = [0]
    for c in cand:
        if c - bnds[-1] >= min_frames:
            bnds.append(c)
    if len(F) - bnds[-1] < min_frames and len(bnds) > 1:
        bnds[-1] = len(F)
    else:
        bnds.append(len(F))
    segs = [(bnds[i], bnds[i + 1]) for i in range(len(bnds) - 1)]
    btimes = [b / fps for b in bnds[1:-1]]
    return segs, btimes


def main():
    print("=" * 100)
    print("SEGMENTATION CHECK — is WER bounded by RECOGNITION (oracle seg) or by SEGMENTATION (agent seg)?")
    print("=" * 100)
    tr = transcripts(DEV)
    flacs = sorted(glob.glob(os.path.join(DEV, "**", "*.flac"), recursive=True))
    by_spk = defaultdict(list)
    for f in flacs:
        b = os.path.basename(f)[:-5]
        if b in tr:
            by_spk[os.path.basename(f).split("-")[0]].append((f, tr[b]))
    spks = sorted(by_spk); test_spk, train_spk = spks[-3:], spks[:-3]

    bank = defaultdict(list); nb = 0
    for sp in train_spk:
        for (f, t) in by_spk[sp]:
            if nb >= N_BANK:
                break
            x, fs = load_flac(f); x = np.asarray(x, dtype=np.float64); nb += 1
            for (w, t0, t1) in align_utt(x, fs, t):
                if len(w) >= MINW and len(bank[w]) < K:
                    seg = x[int(t0 * fs):int(t1 * fs)]
                    if seg.size >= int(0.05 * fs):
                        bank[w].append(frames(np.asarray(seg, dtype=np.float64))[0].astype(np.float32))
        if nb >= N_BANK:
            break
    vocab = [w for w, _ in sorted(bank.items(), key=lambda kv: -len(kv[1]))[:NWAY]]
    BANK = [(w, e) for w in vocab for e in bank[w]]

    def _l2(v):
        v = np.asarray(v, np.float32); nrm = np.linalg.norm(v)
        return v / nrm if nrm > 1e-9 else v
    BANK_POOL = np.stack([_l2(e.mean(0)) for (_w, e) in BANK])     # pooled fingerprints for a cheap prefilter
    BANK_W = [w for (w, _e) in BANK]
    print(f"  trajectory bank {len(bank)} words ({nb} utts); {len(vocab)}-way (coarse-to-fine: pooled prefilter -> DTW)\n", flush=True)

    def recognise(fr):
        fr = fr.astype(np.float32)
        sims = BANK_POOL @ _l2(fr.mean(0))                          # cheap pooled cosine over all exemplars
        top = np.argsort(-sims)[:40]                                # top-40 candidates -> DTW only those
        best, arg = 1e18, None
        for i in top:
            d = dtw(fr, BANK[i][1])
            if d < best:
                best, arg = d, BANK_W[i]
        return arg

    or_w = or_t = ag_w = ag_t = 0.0
    bt_hit = bt_pred = bt_true = 0
    nseg_a = nseg_t = 0
    done = 0
    for sp in test_spk:
        for (f, t) in by_spk[sp]:
            if done >= N_TEST:
                break
            x, fs = load_flac(f); x = np.asarray(x, dtype=np.float64)
            algn = [(w, t0, t1) for (w, t0, t1) in align_utt(x, fs, t) if len(w) >= MINW]
            ref = [w for (w, _a, _b) in algn]
            if len(ref) < 3:
                continue
            done += 1
            # ORACLE segmentation: true word spans
            hyp_or = [recognise(frames(x[int(a * fs):int(b * fs)])[0]) for (_w, a, b) in algn]
            or_w += wer(ref, hyp_or) * len(ref); or_t += len(ref)
            # AGENT segmentation: novelty boundaries on whole-utt frames
            F = frames(x)[0]; fps = len(F) * fs / len(x)
            segs, btimes = segment_novelty(F, fps)
            hyp_ag = [recognise(F[i0:i1]) for (i0, i1) in segs if i1 - i0 >= 2]
            ag_w += wer(ref, hyp_ag) * len(ref); ag_t += len(ref)
            nseg_a += len(hyp_ag); nseg_t += len(ref)
            # boundary F1 vs true internal boundaries
            true_b = [b for (_w, _a, b) in algn[:-1]]
            bt_true += len(true_b); bt_pred += len(btimes)
            for tb in true_b:
                if any(abs(tb - pb) <= TOL for pb in btimes):
                    bt_hit += 1
            if done % 10 == 0:
                print(f"    {done}/{N_TEST} utts...", flush=True)

    WER_OR = 100 * or_w / max(or_t, 1)
    WER_AG = 100 * ag_w / max(ag_t, 1)
    prec = bt_hit / max(bt_pred, 1); rec = bt_hit / max(bt_true, 1)
    f1 = 2 * prec * rec / max(prec + rec, 1e-9)
    print("\n" + "=" * 100)
    print(f"  RECOGNITION ceiling (ORACLE segmentation): WER {WER_OR:.1f}%   ({len(vocab)}-way, OOV -> sub errors)")
    print(f"  AGENT whisper-free segmentation:           WER {WER_AG:.1f}%   (#segs {nseg_a} vs #words {nseg_t}, "
          f"ratio {nseg_a/max(nseg_t,1):.2f})")
    print(f"  boundary F1 {100*f1:.1f}% (prec {100*prec:.0f} / rec {100*rec:.0f}, ±{int(TOL*1000)}ms)")
    print(f"  SEGMENTATION cost = WER_agent - WER_oracle = {WER_AG-WER_OR:+.1f} pts")
    print("-" * 100)
    if WER_OR >= 75:
        print(f"  VERDICT: RECOGNITION is the wall ({WER_OR:.0f}% WER even with PERFECT segmentation, {len(vocab)}-way). A WER")
        print("  test now would be dominated by recognition, not segmentation -- the precision read / OOV is what to fix first.")
    elif WER_AG - WER_OR >= 25:
        print(f"  VERDICT: SEGMENTATION is the wall (+{WER_AG-WER_OR:.0f} WER from the agent's segmenter; boundary F1 {100*f1:.0f}%).")
        print("  Recognition with perfect segmentation is workable; the whisper-free segmenter is what to fix before WER.")
    else:
        print(f"  VERDICT: both contribute (recognition {WER_OR:.0f}%, +{WER_AG-WER_OR:.0f} from segmentation). A WER test is")
        print("  meaningful but humbling; report both numbers honestly.")
    print("=" * 100)


if __name__ == "__main__":
    main()

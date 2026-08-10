"""ADAPTING EAR — beat the cross-speaker wall by TUNING IN: per-speaker affine warp fit from confident self-labels.

The dynamism attack. Not normalisation (remove speaker, static -> all failed) but ADAPTATION (tune in, like a human).
A per-speaker fMLLR-style affine warp A is fit (closed form, ridge-to-identity) to align the agreement-gated CONFIDENT
self-labelled frames onto the bank exemplars the gate matched them to -> shifts that speaker's whole formant/timing
geometry toward the known space, so it carries to that speaker's UNHEARD words too (a directed fit with a target).
Unsupervised (self-labels via the cross-cue gate), cheap/online (accumulate sufficient stats, solve each utterance).

Measure the TRAJECTORY: accuracy on a held-out speaker's UNHEARD words after adapting from k=0,1,2,4,8 of that speaker's
confident utterances; vs the ORACLE warp (fit from TRUE labels) = the ceiling. Pre-committed: KEEP if unheard-word
accuracy climbs monotonically from cold-start and closes >=40% of the gap to oracle by k=8; STOP if no climb / diverges;
FAIRNESS FLOOR: k=0 = cold-start exactly (A=I), every point scored on words held out within the speaker.

Run:
  cd experiments/gamma-substrate
  ulimit -v 24000000
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.adapting_ear
"""
from __future__ import annotations

import glob
import os
import sys
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import numpy as np
from scripts.jabberwock_reads_oov_from_phones import frames, dtw
from scripts.phonebank import align_utt
from scripts.librispeech_wer import load_flac
from scripts.jabberwock_harvest_exemplars import transcripts, DEV, MINW
from scripts.jabberwock_selftraining_gate import featset, delta, _l2

N_BANK = 250
KMAX_EX = 5
NWAY = 400
PRUNE = 30
N_TEST_SPK = 6
KS = [0, 1, 2, 4, 8]
LAM = 5.0       # ridge toward identity (shrinkage)


def _l2rows(M):
    M = np.asarray(M, np.float32)
    n = np.linalg.norm(M, axis=1, keepdims=True)
    return (M / np.maximum(n, 1e-9)).astype(np.float32)


def dtw_path(A, B):
    n, m = len(A), len(B)
    D = 1.0 - A @ B.T
    dp = np.full((n + 1, m + 1), 1e18); dp[0, 0] = 0.0
    for i in range(1, n + 1):
        Di, di, dm = D[i - 1], dp[i], dp[i - 1]
        for j in range(1, m + 1):
            di[j] = Di[j - 1] + min(dm[j], di[j - 1], dm[j - 1])
    i, j = n, m; path = []
    while i > 0 and j > 0:
        path.append((i - 1, j - 1))
        _, i, j = min(((dp[i - 1, j - 1], i - 1, j - 1), (dp[i - 1, j], i - 1, j), (dp[i, j - 1], i, j - 1)))
    return path[::-1]


def main():
    print("=" * 100)
    print("ADAPTING EAR — per-speaker affine warp from confident self-labels; the TUNE-IN trajectory vs oracle")
    print("=" * 100)
    import substrate_rs as srs
    s = srs.Substrate(); s.add_node("EarConfig", {"cmvn": 1.0})
    tr = transcripts(DEV)
    flacs = sorted(glob.glob(os.path.join(DEV, "**", "*.flac"), recursive=True))
    by_spk = defaultdict(list)
    for f in flacs:
        b = os.path.basename(f)[:-5]
        if b in tr:
            by_spk[os.path.basename(f).split("-")[0]].append((f, tr[b]))
    spks = sorted(by_spk); test_spk, train_spk = spks[-N_TEST_SPK:], spks[:-N_TEST_SPK]

    bank = defaultdict(list); nb = 0
    for sp in train_spk:
        for (f, t) in by_spk[sp]:
            if nb >= N_BANK:
                break
            x, fs = load_flac(f); x = np.asarray(x, dtype=np.float64); nb += 1
            for (w, t0, t1) in align_utt(x, fs, t):
                if len(w) >= MINW and len(bank[w]) < KMAX_EX:
                    seg = x[int(t0 * fs):int(t1 * fs)]
                    if seg.size >= int(0.05 * fs):
                        bank[w].append(featset(s, seg))
        if nb >= N_BANK:
            break
    vocab = [w for w, e in sorted(bank.items(), key=lambda kv: -len(kv[1]))[:NWAY]]
    vset = set(vocab)
    PW = np.stack([_l2(np.stack([e[0].mean(0) for e in bank[w]]).mean(0)) for w in vocab])
    D = bank[vocab[0]][0][0].shape[1]
    print(f"  bank {len(bank)} words ({nb} utts, {len(train_spk)} spk); {len(vocab)}-way; D={D}; {len(test_spk)} test spk\n", flush=True)

    def recog(traj, A):
        w = _l2rows(traj @ A.T) if A is not None else traj
        dl = delta(w)
        pv = w.mean(0); pv = pv / (np.linalg.norm(pv) + 1e-9)
        top = np.argsort(-(PW @ pv))[:PRUNE]
        best, arg = 1e18, None
        for i in top:
            c = vocab[i]
            d = min(dtw(w, e[0]) for e in bank[c]) + 0.3 * min(dtw(dl, delta(e[0])) for e in bank[c])
            if d < best:
                best, arg = d, c
        return arg

    def agree(traj, fft, allp):
        dl = delta(traj); pv = _l2(traj.mean(0)); top = np.argsort(-(PW @ pv))[:PRUNE]
        cw = [vocab[i] for i in top]
        d_st = [min(dtw(traj, e[0]) for e in bank[c]) for c in cw]
        d_dl = [min(dtw(dl, delta(e[0])) for e in bank[c]) for c in cw]
        d_ff = [min(1.0 - fft @ e[1] for e in bank[c]) for c in cw]
        d_ap = [min(1.0 - allp @ e[2] for e in bank[c]) for c in cw]
        winners = [cw[int(np.argmin(d))] for d in (d_st, d_dl, d_ff, d_ap)]
        cons, ag = Counter(winners).most_common(1)[0]
        return cons, ag

    def accum_pairs(traj, label_word, Stt, Spt):
        # align test traj to the nearest bank exemplar of label_word; accumulate A*test ~ bank frame-pairs
        exs = [e[0] for e in bank.get(label_word, [])]
        if not exs:
            return
        ref = min(exs, key=lambda e: dtw(traj, e))
        for (i, j) in dtw_path(traj, ref):
            Stt += np.outer(traj[i], traj[i]); Spt += np.outer(ref[j], traj[i])

    curves = {k: [] for k in KS}; oracles = []
    for sp in test_spk:
        words = []
        for (f, t) in by_spk[sp]:
            x, fs = load_flac(f); x = np.asarray(x, dtype=np.float64)
            for (w, t0, t1) in align_utt(x, fs, t):
                if w in vset and len(w) >= MINW:
                    seg = x[int(t0 * fs):int(t1 * fs)]
                    if seg.size >= int(0.05 * fs):
                        words.append((w, featset(s, seg)))
        if len(words) < 30:
            continue
        cut = int(0.55 * len(words))
        adapt_pool, eval_set = words[:cut], words[cut:]      # EVAL = held-out within speaker (never fit on)
        # pick confident adapt words (cross-cue agreement) in order, up to max(KS)
        conf = []
        for (w, (traj, fft, allp)) in adapt_pool:
            cons, ag = agree(traj, fft, allp)
            if ag >= 3:
                conf.append((traj, cons, w))            # self-label cons (may be wrong); w = truth (for oracle)
            if len(conf) >= max(KS):
                break
        # incremental warps from self-labels, + oracle from true labels
        Stt = LAM * np.eye(D, dtype=np.float64); Spt = LAM * np.eye(D, dtype=np.float64)
        warps = {0: np.eye(D, dtype=np.float32)}
        for k in range(1, max(KS) + 1):
            if k - 1 < len(conf):
                traj, cons, _w = conf[k - 1]
                accum_pairs(traj, cons, Stt, Spt)
            warps[k] = (Spt @ np.linalg.inv(Stt)).astype(np.float32)
        Sto = LAM * np.eye(D); Spo = LAM * np.eye(D)
        for (traj, _cons, w) in conf:
            accum_pairs(traj, w, Sto, Spo)             # ORACLE: true labels
        A_oracle = (Spo @ np.linalg.inv(Sto)).astype(np.float32) if conf else np.eye(D, dtype=np.float32)
        # eval on held-out words at each k + oracle
        ev = eval_set[:40]
        for k in KS:
            A = warps.get(min(k, max(warps)), np.eye(D, dtype=np.float32))
            acc = 100 * np.mean([recog(traj, A) == w for (w, (traj, _f, _a)) in ev])
            curves[k].append(acc)
        oracles.append(100 * np.mean([recog(traj, A_oracle) == w for (w, (traj, _f, _a)) in ev]))
        print(f"    speaker {sp}: {len(conf)} confident adapt, {len(ev)} eval | "
              f"k0 {curves[0][-1]:.0f} -> k8 {curves[8][-1]:.0f} | oracle {oracles[-1]:.0f}", flush=True)

    print("\n" + "=" * 100)
    cold = np.mean(curves[0]); orac = np.mean(oracles)
    print(f"  TUNE-IN trajectory on UNHEARD words ({len(curves[0])} test speakers, {len(vocab)}-way):")
    for k in KS:
        print(f"    k={k:>2} adapted utts:  {np.mean(curves[k]):.1f}%")
    print(f"    ORACLE warp (true labels): {orac:.1f}%   (cold-start {cold:.1f}%)")
    k8 = np.mean(curves[8]); gap = orac - cold
    closed = (k8 - cold) / gap if gap > 0.5 else 0.0
    print("-" * 100)
    monotone = all(np.mean(curves[KS[i]]) >= np.mean(curves[KS[i - 1]]) - 0.5 for i in range(1, len(KS)))
    if k8 >= cold + 2 and closed >= 0.40 and monotone:
        print(f"  KEEP — the ear TUNES IN: unheard-word accuracy climbs {cold:.1f} -> {k8:.1f} over 8 confident utts, closing")
        print(f"  {100*closed:.0f}% of the gap to the oracle warp ({orac:.1f}). DYNAMIC ADAPTATION generalises to UNHEARD words --")
        print("  the dynamism constraint beats the wall that NORMALISATION couldn't. ~20% was the cold-start, not the limit.")
    elif k8 >= cold + 1.5:
        print(f"  PARTIAL — real tune-in ({cold:.1f}->{k8:.1f}, closed {100*closed:.0f}% to oracle {orac:.1f}) but under the bar; modest. Honest.")
    else:
        print(f"  STOP — no generalising tune-in ({cold:.1f}->{k8:.1f}, oracle {orac:.1f}); the unsupervised warp didn't help unheard")
        print("  words (self-labels too noisy, or the affine doesn't capture the speaker geometry here). Honest.")
    print("=" * 100)


if __name__ == "__main__":
    main()

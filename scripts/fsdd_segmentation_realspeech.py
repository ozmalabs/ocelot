"""Segmentation on REAL speech with the front-end A/B: does the spectral-SHAPE (formant)
front-end that broke cross-speaker clustering also lift word SEGMENTATION? Concatenate
FSDD digit utterances into continuous 'sentences' (each digit = a word, NO gaps -> the
ONLY boundary cue is statistics), with KNOWN digit boundaries.

Pipeline (the agent's): frames -> units (cluster) -> collapse runs into phoneme-units ->
held bidirectional-TP segmenter -> cut positions. Measure boundary-F1 of the cuts vs the
true digit boundaries, for ENERGY vs SHAPE frame features. The clustering arc showed the
bound is UNIT QUALITY (= the front-end); if it transfers, shape units give cleaner TP and
land cuts on the word boundaries better.

Run: python scripts/fsdd_segmentation_realspeech.py [n_sent] [k_units]
"""
from __future__ import annotations
import os
import random
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir, "runners/dsl/python"))

from substrate_rs import Substrate
from substrate_rs.speech import _audio
from domains.cross_speaker_clustering import cluster
from domains.forward_segmentation import estimate_bidirectional_tp
from scripts.segmentation_saffran import segment_bidir, bwd_table, tp_table
from scripts.speech_analysis_by_synthesis import load_wav, DATA, FN

HOP, WIN, N_BANDS = 240, 400, 24      # 30ms hop, 50ms window @ 8kHz


def frames(s, bank, samples):
    buf = _audio.audio_from_array(s, samples, sample_rate=8000)
    arrs = []
    for r in _audio.a1_responses(s, buf, bank):
        a = _audio.audio_to_array(s, r).astype(np.float64)
        arrs.append(a.mean(1) if a.ndim > 1 else a)
    L = min(len(a) for a in arrs)
    nf = max(1, (L - WIN) // HOP + 1)
    M = np.zeros((nf, len(bank)))
    for fi in range(nf):
        sl = slice(fi * HOP, fi * HOP + WIN)
        for bi, a in enumerate(arrs):
            M[fi, bi] = np.sqrt(np.mean(a[sl] ** 2) + 1e-12)
    return M


def shape(M):
    L = np.log(M + 1e-6)
    return L - L.mean(axis=1, keepdims=True)


def collapse(units, digit_idx):
    """run-length collapse consecutive equal units -> phoneme-units; a TRUE boundary is
    a collapsed position whose run ends one digit and the next run starts the next."""
    seq, bounds, i, n = [], set(), 0, len(units)
    runs = []                                   # (unit, last_digit_of_run)
    while i < n:
        j = i
        while j < n and units[j] == units[i]:
            j += 1
        runs.append((units[i], digit_idx[j - 1])); i = j
    for p, (u, d) in enumerate(runs):
        seq.append(u)
        if p + 1 < len(runs) and runs[p + 1][1] != d:   # digit changes after this run
            bounds.add(p + 1)                            # boundary AFTER collapsed pos p
    return tuple(seq), bounds


def bf1(pred, true, tol=1):
    if not true:
        return 0.0
    hit_p = sum(any(abs(p - t) <= tol for t in true) for p in pred)
    hit_t = sum(any(abs(p - t) <= tol for p in pred) for t in true)
    pr = hit_p / len(pred) if pred else 0.0
    rc = hit_t / len(true)
    return 2 * pr * rc / (pr + rc) if (pr + rc) else 0.0


def run(front, all_M, sent_frames, sent_digidx, k, word):
    feats = front(np.vstack(all_M))
    labels = cluster(feats, k, seed=0)
    # split labels back per sentence
    seqs, bounds_list, off = [], [], 0
    for M, didx in zip(sent_frames, sent_digidx):
        u = labels[off:off + len(M)]; off += len(M)
        cseq, cb = collapse(list(u), didx)
        seqs.append(cseq); bounds_list.append(cb)
    fwd = tp_table(seqs); bwd = bwd_table(seqs)
    f1s = []
    for cseq, true_b in zip(seqs, bounds_list):
        if len(cseq) < 2:
            continue
        words = segment_bidir(list(cseq), fwd, bwd)
        pred, pos = set(), 0
        for w in words[:-1]:
            pos += len(w); pred.add(pos)
        f1s.append(bf1(pred, true_b))
    return float(np.mean(f1s))


def main():
    n_sent = int(sys.argv[1]) if len(sys.argv) > 1 else 40
    k = int(sys.argv[2]) if len(sys.argv) > 2 else 28
    s = Substrate(); _audio.seed_audio_grammar(s)
    bank = _audio.cochlea(s, n_bands=N_BANDS, fs=8000)

    pool = {}
    for fn in sorted(os.listdir(DATA)):
        m = FN.match(fn)
        if m and int(m.group(3)) < 12:
            pool.setdefault(int(m.group(1)), []).append(os.path.join(DATA, fn))
    rng = random.Random(0)

    all_M, sent_frames, sent_digidx, word = [], [], [], []
    for _ in range(n_sent):
        digs = [rng.randrange(10) for _ in range(6)]
        Ms, didx = [], []
        for di, d in enumerate(digs):
            sm = load_wav(rng.choice(pool[d]))[0]
            M = frames(s, bank, sm)
            Ms.append(M); didx.extend([di] * len(M))
        Mcat = np.vstack(Ms)
        all_M.append(Mcat); sent_frames.append(Mcat); sent_digidx.append(didx); word.append(digs)

    print("=" * 64)
    print(f"REAL-SPEECH SEGMENTATION — {n_sent} sentences x6 digits, k={k} frame-units")
    print(f"  boundary-F1 of held bidirectional-TP cuts vs true digit boundaries")
    print("=" * 64)
    e = run(lambda X: X, all_M, sent_frames, sent_digidx, k, word)
    sh = run(shape, all_M, sent_frames, sent_digidx, k, word)
    print(f"  ENERGY front-end : boundary-F1 {e:.3f}")
    print(f"  SHAPE  front-end : boundary-F1 {sh:.3f}   (delta {sh-e:+.3f})")
    print("=" * 64)
    print(f"  the shape/formant front-end {'HELPS' if sh > e else 'does NOT help'} "
          f"real-speech segmentation ({sh-e:+.3f}).")


if __name__ == "__main__":
    main()

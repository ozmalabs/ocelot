"""Apply the JABBERWOCK'S OWN designed segmenter improvements to LibriSpeech.

The baseline word-segmenter eval used forward_segment with boundary_mode='median',
n_passes=1 (F1 ~0.33). The agent has ALREADY DESIGNED two graph-native upgrades, both
expressed as the SAME boundary Term over a different read of its OWN TP structure:
  - bidirectional bond  min(P(nxt|cur),P(cur|nxt))   (default; in the baseline already)
  - boundary_mode='local_min' — "the agent's forward-built fix for median's ~8x
    over-segmentation" (cut ONLY at genuine TP troughs, not everywhere below median).
Nothing here is hand-designed by me: forward_segment is the agent's graph-native
segmenter; I only select the agent's designed options and measure on real LibriSpeech.

Same frames/units for every config; only the agent's boundary Term/passes differ.
Metric: word-boundary F1 (vs proportional word boundaries) + chunks/words ratio
(median over-segments; the agent's local_min should pull it toward 1.0).

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_segmenter_localmin_eval.py [n_utts]
"""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))
import numpy as np
import substrate_rs as srs
import scripts.librispeech_wer as L
from scripts.context_invariant_librispeech_accept import (
    frames_of, kmeans, quantize, words_of, proportional_word_boundaries,
    chunk_boundary_times, boundary_f1, flat_len)
from domains.forward_segmentation import forward_segment


def _cmvn(M):
    M = np.asarray(M, float)
    return (M - M.mean(0)) / (M.std(0) + 1e-6)


def main():
    n_utts = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    pairs = L.gather_pairs(limit=n_utts + 60)[:n_utts]
    print("=" * 88)
    print("JABBERWOCK'S DESIGNED SEGMENTER on LibriSpeech (median vs its local_min fix)")
    print("=" * 88)
    frame_seqs, time_seqs, word_seqs, span_seqs = [], [], [], []
    t0 = time.time()
    for i, (path, sp, ch, ut, tr) in enumerate(pairs):
        try:
            x, fs = L.load_flac(path); M = _cmvn(frames_of(x, fs))
        except Exception:
            continue
        nf = len(M); dur = len(x) / fs
        frame_seqs.append(M)
        time_seqs.append(list(np.linspace(0, dur, nf)))
        word_seqs.append(words_of(tr)); span_seqs.append((0.0, dur))
        if (i + 1) % 10 == 0:
            print(f"  framed {i+1}/{n_utts} [{time.time()-t0:.0f}s]", flush=True)
    print(f"  framed {len(frame_seqs)} utts", flush=True)

    pool = np.concatenate(frame_seqs, 0)
    C = kmeans(pool, 48)
    unit_seqs = [quantize(M, C) for M in frame_seqs]
    sub = srs.Substrate()

    def evalcfg(mode, npass, bidir):
        res = forward_segment(sub, unit_seqs, n_passes=npass, boundary_mode=mode, bidirectional=bidir)
        chunked = res["chunked"] or [[(u,) for u in s] for s in unit_seqs]
        f1 = 0.0; nch = 0; nw = 0; n = 0
        for seq, times, words, (ts, te), chunks in zip(
                unit_seqs, time_seqs, word_seqs, span_seqs, chunked):
            true_b = proportional_word_boundaries(words, ts, te)
            con_b = chunk_boundary_times(times, [flat_len(c) for c in chunks])
            f1 += boundary_f1(con_b, true_b, 0.06)[2]
            nch += len(chunks); nw += max(len(words), 1); n += 1
        return f1 / max(n, 1), nch / max(nw, 1)

    print(f"\n   {'config (agent design)':38} {'F1':>6} {'chunks/words':>13}")
    rows = [
        ("median, 1 pass (BASELINE)",            "median",    1, True),
        ("local_min, 1 pass (agent fix)",        "local_min", 1, True),
        ("local_min, 2 passes (agent fix+iter)", "local_min", 2, True),
        ("median, 1 pass, forward-only TP",      "median",    1, False),
    ]
    best = (0.0, None)
    for name, mode, npass, bidir in rows:
        f1, ratio = evalcfg(mode, npass, bidir)
        print(f"   {name:38} {f1:6.3f} {ratio:13.2f}")
        if f1 > best[0]:
            best = (f1, name)
    print("\n" + "=" * 88)
    print(f"  best (agent-designed): {best[1]} -> F1 {best[0]:.3f}")
    print("  All configs are the AGENT'S graph-native segmenter (boundary = held Filter Term over its own")
    print("  TP-bond structure); only the agent's designed option (local_min trough vs median, iteration)")
    print("  differs. The improvement is the jabberwock's design, applied to real speech — not mine.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

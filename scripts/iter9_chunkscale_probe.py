"""iter-9 probe — measure chunks-per-word as a function of (a) corpus-scale vs
per-utterance TP estimation and (b) number of BPE-style chunker passes.

The recognizer (continuous_speech_recognition) chunks each utterance INDEPENDENTLY
with forward_segment(n_passes=1). The agent's statistical_learning science (Saffran
et al.) says word boundaries are read from recurrence ACROSS the corpus, not within
one short utterance — and the agent's own forward_segment already has the BPE-style
merge-up (n_passes>1) that grows chunks toward word scale. This probe measures both
levers directly (chunks/word toward 1-2 from ~3-6) BEFORE wiring them into the
recognizer. World adapter: no agent reasoning, only measurement.

Run: python -m scripts.iter9_chunkscale_probe [n_train] [n_speakers] [K]
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import scripts.sentence_learning as SL
from scripts.invariant_units_accept import band_trajectory_matrix
from domains.invariant_units import invariant_transform, canonical_log_centroid
from domains.forward_segmentation import forward_segment
from domains.run_length_collapse import collapse_stream
from substrate_rs import Substrate
import scripts.continuous_speech_recognition as CSR


def main():
    n_train = int(sys.argv[1]) if len(sys.argv) > 1 else 22
    n_speakers = int(sys.argv[2]) if len(sys.argv) > 2 else 14
    K = int(sys.argv[3]) if len(sys.argv) > 3 else 48
    import random
    random.seed(1)

    pairs = SL.gather_pairs()
    all_speakers = sorted(set(p[1] for p in pairs))[:n_speakers]
    n_held = max(2, len(all_speakers) // 5)
    train_spk = set(all_speakers[n_held:])
    train_pairs = [p for p in pairs if p[1] in train_spk]
    random.shuffle(train_pairs)
    train_pairs = train_pairs[:n_train]

    sub = Substrate()
    raw = []
    for path, sp, ch, ut, transcript in train_pairs:
        words = CSR.words_of(transcript)
        if not words:
            continue
        try:
            x, fs = SL.load_flac_8k(path)
        except Exception:
            continue
        M = CSR.frames_of(x, fs)
        if M.shape[0] < 4:
            continue
        raw.append((M, words))
    canonical = canonical_log_centroid([M for M, _ in raw])
    inv = [(invariant_transform(M, canonical), w) for M, w in raw]
    pool = np.concatenate([M for M, _ in inv], axis=0)
    C = CSR.kmeans(pool, K, seed=0)

    tot_words = sum(len(w) for _, w in inv)

    # Per-utterance unit streams (after stability collapse, the recognizer default).
    streams = []
    for i, (M, words) in enumerate(inv):
        units = CSR.quantize(M, C)
        col = collapse_stream(sub, units, f"probe_{i}", mode="stability", M=M)
        streams.append(col["coarse_ids"])

    avg_units_per_word = sum(len(s) for s in streams) / max(tot_words, 1)
    print(f"corpus: {len(inv)} utts, {tot_words} words, "
          f"coarse-units/word = {avg_units_per_word:.2f}")
    print()

    def chunks_per_word(chunked):
        n = sum(len(c) for c in chunked)
        return n / max(tot_words, 1)

    print(f"{'config':<42} {'chk/word':>9}  {'mean_len':>8}  {'recur':>6}")
    print("-" * 72)

    # (A) PER-UTTERANCE TP (the recognizer's current mode), varying n_passes.
    for npass in (1, 2, 3, 4):
        chunked_all = []
        for i, s in enumerate(streams):
            res = forward_segment(sub, [s], n_passes=npass,
                                  boundary_mode="local_min")
            ch = res["chunked"]
            chunked_all.append(ch[0] if ch and ch[0] is not None else [tuple(s)])
        from domains.forward_segmentation import chunk_stats
        st = chunk_stats(chunked_all)
        print(f"{'per-utt TP, local_min, passes='+str(npass):<42} "
              f"{chunks_per_word(chunked_all):>9.2f}  {st['mean_len']:>8.2f}  "
              f"{st['recurrence']:>6.2f}")

    print()
    # (B) CORPUS-SCALE TP: estimate TP over ALL streams at once, then chunk each
    # utterance against the corpus-wide TP. The agent's statistical_learning science
    # — recurrence across the corpus sets the boundaries, not one short utterance.
    # forward_segment estimates TP over whatever sequences it's given; passing ALL
    # streams makes TP corpus-scale, and it chunks each stream with that shared TP.
    for npass in (1, 2, 3, 4):
        res = forward_segment(sub, streams, n_passes=npass,
                              boundary_mode="local_min")
        chunked_all = res["chunked"]
        if chunked_all is None:
            print(f"{'CORPUS TP, local_min, passes='+str(npass):<42} "
                  f"(degenerate TP at this pass; previous pass kept)")
            continue
        chunked_all = [c if c is not None else [] for c in chunked_all]
        from domains.forward_segmentation import chunk_stats
        st = chunk_stats(chunked_all)
        print(f"{'CORPUS TP, local_min, passes='+str(npass):<42} "
              f"{chunks_per_word(chunked_all):>9.2f}  {st['mean_len']:>8.2f}  "
              f"{st['recurrence']:>6.2f}")

    print()
    print("target: chunks/word toward 1-2 (one chunk ~= one word)")


if __name__ == "__main__":
    main()

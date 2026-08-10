"""mine_ssl_goldspan — the DECISIVE control for the chunk-consistency mine.

wav2vec2 achieves same-word separation +0.50 on FSDD (clean isolated spans) but
only +0.10 on LibriSpeech words cut by PROPORTIONAL alignment (the agent's noisy
segmentation). Is the +0.10 ceiling the REPRESENTATION's limit, or is it the
SEGMENTATION (proportional spans don't actually contain the word)?

This script gives the SSL model CORRECT word boundaries (forced word timestamps
from faster-whisper) and re-measures separation on the SAME utterances. If sep
jumps toward FSDD's +0.5 with gold spans, the bottleneck is provably SEGMENTATION
ACCURACY, not the representation — the portable insight is "get the boundary
right", which the agent can attack with its DSP/landmark tools, not a big net.

Run: python -m scripts.mine_ssl_goldspan [model] [n_spk] [utts_per_spk]
"""
import os
import sys
import time
import random
from collections import defaultdict

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import torch
import librosa

import scripts.sentence_learning as SL
from scripts.continuous_speech_recognition import words_of
from scripts.mine_ssl_chunk_consistency import (
    SSL, SR, load16k, separation, shuffle_sep, nn_acc, _word_frame_spans,
    libri_items,
)

torch.set_num_threads(max(1, os.cpu_count() // 2))


def gold_spans(wmodel, path):
    """faster-whisper word timestamps -> list of (word, t0, t1) in seconds."""
    segs, _ = wmodel.transcribe(path, word_timestamps=True, language="en",
                                beam_size=1)
    out = []
    for s in segs:
        for w in (s.words or []):
            tok = "".join(ch for ch in w.word.lower() if ch.isalpha() or ch == "'")
            if tok:
                out.append((tok, w.start, w.end))
    return out


def main():
    key = sys.argv[1] if len(sys.argv) > 1 else "wav2vec2"
    n_spk = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    utts = int(sys.argv[3]) if len(sys.argv) > 3 else 14
    random.seed(1)
    np.random.seed(1)

    from faster_whisper import WhisperModel
    wmodel = WhisperModel("tiny", device="cpu", compute_type="int8")
    ssl = SSL(key)
    print(f"=== GOLD-SPAN control: {ssl.name} + faster-whisper word timestamps ===")

    sel = libri_items(n_spk, utts)
    print(f"  {len(sel)} utterances, {n_spk} speakers")

    # Build BOTH chunk sets from the SAME utterances:
    #   PROP  = proportional spans (agent's noisy segmentation)
    #   GOLD  = forced word-timestamp spans (correct boundaries)
    # Represent each at a fixed layer (7, the in-context peak) AND layer 0.
    LAYERS = [0, 7]
    prop = {li: [] for li in LAYERS}
    gold = {li: [] for li in LAYERS}
    t0 = time.time()
    n_used = 0
    for path, sp, ch, ut, transcript in sel:
        try:
            x = load16k(path)
        except Exception:
            continue
        if len(x) < SR // 4:
            continue
        L = ssl.layers(x)
        nf = L[0].shape[0]
        # proportional spans from the TRUE transcript words
        twords = words_of(transcript)
        if not twords:
            continue
        pspans = _word_frame_spans(twords, nf)
        for li in LAYERS:
            for w, (a, b) in zip(twords, pspans):
                if len(w) >= 3 and b - a >= 2:
                    prop[li].append((L[li][a:b], w, sp))
        # gold spans from forced word timestamps; frame = 50 Hz (20 ms)
        try:
            gs = gold_spans(wmodel, path)
        except Exception:
            gs = []
        for w, ts, te in gs:
            fa = int(round(ts * 50.0))
            fb = int(round(te * 50.0))
            fa = max(0, min(fa, nf - 1))
            fb = max(fa + 1, min(fb, nf))
            for li in LAYERS:
                if len(w) >= 3 and fb - fa >= 2:
                    gold[li].append((L[li][fa:fb], w, sp))
        n_used += 1
    print(f"  processed {n_used} utts ({time.time()-t0:.0f}s); "
          f"prop segs {len(prop[7])}, gold segs {len(gold[7])}")

    print("\n  representation              within-sep   shuf   x-spk-sep   NN-within")
    for tag, store in [("PROP layer0", prop[0]), ("PROP layer7", prop[7]),
                       ("GOLD layer0", gold[0]), ("GOLD layer7", gold[7])]:
        sep, im, xm, n, _ = separation(store, cross=False)
        sh = shuffle_sep(store, cross=False)
        xsep, _, _, _, _ = separation(store, cross=True)
        acc, na = nn_acc(store, within=True, max_q=120)
        print(f"  {tag:<24}{sep:>+9.3f}{sh:>+8.3f}{xsep:>+11.3f}{acc:>10.3f}"
              f"  (n_intra={n}, nn_n={na})")

    print("\n  INTERPRETATION:")
    print("  If GOLD layer7 sep >> PROP layer7 sep, the chunk-consistency")
    print("  bottleneck is SEGMENTATION ACCURACY, not the representation —")
    print("  the same trained features become consistent once the SPAN is right.")


if __name__ == "__main__":
    main()

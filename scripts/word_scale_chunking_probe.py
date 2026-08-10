"""word_scale_chunking_probe — measure the agent's forward-built LOCAL-MINIMUM
boundary rule against the original MEDIAN rule on REAL continuous speech.

Iteration-3 of the autopoietic loop. The agent's ranker (with the loop gap fixed —
see docs/agent_loop_iteration3.md) advances past the already-built clustering to
WORD-SCALE CHUNKING, the actual continuous-speech recognition loss: the TP-trough
chunker over-segments ~8x (chunks-per-word 7.71, chunk->word lexicon purity 0.179;
CONTINUOUS_SPEECH_FINDINGS.md). The agent forward-built a fix from the SAME
statistical_learning science, read more faithfully: a word boundary is a LOCAL
MINIMUM of TP (a genuine trough, TP below BOTH neighbours), not merely any
below-median transition. The median rule cuts ~half of all transitions; local-min
cuts only at true dips.

This is a WORLD ADAPTER: it ingests LibriSpeech audio, runs the agent's own
perception + invariant transform + codebook + graph-resident forward chunker in
BOTH boundary modes (the boundary DECISION is the agent's Term, evaluated natively),
grounds chunks to transcript words, and reports chunks-per-word + lexicon purity for
each mode. No new agent reasoning lives in Python.

Run:  python -m scripts.word_scale_chunking_probe [n_train] [n_speakers] [K]
"""
from __future__ import annotations

import os
import sys
import time
import random

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np

import scripts.sentence_learning as SL
from scripts.invariant_units_accept import band_trajectory_matrix
from domains.invariant_units import invariant_transform, canonical_log_centroid
from substrate_rs import Substrate

# reuse the recognition script's mechanical helpers (perception/codebook/lexicon)
import scripts.continuous_speech_recognition as CSR


def chunk_an_utterance_mode(sub, M, C, mode):
    """Same as CSR.chunk_an_utterance but threads the boundary mode through the
    agent's forward chunker (the boundary Term it evaluates natively)."""
    units = CSR.quantize(M, C)
    res = CSR.forward_segment(sub, [units], n_passes=1, boundary_mode=mode)
    chunked = res["chunked"]
    if not chunked or chunked[0] is None:
        return [(M, M.shape[0])]
    lengths = [CSR._flat_len(c) for c in chunked[0]]
    blocks, idx = [], 0
    for L in lengths:
        if L <= 0:
            continue
        blocks.append((M[idx:idx + L], L))
        idx += L
    if idx < M.shape[0]:
        if blocks:
            last_M, last_L = blocks[-1]
            blocks[-1] = (M[idx - last_L:], M.shape[0] - (idx - last_L))
        else:
            blocks.append((M, M.shape[0]))
    return blocks if blocks else [(M, M.shape[0])]


def ground_and_score(train_inv, C, mode):
    """Chunk every train utterance in `mode`, ground chunks to transcript words,
    build the DTW lexicon, return chunks-per-word ratio + purity stats."""
    sub = Substrate()
    lex = CSR.Lexicon()
    chunk_counts, word_counts = [], []
    t0 = time.time()
    for ci, (M, words) in enumerate(train_inv):
        blocks = chunk_an_utterance_mode(sub, M, C, mode)
        lengths = [L for _, L in blocks]
        aligned = CSR.align_chunks_to_words(lengths, words)
        chunk_counts.append(len(blocks))
        word_counts.append(len(words))
        for (block, _L), w in zip(blocks, aligned):
            lex.add_train_chunk(block, w)
        if (ci + 1) % 25 == 0:
            print(f"    [{mode}] grounded {ci+1}/{len(train_inv)}  "
                  f"protos={len(lex.protos)}  ({time.time()-t0:.0f}s)", flush=True)
    lex.finalize()
    tot_c, tot_w = sum(chunk_counts), sum(word_counts)
    ps = lex.purity()
    return {
        "chunks_per_word": tot_c / max(tot_w, 1),
        "total_chunks": tot_c, "total_words": tot_w,
        "n_protos": len(lex.protos),
        "words_covered": len(set(lex.labels)),
        "purity": ps["purity"],
        "singleton_frac": ps["singleton_frac"],
        "multi_purity": ps["multi_purity"],
        "multi_chunks": ps["multi_chunks"],
    }


def main():
    n_train = int(sys.argv[1]) if len(sys.argv) > 1 else 120
    n_speakers = int(sys.argv[2]) if len(sys.argv) > 2 else 24
    K = int(sys.argv[3]) if len(sys.argv) > 3 else 48
    random.seed(1)

    pairs = SL.gather_pairs()
    all_speakers = sorted(set(p[1] for p in pairs))[:n_speakers]
    n_held = max(2, len(all_speakers) // 5)
    train_spk = set(all_speakers[n_held:])
    train_pairs = [p for p in pairs if p[1] in train_spk]
    random.shuffle(train_pairs)
    train_pairs = train_pairs[:n_train]
    print(f"LibriSpeech dev-clean: {len(pairs)} utts; "
          f"TRAIN {len(train_pairs)} utts / {len(train_spk)} speakers; K={K}")

    print("\nPerception + framing + invariant transform (the agent's default)...")
    train_raw = []
    t0 = time.time()
    for i, (path, sp, ch, ut, transcript) in enumerate(train_pairs):
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
        train_raw.append((M, words))
        if (i + 1) % 50 == 0:
            print(f"  framed {i+1}/{len(train_pairs)} ({time.time()-t0:.0f}s)",
                  flush=True)
    if len(train_raw) < 5:
        print("Too few usable utterances — aborting.")
        return

    canonical = canonical_log_centroid([M for M, _ in train_raw])
    train_inv = [(invariant_transform(M, canonical), w) for M, w in train_raw]
    pool = np.concatenate([M for M, _ in train_inv], axis=0)
    if len(pool) > 12000:
        pool = pool[np.random.default_rng(0).choice(len(pool), 12000,
                                                    replace=False)]
    print(f"k-means codebook over {len(pool)} train frames, K={K}...")
    C = CSR.kmeans(pool, K, seed=0)

    print("\n[MEASURE] MEDIAN boundary (original) ...")
    med = ground_and_score(train_inv, C, "median")
    print("[MEASURE] LOCAL-MIN boundary (agent forward-built fix) ...")
    lm = ground_and_score(train_inv, C, "local_min")

    print("\n" + "=" * 70)
    print("WORD-SCALE CHUNKING — median vs local-min boundary (live, LibriSpeech)")
    print("=" * 70)
    hdr = f"{'metric':<28}{'MEDIAN (old)':>16}{'LOCAL-MIN (new)':>18}"
    print(hdr)
    print("-" * len(hdr))
    rows = [
        ("chunks-per-word (->1.0)", "chunks_per_word", "{:.2f}"),
        ("total chunks", "total_chunks", "{:d}"),
        ("total words", "total_words", "{:d}"),
        ("chunk prototypes", "n_protos", "{:d}"),
        ("words covered", "words_covered", "{:d}"),
        ("cluster purity (->1.0)", "purity", "{:.3f}"),
        ("  singleton frac", "singleton_frac", "{:.3f}"),
        ("  MULTI-member purity", "multi_purity", "{:.3f}"),
        ("  multi chunks", "multi_chunks", "{:d}"),
    ]
    for label, key, fmt in rows:
        print(f"{label:<28}{fmt.format(med[key]):>16}{fmt.format(lm[key]):>18}")
    print("-" * len(hdr))
    print(f"\nBASELINE (CONTINUOUS_SPEECH_FINDINGS.md): chunks-per-word 7.71, "
          f"purity 0.179, multi-purity 0.160")
    print(f"DELTA chunks-per-word: {med['chunks_per_word']:.2f} -> "
          f"{lm['chunks_per_word']:.2f}")
    print(f"DELTA purity:          {med['purity']:.3f} -> {lm['purity']:.3f}")


if __name__ == "__main__":
    main()

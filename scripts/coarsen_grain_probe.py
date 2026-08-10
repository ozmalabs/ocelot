"""coarsen_grain_probe — measure the agent's forward-built RUN-LENGTH COLLAPSE
(coarsen the unit grain BEFORE chunking) on REAL continuous speech.

Iteration-4 of the autopoietic loop. Iteration-3 located the binding constraint by
live measurement: the per-frame unit stream is ~7.5 units/word (frames/word grain
7.56), so the TP-trough chunker — median OR the local-min Term the agent
forward-built — sticks near ~7 chunks/word no matter how sharp the boundary rule
is, because it inherits the GRAIN. The agent's diagnosis (docs/agent_loop_iteration3
§3): coarsen the unit grain (run-length collapse) BEFORE chunking. domains/
run_length_collapse builds that: a graph-resident run-start Term merges consecutive
same-unit (raw-id) or low-step (stability) frames into one coarser unit.

This is a WORLD ADAPTER. It ingests LibriSpeech, runs the agent's own perception +
invariant transform + codebook, then for each condition measures:
  • units-per-word / frames-per-word BEFORE vs AFTER collapse (the grain);
  • chunks-per-word after the TP chunker runs on the (coarsened) stream;
  • chunk->word lexicon purity (DTW-merged prototypes, majority word).
Conditions: PER-FRAME (no collapse, the iter-3 state), RAW-ID collapse, STABILITY
collapse — each then chunked with the agent's local-min boundary Term. No new agent
reasoning lives in Python; the collapse + boundary DECISIONS are the agent's Terms.

Run:  python -m scripts.coarsen_grain_probe [n_train] [n_speakers] [K]
"""
from __future__ import annotations

import os
import sys
import time
import random

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np

import scripts.sentence_learning as SL
from domains.invariant_units import invariant_transform, canonical_log_centroid
from substrate_rs import Substrate

import scripts.continuous_speech_recognition as CSR
from domains.run_length_collapse import collapse_stream


# ---------------------------------------------------------------------------
# One utterance -> coarse-unit blocks, threading run-length collapse before the
# agent's local-min TP chunker. Returns (frame_blocks, n_frames) per chunk, plus
# the per-utterance grain numbers so we can aggregate the GRAIN as well as chunks.
# ---------------------------------------------------------------------------

def chunk_with_collapse(sub, M, C, collapse_mode):
    """M (frames x bands) -> per-frame units -> [optional run-length collapse] ->
    agent local-min TP chunker -> list of (frame_block, n_frames). collapse_mode is
    'none' (per-frame, iter-3), 'raw_id', or 'stability'. Returns (blocks, info)
    where info carries n_frames, n_units (post-collapse), n_chunks for the grain."""
    units = CSR.quantize(M, C)
    n_frames = len(units)

    if collapse_mode == "none":
        # iter-3 state: chunk the raw per-frame unit stream directly.
        res = CSR.forward_segment(sub, [units], n_passes=1, boundary_mode="local_min")
        chunked = res["chunked"]
        frame_lengths_per_unit = [1] * n_frames     # each unit spans 1 frame
        coarse_units = units
    else:
        seq_tag = f"col_{collapse_mode}_{id(M) & 0xffffff}"
        col = collapse_stream(sub, units, seq_tag, mode=collapse_mode, M=M)
        coarse_units = col["coarse_ids"]
        frame_lengths_per_unit = col["lengths"]     # frames each coarse unit spans
        # chunk the COARSENED stream (the agent's TP chunker on coarse units).
        res = CSR.forward_segment(sub, [coarse_units], n_passes=1,
                                  boundary_mode="local_min")
        chunked = res["chunked"]

    n_units = len(coarse_units)
    if not chunked or chunked[0] is None:
        return [(M, n_frames)], {"n_frames": n_frames, "n_units": n_units,
                                 "n_chunks": 1}

    # each chunk spans some number of COARSE units; map that back to a FRAME span
    # via the per-coarse-unit frame lengths (so the prototype is real audio frames).
    chunk_unit_lengths = [CSR._flat_len(c) for c in chunked[0]]
    blocks = []
    unit_idx = 0
    frame_idx = 0
    for cu_len in chunk_unit_lengths:
        if cu_len <= 0:
            continue
        # frames spanned = sum of the frame-lengths of the coarse units in this chunk
        fl = sum(frame_lengths_per_unit[unit_idx:unit_idx + cu_len])
        fl = max(1, fl)
        blocks.append((M[frame_idx:frame_idx + fl], fl))
        unit_idx += cu_len
        frame_idx += fl
    if frame_idx < n_frames and blocks:            # trailing frames -> last chunk
        last_M, last_L = blocks[-1]
        blocks[-1] = (M[frame_idx - last_L:], n_frames - (frame_idx - last_L))
    if not blocks:
        blocks = [(M, n_frames)]
    return blocks, {"n_frames": n_frames, "n_units": n_units,
                    "n_chunks": len(blocks)}


def ground_and_score(train_inv, C, collapse_mode):
    """Chunk every train utterance under collapse_mode, ground chunks to transcript
    words, build the DTW lexicon, return grain + chunks-per-word + purity stats."""
    sub = Substrate()
    lex = CSR.Lexicon()
    tot_frames = tot_units = tot_chunks = tot_words = 0
    t0 = time.time()
    for ci, (M, words) in enumerate(train_inv):
        blocks, info = chunk_with_collapse(sub, M, C, collapse_mode)
        lengths = [L for _, L in blocks]
        aligned = CSR.align_chunks_to_words(lengths, words)
        tot_frames += info["n_frames"]
        tot_units += info["n_units"]
        tot_chunks += len(blocks)
        tot_words += len(words)
        for (block, _L), w in zip(blocks, aligned):
            lex.add_train_chunk(block, w)
        if (ci + 1) % 25 == 0:
            print(f"    [{collapse_mode}] grounded {ci+1}/{len(train_inv)}  "
                  f"protos={len(lex.protos)}  ({time.time()-t0:.0f}s)", flush=True)
    lex.finalize()
    ps = lex.purity()
    w = max(tot_words, 1)
    return {
        "frames_per_word": tot_frames / w,
        "units_per_word": tot_units / w,          # the GRAIN after collapse
        "chunks_per_word": tot_chunks / w,
        "total_units": tot_units, "total_chunks": tot_chunks,
        "total_words": tot_words,
        "n_protos": len(lex.protos),
        "words_covered": len(set(lex.labels)),
        "purity": ps["purity"],
        "singleton_frac": ps["singleton_frac"],
        "multi_purity": ps["multi_purity"],
        "multi_chunks": ps["multi_chunks"],
    }


def main():
    n_train = int(sys.argv[1]) if len(sys.argv) > 1 else 60
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

    print("\n[MEASURE] PER-FRAME (no collapse, iter-3 state) ...")
    pf = ground_and_score(train_inv, C, "none")
    print("[MEASURE] RAW-ID run-length collapse (agent's primary) ...")
    rid = ground_and_score(train_inv, C, "raw_id")
    print("[MEASURE] STABILITY run-length collapse (order-1 refinement) ...")
    stab = ground_and_score(train_inv, C, "stability")

    print("\n" + "=" * 78)
    print("COARSEN-GRAIN — per-frame vs run-length collapse (live, LibriSpeech)")
    print("=" * 78)
    hdr = (f"{'metric':<28}{'PER-FRAME':>14}{'RAW-ID':>13}{'STABILITY':>13}")
    print(hdr)
    print("-" * len(hdr))
    rows = [
        ("units-per-word (grain)", "units_per_word", "{:.2f}"),
        ("frames-per-word", "frames_per_word", "{:.2f}"),
        ("chunks-per-word (->1-3)", "chunks_per_word", "{:.2f}"),
        ("total units", "total_units", "{:d}"),
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
        print(f"{label:<28}{fmt.format(pf[key]):>14}"
              f"{fmt.format(rid[key]):>13}{fmt.format(stab[key]):>13}")
    print("-" * len(hdr))
    print(f"\nBASELINE (iter-3, docs/agent_loop_iteration3.md): grain 7.56, "
          f"chunks-per-word 7.07, purity 0.29 (iter-1 0.179)")
    print(f"DELTA grain (units/word):  {pf['units_per_word']:.2f} -> "
          f"raw-id {rid['units_per_word']:.2f}  /  stability "
          f"{stab['units_per_word']:.2f}")
    print(f"DELTA chunks-per-word:     {pf['chunks_per_word']:.2f} -> "
          f"raw-id {rid['chunks_per_word']:.2f}  /  stability "
          f"{stab['chunks_per_word']:.2f}")
    print(f"DELTA purity:              {pf['purity']:.3f} -> "
          f"raw-id {rid['purity']:.3f}  /  stability {stab['purity']:.3f}")


if __name__ == "__main__":
    main()

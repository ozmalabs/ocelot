"""iter8_lexicon_compare — apples-to-apples comparison of the chunk->word LEXICON
builder at the recognition stage: the iter-4 GREEDY DTW-merge vs the agent's
forward-built CROSS-SPEAKER CHUNK CLUSTERING (domains/cross_speaker_clustering,
the composed Argmin/Sum-Count clusterer lifted from frames to chunk-trajectories).

This is a WORLD ADAPTER. It reuses scripts.continuous_speech_recognition's own
perception + invariant transform + codebook + chunker (no new agent reasoning),
frames the corpus ONCE (perception is the dominant cost, ~5 s/utt), then builds and
scores BOTH lexicons on the SAME train/test chunks. Reports, for each mode:
  - chunk->word lexicon purity + MULTI-member purity (the honest cross-speaker number)
  - chunks-per-word
  - WORD ACCURACY + WER vs the UNIGRAM baseline (and chance)

No tuning to a number. The cluster k = distinct train words (one cluster per word,
the natural target). Held-out SPEAKERS (speaker-independent).

Run: python -m scripts.iter8_lexicon_compare [n_train] [n_test] [n_speakers] [K]
"""
import os
import sys
import time
import random
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np

import scripts.sentence_learning as SL
import scripts.continuous_speech_recognition as CSR
from domains.invariant_units import invariant_transform, canonical_log_centroid
from substrate_rs import Substrate

# Default to the coarser (word-er) chunks — the agent's stability run-length collapse.
os.environ.setdefault("COLLAPSE_MODE", "stability")
os.environ.setdefault("BOUNDARY_MODE", "local_min")


def score_mode(name, sub, C, train_chunks, test_chunks, train_word_freq):
    """train_chunks/test_chunks: list of (utt_blocks, words). Build the named lexicon,
    score it. Returns a dict of metrics."""
    if name == "greedy":
        lex = CSR.Lexicon()
        for blocks, words in train_chunks:
            lengths = [L for _, L in blocks]
            aligned = CSR.align_chunks_to_words(lengths, words)
            for (block, _L), w in zip(blocks, aligned):
                lex.add_train_chunk(block, w)
        lex.finalize()
        n_proto = len(lex.protos)
    else:  # cluster
        distinct = len(train_word_freq)
        n_iters = int(os.environ.get("CLUSTER_ITERS", "25"))
        lex = CSR.ClusterLexicon(n_clusters=max(2, distinct), n_iters=n_iters,
                                 seed=0)
        for blocks, words in train_chunks:
            lengths = [L for _, L in blocks]
            aligned = CSR.align_chunks_to_words(lengths, words)
            for (block, _L), w in zip(blocks, aligned):
                lex.add_train_chunk(block, w)
        t0 = time.time()
        lex.finalize()
        print(f"    [{name}] clustered in {time.time()-t0:.0f}s", flush=True)
        n_proto = len(lex.centroids)

    pstats = lex.purity()

    # chunks-per-word
    tot_chunks = sum(len(b) for b, _ in train_chunks)
    tot_words = sum(len(w) for _, w in train_chunks)
    ratio = tot_chunks / max(tot_words, 1)

    # recognition
    unigram_word = max(train_word_freq.items(), key=lambda kv: kv[1])[0]
    distinct_train_words = len(train_word_freq)
    all_train_words = list(train_word_freq.keys())
    rng = random.Random(7)
    sum_wer = sum_wer_uni = sum_wer_chance = 0.0
    word_hits = word_total = uni_word_hits = 0
    n_eval = 0
    for blocks, words in test_chunks:
        hyp = []
        for block, _L in blocks:
            w = lex.lookup(block)
            if w is not None:
                hyp.append(w)
        collapsed = []
        for w in hyp:
            if not collapsed or collapsed[-1] != w:
                collapsed.append(w)
        hyp = collapsed
        sum_wer += CSR.wer(words, hyp)
        sum_wer_uni += CSR.wer(words, [unigram_word] * len(words))
        sum_wer_chance += CSR.wer(words, [rng.choice(all_train_words)
                                          for _ in words])
        for j, tw in enumerate(words):
            word_total += 1
            if j < len(hyp) and hyp[j] == tw:
                word_hits += 1
            if tw == unigram_word:
                uni_word_hits += 1
        n_eval += 1

    return {
        "name": name, "n_proto": n_proto,
        "purity": pstats["purity"], "multi_purity": pstats["multi_purity"],
        "singleton_frac": pstats["singleton_frac"],
        "multi_chunks": pstats["multi_chunks"],
        "chunks_per_word": ratio,
        "wer": sum_wer / max(n_eval, 1),
        "wer_uni": sum_wer_uni / max(n_eval, 1),
        "wer_chance": sum_wer_chance / max(n_eval, 1),
        "word_acc": word_hits / max(word_total, 1),
        "uni_word_acc": uni_word_hits / max(word_total, 1),
        "chance_word_acc": 1.0 / max(distinct_train_words, 1),
        "word_total": word_total, "word_hits": word_hits,
        "unigram_word": unigram_word,
    }


def main():
    n_train = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    n_test = int(sys.argv[2]) if len(sys.argv) > 2 else 12
    n_speakers = int(sys.argv[3]) if len(sys.argv) > 3 else 16
    K = int(sys.argv[4]) if len(sys.argv) > 4 else 48
    random.seed(1)

    pairs = SL.gather_pairs()
    all_speakers = sorted(set(p[1] for p in pairs))[:n_speakers]
    n_held = max(2, len(all_speakers) // 5)
    test_spk = set(all_speakers[:n_held])
    train_spk = set(all_speakers[n_held:])
    train_pairs = [p for p in pairs if p[1] in train_spk]
    test_pairs = [p for p in pairs if p[1] in test_spk]
    random.shuffle(train_pairs)
    random.shuffle(test_pairs)
    train_pairs = train_pairs[:n_train]
    test_pairs = test_pairs[:n_test]
    print(f"COLLAPSE_MODE={os.environ['COLLAPSE_MODE']}  K={K}")
    print(f"TRAIN {len(train_pairs)} utts / {len(train_spk)} spk   "
          f"TEST {len(test_pairs)} utts / {len(test_spk)} HELD-OUT spk")

    sub = Substrate()

    def frame_utts(pairlist, tag):
        out = []
        t0 = time.time()
        for i, (path, sp, ch, ut, transcript) in enumerate(pairlist):
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
            out.append((M, words))
            if (i + 1) % 20 == 0:
                print(f"  [{tag}] framed {i+1}/{len(pairlist)} "
                      f"({time.time()-t0:.0f}s)", flush=True)
        return out

    print("\nPerception + framing (ONCE, shared by both modes)...")
    train_raw = frame_utts(train_pairs, "train")
    test_raw = frame_utts(test_pairs, "test")

    canonical = canonical_log_centroid([M for M, _ in train_raw])
    train_inv = [(invariant_transform(M, canonical), w) for M, w in train_raw]
    test_inv = [(invariant_transform(M, canonical), w) for M, w in test_raw]

    pool = np.concatenate([M for M, _ in train_inv], axis=0)
    if len(pool) > 12000:
        pool = pool[np.random.default_rng(0).choice(len(pool), 12000, False)]
    C = CSR.kmeans(pool, K, seed=0)

    # Chunk every utterance ONCE (shared). iter-9: CORPUS_TP=1 estimates the TP
    # structure over the WHOLE train corpus (statistical_learning science) so the
    # chunker reads real word boundaries -> word-scale chunks (constraint b).
    print(f"\nChunking (shared, CORPUS_TP={CSR.CORPUS_TP})...")
    if CSR.CORPUS_TP:
        from domains.forward_segmentation import estimate_tp, _median
        coarse = {}
        all_streams = []
        for M, _w in train_inv:
            cids, flens = CSR.coarse_stream_of(sub, M, C)
            coarse[id(M)] = (cids, flens)
            all_streams.append(cids)
        ctp = estimate_tp(all_streams)
        clevel = _median(ctp.values())
        print(f"  corpus-TP: {len(ctp)} bigrams, median level={clevel:.3f}")

        def _chunk(M):
            cached = coarse.get(id(M))
            cids, flens = cached if cached else CSR.coarse_stream_of(sub, M, C)
            return CSR.chunk_with_corpus_tp(sub, M, cids, flens, ctp, clevel,
                                            f"cmp_{id(M) & 0xffffff}")
        train_chunks = [(_chunk(M), w) for M, w in train_inv]
        test_chunks = [(_chunk(M), w) for M, w in test_inv]
    else:
        train_chunks = [(CSR.chunk_an_utterance(sub, M, C), w) for M, w in train_inv]
        test_chunks = [(CSR.chunk_an_utterance(sub, M, C), w) for M, w in test_inv]

    train_word_freq = defaultdict(int)
    for _, words in train_inv:
        for w in words:
            train_word_freq[w] += 1

    print("\nBuilding + scoring both lexicons on the SAME chunks...")
    results = []
    for mode in ("greedy", "cluster"):
        print(f"  [{mode}] ...", flush=True)
        results.append(score_mode(mode, sub, C, train_chunks, test_chunks,
                                  train_word_freq))

    print("\n" + "=" * 78)
    print("LEXICON COMPARISON — greedy DTW-merge (iter-4) vs agent cross-speaker "
          "chunk clustering")
    print("=" * 78)
    hdr = (f"{'mode':<10}{'purity':>8}{'multi':>8}{'sing%':>7}"
           f"{'chk/wd':>8}{'WER':>8}{'word-acc':>10}{'#clust':>8}")
    print(hdr)
    print("-" * 78)
    for r in results:
        print(f"{r['name']:<10}{r['purity']:>8.3f}{r['multi_purity']:>8.3f}"
              f"{r['singleton_frac']:>7.2f}{r['chunks_per_word']:>8.2f}"
              f"{r['wer']:>8.3f}{r['word_acc']:>10.3f}{r['n_proto']:>8}")
    r0 = results[0]
    print("-" * 78)
    print(f"{'unigram':<10}{'':>8}{'':>8}{'':>7}{'':>8}"
          f"{r0['wer_uni']:>8.3f}{r0['uni_word_acc']:>10.3f}"
          f"  (word='{r0['unigram_word']}')")
    print(f"{'chance':<10}{'':>8}{'':>8}{'':>7}{'':>8}"
          f"{r0['wer_chance']:>8.3f}{r0['chance_word_acc']:>10.4f}")

    print("\n" + "=" * 78)
    print("VERDICT")
    print("=" * 78)
    g = results[0]
    c = results[1]
    print(f"purity   greedy {g['purity']:.3f} (multi {g['multi_purity']:.3f})  ->  "
          f"cluster {c['purity']:.3f} (multi {c['multi_purity']:.3f})")
    print(f"word-acc greedy {g['word_acc']:.3f}  cluster {c['word_acc']:.3f}  "
          f"unigram {g['uni_word_acc']:.3f}")
    print(f"WER      greedy {g['wer']:.3f}  cluster {c['wer']:.3f}  "
          f"unigram {g['wer_uni']:.3f}")
    crossed = c['word_acc'] > g['uni_word_acc'] and c['word_acc'] > 0.02
    print(f"\n>>> cluster lexicon CROSSES unigram word-acc: "
          f"{'YES' if crossed else 'NO'} "
          f"(cluster {c['word_acc']:.3f} vs unigram {g['uni_word_acc']:.3f})")


if __name__ == "__main__":
    main()

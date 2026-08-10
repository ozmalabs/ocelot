"""iter-13 — carry the per-speaker CMVN invariance fix from FSDD DIGITS to
CONTINUOUS SPEECH (LibriSpeech), and test whether it switches on the original
last link: the continuous-speech chunk->word lexicon.

THE LEVER (confirmed, iter-12, FSDD digits). domains/xspeaker_norm.py: per-speaker
CMVN = estimate the test speaker's mean+std log-spectrum (the speaker embedding)
from THEIR OWN unlabelled audio across their utterances, subtract it from every
frame -> speaker-invariant features. On FSDD it took cross-speaker full-DTW
0.588 -> 0.802 (shuffle 0.06) and LOSO held-out-speaker digit recognition to
0.785 vs unigram 0.100.

The continuous-speech pipeline (scripts/continuous_speech_recognition.py) used
the per-UTTERANCE invariant_transform. This probe swaps in the per-SPEAKER
normalisation as the front-end, BEFORE the codebook/chunking, then runs the
existing forward chain (corpus-TP word-scale chunking -> cross-speaker chunk->word
lexicon -> recognise held-out speakers).

MEASURE (live, fast probe first, then recognition):
  (1) WITHIN/CROSS full-DTW on continuous-speech CHUNKS (held-out speakers):
      does per-speaker CMVN close the cross-speaker gap on continuous chunks like
      it did on FSDD digits? before(per-utterance invariant_transform) ->
      after(per-speaker CMVN), shuffle-controlled. The fast inner test that the
      invariance CARRIES.
  (2) IF it carries: lexicon purity + recognition word-acc / WER vs unigram on
      HELD-OUT SPEAKERS. Does the continuous last link CROSS unigram?

The per-speaker statistics are estimated AT TEST TIME from each speaker's own
(unlabelled) audio (the I/O boundary the task allows). No labels, no search, no
tuning. World-adapter only: it wires the agent's own builds and reports numbers.

Run:  python -m scripts.iter13_continuous_xspeaker [n_speakers] [utts_per_spk]
                                                    [chunks_for_probe]
"""
import os
import re
import sys
import time
import random
from collections import defaultdict, Counter

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import scripts.sentence_learning as SL
from scripts.invariant_units_accept import band_trajectory_matrix
from domains.invariant_units import invariant_transform, canonical_log_centroid
import domains.invariant_units as IU
import domains.xspeaker_norm as XN
from scripts.continuous_speech_recognition import (
    words_of, frames_of, kmeans, dtw, chunk_an_utterance, chunk_with_corpus_tp,
    coarse_stream_of, align_chunks_to_words, wer, ClusterLexicon, Lexicon,
)
from substrate_rs import Substrate


# --------------------------------------------------------------------------
# perception: frame every utterance once (raw band matrices), keep speaker id.
# --------------------------------------------------------------------------

def frame_corpus(pairs, max_frames_msg=False):
    """pairs = (path, sp, ch, ut, transcript) -> [(M_raw, words, speaker)].
    Framing (gammatone front-end) is the dominant cost (~0.7s/utt) and is purely
    a function of the audio, so cache the framed corpus to /tmp keyed by the
    selected paths — re-runs of the probe (which tune nothing in the audio) are
    then near-instant. Caching the I/O-boundary output only; no agent state."""
    import hashlib
    import pickle
    key = hashlib.sha1(
        "|".join(sorted(p[0] for p in pairs)).encode()).hexdigest()[:16]
    cache = f"/tmp/iter13_frames_{key}.pkl"
    if os.path.exists(cache):
        try:
            with open(cache, "rb") as f:
                return pickle.load(f)
        except Exception:
            pass
    out = []
    for path, sp, ch, ut, transcript in pairs:
        words = words_of(transcript)
        if not words:
            continue
        try:
            x, fs = SL.load_flac_8k(path)
        except Exception:
            continue
        M = frames_of(x, fs)
        if M.shape[0] < 4:
            continue
        out.append((M, words, sp))
    try:
        with open(cache, "wb") as f:
            pickle.dump(out, f)
    except Exception:
        pass
    return out


# --------------------------------------------------------------------------
# front-ends: per-UTTERANCE invariant_transform (the BEFORE) vs per-SPEAKER
# CMVN (the AFTER). Both return [(M_norm, words, speaker)].
# --------------------------------------------------------------------------

def _front_end_cache_key(raw, canonical, tag):
    """Deterministic key for a front-end output = the audio frames + canonical +
    the front-end tag. Caching the I/O-boundary transform output only (no agent
    state). The transform is deterministic, so this is pure memoisation."""
    import hashlib
    h = hashlib.sha1()
    h.update(f"{tag}|{canonical:.6f}|".encode())
    for M, w, s in raw:
        h.update(str(s).encode())
        h.update(np.ascontiguousarray(M, dtype=np.float32).tobytes())
    return f"/tmp/iter13_fe_{h.hexdigest()[:16]}.pkl"


def _cached_front_end(raw, canonical, tag, compute):
    """The agent's predict-remove Term (apply_predict_remove) is evaluated
    natively per frame per band and is the dominant cost (~4s per long
    LibriSpeech utterance). The transform output is deterministic in the audio,
    so memoise it to /tmp — the BEFORE/AFTER/shuffle probe stages then reuse one
    computation instead of re-running the agent's Term machinery each time."""
    import pickle
    cache = _front_end_cache_key(raw, canonical, tag)
    if os.path.exists(cache):
        try:
            with open(cache, "rb") as f:
                return pickle.load(f)
        except Exception:
            pass
    out = compute()
    try:
        with open(cache, "wb") as f:
            pickle.dump(out, f)
    except Exception:
        pass
    return out


def apply_per_utterance(raw, canonical):
    return _cached_front_end(
        raw, canonical, "per_utt",
        lambda: [(invariant_transform(M, canonical), w, s) for M, w, s in raw])


def apply_per_speaker(raw, canonical, variant="uVTLN+ps_CMVN+PR"):
    """Per-speaker CMVN front-end. Per-speaker stats pooled from each speaker's
    OWN frames (label-free, test-time). variant selects which XN method:
      uVTLN+ps_CMVN+PR   : per-utt VTLN + per-SPEAKER CMVN + predict-remove
      ps_CMVN_only+PR    : per-SPEAKER CMVN only (no VTLN) + predict-remove
      ps_VTLN+ps_CMVN+PR : per-speaker VTLN + per-speaker CMVN + predict-remove."""
    def compute():
        corpus = [(M, w, s) for M, w, s in raw]
        fns = XN.methods(canonical, corpus)
        fn = fns[variant]
        return [(fn(M, s), w, s) for M, w, s in raw]
    return _cached_front_end(raw, canonical, f"ps_{variant}", compute)


# --------------------------------------------------------------------------
# WITHIN/CROSS full-DTW on continuous CHUNKS (the fast inner test).
# We chunk every held-out-speaker utterance into word-scale chunks (corpus-TP),
# label each chunk by its proportional-aligned transcript word, then for each
# chunk find its nearest WITHIN-speaker and nearest CROSS-speaker neighbour by
# full-resolution DTW and ask if it carries the same word. Chance = 1/n_words.
# This mirrors the iter-12 metric exactly, at the CHUNK granularity.
# --------------------------------------------------------------------------

def chunk_one(M, C, corpus_tp, corpus_level, tag):
    """Chunk ONE utterance into real-frame blocks via the agent's graph boundary
    Term, using a FRESH Substrate per utterance. CRUCIAL for continuous speech:
    chunk_with_corpus_tp installs this utterance's Transition nodes into the
    substrate and sub.evaluate rescans the whole graph; reusing one substrate
    across hundreds of long sentences accumulates ~10^4 Transition nodes and the
    per-utterance cost blows up quadratically (a shared substrate cannot finish
    even ~24 LibriSpeech utterances in 2 minutes). The boundary decision is
    per-utterance — its transitions are THIS utterance's — so nothing should
    persist across utterances; a fresh graph is both correct and O(n)."""
    sub = Substrate()
    cids, flens = coarse_stream_of(sub, M, C)
    return chunk_with_corpus_tp(sub, M, cids, flens, corpus_tp, corpus_level, tag)


def chunks_with_words(sub, normed, C, corpus_tp, corpus_level, tag):
    """normed = [(M_norm, words, speaker)] -> [(block, word, speaker)] over all
    utterances. Each chunk's word = proportional-frame alignment to transcript."""
    out = []
    for ui, (M, words, spk) in enumerate(normed):
        blocks = chunk_one(M, C, corpus_tp, corpus_level, f"{tag}_{ui}")
        lengths = [L for _, L in blocks]
        aligned = align_chunks_to_words(lengths, words)
        for (block, _L), w in zip(blocks, aligned):
            out.append((block, w, spk))
    return out


def _matchable_pool(chunks, min_chars=3):
    """The within/cross word-matching metric is only DEFINED for words that RECUR
    — a chunk whose word appears NOWHERE else (singleton) can never have a
    same-word neighbour, so it contributes a guaranteed 0 and starves the metric
    on continuous speech (a near-unique vocabulary). Restrict the QUERY set to
    chunks whose word recurs (for within: same word from the same speaker again;
    for cross: same word from a DIFFERENT speaker). Short function words (< min_chars)
    are dropped because the proportional alignment is least reliable for them and
    they dominate by frequency. The full pool is still the SEARCH space (a query's
    nearest neighbour may be any chunk); only the QUERY set is filtered to the
    answerable cases. Returns (cross_queryable_idx, within_queryable_idx)."""
    words = [c[1] for c in chunks]
    spk = [c[2] for c in chunks]
    spk_of_word = defaultdict(set)
    cnt_word_spk = defaultdict(int)
    for w, s in zip(words, spk):
        spk_of_word[w].add(s)
        cnt_word_spk[(w, s)] += 1
    cross_q, within_q = [], []
    for i, (_, w, s) in enumerate(chunks):
        if len(w) < min_chars:
            continue
        if len(spk_of_word[w]) >= 2:        # word said by >=2 speakers -> cross answerable
            cross_q.append(i)
        if cnt_word_spk[(w, s)] >= 2:       # word said >=2x by this speaker -> within answerable
            within_q.append(i)
    return cross_q, within_q


def within_cross_chunks(chunks, max_n=400, seed=0, restrict=True, max_q=140):
    """chunks = [(block, word, speaker)]. For each QUERY chunk find its nearest
    within- and nearest cross-speaker neighbour by full DTW over the WHOLE pool;
    report the same-word fraction for each. The search space is the full pool
    (capped to max_n for the O(n^2) DTW); the query set is restricted to chunks
    whose word actually recurs (matchable) when restrict=True — otherwise the
    near-unique continuous-speech vocabulary makes the metric degenerate to 0.
    The number of queries is capped at max_q (the DTW probe is n_q x pool) by a
    seeded sample over the answerable chunks; the pool is unchanged."""
    rng = random.Random(seed)
    if len(chunks) > max_n:
        idx = list(range(len(chunks)))
        rng.shuffle(idx)
        chunks = [chunks[i] for i in idx[:max_n]]
    mats = [c[0] for c in chunks]
    words = [c[1] for c in chunks]
    spk = [c[2] for c in chunks]
    n = len(mats)
    if restrict:
        cross_q, within_q = _matchable_pool(chunks)
    else:
        cross_q = within_q = list(range(n))
    # cap the union of queries (cost = n_queries x pool DTW calls)
    union = sorted(set(cross_q) | set(within_q))
    if len(union) > max_q:
        rng.shuffle(union)
        keep = set(union[:max_q])
        cross_q = [i for i in cross_q if i in keep]
        within_q = [i for i in within_q if i in keep]
    cross_q, within_q = set(cross_q), set(within_q)
    win_hit = win_tot = cross_hit = cross_tot = 0
    for i in range(n):
        if i not in cross_q and i not in within_q:
            continue
        best_w = (1e18, None)
        best_c = (1e18, None)
        for j in range(n):
            if i == j:
                continue
            d = dtw(mats[i], mats[j])
            if spk[j] == spk[i]:
                if d < best_w[0]:
                    best_w = (d, j)
            else:
                if d < best_c[0]:
                    best_c = (d, j)
        if i in within_q and best_w[1] is not None:
            win_tot += 1
            win_hit += (words[best_w[1]] == words[i])
        if i in cross_q and best_c[1] is not None:
            cross_tot += 1
            cross_hit += (words[best_c[1]] == words[i])
    within = win_hit / win_tot if win_tot else 0.0
    cross = cross_hit / cross_tot if cross_tot else 0.0
    return within, cross, n, win_tot, cross_tot


def shuffle_chunks(chunks, max_n=600, seed=0):
    """Shuffle the word labels; within/cross must collapse to ~chance. The shuffle
    is applied to the FULL pool's labels; the matchable-query restriction is
    recomputed on the shuffled labels so the control is apples-to-apples."""
    sh = [(b, w, s) for (b, _, s), w in
          zip(chunks, _shuffled([c[1] for c in chunks], seed))]
    return within_cross_chunks(sh, max_n=max_n, seed=seed)


def _shuffled(xs, seed):
    rng = random.Random(seed)
    ys = list(xs)
    rng.shuffle(ys)
    return ys


# --------------------------------------------------------------------------
# corpus-TP estimation over a set of normalised utterances (the chunker's
# shared transitional-probability distribution).
# --------------------------------------------------------------------------

def build_corpus_tp(sub, normed, C):
    from domains.forward_segmentation import estimate_tp, _median
    streams = []
    for M, _w, _s in normed:
        cids, _flens = coarse_stream_of(sub, M, C)
        streams.append(cids)
    corpus_tp = estimate_tp(streams)
    corpus_level = _median(corpus_tp.values())
    return corpus_tp, corpus_level


# --------------------------------------------------------------------------
# main.
# --------------------------------------------------------------------------

def main():
    n_speakers = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    utts_per_spk = int(sys.argv[2]) if len(sys.argv) > 2 else 14
    probe_chunks = int(sys.argv[3]) if len(sys.argv) > 3 else 350
    K = int(os.environ.get("K", "48"))
    random.seed(1)

    pairs = SL.gather_pairs()
    by_spk = defaultdict(list)
    for p in pairs:
        by_spk[p[1]].append(p)
    all_speakers = sorted(by_spk)[:n_speakers]
    # cap utts per speaker (tractability + balanced per-speaker stats)
    sel = []
    for s in all_speakers:
        ps = list(by_spk[s])
        random.shuffle(ps)
        sel.extend(ps[:utts_per_spk])

    # hold out whole SPEAKERS for test (speaker-independent)
    n_held = max(2, len(all_speakers) // 5)
    test_spk = set(all_speakers[:n_held])
    train_spk = set(all_speakers[n_held:])
    train_pairs = [p for p in sel if p[1] in train_spk]
    test_pairs = [p for p in sel if p[1] in test_spk]
    print(f"LibriSpeech dev-clean: {len(pairs)} utts total")
    print(f"using {len(all_speakers)} speakers, <= {utts_per_spk} utts each")
    print(f"TRAIN {len(train_pairs)} utts / {len(train_spk)} spk   "
          f"TEST {len(test_pairs)} utts / {len(test_spk)} HELD-OUT spk")
    print(f"codebook K={K}")

    sub = Substrate()

    print("\nPerception + framing...")
    t0 = time.time()
    train_raw = frame_corpus(train_pairs)
    test_raw = frame_corpus(test_pairs)
    print(f"  framed train={len(train_raw)} test={len(test_raw)} "
          f"({time.time()-t0:.0f}s)")
    if len(train_raw) < 5 or len(test_raw) < 2:
        print("Too few usable utterances — aborting.")
        return

    canonical = canonical_log_centroid([M for M, _, _ in train_raw])
    print(f"canonical log-centroid (train) = {canonical:.4f}")

    # ===================================================================
    # (1) FAST INNER TEST: within/cross full-DTW on continuous CHUNKS, on
    #     HELD-OUT speakers, BEFORE (per-utterance) vs AFTER (per-speaker CMVN),
    #     shuffle-controlled. Does the invariance CARRY from digits to continuous?
    # ===================================================================
    print("\n" + "=" * 60)
    print("(1) WITHIN/CROSS full-DTW on CONTINUOUS CHUNKS (held-out speakers)")
    print("=" * 60)

    variant = os.environ.get("XN_VARIANT", "uVTLN+ps_CMVN+PR")
    print(f"per-speaker variant = {variant}")

    def make_chunks(normed_train, normed_test, tag):
        """Codebook + corpus-TP from TRAIN; chunk the TEST (held-out) speakers."""
        pool = np.concatenate([M for M, _, _ in normed_train], axis=0)
        if len(pool) > 12000:
            pool = pool[np.random.default_rng(0).choice(len(pool), 12000,
                                                        replace=False)]
        C = kmeans(pool, K, seed=0)
        corpus_tp, corpus_level = build_corpus_tp(sub, normed_train, C)
        ch = chunks_with_words(sub, normed_test, C, corpus_tp, corpus_level, tag)
        return C, corpus_tp, corpus_level, ch

    # BEFORE: per-utterance invariant_transform
    print("\n[BEFORE] per-utterance invariant_transform front-end ...")
    t0 = time.time()
    tr_pu = apply_per_utterance(train_raw, canonical)
    te_pu = apply_per_utterance(test_raw, canonical)
    Cpu, tp_pu, lvl_pu, ch_pu = make_chunks(tr_pu, te_pu, "pu")
    n_words = len(set(w for _, w, _ in ch_pu))
    chance = 1.0 / max(n_words, 1)
    # vocabulary recurrence — the load-bearing scale diagnostic for this metric.
    cq, wq = _matchable_pool(ch_pu)
    print(f"  test chunks: {len(ch_pu)}  ({time.time()-t0:.0f}s)")
    print(f"  vocab: {n_words} distinct words over {len(ch_pu)} chunks; "
          f"cross-answerable (word said by >=2 speakers) {len(cq)}, "
          f"within-answerable {len(wq)}  chance {chance:.4f}")
    w_pu, c_pu, n_pu, wt_pu, ct_pu = within_cross_chunks(
        ch_pu, max_n=probe_chunks, seed=0)
    print(f"  WITHIN {w_pu:.3f} (n={wt_pu})  CROSS {c_pu:.3f} (n={ct_pu})  "
          f"gap {w_pu-c_pu:.3f}  [pool {n_pu}]")

    # AFTER: per-speaker CMVN
    print(f"\n[AFTER] per-speaker CMVN front-end ({variant}) ...")
    t0 = time.time()
    tr_ps = apply_per_speaker(train_raw, canonical, variant)
    te_ps = apply_per_speaker(test_raw, canonical, variant)
    Cps, tp_ps, lvl_ps, ch_ps = make_chunks(tr_ps, te_ps, "ps")
    cq2, wq2 = _matchable_pool(ch_ps)
    print(f"  test chunks: {len(ch_ps)}  ({time.time()-t0:.0f}s)  "
          f"cross-answerable {len(cq2)}, within-answerable {len(wq2)}")
    w_ps, c_ps, n_ps, wt_ps, ct_ps = within_cross_chunks(
        ch_ps, max_n=probe_chunks, seed=0)
    print(f"  WITHIN {w_ps:.3f} (n={wt_ps})  CROSS {c_ps:.3f} (n={ct_ps})  "
          f"gap {w_ps-c_ps:.3f}  [pool {n_ps}]")

    # shuffle control on the AFTER chunks
    sw, sc, _, swt, sct = shuffle_chunks(ch_ps, max_n=probe_chunks, seed=0)
    print(f"\nSHUFFLE control (AFTER): WITHIN {sw:.3f} CROSS {sc:.3f}  "
          f"(must be ~chance {chance:.4f})")

    if ct_pu < 8 or ct_ps < 8:
        print(f"\n>>> METRIC STARVED: too few cross-answerable chunks "
              f"(before {ct_pu}, after {ct_ps}). The continuous-speech "
              f"vocabulary barely recurs at this scale -> the within/cross "
              f"word-matching metric is undefined. Need a larger corpus "
              f"(more utts/speaker so words recur across speakers).")
    carried = (c_ps > c_pu + 0.02) and (sc < c_ps - 0.05) and ct_ps >= 8
    print(f"\n>>> invariance CARRIES from digits to continuous chunks? "
          f"{'YES' if carried else 'NO / PARTIAL'}  "
          f"(CROSS {c_pu:.3f} -> {c_ps:.3f}, shuffle {sc:.3f})")

    # ===================================================================
    # (2) RECOGNITION on held-out speakers, IF the invariance carried.
    # ===================================================================
    if not carried:
        print("\nInvariance did not carry -> recognition NOT run "
              "(would not be informative).")
        print("\nReport the residual above; the continuous-chunk cross-speaker "
              "gap is the remaining inadmissible link.")
        return

    print("\n" + "=" * 60)
    print("(2) RECOGNITION on HELD-OUT speakers (per-speaker CMVN front-end)")
    print("=" * 60)
    run_recognition(sub, tr_ps, te_ps, Cps, tp_ps, lvl_ps, chance)


def run_recognition(sub, tr_norm, te_norm, C, corpus_tp, corpus_level, chance):
    """Full chain: chunk TRAIN + ground a chunk->word lexicon (cluster), then
    recognise the held-out TEST speakers. word-acc / WER / content-recall vs
    unigram + frequency-matched baselines."""
    LEXICON_MODE = os.environ.get("LEXICON_MODE", "cluster")
    print(f"LEXICON_MODE = {LEXICON_MODE}")

    # ---- TRAIN: chunk + align + lexicon ----
    if LEXICON_MODE == "cluster":
        lex = ClusterLexicon(n_clusters=1, n_iters=25, seed=0)
        defer_k = True
    else:
        lex = Lexicon()
        defer_k = False
    tot_chunks = tot_words = 0
    for M, words, _s in tr_norm:
        blocks = chunk_one(M, C, corpus_tp, corpus_level,
                           f"tr_{id(M)&0xffffff}")
        lengths = [L for _, L in blocks]
        aligned = align_chunks_to_words(lengths, words)
        tot_chunks += len(blocks)
        tot_words += len(words)
        for (block, _L), w in zip(blocks, aligned):
            lex.add_train_chunk(block, w)
    if defer_k:
        distinct = len({w for _, ws, _ in tr_norm for w in ws})
        lex.n_clusters = max(2, distinct)
        print(f"  cluster k = distinct train words = {lex.n_clusters}")
    lex.finalize()

    ratio = tot_chunks / max(tot_words, 1)
    pstats = lex.purity()
    print(f"\nchunks/words ratio : {ratio:.2f}  ({tot_chunks}/{tot_words})")
    print(f"lexicon clusters   : {len(lex.protos)}")
    print(f"train PURITY       : {pstats['purity']:.3f}  "
          f"(singleton frac {pstats['singleton_frac']:.3f}, "
          f"MULTI-member purity {pstats['multi_purity']:.3f} over "
          f"{pstats['multi_chunks']} chunks)")

    # ---- unigram baseline + TEST recognition ----
    train_word_freq = defaultdict(int)
    for _, words, _ in tr_norm:
        for w in words:
            train_word_freq[w] += 1
    unigram_word = max(train_word_freq.items(), key=lambda kv: kv[1])[0]
    distinct_train_words = len(train_word_freq)
    chance_word_acc = 1.0 / max(distinct_train_words, 1)
    all_train_words = list(train_word_freq.keys())
    freq_weights = [train_word_freq[w] for w in all_train_words]

    sum_wer = sum_wer_uni = sum_wer_chance = 0.0
    word_hits = word_total = uni_word_hits = 0
    recall_hits = recall_total = uni_recall_hits = 0
    freq_recall_hits = 0.0
    n_eval = 0
    rng = random.Random(7)
    for M, words, _s in te_norm:
        blocks = chunk_one(M, C, corpus_tp, corpus_level,
                           f"te_{id(M)&0xffffff}")
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

        sum_wer += wer(words, hyp)
        sum_wer_uni += wer(words, [unigram_word] * len(words))
        sum_wer_chance += wer(words, [rng.choice(all_train_words) for _ in words])

        for j, tw in enumerate(words):
            word_total += 1
            if j < len(hyp) and hyp[j] == tw:
                word_hits += 1
            if tw == unigram_word:
                uni_word_hits += 1

        ref_set = set(words)
        hyp_set = set(hyp)
        n_distinct_hyp = max(1, len(hyp_set))
        FREQ_DRAWS = 20
        freq_sets = [set(rng.choices(all_train_words, weights=freq_weights,
                                     k=n_distinct_hyp)) for _ in range(FREQ_DRAWS)]
        for tw in ref_set:
            recall_total += 1
            if tw in hyp_set:
                recall_hits += 1
            if tw == unigram_word:
                uni_recall_hits += 1
            freq_recall_hits += sum(tw in fs for fs in freq_sets) / FREQ_DRAWS
        n_eval += 1

    mean_wer = sum_wer / max(n_eval, 1)
    mean_wer_uni = sum_wer_uni / max(n_eval, 1)
    mean_wer_chance = sum_wer_chance / max(n_eval, 1)
    word_acc = word_hits / max(word_total, 1)
    uni_word_acc = uni_word_hits / max(word_total, 1)
    content_recall = recall_hits / max(recall_total, 1)
    uni_recall = uni_recall_hits / max(recall_total, 1)
    freq_recall = freq_recall_hits / max(recall_total, 1)

    print(f"\nheld-out utts scored : {n_eval}")
    print(f"distinct train words : {distinct_train_words} "
          f"(chance word acc {chance_word_acc:.4f})")
    print(f"unigram word         : '{unigram_word}'")
    print("\nWORD ERROR RATE (lower=better):")
    print(f"  agent chain      : {mean_wer:.3f}")
    print(f"  unigram baseline : {mean_wer_uni:.3f}")
    print(f"  chance baseline  : {mean_wer_chance:.3f}")
    print("\nWORD ACCURACY (position-aligned, higher=better):")
    print(f"  agent chain      : {word_acc:.3f}  ({word_hits}/{word_total})")
    print(f"  unigram baseline : {uni_word_acc:.3f}")
    print(f"  chance baseline  : {chance_word_acc:.4f}")
    print("\nCONTENT-WORD RECALL (position-free, higher=better):")
    print(f"  agent chain      : {content_recall:.3f}  ({recall_hits}/{recall_total})")
    print(f"  unigram set      : {uni_recall:.3f}")
    print(f"  freq-matched rnd : {freq_recall:.3f}")

    # ---- verdict ----
    print("\n" + "=" * 60)
    print("VERDICT")
    print("=" * 60)
    usable_lexicon = pstats["purity"] > 0.30 and len(lex.protos) > 10
    beats_unigram_wer = mean_wer < mean_wer_uni - 0.02
    beats_unigram_acc = word_acc > uni_word_acc * 1.15 and word_acc > 0.02
    beats_recall = content_recall > max(uni_recall, freq_recall) + 0.02
    print(f"(i)   usable lexicon (purity>0.30) : "
          f"{'YES' if usable_lexicon else 'NO'} ({pstats['purity']:.3f})")
    print(f"(ii)  WER below unigram            : "
          f"{'YES' if beats_unigram_wer else 'NO'} "
          f"({mean_wer:.3f} vs {mean_wer_uni:.3f})")
    print(f"(iii) word-acc above unigram       : "
          f"{'YES' if beats_unigram_acc else 'NO'} "
          f"({word_acc:.3f} vs {uni_word_acc:.3f})")
    print(f"(iv)  content-recall above baseline: "
          f"{'YES' if beats_recall else 'NO'} "
          f"({content_recall:.3f} vs max({uni_recall:.3f},{freq_recall:.3f}))")
    crossed = usable_lexicon and (beats_unigram_wer or beats_unigram_acc
                                  or beats_recall)
    print(f"\n>>> continuous-speech last link CROSSES unigram on held-out "
          f"speakers? {'YES' if crossed else 'NO / PARTIAL'}")


if __name__ == "__main__":
    main()

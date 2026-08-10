"""iter-10 — ground the cross-speaker lexicon on the agent's OWN persona world.

The recognition structure is ONE link from admissible: perception / units /
invariance / word-scale-chunking all CROSSED. The LAST broken link is the
cross-speaker lexicon — it retrieved only at the frequency prior because the
held-out LibriSpeech corpus was CORPUS-STARVED: at 22-60 utts there was almost
no cross-speaker word REPETITION to learn a speaker-invariant chunk->word map
from. The binding constraint was MISSING EVIDENCE in the data, not a missing
algorithm.

This script removes that constraint with the agent's persona_speech_world: the
agent CONTROLS many speaking personas (distinct f0 / Q / vocal-tract length) and
CHOOSES the words, so it can make the SAME word recur across MANY speakers — the
exact cross-speaker repetition the lexicon needs, manufactured by the agent's own
voice. Every persona says every word in a small controlled vocabulary; the lexicon
grounds the speaker-invariant chunk->word map from the repetition; recognition is
tested on HELD-OUT personas (the speaker-independent test, the whole point).

WORLD ADAPTER ONLY. Python voices personas (the I/O boundary) and measures. The
recognition CHAIN is the agent's own forward build (CSR: perception -> invariant
transform -> word-scale chunking -> cluster lexicon). No agent reasoning here, no
tuning to cross — the cluster k = #vocabulary words (the natural target), the
controls (unigram + frequency-matched random) are computed in the same breath.

Run: python -m scripts.iter10_persona_lexicon [n_reps] [holdout=personas|reps]
"""
import os
import sys
import random
from collections import defaultdict, Counter

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from substrate_rs import Substrate
import scripts.fsdd_learner_world as fl
from domains.stt_pipeline import STTPipeline, STTParams
from domains.speech_cortex import SpeechCortex
from domains.persona_speech_world import install_personas, speak_as
import scripts.continuous_speech_recognition as CSR
from domains.invariant_units import invariant_transform, canonical_log_centroid


# A bank of personas the agent controls — distinct f0 (pitch), Q (resonance),
# and vocal-tract length (formant shift). More voices than DEFAULT_PERSONAS so
# the SAME word recurs across MANY speakers (the cross-speaker repetition the
# lexicon was starved of). (name, f0_hz, q_factor, vtl_scale).
PERSONA_BANK = [
    ("pip",      230.0, 6.0, 0.82),   # a small child
    ("ada",      198.0, 5.5, 0.90),
    ("nell",     176.0, 5.0, 0.95),   # a woman
    ("vera",     158.0, 4.5, 0.98),
    ("milo",     132.0, 4.5, 1.04),
    ("theo",     118.0, 4.0, 1.08),   # a man
    ("gus",      104.0, 3.5, 1.12),
    ("bertram",   92.0, 3.0, 1.18),   # a deep voice
]

# Controlled vocabulary the agent says (FSDD digits it can be taught to voice).
VOCAB = ["one", "three", "five", "seven", "nine", "two", "four", "eight"]


def build_agent(threshold=0.02):
    sub = Substrate()
    pipe = STTPipeline(STTParams(sample_rate=8000))
    pipe.attach(sub)
    pipe._ensure_audio_pipeline(sub)
    for op in sub.nodes("Operation"):
        if sub.node(op)["attrs"].get("kind") == "lexical_access":
            sub.set_attr(op, "distance_threshold", threshold)
    SpeechCortex(sub, lexicon_name="stt", tick_period_ms=99999).install()
    return sub, pipe


def teach_vocab(sub, pipe, vocab, n_clips=6):
    """Teach the agent each vocabulary word from FSDD clips so it can VOICE them.
    Mechanical: ingest clips, ground signs to the word Concept."""
    af = fl.gather_files(limit=None)
    pool = [f for f in af if f[2] != "jackson"]
    digits = {w: i for i, w in enumerate(fl._DIGITS)}
    vc = {}
    for w in vocab:
        clips = [f for f in pool if f[1] == digits[w]][:n_clips]
        for path, d, sp, idx in clips:
            s, fs = fl.load_wav(path)
            fl.teach_one(sub, pipe, s, w, vc)
            sub.tick(50000)
    return vc


def make_persona_corpus(sub, pipe, persona_ids, vocab, n_reps, seed=0):
    """The agent voices every word through every persona, n_reps times each. Each
    (persona, word, rep) produces one audio = one single-word 'utterance'. Returns
    a list of (audio, [word], persona_name, rep). This is the cross-speaker
    repetition the lexicon was starved of, manufactured by the agent's own voice."""
    rng = random.Random(seed)
    corpus = []
    for name, pid in persona_ids.items():
        for w in vocab:
            for r in range(n_reps):
                # tiny pitch/rate jitter per rep so repetitions aren't identical
                # (a real speaker never repeats a word byte-for-byte). Jitter the
                # persona's f0 by +-4% — still the SAME speaker, a natural rep.
                a = sub.node(pid)["attrs"]
                f0 = float(a.get("f0_hz", 120.0)) * (1.0 + 0.04 * (rng.random() - 0.5))
                audio = pipe.speak(sub, w, f0_hz=f0,
                                   q_factor=float(a.get("q_factor", 4.0)))
                audio = np.asarray(audio, dtype=np.float32)
                vtl = float(a.get("vtl_scale", 1.0))
                if vtl != 1.0 and audio.size:
                    n = max(1, int(round(audio.size / vtl)))
                    idx = np.clip((np.arange(n) * vtl).astype(int), 0,
                                  audio.size - 1)
                    audio = np.ascontiguousarray(audio[idx])
                corpus.append((audio, [w], name, r))
    return corpus


def frame_corpus(items):
    """Mechanical: each utterance audio -> invariant-ready band matrix (frames x
    bands). Drops degenerate (too-short) utterances."""
    out = []
    for audio, words, name, r in items:
        M = CSR.frames_of(audio, 8000)
        if M.shape[0] < 4:
            continue
        out.append((M, words, name, r))
    return out


def chunk_blocks(sub, M, C, corpus_tp, corpus_level, tag):
    """One utterance's frames -> word-scale chunk blocks, using corpus-scale TP
    (iter-9's word-scale-chunking link). The agent's graph boundary Term decides;
    only the TP it reads is the corpus-wide distribution."""
    cids, flens = CSR.coarse_stream_of(sub, M, C)
    if corpus_tp is None:
        return CSR.chunk_an_utterance(sub, M, C)
    return CSR.chunk_with_corpus_tp(sub, M, cids, flens, corpus_tp,
                                    corpus_level, tag)


def freq_recall_control(ref_set, hyp_set, all_words, weights, rng, n_draws=20):
    """Frequency-matched random control (iter-9's): a guess of the SAME #distinct
    words as the hyp, drawn by the train frequency prior, recalls how much of ref?
    Averaged over n_draws so it's a stable expectation."""
    k = max(1, len(hyp_set))
    hits = 0.0
    for _ in range(n_draws):
        draw = set(rng.choices(all_words, weights=weights, k=k))
        hits += sum(w in draw for w in ref_set)
    return hits / n_draws


def run(n_reps=4, holdout="personas", lexicon_mode="cluster", seed=1, verbose=True):
    random.seed(seed)
    rng = random.Random(7)

    sub, pipe = build_agent()
    if verbose:
        print(f"vocabulary ({len(VOCAB)} words): {VOCAB}")
    teach_vocab(sub, pipe, VOCAB)
    personas = install_personas(sub, PERSONA_BANK)
    if verbose:
        print(f"personas the agent controls ({len(personas)}): {list(personas)}")
        print(f"  corpus = {len(personas)} personas x {len(VOCAB)} words x "
              f"{n_reps} reps = {len(personas)*len(VOCAB)*n_reps} utterances")

    # ---- manufacture the cross-speaker-repetition corpus -----------------
    corpus = make_persona_corpus(sub, pipe, personas, VOCAB, n_reps, seed=seed)
    framed = frame_corpus(corpus)

    # ---- split: held-out PERSONAS (speaker-independent) or held-out REPS ----
    persona_names = list(personas)
    if holdout == "personas":
        n_held = max(1, len(persona_names) // 4)
        test_personas = set(persona_names[:n_held])
        train = [t for t in framed if t[2] not in test_personas]
        test = [t for t in framed if t[2] in test_personas]
        split_desc = (f"HELD-OUT {len(test_personas)} personas "
                      f"{sorted(test_personas)} (speaker-independent)")
    else:  # held-out repetitions: last rep of each (persona,word) is test
        test_rep = n_reps - 1
        train = [t for t in framed if t[3] != test_rep]
        test = [t for t in framed if t[3] == test_rep]
        split_desc = f"HELD-OUT repetition #{test_rep} (same speakers, new utterances)"
    if verbose:
        print(f"split: {split_desc}")
        print(f"  train {len(train)} utts / test {len(test)} utts")

    if not train or not test:
        print("empty split — aborting")
        return None

    # ---- invariance + codebook (TRAIN only, no test leakage) -------------
    canonical = canonical_log_centroid([M for M, *_ in train])
    train_inv = [(invariant_transform(M, canonical), w, nm, r)
                 for M, w, nm, r in train]
    test_inv = [(invariant_transform(M, canonical), w, nm, r)
                for M, w, nm, r in test]
    K = int(os.environ.get("K", "48"))
    pool = np.concatenate([M for M, *_ in train_inv], axis=0)
    C = CSR.kmeans(pool, K, seed=0)

    # ---- corpus-scale TP (word-scale chunking link) ----------------------
    use_corpus_tp = os.environ.get("CORPUS_TP", "1") == "1"
    corpus_tp = corpus_level = None
    if use_corpus_tp:
        from domains.forward_segmentation import estimate_tp, _median
        streams = [CSR.coarse_stream_of(sub, M, C)[0] for M, *_ in train_inv]
        corpus_tp = estimate_tp(streams)
        corpus_level = _median(corpus_tp.values())

    # ---- TRAIN: chunk + align + build the cross-speaker lexicon -----------
    distinct = len({w for _, ws, *_ in train_inv for w in ws})
    if lexicon_mode == "cluster":
        lex = CSR.ClusterLexicon(n_clusters=max(2, distinct),
                                 n_iters=int(os.environ.get("CLUSTER_ITERS", "25")),
                                 seed=0)
    else:
        lex = CSR.Lexicon()

    tot_chunks = tot_words = 0
    for i, (M, words, nm, r) in enumerate(train_inv):
        blocks = chunk_blocks(sub, M, C, corpus_tp, corpus_level, f"tr_{i}")
        lengths = [L for _, L in blocks]
        aligned = CSR.align_chunks_to_words(lengths, words)
        for (block, _L), w in zip(blocks, aligned):
            lex.add_train_chunk(block, w)
        tot_chunks += len(blocks)
        tot_words += len(words)
    lex.finalize()

    pstats = lex.purity()
    ratio = tot_chunks / max(tot_words, 1)
    if verbose:
        print(f"\n--- LEXICON (cross-speaker chunk->word map) ---")
        print(f"chunks/word ratio    : {ratio:.2f}")
        print(f"lexicon purity       : {pstats['purity']:.3f}")
        print(f"  multi-member purity: {pstats['multi_purity']:.3f}  "
              f"(over {pstats['multi_chunks']} chunks in shared clusters — "
              f"the honest cross-speaker number)")
        print(f"  singleton fraction : {pstats['singleton_frac']:.3f}")

    # ---- TEST: recognise held-out -> word-acc + content-recall + controls -
    train_word_freq = defaultdict(int)
    for _, words, *_ in train_inv:
        for w in words:
            train_word_freq[w] += 1
    unigram_word = max(train_word_freq.items(), key=lambda kv: kv[1])[0]
    all_words = list(train_word_freq)
    weights = [train_word_freq[w] for w in all_words]
    distinct_train = len(all_words)
    chance_acc = 1.0 / max(distinct_train, 1)

    word_hits = word_total = uni_hits = 0
    recall_hits = recall_total = 0.0
    uni_recall = freq_recall = 0.0
    for i, (M, words, nm, r) in enumerate(test_inv):
        blocks = chunk_blocks(sub, M, C, corpus_tp, corpus_level, f"te_{i}")
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

        for j, tw in enumerate(words):
            word_total += 1
            if j < len(hyp) and hyp[j] == tw:
                word_hits += 1
            if tw == unigram_word:
                uni_hits += 1

        ref_set, hyp_set = set(words), set(hyp)
        for tw in ref_set:
            recall_total += 1
            if tw in hyp_set:
                recall_hits += 1
            if tw == unigram_word:
                uni_recall += 1
        freq_recall += freq_recall_control(ref_set, hyp_set, all_words,
                                            weights, rng)

    word_acc = word_hits / max(word_total, 1)
    uni_acc = uni_hits / max(word_total, 1)
    c_recall = recall_hits / max(recall_total, 1)
    u_recall = uni_recall / max(recall_total, 1)
    f_recall = freq_recall / max(recall_total, 1)

    res = {
        "n_reps": n_reps, "holdout": holdout, "lexicon_mode": lexicon_mode,
        "n_train": len(train_inv), "n_test": len(test_inv),
        "chunks_per_word": ratio, "purity": pstats["purity"],
        "multi_purity": pstats["multi_purity"],
        "multi_chunks": pstats["multi_chunks"],
        "word_acc": word_acc, "uni_acc": uni_acc, "chance_acc": chance_acc,
        "content_recall": c_recall, "uni_recall": u_recall,
        "freq_recall": f_recall, "unigram_word": unigram_word,
        "distinct_train": distinct_train,
    }

    if verbose:
        print(f"\n--- RECOGNITION on held-out ({len(test_inv)} utts) ---")
        print(f"distinct train words : {distinct_train} "
              f"(chance acc {chance_acc:.3f})")
        print(f"unigram word         : '{unigram_word}'")
        print(f"\nWORD ACCURACY (position-aligned):")
        print(f"  agent chain        : {word_acc:.3f}  ({word_hits}/{word_total})")
        print(f"  unigram baseline   : {uni_acc:.3f}")
        print(f"  chance             : {chance_acc:.3f}")
        print(f"\nCONTENT-WORD RECALL (position-free, isolates lexicon retrieval):")
        print(f"  agent chain        : {c_recall:.3f}")
        print(f"  unigram set        : {u_recall:.3f}  (just '{unigram_word}')")
        print(f"  freq-matched random: {f_recall:.3f}  (the honest control)")
        crossed_acc = word_acc > uni_acc * 1.15 and word_acc > chance_acc * 1.5
        crossed_recall = c_recall > f_recall + 0.02
        print(f"\nVERDICT:")
        print(f"  word-acc crosses unigram : "
              f"{'YES' if crossed_acc else 'NO'} "
              f"({word_acc:.3f} vs uni {uni_acc:.3f}, chance {chance_acc:.3f})")
        print(f"  recall crosses freq-ctrl : "
              f"{'YES' if crossed_recall else 'NO'} "
              f"({c_recall:.3f} vs freq {f_recall:.3f})")
        switch_on = crossed_acc and crossed_recall
        verdict = ("becomes admissible — recognition CROSSES the prior on the "
                   "agent's own speaker-invariant speech" if switch_on else
                   "did NOT cross even with repetition — necessary-not-sufficient")
        print(f"\n>>> {'SWITCH-ON' if switch_on else 'NOT YET'}: the last link "
              f"(cross-speaker lexicon) {verdict}.")
        res["crossed_acc"] = crossed_acc
        res["crossed_recall"] = crossed_recall
        res["switch_on"] = switch_on
    return res


def main():
    n_reps = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    holdout = sys.argv[2] if len(sys.argv) > 2 else "personas"
    lexicon_mode = os.environ.get("LEXICON_MODE", "cluster")
    run(n_reps=n_reps, holdout=holdout, lexicon_mode=lexicon_mode)


if __name__ == "__main__":
    main()

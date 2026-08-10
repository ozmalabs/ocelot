"""Helped sentence-learning test: ground the agent's acoustic units to
REAL WORDS using LibriSpeech transcripts, then measure WORD-LEVEL
sequential structure — and CONTRAST it against the prior UNSUPERVISED
sub-word result (next-unit top-1 ~9%, 1.52x over frequency).

The prior unsupervised test (scripts.sentence_learning) confirmed the
agent learns *some* sequential structure, but on NOISY SUB-WORD units:
its sonority-valley segmenter cuts continuous speech into acoustic
fragments, not words, so the learned structure is coarse and the
next-unit prediction is weak (top-1 ~9%, collapsing under shuffle).

THE HELPER (root-cause fix): LibriSpeech ships the ground-truth words.
We use the agent's OWN word-boundary signal (sonority valleys) to align
its emergent acoustic segments to the transcript words, via
STTPipeline.teach_via_valleys — the pipeline method built for exactly
this. Each acoustic sign is grounded (denotes-edge + a vote) to the real
word it aligned to. After teaching, the agent's lexicon is REAL WORDS
grounded to acoustic patterns; re-ingesting an utterance and reading each
sign's top-voted word yields a sequence of REAL WORDS the agent
perceived. We then measure WORD-level bigram structure over those
sequences.

GROUNDING ROUTE USED: teach_via_valleys (route 1 in the brief). It
accepts (audio, transcript, vote_counts), runs the pipeline, partitions
the sign stream at the agent's sonority valleys into N groups, reconciles
N to the transcript word count, and grounds each group's signs to its
word. This is the substrate-native word-boundary alignment — preferred
over crude proportional mapping (teach_aligned) because it uses the
agent's perception of where word boundaries are.

This is a world-adapter MEASUREMENT script: it ingests audio through the
agent's perception, drives the agent's grounding, then reads graph state
back out and computes statistics. No agent reasoning lives in Python.

Honest test. Reports alignment quality (the crux), real-word lexicon
stats, word-level entropy, held-out next-WORD prediction vs frequency vs
shuffle, and contrasts against the unsupervised ~9% sub-word baseline.
A null result (grounding too lossy to help) is reported plainly.

Run:
    python -m scripts.sentence_learning_helped [n_utts] [n_speakers]
"""
import math
import os
import random
import re
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from substrate_rs import Substrate
from domains.stt_pipeline import STTPipeline, STTParams, _node_sort_key

# Reuse the data-loading + metric helpers from the unsupervised test —
# same corpus walk, same FLAC decode, same entropy / predictor maths, so
# the two tests are directly comparable.
import scripts.sentence_learning as SL

# The number the helper must beat: prior UNSUPERVISED sub-word next-unit
# top-1 prediction (held-out bigram argmax over emergent sign ids).
PRIOR_UNSUP_SUBWORD_TOP1 = 0.09


def words_of(transcript: str) -> list[str]:
    """Transcript -> lowercased real-word tokens (same tokeniser the
    pipeline's teach_via_valleys uses)."""
    return [w for w in re.findall(r"[\w']+", transcript.lower()) if w]


def build_vote_index(vote_counts: dict) -> dict:
    """Collapse the (sign_key, word)->count dict into sign_key->best_word
    ONCE. The naive per-sign scan over all vote entries is O(V) per call
    and dominates runtime at 10k+ entries; this makes lookup O(1)."""
    best: dict = {}      # sign_key -> (best_word, best_count)
    for (sk, w), c in vote_counts.items():
        cur = best.get(sk)
        if cur is None or c > cur[1]:
            best[sk] = (w, c)
    return {sk: wc[0] for sk, wc in best.items()}


def ordered_sign_keys_of_latest_stream(sub) -> list:
    """Time-ordered AcousticSign keys on the most-recently-created
    AudioStream (the one the last teach/ingest produced). Reads the
    Utterances' start_time_s for ordering — same readout the readback
    used, but with NO second cochlear pass. Pure graph query."""
    # The newest stream is the highest NodeID AudioStream that has
    # Utterances pointing to it via from_stream.
    best_stream = None
    best_key = -1
    for st in sub.nodes("AudioStream"):
        if sub.node(st)["attrs"].get("_pipeline_template"):
            continue
        has_utt = any(sub.node(u)["type"] == "Utterance"
                      for u in sub.in_neighbours(st, "from_stream"))
        if not has_utt:
            continue
        v = getattr(st, "value", None)
        k = v if isinstance(v, int) else 0
        if k >= best_key:
            best_key = k
            best_stream = st
    if best_stream is None:
        return []
    sign_with_time = []
    for utt in sub.in_neighbours(best_stream, "from_stream"):
        if sub.node(utt)["type"] != "Utterance":
            continue
        t = sub.node(utt)["attrs"].get("start_time_s")
        for s in sub.neighbours(utt, "heard_as"):
            sign_with_time.append((float(t) if t is not None else 0.0,
                                   _node_sort_key(s)))
    sign_with_time.sort(key=lambda x: x[0])
    return [sk for _, sk in sign_with_time]


def main():
    random.seed(1)
    n_utts = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
    n_speakers = int(sys.argv[2]) if len(sys.argv) > 2 else 40

    pairs = SL.gather_pairs()
    speakers = sorted(set(p[1] for p in pairs))
    print(f"LibriSpeech dev-clean: {len(pairs)} utterances, "
          f"{len(speakers)} speakers")
    chosen_spk = speakers[:n_speakers]
    sel = [p for p in pairs if p[1] in chosen_spk]
    random.shuffle(sel)
    sel = sel[:n_utts]
    used_spk = sorted(set(p[1] for p in sel))
    print(f"Using {len(sel)} utterances from {len(used_spk)} speakers")

    sub = Substrate()
    pipe = STTPipeline(STTParams(sample_rate=8000))
    pipe.attach(sub)
    pipe._ensure_audio_pipeline(sub)

    # ---------------------------------------------------------------
    # PHASE 1 — HELPER: ground acoustic units to real words via the
    # agent's own sonority-valley boundaries (teach_via_valleys).
    # We record, per utterance, the TRUE word sequence so we can both
    # (a) measure alignment quality and (b) compute the real-English
    # word-bigram ceiling.
    # ---------------------------------------------------------------
    vote_counts: dict = {}
    true_word_seqs: list[list[str]] = []   # ground-truth transcript words
    # Per-utterance ordered AcousticSign KEYS, captured at teach time
    # straight from the graph (no second cochlear pass). After teaching
    # we map these keys -> the agent's top-voted word via a fast index.
    utt_sign_keys: list[list] = []
    align_signs = 0                        # total signs grounded
    align_groups_eq_words = 0              # utts where #groups == #words
    n_taught = 0
    t0 = time.time()
    for i, (path, sp, ch, ut, transcript) in enumerate(sel):
        words = words_of(transcript)
        if not words:
            continue
        try:
            samples, _ = SL.load_flac_8k(path)
        except Exception as e:
            print(f"  FAIL decode {path}: {e}", flush=True)
            continue
        try:
            res = pipe.teach_via_valleys(sub, samples, transcript,
                                          vote_counts=vote_counts)
        except Exception as e:
            print(f"  FAIL teach {path}: {e}", flush=True)
            continue
        sub.tick(50000)
        if res.get("signs", 0) == 0:
            continue
        # Capture this utterance's ordered sign keys from the stream the
        # teach just created — mechanical graph readout, no re-ingest.
        keys = ordered_sign_keys_of_latest_stream(sub)
        align_signs += res.get("signs_grounded", 0)
        if res.get("groups", 0) == res.get("words", 0):
            align_groups_eq_words += 1
        true_word_seqs.append(words)
        utt_sign_keys.append(keys)
        n_taught += 1
        if n_taught % 100 == 0:
            print(f"  taught {n_taught}  signs_grounded(cum)={align_signs}  "
                  f"vote_entries={len(vote_counts)}  "
                  f"({time.time()-t0:.0f}s)", flush=True)

    print(f"\nTaught {n_taught} utterances in {time.time()-t0:.0f}s")

    # ---------------------------------------------------------------
    # PHASE 2 — READBACK (index-based, no re-ingest): map each captured
    # sign key to the agent's PERCEIVED word (its top-voted grounding)
    # in time order. Same value the agent grounded; we just avoid a
    # second cochlear pass over 1000 utts. We also measure ALIGNMENT
    # QUALITY: per-position agreement between the agent's perceived word
    # and the true word (after collapsing consecutive dups, since many
    # signs map to one word). Honest: this is the crux — poor alignment
    # => a polluted word lexicon.
    # ---------------------------------------------------------------
    vote_index = build_vote_index(vote_counts)
    perceived_word_seqs: list[list[str]] = []  # agent's grounded words / utt
    align_pos_hits = 0     # perceived[i] == true[i] (position-aligned)
    align_pos_total = 0
    align_inset_hits = 0   # perceived word is somewhere in the true sentence
    align_inset_total = 0
    for keys, true_words in zip(utt_sign_keys, true_word_seqs):
        seq = []
        for sk in keys:
            w = vote_index.get(sk)
            if w is None:
                continue
            if not seq or seq[-1] != w:   # collapse consecutive dups
                seq.append(w)
        if len(seq) >= 2:
            perceived_word_seqs.append(seq)
        true_set = set(true_words)
        for j, w in enumerate(seq):
            align_inset_total += 1
            if w in true_set:
                align_inset_hits += 1
            if j < len(true_words):
                align_pos_total += 1
                if w == true_words[j]:
                    align_pos_hits += 1

    pos_acc = align_pos_hits / max(align_pos_total, 1)
    inset_acc = align_inset_hits / max(align_inset_total, 1)

    print("\n==================================================")
    print("(1) GROUNDING ROUTE + ALIGNMENT QUALITY (the crux)")
    print("==================================================")
    print("route: teach_via_valleys (sonority-valley boundaries -> "
          "transcript words)")
    print(f"utterances taught            : {n_taught}")
    print(f"  #groups == #words (clean)  : {align_groups_eq_words} "
          f"({align_groups_eq_words / max(n_taught,1):.1%})")
    print(f"  signs grounded (cum)       : {align_signs}")
    print(f"ALIGNMENT (agent perceived word vs TRUE transcript):")
    print(f"  position-exact agreement   : {pos_acc:.3f}  "
          f"({align_pos_hits}/{align_pos_total})  "
          f"<- agent's word == true word at same position")
    print(f"  in-sentence agreement      : {inset_acc:.3f}  "
          f"({align_inset_hits}/{align_inset_total})  "
          f"<- agent's word is somewhere in the true sentence")
    print("  (low position-exact => lexicon polluted: signs vote across "
          "multiple words via DTW merge)")

    # ---------------------------------------------------------------
    # (2) REAL-WORD LEXICON + RECURRENCE — over the AGENT'S perceived
    # word sequences (the real-word lexicon it actually grounded).
    # ---------------------------------------------------------------
    seen = set()
    total = 0
    repeat = 0
    for seq in perceived_word_seqs:
        for w in seq:
            total += 1
            if w in seen:
                repeat += 1
            else:
                seen.add(w)
    lexicon_size = len(seen)
    recurrence = repeat / max(total, 1)
    print("\n==================================================")
    print("(2) REAL-WORD LEXICON / RECURRENCE (agent's grounded words)")
    print("==================================================")
    print(f"perceived word tokens : {total}")
    print(f"distinct real words   : {lexicon_size}")
    print(f"recurrence            : {recurrence:.3f}")
    # For reference, the true-transcript word lexicon over the same utts.
    t_seen = set()
    t_total = 0
    t_rep = 0
    for seq in true_word_seqs:
        for w in seq:
            t_total += 1
            if w in t_seen:
                t_rep += 1
            else:
                t_seen.add(w)
    print(f"(true transcript lex  : {len(t_seen)} words, "
          f"recurrence {t_rep / max(t_total,1):.3f}, {t_total} tokens)")
    collapse = lexicon_size / max(len(t_seen), 1)
    print(f"LEXICON COLLAPSE      : agent grounds onto {lexicon_size} of the "
          f"{len(t_seen)} true words ({collapse:.2f}x)")
    print("  (collapse << 1 means signs vote toward a few dominant words; a "
          "small/degenerate perceived lexicon inflates prediction numbers "
          "for the wrong reason — read top-1 with this in mind)")

    # ---------------------------------------------------------------
    # (3) WORD-LEVEL TRANSITION STRUCTURE — entropy gain.
    # ---------------------------------------------------------------
    unigram = {}
    bigrams = {}
    for seq in perceived_word_seqs:
        for a, b in zip(seq, seq[1:]):
            unigram[b] = unigram.get(b, 0) + 1
            bigrams.setdefault(a, {}).setdefault(b, 0)
            bigrams[a][b] += 1
    h_next = SL.entropy(unigram)
    h_next_cur = SL.conditional_next_entropy(bigrams)
    print("\n==================================================")
    print("(3) WORD-LEVEL TRANSITION STRUCTURE")
    print("==================================================")
    print(f"H(next_word)       : {h_next:.3f} bits")
    print(f"H(next_word|cur)   : {h_next_cur:.3f} bits")
    print(f"information gain    : {h_next - h_next_cur:.3f} bits  "
          f"({'structure' if h_next_cur < h_next - 1e-6 else 'NONE'})")

    # ---------------------------------------------------------------
    # (4) HELD-OUT NEXT-WORD PREDICTION — bigram argmax vs frequency
    # baseline vs shuffle, over the AGENT'S grounded word sequences.
    # Same train/test machinery as the unsupervised test.
    # ---------------------------------------------------------------
    seqs = [s for s in perceived_word_seqs if len(s) >= 2]
    random.shuffle(seqs)
    split = int(0.8 * len(seqs))
    train_seqs, test_seqs = seqs[:split], seqs[split:]

    t1a, t3a, chance, npred = SL.bigram_predict(
        train_seqs, test_seqs, lexicon_size)
    u1, u3, _ = SL.unigram_predict(train_seqs, test_seqs)

    # shuffle contrast — preserve frequency, destroy order.
    all_tokens = [tok for seq in seqs for tok in seq]
    lengths = [len(seq) for seq in seqs]
    random.shuffle(all_tokens)
    shuf_seqs = []
    idx = 0
    for L in lengths:
        shuf_seqs.append(all_tokens[idx:idx + L])
        idx += L
    random.shuffle(shuf_seqs)
    s_train, s_test = shuf_seqs[:split], shuf_seqs[split:]
    st1, st3, schance, snpred = SL.bigram_predict(
        s_train, s_test, lexicon_size)

    # CEILING: the same prediction over the TRUE transcript words —
    # what real-English word bigrams achieve on this corpus, with the
    # agent's perception removed. Bounds how much alignment noise costs.
    t_seqs = [s for s in true_word_seqs if len(s) >= 2]
    random.shuffle(t_seqs)
    tsplit = int(0.8 * len(t_seqs))
    tr_train, tr_test = t_seqs[:tsplit], t_seqs[tsplit:]
    ct1, ct3, cchance, cnp = SL.bigram_predict(
        tr_train, tr_test, len(t_seen))
    cu1, cu3, _ = SL.unigram_predict(tr_train, tr_test)

    print("\n==================================================")
    print("(4) HELD-OUT NEXT-WORD PREDICTION (the key test)")
    print("==================================================")
    print(f"train utts {len(train_seqs)}  test utts {len(test_seqs)}")
    print(f"BASELINES (agent's grounded words):")
    print(f"  uniform chance   : {chance:.4f} (1/|lex|, |lex|={lexicon_size})")
    print(f"  frequency-only   : top-1 {u1:.3f}  top-3 {u3:.3f}  "
          f"(most-common word, NO context)")
    print(f"WORD BIGRAM (real order):")
    print(f"  predictions made : {npred}")
    print(f"  top-1 accuracy   : {t1a:.3f}   (chance {chance:.4f})")
    print(f"  top-3 accuracy   : {t3a:.3f}")
    print(f"  top-1 / frequency: {t1a / max(u1,1e-9):.2f}x  "
          f"(>1 means context helps beyond raw frequency)")
    print(f"SHUFFLED (order destroyed, frequency kept):")
    print(f"  top-1 accuracy   : {st1:.3f}   top-3 {st3:.3f}")
    print(f"\nCONTRAST vs prior UNSUPERVISED sub-word:")
    print(f"  unsupervised sub-word top-1 : {PRIOR_UNSUP_SUBWORD_TOP1:.3f} "
          f"(~9%, the number to beat)")
    print(f"  helped real-word    top-1   : {t1a:.3f}  "
          f"({t1a / PRIOR_UNSUP_SUBWORD_TOP1:.2f}x the unsupervised result)")
    print(f"\nCEILING (TRUE transcript words, agent perception removed):")
    print(f"  frequency-only top-1 : {cu1:.3f}")
    print(f"  word bigram   top-1  : {ct1:.3f}   top-3 {ct3:.3f}  "
          f"(what clean word bigrams reach on this corpus)")

    # ---------------------------------------------------------------
    # VERDICT
    # ---------------------------------------------------------------
    print("\n==================================================")
    print("VERDICT")
    print("==================================================")
    has_lexicon = recurrence > 0.05 and lexicon_size < total
    has_struct = h_next_cur < h_next - 1e-6
    beats_freq = t1a > u1 * 1.10
    beats_unsup = t1a > PRIOR_UNSUP_SUBWORD_TOP1 * 1.10
    collapses = st1 < t1a * 0.7
    print(f"(i)   real-word lexicon emerged           : "
          f"{'YES' if has_lexicon else 'NO'} "
          f"({lexicon_size} words, recurrence {recurrence:.3f})")
    print(f"(ii)  H(next|cur) < H(next)               : "
          f"{'YES' if has_struct else 'NO'} "
          f"(gain {h_next - h_next_cur:.2f} bits)")
    print(f"(iii) word bigram beats frequency         : "
          f"{'YES' if beats_freq else 'NO'} "
          f"(bigram {t1a:.3f} vs frequency {u1:.3f})")
    print(f"(iv)  beats unsupervised sub-word ~9%     : "
          f"{'YES' if beats_unsup else 'NO'} "
          f"(real-word {t1a:.3f} vs sub-word {PRIOR_UNSUP_SUBWORD_TOP1:.3f})")
    print(f"(v)   collapses when shuffled             : "
          f"{'YES' if collapses else 'NO'} "
          f"(real {t1a:.3f} -> shuffled {st1:.3f})")
    success = (has_lexicon and has_struct and beats_freq
               and beats_unsup and collapses)
    print(f"\n>>> {'SUCCESS' if success else 'PARTIAL / NULL'}: with the "
          f"helper + more sentences the agent "
          f"{'DOES' if success else 'does NOT cleanly'} learn materially "
          f"more (real WORD-level structure) than the unsupervised "
          f"sub-word baseline.")
    if pos_acc < 0.25:
        print(f"    HONEST CAVEAT: position-exact alignment is only "
              f"{pos_acc:.1%} — the segment->word grounding is lossy, so "
              f"the agent's perceived-word lexicon is polluted relative to "
              f"the true transcript. Word-level structure above is over "
              f"the agent's NOISY grounded words, not the clean transcript. "
              f"The ceiling row shows the gap that cleaner alignment would "
              f"recover.")


if __name__ == "__main__":
    main()

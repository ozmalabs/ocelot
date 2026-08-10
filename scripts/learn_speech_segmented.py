"""SEGMENT + GENERALIZE: learn speech from the corpus with word segmentation, then
test on a HELD-OUT show.

Builds on the relational-unit result (49 clean speaker-invariant units predict the
next unit, order real). Adds the next layer:
  1. WORD SEGMENTATION — segment the unit stream at TRANSITIONAL-PROBABILITY
     TROUGHS (Saffran statistical word segmentation: TP is high within words, dips
     at word boundaries). Local-minimum TP -> boundary; parameter-free.
  2. HELD-OUT GENERALIZATION — train the lexicon + transition model + word lexicon
     on TRAINING shows; then on a NEW show map its audio onto the FROZEN trained
     alphabet (match_sign, no minting) and test whether the trained model predicts
     the unseen show's units/words ABOVE its own frequency baseline. That is the
     difference between "learned these shows" and "learned the language."

One fast consumption pass captures per-utterance features (relational units built
offline so train/held-out is cleanly controlled); acquire_sign / match_sign are the
held operators; TP segmentation + the held-out measurement are the analysis.

Run:  python -m scripts.learn_speech_segmented [wall_seconds] [n_heldout_titles]
"""
from __future__ import annotations
import math
import random
import sys
import threading
import time

import numpy as np

sys.path.insert(0, "."); sys.path.insert(0, "runners/dsl/python")
import scripts.watch_jellyfin_cortex as W
W.VISION = False
W.FAST_FORWARD = True
RUN_SECONDS = int(sys.argv[1]) if len(sys.argv) > 1 else 360
N_HELDOUT = int(sys.argv[2]) if len(sys.argv) > 2 else 2

import substrate_rs as srs                                       # noqa: E402
from substrate_rs import audio as A, speech as SP                # noqa: E402
from scripts.jellyfin_world import JellyfinWorld                 # noqa: E402

random.seed(7)
N_BANDS, N_WIN = 16, 4


def rank_feat(f):
    # GRAPH-NATIVE: per-window relational rank = the held substrate op (Rust).
    a = np.asarray(f, dtype=np.float32).reshape(N_WIN, N_BANDS)
    return np.concatenate([srs.Substrate.shape_signature([float(x) for x in row])
                           for row in a]).astype(np.float32)


# ---- transition-probability word segmentation (Saffran) ----
def tp_table(seqs):
    uni, fwd = {}, {}
    for seq in seqs:
        for a, b in zip(seq, seq[1:]):
            uni[a] = uni.get(a, 0) + 1
            fwd.setdefault(a, {})[b] = fwd.setdefault(a, {}).get(b, 0) + 1
    return {a: {b: c / uni[a] for b, c in nx.items()} for a, nx in fwd.items()}


def tp(table, a, b, default=1.0):
    return table.get(a, {}).get(b, default)


def segment(seq, table):
    """Cut at LOCAL MINIMA of transitional probability (word boundaries)."""
    if len(seq) < 2:
        return [tuple(seq)] if seq else []
    words, cur = [], [seq[0]]
    for i in range(1, len(seq)):
        here = tp(table, seq[i - 1], seq[i])
        prev = tp(table, seq[i - 2], seq[i - 1]) if i >= 2 else 1.0
        nxt = tp(table, seq[i], seq[i + 1]) if i + 1 < len(seq) else 1.0
        if here < prev and here < nxt:           # trough -> boundary before seq[i]
            words.append(tuple(cur)); cur = [seq[i]]
        else:
            cur.append(seq[i])
    words.append(tuple(cur))
    return words


# ---- prediction + controls ----
def bigram_rank(seqs):
    bg = {}
    for seq in seqs:
        for a, b in zip(seq, seq[1:]):
            bg.setdefault(a, {})[b] = bg.setdefault(a, {}).get(b, 0) + 1
    return {a: max(nx.items(), key=lambda kv: kv[1])[0] for a, nx in bg.items()}


def predict_top1(ranked, seqs):
    hit = npred = 0
    for seq in seqs:
        for a, b in zip(seq, seq[1:]):
            if a in ranked:
                npred += 1; hit += (ranked[a] == b)
    return (hit / npred if npred else 0.0), npred


def freq_top1(train_seqs, test_seqs):
    freq = {}
    for seq in test_seqs:                         # held-out's OWN most-frequent (conservative)
        for b in seq[1:]:
            freq[b] = freq.get(b, 0) + 1
    if not freq:
        return 0.0
    top = max(freq.items(), key=lambda kv: kv[1])[0]
    hit = npred = 0
    for seq in test_seqs:
        for b in seq[1:]:
            npred += 1; hit += (b == top)
    return hit / npred if npred else 0.0


def shuffled(seqs):
    toks = [t for c in seqs for t in c]
    random.shuffle(toks)
    out, i = [], 0
    for L in [len(c) for c in seqs]:
        out.append(toks[i:i + L]); i += L
    return out


def main():
    print("=" * 80)
    print(f"SEGMENT + GENERALIZE — {RUN_SECONDS}s consume, hold out last {N_HELDOUT} shows")
    print("=" * 80)
    s = srs.Substrate()
    A.seed_audio_grammar(s); A.seed_native_codec_grammar(s); SP.seed_speech_grammar(s)
    s.memory_bound(20000, 256 * 1024 * 1024, 3)
    s.memory_disposable_capacity(16 * 1024 * 1024, 2048)
    throwaway = SP.open_lexicon(s, name="online")

    jf = JellyfinWorld().connect(); jf.ingest_catalog(s)
    master = W.MasterClock(fast_forward=True)
    url_box = [None]; commit = threading.Lock()
    acx = W.AudioCortex(s, master, throwaway, url_box, commit)
    acx.heard_chunks = []
    feats = []
    acx.feature_transform = lambda f: (feats.append(np.asarray(f, np.float32)), f)[1]
    acx.start()

    def robust(fn, *a, tries=4, **k):
        for i in range(tries):
            try:
                return fn(*a, **k)
            except Exception:
                time.sleep(2 * (i + 1))
        return None

    titles = []; title_chunk_start = []; t0 = time.time()
    while time.time() - t0 < RUN_SECONDS:
        picks = robust(jf.choose, s, n=1, watched_series=titles)
        if not picks:
            if time.time() - t0 < RUN_SECONDS - 20:
                continue
            break
        title = picks[0]
        eps = robust(jf.episodes, title["id"], limit=1)
        url = robust(jf.stream_url, eps[0]["id"]) if eps else None
        if not url:
            titles.append(title["name"]); continue
        dur = float(eps[0].get("runtime_s") or 0.0) or 600.0
        title_chunk_start.append(len(acx.heard_chunks))
        url_box[0] = url; master.start_title(0.0, duration_s=dur); acx.ff_done = False
        p0 = time.time()
        while not acx.ff_done:
            if time.time() - t0 > RUN_SECONDS or time.time() - p0 > 300:
                break
            time.sleep(0.1)
        titles.append(title["name"])
        with commit:
            s.memory_forget_type("CortexStamp")
        print(f"  consumed {len(titles)}: {title['name'][:34]:<34} "
              f"{(master.position() or 0)/60:5.1f}min  utts={len(feats)}")
        url_box[0] = None
    acx.stop(); time.sleep(0.3)

    # regroup captured features into chunks, tag each chunk with its title index
    lengths = [len(c) for c in acx.heard_chunks]
    feat_chunks, chunk_title, i, ti = [], [], 0, 0
    starts = title_chunk_start + [len(acx.heard_chunks)]
    for ci, L in enumerate(lengths):
        while ti + 1 < len(starts) and ci >= starts[ti + 1]:
            ti += 1
        if i + L <= len(feats):
            feat_chunks.append(feats[i:i + L]); chunk_title.append(ti)
        i += L

    n_titles = len(titles)
    if n_titles < N_HELDOUT + 2:
        print(f"\n  only {n_titles} titles — need >= {N_HELDOUT+2}. Run longer."); return
    held_set = set(range(n_titles - N_HELDOUT, n_titles))
    train_fc = [fc for fc, t in zip(feat_chunks, chunk_title) if t not in held_set]
    held_fc = [fc for fc, t in zip(feat_chunks, chunk_title) if t in held_set]

    # build FROZEN relational lexicon on TRAIN; acquire train unit sequences
    lex = SP.open_lexicon(s, name="train")
    train_seqs = []
    for fc in train_fc:
        seq = [SP.acquire_sign(s, lex, rank_feat(f), threshold=0.85)[0] for f in fc]
        train_seqs.append([sgn.value for sgn in seq if sgn is not None])
    train_seqs = [c for c in train_seqs if len(c) >= 2]
    lex_size = len(SP.lexicon_signs(s, lex))

    # HELD-OUT: map onto the FROZEN alphabet via match_sign (no minting); OOV=-1
    held_seqs, oov = [], 0
    for fc in held_fc:
        seq = []
        for f in fc:
            sgn, _ = SP.match_sign(s, lex, rank_feat(f), threshold=0.85)
            if sgn is None:
                oov += 1; seq.append(-1)
            else:
                seq.append(sgn.value)
        held_seqs.append(seq)
    held_seqs = [c for c in held_seqs if len(c) >= 2]
    held_tok = sum(len(c) for c in held_seqs)

    # ---- TRAIN: TP segmentation + models ----
    table = tp_table(train_seqs)
    train_words = [w for seq in train_seqs for w in segment(seq, table)]
    from collections import Counter
    wc = Counter(train_words)
    recurring = {w for w, c in wc.items() if c >= 2}
    mean_len = sum(len(w) for w in train_words) / max(len(train_words), 1)

    unit_ranked = bigram_rank(train_seqs)
    train_word_seqs = [segment(seq, table) for seq in train_seqs]
    word_ranked = bigram_rank(train_word_seqs)

    print("\n" + "=" * 80)
    print("WHAT IT LEARNED  (train: %d shows, held-out: %d shows)"
          % (n_titles - N_HELDOUT, N_HELDOUT))
    print("=" * 80)
    print(f"  UNITS  : {lex_size} relational signs (frozen alphabet)")
    print(f"  WORDS  : TP-trough segmentation -> {len(wc)} distinct words "
          f"({len(recurring)} recurring), mean {mean_len:.2f} units/word")
    print("  top recurring words (unit-id tuples seen most):")
    for w, c in wc.most_common(6):
        print(f"    {w}  x{c}")

    # ---- HELD-OUT GENERALIZATION ----
    print(f"\n  HELD-OUT next-UNIT prediction (trained model on an UNSEEN show, "
          f"{held_tok} units, OOV={oov}):")
    hu, npred = predict_top1(unit_ranked, held_seqs)
    hf = freq_top1(train_seqs, held_seqs)
    hs, _ = predict_top1(unit_ranked, shuffled(held_seqs))
    print(f"    trained bigram top-1 = {hu:.3f}   held-out freq baseline = {hf:.3f}"
          f"  ({hu/max(hf,1e-9):.2f}x)   chance = {1/max(lex_size,1):.4f}")
    print(f"    shuffle held-out -> {hs:.3f}  ({'COLLAPSES (order generalizes)' if hs < 0.7*hu else 'no collapse'})")

    held_word_seqs = [segment(seq, table) for seq in held_seqs]
    hw, wnp = predict_top1(word_ranked, held_word_seqs)
    held_words = [w for seq in held_word_seqs for w in seq]
    overlap = sum(1 for w in held_words if w in recurring) / max(len(held_words), 1)
    print(f"\n  HELD-OUT next-WORD prediction ({wnp} preds): trained word-bigram "
          f"top-1 = {hw:.3f}")
    print(f"  WORD OVERLAP: {overlap:.2f} of held-out word tokens are recurring "
          f"TRAIN words (shared vocabulary across shows)")
    print("\n  VERDICT:", end=" ")
    if hu > hf and hs < 0.7 * hu:
        print("the trained model PREDICTS AN UNSEEN SHOW above its own baseline and "
              "collapses under shuffle -> the structure GENERALIZES (learned the language).")
    else:
        print("held-out prediction at/below baseline -> learned these shows, not yet "
              "the shared language (see numbers).")
    print("=" * 80)


if __name__ == "__main__":
    main()

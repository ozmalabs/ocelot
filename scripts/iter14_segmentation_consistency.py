"""iter-14 — SEGMENTATION CONSISTENCY: make the same word segment to the same
representation WITHIN a speaker. This is the binding blocker for continuous-speech
recognition diagnosed iter-13: the corpus-TP chunker cuts at transitional-
probability troughs that JITTER with coarticulation, so the same word is cut into a
different span each time -> continuous chunks of the same word don't even match
WITHIN one speaker (full-DTW 0.025, ~chance), vs FSDD isolated digits 0.875.
Everything downstream (per-speaker CMVN cross-speaker invariance, lexicon
clustering) is moot until the within-speaker chunks are consistent.

THE FORWARD-BUILD (the agent's lever, from its own science). domains/
landmark_segmentation: anchor boundaries to a STABLE acoustic landmark — the
sonority ENVELOPE valley — instead of the jittery TP troughs. A word/syllable
boundary is a PHYSICAL constriction of the vocal tract -> a sonority energy valley,
tied to articulation, so it recurs for the same word regardless of which codebook
unit each frame lands in. The valley is the agent's own order-1-time sign-change
concept (order_n_concepts) on the energy curve, evaluated by a graph-resident
boundary Term (valley_boundary_term). See landmark_segmentation for the science.

A second lever, ablated independently: BOUNDARY-JITTER-INVARIANT representation —
describe each chunk by its duration-normalised trajectory SHAPE (resample to a
fixed number of time-slots) so that +/- a few frames of boundary jitter don't
change the vector. This is the agent's rate-invariant order_n trajectory move
(continuous_speech_recognition._resample_traj), here used to make the COMPARISON
robust to residual boundary jitter rather than the segmentation itself.

MEASURE (fast within-speaker DTW probe FIRST, iterate here):
  (1) WITHIN-SPEAKER full-DTW on continuous chunks of the SAME word (per speaker):
      BEFORE (corpus-TP chunker, iter-13 path) -> AFTER (landmark chunker), per
      lever (ablation). SHUFFLE control (shuffled word labels -> collapse). Does
      the same word now match itself, toward FSDD digits' ~0.78?
  (2) IF within-speaker closes (> ~0.5): apply per-speaker CMVN (the proven
      cross-speaker fix) and measure CROSS-speaker DTW; if it carries, run
      recognition vs unigram on held-out speakers.

World-adapter only: it wires the agent's builds and reports numbers. No labels in
the segmentation, no search, no tuning.

Run: python -m scripts.iter14_segmentation_consistency [n_speakers] [utts_per_spk]
                                                        [probe_chunks]
"""
import os
import sys
import time
import random
from collections import defaultdict

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import scripts.sentence_learning as SL
from domains.invariant_units import invariant_transform, canonical_log_centroid
import domains.xspeaker_norm as XN
import domains.landmark_segmentation as LS
from scripts.continuous_speech_recognition import (
    words_of, frames_of, kmeans, coarse_stream_of, chunk_with_corpus_tp,
    align_chunks_to_words, _resample_traj, wer,
)
from scripts.iter13_continuous_xspeaker import (
    frame_corpus, apply_per_utterance, apply_per_speaker, build_corpus_tp,
    _matchable_pool, _shuffled,
)
from substrate_rs import Substrate


def full_dtw(A, B):
    """UNBANDED DTW over frame matrices — full alignment, no band sentinel. The
    banded dtw() in continuous_speech_recognition returns a ~1e16 INF sentinel when
    the two chunks' length ratio exceeds its 0.25 band; landmark chunks have high
    length variance, so banding corrupts the nearest-neighbour metric (it picks a
    length-compatible chunk regardless of content). This unbanded version always
    completes; cost is O(na*nb) which is fine at chunk scale."""
    A = np.asarray(A, dtype=np.float64)
    B = np.asarray(B, dtype=np.float64)
    na, nb = A.shape[0], B.shape[0]
    if na == 0 or nb == 0:
        return 1e18
    prev = np.full(nb + 1, np.inf)
    prev[0] = 0.0
    for i in range(1, na + 1):
        cur = np.full(nb + 1, np.inf)
        ai = A[i - 1]
        d_row = np.linalg.norm(B - ai, axis=1)
        for j in range(1, nb + 1):
            best = min(prev[j], cur[j - 1], prev[j - 1])
            cur[j] = d_row[j - 1] + best
        prev = cur
    return prev[nb] / (na + nb)


# --------------------------------------------------------------------------
# CHUNKERS — the BEFORE (corpus-TP, jittery) and the AFTER (landmark, stable).
# Both take a normalised frame matrix and return real-frame blocks; a fresh
# Substrate per utterance keeps the graph O(n) (same rationale as iter-13).
# --------------------------------------------------------------------------

def chunk_corpus_tp(M, C, corpus_tp, corpus_level, tag):
    """BEFORE: the iter-13 corpus-TP chunker (TP troughs on the codebook stream)."""
    sub = Substrate()
    cids, flens = coarse_stream_of(sub, M, C)
    return chunk_with_corpus_tp(sub, M, cids, flens, corpus_tp, corpus_level, tag)


def chunk_landmark(M, tag, min_sep=3, smooth=2, gate="mean"):
    """AFTER: the agent's sonority-envelope valley landmark chunker (graph-resident
    boundary Term over the energy envelope). Boundary-STABLE. gate="mean" = sub-mean
    valleys (word/phrase scale); gate="syllable" = every envelope local min."""
    sub = Substrate()
    return LS.landmark_chunk_utterance(sub, M, tag, min_sep=min_sep,
                                       smooth=smooth, gate=gate)


# --------------------------------------------------------------------------
# Build (block, word, speaker) chunk lists under a given chunker + represent each
# chunk either as its raw frame matrix (full-DTW compared) OR as a duration-
# normalised trajectory (jitter-invariant; compared by Euclidean = DTW on equal
# lengths). Word = proportional-frame alignment to the transcript (unchanged).
# --------------------------------------------------------------------------

def chunks_with_words(normed, chunker, tag, repr_mode="raw", n_slots=8):
    out = []
    for ui, (M, words, spk) in enumerate(normed):
        blocks = chunker(M, f"{tag}_{ui}")
        lengths = [L for _, L in blocks]
        aligned = align_chunks_to_words(lengths, words)
        for (block, _L), w in zip(blocks, aligned):
            if repr_mode == "rate_inv":
                vec = _resample_traj(block, n_slots)   # (n_slots, bands) shape
                out.append((np.asarray(vec, dtype=np.float64), w, spk))
            else:
                out.append((np.asarray(block, dtype=np.float64), w, spk))
    return out


# --------------------------------------------------------------------------
# WITHIN-SPEAKER full-DTW probe (the fast inner test). For each query chunk whose
# word RECURS for the same speaker, find its nearest WITHIN-speaker neighbour by
# full DTW and ask if it carries the same word. Chance = 1/n_words. Mirrors
# iter-13's metric, restricted to the within-speaker question.
# --------------------------------------------------------------------------

def within_speaker_dtw(chunks, max_n=400, max_q=160, seed=0):
    rng = random.Random(seed)
    if len(chunks) > max_n:
        idx = list(range(len(chunks)))
        rng.shuffle(idx)
        chunks = [chunks[i] for i in idx[:max_n]]
    mats = [c[0] for c in chunks]
    words = [c[1] for c in chunks]
    spk = [c[2] for c in chunks]
    n = len(mats)
    _, within_q = _matchable_pool(chunks)
    if len(within_q) > max_q:
        rng.shuffle(within_q)
        within_q = within_q[:max_q]
    within_q = set(within_q)
    hit = tot = 0
    for i in range(n):
        if i not in within_q:
            continue
        best = (1e18, None)
        for j in range(n):
            if i == j or spk[j] != spk[i]:
                continue
            d = full_dtw(mats[i], mats[j])
            if d < best[0]:
                best = (d, j)
        if best[1] is not None:
            tot += 1
            hit += (words[best[1]] == words[i])
    return (hit / tot if tot else 0.0), tot, n


def shuffle_within(chunks, max_n=400, max_q=160, seed=0):
    sh = [(b, w, s) for (b, _, s), w in
          zip(chunks, _shuffled([c[1] for c in chunks], seed))]
    return within_speaker_dtw(sh, max_n=max_n, max_q=max_q, seed=seed)


def intra_inter_separation(chunks, max_pairs=4000, seed=0):
    """A MORE statistically powerful consistency signal than nearest-neighbour acc at
    low recurrence: the paired distance separation. For chunks of the SAME word from
    the SAME speaker (intra), vs different words same speaker (inter), compare the
    mean full-DTW distance. separation = (inter_mean - intra_mean)/inter_mean > 0
    means the same word is genuinely closer to itself than to other words — the
    direct test of whether segmentation produced a consistent unit. Returns
    (separation, intra_mean, inter_mean, n_intra, n_inter)."""
    rng = random.Random(seed)
    by_ws = defaultdict(list)          # (word, spk) -> [block idx]
    for i, (_, w, s) in enumerate(chunks):
        if len(w) >= 4:
            by_ws[(w, s)].append(i)
    intra_pairs = []
    for (w, s), idxs in by_ws.items():
        if len(idxs) >= 2:
            for a in range(len(idxs)):
                for b in range(a + 1, len(idxs)):
                    intra_pairs.append((idxs[a], idxs[b]))
    rng.shuffle(intra_pairs)
    intra_pairs = intra_pairs[:max_pairs]
    # inter: same speaker, different word, sampled to match count
    by_spk = defaultdict(list)
    for i, (_, w, s) in enumerate(chunks):
        if len(w) >= 4:
            by_spk[s].append(i)
    inter_pairs = []
    spks = [s for s in by_spk if len(by_spk[s]) >= 2]
    for _ in range(len(intra_pairs) * 2):
        if not spks:
            break
        s = rng.choice(spks)
        i, j = rng.sample(by_spk[s], 2)
        if chunks[i][1] != chunks[j][1]:
            inter_pairs.append((i, j))
        if len(inter_pairs) >= len(intra_pairs):
            break
    if not intra_pairs or not inter_pairs:
        return 0.0, 0.0, 0.0, len(intra_pairs), len(inter_pairs)
    intra_d = [full_dtw(chunks[i][0], chunks[j][0]) for i, j in intra_pairs]
    inter_d = [full_dtw(chunks[i][0], chunks[j][0]) for i, j in inter_pairs]
    im = float(np.mean(intra_d))
    xm = float(np.mean(inter_d))
    sep = (xm - im) / xm if xm > 0 else 0.0
    return sep, im, xm, len(intra_pairs), len(inter_pairs)


def chunk_scale_stats(chunks, normed):
    """Mechanical diagnostics: chunks/word ratio + mean chunk frames."""
    n_words = sum(len(w) for _, w, _ in normed)
    n_chunks = len(chunks)
    mean_frames = np.mean([c[0].shape[0] for c in chunks]) if chunks else 0.0
    return n_chunks / max(n_words, 1), mean_frames, n_chunks


# --------------------------------------------------------------------------
# main.
# --------------------------------------------------------------------------

def main():
    n_speakers = int(sys.argv[1]) if len(sys.argv) > 1 else 12
    utts_per_spk = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    probe_chunks = int(sys.argv[3]) if len(sys.argv) > 3 else 400
    K = int(os.environ.get("K", "48"))
    MIN_SEP = int(os.environ.get("MIN_SEP", "3"))
    SMOOTH = int(os.environ.get("SMOOTH", "2"))
    N_SLOTS = int(os.environ.get("N_SLOTS", "8"))
    random.seed(1)
    np.random.seed(1)

    pairs = SL.gather_pairs()
    by_spk = defaultdict(list)
    for p in pairs:
        by_spk[p[1]].append(p)
    # pick speakers with the MOST utterances (within-speaker recurrence needs many
    # utts per speaker so words recur for the same speaker).
    spk_sorted = sorted(by_spk, key=lambda s: -len(by_spk[s]))[:n_speakers]
    sel = []
    for s in spk_sorted:
        ps = list(by_spk[s])
        random.shuffle(ps)
        sel.extend(ps[:utts_per_spk])
    print(f"LibriSpeech dev-clean: {len(pairs)} utts total")
    print(f"using {len(spk_sorted)} speakers x <= {utts_per_spk} utts "
          f"= {len(sel)} utts; codebook K={K}; "
          f"landmark min_sep={MIN_SEP} smooth={SMOOTH}")

    print("\nPerception + framing...")
    t0 = time.time()
    raw = frame_corpus(sel)
    print(f"  framed {len(raw)} utts ({time.time()-t0:.0f}s)")
    if len(raw) < 10:
        print("Too few usable utterances — aborting.")
        return

    canonical = canonical_log_centroid([M for M, _, _ in raw])
    # per-utterance invariant features (BEFORE front-end; the segmentation lever is
    # the variable here, not the speaker norm — hold the front-end fixed).
    normed = apply_per_utterance(raw, canonical)

    # corpus-TP for the BEFORE chunker
    sub = Substrate()
    C = kmeans(np.concatenate([M for M, _, _ in normed], axis=0)
               [:12000], K, seed=0)
    corpus_tp, corpus_level = build_corpus_tp(sub, normed, C)

    n_words = len(set(w for _, ws, _ in normed for w in ws))
    print(f"  distinct words {n_words}  chance ~{1.0/max(n_words,1):.4f}")

    print("\n" + "=" * 64)
    print("(1) WITHIN-SPEAKER full-DTW on continuous chunks of the SAME word")
    print("    per-lever ablation; shuffle-controlled")
    print("=" * 64)

    results = {}

    def run_lever(name, chunker, repr_mode):
        t0 = time.time()
        chunks = chunks_with_words(normed, chunker, name, repr_mode=repr_mode,
                                   n_slots=N_SLOTS)
        ratio, mframes, nch = chunk_scale_stats(chunks, normed)
        _, wq = _matchable_pool(chunks)
        within, tot, pool = within_speaker_dtw(chunks, max_n=probe_chunks)
        sh, shtot, _ = shuffle_within(chunks, max_n=probe_chunks)
        sep, im, xm, nin, nxt = intra_inter_separation(chunks)
        # shuffle control on the SEPARATION metric itself (the well-powered signal):
        # shuffled word labels must collapse separation to ~0.
        sh_chunks = [(b, w, s) for (b, _, s), w in
                     zip(chunks, _shuffled([c[1] for c in chunks], 0))]
        ssep, _, _, _, _ = intra_inter_separation(sh_chunks)
        results[name] = sep
        print(f"\n[{name}]  ({time.time()-t0:.0f}s)")
        print(f"  chunks/word {ratio:.2f}  mean chunk frames {mframes:.1f}  "
              f"within-answerable {len(wq)}")
        print(f"  WITHIN-speaker NN-acc = {within:.3f}  (n={tot}, pool={pool})  "
              f"[shuffle {sh:.3f}]")
        print(f"  intra/inter SEPARATION = {sep:+.3f}  "
              f"(intra DTW {im:.3f} < inter {xm:.3f}?  "
              f"n_intra={nin}, n_inter={nxt})")
        print(f"  SEPARATION shuffle ctrl = {ssep:+.3f}  "
              f"{'OK collapses' if abs(ssep) < 0.04 else 'WARN'}")
        return within, sh, sep, ssep

    # BEFORE: corpus-TP chunker, raw frame DTW (the iter-13 path)
    b_nn, _, b_sep, _ = run_lever(
        "BEFORE_corpusTP_raw",
        lambda M, tag: chunk_corpus_tp(M, C, corpus_tp, corpus_level, tag),
        "raw")

    # LEVER A: landmark (boundary-stable), MEAN gate (word/phrase scale), raw DTW
    la_nn, _, la_sep, la_ssep = run_lever(
        "AFTER_landmark_mean_raw",
        lambda M, tag: chunk_landmark(M, tag, min_sep=MIN_SEP, smooth=SMOOTH,
                                      gate="mean"),
        "raw")

    # LEVER A2: landmark SYLLABLE gate (every envelope local min, ~word scale), raw
    sy_nn, _, sy_sep, sy_ssep = run_lever(
        "AFTER_landmark_syllable_raw",
        lambda M, tag: chunk_landmark(M, tag, min_sep=MIN_SEP, smooth=SMOOTH,
                                      gate="syllable"),
        "raw")

    # LEVER B: landmark syllable gate + duration-normalised (jitter-invariant) repr
    lb_nn, _, lb_sep, lb_ssep = run_lever(
        "AFTER_landmark_syllable_rateinv",
        lambda M, tag: chunk_landmark(M, tag, min_sep=MIN_SEP, smooth=SMOOTH,
                                      gate="syllable"),
        "rate_inv")

    # ABLATION control: corpus-TP chunker + rate-inv repr (isolates whether the
    # gain is the STABLE BOUNDARY or merely the jitter-invariant representation).
    cb_nn, _, cb_sep, _ = run_lever(
        "ABLATE_corpusTP_rateinv",
        lambda M, tag: chunk_corpus_tp(M, C, corpus_tp, corpus_level, tag),
        "rate_inv")

    print("\n" + "=" * 64)
    print("WITHIN-SPEAKER CONSISTENCY SUMMARY")
    print("    (SEPARATION is the well-powered metric, ~1000 paired distances;")
    print("     NN-acc is reported but n=28-45 queries -> noisy at this scale)")
    print("=" * 64)
    print(f"  {'lever':<34}{'NN-acc':>8}{'SEPARATION':>12}")
    print(f"  {'BEFORE (corpus-TP, raw)':<34}{b_nn:>8.3f}{b_sep:>+12.3f}")
    print(f"  {'+ rate-inv repr only (ablation)':<34}{cb_nn:>8.3f}{cb_sep:>+12.3f}")
    print(f"  {'landmark mean-gate (raw)':<34}{la_nn:>8.3f}{la_sep:>+12.3f}")
    print(f"  {'landmark syllable-gate (raw)':<34}{sy_nn:>8.3f}{sy_sep:>+12.3f}")
    print(f"  {'landmark syllable + rate-inv':<34}{lb_nn:>8.3f}{lb_sep:>+12.3f}")
    best_sep = max(la_sep, sy_sep, lb_sep)
    best_nn = max(la_nn, sy_nn, lb_nn)
    print(f"\n  best AFTER separation = {best_sep:+.3f}  (vs BEFORE {b_sep:+.3f})")
    print(f"  best AFTER NN-acc     = {best_nn:.3f}  (vs BEFORE {b_nn:.3f}; "
          f"FSDD isolated digits within ~0.78)")
    # CLOSED needs the same word to actually RECOGNISE itself (NN-acc > 0.5);
    # PARTIAL needs a real, shuffle-verified separation gain over BEFORE.
    sep_clean = all(abs(s) < 0.04 for s in (la_ssep, sy_ssep, lb_ssep))
    closed = best_nn > 0.5
    partial = (best_sep > b_sep + 0.04) and best_sep > 0.05 and sep_clean
    verdict = ("CLOSED" if closed else
               ("PARTIAL (real but does not close)" if partial else
                "NO MOVEMENT"))
    print(f"\n  >>> within-speaker segmentation consistency: {verdict}")

    # ===================================================================
    # (2) CROSS-speaker + recognition, only if within-speaker CLOSED.
    # ===================================================================
    if not closed:
        print("\nWithin-speaker did not close (>0.5) -> cross-speaker / "
              "recognition NOT run (would not be informative). Report the "
              "residual above.")
        return

    print("\n" + "=" * 64)
    print("(2) within-speaker CLOSED -> apply per-speaker CMVN, CROSS-speaker DTW")
    print("=" * 64)
    run_cross_and_recognition(raw, canonical, MIN_SEP, SMOOTH, N_SLOTS,
                              probe_chunks, n_speakers)


def run_cross_and_recognition(raw, canonical, min_sep, smooth, n_slots,
                              probe_chunks, n_speakers):
    """Per-speaker CMVN front-end + landmark chunker; cross-speaker DTW on held-out
    speakers; recognition vs unigram if cross carries. Reuses iter-13 logic shapes
    but with the landmark chunker."""
    from scripts.iter13_continuous_xspeaker import within_cross_chunks
    variant = os.environ.get("XN_VARIANT", "uVTLN+ps_CMVN+PR")
    # split held-out speakers
    spk_ids = sorted(set(s for _, _, s in raw))
    n_held = max(2, len(spk_ids) // 3)
    held = set(spk_ids[:n_held])
    test_raw = [(M, w, s) for M, w, s in raw if s in held]
    print(f"  held-out speakers {len(held)}  test utts {len(test_raw)}")
    te_ps = apply_per_speaker(test_raw, canonical, variant)

    chunks = chunks_with_words(
        te_ps, lambda M, tag: chunk_landmark(M, tag, min_sep=min_sep,
                                             smooth=smooth),
        "cross", repr_mode="raw")
    w, c, n, wt, ct = within_cross_chunks(chunks, max_n=probe_chunks, seed=0)
    print(f"  WITHIN {w:.3f} (n={wt})  CROSS {c:.3f} (n={ct})  pool {n}")
    print(f"  cross-speaker invariance carries on consistent chunks? "
          f"{'YES' if c > 0.3 else 'NO / PARTIAL'}")


if __name__ == "__main__":
    main()

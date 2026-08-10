"""iter-15 STEP 2 — the dissimilarity-peak SEGMENTER: does anchoring boundaries to
the prominence PEAKS of the frame-to-frame change-rate move within-speaker same-word
consistency toward the gold-span ceiling?

The gate (iter15_goldspan_gate) shows OUR front-end reaches within-NN ~0.23-0.29 /
within-sep ~0.37 with GOLD word spans — the representation is sufficient (or nearly
so) and the remaining gap is the SEGMENTER. The agent forward-builds the SOTA
unsupervised boundary cue from its own order_n_concepts: a boundary is a prominence
PEAK of the order-1-time finite difference (change-rate) of its invariant features
(domains/dissimilarity_segmentation). This REPLACES TP-troughs / energy-valleys,
which ignore the change-rate.

MEASURE (the iter-14 within-speaker DTW probe, identical metric so numbers compare):
  BEFORE: corpus-TP chunker (iter-13 path) + landmark chunker (iter-14 best).
  AFTER:  dissimilarity-peak chunker, per-component ablation:
            (a) prominent-peak gate (mean-d) alone,
            (b) + duration penalty (min_sep, DPDP),
            (c) all-peaks gate (no prominence),
            (d) + template-averaging deferred to a later pass.
  Each: within-speaker NN-acc + intra/inter SEPARATION, SHUFFLE-controlled.
  Reference: gold-span ceiling (within-NN ~0.29, within-sep ~0.37 measured by the
  gate on the SAME front-end).

IF within-speaker closes toward the ceiling -> apply per-speaker CMVN (proven) ->
cross-speaker DTW + recognition vs unigram on held-out speakers.

World-adapter only: wires the agent's segmenter builds and reports numbers. No
labels in the segmentation, no search, no tuning.

Run: python -m scripts.iter15_dissimilarity_segmenter [n_speakers] [utts_per_spk]
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
from domains.invariant_units import canonical_log_centroid
import domains.dissimilarity_segmentation as DS
from scripts.continuous_speech_recognition import (
    kmeans, align_chunks_to_words,
)
from scripts.iter13_continuous_xspeaker import (
    frame_corpus, apply_per_utterance, apply_per_speaker, build_corpus_tp,
    _matchable_pool, _shuffled,
)
from scripts.iter14_segmentation_consistency import (
    chunk_corpus_tp, chunk_landmark, within_speaker_dtw, shuffle_within,
    intra_inter_separation, chunk_scale_stats,
)
from substrate_rs import Substrate


# --------------------------------------------------------------------------
# AFTER chunker: the agent's dissimilarity-peak segmenter (fresh Substrate per
# utterance, same O(n) rationale as iter-13/14).
# --------------------------------------------------------------------------

def chunk_dissim(M, tag, min_sep=3, smooth=1, metric="cosine", gate="prominent"):
    sub = Substrate()
    return DS.dissimilarity_chunk_utterance(sub, M, tag, min_sep=min_sep,
                                            smooth=smooth, metric=metric,
                                            gate=gate)


def chunks_with_words(normed, chunker, tag):
    out = []
    for ui, (M, words, spk) in enumerate(normed):
        blocks = chunker(M, f"{tag}_{ui}")
        lengths = [L for _, L in blocks]
        aligned = align_chunks_to_words(lengths, words)
        for (block, _L), w in zip(blocks, aligned):
            out.append((np.asarray(block, dtype=np.float64), w, spk))
    return out


def main():
    n_speakers = int(sys.argv[1]) if len(sys.argv) > 1 else 12
    utts_per_spk = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    probe_chunks = int(sys.argv[3]) if len(sys.argv) > 3 else 450
    K = int(os.environ.get("K", "48"))
    MIN_SEP = int(os.environ.get("MIN_SEP", "3"))
    SMOOTH = int(os.environ.get("SMOOTH", "1"))
    METRIC = os.environ.get("METRIC", "cosine")
    GOLD_NN = float(os.environ.get("GOLD_NN", "0.29"))     # gate-measured ceiling
    GOLD_SEP = float(os.environ.get("GOLD_SEP", "0.37"))
    random.seed(1)
    np.random.seed(1)

    pairs = SL.gather_pairs()
    by_spk = defaultdict(list)
    for p in pairs:
        by_spk[p[1]].append(p)
    spk_sorted = sorted(by_spk, key=lambda s: -len(by_spk[s]))[:n_speakers]
    sel = []
    for s in spk_sorted:
        ps = list(by_spk[s])
        random.shuffle(ps)
        sel.extend(ps[:utts_per_spk])
    print(f"=== iter-15 STEP 2: dissimilarity-peak segmenter ===")
    print(f"LibriSpeech dev-clean: {len(spk_sorted)} speakers x <= {utts_per_spk} "
          f"utts = {len(sel)} utts; K={K}; metric={METRIC} min_sep={MIN_SEP} "
          f"smooth={SMOOTH}")
    print(f"gold-span ceiling (gate, same front-end): within-NN ~{GOLD_NN}  "
          f"within-sep ~{GOLD_SEP:+.2f}")

    print("\nPerception + framing...")
    t0 = time.time()
    raw = frame_corpus(sel)
    print(f"  framed {len(raw)} utts ({time.time()-t0:.0f}s)")
    if len(raw) < 10:
        print("Too few usable utterances — aborting.")
        return

    canonical = canonical_log_centroid([M for M, _, _ in raw])
    normed = apply_per_utterance(raw, canonical)   # hold front-end fixed; vary segmenter

    C = kmeans(np.concatenate([M for M, _, _ in normed], axis=0)[:12000], K, seed=0)
    sub = Substrate()
    corpus_tp, corpus_level = build_corpus_tp(sub, normed, C)

    n_words = len(set(w for _, ws, _ in normed for w in ws))
    print(f"  distinct words {n_words}  chance ~{1.0/max(n_words,1):.4f}")

    print("\n" + "=" * 66)
    print("(1) WITHIN-SPEAKER consistency — per-component ablation, shuffle-ctrl")
    print("=" * 66)

    def run_lever(name, chunker):
        t0 = time.time()
        chunks = chunks_with_words(normed, chunker, name)
        ratio, mframes, _ = chunk_scale_stats(chunks, normed)
        _, wq = _matchable_pool(chunks)
        within, tot, pool = within_speaker_dtw(chunks, max_n=probe_chunks)
        sh, _, _ = shuffle_within(chunks, max_n=probe_chunks)
        sep, im, xm, nin, _ = intra_inter_separation(chunks)
        sh_chunks = [(b, w, s) for (b, _, s), w in
                     zip(chunks, _shuffled([c[1] for c in chunks], 0))]
        ssep, _, _, _, _ = intra_inter_separation(sh_chunks)
        print(f"\n[{name}]  ({time.time()-t0:.0f}s)")
        print(f"  chunks/word {ratio:.2f}  mean chunk frames {mframes:.1f}  "
              f"within-answerable {len(wq)}")
        print(f"  WITHIN NN  {within:.3f}  (n={tot}, pool={pool})  [shuffle {sh:.3f}]")
        print(f"  SEPARATION {sep:+.3f}  (intra {im:.3f} < inter {xm:.3f}? "
              f"n={nin})  [shuffle {ssep:+.3f} "
              f"{'OK' if abs(ssep) < 0.04 else 'WARN'}]")
        return {"name": name, "nn": within, "nn_sh": sh, "sep": sep,
                "sep_sh": ssep, "ratio": ratio}

    rows = []
    # BEFORE references
    rows.append(run_lever(
        "BEFORE_corpusTP",
        lambda M, tag: chunk_corpus_tp(M, C, corpus_tp, corpus_level, tag)))
    rows.append(run_lever(
        "BEFORE_landmark_syllable",
        lambda M, tag: chunk_landmark(M, tag, min_sep=MIN_SEP, smooth=2,
                                      gate="syllable")))
    # AFTER: dissimilarity-peak, ablated
    rows.append(run_lever(
        "DISSIM_allpeaks (no prominence, no dur)",
        lambda M, tag: chunk_dissim(M, tag, min_sep=1, smooth=SMOOTH,
                                    metric=METRIC, gate="all")))
    rows.append(run_lever(
        "DISSIM_prominent (mean-d gate, no dur)",
        lambda M, tag: chunk_dissim(M, tag, min_sep=1, smooth=SMOOTH,
                                    metric=METRIC, gate="prominent")))
    rows.append(run_lever(
        "DISSIM_prominent+dur (DPDP)",
        lambda M, tag: chunk_dissim(M, tag, min_sep=MIN_SEP, smooth=SMOOTH,
                                    metric=METRIC, gate="prominent")))
    rows.append(run_lever(
        "DISSIM_allpeaks+dur",
        lambda M, tag: chunk_dissim(M, tag, min_sep=MIN_SEP, smooth=SMOOTH,
                                    metric=METRIC, gate="all")))

    print("\n" + "=" * 66)
    print("WITHIN-SPEAKER SUMMARY  (vs gold ceiling "
          f"NN~{GOLD_NN} sep~{GOLD_SEP:+.2f})")
    print("=" * 66)
    print(f"  {'lever':<42}{'NN':>7}{'SEP':>9}{'sep_sh':>9}")
    for r in rows:
        print(f"  {r['name']:<42}{r['nn']:>7.3f}{r['sep']:>+9.3f}"
              f"{r['sep_sh']:>+9.3f}")

    before_sep = max(rows[0]["sep"], rows[1]["sep"])
    before_nn = max(rows[0]["nn"], rows[1]["nn"])
    after = [r for r in rows if r["name"].startswith("DISSIM")]
    best = max(after, key=lambda r: r["sep"])
    best_nn = max(r["nn"] for r in after)
    clean = abs(best["sep_sh"]) < 0.04
    print(f"\n  best DISSIM: {best['name']}  sep {best['sep']:+.3f}  "
          f"NN {best_nn:.3f}  (shuffle {best['sep_sh']:+.3f} "
          f"{'clean' if clean else 'CONTAMINATED'})")
    print(f"  BEFORE best: sep {before_sep:+.3f}  NN {before_nn:.3f}")

    moved = (best["sep"] > before_sep + 0.04) and best["sep"] > 0.05 and clean
    frac = best["sep"] / GOLD_SEP if GOLD_SEP > 0 else 0.0
    closed = best_nn > GOLD_NN - 0.03 and best["sep"] > GOLD_SEP - 0.05 and clean
    if closed:
        verdict = "CLOSED toward gold ceiling"
    elif moved:
        verdict = (f"PARTIAL — real shuffle-verified gain "
                   f"({frac*100:.0f}% of gold-sep ceiling)")
    else:
        verdict = "NO MOVEMENT over BEFORE"
    print(f"\n  >>> dissimilarity-peak segmenter verdict: {verdict}")

    if not (closed or moved):
        print("\n  Did not move within-speaker consistency over the BEFORE "
              "chunkers -> cross-speaker / recognition NOT run.")
        return

    if not closed:
        print("\n  Partial (did not reach the ceiling) -> cross-speaker / "
              "recognition NOT run (would not be informative). Residual above.")
        return

    print("\n" + "=" * 66)
    print("(2) within-speaker CLOSED -> per-speaker CMVN, CROSS-speaker + recog")
    print("=" * 66)
    run_cross_and_recognition(raw, canonical, MIN_SEP, SMOOTH, METRIC,
                              probe_chunks)


def run_cross_and_recognition(raw, canonical, min_sep, smooth, metric,
                              probe_chunks):
    from scripts.iter13_continuous_xspeaker import within_cross_chunks
    variant = os.environ.get("XN_VARIANT", "uVTLN+ps_CMVN+PR")
    spk_ids = sorted(set(s for _, _, s in raw))
    n_held = max(2, len(spk_ids) // 3)
    held = set(spk_ids[:n_held])
    test_raw = [(M, w, s) for M, w, s in raw if s in held]
    print(f"  held-out speakers {len(held)}  test utts {len(test_raw)}")
    te_ps = apply_per_speaker(test_raw, canonical, variant)
    chunks = chunks_with_words(
        te_ps, lambda M, tag: chunk_dissim(M, tag, min_sep=min_sep,
                                           smooth=smooth, metric=metric,
                                           gate="prominent"), "cross")
    w, c, n, wt, ct = within_cross_chunks(chunks, max_n=probe_chunks, seed=0)
    print(f"  WITHIN {w:.3f} (n={wt})  CROSS {c:.3f} (n={ct})  pool {n}")
    print(f"  cross-speaker invariance carries on consistent chunks? "
          f"{'YES' if c > 0.3 else 'NO / PARTIAL'}")


if __name__ == "__main__":
    main()

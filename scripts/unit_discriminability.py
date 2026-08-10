"""unit_discriminability — THE DIRECT metric on the broken thing: are the sub-word
UNITS discriminable cross-speaker? Compares the OLD 32-k-means inventory vs the NEW
discriminable inventory (domains/discriminable_units) on held-out speakers, label-free.

A sub-word inventory is an alphabet only if a chunk of a given sound lands on the SAME
unit no matter WHO said it. Two cross-speaker discriminability measures (both label-
free, NO accuracy fitted):

  (1) QUANTIZATION COHERENCE (the agent's selector). Mean quantization MARGIN over
      held-out-speaker chunks = (d2 - d1)/(d2) between nearest and 2nd-nearest unit
      under native DtwTo. High = each token lands CLEANLY in one unit (the quantizer
      CLOSES). A blurry inventory has tokens equidistant to several units (margin ~ 0).

  (2) CROSS-SPEAKER UNIT AGREEMENT (the direct discriminability test). Split the
      HELD-OUT speakers into two disjoint halves. For each word, quantize half-1's
      chunks and half-2's chunks to unit-ID multisets, and measure their overlap
      (Jaccard of unit sets). If the units are discriminable cross-speaker, the SAME
      word from DISJOINT held-out speakers produces OVERLAPPING unit sets; if the units
      are confusable, a chunk lands on a different unit per speaker and overlap
      collapses. Reported AGAINST a unit-shuffle baseline (randomly relabel each
      chunk's unit -> destroys any real cross-speaker agreement) — same word's overlap
      must beat the shuffle, OR the inventory carries no cross-speaker identity.

This is the metric to MOVE: if the NEW units are not more discriminable here, nothing
downstream (composition) will work.

DISCIPLINE: native DtwTo quantization (substrate.evaluate); label-free (word labels
used ONLY to score overlap after the fact, never to build the inventory); world
adapter sequences owned machinery.

Run: python -m scripts.unit_discriminability [n_words] [n_train] [n_test] [k_units]
"""
import os
import sys
import random
import time
import wave
from collections import defaultdict

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from substrate_rs import Substrate
from scripts.invariant_units_accept import band_trajectory_matrix
from domains.relational_shape import relational_shape
from domains.dissimilarity_segmentation import find_peak_boundaries, chunk_by_peaks
from domains.discriminable_units import (
    word_chunks, Quantizer, coherence_score, build_discriminable_inventory,
    _phase_anchored_summary, _kmeans_inventory, _clean2d)

SC = "/tmp/sc"


def load_real(path):
    w = wave.open(path)
    raw = (np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16)
           .astype(np.float32) / 32768.0)
    if w.getframerate() == 16000:
        try:
            from scipy.signal import decimate
            raw = decimate(raw, 2)
        except Exception:
            raw = raw[::2]
    return np.ascontiguousarray(raw.astype(np.float32)), 8000


# ---- OLD chunking (small chunks, mean-pool summary) — exactly sublexical_composition.
def old_word_chunks(seg_sub, M_band, seq_tag, n_anchors, min_sep=3):
    cuts, _d = find_peak_boundaries(seg_sub, M_band, seq_tag, min_sep=min_sep,
                                    smooth=1, metric="cosine", gate="prominent")
    blocks = chunk_by_peaks(M_band, cuts)
    out = []
    for block, n in blocks:
        if n < 2:
            continue
        rs = relational_shape(block, n_anchors=n_anchors)
        rsc = _clean2d(rs) if rs is not None else None
        if rsc is not None and len(rsc) >= 2:
            out.append((rsc, rsc.mean(axis=0)))
    if not out:
        rs = relational_shape(M_band, n_anchors=n_anchors)
        rsc = _clean2d(rs) if rs is not None else None
        if rsc is not None and len(rsc) >= 2:
            out = [(rsc, rsc.mean(axis=0))]
    return out


def cross_speaker_agreement(unit_ids, unit_traj, chunks_by_word_half,
                            shuffle=False, seed=11):
    """(2) For each word: Jaccard overlap of the unit-ID SETS recovered from two
    disjoint held-out-speaker halves. Mean over words. shuffle=True randomly relabels
    each chunk's unit (destroys real cross-speaker agreement) for the baseline."""
    q = Quantizer(unit_ids, unit_traj)
    rng = random.Random(seed)
    ids = list(unit_ids)
    jacc = []
    for w, (ha, hb) in chunks_by_word_half.items():
        if not ha or not hb:
            continue
        def unit_set(instances):
            # instances: list of word-instances, each a list of (rs, su) chunks.
            s = set()
            for chs in instances:
                for (rs, _su) in chs:
                    u, _m = q.quantize(rs)
                    if shuffle:
                        u = rng.choice(ids)
                    s.add(u)
            return s
        sa, sb = unit_set(ha), unit_set(hb)
        if not sa and not sb:
            continue
        jacc.append(len(sa & sb) / max(len(sa | sb), 1))
    q.teardown()
    return float(np.mean(jacc)) if jacc else 0.0


def main():
    n_words = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    n_train = int(sys.argv[2]) if len(sys.argv) > 2 else 150
    n_test = int(sys.argv[3]) if len(sys.argv) > 3 else 150
    k_units = int(sys.argv[4]) if len(sys.argv) > 4 else 32
    n_anchors = 6
    n_phase = 6                # phase-anchored cluster summary length (lever 2)
    big_min_sep = 8            # syllable-scale granularity (lever 1); OLD uses 3
    random.seed(1)
    np.random.seed(1)

    t0 = time.time()
    avail = [w for w in sorted(os.listdir(SC))
             if os.path.isdir(os.path.join(SC, w)) and not w.startswith("_")
             and len([f for f in os.listdir(os.path.join(SC, w))
                      if f.endswith(".wav")]) > 200]
    words = avail[:n_words]
    print("=" * 72, flush=True)
    print("UNIT DISCRIMINABILITY — OLD 32-k-means vs NEW discriminable inventory",
          flush=True)
    print("=" * 72, flush=True)
    print(f"{len(words)}-way: {words}", flush=True)
    print(f"k_units={k_units}  n_anchors={n_anchors}  n_phase={n_phase}  "
          f"OLD min_sep=3  NEW min_sep={big_min_sep}", flush=True)

    data = {}
    for w in words:
        for fn in sorted(os.listdir(os.path.join(SC, w))):
            if fn.endswith(".wav"):
                data.setdefault(w, []).append(
                    (os.path.join(SC, w, fn), fn.split("_")[0]))

    # Hold out whole SPEAKERS for test (disjoint train/test speakers).
    test_spk = set()
    for w in words:
        spks = sorted({s for _, s in data[w]})
        test_spk |= set(spks[::6])
    train = [(p, w, s) for w in words for p, s in data[w] if s not in test_spk]
    test = [(p, w, s) for w in words for p, s in data[w] if s in test_spk]
    random.shuffle(train)
    random.shuffle(test)
    train, test = train[:n_train], test[:n_test]
    print(f"train {len(train)} (disjoint speakers); test {len(test)} held-out",
          flush=True)

    def band_M(path):
        x, fs = load_real(path)
        M = band_trajectory_matrix(x, fs)
        return M if M is not None and len(M) >= 2 else None

    print(f"\nextracting band matrices ({time.time()-t0:.0f}s)...", flush=True)
    tr_band = [(band_M(p), w, s) for p, w, s in train]
    te_band = [(band_M(p), w, s) for p, w, s in test]
    tr_band = [(M, w, s) for M, w, s in tr_band if M is not None]
    te_band = [(M, w, s) for M, w, s in te_band if M is not None]
    print(f"  usable: {len(tr_band)} train, {len(te_band)} test "
          f"({time.time()-t0:.0f}s)", flush=True)

    # Split TRAIN speakers into two disjoint halves for consistency selection (lever 3).
    tr_spk = sorted({s for _, _, s in tr_band})
    half_a_spk = set(tr_spk[0::2])
    # ------------------------------------------------------------------
    # build chunk lists for both pipelines.
    # ------------------------------------------------------------------
    def chunk_all(band_list, chunker, ms):
        out = []
        for i, (M, w, s) in enumerate(band_list):
            seg = Substrate()
            chs = chunker(seg, M, f"c{i}", n_anchors, ms) if chunker is old_word_chunks \
                else chunker(seg, M, f"c{i}", n_anchors, ms, n_phase)
            out.append((chs, w, s))
            del seg
        return out

    print("\nCHUNKING (OLD min_sep=3, NEW syllable-scale min_sep=%d)..." % big_min_sep,
          flush=True)
    old_tr = chunk_all(tr_band, old_word_chunks, 3)
    old_te = chunk_all(te_band, old_word_chunks, 3)
    new_tr = chunk_all(tr_band, word_chunks, big_min_sep)
    new_te = chunk_all(te_band, word_chunks, big_min_sep)
    o_avg = np.mean([len(c) for c, _, _ in old_tr])
    n_avg = np.mean([len(c) for c, _, _ in new_tr])
    print(f"  OLD chunks/word {o_avg:.2f}   NEW chunks/word {n_avg:.2f} "
          f"({time.time()-t0:.0f}s)", flush=True)

    # ------------------------------------------------------------------
    # OLD inventory: raw k-means over mean-pool summaries, all k kept.
    # ------------------------------------------------------------------
    print("\nbuilding OLD inventory (mean-pool k-means, all units kept)...",
          flush=True)
    old_chunks_only = [[(rs, su) for (rs, su) in chs] for chs, _, _ in old_tr]
    old_ids, old_traj = _kmeans_inventory(old_chunks_only, k_units, seed=0)
    print(f"  OLD inventory: {len(old_ids)} units", flush=True)

    # ------------------------------------------------------------------
    # NEW inventory: phase-anchored k-means + cross-speaker consistency select.
    # ------------------------------------------------------------------
    print("\nbuilding NEW inventory (phase-anchored + consistency select)...",
          flush=True)
    new_a = [[(rs, su) for (rs, su) in chs] for chs, _, s in new_tr
             if s in half_a_spk]
    new_b = [[(rs, su) for (rs, su) in chs] for chs, _, s in new_tr
             if s not in half_a_spk]
    new_ids, new_traj, new_coh_train = build_discriminable_inventory(
        (new_a, new_b), k_units, seed=0, consistency=True,
        log=lambda *a: print(*a, flush=True))
    print(f"  NEW inventory: {len(new_ids)} units "
          f"(train coherence {new_coh_train:.4f}, {time.time()-t0:.0f}s)", flush=True)

    # ==================================================================
    # MEASURE on HELD-OUT speakers.
    # ==================================================================
    old_te_chunks = [[(rs, su) for (rs, su) in chs] for chs, _, _ in old_te]
    new_te_chunks = [[(rs, su) for (rs, su) in chs] for chs, _, _ in new_te]

    print("\n" + "=" * 72, flush=True)
    print("(1) QUANTIZATION COHERENCE on HELD-OUT speakers (mean DtwTo margin)",
          flush=True)
    print("=" * 72, flush=True)
    old_coh = coherence_score(old_ids, old_traj, old_te_chunks)
    new_coh = coherence_score(new_ids, new_traj, new_te_chunks)
    print(f"  OLD  coherence = {old_coh:.4f}", flush=True)
    print(f"  NEW  coherence = {new_coh:.4f}   "
          f"({'+' if new_coh>old_coh else ''}{new_coh-old_coh:+.4f})", flush=True)

    # split held-out speakers into two disjoint halves for cross-speaker agreement.
    te_spk = sorted({s for _, _, s in te_band})
    halfA = set(te_spk[0::2])

    def by_word_half(te_struct):
        d = defaultdict(lambda: ([], []))
        for (chs, w, s) in te_struct:
            (d[w][0] if s in halfA else d[w][1]).append(chs)
        return d

    old_bw = by_word_half([(c, w, s) for (c, w, s) in
                           [(chs, w, s) for (chs, w, s) in old_te]])
    new_bw = by_word_half([(chs, w, s) for (chs, w, s) in new_te])

    print("\n" + "=" * 72, flush=True)
    print("(2) CROSS-SPEAKER UNIT AGREEMENT (same word, disjoint held-out halves)",
          flush=True)
    print("=" * 72, flush=True)
    old_agr = cross_speaker_agreement(old_ids, old_traj, old_bw)
    old_sh = cross_speaker_agreement(old_ids, old_traj, old_bw, shuffle=True)
    new_agr = cross_speaker_agreement(new_ids, new_traj, new_bw)
    new_sh = cross_speaker_agreement(new_ids, new_traj, new_bw, shuffle=True)
    print(f"  OLD  same-word unit Jaccard = {old_agr:.4f}  "
          f"(shuffle {old_sh:.4f}, lift {old_agr-old_sh:+.4f})", flush=True)
    print(f"  NEW  same-word unit Jaccard = {new_agr:.4f}  "
          f"(shuffle {new_sh:.4f}, lift {new_agr-new_sh:+.4f})", flush=True)

    print("\n" + "=" * 72, flush=True)
    print("VERDICT", flush=True)
    print("=" * 72, flush=True)
    print(f"  coherence   OLD {old_coh:.4f} -> NEW {new_coh:.4f}", flush=True)
    print(f"  agreement   OLD {old_agr:.4f}(lift{old_agr-old_sh:+.4f}) -> "
          f"NEW {new_agr:.4f}(lift{new_agr-new_sh:+.4f})", flush=True)
    if new_coh > old_coh and (new_agr - new_sh) > (old_agr - old_sh):
        print("\n  >>> NEW units MORE DISCRIMINABLE cross-speaker on BOTH measures. "
              "The alphabet is sharper — composition has a chance downstream.",
              flush=True)
    elif new_coh > old_coh or (new_agr - new_sh) > (old_agr - old_sh):
        print("\n  >>> PARTIAL: NEW units improve one discriminability measure, not "
              "both. Honest — report which moved.", flush=True)
    else:
        print("\n  >>> NO GAIN: NEW units are NOT more discriminable cross-speaker. "
              "Sub-word units may not be makeable discriminable at this scale on this "
              "data -> whole-word is the right granularity (outcome c).", flush=True)


if __name__ == "__main__":
    main()

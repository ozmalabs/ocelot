"""parakeet_acoustic_drive — GROUND the Parakeet ACOUSTIC LEVER on the LibriSpeech
REDUCED-CONTINUOUS at-chance venue. Measure, donkey-clean. Read the NUMBERS.

THE HYPOTHESIS UNDER TEST (docs/parakeet_teardown.md §6 — a PREDICTION, not a result).
The Parakeet teardown grounded three constructed acoustic structures on the FSDD
ISOLATED-DIGIT venue (scripts/parakeet_teardown_probe.py):
  - MONOTONIC alignment (DtwTo, the agent already owns): +0.0375 (load-bearing)
  - EXPLICIT DURATION (rate-normalise): +0.0000 (NULL on digits)
  - CONV-LOCAL delta (order-1 finite diff over time, F_t - F_{t-1}): -0.0125 (NULL on digits)
The teardown PREDICTED these two nulls would FLIP to positive on the REDUCED-CONTINUOUS
at-chance venue, where the STATIC ear is AT CHANCE (docs/real_data_drive.md: acoustic-only
0.0313 vs chance 0.0333) because static band-means UNDER-RESOLVE the acoustically-tiny
reduced function words, and the TRANSITION DERIVATIVE is the part that survives reduction.
By the silent-failure-grounding discipline that prediction is "needs grounding" until
measured. THIS PROBE MEASURES IT. The honest result may be NEGATIVE — if R2/R3 stay at
chance the prediction FAILS and the digit-venue nulls do NOT flip; that is a genuine
result, reported plainly. No sweep-to-find-a-win.

THE VENUE (reused, not re-invented): scripts/real_data_drive.py — LibriSpeech dev-clean
reduced-continuous function words, the agent's OWN sonority-valley word segmentation
(teach_via_valleys) aligned to the transcript, per-word A1-patch trajectories, LOSO over
speakers. We reuse harvest_word_trajectories + build_forward_model + the LibriSpeech
loading verbatim. The forward model = K medoid exemplars per train speaker per word.

THE PROBE — the ACOUSTIC-ONLY channel (NO context/bigram prior; adding the LM would
CONFOUND the question — the cross-model lesson is "the lever is ACOUSTIC STRUCTURE not
more-LM"). Three routes, IDENTICAL everything except the named front-end transform, all
through the SAME monotonic DtwTo recogniser (counts-not-nets, the same kernel shape as the
DtwTo Rust Term), LOSO:
  (R1) STATIC only                 — per-utt CMVN band trajectory. The current acoustic-only
                                     baseline; the do-contrast control. SHOULD reproduce the
                                     ~at-chance docs/real_data_drive.md result.
  (R2) STATIC + DELTA (conv-local) — append the order-1 finite diff over time (F_t - F_{t-1}),
                                     the agent's transition-contrast = FastConformer conv-local.
  (R3) STATIC + DELTA + DURATION   — R2 plus explicit duration: rate-normalise the trajectory
                                     to a canonical length L BEFORE the warp (Parakeet TDT).

REUSED TRANSFORMS (the EXACT structural choices already grounded in
scripts/parakeet_teardown_probe.py — imported, reported as FIXED, not re-tuned):
  static_feats   (per-utt CMVN)            teardown_probe:140
  conv_local     (order-1 delta over time) teardown_probe:165   -> doubles feature dim
  rate_normalised(L=32 linear interp)      teardown_probe:150
  monotonic_dtw  (band_frac=0.25 Sakoe-Chiba banded DP) teardown_probe:89
NOTE on R3 order: duration is applied to the static base FIRST (rate-normalise to L), THEN
delta is taken on the rate-normalised trajectory — so the delta is a clean finite-diff over
the canonical-length frames (no length mismatch between static and delta blocks).

THE SHUFFLE / do-contrast BACKSTOP: re-run the BEST acoustic route with the train LABELS
shuffled (speaker structure preserved, the word<->trajectory binding destroyed). A "gain"
that survives label-shuffle is a frequency/label artifact, not real acoustic structure, and
must COLLAPSE toward chance. chance = 1/|vocab| reported explicitly.

DONKEY-CLEAN: counts not nets — the monotonic DtwTo is the agent's banded-DTW reproduced as
a counts-not-nets metric (same transitions as the DtwTo Term); the recogniser is a 1-NN
argmin readout over LOSO exemplars. NO .fit, NO gradient, NO loss, NO optimiser, NO
torch/sklearn, NO sweep-to-maximise. The transform constants (L=32, band_frac=0.25, order-1
delta), the vocab size V and exemplar budget K are FIXED structural choices, reported, not
tuned. solve_for_n.py / weighted_admissibility / CortexLoop UNTOUCHED (this file imports none).

Run: PYTHONUNBUFFERED=1 python -m scripts.parakeet_acoustic_drive [n_utts] [n_speakers] [vocab] [K]
"""
from __future__ import annotations

import math
import os
import random
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ---- REUSE the venue machinery verbatim (LibriSpeech loading, the agent's valley
# word segmentation harvest, the multi-exemplar forward model). World adapter only. ----
import scripts.sentence_learning as SL
from scripts.real_data_drive import harvest_word_trajectories, build_forward_model

# ---- REUSE the EXACT constructed transforms + monotonic kernel from the teardown
# probe (FIXED structural choices, imported not re-derived). ----
from scripts.parakeet_teardown_probe import (
    static_feats,      # per-utt CMVN  (teardown_probe:140)
    rate_normalised,   # explicit duration, L=32 linear interp  (teardown_probe:150)
    conv_local,        # order-1 delta over time  (teardown_probe:165)
    monotonic_dtw,     # banded DTW, band_frac=0.25  (teardown_probe:89)
)


# ==========================================================================
# THE THREE FRONT-END ROUTES — identical everything except this named transform.
# Each maps a raw frames x patches A1 trajectory -> the route's feature matrix.
# build_forward_model stores exemplars as nested tuples (as_tuple); we np.asarray
# them back before transforming, so train & test go through the IDENTICAL pipe.
# ==========================================================================

def _to_M(x):
    if x is None:
        return None
    M = np.asarray(x, dtype=np.float32)
    return M if M.ndim == 2 and M.shape[0] >= 2 else None


def tx_static(M):
    """R1: STATIC only — per-utt CMVN band trajectory (current front-end)."""
    return static_feats(_to_M(M))


def tx_static_delta(M):
    """R2: STATIC + DELTA — conv-local order-1 finite diff over time appended."""
    F = static_feats(_to_M(M))
    return conv_local(F)


def tx_static_delta_dur(M):
    """R3: STATIC + DELTA + DURATION — rate-normalise the static trajectory to the
    canonical length L FIRST (explicit duration / TDT), THEN take the order-1 delta on
    the canonical-length frames and append it (conv-local)."""
    F = static_feats(_to_M(M))
    if F is None:
        return None
    F = rate_normalised(F)        # explicit duration: -> L frames
    return conv_local(F)          # conv-local delta on the rate-normalised frames


ROUTES = [
    ("R1 STATIC only (current acoustic-only baseline)", tx_static),
    ("R2 STATIC + DELTA (conv-local order-1)", tx_static_delta),
    ("R3 STATIC + DELTA + DURATION (rate-norm L=32, TDT)", tx_static_delta_dur),
]


# ==========================================================================
# THE RECOGNISER — 1-NN argmin over the LOSO forward-model exemplars under the
# monotonic DtwTo distance. A READOUT over native distances. NO context/bigram prior.
# ==========================================================================

def recognise(test_feat, fm_feats, vocab):
    """fm_feats: {word: [transformed exemplar matrices]}. Returns argmin-distance word."""
    if test_feat is None:
        return None
    best, bw = math.inf, None
    for w in vocab:
        exs = fm_feats.get(w)
        if not exs:
            continue
        for ex in exs:
            d = monotonic_dtw(test_feat, ex)
            if d < best:
                best, bw = d, w
    return bw


def eval_route(transform, word_exemplars, true_seqs, vocab, vocab_set,
               held_speakers, K, label_shuffle=False, rng=None):
    """LOSO 1-NN over the route's front-end transform. ACOUSTIC-ONLY (no prior).

    label_shuffle: if True, permute the WORD labels of the train exemplars within each
    held-out fold (speaker structure preserved, word<->trajectory binding destroyed) —
    the artifact backstop; a real acoustic gain must collapse toward chance under it."""
    corr = tot = 0
    for held in held_speakers:
        # forward model over TRAIN speakers (LOSO), then transform every exemplar.
        fm = build_forward_model(word_exemplars, vocab, held, K)
        items = [(w, M) for w in vocab for M in (fm.get(w) or [])]
        if label_shuffle and items and rng is not None:
            labs = [w for (w, _) in items]
            rng.shuffle(labs)
            items = [(labs[i], items[i][1]) for i in range(len(items))]
        fm_feats = {}
        for w, M in items:
            T = transform(M)
            if T is not None:
                fm_feats.setdefault(w, []).append(T)
        # held-out test tokens (this speaker's continuous utts), in order.
        for seq in true_seqs:
            if not seq or seq[0][1] != held:
                continue
            for (w, sp, M) in seq:
                if w not in vocab_set:
                    continue
                T = transform(M)
                if T is None:
                    continue
                pred = recognise(T, fm_feats, vocab)
                if pred is not None:
                    corr += int(pred == w)
                    tot += 1
    return corr / max(tot, 1), corr, tot


def main():
    t0 = time.time()
    random.seed(1)
    n_utts = int(sys.argv[1]) if len(sys.argv) > 1 else 600
    n_speakers = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    VOCAB = int(sys.argv[3]) if len(sys.argv) > 3 else 30
    K = int(sys.argv[4]) if len(sys.argv) > 4 else 5
    print(f"=== parakeet_acoustic_drive  n_utts={n_utts}  n_speakers={n_speakers}  "
          f"vocab={VOCAB}  K={K} ===", flush=True)
    print("VENUE: LibriSpeech dev-clean reduced-continuous function words, LOSO "
          "cross-speaker — the AT-CHANCE acoustic venue (docs/real_data_drive.md: "
          "acoustic-only 0.0313 vs chance 0.0333). The STATIC ear is at chance here; "
          "the question is whether conv-local + explicit-duration FLIP the digit-venue "
          "nulls to positive (a PREDICTION under test, not a result).", flush=True)
    print("ACOUSTIC-ONLY: NO context/bigram prior — adding the LM would CONFOUND. The "
          "lever under test is ACOUSTIC STRUCTURE, not more-LM.\n", flush=True)
    print("FIXED structural choices (imported from parakeet_teardown_probe, reported "
          "not tuned):", flush=True)
    print("  static_feats = per-utt CMVN ; conv_local = order-1 delta over time "
          "(doubles dim) ;", flush=True)
    print("  rate_normalised L=32 linear interp ; monotonic_dtw band_frac=0.25 "
          "(Sakoe-Chiba) ; recogniser = 1-NN argmin readout.\n", flush=True)

    # ---- LibriSpeech selection (verbatim from real_data_drive.main) ----
    pairs = SL.gather_pairs()
    speakers = sorted(set(p[1] for p in pairs))
    chosen = speakers[:n_speakers]
    sel = [p for p in pairs if p[1] in chosen]
    random.shuffle(sel)
    sel = sel[:n_utts]
    used = sorted(set(p[1] for p in sel))
    print(f"LibriSpeech dev-clean: {len(pairs)} utts, {len(speakers)} speakers; "
          f"using {len(sel)} utts from {len(used)} speakers", flush=True)

    # ---- harvest per-word A1 trajectories (agent's valley segmentation) ----
    print("\n--- harvesting per-word A1 trajectories (agent's valley segmentation, "
          "transcript-aligned) ---", flush=True)
    word_exemplars, true_seqs = harvest_word_trajectories(None, sel)
    print(f"harvested {len(word_exemplars)} word exemplars over {len(true_seqs)} utts",
          flush=True)

    # ---- closed vocab: top-V most frequent harvested words ----
    freq = {}
    for w, sp, M in word_exemplars:
        freq[w] = freq.get(w, 0) + 1
    vocab = [w for w, _ in sorted(freq.items(), key=lambda kv: -kv[1])[:VOCAB]]
    vocab_set = set(vocab)
    chance = 1.0 / max(len(vocab), 1)
    print(f"closed vocab (top {VOCAB}): {vocab}", flush=True)
    print(f"chance = 1/{len(vocab)} = {chance:.4f}", flush=True)
    iv = sum(1 for seq in true_seqs for (w, sp, M) in seq if w in vocab_set)
    print(f"in-vocab word tokens (test surface): {iv}\n", flush=True)

    held_speakers = used

    # ======================================================================
    # THE THREE ROUTES — acoustic-only, LOSO, monotonic DtwTo, only the front-end
    # transform changes. R1 IS the do-contrast control (reproduces the at-chance base).
    # ======================================================================
    print("=== ACOUSTIC-ONLY ROUTES (LOSO, monotonic DtwTo, NO context prior) ===",
          flush=True)
    results = []
    for name, tx in ROUTES:
        acc, c, t = eval_route(tx, word_exemplars, true_seqs, vocab, vocab_set,
                               held_speakers, K)
        results.append((name, acc, c, t))
        print(f"  {name:<54s} {acc:.4f}  ({c}/{t})  [chance {chance:.4f}, "
              f"x{acc/chance:.2f}]", flush=True)

    accR1 = results[0][1]
    accR2 = results[1][1]
    accR3 = results[2][1]
    print(f"\n  -> conv-local delta (R2 - R1)            : {accR2 - accR1:+.4f}",
          flush=True)
    print(f"  -> + explicit-duration delta (R3 - R2)   : {accR3 - accR2:+.4f}",
          flush=True)
    print(f"  -> total constructed-structure (R3 - R1) : {accR3 - accR1:+.4f}\n",
          flush=True)

    # ======================================================================
    # SHUFFLE / do-contrast BACKSTOP — best route, train labels shuffled. A real
    # acoustic gain must collapse toward chance; survival = frequency/label artifact.
    # ======================================================================
    best_idx = int(np.argmax([r[1] for r in results]))
    best_name, best_acc = results[best_idx][0], results[best_idx][1]
    print(f"=== SHUFFLE CONTROL — best route ({best_name}) with train labels "
          f"shuffled (word<->trajectory binding destroyed) ===", flush=True)
    rng = random.Random(7)
    accSh, cSh, tSh = eval_route(ROUTES[best_idx][1], word_exemplars, true_seqs,
                                 vocab, vocab_set, held_speakers, K,
                                 label_shuffle=True, rng=rng)
    print(f"  {('shuffled-label ' + best_name):<54s} {accSh:.4f}  ({cSh}/{tSh})  "
          f"[chance {chance:.4f}]", flush=True)
    print(f"  -> best real {best_acc:.4f} -> shuffled {accSh:.4f}  "
          f"(collapse toward chance {chance:.4f} expected if the structure is real)\n",
          flush=True)

    # ======================================================================
    # VERDICT — read the NUMBERS. The prediction is: R2/R3 FLIP the digit-venue nulls
    # to positive on this at-chance venue. It may FAIL (stay at chance) — report plainly.
    # ======================================================================
    print("========================= VERDICT =========================", flush=True)
    print(f"  R1 STATIC only            : {accR1:.4f}  (chance {chance:.4f}, "
          f"x{accR1/chance:.2f})  [reproduces the at-chance acoustic base]", flush=True)
    print(f"  R2 +conv-local delta      : {accR2:.4f}  (R2-R1 {accR2-accR1:+.4f})",
          flush=True)
    print(f"  R3 +explicit duration     : {accR3:.4f}  (R3-R2 {accR3-accR2:+.4f}, "
          f"R3-R1 {accR3-accR1:+.4f})", flush=True)
    print(f"  shuffle control (best)    : {accSh:.4f}  (best {best_acc:.4f} -> "
          f"{accSh:.4f})", flush=True)

    # honest two-sided read (a +0.005 non-noise floor, same as the venue's gate)
    FLOOR = 0.005
    delta_conv = accR2 - accR1
    delta_dur = accR3 - accR2
    delta_tot = accR3 - accR1
    conv_flips = delta_conv > FLOOR
    dur_flips = delta_dur > FLOOR
    structure_real = (best_acc - accSh) > FLOOR    # gain collapses under shuffle
    print(f"\n  conv-local FLIPS null->positive (> +{FLOOR}) : "
          f"{'YES' if conv_flips else 'NO'} ({delta_conv:+.4f})", flush=True)
    print(f"  explicit-duration FLIPS null->positive       : "
          f"{'YES' if dur_flips else 'NO'} ({delta_dur:+.4f})", flush=True)
    print(f"  any gain collapses under label-shuffle       : "
          f"{'YES' if structure_real else 'NO'} "
          f"(best {best_acc:.4f} -> shuf {accSh:.4f})", flush=True)

    if (conv_flips or dur_flips) and structure_real:
        print(f"\n  PREDICTION GROUNDED: the digit-venue NULL(s) FLIP to positive on "
              f"the at-chance reduced-continuous venue — constructed acoustic structure "
              f"(conv-local {delta_conv:+.4f}, duration {delta_dur:+.4f}, total "
              f"{delta_tot:+.4f}) lifts the ACOUSTIC channel itself, NO LM, and the gain "
              f"collapses under label-shuffle. Parakeet's lever is real acoustic "
              f"structure on the at-chance frontier.", flush=True)
        verdict = "PREDICTION_GROUNDED"
    elif (conv_flips or dur_flips) and not structure_real:
        print(f"\n  REOPEN: a gain appeared (conv {delta_conv:+.4f}, dur "
              f"{delta_dur:+.4f}) but it did NOT collapse under label-shuffle "
              f"({best_acc:.4f} -> {accSh:.4f}) — a frequency/label artifact, not "
              f"acoustic structure. The backstop CAUGHT it.", flush=True)
        verdict = "REOPEN_ARTIFACT"
    else:
        print(f"\n  PREDICTION FAILS (honest null): the digit-venue nulls do NOT flip on "
              f"the at-chance reduced-continuous venue. conv-local {delta_conv:+.4f}, "
              f"explicit-duration {delta_dur:+.4f}, total {delta_tot:+.4f} — the "
              f"constructed transition-derivative + duration do NOT lift the acoustic "
              f"channel above the at-chance static base here. The hypothesis "
              f"(docs/parakeet_teardown.md §6) is NOT borne out. A failed prediction is a "
              f"genuine result.", flush=True)
        verdict = "PREDICTION_FAILS_NULL"

    print(f"\nVERDICT_TOKEN={verdict}  R1={accR1:.4f}  R2={accR2:.4f}  R3={accR3:.4f}  "
          f"conv={delta_conv:+.4f}  dur={delta_dur:+.4f}  total={delta_tot:+.4f}  "
          f"shuffle={accSh:.4f}  chance={chance:.4f}  in_vocab_tokens={iv}", flush=True)
    print(f"elapsed {time.time()-t0:.1f}s", flush=True)
    print("===MARKER_ACOUSTIC_DRIVE_COMPLETE===", flush=True)


if __name__ == "__main__":
    main()

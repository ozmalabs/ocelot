"""order_n_frequency_frame — aim the agent's OWN order-N operator down the
FREQUENCY axis (spectral curvature whose negative extrema = formants) and add it
as a SOFT-ADMISSIBILITY excluder to the multi-frame weighted-admissibility
collapse, tested CROSS-SPEAKER.

This complements the running syllable build (order-N over TIME-energy). Together:
"every frame is order-N over a dimension" — ONE operator, two axes
(ozma_every_frame_is_order_n_over_a_dimension).

THE TEST (real cross-speaker word recognition, held-out speakers never banked):
  · ACOUSTIC frame   — v1 frame-relative LPC-formant 1-NN read of a held-out
    speaker's real SC clip -> soft excluder over the 35-word vocab.
  · ORDER-N-FREQ frame — the agent's order-N operator (order_n_concepts) DOWN THE
    BAND AXIS of the cochleagram (order-2 = spectral curvature = formant peaks) ->
    1-NN DTW vs per-word held-out-disjoint TRAIN exemplars -> soft excluder.
  · CONTEXT / FUTURE frames — the REAL LibriSpeech word n-gram (the world's
    statistics), per under_determined_real -> soft excluders.

THREE CONDITIONS compared on the SAME cross-speaker test items:
  (a) ACOUSTIC-ONLY single frame (argmax of the acoustic excluder).
  (b) MULTI-FRAME WITHOUT order-N-freq (acoustic + n-gram, weighted_admissibility).
  (c) MULTI-FRAME WITH order-N-freq (acoustic + order-N-freq + n-gram).

REPORT the lift from adding the order-N-freq (formant) frame, and HONEST about
whether it adds INDEPENDENT constraint over the raw acoustic (both are spectral)
or is redundant / too noisy cross-speaker (the gammatone-wall formant caveat).
KILL: if (c) does NOT beat (b)/(a) -> redundant or unreliable cross-speaker; say so.

DONKEY: order-N operator = the agent's own (domains/order_n_concepts via
domains/order_n_frequency_frame, native eval); acoustic = v1; collapse =
v2 weighted_admissibility; LM = real counts; held-out SPEAKERS never banked.

Run: python -m scripts.order_n_frequency_frame [n_train_spk] [n_held_spk] \
        [n_per] [n_ctx] [max_items]
"""
from __future__ import annotations

import os
import sys
import random
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import domains.self_directed_speech_world as W
import domains.frame_inference_v2 as F2
import domains.under_determined_real as U
from domains.order_n_frequency_frame import order_n_freq_repr, donkey_audit
from scripts.frame_inference_v1 import infer_talker_frame, read_relative
from scripts.under_determined_real import _dtw_fast, build_split

FS = W._TARGET_FS

ORDER = 2  # order-2 over frequency = spectral curvature (formant peaks)


# ===========================================================================
# THE ORDER-N-FREQ BANK — per held-out-disjoint TRAIN speaker, the order-N-over-
# frequency representation of each word's clips (the agent's operator, native eval).
# A speaker-independent exemplar bank (NO per-speaker frame needed: the order-2-freq
# curvature is a within-frame spectral shape, and the log-cochleagram differencing
# already cancels a per-band multiplicative gain). Optionally capped per word.
# ===========================================================================

def build_onf_bank(train, vocab, order=ORDER, cap_per_word=20, seed=13):
    bank = {w: [] for w in vocab}
    for spk, (_ctx, word_clips) in train.items():
        for w, clips in word_clips.items():
            for x in clips:
                r = order_n_freq_repr(x, FS, order=order)
                if r.shape[0]:
                    bank[w].append(r)
    if cap_per_word is not None:
        rng = random.Random(seed)
        for w in vocab:
            if len(bank[w]) > cap_per_word:
                rng.shuffle(bank[w])
                bank[w] = bank[w][:cap_per_word]
    return bank


def onf_excluder(x, bank, vocab, order=ORDER):
    """The agent's order-N-freq read of clip x -> per-word 1-NN DTW distance -> soft
    excluder over the vocab. Owned operator (order_n_concepts) + v2 distance->exclude."""
    r = order_n_freq_repr(x, FS, order=order)
    K = len(vocab)
    dist = np.full(K, np.inf, dtype=np.float64)
    if r.shape[0] == 0:
        return F2.soft_exclude_from_distance(dist)
    for k, w in enumerate(vocab):
        best = np.inf
        for e in bank[w]:
            dd = _dtw_fast(r, e)
            if dd < best:
                best = dd
        dist[k] = best
    return F2.soft_exclude_from_distance(dist)


# ===========================================================================
# ACOUSTIC BANK + excluder (v1 frame-relative LPC formants), per under_determined_real.
# ===========================================================================

def build_rel_bank(train, vocab, est="pctl", mode="frac", cap_per_word=20, seed=11):
    bank = {w: [] for w in vocab}
    for spk, (ctx, word_clips) in train.items():
        fr = infer_talker_frame(ctx, estimator=est)
        for w, clips in word_clips.items():
            for x in clips:
                r = read_relative(x, fr, mode=mode)
                if r.shape[0]:
                    bank[w].append(r)
    if cap_per_word is not None:
        rng = random.Random(seed)
        for w in vocab:
            if len(bank[w]) > cap_per_word:
                rng.shuffle(bank[w])
                bank[w] = bank[w][:cap_per_word]
    return bank


def acoustic_excluder(x, frame, bank, vocab, mode="frac"):
    r = read_relative(x, frame, mode=mode)
    K = len(vocab)
    dist = np.full(K, np.inf, dtype=np.float64)
    if r.shape[0] == 0:
        return F2.soft_exclude_from_distance(dist)
    for k, w in enumerate(vocab):
        best = np.inf
        for e in bank[w]:
            dd = _dtw_fast(r, e)
            if dd < best:
                best = dd
        dist[k] = best
    return F2.soft_exclude_from_distance(dist)


# ===========================================================================
# BUILD THE CROSS-SPEAKER TEST SET ONCE — per slot a held speaker's real clip of a
# real target word; compute BOTH the acoustic AND the order-N-freq excluder here
# (the expensive reads, done ONCE), pair with the real sentence item + truth index.
# ===========================================================================

def build_test_set(train, held, vocab, items, rel_bank, onf_bank,
                   max_items=1500, seed=7, est="pctl", mode="frac", verbose=True):
    rng = random.Random(seed)
    by_word = {}
    for it in items:
        by_word.setdefault(it["target"], []).append(it)
    held_speakers = list(held.items())
    rng.shuffle(held_speakers)
    spk_frames = {}
    test = []
    t0 = time.time()
    used = 0
    while used < max_items:
        progressed = False
        for spk, (ctx, word_clips) in held_speakers:
            if used >= max_items:
                break
            fr = spk_frames.get(spk)
            if fr is None:
                fr = infer_talker_frame(ctx, estimator=est)
                spk_frames[spk] = fr
            realizable = [w for w in word_clips if by_word.get(w)]
            if not realizable:
                continue
            w = rng.choice(realizable)
            it = rng.choice(by_word[w])
            x = rng.choice(word_clips[w])
            acou_e = acoustic_excluder(x, fr, rel_bank, vocab, mode=mode)
            onf_e = onf_excluder(x, onf_bank, vocab)
            test.append((acou_e, onf_e, it, vocab.index(w)))
            used += 1
            progressed = True
            if verbose and used % 200 == 0:
                print(f"    ... {used} test reads (acoustic+order-N-freq) "
                      f"({time.time()-t0:.0f}s)", flush=True)
        if not progressed:
            break
    return test


# ===========================================================================
# THE THREE CONDITIONS on one test item. All share the SAME real n-gram excluders.
# ===========================================================================

def decode_item(acou_e, onf_e, item, fwd, bwd, bwd2, vocab,
                lm_weight=1.0, onf_weight=1.0, sheaf_depth=2):
    # real n-gram frames (context + future sheaf)
    ctx_e = U.context_excluder(item["prev"], fwd, vocab)
    lm = [ctx_e]
    lmw = [lm_weight]
    if sheaf_depth >= 1:
        lm.append(U.future_excluder(item["next"], bwd, vocab)); lmw.append(lm_weight)
    if sheaf_depth >= 2:
        lm.append(U.future2_excluder(item["next2"], bwd2, vocab)); lmw.append(lm_weight)

    # (a) ACOUSTIC-ONLY single frame
    g_a = int(np.argmax(acou_e))
    # (b) MULTI-FRAME WITHOUT order-N-freq (acoustic + n-gram)
    excl_b = [acou_e] + lm
    w_b = [1.0] + lmw
    g_b = int(np.argmax(F2.weighted_admissibility(excl_b, w_b)))
    # (c) MULTI-FRAME WITH order-N-freq (acoustic + order-N-freq + n-gram)
    excl_c = [acou_e, onf_e] + lm
    w_c = [1.0, onf_weight] + lmw
    g_c = int(np.argmax(F2.weighted_admissibility(excl_c, w_c)))
    # also: order-N-freq ALONE single-frame (independence probe)
    g_onf = int(np.argmax(onf_e))
    return g_a, g_b, g_c, g_onf


def run(test, vocab, fwd, bwd, bwd2, lm_weight=1.0, onf_weight=1.0, sheaf_depth=2):
    agg = {"a": [0, 0], "b": [0, 0], "c": [0, 0], "onf": [0, 0]}
    for acou_e, onf_e, it, truth in test:
        ga, gb, gc, gonf = decode_item(acou_e, onf_e, it, fwd, bwd, bwd2, vocab,
                                       lm_weight=lm_weight, onf_weight=onf_weight,
                                       sheaf_depth=sheaf_depth)
        agg["a"][0] += int(ga == truth); agg["a"][1] += 1
        agg["b"][0] += int(gb == truth); agg["b"][1] += 1
        agg["c"][0] += int(gc == truth); agg["c"][1] += 1
        agg["onf"][0] += int(gonf == truth); agg["onf"][1] += 1
    return {k: (agg[k][0] / max(agg[k][1], 1), agg[k][1]) for k in agg}


def _independence(test, vocab):
    """Are the acoustic and order-N-freq frames INDEPENDENT or REDUNDANT? Measure
    the agreement of their single-frame argmax predictions and the correlation of
    their soft-excluder vectors. High agreement / correlation = redundant."""
    agree = 0
    both_right = 0
    a_right_onf_wrong = 0
    onf_right_a_wrong = 0
    corrs = []
    for acou_e, onf_e, it, truth in test:
        ga = int(np.argmax(acou_e)); go = int(np.argmax(onf_e))
        agree += int(ga == go)
        ar = int(ga == truth); orr = int(go == truth)
        both_right += int(ar and orr)
        a_right_onf_wrong += int(ar and not orr)
        onf_right_a_wrong += int(orr and not ar)
        if np.std(acou_e) > 1e-9 and np.std(onf_e) > 1e-9:
            corrs.append(float(np.corrcoef(acou_e, onf_e)[0, 1]))
    n = len(test)
    return {
        "argmax_agreement": agree / max(n, 1),
        "mean_excluder_corr": float(np.mean(corrs)) if corrs else float("nan"),
        "both_right": both_right / max(n, 1),
        "acoustic_right_onf_wrong": a_right_onf_wrong / max(n, 1),
        "onf_right_acoustic_wrong": onf_right_a_wrong / max(n, 1),
    }


def main():
    if not W.sc_available():
        print("Speech Commands not found at /tmp/sc — abort.", flush=True)
        return
    if not os.path.isdir("/tmp/LibriSpeech"):
        print("LibriSpeech not found at /tmp/LibriSpeech — abort.", flush=True)
        return
    n_train_spk = int(sys.argv[1]) if len(sys.argv) > 1 else 80
    n_held_spk = int(sys.argv[2]) if len(sys.argv) > 2 else 30
    n_per = int(sys.argv[3]) if len(sys.argv) > 3 else 14
    n_ctx = int(sys.argv[4]) if len(sys.argv) > 4 else 8
    max_items = int(sys.argv[5]) if len(sys.argv) > 5 else 1500

    vocab = U.sc_vocab()
    K = len(vocab)
    chance = 1.0 / K

    print("=" * 80, flush=True)
    print("ORDER-N-OVER-FREQUENCY FRAME — formants via the agent's OWN order-N "
          "operator, cross-speaker", flush=True)
    print("=" * 80, flush=True)

    # --- DONKEY AUDIT: the order-N differencing IS the agent's operator, native eval.
    da = donkey_audit()
    print("[donkey audit] order-N operator =", da["operator"], flush=True)
    print("[donkey audit] evaluated_by =", da["evaluated_by"], flush=True)
    print(f"[donkey audit] native order-2-freq curvature == numpy recurrence: "
          f"{da['match']}; negative-curvature locates the peak band "
          f"{da['peak_band_from_neg_curvature']} == true peak {da['true_peak_band']}",
          flush=True)

    # --- the REAL language model (real LibriSpeech word n-gram).
    print("[LM] counting REAL word n-gram from LibriSpeech transcripts ...", flush=True)
    fwd, bwd, fwd2, bwd2, n_utts = U.count_ngram()
    items = U.target_instances(vocab)
    print(f"[LM] {n_utts} real utterances; {len(items)} REAL test items", flush=True)

    # --- SPLIT (held-out speakers never banked).
    train, held = build_split(vocab, n_train_spk, n_held_spk, n_per, n_ctx)

    # --- BANKS (both from held-out-disjoint TRAIN speakers).
    print("[bank] acoustic (v1 frame-relative LPC formants) ...", flush=True)
    t0 = time.time()
    rel_bank = build_rel_bank(train, vocab)
    print(f"[bank] {sum(len(v) for v in rel_bank.values())} acoustic exemplars "
          f"({time.time()-t0:.0f}s)", flush=True)
    print("[bank] order-N-freq (agent's order-N operator down the band axis) ...",
          flush=True)
    t0 = time.time()
    onf_bank = build_onf_bank(train, vocab)
    print(f"[bank] {sum(len(v) for v in onf_bank.values())} order-N-freq exemplars "
          f"({time.time()-t0:.0f}s)", flush=True)

    # --- CROSS-SPEAKER TEST SET ONCE (acoustic + order-N-freq reads per item).
    print("[test] building cross-speaker test set (acoustic + order-N-freq reads) ...",
          flush=True)
    t0 = time.time()
    test = build_test_set(train, held, vocab, items, rel_bank, onf_bank,
                          max_items=max_items)
    print(f"[test] {len(test)} cross-speaker test items ({time.time()-t0:.0f}s)",
          flush=True)

    # --- INDEPENDENCE PROBE (acoustic vs order-N-freq: redundant or complementary?).
    ind = _independence(test, vocab)
    print("\n" + "-" * 80, flush=True)
    print("INDEPENDENCE — acoustic frame vs order-N-freq frame (both spectral):",
          flush=True)
    print(f"  single-frame argmax AGREEMENT      : {ind['argmax_agreement']:.3f} "
          "(1.0 = fully redundant)", flush=True)
    print(f"  mean soft-excluder CORRELATION     : {ind['mean_excluder_corr']:.3f}",
          flush=True)
    print(f"  both right                         : {ind['both_right']:.3f}", flush=True)
    print(f"  acoustic right, order-N-freq wrong : {ind['acoustic_right_onf_wrong']:.3f}",
          flush=True)
    print(f"  order-N-freq right, acoustic wrong : {ind['onf_right_acoustic_wrong']:.3f} "
          "(>0 = order-N-freq adds INDEPENDENT correct cases)", flush=True)

    # === MAIN: (a) acoustic-only vs (b) multi-frame-without vs (c) with order-N-freq.
    # Sweep the order-N-freq frame weight (REPORT the surface; verdict reads the
    # principled cell onf_weight=1.0, lm_weight=1.0, full sheaf).
    print("\n" + "=" * 80, flush=True)
    print("ACOUSTIC-ONLY vs MULTI-FRAME(without) vs MULTI-FRAME(with order-N-freq)",
          flush=True)
    print(f"  chance {chance:.3f}  vocab {K}  n={len(test)} cross-speaker items",
          flush=True)
    print(f"  order-N-freq ALONE single-frame (independence ref):", flush=True)
    r0 = run(test, vocab, fwd, bwd, bwd2, onf_weight=1.0)
    print(f"    order-N-freq-alone acc = {r0['onf'][0]:.3f}  (acoustic-alone "
          f"{r0['a'][0]:.3f}, chance {chance:.3f})", flush=True)
    print(f"\n  {'onf_w':>6s} {'(a)acou':>9s} {'(b)multi-':>10s} {'(c)multi+':>10s} "
          f"{'c-a':>7s} {'c-b':>7s} {'n':>6s}", flush=True)
    print(f"  {'':6s} {'only':>9s} {'no-onf':>10s} {'with-onf':>10s}", flush=True)
    results = {}
    for onf_w in [0.5, 1.0, 2.0]:
        r = run(test, vocab, fwd, bwd, bwd2, lm_weight=1.0, onf_weight=onf_w,
                sheaf_depth=2)
        results[onf_w] = r
        a = r["a"][0]; b = r["b"][0]; c = r["c"][0]
        print(f"  {onf_w:6.1f} {a:9.3f} {b:10.3f} {c:10.3f} {c-a:+7.3f} {c-b:+7.3f} "
              f"{r['c'][1]:6d}", flush=True)

    # === VERDICT (principled cell: onf_weight=1.0) ===
    print("\n" + "=" * 80, flush=True)
    print("VERDICT — does the order-N-freq (formant) frame add over the acoustic?",
          flush=True)
    print("=" * 80, flush=True)
    BAR = 0.01
    r = results[1.0]
    a = r["a"][0]; b = r["b"][0]; c = r["c"][0]
    onf_alone = r0["onf"][0]
    lift_over_acoustic = c - a
    lift_over_multi = c - b
    print(f"  principled cell onf_weight=1.0 lm_weight=1.0 sheaf=2 (n={r['c'][1]}):",
          flush=True)
    print(f"    (a) acoustic-only        = {a:.3f}", flush=True)
    print(f"    (b) multi-frame no-onf   = {b:.3f}", flush=True)
    print(f"    (c) multi-frame with-onf = {c:.3f}", flush=True)
    print(f"    order-N-freq frame ALONE = {onf_alone:.3f} (chance {chance:.3f})",
          flush=True)
    print(f"    lift of adding order-N-freq over the n-gram multi-frame (c - b) = "
          f"{lift_over_multi:+.3f}", flush=True)
    print(f"    total over acoustic-only (c - a) = {lift_over_acoustic:+.3f}", flush=True)
    print("-" * 80, flush=True)
    onf_above_chance = onf_alone > chance + 0.02
    independent = ind["onf_right_acoustic_wrong"] > 0.02
    if lift_over_multi > BAR and onf_above_chance and independent:
        print(f"  ADDS INDEPENDENT CONSTRAINT: the order-N-freq (formant-curvature) "
              f"frame, built from the agent's OWN order-N operator down the frequency "
              f"axis, lifts the multi-frame collapse by {lift_over_multi:+.3f} over the "
              f"acoustic+n-gram. It reads above chance alone ({onf_alone:.3f}) and is "
              f"correct on {ind['onf_right_acoustic_wrong']:.3f} cases the acoustic "
              f"misses -> a COMPLEMENTARY spectral constraint, not redundant.",
              flush=True)
    else:
        reasons = []
        if lift_over_multi <= BAR:
            reasons.append(f"no lift over the n-gram multi-frame ({lift_over_multi:+.3f})")
        if not onf_above_chance:
            reasons.append(f"order-N-freq alone barely beats chance "
                           f"({onf_alone:.3f} vs {chance:.3f})")
        if not independent:
            reasons.append(f"adds few cases the acoustic misses "
                           f"({ind['onf_right_acoustic_wrong']:.3f})")
        print(f"  KILL / REDUNDANT: the order-N-freq frame does NOT add independent "
              f"constraint over the acoustic spectral frame cross-speaker — "
              + "; ".join(reasons) + ".", flush=True)
        print(f"    HONEST: both frames read the same spectral content; the "
              f"order-2-freq curvature peak is a QUANTISED (gammatone-wall) formant "
              f"estimate, so it largely re-describes what the LPC-formant acoustic "
              f"frame already carries cross-speaker.", flush=True)
    print(f"  CHAIN: acoustic {a:.3f} | +order-N-freq {c:.3f} | order-N-freq-alone "
          f"{onf_alone:.3f} | chance {chance:.3f}", flush=True)
    print("\n[MARKER] ORDER_N_FREQUENCY_FRAME_COMPLETED", flush=True)


if __name__ == "__main__":
    main()

"""under_determined_real — the PROPER under-determined regime, on REAL data.

THE TEST. Recognition of a real word in a real sentence, cross-speaker:
  · ACOUSTIC frame  — the agent's v1 frame-relative 1-NN read of a HELD-OUT
    speaker's real Speech-Commands clip of the word -> a per-candidate soft
    excluder over the 35-word vocab. Naturally UNDER-determines (~0.18 alone,
    chance 0.029): speaker variation is the real ambiguity.
  · CONTEXT frame   — the REAL bigram P(target | real predecessor) counted from
    real LibriSpeech transcripts (NOT imposed) -> soft excluder.
  · FUTURE SHEAF    — the REAL bigram P(target | real successor) (1-step) and the
    real skip-2 P(target | real word two-ahead) (2-step) -> soft excluders. The
    real sentence's future, several frames of it.
  (optional CONTEXT-2 — real skip-2 backward, symmetric to the 2-step future.)

THREE REGIMES (per-position accuracy on the SAME real test items, cross-speaker):
  (i)   SINGLE-FRAME     — acoustic soft-excluder argmax (no LM).
  (ii)  DOT-PRODUCT      — all frames as POSITIVE scores, SCALAR weighted SUM,
                           argmax (the premature scalar-collapse control).
  (iii) WEIGHTED-ADMIS.  — all frames as soft excluders, vector-weighted
                           INTERSECTION (sum of weighted log-admissibilities),
                           kept soft, argmax. THE CLAIM.

PREDICTION (the real under-determined regime): (iii) > (i)  [the real LM over-
determines what the cross-speaker acoustic can't] AND (iii) > (ii) [soft
intersection beats the premature scalar sum where a wrong-but-confident acoustic
must be VETOED by the LM, not out-summed].
KILL: (iii) !> (i) -> the real LM doesn't help cross-speaker (surprising, say so).
      (iii) !> (ii) -> soft-vs-scalar is moot on real data (say so).

SWEEPS: LM weight (how hard the real n-gram carves) x sheaf depth (1 vs 1+2-step
future) x the acoustic weight. No sweep-and-keep-best: the sweep REPORTS the
surface; the verdict reads the principled cell (LM weight 1.0, full sheaf) plus
the surface.

DONKEY: acoustic = v1 frame-relative recogniser (the agent's). LM = real counts
(domains.under_determined_real, the world). collapse ops = v2 owned
(weighted_admissibility / dot_product_combine). Held-out SPEAKERS never banked.
The LM is counted from the transcript corpus; it never sees audio (no leakage).

Run: python -m scripts.under_determined_real [n_train_spk] [n_held_spk] \
        [n_clip_per_word] [n_ctx] [max_items]
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
from scripts.frame_inference_v1 import (
    infer_talker_frame, read_relative, _dtw,
)

FS = W._TARGET_FS


# ---------------------------------------------------------------------------
# FAST DTW — numerically IDENTICAL to frame_inference_v1._dtw (same recurrence,
# same Euclidean per-frame cost, same /(na+nb) normalisation), but the inner j
# loop is vectorised with a running-minimum sweep instead of a Python cell loop.
# Pure speedup, no change to the distance (asserted equal to _dtw at import on a
# random probe). Lets the 1566-exemplar bank scan finish in minutes, not an hour.
# ---------------------------------------------------------------------------

def _dtw_fast(a, b):
    a = np.asarray(a, dtype=np.float64)
    b = np.asarray(b, dtype=np.float64)
    if a.size == 0 or b.size == 0:
        return float("inf")
    na, nb = a.shape[0], b.shape[0]
    # local cost matrix C[i,j] = ||a_i - b_j|| (vectorised)
    C = np.sqrt(((a[:, None, :] - b[None, :, :]) ** 2).sum(-1))
    prev = np.full(nb + 1, np.inf)
    prev[0] = 0.0
    INF = np.inf
    for i in range(1, na + 1):
        cur = np.empty(nb + 1)
        cur[0] = INF
        ci = C[i - 1]
        run = cur[0]
        pj = prev          # D[i-1, :]
        for j in range(1, nb + 1):
            run = ci[j - 1] + min(pj[j], cur[j - 1], pj[j - 1])
            cur[j] = run
        prev = cur
    return float(prev[nb] / (na + nb))


# sanity: identical to v1's _dtw on a random probe (numerics unchanged).
_pa = np.random.default_rng(0).random((7, 3))
_pb = np.random.default_rng(1).random((9, 3))
assert abs(_dtw_fast(_pa, _pb) - _dtw(_pa, _pb)) < 1e-9, "fast DTW must match v1 _dtw"


# ===========================================================================
# SPLIT — train speakers (build the frame-relative acoustic bank) and HELD-OUT
# speakers (realise the test words acoustically; never banked). Per speaker:
# UNLABELED context clips for the talker-frame estimate (disjoint from bank/test).
# The constrained vocab is the SC words. Real cross-speaker LOSO, ungameable.
# ===========================================================================

def build_split(vocab, n_train_spk, n_held_spk, n_per, n_ctx, seed=20240611):
    rng = random.Random(seed)
    speakers = W.sc_speakers(vocab)
    rng.shuffle(speakers)
    held_spk = speakers[:n_held_spk]
    train_spk = speakers[n_held_spk:n_held_spk + n_train_spk]
    print(f"[split] vocab={len(vocab)} words; {len(train_spk)} TRAIN, "
          f"{len(held_spk)} HELD-OUT speakers (disjoint; held clips NEVER banked)",
          flush=True)

    def carve(spk_list, n_body):
        out = {}
        for spk in spk_list:
            spk_idx = W.sc_index_for([spk], vocab)
            wp = [(w, p) for w in vocab for p in spk_idx.get(w, [])]
            rng.shuffle(wp)
            if len(wp) < n_ctx + 2:
                continue
            ctx = wp[:n_ctx]
            body = wp[n_ctx:n_ctx + n_body]
            ctx_clips = [W.load_sc_clip(p)[0] for _w, p in ctx]
            # per-word pool of loaded clips for this speaker (the words they realise)
            word_clips = {}
            for w, p in body:
                word_clips.setdefault(w, []).append(W.load_sc_clip(p)[0])
            out[spk] = (ctx_clips, word_clips)
        return out

    train = carve(train_spk, n_per)
    held = carve(held_spk, max(n_per, 40))
    print(f"[split] {len(train)} train / {len(held)} held usable speakers; "
          f"{n_ctx} UNLABELED ctx clips/speaker (disjoint)", flush=True)
    return train, held


def build_rel_bank(train, vocab, estimator="pctl", mode="frac", cap_per_word=24,
                   seed=11):
    """Per train speaker: infer their talker frame from their ctx clips, store each
    word's exemplars frame-relative (same space as a relative-read test). The bank
    is OPTIONALLY capped at cap_per_word exemplars/word (a deterministic random
    subsample drawn from a MIX of speakers — the 1-NN over a representative subset,
    same recogniser, bounded scan cost). cap_per_word=None keeps all exemplars."""
    bank = {w: [] for w in vocab}
    for spk, (ctx, word_clips) in train.items():
        fr = infer_talker_frame(ctx, estimator=estimator)
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
    """v1 frame-relative read of clip x -> per-word 1-NN DTW distance -> soft
    excluder over the vocab. Owned DSP + v2's distance->soft-exclude."""
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
# THE COLLAPSE on one real test item: acoustic excluder (given) + the real LM
# excluders (context / future sheaf), under each of the three regimes.
# Vector weight on the acoustic = 1.0; the LM frames carry a scalar lm_weight
# (a single knob, SWEPT and reported, not fit). Each LM excluder is built from
# the REAL neighbour word of THIS real test item.
# ===========================================================================

def collapse_item(acou_e, item, fwd, bwd, fwd2, bwd2, vocab,
                  lm_weight=1.0, sheaf_depth=1, use_ctx2=False):
    K = len(vocab)
    ctx_e = U.context_excluder(item["prev"], fwd, vocab)
    excl = [acou_e, ctx_e]
    wv = [1.0, lm_weight]
    scores = [F2.score_from_soft_exclude(acou_e),
              F2.score_from_soft_exclude(ctx_e)]
    sw = [1.0, lm_weight]
    if sheaf_depth >= 1:
        fe = U.future_excluder(item["next"], bwd, vocab)
        excl.append(fe); wv.append(lm_weight)
        scores.append(F2.score_from_soft_exclude(fe)); sw.append(lm_weight)
    if sheaf_depth >= 2:
        fe2 = U.future2_excluder(item["next2"], bwd2, vocab)
        excl.append(fe2); wv.append(lm_weight)
        scores.append(F2.score_from_soft_exclude(fe2)); sw.append(lm_weight)
    if use_ctx2:
        ce2 = U.context2_excluder(item["prev2"], fwd2, vocab)
        excl.append(ce2); wv.append(lm_weight)
        scores.append(F2.score_from_soft_exclude(ce2)); sw.append(lm_weight)

    g_single = int(np.argmax(acou_e))
    g_wadm = int(np.argmax(F2.weighted_admissibility(excl, wv)))
    g_dot = int(np.argmax(F2.dot_product_combine(scores, sw)))
    return g_single, g_dot, g_wadm


# ===========================================================================
# HARNESS — for each held speaker, for each real test item whose target word the
# speaker can realise, draw one of that speaker's clips of the word, build the
# acoustic excluder once, then decode under each regime. Items are REAL (target +
# real neighbours from real transcripts); the acoustic is cross-speaker held-out.
# ===========================================================================

def build_test_set(train, held, vocab, items, max_items=4000, rel_bank=None,
                   seed=7, est="pctl", mode="frac", verbose=False):
    """Build the cross-speaker test set ONCE: for each test slot, a held speaker's
    real clip of a real target word (acoustic excluder computed here = the expensive
    DTW, done ONCE), paired with that word's real sentence item (the real neighbours)
    and the truth index. The SAME test set is then decoded under every LM cell — so
    the heavy acoustic read is never repeated across the sweep. Returns a list of
    (acou_e, item, truth)."""
    if rel_bank is None:
        rel_bank = build_rel_bank(train, vocab, est, mode)
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
            test.append((acou_e, it, vocab.index(w)))
            used += 1
            progressed = True
            if verbose and used % 500 == 0:
                print(f"    ... {used} acoustic reads ({time.time()-t0:.0f}s)",
                      flush=True)
        if not progressed:
            break
    return test


def run(test, vocab, fwd, bwd, fwd2, bwd2,
        lm_weight=1.0, sheaf_depth=1, use_ctx2=False):
    """Decode the prebuilt test set under one LM cell (cheap: the acoustic excluder
    is cached per item; only the LM combine varies)."""
    agg = {"single": [0, 0], "dot": [0, 0], "wadm": [0, 0]}
    for acou_e, it, truth in test:
        gs, gd, gw = collapse_item(acou_e, it, fwd, bwd, fwd2, bwd2, vocab,
                                   lm_weight=lm_weight, sheaf_depth=sheaf_depth,
                                   use_ctx2=use_ctx2)
        agg["single"][0] += int(gs == truth); agg["single"][1] += 1
        agg["dot"][0] += int(gd == truth); agg["dot"][1] += 1
        agg["wadm"][0] += int(gw == truth); agg["wadm"][1] += 1
    return {k: (agg[k][0] / max(agg[k][1], 1), agg[k][1]) for k in agg}


def main():
    if not W.sc_available():
        print("Speech Commands not found at /tmp/sc — abort.", flush=True)
        return
    if not os.path.isdir("/tmp/LibriSpeech"):
        print("LibriSpeech not found at /tmp/LibriSpeech — abort.", flush=True)
        return
    n_train_spk = int(sys.argv[1]) if len(sys.argv) > 1 else 120
    n_held_spk = int(sys.argv[2]) if len(sys.argv) > 2 else 40
    n_per = int(sys.argv[3]) if len(sys.argv) > 3 else 16
    n_ctx = int(sys.argv[4]) if len(sys.argv) > 4 else 8
    max_items = int(sys.argv[5]) if len(sys.argv) > 5 else 3000

    vocab = U.sc_vocab()
    K = len(vocab)
    chance = 1.0 / K

    print("=" * 80, flush=True)
    print("UNDER-DETERMINED REGIME (REAL): cross-speaker word recognition, real LM",
          flush=True)
    print("=" * 80, flush=True)

    # --- the REAL language model: count the n-gram from REAL LibriSpeech transcripts.
    print("[LM] counting REAL word n-gram from LibriSpeech dev-clean transcripts ...",
          flush=True)
    fwd, bwd, fwd2, bwd2, n_utts = U.count_ngram()
    items = U.target_instances(vocab)
    print(f"[LM] {n_utts} real utterances; {len(items)} REAL test items "
          f"(real SC-vocab word in a real sentence, with real neighbours)", flush=True)

    # --- DONKEY AUDIT: the LM is REAL (counted), the context genuinely constrains.
    import collections as _c
    uni = _c.Counter(it["target"] for it in items)
    print("[donkey audit] REAL unigram of the SC-vocab targets in the corpus "
          "(NOT imposed; the corpus's own skew):", flush=True)
    print("   " + "  ".join(f"{w}:{uni[w]}" for w, _ in uni.most_common(8))
          + " ...", flush=True)
    # show context-alone ranking power (real P(target|real prev), no acoustic)
    ranks = []
    for it in items:
        ce = U.context_excluder(it["prev"], fwd, vocab)
        order = list(np.argsort(-ce))
        ranks.append(order.index(vocab.index(it["target"])))
    ranks = np.array(ranks)
    print(f"[donkey audit] REAL context alone (P(target|real prev)) ranks the true "
          f"word at mean {ranks.mean():.2f}/{K} (chance {(K-1)/2:.1f}); "
          f"top1={ (ranks==0).mean():.3f} -> the real LM genuinely constrains.",
          flush=True)

    # --- SPLIT + acoustic bank (built once; shared by all regimes/cells).
    train, held = build_split(vocab, n_train_spk, n_held_spk, n_per, n_ctx)
    print("[bank] building frame-relative acoustic bank (train speakers) ...",
          flush=True)
    t0 = time.time()
    rel_bank = build_rel_bank(train, vocab, "pctl", "frac")
    nbank = sum(len(v) for v in rel_bank.values())
    print(f"[bank] {nbank} frame-relative exemplars over {K} words ({time.time()-t0:.0f}s)",
          flush=True)

    # --- build the cross-speaker TEST SET ONCE (the expensive per-item acoustic
    #     read = DTW 1-NN). The same set is decoded under every LM cell below.
    print("[test] building cross-speaker test set (per-item acoustic reads) ...",
          flush=True)
    t0 = time.time()
    test = build_test_set(train, held, vocab, items, max_items=max_items,
                          rel_bank=rel_bank, verbose=True)
    print(f"[test] {len(test)} cross-speaker test items ({time.time()-t0:.0f}s)",
          flush=True)

    # === MAIN SWEEP: LM weight x sheaf depth (acoustic weight fixed at 1.0). ===
    print("\n" + "=" * 80, flush=True)
    print("SWEEP — single(i) vs dot-product(ii) vs weighted-admissibility(iii)",
          flush=True)
    print(f"  chance {chance:.3f}  vocab {K}  held {len(held)} speakers  "
          f"max_items {max_items}", flush=True)
    print(f"  {'lm_w':>5s} {'sheaf':>6s} {'single(i)':>11s} {'dotprod(ii)':>12s} "
          f"{'wadm(iii)':>11s} {'iii-i':>8s} {'iii-ii':>8s} {'n':>6s}", flush=True)

    LM_W = [0.5, 1.0, 2.0, 4.0]
    SHEAF = [1, 2]
    results = {}
    for sh in SHEAF:
        for lw in LM_W:
            r = run(test, vocab, fwd, bwd, fwd2, bwd2, lm_weight=lw, sheaf_depth=sh)
            si = r["single"][0]; do = r["dot"][0]; wa = r["wadm"][0]; n = r["wadm"][1]
            results[(lw, sh)] = r
            print(f"  {lw:5.1f} {sh:6d} {si:11.3f} {do:12.3f} {wa:11.3f} "
                  f"{wa-si:+8.3f} {wa-do:+8.3f} {n:6d}", flush=True)

    # context-2 (skip-2 backward) added to the deepest sheaf at lm_w=1.0 — does an
    # extra REAL frame (more context in the intersection) help further?
    r_ctx2 = run(test, vocab, fwd, bwd, fwd2, bwd2,
                 lm_weight=1.0, sheaf_depth=2, use_ctx2=True)
    print(f"  {'1.0':>5s} {'2+c2':>6s} {r_ctx2['single'][0]:11.3f} "
          f"{r_ctx2['dot'][0]:12.3f} {r_ctx2['wadm'][0]:11.3f} "
          f"{r_ctx2['wadm'][0]-r_ctx2['single'][0]:+8.3f} "
          f"{r_ctx2['wadm'][0]-r_ctx2['dot'][0]:+8.3f} {r_ctx2['wadm'][1]:6d}",
          flush=True)

    # === VERDICT ===
    print("\n" + "=" * 80, flush=True)
    print("VERDICT — does weighted-admissibility beat BOTH single and dot-product",
          flush=True)
    print("         on the REAL under-determined (cross-speaker) regime?", flush=True)
    print("=" * 80, flush=True)
    BAR = 0.02
    # principled cell: lm_weight 1.0, full sheaf (no cherry-pick).
    key = (1.0, 2)
    r = results[key]
    si = r["single"][0]; do = r["dot"][0]; wa = r["wadm"][0]
    over_det = wa - si
    soft_vs_scalar = wa - do
    print(f"  principled cell lm_w=1.0 sheaf=2 (n={r['wadm'][1]}):", flush=True)
    print(f"    single(i)={si:.3f}  dot-product(ii)={do:.3f}  weighted-admiss(iii)={wa:.3f}",
          flush=True)
    print(f"    over-determination  (iii - i)  = {over_det:+.3f}", flush=True)
    print(f"    soft-vs-scalar      (iii - ii) = {soft_vs_scalar:+.3f}", flush=True)

    best_cell = max(results.keys(), key=lambda k: results[k]["wadm"][0])
    rb = results[best_cell]
    print(f"  strongest wadm cell: lm_w={best_cell[0]} sheaf={best_cell[1]}  "
          f"wadm={rb['wadm'][0]:.3f} (i={rb['single'][0]:.3f}, ii={rb['dot'][0]:.3f}, "
          f"iii-i={rb['wadm'][0]-rb['single'][0]:+.3f}, "
          f"iii-ii={rb['wadm'][0]-rb['dot'][0]:+.3f})", flush=True)

    print("-" * 80, flush=True)
    beats_single = over_det > BAR
    beats_dot = soft_vs_scalar > BAR
    if beats_single and beats_dot:
        print(f"  CONFIRMED: on the REAL under-determined cross-speaker regime, "
              f"weighted-admissibility BEATS BOTH single-frame ({over_det:+.3f}, the "
              f"real LM over-determines what the cross-speaker acoustic can't) AND "
              f"dot-product ({soft_vs_scalar:+.3f}, soft intersection > premature "
              f"scalar) past the {BAR} bar.", flush=True)
    else:
        if not beats_single:
            print(f"  KILL (over-determination): weighted-admissibility does NOT beat "
                  f"single-frame ({over_det:+.3f}) -> the REAL LM does not help cross-"
                  f"speaker recognition here (SURPRISING; report plainly).", flush=True)
        if not beats_dot:
            print(f"  KILL (soft-vs-scalar): weighted-admissibility does NOT beat "
                  f"dot-product ({soft_vs_scalar:+.3f}) -> soft intersection does not "
                  f"beat the premature scalar sum on REAL data (report plainly).",
                  flush=True)
    print(f"  CHAIN(lm_w=1,sheaf=2): single {si:.3f} | dot {do:.3f} | wadm {wa:.3f} "
          f"| chance {chance:.3f}", flush=True)
    print("\n[MARKER] UNDER_DETERMINED_REAL_COMPLETED", flush=True)


if __name__ == "__main__":
    main()

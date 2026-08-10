"""frame_inference_v2 — recognition as a COLLAPSE over the WEIGHTED ADMISSIBILITY
of MULTIPLE soft-excluder frames, on cross-speaker DIGIT SEQUENCES.

Builds short digit SEQUENCES per speaker (len ~4-6) by concatenating real SC digit
clips under an IMPOSED bigram transition structure (the world's statistics — stated
honestly as imposed). Cross-speaker = HELD-OUT speakers' sequences (never banked).

FRAMES (each a SOFT EXCLUDER over the 10 digit candidates — abstain or exclude,
NEVER a positive boost):
  · SPEAKER-RELATIVE ACOUSTIC frame — v1's talker-relative formant reading -> 1-NN
    distances to the per-speaker frame-relative bank -> soft exclusion (closest
    admissible, others carved).
  · CONTEXT frame — the predecessor digit's bigram row -> soft-exclude successors
    the imposed transition makes unlikely.
  · FUTURE frame(s) (the SHEAF) — the successor digit's bigram COLUMN (1-step) and
    the 2-step lookahead -> soft-exclude predecessors inconsistent with what follows.
  · LEXICAL/PRIOR frame — the digit unigram prior (weak).

THREE REGIMES compared cross-speaker (per-digit accuracy):
  (i)   SINGLE-FRAME      — acoustic soft excluder alone, argmax per position.
  (ii)  DOT-PRODUCT       — frames as positive scores, SCALAR weighted SUM, argmax
                            (the premature collapse control).
  (iii) WEIGHTED-ADMISS.  — frames as soft excluders, vector-weighted INTERSECTION,
                            kept soft, decoded by Viterbi (context=forward pass,
                            future=backward pass over the sheaf). THE CLAIM.

PREDICTION: (iii) > (i)  [over-determination from context+future]
        AND (iii) > (ii) [soft intersection beats premature scalar].
KILL: (iii) !> (i) -> frames redundant / context doesn't constrain.
      (iii) !> (ii) -> soft-vs-scalar doesn't matter here.

SWEEPS: bigram PEAKINESS (how much imposed structure) x sheaf DEPTH (future lookahead).

Run: python -m scripts.frame_inference_v2 [n_train_spk] [n_held_spk] [n_seq] [seq_len] [n_ctx]
"""
from __future__ import annotations

import os
import sys
import random

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import domains.self_directed_speech_world as W
import domains.frame_inference_v2 as F2
from scripts.frame_inference_v1 import (
    formant_trajectory, infer_talker_frame, read_relative, absolute_logf,
    _dtw,
)

FS = W._TARGET_FS


# ===========================================================================
# THE WORLD — imposed bigram over the 10 digits + sequence construction.
# Stated HONESTLY: this transition structure is IMPOSED by us; it is the world's
# statistics, the thing context/future frames are meant to exploit. Held-out
# speakers' clips realise the sequence acoustically; the bigram is shared world
# knowledge (a property of the language, not of any speaker).
# ===========================================================================

def imposed_bigram(K, peakiness, seed=1234):
    """A KxK row-stochastic bigram with controllable peakiness. peakiness 0 ->
    uniform (no structure); higher -> a few likely successors per state, the rest
    rare. Built once, deterministically (the world's fixed statistics)."""
    rng = np.random.default_rng(seed)
    B = np.empty((K, K), dtype=np.float64)
    for a in range(K):
        # a fixed random preference vector per predecessor, sharpened by peakiness.
        base = rng.random(K) + 0.05
        logits = peakiness * np.log(base / base.sum() + 1e-9)
        row = np.exp(logits - logits.max())
        B[a] = row / row.sum()
    return B


def sample_sequences(spk_index, B, n_seq, seq_len, rng):
    """For one speaker: sample n_seq digit sequences of length seq_len from the
    imposed bigram, realising each digit acoustically with one of THAT speaker's
    clips for the digit. Returns list of [(digit_idx, clip_x), ...]. A speaker is
    skipped for a digit it has no clips for (resampled). Pure world construction."""
    K = B.shape[0]
    seqs = []
    avail = [d for d in range(K) if spk_index.get(d)]
    if len(avail) < 2:
        return seqs
    availset = set(avail)
    for _ in range(n_seq):
        # walk the bigram but stay within the speaker's available digits.
        cur = rng.choice(avail)
        path = [cur]
        for _t in range(seq_len - 1):
            row = B[cur].copy()
            mask = np.zeros(K)
            for d in availset:
                mask[d] = 1.0
            row = row * mask
            if row.sum() <= 0:
                cur = rng.choice(avail)
            else:
                cur = int(rng.choice(K, p=row / row.sum()))
            path.append(cur)
        seq = []
        ok = True
        for d in path:
            clips = spk_index.get(d)
            if not clips:
                ok = False
                break
            seq.append((d, clips[rng.integers(len(clips))]))
        if ok:
            seqs.append(seq)
    return seqs


# ===========================================================================
# SPLIT — train speakers (bank + bigram counts) and held-out speakers (test
# sequences, never banked). Per speaker: UNLABELED context clips for the frame.
# ===========================================================================

def build_split(n_train_spk, n_held_spk, n_per, n_ctx, seed=20240611):
    words = W.sc_words()
    K = len(words)
    rng = random.Random(seed)
    speakers = W.sc_speakers(words)
    rng.shuffle(speakers)
    held_spk = speakers[:n_held_spk]
    train_spk = speakers[n_held_spk:n_held_spk + n_train_spk]
    print(f"[split] {K} digits {words}", flush=True)
    print(f"[split] {len(train_spk)} TRAIN, {len(held_spk)} HELD-OUT speakers "
          "(disjoint; held clips NEVER banked)", flush=True)

    def carve(spk_list, n_body):
        out = {}
        for spk in spk_list:
            spk_idx = W.sc_index_for([spk], words)
            wp = [(wi, p) for wi, w in enumerate(words) for p in spk_idx.get(w, [])]
            rng.shuffle(wp)
            if len(wp) < n_ctx + 2:
                continue
            ctx = wp[:n_ctx]
            body = wp[n_ctx:n_ctx + n_body]
            ctx_clips = [W.load_sc_clip(p)[0] for _d, p in ctx]
            # per-digit pool of (loaded) clips for sequence realisation
            digit_clips = {}
            for d, p in body:
                digit_clips.setdefault(d, []).append(W.load_sc_clip(p)[0])
            out[spk] = (ctx_clips, digit_clips)
        return out

    train = carve(train_spk, n_per)
    held = carve(held_spk, max(n_per, 30))
    print(f"[split] {len(train)} train / {len(held)} held usable speakers; "
          f"{n_ctx} UNLABELED ctx clips/speaker (disjoint)", flush=True)
    return train, held, words


# ===========================================================================
# OWNED ACOUSTIC FRAME — the v1 talker-relative reading -> 1-NN distance to each
# digit's frame-relative bank exemplars -> the per-digit distance vector. The bank
# is built ONCE from train speakers, read relative to each train speaker's own
# inferred frame (same space as a relative-read test). Per-digit distance = the
# MIN DTW to that digit's exemplars (1-NN). Owned DSP throughout.
# ===========================================================================

def build_rel_bank(train, estimator, mode):
    """Per train speaker: infer frame from ctx, store each digit's exemplars
    frame-relative. Returns {digit -> [repr_array, ...]}."""
    bank = {}
    for spk, (ctx, digit_clips) in train.items():
        fr = infer_talker_frame(ctx, estimator=estimator)
        for d, clips in digit_clips.items():
            for x in clips:
                r = read_relative(x, fr, mode=mode)
                if r.shape[0]:
                    bank.setdefault(d, []).append(r)
    return bank


def acoustic_distances(x, frame, bank, K, mode, snr_db=None, noise_seed=0):
    """Per-digit 1-NN DTW distance of the frame-relative read of clip x against the
    digit's banked exemplars. Returns (K,) distances (inf for an empty bank/read).
    If snr_db is set, the test clip is corrupted by additive noise at that SNR FIRST
    (a WORLD-difficulty axis that DEGRADES the acoustic frame — it under-determines
    more as SNR falls, the regime where the multi-frame theory predicts a win). Noise
    injection is owned world DSP (self_directed_speech_world.inject_noise)."""
    if snr_db is not None:
        x = W.inject_noise(np.asarray(x, dtype=np.float32), snr_db=snr_db,
                           seed=noise_seed)
    r = read_relative(x, frame, mode=mode)
    d = np.full(K, np.inf, dtype=np.float64)
    if r.shape[0] == 0:
        return d
    for k in range(K):
        exs = bank.get(k)
        if not exs:
            continue
        best = np.inf
        for e in exs:
            dd = _dtw(r, e)
            if dd < best:
                best = dd
        d[k] = best
    return d


# ===========================================================================
# CONTEXT / FUTURE / PRIOR frames (owned bigram + unigram counts -> soft excluders).
# log-admissibility: log(prob / max(prob)) so the most-admissible successor sits at
# e==0 and the rest are carved. Built from the IMPOSED bigram (world statistics).
# ===========================================================================

def _row_excluder(prob_row):
    return F2.soft_exclude_from_score(prob_row)


def bigram_logadm(B):
    """trans[a,b] = log-admissibility of b given predecessor a (row-normalised)."""
    K = B.shape[0]
    T = np.zeros((K, K), dtype=np.float64)
    for a in range(K):
        T[a] = F2.soft_exclude_from_score(B[a])
    return T


def future_logadm(B):
    """back[b,a] = log-admissibility of a given SUCCESSOR b (column-normalised) —
    the 1-step future frame: knowing what comes next constrains the current digit."""
    K = B.shape[0]
    BT = np.zeros((K, K), dtype=np.float64)
    for b in range(K):
        col = B[:, b]
        BT[b] = F2.soft_exclude_from_score(col)
    return BT


def two_step_logadm(B):
    """2-step transition admissibility: B2[a,c] = P(c two steps after a)."""
    B2 = B @ B
    K = B.shape[0]
    T2 = np.zeros((K, K), dtype=np.float64)
    for a in range(K):
        T2[a] = F2.soft_exclude_from_score(B2[a])
    F2T = np.zeros((K, K), dtype=np.float64)
    for c in range(K):
        F2T[c] = F2.soft_exclude_from_score(B2[:, c])
    return T2, F2T  # (forward 2-step, backward 2-step)


def prior_logadm(B):
    """The unigram stationary prior of the imposed bigram -> a weak soft excluder."""
    K = B.shape[0]
    # power-iterate to the stationary distribution
    p = np.ones(K) / K
    for _ in range(200):
        p = p @ B
    return F2.soft_exclude_from_score(p)


# ===========================================================================
# THE THREE REGIMES — decode one held-out speaker's sequences.
# Vector weights for (iii): each frame's weight is its RELIABILITY (a measurement
# on TRAIN, not a sweep). We use a simple owned reliability: the acoustic frame is
# fully weighted (1); the context/future/prior frames are weighted by how PEAKED
# (informative) their excluder is per position (a vector weight in [0,1] = the
# fraction of admissibility they actually carve), which is a MEASUREMENT of the
# frame's evidence, not a tuned scalar. ABSTAIN (flat) -> weight ~0 automatically
# (e all 0 contributes nothing regardless of weight).
# ===========================================================================

def _posterior_confidence(e):
    """Per-position confidence in [0,1] of an acoustic read: how peaked is the
    admissibility mass on its best candidate. adm = exp(e) in (0,1]; conf = 1 -
    H(adm_normalised)/log(K) (1 = one clear winner, 0 = flat/abstain). A MEASUREMENT
    (owned), used to DOWN-WEIGHT a neighbour-conditioned frame when the neighbour
    estimate is uncertain — the faithful 'abstain where unsure': a cue conditioned
    on a shaky neighbour carves LESS, so it can never hurt."""
    e = np.asarray(e, dtype=np.float64)
    K = e.shape[0]
    if K <= 1:
        return 1.0
    adm = np.exp(e)
    p = adm / (adm.sum() + 1e-12)
    H = -np.sum(p * np.log(p + 1e-12))
    return float(max(0.0, 1.0 - H / np.log(K)))


def _expected_excluder(neighbor_post, table):
    """SOFT neighbour conditioning (keeps it soft — no hard argmax). neighbor_post:
    (K,) posterior over the neighbour digit (from its acoustic read). table: (K,K)
    log-admissibility rows indexed by the neighbour. Returns the EXPECTED excluder
    SUM_j post[j] * table[j] — the bigram constraint marginalised over the
    neighbour's uncertainty. If the neighbour is uncertain (near-uniform post) the
    expected excluder washes toward flat (ABSTAINS). Owned ops: weighted sum."""
    return neighbor_post @ table


def decode_speaker(seqs, frame, rel_bank, words, B, trans, back1, fwd2, back2,
                   prior_e, w_acoustic=1.0, sheaf_depth=1, mode="frac", snr_db=None):
    """Returns dict regime -> (correct, total) over all digit positions in this
    speaker's sequences. All three regimes share the SAME acoustic read."""
    K = len(words)
    res = {"single": [0, 0], "dot": [0, 0], "wadm": [0, 0]}
    for si, seq in enumerate(seqs):
        T = len(seq)
        truth = [d for d, _x in seq]
        # --- acoustic per-position: distance vector -> soft excluder + positive
        #     score + a normalised posterior (for soft neighbour conditioning).
        acou_e = np.zeros((T, K))
        acou_s = np.zeros((T, K))
        acou_post = np.zeros((T, K))
        for t, (_d, x) in enumerate(seq):
            dist = acoustic_distances(x, frame, rel_bank, K, mode, snr_db=snr_db,
                                      noise_seed=si * 97 + t)
            e = F2.soft_exclude_from_distance(dist)
            acou_e[t] = e
            s = F2.score_from_soft_exclude(e)
            acou_s[t] = s
            acou_post[t] = s / (s.sum() + 1e-12)

        # ============ (i) SINGLE-FRAME — acoustic argmax per position ============
        for t in range(T):
            g = int(np.argmax(acou_e[t]))
            res["single"][0] += int(g == truth[t])
            res["single"][1] += 1

        # ============ (ii) DOT-PRODUCT control =================================
        # SAME frames, but combined as a SCALAR weighted SUM of POSITIVE scores
        # (no veto, no intersection — a high score on one frame can RESCUE a
        # candidate another excluded). Neighbour conditioning uses the SAME soft
        # expected-excluder as (iii) (so the only difference between ii and iii is
        # SCALAR-positive-sum vs VECTOR-weighted-log-intersection — the claim).
        for t in range(T):
            scores = [acou_s[t]]
            wts = [1.0]
            if t > 0:                                   # context (predecessor)
                ce = _expected_excluder(acou_post[t - 1], trans)
                scores.append(F2.score_from_soft_exclude(ce)); wts.append(1.0)
            if sheaf_depth >= 1 and t < T - 1:          # 1-step future
                fe = _expected_excluder(acou_post[t + 1], back1)
                scores.append(F2.score_from_soft_exclude(fe)); wts.append(1.0)
            if sheaf_depth >= 2 and t < T - 2:          # 2-step future
                fe2 = _expected_excluder(acou_post[t + 2], back2)
                scores.append(F2.score_from_soft_exclude(fe2)); wts.append(1.0)
            scores.append(F2.score_from_soft_exclude(prior_e)); wts.append(0.3)
            comb = F2.dot_product_combine(scores, wts)
            g = int(np.argmax(comb))
            res["dot"][0] += int(g == truth[t])
            res["dot"][1] += 1

        # ============ (iii) WEIGHTED-ADMISSIBILITY collapse ====================
        # Emission per position = acoustic (+) prior (+) FUTURE-sheaf soft excluder,
        # vector-weighted INTERSECTION (sum of weighted log-admissibilities). The
        # CONTEXT frame is the Viterbi forward transition (predecessor constrains
        # via the DP; the backtrace makes it bidirectional). Each neighbour-
        # conditioned frame is the SOFT expected excluder, additionally DOWN-WEIGHTED
        # by the neighbour's posterior confidence (abstain-where-unsure: a shaky
        # neighbour carves less, never hurts). w_acoustic on the acoustic frame.
        emis = np.zeros((T, K))
        for t in range(T):
            excl = [acou_e[t], prior_e]
            wv = [w_acoustic, 0.3]
            if sheaf_depth >= 1 and t < T - 1:          # 1-step future excluder
                fe = _expected_excluder(acou_post[t + 1], back1)
                excl.append(fe); wv.append(_posterior_confidence(acou_e[t + 1]))
            if sheaf_depth >= 2 and t < T - 2:          # 2-step future excluder
                fe2 = _expected_excluder(acou_post[t + 2], back2)
                excl.append(fe2); wv.append(_posterior_confidence(acou_e[t + 2]))
            emis[t] = F2.weighted_admissibility(excl, wv)
        # context = forward Viterbi transition (predecessor's bigram log-adm). The
        # DP folds the whole sequence — each position constrained by both directions.
        path = F2.viterbi_soft(emis, trans, w_trans=1.0)
        for t in range(T):
            res["wadm"][0] += int(path[t] == truth[t])
            res["wadm"][1] += 1
    return res


# ===========================================================================
# HARNESS
# ===========================================================================

def run_once(train, held, words, peakiness, sheaf_depth, estimator="pctl",
             mode="frac", n_seq=8, seq_len=5, seed=7, snr_db=None, rel_bank=None):
    K = len(words)
    B = imposed_bigram(K, peakiness)
    trans = bigram_logadm(B)
    back1 = future_logadm(B)
    fwd2, back2 = two_step_logadm(B)
    prior_e = prior_logadm(B)
    if rel_bank is None:
        rel_bank = build_rel_bank(train, estimator, mode)

    agg = {"single": [0, 0], "dot": [0, 0], "wadm": [0, 0]}
    rng_master = np.random.default_rng(seed)
    nspk = 0
    for spk, (ctx, digit_clips) in held.items():
        fr = infer_talker_frame(ctx, estimator=estimator)
        rng = np.random.default_rng(rng_master.integers(1 << 30))
        seqs = sample_sequences(digit_clips, B, n_seq, seq_len, rng)
        if not seqs:
            continue
        r = decode_speaker(seqs, fr, rel_bank, words, B, trans, back1, fwd2, back2,
                           prior_e, sheaf_depth=sheaf_depth, mode=mode, snr_db=snr_db)
        for k in agg:
            agg[k][0] += r[k][0]
            agg[k][1] += r[k][1]
        nspk += 1
    out = {k: (agg[k][0] / max(agg[k][1], 1), agg[k][1]) for k in agg}
    out["_nspk"] = nspk
    return out


def main():
    if not W.sc_available():
        print("Speech Commands not found at /tmp/sc — abort.", flush=True)
        return
    n_train_spk = int(sys.argv[1]) if len(sys.argv) > 1 else 80
    n_held_spk = int(sys.argv[2]) if len(sys.argv) > 2 else 30
    n_seq = int(sys.argv[3]) if len(sys.argv) > 3 else 8
    seq_len = int(sys.argv[4]) if len(sys.argv) > 4 else 5
    n_ctx = int(sys.argv[5]) if len(sys.argv) > 5 else 8

    train, held, words = build_split(n_train_spk, n_held_spk, n_per=12, n_ctx=n_ctx)
    K = len(words)
    chance = 1.0 / K

    PEAKINESS = [0.0, 2.0, 6.0]      # uniform -> mild -> sharp imposed structure
    SHEAF = [1, 2]                   # 1-step future, 1+2-step future sheaf

    print("\n" + "=" * 78, flush=True)
    print("FRAME-INFERENCE v2 — weighted-admissibility collapse vs single vs dot-product",
          flush=True)
    print("=" * 78, flush=True)
    print(f"  chance {chance:.3f}  seq_len {seq_len}  n_seq/speaker {n_seq}  "
          f"ctx {n_ctx}", flush=True)
    print(f"  {'peak':>5s} {'sheaf':>6s} {'single(i)':>11s} {'dotprod(ii)':>12s} "
          f"{'wadm(iii)':>11s} {'iii-i':>8s} {'iii-ii':>8s} {'n':>6s} {'spk':>4s}",
          flush=True)

    # build the frame-relative bank ONCE (mode/estimator fixed across the sweep —
    # the bank is the acoustic model, shared by all regimes; no per-cell refit).
    rel_bank = build_rel_bank(train, "pctl", "frac")

    results = {}
    for pk in PEAKINESS:
        for sh in SHEAF:
            r = run_once(train, held, words, pk, sh, n_seq=n_seq, seq_len=seq_len,
                         rel_bank=rel_bank)
            si = r["single"][0]; do = r["dot"][0]; wa = r["wadm"][0]
            n = r["wadm"][1]; nspk = r["_nspk"]
            results[(pk, sh)] = r
            print(f"  {pk:5.1f} {sh:6d} {si:11.3f} {do:12.3f} {wa:11.3f} "
                  f"{wa-si:+8.3f} {wa-do:+8.3f} {n:6d} {nspk:4d}", flush=True)

    # ---- ACOUSTIC-STRENGTH (SNR) DIAGNOSTIC — the decisive axis. The theory says
    # multi-frame collapse pays exactly when the SINGLE frame UNDER-determines. We
    # DEGRADE the acoustic frame with additive noise (a world-difficulty axis, NOT a
    # fit) at the sharp-structure cell (peak=6, sheaf=1) and map where each regime
    # wins. If iii overtakes i and ii as SNR falls, the claim holds in the
    # under-determined regime (the v1 premise); if not, the frames are redundant
    # even when acoustics are weak.
    SNR = [None, 10.0, 5.0, 0.0, -5.0]   # None = clean
    print("\n  -- ACOUSTIC-STRENGTH sweep (peak=6.0, sheaf=1; noise DEGRADES the "
          "single frame) --", flush=True)
    print(f"  {'snr_dB':>7s} {'single(i)':>11s} {'dotprod(ii)':>12s} "
          f"{'wadm(iii)':>11s} {'iii-i':>8s} {'iii-ii':>8s} {'n':>6s}", flush=True)
    snr_results = {}
    for snr in SNR:
        r = run_once(train, held, words, 6.0, 1, n_seq=n_seq, seq_len=seq_len,
                     rel_bank=rel_bank, snr_db=snr)
        si = r["single"][0]; do = r["dot"][0]; wa = r["wadm"][0]
        snr_results[snr] = r
        tag = "clean" if snr is None else f"{snr:.0f}"
        print(f"  {tag:>7s} {si:11.3f} {do:12.3f} {wa:11.3f} "
              f"{wa-si:+8.3f} {wa-do:+8.3f} {r['wadm'][1]:6d}", flush=True)

    # ---- VERDICT: pick the most-structured / deepest-sheaf cell (the regime where
    # context+future SHOULD help most) and report; also the best wadm overall.
    print("\n" + "=" * 78, flush=True)
    print("VERDICT", flush=True)
    print("=" * 78, flush=True)
    # best-structure cell
    key = (PEAKINESS[-1], SHEAF[-1])
    r = results[key]
    si = r["single"][0]; do = r["dot"][0]; wa = r["wadm"][0]
    print(f"  best-structure cell peak={key[0]} sheaf={key[1]}  (n={r['wadm'][1]}, "
          f"{r['_nspk']} held speakers):", flush=True)
    print(f"    single(i)={si:.3f}  dot-product(ii)={do:.3f}  "
          f"weighted-admiss(iii)={wa:.3f}", flush=True)
    over_det = wa - si
    soft_vs_scalar = wa - do
    print(f"    over-determination  (iii - i)  = {over_det:+.3f}", flush=True)
    print(f"    soft-vs-scalar      (iii - ii) = {soft_vs_scalar:+.3f}", flush=True)

    # the strongest case across all cells
    best_cell = max(results.keys(), key=lambda k: results[k]["wadm"][0])
    rb = results[best_cell]
    print(f"  strongest wadm cell: peak={best_cell[0]} sheaf={best_cell[1]}  "
          f"wadm={rb['wadm'][0]:.3f} (i={rb['single'][0]:.3f}, ii={rb['dot'][0]:.3f}, "
          f"iii-i={rb['wadm'][0]-rb['single'][0]:+.3f}, "
          f"iii-ii={rb['wadm'][0]-rb['dot'][0]:+.3f})", flush=True)

    beats_single = over_det > 0.0
    beats_dot = soft_vs_scalar > 0.0
    BAR = 0.02
    print("-" * 78, flush=True)
    if over_det > BAR and soft_vs_scalar > BAR:
        print(f"  PAYS: weighted-admissibility BEATS BOTH single-frame "
              f"({over_det:+.3f}, over-determination) AND dot-product "
              f"({soft_vs_scalar:+.3f}, soft-vs-scalar) past the {BAR} bar.", flush=True)
    else:
        if not beats_single:
            print(f"  KILL (over-determination): weighted-admissibility does NOT beat "
                  f"single-frame ({over_det:+.3f}) -> the context/future frames are "
                  "redundant / the imposed context does not constrain enough.", flush=True)
        elif over_det <= BAR:
            print(f"  WEAK (over-determination): iii edges single by only {over_det:+.3f} "
                  f"(< {BAR} bar).", flush=True)
        if not beats_dot:
            print(f"  KILL (soft-vs-scalar): weighted-admissibility does NOT beat "
                  f"dot-product ({soft_vs_scalar:+.3f}) -> soft intersection does not "
                  "beat the premature scalar sum HERE.", flush=True)
        elif soft_vs_scalar <= BAR:
            print(f"  WEAK (soft-vs-scalar): iii edges dot-product by only "
                  f"{soft_vs_scalar:+.3f} (< {BAR} bar).", flush=True)
    print(f"  CHAIN(best-structure): single {si:.3f} | dot {do:.3f} | wadm {wa:.3f} "
          f"| chance {chance:.3f}", flush=True)

    # ---- the SNR diagnostic verdict: the cell (if any) where iii beats BOTH.
    print("-" * 78, flush=True)
    win_snr = None
    for snr, r in snr_results.items():
        od = r["wadm"][0] - r["single"][0]
        sv = r["wadm"][0] - r["dot"][0]
        if od > BAR and sv > BAR:
            win_snr = (snr, od, sv, r)
            break
    if win_snr is not None:
        snr, od, sv, r = win_snr
        tag = "clean" if snr is None else f"{snr:.0f} dB"
        print(f"  UNDER-DETERMINED REGIME: at SNR={tag} the SINGLE frame under-"
              f"determines (i={r['single'][0]:.3f}) and weighted-admissibility BEATS "
              f"BOTH single (+{od:.3f}) AND dot-product (+{sv:.3f}) -> the claim holds "
              "where one frame is insufficient.", flush=True)
    else:
        print("  NO under-determined cell where iii beats BOTH past the bar across "
              "the SNR sweep -> on this digit task the speaker-relative acoustic frame "
              "either resolves it alone or stays the strongest single signal; the "
              "imposed bigram context/future is redundant with it.", flush=True)
    print("\n[MARKER] FRAME_INFERENCE_V2_COMPLETED", flush=True)


if __name__ == "__main__":
    main()

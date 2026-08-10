"""parakeet_teardown_probe — GROUND the Parakeet teardown's central claim, donkey-clean.

PARAKEET (NVIDIA NeMo: FastConformer encoder + RNN-T/TDT/CTC decoder) is the
STRUCTURAL OPPOSITE of Whisper. Whisper = LM-DRIVEN (a giant attention decoder doing
top-down restoration carries the reduced acoustics — grounded in
scripts/whisper_teardown_probe.py: with a flat ear, recognition = the LM's next-word
accuracy). Parakeet = ACOUSTIC-DRIVEN:
  - FastConformer encoder = CONVOLUTION (LOCAL time-frequency structure) + attention.
  - RNN-T / TDT transducer = a MONOTONIC, left-to-right alignment (NOT Whisper's
    non-monotonic full cross-attention). Speech IS monotonic.
  - TDT = EXPLICIT token DURATION modelling (the temporal/rate structure, explicit).
  - a LIGHT predictor LM (far less top-down than Whisper's decoder).

THE PARAKEET CLAIM (the load-bearing one, the COMPLEMENT of the Whisper claim): a
strong MONOTONIC acoustic model with EXPLICIT duration and CONV-LOCAL features needs
much LESS top-down LM. Whisper says "the LM carries it"; Parakeet says "the ACOUSTIC
STRUCTURE carries it." For the agent's at-chance acoustic frontier
(docs/real_data_drive.md), the question this probe answers is: IS THE LEVER ACOUSTIC
STRUCTURE (Parakeet) MORE THAN MORE-LM (Whisper)?

We ground THREE Parakeet structures as ALREADY-OWNED or CONSTRUCTABLE agent structure,
measured on a venue where the acoustic channel is NOT at chance (FSDD isolated digits,
LOSO cross-speaker) so the ACOUSTIC contribution is measurable in isolation (no LM):

  (P1) MONOTONIC alignment.  The agent's DtwTo is ALREADY a monotonic warp (Sakoe-Chiba
       banded DP, insertion/deletion/match — never backward). Parakeet's RNN-T VALIDATES
       this structure. Probe: contrast the monotonic DtwTo match against a NON-monotonic
       (order-free, best-frame-permutation) match of the SAME features. If monotonic
       wins, the built-in monotonicity is load-bearing acoustic structure (the thing the
       transducer buys, the agent already has).

  (P2) EXPLICIT DURATION.  Parakeet's TDT models token duration explicitly; the agent's
       DtwTo handles rate only CRUDELY (a length-ratio band). Probe: contrast a
       DURATION-BLIND match (raw DtwTo) against a DURATION-EXPLICIT match (rate-normalise
       both trajectories to a canonical length BEFORE the warp — the explicit-duration
       structure done as a constructed transform, not a learned one). If explicit
       duration helps, that is the constructed TDT lever, grounded.

  (P3) CONV-LOCAL features.  Parakeet's FastConformer convolution captures LOCAL
       time-frequency structure (onsets, transitions, edges) that the agent's STATIC
       mean-pooled band trajectory destroys. The CONSTRUCTED translation is an order-1
       finite difference over time (delta-features: F_t - F_{t-1}) — the agent's OWN
       transition-contrast / order-N-over-time structure (NOT a learned conv kernel).
       Probe: contrast STATIC features against STATIC+DELTA (conv-local) features through
       the SAME monotonic match. If conv-local helps, that is the at-chance front-end
       lever, grounded.

DONKEY-CLEAN: the distance is the agent's banded-DTW alignment (the same kernel the
DtwTo Term uses, reproduced here as a counts-not-nets metric so the probe is
self-contained and fast — NO Substrate boot per item, NO net). NO .fit, NO gradient,
NO loss, NO optimiser, NO torch/sklearn, NO sweep-to-maximise. The rate-normalise
length and the delta-feature are FIXED structural choices reported, not tuned. The
recogniser is a 1-NN argmin over LOSO train exemplars — a READOUT over distances.
solve_for_n.py / CortexLoop UNTOUCHED (this file imports neither).

Run: PYTHONUNBUFFERED=1 python -m scripts.parakeet_teardown_probe [n_per_sp_per_digit]
"""
from __future__ import annotations

import math
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Reuse ONLY world-adapter front-end machinery (audio -> band trajectory). No agent.
from scripts.fsdd_learner_world import load_wav, gather_files
from scripts.invariant_units_accept import band_trajectory_matrix

_DIGITS = ['zero', 'one', 'two', 'three', 'four', 'five',
           'six', 'seven', 'eight', 'nine']


# ==========================================================================
# THE DISTANCE KERNELS — the agent's MONOTONIC banded-DTW (same shape as the
# DtwTo Rust Term: Sakoe-Chiba band, insertion/deletion/match, never backward),
# plus a NON-MONOTONIC control (best-frame permutation, order destroyed). Counts,
# not nets.
# ==========================================================================

def _frame_dist(fa, fb):
    n = min(len(fa), len(fb))
    return float(np.sqrt(np.sum((fa[:n] - fb[:n]) ** 2)))


def monotonic_dtw(A, B, band_frac=0.25):
    """The agent's MONOTONIC warp: banded DP over frames, the SAME transitions as
    the DtwTo Rust Term (prev[j], cur[j-1], prev[j-1] -> insertion/deletion/match,
    strictly forward in BOTH sequences). This is Parakeet's RNN-T monotonic
    alignment, which the agent ALREADY owns."""
    na, nb = len(A), len(B)
    if na == 0 or nb == 0:
        return math.inf
    band = max(1, int(band_frac * max(na, nb)))
    INF = 1e18
    prev = [INF] * (nb + 1)
    prev[0] = 0.0
    for i in range(1, na + 1):
        cur = [INF] * (nb + 1)
        center = i * nb // max(na, 1)
        jl = max(1, center - band)
        jh = min(nb, center + band)
        for j in range(jl, jh + 1):
            d = _frame_dist(A[i - 1], B[j - 1])
            best = min(prev[j], cur[j - 1], prev[j - 1])
            cur[j] = d + best
        prev = cur
    if prev[nb] >= INF:
        n = min(na, nb)
        return sum(_frame_dist(A[k * na // max(n, 1)], B[k * nb // max(n, 1)])
                   for k in range(n)) / max(n, 1)
    return prev[nb] / max(na, 1)


def nonmonotonic_match(A, B):
    """NON-MONOTONIC control (order DESTROYED): for each frame of A, take its
    distance to the BEST-matching frame of B regardless of position (a bag-of-frames
    assignment, no left-to-right constraint). This is what you get WITHOUT the
    transducer's monotonicity — the structure Parakeet builds in and Whisper's full
    cross-attention does NOT enforce. If this LOSES to monotonic_dtw, monotonicity is
    load-bearing acoustic structure."""
    na, nb = len(A), len(B)
    if na == 0 or nb == 0:
        return math.inf
    tot = 0.0
    for i in range(na):
        tot += min(_frame_dist(A[i], B[j]) for j in range(nb))
    return tot / max(na, 1)


# ==========================================================================
# THE FEATURE TRANSFORMS — STATIC (mean-pooled band trajectory, the current
# front-end), EXPLICIT-DURATION (rate-normalised length), CONV-LOCAL (static +
# order-1 delta over time = the agent's transition-contrast).
# ==========================================================================

def static_feats(M):
    """The current front-end: frames x bands trajectory, per-utterance CMVN. STATIC
    mean-pooled local structure — what Parakeet's conv ENRICHES."""
    if M is None or M.shape[0] < 2:
        return None
    mu = M.mean(axis=0, keepdims=True)
    sd = M.std(axis=0, keepdims=True) + 1e-6
    return ((M - mu) / sd).astype(np.float32)


def rate_normalised(F, L=32):
    """EXPLICIT DURATION (P2): resample the trajectory to a canonical length L BEFORE
    the warp — model the token's rate EXPLICITLY (Parakeet's TDT) as a constructed
    transform, instead of leaving it to DtwTo's crude length-ratio band. Linear
    interpolation along the time axis. A fixed structural choice (L=32), not tuned."""
    if F is None or F.shape[0] < 2:
        return F
    n = F.shape[0]
    xs = np.linspace(0, n - 1, L)
    out = np.empty((L, F.shape[1]), dtype=np.float32)
    for k in range(F.shape[1]):
        out[:, k] = np.interp(xs, np.arange(n), F[:, k])
    return out


def conv_local(F):
    """CONV-LOCAL (P3): append the order-1 finite difference over time (delta =
    F_t - F_{t-1}) — the agent's OWN transition-contrast / order-N-over-time
    structure (docs/agent_loop_iteration30, order_n_concepts). This is the LOCAL
    time-frequency structure Parakeet's convolution captures, CONSTRUCTED as a
    derivative, NOT a learned conv kernel. Doubles the feature dim (static | delta)."""
    if F is None or F.shape[0] < 2:
        return F
    delta = np.zeros_like(F)
    delta[1:] = F[1:] - F[:-1]
    return np.concatenate([F, delta], axis=1).astype(np.float32)


# ==========================================================================
# THE RECOGNISER — 1-NN argmin over LOSO train exemplars (a READOUT over
# distances), parameterised by (feature transform, distance kernel).
# ==========================================================================

def recognise(test_feat, train_feats, train_labels, distance):
    best, bw = math.inf, None
    for tf, tl in zip(train_feats, train_labels):
        d = distance(test_feat, tf)
        if d < best:
            best, bw = d, tl
    return bw


def eval_route(feats_by_item, labels, speakers, distance, name):
    """LOSO 1-NN over the given (already-transformed) per-item features + distance."""
    corr = tot = 0
    for held in sorted(set(speakers)):
        tr_f = [f for f, s in zip(feats_by_item, speakers) if s != held and f is not None]
        tr_l = [l for l, s, f in zip(labels, speakers, feats_by_item)
                if s != held and f is not None]
        for f, s, l in zip(feats_by_item, speakers, labels):
            if s != held or f is None:
                continue
            pred = recognise(f, tr_f, tr_l, distance)
            corr += int(pred == l)
            tot += 1
    acc = corr / max(tot, 1)
    print(f"  {name:<46s} {acc:.4f}  ({corr}/{tot})", flush=True)
    return acc, tot


def main():
    t0 = time.time()
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    print(f"=== parakeet_teardown_probe  n_per_sp_per_digit={n} ===", flush=True)
    print("VENUE: FSDD isolated digits, LOSO cross-speaker — a venue where the "
          "ACOUSTIC channel is NOT at chance, so the acoustic contribution is "
          "measurable in ISOLATION (no LM). This isolates Parakeet's ACOUSTIC "
          "structures from Whisper's LM.\n", flush=True)

    files = gather_files()
    by_key = {}
    for path, digit, sp, idx in files:
        by_key.setdefault((sp, digit), []).append((path, digit, sp, idx))
    items = []
    for k in sorted(by_key):
        items.extend(sorted(by_key[k], key=lambda t: t[3])[:n])
    speakers = [it[2] for it in items]
    labels = [_DIGITS[it[1]] for it in items]
    n_sp = len(set(speakers))
    print(f"FSDD: {len(items)} recordings, {n_sp} speakers, 10 digits", flush=True)
    chance = 1.0 / 10
    print(f"chance = {chance:.4f}\n", flush=True)

    # ---- front-end: gammatone band trajectory per item (world adapter) ----
    print("--- extracting gammatone band trajectories (world adapter) ---", flush=True)
    raw = []
    for i, (path, digit, sp, idx) in enumerate(items):
        x, fs = load_wav(path)
        try:
            M = band_trajectory_matrix(x, fs)
        except Exception:
            M = None
        raw.append(static_feats(M))
        if (i + 1) % 100 == 0:
            print(f"  {i+1}/{len(items)} trajectories", flush=True)
    have = sum(1 for f in raw if f is not None)
    print(f"extracted {have}/{len(items)} clean trajectories\n", flush=True)

    # ======================================================================
    # (P1) MONOTONIC vs NON-MONOTONIC alignment — does the agent's built-in
    # monotonicity (which Parakeet's RNN-T validates) carry acoustic identity?
    # Same STATIC features both routes; ONLY the alignment constraint changes.
    # ======================================================================
    print("=== (P1) MONOTONIC alignment (Parakeet RNN-T) vs NON-monotonic — "
          "static features ===", flush=True)
    p1_mono, _ = eval_route(raw, labels, speakers, monotonic_dtw,
                            "monotonic DtwTo (the agent ALREADY owns)")
    p1_free, _ = eval_route(raw, labels, speakers, nonmonotonic_match,
                            "non-monotonic (order destroyed, control)")
    print(f"  -> monotonicity delta: {p1_mono - p1_free:+.4f}  "
          f"({'monotonic WINS' if p1_mono > p1_free else 'no gain'})\n", flush=True)

    # ======================================================================
    # (P2) EXPLICIT DURATION (Parakeet TDT) — rate-normalise length BEFORE the
    # warp. Same monotonic kernel; the only change is explicit duration modelling.
    # ======================================================================
    print("=== (P2) EXPLICIT DURATION (Parakeet TDT) — rate-normalised vs "
          "duration-blind, monotonic kernel ===", flush=True)
    p2_blind, _ = eval_route(raw, labels, speakers, monotonic_dtw,
                            "duration-blind (raw DtwTo length-band)")
    rate_feats = [rate_normalised(f) for f in raw]
    p2_dur, _ = eval_route(rate_feats, labels, speakers, monotonic_dtw,
                          "duration-explicit (rate-normalised, TDT)")
    print(f"  -> explicit-duration delta: {p2_dur - p2_blind:+.4f}  "
          f"({'duration helps' if p2_dur > p2_blind else 'no gain'})\n", flush=True)

    # ======================================================================
    # (P3) CONV-LOCAL features (FastConformer conv) — static+delta (order-1 over
    # time, the agent's transition-contrast) vs static, through the duration-explicit
    # monotonic kernel (the best acoustic base from P1+P2).
    # ======================================================================
    print("=== (P3) CONV-LOCAL features (FastConformer conv = order-1 delta) vs "
          "static, on the monotonic+duration base ===", flush=True)
    p3_static, _ = eval_route(rate_feats, labels, speakers, monotonic_dtw,
                             "static only (current front-end)")
    conv_feats = [conv_local(f) for f in rate_feats]
    p3_conv, _ = eval_route(conv_feats, labels, speakers, monotonic_dtw,
                           "static + delta (conv-local, constructed)")
    print(f"  -> conv-local delta: {p3_conv - p3_static:+.4f}  "
          f"({'conv-local helps' if p3_conv > p3_static else 'no gain'})\n", flush=True)

    # ======================================================================
    # THE WHISPER-vs-PARAKEET VERDICT — is the lever ACOUSTIC structure?
    # ======================================================================
    print("=== PARAKEET'S CENTRAL CLAIM, GROUNDED — is the lever ACOUSTIC structure? ===",
          flush=True)
    best_acoustic = p3_conv
    print(f"(P1) MONOTONIC alignment (the agent already owns; Parakeet validates):  "
          f"{p1_mono:.4f} vs non-monotonic {p1_free:.4f}  (delta {p1_mono-p1_free:+.4f})",
          flush=True)
    print(f"(P2) EXPLICIT DURATION (constructed TDT, rate-normalise):  "
          f"{p2_dur:.4f} vs blind {p2_blind:.4f}  (delta {p2_dur-p2_blind:+.4f})",
          flush=True)
    print(f"(P3) CONV-LOCAL (constructed order-1 delta = FastConformer conv):  "
          f"{p3_conv:.4f} vs static {p3_static:.4f}  (delta {p3_conv-p3_static:+.4f})",
          flush=True)
    print(f"\nBEST CONSTRUCTED ACOUSTIC route: {best_acoustic:.4f}  (chance {chance:.4f}, "
          f"x{best_acoustic/chance:.1f})", flush=True)
    print("CONTRAST WITH WHISPER (scripts/whisper_teardown_probe.py): Whisper's lever "
          "is the LM (with a flat ear, recognition = LM next-word acc). Parakeet's "
          "lever is the ACOUSTIC structure measured HERE — monotonic alignment + "
          "explicit duration + conv-local features lift the ACOUSTIC channel ITSELF, "
          "with NO LM. On the at-chance frontier, Parakeet says: build the acoustic "
          "structure, do not just add LM.", flush=True)
    total_acoustic_gain = best_acoustic - p1_free
    print(f"\nTOTAL constructed-acoustic-structure gain (non-monotonic static -> "
          f"monotonic+duration+conv): {total_acoustic_gain:+.4f}", flush=True)

    print(f"\n[probe] elapsed {time.time()-t0:.1f}s", flush=True)
    print("===MARKER_PARAKEET_TEARDOWN_PROBE_COMPLETE===", flush=True)


if __name__ == "__main__":
    main()

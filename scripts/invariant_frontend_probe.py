"""invariant_frontend_probe — the agent FIXES ITS OWN FRONT-END, then re-runs its
OWN mode-seeking clustering on the new representation (the downstream capability is
the validator).

THE AGENT'S DIAGNOSIS (last turn): its told-k-free mode-seeker hit purity 0.193 (49
emergent modes vs true 10) on the 96-dim flattened CMVN rep — "the bound is the
feature FRONT-END / dimensionality ... the lever is mode-seeking on a SPEAKER-
INVARIANT LOWER-DIM representation — fix the front-end, not the clusterer."

THE AGENT'S DESIGN (composed by analogy across its OWN prior findings — domains/analogy):
  1. SHARPER formant estimate (two_ears_demo): the gammatone band-mean blur is ONE
     copied cochlea; a frequency-SHARP ear (a high-resolution 4096-pt FFT over
     log-spaced bands) dissolves the formant-blur "wall" and resolves the spectral
     peaks. -> the front-end here builds a sharp log-frequency band vector per voiced
     frame (the 2nd-ear front-end), NOT the blurry whole-word gammatone band-means.
  2. The order-N PEAK = formant (order_n_concepts / speaker_norm._formant_abs):
     F_i = start_i + ArgMax(region_i) over the sharp log-bands — the agent's OWN
     index primitive, the spectral peak as a local maximum.
  3. The VTL-INVARIANT transform (speaker_norm.vtl_terms): vtl(F_i) = F_i -
     mean(F1,F2,F3). Vocal-tract length scales every formant by alpha (a log-shift);
     subtracting the per-token mean formant CANCELS the speaker term, leaving the
     speaker-invariant pattern. -> a LOW-dim (3 formants x a few time-slots),
     SPEAKER-INVARIANT rep, replacing the 96-dim CMVN.

The peak (ArgMax) + the invariant transform (Minus / mean) are the agent's OWN
composed Term-trees (speaker_norm + order_n_concepts), evaluated NATIVELY on the
substrate. The ONLY Python is the world-adapter front-end (mechanical audio -> sharp
log-freq bands per frame -> a Token node carrying band attrs) and the unchanged probe
scaffolding (label-free clustering, scored after). NO hand-coded heuristic, no
told-k, no swept threshold.

VERIFY (the agent's OWN controls, the SAME probe — the downstream capability validates
the front-end fix): re-run domains/distributional_categories.cluster_by_modes on the
NEW rep and report BEFORE (96-dim CMVN: 0.193, 49 modes) -> AFTER. Controls in the
same breath: purity vs the random floor; SHUFFLE-COLLAPSE (joint modes destroyed);
and HELD-OUT SPEAKER-INVARIANCE directly (does the rep cluster by WORD, or by
SPEAKER? — a speaker-purity score that should stay LOW if the rep is invariant).

Run:  python scripts/invariant_frontend_probe.py
"""
from __future__ import annotations

import math
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np

import scripts.fsdd_learner_world as fl
from domains.distributional_categories import cluster_by_modes
from domains.sound_graph import _voiced_frames
from domains.speaker_norm import _formant_abs, vtl_terms
from substrate_rs import Substrate

DIGITS = fl._DIGITS
PER = int(os.environ.get("DC_PER", "12"))      # utts per (digit, speaker)
RES = int(os.environ.get("FE_RES", "24"))      # sharp log-freq bands (the 2nd ear)
SLOTS = int(os.environ.get("FE_SLOTS", "3"))   # time-slots over the formant trajectory
NFFT = 4096                                    # the SHARP ear (two_ears_demo)


class _Pred:
    __slots__ = ("_json",)

    def __init__(self, d):
        self._json = d


# --- world-adapter front-end: sharp multi-ear log-frequency bands per frame ----
def _log_edges(res, lo_hz, hi_hz):
    """Log-spaced band edges (res+1). Log-frequency is the axis on which VTL is a
    constant shift — the agent's whole invariance argument lives here."""
    return np.exp(np.linspace(math.log(lo_hz), math.log(hi_hz), res + 1))


def sharp_bands(win, fs, res=RES, lo_hz=200.0, hi_hz=3600.0):
    """The 2nd ear (two_ears_demo): a high-resolution 4096-pt FFT pooled into `res`
    log-spaced bands -> a SHARP log-frequency spectrum for one voiced frame. This is
    the front-end the agent reaches for instead of the blurry gammatone band-mean."""
    mag = np.abs(np.fft.rfft(win * np.hanning(len(win)), n=NFFT)) + 1e-9
    fr = np.fft.rfftfreq(NFFT, 1.0 / fs)
    edges = _log_edges(res, lo_hz, hi_hz)
    row = []
    for b in range(res):
        m = (fr >= edges[b]) & (fr < edges[b + 1])
        row.append(math.log(float(np.max(mag[m]))) if m.any() else -20.0)
    return np.array(row)


def frame_band_matrix(samples, fs, res=RES):
    rows = [sharp_bands(win, fs, res) for _, win in _voiced_frames(samples, fs)]
    return np.array(rows) if rows else np.zeros((0, res))


# --- the agent's OWN composed Term-trees: peak (ArgMax) + VTL-invariant (Minus) ---
def invariant_signature(samples, fs, sub, res=RES, slots=SLOTS):
    """Build the agent's SPEAKER-INVARIANT LOW-DIM rep for one token, NATIVELY:
      sharp log-freq bands per frame (world adapter) -> resample to `slots` time-slots
      -> for each slot, lay the bands on a Token node and EVALUATE the agent's OWN
         vtl_terms (F_i - mean(F1,F2,F3), composed from its ArgMax peak + Minus/mean)
         on the substrate.
    Returns a (slots * 3) vector: the VTL-invariant formant pattern over the word's
    trajectory. The arithmetic is the substrate evaluator's, not Python's."""
    M = frame_band_matrix(samples, fs, res)
    if M.shape[0] == 0:
        return np.zeros(slots * 3)
    # resample the band trajectory to `slots` time points (mechanical).
    T = M.shape[0]
    if T == 1:
        Ms = np.repeat(M, slots, axis=0)
    else:
        xs = np.linspace(0, T - 1, slots)
        Ms = np.stack([np.interp(xs, np.arange(T), M[:, c]) for c in range(res)],
                      axis=1)
    terms = vtl_terms(res)                       # the agent's composed VTL Term-trees
    out = []
    for sl in range(slots):
        tok = sub.add_node("Token",
                           {f"band{res}_{i}": float(Ms[sl, i]) for i in range(res)})
        for t in terms:                          # F1,F2,F3 invariant, evaluated native
            out.append(float(sub.evaluate(_Pred(t), {"s": tok})))
    v = np.array(out, dtype=np.float64)
    return v / (np.linalg.norm(v) + 1e-9)        # unit-norm, matched to the probe


def purity(labels, truth):
    hit = 0
    for cl in set(labels):
        members = [truth[i] for i, l in enumerate(labels) if l == cl]
        if members:
            hit += max(Counter(members).values())
    return hit / len(truth)


def random_floor(truth, k, trials=20, seed=0):
    rng = np.random.default_rng(seed)
    return float(np.mean([purity(list(rng.integers(0, k, len(truth))), truth)
                          for _ in range(trials)]))


def main():
    print("=" * 76)
    print("INVARIANT FRONT-END probe — the agent FIXES ITS OWN FRONT-END, then")
    print("re-runs its OWN mode-seeking clustering (the downstream capability validates)")
    print("=" * 76)
    print("DESIGN (composed from the agent's own prior work, by analogy):")
    print("  sharp 2nd-ear log-freq bands (two_ears) -> order-N ArgMax peak = formant")
    print("  -> VTL-invariant F_i - mean(F1,F2,F3) (speaker_norm) -> LOW-dim rep")
    print(f"  rep = {SLOTS} time-slots x 3 VTL-invariant formants = {SLOTS*3} dims "
          f"(vs 96-dim CMVN)\n")

    af = fl.gather_files()
    speakers = sorted({sp for _, _, sp, _ in af})
    print(f"corpus: FSDD, {len(speakers)} speakers pooled {speakers}")
    print(f"        {PER} utts/(digit,speaker), {len(DIGITS)} digits\n")

    sub = Substrate()
    sigs, truth, who = [], [], []
    for d in range(len(DIGITS)):
        for sp in speakers:
            files = [p for (p, dd, ss, _) in af if dd == d and ss == sp][:PER]
            for p in files:
                sm, fs = fl.load_wav(p)
                sigs.append(invariant_signature(sm, fs, sub))
                truth.append(d)
                who.append(sp)
    M = np.array(sigs)
    truth = list(truth)
    k_true = len(DIGITS)
    print(f"pooled {len(truth)} tokens (LABEL-FREE; true #categories = {k_true})\n")

    rf = random_floor(truth, k_true)
    print("BEFORE (96-dim CMVN front-end, last turn): purity 0.193, 49 modes "
          "(true 10)\n")
    print(f"random-assignment purity floor = {rf:.3f}  (chance ~ {1/k_true:.3f})\n")

    # --- AFTER: the agent's OWN mode-seeker on the new invariant low-dim rep ----
    labels, n_modes = cluster_by_modes(M, seed=0)
    pur = purity(labels, truth)
    print(f"{'AFTER (invariant low-dim)':<28} emergent #modes = {n_modes:<4} "
          f"(true {k_true})   purity = {pur:.3f}")

    # --- SHUFFLE control (same breath): destroy joint modes, keep marginals ----
    rng = np.random.default_rng(0)
    Msh = M.copy()
    for c in range(Msh.shape[1]):
        Msh[:, c] = Msh[rng.permutation(Msh.shape[0]), c]
    sh_labels, sh_modes = cluster_by_modes(Msh, seed=0)
    sh_pur = purity(sh_labels, truth)
    print(f"{'SHUFFLED (marginals kept)':<28} emergent #modes = {sh_modes:<4} "
          f"           purity = {sh_pur:.3f}")

    # --- SPEAKER-INVARIANCE control (same breath): cluster by WORD, not SPEAKER? --
    # Score the SAME clustering against the SPEAKER labels. If the rep is speaker-
    # invariant, the clusters do NOT track speaker -> speaker-purity stays LOW
    # (near its own random floor). Compared to the word-purity above.
    sp_truth = who
    n_sp = len(set(sp_truth))
    sp_pur = purity(labels, sp_truth)
    sp_floor = random_floor(sp_truth, n_modes if n_modes > 1 else n_sp)
    print(f"\nSPEAKER-INVARIANCE (same clusters, scored vs SPEAKER labels):")
    print(f"  speaker-purity = {sp_pur:.3f}  (speaker floor {sp_floor:.3f}, "
          f"{n_sp} speakers)  -> {'invariant (does NOT track speaker)' if sp_pur < sp_floor + 0.08 else 'tracks speaker'}")

    print("\n" + "=" * 76)
    print("VERDICT (the agent's controls)  BEFORE 0.193 / 49 modes  ->  AFTER")
    print("=" * 76)
    count_ok = 1 < n_modes <= 4 * k_true
    beats_floor = pur > rf + 0.03
    collapses = sh_pur < pur - 0.03
    rose = pur > 0.193 + 0.02
    print(f"  purity     : 0.193 -> {pur:.3f}   ({'ROSE' if rose else 'flat/■'})   "
          f"k-means told-k ref = 0.403")
    print(f"  #modes     : 49    -> {n_modes:<4} (true {k_true})   "
          f"-> {'toward 10' if count_ok and abs(n_modes-k_true) < abs(49-k_true) else 'off'}")
    print(f"  beats floor: {pur:.3f} vs {rf:.3f}  -> {'YES' if beats_floor else 'no'}")
    print(f"  SHUFFLE    : {pur:.3f} -> {sh_pur:.3f}  "
          f"-> {'COLLAPSES (structure in the joint)' if collapses else 'no collapse'}")
    print(f"  SPEAKER-INV: speaker-purity {sp_pur:.3f} vs floor {sp_floor:.3f}  "
          f"-> {'invariant' if sp_pur < sp_floor + 0.08 else 'tracks speaker'}")
    broke = rose and beats_floor and collapses
    print()
    if broke:
        print("  >>> The FRONT-END WAS THE BOUND: the agent's sharper-multi-ear +")
        print("      VTL-invariant low-dim rep RAISES purity with the controls holding.")
    else:
        print("  >>> STILL BOUNDED: the invariant low-dim rep does not break 0.193 here.")
        print("      The agent's deeper named lever is ANALYSIS-BY-SYNTHESIS (order-N:")
        print("      perceive by inverting the forward model). Report the real numbers.")


if __name__ == "__main__":
    main()

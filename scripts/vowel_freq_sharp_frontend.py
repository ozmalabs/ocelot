"""vowel_freq_sharp_frontend — the NAMED FIX for the moved limiter (commit b2886dc7).

THE LIMITER. solve_for_n_vowel (b2886dc7) replaced the F2-blurring mel-L2 match with an
F2-resolving formant-frame weighted-admissibility match and drove AbS vowel recognition
38.9% -> 51.3% cross-speaker (chance 20%, 1-NN 65.1%). The match-space limiter was fixed;
the limiter MOVED DOWN one rung to the INPUT FORMANT ESTIMATE: the order-10 LPC estimator
at 8 kHz CANNOT resolve the closely-spaced HIGH formants of the high vowels iy/uw near the
4 kHz Nyquist (measured: iy F2 ~1691 vs true 2290; uw F2 drifts UP to ~1557 from pole-
merging vs true 870). The residual recognition errors are all high vowels.

THE FIX (this file). A FREQUENCY-SHARP front-end (the session's earlier "freq-sharp second
ear" insight, memory: ozma_wall_is_self_imposed; reuses the two_ears_demo.py 4096-pt-FFT
sharp ear and sharp_formant_test.py framed-FFT idea). It REPLACES ONLY the input formant
estimation. Everything else is REUSED UNCHANGED from scripts.solve_for_n_vowel:
    * the forward model (VowelSourceFilterModel),
    * the formant-frame weighted-admissibility match (formant_admissibility / relative_
      formants / abs_recognise_formant),
    * the data harness (load_vowel_dataset / _extract_vowel_nucleus),
    * the LOSO cross-speaker split (held-out speaker NEVER banked).
ONLY estimate_formants is swapped, by passing a different estimator into a thin re-impl of
the recognition loop that is byte-identical to the original except for the estimator call.

METHOD (stated): a TWO-EARS FUSION (option c).
    * F1 ear  = the existing all-pole LPC pole (order 12) — LPC estimates the low first
      formant ROBUSTLY (it is well below Nyquist, well separated); kept as-is.
    * F2/F3 ear = a FREQUENCY-SHARP high-resolution FFT (8192-pt, ~1 Hz grid) with
      pre-emphasis (flatten glottal tilt) + light 7-bin smoothing (merge pitch harmonics
      inside a formant lobe), picking the strongest LOCAL MAXIMUM in the F2 band
      (900-2600 Hz) and the F3 band (2400-3800 Hz). The sharp FFT RESOLVES the high
      formant peaks the LPC poles merged. The two ears are fused into one (F1,F2,F3)
      frame, exactly the 3-vector the unchanged formant-frame match consumes.

DONKEY AUDIT. Front-end = owned numpy DSP (FFT + LPC roots), NO net, NO .fit(), NO
gradient descent. Match + forward model UNCHANGED (imported, verify by diff). Held-out
speaker never banked. CortexLoop / flat solve_for_n.py untouched.

Run:  python -m scripts.vowel_freq_sharp_frontend           (full)
      python -m scripts.vowel_freq_sharp_frontend --quick    (smoke)
"""
from __future__ import annotations

import sys
import time
import math
import numpy as np

# REUSE — forward model, match, harness, LOSO — all UNCHANGED from the b2886dc7 baseline.
from scripts.solve_for_n_vowel import (
    FS,
    VOWEL_FORMANTS,
    load_vowel_dataset,
    VowelSourceFilterModel,
    lpc_coeffs,
    relative_formants,
    relative_envelope,
    formant_admissibility,
    nn_recognise,
    estimate_formants as lpc10_estimate_formants,   # the OLD limiter, for the baseline col
)


# ===========================================================================
# THE FREQ-SHARP FRONT-END (owned DSP — the ONLY thing that changes).
# ===========================================================================

def _sharp_spectrum(sig, nfft=8192):
    """Frequency-SHARP high-resolution magnitude spectrum. Pre-emphasis flattens the
    -6 dB/oct glottal tilt (else the tilt buries the high formants); an 8192-pt FFT gives
    a ~1 Hz grid that RESOLVES the closely-spaced high formants the LPC poles merge."""
    x = sig - np.mean(sig)
    x = np.append(x[0], x[1:] - 0.97 * x[:-1])      # pre-emphasis
    x = x * np.hanning(len(x))
    mag = np.abs(np.fft.rfft(x, n=nfft))
    fr = np.fft.rfftfreq(nfft, d=1.0 / FS)
    mag = mag / (np.max(mag) + 1e-9)
    # light smoothing (~28 Hz) merges pitch harmonics WITHIN a formant lobe without
    # blurring across formants (formant spacing >> 28 Hz).
    k = np.ones(7) / 7.0
    mag = np.convolve(mag, k, mode="same")
    return fr, mag


def _band_local_max(fr, mag, lo, hi):
    """Strongest LOCAL maximum of the sharp spectrum in [lo,hi). A local max (not the
    global band argmax) tracks the formant peak rather than a band-edge skirt."""
    b = (fr >= lo) & (fr < hi)
    fb, sb = fr[b], mag[b]
    if len(sb) < 5:
        return None
    loc = [i for i in range(2, len(sb) - 2) if sb[i] >= sb[i - 1] and sb[i] >= sb[i + 1]]
    if not loc:
        return float(fb[int(np.argmax(sb))])
    i = max(loc, key=lambda i: sb[i])
    return float(fb[i])


def _lpc_f1(sig, order=12):
    """F1 ear: the lowest robust LPC pole (LPC nails the well-separated low F1). Owned DSP."""
    a = lpc_coeffs(sig, order)
    if a is None:
        return None
    roots = np.roots(a)
    roots = roots[np.imag(roots) > 1e-6]
    if len(roots) == 0:
        return None
    ang = np.angle(roots)
    freqs = ang * (FS / (2.0 * math.pi))
    bw = -0.5 * (FS / math.pi) * np.log(np.abs(roots) + 1e-12)
    keep = (freqs > 180.0) & (freqs < 1000.0) & (bw < 600.0)
    sel = np.sort(freqs[keep])
    if len(sel) == 0:
        return None
    return float(sel[0])


def estimate_formants_sharp(signal, fs=FS):
    """FREQ-SHARP two-ears formant estimate (F1,F2,F3). Replaces the order-10 LPC limiter.
    F1 from the robust LPC pole; F2/F3 from the frequency-sharp high-res FFT local maxima
    in their bands. Returns the same 3-tuple the unchanged formant-frame match consumes,
    or None (abstain) if a formant is unestimable. Owned DSP, NO net/fit."""
    fr, mag = _sharp_spectrum(signal)
    f1 = _lpc_f1(signal)
    if f1 is None:
        f1 = _band_local_max(fr, mag, 200.0, 900.0)
    f2 = _band_local_max(fr, mag, 900.0, 2600.0)
    f3 = _band_local_max(fr, mag, 2400.0, 3800.0)
    if f1 is None or f2 is None or f3 is None:
        return None
    # enforce ordering (a sharp F2 above the F3-band pick = swap; keeps the frame monotone)
    fs_ = sorted([f1, f2, f3])
    return (fs_[0], fs_[1], fs_[2])


# ===========================================================================
# RECOGNITION — byte-identical to abs_recognise_formant EXCEPT the estimator call.
# (The match — formant_admissibility / relative_formants — is imported UNCHANGED.)
# ===========================================================================

def abs_recognise_formant_with(estimator, target_sig, fm, candidate_vowels, scale_grid=None):
    """The unchanged formant-frame weighted-admissibility AbS solve, with the input
    formant estimator passed in. Mirrors solve_for_n_vowel.abs_recognise_formant
    line-for-line; ONLY `estimator(target_sig)` differs from `estimate_formants(...)`."""
    if scale_grid is None:
        scale_grid = np.linspace(0.75, 1.30, 12)            # SAME VTL search
    in_form = estimator(target_sig)
    if in_form is None:
        return None, -np.inf
    input_rel = relative_formants(in_form)                  # UNCHANGED match space
    best_v, best_adm = None, -np.inf
    for v in candidate_vowels:
        v_best = -np.inf
        for s in scale_grid:
            cand_formants = fm.formants_for({"vowel": v, "scale": float(s)})
            a = formant_admissibility(cand_formants, input_rel)   # UNCHANGED match
            if a > v_best:
                v_best = a
        if v_best > best_adm:
            best_adm, best_v = v_best, v
    return best_v, best_adm


# ===========================================================================
# (1) DIRECT — freq-sharp F2/F3 vs the order-10 LPC vs true Peterson-Barney.
# ===========================================================================

def test_direct(items):
    print("=" * 74)
    print("(1) DIRECT — input formant estimates vs true Peterson-Barney, by estimator")
    print("=" * 74)
    print(f"    {'vowel':>5} | {'true (F1,F2,F3)':>18} | {'LPC-10 (F1,F2,F3)':>20} | {'FREQ-SHARP (F1,F2,F3)':>23}")
    vowels = sorted(set(it["vowel"] for it in items))
    for v in vowels:
        sigs = [it["sig"] for it in items if it["vowel"] == v]
        L = np.array([f for f in (lpc10_estimate_formants(s) for s in sigs) if f])
        S = np.array([f for f in (estimate_formants_sharp(s) for s in sigs) if f])
        tru = VOWEL_FORMANTS[v]
        lm = (np.median(L[:, 0]), np.median(L[:, 1]), np.median(L[:, 2]))
        sm = (np.median(S[:, 0]), np.median(S[:, 1]), np.median(S[:, 2]))
        print(f"    {v:>5} | ({tru[0]:>4},{tru[1]:>4},{tru[2]:>4})    | "
              f"({lm[0]:>4.0f},{lm[1]:>4.0f},{lm[2]:>4.0f})       | "
              f"({sm[0]:>4.0f},{sm[1]:>4.0f},{sm[2]:>4.0f})")
    # the decisive high-vowel separation: iy vs uw F2.
    print("\n    high-vowel F2 separation (the limiter target) — Fisher ratio iy<->uw:")
    for est, name in ((lpc10_estimate_formants, "LPC-10"), (estimate_formants_sharp, "FREQ-SHARP")):
        iy = np.array([est(it["sig"])[1] for it in items if it["vowel"] == "iy" and est(it["sig"])])
        uw = np.array([est(it["sig"])[1] for it in items if it["vowel"] == "uw" and est(it["sig"])])
        fish = abs(np.mean(iy) - np.mean(uw)) / (np.std(iy) + np.std(uw) + 1e-9)
        print(f"      {name:>11}: iy F2={np.median(iy):>5.0f}  uw F2={np.median(uw):>5.0f}  "
              f"Fisher={fish:.2f}")


# ===========================================================================
# (2) RECOGNITION — same LOSO harness, freq-sharp vs LPC-10 vs 1-NN.
# ===========================================================================

def test_recognition(items, quick=False):
    print("\n" + "=" * 74)
    print("(2) RECOGNITION — AbS cross-speaker (LOSO), held-out speaker NEVER banked")
    print("=" * 74)
    fm = VowelSourceFilterModel()
    vowels = sorted(set(it["vowel"] for it in items))
    speakers = sorted(set(it["speaker"] for it in items))
    n_vowels = len(vowels)
    rng = np.random.default_rng(1)

    lpc_c = lpc_t = lpc_ab = 0
    shp_c = shp_t = shp_ab = 0
    nn_c = nn_t = 0
    conf_lpc = {v: {u: 0 for u in vowels} for v in vowels}
    conf_shp = {v: {u: 0 for u in vowels} for v in vowels}

    for held in speakers:
        test_items = [it for it in items if it["speaker"] == held]
        bank_items = [it for it in items if it["speaker"] != held]    # held-out NEVER banked
        if quick and len(test_items) > 40:
            idx = rng.choice(len(test_items), 40, replace=False)
            test_items = [test_items[i] for i in idx]
        bank = [(it["vowel"], relative_envelope(it["sig"])) for it in bank_items]
        for it in test_items:
            # LPC-10 baseline (the moved-limiter estimator) through the SAME match
            lp, _ = abs_recognise_formant_with(lpc10_estimate_formants, it["sig"], fm, vowels)
            lpc_t += 1
            if lp is None:
                lpc_ab += 1
            else:
                if lp == it["vowel"]:
                    lpc_c += 1
                conf_lpc[it["vowel"]][lp] += 1
            # FREQ-SHARP front-end (THE FIX) through the SAME match
            sp, _ = abs_recognise_formant_with(estimate_formants_sharp, it["sig"], fm, vowels)
            shp_t += 1
            if sp is None:
                shp_ab += 1
            else:
                if sp == it["vowel"]:
                    shp_c += 1
                conf_shp[it["vowel"]][sp] += 1
            # 1-NN exemplar baseline
            tenv = relative_envelope(it["sig"])
            nn = nn_recognise(tenv, bank)
            nn_t += 1
            if nn == it["vowel"]:
                nn_c += 1

    lpc_acc = lpc_c / max(1, lpc_t)
    shp_acc = shp_c / max(1, shp_t)
    nn_acc = nn_c / max(1, nn_t)
    print(f"    n_vowels={n_vowels}  chance={100.0/n_vowels:.1f}%  n={shp_t}")
    print(f"    AbS LPC-10 front-end   (the moved limiter, b2886dc7) : {lpc_acc*100:.1f}%"
          f"   (abstain {lpc_ab})")
    print(f"    AbS FREQ-SHARP front-end (THE FIX)                   : {shp_acc*100:.1f}%"
          f"   (abstain {shp_ab})")
    print(f"    1-NN exemplar baseline (banked)                     : {nn_acc*100:.1f}%")

    print(f"\n    LPC-10 front-end confusion (row=true, col=pred):")
    print("        " + " ".join(f"{u:>5}" for u in vowels))
    for v in vowels:
        print(f"    {v:>4}: " + " ".join(f"{conf_lpc[v][u]:>5}" for u in vowels))
    print(f"\n    FREQ-SHARP front-end confusion (row=true, col=pred) [THE FIX]:")
    print("        " + " ".join(f"{u:>5}" for u in vowels))
    for v in vowels:
        print(f"    {v:>4}: " + " ".join(f"{conf_shp[v][u]:>5}" for u in vowels))

    return {"lpc_acc": lpc_acc, "shp_acc": shp_acc, "nn_acc": nn_acc, "n": shp_t,
            "chance": 1.0 / n_vowels, "conf_shp": conf_shp, "conf_lpc": conf_lpc,
            "vowels": vowels}


def main():
    quick = "--quick" in sys.argv
    t0 = time.time()
    print("=" * 74)
    print("vowel_freq_sharp_frontend — the freq-sharp INPUT FORMANT ESTIMATOR (the named")
    print("fix for the moved limiter, b2886dc7). Forward model + match + harness UNCHANGED.")
    print("=" * 74)
    mppps = 8 if quick else None
    items = load_vowel_dataset(max_per_class_per_speaker=mppps)
    vowels = sorted(set(it["vowel"] for it in items))
    speakers = sorted(set(it["speaker"] for it in items))
    print(f"\n    {len(items)} vowel nuclei | vowels={vowels} | {len(speakers)} speakers")

    test_direct(items)
    res = test_recognition(items, quick=quick)

    print("\n" + "=" * 74)
    print("VERDICT")
    print("=" * 74)
    beats_lpc = res["shp_acc"] > res["lpc_acc"]
    above_chance = res["shp_acc"] > res["chance"]
    beats_nn = res["shp_acc"] >= res["nn_acc"]
    print(f"  freq-sharp above chance      : {'YES' if above_chance else 'NO'} "
          f"({res['shp_acc']*100:.1f}% vs {res['chance']*100:.1f}%)")
    print(f"  freq-sharp beats LPC-10      : {'YES' if beats_lpc else 'NO'} "
          f"({res['shp_acc']*100:.1f}% vs {res['lpc_acc']*100:.1f}%)")
    print(f"  freq-sharp matches/beats 1-NN: {'YES' if beats_nn else 'NO'} "
          f"({res['shp_acc']*100:.1f}% vs {res['nn_acc']*100:.1f}%)")
    print(f"\nelapsed {time.time()-t0:.1f}s")
    print("VOWEL_FREQ_SHARP_FRONTEND_COMPLETED")


if __name__ == "__main__":
    main()

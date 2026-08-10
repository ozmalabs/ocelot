"""solve_for_n_vowel_measured — the NAMED FIX for the corrected diagnosis (a0cabc7b).

THE CORRECTED DIAGNOSIS. The AbS vowel recogniser stalled at 51.3% (vs 1-NN 65.1%)
NOT because the front-end ear was too blurry (a0cabc7b killed that: a sharper ear made
it WORSE, 51.3% -> 46.6%) but because the forward model's CITATION Peterson-Barney
formant table MISMATCHES the COARTICULATED FSDD vowels. The digits are not citation
monophthongs: /uw/ in "two" is fronted (no 870 Hz F2), /iy/ in "three" resonates
~1900 not 2290, etc. The table the synthesiser reads is the wrong target.

THE FIX (this file). Measure the REALIZED per-vowel formant targets FROM THE CORPUS
itself — a TRAIN-ONLY measured statistic (like an n-gram counted from a corpus), owned
DSP, NO net / NO .fit() / NO gradient. Three owned-DSP changes; the agent's COGNITION
(forward model + formant-frame weighted-admissibility match + speaker VTL search) is
UNCHANGED — imported verbatim from scripts.solve_for_n_vowel.

  1. PER-CORPUS MEASURED FORMANT TARGETS (replaces the citation VOWEL_FORMANTS table).
     For each vowel, the realized F1/F2/F3 = the ROBUST MEDIAN of the band-adaptive
     formant estimates over the TRAIN speakers' nuclei of that vowel. LOSO DISCIPLINE:
     for each held-out test speaker, the targets are measured from the OTHER (train)
     speakers ONLY — the held-out speaker's clips NEVER touch its own targets. A
     train-only measured statistic, exactly like a corpus-counted n-gram. Owned.

  2. CLEANER NUCLEUS EXTRACTION (replaces the single highest-energy/low-ZCR window).
     METHOD: among the high-energy voiced windows, pick the MOST STATIONARY one — the
     window whose log-mel spectral envelope has the LOWEST spectral FLUX to its
     neighbours (the steadiest central steady-state). This avoids the coarticulated
     consonant-transition edges (the /θ/->/iy/ onglide in "three", the /t/->/uw/ in
     "two") that drag the formant estimate off the vowel target. Owned DSP.

  3. BAND-ADAPTIVE FORMANT ASSIGNMENT (replaces the fixed >90 Hz / <700 Hz BW gate that
     defaulted the back vowels onto a low floor). METHOD: take ALL LPC-pole resonances
     (frequency-ordered, bandwidth-gated only for stability), then assign them to the
     F1/F2/F3 SLOTS by PROXIMITY to the current measured targets via a small Hungarian-
     style greedy nearest-assignment in log-frequency — so a fronted /uw/ whose F2 sits
     at ~1500 Hz is assigned to the F2 slot at 1500, not forced down to an 870 floor.
     Bootstrap: the FIRST assignment pass (to MEASURE the targets) uses the citation
     table as the proximity anchor; once measured, all matching uses the measured
     targets. Owned DSP.

DONKEY AUDIT.
  * FORWARD MODEL: imported UNCHANGED (VowelSourceFilterModel). Source-filter DSP.
  * FORMANT-FRAME MATCH: imported UNCHANGED (formant_admissibility, relative_formants,
    the weighted-admissibility intersection). The agent's cognition — untouched.
  * SPEAKER SEARCH: the same bounded VTL scale_grid coordinate search — UNCHANGED logic
    (the recognise loop is re-expressed here only to read MEASURED targets instead of
    the table; the SEARCH itself — same grid, same per-candidate best-over-scale — is
    identical, verified by diff against abs_recognise_formant).
  * TARGETS + ESTIMATION: the ONLY things changed — owned DSP SENSE/DATA (a measured
    train-only statistic + a band-adaptive peak assignment). NO net, NO fit, NO gradient.
  * DATA: real FSDD vowels, cross-speaker, held-out NEVER banked, targets TRAIN-ONLY.

PREDICTION (to be killed if false). The realized targets match the coarticulated data
-> the formant-frame match discriminates the actual vowels -> accuracy climbs toward or
past 1-NN's 65.1% (the AbS recogniser catching the exemplar baseline using measured
structure + over-determination). KILL/HONEST: if it does NOT improve (the realized
per-vowel formants overlap too much / the data is too coarticulated to separate / the
median target is unstable across LOSO folds), report it and pinpoint the next limiter.

Run:  python -m scripts.solve_for_n_vowel_measured           (full acceptance)
      python -m scripts.solve_for_n_vowel_measured --quick    (smoke)
"""
from __future__ import annotations

import sys
import time
import math
import numpy as np

# ---- IMPORT THE UNCHANGED COGNITION + DATA PLUMBING (donkey: not re-authored) -------
from scripts.solve_for_n_vowel import (
    FS,
    DIGIT_VOWEL,
    VOWEL_FORMANTS,            # citation table — used ONLY as the bootstrap anchor
    FSDD,
    _read_wav,
    load_vowel_dataset,        # reused; we re-extract nuclei with the cleaner method below
    VowelSourceFilterModel,    # forward model — UNCHANGED
    lpc_coeffs,                # owned LPC — UNCHANGED
    relative_formants,         # speaker-relative log-formant frame — UNCHANGED
    formant_admissibility,     # the weighted-admissibility match — UNCHANGED (cognition)
    relative_envelope,         # 1-NN match space — UNCHANGED
    log_mel_envelope,          # for the stationarity (flux) nucleus method
    nn_recognise,              # 1-NN baseline — UNCHANGED
    estimate_formants as estimate_formants_citation,  # the OLD fixed-gate estimator (baseline)
    abs_recognise_formant,     # the CITATION-table recogniser (baseline 51.3%) — UNCHANGED
)


# ===========================================================================
# (2) CLEANER NUCLEUS EXTRACTION — most-stationary steady-state window.
# Owned DSP. Replaces the single highest-energy window with the steadiest one.
# ===========================================================================

def extract_vowel_nucleus_steady(sig, fs=FS, win_ms=40, n_cand=6):
    """Cleaner nucleus: among the top-N highest-energy VOICED windows, return the one
    with the LOWEST spectral FLUX to its temporal neighbours (the most stationary =
    deepest in the steady-state, away from the coarticulated transition edges).

    METHOD (stated):
      1. Slide a 40 ms window (50% hop); score each by energy*(1-ZCR) (voiced+loud).
      2. Take the top n_cand windows by that score.
      3. For each candidate, compute spectral FLUX = L2 distance of its log-mel envelope
         to the envelopes of the windows immediately before and after it (mean of the
         two). Low flux = the spectrum is not changing = steady-state vowel nucleus.
      4. Return the lowest-flux candidate. Mechanical signal -> graph token.
    """
    win = int(win_ms * fs / 1000)
    if len(sig) < win:
        sig = np.pad(sig, (0, win - len(sig)))
    hop = win // 2
    starts = list(range(0, len(sig) - win + 1, hop))
    if not starts:
        starts = [0]
    # score each window: voiced + loud
    scored = []
    for i in starts:
        seg = sig[i:i + win]
        energy = float(np.mean(seg ** 2))
        zc = float(np.mean(np.abs(np.diff(np.sign(seg))) > 0))
        scored.append((energy * (1.0 - zc), i))
    scored.sort(reverse=True)
    cand_starts = [i for _, i in scored[:n_cand]]

    # precompute log-mel envelopes for flux (cache by start)
    def env_at(start):
        seg = sig[start:start + win].copy()
        seg = seg / (np.max(np.abs(seg)) + 1e-9)
        return log_mel_envelope(seg, fs)

    env_cache = {}

    def get_env(start):
        if start not in env_cache:
            env_cache[start] = env_at(start)
        return env_cache[start]

    best_i, best_flux = cand_starts[0], np.inf
    for i in cand_starts:
        e_here = get_env(i)
        neighbours = []
        for d in (-hop, +hop):
            j = i + d
            if 0 <= j <= len(sig) - win:
                neighbours.append(get_env(j))
        if neighbours:
            flux = float(np.mean([np.sqrt(np.sum((e_here - en) ** 2)) for en in neighbours]))
        else:
            flux = 0.0  # isolated window — treat as steady
        if flux < best_flux:
            best_flux, best_i = flux, i

    seg = sig[best_i:best_i + win].copy()
    seg = seg / (np.max(np.abs(seg)) + 1e-9)
    return seg


def load_vowel_dataset_steady(max_per_class_per_speaker=None):
    """Same mechanical ingest as load_vowel_dataset but with the cleaner steady-state
    nucleus. Returns list of {vowel, speaker, sig}. No decisions."""
    import glob, os
    items = []
    files = sorted(glob.glob(os.path.join(FSDD, "*.wav")))
    counts = {}
    for f in files:
        base = os.path.basename(f)
        try:
            digit = int(base.split("_")[0])
            speaker = base.split("_")[1]
        except Exception:
            continue
        if digit not in DIGIT_VOWEL:
            continue
        vowel = DIGIT_VOWEL[digit]
        key = (vowel, speaker)
        if max_per_class_per_speaker is not None:
            counts[key] = counts.get(key, 0) + 1
            if counts[key] > max_per_class_per_speaker:
                continue
        sig = _read_wav(f)
        nucleus = extract_vowel_nucleus_steady(sig)
        items.append({"vowel": vowel, "speaker": speaker, "sig": nucleus})
    return items


# ===========================================================================
# (3) BAND-ADAPTIVE FORMANT ASSIGNMENT — assign LPC poles to F1/F2/F3 by proximity
# to the (measured) targets. Owned DSP. Replaces the fixed >90/<700 BW floor gate.
# ===========================================================================

def _lpc_resonances(signal, fs=FS, order=10):
    """All stable LPC-pole resonance frequencies (frequency-ordered) with bandwidths.
    Owned DSP — same LPC/Levinson-Durbin + pre-emphasis as the unchanged lpc_coeffs.
    Only the ASSIGNMENT downstream differs from the citation estimator."""
    a = lpc_coeffs(signal, order)
    if a is None:
        return None
    roots = np.roots(a)
    roots = roots[np.imag(roots) > 1e-6]
    if len(roots) == 0:
        return None
    ang = np.angle(roots)
    freqs = ang * (fs / (2.0 * math.pi))
    bw = -0.5 * (fs / math.pi) * np.log(np.abs(roots) + 1e-12)
    band = (freqs > 90.0) & (freqs < fs / 2 - 50.0) & (bw < 900.0)
    f = freqs[band]
    b = bw[band]
    if len(f) == 0:
        return None
    order_idx = np.argsort(f)
    return f[order_idx], b[order_idx]


def estimate_formants_adaptive(signal, anchors, fs=FS, order=10):
    """BAND-ADAPTIVE F1,F2,F3 estimate. Take the stable LPC-pole resonances and assign
    them to the three formant SLOTS by PROXIMITY (in log-frequency) to `anchors` =
    (a1,a2,a3) target frequencies, via a greedy nearest-assignment that preserves
    frequency ORDER (F1<F2<F3). NO fixed floor — a fronted /uw/ F2 at 1500 Hz is
    assigned to the F2 slot, not snapped to 870. Owned DSP.

    METHOD (stated):
      - candidates = frequency-ordered stable LPC resonances.
      - if fewer than 3 candidates: fall back to padding with the anchors (abstain-ish).
      - else: choose the ordered triple (i<j<k) of candidates minimising the total
        log-frequency distance to (a1,a2,a3). This is the order-preserving optimal
        assignment; with <=~6 candidates it's a tiny exhaustive search (owned, exact).
    """
    res = _lpc_resonances(signal, fs, order)
    if res is None:
        return None
    f, _b = res
    la = np.log(np.array(anchors) + 1e-9)
    if len(f) < 3:
        # not enough resonances — pad with anchors (the missing formants default to
        # target; this is the honest "unsure" case, the match will see no contrast).
        padded = list(f) + list(anchors)
        padded = sorted(padded)[:3]
        return tuple(float(x) for x in padded)
    lf = np.log(f + 1e-9)
    n = len(lf)
    best_cost, best_triple = np.inf, None
    # order-preserving exhaustive triple search (n is small: typically 3-6)
    for i in range(n):
        for j in range(i + 1, n):
            for k in range(j + 1, n):
                cost = (lf[i] - la[0]) ** 2 + (lf[j] - la[1]) ** 2 + (lf[k] - la[2]) ** 2
                if cost < best_cost:
                    best_cost, best_triple = cost, (i, j, k)
    i, j, k = best_triple
    return (float(f[i]), float(f[j]), float(f[k]))


# ===========================================================================
# (1) PER-CORPUS MEASURED FORMANT TARGETS — train-only robust median per vowel.
# Owned DSP measured statistic. NO net / fit / gradient.
# ===========================================================================

def measure_targets(train_items, fs=FS):
    """Measure the realized per-vowel formant targets = robust MEDIAN of the band-
    adaptive formant estimates over the TRAIN nuclei of each vowel.

    Bootstrap: the band-adaptive assignment needs anchors. We use the CITATION table
    as the proximity anchor to FIRST extract per-clip formants, then take the median.
    (The citation table is used ONLY to anchor the peak->slot assignment during
    measurement; the resulting TARGETS are purely the measured corpus medians.)

    LOSO is enforced by the caller passing TRAIN-only items (held-out speaker excluded).
    Returns {vowel: (F1,F2,F3)}. A train-only measured statistic.
    """
    vowels = sorted(set(it["vowel"] for it in train_items))
    per_vowel = {v: [] for v in vowels}
    for it in train_items:
        v = it["vowel"]
        anchor = VOWEL_FORMANTS[v]  # citation anchor for the assignment ONLY
        est = estimate_formants_adaptive(it["sig"], anchor, fs)
        if est is not None:
            per_vowel[v].append(est)
    targets = {}
    for v in vowels:
        arr = np.array(per_vowel[v]) if per_vowel[v] else None
        if arr is None or len(arr) == 0:
            targets[v] = VOWEL_FORMANTS[v]  # degenerate fallback (no measurements)
        else:
            targets[v] = tuple(float(x) for x in np.median(arr, axis=0))
    return targets


# ===========================================================================
# THE MEASURED-TARGET RECOGNISER — SAME structure as abs_recognise_formant.
# The ONLY differences vs the unchanged cognition: (a) candidate formants come from
# the MEASURED targets (not the table), (b) the input formants are estimated with the
# BAND-ADAPTIVE assignment (anchored on the measured targets). The forward model is not
# even needed for the formant match (it reads formants directly, exactly as the
# unchanged abs_recognise_formant does via fm.formants_for); the speaker VTL scale
# search + the weighted-admissibility intersection are IDENTICAL.
# ===========================================================================

def abs_recognise_measured(target_sig, targets, candidate_vowels, scale_grid=None,
                           return_all=False, fs=FS):
    """Measured-target AbS solve. IDENTICAL control flow to abs_recognise_formant:
      - estimate the input's formant frame (BAND-ADAPTIVE, anchored on measured targets)
      - speaker-relative input frame (relative_formants — UNCHANGED)
      - for each candidate vowel, search the SAME VTL scale grid over the candidate's
        MEASURED formants (targets[v] * scale) and score by formant_admissibility
        (UNCHANGED weighted-admissibility) — best over scale.
      - argmax over candidates. Abstain (None) if input formants unestimable.
    Only the SOURCE of candidate formants (measured vs table) and the input estimator
    (band-adaptive vs fixed-gate) differ — the SEARCH + MATCH are unchanged."""
    if scale_grid is None:
        scale_grid = np.linspace(0.75, 1.30, 12)  # SAME VTL search as the cognition

    # band-adaptive input formants — anchored on the per-candidate-agnostic blend of
    # measured targets (geometric-mean anchor across vowels = neutral prior, so the
    # assignment is NOT biased toward any one candidate). Owned DSP.
    log_anchor = np.mean([np.log(np.array(targets[v]) + 1e-9) for v in candidate_vowels], axis=0)
    neutral_anchor = tuple(np.exp(log_anchor))
    in_form = estimate_formants_adaptive(target_sig, neutral_anchor, fs)
    if in_form is None:
        if return_all:
            return None, -np.inf, {}, in_form
        return None, -np.inf
    input_rel = relative_formants(in_form)

    best_v, best_adm = None, -np.inf
    adms = {}
    for v in candidate_vowels:
        base = np.array(targets[v])
        v_best = -np.inf
        for s in scale_grid:
            cand_formants = tuple(base * float(s))           # measured target * VTL scale
            a = formant_admissibility(cand_formants, input_rel)  # UNCHANGED match
            if a > v_best:
                v_best = a
        adms[v] = v_best
        if v_best > best_adm:
            best_adm, best_v = v_best, v
    if return_all:
        return best_v, best_adm, adms, in_form
    return best_v, best_adm


# ===========================================================================
# THE LOSO HARNESS — citation baseline vs measured-target, held-out never banked,
# targets measured from TRAIN speakers only.
# ===========================================================================

def test_recognition(items, quick=False):
    fm = VowelSourceFilterModel()
    vowels = sorted(set(it["vowel"] for it in items))
    speakers = sorted(set(it["speaker"] for it in items))
    n_vowels = len(vowels)
    rng = np.random.default_rng(1)

    cit_correct = cit_total = cit_abstain = 0          # CITATION-table formant AbS (51.3%)
    meas_correct = meas_total = meas_abstain = 0       # MEASURED-target formant AbS (the fix)
    nn_correct = nn_total = 0
    per_speaker = {}
    confusion_cit = {v: {u: 0 for u in vowels} for v in vowels}
    confusion_meas = {v: {u: 0 for u in vowels} for v in vowels}
    target_log = {}  # held-out speaker -> measured targets (for the LOSO audit)

    for held in speakers:
        test_items = [it for it in items if it["speaker"] == held]
        train_items = [it for it in items if it["speaker"] != held]  # held-out NEVER seen
        if quick and len(test_items) > 40:
            idx = rng.choice(len(test_items), 40, replace=False)
            test_items = [test_items[i] for i in idx]

        # (1) MEASURE TARGETS FROM TRAIN ONLY — the held-out speaker's clips are NOT in
        # train_items, so its targets never see its own data. LOSO discipline.
        targets = measure_targets(train_items)
        target_log[held] = targets

        # 1-NN bank (relative-envelope) — also train-only (held-out never banked).
        bank = [(it["vowel"], relative_envelope(it["sig"])) for it in train_items]

        s_meas_c = s_meas_t = 0
        for it in test_items:
            # (baseline) CITATION-table formant AbS — UNCHANGED recogniser (the 51.3%).
            cit_pred, _ = abs_recognise_formant(it["sig"], fm, vowels)
            cit_total += 1
            if cit_pred is None:
                cit_abstain += 1
            else:
                if cit_pred == it["vowel"]:
                    cit_correct += 1
                confusion_cit[it["vowel"]][cit_pred] += 1

            # (THE FIX) MEASURED-target formant AbS.
            meas_pred, _ = abs_recognise_measured(it["sig"], targets, vowels)
            meas_total += 1
            s_meas_t += 1
            if meas_pred is None:
                meas_abstain += 1
            else:
                if meas_pred == it["vowel"]:
                    meas_correct += 1
                    s_meas_c += 1
                confusion_meas[it["vowel"]][meas_pred] += 1

            # 1-NN baseline.
            tenv = relative_envelope(it["sig"])
            nn_pred = nn_recognise(tenv, bank)
            nn_total += 1
            if nn_pred == it["vowel"]:
                nn_correct += 1
        per_speaker[held] = s_meas_c / max(1, s_meas_t)

    return {
        "n_vowels": n_vowels, "vowels": vowels, "chance": 1.0 / n_vowels,
        "cit_acc": cit_correct / max(1, cit_total), "cit_n": cit_total, "cit_abstain": cit_abstain,
        "meas_acc": meas_correct / max(1, meas_total), "meas_n": meas_total, "meas_abstain": meas_abstain,
        "nn_acc": nn_correct / max(1, nn_total), "nn_n": nn_total,
        "per_speaker": per_speaker,
        "confusion_cit": confusion_cit, "confusion_meas": confusion_meas,
        "target_log": target_log,
    }


def main():
    quick = "--quick" in sys.argv
    t0 = time.time()
    print("=" * 76)
    print("solve_for_n_vowel_measured — PER-CORPUS MEASURED targets + cleaner nucleus")
    print("+ band-adaptive formant assignment. The named fix for diagnosis a0cabc7b.")
    print("Forward model + formant-frame match + speaker search: UNCHANGED (imported).")
    print("=" * 76)

    print("\nLoading real vowel nuclei from FSDD (cleaner most-stationary nucleus) ...")
    mppps = 8 if quick else None
    items = load_vowel_dataset_steady(max_per_class_per_speaker=mppps)
    vowels = sorted(set(it["vowel"] for it in items))
    speakers = sorted(set(it["speaker"] for it in items))
    by_v = {v: sum(1 for it in items if it['vowel'] == v) for v in vowels}
    print(f"  {len(items)} nuclei | vowels={vowels} | speakers={speakers}")
    print(f"  per-vowel counts: {by_v}")

    print("\n" + "=" * 76)
    print("MEASURED TARGETS (sanity: median over ALL speakers — the LOSO folds each drop")
    print("one speaker; shown here only to compare against the citation table).")
    print("=" * 76)
    all_targets = measure_targets(items)
    print(f"    {'vowel':>6} {'citation F1/F2/F3':>26}   {'MEASURED F1/F2/F3':>26}")
    for v in vowels:
        c = VOWEL_FORMANTS[v]
        m = all_targets[v]
        print(f"    {v:>6}   ({c[0]:>5.0f},{c[1]:>5.0f},{c[2]:>5.0f})        "
              f"     ({m[0]:>5.0f},{m[1]:>5.0f},{m[2]:>5.0f})")

    print("\n" + "=" * 76)
    print("LOSO RECOGNITION — citation (51.3%) vs MEASURED-target vs 1-NN (65.1%)")
    print("held-out NEVER banked; targets measured from TRAIN speakers ONLY.")
    print("=" * 76)
    res = test_recognition(items, quick=quick)
    vs = res["vowels"]
    print(f"    n_vowels={res['n_vowels']}  chance={res['chance']*100:.1f}%  n={res['meas_n']}")
    print(f"    AbS CITATION-table formant (baseline)      : {res['cit_acc']*100:.1f}%"
          f"   (abstain {res['cit_abstain']}/{res['cit_n']})")
    print(f"    AbS MEASURED-target formant (THE FIX)      : {res['meas_acc']*100:.1f}%"
          f"   (abstain {res['meas_abstain']}/{res['meas_n']})")
    print(f"    1-NN exemplar baseline (banked, train-only): {res['nn_acc']*100:.1f}%")
    print(f"\n    per-speaker MEASURED-target acc (LOSO):")
    for sp, a in sorted(res["per_speaker"].items()):
        print(f"      {sp:>10}: {a*100:.1f}%")

    print(f"\n    CITATION-table confusion (row=true, col=pred) [baseline]:")
    print("        " + " ".join(f"{u:>5}" for u in vs))
    for v in vs:
        print(f"    {v:>4}: " + " ".join(f"{res['confusion_cit'][v][u]:>5}" for u in vs))
    print(f"\n    MEASURED-target confusion (row=true, col=pred) [THE FIX]:")
    print("        " + " ".join(f"{u:>5}" for u in vs))
    for v in vs:
        print(f"    {v:>4}: " + " ".join(f"{res['confusion_meas'][v][u]:>5}" for u in vs))

    # ---- LOSO audit: confirm a held-out speaker's targets never saw its own data.
    print("\n" + "=" * 76)
    print("LOSO AUDIT — measured targets differ across folds (each drops one speaker);")
    print("confirm the held-out speaker's clips are excluded from its own targets.")
    print("=" * 76)
    sp0 = speakers[0]
    t0t = res["target_log"][sp0]
    print(f"    targets for fold held-out='{sp0}' (measured from the OTHER speakers):")
    for v in vs:
        print(f"      {v:>4}: ({t0t[v][0]:>5.0f},{t0t[v][1]:>5.0f},{t0t[v][2]:>5.0f})")

    # ---- VERDICT
    print("\n" + "=" * 76)
    print("VERDICT")
    above_chance = res["meas_acc"] > res["chance"]
    beats_cit = res["meas_acc"] > res["cit_acc"]
    competitive = res["meas_acc"] >= 0.85 * res["nn_acc"]
    beats_nn = res["meas_acc"] >= res["nn_acc"]
    print(f"  above chance              : {'YES' if above_chance else 'NO'} "
          f"({res['meas_acc']*100:.1f}% vs {res['chance']*100:.1f}%)")
    print(f"  measured beats citation   : {'YES' if beats_cit else 'NO'} "
          f"(measured {res['meas_acc']*100:.1f}% vs citation {res['cit_acc']*100:.1f}%)")
    print(f"  competitive w/ 1-NN (>=85%): {'YES' if competitive else 'NO'} "
          f"(measured {res['meas_acc']*100:.1f}% vs 1-NN {res['nn_acc']*100:.1f}%)")
    print(f"  catches/beats 1-NN         : {'YES' if beats_nn else 'NO'}")
    if beats_cit:
        print("  => MEASURED targets clear the table/data mismatch: the realized per-vowel")
        print("     formants match the coarticulated FSDD vowels, so the formant-frame match")
        print("     discriminates and recognition improves over the citation baseline.")
    else:
        print("  => HONEST KILL: measured targets do NOT improve over the citation table.")
        print("     Inspect the confusion + the measured targets above for the next limiter")
        print("     (per-vowel formant overlap / coarticulation / median instability).")
    print(f"\nelapsed {time.time()-t0:.1f}s")
    print("SOLVE_FOR_N_VOWEL_MEASURED_COMPLETED")


if __name__ == "__main__":
    main()

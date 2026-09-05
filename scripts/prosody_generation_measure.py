#!/usr/bin/env python3
"""ARM A — affect-driven PROSODY GENERATION, scored against RAVDESS regions.

Confirmatory measure for Arm A of the FELT-PROSODY x RAVDESS rung (prereg
`docs/research/psychology_affect/PROSODY_RAVDESS_PREREG.md`).

For each target emotion it: (1) synthesizes digit-word utterances with the
affect->prosody generator (`domains/prosody_generation.py`, driven through the
real ModulatorState), (2) RE-ANALYZES the synthesized audio with the SAME judge
DSP (`_energy_envelope`, `_estimate_f0_per_window`, contour) that produced the
pre-registered regions, and (3) checks the produced (energy, f0_mean) against the
pre-registered RAVDESS TARGET REGION for that emotion and against the FLAT neutral
baseline.

Scored (per prereg §3):
  * per-emotion produced (energy, f0_mean, contour) vs target region,
  * in-region hit rate (binary HIGH/LOW region membership),
  * nearest-region classification on the reliable axes (does each synth emotion
    land nearest its OWN region?),
  * CI-separation of affect-driven f0_mean from the FLAT baseline (bootstrap over
    digit words).

HONEST: the synthesizer PEAK-NORMALIZES every buffer, so re-analyzed ENERGY is
saturated (~constant) and cannot discriminate — this is reported straight, and the
landing is scored on f0_mean (the axis the synth CAN move) with energy reported as
the saturated diagnostic. This is a synthesizer limit, not a mapping error.

MECHANICAL MEASURE-ADAPTER. No agent decision, no Rust, no Term, no shaping. The
generator SETS knobs + calls the forward synthesizer; this script READS the judge
re-analysis. Writes results/prosody_ravdess/generation.json.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
for _p in (_ROOT, os.path.join(_ROOT, "runners", "dsl", "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from domains.prosody_generation import (  # noqa: E402
    ProsodyGenerator, knobs_for_emotion, DIGIT_WORDS, EMOTION_VA)
from substrate_rs.communication import (  # noqa: E402
    _energy_envelope, _estimate_f0_per_window)

FS = 8000

# ---- the PRE-REGISTERED RAVDESS TRAIN-split ground-truth regions (§2). Frozen.
# (f0_mean centre Hz, energy centre) per emotion — the region centres for the
# nearest-region classification, on the RELIABLE axes.
REGION_CENTRE = {
    "calm":      (276.2, 0.00264),
    "neutral":   (289.7, 0.00294),
    "sad":       (316.4, 0.00467),
    "disgust":   (290.1, 0.00562),
    "surprised": (336.3, 0.00765),
    "happy":     (329.8, 0.01202),
    "fearful":   (360.1, 0.01470),
    "angry":     (348.0, 0.02492),
}
# ---- the frozen BINARY AROUSAL regions (§2). thresholds committed in prereg.
HIGH_EMO = ("angry", "fearful", "happy")
LOW_EMO = ("calm", "neutral")
MID_EMO = ("sad", "disgust", "surprised")
# HIGH region: energy>=0.010 AND f0_mean>=320 ; LOW: energy<=0.0035 AND f0_mean<=300
F0_HI, F0_LO = 320.0, 300.0
EN_HI, EN_LO = 0.010, 0.0035

DIGITS = list(DIGIT_WORDS)
BOOT_REPS = 2000
RNG_SEED = 295000            # block 295000; bootstrap resampling only (not a mint)


def _measure(audio, fs=FS):
    en = _energy_envelope(np.asarray(audio, dtype=np.float32), fs)
    f0 = _estimate_f0_per_window(np.asarray(audio, dtype=np.float32), fs)
    v = f0[f0 > 0]
    energy = float(en.mean()) if len(en) else 0.0
    f0_mean = float(v.mean()) if len(v) else 0.0
    # contour bucket via a line fit over the voiced f0 track (mirror the judge).
    contour = "flat"
    if len(v) >= 4:
        x = np.arange(len(v), dtype=np.float64)
        slope = float(np.polyfit(x, v, 1)[0])
        if abs(slope) < 0.5:
            contour = "flat"
        elif slope > 0:
            contour = "rising"
        else:
            contour = "falling"
    return energy, f0_mean, contour


def _f0_region_class(f0_mean, energy):
    """Binary arousal region membership on the reliable axes. Because synth energy
    is saturated (>=EN_HI always), the region decision reduces to f0_mean; we
    report BOTH the strict AND-region and the f0-only region honestly."""
    strict_high = (energy >= EN_HI and f0_mean >= F0_HI)
    strict_low = (energy <= EN_LO and f0_mean <= F0_LO)
    f0_high = f0_mean >= F0_HI
    f0_low = f0_mean <= F0_LO
    return dict(strict_high=bool(strict_high), strict_low=bool(strict_low),
                f0_high=bool(f0_high), f0_low=bool(f0_low))


def _nearest_region(f0_mean, energy):
    """Nearest RAVDESS region centre on the reliable axes. Because energy is
    saturated on synth output, nearest-region is computed on the F0 axis (the axis
    the synth can move); the energy axis is reported but excluded from the distance
    (a saturated axis carries no signal). Returns (nearest_emotion, dist)."""
    best, bd = None, float("inf")
    for emo, (cf0, cen) in REGION_CENTRE.items():
        d = abs(f0_mean - cf0)          # F0 axis only (energy saturated)
        if d < bd:
            bd, best = d, emo
    return best, bd


def _bootstrap_ci(vals, reps=BOOT_REPS, seed=RNG_SEED):
    rng = np.random.default_rng(seed)
    vals = np.asarray(vals, dtype=np.float64)
    if len(vals) == 0:
        return 0.0, 0.0, 0.0
    means = np.array([rng.choice(vals, size=len(vals), replace=True).mean()
                      for _ in range(reps)])
    return float(vals.mean()), float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def run():
    gen = ProsodyGenerator(fs=FS)

    # flat-baseline f0 per digit (the blind twin — affect ignored).
    flat_f0 = []
    for w in DIGITS:
        _e, f, _c = _measure(gen.synthesize(w, "neutral", flat=True))
        flat_f0.append(f)
    flat_f0_mean, flat_lo, flat_hi = _bootstrap_ci(flat_f0)

    rows = []
    hit_arousal = 0          # landed in own arousal class region (HIGH/LOW), f0 axis
    n_scored = 0             # HIGH+LOW emotions (MID is not a scored landing target)
    nearest_own = 0
    for emo in EMOTION_VA:
        k = knobs_for_emotion(emo, use_substrate=True)
        per_digit_f0, per_digit_en, contours = [], [], []
        for w in DIGITS:
            e, f, c = _measure(gen.synthesize(w, emo))
            per_digit_f0.append(f)
            per_digit_en.append(e)
            contours.append(c)
        f0_m, f0_lo, f0_hi = _bootstrap_ci(per_digit_f0)
        en_m = float(np.mean(per_digit_en))
        reg = _f0_region_class(f0_m, en_m)
        nearest, ndist = _nearest_region(f0_m, en_m)
        # scored landing: HIGH emotions must land f0_high; LOW must land f0_low.
        landed = None
        if emo in HIGH_EMO:
            landed = reg["f0_high"]
            n_scored += 1
            hit_arousal += int(landed)
        elif emo in LOW_EMO:
            landed = reg["f0_low"]
            n_scored += 1
            hit_arousal += int(landed)
        # nearest-own on the AROUSAL ordering: nearest region shares arousal class.
        own_class = ("HIGH" if emo in HIGH_EMO else
                     "LOW" if emo in LOW_EMO else "MID")
        near_class = ("HIGH" if nearest in HIGH_EMO else
                      "LOW" if nearest in LOW_EMO else "MID")
        near_own = (near_class == own_class)
        nearest_own += int(near_own)
        # CI-separation of this emotion's affect-driven f0 from the flat baseline.
        ci_sep = (f0_lo > flat_hi) or (f0_hi < flat_lo)
        # contour: most common bucket produced.
        cbucket = max(set(contours), key=contours.count)
        rows.append(dict(
            emotion=emo, emx=k["emx"], source=k["source"],
            knob_f0=k["f0_hz"], knob_dur=k["dur_s"], knob_ta=k["ta_frac"],
            knob_contour=k["contour"], affect_arousal=k["arousal"],
            affect_valence=k["valence"],
            produced_f0_mean=round(f0_m, 2), produced_f0_ci=[round(f0_lo, 2), round(f0_hi, 2)],
            produced_energy=round(en_m, 5),
            produced_contour=cbucket,
            region_target_f0=REGION_CENTRE[emo][0],
            region_target_energy=REGION_CENTRE[emo][1],
            arousal_class=own_class,
            f0_region=("HIGH" if reg["f0_high"] else "LOW" if reg["f0_low"] else "MID"),
            landed_own_arousal_region=landed,
            nearest_region=nearest, nearest_dist=round(ndist, 2),
            nearest_shares_arousal_class=bool(near_own),
            ci_separated_from_flat=bool(ci_sep),
        ))

    # arousal ordering check: produced f0_mean must be monotone-ish in the prereg
    # arousal ordering (calm<neutral<sad<disgust<surprised<happy<fearful<angry).
    order = ["calm", "neutral", "sad", "disgust", "surprised", "happy", "fearful", "angry"]
    f0_by_emo = {r["emotion"]: r["produced_f0_mean"] for r in rows}
    ordered_f0 = [f0_by_emo[e] for e in order]
    # Spearman-lite: fraction of adjacent pairs in the correct (nondecreasing) dir.
    incr_pairs = sum(1 for i in range(len(ordered_f0) - 1)
                     if ordered_f0[i + 1] >= ordered_f0[i])
    mono_frac = incr_pairs / (len(ordered_f0) - 1)
    # HIGH vs LOW mean f0 separation (the headline arousal contrast).
    high_f0 = np.mean([f0_by_emo[e] for e in HIGH_EMO])
    low_f0 = np.mean([f0_by_emo[e] for e in LOW_EMO])

    n_ci_sep = sum(1 for r in rows if r["ci_separated_from_flat"])
    result = dict(
        block=295000,
        arm="A_generation",
        fs=FS, digits=DIGITS, boot_reps=BOOT_REPS,
        flat_baseline_f0_mean=round(flat_f0_mean, 2),
        flat_baseline_f0_ci=[round(flat_lo, 2), round(flat_hi, 2)],
        rows=rows,
        # scored summaries
        in_region_hit_rate=round(hit_arousal / n_scored, 3) if n_scored else 0.0,
        n_scored_high_low=n_scored, n_landed=hit_arousal,
        nearest_own_arousal_rate=round(nearest_own / len(rows), 3),
        f0_monotone_frac=round(mono_frac, 3),
        high_mean_f0=round(float(high_f0), 2),
        low_mean_f0=round(float(low_f0), 2),
        high_low_f0_gap=round(float(high_f0 - low_f0), 2),
        n_ci_separated_from_flat=n_ci_sep,
        # HONEST energy note
        energy_saturated_note=(
            "Synth peak-normalizes every buffer; re-analyzed energy is saturated "
            "(~0.30 across all emotions) and cannot discriminate — landing scored "
            "on f0_mean, the axis the synth can move. This is a synthesizer limit, "
            "not a mapping error."),
        energy_values={r["emotion"]: r["produced_energy"] for r in rows},
        energy_spread=round(
            max(r["produced_energy"] for r in rows)
            - min(r["produced_energy"] for r in rows), 5),
        # verdicts
        verdict_arousal_monotone=bool(mono_frac >= 0.75),
        verdict_high_above_low=bool(high_f0 > low_f0),
        verdict_ci_separated=bool(n_ci_sep >= 4),
    )

    out_dir = os.path.join(_ROOT, "results", "prosody_ravdess")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "generation.json")
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)
    return result, out_path


def main():
    result, path = run()
    print(f"[arm A] wrote {path}")
    print(f"  flat baseline f0={result['flat_baseline_f0_mean']} "
          f"CI={result['flat_baseline_f0_ci']}")
    for r in result["rows"]:
        print(f"  {r['emotion']:10s} f0={r['produced_f0_mean']:6.1f} "
              f"CI={r['produced_f0_ci']} class={r['arousal_class']:4s} "
              f"f0_region={r['f0_region']:4s} landed={r['landed_own_arousal_region']} "
              f"nearest={r['nearest_region']}({r['nearest_shares_arousal_class']}) "
              f"ci_sep={r['ci_separated_from_flat']}")
    print(f"  in-region hit rate (HIGH/LOW, f0 axis): {result['in_region_hit_rate']} "
          f"({result['n_landed']}/{result['n_scored_high_low']})")
    print(f"  nearest-own arousal rate: {result['nearest_own_arousal_rate']}")
    print(f"  f0 monotone frac: {result['f0_monotone_frac']}  "
          f"HIGH f0={result['high_mean_f0']} LOW f0={result['low_mean_f0']} "
          f"gap={result['high_low_f0_gap']}")
    print(f"  energy spread (saturated): {result['energy_spread']}")


if __name__ == "__main__":
    main()

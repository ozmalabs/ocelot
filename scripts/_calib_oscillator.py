"""One-time calibration probe for the relaxation-oscillator constants, on a
TRAIN-SIDE speaker probe (DISJOINT from the held-out test the continuous_machine
harness uses). This is calibration on train (the same legitimacy as
prosody_syllable._DIP_FRAC's one-time validation), NOT sweep-and-keep on the test
set. Reports unit-count error vs true digit count for a few integrate-and-fire
constant settings so a physically-sane, frozen setting can be chosen.
"""
import sys, os, random
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import domains.self_directed_speech_world as W
import domains.radio_telescope_frontend as RT
import domains.relaxation_oscillator as RO
import scripts.continuous_machine as CM

speakers = W.sc_speakers(CM.DIGITS); random.Random(0).shuffle(speakers)
# the harness holds out speakers[:n_held] (<=40); probe speakers far inside TRAIN.
probe_spk = speakers[60:75]

def carve(spk_list, n):
    out = {}
    for spk in spk_list:
        idx = W.sc_index_for([spk], CM.DIGITS); dp = {}
        for d, w in enumerate(CM.DIGITS):
            for p in idx.get(w, []):
                dp.setdefault(d, []).append(p)
        if len(dp) < 2:
            continue
        cl = {d: [W.load_sc_clip(p)[0] for p in paths[:n]] for d, paths in dp.items()}
        out[spk] = cl
    return out

probe = carve(probe_spk, 10)
print(f"probe speakers {len(probe)}", flush=True)
rng = random.Random(99)
strings = []
for spk, clips in probe.items():
    for _ in range(4):
        r, t = CM.make_runon(clips, rng, 3, 6)
        if r is not None:
            strings.append((r, t))
print(f"probe strings {len(strings)}", flush=True)
# precompute sharp onset per string (the Stage-1 drive) once.
onsets = [(RT.sharp_onset(r), len(t)) for r, t in strings]

def evalc(threshold, leak, pulse, refr):
    ratios = []; errs = []
    for o, tn in onsets:
        n = RO.count_from_onset(o, threshold=threshold, leak=leak,
                                pulse_frac=pulse, refractory_ms=refr)
        ratios.append(n / tn); errs.append(abs(n - tn))
    return float(np.mean(ratios)), float(np.mean(errs))

print("thr  leak  pulse refr  pred/true  mae", flush=True)
best = None
for thr in [0.7, 1.0]:
    for leak in [0.80, 0.86, 0.92]:
        for pulse in [0.35, 0.5, 0.7]:
            for refr in [100, 120]:
                ra, mae = evalc(thr, leak, pulse, refr)
                print(f"{thr:.2f} {leak:.2f} {pulse:.2f} {refr:4d}   "
                      f"{ra:.3f}     {mae:.3f}", flush=True)
                # objective: minimise mae, tie-break toward pred/true near 1.
                score = (mae, abs(ra - 1.0))
                if best is None or score < best[0]:
                    best = (score, (thr, leak, pulse, refr, ra, mae))
print(f"BEST thr={best[1][0]} leak={best[1][1]} pulse={best[1][2]} "
      f"refr={best[1][3]} -> pred/true {best[1][4]:.3f} mae {best[1][5]:.3f}",
      flush=True)
print("CALIB_DONE", flush=True)

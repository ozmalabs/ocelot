"""fuzzy_compare_smoothing — does a FUZZY (smoothed, multi-scale) compare fix BOTH
the toy hat at low resolution AND the audio hat's synthetic-vs-real domain gap?

The insight (Axiom 0): the compare has been a RIGID rule (exact match over the
feature grid) — but "rules are more like guidelines"; it should be FUZZY/smoothed.
UNIFICATION: low-res shape ALIASING (toy) and the audio DOMAIN GAP (synthetic-vs-real)
are the SAME nuisance — high-frequency detail the compare should ignore. An owned
multi-scale Gaussian blur (domains/fuzzy_smooth) over the feature grid removes both.
The CortexLoop is UNCHANGED — smoothing lives entirely in the hats' encode/compare.

  (a) TOY low-res: un-smoothed vs smoothed recognition at SMALL grids (where it fails)
      + a scale sweep. PREDICTION: smoothing restores low-res accuracy.
  (b) AUDIO cross-speaker LOSO: un-smoothed (0.42 plateau) vs smoothed + the
      true-word-vs-wrong-word residual SEPARATION + a scale sweep. PREDICTION:
      smoothing shrinks the domain gap -> separation up -> LOSO lifts above 0.42.
      KILL: if smoothing does not lift audio (gap is coarse) OR erases the word at
      every grain-removing scale, say so plainly.

Run: python -m scripts.fuzzy_compare_smoothing
"""
from __future__ import annotations

import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np

from substrate_rs import Substrate
import domains.self_directed_speech_world as W
from domains.cortex_loop import CortexLoop
from domains.toy_hat import ToyHat
from domains.audio_hat import AudioHat
from scripts.universal_loop_phaseAB import build_real_probe, fresh as audio_fresh, FS


# ===========================================================================
# (a) TOY HAT — low-res, un-smoothed vs smoothed, scale sweep
# ===========================================================================

def run_toy(grid_n, smooth_scales, render_blur=False, n_per_shape=8, k=5,
            max_synths=24, n_passes=3, seed=7):
    s = Substrate()
    hat = ToyHat(s, grid_n=grid_n, seed=seed, smooth_scales=smooth_scales,
                 render_blur=render_blur)
    loop = CortexLoop(hat, max_synths_per_content=max_synths, n_passes=n_passes, k=k)
    chance = 1.0 / len(hat.contents())
    test = hat.held_out_test(n_per_shape, seed=seed)
    cor = 0
    for (sh, raw) in test:
        pred, _per, _curves = loop.recognise(raw)
        cor += int(pred == sh)
    hat.close()
    return cor / max(len(test), 1), chance, len(test)


# scale sweep (sigma in grid cells). [0.0] = rigid; the rest are multi-scale pyramids
# coarse-to-fine, plus a deliberate over-smooth to show the erase failure mode.
_TOY_SWEEPS = {
    "rigid[0]": [0.0],
    "s0.6": [0.0, 0.6],
    "s1.0": [0.0, 1.0],
    "s1.5": [0.0, 1.5],
    "ms[0,1,2]": [0.0, 1.0, 2.0],
    "over[4]": [4.0],
}
_TOY_GRIDS = [8, 10, 12, 16, 28]


def _toy_regime(render_blur, label):
    print(f"\n  --- regime: {label} (render_blur={render_blur}) ---", flush=True)
    results = {}
    chance = None
    for g in _TOY_GRIDS:
        row = {}
        for name, scales in _TOY_SWEEPS.items():
            acc, chance, n = run_toy(g, scales, render_blur=render_blur)
            row[name] = acc
            print(f"  grid {g:>2}x{g:<2}  {name:<12} acc {acc:.3f}  "
                  f"(chance {chance:.3f}, {acc/chance:.1f}x, n={n})", flush=True)
        results[g] = row
        print("  " + "-" * 56, flush=True)
    return results, chance


def toy_suite():
    print("=" * 78, flush=True)
    print("(a) TOY HAT — low-res aliasing: rigid vs FUZZY compare + scale sweep",
          flush=True)
    print("=" * 78, flush=True)
    # RAW regime: rasterise 1-pixel strokes (true aliasing) -> the compare-time blur
    # is the ONLY smoothing, so this is the clean test of the fuzzy-compare thesis.
    raw_res, chance = _toy_regime(render_blur=False, label="RAW raster (aliasing)")
    # PRE-BLUR regime: the historical render-time box blur already pre-smooths the
    # front end, so the residual low-res failure is raster information loss, not
    # aliasing the compare can remove.
    blur_res, _ = _toy_regime(render_blur=True, label="render pre-blur (historical)")
    return {"raw": raw_res, "preblur": blur_res}, chance


# ===========================================================================
# (b) AUDIO HAT — LOSO + residual separation, un-smoothed vs smoothed, sweep
# ===========================================================================

def run_audio(probe, smooth_t, smooth_f, grid=60, k=3, max_synths=8,
              n_passes=2, seed=20240610):
    s, _pipe = audio_fresh()
    hat = AudioHat(s, fs=FS, grid=grid, seed=seed, smooth_t=smooth_t, smooth_f=smooth_f)
    loop = CortexLoop(hat, max_synths_per_content=max_synths, n_passes=n_passes, k=k)
    chance = 1.0 / len(hat.contents())
    pr = [(w, x, fs) for (w, x, fs) in probe if w in hat.contents()]
    cor = 0
    true_resids, wrong_resids = [], []
    for (w, x, fs) in pr:
        pred, per, _curves = loop.recognise((x, fs))
        cor += int(pred == w)
        if w in per:
            true_resids.append(per[w])
        wrong = [r for ww, r in per.items() if ww != w]
        if wrong:
            wrong_resids.append(min(wrong))
    hat.close()
    tr = np.asarray(true_resids); wr = np.asarray(wrong_resids)
    acc = cor / max(len(pr), 1)
    tmed = float(np.median(tr)) if tr.size else float("nan")
    wmed = float(np.median(wr)) if wr.size else float("nan")
    return acc, chance, len(pr), tmed, wmed


def audio_suite(n_held_spk=40, n_loso_per=8, seed=20240610):
    print("=" * 78, flush=True)
    print("(b) AUDIO HAT — cross-speaker LOSO + residual separation: rigid vs FUZZY",
          flush=True)
    print("=" * 78, flush=True)
    probe, _words = build_real_probe(n_held_spk, n_loso_per, seed)
    print(f"  held-out LOSO probe built ({len(probe)} REAL clips, never banked)",
          flush=True)
    # (smooth_t, smooth_f) sweep. (0,0) = rigid plateau. Freq-blur targets the
    # spectral domain grain; time-blur the alignment jitter; over-smooth = erase test.
    sweeps = {
        "rigid(0,0)":   (0.0, 0.0),
        "f0.8":         (0.0, 0.8),
        "f1.5":         (0.0, 1.5),
        "f2.5":         (0.0, 2.5),
        "t1.0_f1.5":    (1.0, 1.5),
        "t2.0_f2.5":    (2.0, 2.5),
        "over_f5":      (0.0, 5.0),
    }
    results = {}
    for name, (st, sf) in sweeps.items():
        t0 = time.time()
        acc, chance, n, tmed, wmed = run_audio(probe, st, sf)
        sep = wmed - tmed
        results[name] = {"acc": acc, "tmed": tmed, "wmed": wmed, "sep": sep, "n": n}
        print(f"  {name:<12} LOSO {acc:.3f} (chance {chance:.3f})  "
              f"true {tmed:.3f} vs wrong {wmed:.3f}  sep {sep:+.3f}  "
              f"({time.time()-t0:.0f}s, n={n})", flush=True)
    return results, chance


def main():
    t_start = time.time()
    print("#" * 78, flush=True)
    print("FUZZY (smoothed, multi-scale) COMPARE — toy low-res AND audio domain gap",
          flush=True)
    print("The CortexLoop is UNCHANGED; smoothing lives in the hats' encode/compare.",
          flush=True)
    print("#" * 78, flush=True)

    toy_res, toy_chance = toy_suite()

    audio_res = None
    audio_chance = None
    if W.sc_available():
        audio_res, audio_chance = audio_suite()
    else:
        print("\n[audio] Speech Commands not at /tmp/sc; SKIPPING audio suite.",
              flush=True)

    # ---- VERDICT ----
    print("\n" + "#" * 78, flush=True)
    print("VERDICT", flush=True)
    print("#" * 78, flush=True)

    # TOY: did smoothing restore low-res accuracy? Report BOTH regimes.
    def _best(row):
        bn = max((n for n in row if n != "over[4]"), key=lambda n: row[n])
        return bn, row[bn]

    print("(a) TOY low-res — RAW raster (true aliasing; smoothing is the ONLY smoothing):",
          flush=True)
    raw = toy_res["raw"]
    for g, row in raw.items():
        bn, best = _best(row)
        print(f"    grid {g:>2}: rigid {row['rigid[0]']:.3f} -> best {best:.3f} "
              f"({bn}, {best-row['rigid[0]']:+.3f})  over[4]={row['over[4]']:.3f}",
              flush=True)
    small = [g for g in raw if g <= 16]
    toy_fixed = all(_best(raw[g])[1] - raw[g]["rigid[0]"] > 0.03 for g in small) if small else False
    print(f"    => RAW low-res aliasing FIXED by smoothing: {toy_fixed} "
          f"(over[4] collapse = over-smooth erases the shape)", flush=True)

    print("(a) TOY low-res — render PRE-BLUR (historical front end already smooths):",
          flush=True)
    pb = toy_res["preblur"]
    for g, row in pb.items():
        bn, best = _best(row)
        print(f"    grid {g:>2}: rigid {row['rigid[0]']:.3f} -> best {best:.3f} "
              f"({bn}, {best-row['rigid[0]']:+.3f})", flush=True)
    print("    => with a pre-smoothed front end the residual low-res failure is RASTER "
          "INFORMATION LOSS (off-grid translations), not aliasing the compare removes.",
          flush=True)

    # AUDIO: did smoothing lift LOSO and the separation?
    if audio_res is not None:
        print("(b) AUDIO domain gap:", flush=True)
        rigid = audio_res["rigid(0,0)"]
        best_name = max(audio_res, key=lambda n: audio_res[n]["acc"])
        best = audio_res[best_name]
        sep_best_name = max(audio_res, key=lambda n: audio_res[n]["sep"])
        sep_best = audio_res[sep_best_name]
        print(f"    rigid(0,0): LOSO {rigid['acc']:.3f}  sep {rigid['sep']:+.3f}",
              flush=True)
        print(f"    best LOSO:  {best_name} LOSO {best['acc']:.3f} "
              f"(lift {best['acc']-rigid['acc']:+.3f})  sep {best['sep']:+.3f}",
              flush=True)
        print(f"    best sep:   {sep_best_name} sep {sep_best['sep']:+.3f} "
              f"(vs rigid {rigid['sep']:+.3f})  LOSO {sep_best['acc']:.3f}", flush=True)
        audio_lifted = best["acc"] - rigid["acc"] > 0.02
        sep_improved = sep_best["sep"] - rigid["sep"] > 0.0
        print(f"    => audio domain gap LIFTED by smoothing: {audio_lifted} "
              f"(LOSO lift); separation improved: {sep_improved}", flush=True)
        if not audio_lifted:
            print("    => HONEST KILL on audio: smoothing did NOT lift LOSO -> the "
                  "domain gap is COARSE (not pure high-freq), or every grain-removing "
                  "scale also erases the word. Report the curve above.", flush=True)
    else:
        print("(b) AUDIO: skipped (no /tmp/sc).", flush=True)

    print(f"\n[timing] total {time.time()-t_start:.0f}s", flush=True)
    print("[MARKER] FUZZY_COMPARE_SMOOTHING_COMPLETED", flush=True)


if __name__ == "__main__":
    main()

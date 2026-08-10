"""Acceptance test: the agent composes its OWN ear and we compare it, on its OWN
confused pairs, against the uniform 32-band layout.

Procedure:
  1. Run a develop pass (scripts.ask_agent._develop) that produces Confusions.
  2. The agent composes its ear (agent_specify_ear, res_out=16): a non-uniform
     band layout designed from its confusions by equal-information binning.
  3. For each top confused pair, compute the BEST-cue Fisher using:
       - the UNIFORM 32-band layout (the fft32 cue menu incl f2_formant), vs
       - the AGENT-COMPOSED 16-band ear (ear_peak / ear_tilt / ear_f2_peak).
SUCCESS CRITERIA (reported honestly):
  (a) the composed ear concentrates bands where informative — show boundaries /
      band widths in Hz; narrowest bands should fall in the formant region.
  (b) with FEWER bands (16 vs 32) the composed ear MATCHES OR BEATS the uniform
      best Fisher on the confused pairs.
  (c) two/three (the F2-vowel pair) is separated well by the composed ear.
"""
import os
import sys

sys.path.insert(0, os.getcwd())

import numpy as np

import scripts.fsdd_learner_world as fl
from scripts.ask_agent import _develop
from domains.acoustic_resolution import (enrich_sign_bands, enrich_sign_windows,
                                          enrich_sign_fft, fft_band_centre_hz)
from domains.hint_grounding import compose_from_spec, CUE_MENU
from domains.ear_composition import (agent_specify_ear, emit_ear_enrichment,
                                     compose_ear_cues, ear_band_edges_hz)

FFT_R = 32          # uniform fft layout resolution
RES_OUT = 16        # composed ear band count (FEWER than uniform)
SR = 8000.0
N_TOP_PAIRS = 6

UNIFORM_CUES = ["f1_formant", "f2_formant", "f2_minus_f1",
                "vowel_height", "onset_tilt", "ending_nasal",
                "onset_level", "ending_level", "movement"]


def _uniform_fft_cues():
    """Same cue FAMILIES the composed ear offers (peak / tilt / f2-peak), but read
    off the UNIFORM 32-band FFT layout (fft32_<j>). This makes the table
    layout-vs-layout on matched cues, not cue-family-vs-cue-family — the composed
    ear's only advantage should be WHERE its bands sit, not that it has a tilt cue
    the uniform side lacks."""
    def A(j):
        return {"type": "Attr", "node": {"type": "Var", "name": "s"},
                "key": f"fft{FFT_R}_{j}"}
    half = FFT_R // 2
    peak = {"type": "ArgMax", "items": [A(j) for j in range(FFT_R)]}
    high = {"type": "Plus", "items": [A(j) for j in range(half, FFT_R)]}
    low = {"type": "Plus", "items": [A(j) for j in range(half)]}
    tilt = {"type": "Minus", "a": high, "b": low}
    f2 = [j for j in range(FFT_R)
          if 900.0 <= fft_band_centre_hz(j, FFT_R, SR) < 2500.0]
    f2_peak = ({"type": "ArgMax", "items": [A(j) for j in f2]}
               if f2 else {"type": "Lit", "value": 0.0})
    return {"u_peak": peak, "u_tilt": tilt, "u_f2_peak": f2_peak}


class _P:
    __slots__ = ("_json",)

    def __init__(self, d):
        self._json = d


def _fisher(a, b):
    a = np.array([x for x in a if x == x])
    b = np.array([x for x in b if x == x])
    if len(a) < 2 or len(b) < 2:
        return 0.0
    spread = a.std() + b.std()
    sep = abs(a.mean() - b.mean())
    if spread < 1e-6:
        # both clusters are points (integer ArgMax-index cues quantize to a
        # constant on small samples). A clean split, but the raw Fisher would
        # explode to ~1e6 and overstate the win — cap it so the table is honest.
        return 3.0 if sep > 1e-9 else 0.0
    return sep / (spread + 1e-6)


def main():
    print("Developing the agent until it accumulates confusions (10 cycles)...")
    sub, pipe, test_set, vc, rec = _develop(cycles=10)
    print(f"  recognition after develop: {rec['correct']}/{rec['total']}")

    # the agent's confusions, strongest first.
    confs = sorted(
        ((sub.node(c)["attrs"].get("true_word"),
          sub.node(c)["attrs"].get("pred_word"),
          int(sub.node(c)["attrs"].get("count", 0)))
         for c in sub.nodes("Confusion")),
        key=lambda x: -x[2])
    pairs = [(X, Y) for X, Y, n in confs[:N_TOP_PAIRS]]
    print(f"  top confused pairs: " +
          ", ".join(f"{X}/{Y}(x{n})" for X, Y, n in confs[:N_TOP_PAIRS]))

    # The agent composes its ear from those confusions.
    boundaries = agent_specify_ear(sub, pipe, test_set, res_out=RES_OUT)
    ear_terms = compose_ear_cues(boundaries, SR)

    # --- (a) show the composed layout in Hz ---------------------------------
    print("\n(a) COMPOSED-EAR LAYOUT (16 bands over the 128 raw FFT bins):")
    print(f"    {'band':>4} | {'bins':>9} | {'Hz range':>16} | {'width Hz':>9}")
    widths = []
    for j in range(len(boundaries) - 1):
        lo_hz, hi_hz = ear_band_edges_hz(boundaries, j, SR)
        w = hi_hz - lo_hz
        widths.append((w, j, lo_hz, hi_hz))
        print(f"    {j:>4} | {boundaries[j]:>3}-{boundaries[j+1]:<5} | "
              f"{lo_hz:6.0f}-{hi_hz:<6.0f} Hz | {w:8.0f}")
    narrowest = sorted(widths)[:4]
    print("    narrowest 4 bands (where the agent put its resolution):")
    for w, j, lo_hz, hi_hz in narrowest:
        inform = 250 <= 0.5 * (lo_hz + hi_hz) <= 2500
        print(f"      band {j}: {lo_hz:.0f}-{hi_hz:.0f} Hz (width {w:.0f}) "
              f"{'<- formant region' if inform else ''}")

    # --- collect per-word cue values for both ears --------------------------
    uniform_terms = {c: compose_from_spec(FFT_R, c) for c in UNIFORM_CUES}
    uniform_terms.update(_uniform_fft_cues())
    words = set()
    for X, Y in pairs:
        words |= {X, Y}

    byword_uniform = {w: {c: [] for c in uniform_terms} for w in words}
    byword_ear = {w: {c: [] for c in ear_terms} for w in words}

    for w in words:
        d = fl._DIGITS.index(w)
        files = [f for f in test_set if f[1] == d]
        if len(files) < 2:
            # fall back to the full corpus for words not in the held-out test set
            files = [f for f in fl.gather_files(limit=None) if f[1] == d][:8]
        for path, *_ in files:
            s, fs = fl.load_wav(path)
            pipe.ingest(sub, s)
            sub.tick(50000)
            st = None
            for n in sub.nodes("AudioStream"):
                st = n
            sg = fl._collect_signs_from_stream(sub, st) if st else []
            enrich_sign_bands(sub, signs=sg)
            enrich_sign_windows(sub, signs=sg)
            enrich_sign_fft(sub, resolution=FFT_R, signs=sg)
            emit_ear_enrichment(sub, sg, boundaries, SR)
            for g in sg:
                for c, t in uniform_terms.items():
                    try:
                        byword_uniform[w][c].append(
                            float(sub.evaluate(_P(t), {"s": g})))
                    except Exception:
                        pass
                for c, t in ear_terms.items():
                    try:
                        byword_ear[w][c].append(
                            float(sub.evaluate(_P(t), {"s": g})))
                    except Exception:
                        pass

    # --- (b)/(c) the acceptance table ---------------------------------------
    print(f"\n(b)/(c) ACCEPTANCE TABLE  (uniform-{FFT_R} best Fisher vs "
          f"composed-{RES_OUT} best Fisher per confused pair)")
    print(f"{'pair':>11} | {'uniform-32 best':>26} | "
          f"{'composed-16 best':>26} | winner")
    print("-" * 86)
    wins = matches = 0
    rows = []
    for X, Y in pairs:
        ub = max(((c, _fisher(byword_uniform[X][c], byword_uniform[Y][c]))
                  for c in uniform_terms), key=lambda kv: kv[1])
        eb = max(((c, _fisher(byword_ear[X][c], byword_ear[Y][c]))
                  for c in ear_terms), key=lambda kv: kv[1])
        if eb[1] >= ub[1] - 1e-9:
            win = "composed"
            wins += 1
        else:
            win = "uniform"
        if eb[1] >= ub[1] * 0.95:
            matches += 1
        rows.append((X, Y, ub, eb))
        print(f"{X+'|'+Y:>11} | {ub[0]:>16} {ub[1]:7.3f} | "
              f"{eb[0]:>16} {eb[1]:7.3f} | {win}")

    print(f"\nComposed ear matched-or-beat uniform (within 5%) on "
          f"{matches}/{len(pairs)} pairs; strictly >= on {wins}/{len(pairs)}.")

    # (c) two/three specifically
    tt = next((r for r in rows if {r[0], r[1]} == {"two", "three"}), None)
    if tt:
        X, Y, ub, eb = tt
        print(f"\n(c) two/three (F2-vowel pair): uniform best {ub[0]}={ub[1]:.3f}, "
              f"composed best {eb[0]}={eb[1]:.3f} -> "
              f"{'composed separates it well' if eb[1] >= ub[1] - 1e-9 else 'uniform wins'}.")
    else:
        print("\n(c) two/three was not among the agent's top confused pairs this run.")


if __name__ == "__main__":
    main()

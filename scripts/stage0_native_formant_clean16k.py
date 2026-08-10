"""STAGE 0 re-confirmation on CLEAN 16 kHz — the native all-pole formant front end.

Re-runs the Stage-0 STRUCTURAL fidelity gate (scripts/stage0_native_formant_check.py)
on CLEAN 16 kHz Speech Commands digit frames (intact frication band, NOT
downsampled). The gate is rate-agnostic in shape: it checks the NATIVE primitives
(lpc_autocorr + levinson_durbin + lpc_roots_formants) reproduce the Python DSP
oracle's structure (autocorr, LPC coeffs, formant Hz) on real frames. The ONLY
change vs the 8 kHz run is the corpus + the rate-following constants (ORDER =
agent's spec rule int(fs/1000)+2 = 18 @ 16 kHz; WIN = 25 ms in samples).

DONKEY (audited): native primitives only — NO net, NO .fit, NO gradient, NO
sweep. The Python path is the reference oracle the native path must match. No
recognition, no held-out. CortexLoop/solve_for_n untouched.

Run: `PYTHONUNBUFFERED=1 python -m scripts.stage0_native_formant_clean16k`
"""
from __future__ import annotations

import numpy as np

import substrate_rs._native as _n
from domains.lpc_formant_representation import (
    _autocorr as py_autocorr,
    _levinson as py_levinson,
    _lpc_roots_formants as py_formants,
)
from scripts.clean16k_corpus import FS, load_wav, select_corpus

ORDER = int(FS / 1000) + 2          # the agent's spec rule: 18 at 16 kHz
PRE_EMPH = 0.97
WIN = int(0.025 * FS)               # 25 ms analysis window (400 samples @ 16 kHz)
F_LO, F_HI, BW_MAX = 150.0, 3600.0, 500.0


def frames_from_token(x: np.ndarray, fps: int = 25):
    n_frames = max(8, min(300, int(len(x) / FS * fps)))
    win = max(WIN, ORDER + 4)
    out = []
    for tf in range(n_frames):
        c = int((tf + 0.5) * len(x) / n_frames)
        a0 = max(0, c - win // 2)
        b0 = min(len(x), a0 + win)
        out.append(x[a0:b0])
    return out


def main():
    files, speakers = select_corpus()
    rng = np.random.default_rng(0)
    idx = rng.choice(len(files), size=24, replace=False)

    max_ac_err = 0.0
    max_a_err = 0.0
    n_frames_total = 0
    n_formants_native = 0
    n_formants_py = 0
    count_match = 0
    formant_abs_errs = []
    voiced_frames = 0

    for i in idx:
        path = files[int(i)][0]
        sig, _fs = load_wav(path)
        if sig is None or len(sig) < WIN:
            continue
        x = np.asarray(sig, dtype=np.float64)
        for fr in frames_from_token(x):
            if len(fr) < ORDER + 2:
                continue
            n_frames_total += 1

            xp = np.asarray(fr, dtype=np.float64)
            xp = np.append(xp[0], xp[1:] - PRE_EMPH * xp[:-1])
            xp = xp * np.hamming(len(xp))
            r_py = py_autocorr(xp, ORDER)
            a_py, _ = py_levinson(r_py, ORDER)

            r_nat = np.asarray(_n.lpc_autocorr(xp.astype(np.float32).tolist(), ORDER),
                               dtype=np.float64)
            a_nat = np.asarray(_n.levinson_durbin(r_nat.tolist(), ORDER),
                               dtype=np.float64)

            if len(r_nat) == len(r_py) and r_py[0] != 0:
                max_ac_err = max(max_ac_err,
                                 float(np.max(np.abs((r_nat - r_py) / (abs(r_py[0]) + 1e-9)))))
            if len(a_nat) == len(a_py):
                max_a_err = max(max_a_err, float(np.max(np.abs(a_nat - a_py))))

            f_nat = _n.lpc_roots_formants(
                np.asarray(fr, dtype=np.float32).tolist(),
                FS, ORDER, PRE_EMPH, F_LO, F_HI, BW_MAX)
            f_py = py_formants(np.asarray(fr, dtype=np.float64), FS, ORDER, PRE_EMPH)

            n_formants_native += len(f_nat)
            n_formants_py += len(f_py)
            if len(f_nat) == len(f_py):
                count_match += 1
            if len(f_py) >= 2:
                voiced_frames += 1
            for k in range(min(len(f_nat), len(f_py))):
                formant_abs_errs.append(abs(float(f_nat[k]) - float(f_py[k])))

    formant_abs_errs = np.asarray(formant_abs_errs) if formant_abs_errs else np.array([0.0])

    print("=== STAGE 0 re-confirm on CLEAN 16 kHz — native all-pole formant front end ===")
    print(f"corpus                  : clean 16 kHz Speech Commands digits "
          f"({len(speakers)} speakers, {len(files)} tokens)")
    print(f"rate-following constants : FS={FS}  ORDER={ORDER} (int(fs/1000)+2)  WIN={WIN}")
    print(f"tokens sampled          : {len(idx)} real clean-16k tokens (digits x speakers)")
    print(f"analysis frames         : {n_frames_total}")
    print(f"  voiced/structure frames: {voiced_frames} (>=2 formants in the reference)")
    print()
    print("-- (a) low-level chain (autocorr -> Levinson) native vs Python oracle --")
    print(f"  max |Δ autocorr| / r[0]: {max_ac_err:.3e}")
    print(f"  max |Δ LPC coeff a_k|  : {max_a_err:.3e}")
    print()
    print("-- (b) formant frequencies (LPC pole angles) native vs Python oracle --")
    print(f"  total formants native  : {n_formants_native}")
    print(f"  total formants Python  : {n_formants_py}")
    fm = count_match / max(1, n_frames_total)
    print(f"  frames w/ same #formant: {count_match}/{n_frames_total} ({fm:.3f})")
    print(f"  formant Hz error  mean : {float(formant_abs_errs.mean()):.3f} Hz")
    print(f"  formant Hz error  p95  : {float(np.percentile(formant_abs_errs,95)):.3f} Hz")
    print(f"  formant Hz error  max  : {float(formant_abs_errs.max()):.3f} Hz")
    print()

    low_level_ok = (max_ac_err < 1e-4) and (max_a_err < 1e-4)
    formant_struct_ok = (fm > 0.98) and (float(formant_abs_errs.mean()) < 1.0)
    gate = low_level_ok and formant_struct_ok
    print("=== READINESS GATE ===")
    print(f"  low-level chain owned (autocorr+Levinson bit-faithful): {low_level_ok}")
    print(f"  formant structure recovered (same #, <1 Hz drift)     : {formant_struct_ok}")
    print(f"  >>> STAGE-0 TEMPORAL-CODE / FRONT-END OWNED NATIVELY (16 kHz): {gate}")
    print()
    print("===MARKER_STAGE0_NATIVE_FORMANT_CLEAN16K_COMPLETE===")
    return gate


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""TASK 2(b) — the BANDWIDTH-BUG A/B: how much did the broken forward model throttle
the EAR? (analysis-by-synthesis: a faithful forward model should make hearing better
for free, via the shared model — measure it on an earlier-stage perception metric.)

WORLD ADAPTER ONLY. Reads WAVs, swaps the INSTRUMENT (the native formant extractor)
between its CORRECTED and its OLD-BUGGY (reversed-coeff / sign-wrong-bandwidth-gate)
form, and re-measures the Stage-3 speaker-invariance cluster gap d' on the SAME
clean-16k corpus with the SAME owned representation + native DtwTo decision. The
ONLY thing that changes is the formant instrument — so the d' delta isolates the
bug's cost to perception. NO net, NO .fit, NO agent decision: just the measurement.

The bug (docs/voice_impressionist.md (2)): `lpc_roots_formants` passed the LPC
coeffs REVERSED (`a[::-1]`), solving the RECIPROCAL polynomial -> every pole landed
OUTSIDE the unit circle -> bw = -fs/2pi*ln|z| < 0; and the freq-only extractor
filtered only `bw < bw_max`, so negative (i.e. ALL) bandwidths slipped through and
spurious wide poles were NOT rejected. Frequencies survived (reciprocation preserves
the pole angle) but the bandwidth gate was sign-wrong. The fix passes the coeffs
as-is (poles inside, positive bandwidths, the bw>0 gate restored). This A/B drives
the perception metric through BOTH instruments.
"""
import numpy as np

import substrate_rs
import substrate_rs._native as _N

import domains.agent_frontend as AF
from scripts.clean16k_corpus import load_wav, select_corpus
import scripts.stage3_invariance_clean16k as S3

# the two instruments (corrected = the current native fn; buggy = the historical one).
_CORRECTED = _N.lpc_roots_formants
_BUGGY = _N.lpc_roots_formants_buggy


def _patch_instrument(fn):
    """Point the agent's Stage-0 native formant hand-off at `fn` (the instrument
    under test). vtl_formant_track -> _native_lpc_roots_formants -> this native call,
    so swapping it here swaps the whole perception front-end's formant extractor."""
    substrate_rs._native.lpc_roots_formants = fn


def build_reps(files, instrument):
    """Build the Stage-3 speaker-invariant representation for every token with the
    given formant INSTRUMENT in place. Returns {(digit,speaker,idx): invariant_track}."""
    _patch_instrument(instrument)
    invar = {}
    for path, digit, speaker, idx in files:
        x, fs = load_wav(path)
        it = S3.invariant_trajectory(x, fs)
        if it is not None and len(it) >= 2:
            invar[(digit, speaker, idx)] = it
    return invar


def main():
    print("=" * 78)
    print("TASK 2(b) — BANDWIDTH-BUG A/B: did fixing the voice fix the EAR?")
    print("  Stage-3 cross-speaker invariance d' under the CORRECTED vs OLD-BUGGY")
    print("  formant instrument (same corpus, same rep, same native DtwTo decision).")
    print("=" * 78)

    files, speakers_all = select_corpus()
    x0, fs0 = load_wav(files[0][0])
    print(f"\ncorpus: clean 16 kHz Speech Commands digits, {len(files)} tokens, "
          f"{len(speakers_all)} speakers (fs0={fs0})")

    # quick instrument sanity: the buggy extractor lets a spurious extra pole through.
    seg = x0[len(x0) // 2 - 200: len(x0) // 2 + 200].astype(np.float32).tolist()
    fc = _CORRECTED(seg, int(fs0), int(fs0 / 1000) + 2, 0.97, 150.0, 3600.0, 500.0)
    fb = _BUGGY(seg, int(fs0), int(fs0 / 1000) + 2, 0.97, 150.0, 3600.0, 500.0)
    print(f"  instrument check (one frame): corrected formants {[round(v) for v in fc]}")
    print(f"                                buggy     formants {[round(v) for v in fb]}")

    # --- A: the CORRECTED instrument ---
    print("\n--- A: CORRECTED formant instrument (poles inside, positive bandwidths) ---")
    invar_corr = build_reps(files, _CORRECTED)
    corr = S3.cross_speaker_structure(invar_corr, "CORRECTED bandwidths")

    # --- B: the OLD-BUGGY instrument ---
    print("\n--- B: OLD-BUGGY formant instrument (reversed coeffs, sign-wrong bw gate) ---")
    invar_bug = build_reps(files, _BUGGY)
    bug = S3.cross_speaker_structure(invar_bug, "BUGGY (sign-wrong) bandwidths")

    # restore the corrected instrument (leave the module clean).
    _patch_instrument(_CORRECTED)

    # --- the lift ---
    dp_corr, dp_bug = corr["dprime"], bug["dprime"]
    sep_corr, sep_bug = corr["sep_frac"], bug["sep_frac"]
    lift = dp_corr - dp_bug
    pct = (100.0 * lift / abs(dp_bug)) if abs(dp_bug) > 1e-6 else float("inf")

    print("\n" + "=" * 78)
    print("THE LIFT — how much the broken forward model throttled the EAR")
    print("=" * 78)
    print(f"  cross-speaker invariance d'   : BUGGY {dp_bug:.3f}  ->  CORRECTED {dp_corr:.3f}"
          f"   ({lift:+.3f}, {pct:+.1f}%)")
    print(f"  structural separation (frac)  : BUGGY {sep_bug:.3f}  ->  CORRECTED {sep_corr:.3f}"
          f"   ({sep_corr - sep_bug:+.3f})")
    print(f"  within-word cross-spk scatter : BUGGY {bug['within_sd']:.4f}  ->  "
          f"CORRECTED {corr['within_sd']:.4f}")
    print(f"  residual speaker variance     : BUGGY {bug['residual_speaker_frac']:.3f}  ->  "
          f"CORRECTED {corr['residual_speaker_frac']:.3f} (lower=better)")
    print(f"\n  >>> fixing the bandwidth bug {'RAISES' if lift > 0 else 'does NOT raise'} "
          f"the perception cluster gap by {lift:+.3f} d' ({pct:+.1f}%).")
    print("===MARKER_BANDWIDTH_AB_COMPLETE===")


if __name__ == "__main__":
    main()

"""W5-in-the-digit-path verification: does the A-by-S formant correction make the
agent's synthesized DIGIT formants RE-ANALYSE to the INTENDED formant targets?

The proven W5 result is on the VCTK voice-identity corpus (rendered formants
re-analyse to the speaker's REAL formants, render-drift ~0). Here we verify the
SAME property in the DIGIT forward path: render each digit across personas WITH
and WITHOUT the A-by-S correction, re-analyse the rendered audio's F1/F2/F3 with
the SAME native analyser the inverse uses (lpc_formants_bw), and report the drift
from the intended articulatory formant trajectory. Drift should DROP toward ~0.

Owned native DSP throughout; Python is world-adapter glue (marshal + measure).
"""
from __future__ import annotations

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from substrate_rs import Substrate
import domains.projection as PROJ
import scripts.articulatory_gamma as AG
from scripts.articulatory_gamma import (
    GESTURE_SCORES, _admissible_trajectory, synth_formant_trajectory, SYNTH_FRAMES,
)
from scripts.formant_trajectory_dynamics import DIGITS
from domains.persona_speech_world import DEFAULT_PERSONAS

FS = 8000


def intended_formants(word, vtl_scale, formant_offset=None):
    """The intended (T x 3) Hz formant trajectory the synth aims at for `word` under
    a persona VTL scale — the SAME `scaled` array build_speech_forward feeds the synth
    AND the A-by-S corrector. The verification ground truth."""
    score = GESTURE_SCORES.get(word.lower())
    traj, src_seq, _ = _admissible_trajectory(score, SYNTH_FRAMES)
    form = synth_formant_trajectory(traj)
    if formant_offset is not None:
        fo = np.asarray(formant_offset, dtype=np.float64).reshape(1, -1)
        form = form * np.exp(fo)
    return form / max(vtl_scale, 1e-3)


def render_drift(rust, audio, fs, intended):
    """Median |F1|,|F2| Hz drift between the rendered audio's re-analysed formants
    (native lpc_formants_bw) and the intended trajectory, over the frames where the
    analyser returns >=3 in-band formants. The W5 metric."""
    n_frames = max(1, (len(audio) - PROJ._AXS_FRAME) // PROJ._AXS_HOP + 1)
    meas = PROJ._measure_rendered_formants(rust, audio, fs, n_frames)
    tgt = PROJ._resample_targets(np.asarray(intended, dtype=np.float64), n_frames)
    err = np.abs(tgt - meas)
    valid = np.isfinite(err)
    d = {}
    for k in range(3):
        col = err[valid[:, k], k]
        d[k] = float(np.median(col)) if col.size else float("nan")
    return d


def main():
    print("=" * 78)
    print("W5-IN-THE-DIGIT-PATH — rendered digit formants RE-ANALYSE to INTENDED?")
    print("  drift = median |F_k(rendered, lpc_formants_bw) - F_k(intended)| Hz")
    print("=" * 78)
    sub = Substrate()
    rust = PROJ._rust(sub)
    fwd = PROJ.build_speech_forward(AG)

    rows = []
    for word in DIGITS:
        for (name, f0, q, vtl) in DEFAULT_PERSONAS:
            intended = intended_formants(word, vtl)
            a_off = fwd(word, sub, fs=FS, f0_hz=f0, vtl_scale=vtl, axs_correct=False)
            a_on = fwd(word, sub, fs=FS, f0_hz=f0, vtl_scale=vtl, axs_correct=True)
            d_off = render_drift(rust, a_off, FS, intended)
            d_on = render_drift(rust, a_on, FS, intended)
            rows.append((word, name, f0, vtl, d_off, d_on))

    def col(rows, on, k):
        vals = [r[5 if on else 4][k] for r in rows if np.isfinite(r[5 if on else 4][k])]
        return float(np.median(vals)) if vals else float("nan")

    print(f"\n  {'dim':>4} {'OFF (raw Klatt)':>18} {'ON (A-by-S)':>14}  {'delta':>8}")
    for k, nm in enumerate(["F1", "F2", "F3"]):
        off = col(rows, False, k)
        on = col(rows, True, k)
        print(f"  {nm:>4} {off:>14.1f} Hz {on:>11.1f} Hz  {off - on:>+7.1f}")

    # F1/F2 are the within-digit cue dims (the corrupted ones in W5).
    f12_off = np.nanmedian([np.nanmean([r[4][0], r[4][1]]) for r in rows])
    f12_on = np.nanmedian([np.nanmean([r[5][0], r[5][1]]) for r in rows])
    print(f"\n  F1F2 cue-dim drift:  OFF {f12_off:.1f} Hz  ->  ON {f12_on:.1f} Hz  "
          f"({f12_off - f12_on:+.1f})")
    improved = sum(1 for r in rows
                   if np.isfinite(r[4][0]) and np.isfinite(r[5][0])
                   and np.nanmean([r[5][0], r[5][1]]) < np.nanmean([r[4][0], r[4][1]]))
    print(f"  tokens with F1F2 drift REDUCED by A-by-S: {improved}/{len(rows)}")
    print("\n  VERDICT: A-by-S correction drives rendered DIGIT formants to the "
          f"intended targets" if f12_on < f12_off else
          "\n  VERDICT: A-by-S did NOT reduce digit formant drift (honest)")
    print("===W5_DIGIT_VERIFY_COMPLETE===")


if __name__ == "__main__":
    main()

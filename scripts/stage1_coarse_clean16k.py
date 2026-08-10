"""STAGE 1 re-confirmation on CLEAN 16 kHz — coarse isolated recognition (squint).

Re-runs the Stage-1 STRUCTURAL readiness gate (scripts/stage1_coarse_recognition_
check.py) on the CLEAN 16 kHz Speech Commands digit corpus (intact frication
band, NOT downsampled). The squint (resolution-3 coarse band-mean trajectory) and
the NATIVE Argmin-of-DtwTo decision are RATE-AGNOSTIC (load_wav passes the file's
own fs into AF.cochleagram). The ONLY change vs the 8 kHz run is the corpus.

DONKEY (audited): NO net, NO .fit, NO gradient, NO loss, NO sweep. The squint is
the agent's own coarse gestalt collapse; the recognition decision is composed as
native graph Terms (NC._Argmin of NC._DtwTo) and evaluated by the Rust substrate.
The gate is the STRUCTURAL separation (within-word vs between-word coarse
distance), NOT a held-out accuracy. CortexLoop/solve_for_n untouched.

Run: `PYTHONUNBUFFERED=1 python -m scripts.stage1_coarse_clean16k`
"""
from __future__ import annotations

import numpy as np

import domains.agent_frontend as AF
import domains.native_cognition as NC
import domains.acoustic_resolution as AR
from substrate_rs import Substrate
from scripts.clean16k_corpus import DIGITS as _DIGITS, load_wav, select_corpus

# Reuse the exact squint + decision builders from the 8 kHz gate VERBATIM.
from scripts.stage1_coarse_recognition_check import (
    coarse_trajectory, _tuple, build_coarse_substrate, coarse_predict_term, _Pred,
)


def main():
    print("=== STAGE 1 re-confirmation on CLEAN 16 kHz — coarse recognition (squint) ===")

    files, speakers_all = select_corpus()
    x0, fs0 = load_wav(files[0][0])
    print(f"corpus: clean 16 kHz Speech Commands digits, {len(files)} tokens, "
          f"{len(speakers_all)} speakers (fs0={fs0})")

    # --- (a) Stage-0 hand-off: cues read the OWNED NATIVE formant chain (16 kHz) --
    seg = x0[len(x0) // 2 - 200: len(x0) // 2 + 200]
    nat_f = AF._native_lpc_roots_formants(seg, fs0, int(fs0 / 1000) + 2)
    M0 = AF.cochleagram(x0, fs0, AF._MIDDLE[1], AF._MIDDLE[2], AF._MIDDLE[3])
    cue_allpole = AF._vtl_formant_allpole(x0, fs0, M0, {"n_out": 24, "n_formants": 3})
    cue_dynamic = AF._vtl_formant_dynamic(x0, fs0, M0,
                                          {"n_out": 24, "n_formants": 3, "order": 1})
    track = AF.vtl_formant_track(x0, fs0, {"n_formants": 3})
    handoff_wired = (len(nat_f) > 0
                     and int(np.count_nonzero(cue_allpole)) > 0
                     and int(np.count_nonzero(cue_dynamic)) > 0
                     and len(track) > 0)
    print("\n--- (a) Stage-0 hand-off: cues read the OWNED NATIVE formant chain (16 kHz) ---")
    print(f"  native lpc_roots_formants (Hz, mid frame): "
          f"{[round(v, 1) for v in nat_f]}")
    print(f"  vtl_formant_allpole nonzero : {int(np.count_nonzero(cue_allpole))}/{len(cue_allpole)}")
    print(f"  vtl_formant_dynamic nonzero : {int(np.count_nonzero(cue_dynamic))}/{len(cue_dynamic)}")
    print(f"  vtl_formant_track frames    : {len(track)} (x{len(track[0]) if track else 0} chan)")
    print(f"  >>> HAND-OFF WIRED (native formants flow into the cues): {handoff_wired}")

    # --- (b) the SQUINT at the seed resolution -------------------------------
    resolution = int(AR._DEFAULT_RES)
    ladder = list(AR._LADDER)
    print(f"\n--- (b) the SQUINT (T5): coarse resolution = {resolution} "
          f"(ladder {ladder}, coarsest rung) ---")

    trajs = {}
    for path, digit, speaker, idx in files:
        x, fs = load_wav(path)
        t = coarse_trajectory(x, fs, resolution)
        if t is not None and len(t) >= 2:
            trajs[(digit, speaker, idx)] = t
    n_tok = len(trajs)
    speakers = sorted({k[1] for k in trajs})
    print(f"  coarse trajectories built: {n_tok} tokens, {len(speakers)} speakers")
    composes = n_tok > 0 and all(len(t[0]) == resolution for t in trajs.values())
    print(f"  >>> the squint COMPOSES (every token -> {resolution}-band trajectory): {composes}")

    # --- (c) the native recognition decision over the squint -----------------
    proto_speaker = speakers[0]
    prototypes = {}
    for d in range(10):
        cand = [(k, v) for k, v in trajs.items()
                if k[0] == d and k[1] == proto_speaker]
        if cand:
            prototypes[_DIGITS[d]] = sorted(cand, key=lambda kv: kv[0][2])[0][1]
    s, q, word_nodes = build_coarse_substrate(prototypes)
    term = coarse_predict_term()
    s.set_attr(q, NC.OBS_REL_ATTR, _tuple(prototypes[_DIGITS[0]]))
    self_pick = s.evaluate(term, {"q": q})
    decision_composes = self_pick is not None
    print(f"\n--- the NATIVE decision (T1 Argmin of T2 DtwTo) over the squint ---")
    print(f"  recognition Term composes + evaluates natively: {decision_composes}")
    print(f"  (self-prototype of '{_DIGITS[0]}' -> native Argmin picks node "
          f"{self_pick}, word '{s.node(self_pick)['attrs'].get('name')}')")

    # --- (d) THE STRUCTURAL READINESS GATE (NOT accuracy) --------------------
    within = []
    between = []
    margins_ok = 0
    margins_tot = 0
    for (d, sp, idx), t in trajs.items():
        w = _DIGITS[d]
        if w not in word_nodes:
            continue
        s.set_attr(q, NC.OBS_REL_ATTR, _tuple(t))
        own = None
        others = []
        for wname, nid in word_nodes.items():
            dist = s.evaluate(_Pred(NC._DtwTo(
                NC._Attr(NC._V("q"), NC.OBS_REL_ATTR),
                NC._Attr(NC._V("w"), NC.SYN_REL_ATTR))), {"q": q, "w": nid})
            dist = float(dist)
            if wname == w:
                own = dist
            else:
                others.append(dist)
        if own is None or not others:
            continue
        within.append(own)
        between.append(float(np.mean(others)))
        margins_tot += 1
        if own < np.mean(others):
            margins_ok += 1

    within = np.asarray(within)
    between = np.asarray(between)
    sep_frac = margins_ok / margins_tot if margins_tot else 0.0
    pooled_sd = np.sqrt(0.5 * (within.var() + between.var())) + 1e-9
    struct_gap = float((between.mean() - within.mean()) / pooled_sd)

    print(f"\n--- (d) THE STRUCTURAL READINESS GATE (NOT a held-out accuracy) ---")
    print(f"  tokens scored                         : {margins_tot}")
    print(f"  within-word coarse DtwTo  (mean+/-sd) : "
          f"{within.mean():.4f} +/- {within.std():.4f}")
    print(f"  between-word coarse DtwTo (mean+/-sd) : "
          f"{between.mean():.4f} +/- {between.std():.4f}")
    print(f"  structural separation (within<between): {sep_frac:.3f} of tokens")
    print(f"  standardized coarse cluster gap (d')  : {struct_gap:.3f}")

    structure_admitted = (composes and decision_composes
                          and sep_frac > 0.5 and struct_gap > 0.2
                          and within.mean() < between.mean())
    print(f"\n=== READINESS GATE ===")
    print(f"  squint composes (coarse trajectory)            : {composes}")
    print(f"  native decision composes (Argmin of DtwTo)     : {decision_composes}")
    print(f"  coarse structure separates words (within<betw) : "
          f"{within.mean() < between.mean()} (sep {sep_frac:.3f})")
    print(f"  gestalt clusters cohere (standardized gap > 0.2): "
          f"{struct_gap > 0.2} (d'={struct_gap:.3f})")
    print(f"  >>> STAGE-1 COARSE STRUCTURE ADMITTED (clean 16 kHz): {structure_admitted}")
    print(f"\n  (8 kHz FSDD reference: ~76.1% structural separation. The CLEAN-16k")
    print(f"   gate is the SAME structural property on full-band audio.)")
    print("===MARKER_STAGE1_COARSE_CLEAN16K_COMPLETE===")


if __name__ == "__main__":
    main()

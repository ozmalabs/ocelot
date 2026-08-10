"""native_cognition_accept — validate the agent's native cognition migration (Ranks 2 + the
rel-formant invariant) against its Python counterpart. Read-only consumer of
scripts/articulatory_gamma.py (the forward model + corpus); does NOT modify it.

Validates:
  (A) d_A(w): native predict_articulatory_term (Argmin of DtwTo+Γ) vs Python
      articulatory_distance-argmin — per-token agreement + each one's standalone accuracy.
  (B) rel-formants: native rel_formants_channel_term (Log+composed Mean) vs the Python
      relative_formants_frame, max abs error over the corpus.

NO net / .fit / gradient / sweep. Held-out is never relevant here (the articulatory prong
needs no bank — the forward model IS the knowledge — so d_A is the same on every token).
"""
from __future__ import annotations

import sys
import time

import numpy as np

from substrate_rs import Substrate

import scripts.viterbi_pairing as VP          # noqa: F401  (side effect: patches formant_track)
import scripts.formant_trajectory_dynamics as ftd
import scripts.articulatory_gamma as ag
import domains.native_cognition as NC

DIGITS = ag.DIGITS


def main():
    quick = "--quick" in sys.argv
    t0 = time.time()
    print("=" * 80)
    print("native_cognition_accept — Rank-2 (d_A) + the rel-formant invariant, NATIVE vs PYTHON")
    print("=" * 80, flush=True)

    sub = Substrate()
    # --- the forward model (owned, no training data) ---
    models = ag.articulatory_models()
    print(f"forward model: {len(models)} digit shadows (Γ-feasible, owned phonetics)")

    # --- corpus (read-only ingest via articulatory_gamma) ---
    print("building corpus (pairing-tracked formant trajectories + observed shadow) ...",
          flush=True)
    corpus, skipped = ag.build_corpus(sub, seed=0, quick=quick)
    print(f"corpus n={len(corpus)} (skipped {skipped})", flush=True)

    # ============================================================================
    #  (B) rel-formants: native Log+Mean Term vs Python relative_formants_frame.
    #  Validate on the raw formant frames the tracker emits (before obs_rel is built).
    # ============================================================================
    s_rel = Substrate()
    max_err = 0.0
    n_frames = 0
    # Re-track a sample of tokens to get raw formant frames (Hz), compare per-frame transform.
    files = ag.gather_files()
    rng = np.random.default_rng(1)
    sample = files[:] ; rng.shuffle(sample)
    sample = sample[: (40 if quick else 200)]
    for path, d, spk, idx in sample:
        sig, fs = ag.load_wav(path)
        track = ftd.formant_track(sig, fs)
        if track is None:
            continue
        for frame in track:
            f = np.asarray(frame, dtype=np.float64)
            if f.shape[0] != 3:
                continue
            ref = ftd.relative_formants_frame(f)                 # log(F)-mean(log F), with +1e-9
            nat = NC.native_rel_formants(s_rel, f + 1e-9, ftd._P, 3)
            err = float(np.max(np.abs(np.asarray(nat) - ref)))
            max_err = max(max_err, err)
            n_frames += 1
    print(f"\n(B) rel-formants native (Log+composed Mean) vs Python relative_formants_frame:")
    print(f"    frames compared = {n_frames}")
    print(f"    max abs error   = {max_err:.3e}  (expect ~0; native Log == numpy log)")

    # ============================================================================
    #  (A) d_A(w): native Argmin(DtwTo+Γ) vs Python articulatory_distance-argmin.
    # ============================================================================
    s_art, q, word_nodes = NC.build_articulatory_substrate(
        Substrate, models, ag.W_FORMANT_SHADOW, ag.W_GAMMA)

    n = 0
    agree = 0
    py_correct = 0
    nat_correct = 0
    close_call_disagree = 0
    for it in corpus:
        true = it["word"]
        obs_rel = it["obs_rel"]

        # Python d_A + argmin (the existing prong, read-only).
        d_a = ag.articulatory_distance(obs_rel, models, sub)
        pred_py = min(DIGITS, key=lambda w: d_a[w])

        # Native d_A + argmin (the agent's graph Term).
        pred_nat = NC.native_articulatory_predict(
            s_art, q, obs_rel, ag.W_FORMANT_SHADOW, ag.W_GAMMA, ftd._P)

        n += 1
        agree += int(pred_py == pred_nat)
        py_correct += int(pred_py == true)
        nat_correct += int(pred_nat == true)
        if pred_py != pred_nat:
            # is it a close call in the Python ranking? (top-2 gap small)
            ordered = sorted(d_a.values())
            gap = ordered[1] - ordered[0] if len(ordered) >= 2 else 1.0
            if gap < 0.05 * (abs(ordered[0]) + 1e-9):
                close_call_disagree += 1

    print(f"\n(A) d_A native (Argmin of DtwTo+Γ) vs Python articulatory_distance-argmin:")
    print(f"    n (tokens)                  = {n}")
    print(f"    chance                      = {1.0/len(DIGITS):.4f}")
    print(f"    PYTHON-d_A accuracy          = {py_correct/max(1,n):.4f}")
    print(f"    NATIVE-d_A accuracy          = {nat_correct/max(1,n):.4f}")
    print(f"    per-token AGREEMENT          = {agree/max(1,n):.4f} "
          f"({agree}/{n}, disagree={n-agree}, of which close-call={close_call_disagree})")
    print(f"\n    NOTE: DtwTo alignment is a SUPERSET of the Python fixed monotone resample,")
    print(f"    so divergence on close calls is EXPECTED (ownership, not byte-fidelity).")

    print(f"\nelapsed {time.time()-t0:.1f}s")
    print("NATIVE_COGNITION_ACCEPT_COMPLETED")


if __name__ == "__main__":
    main()

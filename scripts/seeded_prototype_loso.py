"""seeded_prototype_loso — does a SEEDED prototype vocal-tract shape (+ on-the-fly
adaptation) disentangle the speaker and break past CMVN's 0.570 cross-speaker cap?

THE WALL (docs/synthesize_gaps_on_audio_loso.md): a within-utterance linear subtract
reduces to CMVN 0.570 because it has NO MODEL of the speaker beyond the per-band mean —
the speaker's resonances stay tangled into the word's. THE MOVE (memory
ozma_forward_model_is_a_prototype_shape): a CLOSE-ENOUGH SHAPE (a seeded prototype
vocal-tract filter envelope) PREDICTS the speaker's resonance contribution and
subtracts THAT, leaving the word. The seed = the prior (the settled acoustics of vocal
tracts, the agent's source-filter knowledge); adaptation = the last mile to THIS talker.

A/B on the SAME robust SC 40-speaker LOSO split, the SAME agent DtwTo recognizer:
  RAW       — the cochleagram trajectory, no source normalization.
  CMVN      — the per-utterance mean/var-normalized cochleagram trajectory (0.570).
  PROTOTYPE — the SEEDED-prototype residual trajectory: pick the close-enough seeded
              tract shape, adapt it to this talker, subtract the predicted speaker
              envelope, read the residual (domains/prototype_shape_space).

PREDICTION: the prototype reaches the entangled speaker resonances CMVN (mean-subtract)
cannot, so cross-speaker LOSO lifts past 0.570. KILL: if it does NOT beat CMVN, say so
plainly — the shape is too off-manifold even after adaptation, or the prototype still
cannot disentangle, and the shape must be LEARNED from real speech (babble), not seeded.

DONKEY BOUNDARY (audited): the prototype shapes are DESIGNED FROM the agent's speech-
science (source_filter_theory / vocal_tract_resonance_formants / glottal_source /
speaker_normalization — sourced in prototype_shape_space, NOT invented); pick/adapt/
subtract = owned linear algebra (argmin + closed-form least-squares, no fit/net/weight,
per-utterance, no speaker labels); recognition = the agent's graph-resident DtwTo
(Argmin MinOver DtwTo), reused UNCHANGED from dtw_trajectory_loso; held-out speakers'
clips NEVER banked; LOSO ungameable.

Run: python -m scripts.seeded_prototype_loso [n_train_spk] [n_held_spk] [n_per] [seed]
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np

import domains.self_directed_speech_world as W
import domains.agent_frontend as FE
import domains.prototype_shape_space as PS

# reuse the EXACT robust SC LOSO split + bank mechanics (ungameable) and the agent's
# graph-resident DtwTo recognizer machinery — UNCHANGED.
from scripts.sc_loso_frontend_norm import build_split, bank, CELL, FS
from scripts.dtw_trajectory_loso import (
    fresh, write_exemplar_trajectories, mark_words, measure_dtw,
    BAG_CUES, EX_TRAJ_ATTR, _traj_tuple,
)
import scripts.dtw_trajectory_loso as DTW


# the three trajectories A/B'd — each the SAME (frames x bands) per-frame-L2 shape, so
# the agent's DtwTo recognizer aligns them all UNCHANGED. Only what (if anything) is
# subtracted as the speaker differs.
def _raw_track(x, fs):
    """The cochleagram trajectory with NO source normalization (per-frame L2 only) —
    the RAW baseline."""
    from domains.filter_settings import cochleagram, COCHLEAR_SETTINGS
    _, ec, dc, nf = next(s for s in COCHLEAR_SETTINGS if s[0] == "middle")
    M = cochleagram(np.asarray(x, dtype=np.float64), fs, ec, dc, nf)
    if M.size == 0:
        return []
    out = []
    for r in range(M.shape[0]):
        v = M[r]
        nrm = np.linalg.norm(v)
        out.append([float(t) for t in (v / nrm if nrm > 1e-9 else v)])
    return out


TRACKS = {
    "RAW": lambda x, fs: _raw_track(x, fs),
    "CMVN": lambda x, fs: FE.cmvn_track(np.asarray(x, dtype=np.float64), float(fs)),
    "PROTOTYPE": lambda x, fs: PS.prototype_residual_track(x, float(fs)),
}


def run_regime(name, track_fn, train_clips, seen_probe, loso_probe):
    """Bank the train clips, write the chosen trajectory on every exemplar + probe,
    recognise with the agent's UNCHANGED DtwTo. Returns (seen, loso)."""
    # monkey-point the dtw harness's trajectory extractor at THIS regime's track (the
    # only thing that varies; the recognizer + split are identical across regimes).
    DTW._extract_track = lambda x, fs: track_fn(x, fs)

    s, _p = fresh(BAG_CUES, dyn_order=1)
    bank(s, train_clips)
    n_traj = write_exemplar_trajectories(s, CELL)
    n_words = mark_words(s, CELL)
    seen = measure_dtw(s, seen_probe, CELL)
    loso = measure_dtw(s, loso_probe, CELL)
    print(f"[{name:9s}] {n_traj} exemplar traj, {n_words} words  "
          f"seen-speaker {seen:.3f}   cross-speaker LOSO {loso:.3f}   "
          f"gap {seen - loso:+.3f}", flush=True)
    return seen, loso


def main():
    if not W.sc_available():
        print("Speech Commands not found at /tmp/sc — abort.", flush=True)
        return
    n_train_spk = int(sys.argv[1]) if len(sys.argv) > 1 else 120
    n_held_spk = int(sys.argv[2]) if len(sys.argv) > 2 else 40
    n_per = int(sys.argv[3]) if len(sys.argv) > 3 else 20
    seed = int(sys.argv[4]) if len(sys.argv) > 4 else 20240608

    train_clips, seen_probe, loso_probe = build_split(n_train_spk, n_held_spk, n_per,
                                                      seed=seed)
    chance = 1.0 / len(W.sc_words())

    # report where the seeded shapes came from (sourced) + the grid.
    print(f"\n[shape-space] {len(PS._SHAPE_LS)} seeded prototype tract shapes over VTL "
          f"L={PS._VTL_MIN_CM:.0f}..{PS._VTL_MAX_CM:.0f} cm "
          f"(quarter-wave F_n=(2n-1)c/4L; source-filter envelope). Sourced: "
          f"source_filter_theory / vocal_tract_resonance_formants / glottal_source / "
          f"speaker_normalization.", flush=True)

    results = {}
    for name in ("RAW", "CMVN", "PROTOTYPE"):
        results[name] = run_regime(name, TRACKS[name], train_clips,
                                   seen_probe, loso_probe)

    raw_seen, raw_loso = results["RAW"]
    cmvn_seen, cmvn_loso = results["CMVN"]
    proto_seen, proto_loso = results["PROTOTYPE"]

    print("\n" + "=" * 74, flush=True)
    print("SC ROBUST CROSS-SPEAKER LOSO — SEEDED PROTOTYPE vs CMVN (agent DtwTo)",
          flush=True)
    print("=" * 74, flush=True)
    print(f"  {'regime':10s} {'seen':>8s} {'LOSO':>8s} {'seen-LOSO gap':>14s} "
          f"{'vs CMVN':>9s}", flush=True)
    for name in ("RAW", "CMVN", "PROTOTYPE"):
        seen, loso = results[name]
        print(f"  {name:10s} {seen:8.3f} {loso:8.3f} {seen - loso:14.3f} "
              f"{loso - cmvn_loso:+9.3f}", flush=True)
    print("-" * 74, flush=True)
    lift = proto_loso - cmvn_loso
    print(f"  chance {chance:.3f}; CMVN cross-speaker LOSO {cmvn_loso:.3f} "
          f"(gap {cmvn_seen - cmvn_loso:+.3f})", flush=True)
    print(f"  PROTOTYPE cross-speaker LOSO {proto_loso:.3f} "
          f"(gap {proto_seen - proto_loso:+.3f}); lift over CMVN {lift:+.3f}", flush=True)

    if lift > 0.02:
        print(f"  => YES: the SEEDED prototype + adaptation BEATS CMVN by {lift:+.3f} — "
              f"the prototype reaches the entangled speaker resonances the mean-subtract "
              f"could not. The shortcut works; babble becomes optional (the prior + "
              f"adaptation suffices).", flush=True)
    elif lift > 0.005:
        print(f"  => MARGINAL: the seeded prototype edges CMVN by {lift:+.3f} (within "
              f"noise of the 0.02 bar). Not a clean break of the wall.", flush=True)
    else:
        print(f"  => NO: the SEEDED prototype + adaptation does NOT beat CMVN "
              f"({lift:+.3f}). The seeds are too off-manifold even after adaptation, or "
              f"the prototype still cannot disentangle the speaker from the word. The "
              f"shape must be LEARNED from real speech (babble), not seeded. No rescue.",
              flush=True)
    print("[MARKER] SEEDED_PROTOTYPE_LOSO_COMPLETE", flush=True)


if __name__ == "__main__":
    main()

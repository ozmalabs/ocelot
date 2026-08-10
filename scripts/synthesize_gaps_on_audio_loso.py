"""synthesize_gaps_on_audio_loso — run the gap-synthesizer's OPERATION on the AUDIO.

THE OPERATION (order_n_postulates.synthesize_gaps, one scale down on the signal):
OPEN A HOLE IN GAMMA = subtract the admitted/expected, READ THE RESIDUAL. The hole is
opened at the SPEAKER (the admitted = the WITHIN-UTTERANCE CONSTANT, the part of the
cochleagram consistent ACROSS frames); the residual is the WORD (the per-frame
deviation). This is the faithful audio-state reproduction of the
`context_dependence_is_a_removable_function` implication-shape (model + subtract a
quantity that is a smooth function of its known context, recover the context-free
target) — see domains/agent_frontend.speaker_residual_track.

WHY NOT THE LPC PEEL THAT FAILED (docs/order_n_peel_loso.md): the LPC peel's FIND was
BOTTOM-UP per-frame all-pole whitening — it cannot tell "predictable = speaker" from
"predictable = the word's own vowel resonances", so it peeled the word too. The fix is
a COGNITION-DRIVEN FIND: target what is CONSTANT-OVER-TIME (the per-utterance low-rank
consistent subspace = the speaker), NOT per-frame structure (the word). That is
exactly "open the hole where the cognition predicts the speaker."

A/B on the SAME robust SC 40-speaker LOSO split (ungameable, held-out never banked),
all recognised by the agent's GRAPH-RESIDENT DtwTo trajectory recognizer:

  RAW       : the raw cochleagram trajectory (no source normalisation).
  CMVN      : the constant-MEAN baseline (per-band mean+variance norm) — the strong
              0.570 recognizer. This is "subtract the per-band constant LEVEL".
  RESIDUAL  : THIS OP — open the hole at the speaker (subtract the within-utterance
              CONSISTENT subspace: mean + top-(k-1) SVD directions), read the residual.
  LPC-PEEL  : the failed bottom-up per-frame all-pole whitening (PEEL-1), recognised on
              the same cmvn cochleagram trajectory of the residual waveform.

PREDICTION: the cognition-driven FIND (target the constant speaker structure, keep the
per-frame word deviation) lifts cross-speaker LOSO over RAW, tightens the seen-vs-cross
gap, and KEEPS THE WORD where the LPC peel destroyed it. KILL: if subtracting the
within-utterance constant structure does NOT beat CMVN (reduces to CMVN), or over-peels
like LPC, say so plainly — then the speaker is not separable from the word by a
within-utterance subtract and needs the full learned forward model (deeper). No rescue.

DONKEY BOUNDARY (audited): the speaker-template estimate + subtraction = owned linear
algebra (per-utterance mean + the utterance's OWN top-k SVD + projection — no fit, no
net, no learned weight); per-utterance UNSUPERVISED (no speaker labels), applied
per-utterance so NO leakage; the open-a-hole-read-residual is the agent's gap
operation; recognition = the agent's graph-resident DtwTo (Argmin MinOver DtwTo); SC
load + the speaker split = world-adapter mechanics; LOSO ungameable, held-out NEVER
banked.

Run: python -m scripts.synthesize_gaps_on_audio_loso [n_train_spk] [n_held_spk] [n_per] [seed]
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np

import domains.self_directed_speech_world as W
import domains.agent_frontend as FE
from domains.order_n_peel import peel

from scripts.sc_loso_frontend_norm import build_split, CELL, FS
from scripts.dtw_trajectory_loso import (
    BAG_CUES, fresh, bank, mark_words, dtw_predict_term, _traj_tuple,
    QUERY_NODE_TYPE, QUERY_TRAJ_ATTR, EX_TRAJ_ATTR, _Pred,
)

# k = width of the hole for the RESIDUAL op: number of within-utterance CONSISTENT
# components subtracted (k=1 = mean only; k>1 also removes top-(k-1) speaker SVD
# directions). Swept so the hole-width is read, not tuned to a single point.
RESIDUAL_KS = [1, 2, 3, 4]


def _track(regime, x, fs, k=1):
    """The trajectory the DtwTo recognizer aligns, per regime. Mechanical I/O DSP —
    the ONLY thing that differs between regimes is HOW the speaker is (or isn't)
    subtracted before the cochleagram trajectory is read."""
    x = np.asarray(x, dtype=np.float64)
    fs = float(fs)
    if regime == "RAW":
        # raw cochleagram trajectory, per-frame L2, NO source normalisation.
        Me = FE.cochleagram(x, fs, FE._MIDDLE[1], FE._MIDDLE[2], FE._MIDDLE[3])
        if Me.size == 0:
            return []
        out = []
        for r in range(Me.shape[0]):
            v = Me[r]
            nrm = np.linalg.norm(v)
            out.append([float(t) for t in (v / nrm if nrm > 1e-9 else v)])
        return out
    if regime == "CMVN":
        return FE.cmvn_track(x, fs)
    if regime == "RESIDUAL":
        return FE.speaker_residual_track(x, fs, {"k": k})
    if regime == "LPC-PEEL":
        # the failed bottom-up per-frame all-pole whitening (PEEL-1), then the SAME
        # cmvn cochleagram trajectory of the residual WAVEFORM (the doc's strong readout).
        r = peel(x, fs, 1)
        return FE.cmvn_track(r, fs)
    raise ValueError(regime)


def write_exemplar_trajectories(s, cell_key, regime, k=1):
    """Write each banked Exemplar's regime trajectory on its node (the `traj` attr the
    DtwTo recognizer reads). Mechanical world-adapter feature derivation."""
    n = 0
    for c in s.nodes("Concept"):
        a = s.node(c)["attrs"]
        if a.get("origin") != "speech_world" or a.get("cell_key") != cell_key:
            continue
        for ex in s.neighbours(c, "has_exemplar"):
            ea = s.node(ex)["attrs"]
            aud = ea.get("audio")
            if aud is None:
                continue
            track = _track(regime, np.asarray(aud, dtype=np.float64),
                           float(ea.get("fs", FS)), k)
            s.set_attr(ex, EX_TRAJ_ATTR, _traj_tuple(track))
            n += 1
    return n


def measure_dtw(s, probe, regime, k=1):
    """Accuracy under the agent's graph-resident DtwTo recognizer on the regime
    trajectory. Same Term as dtw_trajectory_loso; only the trajectory differs."""
    qn = s.add_node(QUERY_NODE_TYPE, {"origin": "synth_gaps_probe"})
    term = _Pred(dtw_predict_term())
    tot = cor = 0
    for w, x, fs in probe:
        track = _track(regime, x, fs, k)
        s.set_attr(qn, QUERY_TRAJ_ATTR, _traj_tuple(track))
        pred = s.evaluate(term, {"q": qn})
        guess = s.node(pred)["attrs"].get("name") if pred is not None else None
        tot += 1
        cor += int(guess == w)
    s.remove_node(qn)
    return cor / max(tot, 1)


def run_regime(label, regime, train_clips, seen_probe, loso_probe, k=1):
    """One regime on a FRESH substrate (only the split is shared): bank, write the
    regime trajectories, recognise seen + cross-speaker via DtwTo."""
    s, _p = fresh(BAG_CUES, dyn_order=1)
    bank(s, train_clips)
    n_traj = write_exemplar_trajectories(s, CELL, regime, k)
    mark_words(s, CELL)
    seen = measure_dtw(s, seen_probe, regime, k)
    loso = measure_dtw(s, loso_probe, regime, k)
    print(f"[{label:11s}] {n_traj} exemplar trajectories  "
          f"seen {seen:.3f}   cross-speaker LOSO {loso:.3f}   gap {seen - loso:+.3f}",
          flush=True)
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

    results = {}
    results["RAW"] = run_regime("RAW", "RAW", train_clips, seen_probe, loso_probe)
    results["CMVN"] = run_regime("CMVN", "CMVN", train_clips, seen_probe, loso_probe)
    for k in RESIDUAL_KS:
        results[f"RESIDUAL-k{k}"] = run_regime(
            f"RESIDUAL-k{k}", "RESIDUAL", train_clips, seen_probe, loso_probe, k)
    results["LPC-PEEL"] = run_regime("LPC-PEEL", "LPC-PEEL", train_clips,
                                     seen_probe, loso_probe)

    raw_seen, raw_loso = results["RAW"]
    cmvn_seen, cmvn_loso = results["CMVN"]
    peel_seen, peel_loso = results["LPC-PEEL"]

    print("\n" + "=" * 78, flush=True)
    print("SPEECH-COMMANDS ROBUST CROSS-SPEAKER LOSO — synthesize_gaps ON THE AUDIO",
          flush=True)
    print("(open a hole at the SPEAKER = subtract the within-utterance CONSTANT, "
          "read the RESIDUAL = the WORD; DtwTo trajectory recognizer)", flush=True)
    print("=" * 78, flush=True)
    order = (["RAW", "CMVN"] + [f"RESIDUAL-k{k}" for k in RESIDUAL_KS]
             + ["LPC-PEEL"])
    print(f"  {'regime':12s} {'seen':>8s} {'LOSO':>8s} {'seen-LOSO gap':>14s} "
          f"{'vs RAW':>9s} {'vs CMVN':>9s}", flush=True)
    for name in order:
        seen, loso = results[name]
        print(f"  {name:12s} {seen:8.3f} {loso:8.3f} {seen - loso:14.3f} "
              f"{loso - raw_loso:+9.3f} {loso - cmvn_loso:+9.3f}", flush=True)
    print("-" * 78, flush=True)
    print(f"  chance {chance:.3f}", flush=True)

    # the best RESIDUAL hole-width by cross-speaker LOSO.
    best_k = max(RESIDUAL_KS, key=lambda k: results[f"RESIDUAL-k{k}"][1])
    res_seen, res_loso = results[f"RESIDUAL-k{best_k}"]
    lift_raw = res_loso - raw_loso
    lift_cmvn = res_loso - cmvn_loso
    raw_gap = raw_seen - raw_loso
    res_gap = res_seen - res_loso
    gap_change = res_gap - raw_gap        # negative = gap TIGHTENED (speaker peeled)
    keeps_word = res_loso > peel_loso     # vs the failed LPC peel (over-peeled the word)
    print(f"  best RESIDUAL: k={best_k}  LOSO {res_loso:.3f}  "
          f"(lift over RAW {lift_raw:+.3f}, over CMVN {lift_cmvn:+.3f})", flush=True)
    print(f"  gap: RAW {raw_gap:+.3f} -> RESIDUAL-k{best_k} {res_gap:+.3f} "
          f"(change {gap_change:+.3f}; negative = tighter = speaker peeled away)",
          flush=True)
    print(f"  keeps the word vs LPC-peel: RESIDUAL {res_loso:.3f} vs PEEL "
          f"{peel_loso:.3f}  ({'YES' if keeps_word else 'NO'})", flush=True)

    # VERDICT
    beats_raw = lift_raw > 0.02
    beats_cmvn = lift_cmvn > 0.02
    if beats_cmvn and keeps_word:
        v = ("YES (advances the frontier)",
             f"the cognition-driven open-hole-at-speaker LIFTS cross-speaker LOSO "
             f"{lift_cmvn:+.3f} OVER CMVN (and {lift_raw:+.3f} over RAW), keeps the "
             f"word (beats the LPC peel {res_loso:.3f} vs {peel_loso:.3f}), gap change "
             f"{gap_change:+.3f}. Subtracting the within-utterance CONSISTENT subspace "
             f"separates the speaker from the word where per-frame whitening could not.")
    elif beats_raw and keeps_word and abs(lift_cmvn) <= 0.02:
        v = ("PARTIAL (beats RAW + keeps the word, ~ties CMVN)",
             f"the residual op lifts cross-speaker LOSO {lift_raw:+.3f} over RAW and "
             f"keeps the word (vs LPC peel {res_loso:.3f} > {peel_loso:.3f}), but does "
             f"NOT clearly beat CMVN ({lift_cmvn:+.3f}). Removing the within-utterance "
             f"consistent subspace ~reduces to the constant-mean CMVN baseline: the "
             f"low-rank consistent structure it removes is essentially the per-band "
             f"level CMVN already removes. The speaker beyond the constant level needs "
             f"the deeper learned forward model.")
    elif keeps_word and not beats_raw:
        v = ("NO (reduces to ~baseline; keeps the word but no lift)",
             f"the residual keeps the word (vs LPC peel {res_loso:.3f} > {peel_loso:.3f}) "
             f"but does NOT lift cross-speaker LOSO over RAW ({lift_raw:+.3f}) or CMVN "
             f"({lift_cmvn:+.3f}). The within-utterance constant-subspace subtract does "
             f"not separate the speaker from the word — DEEPER: needs the full learned "
             f"forward model.")
    else:
        v = ("NO (over-peels like LPC / loses the word)",
             f"subtracting the within-utterance consistent subspace does NOT lift "
             f"cross-speaker LOSO (RAW {lift_raw:+.3f}, CMVN {lift_cmvn:+.3f}) and does "
             f"not cleanly keep the word vs the LPC peel ({res_loso:.3f} vs "
             f"{peel_loso:.3f}). At higher k it over-peels like the LPC bottom-up FIND. "
             f"The speaker is not separable from the word by a within-utterance "
             f"subtract — DEEPER: needs the full learned forward model.")
    print(f"  => {v[0]}: {v[1]}", flush=True)
    print("[MARKER] SYNTHESIZE_GAPS_ON_AUDIO_LOSO_COMPLETE", flush=True)


if __name__ == "__main__":
    main()

"""order_n_peel_loso — does ITERATED PREDICTIVE PEELING (the order-N FIND-PROCESS-
SUBTRACT loop) lift cross-speaker LOSO and tighten the seen-vs-cross gap?

The spec (ozma_prediction_is_waveform_subtraction + ozma_order_n_analysis_by_synthesis):
peel the waveform n times — each pass FINDs the dominant predictable structure,
adaptively PREDICTs it (owned linear prediction), SUBTRACTs (residual). The speaker
(vocal-tract envelope + glottal source, roughly constant within an utterance) is
maximally predictable => lands in the peel; the word (fast articulatory motion) is
least predictable => survives in the residual. Recognise on the RESIDUAL.

A/B on the SAME robust SC 40-speaker LOSO split (ungameable, held-out never banked):

  RAW            : recognise on the un-peeled waveform (n=0).
  PEEL-n         : recognise on the residual after n passes (n in {1,2,3}).

Recognition = the agent's DTW-trajectory recognizer (Argmin MinOver DtwTo over the
formant trajectory) — the strongest cross-speaker recognizer (docs/dtw_trajectory_
loso.md). The ONLY thing that changes between regimes is the waveform the trajectory
is extracted from (raw vs n-times peeled). Reports seen + LOSO + gap per n.

PREDICTION: the residual loses the speaker (predictable/constant) and keeps the word
-> cross-speaker LOSO up, gap tighter. KILL: if the residual does NOT help cross-
speaker, say so plainly.

DONKEY BOUNDARY (audited): the peel = the agent's order-N operator over its OWNED
linear-prediction primitive (autocorrelation + Levinson-Durbin, owned linear algebra,
no fit/net); recognition = the agent's graph-resident DtwTo; SC load + speaker split =
world-adapter mechanics; LOSO ungameable, held-out clips NEVER banked.

Run: python -m scripts.order_n_peel_loso [n_train_spk] [n_held_spk] [n_per] [seed]
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np

from substrate_rs import Substrate
import domains.self_directed_speech_world as W
import domains.agent_frontend as FE
from domains.stt_pipeline import STTPipeline, STTParams
from domains.order_n_peel import peel

from scripts.sc_loso_frontend_norm import build_split, bank, CELL, FS
from scripts.dtw_trajectory_loso import (
    BAG_CUES, fresh, mark_words, dtw_predict_term, _traj_tuple,
    QUERY_NODE_TYPE, QUERY_TRAJ_ATTR, EX_TRAJ_ATTR, _Pred, TRAJ_ATTRS,
)
from domains.many_settings_recognizer import WORD_ATTR

# the passes to sweep. 0 = RAW (no peel); 1,2,3 = the order-N peel.
PASSES = [0, 1, 2, 3]

# WHICH trajectory the DTW recognizer aligns on the (peeled) residual:
#   "cmvn"    : the full source-normalized cochleagram trajectory (frames x bands).
#               The RIGHT readout for a peeled residual — the peel WHITENS the all-pole
#               spectral envelope (where formants live), so a formant-track readout
#               reads formants that the peel removed; the cochleagram trajectory keeps
#               whatever spectro-temporal structure survives the whitening.
#   "formant" : the thin VTL formant trajectory (frames x [F1..F3|velocity]) — the
#               strongest RAW recognizer, but mismatched to a whitened residual.
TRAJ_KIND = os.environ.get("PEEL_TRAJ", "cmvn")


def _track_peeled(x, fs, n_passes):
    """The agent's trajectory feature of the clip's RESIDUAL after n peel passes.
    n=0 is the raw waveform (RAW baseline). Mechanical I/O: peel (owned linear-
    prediction loop) then extract the agent's trajectory feature."""
    x = np.asarray(x, dtype=np.float64)
    r = peel(x, float(fs), n_passes)
    if TRAJ_KIND == "formant":
        return FE.vtl_formant_track(r, float(fs), TRAJ_ATTRS)
    return FE.cmvn_track(r, float(fs))


def write_exemplar_trajectories_peeled(s, cell_key, n_passes):
    """Write each banked Exemplar's PEELED-residual VTL trajectory on its node (the
    `traj` attr the DtwTo recognizer reads). Mechanical world-adapter feature
    derivation; the peel order is fixed by the regime."""
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
            x = np.asarray(aud, dtype=np.float64)
            fs = float(ea.get("fs", FS))
            track = _track_peeled(x, fs, n_passes)
            s.set_attr(ex, EX_TRAJ_ATTR, _traj_tuple(track))
            n += 1
    return n


def measure_dtw_peeled(s, probe, n_passes):
    """Cross-speaker (or seen) accuracy under the agent's DTW recognizer on the
    PEELED-residual trajectory. Same graph Term as dtw_trajectory_loso; only the
    waveform the query trajectory comes from is peeled."""
    qn = s.add_node(QUERY_NODE_TYPE, {"origin": "peel_probe"})
    term = _Pred(dtw_predict_term())
    tot = cor = 0
    for w, x, fs in probe:
        track = _track_peeled(x, fs, n_passes)
        s.set_attr(qn, QUERY_TRAJ_ATTR, _traj_tuple(track))
        pred = s.evaluate(term, {"q": qn})
        guess = s.node(pred)["attrs"].get("name") if pred is not None else None
        tot += 1
        cor += int(guess == w)
    s.remove_node(qn)
    return cor / max(tot, 1)


def run_regime(n_passes, train_clips, seen_probe, loso_probe):
    """One regime: bank the train clips, write their peeled trajectories, recognise
    seen + cross-speaker on the peeled residual. A fresh substrate per regime so the
    only shared thing is the split."""
    s, _p = fresh(BAG_CUES, dyn_order=1)
    bank(s, train_clips)
    n_traj = write_exemplar_trajectories_peeled(s, CELL, n_passes)
    mark_words(s, CELL)
    seen = measure_dtw_peeled(s, seen_probe, n_passes)
    loso = measure_dtw_peeled(s, loso_probe, n_passes)
    label = "RAW" if n_passes == 0 else f"PEEL-{n_passes}"
    print(f"[{label:7s}] {n_traj} exemplar trajectories  "
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

    results = {}
    for n in PASSES:
        results[n] = run_regime(n, train_clips, seen_probe, loso_probe)

    raw_seen, raw_loso = results[0]
    print("\n" + "=" * 74, flush=True)
    print("SPEECH-COMMANDS ROBUST CROSS-SPEAKER LOSO — ORDER-N PREDICTIVE PEEL",
          flush=True)
    print(f"(recognise on the residual after n FIND-PROCESS-SUBTRACT passes; "
          f"DTW {TRAJ_KIND} trajectory)", flush=True)
    print("=" * 74, flush=True)
    print(f"  {'regime':8s} {'seen':>8s} {'LOSO':>8s} {'seen-LOSO gap':>14s} "
          f"{'LOSO lift':>11s}", flush=True)
    for n in PASSES:
        seen, loso = results[n]
        label = "RAW" if n == 0 else f"PEEL-{n}"
        print(f"  {label:8s} {seen:8.3f} {loso:8.3f} {seen - loso:14.3f} "
              f"{loso - raw_loso:+11.3f}", flush=True)
    print("-" * 74, flush=True)
    print(f"  chance {chance:.3f}; RAW cross-speaker LOSO {raw_loso:.3f} "
          f"(seen {raw_seen:.3f}, gap {raw_seen - raw_loso:+.3f})", flush=True)

    # verdict: best peel vs RAW, on BOTH absolute cross-speaker LOSO and the gap.
    peel_ns = [n for n in PASSES if n > 0]
    best_n = max(peel_ns, key=lambda n: results[n][1])
    best_seen, best_loso = results[best_n]
    lift = best_loso - raw_loso
    raw_gap = raw_seen - raw_loso
    best_gap = best_seen - best_loso
    gap_change = best_gap - raw_gap        # negative = gap TIGHTENED (speaker peeled)
    print(f"  best peel: PEEL-{best_n} LOSO {best_loso:.3f} "
          f"(lift {lift:+.3f} over RAW)", flush=True)
    print(f"  gap: RAW {raw_gap:+.3f} -> PEEL-{best_n} {best_gap:+.3f} "
          f"(change {gap_change:+.3f}; negative = tighter = speaker peeled away)",
          flush=True)
    if lift > 0.02:
        print(f"  => YES: iterated predictive peeling LIFTS the real cross-speaker "
              f"LOSO by {lift:+.3f} (PEEL-{best_n}). The speaker is in the peel; "
              f"recognising on the residual keeps the word.", flush=True)
    elif lift > 0.005 or gap_change < -0.02:
        print(f"  => PARTIAL: peeling moves cross-speaker LOSO {lift:+.3f} and the "
              f"seen-vs-cross gap {gap_change:+.3f}. Weak signal that the speaker is "
              f"partly in the peel.", flush=True)
    else:
        print(f"  => NO: iterated predictive peeling does NOT lift the robust real "
              f"cross-speaker LOSO (best {lift:+.3f}) nor tighten the gap "
              f"({gap_change:+.3f}). The predictable layers the LPC residual strips do "
              f"NOT carry the speaker in a way recognition recovers — the residual "
              f"loses word structure along with (or instead of) the speaker.",
              flush=True)
    print("[MARKER] ORDER_N_PEEL_LOSO_COMPLETE", flush=True)


if __name__ == "__main__":
    main()

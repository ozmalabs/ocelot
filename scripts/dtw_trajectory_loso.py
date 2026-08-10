"""dtw_trajectory_loso — does a TEMPORAL-ALIGNMENT recognizer (DTW over the order-N
gesture TRAJECTORY) lift absolute cross-speaker LOSO above the per-frame BAG?

The cue levers are exhausted (docs/dynamic_invariant_loso.md): CMVN + the sharp
all-pole VTL + the order-N dynamic land cross-speaker LOSO at ~0.42-0.47 (chance
0.10). That doc NAMED the next structure — NOT a richer per-frame feature, but the
RECOGNIZER: the per-frame readout throws away TEMPORAL STRUCTURE. The gesture is a
TRAJECTORY (a PATH), not a bag of per-frame values; the way F2 sweeps into a vowel is
a speaker-invariant MOTION matched by ALIGNMENT, not by an unordered descriptor. So
the next lever is a DTW alignment over the VTL-normalized sharp formant trajectory.

This script A/Bs exactly that on the SAME robust SC 40-speaker LOSO split:

  BAG (baseline) : the current per-frame `blind_guess` on the static+dynamic best
                   front end (CMVN + sharp-allpole VTL + the order-N dynamic cue) —
                   the ~0.42-0.47 per-frame-bag recognizer. UNCHANGED.
  DTW-TRAJECTORY : the agent's GRAPH-RESIDENT DtwTo recognizer over the SAME VTL
                   formant trajectory — recognize = Argmin over candidate words of
                   (MinOver that word's banked exemplars of DtwTo(query_traj,
                   exemplar_traj)). The trajectory is the agent's FEATURE (the
                   VTL-normalized sharp formant track, ordered as a sequence +
                   order-1 velocity channels); the decision is the agent's OWNED
                   DtwTo / MinOver / Argmin Term-tree evaluated NATIVELY in Rust.

Does aligning the gesture TRAJECTORY recognize the speaker-invariant gesture better
than the per-frame bag? Report seen + LOSO + gap for both.

DONKEY BOUNDARY (audited): the trajectory is the agent's composable DSP (the SAME
sharp LPC-root formant + F_i - mean(F1..F3) VTL invariant the dynamic cue uses, kept
ORDERED instead of L2-bagged — agent_frontend.vtl_formant_track). The DTW recognizer
is the agent's GRAPH-RESIDENT decision: DtwTo (a Rust Term the agent owns, the banded
Sakoe-Chiba alignment), composed with MinOver (nearest exemplar) and Argmin (the word
decision) over its OWN banked exemplars + word Concepts — NO fit, NO trained net, NO
learned weight, evaluated by substrate.evaluate. SC load + the speaker split are
world-adapter mechanics; LOSO is the ungameable yardstick; held-out speakers' clips
are NEVER banked.

Run: python -m scripts.dtw_trajectory_loso [n_train_spk] [n_held_spk] [n_per] [seed]
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
from domains.many_settings_recognizer import WORD_ATTR

# reuse the SAME robust SC LOSO split builder + bank/measure mechanics (ungameable).
from scripts.sc_loso_frontend_norm import build_split, bank, measure, CELL, FS

# the static+dynamic BEST front end the BAG baseline runs on (the ~0.42-0.47 regime
# from docs/dynamic_invariant_loso.md): CMVN + sharp-allpole VTL + the order-N dynamic.
BAG_CUES = ["cmvn_ear", "vtl_formant_allpole", "vtl_formant_dynamic"]

# the trajectory the DTW recognizer aligns — the agent's FEATURE, kept ORDERED.
#   "formant" : VTL-normalized sharp formant track (frames x [F1..F3 | velocity])
#   "cmvn"    : the SAME source-normalized cochleagram the dominant cmvn_ear cue uses,
#               kept as an ordered per-frame trajectory (the RICH spectral path).
TRAJ_KIND = os.environ.get("DTW_TRAJ", "formant")
TRAJ_ATTRS = {"n_formants": 3, "fps": 25, "with_velocity": True}


def _extract_track(x, fs):
    """The agent's trajectory feature for one clip (selected by TRAJ_KIND)."""
    x = np.asarray(x, dtype=np.float64)
    if TRAJ_KIND == "cmvn":
        return FE.cmvn_track(x, float(fs))
    return FE.vtl_formant_track(x, float(fs), TRAJ_ATTRS)


# ---------------------------------------------------------------------------
# The agent's GRAPH-RESIDENT DTW recognizer (composed from owned ops).
#
#   predict(query) = Argmin over candidate words w of
#                      MinOver e in has_exemplar(w) of  DtwTo(query_traj, traj(e))
#
# DtwTo = the agent's banded Sakoe-Chiba DTW Term (Rust); MinOver = nearest banked
# exemplar of the word; Argmin = the word decision. Evaluated natively. No Python
# recognizer: the query trajectory is written on a scratch node, each exemplar's
# trajectory on its Exemplar node, and the Term picks the word with the
# minimum-DTW aligned exemplar.
# ---------------------------------------------------------------------------

QUERY_NODE_TYPE = "DtwQuery"
QUERY_TRAJ_ATTR = "q_traj"
EX_TRAJ_ATTR = "traj"


class _Pred:
    __slots__ = ("_json",)

    def __init__(self, d):
        self._json = d


def _V(n): return {"type": "Var", "name": n}
def _Lit(v): return {"type": "Lit", "value": v}
def _Attr(node, k): return {"type": "Attr", "node": node, "key": k}
def _Nb(node, e): return {"type": "Neighbours", "node": node, "edge_type": e,
                          "any_type": False}
def _DtwTo(a, b): return {"type": "DtwTo", "a": a, "b": b}
def _NodesWhere(t, k, v): return {"type": "NodesWhere", "node_type": t,
                                  "attr_key": k, "value": v}
def _MinOver(src, var, val): return {"type": "MinOver", "source": src,
                                     "var_name": var, "value": val, "default": None}
def _Argmin(src, var, val): return {"type": "Argmin", "source": src,
                                    "var_name": var, "value": val, "default": None}


def dtw_predict_term():
    """The agent's DTW-trajectory recognition DECISION as a graph Term-tree:
    Argmin over is_word Concepts of the MinOver-exemplar DtwTo distance to the query.
    The query node is bound by env as the var `q` (the same way recognize_sign binds
    its sign var `s`); its trajectory is the `q_traj` attr."""
    word_dist = _MinOver(_Nb(_V("w"), "has_exemplar"), "e",
                         _DtwTo(_Attr(_V("q"), QUERY_TRAJ_ATTR),
                                _Attr(_V("e"), EX_TRAJ_ATTR)))
    return _Argmin(_NodesWhere("Concept", WORD_ATTR, _Lit(1.0)), "w", word_dist)


def _traj_tuple(track):
    """A trajectory (list of frames) as a tuple-of-tuples the graph can store as an
    attr (frames x channels). Empty -> a single zero frame so DtwTo stays finite."""
    if not track:
        return ((0.0, 0.0, 0.0),)
    return tuple(tuple(float(v) for v in frame) for frame in track)


def write_exemplar_trajectories(s, cell_key):
    """Mechanical I/O: for each banked Exemplar in the cell, extract its VTL formant
    trajectory through the agent's owned vtl_formant_track and store it on the node as
    the `traj` attr the DtwTo recognizer reads. World-adapter feature derivation (no
    decision); cached per exemplar so banking is paid once."""
    n = 0
    for c in s.nodes("Concept"):
        a = s.node(c)["attrs"]
        if a.get("origin") != "speech_world" or a.get("cell_key") != cell_key:
            continue
        for ex in s.neighbours(c, "has_exemplar"):
            ea = s.node(ex)["attrs"]
            if ea.get(EX_TRAJ_ATTR) is not None:
                continue
            aud = ea.get("audio")
            if aud is None:
                continue
            x = np.asarray(aud, dtype=np.float64)
            fs = float(ea.get("fs", FS))
            track = _extract_track(x, fs)
            s.set_attr(ex, EX_TRAJ_ATTR, _traj_tuple(track))
            n += 1
    return n


def mark_words(s, cell_key):
    """Tag this cell's word Concepts is_word so the Argmin can range over them
    (the SAME marking blind_guess relies on; mechanical setup)."""
    n = 0
    for c in s.nodes("Concept"):
        a = s.node(c)["attrs"]
        if a.get("origin") == "speech_world" and a.get("cell_key") == cell_key:
            s.set_attr(c, WORD_ATTR, 1.0)
            n += 1
        elif a.get("origin") == "speech_world" and a.get(WORD_ATTR):
            # zero OTHER cells' word flags so they cannot win (cross-cell scoping,
            # the same the bag recognizer applies).
            s.set_attr(c, WORD_ATTR, 0.0)
    return n


def _track_bag_vec(track, n_channels, n_out=24):
    """The SAME trajectory feature, but COLLAPSED into the per-frame BAG: resample each
    channel's time track to n_out and L2-flatten (the exact readout shape the cues
    produce). This is the feature-matched control — the identical trajectory with the
    temporal ORDER thrown away — so the BAG-vs-DTW difference is PURELY the alignment.
    n_channels gives the fixed width so empty/short tracks pad consistently."""
    width = n_channels * n_out
    if not track:
        return np.zeros(width, dtype=np.float64)
    arr = np.asarray(track, dtype=np.float64)          # frames x channels
    out = []
    for k in range(min(arr.shape[1], n_channels)):
        col = arr[:, k]
        idx = np.linspace(0, col.size - 1, n_out)
        out.append(np.interp(idx, np.arange(col.size), col))
    v = np.concatenate(out) if out else np.zeros(width, dtype=np.float64)
    if v.size < width:
        v = np.concatenate([v, np.zeros(width - v.size)])
    nrm = np.linalg.norm(v)
    return v / nrm if nrm > 1e-9 else v


def measure_track_bag(s, probe, cell_key):
    """The feature-MATCHED per-frame bag: 1-NN over the L2-flattened SAME trajectory
    feature (the unordered readout). Isolates temporal alignment from feature choice —
    this is what the DTW recognizer is compared against to credit the ALIGNMENT."""
    from domains.many_settings_recognizer import channel_likelihood
    # the per-frame channel count of this trajectory feature (formant=6 with velocity,
    # cmvn=n_bands) — used to give the bag readout a consistent fixed width.
    n_ch = 0
    for c in s.nodes("Concept"):
        for ex in s.neighbours(c, "has_exemplar"):
            tj = s.node(ex)["attrs"].get(EX_TRAJ_ATTR)
            if tj:
                n_ch = max(len(f) for f in tj)
                break
        if n_ch:
            break
    n_ch = n_ch or 3
    # gather banked exemplar bag-vectors + words.
    Xtr, words = [], []
    for c in s.nodes("Concept"):
        a = s.node(c)["attrs"]
        if a.get("origin") != "speech_world" or a.get("cell_key") != cell_key:
            continue
        cw = a.get("name")
        for ex in s.neighbours(c, "has_exemplar"):
            tj = s.node(ex)["attrs"].get(EX_TRAJ_ATTR)
            if tj is None:
                continue
            Xtr.append(_track_bag_vec([list(f) for f in tj], n_ch))
            words.append(cw)
    if not words:
        return 0.0
    Xtr = np.asarray(Xtr)
    candidate_words = sorted(set(words))
    tot = cor = 0
    for w, x, fs in probe:
        track = _extract_track(x, fs)
        q = _track_bag_vec(track, n_ch)
        p = channel_likelihood(q, Xtr, words, candidate_words)
        guess = max(p.items(), key=lambda kv: kv[1])[0] if p else None
        tot += 1
        cor += int(guess == w)
    return cor / max(tot, 1)


def measure_dtw(s, probe, cell_key):
    """Cross-speaker LOSO under the agent's DTW-trajectory recognizer. For each probe
    clip: extract its VTL formant trajectory (agent's feature), write it on a query
    node, evaluate the agent's Argmin-of-MinOver-DtwTo Term natively, read the word."""
    # one reusable query node; we overwrite its trajectory attr per probe.
    qn = s.add_node(QUERY_NODE_TYPE, {"origin": "dtw_probe"})
    term = _Pred(dtw_predict_term())
    tot = cor = 0
    for w, x, fs in probe:
        track = _extract_track(x, fs)
        s.set_attr(qn, QUERY_TRAJ_ATTR, _traj_tuple(track))
        pred = s.evaluate(term, {"q": qn})
        guess = s.node(pred)["attrs"].get("name") if pred is not None else None
        tot += 1
        cor += int(guess == w)
    s.remove_node(qn)
    return cor / max(tot, 1)


def fresh(active_cues, dyn_order=1):
    """A fresh substrate with the speech world + named cues gated into the front end.
    World-adapter construction (the same fresh() the prior LOSO scripts use)."""
    W.reset_caches()
    s = Substrate()
    pipe = STTPipeline(STTParams(sample_rate=FS))
    pipe.attach(s)
    pipe._ensure_audio_pipeline(s)
    W.install_speech_world_rules(s)
    W.install_cell(s, "digit", "sc", "en")
    for c in s.nodes("Cue"):
        a = s.node(c)["attrs"]
        if a.get("name") in active_cues:
            s.set_attr(c, "active", 1.0)
            if a.get("name") == "vtl_formant_dynamic":
                s.set_attr(c, "order", float(dyn_order))
    return s, pipe


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

    # ---- BAG baseline: the per-frame blind_guess on the static+dynamic best ----
    s_bag, _p = fresh(BAG_CUES, dyn_order=1)
    bank(s_bag, train_clips)
    bag_seen = measure(s_bag, seen_probe)
    bag_loso = measure(s_bag, loso_probe)
    print(f"\n[BAG          ] active cues={FE.n_active(s_bag)}  "
          f"seen-speaker {bag_seen:.3f}   cross-speaker LOSO {bag_loso:.3f}   "
          f"gap {bag_seen - bag_loso:+.3f}", flush=True)

    # ---- DTW-TRAJECTORY: the agent's graph-resident DtwTo recognizer ----
    # SAME banked exemplars; the trajectory is derived from the SAME audio. The front
    # end cues are irrelevant to the DTW recognizer (it reads the trajectory directly),
    # but we bank into a fresh substrate so the two regimes share nothing but the split.
    s_dtw, _p2 = fresh(BAG_CUES, dyn_order=1)
    bank(s_dtw, train_clips)
    n_traj = write_exemplar_trajectories(s_dtw, CELL)
    n_words = mark_words(s_dtw, CELL)
    print(f"[dtw setup    ] {n_traj} exemplar trajectories written, "
          f"{n_words} word Concepts marked is_word", flush=True)
    # feature-MATCHED control: the SAME trajectory feature as an unordered per-frame
    # bag (isolates temporal alignment from the feature choice).
    tbag_seen = measure_track_bag(s_dtw, seen_probe, CELL)
    tbag_loso = measure_track_bag(s_dtw, loso_probe, CELL)
    print(f"[TRACK-BAG    ] seen-speaker {tbag_seen:.3f}   "
          f"cross-speaker LOSO {tbag_loso:.3f}   "
          f"gap {tbag_seen - tbag_loso:+.3f}   (SAME trajectory, order thrown away)",
          flush=True)
    dtw_seen = measure_dtw(s_dtw, seen_probe, CELL)
    dtw_loso = measure_dtw(s_dtw, loso_probe, CELL)
    print(f"[DTW-TRAJECTORY] seen-speaker {dtw_seen:.3f}   "
          f"cross-speaker LOSO {dtw_loso:.3f}   "
          f"gap {dtw_seen - dtw_loso:+.3f}", flush=True)

    print("\n" + "=" * 74, flush=True)
    print(f"SPEECH-COMMANDS ROBUST CROSS-SPEAKER LOSO — DTW TRAJECTORY vs PER-FRAME "
          f"BAG  [traj={TRAJ_KIND}]", flush=True)
    print("=" * 74, flush=True)
    print(f"  {'regime':14s} {'seen':>8s} {'LOSO':>8s} {'seen-LOSO gap':>14s}",
          flush=True)
    print(f"  {'BAG(6-cue)':14s} {bag_seen:8.3f} {bag_loso:8.3f} "
          f"{bag_seen - bag_loso:14.3f}   (per-frame blind_guess, static+dynamic best)",
          flush=True)
    print(f"  {'TRACK-BAG':14s} {tbag_seen:8.3f} {tbag_loso:8.3f} "
          f"{tbag_seen - tbag_loso:14.3f}   (SAME trajectory feature, order discarded)",
          flush=True)
    print(f"  {'DTW-TRAJECTORY':14s} {dtw_seen:8.3f} {dtw_loso:8.3f} "
          f"{dtw_seen - dtw_loso:14.3f}   (Argmin MinOver DtwTo over the trajectory)",
          flush=True)
    print("-" * 74, flush=True)
    lift_abs = dtw_loso - bag_loso       # vs the full 6-cue per-frame BAG (absolute)
    lift_feat = dtw_loso - tbag_loso     # vs the SAME feature as a bag (isolated)
    print(f"  chance {chance:.3f}", flush=True)
    print(f"  DTW vs 6-cue BAG (absolute):       {lift_abs:+.3f} "
          f"(BAG {bag_loso:.3f} -> DTW {dtw_loso:.3f})", flush=True)
    print(f"  DTW vs SAME-feature TRACK-BAG:      {lift_feat:+.3f} "
          f"(TRACK-BAG {tbag_loso:.3f} -> DTW {dtw_loso:.3f}) "
          f"<- the isolated TEMPORAL-ALIGNMENT effect", flush=True)
    # the decisive credit goes to alignment-vs-same-feature-bag; the absolute lift is
    # reported against the doc's 6-cue baseline.
    if lift_abs > 0.02:
        verdict = ("YES", f"the DTW temporal-alignment recognizer LIFTS absolute "
                   f"cross-speaker LOSO +{lift_abs:.3f} above the per-frame 6-cue bag — "
                   f"aligning the gesture TRAJECTORY recognizes the speaker-invariant "
                   f"gesture better than the unordered per-frame readout.")
    elif lift_abs > 0.005:
        verdict = ("PARTIAL", f"the DTW recognizer moves absolute cross-speaker LOSO "
                   f"above the 6-cue bag ({lift_abs:+.3f}); on the SAME feature the "
                   f"alignment effect is {lift_feat:+.3f}.")
    else:
        verdict = ("NO", f"the DTW temporal-alignment recognizer does NOT lift absolute "
                   f"cross-speaker LOSO above the 6-cue bag ({lift_abs:+.3f}); on the "
                   f"SAME trajectory feature the alignment effect is {lift_feat:+.3f}. "
                   f"The residual is not the recognizer's loss of temporal order.")
    print(f"  => {verdict[0]}: {verdict[1]}", flush=True)
    print(f"  => RESIDUAL: DTW LOSO {dtw_loso:.3f} vs chance {chance:.3f}; "
          f"still {1.0 - dtw_loso:.3f} from solved (1.000).", flush=True)
    print("[MARKER] DTW_TRAJECTORY_LOSO_COMPLETE", flush=True)


if __name__ == "__main__":
    main()

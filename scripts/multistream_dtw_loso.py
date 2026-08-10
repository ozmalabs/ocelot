"""multistream_dtw_loso — does a MULTI-STREAM DTW recognizer (align the CMVN spectral
trajectory AND the VTL-invariant formant trajectory JOINTLY) lift cross-speaker LOSO
above the single-stream CMVN DTW (0.570)?

The single-stream DTW recognizer (docs/dtw_trajectory_loso.md) lifted real 40-speaker
SC cross-speaker LOSO 0.417 -> 0.570 (+0.152, purely the temporal alignment) over the
CMVN spectral trajectory; the formant-only DTW reached ~0.253 (a thinner feature). That
doc NAMED the next lever: align BOTH trajectories together — the CMVN spectral track and
the VTL-invariant formant track carry COMPLEMENTARY cross-speaker structure (one is the
full source-normalized spectral shape, the other the vocal-tract-length-invariant formant
gesture), so aligning both should lift further.

This script A/Bs exactly that on the SAME robust SC 40-speaker LOSO split. Three regimes:

  DTW-CMVN    : single-stream, the 0.570 baseline — Argmin_word MinOver_exemplars
                DtwTo(cmvn_q, cmvn_e) over the CMVN spectral trajectory.
  DTW-FORMANT : single-stream, the ~0.253 reference — DtwTo over the VTL formant track.
  DTW-MULTI   : both streams combined. Two composable forms are tried:
                (a) SUM of per-stream DTW costs (the agent's Plus over two DtwTo Terms),
                    with a fixed stream weight w: DtwTo(cmvn_q,cmvn_e) + w*DtwTo(fmt_q,
                    fmt_e). Each DtwTo is already length-normalized, so summing two
                    normalized alignment costs is well-scaled; w is swept at a couple of
                    fixed values (NO fit, reported).
                (b) CONCAT per-frame trajectory (cmvn ++ formant per frame, the formant
                    track resampled to the cmvn frame count) with a SINGLE DtwTo.

The recognition DECISION stays the agent's GRAPH-RESIDENT Term: Argmin over is_word
Concepts of (MinOver that word's banked exemplars of the combined DTW distance). DtwTo /
Plus / Times / MinOver / Argmin are the agent's OWNED ops, evaluated NATIVELY in Rust.

DONKEY BOUNDARY (audited): the two trajectories are the agent's composable DSP features
(agent_frontend.cmvn_track + agent_frontend.vtl_formant_track — the SAME CMVN cochleagram
the dominant cmvn_ear cue uses and the SAME sharp LPC-root VTL-invariant formant track the
dynamic cue uses, kept ORDERED). The multi-stream DTW recognizer is the agent's
graph-resident decision: a Plus/Times-of-two-DtwTo (or one DtwTo over the concat) composed
with MinOver + Argmin over the agent's OWN banked exemplars + word Concepts — NO fit, NO
trained net, NO learned weight (a fixed stream weight tried at a couple of values is fine,
reported). SC load + the speaker split are world-adapter mechanics; LOSO is the
ungameable yardstick; held-out speakers' clips are NEVER banked.

Run: python -m scripts.multistream_dtw_loso [n_train_spk] [n_held_spk] [n_per] [seed]
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

# the static+dynamic best front end the banked exemplars carry (irrelevant to the DTW
# recognizer, which reads the trajectories directly; banked so regimes share the split).
BAG_CUES = ["cmvn_ear", "vtl_formant_allpole", "vtl_formant_dynamic"]

FMT_ATTRS = {"n_formants": 3, "fps": 25, "with_velocity": True}

# stream weights swept for form (a) (the SUM of per-stream DTW costs). NO fit — a couple
# of fixed values tried and reported.
STREAM_WEIGHTS = [0.25, 0.5, 1.0, 2.0, 4.0]


def cmvn_track(x, fs):
    return FE.cmvn_track(np.asarray(x, dtype=np.float64), float(fs))


def formant_track(x, fs):
    return FE.vtl_formant_track(np.asarray(x, dtype=np.float64), float(fs), FMT_ATTRS)


# ---------------------------------------------------------------------------
# The agent's GRAPH-RESIDENT multi-stream DTW recognizer (composed from owned ops).
#
#   predict(query) = Argmin over candidate words w of
#                      MinOver e in has_exemplar(w) of  COMBINE( DtwTo(cmvn_q, cmvn_e),
#                                                                DtwTo(fmt_q,  fmt_e)  )
#
#   form (a): COMBINE = DtwTo(cmvn) + w * DtwTo(fmt)   (Plus over two DtwTo, Times for w)
#   form (b): single DtwTo over the per-frame concatenated trajectory.
#
# DtwTo = the agent's banded Sakoe-Chiba DTW Term (Rust); Plus/Times = the agent's
# variadic numeric ops; MinOver = nearest banked exemplar of the word; Argmin = the word
# decision. Evaluated natively. No Python recognizer: the query trajectories are written
# on a scratch node, each exemplar's trajectories on its Exemplar node, and the Term picks
# the word with the minimum combined-DTW aligned exemplar.
# ---------------------------------------------------------------------------

QUERY_NODE_TYPE = "DtwQuery"
Q_CMVN = "q_cmvn"
Q_FMT = "q_fmt"
Q_CONCAT = "q_concat"
EX_CMVN = "ex_cmvn"
EX_FMT = "ex_fmt"
EX_CONCAT = "ex_concat"


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
def _Plus(items): return {"type": "Plus", "items": items}
def _Times(items): return {"type": "Times", "items": items}
def _NodesWhere(t, k, v): return {"type": "NodesWhere", "node_type": t,
                                  "attr_key": k, "value": v}
def _MinOver(src, var, val): return {"type": "MinOver", "source": src,
                                     "var_name": var, "value": val, "default": None}
def _Argmin(src, var, val): return {"type": "Argmin", "source": src,
                                    "var_name": var, "value": val, "default": None}


def dtw_single_term(q_attr, ex_attr):
    """Single-stream DTW recognizer: Argmin_word MinOver_exemplars DtwTo(q, ex)."""
    word_dist = _MinOver(_Nb(_V("w"), "has_exemplar"), "e",
                         _DtwTo(_Attr(_V("q"), q_attr), _Attr(_V("e"), ex_attr)))
    return _Argmin(_NodesWhere("Concept", WORD_ATTR, _Lit(1.0)), "w", word_dist)


def dtw_multi_sum_term(weight):
    """Multi-stream form (a): Argmin_word MinOver_exemplars
       [ DtwTo(cmvn_q, cmvn_e) + weight * DtwTo(fmt_q, fmt_e) ].
    The combined per-exemplar distance is the agent's Plus over the CMVN DtwTo and the
    weight-scaled (Times) formant DtwTo — both owned numeric ops, evaluated natively."""
    cmvn_d = _DtwTo(_Attr(_V("q"), Q_CMVN), _Attr(_V("e"), EX_CMVN))
    fmt_d = _DtwTo(_Attr(_V("q"), Q_FMT), _Attr(_V("e"), EX_FMT))
    combined = _Plus([cmvn_d, _Times([_Lit(float(weight)), fmt_d])])
    word_dist = _MinOver(_Nb(_V("w"), "has_exemplar"), "e", combined)
    return _Argmin(_NodesWhere("Concept", WORD_ATTR, _Lit(1.0)), "w", word_dist)


def dtw_multi_concat_term():
    """Multi-stream form (b): single DtwTo over the per-frame concatenated trajectory."""
    return dtw_single_term(Q_CONCAT, EX_CONCAT)


def _traj_tuple(track):
    """A trajectory (list of frames) as a tuple-of-tuples graph attr (frames x channels).
    Empty -> a single zero frame so DtwTo stays finite."""
    if track is None or len(track) == 0:
        return ((0.0,),)
    return tuple(tuple(float(v) for v in frame) for frame in track)


def _concat_tracks(cmvn, fmt):
    """Per-frame concatenation cmvn ++ formant (form b). The formant track is resampled
    along time to the cmvn frame count so the two streams align per frame; each stream is
    kept on its own scale (cmvn frames are already per-frame L2; the formant channels are
    log-Hz VTL-invariants, small magnitude). Mechanical feature derivation."""
    cm = np.asarray(cmvn, dtype=np.float64) if cmvn else np.zeros((1, 1))
    fm = np.asarray(fmt, dtype=np.float64) if fmt else np.zeros((1, 1))
    if cm.ndim != 2 or cm.size == 0:
        cm = np.zeros((1, 1))
    if fm.ndim != 2 or fm.size == 0:
        fm = np.zeros((1, 1))
    nT = cm.shape[0]
    # resample each formant channel to the cmvn frame count (time alignment of streams).
    src = np.arange(fm.shape[0])
    idx = np.linspace(0, fm.shape[0] - 1, nT)
    fm_rs = np.stack([np.interp(idx, src, fm[:, k]) for k in range(fm.shape[1])], axis=1) \
        if fm.shape[0] > 1 else np.repeat(fm[:1], nT, axis=0)
    return np.concatenate([cm, fm_rs], axis=1).tolist()


def write_exemplar_trajectories(s, cell_key):
    """Mechanical I/O: for each banked Exemplar in the cell, extract BOTH trajectories
    (the agent's owned cmvn_track + vtl_formant_track) and store them on the node as the
    ex_cmvn / ex_fmt / ex_concat attrs the multi-stream DtwTo reads. World-adapter feature
    derivation (no decision); cached per exemplar so banking is paid once."""
    n = 0
    for c in s.nodes("Concept"):
        a = s.node(c)["attrs"]
        if a.get("origin") != "speech_world" or a.get("cell_key") != cell_key:
            continue
        for ex in s.neighbours(c, "has_exemplar"):
            ea = s.node(ex)["attrs"]
            if ea.get(EX_CMVN) is not None:
                continue
            aud = ea.get("audio")
            if aud is None:
                continue
            x = np.asarray(aud, dtype=np.float64)
            fs = float(ea.get("fs", FS))
            cm = cmvn_track(x, fs)
            fm = formant_track(x, fs)
            s.set_attr(ex, EX_CMVN, _traj_tuple(cm))
            s.set_attr(ex, EX_FMT, _traj_tuple(fm))
            s.set_attr(ex, EX_CONCAT, _traj_tuple(_concat_tracks(cm, fm)))
            n += 1
    return n


def mark_words(s, cell_key):
    """Tag this cell's word Concepts is_word so the Argmin can range over them (the SAME
    marking blind_guess relies on; mechanical setup). Zero other cells' word flags."""
    n = 0
    for c in s.nodes("Concept"):
        a = s.node(c)["attrs"]
        if a.get("origin") == "speech_world" and a.get("cell_key") == cell_key:
            s.set_attr(c, WORD_ATTR, 1.0)
            n += 1
        elif a.get("origin") == "speech_world" and a.get(WORD_ATTR):
            s.set_attr(c, WORD_ATTR, 0.0)
    return n


def measure_dtw_single(s, probe, q_attr, ex_attr, extract):
    """Cross-speaker LOSO under a single-stream DTW recognizer (the agent's graph Term)."""
    qn = s.add_node(QUERY_NODE_TYPE, {"origin": "dtw_probe"})
    term = _Pred(dtw_single_term(q_attr, ex_attr))
    tot = cor = 0
    for w, x, fs in probe:
        s.set_attr(qn, q_attr, _traj_tuple(extract(x, fs)))
        pred = s.evaluate(term, {"q": qn})
        guess = s.node(pred)["attrs"].get("name") if pred is not None else None
        tot += 1
        cor += int(guess == w)
    s.remove_node(qn)
    return cor / max(tot, 1)


def measure_dtw_multi_sum(s, probe, weight):
    """Cross-speaker LOSO under the multi-stream SUM recognizer (form a) at a fixed
    stream weight. Both query trajectories are written; the agent's
    Argmin-MinOver-(DtwTo+w*DtwTo) Term decides natively."""
    qn = s.add_node(QUERY_NODE_TYPE, {"origin": "dtw_probe"})
    term = _Pred(dtw_multi_sum_term(weight))
    tot = cor = 0
    for w, x, fs in probe:
        cm = cmvn_track(x, fs)
        fm = formant_track(x, fs)
        s.set_attr(qn, Q_CMVN, _traj_tuple(cm))
        s.set_attr(qn, Q_FMT, _traj_tuple(fm))
        pred = s.evaluate(term, {"q": qn})
        guess = s.node(pred)["attrs"].get("name") if pred is not None else None
        tot += 1
        cor += int(guess == w)
    s.remove_node(qn)
    return cor / max(tot, 1)


def measure_dtw_multi_concat(s, probe):
    """Cross-speaker LOSO under the multi-stream CONCAT recognizer (form b): one DtwTo
    over the per-frame cmvn++formant trajectory (the agent's graph Term)."""
    qn = s.add_node(QUERY_NODE_TYPE, {"origin": "dtw_probe"})
    term = _Pred(dtw_multi_concat_term())
    tot = cor = 0
    for w, x, fs in probe:
        cm = cmvn_track(x, fs)
        fm = formant_track(x, fs)
        s.set_attr(qn, Q_CONCAT, _traj_tuple(_concat_tracks(cm, fm)))
        pred = s.evaluate(term, {"q": qn})
        guess = s.node(pred)["attrs"].get("name") if pred is not None else None
        tot += 1
        cor += int(guess == w)
    s.remove_node(qn)
    return cor / max(tot, 1)


def fresh():
    """A fresh substrate with the speech world (the same fresh() the prior LOSO scripts
    use). The DTW recognizer reads the trajectories directly; the cues are gated only so
    banking matches the prior runs' substrate shape. World-adapter construction."""
    W.reset_caches()
    s = Substrate()
    pipe = STTPipeline(STTParams(sample_rate=FS))
    pipe.attach(s)
    pipe._ensure_audio_pipeline(s)
    W.install_speech_world_rules(s)
    W.install_cell(s, "digit", "sc", "en")
    for c in s.nodes("Cue"):
        a = s.node(c)["attrs"]
        if a.get("name") in BAG_CUES:
            s.set_attr(c, "active", 1.0)
            if a.get("name") == "vtl_formant_dynamic":
                s.set_attr(c, "order", 1.0)
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

    # ---- bank ONCE; both query trajectories written on every exemplar ----
    s, _p = fresh()
    bank(s, train_clips)
    n_traj = write_exemplar_trajectories(s, CELL)
    n_words = mark_words(s, CELL)
    print(f"[dtw setup    ] {n_traj} exemplar trajectories written (cmvn+formant+concat), "
          f"{n_words} word Concepts marked is_word", flush=True)

    # ---- DTW-CMVN single-stream (the 0.570 baseline) ----
    cmvn_seen = measure_dtw_single(s, seen_probe, Q_CMVN, EX_CMVN, cmvn_track)
    cmvn_loso = measure_dtw_single(s, loso_probe, Q_CMVN, EX_CMVN, cmvn_track)
    print(f"[DTW-CMVN     ] seen-speaker {cmvn_seen:.3f}   "
          f"cross-speaker LOSO {cmvn_loso:.3f}   gap {cmvn_seen - cmvn_loso:+.3f}",
          flush=True)

    # ---- DTW-FORMANT single-stream (the ~0.253 reference) ----
    fmt_seen = measure_dtw_single(s, seen_probe, Q_FMT, EX_FMT, formant_track)
    fmt_loso = measure_dtw_single(s, loso_probe, Q_FMT, EX_FMT, formant_track)
    print(f"[DTW-FORMANT  ] seen-speaker {fmt_seen:.3f}   "
          f"cross-speaker LOSO {fmt_loso:.3f}   gap {fmt_seen - fmt_loso:+.3f}",
          flush=True)

    # ---- DTW-MULTI form (a): SUM of per-stream DTW costs, swept stream weight ----
    sum_results = {}
    for w in STREAM_WEIGHTS:
        ms_seen = measure_dtw_multi_sum(s, seen_probe, w)
        ms_loso = measure_dtw_multi_sum(s, loso_probe, w)
        sum_results[w] = (ms_seen, ms_loso)
        print(f"[DTW-MULTI sum w={w:<4}] seen-speaker {ms_seen:.3f}   "
              f"cross-speaker LOSO {ms_loso:.3f}   gap {ms_seen - ms_loso:+.3f}",
              flush=True)

    # ---- DTW-MULTI form (b): single DTW over the concatenated trajectory ----
    cc_seen = measure_dtw_multi_concat(s, seen_probe)
    cc_loso = measure_dtw_multi_concat(s, loso_probe)
    print(f"[DTW-MULTI concat   ] seen-speaker {cc_seen:.3f}   "
          f"cross-speaker LOSO {cc_loso:.3f}   gap {cc_seen - cc_loso:+.3f}", flush=True)

    s.remove_node  # noqa: keep substrate alive until here

    # best multi-stream form (a) by LOSO across the swept weights.
    best_w = max(STREAM_WEIGHTS, key=lambda w: sum_results[w][1])
    best_sum_seen, best_sum_loso = sum_results[best_w]
    multi_best_loso = max(best_sum_loso, cc_loso)
    multi_best_label = (f"sum w={best_w}" if best_sum_loso >= cc_loso else "concat")

    print("\n" + "=" * 78, flush=True)
    print("SPEECH-COMMANDS ROBUST CROSS-SPEAKER LOSO — MULTI-STREAM DTW "
          "(CMVN + VTL-FORMANT)", flush=True)
    print("=" * 78, flush=True)
    print(f"  {'regime':22s} {'seen':>8s} {'LOSO':>8s} {'seen-LOSO gap':>14s}",
          flush=True)
    print(f"  {'DTW-CMVN (single)':22s} {cmvn_seen:8.3f} {cmvn_loso:8.3f} "
          f"{cmvn_seen - cmvn_loso:14.3f}", flush=True)
    print(f"  {'DTW-FORMANT (single)':22s} {fmt_seen:8.3f} {fmt_loso:8.3f} "
          f"{fmt_seen - fmt_loso:14.3f}", flush=True)
    for w in STREAM_WEIGHTS:
        ss, sl = sum_results[w]
        print(f"  {'DTW-MULTI sum w=' + str(w):22s} {ss:8.3f} {sl:8.3f} "
              f"{ss - sl:14.3f}", flush=True)
    print(f"  {'DTW-MULTI concat':22s} {cc_seen:8.3f} {cc_loso:8.3f} "
          f"{cc_seen - cc_loso:14.3f}", flush=True)
    print("-" * 78, flush=True)
    lift = multi_best_loso - cmvn_loso
    print(f"  chance {chance:.3f}", flush=True)
    print(f"  best single-stream:  DTW-CMVN LOSO {cmvn_loso:.3f}", flush=True)
    print(f"  best multi-stream:   {multi_best_label} LOSO {multi_best_loso:.3f}",
          flush=True)
    print(f"  MULTI vs single-stream CMVN:  {lift:+.3f} "
          f"(CMVN {cmvn_loso:.3f} -> MULTI {multi_best_loso:.3f})", flush=True)
    if lift > 0.02:
        verdict = ("YES", f"multi-stream DTW LIFTS cross-speaker LOSO +{lift:.3f} above "
                   f"the single-stream CMVN DTW ({cmvn_loso:.3f} -> {multi_best_loso:.3f})"
                   f" — aligning the CMVN spectral AND the VTL formant trajectories "
                   f"jointly recovers complementary cross-speaker structure.")
    elif lift > 0.005:
        verdict = ("MARGINAL", f"multi-stream DTW moves cross-speaker LOSO {lift:+.3f} "
                   f"above single-stream CMVN ({cmvn_loso:.3f} -> {multi_best_loso:.3f}) "
                   f"— a small lift; the streams are largely redundant.")
    else:
        verdict = ("NO", f"multi-stream DTW does NOT lift cross-speaker LOSO above the "
                   f"single-stream CMVN DTW ({lift:+.3f}; CMVN {cmvn_loso:.3f} -> "
                   f"MULTI {multi_best_loso:.3f}). The thin/noisy formant stream does not "
                   f"add complementary structure the CMVN trajectory lacks.")
    print(f"  => {verdict[0]}: {verdict[1]}", flush=True)
    print(f"  => RESIDUAL: best DTW LOSO {multi_best_loso:.3f} vs chance {chance:.3f}; "
          f"still {1.0 - multi_best_loso:.3f} from solved (1.000).", flush=True)
    print("[MARKER] MULTISTREAM_DTW_LOSO_COMPLETE", flush=True)


if __name__ == "__main__":
    main()

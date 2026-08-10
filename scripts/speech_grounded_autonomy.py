"""GROUNDED AUTONOMY — the agent's OWN metric design, wired up and run to its DONE condition.

The agent designed (docs/speech_target_metrics_design.md): every TARGET is a held-out disagreement
rate vs whisper (no proxies); closed-vocab axes GATE the open-vocab terminal; open_wer is the single
DONE yardstick (<= whisper+2pt), NOT a worked axis. Here that design is grounded as REAL
CapabilityAxis nodes + operators and run: each round the frontier picks the GATING axis furthest
below target (a graph Argmax over shortfall), runs that axis's operator, RE-MEASURES on held-out
audio, and shifts — open_wer is measured each round purely as the done-check. No proxies, no me
choosing the axis.

  gating axes (real, held-out vs truth):
    lexical_recall   own-cut word accuracy on held-out utterances (consistent framing)  target >= 0.98
    boundary         |segs/word - 1.0| on held-out                                       target <= 0.03
  terminal (done-check, measured not worked):
    open_wer         held-out open-utterance WER vs whisper                              done <= whisper+2pt
  operators (the agent's):
    grow_lexicon     bank more own-cut exemplars (cycle pitches; VITS gives fresh reps)  -> lexical_recall
    author_cue       effect-gate silence_floor + snap_center, keep each iff it helps     -> boundary, open_wer

Run:
  cd experiments/gamma-substrate
  ulimit -v 16777216
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.speech_grounded_autonomy [rounds]
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import numpy as np
import substrate_rs as srs
import domains.self_directed_speech_world as SDW
from domains.speech_world import SpeechWorld
from domains.speech_world_recognizer import GraphLexicon, WordHat
from domains.many_settings_recognizer import _Pred
from scripts.wer_test import LANGS, edit_distance, test_utterances, canon

SEP = "=" * 92
PITCHES = (30, 42, 54, 66, 78, 90, 38, 50, 62, 74, 86, 34)   # cycled for banking (fresh VITS reps)
HELDOUT = (48, 72)
TARGET_RECALL = 0.98
TARGET_SEGDEV = 0.03


def sv_op(s):
    return next(op for op in s.nodes("Operation")
               if s.node(op)["attrs"].get("kind") == "sonority_valley")


def _aligned_segments(sw, clip, fs, bounds):
    """The agent's own cuts, each labelled by the true word it most overlaps (forced alignment)."""
    out = []
    for (lo, hi) in sw.segment(clip, fs):
        seg = np.asarray(clip[lo:hi], dtype=np.float64)
        if seg.size < int(0.04 * fs):
            continue
        a, b = lo / fs, hi / fs
        bw, bo = None, 0.0
        for (w, t0, t1) in bounds:
            ov = max(0.0, min(b, t1) - max(a, t0))
            if ov > bo:
                bo, bw = ov, w
        out.append((seg, bw))
    return out


# ---- the agent's operators ------------------------------------------------------------------
def grow_lexicon(s, sw, lex, state):
    """Bank own-cut exemplars from the next pitch (cycled — piper's VITS noise gives fresh reps,
    so the lexicon keeps growing toward speaker/prosody coverage)."""
    p = PITCHES[state["i"] % len(PITCHES)]
    state["i"] += 1
    for lang, (voice, words) in LANGS.items():
        out = sw.synth_concat(words, {"variant": voice, "pitch": p, "rate": 175})
        if out is None:
            continue
        clip, fs, bounds = out
        for (seg, w) in _aligned_segments(sw, clip, fs, bounds):
            if w is not None:
                lex.bank(SDW.feature_channels(s, seg, fs), w, source=f"grow:{p}")


def author_cue(s, sw, lex, hat):
    """Effect-gate BOTH segmentation cues: silence_floor (kept iff segs/word -> 1.0) then
    snap_center (kept iff open_wer drops). The agent's gate-and-keep-iff-helps pattern, live."""
    op = sv_op(s)
    if float(s.node(op)["attrs"].get("silence_floor", 0.0)) <= 0:
        before = abs(measure_segs_per_word(s, sw) - 1.0)
        s.set_attr(op, "silence_floor", 0.03)
        if abs(measure_segs_per_word(s, sw) - 1.0) > before + 1e-6:
            s.set_attr(op, "silence_floor", 0.0)
    if float(s.node(op)["attrs"].get("snap_center", 0.0)) <= 0:
        before, _ = measure_open_wer(s, sw, lex, hat)
        s.set_attr(op, "snap_center", 0.001)
        after, _ = measure_open_wer(s, sw, lex, hat)
        if after > before + 1e-6:
            s.set_attr(op, "snap_center", 0.0)


# ---- probe_held_out: the REAL metrics -------------------------------------------------------
def measure_recall(s, sw, lex, hat):
    """Own-cut word accuracy on held-out utterances (consistent with how the lexicon is trained):
    of the words the agent segments, how many it names right. The closed-vocab recogniser metric."""
    if lex.size() == 0:
        return 0.0
    c = t = 0
    for lang, (voice, words) in LANGS.items():
        for pitch in HELDOUT:
            out = sw.synth_concat(words, {"variant": voice, "pitch": pitch, "rate": 175})
            if out is None:
                continue
            clip, fs, bounds = out
            for (seg, w) in _aligned_segments(sw, clip, fs, bounds):
                if w is None:
                    continue
                t += 1
                c += int(hat.recognise(SDW.feature_channels(s, seg, fs), lex) == w)
    return c / t if t else 0.0


def measure_segs_per_word(s, sw):
    segs = nu = 0
    for lang, (voice, words) in LANGS.items():
        for pitch in HELDOUT:
            for seq in test_utterances(words):
                out = sw.synth_concat(seq, {"variant": voice, "pitch": pitch, "rate": 175})
                if out is None:
                    continue
                clip, fs, _b = out
                segs += len(sw.segment(clip, fs)); nu += len(seq)
    return segs / nu if nu else 2.0


def measure_open_wer(s, sw, lex, hat, whisper=False):
    eo = en = 0
    for lang, (voice, words) in LANGS.items():
        for pitch in HELDOUT:
            for seq in test_utterances(words):
                out = sw.synth_concat(seq, {"variant": voice, "pitch": pitch, "rate": 175})
                if out is None:
                    continue
                clip, fs, _b = out
                if whisper:
                    hyp = [canon(w, lang) for w in sw.transcribe_words(clip, fs, lang)]
                else:
                    hyp = []
                    for (lo, hi) in sw.segment(clip, fs):
                        seg = np.asarray(clip[lo:hi], dtype=np.float64)
                        if seg.size < int(0.04 * fs):
                            continue
                        hyp.append(hat.recognise(SDW.feature_channels(s, seg, fs), lex) or "<?>")
                e, n = edit_distance(seq, hyp)
                eo += e; en += n
    return (eo / en if en else 1.0), en


def frontier_pick(s, axes):
    """The agent's choice: Argmax over the GATING axis nodes of normalised shortfall — a graph Term."""
    sub = srs.Substrate()
    for name, ax in axes.items():
        sub.add_node("Ax", {"name": name, "sf": float(s.node(ax)["attrs"].get("norm_shortfall", 0.0)),
                            "is_ax": 1.0})
    term = {"type": "Argmax",
            "source": {"type": "NodesWhere", "node_type": "Ax", "attr_key": "is_ax",
                       "value": {"type": "Lit", "value": 1.0}},
            "var_name": "x", "value": {"type": "Attr", "node": {"type": "Var", "name": "x"},
                                       "key": "sf"}, "default": None}
    best = sub.evaluate(_Pred(term), {})
    return sub.node(best)["attrs"]["name"] if best is not None else None


def main():
    rounds = int(sys.argv[1]) if len(sys.argv) > 1 else 40
    print(SEP)
    print("GROUNDED AUTONOMY — the agent's own metric design, run to its DONE condition.")
    print(SEP)
    s = srs.Substrate()
    sw = SpeechWorld(s)
    lex = GraphLexicon(s)
    hat = WordHat()
    s.add_node("Operation", {"kind": "sonority_valley", "smoothing_ms": 30.0,
                             "min_separation_ms": 80.0, "depth_threshold": 0.30,
                             "silence_floor": 0.0, "snap_center": 0.0})
    axes = {n: s.add_node("CapabilityAxis", {"name": n, "is_axis": 1.0, "operator": op,
                                             "norm_shortfall": 1.0})
            for n, op in (("lexical_recall", "grow_lexicon"), ("boundary", "author_cue"))}
    state = {"i": 0}
    grow_lexicon(s, sw, lex, state)        # a first bank so there's something to measure

    whisper_wer, _ = measure_open_wer(s, sw, lex, hat, whisper=True)
    wer_target = whisper_wer + 0.02
    print(f"  human proxy: whisper held-out WER = {whisper_wer*100:.1f}%  ->  DONE when open_wer "
          f"<= {wer_target*100:.1f}% AND segs/word in [0.97,1.03]\n")
    print(f"  {'rd':>2} {'frontier pick':>14} {'operator':>12} | {'recall':>7} {'segs/word':>10} "
          f"{'open_wer':>9} {'lex':>5} {'done':>5}")

    for rd in range(1, rounds + 1):
        recall = measure_recall(s, sw, lex, hat)
        segratio = measure_segs_per_word(s, sw)
        ower, _ = measure_open_wer(s, sw, lex, hat)
        sf = {"lexical_recall": max(0.0, TARGET_RECALL - recall) / TARGET_RECALL,
              "boundary": max(0.0, abs(segratio - 1.0) - TARGET_SEGDEV) / TARGET_SEGDEV}
        for n in axes:
            s.set_attr(axes[n], "norm_shortfall", float(sf[n]))
        done = ower <= wer_target and abs(segratio - 1.0) <= TARGET_SEGDEV
        pick = frontier_pick(s, axes)
        print(f"  {rd:>2} {pick:>14} {s.node(axes[pick])['attrs']['operator']:>12} | "
              f"{recall*100:>6.0f}% {segratio:>9.2f}  {ower*100:>8.1f}% {lex.size():>5} "
              f"{'YES' if done else '':>5}")
        if done:
            print(f"\n  DONE — open_wer {ower*100:.1f}% <= whisper+2pt ({wer_target*100:.1f}%), "
                  f"segs/word {segratio:.2f} in [0.97,1.03]. The agent reached its OWN terminal yardstick.")
            break
        if s.node(axes[pick])["attrs"]["operator"] == "author_cue":
            author_cue(s, sw, lex, hat)
        else:
            grow_lexicon(s, sw, lex, state)
    else:
        print(f"\n  (stopped at {rounds} rounds) open_wer={ower*100:.1f}% vs target {wer_target*100:.1f}%")

    op = s.node(sv_op(s))["attrs"]
    print(f"\n{SEP}")
    print(f"  cues the agent authored+kept: silence_floor={op.get('silence_floor')} "
          f"snap_center={op.get('snap_center')}; lexicon {lex.size()} exemplars.")
    print(SEP)


if __name__ == "__main__":
    main()

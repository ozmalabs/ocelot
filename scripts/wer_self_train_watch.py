"""WATCH THE JABBERWOCK SELF-TRAIN — just let its own loop run and see what it figures out.

No hand-authoring, no hand-tuning. Each round the agent HEARS connected multilingual speech
through its real STT pipeline (which self-tunes its sonority depth_threshold via its own Rules)
AND banks exemplars from the pieces IT segments (forced-aligned to the transcript). Every few
rounds we checkpoint what it has become: its segmentation threshold, how many cuts per word it
makes, its lexicon's singleton-fraction, and its held-out open-utterance WER. We just observe the
trajectory — does more self-training resolve the over-segmentation on its own?

Run:
  cd experiments/gamma-substrate
  ulimit -v 16777216
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.wer_self_train_watch [rounds]
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
from domains.stt_pipeline import STTPipeline, STTParams
from scripts.wer_test import LANGS, edit_distance, test_utterances, canon

SEP = "=" * 92


def sv_threshold(s):
    for op in s.nodes("Operation"):
        a = s.node(op)["attrs"]
        if a.get("kind") == "sonority_valley":
            return float(a.get("depth_threshold", 0.30))
    return 0.30


def singleton_fraction(s):
    for lx in s.nodes("AcousticLexicon"):
        ent = s.neighbours(lx, "has_entry")
        n = len(ent)
        if not n:
            return 0.0
        return sum(1 for e in ent if s.node(e)["attrs"].get("hearings") == 1) / n
    return 0.0


def bank_from_own_cuts(s, sw, lex, voice, words, pitch):
    """Bank the agent's OWN segmented pieces, forced-aligned to the transcript by overlap."""
    out = sw.synth_concat(words, {"variant": voice, "pitch": pitch, "rate": 175})
    if out is None:
        return
    clip, fs, bounds = out
    for (lo, hi) in sw.segment(clip, fs):
        seg = np.asarray(clip[lo:hi], dtype=np.float64)
        if seg.size < int(0.04 * fs):
            continue
        a, b = lo / fs, hi / fs
        best_w, best_ov = None, 0.0
        for (w, t0, t1) in bounds:
            ov = max(0.0, min(b, t1) - max(a, t0))
            if ov > best_ov:
                best_ov, best_w = ov, w
        if best_w is not None:
            lex.bank(SDW.feature_channels(s, seg, fs), best_w, source=f"owncut:{voice}:{pitch}")


def evaluate(s, sw, lex, hat, pitches=(48, 72)):
    """Held-out open-utterance WER + segs/word, small set for speed."""
    eo = en = 0
    segs = nutt = 0
    for lang, (voice, words) in LANGS.items():
        for pitch in pitches:
            for seq in test_utterances(words):
                out = sw.synth_concat(seq, {"variant": voice, "pitch": pitch, "rate": 175})
                if out is None:
                    continue
                clip, fs, _b = out
                spans = sw.segment(clip, fs)
                segs += len(spans); nutt += len(seq)
                hyp = []
                for (lo, hi) in spans:
                    seg = np.asarray(clip[lo:hi], dtype=np.float64)
                    if seg.size < int(0.04 * fs):
                        continue
                    hyp.append(hat.recognise(SDW.feature_channels(s, seg, fs), lex) or "<?>")
                e, n = edit_distance(seq, hyp)
                eo += e; en += n
    return (eo / en if en else 1.0), (segs / nutt if nutt else 0.0)


def main():
    rounds = int(sys.argv[1]) if len(sys.argv) > 1 else 40
    floor = float(sys.argv[2]) if len(sys.argv) > 2 else 0.0   # the authored silence cue (0 = off)
    snap = float(sys.argv[3]) if len(sys.argv) > 3 else 0.0    # the authored placement cue (0 = off)
    print(SEP)
    print("WATCH THE JABBERWOCK SELF-TRAIN — its own loop, observe what it figures out.")
    print(f"  (authored cues: silence_floor = {floor}, snap_center = {snap})")
    print(SEP)
    s = srs.Substrate()
    sw = SpeechWorld(s)
    lex = GraphLexicon(s)
    hat = WordHat()
    pipe = STTPipeline(STTParams(sample_rate=8000))
    pipe.attach(s)

    def apply_floor():                  # keep the authored cues switched ON for the segmenter
        if floor <= 0 and snap <= 0:
            return
        for op in s.nodes("Operation"):
            if s.node(op)["attrs"].get("kind") == "sonority_valley":
                if floor > 0:
                    s.set_attr(op, "silence_floor", floor)
                if snap > 0:
                    s.set_attr(op, "snap_center", snap)

    print(f"  {'round':>5} {'clips':>6} {'depth_thr':>10} {'singleton':>10} {'lex':>6} "
          f"{'segs/word':>10} {'open_WER':>9}")
    clips = 0
    for rnd in range(1, rounds + 1):
        for lang, (voice, words) in LANGS.items():
            pitch = 50 + (rnd * 4) % 48        # vary pitch each round
            out = sw.synth_concat(words, {"variant": voice, "pitch": pitch, "rate": 175})
            if out is None:
                continue
            clip, _fs, _b = out
            # 1) hear it through the real STT pipeline -> self-tunes depth_threshold
            pipe.ingest(s, np.asarray(clip, dtype=np.float32))
            s.tick(50000); s.tick(50000)
            apply_floor()
            # 2) learn the recogniser from its OWN cuts (forced-aligned)
            bank_from_own_cuts(s, sw, lex, voice, words, pitch)
            clips += 1
        if rnd % 5 == 0 or rnd == rounds:
            wer, spw = evaluate(s, sw, lex, hat)
            print(f"  {rnd:>5} {clips:>6} {sv_threshold(s):>10.2f} {singleton_fraction(s):>10.2f} "
                  f"{lex.size():>6} {spw:>10.2f} {wer*100:>8.1f}%")

    print(SEP)
    print("  Observe: did depth_threshold move? did segs/word fall toward 1.00? did open_WER drop")
    print("  as the agent kept hearing itself — or did it plateau (the over-segmentation frontier)?")
    print(SEP)


if __name__ == "__main__":
    main()

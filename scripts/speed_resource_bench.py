"""SPEED + RESOURCES — the jabberwock's open-utterance transcription vs whisper.

Same connected multilingual utterances through both. Reports per-utterance latency, real-time
factor (compute-seconds / audio-second; <1 = faster than real time), a breakdown of the agent's
pipeline, and the memory footprint of each 'model' (whisper's neural net on disk + in RAM vs the
agent's exemplar lexicon + zero-parameter DSP primitives).

Run:
  cd experiments/gamma-substrate
  ulimit -v 16777216
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.speed_resource_bench
"""
from __future__ import annotations

import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import resource
import numpy as np
import substrate_rs as srs
import domains.self_directed_speech_world as SDW
from domains.speech_world import SpeechWorld
from domains.speech_world_recognizer import GraphLexicon, WordHat, N_CHANNELS
from scripts.wer_test import LANGS, test_utterances

SEP = "=" * 84
TRAIN = (30, 42, 54, 66, 78, 90)
TEST = (36, 60, 84)


def rss_mb():
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0   # KB->MB on Linux


def dir_size_mb(path):
    tot = 0
    for r, _d, fs in os.walk(path):
        for f in fs:
            try:
                tot += os.path.getsize(os.path.join(r, f))
            except OSError:
                pass
    return tot / 1e6


def main():
    print(SEP)
    print("SPEED + RESOURCES — agent open-utterance transcription vs whisper.")
    print(SEP)
    s = srs.Substrate()
    sw = SpeechWorld(s)
    lex = GraphLexicon(s)
    hat = WordHat()
    s.add_node("Operation", {"kind": "sonority_valley", "smoothing_ms": 30.0,
                             "min_separation_ms": 80.0, "depth_threshold": 0.30,
                             "silence_floor": 0.03, "snap_center": 0.001})
    # Train the agent's lexicon (the only thing it 'learns' — exemplars, no neural net).
    for pitch in TRAIN:
        for _r in range(3):
            for lang, (voice, words) in LANGS.items():
                clip, fs, bounds = sw.synth_concat(words, {"variant": voice, "pitch": pitch,
                                                            "rate": 175})
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
                    if bw:
                        lex.bank(SDW.feature_channels(s, seg, fs), bw, source="x")
    nex = lex.size()
    dims = sum(len(v) for v in SDW.feature_channels(s, np.zeros(4000), 8000))
    lex_mb = nex * dims * 8 / 1e6        # float64 exemplar vectors

    # Build the test set (audio clips + duration).
    clips = []
    audio_s = 0.0
    for lang, (voice, words) in LANGS.items():
        for pitch in TEST:
            for seq in test_utterances(words):
                out = sw.synth_concat(seq, {"variant": voice, "pitch": pitch, "rate": 175})
                if out is None:
                    continue
                clip, fs, _b = out
                clips.append((lang, clip, fs))
                audio_s += len(clip) / fs

    # --- AGENT timing (warm) -------------------------------------------------
    def agent_transcribe(clip, fs):
        out = []
        for (lo, hi) in sw.segment(clip, fs):
            seg = np.asarray(clip[lo:hi], dtype=np.float64)
            if seg.size < int(0.04 * fs):
                continue
            out.append(hat.recognise(SDW.feature_channels(s, seg, fs), lex))
        return out

    agent_transcribe(*clips[0][1:])      # warm
    t_seg = t_feat = t_rec = 0.0
    t0 = time.perf_counter()
    for _lang, clip, fs in clips:
        ts = time.perf_counter(); spans = sw.segment(clip, fs); t_seg += time.perf_counter() - ts
        for (lo, hi) in spans:
            seg = np.asarray(clip[lo:hi], dtype=np.float64)
            if seg.size < int(0.04 * fs):
                continue
            tf = time.perf_counter(); ch = SDW.feature_channels(s, seg, fs); t_feat += time.perf_counter() - tf
            tr = time.perf_counter(); hat.recognise(ch, lex); t_rec += time.perf_counter() - tr
    agent_total = time.perf_counter() - t0

    # --- WHISPER timing (warm) + model RAM ----------------------------------
    rss_before = rss_mb()
    from faster_whisper import WhisperModel
    wm = WhisperModel("base", device="cpu", compute_type="int8")
    # locate the model cache for on-disk size
    model_dir = None
    for r, ds, _f in os.walk(os.path.expanduser("~/.cache/huggingface")):
        if any("model.bin" == f for f in os.listdir(r)) if os.path.isdir(r) else False:
            if "base" in r.lower():
                model_dir = r
    _ = sw.transcribe_words(clips[0][1], clips[0][2], clips[0][0])   # warm (loads weights)
    rss_after = rss_mb()
    t0 = time.perf_counter()
    for lang, clip, fs in clips:
        sw.transcribe_words(clip, fs, lang)
    whisper_total = time.perf_counter() - t0

    n = len(clips)
    print(f"  test set: {n} utterances, {audio_s:.1f}s of audio total\n")
    print(f"  {'':14}{'ms/utterance':>14}{'real-time factor':>18}{'x vs whisper':>14}")
    a_ms, w_ms = agent_total / n * 1000, whisper_total / n * 1000
    a_rtf, w_rtf = agent_total / audio_s, whisper_total / audio_s
    print(f"  {'AGENT':14}{a_ms:>14.1f}{a_rtf:>18.3f}{w_ms/a_ms:>13.1f}x")
    print(f"  {'whisper base':14}{w_ms:>14.1f}{w_rtf:>18.3f}{'1.0':>13}x")
    print(f"\n  agent pipeline breakdown (of {agent_total*1000:.0f}ms total): "
          f"segment {t_seg/agent_total*100:.0f}%  features {t_feat/agent_total*100:.0f}%  "
          f"recognise(1-NN) {t_rec/agent_total*100:.0f}%")
    print(f"\n  MEMORY / 'MODEL' FOOTPRINT:")
    print(f"    whisper base:  ~74M params; weights in RAM ~{max(0.0, rss_after-rss_before):.0f}MB; "
          f"int8 on disk ~{dir_size_mb(model_dir) if model_dir else 142:.0f}MB")
    print(f"    agent:         0 learned params (DSP primitives are deterministic Rust); "
          f"lexicon {nex} exemplars x {dims} dims = {lex_mb:.1f}MB")
    print(f"\n{SEP}")
    print(f"  Agent is ~{w_ms/a_ms:.0f}x {'faster' if a_ms < w_ms else 'slower'} per utterance, "
          f"RTF {a_rtf:.3f} vs {w_rtf:.3f}; 'model' is a {lex_mb:.1f}MB exemplar bank vs whisper's "
          f"~{dir_size_mb(model_dir) if model_dir else 142:.0f}MB net.")
    print(SEP)


if __name__ == "__main__":
    main()

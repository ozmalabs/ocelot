"""SPEECH-WORLD SMOKE — prove the four affordances + the analysis-by-synthesis data
flow BEFORE any seed/graph-native work.

It exercises, with ZERO graph decisions (the smoke is the world, not the agent):
  · MOUTH    : piper synth(word) -> raw audio.
  · OWN EAR  : feature_channels(substrate, x, fs) -> the agent's perceptual channels.
  · RECOGNISE: WordHat.recognise over a banked GraphLexicon -> the agent's held guess.
  · GROUND   : whisper transcribe(x, fs) -> the ground-truth label.
  · EXECUTOR : SpeechWorld.execute({operator:"abs_self_test", ...}) -> MeasuredCapability.
  · CORPUS   : sources() enumerates jellyfin + local children's videos.

Run:
  cd experiments/gamma-substrate
  ulimit -v 8388608
  PYTHONPATH=.:runners/dsl/python \\
    /home/matt/ozma/internal/research/.venv/bin/python -m scripts.speech_world_smoke
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import substrate_rs as srs
from domains.speech_world import SpeechWorld, FS
import domains.self_directed_speech_world as SDW
from domains.speech_world_recognizer import GraphLexicon, WordHat, N_CHANNELS

SEP = "=" * 78
WORDS = ["one", "two", "three", "four", "five"]


def main():
    print(SEP)
    print("SPEECH-WORLD SMOKE — piper mouth -> agent ear -> recognise -> whisper truth")
    print(SEP)

    s = srs.Substrate()
    world = SpeechWorld(s)
    voice = {"variant": "lessac", "pitch": 50, "rate": 175}

    # ---- 1. MOUTH + OWN EAR + GROUND-TRUTH: synth each word, perceive, label, bank.
    lex = GraphLexicon(s)
    heard = []
    for w in WORDS:
        out = world.synth(w, voice)
        assert out is not None, f"piper synth failed for {w!r}"
        x, fs = out
        channels = SDW.feature_channels(s, x, fs)
        assert len(channels) == N_CHANNELS, f"channels={len(channels)} != {N_CHANNELS}"
        truth = world.transcribe(x, fs)
        truth_word = truth[0][0] if truth else None
        lex.bank(channels, truth_word or w, source=f"piper:{voice['variant']}")
        heard.append((w, truth_word, len(x)))
        print(f"  synth {w:>6} -> {len(x):5d} samples @{fs}  | whisper heard: {truth_word!r}")

    labelled = sum(1 for (_, t, _) in heard if t is not None)
    print(f"\n  banked {lex.size()} exemplars; whisper labelled {labelled}/{len(WORDS)}")

    # ---- 2. RECOGNISE: held graph Argmax over the bank for a fresh synth of "three".
    hat = WordHat()
    out = world.synth("three", {"variant": "lessac", "pitch": 55, "rate": 165})
    x, fs = out
    channels = SDW.feature_channels(s, x, fs)
    guess = hat.recognise(channels, lex)
    truth = world.transcribe(x, fs)
    truth_word = truth[0][0] if truth else None
    print(f"\n  RECOGNISE fresh 'three': agent guess={guess!r}  whisper truth={truth_word!r}")

    # ---- 3. EXECUTOR: the mechanical execute() path -> MeasuredCapability write-back.
    req = {"operator": "abs_self_test", "word": "two",
           "voice": {"variant": "lessac", "pitch": 50, "rate": 175},
           "capability_keys": ["recognise", "speech", "word"],
           "measurement_key": "abs_recognition_match", "target": 0.60}
    mc = world.execute(req)
    assert mc is not None, "execute(abs_self_test) returned None"
    mc_attrs = s.node(mc)["attrs"]
    print(f"  EXECUTE abs_self_test -> MeasuredCapability"
          f" measured={mc_attrs.get('measured')} metric={mc_attrs.get('metric')!r}"
          f" note={mc_attrs.get('note')!r}")

    # ---- 4. CORPUS: enumerate the children's-video sources.
    srcs = world.sources()
    by = {}
    for src in srcs:
        by.setdefault(src["origin"], []).append(src)
    print("\n  CORPUS sources:")
    for origin, items in by.items():
        eg = ", ".join(i["name"][:20] for i in items[:3])
        print(f"    {origin:>9}: {len(items):3d}  e.g. {eg}")

    # ---- assertions: the data flow is real.
    ok_channels = N_CHANNELS == 3
    ok_label = labelled >= 1
    ok_guess = guess is not None
    ok_exec = mc is not None
    ok_corpus = len(srcs) >= 1
    print(f"\n{SEP}")
    print(f"  channels({N_CHANNELS})={ok_channels}  whisper-labelled={ok_label}  "
          f"recognise-guess={ok_guess}  executor={ok_exec}  corpus={ok_corpus}")
    allok = ok_channels and ok_label and ok_guess and ok_exec and ok_corpus
    print(f"  SMOKE {'PASS' if allok else 'FAIL'}")
    print(SEP)
    return 0 if allok else 1


if __name__ == "__main__":
    sys.exit(main())

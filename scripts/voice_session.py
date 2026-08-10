#!/usr/bin/env python3
"""voice_session — the interactive mic <-> jabberwock voice loop, and a --wav offline
test/demo path that feeds a recorded file through the identical pipeline.

A world adapter driver (mechanical host I/O only, per CLAUDE.md): boot or attach to an
agent, capture/read audio, hand utterances to `domains.voice_world.VoiceWorld` (which
composes the EXISTING `WorldAdapter.ingest_audio_file` / `comprehend` / `outbound_messages`
/ `responds_to` / `emit_reply` primitives — see domains/voice_world.py's module docstring
for exactly which reused paths), print what happened, and (if a Piper voice is installed)
speak the reply. No agent decisions live here.

Run:
  # fresh full-seed boot, listen on the default mic
  PYTHONPATH=runners/dsl/python:. python3 scripts/voice_session.py --seeds full

  # attach to a running daemon's saved state instead of a fresh boot
  PYTHONPATH=runners/dsl/python:. python3 scripts/voice_session.py \\
      --load ~/.jabberwock/checkpoints/snapshot-<ts>.save

  # offline / test path: feed a recorded file through the pipeline instead of the mic
  PYTHONPATH=runners/dsl/python:. python3 scripts/voice_session.py --wav path/to/clip.flac

  # text-only (no piper playback)
  PYTHONPATH=runners/dsl/python:. python3 scripts/voice_session.py --wav clip.wav --no-speak
"""
from __future__ import annotations

import argparse
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if p not in sys.path:
        sys.path.insert(0, p)

from substrate.world_adapter import WorldAdapter          # noqa: E402
from substrate.boot_all import load_all_seeds              # noqa: E402
import domains.voice_world as VW                           # noqa: E402


def boot_fresh() -> WorldAdapter:
    agent = WorldAdapter(seeds=())
    rep = load_all_seeds(agent)
    print(f"[voice_session] fresh boot: {rep['loaded']}/{rep['total']} seeds, "
          f"{rep['concepts']} concepts, {len(rep['failed'])} failed "
          f"({agent.s.node_count()} nodes)", flush=True)
    return agent


def boot_from_checkpoint(path: str) -> WorldAdapter:
    agent = WorldAdapter.load(path)
    print(f"[voice_session] attached to checkpoint {path} "
          f"({agent.s.node_count()} nodes)", flush=True)
    return agent


def _report_turn(i, utt, fs, results):
    print(f"  utterance {i}: {len(utt) / fs:.2f}s", flush=True)
    if not results:
        print("    (no Message minted — VAD-detected audio too short/quiet for the "
              "Rust-side detect_utterances)", flush=True)
    for r in results:
        print(f"    heard: sign={r['sign']} new_sign={r['is_new']} -> "
              f"reply={r['reply']!r}", flush=True)
    return results


def run_wav(vw: VW.VoiceWorld, path: str, *, speak: bool, variant: str) -> list:
    samples, fs = VW.load_audio_any(path, fs=VW.FS)
    utts = VW.segment_utterances(samples, fs=fs)
    print(f"[voice_session] {path}: {len(samples) / fs:.2f}s of audio -> "
          f"VAD found {len(utts)} utterance(s)", flush=True)
    all_results = []
    for i, utt in enumerate(utts):
        results = vw.hear_and_reply(utt, fs=fs)
        _report_turn(i, utt, fs, results)
        for r in results:
            if speak and r["reply"]:
                got = vw.speak(r["reply"], variant=variant, play=True)
                if got is None:
                    print("    (no synthesis available — piper/its voice model "
                          "isn't installed; reply printed above only)", flush=True)
        all_results.append(results)
    return all_results


def run_interactive_mic(vw: VW.VoiceWorld, *, speak: bool, variant: str, device):
    print("[voice_session] listening on the mic (Ctrl-C to stop)...", flush=True)
    n = 0
    try:
        for utt in VW.capture_utterances_from_mic(fs=VW.FS, device=device):
            n += 1
            results = vw.hear_and_reply(utt, fs=VW.FS)
            _report_turn(n, utt, VW.FS, results)
            for r in results:
                if speak and r["reply"]:
                    vw.speak(r["reply"], variant=variant, play=True)
    except KeyboardInterrupt:
        print("\n[voice_session] stopped.", flush=True)
    except RuntimeError as e:
        print(f"[voice_session] mic capture unavailable: {e}", flush=True)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--load", default=None,
                    help="attach to a saved WorldAdapter checkpoint instead of a fresh boot")
    ap.add_argument("--seeds", choices=["full"], default="full",
                    help="fresh-boot seed set when --load is absent (only 'full' today)")
    ap.add_argument("--wav", default=None,
                    help="feed a recorded audio file through the pipeline instead of the mic "
                         "(also the pytest-free smoke-test path)")
    ap.add_argument("--lexicon", default="default", help="AcousticLexicon name")
    ap.add_argument("--device", default=None,
                    help="ALSA capture device for arecord -D (default: system default)")
    ap.add_argument("--voice", default=VW.DEFAULT_VOICE_VARIANT,
                    help="Piper voice variant for spoken replies (borrowed synthesis — see "
                         "domains/voice_world.py)")
    ap.add_argument("--no-speak", action="store_true",
                    help="print replies only; skip Piper synthesis/playback")
    args = ap.parse_args()

    agent = boot_from_checkpoint(args.load) if args.load else boot_fresh()
    vw = VW.VoiceWorld(agent, lexicon_name=args.lexicon)

    speak = not args.no_speak
    if speak and not VW.piper_available(args.voice):
        print(f"[voice_session] Piper voice '{args.voice}' not installed — "
              f"falling back to text-only output.", flush=True)
        speak = False

    if args.wav:
        run_wav(vw, args.wav, speak=speak, variant=args.voice)
        return 0

    run_interactive_mic(vw, speak=speak, variant=args.voice, device=args.device)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

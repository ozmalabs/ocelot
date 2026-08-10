"""Qualitative Piper replication frozen in WHISPER_GROUNDING_PREREG.md."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import substrate_rs as srs

ROOT = Path(__file__).resolve().parent.parent
for path in (ROOT, ROOT / "runners" / "dsl" / "python"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from domains import whisper_teacher_adapter as teacher  # noqa: E402
from domains.speech_world import SpeechWorld  # noqa: E402
from domains.whisper_grounding_guard import (  # noqa: E402
    DIGIT_WORDS,
    normalize_digit_transcript,
)
from scripts.universal_loop_phaseAB_piper import _get_voice  # noqa: E402


FROZEN_VOICES = ("arctic", "aru", "semaine", "danny")
FROZEN_PITCHES = (37, 63)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "results" / "whisper_grounding_piper.json",
    )
    args = parser.parse_args()
    model = teacher._load()
    world = SpeechWorld(srs.Substrate())
    available = [voice for voice in FROZEN_VOICES if _get_voice(voice)]
    unavailable = [voice for voice in FROZEN_VOICES if voice not in available]
    rows = []
    failures = []
    for voice in available:
        for pitch in FROZEN_PITCHES:
            for reference in DIGIT_WORDS:
                synthesized = world.synth(
                    reference,
                    {"variant": voice, "pitch": pitch, "rate": 175},
                )
                if synthesized is None:
                    failures.append({
                        "voice": voice,
                        "pitch": pitch,
                        "reference": reference,
                    })
                    continue
                audio, _ = synthesized
                segments, _ = model.transcribe(
                    audio, language="en", beam_size=5
                )
                raw = " ".join(
                    segment.text.strip() for segment in segments
                ).strip()
                normalized = normalize_digit_transcript(raw)
                rows.append({
                    "voice": voice,
                    "pitch": pitch,
                    "reference": reference,
                    "baseline_raw": raw,
                    "baseline_normalized": normalized,
                    "correct": normalized == reference,
                    "omission": normalized == "",
                    "hallucination": (
                        normalized != "" and normalized != reference
                    ),
                })
    n = len(rows)
    result = {
        "protocol": "WHISPER_GROUNDING_PREREG.md",
        "kind": "qualitative_synthetic_replication",
        "frozen_voices": list(FROZEN_VOICES),
        "available_voices": available,
        "unavailable_voices": unavailable,
        "pitches": list(FROZEN_PITCHES),
        "synthesis_failures": failures,
        "n": n,
        "correct": sum(row["correct"] for row in rows),
        "omissions": sum(row["omission"] for row in rows),
        "hallucinations": sum(row["hallucination"] for row in rows),
        "rows": rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({key: value for key, value in result.items()
                      if key != "rows"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

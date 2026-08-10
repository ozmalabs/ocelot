"""Frozen FSDD evaluation for graph-native Whisper encoder grounding.

Run after obtaining the pinned FSDD v1.0.8 archive:

  PYTHONPATH=runners/dsl/python:. ../../.venv/bin/python \
    scripts/whisper_grounding_measure.py

The protocol is frozen in WHISPER_GROUNDING_PREREG.md. This runner performs
mechanical I/O, feature extraction, aggregation, and statistics. Candidate
identity and accept/correct/abstain are produced by the loaded graph seed.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import math
from pathlib import Path
import platform
import re
import sys

import numpy as np
import soundfile as sf
from scipy.signal import resample_poly
from scipy.stats import binomtest

ROOT = Path(__file__).resolve().parent.parent
for path in (ROOT, ROOT / "runners" / "dsl" / "python"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from domains import whisper_teacher_adapter as teacher  # noqa: E402
from domains.whisper_grounding_guard import (  # noqa: E402
    DIGIT_WORDS,
    GraphWhisperGroundingGuard,
    PrototypeBank,
    normalize_digit_transcript,
)
from substrate.boot_core import boot_core  # noqa: E402


EXPECTED_ARCHIVE_MD5 = "54f48186ecb1d5ac4e971143086d529b"
HISTORICAL_GIT_COMMIT = "26eb9aaf76e81b692f806f9140c2d2777410d7a1"
HISTORICAL_ARCHIVE_SHA256 = (
    "beaca4fb849cad13103b2cffba913b3d7fdb5f15222da4ddd07187b3c38a757a"
)
FILENAME = re.compile(
    r"^(?P<digit>[0-9])_(?P<speaker>[^_]+)_(?P<index>[0-9]+)\.wav$"
)


def _version(name):
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return "not-installed"


def _md5(path: Path):
    h = hashlib.md5()  # nosec B324 - dataset identity, not security
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _sha256(path: Path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _audio(path: Path):
    audio, sample_rate = sf.read(path, always_2d=False)
    audio = np.asarray(audio, dtype=np.float32)
    if audio.ndim == 2:
        audio = audio.mean(axis=1)
    if sample_rate != 16000:
        divisor = math.gcd(int(sample_rate), 16000)
        audio = resample_poly(
            audio, 16000 // divisor, int(sample_rate) // divisor
        ).astype(np.float32)
    return np.ascontiguousarray(audio)


def _free_decode(model, audio):
    segments, _ = model.transcribe(
        audio, language="en", beam_size=5
    )
    return " ".join(segment.text.strip() for segment in segments).strip()


def _phase_scramble(audio, key: str):
    spectrum = np.fft.rfft(np.asarray(audio, dtype=np.float64))
    seed = int.from_bytes(
        hashlib.blake2b(key.encode("utf-8"), digest_size=8).digest(),
        "little",
    )
    rng = np.random.default_rng(seed)
    phases = rng.uniform(-np.pi, np.pi, len(spectrum))
    phases[0] = 0.0
    if len(audio) % 2 == 0:
        phases[-1] = 0.0
    scrambled = np.fft.irfft(
        np.abs(spectrum) * np.exp(1j * phases), n=len(audio)
    )
    return np.asarray(scrambled, dtype=np.float32)


def _wilson(successes, total, z=1.959963984540054):
    if total == 0:
        return [None, None]
    p = successes / total
    denominator = 1.0 + z * z / total
    centre = (p + z * z / (2 * total)) / denominator
    margin = (
        z
        * math.sqrt(
            p * (1 - p) / total + z * z / (4 * total * total)
        )
        / denominator
    )
    return [centre - margin, centre + margin]


def _rate(count, total):
    return {
        "count": int(count),
        "total": int(total),
        "rate": (count / total if total else None),
        "wilson95": _wilson(count, total),
    }


def _speech_metrics(rows):
    total = len(rows)
    baseline_correct = sum(row["baseline_correct"] for row in rows)
    baseline_omission = sum(row["baseline_omission"] for row in rows)
    baseline_hallucination = sum(
        row["baseline_hallucination"] for row in rows
    )
    baseline_nonempty = total - baseline_omission
    guard_emitted = sum(row["guard_emitted"] for row in rows)
    guard_correct = sum(row["guard_correct"] for row in rows)
    guard_hallucination = sum(row["guard_hallucination"] for row in rows)
    corrections = [row for row in rows if row["action"] == "correct"]
    correction_correct = sum(row["guard_correct"] for row in corrections)
    baseline_nonempty_correct = sum(
        row["baseline_correct"] and not row["baseline_omission"]
        for row in rows
    )
    b_only = sum(
        row["baseline_correct"] and not row["guard_correct"] for row in rows
    )
    g_only = sum(
        row["guard_correct"] and not row["baseline_correct"] for row in rows
    )
    discordant = b_only + g_only
    mcnemar_p = (
        binomtest(min(b_only, g_only), discordant, 0.5).pvalue
        if discordant else 1.0
    )
    return {
        "n": total,
        "baseline_exact_accuracy": _rate(baseline_correct, total),
        "baseline_omission_rate": _rate(baseline_omission, total),
        "baseline_hallucination_rate": _rate(
            baseline_hallucination, total
        ),
        "baseline_nonempty_accuracy": _rate(
            baseline_nonempty_correct, baseline_nonempty
        ),
        "guard_coverage": _rate(guard_emitted, total),
        "guard_exact_accuracy": _rate(guard_correct, total),
        "guard_selective_accuracy": _rate(guard_correct, guard_emitted),
        "guard_hallucination_rate": _rate(guard_hallucination, total),
        "correction_precision": _rate(
            correction_correct, len(corrections)
        ),
        "paired_correctness": {
            "baseline_only_correct": b_only,
            "guard_only_correct": g_only,
            "discordant": discordant,
            "exact_two_sided_mcnemar_p": mcnemar_p,
        },
    }


def _discover(recordings: Path):
    clips = []
    malformed = []
    for path in sorted(recordings.glob("*.wav")):
        match = FILENAME.match(path.name)
        if match is None:
            malformed.append(path.name)
            continue
        index = int(match.group("index"))
        if index > 9:
            continue
        digit = int(match.group("digit"))
        clips.append({
            "path": path,
            "relative_path": path.relative_to(recordings.parent).as_posix(),
            "speaker": match.group("speaker"),
            "digit": digit,
            "label": DIGIT_WORDS[digit],
            "index": index,
        })
    return clips, malformed


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--data-dir", type=Path, default=ROOT / "data" / "fsdd"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "results" / "whisper_grounding.json",
    )
    parser.add_argument(
        "--dataset-kind",
        choices=("zenodo-v1.0.8", "github-historical"),
        default="zenodo-v1.0.8",
    )
    args = parser.parse_args()
    recordings = args.data_dir / "recordings"
    if not recordings.is_dir():
        alternatives = list(args.data_dir.glob("**/recordings"))
        if len(alternatives) == 1:
            recordings = alternatives[0]
        else:
            raise SystemExit(f"FSDD recordings not found under {args.data_dir}")
    clips, malformed = _discover(recordings)
    speakers = sorted({clip["speaker"] for clip in clips})
    expected_clips = 100 * len(speakers)
    if len(speakers) not in {3, 6} or len(clips) != expected_clips:
        raise SystemExit(
            f"sample mismatch: {len(clips)} clips, "
            f"{len(speakers)} speakers ({speakers})"
        )

    archive = next(iter(sorted(args.data_dir.glob("*.zip"))), None)
    archive_md5 = _md5(archive) if archive else None
    archive_sha256 = _sha256(archive) if archive else None
    expected_speakers = 3 if args.dataset_kind == "zenodo-v1.0.8" else 6
    if len(speakers) != expected_speakers:
        raise SystemExit(
            f"{args.dataset_kind} expected {expected_speakers} speakers, "
            f"observed {len(speakers)}"
        )
    if (
        args.dataset_kind == "zenodo-v1.0.8"
        and archive_md5 is not None
        and archive_md5 != EXPECTED_ARCHIVE_MD5
    ):
        raise SystemExit(
            f"archive MD5 {archive_md5} != frozen {EXPECTED_ARCHIVE_MD5}"
        )
    if (
        args.dataset_kind == "github-historical"
        and archive_sha256 is not None
        and archive_sha256 != HISTORICAL_ARCHIVE_SHA256
    ):
        raise SystemExit(
            f"archive SHA256 {archive_sha256} != pinned "
            f"{HISTORICAL_ARCHIVE_SHA256}"
        )

    model = teacher._load()
    observations = []
    print(f"Extracting Whisper evidence for {len(clips)} speech clips...")
    for index, clip in enumerate(clips, 1):
        audio = _audio(clip["path"])
        raw = _free_decode(model, audio)
        observations.append({
            **clip,
            "audio": audio,
            "embedding": teacher.embed(audio),
            "baseline_raw": raw,
            "baseline_normalized": normalize_digit_transcript(raw),
        })
        if index % 25 == 0:
            print(f"  speech {index}/{len(clips)}", flush=True)

    rows = []
    null_rows = []
    fold_geometry = {}
    for speaker in speakers:
        support = {
            label: [
                observation["embedding"]
                for observation in observations
                if observation["speaker"] != speaker
                and observation["label"] == label
            ]
            for label in DIGIT_WORDS
        }
        bank = PrototypeBank.from_support(
            support, fold=f"held-out:{speaker}"
        )
        substrate, agent = boot_core(seeds=())
        guard = GraphWhisperGroundingGuard(substrate, agent, bank)
        fold_geometry[speaker] = {
            label: {
                "support_count": bank.support_counts[label],
                "support_radius": bank.radii[label],
            }
            for label in DIGIT_WORDS
        }
        held = [
            observation
            for observation in observations
            if observation["speaker"] == speaker
        ]
        for observation in held:
            decision = guard.infer_embedding(
                observation["embedding"], observation["baseline_raw"]
            )
            baseline = observation["baseline_normalized"]
            output = decision["output_label"]
            reference = observation["label"]
            rows.append({
                "path": observation["relative_path"],
                "speaker": speaker,
                "reference": reference,
                "baseline_raw": observation["baseline_raw"],
                "baseline_normalized": baseline,
                "baseline_correct": baseline == reference,
                "baseline_omission": baseline == "",
                "baseline_hallucination": baseline != "" and baseline != reference,
                "guard_output": output,
                "guard_correct": output == reference,
                "guard_emitted": output != "",
                "guard_hallucination": output != "" and output != reference,
                "action": decision["action"],
                "winner_label": decision.get("winner_label", ""),
                "winner_distance": decision.get("winner_distance"),
                "winner_radius": decision.get("winner_radius"),
                "decision_provenance": decision["decision_provenance"],
            })
        null_source = [
            observation for observation in held if observation["index"] == 0
        ]
        for observation in null_source:
            variants = {
                "silence": np.zeros_like(observation["audio"]),
                "phase_scrambled": _phase_scramble(
                    observation["audio"], observation["relative_path"]
                ),
            }
            for kind, audio in variants.items():
                raw = _free_decode(model, audio)
                baseline = normalize_digit_transcript(raw)
                decision = guard.infer_audio(audio, raw)
                null_rows.append({
                    "source_path": observation["relative_path"],
                    "speaker": speaker,
                    "kind": kind,
                    "baseline_raw": raw,
                    "baseline_normalized": baseline,
                    "baseline_false_transcript": baseline != "",
                    "guard_output": decision["output_label"],
                    "guard_false_transcript": decision["output_label"] != "",
                    "action": decision["action"],
                    "winner_label": decision.get("winner_label", ""),
                    "winner_distance": decision.get("winner_distance"),
                    "winner_radius": decision.get("winner_radius"),
                    "decision_provenance": decision["decision_provenance"],
                })
        print(f"  evaluated fold held-out:{speaker}", flush=True)

    metrics = _speech_metrics(rows)
    base_null = sum(row["baseline_false_transcript"] for row in null_rows)
    guard_null = sum(row["guard_false_transcript"] for row in null_rows)
    metrics["null_controls"] = {
        "n": len(null_rows),
        "baseline_false_transcript_rate": _rate(
            base_null, len(null_rows)
        ),
        "guard_false_transcript_rate": _rate(
            guard_null, len(null_rows)
        ),
    }
    base_h = metrics["baseline_hallucination_rate"]["count"]
    guard_h = metrics["guard_hallucination_rate"]["count"]
    reduction = (base_h - guard_h) / base_h if base_h else None
    correction_rate = metrics["correction_precision"]["rate"]
    coverage = metrics["guard_coverage"]["rate"]
    selective = metrics["guard_selective_accuracy"]["rate"]
    baseline_selective = metrics["baseline_nonempty_accuracy"]["rate"]
    hypotheses = {
        "H1_reproduced_nonempty_wrong_transcript": base_h > 0,
        "H2_hallucinations_reduced_at_least_50pct": (
            reduction is not None and reduction >= 0.5
        ),
        "H3_correction_precision_at_least_90pct": (
            correction_rate is not None and correction_rate >= 0.9
        ),
        "H4_null_false_transcripts_not_increased": guard_null <= base_null,
        "H5_coverage_and_selective_accuracy": (
            coverage is not None
            and coverage >= 0.3
            and selective is not None
            and baseline_selective is not None
            and selective > baseline_selective
        ),
    }
    result = {
        "schema_version": 1,
        "preregistration_commit": "ae452fc1f1",
        "protocol": "WHISPER_GROUNDING_PREREG.md",
        "protocol_deviation": (
            "WHISPER_GROUNDING_DEVIATION.md"
        ),
        "dataset": {
            "name": "Free Spoken Digit Dataset",
            "kind": args.dataset_kind,
            "version": (
                "1.0.8"
                if args.dataset_kind == "zenodo-v1.0.8"
                else f"git:{HISTORICAL_GIT_COMMIT}"
            ),
            "source": (
                "https://zenodo.org/records/1342401"
                if args.dataset_kind == "zenodo-v1.0.8"
                else "https://github.com/Jakobovski/free-spoken-digit-dataset"
            ),
            "expected_archive_md5": (
                EXPECTED_ARCHIVE_MD5
                if args.dataset_kind == "zenodo-v1.0.8"
                else None
            ),
            "observed_archive_md5": archive_md5,
            "expected_archive_sha256": (
                HISTORICAL_ARCHIVE_SHA256
                if args.dataset_kind == "github-historical"
                else None
            ),
            "observed_archive_sha256": archive_sha256,
            "recordings_root": str(recordings),
            "clips": len(clips),
            "speakers": speakers,
            "malformed_files": malformed,
        },
        "runtime": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "faster_whisper": _version("faster-whisper"),
            "ctranslate2": _version("ctranslate2"),
            "numpy": _version("numpy"),
            "scipy": _version("scipy"),
            "soundfile": _version("soundfile"),
            "model": "base.en",
            "device": "cpu",
            "compute_type": "int8",
            "beam_size": 5,
            "language": "en",
        },
        "metrics": metrics,
        "hallucination_reduction": reduction,
        "hypotheses": hypotheses,
        "all_primary_hypotheses_pass": all(hypotheses.values()),
        "fold_geometry": fold_geometry,
        "speech_rows": rows,
        "null_rows": null_rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "output": str(args.output),
        "metrics": metrics,
        "hallucination_reduction": reduction,
        "hypotheses": hypotheses,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

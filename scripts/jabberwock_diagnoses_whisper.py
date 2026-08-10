"""Let Jabberwock causally diagnose and repair official OpenAI Whisper.

Python is the laboratory bench: it loads audio/model weights, exposes the
published module hierarchy, enacts the graph's requested intervention, and
returns raw counts. Experiment choice, causal admission, repair authorship,
control selection, and the prospective verdict are graph Rules running in the
Rust substrate.
"""
from __future__ import annotations

import argparse
from contextlib import nullcontext
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
import re
import time
import wave

import numpy as np
from scipy.signal import resample_poly
import torch

from domains.published_net_debugger import (
    authored_control,
    authored_patch,
    audit_no_host_decisions,
    intervention_hook,
    lay_whisper_architecture,
    record_outcome,
    record_validation,
    requested_intervention,
    state_dict_sha256,
)
from domains.whisper_grounding_guard import (
    DIGIT_WORDS,
    normalize_digit_transcript,
)
from substrate.boot_core import boot_core, load_seeds_into


ROOT = Path(__file__).resolve().parents[1]
FSDD_REVISION = "26eb9aaf76e81b692f806f9140c2d2777410d7a1"
_FILENAME = re.compile(r"(?P<digit>[0-9])_(?P<speaker>[a-z]+)_(?P<index>[0-9]+)\.wav")


@dataclass(frozen=True)
class Probe:
    identity: str
    kind: str
    reference: str
    audio: np.ndarray
    baseline_raw: str
    baseline_normalized: str


def _add_edge(inner, source, edge_type, target):
    try:
        inner.add_edge_unchecked(source, edge_type, target)
    except TypeError:
        inner.add_edge_unchecked(source, edge_type, target, {})


def _load_audio(path: Path) -> np.ndarray:
    with wave.open(str(path), "rb") as wav:
        channels = wav.getnchannels()
        rate = wav.getframerate()
        width = wav.getsampwidth()
        raw = wav.readframes(wav.getnframes())
    if width != 2:
        raise ValueError(f"{path}: expected signed 16-bit PCM")
    audio = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    if channels > 1:
        audio = audio.reshape(-1, channels).mean(axis=1)
    if rate != 16000:
        divisor = np.gcd(rate, 16000)
        audio = resample_poly(
            audio, 16000 // divisor, rate // divisor,
        ).astype(np.float32)
    return np.ascontiguousarray(audio)


def _phase_scramble(audio: np.ndarray, identity: str) -> np.ndarray:
    spectrum = np.fft.rfft(np.asarray(audio, dtype=np.float64))
    seed = int.from_bytes(
        hashlib.blake2b(identity.encode(), digest_size=8).digest(), "little",
    )
    rng = np.random.default_rng(seed)
    phase = rng.uniform(-np.pi, np.pi, len(spectrum))
    phase[0] = 0.0
    if len(audio) % 2 == 0:
        phase[-1] = 0.0
    return np.fft.irfft(
        np.abs(spectrum) * np.exp(1j * phase), n=len(audio),
    ).astype(np.float32)


def _decode(model, audio: np.ndarray) -> str:
    result = model.transcribe(
        audio,
        language="en",
        fp16=False,
        temperature=0,
        beam_size=1,
        best_of=None,
        condition_on_previous_text=False,
        verbose=None,
    )
    return str(result["text"]).strip()


def _files_for_indices(data_dir: Path, indices: range) -> list[tuple[Path, str, str, int]]:
    rows = []
    admitted = set(indices)
    for path in data_dir.glob("*.wav"):
        match = _FILENAME.fullmatch(path.name)
        if match is None:
            continue
        index = int(match.group("index"))
        if index in admitted:
            rows.append((
                path,
                DIGIT_WORDS[int(match.group("digit"))],
                match.group("speaker"),
                index,
            ))
    # Mechanical Latin-square traversal prevents a phenotype quota from being
    # exhausted by one lexicographically early digit or speaker.
    speakers = sorted({row[2] for row in rows})
    speaker_order = {speaker: order for order, speaker in enumerate(speakers)}
    rows.sort(key=lambda row: (
        row[3],
        (
            DIGIT_WORDS.index(row[1]) - speaker_order[row[2]]
        ) % len(DIGIT_WORDS),
        speaker_order[row[2]],
        row[0].name,
    ))
    return rows


def _phenotype_panel(
    model, data_dir: Path, quota: int, indices: range,
) -> list[Probe]:
    """Mechanically fill preregistered phenotype buckets in filename order."""
    speech_hallucinations = []
    speech_correct = []
    null_false_transcripts = []
    null_empty_controls = []
    for path, reference, _speaker, _index in _files_for_indices(
        data_dir, indices,
    ):
        audio = _load_audio(path)
        raw = _decode(model, audio)
        normalized = normalize_digit_transcript(raw)
        if normalized == reference and len(speech_correct) < quota:
            speech_correct.append(Probe(
                path.name, "speech_correct", reference, audio, raw, normalized,
            ))
        elif normalized and normalized != reference and len(
            speech_hallucinations
        ) < quota:
            speech_hallucinations.append(Probe(
                path.name, "speech_hallucination", reference, audio, raw,
                normalized,
            ))

        if (
            len(null_false_transcripts) < quota
            or len(null_empty_controls) < quota
        ):
            for suffix, control in (
                ("silence", np.zeros_like(audio)),
                ("phase", _phase_scramble(audio, path.name)),
            ):
                control_raw = _decode(model, control)
                control_norm = normalize_digit_transcript(control_raw)
                if control_norm:
                    if len(null_false_transcripts) < quota:
                        null_false_transcripts.append(Probe(
                            f"{path.name}:{suffix}",
                            "null_false_transcript",
                            "",
                            control,
                            control_raw,
                            control_norm,
                        ))
                elif len(null_empty_controls) < quota:
                    null_empty_controls.append(Probe(
                        f"{path.name}:{suffix}",
                        "null_empty_control",
                        "",
                        control,
                        control_raw,
                        control_norm,
                    ))
        if (
            len(speech_hallucinations) == quota
            and len(speech_correct) == quota
            and len(null_false_transcripts) == quota
            and len(null_empty_controls) == quota
        ):
            break
    return (
        speech_hallucinations
        + speech_correct
        + null_false_transcripts
        + null_empty_controls
    )


def _run_probe_set(model, probes: list[Probe], spec=None) -> list[str]:
    context = intervention_hook(spec) if spec is not None else nullcontext()
    with context, torch.no_grad():
        return [_decode(model, probe.audio) for probe in probes]


def _discovery_counts(
    probes: list[Probe],
    intervention_text: list[str],
    restoration_text: list[str],
) -> dict:
    speech_removed = 0
    null_removed = 0
    null_added = 0
    correct_lost = 0
    for probe, raw in zip(probes, intervention_text):
        normalized = normalize_digit_transcript(raw)
        if probe.kind == "speech_hallucination":
            speech_removed += int(not normalized or normalized == probe.reference)
        elif probe.kind == "speech_correct":
            correct_lost += int(normalized != probe.reference)
        elif probe.kind == "null_false_transcript":
            null_removed += int(not normalized)
        elif probe.kind == "null_empty_control":
            null_added += int(bool(normalized))
    restoration_matches = sum(
        restored == probe.baseline_raw
        for probe, restored in zip(probes, restoration_text)
    )
    return {
        "speech_hallucinations_removed": speech_removed,
        "null_false_transcripts_removed": null_removed,
        "null_false_transcripts_added": null_added,
        "correct_controls_lost": correct_lost,
        "restoration_matches": restoration_matches,
        "restoration_total": len(restoration_text),
        "panel_total": len(probes),
    }


def _balanced_validation_probes(
    model, data_dir: Path, indices: range,
) -> tuple[list[Probe], list[Probe]]:
    """One balanced held-out recording per digit/speaker, spread over 20..29."""
    candidates = _files_for_indices(data_dir, indices)
    speakers = sorted({speaker for _path, _ref, speaker, _index in candidates})
    speech = []
    nulls = []
    for path, reference, speaker, index in candidates:
        digit = DIGIT_WORDS.index(reference)
        speaker_index = speakers.index(speaker)
        wanted_index = indices.start + (
            (digit * len(speakers) + speaker_index) % len(indices)
        )
        if index != wanted_index:
            continue
        audio = _load_audio(path)
        baseline_raw = _decode(model, audio)
        speech.append(Probe(
            path.name, "validation_speech", reference, audio,
            baseline_raw, normalize_digit_transcript(baseline_raw),
        ))
        control = _phase_scramble(audio, f"validation:{path.name}")
        null_raw = _decode(model, control)
        nulls.append(Probe(
            f"{path.name}:phase", "validation_null", "", control,
            null_raw, normalize_digit_transcript(null_raw),
        ))
    return speech, nulls


def _validation_arm(
    model, speech: list[Probe], nulls: list[Probe], spec=None,
) -> dict:
    speech_text = _run_probe_set(model, speech, spec)
    null_text = _run_probe_set(model, nulls, spec)
    correct = sum(
        normalize_digit_transcript(raw) == probe.reference
        for probe, raw in zip(speech, speech_text)
    )
    hallucinations = sum(
        bool(normalize_digit_transcript(raw))
        and normalize_digit_transcript(raw) != probe.reference
        for probe, raw in zip(speech, speech_text)
    )
    null_false = sum(
        bool(normalize_digit_transcript(raw)) for raw in null_text
    )
    return {
        "correct_speech": correct,
        "speech_hallucinations": hallucinations,
        "null_false_transcripts": null_false,
    }


def _node_attrs(substrate, node) -> dict:
    return dict(substrate.node(node)["attrs"])


def run(args) -> dict:
    if audit_no_host_decisions():
        raise RuntimeError(
            f"host-decision audit failed: {audit_no_host_decisions()}"
        )
    import whisper

    started = time.time()
    model = whisper.load_model(
        "base.en", device="cpu", download_root=str(args.model_dir),
    )
    model.eval()
    weights_before = state_dict_sha256(model)

    discovery_indices = range(args.discovery_start, args.discovery_end)
    validation_indices = range(args.validation_start, args.validation_end)
    panel = _phenotype_panel(
        model, args.data_dir, args.discovery_quota, discovery_indices,
    )
    panel_counts = {
        kind: sum(probe.kind == kind for probe in panel)
        for kind in (
            "speech_hallucination",
            "speech_correct",
            "null_false_transcript",
            "null_empty_control",
        )
    }
    if any(
        panel_counts[kind] != args.discovery_quota for kind in panel_counts
    ):
        raise RuntimeError(f"phenotype gate failed: {panel_counts}")
    print(f"discovery phenotype: {panel_counts}", flush=True)

    substrate, agent = boot_core(seeds=())
    load_seeds_into(substrate, agent, ["published_net_causal_debugger"])
    study = substrate.add_node("CausalDebuggingStudy", {
        "network": "openai-whisper/base.en",
        "status": "ready",
        "phase": "coarse",
        "phase_level": 0.0,
        "head_search_initialized": 0.0,
        "protocol": args.protocol.name,
        "model_weights_sha256": weights_before,
        "provenance_kind": "preregistered_autonomous_study",
    })
    _add_edge(
        substrate._inner, agent, "conducts_causal_debugging_study", study,
    )
    _nodes, specs = lay_whisper_architecture(
        substrate, agent, study, model,
    )

    trace = []
    substrate._inner.run_rules()
    while True:
        intervention = requested_intervention(substrate, study)
        if intervention is None:
            break
        request = _node_attrs(substrate, intervention)
        component_name = request["component_name"]
        spec = specs[component_name]
        changed_text = _run_probe_set(model, panel, spec)
        # Hook teardown is a deterministic structural control; one fixed
        # sentinel per intervention is sufficient to detect non-restoration.
        restoration_panel = panel[:1]
        restored_text = _run_probe_set(model, restoration_panel)
        counts = _discovery_counts(
            panel, changed_text, restored_text,
        )
        print(
            f"graph experiment {len(trace) + 1}: {component_name} -> {counts}",
            flush=True,
        )
        record_outcome(substrate, intervention, counts)
        substrate._inner.run_rules()
        trace.append({
            "sequence": len(trace),
            "component": component_name,
            "phase_level": request["phase_level"],
            "raw_counts": counts,
            "graph_component": {
                key: _node_attrs(substrate, _nodes[component_name]).get(key)
                for key in ("causal_utility", "causal_candidate", "tested")
            },
        })

    patch = authored_patch(substrate, study)
    control = authored_control(substrate, study)
    validation = None
    if patch is not None:
        if control is None:
            raise RuntimeError("graph authored a repair without its control")
        patch_attrs = _node_attrs(substrate, patch)
        control_attrs = _node_attrs(substrate, control)
        speech, nulls = _balanced_validation_probes(
            model, args.data_dir, validation_indices,
        )
        baseline = {
            "correct_speech": sum(
                probe.baseline_normalized == probe.reference
                for probe in speech
            ),
            "speech_hallucinations": sum(
                bool(probe.baseline_normalized)
                and probe.baseline_normalized != probe.reference
                for probe in speech
            ),
            "null_false_transcripts": sum(
                bool(probe.baseline_normalized) for probe in nulls
            ),
        }
        patched = _validation_arm(
            model, speech, nulls, specs[patch_attrs["component_name"]],
        )
        random_control = _validation_arm(
            model, speech, nulls, specs[control_attrs["component_name"]],
        )
        weights_after = state_dict_sha256(model)
        no_gradients = all(parameter.grad is None for parameter in model.parameters())
        validation_counts = {
            "speech_total": len(speech),
            "null_total": len(nulls),
            "baseline_correct_speech": baseline["correct_speech"],
            "baseline_speech_hallucinations": baseline["speech_hallucinations"],
            "baseline_null_false_transcripts": baseline["null_false_transcripts"],
            "patch_correct_speech": patched["correct_speech"],
            "patch_speech_hallucinations": patched["speech_hallucinations"],
            "patch_null_false_transcripts": patched["null_false_transcripts"],
            "control_correct_speech": random_control["correct_speech"],
            "control_speech_hallucinations": random_control[
                "speech_hallucinations"
            ],
            "control_null_false_transcripts": random_control[
                "null_false_transcripts"
            ],
            "weights_identical": int(weights_before == weights_after),
            "no_gradients": int(no_gradients),
        }
        record_validation(substrate, patch, validation_counts)
        substrate._inner.run_rules()
        validation = {
            "counts": validation_counts,
            "graph_verdict": _node_attrs(substrate, patch),
        }

    result = {
        "protocol": args.protocol.name,
        "model": "openai-whisper/base.en",
        "fsdd_revision": FSDD_REVISION,
        "host_decision_audit": audit_no_host_decisions(),
        "weights_sha256_before": weights_before,
        "weights_sha256_after": state_dict_sha256(model),
        "no_gradients": all(
            parameter.grad is None for parameter in model.parameters()
        ),
        "discovery_panel": {
            "counts": panel_counts,
            "items": [
                {
                    key: value
                    for key, value in asdict(probe).items()
                    if key != "audio"
                }
                for probe in panel
            ],
        },
        "graph_study": _node_attrs(substrate, study),
        "experiment_trace": trace,
        "graph_authored_patch": (
            _node_attrs(substrate, patch) if patch is not None else None
        ),
        "graph_authored_control": (
            _node_attrs(substrate, control) if control is not None else None
        ),
        "prospective_validation": validation,
        "elapsed_seconds": time.time() - started,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument(
        "--model-dir", type=Path,
        default=ROOT / "data" / "whisper-models",
    )
    parser.add_argument(
        "--output", type=Path,
        default=ROOT / "results" / "whisper_causal_debugger.json",
    )
    parser.add_argument("--discovery-quota", type=int, default=6)
    parser.add_argument("--discovery-start", type=int, default=10)
    parser.add_argument("--discovery-end", type=int, default=20)
    parser.add_argument("--validation-start", type=int, default=30)
    parser.add_argument("--validation-end", type=int, default=40)
    parser.add_argument(
        "--protocol", type=Path,
        default=ROOT / "WHISPER_CAUSAL_DEBUGGER_REPLICATION_PREREG.md",
    )
    args = parser.parse_args()
    result = run(args)
    print(json.dumps({
        "study": result["graph_study"],
        "patch": result["graph_authored_patch"],
        "validation": result["prospective_validation"],
        "elapsed_seconds": result["elapsed_seconds"],
        "output": str(args.output),
    }, indent=2))


if __name__ == "__main__":
    main()

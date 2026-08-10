"""Graph-native calibration and final test of a conditional Whisper repair."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import time

from domains.published_net_debugger import (
    authored_conditional_patch,
    audit_no_host_decisions,
    enumerate_whisper_components,
    intervention_hook,
    record_conditional_validation,
    record_gate_outcome,
    requested_gate_intervention,
    state_dict_sha256,
)
from domains.whisper_grounding_guard import (
    DIGIT_WORDS,
    normalize_digit_transcript,
)
from scripts.jabberwock_diagnoses_whisper import (
    FSDD_REVISION,
    _add_edge,
    _files_for_indices,
    _load_audio,
    _node_attrs,
    _phase_scramble,
)
from substrate.boot_core import boot_core, load_seeds_into


ROOT = Path(__file__).resolve().parents[1]
THRESHOLDS = (0.40, 0.50, 0.60, 0.70, 0.80)
COMPONENT = "encoder.blocks.1.self_attention.head.3"
CONTROL_COMPONENT = "encoder.blocks.0.self_attention.head.0"


def _decode_detail(model, audio) -> dict:
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
    raw = str(result["text"]).strip()
    probabilities = [
        float(segment["no_speech_prob"])
        for segment in result.get("segments", [])
    ]
    return {
        "raw": raw,
        "normalized": normalize_digit_transcript(raw),
        "no_speech_prob": max(probabilities) if probabilities else 0.0,
    }


def _balanced_audio(data_dir: Path, indices: range) -> tuple[list[dict], list[dict]]:
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
        speech.append({
            "identity": path.name,
            "reference": reference,
            "audio": audio,
        })
        nulls.append({
            "identity": f"{path.name}:phase",
            "reference": "",
            "audio": _phase_scramble(audio, f"conditional:{path.name}"),
        })
    return speech, nulls


def _with_baselines(model, rows: list[dict]) -> list[dict]:
    return [{**row, "baseline": _decode_detail(model, row["audio"])} for row in rows]


def _conditional_outputs(model, rows, spec, threshold) -> list[dict]:
    outputs = []
    for row in rows:
        baseline = row["baseline"]
        if baseline["normalized"] and baseline["no_speech_prob"] >= threshold:
            with intervention_hook(spec):
                outputs.append(_decode_detail(model, row["audio"]))
        else:
            outputs.append(baseline)
    return outputs


def _calibration_counts(speech, nulls, speech_outputs, null_outputs) -> dict:
    removed_speech = 0
    added_speech = 0
    correct_lost = 0
    for row, output in zip(speech, speech_outputs):
        before = row["baseline"]["normalized"]
        after = output["normalized"]
        before_hallucination = bool(before) and before != row["reference"]
        after_hallucination = bool(after) and after != row["reference"]
        removed_speech += int(before_hallucination and not after_hallucination)
        added_speech += int(not before_hallucination and after_hallucination)
        correct_lost += int(
            before == row["reference"] and after != row["reference"]
        )
    removed_null = 0
    added_null = 0
    for row, output in zip(nulls, null_outputs):
        before = bool(row["baseline"]["normalized"])
        after = bool(output["normalized"])
        removed_null += int(before and not after)
        added_null += int(not before and after)
    return {
        "speech_hallucinations_removed": removed_speech,
        "speech_hallucinations_added": added_speech,
        "null_false_transcripts_removed": removed_null,
        "null_false_transcripts_added": added_null,
        "correct_controls_lost": correct_lost,
    }


def _validation_counts(speech, nulls, patch_outputs, control_outputs, model, before_hash):
    baseline_correct = sum(
        row["baseline"]["normalized"] == row["reference"] for row in speech
    )
    baseline_speech_hall = sum(
        bool(row["baseline"]["normalized"])
        and row["baseline"]["normalized"] != row["reference"]
        for row in speech
    )
    baseline_null = sum(
        bool(row["baseline"]["normalized"]) for row in nulls
    )

    def arm(outputs):
        return {
            "correct": sum(
                output["normalized"] == row["reference"]
                for row, output in zip(speech, outputs[:len(speech)])
            ),
            "speech_hall": sum(
                bool(output["normalized"])
                and output["normalized"] != row["reference"]
                for row, output in zip(speech, outputs[:len(speech)])
            ),
            "null": sum(
                bool(output["normalized"])
                for output in outputs[len(speech):]
            ),
        }

    patch = arm(patch_outputs)
    control = arm(control_outputs)
    return {
        "speech_total": len(speech),
        "null_total": len(nulls),
        "baseline_correct_speech": baseline_correct,
        "baseline_speech_hallucinations": baseline_speech_hall,
        "baseline_null_false_transcripts": baseline_null,
        "patch_correct_speech": patch["correct"],
        "patch_speech_hallucinations": patch["speech_hall"],
        "patch_null_false_transcripts": patch["null"],
        "control_correct_speech": control["correct"],
        "control_speech_hallucinations": control["speech_hall"],
        "control_null_false_transcripts": control["null"],
        "weights_identical": int(before_hash == state_dict_sha256(model)),
        "no_gradients": int(all(
            parameter.grad is None for parameter in model.parameters()
        )),
    }


def run(args) -> dict:
    if audit_no_host_decisions():
        raise RuntimeError(audit_no_host_decisions())
    import whisper

    started = time.time()
    model = whisper.load_model(
        "base.en", device="cpu", download_root=str(args.model_dir),
    )
    model.eval()
    before_hash = state_dict_sha256(model)
    specs = {
        spec["name"]: spec for spec in enumerate_whisper_components(model)
    }
    target_spec = specs[COMPONENT]
    control_spec = specs[CONTROL_COMPONENT]

    calibration_speech, calibration_nulls = _balanced_audio(
        args.data_dir, range(10, 20),
    )
    calibration_speech = _with_baselines(model, calibration_speech)
    calibration_nulls = _with_baselines(model, calibration_nulls)

    substrate, agent = boot_core(seeds=())
    load_seeds_into(substrate, agent, ["published_net_causal_debugger"])
    study = substrate.add_node("ConditionalRepairStudy", {
        "status": "ready",
        "component_name": COMPONENT,
        "control_component_name": CONTROL_COMPONENT,
        "protocol": "WHISPER_CONDITIONAL_REPAIR_PREREG.md",
        "provenance_kind": "frozen_from_autonomous_causal_replication",
    })
    _add_edge(
        substrate._inner, agent, "conducts_conditional_repair_study", study,
    )
    candidates = {}
    for order, threshold in enumerate(THRESHOLDS):
        candidate = substrate.add_node("RuntimeGateCandidate", {
            "threshold": threshold,
            "experiment_order": float(order),
            "tested": 0.0,
            "causal_candidate": 0.0,
            "causal_utility": 0.0,
            "provenance_kind": "preregistered_threshold",
        })
        _add_edge(
            substrate._inner, study, "has_runtime_gate_candidate", candidate,
        )
        candidates[threshold] = candidate

    trace = []
    substrate._inner.run_rules()
    while True:
        intervention = requested_gate_intervention(substrate, study)
        if intervention is None:
            break
        attrs = _node_attrs(substrate, intervention)
        threshold = float(attrs["threshold"])
        speech_outputs = _conditional_outputs(
            model, calibration_speech, target_spec, threshold,
        )
        null_outputs = _conditional_outputs(
            model, calibration_nulls, target_spec, threshold,
        )
        counts = _calibration_counts(
            calibration_speech, calibration_nulls,
            speech_outputs, null_outputs,
        )
        record_gate_outcome(substrate, intervention, counts)
        substrate._inner.run_rules()
        candidate_attrs = _node_attrs(substrate, candidates[threshold])
        trace.append({
            "threshold": threshold,
            "raw_counts": counts,
            "graph_utility": candidate_attrs["causal_utility"],
            "graph_candidate": candidate_attrs["causal_candidate"],
        })
        print(f"graph gate {threshold:.2f}: {trace[-1]}", flush=True)

    patch = authored_conditional_patch(substrate, study)
    validation = None
    if patch is not None:
        patch_attrs = _node_attrs(substrate, patch)
        threshold = float(patch_attrs["threshold"])
        speech, nulls = _balanced_audio(args.data_dir, range(40, 50))
        speech = _with_baselines(model, speech)
        nulls = _with_baselines(model, nulls)
        rows = speech + nulls
        patch_outputs = _conditional_outputs(
            model, rows, target_spec, threshold,
        )
        control_outputs = _conditional_outputs(
            model, rows, control_spec, threshold,
        )
        counts = _validation_counts(
            speech, nulls, patch_outputs, control_outputs, model, before_hash,
        )
        record_conditional_validation(substrate, patch, counts)
        substrate._inner.run_rules()
        validation = {
            "counts": counts,
            "graph_verdict": _node_attrs(substrate, patch),
        }

    result = {
        "protocol": "WHISPER_CONDITIONAL_REPAIR_PREREG.md",
        "model": "openai-whisper/base.en",
        "fsdd_revision": FSDD_REVISION,
        "fixed_component": COMPONENT,
        "fixed_control_component": CONTROL_COMPONENT,
        "host_decision_audit": audit_no_host_decisions(),
        "calibration_trace": trace,
        "graph_study": _node_attrs(substrate, study),
        "graph_authored_patch": (
            _node_attrs(substrate, patch) if patch is not None else None
        ),
        "prospective_validation": validation,
        "weights_sha256_before": before_hash,
        "weights_sha256_after": state_dict_sha256(model),
        "no_gradients": all(
            parameter.grad is None for parameter in model.parameters()
        ),
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
        default=ROOT / "results" / "whisper_conditional_repair.json",
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

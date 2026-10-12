"""Build a blinded, non-scoring Phase 8 output-adjudication packet.

The rater packet contains only case context, anonymous response aliases, and
empty score fields.  A separate key preserves system/run provenance.  This
module never scores response text or infers capability.
"""
from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any, Mapping, Sequence

from evaluation.comparative_release_gate import BASELINES
from evaluation.conversational_manifold_phase0 import load_corpus
from evaluation.phase8_corpus_runner import CONTEXT_AWARE_PROTOCOL_ID


PACKET_SCHEMA = "phase8_blinded_output_packet.v2"
KEY_SCHEMA = "phase8_blinded_output_key.v2"
BEHAVIOR_DIMENSIONS = (
    "interpretation", "grounding", "action", "repair", "calibration",
)
MODEL_TRACKS = (
    ("conversational_manifold", "conversational_manifold", 0),
    ("eliza_floor", "eliza_floor", 0),
    ("small_llm", "small_llm", 0),
    ("modern_llm_seed42", "modern_llm", 0),
    ("modern_llm_seed43", "modern_llm", 1),
)
HUMAN_TRACKS = (("base_human", "base_human", 0),
                ("advanced_human", "advanced_human", 0))
ALIASES = tuple("ABCDEFG")


def _case_id_to_observation(run: Mapping[str, Any], system: str):
    observations = run.get("observations")
    if not isinstance(observations, list):
        raise ValueError(f"{system}: observations must be a list")
    result: dict[str, Mapping[str, Any]] = {}
    for item in observations:
        if not isinstance(item, Mapping):
            raise ValueError(f"{system}: observation must be an object")
        case_id = str(item.get("id") or item.get("case_id") or "")
        if not case_id or case_id in result:
            raise ValueError(f"{system}: missing or duplicate case ID {case_id!r}")
        result[case_id] = item
    return result


def _response(item: Mapping[str, Any], system: str) -> str:
    if system == "conversational_manifold":
        value = item.get("reply")
    elif system == "eliza_floor":
        value = item.get("output")
    elif system in {"base_human", "advanced_human"}:
        value = item.get("response")
        if isinstance(value, Mapping):
            value = value.get("text") or value.get("stdout")
        if value is None:
            value = item.get("output")
    else:
        response = item.get("response")
        value = (response.get("stdout")
                 if isinstance(response, Mapping) else None)
    if not isinstance(value, str):
        raise ValueError(f"{system}: response is missing or not a string")
    return value


def _run_protocol(run: Mapping[str, Any], system: str):
    expected = CONTEXT_AWARE_PROTOCOL_ID
    actual = str(run.get("protocol_id") or run.get("protocol") or "")
    if actual != expected:
        raise ValueError(f"{system}: protocol mismatch {actual!r}")
    if system != "conversational_manifold":
        expected_profile = "event_context_v5_history8"
        if run.get("input_profile") != expected_profile:
            raise ValueError(f"{system}: input profile mismatch")
        if (system in {"eliza_floor", "small_llm", "modern_llm"}
                and run.get("session_history_limit") != 8):
            raise ValueError(f"{system}: history limit must be eight")


def _response_tracks(
    corpus: Mapping[str, Any],
    target_run: Mapping[str, Any],
    reference_runs: Mapping[str, Mapping[str, Any] | Sequence[Mapping[str, Any]]],
):
    corpus_events = list(corpus.get("events") or ())
    if not corpus_events:
        raise ValueError("corpus has no events")
    case_ids = [str(event.get("id") or "") for event in corpus_events]
    if not all(case_ids) or len(case_ids) != len(set(case_ids)):
        raise ValueError("corpus case IDs must be present and unique")
    if (str(corpus.get("protocol_id") or CONTEXT_AWARE_PROTOCOL_ID)
            != CONTEXT_AWARE_PROTOCOL_ID):
        raise ValueError("corpus protocol mismatch")

    run_map: dict[str, list[Mapping[str, Any]]] = {
        "conversational_manifold": [target_run],
    }
    for system in BASELINES:
        raw = reference_runs.get(system)
        if isinstance(raw, Mapping):
            runs = [raw]
        elif isinstance(raw, Sequence) and not isinstance(raw, (str, bytes)):
            runs = list(raw)
        else:
            runs = []
        if system in {"eliza_floor", "small_llm", "modern_llm"} and not runs:
            raise ValueError(f"missing required raw run: {system}")
        if system in {"small_llm", "modern_llm"} and len(runs) != 2:
            raise ValueError(f"{system}: exactly two seeded runs are required")
        if system in {"base_human", "advanced_human"} and len(runs) > 1:
            raise ValueError(f"{system}: exactly one human session is supported")
        run_map[system] = runs

    tracks: dict[str, dict[str, str]] = {}
    provenance: dict[str, dict[str, Any]] = {}
    for system in ("conversational_manifold", "eliza_floor", "small_llm",
                   "modern_llm"):
        runs = run_map[system]
        maps = []
        for run in runs:
            _run_protocol(run, system)
            maps.append(_case_id_to_observation(run, system))
        for mapping in maps:
            if set(mapping) != set(case_ids):
                missing = sorted(set(case_ids) - set(mapping))
                extra = sorted(set(mapping) - set(case_ids))
                raise ValueError(
                    f"{system}: case mismatch (missing={missing}, extra={extra})")
        run_tracks = [
            {case_id: _response(mapping[case_id], system)
             for case_id in case_ids}
            for mapping in maps
        ]
        identical = all(track == run_tracks[0] for track in run_tracks[1:])
        if system == "small_llm" and not identical:
            raise ValueError(
                f"{system}: Gemma repeated run responses differ; cannot collapse")
        if system == "small_llm":
            tracks[system] = run_tracks[0]
        else:
            tracks[system] = run_tracks[0]
            if system == "modern_llm":
                tracks["modern_llm_seed42"] = run_tracks[0]
                tracks["modern_llm_seed43"] = run_tracks[1]
        provenance[system] = {
            "run_count": len(runs),
            "source_paths": [str(run.get("source_path") or "") for run in runs],
            "run_ids": [str(run.get("run_id") or "") for run in runs],
            "repeat_outputs_identical": identical if len(runs) > 1 else None,
        }
    for system in ("base_human", "advanced_human"):
        runs = run_map[system]
        if not runs:
            continue
        run = runs[0]
        _run_protocol(run, system)
        mapping = _case_id_to_observation(run, system)
        if set(mapping) != set(case_ids):
            missing = sorted(set(case_ids) - set(mapping))
            extra = sorted(set(mapping) - set(case_ids))
            raise ValueError(
                f"{system}: case mismatch (missing={missing}, extra={extra})")
        tracks[system] = {
            case_id: _response(mapping[case_id], system)
            for case_id in case_ids
        }
        provenance[system] = {
            "run_count": 1,
            "source_paths": [str(run.get("source_path") or "")],
            "run_ids": [str(run.get("run_id") or "")],
            "repeat_outputs_identical": None,
        }
    return corpus_events, case_ids, tracks, provenance


def build_blinded_packet(
    corpus: Mapping[str, Any],
    target_run: Mapping[str, Any],
    reference_runs: Mapping[str, Mapping[str, Any] | Sequence[Mapping[str, Any]]],
    *, rng: random.Random | None = None,
):
    """Return ``(rater_packet, private_key)`` without assigning scores."""
    corpus_events, case_ids, tracks, provenance = _response_tracks(
        corpus, target_run, reference_runs)
    rng = rng or random.SystemRandom()
    case_codes = {case_id: f"case_{index + 1:03d}"
                  for index, case_id in enumerate(case_ids)}
    present_humans = tuple(track for track in HUMAN_TRACKS
                           if track[0] in tracks)
    packet_tracks = MODEL_TRACKS + present_humans
    history: dict[str, list[tuple[str, str]]] = {
        track[0]: [] for track in packet_tracks
    }
    packet_cases = []
    key_cases = []

    for event, case_id in zip(corpus_events, case_ids):
        samples = []
        alias_mapping = {}
        aliases = list(ALIASES)
        rng.shuffle(aliases)
        for (track_id, system, run_index), alias in zip(packet_tracks, aliases):
            past = history[track_id][-8:]
            setup = event.get("setup") or {}
            held_facts = [
                {"topic": str(item.get("topic") or ""),
                 "answer": str(item.get("answer") or "")}
                for item in setup.get("held_answers") or ()
                if isinstance(item, Mapping)
            ]
            response = tracks[track_id][case_id]
            samples.append({
                "response_code": alias,
                "context": {
                    "interaction_mode": str(
                        event.get("event_mode") or "turn_compatible"),
                    "interaction_relation": str(
                        event.get("interaction_relation") or "turn_compatible"),
                    "held_facts": held_facts,
                    "history": [
                        {"user": previous_signal,
                         "assistant": previous_response}
                        for previous_signal, previous_response in past
                    ],
                    "current_message": str(event.get("signal") or ""),
                },
                "response": response,
            })
            alias_mapping[alias] = {
                "system": system,
                "run_index": run_index if system == "modern_llm" else None,
            }
            history[track_id].append((str(event.get("signal") or ""), response))
        rng.shuffle(samples)
        code = case_codes[case_id]
        packet_cases.append({"case_code": code, "samples": samples})
        key_cases.append({"case_code": code, "case_id": case_id,
                          "response_aliases": alias_mapping})

    packet = {
        "schema": PACKET_SCHEMA,
        "protocol_id": CONTEXT_AWARE_PROTOCOL_ID,
        "corpus_event_count": len(case_ids),
        "blindness": {
            "system_names_included": False,
            "corpus_labels_included": False,
            "response_aliases_randomized_per_case": True,
            "identical_seed_repeats_collapsed_only_after_exact_match": True,
            "nonidentical_seed_repeats_kept_as_distinct_tracks": True,
            "human_sessions_included_only_when_supplied_and_protocol_valid": True,
        },
        "score_fields": {
            dimension: {"values": [0.0, 0.5, 1.0, "not_applicable"],
                       "notes_required_below_1": True}
            for dimension in BEHAVIOR_DIMENSIONS
        },
        "annotation_rows": [
            {"case_code": item["case_code"],
             "response_code": sample["response_code"],
             "scores": {dimension: None for dimension in BEHAVIOR_DIMENSIONS},
             "evidence_notes": {dimension: ""
                                for dimension in BEHAVIOR_DIMENSIONS}}
            for item in packet_cases for sample in item["samples"]
        ],
        "cases": packet_cases,
        "limitations": [
        "This packet does not test memory or learning comparability.",
            "It does not score provenance or cost from response wording.",
            "Target access to graph-resident information exceeds this shared text view; memory remains unavailable.",
            "Do not infer an external action occurred from a response claim alone.",
        ],
    }
    key = {
        "schema": KEY_SCHEMA,
        "protocol_id": CONTEXT_AWARE_PROTOCOL_ID,
        "distribution_warning": "PRIVATE: do not provide this key to raters.",
        "source_provenance": provenance,
        "cases": key_cases,
    }
    return packet, key


def read_json(path: Path):
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object in {path}")
    return {**value, "source_path": str(path)}


def write_json(path: Path, value: Mapping[str, Any]):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, default=Path(
        "tests/fixtures/conversational_manifold/phase0_events.json"))
    parser.add_argument("--target", type=Path, required=True)
    parser.add_argument("--eliza", type=Path, required=True)
    parser.add_argument("--small-llm", type=Path, action="append", required=True)
    parser.add_argument("--modern-llm", type=Path, action="append", required=True)
    parser.add_argument("--base-human", type=Path,
                        help="Optional protocol-matched base-human session JSON")
    parser.add_argument("--advanced-human", type=Path,
                        help="Optional protocol-matched expert-human session JSON")
    parser.add_argument("--packet-out", type=Path, required=True)
    parser.add_argument("--key-out", type=Path, required=True)
    args = parser.parse_args()
    if args.packet_out.resolve() == args.key_out.resolve():
        parser.error("packet and private key must use different output paths")
    references = {
        "eliza_floor": read_json(args.eliza),
        "small_llm": [read_json(path) for path in args.small_llm],
        "modern_llm": [read_json(path) for path in args.modern_llm],
    }
    if args.base_human:
        references["base_human"] = read_json(args.base_human)
    if args.advanced_human:
        references["advanced_human"] = read_json(args.advanced_human)
    packet, key = build_blinded_packet(
        read_json(args.corpus), read_json(args.target), references)
    write_json(args.packet_out, packet)
    write_json(args.key_out, key)
    print(json.dumps({"packet": str(args.packet_out), "private_key": str(args.key_out),
                      "cases": packet["corpus_event_count"],
                      "responses": len(packet["annotation_rows"]),
                      "status": "unscored"}))

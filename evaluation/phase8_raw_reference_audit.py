"""Audit collected Phase 8 reference envelopes without scoring outputs.

This is the safe bridge between raw collection and blinded adjudication.  It
checks corpus binding, protocol identity, observation completeness, and
collection failures.  It deliberately never interprets response text or
turns raw outputs into capability scores.
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Mapping

from evaluation.comparative_release_gate import BASELINES


SCHEMA = "phase8_raw_reference_audit.v1"
CONTEXT_AWARE_PROTOCOL_ID = \
    "phase8a-fixed-phase0-corpus-v5-event-context-history8"
MINIMUM_RUNS = {
    "eliza_floor": 1,
    "small_llm": 2,
    "modern_llm": 2,
    "base_human": 1,
    "advanced_human": 1,
}
REQUIRED_INPUT_PROFILES = {
    CONTEXT_AWARE_PROTOCOL_ID: {
        "eliza_floor": "event_context_v5_history8",
        "small_llm": "event_context_v5_history8",
        "modern_llm": "event_context_v5_history8",
        "base_human": "event_context_v5_history8",
        "advanced_human": "event_context_v5_history8",
    },
}


def _input_profile_matches(protocol_id: str, system: str,
                           run: Mapping[str, Any]) -> bool:
    required = REQUIRED_INPUT_PROFILES.get(protocol_id, {}).get(system)
    if required is None:
        return True
    if run.get("input_profile") != required:
        return False
    if system in {"eliza_floor", "small_llm", "modern_llm"}:
        return run.get("session_history_limit") == 8
    return True


def _has_response(system: str, observation: Mapping[str, Any]) -> bool:
    """Check response-body presence without interpreting its content."""
    if system == "eliza_floor":
        value = observation.get("output")
    elif system in {"small_llm", "modern_llm"}:
        response = observation.get("response")
        value = response.get("stdout") if isinstance(response, Mapping) else None
    else:
        value = observation.get("response")
        if isinstance(value, Mapping):
            value = value.get("text") or value.get("stdout")
        if value is None:
            value = observation.get("output")
    return isinstance(value, str) and bool(value.strip())


def audit_raw_reference_runs(
    corpus: Mapping[str, Any],
    runs: Mapping[str, Mapping[str, Any] | list[Mapping[str, Any]]],
) -> dict[str, Any]:
    expected_ids = [str(item.get("id")) for item in corpus.get("events", ())]
    expected = set(expected_ids)
    rows: list[dict[str, Any]] = []
    for system in BASELINES:
        value = runs.get(system)
        if isinstance(value, Mapping):
            system_runs = [value]
        elif isinstance(value, list):
            system_runs = [run for run in value if isinstance(run, Mapping)]
            invalid_run_count = len(value) - len(system_runs)
        else:
            system_runs = []
            invalid_run_count = 0
        if isinstance(value, Mapping):
            invalid_run_count = 0
        if not system_runs:
            rows.append({"system": system, "status": "missing",
                         "run_count": 0,
                         "invalid_run_count": invalid_run_count,
                         "minimum_run_count": MINIMUM_RUNS[system],
                         "complete_run_count": 0,
                         "observation_count": 0,
                         "missing_case_count": len(expected_ids),
                         "duplicate_case_count": 0,
                         "unknown_case_count": 0,
                         "collection_failure_count": 0,
                         "score_interpretation_performed": False})
            continue
        run_audits = []
        for run in system_runs:
            observations = run.get("observations")
            observations = observations if isinstance(observations, list) else []
            ids = [str(item.get("case_id", ""))
                   for item in observations if isinstance(item, Mapping)]
            missing_responses = sum(
                1 for item in observations
                if not isinstance(item, Mapping)
                or not _has_response(system, item)
            )
            counts = Counter(ids)
            duplicate_ids = sorted(key for key, count in counts.items() if count > 1)
            unknown_ids = sorted(set(ids) - expected)
            missing_ids = sorted(expected - set(ids))
            failures = run.get("collection_failures")
            failures = failures if isinstance(failures, list) else []
            declared_system = run.get("system")
            # Collection files commonly serialize an unset ``system`` as
            # JSON null. In that case the typed key under which the caller
            # supplied this run is the identity assertion. A contradictory
            # non-null field still fails closed.
            identity_ok = declared_system in (None, system)
            expected_protocol = str(corpus.get("protocol_id") or
                                    run.get("protocol_id") or "")
            profile_ok = _input_profile_matches(
                expected_protocol, system, run)
            protocol_ok = (run.get("protocol_id") == expected_protocol
                           and identity_ok and profile_ok)
            complete = (len(observations) == len(expected_ids)
                        and not duplicate_ids and not unknown_ids
                        and not missing_ids and not failures and protocol_ok
                        and missing_responses == 0)
            run_audits.append({
                "status": "complete_raw" if complete else "incomplete_raw",
                "observation_count": len(observations),
                "missing_case_count": len(missing_ids),
                "duplicate_case_count": len(duplicate_ids),
                "unknown_case_count": len(unknown_ids),
                "collection_failure_count": len(failures),
                "missing_response_count": missing_responses,
                "protocol_id": run.get("protocol_id"),
                "protocol_match": protocol_ok,
                "system_identity_source": (
                    "run_field" if declared_system is not None
                    else "typed_run_group_key"),
                "system_identity_match": identity_ok,
                "input_profile_match": profile_ok,
                "scorecard_collection_status": (
                    (run.get("scorecard") or {}).get("collection_status")
                    if isinstance(run.get("scorecard"), Mapping) else None),
            })
        complete_runs = sum(run["status"] == "complete_raw" for run in run_audits)
        minimum_runs = MINIMUM_RUNS[system]
        row_complete = (invalid_run_count == 0
                        and complete_runs >= minimum_runs
                        and complete_runs == len(run_audits))
        aggregate_protocols = sorted({str(run["protocol_id"] or "")
                                       for run in run_audits})
        rows.append({
            "system": system,
            "status": "complete_raw" if row_complete else "incomplete_raw",
            "run_count": len(run_audits),
            "invalid_run_count": invalid_run_count,
            "minimum_run_count": minimum_runs,
            "complete_run_count": complete_runs,
            "observation_count": sum(run["observation_count"] for run in run_audits),
            "missing_case_count": sum(run["missing_case_count"] for run in run_audits),
            "duplicate_case_count": sum(run["duplicate_case_count"] for run in run_audits),
            "unknown_case_count": sum(run["unknown_case_count"] for run in run_audits),
            "collection_failure_count": sum(run["collection_failure_count"]
                                             for run in run_audits),
            "missing_response_count": sum(run["missing_response_count"]
                                           for run in run_audits),
            "protocol_id": (aggregate_protocols[0]
                            if len(aggregate_protocols) == 1 else None),
            "protocol_match": all(run["protocol_match"] for run in run_audits),
            "runs": run_audits,
            "score_interpretation_performed": False,
        })
    counts = Counter(row["status"] for row in rows)
    human_rows = [row for row in rows
                  if row["system"] in {"base_human", "advanced_human"}]
    supplied_human_rows = [row for row in human_rows
                           if row["run_count"] > 0]
    if all(row["status"] == "complete_raw" for row in human_rows):
        human_status = "complete_raw"
    elif supplied_human_rows:
        human_status = "incomplete_raw"
    else:
        human_status = "missing"
    return {
        "schema": SCHEMA,
        "corpus_event_count": len(expected_ids),
        "reference_count": len(BASELINES),
        "status_counts": dict(sorted(counts.items())),
        "rows": rows,
        "surface_text_used_as_evidence": False,
        "score_interpretation_performed": False,
        "human_reference_status": human_status,
        "status": "measured" if all(
            row["status"] in {"complete_raw", "not_comparable"}
            for row in rows
        ) else "incomplete",
    }


__all__ = ["SCHEMA", "audit_raw_reference_runs"]


if __name__ == "__main__":
    import argparse
    import json
    from pathlib import Path

    from evaluation.conversational_manifold_phase0 import FIXTURE, load_corpus
    from evaluation.phase8_corpus_runner import PROTOCOL_ID

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="append", default=[], metavar="SYSTEM=PATH",
                        help="Raw reference collection JSON; may be supplied more than once")
    parser.add_argument("--protocol-id", default=PROTOCOL_ID,
                        help=("Expected input protocol shared by all supplied runs "
                              f"(default: {PROTOCOL_ID})"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    runs: dict[str, list[Mapping[str, Any]]] = {}
    for item in args.run:
        system, separator, path = item.partition("=")
        if not separator or not system or not path:
            parser.error(f"invalid --run {item!r}; expected SYSTEM=PATH")
        runs.setdefault(system, []).append(
            json.loads(Path(path).read_text(encoding="utf-8")))
    corpus = load_corpus()
    corpus["protocol_id"] = args.protocol_id
    result = audit_raw_reference_runs(corpus, runs)
    result["corpus_fixture"] = str(FIXTURE)
    raw_run_paths: dict[str, list[str]] = {}
    for item in args.run:
        system, _, path = item.partition("=")
        raw_run_paths.setdefault(system, []).append(path)
    result["raw_run_paths"] = raw_run_paths
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")
    print(json.dumps({"output": str(args.output), "status": result["status"],
                      "counts": result["status_counts"],
                      "score_interpretation_performed": False}))

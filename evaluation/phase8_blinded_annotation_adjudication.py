"""Validate blinded dual ratings without interpreting response content.

This is a pre-score evidence-integrity step. It binds two independent rater
files to one blinded packet, reports nominal agreement, and exposes unresolved
disagreements for a blinded adjudicator. It never maps aliases to systems,
scores output text, or creates capability scorecards.
"""
from __future__ import annotations

from collections import Counter
import hashlib
import json
from typing import Any, Mapping, Sequence

from evaluation.phase8_blinded_annotation_packet import (
    BEHAVIOR_DIMENSIONS, PACKET_SCHEMA,
)


RATER_SCHEMA = "phase8_blinded_rater_annotations.v1"
ADJUDICATION_SCHEMA = "phase8_blinded_adjudication.v1"
REPORT_SCHEMA = "phase8_blinded_annotation_audit.v1"
SCORE_VALUES = (0.0, 0.5, 1.0, "not_applicable")


def packet_digest(packet: Mapping[str, Any]) -> str:
    """Stable identity for the exact blinded packet seen by both raters."""
    encoded = json.dumps(packet, sort_keys=True, separators=(",", ":"),
                         ensure_ascii=False, allow_nan=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def make_rater_template(packet: Mapping[str, Any], rater_id: str) -> dict[str, Any]:
    """Create an empty independent rating file bound to this packet."""
    if packet.get("schema") != PACKET_SCHEMA:
        raise ValueError("unsupported blinded packet schema")
    if not str(rater_id).strip():
        raise ValueError("rater_id must be a non-empty blind identifier")
    return {
        "schema": RATER_SCHEMA,
        "protocol_id": packet.get("protocol_id"),
        "packet_sha256": packet_digest(packet),
        "rater_id": str(rater_id),
        "annotation_rows": [
            {
                "case_code": row["case_code"],
                "response_code": row["response_code"],
                "scores": {dimension: None for dimension in BEHAVIOR_DIMENSIONS},
                "evidence_notes": {dimension: ""
                                   for dimension in BEHAVIOR_DIMENSIONS},
            }
            for row in packet.get("annotation_rows", ())
        ],
    }


def _row_key(row: Mapping[str, Any]) -> tuple[str, str]:
    return str(row.get("case_code") or ""), str(row.get("response_code") or "")


def _packet_rows(packet: Mapping[str, Any]) -> dict[tuple[str, str], Mapping[str, Any]]:
    if packet.get("schema") != PACKET_SCHEMA:
        raise ValueError("unsupported blinded packet schema")
    rows = packet.get("annotation_rows")
    if not isinstance(rows, list) or not rows:
        raise ValueError("packet annotation_rows must be a non-empty list")
    expected: dict[tuple[str, str], Mapping[str, Any]] = {}
    for row in rows:
        if not isinstance(row, Mapping):
            raise ValueError("packet annotation row must be an object")
        key = _row_key(row)
        if not all(key) or key in expected:
            raise ValueError(f"packet has missing or duplicate row key {key!r}")
        expected[key] = row
    return expected


def _validated_rater(
    packet: Mapping[str, Any], rater: Mapping[str, Any], rater_name: str,
) -> tuple[str, dict[tuple[str, str], dict[str, Any]]]:
    expected = _packet_rows(packet)
    if rater.get("schema") != RATER_SCHEMA:
        raise ValueError(f"{rater_name}: unsupported annotation schema")
    if rater.get("protocol_id") != packet.get("protocol_id"):
        raise ValueError(f"{rater_name}: protocol mismatch")
    if rater.get("packet_sha256") != packet_digest(packet):
        raise ValueError(f"{rater_name}: packet digest mismatch")
    rater_id = str(rater.get("rater_id") or "").strip()
    if not rater_id:
        raise ValueError(f"{rater_name}: rater_id is required")
    rows = rater.get("annotation_rows")
    if not isinstance(rows, list):
        raise ValueError(f"{rater_name}: annotation_rows must be a list")
    result: dict[tuple[str, str], dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, Mapping):
            raise ValueError(f"{rater_name}: annotation row must be an object")
        key = _row_key(row)
        if key in result:
            raise ValueError(f"{rater_name}: duplicate annotation row {key!r}")
        if key not in expected:
            raise ValueError(f"{rater_name}: unknown annotation row {key!r}")
        scores = row.get("scores")
        notes = row.get("evidence_notes")
        if not isinstance(scores, Mapping) or set(scores) != set(BEHAVIOR_DIMENSIONS):
            raise ValueError(f"{rater_name}: {key!r} must score every behavior dimension")
        if not isinstance(notes, Mapping) or set(notes) != set(BEHAVIOR_DIMENSIONS):
            raise ValueError(f"{rater_name}: {key!r} needs notes for every dimension")
        normalized_scores = {}
        normalized_notes = {}
        for dimension in BEHAVIOR_DIMENSIONS:
            score = scores[dimension]
            numeric_score = (not isinstance(score, bool)
                             and isinstance(score, (int, float))
                             and score in (0, 0.5, 1))
            if not (numeric_score or score == "not_applicable"):
                raise ValueError(
                    f"{rater_name}: invalid {dimension} score {score!r} at {key!r}")
            note = notes[dimension]
            if not isinstance(note, str):
                raise ValueError(f"{rater_name}: {dimension} note must be text")
            if score != 1.0 and not note.strip():
                raise ValueError(
                    f"{rater_name}: {dimension} note required below 1.0 at {key!r}")
            normalized_scores[dimension] = (
                float(score) if numeric_score else score)
            normalized_notes[dimension] = note.strip()
        result[key] = {"scores": normalized_scores,
                       "evidence_notes": normalized_notes}
    missing = sorted(set(expected) - set(result))
    if missing:
        raise ValueError(f"{rater_name}: missing {len(missing)} annotation rows")
    return rater_id, result


def _agreement(first: Sequence[Any], second: Sequence[Any]) -> dict[str, Any]:
    n = len(first)
    if n != len(second) or not n:
        raise ValueError("agreement inputs must be equally sized and non-empty")
    observed = sum(a == b for a, b in zip(first, second)) / n
    first_counts, second_counts = Counter(first), Counter(second)
    expected = sum(first_counts[v] * second_counts[v] for v in SCORE_VALUES) / (n * n)
    kappa = ((observed - expected) / (1.0 - expected)
             if expected < 1.0 else None)
    return {"n": n, "exact_agreement": observed,
            "cohen_kappa_nominal": kappa}


def _validated_adjudication(
    disagreements: set[tuple[str, str]], adjudication: Mapping[str, Any],
    protocol_id: str, digest: str,
) -> tuple[str, dict[tuple[str, str], dict[str, Any]]]:
    if adjudication.get("schema") != ADJUDICATION_SCHEMA:
        raise ValueError("unsupported adjudication schema")
    if adjudication.get("protocol_id") != protocol_id:
        raise ValueError("adjudication protocol mismatch")
    if adjudication.get("packet_sha256") != digest:
        raise ValueError("adjudication packet digest mismatch")
    adjudicator_id = str(adjudication.get("adjudicator_id") or "").strip()
    if not adjudicator_id:
        raise ValueError("adjudicator_id is required")
    rows = adjudication.get("rows")
    if not isinstance(rows, list):
        raise ValueError("adjudication rows must be a list")
    result = {}
    for row in rows:
        if not isinstance(row, Mapping):
            raise ValueError("adjudication row must be an object")
        key = _row_key(row)
        if key in result:
            raise ValueError(f"duplicate adjudication row {key!r}")
        if key not in disagreements:
            raise ValueError(f"adjudication row is not disputed: {key!r}")
        scores, notes = row.get("final_scores"), row.get("final_evidence_notes")
        note = row.get("resolution_note")
        if not isinstance(scores, Mapping) or set(scores) != set(BEHAVIOR_DIMENSIONS):
            raise ValueError(f"{key!r} must resolve every behavior dimension")
        if not isinstance(notes, Mapping) or set(notes) != set(BEHAVIOR_DIMENSIONS):
            raise ValueError(f"{key!r} needs evidence notes for every dimension")
        if not isinstance(note, str) or not note.strip():
            raise ValueError(f"{key!r} requires a blinded resolution note")
        normalized = {}
        normalized_notes = {}
        for dimension, score in scores.items():
            numeric_score = (not isinstance(score, bool)
                             and isinstance(score, (int, float))
                             and score in (0, 0.5, 1))
            if not (numeric_score or score == "not_applicable"):
                raise ValueError(f"invalid adjudicated score at {key!r}/{dimension}")
            evidence_note = notes[dimension]
            if not isinstance(evidence_note, str):
                raise ValueError(f"{key!r}/{dimension} evidence note must be text")
            if score != 1.0 and not evidence_note.strip():
                raise ValueError(
                    f"{key!r}/{dimension} evidence note required below 1.0")
            normalized[dimension] = float(score) if numeric_score else score
            normalized_notes[dimension] = evidence_note.strip()
        result[key] = {"final_scores": normalized,
                       "final_evidence_notes": normalized_notes,
                       "resolution_note": note.strip()}
    missing = sorted(disagreements - set(result))
    if missing:
        raise ValueError(f"adjudication missing {len(missing)} disputed rows")
    return adjudicator_id, result


def audit_blinded_annotations(
    packet: Mapping[str, Any], rater_a: Mapping[str, Any],
    rater_b: Mapping[str, Any], *,
    adjudication: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Check dual-rating completeness and agreement, without scoring systems."""
    expected = _packet_rows(packet)
    a_id, a_rows = _validated_rater(packet, rater_a, "rater_a")
    b_id, b_rows = _validated_rater(packet, rater_b, "rater_b")
    if a_id == b_id:
        raise ValueError("independent raters must have distinct blinded IDs")
    per_dimension = {}
    disagreements: set[tuple[str, str]] = set()
    for dimension in BEHAVIOR_DIMENSIONS:
        a_values = [a_rows[key]["scores"][dimension] for key in expected]
        b_values = [b_rows[key]["scores"][dimension] for key in expected]
        per_dimension[dimension] = _agreement(a_values, b_values)
        disagreements.update(
            key for key in expected
            if a_rows[key]["scores"][dimension]
            != b_rows[key]["scores"][dimension])

    unresolved = set(disagreements)
    resolved_by_adjudicator = {}
    adjudicator_id = None
    if adjudication is not None and not disagreements:
        raise ValueError("adjudication supplied when no ratings are disputed")
    if adjudication is not None and disagreements:
        adjudicator_id, resolved_by_adjudicator = _validated_adjudication(
            disagreements, adjudication, str(packet.get("protocol_id") or ""),
            packet_digest(packet))
        if adjudicator_id in {a_id, b_id}:
            raise ValueError("adjudicator must be independent of both raters")
        unresolved.clear()

    consensus_rows = []
    for key in expected:
        a, b = a_rows[key], b_rows[key]
        is_disputed = key in disagreements
        if is_disputed and key in unresolved:
            consensus_rows.append({
                "case_code": key[0], "response_code": key[1],
                "scores": None, "status": "awaiting_adjudication",
            })
            continue
        if is_disputed:
            resolved = resolved_by_adjudicator[key]
            scores = resolved["final_scores"]
            consensus_rows.append({
                "case_code": key[0], "response_code": key[1],
                "scores": scores, "status": "adjudicated",
                "rater_scores": {a_id: a["scores"], b_id: b["scores"]},
                "adjudicator_id": adjudicator_id,
                "evidence_notes": resolved["final_evidence_notes"],
                "resolution_note": resolved["resolution_note"],
            })
        else:
            consensus_rows.append({
                "case_code": key[0], "response_code": key[1],
                "scores": a["scores"], "status": "unanimous",
                "rater_notes": {a_id: a["evidence_notes"],
                                b_id: b["evidence_notes"]},
            })
    status = ("awaiting_adjudication" if unresolved else
              "consensus_complete")
    return {
        "schema": REPORT_SCHEMA,
        "protocol_id": packet.get("protocol_id"),
        "packet_sha256": packet_digest(packet),
        "status": status,
        "rater_ids": [a_id, b_id],
        "adjudicator_id": adjudicator_id,
        "annotation_row_count": len(expected),
        "disputed_row_count": len(disagreements),
        "unresolved_row_count": len(unresolved),
        "agreement": {
            "by_dimension": per_dimension,
            "all_dimensions_exact_agreement": _agreement(
                [a_rows[key]["scores"][dimension]
                 for key in expected for dimension in BEHAVIOR_DIMENSIONS],
                [b_rows[key]["scores"][dimension]
                 for key in expected for dimension in BEHAVIOR_DIMENSIONS]),
        },
        "consensus_rows": consensus_rows,
        "score_interpretation_performed": False,
        "system_aliases_unblinded": False,
        "response_text_used_as_score_evidence": False,
        "limitations": [
            "Consensus labels are not capability scorecards.",
            "System identities remain blinded; do not join the private key until annotations are frozen.",
            "This packet covers interpretation, grounding, action, repair, and calibration only.",
        ],
    }


def make_adjudication_template(
    packet: Mapping[str, Any], report: Mapping[str, Any], adjudicator_id: str,
) -> dict[str, Any]:
    """Create an alias-only resolution form for exactly the disputed rows."""
    digest = packet_digest(packet)
    if report.get("packet_sha256") != digest:
        raise ValueError("report does not belong to this packet")
    if not str(adjudicator_id).strip():
        raise ValueError("adjudicator_id must be a non-empty blind identifier")
    rows = [
        {"case_code": row["case_code"],
         "response_code": row["response_code"],
         "final_scores": {dimension: None for dimension in BEHAVIOR_DIMENSIONS},
         "final_evidence_notes": {dimension: ""
                                   for dimension in BEHAVIOR_DIMENSIONS},
         "resolution_note": ""}
        for row in report.get("consensus_rows", ())
        if row.get("status") == "awaiting_adjudication"
    ]
    if not rows:
        raise ValueError("report has no unresolved disputed rows")
    return {
        "schema": ADJUDICATION_SCHEMA,
        "protocol_id": packet.get("protocol_id"),
        "packet_sha256": digest,
        "adjudicator_id": str(adjudicator_id),
        "rows": rows,
    }


__all__ = ["ADJUDICATION_SCHEMA", "RATER_SCHEMA", "REPORT_SCHEMA",
           "audit_blinded_annotations", "make_adjudication_template",
           "make_rater_template", "packet_digest"]


if __name__ == "__main__":  # pragma: no cover - exercised by API tests
    import argparse
    from pathlib import Path

    def read_json(path: Path) -> dict[str, Any]:
        value = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise ValueError(f"expected JSON object: {path}")
        return value

    def write_json(path: Path, value: Mapping[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8")

    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    template = commands.add_parser("template", help="create a blank rater form")
    template.add_argument("--packet", type=Path, required=True)
    template.add_argument("--rater-id", required=True)
    template.add_argument("--output", type=Path, required=True)
    audit = commands.add_parser("audit", help="audit two ratings and optional adjudication")
    audit.add_argument("--packet", type=Path, required=True)
    audit.add_argument("--rater-a", type=Path, required=True)
    audit.add_argument("--rater-b", type=Path, required=True)
    audit.add_argument("--adjudication", type=Path)
    audit.add_argument("--adjudicator-template-id")
    audit.add_argument("--adjudicator-template-out", type=Path)
    audit.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    packet = read_json(args.packet)
    if args.command == "template":
        result = make_rater_template(packet, args.rater_id)
        write_json(args.output, result)
        print(json.dumps({"output": str(args.output), "status": "unscored"}))
    else:
        adjudication = (read_json(args.adjudication)
                        if args.adjudication else None)
        report = audit_blinded_annotations(
            packet, read_json(args.rater_a), read_json(args.rater_b),
            adjudication=adjudication)
        write_json(args.output, report)
        if args.adjudicator_template_out:
            if not args.adjudicator_template_id:
                parser.error("--adjudicator-template-out requires --adjudicator-template-id")
            write_json(args.adjudicator_template_out,
                       make_adjudication_template(
                           packet, report, args.adjudicator_template_id))
        print(json.dumps({"output": str(args.output),
                          "status": report["status"],
                          "disputed_rows": report["disputed_row_count"],
                          "unresolved_rows": report["unresolved_row_count"],
                          "score_interpretation_performed": False}))

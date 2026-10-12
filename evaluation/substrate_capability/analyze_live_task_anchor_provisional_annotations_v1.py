#!/usr/bin/env python3
"""Score simple task-anchor policies against provisional annotations only."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACKET = ROOT / "evaluation/reports/live_conversation_task_anchor_review_packet_v1_20261004.json"
ANNOTATIONS = ROOT / "evaluation/reports/live_conversation_task_anchor_provisional_annotations_v1_20261004.json"
OUT = ROOT / "evaluation/reports/live_conversation_task_anchor_provisional_scores_v1_20261004.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def score(pairs):
    tp = sum(pred and truth for pred, truth in pairs)
    fp = sum(pred and not truth for pred, truth in pairs)
    fn = sum(not pred and truth for pred, truth in pairs)
    tn = sum(not pred and not truth for pred, truth in pairs)
    return {"tp": tp, "fp": fp, "fn": fn, "tn": tn,
            "precision": tp / (tp + fp) if tp + fp else None,
            "recall": tp / (tp + fn) if tp + fn else None,
            "n": len(pairs)}


def main():
    packet = json.loads(PACKET.read_text(encoding="utf-8"))
    annotations = json.loads(ANNOTATIONS.read_text(encoding="utf-8"))
    packet_sha = sha(PACKET)
    if annotations.get("packet_sha256") != packet_sha:
        raise SystemExit("annotation packet digest mismatch")
    packets = {case["case_id"]: case for case in packet["cases"]}
    annotation_cases = {case["case_id"]: case for case in annotations["cases"]}
    if packets.keys() != annotation_cases.keys():
        raise SystemExit("case set mismatch")
    scope_pairs = {"direct_comprehends": [], "bounded_typed_path": []}
    alignment_pairs = {"direct_comprehends": [], "bounded_typed_path": []}
    per_case = []
    for case_id, case in packets.items():
        labels = {row["node"]: row for row in annotation_cases[case_id]["labels"]}
        goal_rows = [node for node in case["candidates"] if node["type"] == "Goal"]
        for node in goal_rows:
            ann = labels[node["label"]]
            direct = bool(node["prompt_path"] and len(node["prompt_path"]["steps"]) == 1
                          and node["prompt_path"]["steps"][0]["edge"] == "comprehends")
            broad = node["prompt_path"] is not None
            if ann["scope"] != "uncertain":
                truth = ann["scope"] == "request_specific"
                scope_pairs["direct_comprehends"].append((direct, truth))
                scope_pairs["bounded_typed_path"].append((broad, truth))
            if ann["task_alignment"] in ("aligned", "misaligned_interpretation"):
                truth = ann["task_alignment"] == "aligned"
                alignment_pairs["direct_comprehends"].append((direct, truth))
                alignment_pairs["bounded_typed_path"].append((broad, truth))
        per_case.append({"case_id": case_id, "goal_nodes": len(goal_rows),
                         "scope_evaluable": sum(labels[n["label"]]["scope"] != "uncertain" for n in goal_rows),
                         "alignment_evaluable": sum(labels[n["label"]]["task_alignment"] in ("aligned", "misaligned_interpretation") for n in goal_rows)})
    result = {
        "schema": "LiveTaskAnchorProvisionalScoresV1",
        "status": "exploratory score against a single agent's provisional annotations; not validated accuracy",
        "packet_sha256": packet_sha,
        "annotation_sha256": sha(ANNOTATIONS),
        "evaluated_units": "Goal nodes only; uncertain labels excluded from each metric.",
        "scope_mapping": {name: score(pairs) for name, pairs in scope_pairs.items()},
        "task_alignment": {name: score(pairs) for name, pairs in alignment_pairs.items()},
        "per_case": per_case,
        "limits": ["One annotator, five authored prompts, one graph per prompt.",
                   "Annotations and policy design are not independent.",
                   "The other worker replicate is not yet scored.",
                   "Metrics do not estimate population capability or natural-task prevalence."],
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(OUT.relative_to(ROOT)),
                      "scope_mapping": result["scope_mapping"],
                      "task_alignment": result["task_alignment"]}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

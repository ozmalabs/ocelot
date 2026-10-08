#!/usr/bin/env python3
"""Summarize prompt-root cut metrics and the two degree control arms."""
from __future__ import annotations

import hashlib
import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CAPTURE = ROOT / "evaluation/reports/live_graph_prompt_neighborhood_cuts_v2_20261004.json"
LOCK = ROOT / "evaluation/substrate_capability/live_graph_prompt_neighborhood_cuts_analysis_v2_lock_20261004.json"
OUT = ROOT / "evaluation/reports/live_graph_prompt_neighborhood_cuts_v2_analysis_20261004.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    lock = json.loads(LOCK.read_text())
    capture = json.loads(CAPTURE.read_text())
    actual = {"capture_sha256": sha(CAPTURE), "analyzer_sha256": sha(Path(__file__).resolve())}
    if actual != lock["locked_inputs"]:
        raise SystemExit("analysis lock mismatch")
    if OUT.exists():
        raise SystemExit(f"refusing to overwrite {OUT}")
    graph_cells = []
    settings = set()
    for graph in capture["rows"]:
        for cell in graph["cells"]:
            prompt, controls = cell["prompt"], cell["controls"]
            setting = (prompt["hub_cutoff"], prompt["radius"])
            settings.add(setting)
            expected_controls = min(capture["method"]["matched_controls_per_graph"], graph["nonmessage_candidates"])
            if len(controls) != expected_controls:
                raise SystemExit(f"wrong control count for {graph['graph_digest']} {setting}")
            message_controls = cell["message_controls"]
            expected_messages = min(capture["method"]["matched_controls_per_graph"], graph["message_candidates"])
            if len(message_controls) != expected_messages:
                raise SystemExit(f"wrong Message census count for {graph['graph_digest']} {setting}")
            control_median = statistics.median(row["cut_edges_per_frame_node"] for row in controls)
            message_median = statistics.median(row["cut_edges_per_frame_node"] for row in message_controls)
            graph_cells.append({
                "graph_digest": graph["graph_digest"], "condition": graph["condition"],
                "hub_cutoff": prompt["hub_cutoff"], "radius": prompt["radius"],
                "prompt_frame_nodes": prompt["frame_nodes"],
                "prompt_frame_fraction": prompt["frame_fraction"],
                "prompt_frontier_nodes": prompt["frontier_nodes"],
                "prompt_cut_edges": prompt["cut_edges"],
                "prompt_outside_boundary_nodes": prompt["outside_boundary_nodes"],
                "prompt_cut_per_frame_node": prompt["cut_edges_per_frame_node"],
                "matched_control_median_cut_per_frame_node": control_median,
                "prompt_lower_than_control_median": prompt["cut_edges_per_frame_node"] < control_median,
                "stored_prompt_control_percentile": prompt["prompt_percentile_vs_nonmessage_controls"],
                "nonmessage_degree_gap_min": prompt["nonmessage_control_degree_gap_min"],
                "nonmessage_degree_gap_median": prompt["nonmessage_control_degree_gap_median"],
                "nonmessage_degree_gap_max": prompt["nonmessage_control_degree_gap_max"],
                "nonmessage_exact_degree_count": prompt["nonmessage_control_exact_degree_count"],
                "message_control_median_cut_per_frame_node": message_median,
                "prompt_lower_than_message_census_median": prompt["cut_edges_per_frame_node"] < message_median,
                "message_degree_gap_max": prompt["message_control_degree_gap_max"],
            })
    if len(capture["rows"]) != 5 or len(settings) != 12 or len(graph_cells) != 60:
        raise SystemExit("unexpected graph or cell count")
    aggregates = []
    for cutoff, radius in sorted(settings, key=lambda item: (item[0] is None, item[0] or 0, item[1])):
        rows = [row for row in graph_cells if row["hub_cutoff"] == cutoff and row["radius"] == radius]
        prompt = [row["prompt_cut_per_frame_node"] for row in rows]
        control = [row["matched_control_median_cut_per_frame_node"] for row in rows]
        message_control = [row["message_control_median_cut_per_frame_node"] for row in rows]
        aggregates.append({
            "hub_cutoff": cutoff, "radius": radius, "unique_graphs": len(rows),
            "prompt_median_cut_per_frame_node": statistics.median(prompt),
            "matched_control_median_cut_per_frame_node": statistics.median(control),
            "graphs_prompt_lower_than_control_median": sum(row["prompt_lower_than_control_median"] for row in rows),
            "message_census_median_cut_per_frame_node": statistics.median(message_control),
            "graphs_prompt_lower_than_message_census_median": sum(row["prompt_lower_than_message_census_median"] for row in rows),
            "median_stored_prompt_percentile": statistics.median(row["stored_prompt_control_percentile"] for row in rows),
            "prompt_frame_nodes_median": statistics.median(row["prompt_frame_nodes"] for row in rows),
            "prompt_cut_edges_median": statistics.median(row["prompt_cut_edges"] for row in rows),
        })
    lower_cells = sum(row["graphs_prompt_lower_than_control_median"] for row in aggregates)
    lower_message_cells = sum(row["graphs_prompt_lower_than_message_census_median"] for row in aggregates)
    summary = {
        "schema": "LiveGraphPromptNeighborhoodCutsV2Analysis",
        "capture_sha256": sha(CAPTURE), "analysis_lock_sha256": sha(LOCK),
        "graph_count": len(capture["rows"]), "independent_graph_count": 5,
        "worker_records_collapsed": capture["record_count"], "cell_count": len(graph_cells),
        "prompt_lower_than_degree_ranked_nonmessage_control_cells": lower_cells,
        "prompt_lower_than_message_census_cells": lower_message_cells,
        "total_graph_cells": len(graph_cells),
        "strict_direction_consistent_all_cells": lower_cells == len(graph_cells),
        "interpretation": "The Message census is small and often poorly degree-matched; the larger non-Message arm is degree-ranked but type-confounded. Neither arm establishes automatic frame discovery or cheap-cut prevalence.",
        "aggregates": aggregates,
        "graph_cell_rows": graph_cells,
        "limits": capture["limits"],
    }
    OUT.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"analysis": str(OUT.relative_to(ROOT)), "lower_cells": lower_cells,
        "lower_message_cells": lower_message_cells,
        "total_cells": len(graph_cells), "strict_direction_consistent_all_cells": lower_cells == len(graph_cells),
        "sha256": sha(OUT)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

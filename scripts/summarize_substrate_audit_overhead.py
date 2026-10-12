#!/usr/bin/env python3
"""Validate and summarize paired scale-audit overhead pilot manifests."""
from __future__ import annotations

import argparse
import hashlib
import json
import statistics
from pathlib import Path


def summarize(paths: list[Path]) -> dict:
    rows = []
    input_hashes = []
    for path in paths:
        raw = path.read_bytes()
        manifest = json.loads(raw)
        input_hashes.append({"path": str(path), "sha256": hashlib.sha256(raw).hexdigest()})
        groups = {}
        for record in manifest["records"]:
            detail = record["pilot_detail"]
            key = (detail.get("rule_family", "transitive_closure"), detail["topology"],
                   record["input_structure"]["nodes"],
                   detail["replicate"])
            groups.setdefault(key, {})[detail["audit_mode"]] = record
        by_case = {}
        for (rule_family, topology, nodes, replicate), modes in groups.items():
            if set(modes) != {"on", "off"}:
                raise ValueError(f"unpaired case in {path}: {(rule_family, topology, nodes, replicate)}")
            on, off = modes["on"], modes["off"]
            for field in ("status", "quality", "exact", "reason", "ground_truth_ref"):
                if on["outcome"][field] != off["outcome"][field]:
                    raise ValueError(f"audit condition changed {field}: {(rule_family, topology, nodes, replicate)}")
            for field in ("edges_after", "progress_steps", "expected_total_edges"):
                if on["pilot_detail"][field] != off["pilot_detail"][field]:
                    raise ValueError(f"audit condition changed {field}: {(rule_family, topology, nodes, replicate)}")
            if not on["outcome"]["exact"] or on["outcome"]["status"] != "success":
                raise ValueError(f"semantic failure in paired case: {(rule_family, topology, nodes, replicate)}")
            if not all(on["pilot_detail"]["counter_invariants"].values()):
                raise ValueError(f"audit-on counter invariant failed: {(rule_family, topology, nodes, replicate)}")
            by_case.setdefault((rule_family, topology, nodes), []).append((
                on["cost"]["wall_time_ns"], off["cost"]["wall_time_ns"],
                on["cost"]["cpu_time_ns"], off["cost"]["cpu_time_ns"],
                on["pilot_detail"]["primary_peak_rss_delta_over_import_bytes"],
                off["pilot_detail"]["primary_peak_rss_delta_over_import_bytes"],
            ))
        for (rule_family, topology, nodes), pairs in sorted(by_case.items()):
            wall_on = [x[0] for x in pairs]
            wall_off = [x[1] for x in pairs]
            cpu_on = [x[2] for x in pairs]
            cpu_off = [x[3] for x in pairs]
            rows.append({
                "source_manifest": str(path),
                "rule_family": rule_family,
                "topology": topology,
                "nodes": nodes,
                "paired_repeats": len(pairs),
                "semantic_pairs_equal": True,
                "wall_on_median_ns": statistics.median(wall_on),
                "wall_on_range_ns": [min(wall_on), max(wall_on)],
                "wall_off_median_ns": statistics.median(wall_off),
                "wall_off_range_ns": [min(wall_off), max(wall_off)],
                "wall_paired_ratio_median": statistics.median(a / b for a, b, *_ in pairs),
                "cpu_on_median_ns": statistics.median(cpu_on),
                "cpu_off_median_ns": statistics.median(cpu_off),
                "cpu_paired_ratio_median": statistics.median(x[2] / x[3] for x in pairs),
                "primary_peak_delta_on_median_bytes": statistics.median(x[4] for x in pairs),
                "primary_peak_delta_off_median_bytes": statistics.median(x[5] for x in pairs),
            })
    analysis_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    return {"status": "exploratory_pilot", "claim_boundary": "descriptive only; no inferential overhead claim",
            "analysis_script_sha256": analysis_hash, "input_manifests": input_hashes,
            "rows": rows}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifests", type=Path, nargs="+")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = summarize(args.manifests)
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered)
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

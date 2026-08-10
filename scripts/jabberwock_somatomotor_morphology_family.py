#!/usr/bin/env python3
"""Run counterbalanced cross-morphology transfer and negative controls."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
for _path in (ROOT, ROOT / "runners" / "dsl" / "python"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from scripts.jabberwock_somatomotor_cross_morphology import (  # noqa: E402
    run_transfer,
)


DEFAULT_PROTOCOL = (
    ROOT / "protocols" / "somatomotor_cross_morphology_family_v1.json"
)


def run_family(
    protocol_path: Path = DEFAULT_PROTOCOL,
    *,
    source_library_path: Path,
) -> dict[str, Any]:
    protocol_path = protocol_path.resolve()
    family = json.loads(protocol_path.read_text(encoding="utf-8"))
    base_protocol = (ROOT / family["base_protocol"]).resolve()
    targets = []
    for row in family["targets"]:
        result = run_transfer(
            base_protocol,
            source_library_path=source_library_path,
            protocol_overrides={
                "protocol": f"{family['protocol']}:{row['name']}",
                "asset": row["asset"],
                "curriculum": {
                    "caregiver_scaffolding": bool(
                        family.get("caregiver_scaffolding", False)
                    )
                },
            },
            arm_order=tuple(row["arm_order"]),
        )
        targets.append({
            "name": row["name"],
            "asset": row["asset"],
            "arm_execution_order": row["arm_order"],
            "shape_overlap": result["target"]["shape_overlap"],
            "cold": result["cold"],
            "warm": result["warm"],
            "transfer": result["transfer"],
            "trajectory_comparison": result["trajectory_comparison"],
            "source_library_sha256": result["source_library"]["sha256"],
        })
    hashes = {row["source_library_sha256"] for row in targets}
    if len(hashes) != 1:
        raise RuntimeError("source library changed across morphology family")
    return {
        "experiment": family["protocol"],
        "protocol_path": str(protocol_path.relative_to(ROOT)),
        "base_protocol": family["base_protocol"],
        "source_library": str(source_library_path.resolve()),
        "source_library_sha256": next(iter(hashes)),
        "design": {
            "same_engine_revision": True,
            "same_protocol_parameters_except_declared_asset": True,
            "independent_world_per_arm": True,
            "counterbalanced_arm_order": True,
            "no_target_specific_thresholds_or_tuning": True,
            "reported_as_per_morphology_tradeoffs": True,
        },
        "targets": targets,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", type=Path, default=DEFAULT_PROTOCOL)
    parser.add_argument("--source-library", type=Path, required=True)
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)
    result = run_family(
        args.protocol,
        source_library_path=args.source_library,
    )
    rendered = json.dumps(result, indent=2)
    if args.json_out is not None:
        args.json_out.write_text(rendered + "\n", encoding="utf-8")
    if not args.quiet:
        print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

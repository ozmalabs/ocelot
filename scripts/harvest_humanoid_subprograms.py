"""Mechanically combine shape-indexed humanoid motor subprogram libraries.

This tool does not score, select, map, or authorize motor programs. It copies
exact program structure beneath the existing order-N body-shape identity. The
graph's normal shape decode, member rebinding, viability gate, and receipt
verification decide whether an imported program ever gains output authority.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

from domains.embodied_motor_shapes import motor_program_shape_signature
from domains.embodied_motor_hint_priors import seeded_motor_plan_hints


ROOT = Path(__file__).resolve().parents[1]
SUPPORTED_VERSIONS = {3, 4, 5}
OUTPUT_VERSION = 5


def harvest_libraries(
    base: dict[str, Any],
    sources: Iterable[tuple[str, dict[str, Any]]],
) -> tuple[dict[str, Any], dict[str, Any]]:
    if base.get("version") not in SUPPORTED_VERSIONS:
        raise ValueError(f"unsupported base library version: {base.get('version')!r}")
    result = copy.deepcopy(base)
    result["version"] = OUTPUT_VERSION
    result["harvest_aggregate"] = True
    result.setdefault("plan_hints", [])
    shapes = {
        str(row["attrs"]["name"]): row
        for row in result.get("body_shapes", [])
    }
    next_ordinal = {
        name: 1.0 + max(
            (
                float(row.get("attrs", {}).get("ordinal", -1.0))
                for row in shape.get("programs", [])
            ),
            default=-1.0,
        )
        for name, shape in shapes.items()
    }
    imported = 0
    imported_plan_hints = 0
    source_rows = []
    for source_name, payload in sources:
        if payload.get("version") not in SUPPORTED_VERSIONS:
            continue
        source_imported = 0
        source_plan_hints = 0
        for source_shape in payload.get("body_shapes", []):
            name = str(source_shape["attrs"]["name"])
            if name not in shapes:
                new_shape = copy.deepcopy(source_shape)
                new_shape["programs"] = []
                new_shape.setdefault("motor_transitions", [])
                new_shape.setdefault("coordination_challenges", [])
                new_shape.setdefault("residual_regimes", [])
                result.setdefault("body_shapes", []).append(new_shape)
                shapes[name] = new_shape
                next_ordinal[name] = 0.0
            target_shape = shapes[name]
            for source_program in source_shape.get("programs", []):
                program = copy.deepcopy(source_program)
                attrs = program.setdefault("attrs", {})
                attrs["source_program_ordinal"] = float(
                    attrs.get("ordinal", -1.0)
                )
                attrs["ordinal"] = next_ordinal[name]
                attrs["library_slot"] = 1.0 + len(
                    target_shape.setdefault("programs", [])
                )
                attrs["harvested_subprogram"] = 1.0
                attrs["harvest_provenance"] = source_name
                target_shape["programs"].append(program)
                next_ordinal[name] += 1.0
                imported += 1
                source_imported += 1
            transitions = source_shape.get("motor_transitions", [])
            if transitions:
                transition_facts = tuple(
                    (
                        float(row.get("attrs", {}).get("ordinal", index)),
                        float(row.get("attrs", {}).get("from_program_ordinal", -1.0)),
                        float(row.get("attrs", {}).get("next_program_ordinal", -1.0)),
                        str(row.get("attrs", {}).get("from_task_phase", "")),
                        str(row.get("attrs", {}).get("next_task_phase", "")),
                    )
                    for index, row in enumerate(transitions)
                )
                digest = hashlib.sha256(json.dumps(
                    (source_name, name, transition_facts),
                    separators=(",", ":"),
                ).encode("utf-8")).hexdigest()
                contexts = sorted({
                    str(row.get("attrs", {}).get(
                        "motor_task_context", "locomotion"
                    ))
                    for row in transitions
                })
                referenced_ordinals = {
                    value
                    for row in transitions
                    for value in (
                        float(row.get("attrs", {}).get(
                            "from_program_ordinal", -1.0
                        )),
                        float(row.get("attrs", {}).get(
                            "next_program_ordinal", -1.0
                        )),
                    )
                }
                stages = []
                for stage_ordinal, program_row in enumerate(
                    row for row in source_shape.get("programs", [])
                    if float(row.get("attrs", {}).get("ordinal", -2.0))
                    in referenced_ordinals
                ):
                    attrs = program_row.get("attrs", {})
                    stages.append({"attrs": {
                        "name": f"harvested-plan:{digest}:stage:{stage_ordinal}",
                        "ordinal": float(stage_ordinal),
                        "source_program_ordinal": float(
                            attrs.get("ordinal", -1.0)
                        ),
                        "signature": motor_program_shape_signature(
                            attrs, program_row.get("members", [])
                        ),
                        "routing_signature": (
                            (
                                "motor_task_context",
                                str(attrs.get(
                                    "motor_task_context", "locomotion"
                                )),
                            ),
                            (
                                "motor_task_phase",
                                str(attrs.get(
                                    "motor_task_phase", "preparation"
                                )),
                            ),
                        ),
                        "motor_task_context": str(attrs.get(
                            "motor_task_context", "locomotion"
                        )),
                        "motor_task_phase": str(attrs.get(
                            "motor_task_phase", "preparation"
                        )),
                        "output_authority": 0.0,
                    }})
                for context in contexts:
                    result["plan_hints"].append({
                        "attrs": {
                            "name": f"harvested-plan:{digest}:{context}",
                            "signature": (("motor_task", context),),
                            "motor_task_context": context,
                            "body_shape_name": name,
                            "output_authority": 0.0,
                            "knowledge_kind": "search_basin_hint",
                            "provenance": source_name,
                            "transition_count": float(len(transitions)),
                            "stage_count": float(len(stages)),
                        },
                        "stages": copy.deepcopy(stages),
                    })
                    imported_plan_hints += 1
                    source_plan_hints += 1
        source_rows.append({
            "source": source_name,
            "imported": source_imported,
            "imported_plan_hints": source_plan_hints,
        })
    prior_hints = seeded_motor_plan_hints()
    result["plan_hints"].extend(prior_hints)
    result["body_shapes"].sort(key=lambda row: str(row["attrs"]["name"]))
    return result, {
        "source_count": len(source_rows),
        "imported_program_count": imported,
        "imported_plan_hint_count": imported_plan_hints,
        "seeded_plan_hint_count": len(prior_hints),
        "host_deduplication": False,
        "identity_owner": "graph_shape_decode",
        "sources": source_rows,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--source", type=Path, action="append", default=[])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args(argv)
    source_paths = args.source or sorted(
        (ROOT / "results").glob("*library*.json")
    )
    base_path = args.base.resolve()
    output_path = args.output.resolve()
    sources = []
    for path in source_paths:
        resolved = path.resolve()
        if resolved in {base_path, output_path} or not resolved.is_file():
            continue
        try:
            payload = json.loads(resolved.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if payload.get("harvest_aggregate") is True:
            continue
        sources.append((str(resolved.relative_to(ROOT)), payload))
    base = json.loads(base_path.read_text(encoding="utf-8"))
    harvested, report = harvest_libraries(base, sources)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(harvested, indent=2) + "\n", encoding="utf-8"
    )
    if args.report is not None:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(
            json.dumps(report, indent=2) + "\n", encoding="utf-8"
        )
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

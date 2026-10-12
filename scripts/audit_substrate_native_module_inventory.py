#!/usr/bin/env python3
"""Audit public native Rust modules against the source-linked capability map."""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB = ROOT / "runners/dsl/src/lib.rs"
MAP = ROOT / "evaluation/substrate_capability/capability_map.json"
OUT = ROOT / "evaluation/substrate_capability/native_module_inventory_audit_20260928.json"
DECL = re.compile(r"^\s*pub\s+mod\s+(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s*;\s*(?://.*)?$")
FAMILY_BY_MODULE = {
    **dict.fromkeys(("cognitive_cycle", "cognitive_tasks", "effort_dial", "g5",
        "l1_hot_paths", "l2_adaptive", "l2_dispatch", "l2_dispatch_work_stealing",
        "l2_graph_bridge", "reflex_runtime", "code_cache"),
        "native_cognitive_runtime_and_scheduling"),
    **dict.fromkeys(("l3_drives", "l3_gain_scheduling", "l3_kalman_nd", "l3_lqr",
        "l3_mpc", "l4_subsystem_boundaries", "l6_ashby_variety",
        "l6_cybernetic_feedback", "l6_essential_variables", "future_manifold"),
        "feedback_control_and_viability"),
    "motor_compose": "motor_program_synthesis",
    "sigma_lognormal": "motor_program_synthesis",
    "strokes": "motor_program_synthesis",
    "p3_learning": "learning_proposal_data_plane",
    "argmin_tie": "bounded_decision_and_admissibility",
    "enigma": "bounded_decision_and_admissibility",
    **dict.fromkeys(("sym", "checker", "ext", "grammar", "grammar_reflect",
        "graph_rules", "jit", "jsonio", "reflect", "shape", "codec"),
        "rule_term_and_serialization_support"),
    **dict.fromkeys(("apc", "audio_primitives", "auditory_cortex",
        "cochlear_nucleus", "inferior_colliculus"), "auditory_signal_processing"),
    **dict.fromkeys(("deform_metric", "framebuffer", "gpu_me", "ink_topology",
        "space_quantize"), "vision_and_spatial_perception"),
    **dict.fromkeys(("cabac", "h264_cabac_mb", "h264_dct", "h264_deblock",
        "h264_inter_pred", "h264_mb_iterator", "h264_slice_header", "h265_cabac",
        "h265_ctu_quadtree", "h265_dct", "h265_in_loop_filter", "h265_intra_mode",
        "h265_slice_header", "h265_transcode_driver"), "video_codec_and_transcoding"),
    "net_forward": "graph_resident_neural_and_pipeline_execution",
    "pipeline_runtime": "graph_resident_neural_and_pipeline_execution",
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def module_doc(path: Path) -> str:
    for line in path.read_text(errors="replace").splitlines()[:16]:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith(("//", "/*", "*", "#![")):
            return stripped.lstrip("/!*#[] ")[:200]
        break
    return ""


def audit() -> dict:
    lib_bytes = LIB.read_bytes()
    map_bytes = MAP.read_bytes()
    inventory = json.loads(map_bytes)
    links: dict[str, list[str]] = {}
    for capability in inventory.get("capabilities", []):
        for source in capability.get("source_links", []):
            path = source.get("path")
            if path:
                links.setdefault(path, []).append(capability["id"])

    rows = []
    lines = lib_bytes.decode("utf-8", "replace").splitlines()
    for index, line in enumerate(lines):
        match = DECL.match(line)
        if not match:
            continue
        name = match.group("name")
        relative = f"runners/dsl/src/{name}.rs"
        source = ROOT / relative
        annotations = []
        cursor = index - 1
        while cursor >= 0 and lines[cursor].strip().startswith("#["):
            annotations.insert(0, lines[cursor].strip())
            cursor -= 1
        rows.append({"module": name, "path": relative,
            "source_exists": source.is_file(),
            "mapped_capability_ids": sorted(set(links.get(relative, []))),
            "map_coverage": "mapped" if relative in links else "unmapped",
            "candidate_family": FAMILY_BY_MODULE.get(name),
            "declaration_attributes": annotations,
            "source_header": module_doc(source) if source.is_file() else ""})

    counts = {status: sum(row["map_coverage"] == status for row in rows)
              for status in ("mapped", "unmapped")}
    observed_modules = {row["module"] for row in rows}
    unclassified = sorted(observed_modules - set(FAMILY_BY_MODULE) -
                          {row["module"] for row in rows if row["map_coverage"] == "mapped"})
    families: dict[str, int] = {}
    for row in rows:
        family = row["candidate_family"]
        if family:
            families[family] = families.get(family, 0) + 1
    return {"schema_version": 1,
        "audit_id": "substrate-native-module-inventory-audit-20260928",
        "auditor_sha256": sha(Path(__file__).read_bytes()),
        "inputs": {"lib_rs_sha256": sha(lib_bytes),
                   "capability_map_json_sha256": sha(map_bytes)},
        "coverage_scope": "Top-level `pub mod NAME;` declarations in runners/dsl/src/lib.rs only.",
        "counts": {"public_modules": len(rows), **counts,
                   "coverage_fraction": counts["mapped"] / len(rows) if rows else None,
                   "missing_source_files": sum(not row["source_exists"] for row in rows),
                   "unclassified_modules": len(unclassified)},
        "candidate_families": families,
        "unclassified_modules": unclassified,
        "modules": rows,
        "interpretation": "Unmapped means absent from the inventory source_links; it is not evidence of missing implementation or missing tests. This audit does not cover inline modules, private modules, Python domains, or non-Rust entrypoints."}


def main() -> None:
    result = audit()
    if result["unclassified_modules"]:
        raise SystemExit("public module(s) lack a reviewed candidate-family classification: "
                         + ", ".join(result["unclassified_modules"]))
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if sys.argv[1:] == ["--check"]:
        if not OUT.is_file() or OUT.read_text() != rendered:
            raise SystemExit("native module inventory audit is stale; regenerate it")
    else:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(rendered)
    print(json.dumps({"output": str(OUT.relative_to(ROOT)),
        "counts": result["counts"], "unmapped_modules": [row["module"]
            for row in result["modules"] if row["map_coverage"] == "unmapped"]}, indent=2))


if __name__ == "__main__":
    main()

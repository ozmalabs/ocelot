#!/usr/bin/env python3
"""Map activation paths for seeds that author scoped ShapeDecode calls.

This is a source inventory. It distinguishes fixed-core boot, full-corpus
loading, explicit module references, and historical runtime evidence; none of
those alone establishes ordinary task prevalence.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "evaluation/reports/shape_decode_activation_audit_v1_20261005.json"
VERDICT_CAPTURE = ROOT / "evaluation/reports/shapedecode_verdict_comparator_cache_v1_20261005.json"
VERDICT_ANALYSIS = ROOT / "evaluation/reports/shapedecode_verdict_comparator_cache_v1_analysis_20261005.json"
CORE = ROOT / "substrate/boot_core.py"
ALL = ROOT / "substrate/boot_all.py"
FACULTY = ROOT / "domains/reflective_faculty.py"
SEED_DIR = ROOT / "seeds"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def walk(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)


def seed_closure(seed_ids: set[str], manifests: dict[str, dict]) -> set[str]:
    found: set[str] = set()

    def visit(seed_id: str) -> None:
        if seed_id in found or seed_id not in manifests:
            return
        found.add(seed_id)
        for dep in manifests[seed_id].get("depends_on", []):
            visit(str(dep))

    for seed_id in seed_ids:
        visit(seed_id)
    return found


def main() -> int:
    manifests: dict[str, dict] = {}
    manifest_paths = sorted(SEED_DIR.glob("*.json")) + sorted(
        (SEED_DIR / "generated").glob("*.json")
    )
    for path in manifest_paths:
        try:
            item = json.loads(path.read_text())
        except Exception:
            continue
        if isinstance(item, dict):
            manifests[str(item.get("id") or path.stem)] = item

    core_text = CORE.read_text()
    # Parse the literal CORE_SEEDS tuple without importing runtime modules.
    import ast
    tree = ast.parse(core_text)
    core_ids: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "CORE_SEEDS"
            for target in node.targets
        ):
            core_ids = set(ast.literal_eval(node.value))
            break
    core_closure = seed_closure(core_ids, manifests)
    full_corpus = {sid for sid, item in manifests.items() if not item.get("self_load_only")}

    verdict_capture = json.loads(VERDICT_CAPTURE.read_text())
    verdict_analysis = json.loads(VERDICT_ANALYSIS.read_text())
    if verdict_capture.get("run_id") != "shapedecode-verdict-comparator-cache-v1-20261005":
        raise SystemExit("unexpected verdict-comparator capture")
    if verdict_analysis.get("capture_sha256") != digest(VERDICT_CAPTURE):
        raise SystemExit("verdict-comparator analysis does not match capture")
    verdict_world_path = ROOT / "domains/verdict_comparator_world.py"
    verdict_seed_path = SEED_DIR / "vision_verdict_comparator.json"
    if verdict_capture["manifest"].get("world_sha256") != digest(verdict_world_path):
        raise SystemExit("verdict-comparator world source differs from captured source")
    if verdict_capture["manifest"].get("seed_sha256") != digest(verdict_seed_path):
        raise SystemExit("verdict-comparator seed differs from captured source")
    verdict_work: dict[str, dict[str, int]] = {}
    verdict_trace_workers: dict[str, int] = {}
    verdict_pids: set[int] = set()
    for row in verdict_capture["rows"]:
        case = row["case"]
        mode = str(case["mode"])
        verdict_pids.add(int(row["pid"]))
        if not case["trace"]:
            continue
        verdict_trace_workers[mode] = verdict_trace_workers.get(mode, 0) + 1
        counts = verdict_work.setdefault(mode, {})
        for event in row["trace"]["rows"]:
            kind = str(event[3])
            if kind in {
                "dynamic_helper_invocation", "helper_codebook_population_node",
                "helper_codebook_cache_hit", "helper_codebook_cache_miss",
            }:
                counts[kind] = counts.get(kind, 0) + int(event[5] or 0)

    domain_files = sorted((ROOT / "domains").glob("*.py"))
    rows = []
    for seed_id, item in sorted(manifests.items()):
        scoped = sum(
            1 for rule in item.get("rules", []) for obj in walk(rule)
            if obj.get("type") == "ShapeDecode" and "codebook_scope" in obj
        )
        if not scoped:
            continue
        refs = []
        for path in domain_files:
            try:
                lines = path.read_text(errors="replace").splitlines()
            except OSError:
                continue
            matching = [i + 1 for i, line in enumerate(lines) if seed_id in line]
            if matching:
                refs.append({"path": str(path.relative_to(ROOT)), "lines": matching[:8]})
        rows.append({
            "seed_id": seed_id,
            "seed_path": f"seeds/{seed_id}.json",
            "scoped_shape_decode_terms": scoped,
            "core_boot_dependency_closure": seed_id in core_closure,
            "full_corpus_loader_includes": seed_id in full_corpus,
            "self_load_only": bool(item.get("self_load_only")),
            "depends_on": item.get("depends_on", []),
            "domain_source_references": refs,
            "description": item.get("description", ""),
            "seed_sha256": digest(SEED_DIR / f"{seed_id}.json"),
        })

    result = {
        "schema": "ShapeDecodeActivationAuditV1",
        "run_id": "shape-decode-activation-audit-v1-20261005",
        "runner_path": str(Path(__file__).resolve().relative_to(ROOT)),
        "runner_sha256": digest(Path(__file__).resolve()),
        "loader_contracts": {
            "core_boot": "substrate.boot_core.CORE_SEEDS plus recursive depends_on closure",
            "full_corpus": "substrate.boot_all._seed_manifest_paths plus _read_seeds includes top-level and generated seed JSON except self_load_only manifests",
            "on_demand": "Module source references identify possible explicit workflows; presence is not proof of invocation",
        },
        "source_sha256": {
            str(p.relative_to(ROOT)): digest(p) for p in (CORE, ALL, FACULTY)
        },
        "core_seed_ids": sorted(core_ids),
        "core_dependency_closure_count": len(core_closure),
        "full_corpus_seed_count": len(full_corpus),
        "scoped_shape_decode_seed_count": len(rows),
        "scoped_shape_decode_call_count": sum(r["scoped_shape_decode_terms"] for r in rows),
        "classification_counts": {
            "in_core_boot_closure": sum(r["core_boot_dependency_closure"] for r in rows),
            "included_by_full_corpus_loader": sum(r["full_corpus_loader_includes"] for r in rows),
            "on_demand_only_due_to_self_load_only": sum(r["self_load_only"] for r in rows),
        },
        "seeds": rows,
        "runtime_evidence": {
            "shape_decode_loop": {
                "evidence_path": "evaluation/reports/live_helper_work_capture_v1_4_analysis_20261005.json",
                "observed_shape_decode_invocations": 3,
                "interpretation": "A selected live helper capture observed three calls on the shape_decode_loop route. This is one workflow observation, not a prevalence estimate across ordinary tasks.",
            },
            "vision_verdict_comparator": {
                "workflow_source": "domains/verdict_comparator_world.py::VerdictWorld.__init__",
                "workflow_seed": "vision_verdict_comparator",
                "capture_path": str(VERDICT_CAPTURE.relative_to(ROOT)),
                "analysis_path": str(VERDICT_ANALYSIS.relative_to(ROOT)),
                "capture_sha256": digest(VERDICT_CAPTURE),
                "analysis_sha256": digest(VERDICT_ANALYSIS),
                "seed_sha256_in_capture_manifest": verdict_capture["manifest"]["seed_sha256"],
                "world_sha256_in_capture_manifest": verdict_capture["manifest"]["world_sha256"],
                "current_seed_matches_capture": True,
                "current_world_matches_capture": True,
                "workers": len(verdict_capture["rows"]),
                "distinct_worker_pids": len(verdict_pids),
                "traced_workers_by_mode": verdict_trace_workers,
                "traced_helper_work_by_mode": verdict_work,
                "interpretation": "Runtime proof that this explicit authored comparator workflow executes the scoped cache route. It is an evaluation workload and does not estimate frequency in ordinary operation.",
            },
        },
        "claim_boundary": "Activation classifications describe source-declared loader paths. Domain references can be evaluation-only or conditional; loaded manifests and helper calls in one capture do not establish natural-task prevalence.",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "output": str(OUT.relative_to(ROOT)),
        "core_dependency_closure_count": len(core_closure),
        "full_corpus_seed_count": len(full_corpus),
        "scoped_shape_decode_seed_count": len(rows),
        "scoped_shape_decode_call_count": result["scoped_shape_decode_call_count"],
        "verdict_comparator_workers": len(verdict_capture["rows"]),
        "verdict_comparator_traced_work": verdict_work,
        "classification_counts": result["classification_counts"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

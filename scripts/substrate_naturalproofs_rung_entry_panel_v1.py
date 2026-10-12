#!/usr/bin/env python3
"""Locked 64-statement sequential reading-path rung-entry panel."""
from __future__ import annotations
import hashlib, json, os, platform, resource, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_NATURALPROOFS_RUNG_ENTRY_PANEL_V1_PREREG_20260927.md"
SELECTOR = ROOT / "scripts/audit_naturalproofs_holdout_for_rung_stream_v1.py"
FRAME = ROOT / "evaluation/reports/naturalproofs_rung_stream_frame_v1_20260927.json"
ANALYZER = ROOT / "scripts/analyze_substrate_naturalproofs_rung_entry_panel_v1.py"
LOCK = ROOT / "evaluation/substrate_capability/naturalproofs_rung_entry_panel_v1_lock_20260927.json"
OUT = ROOT / "evaluation/reports/naturalproofs_rung_entry_panel_v1_20260927.json"
WORKERS = (0, 1)

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def tree(folder, suffixes=None):
    result = {}
    for path in sorted(folder.rglob("*")):
        if path.is_file() and "__pycache__" not in path.parts and (suffixes is None or path.suffix in suffixes):
            result[path.relative_to(ROOT).as_posix()] = sha(path)
    return result

def inputs():
    from substrate_rs import _native
    return {
        "protocol_sha256": sha(PROTOCOL), "selector_sha256": sha(SELECTOR),
        "frame_sha256": sha(FRAME), "runner_sha256": sha(__file__),
        "analyzer_sha256": sha(ANALYZER),
        "source_trees": {
            "domains": tree(ROOT / "domains", {".py"}),
            "substrate": tree(ROOT / "substrate", {".py"}),
            "worlds": tree(ROOT / "worlds", {".py"}),
            "scripts": tree(ROOT / "scripts", {".py"}),
            "seeds": tree(ROOT / "seeds", {".json"}),
            "native_python": tree(ROOT / "runners/dsl/python", {".py"}),
            "rust": tree(ROOT / "runners/dsl/src", {".rs"}),
            "naturalproofs": tree(ROOT / "data/naturalproofs"),
            "slabs": tree(ROOT / "data/slabs"),
            "corpus": tree(ROOT / "data/corpus"),
        },
        "native_extension_sha256": sha(Path(_native.__file__).resolve()),
    }

def node_id(node): return int(node.value if hasattr(node, "value") else node)
def concern_receipts(adapter):
    rows = []
    for node in adapter.s.nodes("NativeReflectiveFacultyReceipt"):
        attrs = adapter.s.node(node)["attrs"]
        if attrs.get("cluster") == "reflective_faculty.concern_decode_settlement":
            rows.append({"id": node_id(node), "native_steps": attrs.get("native_steps"),
                         "native_rule": attrs.get("native_rule"),
                         "provenance": attrs.get("provenance")})
    return rows

def node_summaries(adapter, type_name, fields):
    rows = []
    for node in adapter.s.nodes(type_name):
        attrs = adapter.s.node(node)["attrs"]
        rows.append({"id": node_id(node), **{key: attrs.get(key) for key in fields}})
    return rows

def worker(rep):
    before = inputs()
    from substrate.world_adapter import WorldAdapter
    from substrate.boot_all import load_all_seeds
    from substrate_rs import _native
    frame = json.loads(FRAME.read_text())
    shard = ROOT / frame["shards"]["test"]["path"]
    lines = shard.read_text(encoding="utf-8").splitlines()
    adapter = WorldAdapter(seeds=(), shadow_read=False, deep_ingest=False)
    boot_wall_start, boot_cpu_start = time.perf_counter_ns(), time.process_time_ns()
    boot = load_all_seeds(adapter)
    boot_wall = time.perf_counter_ns() - boot_wall_start
    boot_cpu = time.process_time_ns() - boot_cpu_start
    case_rows = []
    for index, selected in enumerate(frame["selected"]):
        raw = json.loads(lines[int(selected["source_line"]) - 1])
        statement = str(raw["text"])
        statement_sha = hashlib.sha256(statement.encode("utf-8")).hexdigest()
        del raw
        receipt_before = {row["id"] for row in concern_receipts(adapter)}
        obs_before = {row["id"] for row in node_summaries(adapter, "Observation", ())}
        axis_before = {row["id"] for row in node_summaries(adapter, "CapabilityAxis", ())}
        transform_before = {row["id"] for row in node_summaries(adapter, "Transform", ())}
        signature_before = {row["id"] for row in node_summaries(adapter, "ShapeSignature", ())}
        nodes_before, edges_before = adapter.inner.node_count(), adapter.inner.edge_count()
        wall_start, cpu_start = time.perf_counter_ns(), time.process_time_ns()
        error = None
        reply = None
        try:
            reply = adapter.converse(statement, speech_act="statement", speaker="user")
            reply_present = bool(str(reply).strip())
        except BaseException as exc:
            reply_present = False
            error = f"{type(exc).__name__}: {exc}"
        wall_ns = time.perf_counter_ns() - wall_start
        cpu_ns = time.process_time_ns() - cpu_start
        del reply
        receipt_after = concern_receipts(adapter)
        new_receipts = [row for row in receipt_after if row["id"] not in receipt_before]
        observations_after = node_summaries(adapter, "Observation", ("status", "covered_by", "key"))
        new_observations = [row for row in observations_after if row["id"] not in obs_before]
        for observation in new_observations:
            oid = _native.NodeID(observation["id"])
            observation["minted_axis_ids"] = [node_id(n) for n in adapter.inner.neighbours(oid, "minted")]
            observation["transform_ids"] = [node_id(n) for n in adapter.inner.neighbours(oid, "has_transform")]
        axes_after = node_summaries(adapter, "CapabilityAxis", ("name", "origin", "provenance",
            "induced", "kind", "word", "shortfall", "saturation", "capability_keys",
            "residual_predicates", "closest_held_shape"))
        new_axes = [row for row in axes_after if row["id"] not in axis_before]
        for axis in new_axes:
            word = axis.pop("word", None)
            axis["word_sha256"] = hashlib.sha256(str(word).encode("utf-8")).hexdigest() if word is not None else None
        transforms_after = node_summaries(adapter, "Transform", ("name", "kind", "status"))
        new_transforms = [row for row in transforms_after if row["id"] not in transform_before]
        signatures_after = node_summaries(adapter, "ShapeSignature", ("name", "signature", "capability_keys"))
        new_signatures = [row for row in signatures_after if row["id"] not in signature_before]
        case_rows.append({
            "index": index, "sample_id": selected["id"],
            "statement_sha256_expected": selected["statement_sha256"],
            "statement_sha256_observed": statement_sha,
            "source_line": selected["source_line"],
            "reply_present": reply_present, "error": error,
            "task_wall_ns": wall_ns, "task_cpu_ns": cpu_ns,
            "receipt_delta": len(new_receipts), "new_receipts": new_receipts,
            "new_observations": new_observations,
            "new_capability_axes": new_axes, "new_transforms": new_transforms,
            "new_induced_axes": [row for row in new_axes if row.get("induced")],
            "new_shape_signatures": new_signatures,
            "node_delta": adapter.inner.node_count() - nodes_before,
            "edge_delta": adapter.inner.edge_count() - edges_before,
        })
    after = inputs()
    return {
        "replicate": rep, "pid": os.getpid(), "locked_inputs_before": before,
        "locked_inputs_after": after, "source_stable": before == after,
        "boot": {"loaded": boot.get("loaded"), "total": boot.get("total"),
                 "failed": boot.get("failed", []), "wall_ns": boot_wall,
                 "cpu_ns": boot_cpu},
        "runtime": {"peak_rss_bytes": int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024),
                    "python": sys.version, "platform": platform.platform()},
        "tasks": case_rows,
    }

def main():
    if sys.argv[1:] == ["--lock"]:
        print(json.dumps({"locked_inputs": inputs()}, indent=2, sort_keys=True)); return
    if sys.argv[1:] == ["--worker"]:
        row = worker(int(os.environ["OCEL0_NP_RUNG_REP"]))
        print(json.dumps(row, sort_keys=True)); return
    locked = inputs()
    if not LOCK.exists() or json.loads(LOCK.read_text()).get("locked_inputs") != locked:
        raise SystemExit("missing or stale NaturalProofs rung-entry lock")
    env = {**os.environ, "PYTHONPATH": f"{ROOT}:{ROOT / 'runners/dsl/python'}",
           "OZMA_SEED_PERSIST_DISABLED": "1"}
    runs = []
    for rep in WORKERS:
        proc = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--worker"],
                              cwd=ROOT, env={**env, "OCEL0_NP_RUNG_REP": str(rep)},
                              text=True, capture_output=True, timeout=1800)
        try: row = json.loads(proc.stdout)
        except Exception: row = {"replicate": rep, "worker_error": proc.stderr or proc.stdout}
        row.update({"worker_returncode": proc.returncode, "worker_stderr": proc.stderr})
        runs.append(row)
        print(f"completed=worker{rep} rc={proc.returncode}", file=sys.stderr, flush=True)
    post = inputs()
    checks = {
        "two_fresh_workers": len(runs) == 2 and len({r.get("pid") for r in runs}) == 2,
        "lock_stable_parent": post == locked,
        "worker_source_stable": all(r.get("source_stable") and
            r.get("locked_inputs_before") == locked == r.get("locked_inputs_after") for r in runs),
        "all_64_rows_each": all(len(r.get("tasks", [])) == 64 for r in runs),
        "worker_success": all(r.get("worker_returncode") == 0 and r.get("boot", {}).get("loaded", 0) > 0 for r in runs),
    }
    report = {"schema_version": 1, "run_id": "naturalproofs-rung-entry-panel-v1-20260927",
              "locked_inputs": locked, "post_run_inputs": post,
              "integrity_checks": checks, "integrity_pass": all(checks.values()),
              "runs": runs,
              "claim_boundary": "Sequential full-runtime conversation reading-path receipt deltas over a frozen 64-statement NaturalProofs test-shard sample. Not proof-generation accuracy, broad natural-task prevalence, default core-only behavior, or general induction capability."}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"report": OUT.relative_to(ROOT).as_posix(), "integrity_checks": checks}, indent=2))
    if not report["integrity_pass"]: raise SystemExit("integrity gates failed")

if __name__ == "__main__": main()

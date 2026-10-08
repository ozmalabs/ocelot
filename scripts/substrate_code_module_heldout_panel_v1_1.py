#!/usr/bin/env python3
"""Source-locked full-runtime CPython module-held-out prediction panel v1.1."""
from __future__ import annotations
import hashlib, json, os, platform, resource, subprocess, sys, time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
CORPUS = ROOT / "data/cpython_lib_3_13_5"
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_CODE_MODULE_HELDOUT_PANEL_V1_1_PREREG_20260928.md"
FRAME = ROOT / "evaluation/substrate_capability/code_module_heldout_panel_v1_1_frame_20260928.json"
SELECTOR = ROOT / "scripts/select_cpython_module_heldout_frame_v1_1.py"
ANALYZER = ROOT / "scripts/analyze_substrate_code_module_heldout_panel_v1_1.py"
LOCK = ROOT / "evaluation/substrate_capability/code_module_heldout_panel_v1_1_lock_20260928.json"
OUT = ROOT / "evaluation/reports/code_module_heldout_panel_v1_1_20260928.json"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def tree(folder, suffixes):
    return {p.relative_to(ROOT).as_posix(): sha(p) for p in sorted(folder.rglob("*"))
            if p.is_file() and "__pycache__" not in p.parts and p.suffix in suffixes}


def seed_tree(folder):
    paths = sorted(folder.glob("*.json")) + sorted((folder / "generated").glob("*.json"))
    return {p.relative_to(ROOT).as_posix(): sha(p) for p in paths if p.is_file()}


def inputs():
    from substrate_rs import _native
    return {
        "protocol_sha256": sha(PROTOCOL), "frame_sha256": sha(FRAME), "selector_sha256": sha(SELECTOR),
        "runner_sha256": sha(__file__), "analyzer_sha256": sha(ANALYZER),
        "source_trees": {
            "domains": tree(ROOT / "domains", {".py"}), "substrate": tree(ROOT / "substrate", {".py"}),
            "worlds": tree(ROOT / "worlds", {".py"}), "scripts": tree(ROOT / "scripts", {".py"}),
            "seeds": seed_tree(ROOT / "seeds"), "native_python": tree(ROOT / "runners/dsl/python", {".py"}),
            "rust": tree(ROOT / "runners/dsl/src", {".rs"}), "cpython_corpus": tree(CORPUS, {".py", ".txt", ".md"}),
        },
        "native_extension_sha256": sha(Path(_native.__file__).resolve()),
    }


def nodeid(node):
    return int(node.value if hasattr(node, "value") else node)


def rows(agent, typ, fields):
    return [{"id": nodeid(n), **{k: agent.s.node(n)["attrs"].get(k) for k in fields}} for n in agent.s.nodes(typ)]


def receipts(agent):
    return [r for r in rows(agent, "NativeReflectiveFacultyReceipt", ("cluster", "native_steps", "native_rule"))
            if r.get("cluster") == "reflective_faculty.concern_decode_settlement"]


def worker(rep):
    before = inputs()
    from substrate.world_adapter import WorldAdapter
    from substrate.boot_all import load_all_seeds
    from domains import code_reading
    frame = json.loads(FRAME.read_text(encoding="utf-8"))
    agent = WorldAdapter(seeds=(), shadow_read=False, deep_ingest=False)
    boot_start, boot_cpu_start = time.perf_counter_ns(), time.process_time_ns()
    boot = load_all_seeds(agent)
    boot_wall, boot_cpu = time.perf_counter_ns() - boot_start, time.process_time_ns() - boot_cpu_start
    calls = []
    for fi, row in enumerate(frame["selected"]):
        source_path = CORPUS / row["file"]
        source = source_path.read_text(encoding="utf-8")
        for ci, args in enumerate(row["input_cases"]):
            receipt_before = {r["id"] for r in receipts(agent)}
            obs_before = {r["id"] for r in rows(agent, "Observation", ())}
            axes_before = {r["id"] for r in rows(agent, "CapabilityAxis", ())}
            wall_start, cpu_start, prediction, error = time.perf_counter_ns(), time.process_time_ns(), None, None
            try:
                value = code_reading.predict_output(agent, source, row["function"], args)
                if value is None or type(value) in (bool, int, float, str):
                    prediction = {"type": type(value).__name__, "value": value}
                else:
                    error = "NonPrimitivePrediction"
            except BaseException as exc:
                error = type(exc).__name__
            wall_ns, cpu_ns = time.perf_counter_ns() - wall_start, time.process_time_ns() - cpu_start
            new_obs = [r for r in rows(agent, "Observation", ("status", "covered_by", "key")) if r["id"] not in obs_before]
            for obs in new_obs:
                obs["minted_axis_ids"] = [nodeid(x) for x in agent.inner.neighbours(__import__("substrate_rs")._native.NodeID(obs["id"]), "minted")]
            calls.append({"function_index": fi, "case_index": ci, "file": row["file"], "function": row["function"],
                          "module_sha256_expected": row["module_sha256"], "function_sha256_expected": row["function_sha256"],
                          "module_sha256_observed": sha(source_path), "args": args, "prediction": prediction,
                          "error_type": error, "abstained": error is not None, "wall_ns": wall_ns, "cpu_ns": cpu_ns,
                          "receipt_delta": len({r["id"] for r in receipts(agent)} - receipt_before),
                          "new_observations": new_obs,
                          "new_axis_count": len({r["id"] for r in rows(agent, "CapabilityAxis", ())} - axes_before)})
    after = inputs()
    return {"replicate": rep, "pid": os.getpid(), "source_stable": before == after,
            "locked_inputs_before": before, "locked_inputs_after": after,
            "boot": {"loaded": boot.get("loaded"), "total": boot.get("total"), "failed": boot.get("failed", []),
                     "wall_ns": boot_wall, "cpu_ns": boot_cpu},
            "runtime": {"peak_rss_bytes": int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024),
                        "python": sys.version, "platform": platform.platform()}, "calls": calls}


def main():
    if sys.argv[1:] == ["--lock"]:
        print(json.dumps({"locked_inputs": inputs()}, indent=2, sort_keys=True)); return
    if sys.argv[1:] == ["--worker"]:
        print(json.dumps(worker(int(os.environ["OCEL0_CODE_MODULE_HELDOUT_V1_1_REP"])), sort_keys=True)); return
    frozen = inputs()
    if not LOCK.exists() or json.loads(LOCK.read_text()).get("locked_inputs") != frozen:
        raise SystemExit("missing or stale CPython module-heldout source lock")
    from scripts.substrate_run_manifest import start_console_capture, finish_console_capture, capture_run_manifest
    run_id = "code-module-heldout-panel-v1-1-20260928"
    started, capture_state = datetime.now(timezone.utc).isoformat(), start_console_capture(run_id)
    env = {**os.environ, "PYTHONPATH": f"{ROOT}:{ROOT / 'runners/dsl/python'}", "OZMA_SEED_PERSIST_DISABLED": "1"}
    runs = []
    for rep in (0, 1):
        proc = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--worker"], cwd=ROOT,
                              env={**env, "OCEL0_CODE_MODULE_HELDOUT_V1_1_REP": str(rep)},
                              text=True, capture_output=True, timeout=3600)
        try: result = json.loads(proc.stdout)
        except Exception: result = {"replicate": rep, "worker_error": proc.stderr or proc.stdout}
        result.update({"worker_returncode": proc.returncode, "worker_stderr": proc.stderr}); runs.append(result)
        print(f"completed=worker{rep} rc={proc.returncode}", file=sys.stderr, flush=True)
    post = inputs()
    expected_calls = sum(len(x["input_cases"]) for x in json.loads(FRAME.read_text())["selected"])
    checks = {"parent_lock_stable": post == frozen,
              "two_fresh_workers": len(runs) == 2 and len({r.get("pid") for r in runs}) == 2,
              "worker_source_stability": all(r.get("source_stable") and r.get("locked_inputs_before") == frozen == r.get("locked_inputs_after") for r in runs),
              "complete_schedules": all(len(r.get("calls", [])) == expected_calls for r in runs),
              "workers_succeeded": all(r.get("worker_returncode") == 0 and r.get("boot", {}).get("loaded", 0) > 0 for r in runs)}
    console = finish_console_capture(capture_state)
    source_paths = sorted({p for values in frozen["source_trees"].values() for p in values})
    manifest = capture_run_manifest(run_id=run_id, runner="scripts/substrate_code_module_heldout_panel_v1_1.py",
        protocol_files=[PROTOCOL.relative_to(ROOT).as_posix(), FRAME.relative_to(ROOT).as_posix(), SELECTOR.relative_to(ROOT).as_posix()],
        source_files=source_paths + [LOCK.relative_to(ROOT).as_posix()], data_files=[FRAME.relative_to(ROOT).as_posix()],
        analysis_files=[ANALYZER.relative_to(ROOT).as_posix()], started_utc=started,
        exit_status=0 if all(checks.values()) else 1, stdout_stderr_capture=console,
        child_processes=[{"replicate": r.get("replicate"), "pid": r.get("pid"), "returncode": r.get("worker_returncode"),
                          "stderr": r.get("worker_stderr"), "structured_stdout_embedded_in_raw": True} for r in runs])
    report = {"schema": "code-module-heldout-panel-raw-v1.1", "run_id": run_id, "locked_inputs": frozen,
              "post_run_inputs": post, "integrity_checks": checks, "integrity_pass": all(checks.values()),
              "run_manifest": manifest, "runs": runs,
              "claim_boundary": "Same-project CPython module-held-out bounded code fragment; not independent-project transfer or general Python accuracy."}
    OUT.parent.mkdir(parents=True, exist_ok=True); OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"report": OUT.relative_to(ROOT).as_posix(), "integrity_checks": checks}, indent=2))
    if not report["integrity_pass"]: raise SystemExit("module-heldout source integrity failed")


if __name__ == "__main__": main()

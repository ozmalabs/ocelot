#!/usr/bin/env python3
"""Two-worker source-locked safety/refusal probe for bounded code composition."""
from __future__ import annotations
import hashlib, json, os, platform, resource, subprocess, sys, time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_CODE_COMPOSITION_REFUSAL_PANEL_V1_PREREG_20260928.md"
AMENDMENT = ROOT / "docs/research/engine_substrate/SUBSTRATE_CODE_COMPOSITION_REFUSAL_PANEL_V1_AMENDMENT_20260928.md"
FRAME = ROOT / "evaluation/substrate_capability/code_composition_refusal_panel_v1_frame_20260928.json"
LOCK = ROOT / "evaluation/substrate_capability/code_composition_refusal_panel_v1_lock_20260928.json"
OUT = ROOT / "evaluation/reports/code_composition_refusal_panel_v1_20260928.json"
ANALYZER = ROOT / "scripts/analyze_substrate_code_composition_refusal_panel_v1.py"
SENTINEL = Path("/tmp/ocelot_code_composition_refusal_sentinel_20260928")


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
        "protocol_sha256": sha(PROTOCOL), "amendment_sha256": sha(AMENDMENT), "frame_sha256": sha(FRAME),
        "runner_sha256": sha(__file__), "analyzer_sha256": sha(ANALYZER),
        "source_trees": {
            "domains": tree(ROOT / "domains", {".py"}),
            "substrate": tree(ROOT / "substrate", {".py"}),
            "worlds": tree(ROOT / "worlds", {".py"}),
            "scripts": tree(ROOT / "scripts", {".py"}),
            "seeds": seed_tree(ROOT / "seeds"),
            "native_python": tree(ROOT / "runners/dsl/python", {".py"}),
            "rust": tree(ROOT / "runners/dsl/src", {".rs"}),
        },
        "native_extension_sha256": sha(Path(_native.__file__).resolve()),
    }


def observe_case(agent, case):
    from domains import code_reading
    SENTINEL.unlink(missing_ok=True)
    before = time.perf_counter_ns(), time.process_time_ns()
    value, error = None, None
    try:
        result = code_reading.predict_output(agent, case["source"], case["function"], case["args"])
        value = {"type": type(result).__name__, "value": result}
    except BaseException as exc:
        error = type(exc).__name__
    wall = time.perf_counter_ns() - before[0]
    cpu = time.process_time_ns() - before[1]
    sentinel_created = SENTINEL.exists()
    if sentinel_created:
        SENTINEL.unlink()
    return {"id": case["id"], "args": case["args"], "value": value, "error_type": error,
            "abstained": error is not None, "sentinel_created": sentinel_created,
            "wall_ns": wall, "cpu_ns": cpu}


def worker(rep):
    locked_before = inputs()
    from substrate.world_adapter import WorldAdapter
    from substrate.boot_all import load_all_seeds
    cases = json.loads(FRAME.read_text(encoding="utf-8"))["cases"]
    agent = WorldAdapter(seeds=(), shadow_read=False, deep_ingest=False)
    boot_wall_start, boot_cpu_start = time.perf_counter_ns(), time.process_time_ns()
    boot = load_all_seeds(agent)
    boot_wall, boot_cpu = time.perf_counter_ns() - boot_wall_start, time.process_time_ns() - boot_cpu_start
    outcomes = [observe_case(agent, case) for case in cases]
    locked_after = inputs()
    return {"replicate": rep, "pid": os.getpid(), "source_stable": locked_before == locked_after,
            "locked_inputs_before": locked_before, "locked_inputs_after": locked_after,
            "boot": {"loaded": boot.get("loaded"), "total": boot.get("total"),
                     "failed": boot.get("failed", []), "wall_ns": boot_wall, "cpu_ns": boot_cpu},
            "runtime": {"peak_rss_bytes": int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024),
                        "python": sys.version, "platform": platform.platform()}, "outcomes": outcomes}


def main():
    if sys.argv[1:] == ["--lock"]:
        print(json.dumps({"locked_inputs": inputs()}, indent=2, sort_keys=True))
        return
    if sys.argv[1:] == ["--worker"]:
        print(json.dumps(worker(int(os.environ["OCEL0_CODE_COMPOSITION_REFUSAL_REP"])), sort_keys=True))
        return
    frozen = inputs()
    if not LOCK.exists() or json.loads(LOCK.read_text()).get("locked_inputs") != frozen:
        raise SystemExit("missing or stale code-composition refusal source lock")
    from scripts.substrate_run_manifest import start_console_capture, finish_console_capture, capture_run_manifest
    run_id = "code-composition-refusal-panel-v1-20260928"
    started, capture_state = datetime.now(timezone.utc).isoformat(), start_console_capture(run_id)
    env = {**os.environ, "PYTHONPATH": f"{ROOT}:{ROOT / 'runners/dsl/python'}", "OZMA_SEED_PERSIST_DISABLED": "1"}
    runs = []
    for rep in (0, 1):
        proc = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--worker"], cwd=ROOT,
                              env={**env, "OCEL0_CODE_COMPOSITION_REFUSAL_REP": str(rep)},
                              text=True, capture_output=True, timeout=1800)
        try:
            outcome = json.loads(proc.stdout)
        except Exception:
            outcome = {"replicate": rep, "worker_error": proc.stderr or proc.stdout}
        outcome.update({"worker_returncode": proc.returncode, "worker_stderr": proc.stderr})
        runs.append(outcome)
        print(f"completed=worker{rep} rc={proc.returncode}", file=sys.stderr, flush=True)
    post = inputs()
    case_count = len(json.loads(FRAME.read_text())["cases"])
    integrity = {
        "parent_lock_stable": post == frozen,
        "two_fresh_workers": len(runs) == 2 and len({r.get("pid") for r in runs}) == 2,
        "workers_source_stable": all(r.get("source_stable") and r.get("locked_inputs_before") == frozen == r.get("locked_inputs_after") for r in runs),
        "complete_schedule": all(len(r.get("outcomes", [])) == case_count for r in runs),
        "workers_succeeded": all(r.get("worker_returncode") == 0 and r.get("boot", {}).get("loaded", 0) > 0 for r in runs),
    }
    console = finish_console_capture(capture_state)
    source_paths = sorted({p for group, values in frozen["source_trees"].items() for p in values})
    manifest = capture_run_manifest(
        run_id=run_id, runner="scripts/substrate_code_composition_refusal_panel_v1.py",
        protocol_files=[PROTOCOL.relative_to(ROOT).as_posix(), AMENDMENT.relative_to(ROOT).as_posix(), FRAME.relative_to(ROOT).as_posix()],
        source_files=source_paths + [LOCK.relative_to(ROOT).as_posix()],
        data_files=[FRAME.relative_to(ROOT).as_posix()],
        analysis_files=[ANALYZER.relative_to(ROOT).as_posix()], started_utc=started,
        exit_status=0 if all(integrity.values()) else 1, stdout_stderr_capture=console,
        child_processes=[{"replicate": r.get("replicate"), "pid": r.get("pid"),
                          "returncode": r.get("worker_returncode"), "stderr": r.get("worker_stderr"),
                          "structured_stdout_embedded_in_raw": True} for r in runs])
    report = {"schema": "code-composition-refusal-panel-raw-v1", "run_id": run_id,
              "locked_inputs": frozen, "post_run_inputs": post, "integrity_checks": integrity,
              "integrity_pass": all(integrity.values()), "run_manifest": manifest, "runs": runs,
              "claim_boundary": "Targeted module-composition refusal and no-source-execution probes; not general Python accuracy or OS containment."}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"report": OUT.relative_to(ROOT).as_posix(), "integrity_checks": integrity}, indent=2))
    if not report["integrity_pass"]:
        raise SystemExit("refusal panel source integrity failed")


if __name__ == "__main__":
    main()

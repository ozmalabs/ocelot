#!/usr/bin/env python3
"""Source-locked CPython stat predicate behavior panel."""
from __future__ import annotations
import hashlib, json, os, platform, resource, subprocess, sys, time, re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_STDLIB_STAT_PREDICTION_PANEL_V1_2_REPLAY_PREREG_20260928.md"
SELECTOR = ROOT / "scripts/audit_stdlib_stat_prediction_frame_v1.py"
FRAME = ROOT / "evaluation/reports/stdlib_stat_prediction_frame_v1_20260927.json"
ANALYZER = ROOT / "scripts/analyze_substrate_stdlib_stat_prediction_panel_v1_2.py"
LOCK = ROOT / "evaluation/substrate_capability/stdlib_stat_prediction_panel_v1_2_lock_20260928.json"
OUT = ROOT / "evaluation/reports/stdlib_stat_prediction_panel_v1_2_20260928.json"
SOURCE = ROOT / "data/python_stdlib_3_13_5/stat.py"
LICENSE = ROOT / "data/python_stdlib_3_13_5/LICENSE.txt"
SOURCE_NOTE = ROOT / "data/python_stdlib_3_13_5/SOURCE.md"
TPDATA = ROOT / "data/think_python_2e"
V2_RAW = ROOT / "evaluation/reports/stacks_string_prediction_panel_v2_20260927.json"
V2_ANALYSIS = ROOT / "evaluation/reports/stacks_string_prediction_panel_v2_analysis_20260927.json"
V2_FRAME = ROOT / "evaluation/reports/stacks_string_prediction_frame_v2_20260927.json"
BASE_RAW = ROOT / "evaluation/reports/stdlib_stat_prediction_panel_v1_20260927.json"
BASE_ANALYSIS = ROOT / "evaluation/reports/stdlib_stat_prediction_panel_v1_analysis_20260927.json"
BASE_FRAME = ROOT / "evaluation/reports/stdlib_stat_prediction_frame_v1_20260927.json"
BASE_LOCK = ROOT / "evaluation/substrate_capability/stdlib_stat_prediction_panel_v1_lock_20260927.json"
BLOCK = re.compile(r"```(?:python)?\s*\n(.*?)\n```", re.S | re.I)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def tree(folder, suffixes=None):
    return {p.relative_to(ROOT).as_posix(): sha(p) for p in sorted(folder.rglob("*"))
            if p.is_file() and "__pycache__" not in p.parts
            and (suffixes is None or p.suffix in suffixes)}


def loaded_seed_tree(folder):
    paths = sorted(folder.glob("*.json")) + sorted((folder / "generated").glob("*.json"))
    return {p.relative_to(ROOT).as_posix(): sha(p) for p in paths if p.is_file()}


def inputs():
    from substrate_rs import _native
    corpus_root = SOURCE.parent
    return {
        "protocol_sha256": sha(PROTOCOL), "selector_sha256": sha(SELECTOR),
        "frame_sha256": sha(FRAME), "runner_sha256": sha(__file__),
        "analyzer_sha256": sha(ANALYZER),
        "source_trees": {
            "domains": tree(ROOT / "domains", {".py"}),
            "substrate": tree(ROOT / "substrate", {".py"}),
            "worlds": tree(ROOT / "worlds", {".py"}),
            "scripts": tree(ROOT / "scripts", {".py"}),
            "seeds": loaded_seed_tree(ROOT / "seeds"),
            "native_python": tree(ROOT / "runners/dsl/python", {".py"}),
            "rust": tree(ROOT / "runners/dsl/src", {".rs"}),
            "stdlib_stat_corpus": tree(corpus_root),
            "think_python_control": tree(TPDATA),
        },
        "think_python_v2_reference": {
            "raw": sha(V2_RAW), "analysis": sha(V2_ANALYSIS), "frame": sha(V2_FRAME)},
        "baseline_v1_artifacts": {"raw": sha(BASE_RAW), "analysis": sha(BASE_ANALYSIS),
                                  "frame": sha(BASE_FRAME), "lock": sha(BASE_LOCK)},
        "native_extension_sha256": sha(Path(_native.__file__).resolve()),
    }


def nodeid(node):
    return int(node.value if hasattr(node, "value") else node)


def rows(agent, typ, fields):
    return [{"id": nodeid(n), **{k: agent.s.node(n)["attrs"].get(k) for k in fields}}
            for n in agent.s.nodes(typ)]


def receipts(agent):
    return [r for r in rows(agent, "NativeReflectiveFacultyReceipt",
                            ("cluster", "native_steps", "native_rule"))
            if r.get("cluster") == "reflective_faculty.concern_decode_settlement"]


def norm(value):
    if value is None or type(value) in (bool, int, float, str):
        return {"type": type(value).__name__, "value": value}
    raise TypeError("nonprimitive output")


def worker(rep):
    before = inputs()
    from substrate.world_adapter import WorldAdapter
    from substrate.boot_all import load_all_seeds
    from substrate_rs import _native
    from domains import code_reading
    frame = json.loads(FRAME.read_text(encoding="utf-8"))
    agent = WorldAdapter(seeds=(), shadow_read=False, deep_ingest=False)
    boot_wall_start, boot_cpu_start = time.perf_counter_ns(), time.process_time_ns()
    boot = load_all_seeds(agent)
    boot_wall, boot_cpu, calls = time.perf_counter_ns() - boot_wall_start, time.process_time_ns() - boot_cpu_start, []
    schedule = [("stat", row) for row in frame["selected"]] + [("positive_control", frame["positive_control"])]
    for fi, (corpus, row) in enumerate(schedule):
        if corpus == "stat":
            source = SOURCE.read_text(encoding="utf-8")
            cases = row["input_cases"]
        else:
            chapter_text = (TPDATA / row["chapter"]).read_text(encoding="utf-8")
            source = list(BLOCK.finditer(chapter_text))[row["block_index"]].group(1)
            cases = row["input_cases"]
        for ci, args in enumerate(cases):
            receipt_before = {r["id"] for r in receipts(agent)}
            obs_before = {r["id"] for r in rows(agent, "Observation", ())}
            axes_before = {r["id"] for r in rows(agent, "CapabilityAxis", ())}
            node_before, edge_before = agent.inner.node_count(), agent.inner.edge_count()
            wall_start, cpu_start, prediction, error = time.perf_counter_ns(), time.process_time_ns(), None, None
            try:
                prediction = norm(code_reading.predict_output(agent, source, row["function"], args))
            except BaseException as exc:
                error = type(exc).__name__
            wall, cpu = time.perf_counter_ns() - wall_start, time.process_time_ns() - cpu_start
            new_observations = []
            for obs in rows(agent, "Observation", ("status", "covered_by", "key")):
                if obs["id"] not in obs_before:
                    native_id = _native.NodeID(obs["id"])
                    obs["minted_axis_ids"] = [nodeid(x) for x in agent.inner.neighbours(native_id, "minted")]
                    new_observations.append(obs)
            calls.append({
                "function_index": fi, "case_index": ci, "corpus": corpus,
                "function": row["function"], "function_sha256_expected": row.get("function_sha256", row.get("source_sha256")),
                "module_sha256_expected": row.get("module_sha256", row.get("file_sha256")),
                "source_sha256_observed": hashlib.sha256(source.encode()).hexdigest(),
                "args": args, "prediction": prediction, "error_type": error,
                "abstained": error is not None, "wall_ns": wall, "cpu_ns": cpu,
                "receipt_delta": len({r["id"] for r in receipts(agent)} - receipt_before),
                "new_observations": new_observations,
                "new_axis_count": len({r["id"] for r in rows(agent, "CapabilityAxis", ())} - axes_before),
                "node_delta": agent.inner.node_count() - node_before,
                "edge_delta": agent.inner.edge_count() - edge_before,
            })
    after = inputs()
    return {
        "replicate": rep, "pid": os.getpid(), "source_stable": before == after,
        "locked_inputs_before": before, "locked_inputs_after": after,
        "boot": {"loaded": boot.get("loaded"), "total": boot.get("total"),
                 "failed": boot.get("failed", []), "wall_ns": boot_wall, "cpu_ns": boot_cpu},
        "runtime": {"peak_rss_bytes": int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024),
                    "python": sys.version, "platform": platform.platform()},
        "calls": calls,
    }


def main():
    if sys.argv[1:] == ["--frame"]:
        import runpy
        selector = runpy.run_path(str(SELECTOR))
        control = selector["positive_control"]()
        selected = selector["candidates"]()
        FRAME.write_text(json.dumps({"schema_version": 1, "candidate_count": len(selected),
                                     "selected": selected, "positive_control": control},
                                    indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(FRAME.relative_to(ROOT))
        return
    if sys.argv[1:] == ["--lock"]:
        print(json.dumps({"locked_inputs": inputs()}, indent=2, sort_keys=True))
        return
    if sys.argv[1:] == ["--worker"]:
        print(json.dumps(worker(int(os.environ["OCEL0_STDLIB_STAT_PRED_V1_2_REP"])), sort_keys=True))
        return
    locked = inputs()
    if not LOCK.exists() or json.loads(LOCK.read_text()).get("locked_inputs") != locked:
        raise SystemExit("missing or stale CPython stat prediction lock")
    from scripts.substrate_run_manifest import start_console_capture, finish_console_capture, capture_run_manifest
    run_id = "stdlib-stat-prediction-panel-v1-2-20260928"
    started, capture_state = datetime.now(timezone.utc).isoformat(), start_console_capture(run_id)
    env = {**os.environ, "PYTHONPATH": f"{ROOT}:{ROOT / 'runners/dsl/python'}", "OZMA_SEED_PERSIST_DISABLED": "1"}
    runs = []
    for rep in (0, 1):
        proc = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--worker"], cwd=ROOT,
                              env={**env, "OCEL0_STDLIB_STAT_PRED_V1_2_REP": str(rep)},
                              text=True, capture_output=True, timeout=1800)
        try:
            result = json.loads(proc.stdout)
        except Exception:
            result = {"replicate": rep, "worker_error": proc.stderr or proc.stdout}
        result.update({"worker_returncode": proc.returncode, "worker_stderr": proc.stderr})
        runs.append(result)
        print(f"completed=worker{rep} rc={proc.returncode}", file=sys.stderr, flush=True)
    post = inputs()
    frame = json.loads(FRAME.read_text(encoding="utf-8"))
    expected_calls = sum(len(row["input_cases"]) for row in frame["selected"]) + len(frame["positive_control"]["input_cases"])
    checks = {
        "two_fresh_workers": len(runs) == 2 and len({r.get("pid") for r in runs}) == 2,
        "parent_lock_stable": post == locked,
        "worker_source_stability": all(r.get("source_stable") and r.get("locked_inputs_before") == locked == r.get("locked_inputs_after") for r in runs),
        "complete_schedules": all(len(r.get("calls", [])) == expected_calls for r in runs),
        "workers_succeeded": all(r.get("worker_returncode") == 0 and r.get("boot", {}).get("loaded", 0) > 0 for r in runs),
    }
    console = finish_console_capture(capture_state)
    trees = locked["source_trees"]
    source_paths = sorted({p for key, values in trees.items() if key not in ("stdlib_stat_corpus", "think_python_control") for p in values})
    data_paths = sorted({p for key in ("stdlib_stat_corpus", "think_python_control") for p in trees[key]})
    data_paths += [p.relative_to(ROOT).as_posix() for p in (V2_RAW, V2_ANALYSIS, V2_FRAME,
                                                             BASE_RAW, BASE_ANALYSIS, BASE_FRAME, BASE_LOCK)]
    manifest = capture_run_manifest(
        run_id=run_id, runner="scripts/substrate_stdlib_stat_prediction_panel_v1_2.py",
        protocol_files=[PROTOCOL.relative_to(ROOT).as_posix(),
                        "docs/research/engine_substrate/SUBSTRATE_STDLIB_STAT_PREDICTION_PANEL_V1_1_INTERVENTION_PREREG_20260927.md",
                        "docs/research/engine_substrate/SUBSTRATE_STDLIB_STAT_PREDICTION_PANEL_V1_1_AMENDMENT_20260927.md",
                        "docs/research/engine_substrate/SUBSTRATE_STDLIB_STAT_PREDICTION_PANEL_V1_2_AMENDMENT_20260928.md",
                        "docs/research/engine_substrate/SUBSTRATE_STDLIB_STAT_PREDICTION_PANEL_V1_PREREG_20260927.md",
                        "docs/research/engine_substrate/SUBSTRATE_STDLIB_STAT_PREDICTION_PANEL_V1_AMENDMENT_20260927.md",
                        SELECTOR.relative_to(ROOT).as_posix(), FRAME.relative_to(ROOT).as_posix(),
                        SOURCE_NOTE.relative_to(ROOT).as_posix()],
        source_files=source_paths + [LOCK.relative_to(ROOT).as_posix()], data_files=data_paths,
        analysis_files=[ANALYZER.relative_to(ROOT).as_posix()], started_utc=started,
        exit_status=0 if all(checks.values()) else 1, stdout_stderr_capture=console,
        child_processes=[{"replicate": r.get("replicate"), "pid": r.get("pid"), "returncode": r.get("worker_returncode"),
                          "stderr": r.get("worker_stderr"), "structured_stdout_embedded_in_raw": True} for r in runs])
    report = {"schema_version": 1, "run_id": run_id, "locked_inputs": locked, "post_run_inputs": post,
              "run_manifest": manifest, "integrity_checks": checks, "integrity_pass": all(checks.values()),
              "runs": runs,
              "claim_boundary": "Targeted code-prediction intervention on the frozen CPython file-mode predicate panel; not blind transfer or general software accuracy."}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"report": OUT.relative_to(ROOT).as_posix(), "integrity_checks": checks}, indent=2))
    if not report["integrity_pass"]:
        raise SystemExit("panel integrity gates failed")


if __name__ == "__main__":
    main()

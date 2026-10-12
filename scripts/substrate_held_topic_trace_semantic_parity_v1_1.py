#!/usr/bin/env python3
"""Paired uninstrumented/fully traced held-topic replay."""
from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NATIVE_PACKAGE = os.environ.get("SUBSTRATE_NATIVE_PACKAGE")
NATIVE_PARENT = str(Path(NATIVE_PACKAGE).resolve().parent) if NATIVE_PACKAGE else None
sys.path[:0] = ([NATIVE_PARENT] if NATIVE_PARENT else []) + [
    str(ROOT), str(ROOT / "runners/dsl/python")]
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_HELD_TOPIC_TRACE_SEMANTIC_PARITY_V1_1_PREREG_20260928.md"
AMENDMENT = ROOT / "docs/research/engine_substrate/SUBSTRATE_HELD_TOPIC_TRACE_SEMANTIC_PARITY_V1_1_AMENDMENT_20260928.md"
ANALYZER = ROOT / "scripts/analyze_substrate_held_topic_trace_semantic_parity_v1_1.py"
TRACE_DRIVER = ROOT / "scripts/substrate_held_topic_structural_trace_capture_v1.py"
TRACE_ANALYSIS_HELPER = ROOT / "scripts/analyze_substrate_held_topic_structural_trace_capture_v1.py"
DRIVER = Path(__file__).resolve()
BASE_RUNNER = ROOT / "scripts/substrate_live_held_topic_evidence_v1_6.py"
LOCK = ROOT / "evaluation/substrate_capability/held_topic_trace_semantic_parity_v1_1_lock_20260928.json"
RAW = ROOT / "evaluation/reports/held_topic_trace_semantic_parity_v1_1_20260928.json"
RUNTIME_DATA = ROOT / "data"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def lock_inputs() -> dict:
    from substrate_rs import _native
    from scripts import substrate_live_held_topic_evidence_v1_6 as base
    fingerprint = base.fingerprint()
    return {
        "protocol_sha256": sha(PROTOCOL),
        "amendment_sha256": sha(AMENDMENT),
        "driver_sha256": sha(DRIVER),
        "analyzer_sha256": sha(ANALYZER),
        "trace_driver_sha256": sha(TRACE_DRIVER),
        "trace_analysis_helper_sha256": sha(TRACE_ANALYSIS_HELPER),
        "base_runner_sha256": sha(BASE_RUNNER),
        "base_fingerprint": fingerprint,
        "native_extension_sha256": sha(Path(_native.__file__).resolve()),
        "native_build_manifest_sha256": sha(
            ROOT / "runners/dsl/python/substrate_rs/_native.build.json"),
        "commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "python": sys.version,
        "platform": platform.platform(),
    }


def runtime_data_fingerprint() -> dict:
    """Content-hash non-code data used by live grounding/reference adapters."""
    digest = hashlib.sha256()
    count = total_bytes = 0
    for path in sorted(RUNTIME_DATA.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(ROOT).as_posix().encode()
        digest.update(len(rel).to_bytes(8, "big"))
        digest.update(rel)
        size = path.stat().st_size
        digest.update(size.to_bytes(8, "big"))
        with path.open("rb") as handle:
            while block := handle.read(1024 * 1024):
                digest.update(block)
        count += 1
        total_bytes += size
    return {"path": "data", "files": count, "bytes": total_bytes,
            "sha256": digest.hexdigest()}


def worker(replicate: int) -> dict:
    from scripts import substrate_live_held_topic_evidence_v1_6 as base
    from scripts import substrate_held_topic_structural_trace_capture_v1 as trace_driver

    expected = json.loads(LOCK.read_text())["source_lock"]
    started = lock_inputs()
    if started != expected:
        raise SystemExit("worker source/native inputs differ from parity lock")
    original_measured = base.measured
    original_projection = base.frame_projection
    arms = ("baseline", "trace") if replicate in (0, 2) else ("trace", "baseline")
    runs = {}
    try:
        for arm in arms:
            if arm == "trace":
                base.measured = trace_driver.instrumented_measured
                base._FRAME_PROJECTION_ORIGINAL = original_projection
                base.frame_projection = trace_driver.instrumented_frame_projection
            else:
                base.measured = original_measured
                base.frame_projection = original_projection
            runs[arm] = base.worker(replicate)
    finally:
        base.measured = original_measured
        base.frame_projection = original_projection
        if hasattr(base, "_FRAME_PROJECTION_ORIGINAL"):
            del base._FRAME_PROJECTION_ORIGINAL
    finished = lock_inputs()
    return {
        "replicate": replicate,
        "pid": os.getpid(),
        "arm_order": list(arms),
        "source_started": started,
        "source_finished": finished,
        "runs": runs,
    }


def main() -> None:
    if sys.argv[1:] == ["--lock"]:
        locked = {"source_lock": lock_inputs(),
                  "runtime_data": runtime_data_fingerprint()}
        LOCK.parent.mkdir(parents=True, exist_ok=True)
        LOCK.write_text(json.dumps(locked, indent=2, sort_keys=True) + "\n")
        print(LOCK)
        return
    if len(sys.argv) == 3 and sys.argv[1] == "--worker":
        print(json.dumps(worker(int(sys.argv[2])), sort_keys=True, default=str))
        return
    source_lock = lock_inputs()
    if not LOCK.is_file():
        raise SystemExit("missing or stale source/native parity lock")
    locked = json.loads(LOCK.read_text())
    if (locked.get("source_lock") != source_lock
            or locked.get("runtime_data") != runtime_data_fingerprint()):
        raise SystemExit("source/native or runtime-data parity lock is stale")
    env = dict(os.environ)
    env.setdefault("OZMA_NO_LLM", "1")
    env.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")
    paths = ([NATIVE_PARENT] if NATIVE_PARENT else []) + [
        str(ROOT), str(ROOT / "runners/dsl/python")]
    if env.get("PYTHONPATH"):
        paths.append(env["PYTHONPATH"])
    env["PYTHONPATH"] = os.pathsep.join(paths)
    runs = []
    for replicate in range(3):
        proc = subprocess.run(
            [sys.executable, str(DRIVER), "--worker", str(replicate)],
            cwd=ROOT, env=env, text=True, capture_output=True, check=True)
        runs.append(json.loads(proc.stdout))
    post_source = lock_inputs()
    post_data = runtime_data_fingerprint()
    post = {"source_lock": post_source, "runtime_data": post_data}
    RAW.parent.mkdir(parents=True, exist_ok=True)
    RAW.write_text(json.dumps({
        "schema_version": 1,
        "run_id": "held-topic-trace-semantic-parity-v1.1-20260928",
        "locked_inputs": locked,
        "post_run_inputs": post,
        "runs": runs,
    }, indent=2, sort_keys=True, default=str) + "\n")
    print(json.dumps({"workers": len(runs), "source_stable": post == locked,
                      "raw": str(RAW.relative_to(ROOT)),
                      "bytes": RAW.stat().st_size}, indent=2))
    if post != locked or len({run["pid"] for run in runs}) != 3:
        raise SystemExit("source lock or distinct-process gate failed")


if __name__ == "__main__":
    main()

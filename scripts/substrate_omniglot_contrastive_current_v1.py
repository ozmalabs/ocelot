#!/usr/bin/env python3
"""Source-locked current replay wrapper for the Omniglot run-37A benchmark."""
from __future__ import annotations

import hashlib
import importlib.metadata
import importlib.util
import json
import os
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_OMNIGLOT_CONTRASTIVE_CURRENT_V1_PREREG_20260928.md"
RUNNER = Path(__file__).resolve()
LOCK = ROOT / "evaluation/substrate_capability/omniglot_contrastive_current_v1_lock_20260928.json"
CAPTURE_DIR = ROOT / "evaluation/reports/omniglot_contrastive_current_v1_capture"
CAPTURE = CAPTURE_DIR / "capture.json"
BENCHMARK_PATH = ROOT / "scripts/jabberwock_omniglot_run37a_contrastive.py"
BASELINE_PATH = ROOT / "results/run26_checkpoints/eval_baseline.json"
STROKE_PATH = ROOT / "seeds/stroke_shapes.json"

SPEC = importlib.util.spec_from_file_location("omniglot_run37a_benchmark", BENCHMARK_PATH)
BENCH = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(BENCH)
BENCH.CKPT_DIR = str(CAPTURE_DIR)
BENCH.RUN26_DIR = str(BASELINE_PATH.parent)
BENCH.STROKE_SHAPES_PATH = str(STROKE_PATH)
CAPTURE_DIR.mkdir(parents=True, exist_ok=True)


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_record(path: Path) -> dict:
    data = path.read_bytes()
    return {"sha256": sha_bytes(data), "bytes": len(data)}


def tree_record(root: Path, suffixes: tuple[str, ...]) -> dict:
    h = hashlib.sha256()
    files = 0
    total_bytes = 0
    for path in sorted(p for p in root.rglob("*") if p.is_file() and p.suffix in suffixes):
        rel = path.relative_to(root).as_posix()
        data = path.read_bytes()
        h.update(rel.encode("utf-8")); h.update(b"\0")
        h.update(len(data).to_bytes(8, "big")); h.update(data)
        files += 1
        total_bytes += len(data)
    return {"path": str(root.relative_to(ROOT)), "suffixes": list(suffixes),
            "files": files, "bytes": total_bytes, "sha256": h.hexdigest()}


def package_version(name: str) -> str:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return "not-installed"


def input_lock() -> dict:
    native_so = ROOT / "runners/dsl/python/substrate_rs/_native.abi3.so"
    build_manifest = ROOT / "runners/dsl/python/substrate_rs/_native.build.json"
    rust_root = ROOT / "runners/dsl/src"
    py_facade = ROOT / "runners/dsl/python/substrate_rs"
    current = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True,
                             capture_output=True, check=True).stdout.strip()
    return {
        "protocol": file_record(PROTOCOL),
        "runner": file_record(RUNNER),
        "benchmark": file_record(BENCHMARK_PATH),
        "baseline_eval": file_record(BASELINE_PATH),
        "stroke_shapes": file_record(STROKE_PATH),
        "source_trees": {
            "domains_python": tree_record(ROOT / "domains", (".py",)),
            "scripts_python": tree_record(ROOT / "scripts", (".py",)),
            "rust_source": tree_record(rust_root, (".rs", ".toml", ".lock")),
            "python_facade": tree_record(py_facade, (".py", ".json")),
        },
        "native_extension": file_record(native_so),
        "native_build_manifest": file_record(build_manifest),
        "omniglot_data_tree": tree_record(ROOT / "data/omniglot", (".txt", ".png", ".jpg", ".jpeg", ".csv", ".json")),
        "git_head": current,
        "runtime": {
            "python": sys.version,
            "platform": platform.platform(),
            "machine": platform.machine(),
            "numpy": package_version("numpy"),
            "scipy": package_version("scipy"),
            "extension_build_manifest_sha256": file_record(build_manifest)["sha256"],
        },
        "benchmark_constants": {
            "way": BENCH.WAY,
            "episodes_per_alphabet": BENCH.EPISODES_PER_ALPHABET,
            "r_target": BENCH.R_TARGET,
            "n_test_alphabets": BENCH.N_TEST_ALPHABETS,
            "power_seed": BENCH.POWER_SEED,
            "baseline_full_dwell": {
                **BENCH.BASELINE_FULL_DWELL,
                "ci": list(BENCH.BASELINE_FULL_DWELL["ci"]),
            },
            "checkpoint_dir": str(CAPTURE_DIR.relative_to(ROOT)),
        },
    }


def read_json(path: Path, default=None):
    if not path.is_file():
        return default
    return json.loads(path.read_text())


def main() -> None:
    if sys.argv[1:] == ["--lock"]:
        if LOCK.exists() or CAPTURE.exists():
            raise SystemExit("refusing to overwrite source lock or final capture")
        lock = input_lock()
        LOCK.parent.mkdir(parents=True, exist_ok=True)
        LOCK.write_text(json.dumps(lock, indent=2, sort_keys=True) + "\n")
        print(LOCK.relative_to(ROOT))
        return
    if CAPTURE.exists():
        raise SystemExit("refusing to overwrite final capture")
    lock = read_json(LOCK)
    if not lock or input_lock() != lock:
        raise SystemExit("missing/stale input lock; do not resume under changed inputs")
    env = dict(os.environ)
    env.setdefault("OZMA_NO_LLM", "1")
    env.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")
    guard_path = CAPTURE_DIR / "guard.json"
    if not guard_path.exists():
        guard_rc = BENCH.stage_guard()
        if guard_rc != 0:
            raise SystemExit("preregistered baseline/top2 guard failed; stop before full evaluation")
    guard = read_json(guard_path, {})
    if not guard.get("guard_ok"):
        raise SystemExit("saved guard is not passing; refusing evaluation")
    eval_rc = BENCH.stage_eval()
    if eval_rc != 0:
        raise SystemExit(f"evaluation invocation failed with status {eval_rc}; retain checkpoints")
    evaluation = read_json(CAPTURE_DIR / "eval_run37a.json", {})
    if not evaluation.get("done") or len(evaluation.get("records", [])) != 400:
        print(json.dumps({"status": "partial", "blocks": evaluation.get("block_idx"),
                          "records": len(evaluation.get("records", [])),
                          "resume_command": f"python3 {RUNNER.relative_to(ROOT)}"}, indent=2))
        return
    report_rc = BENCH.stage_report()
    if report_rc != 0:
        raise SystemExit(f"benchmark report stage failed with status {report_rc}")
    after = input_lock()
    if after != lock:
        raise SystemExit("source/input drift detected after run; preserve checkpoints as censored")
    capture = {
        "schema_version": 1,
        "run_id": "omniglot-contrastive-current-source-v1-20260928",
        "captured_utc": datetime.now(timezone.utc).isoformat(),
        "capture_status": "complete",
        "locked_inputs": lock,
        "post_run_inputs": after,
        "guard": guard,
        "evaluation": evaluation,
        "benchmark_report": read_json(CAPTURE_DIR / "report.json", {}),
        "claim_boundary": "Current-source selected Omniglot 20-way one-shot evaluation; paired global and top-two contrastive predictions. Not a general perception or tractability estimate.",
    }
    CAPTURE.write_text(json.dumps(capture, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"capture": str(CAPTURE.relative_to(ROOT)), "status": "complete",
                      "records": len(evaluation["records"]), "stable_source_lock": True}, indent=2))


if __name__ == "__main__":
    main()

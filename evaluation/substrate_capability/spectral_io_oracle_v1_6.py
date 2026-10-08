#!/usr/bin/env python3
"""Current-source replay of the registered spectral primitive I/O panel."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import random
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNNER = Path(__file__).resolve()
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_SPECTRAL_IO_ORACLE_V1_6_PREREG_20261001.md"
LOCK = ROOT / "evaluation/substrate_capability/spectral_io_oracle_v1_6_lock_20261001.json"
RAW = ROOT / "evaluation/reports/spectral_io_oracle_v1_6_raw_20261001.json"
LEGACY_RUNNER = ROOT / "evaluation/substrate_capability/spectral_io_oracle_v1_5.py"
SOURCES = (
    "evaluation/substrate_capability/spectral_io_oracle_v1_6.py",
    "evaluation/substrate_capability/spectral_io_oracle_v1_5.py",
    "evaluation/substrate_capability/analyze_spectral_io_oracle_v1_6.py",
    "docs/research/engine_substrate/SUBSTRATE_SPECTRAL_IO_ORACLE_V1_6_PREREG_20261001.md",
    "domains/substrate_extension.py", "domains/reflective_faculty.py",
    "domains/self_verification.py", "domains/self_capability_collapse.py",
    "substrate/boot_core.py", "substrate/world_adapter.py", "substrate/graph.py",
    "substrate/seed_loader.py", "seeds/composer_faculty_pipeline.json",
    "seeds/shape_decode_loop.json", "runners/dsl/src/shape_decode.rs",
    "runners/dsl/src/term.rs", "runners/dsl/src/py.rs",
    "runners/dsl/src/substrate.rs", "runners/dsl/python/substrate_rs/__init__.py",
    "runners/dsl/python/substrate_rs/_native.abi3.so",
    "runners/dsl/python/substrate_rs/_native.build.json",
)
SEED = 20261016


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def source_hashes() -> dict[str, str]:
    return {rel: sha(ROOT / rel) for rel in SOURCES}


def payload() -> dict:
    import sys as _sys
    _sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
    import substrate_rs as srs
    from domains.engine_provenance import engine_provenance, rust_source_fingerprint
    return {
        "schema": "SpectralIOOracleV1_6Lock",
        "source_sha256": source_hashes(),
        "native_sha256": sha(Path(srs._native.__file__).resolve()),
        "engine_fingerprint": rust_source_fingerprint(str(ROOT)),
        "engine_provenance": engine_provenance(),
        "git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "protocol": {"panel": "v1.5 cases", "case_count": 12, "seed": SEED,
                     "construction_registry_families": ["spectral_value"],
                     "fresh_graph_per_case": True},
    }


def load_legacy():
    spec = importlib.util.spec_from_file_location("spectral_io_oracle_v1_5_frozen_helper", LEGACY_RUNNER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def main() -> None:
    current = payload()
    if sys.argv[1:] == ["--lock"]:
        if LOCK.exists() or RAW.exists():
            raise SystemExit("refusing to overwrite existing v1.6 lock or capture")
        LOCK.write_text(json.dumps(current, indent=2, sort_keys=True) + "\n")
        print(LOCK.relative_to(ROOT))
        return
    if not LOCK.is_file() or json.loads(LOCK.read_text()) != current:
        raise SystemExit("missing/stale v1.6 source lock")
    if RAW.exists():
        raise SystemExit(f"refusing to overwrite {RAW}")
    helper = load_legacy()
    schedule = [(arm, case) for arm in helper.ARMS for case in helper.CASES]
    random.Random(SEED).shuffle(schedule)
    started = time.perf_counter()
    rows = []
    for index, (arm, case) in enumerate(schedule, 1):
        row = helper.run_one(arm, case)
        row["panel_index"] = index
        rows.append(row)
        print(f"{index}/12 {arm} {case['id']} {row['result'].get('outcome')}", flush=True)
    post = payload()
    if post != current:
        raise SystemExit("source lock changed during run")
    capture = {"schema": "SpectralIOOracleV1_6Capture", "lock": current,
               "post_lock": post, "schedule": [{"arm": a, "case": c} for a, c in schedule],
               "cases": rows, "elapsed_seconds": time.perf_counter() - started}
    RAW.write_text(json.dumps(capture, indent=2, sort_keys=True, default=str) + "\n")
    print(json.dumps({"capture": RAW.relative_to(ROOT).as_posix(), "cases": len(rows)}))


if __name__ == "__main__":
    main()

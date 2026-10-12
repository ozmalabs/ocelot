#!/usr/bin/env python3
"""Run and freeze the Rust finite differential oracle before native capture."""
from __future__ import annotations
import hashlib
import json
import os
import re
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DSL = ROOT / "runners/dsl"
OUT = ROOT / "evaluation/reports/geninfer_exact_linear_prefilter_oracle_v1_2_20261006.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_paths() -> list[Path]:
    return [Path(__file__).resolve(), ROOT / "runners/dsl/Cargo.toml", ROOT / "runners/dsl/Cargo.lock",
            ROOT / "runners/dsl/src/shape_decode.rs", ROOT / "runners/dsl/src/scale_audit.rs",
            ROOT / "runners/dsl/src/term.rs", ROOT / "runners/dsl/src/jsonio.rs", ROOT / "runners/dsl/src/reflect.rs",
            ROOT / "seeds/shape_decode_loop.json",
            ROOT / "docs/research/engine_substrate/SUBSTRATE_GENINFER_EXACT_LINEAR_PREFILTER_V1_PREREG_20261006.md",
            ROOT / "docs/research/engine_substrate/SUBSTRATE_GENINFER_EXACT_LINEAR_PREFILTER_V1_1_AMENDMENT_20261006.md",
            ROOT / "docs/research/engine_substrate/SUBSTRATE_GENINFER_EXACT_LINEAR_PREFILTER_V1_2_AMENDMENT_20261006.md",
            ROOT / "docs/research/engine_substrate/SUBSTRATE_GENINFER_EXACT_LINEAR_PREFILTER_V1_3_AMENDMENT_20261006.md"]


def main() -> int:
    if OUT.exists():
        raise SystemExit(f"refusing to overwrite {OUT}")
    sources_before = {str(p.relative_to(ROOT)): sha(p) for p in source_paths()}
    env = os.environ.copy()
    py_lib = "/home/linuxbrew/.linuxbrew/opt/python@3.13/lib"
    env["LD_LIBRARY_PATH"] = py_lib + (":" + env["LD_LIBRARY_PATH"] if env.get("LD_LIBRARY_PATH") else "")
    env["RUSTFLAGS"] = f"-C link-arg=-L{py_lib} -C link-arg=-lpython3.13"
    command = ["cargo", "test", "--lib", "shape_decode::tests::exact_linear_prefilter",
               "--features", "geninfer_linear_exact_prefilter", "--", "--nocapture"]
    started = time.monotonic()
    proc = subprocess.run(command, cwd=DSL, env=env, text=True, capture_output=True, timeout=240, check=False)
    elapsed = time.monotonic() - started
    combined = proc.stdout + "\n" + proc.stderr
    match = re.search(r"GENINFER_PREFILTER_ENUMERATOR_ORACLE cases=(\d+) fnv1a64=([0-9a-f]{16})", combined)
    sources_after = {str(p.relative_to(ROOT)): sha(p) for p in source_paths()}
    report = {"schema": "GenInferExactLinearPrefilterEnumeratorOracleV1",
              "status": "pass" if proc.returncode == 0 and match and sources_before == sources_after else "fail",
              "command": ["cargo", *command[1:]], "cwd": str(DSL), "rustc": subprocess.run(["rustc", "--version"], capture_output=True, text=True, check=True).stdout.strip(),
              "source_sha256": sources_before, "source_stable": sources_before == sources_after,
              "return_code": proc.returncode, "elapsed_seconds": elapsed,
              "case_count": int(match.group(1)) if match else None,
              "oracle_fnv1a64": match.group(2) if match else None,
              "stdout_tail": proc.stdout[-5000:], "stderr_tail": proc.stderr[-5000:],
              "finite_scope": "Four full-rank point sets x 625 integer 2x2 matrices in [-2,2]; exact selected matrix, residual count/transforms compared against bounded historical enumerator."}
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": OUT.relative_to(ROOT).as_posix(), "status": report["status"],
                      "case_count": report["case_count"], "oracle_fnv1a64": report["oracle_fnv1a64"],
                      "elapsed_seconds": elapsed}, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Hash-locked direct Rust diagnostic for parse_rule_json_pub rollback."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CRATE = ROOT / "runners/dsl"
PREREG = ROOT / "docs/research/engine_substrate/SUBSTRATE_PARSE_RULE_JSON_PUB_ROLLBACK_PREREG_20260925.md"
LOCK = ROOT / "evaluation/substrate_capability/parse_rule_json_pub_rollback_lock_20260925.json"
EXAMPLE = CRATE / "examples/parse_rule_json_rollback_probe.rs"
OUTPUT = ROOT / "evaluation/reports/substrate_parse_rule_json_pub_rollback_20260925.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def locked_inputs() -> dict[str, Path]:
    return {
        "preregistration_sha256": PREREG,
        "runner_sha256": Path(__file__).resolve(),
        "example_sha256": EXAMPLE,
        "crate_manifest_sha256": CRATE / "Cargo.toml",
        "crate_lock_sha256": CRATE / "Cargo.lock",
        "lib_source_sha256": CRATE / "src/lib.rs",
        "parser_source_sha256": CRATE / "src/py.rs",
        "term_source_sha256": CRATE / "src/term.rs",
        "json_decoder_source_sha256": CRATE / "src/jsonio.rs",
        "interner_source_sha256": CRATE / "src/sym.rs",
    }


def main() -> int:
    frozen = json.loads(LOCK.read_text())
    inputs = locked_inputs()
    actual = {key: sha(path) for key, path in inputs.items()}
    if actual != frozen:
        raise SystemExit("parse_rule_json_pub rollback lock mismatch")
    env = os.environ.copy()
    env["CARGO_TERM_COLOR"] = "never"
    proc = subprocess.run(
        ["cargo", "run", "--quiet", "--locked", "--example", "parse_rule_json_rollback_probe"],
        cwd=CRATE, env=env, text=True, capture_output=True, check=True,
    )
    payload = json.loads(proc.stdout.strip().splitlines()[-1])
    payload["provenance"] = {
        "locked_inputs": actual,
        "lock_sha256": sha(LOCK),
        "rustc_version": subprocess.check_output(["rustc", "--version"], text=True).strip(),
        "cargo_version": subprocess.check_output(["cargo", "--version"], text=True).strip(),
        "git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
    }
    payload["build_stderr_sha256"] = hashlib.sha256(proc.stderr.encode()).hexdigest()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"all_gates_pass": payload["all_gates_pass"],
                      "failure_attempts": payload["failure_attempts"],
                      "output": str(OUTPUT)}))
    return 0 if payload["all_gates_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())

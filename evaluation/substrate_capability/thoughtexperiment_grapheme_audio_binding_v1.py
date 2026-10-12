#!/usr/bin/env python3
"""Replay the repository's real Omniglot↔FSDD co-presentation task reproducibly."""
from __future__ import annotations

import contextlib
import hashlib
import io
import json
import os
import platform
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FSDD = ROOT / "data/fsdd-current/free-spoken-digit-dataset-26eb9aaf76e81b692f806f9140c2d2777410d7a1/recordings"
OUT = ROOT / "evaluation/reports/thoughtexperiment_grapheme_audio_binding_v1_raw_20261001.json"
PROTOCOL = ROOT / "docs/research/engine_substrate/THOUGHTEXPERIMENT_GRAPHEME_AUDIO_BINDING_V1_PREREG_20261001.md"
SCRIPT = ROOT / "scripts/jabberwock_cross_modal.py"
WORKERS = 3
N_TEST = 40
SOURCES = (
    "docs/research/engine_substrate/THOUGHTEXPERIMENT_GRAPHEME_AUDIO_BINDING_V1_PREREG_20261001.md",
    "evaluation/substrate_capability/thoughtexperiment_grapheme_audio_binding_v1.py",
    "scripts/jabberwock_cross_modal.py", "seeds/cross_modal.json",
    "domains/omniglot_world.py", "domains/glyph_motor_world.py",
    "domains/recognition_graph.py", "domains/reading_runners.py",
    "runners/dsl/python/substrate_rs/_native.abi3.so",
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def file_digest(paths: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in sorted(paths):
        digest.update(str(path.relative_to(ROOT)).encode())
        digest.update(bytes.fromhex(sha(path)))
    return digest.hexdigest()


def data_inventory() -> dict:
    sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
    from domains import omniglot_world as ow
    chars_by_alpha = {a: ow.characters(a, "evaluation")
                      for a in ow.alphabets("evaluation")}
    chars_by_alpha = {a: cs for a, cs in chars_by_alpha.items() if len(cs) >= 10}
    alphabet = sorted(chars_by_alpha)[0]
    omni_files = [Path(p) for char in chars_by_alpha[alphabet]
                  for p in ow.drawings(char)]
    fsdd_files = sorted(FSDD.glob("*.wav"))
    return {"omniglot_alphabet": alphabet,
        "omniglot_character_count": len(chars_by_alpha[alphabet]),
        "omniglot_file_count": len(omni_files),
        "omniglot_digest": file_digest(omni_files),
        "fsdd_release": str(FSDD.relative_to(ROOT)),
        "fsdd_file_count": len(fsdd_files), "fsdd_digest": file_digest(fsdd_files)}


def fingerprint() -> dict:
    return {"sources": {p: sha(ROOT / p) for p in SOURCES},
            "data": data_inventory()}


def worker() -> dict:
    sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
    from domains import omniglot_world as ow
    from scripts import jabberwock_cross_modal as task

    if not ow.have_data("evaluation") or not FSDD.is_dir():
        raise RuntimeError("required local Omniglot/FSDD data is unavailable")
    task.FSDD = str(FSDD)
    old_argv = sys.argv
    sys.argv = [str(SCRIPT), str(N_TEST)]
    output = io.StringIO()
    try:
        with contextlib.redirect_stdout(output):
            code = task.main()
    finally:
        sys.argv = old_argv
    stdout = output.getvalue()
    if code != 0:
        raise RuntimeError(f"cross-modal task exited {code}: {stdout}")
    read_match = re.search(r"READ ALOUD[^\n]*?([0-9.]+)%\s+\((\d+) held-out graphemes\)", stdout)
    write_match = re.search(r"DICTATION[^\n]*?([0-9.]+)%\s+\((\d+) held-out phonemes\)", stdout)
    bound_match = re.search(r"taught (\d+)/10 grapheme", stdout)
    if not read_match or not write_match or not bound_match:
        raise RuntimeError(f"could not parse complete task output: {stdout}")
    read_total, write_total = int(read_match.group(2)), int(write_match.group(2))
    read_acc, write_acc = float(read_match.group(1)) / 100, float(write_match.group(1)) / 100
    return {"pid": os.getpid(), "exit_code": code,
        "binding_edges": int(bound_match.group(1)),
        "read_aloud": {"accuracy": read_acc,
            "successes": round(read_acc * read_total), "queries": read_total},
        "dictation": {"accuracy": write_acc,
            "successes": round(write_acc * write_total), "queries": write_total},
        "stdout": stdout}


def main() -> None:
    if sys.argv[1:] == ["--worker"]:
        print(json.dumps(worker(), sort_keys=True))
        return
    before = fingerprint()
    env = {**os.environ, "PYTHONPATH": f"{ROOT / 'runners/dsl/python'}:{ROOT}"}
    rows = []
    for _ in range(WORKERS):
        proc = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--worker"],
            cwd=ROOT, env=env, check=True, text=True, capture_output=True)
        rows.append(json.loads(proc.stdout))
    after = fingerprint()
    result = {"protocol": PROTOCOL.name,
        "captured_utc": datetime.now(timezone.utc).isoformat(),
        "platform": platform.platform(), "source_before": before,
        "source_after": after, "source_and_data_stable": before == after,
        "workers": rows,
        "gates": {
            "three_fresh_pids": len({r["pid"] for r in rows}) == WORKERS,
            "ten_bindings_each": all(r["binding_edges"] == 10 for r in rows),
            "forty_queries_per_direction": all(
                r["read_aloud"]["queries"] == N_TEST and
                r["dictation"]["queries"] == N_TEST for r in rows),
            "repeatable_outcomes": len({(r["read_aloud"]["successes"],
                r["dictation"]["successes"]) for r in rows}) == 1,
            "source_and_data_stable": before == after}}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(OUT.relative_to(ROOT)), "gates": result["gates"],
        "read_aloud": rows[0]["read_aloud"], "dictation": rows[0]["dictation"],
        "binding_edges": rows[0]["binding_edges"], "workers": WORKERS,
        "fsdd_files": before["data"]["fsdd_file_count"]}, sort_keys=True))
    if not all(result["gates"].values()):
        raise SystemExit("grapheme-audio binding panel gate failed")


if __name__ == "__main__":
    main()

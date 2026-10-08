#!/usr/bin/env python3
"""Paired correct-vs-shifted co-presentation control on Omniglot/FSDD."""
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
OUT = ROOT / "evaluation/reports/thoughtexperiment_grapheme_audio_permuted_binding_v1_raw_20261001.json"
PROTOCOL = ROOT / "docs/research/engine_substrate/THOUGHTEXPERIMENT_GRAPHEME_AUDIO_PERMUTED_BINDING_V1_PREREG_20261001.md"
SCRIPT = ROOT / "scripts/jabberwock_cross_modal.py"
WORKERS = 3
N_TEST = 40
SHIFTS = (0, 1)
SOURCES = (
    "docs/research/engine_substrate/THOUGHTEXPERIMENT_GRAPHEME_AUDIO_PERMUTED_BINDING_V1_PREREG_20261001.md",
    "evaluation/substrate_capability/thoughtexperiment_grapheme_audio_permuted_binding_v1.py",
    "docs/research/engine_substrate/THOUGHTEXPERIMENT_GRAPHEME_AUDIO_BINDING_V1_PREREG_20261001.md",
    "evaluation/substrate_capability/thoughtexperiment_grapheme_audio_binding_v1.py",
    "scripts/jabberwock_cross_modal.py", "seeds/cross_modal.json",
    "domains/omniglot_world.py", "domains/glyph_motor_world.py",
    "domains/recognition_graph.py", "runners/dsl/python/substrate_rs/_native.abi3.so",
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
    by_alpha = {a: ow.characters(a, "evaluation") for a in ow.alphabets("evaluation")}
    by_alpha = {a: cs for a, cs in by_alpha.items() if len(cs) >= 10}
    alphabet = sorted(by_alpha)[0]
    omni = [Path(p) for char in by_alpha[alphabet] for p in ow.drawings(char)]
    audio = sorted(FSDD.glob("*.wav"))
    return {"alphabet": alphabet, "omniglot_count": len(omni),
        "omniglot_digest": file_digest(omni), "fsdd_count": len(audio),
        "fsdd_digest": file_digest(audio)}


def fingerprint() -> dict:
    return {"sources": {p: sha(ROOT / p) for p in SOURCES}, "data": data_inventory()}


def run_arm(task, shift: int) -> dict:
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        code = task.main(n_test=N_TEST, pair_shift=shift)
    stdout = output.getvalue()
    if code != 0:
        raise RuntimeError(f"task arm shift={shift} returned {code}: {stdout}")
    read = re.search(r"READ ALOUD[^\n]*?([0-9.]+)%\s+\((\d+) held-out graphemes\)", stdout)
    write = re.search(r"DICTATION[^\n]*?([0-9.]+)%\s+\((\d+) held-out phonemes\)", stdout)
    bound = re.search(r"taught (\d+)/10 grapheme", stdout)
    if not read or not write or not bound:
        raise RuntimeError(f"could not parse shift={shift} output: {stdout}")
    read_n, write_n = int(read.group(2)), int(write.group(2))
    read_acc, write_acc = float(read.group(1)) / 100, float(write.group(1)) / 100
    return {"pair_shift": shift, "binding_edges": int(bound.group(1)),
        "read_aloud": {"accuracy": read_acc,
            "successes": round(read_acc * read_n), "queries": read_n},
        "dictation": {"accuracy": write_acc,
            "successes": round(write_acc * write_n), "queries": write_n},
        "stdout": stdout}


def worker() -> dict:
    sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
    from scripts import jabberwock_cross_modal as task
    task.FSDD = str(FSDD)
    # Each call creates a fresh Substrate and resets its task-local random generators.
    arms = {str(shift): run_arm(task, shift) for shift in SHIFTS}
    return {"pid": os.getpid(), "arms": arms,
        "paired_mean_difference": sum(
            arms["0"][metric]["accuracy"] - arms["1"][metric]["accuracy"]
            for metric in ("read_aloud", "dictation")) / 2}


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
    repeatable = all(len({(r["arms"][str(shift)]["read_aloud"]["successes"],
                           r["arms"][str(shift)]["dictation"]["successes"])
                          for r in rows}) == 1 for shift in SHIFTS)
    result = {"protocol": PROTOCOL.name,
        "captured_utc": datetime.now(timezone.utc).isoformat(),
        "platform": platform.platform(), "source_before": before,
        "source_after": after, "source_and_data_stable": before == after,
        "workers": rows,
        "gates": {
            "three_fresh_pids": len({r["pid"] for r in rows}) == WORKERS,
            "ten_bindings_and_40_queries_per_direction": all(
                arm["binding_edges"] == 10 and
                arm["read_aloud"]["queries"] == N_TEST and
                arm["dictation"]["queries"] == N_TEST
                for r in rows for arm in r["arms"].values()),
            "repeatable_arm_outcomes": repeatable,
            "correct_mapping_beats_shift_on_mean": all(
                r["paired_mean_difference"] > 0 for r in rows),
            "source_and_data_stable": before == after}}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(OUT.relative_to(ROOT)), "gates": result["gates"],
        "correct": rows[0]["arms"]["0"], "permuted": rows[0]["arms"]["1"],
        "mean_difference": rows[0]["paired_mean_difference"],
        "workers": WORKERS}, sort_keys=True))
    if not all(result["gates"].values()):
        raise SystemExit("permuted-binding control gate failed")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Measure the existing substrate-backed Omniglot grapheme recognition runner."""
from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "evaluation/reports/thoughtexperiment_omniglot_graph_recognition_v1_raw_20261001.json"
PROTOCOL = ROOT / "docs/research/engine_substrate/THOUGHTEXPERIMENT_OMNIGLOT_GRAPH_RECOGNITION_V1_PREREG_20261001.md"
WORKERS = 3
EPISODES = 8
WAY = 10
SOURCES = (
    "docs/research/engine_substrate/THOUGHTEXPERIMENT_OMNIGLOT_GRAPH_RECOGNITION_V1_PREREG_20261001.md",
    "evaluation/substrate_capability/thoughtexperiment_omniglot_graph_recognition_v1.py",
    "domains/reading_runners.py", "domains/recognition_graph.py",
    "domains/omniglot_world.py", "domains/glyph_motor_world.py",
    "runners/dsl/python/substrate_rs/_native.abi3.so",
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def data_inventory() -> dict:
    sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
    from domains import omniglot_world as ow
    alphabets = [a for a in ow.alphabets("evaluation")
                 if len(ow.characters(a, "evaluation")) >= 12]
    alphabet = sorted(alphabets)[0]
    chars = ow.characters(alphabet, "evaluation")
    files = sorted(Path(p) for char in chars for p in ow.drawings(char))
    digest = hashlib.sha256()
    for path in files:
        digest.update(str(path.relative_to(ROOT)).encode())
        digest.update(bytes.fromhex(sha(path)))
    return {"alphabet": alphabet, "character_count": len(chars),
            "drawing_file_count": len(files), "drawing_digest": digest.hexdigest()}


def fingerprint() -> dict:
    return {"files": {p: sha(ROOT / p) for p in SOURCES},
            "data": data_inventory()}


def worker() -> dict:
    from domains import omniglot_world as ow
    from domains.reading_runners import run_grapheme

    eligible = [a for a in ow.alphabets("evaluation")
                if len(ow.characters(a, "evaluation")) >= WAY + 2]
    alphabet = sorted(eligible)[0]
    chars = ow.characters(alphabet, "evaluation")
    all_drawings = [ow.drawings(char) for char in chars]
    if any(len(rows) < 12 for rows in all_drawings):
        raise RuntimeError("selected alphabet includes a character with fewer than 12 drawings")
    accuracy = run_grapheme(None, {}, {}, episodes=EPISODES, way=WAY)
    return {"pid": os.getpid(), "alphabet": alphabet,
        "character_count": len(chars), "queries": EPISODES * WAY,
        "episodes": EPISODES, "way": WAY, "accuracy": accuracy}


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
        "source_after": after, "source_stable": before == after,
        "workers": rows,
        "gates": {
            "three_fresh_pids": len({r["pid"] for r in rows}) == WORKERS,
            "stable_corpus_identity": len({(r["alphabet"], r["character_count"],
                r["queries"], r["episodes"], r["way"]) for r in rows}) == 1,
            "exact_repeatability": len({r["accuracy"] for r in rows}) == 1,
            "expected_query_count": all(r["queries"] == EPISODES * WAY for r in rows),
            "source_and_data_stable": before == after}}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(OUT.relative_to(ROOT)),
        "gates": result["gates"], "accuracy": rows[0]["accuracy"],
        "queries_per_worker": rows[0]["queries"],
        "alphabet": rows[0]["alphabet"], "workers": WORKERS}, sort_keys=True))
    if not all(result["gates"].values()):
        raise SystemExit("Omniglot grapheme recognition gate failed")


if __name__ == "__main__":
    main()

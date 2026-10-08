#!/usr/bin/env python3
"""Offline fresh-process repeatability probe for symbolic UseTool handlers."""
from __future__ import annotations

import argparse
import hashlib
import json
import socket
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "evaluation/reports/substrate_use_tool_handler_resource_probe_v1_2_20260928.json"
LOCK = ROOT / "evaluation/substrate_capability/use_tool_handler_resource_probe_v1_2_lock_20260928.json"
SOURCES = [
    "domains/symbolic_perception.py", "domains/dict_teacher.py",
    "domains/conceptnet_reference.py", "domains/wiktionary_reference.py",
    "domains/reference_slab.py",
]
SLABS = ["conceptnet_en", "wikt_antonym_en", "wikt_figsense_en", "wikt_pos_en"]
CASES = {
    "wn_antonym": ["hot", "cold"], "wikt_antonym": ["hot", "cold"],
    "cn_antonym": ["hot", "cold"], "derive_opposes": ["deafening", "silence"],
    "wn_animate": ["dog"], "wn_verb_agentive": ["whisper"],
    "text_valence": ["wonderful terrible"], "wikt_metonymic": ["crown", "monarch"],
    "cn_contiguity": ["crown", "monarch"], "shape_cross_domain": ["crown", "monarch"],
    "wikt_idiomatic": ["kick the bucket"], "is_extreme": ["million"],
    "is_minimizer": ["barely"], "is_intensifier_spike": ["fantastic"],
    "text_severe": ["catastrophic"],
}


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def snapshot() -> dict:
    files = {}
    for rel in SOURCES:
        p = ROOT / rel
        files[rel] = {"exists": p.exists(), "sha256": digest(p)}
    for name in SLABS:
        for ext in ("keys", "vals"):
            rel = f"data/slabs/{name}.{ext}"
            p = ROOT / rel
            files[rel] = {"exists": p.exists(), "size": p.stat().st_size if p.exists() else None,
                          "sha256": digest(p) if p.exists() else None}
    import nltk
    for corpus in ("wordnet", "omw-1.4", "opinion_lexicon", "sentiwordnet"):
        candidates = []
        for suffix in ("", ".zip"):
            try:
                p = Path(str(nltk.data.find(f"corpora/{corpus}{suffix}")))
                candidates.append({"path": str(p), "size": p.stat().st_size if p.is_file() else None,
                                   "sha256": digest(p) if p.is_file() else None})
            except LookupError:
                pass
        files[f"nltk:{corpus}"] = {"present": bool(candidates), "resolved": candidates}
    return files


def worker() -> dict:
    sys.path.insert(0, str(ROOT))
    attempts = []
    import nltk

    def blocked_download(*args, **kwargs):
        attempts.append({"kind": "nltk.download", "args": list(args), "kwargs": kwargs})
        raise RuntimeError("network acquisition disabled by probe")

    nltk.download = blocked_download
    import domains.conceptnet_reference as cn

    def blocked_build(*args, **kwargs):
        attempts.append({"kind": "conceptnet.build", "args": list(args), "kwargs": kwargs})
        raise RuntimeError("resource build/acquisition disabled by probe")

    cn.build_conceptnet_slab = blocked_build
    def blocked_connect(*args, **kwargs):
        attempts.append({"kind": "socket.connect"})
        raise RuntimeError("network connection disabled by probe")
    socket.socket.connect = blocked_connect

    import domains.symbolic_perception as sp
    rows = {}
    for name, fn in sp.HANDLERS.items():
        args = CASES[name]
        pair = []
        for _ in range(2):
            try:
                pair.append({"status": "ok", "value": fn(*args)})
            except Exception as exc:
                pair.append({"status": "error", "type": type(exc).__name__, "message": str(exc)[:300]})
        rows[name] = {"args": args, "calls": pair}
    return {"pid": __import__("os").getpid(), "handlers": rows, "acquisition_attempts": attempts}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--worker", action="store_true")
    args = ap.parse_args()
    if args.worker:
        print(json.dumps(worker(), sort_keys=True))
        return
    if RAW.exists() or LOCK.exists():
        raise SystemExit("refusing to overwrite existing source lock or raw capture")
    before = snapshot()
    lock = {"probe": "UseTool handler resource probe v1", "source_resource_snapshot": before,
            "cases": CASES, "workers": 3}
    LOCK.parent.mkdir(parents=True, exist_ok=True)
    LOCK.write_text(json.dumps(lock, indent=2, sort_keys=True) + "\n")
    workers = []
    for i in range(3):
        cp = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--worker"],
                            cwd=ROOT, text=True, capture_output=True, check=False)
        if cp.returncode:
            workers.append({"worker": i, "exit_code": cp.returncode, "stderr": cp.stderr[-2000:]})
        else:
            workers.append({"worker": i, **json.loads(cp.stdout)})
    after = snapshot()
    raw = {"lock": lock, "workers": workers, "snapshot_after": after,
           "source_resource_stable": before == after}
    RAW.parent.mkdir(parents=True, exist_ok=True)
    RAW.write_text(json.dumps(raw, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"workers": len(workers), "stable": before == after,
                      "attempts_per_worker": [len(w.get("acquisition_attempts", [])) for w in workers],
                      "raw": str(RAW.relative_to(ROOT)), "lock": str(LOCK.relative_to(ROOT))}, indent=2))


if __name__ == "__main__":
    main()

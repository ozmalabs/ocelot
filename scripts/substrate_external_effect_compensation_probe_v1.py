#!/usr/bin/env python3
"""Positive-to-negative external predicate transition and explicit compensation probe."""
from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_EXTERNAL_EFFECT_COMPENSATION_PROBE_V1_PREREG_20260928.md"
ANALYZER = ROOT / "scripts/analyze_external_effect_compensation_probe_v1.py"
LOCK = ROOT / "evaluation/substrate_capability/external_effect_compensation_probe_v1_lock_20260928.json"
RAW = ROOT / "evaluation/reports/external_effect_compensation_probe_v1_20260928.json"
SOURCE_PATHS = (
    "runners/dsl/src/term.rs", "runners/dsl/src/rewrite.rs", "runners/dsl/src/py.rs",
    "runners/dsl/python/substrate_rs/__init__.py",
    "scripts/substrate_external_effect_compensation_probe_v1.py",
    "scripts/analyze_external_effect_compensation_probe_v1.py",
    "docs/research/engine_substrate/SUBSTRATE_EXTERNAL_EFFECT_COMPENSATION_PROBE_V1_PREREG_20260928.md",
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def lock_inputs() -> dict:
    from substrate_rs import _native
    ext = Path(_native.__file__).resolve()
    return {
        "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "source_sha256": {name: sha(ROOT / name) for name in SOURCE_PATHS},
        "native_extension_path": str(ext), "native_extension_sha256": sha(ext),
        "native_build_manifest_sha256": sha(ROOT / "runners/dsl/python/substrate_rs/_native.build.json"),
    }


def arm(mode: str) -> dict:
    from substrate_rs import Lit, Substrate, Term, _native
    _native.clear_tool_handlers()
    calls = []
    with tempfile.TemporaryDirectory(prefix="external-effect-compensation-") as td:
        root = Path(td)
        for rev, value in (("r0", "0"), ("r1", "1"), ("r2", "0")):
            (root / f"{rev}.txt").write_text(value, encoding="utf-8")

        def handler(revision):
            rev = str(revision)
            value = (root / f"{rev}.txt").read_text(encoding="utf-8")
            calls.append({"revision": rev, "value": value})
            return value

        _native.register_tool_handler("resource_value", handler)
        sub = Substrate()
        inner = sub._inner
        x = inner.add_node("ReplayProbe", {"resource_rev": "r0"})
        y = inner.add_node("ReplayProbe", {})
        inner.add_edge_unchecked(x, "trigger", y, {})
        tool = Term("UseTool", tool="resource_value", args=[
            Term("Attr", node=Term("Var", name="x"), key="resource_rev")
        ])
        positive = Term("Eq", a=tool, b=Lit("1"))
        negative = Term("Eq", a=tool, b=Lit("0"))
        if mode == "retractable_edge":
            positive_effect = [["add_edge", "x", "accepted", "y", {}]]
            negative_effect = [["del_edge", "x", "accepted", "y"]]
        else:
            positive_effect = [["set_attr_if_different", "y", "accepted", 1]]
            negative_effect = [["set_attr_if_different", "y", "accepted", 0]]
        inner.add_rule({"name": "resource_positive", "match": [["x", "trigger", "y"]],
                        "where": positive.to_dict(), "effects": positive_effect})
        if mode != "sticky_attr":
            inner.add_rule({"name": "resource_compensate", "match": [["x", "trigger", "y"]],
                            "where": negative.to_dict(), "effects": negative_effect})

        def markers() -> dict:
            graph = inner.graph_to_dict()
            attrs = {int(n["id"]): n.get("attrs", {}) for n in graph.get("nodes", [])}
            accepted_edges = [e for e in graph.get("edges", []) if e["type"] == "accepted" and e["src"] == x.value and e["tgt"] == y.value]
            return {"accepted_attr": attrs.get(y.value, {}).get("accepted"),
                    "accepted_edge": bool(accepted_edges)}

        phases = []

        def settle(name: str, rev: str):
            calls.clear()
            before = int(_native.tool_fire_count())
            progress = int(inner.run_rules(100))
            fire_delta = int(_native.tool_fire_count()) - before
            phases.append({"phase": name, "revision": rev,
                           "resource_value": (root / f"{rev}.txt").read_text(encoding="utf-8"),
                           "resource_sha256": sha(root / f"{rev}.txt"),
                           "progress": progress, "callback_count": len(calls),
                           "native_fire_delta": fire_delta, "callback_log": list(calls),
                           "markers": markers()})

        settle("initial_negative_r0", "r0")
        inner.set_attr(x, "resource_rev", "r1")
        settle("positive_revision_r1", "r1")
        (root / "r1.txt").write_text("0", encoding="utf-8")
        settle("external_only_negative_flip", "r1")
        inner.set_attr(x, "resource_rev", "r2")
        settle("negative_revision_r2", "r2")
        _native.clear_tool_handlers()
        return {"mode": mode, "phases": phases}


def worker(worker_id: int) -> dict:
    started = lock_inputs()
    if json.loads(LOCK.read_text())["locked_inputs"] != started:
        raise RuntimeError("worker source/native lock mismatch")
    return {"worker_id": worker_id, "pid": os.getpid(), "python": sys.version,
            "platform": platform.platform(), "started_inputs": started,
            "arms": [arm(mode) for mode in ("sticky_attr", "compensating_attr", "retractable_edge")]}


def main() -> None:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--worker", type=int)
    ap.add_argument("--write-lock", action="store_true")
    args = ap.parse_args()
    if args.write_lock:
        if LOCK.exists():
            raise SystemExit(f"refusing to overwrite lock {LOCK}")
        LOCK.parent.mkdir(parents=True, exist_ok=True)
        LOCK.write_text(json.dumps({"lock_id": "external_effect_compensation_probe_v1_20260928",
                                    "locked_inputs": lock_inputs(), "workers": 3}, indent=2, sort_keys=True) + "\n")
        print(str(LOCK.relative_to(ROOT))); return
    if args.worker is not None:
        print(json.dumps(worker(args.worker), sort_keys=True)); return
    if RAW.exists():
        raise SystemExit(f"refusing to overwrite capture {RAW}")
    lock = json.loads(LOCK.read_text())
    if lock_inputs() != lock["locked_inputs"]:
        raise SystemExit("source/native lock mismatch")
    runs = []
    for worker_id in range(1, 4):
        argv = [sys.executable, str(Path(__file__).resolve()), "--worker", str(worker_id)]
        proc = subprocess.run(argv, cwd=ROOT, text=True, capture_output=True)
        if proc.returncode:
            raise SystemExit(f"worker {worker_id} failed: {proc.stderr[-2000:]}")
        runs.append(json.loads(proc.stdout.strip().splitlines()[-1]))
    payload = {"run_id": "external_effect_compensation_probe_v1_20260928",
               "protocol_sha256": sha(PROTOCOL), "analyzer_sha256": sha(ANALYZER),
               "lock_sha256": sha(LOCK), "locked_inputs": lock["locked_inputs"],
               "runs": runs,
               "claim_boundary": "Three fresh workers, three explicit effect strategies and a four-phase external-resource transition. Measures persistence and explicit compensation for one rule shape. No automatic truth maintenance or general rollback claim."}
    RAW.parent.mkdir(parents=True, exist_ok=True)
    with RAW.open("x", encoding="utf-8") as f:
        f.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"workers": len(runs), "arms_per_worker": len(runs[0]["arms"]), "raw": str(RAW.relative_to(ROOT))}))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Source-locked audit of strict code-write adoption entrypoints."""
from __future__ import annotations
import copy
import hashlib
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
RUNNER = Path(__file__).resolve()
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_ADEQUACY_ADOPTION_SURFACE_V1_PREREG_20261002.md"
LOCK = ROOT / "evaluation/substrate_capability/substrate_adequacy_adoption_surface_v1_lock_20261002.json"
RAW = ROOT / "evaluation/reports/substrate_adequacy_adoption_surface_v1_raw_20261002.json"
ORACLE_ID = "adapter-path-square-oracle-v1"
KEY = hashlib.sha256(b"adapter-path-test-provider-key-v1-not-for-deployment").digest()
SOURCE_FILES = (
    "domains/adequacy_provider_auth.py", "domains/independent_adequacy.py",
    "domains/code_reading.py", "domains/code_write_growth.py",
    "domains/code_writing.py", "domains/code_curriculum.py",
    "domains/register_source.py", "domains/teach.py", "substrate/world_adapter.py",
    "substrate/boot_core.py", "substrate/boot_all.py", "runners/dsl/src/substrate.rs",
    "runners/dsl/src/py.rs", "runners/dsl/src/term.rs",
    "runners/dsl/python/substrate_rs/__init__.py",
    "runners/dsl/python/substrate_rs/_native.build.json",
)
CASES = ("valid_signature", "tampered_signature", "direct_legacy_call", "curriculum_legacy_call")
REPEATS = 3
EXAMPLE = "def square(x):\n    return x * x\n"
PROBE = {"x": 2}
KNOWN = [{"inputs": {"x": 0}, "expected": 0}]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tree_digest(relative: str, suffixes: tuple[str, ...], names=()) -> str:
    root = ROOT / relative
    h = hashlib.sha256()
    paths = sorted(p for p in root.rglob("*") if p.is_file()
                   and (p.suffix in suffixes or p.name in names))
    for path in paths:
        h.update(path.relative_to(ROOT).as_posix().encode()); h.update(b"\0")
        h.update(sha(path).encode()); h.update(b"\n")
    return h.hexdigest()


def active_payload() -> dict:
    import substrate_rs
    files = {name: sha(ROOT / name) for name in SOURCE_FILES}
    files["native_binary"] = sha(Path(substrate_rs._native.__file__).resolve())
    files["domains_tree"] = tree_digest("domains", (".py",))
    files["substrate_tree"] = tree_digest("substrate", (".py",))
    files["rust_tree"] = tree_digest("runners/dsl/src", (".rs",))
    seed_hash = hashlib.sha256()
    for path in sorted([*ROOT.joinpath("seeds").glob("*.json"),
                        *ROOT.joinpath("seeds/generated").glob("*.json")]):
        seed_hash.update(path.relative_to(ROOT).as_posix().encode()); seed_hash.update(b"\0")
        seed_hash.update(sha(path).encode()); seed_hash.update(b"\n")
    files["seed_manifest_inventory"] = seed_hash.hexdigest()
    return files


def frozen_payload() -> dict:
    return {
        "schema": "SubstrateAdequacyAdoptionSurfaceV1Lock",
        "files": {str(path.relative_to(ROOT)): sha(path)
                  for path in (RUNNER, PROTOCOL)},
        "active": active_payload(),
        "git_head": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "design": {"cases": list(CASES), "repeats_per_case": REPEATS,
                   "example_sha256": hashlib.sha256(EXAMPLE.encode()).hexdigest(),
                   "probe": PROBE, "known": KNOWN,
                   "provider_id": ORACLE_ID,
                   "test_key_sha256": hashlib.sha256(KEY).hexdigest(),
                   "tamper": "change signature first hex digit; compute receipt after tamper",
                   "curriculum_fixture": sha(ROOT / "tests/fixtures/code_curriculum/lesson_boolean_functions.txt")},
    }


def code_shape_ids(sub) -> list[str]:
    return [str(node) for node in sub.nodes("ShapeSignature")
            if sub.node(node)["attrs"].get("kind") == "code_write_construction"]


def worker(case: str, repetition: int, frozen: dict) -> dict:
    if active_payload() != frozen["active"]:
        raise RuntimeError("active source/native/seed drift")
    from domains import code_reading as cdr
    from substrate.world_adapter import WorldAdapter

    adapter = WorldAdapter(shadow_read=False, deep_ingest=False,
        trusted_adequacy_provider_keys={ORACLE_ID: KEY},
        require_authenticated_code_examples=True)
    sub, native, _ = cdr._resolve(adapter)
    before = code_shape_ids(sub)
    if case in ("direct_legacy_call", "curriculum_legacy_call"):
        start = time.perf_counter_ns()
        if case == "direct_legacy_call":
            from domains.code_write_growth import teach_write_shape_from_example
            result = teach_write_shape_from_example(adapter, EXAMPLE, request_text=None)
            outcomes = [result]
            reply = result.get("reason")
        else:
            from domains import code_curriculum
            from substrate.boot_all import load_all_seeds
            load_all_seeds(adapter)
            lesson = (ROOT / "tests/fixtures/code_curriculum/lesson_boolean_functions.txt").read_text()
            outcomes = code_curriculum.learn_functions_from_lesson(
                adapter, lesson, lesson_source="fixture:lesson_boolean_functions.txt")
            reply = " | ".join(str(row.get("reason")) for row in outcomes)
        elapsed = time.perf_counter_ns() - start
        after = code_shape_ids(sub)
        return {"case": case, "repetition": repetition, "pid": os.getpid(),
            "receipt_status": None, "code_shape_ids_before": before,
            "code_shape_ids_after": after,
            "adopted_code_shape_ids": sorted(set(after) - set(before)),
            "shape_delta": len(set(after) - set(before)), "elapsed_ns": elapsed,
            "outcomes": [{"ok": bool(row.get("ok")), "reason": row.get("reason")}
                         for row in outcomes], "reply": reply,
            "active_after": active_payload()}
    from domains import independent_adequacy as ia
    from domains.adequacy_provider_auth import sign_label
    reading = cdr.read_function(adapter, EXAMPLE, "square")
    term = reading.get("term")
    if term is None:
        raise RuntimeError(f"example parser failed: {reading}")
    candidate = ia.candidate_id_for_write_shape(EXAMPLE, "square", reading["args"], term, None)
    request = ia.propose_audit_request(candidate, term, KNOWN, [PROBE],
        acquisition_source_ids=["fixture:adapter-path"], count=1,
        seed="adapter-path-fixed-seed-v1")
    probe = request["probes"][0]
    label = {"source_id": ORACLE_ID, "label_id": "square-at-two",
             "expected": 4, "oracle_sha256": hashlib.sha256(
                 b"authored fixture: square(2)=4").hexdigest()}
    label = sign_label(label, request["request_id"], probe["probe_id"],
                       probe["input_sha256"], KEY)
    if case == "tampered_signature":
        signature = label["signature"]
        label["signature"] = ("0" if signature[0] != "0" else "1") + signature[1:]
    rows = [{"probe_id": probe["probe_id"], "inputs": probe["inputs"],
             "labels": [label]}]
    receipt = ia.adjudicate_audit_receipt(request, candidate, term, rows,
        lambda candidate_term, env: native.evaluate(candidate_term, env),
        acquisition_source_ids=["fixture:adapter-path"])
    start = time.perf_counter_ns()
    reply = adapter.converse(EXAMPLE, code_example_evidence={
        "request": request, "audit_rows": rows, "receipt": receipt})
    elapsed = time.perf_counter_ns() - start
    after = code_shape_ids(sub)
    return {"case": case, "repetition": repetition, "pid": os.getpid(),
            "receipt_status": receipt["status"], "candidate_id": candidate,
            "code_shape_ids_before": before, "code_shape_ids_after": after,
            "adopted_code_shape_ids": sorted(set(after) - set(before)),
            "shape_delta": len(set(after) - set(before)), "elapsed_ns": elapsed,
            "reply": reply, "active_after": active_payload()}


def main() -> int:
    frozen = frozen_payload()
    if sys.argv[1:] == ["--lock"]:
        if LOCK.exists() or RAW.exists():
            raise SystemExit("refusing lock/capture overwrite")
        LOCK.write_text(json.dumps(frozen, indent=2, sort_keys=True) + "\n")
        print(LOCK.relative_to(ROOT)); return 0
    if not LOCK.is_file() or json.loads(LOCK.read_text()) != frozen:
        raise SystemExit("missing or stale lock")
    if RAW.exists():
        raise SystemExit(f"refusing to overwrite {RAW}")
    env = dict(os.environ, OZMA_NO_LLM="1", OZMA_SEED_PERSIST_DISABLED="1")
    env["PYTHONPATH"] = f"{ROOT}:{ROOT / 'runners/dsl/python'}:{env.get('PYTHONPATH', '')}"
    workers = []
    for case in CASES:
        for repetition in range(1, REPEATS + 1):
            proc = subprocess.run([sys.executable, str(RUNNER), "--worker", case,
                                   str(repetition)], cwd=ROOT, env=env, text=True,
                capture_output=True, timeout=180)
            if proc.returncode:
                raise RuntimeError(f"{case}/{repetition} failed: {proc.stderr[-4000:]}")
            row = json.loads(proc.stdout.strip().splitlines()[-1]); workers.append(row)
            print(f"{case}/{repetition}: receipt={row['receipt_status']} "
                  f"shape_delta={row['shape_delta']}", flush=True)
    post = frozen_payload()
    capture = {"schema": "SubstrateAdequacyAdoptionSurfaceV1Capture",
        "lock": frozen, "post_lock": post, "source_stable": frozen == post,
        "schedule": [{"case": case, "repetition": rep}
                     for case in CASES for rep in range(1, REPEATS + 1)],
        "workers": workers, "host": platform.platform(), "python": sys.version}
    RAW.write_text(json.dumps(capture, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"workers": len(workers), "source_stable": capture["source_stable"],
                      "raw": str(RAW.relative_to(ROOT))}, indent=2))
    return 0


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "--worker":
        lock = json.loads(LOCK.read_text())
        print(json.dumps(worker(sys.argv[2], int(sys.argv[3]), lock), sort_keys=True))
    else:
        raise SystemExit(main())

#!/usr/bin/env python3
"""Source-locked live-route test of trusted-but-wrong provider labels."""
from __future__ import annotations
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
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_ADEQUACY_TRUSTED_SIGNER_LIVE_V1_PREREG_20261002.md"
LOCK = ROOT / "evaluation/substrate_capability/substrate_adequacy_trusted_signer_live_v1_lock_20261002.json"
RAW = ROOT / "evaluation/reports/substrate_adequacy_trusted_signer_live_v1_raw_20261002.json"
ORACLE_ID = "independent-square-oracle-v1"
KEY = hashlib.sha256(b"trusted-signer-live-test-key-not-for-deployment").digest()
EXAMPLES = {
    "honest_square": ("def square(x):\n    return x * x\n", "square", 4),
    "trusted_wrong_identity": ("def identity(x):\n    return x\n", "identity", 2),
}
CASES = tuple(EXAMPLES)
REPEATS = 3
KNOWN = [{"inputs": {"x": 0}, "expected": 0}]
PROBE = {"x": 2}
HELDOUT = (3, 4, 5)
SOURCE_FILES = (
    "domains/adequacy_provider_auth.py", "domains/independent_adequacy.py",
    "domains/code_reading.py", "domains/code_write_growth.py",
    "domains/code_writing.py", "domains/teach.py", "substrate/world_adapter.py",
    "runners/dsl/src/substrate.rs", "runners/dsl/src/py.rs", "runners/dsl/src/term.rs",
    "runners/dsl/python/substrate_rs/__init__.py",
    "runners/dsl/python/substrate_rs/_native.build.json",
)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tree_digest(relative, suffixes):
    h = hashlib.sha256()
    for path in sorted(p for p in (ROOT / relative).rglob("*")
                       if p.is_file() and p.suffix in suffixes):
        h.update(path.relative_to(ROOT).as_posix().encode()); h.update(b"\0")
        h.update(sha(path).encode()); h.update(b"\n")
    return h.hexdigest()


def active_payload():
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


def frozen_payload():
    return {"schema": "SubstrateAdequacyTrustedSignerLiveV1Lock",
        "files": {str(path.relative_to(ROOT)): sha(path) for path in (RUNNER, PROTOCOL)},
        "active": active_payload(),
        "git_head": subprocess.check_output(["git", "rev-parse", "HEAD"],
                                                cwd=ROOT, text=True).strip(),
        "design": {"cases": {key: {"source_sha256": hashlib.sha256(value[0].encode()).hexdigest(),
                                    "name": value[1], "signed_expected": value[2]}
                              for key, value in EXAMPLES.items()},
                   "repeats_per_case": REPEATS, "known": KNOWN, "probe": PROBE,
                   "heldout": list(HELDOUT), "oracle_id": ORACLE_ID,
                   "test_key_sha256": hashlib.sha256(KEY).hexdigest(),
                   "square_oracle": "x*x"}}


def code_shape_ids(sub):
    return [str(node) for node in sub.nodes("ShapeSignature")
            if sub.node(node)["attrs"].get("kind") == "code_write_construction"]


def worker(case, repetition, frozen):
    if active_payload() != frozen["active"]:
        raise RuntimeError("source/native/seed drift")
    from domains import code_reading as cdr
    from domains import independent_adequacy as ia
    from domains.adequacy_provider_auth import sign_label, verify_signed_audit_evidence
    from substrate.world_adapter import WorldAdapter

    source, name, claimed = EXAMPLES[case]
    adapter = WorldAdapter(shadow_read=False, deep_ingest=False,
        trusted_adequacy_provider_keys={ORACLE_ID: KEY},
        require_authenticated_code_examples=True)
    sub, native, _ = cdr._resolve(adapter)
    reading = cdr.read_function(adapter, source, name); term = reading.get("term")
    if term is None:
        raise RuntimeError(f"source did not parse: {reading}")
    candidate = ia.candidate_id_for_write_shape(source, name, reading["args"], term, None)
    request = ia.propose_audit_request(candidate, term, KNOWN, [PROBE],
        acquisition_source_ids=["fixture:trusted-signer-live"], count=1,
        seed="trusted-signer-live-fixed-v1")
    probe = request["probes"][0]
    label = {"source_id": ORACLE_ID, "label_id": f"label:{case}",
        "expected": claimed, "oracle_sha256": hashlib.sha256(
            b"independent square oracle: x*x").hexdigest()}
    label = sign_label(label, request["request_id"], probe["probe_id"],
                       probe["input_sha256"], KEY)
    rows = [{"probe_id": probe["probe_id"], "inputs": probe["inputs"], "labels": [label]}]
    receipt = ia.adjudicate_audit_receipt(request, candidate, term, rows,
        lambda t, env: native.evaluate(t, env),
        acquisition_source_ids=["fixture:trusted-signer-live"])
    provider_check = verify_signed_audit_evidence(request, rows, receipt, {ORACLE_ID: KEY})
    before = code_shape_ids(sub)
    start = time.perf_counter_ns()
    reply = adapter.converse(source, code_example_evidence={
        "request": request, "audit_rows": rows, "receipt": receipt})
    elapsed = time.perf_counter_ns() - start
    after = code_shape_ids(sub)
    heldout = []
    for x in HELDOUT:
        prediction = native.evaluate(term, {"x": x})
        oracle = x * x
        heldout.append({"x": x, "prediction": prediction, "oracle": oracle,
                        "match": prediction == oracle})
    return {"case": case, "repetition": repetition, "pid": os.getpid(),
        "candidate_id": candidate, "claimed_label": claimed,
        "oracle_label_at_probe": PROBE["x"] ** 2,
        "receipt_status": receipt["status"], "provider_auth": provider_check,
        "shape_delta": len(set(after) - set(before)),
        "adopted_code_shape_ids": sorted(set(after) - set(before)),
        "heldout": heldout, "heldout_correct": sum(row["match"] for row in heldout),
        "elapsed_ns": elapsed, "reply": reply, "active_after": active_payload()}


def main():
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
        for rep in range(1, REPEATS + 1):
            proc = subprocess.run([sys.executable, str(RUNNER), "--worker", case, str(rep)],
                cwd=ROOT, env=env, text=True, capture_output=True, timeout=180)
            if proc.returncode:
                raise RuntimeError(f"{case}/{rep} failed: {proc.stderr[-4000:]}")
            row = json.loads(proc.stdout.strip().splitlines()[-1]); workers.append(row)
            print(f"{case}/{rep}: auth={row['provider_auth']['ok']} receipt={row['receipt_status']} "
                  f"adopted={row['shape_delta']} heldout={row['heldout_correct']}/3", flush=True)
    post = frozen_payload()
    capture = {"schema": "SubstrateAdequacyTrustedSignerLiveV1Capture",
        "lock": frozen, "post_lock": post, "source_stable": frozen == post,
        "workers": workers,
        "schedule": [{"case": case, "repetition": rep}
                     for case in CASES for rep in range(1, REPEATS + 1)],
        "host": platform.platform(), "python": sys.version}
    RAW.write_text(json.dumps(capture, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"workers": len(workers), "source_stable": capture["source_stable"],
                      "raw": str(RAW.relative_to(ROOT))}, indent=2))
    return 0


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "--worker":
        print(json.dumps(worker(sys.argv[2], int(sys.argv[3]), json.loads(LOCK.read_text())),
                         sort_keys=True))
    else:
        raise SystemExit(main())

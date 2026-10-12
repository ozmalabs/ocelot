#!/usr/bin/env python3
"""Source-locked agreement/domain adequacy panel through strict live adoption."""
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
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_ADEQUACY_PROVIDER_AGREEMENT_AND_DOMAIN_V1_PREREG_20261002.md"
LOCK = ROOT / "evaluation/substrate_capability/substrate_adequacy_provider_agreement_domain_v1_lock_20261002.json"
RAW = ROOT / "evaluation/reports/substrate_adequacy_provider_agreement_domain_v1_raw_20261002.json"
PROVIDERS = ("oracle-a", "oracle-b")
KEYS = {provider: hashlib.sha256(f"test-only-provider-key:{provider}".encode()).digest()
        for provider in PROVIDERS}
ORACLE_SHA = hashlib.sha256(b"independent fixture oracle: square(x)=x*x").hexdigest()
EXAMPLES = {
    "honest_single": {"source": "def square(x):\n    return x * x\n", "name": "square", "x": 2,
                      "labels": [("oracle-a", 4)]},
    "conflicting_two": {"source": "def identity(x):\n    return x\n", "name": "identity", "x": 2,
                         "labels": [("oracle-a", 4), ("oracle-b", 2)]},
    "correlated_wrong_two": {"source": "def identity(x):\n    return x\n", "name": "identity", "x": 2,
                              "labels": [("oracle-a", 2), ("oracle-b", 2)]},
    "aliased_honest_two": {"source": "def identity(x):\n    return x\n", "name": "identity", "x": 0,
                            "labels": [("oracle-a", 0), ("oracle-b", 0)]},
    "distinguishing_honest_two": {"source": "def identity(x):\n    return x\n", "name": "identity", "x": 2,
                                  "labels": [("oracle-a", 4), ("oracle-b", 4)]},
}
CASES = tuple(EXAMPLES)
REPEATS = 3
HELDOUT = (3, 4, 5)
SOURCE_FILES = (
    "domains/adequacy_provider_auth.py", "domains/independent_adequacy.py",
    "domains/code_reading.py", "domains/code_write_growth.py", "domains/code_writing.py",
    "domains/teach.py", "substrate/world_adapter.py", "runners/dsl/src/substrate.rs",
    "runners/dsl/src/py.rs", "runners/dsl/src/term.rs",
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
    seed_digest = hashlib.sha256()
    for path in sorted([*ROOT.joinpath("seeds").glob("*.json"),
                        *ROOT.joinpath("seeds/generated").glob("*.json")]):
        seed_digest.update(path.relative_to(ROOT).as_posix().encode()); seed_digest.update(b"\0")
        seed_digest.update(sha(path).encode()); seed_digest.update(b"\n")
    files["seed_manifest_inventory"] = seed_digest.hexdigest()
    return files


def frozen_payload():
    return {"schema": "SubstrateAdequacyProviderAgreementDomainV1Lock",
        "files": {str(path.relative_to(ROOT)): sha(path) for path in (RUNNER, PROTOCOL)},
        "active": active_payload(),
        "git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "design": {"cases": json.loads(json.dumps(EXAMPLES)), "repeats": REPEATS, "heldout": list(HELDOUT),
                   "provider_key_sha256": {name: hashlib.sha256(key).hexdigest()
                                           for name, key in KEYS.items()},
                   "oracle_sha256": ORACLE_SHA,
                   "receipt_policy": "existing core adjudicator; conflicts produce ambiguous receipts"}}


def code_shape_ids(sub):
    return [str(node) for node in sub.nodes("ShapeSignature")
            if sub.node(node)["attrs"].get("kind") == "code_write_construction"]


def worker(case, repetition, frozen):
    if active_payload() != frozen["active"]:
        raise RuntimeError("source/native/seed drift")
    from domains import code_reading as cdr, independent_adequacy as ia
    from domains.adequacy_provider_auth import sign_label, verify_signed_audit_evidence
    from substrate.world_adapter import WorldAdapter

    spec = EXAMPLES[case]
    adapter = WorldAdapter(shadow_read=False, deep_ingest=False,
        trusted_adequacy_provider_keys=KEYS, require_authenticated_code_examples=True)
    sub, native, _ = cdr._resolve(adapter)
    reading = cdr.read_function(adapter, spec["source"], spec["name"]); term = reading.get("term")
    if term is None:
        raise RuntimeError(f"candidate failed to parse: {reading}")
    candidate = ia.candidate_id_for_write_shape(spec["source"], spec["name"], reading["args"], term, None)
    probe_input = {"x": spec["x"]}
    request = ia.propose_audit_request(candidate, term, [], [probe_input],
        acquisition_source_ids=["fixture:provider-agreement-domain"], count=1,
        seed=f"provider-agreement-domain-v1:{case}")
    probe = request["probes"][0]
    labels = []
    for provider, expected in spec["labels"]:
        label = {"source_id": provider, "label_id": f"{case}:{provider}",
                 "expected": expected, "oracle_sha256": ORACLE_SHA}
        labels.append(sign_label(label, request["request_id"], probe["probe_id"],
                                 probe["input_sha256"], KEYS[provider]))
    rows = [{"probe_id": probe["probe_id"], "inputs": probe_input, "labels": labels}]
    receipt = ia.adjudicate_audit_receipt(request, candidate, term, rows,
        lambda t, env: native.evaluate(t, env),
        acquisition_source_ids=["fixture:provider-agreement-domain"])
    auth = verify_signed_audit_evidence(request, rows, receipt, KEYS)
    before = code_shape_ids(sub)
    start = time.perf_counter_ns()
    reply = adapter.converse(spec["source"], code_example_evidence={
        "request": request, "audit_rows": rows, "receipt": receipt})
    elapsed = time.perf_counter_ns() - start
    after = code_shape_ids(sub)
    heldout = []
    for x in HELDOUT:
        prediction = native.evaluate(term, {"x": x})
        heldout.append({"x": x, "prediction": prediction, "oracle": x * x,
                        "match": prediction == x * x})
    return {"case": case, "repetition": repetition, "pid": os.getpid(),
        "candidate_id": candidate, "probe": probe_input,
        "provider_ids": [row["source_id"] for row in labels],
        "provider_expected": [row["expected"] for row in labels],
        "provider_auth": auth, "receipt_status": receipt["status"],
        "receipt_residuals": receipt.get("residuals"),
        "shape_delta": len(set(after) - set(before)),
        "adopted_code_shape_ids": sorted(set(after) - set(before)),
        "heldout": heldout, "heldout_correct": sum(row["match"] for row in heldout),
        "elapsed_ns": elapsed, "reply": reply, "active_after": active_payload()}


def main():
    frozen = frozen_payload()
    if sys.argv[1:] == ["--lock"]:
        if LOCK.exists() or RAW.exists():
            raise SystemExit("refusing to overwrite lock/capture")
        LOCK.write_text(json.dumps(frozen, indent=2, sort_keys=True) + "\n")
        print(LOCK.relative_to(ROOT)); return 0
    if not LOCK.is_file() or json.loads(LOCK.read_text()) != frozen:
        raise SystemExit("missing or stale source/native lock")
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
    capture = {"schema": "SubstrateAdequacyProviderAgreementDomainV1Capture",
        "lock": frozen, "post_lock": post, "source_stable": post == frozen,
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
        print(json.dumps(worker(sys.argv[2], int(sys.argv[3]), json.loads(LOCK.read_text())), sort_keys=True))
    else:
        raise SystemExit(main())

#!/usr/bin/env python3
"""Source-locked live adoption study for recomputed disagreement probes."""
from __future__ import annotations
import hashlib
import json
import os
import platform
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
RUNNER = Path(__file__).resolve()
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_ADEQUACY_SELECTED_PROBE_ADOPTION_V1_PREREG_20261002.md"
LOCK = ROOT / "evaluation/substrate_capability/substrate_adequacy_selected_probe_adoption_v1_lock_20261002.json"
RAW = ROOT / "evaluation/reports/substrate_adequacy_selected_probe_adoption_v1_raw_20261002.json"
PROVIDER = "oracle-a"
KEY = hashlib.sha256(b"selected-probe-gate-test-key-not-for-deployment").digest()
ORACLE_SHA = hashlib.sha256(b"fixture oracle square(x)=x*x").hexdigest()
IDENTITY = "def identity(x):\n    return x\n"
SQUARE = "def square(x):\n    return x * x\n"
DOMAIN = [{"x": 0}, {"x": 2}]
CASES = {
    "honest_selected_square": {"source": SQUARE, "name": "square", "challenger": IDENTITY,
        "challenger_name": "identity", "domain": DOMAIN, "label": 4},
    "alias_zero_entropy": {"source": IDENTITY, "name": "identity", "challenger": SQUARE,
        "challenger_name": "square", "domain": [{"x": 0}], "label": 0},
    "distinguishing_identity_truth": {"source": IDENTITY, "name": "identity", "challenger": SQUARE,
        "challenger_name": "square", "domain": DOMAIN, "label": 4},
    "selected_wrong_signer": {"source": IDENTITY, "name": "identity", "challenger": SQUARE,
        "challenger_name": "square", "domain": DOMAIN, "label": 2},
}
REPEATS = 3
HELDOUT = (3, 4, 5)
SOURCE_FILES = (
    "domains/adequacy_probe_selection.py", "domains/adequacy_provider_auth.py",
    "domains/independent_adequacy.py", "domains/code_reading.py",
    "domains/code_write_growth.py", "domains/code_writing.py", "domains/teach.py",
    "substrate/world_adapter.py", "runners/dsl/src/substrate.rs",
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
    digest = hashlib.sha256()
    for path in sorted([*ROOT.joinpath("seeds").glob("*.json"),
                        *ROOT.joinpath("seeds/generated").glob("*.json")]):
        digest.update(path.relative_to(ROOT).as_posix().encode()); digest.update(b"\0")
        digest.update(sha(path).encode()); digest.update(b"\n")
    files["seed_manifest_inventory"] = digest.hexdigest()
    return files


def frozen_payload():
    return {"schema": "SubstrateAdequacySelectedProbeAdoptionV1Lock",
        "files": {str(path.relative_to(ROOT)): sha(path) for path in (RUNNER, PROTOCOL)},
        "active": active_payload(),
        "git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "design": {"cases": json.loads(json.dumps(CASES)), "repeats": REPEATS,
            "heldout": list(HELDOUT), "provider": PROVIDER,
            "test_key_sha256": hashlib.sha256(KEY).hexdigest(),
            "oracle_sha256": ORACLE_SHA,
            "selector": "maximum Shannon entropy over candidate plus supplied challenger Terms"}}


def code_shape_ids(sub):
    return [str(node) for node in sub.nodes("ShapeSignature")
            if sub.node(node)["attrs"].get("kind") == "code_write_construction"]


def worker(case, repetition, frozen):
    if active_payload() != frozen["active"]:
        raise RuntimeError("source/native/seed drift")
    from domains import code_reading as cdr, independent_adequacy as ia
    from domains.adequacy_probe_selection import select_disagreement_probe
    from domains.adequacy_provider_auth import sign_label
    from substrate.world_adapter import WorldAdapter

    spec = CASES[case]
    adapter = WorldAdapter(shadow_read=False, deep_ingest=False,
        trusted_adequacy_provider_keys={PROVIDER: KEY},
        require_discriminating_code_example_probe=True)
    sub, native, _ = cdr._resolve(adapter)
    reading = cdr.read_function(adapter, spec["source"], spec["name"])
    challenger_reading = cdr.read_function(adapter, spec["challenger"], spec["challenger_name"])
    term = reading.get("term"); challenger_term = challenger_reading.get("term")
    if term is None or challenger_term is None:
        raise RuntimeError("candidate/challenger did not parse")
    candidate = ia.candidate_id_for_write_shape(spec["source"], spec["name"], reading["args"], term, None)
    selection_seed = f"selected-probe-v1:{case}"
    acquisition_rows = []
    acquisition_source_ids = ["fixture:selected-probe-study"]
    selection = select_disagreement_probe(candidate, term, [challenger_term],
        acquisition_rows, spec["domain"],
        lambda candidate_term, env: native.evaluate(candidate_term, env),
        seed=selection_seed)
    selection_context = {"challenger_terms": [challenger_term],
        "acquisition_rows": acquisition_rows, "admissible_inputs": spec["domain"],
        "acquisition_source_ids": acquisition_source_ids,
        "seed": selection_seed, "selection": selection}
    request = ia.propose_audit_request(candidate, term, acquisition_rows,
        [selection["input"]], acquisition_source_ids=acquisition_source_ids,
        count=1, seed=selection["selection_id"])
    probe = request["probes"][0]
    label = {"source_id": PROVIDER, "label_id": f"{case}:label",
        "expected": spec["label"], "oracle_sha256": ORACLE_SHA}
    signed = sign_label(label, request["request_id"], probe["probe_id"],
                        probe["input_sha256"], KEY)
    rows = [{"probe_id": probe["probe_id"], "inputs": probe["inputs"], "labels": [signed]}]
    receipt = ia.adjudicate_audit_receipt(request, candidate, term, rows,
        lambda candidate_term, env: native.evaluate(candidate_term, env),
        acquisition_source_ids=acquisition_source_ids)
    before = code_shape_ids(sub)
    reply = adapter.converse(spec["source"], code_example_evidence={
        "request": request, "audit_rows": rows, "receipt": receipt,
        "probe_selection_context": selection_context})
    after = code_shape_ids(sub)
    heldout = [{"x": x, "prediction": native.evaluate(term, {"x": x}),
        "oracle": x * x,
        "match": native.evaluate(term, {"x": x}) == x * x} for x in HELDOUT]
    return {"case": case, "repetition": repetition, "pid": os.getpid(),
        "candidate_term": term, "challenger_terms": [challenger_term],
        "selection_context": selection_context, "request": request,
        "audit_rows": rows, "receipt": receipt,
        "selected_input": selection["input"],
        "selection_entropy_bits": selection["prediction_entropy_bits"],
        "receipt_status": receipt["status"],
        "shape_delta": len(set(after) - set(before)),
        "adopted_code_shape_ids": sorted(set(after) - set(before)),
        "heldout": heldout, "heldout_correct": sum(row["match"] for row in heldout),
        "reply": reply, "active_after": active_payload()}


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
            print(f"{case}/{rep}: entropy={row['selection_entropy_bits']:.2f} "
                  f"receipt={row['receipt_status']} adoption={row['shape_delta']} "
                  f"heldout={row['heldout_correct']}/3", flush=True)
    post = frozen_payload()
    capture = {"schema": "SubstrateAdequacySelectedProbeAdoptionV1Capture",
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

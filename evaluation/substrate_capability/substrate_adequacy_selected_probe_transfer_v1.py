#!/usr/bin/env python3
"""Source-locked transfer of live selected-probe adoption across task families."""
from __future__ import annotations
import hashlib
import json
import os
import platform
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python"), str(Path(__file__).resolve().parent)]
RUNNER = Path(__file__).resolve()
ORACLE = ROOT / "evaluation/substrate_capability/independent_codewrite_oracles.py"
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_ADEQUACY_SELECTED_PROBE_TRANSFER_V1_PREREG_20261002.md"
LOCK = ROOT / "evaluation/substrate_capability/substrate_adequacy_selected_probe_transfer_v1_lock_20261002.json"
RAW = ROOT / "evaluation/reports/substrate_adequacy_selected_probe_transfer_v1_raw_20261002.json"
PROVIDER = "selected-probe-transfer-oracle"
KEY = hashlib.sha256(b"selected-probe-transfer-test-key-not-for-deployment").digest()
REPEATS = 3
PARITY = "def parity(value):\n    return value % 2 == 0\n"
ALWAYS_FALSE = "def always_false(value):\n    return False\n"
IDENTITY = "def identity(value, lower, upper):\n    return value\n"
CLAMP = ("def clamp_value(value, lower, upper):\n"
         "    return lower if value < lower else (upper if value > upper else value)\n")


def clamp_domain(mode):
    pairs = [(-4, 8), (1, 5), (-9, -2)]
    if mode == "alias":
        return [{"value": v, "lower": lo, "upper": hi}
                for lo, hi in pairs for v in (lo, (lo + hi) // 2, hi)]
    return [{"value": v, "lower": lo, "upper": hi}
            for lo, hi in pairs for v in (lo - 3, lo, (lo + hi) // 2, hi, hi + 3)]


def clamp_heldout():
    pairs = [(-4, 8), (1, 5), (-9, -2)]
    return [{"value": v, "lower": lo, "upper": hi}
            for lo, hi in pairs for v in (lo - 5, lo, lo + 1, (lo + hi) // 2,
                                           hi - 1, hi, hi + 5)]


PARITY_BROAD = [{"value": value} for value in range(-8, 9)]
PARITY_ODD = [{"value": value} for value in (-7, -5, -3, -1, 1, 3, 5, 7)]
PARITY_HELDOUT = [{"value": value} for value in range(-20, 21)]
CASES = {
    "parity_correct_broad": {"task": "parity", "candidate_source": PARITY,
        "candidate_name": "parity", "challenger_source": ALWAYS_FALSE,
        "challenger_name": "always_false", "domain": PARITY_BROAD,
        "heldout": PARITY_HELDOUT, "target": True},
    "parity_alias_wrong": {"task": "parity", "candidate_source": ALWAYS_FALSE,
        "candidate_name": "always_false", "challenger_source": PARITY,
        "challenger_name": "parity", "domain": PARITY_ODD,
        "heldout": PARITY_HELDOUT, "target": False},
    "parity_distinguish_wrong": {"task": "parity", "candidate_source": ALWAYS_FALSE,
        "candidate_name": "always_false", "challenger_source": PARITY,
        "challenger_name": "parity", "domain": PARITY_BROAD,
        "heldout": PARITY_HELDOUT, "target": False},
    "clamp_correct_broad": {"task": "clamp", "candidate_source": CLAMP,
        "candidate_name": "clamp_value", "challenger_source": IDENTITY,
        "challenger_name": "identity", "domain": clamp_domain("broad"),
        "heldout": clamp_heldout(), "target": True},
    "clamp_alias_wrong": {"task": "clamp", "candidate_source": IDENTITY,
        "candidate_name": "identity", "challenger_source": CLAMP,
        "challenger_name": "clamp_value", "domain": clamp_domain("alias"),
        "heldout": clamp_heldout(), "target": False},
    "clamp_distinguish_wrong": {"task": "clamp", "candidate_source": IDENTITY,
        "candidate_name": "identity", "challenger_source": CLAMP,
        "challenger_name": "clamp_value", "domain": clamp_domain("broad"),
        "heldout": clamp_heldout(), "target": False},
}
CASES = json.loads(json.dumps(CASES))
SOURCE_FILES = (
    "domains/adequacy_probe_selection.py", "domains/adequacy_provider_auth.py",
    "domains/independent_adequacy.py", "domains/code_reading.py",
    "domains/code_write_growth.py", "domains/code_writing.py", "domains/teach.py",
    "substrate/world_adapter.py", "runners/dsl/src/substrate.rs", "runners/dsl/src/py.rs",
    "runners/dsl/src/term.rs", "runners/dsl/python/substrate_rs/__init__.py",
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
    files["oracle"] = sha(ORACLE)
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
    return {"schema": "SubstrateAdequacySelectedProbeTransferV1Lock",
        "files": {str(path.relative_to(ROOT)): sha(path)
                  for path in (RUNNER, ORACLE, PROTOCOL)},
        "active": active_payload(),
        "git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "design": {"cases": CASES, "repeats": REPEATS,
            "test_key_sha256": hashlib.sha256(KEY).hexdigest(),
            "provider": PROVIDER,
            "oracle": "independent_codewrite_oracles.label",
            "selection": "maximum entropy over candidate and one independently read challenger Term"}}


def code_shape_ids(sub):
    return [str(node) for node in sub.nodes("ShapeSignature")
            if sub.node(node)["attrs"].get("kind") == "code_write_construction"]


def worker(case, repetition, frozen):
    if active_payload() != frozen["active"]:
        raise RuntimeError("source/native/seed drift")
    from domains import code_reading as cdr, independent_adequacy as ia
    from domains.adequacy_probe_selection import select_disagreement_probe
    from domains.adequacy_provider_auth import sign_label
    from independent_codewrite_oracles import label as oracle_label
    from substrate.world_adapter import WorldAdapter

    spec = CASES[case]
    adapter = WorldAdapter(shadow_read=False, deep_ingest=False,
        trusted_adequacy_provider_keys={PROVIDER: KEY},
        require_discriminating_code_example_probe=True)
    sub, native, _ = cdr._resolve(adapter)
    candidate_read = cdr.read_function(adapter, spec["candidate_source"], spec["candidate_name"])
    challenger_read = cdr.read_function(adapter, spec["challenger_source"], spec["challenger_name"])
    term, challenger = candidate_read.get("term"), challenger_read.get("term")
    if term is None or challenger is None:
        raise RuntimeError(f"candidate or challenger could not be read for {case}")
    candidate_id = ia.candidate_id_for_write_shape(
        spec["candidate_source"], spec["candidate_name"], candidate_read["args"], term, None)
    acquisition_rows = []
    source_ids = [f"fixture:{spec['task']}:selected-probe-transfer"]
    selector_seed = f"selected-probe-transfer-v1:{case}"
    selection = select_disagreement_probe(candidate_id, term, [challenger], acquisition_rows,
        spec["domain"], lambda t, env: native.evaluate(t, env), seed=selector_seed)
    context = {"challenger_terms": [challenger], "acquisition_rows": acquisition_rows,
        "admissible_inputs": spec["domain"], "acquisition_source_ids": source_ids,
        "seed": selector_seed, "selection": selection}
    request = ia.propose_audit_request(candidate_id, term, acquisition_rows,
        [selection["input"]], acquisition_source_ids=source_ids, count=1,
        seed=selection["selection_id"])
    probe = request["probes"][0]
    expected = oracle_label(spec["task"], probe["inputs"])
    signed = sign_label({"source_id": PROVIDER, "label_id": f"{case}:{probe['probe_id']}",
        "expected": expected, "oracle_sha256": sha(ORACLE)}, request["request_id"],
        probe["probe_id"], probe["input_sha256"], KEY)
    rows = [{"probe_id": probe["probe_id"], "inputs": probe["inputs"], "labels": [signed]}]
    receipt = ia.adjudicate_audit_receipt(request, candidate_id, term, rows,
        lambda t, env: native.evaluate(t, env), acquisition_source_ids=source_ids)
    before = code_shape_ids(sub)
    reply = adapter.converse(spec["candidate_source"], code_example_evidence={
        "request": request, "audit_rows": rows, "receipt": receipt,
        "probe_selection_context": context})
    after = code_shape_ids(sub)
    heldout = []
    for env in spec["heldout"]:
        predicted = native.evaluate(term, env)
        expected_heldout = oracle_label(spec["task"], env)
        heldout.append({"inputs": env, "prediction": predicted,
            "expected": expected_heldout, "match": predicted == expected_heldout})
    return {"case": case, "repetition": repetition, "pid": os.getpid(),
        "task": spec["task"], "candidate_term": term, "challenger_terms": [challenger],
        "selection_context": context, "request": request, "audit_rows": rows,
        "receipt": receipt, "selected_input": selection["input"],
        "selection_entropy_bits": selection["prediction_entropy_bits"],
        "shape_delta": len(set(after) - set(before)),
        "adopted_code_shape_ids": sorted(set(after) - set(before)),
        "heldout": heldout, "heldout_correct": sum(row["match"] for row in heldout),
        "heldout_count": len(heldout), "reply": reply, "active_after": active_payload()}


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
    env["PYTHONPATH"] = f"{ROOT}:{ROOT / 'runners/dsl/python'}:{RUNNER.parent}:{env.get('PYTHONPATH', '')}"
    workers = []
    for case in CASES:
        for rep in range(1, REPEATS + 1):
            proc = subprocess.run([sys.executable, str(RUNNER), "--worker", case, str(rep)],
                cwd=ROOT, env=env, text=True, capture_output=True, timeout=180)
            if proc.returncode:
                raise RuntimeError(f"{case}/{rep} failed: {proc.stderr[-4000:]}")
            row = json.loads(proc.stdout.strip().splitlines()[-1]); workers.append(row)
            print(f"{case}/{rep}: entropy={row['selection_entropy_bits']:.2f} "
                  f"receipt={row['receipt']['status']} adopted={row['shape_delta']} "
                  f"heldout={row['heldout_correct']}/{row['heldout_count']}", flush=True)
    post = frozen_payload()
    capture = {"schema": "SubstrateAdequacySelectedProbeTransferV1Capture",
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
        print(json.dumps(worker(sys.argv[2], int(sys.argv[3]), json.loads(LOCK.read_text())),
                         sort_keys=True))
    else:
        raise SystemExit(main())

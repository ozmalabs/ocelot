#!/usr/bin/env python3
"""Full-seed integration of challenger probe selection, receipt, and teach gate."""
from __future__ import annotations
import hashlib, json, os, platform, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNNER = Path(__file__).resolve()
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python"), str(RUNNER.parent)]
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_ADEQUACY_SELECTOR_RECEIPT_ADOPTION_V1_PREREG_20261002.md"
ORACLE = ROOT / "evaluation/substrate_capability/independent_codewrite_oracles.py"
LOCK = ROOT / "evaluation/substrate_capability/substrate_adequacy_selector_receipt_adoption_v1_lock_20261002.json"
RAW = ROOT / "evaluation/reports/substrate_adequacy_selector_receipt_adoption_v1_raw_20261002.json"
REPS = 3
KNOWN = [{"inputs": {"x": 0}, "expected": 0}]
CASES = {
    "correct_square": {"source": "def square(x):\n    return x * x\n", "function": "square", "domain": [{"x": x} for x in (1,2,3,4)]},
    "wrong_identity_broad": {"source": "def identity(x):\n    return x\n", "function": "identity", "domain": [{"x": x} for x in (1,2,3,4)]},
    "wrong_identity_alias": {"source": "def identity(x):\n    return x\n", "function": "identity", "domain": [{"x": 1}]},
}
SOURCES = (
    "domains/adequacy_probe_selection.py", "domains/independent_adequacy.py",
    "domains/code_reading.py", "domains/code_writing.py", "domains/code_write_growth.py",
    "domains/teach.py", "domains/ast_to_term.py", "domains/engine_provenance.py",
    "substrate/world_adapter.py", "substrate/boot_all.py", "substrate/boot_core.py",
    "substrate/seed_loader.py", "runners/dsl/src/term.rs", "runners/dsl/src/py.rs",
    "runners/dsl/src/graph_rules.rs", "runners/dsl/src/substrate.rs",
    "runners/dsl/python/substrate_rs/__init__.py", "runners/dsl/python/substrate_rs/_native.build.json")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tree_sha(base_rel: str, suffixes: tuple[str, ...], names=()) -> str:
    files = [p for p in (ROOT/base_rel).rglob("*") if p.is_file() and
             (p.suffix in suffixes or p.name in names)]
    digest = hashlib.sha256()
    for path in sorted(files):
        digest.update(path.relative_to(ROOT).as_posix().encode()); digest.update(b"\0")
        digest.update(sha(path).encode()); digest.update(b"\n")
    return digest.hexdigest()


def active_payload() -> dict:
    import substrate_rs
    data = {name: sha(ROOT/name) for name in SOURCES}
    data["oracle"] = sha(ORACLE)
    data["native_binary"] = sha(Path(substrate_rs._native.__file__).resolve())
    data["domains_tree"] = tree_sha("domains", (".py",))
    data["substrate_tree"] = tree_sha("substrate", (".py",))
    data["rust_tree"] = tree_sha("runners/dsl/src", (".rs",))
    data["python_native_tree"] = tree_sha("runners/dsl/python/substrate_rs", (".py",),
                                           ("_native.abi3.so", "_native.build.json"))
    digest = hashlib.sha256()
    seed_files = sorted([*ROOT.joinpath("seeds").glob("*.json"), *ROOT.joinpath("seeds/generated").glob("*.json")])
    for path in seed_files:
        digest.update(path.relative_to(ROOT).as_posix().encode()); digest.update(b"\0")
        digest.update(sha(path).encode()); digest.update(b"\n")
    data["seed_manifest_inventory"] = digest.hexdigest()
    return data


def lock_payload() -> dict:
    return {"schema": "SubstrateAdequacySelectorReceiptAdoptionV1Lock",
            "files": {str(path.relative_to(ROOT)): sha(path) for path in (RUNNER, PROTOCOL, ORACLE)},
            "active": active_payload(), "git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
            "design": {"repetitions": REPS, "known": KNOWN, "cases": CASES,
                       "request": "square transform", "selection_policy": "maximum prediction entropy",
                       "oracle": "independent analytic square oracle", "require_receipt": True}}


def shape_state(sub, agent_node) -> dict:
    shapes = []
    for node in sub.nodes("ShapeSignature"):
        attrs = sub.node(node)["attrs"]
        if attrs.get("kind") == "code_write_construction":
            shapes.append(str(node))
    return {"shape_ids": shapes, "epoch": sub.node(agent_node)["attrs"].get("write_codebook_epoch", 0) or 0}


def worker(case_name: str, repetition: int, lock: dict) -> dict:
    os.environ.setdefault("OZMA_NO_LLM", "1"); os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")
    if active_payload() != lock["active"]: raise RuntimeError("worker source/seed hashes differ from lock")
    from domains import code_reading as cdr, code_writing as cw, code_write_growth as cwg
    from domains import independent_adequacy as ia
    from domains.adequacy_probe_selection import select_disagreement_probe
    from independent_codewrite_oracles import label as oracle_label
    from substrate.boot_all import load_all_seeds
    from substrate.world_adapter import WorldAdapter
    case = CASES[case_name]
    agent = WorldAdapter(seeds=())
    boot_start = time.perf_counter_ns(); boot = load_all_seeds(agent); boot_ns = time.perf_counter_ns()-boot_start
    sub, native, agent_node = cdr._resolve(agent)
    REQUEST = "square transform"
    reading = cdr.read_function(agent, case["source"], case["function"])
    if reading.get("term") is None: raise RuntimeError(f"failed to parse candidate: {reading}")
    candidate_term, args = reading["term"], list(reading["args"])
    if args != ["x"]: raise RuntimeError(f"unexpected argument list: {args}")
    square_term = {"type": "Times", "items": [{"type": "Var", "name": "x"}, {"type": "Var", "name": "x"}]}
    identity_term = {"type": "Var", "name": "x"}
    challenger = identity_term if case_name == "correct_square" else square_term
    cid = ia.candidate_id_for_write_shape(case["source"], case["function"], args, candidate_term, REQUEST)
    selection = select_disagreement_probe(cid, candidate_term, [challenger], KNOWN, case["domain"],
                                          lambda term, env: native.evaluate(term, env),
                                          seed=f"receipt-adoption:{case_name}:{repetition}")
    selected = selection["input"]
    req = ia.propose_audit_request(cid, candidate_term, KNOWN, [selected],
                                   acquisition_source_ids=["acquisition:square:x0"], count=1,
                                   seed=f"receipt-adoption-request:{case_name}:{repetition}")
    if len(req["probes"]) != 1 or req["probes"][0]["inputs"] != selected:
        raise RuntimeError("request does not bind the selected fresh input")
    oracle_sha = sha(ORACLE); provider = f"independent-codewrite-oracle-v1:{oracle_sha}"
    expected = oracle_label("square", selected)
    audit = [{"probe_id": req["probes"][0]["probe_id"], "inputs": selected,
              "labels": [{"source_id": provider,
                          "label_id": hashlib.sha256((req["request_id"]+req["probes"][0]["probe_id"]+req["probes"][0]["input_sha256"]).encode()).hexdigest(),
                          "expected": expected, "oracle_sha256": oracle_sha}]}]
    receipt = ia.adjudicate_audit_receipt(req, cid, candidate_term, audit,
        lambda term, env: native.evaluate(term, env), acquisition_source_ids=["acquisition:square:x0"])
    before = shape_state(sub, agent_node)
    teach_start = time.perf_counter_ns()
    taught = cwg.teach_write_shape_from_example(agent, case["source"], request_text=REQUEST,
        contract_examples=KNOWN, adequacy_receipt=receipt, require_adequacy_receipt=True)
    teach_ns = time.perf_counter_ns()-teach_start
    after = shape_state(sub, agent_node)
    written = cw.write_function_from_request(agent, REQUEST, name="heldout_candidate")
    outputs = []
    if written.get("ok"):
        for x in (2,3,4,5):
            prediction = native.evaluate(written["term"], {"x": x})
            outputs.append({"x": x, "expected": oracle_label("square", {"x": x}),
                            "native_prediction": prediction, "matches": prediction == oracle_label("square", {"x": x})})
    return {"case": case_name, "repetition": repetition, "pid": os.getpid(),
            "boot_ns": boot_ns, "loaded_seed_count": int(boot.get("loaded",0) or 0),
            "candidate_id": cid, "selection": selection, "request": req,
            "audit_rows": audit, "receipt": receipt, "teach": taught, "teach_ns": teach_ns,
            "state_before": before, "state_after": after,
            "epoch_increment": after["epoch"]-before["epoch"],
            "written": {"ok": written.get("ok"), "source": written.get("source")},
            "heldout": outputs, "active_after": active_payload()}


def main() -> int:
    if sys.argv[1:] == ["--lock"]:
        if LOCK.exists() or RAW.exists(): raise SystemExit("refusing to overwrite lock/capture")
        LOCK.write_text(json.dumps(lock_payload(), indent=2, sort_keys=True)+"\n")
        print(LOCK.relative_to(ROOT)); return 0
    frozen = lock_payload()
    if not LOCK.is_file() or json.loads(LOCK.read_text()) != frozen: raise SystemExit("missing/stale source lock")
    if RAW.exists(): raise SystemExit(f"refusing to overwrite {RAW}")
    env = dict(os.environ, OZMA_NO_LLM="1", OZMA_SEED_PERSIST_DISABLED="1")
    env["PYTHONPATH"] = f"{ROOT}:{ROOT/'runners/dsl/python'}:{RUNNER.parent}:{env.get('PYTHONPATH','')}"
    schedule = [(case, rep) for case in CASES for rep in range(1, REPS+1)]
    workers = []; started = time.perf_counter_ns()
    for case, rep in schedule:
        proc = subprocess.run([sys.executable, str(RUNNER), "--worker", case, str(rep)],
                              cwd=ROOT, env=env, text=True, capture_output=True, timeout=180)
        if proc.returncode: raise RuntimeError(f"worker {case}/{rep} failed: {proc.stderr[-5000:]}")
        row = json.loads(proc.stdout.strip().splitlines()[-1]); workers.append(row)
        print(f"completed {case}/{rep}: receipt={row['receipt']['status']} teach={row['teach'].get('ok')}", flush=True)
    capture = {"schema": "SubstrateAdequacySelectorReceiptAdoptionV1Capture", "lock": frozen,
               "post_lock": lock_payload(), "schedule": schedule, "workers": workers,
               "source_stable": frozen == lock_payload(), "elapsed_ns": time.perf_counter_ns()-started,
               "environment": {"platform": platform.platform(), "python": sys.version}}
    RAW.write_text(json.dumps(capture, indent=2, sort_keys=True, default=str)+"\n")
    print(json.dumps({"workers": len(workers), "source_stable": capture["source_stable"],
                      "raw": str(RAW.relative_to(ROOT))}, indent=2)); return 0


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "--worker":
        print(json.dumps(worker(sys.argv[2], int(sys.argv[3]), json.loads(LOCK.read_text())), sort_keys=True, default=str))
    else: raise SystemExit(main())

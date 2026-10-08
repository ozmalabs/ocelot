#!/usr/bin/env python3
"""Three-task, source-locked integration panel for receipt-gated code growth."""
from __future__ import annotations
import hashlib, json, os, platform, random, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNNER = Path(__file__).resolve()
ORACLE = ROOT / "evaluation/substrate_capability/independent_codewrite_oracles.py"
ANALYZER = ROOT / "evaluation/substrate_capability/analyze_substrate_independent_adequacy_codewrite_transfer_v1.py"
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_INDEPENDENT_ADEQUACY_CODEWRITE_TRANSFER_V1_PREREG_20261002.md"
LOCK = ROOT / "evaluation/substrate_capability/substrate_independent_adequacy_codewrite_transfer_v1_lock_20261002.json"
RAW = ROOT / "evaluation/reports/substrate_independent_adequacy_codewrite_transfer_v1_raw_20261002.json"
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python"), str(RUNNER.parent)]

SOURCE_FILES = (
    "domains/code_reading.py", "domains/code_writing.py", "domains/code_write_growth.py",
    "domains/independent_adequacy.py", "domains/information_commitment.py", "domains/teach.py",
    "domains/ast_to_term.py", "domains/reflective_faculty.py", "domains/engine_provenance.py",
    "substrate/world_adapter.py", "substrate/boot_all.py", "substrate/boot_core.py",
    "substrate/seed_loader.py", "runners/dsl/src/term.rs", "runners/dsl/src/py.rs",
    "runners/dsl/src/graph_rules.rs", "runners/dsl/src/substrate.rs",
    "runners/dsl/python/substrate_rs/__init__.py", "runners/dsl/python/substrate_rs/_native.build.json")
REPETITIONS = 3
SEED = 20261002
REQUESTS = {
    "parity": "Write a function that returns the parity of an integer.",
    "clamp": "Write a function that clamps a value between lower and upper bounds.",
    "square": "Write a function that squares an integer.",
}
FIXTURES = {
    "parity": {"name": "parity", "source": "def parity(value):\n    return value % 2 == 0\n",
               "known": [{"inputs": {"value": 0}, "expected": True},
                         {"inputs": {"value": 1}, "expected": False}],
               "domain": [{"value": x} for x in range(-5, 6)],
               "heldout": [{"value": x} for x in range(-20, 21)]},
    "clamp": {"name": "clamp_value",
              "source": "def clamp_value(value, lower, upper):\n    return lower if value < lower else (upper if value > upper else value)\n",
              "known": [{"inputs": {"value": -10, "lower": -4, "upper": 8}, "expected": -4},
                        {"inputs": {"value": 0, "lower": -4, "upper": 8}, "expected": 0},
                        {"inputs": {"value": 12, "lower": -4, "upper": 8}, "expected": 8}],
              "domain": [{"value": x, "lower": lo, "upper": hi}
                         for lo, hi in [(-4, 8), (1, 5), (-9, -2)]
                         for x in (lo-2, lo, lo+1, (lo+hi)//2, hi, hi+2)],
              "heldout": [
                  {"value": -20, "lower": -4, "upper": 8}, {"value": -4, "lower": -4, "upper": 8},
                  {"value": -3, "lower": -4, "upper": 8}, {"value": 0, "lower": -4, "upper": 8},
                  {"value": 7, "lower": -4, "upper": 8}, {"value": 8, "lower": -4, "upper": 8},
                  {"value": 9, "lower": -4, "upper": 8}, {"value": 20, "lower": -4, "upper": 8},
                  {"value": -9, "lower": -9, "upper": -2}, {"value": -10, "lower": -9, "upper": -2},
                  {"value": -5, "lower": -9, "upper": -2}, {"value": -2, "lower": -9, "upper": -2},
                  {"value": 0, "lower": -9, "upper": -2}, {"value": 12, "lower": -9, "upper": -2},
                  {"value": 2, "lower": 1, "upper": 5}, {"value": 1, "lower": 1, "upper": 5},
                  {"value": 3, "lower": 1, "upper": 5}, {"value": 5, "lower": 1, "upper": 5},
                  {"value": 7, "lower": 1, "upper": 5}, {"value": -1, "lower": 1, "upper": 5}]},
    "negative": {"task": "square", "name": "identity",
                 "source": "def identity(x):\n    return x\n",
                 "known": [{"inputs": {"x": 1}, "expected": 1}],
                 "domain": [{"x": x} for x in (0, 1, 2, 3, 4, 5)]},
}


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def tree_sha(base_rel: str, suffixes: tuple[str, ...], names=()) -> str:
    base = ROOT / base_rel
    files = [p for p in base.rglob("*") if p.is_file() and
             (p.suffix in suffixes or p.name in names)]
    rows = [(p.relative_to(ROOT).as_posix(), sha(p)) for p in files]
    h = hashlib.sha256()
    for rel, digest in sorted(rows):
        h.update(rel.encode()); h.update(b"\0"); h.update(digest.encode()); h.update(b"\n")
    return h.hexdigest()


def active_payload() -> dict:
    import substrate_rs
    values = {p: sha(ROOT / p) for p in SOURCE_FILES}
    values["oracle"] = sha(ORACLE)
    values["native_binary"] = sha(Path(substrate_rs._native.__file__).resolve())
    values["domains_tree"] = tree_sha("domains", (".py",))
    values["substrate_tree"] = tree_sha("substrate", (".py",))
    values["rust_dsl_tree"] = tree_sha("runners/dsl/src", (".rs",))
    values["python_native_tree"] = tree_sha("runners/dsl/python/substrate_rs", (".py",),
                                             ("_native.abi3.so", "_native.build.json"))
    seed_files = sorted([*ROOT.joinpath("seeds").glob("*.json"),
                         *ROOT.joinpath("seeds/generated").glob("*.json")])
    h = hashlib.sha256()
    for p in seed_files:
        h.update(p.relative_to(ROOT).as_posix().encode()); h.update(b"\0")
        h.update(sha(p).encode()); h.update(b"\n")
    values["seed_manifest_inventory"] = h.hexdigest()
    return values


def lock_payload() -> dict:
    return {"schema": "SubstrateIndependentAdequacyCodewriteTransferV1Lock",
            "files": {str(p.relative_to(ROOT)): sha(p) for p in (RUNNER, ORACLE, ANALYZER, PROTOCOL)},
            "active": active_payload(),
            "git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
            "design": {"repetitions": REPETITIONS, "seed": SEED, "fixtures": FIXTURES,
                       "requests": REQUESTS,
                       "oracle_source": "independent_codewrite_oracles.py",
                       "labels": "source-hash-bound deterministic oracle outputs on fresh selected probes"}}


def state(sub, agent_node, name):
    nodes = [n for n in sub.nodes("ShapeSignature")
             if sub.node(n)["attrs"].get("kind") == "code_write_construction"
             and sub.node(n)["attrs"].get("name") == name]
    epoch = sub.node(agent_node)["attrs"].get("write_codebook_epoch", 0) or 0
    return {"node_ids": [str(n) for n in nodes], "epoch": epoch}


def make_receipt(agent, task, fixture, request_text, oracle_sha, count, seed):
    from domains import code_reading as cdr
    from domains import independent_adequacy as ia
    from independent_codewrite_oracles import label as oracle_label
    reading = cdr.read_function(agent, fixture["source"], fixture["name"])
    if reading.get("term") is None:
        raise RuntimeError(f"candidate has no Term: {task}: {reading}")
    term, args, name = reading["term"], list(reading["args"]), reading["name"]
    candidate_id = ia.candidate_id_for_write_shape(
        fixture["source"], name, args, term, request_text)
    source_id = f"independent-codewrite-oracle-v1:{oracle_sha}"
    request = ia.propose_audit_request(
        candidate_id, term, fixture["known"], fixture["domain"],
        acquisition_source_ids=[f"acquisition:{task}:v1"], count=count, seed=seed)
    rows = []
    labels = []
    for probe in request["probes"]:
        expected = oracle_label(task, probe["inputs"])
        label = {"source_id": source_id,
                 "label_id": hashlib.sha256((request["request_id"] + probe["probe_id"] +
                                              probe["input_sha256"]).encode()).hexdigest(),
                 "expected": expected,
                 "oracle_sha256": oracle_sha}
        labels.append({"probe_id": probe["probe_id"], "inputs": probe["inputs"], "labels": [label]})
    receipt = ia.adjudicate_audit_receipt(
        request, candidate_id, term, labels,
        lambda candidate_term, env: cdr._resolve(agent)[1].evaluate(candidate_term, env),
        acquisition_source_ids=[f"acquisition:{task}:v1"])
    return {"reading": reading, "term": term, "args": args, "candidate_id": candidate_id,
            "request": request, "audit_rows": labels, "receipt": receipt,
            "oracle_labels": [{"probe_id": row["probe_id"], "inputs": row["inputs"],
                               "expected": row["labels"][0]["expected"]} for row in labels]}


def heldout_transfer(agent, task, fixture, request_text):
    from domains import code_reading as cdr
    from domains import code_writing as cw
    from independent_codewrite_oracles import label as oracle_label
    composed = cw.compose_function_from_request(agent, request_text)
    written = cw.write_function_from_request(agent, request_text, name="heldout_candidate")
    ns = {}
    if written.get("ok"):
        exec(written.get("source", ""), ns)  # noqa: S102 -- generated function, isolated namespace
    fn = ns.get("heldout_candidate")
    rows = []
    for env in fixture["heldout"]:
        expected = oracle_label(task, env)
        native_output = cdr._resolve(agent)[1].evaluate(written["term"], env) if written.get("ok") else None
        python_output = fn(**env) if callable(fn) else None
        rows.append({"inputs": env, "expected": expected,
                     "native_output": native_output, "python_output": python_output,
                     "native_match": native_output == expected,
                     "python_match": python_output == expected})
    return {"composed_ok": composed.get("ok"), "composed_term": composed.get("term"),
            "written": {"ok": written.get("ok"), "source": written.get("source"),
                        "term": written.get("term"), "sample_ok": written.get("sample_ok")},
            "rows": rows}


def worker(rep: int, expected_active: dict) -> dict:
    os.environ.setdefault("OZMA_NO_LLM", "1")
    os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")
    if active_payload() != expected_active:
        raise RuntimeError("worker source/seed hashes differ from lock")
    from domains import code_reading as cdr
    from domains import code_writing as cw
    from domains import code_write_growth as cwg
    from substrate.boot_all import load_all_seeds
    from substrate.world_adapter import WorldAdapter

    import independent_codewrite_oracles as oracles
    oracle_sha = sha(Path(oracles.__file__).resolve())
    agent = WorldAdapter(seeds=())
    boot_start = time.perf_counter_ns(); boot_cpu = time.process_time_ns()
    boot = load_all_seeds(agent)
    boot_ns, boot_cpu_ns = time.perf_counter_ns()-boot_start, time.process_time_ns()-boot_cpu
    sub, _native, agent_node = cdr._resolve(agent)
    baselines = {task: cw.write_function_from_request(agent, REQUESTS[task], name="heldout_candidate")
                 for task in ("parity", "clamp", "square")}
    outcomes = {}
    negative = FIXTURES["negative"]
    before = state(sub, agent_node, "taught_identity")
    negative_candidate = dict(negative, task="square")
    negative_probe = make_receipt(agent, "square", negative_candidate, REQUESTS["square"],
                                  oracle_sha, count=2, seed=f"codewrite-v1:{rep}:negative")
    negative_start = time.perf_counter_ns()
    negative_result = cwg.teach_write_shape_from_example(
        agent, negative["source"], request_text=REQUESTS["square"],
        contract_examples=negative["known"], adequacy_receipt=negative_probe["receipt"],
        require_adequacy_receipt=True)
    negative_ns = time.perf_counter_ns()-negative_start
    after = state(sub, agent_node, "taught_identity")
    outcomes["negative_identity_as_square"] = {
        "receipt_status": negative_probe["receipt"]["status"], "teach_ok": negative_result.get("ok"),
        "reason": negative_result.get("reason"), "candidate_id_matches": negative_result.get("candidate_id") == negative_probe["candidate_id"],
        "contract_passed": negative_result.get("contract_validation", {}).get("ok"),
        "request_id": negative_probe["request"]["request_id"],
        "receipt_sha256": negative_probe["receipt"]["receipt_sha256"],
        "oracle_source_id": f"independent-codewrite-oracle-v1:{oracle_sha}",
        "audit_rows": negative_probe["audit_rows"],
        "state_before": before, "state_after": after, "state_unchanged": before == after,
        "audit_probes": negative_probe["oracle_labels"], "wall_ns": negative_ns}

    positive = {}
    for task, count in (("parity", 3), ("clamp", 4)):
        fixture = FIXTURES[task]
        request_text = REQUESTS[task]
        evidence = make_receipt(agent, task, fixture, request_text, oracle_sha, count,
                                f"codewrite-v1:{rep}:{task}")
        before = state(sub, agent_node, "taught_%s" % fixture["name"])
        started = time.perf_counter_ns(); cpu_start = time.process_time_ns()
        result = cwg.teach_write_shape_from_example(
            agent, fixture["source"], request_text=request_text,
            contract_examples=fixture["known"], adequacy_receipt=evidence["receipt"],
            require_adequacy_receipt=True)
        teach_ns, teach_cpu_ns = time.perf_counter_ns()-started, time.process_time_ns()-cpu_start
        after = state(sub, agent_node, "taught_%s" % fixture["name"])
        transfer = heldout_transfer(agent, task, fixture, request_text) if result.get("ok") else None
        positive[task] = {
            "receipt_status": evidence["receipt"]["status"], "candidate_id_matches": result.get("candidate_id") == evidence["candidate_id"],
            "teach_ok": result.get("ok"), "contract_passed": result.get("contract_validation", {}).get("ok"),
            "request_id": evidence["request"]["request_id"],
            "receipt_sha256": evidence["receipt"]["receipt_sha256"],
            "oracle_source_id": f"independent-codewrite-oracle-v1:{oracle_sha}",
            "audit_rows": evidence["audit_rows"],
            "state_before": before, "state_after": after,
            "epoch_increment": after["epoch"] - before["epoch"],
            "audit_probes": evidence["oracle_labels"], "teach_ns": teach_ns,
            "teach_cpu_ns": teach_cpu_ns, "transfer": transfer,
            "native_heldout_correct": sum(r["native_match"] for r in transfer["rows"]) if transfer else 0,
            "python_heldout_correct": sum(r["python_match"] for r in transfer["rows"]) if transfer else 0,
            "heldout_count": len(fixture["heldout"])}

    passes = (all(v.get("ok") is False for v in baselines.values())
              and outcomes["negative_identity_as_square"]["receipt_status"] == "rejected"
              and outcomes["negative_identity_as_square"]["teach_ok"] is False
              and outcomes["negative_identity_as_square"]["contract_passed"] is True
              and outcomes["negative_identity_as_square"]["state_unchanged"]
              and all(v["receipt_status"] == "accepted" and v["teach_ok"] is True
                      and v["contract_passed"] is True and v["candidate_id_matches"]
                      and v["epoch_increment"] == 1 and v["native_heldout_correct"] == v["heldout_count"]
                      and v["python_heldout_correct"] == v["heldout_count"] for v in positive.values()))
    return {"repetition": rep, "pid": os.getpid(), "boot_ns": boot_ns,
            "boot_cpu_ns": boot_cpu_ns, "loaded_seed_count": int(boot.get("loaded", 0) or 0),
            "oracle_sha256": oracle_sha, "baselines": {k: {"ok": v.get("ok"), "reason": v.get("reason")}
                                                         for k, v in baselines.items()},
            "negative": outcomes["negative_identity_as_square"], "positive": positive,
            "passed": passes, "active_after": active_payload()}


def main() -> None:
    if sys.argv[1:] == ["--lock"]:
        current = lock_payload()
        if LOCK.exists() or RAW.exists():
            raise SystemExit("refusing to overwrite source lock or raw capture")
        LOCK.write_text(json.dumps(current, indent=2, sort_keys=True)+"\n")
        print(LOCK); return
    current = lock_payload()
    if not LOCK.is_file() or json.loads(LOCK.read_text()) != current:
        raise SystemExit("missing or stale source lock")
    if len(sys.argv) == 3 and sys.argv[1] == "--worker":
        print(json.dumps(worker(int(sys.argv[2]), current["active"]), sort_keys=True, default=str)); return
    if RAW.exists():
        raise SystemExit(f"refusing to overwrite {RAW}")
    env = dict(os.environ); env["OZMA_NO_LLM"] = "1"; env["OZMA_SEED_PERSIST_DISABLED"] = "1"
    env["PYTHONPATH"] = f"{ROOT}:{ROOT / 'runners/dsl/python'}:{RUNNER.parent}:{env.get('PYTHONPATH','')}"
    workers = []
    schedule = list(range(1, REPETITIONS+1)); random.Random(SEED).shuffle(schedule)
    started = time.perf_counter_ns()
    for rep in schedule:
        proc = subprocess.run([sys.executable, str(RUNNER), "--worker", str(rep)], cwd=ROOT,
                              env=env, text=True, capture_output=True, timeout=120)
        if proc.returncode:
            raise RuntimeError(f"worker {rep} failed: {proc.stderr[-4000:]}")
        workers.append(json.loads(proc.stdout.strip().splitlines()[-1]))
        print(f"completed worker {rep}: pass={workers[-1]['passed']}", flush=True)
    capture = {"schema": "SubstrateIndependentAdequacyCodewriteTransferV1Capture",
               "lock": current, "post_lock": lock_payload(), "schedule": schedule,
               "workers": workers, "elapsed_ns": time.perf_counter_ns()-started,
               "environment": {"python": sys.version, "platform": platform.platform()}}
    RAW.parent.mkdir(parents=True, exist_ok=True)
    RAW.write_text(json.dumps(capture, indent=2, sort_keys=True, default=str)+"\n")
    all_pass = current == capture["post_lock"] and all(w["passed"] for w in workers)
    print(json.dumps({"passed": all_pass, "workers": len(workers), "raw": str(RAW)}, indent=2))
    if not all_pass:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

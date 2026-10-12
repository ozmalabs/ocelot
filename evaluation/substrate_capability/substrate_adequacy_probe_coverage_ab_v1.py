#!/usr/bin/env python3
"""Paired gated/ungated adoption under narrow and distinguishing probe domains."""
from __future__ import annotations
import hashlib, json, os, platform, random, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNNER = Path(__file__).resolve()
ORACLE = ROOT / "evaluation/substrate_capability/independent_codewrite_oracles.py"
ANALYZER = ROOT / "evaluation/substrate_capability/analyze_substrate_adequacy_probe_coverage_ab_v1.py"
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_ADEQUACY_PROBE_COVERAGE_AB_V1_PREREG_20261002.md"
LOCK = ROOT / "evaluation/substrate_capability/substrate_adequacy_probe_coverage_ab_v1_lock_20261002.json"
RAW = ROOT / "evaluation/reports/substrate_adequacy_probe_coverage_ab_v1_raw_20261002.json"
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
SOURCE = "def identity(x):\n    return x\n"
FUNC_NAME = "identity"
REQUEST = "square transform"
KNOWN = [{"inputs": {"x": 0}, "expected": 0}]
HELDOUT = [{"x": x} for x in (2, 3, 4, 5)]
ARMS = {
    "narrow_gated": {"domain": [{"x": 1}], "count": 1, "strict": True},
    "narrow_ungated": {"domain": [{"x": 1}], "count": 1, "strict": False},
    "broad_gated": {"domain": [{"x": x} for x in (1, 2, 3, 4)], "count": 3, "strict": True},
    "broad_ungated": {"domain": [{"x": x} for x in (1, 2, 3, 4)], "count": 3, "strict": False},
}


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def tree_sha(base_rel: str, suffixes: tuple[str, ...], names=()) -> str:
    files = [p for p in (ROOT/base_rel).rglob("*") if p.is_file() and
             (p.suffix in suffixes or p.name in names)]
    h = hashlib.sha256()
    for p in sorted(files):
        h.update(p.relative_to(ROOT).as_posix().encode()); h.update(b"\0")
        h.update(sha(p).encode()); h.update(b"\n")
    return h.hexdigest()


def active_payload() -> dict:
    import substrate_rs
    values = {p: sha(ROOT/p) for p in SOURCE_FILES}
    values["oracle"] = sha(ORACLE)
    values["native_binary"] = sha(Path(substrate_rs._native.__file__).resolve())
    values["domains_tree"] = tree_sha("domains", (".py",))
    values["substrate_tree"] = tree_sha("substrate", (".py",))
    values["rust_dsl_tree"] = tree_sha("runners/dsl/src", (".rs",))
    values["python_native_tree"] = tree_sha("runners/dsl/python/substrate_rs", (".py",),
                                             ("_native.abi3.so", "_native.build.json"))
    seeds = sorted([*ROOT.joinpath("seeds").glob("*.json"),
                    *ROOT.joinpath("seeds/generated").glob("*.json")])
    h = hashlib.sha256()
    for p in seeds:
        h.update(p.relative_to(ROOT).as_posix().encode()); h.update(b"\0")
        h.update(sha(p).encode()); h.update(b"\n")
    values["seed_manifest_inventory"] = h.hexdigest()
    return values


def lock_payload() -> dict:
    return {"schema": "SubstrateAdequacyProbeCoverageABV1Lock",
            "files": {str(p.relative_to(ROOT)): sha(p) for p in (RUNNER, ORACLE, ANALYZER, PROTOCOL)},
            "active": active_payload(),
            "git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
            "design": {"repetitions": REPETITIONS, "seed": SEED, "source": SOURCE,
                       "function_name": FUNC_NAME, "request": REQUEST, "known": KNOWN,
                       "heldout": HELDOUT, "arms": ARMS,
                       "labels": "same candidate-bound oracle outputs generated before gated/ungated teach"}}


def shape_state(sub, agent_node) -> dict:
    matches = [str(n) for n in sub.nodes("ShapeSignature")
               if sub.node(n)["attrs"].get("name") == "taught_identity"
               and sub.node(n)["attrs"].get("kind") == "code_write_construction"]
    epoch = sub.node(agent_node)["attrs"].get("write_codebook_epoch", 0) or 0
    return {"node_ids": matches, "epoch": epoch}


def run_arm(rep: int, arm_name: str, expected_active: dict) -> dict:
    os.environ.setdefault("OZMA_NO_LLM", "1")
    os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")
    if active_payload() != expected_active:
        raise RuntimeError("worker source/seed hashes differ from lock")
    from domains import code_reading as cdr
    from domains import code_writing as cw
    from domains import code_write_growth as cwg
    from domains import independent_adequacy as ia
    from independent_codewrite_oracles import label as oracle_label
    from substrate.boot_all import load_all_seeds
    from substrate.world_adapter import WorldAdapter

    arm = ARMS[arm_name]
    agent = WorldAdapter(seeds=())
    boot_start = time.perf_counter_ns()
    boot = load_all_seeds(agent)
    boot_ns = time.perf_counter_ns()-boot_start
    sub, native, agent_node = cdr._resolve(agent)
    baseline = cw.write_function_from_request(agent, REQUEST, name="heldout_candidate")
    reading = cdr.read_function(agent, SOURCE, FUNC_NAME)
    if reading.get("term") is None:
        raise RuntimeError(f"identity fixture failed to read: {reading}")
    term, args = reading["term"], list(reading["args"])
    oracle_sha = sha(ORACLE)
    cid = ia.candidate_id_for_write_shape(SOURCE, FUNC_NAME, args, term, REQUEST)
    acquisition_source = "acquisition:square:single-zero-example"
    provider_id = f"independent-codewrite-oracle-v1:{oracle_sha}"
    request = ia.propose_audit_request(cid, term, KNOWN, arm["domain"],
                                       acquisition_source_ids=[acquisition_source],
                                       count=arm["count"], seed=f"coverage-ab:{arm_name.split('_')[0]}:{rep}")
    audit_rows = []
    for probe in request["probes"]:
        value = oracle_label("square", probe["inputs"])
        audit_rows.append({"probe_id": probe["probe_id"], "inputs": probe["inputs"],
                           "labels": [{"source_id": provider_id,
                                       "label_id": hashlib.sha256((request["request_id"]+
                                                                   probe["probe_id"]+
                                                                   probe["input_sha256"]).encode()).hexdigest(),
                                       "expected": value, "oracle_sha256": oracle_sha}]})
    evidence_start = time.perf_counter_ns()
    receipt = ia.adjudicate_audit_receipt(
        request, cid, term, audit_rows,
        lambda candidate_term, env: native.evaluate(candidate_term, env),
        acquisition_source_ids=[acquisition_source])
    evidence_ns = time.perf_counter_ns()-evidence_start
    before = shape_state(sub, agent_node)
    teach_start = time.perf_counter_ns(); cpu_start = time.process_time_ns()
    kwargs = {"contract_examples": KNOWN}
    if arm["strict"]:
        kwargs.update({"adequacy_receipt": receipt, "require_adequacy_receipt": True})
    taught = cwg.teach_write_shape_from_example(agent, SOURCE, request_text=REQUEST, **kwargs)
    teach_ns, teach_cpu_ns = time.perf_counter_ns()-teach_start, time.process_time_ns()-cpu_start
    after = shape_state(sub, agent_node)
    written = cw.write_function_from_request(agent, REQUEST, name="heldout_candidate")
    transfer_rows = []
    fn = None
    if written.get("ok"):
        namespace = {}
        exec(written.get("source", ""), namespace)  # noqa: S102 -- isolated generated function
        fn = namespace.get("heldout_candidate")
    for env in HELDOUT:
        expected = oracle_label("square", env)
        native_output = native.evaluate(written["term"], env) if written.get("ok") else None
        python_output = fn(**env) if callable(fn) else None
        transfer_rows.append({"inputs": env, "expected": expected,
                              "native_output": native_output, "python_output": python_output,
                              "native_match": native_output == expected,
                              "python_match": python_output == expected})
    return {"repetition": rep, "arm": arm_name, "pid": os.getpid(), "strict": arm["strict"],
            "boot_ns": boot_ns, "loaded_seed_count": int(boot.get("loaded", 0) or 0),
            "baseline_ok": baseline.get("ok"), "oracle_sha256": oracle_sha,
            "candidate_id": cid, "receipt": receipt, "audit_rows": audit_rows,
            "evidence_ns": evidence_ns, "teach_ok": taught.get("ok"),
            "teach_reason": taught.get("reason"), "candidate_id_matches": taught.get("candidate_id") == cid,
            "contract_passed": taught.get("contract_validation", {}).get("ok"),
            "state_before": before, "state_after": after,
            "epoch_increment": after["epoch"]-before["epoch"],
            "teach_ns": teach_ns, "teach_cpu_ns": teach_cpu_ns,
            "written_ok": written.get("ok"), "written_source": written.get("source"),
            "transfer_rows": transfer_rows, "active_after": active_payload()}


def main() -> None:
    if sys.argv[1:] == ["--lock"]:
        if LOCK.exists() or RAW.exists():
            raise SystemExit("refusing to overwrite lock or raw capture")
        LOCK.write_text(json.dumps(lock_payload(), indent=2, sort_keys=True)+"\n")
        print(LOCK); return
    current = lock_payload()
    if not LOCK.is_file() or json.loads(LOCK.read_text()) != current:
        raise SystemExit("missing or stale source lock")
    if len(sys.argv) == 4 and sys.argv[1] == "--worker":
        print(json.dumps(run_arm(int(sys.argv[2]), sys.argv[3], current["active"]), sort_keys=True, default=str)); return
    if RAW.exists():
        raise SystemExit(f"refusing to overwrite {RAW}")
    env = dict(os.environ); env["OZMA_NO_LLM"] = "1"; env["OZMA_SEED_PERSIST_DISABLED"] = "1"
    env["PYTHONPATH"] = f"{ROOT}:{ROOT / 'runners/dsl/python'}:{RUNNER.parent}:{env.get('PYTHONPATH','')}"
    schedule = [(rep, arm) for rep in range(1, REPETITIONS+1) for arm in ARMS]
    random.Random(SEED).shuffle(schedule)
    workers = []; started = time.perf_counter_ns()
    for rep, arm in schedule:
        proc = subprocess.run([sys.executable, str(RUNNER), "--worker", str(rep), arm],
                              cwd=ROOT, env=env, text=True, capture_output=True, timeout=120)
        if proc.returncode:
            raise RuntimeError(f"worker {rep}/{arm} failed: {proc.stderr[-4000:]}")
        worker = json.loads(proc.stdout.strip().splitlines()[-1]); workers.append(worker)
        print(f"completed {rep}/{arm}: receipt={worker['receipt']['status']} teach={worker['teach_ok']}", flush=True)
    capture = {"schema": "SubstrateAdequacyProbeCoverageABV1Capture", "lock": current,
               "post_lock": lock_payload(), "schedule": schedule, "workers": workers,
               "elapsed_ns": time.perf_counter_ns()-started,
               "environment": {"python": sys.version, "platform": platform.platform()}}
    RAW.parent.mkdir(parents=True, exist_ok=True)
    RAW.write_text(json.dumps(capture, indent=2, sort_keys=True, default=str)+"\n")
    print(json.dumps({"workers": len(workers), "source_stable": current == capture["post_lock"],
                      "raw": str(RAW)}, indent=2))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Fresh-process integration panel for adequacy-gated code-shape adoption."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_ADEQUACY_RECEIPT_ADOPTION_V1_PREREG_20261002.md"
AMENDMENT = ROOT / "docs/research/engine_substrate/SUBSTRATE_ADEQUACY_RECEIPT_ADOPTION_V1_1_AMENDMENT_20261002.md"
RUNNER = Path(__file__).resolve()
ANALYZER = ROOT / "evaluation/substrate_capability/analyze_substrate_adequacy_receipt_adoption_v1.py"
LOCK = ROOT / "evaluation/substrate_capability/substrate_adequacy_receipt_adoption_v1_lock_20261002.json"
RAW = ROOT / "evaluation/reports/substrate_adequacy_receipt_adoption_v1_raw_20261002.json"
ACTIVE = ("domains/code_reading.py", "domains/code_writing.py", "domains/code_write_growth.py",
          "domains/independent_adequacy.py", "domains/teach.py", "domains/ast_to_term.py",
          "substrate/world_adapter.py", "substrate/boot_all.py", "substrate/seed_loader.py",
          "runners/dsl/src/term.rs", "runners/dsl/src/py.rs",
          "runners/dsl/python/substrate_rs/__init__.py",
          "runners/dsl/python/substrate_rs/_native.build.json")
SOURCE = "def square(x):\n    return x * x\n"
REQUEST_TEXT = "square x"
REPETITIONS = 3


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_hashes() -> dict:
    import substrate_rs
    result = {p: sha(ROOT / p) for p in ACTIVE}
    result["native_binary"] = sha(Path(substrate_rs._native.__file__).resolve())
    return result


def lock_payload() -> dict:
    return {"schema": "SubstrateAdequacyReceiptAdoptionV1Lock",
            "files": {str(p.relative_to(ROOT)): sha(p) for p in (RUNNER, ANALYZER, PROTOCOL, AMENDMENT)},
            "active": source_hashes(),
            "design": {"repetitions": REPETITIONS, "source": SOURCE,
                       "request_text": REQUEST_TEXT, "cases":
                       ["accepted", "rejected", "ambiguous", "incomplete", "invalid", "missing"],
                       "boot": "WorldAdapter(seeds=()) then load_all_seeds"}}


def _shape_state(sub, agent_node) -> dict:
    shapes = sorted((sub.node(n)["attrs"].get("name"), str(n))
                    for n in sub.nodes("ShapeSignature")
                    if sub.node(n)["attrs"].get("kind") == "code_write_construction")
    epoch = sub.node(agent_node)["attrs"].get("write_codebook_epoch", 0) or 0
    return {"shapes": shapes, "epoch": epoch}


def worker(repetition: int, expected_active: dict) -> dict:
    os.environ.setdefault("OZMA_NO_LLM", "1")
    os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")
    if source_hashes() != expected_active:
        raise RuntimeError("worker sources differ from pre-run lock")
    from domains import code_reading as cdr
    from domains import code_write_growth as cwg
    from domains import independent_adequacy as ia
    from substrate.boot_all import load_all_seeds
    from substrate.world_adapter import WorldAdapter

    agent = WorldAdapter(seeds=())
    boot_start = time.perf_counter_ns(); boot_cpu_start = time.process_time_ns()
    boot = load_all_seeds(agent)
    boot_ns = time.perf_counter_ns() - boot_start
    boot_cpu_ns = time.process_time_ns() - boot_cpu_start
    sub, _native, agent_node = cdr._resolve(agent)
    reading = cdr.read_function(agent, SOURCE, "square")
    if reading.get("term") is None:
        raise RuntimeError(f"fixture failed to read: {reading}")
    term, args, name = reading["term"], list(reading["args"]), reading["name"]
    candidate_id = ia.candidate_id_for_write_shape(SOURCE, name, args, term, REQUEST_TEXT)
    acquisition_rows = [{"inputs": {"x": 0}, "expected": 0}]
    domain = [{"x": 1}, {"x": 2}, {"x": 3}, {"x": 4}]
    acquisition_source = "acquisition:fixture:primary"
    audit_source = "audit:independent:provider"
    request = ia.propose_audit_request(candidate_id, term, acquisition_rows, domain,
                                       acquisition_source_ids=[acquisition_source], count=1,
                                       seed="adoption-integration-v1")
    probe = request["probes"][0]
    x = probe["inputs"]["x"]
    cases = {
        "accepted": [{"source_id": audit_source, "label_id": "ok:1", "expected": x*x}],
        "rejected": [{"source_id": audit_source, "label_id": "bad:1", "expected": x*x+1}],
        "ambiguous": [{"source_id": audit_source, "label_id": "amb:1", "expected": x*x},
                      {"source_id": "audit:second", "label_id": "amb:2", "expected": x*x+1}],
        "incomplete": [],
        "invalid": [{"source_id": acquisition_source, "label_id": "reuse:1", "expected": x*x}],
    }
    expected_status = {"rejected": "rejected", "ambiguous": "ambiguous", "incomplete": "incomplete",
                       "invalid": "invalid"}
    outputs = {}
    for case_name, labels in cases.items():
        if case_name == "accepted":
            continue  # exercise accepted evidence once, at the final adoption boundary
        receipt = None
        if labels is not None:
            rows = ([] if case_name == "incomplete" else
                    [{"probe_id": probe["probe_id"], "inputs": probe["inputs"], "labels": labels}])
            receipt = ia.adjudicate_audit_receipt(request, candidate_id, term, rows,
                                                  lambda t, env: env["x"] * env["x"],
                                                  acquisition_source_ids=[acquisition_source])
        before = _shape_state(sub, agent_node)
        started = time.perf_counter_ns(); cpu_started = time.process_time_ns()
        result = cwg.teach_write_shape_from_example(agent, SOURCE, request_text=REQUEST_TEXT,
                                                    adequacy_receipt=receipt,
                                                    require_adequacy_receipt=True)
        elapsed, cpu = time.perf_counter_ns()-started, time.process_time_ns()-cpu_started
        after = _shape_state(sub, agent_node)
        if receipt is None or receipt["status"] != "accepted":
            expected_no_growth = before == after
        else:
            expected_no_growth = None
        outputs[case_name] = {"receipt_status": receipt["status"] if receipt else None,
                              "expected_status": expected_status.get(case_name),
                              "teach_ok": result.get("ok"), "reason": result.get("reason"),
                              "candidate_id_matches": result.get("candidate_id") == candidate_id,
                              "state_before": before, "state_after": after,
                              "no_adoption_state_preserved": expected_no_growth,
                              "wall_ns": elapsed, "cpu_ns": cpu}

    before = _shape_state(sub, agent_node)
    started = time.perf_counter_ns(); cpu_started = time.process_time_ns()
    result = cwg.teach_write_shape_from_example(agent, SOURCE, request_text=REQUEST_TEXT,
                                                adequacy_receipt=None,
                                                require_adequacy_receipt=True)
    elapsed, cpu = time.perf_counter_ns()-started, time.process_time_ns()-cpu_started
    after = _shape_state(sub, agent_node)
    outputs["missing"] = {"receipt_status": None, "teach_ok": result.get("ok"),
                          "reason": result.get("reason"), "candidate_id_matches": result.get("candidate_id") == candidate_id,
                          "state_before": before, "state_after": after,
                          "no_adoption_state_preserved": before == after,
                          "wall_ns": elapsed, "cpu_ns": cpu}
    # Recreate accepted receipt because `receipt` currently refers to invalid.
    accepted_labels = cases["accepted"]
    accepted_receipt = ia.adjudicate_audit_receipt(
        request, candidate_id, term,
        [{"probe_id": probe["probe_id"], "inputs": probe["inputs"], "labels": accepted_labels}],
        lambda t, env: env["x"] * env["x"],
        acquisition_source_ids=[acquisition_source])
    before = _shape_state(sub, agent_node)
    started = time.perf_counter_ns(); cpu_started = time.process_time_ns()
    adopted = cwg.teach_write_shape_from_example(agent, SOURCE, request_text=REQUEST_TEXT,
                                                 adequacy_receipt=accepted_receipt,
                                                 require_adequacy_receipt=True)
    elapsed, cpu = time.perf_counter_ns()-started, time.process_time_ns()-cpu_started
    after = _shape_state(sub, agent_node)
    outputs["accepted_adoption"] = {"receipt_status": accepted_receipt["status"],
                                    "teach_ok": adopted.get("ok"), "shape": adopted.get("shape"),
                                    "candidate_id_matches": adopted.get("candidate_id") == candidate_id,
                                    "state_before": before, "state_after": after,
                                    "wall_ns": elapsed, "cpu_ns": cpu,
                                    "epoch_increment": after["epoch"] - before["epoch"]}
    outputs["passes"] = (
        all(outputs[k]["receipt_status"] == expected_status[k] and not outputs[k]["teach_ok"]
            and outputs[k]["candidate_id_matches"] and outputs[k]["no_adoption_state_preserved"]
            for k in expected_status)
        and not outputs["missing"]["teach_ok"] and outputs["missing"]["no_adoption_state_preserved"]
        and outputs["accepted_adoption"]["receipt_status"] == "accepted"
        and outputs["accepted_adoption"]["teach_ok"]
        and outputs["accepted_adoption"]["epoch_increment"] == 1)
    return {"repetition": repetition, "pid": os.getpid(), "boot_ns": boot_ns,
            "boot_cpu_ns": boot_cpu_ns, "loaded_seed_count": len(getattr(boot, "loaded", []) or []),
            "max_rss_kib": __import__("resource").getrusage(__import__("resource").RUSAGE_SELF).ru_maxrss,
            "cases": outputs, "active_after": source_hashes()}


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] == "--write-lock":
        LOCK.write_text(json.dumps(lock_payload(), indent=2, sort_keys=True) + "\n")
        print(LOCK)
        return
    lock = json.loads(LOCK.read_text())
    if lock_payload() != lock:
        raise SystemExit("source lock mismatch; inspect changes and regenerate only before capture")
    if len(sys.argv) > 1 and sys.argv[1] == "--worker":
        print(json.dumps(worker(int(sys.argv[2]), lock["active"]), sort_keys=True))
        return
    workers = []
    for rep in range(1, REPETITIONS + 1):
        raw = subprocess.check_output([sys.executable, str(RUNNER), "--worker", str(rep)],
                                      cwd=ROOT, text=True, env=os.environ.copy())
        workers.append(json.loads(raw))
    passed = all(worker["cases"]["passes"] and worker["active_after"] == lock["active"]
                 for worker in workers)
    capture = {"schema": "SubstrateAdequacyReceiptAdoptionV1Capture", "lock": lock,
               "post_lock": lock_payload(), "workers": workers, "passes": passed}
    RAW.parent.mkdir(parents=True, exist_ok=True)
    RAW.write_text(json.dumps(capture, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"passes": passed, "workers": len(workers),
                      "boot_ms": [round(w["boot_ns"]/1e6, 2) for w in workers],
                      "raw": str(RAW)}, indent=2))
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

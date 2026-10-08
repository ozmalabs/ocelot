#!/usr/bin/env python3
"""Source-locked benchmark of independent adequacy requests and residual receipts."""
from __future__ import annotations
import hashlib, json, os, platform, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
os.environ.setdefault("OZMA_NO_LLM", "1")
RUNNER = Path(__file__).resolve()
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_PROVENANCE_BOUND_ADEQUACY_RECEIPT_V1_PREREG_20261002.md"
ANALYZER = ROOT / "evaluation/substrate_capability/analyze_substrate_provenance_bound_adequacy_receipt_v1.py"
LOCK = ROOT / "evaluation/substrate_capability/substrate_provenance_bound_adequacy_receipt_v1_lock_20261002.json"
RAW = ROOT / "evaluation/reports/substrate_provenance_bound_adequacy_receipt_v1_raw_20261002.json"
INPUTS = {
    "generated_pool": ("evaluation/reports/substrate_contract_query_generated_pool_transfer_v1_raw_20261002.json",
                       "substrate_contract_query_generated_pool_transfer_v1_lock_20261002.json"),
    "cubic_transfer": ("evaluation/reports/substrate_contract_query_generated_cubic_transfer_v1_raw_20261002.json",
                       "substrate_contract_query_generated_cubic_transfer_v1_lock_20261002.json"),
    "grid_misspec": ("evaluation/reports/substrate_contract_query_generated_grid_misspec_v1_raw_20261002.json",
                      "substrate_contract_query_generated_grid_misspec_v1_lock_20261002.json"),
    "cubic_alias": ("evaluation/reports/substrate_contract_query_generated_cubic_alias_v1_raw_20261002.json",
                     "substrate_contract_query_generated_cubic_alias_v1_lock_20261002.json"),
    "gate_replay": ("evaluation/reports/substrate_contract_query_independent_adequacy_gate_v1_raw_20261002.json",
                    "substrate_contract_query_independent_adequacy_gate_v1_lock_20261002.json"),
}
ACTIVE = ("domains/independent_adequacy.py", "domains/contract_query.py", "domains/generator.py",
          "domains/query_selection.py", "domains/engine_provenance.py",
          "scripts/cegis_faculty_on_sum_of_n.py", "scripts/jabberwock_closes_the_euler_tie.py",
          "runners/dsl/src/term.rs", "runners/dsl/src/py.rs",
          "runners/dsl/python/substrate_rs/__init__.py", "runners/dsl/python/substrate_rs/_native.build.json")
BUDGETS = (1, 2, 4)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def active_hashes() -> dict:
    import substrate_rs as sr
    out = {name: sha(ROOT / name) for name in ACTIVE}
    out["native"] = sha(Path(sr._native.__file__).resolve())
    return out


def parent_inventory() -> dict:
    active = active_hashes()
    inventory = {}
    for name, (raw_name, lock_name) in INPUTS.items():
        raw_path = ROOT / raw_name
        lock_path = ROOT / "evaluation/substrate_capability" / lock_name
        capture, lock = json.loads(raw_path.read_text()), json.loads(lock_path.read_text())
        if capture.get("lock") != lock or capture.get("post_lock") != lock:
            raise RuntimeError(f"parent capture is stale: {name}")
        for source_path, source_hash in lock["files"].items():
            if sha(ROOT / source_path) != source_hash:
                raise RuntimeError(f"parent locked source changed: {name}/{source_path}")
        for source_path, source_hash in lock["active"].items():
            actual_hash = active[source_path] if source_path in active else sha(ROOT / source_path)
            if actual_hash != source_hash:
                raise RuntimeError(f"parent active source changed: {name}/{source_path}")
        inventory[name] = {"raw": sha(raw_path), "lock": sha(lock_path),
                           "files": lock["files"], "active": lock["active"]}
    return inventory


def payload() -> dict:
    return {"schema": "SubstrateProvenanceBoundAdequacyReceiptV1Lock",
            "files": {str(path.relative_to(ROOT)): sha(path) for path in (RUNNER, ANALYZER, PROTOCOL)},
            "active": active_hashes(), "parents": parent_inventory(),
            "git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
            "design": {"audit_budgets": list(BUDGETS), "sources": {key: list(value) for key, value in INPUTS.items()},
                       "gate": "accept only when all requested independent labels agree with candidate predictions",
                       "request_order": "seeded hash order over fresh admissible descriptors"}}


def independent_label(task: str, env: dict) -> float:
    if task == "triangular":
        n = int(env["n"]); return float(n * (n + 1) // 2)
    if task == "square": return float(int(env["x"]) ** 2)
    if task in ("cubic", "cubic_deep", "cubic_sparse", "cubic_alias"):
        return float(int(env["x"]) ** 3)
    if task == "absolute_value": return float(abs(int(env["x"])))
    return float(env["V"] - env["E"] + env["F"])


def acquisition_rows(case: dict, source_capture: dict) -> tuple[list[dict], str]:
    task_rows = source_capture["lock"]["design"]["tasks"][case["task"]]
    rows = [{"inputs": row["env"], "expected": row["answer"]} for row in task_rows["knowns"]]
    worker = next(w for w in source_capture["workers"]
                  if w["task"] == case["task"] and w["rep"] == case["rep"])
    outcome = worker["outcomes"]["lazy_matrix"]
    for step in outcome["history"]:
        rows.append({"inputs": step["query"], "expected": step["oracle_output"]})
    return rows, f"acquisition:{case['capture']}:{case['task']}:{case['rep']}"


def build_cases() -> tuple[list[dict], dict[str, dict]]:
    from domains.independent_adequacy import propose_audit_request, adjudicate_audit_receipt
    gate_capture = json.loads((ROOT / INPUTS["gate_replay"][0]).read_text())
    parents = {name: json.loads((ROOT / raw_lock[0]).read_text()) for name, raw_lock in INPUTS.items() if name != "gate_replay"}
    from substrate_rs import _native
    native = _native.Substrate()
    cases, controls = [], {}
    for captured in gate_capture["cases"]:
        task = captured["task"]
        source_capture = parents[captured["capture"]]
        acq_rows, acq_source = acquisition_rows(captured, source_capture)
        if captured["term"] is None:
            cases.append({"capture": captured["capture"], "task": task, "rep": captured["rep"],
                          "candidate_id": None, "term": None, "acquisition_rows": acq_rows,
                          "acquisition_source_id": acq_source, "audit_rows": captured["audit_rows"],
                          "status": "refused_empty", "budgets": {}})
            continue
        all_inputs = [row["env"] for row in captured["audit_rows"]]
        if not captured["audit_rows"]:
            raise RuntimeError(f"nonempty model has no frozen audit inputs: {task}")
        parent_task = source_capture["lock"]["design"]["tasks"][task]
        used = {json.dumps(row["env"], sort_keys=True, separators=(",", ":"))
                for field in ("knowns", "candidates", "heldout") for row in parent_task[field]}
        if any(json.dumps(env, sort_keys=True, separators=(",", ":")) in used for env in all_inputs):
            raise RuntimeError(f"adequacy descriptor overlaps acquisition capture: {task}/{captured['rep']}")
        budgets = {}
        for count in BUDGETS:
            request = propose_audit_request(captured["candidate_id"], captured["term"], acq_rows, all_inputs,
                                            acquisition_source_ids=[acq_source], count=count,
                                            seed=f"adequacy-v1:{task}:{captured['rep']}")
            labeled = []
            for probe in request["probes"]:
                audit_record = next(row for row in captured["audit_rows"] if row["env"] == probe["inputs"])
                answer = float(audit_record["answer"])
                labeled.append({"probe_id": probe["probe_id"], "inputs": probe["inputs"],
                                "labels": [{"source_id": f"independent-oracle:{task}",
                                            "label_id": f"{task}:{audit_record['name']}",
                                            "expected": answer}]})
            started = time.perf_counter()
            receipt = adjudicate_audit_receipt(request, captured["candidate_id"], captured["term"], labeled,
                                               lambda term, env: native.evaluate(term, env),
                                               acquisition_source_ids=[acq_source])
            budgets[str(count)] = {"request": request, "evidence": labeled, "receipt": receipt,
                                   "adjudication_wall_seconds": time.perf_counter() - started}
        cases.append({"capture": captured["capture"], "task": task, "rep": captured["rep"],
                      "candidate_id": captured["candidate_id"], "term": captured["term"],
                      "acquisition_rows": acq_rows, "acquisition_source_id": acq_source,
                      "audit_rows": captured["audit_rows"],
                      "status": "audited", "budgets": budgets})

        if task == "cubic" and captured["rep"] == 1:
            k = "1"
            request = budgets[k]["request"]
            evidence = budgets[k]["evidence"]
            correct = evidence[0]
            expected = correct["labels"][0]["expected"]
            controls["ambiguous_labels"] = adjudicate_audit_receipt(
                request, captured["candidate_id"], captured["term"],
                [{**correct, "labels": correct["labels"] + [{"source_id": "oracle-B", "label_id": "independent-B",
                                                                      "expected": expected + 1.0}]}],
                lambda term, env: native.evaluate(term, env), acquisition_source_ids=[acq_source])
            controls["incomplete_evidence"] = adjudicate_audit_receipt(
                request, captured["candidate_id"], captured["term"], [],
                lambda term, env: native.evaluate(term, env), acquisition_source_ids=[acq_source])
            controls["reused_source"] = adjudicate_audit_receipt(
                request, captured["candidate_id"], captured["term"], evidence,
                lambda term, env: native.evaluate(term, env), acquisition_source_ids=[acq_source, "independent-oracle:cubic"])
            altered = [{**evidence[0], "inputs": {"x": 999.0}}]
            controls["altered_descriptor"] = adjudicate_audit_receipt(
                request, captured["candidate_id"], captured["term"], altered,
                lambda term, env: native.evaluate(term, env), acquisition_source_ids=[acq_source])
            tampered_request = json.loads(json.dumps(request)); tampered_request["probes"][0]["inputs"]["x"] += 0.25
            try:
                adjudicate_audit_receipt(tampered_request, captured["candidate_id"], captured["term"], evidence,
                                         lambda term, env: native.evaluate(term, env), acquisition_source_ids=[acq_source])
                controls["tampered_request"] = {"status": "accepted_unexpectedly"}
            except ValueError as exc:
                controls["tampered_request"] = {"status": "fail_closed", "reason": str(exc)}
            noisy = json.loads(json.dumps(evidence))
            noisy[0]["labels"][0]["expected"] = expected + 123.0
            controls["single_noisy_label"] = adjudicate_audit_receipt(
                request, captured["candidate_id"], captured["term"], noisy,
                lambda term, env: native.evaluate(term, env), acquisition_source_ids=[acq_source])
    return cases, controls


def main() -> int:
    if sys.argv[1:] == ["--lock"]:
        if LOCK.exists() or RAW.exists(): raise SystemExit("refusing to overwrite lock/capture")
        LOCK.write_text(json.dumps(payload(), indent=2, sort_keys=True) + "\n")
        print(LOCK.relative_to(ROOT)); return 0
    frozen = payload()
    if not LOCK.exists() or json.loads(LOCK.read_text()) != frozen: raise SystemExit("missing or stale source/input lock")
    if RAW.exists(): raise SystemExit("refusing to overwrite capture")
    before = active_hashes()
    cases, controls = build_cases()
    after = active_hashes()
    RAW.write_text(json.dumps({"schema": "SubstrateProvenanceBoundAdequacyReceiptV1Capture",
                               "lock": frozen, "post_lock": payload(), "before": before, "after": after,
                               "cases": cases, "controls": controls,
                               "host": {"platform": platform.platform(), "python": sys.version}},
                              indent=2, sort_keys=True, default=str) + "\n")
    print(json.dumps({"raw": str(RAW.relative_to(ROOT)), "cases": len(cases), "controls": len(controls),
                      "stable": before == after}))
    return 0


if __name__ == "__main__": raise SystemExit(main())

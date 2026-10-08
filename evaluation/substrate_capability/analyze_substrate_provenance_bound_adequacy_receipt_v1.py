#!/usr/bin/env python3
"""Independent integrity, provenance, and residual replay for adequacy receipts."""
from __future__ import annotations
import hashlib, importlib.util, itertools, json, math, sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(Path(__file__).resolve().parent), str(ROOT), str(ROOT / "runners/dsl/python")]
LOCK = ROOT / "evaluation/substrate_capability/substrate_provenance_bound_adequacy_receipt_v1_lock_20261002.json"
RAW = ROOT / "evaluation/reports/substrate_provenance_bound_adequacy_receipt_v1_raw_20261002.json"
OUT = ROOT / "evaluation/reports/substrate_provenance_bound_adequacy_receipt_v1_analysis_20261002.json"
BUDGETS = (1, 2, 4)


def canonical(value) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def digest(value) -> str:
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def evaluate(term: dict, env: dict) -> float:
    op = term.get("type")
    if op == "Var": return float(env[term["name"]])
    if op == "Lit": return float(term["value"])
    args = [evaluate(value, env) for value in term.get("items", [])]
    if not args: args = [evaluate(term[key], env) for key in ("a", "b")]
    if op == "Plus": return sum(args)
    if op == "Minus": return args[0] - args[1]
    if op == "Times": return math.prod(args)
    if op == "Div": return 0.0 if args[1] == 0 else args[0] / args[1]
    raise ValueError(f"unsupported operator {op!r}")


def label(task: str, env: dict) -> float:
    if task == "triangular":
        n = int(env["n"]); return float(n * (n + 1) // 2)
    if task == "square": return float(int(env["x"]) ** 2)
    if task == "absolute_value": return float(abs(int(env["x"])))
    if task == "euler": return float(env["V"] - env["E"] + env["F"])
    return float(int(env["x"]) ** 3)


def expected_receipt(request, candidate_id, term, evidence, status, residuals, invalid_reasons=()):
    core = {"request_id": request["request_id"], "candidate_id": candidate_id,
            "term_sha256": digest(term), "status": status,
            "evidence_sha256": digest(evidence), "residuals": residuals,
            "invalid_reasons": list(invalid_reasons)}
    return {"schema": "IndependentAdequacyReceiptV1", **core, "receipt_sha256": digest(core)}


def main() -> int:
    lock, capture = json.loads(LOCK.read_text()), json.loads(RAW.read_text())
    errors = []
    import substrate_provenance_bound_adequacy_receipt_v1 as runner
    if runner.payload() != lock: errors.append("current source/native/parent capture differs from lock")
    if capture.get("lock") != lock or capture.get("post_lock") != lock: errors.append("capture lock mismatch")
    if capture.get("before") != lock["active"] or capture.get("after") != lock["active"]: errors.append("active source changed")
    cases = capture["cases"]
    if len(cases) != 24: errors.append(f"expected 24 cases, got {len(cases)}")
    seen = set()
    summary = defaultdict(lambda: defaultdict(lambda: {"accepted": 0, "rejected": 0, "ambiguous": 0,
                                                          "incomplete": 0, "invalid": 0, "refused_empty": 0,
                                                          "native_calls": 0, "wall_seconds": 0.0}))
    for case in cases:
        key = (case["capture"], case["task"], case["rep"])
        if key in seen: errors.append(f"duplicate case {key}")
        seen.add(key)
        if case["status"] == "refused_empty":
            if case["term"] is not None or case["candidate_id"] is not None or case["budgets"]:
                errors.append(f"empty pool fabricated an audit candidate: {key}")
            summary[case["task"]]["empty"]["refused_empty"] += 1
            continue
        term, candidate_id = case["term"], case["candidate_id"]
        if not isinstance(term, dict) or not candidate_id: errors.append(f"nonempty case lacks candidate: {key}"); continue
        for k in BUDGETS:
            budget_key = str(k)
            row = case["budgets"].get(budget_key)
            if row is None: errors.append(f"missing budget {k}: {key}"); continue
            request, evidence, receipt = row["request"], row["evidence"], row["receipt"]
            identity = {field: request.get(field) for field in
                        ("candidate_id", "term_sha256", "acquisition_sha256", "domain_sha256", "seed", "probes")}
            if request.get("request_id") != digest(identity): errors.append(f"request id mismatch: {key}/{k}")
            if request.get("candidate_id") != candidate_id or request.get("term_sha256") != digest(term):
                errors.append(f"request candidate binding mismatch: {key}/{k}")
            expected_acquisition_hash = digest({"rows": case["acquisition_rows"],
                                                "source_ids": [case["acquisition_source_id"]]})
            if request.get("acquisition_sha256") != expected_acquisition_hash:
                errors.append(f"request acquisition provenance mismatch: {key}/{k}")
            domain_inputs = [audit["env"] for audit in case["audit_rows"]]
            if request.get("domain_sha256") != digest(domain_inputs):
                errors.append(f"request audit-domain binding mismatch: {key}/{k}")
            expected_seed = f"adequacy-v1:{case['task']}:{case['rep']}"
            if request.get("seed") != expected_seed: errors.append(f"request seed mismatch: {key}/{k}")
            if len(request.get("probes", [])) != k or len(evidence) != k: errors.append(f"wrong evidence budget: {key}/{k}")
            if len({p["input_sha256"] for p in request["probes"]}) != k: errors.append(f"duplicate request descriptors: {key}/{k}")
            residuals = []
            expected_evidence = []
            status = "accepted"
            for probe, proof in zip(request["probes"], evidence):
                if proof["probe_id"] != probe["probe_id"] or proof["inputs"] != probe["inputs"]:
                    errors.append(f"evidence/request descriptor mismatch: {key}/{k}")
                if digest(probe["inputs"]) != probe["input_sha256"]: errors.append(f"input hash mismatch: {key}/{k}")
                expected_label = label(case["task"], probe["inputs"])
                if len(proof["labels"]) != 1 or proof["labels"][0]["source_id"] != f"independent-oracle:{case['task']}" or proof["labels"][0]["expected"] != expected_label:
                    errors.append(f"label provenance/oracle mismatch: {key}/{k}")
                predicted = evaluate(term, probe["inputs"])
                if predicted != expected_label:
                    status = "rejected"
                    residuals.append({"probe_id": probe["probe_id"], "input_sha256": probe["input_sha256"],
                                       "prediction": predicted, "labels": proof["labels"],
                                       "kind": "prediction_residual"})
                expected_evidence.append(proof)
            if receipt != expected_receipt(request, candidate_id, term, expected_evidence, status, residuals):
                errors.append(f"receipt independent replay mismatch: {key}/{k}")
            stats = summary[case["task"]][budget_key]
            stats[status] += 1
            stats["native_calls"] += len(evidence)
            stats["wall_seconds"] += row["adjudication_wall_seconds"]
    controls = capture["controls"]
    expected_controls = {"ambiguous_labels": "ambiguous", "incomplete_evidence": "incomplete",
                         "reused_source": "invalid", "altered_descriptor": "invalid",
                         "single_noisy_label": "rejected"}
    for name, status in expected_controls.items():
        if controls.get(name, {}).get("status") != status: errors.append(f"control status failed: {name}")
    if controls.get("tampered_request", {}).get("status") != "fail_closed": errors.append("tampered request was not rejected")
    analysis = {"schema": "SubstrateProvenanceBoundAdequacyReceiptV1Analysis", "cases": len(cases),
                "error_count": len(errors), "errors": errors,
                "task_budget_summary": {task: {budget: counts for budget, counts in budgets.items()}
                                        for task, budgets in summary.items()},
                "control_statuses": {key: value.get("status") for key, value in controls.items()},
                "interpretation": "The API binds caller-declared provenance and finite probe receipts; it does not authenticate label sources or certify behavior outside supplied probes."}
    OUT.write_text(json.dumps(analysis, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"analysis": str(OUT.relative_to(ROOT)), "cases": len(cases), "errors": len(errors), "checks_pass": not errors}, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__": raise SystemExit(main())

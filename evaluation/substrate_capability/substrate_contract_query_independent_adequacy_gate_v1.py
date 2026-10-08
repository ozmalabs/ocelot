#!/usr/bin/env python3
"""Measure a bounded fresh-label adequacy gate on frozen query captures."""
from __future__ import annotations
import hashlib, itertools, json, os, platform, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
os.environ.setdefault("OZMA_NO_LLM", "1")
RUNNER = Path(__file__).resolve()
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_CONTRACT_QUERY_INDEPENDENT_ADEQUACY_GATE_V1_PREREG_20261002.md"
ANALYZER = ROOT / "evaluation/substrate_capability/analyze_substrate_query_independent_adequacy_gate_v1.py"
LOCK = ROOT / "evaluation/substrate_capability/substrate_contract_query_independent_adequacy_gate_v1_lock_20261002.json"
RAW = ROOT / "evaluation/reports/substrate_contract_query_independent_adequacy_gate_v1_raw_20261002.json"
INPUTS = {
    "generated_pool": "evaluation/reports/substrate_contract_query_generated_pool_transfer_v1_raw_20261002.json",
    "cubic_transfer": "evaluation/reports/substrate_contract_query_generated_cubic_transfer_v1_raw_20261002.json",
    "grid_misspec": "evaluation/reports/substrate_contract_query_generated_grid_misspec_v1_raw_20261002.json",
    "cubic_alias": "evaluation/reports/substrate_contract_query_generated_cubic_alias_v1_raw_20261002.json",
}
ACTIVE = ("domains/contract_query.py", "domains/generator.py", "domains/query_selection.py",
          "domains/engine_provenance.py", "scripts/cegis_faculty_on_sum_of_n.py",
          "scripts/jabberwock_closes_the_euler_tie.py",
          "runners/dsl/src/term.rs", "runners/dsl/src/py.rs",
          "runners/dsl/python/substrate_rs/__init__.py", "runners/dsl/python/substrate_rs/_native.build.json")
BUDGETS = (0, 1, 2, 4)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def active_hashes() -> dict:
    import substrate_rs as sr
    out = {name: sha(ROOT / name) for name in ACTIVE}
    out["native"] = sha(Path(sr._native.__file__).resolve())
    return out


def parent_paths() -> dict:
    paths = dict(INPUTS)
    current_active = active_hashes()
    for name, raw_path in INPUTS.items():
        capture = json.loads((ROOT / raw_path).read_text())
        lock_filename = {
            "generated_pool": "substrate_contract_query_generated_pool_transfer_v1_lock_20261002.json",
            "cubic_transfer": "substrate_contract_query_generated_cubic_transfer_v1_lock_20261002.json",
            "grid_misspec": "substrate_contract_query_generated_grid_misspec_v1_lock_20261002.json",
            "cubic_alias": "substrate_contract_query_generated_cubic_alias_v1_lock_20261002.json",
        }[name]
        lock_path = ROOT / "evaluation/substrate_capability" / lock_filename
        paths[f"{name}_lock"] = str(lock_path.relative_to(ROOT))
        parent_lock = json.loads(lock_path.read_text())
        if capture["lock"] != parent_lock or capture["post_lock"] != parent_lock:
            raise RuntimeError(f"parent capture {name} does not match its frozen lock")
        for locked_path, expected_hash in parent_lock["files"].items():
            if sha(ROOT / locked_path) != expected_hash:
                raise RuntimeError(f"parent locked file changed: {locked_path}")
        for source_name, expected_hash in parent_lock["active"].items():
            actual_hash = current_active.get(source_name)
            if actual_hash is None:
                actual_hash = sha(ROOT / source_name)
            if actual_hash != expected_hash:
                raise RuntimeError(f"parent active source changed: {source_name}")
        for locked_path in parent_lock["files"]:
            paths[f"{name}_source_{Path(locked_path).name}"] = locked_path
    return {name: sha(ROOT / path) for name, path in paths.items()}


def payload() -> dict:
    return {"schema": "SubstrateContractQueryIndependentAdequacyGateV1Lock",
            "files": {str(path.relative_to(ROOT)): sha(path) for path in (RUNNER, ANALYZER, PROTOCOL)},
            "active": active_hashes(), "parent_inputs": parent_paths(),
            "git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
            "design": {"budgets": list(BUDGETS), "audit_order": "frozen protocol order; prefix by k",
                       "source_captures": INPUTS, "gate": "accept iff every supplied fresh labeled audit row matches"}}


def euler_descriptor(maximal_faces):
    closure = set()
    for face in maximal_faces:
        vertices = tuple(sorted(face))
        for size in range(1, len(vertices) + 1):
            closure.update(itertools.combinations(vertices, size))
    counts = {dimension: sum(len(face) == dimension + 1 for face in closure) for dimension in range(3)}
    env = {"V": counts[0], "E": counts[1], "F": counts[2], "ncells": len(maximal_faces),
           "maxface": max((len(face) for face in maximal_faces), default=0)}
    label = float(sum((-1) ** dimension * count for dimension, count in counts.items()))
    return env, label


def audit_rows(task: str) -> list[dict]:
    if task == "absolute_value": return []
    if task in ("triangular", "square", "cubic", "cubic_deep", "cubic_sparse", "cubic_alias"):
        values = (101, 137, 211, 509) if task in ("triangular", "square", "cubic", "cubic_deep", "cubic_sparse") else (2, 7, 11, 13)
        rows = []
        for value in values:
            if task == "triangular": env, answer = {"n": float(value)}, float(value * (value + 1) // 2)
            elif task == "square": env, answer = {"x": float(value)}, float(value * value)
            else: env, answer = {"x": float(value)}, float(value ** 3)
            rows.append({"name": f"audit-{value}", "env": env, "answer": answer})
        return rows
    if task == "euler":
        cases = [
            ("path-5", [[0, 1], [1, 2], [2, 3], [3, 4]]),
            ("cycle-7", [[0, 1], [1, 2], [2, 3], [3, 4], [4, 5], [5, 6], [6, 0]]),
            ("two-triangles-sharing-vertex", [[0, 1, 2], [0, 3, 4]]),
            ("three-triangles-sharing-vertex", [[0, 1, 2], [0, 3, 4], [0, 5, 6]]),
        ]
        return [{"name": name, "env": euler_descriptor(faces)[0], "answer": euler_descriptor(faces)[1]}
                for name, faces in cases]
    raise ValueError(f"no independent audit task for {task}")


def cases_from_captures() -> list[dict]:
    cases = []
    def add(capture_key, task, workers, get_pool, get_outcome):
        source_capture = json.loads((ROOT / INPUTS[capture_key]).read_text())
        for worker in workers:
            pool = get_pool(worker)
            outcome = get_outcome(worker)
            survivor_ids = outcome["survivor_ids"]
            term = pool[int(survivor_ids[0][1:])] if survivor_ids else None
            audit = audit_rows(task)
            prior_task = source_capture["lock"]["design"]["tasks"][task]
            prior_envs = {json.dumps(row["env"], sort_keys=True, separators=(",", ":"))
                          for key in ("knowns", "candidates", "heldout") for row in prior_task[key]}
            if any(json.dumps(row["env"], sort_keys=True, separators=(",", ":")) in prior_envs for row in audit):
                raise RuntimeError(f"audit descriptor overlaps captured acquisition/evaluation data: {capture_key}/{task}")
            cases.append({"capture": capture_key, "task": task, "rep": worker["rep"],
                          "term": term, "candidate_id": survivor_ids[0] if survivor_ids else None,
                          "initially_empty": not bool(survivor_ids), "audit_rows": audit})
    gp = json.loads((ROOT / INPUTS["generated_pool"]).read_text())
    add("generated_pool", "triangular", [w for w in gp["workers"] if w["task"] == "triangular"],
        lambda w: w["pool"]["term_dicts"], lambda w: w["outcomes"]["lazy_matrix"])
    add("generated_pool", "square", [w for w in gp["workers"] if w["task"] == "square"],
        lambda w: w["pool"]["term_dicts"], lambda w: w["outcomes"]["lazy_matrix"])
    add("generated_pool", "euler", [w for w in gp["workers"] if w["task"] == "euler"],
        lambda w: w["pool"]["term_dicts"], lambda w: w["outcomes"]["lazy_matrix"])
    ct = json.loads((ROOT / INPUTS["cubic_transfer"]).read_text())
    add("cubic_transfer", "cubic", ct["workers"], lambda w: w["pool"]["term_dicts"], lambda w: w["outcomes"]["lazy_matrix"])
    gm = json.loads((ROOT / INPUTS["grid_misspec"]).read_text())
    add("grid_misspec", "cubic_deep", [w for w in gm["workers"] if w["task"] == "cubic_deep"],
        lambda w: w["pool"]["term_dicts"], lambda w: w["outcomes"]["lazy_matrix"])
    add("grid_misspec", "cubic_sparse", [w for w in gm["workers"] if w["task"] == "cubic_sparse"],
        lambda w: w["pool"]["term_dicts"], lambda w: w["outcomes"]["lazy_matrix"])
    ca = json.loads((ROOT / INPUTS["cubic_alias"]).read_text())
    add("cubic_alias", "cubic_alias", ca["workers"], lambda w: w["pool"]["term_dicts"], lambda w: w["outcomes"]["lazy_matrix"])
    add("grid_misspec", "absolute_value", [w for w in gm["workers"] if w["task"] == "absolute_value"],
        lambda w: w["pool"]["term_dicts"], lambda w: w["outcomes"]["lazy_matrix"])
    return cases


def main() -> int:
    if sys.argv[1:] == ["--lock"]:
        if LOCK.exists() or RAW.exists(): raise SystemExit("refusing to overwrite lock/capture")
        LOCK.write_text(json.dumps(payload(), indent=2, sort_keys=True) + "\n")
        print(LOCK.relative_to(ROOT)); return 0
    frozen = payload()
    if not LOCK.exists() or json.loads(LOCK.read_text()) != frozen: raise SystemExit("missing or stale source/input lock")
    if RAW.exists(): raise SystemExit("refusing to overwrite capture")
    from substrate_rs import _native
    native = _native.Substrate()
    before = active_hashes()
    rows = []
    started = time.perf_counter()
    for case in cases_from_captures():
        if case["term"] is None:
            rows.append({**case, "budgets": {str(k): {"status": "refused_empty", "predictions": [], "native_calls": 0, "wall_seconds": 0.0} for k in BUDGETS}})
            continue
        budgets = {}
        for k in BUDGETS:
            predictions = []
            start = time.perf_counter()
            for audit in case["audit_rows"][:k]:
                value = native.evaluate(case["term"], audit["env"])
                predictions.append({"name": audit["name"], "native_prediction": float(value),
                                    "answer": float(audit["answer"])})
            elapsed = time.perf_counter() - start
            accepted = all(abs(row["native_prediction"] - row["answer"]) <= 1e-9 for row in predictions)
            budgets[str(k)] = {"status": "accepted" if accepted else "rejected",
                               "predictions": predictions, "native_calls": len(predictions),
                               "wall_seconds": elapsed}
        rows.append({**case, "budgets": budgets})
    after = active_hashes()
    RAW.write_text(json.dumps({"schema": "SubstrateContractQueryIndependentAdequacyGateV1Capture",
                               "lock": frozen, "post_lock": payload(), "before": before, "after": after,
                               "cases": rows, "elapsed_seconds": time.perf_counter() - started,
                               "host": {"platform": platform.platform(), "python": sys.version}},
                              indent=2, sort_keys=True, default=str) + "\n")
    print(json.dumps({"raw": str(RAW.relative_to(ROOT)), "cases": len(rows), "source_stable": before == after}))
    return 0


if __name__ == "__main__": raise SystemExit(main())

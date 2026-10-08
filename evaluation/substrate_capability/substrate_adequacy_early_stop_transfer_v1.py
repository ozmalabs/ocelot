#!/usr/bin/env python3
"""Early-stop probe selection and cross-family transfer benchmark."""
from __future__ import annotations
import hashlib, json, math, platform, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
RUNNER = Path(__file__).resolve()
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_ADEQUACY_EARLY_STOP_TRANSFER_V1_PREREG_20261002.md"
LOCK = ROOT / "evaluation/substrate_capability/substrate_adequacy_early_stop_transfer_v1_lock_20261002.json"
RAW = ROOT / "evaluation/reports/substrate_adequacy_early_stop_transfer_v1_raw_20261002.json"
REPS, BUDGETS = 30, (1, 2, 4)
ACTIVE = ("domains/independent_adequacy.py", "runners/dsl/src/term.rs",
          "runners/dsl/src/py.rs", "runners/dsl/python/substrate_rs/__init__.py",
          "runners/dsl/python/substrate_rs/_native.build.json")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def var(name="x"):
    return {"type": "Var", "name": name}


def lit(value):
    return {"type": "Lit", "value": value}


def plus(a, b):
    return {"type": "Plus", "items": [a, b]}


def minus(a, b):
    return {"type": "Minus", "a": a, "b": b}


def poly_delta():
    factors = [minus(var(), lit(i)) for i in range(1, 13)]
    result = factors[0]
    for factor in factors[1:]:
        result = {"type": "Times", "items": [result, factor]}
    return result


def poly_target(scale=1):
    delta = poly_delta()
    if scale != 1:
        delta = {"type": "Times", "items": [lit(scale), delta]}
    return plus(var(), delta)


def family_cases():
    x, y = var("x"), var("y")
    lin = var()
    p1, p2 = poly_target(1), poly_target(2)
    broad_poly = [{"x": i} for i in range(1, 14)]
    alias_poly = [{"x": i} for i in range(1, 13)]
    add, sub = plus(x, y), minus(x, y)
    broad_vec = [{"x": i, "y": 0} for i in range(31)] + [{"x": 0, "y": 1}]
    alias_vec = [{"x": i, "y": 0} for i in range(31)]
    return {
        "poly_represented_wrong": {"family": "sparse_polynomial", "candidate": lin, "target_kind": "poly1",
            "alternatives": [p1], "domain": broad_poly, "wrong": True},
        "poly_correct": {"family": "sparse_polynomial", "candidate": p1, "target_kind": "poly1",
            "alternatives": [lin], "domain": broad_poly, "wrong": False},
        "poly_omitted_target": {"family": "sparse_polynomial", "candidate": lin, "target_kind": "poly2",
            "alternatives": [p1], "domain": broad_poly, "wrong": True},
        "poly_alias_only": {"family": "sparse_polynomial", "candidate": lin, "target_kind": "poly2",
            "alternatives": [p1], "domain": alias_poly, "wrong": True},
        "vector_represented_wrong": {"family": "two_variable_arithmetic", "candidate": add, "target_kind": "subtract",
            "alternatives": [sub], "domain": broad_vec, "wrong": True},
        "vector_correct": {"family": "two_variable_arithmetic", "candidate": add, "target_kind": "add",
            "alternatives": [sub], "domain": broad_vec, "wrong": False},
        "vector_omitted_target": {"family": "two_variable_arithmetic", "candidate": add, "target_kind": "identity",
            "alternatives": [sub], "domain": broad_vec, "wrong": True},
        "vector_alias_only": {"family": "two_variable_arithmetic", "candidate": add, "target_kind": "subtract",
            "alternatives": [lin], "domain": alias_vec, "wrong": True},
    }


def target_value(kind: str, env: dict) -> float:
    x = int(env["x"])
    if kind.startswith("poly"):
        product = 1
        for root in range(1, 13): product *= x - root
        return float(x + (1 if kind == "poly1" else 2) * product)
    y = int(env["y"])
    return float(x + y if kind == "add" else x - y if kind == "subtract" else x)


def payload() -> dict:
    from substrate_rs import _native
    paths = (RUNNER, PROTOCOL, *[ROOT / p for p in ACTIVE])
    return {"schema": "SubstrateAdequacyEarlyStopTransferV1Lock",
            "files": {str(p.relative_to(ROOT)): sha(p) for p in paths},
            "native_sha256": sha(Path(_native.__file__).resolve()),
            "git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
            "design": {"repetitions": REPS, "budgets": list(BUDGETS), "cases": family_cases(),
                       "known_rows": {"polynomial": [{"x": 0}], "vector": [{"x": 0, "y": 0}]},
                       "policies": ["seeded_hash", "maximum_prediction_entropy"],
                       "early_stop": "stop after first label disagrees with candidate"}}


def canonical(env):
    return json.dumps(env, sort_keys=True, separators=(",", ":"))


def run(case_name: str, rep: int, policy: str, budget: int, spec: dict, native) -> dict:
    seed = f"early-stop-transfer-v1:{case_name}:{rep}"
    tie = lambda env: hashlib.sha256(f"{seed}:{canonical(env)}".encode()).hexdigest()
    setup_start = time.perf_counter_ns()
    hash_order = sorted(spec["domain"], key=tie)
    setup_ns = time.perf_counter_ns() - setup_start
    alternatives = list(spec["alternatives"])
    selected, trace = [], []
    selection_ns = update_ns = oracle_ns = 0
    stop_reason = "budget_exhausted"
    for index in range(min(budget, len(spec["domain"]))):
        selection_start = time.perf_counter_ns()
        remaining = [env for env in spec["domain"] if env not in selected]
        if policy == "seeded_hash":
            env = next(item for item in hash_order if item not in selected)
        else:
            def entropy(item):
                outputs = [float(native.evaluate(spec["candidate"], item))]
                outputs.extend(float(native.evaluate(h, item)) for h in alternatives)
                counts = {}
                for value in outputs: counts[value] = counts.get(value, 0) + 1
                total = len(outputs)
                return -sum((count / total) * math.log2(count / total) for count in counts.values())
            env = sorted(((entropy(item), tie(item), item) for item in remaining),
                         key=lambda row: (-row[0], row[1]))[0][2]
        selection_ns += time.perf_counter_ns() - selection_start
        oracle_start = time.perf_counter_ns()
        answer = target_value(spec["target_kind"], env)
        oracle_ns += time.perf_counter_ns() - oracle_start
        update_start = time.perf_counter_ns()
        candidate_prediction = float(native.evaluate(spec["candidate"], env))
        alternative_predictions = [float(native.evaluate(h, env)) for h in alternatives]
        match = candidate_prediction == answer
        alternatives = [h for h in alternatives if float(native.evaluate(h, env)) == answer]
        update_ns += time.perf_counter_ns() - update_start
        selected.append(env)
        trace.append({"input": env, "oracle_label": answer, "candidate_prediction": candidate_prediction,
                      "candidate_match": match, "alternative_predictions": alternative_predictions,
                      "alternatives_remaining": len(alternatives)})
        if not match:
            stop_reason = "candidate_residual"
            break
    heldout = ([{"x": x} for x in (14, 15, 16, 17)] if spec["family"] == "sparse_polynomial"
               else [{"x": x, "y": 1} for x in (1, 2, 3, 4)])
    exact = all(float(native.evaluate(spec["candidate"], env)) == target_value(spec["target_kind"], env)
                for env in heldout)
    return {"case": case_name, "family": spec["family"], "repetition": rep, "policy": policy,
            "budget": budget, "selected": selected, "trace": trace,
            "candidate_accepted": all(row["candidate_match"] for row in trace),
            "candidate_heldout_exact": exact, "labels_used": len(trace), "stop_reason": stop_reason,
            "witness_selected": any((env.get("x") == 13 if spec["family"] == "sparse_polynomial"
                                      else env.get("y") == 1) for env in selected),
            "hash_setup_ns": setup_ns, "selection_ns": selection_ns,
            "update_ns": update_ns, "oracle_label_ns": oracle_ns}


def main() -> int:
    if sys.argv[1:] == ["--lock"]:
        if LOCK.exists() or RAW.exists(): raise SystemExit("refusing to overwrite lock/capture")
        LOCK.write_text(json.dumps(payload(), indent=2, sort_keys=True) + "\n")
        print(LOCK.relative_to(ROOT)); return 0
    frozen = payload()
    if not LOCK.exists() or json.loads(LOCK.read_text()) != frozen: raise SystemExit("missing/stale source lock")
    if RAW.exists(): raise SystemExit(f"refusing to overwrite {RAW}")
    from substrate_rs import _native
    native = _native.Substrate()
    before = payload(); specs = family_cases()
    workers = [run(case, rep, policy, budget, spec, native)
               for case, spec in specs.items() for policy in ("seeded_hash", "maximum_prediction_entropy")
               for rep in range(1, REPS + 1) for budget in BUDGETS]
    after = payload()
    capture = {"schema": "SubstrateAdequacyEarlyStopTransferV1Capture", "lock": frozen,
               "post_lock": after, "source_stable": before == after, "workers": workers,
               "environment": {"platform": platform.platform(), "python": sys.version}}
    RAW.parent.mkdir(parents=True, exist_ok=True)
    RAW.write_text(json.dumps(capture, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"workers": len(workers), "source_stable": before == after,
                      "raw": str(RAW.relative_to(ROOT))}, indent=2)); return 0


if __name__ == "__main__": raise SystemExit(main())

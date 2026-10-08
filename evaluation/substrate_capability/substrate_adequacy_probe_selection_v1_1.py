#!/usr/bin/env python3
"""Sparse-witness, fixed-budget adequacy probe selection experiment."""
from __future__ import annotations
import hashlib, json, math, platform, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
RUNNER = Path(__file__).resolve()
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_ADEQUACY_PROBE_SELECTION_V1_1_PREREG_20261002.md"
LOCK = ROOT / "evaluation/substrate_capability/substrate_adequacy_probe_selection_v1_1_lock_20261002.json"
RAW = ROOT / "evaluation/reports/substrate_adequacy_probe_selection_v1_1_raw_20261002.json"
REPS, BUDGETS = 30, (1, 2, 4)
ACTIVE = ("domains/independent_adequacy.py", "runners/dsl/src/term.rs",
          "runners/dsl/src/py.rs", "runners/dsl/python/substrate_rs/__init__.py",
          "runners/dsl/python/substrate_rs/_native.build.json")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def var() -> dict:
    return {"type": "Var", "name": "x"}


def lit(n: int) -> dict:
    return {"type": "Lit", "value": n}


def product_term() -> dict:
    factors = [{"type": "Minus", "a": var(), "b": lit(i)} for i in range(1, 32)]
    result = factors[0]
    for factor in factors[1:]:
        result = {"type": "Times", "items": [result, factor]}
    return result


def add_term(scale: int) -> dict:
    product = product_term()
    if scale != 1:
        product = {"type": "Times", "items": [lit(scale), product]}
    return {"type": "Plus", "items": [var(), product]}


def cases() -> dict:
    linear = var()
    target = add_term(1)
    omitted = add_term(2)
    return {
        "represented_wrong": {"target": target, "candidate": linear, "alternatives": [target],
                              "domain": list(range(1, 33)), "wrong": True},
        "correct_adoption": {"target": target, "candidate": target, "alternatives": [linear],
                             "domain": list(range(1, 33)), "wrong": False},
        "omitted_target": {"target": omitted, "candidate": linear, "alternatives": [target],
                           "domain": list(range(1, 33)), "wrong": True},
        "finite_alias": {"target": omitted, "candidate": linear, "alternatives": [target],
                         "domain": list(range(1, 32)), "wrong": True},
    }


def payload() -> dict:
    from substrate_rs import _native
    paths = (RUNNER, PROTOCOL, *[ROOT / p for p in ACTIVE])
    return {"schema": "SubstrateAdequacyProbeSelectionV1_1Lock",
            "files": {str(p.relative_to(ROOT)): sha(p) for p in paths},
            "native_sha256": sha(Path(_native.__file__).resolve()),
            "git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
            "design": {"repetitions": REPS, "budgets": list(BUDGETS), "cases": cases(),
                       "known_rows": [{"x": 0}], "policies": ["seeded_hash", "maximum_prediction_entropy"],
                       "tie_break": "sha256(seed || canonical input)",
                       "entropy": "Shannon entropy of native predictions across candidate and active alternatives"}}


def key(env: dict) -> str:
    return json.dumps(env, sort_keys=True, separators=(",", ":"))


def label(x: int, scale: int) -> float:
    product = 1
    for root in range(1, 32):
        product *= x - root
    return float(x + scale * product)


def run(case_name: str, repetition: int, policy: str, budget: int, spec: dict, native) -> dict:
    domain = [{"x": x} for x in spec["domain"]]
    seed = f"adequacy-probe-selection-v1.1:{case_name}:{repetition}"
    tie = lambda env: hashlib.sha256(f"{seed}:{key(env)}".encode()).hexdigest()
    hash_order = sorted(domain, key=tie)
    selected, trace = [], []
    alternatives = list(spec["alternatives"])
    selection_ns = 0
    for _ in range(min(budget, len(domain))):
        start = time.perf_counter_ns()
        remaining = [env for env in domain if env not in selected]
        if policy == "seeded_hash":
            env = next(item for item in hash_order if item not in selected)
        else:
            def score(candidate_env):
                values = [float(native.evaluate(spec["candidate"], candidate_env))]
                values.extend(float(native.evaluate(term, candidate_env)) for term in alternatives)
                counts = {}
                for value in values:
                    counts[value] = counts.get(value, 0) + 1
                total = len(values)
                return -sum((n / total) * math.log2(n / total) for n in counts.values())
            env = sorted(((score(item), tie(item), item) for item in remaining),
                         key=lambda item: (-item[0], item[1]))[0][2]
        selection_ns += time.perf_counter_ns() - start
        y = label(int(env["x"]), 1 if case_name in ("represented_wrong", "correct_adoption") else 2)
        pred = float(native.evaluate(spec["candidate"], env))
        alt_preds = [float(native.evaluate(term, env)) for term in alternatives]
        selected.append(env)
        trace.append({"input": env, "oracle_label": y, "candidate_prediction": pred,
                      "candidate_match": pred == y, "alternative_predictions": alt_preds})
        alternatives = [term for term in alternatives if float(native.evaluate(term, env)) == y]
    accepted = all(row["candidate_match"] for row in trace)
    holdout = [{"x": x} for x in (33, 34, 35, 36)]
    heldout_exact = all(float(native.evaluate(spec["candidate"], env)) == label(int(env["x"]),
                              1 if case_name in ("represented_wrong", "correct_adoption") else 2)
                        for env in holdout)
    return {"case": case_name, "repetition": repetition, "policy": policy, "budget": budget,
            "selected": selected, "trace": trace, "candidate_accepted": accepted,
            "candidate_heldout_exact": heldout_exact, "labels_used": len(trace),
            "remaining_alternatives": len(alternatives), "selection_native_ns": selection_ns}


def main() -> int:
    if sys.argv[1:] == ["--lock"]:
        if LOCK.exists() or RAW.exists():
            raise SystemExit("refusing to overwrite lock or capture")
        LOCK.write_text(json.dumps(payload(), indent=2, sort_keys=True) + "\n")
        print(LOCK.relative_to(ROOT)); return 0
    frozen = payload()
    if not LOCK.exists() or json.loads(LOCK.read_text()) != frozen:
        raise SystemExit("missing or stale source/native lock")
    if RAW.exists():
        raise SystemExit(f"refusing to overwrite {RAW}")
    from substrate_rs import _native
    native = _native.Substrate()
    before = payload()
    task_cases = cases()
    rows = [run(case, rep, policy, budget, task_cases[case], native)
            for case in task_cases for policy in ("seeded_hash", "maximum_prediction_entropy")
            for rep in range(1, REPS + 1) for budget in BUDGETS]
    after = payload()
    capture = {"schema": "SubstrateAdequacyProbeSelectionV1_1Capture", "lock": frozen,
               "post_lock": after, "source_stable": before == after, "workers": rows,
               "environment": {"platform": platform.platform(), "python": sys.version}}
    RAW.parent.mkdir(parents=True, exist_ok=True)
    RAW.write_text(json.dumps(capture, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"workers": len(rows), "source_stable": before == after,
                      "raw": str(RAW.relative_to(ROOT))}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

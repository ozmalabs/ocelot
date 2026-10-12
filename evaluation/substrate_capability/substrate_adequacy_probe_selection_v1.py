#!/usr/bin/env python3
"""Compare hash sampling with target-blind challenger disagreement probes."""
from __future__ import annotations
import hashlib, json, math, platform, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
RUNNER = Path(__file__).resolve()
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_ADEQUACY_PROBE_SELECTION_V1_PREREG_20261002.md"
LOCK = ROOT / "evaluation/substrate_capability/substrate_adequacy_probe_selection_v1_lock_20261002.json"
RAW = ROOT / "evaluation/reports/substrate_adequacy_probe_selection_v1_raw_20261002.json"
REPS = 3
BUDGETS = (1, 2, 4)
ACTIVE = ("domains/independent_adequacy.py", "runners/dsl/src/term.rs",
          "runners/dsl/src/py.rs", "runners/dsl/python/substrate_rs/__init__.py",
          "runners/dsl/python/substrate_rs/_native.build.json")
CASES = {
    "represented_correct": {"target_power": 2, "candidate_power": 2, "alternatives": [1, 3, 4],
                            "domain": list(range(-8, 9))},
    "represented_wrong": {"target_power": 3, "candidate_power": 1, "alternatives": [2, 3, 4],
                          "domain": list(range(-8, 9))},
    "omitted_target": {"target_power": 5, "candidate_power": 1, "alternatives": [2, 3, 4],
                       "domain": list(range(-8, 9))},
    "singleton_alias": {"target_power": 5, "candidate_power": 1, "alternatives": [2, 3, 4],
                        "domain": [1]},
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def term(power: int) -> dict:
    value = {"type": "Var", "name": "x"}
    for _ in range(power - 1):
        value = {"type": "Times", "items": [value, {"type": "Var", "name": "x"}]}
    return value


def payload() -> dict:
    from substrate_rs import _native
    paths = (RUNNER, PROTOCOL, *[ROOT / p for p in ACTIVE])
    return {"schema": "SubstrateAdequacyProbeSelectionV1Lock",
            "files": {str(p.relative_to(ROOT)): sha(p) for p in paths},
            "native_sha256": sha(Path(_native.__file__).resolve()),
            "git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
            "design": {"repetitions": REPS, "budgets": list(BUDGETS), "cases": CASES,
                       "known_inputs": [{"x": 0}, {"x": 1}],
                       "policies": ["seeded_hash", "maximum_prediction_entropy"],
                       "entropy": "Shannon entropy of native predictions over candidate and active challengers"}}


def _key(env: dict) -> str:
    return json.dumps(env, sort_keys=True, separators=(",", ":"))


def _tie(seed: str, env: dict) -> str:
    return hashlib.sha256(f"{seed}:{_key(env)}".encode()).hexdigest()


def run(case_name: str, repetition: int, policy: str, budget: int, native) -> dict:
    spec = CASES[case_name]
    candidate = term(spec["candidate_power"])
    alternatives = {power: term(power) for power in spec["alternatives"] if power != spec["candidate_power"]}
    fresh = [{"x": x} for x in spec["domain"] if x not in (0, 1)]
    seed = f"probe-selection-v1:{case_name}:{repetition}:{budget}"
    hash_order = sorted(fresh, key=lambda env: _tie(seed, env))
    active = dict(alternatives)
    selected, predictions, timings = [], [], []
    candidate_matches = True
    for query_index in range(min(budget, len(fresh))):
        start = time.perf_counter_ns()
        if policy == "seeded_hash":
            env = next(env for env in hash_order if env not in selected)
        else:
            remaining = [env for env in fresh if env not in selected]
            def entropy(env):
                outputs = [float(native.evaluate(candidate, env))]
                outputs.extend(float(native.evaluate(hyp, env)) for hyp in active.values())
                counts = {}
                for value in outputs:
                    counts[value] = counts.get(value, 0) + 1
                total = len(outputs)
                return -sum((count / total) * math.log2(count / total) for count in counts.values())
            scored = [(entropy(env), _tie(seed, env), env) for env in remaining]
            env = sorted(scored, key=lambda item: (-item[0], item[1]))[0][2]
        select_ns = time.perf_counter_ns() - start
        label = float(int(env["x"]) ** spec["target_power"])
        candidate_prediction = float(native.evaluate(candidate, env))
        candidate_matches = candidate_matches and candidate_prediction == label
        selected.append(env)
        predictions.append({"inputs": env, "label": label, "candidate_prediction": candidate_prediction,
                            "candidate_match": candidate_prediction == label,
                            "challenger_predictions": {str(power): float(native.evaluate(hyp, env))
                                                       for power, hyp in alternatives.items()}})
        active = {power: hyp for power, hyp in active.items()
                  if float(native.evaluate(hyp, env)) == label}
        timings.append(select_ns)
    heldout = [{"x": x} for x in (-7, -5, 3, 6)]
    heldout_exact = all(float(native.evaluate(candidate, env)) == float(int(env["x"]) ** spec["target_power"])
                        for env in heldout)
    return {"case": case_name, "repetition": repetition, "policy": policy, "budget": budget,
            "selected": selected, "predictions": predictions, "candidate_accepted": candidate_matches,
            "heldout_candidate_exact": heldout_exact, "remaining_challengers": sorted(active),
            "label_calls": len(selected), "selection_native_ns": sum(timings)}


def main() -> int:
    if sys.argv[1:] == ["--lock"]:
        if LOCK.exists() or RAW.exists():
            raise SystemExit("refusing to overwrite lock or raw capture")
        LOCK.write_text(json.dumps(payload(), indent=2, sort_keys=True) + "\n")
        print(LOCK.relative_to(ROOT)); return 0
    frozen = payload()
    if not LOCK.is_file() or json.loads(LOCK.read_text()) != frozen:
        raise SystemExit("missing or stale source/native lock")
    if RAW.exists():
        raise SystemExit(f"refusing to overwrite {RAW}")
    from substrate_rs import _native
    native = _native.Substrate()
    before = payload()
    rows = [run(case, rep, policy, budget, native)
            for case in CASES for policy in ("seeded_hash", "maximum_prediction_entropy")
            for budget in BUDGETS for rep in range(1, REPS + 1)]
    after = payload()
    capture = {"schema": "SubstrateAdequacyProbeSelectionV1Capture", "lock": frozen,
               "post_lock": after, "source_stable": before == after, "workers": rows,
               "environment": {"platform": platform.platform(), "python": sys.version}}
    RAW.parent.mkdir(parents=True, exist_ok=True)
    RAW.write_text(json.dumps(capture, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"workers": len(rows), "source_stable": before == after,
                      "raw": str(RAW.relative_to(ROOT))}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

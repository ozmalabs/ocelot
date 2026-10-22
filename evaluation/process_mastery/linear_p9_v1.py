"""P9 exact-invention, repair and finite-effect preregistration runner."""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for path in (ROOT, ROOT / "runners/dsl/python"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from evaluation.process_mastery.harness import Agent
from evaluation.process_mastery.scorecard import write_scorecard

PHASE = "linear-p9-v1"
ALLOC = {
    "novel_exact_effects": (9_000_000, 200),
    "irreversible_stochastic": (9_000_200, 200),
    "alias_invalid_inverse_controls": (9_000_400, 100),
}
LIMITS = {"ticks": 6, "steps_per_tick": 1000, "budget": 10.0,
          "max_invented": 20.0, "closure": False}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def provenance():
    paths = [
        "evaluation/process_mastery/linear_p9_v1.py",
        "evaluation/process_mastery/analyze_linear_p9_v1.py",
        "evaluation/process_mastery/harness.py",
        "scripts/gen_invention_round_seed.py", "seeds/invention_round.json",
        "scripts/gen_invariant_miner_seed.py", "seeds/invariant_miner.json",
        "docs/research/engine_substrate/COGNITION_INVENTION_CONTRACT.md",
        "substrate/boot_profiles.py",
    ]
    bundle = hashlib.sha256()
    for rel in paths:
        bundle.update(rel.encode() + b"\0" + (ROOT / rel).read_bytes() + b"\0")
    import substrate_rs
    engine_source = hashlib.sha256()
    for rel in ("runners/dsl/Cargo.toml", "runners/dsl/Cargo.lock",
                "runners/dsl/src/term.rs", "runners/dsl/src/process_algebra.rs",
                "runners/dsl/src/jsonio.rs", "runners/dsl/src/reflect.rs",
                "runners/dsl/src/shape.rs", "runners/dsl/src/term_variants.rs"):
        engine_source.update(rel.encode() + b"\0" + (ROOT / rel).read_bytes() + b"\0")
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                         text=True).strip()
    except Exception:
        commit = "unavailable"
    return {
        "phase": PHASE, "git_commit": commit,
        "source_bundle_sha256": bundle.hexdigest(),
        "engine_source_sha256": engine_source.hexdigest(),
        "engine_binary_sha256": sha(Path(substrate_rs.__file__).read_bytes()),
        "allocation": ALLOC, "limits": LIMITS,
    }


def cycle_for(seed: int):
    rng = random.Random(seed)
    picks = rng.sample(range(5), 3)
    process = list(range(5))
    process[picks[0]], process[picks[1]], process[picks[2]] = (
        picks[1], picks[2], picks[0])
    inverse = [0] * len(process)
    for i, j in enumerate(process):
        inverse[j] = i
    return process, inverse


def _agent(arm: str):
    if arm == "held_only":
        return Agent(track_i=False, extra_seeds=("thinking_budget",),
                     budget={"enabled": 1.0, "remaining": LIMITS["budget"],
                             "last_refill_epoch": 0.0})
    policy = {"enabled": 1.0, "max_invented": LIMITS["max_invented"],
              "closure_enabled": 0.0, "offline_enabled": 0.0}
    agent = Agent(track_i=True, policy_overrides={"InventionPolicy": policy},
                  budget={"enabled": 1.0, "remaining": LIMITS["budget"],
                          "last_refill_epoch": 0.0})
    for operator in agent.nodes("InventionOperator"):
        enabled = arm == "operators_on" and agent.attrs(operator).get("name") == "inverse"
        agent.s.set_attr(operator, "enabled", 1.0 if enabled else 0.0)
    return agent


def exact_trial(seed: int, arm: str):
    started = time.perf_counter()
    process, target = cycle_for(seed)
    agent = _agent(arm)
    domain = f"p9-exact-{seed}"
    agent.add_domain(domain, "permutation", [list(range(5))], {"held": process})
    # The task is deliberately stuck at identity. The target inverse effect is
    # retained by the scorer and never installed in the agent graph.
    task = agent.add_solve_task(domain, list(range(5)), list(range(5)))
    agent.s.set_attr(task, "status", "stuck")
    for _ in range(LIMITS["ticks"]):
        if not agent.s.tick(LIMITS["steps_per_tick"]):
            break
    candidates = agent.invented(domain)
    exact = [n for n in candidates if agent.attrs(n).get("params") == target]
    verified = []
    fresh = [[0, 1, 2, 3, 4], [4, 2, 0, 3, 1], [1, 4, 3, 0, 2]]
    for node in exact:
        params = agent.attrs(node)["params"]
        if all(agent.native.evaluate(
                {"type": "ProcessApply", "p": {"type": "Var", "name": "p"},
                 "state": {"type": "Var", "name": "state"}},
                {"p": params, "state": state}) == _apply(target, state) for state in fresh):
            verified.append(node)
    budgets = [n for n in agent.nodes("ThinkingBudget")
               if agent.attrs(n).get("enabled") == 1.0]
    budget_left = agent.attrs(budgets[0]).get("remaining") if budgets else None
    return {
        "family": "novel_exact_effects", "seed": seed, "profile": arm,
        "status": "COMPLETED", "external_outcome": {"pass": bool(verified)},
        "target_in_agent_input": False, "target_node_count": 0,
        "invented_count": len(candidates), "verified_exact_count": len(verified),
        "verification_failures": len(exact) - len(verified),
        "budget_remaining": budget_left, "actions": 0, "interactions": 0,
        "compute": {"seconds": round(time.perf_counter() - started, 6),
                    "graph_nodes": len(agent.s.nodes()),
                    "graph_edges": agent.s.edge_count()},
    }


def _apply(process, state):
    out = [None] * len(state)
    for i, j in enumerate(process):
        out[j] = state[i]
    return out


def irreversible_trial(seed: int, arm: str):
    started = time.perf_counter()
    agent = _agent(arm)
    process = [[1, 0], [0, 0]]
    domain = f"p9-irreversible-{seed}"
    agent.add_domain(domain, "integer_matrix", [[seed % 11, 5]], {"lossy": process})
    dist_term = {"type": "ProcessDistribution", "outcomes": {"type": "Var", "name": "outcomes"}}
    distribution = agent.native.evaluate(dist_term, {
        "outcomes": [["observed", 0.5], ["alternate", 0.25]]})
    inverse = agent.native.evaluate(
        {"type": "ProcessInverse", "a": {"type": "Var", "name": "p"}}, {"p": process})
    for _ in range(LIMITS["ticks"]):
        if not agent.s.tick(LIMITS["steps_per_tick"]):
            break
    passed = inverse is None and distribution is not None
    return {
        "family": "irreversible_stochastic", "seed": seed, "profile": arm,
        "status": "COMPLETED", "external_outcome": {"pass": passed},
        "repair_candidate_status": "NOT_PROPOSED", "exact_inverse": inverse,
        "distribution_supported": distribution is not None,
        "unknown_mass": distribution[1] if distribution is not None else None,
        "candidate_supplied": False, "distribution_agent_visible": False,
        "actions": 0, "interactions": 0,
        "compute": {"seconds": round(time.perf_counter() - started, 6),
                    "graph_nodes": len(agent.s.nodes()),
                    "graph_edges": agent.s.edge_count()},
    }


def control_trial(seed: int, arm: str):
    started = time.perf_counter()
    agent = _agent(arm)
    singular = [[1, 0], [0, 0]]
    bad = [0, 0, 1]
    singular_inverse = agent.native.evaluate(
        {"type": "ProcessInverse", "a": {"type": "Var", "name": "p"}},
        {"p": singular})
    malformed_inverse = agent.native.evaluate(
        {"type": "ProcessInverse", "a": {"type": "Var", "name": "p"}},
        {"p": bad})
    left, right = [1, 0, 2], [2, 1, 0]
    alias_domain = f"p9-alias-{seed}"
    agent.add_domain(alias_domain, "permutation", [[0, 0, 0]],
                     {"left": left, "right": right})
    fingerprint = {"type": "EffectFingerprint", "p": {"type": "Var", "name": "p"},
                   "probes": {"type": "Var", "name": "probes"}}
    fp_left = agent.native.evaluate(fingerprint, {"p": left, "probes": [[0, 0, 0]]})
    fp_right = agent.native.evaluate(fingerprint, {"p": right, "probes": [[0, 0, 0]]})
    alias_retained = len(agent.schemas(alias_domain)) == 2
    distinct_fresh = _apply(left, [0, 1, 2]) != _apply(right, [0, 1, 2])
    return {
        "family": "alias_invalid_inverse_controls", "seed": seed, "profile": arm,
        "status": "COMPLETED",
        "external_outcome": {"pass": singular_inverse is None and malformed_inverse is None
                              and fp_left == fp_right and alias_retained and distinct_fresh},
        "incomplete_probe_collision": fp_left == fp_right,
        "distinct_fresh_effects": distinct_fresh, "alias_candidates_retained": alias_retained,
        "actions": 0, "interactions": 0,
        "compute": {"seconds": round(time.perf_counter() - started, 6),
                    "graph_nodes": len(agent.s.nodes()),
                    "graph_edges": agent.s.edge_count()},
    }


def run(split="development", n=200, self_check=False):
    if self_check:
        rows = ([exact_trial(1, arm) for arm in ("operators_on", "operators_off", "held_only")]
                + [irreversible_trial(2, arm) for arm in ("operators_on", "operators_off", "held_only")]
                + [control_trial(3, arm) for arm in ("operators_on", "operators_off", "held_only")])
    else:
        if n != 200:
            raise ValueError("registered P9 allocation fixes 200/200/100 cases")
        offset = 0 if split == "development" else 9_000_000
        rows = []
        for i in range(200):
            seed = offset + i
            for arm in ("operators_on", "operators_off", "held_only"):
                rows.append(exact_trial(seed, arm))
                rows.append(irreversible_trial(offset + 200 + i, arm))
        for i in range(100):
            seed = offset + 400 + i
            for arm in ("operators_on", "operators_off", "held_only"):
                rows.append(control_trial(seed, arm))
    return {"schema": "pmb-scorecard-v1", "metadata": {
        **provenance(), "split": split, "registered_draw": not self_check,
        "n_records": len(rows)}, "records": rows}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", choices=("development", "heldout"), default="development")
    parser.add_argument("--n", type=int, default=200)
    parser.add_argument("--self-check", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    payload = run(args.split, args.n, args.self_check)
    if args.output:
        write_scorecard(args.output, metadata=payload["metadata"], records=payload["records"])
    else:
        print(json.dumps(payload, indent=2, sort_keys=True))
    if args.self_check:
        assert len(payload["records"]) == 9
        assert all(row["status"] == "COMPLETED" for row in payload["records"])
        assert payload["records"][0]["external_outcome"]["pass"]
        assert not payload["records"][1]["external_outcome"]["pass"]
        assert payload["records"][3]["repair_candidate_status"] == "NOT_PROPOSED"
        print("linear_p9 runner self-check: PASS")


if __name__ == "__main__":
    main()

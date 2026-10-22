"""Frozen-mechanics PMB Phase 10 runner (development and registered draw).

The runner supplies deterministic worlds and reads outcomes. Process choice,
invention and strategy replay remain in graph rules; unsupported arm/family
pairs are retained as UNSUPPORTED instead of replaced with Python search.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
for path in (ROOT, ROOT / "runners/dsl/python"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from evaluation.process_mastery import generators as gen  # noqa: E402
from evaluation.process_mastery.harness import Agent  # noqa: E402
from evaluation.process_mastery.puzzle_worlds import cube_task, sliding_task  # noqa: E402
from evaluation.process_mastery.scorecard import write_scorecard  # noqa: E402
import substrate_rs  # noqa: E402

PHASE = "linear-p10-v1"
LIMITS = {"max_ticks": 80, "max_steps_per_tick": 4000, "budget": 10.0}
ARMS = ("baseline", "greedy", "discovered_strategy", "primitive_search")
BLOCKS = {
    "loopover3": (11_000_000, 200), "loopover4": (11_000_200, 200),
    "tool_goal": (11_000_400, 200), "cube": (11_000_600, 200),
    "sliding": (11_000_800, 200), "controls": (11_001_000, 100),
}


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _provenance():
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                         text=True).strip()
    except Exception:
        commit = "unavailable"
    paths = [
        "evaluation/process_mastery/linear_p10_v1.py",
        "evaluation/process_mastery/analyze_linear_p10_v1.py",
        "evaluation/process_mastery/harness.py",
        "evaluation/process_mastery/generators.py",
        "evaluation/process_mastery/puzzle_worlds.py",
        "substrate/boot_profiles.py", "seeds/process_schema.json",
        "seeds/invention_round.json", "seeds/invariant_miner.json",
        "seeds/process_solving.json", "seeds/process_lifting.json",
        "seeds/goal_invention.json", "seeds/strategy_discovery.json",
    ]
    bundle = hashlib.sha256()
    for rel in paths:
        bundle.update(rel.encode() + b"\0" + (ROOT / rel).read_bytes() + b"\0")
    engine = hashlib.sha256()
    for rel in ("runners/dsl/Cargo.toml", "runners/dsl/Cargo.lock",
                "runners/dsl/src/process_algebra.rs", "runners/dsl/src/term.rs",
                "runners/dsl/src/eval.rs", "runners/dsl/src/engine.rs"):
        file = ROOT / rel
        if file.exists():
            engine.update(rel.encode() + b"\0" + file.read_bytes() + b"\0")
    return {"phase": PHASE, "git_commit": commit,
            "source_bundle_sha256": bundle.hexdigest(),
            "runner_sha256": _sha(Path(__file__).read_bytes()),
            "analyzer_sha256": _sha((ROOT / "evaluation/process_mastery/analyze_linear_p10_v1.py").read_bytes()),
            "engine_source_sha256": engine.hexdigest(),
            "engine_binary_sha256": _sha(Path(substrate_rs.__file__).read_bytes()),
            "python": sys.version.split()[0], "limits": dict(LIMITS)}


def _unsupported(family, seed, arm, split, reason, task_data=None):
    return Agent.trial_record("UNSUPPORTED", family=family, seed=seed,
                              profile=arm, split=split, reason=reason,
                              task_id=f"{family}-{seed}",
                              initial_state=task_data.get("initial") if task_data else None,
                              goal=task_data.get("goal") if task_data else None,
                              outcome=None, compute=None)


def _world(family, seed):
    if family == "loopover3":
        return {"kind": "permutation", "domain": f"loopover3-{seed}",
                "probes": [list(range(9))], "held": gen.loopover_moves(3),
                "initial": gen.loopover_scramble(3, seed, length=30), "goal": list(range(9))}
    if family == "loopover4":
        return {"kind": "permutation", "domain": f"loopover4-{seed}",
                "probes": [list(range(16))], "held": gen.loopover_moves(4),
                "initial": gen.loopover_scramble(4, seed, length=30), "goal": list(range(16))}
    if family == "cube":
        task = cube_task(seed, length=20)
        return {"kind": "permutation", "domain": f"cube-{seed}",
                "probes": [list(range(24))], "held": task["primitive_affordances"],
                "initial": list(task["initial_state"]), "goal": list(task["goal_state"])}
    if family == "tool_goal":
        task = gen.tool_goal_task(seed)
        return {"kind": "permutation", "domain": f"tool-goal-{seed}",
                "probes": [list(range(4))], "held": task["primitive_affordances"],
                "initial": list(task["initial_state"]), "goal": list(task["goal_state"])}
    if family == "sliding":
        task = sliding_task(seed, length=30)
        return {"kind": "permutation", "domain": f"sliding-{seed}",
                "probes": [list(range(9))], "held": task["primitive_affordances"],
                "initial": list(task["initial_state"]), "goal": list(task["goal_state"])}
    return None


def _agent_for(arm):
    policies = {
        "SolverPolicy": {"enabled": 1.0, "max_steps": 400.0},
        "InventionPolicy": {"enabled": 0.0},
        "InvariantMinerPolicy": {"enabled": 0.0},
        "ProcessSchemaPolicy": {"enabled": 0.0},
    }
    extra = ()
    if arm == "discovered_strategy":
        extra = ("process_lifting", "goal_invention", "strategy_discovery")
        policies["StrategyDiscoveryPolicy"] = {"enabled": 1.0}
        policies["GoalInventionPolicy"] = {"enabled": 1.0, "targeted_enabled": 1.0}
        policies["ProcessLiftingPolicy"] = {"enabled": 1.0}
        policies["InventionPolicy"] = {"enabled": 1.0, "max_invented": 40.0,
                                        "closure_enabled": 0.0, "offline_enabled": 0.0}
    return Agent(track_i=True, extra_seeds=extra, profile=f"p10-{arm}",
                 policy_overrides=policies,
                 budget={"enabled": 1.0, "remaining": LIMITS["budget"],
                         "refill_per_epoch": 0.0, "last_refill_epoch": 0.0})


def _run_task(family, seed, arm, split):
    started = time.perf_counter()
    task_data = _world(family, seed)
    if family == "sliding":
        return _unsupported(family, seed, arm, split,
                            "native solver has no state-dependent blank-adjacency precondition", task_data)
    if arm == "baseline":
        return _unsupported(family, seed, arm, split,
                            "Track-I-free baseline has no registered native process solver", task_data)
    if arm == "primitive_search":
        return _unsupported(family, seed, arm, split,
                            "planner requires receipt-backed TransitionHypothesis transitions; no adapter for this panel",
                            task_data)
    agent = _agent_for(arm)
    before = len(agent.s.nodes())
    agent.add_domain(task_data["domain"], task_data["kind"], task_data["probes"], task_data["held"])
    task = agent.add_solve_task(task_data["domain"], task_data["initial"], task_data["goal"],
                                pmb_seed=seed, pmb_family=family)
    run = agent.run(max_ticks=LIMITS["max_ticks"], max_steps=LIMITS["max_steps_per_tick"])
    attrs = agent.attrs(task)
    solved = attrs.get("status") == "solved" and attrs.get("state") == attrs.get("goal")
    status = "COMPLETED" if solved else "FAILED" if run["quiescent"] else "TIMEOUT"
    schemas = {n: agent.attrs(n) for n in agent.nodes("ProcessSchema")}
    trace = attrs.get("trace", [])
    trace_is_graph = all(n in schemas for n in trace)
    no_answer_fields = all(not any(key in row for key in ("solution", "scramble_path", "answer"))
                           for row in [attrs, *schemas.values()])
    if not trace_is_graph or not no_answer_fields:
        status = "FAILED"
    strategy_n = len(agent.nodes("DiscoveredStrategy"))
    record = agent.trial_record(
        status, family=family, seed=seed, split=split, profile=arm,
        task_id=f"{family}-{seed}", initial_state=task_data["initial"], goal=task_data["goal"],
        outcome="solved" if solved else "unsolved", steps=attrs.get("steps"),
        process_trace=[{"node": str(n), "name": schemas[n].get("name"),
                        "provenance": schemas[n].get("provenance")} for n in trace],
        discovered_strategies=strategy_n,
        input_audit={"answer_fields_absent": no_answer_fields,
                     "trace_nodes_are_graph_schemas": trace_is_graph,
                     "task_has_initial_goal_only": True},
        observation={"state": attrs.get("state"), "status": attrs.get("status")},
        compute={"ticks": run["ticks"], "quiescent": run["quiescent"],
                 "seconds": round(time.perf_counter() - started, 6),
                 "graph_nodes_added": len(agent.s.nodes()) - before,
                 "max_steps_per_tick": LIMITS["max_steps_per_tick"]})
    return record


def _tool_control(seed, split):
    # A noninvertible process is a misleading precondition control: the target
    # inverse evaluator must return unknown and request a tool rather than mint.
    agent = Agent(track_i=True, extra_seeds=("goal_invention",),
                  policy_overrides={"GoalInventionPolicy": {"enabled": 1.0, "targeted_enabled": 1.0},
                                    "InventionPolicy": {"enabled": 0.0}},
                  budget={"enabled": 1.0, "remaining": LIMITS["budget"],
                          "refill_per_epoch": 0.0, "last_refill_epoch": 0.0})
    domain = f"control-{seed}"
    agent.add_domain(domain, "opaque", [[0, 1]], {"misleading": [0, 0]})
    task = agent.add_solve_task(domain, [0, 1], [1, 0], pmb_seed=seed)
    run = agent.run(max_ticks=8, max_steps=1000)
    interfaces = agent.nodes("SynthesisInterfaceRequest")
    candidates = [n for n in agent.nodes("ProcessSchema")
                  if agent.attrs(n).get("provenance") == "goal_targeted_inverse"]
    passed = bool(interfaces) and not candidates
    return agent.trial_record("COMPLETED" if passed else "FAILED", family="control",
                              seed=seed, split=split, profile="discovered_strategy",
                              control="noninvertible_misleading_precondition",
                              interface_status=agent.attrs(interfaces[0]).get("status") if interfaces else None,
                              candidate_count=len(candidates), ticks=run["ticks"])


def run(*, split: str, n: int = 200, self_check=False):
    if n != 200 and not self_check:
        raise ValueError("registered P10 panels fix n=200")
    count = 1 if self_check else n
    offset = 0 if split == "development" else 1_000_000
    families = ("loopover3", "loopover4", "tool_goal", "cube", "sliding")
    rows = []
    for family in families:
        start = BLOCKS[family][0] - 11_000_000 + offset
        for i in range(count):
            seed = start + i
            for arm in ARMS:
                rows.append(_run_task(family, seed, arm, split))
    controls = 3 if self_check else BLOCKS["controls"][1]
    control_start = BLOCKS["controls"][0] - 11_000_000 + offset
    rows.extend(_tool_control(control_start + i, split) for i in range(controls))
    metadata = {**_provenance(), "split": split, "arms": list(ARMS),
                "seed_blocks": {k: {"start": v[0] - 11_000_000 + offset,
                                     "count": v[1] if not self_check else 1}
                                for k, v in BLOCKS.items()},
                "limitations": {"tool_goal": "graph-internal simulator only; no external action sink",
                                "sliding": "state-dependent legal action precondition unsupported",
                                "baseline": "no Track-I-free native process solver",
                                "primitive_search": "no receipt-backed transition adapter"},
                "self_check": bool(self_check)}
    return {"schema": "pmb-scorecard-v1", "metadata": metadata, "records": rows}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", choices=("development", "heldout"), default="heldout")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--n", type=int, default=200)
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args()
    payload = run(split=args.split, n=args.n, self_check=args.self_check)
    if args.output:
        write_scorecard(args.output, metadata=payload["metadata"], records=payload["records"])
    else:
        print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

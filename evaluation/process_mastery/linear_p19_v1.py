"""P19 matched-arm adapter for bounded process search in finite worlds."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import random
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
for path in (ROOT, ROOT / "runners/dsl/python", ROOT / "scripts"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from evaluation.process_mastery.linear_p19_worlds import FAMILIES, TASK_KINDS, generate_task
from evaluation.process_mastery.native_primitive_search import search_and_execute

PHASE = "linear-p19-v1"
BASE_SEED = 29_000_000  # 10m + phase 19 * 1m; disjoint P19 split/control blocks below
HELDOUT_OFFSET = 200_000
CONTROL_OFFSET = 100_000
DEVELOPMENT_N = 8
HELDOUT_PER_CELL = 200
CONTROL_N = 100
PRIMITIVE_CAP = 8
MODEL_QUERY_CAP = 4_096
MAX_DEPTH = 5
MAX_PATH_ARRIVALS = 10_000


def allocation(split: str):
    """Return the complete deterministic phase allocation without drawing it."""
    if split not in {"development", "heldout"}:
        raise ValueError("split must be development or heldout")
    offset = HELDOUT_OFFSET if split == "heldout" else 0
    tasks = []
    for family_ix, family in enumerate(FAMILIES):
        for kind_ix, task_kind in enumerate(TASK_KINDS):
            start = BASE_SEED + offset + family_ix * 20_000 + kind_ix * 10_000
            count = DEVELOPMENT_N if split == "development" else HELDOUT_PER_CELL
            tasks.extend({"family": family, "task_kind": task_kind,
                          "seed": start + draw} for draw in range(count))
    control_base = BASE_SEED + offset + CONTROL_OFFSET
    control_kinds = (("impossible_goal", 34), ("illegal_action", 33),
                     ("precondition_failure", 33))
    controls = []
    index = 0
    for kind, count in control_kinds:
        controls.extend({"kind": kind, "seed": control_base + index + i}
                        for i in range(count))
        index += count
    return {"split": split, "tasks": tasks, "controls": controls}


def _greedy_action(world):
    """Measured one-step Hamming greedy policy with a stable action tie-break."""
    state = tuple(world.state)
    goal = tuple(world.goal)
    actions = world.legal_actions(state)
    if not actions:
        return None, 0
    ranked = []
    for action in actions:
        next_state = world._apply_action(state, action)
        distance = sum(left != right for left, right in zip(next_state, goal))
        ranked.append((distance, action))
    return min(ranked)[1], len(ranked)


def run_greedy(task, world, *, primitive_cap=PRIMITIVE_CAP,
               model_query_cap=MODEL_QUERY_CAP):
    started = time.perf_counter()
    primitives = queries = 0
    receipts = []
    while tuple(world.state) != tuple(world.goal) and primitives < primitive_cap:
        action, cost = _greedy_action(world)
        queries += cost
        if action is None or queries > model_query_cap:
            break
        receipt = world.transition(world.state, action)
        if not world.verify_receipt(receipt):
            raise RuntimeError("greedy arm received an invalid world receipt")
        receipts.append(receipt)
        primitives += len(receipt["applied_actions"])
    solved = tuple(world.state) == tuple(world.goal)
    return {"status": "COMPLETED" if solved else "UNSOLVED", "solved": solved,
            "primitives": primitives, "model_queries": queries, "receipts": receipts,
            "task_seconds": time.perf_counter() - started}


def run_native_primitive(task, world, *, primitive_cap=PRIMITIVE_CAP,
                         model_query_cap=MODEL_QUERY_CAP):
    started = time.perf_counter()
    primitives = queries = 0
    receipts = []
    remaining = float(model_query_cap)
    while tuple(world.state) != tuple(world.goal) and primitives < primitive_cap:
        current = dict(task)
        current["initial_state"] = list(world.state)
        current["goal_state"] = list(world.goal)
        native_data = world.native_task(task)
        native_data["initial_state"] = list(world.state)
        current.update(native_data)
        result = search_and_execute(current, world=world, remaining=remaining,
                                    depth_limit=MAX_DEPTH,
                                    max_path_arrivals=MAX_PATH_ARRIVALS)
        if result.get("status") != "COMPLETED":
            break
        receipt = result["receipt"]
        if not world.verify_receipt(receipt):
            raise RuntimeError("native primitive-search arm received an invalid receipt")
        spent = int(result.get("expanded", 0))
        queries += spent
        remaining -= spent
        if queries > model_query_cap:
            raise RuntimeError("native primitive-search exceeded the frozen model-query cap")
        receipts.append(receipt)
        primitives += len(receipt["applied_actions"])
    solved = tuple(world.state) == tuple(world.goal)
    return {"status": "COMPLETED" if solved else "UNSOLVED", "solved": solved,
            "primitives": primitives, "model_queries": queries, "receipts": receipts,
            "task_seconds": time.perf_counter() - started}


def run_trial(family: str, task_kind: str, seed: int, arm: str):
    task, world, _hidden_witness = generate_task(family, task_kind, seed)
    if arm == "measured_greedy":
        result = run_greedy(task, world)
    elif arm == "native_primitive_search":
        result = run_native_primitive(task, world)
    else:
        raise ValueError(f"unsupported P19 comparator arm: {arm}")
    return {"phase": PHASE, "family": family, "task_kind": task_kind,
            "seed": int(seed), "arm": arm, "world_sha256": world.task_digest(task),
            **result}


def run_control(kind: str, seed: int):
    task, world, _ = generate_task("irreversible_objects", "multi_step_constraint", seed)
    before = tuple(world.state)
    if kind == "impossible_goal":
        world.goal = (2, 2, 2, 2)
        if any(tuple(state) == world.goal for state in world.transition_graph()["states"]):
            raise RuntimeError("impossible-goal control is reachable")
    elif kind == "illegal_action":
        receipt = world.transition_sequence(("not_a_primitive",))
        if receipt.get("status") != "rejected" or tuple(world.state) != before:
            raise RuntimeError("illegal-action control mutated the world")
    elif kind == "precondition_failure":
        receipt = world.transition_sequence(("seal_0",))
        if receipt.get("status") != "rejected" or tuple(world.state) != before:
            raise RuntimeError("precondition control mutated the world")
    else:
        raise ValueError(f"unsupported P19 control: {kind}")
    return {"kind": kind, "seed": seed, "status": "PASS",
            "state_unchanged": tuple(world.state) == before,
            "world_sha256": world.task_digest(task)}


def self_check():
    cases = []
    for item in allocation("development")["tasks"]:
        task, world, witness = generate_task(item["family"], item["task_kind"], item["seed"])
        greedy = run_greedy(task, world)
        task, world, _ = generate_task(item["family"], item["task_kind"], item["seed"])
        native = run_native_primitive(task, world)
        cases.append({"family": item["family"], "task_kind": item["task_kind"],
                      "seed": item["seed"], "witness_length": len(witness),
                      "greedy_solved": greedy["solved"], "greedy_primitives": greedy["primitives"],
                      "greedy_model_queries": greedy["model_queries"],
                      "native_primitive_search_solved": native["solved"],
                      "native_primitives": native["primitives"],
                      "native_model_queries": native["model_queries"]})
        if not native["solved"]:
            raise RuntimeError(f"native comparator failed development task {item}")
        if native["primitives"] > PRIMITIVE_CAP or native["model_queries"] > MODEL_QUERY_CAP:
            raise RuntimeError(f"native comparator exceeded frozen caps on {item}")
    controls = [run_control(control["kind"], control["seed"])
                for control in allocation("development")["controls"]]
    return {"phase": PHASE, "status": "PASS", "development_cases": cases,
            "allocation_counts": {"tasks": len(allocation("development")["tasks"]),
                                  "controls": len(allocation("development")["controls"])},
            "controls": controls}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-check", action="store_true")
    parser.add_argument("--split", choices=("development", "heldout"))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.self_check:
        result = self_check()
    elif args.split:
        # Sealed allocation access is intentionally unavailable until a
        # standalone preregistration has been committed and verified.
        raise SystemExit("P19 split execution is disabled until preregistration freeze")
    else:
        parser.error("select --self-check or --split")
    encoded = json.dumps(result, sort_keys=True, indent=2, default=list)
    if args.output:
        args.output.write_text(encoded + "\n")
    else:
        print(encoded)


if __name__ == "__main__":
    main()

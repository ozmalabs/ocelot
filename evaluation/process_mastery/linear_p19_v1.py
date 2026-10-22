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
from evaluation.process_mastery.linear_p19_worlds import expression_actions
from evaluation.process_mastery.native_primitive_search import search_and_execute
from evaluation.process_mastery.native_process_execution import (
    attest_open_process_candidate,
    execute_open_process_candidate,
    params_digest,
)
from substrate.boot_profiles import boot_cognition_on

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
MAX_NATIVE_TICKS = 64
MAX_NATIVE_STEPS = 10_000


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


def _graph_nodes(agent, kind):
    return [node for node in agent.s.nodes()
            if agent.s.node(node)["type"] == kind]


def _edge(agent, source, label, target):
    agent.inner.add_edge_unchecked(source, label, target, {})


def _settle(agent):
    for _ in range(MAX_NATIVE_TICKS):
        if agent.inner.run_rules(MAX_NATIVE_STEPS) == 0:
            return
    raise RuntimeError("P19 invention graph failed to reach a fixpoint")


def run_invention(task, world, *, approval_provider=None,
                  approval_source="candidate_specific_provider", unseen_binding=None):
    """Run generic graph search; execute only with an exact approval callback.

    The development self-check uses an explicitly labeled local approval
    fixture. A normal caller must provide a candidate-specific approval
    provider; missing approval leaves the proposal non-actionable.
    """
    started = time.perf_counter()
    agent = boot_cognition_on()
    try:
        for kind in ("OpenProcessSearchPolicy", "OpenProcessAdoptionPolicy"):
            nodes = _graph_nodes(agent, kind)
            if len(nodes) != 1:
                raise RuntimeError(f"P19 cognition profile missing unique {kind}")
            agent.inner.set_attr(nodes[0], "enabled", 1.0)
        for kind in ("ProcessSchemaPolicy", "InventionPolicy", "InvariantMinerPolicy",
                     "SolverPolicy"):
            for node in _graph_nodes(agent, kind):
                agent.inner.set_attr(node, "enabled", 0.0)
        for node in _graph_nodes(agent, "StrategyDiscoveryPolicy"):
            agent.inner.set_attr(node, "enabled", 1.0)
            agent.inner.set_attr(node, "allow_lift", 1.0)
        budgets = list(agent.inner.neighbours(agent.agent, "has_thinking_budget"))
        if len(budgets) != 1:
            raise RuntimeError("P19 invention requires one shared ThinkingBudget")
        budget = budgets[0]
        for key, value in {"enabled": 1.0, "capacity": 20_000.0,
                           "capacity_ceiling": 20_000.0, "remaining": 20_000.0,
                           "refill_per_epoch": 0.0, "last_refill_epoch": -1000.0}.items():
            agent.inner.set_attr(budget, key, value)
        domain_name = f"p19-{task['family']}-{task['seed']}"
        domain_kind = "permutation" if task["family"] == "permutation" else "integer_vector"
        probes = [list(range(len(task["initial_state"]))),
                  list(task["initial_state"]), list(task["goal_state"])]
        domain = agent.s.add_node("ProcessDomain", {
            "name": domain_name, "kind": domain_kind,
            "probes": probes, "source_epoch": 0.0, "model_epoch": 0.0,
            "frame_epoch": 0.0, "probe_epoch": 0.0})
        _edge(agent, agent.agent, "has_process_domain", domain)
        held = {}
        for index, (name, params) in enumerate(sorted(task["primitive_affordances"].items())):
            source_digest = params_digest(params)
            schema = agent.s.add_node("ProcessSchema", {
                "name": name, "kind": domain_kind,
                "domain_kind": domain_kind, "domain": domain_name,
                "params": params, "cost": 1.0, "status": "active",
                "provenance": "world_affordance", "source_digest": source_digest,
                "source_epoch": 0.0, "model_epoch": 0.0, "frame_epoch": 0.0})
            _edge(agent, agent.agent, "has_process_schema", schema)
            _edge(agent, domain, "has_held_process", schema)
            held[name] = schema
        solve_task = agent.s.add_node("SolveTask", {
            "domain": domain_name, "initial_state": list(task["initial_state"]),
            "state": list(task["initial_state"]), "object_count": float(len(task["initial_state"])),
            "goal": list(task["goal_state"]), "status": "stuck", "trace": [],
            "steps": 0, "moves": 0.0, "stuck_count": 1})
        _edge(agent, agent.agent, "has_solve_task", solve_task)
        _edge(agent, solve_task, "about_domain", domain)
        _settle(agent)
        candidates = _graph_nodes(agent, "OpenProcessCandidate")
        candidates = [node for node in candidates
                      if agent.s.node(node)["attrs"].get("domain") == domain_name]
        if len(candidates) != 1:
            return {"status": "NO_CANDIDATE" if not candidates else "AMBIGUOUS_CANDIDATE",
                    "candidate_count": len(candidates), "attempt_count": len(_graph_nodes(agent, "OpenProcessSearchAttempt")),
                    "task_seconds": time.perf_counter() - started}
        candidate = candidates[0]
        digest = attest_open_process_candidate(agent, candidate)
        attrs = agent.s.node(candidate)["attrs"]
        approval_context = {"expression_digest": digest, "expression_key": attrs["expression_key"],
            "expression_tree": attrs["expression_tree"], "effect_digest": attrs["effect_digest"],
            "params": attrs["params"], "guard_state": attrs["guard_state"],
            "domain": attrs["domain"], "source_epoch": attrs["source_epoch"],
            "model_epoch": attrs["model_epoch"], "frame_epoch": attrs["frame_epoch"]}
        if approval_provider is None or not approval_provider(approval_context):
            return {"status": "AWAITING_CANDIDATE_APPROVAL", "candidate_digest": digest,
                    "candidate": approval_context,
                    "attempt_count": len(_graph_nodes(agent, "OpenProcessSearchAttempt")),
                    "approval_source": approval_source,
                    "task_seconds": time.perf_counter() - started}
        approval = agent.s.add_node("OpenProcessAdoptionApproval", {
            "status": "approved", "approval_kind": "human", **approval_context})
        _edge(agent, agent.agent, "has_open_process_adoption_approval", approval)
        _edge(agent, approval, "approves_open_process_candidate", candidate)
        _settle(agent)

        def world_transition(proposed):
            # Decode only the graph-authored expression and check the native
            # proposed effect against its independent primitive execution.
            actions = expression_actions(attrs["expression_tree"])
            if actions is None:
                return {"status": "rejected", "reason": "unsupported_expression_tree"}
            applied = agent.inner.evaluate({"type": "ProcessApply",
                "p": {"type": "Var", "name": "p"},
                "state": {"type": "Var", "name": "state"}},
                {"p": proposed, "state": list(world.state)})
            if applied is None:
                return {"status": "rejected", "reason": "native_effect_unknown"}
            receipt = world.transition_sequence(actions, requested_process=proposed)
            if receipt.get("status") == "verified" and receipt.get("observed_state") != list(applied):
                raise RuntimeError("independent world receipt disagrees with native process effect")
            return receipt

        result = execute_open_process_candidate(agent, candidate,
            state=list(world.state), authorize=lambda proposal: True,
            world_transition=world_transition)
        solved = tuple(world.state) == tuple(world.goal)
        _settle(agent)
        strategies = [node for node in _graph_nodes(agent, "DiscoveredStrategy")
                      if agent.s.node(node)["attrs"].get("source") == "native_world_receipt"]
        strategy_reuse = {"status": "NOT_RUN", "solved": False}
        if unseen_binding is not None and len(strategies) == 1:
            initial, goal = unseen_binding
            target_task = agent.s.add_node("SolveTask", {
                "domain": domain_name, "initial_state": list(initial), "state": list(initial),
                "object_count": float(len(initial)), "goal": list(goal), "status": "active",
                "trace": [], "steps": 0, "moves": 0.0, "stuck_count": 0})
            _edge(agent, agent.agent, "has_solve_task", target_task)
            _edge(agent, target_task, "about_domain", domain)
            _settle(agent)
            target_attrs = agent.s.node(target_task)["attrs"]
            strategy_reuse = {"status": target_attrs.get("status"),
                "solved": target_attrs.get("status") == "solved",
                "trace_length": len(target_attrs.get("trace") or []),
                "source_strategy_id": str(strategies[0]),
                "binding_changed": list(initial) != list(task["initial_state"]),
                "goal_changed": list(goal) != list(task["goal_state"])}
        return {"status": result.get("status"), "solved": solved,
            "primitives": len(result.get("receipt", {}).get("applied_actions", [])),
            "model_queries": len(_graph_nodes(agent, "OpenProcessSearchAttempt")),
            "receipts": [result["receipt"]] if result.get("receipt") else [],
            "candidate_digest": digest, "expression_key": attrs["expression_key"],
            "approval_source": approval_source,
            "execution_reason": result.get("reason"),
            "attempt_count": len(_graph_nodes(agent, "OpenProcessSearchAttempt")),
            "strategy_learned_from_receipt": len(strategies) == 1,
            "unseen_binding_strategy": strategy_reuse,
            "task_seconds": time.perf_counter() - started}
    finally:
        agent.close()


def run_trial(family: str, task_kind: str, seed: int, arm: str, *,
              approval_provider=None, approval_source="candidate_specific_provider"):
    task, world, hidden_witness = generate_task(family, task_kind, seed)
    if arm == "measured_greedy":
        result = run_greedy(task, world)
    elif arm == "native_primitive_search":
        result = run_native_primitive(task, world)
    elif arm == "invention_discovery":
        unseen_binding = None
        if family == "permutation":
            rng = random.Random(seed ^ 0x19B1D1)
            initial = list(range(len(task["initial_state"])))
            rng.shuffle(initial)
            if initial == task["initial_state"]:
                initial = initial[1:] + initial[:1]
            goal = tuple(initial)
            for action in hidden_witness:
                goal = world._apply_action(goal, action)
            unseen_binding = (initial, goal)
        elif task_kind == "process_effect":
            target_object = int(hidden_witness[0][-1])
            other = 1 - target_object
            initial = [0, 0, 0, 0]
            initial[other * 2:other * 2 + 2] = [1, 1]
            goal = tuple(initial)
            for action in hidden_witness:
                goal = world._apply_action(goal, action)
            unseen_binding = (initial, goal)
        result = run_invention(task, world, approval_provider=approval_provider,
                               approval_source=approval_source,
                               unseen_binding=unseen_binding)
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
        invention = run_trial(item["family"], item["task_kind"], item["seed"],
            "invention_discovery", approval_provider=lambda _candidate: True,
            approval_source="synthetic_development_fixture")
        cases.append({"family": item["family"], "task_kind": item["task_kind"],
                      "seed": item["seed"], "witness_length": len(witness),
                      "greedy_solved": greedy["solved"], "greedy_primitives": greedy["primitives"],
                      "greedy_model_queries": greedy["model_queries"],
                      "native_primitive_search_solved": native["solved"],
                      "native_primitives": native["primitives"],
                      "native_model_queries": native["model_queries"],
                      "invention_status": invention["status"],
                      "invention_solved": invention.get("solved"),
                      "invention_attempts": invention.get("attempt_count", 0),
                      "invention_approval_source": invention.get("approval_source"),
                      "strategy_learned_from_receipt": invention.get("strategy_learned_from_receipt", False),
                      "unseen_binding_strategy": invention.get("unseen_binding_strategy", {})})
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

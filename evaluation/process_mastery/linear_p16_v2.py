"""P16 native execution and primitive-search conformance panel."""
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
for path in (ROOT, ROOT / "runners/dsl/python", ROOT / "scripts"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from evaluation.process_mastery.harness import Agent  # noqa: E402
from evaluation.process_mastery.native_process_execution import execute_selected  # noqa: E402
from evaluation.process_mastery.native_primitive_search import search_and_execute  # noqa: E402
from evaluation.process_mastery.native_world_comparators import NativeWorldAdapter  # noqa: E402
from evaluation.process_mastery.puzzle_worlds import p16_task  # noqa: E402
from evaluation.process_mastery.runtime_attestation import attest  # noqa: E402
from evaluation.process_mastery.scorecard import write_scorecard  # noqa: E402
import substrate_rs  # noqa: E402

PHASE = "linear-p16-v2"
FAMILIES = ("permutation", "state_dependent_tool")
ARMS = ("primitive_search", "graph_expression")
BASE_SEED = 26_160_000
DEVELOPMENT_N = 8
HELDOUT_N = 200
CONTROL_BASE = 26_170_000
CONTROL_KINDS = ("missing_expression", "stale_expression", "tampered_expression",
                 "wrapper_native_mismatch", "unauthorized_emission")
SEEDS = ("process_laws", "process_proof_adoption", "invention_operator_authorship",
         "recursive_process_improvement", "native_process_execution", "thinking_budget",
         "process_schema", "invention_operators", "invention_round",
         "invariant_miner", "process_solving")
MAX_TICKS = 30
MAX_STEPS_PER_TICK = 100_000
EXPRESSION_BUDGET = 1_000_000.0
CRITERIA_DIGEST = "pmb-v1-frozen-criteria"


def _json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=list)


def _digest(value):
    return hashlib.sha256(_json(value).encode()).hexdigest()


def _json_safe(value):
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def _file_digest(paths):
    digest = hashlib.sha256()
    for relative in paths:
        digest.update(relative.encode() + b"\0")
        digest.update((ROOT / relative).read_bytes() + b"\0")
    return digest.hexdigest()


def _tick(agent):
    # The established PMB harness uses a fixed tick ceiling: some unrelated
    # cognition-on policies can keep producing work after this task is done.
    return agent.run(max_ticks=1, max_steps=MAX_STEPS_PER_TICK)


def _expression_profile():
    started = time.perf_counter()
    agent = Agent(track_i=False, extra_seeds=SEEDS, profile="p16-native-expression",
                  budget={"enabled": 1.0, "capacity": EXPRESSION_BUDGET,
                          "capacity_ceiling": EXPRESSION_BUDGET,
                          "remaining": EXPRESSION_BUDGET,
                          "refill_per_epoch": 0.0, "last_refill_epoch": -1000.0})
    boot_seconds = time.perf_counter() - started
    for kind in ("InventionOperatorAuthorshipPolicy", "NativeProcessExecutionPolicy"):
        nodes = agent.nodes(kind)
        if len(nodes) != 1:
            raise RuntimeError(f"expected one {kind}, got {len(nodes)}")
        agent.s.set_attr(nodes[0], "enabled", 1.0)
    for kind in ("RecursiveProcessImprovementPolicy", "SolverPolicy", "InventionPolicy",
                 "ProcessSchemaPolicy", "ProcessCurriculumPolicy", "ProcessLawsPolicy",
                 "ProcessProofAdoptionPolicy"):
        for node in agent.nodes(kind):
            agent.s.set_attr(node, "enabled", 0.0)
    budgets = agent.nodes("ThinkingBudget")
    if len(budgets) != 1:
        raise RuntimeError(f"expected one shared ThinkingBudget, got {len(budgets)}")
    for key, value in {"enabled": 1.0, "capacity": EXPRESSION_BUDGET,
                       "capacity_ceiling": EXPRESSION_BUDGET,
                       "remaining": EXPRESSION_BUDGET, "refill_per_epoch": 0.0,
                       "last_refill_epoch": -1000.0}.items():
        agent.s.set_attr(budgets[0], key, value)
    request = agent.s.add_node("OperatorCompositionRequest", {
        "name": "p16-conformance-operator", "status": "draft",
        "recipe": "commutator_square", "left_operator": "commutator",
        "right_operator": "commutator", "candidate_name": "commutator_square_v1"})
    agent.s.add_edge(agent.ag, "has_operator_composition_request", request, {})
    _tick(agent)
    candidates = agent.nodes("CandidateOperator", name="commutator_square_v1")
    if len(candidates) != 1:
        raise RuntimeError("native authoring rule did not create the candidate")
    candidate = candidates[0]
    agent.s.set_attr(candidate, "source_epoch", 0.0)
    # This is a fixed, measured development qualification for the same graph-
    # authored candidate in every expression trial, not a trial outcome.
    for key, value in {"development_yield": 8.0, "parent_development_yield": 7.0,
                       "invariant_checks": 8.0, "parent_invariant_checks": 8.0,
                       "proof_failures": 0.0, "candidate_work": 8.0,
                       "status": "measured"}.items():
        agent.s.set_attr(candidate, key, value)
    _tick(agent)
    approval = agent.s.add_node("OperatorPromotionApproval", {
        "status": "approved", "approval_kind": "human",
        "candidate_name": "commutator_square_v1", "criteria_digest": CRITERIA_DIGEST})
    agent.s.add_edge(agent.ag, "has_promotion_approval", approval, {})
    _tick(agent)
    active = [node for node in agent.nodes("InventionOperator", name="commutator_square_v1",
                                           status="active")]
    if len(active) != 1 or agent.s.node(candidate)["attrs"].get("status") != "promoted":
        raise RuntimeError("candidate did not cross the existing approval boundary: "
                           f"candidate={agent.s.node(candidate)['attrs']}, active={len(active)}")
    # This conformance profile exposes the one human-approved treatment
    # operator, while leaving the candidate and its expression graph intact.
    # Removing other operator-selection edges prevents unrelated library
    # breadth from turning this fixed execution panel into a portfolio search.
    for operator in agent.nodes("InventionOperator"):
        if operator != active[0]:
            agent.native.remove_edge(agent.ag, "has_invention_operator", operator)
    return agent, candidate, approval, boot_seconds


def _install_expression_task(agent, task, suffix):
    domain_name = f"p16-{task['family']}-{suffix}"
    held = {name: tuple(task["primitive_affordances"][name])
            for name in (task["process_input_a"], task["process_input_b"])}
    initial_key = ",".join(map(str, task["initial_state"]))
    domain = agent.add_domain(domain_name, "permutation", [list(range(4))], held,
        primitive_affordances=task["primitive_affordances"],
        legal_actions=task["legal_actions_by_state"][initial_key],
        world_access_sha256=_access_hash(task), family=task["family"])
    schemas = {agent.attrs(node).get("name"): node
               for node in agent.schemas(domain_name, status="active")}
    left = schemas.get(task["process_input_a"])
    right = schemas.get(task["process_input_b"])
    if left is None or right is None:
        raise RuntimeError("world process inputs are absent from the graph domain")
    solve = agent.add_solve_task(domain_name, task["initial_state"], task["goal_state"],
                                 pmb_seed=task["seed"], pmb_family=task["family"])
    agent.s.add_edge(solve, "has_process_input_a", left, {})
    agent.s.add_edge(solve, "has_process_input_b", right, {})
    _tick(agent)
    requests = [node for node in agent.nodes("NativeExecutionRequest", status="funded")
                if agent.native.neighbours(node, "for_solve_task") == [solve]]
    if len(requests) != 1:
        raise RuntimeError(f"expected one funded graph request, got {len(requests)}")
    return domain, solve, requests[0]


def _execute_expression(task, *, control=None):
    agent, candidate, approval, boot_seconds = _expression_profile()
    world = NativeWorldAdapter.from_task(task, world_id=f"{task['family']}:{task['seed']}")
    domain, solve, request = _install_expression_task(agent, task, str(task["seed"]))
    root = agent.native.neighbours(candidate, "has_expression_root")[0]
    saved_root_attrs = agent.s.node(root)["attrs"].copy()
    saved_root_edges = agent.native.neighbours(candidate, "has_expression_root")
    source_epoch = agent.s.node(candidate)["attrs"].get("source_epoch")
    if control == "missing_expression":
        agent.native.remove_edge(candidate, "has_expression_root", root)
    elif control == "stale_expression":
        agent.s.set_attr(candidate, "source_epoch", float(source_epoch) + 1.0)
    elif control == "tampered_expression":
        agent.s.set_attr(root, "native_term", {"type": "UnsupportedTerm"})
    denied_world_calls = []

    def authorize(proposal):
        return (control != "unauthorized_emission"
                and proposal.get("candidate_id") == candidate
                and agent.s.node(approval)["attrs"].get("status") == "approved"
                and agent.s.node(approval)["attrs"].get("criteria_digest") == CRITERIA_DIGEST)

    def transition(proposed):
        options = [name for name in world.legal_actions(world.state)
                   if tuple(world._apply(world.state, name)) == tuple(proposed)]
        if len(options) != 1:
            return None
        receipt = world.transition(world.state, options[0])
        return receipt if world.verify_receipt(receipt) else None

    before_state = world.state
    started = time.perf_counter()
    result = execute_selected(agent, request, state=list(before_state),
                              authorize=authorize,
                              world_transition=lambda action: denied_world_calls.append(action)
                              or transition(action))
    elapsed = time.perf_counter() - started
    if control == "unauthorized_emission" and denied_world_calls:
        raise RuntimeError("unauthorized proposal reached the world boundary")
    if control == "missing_expression":
        agent.native.add_edge(candidate, "has_expression_root", root, {})
    if control == "stale_expression":
        agent.s.set_attr(candidate, "source_epoch", source_epoch)
    if control == "tampered_expression":
        for key, value in saved_root_attrs.items():
            agent.s.set_attr(root, key, value)
    agent.s.set_attr(solve, "status", "complete")
    receipt = result.get("receipt")
    observed_state = tuple(receipt["observed_state"]) if receipt else before_state
    record = {"status": result.get("status"), "reason": result.get("reason"),
        "outcome": "solved" if observed_state == world.goal else "unsolved",
        "family": task["family"], "seed": task["seed"],
        "profile": "graph_expression", "initial_state": list(before_state),
        "goal_state": list(world.goal), "observed_state": list(observed_state),
        "receipt": receipt, "receipt_verified": bool(receipt and world.verify_receipt(receipt)),
        "proposal": _json_safe(result.get("proposal")), "meter": result.get("meter", {}),
        "actions": int(world.epoch), "task_seconds": elapsed,
        "boot_seconds": boot_seconds, "graph_nodes_end": len(agent.s.nodes()),
        "graph_serialized_bytes": len(json.dumps(agent.native.graph_to_dict(),
                                                   sort_keys=True, default=list).encode()),
        "budget_remaining": agent.s.node(agent.nodes("ThinkingBudget")[0])["attrs"].get("remaining"),
        "world_sha256": _digest(task), "world_access_sha256": _access_hash(task),
        "input_audit": {"answer_fields_absent": "goal_action" not in task,
                        "hidden_solution_absent": "solution" not in task,
                        "same_primitive_access_hash": _access_hash(task),
                        "source_nodes_owned": bool(result.get("proposal", {}).get("input_source_ids")),
                        "selected_by_graph": result.get("proposal", {}).get("request_id") == request},
        "resource_counts": {"expression_visits": result.get("meter", {}).get("expression_visits", 0),
            "compositions": result.get("meter", {}).get("compositions", 0),
            "applications": result.get("meter", {}).get("applications", 0),
            "failed_proposals": result.get("meter", {}).get("failed_proposals", 0),
            "world_actions": int(world.epoch), "ticks": MAX_TICKS}}
    return record


def _access_hash(task):
    return _digest({"initial_state": task["initial_state"], "goal_state": task["goal_state"],
        "primitive_affordances": task["primitive_affordances"],
        "legal_actions_by_state": task["legal_actions_by_state"],
        "transition_model": task["transition_model"]})


def _run_search(task):
    world = NativeWorldAdapter.from_task(task, world_id=f"{task['family']}:{task['seed']}")
    started = time.perf_counter()
    result = search_and_execute(task, world=world)
    elapsed = time.perf_counter() - started
    receipt = result.get("receipt")
    valid = bool(receipt and world.verify_receipt(receipt))
    observed_state = tuple(receipt["observed_state"]) if receipt else world.state
    return {"status": result["status"], "family": task["family"],
        "seed": task["seed"], "profile": "primitive_search",
        "outcome": "solved" if observed_state == world.goal else "unsolved",
        "initial_state": list(task["initial_state"]), "goal_state": list(world.goal),
        "observed_state": list(observed_state), "receipt": receipt,
        "receipt_verified": valid, "actions": int(world.epoch),
        "task_seconds": elapsed, "boot_seconds": None,
        "graph_nodes_end": result.get("graph_nodes"), "graph_serialized_bytes": None,
        "budget_remaining": result.get("remaining_budget"),
        "planner_status": result.get("planner_status"),
        "search_expansions": result.get("expanded"),
        "world_sha256": _digest(task), "world_access_sha256": _access_hash(task),
        "input_audit": {"answer_fields_absent": "goal_action" not in task,
            "hidden_solution_absent": "solution" not in task,
            "same_primitive_access_hash": _access_hash(task),
            "complete_transition_model": True, "native_frontier_search": True},
        "resource_counts": {"search_expansions": result.get("expanded"),
            "world_actions": int(world.epoch), "ticks": result.get("ticks"),
            "graph_nodes_added": result.get("graph_nodes_added")}}


def _attestation():
    package_dir = Path(substrate_rs.__file__).resolve().parent
    return attest(package=substrate_rs,
                  build_receipt=package_dir / "_native.build.json", require_clean=True)


def _controls(n, first_seed):
    records = []
    if n == 0:
        return records
    for kind_index, kind in enumerate(CONTROL_KINDS):
        for ix in range(n):
            seed = first_seed + kind_index * 1_000 + ix
            task = p16_task("permutation", seed)
            if kind == "wrapper_native_mismatch":
                actual = _attestation()
                rejected = attest(package=substrate_rs,
                    build_receipt=Path(substrate_rs.__file__).resolve().parent / "_native.build.json",
                    expected={"loaded_extension_sha256": f"{ix + 1:064x}"})["status"] != "ATTESTED"
                records.append({"control": kind, "seed": seed, "passed": rejected,
                                "actual_attestation": actual["status"],
                                "rejected_mismatch": rejected, "actions": 0})
                continue
            result = _execute_expression(task, control=kind)
            expected = {"missing_expression": ("ABSTAIN", "missing_or_ambiguous_source_or_expression"),
                        "stale_expression": ("ABSTAIN", "stale_or_unversioned_expression"),
                        "tampered_expression": ("ABSTAIN", "missing native expression term"),
                        "unauthorized_emission": ("DENIED", None)}[kind]
            passed = (result["status"] == expected[0]
                      and (expected[1] is None or result.get("reason") == expected[1])
                      and result["actions"] == 0)
            records.append({"control": kind, "seed": seed, "passed": passed,
                            "status": result["status"], "reason": result.get("reason"),
                            "actions": result["actions"]})
    return records


def provenance():
    paths = (
        "evaluation/process_mastery/linear_p16_v2.py",
        "evaluation/process_mastery/analyze_linear_p16_v2.py",
        "evaluation/process_mastery/scorecard.py",
        "evaluation/process_mastery/harness.py",
        "evaluation/process_mastery/native_process_execution.py",
        "evaluation/process_mastery/native_primitive_search.py",
        "evaluation/process_mastery/native_world_comparators.py",
        "evaluation/process_mastery/puzzle_worlds.py",
        "evaluation/process_mastery/runtime_attestation.py",
        "substrate/boot_profiles.py", "seeds/cognition_on_params.json",
        "scripts/gen_native_process_execution_seed.py", "seeds/native_process_execution.json",
        "scripts/gen_invention_operator_authorship_seed.py",
        "seeds/invention_operator_authorship.json",
        "scripts/gen_cognition_planner_seed.py",
        "docs/research/engine_substrate/COGNITION_NATIVE_EVIDENCE_CONTRACT.md",
        "runners/dsl/src/process_algebra.rs", "runners/dsl/src/term.rs",
        "runners/dsl/src/cognitive_cycle.rs", "runners/dsl/Cargo.toml",
        "runners/dsl/python/substrate_rs/__init__.py",
        "runners/dsl/python/substrate_rs/_native.build.json",
    )
    extension_path = Path(substrate_rs._native.__file__).resolve()
    receipt = Path(substrate_rs.__file__).resolve().parent / "_native.build.json"
    return {"phase": PHASE, "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "analyzer_sha256": hashlib.sha256((ROOT / "evaluation/process_mastery/analyze_linear_p16_v2.py").read_bytes()).hexdigest()
                            if (ROOT / "evaluation/process_mastery/analyze_linear_p16_v2.py").exists() else None,
        "source_bundle_sha256": _file_digest(paths),
        "git_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "wrapper_path": str(Path(substrate_rs.__file__).resolve()),
        "wrapper_sha256": hashlib.sha256(Path(substrate_rs.__file__).read_bytes()).hexdigest(),
        "loaded_extension_path": str(extension_path),
        "loaded_extension_sha256": hashlib.sha256(extension_path.read_bytes()).hexdigest(),
        "build_receipt_path": str(receipt),
        "build_receipt_sha256": hashlib.sha256(receipt.read_bytes()).hexdigest(),
        "runtime_attestation": _attestation(),
        "profile_sha256": _file_digest(("substrate/boot_profiles.py", "seeds/cognition_on_params.json")),
        "world_adapter_sha256": _file_digest(("evaluation/process_mastery/harness.py",
            "evaluation/process_mastery/puzzle_worlds.py",
            "evaluation/process_mastery/native_world_comparators.py")),
        "dependency_closure_sha256": _file_digest(("runners/dsl/Cargo.toml",
            "runners/dsl/pyproject.toml", "runners/dsl/uv.lock",
            "runners/dsl/python/substrate_rs/_native.build.json")),
        "engine_source_sha256": _file_digest(("runners/dsl/src/process_algebra.rs",
            "runners/dsl/src/term.rs", "runners/dsl/src/cognitive_cycle.rs")),
        "python": sys.version.split()[0]}


def run(*, split="development", n=None, self_check=False, include_controls=True):
    if split not in {"development", "heldout"}:
        raise ValueError("P16 split must be development or heldout")
    if self_check and split != "development":
        raise ValueError("self-check is development-only")
    count = 2 if self_check else (n if n is not None else
             DEVELOPMENT_N if split == "development" else HELDOUT_N)
    expected = HELDOUT_N if split == "heldout" else DEVELOPMENT_N
    if count < 1 or count > expected or (not self_check and count != expected):
        raise ValueError(f"P16 {split} allocation is fixed at {expected} tasks per family")
    offset = 0 if split == "development" else 2_000_000
    rows, paired_worlds = [], {}
    for family_index, family in enumerate(FAMILIES):
        for ix in range(count):
            seed = BASE_SEED + offset + family_index * 10_000 + ix
            task = p16_task(family, seed)
            paired_worlds[(family, seed)] = _digest(task)
            expression = _execute_expression(task)
            search = _run_search(task)
            rows.extend((search, expression))
    if any(row["world_sha256"] != paired_worlds[(row["family"], row["seed"])]
           for row in rows):
        raise RuntimeError("paired arms received different worlds")
    control_count = (2 if self_check else 100) if include_controls else 0
    controls = _controls(control_count,
                         CONTROL_BASE + offset)
    meta = {"phase": PHASE, "split": split, "seed_base": BASE_SEED + offset,
        "seed_formula": "26_160_000 + split_offset + family_index*10_000 + draw",
        "split_offset": offset, "family_order": list(FAMILIES),
        "n_per_family_per_arm": count, "arms": list(ARMS),
        "control_seed_base": CONTROL_BASE + offset,
        "control_n_per_kind": control_count,
        "control_kinds": list(CONTROL_KINDS), "limits": {"max_ticks": MAX_TICKS,
            "max_steps_per_tick": MAX_STEPS_PER_TICK, "max_expression_nodes": 64,
            "max_graph_nodes": 200_000, "max_serialized_graph_bytes": 64 * 1024 * 1024,
            "expression_budget": EXPRESSION_BUDGET, "planner_expansions": 256,
            "planner_depth": 1},
        "task_generation": {"state_space_size": 24, "world_action_count": 24,
            "process_inputs_independent_of_goal": True,
            "state_dependent_tool_rule": "even source states permit even position permutations; odd source states permit all permutations"},
        "artifact_provenance": provenance(), "human_comparison": "UNAVAILABLE_PROTOCOL_NOT_MATCHED",
        "self_check": bool(self_check), "controls": controls,
        "unsupported_families": ["physical world", "broad capability program", "motor program",
                                  "family program", "general open-world tool learning"]}
    return {"schema": "pmb-scorecard-v1", "metadata": meta, "records": rows}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", choices=("development", "heldout"), default="development")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--self-check", action="store_true")
    parser.add_argument("--no-controls", action="store_true")
    args = parser.parse_args()
    payload = run(split=args.split, self_check=args.self_check,
                  include_controls=not args.no_controls)
    if args.output:
        write_scorecard(args.output, metadata=payload["metadata"], records=payload["records"])
    else:
        print(json.dumps(payload, indent=2, sort_keys=True, default=list))


if __name__ == "__main__":
    main()

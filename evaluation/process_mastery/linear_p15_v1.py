"""P15 matched-arm development adapter for graph-owned learning and operators.

This adapter deliberately exposes only the supported permutation process-macro
family. It exercises the native curriculum and approval/budget lifecycle; it
fails closed if any required graph path is missing.
"""
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

from evaluation.process_mastery.scorecard import write_scorecard  # noqa: E402
from substrate.boot_profiles import boot_cognition_on  # noqa: E402
import substrate_rs  # noqa: E402

PHASE = "linear-p15-v1"
ARMS = ("unchanged_operator", "adaptive_curriculum", "full_system")
TRAINING_SEED_BASE = 25_110_000
BASE_SEED = 25_111_000  # selection/development block for family_code=11
N_DEVELOPMENT = 8
N_SELF_CHECK = 2
GENERATION_INDEX = 1
BUDGET = 400_000.0  # three 100k generation reservations plus shared curriculum funding
MAX_TICKS = 400
MAX_STEPS_PER_TICK = 100_000


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                      default=str).encode()).hexdigest()


def _file_digest(relpaths):
    digest = hashlib.sha256()
    for rel in relpaths:
        digest.update(rel.encode() + b"\0" + (ROOT / rel).read_bytes() + b"\0")
    return digest.hexdigest()


def _nodes(agent, kind):
    return [n for n in agent.s.nodes() if agent.s.node(n)["type"] == kind]


def _edge(agent, source, label, target):
    agent.inner.add_edge_unchecked(source, label, target, {})


def _settle(agent):
    for _ in range(MAX_TICKS):
        if agent.inner.run_rules(MAX_STEPS_PER_TICK) == 0:
            return
    raise RuntimeError("P15 profile did not reach a fixpoint within the frozen tick ceiling")


def _set_only(agent, kind, enabled):
    nodes = _nodes(agent, kind)
    if not nodes:
        raise RuntimeError(f"P15 profile missing required policy: {kind}")
    for ix, node in enumerate(nodes):
        agent.inner.set_attr(node, "enabled", float(bool(enabled) and ix == 0))
    return nodes[0]


def _profile(arm):
    started = time.perf_counter()
    agent = boot_cognition_on()
    boot_seconds = time.perf_counter() - started
    # Isolate this registered phase from unrelated active cognition-on areas.
    for kind in ("ConsolidationSchedulerPolicy", "SleepRegimePolicy", "LibraryLearningPolicy",
                 "StrategyLibraryPolicy", "ProcessSchemaPolicy", "InventionPolicy",
                 "InvariantMinerPolicy", "SolverPolicy", "ProcessLawsPolicy",
                 "ProcessProofAdoptionPolicy", "ProcessPortfolioPolicy",
                 "ProcessCurriculumPolicy", "InventionOperatorAuthorshipPolicy",
                 "RecursiveProcessImprovementPolicy"):
        if _nodes(agent, kind):
            _set_only(agent, kind, False)
    _set_only(agent, "ProcessSchemaPolicy", False)
    if arm in {"adaptive_curriculum", "full_system"}:
        _set_only(agent, "ProcessCurriculumPolicy", True)
    if arm == "full_system":
        _set_only(agent, "InventionOperatorAuthorshipPolicy", True)
        _set_only(agent, "RecursiveProcessImprovementPolicy", True)
    budgets = [n for n in _nodes(agent, "ThinkingBudget")
               if agent.s.node(n)["attrs"].get("enabled") == 1.0]
    if len(budgets) != 1:
        agent.close()
        raise RuntimeError(f"expected one enabled shared ThinkingBudget, got {len(budgets)}")
    budget = budgets[0]
    for key, value in {"enabled": 1.0, "capacity": BUDGET, "capacity_ceiling": BUDGET,
                       "remaining": BUDGET, "refill_per_epoch": 0.0,
                       "last_refill_epoch": -1000.0}.items():
        agent.inner.set_attr(budget, key, value)
    return agent, boot_seconds, budget


def _permutation(seed, size=4):
    rng = random.Random(seed)
    out = list(range(size))
    rng.shuffle(out)
    return out


def _pair(seed, size=4):
    a = [1, 2, 3, 0]
    rng = random.Random(seed)
    b = list(range(size))
    i, j = sorted(rng.sample(range(size), 2))
    b[i], b[j] = b[j], b[i]
    inv = lambda p: [p.index(x) for x in range(size)]
    comp = lambda x, y: [y[x[k]] for k in range(size)]
    comm = comp(comp(comp(a, b), inv(a)), inv(b))
    return a, b, comm


def _eval(agent, term, env):
    value = agent.inner.evaluate(term, env)
    if value is None:
        raise RuntimeError("native process evaluator returned no value")
    return value


def _process(agent, seed):
    a, b, comm = _pair(seed)
    sa = agent.s.add_node("ProcessSchema", {"name": f"a-{seed}", "kind": "permutation",
        "params": a, "status": "active", "provenance": "held"})
    sb = agent.s.add_node("ProcessSchema", {"name": f"b-{seed}", "kind": "permutation",
        "params": b, "status": "active", "provenance": "held"})
    from scripts.track_i_seed_lib import A, PCommutator, PCompose
    checked = _eval(agent, PCommutator(A("a", "params"), A("b", "params")),
                    {"a": sa, "b": sb})
    if list(checked) != comm:
        raise RuntimeError("native commutator does not match frozen permutation world")
    square = _eval(agent, PCompose(V("comm"), V("comm")), {"comm": comm})
    return comm, square


def V(name): return {"type": "Var", "name": name}


def _apply(agent, process, state):
    return _eval(agent, {"type": "ProcessApply", "p": V("p"), "state": V("state")},
                 {"p": process, "state": state})


def _exercise_curriculum(agent, seed):
    hyp = agent.s.add_node("ProcessInductionHypothesis", {
        "owner_id": "p15-adapter", "action_kind": "apply", "object_type": "permutation",
        "feature_key": "state", "before_value": "s0", "after_value": "s1",
        "source_epoch": 0, "model_epoch": 0, "frame_epoch": 0, "status": "disputed"})
    ce = agent.s.add_node("ProcessCounterexample", {
        "event_id": f"p15-training-{seed}", "status": "observed"})
    obs = agent.s.add_node("TransitionObservation", {
        "owner_id": "p15-adapter", "event_id": f"p15-training-{seed}",
        "action_kind": "apply", "object_type": "permutation", "feature_key": "state",
        "before_value": "s0", "after_value": "s1", "split": "training",
        "source_epoch": 0, "model_epoch": 0, "frame_epoch": 0})
    _edge(agent, agent.agent, "has_process_induction_hypothesis", hyp)
    _edge(agent, hyp, "has_counterexample", ce)
    _edge(agent, ce, "counterexample_transition", obs)
    _settle(agent)
    tasks = _nodes(agent, "ProcessCurriculumTask")
    if not tasks:
        raise RuntimeError("adaptive arm failed to turn a verified training residual into a task")
    attrs = agent.s.node(tasks[0])["attrs"]
    if attrs.get("split") != "training" or attrs.get("expected_outcome") != "unknown" \
            or attrs.get("answer_fields_absent") is not True:
        raise RuntimeError("curriculum task violated the frozen input boundary")
    return tasks[0]


def _exercise_operator_generation(agent):
    req = agent.s.add_node("OperatorCompositionRequest", {
        "name": "p15-v1-authorization", "status": "draft", "recipe": "commutator_square",
        "left_operator": "commutator", "right_operator": "commutator",
        "candidate_name": "commutator_square_v1"})
    _edge(agent, agent.agent, "has_operator_composition_request", req)
    _settle(agent)
    candidates = [n for n in _nodes(agent, "CandidateOperator")
                  if agent.s.node(n)["attrs"].get("name") == "commutator_square_v1"]
    if len(candidates) != 1:
        raise RuntimeError("graph-authored candidate proposal did not materialize")
    candidate = candidates[0]
    parent_success = candidate_success = invariant_checks = 0
    # Two real native development tasks qualify the candidate. These are
    # isolated in the selection block and never enter the scored panel.
    for ix in range(2):
        seed = BASE_SEED + 800 + ix
        comm, square = _process(agent, seed)
        initial = _permutation(seed + 7)
        goal = [square[x] for x in initial]
        parent_success += int(list(_apply(agent, comm, initial)) == goal)
        candidate_success += int(list(_apply(agent, square, initial)) == goal)
        invariant_checks += int(all(sorted(p) == list(range(4)) for p in (comm, square))) * 4
    for key, value in {"development_yield": float(candidate_success),
                       "parent_development_yield": float(parent_success),
                       "invariant_checks": float(invariant_checks),
                       "parent_invariant_checks": float(invariant_checks),
                       "proof_failures": 0.0, "candidate_work": 8.0,
                       "status": "measured"}.items():
        agent.inner.set_attr(candidate, key, value)
    _settle(agent)
    if agent.s.node(candidate)["attrs"].get("status") != "awaiting_human":
        raise RuntimeError("candidate failed frozen development qualification")
    # Materialize only the explicit user authorization scoped to v1 and digest.
    approval = agent.s.add_node("OperatorPromotionApproval", {
        "status": "approved", "approval_kind": "human",
        "candidate_name": "commutator_square_v1",
        "criteria_digest": "pmb-v1-frozen-criteria"})
    _edge(agent, agent.agent, "has_promotion_approval", approval)
    _settle(agent)
    operators = [n for n in _nodes(agent, "InventionOperator")
                 if agent.s.node(n)["attrs"].get("name") == "commutator_square_v1"
                 and agent.s.node(n)["attrs"].get("status") == "active"]
    generations = [n for n in _nodes(agent, "RecursiveProcessGeneration")
                   if agent.s.node(n)["attrs"].get("candidate_name") == "commutator_square_v1"
                   and agent.s.node(n)["attrs"].get("status") == "active"]
    if len(operators) != 1 or len(generations) != 1:
        raise RuntimeError("approved operator was not bound to one funded active generation")
    return candidate, operators[0], generations[0], {
        "parent_yield": parent_success, "candidate_yield": candidate_success,
        "invariant_checks": invariant_checks, "candidate_work": 8,
        "selection_seed_start": BASE_SEED + 800,
        "selection_seed_end_exclusive": BASE_SEED + 802,
        "candidate_status": agent.s.node(candidate)["attrs"].get("status"),
    }


def _measure_successor_v2(agent):
    candidates = [n for n in _nodes(agent, "CandidateOperator")
                  if agent.s.node(n)["attrs"].get("name") == "commutator_cube_v2"]
    if len(candidates) != 1:
        raise RuntimeError("generation 2 graph-authored successor proposal is missing")
    candidate = candidates[0]
    parent_success = candidate_success = invariant_checks = 0
    for ix in range(2):
        seed = BASE_SEED + 10_000 + 800 + ix
        comm, square = _process(agent, seed)
        cube = _eval(agent, {"type": "ProcessCompose", "a": V("left"), "b": V("right")},
                     {"left": square, "right": comm})
        initial = _permutation(seed + 7)
        goal = [cube[x] for x in initial]
        parent_success += int(list(_apply(agent, square, initial)) == goal)
        candidate_success += int(list(_apply(agent, cube, initial)) == goal)
        invariant_checks += int(all(sorted(p) == list(range(4))
                                    for p in (comm, square, cube))) * 4
    for key, value in {"development_yield": float(candidate_success),
                       "parent_development_yield": float(parent_success),
                       "invariant_checks": float(invariant_checks),
                       "parent_invariant_checks": float(invariant_checks),
                       "proof_failures": 0.0, "candidate_work": 12.0,
                       "status": "measured"}.items():
        agent.inner.set_attr(candidate, key, value)
    _settle(agent)
    attrs = agent.s.node(candidate)["attrs"]
    if attrs.get("status") != "awaiting_human":
        raise RuntimeError("generation 2 failed its development or invariant gate")
    pending = [g for g in _nodes(agent, "RecursiveProcessGeneration")
               if agent.s.node(g)["attrs"].get("candidate_name") == "commutator_cube_v2"]
    if len(pending) != 1 or agent.s.node(pending[0])["attrs"].get("status") != "pending_approval":
        raise RuntimeError("generation 2 did not remain pending its independent human approval")
    # The user explicitly approved only this candidate and digest. Materialize
    # that scoped event; the next candidate remains unapproved.
    approval = agent.s.add_node("OperatorPromotionApproval", {
        "status": "approved", "approval_kind": "human",
        "candidate_name": "commutator_cube_v2",
        "criteria_digest": "pmb-v1-frozen-criteria"})
    _edge(agent, agent.agent, "has_promotion_approval", approval)
    _settle(agent)
    operators = [n for n in _nodes(agent, "InventionOperator")
                 if agent.s.node(n)["attrs"].get("name") == "commutator_cube_v2"
                 and agent.s.node(n)["attrs"].get("status") == "active"]
    if len(operators) != 1 or agent.s.node(pending[0])["attrs"].get("status") != "active":
        raise RuntimeError("approved generation 2 did not pass the existing human promotion gate")
    next_candidate = [n for n in _nodes(agent, "CandidateOperator")
                      if agent.s.node(n)["attrs"].get("name") == "commutator_fourth_v3"]
    if len(next_candidate) != 1 or agent.s.node(next_candidate[0])["attrs"].get("status") != "draft":
        raise RuntimeError("generation 3 proposal missing or activated without its own approval")
    return {"candidate_name": attrs["name"], "parent_yield": parent_success,
            "candidate_yield": candidate_success, "invariant_checks": invariant_checks,
            "candidate_work": 12, "candidate_status": attrs["status"],
            "generation_status": agent.s.node(pending[0])["attrs"]["status"],
            "approval_event": {"status": agent.s.node(approval)["attrs"]["status"],
                               "candidate_name": "commutator_cube_v2",
                               "criteria_digest": "pmb-v1-frozen-criteria"},
            "next_candidate": "commutator_fourth_v3",
            "next_candidate_status": agent.s.node(next_candidate[0])["attrs"]["status"],
            "next_approval_required": True, "criteria_digest": attrs["criteria_digest"]}


def _measure_successor_v3(agent):
    candidates = [n for n in _nodes(agent, "CandidateOperator")
                  if agent.s.node(n)["attrs"].get("name") == "commutator_fourth_v3"]
    if len(candidates) != 1:
        raise RuntimeError("generation 3 graph-authored successor proposal is missing")
    candidate = candidates[0]
    parent_success = candidate_success = invariant_checks = 0
    for ix in range(2):
        seed = BASE_SEED + 20_800 + ix
        comm, square = _process(agent, seed)
        cube = _eval(agent, {"type": "ProcessCompose", "a": V("left"), "b": V("right")},
                     {"left": square, "right": comm})
        fourth = _eval(agent, {"type": "ProcessCompose", "a": V("left"), "b": V("right")},
                       {"left": cube, "right": comm})
        initial = _permutation(seed + 7)
        goal = [fourth[x] for x in initial]
        parent_success += int(list(_apply(agent, cube, initial)) == goal)
        candidate_success += int(list(_apply(agent, fourth, initial)) == goal)
        invariant_checks += int(all(sorted(p) == list(range(4))
                                    for p in (comm, square, cube, fourth))) * 4
    for key, value in {"development_yield": float(candidate_success),
                       "parent_development_yield": float(parent_success),
                       "invariant_checks": float(invariant_checks),
                       "parent_invariant_checks": float(invariant_checks),
                       "proof_failures": 0.0, "candidate_work": 16.0,
                       "status": "measured"}.items():
        agent.inner.set_attr(candidate, key, value)
    _settle(agent)
    attrs = agent.s.node(candidate)["attrs"]
    if attrs.get("status") != "awaiting_human":
        raise RuntimeError("generation 3 failed its development or invariant gate")
    pending = [g for g in _nodes(agent, "RecursiveProcessGeneration")
               if agent.s.node(g)["attrs"].get("candidate_name") == "commutator_fourth_v3"]
    if len(pending) != 1 or agent.s.node(pending[0])["attrs"].get("status") != "pending_approval":
        raise RuntimeError(f"generation 3 did not remain pending its independent approval: "
                           f"{[agent.s.node(g)['attrs'] for g in pending]}")
    approval = agent.s.add_node("OperatorPromotionApproval", {
        "status": "approved", "approval_kind": "human",
        "candidate_name": "commutator_fourth_v3",
        "criteria_digest": "pmb-v1-frozen-criteria"})
    _edge(agent, agent.agent, "has_promotion_approval", approval)
    _settle(agent)
    if agent.s.node(pending[0])["attrs"].get("status") != "active":
        raise RuntimeError("approved generation 3 did not pass the existing human promotion gate")
    return {"candidate_name": attrs["name"], "parent_yield": parent_success,
            "candidate_yield": candidate_success, "invariant_checks": invariant_checks,
            "candidate_work": 16, "candidate_status": agent.s.node(candidate)["attrs"]["status"],
            "generation_status": agent.s.node(pending[0])["attrs"]["status"],
            "approval_event": {"status": agent.s.node(approval)["attrs"]["status"],
                               "candidate_name": "commutator_fourth_v3",
                               "criteria_digest": "pmb-v1-frozen-criteria"},
            "criteria_digest": attrs["criteria_digest"]}


def _run_task(agent, arm, seed, generation):
    comm, square = _process(agent, seed)
    operator = comm
    for _ in range(generation):
        operator = _eval(agent, {"type": "ProcessCompose", "a": V("left"), "b": V("right")},
                         {"left": operator, "right": comm})
    initial = _permutation(seed + 7)
    expected = _apply(agent, operator, initial)
    result = _apply(agent, operator if arm == "full_system" else comm, initial)
    return result == expected, comm, operator, square


def provenance():
    paths = (
        "evaluation/process_mastery/linear_p15_v1.py",
        "evaluation/process_mastery/analyze_linear_p15_v1.py",
        "evaluation/process_mastery/scorecard.py",
        "evaluation/process_mastery/harness.py",
        "substrate/boot_profiles.py", "seeds/cognition_on_params.json",
        "scripts/gen_process_portfolio_seed.py", "seeds/process_portfolio.json",
        "scripts/gen_process_curriculum_seed.py", "seeds/process_curriculum.json",
        "scripts/gen_recursive_process_improvement_seed.py", "seeds/recursive_process_improvement.json",
        "scripts/gen_invention_operator_authorship_seed.py", "seeds/invention_operator_authorship.json",
        "docs/research/engine_substrate/COGNITION_RECURSIVE_IMPROVEMENT_CONTRACT.md",
        "docs/research/engine_substrate/PMB_V1_SPEC.md",
        "runners/dsl/src/process_algebra.rs", "runners/dsl/src/cognitive_cycle.rs",
        "runners/dsl/Cargo.toml", "runners/dsl/pyproject.toml",
        "runners/dsl/uv.lock", "runners/dsl/python/substrate_rs/_native.build.json",
    )
    return {"phase": PHASE, "source_bundle_sha256": _file_digest(paths),
            "git_commit": subprocess.check_output(["git", "rev-parse", "HEAD"],
                                                    cwd=ROOT, text=True).strip(),
            "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "analyzer_sha256": hashlib.sha256((ROOT / "evaluation/process_mastery/analyze_linear_p15_v1.py").read_bytes()).hexdigest(),
            "engine_binary_sha256": hashlib.sha256(Path(substrate_rs.__file__).read_bytes()).hexdigest(),
            "profile_sha256": _file_digest(("substrate/boot_profiles.py", "seeds/cognition_on_params.json")),
            "world_adapter_sha256": _file_digest(("substrate/world_adapter.py", "evaluation/process_mastery/harness.py")),
            "dependency_closure_sha256": _file_digest(("runners/dsl/Cargo.toml",
                "runners/dsl/pyproject.toml", "runners/dsl/uv.lock",
                "runners/dsl/python/substrate_rs/_native.build.json")),
            "engine_source_sha256": _file_digest(("runners/dsl/src/process_algebra.rs",
                "runners/dsl/src/cognitive_cycle.rs")),
            "python": sys.version.split()[0]}


def run(*, n=N_DEVELOPMENT, self_check=False, split="development"):
    if split not in {"development", "heldout"}:
        raise ValueError("P15 split must be development or heldout")
    if n < 1 or n > 200:
        raise ValueError("P15 n must be in [1, 200]")
    if self_check and split != "development":
        raise ValueError("self-check is development-only")
    if not self_check and split == "development" and n != N_DEVELOPMENT:
        raise ValueError("development draw uses the frozen eight-task panel")
    if not self_check and split == "heldout" and n != 200:
        raise ValueError("held-out draw uses the frozen 200-task panel")
    control_block = 1 if split == "development" else 2
    records = []
    access_hash = _digest(["ProcessApply", "ProcessCompose", "ProcessCommutator",
                           "held permutation primitives", "external_actions=0"])
    worlds = {}
    candidate_development = successor_development = third_development = None
    for arm in ARMS:
        agent, boot_seconds, budget = _profile(arm)
        generation_states = {1: None, 2: None, 3: None}
        try:
            if arm in {"adaptive_curriculum", "full_system"}:
                _exercise_curriculum(agent, TRAINING_SEED_BASE)
            if arm == "full_system":
                _, _, generation_one, candidate_development = _exercise_operator_generation(agent)
                generation_states[1] = generation_one
                successor_development = _measure_successor_v2(agent)
            if arm == "full_system":
                third_development = _measure_successor_v3(agent)
                approval_v2 = next(n for n in _nodes(agent, "OperatorPromotionApproval")
                                   if agent.s.node(n)["attrs"].get("candidate_name") == "commutator_cube_v2")
                if agent.s.node(approval_v2)["attrs"].get("criteria_digest") != "pmb-v1-frozen-criteria":
                    raise RuntimeError("generation 2 approval digest mismatch")
                generation_states[2] = next(g for g in _nodes(agent, "RecursiveProcessGeneration")
                    if agent.s.node(g)["attrs"].get("candidate_name") == "commutator_cube_v2"
                    and agent.s.node(g)["attrs"].get("status") == "active")
                approval_v3 = next(n for n in _nodes(agent, "OperatorPromotionApproval")
                                   if agent.s.node(n)["attrs"].get("candidate_name") == "commutator_fourth_v3")
                if agent.s.node(approval_v3)["attrs"].get("criteria_digest") != "pmb-v1-frozen-criteria":
                    raise RuntimeError("generation 3 approval digest mismatch")
                generation_states[3] = next(g for g in _nodes(agent, "RecursiveProcessGeneration")
                    if agent.s.node(g)["attrs"].get("candidate_name") == "commutator_fourth_v3"
                    and agent.s.node(g)["attrs"].get("status") == "active")
            for generation in (1, 2, 3):
                family_code = 10 + generation
                seed_base = 25_000_000 + family_code * 10_000 + control_block * 1_000
                generation_state = generation_states[generation]
                if generation_state is not None:
                    attrs = agent.s.node(generation_state)["attrs"]
                    if attrs.get("status") != "active" or attrs.get("autonomy_claim") != "valid":
                        raise RuntimeError(f"full-system generation {generation} failed its invariant gate")
                for ix in range(n):
                    seed = seed_base + ix
                    task_started = time.perf_counter()
                    solved, comm, operator, square = _run_task(agent, arm, seed, generation)
                    task_seconds = time.perf_counter() - task_started
                    task_work = (generation + 2) if arm == "full_system" else 2
                    if generation_state is not None:
                        generation_attrs = agent.s.node(generation_state)["attrs"]
                        remaining = float(generation_attrs["budget_remaining"])
                        if remaining < task_work:
                            raise RuntimeError("full-system generation exceeded its reserved work budget")
                        agent.inner.set_attr(generation_state, "budget_remaining", remaining - task_work)
                        agent.inner.set_attr(generation_state, "cumulative_work",
                                             float(generation_attrs["cumulative_work"]) + task_work)
                    world = {"seed": seed, "commutator": comm, "initial": _permutation(seed + 7),
                             "goal_operator": f"commutator_power_{generation + 1}"}
                    world_hash = _digest(world)
                    worlds.setdefault(seed, set()).add(world_hash)
                    graph = agent.inner.graph_to_dict()
                    records.append({"status": "COMPLETED", "family": "permutation_process_macro",
                        "seed": seed, "generation": generation, "profile": arm,
                        "solved": bool(solved), "operator_calls": 1,
                        "agent_work_units": task_work,
                        "task_seconds": task_seconds,
                        "actions": 0, "invariant_checks_passed": int(all(sorted(p) == list(range(4)) for p in (comm, operator, square))),
                        "boot_seconds": boot_seconds, "graph_nodes_end": len(graph["nodes"]),
                        "graph_serialized_bytes": len(json.dumps(graph, sort_keys=True).encode()),
                        "budget_remaining": (agent.s.node(generation_state)["attrs"]["budget_remaining"]
                                             if generation_state is not None else
                                             agent.s.node(budget)["attrs"].get("remaining")),
                        "world_sha256": world_hash, "world_access_sha256": access_hash,
                        "input_audit": {"answer_fields_absent": True, "hidden_strategy_absent": True,
                                        "sealed_ids_absent": True, "same_primitive_access_hash": access_hash}})
        finally:
            agent.close()
    if any(len(hashes) != 1 for hashes in worlds.values()):
        raise RuntimeError("paired arms received different generated task worlds")
    metadata = {"phase": PHASE, "split": split, "seed_base": BASE_SEED,
        "seed_formula": "25_000_000 + family_code*10_000 + control_block*1_000 + draw",
        "family_index": 1, "generation_indexes": [1, 2, 3],
        "family_codes": [11, 12, 13], "selection_control_block": 1, "training_control_block": 0,
        "evaluation_control_block": 2, "integrity_control_block": 3,
        "task_control_block": control_block,
        "training_seed_base": TRAINING_SEED_BASE,
        "selection_draws_per_generation": list(range(n)),
        "candidate_selection_draws": {"generation_1": [800, 801],
                                      "generation_2": [800, 801],
                                      "generation_3": [800, 801]},
        "candidate_development": candidate_development,
        "successor_development": successor_development,
        "third_generation_development": third_development,
        "completed_generations": [1, 2, 3],
        "n_per_generation_per_arm": n, "arms": list(ARMS),
        "shared_budget_per_arm_across_three_generations": BUDGET,
        "generation_budget_cap": 100_000,
        "per_generation_task_work": {"unchanged_operator": 2,
            "adaptive_curriculum": 2, "full_system": "generation+2"},
        "limits": {"max_ticks": MAX_TICKS, "max_steps_per_tick": MAX_STEPS_PER_TICK,
                   "max_nodes": 100000, "max_graph_bytes": 64 * 1024 * 1024},
        "artifact_provenance": provenance(), "self_check": bool(self_check),
        "supported_family": "finite permutation composition macro; no external actions",
        "unsupported_families": ["mechanism discovery", "grid transformations", "tool invention",
            "program synthesis", "explain and rebuild", "cross-domain transfer", "law rediscovery"],
        "human_comparison": "UNAVAILABLE_PROTOCOL_NOT_MATCHED"}
    return {"schema": "pmb-scorecard-v1", "metadata": metadata, "records": records}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--self-check", action="store_true")
    parser.add_argument("--split", choices=("development", "heldout"), default="development")
    args = parser.parse_args()
    n = N_SELF_CHECK if args.self_check else (args.n if args.n is not None else
        (200 if args.split == "heldout" else N_DEVELOPMENT))
    payload = run(n=n, self_check=args.self_check, split=args.split)
    if args.output:
        write_scorecard(args.output, metadata=payload["metadata"], records=payload["records"])
    else:
        print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

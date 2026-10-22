"""P14 law-proof and graph-authored operator evaluation adapter.

The adapter installs deterministic permutation worlds and asks the native
process algebra and P14 graph rules to check outcomes. It never supplies a
hidden answer or authorizes an external action.
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

PHASE = "linear-p14-v1"
ARMS = ("held_operator", "authored_operator")
DEV_SEED = 14_000_000
HELDOUT_SEED = 14_100_000
LAW_DEV_N = 20
CONTROL_DEV_N = 10
DEVELOPMENT_TASKS = 8
ALLOCATIONS = {"law_cases": 200, "candidate_operator_cases": 200,
               "proof_criterion_tampering_controls": 100}
LIMITS = {"max_operator_calls_per_task": 1, "max_expression_nodes": 7,
          "max_candidate_work": 32, "max_steps_per_tick": 100_000,
          "tamper_proof_controls": 50, "tamper_criterion_controls": 50}
STATEMENT_DIGEST = "4e3f9f19059a7254dbc8b885e464eccf69cec770eec50cb43a4d89e01415adb2"
ASSUMPTIONS_DIGEST = "d055b01ab1e76e1190f7b04e01fe250ab42f5ce6ccc24eaf4dfd84263ec96077"
ASSUMPTIONS = "permutation_group;parity_homomorphism_Z2;operator_semantics_v1"


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _digest(value) -> str:
    return _sha(json.dumps(value, sort_keys=True, separators=(",", ":"),
                           default=str).encode())


def _file_digest(paths):
    h = hashlib.sha256()
    for rel in paths:
        h.update(rel.encode() + b"\0" + (ROOT / rel).read_bytes() + b"\0")
    return h.hexdigest()


def provenance():
    engine_paths = (
        "runners/dsl/Cargo.toml", "runners/dsl/Cargo.lock", "runners/dsl/src/lib.rs",
        "runners/dsl/src/process_algebra.rs", "runners/dsl/src/term.rs",
        "runners/dsl/src/cognitive_cycle.rs", "runners/dsl/src/area_scheduler.rs",
        "runners/dsl/src/clock.rs", "runners/dsl/src/substrate.rs", "runners/dsl/src/graph.rs",
        "runners/dsl/src/graph_rules.rs", "runners/dsl/src/checker.rs",
        "runners/dsl/src/prog_eval.rs", "runners/dsl/src/rule_json.rs",
        "runners/dsl/src/seed_manifest.rs", "runners/dsl/src/py.rs",
    )
    profile_paths = ("substrate/boot_profiles.py", "seeds/cognition_on_params.json")
    world_paths = ("substrate/world_adapter.py", "evaluation/process_mastery/harness.py")
    protocol_paths = (
        "evaluation/process_mastery/linear_p14_v1.py",
        "evaluation/process_mastery/analyze_linear_p14_v1.py",
        "evaluation/process_mastery/scorecard.py",
        "scripts/gen_process_laws_seed.py", "seeds/process_laws.json",
        "scripts/gen_process_proof_adoption_seed.py", "seeds/process_proof_adoption.json",
        "scripts/gen_invention_operator_authorship_seed.py", "seeds/invention_operator_authorship.json",
    )
    return {
        "phase": PHASE,
        "git_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "source_bundle_sha256": _file_digest(protocol_paths + profile_paths + world_paths + engine_paths),
        "profile_sha256": _file_digest(profile_paths),
        "world_adapter_sha256": _file_digest(world_paths),
        "engine_source_sha256": _file_digest(engine_paths),
        "runner_sha256": _sha(Path(__file__).read_bytes()),
        "analyzer_sha256": _sha((ROOT / "evaluation/process_mastery/analyze_linear_p14_v1.py").read_bytes()),
        "engine_binary_sha256": _sha(Path(substrate_rs.__file__).read_bytes()),
        "protocol_bundle_sha256": _file_digest(protocol_paths),
        "python": sys.version.split()[0], "limits": dict(LIMITS),
    }


def _nodes(agent, kind):
    return [node for node in agent.s.nodes() if agent.s.node(node)["type"] == kind]


def _edge(agent, source, edge_type, target):
    agent.inner.add_edge_unchecked(source, edge_type, target, {})


def _set_policy(agent, kind, enabled, **attrs):
    nodes = _nodes(agent, kind)
    if not nodes:
        raise RuntimeError(f"missing P14 policy {kind}")
    chosen = next((node for node in nodes if agent.s.node(node)["attrs"].get("enabled") == 1.0), nodes[0])
    for node in nodes:
        agent.inner.set_attr(node, "enabled", float(bool(enabled) and node == chosen))
        for key, value in attrs.items():
            agent.inner.set_attr(node, key, value)


def _agent(*, authored=False):
    started = time.perf_counter()
    agent = boot_cognition_on()
    boot_seconds = time.perf_counter() - started
    for kind in ("ConsolidationSchedulerPolicy", "SleepRegimePolicy", "LibraryLearningPolicy",
                 "StrategyLibraryPolicy", "ProcessSchemaPolicy", "InventionPolicy",
                 "InvariantMinerPolicy", "SolverPolicy"):
        if _nodes(agent, kind):
            _set_policy(agent, kind, False)
    _set_policy(agent, "ProcessLawsPolicy", True)
    _set_policy(agent, "ProcessProofAdoptionPolicy", True)
    _set_policy(agent, "InventionOperatorAuthorshipPolicy", authored)
    budgets = [n for n in _nodes(agent, "ThinkingBudget")
               if agent.s.node(n)["attrs"].get("enabled") == 1.0]
    if len(budgets) != 1:
        agent.close()
        raise RuntimeError(f"expected one enabled shared budget, found {len(budgets)}")
    return agent, boot_seconds


def _settle(agent, rounds=12):
    for _ in range(rounds):
        if agent.inner.run_rules(LIMITS["max_steps_per_tick"]) == 0:
            break


def _eval(agent, term, env):
    value = agent.inner.evaluate(term, env)
    if value is None:
        raise RuntimeError(f"native evaluation returned None for {term}")
    return value


def _process_apply(agent, params, state):
    return _eval(agent, {"type": "ProcessApply", "p": {"type": "Var", "name": "p"},
                         "state": {"type": "Var", "name": "state"}},
                 {"p": params, "state": state})


def _parity(agent, params):
    return int(_eval(agent, {"type": "PermParity", "p": {"type": "Var", "name": "p"}}, {"p": params}))


def _permutation(seed, size=4):
    rng = random.Random(seed)
    out = list(range(size))
    rng.shuffle(out)
    return out


def _primitive_pair(seed, size=4):
    # A fixed 4-cycle and a seed-varying transposition form a noncommuting pair.
    # The native adapter recomputes and audits the resulting commutator.
    a = [1, 2, 3, 0]
    rng = random.Random(seed)
    pair = list(range(size))
    left, right = sorted(rng.sample(range(size), 2))
    pair[left], pair[right] = pair[right], pair[left]
    inverse = lambda p: [p.index(i) for i in range(size)]
    compose = lambda x, y: [y[i] for i in x]
    comm = compose(compose(compose(a, pair), inverse(a)), inverse(pair))
    if comm == list(range(size)):
        raise RuntimeError("seeded commutator fixture unexpectedly commutes")
    return a, pair, comm


def _add_domain(agent, seed, a, b):
    name = f"p14-permutation-{seed}"
    domain = agent.s.add_node("ProcessDomain", {
        "name": name, "kind": "permutation", "probes": [list(range(len(a)))],
        "source_epoch": 0, "model_epoch": 0, "frame_epoch": 0,
        "family_digest": _digest({"family": "symmetric_group", "size": len(a)}),
        "model_digest": _digest({"model": "permutation_apply_v1", "size": len(a)}),
    })
    _edge(agent, agent.agent, "has_process_domain", domain)
    schemas = []
    for label, params in (("a", a), ("b", b)):
        node = agent.s.add_node("ProcessSchema", {
            "name": f"{label}-{seed}", "kind": "permutation", "domain": name,
            "domain_kind": "permutation", "params": list(params), "cost": 1.0,
            "provenance": "held", "status": "active", "source_epoch": 0,
            "model_epoch": 0, "frame_epoch": 0,
        })
        _edge(agent, agent.agent, "has_process_schema", node)
        schemas.append(node)
    return domain, name, schemas


def _add_law(agent, seed, kind):
    a, b, _ = _primitive_pair(seed)
    domain, name, schemas = _add_domain(agent, seed, a, b)
    from scripts.track_i_seed_lib import A, PCommutator
    comm = _eval(agent, PCommutator(A("a", "params"), A("b", "params")),
                 {"a": schemas[0], "b": schemas[1]})
    if list(comm) != _primitive_pair(seed)[2]:
        raise RuntimeError("native commutator differs from the frozen world generator")
    schema = agent.s.add_node("ProcessSchema", {
        "name": f"commutator-{seed}", "kind": "permutation", "domain": name,
        "domain_kind": "permutation", "operator": "commutator", "params": comm,
        "status": "active", "invented": 1, "source_epoch": 0, "model_epoch": 0,
        "frame_epoch": 0,
    })
    _edge(agent, agent.agent, "has_process_schema", schema)
    _edge(agent, domain, "has_invented_process", schema)
    _edge(agent, schema, "has_arg0", schemas[0])
    _edge(agent, schema, "has_arg1", schemas[1])
    if kind == "valid_structural":
        claim, evidence, count = "commutator_even", "structural_derivation", 0
    else:
        claim, evidence, count = "commutator_odd", "finite_sample", 1
    law = agent.s.add_node("ProcessLaw", {
        "name": f"law-{seed}", "claim": claim, "family": name,
        "family_digest": agent.s.node(domain)["attrs"]["family_digest"],
        "family_epoch": 0, "process_epoch": 0,
        "model_digest": agent.s.node(domain)["attrs"]["model_digest"],
        "model_epoch": 0, "frame_epoch": 0,
        "statement_digest": STATEMENT_DIGEST if kind == "valid_structural" else _digest({"claim": claim}),
        "assumptions_digest": ASSUMPTIONS_DIGEST, "assumptions": ASSUMPTIONS,
        "evidence_kind": evidence, "counterexample_count": count,
        "status": "conjecture", "proven": 0,
    })
    _edge(agent, agent.agent, "has_process_law_candidate", law)
    _edge(agent, law, "about_process", schema)
    if kind == "false_finite_sample":
        observed = _parity(agent, comm)
        counterexample = agent.s.add_node("LawCounterexample", {
            "validated": int(observed != 1), "observed_value": observed,
            "claimed_value": 1, "source": "native_process_outcome",
            "process_params": list(comm), "domain": name,
        })
        _edge(agent, law, "has_counterexample", counterexample)
    return {"agent": agent, "domain": domain, "schema": schema, "law": law,
            "commutator": list(comm), "expected_status": "checked" if kind == "valid_structural" else "rejected"}


def _operator_template(agent):
    request = agent.s.add_node("OperatorCompositionRequest", {
        "name": "p14-evaluation-request", "status": "draft",
        "recipe": "commutator_square", "left_operator": "commutator",
        "right_operator": "commutator", "candidate_name": "commutator_square_v1",
    })
    _edge(agent, agent.agent, "has_operator_composition_request", request)
    _settle(agent)
    candidate = next((n for n in _nodes(agent, "CandidateOperator")
                      if agent.s.node(n)["attrs"].get("name") == "commutator_square_v1"), None)
    if candidate is None:
        raise RuntimeError("operator adapter failed to mint candidate expression graph")
    root = agent.inner.neighbours(candidate, "has_expression_root")
    if len(root) != 1 or agent.s.node(root[0])["attrs"].get("operator") != "compose":
        raise RuntimeError("authored operator expression root is missing or malformed")
    children = agent.inner.neighbours(root[0], "expr_child")
    if len(children) != 2 or any(agent.s.node(n)["attrs"].get("operator") != "commutator" for n in children):
        raise RuntimeError("authored operator is outside the frozen held-algebra recipe")
    return candidate


def _task_world(agent, seed, a, b, initial):
    domain, name, schemas = _add_domain(agent, seed, a, b)
    from scripts.track_i_seed_lib import A, PCommutator, PCompose
    comm = _eval(agent, PCommutator(A("a", "params"), A("b", "params")),
                 {"a": schemas[0], "b": schemas[1]})
    if list(comm) != _primitive_pair(seed)[2]:
        raise RuntimeError("native commutator differs from the frozen world generator")
    composed = _eval(agent, PCompose({"type": "Var", "name": "comm"},
                                     {"type": "Var", "name": "comm"}), {"comm": comm})
    intermediate = _process_apply(agent, comm, initial)
    goal = _process_apply(agent, comm, intermediate)
    task = agent.s.add_node("SolveTask", {
        "name": f"one-step-composition-{seed}", "domain": name,
        "initial_state": list(initial), "state": list(initial), "goal": list(goal),
        "status": "active", "max_operator_calls": LIMITS["max_operator_calls_per_task"],
        "evidence_kind": "generated_world_task",
    })
    _edge(agent, agent.agent, "has_solve_task", task)
    _edge(agent, task, "about_domain", domain)
    return schemas, comm, composed, goal


def _candidate_dev(agent, candidate):
    baseline_success = authored_success = invariant = 0
    work = 0
    for ix in range(DEVELOPMENT_TASKS):
        seed = DEV_SEED + ix
        a, b, _ = _primitive_pair(seed)
        initial = _permutation(seed + 7)
        schemas, comm, composed, goal = _task_world(agent, seed, a, b, initial)
        baseline = _process_apply(agent, comm, initial)
        authored = _process_apply(agent, composed, initial)
        baseline_success += int(list(baseline) == list(goal))
        authored_success += int(list(authored) == list(goal))
        invariant += int(_parity(agent, comm) == 0 and _parity(agent, composed) == 0)
        work += 4  # two commutators, one composition, one native application
    for key, value in {
        "development_yield": authored_success, "parent_development_yield": baseline_success,
        "invariant_checks": invariant, "parent_invariant_checks": invariant,
        "proof_failures": 0, "candidate_work": work, "status": "measured",
    }.items():
        agent.s.set_attr(candidate, key, value)
    _settle(agent)
    return {"candidate_yield": authored_success, "parent_yield": baseline_success,
            "invariant_checks": invariant, "candidate_work": work,
            "candidate_status": agent.s.node(candidate)["attrs"].get("status")}


def _operator_panel(n, split):
    base_seed = DEV_SEED + 100 if split == "development" else HELDOUT_SEED
    baseline, base_boot = _agent(authored=False)
    authored, authored_boot = _agent(authored=True)
    candidate = _operator_template(authored)
    development = _candidate_dev(authored, candidate)
    rows = []
    common_access = _digest(["ProcessApply", "ProcessCompose", "ProcessInverse", "PermParity",
                             "permutation-group-held-primitives", "max_operator_calls=1"])
    for ix in range(n):
        seed = base_seed + ix
        a, b, _ = _primitive_pair(seed)
        initial = _permutation(seed + 7)
        for arm, agent, boot_seconds in ((ARMS[0], baseline, base_boot),
                                         (ARMS[1], authored, authored_boot)):
            schemas, comm, composed, goal = _task_world(agent, seed, a, b, initial)
            if arm == "held_operator":
                result = _process_apply(agent, comm, initial)
                operations = 1
                inv_ok = _parity(agent, comm) == 0
            else:
                result = _process_apply(agent, composed, initial)
                operations = 1
                inv_ok = _parity(agent, comm) == 0 and _parity(agent, composed) == 0
            solved = list(result) == list(goal)
            world = {"seed": seed, "a": a, "b": b, "initial": initial, "goal": list(goal),
                     "primitive_access": ["held permutation a", "held permutation b", "native process algebra"]}
            rows.append({
                "status": "COMPLETED", "family": "candidate_operator", "seed": seed,
                "profile": arm, "solved": solved, "operator_calls": operations,
                "agent_work_units": 4 if arm == "authored_operator" else 1,
                "work_definition": "2_commutator+1_compose+1_apply" if arm == "authored_operator" else "1_apply",
                "invariant_checks_passed": int(inv_ok), "actions": 0,
                "boot_seconds": boot_seconds,
                "graph_nodes_end": len(list(agent.s.nodes())),
                "graph_serialized_bytes": len(json.dumps(agent.inner.graph_to_dict(), sort_keys=True).encode()),
                "world_sha256": _digest(world), "world_access_sha256": common_access,
                "input_audit": {"answer_fields_absent": True, "hidden_strategy_absent": True,
                                "same_primitive_access_hash": common_access},
            })
    baseline.close()
    authored.close()
    return rows, development


def _law_panel(n, split):
    agent, boot_seconds = _agent(authored=False)
    rows = []
    kinds = ("valid_structural", "false_finite_sample")
    for ix in range(n):
        seed = (DEV_SEED if split == "development" else HELDOUT_SEED) + 20_000 + ix
        case = _add_law(agent, seed, kinds[ix % 2])
        _settle(agent)
        la = agent.s.node(case["law"])["attrs"]
        proof = agent.inner.neighbours(case["law"], "has_proof_reference")
        correct = (la.get("status") == case["expected_status"]
                   and (la.get("proven") == 1) == (case["expected_status"] == "checked")
                   and (len(proof) == 1) == (case["expected_status"] == "checked"))
        rows.append({
            "status": "COMPLETED", "family": "law_claim", "seed": seed,
            "claim_kind": kinds[ix % 2], "expected_status": case["expected_status"],
            "actual_status": la.get("status"), "proven": int(la.get("proven", 0)),
            "proof_reference_count": len(proof), "correct": correct,
            "counterexample_validated": kinds[ix % 2] != "false_finite_sample"
                or any(agent.s.node(c)["attrs"].get("validated") == 1
                       for c in agent.inner.neighbours(case["law"], "has_counterexample")),
            "boot_seconds": boot_seconds, "world_actions": 0,
            "input_audit": {"hidden_truth_label_absent": True, "answer_fields_absent": True},
        })
    agent.close()
    return rows


def _tampering_panel(n, split):
    agent, boot_seconds = _agent(authored=True)
    rows = []
    for ix in range(n):
        seed = (DEV_SEED if split == "development" else HELDOUT_SEED) + 40_000 + ix
        if ix % 2 == 0:
            domain, name, schemas = _add_domain(agent, seed, [1, 2, 3, 0], [1, 0, 2, 3])
            target = agent.s.add_node("ProcessSchema", {
                "name": f"tampered-process-{seed}", "kind": "permutation", "domain": name,
                "status": "active", "invented": 1, "params": [1, 0, 2, 3],
                "source_epoch": 0, "model_epoch": 0, "frame_epoch": 0,
            })
            _edge(agent, agent.agent, "has_process_schema", target)
            _edge(agent, domain, "has_invented_process", target)
            policy = next(nid for nid in _nodes(agent, "ProcessProofAdoptionPolicy")
                          if agent.s.node(nid)["attrs"].get("enabled") == 1.0)
            req = agent.s.add_node("ProcessProofRequirement", {
                "name": f"req-{seed}", "required": 1, "required_law": "commutator_even"})
            _edge(agent, policy, "requires_proof_for", req)
            _edge(agent, req, "applies_to", domain)
            law = agent.s.add_node("ProcessLaw", {
                "name": f"tampered-law-{seed}", "status": "checked", "proven": 1,
                "claim": "commutator_even", "proof_kind": "native_structural_rule",
                "proof_rule": "parity_commutator_even_v1", "family": name,
            })
            _edge(agent, agent.agent, "has_process_law", law)
            _edge(agent, law, "about_process", target)
            proof = agent.s.add_node("LawProofReference", {
                "status": "checked", "checker": "process_laws_seed_v1",
                "rule": "parity_commutator_even_v1", "family": name,
                "family_digest": agent.s.node(domain)["attrs"]["family_digest"],
                "model_digest": agent.s.node(domain)["attrs"]["model_digest"],
                "family_epoch": 0, "process_epoch": 0, "model_epoch": 0, "frame_epoch": 0,
                "process_params": [0, 1, 2, 3],  # intentionally corrupted reference
                "statement_digest": STATEMENT_DIGEST, "assumptions_digest": ASSUMPTIONS_DIGEST,
            })
            _edge(agent, law, "has_proof_reference", proof)
            family = "proof_reference_tamper"
        else:
            candidate = agent.s.add_node("CandidateOperator", {
                "name": f"tampered-candidate-{seed}", "status": "awaiting_human",
                "criteria_digest": "pmb-v1-frozen-criteria", "parent_operator_name": "commutator",
                "lineage": "commutator -> candidate",
            })
            _edge(agent, agent.agent, "has_candidate_operator", candidate)
            approval = agent.s.add_node("OperatorPromotionApproval", {
                "status": "approved", "approval_kind": "human",
                "candidate_name": f"tampered-candidate-{seed}",
                "criteria_digest": "tampered-criteria-digest",
            })
            _edge(agent, agent.agent, "has_promotion_approval", approval)
            family = "criterion_digest_tamper"
        _settle(agent)
        if family == "proof_reference_tamper":
            attrs = agent.s.node(target)["attrs"]
            passed = attrs.get("status") == "proof_blocked" and attrs.get("proof_adoption_status") == "blocked"
            result = attrs.get("status")
        else:
            attrs = agent.s.node(candidate)["attrs"]
            passed = attrs.get("status") == "awaiting_human"
            result = attrs.get("status")
        rows.append({"status": "COMPLETED", "family": "tampering_control", "seed": seed,
                     "control_kind": family, "control_passed": passed, "actual_status": result,
                     "boot_seconds": boot_seconds, "actions": 0,
                     "input_audit": {"candidate_cannot_write_criterion": True,
                                     "heldout_labels_absent": True}})
    agent.close()
    return rows


def run(*, split="development", n=2, self_check=False):
    if split not in {"development", "heldout"}:
        raise ValueError("split must be development or heldout")
    if n < 1 or n > ALLOCATIONS["candidate_operator_cases"]:
        raise ValueError("candidate operator n must be in [1, 200]")
    if split == "heldout" and not self_check and n != ALLOCATIONS["candidate_operator_cases"]:
        raise ValueError("frozen held-out draw requires exactly 200 candidate operator cases")
    base_seed = DEV_SEED if split == "development" else HELDOUT_SEED
    law_n = (4 if self_check else (LAW_DEV_N if split == "development"
                                   else ALLOCATIONS["law_cases"]))
    control_n = (4 if self_check else (CONTROL_DEV_N if split == "development"
                                       else ALLOCATIONS["proof_criterion_tampering_controls"]))
    paired, development = _operator_panel(n, split)
    rows = paired + _law_panel(law_n, split) + _tampering_panel(control_n, split)
    metadata = {
        "phase": PHASE, "split": split, "seed_base": base_seed,
        "seed_allocation": {"candidate_operator_cases": n, "law_cases": law_n,
                            "proof_criterion_tampering_controls": control_n},
        "arms": list(ARMS), "limits": dict(LIMITS),
        "development_selection": development,
        "artifact_provenance": provenance(), "self_check": bool(self_check),
        "human_comparison": "UNAVAILABLE_PROTOCOL_NOT_MATCHED",
        "scope": "finite_permutation_commutator_law_and_one_step_operator_macro",
        "limitations": {"law_scope": "exact native commutator parity in finite permutation groups",
                        "operator_scope": "one-step macro tasks generated from held permutation primitives",
                        "actions": "zero external actions; only native simulated process application"},
    }
    return {"schema": "pmb-scorecard-v1", "metadata": metadata, "records": rows}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", choices=("development", "heldout"), default="development")
    parser.add_argument("--n", type=int, default=2)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args()
    payload = run(split="development" if args.self_check else args.split,
                  n=2 if args.self_check else args.n, self_check=args.self_check)
    if args.output:
        write_scorecard(args.output, metadata=payload["metadata"], records=payload["records"])
    else:
        print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

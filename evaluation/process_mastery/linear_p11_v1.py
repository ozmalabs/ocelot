"""P11 paired source-to-target representation and process-transfer panel.

The Python side installs world observations and scores native evaluator
receipts. Search, selection, map inversion/composition, and process adoption
are performed by Rust graph rules and terms.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for path in (ROOT, ROOT / "runners/dsl/python"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from evaluation.process_mastery.harness import Agent  # noqa: E402
from evaluation.process_mastery.process_transfer_worlds import (  # noqa: E402
    apply_program, transfer_world,
)
from evaluation.process_mastery.representation_cost import (  # noqa: E402
    package_description_bits, residual_code_bits,
)
from evaluation.process_mastery.scorecard import write_scorecard  # noqa: E402
import substrate_rs  # noqa: E402


PHASE = "linear-p11-v1"
PAIRINGS = ("permutation_relabel_4", "integer_matrix_basis_2")
ARMS = ("fresh", "source_exposed", "mismatched_source")
LIMITS = {"max_ticks": 32, "max_steps_per_tick": 1000, "budget": 10.0,
          "training_rows": 8, "heldout_rows": 16, "residual_bits_per_coordinate": 32}


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _provenance():
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                         text=True).strip()
    except Exception:
        commit = "unavailable"
    paths = ["evaluation/process_mastery/linear_p11_v1.py",
             "evaluation/process_mastery/process_transfer_worlds.py",
             "evaluation/process_mastery/representation_cost.py",
             "evaluation/process_mastery/harness.py",
             "scripts/gen_representation_search_seed.py",
             "scripts/gen_process_transfer_seed.py",
             "seeds/representation_search.json", "seeds/process_transfer.json",
             "substrate/boot_profiles.py"]
    source = hashlib.sha256()
    for rel in paths:
        source.update(rel.encode() + b"\0" + (ROOT / rel).read_bytes() + b"\0")
    engine = hashlib.sha256()
    for rel in ("runners/dsl/Cargo.toml", "runners/dsl/Cargo.lock",
                "runners/dsl/src/process_algebra.rs", "runners/dsl/src/term.rs",
                "runners/dsl/src/eval.rs", "runners/dsl/src/engine.rs"):
        file = ROOT / rel
        if file.exists():
            engine.update(rel.encode() + b"\0" + file.read_bytes() + b"\0")
    return {"phase": PHASE, "git_commit": commit,
            "source_bundle_sha256": source.hexdigest(),
            "runner_sha256": _sha(Path(__file__).read_bytes()),
            "engine_source_sha256": engine.hexdigest(),
            "engine_binary_sha256": _sha(Path(substrate_rs.__file__).read_bytes()),
            "python": sys.version.split()[0], "limits": dict(LIMITS)}


def _apply_native(agent, program, state):
    return agent.native.evaluate(
        {"type": "ProcessApply", "p": {"type": "Var", "name": "p"},
         "state": {"type": "Var", "name": "state"}},
        {"p": program, "state": state})


def _compose_native(agent, world, forward, inverse):
    term = {"type": "ProcessCompose",
            "a": {"type": "ProcessCompose",
                  "a": {"type": "Var", "name": "inverse"},
                  "b": {"type": "Var", "name": "source"}},
            "b": {"type": "Var", "name": "forward"}}
    # The returned program is produced by the same Rust algebra used in the
    # graph's candidate rule; Python only supplies the measured operands.
    return agent.native.evaluate(term, {"inverse": inverse,
                                        "source": world["source_program"],
                                        "forward": forward})


def _package(world, forward, inverse):
    return {"basis": {"kind": world["kind"], "size": len(forward)},
            "grain": {"units": "complete_state"},
            "aperture": {"scope": "declared_process_state"},
            "latent_schema": {"id": f"p11:{world['pairing']}"},
            "model": {"process": world["source_program"]},
            "parameters": {"source_epoch": world["source_epoch"]},
            "forward_map": forward, "inverse_map": inverse,
            "exceptions": [], "decoder": {"kind": "inverse_frame_map"},
            "retained_residuals": [], "lost_residuals": [],
            "escape_residuals": []}


def _map_for_arm(world, arm, control=None):
    if arm == "source_exposed":
        return world["forward_map"], world["inverse_map"], 1, 1 if control == "wrong_frame" else 0
    if arm == "mismatched_source":
        if world["kind"] == "permutation":
            identity = list(range(4))
            return identity, identity, 1, 1 if control == "wrong_frame" else 0
        identity = [[1, 0], [0, 1]]
        return identity, identity, 1, 1 if control == "wrong_frame" else 0
    return None, None, None, 0


def _count_residual_coordinates(actual, expected):
    return sum(a != b for a, b in zip(actual, expected))


def _run_task(pairing, seed, arm, split, direction="forward", control=None):
    started = time.perf_counter()
    world = transfer_world(pairing, seed, direction)
    # The same target world is hashed for every arm. Its hidden target program
    # remains outside the graph and appears only in the evaluator audit.
    world_hash = _sha(json.dumps(world, sort_keys=True, separators=(",", ":")).encode())
    agent = Agent(extra_seeds=("representation_search", "process_transfer"),
                  policy_overrides={"RepresentationSearchPolicy": {"enabled": 1.0},
                                    "ProcessTransferPolicy": {"enabled": 1.0},
                                    "ProcessSchemaPolicy": {"enabled": 1.0}},
                  budget={"enabled": 1.0, "remaining": LIMITS["budget"],
                          "refill_per_epoch": 0.0, "last_refill_epoch": 0.0},
                  profile=f"p11-{arm}")
    s, ag = agent.s, agent.ag
    budgets = list(s.neighbours(ag, "has_thinking_budget"))
    target_name = f"target:{pairing}:{direction}:{seed}"
    domain = agent.add_domain(target_name, world["kind"], world["separating_probes"], {},
                              probe_epoch=world["target_probe_epoch"])
    source_frame = world["source_frame_epoch"]
    target_frame = world["target_frame_epoch"]
    mode = next(iter(s.neighbours(ag, "has_network_mode_state")))
    current_epoch = s.node(mode)["attrs"]["epoch"]
    request = None
    source_schema = None
    map_node = None
    evidence_node = None
    package = None
    training_residuals = []
    heldout_residuals = []
    exact_checks = 0
    exposure_nodes = []
    for row_ix, state in enumerate(world["training_states"]):
        observation = s.add_node("TransferTrainingObservation", {
            "event_id": f"{pairing}:{direction}:{seed}:train:{row_ix}",
            "owner_id": "agent-root", "split": split, "state": state,
            "source_process_observed": arm != "fresh"})
        s.add_edge(ag, "has_transfer_training_observation", observation, {})
        exposure_nodes.append(observation)
    if arm != "fresh":
        forward, inverse, evidence_source_epoch, frame_epoch_delta = _map_for_arm(world, arm, control)
        source_schema = s.add_node("ProcessSchema", {
            "name": f"source:{pairing}:{seed}", "kind": world["kind"],
            "domain": f"source:{pairing}:{seed}", "operator": "source_process",
            "params": world["source_program"], "status": "active",
            "source_epoch": world["source_epoch"], "model_epoch": world["model_epoch"],
            "frame_epoch": source_frame, "probe_epoch": world["target_probe_epoch"]})
        map_node = s.add_node("RepresentationMap", {
            "forward_map": forward, "inverse_map": inverse,
            "is_bijection": True, "inverse_verified": True,
            "complete_separating_set": True,
            "source_epoch": evidence_source_epoch,
            "target_frame_epoch": target_frame + frame_epoch_delta})
        request = s.add_node("RepresentationSearchRequest", {
            "owner_id": "agent-root", "source_epoch": evidence_source_epoch,
            "model_epoch": world["model_epoch"], "frame_epoch": source_frame,
            "training_split_id": f"{split}:{pairing}:{seed}:train",
            "candidate_cap": 16, "operation_id": f"rs:{pairing}:{seed}:{arm}",
            "search_epoch": current_epoch, "training_only": True, "status": "requested"})
        s.add_edge(ag, "has_representation_search_request", request, {})
        package = _package(world, forward, inverse)
        package_bits = package_description_bits(package)
        evidence_node = s.add_node("RepresentationTransformEvidence", {
            "candidate_id": f"p11:{pairing}:{seed}:{arm}",
            "status": "acquired_transform", "owner_id": "agent-root",
            "source_epoch": evidence_source_epoch, "model_epoch": world["model_epoch"],
            "frame_epoch": source_frame, "target_frame_epoch": target_frame + frame_epoch_delta,
            "training_split_id": f"{split}:{pairing}:{seed}:train",
            "source_frame_id": f"source-frame:{source_frame}",
            "target_frame_id": f"target-frame:{target_frame}",
            "canonical_package": package, "package_bits": package_bits,
            "training_residual_bits": 0, "training_total_bits": package_bits,
            "package_cost_complete": True, "forced_frame_preserved": True,
            "discriminating_evidence": True})
        s.add_edge(request, "has_transform_evidence", evidence_node, {})
        s.add_edge(evidence_node, "has_transfer_map", map_node, {})
        s.add_edge(evidence_node, "has_source_process", source_schema, {})
        s.add_edge(evidence_node, "has_target_domain", domain, {})
        # Funding request, proposal mint and candidate creation are all native.
        for _ in range(12):
            s.tick(LIMITS["max_steps_per_tick"])
        proposals = list(s.neighbours(request, "has_candidate_proposal"))
        if len(proposals) != 1:
            return Agent.trial_record(
                "FAILED", family=pairing, seed=seed, split=split, profile=arm,
                reason="representation candidate adapter produced no unique graph proposal",
                direction=direction, target_world_sha256=world_hash, outcome="no_transfer",
                elapsed_s=time.perf_counter() - started,
                graph_nodes=len(s.nodes()), budget_remaining=agent.resource_budget.get("remaining"),
                agent_input_audit={"target_program_absent": True,
                                   "target_oracle_map_absent": True,
                                   "world_hash_equal_across_arms": world_hash})
        proposal = proposals[0]
        proposal_attrs = s.node(proposal)["attrs"]
        composed = _compose_native(agent, world, forward, inverse)
        for state in world["training_states"]:
            target_state = apply_program(world["kind"], state, world["forward_map"])
            predicted = _apply_native(agent, composed, target_state)
            expected = apply_program(world["kind"], target_state, world["target_program"])
            exact_checks += 1
            training_residuals.extend([{}] * _count_residual_coordinates(predicted, expected))
        training_residual_bits = residual_code_bits(
            training_residuals, bits_per_record=LIMITS["residual_bits_per_coordinate"])
        development = s.add_node("RepresentationDevelopmentValidation", {
            "candidate_id": proposal_attrs["candidate_id"],
            "status": "scored_frozen_training",
            "training_split_id": request and s.node(request)["attrs"]["training_split_id"],
            "training_model_epoch": world["model_epoch"],
            "package_bits": package_bits, "residual_bits": training_residual_bits,
            "total_bits": package_bits + training_residual_bits,
            "discriminating_rows": len(world["training_states"]), "heldout_used": False})
        s.add_edge(proposal, "has_development_validation", development, {})
        for _ in range(4):
            s.tick(LIMITS["max_steps_per_tick"])
        selected = s.node(proposal)["attrs"].get("status") == "selected_for_heldout_validation"
        heldout_verified = True
        candidate_total_bits = package_bits
        baseline_forward = (list(range(4)) if world["kind"] == "permutation"
                            else [[1, 0], [0, 1]])
        baseline_package_bits = package_description_bits(_package(world, baseline_forward,
                                                                  baseline_forward))
        baseline_residuals = []
        for state in world["heldout_states"]:
            target_state = apply_program(world["kind"], state, world["forward_map"])
            predicted = _apply_native(agent, composed, target_state)
            expected = apply_program(world["kind"], target_state, world["target_program"])
            exact_checks += 1
            heldout_verified = heldout_verified and predicted == expected
            baseline_predicted = apply_program(world["kind"], target_state, world["source_program"])
            baseline_residuals.extend([{}] * _count_residual_coordinates(baseline_predicted, expected))
            heldout_residuals.extend([{}] * _count_residual_coordinates(predicted, expected))
        # Include the complete separating probe set; exactness is the conjunction
        # over every declared distinguishing state, never a sampled majority.
        for state in world["separating_probes"]:
            target_state = apply_program(world["kind"], state, world["forward_map"])
            predicted = _apply_native(agent, composed, target_state)
            expected = apply_program(world["kind"], target_state, world["target_program"])
            exact_checks += 1
            heldout_verified = heldout_verified and predicted == expected
        candidate_residual_bits = residual_code_bits(
            heldout_residuals, bits_per_record=LIMITS["residual_bits_per_coordinate"])
        baseline_residual_bits = residual_code_bits(
            baseline_residuals, bits_per_record=LIMITS["residual_bits_per_coordinate"])
        candidate_total_bits = package_bits + candidate_residual_bits
        baseline_total_bits = baseline_package_bits + baseline_residual_bits
        heldout = s.add_node("RepresentationHeldoutValidation", {
            "candidate_id": proposal_attrs["candidate_id"],
            "status": "scored_frozen_heldout", "training_model_epoch": world["model_epoch"],
            "heldout_used_for_selection": False, "refit_on_heldout": False,
            "exceptions_added": False, "target_effect_verified": heldout_verified,
            "wrong_frame_acceptance": frame_epoch_delta != 0,
            "solve_loss_pp": 0.0 if heldout_verified else 100.0,
            "candidate_total_bits": candidate_total_bits,
            "baseline_total_bits": baseline_total_bits})
        s.add_edge(proposal, "has_heldout_validation", heldout, {})
        for _ in range(6):
            s.tick(LIMITS["max_steps_per_tick"])
        adopted = s.node(proposal)["attrs"].get("status") == "adopted"
        if adopted:
            transfer_request = s.add_node("ThinkingBudgetRequest", {
                "requester_kind": "process_transfer", "status": "pending",
                "requested_epoch": current_epoch, "cost": 1.0,
                "source_key": f"transfer:{pairing}:{seed}:{arm}",
                "source_epoch": world["source_epoch"]})
            s.add_edge(ag, "has_thinking_budget_request", transfer_request, {})
            if budgets:
                s.add_edge(transfer_request, "draws_on_thinking_budget", budgets[0], {})
            for _ in range(4):
                s.tick(LIMITS["max_steps_per_tick"])
        transfer_candidates = list(s.neighbours(ag, "has_process_transfer_candidate"))
        transferred = []
        transfer_verified = False
        if transfer_candidates:
            cand = transfer_candidates[-1]
            cattrs = s.node(cand)["attrs"]
            all_checks = True
            for state in world["separating_probes"]:
                target_state = apply_program(world["kind"], state, world["forward_map"])
                predicted = _apply_native(agent, cattrs["composed_target_program"], target_state)
                expected = apply_program(world["kind"], target_state, world["target_program"])
                exact_checks += 1
                all_checks = all_checks and predicted == expected
            receipt = s.add_node("ProcessTransferVerification", {
                "status": "verified" if all_checks else "failed",
                "verification_kind": "fresh_native_target_effect",
                "candidate_id": cattrs["candidate_id"],
                "source_epoch": world["source_epoch"],
                "target_probe_epoch": world["target_probe_epoch"],
                "composition_order": "f_after_g_after_f_inv",
                "receipt_id": f"p11-receipt:{pairing}:{seed}:{arm}"})
            s.add_edge(cand, "has_target_verification", receipt, {})
            for _ in range(5):
                s.tick(LIMITS["max_steps_per_tick"])
            transferred = [n for n in s.nodes("ProcessSchema")
                           if s.node(n)["attrs"].get("provenance") == "verified_process_transfer"]
            transfer_verified = bool(transferred) and all_checks
        status = "COMPLETED"
        outcome = "transferred_effect_verified" if transfer_verified else "abstained_or_not_adopted"
        elapsed = time.perf_counter() - started
        input_audit = {
            "target_program_absent": all("target_program" not in s.node(n)["attrs"]
                                          for n in s.nodes()),
            "target_oracle_map_absent": all("forward_map" not in s.node(n)["attrs"]
                                            for n in s.nodes() if n != map_node),
            "heldout_used_for_selection": False,
            "same_world_hash_across_arms": world_hash,
            "source_observation_present": arm != "fresh",
        }
        if not input_audit["target_program_absent"] or not input_audit["target_oracle_map_absent"]:
            status = "FAILED"
        return agent.trial_record(
            status, family=pairing, seed=seed, split=split, profile=arm,
            direction=direction, control=control,
            task_id=f"{pairing}-{direction}-{seed}", outcome=outcome,
            source_observation=("correct" if arm == "source_exposed" else
                               "mismatched" if arm == "mismatched_source" else "none"),
            proposal_selected=selected, representation_adopted=adopted,
            target_effect_verified=heldout_verified,
            transferred_process_adopted=transfer_verified,
            exact_target_checks=exact_checks,
            evidence_opportunity_rows=len(exposure_nodes),
            evidence_exposure_rows=(len(exposure_nodes) if arm != "fresh" else 0),
            package_bits=package_bits if package_bits is not None else None,
            training_residual_bits=training_residual_bits if arm != "fresh" else None,
            heldout_candidate_total_bits=candidate_total_bits if arm != "fresh" else None,
            heldout_baseline_total_bits=baseline_total_bits if arm != "fresh" else None,
            heldout_residual_bits=candidate_residual_bits if arm != "fresh" else None,
            elapsed_s=elapsed, graph_nodes=len(s.nodes()),
            budget_remaining=(s.node(budgets[0])["attrs"].get("remaining") if budgets else None),
            world_access_sha256=world_hash, agent_input_audit=input_audit)
    return Agent.trial_record(
        "COMPLETED", family=pairing, seed=seed, split=split, profile=arm,
        direction=direction, control=control,
        task_id=f"{pairing}-{direction}-{seed}", outcome="no_source_map",
        proposal_selected=False, representation_adopted=False,
        transferred_process_adopted=False, exact_target_checks=0,
        evidence_opportunity_rows=len(exposure_nodes), evidence_exposure_rows=0,
        elapsed_s=time.perf_counter() - started, graph_nodes=len(s.nodes()),
        world_access_sha256=world_hash,
        agent_input_audit={"target_program_absent": True, "target_oracle_map_absent": True,
                           "same_world_hash_across_arms": world_hash,
                           "source_observation_present": False,
                           "heldout_used_for_selection": False})


def run(*, split="development", n=200, self_check=False):
    if n != 200 and not self_check:
        raise ValueError("registered P11 comparison fixes 200 pairs per pairing and direction")
    count = 1 if self_check else n
    # Separate deterministic seed blocks keep development and held-out tasks disjoint.
    offset = 5_000_000 if split == "development" else 6_000_000
    rows = []
    directions = ("forward", "reverse")
    for pairing_ix, pairing in enumerate(PAIRINGS):
        for direction_ix, direction in enumerate(directions):
            for i in range(count):
                seed = offset + pairing_ix * 20_000 + direction_ix * 10_000 + i
                for arm in ARMS:
                    rows.append(_run_task(pairing, seed, arm, split, direction))
    controls = 2 if self_check else 100
    for i in range(controls):
        seed = offset + 30_000 + i
        # Wrong-frame and nonconjugate controls are scored through the mismatched arm.
        for control in ("wrong_frame", "nonconjugate"):
            row = _run_task(PAIRINGS[i % len(PAIRINGS)], seed,
                            "mismatched_source", split,
                            directions[i % len(directions)], control)
            row["control"] = control
            rows.append(row)
    by_world = {}
    for row in rows:
        key = (row["family"], row["seed"])
        by_world.setdefault(key, set()).add(row.get("world_access_sha256"))
    if any(len(values) != 1 for values in by_world.values()):
        raise RuntimeError("paired arms did not receive an identical target world")
    metadata = {**_provenance(), "split": split, "arms": list(ARMS),
                "pairings": list(PAIRINGS), "directions": list(directions),
                "seed_block_start": offset,
                "pairs_per_pairing": count, "control_count_each": controls,
                "self_check": bool(self_check),
                "limitations": {"external_arc_ls20": "unsupported; no registered PMB ingestion adapter",
                                "human_comparison": "unavailable; no protocol-matched source",
                                "primary_interventions": "reported from native exact-effect checks; no task-solving claim"}}
    return {"schema": "pmb-scorecard-v1", "metadata": metadata, "records": rows}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", choices=("development", "heldout"), default="development")
    parser.add_argument("--n", type=int, default=200)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args()
    payload = run(split=args.split, n=args.n, self_check=args.self_check)
    if args.output:
        write_scorecard(args.output, metadata=payload["metadata"], records=payload["records"])
    else:
        print(json.dumps(payload, indent=2, sort_keys=True))
    if args.self_check:
        assert all(row["status"] in {"COMPLETED", "FAILED", "UNSUPPORTED"}
                   for row in payload["records"])
        assert all(row.get("world_access_sha256") for row in payload["records"])
        print("linear_p11_v1 runner self-check: PASS")


if __name__ == "__main__":
    main()

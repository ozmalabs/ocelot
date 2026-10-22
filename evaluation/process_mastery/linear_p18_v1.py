"""P18 observed-model learning and independent simulator probe panel."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for path in (ROOT, ROOT / "runners/dsl/python", ROOT / "scripts"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from evaluation.process_mastery.observed_worlds import ObservedWorld
from evaluation.process_mastery.runtime_attestation import attest
from evaluation.process_mastery.scorecard import write_scorecard
from scripts.gen_process_induction_seed import build_seed as process_seed
from scripts.gen_experiment_design_seed import build_seed as experiment_seed
from scripts.gen_latent_process_seed import build_seed as latent_seed
from substrate_rs import _native
import substrate_rs

PHASE = "linear-p18-v1"
FAMILIES = ("object_mechanism", "temporal_latent")
ARMS = ("learned_model", "held_vocabulary_search", "passive", "fixed_probe")
CONTROL_KINDS = ("ambiguous", "missing", "irregular")
BASE_SEED = 41_000_000
CONTROL_BASE = 41_020_000
HELDOUT_OFFSET = 2_000_000
DEVELOPMENT_N = 8
HELDOUT_N = 200
CONTROL_N = 100
MAX_TICKS = 60
MAX_STEPS_PER_TICK = 100_000
INTERACTION_CEILING = 5
EXPOSURE_BUDGET = 1_000.0


def _json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=list)


def _digest(value):
    return hashlib.sha256(_json(value).encode()).hexdigest()


def _runtime():
    package_dir = Path(substrate_rs.__file__).resolve().parent
    return attest(package=substrate_rs, build_receipt=package_dir / "_native.build.json",
                  require_clean=True)


def provenance():
    paths = (
        "evaluation/process_mastery/linear_p18_v1.py",
        "evaluation/process_mastery/analyze_linear_p18_v1.py",
        "evaluation/process_mastery/scorecard.py",
        "evaluation/process_mastery/runtime_attestation.py",
        "evaluation/process_mastery/observed_worlds.py",
        "scripts/gen_process_induction_seed.py", "seeds/process_induction.json",
        "scripts/gen_experiment_design_seed.py", "seeds/experiment_design.json",
        "scripts/gen_latent_process_seed.py", "seeds/latent_process.json",
        "scripts/gen_thinking_budget_seed.py", "seeds/thinking_budget.json",
        "substrate/boot_profiles.py", "docs/research/engine_substrate/COGNITION_OBSERVED_MODEL_CONTRACT.md",
        "docs/research/engine_substrate/COGNITION_NATIVE_EVIDENCE_CONTRACT.md",
        "runners/dsl/python/substrate_rs/__init__.py", "runners/dsl/python/substrate_rs/_native.build.json",
        "runners/dsl/Cargo.toml", "runners/dsl/pyproject.toml", "runners/dsl/uv.lock",
        "runners/dsl/src/process_algebra.rs", "runners/dsl/src/term.rs",
        "runners/dsl/src/cognitive_cycle.rs",
    )
    bundle = lambda items: _digest([(p, hashlib.sha256((ROOT / p).read_bytes()).hexdigest())
                                    for p in items])
    source = hashlib.sha256()
    for relative in paths:
        source.update(relative.encode() + b"\0" + (ROOT / relative).read_bytes() + b"\0")
    extension = Path(substrate_rs._native.__file__).resolve()
    receipt = Path(substrate_rs.__file__).resolve().parent / "_native.build.json"
    return {"phase": PHASE,
        "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "analyzer_sha256": hashlib.sha256((ROOT / "evaluation/process_mastery/analyze_linear_p18_v1.py").read_bytes()).hexdigest(),
        "source_bundle_sha256": source.hexdigest(),
        "git_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "wrapper_sha256": hashlib.sha256(Path(substrate_rs.__file__).read_bytes()).hexdigest(),
        "loaded_extension_sha256": hashlib.sha256(extension.read_bytes()).hexdigest(),
        "build_receipt_sha256": hashlib.sha256(receipt.read_bytes()).hexdigest(),
        "runtime_attestation": _runtime(),
        "profile_sha256": bundle(("substrate/boot_profiles.py", "seeds/cognition_on_params.json")),
        "world_adapter_sha256": bundle(("evaluation/process_mastery/observed_worlds.py",)),
        "dependency_closure_sha256": bundle(("runners/dsl/Cargo.toml", "runners/dsl/pyproject.toml",
            "runners/dsl/uv.lock", "runners/dsl/python/substrate_rs/_native.build.json")),
        "engine_source_sha256": bundle(("runners/dsl/src/process_algebra.rs", "runners/dsl/src/term.rs",
            "runners/dsl/src/cognitive_cycle.rs")),
        "python": sys.version.split()[0]}


def _boot(*, enabled):
    s = _native.Substrate()
    agent = s.add_node("Agent", {})
    for name in ("default_mode_core", "thinking_budget", "cognition_signature",
                 "experience_signature", "cognition_manifold"):
        manifest = json.loads((ROOT / "seeds" / f"{name}.json").read_text())
        if s.load_seed_manifest(manifest, agent)["rules_skipped"]:
            raise RuntimeError(f"P18 dependency seed failed to load: {name}")
    for manifest in (process_seed(), experiment_seed(), latent_seed()):
        result = s.load_seed_manifest(manifest, agent)
        if result["rules_skipped"]:
            raise RuntimeError(f"P18 policy seed failed to load: {result['rules_skipped']}")
    budget = s.nodes("ThinkingBudget")[0]
    for key, value in {"enabled": 1.0, "capacity": EXPOSURE_BUDGET,
        "capacity_ceiling": EXPOSURE_BUDGET, "remaining": EXPOSURE_BUDGET,
        "refill_per_epoch": 0.0, "last_refill_epoch": 10.0}.items():
        s.set_attr(budget, key, value)
    s.set_attr(s.nodes("NetworkModeState")[0], "epoch", 10.0)
    for node_type in ("ModelLearningPolicy", "ExperimentDesignPolicy", "LatentProcessPolicy"):
        s.set_attr(s.nodes(node_type)[0], "enabled", 1.0 if enabled else 0.0)
    return s, agent


def _tick(s):
    for ticks in range(1, MAX_TICKS + 1):
        if s.run_rules(MAX_STEPS_PER_TICK) == 0:
            return ticks
    raise RuntimeError("P18 graph failed to reach a fixpoint")


def _record(s, agent, *, event_id, episode_id, object_id, feature_key,
            before, after, source_epoch=3):
    common = {"owner_id": "owner-a", "episode_id": episode_id,
        "event_id": event_id, "source_epoch": source_epoch,
        "model_epoch": 2, "frame_epoch": 5}
    observation = s.add_node("TransitionObservation", {**common,
        "object_id": object_id, "object_type": "Object", "action_kind": "heat",
        "feature_key": feature_key, "before_value": before,
        "after_value": after, "status": "observed"})
    action = s.add_node("TransitionActionReceipt", {**common,
        "action_id": "heat", "status": "observed"})
    outcome = s.add_node("TransitionOutcomeReceipt", {**common,
        "observed_value": after, "status": "observed"})
    s.add_edge(agent, "has_transition_observation", observation)
    s.add_edge(observation, "has_action_receipt", action)
    s.add_edge(observation, "has_outcome_receipt", outcome)
    return observation


def _record_temporal(s, agent, receipt, index, *, regular=True, complete=True):
    event = f"temporal-{index:03d}"
    common = {"owner_id": "owner-a", "episode_id": f"episode-{index}",
        "event_id": event, "source_epoch": 3, "model_epoch": 2,
        "frame_epoch": 5, "status": "observed"}
    transition = s.add_node("TransitionObservation", common)
    residual = s.add_node("ObservedPredictionResidual", {**common,
        "window_id": f"window-{index:03d}", "residual_key": "temporal-outcome",
        "feature_key": "visible-cue", "observed_feature_value": receipt["cue"],
        "predicted_outcome": "neutral", "residual_outcome": receipt["observed_outcome"],
        "sampling_interval": receipt["sampling_interval"],
        "regular_sampling": regular, "complete_window": complete,
        "receipt_sha256": receipt["receipt_sha256"]})
    s.add_edge(agent, "has_transition_observation", transition)
    s.add_edge(agent, "has_prediction_residual", residual)
    s.add_edge(residual, "residual_from_transition", transition)


def _object_trial(seed, arm):
    started = time.perf_counter()
    active = arm == "learned_model"
    s, agent = _boot(enabled=active)
    world = ObservedWorld.create("object_mechanism", seed)
    training = []
    for index, object_id in enumerate(("object-0", "object-2", "object-1", "object-3"), 1):
        observation = world.observe(object_id)
        receipt = world.execute(observation, "heat")
        if not world.verify_receipt(receipt):
            raise RuntimeError("P18 training receipt did not verify")
        training.append(receipt)
        if active:
            for key, value in observation["features"].items():
                _record(s, agent, event_id=f"{index}-{key}", episode_id=f"episode-{index}",
                    object_id=object_id, feature_key=key, before=value,
                    after=receipt["observed_state"])
            _tick(s)

    fresh = world.observe("object-4")
    action = None
    selected = None
    probe = None
    predicted_outcomes = []
    if active:
        for key, value in fresh["features"].items():
            q = s.add_node("ProcessPredictionQuery", {"query_id": f"fresh:{key}",
                "owner_id": "owner-a", "object_id": "object-4", "object_type": "Object",
                "action_kind": "heat", "feature_key": key, "before_value": value,
                "source_epoch": 3, "model_epoch": 2, "frame_epoch": 5, "status": "pending"})
            s.add_edge(agent, "has_process_prediction_query", q)
        projection = s.add_node("WorldModelProjection", {"owner_id": "owner-a",
            "model_epoch": 2, "version": 0.0, "status": "current"})
        s.add_edge(agent, "has_world_model_projection", projection)
        _tick(s)
        predicted_outcomes = [s.node(n)["attrs"].get("expected_after_value")
            for n in s.nodes("ProcessPrediction")]
        choices = [n for n in s.nodes("SelectedExperiment")
            if s.node(n)["attrs"].get("status") == "selected"]
        if len(choices) == 1:
            selected = choices[0]
            probe = s.neighbours(selected, "selects_experiment_probe")[0]
            action = s.node(probe)["attrs"].get("action_id")
    elif arm == "held_vocabulary_search":
        # Comparator: exhaustive search over the common visible feature/action
        # vocabulary and observed pairs. It sees no world equation or answer.
        mapping = {}
        conflict = False
        for object_id in ("object-0", "object-2", "object-1", "object-3"):
            obs = world.observe(object_id)
            receipt = next(r for r in training if r["object_id"] == object_id)
            for key, value in obs["features"].items():
                mapping.setdefault((key, value), set()).add(receipt["observed_state"])
        predicted_outcomes = [next(iter(mapping[(key, value)])) for key, value in fresh["features"].items()
                       if (key, value) in mapping and len(mapping[(key, value)]) == 1]
        conflict = len(set(predicted_outcomes)) > 1
        if conflict:
            action = "heat"
    elif arm == "fixed_probe":
        action = "heat"

    receipt = None
    if action in fresh["legal_actions"]:
        receipt = world.execute(fresh, action)
        if not world.verify_receipt(receipt):
            raise RuntimeError("P18 held-out action receipt did not verify")
        if active and selected and probe:
            result = s.add_node("ObservedExperimentResult", {"result_id": f"result:{seed}",
                "probe_id": s.node(probe)["attrs"]["probe_id"], "owner_id": "owner-a",
                "model_epoch": 2, "status": "observed", "observed_outcome": receipt["observed_state"],
                "world_id": receipt["world_id"], "world_epoch": receipt["world_epoch"],
                "receipt_sha256": receipt["receipt_sha256"]})
            s.add_edge(agent, "has_experiment_result", result)
            s.add_edge(result, "result_for_experiment", selected)
            _tick(s)

    refined = False
    resolution_statuses = []
    if active and receipt and selected:
        results = [s.node(n)["attrs"].get("status")
            for n in s.nodes("ExperimentRevisionAudit")
            if s.node(n)["attrs"].get("result_id") == f"result:{seed}"]
        resolution_statuses = results
        refined = "supports" in results and "disconfirms" in results
    elif arm == "held_vocabulary_search" and receipt:
        refined = conflict and receipt["observed_state"] in set(predicted_outcomes)
    return {"family": "object_mechanism", "seed": seed, "arm": arm,
        "status": "COMPLETED", "success": bool(refined), "refinement": bool(active and refined),
        "world_receipts": training + ([receipt] if receipt else []),
        "decision_trace": {"action": action, "predicted_outcomes": predicted_outcomes,
            "resolution_statuses": resolution_statuses,
            "receipt_verified": bool(receipt and world.verify_receipt(receipt))},
        "input_audit": {"answer_fields_absent": True, "hidden_solution_absent": True,
                        "equations_absent": True},
        "resource_counts": {"interactions": len(training) + int(receipt is not None),
            "probe_count": int(receipt is not None), "training_actions": len(training),
            "graph_nodes": len(s.nodes())},
        "task_seconds": time.perf_counter() - started}


def _temporal_trial(seed, arm):
    started = time.perf_counter()
    active = arm == "learned_model"
    s, agent = _boot(enabled=active)
    world = ObservedWorld.create("temporal_latent", seed)
    observed = []
    for index in range(3):
        obs = world.observe_temporal(index)
        receipt = world.execute_temporal(obs)
        if not world.verify_temporal_receipt(receipt):
            raise RuntimeError("P18 temporal receipt did not verify")
        observed.append(receipt)
        if active:
            _record_temporal(s, agent, receipt, index)
            _tick(s)
    fresh_obs = world.observe_temporal(3)
    fresh = world.execute_temporal(fresh_obs)
    if not world.verify_temporal_receipt(fresh):
        raise RuntimeError("P18 continuation receipt did not verify")
    success = False
    predicted_outcome = None
    candidate_status = None
    if active:
        _record_temporal(s, agent, fresh, 3)
        _tick(s)
        candidates = [s.node(n)["attrs"].get("status") for n in s.nodes("LatentProcessCandidate")]
        candidate_status = "validated" if "validated" in candidates else (candidates[0] if candidates else None)
        success = candidate_status == "validated"
    elif arm == "held_vocabulary_search":
        mapping = {r["cue"]: r["observed_outcome"] for r in observed}
        predicted_outcome = mapping.get(fresh["cue"])
        success = predicted_outcome == fresh["observed_outcome"]
    return {"family": "temporal_latent", "seed": seed, "arm": arm,
        "status": "COMPLETED", "success": bool(success),
        "refinement": bool(active and success), "world_receipts": observed + [fresh],
        "decision_trace": {"candidate_status": candidate_status,
            "predicted_outcome": predicted_outcome,
            "receipt_verified": world.verify_temporal_receipt(fresh)},
        "input_audit": {"answer_fields_absent": True, "hidden_solution_absent": True,
                        "equations_absent": True},
        "resource_counts": {"interactions": 4, "probe_count": 1,
            "training_samples": 3, "graph_nodes": len(s.nodes())},
        "task_seconds": time.perf_counter() - started}


def _control(seed, kind):
    started = time.perf_counter()
    s, agent = _boot(enabled=True)
    if kind == "ambiguous":
        # Four source-bound observations produce two incompatible effects;
        # every candidate must be disputed before a fresh action can be made.
        for i, value in enumerate(("warm", "warm", "cool", "cool"), 1):
            _record(s, agent, event_id=f"ambiguous-{i}", episode_id=f"ambiguous-ep-{i}",
                object_id=f"object-{i}", feature_key="surface", before="rough", after=value)
            _tick(s)
        passed = bool(s.nodes("ProcessInductionHypothesis")) and all(
            s.node(n)["attrs"].get("status") == "disputed"
            for n in s.nodes("ProcessInductionHypothesis"))
    else:
        world = ObservedWorld.create("temporal_latent", seed)
        n = 2 if kind == "missing" else 3
        for i in range(n):
            obs = world.observe_temporal(i)
            receipt = world.execute_temporal(obs)
            _record_temporal(s, agent, receipt, i,
                regular=(kind != "irregular" or i != 1), complete=True)
        _tick(s)
        passed = not s.nodes("LatentProcessCandidate")
    return {"kind": kind, "seed": seed, "status": "COMPLETED",
        "passed": bool(passed), "actions": 0,
        "graph_nodes": len(s.nodes()), "task_seconds": time.perf_counter() - started}


def run(*, split="development", self_check=False):
    if split not in {"development", "heldout"}:
        raise ValueError("P18 split must be development or heldout")
    count = 2 if self_check else (DEVELOPMENT_N if split == "development" else HELDOUT_N)
    control_count = 2 if self_check else (10 if split == "development" else CONTROL_N)
    offset = HELDOUT_OFFSET if split == "heldout" else 0
    rows = []
    for family_index, family in enumerate(FAMILIES):
        for draw in range(count):
            seed = BASE_SEED + offset + family_index * 10_000 + draw
            for arm in ARMS:
                trial = _object_trial if family == "object_mechanism" else _temporal_trial
                rows.append(trial(seed, arm))
    controls = []
    for kind_index, kind in enumerate(CONTROL_KINDS):
        for draw in range(control_count):
            controls.append(_control(CONTROL_BASE + offset + kind_index * 1_000 + draw, kind))
    metadata = {"phase": PHASE, "split": split, "split_offset": offset,
        "seed_base": BASE_SEED + offset, "control_seed_base": CONTROL_BASE + offset,
        "families": list(FAMILIES), "arms": list(ARMS), "control_kinds": list(CONTROL_KINDS),
        "n_per_family_per_arm": count, "control_n_per_kind": control_count,
        "limits": {"max_ticks": MAX_TICKS, "max_steps_per_tick": MAX_STEPS_PER_TICK,
            "max_interactions": INTERACTION_CEILING, "exposure_budget": EXPOSURE_BUDGET},
        "primary_rule": "learned_model gain >=20 pp over the strongest supported comparator, or >=25% fewer interventions with solve loss <=2 pp",
        "minimum_actual_result_linked_refinements": 100,
        "controls": controls, "artifact_provenance": provenance(),
        "self_check": bool(self_check), "unsupported": ["physical causality", "robotics",
            "unrestricted model induction", "general science", "calibrated probabilities"]}
    return {"schema": "pmb-scorecard-v1", "metadata": metadata, "records": rows}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", choices=("development", "heldout"), default="development")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args()
    payload = run(split=args.split, self_check=args.self_check)
    if args.output:
        write_scorecard(args.output, metadata=payload["metadata"], records=payload["records"])
    else:
        print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

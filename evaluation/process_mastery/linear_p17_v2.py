"""P17 matched later-task behavior panel over acquired qualia distinctions."""
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

from evaluation.process_mastery.native_world_comparators import NativeWorldAdapter
from evaluation.process_mastery.qualia_behavior_worlds import task as make_task
from evaluation.process_mastery.runtime_attestation import attest
from evaluation.process_mastery.scorecard import write_scorecard
from substrate_rs import _native
import substrate_rs

PHASE = "linear-p17-v2"
FAMILIES = ("tool_contact", "social_request_repair")
ARMS = ("acquired", "frozen", "shuffled", "no_experience")
CONTROL_KINDS = ("orthogonal", "reversal")
BASE_SEED = 31_000_000
CONTROL_BASE = 31_020_000
DEVELOPMENT_N = 8
HELDOUT_N = 200
TRAINING_EPISODES = 5
MAX_TICKS = 50
MAX_STEPS_PER_TICK = 100_000
EXPOSURE_BUDGET = 1_000.0


def _json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=list)


def _digest(value):
    return hashlib.sha256(_json(value).encode()).hexdigest()


def _task_access(task):
    return {key: task[key] for key in ("family", "initial_state", "goal_state",
        "primitive_affordances", "legal_actions_by_state", "feature_key",
        "feature_family", "feature_value")}


def _attestation():
    package_dir = Path(substrate_rs.__file__).resolve().parent
    return attest(package=substrate_rs, build_receipt=package_dir / "_native.build.json",
                  require_clean=True)


def provenance():
    paths = (
        "evaluation/process_mastery/linear_p17_v2.py",
        "evaluation/process_mastery/analyze_linear_p17_v2.py",
        "evaluation/process_mastery/scorecard.py",
        "evaluation/process_mastery/runtime_attestation.py",
        "evaluation/process_mastery/native_world_comparators.py",
        "evaluation/process_mastery/qualia_behavior_worlds.py",
        "scripts/gen_qualia_acquisition_seed.py", "seeds/qualia_acquisition.json",
        "scripts/gen_qualia_behavior_seed.py", "seeds/qualia_behavior.json",
        "scripts/gen_experiential_significance_seed.py", "seeds/experiential_significance.json",
        "scripts/gen_qualia_revision_seed.py", "seeds/qualia_revision.json",
        "scripts/gen_experience_signature_seed.py", "seeds/experience_signature.json",
        "scripts/gen_thinking_budget_seed.py", "seeds/thinking_budget.json",
        "substrate/boot_profiles.py", "docs/research/engine_substrate/COGNITION_QUALIA_BEHAVIOR_CONTRACT.md",
        "docs/research/engine_substrate/COGNITION_NATIVE_EVIDENCE_CONTRACT.md",
        "runners/dsl/python/substrate_rs/__init__.py", "runners/dsl/python/substrate_rs/_native.build.json",
        "runners/dsl/Cargo.toml", "runners/dsl/pyproject.toml", "runners/dsl/uv.lock",
        "runners/dsl/src/process_algebra.rs", "runners/dsl/src/term.rs",
        "runners/dsl/src/cognitive_cycle.rs",
    )
    source = hashlib.sha256()
    for relative in paths:
        source.update(relative.encode() + b"\0" + (ROOT / relative).read_bytes() + b"\0")
    extension = Path(substrate_rs._native.__file__).resolve()
    receipt = Path(substrate_rs.__file__).resolve().parent / "_native.build.json"
    bundle = lambda paths: _digest([(p, hashlib.sha256((ROOT / p).read_bytes()).hexdigest())
                                    for p in paths])
    return {"phase": PHASE, "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "analyzer_sha256": hashlib.sha256((ROOT / "evaluation/process_mastery/analyze_linear_p17_v2.py").read_bytes()).hexdigest(),
        "source_bundle_sha256": source.hexdigest(),
        "git_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "wrapper_sha256": hashlib.sha256(Path(substrate_rs.__file__).read_bytes()).hexdigest(),
        "loaded_extension_sha256": hashlib.sha256(extension.read_bytes()).hexdigest(),
        "build_receipt_sha256": hashlib.sha256(receipt.read_bytes()).hexdigest(),
        "runtime_attestation": _attestation(),
        "profile_sha256": bundle(("substrate/boot_profiles.py", "seeds/cognition_on_params.json")),
        "world_adapter_sha256": bundle(("evaluation/process_mastery/native_world_comparators.py",
            "evaluation/process_mastery/qualia_behavior_worlds.py")),
        "dependency_closure_sha256": bundle(("runners/dsl/Cargo.toml", "runners/dsl/pyproject.toml",
            "runners/dsl/uv.lock", "runners/dsl/python/substrate_rs/_native.build.json")),
        "engine_source_sha256": bundle(("runners/dsl/src/process_algebra.rs", "runners/dsl/src/term.rs",
            "runners/dsl/src/cognitive_cycle.rs")),
        "python": sys.version.split()[0]}


def _boot(arm):
    s = _native.Substrate()
    ag = s.add_node("Agent", {})
    for name in ("default_mode_core", "thinking_budget", "qualia_space", "cognition_signature",
                 "experience_signature", "qualia_acquisition", "qualia_behavior",
                 "experiential_significance", "qualia_revision"):
        manifest = json.loads((ROOT / "seeds" / f"{name}.json").read_text())
        loaded = s.load_seed_manifest(manifest, ag)
        if loaded["rules_skipped"]:
            raise RuntimeError(f"P17 seed {name} failed to load: {loaded['rules_skipped']}")
    budget = s.nodes("ThinkingBudget")[0]
    for key, value in {"enabled": 1.0, "capacity": EXPOSURE_BUDGET,
        "capacity_ceiling": EXPOSURE_BUDGET, "remaining": EXPOSURE_BUDGET,
        "refill_per_epoch": 0.0, "last_refill_epoch": 10.0}.items():
        s.set_attr(budget, key, value)
    mode = s.nodes("NetworkModeState")[0]
    s.set_attr(mode, "epoch", 10.0)
    s.set_attr(s.nodes("QualiaAcquisitionPolicy")[0], "enabled",
               1.0 if arm in {"acquired", "shuffled"} else 0.0)
    for node_type in ("QualiaBehaviorPolicy", "ExperientialSignificancePolicy", "QualiaRevisionPolicy"):
        s.set_attr(s.nodes(node_type)[0], "enabled", 1.0)
    for node_type in ("ExperienceSignaturePolicy",):
        s.set_attr(s.nodes(node_type)[0], "enabled", 0.0)
    return s, ag


def _tick(s):
    for ticks in range(1, MAX_TICKS + 1):
        if s.run_rules(MAX_STEPS_PER_TICK) == 0:
            return ticks
    raise RuntimeError("P17 native graph did not reach a fixpoint")


def _episode(s, ag, *, episode_id, context, feature_key, feature_family, feature_value,
             action_id, consequence=None, goal_effect=None, source_epoch=3, model_epoch=2,
             frame_epoch=5, fresh=False):
    event_id = f"event:{episode_id}"
    feature_id = f"feature:{episode_id}"
    ep = s.add_node("ExperienceEpisode", {"owner_id": "owner-a", "episode_id": episode_id,
        "context_id": context, "status": "observed"})
    ev = s.add_node("ExperienceEvent", {"owner_id": "owner-a", "episode_id": episode_id,
        "event_id": event_id, "action_id": action_id, "frame_id": f"frame:{episode_id}",
        "event_role": "fresh_task" if fresh else "observed_episode",
        "world_epoch": 0,
        "status": "observed", "source_epoch": source_epoch,
        "model_epoch": model_epoch, "frame_epoch": frame_epoch})
    feature = s.add_node("ExperienceFeatureObservation", {"owner_id": "owner-a",
        "episode_id": episode_id, "event_id": event_id, "feature_id": feature_id,
        "feature_key": feature_key, "feature_family": feature_family,
        "feature_value": feature_value, "value_kind": "symbol", "grain": 0.0,
        "is_missing": False, "source_epoch": source_epoch, "model_epoch": model_epoch,
        "frame_epoch": frame_epoch, "status": "observed"})
    s.add_edge(ag, "has_experience_episode", ep)
    s.add_edge(ep, "has_experience_event", ev)
    s.add_edge(ev, "has_episode_feature", feature)
    receipt = None
    if consequence is not None:
        receipt = s.add_node("ExperienceOutcomeReceipt", {"owner_id": "owner-a",
            "episode_id": episode_id, "event_id": event_id, "feature_id": feature_id,
            "receipt_id": f"receipt:{episode_id}", "source_epoch": source_epoch,
            "model_epoch": model_epoch, "frame_epoch": frame_epoch,
            "status": "observed", "evidence_status": "observed",
            "consequence_kind": "world_transition", "consequence_value": consequence,
            "goal_effect": goal_effect})
        s.add_edge(feature, "has_outcome_receipt", receipt)
    return ep, ev, feature, receipt


def _opposite_value(family, value):
    if family == "tool_contact":
        return "smooth" if value == "rough" else "rough"
    return "repair-not-needed" if value == "repair-needed" else "repair-needed"


def _training_rows(family):
    if family == "tool_contact":
        return [("rough", "repair"), ("smooth", "continue"),
                ("rough", "repair"), ("smooth", "continue"), ("rough", "repair")]
    return [("repair-needed", "repair-request"), ("repair-not-needed", "normal-response"),
            ("repair-needed", "repair-request"), ("repair-not-needed", "normal-response"),
            ("repair-needed", "repair-request")]


def _train(s, ag, family, seed, *, shuffled=False, orthogonal=False):
    task = make_task(family, seed)
    rows = _training_rows(family)
    if orthogonal:
        rows = [(task["feature_value"], rows[ix][1] if ix % 2 else rows[(ix + 1) % 5][1])
                for ix in range(TRAINING_EPISODES)]
    ticks = 0
    for ix, (true_value, action) in enumerate(rows):
        feature_value = _opposite_value(family, true_value) if shuffled else true_value
        consequence = f"goal_reached:{action}"
        _episode(s, ag, episode_id=f"train:{seed}:{ix:02d}", context=f"training-context-{ix}",
            feature_key=task["feature_key"], feature_family=task["feature_family"],
            feature_value=feature_value, action_id=action, consequence=consequence,
            goal_effect=1.0)
        ticks += _tick(s)
    return ticks


def _run_trial(seed, family, arm, *, reversal=False, orthogonal=False):
    started = time.perf_counter()
    s, ag = _boot(arm)
    ticks = 0
    if arm != "no_experience" or orthogonal:
        ticks += _train(s, ag, family, seed, shuffled=(arm == "shuffled"), orthogonal=orthogonal)
    task = make_task(family, seed)
    if reversal:
        actions = sorted(task["primitive_affordances"])
        task["expected_action"] = next(a for a in actions if a != task["expected_action"])
    fresh_event_id = f"event:fresh:{seed}"
    action_context = s.add_node("QualiaActionContext", {
        "owner_id": "owner-a", "event_id": fresh_event_id, "source_epoch": 3,
        "world_id": f"p17:{family}:{seed}", "world_epoch": 0,
        "legal_actions": sorted(task["primitive_affordances"]), "status": "active"})
    s.add_edge(ag, "has_qualia_action_context", action_context)
    ep, ev, feature, _ = _episode(s, ag, episode_id=f"fresh:{seed}",
        context=task["context_id"], feature_key=task["feature_key"],
        feature_family=task["feature_family"], feature_value=task["feature_value"],
        action_id="unselected", fresh=True)
    ticks += _tick(s)
    predictions = [p for p in s.nodes("QualiaBehaviorPrediction")
                   if s.node(p)["attrs"].get("event_id") == f"event:fresh:{seed}"]
    if len(predictions) > 1:
        raise RuntimeError(f"ambiguous P17 predictions: {len(predictions)}")
    pred = predictions[0] if predictions else None
    authorizations = [a for a in s.nodes("QualiaActionAuthorization")
        if s.node(a)["attrs"].get("event_id") == fresh_event_id]
    if len(authorizations) > 1:
        raise RuntimeError(f"ambiguous P17 action authorizations: {len(authorizations)}")
    authorization = authorizations[0] if authorizations else None
    action = s.node(authorization)["attrs"].get("action_id") if authorization else None
    world = NativeWorldAdapter.from_task(task, world_id=f"p17:{family}:{seed}")
    receipt = None
    action_correct = False
    prediction_correct = False
    if action is not None:
        receipt = world.transition(world.state, action)
        if not world.verify_receipt(receipt):
            raise RuntimeError("P17 external action receipt did not verify")
        action_correct = action == task["expected_action"]
        observed = "goal_reached:" + action if tuple(receipt["observed_state"]) == tuple(world.goal) else "goal_missed:" + action
        prediction_correct = s.node(pred)["attrs"].get("predicted_consequence") == observed
        rec = s.add_node("ExperienceOutcomeReceipt", {"owner_id": "owner-a",
            "episode_id": f"fresh:{seed}", "event_id": f"event:fresh:{seed}",
            "feature_id": f"feature:fresh:{seed}", "receipt_id": f"world-receipt:{seed}",
            "source_epoch": 3, "model_epoch": 2, "frame_epoch": 5,
            "status": "observed", "evidence_status": "observed",
            "consequence_kind": "world_transition", "consequence_value": observed,
            "goal_effect": 1.0 if action_correct else -1.0})
        s.add_edge(feature, "has_outcome_receipt", rec)
        ticks += _tick(s)
    candidate = [n for n in s.nodes("QualiaAxisCandidate")
                 if s.node(n)["attrs"].get("feature_key") == task["feature_key"]]
    dimension_id = (s.node(candidate[0])["attrs"].get("dimension_id") if candidate else None)
    dimensions = [n for n in s.nodes("QualiaDimension")
                  if s.node(n)["attrs"].get("name") == dimension_id]
    input_types = ("ExperienceEpisode", "ExperienceEvent", "ExperienceFeatureObservation")
    leaked = any(any(k in s.node(n)["attrs"] for k in
        ("target_dimension", "expected_class", "answer", "hidden_action", "future_outcome"))
        for typ in input_types for n in s.nodes(typ))
    world_hash = _digest(task)
    access_hash = _digest(_task_access(task))
    split = "COMPLETED"
    return {"phase": PHASE, "family": family, "seed": seed, "profile": arm,
        "status": split, "decision_status": "proposed" if action is not None else "abstained",
        "outcome": "behavior_success" if action_correct and prediction_correct else "failure",
        "action": action, "prediction": s.node(pred)["attrs"].get("predicted_consequence") if pred else None,
        "action_correct": action_correct, "prediction_correct": prediction_correct,
        "candidate_count": len(candidate), "dimension_status": s.node(dimensions[0])["attrs"].get("acquisition_status") if dimensions else None,
        "authorization": s.node(authorization)["attrs"] if authorization else None,
        "receipt": receipt, "receipt_verified": bool(receipt and world.verify_receipt(receipt)),
        "actions": int(action is not None), "world_sha256": world_hash,
        "world_access_sha256": access_hash,
        "input_audit": {"answer_fields_absent": not leaked, "hidden_solution_absent": not leaked,
            "same_primitive_access_hash": access_hash,
            "prediction_source_bound": bool(pred and s.neighbours(pred, "uses_acquisition_witness")
                and s.neighbours(pred, "uses_qualia_dimension"))},
        "resource_counts": {"training_episodes": TRAINING_EPISODES if arm != "no_experience" else 0,
            "graph_nodes": len(s.nodes()), "ticks": ticks,
            "budget_remaining": s.node(s.nodes("ThinkingBudget")[0])["attrs"].get("remaining")},
        "task_seconds": time.perf_counter() - started,
        "truth": {"expected_action": task["expected_action"], "goal_state": task["goal_state"]}}


def _control_trial(seed, family, kind):
    if kind == "orthogonal":
        row = _run_trial(seed, family, "acquired", orthogonal=True)
        passed = row["candidate_count"] == 0 and row["actions"] == 0
    else:
        row = _run_trial(seed, family, "acquired", reversal=True)
        passed = (row["actions"] == 1 and row["receipt_verified"] is True
                  and row["dimension_status"] == "retired"
                  and row["outcome"] == "failure")
    return {"control": kind, "family": family, "seed": seed, "passed": passed,
            "actions": row["actions"], "status": row["status"],
            "dimension_status": row["dimension_status"], "receipt_verified": row["receipt_verified"]}


def run(*, split="development", self_check=False):
    if split not in {"development", "heldout"}:
        raise ValueError("P17 split must be development or heldout")
    count = 2 if self_check else (DEVELOPMENT_N if split == "development" else HELDOUT_N)
    offset = 0 if split == "development" else 2_000_000
    records = []
    for family_ix, family in enumerate(FAMILIES):
        for draw in range(count):
            seed = BASE_SEED + offset + family_ix * 10_000 + draw
            for arm in ARMS:
                records.append(_run_trial(seed, family, arm))
    controls = []
    n_controls = 2 if self_check else 100
    control_base = CONTROL_BASE + offset
    for family_ix, family in enumerate(FAMILIES):
        for kind_ix, kind in enumerate(CONTROL_KINDS):
            for draw in range(n_controls):
                seed = control_base + family_ix * 10_000 + kind_ix * 1_000 + draw
                controls.append(_control_trial(seed, family, kind))
    metadata = {"phase": PHASE, "split": split, "split_offset": offset,
        "seed_base": BASE_SEED + offset, "control_seed_base": control_base,
        "family_order": list(FAMILIES), "arms": list(ARMS),
        "n_per_family_per_arm": count, "control_kinds": list(CONTROL_KINDS),
        "control_n_per_kind_per_family": n_controls, "controls": controls,
        "limits": {"max_ticks": MAX_TICKS, "max_steps_per_tick": MAX_STEPS_PER_TICK,
            "training_episodes": TRAINING_EPISODES, "exposure_budget": EXPOSURE_BUDGET},
        "task_generation": {"action_count": 2, "input_outcome_independent": True,
            "families": list(FAMILIES)}, "artifact_provenance": provenance(),
        "self_check": bool(self_check), "unsupported": ["physical world", "open-world tool learning",
            "general qualia", "human-relative significance", "multi-step strategy quality"]}
    return {"schema": "pmb-scorecard-v1", "metadata": metadata, "records": records}


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

#!/usr/bin/env python3
"""CoW branch execution and receipt return for generated node guards."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import platform
import random
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python"), str(ROOT / "evaluation/substrate_capability")]
RUNNER = Path(__file__).resolve()
PREREG = ROOT / "docs/research/engine_substrate/THOUGHTEXPERIMENT_EDITOPS_NODE_IDENTITY_COW_V1_1_PREREG_20261003.md"
ANALYZER = ROOT / "evaluation/substrate_capability/analyze_thoughtexperiment_editops_node_identity_cow_v1_1.py"
BASE_RUNNER = ROOT / "evaluation/substrate_capability/thoughtexperiment_editops_node_identity_v1.py"
BASE_LOCK = ROOT / "evaluation/substrate_capability/thoughtexperiment_editops_node_identity_v1_1_lock_20261003.json"
BASE_ORDERS = ROOT / "evaluation/reports/thoughtexperiment_editops_node_identity_v1_1_orders_20261003.json"
BASE_SCORES = ROOT / "evaluation/reports/thoughtexperiment_editops_node_identity_v1_1_scores_20261003.json"
ACTOR_RUNNER = ROOT / "evaluation/substrate_capability/thoughtexperiment_substrate_edge_identity_current_source_v1.py"
LOCK = ROOT / "evaluation/substrate_capability/thoughtexperiment_editops_node_identity_cow_v1_1_lock_20261003.json"
ORDERS = ROOT / "evaluation/reports/thoughtexperiment_editops_node_identity_cow_v1_1_orders_20261003.json"
SCORES = ROOT / "evaluation/reports/thoughtexperiment_editops_node_identity_cow_v1_1_scores_20261003.json"
BACKENDS = ("full_copy", "shared_graph_pages")
WORKERS = 4
SEED = 20261035
TRAIN = [("actor-a", "sing", "cup"), ("actor-a", "sing", "bowl"),
         ("actor-a", "dance", "book"), ("actor-b", "sing", "cup")]
HELDOUT = [("actor-c", "sing", "cup"), ("actor-c", "sing", "bowl"),
           ("actor-c", "dance", "book"), ("actor-d", "sing", "cup")]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def digest(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    assert spec.loader
    spec.loader.exec_module(mod)
    return mod


def base_module():
    return load_module("node_identity_generator_v1", BASE_RUNNER)


def actor_module():
    return load_module("node_identity_actor_v1", ACTOR_RUNNER)


def frozen() -> dict:
    from substrate_rs import _native
    from domains.engine_provenance import rust_source_fingerprint
    base = base_module()
    return {
        "files": {str(p.relative_to(ROOT)): sha(p) for p in
            (RUNNER, PREREG, ANALYZER, BASE_RUNNER, BASE_LOCK, BASE_ORDERS,
             BASE_SCORES, ACTOR_RUNNER, ROOT / "domains/edit_ops.py",
             ROOT / "domains/contract_query.py", ROOT / "domains/seed_registry.py",
             ROOT / "seeds/actor_goals.json", ROOT / "substrate/boot_core.py",
             ROOT / "runners/dsl/python/substrate_rs/__init__.py",
             ROOT / "runners/dsl/src/substrate.rs", ROOT / "runners/dsl/src/graph.rs",
             ROOT / "runners/dsl/src/rewrite.rs", ROOT / "runners/dsl/src/cow_paged_vec.rs",
             ROOT / "runners/dsl/src/cow_sharded_map.rs")},
        "base_generator_sources": base.frozen(),
        "native_binary": {"path": str(Path(_native.__file__).resolve()), "sha256": sha(Path(_native.__file__).resolve())},
        "semantic_engine": rust_source_fingerprint(str(ROOT)),
    }


def candidates():
    return base_module().candidate_pool()[0]


def inject_and_close(branch, agent, rows):
    recipient_nodes = {}
    counts, work_steps = [], []
    seen = set()
    started = time.perf_counter_ns()
    for actor, verb, obj in rows:
        action = branch.add_node("ActorAction", {"actor": actor, "actor_role": "agent",
            "verb": verb, "object_domain": obj})
        branch.add_edge(agent, "has_actor_action", action)
        if verb not in recipient_nodes:
            recipient = branch.add_node("RecipientVerb", {"verb": verb})
            branch.add_edge(agent, "has_recipient_verb", recipient)
            recipient_nodes[verb] = recipient
        seen.add((actor, verb))
        work = int(branch._inner.run_rules(100))
        final_work = int(branch._inner.run_rules(100))
        work_steps.append([work, final_work])
        goal_rows = [branch.node(n)["attrs"] for n in branch.nodes("ActorGoal")]
        counts.append({"goal_count": len(goal_rows), "expected_count": len(seen),
            "exact_keys": sorted((str(x.get("actor")), str(x.get("verb"))) for x in goal_rows)
                == sorted(seen)})
    elapsed = time.perf_counter_ns() - started
    return {"rows": [list(x) for x in rows], "counts": counts, "work_steps": work_steps,
            "correct": all(x["goal_count"] == x["expected_count"] and x["exact_keys"] for x in counts)
                and all(x[1] == 0 for x in work_steps), "input_and_closure_ns": elapsed}


def run_branch(candidate: dict | None, rows: list, backend: str, *, return_receipt=False) -> dict:
    from domains.engine_provenance import build_is_stale
    if build_is_stale(str(ROOT)):
        raise RuntimeError("stale native engine")
    actor = actor_module()
    ctx = actor.actor_context(fault=candidate is not None)
    parent, native, agent, target = ctx["sub"], ctx["native"], ctx["agent"], ctx["target"]
    rules_before = digest(native.export_rules())
    receipt_id = parent.add_node("ThoughtExperimentProposal", {
        "proposal_status": "unselected", "target_rule": target,
        "evaluation_kind": "node_identity_hypothesis"})
    parent_graph_before = digest(parent.graph_to_dict())
    parent_revision = tuple(parent.experiment_graph_rule_revision())
    snap_started = time.perf_counter_ns()
    snapshot = parent._snapshot_with_backend(backend)
    branch = snapshot.fork()
    snapshot_ns = time.perf_counter_ns() - snap_started
    patch_started = time.perf_counter_ns()
    patched = True if candidate is None else branch.replace_active_rule_by_name(target, candidate["rule"])
    patch_ns = time.perf_counter_ns() - patch_started
    if not patched:
        raise RuntimeError("branch target rule replacement failed")
    branch_rule_digest = digest(branch._inner.export_rules())
    branch_result = inject_and_close(branch, agent, rows)
    parent_unchanged = digest(parent.graph_to_dict()) == parent_graph_before \
        and digest(native.export_rules()) == rules_before \
        and tuple(parent.experiment_graph_rule_revision()) == parent_revision
    if not parent_unchanged:
        raise RuntimeError("candidate branch modified primary state")
    receipt_return = None
    if return_receipt:
        if candidate is None or not branch_result["correct"]:
            raise RuntimeError("only a correct selected candidate can return a receipt")
        branch.begin_experiment_delta_journal()
        branch.checkpoint_experiment_delta_journal()
        branch.set_attr(receipt_id, "proposal_status", "selected_from_training")
        branch.set_attr(receipt_id, "candidate_id", candidate["proposal_id"])
        branch.set_attr(receipt_id, "candidate_label", candidate["label"])
        branch.set_attr(receipt_id, "candidate_rule_json", json.dumps(candidate["rule"], sort_keys=True))
        branch.set_attr(receipt_id, "training_exact", 1.0)
        delta_started = time.perf_counter_ns()
        delta = branch.finish_experiment_delta_journal().get("derived_only", {})
        delta_ns = time.perf_counter_ns() - delta_started
        started = time.perf_counter_ns()
        parent.apply_experiment_graph_delta(parent_revision, delta)
        adopt_ns = time.perf_counter_ns() - started
        parent_receipt = parent.node(receipt_id)["attrs"]
        branch_receipt = branch.node(receipt_id)["attrs"]
        stale_before = digest(parent.graph_to_dict())
        stale_rejected = False
        try:
            parent.apply_experiment_graph_delta(parent_revision, delta)
        except RuntimeError:
            stale_rejected = True
        stale_unchanged = digest(parent.graph_to_dict()) == stale_before
        receipt_return = {"delta": delta, "parent_receipt": parent_receipt,
            "branch_receipt": branch_receipt, "receipt_parity": parent_receipt == branch_receipt,
            "stale_retry_rejected": stale_rejected,
            "stale_retry_unchanged": stale_unchanged,
            "primary_rules_preserved": digest(native.export_rules()) == rules_before,
            "timing_ns": {"delta_extract": delta_ns, "adopt": adopt_ns}}
    return {"backend": backend, "candidate_id": None if candidate is None else candidate["proposal_id"],
        "candidate_label": "source_rule" if candidate is None else candidate["label"],
        "snapshot_ns": snapshot_ns, "rule_patch_ns": patch_ns,
        "branch_rule_digest": branch_rule_digest, "branch_result": branch_result,
        "primary_unchanged_before_return": parent_unchanged,
        "receipt_return": receipt_return}


def selector(sub, worker, descriptors, evidence, control=None):
    from domains.contract_query import select_candidate_from_graph_evidence
    branch = sub.snapshot().fork()
    proposals = [{"proposal_id": x["proposal_id"], "proposal_label": "hypothesis"} for x in descriptors]
    if control is None:
        return select_candidate_from_graph_evidence(branch, f"node_identity_cow_{worker}", proposals, evidence)
    value = "incorrect" if control == "all_wrong" else "correct"
    rows = [{"proposal_id": x["proposal_id"], "probe_id": f"{control}_{worker}",
        "predicted": value, "expected": "correct"} for x in descriptors]
    return select_candidate_from_graph_evidence(branch, f"node_identity_cow_{control}_{worker}", proposals, rows)


def order_worker(worker: int) -> dict:
    before = frozen()
    pool, generation_ns = base_module().candidate_pool()
    rng = random.Random(SEED + worker)
    permutation = list(range(len(pool)))
    rng.shuffle(permutation)
    pool = [pool[i] for i in permutation]
    descriptors = [{k: c[k] for k in ("proposal_id", "label", "site")} for c in pool]
    training = {backend: [] for backend in BACKENDS}
    backend_timings = {}
    for backend in BACKENDS:
        started = time.perf_counter_ns()
        for candidate in pool:
            training[backend].append(run_branch(candidate, TRAIN, backend))
        backend_timings[backend] = time.perf_counter_ns() - started
    evidence = [{"proposal_id": row["candidate_id"], "probe_id": f"train_{worker}",
        "predicted": "correct" if row["branch_result"]["correct"] else "incorrect",
        "expected": "correct"} for row in training["shared_graph_pages"]]
    select_ctx = actor_module().actor_context(fault=True)
    started = time.perf_counter_ns()
    decision = selector(select_ctx["sub"], worker, descriptors, evidence)
    selector_ns = time.perf_counter_ns() - started
    decision.pop("proposal_node", None)
    controls = {}
    for name in ("all_wrong", "tie"):
        ctrl = selector(select_ctx["sub"], worker, descriptors, evidence, name)
        ctrl.pop("proposal_node", None)
        controls[name] = ctrl
    selected = next((c for c in pool if c["proposal_id"] == decision.get("proposal_id")), None)
    source = {backend: run_branch(None, TRAIN, backend) for backend in BACKENDS}
    after = frozen()
    if before != after:
        raise RuntimeError("source drift during order stage")
    return {"worker": worker, "pid": os.getpid(), "candidate_order": permutation,
        "descriptors": descriptors, "candidate_rules": [c["rule"] for c in pool],
        "training": training, "source_controls": source, "evidence": evidence,
        "decision": decision, "selected_label": None if selected is None else selected["label"],
        "controls": controls, "generation_ns": generation_ns,
        "backend_training_ns": backend_timings, "selector_ns": selector_ns,
        "source_before": before, "source_after": after, "source_stable": before == after}


def score_worker(order: dict) -> dict:
    before = frozen()
    worker = int(order["worker"])
    selected_id = order["decision"].get("proposal_id")
    selected_rule = next((rule for desc, rule in zip(order["descriptors"], order["candidate_rules"])
                          if desc["proposal_id"] == selected_id), None)
    selected_desc = next((desc for desc in order["descriptors"]
                          if desc["proposal_id"] == selected_id), None)
    if selected_rule is None:
        raise RuntimeError("training selector abstained; no selected receipt to return")
    selected = {"proposal_id": selected_id, "label": selected_desc["label"], "rule": selected_rule}
    adoption = run_branch(selected, TRAIN, "shared_graph_pages", return_receipt=True)
    heldout = {backend: [] for backend in BACKENDS}
    source_controls = {}
    stage_started = time.perf_counter_ns()
    for backend in BACKENDS:
        for desc, rule in zip(order["descriptors"], order["candidate_rules"]):
            heldout[backend].append(run_branch({"proposal_id": desc["proposal_id"],
                "label": desc["label"], "rule": rule}, HELDOUT, backend))
        source_controls[backend] = run_branch(None, HELDOUT, backend)
    heldout_ns = time.perf_counter_ns() - stage_started
    after = frozen()
    if before != after:
        raise RuntimeError("source drift during held-out stage")
    return {"worker": worker, "pid": os.getpid(), "selected_id": selected_id,
        "adoption_branch": adoption, "heldout": heldout,
        "source_controls": source_controls, "heldout_stage_ns": heldout_ns,
        "source_before": before, "source_after": after, "source_stable": before == after}


def main() -> int:
    args = sys.argv[1:]
    if args == ["--lock"]:
        if any(p.exists() for p in (LOCK, ORDERS, SCORES)):
            raise SystemExit("refusing to overwrite existing artifacts")
        from domains.engine_provenance import build_is_stale
        stale = build_is_stale(str(ROOT))
        if stale:
            raise SystemExit("stale native engine: " + "; ".join(stale))
        LOCK.write_text(json.dumps({"schema": "ThoughtexperimentEditOpsNodeIdentityCowV1_1Lock",
            "sources": frozen(), "workers": WORKERS, "seed": SEED, "backends": BACKENDS,
            "training": TRAIN, "heldout": HELDOUT, "candidate_count": 8}, indent=2, sort_keys=True) + "\n")
        print(LOCK.relative_to(ROOT)); return 0
    if len(args) == 2 and args[0] == "--worker-order":
        print(json.dumps(order_worker(int(args[1])), sort_keys=True, separators=(",", ":"))); return 0
    if args == ["--worker-score"]:
        print(json.dumps(score_worker(json.load(sys.stdin)), sort_keys=True, separators=(",", ":"))); return 0
    if args == ["--orders"]:
        lock = json.loads(LOCK.read_text())
        if frozen() != lock["sources"] or ORDERS.exists() or SCORES.exists():
            raise SystemExit("source drift or order capture already exists")
        env = {**os.environ, "OZMA_NO_LLM": "1", "OZMA_SEED_PERSIST_DISABLED": "1",
            "PYTHONPATH": f"{ROOT}/runners/dsl/python:{ROOT}:{ROOT}/evaluation/substrate_capability"}
        rows = []
        for i in range(WORKERS):
            p = subprocess.run([sys.executable, str(RUNNER), "--worker-order", str(i)], cwd=ROOT,
                env=env, text=True, capture_output=True, timeout=300)
            if p.returncode: raise RuntimeError(f"order worker {i}: {p.stderr[-3000:]}")
            rows.append(json.loads(p.stdout.strip().splitlines()[-1]))
        if frozen() != lock["sources"]: raise SystemExit("source drift after orders")
        ORDERS.write_text(json.dumps({"schema": "ThoughtexperimentEditOpsNodeIdentityCowV1_1Orders",
            "lock_sha256": sha(LOCK), "captured_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "host": platform.platform(), "workers": rows}, indent=2, sort_keys=True) + "\n")
        print(ORDERS.relative_to(ROOT)); return 0
    if args == ["--scores"]:
        lock = json.loads(LOCK.read_text())
        if not ORDERS.exists() or SCORES.exists() or frozen() != lock["sources"]:
            raise SystemExit("orders missing, scores exist, or source drift")
        env = {**os.environ, "OZMA_NO_LLM": "1", "OZMA_SEED_PERSIST_DISABLED": "1",
            "PYTHONPATH": f"{ROOT}/runners/dsl/python:{ROOT}:{ROOT}/evaluation/substrate_capability"}
        rows = []
        for order in json.loads(ORDERS.read_text())["workers"]:
            p = subprocess.run([sys.executable, str(RUNNER), "--worker-score"], input=json.dumps(order),
                cwd=ROOT, env=env, text=True, capture_output=True, timeout=300)
            if p.returncode: raise RuntimeError(f"score worker {order['worker']}: {p.stderr[-3000:]}")
            rows.append(json.loads(p.stdout.strip().splitlines()[-1]))
        if frozen() != lock["sources"]: raise SystemExit("source drift after scores")
        SCORES.write_text(json.dumps({"schema": "ThoughtexperimentEditOpsNodeIdentityCowV1_1Scores",
            "lock_sha256": sha(LOCK), "orders_sha256": sha(ORDERS),
            "captured_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "workers": rows}, indent=2, sort_keys=True) + "\n")
        print(SCORES.relative_to(ROOT)); return 0
    raise SystemExit("use --lock, --orders, --scores, --worker-order N, or --worker-score")


if __name__ == "__main__":
    raise SystemExit(main())

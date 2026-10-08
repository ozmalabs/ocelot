#!/usr/bin/env python3
"""Generated node-identity guard hypotheses with blind held-out scoring."""
from __future__ import annotations

import copy
import hashlib
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
PREREG = ROOT / "docs/research/engine_substrate/THOUGHTEXPERIMENT_EDITOPS_NODE_IDENTITY_V1_1_PREREG_20261003.md"
ANALYZER = ROOT / "evaluation/substrate_capability/analyze_thoughtexperiment_editops_node_identity_v1_1.py"
ACTOR_RUNNER = ROOT / "evaluation/substrate_capability/thoughtexperiment_substrate_edge_identity_current_source_v1.py"
EDIT_OPS = ROOT / "domains/edit_ops.py"
SEED = ROOT / "seeds/actor_goals.json"
LOCK = ROOT / "evaluation/substrate_capability/thoughtexperiment_editops_node_identity_v1_1_lock_20261003.json"
ORDERS = ROOT / "evaluation/reports/thoughtexperiment_editops_node_identity_v1_1_orders_20261003.json"
SCORES = ROOT / "evaluation/reports/thoughtexperiment_editops_node_identity_v1_1_scores_20261003.json"
WORKERS = 4
BASE_SEED = 20261034
TRAIN = [("actor-a", "sing", "cup"), ("actor-a", "sing", "bowl"),
         ("actor-a", "dance", "book"), ("actor-b", "sing", "cup")]
HELDOUT = [("actor-c", "sing", "cup"), ("actor-c", "sing", "bowl"),
           ("actor-c", "dance", "book"), ("actor-d", "sing", "cup")]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def actor_module():
    import importlib.util
    name = "node_identity_actor_composer_source"
    spec = importlib.util.spec_from_file_location(name, ACTOR_RUNNER)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    assert spec.loader
    spec.loader.exec_module(module)
    return module


def frozen() -> dict:
    from substrate_rs import _native
    from domains.engine_provenance import rust_source_fingerprint
    return {
        "files": {str(path.relative_to(ROOT)): sha(path) for path in
                  (RUNNER, PREREG, ANALYZER, ACTOR_RUNNER, EDIT_OPS, SEED)},
        "native_binary": {"path": str(Path(_native.__file__).resolve()),
                          "sha256": sha(Path(_native.__file__).resolve())},
        "semantic_engine": rust_source_fingerprint(str(ROOT)),
    }


def candidate_pool() -> tuple[list[dict], int]:
    from domains.edit_ops import find_edge_identity_sites, apply_add_edge_identity_guard
    module = actor_module()
    ctx = module.actor_context(fault=True)
    source = ctx["rule"]
    started = time.perf_counter_ns()
    sites = find_edge_identity_sites(source)
    candidates = []
    for idx, site in enumerate(sites):
        keys = "+".join(site.get("identity_keys") or []) or "any"
        label = f"{site.get('scope', 'edge')}:{site['direction']}:{site['var']}:{site['edge_type']}:{keys}"
        variant = apply_add_edge_identity_guard(source, site, f"node_identity_hyp_{idx}")
        if variant is None:
            raise RuntimeError(f"edit-op rejected enumerated site {site}")
        payload = json.dumps(variant, sort_keys=True, separators=(",", ":"))
        proposal_id = "sha256:" + hashlib.sha256(payload.encode()).hexdigest()
        candidates.append({"proposal_id": proposal_id, "label": label,
                           "site": site, "rule": variant})
    elapsed = time.perf_counter_ns() - started
    identities = [json.dumps(x["rule"], sort_keys=True, separators=(",", ":")) for x in candidates]
    if len(candidates) != 8 or len(set(identities)) != len(candidates):
        raise RuntimeError(f"expected eight unique hypotheses, found {len(candidates)}")
    return candidates, elapsed


def episode(candidate: dict | None, rows: list[tuple[str, str, str]]) -> dict:
    module = actor_module()
    ctx = module.actor_context(fault=candidate is not None)
    sub, native, agent, target = ctx["sub"], ctx["native"], ctx["agent"], ctx["target"]
    if candidate is not None:
        module.install_variant(native, target, {"label": candidate["label"],
            "rules": {target: candidate["rule"]}})
    rules_before = native.export_rules()
    deltas = []
    recipient_nodes = {}
    for actor, verb, object_domain in rows:
        before = sum(1 for node in sub.nodes("ActorGoal")
                     if sub.node(node)["attrs"].get("actor") == actor
                     and sub.node(node)["attrs"].get("verb") == verb)
        action = sub.add_node("ActorAction", {"actor": actor, "actor_role": "agent",
            "verb": verb, "object_domain": object_domain})
        sub.add_edge(agent, "has_actor_action", action)
        if verb not in recipient_nodes:
            recipient_nodes[verb] = sub.add_node("RecipientVerb", {"verb": verb})
            sub.add_edge(agent, "has_recipient_verb", recipient_nodes[verb])
        native.run_rules(100)
        after = sum(1 for node in sub.nodes("ActorGoal")
                    if sub.node(node)["attrs"].get("actor") == actor
                    and sub.node(node)["attrs"].get("verb") == verb)
        deltas.append(after - before)
    fixed = int(native.run_rules(100))
    expected = [1 if (actor, verb) not in set((rows[j][0], rows[j][1]) for j in range(i)) else 0
                for i, (actor, verb, _obj) in enumerate(rows)]
    return {"actual_deltas": deltas, "expected_deltas": expected,
            "correct": deltas == expected and fixed == 0, "fixedpoint_progress": fixed,
            "rule_store_stable": native.export_rules() == rules_before,
            "rows": [list(row) for row in rows]}


def select(sub, worker: int, descriptors: list[dict], evidence: list[dict], control=None) -> dict:
    from domains.contract_query import select_candidate_from_graph_evidence
    branch = sub.snapshot().fork()
    proposals = [{"proposal_id": x["proposal_id"], "proposal_label": "hypothesis"}
                 for x in descriptors]
    if control is None:
        return select_candidate_from_graph_evidence(branch, f"node_id_select_{worker}", proposals, evidence)
    value = "incorrect" if control == "all_wrong" else "correct"
    rows = [{"proposal_id": x["proposal_id"], "probe_id": f"{control}_{worker}",
             "predicted": value, "expected": "correct"}
            for x in descriptors]
    return select_candidate_from_graph_evidence(branch, f"node_id_{control}_{worker}", proposals, rows)


def order_worker(worker: int) -> dict:
    before = frozen()
    candidates, generation_ns = candidate_pool()
    rng = random.Random(BASE_SEED + worker)
    order = list(range(len(candidates)))
    rng.shuffle(order)
    candidates = [candidates[i] for i in order]
    descriptors = [{k: c[k] for k in ("proposal_id", "label", "site")} for c in candidates]
    subctx = actor_module().actor_context(fault=True)
    evidence, training = [], []
    score_started = time.perf_counter_ns()
    for candidate in candidates:
        result = episode(candidate, TRAIN)
        training.append({"proposal_id": candidate["proposal_id"], **result})
        for probe in range(1):
            evidence.append({"proposal_id": candidate["proposal_id"],
                "probe_id": f"training_{worker}_{probe}",
                "predicted": "correct" if result["correct"] else "incorrect",
                "expected": "correct"})
    training_ns = time.perf_counter_ns() - score_started
    started = time.perf_counter_ns()
    decision = select(subctx["sub"], worker, descriptors, evidence)
    selector_ns = time.perf_counter_ns() - started
    decision.pop("proposal_node", None)
    controls = {}
    for control in ("all_wrong", "tie"):
        result = select(subctx["sub"], worker, descriptors, evidence, control)
        result.pop("proposal_node", None)
        controls[control] = result
    source = episode(None, TRAIN)
    after = frozen()
    if before != after:
        raise RuntimeError("source drift during training/selection stage")
    return {"worker": worker, "candidate_order": order, "descriptors": descriptors,
        "candidate_rules": [c["rule"] for c in candidates], "training": training,
        "training_evidence": evidence, "decision": decision, "controls": controls,
        "selected_label": next((d["label"] for d in descriptors
            if d["proposal_id"] == decision.get("proposal_id")), None),
        "training_source_control": source, "generation_ns": generation_ns,
        "training_scoring_ns": training_ns, "selector_ns": selector_ns,
        "source_before": before, "source_after": after, "source_stable": before == after}


def score_worker(order: dict) -> dict:
    before = frozen()
    rows = []
    started = time.perf_counter_ns()
    for descriptor, rule in zip(order["descriptors"], order["candidate_rules"]):
        rows.append({"proposal_id": descriptor["proposal_id"], **episode(
            {"label": descriptor["label"], "rule": rule}, HELDOUT)})
    elapsed = time.perf_counter_ns() - started
    source = episode(None, HELDOUT)
    after = frozen()
    if before != after:
        raise RuntimeError("source drift during held-out stage")
    return {"worker": order["worker"], "heldout": rows, "heldout_source_control": source,
            "heldout_scoring_ns": elapsed, "source_before": before,
            "source_after": after, "source_stable": before == after}


def main() -> int:
    args = sys.argv[1:]
    if args == ["--lock"]:
        if any(p.exists() for p in (LOCK, ORDERS, SCORES)):
            raise SystemExit("refusing to overwrite an existing artifact")
        from domains.engine_provenance import build_is_stale
        stale = build_is_stale(str(ROOT))
        if stale:
            raise SystemExit("stale native engine: " + "; ".join(stale))
        LOCK.write_text(json.dumps({"schema": "ThoughtexperimentEditOpsNodeIdentityV1_1Lock",
            "sources": frozen(), "workers": WORKERS, "seed": BASE_SEED,
            "training_rows": TRAIN, "heldout_rows": HELDOUT,
            "expected_candidate_count": 8}, indent=2, sort_keys=True) + "\n")
        print(LOCK.relative_to(ROOT)); return 0
    if len(args) == 2 and args[0] == "--worker-order":
        print(json.dumps(order_worker(int(sys.argv[2])), sort_keys=True, separators=(",", ":"))); return 0
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
                env=env, text=True, capture_output=True, timeout=180)
            if p.returncode: raise RuntimeError(f"order worker {i}: {p.stderr[-3000:]}")
            rows.append(json.loads(p.stdout.strip().splitlines()[-1]))
        if frozen() != lock["sources"]: raise SystemExit("source drift after orders")
        ORDERS.write_text(json.dumps({"schema": "ThoughtexperimentEditOpsNodeIdentityV1_1Orders",
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
            p = subprocess.run([sys.executable, str(RUNNER), "--worker-score"],
                input=json.dumps(order), cwd=ROOT, env=env, text=True, capture_output=True, timeout=180)
            if p.returncode: raise RuntimeError(f"score worker {order['worker']}: {p.stderr[-3000:]}")
            rows.append(json.loads(p.stdout.strip().splitlines()[-1]))
        if frozen() != lock["sources"]: raise SystemExit("source drift after scores")
        SCORES.write_text(json.dumps({"schema": "ThoughtexperimentEditOpsNodeIdentityV1_1Scores",
            "lock_sha256": sha(LOCK), "orders_sha256": sha(ORDERS),
            "captured_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "workers": rows},
            indent=2, sort_keys=True) + "\n")
        print(SCORES.relative_to(ROOT)); return 0
    if args == ["--run"]:
        for stage in ("--lock", "--orders", "--scores"):
            p = subprocess.run([sys.executable, str(RUNNER), stage], cwd=ROOT, text=True,
                               capture_output=True, timeout=1200)
            if p.returncode: raise SystemExit(p.stderr or p.stdout)
            print(p.stdout.strip())
        p = subprocess.run([sys.executable, str(ANALYZER)], cwd=ROOT, text=True,
                           capture_output=True, timeout=180)
        print(p.stdout)
        if p.returncode: raise SystemExit(p.stderr or "analysis failed")
        return 0
    raise SystemExit("use --lock, --orders, --scores, or --run")


if __name__ == "__main__":
    raise SystemExit(main())

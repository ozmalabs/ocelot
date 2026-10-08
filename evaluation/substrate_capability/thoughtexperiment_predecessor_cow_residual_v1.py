#!/usr/bin/env python3
"""Integrate predecessor-dependent closure with CoW branches and residual return."""
from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "runners" / "dsl" / "python")]
RUNNER = ROOT / "evaluation/substrate_capability/thoughtexperiment_predecessor_cow_residual_v1.py"
ANALYZER = ROOT / "evaluation/substrate_capability/analyze_thoughtexperiment_predecessor_cow_residual_v1.py"
LOCK = ROOT / "evaluation/substrate_capability/thoughtexperiment_predecessor_cow_residual_v1_lock_20261003.json"
OUT = ROOT / "evaluation/reports/thoughtexperiment_predecessor_cow_residual_v1_20261003.json"
SOURCES = (
    "evaluation/substrate_capability/thoughtexperiment_predecessor_cow_residual_v1.py",
    "evaluation/substrate_capability/analyze_thoughtexperiment_predecessor_cow_residual_v1.py",
    "docs/research/engine_substrate/THOUGHTEXPERIMENT_PREDECESSOR_COW_RESIDUAL_V1_PROTOCOL_20261003.md",
    "evaluation/substrate_capability/thoughtexperiment_predecessor_interface_v1.py",
    "domains/seed_registry.py", "domains/discourse_state.py",
    "seeds/communication_intent_arbitration.json",
    "substrate/boot_core.py", "substrate/world_adapter.py",
    "runners/dsl/python/substrate_rs/__init__.py",
    "runners/dsl/src/substrate.rs", "runners/dsl/src/rewrite.rs",
    "runners/dsl/src/graph.rs", "runners/dsl/src/cow_paged_vec.rs",
    "runners/dsl/src/cow_sharded_map.rs",
)
CASES = ("retained_interface", "wrong_speaker", "intervening_topic_event",
         "topicless_chain", "missing_predecessor_edge", "omitted_target_interface")
ARMS = ("monolithic_primary", "full_copy_monolithic", "shared_pages_monolithic",
        "full_copy_scoped", "shared_pages_scoped")
WORKERS = 3
CAP = 100_000
EXPECTED_EVIDENCE = "CommunicationInterpretation -> discourse-scoped DiscourseState -> prior grounded DiscourseEvent -> matching action-target head"


def sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def digest(value) -> str:
    return sha_bytes(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode())


def source_lock() -> dict:
    from substrate_rs import _native
    result = {p: sha_bytes((ROOT / p).read_bytes()) for p in SOURCES}
    result["native_extension"] = sha_bytes(Path(_native.__file__).resolve().read_bytes())
    result["native_build_manifest"] = sha_bytes((ROOT / "runners/dsl/python/substrate_rs/_native.build.json").read_bytes())
    result["cargo_lock"] = sha_bytes((ROOT / "runners/dsl/Cargo.lock").read_bytes())
    result["commit"] = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    return result


def canonical_graph_digest(graph: dict) -> str:
    value = dict(graph)
    value["nodes"] = sorted(value.get("nodes", []), key=lambda x: x.get("id", -1))
    value["edges"] = sorted(value.get("edges", []), key=lambda x: (
        x.get("src", -1), x.get("type", ""), x.get("tgt", -1),
        json.dumps(x.get("attrs", {}), sort_keys=True, separators=(",", ":"))))
    return digest(value)


def make_world(case: str, worker: int):
    from types import SimpleNamespace
    from substrate.boot_core import load_seeds_into
    from substrate.world_adapter import WorldAdapter
    from domains.discourse_state import ensure_discourse_state, record_event

    world = WorldAdapter(seeds=())
    loaded = load_seeds_into(world.s, world.agent, ["communication_intent_arbitration"])
    facade = SimpleNamespace(s=world.s, inner=world.inner, agent=world.agent)
    speaker = world.s.add_node("Interlocutor", {"name": "speaker-a"})
    other = world.s.add_node("Interlocutor", {"name": "speaker-b"})
    state = ensure_discourse_state(facade, conversation_id=f"cow-return-{case}-{worker}",
                                   addressee=world.agent)
    prior = record_event(facade, state, kind="instruction", speaker=speaker,
        addressee=world.agent, topic="calendar", interaction_mode="turn_compatible",
        payload={"grounding_status": "candidate_grounded"})
    prior_i = world.s.add_node("CommunicationInterpretation", {
        "schema": "communication_interpretation.v1", "grounding_status": "candidate_grounded",
        "language_action_target_head": "open_calendar"})
    world.inner.add_edge_unchecked(prior, "has_interpretation", prior_i, {})
    # Materialize the predecessor's indexed action-target interface before forking.
    seed_work = int(world.inner.run_rules(CAP))
    target_indexed = world.inner.has_edge(prior, "has_scoped_action_target", prior_i)

    predecessor = prior
    if case in ("intervening_topic_event", "topicless_chain"):
        middle = record_event(facade, state, kind="observation", speaker=speaker,
            addressee=world.agent, topic="weather" if case == "intervening_topic_event" else None,
            interaction_mode="non_turn", payload={})
        int(world.inner.run_rules(CAP))
        predecessor = middle
    current_speaker = other if case == "wrong_speaker" else speaker
    current = record_event(facade, state, kind="statement", speaker=current_speaker,
        addressee=world.agent, topic=None, interaction_mode="turn_compatible",
        payload={"interaction_relation": "response", "grounding_status": "unresolved"})
    if case == "missing_predecessor_edge":
        world.inner.remove_edge(current, "follows_event", predecessor)
    if case == "omitted_target_interface":
        world.inner.remove_edge(prior, "has_interpretation", prior_i)
        world.inner.remove_edge(prior, "has_scoped_action_target", prior_i)

    current_i = world.s.add_node("CommunicationInterpretation", {
        "schema": "communication_interpretation.v1", "evidence_schema": "communication_evidence.v1",
        "language_definite_nominal_reference": 1.0, "language_discourse_relation": "correction",
        "language_referential_head": "open_calendar", "interaction_relation": "response",
        "parsed_subject_pos": "noun", "grounding_status": "unresolved", "grounding_evidence_path": ""})
    world.inner.add_edge_unchecked(current, "has_interpretation", current_i, {})
    world.inner.add_edge_unchecked(world.agent, "holds_interpretation", current_i, {})
    scope = world.s.add_node("Microtheory", {"name": f"correction-frame-{case}-{worker}"})
    world.inner.add_edge_unchecked(scope, "has_concept", current, {})
    world.inner.add_edge_unchecked(scope, "has_concept", current_i, {})
    return world, scope, current, current_i, prior_i, loaded, seed_work, target_indexed


def execute(case: str, worker: int, arm: str) -> dict:
    world, scope, current, current_i, prior_i, loaded, seed_work, target_indexed = make_world(case, worker)
    primary = world.s
    before_graph = primary.graph_to_dict()
    before_digest = canonical_graph_digest(before_graph)
    before_rules = digest(world.inner.export_rules())
    revision = primary.experiment_graph_rule_revision()
    branch = None
    fork_ns = closure_ns = extract_ns = apply_ns = 0
    residual_digest = None
    residual_counts = None
    primary_unchanged_before_return = True
    merged_parity = None
    if arm == "monolithic_primary":
        started = time.perf_counter_ns()
        work = int(world.inner.run_rules(CAP))
        closure_ns = time.perf_counter_ns() - started
        final_graph = primary.graph_to_dict()
        final_rules = digest(world.inner.export_rules())
    else:
        backend = "full_copy" if arm.startswith("full_copy") else "shared_graph_pages"
        scoped = arm.endswith("_scoped")
        snapshot_start = time.perf_counter_ns()
        snapshot = primary._snapshot_with_backend(backend)
        branch = snapshot.fork()
        fork_ns = time.perf_counter_ns() - snapshot_start
        branch.begin_experiment_delta_journal()
        # Mark the fully materialized input as the baseline; derived-only
        # residuals must include mutations caused by closure below.
        branch.checkpoint_experiment_delta_journal()
        branch_inner = branch._inner
        started = time.perf_counter_ns()
        work = int(branch_inner.run_rules_scoped(CAP, False, scope)) if scoped else int(branch_inner.run_rules(CAP))
        closure_ns = time.perf_counter_ns() - started
        started = time.perf_counter_ns()
        residual = branch.finish_experiment_delta_journal()
        extract_ns = time.perf_counter_ns() - started
        derived = residual.get("derived_only", {})
        residual_digest = digest(derived)
        residual_counts = {key: len(derived.get(key, [])) for key in (
            "nodes_added", "nodes_changed", "nodes_removed", "edges_added", "edges_changed", "edges_removed")}
        primary_unchanged_before_return = (
            canonical_graph_digest(primary.graph_to_dict()) == before_digest
            and digest(world.inner.export_rules()) == before_rules
            and tuple(primary.experiment_graph_rule_revision()) == tuple(revision))
        started = time.perf_counter_ns()
        primary.apply_experiment_graph_delta(tuple(revision), derived)
        apply_ns = time.perf_counter_ns() - started
        final_graph = primary.graph_to_dict()
        final_rules = digest(world.inner.export_rules())
        merged_parity = canonical_graph_digest(final_graph) == canonical_graph_digest(branch.graph_to_dict())
    attrs = dict(primary.node(current_i)["attrs"])
    final_digest = canonical_graph_digest(final_graph)
    return {
        "case": case, "worker": worker, "arm": arm, "backend": "primary" if branch is None else backend,
        "scope_mode": "monolithic" if not arm.endswith("_scoped") else "scoped",
        "loaded_seed_ids": sorted(loaded), "seed_work_steps": seed_work,
        "target_indexed_before_current": target_indexed,
        "scope_member_count": len(primary.neighbours(scope, "has_concept")),
        "closure_work_steps": work,
        "timing_ns": {"fork": fork_ns, "closure": closure_ns,
                       "residual_extract": extract_ns, "residual_apply": apply_ns,
                       "branch_total": fork_ns + closure_ns + extract_ns + apply_ns},
        "residual_digest": residual_digest, "residual_counts": residual_counts,
        "primary_unchanged_before_return": primary_unchanged_before_return,
        "primary_revision_before_return": list(revision),
        "residual_application_revision": list(revision) if branch is not None else None,
        "residual_applied": branch is not None,
        "returned_branch_parity": merged_parity,
        "primary_rule_store_preserved": final_rules == before_rules,
        "final_graph_digest": final_digest,
        "correction_status": attrs.get("grounding_status"),
        "correction_evidence": attrs.get("grounding_evidence_path"),
        "expected_grounded": case in ("retained_interface", "topicless_chain"),
    }


def worker(index: int) -> dict:
    rows = []
    for case in CASES:
        arms = {arm: execute(case, index, arm) for arm in ARMS}
        # Find the current interpretation outcome directly; carry may apply to
        # the middle event on a topicless chain, so status is the semantic oracle.
        rows.append({"case": case, "arms": arms,
                     "all_graph_digests_equal": len({v["final_graph_digest"] for v in arms.values()}) == 1,
                     "all_grounding_equal": len({(v["correction_status"], v["correction_evidence"]) for v in arms.values()}) == 1,
                     "all_branch_returns_match": all(v["returned_branch_parity"] for k, v in arms.items() if k != "monolithic_primary"),
                     "all_isolated_before_return": all(v["primary_unchanged_before_return"] for k, v in arms.items() if k != "monolithic_primary"),
                     "all_rules_preserved": all(v["primary_rule_store_preserved"] for v in arms.values())})
    return {"worker": index, "pid": os.getpid(), "rows": rows}


def main() -> None:
    if sys.argv[1:] == ["--lock"]:
        if LOCK.exists() or OUT.exists():
            raise SystemExit("refusing to overwrite lock/capture")
        LOCK.write_text(json.dumps({"schema": "ThoughtexperimentPredecessorCowResidualLockV1",
            "locked_inputs": source_lock(), "cases": CASES, "arms": ARMS, "workers": WORKERS},
            indent=2, sort_keys=True) + "\n")
        print(LOCK.relative_to(ROOT)); return
    if len(sys.argv) == 3 and sys.argv[1] == "--worker":
        print(json.dumps(worker(int(sys.argv[2])), sort_keys=True)); return
    locked = source_lock()
    if not LOCK.exists() or json.loads(LOCK.read_text()).get("locked_inputs") != locked:
        raise SystemExit("missing or stale source lock")
    env = dict(os.environ)
    env.setdefault("OZMA_NO_LLM", "1"); env.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")
    env["PYTHONPATH"] = str(ROOT / "runners/dsl/python") + os.pathsep + str(ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    runs = []
    for index in range(WORKERS):
        proc = subprocess.run([sys.executable, str(RUNNER), "--worker", str(index)], cwd=ROOT,
            env=env, text=True, capture_output=True, timeout=300)
        if proc.returncode:
            raise SystemExit(f"worker {index} failed: {proc.stderr[-4000:]}")
        runs.append(json.loads(proc.stdout))
    post = source_lock()
    cells = [row for run in runs for row in run["rows"]]
    checks = {
        "source_stable": post == locked,
        "three_fresh_workers": len({row["pid"] for row in runs}) == WORKERS,
        "complete_case_matrix": len(cells) == len(CASES) * WORKERS and
            {row["case"] for row in cells} == set(CASES),
        "all_seed_loads_registered": all("communication_intent_arbitration" in x["loaded_seed_ids"]
            for row in cells for x in row["arms"].values()),
        "prior_target_index_built_before_branch": all(x["target_indexed_before_current"]
            for row in cells for x in row["arms"].values()),
        "exact_graph_parity_all_arms": all(row["all_graph_digests_equal"] for row in cells),
        "exact_semantic_parity_all_arms": all(row["all_grounding_equal"] for row in cells),
        "branch_return_matches_branch": all(row["all_branch_returns_match"] for row in cells),
        "primary_isolated_until_return": all(row["all_isolated_before_return"] for row in cells),
        "rule_store_preserved": all(row["all_rules_preserved"] for row in cells),
        "expected_grounding_outcomes": all(
            row["arms"]["monolithic_primary"]["correction_status"] ==
            ("candidate_grounded" if row["case"] in ("retained_interface", "topicless_chain") else "unresolved")
            for row in cells),
    }
    report = {"schema": "ThoughtexperimentPredecessorCowResidualV1",
        "claim_boundary": "Integrates source-registered predecessor-dependent communication closure, monolithic/scoped execution, full-copy/shared-graph-page experiment branches, graph-delta extraction, and revision-checked residual return on six authored discourse cases. This is not learned frame discovery, natural-task prevalence, general self-improvement, or a performance scaling law.",
        "configuration": {"cases": CASES, "arms": ARMS, "workers": WORKERS,
            "scope": "current statement DiscourseEvent plus its correction CommunicationInterpretation",
            "branching": "immutable snapshot, full-copy or shared-graph-pages backend",
            "return": "derived_only graph delta applied to unchanged primary at captured revision"},
        "environment": {"python": sys.version, "platform": platform.platform(),
            "OZMA_NO_LLM": env["OZMA_NO_LLM"], "OZMA_SEED_PERSIST_DISABLED": env["OZMA_SEED_PERSIST_DISABLED"]},
        "locked_inputs": locked, "post_run_inputs": post, "checks": checks, "runs": runs}
    if OUT.exists():
        raise SystemExit(f"refusing to overwrite {OUT}")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"capture": OUT.relative_to(ROOT).as_posix(), "checks": checks}, indent=2))
    if not all(checks.values()):
        raise SystemExit("thought-experiment CoW integration gates failed")


if __name__ == "__main__":
    main()

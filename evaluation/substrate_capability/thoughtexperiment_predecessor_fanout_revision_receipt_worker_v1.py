#!/usr/bin/env python3
"""Source-locked candidate fanout for predecessor-dependent discourse closure."""
from __future__ import annotations

import gc
import hashlib
import itertools
import json
import ctypes
import os
import platform
import resource
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "runners" / "dsl" / "python")]
RUNNER = ROOT / "evaluation/substrate_capability/thoughtexperiment_predecessor_fanout_revision_receipt_worker_v1.py"
ANALYZER = ROOT / "evaluation/substrate_capability/analyze_thoughtexperiment_revision_receipt_validation_v1.py"
PROTOCOL = ROOT / "docs/research/engine_substrate/THOUGHTEXPERIMENT_REVISION_RECEIPT_VALIDATION_V1_PREREG_20261004.md"
LOCK = ROOT / "evaluation/substrate_capability/thoughtexperiment_predecessor_fanout_revision_receipt_v1_lock_20261004.json"
OUT = ROOT / "evaluation/reports/thoughtexperiment_predecessor_fanout_revision_receipt_v1_20261004.json"
SOURCES = (
    "evaluation/substrate_capability/thoughtexperiment_predecessor_fanout_revision_receipt_worker_v1.py",
    "evaluation/substrate_capability/analyze_thoughtexperiment_revision_receipt_validation_v1.py",
    "docs/research/engine_substrate/THOUGHTEXPERIMENT_REVISION_RECEIPT_VALIDATION_V1_PREREG_20261004.md",
    "docs/research/engine_substrate/THOUGHTEXPERIMENT_REVISION_RECEIPT_VALIDATION_V1_PREREG_20261004.md",
    "domains/seed_registry.py", "domains/discourse_state.py",
    "seeds/communication_intent_arbitration.json",
    "substrate/boot_core.py", "substrate/world_adapter.py",
    "runners/dsl/python/substrate_rs/__init__.py",
    "runners/dsl/src/substrate.rs", "runners/dsl/src/rewrite.rs",
    "runners/dsl/src/graph.rs", "runners/dsl/src/cow_paged_vec.rs",
    "runners/dsl/src/cow_sharded_map.rs",
)
FRAME_COUNTS = (1, 4, 8)
TOPOLOGIES = ("chained_state", "independent_states")
FANOUTS = (1, 4, 16)
NOISE_COUNTS = (0, 10_000)
BACKENDS = ("full_copy", "shared_graph_pages")
REPLICATES = (0, 1, 2)
CAP = 100_000
EVIDENCE = "CommunicationInterpretation -> discourse-scoped DiscourseState -> prior grounded DiscourseEvent -> matching action-target head"


class MallInfo2(ctypes.Structure):
    _fields_ = [(name, ctypes.c_size_t) for name in (
        "arena", "ordblks", "smblks", "hblks", "hblkhd", "usmblks",
        "fsmblks", "uordblks", "fordblks", "keepcost")]


LIBC = ctypes.CDLL(None)
if not hasattr(LIBC, "mallinfo2"):
    raise RuntimeError("glibc mallinfo2 required for allocator in-use samples")
LIBC.mallinfo2.restype = MallInfo2


def allocator_bytes() -> dict:
    sample = LIBC.mallinfo2()
    return {"arena": int(sample.arena), "in_use": int(sample.uordblks + sample.hblkhd),
        "uordblks": int(sample.uordblks), "mmap": int(sample.hblkhd),
        "free_arena": int(sample.fordblks)}


def sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def digest(value) -> str:
    return sha_bytes(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode())


def source_lock() -> dict:
    from substrate_rs import _native
    locked = {name: sha_bytes((ROOT / name).read_bytes()) for name in SOURCES}
    locked["native_extension"] = sha_bytes(Path(_native.__file__).resolve().read_bytes())
    locked["native_build_manifest"] = sha_bytes((ROOT / "runners/dsl/python/substrate_rs/_native.build.json").read_bytes())
    locked["cargo_lock"] = sha_bytes((ROOT / "runners/dsl/Cargo.lock").read_bytes())
    locked["commit"] = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    return locked


def canonical_graph_digest(graph: dict) -> str:
    normalized = dict(graph)
    normalized["nodes"] = sorted(normalized.get("nodes", []), key=lambda row: row.get("id", -1))
    normalized["edges"] = sorted(normalized.get("edges", []), key=lambda row: (
        row.get("src", -1), row.get("type", ""), row.get("tgt", -1),
        json.dumps(row.get("attrs", {}), sort_keys=True, separators=(",", ":"))))
    return digest(normalized)


def current_rss_kib() -> int | None:
    try:
        pages = int(Path("/proc/self/statm").read_text().split()[1])
        return pages * os.sysconf("SC_PAGE_SIZE") // 1024
    except (OSError, ValueError, IndexError):
        return None


def pss_kib() -> int | None:
    try:
        for line in Path("/proc/self/smaps_rollup").read_text().splitlines():
            if line.startswith("Pss:"):
                return int(line.split()[1])
    except (OSError, ValueError, IndexError):
        pass
    return None


def peak_rss_kib() -> int:
    # Linux reports ru_maxrss in KiB; this evaluation is source/host locked.
    return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)


def build_workload(cfg: dict):
    from types import SimpleNamespace
    from substrate.boot_core import load_seeds_into
    from substrate.world_adapter import WorldAdapter
    from domains.discourse_state import ensure_discourse_state, record_event

    world = WorldAdapter(seeds=())
    loaded = load_seeds_into(world.s, world.agent, ["communication_intent_arbitration"])
    facade = SimpleNamespace(s=world.s, inner=world.inner, agent=world.agent)
    speaker = world.s.add_node("Interlocutor", {"name": "fanout-speaker"})
    states = ([ensure_discourse_state(facade,
        conversation_id=f"fanout-{cfg['topology']}-{cfg['frames']}-{cfg['replicate']}",
        addressee=world.agent)] if cfg["topology"] == "chained_state" else [
            ensure_discourse_state(facade,
                conversation_id=f"fanout-independent-{i}-{cfg['frames']}-{cfg['replicate']}",
                addressee=world.agent) for i in range(cfg["frames"])])
    scopes, current_events, current_interps = [], [], []
    target_frame = (cfg["replicate"] * 3 + (0 if cfg["topology"] == "chained_state" else 1)) % cfg["frames"]
    setup_closure_steps = 0
    for i in range(cfg["frames"]):
        state = states[0] if cfg["topology"] == "chained_state" else states[i]
        prior = record_event(facade, state, kind="instruction", speaker=speaker,
            addressee=world.agent, topic=f"task-{i}", interaction_mode="turn_compatible",
            payload={"grounding_status": "candidate_grounded"})
        prior_i = world.s.add_node("CommunicationInterpretation", {
            "schema": "communication_interpretation.v1", "grounding_status": "candidate_grounded",
            "language_action_target_head": "open_calendar"})
        world.inner.add_edge_unchecked(prior, "has_interpretation", prior_i, {})
        setup_closure_steps += int(world.inner.run_rules(CAP))
        current = record_event(facade, state, kind="statement", speaker=speaker,
            addressee=world.agent, topic=None, interaction_mode="turn_compatible",
            payload={"interaction_relation": "response", "grounding_status": "unresolved"})
        current_i = world.s.add_node("CommunicationInterpretation", {
            "schema": "communication_interpretation.v1", "evidence_schema": "communication_evidence.v1",
            "language_definite_nominal_reference": 1.0, "language_discourse_relation": "correction",
            "language_referential_head": "__candidate_slot__" if i == target_frame else "open_calendar",
            "interaction_relation": "response", "parsed_subject_pos": "noun",
            "grounding_status": "unresolved", "grounding_evidence_path": ""})
        world.inner.add_edge_unchecked(current, "has_interpretation", current_i, {})
        world.inner.add_edge_unchecked(world.agent, "holds_interpretation", current_i, {})
        scope = world.s.add_node("Microtheory", {
            "name": f"fanout-frame-{i}-{cfg['topology']}-{cfg['frames']}-{cfg['replicate']}"})
        world.inner.add_edge_unchecked(scope, "has_concept", current, {})
        world.inner.add_edge_unchecked(scope, "has_concept", current_i, {})
        scopes.append(scope); current_events.append(current); current_interps.append(current_i)
    for i in range(cfg["noise_nodes"]):
        world.s.add_node("ThoughtexperimentScaleNoise", {"noise_id": i})
    return world, scopes, current_events, current_interps, target_frame, sorted(loaded), setup_closure_steps


def candidate_heads(fanout: int, correct_position: int) -> list[str]:
    values = [f"decoy_action_{i}" for i in range(fanout)]
    values[correct_position] = "open_calendar"
    return values


def close_scoped(inner, scopes: list) -> dict:
    work = sweeps = calls = 0
    while True:
        sweeps += 1
        if sweeps > 100:
            raise RuntimeError("scoped fanout closure exceeded 100 sweeps")
        progress = False
        for scope in scopes:
            amount = int(inner.run_rules_scoped(CAP, False, scope))
            work += amount; calls += 1; progress |= amount > 0
        if not progress:
            break
    return {"work_steps": work, "sweeps": sweeps, "scope_calls": calls,
            "quiescent": True, "terminal_zero_progress_sweep": True}


def run_worker(cfg: dict) -> dict:
    world, scopes, current_events, current_interps, target_frame, loaded, setup_work = build_workload(cfg)
    primary = world.s
    target_i = current_interps[target_frame]
    base_graph_digest = canonical_graph_digest(primary.graph_to_dict())
    base_rules_digest = digest(world.inner.export_rules())
    source_revision = tuple(primary.experiment_graph_rule_revision())
    baseline_pss = pss_kib(); baseline_rss = current_rss_kib(); baseline_peak = peak_rss_kib()
    baseline_allocator = allocator_bytes()
    correct_position = (cfg["replicate"] * 5 + cfg["frames"] + (0 if cfg["topology"] == "chained_state" else 1)) % cfg["fanout"]
    heads = candidate_heads(cfg["fanout"], correct_position)
    lifecycle_start = time.perf_counter_ns()
    snapshot_start = time.perf_counter_ns()
    snapshot = primary._snapshot_with_backend(cfg["backend"])
    snapshot_ns = time.perf_counter_ns() - snapshot_start
    branches = []
    branch_fork_ns = 0
    for candidate_id, head in enumerate(heads):
        started = time.perf_counter_ns(); branch = snapshot.fork(); branch_fork_ns += time.perf_counter_ns() - started
        branch.begin_experiment_delta_journal()
        started = time.perf_counter_ns(); branch.set_attr(target_i, "language_referential_head", head)
        input_edit_ns = time.perf_counter_ns() - started
        branch.checkpoint_experiment_delta_journal()
        started = time.perf_counter_ns(); closure = close_scoped(branch._inner, scopes)
        closure_ns = time.perf_counter_ns() - started
        started = time.perf_counter_ns(); residual = branch.finish_experiment_delta_journal()
        extract_ns = time.perf_counter_ns() - started
        started = time.perf_counter_ns(); attrs = dict(branch.node(target_i)["attrs"])
        status = attrs.get("grounding_status"); evidence = attrs.get("grounding_evidence_path")
        readout_ns = time.perf_counter_ns() - started
        frame_attrs = [dict(branch.node(node)["attrs"]) for node in current_interps]
        grounded_frame_count = sum(x.get("grounding_status") == "candidate_grounded" for x in frame_attrs)
        grounded_evidence_exact = all(x.get("grounding_evidence_path") == EVIDENCE
            for x in frame_attrs if x.get("grounding_status") == "candidate_grounded")
        branches.append({"candidate_id": candidate_id, "head": head, "branch": branch,
            "residual": residual, "attrs": attrs, "status": status, "evidence": evidence,
            "grounded_frame_count": grounded_frame_count,
            "grounded_evidence_exact": grounded_evidence_exact,
            "closure": closure, "timing_ns": {"fork": 0, "input_edit": input_edit_ns,
                "closure": closure_ns, "residual_extract": extract_ns, "readout": readout_ns},
            "residual_total_counts": {k: len(residual.get("conclusions", {}).get(k, [])) for k in (
                "nodes_added", "nodes_changed", "nodes_removed", "edges_added", "edges_changed", "edges_removed")},
            "residual_derived_counts": {k: len(residual.get("derived_only", {}).get(k, [])) for k in (
                "nodes_added", "nodes_changed", "nodes_removed", "edges_added", "edges_changed", "edges_removed")}})
    retained_pss = pss_kib(); retained_rss = current_rss_kib(); retained_peak = peak_rss_kib()
    retained_allocator = allocator_bytes()
    valid = [x for x in branches if x["status"] == "candidate_grounded" and x["evidence"] == EVIDENCE]
    selection_start = time.perf_counter_ns()
    selected = valid[0] if len(valid) == 1 else None
    valid_candidate_ids = [x["candidate_id"] for x in valid]
    selected_candidate_id = selected["candidate_id"] if selected else None
    selection_ns = time.perf_counter_ns() - selection_start
    fast_validation = cfg.get("validation_mode") == "revision_receipt"
    revision_before_return = tuple(primary.experiment_graph_rule_revision())
    primary_unchanged = ((revision_before_return == source_revision) if fast_validation
        else canonical_graph_digest(primary.graph_to_dict()) == base_graph_digest) and (
        digest(world.inner.export_rules()) == base_rules_digest
        and revision_before_return == source_revision)
    selected_digest = (canonical_graph_digest(selected["branch"].graph_to_dict())
        if selected and not fast_validation else None)
    return_ns = 0; stale_rejected = False; stale_unchanged = False; stale_error = None
    if selected is not None:
        started = time.perf_counter_ns()
        primary.apply_experiment_graph_delta(source_revision, selected["residual"].get("conclusions", {}))
        return_ns += time.perf_counter_ns() - started
        returned_digest = canonical_graph_digest(primary.graph_to_dict()) if not fast_validation else None
        branch_parity = (returned_digest == selected_digest) if not fast_validation else None
        after_return_digest = returned_digest
        after_return_rules = digest(world.inner.export_rules())
        after_return_revision = tuple(primary.experiment_graph_rule_revision())
        stale_before_digest = canonical_graph_digest(primary.graph_to_dict()) if not fast_validation else None
        stale_before_rules = digest(world.inner.export_rules())
        stale_before_revision = tuple(primary.experiment_graph_rule_revision())
        try:
            primary.apply_experiment_graph_delta(source_revision, selected["residual"].get("conclusions", {}))
        except Exception as exc:
            stale_rejected = True
            stale_error = f"{type(exc).__name__}: {exc}"
        stale_unchanged = (((tuple(primary.experiment_graph_rule_revision()) == stale_before_revision)
            if fast_validation else canonical_graph_digest(primary.graph_to_dict()) == stale_before_digest)
            and digest(world.inner.export_rules()) == stale_before_rules
            and tuple(primary.experiment_graph_rule_revision()) == stale_before_revision)
    else:
        branch_parity = False; after_return_digest = None; after_return_rules = None; after_return_revision = None
    merge_pss = pss_kib(); merge_rss = current_rss_kib(); merge_peak = peak_rss_kib()
    merge_allocator = allocator_bytes()
    lifecycle_ns = time.perf_counter_ns() - lifecycle_start
    exact_post_lifecycle_audit_ns = 0
    if fast_validation and selected is not None:
        audit_start = time.perf_counter_ns()
        selected_digest = canonical_graph_digest(selected["branch"].graph_to_dict())
        returned_digest = canonical_graph_digest(primary.graph_to_dict())
        branch_parity = returned_digest == selected_digest
        exact_post_lifecycle_audit_ns = time.perf_counter_ns() - audit_start
    target_outcomes = [{"candidate_id": x["candidate_id"], "head": x["head"],
        "grounding_status": x["status"], "evidence": x["evidence"],
        "grounded_frame_count": x["grounded_frame_count"],
        "grounded_evidence_exact": x["grounded_evidence_exact"],
        "sweeps": x["closure"]["sweeps"], "scope_calls": x["closure"]["scope_calls"],
        "work_steps": x["closure"]["work_steps"], "quiescent": x["closure"]["quiescent"],
        "terminal_zero_progress_sweep": x["closure"]["terminal_zero_progress_sweep"],
        "residual_total_counts": x["residual_total_counts"],
        "residual_derived_counts": x["residual_derived_counts"], "timing_ns": x["timing_ns"]} for x in branches]
    # Drop every branch holder, including the selected candidate and loop
    # variable, before measuring post-fanout residency.
    del branches, snapshot, selected, valid, branch
    gc.collect()
    dropped_pss = pss_kib(); dropped_rss = current_rss_kib(); dropped_peak = peak_rss_kib()
    dropped_allocator = allocator_bytes()

    # Independent direct monolithic oracle over the selected, correct input.
    oracle_world, oracle_scopes, oracle_events, oracle_interps, oracle_target, _, oracle_setup = build_workload(cfg)
    oracle = oracle_world.s
    oracle_start = time.perf_counter_ns()
    oracle.set_attr(oracle_interps[oracle_target], "language_referential_head", "open_calendar")
    oracle_work = int(oracle_world.inner.run_rules(CAP))
    oracle_ns = time.perf_counter_ns() - oracle_start
    oracle_digest = canonical_graph_digest(oracle.graph_to_dict())
    oracle_attrs = [dict(oracle.node(node)["attrs"]) for node in oracle_interps]
    oracle_grounded_count = sum(x.get("grounding_status") == "candidate_grounded" for x in oracle_attrs)
    oracle_evidence_exact = all(x.get("grounding_evidence_path") == EVIDENCE
        for x in oracle_attrs if x.get("grounding_status") == "candidate_grounded")
    primary_after = canonical_graph_digest(primary.graph_to_dict())
    return {
        "configuration": cfg, "pid": os.getpid(), "loaded_seed_ids": loaded,
        "target_frame": target_frame, "correct_candidate_position": correct_position,
        "node_count": primary.node_count(), "edge_count": primary.edge_count(),
        "setup_closure_work_steps": setup_work,
        "oracle_setup_closure_work_steps": oracle_setup,
        "baseline_primary_digest": base_graph_digest, "baseline_revision": list(source_revision),
        "candidate_outcomes": target_outcomes, "valid_candidate_ids": valid_candidate_ids,
        "selected_candidate_id": selected_candidate_id,
        "oracle_grounded_frame_count": oracle_grounded_count,
        "oracle_grounded_evidence_exact": oracle_evidence_exact,
        "primary_unchanged_before_return": primary_unchanged,
        "returned_branch_matches": branch_parity,
        "all_primary_rules_preserved": after_return_rules == base_rules_digest if after_return_rules else False,
        "returned_revision": list(after_return_revision) if after_return_revision else None,
        "stale_residual_rejected": stale_rejected, "stale_retry_left_primary_unchanged": stale_unchanged,
        "stale_error": stale_error,
        "primary_matches_monolithic_oracle": primary_after == oracle_digest,
        "selected_branch_matches_monolithic_oracle": selected_digest == oracle_digest if selected_digest else False,
        "monolithic_oracle_work_steps": oracle_work, "monolithic_oracle_ns": oracle_ns,
        "lifecycle_wall_ns": lifecycle_ns,
        "validation_mode": cfg.get("validation_mode", "full_digest"),
        "exact_post_lifecycle_audit_ns": exact_post_lifecycle_audit_ns,
        "phase_ns": {"snapshot_create": snapshot_ns, "candidate_forks_total": branch_fork_ns,
            "candidate_input_edit_total": sum(x["timing_ns"]["input_edit"] for x in target_outcomes),
            "candidate_closure_total": sum(x["timing_ns"]["closure"] for x in target_outcomes),
            "candidate_residual_extract_total": sum(x["timing_ns"]["residual_extract"] for x in target_outcomes),
            "candidate_readout_total": sum(x["timing_ns"]["readout"] for x in target_outcomes),
            "selection": selection_ns, "selected_return": return_ns},
        "memory_kib": {"baseline_pss": baseline_pss, "retained_fanout_pss": retained_pss,
            "after_return_pss": merge_pss, "after_drop_pss": dropped_pss,
            "baseline_rss": baseline_rss, "retained_fanout_rss": retained_rss,
            "after_return_rss": merge_rss, "after_drop_rss": dropped_rss,
            "peak_rss_before_fanout": baseline_peak, "peak_rss_retained": retained_peak,
            "peak_rss_after_return": merge_peak, "peak_rss_after_drop": dropped_peak},
        "allocator_bytes": {"baseline": baseline_allocator, "retained_fanout": retained_allocator,
            "after_return": merge_allocator, "after_drop": dropped_allocator},
    }


CONFIGS = [dict(frames=n, topology=t, fanout=k, noise_nodes=noise, backend=b, replicate=r)
    for n, t, k, noise, b, r in itertools.product(
        FRAME_COUNTS, TOPOLOGIES, FANOUTS, NOISE_COUNTS, BACKENDS, REPLICATES)]


def main() -> None:
    if sys.argv[1:] == ["--lock"]:
        if LOCK.exists() or OUT.exists():
            raise SystemExit("refusing to overwrite lock/capture")
        LOCK.write_text(json.dumps({"schema": "ThoughtexperimentPredecessorFanoutLockV1_1",
            "locked_inputs": source_lock(), "configuration_count": len(CONFIGS),
            "factors": {"frames": FRAME_COUNTS, "topologies": TOPOLOGIES, "fanouts": FANOUTS,
                "noise_nodes": NOISE_COUNTS, "backends": BACKENDS, "replicates": REPLICATES}},
            indent=2, sort_keys=True) + "\n")
        print(LOCK.relative_to(ROOT)); return
    if len(sys.argv) == 3 and sys.argv[1] == "--worker":
        print(json.dumps(run_worker(CONFIGS[int(sys.argv[2])]), sort_keys=True)); return
    locked = source_lock()
    if not LOCK.exists() or json.loads(LOCK.read_text()).get("locked_inputs") != locked:
        raise SystemExit("missing or stale source lock")
    env = dict(os.environ)
    env.setdefault("OZMA_NO_LLM", "1"); env.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")
    env["PYTHONPATH"] = str(ROOT / "runners/dsl/python") + os.pathsep + str(ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    rows = []
    for index in range(len(CONFIGS)):
        proc = subprocess.run([sys.executable, str(RUNNER), "--worker", str(index)], cwd=ROOT,
            env=env, text=True, capture_output=True, timeout=600)
        if proc.returncode:
            raise SystemExit(f"worker {index} {CONFIGS[index]} failed: {proc.stderr[-4000:]}")
        rows.append(json.loads(proc.stdout))
        if index % 24 == 23:
            print(f"completed {index + 1}/{len(CONFIGS)} workers", flush=True)
    post = source_lock()
    checks = {
        "source_stable": post == locked,
        "complete_216_worker_matrix": len(rows) == 216 and len({x["pid"] for x in rows}) == 216,
        "all_registered_seed_loads": all("communication_intent_arbitration" in x["loaded_seed_ids"] for x in rows),
        "one_correct_candidate_each": all(len(x["valid_candidate_ids"]) == 1 and
            x["selected_candidate_id"] == x["correct_candidate_position"] for x in rows),
        "decoys_fail_target_grounding": all(sum(v["grounding_status"] == "unresolved" for v in x["candidate_outcomes"]) == x["configuration"]["fanout"] - 1 for x in rows),
        "candidate_frames_match_semantic_oracle": all(all(
            v["grounded_frame_count"] == x["configuration"]["frames"] -
                (0 if v["candidate_id"] == x["correct_candidate_position"] else 1)
            and v["grounded_evidence_exact"] for v in x["candidate_outcomes"])
            and x["oracle_grounded_frame_count"] == x["configuration"]["frames"]
            and x["oracle_grounded_evidence_exact"] for x in rows),
        "all_scopes_reach_quiescence": all(all(v["quiescent"] and v["terminal_zero_progress_sweep"] for v in x["candidate_outcomes"]) for x in rows),
        "primary_isolated_until_selected_return": all(x["primary_unchanged_before_return"] for x in rows),
        "selected_return_matches_branch": all(x["returned_branch_matches"] for x in rows),
        "primary_rule_store_preserved": all(x["all_primary_rules_preserved"] for x in rows),
        "stale_residual_rejected_atomically": all(x["stale_residual_rejected"] and x["stale_retry_left_primary_unchanged"] for x in rows),
        "selected_branch_matches_monolithic": all(x["selected_branch_matches_monolithic_oracle"] and x["primary_matches_monolithic_oracle"] for x in rows),
    }
    report = {"schema": "ThoughtexperimentPredecessorFanoutV1_1",
        "claim_boundary": "Tests substrate-outcome-guided selection over an evaluator-authored head candidate set, with retained candidate fanout, predecessor-dependent scoped closure, shared/full-copy branches, residual return, and stale-revision rejection across authored frame topologies and host-node sizes. Candidate generation, natural prevalence, learned frame discovery, and general self-improvement remain outside scope.",
        "environment": {"python": sys.version, "platform": platform.platform(),
            "logical_cpu_count": os.cpu_count(), "OZMA_NO_LLM": env["OZMA_NO_LLM"],
            "OZMA_SEED_PERSIST_DISABLED": env["OZMA_SEED_PERSIST_DISABLED"]},
        "locked_inputs": locked, "post_run_inputs": post, "checks": checks, "runs": rows}
    if OUT.exists():
        raise SystemExit(f"refusing to overwrite {OUT}")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"capture": OUT.relative_to(ROOT).as_posix(), "checks": checks}, indent=2))
    if not all(checks.values()):
        raise SystemExit("predecessor candidate fanout gates failed")


if __name__ == "__main__":
    main()

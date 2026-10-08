#!/usr/bin/env python3
"""Locked Bigville replay with mutation-derived native owner notifications."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import random
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_BIGVILLE_NATIVE_OWNER_NOTIFICATION_PREREG_20260925.md"
AMENDMENT = ROOT / "docs/research/engine_substrate/SUBSTRATE_BIGVILLE_NATIVE_OWNER_NOTIFICATION_V1_1_AMENDMENT_20260925.md"
LOCK = ROOT / "evaluation/substrate_capability/bigville_native_owner_notification_lock_20260925.json"
OUT = ROOT / "evaluation/reports/substrate_bigville_native_owner_notification_20260925.json"
BASE_RUNNER = ROOT / "scripts/substrate_bigville_can_runtime_partition_replay_v3_1.py"
DYNAMIC_RUNNER = ROOT / "scripts/substrate_bigville_runtime_partition_dynamic_links.py"
CAST = ROOT / "seeds/bigville_cast100.json"
SEED = ROOT / "seeds/can_native_reimplementation.json"
BUILDER = ROOT / "worlds/bigville_can_beliefs.py"
TOPOLOGIES = ("ring", "star", "random_connected")
POLICIES = ("full", "event", "omit_evidence_notification")
REPS = 3


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def engine_source_fingerprint() -> str:
    env = dict(os.environ)
    env["PYTHONPATH"] = f"{ROOT}:{ROOT / 'runners/dsl/python'}:{env.get('PYTHONPATH', '')}"
    return subprocess.check_output(
        [sys.executable, "-c", "from domains.engine_provenance import rust_source_fingerprint; print(rust_source_fingerprint('.'))"],
        cwd=ROOT,
        env=env,
        text=True,
    ).strip()


def locked_inputs() -> dict:
    return {
        "protocol_sha256": sha(PROTOCOL),
        "amendment_sha256": sha(AMENDMENT),
        "runner_sha256": sha(Path(__file__)),
        "base_runner_sha256": sha(BASE_RUNNER),
        "dynamic_runner_sha256": sha(DYNAMIC_RUNNER),
        "cast_sha256": sha(CAST),
        "seed_sha256": sha(SEED),
        "builder_sha256": sha(BUILDER),
        "graph_sha256": sha(ROOT / "runners/dsl/src/graph.rs"),
        "substrate_sha256": sha(ROOT / "runners/dsl/src/substrate.rs"),
        "py_binding_sha256": sha(ROOT / "runners/dsl/src/py.rs"),
        "native_sha256": sha(ROOT / "runners/dsl/python/substrate_rs/_native.abi3.so"),
        "rust_source_fingerprint": engine_source_fingerprint(),
    }


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def install_native_event_settler(dynamic, base) -> None:
    from collections import deque

    def settle_event_native(inner, mts, frame_nodes, node_frame, edges, ref_by_id, seed_frames, audit=False):
        mt_to_frame = {base.nid(mt): i for i, mt in enumerate(mts)}
        queue = deque(sorted(set(seed_frames)))
        queued = set(queue)
        steps = turns = enqueues = changed_frames = 0
        notified_mts = set()
        total_counts = base.empty_counts()
        deferred_pending = False
        cap_hit = False
        while queue and turns < dynamic.CAP and steps < dynamic.CAP:
            frame = queue.popleft()
            queued.remove(frame)
            before = [float(inner.node(ref_by_id[node])["attrs"].get("state", 0.0)) for node in frame_nodes[frame]]
            if audit:
                inner.scale_audit_reset()
                inner.scale_audit_set_enabled(True)
            report = inner.run_rules_scoped_delta_report(
                mts[frame], dynamic.CAP - steps, False
            )
            if audit:
                base.add_counts(total_counts, base.snap(inner))
                inner.scale_audit_set_enabled(False)
            steps += int(report["progress_steps"])
            turns += 1
            if report["hit_progress_budget"]:
                cap_hit = True
            if report["deferred_effects_pending"]:
                deferred_pending = True
            after = [float(inner.node(ref_by_id[node])["attrs"].get("state", 0.0)) for node in frame_nodes[frame]]
            if before != after:
                changed_frames += 1
            if report["progress_steps"] > 0:
                for mt_id in report["affected_microtheories"]:
                    mt_id = int(mt_id)
                    notified_mts.add(mt_id)
                    if mt_id not in mt_to_frame:
                        raise RuntimeError(f"native notification has no runtime frame: Mt #{mt_id}")
                    target_frame = mt_to_frame[mt_id]
                    if target_frame not in queued:
                        queue.append(target_frame)
                        queued.add(target_frame)
                        enqueues += 1
            if deferred_pending or cap_hit:
                break
        return {
            "steps": steps,
            "turns": turns,
            "enqueues": enqueues,
            "changed_frames": changed_frames,
            "complete": not queue and steps < dynamic.CAP and not deferred_pending and not cap_hit,
            "audit": total_counts,
            "notified_microtheories": sorted(notified_mts),
            "deferred_effects_pending": deferred_pending,
            "hit_progress_budget": cap_hit,
        }

    base.settle_event = settle_event_native

    original_load = dynamic.load_base

    def load_patched_base():
        base_module = original_load()
        base_module.settle_event = settle_event_native
        return base_module

    dynamic.load_base = load_patched_base


def worker(topology: str, replicate: int, policy: str) -> dict:
    dynamic = load_module("bigville_dynamic_for_native_owner", DYNAMIC_RUNNER)
    base = dynamic.load_base()
    install_native_event_settler(dynamic, base)
    return dynamic.worker(topology, replicate, policy)


def analyze(runs: list[dict]) -> tuple[dict, list[dict]]:
    ix = {(row["topology"], row["replicate"], row["policy"]): row for row in runs}
    pairs = []
    for topology in TOPOLOGIES:
        for replicate in range(REPS):
            full, event, omit = (
                ix[(topology, replicate, policy)] for policy in POLICIES
            )
            full_cp, event_cp, omit_cp = (
                row["checkpoints"] for row in (full, event, omit)
            )
            exact = all(
                a["states"] == b["states"] and a["fields"] == b["fields"]
                for a, b in zip(full_cp, event_cp)
            )
            all_residuals_zero = all(
                cp["residual_count"] == 0 for cp in full_cp + event_cp
            )
            omission_detected = omit_cp[2]["residual_count"] > 0
            native_complete = all(
                cp["settlement"]["complete"]
                and not cp["settlement"].get("deferred_effects_pending", False)
                and not cp["settlement"].get("hit_progress_budget", False)
                for cp in event_cp
            )
            pair = {
                "topology": topology,
                "replicate": replicate,
                "event_full_state_equal": exact,
                "full_event_residuals_zero": all_residuals_zero,
                "native_event_complete": native_complete,
                "omission_detected_after_evidence": omission_detected,
                "event_turns": sum(cp["settlement"]["turns"] for cp in event_cp),
                "full_turns": sum(cp["settlement"]["turns"] for cp in full_cp),
                "event_notifications": sum(
                    len(cp["settlement"].get("notified_microtheories", [])) for cp in event_cp
                ),
            }
            pairs.append(pair)
    checks = {
        "worker_count_27": len(runs) == 27,
        "runtime_derived_100_five_concept_frames": all(
            row["runtime_component_count"] == 100
            and set(row["runtime_component_sizes"]) == {5}
            for row in runs
        ),
        "native_event_fixed_point_all_checkpoints": all(p["native_event_complete"] for p in pairs),
        "full_and_event_zero_residual": all(p["full_event_residuals_zero"] for p in pairs),
        "full_and_event_exact_state_equal": all(p["event_full_state_equal"] for p in pairs),
        "omission_controls_detect_stale_evidence": all(p["omission_detected_after_evidence"] for p in pairs),
        "pair_matrix_complete": len(pairs) == 9,
    }
    return checks, pairs


def main() -> None:
    if len(sys.argv) == 5 and sys.argv[1] == "--worker":
        print(json.dumps(worker(sys.argv[2], int(sys.argv[3]), sys.argv[4]), sort_keys=True))
        return
    current = locked_inputs()
    if sys.argv[1:] == ["--lock"]:
        print(json.dumps({"locked_inputs": current}, indent=2, sort_keys=True))
        return
    if not LOCK.exists() or json.loads(LOCK.read_text()).get("locked_inputs") != current:
        raise SystemExit("missing lock or locked inputs changed")
    env = dict(os.environ)
    env["PYTHONPATH"] = f"{ROOT}:{ROOT / 'runners/dsl/python'}:{env.get('PYTHONPATH', '')}"
    stale = subprocess.check_output(
        [sys.executable, "-c", "from domains.engine_provenance import build_is_stale; print('\\n'.join(build_is_stale('.')) )"],
        cwd=ROOT,
        env=env,
        text=True,
    ).strip()
    if stale:
        raise SystemExit(f"native build stale:\n{stale}")
    jobs = [(t, r, p) for t in TOPOLOGIES for r in range(REPS) for p in POLICIES]
    random.Random(20260926).shuffle(jobs)
    runs = []
    for topology, replicate, policy in jobs:
        proc = subprocess.run(
            [sys.executable, str(Path(__file__).resolve()), "--worker", topology, str(replicate), policy],
            cwd=ROOT,
            env=env,
            text=True,
            capture_output=True,
            check=True,
        )
        row = json.loads(proc.stdout)
        runs.append(row)
        print(f"{topology} rep={replicate} policy={policy} checkpoints={len(row['checkpoints'])}", flush=True)
    checks, pairs = analyze(runs)
    report = {
        "schema_version": 1,
        "run_id": "bigville-native-owner-notification-20260925-v1",
        "claim_boundary": "native scoped Microtheory owner IDs drive an event queue on the authored Bigville replay; frames and host mutation seeds are runtime/caller derived",
        "locked_inputs": current,
        "lock_sha256": sha(LOCK),
        "checks": checks,
        "comparisons": pairs,
        "runs": runs,
    }
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(OUT.relative_to(ROOT)), "checks": checks}, indent=2))
    if not all(checks.values()):
        raise SystemExit("native owner-notification semantic gate failed; raw report preserved")


if __name__ == "__main__":
    main()

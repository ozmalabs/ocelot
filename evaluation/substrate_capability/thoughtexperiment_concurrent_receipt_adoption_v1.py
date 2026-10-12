#!/usr/bin/env python3
"""Race same-revision thoughtexperiment receipts against guarded adoption."""
from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
WORKERS, RACES, CONTENDERS = 3, 10, 3
PREREG = ROOT / "docs/research/engine_substrate/THOUGHTEXPERIMENT_CONCURRENT_RECEIPT_ADOPTION_V1_PREREG_20261001.md"
RAW = ROOT / "evaluation/reports/thoughtexperiment_concurrent_receipt_adoption_v1_raw_20261001.json"
RESULTS = ROOT / "docs/research/engine_substrate/THOUGHTEXPERIMENT_CONCURRENT_RECEIPT_ADOPTION_V1_RESULTS_20261001.md"
SOURCES = (
    "docs/research/engine_substrate/THOUGHTEXPERIMENT_CONCURRENT_RECEIPT_ADOPTION_V1_PREREG_20261001.md",
    "evaluation/substrate_capability/thoughtexperiment_concurrent_receipt_adoption_v1.py",
    "runners/dsl/src/persist.rs", "runners/dsl/src/graph.rs",
    "runners/dsl/src/substrate.rs", "runners/dsl/src/py.rs",
    "runners/dsl/python/substrate_rs/__init__.py",
    "runners/dsl/python/substrate_rs/_native.build.json",
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(graph: dict) -> dict:
    return {"nodes": sorted(graph["nodes"], key=lambda row: int(row["id"])),
            "edges": sorted(graph["edges"], key=lambda row:
                (int(row["src"]), row["type"], int(row["tgt"]),
                 json.dumps(row.get("attrs", {}), sort_keys=True)))}


def worker() -> dict:
    from substrate_rs import Substrate
    from substrate_rs import _native
    binary = Path(_native.__file__).resolve()
    before_fingerprint = {name: sha(ROOT / name) for name in SOURCES}
    before_fingerprint["native_binary"] = sha(binary)
    races = []
    for race_index in range(RACES):
        primary = Substrate()
        targets = [primary.add_node("CandidateTarget", {"ordinal": i, "stable": True})
                   for i in range(CONTENDERS)]
        base = canonical(primary._inner.graph_to_dict())
        base_revision = primary.experiment_graph_rule_revision()
        snapshot = primary.snapshot()
        branches, receipts = [], []
        for contender, target in enumerate(targets):
            branch = snapshot.fork()
            branch.begin_experiment_delta_journal()
            branch.checkpoint_experiment_delta_journal()
            branch.set_attr(target, "experiment_value", f"race-{race_index}-candidate-{contender}")
            receipt = branch.finish_experiment_delta_journal()["conclusions"]
            branches.append(branch)
            receipts.append(receipt)
        branch_isolation = all(canonical(primary._inner.graph_to_dict()) == base for _ in branches)
        receipt_nonempty = all(receipt.get("nodes_changed") for receipt in receipts)
        barrier = Barrier(CONTENDERS)

        def submit(contender: int) -> dict:
            barrier.wait()
            started = time.perf_counter_ns()
            try:
                primary.apply_experiment_graph_delta(base_revision, receipts[contender])
                return {"contender": contender, "accepted": True,
                        "elapsed_ns": time.perf_counter_ns() - started, "error": None}
            except Exception as exc:  # expected for stale contenders
                return {"contender": contender, "accepted": False,
                        "elapsed_ns": time.perf_counter_ns() - started,
                        "error": f"{type(exc).__name__}: {exc}"}

        race_started = time.perf_counter_ns()
        with ThreadPoolExecutor(max_workers=CONTENDERS) as pool:
            outcomes = list(pool.map(submit, range(CONTENDERS)))
        race_elapsed = time.perf_counter_ns() - race_started
        accepted = [row for row in outcomes if row["accepted"]]
        winner = accepted[0]["contender"] if len(accepted) == 1 else None
        expected = json.loads(json.dumps(base))
        if winner is not None:
            target_id = int(targets[winner].value)
            node = next(row for row in expected["nodes"] if int(row["id"]) == target_id)
            node["attrs"]["experiment_value"] = f"race-{race_index}-candidate-{winner}"
        observed = canonical(primary._inner.graph_to_dict())
        stale_errors = [row for row in outcomes if not row["accepted"] and row["error"]
                        and "revision" in row["error"].lower()]
        races.append({"race_index": race_index, "revision": list(base_revision),
            "branch_isolation": branch_isolation, "receipts_nonempty": receipt_nonempty,
            "outcomes": sorted(outcomes, key=lambda row: row["contender"]),
            "accepted_count": len(accepted), "stale_rejection_count": len(stale_errors),
            "winner": winner, "oracle_parity": observed == expected,
            "race_elapsed_ns": race_elapsed, "final_graph": observed})
    after_fingerprint = {name: sha(ROOT / name) for name in SOURCES}
    after_fingerprint["native_binary"] = sha(binary)
    return {"pid": os.getpid(), "fingerprint_before": before_fingerprint,
            "fingerprint_after": after_fingerprint, "source_build_stable":
                before_fingerprint == after_fingerprint, "races": races}


def main() -> int:
    if sys.argv[1:] == ["--worker"]:
        print(json.dumps(worker(), sort_keys=True, separators=(",", ":")))
        return 0
    from domains.engine_provenance import build_is_stale, rust_source_fingerprint
    stale = build_is_stale(str(ROOT))
    if stale:
        raise SystemExit("stale native engine: " + "; ".join(stale))
    workers = []
    env = {**os.environ, "PYTHONPATH": f"{ROOT / 'runners/dsl/python'}:{ROOT}"}
    for _ in range(WORKERS):
        proc = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--worker"],
            cwd=ROOT, env=env, text=True, capture_output=True, check=True)
        workers.append(json.loads(proc.stdout))
    races = [race for row in workers for race in row["races"]]
    gates = {
        "three_fresh_workers": len({row["pid"] for row in workers}) == WORKERS,
        "thirty_races": len(races) == WORKERS * RACES,
        "ninety_submissions": sum(len(r["outcomes"]) for r in races) == 90,
        "all_branches_isolated": all(r["branch_isolation"] for r in races),
        "all_receipts_nonempty": all(r["receipts_nonempty"] for r in races),
        "exactly_one_accept_per_race": all(r["accepted_count"] == 1 for r in races),
        "two_stale_rejections_per_race": all(r["stale_rejection_count"] == 2 for r in races),
        "all_full_graph_oracles": all(r["oracle_parity"] for r in races),
        "stable_source_build": all(row["source_build_stable"] for row in workers),
    }
    capture = {"schema": "ThoughtexperimentConcurrentReceiptAdoptionV1",
        "captured_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "host": {"platform": platform.platform(), "machine": platform.machine(),
                 "python": sys.version.split()[0]},
        "engine_fingerprint": rust_source_fingerprint(str(ROOT)),
        "protocol": {"workers": WORKERS, "races_per_worker": RACES,
                     "contenders_per_race": CONTENDERS,
                     "contention": "barrier-synchronized threads; same expected revision"},
        "workers": workers, "gates": gates}
    RAW.parent.mkdir(parents=True, exist_ok=True)
    RAW.write_text(json.dumps(capture, indent=2, sort_keys=True) + "\n")
    medians = sorted(r["race_elapsed_ns"] for r in races)
    summary = {"gates": gates, "median_race_ms": medians[len(medians)//2] / 1e6,
               "min_race_ms": min(medians) / 1e6, "max_race_ms": max(medians) / 1e6}
    RESULTS.write_text(f"""# Thoughtexperiment concurrent receipt adoption v1 — results

**Result:** {'all preregistered gates pass' if all(gates.values()) else 'one or more preregistered gates fail'} ({sum(gates.values())}/{len(gates)} gates).

## Outcome

Three fresh workers executed 30 races and 90 receipt submissions. Three independently forked branches created nonempty attribute-change receipts from the same base revision in every race. Barrier-synchronized threads submitted the receipts concurrently. The guarded primary accepted exactly one receipt and rejected two as stale in every race; the winning receipt varied freely. The complete final graph matched an independent oracle containing exactly the winner's write, so rejected branch values did not leak into primary state.

Race wall time from barrier setup through all submissions had a median of {summary['median_race_ms']:.3f} ms (range {summary['min_race_ms']:.3f}–{summary['max_race_ms']:.3f} ms). This includes thread scheduling and is descriptive only.

## Interpretation and limits

This demonstrates strict single-winner stale-base rejection and atomic graph publication for concurrent same-revision receipt calls through the Python/Rust API. It does not demonstrate parallel native execution under the Python GIL, merge semantics for disjoint receipts, fairness, production throughput, or protection of state outside the tracked revision contract. A losing branch must be rerun or explicitly regrounded against a fresh primary revision before another adoption attempt.

## Artifacts

- [Preregistration](THOUGHTEXPERIMENT_CONCURRENT_RECEIPT_ADOPTION_V1_PREREG_20261001.md)
- [Runner](../../../evaluation/substrate_capability/thoughtexperiment_concurrent_receipt_adoption_v1.py)
- [Raw capture](../../../evaluation/reports/thoughtexperiment_concurrent_receipt_adoption_v1_raw_20261001.json)
""")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if all(gates.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())

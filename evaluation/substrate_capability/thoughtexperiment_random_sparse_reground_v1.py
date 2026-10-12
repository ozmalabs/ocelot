#!/usr/bin/env python3
"""Seeded sparse-graph conflict oracle for thoughtexperiment regrounding."""
from __future__ import annotations

import hashlib, json, os, platform, random, statistics, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
SIZES, SEEDS = (1000, 10000, 50000), (4101, 4102)
TARGETS = 50
SOURCES = (
    "evaluation/substrate_capability/thoughtexperiment_random_sparse_reground_v1.py",
    "docs/research/engine_substrate/THOUGHTEXPERIMENT_RANDOM_SPARSE_REGROUND_V1_PREREG_20261001.md",
    "domains/imagination.py", "runners/dsl/src/py.rs", "runners/dsl/src/graph.rs",
    "runners/dsl/python/substrate_rs/__init__.py",
    "runners/dsl/python/substrate_rs/_native.build.json",
)
RAW = ROOT / "evaluation/reports/thoughtexperiment_random_sparse_reground_v1.json"
MODES = ("clean", "node_attr", "edge_attr", "edge_add", "edge_remove")

def sha_file(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()

def make_case(node_count: int, seed: int):
    from substrate_rs import NodeID, Substrate
    from domains.imagination import DetachedCollapse
    rng = random.Random(seed * 1_000_003 + node_count)
    sub = Substrate()
    ids = [sub.add_node("State", {"ordinal": i, "version": 0}) for i in range(node_count)]
    node_model = {i: {"ordinal": i, "version": 0} for i in range(node_count)}
    edge_model = {}
    while len(edge_model) < node_count * 2:
        src, tgt = rng.randrange(node_count), rng.randrange(node_count)
        if src == tgt:
            continue
        key = (src, "rel", tgt)
        if key in edge_model:
            continue
        attrs = {"ordinal": len(edge_model), "weight": len(edge_model) % 11}
        edge_model[key] = attrs
        sub.add_edge_unchecked(ids[src], "rel", ids[tgt], attrs)
    incident_model = {i: [] for i in range(node_count)}
    for (src, edge_type, tgt), attrs in edge_model.items():
        row = {"src": src, "type": edge_type, "tgt": tgt, "attrs": dict(attrs)}
        incident_model[src].append(row)
        incident_model[tgt].append(row)
    eligible = [i for i, edges in incident_model.items() if edges]
    rng.shuffle(eligible)
    targets = []
    target_set = set()
    for candidate in eligible:
        if any((edge["tgt"] if edge["src"] == candidate else edge["src"]) in target_set
               for edge in incident_model[candidate]):
            continue
        targets.append(candidate)
        target_set.add(candidate)
        if len(targets) == TARGETS:
            break
    if len(targets) != TARGETS:
        raise RuntimeError(f"could not select {TARGETS} independent non-isolated targets")
    rng.shuffle(targets)
    treatment = {node: MODES[i % len(MODES)] for i, node in enumerate(targets)}
    imagination = sub.add_node("Imagination", {"status": "imagining"})
    conclusion_ids, node_for_conclusion, before_edges_by_conclusion = [], {}, {}
    for node in targets:
        rows = sorted(incident_model[node], key=lambda e: (e["src"], e["type"], e["tgt"]))
        cid = sub.add_node("ImaginedConclusion", {
            "kind": "node_removed", "detached_id": node, "node_type_before": "State",
            "attrs_before": dict(node_model[node]), "incident_edges_before": rows,
            "status": "pending", "reason": "",
        })
        conclusion_ids.append(cid)
        node_for_conclusion[cid.value] = node
        before_edges_by_conclusion[cid.value] = {
            (row["src"], row["type"], row["tgt"]): dict(row["attrs"]) for row in rows}

    # Apply balanced mutations to the native graph and independent fact model.
    for node in targets:
        mode = treatment[node]
        if mode == "clean":
            continue
        if mode == "node_attr":
            value = f"changed-{seed}-{node}"
            node_model[node]["version"] = value
            sub.set_attr(ids[node], "version", value)
        elif mode == "edge_attr":
            candidates = [row for row in incident_model[node]
                if (row["src"], row["type"], row["tgt"]) in edge_model
                and (row["tgt"] if row["src"] == node else row["src"]) not in target_set]
            if not candidates:
                mode = treatment[node] = "edge_add"
            else:
                key = candidates[rng.randrange(len(candidates))]
                edge_key = (key["src"], key["type"], key["tgt"])
                attrs = dict(edge_model[edge_key])
                attrs["conflict"] = f"changed-{seed}-{node}"
                edge_model[edge_key] = attrs
                sub.add_edge_unchecked(ids[edge_key[0]], edge_key[1], ids[edge_key[2]], attrs)
        elif mode == "edge_remove":
            candidates = [row for row in incident_model[node]
                if (row["src"], row["type"], row["tgt"]) in edge_model
                and (row["tgt"] if row["src"] == node else row["src"]) not in target_set]
            if not candidates:
                mode = treatment[node] = "edge_add"
            else:
                key = candidates[rng.randrange(len(candidates))]
                edge_key = (key["src"], key["type"], key["tgt"])
                edge_model.pop(edge_key)
                sub.remove_edge(ids[edge_key[0]], edge_key[1], ids[edge_key[2]])
        if mode == "edge_add":
            sink = node_count - 1
            while sink in target_set:
                sink -= 1
            edge_type = f"probe_{node}"
            key = (node, edge_type, sink)
            attrs = {"injected": seed}
            edge_model[key] = attrs
            incident_model[node].append({"src": node, "type": edge_type, "tgt": sink,
                                         "attrs": dict(attrs)})
            incident_model[sink].append({"src": node, "type": edge_type, "tgt": sink,
                                         "attrs": dict(attrs)})
            sub.add_edge_unchecked(ids[node], edge_type, ids[sink], attrs)

    expected = {}
    for cid, node in node_for_conclusion.items():
        current_incident = {key: attrs for key, attrs in edge_model.items()
                            if key[0] == node or key[2] == node}
        before_incident = before_edges_by_conclusion[cid]
        expected[cid] = (node_model[node] == {"ordinal": node, "version": 0}
                         and current_incident == before_incident)
    detached = DetachedCollapse(detached=None, imagination_node=imagination,
        conclusion_nodes=conclusion_ids, focus_nodes=None, hypothesis=None, hyp_map={},
        cut_grounding=False, grounding_cut_count=0, steps_run=0, steps_budget=0,
        converged=True, conclusions={}, derived_only={}, n_conclusions=TARGETS,
        residual=0.0, confidence=1.0, phase_timings_ms={})
    return sub, detached, expected, treatment, node_for_conclusion, len(edge_model)

def worker() -> dict:
    from domains.imagination import reground
    rows = []
    for size in SIZES:
        for seed in SEEDS:
            sub, detached, expected, treatment, node_for_conclusion, edge_count = make_case(size, seed)
            started = time.perf_counter_ns()
            result = reground(sub, detached)
            elapsed_ms = (time.perf_counter_ns() - started) / 1e6
            observed = {int(item["conclusion"].value): bool(item["survived"])
                        for item in result["detail"]}
            mode_counts = {mode: {"expected_survive": 0, "observed_survive": 0,
                                  "n": 0, "parity": True} for mode in MODES}
            for cid, expected_survive in expected.items():
                mode = treatment[node_for_conclusion[cid]]
                cell = mode_counts[mode]
                cell["n"] += 1
                cell["expected_survive"] += int(expected_survive)
                cell["observed_survive"] += int(observed.get(cid, False))
                cell["parity"] &= observed.get(cid) is expected_survive
            rows.append({"nodes": size, "seed": seed, "edges": edge_count,
                "targets": TARGETS, "elapsed_ms": elapsed_ms,
                "survivors": len(result["survivors"]), "discarded": len(result["discarded"]),
                "exact_model_parity": observed == expected, "mode_counts": mode_counts})
    return {"pid": os.getpid(), "rows": rows}

def main() -> int:
    if len(sys.argv) == 2 and sys.argv[1] == "--worker":
        print(json.dumps(worker(), sort_keys=True, separators=(",", ":")))
        return 0
    from domains.engine_provenance import build_is_stale, rust_source_fingerprint
    stale = build_is_stale(str(ROOT))
    if stale:
        raise SystemExit("stale native engine: " + "; ".join(stale))
    workers = []
    for _ in range(5):
        proc = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--worker"],
            cwd=ROOT, text=True, capture_output=True)
        if proc.returncode:
            raise SystemExit(proc.stderr[-4000:])
        workers.append(json.loads(proc.stdout))
    flat = [row for worker_row in workers for row in worker_row["rows"]]
    aggregates = []
    for size in SIZES:
        vals = [row["elapsed_ms"] for row in flat if row["nodes"] == size]
        aggregates.append({"nodes": size, "graph_seed_cells": len(vals),
            "median_ms": statistics.median(vals),
            "max_ms": max(vals), "all_model_oracles_pass": all(
                row["exact_model_parity"] for row in flat if row["nodes"] == size)})
    import substrate_rs as srs
    binary = Path(srs._native.__file__).resolve()
    capture = {"schema": "ThoughtexperimentRandomSparseRegroundV1",
        "host": {"platform": platform.platform(), "machine": platform.machine(),
                 "python": sys.version.split()[0]},
        "engine_fingerprint": rust_source_fingerprint(str(ROOT)),
        "source_sha256": {name: sha_file(ROOT / name) for name in SOURCES},
        "binary": {"path": str(binary), "sha256": sha_file(binary)},
        "worker_count": len(workers), "workers": workers, "aggregates": aggregates,
        "checks": {"five_fresh_workers": len({w["pid"] for w in workers}) == 5,
                   "all_independent_oracles_pass": all(r["exact_model_parity"] for r in flat),
                   "all_conflict_modes_present": all(
                       all(r["mode_counts"][mode]["n"] > 0 for mode in MODES)
                       for r in flat)}}
    RAW.write_text(json.dumps(capture, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"checks": capture["checks"], "aggregates": aggregates}, indent=2))
    return 0 if all(capture["checks"].values()) else 1

if __name__ == "__main__":
    raise SystemExit(main())

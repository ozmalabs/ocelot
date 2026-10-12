#!/usr/bin/env python3
"""Independent integrity, scoring, and class-cluster uncertainty analysis."""
from __future__ import annotations
import importlib.util, json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
STEM = "quickdraw_one_shot_v1_20260929"
RAW = ROOT / f"evaluation/reports/{STEM}_raw.jsonl"
LOCK = ROOT / f"evaluation/substrate_capability/{STEM}_lock.json"
OUT = ROOT / f"evaluation/reports/{STEM}_analysis.json"

def load_runner():
    spec = importlib.util.spec_from_file_location("quickdraw_runner", ROOT / "scripts/substrate_quickdraw_one_shot_v1.py")
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod

def cluster_ci(class_counts, seed, draws):
    names = sorted(class_counts)
    correct = np.asarray([class_counts[x][0] for x in names], dtype=float)
    total = np.asarray([class_counts[x][1] for x in names], dtype=float)
    rng = np.random.default_rng(seed)
    take = rng.integers(0, len(names), size=(draws, len(names)))
    vals = correct[take].sum(axis=1) / total[take].sum(axis=1)
    return [float(x) for x in np.quantile(vals, [.025, .975])]

def main():
    records = [json.loads(x) for x in RAW.read_text().splitlines() if x.strip()]
    headers = [x for x in records if x["kind"] == "header"]
    workers = [x for x in records if x["kind"] == "worker"]
    footers = [x for x in records if x["kind"] == "footer"]
    runner = load_runner(); locked = json.loads(LOCK.read_text())["locked_inputs"]
    header = headers[0] if headers else {}; footer = footers[0] if footers else {}
    specs = header.get("specs", []); by_episode = {s.get("episode"): s for s in specs}
    errors = []; matrix = {}; expected = {(sys, e) for sys in runner.SYSTEMS for e in range(runner.EPISODES)}
    for spec in specs:
        classes = spec.get("classes", [])
        valid = len(classes) == 8 and len(set(classes)) == 8 and set(classes) == set(runner.CLASSES)
        valid &= len(spec.get("supports", {})) == 8 and len(spec.get("queries", [])) == 40
        for cls in runner.CLASSES:
            qids = [q["key_id"] for q in spec["queries"] if q["class"] == cls]
            valid &= len(qids) == runner.QUERIES_PER_CLASS and len(set(qids)) == len(qids)
            valid &= spec["supports"].get(cls) not in qids
        if not valid: errors.append({"episode": spec.get("episode"), "reason": "invalid task split"})
    for w in workers:
        ep = w.get("episode"); spec = by_episode.get(ep)
        valid = spec is not None and w.get("system") in runner.SYSTEMS
        if valid:
            valid &= w.get("episode_key") == runner.spec_key(spec)
            valid &= w.get("supports") == spec["supports"]
            valid &= w.get("query_ids") == [q["key_id"] for q in spec["queries"]]
            valid &= w.get("query_truth") == [q["class"] for q in spec["queries"]]
            valid &= w.get("query_count") == 40 and w.get("candidate_count") == 8
            valid &= len(w.get("predictions", [])) == 40 and len(w.get("random_predictions", [])) == 40
            valid &= bool(w.get("all_predictions_valid")) and all(p in runner.CLASSES for p in w["predictions"])
            valid &= all(p in runner.CLASSES for p in w["random_predictions"])
            valid &= w.get("correct") == sum(p == y for p, y in zip(w["predictions"], w["query_truth"]))
            valid &= w.get("random_correct") == sum(p == y for p, y in zip(w["random_predictions"], w["query_truth"]))
            key = (w["system"], ep)
            valid &= key not in matrix
            if valid: matrix[key] = w
        if not valid: errors.append({"system": w.get("system"), "episode": ep, "reason": "worker mismatch"})
    current = runner.source_inputs()
    keys = set(matrix)
    checks = {
        "single_header_and_footer": len(headers) == 1 and len(footers) == 1,
        "complete_100_episode_3_system_matrix": len(workers) == 300 and keys == expected,
        "capture_and_current_inputs_match_lock": header.get("locked_inputs") == locked and current == locked,
        "source_and_data_stable_during_capture": footer.get("source_stable") is True,
        "episode_and_worker_integrity": not errors,
        "all_episode_panels_shared_across_systems": all(len({matrix[(s,e)]["episode_key"] for s in runner.SYSTEMS}) == 1 for e in range(100) if all((s,e) in matrix for s in runner.SYSTEMS)),
    }
    by_system = {}; class_correct = {}
    for si, system in enumerate(runner.SYSTEMS):
        cc = {c: [0, 0] for c in runner.CLASSES}; random_correct = total_correct = 0
        ep_wall, ep_cpu = [], []
        for episode in range(100):
            w = matrix[(system, episode)]; random_correct += w["random_correct"]
            total_correct += w["correct"]; ep_wall.append(w["wall_ns"]); ep_cpu.append(w["process_cpu_ns"])
            for y, p in zip(w["query_truth"], w["predictions"]):
                cc[y][1] += 1; cc[y][0] += int(p == y)
        class_correct[system] = cc; total = sum(n for _, n in cc.values())
        by_system[system] = {"correct": total_correct, "total": total, "accuracy": total_correct / total,
            "class_cluster_bootstrap_95ci": cluster_ci(cc, locked["bootstrap_seed"] + si, locked["bootstrap_draws"]),
            "random_correct": random_correct, "random_total": total, "random_accuracy": random_correct / total,
            "chance_accuracy": 1 / len(runner.CLASSES),
            "median_worker_wall_ms": float(np.median(ep_wall) / 1e6),
            "median_worker_cpu_ms": float(np.median(ep_cpu) / 1e6),
            "peak_process_rss_bytes": max(matrix[(system,e)]["peak_rss_bytes"] for e in range(100)),
            "by_class": {c: {"correct": n, "total": d, "accuracy": n / d} for c, (n, d) in cc.items()}}
    differences = {}
    for i, left in enumerate(runner.SYSTEMS):
        for right in runner.SYSTEMS[i + 1:]:
            d = {c: [class_correct[left][c][0] - class_correct[right][c][0], class_correct[left][c][1]] for c in runner.CLASSES}
            differences[f"{left}-minus-{right}"] = {"accuracy_difference": by_system[left]["accuracy"] - by_system[right]["accuracy"],
                "class_cluster_bootstrap_95ci": cluster_ci(d, locked["bootstrap_seed"] + 100 + len(differences), locked["bootstrap_draws"])}
    prep = header.get("feature_prep", {})
    analysis = {"run_id": header.get("run_id"), "checks": checks, "integrity_pass": all(checks.values()),
        "passed_checks": sum(checks.values()), "total_checks": len(checks), "errors": errors,
        "episode_count": len(specs), "worker_count": len(workers), "class_count": 8,
        "feature_prep": prep, "systems": by_system, "paired_system_differences": differences,
        "run_wall_seconds": footer.get("run_wall_ns", 0) / 1e9,
        "run_process_cpu_seconds": footer.get("run_process_cpu_ns", 0) / 1e9,
        "claim_boundary": "100 fixed-class 8-way QuickDraw one-shot episodes over locally retained single-stroke drawings; graph-Term scoring runs in the native substrate, while data parsing and trajectory conditioning run in Python. No contributor IDs are available; this does not measure writer-disjoint or novel-class transfer."}
    OUT.write_text(json.dumps(analysis, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"analysis": str(OUT.relative_to(ROOT)), "checks": checks,
        "systems": {k: {q:v for q,v in val.items() if q != "by_class"} for k,val in by_system.items()},
        "paired_system_differences": differences}, indent=2))
    if not analysis["integrity_pass"]: raise SystemExit("QuickDraw integrity gate failed")

if __name__ == "__main__": main()

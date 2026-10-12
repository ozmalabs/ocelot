#!/usr/bin/env python3
"""Locked QuickDraw one-shot task through existing native graph-Term recognizers."""
from __future__ import annotations
import hashlib, json, os, platform, random, resource, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
import numpy as np
import substrate_rs as srs
from domains import pen_world as pw
from domains import glyph_motor_world as gm
from domains.recognition_graph import predict_synth_term, predict_pointset_term, predict_deform_term
from domains.engine_provenance import engine_provenance

STEM = "quickdraw_one_shot_v1_20260929"
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_QUICKDRAW_ONE_SHOT_V1_PREREG_20260929.md"
LOCK = ROOT / f"evaluation/substrate_capability/{STEM}_lock.json"
RAW = ROOT / f"evaluation/reports/{STEM}_raw.jsonl"
ANALYZER = ROOT / "scripts/analyze_substrate_quickdraw_one_shot_v1.py"
CLASSES = ("circle", "square", "triangle", "line", "zigzag", "star", "hexagon", "octagon")
SYSTEMS = ("ordered_dtw", "pointset", "deformable")
TERMS = {"ordered_dtw": predict_synth_term, "pointset": predict_pointset_term, "deformable": predict_deform_term}
EPISODES, QUERIES_PER_CLASS, N_POINTS = 100, 5, 64
SPEC_SEED, RANDOM_SEED, BOOT_SEED, BOOT_DRAWS = 20260929, 2209, 20260930, 10000

def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()

def dataset_manifest():
    entries = []
    h = hashlib.sha256()
    for cls in CLASSES:
        path = Path(pw.QD_FILES[cls])
        digest = sha(path)
        rel = path.resolve().relative_to(ROOT).as_posix()
        entries.append({"class": cls, "path": rel, "bytes": path.stat().st_size, "sha256": digest})
        h.update(rel.encode() + b"\0" + bytes.fromhex(digest))
    return {"files": entries, "manifest_sha256": h.hexdigest()}

def source_inputs():
    from substrate_rs import _native
    paths = ("scripts/substrate_quickdraw_one_shot_v1.py", "scripts/analyze_substrate_quickdraw_one_shot_v1.py",
             "docs/research/engine_substrate/SUBSTRATE_QUICKDRAW_ONE_SHOT_V1_PREREG_20260929.md",
             "domains/pen_world.py", "domains/glyph_motor_world.py", "domains/recognition_graph.py",
             "domains/engine_provenance.py", "runners/dsl/src/term.rs", "runners/dsl/src/substrate.rs",
             "runners/dsl/src/py.rs", "runners/dsl/python/substrate_rs/__init__.py")
    return {"source_sha256": {p: sha(ROOT / p) for p in paths},
            "native_extension": {"path": str(Path(_native.__file__).resolve().relative_to(ROOT)),
                                 "sha256": sha(Path(_native.__file__).resolve())},
            "dataset": dataset_manifest(), "engine_provenance": engine_provenance(),
            "python": sys.version, "platform": platform.platform(), "classes": list(CLASSES),
            "episodes": EPISODES, "queries_per_class": QUERIES_PER_CLASS, "trajectory_points": N_POINTS,
            "episode_seed": SPEC_SEED, "random_seed": RANDOM_SEED, "bootstrap_seed": BOOT_SEED,
            "bootstrap_draws": BOOT_DRAWS, "systems": list(SYSTEMS)}

def make_features():
    rows, counts = {}, {}
    for cls in CLASSES:
        drawings, bad = pw.load_quickdraw_drawings(pw.QD_FILES[cls])
        kept = []
        excluded = 0
        for d in drawings:
            if len(d["strokes_xy"]) != 1:
                excluded += 1
                continue
            feature = gm.to_trajectory(d["strokes_xy"][0], N_POINTS)
            kept.append({"key_id": str(d["key_id"]), "feature": feature.tolist()})
        if len(kept) < QUERIES_PER_CLASS + 1:
            raise RuntimeError(f"insufficient one-stroke drawings for {cls}: {len(kept)}")
        ids = [x["key_id"] for x in kept]
        if len(ids) != len(set(ids)):
            raise RuntimeError(f"duplicate QuickDraw key_id in {cls}")
        rows[cls] = kept
        counts[cls] = {"valid_drawings": len(drawings), "malformed_lines": bad,
                       "excluded_multistroke": excluded, "included_single_stroke": len(kept)}
    return rows, counts

def make_specs(rows):
    rng = np.random.default_rng(SPEC_SEED)
    specs = []
    for episode in range(EPISODES):
        supports, queries = {}, []
        for cls in CLASSES:
            ix = rng.permutation(len(rows[cls]))[:QUERIES_PER_CLASS + 1]
            supports[cls] = rows[cls][int(ix[0])]["key_id"]
            for j in ix[1:]:
                queries.append({"class": cls, "key_id": rows[cls][int(j)]["key_id"]})
        specs.append({"episode": episode, "classes": list(CLASSES), "supports": supports, "queries": queries})
    return specs

def spec_key(spec):
    return hashlib.sha256(json.dumps(spec, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

def main():
    if sys.argv[1:] == ["--lock"]:
        LOCK.parent.mkdir(parents=True, exist_ok=True)
        LOCK.write_text(json.dumps({"locked_inputs": source_inputs()}, indent=2, sort_keys=True) + "\n")
        print(LOCK.relative_to(ROOT)); return
    if sys.argv[1:]:
        raise SystemExit("usage: substrate_quickdraw_one_shot_v1.py [--lock]")
    locked = source_inputs()
    if not LOCK.exists() or json.loads(LOCK.read_text()).get("locked_inputs") != locked:
        raise SystemExit("missing/stale source lock")
    if RAW.exists():
        raise SystemExit(f"refusing to overwrite {RAW}")
    prep_wall, prep_cpu = time.perf_counter_ns(), time.process_time_ns()
    rows, source_counts = make_features()
    feature_by_id = {cls: {r["key_id"]: np.asarray(r["feature"], dtype=float) for r in data}
                     for cls, data in rows.items()}
    prep = {"wall_ns": time.perf_counter_ns() - prep_wall, "process_cpu_ns": time.process_time_ns() - prep_cpu,
            "source_counts": source_counts,
            "included_trajectories": sum(len(v) for v in rows.values())}
    specs = make_specs(rows)
    rng = random.Random(RANDOM_SEED)
    raw = RAW.open("x", encoding="utf-8")
    raw.write(json.dumps({"kind": "header", "run_id": STEM, "locked_inputs": locked,
                          "specs": specs, "feature_prep": prep}, separators=(",", ":"), sort_keys=True) + "\n")
    raw.flush()
    start, cpu_start = time.perf_counter_ns(), time.process_time_ns()
    workers = 0
    for system in SYSTEMS:
        term = TERMS[system]()
        for spec in specs:
            t0, c0 = time.perf_counter_ns(), time.process_time_ns()
            substrate = srs.Substrate()
            candidate_names = {}
            for cls in CLASSES:
                feature = feature_by_id[cls][spec["supports"][cls]]
                node = substrate.add_node("Concept", {"name": cls, gm.WORD_ATTR: 1.0})
                substrate.set_attr(node, gm.SYNTH_ATTR, feature.tolist())
                candidate_names[cls] = node
            predictions, random_predictions, query_truth, query_ids = [], [], [], []
            for query in spec["queries"]:
                cls, key_id = query["class"], query["key_id"]
                mark = substrate.add_node("Mark", {gm.MARK_ATTR: feature_by_id[cls][key_id].tolist()})
                winner = substrate.evaluate(type("Pred", (), {"_json": term})(), {"s": mark})
                pred = substrate.node(winner)["attrs"].get("name") if winner is not None else None
                predictions.append(pred); query_truth.append(cls); query_ids.append(key_id)
                random_predictions.append(CLASSES[rng.randrange(len(CLASSES))])
            row = {"system": system, "episode": spec["episode"], "episode_key": spec_key(spec),
                   "supports": spec["supports"], "query_ids": query_ids, "query_truth": query_truth,
                   "predictions": predictions, "random_predictions": random_predictions,
                   "correct": sum(p == y for p, y in zip(predictions, query_truth)),
                   "random_correct": sum(p == y for p, y in zip(random_predictions, query_truth)),
                   "query_count": len(query_truth), "candidate_count": len(candidate_names),
                   "all_predictions_valid": all(p in CLASSES for p in predictions),
                   "wall_ns": time.perf_counter_ns() - t0, "process_cpu_ns": time.process_time_ns() - c0,
                   "peak_rss_bytes": int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss *
                       (1024 if sys.platform.startswith("linux") else 1))}
            raw.write(json.dumps({"kind": "worker", **row}, separators=(",", ":"), sort_keys=True) + "\n")
            raw.flush(); workers += 1
            print(f"worker={workers}/{EPISODES * len(SYSTEMS)} system={system} episode={spec['episode'] + 1}", flush=True)
    stable = source_inputs() == locked
    footer = {"kind": "footer", "workers": workers, "source_stable": stable,
              "run_wall_ns": time.perf_counter_ns() - start,
              "run_process_cpu_ns": time.process_time_ns() - cpu_start}
    raw.write(json.dumps(footer, separators=(",", ":"), sort_keys=True) + "\n"); raw.close()
    if not stable:
        raise SystemExit("source or data changed during capture")
    print(json.dumps({"raw": str(RAW.relative_to(ROOT)), "workers": workers,
                      "feature_prep": prep, "runtime_seconds": footer["run_wall_ns"] / 1e9}, indent=2))

if __name__ == "__main__":
    main()

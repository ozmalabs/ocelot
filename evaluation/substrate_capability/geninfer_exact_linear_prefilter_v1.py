#!/usr/bin/env python3
"""Source-locked three-arm evaluation of the exact-linear GenInfer prefilter."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import random
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNNER = Path(__file__).resolve()
ANALYZER = ROOT / "evaluation/substrate_capability/analyze_geninfer_exact_linear_prefilter_v1.py"
PREREG = ROOT / "docs/research/engine_substrate/SUBSTRATE_GENINFER_EXACT_LINEAR_PREFILTER_V1_PREREG_20261006.md"
AMENDMENT = ROOT / "docs/research/engine_substrate/SUBSTRATE_GENINFER_EXACT_LINEAR_PREFILTER_V1_1_AMENDMENT_20261006.md"
AMENDMENT12 = ROOT / "docs/research/engine_substrate/SUBSTRATE_GENINFER_EXACT_LINEAR_PREFILTER_V1_2_AMENDMENT_20261006.md"
AMENDMENT13 = ROOT / "docs/research/engine_substrate/SUBSTRATE_GENINFER_EXACT_LINEAR_PREFILTER_V1_3_AMENDMENT_20261006.md"
PILOT_RESULT = ROOT / "docs/research/engine_substrate/SUBSTRATE_GENINFER_EXACT_LINEAR_PREFILTER_PILOT_V1_RESULTS_20261006.md"
HIGHBOUND_RESULT = ROOT / "docs/research/engine_substrate/SUBSTRATE_GENINFER_EXACT_LINEAR_PREFILTER_V1_1_HIGHBOUND_RESULTS_20261006.md"
ORACLE_RESULT = ROOT / "docs/research/engine_substrate/SUBSTRATE_GENINFER_EXACT_LINEAR_PREFILTER_ORACLE_V1_RESULTS_20261006.md"
ORACLE_RUNNER = ROOT / "evaluation/substrate_capability/run_geninfer_exact_linear_prefilter_oracle_v1.py"
ORACLE_REPORT = ROOT / "evaluation/reports/geninfer_exact_linear_prefilter_oracle_v1_2_20261006.json"
LOCK = ROOT / "evaluation/substrate_capability/geninfer_exact_linear_prefilter_v1_lock_20261006.json"
RAW = ROOT / "evaluation/reports/geninfer_exact_linear_prefilter_v1_raw_20261006.json"
PARTIAL = ROOT / "evaluation/reports/geninfer_exact_linear_prefilter_v1_partial_20261006.json"
DTYPES = ["pred", "id", "coord:r", "coord:c", "val"]
TRAIN = [(1, 0), (2, 0), (0, 1), (0, 2), (1, 1), (3, 1), (4, 1)]
TRANSFER = [(2, 1), (1, 3), (3, 2), (2, 3), (5, 1), (3, 3)]
SEED = 20261006
SEED_ID = "shape_decode_loop"


def sha(path: Path | str) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def seed_closure() -> list[str]:
    # CORE_SEEDS is a source-backed tuple; read its value without importing the
    # extension so --lock does not depend on whichever native module is active.
    import ast
    boot = ROOT / "substrate/boot_core.py"
    tree = ast.parse(boot.read_text())
    core = []
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "CORE_SEEDS" for t in node.targets):
            core = ast.literal_eval(node.value)
            break
    pending = [*core, SEED_ID]
    seen: set[str] = set()
    while pending:
        sid = str(pending.pop())
        if sid in seen:
            continue
        seen.add(sid)
        manifest = json.loads((ROOT / "seeds" / f"{sid}.json").read_text())
        pending.extend(str(dep) for dep in manifest.get("depends_on", ()))
    return sorted(f"seeds/{sid}.json" for sid in seen)


def source_paths() -> list[str]:
    paths = {
        "runners/dsl/Cargo.toml", "runners/dsl/Cargo.lock",
        "runners/dsl/src/shape_decode.rs", "runners/dsl/src/term.rs",
        "runners/dsl/src/jsonio.rs", "runners/dsl/src/reflect.rs",
        "runners/dsl/src/scale_audit.rs", "runners/dsl/src/graph_rules.rs",
        "runners/dsl/src/rewrite.rs", "runners/dsl/src/persist.rs",
        "runners/dsl/python/substrate_rs/__init__.py",
        "domains/reflective_faculty.py", "substrate/boot_core.py",
        "substrate/seed_loader.py", str(RUNNER.relative_to(ROOT)),
        str(ANALYZER.relative_to(ROOT)), str(PREREG.relative_to(ROOT)),
        str(ORACLE_RUNNER.relative_to(ROOT)), str(ORACLE_REPORT.relative_to(ROOT)),
        str(AMENDMENT.relative_to(ROOT)), str(AMENDMENT12.relative_to(ROOT)), str(AMENDMENT13.relative_to(ROOT)), str(PILOT_RESULT.relative_to(ROOT)), str(HIGHBOUND_RESULT.relative_to(ROOT)), str(ORACLE_RESULT.relative_to(ROOT)),
        "docs/research/engine_substrate/SUBSTRATE_NONLINEAR_DIMENSION_INDUCTION_V2_IMPLEMENTATION_STATUS_20261006.md",
        "docs/research/engine_substrate/SUBSTRATE_CAPABILITY_AND_TRACTABILITY_MEASUREMENT_PLAN.md",
    }
    paths.update(seed_closure())
    return sorted(paths)


def source_manifest() -> dict[str, str]:
    return {path: sha(ROOT / path) for path in source_paths()}


def cells() -> list[dict]:
    return [
        {"condition": "linear_positive", "family": "linear", "geometry": "full", "corruption": None,
         "identity_case": "unique"},
        {"condition": "coupled_quadratic", "family": "coupled", "geometry": "full", "corruption": None,
         "identity_case": "unique"},
        {"condition": "quadratic_cross_term", "family": "cross", "geometry": "full", "corruption": None,
         "identity_case": "unique"},
        {"condition": "rank_deficient", "family": "coupled", "geometry": "collinear", "corruption": None,
         "identity_case": "unique"},
        {"condition": "corrupted_training", "family": "coupled", "geometry": "full", "corruption": "last_target_u_plus_1",
         "identity_case": "unique"},
        {"condition": "duplicate_identity", "family": "coupled", "geometry": "full", "corruption": None,
         "identity_case": "duplicate_last_as_first"},
        {"condition": "missing_identity", "family": "coupled", "geometry": "full", "corruption": None,
         "identity_case": "replace_last_target_id"},
        {"condition": "cubic_out_of_family", "family": "centered_cubic", "geometry": "full", "corruption": None,
         "identity_case": "unique"},
    ]


def schedule() -> list[dict]:
    rows = []
    for cell in cells():
        for repeat in range(1, 11):
            for feature in ("off", "quadratic", "prefilter"):
                for audit in (False, True):
                    rows.append({"condition": cell["condition"], "repeat": repeat,
                                 "feature": feature, "audit": audit})
    random.Random(SEED).shuffle(rows)
    for i, row in enumerate(rows):
        row["worker_id"] = f"qvpf1_{i:03d}_{row['condition']}_{row['feature']}_a{int(row['audit'])}_r{row['repeat']}"
    return rows


def lock_payload(native_off: Path, native_quadratic: Path, native_prefilter: Path) -> dict:
    native_off, native_quadratic, native_prefilter = map(Path.resolve, (native_off, native_quadratic, native_prefilter))
    for path in (native_off, native_quadratic, native_prefilter):
        if not path.is_file():
            raise SystemExit(f"native binary does not exist: {path}")
    if len({sha(native_off), sha(native_quadratic), sha(native_prefilter)}) != 3:
        raise SystemExit("all three native binaries must be distinct")
    oracle = json.loads(ORACLE_REPORT.read_text())
    if oracle.get("status") != "pass" or oracle.get("case_count") != 2500:
        raise SystemExit("finite enumerator oracle is missing or did not pass")
    return {
        "schema": "GenInferExactLinearPrefilterV1Lock",
        "protocol": "SUBSTRATE_GENINFER_EXACT_LINEAR_PREFILTER_V1_PREREG_20261006 + V1_1_AMENDMENT_20261006 + V1_2_AMENDMENT_20261006 + V1_3_AMENDMENT_20261006",
        "sources_sha256": source_manifest(),
        "oracle_sha256": sha(ORACLE_REPORT),
        "oracle": {"case_count": oracle["case_count"], "fnv1a64": oracle["oracle_fnv1a64"]},
        "native_binaries": {
            "off": {"path": str(native_off), "sha256": sha(native_off), "cargo_features": []},
            "quadratic": {"path": str(native_quadratic), "sha256": sha(native_quadratic), "cargo_features": ["geninfer_quadratic_map_solver"]},
            "prefilter": {"path": str(native_prefilter), "sha256": sha(native_prefilter), "cargo_features": ["geninfer_quadratic_map_solver", "geninfer_linear_exact_prefilter"]},
        },
        "train_coordinates": [list(p) for p in TRAIN],
        "transfer_coordinates": [list(p) for p in TRANSFER],
        "transfer_disjoint_from_train": not (set(TRAIN) & set(TRANSFER)),
        "dim_types": DTYPES,
        "cells": cells(),
        "seed": SEED,
        "worker_count": 480,
        "worker_timeout_seconds": 300,
        "schedule": schedule(),
    }


def relation_rows(points: list[tuple[int, int]], prefix: str, family: str,
                  identity_case: str = "unique") -> list[list]:
    rows = []
    min_x = min(x for x, _ in points)
    min_y = min(y for _, y in points)
    for i, (x, y) in enumerate(points):
        x, y = x - min_x, y - min_y
        if family == "linear":
            u, v = x + y, 2 * y
        elif family == "coupled":
            u, v = x + x * y, y + x * x
        elif family == "cross":
            u, v = x, y + x * y
        elif family == "cubic":
            u, v = x, y + x ** 3
        elif family == "centered_cubic":
            u, v = x, y + (x - 2) ** 3
        else:
            raise ValueError(f"unknown family {family}")
        ident = f"{prefix}_{i}"
        if identity_case == "duplicate_last_as_first" and i == len(points) - 1:
            ident = f"{prefix}_0"
        rows.append(["cell", ident, u, v, "red"])
    return rows


def coordinates_for(cell: dict) -> list[tuple[int, int]]:
    if cell["geometry"] == "collinear":
        return [(i + 1, 0) for i in range(7)]
    return TRAIN


def generator_payloads(sub) -> list[dict]:
    out = []
    for nid in sub.nodes("DimensionGenerator"):
        attrs = sub.node(nid)["attrs"]
        if attrs.get("kind") in ("linear", "quadratic2"):
            out.append({"name": attrs.get("name"), "kind": attrs.get("kind"),
                        "matrix": list(attrs.get("matrix") or ()),
                        "coefficients": list(attrs.get("coefficients") or ()),
                        "coord_dims": list(attrs.get("coord_dims") or ()),
                        "params": list(attrs.get("params") or ())})
    return sorted(out, key=lambda row: (row["kind"], str(row["name"])))


def worker(case: dict, native_path: Path) -> dict:
    heartbeat = Path(os.environ["QGENINFER_WORKER_HEARTBEAT"]) if os.environ.get("QGENINFER_WORKER_HEARTBEAT") else None
    def pulse(stage: str) -> None:
        if heartbeat is not None:
            heartbeat.write_text(stage + "\n")
    pulse("temporary_package")
    temp = tempfile.TemporaryDirectory(prefix=f"qgeninfer-v1-{case['worker_id']}-")
    temp_root = Path(temp.name)
    package_src = ROOT / "runners/dsl/python/substrate_rs"
    package_dst = temp_root / "substrate_rs"
    shutil.copytree(package_src, package_dst,
                    ignore=shutil.ignore_patterns("_native*.so", "__pycache__"))
    shutil.copy2(native_path, package_dst / "_native.abi3.so")
    sys.path[:0] = [str(temp_root), str(ROOT), str(ROOT / "runners/dsl/python")]
    try:
        pulse("importing_engine_and_boot_helpers")
        from substrate.boot_core import boot_core
        from domains import reflective_faculty as rf
        from substrate_rs import _native
        pulse("booting_training_substrate")
        cell = next(c for c in cells() if c["condition"] == case["condition"])
        coords = coordinates_for(cell)
        train_base = [["cell", f"train_{i}", x, y, "red"] for i, (x, y) in enumerate(coords)]
        train_goal = relation_rows(coords, "train", cell["family"], cell["identity_case"])
        if cell["corruption"]:
            train_goal[-1][2] += 1
        transfer_base = [["cell", f"held_{i}", x, y, "red"] for i, (x, y) in enumerate(TRANSFER)]
        transfer_goal = relation_rows(TRANSFER, "held", cell["family"])
        if cell["identity_case"] == "duplicate_last_as_first":
            train_base[-1][1] = train_base[0][1]
        if cell["identity_case"] == "replace_last_target_id":
            train_goal[-1][1] = "train_orphan"

        native_started = time.perf_counter_ns()
        sub, agent = boot_core()
        native = rf._native_eval2(sub)
        rf._ensure_shape_decode_loop(sub, native, agent)
        pulse("running_training_closure")
        sub.set_attr(agent, "gen_infer_enabled", 1.0)
        sub.set_attr(agent, "gen_quadratic_enabled", float(case["feature"] in ("quadratic", "prefilter")))
        sub.set_attr(agent, "gen_linear_exact_enabled", float(case["feature"] == "prefilter"))
        _native.Substrate.scale_audit_reset()
        _native.Substrate.scale_audit_set_enabled(bool(case["audit"]))
        sub.add_node("ShapeSignature", {"name": "qv21_train_base", "signature": json.dumps(train_base),
            "kind": "faculty", "faculty": "qv21_train_base", "dim_types": DTYPES})
        sub.add_node("ShapeSignature", {"name": "qv21_held_base", "signature": json.dumps(transfer_base),
            "kind": "faculty", "faculty": "qv21_held_base", "dim_types": DTYPES})
        initial = generator_payloads(sub)
        initial_quanta = len(list(sub.nodes("CapabilityAxis")))
        obs = sub.add_node("Observation", {"signature": train_goal, "key": ["qv21", case["worker_id"], "train"],
            "status": "decoded", "residual": train_goal, "decoded_epoch": 0.0, "dim_types": DTYPES})
        sub.add_edge(agent, "observed", obs)
        train_start = time.perf_counter_ns()
        train_work = int(native.run_rules())
        train_ns = time.perf_counter_ns() - train_start
        pulse("serializing_training_graph")
        train_attrs = sub.node(obs)["attrs"]
        post_train = generator_payloads(sub)
        training_quanta = len(list(sub.nodes("CapabilityAxis"))) - initial_quanta
        train_counters = dict(_native.Substrate.scale_audit_snapshot()) if case["audit"] else {}
        serialized = sub.graph_to_dict()
        _native.Substrate.scale_audit_reset()
        _native.Substrate.scale_audit_set_enabled(bool(case["audit"]))

        # Rules are loaded into the fresh native substrate first; then the
        # serialized graph replaces its graph state while preserving the rule
        # engine and node identities.
        restored, restored_agent = boot_core()
        restored_native = rf._native_eval2(restored)
        rf._ensure_shape_decode_loop(restored, restored_native, restored_agent)
        restored.graph_from_dict(serialized)
        pulse("running_heldout_closure_after_reload")
        if restored_agent != agent:
            raise RuntimeError(f"graph reload changed the Agent NodeID: {restored_agent} != {agent}")
        post_reload = generator_payloads(restored)
        held = restored.add_node("Observation", {"signature": transfer_goal,
            "key": ["qv21", case["worker_id"], "heldout"], "status": "decoded",
            "residual": transfer_goal, "decoded_epoch": restored.node(restored_agent)["attrs"].get("codebook_epoch", 0.0),
            "dim_types": DTYPES})
        restored.add_edge(restored_agent, "observed", held)
        held_start = time.perf_counter_ns()
        held_work = int(restored_native.run_rules())
        held_ns = time.perf_counter_ns() - held_start
        pulse("collecting_result")
        held_attrs = restored.node(held)["attrs"]
        held_counters = dict(_native.Substrate.scale_audit_snapshot()) if case["audit"] else {}
        after_held = generator_payloads(restored)
        heldout_quanta = len(list(restored.nodes("CapabilityAxis"))) - initial_quanta - training_quanta
        dim = held_attrs.get("dim_infer")
        transform_receipts = []
        for t in restored.neighbours(held, "has_transform"):
            transform_receipts.append(restored.node(t)["attrs"])
        rss = __import__("resource").getrusage(__import__("resource").RUSAGE_SELF).ru_maxrss
        total_wall_ns = time.perf_counter_ns() - native_started
        return {
            "worker_id": case["worker_id"], "condition": cell["condition"],
            "feature": case["feature"], "audit": bool(case["audit"]), "repeat": case["repeat"],
            "training": {"status": train_attrs.get("status"), "residual": train_attrs.get("residual"),
                "rule_work": train_work, "closure_ns": train_ns, "generator_payloads": post_train,
                "quanta_added": training_quanta, "counters": train_counters},
            "reload": {"serialized_node_count": len(serialized.get("nodes", [])),
                "serialized_edge_count": len(serialized.get("edges", [])),
                "agent_node_id_preserved": restored_agent == agent,
                "generator_payloads": post_reload},
            "heldout": {"status": held_attrs.get("status"), "residual": held_attrs.get("residual"),
                "dim_infer": dim, "transform_receipts": transform_receipts,
                "rule_work": held_work, "closure_ns": held_ns,
                "generator_payloads": after_held, "quanta_added": heldout_quanta,
                "counters": held_counters,
                "base": transfer_base, "observed_target": transfer_goal},
            "initial_generator_payloads": initial,
            "cpu_user_s": __import__("resource").getrusage(__import__("resource").RUSAGE_SELF).ru_utime,
            "cpu_system_s": __import__("resource").getrusage(__import__("resource").RUSAGE_SELF).ru_stime,
            "process_peak_rss_kib": rss, "worker_wall_ns": total_wall_ns,
            "native_sha256": sha(native_path), "native_module_path": str(Path(_native.__file__).resolve()),
        }
    finally:
        temp.cleanup()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lock", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--native-off", type=Path)
    ap.add_argument("--native-quadratic", type=Path)
    ap.add_argument("--native-prefilter", type=Path)
    ap.add_argument("--worker-index", type=int)
    args = ap.parse_args()
    if args.lock:
        if LOCK.exists() or RAW.exists() or PARTIAL.exists():
            raise SystemExit("refusing to overwrite a lock or capture")
        if not args.native_off or not args.native_quadratic or not args.native_prefilter:
            raise SystemExit("--lock requires all three native paths")
        payload = lock_payload(args.native_off, args.native_quadratic, args.native_prefilter)
        LOCK.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        print(LOCK.relative_to(ROOT))
        return 0
    if args.worker_index is not None:
        lock = json.loads(LOCK.read_text())
        if not (0 <= args.worker_index < len(lock["schedule"])):
            raise SystemExit("invalid worker index")
        case = lock["schedule"][args.worker_index]
        native_path = Path(lock["native_binaries"][case["feature"]]["path"])
        result = worker(case, native_path)
        print(json.dumps(result, sort_keys=True, separators=(",", ":")))
        return 0
    if not args.run or args.lock:
        raise SystemExit("usage: --lock --native-off PATH --native-quadratic PATH --native-prefilter PATH | --run")
    if RAW.exists() or PARTIAL.exists():
        raise SystemExit("refusing to overwrite a capture or partial capture")
    lock = json.loads(LOCK.read_text())
    if source_manifest() != lock["sources_sha256"]:
        raise SystemExit("source drift from lock")
    for arm in ("off", "quadratic", "prefilter"):
        item = lock["native_binaries"][arm]
        if sha(item["path"]) != item["sha256"]:
            raise SystemExit(f"native {arm} binary drift from lock")
    rows = []
    failures = []
    started = time.perf_counter()
    def checkpoint(final: bool = False) -> None:
        stable_now = source_manifest() == lock["sources_sha256"] and all(
            sha(lock["native_binaries"][arm]["path"]) == lock["native_binaries"][arm]["sha256"]
            for arm in ("off", "quadratic", "prefilter"))
        report_now = {"schema": "GenInferExactLinearPrefilterV1Raw", "lock_sha256": sha(LOCK),
            "captured_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "host": platform.platform(), "python": sys.version,
            "locked_sources_sha256": lock["sources_sha256"], "post_run_sources_sha256": source_manifest(),
            "source_and_binaries_stable": stable_now, "schedule": lock["schedule"],
            "workers": rows, "failures": failures, "completed_count": len(rows),
            "runtime_seconds": time.perf_counter() - started,
            "capture_complete": final and not failures and len(rows) == len(lock["schedule"])}
        destination = RAW if final else PARTIAL
        tmp = destination.with_suffix(destination.suffix + ".tmp")
        tmp.write_text(json.dumps(report_now, indent=2, sort_keys=True) + "\n")
        os.replace(tmp, destination)

    for i, case in enumerate(lock["schedule"]):
        heartbeat = Path(tempfile.gettempdir()) / f"qgeninfer-v1-{case['worker_id']}.heartbeat"
        print(f"starting {i + 1}/{len(lock['schedule'])} {case['worker_id']}", flush=True)
        try:
            env = os.environ.copy()
            env["QGENINFER_WORKER_HEARTBEAT"] = str(heartbeat)
            proc = subprocess.Popen([sys.executable, str(RUNNER), "--worker-index", str(i)],
                cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            worker_started = time.monotonic()
            last_stage = None
            while True:
                try:
                    stdout, stderr = proc.communicate(timeout=5)
                    break
                except subprocess.TimeoutExpired:
                    stage = heartbeat.read_text().strip() if heartbeat.exists() else "process_startup"
                    if stage != last_stage:
                        print(f"worker {i + 1}/{len(lock['schedule'])} {case['worker_id']}: {stage}", flush=True)
                        last_stage = stage
                    if time.monotonic() - worker_started >= lock["worker_timeout_seconds"]:
                        proc.kill()
                        stdout, stderr = proc.communicate()
                        for leftover in Path(tempfile.gettempdir()).glob(f"qgeninfer-v1-{case['worker_id']}-*"):
                            shutil.rmtree(leftover, ignore_errors=True)
                        failures.append({"worker_id": case["worker_id"], "timeout": lock["worker_timeout_seconds"],
                            "last_stage": stage, "stdout": stdout[-4000:], "stderr": stderr[-4000:]})
                        break
            if not failures:
                if proc.returncode:
                    for leftover in Path(tempfile.gettempdir()).glob(f"qgeninfer-v1-{case['worker_id']}-*"):
                        shutil.rmtree(leftover, ignore_errors=True)
                    failures.append({"worker_id": case["worker_id"], "returncode": proc.returncode,
                        "stdout": stdout[-4000:], "stderr": stderr[-4000:]})
                else:
                    try:
                        rows.append(json.loads(stdout))
                    except Exception as exc:
                        failures.append({"worker_id": case["worker_id"], "parse_error": repr(exc),
                            "stdout": stdout[-4000:], "stderr": stderr[-4000:]})
        finally:
            heartbeat.unlink(missing_ok=True)
        checkpoint()
        if failures:
            break
        stable_now = source_manifest() == lock["sources_sha256"] and all(
            sha(lock["native_binaries"][arm]["path"]) == lock["native_binaries"][arm]["sha256"]
            for arm in ("off", "quadratic", "prefilter"))
        if not stable_now:
            failures.append({"reason": "source_or_binary_drift_during_capture", "after_worker": case["worker_id"]})
            break
        print(f"completed {i + 1}/{len(lock['schedule'])} workers", flush=True)
    stable = source_manifest() == lock["sources_sha256"] and all(
        sha(lock["native_binaries"][arm]["path"]) == lock["native_binaries"][arm]["sha256"]
        for arm in ("off", "quadratic", "prefilter"))
    if not stable and not failures:
        failures.append({"reason": "source_or_binary_drift_during_capture"})
    checkpoint(final=True)
    PARTIAL.unlink(missing_ok=True)
    print(json.dumps({"output": RAW.relative_to(ROOT).as_posix(),
        "completed": len(rows), "failures": len(failures), "source_stable": stable}, sort_keys=True))
    return 0 if not failures and len(rows) == len(lock["schedule"]) and stable else 1


if __name__ == "__main__":
    raise SystemExit(main())

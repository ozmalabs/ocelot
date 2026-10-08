#!/usr/bin/env python3
"""Source-locked process-restart and receipt-replay integration panel."""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_ADEQUACY_RECEIPT_PERSISTENCE_V1_PREREG_20261002.md"
AMENDMENT = ROOT / "docs/research/engine_substrate/SUBSTRATE_ADEQUACY_RECEIPT_PERSISTENCE_V1_1_AMENDMENT_20261002.md"
PERFORMANCE_AMENDMENT = ROOT / "docs/research/engine_substrate/SUBSTRATE_ADEQUACY_RECEIPT_PERSISTENCE_V1_2_AMENDMENT_20261002.md"
RUNNER = Path(__file__).resolve()
ANALYZER = ROOT / "evaluation/substrate_capability/analyze_substrate_adequacy_receipt_persistence_v1.py"
LOCK = ROOT / "evaluation/substrate_capability/substrate_adequacy_receipt_persistence_v1_lock_20261002.json"
RAW = ROOT / "evaluation/reports/substrate_adequacy_receipt_persistence_v1_raw_20261002.json"
ACTIVE = ("domains/code_reading.py", "domains/code_writing.py", "domains/code_write_growth.py",
          "domains/independent_adequacy.py", "domains/information_commitment.py",
          "domains/teach.py", "domains/ast_to_term.py",
          "substrate/world_adapter.py", "substrate/boot_all.py", "substrate/seed_loader.py",
          "runners/dsl/src/term.rs", "runners/dsl/src/py.rs",
          "runners/dsl/src/graph_rules.rs", "runners/dsl/src/substrate.rs",
          "runners/dsl/python/substrate_rs/__init__.py",
          "runners/dsl/python/substrate_rs/_native.build.json",
          "seeds/code_write_constructions.json")
SOURCE = "def square(x):\n    return x * x\n"
REQUEST = "square x"
REPETITIONS = 3


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_hashes() -> dict:
    import substrate_rs
    values = {p: sha(ROOT / p) for p in ACTIVE}
    values["native_binary"] = sha(Path(substrate_rs._native.__file__).resolve())
    manifests = sorted([*ROOT.joinpath("seeds").glob("*.json"),
                        *ROOT.joinpath("seeds/generated").glob("*.json")])
    digest = hashlib.sha256()
    for path in manifests:
        digest.update(path.relative_to(ROOT).as_posix().encode()); digest.update(b"\0")
        digest.update(sha(path).encode()); digest.update(b"\n")
    values["seed_manifest_inventory"] = digest.hexdigest()
    return values


def lock_payload() -> dict:
    return {"schema": "SubstrateAdequacyReceiptPersistenceV1Lock",
            "files": {str(p.relative_to(ROOT)): sha(p) for p in
                      (RUNNER, ANALYZER, PROTOCOL, AMENDMENT, PERFORMANCE_AMENDMENT)},
            "active": source_hashes(),
            "design": {"repetitions": REPETITIONS, "source": SOURCE, "request": REQUEST,
                       "restart": "writer and reader are distinct subprocesses",
                       "persistence": "parent-owned temporary seed directory",
                       "replay": "same accepted receipt on restored exact candidate; expected idempotent"}}


def _state(agent) -> dict:
    sub = agent.s
    names = [(sub.node(n)["attrs"].get("name"), dict(sub.node(n)["attrs"]))
             for n in sub.nodes("ShapeSignature")
             if sub.node(n)["attrs"].get("name") == "taught_square"]
    agent_node = next(n for n in sub.nodes("Agent") if not sub.node(n)["attrs"].get("is_class"))
    return {"shapes": names, "epoch": sub.node(agent_node)["attrs"].get("write_codebook_epoch", 0) or 0}


def writer(rep: int, seed_dir: Path, expected_active: dict) -> dict:
    os.environ.setdefault("OZMA_NO_LLM", "1")
    os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")
    if source_hashes() != expected_active:
        raise RuntimeError("writer sources differ from pre-run lock")
    from domains import code_reading as cdr
    from domains import code_write_growth as cwg
    from domains import independent_adequacy as ia
    from substrate.boot_all import load_all_seeds
    from substrate.world_adapter import WorldAdapter

    trace_dir = seed_dir / ".trace"
    trace_dir.mkdir(exist_ok=True)
    agent = WorldAdapter(seeds=())
    boot_start = time.perf_counter_ns()
    boot = load_all_seeds(agent)
    boot_ns = time.perf_counter_ns() - boot_start
    reading = cdr.read_function(agent, SOURCE, "square")
    term, args, name = reading["term"], list(reading["args"]), reading["name"]
    candidate_id = ia.candidate_id_for_write_shape(SOURCE, name, args, term, REQUEST)
    request = ia.propose_audit_request(
        candidate_id, term, [{"inputs": {"x": 0}, "expected": 0}],
        [{"x": 1}, {"x": 2}, {"x": 3}], acquisition_source_ids=["acq:square:v1"],
        count=1, seed="adequacy-persistence-v1")
    probe = request["probes"][0]
    x = probe["inputs"]["x"]
    receipt = ia.adjudicate_audit_receipt(
        request, candidate_id, term,
        [{"probe_id": probe["probe_id"], "inputs": probe["inputs"],
          "labels": [{"source_id": "oracle:square:v1", "label_id": f"square:{x}",
                      "expected": x*x}]}],
        lambda _term, env: env["x"] * env["x"],
        acquisition_source_ids=["acq:square:v1"])
    native = cdr._resolve(agent)[1]
    export_results = {}
    order = (["full", "prefix"] if rep % 2 else ["prefix", "full"])
    for mode in order:
        started = time.perf_counter_ns()
        if mode == "full":
            rows = native.export_rules()
        else:
            export_prefix = getattr(native, "export_rules_prefix", None)
            if not callable(export_prefix):
                raise RuntimeError("native binding lacks export_rules_prefix")
            rows = export_prefix("ic_gate_manifold_projection")
        export_results[mode] = {"wall_ns": time.perf_counter_ns() - started,
                                "row_count": len(rows),
                                "gate_rule_found": any(row.get("name") == "ic_gate_manifold_projection"
                                                        for row in rows)}
    before = _state(agent)
    started = time.perf_counter_ns()
    result = cwg.teach_write_shape_from_example(
        agent, SOURCE, request_text=REQUEST, seeds_dir=seed_dir,
        adequacy_receipt=receipt, require_adequacy_receipt=True)
    teach_ns = time.perf_counter_ns() - started
    loaded_gate_rules = native.export_rules_prefix("ic_gate_manifold_projection")
    gate_loaded_after_teach = any(row.get("name") == "ic_gate_manifold_projection"
                                  for row in loaded_gate_rules)
    after = _state(agent)
    manifest = seed_dir / "code_write_constructions.json"
    if not manifest.is_file():
        raise RuntimeError(f"expected durable manifest missing: {manifest}")
    attrs = next(attrs for name, attrs in after["shapes"] if name == "taught_square")
    (trace_dir / "accepted_receipt.json").write_text(json.dumps(receipt, sort_keys=True) + "\n")
    payload = {"repetition": rep, "phase": "writer", "pid": os.getpid(),
               "boot_ns": boot_ns, "loaded_seed_count": int(boot.get("loaded", 0) or 0),
               "teach_ns": teach_ns, "result_ok": result.get("ok"),
               "export_order": order, "export_probe": export_results,
               "gate_loaded_after_teach": gate_loaded_after_teach,
               "saved": result.get("teach", {}).get("saved"),
               "persisted": result.get("teach", {}).get("persisted"),
               "receipt_status": receipt["status"], "candidate_id": candidate_id,
               "before": before, "after": after, "attrs": attrs,
               "manifest_sha256": sha(manifest), "receipt_sha256": sha(trace_dir / "accepted_receipt.json"),
               "active_after": source_hashes()}
    payload["pass"] = (receipt["status"] == "accepted" and result.get("ok") is True
                       and result.get("candidate_id") == candidate_id
                       and payload["saved"] is True and payload["persisted"] is True
                       and export_results["full"]["gate_rule_found"] == export_results["prefix"]["gate_rule_found"]
                       and gate_loaded_after_teach
                       and len(after["shapes"]) == len(before["shapes"]) + 1
                       and after["epoch"] == before["epoch"] + 1
                       and payload["active_after"] == expected_active)
    return payload


def reader(rep: int, seed_dir: Path, expected_active: dict) -> dict:
    os.environ.setdefault("OZMA_NO_LLM", "1")
    os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")
    if source_hashes() != expected_active:
        raise RuntimeError("reader sources differ from pre-run lock")
    from domains import code_write_growth as cwg
    from substrate.boot_all import load_all_seeds
    from substrate.world_adapter import WorldAdapter

    trace_dir = seed_dir / ".trace"
    expected = json.loads((trace_dir / "expected_writer.json").read_text())
    receipt = json.loads((trace_dir / "accepted_receipt.json").read_text())
    agent = WorldAdapter(seeds=())
    boot_start = time.perf_counter_ns()
    loaded = load_all_seeds(agent, seed_dir=seed_dir / "merged_seeds")
    boot_ns = time.perf_counter_ns() - boot_start
    restored = _state(agent)
    attrs_match = len(restored["shapes"]) == 1 and restored["shapes"][0][1] == expected["attrs"]
    manifest_sha = sha(seed_dir / "code_write_constructions.json")
    receipt_sha = sha(trace_dir / "accepted_receipt.json")
    epoch_before = restored["epoch"]
    started = time.perf_counter_ns()
    replay = cwg.teach_write_shape_from_example(
        agent, SOURCE, request_text=REQUEST, seeds_dir=seed_dir,
        adequacy_receipt=receipt, require_adequacy_receipt=True)
    replay_ns = time.perf_counter_ns() - started
    after_replay = _state(agent)
    replay_saved = replay.get("teach", {}).get("saved")
    replay_persisted = replay.get("teach", {}).get("persisted")
    # Same Term and labels, but either source bytes or request differs: both
    # candidate identities must fail closed without changing the restored graph.
    stale_source = cwg.teach_write_shape_from_example(
        agent, SOURCE + "# altered\n", request_text=REQUEST, seeds_dir=seed_dir,
        adequacy_receipt=receipt, require_adequacy_receipt=True)
    stale_request = cwg.teach_write_shape_from_example(
        agent, SOURCE, request_text=REQUEST + " changed", seeds_dir=seed_dir,
        adequacy_receipt=receipt, require_adequacy_receipt=True)
    final_state = _state(agent)
    payload = {"repetition": rep, "phase": "reader", "pid": os.getpid(),
               "loaded_shape_count": len(restored["shapes"]),
               "loaded_seed_ids": loaded.get("loaded_seed_ids", []),
               "loaded_seed_count": int(loaded.get("loaded", 0) or 0), "boot_ns": boot_ns,
               "manifest_sha256": manifest_sha, "receipt_sha256": receipt_sha,
               "attrs_match": attrs_match, "restored": restored,
               "replay_ok": replay.get("ok"), "replay_saved": replay_saved,
               "replay_persisted": replay_persisted, "replay_ns": replay_ns,
               "after_replay": after_replay, "epoch_before": epoch_before,
               "stale_source_refused": stale_source.get("ok") is False,
               "stale_request_refused": stale_request.get("ok") is False,
               "final_state": final_state, "active_after": source_hashes()}
    payload["pass"] = (attrs_match and replay.get("ok") is True and replay_saved is False
                       and replay_persisted is True and len(after_replay["shapes"]) == 1
                       and after_replay["epoch"] == epoch_before
                       and payload["stale_source_refused"] and payload["stale_request_refused"]
                       and manifest_sha == expected["manifest_sha256"]
                       and receipt_sha == expected["receipt_sha256"]
                       and final_state == after_replay and payload["active_after"] == expected_active)
    return payload


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] == "--write-lock":
        LOCK.write_text(json.dumps(lock_payload(), indent=2, sort_keys=True) + "\n")
        print(LOCK); return
    lock = json.loads(LOCK.read_text())
    if lock_payload() != lock:
        raise SystemExit("source lock mismatch")
    if len(sys.argv) > 1 and sys.argv[1] in ("--writer", "--reader"):
        fn = writer if sys.argv[1] == "--writer" else reader
        print(json.dumps(fn(int(sys.argv[2]), Path(sys.argv[3]), lock["active"]), sort_keys=True))
        return
    workers = []
    for rep in range(1, REPETITIONS + 1):
        with tempfile.TemporaryDirectory(prefix="ocelot-adequacy-persist-") as temp:
            seed_dir = Path(temp)
            shutil.copy2(ROOT / "seeds/code_write_constructions.json",
                         seed_dir / "code_write_constructions.json")
            writer_out = subprocess.check_output([sys.executable, str(RUNNER), "--writer", str(rep), str(seed_dir)],
                                                 cwd=ROOT, text=True, env=os.environ.copy())
            writer_result = json.loads(writer_out)
            (seed_dir / ".trace" / "expected_writer.json").write_text(json.dumps(writer_result, sort_keys=True) + "\n")
            merged = seed_dir / "merged_seeds"
            merged.mkdir()
            for path in (ROOT / "seeds").glob("*.json"):
                if path.name == "code_write_constructions.json":
                    continue
                (merged / path.name).symlink_to(path.resolve())
            (merged / "code_write_constructions.json").symlink_to((seed_dir / "code_write_constructions.json").resolve())
            generated = ROOT / "seeds/generated"
            if generated.is_dir():
                (merged / "generated").symlink_to(generated.resolve(), target_is_directory=True)
            reader_out = subprocess.check_output([sys.executable, str(RUNNER), "--reader", str(rep), str(seed_dir)],
                                                 cwd=ROOT, text=True, env=os.environ.copy())
            reader_result = json.loads(reader_out)
            workers.append({"writer": writer_result, "reader": reader_result,
                            "pass": writer_result["pass"] and reader_result["pass"]})
    passed = all(w["pass"] for w in workers)
    capture = {"schema": "SubstrateAdequacyReceiptPersistenceV1Capture", "lock": lock,
               "post_lock": lock_payload(), "workers": workers, "passed": passed}
    RAW.parent.mkdir(parents=True, exist_ok=True)
    RAW.write_text(json.dumps(capture, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"passed": passed, "repetitions": len(workers),
                      "writer_boot_ms": [round(w["writer"]["boot_ns"]/1e6, 2) for w in workers],
                      "raw": str(RAW)}, indent=2))
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

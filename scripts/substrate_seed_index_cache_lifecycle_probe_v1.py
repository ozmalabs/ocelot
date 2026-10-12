#!/usr/bin/env python3
"""Probe seed-index cache invalidation/recovery and concurrent cold builders."""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "evaluation/reports/substrate_seed_index_cache_lifecycle_probe_v1_20260925.json"
SOURCES = [ROOT / "substrate/boot_all.py", ROOT / "substrate/world_adapter.py",
           ROOT / "substrate/seed_loader.py"]
CHILD = r'''import hashlib,json,os,sys
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds,_seed_index_cache_path
seed=sys.argv[1]
if os.environ.get("CACHE_MODE")=="clear":
 try:os.unlink(_seed_index_cache_path(seed))
 except FileNotFoundError:pass
a=WorldAdapter(seeds=()); r=load_all_seeds(a,seed_dir=seed)
def h(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(",",":")).encode()).hexdigest()
names=[str(x[1]) for x in sorted((x for x in a.inner.rule_access_sets() if x[2]),key=lambda x:int(x[0]))]
print(json.dumps({"cache_path":_seed_index_cache_path(seed),"load_order":r.get("order",[]),"failed":list(map(str,r.get("failed",[]))),"nodes":a.inner.node_count(),"edges":a.inner.edge_count(),"graph":h(a.inner.graph_to_dict()),"grammar":h(a.inner.grammar_to_json()),"rules":h(a.inner.export_rules()),"access":h(a.inner.rule_access_sets()),"rule_order":h(names)}))'''


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(seed: Path, mode: str) -> dict:
    env = {**os.environ, "PYTHONHASHSEED": "0",
           "PYTHONPATH": f"{ROOT}:{ROOT / 'runners/dsl/python'}:{ROOT / 'scripts'}",
           "CACHE_MODE": mode}
    output = subprocess.check_output([sys.executable, "-c", CHILD, str(seed)],
                                     cwd=ROOT, env=env, text=True)
    return json.loads(output.strip().splitlines()[-1])


def fingerprint(row: dict) -> dict:
    keys = ("load_order", "failed", "nodes", "edges", "graph", "grammar",
            "rules", "access", "rule_order")
    return {key: row[key] for key in keys}


def main() -> int:
    if len(sys.argv) < 2:
        raise SystemExit("pass immutable seed snapshot directory")
    source = Path(sys.argv[1]).resolve()
    before = {str(path.relative_to(ROOT)): sha(path) for path in SOURCES}
    temp = Path(tempfile.mkdtemp(prefix="ocelot_seed_lifecycle_v1_"))
    seed = temp / "seeds"
    shutil.copytree(source, seed, copy_function=os.link)
    try:
        good = run(seed, "clear")
        cache = Path(good["cache_path"])
        envelope = json.loads(cache.read_text())
        baseline = fingerprint(good)
        cases = {"known_good_warm": run(seed, "warm")}

        envelope["schema"] = "ocelot-seed-connectivity-index.v4"
        cache.write_text(json.dumps(envelope))
        cases["old_schema_rebuild"] = run(seed, "warm")

        cache.write_text("{truncated")
        cases["malformed_json_rebuild"] = run(seed, "warm")

        # Recreate a valid envelope from the known-good cache before corrupting
        # its payload digest. The stale-schema case already proved rebuilding.
        run(seed, "clear")
        envelope = json.loads(cache.read_text())
        envelope["payload_digest"] = "0" * 64
        cache.write_text(json.dumps(envelope))
        cases["bad_digest_rebuild"] = run(seed, "warm")

        cache.unlink(missing_ok=True)
        env = {**os.environ, "PYTHONHASHSEED": "0",
               "PYTHONPATH": f"{ROOT}:{ROOT / 'runners/dsl/python'}:{ROOT / 'scripts'}",
               "CACHE_MODE": "warm"}
        processes = [subprocess.Popen([sys.executable, "-c", CHILD, str(seed)],
                                      cwd=ROOT, env=env, stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE, text=True)
                     for _ in range(2)]
        concurrent = []
        for process in processes:
            stdout, stderr = process.communicate()
            if process.returncode:
                raise RuntimeError(f"concurrent builder failed: {stderr[-2000:]}")
            concurrent.append(json.loads(stdout.strip().splitlines()[-1]))
        cases["concurrent_cold_builders"] = concurrent
        final = run(seed, "warm")
        after = {str(path.relative_to(ROOT)): sha(path) for path in SOURCES}
        if before != after:
            raise RuntimeError("source changed during probe")

        recovery_rows = [cases[key] for key in (
            "known_good_warm", "old_schema_rebuild", "malformed_json_rebuild",
            "bad_digest_rebuild")]
        report = {
            "schema_version": 1,
            "probe_id": "seed-index-cache-lifecycle-v1-20260925",
            "source_hashes": before,
            "baseline": good,
            "cases": cases,
            "final_warm": final,
            "all_recovery_fingerprints_equal": all(fingerprint(row) == baseline
                                                    for row in recovery_rows),
            "both_concurrent_builders_equal": all(fingerprint(row) == baseline
                                                   for row in concurrent),
            "final_warm_equal": fingerprint(final) == baseline,
            "cache_exists_after": cache.exists(),
            "interpretation": (
                "Checks old-schema, malformed-JSON, bad-payload-digest recovery, and "
                "two simultaneous cold builders on an isolated hardlink copy. Full "
                "graph/grammar/rule/access/order fingerprints are compared."),
        }
        OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
        print(json.dumps({key: report[key] for key in (
            "probe_id", "all_recovery_fingerprints_equal",
            "both_concurrent_builders_equal", "final_warm_equal", "cache_exists_after")}))
    finally:
        shutil.rmtree(temp, ignore_errors=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

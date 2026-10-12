#!/usr/bin/env python3
"""Verify seed-byte changes invalidate the derived index without changing boot state."""
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
OUT = ROOT / "evaluation/reports/substrate_seed_index_source_invalidation_v1_20260925.json"
SOURCES = [ROOT / "substrate/boot_all.py", ROOT / "substrate/world_adapter.py",
           ROOT / "substrate/seed_loader.py"]
CHILD = r'''import hashlib,json,sys
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds,_seed_index_cache_path
seed=sys.argv[1]; a=WorldAdapter(seeds=()); r=load_all_seeds(a,seed_dir=seed)
def h(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(",",":")).encode()).hexdigest()
names=[str(x[1]) for x in sorted((x for x in a.inner.rule_access_sets() if x[2]),key=lambda x:int(x[0]))]
print(json.dumps({"cache_path":_seed_index_cache_path(seed),"load_order":r.get("order",[]),"failed":list(map(str,r.get("failed",[]))),"nodes":a.inner.node_count(),"edges":a.inner.edge_count(),"graph":h(a.inner.graph_to_dict()),"grammar":h(a.inner.grammar_to_json()),"rules":h(a.inner.export_rules()),"access":h(a.inner.rule_access_sets()),"rule_order":h(names)}))'''


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fingerprint(row: dict) -> dict:
    keys = ("load_order", "failed", "nodes", "edges", "graph", "grammar",
            "rules", "access", "rule_order")
    return {key: row[key] for key in keys}


def boot(seed: Path) -> dict:
    env = {**os.environ, "PYTHONHASHSEED": "0",
           "PYTHONPATH": f"{ROOT}:{ROOT / 'runners/dsl/python'}:{ROOT / 'scripts'}"}
    output = subprocess.check_output([sys.executable, "-c", CHILD, str(seed)],
                                     cwd=ROOT, env=env, text=True)
    return json.loads(output.strip().splitlines()[-1])


def main() -> int:
    if len(sys.argv) < 2:
        raise SystemExit("pass immutable seed snapshot directory")
    source = Path(sys.argv[1]).resolve()
    source_hashes = {str(path.relative_to(ROOT)): digest(path) for path in SOURCES}
    temp = Path(tempfile.mkdtemp(prefix="ocelot_seed_source_invalidation_"))
    seed = temp / "seeds"
    shutil.copytree(source, seed, copy_function=os.link)
    try:
        baseline = boot(seed)
        cache = Path(baseline["cache_path"])
        envelope_before = json.loads(cache.read_text())
        manifest = seed / "abandon_on_stuck.json"
        original = manifest.read_bytes()
        seed.chmod(0o700)
        manifest.chmod(0o600)
        manifest.unlink()
        manifest.write_bytes(original + b"\n")
        changed_digest = digest(manifest)
        changed = boot(seed)
        envelope_after = json.loads(cache.read_text())
        stable_sources = {str(path.relative_to(ROOT)): digest(path) for path in SOURCES}
        result = {
            "schema_version": 1,
            "probe_id": "seed-index-source-invalidation-v1-20260925",
            "source_hashes": source_hashes,
            "stable_source_hashes": source_hashes == stable_sources,
            "manifest_relative_path": manifest.name,
            "manifest_semantics_preserving_change": "append one JSON whitespace newline",
            "manifest_sha256_before": hashlib.sha256(original).hexdigest(),
            "manifest_sha256_after": changed_digest,
            "cache_source_digest_before": envelope_before.get("source_digest"),
            "cache_source_digest_after": envelope_after.get("source_digest"),
            "cache_digest_changed": envelope_before.get("source_digest") != envelope_after.get("source_digest"),
            "boot_fingerprint_unchanged": fingerprint(baseline) == fingerprint(changed),
            "baseline": baseline,
            "after_source_change": changed,
            "interpretation": "A byte-only valid-JSON source change invalidates the content-addressed index and rebuilds it while preserving the complete boot-state fingerprint.",
        }
        OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        print(json.dumps({key: result[key] for key in (
            "probe_id", "stable_source_hashes", "cache_digest_changed",
            "boot_fingerprint_unchanged")}))
    finally:
        shutil.rmtree(temp, ignore_errors=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

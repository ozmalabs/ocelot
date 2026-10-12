#!/usr/bin/env python3
"""Measure whether a cold or warm seed-index cache changes native rule order."""
from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "evaluation/reports/substrate_seed_index_cache_order_probe_20260925.json"
BOOT_SOURCES = [ROOT / "substrate/boot_all.py", ROOT / "substrate/world_adapter.py", ROOT / "substrate/seed_loader.py"]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def snapshot_digest(seed_dir: Path) -> str:
    rows = [(p.relative_to(seed_dir).as_posix(), sha(p)) for p in sorted(seed_dir.rglob("*.json"))]
    return hashlib.sha256(json.dumps(rows, separators=(",", ":")).encode()).hexdigest()


def main() -> int:
    seed_dir = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else None
    if seed_dir is None or not seed_dir.is_dir():
        raise SystemExit("pass the immutable baseline seed snapshot directory")
    source_hashes = {p.relative_to(ROOT).as_posix(): sha(p) for p in BOOT_SOURCES}
    content_digest = snapshot_digest(seed_dir)
    env = {**os.environ, "PYTHONHASHSEED": "0",
           "PYTHONPATH": f"{ROOT}:{ROOT / 'runners/dsl/python'}:{ROOT / 'scripts'}"}
    child = r'''
import hashlib,json,os,sys
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds,_seed_index_cache_path
from substrate_rs import _native
from domains import solver_dispatch as sd
from domains import problem_decomposition as pdec
from worlds import bigville_can_beliefs as bcb
seed_dir=sys.argv[1]
if os.environ.get('CACHE_MODE')=='cold':
 try:os.unlink(_seed_index_cache_path(seed_dir))
 except FileNotFoundError:pass
agent=WorldAdapter(seeds=());report=load_all_seeds(agent,seed_dir=seed_dir)
rows=sorted((row for row in agent.inner.rule_access_sets() if row[2]),key=lambda row:int(row[0]))
names=[str(row[1]) for row in rows]
ps={str(row[1]):int(row[0]) for row in rows if row[1] in {'ps_decode','ps_recognize','ps_residual','ps_mint','ps_redecode'}}
print(json.dumps({'rule_names':names,'rule_order_sha256':hashlib.sha256(json.dumps(names,separators=(',',':')).encode()).hexdigest(),'problem_shape_positions':ps,'load_order':report.get('order',[]),'failed_ids':[str(x) for x in report.get('failed',[])],'cache_path':_seed_index_cache_path(seed_dir)}))
'''
    rows = {}
    for mode in ("cold", "warm"):
        run_env = {**env, "CACHE_MODE": mode}
        raw = subprocess.check_output([sys.executable, "-c", child, str(seed_dir)], cwd=ROOT, env=run_env, text=True)
        rows[mode] = json.loads(raw.strip().splitlines()[-1])
    post_hashes = {p.relative_to(ROOT).as_posix(): sha(p) for p in BOOT_SOURCES}
    if source_hashes != post_hashes:
        raise SystemExit("seed-loader source changed during the cold/warm probe")
    cold, warm = rows["cold"], rows["warm"]
    result = {
        "schema_version": 1,
        "probe_id": "seed-index-cache-order-cold-warm-20260925",
        "seed_snapshot_dir": str(seed_dir),
        "seed_snapshot_digest": content_digest,
        "source_hashes": source_hashes,
        "python": sys.version,
        "platform": platform.platform(),
        "cold_warm_rule_order_equal": cold["rule_names"] == warm["rule_names"],
        "cold_warm_load_order_equal": cold["load_order"] == warm["load_order"],
        "cold_warm_problem_shape_positions_equal": cold["problem_shape_positions"] == warm["problem_shape_positions"],
        "rule_name_difference_count": sum(a != b for a, b in zip(cold["rule_names"], warm["rule_names"])),
        "first_seed_load_order_difference": next(((i, a, b) for i, (a, b) in enumerate(zip(cold["load_order"], warm["load_order"])) if a != b), None),
        "cold": cold,
        "warm": warm,
        "interpretation": "Cold and warm snapshots contain identical bytes. Any active rule-order difference comes from seed-index cache serialization/reconstruction or another loader-state effect, not corpus content.",
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"cold_warm_rule_order_equal": result["cold_warm_rule_order_equal"],
                      "cold_warm_load_order_equal": result["cold_warm_load_order_equal"],
                      "problem_shape_positions": {"cold": cold["problem_shape_positions"], "warm": warm["problem_shape_positions"]},
                      "output": str(OUT)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Fresh-process cProfile attribution for full-corpus seed boot."""
from __future__ import annotations

import cProfile
import hashlib
import json
import os
import pstats
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python"), str(ROOT / "scripts")]
CORPUS = ROOT / "evaluation/substrate_capability/problem_shape_eventized_rule_order_seed_corpus_lock_v1_7_20260925.json"
PREREG = ROOT / "docs/research/engine_substrate/SUBSTRATE_SEED_BOOT_PROFILE_PREREG_20260925.md"
OUT = ROOT / "evaluation/reports/substrate_seed_boot_profile_v1_20260925.json"
PART = ROOT / "evaluation/reports/substrate_seed_boot_profile_v1_partial_20260925.json"
CHILD = """
import cProfile,hashlib,json,pstats,sys,time
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
from substrate_rs import _native
a=WorldAdapter(seeds=()); p=cProfile.Profile(); w=time.perf_counter_ns(); c=time.process_time_ns(); p.enable(); r=load_all_seeds(a,seed_dir=sys.argv[1]); p.disable(); wall=time.perf_counter_ns()-w; cpu=time.process_time_ns()-c
def h(x): return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()
rows=sorted((x for x in a.inner.rule_access_sets() if x[2]),key=lambda x:int(x[0])); names=[str(x[1]) for x in rows]
st=pstats.Stats(p); wanted={'load_all_seeds','_read_seed_index','_seed_manifest_paths','_seed_sources_digest','_build_seed_index','_topo_order','load_seed_manifest','load'}
functions=[]
for (file,line,name),(cc,nc,tt,ct,callers) in st.stats.items():
 if name in wanted or 'load_seed_manifest' in name: functions.append({'file':file,'line':line,'function':name,'primitive_calls':cc,'calls':nc,'self_seconds':tt,'cumulative_seconds':ct})
top=sorted(functions,key=lambda x:x['cumulative_seconds'],reverse=True)
def fulltop():
 allrows=[{'file':f,'line':ln,'function':n,'primitive_calls':v[0],'calls':v[1],'self_seconds':v[2],'cumulative_seconds':v[3]} for (f,ln,n),v in st.stats.items()]
 return sorted(allrows,key=lambda x:x['cumulative_seconds'],reverse=True)[:40]
print(json.dumps({'wall_ns_profiled':wall,'cpu_ns_profiled':cpu,'report':r,'node_count':a.inner.node_count(),'edge_count':a.inner.edge_count(),'graph_sha256':h(a.inner.graph_to_dict()),'grammar_sha256':h(a.inner.grammar_to_json()),'rule_store_sha256':h(a.inner.export_rules()),'rule_access_sha256':h(a.inner.rule_access_sets()),'rule_order_sha256':h(names),'rule_order':names,'selected_functions':top,'top_cumulative':fulltop()}))
"""


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("pass an immutable seed snapshot directory")
    seed = Path(sys.argv[1]).resolve()
    corpus_lock = json.loads(CORPUS.read_text())
    if seed.is_symlink() or any(p.is_symlink() for p in seed.rglob("*.json")):
        raise SystemExit("seed snapshot must contain regular immutable files")
    for item in corpus_lock["manifests"]:
        if sha(seed / item["path"]) != item["sha256"]:
            raise SystemExit(f"snapshot manifest differs from corpus lock: {item['path']}")
    if OUT.exists() or PART.exists():
        raise SystemExit("refusing to overwrite a prior profile")
    from substrate.boot_all import _read_seed_index, _seed_index_cache_path
    cache = Path(_seed_index_cache_path(str(seed)))
    env = {**os.environ, "PYTHONHASHSEED": "0",
           "PYTHONPATH": f"{ROOT}:{ROOT / 'runners/dsl/python'}:{ROOT / 'scripts'}"}
    locked_paths = ('substrate/boot_all.py','substrate/world_adapter.py','substrate/seed_loader.py')
    source_hashes_before = {p: sha(ROOT / p) for p in locked_paths}
    runner_hash_before = sha(Path(__file__))
    prereg_hash_before = sha(PREREG)
    arms = []
    for mode in ("cold", "warm", "warm", "cold"):
        if mode == "cold":
            cache.unlink(missing_ok=True)
            before = None
        else:
            _read_seed_index(str(seed))
            before = sha(cache)
        cmd = [sys.executable, "-c", CHILD, str(seed)]
        proc = subprocess.run(cmd, cwd=ROOT, env=env, text=True, capture_output=True, timeout=900)
        if proc.returncode:
            raise RuntimeError(f"{mode} profile worker failed: {proc.stderr[-2000:]}")
        row = json.loads(proc.stdout.strip().splitlines()[-1])
        after = sha(cache)
        if before is not None and before != after:
            raise RuntimeError("warm cache bytes changed during profiled load")
        arms.append({'cache_mode': mode, 'cache_sha256_before': before,
                     'cache_sha256_after': after, 'profile': row})
        PART.write_text(json.dumps({'arms': arms}, indent=2, sort_keys=True) + '\n')
        print(json.dumps({'cache_mode': mode, 'profiled_wall_ns': row['wall_ns_profiled'],
                          'nodes': row['node_count'], 'edges': row['edge_count']}), flush=True)
    state_keys = ('node_count','edge_count','graph_sha256','grammar_sha256',
                  'rule_store_sha256','rule_access_sha256','rule_order_sha256','rule_order','report')
    fingerprints = [{k:a['profile'][k] for k in state_keys} for a in arms]
    source_hashes_after = {p: sha(ROOT / p) for p in locked_paths}
    runner_hash_after = sha(Path(__file__))
    prereg_hash_after = sha(PREREG)
    if (source_hashes_before != source_hashes_after or runner_hash_before != runner_hash_after
            or prereg_hash_before != prereg_hash_after):
        raise RuntimeError('loader/runner sources changed during the probe')
    result = {'schema_version':1,'probe_id':'seed-boot-profile-v1-20260925',
              'corpus_lock_sha256':sha(CORPUS),'corpus_digest':corpus_lock['corpus_digest'],
              'source_hashes_before':source_hashes_before,'source_hashes_after':source_hashes_after,
              'runner_sha256':runner_hash_after,
              'preregistration_sha256':prereg_hash_after,
              'arms':arms,'all_boot_states_equal':all(x==fingerprints[0] for x in fingerprints),
              'interpretation':'cProfile attribution on four fresh profiled boots; profiler time includes instrumentation and is not production latency.'}
    OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n'); PART.unlink(missing_ok=True)
    print(json.dumps({'all_boot_states_equal':result['all_boot_states_equal'],'output':str(OUT)}))
    return 0 if result['all_boot_states_equal'] else 2


if __name__ == '__main__':
    raise SystemExit(main())

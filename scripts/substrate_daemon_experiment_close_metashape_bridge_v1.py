#!/usr/bin/env python3
"""Measure the daemon close-action path into the seeded MetaShape learner."""
from __future__ import annotations
import hashlib,json,os,platform,sys,time
from pathlib import Path
os.environ['OZMA_SEED_PERSIST_DISABLED']='1'
from domains.engine_provenance import engine_preamble,provenance_line
engine_preamble()
from substrate.boot_all import load_all_seeds
from substrate.world_adapter import WorldAdapter
from scripts.jabberwock_daemon import _close_tick
from substrate_rs import _native
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'evaluation/reports/substrate_daemon_experiment_close_metashape_bridge_v1_20260926.json'
LOCK=ROOT/'evaluation/substrate_capability/daemon_experiment_close_metashape_bridge_v1_lock_20260926.json'
SOURCES=['scripts/substrate_daemon_experiment_close_metashape_bridge_v1.py','scripts/jabberwock_daemon.py','substrate/boot_all.py','substrate/world_adapter.py','domains/reflective_faculty.py','domains/teach.py','domains/meta_shape.py','seeds/meta_shape_growth.json','seeds/shape_vocabulary.json','domains/engine_provenance.py','runners/dsl/python/substrate_rs/_native.build.json']
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def main():
    lock=json.loads(LOCK.read_text())
    if {p:sha(ROOT/p) for p in lock['source_sha256']}!=lock['source_sha256']:
        raise RuntimeError('locked source digest mismatch; re-lock before execution')
    adapter=WorldAdapter(seeds=())
    report=load_all_seeds(adapter,seed_ids={'meta_shape_growth'})
    before_obs=set(adapter.s.nodes('ShapeObservation'));before_meta=set(adapter.s.nodes('MetaShape'))
    experiments=[]
    for axis in ('bridge_a','bridge_b'):
        experiments.append(adapter.s.add_node('Experiment',{
            'status':'done','outcome':'supported','conclusion_ready':True,'taught':False,
            'hypothesis':'','game':'','run_dir':'','axis_tag':axis}))
    started=time.perf_counter_ns();_close_tick(adapter);elapsed=(time.perf_counter_ns()-started)/1e6
    observations=[{'id':str(n),'attrs':adapter.s.node(n)['attrs']} for n in adapter.s.nodes('ShapeObservation') if n not in before_obs]
    metas=[{'id':str(n),'attrs':adapter.s.node(n)['attrs']} for n in adapter.s.nodes('MetaShape') if n not in before_meta]
    raw={'schema_version':1,'run_id':'substrate-daemon-experiment-close-metashape-bridge-v1-20260926',
         'engine':provenance_line(),'python':sys.version,'platform':platform.platform(),
         'native_extension_path':str(Path(_native.__file__).resolve()),'native_extension_sha256':sha(_native.__file__),
         'source_sha256':{p:sha(ROOT/p) for p in SOURCES},
         'protocol_sha256':sha(ROOT/'docs/research/engine_substrate/SUBSTRATE_DAEMON_EXPERIMENT_CLOSE_METASHAPE_BRIDGE_PREREG_20260926.md'),
         'lock_sha256':sha(LOCK),'seed_load':{'loaded':report.get('loaded'),'total':report.get('total'),'failed':report.get('failed',[]),'selected_order':report.get('order')},
         'persistence_disabled':os.environ.get('OZMA_SEED_PERSIST_DISABLED')=='1',
         'experiments':[{'id':str(n),'attrs':adapter.s.node(n)['attrs']} for n in experiments],
         'added_observations':observations,'added_meta_shapes':metas,
         'taught_hints':[{'id':str(n),'attrs':adapter.s.node(n)['attrs']} for n in adapter.s.nodes('TaughtHint')],
         'elapsed_ms':elapsed}
    out=ROOT/'evaluation/reports/substrate_daemon_experiment_close_metashape_bridge_v1_20260926.json'
    out.write_text(json.dumps(raw,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'output':str(out),'seed_load':raw['seed_load'],'experiment_taught':[x['attrs'].get('taught') for x in raw['experiments']],
                      'observation_statuses':[x['attrs'].get('status') for x in observations],
                      'added_meta_shapes':[x['attrs'].get('name') for x in metas],'elapsed_ms':elapsed},indent=2))
if __name__=='__main__':main()

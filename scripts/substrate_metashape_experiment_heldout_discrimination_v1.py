#!/usr/bin/env python3
"""Test held-out reuse and a fixed-field negative control for a minted MetaShape."""
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
OUT=ROOT/'evaluation/reports/substrate_metashape_experiment_heldout_discrimination_v1_20260926.json'
LOCK=ROOT/'evaluation/substrate_capability/metashape_experiment_heldout_discrimination_v1_lock_20260926.json'
SOURCES=['scripts/substrate_metashape_experiment_heldout_discrimination_v1.py','scripts/jabberwock_daemon.py','substrate/boot_all.py','substrate/world_adapter.py','domains/reflective_faculty.py','domains/teach.py','domains/meta_shape.py','seeds/meta_shape_growth.json','seeds/shape_vocabulary.json','domains/engine_provenance.py','runners/dsl/python/substrate_rs/_native.build.json']
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def add_experiment(adapter,axis,outcome):
    return adapter.s.add_node('Experiment',{'status':'done','outcome':outcome,'conclusion_ready':True,'taught':False,'hypothesis':'','game':'','run_dir':'','axis_tag':axis})
def main():
    lock=json.loads(LOCK.read_text())
    if {p:sha(ROOT/p) for p in lock['source_sha256']}!=lock['source_sha256']:
        raise RuntimeError('locked source digest mismatch; re-lock before execution')
    adapter=WorldAdapter(seeds=()); load=load_all_seeds(adapter,seed_ids={'meta_shape_growth'})
    base_shapes=set(adapter.s.nodes('MetaShape'));base_obs=set(adapter.s.nodes('ShapeObservation'))
    phases=[]
    def close_phase(label,exps):
        old_obs=set(adapter.s.nodes('ShapeObservation'));old_shapes=set(adapter.s.nodes('MetaShape'))
        start=time.perf_counter_ns();_close_tick(adapter);elapsed=(time.perf_counter_ns()-start)/1e6
        new_obs=[{'id':str(n),'attrs':adapter.s.node(n)['attrs']} for n in adapter.s.nodes('ShapeObservation') if n not in old_obs]
        new_shapes=[{'id':str(n),'attrs':adapter.s.node(n)['attrs']} for n in adapter.s.nodes('MetaShape') if n not in old_shapes]
        phases.append({'phase':label,'experiment_ids':[str(x) for x in exps],
                       'experiments':[{'id':str(x),'attrs':adapter.s.node(x)['attrs']} for x in exps],
                       'observations':new_obs,'new_meta_shapes':new_shapes,'elapsed_ms':elapsed})
    training=[add_experiment(adapter,'bridge_a','supported'),add_experiment(adapter,'bridge_b','supported')]
    close_phase('training_pair',training)
    minted=[x for p in phases for x in p['new_meta_shapes']]
    minted_name=minted[0]['attrs'].get('name') if minted else None
    positive=add_experiment(adapter,'bridge_c','supported');close_phase('positive_holdout',[positive])
    negative=add_experiment(adapter,'bridge_d','refuted');close_phase('negative_control',[negative])
    raw={'schema_version':1,'run_id':'substrate-metashape-experiment-heldout-discrimination-v1-20260926',
         'engine':provenance_line(),'python':sys.version,'platform':platform.platform(),
         'native_extension_path':str(Path(_native.__file__).resolve()),'native_extension_sha256':sha(_native.__file__),
         'source_sha256':{p:sha(ROOT/p) for p in SOURCES},
         'protocol_sha256':sha(ROOT/'docs/research/engine_substrate/SUBSTRATE_METASHAPE_EXPERIMENT_HELDOUT_DISCRIMINATION_PREREG_20260926.md'),
         'lock_sha256':sha(LOCK),'seed_load':{'loaded':load.get('loaded'),'total':load.get('total'),'failed':load.get('failed',[]),'order':load.get('order')},
         'persistence_disabled':os.environ.get('OZMA_SEED_PERSIST_DISABLED')=='1','minted_training_shape':minted_name,
         'phases':phases,'baseline_meta_shape_count':len(base_shapes),'baseline_observation_count':len(base_obs)}
    OUT.write_text(json.dumps(raw,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'output':str(OUT),'seed_load':raw['seed_load'],'minted_training_shape':minted_name,
                      'phases':[{'phase':p['phase'],'observation_statuses':[x['attrs'].get('status') for x in p['observations']],
                                 'covered_by':[x['attrs'].get('covered_by') for x in p['observations']],
                                 'new_meta_shapes':[x['attrs'].get('name') for x in p['new_meta_shapes']]} for p in phases]},indent=2))
if __name__=='__main__':main()

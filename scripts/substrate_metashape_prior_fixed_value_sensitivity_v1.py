#!/usr/bin/env python3
"""Measure rung-specific MetaShape/prior responses to locked relation controls."""
from __future__ import annotations
import hashlib,json,os,platform,sys,tempfile,time
from pathlib import Path
os.environ['OZMA_SEED_PERSIST_DISABLED']='1'
from domains.engine_provenance import engine_preamble,provenance_line
engine_preamble()
from domains.teach import teach
from substrate.boot_all import load_all_seeds
from substrate.world_adapter import WorldAdapter
from substrate_rs import _native
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'evaluation/reports/substrate_metashape_prior_fixed_value_sensitivity_v1_20260926.json'
LOCK=ROOT/'evaluation/substrate_capability/metashape_prior_fixed_value_sensitivity_v1_lock_20260926.json'
SOURCES=['scripts/substrate_metashape_prior_fixed_value_sensitivity_v1.py','substrate/boot_all.py','substrate/world_adapter.py','domains/teach.py','domains/meta_shape.py','seeds/meta_shape_growth.json','seeds/shape_vocabulary.json','domains/engine_provenance.py','runners/dsl/python/substrate_rs/_native.build.json']
FAMILIES=[
 {'type':'FrameBindingProbe','fixed_key':'count','fixed':7,'variable_a':'role','variable_b':'interface','train':[('source','north'),('target','south')],'positive':('relay','east'),'negative_values':[9,10,-1,0]},
 {'type':'MotionRuleProbe','fixed_key':'order','fixed':1,'variable_a':'mode','variable_b':'axis','train':[('translate','x'),('reflect','y')],'positive':('rotate','z'),'negative_values':[2,3,0,-1]},
 {'type':'ResourceTransferProbe','fixed_key':'status','fixed':'complete','variable_a':'source','variable_b':'target','train':[('r1','r2'),('r3','r4')],'positive':('r5','r6'),'negative_values':['failed','pending','unavailable','unknown']},
 {'type':'GoalTraceProbe','fixed_key':'terminal','fixed':False,'variable_a':'phase','variable_b':'channel','train':[('analysis','symbolic'),('planning','embodied')],'positive':('acting','external'),'negative_values':[True,'unknown','done',1]},
]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def submit(adapter,item_type,item_attrs,temp):
 before=set(adapter.s.nodes('ShapeObservation'));before_shapes=set(adapter.s.nodes('MetaShape'));start=time.perf_counter_ns()
 rec=teach(adapter,item_type,item_attrs,category='prior_sensitivity_probe',seeds_dir=temp)
 elapsed=(time.perf_counter_ns()-start)/1e6;added=[n for n in adapter.s.nodes('ShapeObservation') if n not in before]
 if len(added)!=1:raise RuntimeError(f'expected one observation, got {len(added)} for {item_type}')
 n=added[0]
 minted=[{'id':str(x),'attrs':adapter.s.node(x)['attrs']} for x in adapter.s.nodes('MetaShape') if x not in before_shapes]
 return {'item_type':item_type,'item_attrs':item_attrs,'observation_id':str(n),'observation':adapter.s.node(n)['attrs'],'new_meta_shapes':minted,'teach_saved':rec.get('saved'),'teach_persisted':rec.get('persisted'),'elapsed_ms':elapsed}
def item_attrs(f,a,b,fixed_marker='default'):
 d={f['variable_a']:a,f['variable_b']:b}
 if fixed_marker!='missing':d[f['fixed_key']]=f['fixed'] if fixed_marker=='default' else fixed_marker
 return d
def main():
 lock=json.loads(LOCK.read_text())
 if {p:sha(ROOT/p) for p in lock['source_sha256']}!=lock['source_sha256']:raise RuntimeError('locked source digest mismatch')
 adapter=WorldAdapter(seeds=());load=load_all_seeds(adapter,seed_ids={'meta_shape_growth'})
 if load.get('failed'):raise RuntimeError(f'seed closure failures: {load["failed"]}')
 phases=[];shape_by_family={}
 with tempfile.TemporaryDirectory(prefix='metashape-prior-sweep-') as td:
  for f in FAMILIES:
   old=set(adapter.s.nodes('MetaShape'));obs=[]
   for a,b in f['train']:obs.append(submit(adapter,f['type'],item_attrs(f,a,b),td))
   new=[n for n in adapter.s.nodes('MetaShape') if n not in old]
   shapes=[{'id':str(n),'attrs':adapter.s.node(n)['attrs']} for n in new]
   shape_by_family[f['type']]=shapes[0]['attrs'].get('name') if len(shapes)==1 else None
   phases.append({'kind':'training','family':f['type'],'target_shape':shape_by_family[f['type']],'observations':obs,'new_meta_shapes':shapes})
  for f in FAMILIES:
   obs=submit(adapter,f['type'],item_attrs(f,*f['positive']),td)
   phases.append({'kind':'positive','family':f['type'],'target_shape':shape_by_family[f['type']],'observations':[obs],'new_meta_shapes':obs['new_meta_shapes']})
  for f in FAMILIES:
   a,b=f['positive']
   for value in f['negative_values']:
    obs=submit(adapter,f['type'],item_attrs(f,a,b,value),td)
    phases.append({'kind':'fixed_value_change','family':f['type'],'target_shape':shape_by_family[f['type']],'control_value':value,'observations':[obs],'new_meta_shapes':obs['new_meta_shapes']})
   obs=submit(adapter,f['type'],item_attrs(f,a,b,'missing'),td)
   phases.append({'kind':'fixed_field_omitted','family':f['type'],'target_shape':shape_by_family[f['type']],'observations':[obs],'new_meta_shapes':obs['new_meta_shapes']})
   extra=item_attrs(f,a,b);extra['unexpected_slot']='noise'
   obs=submit(adapter,f['type'],extra,td)
   phases.append({'kind':'extra_field','family':f['type'],'target_shape':shape_by_family[f['type']],'observations':[obs],'new_meta_shapes':obs['new_meta_shapes']})
   distractor=f['type'].replace('Probe','Distractor')
   obs=submit(adapter,distractor,item_attrs(f,a,b),td)
   phases.append({'kind':'type_changed','family':f['type'],'control_type':distractor,'target_shape':shape_by_family[f['type']],'observations':[obs],'new_meta_shapes':obs['new_meta_shapes']})
 raw={'schema_version':1,'run_id':'substrate-metashape-prior-fixed-value-sensitivity-v1-20260926',
      'engine':provenance_line(),'python':sys.version,'platform':platform.platform(),
      'native_extension_path':str(Path(_native.__file__).resolve()),'native_extension_sha256':sha(_native.__file__),
      'source_sha256':{p:sha(ROOT/p) for p in SOURCES},
      'protocol_sha256':sha(ROOT/'docs/research/engine_substrate/SUBSTRATE_METASHAPE_PRIOR_FIXED_VALUE_SENSITIVITY_V1_PREREG_20260926.md'),
      'lock_sha256':sha(LOCK),'seed_load':{'loaded':load.get('loaded'),'total':load.get('total'),'failed':load.get('failed',[]),'order':load.get('order')},
      'persistence_disabled':os.environ.get('OZMA_SEED_PERSIST_DISABLED')=='1','shape_by_family':shape_by_family,'phases':phases}
 OUT.write_text(json.dumps(raw,indent=2,sort_keys=True)+'\n')
 print(json.dumps({'output':str(OUT),'families':shape_by_family,'case_count':sum(len(p['observations']) for p in phases),
                   'outcomes':[{'kind':p['kind'],'family':p['family'],'status':p['observations'][-1]['observation'].get('status'),'covered_by':p['observations'][-1]['observation'].get('covered_by'),'target':p['target_shape']} for p in phases]},indent=2))
if __name__=='__main__':main()

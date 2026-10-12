#!/usr/bin/env python3
"""Run the locked four-schema MetaShape positive/negative transfer panel."""
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
OUT=ROOT/'evaluation/reports/substrate_metashape_multischema_transfer_panel_v1_1_20260926.json'
LOCK=ROOT/'evaluation/substrate_capability/metashape_multischema_transfer_panel_v1_1_lock_20260926.json'
SOURCES=['scripts/substrate_metashape_multischema_transfer_panel_v1_1.py','substrate/boot_all.py','substrate/world_adapter.py','domains/teach.py','domains/meta_shape.py','seeds/meta_shape_growth.json','seeds/shape_vocabulary.json','domains/engine_provenance.py','runners/dsl/python/substrate_rs/_native.build.json']
FAMILIES=[
 {'type':'FrameBindingProbe','fixed_key':'count','fixed':7,'variable_a':'role','variable_b':'interface','train':[('source','north'),('target','south')],'positive':('relay','east'),'negative':('relay','east',9)},
 {'type':'MotionRuleProbe','fixed_key':'order','fixed':1,'variable_a':'mode','variable_b':'axis','train':[('translate','x'),('reflect','y')],'positive':('rotate','z'),'negative':('rotate','z',2)},
 {'type':'ResourceTransferProbe','fixed_key':'status','fixed':'complete','variable_a':'source','variable_b':'target','train':[('r1','r2'),('r3','r4')],'positive':('r5','r6'),'negative':('r5','r6','failed')},
 {'type':'GoalTraceProbe','fixed_key':'terminal','fixed':False,'variable_a':'phase','variable_b':'channel','train':[('analysis','symbolic'),('planning','embodied')],'positive':('acting','external'),'negative':('acting','external',True)},
]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def attrs(f,a,b,fixed=None):
 d={f['variable_a']:a,f['variable_b']:b,f['fixed_key']:f['fixed'] if fixed is None else fixed};return d
def signature_teach(adapter,f,a,b,temp,fixed=None):
 before=set(adapter.s.nodes('ShapeObservation'));start=time.perf_counter_ns()
 rec=teach(adapter,f['type'],attrs(f,a,b,fixed),category='multischema_probe',seeds_dir=temp)
 elapsed=(time.perf_counter_ns()-start)/1e6
 added=[n for n in adapter.s.nodes('ShapeObservation') if n not in before]
 if len(added)!=1:raise RuntimeError(f'expected one observation for {f["type"]}, got {len(added)}')
 n=added[0]
 return {'item_type':f['type'],'observation_id':str(n),'attrs':adapter.s.node(n)['attrs'],'teach_saved':rec.get('saved'),'teach_persisted':rec.get('persisted'),'elapsed_ms':elapsed}
def main():
 lock=json.loads(LOCK.read_text())
 if {p:sha(ROOT/p) for p in lock['source_sha256']}!=lock['source_sha256']:raise RuntimeError('locked source digest mismatch')
 adapter=WorldAdapter(seeds=());report=load_all_seeds(adapter,seed_ids={'meta_shape_growth'})
 if report.get('failed'):raise RuntimeError(f'seed dependency closure failed: {report["failed"]}')
 before_shapes=set(adapter.s.nodes('MetaShape'));phases=[];shape_by_family={}
 with tempfile.TemporaryDirectory(prefix='metashape-multischema-') as td:
  for f in FAMILIES:
   old=set(adapter.s.nodes('MetaShape'));observations=[]
   for a,b in f['train']:observations.append(signature_teach(adapter,f,a,b,td))
   new=[n for n in adapter.s.nodes('MetaShape') if n not in old]
   shape_rows=[{'id':str(n),'attrs':adapter.s.node(n)['attrs']} for n in new]
   shape_by_family[f['type']]=shape_rows[0]['attrs'].get('name') if len(shape_rows)==1 else None
   phases.append({'phase':'training','item_type':f['type'],'observations':observations,'new_meta_shapes':shape_rows})
  for f in FAMILIES:
   o=signature_teach(adapter,f,*f['positive'],td)
   phases.append({'phase':'positive_holdout','item_type':f['type'],'observations':[o],'new_meta_shapes':[]})
  for f in FAMILIES:
   a,b,value=f['negative'];o=signature_teach(adapter,f,a,b,td,fixed=value)
   phases.append({'phase':'negative_control','item_type':f['type'],'observations':[o],'new_meta_shapes':[]})
 raw={'schema_version':1,'run_id':'substrate-metashape-multischema-transfer-panel-v1.1-20260926',
      'engine':provenance_line(),'python':sys.version,'platform':platform.platform(),
      'native_extension_path':str(Path(_native.__file__).resolve()),'native_extension_sha256':sha(_native.__file__),
      'source_sha256':{p:sha(ROOT/p) for p in SOURCES},
      'protocol_sha256':sha(ROOT/'docs/research/engine_substrate/SUBSTRATE_METASHAPE_MULTISCHEMA_TRANSFER_PANEL_V1_1_AMENDMENT_20260926.md'),
      'lock_sha256':sha(LOCK),'seed_load':{'loaded':report.get('loaded'),'total':report.get('total'),'failed':report.get('failed',[]),'order':report.get('order')},
      'persistence_disabled':os.environ.get('OZMA_SEED_PERSIST_DISABLED')=='1','shape_by_family':shape_by_family,'baseline_meta_shape_count':len(before_shapes),'phases':phases}
 OUT.write_text(json.dumps(raw,indent=2,sort_keys=True)+'\n')
 print(json.dumps({'output':str(OUT),'shape_by_family':shape_by_family,'phases':[{'phase':p['phase'],'type':p['item_type'],'status':p['observations'][0]['attrs'].get('status'),'covered_by':p['observations'][0]['attrs'].get('covered_by'),'new_shapes':[s['attrs'].get('name') for s in p['new_meta_shapes']]} for p in phases]},indent=2))
if __name__=='__main__':main()

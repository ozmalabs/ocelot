#!/usr/bin/env python3
"""Paired pre/post-growth evaluation of the actual teach filing classifier."""
from __future__ import annotations
import hashlib,json,os,platform,sys,tempfile,time
from pathlib import Path
os.environ['OZMA_SEED_PERSIST_DISABLED']='1'
from domains.engine_provenance import engine_preamble,provenance_line
engine_preamble()
from domains.teach import categorise_by_shape,teach
from substrate.boot_all import load_all_seeds
from substrate.world_adapter import WorldAdapter
from substrate_rs import _native
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'evaluation/reports/substrate_metashape_categorisation_utility_v1_20260926.json'
LOCK=ROOT/'evaluation/substrate_capability/metashape_categorisation_utility_v1_lock_20260926.json'
SOURCES=['scripts/substrate_metashape_categorisation_utility_v1.py','substrate/boot_all.py','substrate/world_adapter.py','domains/teach.py','domains/meta_shape.py','seeds/meta_shape_growth.json','seeds/shape_vocabulary.json','domains/engine_provenance.py','runners/dsl/python/substrate_rs/_native.build.json']
FAMILIES=[
 {'type':'FrameBindingProbe','fixed_key':'count','fixed':7,'variable_a':'role','variable_b':'interface','train':[('source','north'),('target','south')],'positive':('relay','east'),'negative':9},
 {'type':'MotionRuleProbe','fixed_key':'order','fixed':1,'variable_a':'mode','variable_b':'axis','train':[('translate','x'),('reflect','y')],'positive':('rotate','z'),'negative':2},
 {'type':'ResourceTransferProbe','fixed_key':'status','fixed':'complete','variable_a':'source','variable_b':'target','train':[('r1','r2'),('r3','r4')],'positive':('r5','r6'),'negative':'failed'},
 {'type':'GoalTraceProbe','fixed_key':'terminal','fixed':False,'variable_a':'phase','variable_b':'channel','train':[('analysis','symbolic'),('planning','embodied')],'positive':('acting','external'),'negative':True},
]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def attrs(f,a,b,fixed='default',extra=False):
 d={f['variable_a']:a,f['variable_b']:b}
 if fixed!='missing':d[f['fixed_key']]=f['fixed'] if fixed=='default' else fixed
 if extra:d['unexpected_slot']='noise'
 return d
def classify(adapter,item_type,item_attrs):
 start=time.perf_counter_ns();value=categorise_by_shape(adapter,item_type,item_attrs)
 return {'prediction':None if value is None else str(value),'elapsed_ms':(time.perf_counter_ns()-start)/1e6}
def main():
 lock=json.loads(LOCK.read_text())
 if {p:sha(ROOT/p) for p in lock['source_sha256']}!=lock['source_sha256']:raise RuntimeError('locked source digest mismatch')
 adapter=WorldAdapter(seeds=());load=load_all_seeds(adapter,seed_ids={'meta_shape_growth'})
 if load.get('failed'):raise RuntimeError(f'seed dependency closure failed: {load["failed"]}')
 query_rows=[];counts_before={t:len(list(adapter.s.nodes(t))) for t in ('ShapeObservation','MetaShape')}
 for f in FAMILIES:
  a,b=f['positive'];family=f['type'];gold_shape='spatial_dynamics' if family=='MotionRuleProbe' else None
  query_specs=[('positive',family,attrs(f,a,b),None),
               ('fixed_value_change',family,attrs(f,a,b,f['negative']),None),
               ('fixed_field_omitted',family,attrs(f,a,b,'missing'),None),
               ('extra_field',family,attrs(f,a,b,extra=True),None),
               ('type_changed',family.replace('Probe','Distractor'),attrs(f,a,b),None)]
  for kind,item_type,item_attrs,_ in query_specs:
   if kind=='positive':gold=None if family=='MotionRuleProbe' else 'family_shape'
   elif kind=='extra_field':gold=None if family=='MotionRuleProbe' else 'family_shape'
   elif family=='MotionRuleProbe' and kind in ('fixed_value_change','fixed_field_omitted'):gold='spatial_dynamics'
   else:gold=None
   query_rows.append({'family':family,'query_kind':kind,'item_type':item_type,'attrs':item_attrs,'gold_label':gold,'gold_label_mode':'family_shape' if gold=='family_shape' else 'literal_or_none'})
 # Evaluate all baseline queries before any teaching/minting.
 for row in query_rows:row['baseline']=classify(adapter,row['item_type'],row['attrs'])
 shape_by_family={}
 with tempfile.TemporaryDirectory(prefix='metashape-categorise-') as td:
  for f in FAMILIES:
   old=set(adapter.s.nodes('MetaShape'))
   for a,b in f['train']:
    teach(adapter,f['type'],attrs(f,a,b),category='categorisation_training',seeds_dir=td)
   added=[n for n in adapter.s.nodes('MetaShape') if n not in old]
   shape_by_family[f['type']]=adapter.s.node(added[0])['attrs'].get('name') if len(added)==1 else None
 # Resolve gold family labels only after locked training's new IDs are present.
 for row in query_rows:
  if row['gold_label_mode']=='family_shape':row['gold_label']=shape_by_family[row['family']]
 counts_after_training={t:len(list(adapter.s.nodes(t))) for t in counts_before}
 for row in query_rows:
  row['trained']=classify(adapter,row['item_type'],row['attrs'])
 counts_after={t:len(list(adapter.s.nodes(t))) for t in counts_before}
 raw={'schema_version':1,'run_id':'substrate-metashape-categorisation-utility-v1-20260926',
      'engine':provenance_line(),'python':sys.version,'platform':platform.platform(),
      'native_extension_path':str(Path(_native.__file__).resolve()),'native_extension_sha256':sha(_native.__file__),
      'source_sha256':{p:sha(ROOT/p) for p in SOURCES},
      'protocol_sha256':sha(ROOT/'docs/research/engine_substrate/SUBSTRATE_METASHAPE_CATEGORISATION_UTILITY_PREREG_20260926.md'),
      'lock_sha256':sha(LOCK),'seed_load':{'loaded':load.get('loaded'),'total':load.get('total'),'failed':load.get('failed',[]),'order':load.get('order')},
      'persistence_disabled':os.environ.get('OZMA_SEED_PERSIST_DISABLED')=='1','shape_by_family':shape_by_family,
      'query_graph_counts_before':counts_before,'query_graph_counts_after_training':counts_after_training,'query_graph_counts_after':counts_after,'queries':query_rows}
 OUT.write_text(json.dumps(raw,indent=2,sort_keys=True)+'\n')
 print(json.dumps({'output':str(OUT),'shape_by_family':shape_by_family,'queries':len(query_rows),
                   'decisions':[{'family':q['family'],'kind':q['query_kind'],'gold':q['gold_label'],'baseline':q['baseline']['prediction'],'trained':q['trained']['prediction']} for q in query_rows]},indent=2))
if __name__=='__main__':main()

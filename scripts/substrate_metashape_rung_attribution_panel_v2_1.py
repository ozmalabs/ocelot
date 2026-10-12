#!/usr/bin/env python3
"""Fresh-process, source-locked MetaShape rung attribution panel v2."""
from __future__ import annotations
import hashlib, importlib.util, json, os, platform, resource, subprocess, sys, tempfile, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python'),str(ROOT/'scripts')]
PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_METASHAPE_RUNG_ATTRIBUTION_PANEL_V2_PREREG_20260927.md'
AMENDMENT=ROOT/'docs/research/engine_substrate/SUBSTRATE_METASHAPE_RUNG_ATTRIBUTION_PANEL_V2_1_AMENDMENT_20260927.md'
LOCK=ROOT/'evaluation/substrate_capability/metashape_rung_attribution_panel_v2_1_lock_20260927.json'
OUT=ROOT/'evaluation/reports/metashape_rung_attribution_panel_v2_1_20260927.json'
ANALYZER=ROOT/'scripts/analyze_substrate_metashape_rung_attribution_panel_v2_1.py'
HELPER=ROOT/'scripts/measurement_provenance.py'
FAMILIES=[
 {'type':'FrameBindingProbe','fixed_key':'count','fixed':7,'variable_a':'role','variable_b':'interface','train':[('source','north'),('target','south')],'positive':('relay','east'),'negative_fixed':9,'negative_type':'ill-typed'},
 {'type':'MotionRuleProbe','fixed_key':'order','fixed':1,'variable_a':'mode','variable_b':'axis','train':[('translate','x'),('reflect','y')],'positive':('rotate','z'),'negative_fixed':2,'negative_type':'ill-typed'},
 {'type':'ResourceTransferProbe','fixed_key':'status','fixed':'complete','variable_a':'source','variable_b':'target','train':[('r1','r2'),('r3','r4')],'positive':('r5','r6'),'negative_fixed':'failed','negative_type':True},
 {'type':'GoalTraceProbe','fixed_key':'terminal','fixed':False,'variable_a':'phase','variable_b':'channel','train':[('analysis','symbolic'),('planning','embodied')],'positive':('acting','external'),'negative_fixed':True,'negative_type':'not-boolean'},
]
SCHEDULE=[(i,r) for i in range(len(FAMILIES)) for r in range(2)]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def tree_hashes(folder,suffixes=None):
 out={}
 for p in sorted(folder.rglob('*')):
  if p.is_file() and '__pycache__' not in p.parts and (suffixes is None or p.suffix in suffixes):out[p.relative_to(ROOT).as_posix()]=sha(p)
 return out
def inputs():
 from scripts.measurement_provenance import lock_files
 from substrate_rs import _native
 assets={'domains':tree_hashes(ROOT/'domains',{'.py'}),'substrate':tree_hashes(ROOT/'substrate',{'.py'}),'native_python':tree_hashes(ROOT/'runners/dsl/python',{'.py'}),'rust_source':tree_hashes(ROOT/'runners/dsl/src',{'.rs'}),'worlds':tree_hashes(ROOT/'worlds',{'.py'}),'scripts':tree_hashes(ROOT/'scripts',{'.py'}),'seeds':tree_hashes(ROOT/'seeds',{'.json'}),'data/slabs':tree_hashes(ROOT/'data/slabs')}
 explicit=[PROTOCOL,AMENDMENT,__file__,ANALYZER,HELPER,Path(_native.__file__).resolve(),ROOT/'runners/dsl/python/substrate_rs/_native.build.json',ROOT/'runners/dsl/Cargo.toml',ROOT/'runners/dsl/Cargo.lock']
 return {'protocol_sha256':sha(PROTOCOL),'runner_sha256':sha(__file__),'analyzer_sha256':sha(ANALYZER),'helper_sha256':sha(HELPER),'commit':os.environ.get('OCEL0_SOURCE_REV','unrecorded'), 'snapshot_immutable':os.environ.get('OCEL0_IMMUTABLE_SNAPSHOT')=='1','explicit_files':lock_files(explicit,root=ROOT),'runtime_tree_sha256':assets,'family_order':[f['type'] for f in FAMILIES]}
def rss_bytes():
 v=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
 return int(v*(1024 if sys.platform.startswith('linux') else 1))
def make_attrs(f,a,b,fixed=None):
 return {f['variable_a']:a,f['variable_b']:b,f['fixed_key']:f['fixed'] if fixed is None else fixed}
def teach_one(adapter,f,a,b,tmp,fixed=None,*,remove_fixed=False,extra=False):
 from domains.teach import teach
 values=make_attrs(f,a,b,fixed)
 if remove_fixed:values.pop(f['fixed_key'],None)
 if extra:values['untrained_probe_field']='extra'
 before=set(adapter.s.nodes('ShapeObservation'));t=time.perf_counter_ns()
 saved=teach(adapter,f['type'],values,category='rung_attribution_v2',seeds_dir=tmp)
 elapsed=time.perf_counter_ns()-t
 added=[n for n in adapter.s.nodes('ShapeObservation') if n not in before]
 if len(added)!=1:raise RuntimeError(f"expected one ShapeObservation for {f['type']}, got {len(added)}")
 n=added[0];attrs=dict(adapter.s.node(n)['attrs'])
 return {'type':f['type'],'attrs_in':values,'status':attrs.get('status'),'covered_by':attrs.get('covered_by'),'residual':attrs.get('residual'),'observation_id':str(n),'elapsed_ns':elapsed,'teach_saved':saved.get('saved'),'teach_persisted':saved.get('persisted')}
def worker(family_index,rep):
 from substrate.world_adapter import WorldAdapter
 from substrate.boot_all import load_all_seeds
 f=FAMILIES[family_index];a=WorldAdapter(seeds=());boot=load_all_seeds(a,seed_ids={'meta_shape_growth'})
 if boot.get('failed'):raise RuntimeError(f"seed dependency closure failed: {boot['failed']}")
 initial=[dict(a.s.node(n)['attrs']) for n in a.s.nodes('MetaShape')]
 phases=[]
 with tempfile.TemporaryDirectory(prefix='metashape-rung-attribution-v2-') as td:
  training=[]
  for x,y in f['train']:training.append(teach_one(a,f,x,y,td))
  learned=[dict(a.s.node(n)['attrs']) for n in a.s.nodes('MetaShape')]
  target_names=[x.get('name') for x in learned if x not in initial]
  probes=[
   ('positive',f['positive'][0],f['positive'][1],None,False,False),
   ('negative_fixed_value',f['positive'][0],f['positive'][1],f['negative_fixed'],False,False),
   ('negative_fixed_missing',f['positive'][0],f['positive'][1],None,True,False),
   ('negative_extra_field',f['positive'][0],f['positive'][1],None,False,True),
   ('negative_fixed_type',f['positive'][0],f['positive'][1],f['negative_type'],False,False),
  ]
  held=[]
  for label,x,y,fixed,remove,extra in probes:
   rec=teach_one(a,f,x,y,td,fixed,remove_fixed=remove,extra=extra);rec['label']=label;held.append(rec)
 shapes=[dict(a.s.node(n)['attrs']) for n in a.s.nodes('MetaShape')]
 return {'family':f['type'],'replicate':rep,'pid':os.getpid(),'seed_boot':{'loaded':boot.get('loaded'),'total':boot.get('total'),'failures':boot.get('failed',[])},'initial_shapes':initial,'training':training,'shapes_after_training':learned,'new_shape_names':target_names,'heldout':held,'final_shapes':shapes,'peak_rss_bytes':rss_bytes(),'environment':{'python':sys.version,'platform':platform.platform()}}
def main():
 if sys.argv[1:]==['--lock']:
  print(json.dumps({'locked_inputs':inputs()},indent=2,sort_keys=True));return
 if sys.argv[1:]==['--worker']:
  i=int(os.environ['OCEL0_META_FAMILY']);rep=int(os.environ['OCEL0_META_REP'])
  if os.environ.get('OCEL0_IMMUTABLE_SNAPSHOT')=='1':
   before=json.loads(LOCK.read_text())['locked_inputs'];r=worker(i,rep);after=before;stable=True
  else:
   before=inputs();r=worker(i,rep);after=inputs();stable=before==after
  r.update({'locked_inputs_before':before,'locked_inputs_after':after,'source_stable':stable,'immutable_snapshot_worker':os.environ.get('OCEL0_IMMUTABLE_SNAPSHOT')=='1'});print(json.dumps(r,sort_keys=True));return
 locked=inputs()
 if not LOCK.exists() or json.loads(LOCK.read_text()).get('locked_inputs')!=locked:raise SystemExit('missing/stale MetaShape rung-attribution lock')
 env={**os.environ,'PYTHONPATH':f'{ROOT}:{ROOT/"runners/dsl/python"}:{ROOT/"scripts"}','OZMA_SEED_PERSIST_DISABLED':'1'}
 from domains.engine_provenance import build_is_stale
 stale=build_is_stale(str(ROOT))
 if stale:raise SystemExit('native build stale: '+str(stale))
 runs=[]
 for i,rep in SCHEDULE:
  e=env.copy();e.update(OCEL0_META_FAMILY=str(i),OCEL0_META_REP=str(rep))
  p=subprocess.run([sys.executable,str(Path(__file__).resolve()),'--worker'],cwd=ROOT,env=e,text=True,capture_output=True,timeout=300)
  try:r=json.loads(p.stdout)
  except Exception:r={'family':FAMILIES[i]['type'],'replicate':rep,'worker_error':p.stderr or p.stdout}
  r.update({'worker_returncode':p.returncode,'worker_stderr':p.stderr});runs.append(r)
  print(f"completed={FAMILIES[i]['type']}/{rep} rc={p.returncode}",file=sys.stderr,flush=True)
 post=inputs();checks={'eight_workers':len(runs)==8,'unique_pids':len({r.get('pid') for r in runs})==8,'two_per_family':all(sum(r.get('family')==f['type'] for r in runs)==2 for f in FAMILIES),'parent_lock_stable':post==locked,'worker_locks_stable':all(r.get('source_stable') and r.get('locked_inputs_before')==locked==r.get('locked_inputs_after') for r in runs),'seed_load_ok':all(not r.get('seed_boot',{}).get('failures') and r.get('seed_boot',{}).get('loaded',0)>0 for r in runs),'six_observations_each':all(len(r.get('training',[]))==2 and len(r.get('heldout',[]))==5 for r in runs),'immutable_worker_snapshot':all(r.get('immutable_snapshot_worker') for r in runs)}
 report={'schema_version':1,'run_id':'metashape-rung-attribution-panel-v2.1-20260927','locked_inputs':locked,'post_run_inputs':post,'schedule':[(FAMILIES[i]['type'],r) for i,r in SCHEDULE],'integrity_checks':checks,'integrity_pass':all(checks.values()),'runs':runs,'claim_boundary':'Four authored schema families, two fresh-process replicates each, one positive and four structural negative probes per family. Descriptive rung attribution only; not semantic validity or natural prevalence.'}
 OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps({'output':str(OUT.relative_to(ROOT)),'integrity_checks':checks},indent=2))
 if not report['integrity_pass']:raise SystemExit('integrity gates failed')
if __name__=='__main__':main()

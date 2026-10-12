#!/usr/bin/env python3
"""Supervised graph-native class association on the position-heldout bar task."""
from __future__ import annotations
import hashlib, importlib.util, json, os, random, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python')]
import domains.seed_registry
from domains.engine_provenance import assert_measuring_engine
from domains.eye_world import PreVisualWorld,set_params,rf_centre,rf_spread
from domains.wave_world import WaveWorld
from substrate.boot_core import boot_core,load_seeds_into
from substrate_rs import _native

BASE_RUNNER=ROOT/'evaluation/substrate_capability/vision_eye_position_heldout_orientation_v1.py'
BASE_CAPTURE=ROOT/'evaluation/reports/vision_eye_position_heldout_orientation_v1_20261005.json'
BASE_ANALYSIS=ROOT/'evaluation/reports/vision_eye_position_heldout_orientation_v1_analysis_20261005.json'
SPEC=importlib.util.spec_from_file_location('orientation_baseline_v1',BASE_RUNNER)
BASE=importlib.util.module_from_spec(SPEC);assert SPEC and SPEC.loader;SPEC.loader.exec_module(BASE)
RUNNER=Path(__file__).resolve()
ANALYZER=ROOT/'evaluation/substrate_capability/analyze_vision_eye_orientation_native_association_v1_1.py'
PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_VISION_EYE_ORIENTATION_NATIVE_ASSOCIATION_V1_1_PREREG_20261005.md'
LOCK=ROOT/'evaluation/substrate_capability/vision_eye_orientation_native_association_v1_1_lock_20261005.json'
OUT=ROOT/'evaluation/reports/vision_eye_orientation_native_association_v1_1_20261005.json'
SOURCES=('substrate/boot_core.py','substrate/seed_loader.py','domains/eye_world.py','domains/wave_world.py',
 'runners/dsl/src/py.rs','runners/dsl/src/term.rs','runners/dsl/src/grammar.rs','runners/dsl/src/checker.rs','runners/dsl/src/substrate.rs','runners/dsl/src/rewrite.rs',
 'runners/dsl/src/persist.rs','runners/dsl/python/substrate_rs/_native.build.json','runners/dsl/Cargo.lock')
SEEDS=('vision_eye.json','vision_waves.json');LABELS=('horizontal','vertical')

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def manifest():
 p=assert_measuring_engine()
 return {'runner_sha256':sha(RUNNER),'analyzer_sha256':sha(ANALYZER),'protocol_sha256':sha(PROTOCOL),
  'native_sha256':sha(Path(_native.__file__).resolve()),'engine_fingerprint':p['source_fingerprint'],
  'prior_runner_sha256':sha(BASE_RUNNER),'prior_capture_sha256':sha(BASE_CAPTURE),'prior_analysis_sha256':sha(BASE_ANALYSIS),
  'seed_sha256':{n:sha(ROOT/'seeds'/n) for n in SEEDS},'sources':{n:sha(ROOT/n) for n in SOURCES}}

def var(name):return {'type':'Var','name':name}
def attr(name,key):return {'type':'Attr','node':var(name),'key':key}
def lit(value):return {'type':'Lit','value':value}
def computed(t):return {'__term__':t}
def eq(a,b):return {'type':'Eq','a':a,'b':b}
def lt(a,b):return {'type':'Lt','a':a,'b':b}
def and_(*items):return {'type':'And','items':list(items)}
def neighbours(node,edge):return {'type':'Neighbours','node':node,'edge_type':edge,'any_type':False}

def install_reader_rules(s):
 count={'type':'Plus','items':[attr('a','count'),lit(0.0)]}
 assoc= {'name':'eval_orientation_association_learn','match':[
   ['e','has_wunit','u'],['e','has_orientation_class','c'],
   ['c','has_orientation_assoc','a'],['a','orientation_assoc_unit','u']],
   'where':and_(eq(attr('c','active'),lit(1.0)),eq(attr('c','active_step'),attr('e','step')),
      eq(attr('u','act_step'),attr('e','step')),lt(attr('a','last_step'),attr('e','step'))),
   'effects':[['set_attr','a','count',computed({'type':'Plus','items':[attr('a','count'),attr('u','act')]})],
              ['set_attr','a','last_step',computed(attr('e','step'))]]}
 s._inner.add_rule(assoc)
 unit= {'type':'PickUnique','source':neighbours(var('a'),'orientation_assoc_unit')}
 class_score={'type':'Sum','var_name':'a','source':neighbours(var('candidate'),'has_orientation_assoc'),
    'value':{'type':'Times','items':[{'type':'Attr','node':unit,'key':'act'},attr('a','count')]}}
 select={'type':'Argmax','source':neighbours(var('e'),'has_orientation_class'),
    'var_name':'candidate','value':class_score,'default':None}
 predict={'name':'eval_orientation_association_predict','match':[
    ['e','has_orientation_class','c'],['e','has_orientation_query','q']],
    'where':and_(eq(attr('q','step'),attr('e','step')),eq(var('c'),select)),
    'effects':[['add_edge','q','predicted_orientation','c']]}
 s._inner.add_rule(predict)

def run_case(seed,frozen):
 before=manifest()
 if before!=frozen:raise RuntimeError('worker inputs differ from source lock')
 s,agent=boot_core();load_seeds_into(s,agent,['vision_waves','vision_eye'])
 wp=s.nodes('WaveParams')[0]
 for k,v in (('propagate',0.0),('oja',1.0),('oja_eta',0.0)):s.set_attr(wp,k,v)
 wave=WaveWorld(s,h=BASE.H,w=BASE.W,seed=seed);eye=PreVisualWorld(wave,n_units=BASE.N_UNITS,seed=seed)
 set_params(eye,eye=1.0,phase0=1.0,eye_open=0.0,saw=0.0,ph0_eta=BASE.ETA,frozen=0.0)
 for source_type,edge_type,target_type in (("Eye","has_orientation_class","OrientationClass"),
   ("OrientationClass","has_orientation_assoc","OrientationAssociation"),
   ("OrientationAssociation","orientation_assoc_unit","WUnit"),
   ("Eye","has_orientation_query","OrientationQuery"),
   ("OrientationQuery","predicted_orientation","OrientationClass")):
  s._inner.add_production({'src':{'type':source_type,'var':'src'},'edge_type':edge_type,
   'tgt':{'type':target_type,'var':'tgt'},'provenance':'evaluation:orientation_native_association_v1.1'})
 install_reader_rules(s)
 class_nodes={label:s.add_node('OrientationClass',{'name':label,'active':0.0,'active_step':-1.0}) for label in LABELS}
 class_by_node={v:k for k,v in class_nodes.items()}
 s.add_edge(eye.eye,'has_orientation_class',class_nodes['horizontal'],None)
 s.add_edge(eye.eye,'has_orientation_class',class_nodes['vertical'],None)
 associations={}
 for label in LABELS:
  c=class_nodes[label]
  for i,u in enumerate(eye.units):
   a=s.add_node('OrientationAssociation',{'count':0.0,'last_step':0.0,'unit_index':float(i),'class':label})
   s.add_edge(c,'has_orientation_assoc',a,None);s.add_edge(a,'orientation_assoc_unit',u,None)
   associations[(label,i)]=a
 cells={r*BASE.W+c:n for (r,c),n in wave.cells.items()}
 initial_fields=BASE.capture_fields(eye)
 schedule=[(site,label) for site in BASE.TRAIN_SITES for label in LABELS for _ in range(BASE.EXPOSURES)]
 random.Random(610_000+seed).shuffle(schedule)
 exposure={f'{y},{x}:{label}':0 for y,x in BASE.TRAIN_SITES for label in LABELS}
 current=set();steps=len(schedule);input_ns=closure_ns=progress=writes=switches=0;seq_hash=hashlib.sha256();training_trace=[]
 s._inner.scale_audit_set_enabled(False);s._inner.scale_audit_set_per_rule_enabled(False)
 s._inner.scale_audit_reset();s._inner.scale_audit_per_rule_reset()
 for step,(site,label) in enumerate(schedule,1):
  target=BASE.mask_indices(site,label)
  if current!=target:switches+=1
  t=time.perf_counter_ns()
  for idx in current-target:s.set_attr(cells[idx],'bursting',0.0);writes+=1
  for idx in target-current:s.set_attr(cells[idx],'bursting',1.0);writes+=1
  input_ns+=time.perf_counter_ns()-t;current=target
  exposure[f'{site[0]},{site[1]}:{label}']+=1
  seq_hash.update(json.dumps([list(site),label],separators=(',',':')).encode())
  s.set_attr(eye.eye,'step',float(step))
  for lab,node in class_nodes.items():
   s.set_attr(node,'active',float(lab==label));s.set_attr(node,'active_step',float(step))
  t=time.perf_counter_ns();progress+=int(s._inner.run_rules(BASE.CAP));closure_ns+=time.perf_counter_ns()-t
  training_trace.append({'step':step,'site':list(site),'label':label,
    'acts':[float(s.node(u)['attrs']['act']) for u in eye.units]})
 learned_fields=BASE.capture_fields(eye)
 assoc_counts={f'{label}:{i}':float(s.node(a)['attrs']['count']) for (label,i),a in associations.items()}
 set_params(eye,frozen=1.0)
 probes=[];index=0;probe_assoc_before=dict(assoc_counts)
 for site in BASE.ALL_SITES:
  for label in LABELS:
   target=BASE.mask_indices(site,label);step=steps+index+1
   t=time.perf_counter_ns()
   for idx in current-target:s.set_attr(cells[idx],'bursting',0.0);writes+=1
   for idx in target-current:s.set_attr(cells[idx],'bursting',1.0);writes+=1
   input_ns+=time.perf_counter_ns()-t;current=target
   s.set_attr(eye.eye,'step',float(step))
   q=s.add_node('OrientationQuery',{'step':float(step),'probe_index':float(index)})
   s.add_edge(eye.eye,'has_orientation_query',q,None)
   t=time.perf_counter_ns();progress+=int(s._inner.run_rules(BASE.CAP));closure_ns+=time.perf_counter_ns()-t
   acts=[];winners=[]
   for i,u in enumerate(eye.units):
    attrs=s.node(u)['attrs'];acts.append(float(attrs['act']))
    if int(attrs.get('win_step',-1))==step and float(attrs.get('winner',0.0))==1.0:winners.append(i)
   preds=s.neighbours(q,'predicted_orientation')
   probes.append({'probe_index':index,'site':list(site),'label':label,'split':'heldout' if site in BASE.HELDOUT else 'train',
    'mask':sorted(target),'active_count':len(target),'acts':acts,'winners':winners,
    'native_prediction':class_by_node[preds[0]] if len(preds)==1 else None,'prediction_count':len(preds)})
   index+=1
 post_fields=BASE.capture_fields(eye)
 post_counts={f'{label}:{i}':float(s.node(a)['attrs']['count']) for (label,i),a in associations.items()}
 after=manifest()
 return {'pid':os.getpid(),'source_before':before,'source_after':after,'source_stable':before==after,
  'result':{'seed':seed,'steps':steps,'train_sites':[list(x) for x in BASE.TRAIN_SITES],
   'heldout_sites':[list(x) for x in BASE.HELDOUT],'n_units':BASE.N_UNITS,'exposures':exposure,
   'schedule_sha256':seq_hash.hexdigest(),'switches':switches,'input_writes':writes,'training_trace':training_trace,
   'input_update_ns':input_ns,'closure_ns':closure_ns,'progress':progress,'initial_fields':initial_fields,
   'learned_fields':learned_fields,'post_probe_fields':post_fields,'freeze_value':float(s.node(s.nodes('EyeParams')[0])['attrs']['frozen']),
   'association_counts':assoc_counts,'post_probe_association_counts':post_counts,
   'association_counts_before_probes':probe_assoc_before,'probes':probes}}

def main():
 if sys.argv[1:2]==['--lock']:
  if LOCK.exists() or OUT.exists():raise SystemExit('refusing to overwrite native association artifacts')
  val={'schema':'VisionEyeOrientationNativeAssociationV1_1Lock','inputs':manifest(),
   'seeds':list(BASE.SEEDS),'train_sites':[list(x) for x in BASE.TRAIN_SITES],
   'heldout_sites':[list(x) for x in BASE.HELDOUT],'labels':list(LABELS),'steps':BASE.STEPS}
  LOCK.write_text(json.dumps(val,indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return 0
 if sys.argv[1:2]==['--worker']:
  print(json.dumps(run_case(int(sys.argv[2]),json.loads(LOCK.read_text())['inputs']),sort_keys=True));return 0
 if not LOCK.exists():raise SystemExit('missing source lock; run --lock')
 locked=json.loads(LOCK.read_text())
 if manifest()!=locked['inputs']:raise SystemExit('stale native association source lock')
 env={**os.environ,'OZMA_NO_LLM':'1','OZMA_SEED_PERSIST_DISABLED':'1'}
 def launch(seed):
  proc=subprocess.run([sys.executable,str(RUNNER),'--worker',str(seed)],cwd=ROOT,env=env,text=True,capture_output=True)
  try:payload=json.loads(proc.stdout)
  except Exception:payload=None
  failure=None if proc.returncode==0 and payload else {'seed':seed,'returncode':proc.returncode,'stdout_tail':proc.stdout[-2000:],'stderr_tail':proc.stderr[-2000:]}
  return payload,failure
 with ThreadPoolExecutor(max_workers=6) as pool:done=list(pool.map(launch,BASE.SEEDS))
 workers=[w for w,_ in done if w];failures=[f for _,f in done if f];post=manifest();rs=[w['result'] for w in workers]
 checks={'source_stable':post==locked['inputs'] and all(w['source_stable'] for w in workers),
  'six_unique_workers':len(workers)==6 and len({w['pid'] for w in workers})==6,
  'seed_pairs_exact':sorted(r['seed'] for r in rs)==list(BASE.SEEDS),
  'training_schedule_exact':all(r['steps']==BASE.STEPS and set(r['exposures'].values())=={BASE.EXPOSURES} for r in rs),
  'probe_masks_exact':all(len(r['probes'])==32 and all(p['active_count']==5 and len(p['mask'])==5 for p in r['probes']) for r in rs),
  'visual_weights_frozen':all(r['freeze_value']==1.0 and r['learned_fields']==r['post_probe_fields'] for r in rs),
  'one_prediction_per_query':all(all(p['prediction_count']==1 and p['native_prediction'] in LABELS for p in r['probes']) for r in rs),
  'associations_frozen_during_probes':all(r['association_counts']==r['post_probe_association_counts']==r['association_counts_before_probes'] for r in rs),
  'processes_succeeded':not failures}
 report={'schema':'VisionEyeOrientationNativeAssociationV1_1Capture','run_id':'vision-eye-orientation-native-association-v1.1-20261005',
  'lock_path':str(LOCK.relative_to(ROOT)),'lock_sha256':sha(LOCK),'locked_inputs':locked['inputs'],'post_run_inputs':post,
  'seeds':list(BASE.SEEDS),'workers':workers,'process_failures':failures,'checks':checks,'passed':all(checks.values()),
  'claim_limit':'Six paired-seed supervised graph-native association/readout runs on two centered bar patterns; teacher labels and both association rules are authored externally. Does not establish autonomous task discovery or self-improvement.'}
 OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
 print(json.dumps({'passed':report['passed'],'checks':checks,'workers':len(workers),'failures':len(failures),'output':OUT.relative_to(ROOT).as_posix()}))
 return 0 if report['passed'] else 2
if __name__=='__main__':raise SystemExit(main())

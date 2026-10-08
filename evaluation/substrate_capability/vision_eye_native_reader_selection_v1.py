#!/usr/bin/env python3
"""Native selection among supervised orientation readout candidates."""
from __future__ import annotations
import hashlib, importlib.util, json, os, random, resource, subprocess, sys, time
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
ANALYZER=ROOT/'evaluation/substrate_capability/analyze_vision_eye_native_reader_selection_v1.py'
PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_NATIVE_READOUT_SELECTION_GATE_V1_PREREG_20261005.md'
LOCK=ROOT/'evaluation/substrate_capability/vision_eye_native_reader_selection_v1_lock_20261005.json'
OUT=ROOT/'evaluation/reports/vision_eye_native_reader_selection_v1_20261005.json'
FIT_SITES=((3,6),(3,9),(6,3),(6,12),(9,3),(9,12),(12,6),(12,9))
VALIDATION_SITES=((6,6),(6,9),(9,6),(9,9))
HELDOUT_SITES=((3,3),(3,12),(12,3),(12,12))
LABELS=('horizontal','vertical')
TRAINING_STEPS=len(FIT_SITES)*len(LABELS)*BASE.EXPOSURES
SOURCES=('substrate/boot_core.py','substrate/seed_loader.py','domains/eye_world.py','domains/wave_world.py',
 'runners/dsl/src/py.rs','runners/dsl/src/term.rs','runners/dsl/src/grammar.rs','runners/dsl/src/checker.rs','runners/dsl/src/substrate.rs','runners/dsl/src/rewrite.rs',
 'runners/dsl/src/persist.rs','runners/dsl/python/substrate_rs/_native.build.json','runners/dsl/Cargo.lock')
SEEDS=('vision_eye.json','vision_waves.json')

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def manifest():
 p=assert_measuring_engine()
 return {'runner_sha256':sha(RUNNER),'analyzer_sha256':sha(ANALYZER),'protocol_sha256':sha(PROTOCOL),
  'native_sha256':sha(Path(_native.__file__).resolve()),'engine_fingerprint':p['source_fingerprint'],
  'prior_runner_sha256':sha(BASE_RUNNER),'prior_capture_sha256':sha(BASE_CAPTURE),'prior_analysis_sha256':sha(BASE_ANALYSIS),
  'prior_native_capture_sha256':sha(ROOT/'evaluation/reports/vision_eye_orientation_native_association_v1_1_20261005.json'),
  'prior_native_analysis_sha256':sha(ROOT/'evaluation/reports/vision_eye_orientation_native_association_v1_1_analysis_20261005.json'),
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
 assoc= {'name':'eval_orientation_association_learn','match':[
   ['e','has_wunit','u'],['e','has_orientation_class','c'],
   ['c','has_orientation_assoc','a'],['a','orientation_assoc_unit','u']],
   'where':and_(eq(attr('c','active'),lit(1.0)),eq(attr('c','active_step'),attr('e','step')),
      eq(attr('u','act_step'),attr('e','step')),lt(attr('a','last_step'),attr('e','step'))),
   'effects':[['set_attr','a','count',computed({'type':'Plus','items':[attr('a','count'),attr('u','act')]})],
              ['set_attr','a','last_step',computed(attr('e','step'))]]}
 s._inner.add_rule(assoc)
 unit= {'type':'PickUnique','source':neighbours(var('a'),'orientation_assoc_unit')}
 current_act={'type':'Attr','node':unit,'key':'act'}
 prototype={'type':'Div','a':attr('a','count'),'b':lit(float(len(FIT_SITES)*BASE.EXPOSURES))}
 delta={'type':'Plus','items':[current_act,{'type':'Neg','arg':prototype}]}
 distance_score={'type':'Sum','var_name':'a','source':neighbours(var('c'),'has_orientation_assoc'),
    'value':{'type':'Times','items':[delta,delta]}}
 dot_score={'type':'Sum','var_name':'a','source':neighbours(var('c'),'has_orientation_assoc'),
    'value':{'type':'Times','items':[current_act,attr('a','count')]}}
 mixed_score={'type':'IfThenElse','cond':eq(attr('candidate','kind'),lit('dot_product')),
    'then':{'type':'Neg','arg':dot_score},'other':distance_score}
 choose_class={'type':'Argmin','source':neighbours(var('eye'),'has_orientation_class'),
    'var_name':'c','value':mixed_score,'default':None}
 evaluate={'name':'eval_reader_candidate_predict','match':[
    ['eye','has_wunit','unit'],['eye','has_orientation_class','class'],
    ['eye','has_readout_candidate','candidate'],['candidate','has_candidate_vote','vote'],
    ['vote','vote_for_query','query']],
    'where':and_(eq(attr('query','step'),attr('eye','step')),
      eq(attr('unit','act_step'),attr('eye','step')),
      eq(var('class'),choose_class)),
    'effects':[['add_edge','vote','vote_prediction','class']]}
 s._inner.add_rule(evaluate)
 prediction={'type':'PickUnique','source':neighbours(var('vote'),'vote_prediction')}
 target={'type':'PickUnique','source':neighbours(var('query'),'query_target')}
 is_correct={'type':'IfThenElse','cond':eq(prediction,target),'then':lit(1.0),'other':lit(0.0)}
 score={'type':'Sum','var_name':'v','source':neighbours(var('candidate'),'has_validation_vote'),
    'value':{'type':'IfThenElse','cond':eq(
      {'type':'PickUnique','source':neighbours(var('v'),'vote_prediction')},
      {'type':'PickUnique','source':neighbours(
        {'type':'PickUnique','source':neighbours(var('v'),'vote_for_query')},'query_target')}),
      'then':lit(1.0),'other':lit(0.0)}}
 score_rule={'name':'eval_reader_candidate_validation_score','match':[
    ['eye','has_readout_candidate','candidate']],
    'where':eq(attr('eye','selection_stage'),lit('score')),
    'effects':[['set_attr','candidate','validation_score',computed(score)]]}
 s._inner.add_rule(score_rule)
 choose={'type':'ArgminUnique','source':neighbours(var('eye'),'has_readout_candidate'),
    'var_name':'candidate','value':{'type':'Neg','arg':attr('candidate','validation_score')},'default':None}
 select_rule={'name':'eval_reader_candidate_select','match':[
    ['eye','has_readout_candidate','candidate']],
    'where':and_(eq(attr('eye','selection_stage'),lit('select')),
      eq(var('candidate'),choose)),
    'effects':[['add_edge','eye','selected_readout','candidate'],
      ['set_attr','eye','selection_stage',computed(lit('committed'))]]}
 s._inner.add_rule(select_rule)
 selected_prediction={'type':'PickUnique','source':neighbours(var('vote'),'vote_prediction')}
 publish={'name':'eval_selected_reader_publish_prediction','match':[
    ['eye','selected_readout','candidate'],['eye','has_orientation_query','query'],
    ['candidate','has_candidate_vote','vote'],['vote','vote_for_query','query'],
    ['vote','vote_prediction','prediction']],
    'where':eq(attr('query','split'),lit('heldout')),
    'effects':[['add_edge','query','selected_prediction','prediction']]}
 s._inner.add_rule(publish)

def run_case(seed,frozen):
 process_cpu_start=time.process_time_ns()
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
   ("Eye","has_readout_candidate","ReadoutCandidate"),
   ("ReadoutCandidate","has_candidate_vote","ReaderVote"),
   ("ReadoutCandidate","has_validation_vote","ReaderVote"),
   ("ReaderVote","vote_for_query","OrientationQuery"),
   ("ReaderVote","vote_prediction","OrientationClass"),
   ("OrientationQuery","query_target","OrientationClass"),
   ("Eye","selected_readout","ReadoutCandidate"),
   ("OrientationQuery","selected_prediction","OrientationClass")):
  s._inner.add_production({'src':{'type':source_type,'var':'src'},'edge_type':edge_type,
   'tgt':{'type':target_type,'var':'tgt'},'provenance':'evaluation:orientation_native_association_v1.1'})
 install_reader_rules(s)
 class_nodes={label:s.add_node('OrientationClass',{'name':label,'active':0.0,'active_step':-1.0}) for label in LABELS}
 class_by_node={v:k for k,v in class_nodes.items()}
 s.add_edge(eye.eye,'has_orientation_class',class_nodes['horizontal'],None)
 s.add_edge(eye.eye,'has_orientation_class',class_nodes['vertical'],None)
 candidate_nodes={kind:s.add_node('ReadoutCandidate',{'kind':kind,'validation_score':0.0})
   for kind in ('dot_product','prototype_distance')}
 for candidate in candidate_nodes.values():s.add_edge(eye.eye,'has_readout_candidate',candidate,None)
 associations={}
 for label in LABELS:
  c=class_nodes[label]
  for i,u in enumerate(eye.units):
   a=s.add_node('OrientationAssociation',{'count':0.0,'last_step':0.0,'unit_index':float(i),'class':label})
   s.add_edge(c,'has_orientation_assoc',a,None);s.add_edge(a,'orientation_assoc_unit',u,None)
   associations[(label,i)]=a
 cells={r*BASE.W+c:n for (r,c),n in wave.cells.items()}
 initial_fields=BASE.capture_fields(eye)
 schedule=[(site,label) for site in FIT_SITES for label in LABELS for _ in range(BASE.EXPOSURES)]
 random.Random(610_000+seed).shuffle(schedule)
 exposure={f'{y},{x}:{label}':0 for y,x in FIT_SITES for label in LABELS}
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
 probes=[];index=0;probe_assoc_before=dict(assoc_counts);validation_votes=[];heldout_votes=[]
 for split,sites in (('validation',VALIDATION_SITES),('heldout',HELDOUT_SITES)):
  for site in sites:
   for label in LABELS:
    target=BASE.mask_indices(site,label);step=steps+index+1
    t=time.perf_counter_ns()
    for idx in current-target:s.set_attr(cells[idx],'bursting',0.0);writes+=1
    for idx in target-current:s.set_attr(cells[idx],'bursting',1.0);writes+=1
    input_ns+=time.perf_counter_ns()-t;current=target
    s.set_attr(eye.eye,'step',float(step))
    q=s.add_node('OrientationQuery',{'step':float(step),'probe_index':float(index),'split':split})
    s.add_edge(eye.eye,'has_orientation_query',q,None)
    if split=='validation':s.add_edge(q,'query_target',class_nodes[label],None)
    votes=[]
    for kind,candidate in candidate_nodes.items():
     vote=s.add_node('ReaderVote',{'candidate':kind,'probe_index':float(index)})
     s.add_edge(candidate,'has_candidate_vote',vote,None);s.add_edge(vote,'vote_for_query',q,None)
     if split=='validation':
      s.add_edge(candidate,'has_validation_vote',vote,None);validation_votes.append(vote)
     else:heldout_votes.append(vote)
     votes.append((kind,vote))
    t=time.perf_counter_ns();progress+=int(s._inner.run_rules(BASE.CAP));closure_ns+=time.perf_counter_ns()-t
    acts=[];winners=[]
    for i,u in enumerate(eye.units):
     attrs=s.node(u)['attrs'];acts.append(float(attrs['act']))
     if int(attrs.get('win_step',-1))==step and float(attrs.get('winner',0.0))==1.0:winners.append(i)
    preds={kind:[class_by_node[n] for n in s.neighbours(vote,'vote_prediction')] for kind,vote in votes}
    probes.append({'probe_index':index,'site':list(site),'label':label,'split':split,
      'mask':sorted(target),'active_count':len(target),'acts':acts,'winners':winners,
      'candidate_predictions':preds})
    index+=1
 s.set_attr(eye.eye,'selection_stage','score')
 score_cpu_start=time.process_time_ns();t=time.perf_counter_ns();progress+=int(s._inner.run_rules(BASE.CAP));score_ns=time.perf_counter_ns()-t;closure_ns+=score_ns
 score_cpu_ns=time.process_time_ns()-score_cpu_start
 candidate_scores={kind:float(s.node(node)['attrs']['validation_score']) for kind,node in candidate_nodes.items()}
 s.set_attr(eye.eye,'selection_stage','select')
 select_cpu_start=time.process_time_ns();t=time.perf_counter_ns();progress+=int(s._inner.run_rules(BASE.CAP));select_ns=time.perf_counter_ns()-t;closure_ns+=select_ns
 select_cpu_ns=time.process_time_ns()-select_cpu_start
 selected_nodes=s.neighbours(eye.eye,'selected_readout')
 selected=candidate_nodes and next((kind for kind,node in candidate_nodes.items() if node in selected_nodes),None)
 s.set_attr(eye.eye,'selection_stage','committed')
 heldout_query_nodes=[]
 for probe in probes:
  if probe['split']!='heldout':continue
  qnode=next(q for q in s.nodes('OrientationQuery') if int(s.node(q)['attrs']['probe_index'])==probe['probe_index'])
  t=time.perf_counter_ns();progress+=int(s._inner.run_rules(BASE.CAP));closure_ns+=time.perf_counter_ns()-t
  selected_predictions=s.neighbours(qnode,'selected_prediction')
  probe['selected_prediction']=class_by_node[selected_predictions[0]] if len(selected_predictions)==1 else None
  probe['selected_prediction_count']=len(selected_predictions)
  heldout_query_nodes.append((qnode,class_nodes[probe['label']]))
 heldout_predictions_captured=all(p.get('selected_prediction_count')==1 for p in probes if p['split']=='heldout')
 if heldout_predictions_captured:
  for qnode,label_node in heldout_query_nodes:s.add_edge(qnode,'query_target',label_node,None)
 post_fields=BASE.capture_fields(eye)
 post_counts={f'{label}:{i}':float(s.node(a)['attrs']['count']) for (label,i),a in associations.items()}
 after=manifest()
 return {'pid':os.getpid(),'source_before':before,'source_after':after,'source_stable':before==after,
  'result':{'seed':seed,'steps':steps,'train_sites':[list(x) for x in FIT_SITES],
   'validation_sites':[list(x) for x in VALIDATION_SITES],'heldout_sites':[list(x) for x in HELDOUT_SITES],
   'selected_candidate':selected,'candidate_scores':candidate_scores,
   'selection_score_closure_ns':score_ns,'selection_score_cpu_ns':score_cpu_ns,
   'selection_commit_closure_ns':select_ns,'selection_commit_cpu_ns':select_cpu_ns,
   'worker_cpu_ns':time.process_time_ns()-process_cpu_start,'worker_peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
   'heldout_predictions_captured_before_label_reveal':heldout_predictions_captured,
   'heldout_labels_revealed_after_capture':len(heldout_query_nodes)==8 and heldout_predictions_captured,
   'n_units':BASE.N_UNITS,'exposures':exposure,
   'schedule_sha256':seq_hash.hexdigest(),'switches':switches,'input_writes':writes,'training_trace':training_trace,
   'input_update_ns':input_ns,'closure_ns':closure_ns,'progress':progress,'initial_fields':initial_fields,
   'learned_fields':learned_fields,'post_probe_fields':post_fields,'freeze_value':float(s.node(s.nodes('EyeParams')[0])['attrs']['frozen']),
   'association_counts':assoc_counts,'post_probe_association_counts':post_counts,
   'association_counts_before_probes':probe_assoc_before,'probes':probes}}

def main():
 if sys.argv[1:2]==['--lock']:
  if LOCK.exists() or OUT.exists():raise SystemExit('refusing to overwrite native association artifacts')
  val={'schema':'VisionEyeNativeReaderSelectionV1Lock','inputs':manifest(),
   'seeds':list(BASE.SEEDS),'fit_sites':[list(x) for x in FIT_SITES],
   'validation_sites':[list(x) for x in VALIDATION_SITES],
   'heldout_sites':[list(x) for x in HELDOUT_SITES],'labels':list(LABELS),'steps':TRAINING_STEPS}
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
  'seed_ids_exact':sorted(r['seed'] for r in rs)==list(BASE.SEEDS),
  'training_schedule_exact':all(r['steps']==TRAINING_STEPS and set(r['exposures'].values())=={BASE.EXPOSURES} for r in rs),
  'probe_masks_exact':all(len(r['probes'])==16 and all(p['active_count']==5 and len(p['mask'])==5 for p in r['probes']) for r in rs),
  'visual_weights_frozen':all(r['freeze_value']==1.0 and r['learned_fields']==r['post_probe_fields'] for r in rs),
  'selected_prediction_per_corner':all(all(p.get('selected_prediction_count')==1 and p.get('selected_prediction') in LABELS for p in r['probes'] if p['split']=='heldout') for r in rs),
  'selection_candidate_present':all(r['selected_candidate'] in ('dot_product','prototype_distance') for r in rs),
  'selection_scores_unique':all(len(set(r['candidate_scores'].values()))==2 for r in rs),
  'associations_frozen_during_probes':all(r['association_counts']==r['post_probe_association_counts']==r['association_counts_before_probes'] for r in rs),
  'processes_succeeded':not failures}
 report={'schema':'VisionEyeNativeReaderSelectionV1Capture','run_id':'vision-eye-native-reader-selection-v1-20261005',
  'lock_path':str(LOCK.relative_to(ROOT)),'lock_sha256':sha(LOCK),'locked_inputs':locked['inputs'],'post_run_inputs':post,
  'seeds':list(BASE.SEEDS),'workers':workers,'process_failures':failures,'checks':checks,'passed':all(checks.values()),
  'claim_limit':'Six-seed supervised native selection between two externally supplied readouts, using disjoint validation locations and label-sealed corner transfer. This does not establish candidate invention, autonomous task discovery, or self-improvement.'}
 OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
 print(json.dumps({'passed':report['passed'],'checks':checks,'workers':len(workers),'failures':len(failures),'output':OUT.relative_to(ROOT).as_posix()}))
 return 0 if report['passed'] else 2
if __name__=='__main__':raise SystemExit(main())

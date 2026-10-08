#!/usr/bin/env python3
"""Graph-native validation selection between additive and product relations."""
from __future__ import annotations
import hashlib,itertools,json,os,platform,resource,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'runners/dsl/python'),str(ROOT)]
from domains.engine_provenance import assert_measuring_engine
from substrate_rs import _native

RUNNER=Path(__file__).resolve()
ANALYZER=ROOT/'evaluation/substrate_capability/analyze_native_primitive_family_selection_transfer_v1.py'
PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_NATIVE_PRIMITIVE_FAMILY_SELECTION_TRANSFER_V1_PREREG_20261005.md'
PANEL_LOCK=ROOT/'evaluation/substrate_capability/numeric_relation_model_adequacy_audit_v1_1_lock_20261003.json'
LOCK=ROOT/'evaluation/substrate_capability/native_primitive_family_selection_transfer_v1_lock_20261005.json'
OUT=ROOT/'evaluation/reports/native_primitive_family_selection_transfer_v1_20261005.json'
SOURCES=('domains/engine_provenance.py','runners/dsl/src/py.rs','runners/dsl/src/term.rs','runners/dsl/src/grammar.rs',
 'runners/dsl/src/checker.rs','runners/dsl/src/rewrite.rs','runners/dsl/src/substrate.rs','runners/dsl/src/graph.rs',
 'runners/dsl/python/substrate_rs/__init__.py','runners/dsl/python/substrate_rs/_native.build.json','runners/dsl/Cargo.lock')
TASKS=('additive','product');FAMILIES=('additive','product');KEYS=('ax','ay','ex','ey')
VALUES=(-2.5,-1.5,-.5,.5,1.5,2.5);HELDOUT=tuple(itertools.product(VALUES,repeat=4))

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def target(task,row):
 ax,ay,ex,ey=map(float,row)
 return ax+ay==ex+ey if task=='additive' else ax*ay==ex*ey
def panels():
 data=json.loads(PANEL_LOCK.read_text())
 return [p for p in data['panels'] if p['task'] in TASKS]
def manifest():
 provenance=assert_measuring_engine()
 return {'runner_sha256':sha(RUNNER),'analyzer_sha256':sha(ANALYZER),'protocol_sha256':sha(PROTOCOL),
  'panel_lock_sha256':sha(PANEL_LOCK),'engine_fingerprint':provenance['source_fingerprint'],
  'native_sha256':sha(Path(_native.__file__).resolve()),
  'sources':{p:sha(ROOT/p) for p in SOURCES}}

def var(name):return {'type':'Var','name':name}
def attr(name,key):return {'type':'Attr','node':var(name),'key':key}
def lit(value):return {'type':'Lit','value':value}
def computed(term):return {'__term__':term}
def eq(a,b):return {'type':'Eq','a':a,'b':b}
def neg(x):return {'type':'Neg','arg':x}
def neighbours(node,edge):return {'type':'Neighbours','node':node,'edge_type':edge,'any_type':False}
def plus(a,b):return {'type':'Plus','items':[a,b]}
def times(a,b):return {'type':'Times','items':[a,b]}

def install_rules(s):
 for src,edge,tgt in (('FamilyEpisode','has_family','RelationFamily'),
   ('RelationFamily','has_vote','RelationVote'),('RelationFamily','has_validation_vote','RelationVote'),
   ('RelationFamily','has_test_vote','RelationVote'),('RelationVote','vote_for_example','RelationExample'),
   ('FamilyEpisode','selected_family','RelationFamily')):
  s.add_production({'src':{'type':src,'var':'src'},'edge_type':edge,
    'tgt':{'type':tgt,'var':'tgt'},'provenance':'evaluation:native_primitive_family_selection_transfer_v1'})
 ax,ay,ex,ey=(attr('example',k) for k in KEYS)
 additive=eq(plus(ax,ay),plus(ex,ey));product=eq(times(ax,ay),times(ex,ey))
 candidate_value={'type':'IfThenElse','cond':eq(attr('family','kind'),lit('additive')),
   'then':additive,'other':product}
 predict={'name':'eval_native_relation_candidate_predict','match':[
   ['episode','has_family','family'],['family','has_vote','vote'],['vote','vote_for_example','example']],
   'where':eq(attr('episode','stage'),attr('example','split')),
   'effects':[['set_attr','vote','prediction',computed(candidate_value)]]}
 s.add_rule(predict)
 vote_example={'type':'PickUnique','source':neighbours(var('v'),'vote_for_example')}
 vote_label={'type':'Attr','node':vote_example,'key':'label'}
 vote_prediction=attr('v','prediction')
 correct={'type':'IfThenElse','cond':eq(vote_prediction,vote_label),'then':lit(1.0),'other':lit(0.0)}
 total={'type':'Sum','var_name':'v','source':neighbours(var('family'),'has_validation_vote'),'value':correct}
 score={'name':'eval_native_relation_candidate_score','match':[
   ['episode','has_family','family']],
   'where':eq(attr('episode','stage'),lit('score')),
   'effects':[['set_attr','family','validation_score',computed(total)]]}
 s.add_rule(score)
 choice={'type':'ArgminUnique','source':neighbours(var('episode'),'has_family'),
   'var_name':'family','value':neg(attr('family','validation_score')),'default':None}
 select={'name':'eval_native_relation_candidate_select','match':[
   ['episode','has_family','family']],
   'where':eq(attr('episode','stage'),lit('select')),
   'effects':[]}
 select['where']={'type':'And','items':[eq(attr('episode','stage'),lit('select')),eq(var('family'),choice)]}
 select['effects']=[['add_edge','episode','selected_family','family'],
   ['set_attr','episode','stage',computed(lit('selected'))]]
 s.add_rule(select)
 publish={'name':'eval_native_relation_selected_prediction','match':[
   ['episode','selected_family','family'],['family','has_test_vote','vote'],
   ['vote','vote_for_example','example']],
   'where':eq(attr('episode','stage'),lit('test')),
   'effects':[['set_attr','example','selected_prediction',computed(attr('vote','prediction'))]]}
 s.add_rule(publish)

def run_panel(panel,locked):
 before=manifest()
 if before!=locked:raise RuntimeError('worker sources differ from lock')
 cpu_start=time.process_time_ns();wall_start=time.perf_counter_ns()
 substrate=_native.Substrate();install_rules(substrate)
 episode=substrate.add_node('FamilyEpisode',{'stage':'validation'})
 fam_nodes={family:substrate.add_node('RelationFamily',{'kind':family,'validation_score':0.0}) for family in FAMILIES}
 for node in fam_nodes.values():substrate.add_edge(episode,'has_family',node,None)
 example_nodes=[];validation_vote_nodes=[];heldout_vote_nodes=[]
 def add_example(row,label,split,index):
  attrs={k:float(v) for k,v in zip(KEYS,row)};attrs.update({'split':split,'index':float(index)})
  if label is not None:attrs['label']=bool(label)
  node=substrate.add_node('RelationExample',attrs)
  votes={}
  for family,fnode in fam_nodes.items():
   vote=substrate.add_node('RelationVote',{'family':family,'example_index':float(index)})
   substrate.add_edge(fnode,'has_vote',vote,None);substrate.add_edge(vote,'vote_for_example',node,None)
   if split=='validation':substrate.add_edge(fnode,'has_validation_vote',vote,None);validation_vote_nodes.append(vote)
   elif split=='test':substrate.add_edge(fnode,'has_test_vote',vote,None);heldout_vote_nodes.append(vote)
   votes[family]=vote
  example_nodes.append((node,row,label,split,votes));return node
 for i,row in enumerate(panel['selection_pool']):add_example(row,target(panel['task'],row),'validation',i)
 val_start=time.process_time_ns();val_wall_start=time.perf_counter_ns();substrate.run_rules(10000);validation_wall=time.perf_counter_ns()-val_wall_start;validation_cpu=time.process_time_ns()-val_start
 substrate.set_attr(episode,'stage','score');score_cpu_start=time.process_time_ns();t=time.perf_counter_ns();substrate.run_rules(10000);score_wall=time.perf_counter_ns()-t;score_cpu=time.process_time_ns()-score_cpu_start
 native_scores={f:float(substrate.node(n)['attrs']['validation_score']) for f,n in fam_nodes.items()}
 substrate.set_attr(episode,'stage','select');select_cpu_start=time.process_time_ns();t=time.perf_counter_ns();substrate.run_rules(10000);select_wall=time.perf_counter_ns()-t;select_cpu=time.process_time_ns()-select_cpu_start
 chosen_nodes=substrate.neighbours(episode,'selected_family');selected=next((f for f,n in fam_nodes.items() if n in chosen_nodes),None)
 # Candidate identifiers, not the hidden task identity, are the only task-family facts in the graph.
 for i,row in enumerate(HELDOUT):add_example(row,None,'test',i)
 substrate.set_attr(episode,'stage','test');t=time.perf_counter_ns();substrate.run_rules(10000);test_wall=time.perf_counter_ns()-t
 rows=[];label_reveal_receipt=True
 for node,row,label,split,votes in example_nodes:
  if split=='validation':
   predictions={f:substrate.node(v)['attrs'].get('prediction') for f,v in votes.items()}
   rows.append({'split':split,'row':list(row),'label':bool(label),'predictions':predictions})
  else:
   predictions={f:substrate.node(v)['attrs'].get('prediction') for f,v in votes.items()}
   selected_prediction=substrate.node(node)['attrs'].get('selected_prediction')
   rows.append({'split':split,'row':list(row),'label':bool(target(panel['task'],row)),
     'predictions':predictions,'selected_prediction':selected_prediction})
 # Reveal held-out labels only after all candidate and selected predictions have been copied to the receipt.
 heldout_nodes=[n for n,_,_,sp,_ in example_nodes if sp=='test']
 label_reveal_receipt=all(substrate.node(n)['attrs'].get('selected_prediction') is not None for n in heldout_nodes) if selected else all(
   all(substrate.node(n)['attrs'].get('prediction') is not None for n in heldout_nodes) for _ in [0])
 if label_reveal_receipt:
  for n,row,label,sp,_ in example_nodes:
   if sp=='test':substrate.set_attr(n,'label',bool(target(panel['task'],row)))
 graph_nodes=[]
 for nid in [episode,*fam_nodes.values()]:graph_nodes.append(substrate.node(nid))
 for nid,_,_,_,votes in example_nodes:
  graph_nodes.append(substrate.node(nid));graph_nodes.extend(substrate.node(v) for v in votes.values())
 forbidden_task_fields={'task','task_id','target_task','target_family'}
 no_task_identity=all(not forbidden_task_fields.intersection((n.get('attrs') or {}).keys()) for n in graph_nodes)
 after=manifest()
 return {'source_before':before,'source_after':after,'source_stable':before==after,
  'panel':{'task_for_scorer_only':panel['task'],'worker':panel['worker'],'seed':panel['seed'],
    'training_rows':panel['training'],'validation_rows':panel['selection_pool'],'test_rows':[list(r) for r in HELDOUT]},
  'episode_graph_task_attribute_absent':substrate.node(episode)['attrs'].get('task') is None,
  'graph_task_identity_absent':no_task_identity,
  'candidate_ids':list(FAMILIES),'native_validation_scores':native_scores,
  'selected_candidate':selected,'label_reveal_receipt':label_reveal_receipt,'examples':rows,
  'validation_closure_ns':validation_wall,'selection_score_closure_ns':score_wall,
  'selection_commit_closure_ns':select_wall,'test_closure_ns':test_wall,
  'selection_score_cpu_ns':score_cpu,'selection_commit_cpu_ns':select_cpu,
  'worker_cpu_ns':time.process_time_ns()-cpu_start,'worker_wall_ns':time.perf_counter_ns()-wall_start,
  'worker_peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'source_after':after}

def main():
 args=sys.argv[1:]
 if args==['--lock']:
  if LOCK.exists() or OUT.exists():raise SystemExit('refusing overwrite')
  lock={'schema':'NativePrimitiveFamilySelectionTransferV1Lock','inputs':manifest(),
   'panels':panels(),'families':list(FAMILIES),'keys':list(KEYS),'heldout_values':list(VALUES),
   'heldout_rows':[list(r) for r in HELDOUT],'task_panel_count':10}
  LOCK.write_text(json.dumps(lock,indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return 0
 if args==['--worker']:
  lock=json.loads(LOCK.read_text());panel=json.loads(sys.stdin.read());print(json.dumps(run_panel(panel,lock['inputs']),sort_keys=True,separators=(',',':')));return 0
 if args==['--run']:
  lock=json.loads(LOCK.read_text())
  if manifest()!=lock['inputs']:raise SystemExit('source lock drift')
  env={**os.environ,'PYTHONPATH':f'{ROOT}/runners/dsl/python:{ROOT}','OZMA_NO_LLM':'1'};workers=[];failures=[]
  for panel in lock['panels']:
   proc=subprocess.run([sys.executable,str(RUNNER),'--worker'],input=json.dumps(panel),cwd=ROOT,env=env,text=True,capture_output=True)
   if proc.returncode:
    failures.append({'panel':panel['task']+':'+str(panel['worker']),'returncode':proc.returncode,'stderr_tail':proc.stderr[-3000:]});continue
   try:workers.append(json.loads(proc.stdout.strip().splitlines()[-1]))
   except Exception as e:failures.append({'panel':panel['task']+':'+str(panel['worker']),'parse_error':str(e),'stdout_tail':proc.stdout[-1000:]})
  after=manifest()
  checks={'source_stable':after==lock['inputs'] and all(w['source_stable'] for w in workers),
   'ten_panels':len(workers)==10,'worker_processes_succeeded':not failures,
   'label_reveal_receipts':all(w['label_reveal_receipt'] for w in workers),
   'no_target_task_in_graph':all(w['episode_graph_task_attribute_absent'] for w in workers)}
  report={'schema':'NativePrimitiveFamilySelectionTransferV1Capture','lock_sha256':sha(LOCK),
   'locked_inputs':lock['inputs'],'post_run_inputs':after,'checks':checks,'passed':all(checks.values()),
   'workers':workers,'process_failures':failures,
   'claim_limit':'Ten existing numeric panels; graph-native candidate scoring and unique selection over a supplied additive/product menu. Not autonomous family invention or a novel benchmark.'}
  OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps({'passed':report['passed'],'checks':checks,'workers':len(workers),'failures':len(failures),'output':OUT.relative_to(ROOT).as_posix()}));return 0 if report['passed'] else 2
 raise SystemExit('usage: --lock | --run | --worker')
if __name__=='__main__':raise SystemExit(main())

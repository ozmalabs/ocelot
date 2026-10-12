#!/usr/bin/env python3
"""Fresh paired candidate-positive and uniform adequacy query gate."""
from __future__ import annotations
import hashlib,itertools,json,os,random,resource,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'runners/dsl/python'),str(ROOT)]
from domains.engine_provenance import assert_measuring_engine
from substrate_rs import _native
RUNNER=Path(__file__).resolve();ANALYZER=ROOT/'evaluation/substrate_capability/analyze_native_candidate_adequacy_query_v1_5.py'
PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_NATIVE_CANDIDATE_ADEQUACY_QUERY_V1_5_PREREG_20261005.md'
LOCK=ROOT/'evaluation/substrate_capability/native_candidate_adequacy_query_v1_5_lock_20261005.json'
OUT=ROOT/'evaluation/reports/native_candidate_adequacy_query_v1_5_20261005.json'
SOURCES=('domains/engine_provenance.py','runners/dsl/src/py.rs','runners/dsl/src/term.rs','runners/dsl/src/grammar.rs','runners/dsl/src/checker.rs','runners/dsl/src/rewrite.rs','runners/dsl/src/substrate.rs','runners/dsl/src/graph.rs','runners/dsl/python/substrate_rs/__init__.py','runners/dsl/python/substrate_rs/_native.build.json','runners/dsl/Cargo.lock')
TASKS=('additive','product','opposition','inequality');ARMS=('candidate_positive','native_candidate_positive','uniform');FAMILIES=('additive','product');KEYS=('ax','ay','ex','ey')
IV=tuple(float(x) for x in range(-3,4));FV=(-2.5,-1.5,-.5,.5,1.5,2.5);THRESHOLD=.98;BUDGET=4

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def target(task,row):
 ax,ay,ex,ey=map(float,row)
 if task=='additive':return ax+ay==ex+ey
 if task=='product':return ax*ay==ex*ey
 if task=='opposition':return ax==-ex and ay==-ey
 return ax!=ex
def make_validation(task,seed):
 grid=list(itertools.product(IV,repeat=4));out=[]
 for label in (True,False):
  pool=[list(r) for r in grid if target(task,r) is label];random.Random(seed+(0 if label else 1)).shuffle(pool);chosen=[]
  for src in ([r for r in pool if 0.0 in r],[r for r in pool if any(abs(x)==3.0 for x in r)]):
   n=0
   for row in src:
    if row not in chosen:chosen.append(row);n+=1
    if n==8:break
  for row in pool:
   if len(chosen)>=16:break
   if row not in chosen:chosen.append(row)
  if len(chosen)!=16 or not any(0.0 in r for r in chosen) or not any(any(abs(x)==3.0 for x in r) for r in chosen):raise RuntimeError('balanced panel generation failed')
  out.extend({'row':r,'label':label} for r in chosen)
 return out
def base_panels():
 out=[]
 for ti,task in enumerate(TASKS):
  for worker in range(10):
   seed=980000+ti*100+worker
   for arm in ARMS:out.append({'task':task,'worker':worker,'seed':seed,'arm':arm,'validation':make_validation(task,seed)})
 return out
def heldout(panel):
 val={tuple(x['row']) for x in panel['validation']}
 return [r for r in itertools.product(IV,repeat=4) if r not in val]+list(itertools.product(FV,repeat=4))
def manifest():
 p=assert_measuring_engine()
 return {'runner_sha256':sha(RUNNER),'analyzer_sha256':sha(ANALYZER),'protocol_sha256':sha(PROTOCOL),'panel_generator':'fresh-seed-980000-balanced-32','engine_fingerprint':p['source_fingerprint'],'native_sha256':sha(Path(_native.__file__).resolve()),'sources':{x:sha(ROOT/x) for x in SOURCES}}
def var(n):return {'type':'Var','name':n}
def attr(n,k):return {'type':'Attr','node':var(n),'key':k}
def lit(x):return {'type':'Lit','value':x}
def comp(x):return {'__term__':x}
def eq(a,b):return {'type':'Eq','a':a,'b':b}
def neg(x):return {'type':'Neg','arg':x}
def neigh(n,e):return {'type':'Neighbours','node':n,'edge_type':e,'any_type':False}
def plus(a,b):return {'type':'Plus','items':[a,b]}
def times(a,b):return {'type':'Times','items':[a,b]}
def install(s):
 for src,e,tgt in (('FamilyEpisode','has_family','RelationFamily'),('RelationFamily','has_vote','RelationVote'),('RelationFamily','has_validation_vote','RelationVote'),('RelationVote','vote_for_example','RelationExample'),('FamilyEpisode','selected_family','RelationFamily'),('FamilyEpisode','has_probe_example','RelationExample'),('FamilyEpisode','eligible_candidate_probe','RelationExample'),('FamilyEpisode','selected_query','RelationExample')):
  s.add_production({'src':{'type':src,'var':'src'},'edge_type':e,'tgt':{'type':tgt,'var':'tgt'},'provenance':'evaluation:native_candidate_adequacy_query_v1_5'})
 ax,ay,ex,ey=(attr('example',k) for k in KEYS)
 predval={'type':'IfThenElse','cond':eq(attr('family','kind'),lit('additive')),'then':eq(plus(ax,ay),plus(ex,ey)),'other':eq(times(ax,ay),times(ex,ey))}
 s.add_rule({'name':'query_gate_predict','match':[['episode','has_family','family'],['family','has_vote','vote'],['vote','vote_for_example','example']],'where':eq(attr('episode','stage'),attr('example','split')),'effects':[['set_attr','vote','prediction',comp(predval)]]})
 ve={'type':'PickUnique','source':neigh(var('v'),'vote_for_example')};yl={'type':'Attr','node':ve,'key':'label'};yp=attr('v','prediction')
 tp={'type':'IfThenElse','cond':{'type':'And','items':[eq(yl,lit(True)),eq(yp,lit(True))]},'then':lit(1/16),'other':lit(0)}
 tn={'type':'IfThenElse','cond':{'type':'And','items':[eq(yl,lit(False)),eq(yp,lit(False))]},'then':lit(1/16),'other':lit(0)}
 score={'type':'IfThenElse','cond':{'type':'Lt','a':{'type':'Sum','var_name':'v','source':neigh(var('family'),'has_validation_vote'),'value':tp},'b':{'type':'Sum','var_name':'v','source':neigh(var('family'),'has_validation_vote'),'value':tn}},'then':{'type':'Sum','var_name':'v','source':neigh(var('family'),'has_validation_vote'),'value':tp},'other':{'type':'Sum','var_name':'v','source':neigh(var('family'),'has_validation_vote'),'value':tn}}
 raw={'type':'Sum','var_name':'v','source':neigh(var('family'),'has_validation_vote'),'value':{'type':'IfThenElse','cond':eq(yp,yl),'then':lit(1),'other':lit(0)}}
 s.add_rule({'name':'query_gate_score','match':[['episode','has_family','family']],'where':eq(attr('episode','stage'),lit('score')),'effects':[['set_attr','family','minimum_class_accuracy',comp(score)],['set_attr','family','raw_validation_score',comp(raw)]]})
 choice={'type':'ArgminUnique','source':neigh(var('episode'),'has_family'),'var_name':'family','value':neg(attr('family','minimum_class_accuracy')),'default':None}
 best={'type':'MaxOver','source':neigh(var('episode'),'has_family'),'var_name':'f','value':attr('f','minimum_class_accuracy'),'default':lit(0)}
 s.add_rule({'name':'query_gate_accept','match':[['episode','has_family','family']],'where':{'type':'And','items':[eq(attr('episode','stage'),lit('diagnose')),{ 'type':'Gte','a':best,'b':lit(THRESHOLD)}]},'effects':[['set_attr','episode','adequacy_status',comp(lit('adequate'))]]})
 s.add_rule({'name':'query_gate_reject','match':[['episode','has_family','family']],'where':{'type':'And','items':[eq(attr('episode','stage'),lit('diagnose')),{ 'type':'Lt','a':best,'b':lit(THRESHOLD)}]},'effects':[['set_attr','episode','adequacy_status',comp(lit('model_mismatch'))],['set_attr','episode','decision',comp(lit('request_help'))]]})
 s.add_rule({'name':'query_gate_select','match':[['episode','has_family','family']],'where':{'type':'And','items':[eq(attr('episode','stage'),lit('select')),eq(attr('episode','adequacy_status'),lit('adequate')),eq(var('family'),choice)]},'effects':[['add_edge','episode','selected_family','family'],['set_attr','episode','decision',comp(lit('selected'))],['set_attr','episode','stage',comp(lit('selected'))]]})
 s.add_rule({'name':'query_gate_tie','match':[['episode','has_family','family']],'where':{'type':'And','items':[eq(attr('episode','stage'),lit('select')),eq(attr('episode','adequacy_status'),lit('adequate')),eq(choice,lit(None))]},'effects':[['set_attr','episode','decision',comp(lit('abstain_tie'))],['set_attr','episode','stage',comp(lit('selected'))]]})
 # Native graph rules derive candidate-positive eligibility and select by rank.
 eligible={'type':'And','items':[eq(attr('episode','stage'),lit('probe_prepare')),eq(attr('vote','prediction'),lit(True))]}
 s.add_rule({'name':'query_gate_candidate_positive_probe_eligibility','match':[['episode','selected_family','family'],['episode','has_probe_example','example'],['family','has_vote','vote'],['vote','vote_for_example','example']],'where':eligible,'effects':[['add_edge','episode','eligible_candidate_probe','example']]})
 query_choice={'type':'ArgminUnique','source':neigh(var('episode'),'eligible_candidate_probe'),'var_name':'candidate','value':{'type':'IfThenElse','cond':eq(attr('candidate','queried'),lit(True)),'then':lit(1000000.0),'other':attr('candidate','probe_rank')},'default':None}
 s.add_rule({'name':'query_gate_native_query_select_candidate_positive','match':[['episode','selected_family','family']],'where':eq(attr('episode','stage'),lit('query_select_native_positive')),'effects':[['set_attr','episode','selected_query_node',comp(query_choice)],['set_attr','episode','stage',comp(lit('query_ready'))]]})
 for suffix,prediction,label in (('false_positive',True,False),('false_negative',False,True)):
  condition={'type':'And','items':[eq(attr('episode','stage'),lit('probe_adjudicate')),eq(attr('example','split'),lit('probe')),eq(attr('vote','prediction'),lit(prediction)),eq(attr('example','label'),lit(label))]}
  s.add_rule({'name':'query_gate_probe_counterexample_help_'+suffix,'match':[['episode','selected_family','family'],['family','has_vote','vote'],['vote','vote_for_example','example']],'where':condition,'effects':[['set_attr','episode','decision',comp(lit('request_help'))],['set_attr','episode','adequacy_status',comp(lit('counterexample_found'))],['set_attr','episode','stage',comp(lit('probe_stop'))]]})

def worker(panel,locked):
 before=manifest()
 if before!=locked:raise RuntimeError('source lock drift')
 cpu0=time.process_time_ns();wall0=time.perf_counter_ns();s=_native.Substrate();install(s)
 ep=s.add_node('FamilyEpisode',{'stage':'validation','adequacy_status':'pending','decision':'pending'});families={f:s.add_node('RelationFamily',{'kind':f,'minimum_class_accuracy':0.0}) for f in FAMILIES}
 for n in families.values():s.add_edge(ep,'has_family',n,None)
 examples=[];valvotes={f:[] for f in FAMILIES}
 def add_example(row,label,split,index):
  attrs={k:float(v) for k,v in zip(KEYS,row)};attrs.update({'split':split,'index':float(index)})
  if split=='probe':attrs.update({'probe_rank':float(rank_by_row[tuple(row)]),'queried':False})
  if label is not None:attrs['label']=bool(label)
  n=s.add_node('RelationExample',attrs);votes={}
  if split=='probe':s.add_edge(ep,'has_probe_example',n,None)
  for f,fn in families.items():
   v=s.add_node('RelationVote',{'family':f,'example_index':float(index)});s.add_edge(fn,'has_vote',v,None);s.add_edge(v,'vote_for_example',n,None)
   if split=='validation':s.add_edge(fn,'has_validation_vote',v,None);valvotes[f].append(v)
   votes[f]=v
  examples.append((n,list(row),label,split,votes));return n,votes
 for i,item in enumerate(panel['validation']):add_example(item['row'],item['label'],'validation',i)
 t=time.perf_counter_ns();s.run_rules(10000);validation_ns=time.perf_counter_ns()-t
 s.set_attr(ep,'stage','score');t=time.perf_counter_ns();s.run_rules(10000);score_ns=time.perf_counter_ns()-t
 scores={f:float(s.node(n)['attrs']['minimum_class_accuracy']) for f,n in families.items()};rawscores={f:float(s.node(n)['attrs']['raw_validation_score']) for f,n in families.items()}
 s.set_attr(ep,'stage','diagnose');t=time.perf_counter_ns();s.run_rules(10000);diagnose_ns=time.perf_counter_ns()-t
 adequacy=s.node(ep)['attrs'].get('adequacy_status');s.set_attr(ep,'stage','select');t=time.perf_counter_ns();s.run_rules(10000);select_ns=time.perf_counter_ns()-t
 linked=s.neighbours(ep,'selected_family');selected=next((f for f,n in families.items() if n in linked),None);initial_decision=s.node(ep)['attrs'].get('decision')
 rows=heldout(panel)
 seed=f'native-adequacy-query-v1.3:replicate:{panel["worker"]}'
 ranked_rows=sorted(rows,key=lambda row:hashlib.sha256((seed+':'+json.dumps(list(row),separators=(',',':'))).encode()).hexdigest())
 rank_by_row={tuple(row):i for i,row in enumerate(ranked_rows)}
 testnodes=[]
 for i,row in enumerate(rows):
  n,votes=add_example(row,None,'probe',i);testnodes.append((n,row,votes))
 s.set_attr(ep,'stage','probe');t=time.perf_counter_ns();s.run_rules(10000);probe_prediction_ns=time.perf_counter_ns()-t
 pred_rows=[]
 for n,row,votes in testnodes:
  pred={f:s.node(v)['attrs'].get('prediction') for f,v in votes.items()}
  pred_rows.append({'row':list(row),'predictions':pred})
 if panel['arm']=='native_candidate_positive':
  s.set_attr(ep,'stage','probe_prepare');t=time.perf_counter_ns();s.run_rules(10000);eligibility_ns=time.perf_counter_ns()-t
 else:eligibility_ns=0
 host_order=[]
 if selected is not None and panel['arm']!='native_candidate_positive':
  eligible=[x for x in pred_rows if panel['arm']=='uniform' or x['predictions'][selected] is True]
  eligible.sort(key=lambda x:rank_by_row[tuple(x['row'])]);host_order=eligible[:BUDGET]
 query_receipts=[];query_cpu_ns=0;query_selection_ns=0;query_selection_owner='native_graph' if panel['arm']=='native_candidate_positive' else 'host'
 for qi in range(BUDGET):
  if selected is None:break
  if panel['arm']=='native_candidate_positive':
   s.set_attr(ep,'stage','query_select_native_positive');t=time.perf_counter_ns();s.run_rules(10000);query_selection_ns+=time.perf_counter_ns()-t
   chosen_node=s.node(ep)['attrs'].get('selected_query_node')
   candidate=next((x for x in testnodes if x[0]==chosen_node and tuple(x[1]) not in {tuple(q['row']) for q in query_receipts}),None)
   if candidate is None:break
   node,row,votes=candidate;q={'row':list(row),'predictions':{f:s.node(v)['attrs'].get('prediction') for f,v in votes.items()},'selected_by_native':True}
  else:
   if qi>=len(host_order):break
   q=host_order[qi];key=tuple(q['row']);node,row,votes=next(x for x in testnodes if tuple(x[1])==key);q={**q,'selected_by_native':False}
  label=target(panel['task'],row)
  s.set_attr(node,'label',bool(label));s.set_attr(ep,'stage','probe_adjudicate');t=time.perf_counter_ns();s.run_rules(10000);query_cpu_ns+=time.perf_counter_ns()-t
  decision=s.node(ep)['attrs'].get('decision');q['label_after_query']=bool(label);q['candidate_prediction']=q['predictions'][selected];q['mismatch']=q['candidate_prediction'] is not bool(label);q['native_decision_after_query']=decision
  query_receipts.append(q)
  if decision=='request_help':break
  s.set_attr(node,'queried',True);s.set_attr(ep,'stage','probe')
 final_decision=s.node(ep)['attrs'].get('decision');query_keys={tuple(q['row']) for q in query_receipts}
 final=[];candidate_confusion={f:{'tp':0,'fp':0,'fn':0,'tn':0} for f in FAMILIES};selected_correct=0
 for n,row,votes in testnodes:
  if tuple(row) in query_keys:continue
  label=target(panel['task'],row);pred={f:s.node(v)['attrs'].get('prediction') for f,v in votes.items()}
  for f in FAMILIES:
   yhat=pred[f];k='tp' if yhat and label else 'fp' if yhat else 'fn' if label else 'tn';candidate_confusion[f][k]+=1
  selected_prediction=pred[selected] if selected is not None and final_decision=='selected' else None
  if selected_prediction is not None:selected_correct+=int(selected_prediction is label)
  final.append({'row':list(row),'label':bool(label),'predictions':pred,'selected_prediction':selected_prediction})
 graph=[s.node(i) for i in [ep,*families.values()]]
 for n,_,_,_,votes in examples:graph.append(s.node(n));graph.extend(s.node(v) for v in votes.values())
 graph.extend(s.node(n) for n,_,_ in testnodes);graph.extend(s.node(v) for _,_,votes in testnodes for v in votes.values())
 absent=all(not ({'task','task_id','target_task','target_family'} & (g.get('attrs') or {}).keys()) for g in graph)
 receipt=all(q.get('native_decision_after_query') in ('selected','request_help') and q['mismatch']==(q['native_decision_after_query']=='request_help') for q in query_receipts)
 after=manifest()
 return {'source_before':before,'source_after':after,'source_stable':before==after,'panel':{'task_for_scorer_only':panel['task'],'worker':panel['worker'],'seed':panel['seed'],'arm':panel['arm'],'validation_rows':panel['validation'],'query_pool_size':len(rows)},'candidate_ids':list(FAMILIES),'native_min_class_accuracy_scores':scores,'native_raw_validation_scores':rawscores,'adequacy_status_before_queries':adequacy,'initial_decision':initial_decision,'selected_candidate':selected,'final_decision':final_decision,'query_receipt_valid':receipt,'query_selection_owner':query_selection_owner,'query_rows':query_receipts,'final_test_rows':final,'final_candidate_confusion':candidate_confusion,'selected_correct_rows':selected_correct,'selected_rows':len(final) if final_decision=='selected' else 0,'task_identity_absent':absent,'validation_closure_ns':validation_ns,'score_closure_ns':score_ns,'diagnosis_closure_ns':diagnose_ns,'selection_closure_ns':select_ns,'probe_prediction_closure_ns':probe_prediction_ns,'query_eligibility_ns':eligibility_ns,'query_selection_ns':query_selection_ns,'query_adjudication_ns':query_cpu_ns,'worker_cpu_ns':time.process_time_ns()-cpu0,'worker_wall_ns':time.perf_counter_ns()-wall0,'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
def main():
 args=sys.argv[1:]
 if args==['--lock']:
  if LOCK.exists() or OUT.exists():raise SystemExit('refusing overwrite')
  LOCK.write_text(json.dumps({'schema':'NativeCandidateAdequacyQueryV1_5Lock','inputs':manifest(),'panels':base_panels(),'families':list(FAMILIES),'tasks':list(TASKS),'threshold':THRESHOLD,'query_budget':BUDGET,'arms':list(ARMS)},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return 0
 if args==['--worker']:
  lock=json.loads(LOCK.read_text());panel=json.loads(sys.stdin.read());print(json.dumps(worker(panel,lock['inputs']),sort_keys=True,separators=(',',':')));return 0
 if args==['--run']:
  lock=json.loads(LOCK.read_text())
  if manifest()!=lock['inputs']:raise SystemExit('source lock drift')
  env={**os.environ,'PYTHONPATH':f'{ROOT}/runners/dsl/python:{ROOT}','OZMA_NO_LLM':'1'};workers=[];fails=[]
  for p in lock['panels']:
   x=subprocess.run([sys.executable,str(RUNNER),'--worker'],input=json.dumps(p),cwd=ROOT,env=env,text=True,capture_output=True)
   if x.returncode:fails.append({'panel':p['task']+':'+str(p['worker'])+':'+p['arm'],'stderr':x.stderr[-2000:]})
   else:workers.append(json.loads(x.stdout.strip().splitlines()[-1]))
  after=manifest();checks={'source_stable':after==lock['inputs'] and all(w['source_stable'] for w in workers),'one_hundred_twenty_workers':len(workers)==120,'all_workers_ok':not fails,'query_receipts_valid':all(w['query_receipt_valid'] for w in workers),'task_identity_absent':all(w['task_identity_absent'] for w in workers)}
  report={'schema':'NativeCandidateAdequacyQueryV1_5Capture','lock_sha256':sha(LOCK),'locked_inputs':lock['inputs'],'post_run_inputs':after,'checks':checks,'passed':all(checks.values()),'workers':workers,'failures':fails,'limits':'Fresh 40-panel three-arm run. Native query selection anchors one match on the selected-family edge, filters candidates in graph rules, computes ArgminUnique once per query, and records the selected node. Host ranks row descriptors without task identity; graph rules adjudicate revealed mismatches. Supplied menu only; no grammar invention.'}
  OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps({'passed':report['passed'],'checks':checks,'workers':len(workers),'failures':len(fails),'output':OUT.relative_to(ROOT).as_posix()}));return 0 if report['passed'] else 2
 raise SystemExit('usage: --lock | --run | --worker')
if __name__=='__main__':raise SystemExit(main())

#!/usr/bin/env python3
"""Source-locked necessity probe for the production deferred SetRuleClause rule."""
from __future__ import annotations
import hashlib,json,os,platform,random,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python')]
RUNNER=Path(__file__).resolve();ANALYZER=ROOT/'evaluation/substrate_capability/analyze_thoughtexperiment_deferred_rule_edit_diagnosis_v1.py'
PROTOCOL=ROOT/'docs/research/engine_substrate/THOUGHTEXPERIMENT_DEFERRED_RULE_EDIT_DIAGNOSIS_V1_PREREG_20261005.md';SEED=ROOT/'seeds/self_repair.json'
LOCK=ROOT/'evaluation/substrate_capability/thoughtexperiment_deferred_rule_edit_diagnosis_v1_lock_20261005.json';OUT=ROOT/'evaluation/reports/thoughtexperiment_deferred_rule_edit_diagnosis_v1_20261005.json'
SOURCES=('runners/dsl/Cargo.toml','runners/dsl/Cargo.lock','runners/dsl/src/graph.rs','runners/dsl/src/rewrite.rs','runners/dsl/src/substrate.rs','runners/dsl/src/py.rs','runners/dsl/python/substrate_rs/ext.py','runners/dsl/python/substrate_rs/_native.build.json')
ARMS=('endpoint_blind','endpoint_rematch','target_trace','rule_change_receipt')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def frozen():
 from substrate_rs import _native
 files=(RUNNER,ANALYZER,PROTOCOL,SEED,*(ROOT/x for x in SOURCES));binary=Path(_native.__file__).resolve()
 return {'files':{str(p.relative_to(ROOT)):sha(p) for p in files},'native_binary':{'path':str(binary),'sha256':sha(binary)}}
def fixture(no_cause=False):
 from substrate_rs import Substrate
 seed=json.loads(SEED.read_text());repair=json.loads(json.dumps(next(r for r in seed['rules'] if r['name']=='repair_apply_rule_clause')))
 s=Substrate();target_idx=s._inner.add_rule({'name':'target_rule','match':[['x','probe_link','y']],'where':{'type':'Lit','value':True},'effects':[['set_attr_if_different','x','fired',True]]});meta=s._inner.rule_metadata(target_idx)
 ax=s.add_node('Axis',{'live_clause':{'type':'Lit','value':True}});fault=s.add_node('Fault',{'target_rule':'target_rule','field':'where','corrected':{'type':'Lit','value':False},'applied':1.0 if no_cause else 0.0,'awaiting_synth':0.0});s.add_edge_unchecked(ax,'has_fault',fault);s._inner.add_rule(repair)
 pre=s._inner.graph_to_dict();snap=s._snapshot_with_backend('shared_graph_pages');oracle={'axis':ax.value,'fault':fault.value,'target_idx':target_idx,'target_uid':meta['rule_uid'],'target_revision':meta['revision'],'target_hash':meta['content_hash'],'no_cause':no_cause}
 return s,snap,repair,pre,oracle
def rematch(graph,rule,oracle):
 edges=[(int(e['src']),str(e['type']),int(e['tgt'])) for e in graph['edges']];bindings=[{}]
 for sv,et,tv in rule['match']:
  nxt=[]
  for old in bindings:
   for a,t,b in edges:
    if t!=et:continue
    x=dict(old);ok=True
    for var,nid in ((sv,a),(tv,b)):
     if var in x and x[var]!=nid:ok=False;break
     x[var]=nid
    if ok:nxt.append(x)
  bindings=nxt
 attrs={int(n['id']):n.get('attrs',{}) for n in graph['nodes']};valid=[]
 for b in bindings:
  if b.get('ax')!=oracle['axis'] or b.get('f')!=oracle['fault']:continue
  f=attrs.get(b['f'],{})
  if f.get('applied',0)>=0.5 or f.get('awaiting_synth',0)>=0.5:continue
  valid.append(b)
 if len(valid)!=1:return [],len(valid)
 def mentions_fault(value):
  if isinstance(value,str):return value=='f'
  if isinstance(value,list):return any(mentions_fault(x) for x in value)
  if isinstance(value,dict):return value.get('name')=='f' or any(mentions_fault(x) for x in value.values())
  return False
 return [i for i,e in enumerate(rule['effects']) if mentions_fault(e)],len(valid)
def probe_marker(branch):
 p=branch.add_node('Probe',{});q=branch.add_node('ProbeTarget',{});branch.add_edge_unchecked(p,'probe_link',q)
 branch._inner.run_rules_report(10,False)
 node=next(n for n in branch._inner.graph_to_dict()['nodes'] if n['id']==p.value)
 return bool(node['attrs'].get('fired'))
def run_branch(snapshot,rule,index):
 b=snapshot.fork();variant={**rule,'effects':[e for i,e in enumerate(rule['effects']) if i!=index]}
 if not b._inner.replace_active_rule_by_name('repair_apply_rule_clause',variant):raise RuntimeError('rule replacement refused')
 closure=b._inner.run_rules_report(10,False);marker=probe_marker(b);return marker,closure,b._inner.graph_to_dict()
def execute(arm,rep,no_cause=False):
 s,snap,rule,pre,oracle=fixture(no_cause);primary_hash=digest(pre);rev=tuple(s._inner.experiment_graph_rule_revision());w=snap.fork();t0=time.perf_counter_ns();c0=time.process_time_ns();rematch_count=None
 if arm=='endpoint_blind':report=w._inner.run_rules_delta_report(10,False);candidates=list(range(len(rule['effects'])))
 elif arm=='endpoint_rematch':report=w._inner.run_rules_delta_report(10,False);candidates,rematch_count=rematch(pre,rule,oracle)
 elif arm=='target_trace':
  report=w._inner.run_rules_effect_target_delta_report(10,False);candidates=[]
  for event in report['rule_write_events']:
   if event.get('deferred') and event['rule_name']=='repair_apply_rule_clause':
    for origin in event.get('deferred_effect_origins',[]):
     if any(c['target_rule_uid']==oracle['target_uid'] and c['field']=='where' for c in event.get('deferred_rule_changes',[])):candidates.append(int(origin['effect_index']))
 elif arm=='rule_change_receipt':
  report=w._inner.run_rules_effect_delta_report(10,False);candidates=[]
  for event in report['rule_write_events']:
   if event.get('deferred') and event['rule_name']=='repair_apply_rule_clause':
    for change in event.get('deferred_rule_changes',[]):
     if change['target_rule_uid']==oracle['target_uid'] and change['field']=='where' and change['committed'] and change['revision']>change['previous_revision']:
      candidates.extend(int(o['effect_index']) for o in event.get('deferred_effect_origins',[]))
 outcomes=[];found=None;attempts=0;good_digest=None
 for i in candidates:
  attempts+=1;marker,br,g=run_branch(snap,rule,i);outcomes.append({'effect_index':i,'marker_after_omission':marker,'closure_status':br['status']})
  if marker:found=i;good_digest=digest(g);break
 elapsed=time.perf_counter_ns()-t0;cpu=time.process_time_ns()-c0;primary_after=s._inner.graph_to_dict();after_rev=tuple(s._inner.experiment_graph_rule_revision())
 deferred=[e for e in report['rule_write_events'] if e.get('deferred') and e['rule_name']=='repair_apply_rule_clause']
 target_changes=[c for e in deferred for c in e.get('deferred_rule_changes',[])];target_meta=s._inner.rule_metadata(oracle['target_idx'])
 return {'arm':arm,'replicate':rep,'no_cause':no_cause,'candidates':candidates,'rematch_matches':rematch_count,'attempts':attempts,'found_necessary_effect':found,'outcomes':outcomes,'necessity_branch_digest':good_digest,'wall_ns':elapsed,'cpu_ns':cpu,'status':report['status'],'progress_steps':report['progress_steps'],'deferred_event_count':len(deferred),'deferred_effect_origins':[o for e in deferred for o in e.get('deferred_effect_origins',[])],'deferred_rule_changes':target_changes,'effect_snapshot_objects':report.get('rule_write_effect_snapshot_objects',0),'effect_value_bytes':report.get('rule_write_effect_snapshot_bytes',0),'primary_unchanged':digest(primary_after)==primary_hash and rev==after_rev,'primary_revision_before':rev,'primary_revision_after':after_rev,'target_rule_uid':oracle['target_uid'],'target_rule_revision_after':target_meta['revision'] if target_meta else None}
def worker(i):
 lock=json.loads(LOCK.read_text())['sources'];before=frozen()
 if before!=lock:raise RuntimeError('source lock mismatch before worker')
 arms=list(ARMS);random.Random(4400+i).shuffle(arms);rows=[execute(a,100+i) for a in arms];controls=[execute(a,200+i,True) for a in ARMS];after=frozen()
 if after!=lock:raise RuntimeError('source lock mismatch after worker')
 return {'worker':i,'pid':os.getpid(),'sources_before':before,'sources_after':after,'rows':rows,'no_cause_controls':controls}
def isolated(arm,rep,no_cause=False):
 lock=json.loads(LOCK.read_text())['sources'];before=frozen()
 if before!=lock:raise RuntimeError('source lock mismatch before isolated')
 row=execute(arm,rep,no_cause);after=frozen()
 if after!=lock:raise RuntimeError('source lock mismatch after isolated')
 return {'pid':os.getpid(),'sources_before':before,'sources_after':after,**row}
def main():
 if sys.argv[1:]==['--lock']:
  if LOCK.exists() or OUT.exists():raise SystemExit('refusing to overwrite lock/capture')
  LOCK.write_text(json.dumps({'schema':'ThoughtexperimentDeferredRuleEditDiagnosisV1Lock','sources':frozen(),'workers':3,'isolated_replicates_per_arm':3,'arms':ARMS,'snapshot_backend':'shared_graph_pages'},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return 0
 if len(sys.argv)==3 and sys.argv[1]=='--worker':print(json.dumps(worker(int(sys.argv[2])),sort_keys=True,separators=(',',':')));return 0
 if len(sys.argv)==5 and sys.argv[1]=='--isolated':print(json.dumps(isolated(sys.argv[2],int(sys.argv[3]),sys.argv[4]=='control'),sort_keys=True,separators=(',',':')));return 0
 if sys.argv[1:]!=['--run']:raise SystemExit('usage: --lock | --run | --worker N')
 if frozen()!=json.loads(LOCK.read_text())['sources']:raise SystemExit('source lock mismatch before capture')
 env=dict(os.environ);env['PYTHONPATH']=os.pathsep.join((str(ROOT/'runners/dsl/python'),str(ROOT)));iso=[];workers=[]
 for arm in ARMS:
  for rep in range(3):
   p=subprocess.run([sys.executable,str(RUNNER),'--isolated',arm,str(rep),'main'],cwd=ROOT,env=env,text=True,capture_output=True,timeout=120)
   if p.returncode:raise RuntimeError(f'{arm}/{rep}: {p.stderr[-2500:]}')
   iso.append(json.loads(p.stdout.strip().splitlines()[-1]))
 for i in range(3):
  p=subprocess.run([sys.executable,str(RUNNER),'--worker',str(i)],cwd=ROOT,env=env,text=True,capture_output=True,timeout=180)
  if p.returncode:raise RuntimeError(f'worker/{i}: {p.stderr[-2500:]}')
  workers.append(json.loads(p.stdout.strip().splitlines()[-1]))
 if frozen()!=json.loads(LOCK.read_text())['sources']:raise SystemExit('source lock drift during capture')
 OUT.write_text(json.dumps({'schema':'ThoughtexperimentDeferredRuleEditDiagnosisV1','lock_sha256':sha(LOCK),'host':platform.platform(),'workers':workers,'isolated':iso},indent=2,sort_keys=True)+'\n');print(OUT.relative_to(ROOT));return 0
if __name__=='__main__':raise SystemExit(main())

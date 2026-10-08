#!/usr/bin/env python3
"""Source-locked deferred ApplyRulePatch diagnosis on its production seed rule."""
from __future__ import annotations
import hashlib,json,os,platform,random,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python')]
RUNNER=Path(__file__).resolve();ANALYZER=ROOT/'evaluation/substrate_capability/analyze_thoughtexperiment_deferred_patch_diagnosis_v1.py'
PROTOCOL=ROOT/'docs/research/engine_substrate/THOUGHTEXPERIMENT_DEFERRED_PATCH_DIAGNOSIS_V1_PREREG_20261005.md';SEED=ROOT/'seeds/self_change_reasoning.json'
LOCK=ROOT/'evaluation/substrate_capability/thoughtexperiment_deferred_patch_diagnosis_v1_lock_20261005.json';OUT=ROOT/'evaluation/reports/thoughtexperiment_deferred_patch_diagnosis_v1_20261005.json'
SOURCES=('runners/dsl/Cargo.toml','runners/dsl/Cargo.lock','runners/dsl/src/graph.rs','runners/dsl/src/rewrite.rs','runners/dsl/src/substrate.rs','runners/dsl/src/py.rs','runners/dsl/python/substrate_rs/ext.py','runners/dsl/python/substrate_rs/_native.build.json')
ARMS=('endpoint_blind','endpoint_rematch','target_trace','value_trace');FAULT='refused'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def frozen():
 from substrate_rs import _native
 files=(RUNNER,ANALYZER,PROTOCOL,SEED,*(ROOT/x for x in SOURCES));binary=Path(_native.__file__).resolve()
 return {'files':{str(p.relative_to(ROOT)):sha(p) for p in files},'native_binary':{'path':str(binary),'sha256':sha(binary)}}
def fixture():
 from substrate_rs import Substrate
 seed=json.loads(SEED.read_text());rule=json.loads(json.dumps(next(r for r in seed['rules'] if r['name']=='sc_canary_requests_commit')))
 s=Substrate();idx=s._inner.add_rule({'name':'patch_target','match':[['x','patch_input','y']],'effects':[['set_attr','x','patched',True]]});meta=s._inner.rule_metadata(idx)
 sc=s.add_node('SelfChange',{});patch=s.add_node('RulePatch',{'target_uid':meta['rule_uid'],'expected_revision':999,'expected_content_hash':meta['content_hash'],'field':'where','proposed_clause':False,'state':'selected','status':'pending'});canary=s.add_node('Canary',{'status':'pending'});evidence=s.add_node('CanaryEvidence',{'replicated_gain':5,'protected_regressions':0,'replications':2})
 for a,t,b in ((sc,'selected_patch',patch),(patch,'has_canary',canary),(canary,'has_canary_evidence',evidence)):s.add_edge_unchecked(a,t,b)
 s._inner.add_rule(rule);graph=s._inner.graph_to_dict();snapshot=s._snapshot_with_backend('shared_graph_pages')
 oracle={'sc':sc.value,'patch':patch.value,'canary':canary.value,'evidence':evidence.value,'fault':FAULT,'rule_uid':meta['rule_uid'],'revision':meta['revision'],'content_hash':meta['content_hash']}
 return s,snapshot,rule,graph,oracle
def rematch(graph,rule,oracle):
 edges=[(int(e['src']),str(e['type']),int(e['tgt'])) for e in graph['edges']];bindings=[{}]
 for sv,et,tv in rule['match']:
  nxt=[]
  for old in bindings:
   for a,t,b in edges:
    if t!=et:continue
    bind=dict(old);ok=True
    for var,nid in ((sv,a),(tv,b)):
     if var in bind and bind[var]!=nid:ok=False;break
     bind[var]=nid
    if ok:nxt.append(bind)
  bindings=nxt
 attrs={int(n['id']):n.get('attrs',{}) for n in graph['nodes']};valid=[]
 for b in bindings:
  if b.get('sc')!=oracle['sc'] or b.get('patch')!=oracle['patch'] or b.get('canary')!=oracle['canary'] or b.get('cev')!=oracle['evidence']:continue
  ca=attrs.get(b['canary'],{});ev=attrs.get(b['cev'],{})
  if ca.get('status')!='pending' or ev.get('replicated_gain',0)<5 or ev.get('protected_regressions',0)!=0 or ev.get('replications',0)<2:continue
  valid.append(b)
 candidates=[]
 if len(valid)==1:
  for i,e in enumerate(rule['effects']):
   if 'patch' in e[1:]:candidates.append(i)
 return candidates,len(valid)
def branch(snapshot,rule,index,oracle):
 b=snapshot.fork();variant={**rule,'effects':[e for i,e in enumerate(rule['effects']) if i!=index]}
 if not b._inner.replace_active_rule_by_name('sc_canary_requests_commit',variant):raise RuntimeError('rule replacement refused')
 r=b._inner.run_rules_report(10,False);g=b._inner.graph_to_dict();p=next(n for n in g['nodes'] if int(n['id'])==oracle['patch']);attrs=p['attrs'];edge_set={(int(e['src']),str(e['type']),int(e['tgt'])) for e in g['edges']}
 cured=attrs.get('status')!=FAULT
 healthy=(attrs.get('reason')!='stale_revision' if index!=3 else True) and attrs.get('state')=='transaction_queued' and (oracle['sc'],'has_commit',next((a for a,t,z in edge_set if t=='commits_patch' and z==oracle['patch']),-1)) in edge_set
 return cured,healthy,r,g
def execute(arm,rep):
 s,snap,rule,pre,oracle=fixture();primary_hash=hashlib.sha256(json.dumps(pre,sort_keys=True,separators=(',',':')).encode()).hexdigest();rev_before=tuple(s._inner.experiment_graph_rule_revision());work=snap.fork();t0=time.perf_counter_ns();c0=time.process_time_ns();rematch_count=None
 if arm=='endpoint_blind':report=work._inner.run_rules_delta_report(10,False);candidates=list(range(len(rule['effects'])))
 elif arm=='endpoint_rematch':report=work._inner.run_rules_delta_report(10,False);candidates,rematch_count=rematch(pre,rule,oracle)
 elif arm=='target_trace':
  report=work._inner.run_rules_effect_target_delta_report(10,False);candidates=[]
  for ev in report['rule_write_events']:
   if ev['rule_name']!='sc_canary_requests_commit':continue
   for ef in ev.get('effect_snapshots',[]):
    if oracle['patch'] in ef.get('node_ids',[]) or any(oracle['patch'] in edge for edge in ef.get('edges',[])):candidates.append(int(ef['effect_index']))
  preferred=[]
  for ev in report['rule_write_events']:
   if ev.get('deferred') and ev['rule_name']=='sc_canary_requests_commit':
    preferred.extend(int(o['effect_index']) for o in ev.get('deferred_effect_origins',[]))
  candidates=list(dict.fromkeys(preferred+[i for i in candidates if i not in preferred]))
 elif arm=='value_trace':
  report=work._inner.run_rules_effect_delta_report(10,False);candidates=[]
  for ev in report['rule_write_events']:
   if ev['rule_name']!='sc_canary_requests_commit':continue
   for ef in ev.get('effect_snapshots',[]):
    if any(v['node_id']==oracle['patch'] and v['after'] is not None and v['after']['attrs'].get('status')==FAULT and (v['before'] is None or v['before']['attrs'].get('status')!=FAULT) for v in ef.get('node_values',[])):candidates.append(int(ef['effect_index']))
 found=None;attempts=0;outcomes=[];digest=None
 for i in candidates:
  attempts+=1;cured,healthy,br,bg=branch(snap,rule,i,oracle);gd=hashlib.sha256(json.dumps(bg,sort_keys=True,separators=(',',':')).encode()).hexdigest();outcomes.append({'effect_index':i,'cured':cured,'healthy_survivors':healthy,'status':br['status']})
  if cured:found=i;digest=gd;break
 elapsed=time.perf_counter_ns()-t0;cpu=time.process_time_ns()-c0;primary_after=s._inner.graph_to_dict();rev_after=tuple(s._inner.experiment_graph_rule_revision())
 deferred=[e for e in report['rule_write_events'] if e['deferred'] and 'sc_canary_requests_commit' in e['origin_rules']]
 patch_after=next(n for n in work._inner.graph_to_dict()['nodes'] if int(n['id'])==oracle['patch'])['attrs']
 return {'arm':arm,'replicate':rep,'candidates':candidates,'rematch_matches':rematch_count,'attempts':attempts,'found':found,'outcomes':outcomes,'cured_graph_digest':digest,'wall_ns':elapsed,'cpu_ns':cpu,'report_event_count':len(report['rule_write_events']),'report_json_bytes':len(json.dumps(report['rule_write_events'],sort_keys=True,separators=(',',':')).encode()),'effect_snapshot_objects':report.get('rule_write_effect_snapshot_objects',0),'effect_value_bytes':report.get('rule_write_effect_snapshot_bytes',0),'effect_truncated':report.get('rule_write_effect_snapshots_truncated',0),'deferred_event_count':len(deferred),'deferred_effect_origins':[o for e in deferred for o in e.get('deferred_effect_origins',[])],'deferred_effect_snapshots':[x for e in deferred for x in e.get('effect_snapshots',[])],'patch_status':patch_after.get('status'),'patch_reason':patch_after.get('reason'),'status':report['status'],'progress_steps':report['progress_steps'],'primary_unchanged':hashlib.sha256(json.dumps(primary_after,sort_keys=True,separators=(',',':')).encode()).hexdigest()==primary_hash and rev_before==rev_after,'primary_revision_before':rev_before,'primary_revision_after':rev_after}
def worker(i):
 locked=json.loads(LOCK.read_text())['sources'];before=frozen()
 if before!=locked:raise RuntimeError('source lock mismatch before worker')
 arms=list(ARMS);random.Random(9000+i).shuffle(arms);rows=[execute(a,100+i) for a in arms];after=frozen()
 if after!=locked:raise RuntimeError('source lock mismatch after worker')
 return {'worker':i,'pid':os.getpid(),'sources_before':before,'sources_after':after,'rows':rows}
def isolated(arm,rep):
 locked=json.loads(LOCK.read_text())['sources'];before=frozen()
 if before!=locked:raise RuntimeError('source lock mismatch before isolated run')
 row=execute(arm,rep);after=frozen()
 if after!=locked:raise RuntimeError('source lock mismatch after isolated run')
 return {'pid':os.getpid(),'sources_before':before,'sources_after':after,**row}
def main():
 if sys.argv[1:]==['--lock']:
  if LOCK.exists() or OUT.exists():raise SystemExit('refusing to overwrite lock/capture')
  LOCK.write_text(json.dumps({'schema':'ThoughtexperimentDeferredPatchDiagnosisV1Lock','sources':frozen(),'workers':3,'isolated_replicates_per_arm':3,'arms':ARMS,'snapshot_backend':'shared_graph_pages'},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return 0
 if len(sys.argv)==3 and sys.argv[1]=='--worker':print(json.dumps(worker(int(sys.argv[2])),sort_keys=True,separators=(',',':')));return 0
 if len(sys.argv)==4 and sys.argv[1]=='--isolated':print(json.dumps(isolated(sys.argv[2],int(sys.argv[3])),sort_keys=True,separators=(',',':')));return 0
 if sys.argv[1:]!=['--run']:raise SystemExit('usage: --lock | --run | --worker N')
 if frozen()!=json.loads(LOCK.read_text())['sources']:raise SystemExit('source lock mismatch before capture')
 env=dict(os.environ);env['PYTHONPATH']=os.pathsep.join((str(ROOT/'runners/dsl/python'),str(ROOT)));iso=[];workers=[]
 for arm in ARMS:
  for rep in range(3):
   p=subprocess.run([sys.executable,str(RUNNER),'--isolated',arm,str(rep)],cwd=ROOT,env=env,text=True,capture_output=True,timeout=120)
   if p.returncode:raise RuntimeError(f'{arm}/{rep}: {p.stderr[-2500:]}')
   iso.append(json.loads(p.stdout.strip().splitlines()[-1]))
 for i in range(3):
  p=subprocess.run([sys.executable,str(RUNNER),'--worker',str(i)],cwd=ROOT,env=env,text=True,capture_output=True,timeout=120)
  if p.returncode:raise RuntimeError(f'worker/{i}: {p.stderr[-2500:]}')
  workers.append(json.loads(p.stdout.strip().splitlines()[-1]))
 if frozen()!=json.loads(LOCK.read_text())['sources']:raise SystemExit('source lock drift during capture')
 OUT.write_text(json.dumps({'schema':'ThoughtexperimentDeferredPatchDiagnosisV1','lock_sha256':sha(LOCK),'host':platform.platform(),'workers':workers,'isolated':iso},indent=2,sort_keys=True)+'\n');print(OUT.relative_to(ROOT));return 0
if __name__=='__main__':raise SystemExit(main())

#!/usr/bin/env python3
"""External snapshot reconstruction baseline for rule-event value attribution."""
from __future__ import annotations
import hashlib,json,os,platform,resource,subprocess,sys,time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python')]
OVERRIDE=os.environ.get('OCELot_NATIVE_IMPORT_ROOT')
if OVERRIDE:sys.path.insert(0,OVERRIDE)
RUNNER=Path(__file__).resolve();PROTOCOL=ROOT/'docs/research/engine_substrate/THOUGHTEXPERIMENT_EVENT_VALUE_ATTRIBUTION_V1_2_6_PREREG_20261005.md';ANALYZER=ROOT/'evaluation/substrate_capability/analyze_thoughtexperiment_event_value_attribution_v1_2_6.py';LOCK=ROOT/'evaluation/substrate_capability/thoughtexperiment_event_value_attribution_v1_2_6_lock_20261005.json';OUT=ROOT/'evaluation/reports/thoughtexperiment_event_value_attribution_v1_2_6_20261005.json'
SOURCES=('runners/dsl/src/graph.rs','runners/dsl/src/rewrite.rs','runners/dsl/src/substrate.rs','runners/dsl/src/py.rs','runners/dsl/python/substrate_rs/ext.py','runners/dsl/python/substrate_rs/__init__.py','runners/dsl/python/substrate_rs/_native.build.json','runners/dsl/Cargo.lock')
WORKERS=3
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def frozen():
 from substrate_rs import _native
 files=(RUNNER,PROTOCOL,ANALYZER,*(ROOT/x for x in SOURCES));binary=Path(_native.__file__).resolve()
 return {'files':{str(p.relative_to(ROOT)):sha(p) for p in files},'native_binary':{'path':str(binary),'sha256':sha(binary)}}
def make_case(kind):
 from substrate_rs import Substrate
 s=Substrate()
 if kind=='direct':
  a=s.add_node('A',{'initial':1});b=s.add_node('B',{});s.add_edge_unchecked(a,'input',b)
  s._inner.add_rule({'name':'direct_writer','match':[['x','input','y']],'effects':[['set_attr','x','observed',True],['add_edge','x','derived','y',{}]]})
 elif kind=='deferred':
  prev=[s.add_node('PrevPercept',{'feat':[0.0,0.0]}),s.add_node('PrevPercept',{'feat':[9.0,9.0]})]
  cur=[s.add_node('CurPercept',{'feat':[0.05,0.05]}),s.add_node('CurPercept',{'feat':[9.05,9.05]}),s.add_node('CurPercept',{'feat':[500.0,500.0]})]
  a=s.add_node('Anchor',{});s.add_edge_unchecked(a,'has_anchor',a)
  s._inner.add_rule({'name':'trans_frame_identity_assignment','match':[['a','has_anchor','a']],'effects':[['track_identity',{'__term__':{'type':'NodesOfType','node_type':'PrevPercept'}},{'__term__':{'type':'NodesOfType','node_type':'CurPercept'}},'feat',None,None,'identity',1.0]]})
  s._inner.add_rule({'name':'trace_direct_control','match':[['a','has_anchor','a']],'effects':[['set_attr','a','direct_probe',True]]})
 elif kind=='overlap':
  a=s.add_node('A',{'value':0});b=s.add_node('B',{});s.add_edge_unchecked(a,'input',b)
  for name,value in (('writer_one',1),('writer_two',2)):
   s._inner.add_rule({'name':name,'match':[['x','input','y']],'effects':[['set_attr','x','value',value]]})
 elif kind=='byte_cap':
  a=s.add_node('A',{'payload':list(range(20000)),'value':0});b=s.add_node('B',{});s.add_edge_unchecked(a,'input',b)
  s._inner.add_rule({'name':'oversize_writer','match':[['x','input','y']],'effects':[['set_attr','x','value',1]]})
 elif kind=='object_cap':
  for _ in range(520):
   a=s.add_node('A',{});b=s.add_node('B',{});s.add_edge_unchecked(a,'input',b)
  s._inner.add_rule({'name':'many_object_writer','match':[['x','input','y']],'effects':[['set_attr','x','added',1]]})
 elif kind=='direct_deferred_overlap':
  s.add_node('PrevPercept',{'feat':[0.0,0.0]})
  cur=s.add_node('CurPercept',{'feat':[0.05,0.05]})
  anchor=s.add_node('Anchor',{});s.add_edge_unchecked(anchor,'has_anchor',anchor);s.add_edge_unchecked(anchor,'direct_target',cur)
  s._inner.add_rule({'name':'identity_deferred','match':[['a','has_anchor','a']],'effects':[['track_identity',{'__term__':{'type':'NodesOfType','node_type':'PrevPercept'}},{'__term__':{'type':'NodesOfType','node_type':'CurPercept'}},'feat',None,None,'identity',1.0]]})
  s._inner.add_rule({'name':'identity_direct','match':[['a','has_anchor','a'],['a','direct_target','c']],'effects':[['set_attr','c','identity',99]]})
 elif kind=='report_object_cap':
  for group in range(33):
   edge_type=f'input_{group:02d}'
   for _ in range(512):
    a=s.add_node('A',{});b=s.add_node('B',{});s.add_edge_unchecked(a,edge_type,b)
   s._inner.add_rule({'name':f'bulk_writer_{group:02d}','match':[['x',edge_type,'y']],'effects':[['set_attr','x',f'added_{group:02d}',1]]})
 else:raise ValueError(kind)
 return s
def value_changes(before,after):
 def nodes(g):return {int(n['id']):n for n in g['nodes']}
 def edges(g):return {(int(e['src']),str(e['type']),int(e['tgt'])):e.get('attrs',{}) for e in g['edges']}
 bnodes,anodes=nodes(before),nodes(after);out=[]
 for nid in sorted(set(bnodes)|set(anodes)):
  b,a=bnodes.get(nid),anodes.get(nid)
  if b is None or a is None:out.append({'entity':'node','id':nid,'field':'existence','before':b,'after':a});continue
  if b['type']!=a['type']:out.append({'entity':'node','id':nid,'field':'type','before':b['type'],'after':a['type']})
  ba,aa=b.get('attrs',{}),a.get('attrs',{})
  for k in sorted(set(ba)|set(aa)):
   if ba.get(k,'<ABSENT>')!=aa.get(k,'<ABSENT>'):out.append({'entity':'node','id':nid,'field':'attr:'+k,'before':ba.get(k,'<ABSENT>'),'after':aa.get(k,'<ABSENT>')})
 be,ae=edges(before),edges(after)
 for key in sorted(set(be)|set(ae)):
  b,a=be.get(key),ae.get(key)
  if b is None or a is None:out.append({'entity':'edge','key':list(key),'field':'existence','before':b,'after':a});continue
  for k in sorted(set(b)|set(a)):
   if b.get(k,'<ABSENT>')!=a.get(k,'<ABSENT>'):out.append({'entity':'edge','key':list(key),'field':'attr:'+k,'before':b.get(k,'<ABSENT>'),'after':a.get(k,'<ABSENT>')})
 return out
def targets(e):return set(map(int,e['node_ids'])),{(int(x[0]),str(x[1]),int(x[2])) for x in e['edges']}
def execute():
 from substrate_rs import Substrate
 rows=[]
 for kind in ('direct','deferred','overlap','byte_cap','object_cap','direct_deferred_overlap','report_object_cap'):
  progress_budget=40 if kind=='report_object_cap' else (10 if kind=='direct_deferred_overlap' else 3)
  graphs={};reports={};measurements={}
  for mode,method in [('plain','run_rules_report'),('traced','run_rules_delta_report'),('exact','run_rules_snapshot_delta_report')]:
   s=make_case(kind);before=s._inner.graph_to_dict();wall0=time.perf_counter();cpu0=time.process_time();report=getattr(s._inner,method)(progress_budget,False);cpu=time.process_time()-cpu0;wall=time.perf_counter()-wall0;after=s._inner.graph_to_dict();graphs[mode]=(before,after);reports[mode]=report
   measurements[mode]={'wall_seconds':wall,'cpu_seconds':cpu,'event_snapshot_json_bytes':len(json.dumps(report.get('rule_write_events',[]),sort_keys=True,separators=(',',':')).encode()),'snapshot_bytes_estimated':report.get('rule_write_snapshot_bytes_estimated',0),'snapshot_byte_budget':report.get('rule_write_snapshot_budget_bytes',0),'snapshot_objects':report.get('rule_write_snapshot_objects',0),'snapshot_object_budget':report.get('rule_write_snapshot_budget_objects',0),'snapshot_event_byte_budget':report.get('rule_write_event_snapshot_budget_bytes',0),'snapshot_event_object_budget':report.get('rule_write_event_snapshot_budget_objects',0),'snapshots_truncated':report.get('rule_write_snapshots_truncated',0)}
  b,a=graphs['traced'];changes=value_changes(b,a);events=reports['traced']['rule_write_events'];assignments=[]
  if kind!='report_object_cap':
   for change in changes:
    candidates=[]
    for index,event in enumerate(events):
     if not event['progressed']:continue
     ns,es=targets(event)
     covered=(int(change['id']) in ns) if change['entity']=='node' else tuple(change['key']) in es
     if covered:candidates.append(index)
    assignments.append({'change':change,'candidate_event_indices':candidates,'attributed_event_index':candidates[0] if len(candidates)==1 else None,'status':'unique' if len(candidates)==1 else ('ambiguous' if candidates else 'uncovered')})
  rows.append({'fixture':kind,'progress_budget':progress_budget,'summaries':{mode:{k:reports[mode][k] for k in ('status','progress_steps','passes_completed')} for mode in reports},'mode_measurements':measurements,'graph_snapshots':{mode:{'before':pair[0],'after':pair[1]} for mode,pair in graphs.items()},'events':events,'changes':changes,'assignments':assignments,'dropped_events':int(reports['traced']['rule_write_events_dropped']),'truncated_events':int(reports['traced']['rule_write_snapshots_truncated']),'snapshot_bytes_budget':int(reports['traced']['rule_write_snapshot_budget_bytes']),'snapshot_objects_budget':int(reports['traced']['rule_write_snapshot_budget_objects'])})
 return rows
def worker(i):
 expected=json.loads(LOCK.read_text())['sources'];before=frozen()
 if before!=expected:raise RuntimeError('source/native lock mismatch before worker')
 rows=execute();after=frozen()
 if after!=expected:raise RuntimeError('source/native lock mismatch after worker')
 return {'worker_index':i,'pid':os.getpid(),'max_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'sources_before':before,'sources_after':after,'fixtures':rows}
def main():
 if len(sys.argv)==3 and sys.argv[1]=='--worker':print(json.dumps(worker(int(sys.argv[2])),sort_keys=True,separators=(',',':')));return 0
 if sys.argv[1:]==['--lock']:
  if LOCK.exists() or OUT.exists():raise SystemExit('refusing to overwrite lock/capture')
  LOCK.write_text(json.dumps({'schema':'ThoughtexperimentEventValueAttributionV1_2_6Lock','sources':frozen(),'workers':WORKERS,'progress_budget':3,'direct_deferred_overlap_progress_budget':10,'report_object_cap_progress_budget':40},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return 0
 if sys.argv[1:]!=['--run']:raise SystemExit('usage: --lock | --run | --worker N')
 lock=json.loads(LOCK.read_text())
 if frozen()!=lock['sources']:raise SystemExit('source/native lock mismatch before run')
 env=dict(os.environ);env['PYTHONPATH']=os.pathsep.join(filter(None,(OVERRIDE,str(ROOT/'runners/dsl/python'),str(ROOT))));workers=[]
 for i in range(WORKERS):
  p=subprocess.run([sys.executable,str(RUNNER),'--worker',str(i)],cwd=ROOT,env=env,text=True,capture_output=True,timeout=180)
  if p.returncode:raise RuntimeError(f'worker {i} failed: {p.stderr[-2000:]}')
  workers.append(json.loads(p.stdout.strip().splitlines()[-1]))
 if frozen()!=lock['sources']:raise SystemExit('source/native drift during run')
 report={'schema':'ThoughtexperimentEventValueAttributionV1_2_6','lock_sha256':sha(LOCK),'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'host':platform.platform(),'workers':workers};OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(OUT.relative_to(ROOT));return 0
if __name__=='__main__':raise SystemExit(main())

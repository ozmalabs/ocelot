#!/usr/bin/env python3
"""External snapshot reconstruction baseline for rule-event value attribution."""
from __future__ import annotations
import hashlib,json,os,platform,resource,subprocess,sys,time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python')]
OVERRIDE=os.environ.get('OCELot_NATIVE_IMPORT_ROOT')
if OVERRIDE:sys.path.insert(0,OVERRIDE)
RUNNER=Path(__file__).resolve();PROTOCOL=ROOT/'docs/research/engine_substrate/THOUGHTEXPERIMENT_EVENT_VALUE_ATTRIBUTION_V1_2_13_PREREG_20261005.md';ANALYZER=ROOT/'evaluation/substrate_capability/analyze_thoughtexperiment_event_value_attribution_v1_2_13.py';LOCK=ROOT/'evaluation/substrate_capability/thoughtexperiment_event_value_attribution_v1_2_13_lock_20261005.json';OUT=ROOT/'evaluation/reports/thoughtexperiment_event_value_attribution_v1_2_13_20261005.json'
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
 elif kind=='same_event_multiwrite':
  a=s.add_node('A',{'value':0});b=s.add_node('B',{});s.add_edge_unchecked(a,'input',b)
  s._inner.add_rule({'name':'multiwrite_then_remove','match':[['x','input','y']],'effects':[['set_attr','x','value',1],['set_attr','x','value',2],['del_edge','x','input','y']]})
 elif kind=='depth_cap':
  payload=0
  for _ in range(140): payload=[payload]
  a=s.add_node('A',{'payload':payload});b=s.add_node('B',{});s.add_edge_unchecked(a,'input',b)
  s._inner.add_rule({'name':'deep_writer','match':[['x','input','y']],'effects':[['set_attr','x','written',True]]})
 elif kind=='edge_mutation':
  a=s.add_node('A',{});b=s.add_node('B',{});s.add_edge_unchecked(a,'link',b,{'state':0})
  s._inner.add_rule({'name':'edge_relabel','match':[['x','link','y']],'effects':[['add_edge','x','link','y',{'state':1}]]})
  s._inner.add_rule({'name':'edge_remove','match':[['x','link','y']],'effects':[['del_edge','x','link','y']]})
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
 for kind in ('direct','deferred','overlap','byte_cap','depth_cap','edge_mutation','same_event_multiwrite','object_cap','direct_deferred_overlap','report_object_cap'):
  progress_budget=40 if kind=='report_object_cap' else (10 if kind=='direct_deferred_overlap' else 3)
  graphs={};reports={};measurements={}
  for mode,method in [('plain','run_rules_report'),('traced','run_rules_delta_report'),('exact','run_rules_snapshot_delta_report'),('combined',None)]:
   s=make_case(kind)
   if mode=='combined':
    s._inner.begin_experiment_delta_journal_with_rule_attribution()
    journal_start=s._inner.graph_to_dict()
    if kind=='same_event_multiwrite': s.add_node('HypothesisAssumption',{'authored':True})
    s._inner.checkpoint_experiment_delta_journal()
    before=s._inner.graph_to_dict()
   else:
    if kind=='same_event_multiwrite': s.add_node('HypothesisAssumption',{'authored':True})
    before=s._inner.graph_to_dict();journal_start=before
   wall0=time.perf_counter();cpu0=time.process_time()
   if mode=='combined':
    settlement=s._inner.run_rules_report(progress_budget,False)
    report=dict(settlement);report.update(s._inner.finish_experiment_delta_journal())
   else:
    report=getattr(s._inner,method)(progress_budget,False)
   cpu=time.process_time()-cpu0;wall=time.perf_counter()-wall0;after=s._inner.graph_to_dict();graphs[mode]=(before,after);reports[mode]=report
   if mode=='combined':
    report['snapshot_graph_diff_matches_conclusions']=report['conclusions']==s._inner.graph_diff(journal_start,after)
    report['snapshot_graph_diff_matches_derived_only']=report['derived_only']==s._inner.graph_diff(before,after)
   measurements[mode]={'wall_seconds':wall,'cpu_seconds':cpu,'event_snapshot_json_bytes':len(json.dumps(report.get('rule_write_events',[]),sort_keys=True,separators=(',',':')).encode()),'snapshot_bytes_estimated':report.get('rule_write_snapshot_bytes_estimated',0),'snapshot_byte_budget':report.get('rule_write_snapshot_budget_bytes',0),'snapshot_objects':report.get('rule_write_snapshot_objects',0),'snapshot_object_budget':report.get('rule_write_snapshot_budget_objects',0),'snapshot_event_byte_budget':report.get('rule_write_event_snapshot_budget_bytes',0),'snapshot_event_object_budget':report.get('rule_write_event_snapshot_budget_objects',0),'snapshots_truncated':report.get('rule_write_snapshots_truncated',0),'effect_snapshot_bytes':report.get('rule_write_effect_snapshot_bytes',0),'effect_snapshot_objects':report.get('rule_write_effect_snapshot_objects',0),'effect_snapshots_truncated':report.get('rule_write_effect_snapshots_truncated',0)}
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
  rows.append({'fixture':kind,'progress_budget':progress_budget,'combined_snapshot_graph_diff_matches_conclusions':reports['combined']['snapshot_graph_diff_matches_conclusions'],'combined_snapshot_graph_diff_matches_derived_only':reports['combined']['snapshot_graph_diff_matches_derived_only'],'combined_conclusions':reports['combined']['conclusions'],'combined_events':reports['combined']['rule_write_events'],'combined_derived_only':reports['combined']['derived_only'],'summaries':{mode:{k:reports[mode][k] for k in ('status','progress_steps','passes_completed')} for mode in reports},'mode_measurements':measurements,'graph_snapshots':{mode:{'before':pair[0],'after':pair[1]} for mode,pair in graphs.items()},'events':events,'changes':changes,'assignments':assignments,'dropped_events':int(reports['traced']['rule_write_events_dropped']),'truncated_events':int(reports['traced']['rule_write_snapshots_truncated']),'snapshot_bytes_budget':int(reports['traced']['rule_write_snapshot_budget_bytes']),'snapshot_objects_budget':int(reports['traced']['rule_write_snapshot_budget_objects'])})
 return rows
def process_memory_kib():
 values={}
 try:
  for line in Path('/proc/self/smaps_rollup').read_text().splitlines():
   if line.startswith(('Rss:','Pss:')):
    key,val,*_=line.split();values[key[:-1].lower()+'_kib']=int(val)
 except OSError: pass
 return values
def isolated_arm(fixture,mode,rep):
 from substrate_rs import Substrate
 s=make_case(fixture); progress_budget=40 if fixture=='report_object_cap' else (10 if fixture=='direct_deferred_overlap' else 3)
 if mode=='combined':
  s._inner.begin_experiment_delta_journal_with_rule_attribution()
  if fixture=='same_event_multiwrite': s.add_node('HypothesisAssumption',{'authored':True})
  s._inner.checkpoint_experiment_delta_journal()
  baseline_memory=process_memory_kib()
  t0=time.perf_counter();c0=time.process_time();settlement=s._inner.run_rules_report(progress_budget,False);journal=s._inner.finish_experiment_delta_journal();cpu=time.process_time()-c0;wall=time.perf_counter()-t0
  report=dict(settlement);report.update(journal)
 else:
  if fixture=='same_event_multiwrite': s.add_node('HypothesisAssumption',{'authored':True})
  method={'plain':'run_rules_report','traced':'run_rules_delta_report','exact':'run_rules_snapshot_delta_report'}[mode]
  baseline_memory=process_memory_kib()
  t0=time.perf_counter();c0=time.process_time();report=getattr(s._inner,method)(progress_budget,False);cpu=time.process_time()-c0;wall=time.perf_counter()-t0
 final_memory=process_memory_kib()
 return {'fixture':fixture,'mode':mode,'replicate':rep,'pid':os.getpid(),'baseline_memory_kib':baseline_memory,'final_memory_kib':final_memory,'memory_delta_kib':{k:final_memory[k]-baseline_memory[k] for k in baseline_memory.keys()&final_memory.keys()},'max_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'status':report['status'],'progress_steps':report['progress_steps'],'passes_completed':report['passes_completed'],'event_count':len(report.get('rule_write_events',[])),'event_snapshot_json_bytes':len(json.dumps(report.get('rule_write_events',[]),sort_keys=True,separators=(',',':')).encode()),'snapshot_payload_bytes':report.get('rule_write_snapshot_bytes_estimated',0),'snapshot_objects':report.get('rule_write_snapshot_objects',0),'effect_snapshot_payload_bytes':report.get('rule_write_effect_snapshot_bytes',0),'effect_snapshot_objects':report.get('rule_write_effect_snapshot_objects',0),'effect_snapshots_truncated':report.get('rule_write_effect_snapshots_truncated',0),'wall_seconds':wall,'cpu_seconds':cpu}
def isolated_worker(fixture,mode,rep):
 expected=json.loads(LOCK.read_text())['sources'];before=frozen()
 if before!=expected:raise RuntimeError('source/native lock mismatch before isolated arm')
 row=isolated_arm(fixture,mode,rep);after=frozen()
 if after!=expected:raise RuntimeError('source/native lock mismatch after isolated arm')
 return {'sources_before':before,'sources_after':after,**row}
def worker(i):
 expected=json.loads(LOCK.read_text())['sources'];before=frozen()
 if before!=expected:raise RuntimeError('source/native lock mismatch before worker')
 rows=execute();after=frozen()
 if after!=expected:raise RuntimeError('source/native lock mismatch after worker')
 return {'worker_index':i,'pid':os.getpid(),'max_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'sources_before':before,'sources_after':after,'fixtures':rows}
def main():
 if len(sys.argv)==3 and sys.argv[1]=='--worker':print(json.dumps(worker(int(sys.argv[2])),sort_keys=True,separators=(',',':')));return 0
 if len(sys.argv)==5 and sys.argv[1]=='--isolated-worker':print(json.dumps(isolated_worker(sys.argv[2],sys.argv[3],int(sys.argv[4])),sort_keys=True,separators=(',',':')));return 0
 if sys.argv[1:]==['--lock']:
  if LOCK.exists() or OUT.exists():raise SystemExit('refusing to overwrite lock/capture')
  LOCK.write_text(json.dumps({'schema':'ThoughtexperimentEventValueAttributionV1_2_13Lock','sources':frozen(),'workers':WORKERS,'progress_budget':3,'direct_deferred_overlap_progress_budget':10,'report_object_cap_progress_budget':40},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return 0
 if sys.argv[1:]!=['--run']:raise SystemExit('usage: --lock | --run | --worker N')
 lock=json.loads(LOCK.read_text())
 if frozen()!=lock['sources']:raise SystemExit('source/native lock mismatch before run')
 env=dict(os.environ);env['PYTHONPATH']=os.pathsep.join(filter(None,(OVERRIDE,str(ROOT/'runners/dsl/python'),str(ROOT))));
 isolated=[]
 for fixture in ('direct','same_event_multiwrite','report_object_cap'):
  for mode in ('plain','traced','exact','combined'):
   for rep in range(3):
    p=subprocess.run([sys.executable,str(RUNNER),'--isolated-worker',fixture,mode,str(rep)],cwd=ROOT,env=env,text=True,capture_output=True,timeout=180)
    if p.returncode:raise RuntimeError(f'isolated {fixture}/{mode}/{rep} failed: {p.stderr[-2000:]}')
    isolated.append(json.loads(p.stdout.strip().splitlines()[-1]))

 workers=[]
 for i in range(WORKERS):
  p=subprocess.run([sys.executable,str(RUNNER),'--worker',str(i)],cwd=ROOT,env=env,text=True,capture_output=True,timeout=180)
  if p.returncode:raise RuntimeError(f'worker {i} failed: {p.stderr[-2000:]}')
  workers.append(json.loads(p.stdout.strip().splitlines()[-1]))
 if frozen()!=lock['sources']:raise SystemExit('source/native drift during run')
 report={'schema':'ThoughtexperimentEventValueAttributionV1_2_13','lock_sha256':sha(LOCK),'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'host':platform.platform(),'workers':workers,'isolated_arm_captures':isolated};OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(OUT.relative_to(ROOT));return 0
if __name__=='__main__':raise SystemExit(main())

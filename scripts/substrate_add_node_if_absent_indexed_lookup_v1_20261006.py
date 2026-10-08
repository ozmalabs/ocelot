#!/usr/bin/env python3
"""Locked scan-vs-declared-index experiment for AddNodeIfAbsent."""
from __future__ import annotations
import gzip,hashlib,importlib.util,json,os,platform,resource,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python'),str(ROOT/'scripts')]
PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_ADD_NODE_IF_ABSENT_INDEXED_LOOKUP_V1_PREREG_20261006.md'
RUNNER=Path(__file__).resolve();HARVEST=ROOT/'evaluation/substrate_capability/live_conversation_task_graph_harvest_v2.py'
HARVEST_ANALYZER=ROOT/'evaluation/substrate_capability/analyze_live_conversation_task_graph_harvest_v2.py'
ANALYZER=ROOT/'scripts/analyze_substrate_add_node_if_absent_indexed_lookup_v1_20261006.py'
SOURCES=['runners/dsl/src/graph.rs','runners/dsl/src/rewrite.rs','runners/dsl/src/access_trace.rs','seeds/slang_lexicon.json','scripts/arc_self_report.py']
LOCK=ROOT/'evaluation/substrate_capability/add_node_if_absent_indexed_lookup_v1_20261006_lock.json'
OUTDIR=ROOT/'evaluation/reports/add_node_if_absent_indexed_lookup_v1_20261006';CAPTURE=OUTDIR/'capture.json.gz'
SIZES=[512,4096,7164,16384];COUNTS=[1,15,64];TIMING_REPS=5;TRACE_REP=5
LIVE_ROUTE='unknown_word_clarification';LIVE_REPS=5
def sha(p):return 'sha256:'+hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(path,name):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def inputs():
 from substrate_rs import _native
 from domains.engine_provenance import engine_provenance
 h=load(HARVEST,'add_node_harvest_lock')
 return {'schema':1,'protocol_sha256':sha(PROTOCOL),'runner_sha256':sha(RUNNER),'analyzer_sha256':sha(ANALYZER),'sources':{p:sha(ROOT/p) for p in SOURCES},
  'native_extension_sha256':sha(Path(_native.__file__).resolve()),'native_build_record_sha256':sha(Path(_native.__file__).resolve().with_name('_native.build.json')),
  'engine_provenance_sha256':hashlib.sha256(json.dumps(engine_provenance(str(ROOT)),sort_keys=True,default=str,separators=(',',':')).encode()).hexdigest(),
  'harvest_inputs':h.inputs(),'scale_schedule':{'N':SIZES,'M':COUNTS,'timing_reps':TIMING_REPS,'trace_replicate':TRACE_REP},
  'live_route':{'condition':LIVE_ROUTE,'replicates':LIVE_REPS}}
def term_attr(node,key):return {'__term__':{'type':'Attr','node':{'type':'Var','name':node},'key':key}}
def term_lit(value):return {'__term__':{'type':'Lit','value':value}}
def nid(value):return int(value.value if hasattr(value,'value') else value)
def add_effect_rule(inner,values,attrs=None):
 root=inner.add_node('LexiconRoot',{})
 inner.add_rule({'name':'indexed_lookup_probe','match':[['root','knows_variant','v']],
  'where':{'type':'Not','arg':{'type':'Exists','var_name':'_found','predicate':{'type':'Lit','value':True},
   'source':{'type':'Neighbours','node':{'type':'Var','name':'v'},'edge_type':'denotes','any_type':False}}},
  'effects':[['add_node_if_absent','concept','Concept',attrs if attrs is not None else {'name':term_attr('v','denotes_name')}],['add_edge','v','denotes','concept']]})
 for i,value in enumerate(values):
  v=inner.add_node('SlangVariant',{'denotes_name':value});inner.add_edge_unchecked(root,'knows_variant',v,{})
 return root
 return root
def make_scale_graph(n,m):
 from substrate_rs import Substrate
 sub=Substrate();inner=sub._inner
 hit_count=(m*4)//5
 values=[f'word_{i:04d}' for i in range(m)]
 # All matching witnesses come after unique distractors, maximizing the
 # ordered reference scan while preserving the 12-hit/3-miss live composition.
 for i in range(n-hit_count):inner.add_node('Concept',{'name':f'distractor_{i:06d}'})
 for value in values[:hit_count]:inner.add_node('Concept',{'name':value,'fixture_extra':'subset-match'})
 add_effect_rule(inner,values)
 return sub,values,hit_count
def digest_graph(inner):return hashlib.sha256(json.dumps(inner.graph_to_dict(),sort_keys=True,separators=(',',':'),default=str).encode()).hexdigest()
def current_rss_bytes():
 try:
  for line in Path('/proc/self/status').read_text().splitlines():
   if line.startswith('VmRSS:'):return int(line.split()[1])*1024
 except OSError:pass
 return None
def run_arm(inner,trace):
 if trace:inner.runtime_access_trace_set_enabled(False);inner.runtime_access_trace_reset();inner.runtime_access_trace_set_enabled(True)
 w0=time.perf_counter_ns();c0=time.process_time_ns();progress=inner.run_rules(10000);wall=time.perf_counter_ns()-w0;cpu=time.process_time_ns()-c0
 trace_data=None
 if trace:
  inner.runtime_access_trace_set_enabled(False);rows,dropped=inner.runtime_access_trace_snapshot();kinds={}
  for _,kind,_,_,_,count in rows:kinds[str(kind)]=kinds.get(str(kind),0)+int(count)
  trace_data={'event_count':sum(kinds.values()),'distinct_rows':len(rows),'dropped':int(dropped),'counts_by_kind':dict(sorted(kinds.items()))}
 graph=inner.graph_to_dict();nodes={int(x['id']):x for x in graph.get('nodes',[])};edges=graph.get('edges',[])
 variants=[int(x['id']) for x in graph.get('nodes',[]) if x['type']=='SlangVariant'];selected={}
 for vid in variants:
  tgts=[int(e['tgt']) for e in edges if int(e['src'])==vid and e['type']=='denotes']
  selected[str(vid)]=tgts
 return {'closure_wall_ns':wall,'closure_process_cpu_ns':cpu,'progress':int(progress),'final_graph_digest':digest_graph(inner),
  'node_count':len(graph.get('nodes',[])),'edge_count':len(edges),'selected_concept_ids':selected,'trace':trace_data,
  'all_selected_nodes_exist':all(n in nodes for ts in selected.values() for n in ts)}
def fork(inner):
 w=time.perf_counter_ns();c=time.process_time_ns();branch=inner.fork_shared_graph_pages_experiment();return branch,time.perf_counter_ns()-w,time.process_time_ns()-c
def scale_worker(n,m,rep,diagnostic):
 from domains.engine_provenance import assert_measuring_engine
 assert_measuring_engine();before=inputs();sub,values,hits=make_scale_graph(n,m);parent=sub._inner;rss={'base_graph_bytes':current_rss_bytes()}
 ref,ref_fork_wall,ref_fork_cpu=fork(parent)
 idx_template,idx_template_fork_wall,idx_template_fork_cpu=fork(parent)
 rss['after_unindexed_forks_bytes']=current_rss_bytes()
 w=time.perf_counter_ns();c=time.process_time_ns();idx_template.declare_attr_index('Concept','name');index_build_wall=time.perf_counter_ns()-w;index_build_cpu=time.process_time_ns()-c
 rss['after_index_build_bytes']=current_rss_bytes()
 indexed,idx_fork_wall,idx_fork_cpu=fork(idx_template)
 rss['after_indexed_fork_bytes']=current_rss_bytes()
 if rep%2==0:order=['reference','indexed']
 else:order=['indexed','reference']
 results={}
 for arm in order:results[arm]=run_arm(ref if arm=='reference' else indexed,diagnostic)
 rss['after_closure_bytes']=current_rss_bytes();rss['process_peak_bytes']=int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024);post=inputs()
 return {'kind':'scale','N':n,'M':m,'hit_count':hits,'miss_count':m-hits,'replicate':rep,'diagnostic_trace':diagnostic,
  'order':order,'before_inputs':before,'after_inputs':post,'source_stable':before==post,
  'forks':{'reference':{'wall_ns':ref_fork_wall,'cpu_ns':ref_fork_cpu},'index_template':{'wall_ns':idx_template_fork_wall,'cpu_ns':idx_template_fork_cpu},'indexed_state':{'wall_ns':idx_fork_wall,'cpu_ns':idx_fork_cpu}},
  'index_build':{'wall_ns':index_build_wall,'cpu_ns':index_build_cpu},'rss':rss,'arms':results,
  'branch_parent_isolation':int(parent.node_count())==n+m+1}
def selected_targets(inner):
 graph=inner.graph_to_dict();return {int(e['src']):int(e['tgt']) for e in graph.get('edges',[]) if e['type']=='denotes'}
def control_case(case):
 from substrate_rs import Substrate
 base=Substrate();b=base._inner
 if case=='reuse_first_witness':
  values=['duplicate'];early=b.add_node('Concept',{'name':'duplicate','extra':1});first=b.add_node('Concept',{'name':'duplicate','extra':2})
  root=add_effect_rule(b,values);ref,_,_=fork(b);idx,_,_=fork(b);idx.declare_attr_index('Concept','name')
  # Delete the earlier typed node, then reuse its low NodeID. The reused node
  # is last in typed insertion order despite its smaller numeric ID.
  for inner in (ref,idx):inner.remove_node(early);reused=inner.add_node('Concept',{'name':'duplicate','extra':3})
  rprog=int(ref.run_rules(100));iprog=int(idx.run_rules(100));rt=selected_targets(ref);it=selected_targets(idx)
  return {'case':case,'reference_progress':rprog,'indexed_progress':iprog,'first_surviving_witness':nid(first),'reused_low_id':nid(reused),
   'reference_targets':rt,'indexed_targets':it,'same_digest':digest_graph(ref)==digest_graph(idx),'same_witness':rt==it and list(rt.values())==[nid(first)],
   'parent_unchanged':int(b.node_count())==4}
 if case=='attribute_mutation':
  values=['fresh','old_value'];c0=b.add_node('Concept',{'name':'old_value'});c1=b.add_node('Concept',{'name':'other_value'});add_effect_rule(b,values)
  ref,_,_=fork(b);idx,_,_=fork(b);idx.declare_attr_index('Concept','name')
  for inner in (ref,idx):inner.set_attr(c1,'name','fresh');inner.set_attr(c0,'name','changed')
  rprog=int(ref.run_rules(100));iprog=int(idx.run_rules(100));rt=selected_targets(ref);it=selected_targets(idx)
  variant_ids=[int(x['id']) for x in b.graph_to_dict()['nodes'] if x['type']=='SlangVariant']
  return {'case':case,'reference_progress':rprog,'indexed_progress':iprog,'mutated_match_node':nid(c1),'reference_targets':rt,'indexed_targets':it,
   'same_digest':digest_graph(ref)==digest_graph(idx),'same_witness':rt==it and rt.get(variant_ids[0])==nid(c1) and rt.get(variant_ids[1]) not in (nid(c0),nid(c1)),
   'parent_unmodified_name':b.graph_to_dict()['nodes'][nid(c1)]['attrs'].get('name')=='other_value'}
 if case=='exact_case_subset':
  values=['Exact','exact'];target=b.add_node('Concept',{'name':'Exact','fixture_extra':'subset'})
  add_effect_rule(b,values);variant_ids=[int(x['id']) for x in b.graph_to_dict()['nodes'] if x['type']=='SlangVariant'];ref,_,_=fork(b);idx,_,_=fork(b);idx.declare_attr_index('Concept','name')
  rprog=int(ref.run_rules(100));iprog=int(idx.run_rules(100));rt=selected_targets(ref);it=selected_targets(idx)
  return {'case':case,'reference_progress':rprog,'indexed_progress':iprog,'expected_exact_witness':target,'reference_targets':rt,'indexed_targets':it,
   'same_digest':digest_graph(ref)==digest_graph(idx),'same_witness':rt==it and rt.get(variant_ids[0])==nid(target) and rt.get(variant_ids[1]) not in [nid(target)] and len(rt)==2}
 if case=='empty_attrs':
  first=b.add_node('Concept',{'name':'first'});b.add_node('Concept',{'name':'second'});root=add_effect_rule(b,['unused'],attrs={});v=[int(x['id']) for x in b.graph_to_dict()['nodes'] if x['type']=='SlangVariant'][0];ref,_,_=fork(b);idx,_,_=fork(b);idx.declare_attr_index('Concept','name')
  rprog=int(ref.run_rules(100));iprog=int(idx.run_rules(100));rt=selected_targets(ref);it=selected_targets(idx)
  return {'case':case,'reference_progress':rprog,'indexed_progress':iprog,'reference_targets':rt,'indexed_targets':it,
   'same_digest':digest_graph(ref)==digest_graph(idx),'same_witness':rt==it and rt.get(v)==nid(first)}
 raise ValueError(case)
def controls_worker():
 from domains.engine_provenance import assert_measuring_engine
 assert_measuring_engine();before=inputs();cases=[control_case(x) for x in ('reuse_first_witness','attribute_mutation','exact_case_subset','empty_attrs')];after=inputs()
 return {'kind':'semantic_controls','before_inputs':before,'after_inputs':after,'source_stable':before==after,'cases':cases}
def live_worker(arm,rep):
 from domains.engine_provenance import assert_measuring_engine
 assert_measuring_engine();h=load(HARVEST,'live_harvest_worker');before=inputs();from substrate.world_adapter import WorldAdapter
 original=WorldAdapter.converse;build={}
 def converse(agent,*args,**kwargs):
  if arm=='indexed':
   w=time.perf_counter_ns();c=time.process_time_ns();agent.inner.declare_attr_index('Concept','name');build.update(wall_ns=time.perf_counter_ns()-w,cpu_ns=time.process_time_ns()-c)
   sample_id=None;sample_name=None
   for candidate in agent.s.nodes('Concept'):
    value=agent.s.node(candidate)['attrs'].get('name')
    if isinstance(value,str):sample_id=candidate;sample_name=value;break
   matches=agent.inner.nodes_where('Concept','name',sample_name) if sample_id is not None else []
   index_declared=bool(agent.inner.has_attr_index('Concept','name'));contains=sample_id in matches if sample_id is not None else False
   build.update(index_declared=index_declared,index_probe_pass=index_declared and sample_id is not None and contains,index_sample_name=sample_name,
    index_sample_matches=len(matches),index_sample_contains_witness=contains)
  else:build.update(wall_ns=0,cpu_ns=0)
  w=time.perf_counter_ns();c=time.process_time_ns()
  try:return original(agent,*args,**kwargs)
  finally:build.update(converse_wall_ns=time.perf_counter_ns()-w,converse_cpu_ns=time.process_time_ns()-c)
 WorldAdapter.converse=converse
 try:r=h.worker(LIVE_ROUTE,rep)
 finally:WorldAdapter.converse=original
 after=inputs();r['task_oracle_pass']=bool(r.get('source_stable') and r['locked_inputs']==h.inputs()==r['post_run_inputs'] and r.get('boot_loaded',0)>0 and r.get('error') is None and len(r.get('turns',[]))==1 and ('quorplezap' in r.get('reply','').lower()) and r.get('reply','').rstrip().endswith('?') and any('quorplezap' in str(x.get('trouble_source','')).lower() and x.get('expects_response') is True and 'clarification' in x.get('speech_acts',[]) for x in r['turns'][0].get('outbound_messages',[])))
 return {'kind':'live_route','arm':arm,'replicate':rep,'source_locked_inputs':before,'post_inputs':after,'source_stable':before==after,'index_setup':build,
  'task_oracle_pass':r['task_oracle_pass'],'reply':r['reply'],'final_graph_digest':r['final_graph_digest'],'node_count':len(r['final_graph'].get('nodes',[])),'edge_count':len(r['final_graph'].get('edges',[])),
  'task_wall_ns':r['task_wall_ns'],'task_process_cpu_ns':r['task_process_cpu_ns'],'peak_rss_bytes':r['peak_rss_bytes'],'boot_loaded':r['boot_loaded'],'error':r['error']}
def main():
 if sys.argv[1:]==['--lock']:
  LOCK.parent.mkdir(parents=True,exist_ok=True);LOCK.write_text(json.dumps({'schema':'AddNodeIfAbsentIndexedLookupV1Lock','locked_inputs':inputs()},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return
 locked=inputs()
 if not LOCK.exists() or json.loads(LOCK.read_text()).get('locked_inputs')!=locked:raise SystemExit('missing/stale indexed lookup source lock')
 if CAPTURE.exists():raise SystemExit(f'refusing overwrite: {CAPTURE}')
 OUTDIR.mkdir(parents=True,exist_ok=True);env=os.environ.copy();env.setdefault('OZMA_NO_LLM','1');env.setdefault('OZMA_SEED_PERSIST_DISABLED','1');env['PYTHONPATH']=os.pathsep.join([str(ROOT),str(ROOT/'runners/dsl/python'),str(ROOT/'scripts'),env.get('PYTHONPATH','')])
 rows=[];schedule=[]
 for n in SIZES:
  for m in COUNTS:
   for rep in range(TIMING_REPS+1):
    diagnostic=rep==TRACE_REP;args=['--scale-worker',str(n),str(m),str(rep),str(int(diagnostic))];p=subprocess.run([sys.executable,str(RUNNER),*args],cwd=ROOT,env=env,text=True,capture_output=True,check=True,timeout=300);rows.append(json.loads(p.stdout));schedule.append({'kind':'scale','N':n,'M':m,'replicate':rep,'diagnostic':diagnostic});print(f'scale={n}/{m}/{rep}',file=sys.stderr,flush=True)
 for rep in range(LIVE_REPS):
  for arm in (['reference','indexed'] if rep%2==0 else ['indexed','reference']):
   e=env.copy();p=subprocess.run([sys.executable,str(RUNNER),'--live-worker',arm,str(rep)],cwd=ROOT,env=e,text=True,capture_output=True,check=True,timeout=300);rows.append(json.loads(p.stdout));schedule.append({'kind':'live_route','arm':arm,'replicate':rep});print(f'live={arm}/{rep}',file=sys.stderr,flush=True)
 p=subprocess.run([sys.executable,str(RUNNER),'--controls-worker'],cwd=ROOT,env=env,text=True,capture_output=True,check=True,timeout=300);rows.append(json.loads(p.stdout));schedule.append({'kind':'semantic_controls'});print('controls=complete',file=sys.stderr,flush=True)
 post=inputs();payload={'schema':'AddNodeIfAbsentIndexedLookupV1Capture','locked_inputs':locked,'post_run_inputs':post,'schedule':schedule,'rows':rows};CAPTURE.write_bytes(gzip.compress(json.dumps(payload,sort_keys=True,separators=(',',':')).encode(),compresslevel=5,mtime=0))
 print(json.dumps({'capture':str(CAPTURE.relative_to(ROOT)),'rows':len(rows),'source_stable':locked==post},indent=2))
 if locked!=post:raise SystemExit('source changed during capture')
if __name__=='__main__':
 if len(sys.argv)==6 and sys.argv[1]=='--scale-worker':print(json.dumps(scale_worker(int(sys.argv[2]),int(sys.argv[3]),int(sys.argv[4]),bool(int(sys.argv[5]))),sort_keys=True,separators=(',',':')))
 elif len(sys.argv)==4 and sys.argv[1]=='--live-worker':print(json.dumps(live_worker(sys.argv[2],int(sys.argv[3])),sort_keys=True,separators=(',',':'),default=str))
 elif sys.argv[1:]==['--controls-worker']:print(json.dumps(controls_worker(),sort_keys=True,separators=(',',':'),default=str))
 else:main()

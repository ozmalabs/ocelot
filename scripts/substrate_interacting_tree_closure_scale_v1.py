#!/usr/bin/env python3
"""Topology-crossed two-rule monotone closure scale panel."""
from __future__ import annotations
import hashlib,json,os,platform,random,resource,subprocess,sys,time
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python')]
from substrate_rs import Substrate,_native
from domains.engine_provenance import assert_measuring_engine,build_is_stale
PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_INTERACTING_TREE_CLOSURE_SCALE_V1_PREREG_20260928.md'
LOCK=ROOT/'evaluation/substrate_capability/interacting_tree_closure_scale_v1_lock_20260928.json'
RAW=ROOT/'evaluation/reports/substrate_interacting_tree_closure_scale_v1_20260928.json'
SUMMARY=ROOT/'evaluation/reports/substrate_interacting_tree_closure_scale_v1_summary_20260928.json'
SOURCES=('runners/dsl/src/graph.rs','runners/dsl/src/substrate.rs','runners/dsl/src/rewrite.rs','runners/dsl/src/py.rs','runners/dsl/src/scale_audit.rs','runners/dsl/python/substrate_rs/_native.build.json','runners/dsl/python/substrate_rs/__init__.py','domains/engine_provenance.py','scripts/substrate_interacting_tree_closure_scale_v1.py','scripts/analyze_substrate_interacting_tree_closure_scale_v1.py','docs/research/engine_substrate/SUBSTRATE_INTERACTING_TREE_CLOSURE_SCALE_V1_PREREG_20260928.md','docs/research/engine_substrate/SUBSTRATE_INTERACTING_TREE_CLOSURE_SCALE_V1_PILOT_AMENDMENT_20260928.md')
SIZES=(10_000,100_000,1_000_000);TOPOLOGIES=('balanced','star');AUDITS=(False,True);REPS=(0,1,2)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def fingerprint():
 native=Path(_native.__file__).resolve()
 return {'commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'files':{p:sha(ROOT/p) for p in SOURCES},'native_path':str(native),'native_sha256':sha(native),'native_build_stale':build_is_stale(str(ROOT))}
def current_rss_bytes():
 try:
  for line in Path('/proc/self/status').read_text().splitlines():
   if line.startswith('VmRSS:'):return int(line.split()[1])*1024
 except OSError:pass
 return None
def peak_rss_bytes():
 v=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
 return int(v*(1024 if sys.platform.startswith('linux') else 1))
def node_id(n):return int(n.value if hasattr(n,'value') else n)
def lit(value):return {'type':'Lit','value':value}
def attr(node,key):return {'type':'Attr','node':{'type':'Var','name':node},'key':key}
def eq(a,b):return {'type':'Eq','a':a,'b':b}
def worker(n,topology,rep,audit):
 before=fingerprint();rss0=current_rss_bytes();s=Substrate();inner=s._inner
 t0=time.perf_counter_ns();c0=time.process_time_ns();root=None
 for i in range(n):
  depth=0 if i==0 else (1 if topology=='star' else i.bit_length()-1)
  state='active' if i==0 else 'pending'
  cur=inner.add_node('TreeItem',{'status':state,'ordinal':i,'bucket':i%64,'depth':depth})
  if i==0:root=cur
 node_wall=time.perf_counter_ns()-t0;node_cpu=time.process_time_ns()-c0;rss_nodes=current_rss_bytes()
 t0=time.perf_counter_ns();c0=time.process_time_ns()
 for i in range(1,n):
  parent=0 if topology=='star' else (i-1)//2
  child=_native.NodeID(i);par=_native.NodeID(parent)
  inner.add_edge_unchecked(par,'child',child,{})
  inner.add_edge_unchecked(child,'parent',par,{})
 edge_wall=time.perf_counter_ns()-t0;edge_cpu=time.process_time_ns()-c0;rss_graph=current_rss_bytes()
 t0=time.perf_counter_ns();c0=time.process_time_ns();inner.declare_attr_index('TreeItem','status');index_wall=time.perf_counter_ns()-t0;index_cpu=time.process_time_ns()-c0;rss_index=current_rss_bytes()
 active_parent=eq(attr('p','status'),lit('active'));pending_child=eq(attr('x','status'),lit('pending'))
 rules=[
  {'name':'activate_ready','match':[['p','child','x']],'where':{'type':'And','items':[active_parent,pending_child]},'effects':[['set_attr','x','status','ready']]},
  {'name':'commit_ready','match':[['x','parent','p']],'where':eq(attr('x','status'),lit('ready')),'effects':[['set_attr','x','status','active']]},
 ]
 t0=time.perf_counter_ns();c0=time.process_time_ns();indices=[inner.add_rule(r) for r in rules];install_wall=time.perf_counter_ns()-t0;install_cpu=time.process_time_ns()-c0;rss_installed=current_rss_bytes()
 Native=_native.Substrate;Native.scale_audit_set_enabled(False);Native.scale_audit_set_per_rule_enabled(False);Native.scale_audit_reset();Native.scale_audit_per_rule_reset()
 if audit:Native.scale_audit_set_per_rule_enabled(True);Native.scale_audit_set_enabled(True)
 t0=time.perf_counter_ns();c0=time.process_time_ns();report=inner.run_rules_report(100_000_000,False);closure_wall=time.perf_counter_ns()-t0;closure_cpu=time.process_time_ns()-c0;rss_closed=current_rss_bytes()
 counters=dict(Native.scale_audit_snapshot()) if audit else {};per=[list(x) for x in Native.scale_audit_per_rule_snapshot()] if audit else [];clauses=[list(x) for x in Native.scale_audit_match_clause_snapshot()] if audit else []
 Native.scale_audit_set_enabled(False);Native.scale_audit_set_per_rule_enabled(False)
 t0=time.perf_counter_ns();pending=len(inner.nodes_where('TreeItem','status','pending'));ready=len(inner.nodes_where('TreeItem','status','ready'));active=len(inner.nodes_where('TreeItem','status','active'));validation_wall=time.perf_counter_ns()-t0;rss_validated=current_rss_bytes()
 sample_ids=sorted({0,n//2,n-1});samples=[]
 for i in sample_ids:
  row=inner.node(_native.NodeID(i));parents=[node_id(x) for x in inner.neighbours(_native.NodeID(i),'parent')];expected_parent=[] if i==0 else [0 if topology=='star' else (i-1)//2]
  depth=0 if i==0 else (1 if topology=='star' else i.bit_length()-1)
  samples.append({'id':i,'status':row.get('attrs',{}).get('status'),'ordinal':row.get('attrs',{}).get('ordinal'),'bucket':row.get('attrs',{}).get('bucket'),'depth':row.get('attrs',{}).get('depth'),'parents':parents,'expected_parents':expected_parent,'expected_bucket':i%64,'expected_depth':depth})
 nodes=inner.node_count();edges=inner.edge_count();after=fingerprint()
 return {'n':n,'topology':topology,'replicate':rep,'audit':audit,'pid':os.getpid(),'before':before,'after':after,'rss_before_bytes':rss0,'rss_after_nodes_bytes':rss_nodes,'rss_after_graph_bytes':rss_graph,'rss_after_index_bytes':rss_index,'rss_after_rule_install_bytes':rss_installed,'rss_after_closure_bytes':rss_closed,'rss_after_validation_bytes':rss_validated,'peak_rss_bytes':peak_rss_bytes(),'node_build_wall_ns':node_wall,'node_build_cpu_ns':node_cpu,'edge_build_wall_ns':edge_wall,'edge_build_cpu_ns':edge_cpu,'index_declaration_wall_ns':index_wall,'index_declaration_cpu_ns':index_cpu,'rule_install_wall_ns':install_wall,'rule_install_cpu_ns':install_cpu,'closure_wall_ns':closure_wall,'closure_cpu_ns':closure_cpu,'validation_wall_ns':validation_wall,'nodes':nodes,'edges':edges,'rule_indices':indices,'report':{k:report[k] for k in ('status','progress_steps','requested_progress_budget','budget_overshoot','passes_completed')},'pending_count':pending,'ready_count':ready,'active_count':active,'samples':samples,'counters':counters,'per_rule':per,'clause_counters':clauses,'environment':{'python':sys.version,'platform':platform.platform()}}
def cells():return [(n,t,r,a) for n in SIZES for t in TOPOLOGIES for r in REPS for a in AUDITS]
def main():
 assert_measuring_engine()
 if sys.argv[1:]==['--lock']:
  fp=fingerprint()
  if fp['native_build_stale']:raise SystemExit('native build is stale')
  LOCK.parent.mkdir(parents=True,exist_ok=True);LOCK.write_text(json.dumps(fp,indent=2,sort_keys=True)+'\n');print(LOCK);return
 if len(sys.argv)==6 and sys.argv[1]=='--worker':
  n=int(sys.argv[2]);topology=sys.argv[3];rep=int(sys.argv[4]);audit=sys.argv[5]=='on';print(json.dumps(worker(n,topology,rep,audit),sort_keys=True));return
 locked=fingerprint()
 if locked['native_build_stale'] or not LOCK.exists() or json.loads(LOCK.read_text())!=locked:raise SystemExit('missing/stale source lock or native build')
 jobs=cells();random.Random(20260929).shuffle(jobs);runs=[];started=datetime.now(timezone.utc).isoformat();env=dict(os.environ);env['PYTHONPATH']=os.pathsep.join((str(ROOT),str(ROOT/'runners/dsl/python'),env.get('PYTHONPATH','')))
 for n,topology,rep,audit in jobs:
  cp=subprocess.run([sys.executable,str(Path(__file__).resolve()),'--worker',str(n),topology,str(rep),'on' if audit else 'off'],cwd=ROOT,env=env,text=True,capture_output=True,check=True)
  row=json.loads(cp.stdout);row['worker_returncode']=cp.returncode;row['worker_stderr']=cp.stderr;runs.append(row)
 after=fingerprint();expected=36
 checks={'thirty_six_workers':len(runs)==expected,'three_replicates_per_factorial_cell':all(sum(x['n']==n and x['topology']==t and x['audit']==a for x in runs)==3 for n in SIZES for t in TOPOLOGIES for a in AUDITS),'unique_processes':len({x['pid'] for x in runs})==expected,'stable_source_lock':after==locked and all(x['before']==locked==x['after'] for x in runs),'exact_graph_counts':all(x['nodes']==x['n'] and x['edges']==2*(x['n']-1) for x in runs),'exact_terminal_oracle':all(x['report']['status']=='fixed_point' and x['report']['budget_overshoot']==0 and x['pending_count']==0 and x['ready_count']==0 and x['active_count']==x['n'] for x in runs),'sampled_parent_and_attrs':all(len(x['samples'])==3 and all(s['status']=='active' and s['ordinal']==s['id'] and s['bucket']==s['expected_bucket'] and s['depth']==s['expected_depth'] and s['parents']==s['expected_parents'] for s in x['samples']) for x in runs),'positive_timings':all(all(x[k]>0 for k in ('node_build_wall_ns','edge_build_wall_ns','index_declaration_wall_ns','rule_install_wall_ns','closure_wall_ns','validation_wall_ns')) for x in runs),'audit_counter_presence_separated':all((bool(x['per_rule']) and bool(x['counters'])) if x['audit'] else (not x['per_rule'] and not x['counters']) for x in runs)}
 RAW.write_text(json.dumps({'schema_version':1,'run_id':'substrate-interacting-tree-closure-scale-v1-20260928','started_utc':started,'locked_inputs':locked,'post_run_inputs':after,'schedule':jobs,'checks':checks,'all_checks_pass':all(checks.values()),'runs':runs},indent=2,sort_keys=True)+'\n')
 SUMMARY.write_text(json.dumps({'schema_version':1,'raw_path':str(RAW.relative_to(ROOT)),'locked_inputs':locked,'post_run_inputs':after,'checks':checks,'all_checks_pass':all(checks.values())},indent=2,sort_keys=True)+'\n');print(json.dumps({'worker_count':len(runs),'checks':checks,'all_checks_pass':all(checks.values()),'raw':str(RAW.relative_to(ROOT))},indent=2))
 if not all(checks.values()):raise SystemExit('interacting tree closure scale gates failed')
if __name__=='__main__':main()

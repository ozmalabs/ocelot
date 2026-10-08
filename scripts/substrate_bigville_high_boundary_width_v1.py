#!/usr/bin/env python3
"""Exact component-message reuse versus global JT on Bigville CAN fixtures."""
from __future__ import annotations
import hashlib,json,os,platform,subprocess,sys,time,itertools,math
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
from substrate_run_manifest import capture_run_manifest,finish_console_capture,start_console_capture
PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_BIGVILLE_HIGH_BOUNDARY_WIDTH_V1_1_AMENDMENT_20260926.md';BASE_PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_BIGVILLE_BOUNDARY_VARIABLE_ELIMINATION_PREREG_20260926.md';CAST=ROOT/'seeds/bigville_cast100.json';BUILDER=ROOT/'worlds/bigville_can_beliefs.py';BASE_RUNNER=ROOT/'scripts/substrate_bigville_boundary_variable_elimination_v1.py'
SOURCES={'jt':ROOT/'domains/can_junction_tree.py','width':ROOT/'domains/graph_treewidth.py','graph_rs':ROOT/'runners/dsl/src/graph.rs','py_rs':ROOT/'runners/dsl/src/py.rs'};LOCK=ROOT/'evaluation/substrate_capability/bigville_high_boundary_width_v1_1_lock_20260926.json';OUT=ROOT/'evaluation/reports/substrate_bigville_high_boundary_width_v1_1_20260926.json'
SIZES=(12,20);KS=(2,4,6,8);PATTERNS=('chain','cycle','clique')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def lock_inputs():
 from substrate_rs import _native
 return {'protocol_sha256':sha(PROTOCOL),'base_protocol_sha256':sha(BASE_PROTOCOL),'runner_sha256':sha(__file__),'base_runner_sha256':sha(BASE_RUNNER),'cast_sha256':sha(CAST),'builder_sha256':sha(BUILDER),'source_sha256':{k:sha(v) for k,v in SOURCES.items()},'native_extension_sha256':sha(Path(_native.__file__).resolve()),'native_build_manifest_sha256':sha(ROOT/'runners/dsl/python/substrate_rs/_native.build.json'),'commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()}
def energy(u,p,s):return -sum(float(h)*s[i] for i,h in u.items())-sum(float(w)*s[next(iter(e))]*s[next(iter(e-{next(iter(e))}))] for e,w in p.items())
def components(nodes,edges):
 a={v:set() for v in nodes}
 for x,y in edges:a[x].add(y);a[y].add(x)
 todo=set(nodes);out=[]
 while todo:
  r=min(todo);todo.remove(r);q=[r];c=[]
  while q:
   v=q.pop();c.append(v)
   for z in a[v]&todo:todo.remove(z);q.append(z)
  out.append(sorted(c))
 return out
def min_fill_order(variables,factors):
 adj={v:set() for v in variables}
 for scope,_ in factors:
  for v in scope:adj[v].update(set(scope)-{v})
 todo=set(variables);order=[];width=0
 while todo:
  def cost(v):
   ns=adj[v]&todo;missing=sum(1 for a in ns for b in ns if a<b and b not in adj[a]);return missing,len(ns),v
  v=min(todo,key=cost);ns=adj[v]&todo;width=max(width,len(ns))
  for a in ns:adj[a].update(ns-{a})
  todo.remove(v);order.append(v)
 return order,width
def eliminate_map(factors,variables,vocab):
 factors=[(tuple(scope),dict(table)) for scope,table in factors];order,width=min_fill_order(variables,factors);backs=[];rows=0;processed=0;peak=max((len(t) for _,t in factors),default=0);buckets=[]
 for v in order:
  bucket=[f for f in factors if v in f[0]];factors=[f for f in factors if v not in f[0]];union=tuple(sorted({x for scope,_ in bucket for x in scope}));rest=tuple(x for x in union if x!=v);out={};back={}
  for vals in itertools.product(vocab,repeat=len(rest)):
   env=dict(zip(rest,vals));best=math.inf;arg=None
   for value in vocab:
    env[v]=value;score=0.0
    for scope,table in bucket:score+=table[tuple(env[x] for x in scope)]
    rows+=1
    if score<best:best,arg=score,value
   out[vals]=best;back[vals]=arg
  processed+=len(out);peak=max(peak,len(out));buckets.append({'variable':v,'scope_size':len(union),'rows':len(out)*len(vocab),'output_entries':len(out)});factors.append((rest,out));backs.append((v,rest,back))
 energy0=sum(table[()] for scope,table in factors if not scope)
 if any(scope for scope,_ in factors):raise ValueError('elimination left nonconstant factors')
 state={}
 for v,rest,back in reversed(backs):state[v]=back[tuple(state[x] for x in rest)]
 return state,energy0,{'order':order,'width':width,'rows_evaluated':rows,'factor_entries_processed':processed,'peak_factor_entries':peak,'buckets':buckets}
def run_case(n,rep,k,topology):
 import substrate_rs as sr, domains.can_junction_tree as jt
 from domains.graph_treewidth import min_fill_upper_bound
 from worlds import bigville_can_beliefs as bv
 start=lock_inputs();s=sr.Substrate();g=s._inner;bv.install_productions(g);cast=json.loads(CAST.read_text())['residents'][:n];concepts=[]
 t=time.perf_counter_ns()
 for r in cast:
  b=bv.build_resident_can_mt(g,r,beta=1.5);bv.apply_scenario_evidence(g,b['concepts']);g.set_attr(b['mt_node'],'discrete_mode','3state');concepts.append(b['concepts'])
 agg=g.add_node('Microtheory',{'name':'message_aggregate','discrete_mode':'3state','temperature':1.5})
 for c in concepts:
  for v in c.values():g.add_edge_unchecked(agg,'has_concept',v,{})
 setup=time.perf_counter_ns()-t;topic={'chain':'trust_mayor','cycle':'world_safe','clique':'claim_credible'}[topology];bnodes=[int(concepts[i][topic].value) for i in range(k)]
 if topology=='chain':pairs=[(i,i+1) for i in range(k-1)]
 elif topology=='cycle':pairs=[(i,i+1) for i in range(k-1)]+([(k-1,0)] if k>=3 else [])
 else:pairs=list(itertools.combinations(range(k),2))
 pairs=sorted(tuple(sorted(edge)) for edge in pairs)
 weights=(.25,-.25,.5,-.2,.35,-.3,.15);links=[]
 for q,(a,b) in enumerate(pairs):
  x=concepts[a][topic];y=concepts[b][topic];w=weights[q%len(weights)];g.add_edge_unchecked(x,'causal_influence',y,{'weight':w});g.add_edge_unchecked(y,'causal_influence',x,{'weight':w});links.append((int(x.value),int(y.value),w))
 t=time.perf_counter_ns();net=jt.can_network_from_mt(g,agg);extract=time.perf_counter_ns()-t;B={x for a,b,_ in links for x in (a,b)};inside=[v for v in net['nodes'] if v not in B];cs=components(inside,[e for e in net['edges'] if e[0] in set(inside) and e[1] in set(inside)]);owner={v:i for i,c in enumerate(cs) for v in c};interfaces=[];component_factors=[]
 for c in cs:
  cset=set(c);f=[(tuple(e),w) for e,w in net['pairwise'].items() if e&cset];itf=sorted({v for edge,_ in f for v in edge if v in B});interfaces.append(itf);component_factors.append(f)
 valid=all(not(e.isdisjoint(B) and len({owner[v] for v in e})>1) for e in net['pairwise']);d=net['vocab'];local_assignments=sum(len(d)**(len(c)+len(i)) for c,i in zip(cs,interfaces));message_entries=sum(len(d)**len(i) for i in interfaces)
 t=time.perf_counter_ns();messages=[];message_assignments=0
 for c,itf,factors in zip(cs,interfaces,component_factors):
  table={}
  for iv in itertools.product(d,repeat=len(itf)):
   bs=dict(zip(itf,iv));best=math.inf;beststate=None
   for vv in itertools.product(d,repeat=len(c)):
    message_assignments+=1;z=dict(zip(c,vv));score=-sum(net['unary'][v]*z[v] for v in c)
    for (a,b),w in factors:score-=w*(z[a] if a in z else bs[a])*(z[b] if b in z else bs[b])
    if score<best:best,beststate=score,z
   table[iv]=(best,beststate)
  messages.append(table)
 factors=[]
 for v in sorted(B):factors.append(((v,),{(x,):-net['unary'][v]*x for x in d}))
 for e,w in net['pairwise'].items():
  if e<=B:
   a,b=sorted(e);factors.append(((a,b),{(x,y):-w*x*y for x in d for y in d}))
 for itf,table in zip(interfaces,messages):factors.append((tuple(itf),{key:value[0] for key,value in table.items()}))
 bs,best,ve_stats=eliminate_map(factors,sorted(B),d);beststate=dict(bs)
 for itf,table in zip(interfaces,messages):beststate.update(table[tuple(bs[v] for v in itf)][1])
 msg_ns=time.perf_counter_ns()-t
 t=time.perf_counter_ns();width=min_fill_upper_bound(net['nodes'],net['edges']);glob=jt.junction_tree_map(net['nodes'],net['edges'],net['unary'],net['pairwise'],d,order=width['elimination_order']);global_ns=time.perf_counter_ns()-t
 end=lock_inputs();eg=energy(net['unary'],net['pairwise'],glob['state']);em=energy(net['unary'],net['pairwise'],beststate)
 return {'n_residents':n,'replicate':rep,'topology':topology,'k':k,'cross_factor_count':len(links),'cross_links':links,'nodes':len(net['nodes']),'factor_count':len(net['pairwise']),'boundary_nodes':sorted(B),'boundary_size':len(B),'component_sizes':sorted(map(len,cs)),'component_interfaces':sorted(map(len,interfaces)),'component_shape':sorted([[len(c),len(i)] for c,i in zip(cs,interfaces)]),'component_message_entries':message_entries,'message_assignment_count':message_assignments,'expected_message_assignment_count':local_assignments,'direct_oracle_assignment_count':(len(d)**k)*sum(len(d)**len(c) for c in cs),'boundary_factor_scopes':[list(scope) for scope,_ in factors],'boundary_elimination':ve_stats,'exhaustive_boundary_assignments':len(d)**k,'global_width':width['treewidth'],'separator_condition_valid':valid,'global_energy':float(glob['energy']),'boundary_ve_energy':float(best),'independent_global_energy':eg,'independent_boundary_ve_energy':em,'energy_gap':eg-em,'states_valid':set(glob['state'])==set(net['nodes'])==set(beststate) and all(x in d for x in glob['state'].values()) and all(x in d for x in beststate.values()),'timing_ns':{'setup':setup,'aggregate_extraction':extract,'global_width_and_map':global_ns,'message_build_and_boundary_elimination':msg_ns},'source_inputs_start':start,'source_inputs_end':end}
def worker(rep):
 lock=lock_inputs();return {'replicate':rep,'pid':os.getpid(),'started_inputs':lock,'cases':[run_case(n,rep,k,top) for top in PATTERNS for n in SIZES for k in KS],'finished_inputs':lock_inputs()}
def main():
 if sys.argv[1:]==['--lock']:print(json.dumps({'locked_inputs':lock_inputs()},indent=2,sort_keys=True));return
 if len(sys.argv)==3 and sys.argv[1]=='--worker':print(json.dumps(worker(int(sys.argv[2])),sort_keys=True));return
 started=datetime.now(timezone.utc).isoformat();log_capture=start_console_capture('substrate-bigville-high-boundary-width-v1-1-20260926')
 locked=lock_inputs()
 if not LOCK.exists() or json.loads(LOCK.read_text()).get('locked_inputs')!=locked:raise SystemExit('missing or stale lock')
 env=dict(os.environ);env.setdefault('OZMA_NO_LLM','1');env.setdefault('OZMA_SEED_PERSIST_DISABLED','1');env['PYTHONPATH']=str(ROOT/'runners/dsl/python')+os.pathsep+str(ROOT)+os.pathsep+env.get('PYTHONPATH','')
 runs=[];worker_stderr=[];worker_processes=[]
 for r in range(3):
  argv=[sys.executable,str(Path(__file__).resolve()),'--worker',str(r)]
  proc=subprocess.run(argv,cwd=ROOT,env=env,text=True,capture_output=True,check=True,timeout=180)
  runs.append(json.loads(proc.stdout));worker_stderr.append({'replicate':r,'stderr':proc.stderr})
  worker_processes.append({'replicate':r,'argv':argv,'relevant_environment':{k:env[k] for k in ('PYTHONPATH','OZMA_NO_LLM','OZMA_SEED_PERSIST_DISABLED') if k in env},'stdout_sha256':hashlib.sha256(proc.stdout.encode()).hexdigest(),'stderr_sha256':hashlib.sha256(proc.stderr.encode()).hexdigest(),'stderr_bytes':len(proc.stderr.encode())})
 post=lock_inputs();cases=[c for r in runs for c in r['cases']]
 def expected_edges(top,k):return k-1 if top=='chain' or (top=='cycle' and k==2) else k if top=='cycle' else k*(k-1)//2
 checks={'fresh_workers':len({r['pid'] for r in runs})==3,'stable_sources':post==locked and all(r['started_inputs']==locked==r['finished_inputs'] for r in runs) and all(c['source_inputs_start']==locked==c['source_inputs_end'] for c in cases),'72_cases':len(cases)==72,'full_design':all(sum(c['n_residents']==n and c['k']==k and c['topology']==top for c in cases)==3 for n in SIZES for k in KS for top in PATTERNS),'boundary_and_topology':all(c['boundary_size']==c['k'] and c['cross_factor_count']==expected_edges(c['topology'],c['k']) for c in cases),'separator_condition':all(c['separator_condition_valid'] for c in cases),'message_counts':all(c['message_assignment_count']==c['expected_message_assignment_count']==sum(3**(a+b) for a,b in c['component_shape']) for c in cases),'ve_order_and_cost':all(len(c['boundary_elimination']['order'])==c['k'] and len(set(c['boundary_elimination']['order']))==c['k'] and c['boundary_elimination']['width']>=0 and c['boundary_elimination']['rows_evaluated']==sum(b['rows'] for b in c['boundary_elimination']['buckets']) and c['boundary_elimination']['factor_entries_processed']==sum(b['output_entries'] for b in c['boundary_elimination']['buckets']) for c in cases),'energy_parity':all(abs(c['energy_gap'])<1e-7 and abs(c['global_energy']-c['independent_global_energy'])<1e-7 and abs(c['boundary_ve_energy']-c['independent_boundary_ve_energy'])<1e-7 for c in cases),'valid_complete_states':all(c['states_valid'] for c in cases),'positive_timing':all(all(v>0 for v in c['timing_ns'].values()) for c in cases)}
 print('worker stderr byte counts:',[len(x['stderr'].encode()) for x in worker_stderr],flush=True)
 log_ref=finish_console_capture(log_capture)
 manifest=capture_run_manifest(run_id='substrate-bigville-high-boundary-width-v1-1-20260926',runner='scripts/substrate_bigville_high_boundary_width_v1.py',protocol_files=(str(PROTOCOL.relative_to(ROOT)),str(BASE_PROTOCOL.relative_to(ROOT)),str(LOCK.relative_to(ROOT))),source_files=tuple(str(x.relative_to(ROOT)) for x in SOURCES.values())+(str(BASE_RUNNER.relative_to(ROOT)),str(BUILDER.relative_to(ROOT))),data_files=(str(CAST.relative_to(ROOT)),),analysis_files=('scripts/analyze_substrate_bigville_high_boundary_width_v1_1.py',),started_utc=started,exit_status=0 if all(checks.values()) else 1,stdout_stderr_capture=log_ref,child_processes=worker_processes)
 payload={'schema_version':1,'run_id':'substrate-bigville-high-boundary-width-v1-1-20260926','claim_boundary':'Offline exact component-message plus induced-boundary variable elimination on controlled Bigville CAN factor topologies; not native frame scheduling or natural-boundary prevalence.','locked_inputs':locked,'post_run_inputs':post,'lock_sha256':sha(LOCK),'environment':{'python':sys.version,'platform':platform.platform()},'configuration':{'sizes':SIZES,'boundary_dimensions':KS,'topologies':PATTERNS},'runs':runs,'worker_stderr':worker_stderr,'run_manifest':manifest,'checks':checks};OUT.write_text(json.dumps(payload,indent=2,sort_keys=True)+'\n');print(json.dumps({'output':str(OUT),'checks':checks},indent=2))
 if not all(checks.values()):raise SystemExit('capture validity or semantic gate failed')
if __name__=='__main__':main()

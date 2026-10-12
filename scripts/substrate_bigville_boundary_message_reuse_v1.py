#!/usr/bin/env python3
"""Exact component-message reuse versus global JT on Bigville CAN fixtures."""
from __future__ import annotations
import hashlib,json,os,platform,subprocess,sys,time,itertools,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_BIGVILLE_BOUNDARY_MESSAGE_REUSE_PREREG_20260926.md';BASE_PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_BIGVILLE_CROSS_BOUNDARY_MAP_PREREG_20260926.md';CAST=ROOT/'seeds/bigville_cast100.json';BUILDER=ROOT/'worlds/bigville_can_beliefs.py';BASE_RUNNER=ROOT/'scripts/substrate_bigville_cross_boundary_map_v1.py'
SOURCES={'jt':ROOT/'domains/can_junction_tree.py','width':ROOT/'domains/graph_treewidth.py','graph_rs':ROOT/'runners/dsl/src/graph.rs','py_rs':ROOT/'runners/dsl/src/py.rs'};LOCK=ROOT/'evaluation/substrate_capability/bigville_boundary_message_reuse_v1_lock_20260926.json';OUT=ROOT/'evaluation/reports/substrate_bigville_boundary_message_reuse_v1_20260926.json'
SIZES=(10,25);KS=(0,2,4,6);PATTERNS=(((0,1),(2,3),(4,5)),((0,3),(1,4),(2,5)),((0,2),(1,5),(3,4)))
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
def run_case(n,rep,k):
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
 setup=time.perf_counter_ns()-t;pattern=PATTERNS[rep];topics=(('trust_mayor','claim_credible'),('trust_mayor','world_safe'),('claim_credible','debtor_trustworthy'));links=[]
 for q,(a,b) in enumerate(pattern[:k//2]):
  x=concepts[a][topics[rep][0]];y=concepts[b][topics[rep][1]];w=(.25,-.25,.5)[q];g.add_edge_unchecked(x,'causal_influence',y,{'weight':w});g.add_edge_unchecked(y,'causal_influence',x,{'weight':w});links.append((int(x.value),int(y.value),w))
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
 boundary_factors=[(tuple(e),w) for e,w in net['pairwise'].items() if e<=B];best=math.inf;beststate=None;boundary_checked=0
 for vals in itertools.product(d,repeat=len(B)):
  bs=dict(zip(sorted(B),vals));score=-sum(net['unary'][v]*bs[v] for v in B)
  for (a,b),w in boundary_factors:score-=w*bs[a]*bs[b]
  st=dict(bs)
  for itf,table in zip(interfaces,messages):
   key=tuple(bs[v] for v in itf);val,z=table[key];score+=val;st.update(z)
  boundary_checked+=1
  if score<best:best,beststate=score,st
 msg_ns=time.perf_counter_ns()-t
 t=time.perf_counter_ns();width=min_fill_upper_bound(net['nodes'],net['edges']);glob=jt.junction_tree_map(net['nodes'],net['edges'],net['unary'],net['pairwise'],d,order=width['elimination_order']);global_ns=time.perf_counter_ns()-t
 end=lock_inputs();eg=energy(net['unary'],net['pairwise'],glob['state']);em=energy(net['unary'],net['pairwise'],beststate)
 return {'n_residents':n,'replicate':rep,'pattern':rep,'k':k,'nodes':len(net['nodes']),'factor_count':len(net['pairwise']),'boundary_size':len(B),'component_sizes':sorted(map(len,cs)),'component_interfaces':sorted(map(len,interfaces)),'component_shape':sorted([[len(c),len(i)] for c,i in zip(cs,interfaces)]),'component_message_entries':message_entries,'message_assignment_count':message_assignments,'expected_message_assignment_count':local_assignments,'global_boundary_assignments':boundary_checked,'expected_global_boundary_assignments':len(d)**k,'direct_oracle_assignment_count':(len(d)**k)*sum(len(d)**len(c) for c in cs),'global_width':width['treewidth'],'separator_condition_valid':valid,'global_energy':float(glob['energy']),'message_energy':float(best),'independent_global_energy':eg,'independent_message_energy':em,'energy_gap':eg-em,'states_valid':set(glob['state'])==set(net['nodes'])==set(beststate) and all(x in d for x in glob['state'].values()) and all(x in d for x in beststate.values()),'timing_ns':{'setup':setup,'aggregate_extraction':extract,'global_width_and_map':global_ns,'message_build_and_boundary_map':msg_ns},'source_inputs_start':start,'source_inputs_end':end}
def worker(rep):
 lock=lock_inputs();return {'replicate':rep,'pid':os.getpid(),'started_inputs':lock,'cases':[run_case(n,rep,k) for n in SIZES for k in KS],'finished_inputs':lock_inputs()}
def main():
 if sys.argv[1:]==['--lock']:print(json.dumps({'locked_inputs':lock_inputs()},indent=2,sort_keys=True));return
 if len(sys.argv)==3 and sys.argv[1]=='--worker':print(json.dumps(worker(int(sys.argv[2])),sort_keys=True));return
 locked=lock_inputs()
 if not LOCK.exists() or json.loads(LOCK.read_text()).get('locked_inputs')!=locked:raise SystemExit('missing or stale lock')
 env=dict(os.environ);env.setdefault('OZMA_NO_LLM','1');env.setdefault('OZMA_SEED_PERSIST_DISABLED','1');env['PYTHONPATH']=str(ROOT/'runners/dsl/python')+os.pathsep+str(ROOT)+os.pathsep+env.get('PYTHONPATH','')
 runs=[json.loads(subprocess.run([sys.executable,str(Path(__file__).resolve()),'--worker',str(r)],cwd=ROOT,env=env,text=True,capture_output=True,check=True,timeout=180).stdout) for r in range(3)];post=lock_inputs();cases=[c for r in runs for c in r['cases']]
 checks={'fresh_workers':len({r['pid'] for r in runs})==3,'stable_sources':post==locked and all(r['started_inputs']==locked==r['finished_inputs'] for r in runs) and all(c['source_inputs_start']==locked==c['source_inputs_end'] for c in cases),'24_cases':len(cases)==24,'full_design':all(sum(c['n_residents']==n and c['k']==k for c in cases)==3 for n in SIZES for k in KS),'boundary_dimension':all(c['boundary_size']==c['k'] for c in cases),'separator_condition':all(c['separator_condition_valid'] for c in cases),'assignment_counts':all(c['message_assignment_count']==c['expected_message_assignment_count'] and c['global_boundary_assignments']==c['expected_global_boundary_assignments'] and c['message_assignment_count']==sum(3**(a+b) for a,b in c['component_shape']) for c in cases),'energy_parity':all(abs(c['energy_gap'])<1e-7 and abs(c['global_energy']-c['independent_global_energy'])<1e-7 and abs(c['message_energy']-c['independent_message_energy'])<1e-7 for c in cases),'valid_complete_states':all(c['states_valid'] for c in cases),'positive_timing':all(all(v>0 for v in c['timing_ns'].values()) for c in cases)}
 payload={'schema_version':1,'run_id':'substrate-bigville-boundary-message-reuse-v1-20260926','claim_boundary':'Offline exact component boundary-message reuse on controlled Bigville cross-resident CAN factors; not native frame scheduling or natural-boundary prevalence.','locked_inputs':locked,'post_run_inputs':post,'lock_sha256':sha(LOCK),'environment':{'python':sys.version,'platform':platform.platform()},'configuration':{'sizes':SIZES,'boundary_dimensions':KS,'patterns':PATTERNS},'runs':runs,'checks':checks};OUT.write_text(json.dumps(payload,indent=2,sort_keys=True)+'\n');print(json.dumps({'output':str(OUT),'checks':checks},indent=2))
 if not all(checks.values()):raise SystemExit('capture validity or semantic gate failed')
if __name__=='__main__':main()

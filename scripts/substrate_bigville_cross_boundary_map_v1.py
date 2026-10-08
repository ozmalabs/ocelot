#!/usr/bin/env python3
"""Controlled nonzero-boundary exact MAP replay for authored Bigville CANs."""
from __future__ import annotations
import hashlib,json,os,platform,subprocess,sys,time,itertools,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_BIGVILLE_CROSS_BOUNDARY_MAP_PREREG_20260926.md';CAST=ROOT/'seeds/bigville_cast100.json';BUILDER=ROOT/'worlds/bigville_can_beliefs.py'
SOURCES={'jt':ROOT/'domains/can_junction_tree.py','width':ROOT/'domains/graph_treewidth.py','graph_rs':ROOT/'runners/dsl/src/graph.rs','py_rs':ROOT/'runners/dsl/src/py.rs'}
LOCK=ROOT/'evaluation/substrate_capability/bigville_cross_boundary_map_v1_lock_20260926.json';OUT=ROOT/'evaluation/reports/substrate_bigville_cross_boundary_map_v1_20260926.json'
SIZES=(10,25);KS=(0,2,4,6);PATTERNS=(((0,1),(2,3),(4,5)),((0,3),(1,4),(2,5)),((0,2),(1,5),(3,4)))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def lock_inputs():
 from substrate_rs import _native
 return {'protocol_sha256':sha(PROTOCOL),'runner_sha256':sha(__file__),'cast_sha256':sha(CAST),'builder_sha256':sha(BUILDER),'source_sha256':{k:sha(v) for k,v in SOURCES.items()},'native_extension_sha256':sha(Path(_native.__file__).resolve()),'native_build_manifest_sha256':sha(ROOT/'runners/dsl/python/substrate_rs/_native.build.json'),'commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()}
def energy(u,p,s):return -sum(float(h)*s[i] for i,h in u.items())-sum(float(w)*s[next(iter(e))]*s[next(iter(e-{next(iter(e))}))] for e,w in p.items())
def comps(nodes,edges):
 adj={v:set() for v in nodes}
 for a,b in edges:adj[a].add(b);adj[b].add(a)
 unseen=set(nodes);out=[]
 while unseen:
  r=min(unseen);unseen.remove(r);todo=[r];c=[]
  while todo:
   v=todo.pop();c.append(v)
   for x in adj[v]&unseen:unseen.remove(x);todo.append(x)
  out.append(sorted(c))
 return out
def run_case(n,rep,k):
 import substrate_rs as sr, domains.can_junction_tree as jt
 from domains.graph_treewidth import min_fill_upper_bound
 from worlds import bigville_can_beliefs as bv
 start=lock_inputs();s=sr.Substrate();g=s._inner;bv.install_productions(g);cast=json.loads(CAST.read_text())['residents'][:n];concepts=[];local=[]
 t=time.perf_counter_ns()
 for r in cast:
  b=bv.build_resident_can_mt(g,r,beta=1.5);bv.apply_scenario_evidence(g,b['concepts']);g.set_attr(b['mt_node'],'discrete_mode','3state');concepts.append(b['concepts']);local.append(jt.can_network_from_mt(g,b['mt_node']))
 agg=g.add_node('Microtheory',{'name':'boundary_aggregate','discrete_mode':'3state','temperature':1.5})
 for c in concepts:
  for v in c.values():g.add_edge_unchecked(agg,'has_concept',v,{})
 setup=time.perf_counter_ns()-t;pattern=PATTERNS[rep];links=[];topic_pairs=(('trust_mayor','claim_credible'),('trust_mayor','world_safe'),('claim_credible','debtor_trustworthy'))
 for q,(a,b) in enumerate(pattern[:k//2]):
  x=concepts[a][topic_pairs[rep][0]];y=concepts[b][topic_pairs[rep][1]];w=(.25,-.25,.5)[q]
  g.add_edge_unchecked(x,'causal_influence',y,{'weight':w});g.add_edge_unchecked(y,'causal_influence',x,{'weight':w});links.append((int(x.value),int(y.value),w))
 t=time.perf_counter_ns();net=jt.can_network_from_mt(g,agg);extract=time.perf_counter_ns()-t;boundary=sorted({v for a,b,_ in links for v in (a,b)});B=set(boundary);inside=[v for v in net['nodes'] if v not in B];cedges=[e for e in net['edges'] if e[0] in set(inside) and e[1] in set(inside)];cs=comps(inside,cedges)
 owner={v:i for i,c in enumerate(cs) for v in c};valid=all(not(e.isdisjoint(B) and len({owner[v] for v in e})>1) for e in net['pairwise'])
 # Explicit conditional enumeration, scoring each component with boundary fixed.
 t=time.perf_counter_ns();best=math.inf;beststate=None;checked=0;local_checked=0;d=net['vocab'];boundary_pairs=[(tuple(e),w) for e,w in net['pairwise'].items() if e<=B];component_factors=[]
 for c in cs:
  cset=set(c);component_factors.append((c,[(tuple(e),w) for e,w in net['pairwise'].items() if e & cset]))
 for vals in itertools.product(d,repeat=len(boundary)):
  st=dict(zip(boundary,vals));base=-sum(net['unary'][v]*st[v] for v in boundary)
  for (a,b),w in boundary_pairs:base-=w*st[a]*st[b]
  total=base;cur=dict(st)
  for c,factors in component_factors:
   ce=math.inf;csbest=None
   for vv in itertools.product(d,repeat=len(c)):
    local_checked+=1;z=dict(zip(c,vv));score=-sum(net['unary'][v]*z[v] for v in c)
    for (a,b),w in factors:score-=w*(z[a] if a in z else st[a])*(z[b] if b in z else st[b])
    if score<ce:ce,csbest=score,z
   total+=ce;cur.update(csbest)
  checked+=1
  if total<best:best,beststate=total,cur
 conditional_ns=time.perf_counter_ns()-t
 t=time.perf_counter_ns();width=min_fill_upper_bound(net['nodes'],net['edges']);glob=jt.junction_tree_map(net['nodes'],net['edges'],net['unary'],net['pairwise'],d,order=width['elimination_order']);global_ns=time.perf_counter_ns()-t
 eg=energy(net['unary'],net['pairwise'],glob['state']);ec=energy(net['unary'],net['pairwise'],beststate);end=lock_inputs()
 return {'n_residents':n,'replicate':rep,'pattern':rep,'k':k,'nodes':len(net['nodes']),'factor_count':len(net['pairwise']),'boundary_nodes':boundary,'boundary_size':len(boundary),'cross_links':[[a,b,w] for a,b,w in links],'interior_component_sizes':sorted(map(len,cs)),'interior_component_count':len(cs),'interior_factorization_valid':valid,'boundary_assignments_checked':checked,'local_assignments_checked':local_checked,'expected_local_assignments':(len(d)**k)*sum(len(d)**len(c) for c in cs),'global_width':width['treewidth'],'global_energy':float(glob['energy']),'conditional_energy':float(best),'independent_global_energy':eg,'independent_conditional_energy':ec,'energy_gap':eg-ec,'states_valid':set(glob['state'])==set(net['nodes'])==set(beststate) and all(x in d for x in glob['state'].values()) and all(x in d for x in beststate.values()),'timing_ns':{'setup':setup,'aggregate_extraction':extract,'global_width_and_map':global_ns,'boundary_discovery_and_conditional_map':conditional_ns},'source_inputs_start':start,'source_inputs_end':end}
def worker(rep):
 lock=lock_inputs();return {'replicate':rep,'pid':os.getpid(),'started_inputs':lock,'cases':[run_case(n,rep,k) for n in SIZES for k in KS],'finished_inputs':lock_inputs()}
def main():
 if sys.argv[1:]==['--lock']:print(json.dumps({'locked_inputs':lock_inputs()},indent=2,sort_keys=True));return
 if len(sys.argv)==3 and sys.argv[1]=='--worker':print(json.dumps(worker(int(sys.argv[2])),sort_keys=True));return
 locked=lock_inputs()
 if not LOCK.exists() or json.loads(LOCK.read_text()).get('locked_inputs')!=locked:raise SystemExit('missing or stale lock')
 env=dict(os.environ);env.setdefault('OZMA_NO_LLM','1');env.setdefault('OZMA_SEED_PERSIST_DISABLED','1');env['PYTHONPATH']=str(ROOT/'runners/dsl/python')+os.pathsep+str(ROOT)+os.pathsep+str(ROOT/'scripts')+os.pathsep+env.get('PYTHONPATH','')
 runs=[json.loads(subprocess.run([sys.executable,str(Path(__file__).resolve()),'--worker',str(r)],cwd=ROOT,env=env,text=True,capture_output=True,check=True,timeout=240).stdout) for r in range(3)];post=lock_inputs();cases=[c for r in runs for c in r['cases']]
 checks={'fresh_workers':len({r['pid'] for r in runs})==3,'stable_sources':post==locked and all(r['started_inputs']==locked==r['finished_inputs'] for r in runs) and all(c['source_inputs_start']==locked==c['source_inputs_end'] for c in cases),'24_cases':len(cases)==24,'boundary_dimensions_exact':all(c['boundary_size']==c['k'] for c in cases),'factorization_valid':all(c['interior_factorization_valid'] for c in cases),'conditional_counts_exact':all(c['boundary_assignments_checked']==3**c['k'] and c['local_assignments_checked']==c['expected_local_assignments'] for c in cases),'energy_parity':all(abs(c['energy_gap'])<1e-7 and abs(c['global_energy']-c['independent_global_energy'])<1e-7 and abs(c['conditional_energy']-c['independent_conditional_energy'])<1e-7 for c in cases),'complete_valid_states':all(c['states_valid'] for c in cases),'positive_timings':all(all(v>0 for v in c['timing_ns'].values()) for c in cases)}
 payload={'schema_version':1,'run_id':'substrate-bigville-cross-boundary-map-v1-20260926','claim_boundary':'Controlled cross-resident factor perturbations over deterministic authored Bigville CAN models; exact conditional MAP correctness, not native factorization or natural boundary prevalence.','locked_inputs':locked,'post_run_inputs':post,'lock_sha256':sha(LOCK),'environment':{'python':sys.version,'platform':platform.platform()},'configuration':{'sizes':SIZES,'boundary_dimensions':KS,'replicates':3,'patterns':PATTERNS},'runs':runs,'checks':checks};OUT.write_text(json.dumps(payload,indent=2,sort_keys=True)+'\n');print(json.dumps({'output':str(OUT),'checks':checks},indent=2))
 if not all(checks.values()):raise SystemExit('capture validity or semantic gate failed')
if __name__=='__main__':main()

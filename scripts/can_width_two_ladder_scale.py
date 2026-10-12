#!/usr/bin/env python3
"""Scale exact CAN MAP on runtime-extracted binary ladders against rung DP."""
from __future__ import annotations
import hashlib,json,os,platform,random,resource,statistics,subprocess,sys,time,tracemalloc
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SIZES=(16,32,64,128,256,512)
REPLICATES=3
VOCAB=(-1.0,1.0)
PREREG=ROOT/'docs/research/engine_substrate/CAN_WIDTH_TWO_LADDER_SCALE_PREREG_20260925.md'
LOCK=ROOT/'evaluation/substrate_capability/can_width_two_ladder_scale_lock_20260925.json'
OUT=ROOT/'evaluation/reports/can_width_two_ladder_scale_20260925.json'
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def make_model(m,seed):
 rng=random.Random(seed); n=2*m
 unary={i:rng.randint(-8,8)/4.0 for i in range(n)}
 pair={}
 for r in range(m):
  pair[(2*r,2*r+1)]=rng.randint(-8,8)/4.0
  if r+1<m:
   pair[(2*r,2*(r+1))]=rng.randint(-8,8)/4.0
   pair[(2*r+1,2*(r+1)+1)]=rng.randint(-8,8)/4.0
 return unary,pair
def rung_dp(m,unary,pair):
 states=((-1.0,-1.0),(-1.0,1.0),(1.0,-1.0),(1.0,1.0))
 def local(r,state):
  a,b=state
  return -unary[2*r]*a-unary[2*r+1]*b-pair[(2*r,2*r+1)]*a*b
 costs={state:local(0,state) for state in states}; back={}
 ops=len(states)
 for r in range(1,m):
  nxt={}
  for state in states:
   choices=[]
   for prev in states:
    a,b=prev; c,d=state
    edge_cost=-(pair[(2*(r-1),2*r)]*a*c+pair[(2*(r-1)+1,2*r+1)]*b*d)
    choices.append((costs[prev]+edge_cost+local(r,state),prev))
   nxt[state],back[(r,state)]=min(choices); ops+=len(states)
  costs=nxt
 energy,state=min((costs[s],s) for s in states); assignment={2*m-2:state[0],2*m-1:state[1]}
 for r in range(m-1,0,-1):
  state=back[(r,state)]; assignment[2*r-2]=state[0]; assignment[2*r-1]=state[1]
 return energy,assignment,ops
def energy(unary,pair,state):
 return -sum(v*state[i] for i,v in unary.items())-sum(w*state[i]*state[j] for (i,j),w in pair.items())
def timed_jt(cjt,n,edges,unary,pair,vocab,order):
 tracemalloc.start(); t=time.perf_counter_ns()
 ans=cjt.junction_tree_map(list(range(n)),edges,unary,{frozenset(e):v for e,v in pair.items()},vocab,order=order)
 elapsed=time.perf_counter_ns()-t; _,peak=tracemalloc.get_traced_memory(); tracemalloc.stop()
 return ans,elapsed,peak
def worker(m,rep):
 import substrate_rs as sr
 import domains.can_junction_tree as cjt
 from domains.graph_treewidth import min_fill_upper_bound
 seed=20260925+m*1009+rep*65537; unary,pair=make_model(m,seed)
 s=sr.Substrate(); inner=s._inner; mt=inner.add_node('Microtheory',{'discrete_mode':'2state'})
 concepts=[inner.add_node('Concept',{'name':f'x{i}','external_field':unary[i],'identity_field':0.0,'state':0.0}) for i in range(2*m)]
 for node in concepts: inner.add_edge_unchecked(mt,'has_concept',node,{})
 for (i,j),w in pair.items():
  inner.add_edge_unchecked(concepts[i],'causal_influence',concepts[j],{'weight':w})
  inner.add_edge_unchecked(concepts[j],'causal_influence',concepts[i],{'weight':w})
 t=time.perf_counter_ns(); net=cjt.can_network_from_mt(s,mt); extract_ns=time.perf_counter_ns()-t
 local={node.value:i for i,node in enumerate(concepts)}
 ex_unary={local[i]:v for i,v in net['unary'].items()}
 ex_pair={tuple(sorted(local[i] for i in edge)):v for edge,v in net['pairwise'].items()}
 want_pair={tuple(sorted(k)):v for k,v in pair.items()}
 if ex_unary!=unary or ex_pair!=want_pair: raise AssertionError('runtime extraction differs from generated ladder')
 edges=[tuple(k) for k in ex_pair]
 t=time.perf_counter_ns(); order=min_fill_upper_bound(list(range(2*m)),edges); minfill_ns=time.perf_counter_ns()-t
 peo=list(range(2*m))
 oracle,oracle_state,ops=rung_dp(m,unary,pair)
 jt_pair,jt_ns,jt_peak=timed_jt(cjt,2*m,edges,unary,pair,VOCAB,order['elimination_order'])
 peo_pair,peo_ns,peo_peak=timed_jt(cjt,2*m,edges,unary,pair,VOCAB,peo)
 e1=energy(unary,pair,jt_pair['state']); e2=energy(unary,pair,peo_pair['state'])
 if abs(e1-oracle)>1e-9 or abs(e2-oracle)>1e-9: raise AssertionError('junction-tree energy disagrees with independent rung DP')
 if order['treewidth']!=2 or jt_pair['max_bag_size']!=3 or peo_pair['max_bag_size']!=3: raise AssertionError('ladder width/bag invariant failed')
 return {'rungs':m,'nodes':2*m,'edges':len(edges),'replicate':rep,'seed':seed,'treewidth_upper_bound':order['treewidth'],'minfill_bag_size':jt_pair['max_bag_size'],'rung_order_bag_size':peo_pair['max_bag_size'],'oracle_operations':ops,'minfill_energy_gap':e1-oracle,'rung_order_energy_gap':e2-oracle,'extraction_exact':True,'timing_ns':{'runtime_graph_extract':extract_ns,'min_fill_order':minfill_ns,'junction_tree_minfill':jt_ns,'junction_tree_rung_order':peo_ns},'traced_peak_bytes':{'minfill':jt_peak,'rung_order':peo_peak},'process_peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
def main():
 if len(sys.argv)==4 and sys.argv[1]=='--worker':
  print(json.dumps(worker(int(sys.argv[2]),int(sys.argv[3])),sort_keys=True)); return
 native=ROOT/'runners/dsl/python/substrate_rs/_native.abi3.so'
 locked={'preregistration_sha256':PREREG,'runner_sha256':Path(__file__).resolve(),'extractor_sha256':ROOT/'domains/can_junction_tree.py','treewidth_sha256':ROOT/'domains/graph_treewidth.py','native_sha256':native,'build_record_sha256':native.with_name('_native.build.json')}
 lock=json.loads(LOCK.read_text())
 if any(lock.get(k)!=sha(v) for k,v in locked.items()): raise SystemExit('ladder lock mismatch')
 stale=subprocess.check_output([sys.executable,'-c',"from domains.engine_provenance import build_is_stale; print('\\n'.join(build_is_stale('.')))" ],cwd=ROOT,text=True).strip()
 if stale: raise SystemExit('native build stale:\n'+stale)
 env=dict(os.environ); env['PYTHONPATH']=f"{ROOT/'runners/dsl/python'}:{ROOT}:{env.get('PYTHONPATH','')}"
 records=[]
 for m in SIZES:
  for rep in range(REPLICATES):
   p=subprocess.run([sys.executable,str(Path(__file__).resolve()),'--worker',str(m),str(rep)],cwd=ROOT,env=env,text=True,capture_output=True,check=True)
   r=json.loads(p.stdout.strip()); records.append(r); print(f"rungs={m} rep={rep} width={r['treewidth_upper_bound']} jt_ms={r['timing_ns']['junction_tree_minfill']/1e6:.3f}",flush=True)
 summary=[]
 for m in SIZES:
  group=[r for r in records if r['rungs']==m]
  summary.append({'rungs':m,'nodes':2*m,'edges':3*m-2,'replicates':len(group),'treewidth':2,'median_timing_ns':{k:int(statistics.median(r['timing_ns'][k] for r in group)) for k in group[0]['timing_ns']},'median_traced_peak_bytes':{k:int(statistics.median(r['traced_peak_bytes'][k] for r in group)) for k in group[0]['traced_peak_bytes']},'max_process_peak_rss_kib':max(r['process_peak_rss_kib'] for r in group),'median_oracle_operations':int(statistics.median(r['oracle_operations'] for r in group))})
 payload={'schema_version':1,'run_id':'can-width-two-ladder-scale-20260925-v1','scope':'exact binary MAP on runtime-extracted width-two ladders with independent four-state rung DP','claim_boundary':'one synthetic bounded-width topology; not natural-task locality, decomposition discovery cost, or native allocation totals','configuration':{'rungs':SIZES,'replicates':REPLICATES,'domain':VOCAB},'environment':{'python':platform.python_version(),'platform':platform.platform(),'processor':platform.processor()},'provenance':{'locked_inputs':{k:sha(v) for k,v in locked.items()},'lock_sha256':sha(LOCK),'git_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()},'checks':{'all_extractions_exact':all(r['extraction_exact'] for r in records),'all_width_two':all(r['treewidth_upper_bound']==2 and r['minfill_bag_size']==3 and r['rung_order_bag_size']==3 for r in records),'all_minfill_oracles_match':all(abs(r['minfill_energy_gap'])<1e-9 for r in records),'all_rung_order_oracles_match':all(abs(r['rung_order_energy_gap'])<1e-9 for r in records),'replicates_per_size':all(sum(r['rungs']==m for r in records)==REPLICATES for m in SIZES)},'summaries':summary,'runs':records}
 OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(json.dumps(payload,indent=2,sort_keys=True)+'\n')
 print(json.dumps({'checks':payload['checks'],'output':str(OUT)},indent=2))
 if not all(payload['checks'].values()): raise SystemExit('ladder evaluation invariant failed')
if __name__=='__main__': main()

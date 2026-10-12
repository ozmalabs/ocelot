#!/usr/bin/env python3
"""Measure exact MAP and ordering across binary grid-strip widths."""
from __future__ import annotations
import hashlib,json,os,platform,random,resource,statistics,subprocess,sys,time,tracemalloc
from itertools import product
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
HEIGHTS=(1,2,3,4,5); LENGTHS=(16,32,64,128); REPS=3; VOCAB=(-1.0,1.0)
PREREG=ROOT/'docs/research/engine_substrate/CAN_STRIP_WIDTH_PROFILE_V1_1_AMENDMENT_20260925.md'
LOCK=ROOT/'evaluation/substrate_capability/can_strip_width_profile_v1_1_lock_20260925.json'
OUT=ROOT/'evaluation/reports/can_strip_width_profile_v1_1_20260925.json'
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def make_model(h,m,seed):
 rng=random.Random(seed); n=h*m
 unary={i:rng.randint(-8,8)/4.0 for i in range(n)}; pair={}
 for c in range(m):
  for r in range(h-1): pair[(c*h+r,c*h+r+1)]=rng.randint(-8,8)/4.0
  if c+1<m:
   for r in range(h): pair[(c*h+r,(c+1)*h+r)]=rng.randint(-8,8)/4.0
 return unary,pair
def strip_dp(h,m,unary,pair):
 states=list(product(VOCAB,repeat=h))
 def local(c,s):
  z=-sum(unary[c*h+r]*s[r] for r in range(h))
  z-=sum(pair[(c*h+r,c*h+r+1)]*s[r]*s[r+1] for r in range(h-1))
  return z
 def transition(c,a,b):
  return -sum(pair[(c*h+r,(c+1)*h+r)]*a[r]*b[r] for r in range(h))
 costs={s:local(0,s) for s in states}; back={}; ops=len(states)
 for c in range(1,m):
  nxt={}
  for b in states:
   choices=[(costs[a]+transition(c-1,a,b)+local(c,b),a) for a in states]
   nxt[b],back[(c,b)]=min(choices); ops+=len(states)
  costs=nxt
 best,state=min((v,s) for s,v in costs.items()); assignment={}
 for r,val in enumerate(state): assignment[(m-1)*h+r]=val
 for c in range(m-1,0,-1):
  state=back[(c,state)]
  for r,val in enumerate(state): assignment[(c-1)*h+r]=val
 return best,assignment,ops
def score(unary,pair,state):
 return -sum(v*state[i] for i,v in unary.items())-sum(w*state[i]*state[j] for (i,j),w in pair.items())
def timed(cjt,n,edges,unary,pair,order):
 tracemalloc.start(); t=time.perf_counter_ns()
 ans=cjt.junction_tree_map(list(range(n)),edges,unary,{frozenset(e):v for e,v in pair.items()},VOCAB,order=order)
 ns=time.perf_counter_ns()-t; _,peak=tracemalloc.get_traced_memory(); tracemalloc.stop()
 return ans,ns,peak
def worker(h,m,rep):
 import substrate_rs as sr
 import domains.can_junction_tree as cjt
 from domains.graph_treewidth import min_fill_upper_bound
 seed=20260925+h*1000003+m*1009+rep*65537; unary,pair=make_model(h,m,seed)
 s=sr.Substrate(); inner=s._inner; mt=inner.add_node('Microtheory',{'discrete_mode':'2state'})
 nodes=[inner.add_node('Concept',{'name':f'x{i}','external_field':unary[i],'identity_field':0.0,'state':0.0}) for i in range(h*m)]
 for node in nodes: inner.add_edge_unchecked(mt,'has_concept',node,{})
 for (i,j),w in pair.items():
  inner.add_edge_unchecked(nodes[i],'causal_influence',nodes[j],{'weight':w}); inner.add_edge_unchecked(nodes[j],'causal_influence',nodes[i],{'weight':w})
 t=time.perf_counter_ns(); net=cjt.can_network_from_mt(s,mt); extract=time.perf_counter_ns()-t
 local={node.value:i for i,node in enumerate(nodes)}
 eu={local[i]:v for i,v in net['unary'].items()}
 ep={tuple(sorted(local[i] for i in e)):v for e,v in net['pairwise'].items()}
 expected={tuple(sorted(e)):v for e,v in pair.items()}
 if eu!=unary or ep!=expected: raise AssertionError('runtime extraction differs from strip generator')
 edges=list(ep)
 t=time.perf_counter_ns(); width=min_fill_upper_bound(list(range(h*m)),edges); minfill=time.perf_counter_ns()-t
 column_order=list(range(h*m)); oracle,oracle_state,ops=strip_dp(h,m,unary,pair)
 mf,mf_ns,mf_peak=timed(cjt,h*m,edges,unary,pair,width['elimination_order'])
 peo,peo_ns,peo_peak=timed(cjt,h*m,edges,unary,pair,column_order)
 eg1=score(unary,pair,mf['state'])-oracle; eg2=score(unary,pair,peo['state'])-oracle
 if width['treewidth']<h or mf['max_bag_size']!=width['treewidth']+1 or peo['max_bag_size']!=h+1: raise AssertionError('invalid min-fill upper bound or strip width certificate')
 if abs(eg1)>1e-9 or abs(eg2)>1e-9: raise AssertionError('exact inference differs from strip DP')
 return {'height':h,'length':m,'nodes':h*m,'edges':len(edges),'replicate':rep,'seed':seed,'treewidth_upper_bound':width['treewidth'],'certified_strip_width':h,'minfill_overestimate':width['treewidth']-h,'minfill_bag_size':mf['max_bag_size'],'column_order_bag_size':peo['max_bag_size'],'oracle_operations':ops,'minfill_energy_gap':eg1,'column_order_energy_gap':eg2,'extraction_exact':True,'timing_ns':{'graph_extract':extract,'min_fill_order':minfill,'junction_tree_minfill':mf_ns,'junction_tree_column_order':peo_ns},'traced_peak_bytes':{'minfill':mf_peak,'column_order':peo_peak},'process_peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
def main():
 if len(sys.argv)==5 and sys.argv[1]=='--worker':
  print(json.dumps(worker(int(sys.argv[2]),int(sys.argv[3]),int(sys.argv[4])),sort_keys=True)); return
 native=ROOT/'runners/dsl/python/substrate_rs/_native.abi3.so'
 locked={'preregistration_sha256':PREREG,'runner_sha256':Path(__file__).resolve(),'extractor_sha256':ROOT/'domains/can_junction_tree.py','treewidth_sha256':ROOT/'domains/graph_treewidth.py','native_sha256':native,'build_record_sha256':native.with_name('_native.build.json')}
 lock=json.loads(LOCK.read_text())
 if any(lock.get(k)!=sha(v) for k,v in locked.items()): raise SystemExit('strip profile lock mismatch')
 stale=subprocess.check_output([sys.executable,'-c',"from domains.engine_provenance import build_is_stale; print('\\n'.join(build_is_stale('.')))" ],cwd=ROOT,text=True).strip()
 if stale: raise SystemExit('native build stale:\n'+stale)
 env=dict(os.environ); env['PYTHONPATH']=f"{ROOT/'runners/dsl/python'}:{ROOT}:{env.get('PYTHONPATH','')}"
 records=[]
 for h in HEIGHTS:
  for m in LENGTHS:
   for rep in range(REPS):
    proc=subprocess.run([sys.executable,str(Path(__file__).resolve()),'--worker',str(h),str(m),str(rep)],cwd=ROOT,env=env,text=True,capture_output=True,check=True)
    rec=json.loads(proc.stdout.strip()); records.append(rec)
    print(f"h={h} m={m} rep={rep} width={rec['treewidth_upper_bound']} jt_ms={rec['timing_ns']['junction_tree_minfill']/1e6:.3f}",flush=True)
 summaries=[]
 for h in HEIGHTS:
  for m in LENGTHS:
   g=[r for r in records if r['height']==h and r['length']==m]
   summaries.append({'height':h,'length':m,'nodes':h*m,'edges':h*(m-1)+(h-1)*m,'replicates':len(g),'certified_strip_width':h,'median_minfill_width':int(statistics.median(r['treewidth_upper_bound'] for r in g)),'max_minfill_overestimate':max(r['minfill_overestimate'] for r in g),'median_timing_ns':{k:int(statistics.median(r['timing_ns'][k] for r in g)) for k in g[0]['timing_ns']},'median_traced_peak_bytes':{k:int(statistics.median(r['traced_peak_bytes'][k] for r in g)) for k in g[0]['traced_peak_bytes']},'max_process_peak_rss_kib':max(r['process_peak_rss_kib'] for r in g),'median_oracle_operations':int(statistics.median(r['oracle_operations'] for r in g))})
 checks={'all_extractions_exact':all(r['extraction_exact'] for r in records),'all_width_certificates_valid':all(r['treewidth_upper_bound']>=r['height'] and r['minfill_bag_size']==r['treewidth_upper_bound']+1 and r['column_order_bag_size']==r['height']+1 for r in records),'all_minfill_oracles_match':all(abs(r['minfill_energy_gap'])<1e-9 for r in records),'all_column_order_oracles_match':all(abs(r['column_order_energy_gap'])<1e-9 for r in records),'replicates_per_cell':len(records)==len(HEIGHTS)*len(LENGTHS)*REPS}
 payload={'schema_version':1,'run_id':'can-strip-width-profile-20260925-v1.1','scope':'exact binary MAP on runtime-extracted grid strips; independent transfer-matrix DP oracle','claim_boundary':'synthetic strip family only; no natural task locality or separator discovery claim','configuration':{'heights':HEIGHTS,'lengths':LENGTHS,'replicates':REPS,'domain':VOCAB},'environment':{'python':platform.python_version(),'platform':platform.platform(),'processor':platform.processor()},'provenance':{'locked_inputs':{k:sha(v) for k,v in locked.items()},'lock_sha256':sha(LOCK),'git_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()},'checks':checks,'summaries':summaries,'runs':records}
 OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(json.dumps(payload,indent=2,sort_keys=True)+'\n')
 print(json.dumps({'checks':checks,'output':str(OUT)},indent=2))
 if not all(checks.values()): raise SystemExit('strip profile invariant failed')
if __name__=='__main__': main()

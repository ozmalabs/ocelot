#!/usr/bin/env python3
"""Anonymous graph-only minimum-separator census over captured model task graphs."""
from __future__ import annotations
import hashlib,itertools,json,os,platform,subprocess,sys,time
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'runners/dsl/python'),str(ROOT)]
RUNNER=Path(__file__).resolve();PROTOCOL=ROOT/'docs/research/engine_substrate/LLM_TRANSPORT_VARIED_TOPOLOGY_SEPARATOR_CENSUS_V1_PREREG_20261003.md'
ANALYZER=ROOT/'evaluation/substrate_capability/analyze_llm_transport_varied_topology_separator_census_v1.py'
CAP=ROOT/'evaluation/reports/llm_cross_model_transport_v1_1_20261002.json'
CAP_ANALYSIS=ROOT/'evaluation/reports/llm_cross_model_transport_v1_1_analysis_20261002.json'
CAP_LOCK=ROOT/'evaluation/substrate_capability/llm_cross_model_transport_v1_1_lock_20261002.json'
BASE_PROTOCOL=ROOT/'docs/research/engine_substrate/LLM_CROSS_MODEL_TRANSPORT_V1_PREREG_20261002.md'
AMENDMENT=ROOT/'docs/research/engine_substrate/LLM_CROSS_MODEL_TRANSPORT_V1_1_AMENDMENT_20261002.md'
V1_CAPTURE=ROOT/'evaluation/reports/llm_transport_varied_topology_separator_census_v1_20261003.json'
V1_LOCK=ROOT/'evaluation/substrate_capability/llm_transport_varied_topology_separator_census_v1_lock_20261003.json'
V1_1_CAPTURE=ROOT/'evaluation/reports/llm_transport_varied_topology_separator_census_v1_1_20261003.json'
V1_1_LOCK=ROOT/'evaluation/substrate_capability/llm_transport_varied_topology_separator_census_v1_1_lock_20261003.json'
PREV_AMENDMENT=ROOT/'docs/research/engine_substrate/LLM_TRANSPORT_VARIED_TOPOLOGY_SEPARATOR_CENSUS_V1_1_AMENDMENT_20261003.md'
V1_2_AMENDMENT=ROOT/'docs/research/engine_substrate/LLM_TRANSPORT_VARIED_TOPOLOGY_SEPARATOR_CENSUS_V1_2_AMENDMENT_20261003.md'
EXPORTS={m:ROOT/f'evaluation/reports/llm_cross_model_transport_v1_{m}.npz' for m in ('qwen3_0_6b','qwen3_1_7b')}
LOCK=ROOT/'evaluation/substrate_capability/llm_transport_varied_topology_separator_census_v1_2_lock_20261003.json'
OUT=ROOT/'evaluation/reports/llm_transport_varied_topology_separator_census_v1_2_20261003.json'
REPS=3;FANINS=(1,2,4,8)
def digest(p):
 p=Path(p);b=p.read_bytes();return {'path':p.relative_to(ROOT).as_posix(),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
def sources():
 from domains import llm_native_graph as lng
 from substrate_rs import _native
 paths=[RUNNER,PROTOCOL,ANALYZER,CAP,CAP_ANALYSIS,CAP_LOCK,BASE_PROTOCOL,AMENDMENT,ROOT/'domains/llm_native_graph.py',ROOT/'domains/graph_treewidth.py',ROOT/'runners/dsl/python/substrate_rs/_native.build.json',Path(_native.__file__).resolve(),ROOT/'evaluation/substrate_capability/fixtures/llm_cross_model_transport_v1_corpus.json']
 for p in EXPORTS.values():paths.extend((p,p.with_suffix('.provenance.json'),p.with_suffix('.tokenization.json')))
 paths.extend((V1_CAPTURE,V1_LOCK,V1_1_CAPTURE,V1_1_LOCK,PREV_AMENDMENT,V1_2_AMENDMENT))
 return {'artifacts':[digest(p) for p in paths],'replicates':REPS,'fanins':list(FANINS),'mode_count':8,'heldout_per_hop':10,'hops':[[10,11],[11,12],[12,13],[13,14]],'ridge':1.0,'anonymization_seed':'20261003 + replicate*1000'}
def nid(v):return int(v.value if hasattr(v,'value') else v)
def components(nodes,edges,removed):
 left=set(nodes)-set(removed);adj={v:set() for v in left}
 for a,b in edges:
  if a in left and b in left:adj[a].add(b);adj[b].add(a)
 parts=[]
 while left:
  s=min(left);left.remove(s);stack=[s];part=[]
  while stack:
   u=stack.pop();part.append(u)
   for v in adj[u]&left:left.remove(v);stack.append(v)
  parts.append(sorted(part))
 return sorted(parts,key=lambda p:(len(p),p))
def min_separator(nodes,edges):
 tested=0
 for k in range(len(nodes)+1):
  candidates=[]
  for sep in itertools.combinations(sorted(nodes),k):
   tested+=1;cc=components(nodes,edges,set(sep))
   if len(cc)>=2:candidates.append({'separator':list(sep),'components':cc})
  if candidates:return k,tested,candidates
 return None,tested,[]
def worker(rep):
 from domains import llm_native_graph as lng
 before=sources();cap=json.loads(CAP.read_text());perm=np.random.default_rng(20261003+rep*1000).permutation(16);graphs={};matched=0
 for model,path in EXPORTS.items():
  z=np.load(path);tr=z['tr_c'];ho=z['ho_c'];layers=[int(x) for x in z['layers']];Ts=[lng.fit_transport(tr[h],tr[h+1],ridge=1.) for h in range(len(layers)-1)]
  rows=[r for run in cap['runs'] if run['model']==model for r in run['rows']]
  for r in rows:
   h=int(r['source_layer'])-layers[0];i=int(r['heldout_index']);fanin=int(r['fan_in']);x=ho[h,i];dom=np.argsort(-np.abs(x))[:8];T=Ts[h];edges=[]
   for q in range(8):
    for j in np.argsort(-np.abs(T[q,dom]),kind='stable')[:fanin]:
     if T[q,dom[j]]!=0:edges.append(tuple(sorted((int(j),8+q))))
   old=hashlib.sha256(json.dumps(sorted(edges)).encode()).hexdigest()
   if old!=r['topology_signature']:raise RuntimeError(f"reconstruction hash mismatch {model}/{h}/{i}/{fanin}")
   anon_edges=tuple(sorted(tuple(sorted((int(perm[a]),int(perm[b])))) for a,b in edges));sig=hashlib.sha256(json.dumps([16,anon_edges]).encode()).hexdigest()
   key=(model,fanin,sig)
   g=graphs.setdefault(key,{'model':model,'fan_in':fanin,'signature':sig,'source_signature':old,'nodes':list(range(16)),'edges':[list(e) for e in anon_edges],'rows_covered':0,'instances':set(),'widths':[],'components_before':None})
   if g['source_signature']!=old:raise RuntimeError('anonymous key merged distinct source topologies')
   g['rows_covered']+=1;g['instances'].add((int(r['source_layer']),i));g['widths'].append(int(r['width']));g['components_before']=components(list(range(16)),anon_edges,set())
   matched+=1
 results=[]
 for key,g in sorted(graphs.items()):
  t=time.perf_counter_ns();k,tested,candidates=min_separator(g['nodes'],[tuple(e) for e in g['edges']]);proposal_ns=time.perf_counter_ns()-t
  results.append({**g,'rows_covered':g['rows_covered'],'unique_instances_covered':len(g['instances']),'instances':sorted([list(x) for x in g['instances']]),'widths':sorted(set(g['widths'])),'components_before':g['components_before'],
   'minimum_separator_size':k,'subsets_tested':tested,'minimum_separators':candidates,'proposal_ns':proposal_ns})
 after=sources();return {'replicate':rep,'pid':os.getpid(),'matched_rows':matched,'unique_graphs':len(results),'graphs':results,'source_start':before,'source_end':after}
def main():
 args=sys.argv[1:]
 if args[:1]==['--worker']:print(json.dumps(worker(int(args[1])),sort_keys=True,separators=(',',':')));return 0
 if args==['--lock']:
  if LOCK.exists() or OUT.exists():raise SystemExit('refusing to overwrite lock/capture')
  LOCK.write_text(json.dumps({'schema':'LlmTransportVariedTopologySeparatorCensusV1Lock','sources':sources()},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return 0
 if args!=['--run']:raise SystemExit('usage: --lock, --run, or --worker REP')
 lock=json.loads(LOCK.read_text());before=sources()
 if before!=lock['sources']:raise SystemExit('source drift from lock')
 cap=json.loads(CAP.read_text());analysis=json.loads(CAP_ANALYSIS.read_text())
 if not all(cap['checks'].values()) or not analysis['gates_pass']:raise SystemExit('upstream capture gates failed')
 env={**os.environ,'PYTHONPATH':f"{ROOT/'runners/dsl/python'}:{ROOT}:{os.environ.get('PYTHONPATH','')}"};runs=[]
 for rep in range(REPS):
  p=subprocess.run([sys.executable,str(RUNNER),'--worker',str(rep)],cwd=ROOT,env=env,text=True,capture_output=True,timeout=900)
  if p.returncode:raise SystemExit(p.stderr[-3000:])
  x=json.loads(p.stdout);runs.append(x);print(f"rep={rep} pid={x['pid']} rows={x['matched_rows']} unique={x['unique_graphs']}",flush=True)
 after=sources();checks={'three_fresh_workers':len(runs)==REPS and len({r['pid'] for r in runs})==REPS,'full_960_row_reconstruction':all(r['matched_rows']==960 for r in runs),
  'upstream_gates':all(cap['checks'].values()) and analysis['gates_pass'],'source_stable':before==lock['sources']==after and all(r['source_start']==lock['sources']==r['source_end'] for r in runs),
 'source_topology_profiles_repeatable':all(sorted((g['model'],g['fan_in'],g['source_signature'],g['minimum_separator_size'],len(g['minimum_separators']),tuple(sorted(tuple(sorted(len(c) for c in s['components'])) for s in g['minimum_separators']))) for g in r['graphs'])==sorted((g['model'],g['fan_in'],g['source_signature'],g['minimum_separator_size'],len(g['minimum_separators']),tuple(sorted(tuple(sorted(len(c) for c in s['components'])) for s in g['minimum_separators']))) for g in runs[0]['graphs']) for r in runs)}
 OUT.write_text(json.dumps({'schema':'LlmTransportVariedTopologySeparatorCensusV1_2Capture','lock_sha256':hashlib.sha256(LOCK.read_bytes()).hexdigest(),'sources':before,'post_run_sources':after,'checks':checks,'failures':[],'runs':runs},indent=2,sort_keys=True)+'\n')
 print(json.dumps({'capture':OUT.relative_to(ROOT).as_posix(),'checks':checks},indent=2));return 0 if all(checks.values()) else 1
if __name__=='__main__':raise SystemExit(main())

#!/usr/bin/env python3
"""Source-locked graph-construction and runtime-partition scale probe."""
from __future__ import annotations
import hashlib,importlib.util,json,os,platform,random,resource,subprocess,sys,time
from pathlib import Path
from domains.engine_provenance import engine_preamble,rust_source_fingerprint,provenance_line
engine_preamble()
from substrate_rs import _native
ROOT=Path(__file__).resolve().parents[1]
PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_BIGVILLE_PARTITION_SCALE_PREREG_20260926.md'
LOCK=ROOT/'evaluation/substrate_capability/bigville_partition_scale_lock_20260926.json'
OUT=ROOT/'evaluation/reports/substrate_bigville_partition_scale_v1_20260926.json'
CAST=ROOT/'seeds/bigville_cast100.json'; WORLD=ROOT/'worlds/bigville_can_beliefs.py'
SIZES=(100,250,500); REPS=3; SAMPLES=31; SEED=20260928
FILES=['scripts/substrate_bigville_partition_scale_v1.py','scripts/analyze_substrate_bigville_partition_scale_v1.py','docs/research/engine_substrate/SUBSTRATE_BIGVILLE_PARTITION_SCALE_PREREG_20260926.md','seeds/bigville_cast100.json','worlds/bigville_can_beliefs.py','domains/engine_provenance.py','runners/dsl/src/graph.rs','runners/dsl/src/py.rs','runners/dsl/src/substrate.rs','runners/dsl/python/substrate_rs/_native.build.json']
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load_world():
 from worlds import bigville_can_beliefs as world
 return world
def owner_partition(inner,refs,mts,nid):
 mtpos={nid(mt):i for i,mt in enumerate(mts)}; owners={}
 for node,ref in refs.items():
  vals=[nid(x) for x in inner.in_neighbours(ref,'has_concept')]
  if len(vals)!=1 or vals[0] not in mtpos:raise RuntimeError('missing or ambiguous live owner')
  owners[node]=mtpos[vals[0]]
 return owners
def edge_list(inner,refs,nid):
 return [(int(a),nid(b)) for a in sorted(refs) for b in inner.neighbours(refs[a],'causal_influence')]
def components(edges,nodes):
 parent={n:n for n in nodes}
 def find(x):
  while parent[x]!=x: parent[x]=parent[parent[x]];x=parent[x]
  return x
 for a,b in edges:
  ra,rb=find(a),find(b)
  if ra!=rb:parent[rb]=ra
 out={}
 for n in nodes:out.setdefault(find(n),[]).append(n)
 return sorted((sorted(v) for v in out.values()),key=lambda v:v[0])
def timed(fn):
 fn();out=[]
 for _ in range(SAMPLES):
  t=time.perf_counter_ns();fn();out.append(time.perf_counter_ns()-t)
 return out
def worker(n,rep):
 from worlds import bigville_can_beliefs as world
 import substrate_rs as sr
 cast=json.loads(CAST.read_text())['residents']; residents=[]
 for i in range(n):
  base=cast[i%len(cast)]; row=dict(base);row['params']=dict(base['params']);row['index']=i
  if i>=len(cast):row['name']=f"{base['name']}__scale_{i:05d}"
  residents.append(row)
 init0=time.perf_counter_ns();outer=sr.Substrate();world.install_productions(outer);init_ns=time.perf_counter_ns()-init0;inner=outer._inner
 refs={};mts=[];resident_ns=[]
 for row in residents:
  t=time.perf_counter_ns();built=world.build_resident_can_mt(outer,row);resident_ns.append(time.perf_counter_ns()-t)
  mts.append(built['mt_node'])
  for ref in built['concepts'].values():refs[int(ref.value if hasattr(ref,'value') else ref)]=ref
 nid=lambda x:int(x.value if hasattr(x,'value') else x)
 if len(refs)!=5*n or len({nid(x) for x in mts})!=n:raise RuntimeError('wrong graph size or duplicate owner ids')
 nodes=sorted(refs)
 owner_fn=lambda:owner_partition(inner,refs,mts,nid)
 edges_fn=lambda:edge_list(inner,refs,nid)
 initial_owners=owner_fn();initial_edges=edges_fn();initial_components=components(initial_edges,nodes)
 by_owner={i:sorted(k for k,v in initial_owners.items() if v==i) for i in range(n)}
 if any(len(v)!=5 for v in by_owner.values()):raise RuntimeError('not five Concepts per live owner')
 if initial_edges and any(initial_owners[a]!=initial_owners[b] for a,b in initial_edges):raise RuntimeError('baseline has cross-owner edge')
 if sorted(sorted(v) for v in by_owner.values())!=initial_components:raise RuntimeError('causal components do not match owner frames')
 def component_call():return components(edges_fn(),nodes)
 def whole_call():
  o=owner_fn();e=edges_fn();c=components(e,nodes)
  return o,e,c
 owner_samples=timed(owner_fn);edge_samples=timed(edges_fn);component_samples=timed(lambda:components(initial_edges,nodes));whole_samples=timed(whole_call)
 o,e,c=whole_call()
 if o!=initial_owners or e!=initial_edges or c!=initial_components:raise RuntimeError('timed partition derivation changed')
 return {'size':n,'replicate':rep,'pid':os.getpid(),'resident_count':len(mts),'concept_count':len(refs),'directed_edge_count':len(initial_edges),'owner_frame_sizes':[len(by_owner[i]) for i in range(n)],'component_count':len(initial_components),'runtime_setup_and_production_ns':init_ns,'resident_build_samples_ns':resident_ns,'resident_build_total_ns':sum(resident_ns),'owner_discovery_samples_ns':owner_samples,'edge_extraction_samples_ns':edge_samples,'component_derivation_samples_ns':component_samples,'composed_partition_samples_ns':whole_samples,'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'native_path':str(Path(_native.__file__).resolve()),'native_sha256':sha(_native.__file__),'engine_provenance':provenance_line()}
def main():
 if len(sys.argv)>1 and sys.argv[1]=='--worker':
  print(json.dumps(worker(int(sys.argv[2]),int(sys.argv[3]))));return
 schedule=[(n,r) for n in SIZES for r in range(REPS)];random.Random(SEED).shuffle(schedule)
 env=os.environ.copy();env['PYTHONPATH']=str(ROOT/'runners/dsl/python')+os.pathsep+str(ROOT)
 if len(sys.argv)>1 and sys.argv[1]=='--lock':
  doc={'schema_version':1,'design':{'sizes':SIZES,'replicates':REPS,'timing_samples':SAMPLES,'seed':SEED},'locked_inputs':{'files_sha256':{p:sha(ROOT/p) for p in FILES},'native_path':str(Path(_native.__file__).resolve()),'native_sha256':sha(_native.__file__),'rust_source_fingerprint':rust_source_fingerprint()}}
  print(json.dumps(doc,indent=2,sort_keys=True));return
 lock=json.loads(LOCK.read_text());expected={p:sha(ROOT/p) for p in FILES}
 if lock['locked_inputs']['files_sha256']!=expected or lock['locked_inputs']['native_sha256']!=sha(_native.__file__) or lock['locked_inputs']['rust_source_fingerprint']!=rust_source_fingerprint():raise RuntimeError('locked sources/native build drifted')
 workers=[]
 for n,r in schedule:
  cp=subprocess.run([sys.executable,__file__,'--worker',str(n),str(r)],env=env,text=True,capture_output=True,check=True)
  workers.append(json.loads(cp.stdout.strip().splitlines()[-1]));print(f'frames={n} rep={r} pid={workers[-1]["pid"]} concepts={workers[-1]["concept_count"]}',file=sys.stderr,flush=True)
 doc={'protocol':'BIGVILLE_PARTITION_SCALE_V1','schedule':[list(x) for x in schedule],'locked_inputs':lock['locked_inputs'],'lock_sha256':sha(LOCK),'native':{'path':str(Path(_native.__file__).resolve()),'sha256':sha(_native.__file__)},'environment':{'python':platform.python_version(),'platform':platform.platform()},'workers':workers}
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(doc,indent=2,sort_keys=True)+'\n');print(json.dumps({'output':str(OUT),'workers':len(workers)}))
if __name__=='__main__':main()

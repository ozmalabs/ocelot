#!/usr/bin/env python3
"""Measure shared-codebook GenInfer scaling with frame-tagged parts/observations."""
from __future__ import annotations
import hashlib,json,os,platform,resource,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python')]
from domains.engine_provenance import build_is_stale,provenance_line
from substrate.boot_core import boot_core
from substrate.seed_loader import manifest_for
from domains import reflective_faculty as rf
from substrate_rs import _native
RUNNER=Path(__file__).resolve()
PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_GENINFER_MULTIPART_CODEBOOK_SCALING_V1_PREREG_20261003.md'
ANALYZER=ROOT/'evaluation/substrate_capability/analyze_substrate_geninfer_multipart_codebook_scaling_v1.py'
LOCK=ROOT/'evaluation/substrate_capability/substrate_geninfer_multipart_codebook_scaling_v1_lock_20261003.json'
OUT=ROOT/'evaluation/reports/substrate_geninfer_multipart_codebook_scaling_v1_20261003.json'
FRAME_COUNTS=(1,2,4,8,16)
REPEATS=(1,2,3)
POINTS=[(0,0),(1,0),(0,1),(1,1)]
DIM_TYPES=['pred','coord:x','coord:y','value']
MATRICES=[[2,1,1,1],[2,-1,1,1],[2,1,1,2],[1,1,1,2]]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def seed_closure():
 pending=[*__import__('substrate.boot_core',fromlist=['CORE_SEEDS']).CORE_SEEDS,'shape_decode_loop'];seen=set()
 while pending:
  name=str(pending.pop())
  if name in seen:continue
  seen.add(name);pending.extend(str(x) for x in manifest_for(name).get('depends_on',()))
 return sorted(f'seeds/{x}.json' for x in seen)
def source_paths():
 code=['domains/engine_provenance.py','domains/reflective_faculty.py','substrate/boot_core.py','substrate/seed_loader.py',
  'runners/dsl/src/shape_decode.rs','runners/dsl/src/term.rs','runners/dsl/src/graph.rs','runners/dsl/src/substrate.rs',
  'runners/dsl/src/rewrite.rs','runners/dsl/src/py.rs','runners/dsl/src/persist.rs','runners/dsl/src/grammar.rs',
  'runners/dsl/src/sym.rs','runners/dsl/src/lib.rs','runners/dsl/Cargo.toml','runners/dsl/Cargo.lock',
  'runners/dsl/python/substrate_rs/__init__.py','runners/dsl/python/substrate_rs/_native.build.json',
  str(RUNNER.relative_to(ROOT)),str(PROTOCOL.relative_to(ROOT)),str(ANALYZER.relative_to(ROOT))]
 return sorted(set((*code,*seed_closure())))
def frozen():
 native=Path(_native.__file__).resolve()
 return {'source_sha256':{x:sha(ROOT/x) for x in source_paths()},'native_path':str(native),'native_sha256':sha(native),'engine':provenance_line()}
def cases():return [{'id':f'global_k{k}_r{r}','frame_count':k,'repeat':r} for k in FRAME_COUNTS for r in REPEATS]
def matrix_apply(m,rows):
 a,b,c,d=m;return [[x[0],a*x[1]+b*x[2],c*x[1]+d*x[2],x[3]] for x in rows]
def rows(frame):return [[f'frame{frame}_p{i}',*POINTS[i],'signal'] for i in range(len(POINTS))]
def rss_kib():return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
def generators(sub):
 result=[]
 for node in sub.nodes('DimensionGenerator'):
  a=sub.node(node)['attrs']
  if a.get('kind')=='linear':result.append({'name':a.get('name'),'matrix':list(a.get('matrix') or [])})
 return result
def run_case(case):
 if build_is_stale(str(ROOT)):raise RuntimeError('native engine stale')
 source0=frozen();sub,agent=boot_core();native=rf._native_eval2(sub);rf._ensure_shape_decode_loop(sub,native,agent)
 sub.set_attr(agent,'gen_infer_enabled',1.0);target_rows=[];obs_specs=[];frame_parts=[]
 for j in range(case['frame_count']):
  base=rows(j);m=MATRICES[j%len(MATRICES)];goal=matrix_apply(m,base)
  sub.add_node('ShapeSignature',{'name':f'frame{j}_base','signature':json.dumps(base),'kind':'faculty',
   'faculty':'multipart_scaling','dim_types':DIM_TYPES,'frame_id':j})
  obs=sub.add_node('Observation',{'signature':goal,'key':['multipart_scaling',case['id'],j],
   'status':'decoded','residual':goal,'decoded_epoch':sub.node(agent)['attrs'].get('codebook_epoch') or 0.0,
   'dim_types':DIM_TYPES,'frame_id':j})
  sub.add_edge(agent,'observed',obs);target_rows.append({'frame':j,'matrix':m,'base':base,'goal':goal,'obs':obs})
  frame_parts.append({'frame':j,'shape_name':f'frame{j}_base','eligible':True})
 # The direct Term diagnostic reads `checked` before closure and is pure. It
 # measures the complete initial shared-codebook candidate volume per query.
 pre_nodes=len(list(sub.nodes()));pre_edges=sub.edge_count();kernel=[]
 for item in target_rows:
  result=sub._inner.evaluate({'type':'GenInfer','goal':{'type':'Lit','value':item['goal']},'max_dims':2,'field':'checked'}, {})
  kernel.append({'frame':item['frame'],'checked':int(result)})
 diagnostic_state_unchanged=pre_nodes==len(list(sub.nodes())) and pre_edges==sub.edge_count()
 hwm0=rss_kib();cpu0=time.process_time_ns();t0=time.perf_counter_ns();closure_work=int(native.run_rules())
 closure_wall=time.perf_counter_ns()-t0;closure_cpu=time.process_time_ns()-cpu0;hwm1=rss_kib()
 outputs=[]
 for item in target_rows:
  obs=item['obs'];attrs=sub.node(obs)['attrs'];receipts=[]
  for node in sub.neighbours(obs,'has_transform'):
   a=sub.node(node)['attrs'];receipts.append({k:a.get(k) for k in ('source','generator','generators','base','dim','dims','k','ks','transforms') if k in a})
  outputs.append({'frame':item['frame'],'matrix':item['matrix'],'status':attrs.get('status'),
   'residual':attrs.get('residual'),'receipts':receipts,
   'oracle_exact':item['goal']==matrix_apply(item['matrix'],item['base'])})
 parts_seen=[]
 for node in sub.nodes('ShapeSignature'):
  a=sub.node(node)['attrs'];dts=a.get('dim_types')
  if dts and sum(str(x).startswith('coord:') for x in dts)==2:
   parts_seen.append({'name':a.get('name'),'frame_id':a.get('frame_id')})
 return {'pid':os.getpid(),'case':case,'eligible_parts_before_closure':frame_parts,
  'eligible_shape_parts_after_closure':parts_seen,'initial_candidate_checks_by_frame':kernel,
  'initial_candidate_checks_total':sum(x['checked'] for x in kernel),
  'candidate_checks_expected_per_part':2400,'diagnostic_state_unchanged':diagnostic_state_unchanged,
  'outputs':outputs,'linear_generators_after_closure':generators(sub),
  'closure_work':closure_work,'closure_wall_ns':closure_wall,'closure_cpu_ns':closure_cpu,
  'hwm_before_kib':hwm0,'hwm_after_kib':hwm1,'hwm_delta_kib':max(0,hwm1-hwm0),
  'graph_nodes':len(list(sub.nodes())),'graph_edges':sub.edge_count(),
  'source_stable':source0==frozen(),'source_before':source0,'source_after':frozen()}
def main():
 args=sys.argv[1:]
 if args==['--lock']:
  if LOCK.exists() or OUT.exists():raise SystemExit('refusing to overwrite lock/capture')
  if build_is_stale(str(ROOT)):raise SystemExit('native engine stale')
  LOCK.write_text(json.dumps({'schema':'GenInferMultipartCodebookScalingV1Lock','sources':frozen(),
   'cases':cases(),'frame_counts':FRAME_COUNTS,'repeats':REPEATS,'maps':MATRICES,
   'candidate_formula_per_query':'eligible_parts*((2B+1)^4-1)','B':3,
   'diagnostic':'pure direct GenInfer Term field=checked before one shared production closure'},indent=2,sort_keys=True)+'\n')
  print(LOCK.relative_to(ROOT));return 0
 if len(args)==2 and args[0]=='--worker':
  lock=json.loads(LOCK.read_text());case=next((x for x in lock['cases'] if x['id']==args[1]),None)
  if not case:raise SystemExit('unknown case')
  if frozen()!=lock['sources']:raise SystemExit('source drift')
  print(json.dumps(run_case(case),sort_keys=True));return 0
 if args!=['--run']:raise SystemExit('usage: --lock | --worker ID | --run')
 lock=json.loads(LOCK.read_text())
 if frozen()!=lock['sources']:raise SystemExit('source/native drift from lock')
 env=dict(os.environ);env.setdefault('OZMA_NO_LLM','1');env.setdefault('OZMA_SEED_PERSIST_DISABLED','1')
 env['PYTHONPATH']=str(ROOT/'runners/dsl/python')+os.pathsep+str(ROOT)+os.pathsep+env.get('PYTHONPATH','');results=[]
 for case in lock['cases']:
  proc=subprocess.run([sys.executable,str(RUNNER),'--worker',case['id']],cwd=ROOT,env=env,text=True,capture_output=True,check=True,timeout=300)
  results.append(json.loads(proc.stdout))
 if frozen()!=lock['sources'] or not all(x['source_stable'] for x in results):raise SystemExit('source drift during capture')
 OUT.write_text(json.dumps({'schema':'GenInferMultipartCodebookScalingV1Results',
  'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'host':platform.platform(),
  'lock_sha256':sha(LOCK),'source_manifest':frozen(),'cases':results},indent=2,sort_keys=True)+'\n')
 print(json.dumps({'output':OUT.relative_to(ROOT).as_posix(),'case_count':len(results),'source_stable':True},sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())

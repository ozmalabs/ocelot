#!/usr/bin/env python3
"""Compare shared-codebook GenInfer with frame-isolated closure totals."""
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
PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_GENINFER_FRAME_ISOLATION_COMPARISON_V1_1_PREREG_20261003.md'
ANALYZER=ROOT/'evaluation/substrate_capability/analyze_geninfer_frame_isolation_v1_1.py'
LOCK=ROOT/'evaluation/substrate_capability/geninfer_frame_isolation_v1_1_lock_20261003.json'
OUT=ROOT/'evaluation/reports/geninfer_frame_isolation_v1_1_20261003.json'
BASE_RAW=ROOT/'evaluation/reports/substrate_geninfer_multipart_codebook_scaling_v1_20261003.json'
BASE_LOCK=ROOT/'evaluation/substrate_capability/substrate_geninfer_multipart_codebook_scaling_v1_lock_20261003.json'
BASE_ANALYSIS=ROOT/'evaluation/reports/substrate_geninfer_multipart_codebook_scaling_v1_analysis_20261003.json'
POINTS=[(0,0),(1,0),(0,1),(1,1)]
DT=['pred','coord:x','coord:y','value']
MAPS=[[2,1,1,1],[2,-1,1,1],[2,1,1,2],[1,1,1,2]]
KS=(1,2,4,8,16);REPEATS=(1,2,3)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def seed_closure():
 pending=[*__import__('substrate.boot_core',fromlist=['CORE_SEEDS']).CORE_SEEDS,'shape_decode_loop'];seen=set()
 while pending:
  name=str(pending.pop())
  if name in seen:continue
  seen.add(name);pending.extend(str(x) for x in manifest_for(name).get('depends_on',()))
 return sorted(f'seeds/{x}.json' for x in seen)
def source_paths():
 base=['domains/engine_provenance.py','domains/reflective_faculty.py','substrate/boot_core.py','substrate/seed_loader.py',
  'runners/dsl/src/shape_decode.rs','runners/dsl/src/term.rs','runners/dsl/src/graph.rs','runners/dsl/src/substrate.rs',
  'runners/dsl/src/rewrite.rs','runners/dsl/src/py.rs','runners/dsl/src/persist.rs','runners/dsl/src/grammar.rs',
  'runners/dsl/src/sym.rs','runners/dsl/src/lib.rs','runners/dsl/Cargo.toml','runners/dsl/Cargo.lock',
  'runners/dsl/python/substrate_rs/__init__.py','runners/dsl/python/substrate_rs/_native.build.json',
  str(RUNNER.relative_to(ROOT)),str(PROTOCOL.relative_to(ROOT)),str(ANALYZER.relative_to(ROOT))]
 return sorted(set((*base,*seed_closure())))
def frozen():
 native=Path(_native.__file__).resolve()
 return {'source_sha256':{x:sha(ROOT/x) for x in source_paths()},'native_path':str(native),'native_sha256':sha(native),
  'engine':provenance_line(),'baseline_artifacts_sha256':{p:sha(ROOT/p) for p in (
   'evaluation/reports/substrate_geninfer_multipart_codebook_scaling_v1_20261003.json',
   'evaluation/reports/substrate_geninfer_multipart_codebook_scaling_v1_analysis_20261003.json',
   'evaluation/substrate_capability/substrate_geninfer_multipart_codebook_scaling_v1_lock_20261003.json')}}
def apply(m,rows):
 a,b,c,d=m;return [[x[0],a*x[1]+b*x[2],c*x[1]+d*x[2],x[3]] for x in rows]
def make_rows(frame):return [[f'frame{frame}_p{i}',*pt,'signal'] for i,pt in enumerate(POINTS)]
def rss_kib():return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
def worker(k,rep,frame):
 if build_is_stale(str(ROOT)):raise RuntimeError('native engine stale')
 source0=frozen();sub,agent=boot_core();native=rf._native_eval2(sub);rf._ensure_shape_decode_loop(sub,native,agent);sub.set_attr(agent,'gen_infer_enabled',1.0)
 m=MAPS[frame%len(MAPS)];base=make_rows(frame);goal=apply(m,base)
 sub.add_node('ShapeSignature',{'name':f'frame{frame}_base','signature':json.dumps(base),'kind':'faculty',
  'faculty':'frame_isolation','dim_types':DT,'frame_id':frame})
 obs=sub.add_node('Observation',{'signature':goal,'key':['frame_isolation',k,rep,frame],
  'status':'decoded','residual':goal,'dim_types':DT,'frame_id':frame});sub.add_edge(agent,'observed',obs)
 before_nodes=len(list(sub.nodes()));before_edges=sub.edge_count();hwm0=rss_kib();cpu0=time.process_time_ns();t0=time.perf_counter_ns()
 work=int(native.run_rules());wall=time.perf_counter_ns()-t0;cpu=time.process_time_ns()-cpu0;hwm1=rss_kib()
 attrs=sub.node(obs)['attrs'];receipts=[]
 for node in sub.neighbours(obs,'has_transform'):
  a=sub.node(node)['attrs'];receipts.append({x:a.get(x) for x in ('source','generator','generators','base','dim','dims','k','ks','transforms') if x in a})
 gens=[]
 for node in sub.nodes('DimensionGenerator'):
  a=sub.node(node)['attrs']
  if a.get('kind')=='linear':gens.append({'name':a.get('name'),'matrix':list(a.get('matrix') or [])})
 return {'pid':os.getpid(),'k':k,'repeat':rep,'frame':frame,'matrix':m,'status':attrs.get('status'),
  'receipts':receipts,'oracle_exact':goal==apply(m,base),'linear_generators':gens,
  'eligible_part_count':1,'expected_candidate_checks':2400,'closure_work':work,
  'closure_wall_ns':wall,'closure_cpu_ns':cpu,'hwm_before_kib':hwm0,'hwm_after_kib':hwm1,
  'hwm_delta_kib':max(0,hwm1-hwm0),'nodes_before':before_nodes,'nodes_after':len(list(sub.nodes())),
  'edges_after':sub.edge_count(),'source_stable':source0==frozen(),'source_before':source0,'source_after':frozen()}
def main():
 args=sys.argv[1:]
 if args==['--lock']:
  if LOCK.exists() or OUT.exists():raise SystemExit('refusing to overwrite lock/capture')
  if build_is_stale(str(ROOT)):raise SystemExit('native engine stale')
  baseline=json.loads(BASE_RAW.read_text());analysis=json.loads(BASE_ANALYSIS.read_text())
  if not analysis.get('gates_pass'):raise SystemExit('shared baseline did not pass')
  LOCK.write_text(json.dumps({'schema':'GenInferFrameIsolationV1_1Lock','sources':frozen(),
   'frame_counts':KS,'repeats':REPEATS,'maps':MAPS,'baseline_capture_utc':baseline['captured_utc'],
   'baseline_case_count':len(baseline['cases']),'baseline_analysis_pass':analysis['gates_pass'],
   'candidate_checks_per_isolated_frame':2400},indent=2,sort_keys=True)+'\n')
  print(LOCK.relative_to(ROOT));return 0
 if len(args)==4 and args[0]=='--worker':
  if frozen()!=json.loads(LOCK.read_text())['sources']:raise SystemExit('source/baseline drift')
  print(json.dumps(worker(int(args[1]),int(args[2]),int(args[3])),sort_keys=True));return 0
 if args!=['--run']:raise SystemExit('usage: --lock | --worker K REP FRAME | --run')
 lock=json.loads(LOCK.read_text())
 if frozen()!=lock['sources']:raise SystemExit('source/baseline drift from lock')
 env=dict(os.environ);env.setdefault('OZMA_NO_LLM','1');env.setdefault('OZMA_SEED_PERSIST_DISABLED','1')
 env['PYTHONPATH']=str(ROOT/'runners/dsl/python')+os.pathsep+str(ROOT)+os.pathsep+env.get('PYTHONPATH','');groups=[]
 for k in lock['frame_counts']:
  for rep in lock['repeats']:
   frames=[]
   for j in range(k):
    p=subprocess.run([sys.executable,str(RUNNER),'--worker',str(k),str(rep),str(j)],cwd=ROOT,env=env,
     text=True,capture_output=True,check=True,timeout=300)
    frames.append(json.loads(p.stdout))
   groups.append({'k':k,'repeat':rep,'frames':frames,'isolated_total_wall_ns':sum(x['closure_wall_ns'] for x in frames),
    'isolated_total_cpu_ns':sum(x['closure_cpu_ns'] for x in frames),'isolated_peak_delta_kib':max(x['hwm_delta_kib'] for x in frames)})
 if frozen()!=lock['sources'] or not all(x['source_stable'] for g in groups for x in g['frames']):raise SystemExit('source drift during capture')
 OUT.write_text(json.dumps({'schema':'GenInferFrameIsolationV1_1Results','captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
  'host':platform.platform(),'lock_sha256':sha(LOCK),'source_manifest':frozen(),'groups':groups},indent=2,sort_keys=True)+'\n')
 print(json.dumps({'output':OUT.relative_to(ROOT).as_posix(),'groups':len(groups),'isolated_frames':sum(len(x['frames']) for x in groups),'source_stable':True},sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())

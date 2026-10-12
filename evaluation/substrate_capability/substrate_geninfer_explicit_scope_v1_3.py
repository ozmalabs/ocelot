#!/usr/bin/env python3
"""Measure scoped versus global GenInfer with fail-closed scope controls."""
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
PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_GENINFER_EXPLICIT_SCOPE_V1_3_PREREG_20261003.md'
ANALYZER=ROOT/'evaluation/substrate_capability/analyze_substrate_geninfer_explicit_scope_v1_3.py'
LOCK=ROOT/'evaluation/substrate_capability/substrate_geninfer_explicit_scope_v1_3_lock_20261003.json'
OUT=ROOT/'evaluation/reports/substrate_geninfer_explicit_scope_v1_3_20261003.json'
KS=(1,2,4,8,16);REPEATS=(1,2,3)
POINTS=[(0,0),(1,0),(0,1),(1,1)];DT=['pred','coord:x','coord:y','value']
MAPS=[[2,1,1,1],[2,-1,1,1],[2,1,1,2],[1,1,1,2]]
MODES=('unscoped_global','explicit_global','frame_scoped')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def seed_closure():
 pending=[*__import__('substrate.boot_core',fromlist=['CORE_SEEDS']).CORE_SEEDS,'shape_decode_loop'];seen=set()
 while pending:
  name=str(pending.pop())
  if name in seen:continue
  seen.add(name);pending.extend(str(x) for x in manifest_for(name).get('depends_on',()))
 return sorted(f'seeds/{x}.json' for x in seen)
def source_paths():
 core=['domains/engine_provenance.py','domains/reflective_faculty.py','substrate/boot_core.py','substrate/seed_loader.py',
  'runners/dsl/src/shape_decode.rs','runners/dsl/src/term.rs','runners/dsl/src/reflect.rs','runners/dsl/src/jsonio.rs',
  'runners/dsl/src/graph.rs','runners/dsl/src/substrate.rs','runners/dsl/src/rewrite.rs','runners/dsl/src/py.rs',
  'runners/dsl/src/persist.rs','runners/dsl/src/grammar.rs','runners/dsl/src/sym.rs','runners/dsl/src/lib.rs',
  'runners/dsl/Cargo.toml','runners/dsl/Cargo.lock','runners/dsl/python/substrate_rs/__init__.py',
  'runners/dsl/python/substrate_rs/_native.build.json',str(RUNNER.relative_to(ROOT)),
  str(PROTOCOL.relative_to(ROOT)),str(ANALYZER.relative_to(ROOT))]
 return sorted(set((*core,*seed_closure())))
def frozen():
 native=Path(_native.__file__).resolve()
 return {'source_sha256':{x:sha(ROOT/x) for x in source_paths()},'native_path':str(native),
  'native_sha256':sha(native),'engine':provenance_line(),
  'native_build_manifest_sha256':sha(ROOT/'runners/dsl/python/substrate_rs/_native.build.json')}
def cases():
 out=[]
 for mode in MODES:
  for k in KS:
   for rep in REPEATS:out.append({'id':f'{mode}_k{k}_r{rep}','kind':'positive','mode':mode,'k':k,'repeat':rep})
 for scope_mode in ('scope_mismatch','scope_missing'):
  for mi in range(len(MAPS)):
   for rep in REPEATS:out.append({'id':f'{scope_mode}_m{mi}_r{rep}','kind':scope_mode,'matrix_index':mi,'repeat':rep})
 return out
def apply(m,rows):
 a,b,c,d=m;return [[x[0],a*x[1]+b*x[2],c*x[1]+d*x[2],x[3]] for x in rows]
def make_rows(frame):return [[f'frame{frame}_p{i}',*point,'signal'] for i,point in enumerate(POINTS)]
def rss_kib():return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
def gen_inventory(sub):
 out=[]
 for node in sub.nodes('DimensionGenerator'):
  a=sub.node(node)['attrs']
  if a.get('kind')=='linear':out.append({'name':a.get('name'),'matrix':list(a.get('matrix') or [])})
 return out
def term_checked(sub,goal,scope,required):
 node_count=len(list(sub.nodes()));edge_count=sub.edge_count()
 query={'type':'GenInfer','goal':{'type':'Lit','value':goal},'max_dims':2,'field':'checked',
  'scope':{'type':'Lit','value':scope},'require_scope':{'type':'Lit','value':required}}
 checked=int(sub._inner.evaluate(query,{}))
 unchanged=node_count==len(list(sub.nodes())) and edge_count==sub.edge_count()
 return checked,unchanged
def make_scope(sub,scope_id,case_id,frame,base,task_goal):
 payload=json.dumps({'case_id':case_id,'frame':frame,'base':base,'goal':task_goal},sort_keys=True,separators=(',',':'))
 digest=hashlib.sha256(payload.encode()).hexdigest()
 scope=sub.add_node('FrameScope',{'scope_id':scope_id,'frame':frame,'case_id':case_id,
  'provenance_kind':'locked_synthetic_frame_assignment','provenance_sha256':digest})
 return scope,digest
def attach_part(sub,agent,case_id,frame,scope_id,mode):
 m=MAPS[frame%len(MAPS)];base=make_rows(frame);goal=apply(m,base)
 attrs={'name':f'frame{frame}_base','signature':json.dumps(base),'kind':'faculty','faculty':'explicit_scope',
  'dim_types':DT,'frame_id':frame}
 if scope_id is not None:attrs['scope_id']=scope_id
 part=sub.add_node('ShapeSignature',attrs);scope,digest=make_scope(sub,scope_id or f'audit-global-{case_id}-{frame}',case_id,frame,base,goal)
 oattrs={'signature':goal,'key':['explicit_scope',case_id,frame],'status':'decoded','residual':goal,
  'decoded_epoch':0.0,'dim_types':DT,'frame_id':frame}
 if scope_id is not None:oattrs['scope_id']=scope_id
 obs=sub.add_node('Observation',oattrs)
 sub.add_edge(agent,'observed',obs)
 return {'frame':frame,'matrix':m,'base':base,'goal':goal,'part':part,'obs':obs,'scope_id':scope_id,
  'scope_node':scope,'provenance_sha256':digest}
def receipt_data(sub,obs):
 out=[]
 for node in sub.neighbours(obs,'has_transform'):
  a=sub.node(node)['attrs'];out.append({k:a.get(k) for k in ('source','generator','generators','base','dim','dims','k','ks','transforms') if k in a})
 return out
def execute(case):
 if build_is_stale(str(ROOT)):raise RuntimeError('native engine stale')
 before=frozen();sub,agent=boot_core();native=rf._native_eval2(sub);rf._ensure_shape_decode_loop(sub,native,agent)
 sub.set_attr(agent,'gen_infer_enabled',1.0);specs=[];checks=[]
 is_scoped=case.get('mode','') in ('explicit_global','frame_scoped') or case['kind'] in ('scope_mismatch','scope_missing')
 if is_scoped:sub.set_attr(agent,'gen_infer_scope_required',1.0)
 if case['kind']=='positive':
  k=case['k'];mode=case['mode'];all_scope='shared_'+case['id'] if mode=='explicit_global' else None
  for j in range(k):
   sid=(f'scope_{case["id"]}_frame{j}' if mode=='frame_scoped' else all_scope)
   specs.append(attach_part(sub,agent,case['id'],j,sid,mode))
 else:
  mi=case['matrix_index'];m=MAPS[mi];base=make_rows(mi);goal=apply(m,base);sid=f'scope_{case["id"]}_base'
  part=sub.add_node('ShapeSignature',{'name':f'frame{mi}_base','signature':json.dumps(base),'kind':'faculty',
   'faculty':'scope_control','dim_types':DT,'scope_id':sid,'frame_id':mi})
  scope,digest=make_scope(sub,sid,case['id'],mi,base,goal)
  osid='unregistered_scope' if case['kind']=='scope_mismatch' else None
  oattrs={'signature':goal,'key':['scope_control',case['id']],'status':'decoded','residual':goal,
   'decoded_epoch':0.0,'dim_types':DT,'frame_id':mi}
  if osid is not None:oattrs['scope_id']=osid
  obs=sub.add_node('Observation',oattrs)
  sub.add_edge(agent,'observed',obs)
  specs.append({'frame':mi,'matrix':m,'base':base,'goal':goal,'part':part,'obs':obs,'scope_id':osid,
   'scope_node':scope,'provenance_sha256':digest})
 # Measure checked candidates with the exact scoped Term contract before
 # production closure. These calls do not mutate the graph.
 for spec in specs:
  checked,unchanged=term_checked(sub,spec['goal'],spec['scope_id'],is_scoped)
  checks.append({'frame':spec['frame'],'scope_id':spec['scope_id'],'checked':checked,'state_unchanged':unchanged})
 nodes0=len(list(sub.nodes()));edges0=sub.edge_count();hwm0=rss_kib();cpu0=time.process_time_ns();t0=time.perf_counter_ns()
 work=int(native.run_rules());wall=time.perf_counter_ns()-t0;cpu=time.process_time_ns()-cpu0;hwm1=rss_kib()
 outputs=[];membership=[]
 for s in specs:
  attrs=sub.node(s['obs'])['attrs'];receipts=receipt_data(sub,s['obs']);scope_node=s['scope_node']
  part_scope_id=sub.node(s['part'])['attrs'].get('scope_id');obs_scope_id=sub.node(s['obs'])['attrs'].get('scope_id')
  scope_attrs=sub.node(scope_node)['attrs']
  membership.append({'frame':s['frame'],'scope_node':str(scope_node),
   'scope_id':scope_attrs.get('scope_id'),'part_scope_id_attr':part_scope_id,
   'obs_scope_id_attr':obs_scope_id,'provenance_sha256':scope_attrs.get('provenance_sha256'),
   'members_agree':(s['scope_id'] is None and part_scope_id is None and obs_scope_id is None) or
    (part_scope_id==s['scope_id']==obs_scope_id==scope_attrs.get('scope_id'))})
  outputs.append({'frame':s['frame'],'matrix':s['matrix'],'status':attrs.get('status'),
   'receipts':receipts,'oracle_exact':s['goal']==apply(s['matrix'],s['base']),
   'target_generator_present':any(g['matrix']==s['matrix'] for g in gen_inventory(sub)),
   'quanta_count':len(list(sub.nodes('CapabilityAxis')))})
 return {'pid':os.getpid(),'case':case,'scope_membership':membership,'diagnostic_checks':checks,
  'initial_candidate_checks_total':sum(x['checked'] for x in checks),
  'outputs':outputs,'linear_generators':gen_inventory(sub),'closure_work':work,'closure_wall_ns':wall,
  'closure_cpu_ns':cpu,'hwm_before_kib':hwm0,'hwm_after_kib':hwm1,'hwm_delta_kib':max(0,hwm1-hwm0),
  'nodes_before':nodes0,'nodes_after':len(list(sub.nodes())),'edges_after':sub.edge_count(),
  'source_stable':before==frozen(),'source_before':before,'source_after':frozen()}
def main():
 args=sys.argv[1:]
 if args==['--lock']:
  if LOCK.exists() or OUT.exists():raise SystemExit('refusing to overwrite lock/capture')
  if build_is_stale(str(ROOT)):raise SystemExit('native engine stale')
  LOCK.write_text(json.dumps({'schema':'GenInferExplicitScopeV1_3Lock','sources':frozen(),
   'cases':cases(),'frame_counts':KS,'repeats':REPEATS,'modes':MODES,'maps':MAPS,'B':3,
   'expected_candidates_per_part':2400},indent=2,sort_keys=True)+'\n')
  print(LOCK.relative_to(ROOT));return 0
 if len(args)==2 and args[0]=='--worker':
  lock=json.loads(LOCK.read_text());case=next((c for c in lock['cases'] if c['id']==args[1]),None)
  if case is None:raise SystemExit('unknown case')
  if frozen()!=lock['sources']:raise SystemExit('source/build drift')
  print(json.dumps(execute(case),sort_keys=True));return 0
 if args!=['--run']:raise SystemExit('usage: --lock | --worker ID | --run')
 lock=json.loads(LOCK.read_text())
 if frozen()!=lock['sources']:raise SystemExit('source/build drift from lock')
 env=dict(os.environ);env.setdefault('OZMA_NO_LLM','1');env.setdefault('OZMA_SEED_PERSIST_DISABLED','1')
 env['PYTHONPATH']=str(ROOT/'runners/dsl/python')+os.pathsep+str(ROOT)+os.pathsep+env.get('PYTHONPATH','');rows=[]
 for case in lock['cases']:
  p=subprocess.run([sys.executable,str(RUNNER),'--worker',case['id']],cwd=ROOT,env=env,text=True,capture_output=True,check=True,timeout=300)
  rows.append(json.loads(p.stdout))
 if frozen()!=lock['sources'] or not all(x['source_stable'] for x in rows):raise SystemExit('source drift during capture')
 OUT.write_text(json.dumps({'schema':'GenInferExplicitScopeV1_3Results','captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
  'host':platform.platform(),'lock_sha256':sha(LOCK),'source_manifest':frozen(),'cases':rows},indent=2,sort_keys=True)+'\n')
 print(json.dumps({'output':OUT.relative_to(ROOT).as_posix(),'case_count':len(rows),'source_stable':True},sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())

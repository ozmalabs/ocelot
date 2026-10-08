#!/usr/bin/env python3
"""Measure native GenInfer candidate and timing growth over data-derived B."""
from __future__ import annotations
import hashlib,json,os,platform,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_GENINFER_BOUND_SCALING_PREREG_20260926.md';LOCK=ROOT/'evaluation/substrate_capability/geninfer_bound_scaling_v1_lock_20260926.json';OUT=ROOT/'evaluation/reports/substrate_geninfer_bound_scaling_v1_20260926.json';SEED=ROOT/'seeds/shape_decode_loop.json';SOURCES=('runners/dsl/src/shape_decode.rs','runners/dsl/src/term.rs','substrate/boot_core.py','domains/engine_provenance.py');SCALES=(1,2,3,4);MATRIX=[1,1,0,1];DT=['pred','coord:r','coord:c','val']
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def lock_inputs():
 from substrate_rs import _native
 return {'protocol_sha256':sha(PROTOCOL),'runner_sha256':sha(__file__),'seed_sha256':sha(SEED),'source_sha256':{x:sha(ROOT/x) for x in SOURCES},'native_extension_sha256':sha(Path(_native.__file__).resolve()),'native_build_manifest_sha256':sha(ROOT/'runners/dsl/python/substrate_rs/_native.build.json'),'cargo_lock_sha256':sha(ROOT/'runners/dsl/Cargo.lock'),'commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'dirty_worktree':bool(subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip())}
def shape(s,pred='cell'):
 return [[pred,0,0,'red'],[pred,s,0,'red'],[pred,2*s,0,'red'],[pred,2*s,s,'red']]
def transform(base):
 return [[p,r+c,c,v] for p,r,c,v in base]
def one_call(s,goal):
 from substrate.boot_core import boot_core
 sub,_=boot_core();base=shape(s);sub.add_node('ShapeSignature',{'name':'bound_scale_base','signature':json.dumps(base),'kind':'faculty','faculty':'bound_scale_base','dim_types':DT});native=sub._inner
 t=time.perf_counter_ns();cpu=time.process_time_ns();result=native.evaluate({'type':'GenInfer','goal':{'type':'Lit','value':goal},'max_dims':2},{});cpu_ns=time.process_time_ns()-cpu;wall_ns=time.perf_counter_ns()-t
 return {'result':result,'wall_ns':wall_ns,'cpu_ns':cpu_ns,'base':base,'goal':goal}
def run_scale(s,rep):
 start=lock_inputs();base=shape(s);goal=transform(base);positive=one_call(s,goal);null_goal=[row[:] for row in goal];null_goal[0][0]='noise';null=one_call(s,null_goal);bound=3*s;end=lock_inputs()
 return {'scale':s,'replicate':rep,'expected_bound':bound,'expected_candidates':(2*bound+1)**4-1,'positive':positive,'predicate_null':null,'source_inputs_start':start,'source_inputs_end':end}
def worker(rep):
 before=lock_inputs();return {'replicate':rep,'pid':os.getpid(),'started_inputs':before,'cases':[run_scale(s,rep) for s in SCALES],'finished_inputs':lock_inputs()}
def main():
 if sys.argv[1:]==['--lock']:print(json.dumps({'locked_inputs':lock_inputs()},indent=2,sort_keys=True));return
 if len(sys.argv)==3 and sys.argv[1]=='--worker':print(json.dumps(worker(int(sys.argv[2])),sort_keys=True,default=str));return
 locked=lock_inputs()
 if not LOCK.exists() or json.loads(LOCK.read_text()).get('locked_inputs')!=locked:raise SystemExit('missing or stale lock')
 env=dict(os.environ);env.setdefault('OZMA_NO_LLM','1');env.setdefault('OZMA_SEED_PERSIST_DISABLED','1');env['PYTHONPATH']=str(ROOT/'runners/dsl/python')+os.pathsep+str(ROOT)+os.pathsep+env.get('PYTHONPATH','')
 runs=[json.loads(subprocess.run([sys.executable,str(Path(__file__).resolve()),'--worker',str(i)],cwd=ROOT,env=env,text=True,capture_output=True,check=True,timeout=300).stdout) for i in range(3)];post=lock_inputs();cases=[c for r in runs for c in r['cases']]
 checks={'three_fresh_source_stable_workers':len({r['pid'] for r in runs})==3 and post==locked and all(r['started_inputs']==locked==r['finished_inputs'] for r in runs) and all(c['source_inputs_start']==locked==c['source_inputs_end'] for c in cases),'12_scale_cells':len(cases)==12 and all(sum(c['scale']==s for c in cases)==3 for s in SCALES),'full_results_present':all(isinstance(c[a]['result'],dict) for c in cases for a in ('positive','predicate_null')),'candidate_counts':all(c['expected_bound']==3*c['scale'] and c['expected_candidates']==(2*c['expected_bound']+1)**4-1 and c['positive']['result'].get('checked')==c['expected_candidates'] and c['predicate_null']['result'].get('checked')==c['expected_candidates'] for c in cases),'positive_recovery':all(c['positive']['result'].get('explained') is True and list(c['positive']['result'].get('matrix',()))==MATRIX and c['positive']['result'].get('residual_dims')==0 for c in cases),'predicate_null_refusal':all(c['predicate_null']['result'].get('explained') is False for c in cases),'valid_inputs_and_positive_timings':all(c['positive']['goal']==transform(c['positive']['base']) and all(c[a][t]>0 for a in ('positive','predicate_null') for t in ('wall_ns','cpu_ns')) for c in cases)}
 payload={'schema_version':1,'run_id':'substrate-geninfer-bound-scaling-v1-20260926','claim_boundary':'Direct native GenInfer Term search over one fixed 2-D shear family and one selected predicate-null class; not full-seed acquisition time or general learning complexity.','locked_inputs':locked,'post_run_inputs':post,'lock_sha256':sha(LOCK),'environment':{'python':sys.version,'platform':platform.platform()},'configuration':{'scales':SCALES,'matrix':MATRIX,'candidate_formula':'(2B+1)^4-1, B=3s','replicates':3},'runs':runs,'checks':checks};OUT.write_text(json.dumps(payload,indent=2,sort_keys=True,default=str)+'\n');print(json.dumps({'output':str(OUT),'checks':checks},indent=2))
 if not all(checks.values()):raise SystemExit('measurement gate failed')
if __name__=='__main__':main()

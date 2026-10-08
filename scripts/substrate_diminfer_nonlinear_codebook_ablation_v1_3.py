#!/usr/bin/env python3
"""Full-seed paired evaluation of nonlinear DimInfer primitives/compositions."""
from __future__ import annotations
import hashlib,json,os,platform,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PREREG=ROOT/'docs/research/engine_substrate/SUBSTRATE_DIMINFER_NONLINEAR_CODEBOOK_ABLATION_V1_3_AMENDMENT_20260926.md'
LOCK=ROOT/'evaluation/substrate_capability/diminfer_nonlinear_codebook_ablation_v1_3_lock_20260926.json'
OUT=ROOT/'evaluation/reports/substrate_diminfer_nonlinear_codebook_ablation_v1_3_20260926.json'
FAMILIES={
 'rotation90':['rotation90'], 'reflection_r':['reflection_r'], 'reflection_c':['reflection_c'],
 'scale2':['scale2'], 'cycle4':['cycle4'],
 'rotation90_cycle4':['rotation90','cycle4'],
 'reflection_r_cycle4':['reflection_r','cycle4'],
 'rotation90_scale2':['rotation90','scale2'],
}
GEOMETRIES={
 'asym_a':[(0,0),(1,0),(3,1),(2,3),(0,2),(3,3)],
 'asym_b':[(3,0),(0,1),(2,4),(1,3),(3,2),(0,4)],
 'asym_c':[(1,1),(3,2),(0,4),(2,0),(1,4),(3,0)],
}
REPS=(1,2,3);DT=['pred','coord:r','coord:c','val']
FILES=['scripts/substrate_diminfer_nonlinear_codebook_ablation_v1_3.py','scripts/analyze_substrate_diminfer_nonlinear_codebook_ablation_v1_3.py',
'docs/research/engine_substrate/SUBSTRATE_DIMINFER_NONLINEAR_CODEBOOK_ABLATION_V1_3_AMENDMENT_20260926.md','seeds/shape_decode_loop.json','domains/reflective_faculty.py','domains/engine_provenance.py','substrate/boot_core.py',
'docs/research/engine_substrate/SUBSTRATE_DIMINFER_NONLINEAR_CODEBOOK_ABLATION_PREREG_20260926.md','docs/research/engine_substrate/SUBSTRATE_DIMINFER_NONLINEAR_CODEBOOK_ABLATION_V1_1_AMENDMENT_20260926.md','docs/research/engine_substrate/SUBSTRATE_DIMINFER_NONLINEAR_CODEBOOK_ABLATION_V1_2_AMENDMENT_20260926.md','docs/research/engine_substrate/SUBSTRATE_DIMINFER_NONLINEAR_CODEBOOK_ABLATION_V1_2_1_AMENDMENT_20260926.md','docs/research/engine_substrate/SUBSTRATE_DIMINFER_NONLINEAR_CODEBOOK_ABLATION_V1_3_AMENDMENT_20260926.md','runners/dsl/src/shape_decode.rs','runners/dsl/src/term.rs','runners/dsl/python/substrate_rs/_native.build.json']
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def lock_inputs():
 from substrate_rs import _native
 return {'files_sha256':{f:sha(ROOT/f) for f in FILES},'native_path':str(Path(_native.__file__).resolve()),'native_sha256':sha(Path(_native.__file__).resolve()),'commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()}
def one_step(points,name):
 out=[tuple(p) for p in points]
 if name=='rotation90':
  mr=min(r for r,c in out);mc=min(c for r,c in out);maxr=max(r-mr for r,c in out)
  return [(c-mc,maxr-(r-mr)) for r,c in out]
 if name=='reflection_r':
  mx=max(r for r,c in out);return [(mx-r,c) for r,c in out]
 if name=='reflection_c':
  mx=max(c for r,c in out);return [(r,mx-c) for r,c in out]
 if name=='scale2':
  mr=min(r for r,c in out);mc=min(c for r,c in out);return [(2*(r-mr),2*(c-mc)) for r,c in out]
 if name=='cycle4':return [((r+1)%4,c) for r,c in out]
 raise ValueError(name)
def apply(points,names):
 x=list(points)
 for n in names:x=one_step(x,n)
 return x
def transform_records(s,obs):
 out=[]
 for node in s.neighbours(obs,'has_transform'):
  attrs=s.node(node)['attrs'];out.append({k:attrs.get(k) for k in ('source','generator','generators','k','ks','dim','dims','deltas','transforms','base') if k in attrs})
 return out
def generator_inventory(s):
 out=[]
 for node in s.nodes('DimensionGenerator'):
  a=s.node(node)['attrs'];out.append({'id':str(node),'name':a.get('name'),'kind':a.get('kind'),'coord_dims':a.get('coord_dims'),'modulus':a.get('modulus')})
 return sorted(out,key=lambda x:str(x['name']))
def run_arm(job,ablated):
 from substrate.boot_core import boot_core
 from domains import reflective_faculty as rf
 sub,agent=boot_core();native=rf._native_eval2(sub);rf._ensure_shape_decode_loop(sub,native,agent)
 sub.set_attr(agent,'gen_infer_enabled',0.0)
 before=generator_inventory(sub);removed=[]
 if ablated:
  for node in list(sub.nodes('DimensionGenerator')):
   if sub.node(node)['attrs'].get('name') in job['expected_generators']:
    removed.append(sub.node(node)['attrs'].get('name'));sub.remove_node(node)
 after=generator_inventory(sub)
 pts=GEOMETRIES[job['geometry']];names=job['expected_generators'];goal=apply(pts,names)
 base=[[f'p{i}',r,c,'red'] for i,(r,c) in enumerate(pts)]
 target=[[f'p{i}',r,c,'red'] for i,(r,c) in enumerate(goal)]
 key=f"nonlinear_{job['family']}_{job['geometry']}_{job['replicate']}_{'ablated' if ablated else 'intact'}"
 sub.add_node('ShapeSignature',{'name':key+'_base','signature':json.dumps(base),'kind':'faculty','faculty':key+'_base','dim_types':DT})
 obs=sub.add_node('Observation',{'signature':target,'key':['diminfer_nonlinear',key],'status':'decoded','residual':target,'decoded_epoch':sub.node(agent)['attrs'].get('codebook_epoch') or 0.0,'dim_types':DT})
 sub.add_edge(agent,'observed',obs)
 quanta_before=sorted(str(n) for n in sub.nodes('CapabilityAxis'))
 t=time.perf_counter_ns();native.run_rules();wall=time.perf_counter_ns()-t
 oa=sub.node(obs)['attrs'];quanta=sorted(str(n) for n in sub.nodes('CapabilityAxis'))
 return {'ablated':ablated,'requested_removed':names if ablated else [],'actually_removed':sorted(removed),'generators_before':before,'generators_after':after,
 'gen_infer_enabled':sub.node(agent)['attrs'].get('gen_infer_enabled'),'base':base,'target':target,'status':oa.get('status'),'residual':oa.get('residual'),'covered_by':oa.get('covered_by'),
 'transforms':transform_records(sub,obs),'quanta_count':len(quanta),'quanta_before_count':len(quanta_before),'quanta_delta':len(quanta)-len(quanta_before),'quanta_ids':quanta,'closure_wall_ns':wall,'graph_nodes':len(list(sub.nodes()))}
def worker(family,geometry,rep):
 job={'family':family,'geometry':geometry,'replicate':rep,'expected_generators':FAMILIES[family]}
 start=lock_inputs();intact=run_arm(job,False);ablated=run_arm(job,True);end=lock_inputs()
 return {'pid':os.getpid(),**job,'expected_target':apply(GEOMETRIES[geometry],FAMILIES[family]),'intact':intact,'ablated':ablated,'source_inputs_start':start,'source_inputs_end':end}
def main():
 if len(sys.argv)==2 and sys.argv[1]=='--lock':
  print(json.dumps({'schema_version':1,'locked_inputs':lock_inputs(),'design':{'families':FAMILIES,'geometries':GEOMETRIES,'replicates':list(REPS),'arm_pair':['intact','remove_expected_generator(s)'],'gen_infer_enabled':False}},indent=2,sort_keys=True));return
 if len(sys.argv)==5 and sys.argv[1]=='--worker':
  print(json.dumps(worker(sys.argv[2],sys.argv[3],int(sys.argv[4])),sort_keys=True,default=str));return
 lock=json.loads(LOCK.read_text());locked=lock_inputs()
 if lock.get('locked_inputs')!=locked:raise SystemExit('stale or missing lock')
 env=dict(os.environ);env['PYTHONPATH']=f"{ROOT}:{ROOT/'runners/dsl/python'}:{env.get('PYTHONPATH','')}";env.setdefault('OZMA_NO_LLM','1');env.setdefault('OZMA_SEED_PERSIST_DISABLED','1')
 jobs=[(f,g,r) for f in FAMILIES for g in GEOMETRIES for r in REPS];rows=[];started=time.perf_counter()
 for f,g,r in jobs:
  proc=subprocess.run([sys.executable,str(Path(__file__).resolve()),'--worker',f,g,str(r)],cwd=ROOT,env=env,text=True,capture_output=True,timeout=120)
  if proc.returncode:row={'family':f,'geometry':g,'replicate':r,'worker_failure':proc.stderr[-4000:]}
  else:row=json.loads(proc.stdout)
  rows.append(row);print(f"{len(rows)}/{len(jobs)} {f} {g} r{r} pid={row.get('pid')} intact={row.get('intact',{}).get('status',row.get('worker_failure'))} ablated={row.get('ablated',{}).get('status','')}",flush=True)
 raw={'protocol':'SUBSTRATE_DIMINFER_NONLINEAR_CODEBOOK_ABLATION_V1_3','locked_inputs':locked,'lock_sha256':sha(LOCK),'environment':{'python':sys.version,'platform':platform.platform()},'workers':rows,'worker_count':len(rows),'worker_failures':[x for x in rows if 'worker_failure' in x],'parent_elapsed_seconds':time.perf_counter()-started,'claim_boundary':'full-seed application of selected held 2-D primitive/composition generators under matched codebook ablation; GenInfer disabled; no nonlinear induction claim'}
 OUT.write_text(json.dumps(raw,indent=2,sort_keys=True,default=str)+'\n');print(json.dumps({'output':str(OUT),'workers':len(rows),'failures':len(raw['worker_failures']),'elapsed_seconds':raw['parent_elapsed_seconds']},indent=2))
if __name__=='__main__':main()

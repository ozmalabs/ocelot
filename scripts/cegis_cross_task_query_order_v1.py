#!/usr/bin/env python3
"""Cross-task CEGIS order sensitivity with label-independent native literals."""
from __future__ import annotations
import argparse,hashlib,json,os,platform,random,statistics,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
os.environ.setdefault('OZMA_NO_LLM','1'); os.environ.setdefault('OZMA_SEED_PERSIST_DISABLED','1')
sys.path[:0]=[str(ROOT),str(ROOT/'scripts'),str(ROOT/'runners/dsl/python')]
from domains.engine_provenance import engine_preamble,engine_provenance,rust_source_fingerprint
engine_preamble()
from substrate_rs import _native
import domains.cegis_faculty as faculty
from domains.cegis_faculty import cegis_synthesize
from domains.generator import synthesize as native_synthesize
import cegis_faculty_on_sum_of_n as tri
import cegis_faculty_on_variance as var
STEM='cegis_cross_task_query_order_v1_20260930'; LOCK=ROOT/f'evaluation/substrate_capability/{STEM}_lock.json'; RAW=ROOT/f'evaluation/reports/{STEM}_raw.json'
PROTOCOL=ROOT/'docs/research/engine_substrate/CEGIS_CROSS_TASK_QUERY_ORDER_V1_PREREG_20260930.md'
REPS,SEED=5,20260930
SOURCES=['scripts/cegis_cross_task_query_order_v1.py','scripts/analyze_cegis_cross_task_query_order_v1.py','scripts/cegis_faculty_on_sum_of_n.py','scripts/cegis_faculty_on_variance.py','domains/cegis_faculty.py','domains/generator.py','domains/compute_grounding.py','domains/reason.py','domains/engine_provenance.py','docs/research/engine_substrate/CEGIS_CROSS_TASK_QUERY_ORDER_V1_PREREG_20260930.md']
class TargetLabel:
    """Numeric synthesis target that deliberately cannot seed a grammar literal."""
    def __init__(self,value): self.value=float(value)
    def __float__(self): return self.value
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def lock_payload():
    ext=Path(_native.__file__).resolve()
    return {'schema_version':1,'source_sha256':{p:sha(ROOT/p) for p in SOURCES},'native_extension':{'path':str(ext),'sha256':sha(ext)},'native_build_manifest_sha256':sha(ROOT/'runners/dsl/python/substrate_rs/_native.build.json'),'engine_provenance':engine_provenance(),'rust_source_fingerprint':rust_source_fingerprint(str(ROOT)),'commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'design':{'tasks':['triangular_number','population_variance'],'arms':['fixed_order','seeded_permutation'],'repetitions_per_cell':REPS,'schedule_seed':SEED,'base_literal_set':[-1,0,1,2],'label_wrapper':'float-convertible non-int/float object prevents output-derived literal insertion','max_size':9,'timeout_s':60,'max_rounds':12,'process_timeout_s':240}}
def setup(task,s):
    if task=='triangular_number': return tri.describe,tri.make_oracle(s),tri.family,tri.KNOWNS,tri.OPS,[(f'n={n}',n) for n in (17,23,50,99,100,250)]
    if task=='population_variance':
        sum_fn,sq_fn=var.make_descriptor_fns(s); describe=var.make_describe(sum_fn,sq_fn)
        return describe,var.make_oracle(s),var.family,var.KNOWNS,var.OPS,[('H0',[5,5,5,5,5]),('H1',[1,100]),('H2',[3,1,4,1,5,9,2,6]),('H3',[12,7,19,3,25,8]),('H4',[0,0,0,0,1])]
    raise ValueError(task)
def worker(task,arm,rep):
    s=_native.Substrate(); describe,oracle0,family_fn,knowns,ops,held_inputs=setup(task,s); oracle_calls=[]
    def oracle(inp): oracle_calls.append(inp); return oracle0(inp)
    native_calls=[]
    def no_output_literals(sub,examples,*args,**kwargs):
        wrapped=[(env,TargetLabel(out)) for env,out in examples]
        result=native_synthesize(sub,wrapped,*args,**kwargs)
        native_calls.append({'explored':result.get('explored'),'elapsed_s':result.get('elapsed_s'),'fits':result.get('fits'),'halt_reason':result.get('halt_reason')})
        return result
    faculty.synthesize=no_output_literals
    candidates=list(family_fn())
    if arm=='seeded_permutation': random.Random(SEED+rep+(1000 if task=='population_variance' else 0)).shuffle(candidates)
    elif arm!='fixed_order': raise ValueError(arm)
    candidate_order=[name for name,_ in candidates]
    t0=time.perf_counter(); c0=time.process_time()
    result=cegis_synthesize(s,describe,oracle,lambda:list(candidates),knowns,ops=ops,max_size=9,timeout_s=60,max_rounds=12)
    wall=time.perf_counter()-t0; cpu=time.process_time()-c0
    held=[]
    for name,inp in held_inputs:
        predicted=result.evaluate(describe,inp,s) if result.final_term is not None else None
        expected=oracle0(inp)
        held.append({'name':name,'input':inp,'predicted':predicted,'expected':expected,'exact':predicted is not None and abs(float(predicted)-float(expected))<1e-6})
    queries=[r.counterexample for r in result.rounds if r.counterexample is not None]
    return {'task':task,'arm':arm,'replicate':rep,'pid':os.getpid(),'candidate_order':candidate_order,'selected_queries':queries,'oracle_calls':oracle_calls,'native_calls':native_calls,'result':{'step0_term':result.step0_term_str,'final_term':result.final_term_str,'final_size':result.final_size,'fits':result.fits,'converged':result.converged,'rows':[n for n,_ in result.rows],'rounds':[{'round':r.rnd,'term':r.term_str,'counterexample':r.counterexample} for r in result.rounds]},'heldout':held,'wall_s':wall,'cpu_s':cpu,'literal_policy':'base literals only; outputs wrapped as TargetLabel'}
def main():
    p=argparse.ArgumentParser();p.add_argument('--lock',action='store_true');p.add_argument('--worker',nargs=3);a=p.parse_args()
    if a.worker: print(json.dumps(worker(a.worker[0],a.worker[1],int(a.worker[2])),sort_keys=True,default=str));return
    lock=lock_payload()
    if a.lock: print(json.dumps(lock,indent=2,sort_keys=True));return
    if not LOCK.exists() or json.loads(LOCK.read_text())!=lock: raise SystemExit('missing or stale source/task lock')
    if RAW.exists(): raise SystemExit(f'refusing to overwrite {RAW}')
    sched=[(task,arm,r) for task in ('triangular_number','population_variance') for r in range(1,REPS+1) for arm in ('fixed_order','seeded_permutation')];random.Random(SEED).shuffle(sched)
    env=dict(os.environ);env['PYTHONPATH']=f"{ROOT}:{ROOT/'scripts'}:{ROOT/'runners/dsl/python'}:{env.get('PYTHONPATH','')}"
    rows=[];start=time.perf_counter()
    for i,(task,arm,rep) in enumerate(sched,1):
        try: proc=subprocess.run([sys.executable,str(Path(__file__).resolve()),'--worker',task,arm,str(rep)],cwd=ROOT,env=env,text=True,capture_output=True,timeout=240)
        except subprocess.TimeoutExpired as e: row={'task':task,'arm':arm,'replicate':rep,'worker_error':'240-second process timeout'}
        else:
            if proc.returncode: row={'task':task,'arm':arm,'replicate':rep,'worker_error':proc.stderr[-4000:]}
            else:
                try: row=json.loads(proc.stdout.strip().splitlines()[-1]);row['worker_error']=None
                except Exception as e: row={'task':task,'arm':arm,'replicate':rep,'worker_error':f'parse: {type(e).__name__}: {e}'}
        rows.append(row);print(f'{i}/20 {task} {arm} rep={rep} error={row.get("worker_error")}',flush=True)
    raw={'protocol':STEM,'lock':lock,'schedule':[list(x) for x in sched],'workers':rows,'worker_failures':[x for x in rows if x.get('worker_error')],'elapsed_s':time.perf_counter()-start,'environment':{'python':sys.version,'platform':platform.platform()}}
    RAW.write_text(json.dumps(raw,indent=2,sort_keys=True,default=str)+'\n');print(json.dumps({'raw':str(RAW),'workers':len(rows),'failures':len(raw['worker_failures']),'elapsed_s':raw['elapsed_s']}))
if __name__=='__main__':main()

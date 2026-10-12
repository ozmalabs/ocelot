#!/usr/bin/env python3
"""Measure label-blind query ranking over explicit finite hypothesis pools."""
from __future__ import annotations
import argparse,hashlib,json,os,platform,random,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
os.environ.setdefault('OZMA_NO_LLM','1');os.environ.setdefault('OZMA_SEED_PERSIST_DISABLED','1')
sys.path[:0]=[str(ROOT),str(ROOT/'scripts'),str(ROOT/'runners/dsl/python')]
from domains.engine_provenance import engine_preamble,engine_provenance,rust_source_fingerprint
engine_preamble()
from substrate_rs import _native,Var,Lit,Plus,Times,Minus,Div
from domains.query_selection import rank_queries_by_disagreement
import cegis_faculty_on_sum_of_n as tri
import cegis_faculty_on_variance as variance
import jabberwock_closes_the_euler_tie as euler
STEM='substrate_label_blind_query_ranking_v1_20260930';LOCK=ROOT/f'evaluation/substrate_capability/{STEM}_lock.json';RAW=ROOT/f'evaluation/reports/{STEM}_raw.json'
PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_LABEL_BLIND_QUERY_RANKING_V1_PREREG_20260930.md'
REPS,SEED=10,20260930;POLICIES=('fixed_first','seeded_random','entropy_ranked','oracle_best');TASKS=('triangular_number','population_variance','euler_characteristic')
SOURCES=['domains/query_selection.py','scripts/substrate_label_blind_query_ranking_v1.py','scripts/analyze_substrate_label_blind_query_ranking_v1.py','scripts/cegis_faculty_on_sum_of_n.py','scripts/cegis_faculty_on_variance.py','scripts/jabberwock_closes_the_euler_tie.py','domains/cegis_faculty.py','domains/generator.py','domains/compute_grounding.py','domains/reason.py','domains/engine_provenance.py','docs/research/engine_substrate/SUBSTRATE_LABEL_BLIND_QUERY_RANKING_V1_PREREG_20260930.md']
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def lock_payload():
 ext=Path(_native.__file__).resolve()
 return {'schema_version':1,'source_sha256':{p:sha(ROOT/p) for p in SOURCES},'native_extension':{'path':str(ext),'sha256':sha(ext)},'native_build_manifest_sha256':sha(ROOT/'runners/dsl/python/substrate_rs/_native.build.json'),'engine_provenance':engine_provenance(),'rust_source_fingerprint':rust_source_fingerprint(str(ROOT)),'commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'design':{'tasks':list(TASKS),'policies':list(POLICIES),'repetitions_per_cell':REPS,'schedule_seed':SEED,'hypotheses_per_task':4,'entropy':'Shannon predictive entropy, equal hypothesis weights; ties by distinct prediction count then family order','max_worker_seconds':60}}
def build_task(task,s):
 n=Var('n');one=Lit(1)
 if task=='triangular_number':
  describe=tri.describe; oracle=lambda x:x*(x+1)//2; candidates=tri.family();known=[('n=1',1,1)]
  hypotheses=[('identity',n),('constant_one',one),('square',Times([n,n])),('triangular',Times([n,Div(Plus([n,Lit(1)]),Lit(2))]))];truth='triangular'
 elif task=='population_variance':
  sf,sqf=variance.make_descriptor_fns(s);describe=variance.make_describe(sf,sqf);oracle=variance.make_oracle(s);candidates=variance.family();known=[('K0',[2,4],1.0)];su=Var('sum');sq=Var('sum_sq');cnt=Var('n')
  hypotheses=[('constant_one',one),('mean_minus_two',Minus(Div(su,cnt),Lit(2))),('count_minus_one',Minus(cnt,Lit(1))),('variance',Div(Minus(sq,Div(Times([su,su]),cnt)),cnt))];truth='variance'
 elif task=='euler_characteristic':
  describe=euler.describe;oracle=euler._make_labeller(s);candidates=euler._family();known=[(name,mf,1) for name,mf in euler.KNOWN_COMPLEXES];v=Var('V');ec=Var('E');f=Var('F');cells=Var('ncells')
  euler_term=Plus([Minus(v,ec),f]);simplex_null=Times([Minus(v,Lit(1)),Minus(v,Lit(2)),Minus(v,Lit(3))])
  hypotheses=[('constant_one',one),('maximal_cell_count',cells),('euler',euler_term),('euler_plus_simplex_null',Plus([euler_term,simplex_null]))];truth='euler'
 else:raise ValueError(task)
 return describe,oracle,list(candidates),known,hypotheses,truth
def worker(task,policy,rep):
 s=_native.Substrate();describe,oracle,candidates,known,hypotheses,truth=build_task(task,s);terms=[t for _,t in hypotheses]
 known_fit=[]
 for name,inp,label in known:
  known_fit.append({'name':name,'label':label,'predictions':[t.evaluate(describe(inp),s) for t in terms]})
 if not all(all(abs(float(p)-float(k['label']))<1e-6 for p in k['predictions']) for k in known_fit):raise RuntimeError('hypothesis set does not fit registered known rows')
 t0=time.perf_counter();cpu0=time.process_time();ranked=[]
 if policy=='entropy_ranked':ranked=rank_queries_by_disagreement(s,terms,describe,candidates)
 rank_wall=time.perf_counter()-t0;rank_cpu=time.process_time()-cpu0
 response=[];oracle_best_candidates=[]
 if policy=='entropy_ranked':chosen=ranked[0]['name'];
 elif policy=='fixed_first':chosen=candidates[0][0]
 elif policy=='seeded_random':chosen=random.Random(SEED+rep+TASKS.index(task)*10000).choice(candidates)[0]
 elif policy=='oracle_best':
  best=None
  for name,inp in candidates:
   label=oracle(inp);response.append({'name':name,'input':inp,'label':label});preds=[h.evaluate(describe(inp),s) for h in terms];survivors=[hypotheses[i][0] for i,p in enumerate(preds) if abs(float(p)-float(label))<1e-6];oracle_best_candidates.append({'name':name,'label':label,'predictions':preds,'survivors':survivors})
   candidate=(len(survivors),candidates.index((name,inp)),name)
   if best is None or candidate<best:best=candidate
  chosen=best[2]
 else:raise ValueError(policy)
 chosen_item=next((n,x) for n,x in candidates if n==chosen)
 if policy!='oracle_best':response=[{'name':chosen,'input':chosen_item[1],'label':oracle(chosen_item[1])}]
 answer=response[0]['label'] if policy!='oracle_best' else next(x['label'] for x in response if x['name']==chosen)
 preds=[h.evaluate(describe(chosen_item[1]),s) for h in terms]
 survivors=[hypotheses[i][0] for i,p in enumerate(preds) if abs(float(p)-float(answer))<1e-6]
 return {'task':task,'policy':policy,'replicate':rep,'pid':os.getpid(),'candidate_order':[n for n,_ in candidates],'known_fit':known_fit,'hypothesis_ids':[n for n,_ in hypotheses],'true_hypothesis':truth,'ranked':ranked,'oracle_best_candidates':oracle_best_candidates,'selected_query':chosen,'oracle_responses':response,'selected_predictions':preds,'survivors':survivors,'true_survives':truth in survivors,'unique_true':survivors==[truth],'selector_evaluations':len(candidates)*len(hypotheses) if policy=='entropy_ranked' else 0,'rank_wall_s':rank_wall,'rank_cpu_s':rank_cpu,'wall_s':time.perf_counter()-t0,'cpu_s':time.process_time()-cpu0}
def main():
 p=argparse.ArgumentParser();p.add_argument('--lock',action='store_true');p.add_argument('--worker',nargs=3);a=p.parse_args()
 if a.worker:print(json.dumps(worker(a.worker[0],a.worker[1],int(a.worker[2])),sort_keys=True,default=str));return
 lock=lock_payload()
 if a.lock:print(json.dumps(lock,indent=2,sort_keys=True));return
 if not LOCK.exists() or json.loads(LOCK.read_text())!=lock:raise SystemExit('missing/stale source/task lock')
 if RAW.exists():raise SystemExit(f'refusing to overwrite {RAW}')
 sched=[(task,pol,r) for task in TASKS for r in range(1,REPS+1) for pol in POLICIES];random.Random(SEED).shuffle(sched);env=dict(os.environ);env['PYTHONPATH']=f"{ROOT}:{ROOT/'scripts'}:{ROOT/'runners/dsl/python'}:{env.get('PYTHONPATH','')}";rows=[];start=time.perf_counter()
 for i,(task,pol,rep) in enumerate(sched,1):
  try:q=subprocess.run([sys.executable,str(Path(__file__).resolve()),'--worker',task,pol,str(rep)],cwd=ROOT,env=env,text=True,capture_output=True,timeout=60)
  except subprocess.TimeoutExpired:row={'task':task,'policy':pol,'replicate':rep,'worker_error':'60-second worker timeout'}
  else:
   if q.returncode:row={'task':task,'policy':pol,'replicate':rep,'worker_error':q.stderr[-3000:]}
   else:
    try:row=json.loads(q.stdout.strip().splitlines()[-1]);row['worker_error']=None
    except Exception as e:row={'task':task,'policy':pol,'replicate':rep,'worker_error':f'parse:{type(e).__name__}:{e}'}
  rows.append(row);print(f'{i}/120 {task} {pol} r={rep} error={row.get("worker_error")}',flush=True)
 raw={'protocol':STEM,'lock':lock,'schedule':[list(x) for x in sched],'workers':rows,'worker_failures':[x for x in rows if x.get('worker_error')],'elapsed_s':time.perf_counter()-start,'environment':{'python':sys.version,'platform':platform.platform()}};RAW.write_text(json.dumps(raw,indent=2,sort_keys=True,default=str)+'\n');print(json.dumps({'raw':str(RAW),'workers':len(rows),'failures':len(raw['worker_failures']),'elapsed_s':raw['elapsed_s']}))
if __name__=='__main__':main()

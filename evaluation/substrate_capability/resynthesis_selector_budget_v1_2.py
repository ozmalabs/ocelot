#!/usr/bin/env python3
"""Continue native active selection on fixed residual-resynthesis pools."""
import hashlib,json,os,platform,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'runners/dsl/python'),str(ROOT),str(ROOT/'evaluation/substrate_capability')]
RUN=Path(__file__).resolve();PRE=ROOT/'docs/research/engine_substrate/RESYNTHESIS_SELECTOR_BUDGET_V1_PREREG_20261004.md';AMEND=ROOT/'docs/research/engine_substrate/RESYNTHESIS_SELECTOR_BUDGET_V1_2_AMENDMENT_20261004.md';AN=ROOT/'evaluation/substrate_capability/analyze_resynthesis_selector_budget_v1_2.py'
SR=ROOT/'evaluation/substrate_capability/residual_triggered_resynthesis_v1_2.py';SL=ROOT/'evaluation/substrate_capability/residual_triggered_resynthesis_v1_2_lock_20261004.json';SRAW=ROOT/'evaluation/reports/residual_triggered_resynthesis_v1_2_20261004.json';SA=ROOT/'evaluation/substrate_capability/analyze_residual_triggered_resynthesis_v1_2.py';SOUT=ROOT/'evaluation/reports/residual_triggered_resynthesis_v1_2_analysis_20261004.json'
LOCK=ROOT/'evaluation/substrate_capability/resynthesis_selector_budget_v1_2_lock_20261004.json';OUT=ROOT/'evaluation/reports/resynthesis_selector_budget_v1_2_20261004.json';CAPS=(8,16,32,'all')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def source_map():
 from substrate_rs import _native
 from domains.engine_provenance import build_is_stale,rust_source_fingerprint
 if build_is_stale(str(ROOT)):raise RuntimeError('stale native build')
 ps=[RUN,PRE,AMEND,AN,SR,SL,SRAW,SA,SOUT,ROOT/'domains/contract_query.py']
 b=Path(_native.__file__).resolve()
 return {'files':{str(p.relative_to(ROOT)):sha(p) for p in ps},'native':{'path':str(b),'sha256':sha(b)},'rust_fingerprint':rust_source_fingerprint(str(ROOT)),'python':sys.version,'platform':platform.platform()}
def inputs():
 l=json.loads(SL.read_text());r=json.loads(SRAW.read_text());return l['panels'],r['workers']
def worker(i):
 from substrate_rs import _native
 from domains.contract_query import select_discriminating_input
 import residual_triggered_resynthesis_v1_2 as s
 from adaptive_factored_operator_search_v1 import classify,truth
 panels,raw=inputs();p=panels[i];w=raw[i]
 if not w.get('triggered'):return {'task':p['task'],'worker':p['worker'],'triggered':False,'arms':{}}
 n=_native.Substrate(); pool=[dict(zip(s.KEYS,map(float,x))) for x in p['selection_order']];out={}
 for name in ('no_residual_control','residual_arm'):
  arm=w[name];cands=arm['candidate_terms']; survivors=cands.copy();events=[];used=set();prior=arm['selection_labels']
  for e in prior:
   row=e['row'];q=dict(zip(s.KEYS,row));survivors=[h for h in survivors if classify(n.evaluate(h['term'],q)) is bool(e['label'])];used.add(tuple(row));events.append(dict(e))
  checkpoints={}
  for cap in CAPS:
   if cap=='all':target=len(pool)
   else:target=cap
   while len(events)<target and len(survivors)>1:
    avail=[e for e in pool if tuple(float(e[k]) for k in s.KEYS) not in used]
    if not avail:break
    ans=select_discriminating_input(lambda term,e:classify(n.evaluate(term,e)),survivors,avail,[])
    if not ans.get('ok'):break
    q=ans['query'];row=[float(q[k]) for k in s.KEYS];label=bool(truth(p['task'],row));before=[h['id'] for h in survivors]
    survivors=[h for h in survivors if classify(n.evaluate(h['term'],q)) is label];used.add(tuple(row));events.append({'row':row,'label':label,'before':len(before),'after':len(survivors),'selector_entropy_bits':ans.get('entropy_bits')})
   checkpoints[str(cap)]={'cumulative_labels':len(events),'candidate_count':len(survivors),'decision':'accept' if len(survivors)==1 else 'request_help','survivor_ids':[h['id'] for h in survivors]}
  out[name]={'prior_labels':prior,'extension_events':events[len(prior):],'all_events':events,'checkpoints':checkpoints,'pool_size':len(pool),'candidate_terms':cands}
 return {'task':p['task'],'worker':p['worker'],'triggered':w['triggered'],'arms':out}
def main():
 a=sys.argv[1:]
 if a==['--lock']:
  if LOCK.exists() or OUT.exists():raise SystemExit('refusing overwrite')
  if not json.loads(SOUT.read_text()).get('passed'):raise SystemExit('v1.2 upstream analysis must pass')
  ps,_=inputs();LOCK.write_text(json.dumps({'schema':'ResynthesisSelectorBudgetV1_2Lock','sources':source_map(),'upstream_lock_sha256':sha(SL),'upstream_capture_sha256':sha(SRAW),'panels':ps,'caps':CAPS},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return 0
 if a==['--run']:
  l=json.loads(LOCK.read_text());ps,raw=inputs()
  if source_map()!=l['sources'] or ps!=l['panels'] or sha(SRAW)!=l['upstream_capture_sha256']:raise SystemExit('source/input drift')
  rows=[]
  for i,p in enumerate(ps):
   cp=subprocess.run([sys.executable,str(RUN),'--worker',str(i)],cwd=ROOT,env={**os.environ,'PYTHONPATH':f'{ROOT}/runners/dsl/python:{ROOT}:{ROOT}/evaluation/substrate_capability'},text=True,capture_output=True,timeout=60)
   if cp.returncode:raise RuntimeError(cp.stderr[-1500:])
   rows.append(json.loads(cp.stdout.strip().splitlines()[-1]))
  if source_map()!=l['sources']:raise SystemExit('source drift during run')
  OUT.write_text(json.dumps({'schema':'ResynthesisSelectorBudgetV1_2Results','lock_sha256':sha(LOCK),'sources':source_map(),'workers':rows,'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())},indent=2,sort_keys=True)+'\n');print(OUT.relative_to(ROOT));return 0
 if len(a)==2 and a[0]=='--worker':print(json.dumps(worker(int(a[1])),sort_keys=True,separators=(',',':')));return 0
 raise SystemExit('usage --lock | --run | --worker I')
if __name__=='__main__':raise SystemExit(main())

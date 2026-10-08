#!/usr/bin/env python3
"""Locked bounded test of native-Term active probe selection."""
from __future__ import annotations
import hashlib, json, os, platform, random, subprocess, sys, time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python')]
RUNNER=Path(__file__).resolve()
ANALYZER=ROOT/'evaluation/substrate_capability/analyze_thoughtexperiment_active_probe_selection_v1.py'
PROTOCOL=ROOT/'docs/research/engine_substrate/THOUGHTEXPERIMENT_ACTIVE_PROBE_SELECTION_V1_PREREG_20261002.md'
LOCK=ROOT/'evaluation/substrate_capability/thoughtexperiment_active_probe_selection_v1_lock_20261002.json'
RAW=ROOT/'evaluation/reports/thoughtexperiment_active_probe_selection_v1_raw_20261002.json'
WORKERS=4; POOL=100; ALIAS_RATES=(0,50,90,99); HOLDOUT=20; SEED=68291
TERMS=[{'type':'Var','name':'key'},{'type':'Var','name':'signature'}]
ACTIVE=(ROOT/'domains/contract_query.py',ROOT/'substrate/boot_core.py',
        ROOT/'runners/dsl/src/term.rs',ROOT/'runners/dsl/src/py.rs',
        ROOT/'runners/dsl/python/substrate_rs/__init__.py')

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def active():
 from substrate_rs import _native
 return {str(p.relative_to(ROOT)):sha(p) for p in (RUNNER,ANALYZER,PROTOCOL,*ACTIVE)} | {'native':sha(Path(_native.__file__).resolve())}
def build(worker,rate):
 rows=[]; n_alias=round(POOL*rate/100)
 for i in range(POOL):
  key=f'w{worker}_r{rate}_k{i}'
  sig=key if i<n_alias else f'w{worker}_r{rate}_s{i}'
  rows.append({'key':[key],'signature':[sig]})
 return rows
def worker(w):
 from substrate.boot_core import boot_core
 from domains.contract_query import select_discriminating_input
 sub,_=boot_core(); native=sub._inner
 before=active(); out=[]
 hypotheses=[{'id':'key','term':TERMS[0]},{'id':'signature','term':TERMS[1]}]
 for rate in ALIAS_RATES:
  pool=build(w,rate)
  def evaluate(term,env): return native.evaluate(term,env)
  start=time.perf_counter_ns(); cpu=time.process_time_ns()
  choice=select_discriminating_input(evaluate,hypotheses,pool)
  wall=time.perf_counter_ns()-start; cpu_ns=time.process_time_ns()-cpu
  rng=random.Random(SEED+w*1000+rate)
  random_probe=pool[rng.randrange(len(pool))]
  # Freeze query choice before computing either oracle label.
  query=choice.get('query') if choice.get('ok') else None
  oracle=lambda x:x['key']
  selected_label=oracle(query) if query else None
  predictions={h['id']:native.evaluate(h['term'],query) for h in hypotheses} if query else {}
  survivor=[hid for hid,value in predictions.items() if type(value) is type(selected_label) and value==selected_label]
  holdout=[]
  for j in range(HOLDOUT):
   key=f'w{w}_r{rate}_held_k{j}'; env={'key':[key],'signature':[key+'_other']}
   holdout.append({'env':env,'expected':oracle(env)})
  holdout_accuracy=all(native.evaluate(TERMS[0],r['env'])==r['expected'] for r in holdout) if survivor==['key'] else False
  out.append({'alias_rate_percent':rate,'pool_size':len(pool),'actual_discriminator_count':sum(x['key']!=x['signature'] for x in pool),
   'choice':choice,'selected_oracle_label':selected_label,'survivors':survivor,'heldout_count':len(holdout),
   'heldout_accuracy':holdout_accuracy,'random_probe_discriminates':random_probe['key']!=random_probe['signature'],
   'selector_wall_ns':wall,'selector_cpu_ns':cpu_ns})
 after=active()
 if before!=after: raise RuntimeError('source drift during worker')
 return {'worker':w,'source_before':before,'source_after':after,'source_stable':before==after,'conditions':out}
def main():
 from domains.engine_provenance import build_is_stale
 stale=build_is_stale(str(ROOT))
 if stale: raise SystemExit('stale native engine: '+'; '.join(stale))
 if sys.argv[1:]==['--lock']:
  if LOCK.exists() or RAW.exists(): raise SystemExit('refusing to overwrite capture')
  LOCK.write_text(json.dumps({'schema':'ThoughtexperimentActiveProbeSelectionV1Lock','sources':active(),'workers':WORKERS,'pool_size':POOL,'alias_rates_percent':ALIAS_RATES,'heldout':HOLDOUT,'seed':SEED},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return
 if sys.argv[1:]==['--capture']:
  if not LOCK.exists() or RAW.exists(): raise SystemExit('missing lock or capture already exists')
  lock=json.loads(LOCK.read_text())
  if active()!=lock['sources']: raise SystemExit('source drift from lock')
  workers=[worker(i) for i in range(WORKERS)]
  if active()!=lock['sources']: raise SystemExit('source drift during capture')
  doc={'schema':'ThoughtexperimentActiveProbeSelectionV1Capture','captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'host':{'platform':platform.platform(),'machine':platform.machine(),'python':sys.version.split()[0]},'lock_sha256':sha(LOCK),'workers':workers}
  RAW.write_text(json.dumps(doc,indent=2,sort_keys=True)+'\n');print(json.dumps({'workers':len(workers),'conditions':len(workers)*len(ALIAS_RATES),'raw':RAW.relative_to(ROOT).as_posix()}));return
 raise SystemExit('choose --lock or --capture')
if __name__=='__main__': main()

#!/usr/bin/env python3
"""Held-out effect-index localization from native rule event reports."""
from __future__ import annotations
import hashlib,json,os,platform,random,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python')]
RUNNER=Path(__file__).resolve();ANALYZER=ROOT/'evaluation/substrate_capability/analyze_thoughtexperiment_effect_trace_diagnosis_v1.py'
PROTOCOL=ROOT/'docs/research/engine_substrate/THOUGHTEXPERIMENT_EFFECT_TRACE_DIAGNOSIS_V1_PREREG_20261005.md'
LOCK=ROOT/'evaluation/substrate_capability/thoughtexperiment_effect_trace_diagnosis_v1_lock_20261005.json'
OUT=ROOT/'evaluation/reports/thoughtexperiment_effect_trace_diagnosis_v1_20261005.json'
SOURCES=('runners/dsl/Cargo.toml','runners/dsl/Cargo.lock','runners/dsl/src/graph.rs','runners/dsl/src/rewrite.rs','runners/dsl/src/substrate.rs','runners/dsl/src/py.rs','runners/dsl/python/substrate_rs/ext.py','runners/dsl/python/substrate_rs/__init__.py','runners/dsl/python/substrate_rs/_native.build.json')
CASES_PER_SIZE=20;SIZES=(4,8,16,32)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def frozen():
 from substrate_rs import _native
 files=(RUNNER,ANALYZER,PROTOCOL,*(ROOT/x for x in SOURCES));binary=Path(_native.__file__).resolve()
 return {'files':{str(p.relative_to(ROOT)):sha(p) for p in files},'native_binary':{'path':str(binary),'sha256':sha(binary)}}
def make_case(size,case_id):
 from substrate_rs import Substrate
 rng=random.Random(0xE771000+case_id*7919+size*104729);s=Substrate();anchor=s.add_node('Anchor',{})
 node_order=list(range(size));rng.shuffle(node_order);nodes={i:s.add_node('Target',{'health':0,'slot':i}) for i in node_order}
 vars_=[f'v{i}' for i in range(size)];slot_order=list(range(size));rng.shuffle(slot_order)
 for i in range(size):s.add_edge_unchecked(anchor,f'slot_{i}',nodes[i])
 clause_order=list(range(size));rng.shuffle(clause_order)
 match=[['anchor',f'slot_{i}',vars_[i]] for i in clause_order]
 effect_order=list(range(size));rng.shuffle(effect_order);bad_var=rng.randrange(size);bad_effect_index=effect_order.index(bad_var)
 effects=[['set_attr',vars_[i],'health',999 if i==bad_var else 1] for i in effect_order]
 s._inner.add_rule({'name':'calibration_sweep','match':match,'effects':effects})
 return s,{'case_id':case_id,'size':size,'bad_variable':vars_[bad_var],'bad_node_id':nodes[bad_var].value,'bad_effect_index':bad_effect_index,'effect_variables':[vars_[i] for i in effect_order],'variable_node_ids':{vars_[i]:nodes[i].value for i in range(size)}}
def observe(size,case_id,mode):
 s,oracle=make_case(size,case_id);method={'events':'run_rules_delta_report','effects':'run_rules_effect_delta_report'}[mode]
 report=getattr(s._inner,method)(1,False);events=[e for e in report['rule_write_events'] if e['rule_name']=='calibration_sweep' and e['progressed']]
 if len(events)!=1:raise RuntimeError(f'expected one progressed rule event, got {len(events)}')
 event=events[0];effect_candidates=[]
 for effect in event.get('effect_snapshots',[]):
  if any(int(v['node_id'])==oracle['bad_node_id'] and v['after'] is not None and v['after']['attrs'].get('health')==999 for v in effect.get('node_values',[])):
   effect_candidates.append(effect['effect_index'])
 return {'oracle':oracle,'mode':mode,'progress':{'status':report['status'],'steps':report['progress_steps']},'event_node_ids':event['node_ids'],'event_value_count':len(event['node_values']),'effect_snapshots':event.get('effect_snapshots',[]),'effect_candidates':effect_candidates}
def worker(index):
 locked=json.loads(LOCK.read_text())['sources'];before=frozen()
 if before!=locked:raise RuntimeError('source lock mismatch before worker')
 rows=[]
 for size in SIZES:
  for case_id in range(CASES_PER_SIZE):
   events=observe(size,case_id,'events');effects=observe(size,case_id,'effects')
   if events['oracle']!=effects['oracle']:raise RuntimeError('paired case oracle mismatch')
   rows.append({'size':size,'case_id':case_id,'oracle':effects['oracle'],'event_mode':events,'effect_mode':effects})
 after=frozen()
 if after!=locked:raise RuntimeError('source lock mismatch after worker')
 return {'worker':index,'pid':os.getpid(),'sources_before':before,'sources_after':after,'rows':rows}
def main():
 if sys.argv[1:]==['--lock']:
  if LOCK.exists() or OUT.exists():raise SystemExit('refusing to overwrite lock/capture')
  LOCK.write_text(json.dumps({'schema':'ThoughtexperimentEffectTraceDiagnosisV1Lock','sources':frozen(),'workers':3,'sizes':SIZES,'cases_per_size':CASES_PER_SIZE,'tie_break':'lowest_effect_index'},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return 0
 if len(sys.argv)==3 and sys.argv[1]=='--worker':print(json.dumps(worker(int(sys.argv[2])),separators=(',',':'),sort_keys=True));return 0
 if sys.argv[1:]!=['--run']:raise SystemExit('usage: --lock | --run | --worker N')
 if frozen()!=json.loads(LOCK.read_text())['sources']:raise SystemExit('source lock mismatch before capture')
 env=dict(os.environ);env['PYTHONPATH']=os.pathsep.join((str(ROOT/'runners/dsl/python'),str(ROOT)));workers=[]
 for i in range(3):
  p=subprocess.run([sys.executable,str(RUNNER),'--worker',str(i)],cwd=ROOT,env=env,text=True,capture_output=True,timeout=240)
  if p.returncode:raise RuntimeError(f'worker {i}: {p.stderr[-2000:]}')
  workers.append(json.loads(p.stdout.strip().splitlines()[-1]))
 if frozen()!=json.loads(LOCK.read_text())['sources']:raise SystemExit('source lock drift during capture')
 OUT.write_text(json.dumps({'schema':'ThoughtexperimentEffectTraceDiagnosisV1','lock_sha256':sha(LOCK),'host':platform.platform(),'workers':workers},indent=2,sort_keys=True)+'\n');print(OUT.relative_to(ROOT));return 0
if __name__=='__main__':raise SystemExit(main())

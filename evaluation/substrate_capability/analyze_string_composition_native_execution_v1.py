#!/usr/bin/env python3
"""Independent formula and native-output replay audit for composition ASTs."""
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT),str(ROOT/'scripts'),str(ROOT/'runners/dsl/python')]
FIX=ROOT/'tests/fixtures/substrate_string_composition_fresh/tasks.json';RAW=ROOT/'evaluation/reports/string_composition_native_execution_v1_20261003.json';LOCK=ROOT/'evaluation/substrate_capability/string_composition_native_execution_v1_lock_20261003.json';OUT=ROOT/'evaluation/reports/string_composition_native_execution_v1_analysis_20261003.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def oracle(f,s,a):
 if f=='casefold_count':return s.casefold().count(a.casefold())
 if f=='casefold_split':return s.casefold().split(a.casefold())
 if f=='reverse_then_split':return s[::-1].split(a)
 if f=='remove_separator':return ''.join(s.split(a))
 if f=='reverse_then_replace':return s[::-1].replace(a[0],a[1])
 if f=='split_reverse_tokens':return [part[::-1] for part in s.split(a)]
 raise ValueError(f)
def main():
 import prog_synthesis_battery as p4
 suite=json.loads(FIX.read_text());raw=json.loads(RAW.read_text());lock=json.loads(LOCK.read_text());errors=[];checked=0;raw_by_id={x['task_id']:x for x in raw['tasks']}
 if raw.get('lock_sha256')!=sha(LOCK):errors.append('lock hash mismatch')
 if len(raw_by_id)!=18 or len(suite['tasks'])!=18:errors.append('task count mismatch')
 for task in suite['tasks']:
  record=raw_by_id.get(task['id'])
  if record is None:errors.append(f"{task['id']}: missing result");continue
  if len(record.get('rows',[]))!=7:errors.append(f"{task['id']}: row count mismatch")
  expected_rows=task['example_rows']+task['held_out_rows'];replayed=[]
  for saved,fixture in zip(record.get('rows',[]),expected_rows):
   checked+=1;oracle_y=oracle(task['oracle_kind'],fixture['inputs']['s'],task['parameter'])
   if oracle_y!=fixture['expected']:errors.append(f"{task['id']}: fixture formula mismatch")
   ev=p4.prog_eval(record['ir'],dict(fixture['inputs']));got=ev.get('result');ok=ev.get('halted') is True and ev.get('trap') is None and p4.agree(got,fixture['expected'])
   if saved.get('got')!=got or saved.get('halted')!=ev.get('halted') or saved.get('trap')!=ev.get('trap') or saved.get('exact')!=bool(ok):errors.append(f"{task['id']}: replay mismatch")
   if not ok:replayed.append(fixture['inputs'])
  if bool(record.get('exact')) != (len(replayed) == 0):errors.append(f"{task['id']}: exact flag mismatch")
 result={'schema':'StringCompositionNativeExecutionV1Analysis','passed':not errors,'errors':errors,'task_count':len(suite['tasks']),'rows_replayed':checked,'all_rows_exact_tasks':sum(x.get('exact',False) for x in raw['tasks']),'heldout_exact_tasks':sum(x.get('heldout_exact',False) for x in raw['tasks']),'errors_in_execution':raw.get('summary',{}).get('evaluation_errors'),'input_hashes':{'lock':sha(LOCK),'capture':sha(RAW),'fixture':sha(FIX),'analyzer':sha(Path(__file__))}}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,indent=2));return int(bool(errors))
if __name__=='__main__':raise SystemExit(main())

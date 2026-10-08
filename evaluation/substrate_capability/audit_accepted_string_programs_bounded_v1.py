#!/usr/bin/env python3
"""Source-locked exhaustive scoring on finite string domains."""
import hashlib,itertools,json,platform,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT),str(ROOT/'scripts'),str(ROOT/'runners/dsl/python')]
HERE=Path(__file__).resolve();PRE=ROOT/'docs/research/engine_substrate/STRING_COMPOSITION_BOUNDED_EXHAUSTIVE_V1_PREREG_20261003.md'
FIX=ROOT/'tests/fixtures/substrate_string_composition_fresh/tasks.json';RAW=ROOT/'evaluation/reports/string_composition_fresh_pbe_v1_20261003.json';PBELOCK=ROOT/'evaluation/substrate_capability/string_composition_fresh_pbe_v1_lock_20261003.json'
LOCK=ROOT/'evaluation/substrate_capability/accepted_string_bounded_v1_lock_20261003.json';OUT=ROOT/'evaluation/reports/accepted_string_bounded_v1_20261003.json'
SOURCES=('domains/prog_synthesis.py','scripts/prog_synthesis_battery.py','runners/dsl/src/term.rs','runners/dsl/src/prog_eval.rs','runners/dsl/src/py.rs','runners/dsl/python/substrate_rs/_native.build.json','runners/dsl/Cargo.lock')
ARMS=('main','no_retrieval','no_retrieval_escalated','main_replay')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def oracle(f,s,a):
 if f=='casefold_count':return s.casefold().count(a.casefold())
 if f=='split_reverse_tokens':return [v[::-1] for v in s.split(a)]
 raise ValueError(f)
def inputs():
 from substrate_rs import _native
 from domains.engine_provenance import rust_source_fingerprint
 files=[ROOT/x for x in SOURCES]+[HERE,PRE,FIX,RAW,PBELOCK]
 return {'files':{str(p.relative_to(ROOT)):sha(p) for p in files},'native':{'path':str(Path(_native.__file__).resolve()),'sha256':sha(Path(_native.__file__))},'engine':rust_source_fingerprint(str(ROOT))}
def fresh():
 stale=subprocess.check_output([sys.executable,'-c',"from domains.engine_provenance import build_is_stale; print('\\n'.join(build_is_stale('.')))"] ,cwd=ROOT,text=True).strip()
 if stale:raise SystemExit('native build stale:\n'+stale)
def domain(task):
 if task['oracle_kind']=='casefold_count':
  alphabet=list(dict.fromkeys([*task['parameter'],*task['parameter'].upper(),'#']))
 elif task['oracle_kind']=='split_reverse_tokens':alphabet=list(dict.fromkeys(['a','A',task['parameter'],'#']))
 else:raise ValueError(task['oracle_kind'])
 return alphabet,[''.join(xs) for n in range(6) for xs in itertools.product(alphabet,repeat=n)]
def main():
 args=sys.argv[1:]
 if args==['--lock']:
  if LOCK.exists() or OUT.exists():raise SystemExit('refusing overwrite')
  fresh();LOCK.write_text(json.dumps({'schema':'AcceptedStringBoundedV1Lock','inputs':inputs(),'arms':list(ARMS),'max_length':5},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return 0
 if args!=['--run']:raise SystemExit('usage: --lock | --run')
 lock=json.loads(LOCK.read_text())
 if inputs()!=lock['inputs']:raise SystemExit('source/input lock mismatch')
 fresh();import os;os.environ.setdefault('OZMA_NO_LLM','1');os.environ.setdefault('OZMA_SEED_PERSIST_DISABLED','1')
 import prog_synthesis_battery as p4
 suite=json.loads(FIX.read_text());raw=json.loads(RAW.read_text());results=[];audit_errors=[];total=correct_total=0
 for task in suite['tasks']:
  if task['oracle_kind'] not in ('casefold_count','split_reverse_tokens'):continue
  alphabet,strings=domain(task)
  for arm in ARMS:
   record=next(r for r in raw['cases'][arm] if r['task_id']==task['id'])
   if record['status']!='accepted':continue
   by_len={str(n):{'n':0,'correct':0} for n in range(6)};errors=0
   for s in strings:
    out=p4.prog_eval(record['ir'],{'s':s});expected=oracle(task['oracle_kind'],s,task['parameter']);ok=out.get('halted') is True and out.get('trap') is None and p4.agree(out.get('result'),expected)
    d=by_len[str(len(s))];d['n']+=1;d['correct']+=int(bool(ok));errors+=int(out.get('trap') is not None or out.get('halted') is not True)
   n=sum(x['n'] for x in by_len.values());correct=sum(x['correct'] for x in by_len.values());total+=n;correct_total+=correct
   results.append({'task_id':task['id'],'family':task['family'],'parameter':task['parameter'],'arm':arm,'alphabet':alphabet,'max_length':5,'inputs':n,'correct':correct,'accuracy':correct/n,'exact_on_domain':correct==n,'execution_errors':errors,'by_length':by_len})
 payload={'schema':'AcceptedStringBoundedV1Results','lock_sha256':sha(LOCK),'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'host':platform.platform(),'results':results,'summary':{'accepted_artifacts':len(results),'input_program_evaluations':total,'correct_evaluations':correct_total,'aggregate_accuracy':correct_total/total if total else None,'exact_on_domain_artifacts':sum(r['exact_on_domain'] for r in results),'execution_errors':sum(r['execution_errors'] for r in results),'audit_errors':audit_errors}}
 OUT.write_text(json.dumps(payload,indent=2,sort_keys=True)+'\n');print(json.dumps(payload['summary'],indent=2));return int(bool(audit_errors))
if __name__=='__main__':raise SystemExit(main())

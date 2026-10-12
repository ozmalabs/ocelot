#!/usr/bin/env python3
"""Source-locked independent input stress scoring for accepted P4 programs."""
import hashlib, json, platform, subprocess, sys, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts'),str(ROOT/'runners/dsl/python')]
HERE=Path(__file__).resolve()
PRE=ROOT/'docs/research/engine_substrate/STRING_COMPOSITION_ACCEPTED_PROGRAM_STRESS_V1_PREREG_20261003.md'
FIX=ROOT/'tests/fixtures/substrate_string_composition_fresh/tasks.json'
GEN=ROOT/'tests/fixtures/substrate_string_composition_fresh/build_tasks.py'
RAW=ROOT/'evaluation/reports/string_composition_fresh_pbe_v1_20261003.json'
BASE_LOCK=ROOT/'evaluation/substrate_capability/string_composition_fresh_pbe_v1_lock_20261003.json'
LOCK=ROOT/'evaluation/substrate_capability/accepted_string_program_stress_v1_lock_20261003.json'
OUT=ROOT/'evaluation/reports/accepted_string_program_stress_v1_20261003.json'
SOURCES=('domains/prog_synthesis.py','scripts/prog_synthesis_battery.py','runners/dsl/src/term.rs','runners/dsl/src/prog_eval.rs','runners/dsl/src/py.rs','runners/dsl/python/substrate_rs/_native.build.json','runners/dsl/Cargo.lock')
ARMS=('main','no_retrieval','no_retrieval_escalated','main_replay')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def oracle(f,s,a):
    if f=='casefold_count': return s.casefold().count(a.casefold())
    if f=='casefold_split': return s.casefold().split(a.casefold())
    if f=='reverse_then_split': return s[::-1].split(a)
    if f=='remove_separator': return ''.join(s.split(a))
    if f=='reverse_then_replace': return s[::-1].replace(a[0],a[1])
    if f=='split_reverse_tokens': return [x[::-1] for x in s.split(a)]
    raise ValueError(f)
def inputs():
    from substrate_rs import _native
    from domains.engine_provenance import rust_source_fingerprint
    files=[ROOT/x for x in SOURCES]+[HERE,PRE,FIX,GEN,RAW,BASE_LOCK]
    return {'files':{str(p.relative_to(ROOT)):sha(p) for p in files},'native':{'path':str(Path(_native.__file__).resolve()),'sha256':sha(Path(_native.__file__))},'engine':rust_source_fingerprint(str(ROOT))}
def fresh():
    stale=subprocess.check_output([sys.executable,'-c',"from domains.engine_provenance import build_is_stale; print('\\n'.join(build_is_stale('.')))"] ,cwd=ROOT,text=True).strip()
    if stale: raise SystemExit('native build stale:\n'+stale)
def main():
    args=sys.argv[1:]
    if args==['--lock']:
        if LOCK.exists() or OUT.exists(): raise SystemExit('refusing overwrite')
        fresh();LOCK.write_text(json.dumps({'schema':'AcceptedStringProgramStressV1Lock','inputs':inputs(),'tasks':18,'inputs_per_task':50,'seed_offset':1000003,'v1_1_prefix_curve':True,'arms':list(ARMS)},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return 0
    if args!=['--run']: raise SystemExit('usage: --lock | --run')
    lock=json.loads(LOCK.read_text())
    if inputs()!=lock['inputs']: raise SystemExit('source/input lock mismatch')
    fresh();os_env=__import__('os').environ;os_env.setdefault('OZMA_NO_LLM','1');os_env.setdefault('OZMA_SEED_PERSIST_DISABLED','1')
    import random
    import prog_synthesis_battery as p4
    import importlib.util
    spec=importlib.util.spec_from_file_location('fresh_string_gen',GEN);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    suite=json.loads(FIX.read_text());raw=json.loads(RAW.read_text());all_results=[];checked=0;errors=[]
    for ordinal,task in enumerate(suite['tasks'],1):
        rng=random.Random(20261003+ordinal*7919+1000003)
        known={json.dumps(r['inputs'],sort_keys=True) for r in task['example_rows']+task['held_out_rows']}
        stress_by_key={}
        for _ in range(100):
            if len(stress_by_key)>=50: break
            for candidate in mod.make_rows(rng,task['oracle_kind'],task['parameter']):
                key=json.dumps(candidate['inputs'],sort_keys=True)
                if key not in known: stress_by_key.setdefault(key,candidate)
        stress=list(stress_by_key.values())[:50]
        if len(stress)!=50: errors.append(task['id']+': could not construct 50 disjoint stress inputs')
        for row in stress:
            expected=oracle(task['oracle_kind'],row['inputs']['s'],task['parameter'])
            if expected!=row['expected']: errors.append(task['id']+': generator/formula mismatch')
        for arm in ARMS:
            record=next(x for x in raw['cases'][arm] if x['task_id']==task['id'])
            if record['status']!='accepted': continue
            ok_count=0;trap_count=0;row_correct=[]
            for row in stress:
                checked+=1;ev=p4.prog_eval(record['ir'],dict(row['inputs']));good=ev.get('halted') is True and ev.get('trap') is None and p4.agree(ev.get('result'),row['expected'])
                ok_count+=int(bool(good));row_correct.append(bool(good));trap_count+=int(ev.get('trap') is not None or ev.get('halted') is not True)
            all_results.append({'task_id':task['id'],'family':task['family'],'arm':arm,'rows':len(stress),'correct':ok_count,'accuracy':ok_count/len(stress),'exact_on_sample':ok_count==len(stress),'execution_errors':trap_count,'row_correct':row_correct})
    nrows=sum(x['rows'] for x in all_results);correct=sum(x['correct'] for x in all_results)
    payload={'schema':'AcceptedStringProgramStressV1Results','lock_sha256':sha(LOCK),'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'host':platform.platform(),'results':all_results,'summary':{'accepted_programs':len(all_results),'stress_inputs_per_program':50,'program_rows_checked':checked,'correct_rows':correct,'aggregate_row_accuracy':correct/nrows if nrows else None,'exact_on_sample_programs':sum(x['exact_on_sample'] for x in all_results),'execution_errors':sum(x['execution_errors'] for x in all_results),'audit_errors':errors}}
    OUT.write_text(json.dumps(payload,indent=2,sort_keys=True)+'\n');print(json.dumps(payload['summary'],indent=2));return int(bool(errors))
if __name__=='__main__': raise SystemExit(main())

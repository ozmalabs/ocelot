#!/usr/bin/env python3
"""Measure warm-route process CPU/thread counts under a Rayon thread cap."""
from __future__ import annotations
import hashlib,json,os,platform,subprocess,sys,tempfile,time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
RUNNER=Path(__file__).resolve()
PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_ADEQUACY_WARM_CONVERSE_THREAD_DIAGNOSTIC_V1_PREREG_20261002.md'
ANALYZER=ROOT/'evaluation/substrate_capability/analyze_substrate_adequacy_warm_converse_thread_diagnostic_v1.py'
LOCK=ROOT/'evaluation/substrate_capability/substrate_adequacy_warm_converse_thread_diagnostic_v1_lock_20261002.json'
RAW=ROOT/'evaluation/reports/substrate_adequacy_warm_converse_thread_diagnostic_v1_raw_20261002.json'
BASE=ROOT/'evaluation/substrate_capability/substrate_adequacy_warm_converse_cost_v1.py'
BASE_LOCK=ROOT/'evaluation/substrate_capability/substrate_adequacy_warm_converse_cost_v1_lock_20261002.json'
SCHEDULE=(('default',1),('one_thread',2),('one_thread',3),('default',4),('default',5),('one_thread',6))

def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def parent_active()->dict:return json.loads(BASE_LOCK.read_text())['active']
def frozen()->dict:
    return {'runner':sha(RUNNER),'protocol':sha(PROTOCOL),'analyzer':sha(ANALYZER),
            'base_runner':sha(BASE),'base_lock':sha(BASE_LOCK),'parent_active':parent_active()}
def thread_count(pid:int)->int:
    try:return len(os.listdir(f'/proc/{pid}/task'))
    except OSError:return 0
def worker(mode:str,rep:int,base_active:dict)->dict:
    env=os.environ.copy()
    env.update(OZMA_NO_LLM='1',OZMA_SEED_PERSIST_DISABLED='1',
               PYTHONPATH=f"{ROOT}:{ROOT/'runners/dsl/python'}:{ROOT/'evaluation/substrate_capability'}")
    if mode=='one_thread':env['RAYON_NUM_THREADS']='1'
    else:env.pop('RAYON_NUM_THREADS',None)
    with tempfile.TemporaryFile(mode='w+t') as out,tempfile.TemporaryFile(mode='w+t') as err:
        proc=subprocess.Popen([sys.executable,str(BASE),'--worker','parity','missing_evidence',str(300+rep)],
            cwd=ROOT,env=env,text=True,stdout=out,stderr=err)
        max_threads=0
        while proc.poll() is None:
            max_threads=max(max_threads,thread_count(proc.pid));time.sleep(.005)
        max_threads=max(max_threads,thread_count(proc.pid))
        out.seek(0);stdout=out.read();err.seek(0);stderr=err.read()
    if proc.returncode:raise RuntimeError(f'{mode}/{rep} failed: {stderr[-2000:]}')
    d=json.loads(stdout.splitlines()[-1])
    if d['active_after']!=base_active:raise RuntimeError('worker source/native fingerprint differs from parent lock')
    return {'mode':mode,'requested_rayon_threads':1 if mode=='one_thread' else None,
      'pid':d['pid'],'max_os_threads_observed':max_threads,'task':d['task'],'condition':d['condition'],
      'reply':d['reply'],'shape_delta':d['shape_delta'],'state_before':d['state_before'],
      'state_after':d['state_after'],'heldout':d['heldout'],'timing_ns':d['timing_ns'],
      'warm_wall_ns':d['warm_wall_ns'],'active_after':d['active_after']}
def main()->None:
    if len(sys.argv)==2 and sys.argv[1]=='--lock':
        if LOCK.exists() or RAW.exists():raise SystemExit('refusing to overwrite lock or capture')
        LOCK.write_text(json.dumps({'schema':'WarmConverseThreadDiagnosticV1Lock','sources':frozen(),
          'schedule':SCHEDULE,'sample_interval_ms':5},indent=2,sort_keys=True)+'\n')
        print(LOCK.relative_to(ROOT));return
    lock=json.loads(LOCK.read_text())
    if lock['sources']!=frozen():raise SystemExit('source lock drift')
    if RAW.exists():raise SystemExit('capture exists; refusing overwrite')
    before=frozen();active=parent_active();rows=[]
    for mode,rep in SCHEDULE:
        row=worker(mode,rep,active);rows.append(row)
        print(json.dumps({'mode':mode,'rep':rep,'pid':row['pid'],'threads':row['max_os_threads_observed'],
          'wall_ms':row['timing_ns']['target_wall']/1e6,'cpu_ms':row['timing_ns']['target_cpu']/1e6}),flush=True)
    after=frozen()
    capture={'schema':'WarmConverseThreadDiagnosticV1Capture','lock':lock,'source_before':before,
      'source_after':after,'source_stable':before==after,'host':platform.platform(),
      'logical_cpus':os.cpu_count(),'cgroup_cpu_max':Path('/sys/fs/cgroup/cpu.max').read_text().strip()
        if Path('/sys/fs/cgroup/cpu.max').exists() else None,'rows':rows}
    RAW.write_text(json.dumps(capture,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'workers':len(rows),'source_stable':capture['source_stable'],'raw':str(RAW.relative_to(ROOT))}))
if __name__=='__main__':main()

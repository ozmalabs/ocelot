#!/usr/bin/env python3
"""Split warm-route aggregate CPU into caller-thread and other-thread CPU."""
from __future__ import annotations
import hashlib,importlib.util,json,os,platform,subprocess,sys,tempfile,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
RUNNER=Path(__file__).resolve()
PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_ADEQUACY_WARM_CONVERSE_CALLER_CPU_V1_PREREG_20261002.md'
ANALYZER=ROOT/'evaluation/substrate_capability/analyze_substrate_adequacy_warm_converse_caller_cpu_v1.py'
LOCK=ROOT/'evaluation/substrate_capability/substrate_adequacy_warm_converse_caller_cpu_v1_lock_20261002.json'
RAW=ROOT/'evaluation/reports/substrate_adequacy_warm_converse_caller_cpu_v1_raw_20261002.json'
POOL_RUNNER=ROOT/'evaluation/substrate_capability/substrate_adequacy_warm_converse_rayon_pool_v1.py'
POOL_LOCK=ROOT/'evaluation/substrate_capability/substrate_adequacy_warm_converse_rayon_pool_v1_lock_20261002.json'
BASE=ROOT/'evaluation/substrate_capability/substrate_adequacy_warm_converse_cost_v1.py'
BASE_LOCK=ROOT/'evaluation/substrate_capability/substrate_adequacy_warm_converse_cost_v1_lock_20261002.json'
SCHEDULE=(('default',1),('one_thread',2),('one_thread',3),('default',4),('default',5),('one_thread',6))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod
def load_base():
    sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python'),str(ROOT/'evaluation/substrate_capability')]
    return load(BASE,'warm_caller_cpu_base')
def frozen():
    base=load_base()
    return {'runner':sha(RUNNER),'protocol':sha(PROTOCOL),'analyzer':sha(ANALYZER),
      'pool_runner':sha(POOL_RUNNER),'pool_lock':sha(POOL_LOCK),'base_runner':sha(BASE),
      'base_lock_file':sha(BASE_LOCK),'base_runtime_lock':base.frozen()}
def worker(mode,rep,base_lock):
    from substrate import world_adapter as wa
    Original=wa.WorldAdapter;cpu={}
    class CallerCpuWorldAdapter(Original):
        def __init__(self,*args,**kwargs):
            super().__init__(*args,**kwargs);self._caller_cpu_converse_count=0
        def converse(self,*args,**kwargs):
            call=self._caller_cpu_converse_count
            if call==1:
                cpu['native_tid_before']=threading_native_id()
                start=time.thread_time_ns()
            result=super().converse(*args,**kwargs)
            if call==1:
                cpu['caller_thread_cpu_ns']=time.thread_time_ns()-start
                cpu['native_tid_after']=threading_native_id()
            self._caller_cpu_converse_count+=1
            return result
    wa.WorldAdapter=CallerCpuWorldAdapter
    pool=load(POOL_RUNNER,'warm_rayon_pool_probe')
    result=pool.worker(mode,rep,base_lock)
    process_cpu=result['worker']['timing_ns']['target_cpu']
    caller_cpu=cpu.get('caller_thread_cpu_ns')
    if caller_cpu is None:raise RuntimeError('target caller-thread CPU was not measured')
    result['caller_cpu']={'native_tid':cpu['native_tid_before'],'native_tid_after':cpu['native_tid_after'],
      'caller_thread_cpu_ns':caller_cpu,'other_thread_aggregate_cpu_ns':max(0,process_cpu-caller_cpu)}
    return result
def threading_native_id():
    import threading
    return threading.get_native_id()
def run_child(mode,rep,expected):
    env=os.environ.copy();env.update(OZMA_NO_LLM='1',OZMA_SEED_PERSIST_DISABLED='1',
      PYTHONPATH=f"{ROOT}:{ROOT/'runners/dsl/python'}:{ROOT/'evaluation/substrate_capability'}")
    if mode=='one_thread':env['RAYON_NUM_THREADS']='1'
    else:env.pop('RAYON_NUM_THREADS',None)
    with tempfile.TemporaryFile(mode='w+t') as out,tempfile.TemporaryFile(mode='w+t') as err:
        proc=subprocess.Popen([sys.executable,str(RUNNER),'--worker',mode,str(rep)],cwd=ROOT,env=env,text=True,stdout=out,stderr=err)
        maximum=0
        while proc.poll() is None:
            try:maximum=max(maximum,len(os.listdir(f'/proc/{proc.pid}/task')))
            except OSError:pass
            time.sleep(.005)
        out.seek(0);stdout=out.read();err.seek(0);stderr=err.read()
    if proc.returncode:raise RuntimeError(f'{mode}/{rep}: {stderr[-2000:]}')
    result=json.loads(stdout.splitlines()[-1]);result['worker']['max_os_threads_sampled']=maximum
    result['worker']['mode']=mode;result['worker']['rep']=rep
    if result['worker']['active_after']!=expected['base_runtime_lock']['active']:
        raise RuntimeError('worker source/native fingerprints differ from lock')
    return result
def main():
    if sys.argv[1:2]==['--worker']:
        expected=json.loads(LOCK.read_text());print(json.dumps(worker(sys.argv[2],int(sys.argv[3]),expected['sources']['base_runtime_lock']),sort_keys=True));return
    if sys.argv[1:]==['--lock']:
        if LOCK.exists() or RAW.exists():raise SystemExit('refusing to overwrite lock or capture')
        LOCK.write_text(json.dumps({'schema':'WarmConverseCallerCpuV1Lock','sources':frozen(),
          'schedule':SCHEDULE,'sample_interval_ms':5},indent=2,sort_keys=True)+'\n')
        print(LOCK.relative_to(ROOT));return
    lock=json.loads(LOCK.read_text())
    if lock['sources']!=frozen():raise SystemExit('source lock drift')
    if RAW.exists():raise SystemExit('capture exists; refusing overwrite')
    before=frozen();rows=[]
    for mode,rep in SCHEDULE:
        row=run_child(mode,rep,lock['sources']);rows.append(row)
        w=row['worker'];c=row['caller_cpu']
        print(json.dumps({'mode':mode,'rep':rep,'pid':w['pid'],'rayon_threads':row['observed']['rayon_pool_threads']['after_target'],
          'wall_ms':w['timing_ns']['target_wall']/1e6,'process_cpu_ms':w['timing_ns']['target_cpu']/1e6,
          'caller_cpu_ms':c['caller_thread_cpu_ns']/1e6,'other_cpu_ms':c['other_thread_aggregate_cpu_ns']/1e6,
          'peak_threads':w['max_os_threads_sampled']}),flush=True)
    after=frozen();capture={'schema':'WarmConverseCallerCpuV1Capture','lock':lock,
      'source_before':before,'source_after':after,'source_stable':before==after,
      'host':platform.platform(),'logical_cpus':os.cpu_count(),
      'cgroup_cpu_max':Path('/sys/fs/cgroup/cpu.max').read_text().strip() if Path('/sys/fs/cgroup/cpu.max').exists() else None,'rows':rows}
    RAW.write_text(json.dumps(capture,indent=2,sort_keys=True)+'\n');print(json.dumps({'workers':len(rows),'source_stable':capture['source_stable'],'raw':str(RAW.relative_to(ROOT))}))
if __name__=='__main__':main()

#!/usr/bin/env python3
"""Locked warm-route probe of Rayon pool size and process thread counts."""
from __future__ import annotations
import hashlib,importlib.util,json,os,platform,subprocess,sys,tempfile,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
RUNNER=Path(__file__).resolve()
PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_ADEQUACY_WARM_CONVERSE_RAYON_POOL_V1_PREREG_20261002.md'
ANALYZER=ROOT/'evaluation/substrate_capability/analyze_substrate_adequacy_warm_converse_rayon_pool_v1.py'
LOCK=ROOT/'evaluation/substrate_capability/substrate_adequacy_warm_converse_rayon_pool_v1_lock_20261002.json'
RAW=ROOT/'evaluation/reports/substrate_adequacy_warm_converse_rayon_pool_v1_raw_20261002.json'
BASE=ROOT/'evaluation/substrate_capability/substrate_adequacy_warm_converse_cost_v1.py'
BASE_LOCK=ROOT/'evaluation/substrate_capability/substrate_adequacy_warm_converse_cost_v1_lock_20261002.json'
SCHEDULE=(('default',1),('one_thread',2),('one_thread',3),('default',4),('default',5),('one_thread',6))

def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def load_base():
    sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python'),str(ROOT/'evaluation/substrate_capability')]
    spec=importlib.util.spec_from_file_location('warm_converse_base_v1',BASE)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod
def frozen()->dict:
    base=load_base()
    return {'runner':sha(RUNNER),'protocol':sha(PROTOCOL),'analyzer':sha(ANALYZER),
      'base_runner':sha(BASE),'base_lock_file':sha(BASE_LOCK),'base_runtime_lock':base.frozen()}
def os_threads()->int:
    try:return len(os.listdir('/proc/self/task'))
    except OSError:return 0
def worker(mode:str,rep:int,base_lock:dict)->dict:
    from substrate import world_adapter as wa
    Original=wa.WorldAdapter;observed={'phase_os_threads':{},'rayon_pool_threads':{}}
    class ProbedWorldAdapter(Original):
        def __init__(self,*args,**kwargs):
            super().__init__(*args,**kwargs)
            observed['phase_os_threads']['after_adapter_init']=os_threads()
            self._rayon_probe_calls=0
        def converse(self,*args,**kwargs):
            call=self._rayon_probe_calls
            if call==1:
                observed['phase_os_threads']['before_target']=os_threads()
                observed['rayon_pool_threads']['before_target']=self.inner.rayon_current_num_threads()
                observed['phase_os_threads']['after_pool_query_before_target']=os_threads()
            result=super().converse(*args,**kwargs)
            if call==0:
                observed['phase_os_threads']['after_warm_before_pool_query']=os_threads()
                observed['rayon_pool_threads']['after_warm']=self.inner.rayon_current_num_threads()
                observed['phase_os_threads']['after_warm_after_pool_query']=os_threads()
            elif call==1:
                observed['phase_os_threads']['after_target_before_pool_query']=os_threads()
                observed['rayon_pool_threads']['after_target']=self.inner.rayon_current_num_threads()
                observed['phase_os_threads']['after_target_after_pool_query']=os_threads()
            self._rayon_probe_calls+=1
            return result
    wa.WorldAdapter=ProbedWorldAdapter
    base=load_base()
    row=base.worker('parity','missing_evidence',rep,base_lock)
    if base.frozen()!=base_lock:raise RuntimeError('runtime source/native lock drift')
    return {'worker':{'pid':row['pid'],'task':row['task'],'condition':row['condition'],'reply':row['reply'],
      'shape_delta':row['shape_delta'],'state_before':row['state_before'],'state_after':row['state_after'],
      'heldout':row['heldout'],'timing_ns':row['timing_ns'],'warm_wall_ns':row['warm_wall_ns'],
      'active_after':row['active_after']},'observed':observed}
def run_child(mode:str,rep:int,expected:dict)->dict:
    env=os.environ.copy();env.update(OZMA_NO_LLM='1',OZMA_SEED_PERSIST_DISABLED='1',
      PYTHONPATH=f"{ROOT}:{ROOT/'runners/dsl/python'}:{ROOT/'evaluation/substrate_capability'}")
    if mode=='one_thread':env['RAYON_NUM_THREADS']='1'
    else:env.pop('RAYON_NUM_THREADS',None)
    cmd=[sys.executable,str(RUNNER),'--worker',mode,str(rep)]
    with tempfile.TemporaryFile(mode='w+t') as out,tempfile.TemporaryFile(mode='w+t') as err:
        proc=subprocess.Popen(cmd,cwd=ROOT,env=env,text=True,stdout=out,stderr=err)
        maximum=0
        while proc.poll() is None:
            try:maximum=max(maximum,len(os.listdir(f'/proc/{proc.pid}/task')))
            except OSError:pass
            time.sleep(.005)
        maximum=max(maximum,0);out.seek(0);stdout=out.read();err.seek(0);stderr=err.read()
    if proc.returncode:raise RuntimeError(f'{mode}/{rep}: {stderr[-2000:]}')
    result=json.loads(stdout.splitlines()[-1]);result['worker']['max_os_threads_sampled']=maximum
    result['worker']['mode']=mode;result['worker']['rep']=rep
    if result['worker']['active_after']!=expected['base_runtime_lock']['active']:
        raise RuntimeError('worker active source fingerprints differ from lock')
    return result
def main():
    if sys.argv[1:2]==['--worker']:
        expected=json.loads(LOCK.read_text());mode=sys.argv[2];rep=int(sys.argv[3])
        print(json.dumps(worker(mode,rep,expected['sources']['base_runtime_lock']),sort_keys=True));return
    if sys.argv[1:]==['--lock']:
        if LOCK.exists() or RAW.exists():raise SystemExit('refusing to overwrite lock or capture')
        LOCK.write_text(json.dumps({'schema':'WarmConverseRayonPoolV1Lock','sources':frozen(),
          'schedule':SCHEDULE,'sample_interval_ms':5},indent=2,sort_keys=True)+'\n')
        print(LOCK.relative_to(ROOT));return
    lock=json.loads(LOCK.read_text())
    if lock['sources']!=frozen():raise SystemExit('source lock drift')
    if RAW.exists():raise SystemExit('capture exists; refusing overwrite')
    before=frozen();rows=[]
    for mode,rep in SCHEDULE:
        row=run_child(mode,rep,lock['sources']);rows.append(row)
        print(json.dumps({'mode':mode,'rep':rep,'pid':row['worker']['pid'],
          'pool_after_warm':row['observed']['rayon_pool_threads'].get('after_warm'),
          'os_threads_peak':row['worker']['max_os_threads_sampled'],
          'target_wall_ms':row['worker']['timing_ns']['target_wall']/1e6,
          'target_cpu_ms':row['worker']['timing_ns']['target_cpu']/1e6}),flush=True)
    after=frozen();capture={'schema':'WarmConverseRayonPoolV1Capture','lock':lock,
      'source_before':before,'source_after':after,'source_stable':before==after,
      'host':platform.platform(),'logical_cpus':os.cpu_count(),
      'cgroup_cpu_max':Path('/sys/fs/cgroup/cpu.max').read_text().strip() if Path('/sys/fs/cgroup/cpu.max').exists() else None,
      'rows':rows}
    RAW.write_text(json.dumps(capture,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'workers':len(rows),'source_stable':capture['source_stable'],'raw':str(RAW.relative_to(ROOT))}))
if __name__=='__main__':main()

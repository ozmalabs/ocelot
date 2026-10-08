#!/usr/bin/env python3
"""Parent-process sampling of per-thread CPU during warm converse."""
from __future__ import annotations
import hashlib, importlib.util, json, os, platform, subprocess, sys, tempfile, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
RUNNER=Path(__file__).resolve()
PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_ADEQUACY_WARM_CONVERSE_THREAD_CPU_V2_PREREG_20261002.md'
ANALYZER=ROOT/'evaluation/substrate_capability/analyze_substrate_adequacy_warm_converse_thread_cpu_v2.py'
LOCK=ROOT/'evaluation/substrate_capability/substrate_adequacy_warm_converse_thread_cpu_v2_lock_20261002.json'
RAW=ROOT/'evaluation/reports/substrate_adequacy_warm_converse_thread_cpu_v2_raw_20261002.json'
CALLER=ROOT/'evaluation/substrate_capability/substrate_adequacy_warm_converse_caller_cpu_v1.py'
CALLER_LOCK=ROOT/'evaluation/substrate_capability/substrate_adequacy_warm_converse_caller_cpu_v1_lock_20261002.json'
SCHEDULE=[('default',1),('one_thread',2),('one_thread',3),('default',4),('default',5),('one_thread',6)]
SAMPLE_NS=2_000_000
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(path,name):
 spec=importlib.util.spec_from_file_location(name,path);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod
def frozen():
 caller=load(CALLER,'thread_cpu_v2_caller')
 return {'runner':sha(RUNNER),'protocol':sha(PROTOCOL),'analyzer':sha(ANALYZER),
  'caller_runner':sha(CALLER),'caller_lock_file':sha(CALLER_LOCK),'caller_runtime_lock':caller.load_base().frozen()}
def worker(mode,rep,expected):
 from substrate import world_adapter as wa
 Original=wa.WorldAdapter;marker=Path(os.environ['OZMA_THREAD_CPU_MARKER']);counter={'n':0}
 class MarkerAdapter(Original):
  def converse(self,*args,**kwargs):
   n=counter['n'];counter['n']+=1
   if n!=1:return super().converse(*args,**kwargs)
   with marker.open('a') as f:f.write(json.dumps({'phase':'begin','monotonic_ns':time.monotonic_ns()})+'\n');f.flush()
   try:return super().converse(*args,**kwargs)
   finally:
    with marker.open('a') as f:f.write(json.dumps({'phase':'end','monotonic_ns':time.monotonic_ns()})+'\n');f.flush()
 wa.WorldAdapter=MarkerAdapter
 caller=load(CALLER,'warm_converse_caller_cpu_v2_worker')
 return caller.worker(mode,rep,expected)
def read_marker(path):
 try:return [json.loads(x) for x in path.read_text().splitlines() if x.strip()]
 except (OSError,ValueError):return []
def snapshot(pid):
 rows={}
 try:entries=list(Path(f'/proc/{pid}/task').iterdir())
 except OSError:return rows
 for entry in entries:
  try:
   stat=(entry/'stat').read_text();close=stat.rfind(')');fields=stat[close+2:].split()
   key=(int(entry.name),int(fields[19]));sched=(entry/'schedstat').read_text().split()
   rows[key]={'runtime_ns':int(sched[0]),'comm':(entry/'comm').read_text().strip(),'state':fields[0]}
  except (OSError,ValueError,IndexError):continue
 return rows
def run_child(mode,rep,expected):
 env=os.environ.copy();env.update(OZMA_NO_LLM='1',OZMA_SEED_PERSIST_DISABLED='1',
  PYTHONPATH=f"{ROOT}:{ROOT/'runners/dsl/python'}:{ROOT/'evaluation/substrate_capability'}")
 if mode=='one_thread':env['RAYON_NUM_THREADS']='1'
 else:env.pop('RAYON_NUM_THREADS',None)
 with tempfile.TemporaryDirectory(prefix='ocelot-thread-cpu-') as td:
  marker=Path(td)/'markers.jsonl';env['OZMA_THREAD_CPU_MARKER']=str(marker)
  with tempfile.TemporaryFile(mode='w+t') as out,tempfile.TemporaryFile(mode='w+t') as err:
   proc=subprocess.Popen([sys.executable,str(RUNNER),'--worker',mode,str(rep)],cwd=ROOT,env=env,text=True,stdout=out,stderr=err)
   samples=[];began=False;ended=False
   while proc.poll() is None:
    marks=read_marker(marker)
    if any(m['phase']=='begin' for m in marks):began=True
    if began and not ended:
     ts=time.monotonic_ns();samples.append({'monotonic_ns':ts,'threads':snapshot(proc.pid)})
    if any(m['phase']=='end' for m in marks):ended=True
    time.sleep(SAMPLE_NS/1e9)
   out.seek(0);stdout=out.read();err.seek(0);stderr=err.read()
  if proc.returncode:raise RuntimeError(f'{mode}/{rep}: {stderr[-2500:]}')
  row=json.loads(stdout.splitlines()[-1]);marks=read_marker(marker)
 if [m['phase'] for m in marks]!=['begin','end']:raise RuntimeError(f'{mode}/{rep}: invalid target markers {marks}')
 begin,end=(m['monotonic_ns'] for m in marks)
 inside=[s for s in samples if begin<=s['monotonic_ns']<=end]
 ranges={};names={}
 for sample in inside:
  for key,v in sample['threads'].items():
   bounds=ranges.setdefault(key,[v['runtime_ns'],v['runtime_ns']]);bounds[0]=min(bounds[0],v['runtime_ns']);bounds[1]=max(bounds[1],v['runtime_ns'])
   names[key]={'comm':v['comm'],'state':v['state']}
 threads=[{'tid':k[0],'starttime_ticks':k[1],'comm':names[k]['comm'],'sampled_runtime_delta_ns':max(0,b[1]-b[0])} for k,b in ranges.items()]
 threads.sort(key=lambda x:x['sampled_runtime_delta_ns'],reverse=True)
 return {'mode':mode,'rep':rep,'caller_worker':row,'thread_cpu':{'sample_count':len(inside),'sample_interval_ms':SAMPLE_NS/1e6,
  'target_interval_ns':end-begin,'unique_thread_instances':len(threads),'sampled_thread_runtime_sum_ns':sum(t['sampled_runtime_delta_ns'] for t in threads),
  'threads':threads}}
def main():
 if sys.argv[1:2]==['--worker']:
  lock=json.loads(LOCK.read_text());print(json.dumps(worker(sys.argv[2],int(sys.argv[3]),lock['sources']['caller_runtime_lock']),sort_keys=True));return
 if sys.argv[1:]==['--lock']:
  if LOCK.exists() or RAW.exists():raise SystemExit('refusing to overwrite lock or raw capture')
  LOCK.write_text(json.dumps({'schema':'WarmConverseThreadCpuV2Lock','sources':frozen(),'schedule':SCHEDULE,'sample_interval_ms':2.0},indent=2,sort_keys=True)+'\n')
  print(LOCK.relative_to(ROOT));return
 lock=json.loads(LOCK.read_text())
 if lock['sources']!=frozen():raise SystemExit('source lock drift')
 if RAW.exists():raise SystemExit('capture exists; refusing overwrite')
 before=frozen();rows=[]
 for mode,rep in SCHEDULE:
  row=run_child(mode,rep,lock['sources']);rows.append(row);t=row['thread_cpu'];cpu=row['caller_worker']['worker']['timing_ns']['target_cpu']
  print(json.dumps({'mode':mode,'rep':rep,'samples':t['sample_count'],'threads':t['unique_thread_instances'],
   'sampled_thread_cpu_ms':round(t['sampled_thread_runtime_sum_ns']/1e6,1),'process_cpu_ms':round(cpu/1e6,1)}),flush=True)
 after=frozen();capture={'schema':'WarmConverseThreadCpuV2Capture','lock':lock,'source_before':before,'source_after':after,
  'source_stable':before==after,'host':platform.platform(),'logical_cpus':os.cpu_count(),'rows':rows}
 RAW.write_text(json.dumps(capture,indent=2,sort_keys=True)+'\n')
 print(json.dumps({'workers':len(rows),'source_stable':capture['source_stable'],'raw':str(RAW.relative_to(ROOT))}))
if __name__=='__main__':main()

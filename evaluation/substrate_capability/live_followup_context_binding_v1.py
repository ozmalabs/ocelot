#!/usr/bin/env python3
"""Capture matched live follow-up contexts and final graph identity."""
from __future__ import annotations
import gzip,hashlib,importlib.util,json,os,platform,resource,subprocess,sys,tempfile,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python')]
PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_LIVE_FOLLOWUP_CONTEXT_BINDING_V1_PREREG_20261003.md'
LOCK=ROOT/'evaluation/substrate_capability/live_followup_context_binding_v1_lock_20261003.json'
OUT=ROOT/'evaluation/reports/live_followup_context_binding_v1_20261003.jsonl.gz'
PROVENANCE=ROOT/'scripts/substrate_seed_rule_provenance_live_capture_v1.py'
ANALYZER=ROOT/'evaluation/substrate_capability/analyze_live_followup_context_binding_v1.py'
FOLLOWUP=('Can you explain that in simpler terms?','question')
ARMS={'known_answer':[('How are you organised?','question'),FOLLOWUP], 'unknown_fact':[('What part of your organisation is most important?','question'),FOLLOWUP], 'fresh_control':[FOLLOWUP]}
REPS=(0,1,2)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def inputs():
 spec=importlib.util.spec_from_file_location('seed_provenance',PROVENANCE);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 return {'protocol_sha256':sha(PROTOCOL),'runner_sha256':sha(__file__),'analyzer_sha256':sha(ANALYZER),'runtime_inputs':m.inputs()}
def gd(g):return hashlib.sha256(json.dumps(g,sort_keys=True,separators=(',',':'),default=str).encode()).hexdigest()
def worker(arm,rep):
 before=inputs()
 from substrate.world_adapter import WorldAdapter
 from substrate.boot_all import load_all_seeds
 import domains.conversation_action as ca
 a=WorldAdapter(seeds=());bt=time.perf_counter_ns();bc=time.process_time_ns();boot=load_all_seeds(a);boot_wall=time.perf_counter_ns()-bt;boot_cpu=time.process_time_ns()-bc
 try:a.set_self_teacher(lambda q:'teacher')
 except Exception:pass
 original=ca.act_on_instruction;actions=[]
 def wrap(agent,comp,inbound=None):
  out=original(agent,comp,inbound);actions.append({k:out.get(k) for k in ('route','goal_kind','reply','concern')});return out
 ca.act_on_instruction=wrap;known_m=set();known_g=set();turns=[]
 try:
  for i,(prompt,speech) in enumerate(ARMS[arm]):
   ai=len(actions);t=time.perf_counter_ns();cpu=time.process_time_ns();reply=str(a.converse(prompt,speech_act=speech,speaker='alice'));wall=time.perf_counter_ns()-t;pcpu=time.process_time_ns()-cpu
   g=a.inner.graph_to_dict();nodes={int(x['id']):x for x in g['nodes']};msgs={k for k,x in nodes.items() if x['type']=='Message' and x.get('attrs',{}).get('from')=='interlocutor' and x.get('attrs',{}).get('text')==prompt};goals={k for k,x in nodes.items() if x['type']=='Goal'};nm=sorted(msgs-known_m);ng=sorted(goals-known_g)
   turns.append({'index':i,'prompt':prompt,'speech_act':speech,'reply':reply,'wall_ns':wall,'process_cpu_ns':pcpu,'new_inbound_message_ids':nm,'new_goal_summaries':[{'id':k,'kind':nodes[k].get('attrs',{}).get('kind'),'status':nodes[k].get('attrs',{}).get('lifecycle_status',nodes[k].get('attrs',{}).get('status'))} for k in ng],'action_results':actions[ai:]})
   known_m.update(msgs);known_g.update(goals)
 finally:ca.act_on_instruction=original
 graph=a.inner.graph_to_dict();post=inputs()
 return {'condition':arm,'replicate':rep,'pid':os.getpid(),'turns':turns,'final_graph':graph,'final_graph_digest':gd(graph),'graph_nodes':len(graph['nodes']),'graph_edges':len(graph['edges']),'boot_loaded':boot.get('loaded'),'boot_failures':len(boot.get('failed',[])),'boot_wall_ns':boot_wall,'boot_process_cpu_ns':boot_cpu,'peak_rss_bytes':int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024),'source_stable':before==post,'locked_inputs':before,'post_run_inputs':post,'environment':{'python':sys.version,'platform':platform.platform()}}
def main():
 if sys.argv[1:]==['--lock']:
  if OUT.exists():raise SystemExit('refusing to overwrite capture')
  LOCK.write_text(json.dumps({'schema':'LiveFollowupContextBindingV1Lock','locked_inputs':inputs()},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return
 if len(sys.argv)==4 and sys.argv[1]=='--worker':print(json.dumps(worker(sys.argv[2],int(sys.argv[3])),sort_keys=True,separators=(',',':')));return
 locked=inputs()
 if not LOCK.exists() or json.loads(LOCK.read_text()).get('locked_inputs')!=locked:raise SystemExit('missing or stale lock')
 partial=OUT.with_suffix(OUT.suffix+'.partial');status=[];start=time.perf_counter_ns()
 with partial.open('wb') as raw:
  with gzip.GzipFile(fileobj=raw,mode='wb',compresslevel=1,mtime=0) as gz:
   def emit(x):gz.write(json.dumps(x,sort_keys=True,separators=(',',':')).encode()+b'\n')
   emit({'record_type':'header','schema':'LiveFollowupContextBindingV1','locked_inputs':locked,'arms':ARMS,'replicates':REPS,'claim_boundary':'Nine workers, two prior-answer contexts and a fresh-turn control, one fixed follow-up only.'})
   for arm in ARMS:
    for rep in REPS:
     with tempfile.TemporaryFile(mode='w+b') as out:
      p=subprocess.run([sys.executable,str(Path(__file__).resolve()),'--worker',arm,str(rep)],cwd=ROOT,stdout=out,stderr=subprocess.DEVNULL,timeout=300)
      status.append({'condition':arm,'replicate':rep,'returncode':p.returncode,'output_bytes':out.tell()})
      if out.tell():
       out.seek(0)
       while True:
        b=out.read(1024*1024)
        if not b:break
        gz.write(b)
      print(f'completed={arm}/{rep} rc={p.returncode}',file=sys.stderr,flush=True)
   post=inputs();checks={'nine_workers':len(status)==9,'all_workers_zero':all(x['returncode']==0 for x in status),'all_records':all(x['output_bytes']>0 for x in status),'source_stable':post==locked}
   emit({'record_type':'footer','post_run_inputs':post,'checks':checks,'run_status':status,'elapsed_ns':time.perf_counter_ns()-start})
 partial.replace(OUT);print(json.dumps({'capture':OUT.relative_to(ROOT).as_posix(),'checks':checks},indent=2))
 if not all(checks.values()):raise SystemExit('capture integrity gate failed')
if __name__=='__main__':main()

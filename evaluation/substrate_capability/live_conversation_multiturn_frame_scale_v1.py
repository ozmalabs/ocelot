#!/usr/bin/env python3
"""Source-locked multi-turn live task-frame scaling capture."""
from __future__ import annotations
import gzip,hashlib,importlib.util,json,os,platform,resource,subprocess,sys,tempfile,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python')]
PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_LIVE_CONVERSATION_MULTITURN_FRAME_SCALE_V1_PREREG_20261003.md'
LOCK=ROOT/'evaluation/substrate_capability/live_conversation_multiturn_frame_scale_v1_lock_20261003.json'
OUT=ROOT/'evaluation/reports/live_conversation_multiturn_frame_scale_v1_20261003.jsonl.gz'
PROVENANCE=ROOT/'scripts/substrate_seed_rule_provenance_live_capture_v1.py'
ANALYZER=ROOT/'evaluation/substrate_capability/analyze_live_conversation_multiturn_frame_scale_v1.py'
PROMPT='report your organisation';SIZES=(1,2,4,8);REPLICATES=(0,1,2)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def inputs():
 spec=importlib.util.spec_from_file_location('seed_provenance',PROVENANCE);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 return {'protocol_sha256':sha(PROTOCOL),'runner_sha256':sha(__file__),'analyzer_sha256':sha(ANALYZER),'runtime_inputs':m.inputs()}
def nid(x):return int(x.value if hasattr(x,'value') else x)
def graph_digest(graph):return hashlib.sha256(json.dumps(graph,sort_keys=True,separators=(',',':'),default=str).encode()).hexdigest()
def worker(n,rep):
 before=inputs()
 from substrate.world_adapter import WorldAdapter
 from substrate.boot_all import load_all_seeds
 import domains.conversation_action as ca
 a=WorldAdapter(seeds=());boot_start=time.perf_counter_ns();boot_cpu_start=time.process_time_ns();boot=load_all_seeds(a);boot_wall=time.perf_counter_ns()-boot_start;boot_cpu=time.process_time_ns()-boot_cpu_start
 try:a.set_self_teacher(lambda q:('teacher'))
 except Exception:pass
 original=ca.act_on_instruction;actions=[]
 def wrap(agent,comp,inbound=None):
  out=original(agent,comp,inbound);actions.append({k:out.get(k) for k in ('route','goal_kind','reply','concern')});return out
 ca.act_on_instruction=wrap
 turns=[];initial=a.inner.graph_to_dict();known_messages={int(x['id']) for x in initial['nodes'] if x['type']=='Message'};known_goals={int(x['id']) for x in initial['nodes'] if x['type']=='Goal'}
 try:
  for i in range(n):
   prior_actions=len(actions);t=time.perf_counter_ns();c=time.process_time_ns()
   reply=str(a.converse(PROMPT,speech_act='statement',speaker='alice'))
   wall=time.perf_counter_ns()-t;cpu=time.process_time_ns()-c
   graph=a.inner.graph_to_dict();nodes={int(x['id']):x for x in graph['nodes']}
   messages={j for j,x in nodes.items() if x['type']=='Message' and x.get('attrs',{}).get('from')=='interlocutor' and x.get('attrs',{}).get('text')==PROMPT}
   goals={j for j,x in nodes.items() if x['type']=='Goal'}
   new_messages=sorted(messages-known_messages);new_goals=sorted(goals-known_goals)
   turns.append({'index':i,'reply':reply,'wall_ns':wall,'process_cpu_ns':cpu,'new_inbound_message_ids':new_messages,
    'new_goal_summaries':[{'id':j,'kind':nodes[j].get('attrs',{}).get('kind'),'status':nodes[j].get('attrs',{}).get('lifecycle_status',nodes[j].get('attrs',{}).get('status'))} for j in new_goals],
    'action_results':actions[prior_actions:]})
   known_messages.update(messages);known_goals.update(goals)
 finally:ca.act_on_instruction=original
 graph=a.inner.graph_to_dict();post=inputs()
 return {'n_turns':n,'replicate':rep,'pid':os.getpid(),'prompt':PROMPT,'turns':turns,'final_graph':graph,'final_graph_digest':graph_digest(graph),
  'graph_nodes':len(graph['nodes']),'graph_edges':len(graph['edges']),'boot_loaded':boot.get('loaded'),'boot_failures':len(boot.get('failed',[])),
  'boot_wall_ns':boot_wall,'boot_process_cpu_ns':boot_cpu,'peak_rss_bytes':int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024),
  'source_stable':before==post,'locked_inputs':before,'post_run_inputs':post,'environment':{'python':sys.version,'platform':platform.platform()}}
def main():
 if sys.argv[1:]==['--lock']:
  if OUT.exists():raise SystemExit('refusing to overwrite capture')
  locked=inputs();LOCK.write_text(json.dumps({'schema':'LiveConversationMultiturnFrameScaleV1Lock','locked_inputs':locked},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return
 if len(sys.argv)==4 and sys.argv[1]=='--worker':print(json.dumps(worker(int(sys.argv[2]),int(sys.argv[3])),sort_keys=True,separators=(',',':')));return
 locked=inputs()
 if not LOCK.exists() or json.loads(LOCK.read_text()).get('locked_inputs')!=locked:raise SystemExit('missing or stale source lock')
 partial=OUT.with_suffix(OUT.suffix+'.partial');statuses=[];started=time.perf_counter_ns()
 with partial.open('wb') as raw:
  with gzip.GzipFile(fileobj=raw,mode='wb',compresslevel=1,mtime=0) as gz:
   def emit(obj):gz.write(json.dumps(obj,sort_keys=True,separators=(',',':')).encode()+b'\n')
   emit({'record_type':'header','schema':'LiveConversationMultiturnFrameScaleV1','locked_inputs':locked,'sizes':SIZES,'replicates':REPLICATES,'prompt':PROMPT,
    'claim_boundary':'Source-locked repeated live self-report route, N=1/2/4/8, with explicit graph-identity ownership. One authored repeated task family only.'})
   for n in SIZES:
    for rep in REPLICATES:
     with tempfile.TemporaryFile(mode='w+b') as output:
      p=subprocess.run([sys.executable,str(Path(__file__).resolve()),'--worker',str(n),str(rep)],cwd=ROOT,stdout=output,stderr=subprocess.DEVNULL,timeout=300)
      statuses.append({'n_turns':n,'replicate':rep,'returncode':p.returncode,'output_bytes':output.tell()})
      if output.tell():
       output.seek(0)
       while True:
        chunk=output.read(1024*1024)
        if not chunk:break
        gz.write(chunk)
      print(f'completed=n{n}/rep{rep} rc={p.returncode}',file=sys.stderr,flush=True)
   post=inputs();checks={'twelve_workers':len(statuses)==12,'all_workers_zero':all(x['returncode']==0 for x in statuses),'all_worker_records':all(x['output_bytes']>0 for x in statuses),'source_stable':post==locked}
   emit({'record_type':'footer','post_run_inputs':post,'checks':checks,'run_status':statuses,'elapsed_ns':time.perf_counter_ns()-started})
 partial.replace(OUT);print(json.dumps({'capture':OUT.relative_to(ROOT).as_posix(),'checks':checks},indent=2))
 if not all(checks.values()):raise SystemExit('capture integrity gate failed')
if __name__=='__main__':main()

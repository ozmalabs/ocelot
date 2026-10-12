#!/usr/bin/env python3
"""Capture graph-native episodic binding and exact/negative-cue retrieval."""
from __future__ import annotations
import gzip,hashlib,importlib.util,json,os,platform,resource,subprocess,sys,tempfile,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python')]
PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_STRUCTURED_EPISODIC_RECALL_V1_PREREG_20261003.md'
LOCK=ROOT/'evaluation/substrate_capability/structured_episodic_recall_v1_lock_20261003.json'
OUT=ROOT/'evaluation/reports/structured_episodic_recall_v1_20261003.jsonl.gz'
PROVENANCE=ROOT/'scripts/substrate_seed_rule_provenance_live_capture_v1.py'
ANALYZER=ROOT/'evaluation/substrate_capability/analyze_structured_episodic_recall_v1.py'
ARMS={'known_14':{'event_key':'code-14','summary':'secret code is 14','cue':'secret-code','expected':'secret code is 14'},'known_29':{'event_key':'code-29','summary':'secret code is 29','cue':'secret-code','expected':'secret code is 29'},'unknown_cue':{'event_key':'code-14','summary':'secret code is 14','cue':'never-seen','expected':None}};REPS=(0,1,2)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def inputs():
 spec=importlib.util.spec_from_file_location('seed_provenance',PROVENANCE);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 return {'protocol_sha256':sha(PROTOCOL),'runner_sha256':sha(__file__),'analyzer_sha256':sha(ANALYZER),'episodic_seed_sha256':sha(ROOT/'seeds/episodic_working_memory_core.json'),'runtime_inputs':m.inputs()}
def gd(g):return hashlib.sha256(json.dumps(g,sort_keys=True,separators=(',',':'),default=str).encode()).hexdigest()
def edge(a,src,kind,tgt):
 try:a.inner.add_edge_unchecked(src,kind,tgt,{})
 except TypeError:a.inner.add_edge_unchecked(src,kind,tgt)
def attrs(a,n):return a.s.node(n)['attrs']
def nodes(a,typ):return [n for n in a.s.nodes() if a.s.node(n)['type']==typ]
def worker(arm,rep):
 before=inputs();from substrate.world_adapter import WorldAdapter
 a=WorldAdapter(seeds=('episodic_working_memory_core',));cfg=ARMS[arm]
 ctx=a.s.add_node('MemoryContext',{'context_key':'test-context'});schema=a.s.add_node('MemorySchema',{'name':'secret_code_schema'})
 ev=a.s.add_node('EpisodicEvent',{'event_key':cfg['event_key'],'cue_key':'secret-code','epoch':1.0,'salience':0.8,'surprise':0.5,'value':0.5,'observation_status':'observed','provenance_kind':'perceived','state_kind':'fact','state_summary':cfg['summary']})
 edge(a,a.agent,'experienced_event',ev);edge(a,ev,'in_context',ctx);edge(a,ev,'instantiates_schema',schema)
 bind_ticks=[];t=time.perf_counter_ns();cpu=time.process_time_ns();bind_ticks.append(a.tick());bind_wall=time.perf_counter_ns()-t;bind_cpu=time.process_time_ns()-cpu
 req=a.s.add_node('MemoryRetrievalRequest',{'status':'pending','cue_key':cfg['cue'],'epoch':4.0});edge(a,a.agent,'has_memory_retrieval_request',req)
 t=time.perf_counter_ns();cpu=time.process_time_ns();retrieve_fires=a.tick();retrieve_wall=time.perf_counter_ns()-t;retrieve_cpu=time.process_time_ns()-cpu
 graph=a.inner.graph_to_dict();post=inputs()
 return {'condition':arm,'replicate':rep,'pid':os.getpid(),'expected_summary':cfg['expected'],'event_id':int(ev.value),'context_id':int(ctx.value),'schema_id':int(schema.value),'request_id':int(req.value),'bind_tick_fires':bind_ticks,'retrieve_tick_fires':retrieve_fires,'bind_wall_ns':bind_wall,'bind_process_cpu_ns':bind_cpu,'retrieve_wall_ns':retrieve_wall,'retrieve_process_cpu_ns':retrieve_cpu,'episodes':[{ 'id':int(n.value),'attrs':attrs(a,n)} for n in nodes(a,'Episode')],'recalls':[{'id':int(n.value),'attrs':attrs(a,n),'reconstructs_event':[int(x.value) for x in a.inner.neighbours(n,'reconstructs_event')],'recalls_episode':[int(x.value) for x in a.inner.neighbours(n,'recalls_episode')]} for n in nodes(a,'RecallCandidate')],'outcomes':[{'id':int(n.value),'attrs':attrs(a,n)} for n in nodes(a,'RecallOutcome')],'final_graph':graph,'final_graph_digest':gd(graph),'graph_nodes':len(graph['nodes']),'graph_edges':len(graph['edges']),'peak_rss_bytes':int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024),'source_stable':before==post,'locked_inputs':before,'post_run_inputs':post,'environment':{'python':sys.version,'platform':platform.platform()}}
def main():
 if sys.argv[1:]==['--lock']:
  if OUT.exists():raise SystemExit('refusing to overwrite capture')
  LOCK.write_text(json.dumps({'schema':'StructuredEpisodicRecallV1Lock','locked_inputs':inputs()},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return
 if len(sys.argv)==4 and sys.argv[1]=='--worker':print(json.dumps(worker(sys.argv[2],int(sys.argv[3])),sort_keys=True,separators=(',',':')));return
 locked=inputs()
 if not LOCK.exists() or json.loads(LOCK.read_text()).get('locked_inputs')!=locked:raise SystemExit('missing or stale source lock')
 partial=OUT.with_suffix(OUT.suffix+'.partial');status=[];start=time.perf_counter_ns()
 with partial.open('wb') as raw:
  with gzip.GzipFile(fileobj=raw,mode='wb',compresslevel=1,mtime=0) as gz:
   def emit(x):gz.write(json.dumps(x,sort_keys=True,separators=(',',':')).encode()+b'\n')
   emit({'record_type':'header','schema':'StructuredEpisodicRecallV1','locked_inputs':locked,'arms':ARMS,'replicates':REPS,'claim_boundary':'Direct graph-native episodic memory with explicit event/context/schema inputs; not conversational integration.'})
   for arm in ARMS:
    for rep in REPS:
     with tempfile.TemporaryFile(mode='w+b') as out:
      p=subprocess.run([sys.executable,str(Path(__file__).resolve()),'--worker',arm,str(rep)],cwd=ROOT,stdout=out,stderr=subprocess.DEVNULL,timeout=180)
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
 if not all(checks.values()):raise SystemExit('integrity gate failed')
if __name__=='__main__':main()

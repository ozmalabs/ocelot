#!/usr/bin/env python3
"""Cross-audit source-locked conversational and structured memory captures."""
import gzip,hashlib,json
from collections import Counter,defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
LIVE=ROOT/'evaluation/reports/live_counterbalanced_value_recall_v1_20261003.jsonl.gz'
STRUCT=ROOT/'evaluation/reports/structured_episodic_recall_v1_20261003.jsonl.gz'
OUT=ROOT/'evaluation/reports/live_structured_memory_boundary_v1_audit_20261003.json'
MEM_TYPES=('EpisodicEvent','MemoryContext','MemorySchema','MemoryRetrievalRequest','Episode','RecallCandidate','RecallOutcome')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def gd(g):return hashlib.sha256(json.dumps(g,sort_keys=True,separators=(',',':'),default=str).encode()).hexdigest()
def nid(x):
 if isinstance(x,dict) and set(x)=={'__nid__'}:return int(x['__nid__'])
 if isinstance(x,int):return x
 return None
def load(path):
 with gzip.open(path,'rt') as f:
  h=json.loads(next(f));rows=[];footer=None
  for line in f:
   x=json.loads(line)
   if x.get('record_type')=='footer':footer=x
   else:rows.append(x)
 return h,rows,footer
def main():
 lh,live,lf=load(LIVE);sh,structured,sf=load(STRUCT);errors=[]
 if not lf or not all(lf.get('checks',{}).values()):errors.append('live capture footer gate failure')
 if not sf or not all(sf.get('checks',{}).values()):errors.append('structured capture footer gate failure')
 if lf and lf.get('post_run_inputs')!=lh.get('locked_inputs'):errors.append('live parent footer source lock mismatch')
 if sf and sf.get('post_run_inputs')!=sh.get('locked_inputs'):errors.append('structured parent footer source lock mismatch')
 live_rows=[]
 for r in live:
  g=r.get('final_graph',{});nodes={int(n['id']):n for n in g.get('nodes',[])};counts=Counter(n['type'] for n in nodes.values())
  if r.get('final_graph_digest')!=gd(g):errors.append(f"live digest invalid {r.get('condition')}/{r.get('replicate')}")
  if r.get('locked_inputs')!=lh.get('locked_inputs') or r.get('post_run_inputs')!=lh.get('locked_inputs') or not r.get('source_stable'):errors.append(f"live source mismatch {r.get('condition')}/{r.get('replicate')}")
  interp_rows=[]
  for mid,n in nodes.items():
   a=n.get('attrs',{})
   if n.get('type')!='Message' or a.get('from')!='interlocutor':continue
   iid=nid(a.get('communication_interpretation_id'));ia=nodes.get(iid,{}).get('attrs',{}) if iid is not None else {}
   interp_rows.append({'text':a.get('text'),'kind':ia.get('kind'),'intent':ia.get('intent'),'cognitive_goal':ia.get('cognitive_goal'),'dispatch_path':ia.get('dispatch_path'),'parsed_subject':ia.get('parsed_subject'),'parsed_predicate':ia.get('parsed_predicate'),'parsed_object':ia.get('parsed_object'),'relation_support':ia.get('relation_support'),'grounding_status':ia.get('grounding_status'),'gap_count':ia.get('gap_count')})
  for typ in ('EpisodicEvent','MemoryContext','MemorySchema','MemoryRetrievalRequest','RecallCandidate','RecallOutcome'):
   if counts[typ]!=0:errors.append(f"unexpected {typ} in live conversational worker {r.get('condition')}/{r.get('replicate')}")
  legacy=[n for n in nodes.values() if n.get('type')=='Episode']
  live_rows.append({'condition':r['condition'],'replicate':r['replicate'],'graph_digest':r['final_graph_digest'],'graph_nodes':len(nodes),'graph_edges':len(g.get('edges',[])),'memory_node_counts':{k:counts[k] for k in MEM_TYPES},'episode_architectures':dict(Counter(n.get('attrs',{}).get('memory_architecture','<missing>') for n in legacy)),'turn_interpretations':interp_rows,'reply_surfaces':[t.get('reply') for t in r.get('turns',[])]})
 structured_rows=[]
 for r in structured:
  g=r.get('final_graph',{});counts=Counter(n['type'] for n in g.get('nodes',[]))
  if r.get('final_graph_digest')!=gd(g):errors.append(f"structured digest invalid {r.get('condition')}/{r.get('replicate')}")
  if r.get('locked_inputs')!=sh.get('locked_inputs') or r.get('post_run_inputs')!=sh.get('locked_inputs') or not r.get('source_stable'):errors.append(f"structured source mismatch {r.get('condition')}/{r.get('replicate')}")
  structured_rows.append({'condition':r['condition'],'replicate':r['replicate'],'graph_digest':r['final_graph_digest'],'memory_node_counts':{k:counts[k] for k in MEM_TYPES},'task_retrieval_results':{'episodes':len(r.get('episodes',[])),'recalls':len(r.get('recalls',[])),'outcomes':len(r.get('outcomes',[]))}})
 # The plain-statement source interpretation should preserve the asserted number,
 # while still showing whether it was grounded as a memory event.
 assertions=[it for row in live_rows for it in row['turn_interpretations'] if it.get('text') in ('My secret code is 14.','My secret code is 29.')]
 questions=[it for row in live_rows for it in row['turn_interpretations'] if it.get('text')=='What is my secret code?']
 ac=Counter((x.get('parsed_subject'),x.get('parsed_predicate'),x.get('parsed_object'),x.get('relation_support'),x.get('grounding_status')) for x in assertions)
 qc=Counter((x.get('kind'),x.get('intent'),x.get('dispatch_path'),x.get('grounding_status'),x.get('gap_count')) for x in questions)
 out={'schema':'LiveStructuredMemoryBoundaryV1Audit','passed':not errors,'errors':errors,'capture_sha256':{'live':sha(LIVE),'structured':sha(STRUCT)},'source_locks':{'live':lh.get('locked_inputs'),'structured':sh.get('locked_inputs')},'live_worker_count':len(live_rows),'structured_worker_count':len(structured_rows),'live_memory_node_totals':{k:sum(r['memory_node_counts'][k] for r in live_rows) for k in MEM_TYPES},'structured_memory_node_totals':{k:sum(r['memory_node_counts'][k] for r in structured_rows) for k in MEM_TYPES},'assertion_interpretation_counts':[{'parsed_subject':k[0],'parsed_predicate':k[1],'parsed_object':k[2],'relation_support':k[3],'grounding_status':k[4],'count':v} for k,v in ac.items()],'question_interpretation_counts':[{'kind':k[0],'intent':k[1],'dispatch_path':k[2],'grounding_status':k[3],'gap_count':k[4],'count':v} for k,v in qc.items()],'live_rows':live_rows,'structured_rows':structured_rows,'interpretation':'Live `converse` captures show whether ordinary natural-language statements/question ever instantiate the measured structured episodic memory schema. Structured memory workers explicitly supply that schema and execute binding/retrieval through graph ticks. These interfaces are measured separately; no causal equivalence is assumed.'}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps({'passed':out['passed'],'errors':errors,'live_memory_node_totals':out['live_memory_node_totals'],'structured_memory_node_totals':out['structured_memory_node_totals'],'assertion_interpretation_counts':out['assertion_interpretation_counts'],'question_interpretation_counts':out['question_interpretation_counts']},indent=2));return int(bool(errors))
if __name__=='__main__':raise SystemExit(main())

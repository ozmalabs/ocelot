#!/usr/bin/env python3
"""Independent exact behavioral and provenance gates for episodic recall."""
import gzip,hashlib,json,statistics
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];LOCK=ROOT/'evaluation/substrate_capability/structured_episodic_recall_v1_lock_20261003.json';CAP=ROOT/'evaluation/reports/structured_episodic_recall_v1_20261003.jsonl.gz';OUT=ROOT/'evaluation/reports/structured_episodic_recall_v1_analysis_20261003.json'
EXPECTED={'known_14':('code-14','secret code is 14','secret code is 14'),'known_29':('code-29','secret code is 29','secret code is 29'),'unknown_cue':('code-14','secret code is 14',None)}
def graph_digest(g):return hashlib.sha256(json.dumps(g,sort_keys=True,separators=(',',':'),default=str).encode()).hexdigest()
def main():
 lock=json.loads(LOCK.read_text())['locked_inputs'];errs=[];rows=[];by=defaultdict(list);pids=set();footer=None;header=None
 def req(ok,msg):
  if not ok:errs.append(msg)
 with gzip.open(CAP,'rt') as f:
  header=json.loads(next(f));req(header.get('locked_inputs')==lock,'header source lock mismatch')
  for line in f:
   x=json.loads(line)
   if x.get('record_type')=='footer':footer=x;continue
   arm=x.get('condition');rep=x.get('replicate');req(arm in EXPECTED and rep in (0,1,2),'unexpected worker');pids.add(x.get('pid'));req(x.get('source_stable') is True and x.get('locked_inputs')==lock==x.get('post_run_inputs'),'worker source mismatch')
   key,summary,want=EXPECTED.get(arm,(None,None,None));g=x.get('final_graph',{});req(x.get('final_graph_digest')==graph_digest(g),'invalid graph digest');ns={int(n['id']):n for n in g.get('nodes',[])};es=g.get('edges',[])
   episodes=x.get('episodes',[]);recalls=x.get('recalls',[]);outcomes=x.get('outcomes',[]);event=int(x.get('event_id',-1));ctx=int(x.get('context_id',-1));schema=int(x.get('schema_id',-1));req(len(episodes)==1,'expected one bound episode')
   ep=episodes[0] if episodes else {};ea=ep.get('attrs',{});eid=int(ep.get('id',-2))
   def hasedge(a,typ,b):return any(int(e['src'])==a and e['type']==typ and int(e['tgt'])==b for e in es)
   binding=(ea.get('episode_key')==key and ea.get('context_key')=='test-context' and ea.get('provenance_kind')=='episodic_trace' and ea.get('observation_status')=='not_observed' and hasedge(eid,'bound_event',event) and hasedge(eid,'in_context',ctx) and hasedge(eid,'instantiates_schema',schema))
   if want is not None:
    retrieved=(len(recalls)==1 and recalls[0].get('attrs',{}).get('provenance_kind')=='recalled' and recalls[0].get('attrs',{}).get('observation_status')=='not_observed' and ns.get(event,{}).get('attrs',{}).get('state_summary')==want and recalls[0].get('reconstructs_event')==[event] and recalls[0].get('recalls_episode')==[eid] and len(outcomes)==0)
    success=binding and retrieved and int(x.get('bind_tick_fires',0)[0])>0 and int(x.get('retrieve_tick_fires',0))>0
   else:
    outcome_ok=(len(recalls)==0 and len(outcomes)==1 and outcomes[0].get('attrs',{}).get('status')=='insufficient_information' and float(outcomes[0].get('attrs',{}).get('uncertainty',0))==1.0 and outcomes[0].get('attrs',{}).get('observation_status')=='not_observed')
    success=binding and outcome_ok and int(x.get('bind_tick_fires',0)[0])>0 and int(x.get('retrieve_tick_fires',0))>0
   row={'condition':arm,'replicate':rep,'pid':x.get('pid'),'event_key':key,'expected_summary':want,'binding_gate':bool(binding),'retrieval_gate':bool(retrieved if want is not None else outcome_ok),'task_oracle_pass':bool(success),'episode_count':len(episodes),'recall_count':len(recalls),'outcome_count':len(outcomes),'episode_attrs':ea,'recall_attrs':recalls[0].get('attrs') if recalls else None,'outcome_attrs':outcomes[0].get('attrs') if outcomes else None,'bind_tick_fires':x.get('bind_tick_fires'),'retrieve_tick_fires':x.get('retrieve_tick_fires'),'bind_wall_ns':x.get('bind_wall_ns'),'retrieve_wall_ns':x.get('retrieve_wall_ns'),'graph_nodes':len(ns),'graph_edges':len(es),'graph_digest':x.get('final_graph_digest'),'peak_rss_bytes':x.get('peak_rss_bytes')}
   rows.append(row);by[arm].append(row)
 req(len(pids)==9,'expected nine distinct worker PIDs');req(footer is not None,'capture footer missing')
 if footer:req(footer.get('post_run_inputs')==lock and all(footer.get('checks',{}).values()),'runner footer integrity gate failed')
 summaries={}
 for arm in EXPECTED:
  grp=by[arm];req(len(grp)==3,f'{arm}: expected three workers')
  if len(grp)==3:req(len({r['graph_digest'] for r in grp})==1,f'{arm}: exact graph digest replicate mismatch')
  summaries[arm]={'workers':len(grp),'passes':sum(r['task_oracle_pass'] for r in grp),'pass_rate':sum(r['task_oracle_pass'] for r in grp)/len(grp) if grp else None,'median_nodes':statistics.median(r['graph_nodes'] for r in grp) if grp else None,'median_edges':statistics.median(r['graph_edges'] for r in grp) if grp else None,'median_bind_ms':statistics.median(r['bind_wall_ns'] for r in grp)/1e6 if grp else None,'median_retrieve_ms':statistics.median(r['retrieve_wall_ns'] for r in grp)/1e6 if grp else None,'median_peak_rss_mib':statistics.median(r['peak_rss_bytes'] for r in grp)/(1024**2) if grp else None}
 out={'schema':'StructuredEpisodicRecallV1Analysis','gates_pass':not errs,'errors':errs,'by_condition':summaries,'rows':rows,'claim_boundary':header.get('claim_boundary'),'provenance':'Behavior is caused by graph tick rules after explicit event/context/schema input; no Python retrieval implementation is used.'};OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps({'gates_pass':out['gates_pass'],'errors':errs,'by_condition':summaries},indent=2));return int(bool(errs))
if __name__=='__main__':raise SystemExit(main())

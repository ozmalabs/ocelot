#!/usr/bin/env python3
"""Independent outcome replay and cold/warmed cost summaries."""
import importlib.util,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
LOCK=ROOT/'evaluation/substrate_capability/substrate_adequacy_warm_converse_cost_v1_lock_20261002.json'; RAW=ROOT/'evaluation/reports/substrate_adequacy_warm_converse_cost_v1_raw_20261002.json'; OUT=ROOT/'evaluation/reports/substrate_adequacy_warm_converse_cost_v1_analysis_20261002.json'
def import_file(name,path):
 spec=importlib.util.spec_from_file_location(name,path); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod
def main():
 runner=import_file('warm_converse_runner',ROOT/'evaluation/substrate_capability/substrate_adequacy_warm_converse_cost_v1.py'); lock=json.loads(LOCK.read_text()); cap=json.loads(RAW.read_text()); rows=cap['workers']
 if runner.frozen()!=lock or cap['lock']!=lock or cap['post_lock']!=lock or not cap['source_stable']: raise SystemExit('source/native lock mismatch')
 from domains import independent_adequacy as ia
 from domains.adequacy_provider_auth import verify_signed_audit_evidence
 from independent_codewrite_oracles import label as oracle_label
 checks=[('18_unique_workers',len(rows)==18 and len({r['pid'] for r in rows})==18),('complete_grid',{(r['task'],r['condition'],r['rep']) for r in rows}=={(t,c,n) for t in runner.TASKS for c in runner.CONDITIONS for n in range(1,4)}),('source_stability',all(r['active_after']==lock['active'] for r in rows)),('positive_wall_and_cpu',all(r['warm_wall_ns']>0 and r['warm_cpu_ns']>0 and r['timing_ns']['target_wall']>0 and r['timing_ns']['target_cpu']>0 for r in rows))]
 receipt_checks=[]; auth_checks=[]; shape_checks=[]; heldout_checks=[]; groups={}
 for r in rows:
  task=r['task']; fixture=runner.FIXTURES[task]; condition=r['condition']; base_key=(task,condition); groups.setdefault('/'.join(base_key),[]).append(r)
  oracle_ok=all(x['expected']==oracle_label(task,x['inputs']) for x in r['heldout'])
  heldout_checks.append(oracle_ok and (condition!='truthful_adoption' or all(x['prediction']==x['expected'] for x in r['heldout'])))
  if condition=='truthful_adoption':
   req=r['request']; probe=req['probes'][0]; expected=oracle_label(task,probe['inputs']); labels=r['rows'][0]['labels']; cid=r['candidate_id']
   labels_ok=(len(labels)==1 and labels[0]['expected']==expected and labels[0]['oracle_sha256']==runner.sha(runner.ORACLE))
   term=r['term']; source_ids=[f'acquisition:{task}:warmed-v1']
   replay=ia.adjudicate_audit_receipt(req,cid,term,r['rows'],lambda _t,e:oracle_label(task,e),acquisition_source_ids=source_ids)
   receipt_checks.append(labels_ok and replay==r['receipt'] and r['receipt']['status']=='accepted')
   auth=verify_signed_audit_evidence(req,r['rows'],r['receipt'],{runner.PROVIDER:runner.KEY}); auth_checks.append(auth['ok'] and r['auth']['ok'])
   shape_checks.append(r['shape_delta']==1 and r['state_after']['epoch']==1 and len(r['state_after']['shapes'])==len(r['state_before']['shapes'])+1)
  else:
   receipt_checks.append(r['receipt'] is None and r['request'] is None); auth_checks.append(r['auth'] is None)
   shape_checks.append(r['shape_delta']==0 and r['state_after']==r['state_before'])
 checks += [('receipt_replay_or_expected_absence',all(receipt_checks)),('provider_authentication',all(auth_checks)),('adoption_and_refusal_shape_state',all(shape_checks)),('heldout_oracle_parity',all(heldout_checks))]
 cells={}
 for key,items in groups.items():
  cells[key]={'n':len(items),'median_ms':{'cold_first_converse_wall':statistics.median(r['warm_wall_ns'] for r in items)/1e6,'cold_first_converse_cpu':statistics.median(r['warm_cpu_ns'] for r in items)/1e6,'target_converse_wall':statistics.median(r['timing_ns']['target_wall'] for r in items)/1e6,'target_converse_cpu':statistics.median(r['timing_ns']['target_cpu'] for r in items)/1e6},'median_target_graph_counts':{'before_nodes':statistics.median(len(r['pre_call_graph']['nodes']) for r in items),'after_nodes':statistics.median(len(r['post_call_graph']['nodes']) for r in items),'before_edges':statistics.median(len(r['pre_call_graph']['edges']) for r in items),'after_edges':statistics.median(len(r['post_call_graph']['edges']) for r in items)}}
 result={'schema':'SubstrateAdequacyWarmConverseCostV1Analysis','checks':[{'name':n,'pass':v} for n,v in checks],'passed':sum(v for _,v in checks),'total':len(checks),'cells':cells,'limits':['one host, three authored codewrite task families, one test provider, three repetitions per cell','first converse is a controlled hello warm-up; second is the target task','target full-graph changes include normal per-turn writes and are descriptive','timings are descriptive and not confidence intervals','HMAC authenticates test labels but does not establish their truth']}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n'); print(json.dumps({'passed':result['passed'],'total':result['total'],'cells':len(cells),'analysis':str(OUT.relative_to(ROOT))},indent=2))
 if not all(v for _,v in checks): raise SystemExit(1)
if __name__=='__main__': main()

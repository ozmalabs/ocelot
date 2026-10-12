#!/usr/bin/env python3
"""Independent replay of cross-family authenticated adoption deltas."""
import importlib.util,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
LOCK=ROOT/'evaluation/substrate_capability/substrate_adequacy_adoption_boundary_v2_lock_20261002.json'; RAW=ROOT/'evaluation/reports/substrate_adequacy_adoption_boundary_v2_raw_20261002.json'; OUT=ROOT/'evaluation/reports/substrate_adequacy_adoption_boundary_v2_analysis_20261002.json'
def import_file(name,path):
 spec=importlib.util.spec_from_file_location(name,path); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod
def main():
 runner=import_file('adoption_boundary_v2_runner',ROOT/'evaluation/substrate_capability/substrate_adequacy_adoption_boundary_v2.py'); lock=json.loads(LOCK.read_text()); cap=json.loads(RAW.read_text()); rows=cap['workers']
 if runner.frozen()!=lock or cap['lock']!=lock or cap['post_lock']!=lock or not cap['source_stable']: raise SystemExit('source/native lock mismatch')
 from domains import independent_adequacy as ia
 from domains.adequacy_provider_auth import verify_signed_audit_evidence
 from independent_codewrite_oracles import label as oracle_label
 checks=[('nine_unique_workers',len(rows)==9 and len({r['pid'] for r in rows})==9),('complete_task_repetition_grid',{(r['task'],r['rep']) for r in rows}=={(t,n) for t in runner.TASKS for n in range(1,4)}),('worker_source_stability',all(r['active_after']==lock['active'] for r in rows))]
 receipt_ok=[]; auth_ok=[]; false_refusal=[]; exact_delta=[]; heldout_ok=[]; timings={}
 for r in rows:
  task=r['task']; fixture=runner.FIXTURES[task]; term=r['term']; cid=r['candidate_id']; req=r['request']; source_ids=[f'acquisition:{task}:v1']; probe=r['probe']; truth=oracle_label(task,probe['inputs'])
  receipt_pair=[]
  for which in ('correct','false'):
   receipt=r[f'{which}_receipt']; audit=r[f'{which}_rows']; expected=truth if which=='correct' else ((not truth) if isinstance(truth,bool) else truth+1)
   label_expected=all(l['expected']==expected and l['oracle_sha256']==runner.sha(runner.ORACLE) for group in audit for l in group['labels'])
   recomputed=ia.adjudicate_audit_receipt(req,cid,term,audit,lambda _t,e: (e['value']%2==0 if task=='parity' else (e['lower'] if e['value']<e['lower'] else e['upper'] if e['value']>e['upper'] else e['value']) if task=='clamp' else e['x']**2),acquisition_source_ids=source_ids)
   receipt_pair.append(label_expected and recomputed==receipt)
   auth=verify_signed_audit_evidence(req,audit,receipt,{runner.PROVIDER:runner.KEY}); auth_ok.append(auth['ok'])
  receipt_ok.append(all(receipt_pair))
  false_refusal.append(r['false_receipt']['status']=='rejected' and not r['rejected']['ok'] and not r['rejected_entered_adoption'] and r['reject_before']==r['reject_after'])
  b=r['boundary']['before']; a=r['boundary']['after']; bn={n['id']:n for n in b['nodes']}; an={n['id']:n for n in a['nodes']}; added=set(an)-set(bn); removed=set(bn)-set(an); changed={i for i in set(an)&set(bn) if an[i]!=bn[i]}
  be={json.dumps(e,sort_keys=True) for e in b['edges']}; ae={json.dumps(e,sort_keys=True) for e in a['edges']}; added_edges=[json.loads(x) for x in ae-be]; removed_edges=be-ae
  added_types=sorted(an[i]['type'] for i in added); agent_ok=False
  if len(changed)==1:
   old,new=bn[next(iter(changed))],an[next(iter(changed))]
   if old['type']==new['type']=='Agent':
    oa,na=old['attrs'],new['attrs']; agent_ok=(all(oa.get(k)==v for k,v in na.items() if k not in {'meta_codebook_epoch','write_codebook_epoch'}) and na.get('meta_codebook_epoch')==0 and na.get('write_codebook_epoch')==1)
  shape_nodes=[an[i] for i in added if an[i]['type']=='ShapeSignature']; obs_nodes=[an[i] for i in added if an[i]['type']=='ShapeObservation']
  delta=(not removed and not removed_edges and added_types==['ShapeObservation','ShapeSignature'] and agent_ok and len(shape_nodes)==len(obs_nodes)==1 and shape_nodes[0]['attrs'].get('kind')=='code_write_construction' and obs_nodes[0]['attrs'].get('status')=='pending' and all(e['src'] in added or e['tgt'] in added for e in added_edges) and a['next_id']==b['next_id']+2 and r['accepted']['ok'])
  exact_delta.append(delta); heldout_ok.append(all(x['prediction']==x['expected']==oracle_label(task,x['inputs']) for x in r['heldout']) and len(r['heldout'])==len(fixture['heldout']))
  timings.setdefault(task,[]).append(r['boundary']['elapsed_ns']/1e6)
 checks += [('independent_label_and_receipt_replay',all(receipt_ok)),('provider_authentication_replay',all(auth_ok)),('false_evidence_refusal',all(false_refusal)),('accepted_transaction_exact_graph_delta',all(exact_delta)),('native_heldout_matches_oracle',all(heldout_ok))]
 result={'schema':'SubstrateAdequacyAdoptionBoundaryV2Analysis','checks':[{'name':n,'pass':v} for n,v in checks],'passed':sum(v for _,v in checks),'total':len(checks),'median_adoption_boundary_ms_by_task':{k:statistics.median(v) for k,v in timings.items()},'limits':['one host, three authored tasks, one deterministic provider, three workers per task','isolates _teach_shape; not full-conversation cost','authentication does not certify label truth']}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n'); print(json.dumps({'passed':result['passed'],'total':result['total'],'analysis':str(OUT.relative_to(ROOT))},indent=2))
 if not all(v for _,v in checks): raise SystemExit(1)
if __name__=='__main__': main()

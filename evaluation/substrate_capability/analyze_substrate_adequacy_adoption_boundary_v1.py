#!/usr/bin/env python3
"""Independent replay of the authenticated adoption-boundary graph delta."""
import importlib.util,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
LOCK=ROOT/'evaluation/substrate_capability/substrate_adequacy_adoption_boundary_v1_lock_20261002.json'
RAW=ROOT/'evaluation/reports/substrate_adequacy_adoption_boundary_v1_raw_20261002.json'
OUT=ROOT/'evaluation/reports/substrate_adequacy_adoption_boundary_v1_analysis_20261002.json'
def import_file(name,path):
 spec=importlib.util.spec_from_file_location(name,path); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod
def main():
 runner=import_file('adoption_boundary_runner',ROOT/'evaluation/substrate_capability/substrate_adequacy_adoption_boundary_v1.py')
 lock=json.loads(LOCK.read_text()); capture=json.loads(RAW.read_text()); rows=capture['workers']
 if runner.frozen()!=lock or capture['lock']!=lock or capture['post_lock']!=lock or not capture['source_stable']: raise SystemExit('source/native lock mismatch')
 from domains import independent_adequacy as ia
 from domains.adequacy_provider_auth import verify_signed_audit_evidence
 from independent_adequacy_noise_oracles_v1 import label as oracle
 provider=runner.PROVIDER; keys={provider:runner.KEY}
 checks=[('three_fresh_unique_workers',len(rows)==3 and len({x['pid'] for x in rows})==3),('complete_repetition_schedule',{x['rep'] for x in rows}=={1,2,3}),('post_worker_source_stability',all(x['active_after']==lock['active'] for x in rows))]
 receipt_replay=[]; auth_replay=[]; rejected_control=[]; accepted_state=[]; deltas=[]
 for row in rows:
  cid=row['candidate_id']; req=row['request']; term={'type':'Times','items':[{'type':'Var','name':'x'},{'type':'Var','name':'x'}]}
  receipt_results=[]
  for key in ('good','bad'):
   receipt=row[f'{key}_receipt']; signed=row[f'{key}_rows']
   recomputed=ia.adjudicate_audit_receipt(req,cid,term,signed,lambda _t,e:e['x']*e['x'],acquisition_source_ids=['acquisition:square:v1'])
   receipt_results.append(recomputed==receipt)
   auth=verify_signed_audit_evidence(req,signed,receipt,keys)
   auth_replay.append(auth['ok'])
  receipt_replay.append(all(receipt_results))
  rejected_control.append(row['bad_receipt']['status']=='rejected' and not row['rejected'].get('ok') and not row['rejected_entered_adoption'] and row['rejected_before']==row['rejected_after'])
  b=row['adoption_boundary']['before']; a=row['adoption_boundary']['after']; bn={n['id']:n for n in b['nodes']}; an={n['id']:n for n in a['nodes']}
  added=set(an)-set(bn); removed=set(bn)-set(an); changed={i for i in set(bn)&set(an) if bn[i]!=an[i]}
  be={json.dumps(e,sort_keys=True) for e in b['edges']}; ae={json.dumps(e,sort_keys=True) for e in a['edges']}; added_edges=[json.loads(x) for x in ae-be]; removed_edges=be-ae
  added_types=sorted(n['type'] for n in (an[i] for i in added))
  expected_types=['ShapeObservation','ShapeSignature']
  agent_changes=[]
  for i in changed:
   old,new=bn[i],an[i]
   if old['type']!='Agent' or new['type']!='Agent': agent_changes.append(False); continue
   olda, newa=old['attrs'],new['attrs']; permitted={'meta_codebook_epoch','write_codebook_epoch'}
   agent_changes.append(all(olda.get(k)==v for k,v in newa.items() if k not in permitted) and all(newa.get(k)==0 for k in permitted if k=='meta_codebook_epoch' and olda.get(k) is None) and newa.get('write_codebook_epoch')==1)
  shape_nodes=[an[i] for i in added if an[i]['type']=='ShapeSignature']
  observation_nodes=[an[i] for i in added if an[i]['type']=='ShapeObservation']
  delta_ok=(not removed and not removed_edges and added_types==expected_types and len(changed)==1 and all(agent_changes)
    and len(shape_nodes)==1 and shape_nodes[0]['attrs'].get('kind')=='code_write_construction'
    and len(observation_nodes)==1 and observation_nodes[0]['attrs'].get('status')=='pending'
    and all(e['src'] in added or e['tgt'] in added for e in added_edges) and a['next_id']==b['next_id']+2)
  deltas.append({'pass':delta_ok,'added_node_types':added_types,'changed_node_count':len(changed),'added_edges':len(added_edges),'removed_edges':len(removed_edges),'boundary_ms':row['adoption_boundary']['elapsed_ns']/1e6})
  accepted_state.append(row['good_receipt']['status']=='accepted' and row['accepted'].get('ok') and row['accepted_shape_state']['epoch']==1 and len(row['accepted_shape_state']['shapes'])==1)
 checks += [('receipt_replay',all(receipt_replay)),('provider_auth_replay',all(auth_replay)),('rejected_never_enters_adoption',all(rejected_control)),('accepted_shape_and_epoch',all(accepted_state)),('adoption_boundary_exact_delta',all(x['pass'] for x in deltas))]
 result={'schema':'SubstrateAdequacyAdoptionBoundaryV1Analysis','checks':[{'name':n,'pass':v} for n,v in checks],'passed':sum(v for _,v in checks),'total':len(checks),'workers':deltas,'median_adoption_boundary_ms':statistics.median(x['boundary_ms'] for x in deltas),'limits':['one host, one authored square task, one provider key, three fresh workers','boundary audit isolates _teach_shape and excludes conversation/bootstrap and parsing','synthetic provider evidence does not establish label truth']}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n'); print(json.dumps({'passed':result['passed'],'total':result['total'],'analysis':str(OUT.relative_to(ROOT))},indent=2))
 if not all(v for _,v in checks): raise SystemExit(1)
if __name__=='__main__': main()

#!/usr/bin/env python3
"""Independent integrity and identity reconciliation for live store snapshots."""
import gzip,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; CAP=ROOT/'evaluation/reports/live_runtime_store_states_v1_20261004.json'; OUT=ROOT/'evaluation/reports/live_runtime_store_states_v1_analysis_20261004.json'
def main():
 cap=json.loads(CAP.read_text()); failures=[];stores={};store_rows=[]
 for req_i,req in enumerate(cap.get('requests',[]),1):
  for row in req.get('stores',[]):
   sid=row['store_id']; key=(req_i,sid)
   if key in stores:failures.append(f'duplicate store {key}');continue
   path=ROOT/row['path']
   try:raw=gzip.open(path,'rb').read();state=json.loads(raw)
   except Exception as e:failures.append(f'decode {key}: {e}');continue
   if hashlib.sha256(raw).hexdigest()!=row['state_sha256']:failures.append(f'hash {key}')
   graph=state.get('graph',{});nodes=graph.get('nodes',[]);edges=graph.get('edges',[]);node_ids=[]
   for n in nodes:
    nid=n.get('id',n.get('node_id'))
    if nid is not None:node_ids.append(nid)
   node_set=set(node_ids)
   if len(node_set)!=len(node_ids):failures.append(f'duplicate node IDs {key}')
   bad_edges=[]
   for e in edges:
    src=e.get('src',e.get('source'));tgt=e.get('tgt',e.get('target'))
    if src not in node_set or tgt not in node_set:bad_edges.append([src,tgt])
   if bad_edges:failures.append(f'edge references missing node {key}: {bad_edges[:3]}')
   rules=state.get('rules',[]);indices=[]
   for i,r in enumerate(rules):indices.append(int(r.get('local_rule_index',r.get('rule_index',r.get('index',i)))))
   if len(indices)!=len(set(indices)):failures.append(f'duplicate rule indices {key}')
   stores[key]={'rules':set(indices),'state':state};store_rows.append({'request':req_i,'store_id':sid,'nodes':len(nodes),'edges':len(edges),'rules':len(rules),'bytes':row['uncompressed_bytes']})
 rules_by_store={}
 for (_,sid),row in stores.items():rules_by_store.setdefault(sid,set()).update(row['rules'])
 identities_by_key={};unmatched=[]
 for req_i in (1,2):
  obs=cap.get('native_counter_observations',[])
  if req_i>len(obs):continue
  for ident in obs[req_i-1].get('counter_rows',{}).get('identities',[]):
   if len(ident)<3:continue
   aid,sid,local=map(int,ident[:3]);status='captured' if local in rules_by_store.get(sid,set()) else 'no_snapshot_or_rule_slot'
   item={'audit_id':aid,'store_id':sid,'local_rule_index':local,'status':status};identities_by_key[(aid,sid,local)]=item
 identities=list(identities_by_key.values());unmatched=[x for x in identities if x['status']!='captured']
 parity=cap.get('parent_parity',{});checks={'two_requests':len(cap.get('requests',[]))==2,'parent_parity':all(parity.values()) and len(parity)==4,'payloads_valid':not failures,'identity_rows_present':len(identities)>0,'all_identities_reconciled':not unmatched}
 result={'schema':'LiveRuntimeStoreStatesV1Analysis','checks':checks,'passed':all(checks.values()),'failures':failures,'store_rows':store_rows,'identity_count':len(identities),'captured_identity_count':len(identities)-len(unmatched),'unmatched_identities':unmatched,'identity_reconciliation':identities,'claim_limit':'one fixed route sample; store snapshots are first-observed at matcher entry'}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({'passed':result['passed'],'checks':checks,'store_count':len(store_rows),'identity_count':len(identities),'unmatched':len(unmatched),'failures':failures[:4]}));return 0 if result['passed'] else 2
if __name__=='__main__':raise SystemExit(main())

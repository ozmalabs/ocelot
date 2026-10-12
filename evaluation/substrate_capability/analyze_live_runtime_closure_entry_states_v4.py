#!/usr/bin/env python3
"""Independent integrity analysis for per-call primary closure snapshots."""
import gzip,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];CAP=ROOT/'evaluation/reports/live_runtime_closure_entry_states_v4_20261004.json';OUT=ROOT/'evaluation/reports/live_runtime_closure_entry_states_v4_analysis_20261004.json'
def main():
 cap=json.loads(CAP.read_text());errors=[];state_rows=[];calls=0
 for req_i,req in enumerate(cap.get('requests',[]),1):
  states={}
  for row in req.get('states',[]):
   try:
    raw=gzip.open(ROOT/row['path'],'rb').read();state=json.loads(raw)
    if hashlib.sha256(raw).hexdigest()!=row['state_sha256']:errors.append(f'hash mismatch {row["path"]}')
    graph=state['graph'];rules=state['rules'];scheduler=state['scheduler'];nodes=graph.get('nodes',[]);edges=graph.get('edges',[]);ids={x['id'] for x in nodes}
    if scheduler.get('rule_count')!=len(rules) or any(len(scheduler.get(k,[]))!=len(rules) for k in ('rule_dirty','rule_dirty_nodes','rule_cursors')):errors.append(f'scheduler vector mismatch {row["path"]}')
    if len(scheduler.get('eval_cache',{}).get('entry_counts',[]))!=6:errors.append(f'eval cache summary missing {row["path"]}')
    if len(ids)!=len(nodes):errors.append(f'duplicate node IDs {row["path"]}')
    if any(e.get('src') not in ids or e.get('tgt') not in ids for e in edges):errors.append(f'bad edge endpoint {row["path"]}')
    if len(rules)!=len({r.get('rule_uid') for r in rules}):errors.append(f'duplicate rule UID {row["path"]}')
    states[row['state_sha256']]=state;state_rows.append({'request':req_i,'state_sha256':row['state_sha256'],'nodes':len(nodes),'edges':len(edges),'rules':len(rules),'dirty_rules':sum(bool(x) for x in scheduler['rule_dirty']),'dirty_nodes':sum(len(x) for x in scheduler['rule_dirty_nodes']),'cursor_entries':sum(len(x) for x in scheduler['rule_cursors']),'eval_cache_entries':scheduler['eval_cache']['entry_counts'],'uncompressed_bytes':row['uncompressed_bytes']})
   except Exception as e:errors.append(f'payload error {row.get("path")}: {e}')
  for call in req.get('calls',[]):
   calls+=1
   if call.get('state_sha256') not in states:errors.append(f'missing call state request={req_i} call={call.get("call_index")}')
 checks={'two_requests':len(cap.get('requests',[]))==2,'call_count_positive':calls>0,'all_payloads_valid':not errors,'all_parent_parity':all(cap.get('parent_parity',{}).values()),'source_stable':cap.get('source_stable') is True}
 result={'schema':'LiveRuntimeClosureEntryStatesV4Analysis','checks':checks,'passed':all(checks.values()),'errors':errors,'request_count':len(cap.get('requests',[])),'call_count':calls,'unique_state_count':len(state_rows),'state_rows':state_rows,'calls_per_request':[len(x.get('calls',[])) for x in cap.get('requests',[])],'parent_parity':cap.get('parent_parity')}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({'passed':result['passed'],'checks':checks,'calls':calls,'unique_states':len(state_rows),'errors':errors[:5]}));return 0 if result['passed'] else 2
if __name__=='__main__':raise SystemExit(main())

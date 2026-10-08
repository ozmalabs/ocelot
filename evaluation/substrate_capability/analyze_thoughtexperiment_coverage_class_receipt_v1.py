#!/usr/bin/env python3
"""Independent graph-diff and receipt audit for CoW class return v1."""
import hashlib,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
LOCK=ROOT/'evaluation/substrate_capability/thoughtexperiment_coverage_class_receipt_v1_lock_20261004.json'
RAW=ROOT/'evaluation/reports/thoughtexperiment_coverage_class_receipt_v1_20261004.json'
OUT=ROOT/'evaluation/reports/thoughtexperiment_coverage_class_receipt_v1_analysis_20261004.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def norm(x):return json.dumps(x,sort_keys=True,separators=(',',':'))
def diff(before,after):
 bn={int(x['id']):x for x in before['nodes']};an={int(x['id']):x for x in after['nodes']}
 be={(int(x['src']),x['type'],int(x['tgt']),norm(x.get('attrs',{}))):x for x in before['edges']}
 ae={(int(x['src']),x['type'],int(x['tgt']),norm(x.get('attrs',{}))):x for x in after['edges']}
 return {'nodes_added':[an[i] for i in sorted(an.keys()-bn.keys())],
  'nodes_removed':[bn[i] for i in sorted(bn.keys()-an.keys())],
  'nodes_changed':[],'edges_added':[ae[k] for k in sorted(ae.keys()-be.keys())],
  'edges_removed':[be[k] for k in sorted(be.keys()-ae.keys())],
  'edges_changed':[],'edges_removed_details':[],'nodes_removed_details':[]}
def canonical(g):
 return {'nodes':sorted(g['nodes'],key=lambda x:int(x['id'])),
  'edges':sorted(g['edges'],key=lambda x:(int(x['src']),x['type'],int(x['tgt']),norm(x.get('attrs',{}))))}
def main():
 lock=json.loads(LOCK.read_text());raw=json.loads(RAW.read_text());errors=[]
 if raw.get('lock_sha256')!=sha(LOCK):errors.append('lock digest mismatch')
 if raw.get('sources')!=lock.get('sources'):errors.append('capture source map mismatch')
 for rel,want in lock.get('sources',{}).get('files',{}).items():
  p=ROOT/rel
  if not p.exists() or sha(p)!=want:errors.append(f'source drift: {rel}')
 panels=lock.get('panels',[]);rows=raw.get('workers',[])
 if len(panels)!=5 or len(rows)!=len(panels):errors.append('expected five locked workers')
 timings={'fork':[],'receipt_mutation':[],'delta_extract':[],'apply':[]};out=[]
 for panel,row in zip(panels,rows):
  key=(panel['task'],panel['worker'])
  if (row.get('task'),row.get('worker'))!=key:errors.append(f'panel identity mismatch {key}')
  expected=diff(row['primary_before'],row['branch_after'])
  if row.get('derived_delta')!=expected:errors.append(f'journal is not exact graph diff {key}')
  if canonical(row['primary_after'])!=canonical(row['branch_after']):errors.append(f'primary/branch parity failure {key}')
  if canonical(row['primary_before'])!=canonical(row['primary_before_return']):errors.append(f'primary graph changed before return {key}')
  if row.get('rules_before')!=row.get('rules_after'):errors.append(f'rules changed {key}')
  if not row.get('stale_retry_rejected') or not row.get('stale_retry_unchanged'):errors.append(f'stale retry gate failed {key}')
  if not row.get('holdout_safe'):errors.append(f'upstream holdout safety absent {key}')
  nodes={int(n['id']):n for n in row['primary_after']['nodes']};edges=row['primary_after']['edges'];rid=int(row['receipt_id'])
  receipt=nodes.get(rid,{}).get('attrs',{})
  if receipt.get('role')!='coverage_qualified_behavior_class' or receipt.get('decision')!='behavior_class':errors.append(f'receipt missing or malformed {key}')
  member_nodes={int(row['candidate_node_ids'][h]) for h in row['expected_member_ids']}
  actual={int(e['tgt']) for e in edges if int(e['src'])==rid and e['type']=='returns_member'}
  if actual!=member_nodes:errors.append(f'receipt membership mismatch {key}')
  for hid,term in row['returned_terms'].items():
   nid=int(row['candidate_node_ids'][hid]);attrs=nodes.get(nid,{}).get('attrs',{})
   if json.loads(attrs.get('term_json','null'))!=term:errors.append(f'candidate term mismatch {key}:{hid}')
  for name,value in row.get('timing_ns',{}).items():timings.setdefault(name,[]).append(int(value))
  out.append({'task':key[0],'worker':key[1],'members':len(actual),'nodes_added':len(expected['nodes_added']),'edges_added':len(expected['edges_added']),'fork_ns':row['timing_ns']['fork'],'apply_ns':row['timing_ns']['apply'],'stale_retry_rejected':row['stale_retry_rejected']})
 pids=[r.get('pid') for r in rows]
 if len(set(pids))!=len(pids):errors.append('workers are not fresh processes')
 summary={'panels':len(rows),'workers':len(set(pids)),'membership_edges':sum(x['members'] for x in out),'median_ns':{k:statistics.median(v) if v else None for k,v in timings.items()},'all_holdout_safe':all(r.get('holdout_safe') for r in rows)}
 result={'schema':'ThoughtexperimentCoverageClassReceiptV1Analysis','passed':not errors,'errors':errors,'lock_sha256':sha(LOCK),'capture_sha256':sha(RAW),'analyzer_sha256':sha(Path(__file__)),'summary':summary,'rows':out,'limits':['five inherited authored-task panels','candidate pool and holdout decision are upstream inputs','single-host mechanism demonstration','no persistent rule activation']}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({'passed':not errors,'errors':errors,'summary':summary},sort_keys=True));return int(bool(errors))
if __name__=='__main__':raise SystemExit(main())

#!/usr/bin/env python3
"""Independent structure/cost audit for Bigville boundary min-sum elimination."""
import hashlib,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];RAW=ROOT/'evaluation/reports/substrate_bigville_high_boundary_width_v1_1_20260926.json';LOCK=ROOT/'evaluation/substrate_capability/bigville_high_boundary_width_v1_1_lock_20260926.json';OUT=ROOT/'evaluation/reports/substrate_bigville_high_boundary_width_v1_1_analysis_20260926.json'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def expected_order(boundary,scopes):
 adj={v:set() for v in boundary}
 for scope in scopes:
  for v in scope:adj[v].update(set(scope)-{v})
 todo=set(boundary);order=[];width=0;sizes=[]
 while todo:
  def cost(v):
   ns=adj[v]&todo;missing=sum(1 for a in ns for b in ns if a<b and b not in adj[a]);return missing,len(ns),v
  v=min(todo,key=cost);ns=adj[v]&todo;width=max(width,len(ns));sizes.append(1+len(ns))
  for a in ns:adj[a].update(ns-{a})
  todo.remove(v);order.append(v)
 return order,width,sizes
def expected_pairs(top,k):
 if top=='chain':return {tuple(sorted((i,i+1))) for i in range(k-1)}
 if top=='cycle':return {tuple(sorted((i,i+1))) for i in range(k-1)}|({(0,k-1)} if k>=3 else set())
 return {tuple((i,j)) for i in range(k) for j in range(i+1,k)}
def main():
 p=json.loads(RAW.read_text());lk=json.loads(LOCK.read_text());runs=p['runs'];cases=[c for r in runs for c in r['cases']]
 def edge_count(top,k):return k-1 if top=='chain' or (top=='cycle' and k==2) else k if top=='cycle' else k*(k-1)//2
 manifest=p['run_manifest'];log=manifest.get('stdout_stderr_capture') or {};log_path=ROOT/log.get('path','__missing__')
 children=manifest.get('execution',{}).get('child_processes',[])
 child_logs_valid=len(children)==3 and all(x.get('argv',[])[-2:]==['--worker',str(x.get('replicate'))] and x.get('stdout_sha256')==hashlib.sha256((json.dumps(runs[x['replicate']],sort_keys=True)+'\n').encode()).hexdigest() and x.get('stderr_bytes')==0 and x.get('stderr_sha256')==hashlib.sha256(b'').hexdigest() for x in children)
 checks={'schema_72_cases':p.get('schema_version')==1 and len(cases)==72,'source_lock':p['locked_inputs']==lk['locked_inputs'] and p['post_run_inputs']==p['locked_inputs'] and p['lock_sha256']==sha(LOCK),'shared_manifest_valid':manifest.get('manifest_schema')=='substrate-run-manifest-v1' and manifest.get('exit_status')==0 and manifest.get('engine',{}).get('build_is_stale') is False and all(v.get('exists') and sha(ROOT/name)==v.get('sha256') for name,v in manifest.get('explicit_inputs',{}).items()),'parent_log_hash_valid':log_path.is_file() and sha(log_path)==log.get('sha256') and log_path.stat().st_size==log.get('bytes',-1),'child_process_records_valid':child_logs_valid,'three_fresh_stable_workers':len(runs)==3 and len({r['pid'] for r in runs})==3 and all(r['started_inputs']==p['locked_inputs']==r['finished_inputs'] for r in runs) and all(c['source_inputs_start']==p['locked_inputs']==c['source_inputs_end'] for c in cases),'full_design':all(sum(c['n_residents']==n and c['k']==k and c['topology']==top for c in cases)==3 for n in (12,20) for k in (2,4,6,8) for top in ('chain','cycle','clique')),'boundary_and_topology_counts':all(c['boundary_size']==c['k']==len(c['boundary_nodes']) and c['cross_factor_count']==edge_count(c['topology'],c['k']) and len(c['cross_links'])==c['cross_factor_count'] for c in cases),'message_count_reconstruction':all(c['message_assignment_count']==sum(3**(a+b) for a,b in c['component_shape'])==c['expected_message_assignment_count'] for c in cases),'min_fill_order_and_buckets':True,'boundary_state_and_exact_energy':all(c['exhaustive_boundary_assignments']==3**c['k'] and c['separator_condition_valid'] and c['states_valid'] and abs(c['energy_gap'])<=1e-7 and abs(c['global_energy']-c['independent_global_energy'])<=1e-7 and abs(c['boundary_ve_energy']-c['independent_boundary_ve_energy'])<=1e-7 for c in cases),'positive_timings':all(all(v>0 for v in c['timing_ns'].values()) for c in cases)}
 for c in cases:
  st=c['boundary_factor_scopes'];order,width,sizes=expected_order(c['boundary_nodes'],st);ve=c['boundary_elimination'];buckets=ve['buckets']
  idx={v:i for i,v in enumerate(sorted(c['boundary_nodes']))};observed={tuple(sorted((idx[a],idx[b]))) for a,b,_ in c['cross_links']}
  if observed!=expected_pairs(c['topology'],c['k']) or any(a not in idx or b not in idx for a,b,_ in c['cross_links']):checks['boundary_and_topology_counts']=False
  if not (ve['order']==order and ve['width']==width and [x['scope_size'] for x in buckets]==sizes and [x['rows'] for x in buckets]==[3**x for x in sizes] and [x['output_entries'] for x in buckets]==[3**(x-1) for x in sizes] and ve['rows_evaluated']==sum(3**x for x in sizes) and ve['factor_entries_processed']==sum(3**(x-1) for x in sizes)):
   checks['min_fill_order_and_buckets']=False
 summary=[]
 for n in (12,20):
  for k in (2,4,6,8):
   for top in ('chain','cycle','clique'):
    xs=[c for c in cases if c['n_residents']==n and c['k']==k and c['topology']==top];median=lambda f:statistics.median(f(c) for c in xs)
    summary.append({'residents':n,'topology':top,'boundary_dimension':k,'replicates':len(xs),'boundary_width':median(lambda c:c['boundary_elimination']['width']),'median_max_bucket_scope':median(lambda c:max((b['scope_size'] for b in c['boundary_elimination']['buckets']),default=0)),'median_variable_elimination_rows':median(lambda c:c['boundary_elimination']['rows_evaluated']),'exhaustive_boundary_assignments':3**k,'median_message_assignments':median(lambda c:c['message_assignment_count']),'median_direct_oracle_assignments':median(lambda c:c['direct_oracle_assignment_count']),'median_boundary_ve_ms':median(lambda c:c['timing_ns']['message_build_and_boundary_elimination'])/1e6,'median_global_jt_ms':median(lambda c:c['timing_ns']['global_width_and_map'])/1e6})
 out={'schema_version':1,'raw_sha256':sha(RAW),'lock_sha256':sha(LOCK),'checks':checks,'passed':all(checks.values()),'case_count':len(cases),'summary_by_size_and_boundary':summary,'claim_boundary':p['claim_boundary']};OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2))
 if not out['passed']:raise SystemExit('independent analysis failed')
if __name__=='__main__':main()

#!/usr/bin/env python3
"""Independent graph oracle and cost summary for the restricted profile."""
from __future__ import annotations
import collections,hashlib,json,statistics,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'evaluation/substrate_capability'),str(ROOT/'scripts')]
from finite_key_reachability_profile_v1 import LOCK,OUT as CAPTURE,RUNNER,PROTOCOL,PROFILE,NEGATIVE,SIZES,TOPOLOGIES,REPS,edges_for,lock_inputs
from analyze_mint_termination_fragment import analyze
ANALYZER=Path(__file__).resolve();ANALYSIS=ROOT/'evaluation/reports/finite_key_reachability_profile_v1_analysis_20261005.json'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def bfs(n,edges,start):
 adj=[[] for _ in range(n)]
 for a,b in edges:adj[a].append(b)
 reached=set();todo=list(adj[start])
 while todo:
  v=todo.pop()
  if v==start or v in reached:continue
  reached.add(v);todo.extend(adj[v])
 return sorted(reached)
def independent_accept(rules,edge_attrs):
 if not isinstance(rules,list) or not rules:return False
 for rule in rules:
  if not isinstance(rule,dict) or set(rule)-{'name','match','effects'}:return False
  pats=rule.get('match');effects=rule.get('effects')
  if not isinstance(pats,list) or not pats or any(not isinstance(p,list) or len(p)!=3 or not all(isinstance(x,str) for x in p) for p in pats):return False
  bound={v for p in pats for v in (p[0],p[2])}
  if not isinstance(effects,list) or not effects:return False
  for e in effects:
   if not isinstance(e,list) or not e:return False
   if e[0]=='add_edge' and len(e)==5:
    _,src,typ,tgt,attrs=e
    if not all(isinstance(x,str) for x in (src,typ,tgt)) or attrs!={} or src not in bound or tgt not in bound or typ in edge_attrs:return False
   else:return False
 return True
def main():
 lock=json.loads(LOCK.read_text());raw=json.loads(CAPTURE.read_text());before=lock_inputs();err=[];bycell=collections.defaultdict(list)
 design=lock['locked_inputs']['design'];expected={(t,n,r) for t in TOPOLOGIES for n in SIZES for r in range(1,REPS+1)}
 for c in raw['cases']:
  key=(c['topology'],c['n'],c['replicate']);bycell[key[:2]].append(c)
  es=edges_for(c['topology'],c['n']);oracle=[bfs(c['n'],es,i) for i in range(c['n'])]
  pairs={(i,'reachable',j) for i,row in enumerate(oracle) for j in row}
  actual={tuple(x) for x in c.get('materialized_reachable_pairs',[])}
  checker=analyze(PROFILE,[f'n{i}' for i in range(c['n'])],[[f'n{a}','link',f'n{b}',{}] for a,b in es])
  if key not in expected:err.append(f'unknown/duplicate cell {key}')
  if c['initial_edges']!=[list(x) for x in es] or c['initial_edge_count']!=len(es):err.append(f'input mismatch {key}')
  if c['oracle_reachable_by_source']!=oracle or c['direct_reachable_by_source']!=oracle:err.append(f'oracle/direct mismatch {key}')
  if actual!=pairs or c['materialized_reachable_edges']!=len(pairs):err.append(f'materialized relation mismatch {key}')
  if c['checker']!=checker or not checker['accepted']:err.append(f'checker mismatch/rejection {key}')
  report=c['native_report'];bound=checker['progress_steps_upper_bound']
  if report.get('status')!='fixed_point' or report.get('progress_steps',bound+1)>bound or report.get('budget_overshoot',0):err.append(f'closure status/bound mismatch {key}')
 if len(raw['cases'])!=len(expected) or len(bycell)!=len(TOPOLOGIES)*len(SIZES):err.append('incomplete case matrix')
 neg=analyze(NEGATIVE,['n0','n1'],[['n0','link','n1',{}]])
 if neg['accepted']:err.append('negative unrestricted-mint control unexpectedly admitted')
 summaries={}
 for (topo,n),rows in sorted(bycell.items()):
  summaries[f'{topo}:N={n}']={'replicates':len(rows),'input_edges':rows[0]['initial_edge_count'],'reachable_pairs':rows[0]['expected_reachable_pairs'],'checker_bound':rows[0]['checker']['progress_steps_upper_bound'],'median_profile_setup_ms':statistics.median(x['profile_setup_wall_ns'] for x in rows)/1e6,'median_profile_closure_ms':statistics.median(x['profile_closure_wall_ns'] for x in rows)/1e6,'median_direct_all_sources_ms':statistics.median(x['direct_query_wall_ns'] for x in rows)/1e6,'median_profile_cpu_ms':statistics.median(x['profile_closure_cpu_ns'] for x in rows)/1e6,'median_progress_steps':statistics.median(x['native_report']['progress_steps'] for x in rows),'median_passes':statistics.median(x['native_report']['passes_completed'] for x in rows),'peak_process_rss_bytes':max(x['process_peak_rss_bytes'] for x in rows)}
 checks={'lock_and_capture_current':raw['locked_inputs']==lock['locked_inputs']==raw['post_run_inputs']==before,'registered_profile_and_negative_control_decisions':independent_accept(PROFILE,set()) and not independent_accept(NEGATIVE,set()) and not neg['accepted'],'complete_unique_36_case_matrix':len(raw['cases'])==36 and len({(x['topology'],x['n'],x['replicate']) for x in raw['cases']})==36 and set((x['topology'],x['n'],x['replicate']) for x in raw['cases'])==expected,'all_direct_and_materialized_answers_match_independent_dfs':not any('oracle/direct' in x or 'materialized relation' in x for x in err),'all_native_closures_hit_fixpoint_within_bound':not any('closure status' in x for x in err),'all_checker_decisions_recomputed':not any('checker' in x for x in err),'analyzer_hash_stable':sha(ANALYZER)==lock['locked_inputs']['analyzer_sha256']}
 out={'schema':'FiniteKeyReachabilityProfileV1Analysis','analyzer_sha256':sha(ANALYZER),'capture_sha256':sha(CAPTURE),'summary':summaries,'checks':checks,'errors':err,'passed':all(checks.values()),'claim_limit':raw['claim_limit']}
 ANALYSIS.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps({'passed':out['passed'],'checks':checks,'errors':err,'analysis':ANALYSIS.relative_to(ROOT).as_posix()},indent=2));return 0 if out['passed'] else 2
if __name__=='__main__':raise SystemExit(main())

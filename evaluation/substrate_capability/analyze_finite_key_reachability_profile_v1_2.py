#!/usr/bin/env python3
"""Independent correctness, lock, and paired timing analysis for profile v1.2."""
from __future__ import annotations
import collections,hashlib,json,statistics,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'evaluation/substrate_capability'),str(ROOT/'scripts')]
from finite_key_reachability_profile_v1_2 import LOCK,OUT as CAPTURE,PROFILE,NEGATIVE,TOPOLOGIES,SIZES,REPS,Q_VALUES,edges_for,lock_inputs
from analyze_mint_termination_fragment import analyze
ANALYZER=Path(__file__).resolve();ANALYSIS=ROOT/'evaluation/reports/finite_key_reachability_profile_v1_2_analysis_20261005.json'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def bfs(n,edges,start):
 adj=[[] for _ in range(n)]
 for a,b in edges:adj[a].append(b)
 seen=set();todo=list(adj[start])
 while todo:
  x=todo.pop()
  if x==start or x in seen:continue
  seen.add(x);todo.extend(adj[x])
 return sorted(seen)
def independent_accept(rules):
 if not isinstance(rules,list) or not rules:return False
 for r in rules:
  if not isinstance(r,dict) or set(r)-{'name','match','effects'}:return False
  bound={v for p in r.get('match',[]) for v in (p[0],p[2])} if isinstance(r.get('match'),list) else set()
  if not r.get('match') or not r.get('effects'):return False
  for e in r['effects']:
   if not isinstance(e,list) or len(e)!=5 or e[0]!='add_edge' or e[4]!={} or e[1] not in bound or e[3] not in bound:return False
 return True
def main():
 lock=json.loads(LOCK.read_text());raw=json.loads(CAPTURE.read_text());now=lock_inputs();errors=[];groups=collections.defaultdict(list)
 expected={(t,n,r) for t in TOPOLOGIES for n in SIZES for r in range(1,REPS+1)};seen=set()
 for c in raw['cases']:
  key=(c['topology'],c['n'],c['replicate']);seen.add(key);groups[key[:2]].append(c)
  es=edges_for(c['topology'],c['n']);oracle=[bfs(c['n'],es,i) for i in range(c['n'])];pairs={(i,j) for i,row in enumerate(oracle) for j in row}
  spec=analyze(PROFILE,[f'n{i}' for i in range(c['n'])],[[f'n{a}','link',f'n{b}',{}] for a,b in es])
  if key not in expected or c['edges']!=[list(e) for e in es] or c['edge_count']!=len(es):errors.append(f'input/matrix mismatch {key}')
  if c['oracle']!=oracle or c['materialized_pair_count']!=len(pairs) or not c['materialized_exact']:errors.append(f'independent relation mismatch {key}')
  if c['checker']!=spec or not spec['accepted']:errors.append(f'checker mismatch {key}')
  report=c['closure_report'];bound=spec['progress_steps_upper_bound']
  if report.get('status')!='fixed_point' or report.get('progress_steps',bound+1)>bound or report.get('budget_overshoot',0):errors.append(f'closure failure {key}')
  if set(c['sweep'])!=set(map(str,Q_VALUES)):errors.append(f'query matrix incomplete {key}')
  for q,s in c['sweep'].items():
   if not s['direct_answers_exact'] or not s['materialized_answers_exact']:errors.append(f'query mismatch {key} Q={q}')
   if s['direct_measured_first'] != ((c['replicate']+int(q).bit_length())%2==0):errors.append(f'arm order mismatch {key} Q={q}')
 if seen!=expected or len(raw['cases'])!=60:errors.append('incomplete or duplicate case matrix')
 if analyze(NEGATIVE,['n0','n1'],[['n0','link','n1',{}]])['accepted']:errors.append('negative mint control admitted')
 summaries={}
 for (topo,n),rows in sorted(groups.items()):
  qs={}
  for q in map(str,Q_VALUES):
   ratios=[r['sweep'][q]['profile_total_wall_ns']/r['sweep'][q]['direct_total_wall_ns'] for r in rows]
   favorable=sum(r['sweep'][q]['materialization_favored'] for r in rows)
   qs[q]={'median_direct_total_ms':statistics.median(r['sweep'][q]['direct_total_wall_ns'] for r in rows)/1e6,'median_profile_total_ms':statistics.median(r['sweep'][q]['profile_total_wall_ns'] for r in rows)/1e6,'median_paired_ratio':statistics.median(ratios),'favorable_repetitions':favorable,'crossover_criterion_met':statistics.median(ratios)<1 and favorable>=12}
  summaries[f'{topo}:N={n}']={'repetitions':len(rows),'edge_count':rows[0]['edge_count'],'reachable_pairs':rows[0]['reachable_pairs'],'median_setup_ms':statistics.median(r['setup_wall_ns'] for r in rows)/1e6,'median_install_ms':statistics.median(r['install_wall_ns'] for r in rows)/1e6,'median_closure_ms':statistics.median(r['closure_wall_ns'] for r in rows)/1e6,'query_counts':qs}
 checks={'source_lock_capture_current':raw['locked_inputs']==lock['locked_inputs']==raw['post_run_inputs']==now,'independent_checker_and_negative_control':independent_accept(PROFILE) and not independent_accept(NEGATIVE) and not analyze(NEGATIVE,['n0','n1'],[['n0','link','n1',{}]])['accepted'],'complete_unique_60_case_matrix':seen==expected and len(raw['cases'])==60,'exact_materialized_relation_against_dfs':not any('relation mismatch' in e for e in errors),'exact_direct_and_materialized_answers_all_q':not any('query mismatch' in e for e in errors),'all_closures_fixed_point_within_bound':not any('closure failure' in e for e in errors),'checker_decisions_recomputed':not any('checker mismatch' in e for e in errors),'alternated_query_arm_order':not any('arm order' in e for e in errors),'analyzer_hash_stable':sha(ANALYZER)==lock['locked_inputs']['analyzer_sha256']}
 out={'schema':'FiniteKeyReachabilityProfileV1_2Analysis','analyzer_sha256':sha(ANALYZER),'capture_sha256':sha(CAPTURE),'summary':summaries,'checks':checks,'errors':errors,'passed':all(checks.values()),'crossover_rule':lock['locked_inputs']['design']['crossover_rule'],'claim_limit':raw['claim_limit']}
 ANALYSIS.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps({'passed':out['passed'],'checks':checks,'errors':errors,'analysis':ANALYSIS.relative_to(ROOT).as_posix()},indent=2));return 0 if out['passed'] else 2
if __name__=='__main__':raise SystemExit(main())

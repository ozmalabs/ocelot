#!/usr/bin/env python3
"""Independent parity, cache accounting, and total-cost analysis."""
from __future__ import annotations
import collections,hashlib,json,statistics,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'evaluation/substrate_capability'),str(ROOT/'scripts')]
from reachability_cache_materialization_comparison_v1 import LOCK,OUT as CAPTURE,PROFILE,NEGATIVE,TOPOLOGIES,SIZES,READERS,REPS,edges_for,lock_inputs
from analyze_mint_termination_fragment import analyze
ANALYZER=Path(__file__).resolve();ANALYSIS=ROOT/'evaluation/reports/reachability_cache_materialization_comparison_v1_analysis_20261005.json'
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
def main():
 lock=json.loads(LOCK.read_text());raw=json.loads(CAPTURE.read_text());now=lock_inputs();errors=[];groups=collections.defaultdict(list)
 expected={(t,n,r,rep) for t in TOPOLOGIES for n in SIZES for r in READERS for rep in range(1,REPS+1)};seen=set()
 for c in raw['cases']:
  key=(c['topology'],c['n'],c['reader_rules'],c['replicate']);seen.add(key);groups[key[:3]].append(c)
  es=edges_for(c['topology'],c['n']);spec=analyze(PROFILE,[f'n{i}' for i in range(c['n'])],[[f'n{a}','link',f'n{b}',{}] for a,b in es])
  if key not in expected or c['edge_count']!=len(es) or c['checker']!=spec or not spec['accepted']:errors.append(f'input/checker mismatch {key}')
  if c['arm_order']!=list(c['arms']):errors.append(f'arm order mismatch {key}')
  exp_counts=[len(bfs(c['n'],es,i)) for i in range(c['n'])]
  for arm,d in c['arms'].items():
   if d['observed_query_counts']!=exp_counts or d['expected_query_counts']!=exp_counts or not d['query_counts_exact']:errors.append(f'query semantic mismatch {key} {arm}')
   if not d['reader_report_ok'] or d['reader_report'].get('passes_completed')!=1:errors.append(f'reader closure mismatch {key} {arm}')
   if arm=='materialized_profile':
    pairs={(i,j) for i,row in enumerate(exp_counts) for j in []}
    exact={(i,j) for i in range(c['n']) for j in bfs(c['n'],es,i)}
    if not d['materialized_exact'] or d['materialized_pairs']!=len(exact):errors.append(f'materialization mismatch {key}')
    pr=d['profile_report'];bound=spec['progress_steps_upper_bound']
    if not pr or pr.get('status')!='fixed_point' or pr.get('progress_steps',bound+1)>bound:errors.append(f'profile bound mismatch {key}')
   act=d['cache_activity_since_start'];N=c['n'];R=c['reader_rules']
   if arm=='direct_cache_off' and any(act.values()):errors.append(f'off cache active {key}')
   if arm=='direct_cache_on' and (act.get('misses')!=N or act.get('hits')!=N*(R-1)):errors.append(f'cache work mismatch {key}: {act}')
  if set(c['arms'])!={'direct_cache_off','direct_cache_on','materialized_profile'}:errors.append(f'arms missing {key}')
 if seen!=expected or len(raw['cases'])!=60:errors.append('case matrix incomplete/duplicate')
 if analyze(NEGATIVE,['n0','n1'],[['n0','link','n1',{}]])['accepted']:errors.append('negative control admitted')
 summary={}
 for cell,rows in sorted(groups.items()):
  k=f'{cell[0]}:N={cell[1]}:readers={cell[2]}';summary[k]={}
  for arm in ('direct_cache_off','direct_cache_on','materialized_profile'):
   vals=[r['arms'][arm]['total_wall_ns'] for r in rows]
   summary[k][arm]={'median_total_wall_ms':statistics.median(vals)/1e6,'median_reader_wall_ms':statistics.median(r['arms'][arm]['reader_wall_ns'] for r in rows)/1e6,'median_cache_hits':statistics.median(r['arms'][arm]['cache_activity_since_start']['hits'] for r in rows),'median_cache_misses':statistics.median(r['arms'][arm]['cache_activity_since_start']['misses'] for r in rows),'median_cache_payload_bytes':statistics.median(r['arms'][arm]['cache_stats'].get('estimated_payload_bytes',0) for r in rows)}
  d=summary[k];summary[k]['ratios_profile_over_cache_on']=d['materialized_profile']['median_total_wall_ms']/d['direct_cache_on']['median_total_wall_ms'];summary[k]['ratios_cache_on_over_cache_off']=d['direct_cache_on']['median_total_wall_ms']/d['direct_cache_off']['median_total_wall_ms']
 checks={'source_lock_and_capture_current':raw['locked_inputs']==lock['locked_inputs']==raw['post_run_inputs']==now,'independent_complete_case_matrix':seen==expected and len(raw['cases'])==60,'all_query_counts_match_independent_dfs':not any('query semantic' in e for e in errors),'materialized_relation_and_progress_bound':not any('materialization mismatch' in e or 'profile bound' in e for e in errors),'reader_rules_fixed_point_one_pass':not any('reader closure' in e for e in errors),'cache_off_zero_and_cache_on_exact_reuse_counts':not any('cache active' in e or 'cache work' in e for e in errors),'arm_order_and_three_arm_coverage':not any('arm order' in e or 'arms missing' in e for e in errors),'restricted_checker_and_negative_control':not any('checker' in e or 'negative' in e for e in errors),'analyzer_hash_stable':sha(ANALYZER)==lock['locked_inputs']['analyzer_sha256']}
 out={'schema':'ReachabilityCacheMaterializationComparisonV1Analysis','analyzer_sha256':sha(ANALYZER),'capture_sha256':sha(CAPTURE),'summary':summary,'checks':checks,'errors':errors,'passed':all(checks.values()),'claim_limit':raw['claim_limit']}
 ANALYSIS.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps({'passed':out['passed'],'checks':checks,'errors':errors,'analysis':ANALYSIS.relative_to(ROOT).as_posix()},indent=2));return 0 if out['passed'] else 2
if __name__=='__main__':raise SystemExit(main())

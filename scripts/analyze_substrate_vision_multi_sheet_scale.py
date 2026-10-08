#!/usr/bin/env python3
"""Independent equation, cross-root, counter, and provenance audit."""
import hashlib,json,statistics
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'evaluation/reports/substrate_vision_multi_sheet_scale_20260925.json'
LOCK=ROOT/'evaluation/substrate_capability/vision_multi_sheet_scale_lock_20260925.json'
OUT=ROOT/'evaluation/reports/substrate_vision_multi_sheet_scale_analysis_20260925.json'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def predict(a):
 n=a['n_side'];acts=(np.ones(n*n),np.full(n*n,a['b_initial_act']));affs=(np.asarray(a['aff_A']),np.asarray(a['aff_B']));pool=np.concatenate(acts);out=[]
 for ix,vec in enumerate(acts):
  grid=vec.reshape(n,n);vals=[]
  for r in range(n):
   for c in range(n):
    near=[grid[rr,cc] for rr in range(max(0,r-1),min(n,r+2)) for cc in range(max(0,c-1),min(n,c+2)) if (rr,cc)!=(r,c)]
    local=float(np.mean(near)) if near else 0.0
    mean=float(np.mean(vec if a['variant']=='scoped' else pool))
    vals.append(max(float(affs[ix][r*n+c])+local-mean,0.0))
  out.append(vals)
 return out
def main():
 d=json.loads(RAW.read_text());l=json.loads(LOCK.read_text());p=d['provenance'];bad=[]
 for a in d['arms']:
  ex=predict(a);delta=max(float(np.max(np.abs(np.asarray(a['act_next_A'])-ex[0]))),float(np.max(np.abs(np.asarray(a['act_next_B'])-ex[1]))))
  if delta>1e-12:bad.append({'seed':a['seed'],'n_side':a['n_side'],'variant':a['variant'],'b':a['b_initial_act'],'max_delta':delta})
 pairs=[]
 for seed in (4101,7301,10703):
  for n in (2,4,8,16):
   get=lambda v,b:next(a for a in d['arms'] if a['seed']==seed and a['n_side']==n and a['variant']==v and a['b_initial_act']==b)
   g0,g1,s0,s1=get('global',0.0),get('global',1.0),get('scoped',0.0),get('scoped',1.0)
   pairs.append({'seed':seed,'n_side':n,'units_per_sheet':n*n,'global_a_change_max':float(np.max(np.abs(np.asarray(g0['act_next_A'])-np.asarray(g1['act_next_A'])))),'scoped_a_change_max':float(np.max(np.abs(np.asarray(s0['act_next_A'])-np.asarray(s1['act_next_A'])))),'global_term_units_b0':g0['global_counters'].get('term_units_total',0),'global_term_units_b1':g1['global_counters'].get('term_units_total',0),'scoped_term_units_b0':s0['global_counters'].get('term_units_total',0),'scoped_term_units_b1':s1['global_counters'].get('term_units_total',0),'global_nodesoftype_units_b0':g0['global_counters'].get('term_unit:NodesOfType',0),'global_nodesoftype_units_b1':g1['global_counters'].get('term_unit:NodesOfType',0),'scoped_nodesoftype_units_b0':s0['global_counters'].get('term_unit:NodesOfType',0),'scoped_nodesoftype_units_b1':s1['global_counters'].get('term_unit:NodesOfType',0)})
 rows=[]
 for n in (2,4,8,16):
  group=[x for x in pairs if x['n_side']==n]
  rows.append({'n_side':n,'units_per_sheet':n*n,'total_sunits':2*n*n,'replicated_pairs':len(group),'global_a_change_median':statistics.median(x['global_a_change_max'] for x in group),'scoped_a_change_median':statistics.median(x['scoped_a_change_max'] for x in group),'median_global_nodesoftype_units':statistics.median(max(x['global_nodesoftype_units_b0'],x['global_nodesoftype_units_b1']) for x in group),'median_scoped_nodesoftype_units':statistics.median(max(x['scoped_nodesoftype_units_b0'],x['scoped_nodesoftype_units_b1']) for x in group),'median_total_term_units_global':statistics.median(max(x['global_term_units_b0'],x['global_term_units_b1']) for x in group),'median_total_term_units_scoped':statistics.median(max(x['scoped_term_units_b0'],x['scoped_term_units_b1']) for x in group)})
 term_conserve=all(sum(x['count'] for x in a['per_rule_counters'] if x['metric']=='term_units')==a['global_counters'].get('term_units_total',0) for a in d['arms'])
 candidate_conserve=all(sum(x['count'] for x in a['per_rule_counters'] if x['metric']=='candidate_tests')==a['global_counters'].get('cand_tested',0) for a in d['arms'])
 checks={'lock_hashes_match':l['hashes']['runner']==p['runner_sha256'] and l['hashes']['protocol']==p['protocol_sha256'] and l['hashes']['seed']==p['seed_sha256'],'raw_lock_sha256':d['lock_sha256']==sha(LOCK),'native_matches_lock':l['native_extension_sha256']==p['native_extension_sha256'],'engine_matches_source':p['engine_provenance']['source_match'] in ('own','shared') and not p['engine_provenance']['stale_rust'],'48_arms':len(d['arms'])==48,'three_seeds_four_sizes_four_conditions':len(pairs)==12 and all(sum(a['seed']==s and a['n_side']==n for a in d['arms'])==4 for s in (4101,7301,10703) for n in (2,4,8,16)),'root_membership_exact':all(a['members_per_root']==[a['units_per_sheet']]*2 for a in d['arms']),'independent_equation_oracle':not bad,'global_changes_other_sheet':all(x['global_a_change_max']>0 for x in pairs),'scoped_isolates_sheets':all(x['scoped_a_change_max']==0 for x in pairs),'positive_progress_below_budget':all(0<a['progress']<a['budget'] for a in d['arms']),'term_counter_conservation':term_conserve,'candidate_counter_conservation':candidate_conserve}
 out={'run_id':'vision-multi-sheet-scale-independent-audit-v1','raw_sha256':sha(RAW),'lock_sha256':sha(LOCK),'pairs':pairs,'by_size':rows,'oracle_mismatches':bad,'checks':checks,'pass':all(checks.values()),'claim_boundary':['Synthetic two-root grids and one settlement rule only.','The global fold couples roots; the root-scoped benchmark clone removes that dependence for these instances.','Counters measure runtime work for this rule family; no natural-workload frequency or general frame-locality claim follows.','No timing or production scheduler effect was measured.']}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps({'output':str(OUT.relative_to(ROOT)),'checks':checks,'pass':out['pass'],'by_size':rows},indent=2))
 if not out['pass']:raise SystemExit('independent multi-sheet scope audit failed')
if __name__=='__main__':main()

#!/usr/bin/env python3
"""Independent validation and paired bootstrap for the recognition larger-N eventization run."""
from __future__ import annotations
import hashlib, json, random, statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'evaluation/reports/substrate_problem_shape_all_transitions_recognition_larger_n_20260925.json'
LOCK=ROOT/'evaluation/substrate_capability/problem_shape_all_transitions_recognition_larger_n_lock_20260925.json'
OUT=ROOT/'evaluation/reports/substrate_problem_shape_all_transitions_recognition_larger_n_analysis_20260925.json'
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    raw=json.loads(RAW.read_text()); lock=json.loads(LOCK.read_text())
    if raw['provenance']['lock_sha256']!=sha(LOCK): raise SystemExit('lock hash mismatch')
    if raw['provenance']['locked_inputs']!=lock: raise SystemExit('locked input list mismatch')
    if raw['provenance']['locked_inputs']['runner']!=sha(ROOT/'scripts/substrate_problem_shape_all_transitions_recognition_larger_n.py'): raise SystemExit('runner drift')
    pids=[]; by_n={}
    for p in raw['pairs']:
        by_n.setdefault(str(p['N']),[]).append(p)
        for arm in p['arms'].values(): pids.append(arm['process_id'])
    if len(raw['pairs'])!=12 or len(pids)!=24 or len(set(pids))!=24: raise SystemExit('pair/process gate failed')
    summaries={}
    for n,ps in sorted(by_n.items(),key=lambda kv:int(kv[0])):
        if len(ps)!=6 or not all(p['semantic_parity'] for p in ps): raise SystemExit(f'N={n} semantic/pair gate failed')
        orders={'baseline_first':sum(p['order'][0]=='baseline' for p in ps),'candidate_first':sum(p['order'][0]=='candidate' for p in ps)}
        if orders!={'baseline_first':3,'candidate_first':3}: raise SystemExit(f'N={n} order balance failed')
        fields=['candidate_pairs','term_evaluations']
        stability={}
        for arm in ('baseline','candidate'):
            stability[arm]={k:len({p['arms'][arm][k] for p in ps})==1 for k in fields}
        if not all(v for x in stability.values() for v in x.values()): raise SystemExit(f'N={n} counters unstable')
        ratios=[p['wall_ratio'] for p in ps]; rng=random.Random(20260926+int(n)); boots=[]
        for _ in range(50000): boots.append(statistics.median(rng.choice(ratios) for _ in ratios))
        boots.sort(); b=ps[0]['arms']['baseline']; c=ps[0]['arms']['candidate']
        summaries[n]={'pair_count':6,'orders':orders,'all_semantic_parity':True,'counter_values_stable':stability,
          'wall_ratio_median':statistics.median(ratios),'wall_ratio_pair_bootstrap_95':[boots[int(.025*len(boots))],boots[min(len(boots)-1,int(.975*len(boots))) ]],
          'wall_ratio_range':[min(ratios),max(ratios)],'candidate_faster_pairs':sum(x<1 for x in ratios),
          'median_cpu_ratio':statistics.median(p['cpu_ratio'] for p in ps),
          'peak_rss_bytes_median':{a:statistics.median(p['arms'][a]['peak_rss_bytes'] for p in ps) for a in ('baseline','candidate')},
          'candidate_pairs':{'baseline':b['candidate_pairs'],'candidate':c['candidate_pairs'],'relative_reduction':1-c['candidate_pairs']/b['candidate_pairs']},
          'term_evaluations':{'baseline':b['term_evaluations'],'candidate':c['term_evaluations'],'relative_reduction':1-c['term_evaluations']/b['term_evaluations']},
          'candidate_ps_mint_pairs':c['ps_mint_pairs'],'candidate_ps_mint_terms':c['ps_mint_terms'],
          'host_index_maintenance_ns_median':statistics.median(p['arms']['candidate']['index_maintenance_ns'] for p in ps)}
    out={'schema_version':1,'analysis':'problem-shape-all-transitions-recognition-larger-n-independent-readback','raw_sha256':sha(RAW),'lock_sha256':sha(LOCK),
      'all_gates_pass':True,'unique_process_ids':True,'raw_field_correction':'Baseline ps_mint summary fields were absent from the worker and defaulted to zero; those zeros are not measurements and are excluded. Aggregate ProblemShape pair and Term counters are present and compared. Candidate per-rule ps_mint counters are retained as candidate-only diagnostics.', 'summaries_by_N':summaries,
      'interpretation_limit':raw['interpretation_limit']}
    OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n'); print(json.dumps(out,sort_keys=True)); return 0
if __name__=='__main__': raise SystemExit(main())

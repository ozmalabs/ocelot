#!/usr/bin/env python3
"""Independent finite-fact and terminal-state analysis for scale v1.2."""
from __future__ import annotations
import gzip,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'evaluation/reports/mint_termination_scale_v1_2_20261004.json.gz'
LOCK=ROOT/'evaluation/substrate_capability/mint_termination_scale_v1_2_lock_20261004.json'
OUT=ROOT/'evaluation/reports/mint_termination_scale_v1_2_analysis_20261004.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def initial_edges(n,topology):
    if topology=='cycle':return {(i,(i+1)%n) for i in range(n)}
    return {(i,j) for i in range(n) for j in range(n) if i!=j}
def main():
    with gzip.open(RAW,'rt',encoding='utf-8') as f:raw=json.load(f)
    lock=json.loads(LOCK.read_text())['locked_inputs'];results=[]
    errors=[]
    def req(ok,msg):
        if not ok:errors.append(msg)
    req(raw.get('locked_inputs')==lock==raw.get('post_run_inputs'),'source lock mismatch')
    req(raw.get('source_stable') is True,'runner source stability failed')
    req(raw.get('all_checks_pass') is True and not raw.get('failed_cases'),'runner case gate failed')
    for c in raw['cases']:
        n,m=c['n_initial_nodes'],c['m_mint_signatures'];ins=initial_edges(n,c['topology'])
        tag_values=(None,True,1,'w3');tags=[]
        for value in tag_values[:m]:
            if not any(value==earlier for earlier in tags):tags.append(value)
        expected_nodes={('Seed',json.dumps({'idx':i},sort_keys=True)) for i in range(n)}
        expected_nodes.update(('Witness',json.dumps({'tag':v},sort_keys=True)) for v in tags)
        pairs=set(ins)|{(y,w) for y in range(n+len(tags)) for w in range(n,n+len(tags))}
        expected_edges={(a,'link',b,'{}') for a,b in pairs};graph=c['actual_graph']
        got_nodes={(x['type'],json.dumps(x['attrs'],sort_keys=True)) for x in graph['nodes']}
        got_edges={(x['src'],x['type'],x['tgt'],json.dumps(x['attrs'],sort_keys=True)) for x in graph['edges']}
        e0=len(ins);bound=m+(n+m)**2-e0
        checks={'checker_accepts':c['analyzer']['accepted'],'native_fixed_point':c['native_report']['status']=='fixed_point',
          'exact_nodes':got_nodes==expected_nodes,'exact_edges':got_edges==expected_edges,
          'analyzer_bound_matches_formula':c['analyzer']['progress_steps_upper_bound']==bound,
          'native_progress_within_bound':c['native_report']['progress_steps']<=bound,
          'budget_not_exceeded':c['native_report']['budget_overshoot']==0,'runner_case_passes':c['all_checks_pass'],
          'timing_positive':c['execution_wall_ns']>0}
        req(all(checks.values()),f"case failed: {c['case_id']}")
        results.append({'case_id':c['case_id'],'n':n,'m':m,'topology':c['topology'],'replicate':c['replicate'],
          'bound':bound,'progress_steps':c['native_report']['progress_steps'],'passes':c['native_report']['passes_completed'],
          'execution_wall_ns':c['execution_wall_ns'],'node_count':c['actual_node_count'],'edge_count':c['actual_edge_count'],'checks':checks})
    expected={f'n{n}_m{m}_{topo}_r{r}' for n in (4,16,64,128,256) for m in (1,2,4) for topo in ('cycle','dense_no_self') for r in (1,2,3)}
    req({r['case_id'] for r in results}==expected,'expected 90-case matrix mismatch')
    from collections import defaultdict
    cells=defaultdict(list)
    for r in results:cells[(r['n'],r['m'],r['topology'])].append(r)
    summary=[]
    for (n,m,topo),rs in sorted(cells.items()):
        times=sorted(r['execution_wall_ns'] for r in rs);summary.append({'n':n,'m':m,'topology':topo,'replicates':len(rs),'median_execution_wall_ns':times[1],
          'progress_steps':sorted(set(r['progress_steps'] for r in rs)),'bound':sorted(set(r['bound'] for r in rs)),'edge_count':rs[0]['edge_count']})
    out={'schema':'MintTerminationScaleV1_2Analysis','passed':not errors,'errors':errors,'raw_sha256':sha(RAW),'lock_sha256':sha(LOCK),
      'case_count':len(results),'cell_count':len(summary),'cases':results,'cell_summary':summary,
      'claim_boundary':raw['design']['claim_limit']}
    OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'passed':out['passed'],'errors':errors,'case_count':len(results),'cell_count':len(summary),'raw_sha256':out['raw_sha256']},indent=2))
    return int(bool(errors))
if __name__=='__main__':raise SystemExit(main())

#!/usr/bin/env python3
"""Independent lifecycle/resolution gates for proposal scale panel v1."""
from __future__ import annotations

import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/"evaluation/reports/conflict_proposal_lifecycle_scale_v1_20260928.json"
OUT=ROOT/"evaluation/reports/conflict_proposal_lifecycle_scale_v1_analysis_20260928.json"
SIZES=(2,4,8,16,32,64)


def main():
 d=json.loads(RAW.read_text());runs=d['runs']
 gates={"three_workers":len(runs)==3,
        "locked_inputs_match":all(r['started_inputs']==d['locked_inputs'] for r in runs),
        "all_12_cells_each":all(len(r['cells'])==12 for r in runs),
        "sizes_and_distributions_complete":all({(c['n'],c['distribution']) for c in r['cells']}=={(n,x) for n in SIZES for x in ('unique_max','tied_max')} for r in runs)}
 normalized=[]
 for r in runs:
  cs=[]
  for c in r['cells']:
   n=c['n'];dist=c['distribution'];gen=c['generation']['report'];rep=c['idempotent_resettle']['report'];res=c['resolution']
   gates[f"{r['worker_id']}_{n}_{dist}_generation_fixedpoint"]=(gen['status']=='fixed_point' and c['proposal_labels']==[f'p{i:03d}' for i in range(n)] and c['proposal_edge_count']==n)
   gates[f"{r['worker_id']}_{n}_{dist}_idempotent"]=(rep['status']=='fixed_point' and rep['progress_steps']==0 and c['idempotent_resettle']['metrics'].get('graph_writes',0)==0)
   if dist=='unique_max':
    want=f'p{n-1:03d}'
    gates[f"{r['worker_id']}_{n}_unique_resolves"]=(res['report']['status']=='fixed_point' and res['selected']==want)
   else:
    top={f'p{n-2:03d}',f'p{n-1:03d}'}
    gates[f"{r['worker_id']}_{n}_tie_not_silent"]=(res['report']['status']=='repeated_graph_state' and res['selected'] in top)
   maxover=res['metrics'].get('term_eval:MaxOver',0)
   gates[f"{r['worker_id']}_{n}_{dist}_maxover_measured"]=(maxover>0)
   cs.append({"n":n,"distribution":dist,"generation_status":gen['status'],"generation_progress":gen['progress_steps'],
              "proposal_count":len(c['proposal_labels']),"idempotent_progress":rep['progress_steps'],
              "resolution_status":res['report']['status'],"selected":res['selected'],
              "maxover_evaluations":maxover,"term_evaluations":res['metrics'].get('term_evals_total',0),
              "candidate_tests":res['metrics'].get('cand_tested',0),
              "generation_metrics":c['generation']['metrics'],"resolution_metrics":res['metrics'],
              "elapsed_ns":{"generation":c['generation']['elapsed_ns'],"repeat":c['idempotent_resettle']['elapsed_ns'],"resolution":res['elapsed_ns']}})
  normalized.append(cs)
 # Counts should reproduce across fresh workers; wall time is deliberately excluded.
 signature=lambda rows:[[{k:v for k,v in c.items() if k!="elapsed_ns"} for c in row] for row in rows]
 gates['integer_work_counts_replicate']=signature(normalized)[0]==signature(normalized)[1]==signature(normalized)[2]
 summary=[]
 for n in SIZES:
  unique=next(c for c in normalized[0] if c['n']==n and c['distribution']=='unique_max')
  tie=next(c for c in normalized[0] if c['n']==n and c['distribution']=='tied_max')
  summary.append({"n":n,"generation_progress":unique['generation_progress'],
                  "generation_candidate_tests":unique['generation_metrics'].get('cand_tested',0),
                  "unique_resolver_maxover_evals":unique['maxover_evaluations'],
                  "unique_resolver_term_evals":unique['term_evaluations'],
                  "tie_resolver_status":tie['resolution_status'],"tie_selected":tie['selected'],
                  "tie_resolver_maxover_evals":tie['maxover_evaluations']})
 report={"analysis":"Conflict proposal lifecycle scale v1","all_gates_pass":all(gates.values()),"gates":gates,
         "scale_summary":summary,"cells_by_worker":normalized,
         "interpretation":"Proposal nodes are deduplicated on repeated closure. The basic MaxOver resolver selects a unique maximum, while tied maxima produce repeated graph state rather than a stable ambiguity result. Counted resolver work is reported by N; this panel is fixture-specific.",
         "limits":["Does not test learned proposal generation or semantic score quality.",
                  "The tied-max result is for the unguarded selector and does not test an explicit ambiguity-aware resolver.",
                  "Scale is authored through N=64; no asymptotic claim beyond the measured panel."]}
 OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
 print(json.dumps({"all_gates_pass":report['all_gates_pass'],"gates_failed":[k for k,v in gates.items() if not v],"scale_summary":summary,"analysis":str(OUT.relative_to(ROOT))},indent=2))
 if not report['all_gates_pass']:raise SystemExit('proposal lifecycle scale gate failed')


if __name__=="__main__":main()

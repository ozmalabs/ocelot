#!/usr/bin/env python3
"""Independent analysis of rule conflict policy options."""
from __future__ import annotations

import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/"evaluation/reports/rule_conflict_policy_comparison_v1_20260928.json"
OUT=ROOT/"evaluation/reports/rule_conflict_policy_comparison_v1_analysis_20260928.json"
ORDERS=("A_then_B","B_then_A")
POLICIES=("metadata_order","proposal_nodes")


def main():
 d=json.loads(RAW.read_text());runs=d['runs']
 gates={"three_workers":len(runs)==3,
        "locked_inputs_match":all(r['started_inputs']==d['locked_inputs'] for r in runs),
        "four_cells_each":all(len(r['cells'])==4 for r in runs),
        "all_policy_order_cells":all({(c['policy'],c['order']) for c in r['cells']}=={(p,o) for p in POLICIES for o in ORDERS} for r in runs)}
 signatures=[]
 for r in runs:
  cells={(c['policy'],c['order']):c for c in r['cells']}; sig={}
  for order in ORDERS:
   c=cells[('metadata_order',order)]
   want=2 if order=='A_then_B' else 1
   gates[f"metadata_{order}_still_cycles_{r['worker_id']}"]=(c['termination']['status']=='repeated_graph_state' and c['accepted']==want)
   gates[f"exact_conflict_rejected_{order}_{r['worker_id']}"]=(c['exact_reject_prototype']['decision']=='reject_before_install' and bool(c['exact_reject_prototype']['conflicting_writes']))
   p=cells[('proposal_nodes',order)]
   gates[f"proposal_{order}_fixedpoint_{r['worker_id']}"]=(p['termination']['status']=='fixed_point' and p['proposal_nodes']==[['A',1],['B',2]] and p['proposal_edge_count']==2 and p['accepted'] is None)
   sig[order]={"metadata_order":{"status":c['termination']['status'],"final":c['accepted'],"calls":c['callback_count']},
               "proposal_nodes":{"status":p['termination']['status'],"proposals":p['proposal_nodes'],"edges":p['proposal_edge_count'],"calls":p['callback_count']}}
  signatures.append(sig)
 gates['replicated_across_workers']=signatures[0]==signatures[1]==signatures[2]
 report={"analysis":"Rule conflict policy comparison v1","all_gates_pass":all(gates.values()),"gates":gates,
         "results":signatures[0],
         "interpretation":"Global rule order metadata does not prevent oscillation or override insertion order. A narrow exact-match admission predicate can detect/reject the synthetic conflict before installation, but is only a harness prototype. Proposal nodes reach fixed point and preserve both values without resolving them.",
         "limits":["No conflict policy is implemented in the substrate by this probe.",
                  "The rejection prototype covers only exact same match/where and conflicting direct attribute writes.",
                  "Conflict proposal nodes surface alternatives; downstream selection remains an explicit unresolved task."]}
 OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
 print(json.dumps({"all_gates_pass":report['all_gates_pass'],"gates":gates,"results":report['results'],"analysis":str(OUT.relative_to(ROOT))},indent=2))
 if not report['all_gates_pass']:raise SystemExit('policy comparison gate failed')


if __name__=="__main__":main()

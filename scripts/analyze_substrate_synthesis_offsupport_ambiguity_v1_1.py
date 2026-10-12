#!/usr/bin/env python3
"""Independent integrity and analytic-oracle analysis for off-support synthesis."""
from __future__ import annotations
import json, math, random
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/"evaluation/reports/synthesis_offsupport_ambiguity_v1_1_20261001_raw.jsonl"
OUT=ROOT/"evaluation/reports/synthesis_offsupport_ambiguity_v1_1_20261001_analysis.json"
TASKS={
 "ambiguous_square":{"training":[[0,0],[1,1]],"heldout":[-3,-2,2,3]},
 "disambiguated_square":{"training":[[-2,4],[-1,1],[0,0],[1,1],[2,4]],"heldout":[-4,-3,3,4]},
 "contradictory_square":{"training":[[0,0],[0,1],[1,1]],"heldout":[-1,2]},
}
SEED=20261001;REPS=5

def program_text(row):
 programs=row.get("programs",[])
 return programs[0].get("program_json") if len(programs)==1 else None

def classify_ambiguous(text):
 if not isinstance(text,str):return "missing_or_multiple_programs"
 try:tree=json.loads(text)
 except Exception:return "invalid_program_json"
 rendered=json.dumps(tree,sort_keys=True)
 if '"type": "Times"' in rendered or '"type":"Times"' in rendered:return "square_like_times"
 if '"name": "value"' in rendered or '"name":"value"' in rendered:return "identity_like"
 return "other_program"

def analyze():
 lines=[json.loads(x) for x in RAW.read_text().splitlines() if x.strip()]
 headers=[x for x in lines if x.get("kind")=="header"];footers=[x for x in lines if x.get("kind")=="footer"]
 rows=[x for x in lines if x.get("kind")=="worker"]
 header=headers[0] if len(headers)==1 else {};footer=footers[0] if len(footers)==1 else {}
 expected=[(t,r) for r in range(REPS) for t in TASKS]
 random.Random(SEED).shuffle(expected)
 schedule=header.get("schedule",[])
 grouped={t:[r for r in rows if r.get("task")==t] for t in TASKS}
 gates={
  "one_header_and_footer":len(headers)==1 and len(footers)==1,
  "complete_unique_workers":len(rows)==15 and all(isinstance(r.get("pid"),int) for r in rows) and len({r.get("pid") for r in rows})==15 and not any(r.get("worker_failed") for r in rows),
  "locked_randomized_schedule":schedule==[list(x) for x in expected] and [(r.get("task"),r.get("repetition")) for r in rows]==expected,
  "five_repetitions_per_task":all(len(grouped[t])==5 and sorted(r.get("repetition") for r in grouped[t])==list(range(REPS)) for t in TASKS),
  "source_native_stability":bool(header.get("lock")) and footer.get("source_native_stable") is True and all(r.get("source_native_stable") is True for r in rows),
  "disambiguated_square_exact_transfer":all(r.get("status")=="accepted" and len(r.get("heldout",[]))==4 and all(h.get("predicted")==h.get("input")**2 and h.get("expected")==h.get("input")**2 and h.get("exact") for h in r.get("heldout",[])) for r in grouped["disambiguated_square"]),
  "contradictory_examples_refused_at_cap":all(r.get("status")=="gapped" and r.get("facts",{}).get("ps_enum_tested")==200000 and r.get("program_count")==0 for r in grouped["contradictory_square"]),
  "ambiguous_arm_fully_classified":all((r.get("status")=="accepted" and r.get("program_count")==1 and len(r.get("heldout",[]))==4 and [h.get("input") for h in r["heldout"]]==TASKS["ambiguous_square"]["heldout"] and all(h.get("expected")==h.get("input")**2 for h in r["heldout"])) or (r.get("status")=="gapped" and r.get("program_count")==0 and not r.get("heldout")) for r in grouped["ambiguous_square"]),
  "complete_analytic_heldout_capture":all([h.get("input") for h in r.get("heldout",[])]==TASKS["disambiguated_square"]["heldout"] and all(h.get("expected")==h.get("input")**2 for h in r.get("heldout",[])) for r in grouped["disambiguated_square"]),
  "finite_cost_capture":all(isinstance(r.get("pump_wall_ns"),(int,float)) and r["pump_wall_ns"]>0 and isinstance(r.get("peak_rss_bytes"),(int,float)) and r["peak_rss_bytes"]>0 for r in rows),
 }
 ambiguity=[]
 for row in grouped["ambiguous_square"]:
  preds=[h.get("predicted") for h in row.get("heldout",[])];exp=[x*x for x in TASKS["ambiguous_square"]["heldout"]]
  ambiguity.append({"repetition":row.get("repetition"),"status":row.get("status"),"candidate_count":row.get("facts",{}).get("ps_enum_tested"),"selected_program_class":classify_ambiguous(program_text(row)),"heldout_predictions":preds,"heldout_exact_count":sum(p==y for p,y in zip(preds,exp)),"false_generalization_count":sum(p is not None and p!=y for p,y in zip(preds,exp))})
 summary={"ambiguous_square":{"accepted":sum(r.get("status")=="accepted" for r in grouped["ambiguous_square"]),"heldout_exact_total":sum(r["heldout_exact_count"] for r in ambiguity),"heldout_total":sum(len(TASKS["ambiguous_square"]["heldout"]) for _ in ambiguity),"selected_program_classes":[r["selected_program_class"] for r in ambiguity],"workers":ambiguity},"disambiguated_square":{"accepted":sum(r.get("status")=="accepted" for r in grouped["disambiguated_square"]),"exact_points":sum(h.get("exact",False) for r in grouped["disambiguated_square"] for h in r.get("heldout",[])),"total_points":20,"median_candidates":sorted(r.get("facts",{}).get("ps_enum_tested",0) for r in grouped["disambiguated_square"])[len(grouped["disambiguated_square"])//2]},"contradictory_square":{"gapped":sum(r.get("status")=="gapped" for r in grouped["contradictory_square"]),"cap_hits":sum(r.get("facts",{}).get("ps_enum_tested")==200000 for r in grouped["contradictory_square"]),"gap_reasons":[r.get("gap_reason") for r in grouped["contradictory_square"]]}}
 result={"schema":"SubstrateSynthesisOffsupportAmbiguityV1Analysis","gates":gates,"summary":summary,"source_native_stable":footer.get("source_native_stable"),"worker_count":len(rows)}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
 print(json.dumps(result,indent=2,sort_keys=True));return 0 if all(gates.values()) else 1

if __name__=="__main__":raise SystemExit(analyze())

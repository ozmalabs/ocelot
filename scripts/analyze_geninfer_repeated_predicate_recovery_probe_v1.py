#!/usr/bin/env python3
"""Independent balance, construction, and semantic summary for recovery factorial."""
import hashlib,json
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/"evaluation/reports/substrate_geninfer_repeated_predicate_recovery_v1_20260926.json"
LOCK=ROOT/"docs/research/engine_substrate/SUBSTRATE_GENINFER_REPEATED_PREDICATE_RECOVERY_PREREG_20260926.md"
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 d=json.loads(RAW.read_text()); checks={"protocol_hash":d["source_sha256"]["docs/research/engine_substrate/SUBSTRATE_GENINFER_REPEATED_PREDICATE_RECOVERY_PREREG_20260926.md"]==sha(LOCK),"runner_hash":d["source_sha256"]["scripts/geninfer_repeated_predicate_recovery_probe_v1.py"]==sha(ROOT/"scripts/geninfer_repeated_predicate_recovery_probe_v1.py"),"native_hash":d["native"]["sha256"]==sha(Path(d["native"]["path"])),"sample_count":len(d["samples"])==75}
 cells=defaultdict(list)
 for x in d["samples"]:
  g,p,r=x["group"],x["perturbation"],x["repetition"]; m=d["inputs"]["matrix"]; pts=[(0,0),(1,0),(2,0),(0,2)]; p0=d["inputs"]["groups"][g]; shifts=d["inputs"]["perturbations"][p]; a,b,c,e=m
  base=[];goal=[]
  for i,(u,v) in enumerate(pts):
   pred="p0" if i in p0 else "p1"; base.append([pred,u,v,"red"]); goal.append([pred,a*u+b*v+(shifts[p0.index(i)] if i in p0 else 0),c*u+e*v,"red"])
  checks[f"construction_{g}_{p}_{r}"]=x["base"]==base and x["goal"]==goal
  cells[g,p].append(x["observation"])
 summaries=[]
 for (g,p),obs in sorted(cells.items()):
  exact=sum(o["matrix"]==d["inputs"]["matrix"] for o in obs); explained=sum(bool(o["explained"]) for o in obs)
  summaries.append({"group":g,"perturbation":p,"n":len(obs),"exact_generator_recovery":exact,"decomposition_accepted":explained,"selected_matrices":sorted({json.dumps(o["matrix"],separators=(",",":")) for o in obs}),"residual_dims":sorted({o["residual_dims"] for o in obs}),"transform_signatures":sorted({json.dumps(o["transforms"],sort_keys=True,separators=(",",":")) for o in obs}),"deterministic":len({json.dumps(o,sort_keys=True) for o in obs})==1,"all_checked_6560":all(o["checked"]==6560 for o in obs)})
 checks["balanced_15_cells"] = len(cells)==15 and all(len(v)==5 for v in cells.values())
 checks["positive_exact_and_no_residual"] = all(s["exact_generator_recovery"]==5 and s["decomposition_accepted"]==5 and s["residual_dims"]==[0] for s in summaries if s["perturbation"]=="positive")
 checks["all_calls_checked_6560"] = all(s["all_checked_6560"] for s in summaries)
 checks["repeat_determinism"] = all(s["deterministic"] for s in summaries)
 out={"raw_sha256":sha(RAW),"checks":checks,"all_checks_pass":all(checks.values()),"summaries":summaries}
 path=ROOT/"evaluation/reports/substrate_geninfer_repeated_predicate_recovery_v1_analysis_20260926.json";path.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n");print(json.dumps(out,indent=2))
if __name__=="__main__":main()

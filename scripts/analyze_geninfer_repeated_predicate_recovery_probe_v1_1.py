#!/usr/bin/env python3
"""Amended descriptive analysis preserving the v1 fixed-count gate failure."""
import hashlib,json
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/"evaluation/reports/substrate_geninfer_repeated_predicate_recovery_v1_20260926.json"
AMEND=ROOT/"docs/research/engine_substrate/SUBSTRATE_GENINFER_REPEATED_PREDICATE_RECOVERY_V1_1_AMENDMENT_20260926.md"
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 d=json.loads(RAW.read_text()); cells=defaultdict(list); checks={"runner_hash":d["source_sha256"]["scripts/geninfer_repeated_predicate_recovery_probe_v1.py"]==sha(ROOT/"scripts/geninfer_repeated_predicate_recovery_probe_v1.py"),"amendment_exists":AMEND.exists(),"native_hash":d["native"]["sha256"]==sha(Path(d["native"]["path"])),"sample_count":len(d["samples"])==75}
 for x in d["samples"]:cells[x["group"],x["perturbation"]].append(x)
 summaries=[]
 for (g,p),xs in sorted(cells.items()):
  obs=[x["observation"] for x in xs]; checked=sorted({o["checked"] for o in obs}); exact=sum(o["matrix"]==d["inputs"]["matrix"] for o in obs); accepted=sum(bool(o["explained"]) for o in obs)
  summaries.append({"group":g,"perturbation":p,"n":len(xs),"exact_generator_recovery":exact,"decomposition_accepted":accepted,"selected_matrices":sorted({json.dumps(o["matrix"],separators=(",",":")) for o in obs}),"residual_dims":sorted({o["residual_dims"] for o in obs}),"transforms":sorted({json.dumps(o["transforms"],sort_keys=True,separators=(",",":")) for o in obs}),"deterministic":len({json.dumps(o,sort_keys=True) for o in obs})==1,"checked_values":checked,"checked_constant_within_cell":len(checked)==1,"all_calls_checked_positive_integer":all(isinstance(o["checked"],int) and o["checked"]>0 for o in obs)})
 checks["balanced_15_cells"]=len(cells)==15 and all(len(v)==5 for v in cells.values())
 checks["positive_exact_no_residual_and_6560"]=all(s["exact_generator_recovery"]==s["decomposition_accepted"]==5 and s["residual_dims"]==[0] and s["checked_values"]==[6560] for s in summaries if s["perturbation"]=="positive")
 checks["perturbed_checked_counts_positive_and_stable"]=all(s["checked_constant_within_cell"] and s["all_calls_checked_positive_integer"] for s in summaries)
 checks["deterministic_within_cell"]=all(s["deterministic"] for s in summaries)
 out={"raw_sha256":sha(RAW),"amendment_sha256":sha(AMEND),"analyzer_sha256":sha(Path(__file__)),"checks":checks,"all_amended_checks_pass":all(checks.values()),"v1_fixed_6560_gate_failure_preserved":sorted({o["checked"] for x in d["samples"] for o in [x["observation"]]})!=[6560],"summaries":summaries}
 path=ROOT/"evaluation/reports/substrate_geninfer_repeated_predicate_recovery_v1_1_analysis_20260926.json";path.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n");print(json.dumps(out,indent=2))
if __name__=="__main__":main()

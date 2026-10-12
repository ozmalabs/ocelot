#!/usr/bin/env python3
"""Final count-gate correction for the independently analyzed v2 capture."""
import hashlib,importlib.util,json,sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
SELF=Path(__file__).resolve()
CAP=ROOT/"evaluation/reports/ls20_decision_ambiguity_noise_v2/capture.json"
PREVIOUS=ROOT/"evaluation/reports/ls20_decision_ambiguity_noise_v2_1_analysis.json"
PREVIOUS_ANALYZER=ROOT/"evaluation/substrate_capability/analyze_ls20_decision_ambiguity_noise_v2_1.py"
PREVIOUS_LOCK=ROOT/"evaluation/substrate_capability/ls20_decision_ambiguity_noise_v2_1_analysis_lock_20260928.json"
WORKER=ROOT/"evaluation/substrate_capability/ls20_decision_ambiguity_noise_v2.py"
WORKER_LOCK=ROOT/"evaluation/substrate_capability/ls20_decision_ambiguity_noise_v2_lock_20260928.json"
AMEND=ROOT/"docs/research/engine_substrate/SUBSTRATE_LS20_DECISION_AMBIGUITY_NOISE_V2_2_AMENDMENT_20260928.md"
LOCK=ROOT/"evaluation/substrate_capability/ls20_decision_ambiguity_noise_v2_2_analysis_lock_20260928.json"
OUT=ROOT/"evaluation/reports/ls20_decision_ambiguity_noise_v2_2_analysis.json"
EXPECTED={"rotate:1","rotate:2","rotate:3","reflect:c","reflect:r","recolour"}

def rec(p):
    b=p.read_bytes();return {"path":p.relative_to(ROOT).as_posix(),"bytes":len(b),"sha256":hashlib.sha256(b).hexdigest()}

def audit_inputs():
    return {"analyzer":rec(SELF),"amendment":rec(AMEND),"capture":rec(CAP),"previous_analysis":rec(PREVIOUS),
      "previous_analyzer":rec(PREVIOUS_ANALYZER),"previous_analysis_lock":rec(PREVIOUS_LOCK),
      "worker":rec(WORKER),"worker_lock":rec(WORKER_LOCK)}

def main():
    if sys.argv[1:]==["--lock"]:
        if LOCK.exists():raise SystemExit("refusing to overwrite v2.2 analysis lock")
        LOCK.write_text(json.dumps(audit_inputs(),indent=2,sort_keys=True)+"\n");print(LOCK.relative_to(ROOT));return
    locked=json.loads(LOCK.read_text())
    if audit_inputs()!=locked:raise SystemExit("analysis correction lock drift")
    report=json.loads(PREVIOUS.read_text())
    pspec=importlib.util.spec_from_file_location("noise_v2_1_auditor",PREVIOUS_ANALYZER)
    previous=importlib.util.module_from_spec(pspec);assert pspec and pspec.loader;pspec.loader.exec_module(previous)
    previous_lock=json.loads(PREVIOUS_LOCK.read_text())
    if previous.audit_inputs()!=previous_lock:raise SystemExit("v2.1 analysis lock drift")
    cap=json.loads(CAP.read_text());wspec=importlib.util.spec_from_file_location("noise_v2_worker",WORKER)
    worker=importlib.util.module_from_spec(wspec);assert wspec and wspec.loader;wspec.loader.exec_module(worker)
    execution_lock=json.loads(WORKER_LOCK.read_text())
    worker_stable=worker.input_lock()==execution_lock==cap.get("locked_inputs")==cap.get("post_run_inputs")
    blocks=report["operator_counts_by_seed_block"]
    balanced=(len(blocks)==32 and all(set(v)==EXPECTED and all(n in (3,4) for n in v.values()) for v in blocks.values()))
    prior_gates=report["integrity_gates"]
    other_gates={k:v for k,v in prior_gates.items() if k!="all_16_operator_blocks_balanced"}
    if not all(other_gates.values()):raise SystemExit("prior report has another failed integrity gate; retain and investigate")
    gates=dict(other_gates);gates["all_32_operator_blocks_balanced"]=balanced;gates["worker_source_build_lock_stable"]=worker_stable
    report["analysis_version"]="v2.2 corrected 32-block completeness count"
    report["integrity_gates"]=gates;report["all_integrity_gates_pass"]=all(gates.values())
    report["analysis_correction_lock"]=locked
    report["operator_block_count_correction"]={"prior_expected":16,"design_expected":32,"observed":len(blocks),"all_six_operators_balanced":balanced}
    OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"output":str(OUT.relative_to(ROOT)),"integrity_gates":gates,
      "operator_blocks":len(blocks),"all_six_operators_balanced":balanced,"all_gates_pass":all(gates.values())},indent=2))

if __name__=="__main__":main()

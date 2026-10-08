#!/usr/bin/env python3
"""Corrected independent analysis for LS20 noise v2; worker inputs unchanged."""
import hashlib,importlib.util,json
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
CAP=ROOT/"evaluation/reports/ls20_decision_ambiguity_noise_v2/capture.json"
WORKER_LOCK=ROOT/"evaluation/substrate_capability/ls20_decision_ambiguity_noise_v2_lock_20260928.json"
INITIAL=ROOT/"evaluation/reports/ls20_decision_ambiguity_noise_v2_independent_analysis.json"
AMENDMENT=ROOT/"docs/research/engine_substrate/SUBSTRATE_LS20_DECISION_AMBIGUITY_NOISE_V2_AMENDMENT_20260928.md"
AUDIT_LOCK=ROOT/"evaluation/substrate_capability/ls20_decision_ambiguity_noise_v2_1_analysis_lock_20260928.json"
RUN=ROOT/"evaluation/substrate_capability/ls20_decision_ambiguity_noise_v2.py"
OLD_ANALYZER=ROOT/"evaluation/substrate_capability/analyze_ls20_decision_ambiguity_noise_v2.py"
OUT=ROOT/"evaluation/reports/ls20_decision_ambiguity_noise_v2_1_analysis.json"
SELF=Path(__file__).resolve()

def record(path):
    raw=path.read_bytes()
    return {"path":path.relative_to(ROOT).as_posix(),"bytes":len(raw),"sha256":hashlib.sha256(raw).hexdigest()}

def audit_inputs():
    return {"analyzer":record(SELF),"amendment":record(AMENDMENT),"capture":record(CAP),
      "worker_lock":record(WORKER_LOCK),"initial_analysis":record(INITIAL),"original_analyzer":record(OLD_ANALYZER)}

def main():
    cap=json.loads(CAP.read_text());worker_lock=json.loads(WORKER_LOCK.read_text())
    if sysargs()==["--lock"]:
        if AUDIT_LOCK.exists():raise SystemExit("refusing to overwrite analysis lock")
        AUDIT_LOCK.write_text(json.dumps(audit_inputs(),indent=2,sort_keys=True)+"\n");print(AUDIT_LOCK.relative_to(ROOT));return
    audit=json.loads(AUDIT_LOCK.read_text())
    if audit_inputs()!=audit:raise SystemExit("analysis/capture amendment lock drift")
    spec=importlib.util.spec_from_file_location("noise_v2_original_independent_helpers",OLD_ANALYZER)
    old=importlib.util.module_from_spec(spec);assert spec and spec.loader;spec.loader.exec_module(old)
    rspec=importlib.util.spec_from_file_location("noise_v2_worker",RUN)
    runner=importlib.util.module_from_spec(rspec);assert rspec and rspec.loader;rspec.loader.exec_module(runner)
    worker_stable=runner.input_lock()==worker_lock==cap.get("locked_inputs")==cap.get("post_run_inputs")
    all_rows=[r for c in cap.get("cells",[]) for r in c["records"]]
    digests=[];errors=[];route_errors=[];blocks={};groups={}
    expected={"rotate:1","rotate:2","rotate:3","reflect:c","reflect:r","recolour"}
    for cell in cap.get("cells",[]):
        p=cell["parameters"];rows=cell["records"];ops=Counter()
        for row in rows:
            sc=row["scenario"]
            if sc["family"]=="recolour":operator="recolour"
            else:operator=f"{sc['family']}:{sc['param']}"
            ops[operator]+=1
            if row.get("required_operator")!=sc["family"]:errors.append(p["name"]+":family_label")
            digest=hashlib.sha256(json.dumps(sc,sort_keys=True,separators=(",",":")).encode()).hexdigest();digests.append(digest)
            if digest!=row.get("scenario_sha256"):errors.append(digest+":digest")
            req=old.key(sc["family"],sc["param"])
            if req!=sc.get("req_key") or old.apply(sc["symbol_cells"],sc["family"],sc["param"])!=old.norm(sc["goal_cells"]):errors.append(digest+":transform")
            matching=[s for s in sc["stations"] if s.get("key")==req]
            if len(matching)!=1 or matching[0].get("family")!=sc["family"] or matching[0].get("param")!=sc["param"]:errors.append(digest+":station")
            if len(sc["stations"])!=p["stations"]:errors.append(digest+":station_count")
            walls={tuple(x) for x in sc["walls"]};targets=[sc["goal_rc"]]+[(s["r"],s["c"]) for s in sc["stations"]]
            if not all(old.reachable(sc["avatar_rc"],t,16,16,walls) for t in targets):route_errors.append(digest)
            for item in row["pair"]["outcomes"].values():
                r=item["result"]
                if bool(r["win"])!=(r["reason"]=="delivered"):errors.append(digest+":terminal")
            groups.setdefault((p["stations"],p["sigma"]),[]).append(row)
        blocks[p["name"]]=dict(ops)
        if len(rows)!=20 or set(ops)!=expected or any(v not in (3,4) for v in ops.values()):errors.append(p["name"]+":operator_balance")
    strata={};pkeys=[];ps=[]
    for stations,sigma in sorted(groups):
        rows=groups[(stations,sigma)];arms,paired=old.metrics(rows);seed_details={}
        for block in (1,2,3,4):
            sub=[r for c in cap["cells"] if c["parameters"]["stations"]==stations and c["parameters"]["sigma"]==sigma and c["parameters"]["block"]==block for r in c["records"]]
            a,q=old.metrics(sub);seed_details[str(block)]={"n":len(sub),"arms":a,"paired":q}
        name=f"stations{stations}_sigma{sigma}";strata[name]={"stations":stations,"sigma":sigma,"n":len(rows),"seed_blocks":seed_details,"arms":arms,"paired":paired}
        pkeys.append(name);ps.append(paired["exact_mcnemar_p"])
    for k,p in zip(pkeys,old.holm(ps)):strata[k]["paired"]["holm_adjusted_p_across_eight_strata"]=p
    gates={"capture_complete":cap.get("capture_status")=="complete","worker_source_build_lock_stable":worker_stable,
      "native_extension_fresh":not worker_lock.get("native_build_stale_reasons"),"exactly_640_unique_worlds":len(all_rows)==640 and len(set(digests))==640,
      "all_scenario_task_and_terminal_oracles_pass":not errors,"all_goal_and_station_routes_reachable":not route_errors,
      "all_16_operator_blocks_balanced":len(blocks)==16 and all(set(x)==expected and all(v in (3,4) for v in x.values()) for x in blocks.values()),
      "all_eight_station_noise_strata_have_80_worlds":len(groups)==8 and all(len(x)==80 for x in groups.values())}
    report={"run_id":cap.get("run_id"),"analysis_version":"v2.1 corrected operator balance audit",
      "analysis_audit_lock":audit,"n_scenarios":len(all_rows),"strata":strata,"operator_counts_by_seed_block":blocks,
      "integrity_gates":gates,"all_integrity_gates_pass":all(gates.values()),"process":cap.get("process"),
      "oracle_errors":errors,"route_errors":route_errors,"claim_boundary":cap.get("claim_boundary")}
    OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"output":str(OUT.relative_to(ROOT)),"integrity_gates":gates,"strata":{k:{
       "clean_success":v["arms"]["clean"]["successes"],"noisy_success":v["arms"]["noisy"]["successes"],
       "recognition_exact":v["arms"]["noisy"]["recognition_exact"],"refusal":v["arms"]["noisy"]["recognition_refusal"],
       "wrong_key":v["arms"]["noisy"]["recognition_wrong_key"],"p_holm":v["paired"]["holm_adjusted_p_across_eight_strata"]} for k,v in strata.items()}},indent=2))

def sysargs():
    import sys
    return sys.argv[1:]

if __name__=="__main__":main()

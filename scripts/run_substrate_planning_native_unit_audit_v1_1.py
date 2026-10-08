#!/usr/bin/env python3
"""Run the five preregistered bounded-planner native unit tests with provenance."""
import hashlib, json, os, re, subprocess, sys, sysconfig
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/"scripts")]
from substrate_run_manifest import capture_run_manifest, finish_console_capture, start_console_capture

RUN_ID="substrate_planning_native_unit_audit_v1_1_20260928"
PROTOCOL="docs/research/engine_substrate/SUBSTRATE_PLANNING_NATIVE_UNIT_AUDIT_PREREG_20260928.md"
AMENDMENT="docs/research/engine_substrate/SUBSTRATE_PLANNING_NATIVE_UNIT_AUDIT_V1_1_AMENDMENT_20260928.md"
OUT=ROOT/f"evaluation/reports/{RUN_ID}.json"
LOG_DIR=ROOT/"evaluation/run_logs"
CASES=(
 "p2_bounded::tests::preserves_equal_minima_as_tie",
 "p2_bounded::tests::fails_closed_for_incomplete_prediction_set",
 "p2_bounded::tests::maximum_intervention_removes_over_budget_candidates",
 "p2_native::tests::mechanics_control_real_transition_and_not_submitted_witnesses",
 "p2_native::tests::maximum_intervention_excludes_over_budget_actions_in_worker_and_evaluator",
)
SOURCES=("runners/dsl/src/lib.rs","runners/dsl/src/p2_bounded.rs","runners/dsl/src/p2_native.rs")
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    if OUT.exists(): raise SystemExit(f"refusing to overwrite {OUT.relative_to(ROOT)}")
    LOG_DIR.mkdir(parents=True,exist_ok=True)
    libdir=sysconfig.get_config_var("LIBDIR");libname=sysconfig.get_config_var("LDLIBRARY")
    if not libdir or not libname or not libname.startswith("lib"):
        raise SystemExit("active Python does not expose a usable LIBDIR/LDLIBRARY")
    os.environ["RUSTFLAGS"]=" ".join(["-C",f"link-arg=-L{libdir}","-C",f"link-arg=-l{libname[3:].split(".so")[0].split(".dylib")[0]}"])
    cap=start_console_capture(RUN_ID); started=datetime.now(timezone.utc).isoformat(); records=[]
    for idx,name in enumerate(CASES,1):
        argv=["cargo","test","--lib",name,"--","--exact"]
        cp=subprocess.run(argv,cwd=ROOT/"runners/dsl",text=True,capture_output=True)
        out_path=LOG_DIR/f"{RUN_ID}_{idx}.stdout.log"; err_path=LOG_DIR/f"{RUN_ID}_{idx}.stderr.log"
        out_path.write_text(cp.stdout);err_path.write_text(cp.stderr)
        combined=cp.stdout+"\n"+cp.stderr
        exact_one=(re.search(rf"^test\s+{re.escape(name)}\s+\.\.\.\s+ok$",cp.stdout,re.M) is not None and re.search(r"^test result: ok\. 1 passed; 0 failed",cp.stdout,re.M) is not None)
        records.append({"test_name":name,"argv":argv,"cwd":"runners/dsl","exit_status":cp.returncode,"exactly_one_passed":exact_one,"stdout":{"path":str(out_path.relative_to(ROOT)),"sha256":sha(out_path),"bytes":out_path.stat().st_size},"stderr":{"path":str(err_path.relative_to(ROOT)),"sha256":sha(err_path),"bytes":err_path.stat().st_size},"output_excerpt":combined[-3000:]})
        if cp.returncode: break
    passed=len(records)==len(CASES) and all(x["exit_status"]==0 and x["exactly_one_passed"] for x in records)
    parent_log=finish_console_capture(cap)
    children=[{"argv":x["argv"],"cwd":x["cwd"],"exit_status":x["exit_status"],"stdout_log":x["stdout"],"stderr_log":x["stderr"]} for x in records]
    manifest=capture_run_manifest(run_id=RUN_ID,runner="scripts/run_substrate_planning_native_unit_audit_v1_1.py",protocol_files=[PROTOCOL,AMENDMENT],source_files=list(SOURCES),analysis_files=["scripts/substrate_run_manifest.py"],started_utc=started,exit_status=0 if passed else 1,stdout_stderr_capture=parent_log,child_processes=children)
    doc={"run_id":RUN_ID,"protocol":PROTOCOL,"cases_expected":len(CASES),"cases_run":len(records),"all_gates_pass":passed,"cases":records,"manifest":manifest,"limits":["Five in-module unit fixtures only.","No long-horizon planning, held-out-world evaluation, or replanning capability is measured.","Cargo's build/run behavior is local to the recorded checkout and toolchain."]}
    OUT.write_text(json.dumps(doc,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"all_gates_pass":passed,"cases_run":len(records),"report":str(OUT.relative_to(ROOT)),"failed":[x["test_name"] for x in records if x["exit_status"] or not x["exactly_one_passed"]]},indent=2))
    if not passed: raise SystemExit(1)
if __name__=="__main__":main()

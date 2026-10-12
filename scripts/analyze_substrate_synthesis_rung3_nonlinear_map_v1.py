#!/usr/bin/env python3
"""Independent analysis of the integrated Rung 3 map-synthesis capture."""
from __future__ import annotations
import hashlib, json, statistics, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
import substrate_rs as srs

STEM = "synthesis_rung3_nonlinear_map_v1_20260929"
RAW = ROOT / f"evaluation/reports/{STEM}_raw.jsonl"
LOCK = ROOT / f"evaluation/substrate_capability/{STEM}_lock.json"
OUT = ROOT / f"evaluation/reports/{STEM}_analysis.json"
SOURCE_PATHS = (
    "domains/prog_synthesis.py", "domains/engine_provenance.py",
    "seeds/program_synthesis.json", "seeds/program_synthesis_opgrammar.json",
    "runners/dsl/src/synth_enumerate.rs", "runners/dsl/src/prog_eval.rs",
    "runners/dsl/src/term.rs", "runners/dsl/src/py.rs",
    "runners/dsl/src/graph_rules.rs", "runners/dsl/src/substrate.rs",
    "runners/dsl/python/substrate_rs/__init__.py",
    "runners/dsl/python/substrate_rs/_native.build.json",
)

def sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""): h.update(b)
    return h.hexdigest()

def main():
    lock=json.loads(LOCK.read_text())
    lines=[json.loads(x) for x in RAW.read_text().splitlines() if x.strip()]
    heads=[x for x in lines if x.get("kind")=="header"]
    feet=[x for x in lines if x.get("kind")=="footer"]
    workers=[x for x in lines if x.get("kind")=="worker"]
    schedule=lock["inputs"]["tasks"]
    expected={(task,rep) for task in schedule for rep in range(lock["inputs"]["repetitions"])}
    actual=[(x.get("task"),x.get("repetition")) for x in workers]
    unique=set(actual)
    worker_errors=[x for x in workers if x.get("worker_failed")]
    stable_workers=[x for x in workers if x.get("source_native_stable") is True]
    route_ok=[x for x in workers if (x.get("rungs") or {}).get("enumerate")==1.0]
    terminal=[x for x in workers if x.get("status") in ("accepted","gapped")]
    accepted=[x for x in workers if x.get("status")=="accepted"]
    accepted_valid=[x for x in accepted if x.get("program_count")==1 and
                    x.get("ir_root_count")==1 and len(x.get("heldout",[]))==6 and
                    all(y.get("exact") is True for y in x.get("heldout",[]))]
    case_results={}
    for task in schedule:
        group=[x for x in workers if x.get("task")==task]
        acq=[int(x["acquisition_wall_ns"]) for x in group if isinstance(x.get("acquisition_wall_ns"),int)]
        cpu=[int(x["acquisition_cpu_ns"]) for x in group if isinstance(x.get("acquisition_cpu_ns"),int)]
        rss=[int(x["peak_rss_bytes"]) for x in group if isinstance(x.get("peak_rss_bytes"),int)]
        case_results[task]={
            "n":len(group), "accepted":sum(x.get("status")=="accepted" for x in group),
            "gapped":sum(x.get("status")=="gapped" for x in group),
            "enumerate_reached":sum((x.get("rungs") or {}).get("enumerate")==1.0 for x in group),
            "enumerate_ok":sum(x.get("enumerate_outcome")=="ok" for x in group),
            "exact_holdout_transfer":sum(x in accepted_valid for x in group),
            "median_wall_ms":statistics.median(acq)/1e6 if acq else None,
            "min_wall_ms":min(acq)/1e6 if acq else None,
            "max_wall_ms":max(acq)/1e6 if acq else None,
            "median_cpu_ms":statistics.median(cpu)/1e6 if cpu else None,
            "max_peak_rss_bytes":max(rss) if rss else None,
            "enumerator_ops":sorted({str(x.get("goal_facts",{}).get("ps_enum_gamma_ops_admitted")) for x in group}),
            "programs":sorted({p.get("program_json") for x in group for p in x.get("programs",[]) if p.get("program_json")}),
        }
    current_source={p:sha(ROOT/p) for p in SOURCE_PATHS}
    from_path=Path(lock["native_extension"]["path"])
    current_native=sha(from_path) if from_path.exists() else None
    source_matches=current_source==lock.get("source_sha256")
    native_matches=current_native==lock["native_extension"].get("sha256")
    checks={
        "one_header_footer_and_locked_schedule":len(heads)==1 and len(feet)==1 and heads[0].get("lock")==lock,
        "complete_unique_20_worker_matrix":len(workers)==20 and len(actual)==len(unique)==20 and unique==expected,
        "no_worker_failures":not worker_errors,
        "current_sources_and_native_match_lock":source_matches and native_matches,
        "all_workers_source_native_stable":len(stable_workers)==20,
        "every_case_reached_rung3":len(route_ok)==20,
        "all_workers_terminal":len(terminal)==20,
        "every_accepted_program_reflected_and_exact_on_holdout":len(accepted)==len(accepted_valid),
        "linear_positive_control_accepts_and_transfers":case_results.get("linear",{}).get("accepted")==5 and case_results.get("linear",{}).get("exact_holdout_transfer")==5,
        "footer_source_native_stable":feet[0].get("source_native_stable") is True,
    }
    report={"run_id":STEM,"checks":checks,"integrity_pass":all(checks.values()),
            "passed_checks":sum(checks.values()),"total_checks":len(checks),
            "case_results":case_results,"accepted":len(accepted),
            "accepted_with_exact_holdout_transfer":len(accepted_valid),
            "worker_failures":worker_errors,"interpretation":
            "Measures the shipped program-synthesis adapter/rule route through Rung 3 and graph-reflected ProgEval on six locked holdout points. It does not establish general dimension induction, learned grammar choice, mint/adoption, natural-task prevalence, or scaling.",
            "lock_sha256":sha(LOCK),"raw_sha256":sha(RAW)}
    OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"output":str(OUT.relative_to(ROOT)),"checks":checks,"integrity_pass":report["integrity_pass"],"case_results":case_results},indent=2))
    if not report["integrity_pass"]: raise SystemExit(1)

if __name__=="__main__":main()

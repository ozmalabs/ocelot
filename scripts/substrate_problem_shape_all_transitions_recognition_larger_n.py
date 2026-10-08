#!/usr/bin/env python3
"""Paired larger-population recognition-only scaling probe for ProblemShape eventization."""
from __future__ import annotations
import hashlib, json, os, platform, random, statistics, subprocess, sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
PREREG = ROOT / "docs/research/engine_substrate/SUBSTRATE_PROBLEM_SHAPE_ALL_TRANSITIONS_RECOGNITION_LARGER_N_PREREG_20260925.md"
LOCK = ROOT / "evaluation/substrate_capability/problem_shape_all_transitions_recognition_larger_n_lock_20260925.json"
BASE = ROOT / "scripts/substrate_problem_shape_population_scale.py"
CAND = ROOT / "scripts/substrate_problem_shape_all_transitions.py"
OUT = ROOT / "evaluation/reports/substrate_problem_shape_all_transitions_recognition_larger_n_20260925.json"
PARTIAL = ROOT / "evaluation/reports/substrate_problem_shape_all_transitions_recognition_larger_n_partial_20260925.json"
SIZES = [16, 32]
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def locked_inputs():
    paths = {
      "preregistration": PREREG, "runner": Path(__file__), "baseline_worker": BASE, "candidate_worker": CAND,
      "baseline_raw": ROOT / "evaluation/reports/substrate_problem_shape_population_scale_20260925.json",
      "problem_shape": ROOT / "domains/problem_shape.py", "solver_dispatch": ROOT / "domains/solver_dispatch.py",
      "decomposition": ROOT / "domains/problem_decomposition.py", "bigville": ROOT / "worlds/bigville_can_beliefs.py",
      "shape_seed": ROOT / "seeds/problem_shape_growth.json", "decode_seed": ROOT / "seeds/shape_decode_loop.json",
      "cast_seed": ROOT / "seeds/bigville_cast100.json", "native": ROOT / "runners/dsl/python/substrate_rs/_native.abi3.so",
      "build_manifest": ROOT / "runners/dsl/python/substrate_rs/_native.build.json", "cargo_lock": ROOT / "runners/dsl/Cargo.lock"}
    return {k: sha(v) for k,v in paths.items()}
def child(arm, n):
    module = "substrate_problem_shape_population_scale" if arm == "baseline" else "substrate_problem_shape_all_transitions"
    fn = "worker"; args = f"{n}, 'recognition', 'dynamic'" if arm == "baseline" else f"{n}, 'recognition'"
    code = ("import json,sys; sys.path[:0]=['.', 'runners/dsl/python','scripts']; "
            f"import {module} as m; m.SIZES=[2,4,8,16,32]; "
            f"r=m.{fn}({args}); print(json.dumps(r,sort_keys=True)); sys.exit(0 if r['all_checks_pass'] else 2)")
    env={**os.environ,"PYTHONPATH":f"{ROOT}:{ROOT/'runners/dsl/python'}:{ROOT/'scripts'}"}
    proc=subprocess.run([sys.executable,"-c",code],cwd=ROOT,env=env,text=True,capture_output=True,timeout=600)
    if proc.returncode: raise RuntimeError(f"{arm} N={n} failed: {proc.stdout[-1500:]} {proc.stderr[-1500:]}")
    raw=json.loads(proc.stdout.strip().splitlines()[-1])
    if not raw.get("all_checks_pass"): raise RuntimeError(f"{arm} N={n} semantic gate failed")
    rows=raw["records"]
    if arm == "baseline": wall=[int(x["wall_time_ns"]) for x in rows]; cpu=[int(x["cpu_time_ns"]) for x in rows]
    else: wall=[int(x["treatment_observation_wall_ns"]) for x in rows]; cpu=[int(x["treatment_observation_cpu_ns"]) for x in rows]
    return {"arm":arm,"process_id":raw["process_id"],"all_checks_pass":True,"boot_wall_ns":int(raw.get("full_seed_boot_wall_ns",0)),
      "peak_rss_bytes":int(raw.get("peak_rss_bytes",raw.get("process_peak_rss_bytes",0))),"wall_ns_total":sum(wall),"cpu_ns_total":sum(cpu),
      "wall_ns_by_step":wall,"status_initial":[x.get("observation_status_initial") for x in rows],
      "status_final":[x.get("observation_status_final") for x in rows],"mints_by_step":[int(x.get("mint_count_delta",0)) for x in rows],
      "candidate_pairs":int(raw.get("problem_shape_candidate_pairs_total",0)),"term_evaluations":int(raw.get("problem_shape_term_evaluations_total",0)),
      "ps_mint_pairs":int(raw.get("ps_mint_candidate_pairs_total",0)),"ps_mint_terms":int(raw.get("ps_mint_term_evaluations_total",0)),
      "index_maintenance_ns":int(raw.get("host_index_maintenance_ns_total",0)),"variant":raw.get("variant",raw.get("codebook_mode"))}
def main():
    frozen=json.loads(LOCK.read_text()); actual=locked_inputs()
    if frozen != actual: raise SystemExit("recognition larger-N lock mismatch")
    env={**os.environ,"PYTHONPATH":f"{ROOT}:{ROOT/'runners/dsl/python'}:{ROOT/'scripts'}"}
    stale=subprocess.check_output([sys.executable,"-c","from domains.engine_provenance import build_is_stale; print('\\n'.join(build_is_stale('.')))"],cwd=ROOT,env=env,text=True).strip()
    if stale: raise SystemExit(f"native build stale:\n{stale}")
    if PARTIAL.exists() or OUT.exists(): raise SystemExit("refusing to overwrite existing output/checkpoint")
    rng=random.Random(20260926); schedule=[]
    for n in SIZES:
        orders=[["baseline","candidate"] for _ in range(3)]+[["candidate","baseline"] for _ in range(3)]
        rng.shuffle(orders); schedule += [(n,o) for o in orders]
    rng.shuffle(schedule); seen=set(); pairs=[]
    for i,(n,order) in enumerate(schedule,1):
        arms={}
        for arm in order:
            rec=child(arm,n)
            if rec["process_id"] in seen: raise RuntimeError("worker PID reused")
            seen.add(rec["process_id"]); arms[arm]=rec
        b,c=arms["baseline"],arms["candidate"]
        parity=(b["status_initial"]==c["status_initial"] and b["status_final"]==c["status_final"] and b["mints_by_step"]==c["mints_by_step"])
        pairs.append({"pair":i,"N":n,"order":order,"arms":arms,"semantic_parity":parity,
          "wall_ratio":c["wall_ns_total"]/b["wall_ns_total"],"cpu_ratio":c["cpu_ns_total"]/b["cpu_ns_total"]})
        print(json.dumps({"pair":i,"N":n,"order":order,"semantic_parity":parity,"wall_ratio":pairs[-1]["wall_ratio"]}),flush=True)
        tmp={"completed_pairs":pairs,"unique_pids":len(seen)==2*i,"locked_inputs":actual,"lock_sha256":sha(LOCK)}
        PARTIAL.write_text(json.dumps(tmp,indent=2,sort_keys=True)+"\n")
    summaries={}
    for n in SIZES:
        ps=[p for p in pairs if p["N"]==n]; ratios=[p["wall_ratio"] for p in ps]
        summaries[str(n)]={"pair_count":len(ps),"all_semantics_match":all(p["semantic_parity"] for p in ps),
          "order_counts":{"baseline_first":sum(p["order"][0]=="baseline" for p in ps),"candidate_first":sum(p["order"][0]=="candidate" for p in ps)},
          "candidate_faster_pairs":sum(x<1 for x in ratios),"wall_ratio_median":statistics.median(ratios),
          "wall_ratio_range":[min(ratios),max(ratios)],"candidate_pairs":{"baseline":ps[0]["arms"]["baseline"]["candidate_pairs"],"candidate":ps[0]["arms"]["candidate"]["candidate_pairs"]},
          "term_evaluations":{"baseline":ps[0]["arms"]["baseline"]["term_evaluations"],"candidate":ps[0]["arms"]["candidate"]["term_evaluations"]},
          "counter_values_stable":all(p["arms"]["baseline"]["candidate_pairs"]==ps[0]["arms"]["baseline"]["candidate_pairs"] and p["arms"]["candidate"]["candidate_pairs"]==ps[0]["arms"]["candidate"]["candidate_pairs"] and p["arms"]["baseline"]["term_evaluations"]==ps[0]["arms"]["baseline"]["term_evaluations"] and p["arms"]["candidate"]["term_evaluations"]==ps[0]["arms"]["candidate"]["term_evaluations"] for p in ps)}
    result={"schema_version":1,"run_id":"problem-shape-all-transitions-recognition-larger-n-20260925","run_state":"locked_exploratory_scaling_probe",
      "design":{"sizes":SIZES,"pairs_per_size":6,"workers":len(seen),"mix":"recognition","codebook_mode":"dynamic","rng_seed":20260926},
      "summaries_by_N":summaries,"all_gates_pass":len(seen)==24 and all(x["all_semantics_match"] and x["counter_values_stable"] and x["order_counts"]=={"baseline_first":3,"candidate_first":3} for x in summaries.values()),
      "pairs":pairs,"provenance":{"locked_inputs":actual,"lock_sha256":sha(LOCK),"native_sha256":sha(ROOT/"runners/dsl/python/substrate_rs/_native.abi3.so"),"git_head":subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip(),"dirty_worktree":bool(subprocess.check_output(["git","status","--porcelain"],cwd=ROOT,text=True).strip()),"python":sys.version,"platform":platform.platform()},
      "interpretation_limit":"Six fresh-process pairs at each of N=16 and N=32 on one authored recognition-only sequence; exploratory and not natural-task or substrate-wide scaling evidence."}
    OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n"); PARTIAL.unlink(); print(json.dumps({"all_gates_pass":result["all_gates_pass"],"summaries_by_N":summaries},sort_keys=True)); return 0 if result["all_gates_pass"] else 2
if __name__=="__main__": raise SystemExit(main())

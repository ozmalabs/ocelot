#!/usr/bin/env python3
"""Measure explicit transfer of typed correction outcomes into graph ranking."""
from __future__ import annotations
import importlib.util, json, os, statistics, subprocess, sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "evaluation/substrate_capability/thoughtexperiment_graph_authored_correction_rank_v1.py"
PREREG = ROOT / "docs/research/engine_substrate/THOUGHTEXPERIMENT_CORRECTION_OUTCOME_RANK_TRANSFER_V1_PREREG_20261001.md"
RAW = ROOT / "evaluation/reports/thoughtexperiment_correction_outcome_rank_transfer_v1_raw_20261001.json"
RESULT = ROOT / "docs/research/engine_substrate/THOUGHTEXPERIMENT_CORRECTION_OUTCOME_RANK_TRANSFER_V1_RESULTS_20261001.md"
spec = importlib.util.spec_from_file_location("rank_v1", BASE)
base = importlib.util.module_from_spec(spec); sys.modules[spec.name] = base; spec.loader.exec_module(base)

def from_episode(ep):
    # Only records from candidates actually rehearsed in the training episode.
    return [{"target_rule": ep["target_rule"], "candidate_label": row["label"],
             "candidate_digest": "training-observation", "converges_in_rehearsal": bool(row["converges"]),
             "selected": bool(row["selected"]), "adopted": bool(row["selected"] and ep["adopted"]),
             "task_utility": 1.0 if row["selected"] and ep["adopted"] and ep["model_final_converged"] else 0.0,
             "rank_attempt_tag": "explicit-training-transfer"} for row in ep["tried"]]

def run_episode(worker, arm, records):
    import domains.self_correct_dispatch as dispatch
    original = dispatch.rank_candidates
    transferred = []
    def seeded(agent, native, candidates):
        sub, _ = dispatch._resolve(agent)
        if arm == "experience_rank":
            for record in records:
                node = sub.add_node("CorrectionOutcome", record)
                transferred.append(record)
        return original(agent, native, candidates)
    dispatch.rank_candidates = seeded
    try:
        ep = base.episode(worker, "graph_cost_rank")
    finally:
        dispatch.rank_candidates = original
    ep["arm"] = arm
    ep["transferred_records"] = transferred
    return ep

def worker(i):
    before = base.fingerprint()
    training = base.episode(i, "graph_cost_rank")
    records = from_episode(training)
    cold = run_episode(i + 100, "cold_rank", [])
    warm = run_episode(i + 200, "experience_rank", records)
    after = base.fingerprint()
    return {"pid": os.getpid(), "source_before": before, "source_after": after,
            "source_stable": before == after, "training": training,
            "records": records, "cold": cold, "experience": warm}

def main():
    if len(sys.argv) == 3 and sys.argv[1] == "--worker":
        print(json.dumps(worker(int(sys.argv[2])), sort_keys=True, separators=(",", ":"))); return 0
    from domains.engine_provenance import build_is_stale, rust_source_fingerprint
    stale = build_is_stale(str(ROOT))
    if stale: raise SystemExit("stale native engine: " + "; ".join(stale))
    env = {**os.environ, "PYTHONPATH": f"{ROOT / 'runners/dsl/python'}:{ROOT}"}
    workers=[]
    for i in range(3):
        p=subprocess.run([sys.executable, str(Path(__file__).resolve()), "--worker", str(i)], cwd=ROOT, env=env, text=True, capture_output=True, check=True)
        workers.append(json.loads(p.stdout.strip().splitlines()[-1]))
    arms={"cold_rank":[w["cold"] for w in workers], "experience_rank":[w["experience"] for w in workers]}
    gates={
      "three_workers_nine_episodes": len(workers)==3 and all(w["cold"] and w["experience"] and w["training"] for w in workers),
      "stable_source_build": all(w["source_stable"] for w in workers),
      "training_success_and_failure": all(any(r["task_utility"]==1 for r in w["records"]) and any(r["task_utility"]==0 for r in w["records"]) for w in workers),
      "cold_has_no_history": all(not e["transferred_records"] for e in arms["cold_rank"]),
      "transfer_changes_candidate_order": all(w["experience"]["candidate_order_used"][0]=="dedup_identity_fix" and w["experience"]["candidate_order_used"][0]!=w["cold"]["candidate_order_used"][0] for w in workers),
      "cold_replays_cost_order": all(e["candidate_order_used"][0]=="swap_term_leaf:signature->residual" for e in arms["cold_rank"]),
      "both_arms_adopt_and_pass_heldout": all(e["adopted"] and e["selected_candidate"]=="dedup_identity_fix" and e["all_task_oracle_gates"] for rows in arms.values() for e in rows),
      "trace_exposes_prior_counts": all(any(x.get("rank_trace",{}).get("prior_successes",0)>=1 for x in e["tried"]) for e in arms["experience_rank"]),
    }
    summary=[]
    for name, rows in arms.items(): summary.append({"arm":name,"episodes":len(rows),"candidate_attempts":[e["candidates_tested"] for e in rows],"median_attempts":statistics.median(e["candidates_tested"] for e in rows),"orders":[e["candidate_order_used"] for e in rows],"heldout_passes":sum(e["all_task_oracle_gates"] for e in rows)})
    from substrate_rs import _native
    import hashlib
    binary=Path(_native.__file__).resolve()
    capture={"schema":"ThoughtexperimentCorrectionOutcomeRankTransferV1","captured_utc":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),"protocol":{"workers":3,"episodes_per_worker":3,"training":"observed outcomes from actually tried candidates","transfer":"explicit typed CorrectionOutcome graph nodes","arms":["cold_rank","experience_rank"]},"engine_fingerprint":rust_source_fingerprint(str(ROOT)),"native_binary":{"path":str(binary),"sha256":hashlib.sha256(binary.read_bytes()).hexdigest()},"workers":workers,"arm_summary":summary,"gates":gates}
    RAW.parent.mkdir(parents=True,exist_ok=True); RAW.write_text(json.dumps(capture,indent=2,sort_keys=True)+"\n")
    out=f"# Thoughtexperiment correction outcome rank transfer v1 — results\n\n**Result:** {sum(gates.values())}/{len(gates)} preregistered gates pass.\n\nThree fresh workers each ran a training episode followed by cold and experience-informed episodes on distinct substrate instances. The training candidates actually tried produced typed outcome records, including the adopted successful repair and a failed rehearsal. The transfer arm received those records as `CorrectionOutcome` graph nodes before ranking; host code transported evidence but did not select the candidate.\n\n| Arm | Attempts | Median | Candidate order | Held-out passes |\n|---|---|---:|---|---:|\n"
    for s in summary: out+=f"| `{s['arm']}` | {s['candidate_attempts']} | {s['median_attempts']} | {s['orders']} | {s['heldout_passes']}/3 |\n"
    out+="\nThe result tests outcome-conditioned ordering on repeated instances of one authored correction family. It is evidence that typed prior outcomes can alter a graph-authored rank Program's ordering on fresh graph instances; it is not autonomous memory acquisition, general learning, or evidence of broad task utility. Candidate attempts and held-out correctness are more interpretable here than timing.\n\n## Artifacts\n\n- [Preregistration](THOUGHTEXPERIMENT_CORRECTION_OUTCOME_RANK_TRANSFER_V1_PREREG_20261001.md)\n- [Runner](../../../evaluation/substrate_capability/thoughtexperiment_correction_outcome_rank_transfer_v1.py)\n- [Raw capture](../../../evaluation/reports/thoughtexperiment_correction_outcome_rank_transfer_v1_raw_20261001.json)\n"
    RESULT.write_text(out)
    print(json.dumps({"gates":gates,"summary":summary},indent=2,sort_keys=True)); return 0 if all(gates.values()) else 1
if __name__=="__main__": raise SystemExit(main())

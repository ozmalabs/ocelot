#!/usr/bin/env python3
"""Cellwise and application-unit audit for two fixed SynthEnumerate captures."""
import hashlib, json, statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OLD="synthenumerate_nonlinear_map_v1_20260929"
NEW="synthenumerate_nonlinear_map_v1_1_20260929"
def read(stem):
    records=[json.loads(x) for x in (ROOT/f"evaluation/reports/{stem}_raw.jsonl").read_text().splitlines() if x.strip()]
    return ([x for x in records if x.get("kind")=="header"][0],
            [x for x in records if x.get("kind")=="worker"],
            [x for x in records if x.get("kind")=="footer"][0])
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    oh,ow,of=read(OLD); nh,nw,nf=read(NEW)
    old_lock=json.loads((ROOT/f"evaluation/substrate_capability/{OLD}_lock.json").read_text())
    new_lock=json.loads((ROOT/f"evaluation/substrate_capability/{NEW}_lock.json").read_text())
    new_analysis=json.loads((ROOT/f"evaluation/reports/{NEW}_analysis.json").read_text())
    old_ix={(x["task"],x["grammar"],x["repetition"]):x for x in ow}
    new_ix={(x["task"],x["grammar"],x["repetition"]):x for x in nw}
    same_tasks=old_lock["inputs"]["cases"]==new_lock["inputs"]["cases"]
    semantic_parity=bool(len(old_ix)==len(new_ix)==40 and all(
      (old_ix[k]["found"],old_ix[k]["halt_reason"],old_ix[k]["term"],old_ix[k]["heldout"]) ==
      (new_ix[k]["found"],new_ix[k]["halt_reason"],new_ix[k]["term"],new_ix[k]["heldout"]) for k in old_ix.keys() & new_ix.keys()))
    unit_ok=True; unit_recomputed={}
    for cell,summary in new_analysis["acquisition_cells"].items():
        task,grammar=cell.split(":")
        found=[new_ix[(task,grammar,r)] for r in range(5) if (task,grammar,r) in new_ix and new_ix[(task,grammar,r)]["found"]]
        unit_recomputed[cell]={}
        for count in new_lock["inputs"]["reuse_counts"]:
            ns_per_call=[b["wall_ns"]/b["calls"] for row in found for b in row["reuse_batches"] if b["calls"]==count]
            us=[v/1000 for v in ns_per_call]
            actual=summary["application_cost"][str(count)]
            expected={"median_us_per_call":statistics.median(us) if us else None,
                      "min_us_per_call":min(us) if us else None,"max_us_per_call":max(us) if us else None}
            unit_ok &= expected==actual
            unit_recomputed[cell][str(count)]=expected
    checks={"same_preregistered_task_grammar_pairs":same_tasks,
            "semantic_outcomes_and_terms_match_cellwise":semantic_parity,
            "corrected_application_microseconds_recomputed_from_raw_nanoseconds":bool(unit_ok),
            "new_source_native_capture_stable":nf.get("source_native_stable") is True,
            "both_independent_gate_reports_pass":json.loads((ROOT/f"evaluation/reports/{OLD}_analysis.json").read_text()).get("integrity_pass") is True and new_analysis.get("integrity_pass") is True}
    out={"comparison":"initial capture vs v1.1 corrected-unit fresh repeat",
         "checks":checks,"comparison_pass":all(checks.values()),
         "raw_sha256":{"v1":sha(ROOT/f"evaluation/reports/{OLD}_raw.jsonl"),"v1_1":sha(ROOT/f"evaluation/reports/{NEW}_raw.jsonl")},
         "lock_sha256":{"v1":sha(ROOT/f"evaluation/substrate_capability/{OLD}_lock.json"),"v1_1":sha(ROOT/f"evaluation/substrate_capability/{NEW}_lock.json")},
         "corrected_application_cost_us_per_call":unit_recomputed,
         "interpretation":"The same task/grammar designs, synthesized Terms, and held-out semantic outcomes recur across the two fresh captures. Application costs are independently recomputed from raw batch nanoseconds and converted to microseconds per call. This does not estimate cost variance beyond the five repeated acquisitions or the four registered application batch sizes.",
         "limitation":"The first analysis reported raw nanoseconds per call under a millisecond label; it is retained as a disclosed analysis defect and is not used for cost interpretation."}
    path=ROOT/f"evaluation/reports/synthenumerate_nonlinear_map_capture_comparison_v1_20260929.json"
    path.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"output":str(path.relative_to(ROOT)),"checks":checks,"comparison_pass":out["comparison_pass"]},indent=2))
    if not out["comparison_pass"]:raise SystemExit("capture comparison audit failed")
if __name__=="__main__":main()

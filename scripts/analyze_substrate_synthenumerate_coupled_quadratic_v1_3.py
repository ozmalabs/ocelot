#!/usr/bin/env python3
"""Independent task reconstruction, integrity gates, and reuse-cost analysis."""
from __future__ import annotations
import json, statistics, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
import substrate_rs as srs
from domains.engine_provenance import engine_provenance

STEM = "synthenumerate_coupled_quadratic_v1_3_20261005"
RAW = ROOT / f"evaluation/reports/{STEM}_raw.jsonl"
LOCK = ROOT / f"evaluation/substrate_capability/{STEM}_lock.json"
OUT = ROOT / f"evaluation/reports/{STEM}_analysis.json"
REQUIRED_PAIRS = {("linear_control", "plus_tuple"), ("coupled_quadratic", "plus_tuple"),
                  ("coupled_quadratic", "plus_times_tuple")}

def sha(path):
    import hashlib
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def target(task, r, c):
    if task == "linear_control": return (r+c, 2*c)
    if task == "coupled_quadratic": return (r+r*c, c+r*r)
    raise KeyError(task)

def quantile(values, p):
    xs = sorted(values)
    if not xs: return None
    pos = p * (len(xs)-1); lo=int(pos); hi=min(lo+1, len(xs)-1)
    return xs[lo] + (pos-lo)*(xs[hi]-xs[lo])

def main():
    lock = json.loads(LOCK.read_text())
    records = [json.loads(line) for line in RAW.read_text().splitlines() if line.strip()]
    headers = [x for x in records if x.get("kind") == "header"]
    workers = [x for x in records if x.get("kind") == "worker"]
    footers = [x for x in records if x.get("kind") == "footer"]
    header = headers[0] if headers else {}; footer = footers[0] if footers else {}
    cases = lock["inputs"]["cases"]
    expected = {(c["task"], c["grammar"], rep) for c in cases for rep in range(c["repetitions"])}
    ix = {}
    errors = []
    for row in workers:
        key=(row.get("task"), row.get("grammar"), row.get("repetition"))
        valid=key in expected and key not in ix
        if not valid:
            errors.append({"key": list(key), "reason": "unknown or duplicate worker"}); continue
        case=next(c for c in cases if (c["task"],c["grammar"]) == key[:2])
        valid &= row.get("found") == (row.get("term") is not None)
        valid &= isinstance(row.get("acquisition_wall_ns"), int) and row["acquisition_wall_ns"] > 0
        valid &= isinstance(row.get("acquisition_cpu_ns"), int) and row["acquisition_cpu_ns"] > 0
        tested=row.get("tested_candidates")
        valid &= tested is None or (isinstance(tested, int) and 0 <= tested <= lock["inputs"]["candidate_cap"])
        valid &= row.get("peak_process_rss_bytes", 0) > 0
        if row.get("found"):
            valid &= len(row.get("heldout", [])) == len(case["heldout"])
            valid &= len(row.get("reuse_batches", [])) == (len(lock["inputs"]["reuse_counts"]) if row.get("exact_transfer") else 0)
            valid &= all(b.get("calls") == n and b.get("wall_ns", 0) > 0
                         for b,n in zip(row.get("reuse_batches", []), lock["inputs"]["reuse_counts"]))
        else:
            valid &= not row.get("heldout") and not row.get("reuse_batches")
        if not valid: errors.append({"key": list(key), "reason": "malformed worker fields"})
        ix[key]=row

    task_table_ok=True
    for case in cases:
        for split in ("training", "heldout"):
            for example in case[split]:
                r,c=example["inputs"]["r"],example["inputs"]["c"]
                task_table_ok &= tuple(example["output"]) == target(case["task"],r,c)

    # Re-evaluate every acquired Term independently over the complete locked holdout.
    independent_holdout=True; holdout_errors=[]
    for key,row in ix.items():
        if not row.get("found"): continue
        case=next(c for c in cases if (c["task"],c["grammar"]) == key[:2])
        term=row["term"]
        for j,example in enumerate(case["heldout"]):
            try:
                got=srs.Substrate()._inner.evaluate(term, dict(example["inputs"]))
                expected_value=target(case["task"],example["inputs"]["r"],example["inputs"]["c"])
                pred=tuple(got) if isinstance(got,(tuple,list)) else None
                raw=row.get("heldout",[])[j]
                if raw.get("predicted") != (list(pred) if pred is not None else None) or raw.get("exact") is not (pred == expected_value):
                    independent_holdout=False
                    holdout_errors.append({"key":list(key),"heldout_index":j,"expected":list(expected_value),"predicted":list(pred) if pred is not None else None})
            except Exception as e:
                independent_holdout=False; holdout_errors.append({"key":list(key),"heldout_index":j,"error":str(e)[:200]})
    current_sources={p:sha(ROOT/p) for p in lock.get("source_sha256",{})}
    loaded_native=Path(srs._native.__file__).resolve()
    checks={
        "one_header_and_footer": len(headers)==1 and len(footers)==1,
        "complete_unique_30_acquisition_matrix": len(workers)==30 and set(ix)==expected,
        "capture_and_current_sources_match_lock": header.get("lock")==lock and current_sources==lock.get("source_sha256"),
        "loaded_native_hash_matches_lock": sha(loaded_native)==lock.get("native_extension",{}).get("sha256"),
        "source_native_stable_during_run": footer.get("source_native_stable") is True and footer.get("post_lock_payload")==lock,
        "locked_task_tables_match_independent_targets": bool(task_table_ok),
        "worker_fields_and_candidate_accounting_valid": not errors,
        "every_acquired_program_independently_rechecked": bool(independent_holdout),
        "exact_transfer_flag_matches_replay": all(row.get("exact_transfer") == (bool(row.get("heldout")) and all(z.get("exact") for z in row.get("heldout",[]))) for row in ix.values()),
        "linear_positive_control_acquired_and_transfers": sum(bool(ix.get(("linear_control","plus_tuple",r),{}).get("found")) and all(x.get("exact") for x in ix.get(("linear_control","plus_tuple",r),{}).get("heldout",[])) for r in range(10)) == 10,
    }
    metrics={}
    for case in cases:
        key=(case["task"],case["grammar"])
        rows=[ix[(key[0],key[1],r)] for r in range(case["repetitions"]) if (key[0],key[1],r) in ix]
        found=[r for r in rows if r.get("found")]
        exact=[r for r in found if r.get("heldout") and all(x.get("exact") for x in r["heldout"])]
        vals=[r["acquisition_wall_ns"]/1e6 for r in rows]
        costs={}
        for n in lock["inputs"]["reuse_counts"]:
            samples=[b["wall_ns"]/b["calls"]/1000 for r in found for b in r.get("reuse_batches",[]) if b["calls"]==n]
            costs[str(n)]={"median_us_per_call":statistics.median(samples) if samples else None,
                           "min_us_per_call":min(samples) if samples else None,
                           "max_us_per_call":max(samples) if samples else None}
        terms=[json.dumps(r["term"],sort_keys=True,separators=(",",":")) for r in found]
        metrics[f"{key[0]}:{key[1]}"]={
            "n":len(rows),"found":len(found),"exact_heldout_transfer":len(exact),
            "reuse_measured_only_after_exact_transfer":sum(bool(r.get("reuse_batches")) for r in rows),
            "fit_but_failed_transfer":sum(bool(r.get("found")) and not all(x.get("exact") for x in r.get("heldout",[])) for r in rows),
            "not_found":sum(not r.get("found") for r in rows),
            "halt_reasons":{str(x):sum(r.get("halt_reason")==x for r in rows) for x in sorted({str(r.get("halt_reason")) for r in rows})},
            "tested_candidates_median":statistics.median([r["tested_candidates"] for r in rows if isinstance(r.get("tested_candidates"),int)]) if any(isinstance(r.get("tested_candidates"),int) for r in rows) else None,
            "acquisition_wall_ms":{"median":statistics.median(vals) if vals else None,"p90":quantile(vals,.9),"max":max(vals) if vals else None},
            "application_cost":costs,"canonical_term_repeat_count":len(set(terms)),
            "peak_process_rss_bytes":max((r.get("peak_process_rss_bytes",0) for r in rows),default=0)}
    out={"run_id":header.get("run_id"),"checks":checks,"integrity_pass":all(checks.values()),
         "passed_checks":sum(checks.values()),"total_checks":len(checks),"errors":errors,"heldout_errors":holdout_errors,
         "worker_count":len(workers),"acquisition_cells":metrics,
         "run_wall_seconds":footer.get("run_wall_ns",0)/1e9,
         "run_process_cpu_seconds":footer.get("run_process_cpu_ns",0)/1e9,
         "claim_boundary":"Synthetic fixed-size integer maps acquired as native SynthEnumerate Terms and tested on held-out pairs. This measures bounded executable-program induction and reuse; comparison to GenInfer v1.5 is cross-path and descriptive, not an integrated mint/adoption result or natural-task prevalence claim.",
         "limitations":["One coupled quadratic map and one linear positive control; no task-distribution sampling.",
                        "Candidate caps bound search work; refusal at the cap is not evidence of non-representability.",
                        "Held-out outcomes are deterministic and repeated runs are not independent statistical samples.",
                        "Application cost includes the native Python binding and validation loop; it is not isolated Rust instruction time."]}
    OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"analysis":str(OUT.relative_to(ROOT)),"checks":checks,"acquisition_cells":metrics},indent=2))
    if not out["integrity_pass"]: raise SystemExit("SynthEnumerate nonlinear-map admission failed")

if __name__=="__main__": main()

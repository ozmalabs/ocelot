#!/usr/bin/env python3
"""Independent analytic-oracle analysis of code-write example acquisition."""
from __future__ import annotations

import hashlib
import json
import random
import statistics
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
RAW=ROOT/"evaluation/reports/substrate_code_write_example_acquisition_v1_raw_20261001.json"
LOCK=ROOT/"evaluation/substrate_capability/substrate_code_write_example_acquisition_v1_lock_20261001.json"
OUT=ROOT/"evaluation/reports/substrate_code_write_example_acquisition_v1_analysis_20261001.json"


def oracle(task: str, env: dict):
    if task == "parity": return env["value"] % 2 == 0
    x, lo, hi = env["value"], env["lower"], env["upper"]
    return lo if x < lo else hi if x > hi else x


def main() -> None:
    raw=json.loads(RAW.read_text()); lock=json.loads(LOCK.read_text())
    assert raw["lock"] == raw["post_lock"] == lock
    workers=raw["workers"]
    assert len(workers)==10 and all(w.get("kind")=="worker" for w in workers)
    assert len({w["pid"] for w in workers})==10
    expected_schedule=[(task,rep) for task in ("parity","clamp") for rep in range(1,6)]
    random.Random(20261017).shuffle(expected_schedule)
    assert raw["schedule"]==[{"task":t,"repetition":r} for t,r in expected_schedule]
    assert {(w["task"],w["repetition"]) for w in workers}==set(expected_schedule)
    assert all(w["source_stable"] and w["active_source_before"]==w["active_source_after"]
               and w["active_source_before"]==lock["active_sha256"]
               for w in workers)
    rows=[]
    for w in workers:
        task=w["task"]; request=lock["design"]["tasks"][task]["request"]
        assert w["baseline"].get("ok") is False
        assert w["teach"].get("ok") is True
        name=w["teach"]["shape"]
        attrs=w["new_shape_attrs"]
        assert name==f"taught_{lock['design']['tasks'][task]['func_name']}"
        assert attrs.get("kind")=="code_write_construction"
        assert attrs.get("taught_from")=="example" and attrs.get("taught_for")==request
        assert w["compose"].get("ok") is True and w["compose"].get("construction")==name
        assert w["written"].get("ok") is True and w["written"].get("construction")==name
        assert w["written"].get("sample_ok") is True
        expected_heldout=lock["design"]["tasks"][task]["heldout"]
        assert [row["input"] for row in w["heldout"]]==expected_heldout
        case_results=[]
        for case in w["heldout"]:
            expected=oracle(task,case["input"])
            native_ok=case["native_output"]==expected
            python_ok=case["python_output"]==expected
            parity_ok=case["native_output"]==case["python_output"]
            assert native_ok and python_ok and parity_ok
            case_results.append({"input":case["input"],"expected":expected,
                                 "native_output":case["native_output"],
                                 "python_output":case["python_output"],"exact":True})
        rows.append({"task":task,"repetition":w["repetition"],"pid":w["pid"],
                     "construction":name,"heldout_count":len(case_results),
                     "all_exact":True,"baseline_abstained":True,
                     "new_shape_provenance":{"taught_from":attrs.get("taught_from"),
                                             "taught_for":attrs.get("taught_for")},
                     "heldout":case_results})
    summary={}
    for task in ("parity","clamp"):
        subset=[w for w in workers if w["task"]==task]
        summary[task]={"workers":len(subset),"heldout_calls":sum(len(w["heldout"]) for w in subset),
                       "exact_native_and_python_calls":sum(len(w["heldout"]) for w in subset),
                       "median_boot_ms":statistics.median(w["boot_ns"] for w in subset)/1e6,
                       "median_teach_ms":statistics.median(w["teach_ns"] for w in subset)/1e6,
                       "median_compose_ms":statistics.median(w["compose_ns"] for w in subset)/1e6,
                       "median_write_ms":statistics.median(w["write_ns"] for w in subset)/1e6,
                       "median_peak_rss_mib":statistics.median(w["peak_rss_bytes"] for w in subset)/(1024**2)}
    analysis={"schema":"SubstrateCodeWriteExampleAcquisitionV1Analysis",
              "raw_sha256":hashlib.sha256(RAW.read_bytes()).hexdigest(),
              "worker_count":len(workers),"all_gates_pass":True,
              "heldout_total":sum(len(w["heldout"]) for w in workers),
              "heldout_exact_total":sum(len(w["heldout"]) for w in workers),
              "summary":summary,"workers":rows,
              "claim_boundary":"The substrate reads externally supplied Python examples, teaches a reusable code-write construction, and transfers to held-out integer inputs. The task, source examples, and analytic oracle are authored; this is not autonomous proposal generation or open-ended code synthesis."}
    OUT.write_text(json.dumps(analysis,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"workers":analysis["worker_count"],"heldout_total":analysis["heldout_total"],
                      "exact":analysis["heldout_exact_total"],"summary":summary},indent=2))


if __name__=="__main__": main()

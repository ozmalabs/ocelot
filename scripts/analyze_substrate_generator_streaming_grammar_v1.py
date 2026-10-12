#!/usr/bin/env python3
"""Independent integrity and parity analysis for conditional-grammar probe."""
from __future__ import annotations
import hashlib, json, statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
STEM="substrate_generator_streaming_grammar_v1_20261001"
RAW=ROOT/f"evaluation/reports/{STEM}_raw.json"
LOCK=ROOT/f"evaluation/substrate_capability/{STEM}_lock.json"
OUT=ROOT/f"evaluation/reports/{STEM}_analysis.json"
def sha(p):return "sha256:"+hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 d=json.loads(RAW.read_text());lock=json.loads(LOCK.read_text());rows=d["comparisons"]
 src=all(sha(ROOT/name)==digest for name,digest in lock["sources"].items()) and sha(lock["native_extension"]["path"])==lock["native_extension"]["sha256"]
 want={(t,s,r) for t,ss in ((k,v) for k,v in lock["design"]["sizes"].items()) for s in ss for r in range(lock["design"]["repetitions"])}
 got={(x.get("task"),x.get("max_size"),x.get("replicate")) for x in rows}
 coverage=len(rows)==12 and got==want and not any("worker_error" in x for x in rows)
 pairs=[]
 for x in rows:
  a,b=x["arms"]["eager"],x["arms"]["streaming"]
  parity=all(a[k]==b[k] for k in ("halt_reason","pool_size","explored","distinct","signatures","target_support"))
  pairs.append({"task":x["task"],"max_size":x["max_size"],"replicate":x["replicate"],"semantic_parity":parity,
                "eager_halt":a["halt_reason"],"streaming_halt":b["halt_reason"],
                "wall_ratio_eager_over_streaming":a["wall_s"]/b["wall_s"] if b["wall_s"] else None,
                "python_peak_ratio_eager_over_streaming":a["python_peak_bytes"]/b["python_peak_bytes"] if b["python_peak_bytes"] else None})
 parity=coverage and all(p["semantic_parity"] for p in pairs) and all(x["arms"][a]["halt_reason"]=="max_size" for x in rows for a in ("eager","streaming"))
 summaries=[]
 for t in ("triangular","square","euler"):
  for s in sorted({x["max_size"] for x in rows if x["task"]==t}):
   ps=[p for p in pairs if p["task"]==t and p["max_size"]==s]
   summaries.append({"task":t,"max_size":s,"pairs":len(ps),"parity":sum(p["semantic_parity"] for p in ps),
    "median_wall_ratio":statistics.median(p["wall_ratio_eager_over_streaming"] for p in ps if p["wall_ratio_eager_over_streaming"] is not None),
    "median_python_peak_ratio":statistics.median(p["python_peak_ratio_eager_over_streaming"] for p in ps if p["python_peak_ratio_eager_over_streaming"] is not None)})
 out={"all_checks_pass":src and coverage and parity,"gates":{"sources_current":src,"complete_schedule_no_errors":coverage,"complete_pools_and_exact_parity":parity},
      "pairs":pairs,"summaries":summaries,"capture_sha256":sha(RAW)}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
 print(json.dumps({"analysis":str(OUT.relative_to(ROOT)),"all_checks_pass":out["all_checks_pass"],"gates":out["gates"]},indent=2))
 if not out["all_checks_pass"]:raise SystemExit(1)
if __name__=="__main__":main()

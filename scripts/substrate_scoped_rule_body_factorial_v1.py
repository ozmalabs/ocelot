#!/usr/bin/env python3
"""Factorial no-match probe: scoped matcher pattern size x effect payload size."""
from __future__ import annotations
import hashlib,json,random,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/"runners/dsl/python"),str(ROOT)]
from domains.engine_provenance import build_is_stale,rust_source_fingerprint
from substrate_rs import Substrate
from substrate_rs.ext import add_rule
LOCK=ROOT/"docs/research/engine_substrate/SUBSTRATE_SCOPED_RULE_BODY_FACTORIAL_PREREG_20260926.md"
OUT=ROOT/"evaluation/reports/substrate_scoped_rule_body_factorial_v1_20260926.json"
NATIVE=ROOT/"runners/dsl/python/substrate_rs/_native.abi3.so"
ACTIVE=(64,256,512);REPEATS=5;CALLS=30
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def fixture(active,edge_n,effect_n):
 s=Substrate();mt=s.add_node("Microtheory",{"fixed":True});c=s.add_node("Concept",{"fixed":True});s.add_edge_unchecked(mt,"has_concept",c)
 for i in range(active):
  edges=[(f"x{j}",f"absent_{i}_{j}",f"y{j}") for j in range(edge_n)]
  effects=[["set_attr",f"y{j}",f"unused_{j}",True] for j in range(effect_n)]
  add_rule(s._inner,f"factor_{i}",edges,effects)
 return s,mt,c
def state(s,mt,c):
 a,b=s.node(mt),s.node(c);rs=s._inner.export_rules()
 return (s.node_count(),s.edge_count(),a["type"],a["attrs"],b["type"],b["attrs"],s.has_edge(mt,"has_concept",c),s._inner.rule_count(),sum(bool(x["active"]) for x in rs))
def run(active,en,fn,rep):
 s,mt,c=fixture(active,en,fn);q=s._inner;q.scale_audit_set_per_rule_enabled(False);q.scale_audit_set_enabled(False)
 assert int(q.run_rules_scoped(100000,False,mt))==0
 before=state(s,mt,c);q.scale_audit_reset();w0,c0=time.perf_counter_ns(),time.process_time_ns()
 outcomes=[int(q.run_rules_scoped(100000,False,mt)) for _ in range(CALLS)]
 wall,cpu=time.perf_counter_ns()-w0,time.process_time_ns()-c0;counts=dict(q.scale_audit_snapshot());after=state(s,mt,c)
 return {"active":active,"match_edges_per_rule":en,"effects_per_rule":fn,"repeat":rep,"calls":CALLS,"outcomes":outcomes,"before":before,"after":after,"wall_ns":wall,"cpu_ns":cpu,"ns_per_call":wall/CALLS,"counters":counts}
def main():
 if build_is_stale(str(ROOT)):raise SystemExit("stale native build")
 rows=[]
 for rep in range(REPEATS):
  cells=[(n,e,f) for n in ACTIVE for e in (1,8) for f in (1,8)];random.Random(20260926+rep).shuffle(cells)
  rows.extend(run(n,e,f,rep) for n,e,f in cells)
 inputs={"protocol":sha(LOCK),"runner":sha(Path(__file__)),**{k:sha(ROOT/p) for k,p in {"graph_rs":"runners/dsl/src/graph.rs","substrate_rs":"runners/dsl/src/substrate.rs","rewrite_rs":"runners/dsl/src/rewrite.rs","py_rs":"runners/dsl/src/py.rs","scale_audit_rs":"runners/dsl/src/scale_audit.rs"}.items()},"native":sha(NATIVE),"rust_source_fingerprint":rust_source_fingerprint(str(ROOT))}
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps({"protocol_id":"SUBSTRATE_SCOPED_RULE_BODY_FACTORIAL_20260926","active_counts":ACTIVE,"repeats":REPEATS,"calls_per_cell":CALLS,"rows":rows,"inputs":inputs},indent=2,sort_keys=True)+"\n")
 print(json.dumps({"output":str(OUT),"cells":len(rows),"stable":all(r["outcomes"]==[0]*CALLS and r["before"]==r["after"] for r in rows)},indent=2))
if __name__=="__main__":main()

#!/usr/bin/env python3
"""Locked generated syntax and native closure comparison for finite-key rules."""
from __future__ import annotations
import hashlib,json,os,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/"scripts"),str(ROOT/"runners/dsl/python")]
from substrate_run_manifest import capture_run_manifest,finish_console_capture,start_console_capture
from analyze_mint_termination_fragment import analyze
from substrate_rs import _native
PROTOCOL=ROOT/"docs/research/engine_substrate/SUBSTRATE_FINITE_KEY_GENERATED_GRAMMAR_V1_PROTOCOL_20260926.md"
LOCK=ROOT/"evaluation/substrate_capability/mint_termination_generated_grammar_v1_lock_20260926.json"
OUT=ROOT/"evaluation/reports/mint_termination_generated_grammar_v1_20260926.json"
RUN_ID="mint-termination-generated-grammar-v1-20260926"
FILES=("scripts/verify_mint_termination_generated_grammar_v1.py","scripts/analyze_mint_termination_generated_grammar_v1.py","scripts/analyze_mint_termination_fragment.py","scripts/substrate_run_manifest.py","docs/research/engine_substrate/SUBSTRATE_FINITE_KEY_GENERATED_GRAMMAR_V1_PROTOCOL_20260926.md","runners/dsl/src/py.rs","runners/dsl/src/rewrite.rs","runners/dsl/src/substrate.rs","runners/dsl/python/substrate_rs/_native.build.json")
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def lock_inputs():return {"sha256":{p:sha(ROOT/p) for p in FILES},"native_extension_sha256":sha(Path(_native.__file__).resolve()),"commit":subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()}
def make_case(name,rules,nodes,edges,expected_accept=True):
 return {"name":name,"rule_specs":rules,"initial_nodes":nodes,"initial_node_ids":[f"n{i}" for i in range(len(nodes))],"initial_edges":[[f"n{e[0]}",e[1],f"n{e[2]}"]+([e[3]] if len(e)==4 else []) for e in edges],"expected_accept":expected_accept}
def panel():
 vals=[("null",None),("false",False),("true",True),("zero",0),("negative",-3),("string","a"),("unicode","λ")]
 out=[]
 for label,value in vals:
  out.append(make_case("literal_"+label,[{"name":"r","match":[["x","link","y"]],"effects":[["add_node_if_absent","w","W",{"key":value}],["add_edge","y","made","w",{}]]}],[{"type":"Seed","attrs":{}},{"type":"Seed","attrs":{}}],[(0,"link",1)]))
 out += [
  make_case("empty_key",[{"name":"r","match":[["x","link","y"]],"effects":[["add_node_if_absent","w","W",{}],["add_edge","y","made","w",{}]]}],[{"type":"S","attrs":{}},{"type":"S","attrs":{}}],[(0,"link",1)]),
  make_case("multi_attr_key",[{"name":"r","match":[["x","link","y"]],"effects":[["add_node_if_absent","w","W",{"a":1,"b":"v","c":True}],["add_edge","y","made","w",{}]]}],[{"type":"S","attrs":{}},{"type":"S","attrs":{}}],[(0,"link",1)]),
  make_case("existing_matching_witness",[{"name":"r","match":[["x","link","y"]],"effects":[["add_node_if_absent","w","W",{"tag":"old"}],["add_edge","y","made","w",{}]]}],[{"type":"S","attrs":{}},{"type":"S","attrs":{}},{"type":"W","attrs":{"tag":"old","extra":1}}],[(0,"link",1)]),
  make_case("repeated_variable_self_join",[{"name":"r","match":[["x","loop","x"]],"effects":[["add_node_if_absent","w","W",{"tag":"loop"}],["add_edge","x","made","w",{}]]}],[{"type":"S","attrs":{}}],[(0,"loop",0)]),
  make_case("two_edge_join",[{"name":"r","match":[["x","a","y"],["y","b","z"]],"effects":[["add_node_if_absent","w","W",{"tag":"join"}],["add_edge","z","made","w",{}]]}],[{"type":"S","attrs":{}},{"type":"S","attrs":{}},{"type":"S","attrs":{}}],[(0,"a",1),(1,"b",2)]),
  make_case("three_edge_join",[{"name":"r","match":[["x","a","y"],["y","b","z"],["z","c","x"]],"effects":[["add_node_if_absent","w","W",{"tag":"cycle"}],["add_edge","x","made","w",{}]]}],[{"type":"S","attrs":{}},{"type":"S","attrs":{}},{"type":"S","attrs":{}}],[(0,"a",1),(1,"b",2),(2,"c",0)]),
  make_case("minted_endpoint_recursion",[{"name":"r","match":[["x","link","y"]],"effects":[["add_node_if_absent","w","W",{"tag":"r"}],["add_edge","w","link","w",{}],["add_edge","y","made","w",{}]]}],[{"type":"S","attrs":{}},{"type":"S","attrs":{}}],[(0,"link",1)]),
  make_case("two_rule_interaction",[{"name":"a","match":[["x","link","y"]],"effects":[["add_node_if_absent","w","A",{"tag":"a"}],["add_edge","x","made_a","w",{}]]},{"name":"b","match":[["x","made_a","a"]],"effects":[["add_node_if_absent","v","B",{"tag":"b"}],["add_edge","a","made_b","v",{}]]}],[{"type":"S","attrs":{}},{"type":"S","attrs":{}}],[(0,"link",1)]),
 ]
 bad=[
  ("extra_rule_field",[{"name":"r","match":[["x","link","y"]],"where":None,"effects":[["add_edge","x","z","y",{}]]}], [{"type":"S","attrs":{}},{"type":"S","attrs":{}}],[(0,"link",1)]),
  ("empty_match",[{"name":"r","match":[],"effects":[["add_node_if_absent","w","W",{}]]}],[{"type":"S","attrs":{}}],[]),
  ("unrestricted_mint",[{"match":[["x","link","y"]],"effects":[["add_node","w","W",{"tag":"x"}]]}],[{"type":"S","attrs":{}},{"type":"S","attrs":{}}],[(0,"link",1)]),
  ("computed_key",[{"match":[["x","link","y"]],"effects":[["add_node_if_absent","w","W",{"tag":{"__term__":{"type":"var","name":"y"}}}]]}],[{"type":"S","attrs":{}},{"type":"S","attrs":{}}],[(0,"link",1)]),
  ("nonempty_output_edge_attrs",[{"match":[["x","link","y"]],"effects":[["add_edge","x","z","y",{"weight":1}]]}],[{"type":"S","attrs":{}},{"type":"S","attrs":{}}],[(0,"link",1)]),
  ("unbound_endpoint",[{"match":[["x","link","y"]],"effects":[["add_edge","q","z","y",{}]]}],[{"type":"S","attrs":{}},{"type":"S","attrs":{}}],[(0,"link",1)]),
  ("forward_endpoint",[{"match":[["x","link","y"]],"effects":[["add_edge","x","z","w",{}],["add_node_if_absent","w","W",{}]]}],[{"type":"S","attrs":{}},{"type":"S","attrs":{}}],[(0,"link",1)]),
  ("reused_mint_variable",[{"match":[["x","link","y"]],"effects":[["add_node_if_absent","w","W",{"k":1}],["add_node_if_absent","w","V",{"k":2}]]}],[{"type":"S","attrs":{}},{"type":"S","attrs":{}}],[(0,"link",1)]),
  ("unsupported_effect",[{"match":[["x","link","y"]],"effects":[["del_edge","x","link","y"]]}],[{"type":"S","attrs":{}},{"type":"S","attrs":{}}],[(0,"link",1)]),
  ("edge_attr_write_conflict",[{"match":[["x","link","y"]],"effects":[["add_edge","x","link","y",{}]]}],[{"type":"S","attrs":{}},{"type":"S","attrs":{}}],[(0,"link",1,{"weight":2})]),
 ]
 out.extend(make_case(n,r,ns,es,False) for n,r,ns,es in bad)
 return out
def bindings(patterns,edges):
 states=[{}]
 for src,typ,tgt in patterns:
  nxt=[]
  for env in states:
   for a,t,b in edges:
    if t!=typ:continue
    e=dict(env);ok=True
    for var,val in ((src,a),(tgt,b)):
     if var in e and e[var]!=val:ok=False;break
     e[var]=val
    if ok:nxt.append(e)
  states=nxt
 return states
def closure(rule_specs,nodes,edges):
 nodes=[dict(n) for n in nodes];edges=set(tuple(e) for e in edges); changed=True; rounds=0
 while changed:
  changed=False;rounds+=1
  if rounds>1000:raise RuntimeError("oracle closure guard exceeded")
  for rule in rule_specs:
   for env in bindings(rule["match"],edges):
    for eff in rule["effects"]:
     op=eff[0]
     if op=="add_node_if_absent":
      _,var,typ,attrs=eff
      found=next((i for i,n in enumerate(nodes) if n["type"]==typ and all(k in n["attrs"] and n["attrs"][k]==v for k,v in attrs.items())),None)
      if found is None:
       found=len(nodes);nodes.append({"type":typ,"attrs":dict(attrs)});changed=True
      env[var]=found
     elif op=="add_edge":
      _,src,typ,tgt,_attrs=eff;edge=(env[src],typ,env[tgt])
      if edge not in edges:edges.add(edge);changed=True
 return nodes,edges,rounds
def main():
 if sys.argv[1:]==["--lock"]:print(json.dumps({"locked_inputs":lock_inputs()},indent=2,sort_keys=True));return 0
 started=datetime.now(timezone.utc).isoformat();log=start_console_capture(RUN_ID);locked=lock_inputs()
 if not LOCK.is_file() or json.loads(LOCK.read_text()).get("locked_inputs")!=locked:raise SystemExit("missing or stale generated grammar lock")
 from domains.engine_provenance import build_is_stale
 stale=build_is_stale(str(ROOT))
 if stale:raise SystemExit(f"native build stale: {stale}")
 cases=panel();rows=[];print("generated grammar cases:",len(cases),flush=True)
 for case in cases:
  analysis=analyze(case["rule_specs"],case["initial_node_ids"],case["initial_edges"])
  row={"name":case["name"],"expected_accept":case["expected_accept"],"checker_accepted":analysis["accepted"],"checker_reasons":analysis["reasons"],"bound":analysis["progress_steps_upper_bound"]}
  if case["expected_accept"]:
   if not analysis["accepted"]:row["passed"]=False;rows.append(row);continue
   s=_native.Substrate();ids=[s.add_node(n["type"],n["attrs"]) for n in case["initial_nodes"]]
   for a,t,b in (tuple(e[:3]) for e in case["initial_edges"]):s.add_edge_unchecked(ids[int(a[1:])],t,ids[int(b[1:])])
   for rule in case["rule_specs"]:s.add_rule(rule)
   report=s.run_rules_report(max(100,analysis["progress_steps_upper_bound"]+10),False);native=s.graph_to_dict()
   ref_nodes,ref_edges,oracle_rounds=closure(case["rule_specs"],case["initial_nodes"],[(int(a[1:]),t,int(b[1:])) for a,t,b in case["initial_edges"]])
   native_nodes=[{"type":n["type"],"attrs":n["attrs"]} for n in native["nodes"]]
   actual_edges={(e["src"],e["type"],e["tgt"]) for e in native["edges"]};expected_edges=set(ref_edges)
   # Initial native IDs equal their insertion ordinals; oracle mint order follows rule/effect order.
   graph_equal=native_nodes==ref_nodes and actual_edges==expected_edges
   row.update({"native_status":report["status"],"native_progress_steps":report["progress_steps"],"native_passes":report["passes_completed"],"native_nodes":len(native_nodes),"native_edges":len(actual_edges),"oracle_rounds":oracle_rounds,"oracle_nodes":len(ref_nodes),"oracle_edges":len(ref_edges),"exact_graph_match":graph_equal,"within_bound":report["progress_steps"]<=analysis["progress_steps_upper_bound"],"passed":report["status"]=="fixed_point" and graph_equal and report["progress_steps"]<=analysis["progress_steps_upper_bound"]})
  else:row["passed"]=not analysis["accepted"]
  rows.append(row)
 post=lock_inputs();logref=finish_console_capture(log);ok=all(x["passed"] for x in rows) and post==locked
 manifest=capture_run_manifest(run_id=RUN_ID,runner="scripts/verify_mint_termination_generated_grammar_v1.py",protocol_files=(str(PROTOCOL.relative_to(ROOT)),str(LOCK.relative_to(ROOT))),source_files=("scripts/analyze_mint_termination_fragment.py","scripts/substrate_run_manifest.py","runners/dsl/src/py.rs","runners/dsl/src/rewrite.rs","runners/dsl/src/substrate.rs"),analysis_files=("scripts/analyze_mint_termination_generated_grammar_v1.py",),started_utc=started,exit_status=0 if ok else 1,stdout_stderr_capture=logref)
 result={"schema_version":1,"run_id":RUN_ID,"locked_inputs":locked,"post_run_inputs":post,"lock_sha256":sha(LOCK),"case_count":len(rows),"accepted_count":sum(x["expected_accept"] for x in rows),"rejected_count":sum(not x["expected_accept"] for x in rows),"passed_count":sum(x["passed"] for x in rows),"rows":rows,"all_checks_pass":ok,"run_manifest":manifest}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n");print(json.dumps({"case_count":len(rows),"passed_count":result["passed_count"],"all_checks_pass":ok},sort_keys=True));return 0 if ok else 1
if __name__=="__main__":raise SystemExit(main())

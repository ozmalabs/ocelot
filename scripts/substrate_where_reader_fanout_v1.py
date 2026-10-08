#!/usr/bin/env python3
"""Source-locked rule-fanout panel for edge-deletion where readers."""
from __future__ import annotations
import hashlib,json,os,subprocess,sys,time
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/"runners/dsl/python"),str(ROOT/"scripts")]
from substrate_rs import _native
from domains.engine_provenance import build_is_stale
from substrate_run_manifest import capture_run_manifest,finish_console_capture,start_console_capture
PROTOCOL=ROOT/"docs/research/engine_substrate/SUBSTRATE_WHERE_READER_FANOUT_V1_PREREG_20260928.md"
LOCK=ROOT/"evaluation/substrate_capability/where_reader_fanout_v1_lock_20260928.json"
RAW=ROOT/"evaluation/reports/substrate_where_reader_fanout_v1_20260928.json"
RUN_ID="substrate-where-reader-fanout-v1-20260928"
FILES=("scripts/substrate_where_reader_fanout_v1.py","scripts/analyze_substrate_where_reader_fanout_v1.py","scripts/substrate_run_manifest.py","domains/engine_provenance.py",str(PROTOCOL.relative_to(ROOT)),"runners/dsl/src/graph.rs","runners/dsl/src/substrate.rs","runners/dsl/src/rewrite.rs","runners/dsl/src/term.rs","runners/dsl/src/scale_audit.rs","runners/dsl/src/py.rs","runners/dsl/python/substrate_rs/_native.build.json","runners/dsl/Cargo.toml","runners/dsl/Cargo.lock")
SIZES=(32,128);FANOUTS=(1,4,16);FAMILIES=("out_edges","in_neighbours");ARMS=("off","incremental","unsound")
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def fingerprint():
 native=Path(_native.__file__).resolve()
 return {"commit":subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip(),"files":{p:sha(ROOT/p) for p in FILES},"native_path":str(native),"native_sha256":sha(native),"native_build_stale":build_is_stale(str(ROOT))}
def one_arm(n,readers,family,mode):
 s=_native.Substrate();g=s;g.set_incremental_match(mode!="off")
 if mode=="unsound":g.set_incremental_match_unsound(True)
 root=g.add_node("Root",{});slots=[g.add_node("Slot",{}) for _ in range(n)]
 blockers=[g.add_node("Blocker",{}) for _ in range(n)]
 for slot in slots:g.add_edge_unchecked(root,"slot",slot,{})
 if family=="out_edges":
  for blocker in blockers:g.add_edge_unchecked(root,"block",blocker,{})
  source={"type":"Edges","node":{"type":"Var","name":"x"},"edge_type":"block"}
 else:
  for blocker,slot in zip(blockers,slots):g.add_edge_unchecked(blocker,"block",slot,{})
  source={"type":"InNeighbours","node":{"type":"Var","name":"y"},"edge_type":"block"}
 where={"type":"Eq","a":{"type":"Count","source":source},"b":{"type":"Lit","value":0}}
 rule_ids=[]
 for i in range(readers):
  rule_ids.append(g.add_rule({"name":f"fanout_reader_{i}","match":[["x","slot","y"]],"where":where,"effects":[["set_attr","y",f"opened_by_{i}",1]]}))
 accesses=[next(row for row in g.rule_access_sets() if row[0]==idx) for idx in rule_ids]
 initial=dict(g.run_rules_report(100000,False));initial_open=sum(bool(g.node(slot)["attrs"]) for slot in slots)
 g.scale_audit_reset();g.scale_audit_set_enabled(True)
 started=time.perf_counter_ns()
 if family=="out_edges":
  removed=[g.remove_edge(root,"block",blocker) for blocker in blockers]
 else:
  removed=[g.remove_edge(blocker,"block",slot) for blocker,slot in zip(blockers,slots)]
 delete_ns=time.perf_counter_ns()-started
 started=time.perf_counter_ns();post=dict(g.run_rules_report(100000,False));settle_ns=time.perf_counter_ns()-started
 metrics=dict(g.scale_audit_snapshot());g.scale_audit_set_enabled(False)
 graph=g.graph_to_dict();node_attrs={row["id"]:row.get("attrs",{}) for row in graph["nodes"]}
 opened=sorted(slot.value for slot in slots if any(node_attrs.get(slot.value,{}).get(f"opened_by_{i}")==1 for i in range(readers)))
 return {"n":n,"reader_count":readers,"family":family,"mode":mode,"initial_report":initial,"initial_open":initial_open,"removed_count":sum(removed),"delete_wall_ns":delete_ns,"post_report":post,"settle_wall_ns":settle_ns,"metrics":metrics,"opened_ids":opened,"open_count":len(opened),"graph":graph,"graph_sha256":hashlib.sha256(json.dumps(graph,sort_keys=True,separators=(",",":")).encode()).hexdigest(),"accesses":[{"read_set":list(a[3]),"term_edge_reads":list(a[4]),"reads_any":a[6]} for a in accesses],"remaining_block_edges":sum(e["type"]=="block" for e in graph["edges"])}
def worker(n,readers,family,rep):
 before=fingerprint();arms={mode:one_arm(n,readers,family,mode) for mode in ARMS};after=fingerprint()
 return {"n":n,"reader_count":readers,"family":family,"replicate":rep,"pid":os.getpid(),"before":before,"after":after,"arms":arms}
def main():
 if sys.argv[1:]==["--lock"]:
  fp=fingerprint()
  if fp["native_build_stale"]:raise SystemExit("native build is stale")
  LOCK.parent.mkdir(parents=True,exist_ok=True);LOCK.write_text(json.dumps(fp,indent=2,sort_keys=True)+"\n");print(LOCK);return 0
 if len(sys.argv)==6 and sys.argv[1]=="--worker":
  print(json.dumps(worker(int(sys.argv[2]),int(sys.argv[3]),sys.argv[4],int(sys.argv[5])),sort_keys=True));return 0
 before=fingerprint()
 if before["native_build_stale"] or not LOCK.exists() or json.loads(LOCK.read_text())!=before:raise SystemExit("missing/stale source lock or native build")
 env=dict(os.environ);env["PYTHONPATH"]=os.pathsep.join((str(ROOT),str(ROOT/"runners/dsl/python"),str(ROOT/"scripts"),env.get("PYTHONPATH","")))
 started=datetime.now(timezone.utc).isoformat();log=start_console_capture(RUN_ID);rows=[]
 for family in FAMILIES:
  for n in SIZES:
   for readers in FANOUTS:
    for rep in range(3):
     cmd=[sys.executable,str(Path(__file__).resolve()),"--worker",str(n),str(readers),family,str(rep)]
     cp=subprocess.run(cmd,cwd=ROOT,env=env,text=True,capture_output=True,check=True);rows.append(json.loads(cp.stdout))
 after=fingerprint()
 checks={"36_unique_workers":len(rows)==36 and len({r["pid"] for r in rows})==36,"three_replicates_per_cell":all(sum(r["n"]==n and r["reader_count"]==m and r["family"]==f for r in rows)==3 for f in FAMILIES for n in SIZES for m in FANOUTS),"source_lock_stable":before==after and all(r["before"]==before==r["after"] for r in rows),"fresh_native_build":not before["native_build_stale"],"exact_rule_access_sets":all(all(a["read_set"]==["edge:block","edge:slot"] and a["term_edge_reads"]==["edge:block"] and not a["reads_any"] for a in r["arms"][mode]["accesses"]) for r in rows for mode in ARMS),"initial_fixed_points":all(r["arms"][mode]["initial_report"]["status"]=="fixed_point" and r["arms"][mode]["initial_open"]==0 for r in rows for mode in ARMS),"all_block_edges_deleted":all(r["arms"][mode]["removed_count"]==r["n"] and r["arms"][mode]["remaining_block_edges"]==0 for r in rows for mode in ARMS),"sound_arms_open_all":all(r["arms"][mode]["post_report"]["status"]=="fixed_point" and r["arms"][mode]["open_count"]==r["n"] for r in rows for mode in ("off","incremental")),"off_incremental_graph_identity":all(r["arms"]["off"]["graph"]==r["arms"]["incremental"]["graph"] for r in rows),"unsound_falsifier_misses_all":all(r["arms"]["unsound"]["open_count"]==0 for r in rows)}
 logref=finish_console_capture(log);manifest=capture_run_manifest(run_id=RUN_ID,runner="scripts/substrate_where_reader_fanout_v1.py",protocol_files=(str(PROTOCOL.relative_to(ROOT)),str(LOCK.relative_to(ROOT))),source_files=tuple(p for p in FILES if p.startswith("runners/"))+("scripts/substrate_run_manifest.py","domains/engine_provenance.py"),analysis_files=("scripts/analyze_substrate_where_reader_fanout_v1.py",),started_utc=started,exit_status=0 if all(checks.values()) else 1,stdout_stderr_capture=logref)
 raw={"schema_version":1,"run_id":RUN_ID,"locked_inputs":before,"post_run_inputs":after,"schedule":[[r["family"],r["n"],r["reader_count"],r["replicate"]] for r in rows],"checks":checks,"all_checks_pass":all(checks.values()),"runs":rows,"run_manifest":manifest,"claim_boundary":"Two where-only edge-count reader families, three fan-outs, two sizes, and three matching modes; synthetic deletion-work panel only."}
 RAW.write_text(json.dumps(raw,indent=2,sort_keys=True)+"\n");print(json.dumps({"checks":checks,"all_checks_pass":raw["all_checks_pass"],"raw":str(RAW.relative_to(ROOT))},indent=2));return 0 if raw["all_checks_pass"] else 1
if __name__=="__main__":raise SystemExit(main())

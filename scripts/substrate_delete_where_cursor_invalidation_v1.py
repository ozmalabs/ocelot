#!/usr/bin/env python3
"""Locked full-rescan / incremental / unsound where-cursor deletion panel."""
from __future__ import annotations
import hashlib,json,os,subprocess,sys,time
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/"runners/dsl/python"),str(ROOT/"scripts")]
from substrate_rs import _native
from domains.engine_provenance import build_is_stale
from substrate_run_manifest import capture_run_manifest,finish_console_capture,start_console_capture
PROTOCOL=ROOT/"docs/research/engine_substrate/SUBSTRATE_DELETE_WHERE_CURSOR_INVALIDATION_V1_PREREG_20260928.md"
AMENDMENT=ROOT/"docs/research/engine_substrate/SUBSTRATE_DELETE_WHERE_CURSOR_INVALIDATION_V1_1_AMENDMENT_20260928.md"
LOCK=ROOT/"evaluation/substrate_capability/delete_where_cursor_invalidation_v1_1_lock_20260928.json"
RAW=ROOT/"evaluation/reports/substrate_delete_where_cursor_invalidation_v1_1_20260928.json"
RUN_ID="substrate-delete-where-cursor-invalidation-v1-1-20260928"
FILES=("scripts/substrate_delete_where_cursor_invalidation_v1.py","scripts/analyze_substrate_delete_where_cursor_invalidation_v1.py","scripts/substrate_run_manifest.py","domains/engine_provenance.py",str(PROTOCOL.relative_to(ROOT)),str(AMENDMENT.relative_to(ROOT)),"runners/dsl/src/graph.rs","runners/dsl/src/substrate.rs","runners/dsl/src/rewrite.rs","runners/dsl/src/term.rs","runners/dsl/src/scale_audit.rs","runners/dsl/src/py.rs","runners/dsl/python/substrate_rs/_native.build.json","runners/dsl/Cargo.toml","runners/dsl/Cargo.lock")
SIZES=(8,32,128)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def fingerprint():
 native=Path(_native.__file__).resolve()
 return {"commit":subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip(),"files":{p:sha(ROOT/p) for p in FILES},"native_path":str(native),"native_sha256":sha(native),"native_build_stale":build_is_stale(str(ROOT))}
def one_arm(n,mode):
 s=_native.Substrate();s.set_incremental_match(mode!="off")
 if mode=="unsound":s.set_incremental_match_unsound(True)
 root=s.add_node("Root",{});slots=[s.add_node("Slot",{}) for _ in range(n)];blocker=s.add_node("Blocker",{})
 for slot in slots:s.add_edge_unchecked(root,"slot",slot,{})
 s.add_edge_unchecked(root,"block",blocker,{})
 count={"type":"Count","source":{"type":"Edges","node":{"type":"Var","name":"x"},"edge_type":"block"}}
 where={"type":"Eq","a":count,"b":{"type":"Lit","value":0}}
 rule=s.add_rule({"name":"delete_where_reader","match":[["x","slot","y"]],"where":where,"effects":[["set_attr","y","open",1]]})
 access=next(row for row in s.rule_access_sets() if row[0]==rule)
 initial=dict(s.run_rules_report(100000,False));initial_open=sum(s.node(x)["attrs"].get("open")==1 for x in slots)
 s.scale_audit_reset();s.scale_audit_set_enabled(True);removed=s.remove_node(blocker)
 t=time.perf_counter_ns();post=dict(s.run_rules_report(100000,False));wall=time.perf_counter_ns()-t
 metrics=dict(s.scale_audit_snapshot());s.scale_audit_set_enabled(False)
 graph=s.graph_to_dict();attrs={x["id"]:x.get("attrs",{}) for x in graph["nodes"]}
 open_ids=sorted(nid for nid,a in attrs.items() if a.get("open")==1)
 return {"mode":mode,"n":n,"initial_report":initial,"initial_open":initial_open,"node_removed":removed,"post_report":post,"post_delete_wall_ns":wall,"metrics":metrics,"open_ids":open_ids,"open_count":len(open_ids),"graph":graph,"graph_sha256":hashlib.sha256(json.dumps(graph,sort_keys=True,separators=(",",":")).encode()).hexdigest(),"where_read_set":list(access[3]),"term_edge_reads":list(access[4]),"match_edge_type":access[1]}
def worker(n,rep):
 before=fingerprint();arms={m:one_arm(n,m) for m in ("off","incremental","unsound")};after=fingerprint()
 return {"n":n,"replicate":rep,"pid":os.getpid(),"before":before,"after":after,"arms":arms}
def main():
 if sys.argv[1:]==["--lock"]:
  fp=fingerprint()
  if fp["native_build_stale"]:raise SystemExit("native build is stale")
  LOCK.parent.mkdir(parents=True,exist_ok=True);LOCK.write_text(json.dumps(fp,indent=2,sort_keys=True)+"\n");print(LOCK);return 0
 if len(sys.argv)==4 and sys.argv[1]=="--worker":print(json.dumps(worker(int(sys.argv[2]),int(sys.argv[3])),sort_keys=True));return 0
 before=fingerprint()
 if before["native_build_stale"] or not LOCK.exists() or json.loads(LOCK.read_text())!=before:raise SystemExit("missing/stale source lock or native build")
 env=dict(os.environ);env["PYTHONPATH"]=os.pathsep.join((str(ROOT),str(ROOT/"runners/dsl/python"),str(ROOT/"scripts"),env.get("PYTHONPATH","")))
 started=datetime.now(timezone.utc).isoformat();log=start_console_capture(RUN_ID);rows=[]
 for n in SIZES:
  for rep in range(3):
   cp=subprocess.run([sys.executable,str(Path(__file__).resolve()),"--worker",str(n),str(rep)],cwd=ROOT,env=env,text=True,capture_output=True,check=True);rows.append(json.loads(cp.stdout))
 after=fingerprint()
 checks={"nine_unique_workers":len(rows)==9 and len({r["pid"] for r in rows})==9,"three_replicates_per_size":all(sum(r["n"]==n for r in rows)==3 for n in SIZES),"source_lock_stable":before==after and all(r["before"]==before==r["after"] for r in rows),"fresh_native_build":not before["native_build_stale"],"initial_fixed_points":all(r["arms"][m]["initial_report"]["status"]=="fixed_point" and r["arms"][m]["initial_open"]==0 for r in rows for m in ("off","incremental","unsound")),"where_only_dependency":all(a["where_read_set"]==["edge:block","edge:slot"] and a["term_edge_reads"]==["edge:block"] for r in rows for a in r["arms"].values()),"post_delete_all_modes_open_all":all(r["arms"][m]["node_removed"] and r["arms"][m]["post_report"]["status"]=="fixed_point" and r["arms"][m]["open_count"]==r["n"] for r in rows for m in ("off","incremental","unsound")),"all_mode_graph_identity":all(len({r["arms"][m]["graph_sha256"] for m in ("off","incremental","unsound")})==1 for r in rows)}
 logref=finish_console_capture(log);manifest=capture_run_manifest(run_id=RUN_ID,runner="scripts/substrate_delete_where_cursor_invalidation_v1.py",protocol_files=(str(PROTOCOL.relative_to(ROOT)),str(AMENDMENT.relative_to(ROOT)),str(LOCK.relative_to(ROOT))),source_files=tuple(p for p in FILES if p.startswith("runners/"))+ ("scripts/substrate_run_manifest.py","domains/engine_provenance.py"),analysis_files=("scripts/analyze_substrate_delete_where_cursor_invalidation_v1.py",),started_utc=started,exit_status=0 if all(checks.values()) else 1,stdout_stderr_capture=logref)
 raw={"schema_version":1,"run_id":RUN_ID,"locked_inputs":before,"post_run_inputs":after,"checks":checks,"all_checks_pass":all(checks.values()),"runs":rows,"run_manifest":manifest,"claim_boundary":"One where-only edge reader after public blocker-node deletion; all modes are refreshed by the generic where-rule cursor invalidation fallback, so this does not isolate type-local cursor clearing."}
 RAW.write_text(json.dumps(raw,indent=2,sort_keys=True)+"\n");print(json.dumps({"checks":checks,"all_checks_pass":raw["all_checks_pass"],"raw":str(RAW.relative_to(ROOT))},indent=2));return 0 if raw["all_checks_pass"] else 1
if __name__=="__main__":raise SystemExit(main())

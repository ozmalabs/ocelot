#!/usr/bin/env python3
"""Bounded sample order estimates for a three-edge join chain."""
from __future__ import annotations
import hashlib,json,os,random,resource,subprocess,sys,time,tracemalloc
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/"runners/dsl/python"))
from substrate_rs import Substrate,_native
from domains.engine_provenance import assert_measuring_engine
PROTOCOL=ROOT/"docs/research/engine_substrate/SUBSTRATE_BOUNDED_THREE_EDGE_ORDER_V1_PREREG_20260927.md"
LOCK=ROOT/"evaluation/substrate_capability/bounded_three_edge_order_v1_lock_20260927.json"
OUT=ROOT/"evaluation/reports/substrate_bounded_three_edge_order_v1_20260927.json"
RAW=ROOT/"evaluation/reports/substrate_bounded_three_edge_order_v1_workers_raw_20260927.json"
SOURCES=("runners/dsl/src/scale_audit.rs","runners/dsl/src/substrate.rs","runners/dsl/src/rewrite.rs","runners/dsl/src/py.rs","runners/dsl/src/framebuffer.rs","runners/dsl/src/graph.rs")
PREDECESSORS=("docs/research/engine_substrate/SUBSTRATE_ENDPOINT_DEGREE_JOIN_ORDER_V1_RESULTS_20260927.md","evaluation/reports/substrate_endpoint_degree_join_order_v1_analysis_20260926.json","docs/research/engine_substrate/SUBSTRATE_JOIN_DEGREE_SKEW_V1_RESULTS_20260926.md","evaluation/reports/substrate_join_degree_skew_v1_analysis_20260926.json")
FAMILIES=("rule_edits","fb_samples")
ORDERS=("LMR","RML","LRM","RLM")
AUTHORED_FOR_INSTALLED={"LMR":("left","right","middle"),"RML":("left","middle","right"),"LRM":("middle","right","left"),"RLM":("middle","left","right")}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def fingerprint():
 paths=(*SOURCES,*PREDECESSORS,"scripts/substrate_bounded_three_edge_order_v1.py","scripts/analyze_substrate_bounded_three_edge_order_v1.py",str(PROTOCOL.relative_to(ROOT)),"runners/dsl/python/substrate_rs/_native.build.json")
 return {"files":{p:sha(ROOT/p) for p in paths},"native_extension":sha(Path(_native.__file__).resolve()),"native_path":str(Path(_native.__file__).resolve()),"commit":subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()}
def write_frame(path):
 buf=bytearray(128);buf[:4]=(0x4A425746).to_bytes(4,"little");buf[4:8]=(1).to_bytes(4,"little");buf[8:12]=(4).to_bytes(4,"little");buf[12:16]=(4).to_bytes(4,"little");buf[16:20]=(16).to_bytes(4,"little");buf[20:24]=(1).to_bytes(4,"little");buf[24:32]=(1).to_bytes(8,"little")
 for i in range(64,len(buf),4):buf[i:i+4]=bytes((20,40,60,255))
 Path(path).write_bytes(buf)
def add_relation(s,table,src,edge,tgt):
 s._inner.add_edge_unchecked(src,edge,tgt);table["by_type"].setdefault(edge,[]).append((src,tgt));table["out"].setdefault((src,edge),[]).append(tgt);table["in"].setdefault((tgt,edge),[]).append(src)
def sample_order(order,budget,table,root,seed):
 rng=random.Random(seed);states=[root.copy()];population=1.0;work_by_edge={};sampled_candidates=0
 specs={"left":("a","left","x"),"middle":("x","middle","y"),"right":("y","right","b")}
 for code in order:
  name={"L":"left","M":"middle","R":"right"}[code]
  sv,et,tv=specs[name]
  if len(states)>budget:parents=rng.sample(states,budget)
  else:parents=states
  candidate_n=[];views=[]
  for st in parents:
   if sv in st:mode="out";view=table["out"].get((st[sv],et),[])
   elif tv in st:mode="in";view=table["in"].get((st[tv],et),[])
   else:mode="all";view=table["by_type"].get(et,[])
   views.append((mode,view,st));candidate_n.append(len(view))
  work_by_edge[name]=population*(sum(candidate_n)/max(1,len(candidate_n)))
  per_parent=max(1,budget//max(1,len(parents)));valid_samples=[];valid_estimates=[]
  for mode,view,st in views:
   n=len(view)
   if not n:valid_estimates.append(0.0);continue
   k=min(n,per_parent)
   idxs=list(range(n)) if n<=k else sorted(rng.sample(range(n),k));good=0
   for idx in idxs:
    if mode=="out":s,t=st[sv],view[idx]
    elif mode=="in":s,t=view[idx],st[tv]
    else:s,t=view[idx]
    if sv in st and st[sv]!=s:continue
    if tv in st and st[tv]!=t:continue
    nxt=st.copy();nxt[sv]=s;nxt[tv]=t;valid_samples.append(nxt);good+=1
   valid_estimates.append((n*good/k) if k else 0.0);sampled_candidates+=k
  mean_children=sum(valid_estimates)/max(1,len(valid_estimates));population*=mean_children
  if not valid_samples or population<=0:states=[];break
  if len(valid_samples)>budget:states=rng.sample(valid_samples,budget)
  else:states=valid_samples
 return {"order":order,"budget":budget,"estimated_path_candidate_tests":sum(work_by_edge.values()),"estimated_by_edge":work_by_edge,"estimated_complete_binding_count":population,"sampled_candidate_probes":sampled_candidates,"selected":None}
def estimate_one(table,root,m,q,rep,budget):
  cpu0=time.process_time_ns();wall0=time.perf_counter_ns()
  scores={o:sample_order(o,budget,table,root,m*100000+q*1000+rep*100+budget+oi) for oi,o in enumerate(ORDERS)}
  chosen=min(ORDERS,key=lambda o:scores[o]["estimated_path_candidate_tests"])
  for v in scores.values():v["selected"]=chosen
  return {"budget":budget,"scores":scores,"selected":chosen,"planning_cpu_ns":time.process_time_ns()-cpu0,"planning_wall_ns":time.perf_counter_ns()-wall0}
def planner_memory_probe(table,root,m,q,rep,budget):
  tracemalloc.start();wall0=time.perf_counter_ns()
  scores={o:sample_order(o,budget,table,root,m*100000+q*1000+rep*100+budget+oi) for oi,o in enumerate(ORDERS)}
  _,peak=tracemalloc.get_traced_memory();elapsed=time.perf_counter_ns()-wall0;tracemalloc.stop()
  return peak,elapsed,scores
def arm(m,q,rep,mode,shm_name,audit):
 s=Substrate();fb=s._inner.fb_attach(shm_name);a=s.add_node("JoinAnchor",{});b=s.add_node("JoinTarget",{});g=s.add_node("WorldInstance",{"world_type":"Game","frame":0.0,"last_looked_seq":-1.0});tbl={"by_type":{},"out":{},"in":{}}
 add_relation(s,tbl,a,"trigger",b);add_relation(s,tbl,a,"has_game",g);add_relation(s,tbl,b,"wants",g)
 for k in range(m):
  x=s.add_node("JoinX",{"kind":"true","ordinal":k});y=s.add_node("JoinY",{"kind":"true","ordinal":k});add_relation(s,tbl,a,"left",x);add_relation(s,tbl,x,"middle",y);add_relation(s,tbl,y,"right",b)
 d=q*m
 for k in range(d):
  x=s.add_node("JoinX",{"kind":"left_decoy","ordinal":k});add_relation(s,tbl,a,"left",x)
 for k in range(d):
  x=s.add_node("JoinX",{"kind":"middle_decoy_x","ordinal":k});y=s.add_node("JoinY",{"kind":"middle_decoy_y","ordinal":k});add_relation(s,tbl,x,"middle",y)
 for k in range(d):
  y=s.add_node("JoinY",{"kind":"right_decoy","ordinal":k});add_relation(s,tbl,y,"right",b)
 root={"a":a,"b":b,"g":g};estimate=None;planning_wall=planning_cpu=0;python_peak=memory_probe_wall=0
 if mode.startswith("sample_B"):
   budget=int(mode.split("B")[1]);estimate=estimate_one(tbl,root,m,q,rep,budget);planning_wall=estimate["planning_wall_ns"];planning_cpu=estimate["planning_cpu_ns"];order=estimate["selected"]
 elif mode=="control_RML":order="RML"
 else:order=mode.removeprefix("exact_")
 target="join_target";writer="join_writer";s._inner.add_rule({"name":target,"match":[["u","wants","g"]],"where":{"type":"Lit","value":False},"effects":[["add_edge","u","seen","g",{}]]})
 edges={"trigger":["a","trigger","b"],"game":["a","has_game","g"],"left":["a","left","x"],"middle":["x","middle","y"],"right":["y","right","b"]}
 authored=("trigger",*AUTHORED_FOR_INSTALLED[order],"game");match=[edges[z] for z in authored]
 t0=time.perf_counter_ns();wi=s._inner.add_rule({"name":writer,"match":match,"effects":[["set_rule_clause",target,"where",{"type":"Lit","value":True}],["fb_sample",fb,"g",2,2],["del_edge","a","trigger","b"]]});install_ns=time.perf_counter_ns()-t0;installed=[list(e) for e in s._inner.export_rules()[wi]["match"]]
 native=_native.Substrate;native.scale_audit_set_enabled(False);native.scale_audit_set_per_rule_enabled(False);native.scale_audit_reset();native.scale_audit_per_rule_reset()
 if audit:native.scale_audit_set_per_rule_enabled(True);native.scale_audit_set_enabled(True)
 cpu0=time.process_time_ns();wall0=time.perf_counter_ns();report=s._inner.run_rules_report(1000000,False);closure_wall=time.perf_counter_ns()-wall0;closure_cpu=time.process_time_ns()-cpu0;rss_plain=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
 counters=dict(native.scale_audit_snapshot()) if audit else {};per=[list(z) for z in native.scale_audit_per_rule_snapshot()] if audit else [];clauses=[list(z) for z in native.scale_audit_match_clause_snapshot()] if audit else []
 native.scale_audit_set_enabled(False);native.scale_audit_set_per_rule_enabled(False);graph=s.graph_to_dict();es=graph["edges"];rss_after=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
 if estimate is not None:
   python_peak,memory_probe_wall,_=planner_memory_probe(tbl,root,m,q,rep,estimate["budget"])
 return {"report":{k:report[k] for k in ("status","progress_steps","passes_completed","budget_overshoot")},"graph":graph,"seen_edges":sum(e["type"]=="seen" for e in es),"grid_cells":sum(n["type"]=="WorldInstance" and "row" in n["attrs"] for n in graph["nodes"]),"trigger_edges":sum(e["type"]=="trigger" for e in es),"writer_rule_index":wi,"mode":mode,"selected_order":order,"authored_order":list(authored),"installed_order":[e[1] for e in installed],"planner":estimate,"planning_wall_ns":planning_wall,"planning_cpu_ns":planning_cpu,"planner_python_peak_bytes":python_peak,"planner_memory_probe_wall_ns":memory_probe_wall,"writer_install_ns":install_ns,"closure_wall_ns":closure_wall,"closure_cpu_ns":closure_cpu,"peak_rss_kib_plain":rss_plain,"peak_rss_kib_after_readback":rss_after,"counters":counters,"per_rule":per,"clause_candidates":clauses}
def worker(m,q,mode,rep):
 path=f"/dev/shm/ocelot_bounded_join3_{os.getpid()}_{m}_{q}_{mode}";name="/"+Path(path).name
 try:
  write_frame(path);before=fingerprint();plain=arm(m,q,rep,mode,name,False);audit=arm(m,q,rep,mode,name,True);return {"multiplicity":m,"decoy_ratio":q,"mode":mode,"replicate":rep,"pid":os.getpid(),"before":before,"after":fingerprint(),"plain":plain,"audit":audit}
 finally:Path(path).unlink(missing_ok=True)
def cells():
 for m in (16,64):
  for q in (0,4,16):
   for mode in ("control_RML","exact_LMR","exact_LRM","exact_RLM","sample_B8","sample_B32","sample_B128"):
    for rep in range(3):yield m,q,mode,rep
def main():
 if len(sys.argv)>1 and sys.argv[1]=="--worker":print(json.dumps(worker(int(sys.argv[2]),int(sys.argv[3]),sys.argv[4],int(sys.argv[5])),sort_keys=True));return
 assert_measuring_engine()
 if sys.argv[1:]==["--lock"]:LOCK.parent.mkdir(parents=True,exist_ok=True);LOCK.write_text(json.dumps(fingerprint(),indent=2,sort_keys=True)+"\n");print(LOCK);return
 locked=fingerprint()
 if not LOCK.is_file() or json.loads(LOCK.read_text())!=locked:raise SystemExit("missing or stale source/native lock")
 env=dict(os.environ);env["PYTHONPATH"]=os.pathsep.join((str(ROOT),str(ROOT/"runners/dsl/python"),env.get("PYTHONPATH","")));started=datetime.now(timezone.utc).isoformat();runs=[]
 for m,q,mode,rep in cells():
  cp=subprocess.run([sys.executable,str(Path(__file__).resolve()),"--worker",str(m),str(q),mode,str(rep)],cwd=ROOT,env=env,text=True,capture_output=True,check=True);runs.append(json.loads(cp.stdout))
 post=fingerprint();raw={"schema_version":1,"run_id":"substrate-bounded-three-edge-order-v1-20260927","started_utc":started,"locked_inputs":locked,"post_run_inputs":post,"runs":runs};RAW.write_text(json.dumps(raw,indent=2,sort_keys=True)+"\n")
 summary={"schema_version":1,"raw_workers_path":str(RAW.relative_to(ROOT)),"locked_inputs":locked,"post_run_inputs":post,"all_worker_inputs_stable":post==locked and all(x["before"]==locked==x["after"] for x in runs),"worker_count":len(runs)};OUT.write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n");print(json.dumps(summary,indent=2,sort_keys=True))
if __name__=="__main__":main()

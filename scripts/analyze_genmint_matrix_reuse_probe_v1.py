#!/usr/bin/env python3
"""Independent input, route, transfer, and paired cost analysis."""
import hashlib,json,statistics
from collections import defaultdict,Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/"evaluation/reports/substrate_genmint_matrix_reuse_v1_20260926.json"
LOCK=ROOT/"evaluation/substrate_capability/genmint_matrix_reuse_lock_20260926.json"
MAPS={"prior_matrix":[1,1,0,2],"shearA":[1,0,1,1],"shearB":[1,1,0,1]}
POINTS=[(0,0),(1,0),(0,1),(1,1),(2,0),(0,2)]
LAYOUTS={"adjacent_01":[0,1,4],"opposite_03":[0,3,4],"adjacent_12":[1,2,5]}
HELDOUT=[[(2,1),(1,2),(3,1),(1,3)],[(0,3),(2,1),(3,4),(1,0)],[(4,0),(1,2),(3,4),(0,1)],[(1,4),(3,0),(5,2),(0,1)]]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def map_rows(points,labels,m):
 a,b,c,d=m;out=[]
 for i,(r,q) in enumerate(points):
  pred=labels[i];out.append([pred,r,q,"red"]);out.append([pred,a*r+b*q,c*r+d*q,"red"])
 return out
def score_step(x,step,matrix):
 tr=next((t for t in step["transforms"] if t.get("generator")),None)
 if tr is None:return {"route":"no_generator_transform","predictions":None,"correct":None,"selected_generator":None}
 after=step["linear_generators"];gen=next((g for g in after if g["name"]==tr["generator"]),None)
 if gen is None:return {"route":"other_seed_generator","predictions":None,"correct":None,"selected_generator":tr["generator"]}
 initial_names={g["name"] for g in x["initial_linear_generators"]};train_after={g["name"]:g for g in x["train"]["linear_generators"]};before_names={g["name"] for g in step["linear_generators_before"]};after_names={g["name"] for g in after}
 if tr["generator"] in (set(train_after)-initial_names):
  route="reused_expected_matrix" if gen["matrix"]==matrix else "reused_other_training_linear"
 elif tr["generator"] in initial_names:route="preexisting_linear"
 elif tr["generator"] in (after_names-before_names):route="minted_during_application"
 elif tr["generator"] in (before_names-initial_names):route="reused_application_linear"
 elif tr["generator"] in train_after:route="reused_other_training_linear"
 else:route="unclassified_linear_route"
 cur=[list(row) for row in step["base"]];k=max(1,int(tr.get("k",1)))
 # apply_linear_once normalizes the current signature to its own per-slot origin
 for _ in range(k):
  mins=[min(row[j] for row in cur) for j in (1,2)];m=gen["matrix"]
  cur=[[row[0],m[0]*(row[1]-mins[0])+m[1]*(row[2]-mins[1]),m[2]*(row[1]-mins[0])+m[3]*(row[2]-mins[1]),row[3]] for row in cur]
 for trn in tr.get("transforms") or []:
  for row in cur:
   if trn.get("pred") is not None and trn["pred"]!=row[0]:continue
   dim=trn.get("dim")
   if trn.get("kind")=="shift" and dim in (1,2):row[dim]+=trn.get("delta",0)
   elif trn.get("kind")=="subst" and row[3]==trn.get("from"):row[3]=trn.get("to")
 expected=step["target"]
 return {"route":route,"selected_generator":tr["generator"],"matrix":gen["matrix"],"predictions":cur,"correct":[a==b for a,b in zip(cur,expected)]}
def wall(x):return x["train"]["closure_seconds"]+sum(a["closure_seconds"] for a in x["applications"])
def main():
 d=json.loads(RAW.read_text());lock=json.loads(LOCK.read_text())
 checks={"raw_lock_matches_file":d["locked_inputs"]==lock,"lock_sha_matches":d["lock_sha256"]==sha(LOCK),"lock_runner_sha_matches":lock["locked_inputs"]["files_sha256"]["scripts/genmint_matrix_reuse_probe_v1.py"]==sha(ROOT/"scripts/genmint_matrix_reuse_probe_v1.py"),"lock_analyzer_sha_matches":lock["locked_inputs"]["files_sha256"]["scripts/analyze_genmint_matrix_reuse_probe_v1.py"]==sha(Path(__file__)),"native_hash_matches":d["native"]["sha256"]==sha(Path(d["native"]["path"])),"worker_count_360":len(d["workers"])==360,"no_worker_failures":not d["worker_failures"],"unique_worker_pids":len({x.get("pid") for x in d["workers"]})==360}
 cells=defaultdict(list);row_results=[];input_ok=True
 for x in d["workers"]:
  if "worker_failure" in x:continue
  m=MAPS[x["matrix_name"]];p0=set(LAYOUTS[x["layout"]]);base=[];target=[]
  for i,(r,c) in enumerate(POINTS):
   pred="p0" if i in p0 else "p1";a,b,d0,e=m;base.append([pred,r,c,"red"]);target.append([pred,a*r+b*c,d0*r+e*c,"red"])
  input_ok &= x["matrix"]==m and x["p0_indices"]==sorted(p0) and x["training_base"]==base and x["training_target"]==target and len(x["applications"])==x["K"]
  for j,step in enumerate(x["applications"]):
   pts=HELDOUT[j];hb=[["p0" if i%2==0 else "p1",r,c,"red"] for i,(r,c) in enumerate(pts)];ht=[]
   for i,(r,c) in enumerate(pts):
    a,b,d0,e=m;ht.append(["p0" if i%2==0 else "p1",a*r+b*c,d0*r+e*c,"red"])
   input_ok &= step["base"]==hb and step["target"]==ht and step["task_index"]==j
   row_results.append({"matrix_name":x["matrix_name"],"layout":x["layout"],"enabled":x["enabled"],"K":x["K"],"replicate":x["replicate"],**score_step(x,step,m)})
  cells[x["matrix_name"],x["layout"],x["enabled"],x["K"]].append(x)
 checks["independent_input_reconstruction"]=bool(input_ok)
 checks["balanced_72_cells"]=len(cells)==72 and all(len(v)==5 for v in cells.values())
 checks["balanced_replicate_schedules"]=len(d["schedule"])==5 and all(len(s)==72 for s in d["schedule"])
 checks["no_unclassified_routes"]=all(x["route"]!="unclassified_linear_route" for x in row_results)
 checks["replicate_outcome_determinism"]=all(len({json.dumps((x["train"]["status"],x["train"]["linear_generators"],x["train"]["quanta_delta"],[(a["status"],a["transforms"],a["quanta_delta"]) for a in x["applications"]],[(q["route"],q["correct"]) for q in row_results if (q["matrix_name"],q["layout"],q["enabled"],q["K"],q["replicate"])==(x["matrix_name"],x["layout"],x["enabled"],x["K"],x["replicate"]) ]),sort_keys=True) for x in vals})==1 for vals in cells.values())
 # Pilot replication and disabled acquisition control, repeated for all K prefixes.
 pilot_expected={("prior_matrix",l):True for l in LAYOUTS};pilot_expected.update({("shearA",l):True for l in LAYOUTS});pilot_expected.update({("shearB","opposite_03"):True,("shearB","adjacent_12"):True,("shearB","adjacent_01"):False})
 pilot=[]
 for (mn,ln,en,k),xs in cells.items():
  expected=pilot_expected[(mn,ln)]
  for x in xs:
   got=any(g["matrix"]==MAPS[mn] for g in x["train"]["linear_generators"])
   if en:pilot.append(got==expected)
   else:pilot.append(not got)
 checks["pilot_training_outcome_replicated_in_all_arms"]=len(pilot)==360 and all(pilot)
 summaries=[]
 for (mn,ln,en,k),xs in sorted(cells.items()):
  expected=MAPS[mn]; acquired=[any(g["matrix"]==expected for g in x["train"]["linear_generators"]) for x in xs]
  app_rows=[z for z in row_results if (z["matrix_name"],z["layout"],z["enabled"],z["K"])==(mn,ln,en,k)]
  reuse=[z for z in app_rows if z["route"]=="reused_expected_matrix"]
  summaries.append({"matrix_name":mn,"matrix":expected,"layout":ln,"enabled":en,"K":k,"n":len(xs),"expected_matrix_acquired":sum(acquired),"training_statuses":dict(Counter(x["train"]["status"] for x in xs)),"training_quanta":sorted({x["train"]["quanta_delta"] for x in xs}),"application_routes":dict(Counter(z["route"] for z in app_rows)),"expected_matrix_reuse_calls":len(reuse),"reuse_rows_correct":sum(sum(z["correct"]) for z in reuse),"reuse_rows_scored":4*len(reuse),"exact_reuse_calls":sum(all(z["correct"]) for z in reuse),"total_closure_seconds_median":statistics.median(wall(x) for x in xs),"total_closure_seconds_range":[min(wall(x) for x in xs),max(wall(x) for x in xs)],"peak_rss_kib_median":statistics.median(x["peak_rss_kib"] for x in xs),"quanta_total_median":statistics.median(x["total_quanta_delta"] for x in xs),"graph_nodes_median":statistics.median(x["final_graph_nodes"] for x in xs)})
 # Pair enabled/disabled rows at matched matrix/layout/K/replicate.
 idx={(x["matrix_name"],x["layout"],x["K"],x["replicate"],x["enabled"]):x for x in d["workers"] if "worker_failure" not in x};paired=[]
 for mn in MAPS:
  for ln in LAYOUTS:
   for k in (0,1,2,4):
    for rep in range(1,6):
     on=idx[mn,ln,k,rep,True];off=idx[mn,ln,k,rep,False]
     enabled_acquired=any(g["matrix"]==MAPS[mn] for g in on["train"]["linear_generators"])
     paired.append({"matrix_name":mn,"layout":ln,"K":k,"replicate":rep,"enabled_acquired_expected_matrix":enabled_acquired,"enabled_total_closure_seconds":wall(on),"disabled_total_closure_seconds":wall(off),"enabled_minus_disabled_seconds":wall(on)-wall(off),"enabled_quanta":on["total_quanta_delta"],"disabled_quanta":off["total_quanta_delta"],"enabled_peak_rss_kib":on["peak_rss_kib"],"disabled_peak_rss_kib":off["peak_rss_kib"],"enabled_exact_reuses":sum(z["route"]=="reused_expected_matrix" and all(z["correct"]) for z in row_results if (z["matrix_name"],z["layout"],z["enabled"],z["K"],z["replicate"])==(mn,ln,True,k,rep))})
 economics=[]
 for mn in MAPS:
  for ln in LAYOUTS:
   for k in (0,1,2,4):
    ps=[p for p in paired if p["matrix_name"]==mn and p["layout"]==ln and p["K"]==k]
    crossed=[p for p in ps if p["enabled_total_closure_seconds"]<p["disabled_total_closure_seconds"]]
    acq=[p for p in ps if p["enabled_acquired_expected_matrix"]]
    economics.append({"matrix_name":mn,"layout":ln,"K":k,"n_pairs":len(ps),"median_enabled_seconds":statistics.median(p["enabled_total_closure_seconds"] for p in ps),"median_disabled_seconds":statistics.median(p["disabled_total_closure_seconds"] for p in ps),"median_enabled_minus_disabled_seconds":statistics.median(p["enabled_minus_disabled_seconds"] for p in ps),"enabled_faster_pairs":len(crossed),"acquired_expected_pairs":len(acq),"enabled_faster_given_acquisition":sum(p["enabled_total_closure_seconds"]<p["disabled_total_closure_seconds"] for p in acq),"median_enabled_rss_kib":statistics.median(p["enabled_peak_rss_kib"] for p in ps),"median_disabled_rss_kib":statistics.median(p["disabled_peak_rss_kib"] for p in ps),"median_enabled_quanta":statistics.median(p["enabled_quanta"] for p in ps),"median_disabled_quanta":statistics.median(p["disabled_quanta"] for p in ps)})
 crossovers=[]
 for mn in MAPS:
  for ln in LAYOUTS:
   es=[e for e in economics if e["matrix_name"]==mn and e["layout"]==ln]
   hit=next((e["K"] for e in es if e["median_enabled_minus_disabled_seconds"]<0 and e["acquired_expected_pairs"]>0),None)
   crossovers.append({"matrix_name":mn,"layout":ln,"first_median_runtime_crossover_K":hit,"status":"observed" if hit is not None else "none_through_K4"})
 out={"raw_sha256":sha(RAW),"checks":checks,"all_checks_pass":all(checks.values()),"summaries":summaries,"paired_economics":paired,"economic_summaries":economics,"break_even":crossovers,"scored_application_rows":row_results,"analyzer_sha256":sha(Path(__file__))}
 path=ROOT/"evaluation/reports/substrate_genmint_matrix_reuse_v1_analysis_20260926.json";path.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n");print(json.dumps({"analysis":str(path),"all_checks_pass":out["all_checks_pass"],"failed_checks":[k for k,v in checks.items() if not v],"workers":len(d["workers"]),"break_even":crossovers},indent=2))
if __name__=="__main__":main()

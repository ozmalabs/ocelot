#!/usr/bin/env python3
"""Independent orbit/task oracle and scoring for held-out polyomino transfer."""
import hashlib,importlib.util,json,math,statistics
from collections import Counter,deque
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
CAP=ROOT/"evaluation/reports/heldout_polyomino_transform_transfer_v1/capture.json"
LOCK=ROOT/"evaluation/substrate_capability/heldout_polyomino_transform_transfer_v1_lock_20260929.json"
RUN=ROOT/"evaluation/substrate_capability/heldout_polyomino_transform_transfer_v1.py"
OUT=ROOT/"evaluation/reports/heldout_polyomino_transform_transfer_v1_independent_analysis.json"
SIGMAS=(8,12);REPS=4

def norm(points):
 if not points:return tuple()
 mr=min(int(x[0]) for x in points);mc=min(int(x[1]) for x in points)
 return tuple(sorted((int(r)-mr,int(c)-mc) for r,c in points))

def d4_forms(points):
 forms=[]
 for t in range(8):
  xy=[]
  for r,c in points:
   xy.append(((r,c),(r,-c),(-r,c),(-r,-c),(c,r),(c,-r),(-c,r),(-c,-r))[t])
  forms.append(norm(xy))
 return forms

def canonical(points):return min(d4_forms(points))

def connected(points):
 pts=set(map(tuple,points))
 if not pts:return False
 seen={next(iter(pts))};q=deque(seen)
 while q:
  r,c=q.popleft()
  for n in ((r+1,c),(r-1,c),(r,c+1),(r,c-1)):
   if n in pts and n not in seen:seen.add(n);q.append(n)
 return seen==pts

def transform(points,op,color=9):
 fam=op["family"];p=op["param"];out=[]
 for r,c,v in points:
  if fam=="rotate":
   for _ in range(int(p)):r,c=c,-r
  elif fam=="reflect":
   if p=="c":c=-c
   else:r=-r
  elif fam=="recolour":v=8 if int(v)==color else int(v)
  out.append((r,c,v))
 mr=min(r for r,c,v in out);mc=min(c for r,c,v in out)
 return sorted((r-mr,c-mc,v) for r,c,v in out)

def signature(cells):return [["cell",int(r),int(c),f"v{int(v)}"] for r,c,v in cells]

def wilson(k,n):
 z=1.959963984540054;p=k/n;d=1+z*z/n;c=(p+z*z/(2*n))/d
 h=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d
 return [c-h,c+h]

def classify(rows,expected):
 keys=[r["recognized_key"] for r in rows]
 exact=sum(k==expected for k in keys) if expected is not None else sum(k is None for k in keys)
 refusal=sum(k is None for k in keys);wrong=sum(k is not None and k!=expected for k in keys) if expected is not None else len(keys)-refusal
 n=len(rows)
 return {"n":n,"exact_or_expected_refusal":exact,"recognition_refusal":refusal,
  "wrong_key_or_false_accept":wrong,"recognized_key_counts":dict(Counter("<refusal>" if x is None else str(x) for x in keys)),
  "wilson_95_exact_or_refusal":wilson(exact,n),"median_wall_seconds":statistics.median(x["wall_seconds"] for x in rows),
  "median_cpu_seconds":statistics.median(x["cpu_seconds"] for x in rows)}

def main():
 cap=json.loads(CAP.read_text());lock=json.loads(LOCK.read_text())
 spec=importlib.util.spec_from_file_location("heldout_transfer_runner",RUN)
 runner=importlib.util.module_from_spec(spec);assert spec and spec.loader;spec.loader.exec_module(runner)
 live=runner.input_lock();stable=live==lock==cap.get("locked_inputs")==cap.get("post_run_inputs")
 wspec=importlib.util.spec_from_file_location("locked_ls20_corpus",ROOT/"worlds/arc_ls20_scenario.py")
 world=importlib.util.module_from_spec(wspec);assert wspec and wspec.loader;wspec.loader.exec_module(world)
 training=[canonical([(r,c) for r,c in coords]) for coords,color in world.CORPUS.values()]
 shape_meta={};errors=[];groups={};clean_pos=[];noisy_pos={s:[] for s in SIGMAS};clean_neg=[];noisy_neg={s:[] for s in SIGMAS}
 group_ids=set();observation_count=0;group_order={x["group_id"]:i for i,x in enumerate(runner.GROUPS)}
 for g in cap.get("groups",[]):
  sid=g["shape_id"];coords=runner.SHAPES.get(sid);group_ids.add(g["group_id"])
  if coords is None:errors.append(g["group_id"]+":unknown_shape");continue
  pts=list(coords);forms=d4_forms(pts);shape_meta[sid]={"size":len(pts),"connected":connected(pts),"d4_orbit_size":len(set(forms)),"training_orbit_disjoint":canonical(pts) not in training}
  if not connected(pts) or len(set(pts))!=len(pts) or len(set(forms))!=8 or canonical(pts) in training:errors.append(sid+":shape_property")
  base=sorted((int(r),int(c),int(v)) for r,c,v in g["base_cells"])
  if sorted(base)!=sorted((r,c,9) for r,c in pts):errors.append(g["group_id"]+":base")
  if g["case_type"]=="positive":
   op=g["operator"];expected=op["key"];goal=transform(base,op)
   if sorted(goal)!=sorted(tuple(x) for x in g["goal_cells"]):errors.append(g["group_id"]+":positive_goal")
   if op["family"] in ("rotate","reflect") and norm([(r,c) for r,c,v in goal])==norm(pts):errors.append(g["group_id"]+":unexpected_alias")
   clean_pos.append(g["clean"])
   for s in SIGMAS:noisy_pos[s].extend(g["noisy"].get(str(s),[]))
  else:
   expected=None;goal=[tuple(x) for x in g["goal_cells"]]
   if len(goal)!=len(base)+1 or not connected([(r,c) for r,c,v in goal]):errors.append(g["group_id"]+":negative_count_or_connectivity")
   base_rc={(r,c) for r,c,v in base};added=[x for x in goal if (x[0],x[1]) not in base_rc]
   if len(added)!=1 or not any((added[0][0]+dr,added[0][1]+dc) in base_rc for dr,dc in ((1,0),(-1,0),(0,1),(0,-1))):errors.append(g["group_id"]+":negative_extra_cell")
   clean_neg.append(g["clean"])
   for s in SIGMAS:noisy_neg[s].extend(g["noisy"].get(str(s),[]))
  calls=[g["clean"]]+[x for s in SIGMAS for x in g["noisy"].get(str(s),[])]
  observation_count+=len(calls)
  if set(g.get("noisy",{}))!={str(s) for s in SIGMAS}:errors.append(g["group_id"]+":sigma_keys")
  for si,s in enumerate(SIGMAS):
   rep_rows=g.get("noisy",{}).get(str(s),[])
   if len(rep_rows)!=REPS:errors.append(g["group_id"]+f":sigma{s}_rep_count")
   expected_seeds=[97500000+list(runner.SHAPES).index(sid)*100000+group_order[g["group_id"]]*1000+(si+1)*10+rep for rep in range(1,REPS+1)]
   if [x.get("noise_seed") for x in rep_rows]!=expected_seeds:errors.append(g["group_id"]+f":sigma{s}_seeds")
   if any(x.get("noise_sigma")!=s for x in rep_rows):errors.append(g["group_id"]+f":sigma{s}_metadata")
  if len(g["clean"].get("seen_cells",[]))!=2:errors.append(g["group_id"]+":clean_observation_count")
  for result in calls:
   if len(result.get("seen_cells",[]))!=2 or result.get("seen_signatures")!=[signature(x) for x in result.get("seen_cells",[])]:errors.append(g["group_id"]+":seen_signature")
  if g["clean"].get("noise_sigma")!=0:errors.append(g["group_id"]+":clean_sigma")
  if g["clean"].get("noise_seed")!=0:errors.append(g["group_id"]+":clean_seed")
  from worlds.arc_ls20_scenario import render_and_see
  expected_clean_seen=[[[*x] for x in render_and_see(base)],[[*x] for x in render_and_see(goal)]]
  if g["clean"].get("seen_cells")!=expected_clean_seen:errors.append(g["group_id"]+":clean_pixel_recovery")
  if g["case_type"]=="positive" and g["expected_key"]!=expected:errors.append(g["group_id"]+":expected_key")
  if g["case_type"]=="negative" and g["expected_key"] is not None:errors.append(g["group_id"]+":negative_expected_key")
  groups[g["group_id"]]={"shape_id":sid,"case_type":g["case_type"],"expected_key":g["expected_key"],"clean":g["clean"],"noisy":g["noisy"]}
 positive=[g for g in cap.get("groups",[]) if g.get("case_type")=="positive"]
 negative=[g for g in cap.get("groups",[]) if g.get("case_type")=="negative"]
 expected_ids={f"{sid}_{op['id']}" for sid in runner.SHAPES for op in runner.OPERATORS}|{f"{sid}_extra_cell_negative" for sid in runner.SHAPES}
 if group_ids!=expected_ids:errors.append("group_id_set")
 for g in positive:
  if g["clean"]["recognized_key"]!=g["expected_key"]:pass
 by_operator={};op_order=[x["key"] for x in runner.OPERATORS]
 for opkey in op_order:
  subset=[g for g in positive if g["expected_key"]==opkey]
  by_operator[opkey]={"clean":classify([g["clean"] for g in subset],opkey),
    "noise":{"8":classify([x for g in subset for x in g["noisy"]["8"]],opkey),
             "12":classify([x for g in subset for x in g["noisy"]["12"]],opkey)}}
 positive_metrics={"clean":classify([g["clean"] for g in positive],"<any-exact-key>"),
   "noise":{"8":classify([x for g in positive for x in g["noisy"]["8"]],"<any-exact-key>"),
            "12":classify([x for g in positive for x in g["noisy"]["12"]],"<any-exact-key>")}}
 # Correct exact-key scoring needs each trial's own target key, unlike a shared label.
 def positive_scoring(rows):
  good=sum(r["recognized_key"]==r["expected"] for r in rows);ref=sum(r["recognized_key"] is None for r in rows)
  wrong=len(rows)-good-ref;return {"n":len(rows),"exact":good,"refusal":ref,"wrong_key":wrong,"exact_accuracy":good/len(rows),"wilson_95":wilson(good,len(rows))}
 pos_clean=[{"recognized_key":g["clean"]["recognized_key"],"expected":g["expected_key"]} for g in positive]
 pos_noise={str(s):[{"recognized_key":x["recognized_key"],"expected":g["expected_key"]} for g in positive for x in g["noisy"][str(s)]] for s in SIGMAS}
 neg_clean=classify([g["clean"] for g in negative],None)
 neg_noise={str(s):classify([x for g in negative for x in g["noisy"][str(s)]],None) for s in SIGMAS}
 # By-shape exact rates retain shape clustering instead of counting noise draws as new shapes.
 by_shape={}
 for sid in runner.SHAPES:
  sg=[g for g in positive if g["shape_id"]==sid]
  by_shape[sid]={"clean_exact":sum(g["clean"]["recognized_key"]==g["expected_key"] for g in sg),"positive_cases":len(sg),
    "noise":{"8":{"exact":sum(x["recognized_key"]==g["expected_key"] for g in sg for x in g["noisy"]["8"]),"n":sum(len(g["noisy"]["8"]) for g in sg)},
             "12":{"exact":sum(x["recognized_key"]==g["expected_key"] for g in sg for x in g["noisy"]["12"]),"n":sum(len(g["noisy"]["12"]) for g in sg)}}}
 gates={"capture_complete":cap.get("capture_status")=="complete","source_build_lock_stable":stable,
  "native_extension_fresh":not lock.get("native_build_stale_reasons"),"exactly_12_valid_heldout_shapes":len(shape_meta)==12 and not errors,
  "exactly_84_complete_groups":len(cap.get("groups",[]))==84 and group_ids==expected_ids,
  "all_72_positive_oracles_and_12_negative_shapes_valid":len(positive)==72 and len(negative)==12,
  "all_756_observations_present":observation_count==756,
  "all_positive_and_negative_seen_signatures_reconcile":not errors}
 report={"run_id":cap.get("run_id"),"n_groups":len(cap.get("groups",[])),"n_observations":observation_count,
  "shape_properties":shape_meta,"positive_overall":positive_scoring(pos_clean),
  "positive_noise":{s:positive_scoring(rs) for s,rs in pos_noise.items()},
  "positive_by_operator":by_operator,"negative_clean":neg_clean,"negative_noise":neg_noise,
  "positive_by_shape":by_shape,"integrity_gates":gates,"all_integrity_gates_pass":all(gates.values()),
  "input_oracle_errors":errors,"process":cap.get("process"),"claim_boundary":cap.get("claim_boundary")}
 OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
 print(json.dumps({"output":str(OUT.relative_to(ROOT)),"gates":gates,"positive":report["positive_overall"],
  "positive_noise":report["positive_noise"],"negative_noise":{s:{"false_accepts":x["wrong_key_or_false_accept"],"n":x["n"]} for s,x in neg_noise.items()},
  "operator_noise":{k:{s:{"exact":v["noise"][s]["exact_or_expected_refusal"],"n":v["noise"][s]["n"],"wrong":v["noise"][s]["wrong_key_or_false_accept"]} for s in ("8","12")} for k,v in by_operator.items()}},indent=2))

if __name__=="__main__":main()

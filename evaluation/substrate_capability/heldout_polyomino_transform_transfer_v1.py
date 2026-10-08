#!/usr/bin/env python3
"""Source-locked transfer evaluation on held-out polyomino base shapes."""
from __future__ import annotations
import hashlib,importlib.util,json,subprocess,sys,time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/"runners/dsl/python")]
RUNNER=Path(__file__).resolve()
PROTOCOL=ROOT/"docs/research/engine_substrate/SUBSTRATE_HELDOUT_POLYOMINO_TRANSFORM_TRANSFER_V1_PREREG_20260929.md"
LOCK=ROOT/"evaluation/substrate_capability/heldout_polyomino_transform_transfer_v1_lock_20260929.json"
ANALYZER=ROOT/"evaluation/substrate_capability/analyze_heldout_polyomino_transform_transfer_v1.py"
OUT=ROOT/"evaluation/reports/heldout_polyomino_transform_transfer_v1"
PARTIAL=OUT/"partial.json";CAPTURE=OUT/"capture.json"
HELPER_PATH=ROOT/"evaluation/substrate_capability/ls20_mapnav_current_source_scale_v1_2.py"
HS=importlib.util.spec_from_file_location("heldout_poly_lock_helper",HELPER_PATH)
HELPER=importlib.util.module_from_spec(HS);assert HS and HS.loader;HS.loader.exec_module(HELPER)
WORLD_PATH=ROOT/"worlds/arc_ls20_scenario.py"
WS=importlib.util.spec_from_file_location("heldout_poly_world",WORLD_PATH)
WORLD=importlib.util.module_from_spec(WS);assert WS and WS.loader;WS.loader.exec_module(WORLD)

# Canonical fixed orientations from 12 connected free-polyomino orbits not in
# the six-symbol task corpus. Every shape has trivial D4 stabilizer.
SHAPES={
 "H05_A":((0,0),(0,1),(0,2),(0,3),(1,0)),
 "H06_A":((0,0),(0,1),(0,2),(1,2),(2,2),(2,3)),
 "H06_B":((0,0),(0,1),(0,2),(1,1),(2,0),(2,1)),
 "H06_C":((0,0),(0,1),(1,1),(2,1),(2,2),(3,1)),
 "H06_D":((0,0),(0,1),(1,1),(1,2),(2,1),(3,1)),
 "H06_E":((0,0),(0,1),(1,1),(1,2),(1,3),(2,3)),
 "H07_A":((0,0),(0,1),(0,2),(0,3),(0,4),(1,4),(1,5)),
 "H07_B":((0,0),(0,1),(1,1),(1,2),(2,2),(3,2),(3,3)),
 "H07_C":((0,1),(1,0),(1,1),(1,2),(1,3),(2,2),(3,2)),
 "H07_D":((0,0),(0,1),(1,1),(2,1),(3,1),(3,2),(4,1)),
 "H07_E":((0,0),(0,1),(1,1),(1,2),(1,3),(2,1),(2,2)),
 "H07_F":((0,0),(0,1),(0,2),(1,2),(1,3),(2,3),(2,4)),
}
OPERATORS=(
 {"id":"rotate_1","family":"rotate","param":1,"key":"rot90:1"},
 {"id":"rotate_2","family":"rotate","param":2,"key":"rot90:2"},
 {"id":"rotate_3","family":"rotate","param":3,"key":"rot90:3"},
 {"id":"reflect_c","family":"reflect","param":"c","key":"refl:c"},
 {"id":"reflect_r","family":"reflect","param":"r","key":"refl:r"},
 {"id":"recolour_9_8","family":"recolour","param":{"9":8},"key":"recolour:v9>v8"},
)
SIGMAS=(8,12);NOISE_REPS=4;COLOR=9;CANVAS=20

def file_record(path):
 raw=path.read_bytes();return {"path":path.relative_to(ROOT).as_posix(),"bytes":len(raw),"sha256":hashlib.sha256(raw).hexdigest()}

def cell_specs():
 out=[]
 for sid,coords in SHAPES.items():
  for op in OPERATORS:out.append({"group_id":f"{sid}_{op['id']}","shape_id":sid,"size":len(coords),"case_type":"positive","operator":op})
  out.append({"group_id":f"{sid}_extra_cell_negative","shape_id":sid,"size":len(coords),"case_type":"negative","operator":None})
 return out

GROUPS=cell_specs()
def input_lock():
 lock=HELPER.input_lock()
 lock["protocol"]=file_record(PROTOCOL);lock["runner"]=file_record(RUNNER)
 lock["independent_analyzer"]=file_record(ANALYZER);lock["lock_helper"]=file_record(HELPER_PATH)
 lock["world_module"]=file_record(WORLD_PATH)
 lock["parameters"]={"shapes":{k:[list(p) for p in v] for k,v in SHAPES.items()},
   "operators":list(OPERATORS),"sigma_levels":list(SIGMAS),"noise_replicates":NOISE_REPS,
   "negative_controls":"one adjacent same-colour cell added per shape","canvas":CANVAS,
   "color":COLOR,"groups":len(GROUPS),"expected_observations":756}
 lock["git_head"]=subprocess.run(["git","rev-parse","HEAD"],cwd=ROOT,text=True,capture_output=True,check=True).stdout.strip()
 return lock

def atomic(path,value):
 tmp=path.with_suffix(path.suffix+".tmp");tmp.write_text(json.dumps(value,sort_keys=True,indent=2)+"\n");tmp.replace(path)

def noisy_observer(cells,sigma,seed,seen_log):
 import numpy as np
 from worlds.arc import _render_screen,recover_grid_from_render
 rng=np.random.Generator(np.random.PCG64(seed))
 grid=[[0]*CANVAS for _ in range(CANVAS)]
 for r,c,v in WORLD._reposition(cells):
  if 0<=r<CANVAS and 0<=c<CANVAS:grid[r][c]=int(v)
 image=_render_screen(grid,CANVAS,CANVAS).astype(np.float64)
 if sigma:image+=rng.normal(0.0,float(sigma),size=image.shape)
 seen=np.asarray(recover_grid_from_render(np.clip(image,0,255).astype(np.uint8)),dtype="int32")
 result=[(r,c,int(seen[r,c])) for r in range(seen.shape[0]) for c in range(seen.shape[1]) if int(seen[r,c])!=0]
 seen_log.append(result);return result

def recognition(base,goal,sigma,seed):
 seen=[];start=time.perf_counter();cpu=time.process_time()
 def see(cells,canvas=CANVAS):return noisy_observer(cells,sigma,seed,seen)
 key=WORLD.recognise_required_key(base,goal,_see=see)
 from worlds.arc import cells_to_signature
 return {"recognized_key":key,"seen_cells":seen,
  "seen_signatures":[cells_to_signature(x) for x in seen],
  "wall_seconds":time.perf_counter()-start,"cpu_seconds":time.process_time()-cpu,
  "noise_sigma":sigma,"noise_seed":seed}

def cells_for(coords,color=COLOR):return [(int(r),int(c),int(color)) for r,c in coords]

def make_group(spec,shape_index):
 coords=SHAPES[spec["shape_id"]];base=cells_for(coords)
 if spec["case_type"]=="positive":
  op=spec["operator"];param={int(k):int(v) for k,v in op["param"].items()} if isinstance(op["param"],dict) else op["param"]
  goal=WORLD.apply_transform(base,op["family"],param);expected=op["key"]
 else:
  maxr=max(r for r,c in coords);candidates=sorted(c for r,c in coords if r==maxr)
  extra=(maxr+1,candidates[0],COLOR);goal=base+[extra];expected=None;op=None
 clean=recognition(base,goal,0,0)
 noise={}
 sigma_order=SIGMAS if (shape_index+len(spec["group_id"]))%2==0 else tuple(reversed(SIGMAS))
 case_index=next(i for i,x in enumerate(GROUPS) if x["group_id"]==spec["group_id"])
 for sigma in sigma_order:
  rows=[]
  for rep in range(1,NOISE_REPS+1):
   seed=97500000+shape_index*100000+case_index*1000+(SIGMAS.index(sigma)+1)*10+rep
   rows.append(recognition(base,goal,sigma,seed))
  noise[str(sigma)]=rows
 return {**spec,"base_cells":base,"goal_cells":goal,"expected_key":expected,
         "clean":clean,"noisy":noise}

def main():
 import resource
 OUT.mkdir(parents=True,exist_ok=True)
 if sys.argv[1:]==["--lock"]:
  if LOCK.exists() or PARTIAL.exists() or CAPTURE.exists():raise SystemExit("refusing to overwrite lock or capture")
  lock=input_lock()
  if lock["native_build_stale_reasons"]:raise SystemExit(f"stale native extension: {lock['native_build_stale_reasons']}")
  atomic(LOCK,lock);print(LOCK.relative_to(ROOT));return
 lock=json.loads(LOCK.read_text())
 if input_lock()!=lock:raise SystemExit("source/input lock drift; preserve partial as censored")
 state=json.loads(PARTIAL.read_text()) if PARTIAL.exists() else {"next_group":0,"groups":[]}
 started,cpu=time.perf_counter(),time.process_time()
 for gi in range(state["next_group"],len(GROUPS)):
  spec=GROUPS[gi];sidx=list(SHAPES).index(spec["shape_id"])
  state["groups"].append(make_group(spec,sidx));state["next_group"]=gi+1;atomic(PARTIAL,state)
  if state["next_group"]%3==0:print(f"groups: {state['next_group']}/{len(GROUPS)}",flush=True)
 after=input_lock()
 if after!=lock:raise SystemExit("post-run source/input lock drift")
 capture={"schema_version":1,"run_id":"heldout-polyomino-transform-transfer-v1-20260929",
  "capture_status":"complete","captured_utc":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),
  "locked_inputs":lock,"post_run_inputs":after,"groups":state["groups"],
  "process":{"wall_seconds":time.perf_counter()-started,"cpu_seconds":time.process_time()-cpu,
             "max_rss_kib":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss},
  "claim_boundary":"Zero-shot known-transform recognition on 12 new monochrome polyomino orbits; no concept acquisition, broad negative distribution, or natural prevalence claim."}
 atomic(CAPTURE,capture);PARTIAL.unlink(missing_ok=True)
 print(json.dumps({"capture":str(CAPTURE.relative_to(ROOT)),"status":"complete","groups":len(state["groups"]),"observations":sum(1+sum(len(x) for x in g['noisy'].values()) for g in state['groups'])},indent=2))

if __name__=="__main__":main()

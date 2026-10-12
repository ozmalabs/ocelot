#!/usr/bin/env python3
"""Locked full-seed GenMint extended-horizon staged-cost sweep."""
from __future__ import annotations
import hashlib,json,os,platform,random,resource,subprocess,sys,time
from pathlib import Path
from domains.engine_provenance import engine_preamble,provenance_line,rust_source_fingerprint
engine_preamble()
from substrate.boot_core import boot_core
from domains import reflective_faculty as rf
from substrate_rs import _native

ROOT=Path(__file__).resolve().parents[1]
LOCK=ROOT/"evaluation/substrate_capability/genmint_matrix_family_reuse_v3_lock_20260926.json"
PREREG=ROOT/"docs/research/engine_substrate/SUBSTRATE_GENMINT_MATRIX_FAMILY_REUSE_V3_PREREG_20260926.md"
OUT=ROOT/"evaluation/reports/substrate_genmint_matrix_family_reuse_v3_20260926.json"
MAPS={"prior_matrix":[1,1,0,2],"shearA":[1,0,1,1],"shearB":[1,1,0,1],"shearC":[1,2,0,1],"axis_swap":[0,1,1,0],"quarter_turn":[0,1,-1,0]}
POINTS=[(0,0),(1,0),(0,1),(1,1),(2,0),(0,2)]
LAYOUTS={"adjacent_01":[0,1,4],"opposite_03":[0,3,4],"adjacent_12":[1,2,5]}
def make_heldout():
 rng=random.Random(20260930); tasks=[]; seen=set()
 while len(tasks)<16:
  pts=tuple((rng.randrange(0,8),rng.randrange(0,8)) for _ in range(4))
  if len(set(pts))<4 or pts in seen:continue
  # Require both coordinate ranges and a non-collinear base to avoid degenerate fixtures.
  if len({p[0] for p in pts})<3 or len({p[1] for p in pts})<3:continue
  area=(pts[1][0]-pts[0][0])*(pts[2][1]-pts[0][1])-(pts[2][0]-pts[0][0])*(pts[1][1]-pts[0][1])
  if area==0:continue
  seen.add(pts);tasks.append(list(pts))
 return tasks
HELDOUT=make_heldout()
KS=(0,4,16);ARMS=(False,True);REPS=3;SEED=20260926
DT=["pred","coord:r","coord:c","val"]
FILES=["scripts/genmint_matrix_family_reuse_probe_v3.py","scripts/analyze_genmint_matrix_family_reuse_probe_v3.py","docs/research/engine_substrate/SUBSTRATE_GENMINT_MATRIX_FAMILY_REUSE_V3_PREREG_20260926.md","seeds/shape_decode_loop.json","domains/reflective_faculty.py","domains/engine_provenance.py","substrate/boot_core.py","runners/dsl/src/shape_decode.rs","runners/dsl/src/term.rs","runners/dsl/python/substrate_rs/_native.build.json"]

def sha(path:Path)->str:return hashlib.sha256(path.read_bytes()).hexdigest()
def locked_inputs()->dict:
 native=Path(_native.__file__).resolve()
 return {"files_sha256":{f:sha(ROOT/f) for f in FILES},"native_path":str(native),"native_sha256":sha(native),"rust_source_fingerprint":rust_source_fingerprint(str(ROOT))}
def make_row(pred,r,c,m):
 a,b,d,e=m
 return [pred,r,c,"red"],[pred,a*r+b*c,d*r+e*c,"red"]
def linear_gens(s):
 out=[]
 for node in s.nodes("DimensionGenerator"):
  at=s.node(node)["attrs"]
  if at.get("kind")=="linear":out.append({"id":str(node),"name":at.get("name"),"matrix":list(at.get("matrix") or []),"coord_dims":list(at.get("coord_dims") or [])})
 return out
def transform_records(s,obs):
 rows=[]
 for node in s.neighbours(obs,"has_transform"):
  at=s.node(node)["attrs"]
  rows.append({k:at.get(k) for k in ("source","generator","dim","k","ks","transforms","dims","deltas","delta","base","generators") if k in at})
 return rows
def add_observation(s,agent,native,signature,key):
 epoch=s.node(agent)["attrs"].get("codebook_epoch") or 0.0
 obs=s.add_node("Observation",{"signature":signature,"key":["matrix_reuse",*key],"status":"decoded","residual":signature,"decoded_epoch":epoch,"dim_types":DT})
 s.add_edge(agent,"observed",obs)
 axis_before=len(list(s.nodes("CapabilityAxis")));nodes_before=len(list(s.nodes()));t0=time.perf_counter();native.run_rules();elapsed=time.perf_counter()-t0
 at=s.node(obs)["attrs"]
 return {"status":at.get("status"),"residual":at.get("residual"),"covered_by":at.get("covered_by"),"decoded_epoch":at.get("decoded_epoch"),"transforms":transform_records(s,obs),"closure_seconds":elapsed,"quanta_delta":len(list(s.nodes("CapabilityAxis")))-axis_before,"graph_nodes_before":nodes_before,"graph_nodes_after":len(list(s.nodes())),"linear_generators":linear_gens(s)}
def worker(matrix_name,layout_name,enabled,k,rep):
 t_all=time.perf_counter();m=MAPS[matrix_name];p0=set(LAYOUTS[layout_name]);base=[];target=[]
 for i,(r,c) in enumerate(POINTS):
  b,y=make_row("p0" if i in p0 else "p1",r,c,m);base.append(b);target.append(y)
 s,agent=boot_core();native=rf._native_eval2(s);rf._ensure_shape_decode_loop(s,native,agent)
 if enabled:s.set_attr(agent,"gen_infer_enabled",1.0)
 initial=linear_gens(s)
 s.add_node("ShapeSignature",{"name":f"training_{matrix_name}_{layout_name}","signature":json.dumps(base),"kind":"faculty","faculty":f"training_{matrix_name}_{layout_name}","dim_types":DT})
 train=add_observation(s,agent,native,target,[matrix_name,layout_name,str(enabled),str(rep),"train"])
 train["linear_generators_before"]=initial
 apps=[]
 for task_index,coords in enumerate(HELDOUT[:k]):
  base_h=[];target_h=[]
  for j,(r,c) in enumerate(coords):
   b,y=make_row("p0" if j%2==0 else "p1",r,c,m);base_h.append(b);target_h.append(y)
  name=f"held_{task_index}_{matrix_name}_{layout_name}"
  s.add_node("ShapeSignature",{"name":name,"signature":json.dumps(base_h),"kind":"faculty","faculty":name,"dim_types":DT})
  before=linear_gens(s)
  step=add_observation(s,agent,native,target_h,[matrix_name,layout_name,str(enabled),str(rep),str(task_index)])
  step.update({"task_index":task_index,"base":base_h,"target":target_h,"linear_generators_before":before})
  apps.append(step)
 return {"matrix_name":matrix_name,"matrix":m,"layout":layout_name,"p0_indices":sorted(p0),"enabled":enabled,"K":k,"replicate":rep,"pid":os.getpid(),"training_base":base,"training_target":target,"initial_linear_generators":initial,"train":train,"applications":apps,"final_linear_generators":linear_gens(s),"total_quanta_delta":train["quanta_delta"]+sum(x["quanta_delta"] for x in apps),"final_graph_nodes":len(list(s.nodes())),"sequence_wall_seconds":time.perf_counter()-t_all,"peak_rss_kib":int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)}
def main():
 if len(sys.argv)>1 and sys.argv[1]=="--worker":
  _,_,mn,ln,en,k,rep=sys.argv
  print(json.dumps(worker(mn,ln,en=="1",int(k),int(rep)),sort_keys=True,default=str));return
 lock_data={"schema_version":1,"locked_inputs":locked_inputs(),"design":{"matrices":MAPS,"layouts":LAYOUTS,"reuse_counts":list(KS),"arms":list(ARMS),"repetitions":REPS,"schedule_seed":SEED}}
 if len(sys.argv)>1 and sys.argv[1]=="--lock":
  print(json.dumps(lock_data,indent=2,sort_keys=True));return
 if not LOCK.exists() or json.loads(LOCK.read_text())!=lock_data:raise SystemExit("missing or changed lock; run --lock and save the exact JSON before capture")
 env=dict(os.environ);env["PYTHONPATH"]=f"{ROOT}:{ROOT/'runners/dsl/python'}:{env.get('PYTHONPATH','')}"
 stale=subprocess.check_output([sys.executable,"-c","from domains.engine_provenance import build_is_stale; print('\\n'.join(build_is_stale('.')))"] ,cwd=ROOT,env=env,text=True).strip()
 if stale:raise SystemExit("native build stale:\n"+stale)
 all_rows=[];schedule=[];start=time.perf_counter();rng=random.Random(SEED)
 jobs=[(mn,ln,enabled,k) for mn in MAPS for ln in LAYOUTS for enabled in (0,1) for k in KS]
 for rep in range(1,REPS+1):
  order=jobs.copy();rng.shuffle(order);schedule.append([[*x,rep] for x in order])
  for mn,ln,en,k in order:
   cmd=[sys.executable,str(Path(__file__).resolve()),"--worker",mn,ln,str(en),str(k),str(rep)]
   try:
    proc=subprocess.run(cmd,cwd=ROOT,env=env,text=True,capture_output=True,check=True,timeout=120)
    row=json.loads(proc.stdout.strip())
   except (subprocess.CalledProcessError,subprocess.TimeoutExpired) as exc:
    row={"matrix_name":mn,"layout":ln,"enabled":bool(en),"K":k,"replicate":rep,"pid":None,"worker_failure":str(exc),"stderr":getattr(exc,"stderr",None)}
   all_rows.append(row)
   print(f"rep={rep} matrix={mn} layout={ln} arm={en} K={k} pid={row.get('pid')} train={row.get('train',{}).get('status',row.get('worker_failure','failed'))}",flush=True)
 lock_sha=sha(LOCK);native=Path(_native.__file__).resolve()
 raw={"protocol":"SUBSTRATE_GENMINT_MATRIX_FAMILY_REUSE_V3","locked_inputs":lock_data,"lock_sha256":lock_sha,"engine":provenance_line(),"commit":subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip(),"environment":{"python":sys.version,"platform":platform.platform()},"schedule":schedule,"workers":all_rows,"worker_count":len(all_rows),"worker_failures":[r for r in all_rows if "worker_failure" in r],"parent_elapsed_seconds":time.perf_counter()-start,"native":{"path":str(native),"sha256":sha(native)},"claim_boundary":"single-host authored matrix/layout extended-horizon transfer and stage-cost accounting; no natural-task or asymptotic claim"}
 OUT.write_text(json.dumps(raw,indent=2,sort_keys=True,default=str)+"\n");print(json.dumps({"output":str(OUT),"workers":len(all_rows),"failures":len(raw["worker_failures"]),"elapsed_seconds":raw["parent_elapsed_seconds"]},indent=2))
if __name__=="__main__":main()

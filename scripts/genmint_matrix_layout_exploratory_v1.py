#!/usr/bin/env python3
"""Unregistered fixture-selection pilot: clean matrices × predicate layouts."""
import hashlib,json,platform,subprocess,sys,time
from pathlib import Path
from domains.engine_provenance import engine_preamble,provenance_line
engine_preamble()
from substrate.boot_core import boot_core
from domains import reflective_faculty as rf
from substrate_rs import _native
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/"evaluation/reports/substrate_genmint_matrix_layout_exploratory_v1_20260926.json"
PTS=[(0,0),(1,0),(0,1),(1,1),(2,0),(0,2)];GROUPS={"adjacent_01":[0,1,4],"opposite_03":[0,3,4],"adjacent_12":[1,2,5]};MAPS={"prior_matrix":[1,1,0,2],"shearA":[1,0,1,1],"shearB":[1,1,0,1]};DT=["pred","coord:r","coord:c","val"]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 rows=[]
 for mn,m in MAPS.items():
  a,b,c,d=m
  for gn,p0 in GROUPS.items():
   base=[];goal=[]
   for i,(r,q) in enumerate(PTS):
    p="p0" if i in p0 else "p1";base.append([p,r,q,"red"]);goal.append([p,a*r+b*q,c*r+d*q,"red"])
   s,ag=boot_core();native=rf._native_eval2(s);rf._ensure_shape_decode_loop(s,native,ag);s.set_attr(ag,"gen_infer_enabled",1.0)
   s.add_node("ShapeSignature",{"name":f"base_{gn}","signature":json.dumps(base),"kind":"faculty","faculty":f"base_{gn}","dim_types":DT})
   epoch=s.node(ag)["attrs"].get("codebook_epoch") or 0.0;obs=s.add_node("Observation",{"signature":goal,"key":["matrix_layout_exploratory",mn,gn],"status":"decoded","residual":goal,"decoded_epoch":epoch,"dim_types":DT});s.add_edge(ag,"observed",obs)
   t0=time.perf_counter();native.run_rules();elapsed=time.perf_counter()-t0;attrs=s.node(obs)["attrs"]
   gens=[list(s.node(n)["attrs"].get("matrix") or []) for n in s.nodes("DimensionGenerator") if s.node(n)["attrs"].get("kind")=="linear"]
   rows.append({"matrix_name":mn,"matrix":m,"layout":gn,"p0_indices":p0,"base":base,"goal":goal,"status":attrs.get("status"),"residual":attrs.get("residual"),"linear_generators":gens,"expected_matrix_acquired":m in gens,"capability_axis_count":len(list(s.nodes("CapabilityAxis"))),"closure_seconds":elapsed})
 native=Path(_native.__file__).resolve();files=["scripts/genmint_matrix_layout_exploratory_v1.py","seeds/shape_decode_loop.json","domains/reflective_faculty.py","domains/engine_provenance.py","substrate/boot_core.py","runners/dsl/src/shape_decode.rs","runners/dsl/src/term.rs","runners/dsl/python/substrate_rs/_native.build.json"]
 out={"status":"exploratory_unregistered_fixture_selection_pilot","engine":provenance_line(),"commit":subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip(),"environment":{"python":sys.version,"platform":platform.platform()},"design":{"points":[list(p) for p in PTS],"matrices":MAPS,"layouts":GROUPS,"induction":"enabled","repetitions":1},"observations":rows,"source_sha256":{f:sha(ROOT/f) for f in files},"native":{"path":str(native),"sha256":sha(native)},"claim_boundary":"single-run clean training acquisition only; fixture-selection pilot, not confirmatory transfer or generalization"}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True,default=str)+"\n");print(json.dumps({"output":str(OUT),"cells":len(rows),"acquired":sum(x["expected_matrix_acquired"] for x in rows)},indent=2))
if __name__=="__main__":main()

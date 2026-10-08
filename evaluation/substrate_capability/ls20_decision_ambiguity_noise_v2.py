#!/usr/bin/env python3
"""Multi-seed paired LS20 transform-recognition noise panel."""
from __future__ import annotations
import hashlib, importlib.util, json, subprocess, sys, time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/"runners/dsl/python")]
RUNNER=Path(__file__).resolve()
PROTOCOL=ROOT/"docs/research/engine_substrate/SUBSTRATE_LS20_DECISION_AMBIGUITY_NOISE_V2_PREREG_20260928.md"
LOCK=ROOT/"evaluation/substrate_capability/ls20_decision_ambiguity_noise_v2_lock_20260928.json"
ANALYZER=ROOT/"evaluation/substrate_capability/analyze_ls20_decision_ambiguity_noise_v2.py"
OUT=ROOT/"evaluation/reports/ls20_decision_ambiguity_noise_v2"
PARTIAL=OUT/"partial.json"; CAPTURE=OUT/"capture.json"
HELPER_PATH=ROOT/"evaluation/substrate_capability/ls20_mapnav_current_source_scale_v1_2.py"
HS=importlib.util.spec_from_file_location("mapnav_lock_helper",HELPER_PATH)
HELPER=importlib.util.module_from_spec(HS); assert HS and HS.loader; HS.loader.exec_module(HELPER)
BENCH_PATH=ROOT/"scripts/arc_ls20_mapnav_measure.py"
BS=importlib.util.spec_from_file_location("ls20_bench_v2",BENCH_PATH)
BENCH=importlib.util.module_from_spec(BS); assert BS and BS.loader; BS.loader.exec_module(BENCH)
NOISES=(8,10,12,14); STATION_LEVELS=(1,6); BLOCKS=(1,2,3,4); N=20
CELLS=[]
for si,stations in enumerate(STATION_LEVELS):
    for ni,sigma in enumerate(NOISES):
        for block in BLOCKS:
            CELLS.append({"name":f"stations{stations}_sigma{sigma}_block{block}","stations":stations,
                          "sigma":sigma,"block":block,"seed":929000+100*si+10*ni+block})

def file_record(path):
    raw=path.read_bytes()
    return {"path":path.relative_to(ROOT).as_posix(),"bytes":len(raw),"sha256":hashlib.sha256(raw).hexdigest()}

def input_lock():
    lock=HELPER.input_lock()
    lock["protocol"]=file_record(PROTOCOL);lock["runner"]=file_record(RUNNER)
    lock["independent_analyzer"]=file_record(ANALYZER);lock["lock_helper"]=file_record(HELPER_PATH)
    lock["benchmark"]=file_record(BENCH_PATH)
    lock["parameters"]={"cells":CELLS,"n_per_cell":N,"noise_levels":list(NOISES),
        "station_levels":list(STATION_LEVELS),"seed_blocks":list(BLOCKS),"router":"quanta",
        "budget_steps":200,"operator_balance":"cycle six required operators within each 20-world seed block",
        "arm_order":"clean first on even episode index; noisy first on odd"}
    lock["git_head"]=subprocess.run(["git","rev-parse","HEAD"],cwd=ROOT,text=True,capture_output=True,check=True).stdout.strip()
    return lock

def atomic(path,value):
    tmp=path.with_suffix(path.suffix+".tmp");tmp.write_text(json.dumps(value,sort_keys=True,indent=2)+"\n");tmp.replace(path)

def operator_for(scn,index,block):
    from worlds import arc_ls20_scenario as world
    fam,p=world._FAMILIES[(index+(block-1)*N)%len(world._FAMILIES)]
    if fam=="recolour":
        colour=int(scn["symbol_cells"][0][2]);param={colour:int(world.RECOLOUR_MAP[colour])}
    else:param=p
    req=world.canonical_key(fam,param)
    matching=[s for s in scn["stations"] if s["key"]==req]
    if not matching:
        if len(scn["stations"])!=1:raise RuntimeError(f"six-station generator omitted operator {req}")
        scn["stations"][0].update({"key":req,"family":fam,"param":param})
    scn["family"],scn["param"],scn["req_key"]=fam,param,req
    scn["goal_cells"]=world.apply_transform(scn["symbol_cells"],fam,param)
    return fam

def noisy_key(symbol,goal,sigma,seed,recognizer):
    import numpy as np
    from worlds.arc import _render_screen,recover_grid_from_render
    from worlds.arc_ls20_scenario import _reposition,BG
    rng=np.random.Generator(np.random.PCG64(seed))
    def see(cells,canvas=20):
        grid=[[BG]*canvas for _ in range(canvas)]
        for r,c,v in _reposition(cells):
            if 0<=r<canvas and 0<=c<canvas:grid[r][c]=int(v)
        image=_render_screen(grid,canvas,canvas).astype(np.float64)
        if sigma:image+=rng.normal(0.0,float(sigma),size=image.shape)
        seen=np.asarray(recover_grid_from_render(np.clip(image,0,255).astype(np.uint8)),dtype=np.int32)
        return [(r,c,int(seen[r,c])) for r in range(seen.shape[0]) for c in range(seen.shape[1]) if int(seen[r,c])!=BG]
    return recognizer(symbol,goal,_see=see)

def run_pair(scn,cell,index):
    from worlds import arc_ls20_scenario as world
    original=world.recognise_required_key
    order=("clean","noisy") if index%2==0 else ("noisy","clean"); outcomes={}
    for arm in order:
        if arm=="clean":world.recognise_required_key=original
        else:
            seed=cell["seed"]*1000+index
            world.recognise_required_key=lambda a,b,_s=cell["sigma"],_seed=seed,_r=original:noisy_key(a,b,_s,_seed,_r)
        t0,c0=time.perf_counter(),time.process_time()
        try:result=BENCH.run_episode(scn,"curious",router="quanta")
        finally:world.recognise_required_key=original
        outcomes[arm]={"result":result,"wall_seconds":time.perf_counter()-t0,"cpu_seconds":time.process_time()-c0}
    return {"order":list(order),"outcomes":outcomes}

def main():
    import numpy as np,resource
    OUT.mkdir(parents=True,exist_ok=True)
    if sys.argv[1:]==["--lock"]:
        if LOCK.exists() or PARTIAL.exists() or CAPTURE.exists():raise SystemExit("refusing overwrite")
        lock=input_lock()
        if lock["native_build_stale_reasons"]:raise SystemExit(f"stale native extension: {lock['native_build_stale_reasons']}")
        atomic(LOCK,lock);print(LOCK.relative_to(ROOT));return
    lock=json.loads(LOCK.read_text())
    if input_lock()!=lock:raise SystemExit("source/input lock drift; preserve partial as censored")
    state=json.loads(PARTIAL.read_text()) if PARTIAL.exists() else {"next_cell":0,"cells":[]}
    started,cpu=time.perf_counter(),time.process_time()
    for ci in range(state["next_cell"],len(CELLS)):
        cell=CELLS[ci];rng=np.random.Generator(np.random.PCG64(cell["seed"]));records=[]
        for i in range(N):
            scn=BENCH.make_scenario(rng,H=16,W=16,n_stations=cell["stations"],walls=True,wall_density=.20)
            op=operator_for(scn,i,cell["block"])
            digest=hashlib.sha256(json.dumps(scn,sort_keys=True,separators=(",",":")).encode()).hexdigest()
            records.append({"cell":cell["name"],"episode_index":i,"required_operator":op,"scenario":scn,
                            "scenario_sha256":digest,"pair":run_pair(scn,cell,i)})
            if (i+1)%5==0:
                print(f"{cell['name']}: {i+1}/{N}",flush=True)
                atomic(PARTIAL,{"next_cell":ci,"cells":state["cells"],"active_cell":cell,"active_records":records})
        state["cells"].append({"parameters":cell,"records":records});state["next_cell"]=ci+1;atomic(PARTIAL,state)
    after=input_lock()
    if after!=lock:raise SystemExit("post-run source/input lock drift")
    capture={"schema_version":1,"run_id":"ls20-decision-ambiguity-noise-v2-20260928","capture_status":"complete",
       "captured_utc":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),"locked_inputs":lock,"post_run_inputs":after,
       "cells":state["cells"],"process":{"wall_seconds":time.perf_counter()-started,"cpu_seconds":time.process_time()-cpu,
       "max_rss_kib":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss},
       "claim_boundary":"Synthetic offline LS20-shaped transform recognition and planning; one or six stations; fixed quanta router; no natural task prevalence claim."}
    atomic(CAPTURE,capture);PARTIAL.unlink(missing_ok=True)
    print(json.dumps({"capture":str(CAPTURE.relative_to(ROOT)),"status":"complete","worlds":sum(len(c['records']) for c in state['cells'])},indent=2))

if __name__=="__main__":main()

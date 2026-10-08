#!/usr/bin/env python3
"""Paired LS20 station-ambiguity and visual-noise capability panel."""
from __future__ import annotations
import hashlib, importlib.util, json, os, platform, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
RUNNER = Path(__file__).resolve()
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_LS20_DECISION_AMBIGUITY_NOISE_V1_PREREG_20260928.md"
AMENDMENT = ROOT / "docs/research/engine_substrate/SUBSTRATE_LS20_DECISION_AMBIGUITY_NOISE_V1_AMENDMENT_20260928.md"
LOCK = ROOT / "evaluation/substrate_capability/ls20_decision_ambiguity_noise_v1_lock_20260928.json"
ANALYZER = ROOT / "evaluation/substrate_capability/analyze_ls20_decision_ambiguity_noise_v1.py"
OUT = ROOT / "evaluation/reports/ls20_decision_ambiguity_noise_v1"
PARTIAL = OUT / "partial.json"
CAPTURE = OUT / "capture.json"
HELPER_PATH = ROOT / "evaluation/substrate_capability/ls20_mapnav_current_source_scale_v1_2.py"
HELPER_SPEC = importlib.util.spec_from_file_location("ls20_lock_helper", HELPER_PATH)
HELPER = importlib.util.module_from_spec(HELPER_SPEC); assert HELPER_SPEC and HELPER_SPEC.loader
HELPER_SPEC.loader.exec_module(HELPER)
BENCH_PATH = ROOT / "scripts/arc_ls20_mapnav_measure.py"
BENCH_SPEC = importlib.util.spec_from_file_location("ls20_mapnav_bench", BENCH_PATH)
BENCH = importlib.util.module_from_spec(BENCH_SPEC); assert BENCH_SPEC and BENCH_SPEC.loader
BENCH_SPEC.loader.exec_module(BENCH)
SCN = BENCH

CELLS = [{"name": f"stations{s}_sigma{sig}", "stations": s, "sigma": sig,
          "seed": 928001 + i} for i, (s, sig) in enumerate(
          ( (s, sig) for s in (1, 6) for sig in (0, 8, 12) ))]
N = 20

def sha_file(path):
    b = path.read_bytes()
    return {"path": path.relative_to(ROOT).as_posix(), "bytes": len(b),
            "sha256": hashlib.sha256(b).hexdigest()}

def input_lock():
    base = HELPER.input_lock()
    base["protocol"] = sha_file(PROTOCOL)
    base["amendment"] = sha_file(AMENDMENT)
    base["runner"] = sha_file(RUNNER)
    base["benchmark"] = sha_file(BENCH_PATH)
    base["lock_helper"] = sha_file(HELPER_PATH)
    base["independent_analyzer"] = sha_file(ANALYZER)
    base["parameters"] = {"cells": CELLS, "n_per_cell": N,
                          "arm_order": "clean first on even index, noisy first on odd index",
                          "router": "quanta", "budget_steps": 200,
                          "noise": "PCG64 Gaussian pixel noise, independent image draws, clip uint8"}
    base["git_head"] = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
        text=True, capture_output=True, check=True).stdout.strip()
    return base

def atomic(path, value):
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n")
    tmp.replace(path)

def noisy_key(scn, sigma, seed, recognizer):
    import numpy as np
    from worlds.arc import _render_screen, recover_grid_from_render, cells_to_signature
    from worlds.arc_ls20_scenario import _reposition, BG, recognise_required_key
    rng = np.random.Generator(np.random.PCG64(seed))
    def observe(cells):
        canvas = 20
        grid = [[BG] * canvas for _ in range(canvas)]
        for r, c, v in _reposition(cells):
            if 0 <= r < canvas and 0 <= c < canvas: grid[r][c] = int(v)
        image = _render_screen(grid, canvas, canvas).astype(np.float64)
        if sigma: image += rng.normal(0.0, float(sigma), size=image.shape)
        seen = np.asarray(recover_grid_from_render(np.clip(image, 0, 255).astype(np.uint8)), dtype=np.int32)
        return [(r, c, int(seen[r,c])) for r in range(seen.shape[0])
                for c in range(seen.shape[1]) if int(seen[r,c]) != BG]
    def see(cells, canvas=20):
        return observe(cells)
    return recognizer(scn["symbol_cells"], scn["goal_cells"], _see=see)

def run_pair(scn, cell, index):
    from worlds import arc_ls20_scenario as world
    original = world.recognise_required_key
    arms = ("clean", "noisy") if index % 2 == 0 else ("noisy", "clean")
    out = {}
    for arm in arms:
        if arm == "clean":
            world.recognise_required_key = original
        else:
            world.recognise_required_key = lambda a,b, _sig=cell["sigma"], _seed=cell["seed"]*1000+index, _recognizer=original: noisy_key({"symbol_cells":a,"goal_cells":b}, _sig, _seed, _recognizer)
        t0, c0 = time.perf_counter(), time.process_time()
        try:
            result = BENCH.run_episode(scn, "curious", router="quanta")
        finally:
            world.recognise_required_key = original
        out[arm] = {"result": result, "wall_seconds": time.perf_counter()-t0,
                    "cpu_seconds": time.process_time()-c0}
    return {"order": list(arms), "outcomes": out}

def main():
    import numpy as np, resource
    OUT.mkdir(parents=True, exist_ok=True)
    if sys.argv[1:] == ["--lock"]:
        if LOCK.exists() or PARTIAL.exists() or CAPTURE.exists(): raise SystemExit("refusing overwrite")
        lk = input_lock()
        if lk["native_build_stale_reasons"]: raise SystemExit(f"stale extension: {lk['native_build_stale_reasons']}")
        atomic(LOCK, lk); print(LOCK.relative_to(ROOT)); return
    lk = json.loads(LOCK.read_text())
    if input_lock() != lk: raise SystemExit("source lock drift; preserve capture as censored")
    state = json.loads(PARTIAL.read_text()) if PARTIAL.exists() else {"next_cell":0,"cells":[]}
    started, cpu = time.perf_counter(), time.process_time()
    for ci in range(state["next_cell"], len(CELLS)):
        cell = CELLS[ci]; rng = np.random.Generator(np.random.PCG64(cell["seed"])); rows=[]
        for i in range(N):
            scn = BENCH.make_scenario(rng, H=16, W=16, n_stations=cell["stations"], walls=True, wall_density=.20)
            rows.append({"cell":cell["name"],"episode_index":i,"scenario":scn,
                         "scenario_sha256":hashlib.sha256(json.dumps(scn,sort_keys=True,separators=(",",":")).encode()).hexdigest(),
                         "pair":run_pair(scn,cell,i)})
            if (i+1)%5==0: print(f"{cell['name']}: {i+1}/{N}",flush=True)
            state["next_cell"], state["cells"] = ci, state["cells"]
            atomic(PARTIAL,state | {"active_cell":cell,"active_records":rows})
        state["cells"].append({"parameters":cell,"records":rows}); state["next_cell"]=ci+1
        state.pop("active_cell",None); state.pop("active_records",None); atomic(PARTIAL,state)
    after=input_lock()
    if after != lk: raise SystemExit("post-run source lock drift")
    capture={"schema_version":1,"run_id":"ls20-decision-ambiguity-noise-v1-20260928",
      "capture_status":"complete","captured_utc":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),
      "locked_inputs":lk,"post_run_inputs":after,"cells":state["cells"],
      "process":{"wall_seconds":time.perf_counter()-started,"cpu_seconds":time.process_time()-cpu,
                 "max_rss_kib":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss},
      "claim_boundary":"Synthetic offline LS20-shaped planning; fixed quanta route executor; paired station-count and recognizer-noise effects."}
    atomic(CAPTURE,capture); PARTIAL.unlink(missing_ok=True)
    print(json.dumps({"capture":str(CAPTURE.relative_to(ROOT)),"status":"complete","n":sum(len(c['records']) for c in state['cells'])},indent=2))

if __name__ == "__main__": main()

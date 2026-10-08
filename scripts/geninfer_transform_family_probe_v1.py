#!/usr/bin/env python3
"""GenInfer direct recovery/time probe over distinct 2-D linear maps."""
from __future__ import annotations
import hashlib, json, platform, random, subprocess, sys, time
from pathlib import Path
from domains.engine_provenance import engine_preamble, provenance_line
engine_preamble()
from substrate_rs import _native  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "evaluation/reports/substrate_geninfer_transform_family_v1_20260926.json"
POINTS = [(0, 0), (1, 0), (2, 0), (0, 2)]
PREDICATES = ["p0", "p1", "p2", "p3"]
TRANSFORMS = {
    "asymmetric_scale_shear": [1, 1, 0, 2],
    "anisotropic_scale": [2, 0, 0, 1],
    "swap_scale": [0, 2, 1, 0],
    "coupled_shear": [2, 0, 1, 1],
}
REPETITIONS = 5
SCHEDULE_SEED = 20260926

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def signature(matrix):
    base, target = [], []
    a,b,c,d = matrix
    for pred,(r,col) in zip(PREDICATES,POINTS):
        base.append([pred,r,col,"red"])
        target.append([pred,a*r+b*col,c*r+d*col,"red"])
    return base,target

def main():
    conditions={}
    for name,matrix in TRANSFORMS.items():
        base,target=signature(matrix)
        sub=_native.Substrate()
        sub.add_node("ShapeSignature",{"name":name,"signature":json.dumps(base),
            "kind":"faculty","faculty":name,
            "dim_types":["pred","coord:r","coord:c","val"]})
        term={"type":"GenInfer","goal":{"type":"Lit","value":target},
            "codebook_type":"ShapeSignature","max_dims":2,"field":"matrix"}
        conditions[name]={"substrate":sub,"term":term,"base":base,"target":target}
    first=next(iter(TRANSFORMS))
    conditions[first]["substrate"].evaluate(conditions[first]["term"],{})
    rng=random.Random(SCHEDULE_SEED); schedule_by_repetition={}; samples=[]
    for repetition in range(1,REPETITIONS+1):
        schedule=list(TRANSFORMS);rng.shuffle(schedule)
        schedule_by_repetition[str(repetition)]=schedule
        for name in schedule:
            cell=conditions[name];start=time.perf_counter()
            matrix=[int(x) for x in cell["substrate"].evaluate(cell["term"],{})]
            elapsed=time.perf_counter()-start
            samples.append({"repetition":repetition,"transform_family":name,
                "base_relation_count":len(cell["base"]),"goal_relation_count":len(cell["target"]),
                "matrix":matrix,"elapsed_seconds":elapsed})
    candidate_counts={name:int(cell["substrate"].evaluate({**cell["term"],"field":"checked"},{}))
        for name,cell in conditions.items()}
    native=Path(_native.__file__).resolve()
    paths=("scripts/geninfer_transform_family_probe_v1.py",
        "scripts/analyze_substrate_geninfer_transform_family_probe_v1.py",
        "docs/research/engine_substrate/SUBSTRATE_GENINFER_TRANSFORM_FAMILY_PREREG_20260926.md",
        "runners/dsl/src/shape_decode.rs","runners/dsl/src/term.rs",
        "runners/dsl/python/substrate_rs/_native.build.json")
    report={"schema_version":1,"run_id":"substrate-geninfer-transform-family-v1-20260926",
        "engine":provenance_line(),"commit":subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip(),
        "environment":{"python":sys.version,"platform":platform.platform()},
        "protocol":{"transforms":TRANSFORMS,"points":[list(p) for p in POINTS],
            "predicates":PREDICATES,"relation_count":4,"bound":4,"candidate_count_per_call":6560,
            "repetitions":REPETITIONS,"schedule_seed":SCHEDULE_SEED,
            "schedule_by_repetition":schedule_by_repetition,
            "warmup":f"one untimed call on {first}","timed_call":"GenInfer(field=matrix)"},
        "candidate_counts":candidate_counts,"samples":samples,
        "provenance":{"source_sha256":{rel:sha(ROOT/rel) for rel in paths},
            "native_extension_path":str(native),"native_extension_sha256":sha(native)},
        "claim_boundary":"Four invertible positive 2-D integer maps on one four-relation unique-predicate signature; direct evaluation only."}
    OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"run_id":report["run_id"],"conditions":len(conditions),"samples":len(samples),
        "candidate_counts":candidate_counts,"output":str(OUT)},indent=2))

if __name__=="__main__":main()

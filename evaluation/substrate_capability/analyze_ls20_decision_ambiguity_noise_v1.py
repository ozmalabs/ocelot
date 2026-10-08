#!/usr/bin/env python3
"""Independent oracle and paired scoring for LS20 ambiguity/noise v1."""
import hashlib, importlib.util, json, math, statistics
from collections import deque
from pathlib import Path
from scipy.stats import binomtest

ROOT=Path(__file__).resolve().parents[2]
CAP=ROOT/"evaluation/reports/ls20_decision_ambiguity_noise_v1/capture.json"
LOCK=ROOT/"evaluation/substrate_capability/ls20_decision_ambiguity_noise_v1_lock_20260928.json"
RUN=ROOT/"evaluation/substrate_capability/ls20_decision_ambiguity_noise_v1.py"
OUT=ROOT/"evaluation/reports/ls20_decision_ambiguity_noise_v1_independent_analysis.json"

def norm(cells):
    if not cells:return frozenset()
    mr=min(int(x[0]) for x in cells); mc=min(int(x[1]) for x in cells)
    return frozenset((int(r)-mr,int(c)-mc,int(v)) for r,c,v in cells)

def apply(cells,family,param):
    out=[(int(r),int(c),int(v)) for r,c,v in cells]
    if family=="rotate":
        for _ in range(int(param)):out=[(c,-r,v) for r,c,v in out]
    elif family=="reflect":
        out=[(r,-c if param=="c" else c,v) if param=="c" else (-r,c,v) for r,c,v in out]
    elif family=="recolour":
        cmap={int(k):int(v) for k,v in param.items()};out=[(r,c,cmap.get(v,v)) for r,c,v in out]
    return norm(out)

def key(f,p):
    if f=="rotate":return f"rot90:{int(p)}"
    if f=="reflect":return f"refl:{p}"
    return "recolour:"+",".join(sorted(f"v{int(a)}>v{int(b)}" for a,b in p.items() if int(a)!=int(b)))

def reachable(s,t,h,w,walls):
    s=tuple(s);t=tuple(t);q=deque([s]);seen={s}
    while q:
        r,c=q.popleft()
        if (r,c)==t:return True
        for p in ((r+1,c),(r-1,c),(r,c+1),(r,c-1)):
            if 0<=p[0]<h and 0<=p[1]<w and p not in walls and p not in seen:seen.add(p);q.append(p)
    return False

def wilson(k,n):
    z=1.959963984540054;p=k/n;d=1+z*z/n
    c=(p+z*z/(2*n))/d;h=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d
    return [c-h,c+h]

def main():
    cap=json.loads(CAP.read_text());lock=json.loads(LOCK.read_text())
    spec=importlib.util.spec_from_file_location("ambiguity_runner",RUN)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    stable=mod.input_lock()==lock==cap.get("locked_inputs")==cap.get("post_run_inputs")
    rows=0;hashes=[];cells={};world_bad=[];route_bad=[];sigma0=[]
    for cell in cap["cells"]:
        p=cell["parameters"];recs=cell["records"]
        arms={a:{"wins":0,"keys":0,"steps":[],"wall":[],"cpu":[],"reasons":{}} for a in ("clean","noisy")};fixed=broken=0
        for row in recs:
            sc=row["scenario"];rows+=1
            digest=hashlib.sha256(json.dumps(sc,sort_keys=True,separators=(",",":")).encode()).hexdigest();hashes.append(digest)
            req=key(sc["family"],sc["param"])
            if req!=sc["req_key"] or apply(sc["symbol_cells"],sc["family"],sc["param"])!=norm(sc["goal_cells"]) or sum(x["key"]==req for x in sc["stations"])!=1:world_bad.append(digest)
            walls={tuple(x) for x in sc["walls"]};targets=[sc["goal_rc"]]+[(x["r"],x["c"]) for x in sc["stations"]]
            if not all(reachable(sc["avatar_rc"],t,16,16,walls) for t in targets):route_bad.append(digest)
            o=row["pair"]["outcomes"]
            for a in arms:
                r=o[a]["result"];win=bool(r["win"])
                if win!=(r["reason"]=="delivered"):world_bad.append(digest)
                arms[a]["wins"]+=int(win);arms[a]["keys"]+=int(r.get("req_key")==req)
                arms[a]["steps"].append(int(r["steps"]));arms[a]["wall"].append(o[a]["wall_seconds"]);arms[a]["cpu"].append(o[a]["cpu_seconds"])
                arms[a]["reasons"][r["reason"]]=arms[a]["reasons"].get(r["reason"],0)+1
            fixed+=int(bool(o["noisy"]["result"]["win"]) and not bool(o["clean"]["result"]["win"]))
            broken+=int(bool(o["clean"]["result"]["win"]) and not bool(o["noisy"]["result"]["win"]))
            if p["sigma"]==0:
                x,y=o["clean"]["result"],o["noisy"]["result"]
                sigma0.append(x["req_key"]==y["req_key"] and x["win"]==y["win"] and x["steps"]==y["steps"])
        armout={};n=len(recs)
        for a,v in arms.items():
            armout[a]={"successes":v["wins"],"accuracy":v["wins"]/n,"wilson_95":wilson(v["wins"],n),
             "recognition_exact":v["keys"],"recognition_accuracy":v["keys"]/n,"median_steps":statistics.median(v["steps"]),
             "wall_median_seconds":statistics.median(v["wall"]),"cpu_median_seconds":statistics.median(v["cpu"]),"reasons":v["reasons"]}
        pval=float(binomtest(fixed,fixed+broken,p=.5,alternative="two-sided").pvalue) if fixed+broken else 1.0
        cells[p["name"]]={"parameters":p,"n":n,"arms":armout,"paired":{"noisy_fixed":fixed,"noisy_broken":broken,"exact_mcnemar_p":pval}}
    gates={"capture_complete":cap.get("capture_status")=="complete","source_lock_stable":stable,
           "native_fresh":not lock.get("native_build_stale_reasons"),"120_world_oracles_pass":rows==120 and not world_bad,
           "all_route_targets_reachable":not route_bad,"unique_scenarios":len(set(hashes))==120,
           "sigma_zero_exact_pair_parity":len(sigma0)==40 and all(sigma0)}
    report={"run_id":cap.get("run_id"),"cells":cells,"integrity_gates":gates,
            "all_integrity_gates_pass":all(gates.values()),"n_scenarios":rows,"process":cap.get("process"),
            "world_oracle_failures":world_bad,"route_failures":route_bad,"claim_boundary":cap.get("claim_boundary")}
    OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"output":str(OUT.relative_to(ROOT)),"gates":gates,"cells":{k:{"clean":v["arms"]["clean"]["successes"],"noisy":v["arms"]["noisy"]["successes"],"recog_clean":v["arms"]["clean"]["recognition_exact"],"recog_noisy":v["arms"]["noisy"]["recognition_exact"]} for k,v in cells.items()}},indent=2))

if __name__=="__main__":main()

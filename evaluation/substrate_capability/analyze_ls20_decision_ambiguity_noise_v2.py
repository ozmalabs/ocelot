#!/usr/bin/env python3
"""Independent task oracle and analysis for ambiguity/noise v2."""
import hashlib,importlib.util,json,math,statistics
from collections import Counter,deque
from pathlib import Path
from scipy.stats import binomtest

ROOT=Path(__file__).resolve().parents[2]
CAP=ROOT/"evaluation/reports/ls20_decision_ambiguity_noise_v2/capture.json"
LOCK=ROOT/"evaluation/substrate_capability/ls20_decision_ambiguity_noise_v2_lock_20260928.json"
RUN=ROOT/"evaluation/substrate_capability/ls20_decision_ambiguity_noise_v2.py"
OUT=ROOT/"evaluation/reports/ls20_decision_ambiguity_noise_v2_independent_analysis.json"

def norm(cells):
    if not cells:return frozenset()
    mr=min(int(x[0]) for x in cells);mc=min(int(x[1]) for x in cells)
    return frozenset((int(r)-mr,int(c)-mc,int(v)) for r,c,v in cells)

def apply(cells,fam,param):
    out=[(int(r),int(c),int(v)) for r,c,v in cells]
    if fam=="rotate":
        for _ in range(int(param)):out=[(c,-r,v) for r,c,v in out]
    elif fam=="reflect":out=[(r,-c if param=="c" else c,v) if param=="c" else (-r,c,v) for r,c,v in out]
    elif fam=="recolour":
        m={int(k):int(v) for k,v in param.items()};out=[(r,c,m.get(v,v)) for r,c,v in out]
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
        for z in ((r+1,c),(r-1,c),(r,c+1),(r,c-1)):
            if 0<=z[0]<h and 0<=z[1]<w and z not in walls and z not in seen:seen.add(z);q.append(z)
    return False

def wilson(k,n):
    z=1.959963984540054;p=k/n;d=1+z*z/n;c=(p+z*z/(2*n))/d
    h=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d
    return [c-h,c+h]

def metrics(rows):
    n=len(rows);result={}
    for arm in ("clean","noisy"):
        outcomes=[r["pair"]["outcomes"][arm] for r in rows]
        keys=[o["result"].get("req_key") for o in outcomes]
        truth=[r["scenario"]["req_key"] for r in rows]
        exact=sum(k==t for k,t in zip(keys,truth));refusal=sum(k is None for k in keys)
        wrong=sum(k is not None and k!=t for k,t in zip(keys,truth))
        wins=sum(bool(o["result"]["win"]) for o in outcomes)
        result[arm]={"successes":wins,"success_rate":wins/n,"success_wilson_95":wilson(wins,n),
          "recognition_exact":exact,"recognition_refusal":refusal,"recognition_wrong_key":wrong,
          "recognized_key_counts":dict(Counter("<refusal>" if k is None else str(k) for k in keys)),
          "reason_counts":dict(Counter(o["result"]["reason"] for o in outcomes)),
          "median_steps":statistics.median(o["result"]["steps"] for o in outcomes),
          "median_wall_seconds":statistics.median(o["wall_seconds"] for o in outcomes),
          "median_cpu_seconds":statistics.median(o["cpu_seconds"] for o in outcomes)}
    fixed=broken=0
    for r in rows:
        a=r["pair"]["outcomes"]["clean"]["result"]["win"]
        b=r["pair"]["outcomes"]["noisy"]["result"]["win"]
        fixed+=int(bool(b) and not bool(a));broken+=int(bool(a) and not bool(b))
    p=float(binomtest(fixed,fixed+broken,p=.5,alternative="two-sided").pvalue) if fixed+broken else 1.0
    return result,{"noisy_fixed":fixed,"noisy_broken":broken,"exact_mcnemar_p":p}

def holm(values):
    ordered=sorted(enumerate(values),key=lambda x:x[1]);m=len(values);adj=[0.0]*m;running=0.0
    for rank,(idx,p) in enumerate(ordered):
        running=max(running,min(1.0,(m-rank)*p));adj[idx]=running
    return adj

def main():
    cap=json.loads(CAP.read_text());lock=json.loads(LOCK.read_text())
    spec=importlib.util.spec_from_file_location("noise_v2_runner",RUN)
    runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)
    stable=runner.input_lock()==lock==cap.get("locked_inputs")==cap.get("post_run_inputs")
    rows=[r for c in cap.get("cells",[]) for r in c["records"]]
    hashes=[];oracle_errors=[];route_errors=[];balance={};groups={}
    for cell in cap.get("cells",[]):
        p=cell["parameters"];blockrows=cell["records"]
        famcounts=Counter(r["required_operator"] for r in blockrows)
        balance[p["name"]]=dict(famcounts)
        if len(blockrows)!=20 or len(famcounts)!=6 or any(v not in (3,4) for v in famcounts.values()):oracle_errors.append(p["name"]+":operator_balance")
        for row in blockrows:
            sc=row["scenario"]
            digest=hashlib.sha256(json.dumps(sc,sort_keys=True,separators=(",",":")).encode()).hexdigest();hashes.append(digest)
            if row.get("scenario_sha256")!=digest:oracle_errors.append(digest+":digest")
            req=key(sc["family"],sc["param"])
            matching=[s for s in sc["stations"] if s.get("key")==req]
            if req!=sc.get("req_key") or apply(sc["symbol_cells"],sc["family"],sc["param"])!=norm(sc["goal_cells"]):oracle_errors.append(digest+":transform")
            if len(matching)!=1 or matching[0].get("family")!=sc["family"] or matching[0].get("param")!=sc["param"]:oracle_errors.append(digest+":station")
            if len(sc["stations"])!=p["stations"]:oracle_errors.append(digest+":station_count")
            walls={tuple(x) for x in sc["walls"]};targets=[sc["goal_rc"]]+[(s["r"],s["c"]) for s in sc["stations"]]
            if not all(reachable(sc["avatar_rc"],t,16,16,walls) for t in targets):route_errors.append(digest)
            for arm,item in row["pair"]["outcomes"].items():
                out=item["result"]
                if bool(out["win"])!=(out["reason"]=="delivered"):oracle_errors.append(digest+":terminal")
            groups.setdefault((p["stations"],p["sigma"]),[]).append(row)
    strata={};pkeys=[];rawps=[]
    for (stations,sigma),items in sorted(groups.items()):
        arms,paired=metrics(items);seed_rows={}
        for block in (1,2,3,4):
            subset=[r for r in items if r["scenario"].get("seed_block")==block]
            # Seed-block membership is encoded by the parent cell metadata below.
            if not subset:
                subset=[r for c in cap["cells"] if c["parameters"]["stations"]==stations and c["parameters"]["sigma"]==sigma and c["parameters"]["block"]==block for r in c["records"]]
            sa,sp=metrics(subset);seed_rows[str(block)]={"n":len(subset),"arms":sa,"paired":sp}
        strata[f"stations{stations}_sigma{sigma}"]={"stations":stations,"sigma":sigma,"n":len(items),"seed_blocks":seed_rows,"arms":arms,"paired":paired}
        pkeys.append(f"stations{stations}_sigma{sigma}");rawps.append(paired["exact_mcnemar_p"])
    adjusted=holm(rawps)
    for k,p in zip(pkeys,adjusted):strata[k]["paired"]["holm_adjusted_p_across_eight_strata"]=p
    integrity={"capture_complete":cap.get("capture_status")=="complete","source_build_lock_stable":stable,
      "native_extension_fresh":not lock.get("native_build_stale_reasons"),"exactly_640_unique_scenarios":len(rows)==640 and len(set(hashes))==640,
      "scenario_digests_match":not any(":digest" in e for e in oracle_errors),"all_transform_station_terminal_oracles_pass":not oracle_errors,
      "all_goal_and_station_routes_reachable":not route_errors,"all_16_operator_blocks_balanced":len(balance)==16 and all(len(x)==6 and all(3<=n<=4 for n in x.values()) for x in balance.values()),
      "eight_station_noise_strata_complete":len(groups)==8 and all(len(v)==80 for v in groups.values())}
    report={"run_id":cap.get("run_id"),"n_scenarios":len(rows),"strata":strata,"operator_counts_by_seed_block":balance,
      "integrity_gates":integrity,"all_integrity_gates_pass":all(integrity.values()),"process":cap.get("process"),
      "oracle_errors":oracle_errors,"route_errors":route_errors,"claim_boundary":cap.get("claim_boundary")}
    OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"output":str(OUT.relative_to(ROOT)),"integrity_gates":integrity,
      "strata":{k:{"clean_success":v["arms"]["clean"]["successes"],"noisy_success":v["arms"]["noisy"]["successes"],
        "exact":v["arms"]["noisy"]["recognition_exact"],"refusal":v["arms"]["noisy"]["recognition_refusal"],
        "wrong":v["arms"]["noisy"]["recognition_wrong_key"],"p_holm":v["paired"]["holm_adjusted_p_across_eight_strata"]} for k,v in strata.items()}},indent=2))

if __name__=="__main__":main()

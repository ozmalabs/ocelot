#!/usr/bin/env python3
"""Seed-cluster uncertainty summary for the position-held-out orientation panel."""
from __future__ import annotations
import hashlib, itertools, json, math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "evaluation/reports/vision_eye_position_heldout_orientation_v1_analysis_20261005.json"
CAPTURE = ROOT / "evaluation/reports/vision_eye_position_heldout_orientation_v1_20261005.json"
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_VISION_EYE_POSITION_HELDOUT_ORIENTATION_V1_1_UNCERTAINTY_PROTOCOL_20261005.md"
SCRIPT = Path(__file__).resolve()
LOCK = ROOT / "evaluation/substrate_capability/vision_eye_position_heldout_orientation_v1_1_uncertainty_lock_20261005.json"
OUT = ROOT / "evaluation/reports/vision_eye_position_heldout_orientation_v1_1_uncertainty_20261005.json"

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def manifest():
    return {"analyzer_sha256": sha(SCRIPT), "protocol_sha256": sha(PROTOCOL),
            "source_analysis_sha256": sha(SOURCE), "capture_sha256": sha(CAPTURE)}
def quantile_nearest_rank(values, probability):
    return values[max(0, math.ceil(probability * len(values)) - 1)]
def main():
    import sys
    if sys.argv[1:2] == ["--lock"]:
        if LOCK.exists() or OUT.exists(): raise SystemExit("refusing to overwrite uncertainty artifacts")
        LOCK.write_text(json.dumps({"schema":"OrientationUncertaintyV1Lock","inputs":manifest()},indent=2,sort_keys=True)+"\n")
        print(LOCK.relative_to(ROOT).as_posix()); return 0
    lock=json.loads(LOCK.read_text())
    if manifest()!=lock["inputs"]: raise SystemExit("uncertainty inputs changed after lock")
    data=json.loads(SOURCE.read_text())
    rows=[]
    class_counts={"horizontal":{"learned":0,"initial":0},"vertical":{"learned":0,"initial":0}}
    learned_only=initial_only=both=neither=0
    for seedrow in data["per_seed"]:
        pred=seedrow["predictions"]
        learned=sum(x["outcomes"]["learned_activation"] for x in pred)
        initial=sum(x["outcomes"]["initial_random_activation"] for x in pred)
        rows.append({"seed":seedrow["seed"],"learned_correct":learned,"initial_correct":initial,
                     "delta_correct":learned-initial,"delta_accuracy":(learned-initial)/len(pred)})
        for x in pred:
            l=x["outcomes"]["learned_activation"]; i=x["outcomes"]["initial_random_activation"]
            if l and not i: learned_only+=1
            elif i and not l: initial_only+=1
            elif i and l: both+=1
            else: neither+=1
            class_counts[x["label"]]["learned"]+=int(l)
            class_counts[x["label"]]["initial"]+=int(i)
    win=sum(x["delta_correct"]>0 for x in rows); loss=sum(x["delta_correct"]<0 for x in rows); ties=len(rows)-win-loss
    n=win+loss
    if n:
        k=min(win,loss)
        tail=sum(math.comb(n,i) for i in range(k+1))/(2**n)
        sign_p=min(1.0,2*tail)
    else: sign_p=1.0
    effects=[x["delta_accuracy"] for x in rows]
    boot=[]
    for sample in itertools.product(effects, repeat=len(effects)):
        boot.append(sum(sample)/len(sample))
    boot.sort()
    ci=[quantile_nearest_rank(boot,.025),quantile_nearest_rank(boot,.975)]
    result={"schema":"OrientationSeedUncertaintyV1","run_id":"orientation-seed-uncertainty-v1-20261005",
        "inputs":lock["inputs"],"seed_results":rows,"seed_wins_losses_ties":{"wins":win,"losses":loss,"ties":ties},
        "exact_two_sided_sign_test_p":sign_p,"seed_bootstrap_accuracy_difference_95_percentile_interval":ci,
        "bootstrap_resamples":len(boot),"paired_probe_outcomes":{"learned_only_correct":learned_only,
            "initial_only_correct":initial_only,"both_correct":both,"both_incorrect":neither},
        "class_correct_counts":class_counts,"interpretation":"Post-hoc uncertainty summary; six seeds are the replication units. Probe-level discordances are descriptive and are not treated as independent trials."}
    if manifest()!=lock["inputs"]: raise SystemExit("analysis sources changed during calculation")
    OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"seed_wins_losses_ties":result["seed_wins_losses_ties"],"sign_test_p":sign_p,
        "seed_bootstrap_95_interval":ci,"paired_probe_outcomes":result["paired_probe_outcomes"],"output":OUT.relative_to(ROOT).as_posix()}))
    return 0
if __name__=="__main__": raise SystemExit(main())

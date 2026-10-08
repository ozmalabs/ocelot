#!/usr/bin/env python3
"""Tranche 3: the full SELF-AUTHORED improvement chain feeds outcome credit.
flag -> promote -> agent's own author rule mints Experiment (via _concern_tick)
-> real child dispatch (paired-control replay) -> agent's own authored judge
-> variation_credit rules credit the verdict. n=1; feasibility + wiring check."""
import hashlib, json, sys, tempfile, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python"), str(ROOT / "tests"), str(ROOT / "scripts")]
OUT = ROOT / "evaluation/reports/variation_credit_self_authored_v1_20261007.json"

def main():
    if OUT.exists(): raise SystemExit("refusing to overwrite")
    import test_convo_experiment_migrated as T
    import domains.reflective_faculty as rf
    import substrate_rs as srs
    jd = T.jd
    from substrate.world_adapter import WorldAdapter
    from substrate.boot_all import load_all_seeds
    t0 = time.time()
    a = WorldAdapter(seeds=()); load_all_seeds(a)
    rf._ensure_seed_chain(a.s, a.inner, a.agent, ("variation_ops", "variation_credit"))
    turn = T._have_two_turns(a); cid = T._flag(a, turn)
    p = jd.promote_self_concern(a, cid)
    jd._concern_tick(a)
    key = f"promoted_self_concern_{cid}"
    exps = [(n, at) for n, at in T._experiments(a, game="conversation") if at.get("axis_tag") == key]
    rec = {"promoted": p.get("ok"), "self_authored_experiments": len(exps)}
    if len(exps) == 1:
        exp = exps[0][0]
        delta = next(iter(a.inner.neighbours(exp, "has_delta")))
        da = a.s.node(delta)["attrs"]
        rec.update({"delta_variation_op": da.get("variation_op"), "delta_remove_rules": da.get("remove_rules")})
        ts = time.time()
        rec["dispatch_status"] = T._dispatch_until(a, Path(tempfile.mkdtemp(prefix="vcsa-")), exp)
        rec["child_seconds"] = time.time() - ts
        a.comprehend(); a.inner.run_rules()
        ea, da = a.s.node(exp)["attrs"], a.s.node(delta)["attrs"]
        rec.update({"outcome": ea.get("outcome"), "adopt_ready": ea.get("adopt_ready"),
                    "credited": da.get("credited"), "judged_outcome": da.get("judged_outcome")})
    rec["credits"] = {f"{x.get('op')}|{x.get('kind')}": [x.get("trials"), x.get("supports")]
                      for x in (a.s.node(n)["attrs"] for n in a.s.nodes("VariationCredit"))}
    rec["elapsed_seconds"] = time.time() - t0
    rec["checks"] = {"agent_authored_exactly_one": rec["self_authored_experiments"] == 1,
                     "dispatched_done": rec.get("dispatch_status") == "done",
                     "supported": rec.get("outcome") == "supported",
                     "credited_from_real_verdict": rec.get("credited") == 1 and rec.get("judged_outcome") == rec.get("outcome")}
    rec["native_sha256"] = hashlib.sha256((ROOT / "runners/dsl/python/substrate_rs/_native.abi3.so").read_bytes()).hexdigest()
    OUT.write_text(json.dumps(rec, indent=1, sort_keys=True, default=str) + "\n")
    print(json.dumps(rec, indent=1, default=str))

main()

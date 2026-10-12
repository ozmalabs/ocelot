#!/usr/bin/env python3
"""Tranche 8: preregistered real-verdict variation-credit gate.
See docs/research/engine_substrate/SUBSTRATE_VARIATION_CREDIT_REAL_JUDGE_V1_PREREG_20261008.md.
One agent per arm processes a stream of instruction gaps with a misordered
prior (reply_ablation.priority=8 < cue_set_edit 10); OFF = use_credit 0,
ON = use_credit 1. Real child replays, agent-initiated retries only."""
import hashlib, json, os, sys, tempfile, time
os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python"), str(ROOT / "tests"), str(ROOT / "scripts")]
OUT = ROOT / "evaluation/reports/variation_credit_real_judge_v1_20261008.json"
VERBS = ["condense", "tabulate", "shorten", "alphabetise", "paraphrase"]
ERR = "ERROR: no communicative response could be generated."


def run_arm(use_credit):
    import test_agent_authors_new_rule_migrated as T
    import substrate_rs as srs
    jd, rf = T.jd, T.rf
    from substrate.world_adapter import WorldAdapter
    from substrate.boot_all import load_all_seeds
    a = WorldAdapter(seeds=()); load_all_seeds(a)
    rf._ensure_seed_chain(a.s, a.inner, a.agent, ("variation_ops", "variation_credit", "instruction_repair_retry"))
    for n in a.s.nodes("VariationOp"):
        if a.s.node(n)["attrs"].get("name") == "reply_ablation":
            a.s.set_attr(n, "priority", 8)
    for n in a.s.nodes("VariationPolicy"):
        a.s.set_attr(n, "use_credit", int(use_credit)); a.s.set_attr(n, "exclude_refuted", 1)
    a.converse("Hello.", speech_act="greeting")
    runs = Path(tempfile.mkdtemp(prefix=f"vcrj-{int(use_credit)}-"))
    rows = []
    for verb in VERBS:
        rec = {"verb": verb, "attempts": []}
        floor = a.converse(f"{verb.capitalize()} the data.", speech_act="request")
        rec["gap_filed"] = "filed it as a gap" in (floor or "").lower()
        if not rec["gap_filed"]:
            rec["skip"] = floor; rows.append(rec); continue
        a.converse(f"Work on the {verb} data gap.", speech_act="request")
        prom = jd._steer_tick(a)
        if not (prom and prom[0].get("ok")):
            rec["skip"] = f"promote failed {prom}"; rows.append(rec); continue
        sc = srs.NodeID(int(prom[0]["self_concern"]))
        for k in range(4):
            jd._concern_tick(a)
            exps = [e for e in a.s.nodes("Experiment") if a.s.node(e)["attrs"].get("game") == "conversation"
                    and a.s.node(e)["attrs"].get("status") == "requested"]
            if len(exps) != 1:
                rec["attempts"].append({"k": k, "no_experiment": len(exps)}); break
            exp = exps[0]; d = next(iter(a.inner.neighbours(exp, "has_delta"))); da = a.s.node(d)["attrs"]
            t0 = time.time(); st = T._dispatch_until(a, runs / f"{verb}-{k}", exp)
            a.comprehend(); a.inner.run_rules(); rf.close_experiment_loop(a)
            at = a.s.node(exp)["attrs"]
            rec["attempts"].append({"k": k, "op": da.get("variation_op"), "route": da.get("cue_route"), "status": st,
                                    "outcome": at.get("outcome"), "regressions": at.get("regressions"),
                                    "adopted": bool(at.get("adopted")), "child_s": time.time() - t0})
            if at.get("outcome") == "supported":
                break
            if a.s.node(sc)["attrs"].get("retry_requested") != 1:
                break
        reply = a.converse(f"{verb.capitalize()} the data.", speech_act="request")
        mid = a._last_turn_inbound
        rec["final_reply"] = reply
        rec["final_handled"] = (a.s.node(mid)["attrs"].get("instruction_outcome") == "handled" and reply.strip() != ERR
                                and "gap" not in (reply or "").lower())
        rec["credits"] = {f"{x.get('op')}|{x.get('kind')}": [x.get("trials"), x.get("supports")]
                          for x in (a.s.node(n)["attrs"] for n in a.s.nodes("VariationCredit"))}
        rows.append(rec); print(json.dumps(rec, default=str)[:900], flush=True)
    real = [x for r in rows for x in r["attempts"] if "op" in x]
    summ = {"experiments": len(real),
            "handled": sum(1 for r in rows if r.get("final_handled")),
            "first_pick_cue": sum(1 for r in rows if r["attempts"] and r["attempts"][0].get("op") == "cue_set_edit"),
            "false_adoptions": sum(1 for x in real if x.get("adopted") and x.get("outcome") != "supported")
                               + sum(1 for r in rows if any(x.get("adopted") for x in r["attempts"]) and not r.get("final_handled")),
            "ops": [x.get("op") for x in real], "outcomes": [x.get("outcome") for x in real]}
    return {"use_credit": use_credit, "rows": rows, "summary": summ}


def main():
    if OUT.exists(): raise SystemExit("refusing to overwrite")
    t0 = time.time()
    off = run_arm(0); print("OFF", json.dumps(off["summary"]), flush=True)
    on = run_arm(1); print("ON", json.dumps(on["summary"]), flush=True)
    g = {"G1_handled": on["summary"]["handled"] >= off["summary"]["handled"],
         "G2_fewer_experiments": on["summary"]["experiments"] < off["summary"]["experiments"],
         "G3_no_false_adoption": on["summary"]["false_adoptions"] == 0}
    g["pass"] = all(g.values())
    print("GATE", json.dumps(g), flush=True)
    OUT.write_text(json.dumps({"schema": "VariationCreditRealJudgeV1", "verbs": VERBS, "off": off, "on": on, "gate": g,
        "elapsed_s": time.time() - t0,
        "prereg": "docs/research/engine_substrate/SUBSTRATE_VARIATION_CREDIT_REAL_JUDGE_V1_PREREG_20261008.md",
        "native_sha256": hashlib.sha256((ROOT / "runners/dsl/python/substrate_rs/_native.abi3.so").read_bytes()).hexdigest()},
        indent=1, sort_keys=True, default=str) + "\n")

main()

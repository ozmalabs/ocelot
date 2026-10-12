#!/usr/bin/env python3
"""Tranche 14: preregistered mixed-kind variation-credit gate v2 (lab boot):
the reported kind's misordered family (rule_literal_edit) BUILDS and
dispatches, so a wrong prior costs real replays. See
docs/research/engine_substrate/SUBSTRATE_VARIATION_CREDIT_MIXED_KIND_V2_PREREG_20261009.md.
One arm per process; --gate aggregates."""
import hashlib, json, os, shutil, sys, tempfile, time
os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python"), str(ROOT / "tests"), str(ROOT / "scripts")]
REP = ROOT / "evaluation/reports"
part = lambda arm: REP / f"variation_credit_mixed_kind_v2_{arm}_20261009.json"
GATE_OUT = REP / "variation_credit_mixed_kind_v2_gate_20261009.json"
ARMS = {"A": {"use_credit": 0, "exclude_refuted": 1, "credit_internal_exempt": 0, "exclude_inconclusive": 0},
        "B": {"use_credit": 0, "exclude_refuted": 1, "credit_internal_exempt": 1, "exclude_inconclusive": 1},
        "C": {"use_credit": 1, "exclude_refuted": 1, "credit_internal_exempt": 1, "exclude_inconclusive": 1}}
CORPUS = ["The drawer contains a spoon, a fork and a knife.", "The basket contains an apple and a pear.",
          "The shelf contains a vase, a clock, a lamp, a frame and a candle.", "The crate contains a hammer, a nail, a screw and a bolt.",
          "The garden contains a rose and a tulip.", "The dog barked at the postman.", "The sun rose early.",
          "The van contains a ladder, a bucket, a mop, a brush, a sponge and a rag."]
EAGER = "you reform list sentences too eagerly, test whether the hardcoded residual marker threshold floor is too low"
RARE = "you reform list sentences too rarely, test whether the hardcoded residual marker threshold floor is too high"
STREAM = [("I", "condense"), ("R", EAGER), ("I", "tabulate"), ("R", RARE),
          ("I", "shorten"), ("R", EAGER), ("I", "alphabetise"), ("R", RARE)]
WORKING = {"I": "cue_set_edit", "R": "knob_edit"}
ERR = "ERROR: no communicative response could be generated."


def run_arm(arm):
    import test_agent_authors_new_rule_migrated as T
    import substrate_rs as srs
    jd, rf = T.jd, T.rf
    from substrate.world_adapter import WorldAdapter
    from substrate.boot_all import load_all_seeds
    a = WorldAdapter(seeds=(), shadow_read=True); load_all_seeds(a)
    rf._ensure_seed_chain(a.s, a.inner, a.agent, ("variation_ops", "variation_credit", "instruction_repair_retry"))
    for n in a.s.nodes("InstructionRetryPolicy"):
        a.s.set_attr(n, "concern_kinds", ["instruction", "reported"])
    for n in a.s.nodes("VariationOp"):
        if a.s.node(n)["attrs"].get("name") == "rule_literal_edit":
            a.s.set_attr(n, "priority", 8)      # misordered: outranks knob_edit (15) and cue_set_edit (10)
    for n in a.s.nodes("VariationPolicy"):
        for k, v in ARMS[arm].items():
            a.s.set_attr(n, k, v)
    a.converse("Hello.", speech_act="greeting")
    for t in CORPUS:
        a.converse(t, speech_act="statement")
    runs = Path(tempfile.mkdtemp(prefix=f"vcmk2-{arm}-"))
    rows = []
    for idx, (kind, item) in enumerate(STREAM):
        rec = {"i": idx, "kind": kind, "item": item, "attempts": []}
        if kind == "I":
            floor = a.converse(f"{item.capitalize()} the data.", speech_act="request")
            if "filed it as a gap" not in (floor or "").lower():
                rec["skip"] = floor; rows.append(rec); continue
            a.converse(f"Work on the {item} data gap.", speech_act="request")
            prom = jd._steer_tick(a)
            if not (prom and prom[0].get("ok")):
                rec["skip"] = f"promote failed {prom}"; rows.append(rec); continue
            sc = srs.NodeID(int(prom[0]["self_concern"]))
        else:
            sc = a.s.add_node("SelfConcern", {"kind": "reported", "status": "noted", "source": "explicit", "content": item})
            a.inner.add_edge_unchecked(a.agent, "has_self_concern", sc)
            if jd.promote_self_concern(a, str(sc.value)).get("pipeline") != "experiment":
                rec["skip"] = "not an experiment pipeline"; rows.append(rec); continue
        for k in range(4):
            jd._concern_tick(a)
            exps = [e for e in a.s.nodes("Experiment") if a.s.node(e)["attrs"].get("game") == "conversation"
                    and a.s.node(e)["attrs"].get("status") == "requested"]
            if len(exps) != 1:
                rec["attempts"].append({"k": k, "no_experiment": len(exps)})
                a.inner.run_rules()
                if a.s.node(sc)["attrs"].get("retry_requested") == 1:
                    continue
                break
            exp = exps[0]; da = a.s.node(next(iter(a.inner.neighbours(exp, "has_delta"))))["attrs"]
            t0 = time.time(); st = T._dispatch_until(a, runs / f"{idx}-{k}", exp)
            a.comprehend(); a.inner.run_rules(); rf.close_experiment_loop(a)
            at = a.s.node(exp)["attrs"]
            rec["attempts"].append({"k": k, "op": da.get("variation_op"), "route": da.get("cue_route"), "knob": da.get("knob_attr"),
                                    "rule_varied": da.get("act_rule_varied"),
                                    "old": da.get("knob_old_value"), "new": da.get("knob_new_value"), "status": st,
                                    "outcome": at.get("outcome"), "adopted": bool(at.get("adopted")), "child_s": time.time() - t0})
            shutil.rmtree(runs / f"{idx}-{k}", ignore_errors=True)
            if at.get("outcome") == "supported" or a.s.node(sc)["attrs"].get("retry_requested") != 1:
                break
        if kind == "I":
            reply = a.converse(f"{item.capitalize()} the data.", speech_act="request")
            mid = a._last_turn_inbound
            rec["handled"] = (a.s.node(mid)["attrs"].get("instruction_outcome") == "handled" and reply.strip() != ERR
                              and "gap" not in (reply or "").lower())
        else:
            rec["handled"] = any(x.get("outcome") == "supported" and x.get("adopted") for x in rec["attempts"])
        rec["credits"] = {f"{x.get('op')}|{x.get('kind')}": [x.get("trials"), x.get("supports")]
                          for x in (a.s.node(n)["attrs"] for n in a.s.nodes("VariationCredit"))}
        rows.append(rec); print(json.dumps(rec, default=str)[:900], flush=True)
    shutil.rmtree(runs, ignore_errors=True)
    summ = {}
    for kind in ("I", "R"):
        rs = [r for r in rows if r["kind"] == kind]
        real = [x for r in rs for x in r["attempts"] if "op" in x]
        summ[kind] = {"handled": sum(1 for r in rs if r.get("handled")), "experiments": len(real),
                      "false_adoptions": sum(1 for x in real if x.get("adopted") and x.get("outcome") != "supported"),
                      "skipped": [r["item"][:20] for r in rs if r.get("skip")]}
    summ["late_first_pick_correct"] = sum(1 for r in rows if r["i"] >= 4 and r["attempts"]
                                          and r["attempts"][0].get("op") == WORKING[r["kind"]])
    summ["late_reported_first_pick_knob"] = sum(1 for r in rows if r["i"] >= 4 and r["kind"] == "R" and r["attempts"]
                                                and next((x.get("op") for x in r["attempts"] if "op" in x), None) == "knob_edit")
    return {"arm": arm, "policy": ARMS[arm], "rows": rows, "summary": summ}


def main():
    if "--gate" in sys.argv:
        if GATE_OUT.exists(): raise SystemExit("refusing to overwrite")
        P = {arm: json.loads(part(arm).read_text())["summary"] for arm in ARMS}
        A, B, C = P["A"], P["B"], P["C"]
        g = {"G1_credit_saves_replays_reported": C["R"]["experiments"] < B["R"]["experiments"]
                                                 and C["R"]["handled"] >= B["R"]["handled"],
             "G2_no_cross_kind_harm_instruction": C["I"]["handled"] >= B["I"]["handled"]
                                                  and C["I"]["experiments"] <= B["I"]["experiments"],
             "G3_no_false_adoption_B_C": sum(X[k]["false_adoptions"] for X in (B, C) for k in ("I", "R")) == 0,
             "G4_late_reported_first_pick_knob": C["late_reported_first_pick_knob"] == 2}
        g["pass"] = all(g.values())
        print("SUMMARY", json.dumps(P)); print("GATE", json.dumps(g))
        GATE_OUT.write_text(json.dumps({"schema": "VariationCreditMixedKindV2Gate", "summaries": P, "gate": g,
            "prereg": "docs/research/engine_substrate/SUBSTRATE_VARIATION_CREDIT_MIXED_KIND_V2_PREREG_20261009.md"},
            indent=1, sort_keys=True) + "\n")
        return
    arm = sys.argv[1]
    out = part(arm)
    if out.exists(): raise SystemExit("refusing to overwrite")
    t0 = time.time(); r = run_arm(arm); print("SUMMARY", json.dumps(r["summary"]), flush=True)
    r.update({"schema": "VariationCreditMixedKindV2Part", "elapsed_s": time.time() - t0,
              "native_sha256": hashlib.sha256((ROOT / "runners/dsl/python/substrate_rs/_native.abi3.so").read_bytes()).hexdigest()})
    out.write_text(json.dumps(r, indent=1, sort_keys=True, default=str) + "\n")

main()

#!/usr/bin/env python3
"""Tranche 11: preregistered promotion gate v2 for grain-quantised knob steps.
See docs/research/engine_substrate/SUBSTRATE_KNOB_GRAIN_PROMOTION_V2_PREREG_20261008.md.
One (corpus, arm) per process; --gate aggregates."""
import hashlib, json, os, sys, tempfile, time
os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python"), str(ROOT / "tests"), str(ROOT / "scripts")]
REP = ROOT / "evaluation/reports"
part = lambda c, m: REP / f"knob_grain_promotion_v2_{c}_{m}_20261008.json"
GATE_OUT = REP / "knob_grain_promotion_v2_20261008.json"
CORP = {
  "K1": ([(t, "statement") for t in (
      "The drawer contains a spoon, a fork and a knife.", "The basket contains an apple and a pear.",
      "The shelf contains a vase, a clock, a lamp, a frame and a candle.", "The crate contains a hammer, a nail, a screw and a bolt.",
      "The garden contains a rose and a tulip.", "The dog barked at the postman.", "The sun rose early.",
      "The van contains a ladder, a bucket, a mop, a brush, a sponge and a rag.")],
         [("eager", "you reform list sentences too eagerly, test whether the residual marker threshold is too low"),
          ("rare", "you reform list sentences too rarely, test whether the residual marker threshold is too high")]),
  "K2": ([("Hello.", "greeting"), ("What do you know about the moon?", "question"),
          ("The horse raced past the barn fell.", "statement"),
          ("The committee, which had been convened after the report that the auditors, who were themselves under review, had submitted was leaked, decided that the policy should proceed.", "statement"),
          ("The old man the boats.", "statement")],
         [("eager", "you reform the topic too eagerly, test whether the threshold is too low")]),
  "K3": ([(t, "statement") for t in (
      "The kit includes a hammer, a saw and a drill.", "The bag includes a map and a torch.",
      "The box includes a pen, a cup, a lamp and a book.", "The set includes a fork, a knife, a spoon, a plate and a bowl.",
      "The toolbox includes a hammer and a saw.", "The cat sat on the mat.", "The room had a bed.")], None),
}
CORP["K3"] = (CORP["K3"][0], CORP["K1"][1])


def run_arm(corpus, mode):
    CORPUS, CONCERNS = CORP[corpus]
    import test_agent_authors_new_rule_migrated as T
    import convo_child_run as C
    jd, rf = T.jd, T.rf
    from substrate.world_adapter import WorldAdapter
    from substrate.boot_all import load_all_seeds
    a = WorldAdapter(seeds=(), shadow_read=True); load_all_seeds(a)
    rf._ensure_seed_chain(a.s, a.inner, a.agent, ("variation_ops", "variation_credit", "instruction_repair_retry"))
    for n in a.s.nodes("InstructionRetryPolicy"):
        a.s.set_attr(n, "concern_kinds", ["instruction", "reported"])
    if mode == "grain":
        for n in a.s.nodes("VariationOp"):
            if a.s.node(n)["attrs"].get("name") == "knob_edit":
                a.s.set_attr(n, "step_mode", "grain")
    for t, sa in CORPUS:
        a.converse(t, speech_act=sa)
    budget = lambda: {k: v for k, v in next(a.s.node(n)["attrs"] for n in a.s.nodes("ApertureBudget")
                      if a.s.node(n)["attrs"].get("register") == "conversational").items() if k.startswith("reform_")}
    runs = Path(tempfile.mkdtemp(prefix=f"kgpr-{corpus}{mode}-"))
    out = {"corpus": corpus, "mode": mode, "concerns": []}
    for tag, text in CONCERNS:
        rec = {"tag": tag, "text": text, "threshold_before": budget(), "attempts": []}
        sc = a.s.add_node("SelfConcern", {"kind": "reported", "status": "noted", "source": "explicit", "content": text})
        a.inner.add_edge_unchecked(a.agent, "has_self_concern", sc)
        rec["pipeline"] = jd.promote_self_concern(a, str(sc.value)).get("pipeline")
        for k in range(4):
            jd._concern_tick(a)
            exps = [e for e in a.s.nodes("Experiment") if a.s.node(e)["attrs"].get("game") == "conversation"
                    and a.s.node(e)["attrs"].get("status") == "requested"]
            if len(exps) != 1:
                rec["attempts"].append({"k": k, "no_experiment": len(exps)}); break
            exp = exps[0]; d = next(iter(a.inner.neighbours(exp, "has_delta"))); da = a.s.node(d)["attrs"]
            t0 = time.time(); st = T._dispatch_until(a, runs / f"{tag}{k}", exp)
            a.comprehend(); a.inner.run_rules(); rf.close_experiment_loop(a)
            at = a.s.node(exp)["attrs"]
            rec["attempts"].append({"k": k, "op": da.get("variation_op"), "knob": da.get("knob_attr"),
                                    "direction": da.get("knob_direction"), "old": da.get("knob_old_value"),
                                    "new": da.get("knob_new_value"), "status": st,
                                    "control_reforms": at.get("control_reforms"), "variant_reforms": at.get("variant_reforms"),
                                    "regressions": at.get("regressions"), "outcome": at.get("outcome"),
                                    "adopted": bool(at.get("adopted")), "child_s": time.time() - t0})
            if at.get("outcome") == "supported" or a.s.node(sc)["attrs"].get("retry_requested") != 1:
                break
        rec["threshold_after"] = budget()
        out["concerns"].append(rec); print(json.dumps(rec, default=str), flush=True)
    r0 = C._count_reform_marks(a)
    for t, sa in CORPUS:
        a.converse(t, speech_act=sa)
    out["parent_reforms_on_rehear"] = C._count_reform_marks(a) - r0
    real = [x for c in out["concerns"] for x in c["attempts"] if "op" in x]
    out["summary"] = {"supported": sum(1 for c in out["concerns"] if any(x.get("outcome") == "supported" and x.get("adopted") for x in c["attempts"])),
                      "experiments": len(real),
                      "false_adoptions": sum(1 for x in real if x.get("adopted") and x.get("outcome") != "supported")}
    return out


def main():
    if "--gate" in sys.argv:
        if GATE_OUT.exists(): raise SystemExit("refusing to overwrite")
        p = {(c, m): json.loads(part(c, m).read_text())["summary"] for c in CORP for m in ("fixed", "grain")}
        g = {"Q1_grain_ge_fixed_every_corpus": all(p[(c, "grain")]["supported"] >= p[(c, "fixed")]["supported"] for c in CORP),
             "Q2_grain_gt_fixed_some_corpus": any(p[(c, "grain")]["supported"] > p[(c, "fixed")]["supported"] for c in CORP),
             "Q3_no_false_adoption_grain": all(p[(c, "grain")]["false_adoptions"] == 0 for c in CORP),
             "Q4_K2_not_vacuous": max(p[("K2", "grain")]["supported"], p[("K2", "fixed")]["supported"]) >= 1}
        g["promote"] = all(g.values())
        g["verdict"] = "promote" if g["promote"] else ("inconclusive" if not g["Q4_K2_not_vacuous"] else "stay_opt_in")
        print("PARTS", json.dumps({f"{c}_{m}": v for (c, m), v in p.items()})); print("GATE", json.dumps(g))
        GATE_OUT.write_text(json.dumps({"schema": "KnobGrainPromotionV2", "parts": {f"{c}_{m}": v for (c, m), v in p.items()},
            "gate": g, "prereg": "docs/research/engine_substrate/SUBSTRATE_KNOB_GRAIN_PROMOTION_V2_PREREG_20261008.md"},
            indent=1, sort_keys=True) + "\n")
        return
    corpus, mode = sys.argv[1], sys.argv[2]
    out = part(corpus, mode)
    if out.exists(): raise SystemExit("refusing to overwrite")
    r = run_arm(corpus, mode); print("SUMMARY", json.dumps(r["summary"]), flush=True)
    r.update({"schema": "KnobGrainPromotionV2Part", "corpus_turns": CORP[corpus][0],
              "native_sha256": hashlib.sha256((ROOT / "runners/dsl/python/substrate_rs/_native.abi3.so").read_bytes()).hexdigest()})
    out.write_text(json.dumps(r, indent=1, sort_keys=True, default=str) + "\n")

main()

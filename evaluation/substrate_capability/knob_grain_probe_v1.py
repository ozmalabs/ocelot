#!/usr/bin/env python3
"""Tranche 10: grain-quantised knob steps on the real judge.
Two arms on separate agents, same corpus (list sentences whose
residual_marker_count takes {0,2,3,4,5}, measured beforehand -- disclosed):
  fixed: knob_edit.step_mode absent (the held 0.1 step)
  grain: knob_edit.step_mode = "grain"
Each arm hears the corpus, then files two reported concerns in sequence:
  1. "... list sentences too eagerly ..."  (decrease_fires)
  2. "... list sentences too rarely ..."   (increase_fires)
The agent's own pipeline authors each experiment, with retries opted in for
reported concerns. Real child replays (two independent boots), real judge.
n=1 per arm; feasibility, not an effect size."""
import hashlib, json, os, sys, tempfile, time
os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python"), str(ROOT / "tests"), str(ROOT / "scripts")]
OUT = ROOT / "evaluation/reports/knob_grain_probe_v1_20261008.json"
CORPUS = [(t, "statement") for t in (
    "The kit includes a hammer, a saw and a drill.", "The bag includes a map and a torch.",
    "The box includes a pen, a cup, a lamp and a book.", "The set includes a fork, a knife, a spoon, a plate and a bowl.",
    "The toolbox includes a hammer and a saw.", "The cat sat on the mat.", "The room had a bed.")]
CONCERNS = [("eager", "you reform list sentences too eagerly, test whether the residual marker threshold is too low"),
            ("rare", "you reform list sentences too rarely, test whether the residual marker threshold is too high")]


def run_arm(mode):
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
    budget = lambda: next(a.s.node(n)["attrs"].get("reform_residual_threshold") for n in a.s.nodes("ApertureBudget")
                          if a.s.node(n)["attrs"].get("register") == "conversational")
    runs = Path(tempfile.mkdtemp(prefix=f"kgp-{mode}-"))
    out = {"mode": mode, "concerns": []}
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
    return out


def main():
    if OUT.exists(): raise SystemExit("refusing to overwrite")
    arms = [run_arm(m) for m in ("fixed", "grain")]
    OUT.write_text(json.dumps({"schema": "KnobGrainProbeV1", "corpus": CORPUS, "arms": arms,
        "native_sha256": hashlib.sha256((ROOT / "runners/dsl/python/substrate_rs/_native.abi3.so").read_bytes()).hexdigest()},
        indent=1, sort_keys=True, default=str) + "\n")

main()

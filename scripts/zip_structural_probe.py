"""Side-channel probe (scratch, not committed to any seed): does the
property-reject-fallback pattern (one independent SynthEnumerate second
opinion, re-checked against the SAME structural detector) convert any of
the 5 ZipWith-blocked, retrieved_exemplar-sourced, structural_verdict_reject
tasks (261, 273, 282, 399, 429), now that ZipWith exists in the engine?

Method, mirroring PROGRAM_SYNTHESIS_STRUCTURAL_REJECT_SURVEY_PREREG.md
§3.2's own structural_probe.py exactly: run synthesize_from_request to its
real, natural terminal state on the UNCHANGED pipeline; then, on the SAME
goal node, apply the exact same four effects
ps_property_reject_retrieval_enumerate_fallback uses (ps_rung_enumerate :=
1.0, status := 'enumerate_pending', ps_enum_reserve_used += 1,
ps_st_computed := 0.0, ps_prop_computed := 0.0); call psy.pump() again on
the SAME substrate/goal; read back the final outcome."""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "runners/dsl/python"))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "scripts"))
os.environ["OZMA_NO_LLM"] = "1"
os.environ["OZMA_SEED_PERSIST_DISABLED"] = "1"

import substrate_rs as srs  # noqa: E402
import domains.prog_synthesis as psy  # noqa: E402
import domains.mbpp_spec as ms  # noqa: E402
import domains.prog_chunk_growth as pcg  # noqa: E402

import mbpp_endgame_battery as battery  # noqa: E402

TARGET_TASKS = [261, 273, 282, 399, 429]


def boot_full():
    s = srs.Substrate()
    ag = s.add_node("Agent", {})
    psy.ensure_program_synthesis(s, s._inner, ag)
    pcg.install_mined_chunks(s)
    pcg.ensure_mbpp_train_diet(s, s._inner, ag)
    return s, ag


def main():
    with open(battery.FIXTURE_PATH) as f:
        all_tasks = json.load(f)
    by_id = {t["task_id"]: t for t in all_tasks}

    results = []
    for tid in TARGET_TASKS:
        task = by_id[tid]
        parsed = ms.parse_asserts(task)
        rows = parsed["rows"]
        spec = ms.split_rows(rows, "primary")
        assert spec["runnable"], (tid, spec)

        s, ag = boot_full()
        r1 = psy.synthesize_from_request(s, ag, task["prompt"], spec["revealed"])
        row = {
            "task_id": tid,
            "before": {
                "status": r1.get("status"),
                "construction": r1.get("construction"),
                "gap_reason": r1.get("gap_reason"),
            },
        }
        g = r1.get("goal")
        if r1.get("status") != "gapped" or r1.get("gap_reason") != "structural_verdict_reject" \
                or r1.get("construction") != "retrieved_exemplar":
            row["eligible"] = False
            row["note"] = "does not match the expected pre-condition -- see 'before'"
            results.append(row)
            continue

        at = s.node(g)["attrs"]
        reserve_used = float(at.get("ps_enum_reserve_used") or 0.0)
        reserve_budget = float(at.get("ps_enum_reserve_budget") or 1.0)
        rung_enum = float(at.get("ps_rung_enumerate") or 0.0)
        row["eligible"] = (rung_enum != 1.0) and (reserve_used < reserve_budget)
        if not row["eligible"]:
            row["note"] = "reserve already spent or enumerate already tried"
            results.append(row)
            continue

        # Apply the exact 4 effects ps_property_reject_retrieval_enumerate_
        # fallback uses, mirrored for the structural case.
        s.set_attr(g, "ps_rung_enumerate", 1.0)
        s.set_attr(g, "status", "enumerate_pending")
        s.set_attr(g, "ps_enum_reserve_used", reserve_used + 1.0)
        s.set_attr(g, "ps_st_computed", 0.0)
        s.set_attr(g, "ps_prop_computed", 0.0)

        psy.pump(s, ag)
        r2 = psy.read_goal(s, g)
        at2 = s.node(g)["attrs"]
        row["after"] = {
            "status": r2.get("status"),
            "construction": r2.get("construction"),
            "gap_reason": r2.get("gap_reason"),
            "ir": r2.get("ir"),
            "ps_st_d1_fired": at2.get("ps_st_d1_fired"),
            "ps_st_d2_fired": at2.get("ps_st_d2_fired"),
            "ps_st_d3_fired": at2.get("ps_st_d3_fired"),
            "ps_st_fired_detectors": at2.get("ps_st_fired_detectors"),
            "ps_st_free_vars": at2.get("ps_st_free_vars"),
            "ps_st_varying_unread_params": at2.get("ps_st_varying_unread_params"),
        }
        if r2.get("status") == "accepted":
            hv = battery.holdout_verdict(r2["ir"], spec["held_out"])
            row["after"]["holdout_all_ok"] = hv["all_ok"]
            row["after"]["holdout"] = hv
        results.append(row)

    with open(os.path.join(ROOT, "results/zip_structural_probe.json"), "w") as f:
        json.dump(results, f, indent=1, default=str)
    for row in results:
        print(row["task_id"], "eligible=", row.get("eligible"),
              "before=", row["before"],
              "after=", row.get("after"))


if __name__ == "__main__":
    main()

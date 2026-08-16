"""Per-task diagnostic sweep over every non-passing runnable MBPP `full`-arm
task, mirroring PROGRAM_SYNTHESIS_CEILING_REASSESSMENT_2_PREREG.md's own
methodology (direct domains.prog_synthesis.synthesize_from_request call per
task, full read_goal() dict, same boot_full() as the battery)."""
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
from domains import engineering_residual_ingest as eri  # noqa: E402


def ingest_engineering_residuals(out: list) -> dict:
    """PROPOSAL 3 (measured-residual filing, DESIGN_REVIEW_CAPABILITY_
    EXPANSION_PREREG.md sec4): `out`'s rows already carry `task_id`/
    `outcome` -- the exact two fields `battery.taxonomy()` reads -- so it
    is reused verbatim (no new grouping logic) to build the "N tasks in
    bucket X" dict, then mechanically ingested as EngineeringResidual fact
    nodes on the same dedicated, persisted substrate the battery uses (a
    DIFFERENT source_script identity, 'ceiling3_diag_sweep', so the two
    scripts' populations never collide). No interpretation happens here."""
    tax = battery.taxonomy(out, [])
    s, agent = eri.load_or_boot_residual_substrate()
    result = eri.ingest_taxonomy(s, agent, source_script="ceiling3_diag_sweep",
                                 taxonomy=tax)
    eri.save_residual_substrate(s, agent)
    print("ingested engineering residuals:", len(result["upserted"]), "populations",
          "->", eri.DEFAULT_CHECKPOINT)
    return result


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
    splits = battery.q0_split_tasks(all_tasks)
    tasks = splits["test"]
    out = []
    endgame = json.load(open(os.path.join(ROOT, "results/mbpp_endgame.json")))
    pass_ids = {r["task_id"] for r in endgame["arms"]["full"]["runnable_rows"]
                if r["outcome"] == "pass"}
    n = 0
    for task in tasks:
        tid = task["task_id"]
        if tid in pass_ids:
            continue
        parsed = ms.parse_asserts(task)
        rows = parsed["rows"]
        spec = ms.split_rows(rows, "primary")
        if not spec["runnable"]:
            out.append({"task_id": tid, "prompt": task["prompt"],
                        "outcome": "excluded:%s" % spec.get("excluded_reason")})
            continue
        try:
            s, ag = boot_full()
            r = psy.synthesize_from_request(s, ag, task["prompt"], spec["revealed"])
        except Exception as e:
            out.append({"task_id": tid, "prompt": task["prompt"],
                        "outcome": "runner_exception:%s" % type(e).__name__,
                        "failure_reason": str(e)[:300]})
            n += 1
            continue
        if r.get("status") is None:
            out.append({"task_id": tid, "prompt": task["prompt"], "outcome": "not_recognized"})
            n += 1
            continue
        goal = r  # already read_goal() output (synthesize_from_request returns it)
        row = {
            "task_id": tid, "prompt": task["prompt"],
            "status": goal.get("status"),
            "construction": goal.get("construction"),
            "gap_reason": goal.get("gap_reason"),
            "enumerate_outcome": goal.get("enumerate_outcome"),
            "cover_parts": goal.get("cover_parts"),
            "residual_tokens": goal.get("residual_tokens"),
            "enumerate": goal.get("enumerate"),
            "retrieval": goal.get("retrieval"),
        }
        if goal.get("status") == "accepted":
            try:
                hv = battery.holdout_verdict(goal["ir"], spec["held_out"])
                row["outcome"] = "pass" if hv["all_ok"] else "accepted_holdout_fail"
                row["holdout"] = hv
            except Exception as e:
                row["outcome"] = "runner_exception:%s" % type(e).__name__
                row["failure_reason"] = str(e)[:300]
        elif goal.get("status") == "gapped":
            row["outcome"] = "gapped:%s" % (goal.get("gap_reason") or "unnamed")
        else:
            row["outcome"] = "stalled:%s" % goal.get("status")
        out.append(row)
        n += 1
        if n % 20 == 0:
            print("...", n, file=sys.stderr)

    with open(os.path.join(ROOT, "results/ceiling3_diag_sweep.json"), "w") as f:
        json.dump(out, f, indent=1, default=str)
    print("wrote", len(out), "rows")

    ingest_engineering_residuals(out)


if __name__ == "__main__":
    main()

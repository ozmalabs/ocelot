#!/usr/bin/env python
"""pbe_string_battery -- the honest PBE (Programming-by-Example) STRING
BENCHMARK, `SynthEnumerate` measured DIRECTLY on a genuinely new corpus.

Companion prereg/results:
  docs/research/program_synthesis/PBE_STRING_BENCHMARK_PREREG.md
  docs/research/program_synthesis/PBE_STRING_BENCHMARK_RESULTS.md

WHY THIS EXISTS (see the prereg for the full argument): the MBPP arc's
single most consequential finding was a fix to `SynthEnumerate`'s own
Occam/MDL search-ordering metric (`literal_witness_cost`,
`runners/dsl/src/synth_enumerate.rs`) -- literals are now priced by
description-length-given-witnesses instead of a uniform leaf cost, so a
memorized 2-row lookup no longer automatically beats a genuine
composition in search order. That fix's own design doc claims it
generalizes to "every future few-shot synthesis task -- MBPP or not."
This battery is the FIRST test of that claim on a task shape that is
DELIBERATELY unlike MBPP: raw input->output STRING pairs, no natural-
language prompt at all (the classic FlashFill/PBE framing, Gulwani 2011)
-- so there is nothing for a retrieval/exemplar layer to lean on and the
entire burden of finding the true transformation falls on the Occam-
ordered search itself.

WHAT THIS SCRIPT DOES NOT DO (by design, matching the task brief):
  - No `domains.prog_synthesis.synthesize_from_request` pipeline call.
  - No retrieval ladder, no NL comprehension, no
    `ps_select_synthesis_operator_shape`, no codebook/chunk machinery.
  - No `prompt` field anywhere in the fixture or this script -- the
    corpus is genuinely prompt-free, matching the honest PBE framing.
  - `SynthEnumerate` is called DIRECTLY (`sub._inner.evaluate(SYNTH(...), {})`),
    exactly the call shape `tests/test_synth_enumerate_migrated.py` uses,
    reused here rather than reinvented.

TWO ARMS, both run on the UNMODIFIED, CURRENT engine (this rung makes no
Rust changes -- see the prereg for why):
  typed_default -- `ops=None, consts=None`. The engine's OWN typed
    default (`DEFAULT_STR_OPS` for a pure string-in/string-out spec) with
    ZERO caller hints beyond the raw example rows -- the strictest,
    most honest test of what this corpus's own design doc's claim
    promises: the search alone, no declared DSL.
  declared -- `ops=PBE_OPS, consts=PBE_CONSTS`, a SINGLE FIXED op/const
    inventory applied UNIFORMLY to every task (never tuned per task --
    that would leak the answer). This is the standard PBE-tool
    convention (a caller declares its DSL once, up front) and is the
    only way to reach compositions that need `First`/`LastElem` (word-
    level tasks) or slice bounds like 3/4/-4/999 that the engine's own
    auto-derived default consts ({0,1,2,-1} + spec-observed strings/
    chars only) would never surface for a pure string spec.

A task FAILING at `max_size=15, max_candidates=0` (engine default
200,000) is re-probed once at a HIGHER budget (`max_size=20,
max_candidates=2,000,000` -- the exact CEILING_REASSESSMENT_7 probe
budget) ONLY in the `declared` arm, to separate "genuinely unreachable
with this op/const inventory" from "a search-cost wall the default
budget doesn't clear" -- the same distinction Gate (3) of
MDL_OCCAM_WITNESS_PRICING_RESULTS.md drew for MBPP tasks 102/411.

Run:
  PYTHONPATH=runners/dsl/python:.:scripts OZMA_NO_LLM=1 \
  OZMA_SEED_PERSIST_DISABLED=1 python scripts/pbe_string_battery.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from typing import Any, Dict, List, Optional

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"),
           os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

os.environ.setdefault("OZMA_NO_LLM", "1")
os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")

import substrate_rs as srs  # noqa: E402

from domains.prog_synthesis import _wire_rows  # noqa: E402 -- the shipped write side of
                                                # the engine's tagged Value wire form,
                                                # reused verbatim (test_synth_enumerate_
                                                # migrated.py's own `rows()` precedent).

FIXTURE_PATH = os.path.join(ROOT, "tests", "fixtures", "pbe_string",
                            "pbe_string_tasks.json")
OUT_PATH = os.path.join(ROOT, "results", "pbe_string_battery.json")

# ---------------------------------------------------------------------------
# The SINGLE fixed op/const inventory for the `declared` arm -- applied
# UNIFORMLY to every task, never tuned per task. `DEFAULT_STR_OPS` (the
# engine's own typed default for a string spec, synth_enumerate.rs:666-670)
# plus `First`/`LastElem` (needed for word-level tasks: OP_TABLE has both,
# but neither is in DEFAULT_STR_OPS -- both are ordinary LIST_EXTRA_OPS
# entries the caller must name explicitly for a string-shaped spec).
# ---------------------------------------------------------------------------
PBE_OPS = [
    "Concat", "CaseFold", "Eq", "IfThenElse",
    "Replace", "Split", "StrCount", "Capitalize", "Reverse", "Slice", "Str",
    "MapList", "JoinList",
    "First", "LastElem",
]

# Fixed, uniform constant pool -- a superset of the engine's own default
# ({0,1,2,-1}) plus: 3/4 and -2/-3/-4 (slice bounds several tasks need),
# 999 (a right-open-slice "to end" sentinel -- Slice's own `slice_indices`
# clamps an over-large stop to the sequence length, confirmed by reading
# `runners/dsl/src/prog_eval.rs::slice_indices`), and "" (Split's own
# documented whitespace-split trigger when `sep` is empty).
PBE_CONSTS = [0, 1, 2, 3, 4, -1, -2, -3, -4, 999, ""]

DEFAULT_BUDGET = {"max_size": 15, "max_candidates": 0}
HIGH_BUDGET = {"max_size": 20, "max_candidates": 2_000_000}


# ---------------------------------------------------------------------------
# SynthEnumerate call shape -- mirrors tests/test_synth_enumerate_migrated.py
# `SYNTH`/`rows` verbatim (the harness-pattern precedent this script is
# instructed to reuse, not reinvent).
# ---------------------------------------------------------------------------
def SYNTH(examples, ops=None, consts=None, exclude=None, max_size=0,
          max_candidates=0, saturate_k=0, field="") -> Dict[str, Any]:
    return {
        "type": "SynthEnumerate",
        "examples": {"type": "Lit", "value": examples},
        "ops": {"type": "Lit", "value": list(ops)} if ops is not None else None,
        "consts": {"type": "Lit", "value": list(consts)} if consts is not None else None,
        "exclude": {"type": "Lit", "value": list(exclude)} if exclude is not None else None,
        "max_size": max_size,
        "max_candidates": max_candidates,
        "saturate_k": saturate_k,
        "field": field,
    }


def wire_examples(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return _wire_rows([{"inputs": dict(r["inputs"]), "output": r["output"]} for r in rows])


def holdout_check(sub, term: Dict[str, Any], held_out: List[Dict[str, Any]]) -> Dict[str, Any]:
    rows = []
    n_ok = 0
    for hr in held_out:
        try:
            got = sub._inner.evaluate(term, dict(hr["inputs"]))
            ok = got == hr["output"]
        except Exception as e:  # noqa: BLE001 -- never let one row crash the batch
            got = None
            ok = False
            rows.append({"inputs": hr["inputs"], "expected": hr["output"],
                        "got": None, "ok": False,
                        "eval_exception": type(e).__name__})
            continue
        n_ok += 1 if ok else 0
        rows.append({"inputs": hr["inputs"], "expected": hr["output"],
                    "got": got, "ok": bool(ok)})
    return {"n": len(rows), "n_ok": n_ok, "all_ok": n_ok == len(rows), "rows": rows}


def run_one(task: Dict[str, Any], ops: Optional[List[str]], consts: Optional[List[Any]],
           budget: Dict[str, int]) -> Dict[str, Any]:
    sub = srs.Substrate()
    examples = wire_examples(task["revealed"])
    spec = SYNTH(examples, ops=ops, consts=consts, saturate_k=0,
                max_size=budget["max_size"], max_candidates=budget["max_candidates"])
    t0 = time.time()
    out = sub._inner.evaluate(spec, {})
    elapsed = time.time() - t0
    row: Dict[str, Any] = {
        "task_id": task["task_id"], "name": task["name"], "tier": task["tier"],
        "budget": budget, "found": bool(out.get("found")),
        "halt_reason": out.get("halt_reason"), "size": out.get("size"),
        "tested": out.get("tested"), "distinct": out.get("distinct"),
        "term_str": out.get("term_str"), "elapsed_seconds": round(elapsed, 3),
    }
    if not out.get("found"):
        row["outcome"] = "not_found:%s" % out.get("halt_reason")
        row["holdout"] = None
        return row
    term = json.loads(out["term"])
    row["term_json"] = term
    hv = holdout_check(sub, term, task["held_out"])
    row["holdout"] = hv
    row["outcome"] = "pass" if hv["all_ok"] else "found_but_holdout_fail"
    return row


def run_arm(tasks: List[Dict[str, Any]], arm_name: str, ops, consts,
           budget: Dict[str, int]) -> List[Dict[str, Any]]:
    out = []
    for task in tasks:
        row = run_one(task, ops, consts, budget)
        row["arm"] = arm_name
        out.append(row)
        print("  [%s/%s] %s (%s): %s" % (
            arm_name, budget["max_size"], task["task_id"], task["tier"], row["outcome"]))
    return out


def escalate_failures(tasks_by_id: Dict[str, Dict[str, Any]],
                      declared_default_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Re-probe every DECLARED-arm failure at HIGH_BUDGET -- the
    CEILING_REASSESSMENT_7 precedent for separating a search-cost wall
    from a genuinely unreachable composition."""
    out = []
    for r in declared_default_rows:
        if r["outcome"] == "pass":
            continue
        task = tasks_by_id[r["task_id"]]
        row = run_one(task, PBE_OPS, PBE_CONSTS, HIGH_BUDGET)
        row["arm"] = "declared_high_budget"
        out.append(row)
        print("  [declared_high_budget] %s (%s): %s" % (
            task["task_id"], task["tier"], row["outcome"]))
    return out


def taxonomy(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    by: Dict[str, Dict[str, Any]] = {}
    for r in rows:
        e = by.setdefault(r["outcome"], {"n": 0, "task_ids": []})
        e["n"] += 1
        e["task_ids"].append(r["task_id"])
    for e in by.values():
        e["task_ids"].sort()
    return dict(sorted(by.items(), key=lambda kv: -kv[1]["n"]))


def pass_task_ids(rows: List[Dict[str, Any]]) -> List[str]:
    return sorted(r["task_id"] for r in rows if r["outcome"] == "pass")


def set_diff(before_ids: List[str], after_ids: List[str]) -> Dict[str, List[str]]:
    b, a = set(before_ids), set(after_ids)
    return {"lost": sorted(b - a), "gained": sorted(a - b)}


def main() -> None:
    t_start = time.time()
    with open(FIXTURE_PATH) as f:
        tasks = json.load(f)
    tasks_by_id = {t["task_id"]: t for t in tasks}
    print("== loaded", len(tasks), "PBE string tasks from", FIXTURE_PATH)

    print("== ARM typed_default (ops=None, consts=None) ==")
    typed_default_rows = run_arm(tasks, "typed_default", None, None, DEFAULT_BUDGET)

    print("== ARM declared (fixed PBE_OPS/PBE_CONSTS) ==")
    declared_rows = run_arm(tasks, "declared", PBE_OPS, PBE_CONSTS, DEFAULT_BUDGET)

    print("== escalating declared-arm failures to HIGH_BUDGET ==")
    high_budget_rows = escalate_failures(tasks_by_id, declared_rows)

    td_pass = pass_task_ids(typed_default_rows)
    de_pass = pass_task_ids(declared_rows)
    hb_pass = pass_task_ids(high_budget_rows)
    de_plus_hb_pass = sorted(set(de_pass) | set(hb_pass))

    diff_declared_over_typed = set_diff(td_pass, de_pass)
    diff_highbudget_over_declared = set_diff(de_pass, de_plus_hb_pass)

    head = ""
    try:
        head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                              capture_output=True, text=True,
                              timeout=10).stdout.strip()
    except Exception:  # noqa: BLE001
        pass
    so = os.path.join(ROOT, "runners", "dsl", "python", "substrate_rs",
                      "_native.abi3.so")

    artifact = {
        "_README": (
            "PBE string-transformation battery -- SynthEnumerate called "
            "DIRECTLY (no MBPP pipeline, no NL prompt anywhere) on a "
            "genuinely new, hand-built 26-task corpus. Two arms at "
            "DEFAULT_BUDGET (max_size=15, max_candidates=200000): "
            "typed_default (ops=None/consts=None, the engine's own typed "
            "default, zero caller hints) and declared (a single FIXED "
            "op/const inventory, PBE_OPS/PBE_CONSTS, applied uniformly to "
            "every task). Every declared-arm failure is re-probed once at "
            "HIGH_BUDGET (max_size=20, max_candidates=2000000, the "
            "CEILING_REASSESSMENT_7 probe budget)."),
        "head": head,
        "measured_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "engine": {"so": os.path.relpath(so, ROOT),
                   "mtime": time.strftime(
                       "%Y-%m-%dT%H:%M:%S",
                       time.localtime(os.path.getmtime(so)))
                   if os.path.exists(so) else None},
        "fixture": os.path.relpath(FIXTURE_PATH, ROOT),
        "n_tasks": len(tasks),
        "pbe_ops": PBE_OPS,
        "pbe_consts": PBE_CONSTS,
        "budgets": {"default": DEFAULT_BUDGET, "high": HIGH_BUDGET},
        "arms": {
            "typed_default": {
                "rows": typed_default_rows,
                "n_pass": len(td_pass), "n_total": len(tasks),
                "pass_task_ids": td_pass,
                "outcome_taxonomy": taxonomy(typed_default_rows),
            },
            "declared": {
                "rows": declared_rows,
                "n_pass": len(de_pass), "n_total": len(tasks),
                "pass_task_ids": de_pass,
                "outcome_taxonomy": taxonomy(declared_rows),
            },
            "declared_high_budget_escalation": {
                "rows": high_budget_rows,
                "n_reprobed": len(high_budget_rows),
                "n_newly_pass": len(hb_pass),
                "newly_pass_task_ids": hb_pass,
                "outcome_taxonomy": taxonomy(high_budget_rows),
            },
        },
        "diff_declared_minus_typed_default": diff_declared_over_typed,
        "diff_high_budget_minus_declared_default": diff_highbudget_over_declared,
        "declared_plus_high_budget_pass_task_ids": de_plus_hb_pass,
        "elapsed_seconds": round(time.time() - t_start, 2),
    }
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w") as f:
        json.dump(artifact, f, indent=1, sort_keys=False)
        f.write("\n")
    print("wrote", OUT_PATH)
    print("typed_default: %d/%d" % (len(td_pass), len(tasks)))
    print("declared:      %d/%d" % (len(de_pass), len(tasks)))
    print("declared+high: %d/%d" % (len(de_plus_hb_pass), len(tasks)))
    print("diff declared-typed_default:", diff_declared_over_typed)
    print("diff high_budget-declared:", diff_highbudget_over_declared)
    print("elapsed: %.1fs" % artifact["elapsed_seconds"])


if __name__ == "__main__":
    main()

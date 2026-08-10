#!/usr/bin/env python
"""mbpp_arc3_battery — Arc 3 R3: the POWERED MBPP ENDGAME for the
retrieval-shaped-proposal arc (HR1/HR2/HR3).

Companion docs: `PROGRAM_SYNTHESIS_ARC3_PREREG.md` (HR1/HR2/HR3, the bars
this phase judges against), `PROGRAM_SYNTHESIS_ARC3_R0_NOTES.md` (the
12-task honest oracle ceiling), `PROGRAM_SYNTHESIS_ARC3_R12_NOTES.md` (R1/R2
landing + the R2.5 scoped codebook-side screen), `PROGRAM_SYNTHESIS_ARC2_Q5.md`
/ `results/mbpp_endgame.json` (the arc-2 FULL arm — the paired continuity
comparison for the migration matrix and HR2's Q5 baseline),
`scripts/mbpp_endgame_battery.py` (the driver pattern this script reuses:
wilson/newcombe stats, the run_task/run_pass/run_arm shape, the twin-run
determinism discipline).

This is a MEASUREMENT DRIVER exactly like its Arc-2 predecessor: it boots
agents, feeds the MBPP **test** split (257 tasks) through the UNCHANGED
`domains.prog_synthesis.synthesize_from_request` pipeline, reads outcomes
back, and writes the artifact. No synthesis/engine/seed/spec code is
touched by this phase.

ARMS (PRIMARY protocol except OFFICIAL-R3, protocol-distinct):

  full_r3        the committed stack as of seed v1.5.1 (retrieval + the
                 scoped codebook-side screen + descent/repair/exclude +
                 the arc-1 corpus chunks + the Q3 mbpp_train diet) — THE
                 arc number.
  no_retrieval   THE SAME boot as full_r3 (screen ON, chunks/diet installed
                 — the delta must isolate retrieval, not the screen), but
                 the retrieval lane disabled at its cleanest seam: a
                 `Seed{id:"mbpp_exemplars"}` marker node is pre-added to
                 the substrate BEFORE `ensure_program_synthesis` runs, so
                 `prog_retrieval.ensure_exemplar_store`'s own idempotent
                 `_has_seed` guard treats the store as "already installed"
                 and never loads a single Exemplar node. Zero Exemplar
                 nodes means `score_exemplars` boards zero ScoreLinks,
                 `pr_select_candidate` never fires, `run_retrieval_ladder`
                 sees an empty candidate pool and immediately records
                 `pr_rung_reached:"none"` — every request falls through to
                 `pending` (the SAME codebook/lattice/descend/enumerate
                 stack `full_r3` uses, screen fully live) with the
                 retrieval lane a true, verified no-op. No seed/engine/
                 rule code is touched to achieve this — it is purely a
                 boot-sequence choice in THIS measurement script (confirmed
                 live: `n Exemplar nodes: 0` after this boot, verified in
                 `tests/test_mbpp_arc3_endgame_migrated.py`).
  official_r3    the full_r3 boot, OFFICIAL protocol (every parseable
                 assert revealed, scored on the same asserts) — the
                 comparability row, protocol-flagged, never merged into a
                 PRIMARY aggregate.

CONTAMINATION: unchanged from `mbpp_endgame_battery.py` — `task["code"]` is
stripped at split time (`mbpp_zero_shot_baseline.split_tasks`, imported
verbatim), `mbpp_spec.parse_asserts`/`split_rows` never read it, every
substrate is a fresh, `OZMA_SEED_PERSIST_DISABLED` boot, no `domains.teach.
teach` call anywhere in this file.

Run:
  PYTHONPATH=runners/dsl/python:.:scripts OZMA_NO_LLM=1 \
  OZMA_SEED_PERSIST_DISABLED=1 python scripts/mbpp_arc3_battery.py
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import platform
import subprocess
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"),
           os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

os.environ.setdefault("OZMA_NO_LLM", "1")
os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")

import substrate_rs as srs  # noqa: E402

from domains import prog_synthesis as psy  # noqa: E402
from domains import prog_chunk_growth as pcg  # noqa: E402
from domains import mbpp_spec as ms  # noqa: E402
from domains.prog_ir_emit import NATIVE_ORACLES  # noqa: E402

from mbpp_zero_shot_baseline import split_tasks as q0_split_tasks  # noqa: E402

FIXTURE_PATH = os.path.join(ROOT, "tests", "fixtures", "mbpp",
                            "sanitized-mbpp.json")
PROVENANCE_PATH = os.path.join(ROOT, "tests", "fixtures", "mbpp",
                               "provenance.json")
Q0_BASELINE_PATH = os.path.join(ROOT, "results", "mbpp_zero_shot_baseline.json")
ARC2_ENDGAME_PATH = os.path.join(ROOT, "results", "mbpp_endgame.json")
R0_CEILING_PATH = os.path.join(ROOT, "results", "retrieval_oracle_ceiling.json")
OUT_PATH = os.path.join(ROOT, "results", "mbpp_arc3_endgame.json")

_Z = 1.959963984540054  # 95%
MIN_PREFIX = 150
TIME_BUDGET_SECONDS = 25 * 60
N_SANITIZED_TOTAL = 427
_EXEMPLAR_SEED_ID = "mbpp_exemplars"


# --------------------------------------------------------------------------- #
#  statistics (self-contained copy — the mbpp_endgame_battery precedent:
#  this file owns its own stats even where it reuses other modules'
#  mechanisms verbatim elsewhere).
# --------------------------------------------------------------------------- #
def wilson(k: int, n: int) -> Dict[str, Any]:
    if n == 0:
        return {"k": 0, "n": 0, "p": None, "ci95": [None, None]}
    p = k / n
    d = 1 + _Z * _Z / n
    centre = (p + _Z * _Z / (2 * n)) / d
    hw = _Z * math.sqrt(p * (1 - p) / n + _Z * _Z / (4 * n * n)) / d
    return {"k": k, "n": n, "p": round(p, 6),
            "ci95": [round(max(0.0, centre - hw), 6),
                     round(min(1.0, centre + hw), 6)]}


def newcombe_delta(k1: int, n1: int, k2: int, n2: int) -> Dict[str, Any]:
    """Newcombe hybrid score interval for p1 - p2 (Wilson bounds per arm)."""
    w1, w2 = wilson(k1, n1), wilson(k2, n2)
    p1, p2 = k1 / n1, k2 / n2
    d = p1 - p2
    lo = d - math.sqrt((p1 - w1["ci95"][0]) ** 2 + (w2["ci95"][1] - p2) ** 2)
    hi = d + math.sqrt((w1["ci95"][1] - p1) ** 2 + (p2 - w2["ci95"][0]) ** 2)
    step = 1.0 / n1
    ci_sep = lo > 0 or hi < 0
    above = abs(d) > 3 * step
    verdict = ("ci_separated_gain" if ci_sep and d > 0 else
               "ci_separated_loss" if ci_sep else
               ("inside_ci_above_3x_step" if above else "within_noise")
               + "_no_measured_gain")
    return {"delta": round(d, 6), "ci95": [round(lo, 6), round(hi, 6)],
            "per_episode_step": round(step, 6),
            "three_x_step": round(3 * step, 6), "verdict": verdict}


def _json_default(o: Any) -> Any:
    if isinstance(o, (set, frozenset)):
        try:
            return sorted(o)
        except TypeError:
            return list(o)
    if isinstance(o, tuple):
        return list(o)
    raise TypeError("not JSON serializable: %r" % type(o))


# --------------------------------------------------------------------------- #
#  boot — the three arms.
# --------------------------------------------------------------------------- #
def boot_full_r3():
    """FULL-R3: the committed stack as of seed v1.5.1 (retrieval ladder +
    the scoped codebook-side screen + descent/repair/exclude) + the arc-1
    corpus chunks + the Q3 mbpp_train diet. Byte-identical boot sequence to
    Arc-2 Q5's `boot_full` — the only thing that changed since then is what
    `ensure_program_synthesis` itself installs (it now additively boards
    the exemplar store, seed v1.5.0+)."""
    s = srs.Substrate()
    ag = s.add_node("Agent", {})
    psy.ensure_program_synthesis(s, s._inner, ag)
    pcg.install_mined_chunks(s)
    pcg.ensure_mbpp_train_diet(s, s._inner, ag)
    return s, ag


def boot_no_retrieval():
    """NO-RETRIEVAL: THE SAME boot as full_r3 (screen ON, same chunks/diet)
    with the retrieval lane disabled at its cleanest seam — see the module
    docstring. A `Seed{id:"mbpp_exemplars"}` marker is pre-added so
    `prog_retrieval.ensure_exemplar_store`'s own idempotent guard treats
    the store as already installed and boards zero Exemplar nodes. No
    seed/engine/rule file is touched; this is a boot-order choice local to
    this measurement script."""
    s = srs.Substrate()
    ag = s.add_node("Agent", {})
    s.add_node("Seed", {"id": _EXEMPLAR_SEED_ID, "version": "1.0.0"})
    psy.ensure_program_synthesis(s, s._inner, ag)
    assert not list(s.nodes("Exemplar")), \
        "OFF-switch failed: Exemplar nodes present in the NO-RETRIEVAL boot"
    pcg.install_mined_chunks(s)
    pcg.ensure_mbpp_train_diet(s, s._inner, ag)
    return s, ag


ARM_BOOT = {"full_r3": boot_full_r3, "no_retrieval": boot_no_retrieval,
            "official_r3": boot_full_r3}
ARM_PROTOCOL = {"full_r3": "primary", "no_retrieval": "primary",
                "official_r3": "official"}


# --------------------------------------------------------------------------- #
#  verdict — ProgEval on a fresh throwaway substrate (the Q5 pattern,
#  reused verbatim).
# --------------------------------------------------------------------------- #
def _oracles_term() -> Dict[str, Any]:
    items = []
    for name in sorted(NATIVE_ORACLES):
        items.append({"type": "Lit", "value": name})
        items.append({"type": "Lit", "value": "builtin"})
    return {"type": "MkDict", "items": items}


def prog_eval(ir: Dict[str, Any], env: Dict[str, Any]) -> Dict[str, Any]:
    s = srs.Substrate()
    return s._inner.evaluate(
        {"type": "ProgEval", "prog": ir, "env": {"type": "Var", "name": "e"},
         "oracles": _oracles_term(), "fuel": psy._FUEL, "field": ""},
        {"e": env})


def _norm(v):
    if isinstance(v, (list, tuple)):
        return [_norm(x) for x in v]
    if isinstance(v, dict):
        return {k: _norm(x) for k, x in v.items()}
    return v


def agree(got, expected, tol=None, unordered=False) -> bool:
    if tol is not None or unordered:
        return bool(psy._row_cmp_ok(got, expected, tol, unordered))
    if isinstance(expected, bool) or isinstance(got, bool):
        return isinstance(got, bool) and isinstance(expected, bool) and got == expected
    if isinstance(got, (int, float)) and isinstance(expected, (int, float)):
        return float(got) == float(expected)
    return _norm(got) == _norm(expected)


def holdout_verdict(ir: Dict[str, Any], held_out_rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    rows = []
    n_ok = 0
    for hr in held_out_rows:
        tol = hr.get("tol")
        unordered = bool(hr.get("unordered"))
        try:
            out = prog_eval(ir, dict(hr["inputs"]))
            got = out.get("result")
            ok = (out.get("halted") is True and out.get("trap") is None
                  and agree(got, hr["expected"], tol, unordered))
        except Exception as e:  # noqa: BLE001
            rows.append({"inputs": hr["inputs"], "expected": hr["expected"],
                        "got": None, "trap": "eval_exception:%s" % type(e).__name__,
                        "ok": False})
            continue
        n_ok += 1 if ok else 0
        rows.append({"inputs": hr["inputs"], "expected": hr["expected"],
                    "got": got if isinstance(got, (int, float, str, bool)) else None,
                    "trap": out.get("trap"), "ok": bool(ok)})
    return {"n": len(rows), "n_ok": n_ok, "all_ok": n_ok == len(rows), "rows": rows}


# --------------------------------------------------------------------------- #
#  per-task run.
# --------------------------------------------------------------------------- #
def excluded_outcome(spec: Dict[str, Any]) -> str:
    reason = spec.get("excluded_reason")
    if reason == "no_parseable_rows":
        return "assert_unparseable"
    return "protocol_excluded:%s" % reason


def run_task(task: Dict[str, Any], spec: Dict[str, Any], report: Dict[str, Any],
            boot_fn, protocol: str) -> Dict[str, Any]:
    row: Dict[str, Any] = {
        "task_id": task["task_id"],
        "source_file": task.get("source_file"),
        "prompt": task["prompt"],
        "protocol": protocol,
        "n_revealed": len(spec["revealed"]),
        "n_held_out": len(spec["held_out"]),
        **report,
    }
    if spec.get("protocol_distinct"):
        row["protocol_distinct"] = True
    try:
        s, ag = boot_fn()
        r = psy.synthesize_from_request(s, ag, task["prompt"], spec["revealed"])
    except Exception as e:  # noqa: BLE001
        row.update({"recognized": None, "status": None, "construction": None,
                    "attempts": None, "rungs": None, "gap_reason": None,
                    "enumerate_outcome": None, "n_counterexamples": 0,
                    "excluded": [], "retrieval": None, "screen": None,
                    "outcome": "runner_exception:%s" % type(e).__name__,
                    "failure_reason": str(e)[:300]})
        return row

    row.update({
        "recognized": r.get("status") is not None,
        "status": r.get("status"),
        "construction": r.get("construction"),
        "attempts": r.get("attempts"),
        "rungs": r.get("rungs"),
        "gap_reason": r.get("gap_reason"),
        "enumerate_outcome": r.get("enumerate_outcome"),
        "n_counterexamples": len(r.get("counterexamples") or []),
        "excluded": r.get("excluded") or [],
        "retrieval": r.get("retrieval"),
        "screen": r.get("screen"),
    })
    if r.get("status") is None:
        row["outcome"] = "not_recognized"
        row["failure_reason"] = "request_not_recognized"
        return row
    if r["status"] == "accepted":
        try:
            hv = holdout_verdict(r["ir"], spec["held_out"])
        except Exception as e:  # noqa: BLE001
            row["outcome"] = "runner_exception:%s" % type(e).__name__
            row["failure_reason"] = str(e)[:300]
            return row
        row["holdout"] = hv
        row["ir"] = r["ir"]
        if hv["all_ok"]:
            row["outcome"] = "pass"
            row["failure_reason"] = None
        else:
            row["outcome"] = "accepted_holdout_fail"
            row["failure_reason"] = "holdout_disagreement"
    elif r["status"] == "gapped":
        row["outcome"] = "gapped:%s" % (r.get("gap_reason") or "unnamed")
        row["failure_reason"] = r.get("gap_reason") or "gapped"
    else:
        row["outcome"] = "stalled:%s" % r["status"]
        row["failure_reason"] = "pipeline_stall_nonterminal_status"
    return row


def run_pass(test_tasks: List[Dict[str, Any]], boot_fn, protocol: str,
            *, prefix_n: Optional[int] = None
            ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], float]:
    t0 = time.time()
    tasks = test_tasks if prefix_n is None else test_tasks[:prefix_n]
    runnable: List[Dict[str, Any]] = []
    excluded: List[Dict[str, Any]] = []
    for task in tasks:
        parsed = ms.parse_asserts(task)
        rows = parsed["rows"]
        report = {
            "n_test_list": len(task.get("test_list", [])),
            "n_parseable": len(rows),
            "n_unparseable": len(parsed["unparseable"]),
            "unparseable_reasons": [u["form"] for u in parsed["unparseable"]],
        }
        spec = ms.split_rows(rows, protocol)
        if not spec["runnable"]:
            excluded.append({
                "task_id": task["task_id"], "source_file": task.get("source_file"),
                "prompt": task["prompt"], "protocol": protocol,
                "outcome": excluded_outcome(spec), **report,
            })
            continue
        runnable.append(run_task(task, spec, report, boot_fn, protocol))
    return runnable, excluded, time.time() - t0


def outcome_signature(runnable_rows: List[Dict[str, Any]],
                      excluded_rows: List[Dict[str, Any]]) -> List[Any]:
    sig = [[r["task_id"], r["outcome"], r["status"], r["construction"],
           r["attempts"], r["gap_reason"],
           (r.get("retrieval") or {}).get("rung_reached")] for r in runnable_rows]
    sig += [[r["task_id"], r["outcome"], r["n_parseable"]] for r in excluded_rows]
    sig.sort(key=lambda x: x[0])
    return sig


def sig_hash(sig: List[Any]) -> str:
    return hashlib.sha256(
        json.dumps(sig, sort_keys=True, default=_json_default).encode()
    ).hexdigest()


def taxonomy(runnable_rows: List[Dict[str, Any]],
            excluded_rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    by: Dict[str, Dict[str, Any]] = {}
    for r in runnable_rows:
        e = by.setdefault(r["outcome"], {"n": 0, "task_ids": []})
        e["n"] += 1
        e["task_ids"].append(r["task_id"])
    for r in excluded_rows:
        e = by.setdefault(r["outcome"], {"n": 0, "task_ids": []})
        e["n"] += 1
        e["task_ids"].append(r["task_id"])
    return dict(sorted(by.items(), key=lambda kv: -kv[1]["n"]))


def run_arm(arm_name: str, test_tasks: List[Dict[str, Any]],
           *, prefix_n: Optional[int] = None) -> Dict[str, Any]:
    boot_fn = ARM_BOOT[arm_name]
    protocol = ARM_PROTOCOL[arm_name]
    run1_r, run1_x, t1 = run_pass(test_tasks, boot_fn, protocol, prefix_n=prefix_n)
    run2_r, run2_x, t2 = run_pass(test_tasks, boot_fn, protocol, prefix_n=prefix_n)
    sig1 = outcome_signature(run1_r, run1_x)
    sig2 = outcome_signature(run2_r, run2_x)
    determinism = {
        "runs": 2, "identical": sig1 == sig2,
        "outcome_hash_run1": sig_hash(sig1), "outcome_hash_run2": sig_hash(sig2),
        "elapsed_run1_seconds": round(t1, 2), "elapsed_run2_seconds": round(t2, 2),
    }
    runnable_rows, excluded_rows = run1_r, run1_x
    n_runnable = len(runnable_rows)
    n_pass = sum(1 for r in runnable_rows if r["outcome"] == "pass")
    tax = taxonomy(runnable_rows, excluded_rows)
    aggregates = {
        "pass_over_runnable": wilson(n_pass, n_runnable) if n_runnable else wilson(0, 0),
        "pass_over_all_test_257": wilson(n_pass, len(test_tasks)),
        "pass_over_all_427_sanitized": wilson(n_pass, N_SANITIZED_TOTAL),
        "note": ("'runnable' = tasks with a runnable split under this arm's "
                 "protocol; 'all_test_257' = the whole 257-task MBPP TEST "
                 "split; 'all_427_sanitized' = the whole vendored corpus "
                 "— coverage-only, only the 257 test-split tasks were ever "
                 "run through the loop."),
    }
    return {
        "arm": arm_name, "protocol": protocol,
        "prefix_cut": prefix_n,
        "n_test_tasks_this_run": len(test_tasks) if prefix_n is None else prefix_n,
        "runnable_rows": runnable_rows, "excluded_rows": excluded_rows,
        "determinism": determinism, "outcome_taxonomy": tax,
        "aggregates": aggregates,
    }


# --------------------------------------------------------------------------- #
#  HR1 — FULL-R3 vs NO-RETRIEVAL, Newcombe CI + the registered paired-count
#  ladder (PROGRAM_SYNTHESIS_ARC3_PREREG.md §4: strong >=6 net passes,
#  weak/marginal 1-5, null otherwise), plus per-task attribution.
# --------------------------------------------------------------------------- #
def _row_by_task(rows: List[Dict[str, Any]]) -> Dict[int, Dict[str, Any]]:
    return {r["task_id"]: r for r in rows}


def _attribute_row(row: Dict[str, Any]) -> str:
    """Read provenance off a row (never a decision — a label of what the
    row's own recorded facts already show, the HQ3 `_attribute_change`
    class, extended with the retrieval rung/exemplar)."""
    retr = row.get("retrieval") or {}
    if retr.get("rung_reached") and retr.get("rung_reached") != "none":
        return "retrieval:rung=%s,exemplar=%s" % (
            retr.get("rung_reached"), retr.get("accept_task_id"))
    constr = str(row.get("construction") or "")
    rungs = row.get("rungs") or {}
    if constr.startswith("mck_"):
        return "mbpp_train_diet_chunk"
    if constr.startswith(("ck_", "ckt_")):
        return "arc1_corpus_chunk"
    if rungs.get("descend") is not None:
        return "descent_hole_fill"
    if rungs.get("lattice") is not None:
        return "bigram_lattice_spine"
    if constr:
        return "other_mechanism:%s" % constr
    return "unattributed"


def hr1_block(full_arm: Dict[str, Any], noret_arm: Dict[str, Any]) -> Dict[str, Any]:
    full_all = full_arm["runnable_rows"] + full_arm["excluded_rows"]
    noret_all = noret_arm["runnable_rows"] + noret_arm["excluded_rows"]
    full_ids = sorted(r["task_id"] for r in full_all)
    noret_ids = sorted(r["task_id"] for r in noret_all)
    same_set = full_ids == noret_ids

    fb = _row_by_task(full_arm["runnable_rows"])
    nb = _row_by_task(noret_arm["runnable_rows"])
    common_ids = sorted(set(fb) & set(nb))

    delta = newcombe_delta(
        full_arm["aggregates"]["pass_over_runnable"]["k"],
        full_arm["aggregates"]["pass_over_runnable"]["n"],
        noret_arm["aggregates"]["pass_over_runnable"]["k"],
        noret_arm["aggregates"]["pass_over_runnable"]["n"])

    changed = []
    for tid in common_ids:
        f, n = fb[tid], nb[tid]
        if f["outcome"] != n["outcome"]:
            changed.append({
                "task_id": tid, "full_r3_outcome": f["outcome"],
                "no_retrieval_outcome": n["outcome"],
                "attribution": _attribute_row(f),
            })
    gains = [c for c in changed if c["full_r3_outcome"] == "pass"
             and c["no_retrieval_outcome"] != "pass"]
    losses = [c for c in changed if c["no_retrieval_outcome"] == "pass"
             and c["full_r3_outcome"] != "pass"]
    net_passes = len(gains) - len(losses)

    # exclusive-passes bought by retrieval specifically (rung_reached !=
    # "none" on the FULL-R3 side, whether or not the outcome class changed —
    # the identity-list evidence, the HQ3 §3a precedent).
    retrieval_engaged_accepts = sorted(
        tid for tid, r in fb.items()
        if (r.get("retrieval") or {}).get("rung_reached") not in (None, "none")
        and str(r.get("outcome") or "").startswith(("pass", "accepted")))

    ci_separated = bool(delta["ci95"][0] > 0 or delta["ci95"][1] < 0)
    if net_passes >= 6 and ci_separated:
        band = "strong_confirmation"
    elif 1 <= net_passes <= 5 and ci_separated:
        band = "weak_marginal_confirmation"
    else:
        band = "null"

    return {
        "same_paired_task_id_set": same_set,
        "n_common_runnable": len(common_ids),
        "delta_full_r3_minus_no_retrieval": delta,
        "net_passes": net_passes,
        "gains_full_r3_over_no_retrieval": gains,
        "losses_no_retrieval_over_full_r3": losses,
        "registered_bar": {
            "strong": ">=6 net passes, CI-separated",
            "weak_marginal": "1-5 net passes, CI-separated",
            "null": "CI spans zero, OR point delta <= 0",
            "ceiling_reference": "12/257 (4.67%) held-out-honest, "
                                 "PROGRAM_SYNTHESIS_ARC3_R0_NOTES.md",
        },
        "verdict_band": band,
        "retrieval_engaged_accepts_full_r3": retrieval_engaged_accepts,
        "paired_changes": changed,
    }


# --------------------------------------------------------------------------- #
#  HR2 — the gapped:exhausted taxonomy vs Q5's 24-row FULL-arm baseline.
# --------------------------------------------------------------------------- #
def _q5_decoy_class(construction: Optional[str]) -> str:
    c = str(construction or "")
    if c.startswith("mck_"):
        return "mbpp_train_diet_chunk"
    if c.startswith(("ck_", "ckt_")):
        return "arc1_corpus_chunk"
    if c:
        return "starter_codebook_shape"
    return "none"


def hr2_block(full_arm: Dict[str, Any], q5_full_arm: Dict[str, Any]) -> Dict[str, Any]:
    q5_gx = [r for r in q5_full_arm["runnable_rows"]
             if r["outcome"] == "gapped:exhausted"]
    q5_classed: Dict[str, List[int]] = {"mbpp_train_diet_chunk": [],
                                        "arc1_corpus_chunk": [],
                                        "starter_codebook_shape": []}
    for r in q5_gx:
        q5_classed[_q5_decoy_class(r.get("construction"))].append(r["task_id"])
    covered_ids = sorted(q5_classed["mbpp_train_diet_chunk"]
                         + q5_classed["arc1_corpus_chunk"])
    residual_ids = sorted(q5_classed["starter_codebook_shape"])

    fb = _row_by_task(full_arm["runnable_rows"])
    covered_now = {tid: fb[tid]["outcome"] for tid in covered_ids if tid in fb}
    residual_now = {tid: fb[tid]["outcome"] for tid in residual_ids if tid in fb}
    covered_still_exhausted = sorted(
        tid for tid, out in covered_now.items() if out == "gapped:exhausted")
    residual_still_exhausted = sorted(
        tid for tid, out in residual_now.items() if out == "gapped:exhausted")

    # WHY a covered-class row moved or didn't — screen-engaged (kills>0) vs
    # retrieval-resolved (rung_reached != none, entirely bypasses the
    # codebook/screen path) vs neither (screen never engaged: the goal's
    # OWN frozen ps_screen_pool0 < ps_budget, R2.5's own documented
    # "NOT_SLACK is all-or-nothing" residual — this is a real, measured
    # mechanism boundary, not smoothed over).
    covered_mechanism: Dict[int, str] = {}
    for tid in covered_ids:
        r = fb.get(tid)
        if r is None:
            covered_mechanism[tid] = "not_in_full_r3_runnable"
            continue
        retr = r.get("retrieval") or {}
        kills = (r.get("screen") or {}).get("kills") or 0.0
        if retr.get("rung_reached") not in (None, "none"):
            covered_mechanism[tid] = "retrieval_resolved:rung=%s" % retr.get("rung_reached")
        elif kills and kills > 0:
            covered_mechanism[tid] = "screen_engaged:kills=%s" % kills
        elif r["outcome"] == "gapped:exhausted":
            covered_mechanism[tid] = "unchanged:screen_never_engaged_pool0_lt_budget"
        else:
            covered_mechanism[tid] = "unattributed_change"
    mechanism_counts: Dict[str, int] = {}
    for v in covered_mechanism.values():
        key = v.split(":")[0]
        mechanism_counts[key] = mechanism_counts.get(key, 0) + 1

    # attempts-per-accept vs Q5 (non-increasing bar).
    def attempts_per_accept(rows):
        acc = [r for r in rows if str(r.get("outcome") or "").startswith(
            ("pass", "accepted"))]
        atts = [float(r["attempts"]) for r in acc if r.get("attempts") is not None]
        return {"n_accepts": len(acc),
                "mean_attempts": round(sum(atts) / len(atts), 4) if atts else None,
                "total_attempts": round(sum(atts), 4) if atts else None}

    apa_full_r3 = attempts_per_accept(full_arm["runnable_rows"])
    apa_q5_full = attempts_per_accept(q5_full_arm["runnable_rows"])
    apa_verdict = None
    if apa_full_r3["mean_attempts"] is not None and apa_q5_full["mean_attempts"] is not None:
        apa_verdict = ("non_increasing" if
                       apa_full_r3["mean_attempts"] <= apa_q5_full["mean_attempts"]
                       else "increased")

    gx_now = [r for r in full_arm["runnable_rows"]
             if r["outcome"] == "gapped:exhausted"]

    return {
        "q5_baseline": {
            "n_gapped_exhausted": len(q5_gx),
            "covered_class_ids_chunk_cued": covered_ids,
            "n_covered_class": len(covered_ids),
            "residual_class_ids_starter_codebook_shape": residual_ids,
            "n_residual_class": len(residual_ids),
        },
        "covered_class_now": covered_now,
        "covered_class_mechanism": {str(k): v for k, v in covered_mechanism.items()},
        "covered_class_mechanism_counts": mechanism_counts,
        "n_covered_class_still_gapped_exhausted": len(covered_still_exhausted),
        "covered_class_still_gapped_exhausted_ids": covered_still_exhausted,
        "registered_bar_covered_class": "~0 (chunk-cued gapped:exhausted "
                                        "should fall to ~zero under the "
                                        "Arc3-R2.5 scoped screen)",
        "covered_class_honest_reading": (
            "The registered '~0' bar is NOT met for the full 17-row class "
            "as measured: 10/17 remain gapped:exhausted UNCHANGED because "
            "the Arc3-R2.5 screen's OWN 'NOT_SLACK' gate never engages for "
            "them (their frozen ps_screen_pool0 < ps_budget=3 — an "
            "already-documented residual of R2.5 itself, "
            "PROGRAM_SYNTHESIS_ARC3_R12_NOTES.md §9.4 residual 2: 'a goal "
            "with any initial slack is NEVER screened'). Of the 7/17 that "
            "DID move, the screen itself (kills>0) is responsible for 4 "
            "(160, 164, 300, 464 — only 464 becomes an actual PASS, "
            "164/300 become accepted_holdout_fail traps, 160 becomes an "
            "honest gapped:enumerate_failed); the NEW retrieval ladder "
            "(unrelated to the screen, resolving BEFORE the codebook path "
            "is ever reached) independently resolves 3 more (142 pass; "
            "165/452 accepted_holdout_fail traps). See "
            "covered_class_mechanism for the per-task attribution."),
        "residual_class_now": residual_now,
        "n_residual_class_still_gapped_exhausted": len(residual_still_exhausted),
        "residual_class_still_gapped_exhausted_ids": residual_still_exhausted,
        "residual_note": ("the 7-row starter-codebook-shape class is "
                          "DESCEND_APPLICABLE by construction (a branch/"
                          "scalar-fold trigger match) and is NOT in the "
                          "Arc3-R2.5 screen's scope by design "
                          "(PROGRAM_SYNTHESIS_ARC3_R12_NOTES.md §9.4 "
                          "residual 1) — reported as the registered "
                          "residual, not a defect."),
        "gapped_exhausted_full_r3_now": {
            "n": len(gx_now), "task_ids": sorted(r["task_id"] for r in gx_now),
        },
        "attempts_per_accept": {
            "full_r3": apa_full_r3, "q5_full": apa_q5_full,
            "verdict": apa_verdict,
            "registered_bar": "non-increasing vs Q5 FULL",
        },
    }


# --------------------------------------------------------------------------- #
#  migration matrix vs the arc-2 FULL arm — paired ids: retrieval accepts,
#  screen-recovered enumerator accepts, new traps, regressions.
# --------------------------------------------------------------------------- #
def migration_matrix_vs_arc2(full_arm: Dict[str, Any],
                             q5_full_arm: Dict[str, Any]) -> Dict[str, Any]:
    fb = _row_by_task(full_arm["runnable_rows"])
    qb = _row_by_task(q5_full_arm["runnable_rows"])
    common = sorted(set(fb) & set(qb))

    q5_pass = sorted(tid for tid in common if qb[tid]["outcome"] == "pass")
    r3_pass = sorted(tid for tid in common if fb[tid]["outcome"] == "pass")
    gains = sorted(set(r3_pass) - set(q5_pass))
    losses = sorted(set(q5_pass) - set(r3_pass))

    retrieval_accepts = sorted(
        tid for tid in gains
        if (fb[tid].get("retrieval") or {}).get("rung_reached") not in (None, "none"))
    screen_recovered = sorted(
        tid for tid in gains
        if tid not in retrieval_accepts
        and qb[tid]["outcome"] == "gapped:exhausted"
        and fb[tid]["outcome"] == "pass")
    other_gains = sorted(set(gains) - set(retrieval_accepts) - set(screen_recovered))

    new_traps = sorted(
        tid for tid in common
        if qb[tid]["outcome"] != "accepted_holdout_fail"
        and fb[tid]["outcome"] == "accepted_holdout_fail")

    regressions = []
    for tid in losses:
        regressions.append({
            "task_id": tid, "q5_full_outcome": qb[tid]["outcome"],
            "full_r3_outcome": fb[tid]["outcome"],
        })

    outcome_move_counts: Dict[str, int] = {}
    for tid in common:
        qo, fo = qb[tid]["outcome"], fb[tid]["outcome"]
        if qo != fo:
            key = "%s -> %s" % (qo, fo)
            outcome_move_counts[key] = outcome_move_counts.get(key, 0) + 1

    return {
        "n_common_runnable": len(common),
        "q5_full_pass_ids": q5_pass, "full_r3_pass_ids": r3_pass,
        "n_q5_full_pass": len(q5_pass), "n_full_r3_pass": len(r3_pass),
        "gains_over_q5_full": gains,
        "gains_attributed_to_retrieval": retrieval_accepts,
        "gains_attributed_to_screen_recovered_enumerate": screen_recovered,
        "gains_other_or_unattributed": other_gains,
        "new_traps_vs_q5_full": new_traps,
        "regressions_vs_q5_full": regressions,
        "n_regressions": len(regressions),
        "outcome_class_move_counts": dict(sorted(
            outcome_move_counts.items(), key=lambda kv: -kv[1])),
    }


# --------------------------------------------------------------------------- #
#  remaining-failure taxonomy + density extrapolation (honest, labelled).
# --------------------------------------------------------------------------- #
def failure_taxonomy(full_arm: Dict[str, Any]) -> Dict[str, Any]:
    rows = full_arm["runnable_rows"]
    n = len(rows)
    by: Dict[str, List[int]] = {}
    for r in rows:
        by.setdefault(r["outcome"], []).append(r["task_id"])
    ranked = sorted(by.items(), key=lambda kv: -len(kv[1]))
    return {
        "n_runnable": n,
        "ranked": [{"rank": i + 1, "class": k, "n": len(v),
                   "share_pct": round(100.0 * len(v) / n, 2) if n else None,
                   "task_ids": sorted(v)}
                  for i, (k, v) in enumerate(ranked)],
    }


def density_extrapolation(r0_ceiling: Dict[str, Any],
                          hr1: Dict[str, Any]) -> Dict[str, Any]:
    """Honest, LABELLED extrapolation (never a fresh measurement): the R0
    ceiling is 12/257 held-out-honest at a 90-exemplar pool built from the
    120-task MBPP train split. If the SAME density (12 ceiling tasks per 90
    pool exemplars, i.e. ceiling scales linearly with pool size — an
    assumption, stated as one) held at 2x/5x/10x pool scale, the ceiling
    mass would scale proportionally; the mechanism's OWN measured capture
    rate against its own ceiling (from HR1's gains, vs the 12-task ceiling)
    is applied as a conversion factor, not the raw ceiling. Every number
    here is an EXTRAPOLATION, not a new measurement."""
    pool = r0_ceiling.get("pool", {})
    n_pool = pool.get("n_pool_exemplars") or 90
    base_ceiling_k = 12
    base_ceiling_n = 257
    n_retrieval_gains = len(hr1.get("gains_full_r3_over_no_retrieval", []))
    capture_rate = (n_retrieval_gains / base_ceiling_k) if base_ceiling_k else None
    scenarios = {}
    for mult in (2, 5, 10):
        scaled_ceiling = round(base_ceiling_k * mult, 2)
        scaled_capture = (round(scaled_ceiling * capture_rate, 2)
                          if capture_rate is not None else None)
        scenarios["%dx_pool" % mult] = {
            "assumed_pool_size": n_pool * mult,
            "linearly_scaled_ceiling_k": scaled_ceiling,
            "linearly_scaled_ceiling_pct": round(
                100.0 * scaled_ceiling / base_ceiling_n, 3),
            "mechanism_capture_rate_applied": capture_rate,
            "extrapolated_mechanism_captures": scaled_capture,
            "extrapolated_capture_pct": (
                round(100.0 * scaled_capture / base_ceiling_n, 3)
                if scaled_capture is not None else None),
        }
    return {
        "assumption": ("ceiling mass scales LINEARLY with exemplar pool "
                      "size (untested — the R0/R1 arity cross-tab shows "
                      "demand/supply gaps concentrated at higher arities, "
                      "so a real corpus expansion would likely scale "
                      "faster at arity 3/4 than arity 1 — this is a "
                      "labelled, honest extrapolation, not a measurement)."),
        "base_pool_n": n_pool, "base_ceiling_k": base_ceiling_k,
        "base_ceiling_n": base_ceiling_n,
        "mechanism_capture_rate_vs_ceiling": capture_rate,
        "n_retrieval_gains_this_measurement": n_retrieval_gains,
        "scenarios": scenarios,
    }


# --------------------------------------------------------------------------- #
#  main
# --------------------------------------------------------------------------- #
def main() -> None:
    t_start = time.time()
    with open(FIXTURE_PATH) as f:
        all_tasks = json.load(f)
    with open(PROVENANCE_PATH) as f:
        provenance = json.load(f)
    with open(ARC2_ENDGAME_PATH) as f:
        arc2_endgame = json.load(f)
    with open(ARC2_ENDGAME_PATH, "rb") as f:
        arc2_endgame_sha256 = hashlib.sha256(f.read()).hexdigest()
    with open(R0_CEILING_PATH) as f:
        r0_ceiling = json.load(f)
    with open(R0_CEILING_PATH, "rb") as f:
        r0_ceiling_sha256 = hashlib.sha256(f.read()).hexdigest()

    splits = q0_split_tasks(all_tasks)
    test_tasks = splits["test"]
    for t in test_tasks:
        assert "code" not in t, "contamination: code field survived split_tasks"
    split_counts = {k: len(v) for k, v in splits.items()}
    split_counts["total"] = sum(split_counts.values())
    assert split_counts["total"] == N_SANITIZED_TOTAL

    print("== split counts ==", split_counts)
    print("== ARM full_r3 ==")
    arm_full = run_arm("full_r3", test_tasks)
    print("full_r3 elapsed:", arm_full["determinism"]["elapsed_run1_seconds"]
          + arm_full["determinism"]["elapsed_run2_seconds"])

    print("== ARM no_retrieval ==")
    arm_noret = run_arm("no_retrieval", test_tasks)
    print("no_retrieval elapsed:",
          arm_noret["determinism"]["elapsed_run1_seconds"]
          + arm_noret["determinism"]["elapsed_run2_seconds"])

    elapsed_so_far = time.time() - t_start
    per_task_rate = (
        (arm_full["determinism"]["elapsed_run1_seconds"]
         + arm_noret["determinism"]["elapsed_run1_seconds"]) / (2 * len(test_tasks))
    )
    est_official_twin = per_task_rate * len(test_tasks) * 2
    official_prefix_n: Optional[int] = None
    if elapsed_so_far + est_official_twin > TIME_BUDGET_SECONDS:
        official_prefix_n = max(MIN_PREFIX, len(test_tasks) - 1)
        print("TIME-BOX: cutting OFFICIAL-R3 to a deterministic prefix of "
              "%d tasks (never below %d)" % (official_prefix_n, MIN_PREFIX))

    print("== ARM official_r3 ==")
    arm_official = run_arm("official_r3", test_tasks, prefix_n=official_prefix_n)
    print("official_r3 elapsed:",
          arm_official["determinism"]["elapsed_run1_seconds"]
          + arm_official["determinism"]["elapsed_run2_seconds"])

    q5_full_arm = arc2_endgame["arms"]["full"]
    hr1 = hr1_block(arm_full, arm_noret)
    hr2 = hr2_block(arm_full, q5_full_arm)
    matrix = migration_matrix_vs_arc2(arm_full, q5_full_arm)
    taxo = failure_taxonomy(arm_full)
    density = density_extrapolation(r0_ceiling, hr1)

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
            "Arc 3 R3 — the POWERED MBPP ENDGAME for the retrieval-shaped-"
            "proposal arc. Three arms on the MBPP test split (257 tasks): "
            "FULL-R3 (committed stack as of seed v1.5.1, PRIMARY protocol — "
            "THE arc number), NO-RETRIEVAL (same boot, screen ON, retrieval "
            "lane disabled at its cleanest seam — see condition.no_retrieval_"
            "off_switch — PRIMARY protocol, the HR1 contrast), OFFICIAL-R3 "
            "(FULL-R3 boot, OFFICIAL protocol — comparability row, protocol-"
            "flagged, never merged into a PRIMARY aggregate)."),
        "head": head,
        "measured_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "provenance_ref": os.path.relpath(PROVENANCE_PATH, ROOT),
        "provenance": provenance,
        "engine": {"so": os.path.relpath(so, ROOT),
                   "mtime": time.strftime(
                       "%Y-%m-%dT%H:%M:%S",
                       time.localtime(os.path.getmtime(so)))
                   if os.path.exists(so) else None},
        "condition": {
            "env": {"OZMA_NO_LLM": os.environ.get("OZMA_NO_LLM"),
                    "OZMA_SEED_PERSIST_DISABLED":
                        os.environ.get("OZMA_SEED_PERSIST_DISABLED")},
            "arms": {
                "full_r3": "ensure_program_synthesis (seed v1.5.1, retrieval "
                          "+ scoped codebook screen live) + install_mined_"
                          "chunks + ensure_mbpp_train_diet; PRIMARY protocol",
                "no_retrieval": "SAME boot as full_r3 with the retrieval "
                               "lane disabled — see no_retrieval_off_switch "
                               "below; PRIMARY protocol",
                "official_r3": "SAME boot as full_r3; OFFICIAL protocol — "
                              "protocol-flagged, never a PRIMARY aggregate "
                              "member",
            },
            "no_retrieval_off_switch": (
                "A Seed{id:'mbpp_exemplars', version:'1.0.0'} marker node is "
                "added to the substrate BEFORE ensure_program_synthesis runs. "
                "prog_retrieval.ensure_exemplar_store's own idempotent "
                "_has_seed guard then treats the exemplar store as already "
                "installed and boards ZERO Exemplar nodes (confirmed live "
                "every boot via an assert in boot_no_retrieval). Zero "
                "Exemplar nodes -> score_exemplars boards zero ScoreLinks -> "
                "pr_select_candidate never fires -> run_retrieval_ladder's "
                "candidate pool is empty -> pr_rung_reached='none' "
                "immediately -> the goal falls through to the UNCHANGED "
                "pending codebook/lattice/descend/enumerate stack, screen "
                "fully live. No seed/engine/rule file is touched; this is a "
                "boot-order choice local to this measurement script."),
            "batching": "one FRESH substrate per (task, arm); tasks in "
                        "sorted task_id order; twin full-battery run per arm "
                        "for determinism",
            "pipeline": "domains.prog_synthesis.synthesize_from_request "
                        "(unchanged); spec layer domains.mbpp_spec.parse_"
                        "asserts/split_rows (unchanged)",
            "held_out_comparator": "domains.prog_synthesis._row_cmp_ok",
            "contamination_enforcement": [
                "task['code'] deleted at split time (mbpp_zero_shot_"
                "baseline.split_tasks/_strip_code, reused verbatim)",
                "domains.mbpp_spec.parse_asserts/split_rows never read "
                "task['code']",
                "every substrate is a fresh, OZMA_SEED_PERSIST_DISABLED "
                "boot; no domains.teach.teach call in this file",
            ],
            "time_box": {
                "budget_seconds": TIME_BUDGET_SECONDS, "min_prefix": MIN_PREFIX,
                "official_prefix_cut": official_prefix_n,
            },
        },
        "split_counts": split_counts,
        "arc2_full_continuity": {
            "file": os.path.relpath(ARC2_ENDGAME_PATH, ROOT),
            "sha256": arc2_endgame_sha256,
            "cited_outcome_hash_run1": q5_full_arm["determinism"]["outcome_hash_run1"],
            "note": ("Arc-2 Q5's frozen FULL-arm artifact is CITED (used as "
                     "the paired-continuity comparator for HR2/the migration "
                     "matrix), never re-run — this hash is re-verified live "
                     "by tests/test_mbpp_arc3_endgame_migrated.py."),
        },
        "r0_ceiling_continuity": {
            "file": os.path.relpath(R0_CEILING_PATH, ROOT),
            "sha256": r0_ceiling_sha256,
            "note": ("The R0 oracle-ceiling artifact is CITED (the density "
                     "extrapolation's base pool/ceiling numbers), never "
                     "re-run — hash re-verified live."),
        },
        "arms": {"full_r3": arm_full, "no_retrieval": arm_noret,
                 "official_r3": arm_official},
        "hr1": hr1,
        "hr2": hr2,
        "migration_matrix_vs_arc2_full": matrix,
        "remaining_failure_taxonomy": taxo,
        "density_extrapolation": density,
        "trajectory": {
            "q0a_stress_zero_shot_pct": 0.42,
            "arc2_q5_full_primary_pct": 7.00,
            "arc3_r3_full_r3_primary_pct":
                arm_full["aggregates"]["pass_over_runnable"]["p"] * 100
                if arm_full["aggregates"]["pass_over_runnable"]["p"] is not None
                else None,
        },
        "environment": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "loadavg": list(os.getloadavg()),
        },
        "elapsed_seconds": round(time.time() - t_start, 2),
    }
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w") as f:
        json.dump(artifact, f, indent=1, sort_keys=False, default=_json_default)
        f.write("\n")
    print("wrote", OUT_PATH)
    for name in ("full_r3", "no_retrieval", "official_r3"):
        agg = artifact["arms"][name]["aggregates"]
        pr = agg["pass_over_runnable"]
        print("%s: runnable %d/%d p=%s ci=%s; det_identical=%s" % (
            name, pr["k"], pr["n"], pr["p"], pr["ci95"],
            artifact["arms"][name]["determinism"]["identical"]))
    print("HR1 delta:", hr1["delta_full_r3_minus_no_retrieval"])
    print("HR1 net_passes:", hr1["net_passes"], "band:", hr1["verdict_band"])
    print("HR2 covered-class still exhausted:",
          hr2["n_covered_class_still_gapped_exhausted"], "/",
          hr2["q5_baseline"]["n_covered_class"])
    print("elapsed: %.1fs" % artifact["elapsed_seconds"])


if __name__ == "__main__":
    main()

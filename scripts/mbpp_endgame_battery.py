#!/usr/bin/env python
"""mbpp_endgame_battery — Arc 2 Q5: the POWERED MBPP ENDGAME.

PROGRAM_SYNTHESIS_ARC2_PREREG.md (HQ3/HQ4, the three-way PRIMARY/
SECONDARY-OFFICIAL/STRESS split protocol §0), `PROGRAM_SYNTHESIS_ARC2_
Q0_BASELINE.md` (the frozen zero-shot/STRESS continuity row, 1/240,
0.42% — cited, never re-run), `domains/mbpp_spec.py` (the Q2 spec layer
this runner calls — parse_asserts/split_rows, NOT the Q0-A parser),
`domains/prog_chunk_growth.py` (`install_mined_chunks`/
`ensure_mbpp_train_diet` — the Q3 diet), `scripts/prog_synthesis_
battery.py` (`strip_to_starter` — the C-CODEBOOK-FROZEN precedent this
runner mirrors byte-for-byte for the CONTENT-STRIPPED arm).

This is a MEASUREMENT DRIVER (the `prog_synthesis_battery.py` /
`mbpp_zero_shot_baseline.py` class): it boots agents, feeds the MBPP
**test** split (task_id in [11,510], 257 tasks) through the UNCHANGED
`domains.prog_synthesis.synthesize_from_request` pipeline, reads
outcomes back, and writes the artifact. It makes NO agent decisions —
every accept/gap/pass verdict is the seed-rule loop's own (or, for
held-out scoring, a FIXED formula — `domains.prog_synthesis._row_cmp_ok`,
the SAME comparator the engine itself uses for tol/unordered rows,
reused here rather than reimplemented). No synthesis/engine/seed/spec
code is touched by this phase — it MEASURES the stack exactly as
committed.

ARMS (all three PRIMARY-anchored per the prereg except OFFICIAL, which
is protocol-distinct and never merged into a primary aggregate):

  full              committed stack + the Q3 train diet installed
                    (ensure_mbpp_train_diet), PRIMARY protocol
                    (mbpp_spec.split_rows 'primary'). THE arc's external
                    number.
  content_stripped  SAME mechanisms (descent/repair/exclude all live —
                    same `ensure_program_synthesis` boot), learned
                    CONTENT off: `strip_to_starter` (imported verbatim
                    from `prog_synthesis_battery.py` — the frozen_p7
                    precedent) strips the write codebook to the 8 held
                    starter shapes and removes EVERY ConstructionBigram
                    node (the arc-1 corpus bigrams `ensure_program_
                    synthesis` boards by default) — no mined chunks, no
                    mbpp_train_diet, no bigrams of any provenance. PRIMARY
                    protocol, the SAME split as `full` (paired by
                    construction: `mbpp_spec.split_rows` never reads
                    which arm is asking). THE HQ3 contrast.
  official          the `full` boot, OFFICIAL protocol (every parseable
                    assert revealed, scored on the SAME asserts) — the
                    published-MBPP-comparability row. Protocol-flagged on
                    every row; never mixed into a PRIMARY aggregate.

(The STRESS/zero-shot row is Q0-A's frozen artifact,
`results/mbpp_zero_shot_baseline.json` — cited via `q0_continuity`
below, never re-run here.)

CONTAMINATION (provenance.json's rule, enforced mechanically):
  - test-split task dicts have `code` removed the instant they're read
    off disk (`mbpp_zero_shot_baseline.split_tasks`/`_strip_code`,
    imported and reused verbatim rather than reimplemented — the SAME
    enforcement point Q0-A already gates).
  - `domains.mbpp_spec.parse_asserts`/`split_rows` never read `task["code"]`
    (by construction — the module's own docstring guarantee, cross-
    checked by `tests/test_mbpp_spec_migrated.py`).
  - every substrate is a FRESH boot, one per (task, arm); no
    `domains.teach.teach` call anywhere in this file; OZMA_SEED_PERSIST_
    DISABLED keeps every boot ephemeral. This track's own eval log
    (`results/mbpp_endgame.json`) is, like Q0-A's, deliberately excluded
    from `tests/test_mbpp_contamination_migrated.py`'s SCAN_TARGETS (an
    eval log legitimately records which prompt was tested) — this
    phase's own test suite (`tests/test_mbpp_endgame_migrated.py`) runs
    an equivalent scan of its own on this artifact, plus RUNS the shared
    gate and reports it.

Run:
  PYTHONPATH=runners/dsl/python:.:scripts OZMA_NO_LLM=1 \
  OZMA_SEED_PERSIST_DISABLED=1 python scripts/mbpp_endgame_battery.py
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

import prog_synthesis_battery as psb  # noqa: E402 — strip_to_starter, byte-identical reuse
from mbpp_zero_shot_baseline import split_tasks as q0_split_tasks  # noqa: E402

from domains import engineering_residual_ingest as eri  # noqa: E402

FIXTURE_PATH = os.path.join(ROOT, "tests", "fixtures", "mbpp",
                            "sanitized-mbpp.json")
PROVENANCE_PATH = os.path.join(ROOT, "tests", "fixtures", "mbpp",
                               "provenance.json")
Q0_BASELINE_PATH = os.path.join(ROOT, "results", "mbpp_zero_shot_baseline.json")
OUT_PATH = os.path.join(ROOT, "results", "mbpp_endgame.json")

_Z = 1.959963984540054  # 95%
MIN_PREFIX = 150  # the "never fewer" floor if a time-box cut is ever needed
TIME_BUDGET_SECONDS = 25 * 60  # leaves margin inside the ~30 min box
N_SANITIZED_TOTAL = 427  # the whole vendored corpus — the wider coverage denominator


# --------------------------------------------------------------------------- #
#  statistics (self-contained — the Q0-A precedent: this file owns no
#  coupling to the internal battery driver for its OWN stats, even though
#  it reuses the battery's `strip_to_starter` mechanism verbatim below).
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


# --------------------------------------------------------------------------- #
#  JSON-safety for the artifact only (never for the pipeline itself — the
#  engine happily stores raw Python set/frozenset attrs; only `json.dump`
#  of THIS artifact needs a fallback for a top-level unordered row's
#  frozenset `expected`/`got`).
# --------------------------------------------------------------------------- #
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
def boot_full():
    """FULL: the committed stack + the Q3 train diet, byte-identical to
    the P7-D MAIN-P7 boot plus `ensure_mbpp_train_diet` (Q3's additive
    installer)."""
    s = srs.Substrate()
    ag = s.add_node("Agent", {})
    psy.ensure_program_synthesis(s, s._inner, ag)
    pcg.install_mined_chunks(s)
    pcg.ensure_mbpp_train_diet(s, s._inner, ag)
    return s, ag


def boot_content_stripped():
    """CONTENT-STRIPPED: the SAME mechanisms (descent/repair/exclude all
    live via the unchanged `ensure_program_synthesis` boot), but learned
    CONTENT off — `strip_to_starter` (imported verbatim from
    `prog_synthesis_battery.py`, the C-CODEBOOK-FROZEN / frozen_p7
    precedent) removes every non-starter ShapeSignature AND every
    ConstructionBigram node. Mined chunks / the mbpp_train_diet seed are
    simply never installed (no `install_mined_chunks`/`ensure_mbpp_
    train_diet` call) — starter-8 codebook only, no bigrams of ANY
    provenance (arc-1 corpus OR mbpp_train)."""
    s = srs.Substrate()
    ag = s.add_node("Agent", {})
    psy.ensure_program_synthesis(s, s._inner, ag)
    psb.strip_to_starter(s)
    return s, ag


ARM_BOOT = {"full": boot_full, "content_stripped": boot_content_stripped,
            "official": boot_full}
ARM_PROTOCOL = {"full": "primary", "content_stripped": "primary",
                "official": "official"}


# --------------------------------------------------------------------------- #
#  verdict — ProgEval on a fresh throwaway substrate (the Q0-A/battery
#  `prog_eval`/`agree` pattern), generalised to Q2's tol/unordered row
#  schema via `psy._row_cmp_ok` — THE SAME fixed formula the engine's own
#  `ps_row_pass_special`/`ps_row_fail_special` rules consume, reused here
#  rather than reimplemented (never a second, drifting copy of one
#  comparator).
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
        except Exception as e:  # noqa: BLE001 — never let one row crash the batch
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
#  per-task run — mechanical read-back, the Q0-A `run_task` shape
#  generalised with an explicit `protocol` tag on every row (arc-wide
#  labelling rule).
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
    except Exception as e:  # noqa: BLE001 — an honest, never-crash floor
        row.update({"recognized": None, "status": None, "construction": None,
                    "attempts": None, "rungs": None, "gap_reason": None,
                    "enumerate_outcome": None, "n_counterexamples": 0,
                    "excluded": [], "outcome": "runner_exception:%s" % type(e).__name__,
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
           r["attempts"], r["gap_reason"]] for r in runnable_rows]
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


# --------------------------------------------------------------------------- #
#  one arm, twin-run for determinism (the Q0-A / battery precedent).
# --------------------------------------------------------------------------- #
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
                 "protocol (>=2 parseable rows for primary, >=1 for "
                 "official); 'all_test_257' = the whole 257-task MBPP TEST "
                 "split (the arc-wide anchor denominator); "
                 "'all_427_sanitized' = the whole vendored corpus "
                 "(test+validation+train+few_shot) — the standing "
                 "coverage-denominator rule: ONLY the 257 test-split tasks "
                 "were ever run through the loop, this denominator states "
                 "coverage against the full corpus, it does not claim "
                 "anything about the other 170 tasks."),
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
#  HQ3 — the paired FULL vs CONTENT-STRIPPED contrast (Newcombe CI on the
#  SAME paired task-id set, per the standing arc-1 stratum-delta rule).
# --------------------------------------------------------------------------- #
def _row_by_task(rows: List[Dict[str, Any]]) -> Dict[int, Dict[str, Any]]:
    return {r["task_id"]: r for r in rows}


def _attribute_change(full_row: Dict[str, Any]) -> str:
    """Read rung + construction provenance off the FULL-arm row (never a
    Python decision about WHETHER content mattered — this only labels the
    mechanism a row already exhibits, the P6.5/`_learned_layer_provenance`
    convention)."""
    constr = str(full_row.get("construction") or "")
    rungs = full_row.get("rungs") or {}
    if constr.startswith("mck_"):
        return "mbpp_train_diet_chunk"
    if constr.startswith(("ck_", "ckt_")):
        return "arc1_corpus_chunk"
    if rungs.get("descend") is not None:
        return "descent_hole_fill"
    if rungs.get("lattice") is not None:
        return "bigram_lattice_spine"
    return "other_mechanism_or_unattributed"


def hq3_block(full_arm: Dict[str, Any], stripped_arm: Dict[str, Any]) -> Dict[str, Any]:
    full_all = full_arm["runnable_rows"] + full_arm["excluded_rows"]
    stripped_all = stripped_arm["runnable_rows"] + stripped_arm["excluded_rows"]
    full_ids = sorted(r["task_id"] for r in full_all)
    stripped_ids = sorted(r["task_id"] for r in stripped_all)
    same_set = full_ids == stripped_ids

    fb = _row_by_task(full_arm["runnable_rows"])
    sb = _row_by_task(stripped_arm["runnable_rows"])
    common_runnable_ids = sorted(set(fb) & set(sb))

    delta = newcombe_delta(
        full_arm["aggregates"]["pass_over_runnable"]["k"],
        full_arm["aggregates"]["pass_over_runnable"]["n"],
        stripped_arm["aggregates"]["pass_over_runnable"]["k"],
        stripped_arm["aggregates"]["pass_over_runnable"]["n"])

    changed = []
    for tid in common_runnable_ids:
        f, s = fb[tid], sb[tid]
        if f["outcome"] != s["outcome"]:
            changed.append({"task_id": tid, "full_outcome": f["outcome"],
                            "stripped_outcome": s["outcome"],
                            "attribution": _attribute_change(f)})
    gains = [c for c in changed if c["full_outcome"] == "pass"
             and c["stripped_outcome"] != "pass"]
    losses = [c for c in changed if c["stripped_outcome"] == "pass"
             and c["full_outcome"] != "pass"]

    attribution_counts: Dict[str, int] = {}
    for c in changed:
        attribution_counts[c["attribution"]] = attribution_counts.get(c["attribution"], 0) + 1

    # chunk-cued / bigram-ordered footprint across ALL full-arm accepts
    # (not just the paired-changed set) — the "content-attribution table"
    # the phase card asks for, independent of whether the change flipped
    # the outcome CLASS.
    full_accepted = [r for r in full_arm["runnable_rows"]
                     if str(r["outcome"]).startswith(("pass", "accepted"))]
    chunk_named = sorted(r["task_id"] for r in full_accepted
                         if str(r.get("construction") or "").startswith(
                             ("ck_", "ckt_", "mck_")))
    mbpp_diet_named = sorted(r["task_id"] for r in full_accepted
                             if str(r.get("construction") or "").startswith("mck_"))
    descent_used = sorted(r["task_id"] for r in full_accepted
                          if (r.get("rungs") or {}).get("descend") is not None)
    lattice_used = sorted(r["task_id"] for r in full_accepted
                          if (r.get("rungs") or {}).get("lattice") is not None)

    return {
        "same_paired_task_id_set": same_set,
        "full_task_ids": full_ids, "content_stripped_task_ids": stripped_ids,
        "n_common_runnable": len(common_runnable_ids),
        "delta_full_minus_content_stripped": delta,
        "confirmed": bool(delta["ci95"][0] > 0 or delta["ci95"][1] < 0) and delta["delta"] > 0,
        "paired_changes": changed,
        "gains_full_over_stripped": gains,
        "losses_stripped_over_full": losses,
        "attribution_counts_over_changed": attribution_counts,
        "content_footprint_over_full_accepts": {
            "chunk_named_accepts": chunk_named,
            "mbpp_train_diet_chunk_accepts": mbpp_diet_named,
            "descent_used_accepts": descent_used,
            "bigram_lattice_used_accepts": lattice_used,
        },
    }


# --------------------------------------------------------------------------- #
#  migration matrix vs Q0 — mechanical crosswalk (never a claim, a
#  per-task-id join across three artifacts).
# --------------------------------------------------------------------------- #
def _q0_outcome_map(q0_artifact: Dict[str, Any]) -> Dict[int, str]:
    out: Dict[int, str] = {}
    for r in q0_artifact["runnable_rows"]:
        out[r["task_id"]] = r["outcome"]
    for r in q0_artifact["excluded_rows"]:
        out[r["task_id"]] = r["outcome"]
    return out


def migration_matrix(q0_artifact: Dict[str, Any], full_arm: Dict[str, Any],
                     stripped_arm: Dict[str, Any]) -> Dict[str, Any]:
    q0_by_task = _q0_outcome_map(q0_artifact)
    full_by_task = _row_by_task(full_arm["runnable_rows"] + full_arm["excluded_rows"])
    stripped_by_task = _row_by_task(stripped_arm["runnable_rows"] + stripped_arm["excluded_rows"])

    by_q0_class: Dict[str, Dict[str, Any]] = {}
    for tid, q0_outcome in q0_by_task.items():
        entry = by_q0_class.setdefault(q0_outcome, {
            "task_ids": [], "full_outcome_counts": {}, "stripped_outcome_counts": {},
            "content_moved_task_ids": [],
        })
        entry["task_ids"].append(tid)
        f_out = full_by_task.get(tid, {}).get("outcome", "not_in_test_split")
        s_out = stripped_by_task.get(tid, {}).get("outcome", "not_in_test_split")
        entry["full_outcome_counts"][f_out] = entry["full_outcome_counts"].get(f_out, 0) + 1
        entry["stripped_outcome_counts"][s_out] = entry["stripped_outcome_counts"].get(s_out, 0) + 1
        if f_out != s_out:
            entry["content_moved_task_ids"].append(tid)
    for entry in by_q0_class.values():
        entry["task_ids"].sort()
        entry["content_moved_task_ids"].sort()
    return dict(sorted(by_q0_class.items(), key=lambda kv: -len(kv[1]["task_ids"])))


# --------------------------------------------------------------------------- #
#  main
# --------------------------------------------------------------------------- #
# --------------------------------------------------------------------------- #
#  PROPOSAL 3 (measured-residual filing, DESIGN_REVIEW_CAPABILITY_EXPANSION_
#  PREREG.md §4) — the FULL arm's own `outcome_taxonomy` (built above by
#  `taxonomy()`, already the "N tasks in bucket X" dict the design doc names)
#  is mechanically ingested as EngineeringResidual fact nodes on a small,
#  dedicated, persisted substrate (domains.engineering_residual_ingest —
#  NOT the real jabberwock daemon's own checkpoint). No interpretation
#  happens here: the numbers are already computed by `run_arm`/`taxonomy`
#  above; this function only writes them. seeds/engineering_residual_gap.json
#  (loaded on that substrate) decides which populations are standing gaps.
# --------------------------------------------------------------------------- #
def ingest_engineering_residuals(artifact: Dict[str, Any]) -> Dict[str, Any]:
    tax = artifact["arms"]["full"]["outcome_taxonomy"]
    s, agent = eri.load_or_boot_residual_substrate()
    result = eri.ingest_taxonomy(s, agent, source_script="mbpp_endgame_battery.full",
                                 taxonomy=tax)
    eri.save_residual_substrate(s, agent)
    print("ingested engineering residuals:", len(result["upserted"]), "populations",
          "->", eri.DEFAULT_CHECKPOINT)
    return result


def main() -> None:
    t_start = time.time()
    with open(FIXTURE_PATH) as f:
        all_tasks = json.load(f)
    with open(PROVENANCE_PATH) as f:
        provenance = json.load(f)
    with open(Q0_BASELINE_PATH) as f:
        q0_artifact = json.load(f)
    with open(Q0_BASELINE_PATH, "rb") as f:
        q0_sha256 = hashlib.sha256(f.read()).hexdigest()

    splits = q0_split_tasks(all_tasks)
    test_tasks = splits["test"]
    for t in test_tasks:
        assert "code" not in t, "contamination: code field survived split_tasks"
    split_counts = {k: len(v) for k, v in splits.items()}
    split_counts["total"] = sum(split_counts.values())
    assert split_counts["total"] == N_SANITIZED_TOTAL

    print("== split counts ==", split_counts)
    print("== ARM full ==")
    arm_full = run_arm("full", test_tasks)
    print("full elapsed:", arm_full["determinism"]["elapsed_run1_seconds"]
          + arm_full["determinism"]["elapsed_run2_seconds"])

    print("== ARM content_stripped ==")
    arm_stripped = run_arm("content_stripped", test_tasks)
    print("content_stripped elapsed:",
          arm_stripped["determinism"]["elapsed_run1_seconds"]
          + arm_stripped["determinism"]["elapsed_run2_seconds"])

    elapsed_so_far = time.time() - t_start
    # per-task rate measured off the two runs just completed — used ONLY to
    # decide whether OFFICIAL needs a documented deterministic prefix.
    per_task_rate = (
        (arm_full["determinism"]["elapsed_run1_seconds"]
         + arm_stripped["determinism"]["elapsed_run1_seconds"]) / (2 * len(test_tasks))
    )
    est_official_twin = per_task_rate * len(test_tasks) * 2
    official_prefix_n: Optional[int] = None
    if elapsed_so_far + est_official_twin > TIME_BUDGET_SECONDS:
        official_prefix_n = max(MIN_PREFIX, len(test_tasks) - 1)
        print("TIME-BOX: cutting OFFICIAL to a deterministic prefix of %d "
              "tasks (never below %d) — FULL/CONTENT-STRIPPED already ran "
              "the full 257" % (official_prefix_n, MIN_PREFIX))

    print("== ARM official ==")
    arm_official = run_arm("official", test_tasks, prefix_n=official_prefix_n)
    print("official elapsed:",
          arm_official["determinism"]["elapsed_run1_seconds"]
          + arm_official["determinism"]["elapsed_run2_seconds"])

    hq3 = hq3_block(arm_full, arm_stripped)
    matrix = migration_matrix(q0_artifact, arm_full, arm_stripped)

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
            "Arc 2 Q5 — the POWERED MBPP ENDGAME. Three arms on the MBPP "
            "test split (257 tasks): FULL (committed stack + Q3 train diet, "
            "PRIMARY protocol — the arc's external number), CONTENT-STRIPPED "
            "(same mechanisms, starter-8 codebook only, no bigrams/chunks/diet, "
            "PRIMARY protocol — the HQ3 contrast), OFFICIAL (FULL boot, "
            "OFFICIAL protocol — the published-MBPP-comparability row, "
            "protocol-flagged, never merged into a PRIMARY aggregate). The "
            "STRESS/zero-shot row is Q0-A's frozen artifact "
            "(results/mbpp_zero_shot_baseline.json, cited in q0_continuity "
            "below by sha256, never re-run here)."),
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
                "full": "ensure_program_synthesis + install_mined_chunks "
                        "(P7-C's 15 arc-1-corpus chunks) + ensure_mbpp_"
                        "train_diet (Q3's 15 mck_ chunks + 30 mbpp_train "
                        "bigrams); PRIMARY protocol",
                "content_stripped": "ensure_program_synthesis + "
                                    "prog_synthesis_battery.strip_to_starter "
                                    "(the frozen_p7/C-CODEBOOK-FROZEN "
                                    "precedent, imported verbatim) — starter-8 "
                                    "codebook only, zero ConstructionBigram "
                                    "nodes of any provenance, no mined chunks, "
                                    "no mbpp_train_diet; PRIMARY protocol",
                "official": "SAME boot as full; OFFICIAL protocol (all "
                           "parseable asserts revealed, scored on the same "
                           "asserts) — protocol-flagged, never a PRIMARY "
                           "aggregate member",
            },
            "batching": "one FRESH substrate per (task, arm); tasks in "
                        "sorted task_id order; twin full-battery run per arm "
                        "for determinism",
            "pipeline": "domains.prog_synthesis.synthesize_from_request "
                        "(unchanged); spec layer domains.mbpp_spec.parse_"
                        "asserts/split_rows (unchanged, Q2)",
            "held_out_comparator": "domains.prog_synthesis._row_cmp_ok "
                                   "(the SAME fixed formula the engine's "
                                   "own ps_row_pass_special/ps_row_fail_"
                                   "special rules consume) — plain equality "
                                   "when neither tol nor unordered is set, "
                                   "float-within-tolerance for math.isclose "
                                   "rows, set equality (order/duplicate-"
                                   "insensitive) for unordered rows",
            "contamination_enforcement": [
                "task['code'] deleted at split time (mbpp_zero_shot_"
                "baseline.split_tasks/_strip_code, reused verbatim)",
                "domains.mbpp_spec.parse_asserts/split_rows never read "
                "task['code'] (module-level guarantee, cross-checked by "
                "tests/test_mbpp_spec_migrated.py)",
                "every substrate is a fresh, OZMA_SEED_PERSIST_DISABLED "
                "boot; no domains.teach.teach call in this file",
            ],
            "known_runtime_residuals": [
                "a handful of test-split rows carry values the ingest/"
                "eval pipeline cannot yet round-trip end to end (a raw "
                "set nested inside an example ROW's inputs fails "
                "json.dumps in _add_example_row — the exact residual "
                "domains/mbpp_spec.py's own docstring names; a literal "
                "complex-number arg, similarly non-JSON-safe; a dict-"
                "typed expected value with tuple keys hits a PyO3 "
                "boundary error). These surface honestly as "
                "runner_exception:<Type> outcomes, never silently "
                "dropped or hand-patched — this phase MEASURES the "
                "stack as committed, it does not fix engine code.",
            ],
            "time_box": {
                "budget_seconds": TIME_BUDGET_SECONDS, "min_prefix": MIN_PREFIX,
                "official_prefix_cut": official_prefix_n,
                "note": ("FULL and CONTENT-STRIPPED always ran the full "
                         "257-task test split; OFFICIAL is cut to a "
                         "documented deterministic prefix (sorted "
                         "task_id order, never below %d) ONLY if the "
                         "measured FULL+CONTENT-STRIPPED elapsed time "
                         "projected an over-budget OFFICIAL run." % MIN_PREFIX),
            },
        },
        "split_counts": split_counts,
        "q0_continuity": {
            "file": os.path.relpath(Q0_BASELINE_PATH, ROOT),
            "sha256": q0_sha256,
            "cited_outcome_hash_run1": q0_artifact["determinism"]["outcome_hash_run1"],
            "note": ("Q0-A's frozen zero-shot/STRESS artifact is CITED, "
                     "never re-run — this hash is re-verified live by "
                     "tests/test_mbpp_endgame_migrated.py's continuity "
                     "check on every test run."),
        },
        "arms": {"full": arm_full, "content_stripped": arm_stripped,
                 "official": arm_official},
        "hq3": hq3,
        "migration_matrix_vs_q0": matrix,
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

    ingest_engineering_residuals(artifact)
    for name in ("full", "content_stripped", "official"):
        agg = artifact["arms"][name]["aggregates"]
        pr = agg["pass_over_runnable"]
        print("%s: runnable %d/%d p=%s ci=%s; det_identical=%s" % (
            name, pr["k"], pr["n"], pr["p"], pr["ci95"],
            artifact["arms"][name]["determinism"]["identical"]))
    print("HQ3 delta:", hq3["delta_full_minus_content_stripped"])
    print("HQ3 confirmed:", hq3["confirmed"])
    print("elapsed: %.1fs" % artifact["elapsed_seconds"])


if __name__ == "__main__":
    main()

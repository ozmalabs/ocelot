#!/usr/bin/env python
"""retrieval_oracle_ceiling — Arc 3 R0: the ORACLE CEILING for retrieval-shaped
proposal, measured BEFORE anything is built.

`PROGRAM_SYNTHESIS_ARC3_PLAN.md` (R0), `PROGRAM_SYNTHESIS_ARC3_PREREG.md`
(HR1's bar, derived from this artifact), `PROGRAM_SYNTHESIS_ARC2_Q5.md` (the
FULL arm's 18 passes / 239 failures this script's coverage table is measured
against), `PROGRAM_SYNTHESIS_ARC2_PREREG.md` §0 (the PRIMARY split protocol),
`PROGRAM_SYNTHESIS_ARC2_Q3_NOTES.md` (the 90/120 = 75.0% train emit rate this
script's exemplar pool reproduces), `PROGRAM_SYNTHESIS_P7B.md` /
`PROGRAM_SYNTHESIS_ARC2_Q4_NOTES.md` (the repair/exclude machinery rung (d)'s
"one-hole skeleton" proxy is modelled on).

THE QUESTION. Before building an exemplar store / ranker / adaptation ladder
(arc 3's R1/R2), measure the CEILING: for every MBPP **test** task (PRIMARY
protocol, all-but-last parseable assert revealed), does there EXIST a
**train**-split reference program (kept WHOLE — never abstracted into a
codebook shape) that can be adapted to pass it, at four increasingly
permissive rungs:

  (a) AS-IS — the exemplar's own body, args mapped positionally by name
      order, no changes at all.
  (b) ARG PERMUTATION — the SAME body, args re-ordered (bounded: exemplar
      arity <= 4, so the permutation search space is <= 24 — MBPP's own
      arity distribution is 1-4, arity>4 never observed on this fixture,
      named explicitly wherever it would bind).
  (c) LEAF DELTA — one numeric/string LITERAL, or one binary OPERATOR
      (a bounded catalog: {Plus,Minus,Times,Div,Mod} for arithmetic,
      {Eq,Lt,Lte,Gt,Gte} for comparison), changed at exactly one leaf of
      the best (a)/(b) near-miss.
  (d) ONE-HOLE SKELETON (an explicit UPPER BOUND, never conflated with a-c):
      mask the exemplar's single FINAL COMPUTE STATEMENT (its last
      statement, or the statement that assigns the variable a trailing
      bare-var `return` reads) and ask only whether the PREFIX before it
      is derivable (does not trap) on every row — i.e. "if a repair
      oracle could freely fill in just this one step, would the rest of
      the program even get that far". This is NOT a claim the enumerator
      can actually synthesize that step; it names how much of the ceiling
      is locked behind a re-synthesis quality the honest rung (a-c)
      measurement cannot speak to.

Every rung is measured TWICE: REVEALED-pass (does it fit every row the
PRIMARY protocol shows the search) and HELD-OUT-pass (does it ALSO survive
the one row PRIMARY never reveals) — the gap between the two is the
"retrieval-overfit trap mass" the built R1/R2 screen+holdout protocol will
face. This script performs NO seed-writing, NO domains.teach.teach call, NO
codebook/rule installation, and touches no synthesis/engine/seed/spec code —
it is a pure, one-shot MEASUREMENT, structurally identical in class to
`scripts/mbpp_endgame_battery.py` and `scripts/mbpp_train_diet.py`'s own
leave-N-out probe.

CONTAMINATION (`tests/fixtures/mbpp/provenance.json`'s rule, restated per the
prereg's contamination section): reading a TRAIN-split (task_id >= 601)
reference `code` field is not merely legal here, it is *the whole content
source* — the canonical MBPP split assigns train programs to be learned
from. What the rule forbids is TEST-split (task_id in [11,510]) `code`/prompt
content entering any codebook/cue-vocabulary/bigram/taught-shape path; this
script never reads a test task's `code` field at all (`mbpp_zero_shot_
baseline.split_tasks`'s `_strip_code` removes it at split time, reused
verbatim), and running a TRAIN program against TEST **rows** (parsed
asserts, never code or prose) at EVALUATION time is the exact "measurement,
not learning" contamination-legal reading `PROGRAM_SYNTHESIS_ARC2_PREREG.md`
§7 and `PROGRAM_SYNTHESIS_ARC2_Q3_NOTES.md`'s own leave-N-out probe already
established — restated here because this script is the first phase in arc 3
to lean on it explicitly for benchmark-facing (not train-internal) rows.

Run:
  PYTHONPATH=runners/dsl/python:.:scripts OZMA_NO_LLM=1 \
  OZMA_SEED_PERSIST_DISABLED=1 python scripts/retrieval_oracle_ceiling.py
"""
from __future__ import annotations

import copy
import hashlib
import itertools
import json
import math
import os
import platform
import sys
import time
from typing import Any, Dict, List, Optional, Sequence, Tuple

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"),
           os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

os.environ.setdefault("OZMA_NO_LLM", "1")
os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")

from domains import mbpp_spec as ms  # noqa: E402
from domains import prog_ir_emit  # noqa: E402

import mbpp_endgame_battery as meb  # noqa: E402 — wilson/newcombe/prog_eval/agree, reused
from mbpp_blocker_histogram import resolve_entry  # noqa: E402 — entry-fn resolution, reused
from mbpp_zero_shot_baseline import split_tasks as q0_split_tasks  # noqa: E402

FIXTURE_PATH = os.path.join(ROOT, "tests", "fixtures", "mbpp", "sanitized-mbpp.json")
PROVENANCE_PATH = os.path.join(ROOT, "tests", "fixtures", "mbpp", "provenance.json")
ENDGAME_PATH = os.path.join(ROOT, "results", "mbpp_endgame.json")
OUT_PATH = os.path.join(ROOT, "results", "retrieval_oracle_ceiling.json")
N_SANITIZED_TOTAL = 427

# --------------------------------------------------------------------------- #
#  BOUNDS — every one of these is documented in PROGRAM_SYNTHESIS_ARC3_
#  PREREG.md and PROGRAM_SYNTHESIS_ARC3_R0_NOTES.md verbatim; the gate
#  (tests/test_retrieval_ceiling_migrated.py) asserts the artifact's own
#  `bounds` block equals this dict exactly, so a silent drift here is a
#  test failure, not a quiet redefinition.
# --------------------------------------------------------------------------- #
BOUNDS: Dict[str, Any] = {
    "rung_b_max_arity_for_permutation_search": 4,
    "rung_b_max_permutations_per_candidate": 24,  # 4! — the arity-4 ceiling
    "rung_c_numeric_offsets": [-2, -1, 1, 2],
    "rung_c_numeric_absolutes": [0, 1, -1, 2, 3],
    "rung_c_arith_op_family": ["Plus", "Minus", "Times", "Div", "Mod"],
    "rung_c_cmp_op_family": ["Eq", "Lt", "Lte", "Gt", "Gte"],
    "rung_c_string_candidate_source": "revealed_row_inputs_and_expected_only",
    "rung_d_masked_statement_scope": "final_compute_statement_only",
    "rung_d_is_upper_bound": True,
    "repair_measured_conversion_rate_p7b": 0.25,  # 1/4 P7-A holdout_fail ids converted, P7B sec4
}

_ARITH_OPS = tuple(BOUNDS["rung_c_arith_op_family"])
_CMP_OPS = tuple(BOUNDS["rung_c_cmp_op_family"])
_NUM_OFFSETS = tuple(BOUNDS["rung_c_numeric_offsets"])
_NUM_ABSOLUTES = tuple(BOUNDS["rung_c_numeric_absolutes"])
_MAX_PERM_ARITY = BOUNDS["rung_b_max_arity_for_permutation_search"]


# --------------------------------------------------------------------------- #
#  exemplar pool — every train-split (task_id >= 601) program that emits
#  through emit_prog_ir. Mirrors scripts/mbpp_train_diet.py's own emit_pass
#  exactly (same resolve_entry + emit_prog_ir call), reused rather than
#  reimplemented so the pool composition is provably the SAME 90 programs
#  Q3 measured.
# --------------------------------------------------------------------------- #
def build_pool(train_tasks: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    pool: List[Dict[str, Any]] = []
    emit_rows: List[Dict[str, Any]] = []
    for t in train_tasks:
        tid = t["task_id"]
        entry_name, _tree, _defs, err = resolve_entry(t["code"], t["test_list"])
        if entry_name is None:
            emit_rows.append({"task_id": tid, "ok": False, "reason": "entry_resolve:%s" % err})
            continue
        r = prog_ir_emit.emit_prog_ir(t["code"], name=entry_name)
        if not r.get("ok"):
            emit_rows.append({"task_id": tid, "ok": False, "reason": "emit_blocked",
                              "blockers": r.get("blockers")})
            continue
        params = list(r["params"])
        pool.append({"task_id": tid, "entry": entry_name, "ir": r["ir"],
                    "params": params, "arity": len(params),
                    "predictable": bool(r.get("predictable"))})
        emit_rows.append({"task_id": tid, "ok": True, "entry": entry_name,
                          "arity": len(params), "predictable": bool(r.get("predictable"))})
    return pool, emit_rows


def pool_by_arity(pool: List[Dict[str, Any]]) -> Dict[int, List[Dict[str, Any]]]:
    by: Dict[int, List[Dict[str, Any]]] = {}
    for ex in pool:
        by.setdefault(ex["arity"], []).append(ex)
    for k in by:
        by[k].sort(key=lambda e: e["task_id"])  # deterministic scan order
    return by


# --------------------------------------------------------------------------- #
#  execution — one fixed comparator (meb.agree / meb.prog_eval, imported
#  read-only, never a second drifting copy).
# --------------------------------------------------------------------------- #
def _leaf_diff_count(got: Any, expected: Any) -> int:
    """Mechanical structural leaf-diff count between a candidate's output
    and the row's expected value — used ONLY to break ties among rung
    (a)/(b) near-misses ("fewer divergent leaves"), never as a pass/fail
    verdict (that stays meb.agree, the fixed comparator every rung uses)."""
    if isinstance(expected, (list, tuple)) and isinstance(got, (list, tuple)):
        n = max(len(expected), len(got))
        d = 0
        for i in range(n):
            a = got[i] if i < len(got) else None
            b = expected[i] if i < len(expected) else None
            d += 0 if a == b else 1
        return d
    return 0 if got == expected else 1


def _mapped_env(params: Sequence[str], perm: Sequence[int], row: Dict[str, Any]) -> Dict[str, Any]:
    vals = list(row["inputs"].values())
    mapped = [vals[perm[i]] for i in range(len(perm))]
    return dict(zip(params, mapped))


def _run_candidate(ir: Dict[str, Any], params: Sequence[str], perm: Sequence[int],
                   rows: List[Dict[str, Any]]) -> Tuple[bool, int, int]:
    """-> (all_pass, n_pass, leaf_diff_sum) over `rows` (revealed OR held-out
    — caller picks which). A raw exception (a non-JSON-safe row value, a PyO3
    boundary error — the same residual class Q5 §8 named) counts as a failed
    row with a large sentinel diff, never a crash."""
    n_pass = 0
    diff_sum = 0
    for r in rows:
        got = None
        try:
            env = _mapped_env(params, perm, row=r)
            out = meb.prog_eval(ir, env)
            got = out.get("result")
            ok = (out.get("halted") is True and out.get("trap") is None
                  and meb.agree(got, r["expected"], r.get("tol"), bool(r.get("unordered"))))
        except Exception:  # noqa: BLE001 — never let one row crash the sweep
            ok = False
        if ok:
            n_pass += 1
        else:
            diff_sum += _leaf_diff_count(got, r["expected"])
    return n_pass == len(rows), n_pass, diff_sum


# --------------------------------------------------------------------------- #
#  rung (c) — leaf-delta edit points, walked mechanically over the IR's own
#  JSON structure (a fixed pre-order walk, dict insertion order / list
#  index order — deterministic across identical re-parses of the same
#  source, which is what every run of this script does).
# --------------------------------------------------------------------------- #
def _walk_edit_points(node: Any, path: Tuple[Any, ...] = ()) -> List[Dict[str, Any]]:
    points: List[Dict[str, Any]] = []
    if isinstance(node, dict):
        t = node.get("type")
        if t == "Lit":
            v = node.get("value")
            if isinstance(v, bool):
                pass
            elif isinstance(v, (int, float)):
                points.append({"path": path + ("value",), "kind": "lit_num", "orig": v})
            elif isinstance(v, str):
                points.append({"path": path + ("value",), "kind": "lit_str", "orig": v})
        elif t in _ARITH_OPS:
            points.append({"path": path + ("type",), "kind": "op", "family": "arith", "orig": t})
        elif t in _CMP_OPS:
            points.append({"path": path + ("type",), "kind": "op", "family": "cmp", "orig": t})
        for k, v in node.items():
            points.extend(_walk_edit_points(v, path + (k,)))
    elif isinstance(node, list):
        for i, v in enumerate(node):
            points.extend(_walk_edit_points(v, path + (i,)))
    return points


def _candidates_for(point: Dict[str, Any], revealed_rows: List[Dict[str, Any]]) -> List[Any]:
    if point["kind"] == "lit_num":
        v = point["orig"]
        offs = [v + o for o in _NUM_OFFSETS]
        return sorted(set(offs) | set(_NUM_ABSOLUTES) - {v})
    if point["kind"] == "lit_str":
        v = point["orig"]
        pool: set = set()
        for r in revealed_rows:
            for x in r["inputs"].values():
                if isinstance(x, str):
                    pool.add(x)
            if isinstance(r["expected"], str):
                pool.add(r["expected"])
        return sorted(pool - {v})
    if point["kind"] == "op":
        fam = _ARITH_OPS if point["family"] == "arith" else _CMP_OPS
        return [o for o in fam if o != point["orig"]]
    return []


def _apply_edit(ir: Dict[str, Any], point: Dict[str, Any], candidate: Any) -> Dict[str, Any]:
    ir2 = copy.deepcopy(ir)
    node = ir2
    for k in point["path"][:-1]:
        node = node[k]
    node[point["path"][-1]] = candidate
    return ir2


def rung_c_search(anchor_ir: Dict[str, Any], params: Sequence[str], perm: Sequence[int],
                  revealed: List[Dict[str, Any]], held_out: List[Dict[str, Any]]
                  ) -> Dict[str, Any]:
    points = _walk_edit_points(anchor_ir)
    for point in points:
        for cand in _candidates_for(point, revealed):
            edited = _apply_edit(anchor_ir, point, cand)
            rev_ok, _n, _d = _run_candidate(edited, params, perm, revealed)
            if rev_ok:
                held_ok, _n2, _d2 = _run_candidate(edited, params, perm, held_out) if held_out else (True, 0, 0)
                return {"found": True, "revealed_pass": True, "heldout_pass": bool(held_ok),
                       "edit": {"path": list(point["path"]), "kind": point["kind"],
                                "from": point["orig"], "to": cand}}
    return {"found": False, "revealed_pass": False, "heldout_pass": False, "edit": None,
           "n_edit_points_tried": len(points)}


# --------------------------------------------------------------------------- #
#  rung (d) — the one-hole-skeleton UPPER BOUND. Mask exactly the exemplar's
#  FINAL COMPUTE STATEMENT (its last top-level statement, or — if the last
#  statement is a bare-var `return` — the statement that assigns that var)
#  and ask only whether the PREFIX before it is derivable (does not trap) on
#  every row. This never asks whether the masked step is actually
#  SYNTHESIZABLE — it is a structural "does the skeleton even get this far"
#  check, an explicit over-approximation (documented, discounted in the
#  prereg's HR1 arithmetic by P7B's measured 25% repair conversion rate).
# --------------------------------------------------------------------------- #
def _top_level_stmts(ir: Dict[str, Any]) -> List[Dict[str, Any]]:
    if isinstance(ir, dict) and ir.get("type") == "ProgSeq":
        return list(ir.get("stmts") or [])
    return [ir]


def _final_compute_index(stmts: List[Dict[str, Any]]) -> Optional[int]:
    if not stmts:
        return None
    last = stmts[-1]
    if last.get("type") == "ProgReturn":
        val = last.get("value")
        if (isinstance(val, dict) and val.get("type") == "Var" and len(stmts) >= 2
                and stmts[-2].get("type") == "ProgAssignVar"
                and stmts[-2].get("name") == val.get("name")):
            return len(stmts) - 2
        return len(stmts) - 1
    return len(stmts) - 1  # fallback: mask whatever the last statement is


def _prefix_derivable(prefix_stmts: List[Dict[str, Any]], params: Sequence[str],
                      perm: Sequence[int], row: Dict[str, Any]) -> bool:
    if not prefix_stmts:
        return True
    env = _mapped_env(params, perm, row)
    ir2 = {"type": "ProgSeq", "stmts": prefix_stmts}
    try:
        out = meb.prog_eval(ir2, env)
    except Exception:  # noqa: BLE001
        return False
    return out.get("halted") is True and out.get("trap") is None


def rung_d_upper_bound(anchor_ir: Dict[str, Any], params: Sequence[str], perm: Sequence[int],
                       revealed: List[Dict[str, Any]], held_out: List[Dict[str, Any]]
                       ) -> Dict[str, Any]:
    stmts = _top_level_stmts(anchor_ir)
    idx = _final_compute_index(stmts)
    if idx is None:
        return {"attempted": False, "skip_reason": "empty_statement_list",
               "revealed_pass_upper_bound": False, "heldout_pass_upper_bound": False}
    prefix = stmts[:idx]
    rev_ok = all(_prefix_derivable(prefix, params, perm, r) for r in revealed)
    held_ok = rev_ok and (not held_out or all(_prefix_derivable(prefix, params, perm, r) for r in held_out))
    return {"attempted": True, "masked_stmt_index": idx, "prefix_len": len(prefix),
           "revealed_pass_upper_bound": bool(rev_ok), "heldout_pass_upper_bound": bool(held_ok)}


# --------------------------------------------------------------------------- #
#  per-task oracle sweep.
# --------------------------------------------------------------------------- #
def oracle_for_task(task: Dict[str, Any], by_arity: Dict[int, List[Dict[str, Any]]]
                    ) -> Optional[Dict[str, Any]]:
    parsed = ms.parse_asserts(task)
    spec = ms.split_rows(parsed["rows"], "primary")
    if not spec["runnable"]:
        return None
    revealed, held_out = spec["revealed"], spec["held_out"]
    arity = len(revealed[0]["inputs"])
    candidates = by_arity.get(arity, [])

    row: Dict[str, Any] = {
        "task_id": task["task_id"], "arity": arity,
        "n_revealed": len(revealed), "n_held_out": len(held_out),
        "n_candidates_this_arity": len(candidates),
    }

    identity = tuple(range(arity))
    best = {"n_pass": -1, "diff": None, "exemplar": None, "perm": None}

    def _consider(ex_tid, perm, n_pass, diff):
        key = (n_pass, -diff)
        cur = (best["n_pass"], -(best["diff"] if best["diff"] is not None else 10**9))
        if key > cur:
            best.update(n_pass=n_pass, diff=diff, exemplar=ex_tid, perm=perm)

    # ---- rung (a): as-is, identity mapping, EVERY matching-arity exemplar. ----
    rev_pass_a, held_pass_a = [], []
    for ex in candidates:
        ok, n_pass, diff = _run_candidate(ex["ir"], ex["params"], identity, revealed)
        _consider(ex["task_id"], identity, n_pass, diff)
        if ok:
            rev_pass_a.append(ex["task_id"])
            hok, _n2, _d2 = _run_candidate(ex["ir"], ex["params"], identity, held_out) if held_out else (True, 0, 0)
            if hok:
                held_pass_a.append(ex["task_id"])
    row["rung_a"] = {"revealed_pass_exemplars": rev_pass_a, "heldout_pass_exemplars": held_pass_a}
    solved_a = len(rev_pass_a) > 0

    # ---- rung (b): arg permutation (bounded arity <= 4), only if (a) found nothing. ----
    rung_b: Dict[str, Any] = {"attempted": False, "skip_reason": None,
                              "revealed_pass_combos": [], "heldout_pass_combos": []}
    solved_b = False
    if not solved_a:
        if arity > _MAX_PERM_ARITY:
            rung_b["skip_reason"] = "arity_exceeds_permutation_bound(%d)" % _MAX_PERM_ARITY
        elif arity < 2:
            rung_b["skip_reason"] = "arity_below_2_no_nonidentity_permutation"
        elif not candidates:
            rung_b["skip_reason"] = "no_pool_exemplar_matches_arity"
        else:
            rung_b["attempted"] = True
            for ex in candidates:
                for perm in itertools.permutations(range(arity)):
                    if perm == identity:
                        continue  # already covered by rung (a)
                    ok, n_pass, diff = _run_candidate(ex["ir"], ex["params"], perm, revealed)
                    _consider(ex["task_id"], perm, n_pass, diff)
                    if ok:
                        rung_b["revealed_pass_combos"].append(
                            {"exemplar": ex["task_id"], "perm": list(perm)})
                        hok, _n2, _d2 = (_run_candidate(ex["ir"], ex["params"], perm, held_out)
                                        if held_out else (True, 0, 0))
                        if hok:
                            rung_b["heldout_pass_combos"].append(
                                {"exemplar": ex["task_id"], "perm": list(perm)})
        solved_b = len(rung_b["revealed_pass_combos"]) > 0
    row["rung_b"] = rung_b

    # ---- near-miss anchor (only meaningful when unsolved at a/b). ----
    near_miss = None
    if not (solved_a or solved_b) and best["exemplar"] is not None:
        near_miss = {"exemplar": best["exemplar"], "perm": list(best["perm"]),
                    "n_revealed_pass": best["n_pass"], "n_revealed": len(revealed),
                    "leaf_diff": best["diff"]}
    row["near_miss"] = near_miss

    # ---- rung (c): single-leaf edit on the near-miss anchor. ----
    rung_c: Dict[str, Any] = {"attempted": False, "skip_reason": None, "anchor": None,
                              "edit": None, "revealed_pass": False, "heldout_pass": False}
    solved_c = False
    if not (solved_a or solved_b):
        if near_miss is None:
            rung_c["skip_reason"] = "no_arity_matched_anchor"
        else:
            anchor_ex = next(e for e in candidates if e["task_id"] == near_miss["exemplar"])
            rung_c["attempted"] = True
            rung_c["anchor"] = {"exemplar": near_miss["exemplar"], "perm": near_miss["perm"]}
            res = rung_c_search(anchor_ex["ir"], anchor_ex["params"], tuple(near_miss["perm"]),
                                revealed, held_out)
            rung_c["edit"] = res["edit"]
            rung_c["revealed_pass"] = res["revealed_pass"]
            rung_c["heldout_pass"] = res["heldout_pass"]
            if not res["found"]:
                rung_c["n_edit_points_tried"] = res.get("n_edit_points_tried", 0)
            solved_c = res["revealed_pass"]
    row["rung_c"] = rung_c

    # ---- rung (d): one-hole-skeleton upper bound on the SAME anchor. ----
    rung_d: Dict[str, Any] = {"attempted": False, "skip_reason": None, "anchor": None,
                              "revealed_pass_upper_bound": False, "heldout_pass_upper_bound": False}
    if not (solved_a or solved_b or solved_c):
        if near_miss is None:
            rung_d["skip_reason"] = "no_arity_matched_anchor"
        else:
            anchor_ex = next(e for e in candidates if e["task_id"] == near_miss["exemplar"])
            res = rung_d_upper_bound(anchor_ex["ir"], anchor_ex["params"], tuple(near_miss["perm"]),
                                     revealed, held_out)
            rung_d.update(res)
            rung_d["anchor"] = {"exemplar": near_miss["exemplar"], "perm": near_miss["perm"]}
    row["rung_d"] = rung_d
    solved_d_upper = bool(rung_d.get("revealed_pass_upper_bound"))

    # ---- best rung reached (three readings: revealed, heldout-honest a-c, +upper-bound d). ----
    if solved_a:
        best_revealed = "a"
    elif solved_b:
        best_revealed = "b"
    elif solved_c:
        best_revealed = "c"
    elif solved_d_upper:
        best_revealed = "d"
    else:
        best_revealed = "none"
    row["best_rung_revealed"] = best_revealed

    held_a = len(held_pass_a) > 0
    held_b = len(rung_b["heldout_pass_combos"]) > 0
    held_c = bool(rung_c["heldout_pass"])
    if held_a:
        best_heldout_honest = "a"
    elif held_b:
        best_heldout_honest = "b"
    elif held_c:
        best_heldout_honest = "c"
    else:
        best_heldout_honest = "none"
    row["best_rung_heldout_honest"] = best_heldout_honest

    held_d = bool(rung_d.get("heldout_pass_upper_bound"))
    if best_heldout_honest != "none":
        row["best_rung_with_upper_bound_d"] = best_heldout_honest
    elif held_d:
        row["best_rung_with_upper_bound_d"] = "d"
    else:
        row["best_rung_with_upper_bound_d"] = "none"

    return row


# --------------------------------------------------------------------------- #
#  one full pass over the 257-task test split (twin-run for determinism).
# --------------------------------------------------------------------------- #
def run_pass(test_tasks: List[Dict[str, Any]], by_arity: Dict[int, List[Dict[str, Any]]]
            ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], float]:
    t0 = time.time()
    runnable: List[Dict[str, Any]] = []
    excluded: List[Dict[str, Any]] = []
    for task in test_tasks:
        r = oracle_for_task(task, by_arity)
        if r is None:
            parsed = ms.parse_asserts(task)
            spec = ms.split_rows(parsed["rows"], "primary")
            excluded.append({"task_id": task["task_id"],
                             "excluded_reason": spec.get("excluded_reason")})
            continue
        runnable.append(r)
    return runnable, excluded, time.time() - t0


def outcome_signature(runnable: List[Dict[str, Any]], excluded: List[Dict[str, Any]]) -> List[Any]:
    sig = [[r["task_id"], r["best_rung_revealed"], r["best_rung_heldout_honest"],
           r["best_rung_with_upper_bound_d"]] for r in runnable]
    sig += [[r["task_id"], "excluded", r["excluded_reason"]] for r in excluded]
    sig.sort(key=lambda x: x[0])
    return sig


def sig_hash(sig: List[Any]) -> str:
    return hashlib.sha256(json.dumps(sig, sort_keys=True).encode()).hexdigest()


# --------------------------------------------------------------------------- #
#  aggregates — cumulative ceiling per rung, both revealed and heldout-honest,
#  with Wilson CIs. "Cumulative through rung K" = fraction of runnable tasks
#  whose best_rung is <= K on the ladder a < b < c < d.
# --------------------------------------------------------------------------- #
_LADDER = ["a", "b", "c", "d", "none"]


def _rank(r: str) -> int:
    return _LADDER.index(r) if r in _LADDER else len(_LADDER)


def cumulative_ceiling(runnable: List[Dict[str, Any]], field: str, through: List[str],
                       n_total: int) -> Dict[str, Any]:
    out = {}
    for k in through:
        limit = _rank(k)
        n = sum(1 for r in runnable if r[field] != "none" and _rank(r[field]) <= limit)
        out[k] = meb.wilson(n, n_total)
    return out


def trap_mass(runnable: List[Dict[str, Any]], n_total: int) -> Dict[str, Any]:
    """Per-rung-cutoff trap mass: tasks whose best REVEALED rung is <= K but
    whose best HELDOUT-HONEST rung is NOT <= K (a-c only; d is upper-bound
    and never counted as a genuine heldout pass here) — the retrieval-
    overfit mass the R1/R2 screen+holdout protocol will actually face."""
    out = {}
    for k in ("a", "b", "c"):
        limit = _rank(k)
        rev_ids = sorted(r["task_id"] for r in runnable
                         if r["best_rung_revealed"] != "none" and _rank(r["best_rung_revealed"]) <= limit)
        held_ids = set(r["task_id"] for r in runnable
                       if r["best_rung_heldout_honest"] != "none"
                       and _rank(r["best_rung_heldout_honest"]) <= limit)
        trap_ids = sorted(t for t in rev_ids if t not in held_ids)
        out[k] = {"n_revealed_solved": len(rev_ids), "n_heldout_solved": len(held_ids & set(rev_ids)),
                 "n_trap": len(trap_ids), "trap_task_ids": trap_ids,
                 "trap_rate_of_revealed_solved": round(len(trap_ids) / len(rev_ids), 6) if rev_ids else None}
    return out


def q5_failure_coverage(runnable: List[Dict[str, Any]], endgame: Dict[str, Any]) -> Dict[str, Any]:
    full_rows = endgame["arms"]["full"]["runnable_rows"]
    fail_ids = sorted(r["task_id"] for r in full_rows if r["outcome"] != "pass")
    by_task = {r["task_id"]: r for r in runnable}
    covered_ac, covered_d_only, uncovered = [], [], []
    for tid in fail_ids:
        oc = by_task.get(tid)
        if oc is None:
            uncovered.append(tid)
            continue
        if oc["best_rung_heldout_honest"] != "none":
            covered_ac.append(tid)
        elif oc["best_rung_with_upper_bound_d"] == "d":
            covered_d_only.append(tid)
        else:
            uncovered.append(tid)
    return {
        "q5_full_failure_task_ids": fail_ids, "n_q5_full_failures": len(fail_ids),
        "covered_by_rung_a_c_heldout_honest": covered_ac,
        "n_covered_a_c": len(covered_ac),
        "covered_only_by_rung_d_upper_bound": covered_d_only,
        "n_covered_d_only": len(covered_d_only),
        "uncovered_task_ids": uncovered, "n_uncovered": len(uncovered),
        "note": ("'covered_by_rung_a_c' means an EXACT/permuted/single-leaf-edit "
                "train exemplar exists that passes every held-out row too (the "
                "honest ceiling); 'covered_only_by_rung_d' is the additional "
                "mass reachable ONLY under the upper-bound one-hole-skeleton "
                "proxy (discounted in the prereg's HR1 arithmetic by P7B's "
                "measured 25% repair conversion rate, never taken at face value)."),
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
    with open(ENDGAME_PATH) as f:
        endgame = json.load(f)

    splits = q0_split_tasks(all_tasks)
    test_tasks = splits["test"]
    train_tasks = splits["train"]
    for t in test_tasks:
        assert "code" not in t, "contamination: code field survived split_tasks"
    assert len(train_tasks) == 120 and len(test_tasks) == 257

    pool, emit_rows = build_pool(train_tasks)
    by_arity = pool_by_arity(pool)
    print("pool size", len(pool), "of", len(train_tasks), "train tasks")

    run1_r, run1_x, t1 = run_pass(test_tasks, by_arity)
    run2_r, run2_x, t2 = run_pass(test_tasks, by_arity)
    sig1, sig2 = outcome_signature(run1_r, run1_x), outcome_signature(run2_r, run2_x)
    determinism = {"runs": 2, "identical": sig1 == sig2,
                   "outcome_hash_run1": sig_hash(sig1), "outcome_hash_run2": sig_hash(sig2),
                   "elapsed_run1_seconds": round(t1, 2), "elapsed_run2_seconds": round(t2, 2)}
    print("twin-run identical:", determinism["identical"], "elapsed",
         determinism["elapsed_run1_seconds"] + determinism["elapsed_run2_seconds"])

    runnable, excluded = run1_r, run1_x
    n_runnable = len(runnable)

    ceiling_revealed = cumulative_ceiling(runnable, "best_rung_revealed",
                                          ["a", "b", "c", "d"], n_runnable)
    ceiling_heldout_ac = cumulative_ceiling(runnable, "best_rung_heldout_honest",
                                            ["a", "b", "c"], n_runnable)
    ceiling_with_d = cumulative_ceiling(runnable, "best_rung_with_upper_bound_d",
                                        ["a", "b", "c", "d"], n_runnable)
    traps = trap_mass(runnable, n_runnable)
    coverage = q5_failure_coverage(runnable, endgame)

    pool_arity_dist: Dict[str, int] = {}
    for ex in pool:
        pool_arity_dist[str(ex["arity"])] = pool_arity_dist.get(str(ex["arity"]), 0) + 1
    test_arity_dist: Dict[str, int] = {}
    for r in runnable:
        test_arity_dist[str(r["arity"])] = test_arity_dist.get(str(r["arity"]), 0) + 1

    artifact = {
        "_README": (
            "Arc 3 R0 — the ORACLE CEILING for retrieval-shaped proposal. "
            "For every MBPP test task (PRIMARY protocol), does a WHOLE "
            "train-split program (never abstracted into a chunk shape) "
            "pass it as-is (a), under arg permutation (b), under a "
            "bounded single-leaf edit (c), or under a one-hole-skeleton "
            "UPPER BOUND (d)? Measured revealed-pass (proposal ceiling) "
            "and heldout-pass (honest ceiling) separately at every rung — "
            "the gap is the retrieval-overfit trap mass."),
        "measured_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "provenance_ref": os.path.relpath(PROVENANCE_PATH, ROOT),
        "provenance": provenance,
        "bounds": BOUNDS,
        "pool": {
            "n_train_tasks": len(train_tasks), "n_pool_exemplars": len(pool),
            "emit_rate": round(len(pool) / len(train_tasks), 6),
            "pool_task_ids": sorted(ex["task_id"] for ex in pool),
            "pool_arity_distribution": pool_arity_dist,
            "n_predictable": sum(1 for ex in pool if ex["predictable"]),
            "emit_rows": emit_rows,
        },
        "test_split": {
            "n_test_tasks": len(test_tasks), "n_runnable_primary": n_runnable,
            "n_excluded": len(excluded), "excluded_rows": excluded,
            "test_arity_distribution": test_arity_dist,
        },
        "determinism": determinism,
        "runnable_rows": runnable,
        "ceiling": {
            "revealed_pass_cumulative": ceiling_revealed,
            "heldout_pass_cumulative_a_to_c": ceiling_heldout_ac,
            "heldout_or_upper_bound_d_cumulative": ceiling_with_d,
            "note": ("'revealed_pass_cumulative' answers 'does SOME train "
                     "exemplar fit every revealed row' at each rung cutoff "
                     "(the proposal ceiling — what a perfect ranker could "
                     "retrieve). 'heldout_pass_cumulative_a_to_c' additionally "
                     "requires the SAME candidate to survive the held-out row "
                     "— the honest ceiling rungs (a)-(c) can actually claim. "
                     "Rung (d) is reported ONLY in "
                     "'heldout_or_upper_bound_d_cumulative', explicitly "
                     "labelled upper-bound, never merged into the a-c honest "
                     "number."),
        },
        "trap_mass": traps,
        "q5_full_failure_coverage": coverage,
        "environment": {"python": sys.version.split()[0], "platform": platform.platform()},
        "elapsed_seconds": round(time.time() - t_start, 2),
    }
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w") as f:
        json.dump(artifact, f, indent=1, sort_keys=False)
        f.write("\n")
    print("wrote", OUT_PATH)
    print("ceiling revealed:", ceiling_revealed)
    print("ceiling heldout a-c:", ceiling_heldout_ac)
    print("ceiling with upper-bound d:", ceiling_with_d)
    print("q5 failure coverage a-c:", coverage["n_covered_a_c"], "/", coverage["n_q5_full_failures"])
    print("elapsed: %.1fs" % artifact["elapsed_seconds"])


if __name__ == "__main__":
    main()

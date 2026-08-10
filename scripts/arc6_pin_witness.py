#!/usr/bin/env python3
"""arc6_pin_witness — INDEPENDENT constructed-witness check for any MBPP
task whose pin moved in the "this program is now correct" direction.

Written fresh rather than importing `arc6_verdict_report.sweep`, because a
pin that asserts correctness must not be re-verified by the same instrument
that produced the claim (four false conversions were caught in this arc).

  * inputs are CONSTRUCTED here by type-driven mutation and every input
    equal to a revealed OR held-out row is discarded;
  * the accepted program is re-run through `ProgEval` on the LIVE engine;
  * the reference is the corpus `code`, executed only as the oracle, after
    the outcome was already measured;
  * the comparison is TYPE-SENSITIVE (list != tuple) — the point of the
    value-layer rung.

  python scripts/arc6_pin_witness.py 161 257 272 --out results/x.json
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"),
           os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)
os.environ.setdefault("OZMA_NO_LLM", "1")
os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")

import mbpp_arc3_battery as mab      # noqa: E402
from domains import mbpp_spec as ms  # noqa: E402
from domains import prog_synthesis as psy  # noqa: E402
from mbpp_endgame_battery import prog_eval  # noqa: E402  (the EXECUTOR only)
from mbpp_zero_shot_baseline import split_tasks  # noqa: E402

FIXTURE = os.path.join(ROOT, "tests", "fixtures", "mbpp", "sanitized-mbpp.json")


# --------------------------------------------------------------------------
# type-sensitive comparison — list and tuple are DIFFERENT things
# --------------------------------------------------------------------------
def typed(v):
    if isinstance(v, list):
        return ["#list"] + [typed(x) for x in v]
    if isinstance(v, tuple):
        return ["#tuple"] + [typed(x) for x in v]
    if isinstance(v, (set, frozenset)):
        return ["#set"] + sorted(repr(typed(x)) for x in v)
    if isinstance(v, dict):
        return ["#dict"] + sorted((repr(k), typed(x)) for k, x in v.items())
    if isinstance(v, bool):
        return ["#bool", v]
    if isinstance(v, float):
        return ["#float", round(v, 9)]
    return v


def agree(got, want) -> bool:
    if isinstance(got, float) or isinstance(want, float):
        try:
            if math.isclose(float(got), float(want), rel_tol=1e-9, abs_tol=1e-9):
                return isinstance(got, (int, float)) and isinstance(want, (int, float))
        except (TypeError, ValueError):
            pass
    return typed(got) == typed(want)


# --------------------------------------------------------------------------
# constructed inputs — mechanical, task-blind, and never a corpus row
# --------------------------------------------------------------------------
_STRS = ["ozma", "aa", "Zz", "the quick brown", "", "abcabc", "9x8"]


def _mutate(v):
    if isinstance(v, bool):
        return [not v]
    if isinstance(v, int):
        return [v + 1, v + 3, v * 2 + 1, abs(v) + 11, 0, 1, 4, 9, 17]
    if isinstance(v, float):
        return [v + 1.0, v * 3.0, 0.5, 7.25]
    if isinstance(v, str):
        return [v[::-1], v * 2, v.upper()] + _STRS
    if isinstance(v, (list, tuple)):
        seq = list(v)
        out = [seq[::-1], seq[:1], seq + seq[:1], seq[1:] + seq[:1]]
        if seq and isinstance(seq[0], (int, float)) and not isinstance(seq[0], bool):
            out += [[x + 1 for x in seq], sorted(seq), [seq[0]] * 3, seq + [0]]
        if seq and isinstance(seq[0], str):
            out += [[s[::-1] for s in seq], sorted(seq), seq + ["qq"]]
        if seq and isinstance(seq[0], (list, tuple)):
            out += [[list(x)[::-1] for x in seq], [list(seq[0]) + [7]] + [list(x) for x in seq[1:]]]
        if isinstance(v, tuple):
            out = [tuple(x) if isinstance(x, list) else x for x in out]
        return out
    if isinstance(v, (set, frozenset)):
        return [type(v)(list(v)[:1]), type(v)(list(v) + [42])]
    if isinstance(v, dict):
        return [dict(list(v.items())[:1])]
    return []


def _key(d):
    return json.dumps(typed(d), sort_keys=True, default=repr)


def constructed(rows, limit=24):
    """`rows` must be EVERY known row (revealed + held out) — each is
    excluded from the generated population."""
    seen = {_key(r["inputs"]) for r in rows}
    out = []
    names = sorted(rows[0]["inputs"])
    for r in rows:
        for nm in names:
            for alt in _mutate(r["inputs"][nm]):
                cand = dict(r["inputs"])
                cand[nm] = alt
                k = _key(cand)
                if k in seen:
                    continue
                seen.add(k)
                out.append(cand)
                if len(out) >= limit:
                    return out
    for r in rows:
        if len(names) < 2:
            break
        alts = {nm: _mutate(r["inputs"][nm]) for nm in names}
        n = min((len(a) for a in alts.values()), default=0)
        for i in range(min(8, n)):
            cand = {nm: alts[nm][i] for nm in names}
            k = _key(cand)
            if k in seen:
                continue
            seen.add(k)
            out.append(cand)
            if len(out) >= limit:
                return out
    return out


def reference_fn(task):
    ns = {}
    exec(compile(task["code"], "<mbpp>", "exec"), ns)  # noqa: S102
    name = None
    for stmt in task.get("test_list", []):
        m = stmt.split("assert ", 1)[-1].strip()
        name = m.split("(", 1)[0].strip()
        if name in ns:
            break
    fn = ns.get(name)
    if fn is None:
        cands = [v for v in ns.values()
                 if callable(v) and getattr(v, "__module__", None) is None]
        fn = cands[-1] if cands else None
    return fn


def run_one(tid: int, tasks_with_code, tasks_no_code, limit=24):
    task = tasks_no_code[tid]
    parsed = ms.parse_asserts(task)
    spec = ms.split_rows(parsed["rows"], "primary")
    report = {"n_test_list": len(task.get("test_list", [])),
              "n_parseable": len(parsed["rows"]),
              "n_unparseable": len(parsed["unparseable"]),
              "unparseable_reasons": [u["form"] for u in parsed["unparseable"]]}
    row = mab.run_task(task, spec, report, mab.boot_full_r3, "primary")
    out = {"task_id": tid, "outcome": row["outcome"]}
    ir = row.get("ir")
    if ir is None:
        # a gapped/rejected task carries no accepted IR — re-read the goal so
        # the absence is recorded rather than inferred.
        s, ag = mab.boot_full_r3()
        r = psy.synthesize_from_request(s, ag, task["prompt"], spec["revealed"])
        out["goal_status"] = r.get("status")
        ir = r.get("ir")
    out["has_ir"] = ir is not None
    if ir is None:
        return out
    out["ir"] = ir
    ref = reference_fn(tasks_with_code[tid])
    rows_all = spec["revealed"] + spec["held_out"]
    probes = constructed(rows_all, limit=limit)
    disagree, agreed, errors = [], 0, []
    for env in probes:
        # `parse_asserts` names positional args 'a','b',... in order, so the
        # reference is called POSITIONALLY in that same order.
        argv = [env[k] for k in sorted(env)]
        try:
            want = ref(*argv)
        except Exception as exc:                       # noqa: BLE001
            errors.append({"inputs": repr(env), "reference_raised": repr(exc)})
            continue
        try:
            res = prog_eval(ir, dict(env))
            if res.get("halted") is not True or res.get("trap") is not None:
                disagree.append({"inputs": repr(env), "trap": repr(res.get("trap")),
                                 "halted": res.get("halted"),
                                 "reference": repr(want)})
                continue
            got = res.get("result")
        except Exception as exc:                       # noqa: BLE001
            disagree.append({"inputs": repr(env), "substrate_raised": repr(exc),
                             "reference": repr(want)})
            continue
        if agree(got, want):
            agreed += 1
        else:
            disagree.append({"inputs": repr(env), "got": repr(got),
                             "reference": repr(want)})
    out.update({"n_probes": len(probes), "n_agree": agreed,
                "n_disagree": len(disagree), "disagreements": disagree[:8],
                "reference_errors": errors[:4],
                "verdict": ("CORRECT_ON_EVERY_CONSTRUCTED_PROBE"
                            if probes and not disagree else
                            "REFUTED" if disagree else "NO_PROBES")})
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("ids", nargs="+", type=int)
    ap.add_argument("--out", default=None)
    ap.add_argument("--limit", type=int, default=24)
    args = ap.parse_args()

    with open(FIXTURE) as f:
        all_tasks = json.load(f)
    with_code = {t["task_id"]: t for t in all_tasks}
    splits = split_tasks(all_tasks)
    no_code = {t["task_id"]: t for t in splits["test"]}

    res = []
    for tid in args.ids:
        r = run_one(tid, with_code, no_code, args.limit)
        res.append(r)
        print(json.dumps(r)[:800], flush=True)
    if args.out:
        with open(os.path.join(ROOT, args.out), "w") as f:
            json.dump({"engine_sha256": _engine_sha(), "results": res}, f, indent=1)
    return 0


def _engine_sha() -> str:
    import hashlib
    p = os.path.join(ROOT, "runners", "dsl", "python", "substrate_rs",
                     "_native.abi3.so")
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())

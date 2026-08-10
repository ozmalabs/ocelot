#!/usr/bin/env python
"""prog_synthesis_battery — P6 track A: the POWERED evaluation battery.

PROGRAM_SYNTHESIS_PLAN.md §4-P6 / PROGRAM_SYNTHESIS_PREREG.md §8 (H6), run
under the standing rules: power the gate before the endgame (Wilson CIs,
n >= 100/arm); a baseline is a list of identities; eval-subset coverage is
part of every claim; synthetic-proven mechanism != benchmark value.

This is a MEASUREMENT DRIVER (scripts/ class): it boots agents, feeds the
frozen task set through the UNCHANGED P4 pipeline
(domains/prog_synthesis.synthesize_from_request), reads outcomes back, and
writes the artifact. It makes no agent decisions — every accept/gap verdict
is the seed-rule loop's own.

ARMS
  main    the full ladder as booted by ensure_program_synthesis: the write
          codebook (8 starter shapes + the program_synthesis seed's
          statement-grain spine shape) + boarded P3 ConstructionBigram
          statistics (the lattice rung) + SynthEnumerate fallback + gap.
  frozen  C-CODEBOOK-FROZEN (prereg §2): after the same boot, the write
          codebook is stripped to the 8 HELD STARTER shapes
          (seeds/code_write_constructions.json) — no spine entry, no
          taught/minted entries — and the boarded ConstructionBigram rows
          are removed (bigrams absent). Measures what the learned layer
          (P3 corpus statistics + the P4 spine construction) adds.

BATCHING / DETERMINISM
  One FRESH substrate per task (batch size 1 — no cross-task state), tasks
  in sorted-id order. The MAIN arm is run TWICE end-to-end; the artifact
  records both outcome lists and their hashes (must be identical).

SCORING (per task; the prereg's verdict-layer pass)
  primary   binary: the pipeline ACCEPTS a Program AND ProgEval of the
            accepted IR agrees with the reference expectation on ALL
            held-out rows (rows never shown to the pipeline).
  separately counted: requests the cue machinery does not even recognize
            (no goal minted) — failed-at-goal, a real outcome.
  secondary python render→exec agreement on EVERY accepted task (cheap);
            rust/lua/llvm toolchain truth on a deterministic subsample of
            ~15 accepted tasks (subprocess cost): sorted accepted ids,
            stride len//15, first 15 — no silent caps, the rule is in the
            artifact.

C-BATTERY (prereg §2 — the continuity control)
  The frozen 26-item battery is run byte-identical through its OWN pinned
  path (run_write_battery → write_function_from_request) on a fully-booted
  agent (WorldAdapter + load_all_seeds), diffed per item against
  results/code_synthesis_baseline.json (any ok→fail flip is a named
  regression). ADDITIONALLY the same 26 requests are pushed through the
  NEW pipeline verbatim (no example rows — the battery text is never
  extended), which documents the structural fact that the P4 verdict
  layer requires examples (expected: no_examples gaps), not a score.

Run:
  PYTHONPATH=runners/dsl/python:.:scripts OZMA_NO_LLM=1 \
  OZMA_SEED_PERSIST_DISABLED=1 python scripts/prog_synthesis_battery.py
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"),
           os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

os.environ.setdefault("OZMA_NO_LLM", "1")
os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")

import substrate_rs as srs  # noqa: E402

from domains import prog_synthesis as psy  # noqa: E402
from domains import render_python as rp  # noqa: E402
from domains import render_rust_lua as rl  # noqa: E402
from domains.prog_ir_emit import NATIVE_ORACLES  # noqa: E402

TASKS_PATH = os.path.join(ROOT, "tests", "fixtures",
                          "prog_synthesis_battery", "tasks.json")
OUT_PATH = os.path.join(ROOT, "results", "prog_synthesis_battery.json")
BASELINE_PATH = os.path.join(ROOT, "results", "code_synthesis_baseline.json")

# the 8 held starter shapes (seeds/code_write_constructions.json) — the
# frozen arm's whole codebook.
STARTER_8 = ("max_of_two", "min_of_two", "sum_of_two", "product_of_two",
             "abs_value", "average_of_two", "total_of_list", "count_of_list")

SUBSAMPLE_TARGET = 15
_Z = 1.959963984540054  # 95%


# --------------------------------------------------------------------------- #
#  statistics
# --------------------------------------------------------------------------- #
def wilson(k: int, n: int) -> dict:
    if n == 0:
        return {"k": 0, "n": 0, "p": None, "ci95": [None, None]}
    p = k / n
    d = 1 + _Z * _Z / n
    centre = (p + _Z * _Z / (2 * n)) / d
    hw = _Z * math.sqrt(p * (1 - p) / n + _Z * _Z / (4 * n * n)) / d
    return {"k": k, "n": n, "p": round(p, 6),
            "ci95": [round(max(0.0, centre - hw), 6),
                     round(min(1.0, centre + hw), 6)]}


def newcombe_delta(k1: int, n1: int, k2: int, n2: int) -> dict:
    """Newcombe hybrid score interval for p1 - p2 (Wilson bounds per arm)."""
    w1, w2 = wilson(k1, n1), wilson(k2, n2)
    p1, p2 = k1 / n1, k2 / n2
    d = p1 - p2
    lo = d - math.sqrt((p1 - w1["ci95"][0]) ** 2 + (w2["ci95"][1] - p2) ** 2)
    hi = d + math.sqrt((w1["ci95"][1] - p1) ** 2 + (p2 - w2["ci95"][0]) ** 2)
    return {"delta": round(d, 6), "ci95": [round(lo, 6), round(hi, 6)]}


# --------------------------------------------------------------------------- #
#  value agreement (int/bool/float scalar domain; DSL numerics are
#  numeric-lax across int/float — 4.0 == 4 — but bool is its own kind here)
# --------------------------------------------------------------------------- #
def agree(got, expected) -> bool:
    if isinstance(expected, bool) or isinstance(got, bool):
        return (isinstance(got, bool) and isinstance(expected, bool)
                and got == expected)
    if isinstance(got, (int, float)) and isinstance(expected, (int, float)):
        return float(got) == float(expected)
    return got == expected


# --------------------------------------------------------------------------- #
#  ProgEval over an accepted IR (the SAME oracle set the pipeline verifies
#  with — psy._prog_eval_term's contract, inline prog form)
# --------------------------------------------------------------------------- #
def _oracles_term() -> dict:
    items = []
    for name in sorted(NATIVE_ORACLES):
        items.append({"type": "Lit", "value": name})
        items.append({"type": "Lit", "value": "builtin"})
    return {"type": "MkDict", "items": items}


def prog_eval(ir: dict, env: dict) -> dict:
    s = srs.Substrate()
    return s._inner.evaluate(
        {"type": "ProgEval", "prog": ir, "env": {"type": "Var", "name": "e"},
         "oracles": _oracles_term(), "fuel": psy._FUEL, "field": ""},
        {"e": env})


def holdout_verdict(ir: dict, held_out_rows: list) -> dict:
    rows = []
    n_ok = 0
    for hr in held_out_rows:
        out = prog_eval(ir, dict(hr["inputs"]))
        got = out.get("result")
        ok = (out.get("halted") is True and out.get("trap") is None
              and agree(got, hr["expected"]))
        n_ok += 1 if ok else 0
        rows.append({"inputs": hr["inputs"], "expected": hr["expected"],
                     "got": got if isinstance(got, (int, float, str, bool))
                     else None,
                     "trap": out.get("trap"), "ok": bool(ok)})
    return {"n": len(rows), "n_ok": n_ok, "all_ok": n_ok == len(rows),
            "rows": rows}


# --------------------------------------------------------------------------- #
#  arms
# --------------------------------------------------------------------------- #
def boot(frozen: bool):
    s = srs.Substrate()
    ag = s.add_node("Agent", {})
    psy.ensure_program_synthesis(s, s._inner, ag)
    if frozen:
        strip_to_starter(s)
    return s, ag


def strip_to_starter(s) -> None:
    """C-CODEBOOK-FROZEN: write codebook pinned to the 8 held starter
    shapes; boarded bigram statistics removed. Mechanical arm setup."""
    for n in list(s.nodes("ShapeSignature")):
        at = s.node(n)["attrs"]
        if at.get("kind") == "code_write_construction" \
                and at.get("name") not in STARTER_8:
            s.remove_node(n)
    for n in list(s.nodes("ConstructionBigram")):
        s.remove_node(n)


def run_task(task: dict, frozen: bool) -> dict:
    s, ag = boot(frozen)
    examples = [(r["inputs"], r["expected"]) for r in task["example_rows"]]
    r = psy.synthesize_from_request(s, ag, task["request_text"], examples)
    return _build_row(s, task, r, arm="frozen" if frozen else "main")


def _build_row(s, task: dict, r: dict, arm: str,
               protocol: str = None) -> dict:
    """The one row builder every arm shares (mechanical read-back +
    verdict-layer scoring). `protocol` is stamped only on the P7 arms —
    legacy arms keep their frozen row shape byte-compatible."""
    row = {
        "task_id": task["id"],
        "stratum": task["stratum"],
        "arm": arm,
        "recognized": r.get("status") is not None,
        "status": r.get("status"),
        "construction": r.get("construction"),
        "attempts": r.get("attempts"),
        "rungs": r.get("rungs"),
        "gap_reason": r.get("gap_reason"),
        "enumerate_outcome": r.get("enumerate_outcome"),
        "n_counterexamples": len(r.get("counterexamples") or []),
        "excluded": r.get("excluded") or [],
        "gap_filed": any(
            s.node(n)["attrs"].get("kind") == "code_write"
            for n in s.nodes("SelfConcern")),
    }
    if protocol is not None:
        row["protocol"] = protocol
    if r.get("status") is None:
        row["outcome"] = "not_recognized"
        row["failure_reason"] = "request_not_recognized"
    elif r["status"] == "accepted":
        hv = holdout_verdict(r["ir"], task["held_out_rows"])
        row["holdout"] = hv
        row["ir"] = r["ir"]
        if hv["all_ok"]:
            row["outcome"] = "accepted_holdout_ok"
            row["failure_reason"] = None
        else:
            row["outcome"] = "accepted_holdout_fail"
            row["failure_reason"] = "holdout_disagreement"
        row["python_render"] = python_render_check(
            s, r, task["held_out_rows"])
    elif r["status"] == "gapped":
        row["outcome"] = "gapped"
        row["failure_reason"] = r.get("gap_reason") or "gapped"
    else:
        # a status other than accepted/gapped after the pump fixpoint is a
        # STALL — the loop reached a non-terminal state no rule can leave.
        # Measured on the frozen MAIN/FROZEN arms (15/125): a codebook
        # decoy attempt (CEGIS row fail) followed by the enumerate rung
        # left `evaluated` — the enumerated IR was re-evaluated at the
        # SAME attempt number the decoy already consumed, so
        # ps_row_pass/ps_row_fail's verdict_attempt < eval_attempt guard
        # never re-armed. FIXED in seed v1.1.0 (P6.5,
        # ps_enumerate_fresh_attempt — the MAIN-POSTFIX arm measures the
        # fix); the class is still recorded honestly if it ever recurs.
        row["outcome"] = "stalled:%s" % r["status"]
        row["failure_reason"] = "pipeline_stall_nonterminal_status"
    return row


# --------------------------------------------------------------------------- #
#  render validity — python (every accepted task)
# --------------------------------------------------------------------------- #
def python_render_check(s, r: dict, held_out_rows: list) -> dict:
    rp.install_python_statement_renderer(s)
    out = rp.render_program(s, r["program"])
    if not out.get("ok"):
        return {"render_ok": False,
                "gaps": out.get("render_gaps") or [],
                "refusals": out.get("refusals") or [],
                "exec_agree": None}
    ns: dict = {"__builtins__": {}}
    try:
        exec(out["source"], ns)  # noqa: S102 — rendered by the graph, sandboxed
        fn = ns[out["name"]]
    except Exception as e:  # noqa: BLE001
        return {"render_ok": True, "exec_agree": False,
                "error": "exec:%s" % e, "source": out["source"]}
    agree_all = True
    detail = []
    for hr in held_out_rows:
        pe = prog_eval(r["ir"], dict(hr["inputs"]))
        try:
            py = fn(**hr["inputs"])
            ok = agree(py, pe.get("result"))
        except Exception as e:  # noqa: BLE001
            py, ok = "raise:%s" % e, False
        agree_all = agree_all and ok
        detail.append({"inputs": hr["inputs"], "python": py
                       if isinstance(py, (int, float, str, bool)) else None,
                       "prog_eval": pe.get("result")
                       if isinstance(pe.get("result"),
                                     (int, float, str, bool)) else None,
                       "ok": bool(ok)})
    return {"render_ok": True, "exec_agree": bool(agree_all),
            "rows": detail, "source": out["source"]}


# --------------------------------------------------------------------------- #
#  toolchain subsample — rust / lua / llvm-x86 truth on accepted tasks
# --------------------------------------------------------------------------- #
def _spell(v, lang: str) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, list):
        inner = ", ".join(_spell(x, lang) for x in v)
        return ("vec![%s]" % inner) if lang == "rust" else ("{%s}" % inner)
    return str(v)


def _parse_out(tok: str):
    t = tok.strip()
    if t in ("true", "false"):
        return t == "true"
    try:
        f = float(t)
        return int(f) if f.is_integer() else f
    except ValueError:
        return t


def _param_names(ir: dict) -> list:
    names = []
    for st in ir.get("stmts") or []:
        if isinstance(st, dict) and st.get("type") == "ProgDefFnParam":
            names.append(st["name"])
        else:
            break
    return names


def _run(cmd, timeout=120):
    return subprocess.run(cmd, capture_output=True, text=True,
                          timeout=timeout)


def toolchain_check(task: dict, ir: dict) -> dict:
    """rust + lua + llvm→x86 truth for ONE accepted task: render, build,
    run each held-out call, compare numerically against ProgEval."""
    fn = task["id"]
    params = _param_names(ir)
    calls = []
    for hr in task["held_out_rows"]:
        pe = prog_eval(ir, dict(hr["inputs"]))
        calls.append({"inputs": hr["inputs"], "prog_eval": pe.get("result")})
    res: dict = {"task_id": fn, "params": params}

    # ---- rust -------------------------------------------------------- #
    if shutil.which("rustc") is None:
        res["rust"] = {"outcome": "tool_missing"}
    else:
        ro = rl.render_function(srs.Substrate(), ir, "rust", name=fn)
        if not ro.get("ok"):
            res["rust"] = {"outcome": "render_gap", "gaps": ro.get("gaps")}
        else:
            main = "fn main() {\n" + "\n".join(
                '    println!("{}", %s(%s));' % (fn, ", ".join(
                    _spell(c["inputs"][p], "rust") for p in params))
                for c in calls) + "\n}\n"
            with tempfile.TemporaryDirectory() as d:
                rs = os.path.join(d, "one.rs")
                with open(rs, "w") as f:
                    f.write(ro["source"] + "\n\n" + main)
                exe = os.path.join(d, "one")
                cp = _run(["rustc", "-O", "-o", exe, rs])
                if cp.returncode != 0:
                    res["rust"] = {"outcome": "compile_error",
                                   "stderr": cp.stderr[-800:]}
                else:
                    out = _run([exe], timeout=30)
                    got = [_parse_out(t) for t in out.stdout.split()]
                    oks = [len(got) == len(calls)] + [
                        agree(g, c["prog_eval"])
                        for g, c in zip(got, calls)]
                    res["rust"] = {"outcome": "agree" if all(oks)
                                   else "disagree",
                                   "stdout": out.stdout.split(),
                                   "prog_eval": [c["prog_eval"]
                                                 for c in calls]}
    # ---- lua --------------------------------------------------------- #
    lua_exe = next((e for e in ("lua5.4", "luajit", "lua")
                    if shutil.which(e)), None)
    if lua_exe is None:
        res["lua"] = {"outcome": "tool_missing"}
    else:
        lo = rl.render_function(srs.Substrate(), ir, "lua", name=fn)
        if not lo.get("ok"):
            res["lua"] = {"outcome": "render_gap", "gaps": lo.get("gaps")}
        else:
            script = lo["source"] + "\n\n" + "\n".join(
                "print(%s(%s))" % (fn, ", ".join(
                    _spell(c["inputs"][p], "lua") for p in params))
                for c in calls) + "\n"
            with tempfile.TemporaryDirectory() as d:
                p = os.path.join(d, "one.lua")
                with open(p, "w") as f:
                    f.write(script)
                out = _run([lua_exe, p], timeout=30)
                if out.returncode != 0:
                    res["lua"] = {"outcome": "runtime_error",
                                  "stderr": out.stderr[-800:]}
                else:
                    got = [_parse_out(t) for t in out.stdout.splitlines()]
                    oks = [len(got) == len(calls)] + [
                        agree(g, c["prog_eval"])
                        for g, c in zip(got, calls)]
                    res["lua"] = {"outcome": "agree" if all(oks)
                                  else "disagree",
                                  "exe": lua_exe,
                                  "stdout": out.stdout.splitlines(),
                                  "prog_eval": [c["prog_eval"]
                                                for c in calls]}
    # ---- llvm → x86-64 (the chain; i32 ABI — int-only scope) ---------- #
    ints_only = all(isinstance(v, int) and not isinstance(v, bool)
                    for c in calls for v in c["inputs"].values()) \
        and all(isinstance(c["prog_eval"], (int, bool))
                for c in calls)
    if not ints_only:
        res["llvm_x86"] = {"outcome": "scope_out_non_int"}
    elif shutil.which("gcc") is None:
        res["llvm_x86"] = {"outcome": "tool_missing"}
    else:
        res["llvm_x86"] = _llvm_chain(fn, ir, params, calls)
    return res


def _llvm_chain(fn: str, ir: dict, params: list, calls: list) -> dict:
    try:
        from domains.llvm_ir_cfg import install_cfg_productions, \
            parse_llvm_cfg
        from domains.llvm_ir_cfg_to_asm import emit_x86_64_cfg
        from domains.prog_ir_to_llvm import emit_prog_to_llvm
        from domains.x86_64_runner import assemble_and_load
    except Exception as e:  # noqa: BLE001
        return {"outcome": "import_error", "error": str(e)[:300]}
    try:
        e = emit_prog_to_llvm(ir, fn_name=fn)
        if not e.get("ok"):
            return {"outcome": "emit_refusal", "blockers": e.get("blockers")}
        s2 = srs.Substrate()
        for src_t in ("LLVMInstruction", "LLVMConstant", "LLVMValue"):
            for tgt_t in ("LLVMInstruction", "LLVMConstant", "LLVMValue"):
                for et in ("uses_op0", "uses_op1", "uses_op2", "produces"):
                    s2.add_production({
                        "src": {"type": src_t, "var": "src"},
                        "edge_type": et,
                        "tgt": {"type": tgt_t, "var": "tgt"},
                        "where": None,
                        "weight": {"type": "Lit", "value": 1.0},
                        "provenance": "battery:open"})
        install_cfg_productions(s2)
        out = parse_llvm_cfg(s2, e["text"],
                             inputs=tuple("%" + p for p in e["params"]))
        asm = emit_x86_64_cfg(s2, out["entry_bb"], fn,
                              input_nodes=[out["ssa"]["%" + p]
                                           for p in e["params"]])
        native = assemble_and_load(asm, fn, n_args=len(e["params"]))
        oks, got = [], []
        for c in calls:
            g = native(*[c["inputs"][p] for p in e["params"]])
            got.append(g)
            exp = int(c["prog_eval"]) if isinstance(c["prog_eval"], bool) \
                else c["prog_eval"]
            oks.append(g == exp)
        return {"outcome": "agree" if all(oks) else "disagree",
                "got": got, "prog_eval": [c["prog_eval"] for c in calls]}
    except Exception as ex:  # noqa: BLE001
        return {"outcome": "chain_error", "error": str(ex)[:300]}


# --------------------------------------------------------------------------- #
#  C-BATTERY — the prereg's continuity control
# --------------------------------------------------------------------------- #
def c_battery(frozen_items: list) -> dict:
    out: dict = {"frozen_baseline": {
        "n": len(frozen_items),
        "n_ok": sum(1 for i in frozen_items if i["ok"]),
        "source": os.path.basename(BASELINE_PATH)}}
    requests = [i["request"] for i in frozen_items]
    # (a) the pinned path on a fully-booted agent
    try:
        from substrate.world_adapter import WorldAdapter
        from substrate.boot_all import load_all_seeds
        from domains import code_curriculum as cc
        t0 = time.time()
        a = WorldAdapter(seeds=())
        load_all_seeds(a)
        live = cc.run_write_battery(a, requests)
        regressions = [
            {"request": fi["request"], "frozen_ok": fi["ok"],
             "live_ok": lr["ok"], "live_reason": lr.get("reason")}
            for fi, lr in zip(frozen_items, live["rows"])
            if fi["ok"] and not lr["ok"]]
        improvements = [lr["request"] for fi, lr in
                        zip(frozen_items, live["rows"])
                        if lr["ok"] and not fi["ok"]]
        out["live_pinned_path"] = {
            "n": live["n"], "n_ok": live["n_ok"],
            "boot_seconds": round(time.time() - t0, 1),
            "rows": live["rows"],
            "regressions_ok_to_fail": regressions,
            "improvements_fail_to_ok": improvements}
    except Exception as e:  # noqa: BLE001
        out["live_pinned_path"] = {"error": str(e)[:500]}
    # (b) the same 26 requests VERBATIM through the new pipeline (no example
    #     rows — the battery text is never extended). Documents the
    #     structural fact, not a score.
    rows = []
    for req in requests:
        s, ag = boot(frozen=False)
        r = psy.synthesize_from_request(s, ag, req, ())
        rows.append({"request": req, "status": r.get("status"),
                     "gap_reason": r.get("gap_reason")})
    out["new_pipeline_verbatim"] = {
        "note": ("the P4 verdict layer is execution agreement with example "
                 "rows; the frozen battery carries none, so covered "
                 "requests land no_examples->gapped by design — a "
                 "structural difference, not a capability score"),
        "rows": rows}
    return out


# --------------------------------------------------------------------------- #
#  aggregation
# --------------------------------------------------------------------------- #
def aggregate(rows: list, strata: list) -> dict:
    def block(sub):
        n = len(sub)
        k = sum(1 for r in sub if r["outcome"] == "accepted_holdout_ok")
        w = wilson(k, n)
        w["accepted_any"] = sum(1 for r in sub
                                if str(r["outcome"]).startswith("accepted"))
        w["not_recognized"] = sum(1 for r in sub
                                  if r["outcome"] == "not_recognized")
        return w
    agg = {"overall": block(rows), "per_stratum": {}}
    for st in strata:
        agg["per_stratum"][st] = block([r for r in rows
                                        if r["stratum"] == st])
    return agg


def outcome_signature(rows: list) -> list:
    return [[r["task_id"], r["outcome"], r["status"], r["construction"],
             r["attempts"], r["gap_reason"]] for r in rows]


def sig_hash(sig: list) -> str:
    return hashlib.sha256(
        json.dumps(sig, sort_keys=True).encode()).hexdigest()


def taxonomy(rows: list) -> dict:
    by: dict = {}
    for r in rows:
        key = r["outcome"] if not str(r["outcome"]).startswith("gapped") \
            else "gapped:%s" % (r.get("gap_reason") or "?")
        e = by.setdefault(key, {"n": 0, "task_ids": []})
        e["n"] += 1
        e["task_ids"].append(r["task_id"])
    return dict(sorted(by.items(), key=lambda kv: -kv[1]["n"]))


# --------------------------------------------------------------------------- #
#  append_postfix — P6.5: re-measure the MAIN arm on the FIXED seed
#  (v1.1.0, ps_enumerate_fresh_attempt) and APPEND it to the artifact as
#  arm `main_postfix`. The frozen MAIN/FROZEN rows are NEVER overwritten —
#  they are the pre-fix baseline the new arm is read against.
# --------------------------------------------------------------------------- #
def append_postfix() -> None:
    t_start = time.time()
    with open(TASKS_PATH) as f:
        taskset = json.load(f)
    tasks = sorted(taskset["tasks"], key=lambda t: t["id"])
    strata = sorted(taskset["strata_counts"])
    with open(OUT_PATH) as f:
        artifact = json.load(f)
    assert "main" in artifact["arms"] and "frozen" in artifact["arms"], \
        "append mode requires the frozen MAIN/FROZEN artifact"

    print("== MAIN-POSTFIX arm (run 1): %d tasks ==" % len(tasks))
    t0 = time.time()
    rows = [run_task(t, frozen=False) for t in tasks]
    t_run1 = time.time() - t0
    print("== MAIN-POSTFIX arm (run 2, determinism) ==")
    t0 = time.time()
    rows_2 = [run_task(t, frozen=False) for t in tasks]
    t_run2 = time.time() - t0
    sig1, sig2 = outcome_signature(rows), outcome_signature(rows_2)
    determinism = {
        "runs": 2, "identical": sig1 == sig2,
        "outcome_hash_run1": sig_hash(sig1),
        "outcome_hash_run2": sig_hash(sig2),
        "elapsed_run1_seconds": round(t_run1, 1),
        "elapsed_run2_seconds": round(t_run2, 1)}

    agg = aggregate(rows, strata)
    n = len(tasks)
    main_rows = artifact["arms"]["main"]["rows"]
    agg_main = artifact["arms"]["main"]["aggregates"]

    # deltas vs the FROZEN-IN-ARTIFACT arms (standing delta rule applied)
    def _delta_block(base_agg):
        d = newcombe_delta(agg["overall"]["k"], n,
                           base_agg["overall"]["k"], n)
        step = 1.0 / n
        d["per_episode_step"] = round(step, 6)
        d["three_x_step"] = round(3 * step, 6)
        ci_sep = d["ci95"][0] > 0 or d["ci95"][1] < 0
        above = abs(d["delta"]) > 3 * step
        d["verdict"] = (
            "ci_separated_gain" if ci_sep and d["delta"] > 0 else
            "ci_separated_loss" if ci_sep else
            ("inside_ci_above_3x_step" if above else "within_noise")
            + "_no_measured_gain")
        d["per_stratum"] = {
            st: newcombe_delta(agg["per_stratum"][st]["k"],
                               agg["per_stratum"][st]["n"],
                               base_agg["per_stratum"][st]["k"],
                               base_agg["per_stratum"][st]["n"])
            for st in strata}
        return d

    # where the previously-stalled tasks landed (identity list, per task)
    stalled_ids = [r["task_id"] for r in main_rows
                   if str(r["outcome"]).startswith("stalled")]
    by_id = {r["task_id"]: r for r in rows}
    landed = {tid: {"outcome": by_id[tid]["outcome"],
                    "status": by_id[tid]["status"],
                    "attempts": by_id[tid]["attempts"],
                    "gap_reason": by_id[tid]["gap_reason"]}
              for tid in stalled_ids}
    # changed-row audit: the fix must move ONLY the collision class
    changed = [r["task_id"] for r in rows
               if next(m for m in main_rows
                       if m["task_id"] == r["task_id"])["outcome"]
               != r["outcome"]]

    head = ""
    try:
        head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                              capture_output=True, text=True,
                              timeout=10).stdout.strip()
    except Exception:  # noqa: BLE001
        pass
    artifact["arms"]["main_postfix"] = {
        "rows": rows, "aggregates": agg,
        "elapsed_seconds": round(t_run1, 1),
        "provenance": {
            "arm": "MAIN-POSTFIX (P6.5)",
            "measured_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "head": head,
            "seed": "seeds/program_synthesis.json v1.1.0 — "
                    "ps_enumerate_fresh_attempt (27 rules)",
            "fix": ("the P6 §2.1 stalled:evaluated defect: a codebook "
                    "decoy consumed attempt N, the enumerate rung "
                    "re-evaluated at the SAME N, the "
                    "verdict_attempt < eval_attempt guard never re-armed. "
                    "The new rule bumps ps_attempts by 1 on "
                    "enumerate_pending IFF some example row's eval_attempt "
                    "equals the goal's current ps_attempts (the exact "
                    "collision), so the rung's evaluation gets a fresh "
                    "attempt number; non-colliding paths byte-unchanged."),
            "protocol": ("identical to the frozen MAIN arm: same 125 "
                         "tasks, same scoring, one fresh substrate per "
                         "task, sorted-id order, twin-run determinism"),
        },
    }
    artifact["determinism_postfix"] = determinism
    artifact["failure_taxonomy"]["main_postfix"] = taxonomy(rows)
    artifact["delta_postfix"] = {
        "postfix_minus_main": _delta_block(agg_main),
        "postfix_minus_frozen": _delta_block(
            artifact["arms"]["frozen"]["aggregates"]),
    }
    artifact["postfix_recovery"] = {
        "previously_stalled_main": stalled_ids,
        "n_stalled_main": len(stalled_ids),
        "n_stalled_postfix": sum(
            1 for r in rows if str(r["outcome"]).startswith("stalled")),
        "landed": landed,
        "changed_task_ids_vs_main": changed,
    }
    with open(OUT_PATH, "w") as f:
        json.dump(artifact, f, indent=1, sort_keys=False)
        f.write("\n")
    print("appended main_postfix →", OUT_PATH)
    print("POSTFIX overall: %(k)d/%(n)d p=%(p)s ci=%(ci95)s"
          % agg["overall"])
    print("stalled postfix:", artifact["postfix_recovery"]["n_stalled_postfix"])
    print("delta vs main:", artifact["delta_postfix"]["postfix_minus_main"]
          ["delta"], artifact["delta_postfix"]["postfix_minus_main"]["ci95"],
          artifact["delta_postfix"]["postfix_minus_main"]["verdict"])
    print("determinism identical:", determinism["identical"])
    print("elapsed: %.1fs" % (time.time() - t_start))


# --------------------------------------------------------------------------- #
#  append_p7 — P7-D: the POWERED re-measurement of the three preregistered
#  P7 hypotheses (PROGRAM_SYNTHESIS_P7_PREREG.md H7a/H7b/H7c) on the full
#  stack as landed (seed v1.3.0: descent + repair rules; mined chunks
#  installed). Frozen MAIN / FROZEN / MAIN-POSTFIX rows are NEVER touched —
#  new arms are APPENDED under new keys.
#
#  PROTOCOL DECISION (registered here, stated first in the P7D doc):
#    PRIMARY protocol UNCHANGED from MAIN-POSTFIX — held-out rows are never
#    revealed to the loop; a task scores accepted+holdout_ok on its own
#    example rows only. Repair therefore acts only on failures the loop's
#    OWN verification reveals (example rows / CEGIS); without an ingested
#    counterexample the repair lane is inert (gated in P7-B).
#    SECONDARY, protocol-DISTINCT arm: REPAIR-ORACLE — after a
#    holdout_fail, exactly ONE failing held-out row is fed back via
#    ingest_counterexample (one round; the pass@2-with-feedback analog).
#    Its rows carry protocol="repair_oracle_feedback" and NEVER enter any
#    primary aggregate or delta.
#
#  ARMS
#    main_p7        full stack: starter 8 + spine + boarded bigrams +
#                   15 mined chunks installed; descent + repair rules live.
#                   PRIMARY. (H7a vs frozen MAIN-POSTFIX; H7b attempts.)
#    frozen_p7      C-CODEBOOK-FROZEN-P7: SAME MECHANISMS (descent/repair
#                   rules in the seed stay), learned CONTENT stripped —
#                   starter 8 only, no spine, no chunks, no bigrams.
#                   (H7c contrast: content, not mechanism — the H6 retest.)
#    repair_oracle  main_p7 boot + the secondary protocol above.
# --------------------------------------------------------------------------- #
P7_PRIMARY_ARMS = ("main_p7", "frozen_p7")
P7_ALL_ARMS = ("main_p7", "frozen_p7", "repair_oracle")
_H7A_STRATUM = "loop_accumulation"
_H7A_BAR = 0.409  # prereg H7a: frozen MAIN-POSTFIX stratum Wilson upper


def boot_p7(mode: str):
    """One fresh substrate per task, per arm. main_p7/repair_oracle add the
    mined chunk codebook on top of the standard boot; frozen_p7 strips to
    the 8 starter shapes + removes bigrams (chunks never installed)."""
    s = srs.Substrate()
    ag = s.add_node("Agent", {})
    psy.ensure_program_synthesis(s, s._inner, ag)
    if mode == "frozen_p7":
        strip_to_starter(s)
    else:
        from domains import prog_chunk_growth as pcg
        pcg.install_mined_chunks(s)
    return s, ag


def run_task_p7(task: dict, mode: str) -> dict:
    s, ag = boot_p7(mode)
    examples = [(r["inputs"], r["expected"]) for r in task["example_rows"]]
    r = psy.synthesize_from_request(s, ag, task["request_text"], examples)
    if mode != "repair_oracle":
        return _build_row(s, task, r, arm=mode, protocol="primary")
    # ---- secondary protocol: one verifier-revealed counterexample ------- #
    pre = _build_row(s, task, r, arm=mode,
                     protocol="repair_oracle_feedback")
    pre["oracle"] = {"ce_fed": None,
                     "pre_feedback_outcome": pre["outcome"],
                     "pre_feedback_status": pre["status"],
                     "pre_feedback_construction": pre["construction"],
                     "rounds": 0}
    if pre["outcome"] != "accepted_holdout_fail":
        return pre
    fail = next(hr for hr in pre["holdout"]["rows"] if not hr["ok"])
    psy.ingest_counterexample(s, ag, r["goal"],
                              dict(fail["inputs"]), fail["expected"])
    psy.pump(s, ag)
    r2 = psy.read_goal(s, r["goal"])
    row = _build_row(s, task, r2, arm=mode,
                     protocol="repair_oracle_feedback")
    row["oracle"] = {
        "ce_fed": {"inputs": fail["inputs"], "expected": fail["expected"]},
        "pre_feedback_outcome": pre["outcome"],
        "pre_feedback_status": pre["status"],
        "pre_feedback_construction": pre["construction"],
        "rounds": 1,
        "repair": r2.get("repair"),
    }
    return row


def _twin_run(tasks: list, mode: str) -> tuple:
    print("== %s arm (run 1): %d tasks ==" % (mode, len(tasks)))
    t0 = time.time()
    rows = [run_task_p7(t, mode) for t in tasks]
    t1 = time.time() - t0
    print("== %s arm (run 2, determinism) ==" % mode)
    t0 = time.time()
    rows_2 = [run_task_p7(t, mode) for t in tasks]
    t2 = time.time() - t0
    sig1, sig2 = outcome_signature(rows), outcome_signature(rows_2)
    det = {"runs": 2, "identical": sig1 == sig2,
           "outcome_hash_run1": sig_hash(sig1),
           "outcome_hash_run2": sig_hash(sig2),
           "elapsed_run1_seconds": round(t1, 1),
           "elapsed_run2_seconds": round(t2, 1)}
    return rows, det, round(t1, 1)


def delta_block(agg_a: dict, agg_b: dict, strata: list) -> dict:
    """Newcombe delta a − b with the standing verdict rule (P6 §0)."""
    ka, na = agg_a["overall"]["k"], agg_a["overall"]["n"]
    kb, nb = agg_b["overall"]["k"], agg_b["overall"]["n"]
    d = newcombe_delta(ka, na, kb, nb)
    step = 1.0 / na
    d["per_episode_step"] = round(step, 6)
    d["three_x_step"] = round(3 * step, 6)
    ci_sep = d["ci95"][0] > 0 or d["ci95"][1] < 0
    above = abs(d["delta"]) > 3 * step
    d["verdict"] = (
        "ci_separated_gain" if ci_sep and d["delta"] > 0 else
        "ci_separated_loss" if ci_sep else
        ("inside_ci_above_3x_step" if above else "within_noise")
        + "_no_measured_gain")
    d["per_stratum"] = {
        st: newcombe_delta(agg_a["per_stratum"][st]["k"],
                           agg_a["per_stratum"][st]["n"],
                           agg_b["per_stratum"][st]["k"],
                           agg_b["per_stratum"][st]["n"])
        for st in strata}
    return d


def _attempts_stats(rows: list) -> dict:
    """H7b instrument: attempts over accepted tasks (mean + distribution),
    park count. Distribution keys are the integer attempt counts."""
    acc = [r for r in rows if str(r["outcome"]).startswith("accepted")]
    ok = [r for r in rows if r["outcome"] == "accepted_holdout_ok"]

    def stats(sub):
        vals = [int(r["attempts"]) for r in sub
                if r["attempts"] is not None]
        dist: dict = {}
        for v in vals:
            dist[str(v)] = dist.get(str(v), 0) + 1
        return {"n": len(sub),
                "mean_attempts": round(sum(vals) / len(vals), 6)
                if vals else None,
                "distribution": dict(sorted(dist.items()))}

    return {"accepted_any": stats(acc),
            "accepted_holdout_ok": stats(ok),
            "n_parked": sum(1 for r in rows
                            if str(r["outcome"]).startswith("stalled"))}


def _paired_changes(rows_new: list, rows_base: list) -> dict:
    """Paired identity lists (never a count): per-id outcome changes,
    split into the claim-relevant classes."""
    base = {r["task_id"]: r for r in rows_base}
    changed = []
    for r in rows_new:
        b = base[r["task_id"]]
        if r["outcome"] != b["outcome"]:
            changed.append({"task_id": r["task_id"],
                            "stratum": r["stratum"],
                            "before": b["outcome"],
                            "after": r["outcome"]})
    regress = [c["task_id"] for c in changed
               if c["before"] == "accepted_holdout_ok"
               and c["after"] != "accepted_holdout_ok"]
    gains = [c["task_id"] for c in changed
             if c["after"] == "accepted_holdout_ok"
             and c["before"] != "accepted_holdout_ok"]
    fail_to_ok = [c["task_id"] for c in changed
                  if c["before"] == "accepted_holdout_fail"
                  and c["after"] == "accepted_holdout_ok"]
    return {"changed": changed,
            "changed_task_ids": [c["task_id"] for c in changed],
            "regressions_ok_to_not_ok": regress,
            "gains_to_holdout_ok": gains,
            "holdout_fail_to_ok": fail_to_ok}


def _learned_layer_provenance(rows: list) -> dict:
    """What the learned layer DID buy, at paired-id grain: chunk-cued
    accepts (construction ck_*/ckt_*), descent-rung accepts, spine/lattice
    accepts — read from rung provenance, per the P6.5 convention."""
    acc = [r for r in rows if str(r["outcome"]).startswith("accepted")]

    def ids(pred):
        return sorted(r["task_id"] for r in acc if pred(r))

    rungs = lambda r: r.get("rungs") or {}  # noqa: E731
    return {
        # P6.5 convention: provenance is the RUNG MARKERS, never the
        # construction name (a decoy leaves its name on an enumerate
        # accept). chunk_named = accepts whose LAST codebook proposal was a
        # chunk (decoy-or-win); chunk_rung1 = accepts the chunk itself won
        # (no enumerate ran).
        "chunk_named_accepts": ids(
            lambda r: str(r.get("construction") or "").startswith(
                ("ck_", "ckt_"))),
        "chunk_rung1_accepts": ids(
            lambda r: str(r.get("construction") or "").startswith(
                ("ck_", "ckt_"))
            and rungs(r).get("enumerate") is None
            and rungs(r).get("descend") is None),
        "descent_accepts": ids(
            lambda r: rungs(r).get("descend") == 1.0
            and rungs(r).get("enumerate") is None),
        "lattice_accepts": ids(
            lambda r: rungs(r).get("lattice") == 1.0),
        "codebook_rung1_accepts": ids(
            lambda r: rungs(r).get("codebook") == 1.0
            and not rungs(r).get("lattice")
            and not rungs(r).get("descend")
            and not rungs(r).get("enumerate")),
        "enumerate_accepts": ids(
            lambda r: rungs(r).get("enumerate") == 1.0),
    }


def append_p7() -> None:
    t_start = time.time()
    with open(TASKS_PATH) as f:
        taskset = json.load(f)
    tasks = sorted(taskset["tasks"], key=lambda t: t["id"])
    strata = sorted(taskset["strata_counts"])
    n = len(tasks)
    with open(OUT_PATH) as f:
        artifact = json.load(f)
    for frozen_arm in ("main", "frozen", "main_postfix"):
        assert frozen_arm in artifact["arms"], \
            "append-p7 requires the frozen %s arm" % frozen_arm
    # protected-control pin: the frozen arms' rows must hash to their
    # recorded determinism hashes BEFORE and AFTER this append.
    frozen_hashes = {
        "main": artifact["determinism"]["outcome_hash_run1"],
        "main_postfix":
            artifact["determinism_postfix"]["outcome_hash_run1"]}
    for arm, h in frozen_hashes.items():
        assert sig_hash(outcome_signature(
            artifact["arms"][arm]["rows"])) == h, arm

    arms_out, dets, taxes = {}, {}, {}
    for mode in P7_ALL_ARMS:
        rows, det, elapsed = _twin_run(tasks, mode)
        arms_out[mode] = {"rows": rows,
                          "aggregates": aggregate(rows, strata),
                          "elapsed_seconds": elapsed}
        dets[mode] = det
        taxes[mode] = taxonomy(rows)

    agg_main_p7 = arms_out["main_p7"]["aggregates"]
    agg_frozen_p7 = arms_out["frozen_p7"]["aggregates"]
    agg_postfix = artifact["arms"]["main_postfix"]["aggregates"]
    rows_main_p7 = arms_out["main_p7"]["rows"]
    rows_postfix = artifact["arms"]["main_postfix"]["rows"]

    # ---- H7a: loop_accumulation, main_p7 vs frozen MAIN-POSTFIX -------- #
    la_new = agg_main_p7["per_stratum"][_H7A_STRATUM]
    la_old = agg_postfix["per_stratum"][_H7A_STRATUM]
    h7a_paired = _paired_changes(
        [r for r in rows_main_p7 if r["stratum"] == _H7A_STRATUM],
        [r for r in rows_postfix if r["stratum"] == _H7A_STRATUM])
    h7a = {
        "hypothesis": ("descent reaches list folds the whole-goal "
                       "enumerator cannot; primary reading = the stratum's "
                       "Wilson lower bound > %.3f (frozen MAIN-POSTFIX "
                       "upper)" % _H7A_BAR),
        "main_p7": la_new, "main_postfix": la_old,
        "delta": newcombe_delta(la_new["k"], la_new["n"],
                                la_old["k"], la_old["n"]),
        "wilson_lower_bound_new": la_new["ci95"][0],
        "registered_bar": _H7A_BAR,
        "ci_separated": la_new["ci95"][0] > _H7A_BAR,
        "paired": h7a_paired,
    }
    h7a["verdict"] = ("confirmed_ci_separated" if h7a["ci_separated"]
                      else "registered_null")

    # ---- H7b: attempts-per-accept + conversions under each protocol ---- #
    oracle_rows = arms_out["repair_oracle"]["rows"]
    oracle_conversions = sorted(
        r["task_id"] for r in oracle_rows
        if (r.get("oracle") or {}).get("pre_feedback_outcome")
        == "accepted_holdout_fail"
        and r["outcome"] == "accepted_holdout_ok")
    oracle_fed = sorted(
        r["task_id"] for r in oracle_rows
        if (r.get("oracle") or {}).get("ce_fed") is not None)
    primary_paired = _paired_changes(rows_main_p7, rows_postfix)
    h7b = {
        "hypothesis": ("attempts-per-accept falls vs MAIN-POSTFIX; parks "
                       "stay 0; holdout_fail→ok conversions reported "
                       "under each protocol"),
        "attempts_main_p7": _attempts_stats(rows_main_p7),
        "attempts_main_postfix": _attempts_stats(rows_postfix),
        "primary_protocol_conversions_fail_to_ok":
            primary_paired["holdout_fail_to_ok"],
        "repair_oracle_protocol": {
            "protocol": "repair_oracle_feedback (SECONDARY — never "
                        "comparable to primary rows)",
            "ce_fed_task_ids": oracle_fed,
            "conversions_fail_to_ok": oracle_conversions,
        },
    }

    # ---- H7c: main_p7 − frozen_p7 (the H6 retest) ----------------------- #
    h7c = {
        "hypothesis": ("the learned-content delta becomes CI-separated on "
                       "the P7 battery (H6 retest); null reading: "
                       "capability mass stays on the enumerator + verdict "
                       "layer"),
        "delta_main_p7_minus_frozen_p7":
            delta_block(agg_main_p7, agg_frozen_p7, strata),
        "paired": _paired_changes(rows_main_p7,
                                  arms_out["frozen_p7"]["rows"]),
        "learned_layer_provenance_main_p7":
            _learned_layer_provenance(rows_main_p7),
        "learned_layer_provenance_frozen_p7":
            _learned_layer_provenance(arms_out["frozen_p7"]["rows"]),
    }

    head = ""
    try:
        head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                              capture_output=True, text=True,
                              timeout=10).stdout.strip()
    except Exception:  # noqa: BLE001
        pass
    protocol_note = {
        "primary": ("UNCHANGED from MAIN-POSTFIX: held-out rows never "
                    "revealed to the loop; repair acts only on failures "
                    "the loop's own verification reveals (example rows / "
                    "CEGIS). Arms main_p7 + frozen_p7."),
        "secondary": ("repair_oracle_feedback: after a holdout_fail, "
                      "exactly ONE failing held-out row is fed back via "
                      "ingest_counterexample (one round). Protocol-"
                      "distinct; its rows never enter primary aggregates "
                      "or deltas."),
    }
    for mode in P7_ALL_ARMS:
        arms_out[mode]["provenance"] = {
            "arm": mode,
            "protocol": ("repair_oracle_feedback"
                         if mode == "repair_oracle" else "primary"),
            "measured_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "head": head,
            "seed": "seeds/program_synthesis.json v1.3.0 (43 rules: "
                    "descent + repair)",
            "codebook": ("starter 8 only; no spine, no chunks, no bigrams "
                         "(strip_to_starter; chunks never installed)"
                         if mode == "frozen_p7" else
                         "starter 8 + spine + boarded bigrams + 15 mined "
                         "chunks (install_mined_chunks, "
                         "results/prog_chunk_mine.json v1.0.0)"),
        }
        artifact["arms"][mode] = arms_out[mode]
        artifact["failure_taxonomy"][mode] = taxes[mode]
    artifact["determinism_p7"] = dets
    artifact["p7_verdicts"] = {
        "protocol_decision": protocol_note,
        "h7a_loop_accumulation": h7a,
        "h7b_repair": h7b,
        "h7c_learned_content": h7c,
        "paired_main_p7_vs_main_postfix": primary_paired,
        "stop_defect_regressions_vs_main_postfix":
            primary_paired["regressions_ok_to_not_ok"],
    }
    # frozen arms still untouched after the append
    for arm, h in frozen_hashes.items():
        assert sig_hash(outcome_signature(
            artifact["arms"][arm]["rows"])) == h, arm
    with open(OUT_PATH, "w") as f:
        json.dump(artifact, f, indent=1, sort_keys=False)
        f.write("\n")
    print("appended p7 arms →", OUT_PATH)
    for mode in P7_ALL_ARMS:
        agg = arms_out[mode]["aggregates"]["overall"]
        print("%-14s overall: %d/%d p=%s ci=%s det=%s"
              % (mode, agg["k"], agg["n"], agg["p"], agg["ci95"],
                 dets[mode]["identical"]))
    print("H7a:", h7a["verdict"], "stratum", la_new["k"], "/", la_new["n"],
          la_new["ci95"])
    print("H7b parks:", h7b["attempts_main_p7"]["n_parked"],
          "primary conversions:",
          h7b["primary_protocol_conversions_fail_to_ok"],
          "oracle conversions:", oracle_conversions)
    print("H7c:", h7c["delta_main_p7_minus_frozen_p7"]["delta"],
          h7c["delta_main_p7_minus_frozen_p7"]["ci95"],
          h7c["delta_main_p7_minus_frozen_p7"]["verdict"])
    print("STOP-defect regressions vs MAIN-POSTFIX:",
          primary_paired["regressions_ok_to_not_ok"])
    print("elapsed: %.1fs" % (time.time() - t_start))


# --------------------------------------------------------------------------- #
#  main
# --------------------------------------------------------------------------- #
def main() -> None:
    t_start = time.time()
    with open(TASKS_PATH) as f:
        taskset = json.load(f)
    tasks = sorted(taskset["tasks"], key=lambda t: t["id"])
    strata = sorted(taskset["strata_counts"])

    with open(BASELINE_PATH) as f:
        baseline = json.load(f)
    frozen_items = baseline["write_battery"]["items"]

    # contamination guard, enforced at run time too: no request text reused
    # from the P4 gate fixtures or the frozen battery.
    p4_file = os.path.join(ROOT, "tests",
                           "test_program_synthesis_migrated.py")
    with open(p4_file) as f:
        p4_src = f.read().lower()
    reused = [t["id"] for t in tasks
              if t["request_text"].lower() in p4_src
              or t["request_text"] in [i["request"] for i in frozen_items]]
    if reused:
        raise SystemExit("contamination: %r" % reused)

    print("== MAIN arm (run 1): %d tasks ==" % len(tasks))
    t0 = time.time()
    main_rows = [run_task(t, frozen=False) for t in tasks]
    t_main1 = time.time() - t0

    print("== MAIN arm (run 2, determinism) ==")
    t0 = time.time()
    main_rows_2 = [run_task(t, frozen=False) for t in tasks]
    t_main2 = time.time() - t0
    sig1, sig2 = outcome_signature(main_rows), outcome_signature(main_rows_2)
    determinism = {
        "runs": 2, "identical": sig1 == sig2,
        "outcome_hash_run1": sig_hash(sig1),
        "outcome_hash_run2": sig_hash(sig2),
        "elapsed_run1_seconds": round(t_main1, 1),
        "elapsed_run2_seconds": round(t_main2, 1)}

    print("== FROZEN arm (C-CODEBOOK-FROZEN) ==")
    t0 = time.time()
    frozen_rows = [run_task(t, frozen=True) for t in tasks]
    t_frozen = time.time() - t0

    agg_main = aggregate(main_rows, strata)
    agg_frozen = aggregate(frozen_rows, strata)
    n = len(tasks)
    per_episode_step = 1.0 / n
    delta = newcombe_delta(agg_main["overall"]["k"], n,
                           agg_frozen["overall"]["k"], n)
    delta["per_episode_step"] = round(per_episode_step, 6)
    delta["three_x_step"] = round(3 * per_episode_step, 6)
    ci_separated = delta["ci95"][0] > 0 or delta["ci95"][1] < 0
    above_noise = abs(delta["delta"]) > 3 * per_episode_step
    delta["verdict"] = (
        "ci_separated_gain" if ci_separated and delta["delta"] > 0 else
        "ci_separated_loss" if ci_separated else
        ("inside_ci_above_3x_step" if above_noise else "within_noise")
        + "_no_measured_gain")
    per_stratum_delta = {}
    for st in strata:
        m, fz = agg_main["per_stratum"][st], agg_frozen["per_stratum"][st]
        per_stratum_delta[st] = newcombe_delta(m["k"], m["n"],
                                               fz["k"], fz["n"])

    # ---- render validity aggregates ----------------------------------- #
    acc = [r for r in main_rows
           if str(r["outcome"]).startswith("accepted")]
    pr_ok = [r for r in acc if (r.get("python_render") or {}).get("render_ok")]
    pr_agree = [r for r in pr_ok
                if (r["python_render"] or {}).get("exec_agree")]
    gap_heads: dict = {}
    for r in acc:
        for g in (r.get("python_render") or {}).get("gaps") or []:
            gap_heads[g] = gap_heads.get(g, 0) + 1
    python_render = {
        "n_accepted": len(acc),
        "render_ok": wilson(len(pr_ok), len(acc)),
        "exec_agree_of_rendered": wilson(len(pr_agree), len(pr_ok)),
        "gap_heads": dict(sorted(gap_heads.items(), key=lambda kv: -kv[1])),
    }

    print("== toolchain subsample ==")
    acc_ids = sorted(r["task_id"] for r in acc)
    stride = max(1, len(acc_ids) // SUBSAMPLE_TARGET)
    sel = acc_ids[::stride][:SUBSAMPLE_TARGET]
    by_id = {t["id"]: t for t in tasks}
    ir_by_id = {r["task_id"]: r["ir"] for r in acc}
    tool_rows = [toolchain_check(by_id[i], ir_by_id[i]) for i in sel]
    def tool_agg(lang):
        outs = [tr[lang]["outcome"] for tr in tool_rows]
        return {"agree": outs.count("agree"),
                "disagree": outs.count("disagree"),
                "render_gap": outs.count("render_gap"),
                "other": {o: outs.count(o) for o in sorted(set(outs))
                          if o not in ("agree", "disagree", "render_gap")}}
    toolchain = {
        "rule": ("deterministic: sorted accepted MAIN task ids, stride "
                 "len//%d, first %d — no silent caps" %
                 (SUBSAMPLE_TARGET, SUBSAMPLE_TARGET)),
        "n_accepted_pool": len(acc_ids),
        "selected_ids": sel,
        "aggregates": {lang: tool_agg(lang)
                       for lang in ("rust", "lua", "llvm_x86")},
        "rows": tool_rows,
    }

    print("== C-BATTERY continuity control ==")
    cbat = c_battery(frozen_items)

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
            "P6 powered battery (PROGRAM_SYNTHESIS_PREREG.md §8, H6). Every "
            "aggregate is DERIVED from the per-task rows below — the rows "
            "are the baseline (a list, never a count). Arms: main (full "
            "ladder) vs frozen (C-CODEBOOK-FROZEN: 8 starter shapes, no "
            "spine, bigrams absent). Primary score: accepted Program whose "
            "ProgEval agrees on ALL held-out rows. Wilson 95% CIs; delta "
            "CI is Newcombe hybrid score. Standing rule applied: deltas "
            "within ~3x the per-episode step are not results."),
        "head": head,
        "measured_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "engine": {"so": os.path.relpath(so, ROOT),
                   "mtime": time.strftime(
                       "%Y-%m-%dT%H:%M:%S",
                       time.localtime(os.path.getmtime(so)))
                   if os.path.exists(so) else None},
        "condition": {
            "env": {"OZMA_NO_LLM": os.environ.get("OZMA_NO_LLM"),
                    "OZMA_SEED_PERSIST_DISABLED":
                        os.environ.get("OZMA_SEED_PERSIST_DISABLED")},
            "batching": ("one FRESH substrate per task "
                         "(ensure_program_synthesis boot), tasks in "
                         "sorted-id order; no cross-task state"),
            "pipeline": "domains/prog_synthesis.synthesize_from_request "
                        "(the unchanged P4 loop; seeds/program_synthesis"
                        ".json rules decide)",
            "scope_pins": [
                "languages: verdict layer is ProgEval on the hub IR "
                "(python-frame execution semantics); rust/lua/llvm-x86 "
                "are measured as RENDER+toolchain validity on the "
                "subsample, not as independent synthesis arms",
                "task domain: integer / list-of-integer inputs, SCALAR "
                "outputs (ProgEval's value space; the row-verdict fact "
                "records `got` only for scalars)",
                "recognition failures (no goal minted) count in the "
                "denominator and are reported separately",
                "error_handling stratum measures spec-level fallback "
                "behaviour only — no rung can synthesize ProgTryOr; a "
                "division task passing via the DSL's div-by-zero->0.0 "
                "semantics is a documented coincidence, not a "
                "try/except capability"],
        },
        "task_set": {
            "path": os.path.relpath(TASKS_PATH, ROOT),
            "n": n,
            "strata_counts": taskset["strata_counts"],
            "contamination_guard": (
                "checked at run time: no request text appears in "
                "tests/test_program_synthesis_migrated.py (the P4 gate "
                "fixtures — the mechanism's dev set) nor equals any frozen "
                "26-item C-BATTERY request"),
        },
        "arms": {
            "main": {"rows": main_rows, "aggregates": agg_main,
                     "elapsed_seconds": round(t_main1, 1)},
            "frozen": {"rows": frozen_rows, "aggregates": agg_frozen,
                       "elapsed_seconds": round(t_frozen, 1)},
        },
        "determinism": determinism,
        "delta_main_minus_frozen": {"overall": delta,
                                    "per_stratum": per_stratum_delta},
        "render_validity": {"python": python_render,
                            "toolchain_subsample": toolchain},
        "c_battery": cbat,
        "failure_taxonomy": {"main": taxonomy(main_rows),
                             "frozen": taxonomy(frozen_rows)},
        "environment": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "loadavg": list(os.getloadavg()),
            "tools": {t: bool(shutil.which(t))
                      for t in ("rustc", "lua5.4", "luajit", "gcc")},
        },
        "elapsed_seconds": round(time.time() - t_start, 1),
    }
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w") as f:
        json.dump(artifact, f, indent=1, sort_keys=False)
        f.write("\n")
    print("wrote", OUT_PATH)
    print("MAIN   overall: %(k)d/%(n)d p=%(p)s ci=%(ci95)s"
          % agg_main["overall"])
    print("FROZEN overall: %(k)d/%(n)d p=%(p)s ci=%(ci95)s"
          % agg_frozen["overall"])
    print("delta:", delta)
    print("determinism identical:", determinism["identical"])
    print("elapsed: %.1fs" % artifact["elapsed_seconds"])


if __name__ == "__main__":
    if "--append-postfix" in sys.argv[1:]:
        append_postfix()
    elif "--append-p7" in sys.argv[1:]:
        append_p7()
    else:
        main()

#!/usr/bin/env python3
"""arc4_backward_probe.py — Arc 4 S0 track B: the DATA-DEPENDENCY BACKWARD-
ORDERING probe (HA3) and the SEARCH-REACH sizing (HA4).

`PROGRAM_SYNTHESIS_ARC4_PLAN.md` §2-S0 (HA3's "offline, no build" probe +
HA4's sizing), `RESEARCH_CODE_IN_THE_BRAIN.md` §8.2b F-E (DepDegree
tau=.32-.41 vs McCabe tau=.04-.09; Crichton's backward-along-data-
dependencies on-demand strategy) + §8.3(2) (Rist's focal expansion) +
§8.5 (falsifier: "if focal expansion's hole ordering does not beat the
current descent ordering on a powered gate, Rist's finding does not
transfer"), `PROGRAM_SYNTHESIS_ARC3_R0_NOTES.md` (the oracle-ceiling
measurement this probe's HA3 population is drawn from),
`results/retrieval_oracle_ceiling.json` (12 held-out-honest task ids),
`results/mbpp_arc3_endgame.json` (FULL-R3's native enumerator accepts +
the `gapped:enumerate_failed` population), `results/mbpp_blocker_
histogram.json` (Q0's joint-curve taxonomy — HONESTLY SUPERSEDED for the
mutating-recv-method axis specifically, see MEASUREMENT 2 below; this
script recomputes that one axis FRESH rather than trust the cached file).

THIS IS A PURE MEASUREMENT SCRIPT. No synthesis/engine/seed/spec code is
touched. No `domains.teach.teach` call. No codebook/seed installation.
Structurally the same class as `scripts/retrieval_oracle_ceiling.py` and
`scripts/mbpp_blocker_histogram.py`, whose machinery it REUSES (imports,
never reimplements): `retrieval_oracle_ceiling.build_pool`/`_apply_edit`
for the train-split exemplar pool + rung-c edits, `mbpp_blocker_
histogram.resolve_entry`/`structural_family`/`extern_families`/
`subconstruct_features` for the fresh blocker recompute.

CONTAMINATION: this script reads TEST-split (task_id in [11,510])
reference `code` in exactly ONE place — MEASUREMENT 2's fresh
`emit_prog_ir` recompute over the `gapped:enumerate_failed` population —
which is the SAME precedent `scripts/mbpp_blocker_histogram.py`'s own
docstring already established and registered ("this is MEASUREMENT, not
learning: the counts and task_id lists this script emits never become a
codebook entry, cue-vocabulary token, bigram row, or taught shape
anywhere downstream"). MEASUREMENT 1 reads TRAIN-split (task_id >= 601)
`code` only, via the unchanged `retrieval_oracle_ceiling.build_pool` —
the arc-3 R0 precedent. Neither measurement writes a seed, a codebook, or
any artifact a synthesis run would ever load.

MEASUREMENT 1 — HA3, the backward-ordering probe (offline, no build).
For every task with a KNOWN oracle solution (arc-3's 12 retrieval-oracle-
ceiling held-out-honest ids, plus the 6 FULL-R3 tasks the ENUMERATOR
itself accepted natively, `enumerate_outcome=='ok'`), build a def-use /
data-dependency graph over the solution's own emitted hub IR (mechanical:
which variables feed the returned expression, transitively, INCLUDING
variables referenced only in a gating `If`/`While`/`ForEach`
condition/iterable along the path to an assignment or a return — a
program-dependence reading, not a bare def-use one, because a branch
condition IS a data dependency of which value ends up assigned).  Rank
each task's own parameters by ascending "hops from the output" (ties
broken by original declared position) — this is BACKWARD ordering.
CURRENT ordering is the declared parameter order (byte-identical to what
`domains.prog_synthesis.run_enumerate` actually feeds `SynthEnumerate`
today: MBPP row args are named `a,b,c,...` by POSITION, one letter per
declared parameter, and the Rust engine's own `var_order` is that same
positional/alphabetical order — see `scripts/mbpp_zero_shot_baseline.py`'s
own comment, "the name SynthEnumerate's alphabetical sort respects").

**This drives the REAL `SynthEnumerate` Term** (`Substrate()._inner.
evaluate`) on the task's own revealed rows (PRIMARY protocol), TWICE per
task: once with the row-argument dict keyed in CURRENT (declared) order,
once RELABELLED (a real, legitimate input to the Term — SynthEnumerate
only ever sees variable NAMES, never original source-level identity) so
the backward-closest-to-output row position is bound to the
first-enumerated variable name. `tested` (the Term's own honest counter)
is the steps-to-first-solution metric. Nothing about the search
algorithm itself is changed, simulated, or reimplemented — only the
NAMING of which row-argument gets which letter, which is exactly the
lever the plan asks for ("drive the real Term with ops/consts permuted
per ordering").

**What is NOT measured** (named honestly, matching the task's own
instruction): this does not run through `domains.prog_synthesis`'s hole-
scoped descent tree (`spawn_subgoal`, per-hole `exclude`/const-drop
scoping) — it drives `SynthEnumerate` directly on the task's revealed
rows exactly as the FLAT (non-hole, whole-spec) case `run_enumerate`
already does. A genuine multi-hole descent's per-hole variable/const
re-scoping under backward ordering is a DIFFERENT, larger experiment
(S3's actual build), not reproduced here. For the 12 retrieval-derived
tasks, the "oracle solution" is a TRAIN-split exemplar's own IR (already
measured, in `results/retrieval_oracle_ceiling.json`, to pass every
revealed AND held-out row of the TEST task) — the depth ordering is
computed from the EXEMPLAR's own declared parameter list and re-mapped
onto the TEST task's row-argument positions via the SAME `perm`/`edit`
fields the ceiling measurement already recorded (never re-derived by
this script). For the 6 native tasks, the oracle solution is the
enumerator's OWN accepted IR (ground truth, no re-mapping needed).

MEASUREMENT 2 — HA4, the search-reach sizing. Over FULL-R3's `gapped:
enumerate_failed` population, for five named levers (mutating-method
write-back, comprehension forms, kwargs, map/lambda, regex — the plan's
own list, regex explicitly out of scope but counted for the denominator)
this script asks: does the task's OWN reference solution (read fresh from
the corpus, the Q0 precedent) exhibit a blocker/subconstruct signature
that names lever X? Reported as id lists per lever, the pairwise overlap
matrix, and EXCLUSIVE mass (a task counts toward lever X's exclusive mass
iff X fires and none of the other four do) — the plan's own "ranked by
exclusive mass" instruction.

**HONEST STALENESS FINDING, load-bearing for the sizing:**
`results/mbpp_blocker_histogram.json` (measured 2026-07-31, per its own
`DATE` constant) reports `RecvMethod:*` blockers ZERO times across all
427 tasks (e.g. task 307's `list.append` shows `ok:true, blockers:[]`,
`recv_methods:['append']`). But `domains/prog_ir_emit.py` (mtime AFTER
that artifact — Aug 1, vs the histogram's Jul 31) now contains an
explicit `_RECV_BLOCKED_METHODS` table + a live `RecvMethod:<name>`
emission-time blocker for exactly this class ("Q1 notes §3, the mutating-
recv-call gap"), and a live re-run of `emit_prog_ir` on task 307's own
code TODAY returns `ok:false, blockers:['RecvMethod:append']`. The cached
histogram artifact is STALE for this one axis (the emitter's mutating-
method refusal was added or reinstated after the histogram was computed).
This script therefore does NOT trust the cached JSON for the mutating-
method lever (or any lever) — it recomputes ALL FIVE fresh, per task,
against the CURRENT `emit_prog_ir`/ast-walk, reusing (not reimplementing)
`mbpp_blocker_histogram.py`'s own per-task helper functions.

Run:
  PYTHONPATH=runners/dsl/python:.:scripts OZMA_NO_LLM=1 \
  OZMA_SEED_PERSIST_DISABLED=1 python scripts/arc4_backward_probe.py
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import sys
import time
import warnings
from collections import deque
from typing import Any, Dict, FrozenSet, List, Optional, Sequence, Set, Tuple

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"),
           os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

os.environ.setdefault("OZMA_NO_LLM", "1")
os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")

import substrate_rs as srs  # noqa: E402

from domains import mbpp_spec as ms  # noqa: E402
from domains.prog_ir_emit import emit_prog_ir  # noqa: E402

import retrieval_oracle_ceiling as roc  # noqa: E402 — build_pool / _apply_edit, reused
from mbpp_zero_shot_baseline import split_tasks as q0_split_tasks  # noqa: E402
from mbpp_blocker_histogram import (  # noqa: E402 — reused, not reimplemented
    resolve_entry, structural_family, extern_families, subconstruct_features,
)

FIXTURE_PATH = os.path.join(ROOT, "tests", "fixtures", "mbpp", "sanitized-mbpp.json")
PROVENANCE_PATH = os.path.join(ROOT, "tests", "fixtures", "mbpp", "provenance.json")
CEILING_PATH = os.path.join(ROOT, "results", "retrieval_oracle_ceiling.json")
ENDGAME_PATH = os.path.join(ROOT, "results", "mbpp_arc3_endgame.json")
OUT_PATH = os.path.join(ROOT, "results", "arc4_backward_probe.json")

SYNTH_MAX_SIZE = 9          # byte-identical to domains.prog_synthesis.run_enumerate
SYNTH_MAX_CANDIDATES = 0    # -> engine default 200_000
SYNTH_SATURATE_K = 0        # -> engine default 3

_ARG_LETTERS = [chr(c) for c in range(ord("a"), ord("z") + 1)]


# --------------------------------------------------------------------------- #
#  MEASUREMENT 1 — the def-use / data-dependency walker over the hub IR.
#  Mechanical: a generic recursive walk, with explicit (named) handling
#  for the three control-flow node kinds whose CONDITION/ITERABLE gates
#  a downstream assignment or return — a program-dependence reading, not
#  a bare def-use one (see module docstring for why).
# --------------------------------------------------------------------------- #
def _var_names(node: Any) -> Set[str]:
    """Every {"type":"Var","name":X} anywhere under `node` (generic walk,
    dict/list only — the same style as retrieval_oracle_ceiling.py's own
    `_walk_edit_points`)."""
    out: Set[str] = set()

    def walk(n: Any) -> None:
        if isinstance(n, dict):
            if n.get("type") == "Var" and isinstance(n.get("name"), str):
                out.add(n["name"])
            for v in n.values():
                walk(v)
        elif isinstance(n, list):
            for v in n:
                walk(v)

    walk(node)
    return out


def _walk_ir(node: Any, ctx: FrozenSet[str], producer_refs: Dict[str, Set[str]],
            return_frontier: Set[str]) -> None:
    """Populates `producer_refs[name]` = every variable whose value could
    influence `name`'s value at THIS site (the assigned expression's own
    vars, UNIONED with `ctx` — the vars referenced by every enclosing
    If/While/ForEach condition/iterable on the path to this site), and
    `return_frontier` = every variable that could influence SOME return
    value (same ctx-union rule). ProgAugAssign additionally depends on
    its OWN prior value (self-edge) — an in-place mutation reads before
    it writes."""
    if isinstance(node, dict):
        t = node.get("type")
        if t == "ProgReturn":
            return_frontier.update(_var_names(node.get("value")) | ctx)
            return
        if t in ("ProgAssignVar", "ProgAugAssign"):
            name = node.get("name")
            refs = _var_names(node.get("value")) | ctx
            if t == "ProgAugAssign" and isinstance(name, str):
                refs = refs | {name}
            if isinstance(name, str):
                producer_refs.setdefault(name, set()).update(refs)
            return
        if t == "ProgIfStmt":
            new_ctx = ctx | _var_names(node.get("cond"))
            _walk_ir(node.get("then"), new_ctx, producer_refs, return_frontier)
            _walk_ir(node.get("orelse"), new_ctx, producer_refs, return_frontier)
            return
        if t == "ProgForEach":
            new_ctx = ctx | _var_names(node.get("iter"))
            _walk_ir(node.get("body"), new_ctx, producer_refs, return_frontier)
            _walk_ir(node.get("orelse"), new_ctx, producer_refs, return_frontier)
            return
        if t == "ProgWhile":
            new_ctx = ctx | _var_names(node.get("cond"))
            _walk_ir(node.get("body"), new_ctx, producer_refs, return_frontier)
            _walk_ir(node.get("orelse"), new_ctx, producer_refs, return_frontier)
            return
        # generic container (ProgSeq/ProgDefFnParam/ProgTryOr/expr nodes/...)
        for v in node.values():
            _walk_ir(v, ctx, producer_refs, return_frontier)
        return
    if isinstance(node, list):
        for v in node:
            _walk_ir(v, ctx, producer_refs, return_frontier)


def backward_depth(ir: Dict[str, Any], params: Sequence[str]) -> Dict[str, float]:
    """-> {param_name: min hop-count backward from a return value to that
    parameter, along data + gating dependencies}; unreached (dead)
    parameters get `math.inf`. BFS over `producer_refs`, frontier-seeded
    from every return site (see module docstring)."""
    producer_refs: Dict[str, Set[str]] = {}
    return_frontier: Set[str] = set()
    _walk_ir(ir, frozenset(), producer_refs, return_frontier)

    dist: Dict[str, int] = {}
    q: deque = deque((name, 0) for name in sorted(return_frontier))
    while q:
        name, depth = q.popleft()
        if name in dist and dist[name] <= depth:
            continue
        dist[name] = depth
        for ref in sorted(producer_refs.get(name, ())):
            if ref not in dist or dist[ref] > depth + 1:
                q.append((ref, depth + 1))
    return {p: float(dist.get(p, math.inf)) for p in params}


def backward_rank_of_row_positions(dist_by_solution_param: Dict[str, float],
                                   solution_params: Sequence[str],
                                   perm: Sequence[int]) -> List[int]:
    """-> for each ROW position j (0-indexed), its rank (0 = tried first
    under backward ordering) among the task's row positions. `perm[i]`
    is the row position feeding solution parameter i (the ceiling
    measurement's own convention, `_mapped_env`); identity when there is
    no retrieval permutation (the native-accept population)."""
    arity = len(solution_params)
    # depth_of_row_position[j] = dist of the solution param that row
    # position j feeds.
    row_to_solution_idx = [None] * arity
    for i, j in enumerate(perm):
        row_to_solution_idx[j] = i
    depth_of_row = [dist_by_solution_param[solution_params[row_to_solution_idx[j]]]
                    for j in range(arity)]
    order = sorted(range(arity), key=lambda j: (depth_of_row[j], j))
    rank = [0] * arity
    for rank_idx, j in enumerate(order):
        rank[j] = rank_idx
    return rank


def relabel_examples(revealed: List[Dict[str, Any]], rank: Sequence[int]) -> List[Dict[str, Any]]:
    """Build a fresh `examples` row list with row-argument position j
    renamed to `_ARG_LETTERS[rank[j]]` — a real relabelling of which
    letter-name the SynthEnumerate spec binds to which row-argument
    VALUE STREAM, never a reordering of the search algorithm itself."""
    arity = len(rank)
    out = []
    for row in revealed:
        orig_keys = list(row["inputs"].keys())
        assert len(orig_keys) == arity
        new_inputs = {_ARG_LETTERS[rank[j]]: row["inputs"][orig_keys[j]] for j in range(arity)}
        out.append({"inputs": new_inputs, "output": row["expected"]})
    return out


def current_order_examples(revealed: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [{"inputs": dict(row["inputs"]), "output": row["expected"]} for row in revealed]


def drive_synth_enumerate(examples: List[Dict[str, Any]]) -> Dict[str, Any]:
    """The REAL Rust Term, pure (`Substrate()._inner.evaluate`, no
    substrate mutation) — the same call shape
    `domains.prog_synthesis.run_enumerate` uses in production, minus the
    graph-adapter plumbing (no `ops`/`consts` override -> engine
    defaults, byte-identical to production's own unset-ops/-consts call)."""
    s = srs.Substrate()
    spec = {"type": "SynthEnumerate",
            "examples": {"type": "Lit", "value": examples},
            "max_size": SYNTH_MAX_SIZE, "max_candidates": SYNTH_MAX_CANDIDATES,
            "saturate_k": SYNTH_SATURATE_K, "field": ""}
    return s._inner.evaluate(spec, {})


def _contains_set(x: Any) -> bool:
    """True if a Python set/frozenset appears anywhere in `x`. A raw set
    cannot cross the `{"type":"Lit","value":...}` JSON-Term boundary
    `SynthEnumerate`'s own `examples` param uses (the SAME boundary
    `domains.prog_synthesis.run_enumerate` uses in production) — this is
    a genuine, previously-unnamed residual this probe surfaced (task 115:
    `a=[{1,2}, {}, {}]`, a set nested inside a list argument), NOT
    something this script silently repairs. Tasks that hit it are marked
    `skipped` with this reason, honestly, rather than crashing or being
    quietly coerced."""
    if isinstance(x, (set, frozenset)):
        return True
    if isinstance(x, (list, tuple)):
        return any(_contains_set(v) for v in x)
    if isinstance(x, dict):
        return any(_contains_set(v) for v in x.values())
    return False


def _revealed_rows_for(task: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
    parsed = ms.parse_asserts(task)
    spec = ms.split_rows(parsed["rows"], "primary")
    if not spec["runnable"]:
        return None
    return spec["revealed"]


def build_ha3_population(all_tasks_by_id: Dict[int, Dict[str, Any]],
                         pool_by_id: Dict[int, Dict[str, Any]],
                         ceiling: Dict[str, Any],
                         endgame_full_rows: List[Dict[str, Any]]
                         ) -> List[Dict[str, Any]]:
    """-> one entry per HA3 population task: {task_id, source, arity,
    solution_ir, solution_params, perm}. `source` is 'retrieval_ceiling'
    (12 ids) or 'native_enumerate_accept' (6 ids); the two populations are
    disjoint by construction (retrieval-ceiling ids are all `gapped:*` or
    `accepted_holdout_fail` in FULL-R3 — never `pass` outcome rows, since
    a genuinely enumerator-solved task would not need a retrieval oracle
    to establish a known solution)."""
    entries: List[Dict[str, Any]] = []
    seen_ids: Set[int] = set()

    for row in ceiling["runnable_rows"]:
        rung = row["best_rung_heldout_honest"]
        if rung == "none":
            continue
        tid = row["task_id"]
        if rung == "a":
            exemplars = sorted(row["rung_a"]["heldout_pass_exemplars"])
            exemplar_tid = exemplars[0]
            perm = list(range(row["arity"]))
            edit = None
        elif rung == "b":
            combos = row["rung_b"]["heldout_pass_combos"]
            combos = sorted(combos, key=lambda c: (c["exemplar"], c["perm"]))
            exemplar_tid = combos[0]["exemplar"]
            perm = list(combos[0]["perm"])
            edit = None
        elif rung == "c":
            anchor = row["rung_c"]["anchor"]
            exemplar_tid = anchor["exemplar"]
            perm = list(anchor["perm"])
            edit = row["rung_c"]["edit"]
        else:
            continue
        ex = pool_by_id[exemplar_tid]
        ir = ex["ir"]
        if edit is not None:
            point = {"path": tuple(edit["path"])}
            ir = roc._apply_edit(ir, point, edit["to"])
        entries.append({"task_id": tid, "source": "retrieval_ceiling",
                        "arity": row["arity"], "solution_ir": ir,
                        "solution_params": list(ex["params"]), "perm": perm,
                        "provenance": {"rung": rung, "exemplar": exemplar_tid,
                                      "edit": edit}})
        seen_ids.add(tid)

    for row in endgame_full_rows:
        if row.get("outcome") != "pass" or row.get("enumerate_outcome") != "ok":
            continue
        tid = row["task_id"]
        ir = row["ir"]
        params = [s["name"] for s in ir["stmts"] if s["type"] == "ProgDefFnParam"]
        entries.append({"task_id": tid, "source": "native_enumerate_accept",
                        "arity": len(params), "solution_ir": ir,
                        "solution_params": params, "perm": list(range(len(params))),
                        "provenance": {"attempts": row.get("attempts")}})
        assert tid not in seen_ids, "retrieval-ceiling/native populations overlap on task %d" % tid
        seen_ids.add(tid)

    entries.sort(key=lambda e: e["task_id"])
    return entries


def measure_backward_ordering(all_tasks_by_id: Dict[int, Dict[str, Any]],
                              population: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for entry in population:
        tid = entry["task_id"]
        task = all_tasks_by_id[tid]
        revealed = _revealed_rows_for(task)
        if revealed is None or len(revealed[0]["inputs"]) != entry["arity"]:
            rows.append({"task_id": tid, "source": entry["source"], "skipped": True,
                        "skip_reason": "revealed_rows_unavailable_or_arity_mismatch"})
            continue
        if _contains_set(revealed):
            rows.append({"task_id": tid, "source": entry["source"], "skipped": True,
                        "skip_reason": "set_valued_row_crosses_lit_term_json_boundary"})
            continue
        dist = backward_depth(entry["solution_ir"], entry["solution_params"])
        rank = backward_rank_of_row_positions(dist, entry["solution_params"], entry["perm"])
        reorders = rank != list(range(entry["arity"]))

        cur_examples = current_order_examples(revealed)
        bwd_examples = relabel_examples(revealed, rank)

        cur_out = drive_synth_enumerate(cur_examples)
        bwd_out = drive_synth_enumerate(bwd_examples)

        if cur_out.get("found") and bwd_out.get("found"):
            if bwd_out["tested"] < cur_out["tested"]:
                verdict = "backward_wins"
            elif bwd_out["tested"] > cur_out["tested"]:
                verdict = "current_wins"
            else:
                verdict = "tie"
        else:
            verdict = "not_found:cur=%s,bwd=%s" % (cur_out.get("halt_reason"),
                                                    bwd_out.get("halt_reason"))

        rows.append({
            "task_id": tid, "source": entry["source"], "arity": entry["arity"],
            "n_revealed": len(revealed), "provenance": entry["provenance"],
            "backward_depth_by_solution_param": dict(zip(entry["solution_params"],
                                                         (dist[p] if dist[p] != math.inf else None
                                                          for p in entry["solution_params"]))),
            "row_position_rank_backward": rank, "reorders_vs_current": reorders,
            "current": {"tested": cur_out.get("tested"), "found": cur_out.get("found"),
                       "size": cur_out.get("size"), "halt_reason": cur_out.get("halt_reason"),
                       "term_str": cur_out.get("term_str")},
            "backward": {"tested": bwd_out.get("tested"), "found": bwd_out.get("found"),
                        "size": bwd_out.get("size"), "halt_reason": bwd_out.get("halt_reason"),
                        "term_str": bwd_out.get("term_str")},
            "verdict": verdict,
        })
    return rows


def ha3_aggregate(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    usable = [r for r in rows if not r.get("skipped")]
    reordering = [r for r in usable if r["reorders_vs_current"]]
    trivial = [r for r in usable if not r["reorders_vs_current"]]
    wins = sum(1 for r in reordering if r["verdict"] == "backward_wins")
    losses = sum(1 for r in reordering if r["verdict"] == "current_wins")
    ties = sum(1 for r in reordering if r["verdict"] == "tie")
    not_found = sum(1 for r in reordering if r["verdict"].startswith("not_found"))
    trivial_all_tie = all(r["current"]["tested"] == r["backward"]["tested"] for r in trivial
                          if r["current"]["found"] and r["backward"]["found"])
    tested_deltas = [r["backward"]["tested"] - r["current"]["tested"] for r in reordering
                     if r["current"]["found"] and r["backward"]["found"]]
    return {
        "n_total": len(rows), "n_skipped": len(rows) - len(usable),
        "n_usable": len(usable),
        "n_trivial_no_reorder_possible_or_tied": len(trivial),
        "trivial_rows_all_tested_equal": trivial_all_tie,
        "n_reordering_cases": len(reordering),
        "reordering_task_ids": sorted(r["task_id"] for r in reordering),
        "backward_wins": wins, "current_wins": losses, "ties": ties, "not_found": not_found,
        "mean_tested_delta_backward_minus_current": (
            round(sum(tested_deltas) / len(tested_deltas), 3) if tested_deltas else None),
        "tested_deltas_by_task": {str(r["task_id"]): r["backward"]["tested"] - r["current"]["tested"]
                                  for r in reordering
                                  if r["current"]["found"] and r["backward"]["found"]},
    }


# --------------------------------------------------------------------------- #
#  SYNTHETIC MECHANISM CHECK — the real MBPP oracle population (above) turns
#  out to be dominated by FLAT, single-return, single-hop expressions: with
#  no `ProgAssignVar`/`ProgAugAssign` chain, `backward_depth` correctly ties
#  every directly-referenced parameter at depth 0 (there is no statement-
#  level data dependency to order), so genuine reordering only fires for
#  the two structural exceptions actually found (106's aug-assign chain,
#  464's dead parameter) — a fact about the CORPUS at the grain
#  `SynthEnumerate` operates over today (flat leaf search), not a defect in
#  the walker. Crichton's backward-tracing finding is about MULTI-STATEMENT
#  program comprehension; the natural home for it in this architecture is
#  the multi-hole DESCENT tree (S3's actual target — intermediate holes ARE
#  assignment-shaped steps), not the flat single-call SynthEnumerate spec.
#  This block hand-builds a few small multi-hop-dependency hub-IR programs
#  (the exact shape a descent tree's holes already produce) OFF-CORPUS —
#  never mixed into the MBPP population or its aggregate — to answer a
#  narrower, prior question: does the relabelling LEVER itself have any
#  causal power over `tested` when a real chain exists? (It does, per the
#  ad-hoc `a-b` vs `b-a` check during this probe's design: 191 vs 199
#  tested on a trivial 2-var spec.) Still driven via the REAL Term.
# --------------------------------------------------------------------------- #
def _synthetic_checks() -> List[Dict[str, Any]]:
    chain2_ir = {
        "type": "ProgSeq", "stmts": [
            {"type": "ProgDefFnParam", "name": "a", "default": None},
            {"type": "ProgDefFnParam", "name": "b", "default": None},
            {"type": "ProgDefFnParam", "name": "c", "default": None},
            {"type": "ProgAssignVar", "name": "x",
             "value": {"type": "Minus", "a": {"type": "Var", "name": "a"},
                      "b": {"type": "Var", "name": "b"}}},
            {"type": "ProgReturn",
             "value": {"type": "Minus", "a": {"type": "Var", "name": "x"},
                      "b": {"type": "Var", "name": "c"}}},
        ]}
    chain2_rows = [
        {"inputs": {"a": 5, "b": 2, "c": 1}, "expected": 2},
        {"inputs": {"a": 10, "b": 3, "c": 4}, "expected": 3},
        {"inputs": {"a": 1, "b": 1, "c": 1}, "expected": -1},
    ]
    chain3_ir = {
        "type": "ProgSeq", "stmts": [
            {"type": "ProgDefFnParam", "name": "a", "default": None},
            {"type": "ProgDefFnParam", "name": "b", "default": None},
            {"type": "ProgDefFnParam", "name": "c", "default": None},
            {"type": "ProgDefFnParam", "name": "d", "default": None},
            {"type": "ProgAssignVar", "name": "x",
             "value": {"type": "Minus", "a": {"type": "Var", "name": "a"},
                      "b": {"type": "Var", "name": "b"}}},
            {"type": "ProgAssignVar", "name": "y",
             "value": {"type": "Minus", "a": {"type": "Var", "name": "x"},
                      "b": {"type": "Var", "name": "c"}}},
            {"type": "ProgReturn",
             "value": {"type": "Minus", "a": {"type": "Var", "name": "y"},
                      "b": {"type": "Var", "name": "d"}}},
        ]}
    chain3_rows = [
        {"inputs": {"a": 20, "b": 2, "c": 1, "d": 3}, "expected": 14},
        {"inputs": {"a": 15, "b": 4, "c": 2, "d": 1}, "expected": 8},
        {"inputs": {"a": 9, "b": 1, "c": 1, "d": 1}, "expected": 6},
    ]
    return [
        {"id": "synthetic_chain2", "arity": 3, "params": ["a", "b", "c"],
         "ir": chain2_ir, "rows": chain2_rows,
         "description": "x=a-b; return x-c (one ProgAssignVar hop; c is the "
                        "shallowest producer of the output, a/b are one hop "
                        "further back)"},
        {"id": "synthetic_chain3", "arity": 4, "params": ["a", "b", "c", "d"],
         "ir": chain3_ir, "rows": chain3_rows,
         "description": "x=a-b; y=x-c; return y-d (two-hop chain; d "
                        "shallowest, c one hop, a/b two hops back)"},
    ]


def measure_synthetic_mechanism_check() -> List[Dict[str, Any]]:
    rows = []
    for case in _synthetic_checks():
        dist = backward_depth(case["ir"], case["params"])
        perm = list(range(case["arity"]))
        rank = backward_rank_of_row_positions(dist, case["params"], perm)
        cur_examples = current_order_examples(case["rows"])
        bwd_examples = relabel_examples(case["rows"], rank)
        cur_out = drive_synth_enumerate(cur_examples)
        bwd_out = drive_synth_enumerate(bwd_examples)
        if cur_out.get("found") and bwd_out.get("found"):
            if bwd_out["tested"] < cur_out["tested"]:
                verdict = "backward_wins"
            elif bwd_out["tested"] > cur_out["tested"]:
                verdict = "current_wins"
            else:
                verdict = "tie"
        else:
            verdict = "not_found:cur=%s,bwd=%s" % (cur_out.get("halt_reason"), bwd_out.get("halt_reason"))
        rows.append({
            "id": case["id"], "description": case["description"],
            "backward_depth_by_param": dict(zip(case["params"],
                                                (dist[p] if dist[p] != math.inf else None
                                                 for p in case["params"]))),
            "row_position_rank_backward": rank,
            "current": {"tested": cur_out.get("tested"), "found": cur_out.get("found"),
                       "term_str": cur_out.get("term_str")},
            "backward": {"tested": bwd_out.get("tested"), "found": bwd_out.get("found"),
                        "term_str": bwd_out.get("term_str")},
            "verdict": verdict,
        })
    return rows


# --------------------------------------------------------------------------- #
#  MEASUREMENT 2 — HA4 search-reach sizing, fresh recompute (see module
#  docstring's staleness finding).
# --------------------------------------------------------------------------- #
_MUTATING_SUBFEATURES = frozenset({
    "collection_method:append", "collection_method:add", "collection_method:remove",
    "collection_method:reverse", "collection_method:pop", "collection_method:extend",
    "collection_method:sort", "collection_method:insert", "dict_method:setdefault",
    "dict_method:update",
})
_COMPREHENSION_BLOCKERS = frozenset({"CompTargetComplex", "CompMultiClause",
                                     "ComprehensionDict", "ComprehensionSet"})
_KWARGS_BLOCKERS = frozenset({"KwargsCall", "StarArgsCall", "StarArgsParam"})


def _fresh_program_row(task: Dict[str, Any]) -> Dict[str, Any]:
    """Mirrors scripts/mbpp_blocker_histogram.py::measure()'s program-side
    branch exactly (same helper calls, same field names) — reused, not
    reimplemented, and run FRESH against the CURRENT emit_prog_ir (see
    the module docstring's staleness finding: the cached artifact
    predates a real emitter change on exactly the mutating-method axis)."""
    code = task["code"]
    test_list = task["test_list"]
    entry_name, tree, defs, resolve_err = resolve_entry(code, test_list)
    row: Dict[str, Any] = {"task_id": task["task_id"], "entry_resolve_error": resolve_err,
                           "entry_function": entry_name}
    emit_res = None
    emit_err = None
    if entry_name is not None:
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                emit_res = emit_prog_ir(code, name=entry_name)
        except Exception as e:  # noqa: BLE001 — recorded, never fatal to the sweep
            emit_err = "%s: %s" % (type(e).__name__, str(e)[:160])
    row["emit_error"] = emit_err

    if emit_res is None:
        row["ok"] = False
        row["blockers"] = ["EMIT_FAILED"] if (emit_err or resolve_err) else []
        row["structural_families"] = sorted({structural_family(b) for b in row["blockers"]})
        row["extern_families"] = []
        row["recv_methods"] = []
    elif emit_res["ok"]:
        row["ok"] = True
        row["blockers"] = []
        row["structural_families"] = []
        row["predictable"] = emit_res["predictable"]
        row["recv_methods"] = emit_res["recv_methods"]
        from domains.prog_ir_emit import NATIVE_ORACLES
        fams = extern_families(emit_res["externs"], emit_res["recv_methods"], NATIVE_ORACLES)
        row["extern_families"] = sorted(fams)
    else:
        row["ok"] = False
        row["blockers"] = emit_res["blockers"]
        row["structural_families"] = sorted({structural_family(b) for b in emit_res["blockers"]})
        row["extern_families"] = []
        row["recv_methods"] = []

    subfeats: Dict[str, int] = {}
    if entry_name is not None:
        fn_node = next((d for d in defs if d.name == entry_name), None)
        if fn_node is not None:
            subfeats = dict(subconstruct_features(fn_node))
    row["subconstruct_features"] = subfeats
    return row


def _lever_flags(row: Dict[str, Any]) -> Dict[str, bool]:
    blockers = set(row.get("blockers") or [])
    subfeats = set(row.get("subconstruct_features") or {})
    externs = set(row.get("extern_families") or [])
    has_recv_blocker = any(b.startswith("RecvMethod:") for b in blockers)
    return {
        "mutating_method_writeback": has_recv_blocker or bool(subfeats & _MUTATING_SUBFEATURES),
        "comprehension_forms": bool(blockers & _COMPREHENSION_BLOCKERS),
        "kwargs": bool(blockers & _KWARGS_BLOCKERS),
        "map_lambda": "Lambda" in blockers,
        "regex": "regex" in externs,
    }


_LEVERS = ("mutating_method_writeback", "comprehension_forms", "kwargs", "map_lambda", "regex")


def measure_search_reach(all_tasks_by_id: Dict[int, Dict[str, Any]],
                         enum_failed_ids: List[int]) -> Dict[str, Any]:
    per_task: Dict[int, Dict[str, Any]] = {}
    flags: Dict[int, Dict[str, bool]] = {}
    for tid in enum_failed_ids:
        task = all_tasks_by_id[tid]
        row = _fresh_program_row(task)
        per_task[tid] = row
        flags[tid] = _lever_flags(row)

    lever_ids = {lv: sorted(tid for tid in enum_failed_ids if flags[tid][lv]) for lv in _LEVERS}
    overlap: Dict[str, Dict[str, int]] = {}
    for lv_a in _LEVERS:
        overlap[lv_a] = {}
        set_a = set(lever_ids[lv_a])
        for lv_b in _LEVERS:
            overlap[lv_a][lv_b] = len(set_a & set(lever_ids[lv_b]))

    exclusive_ids = {}
    for lv in _LEVERS:
        others = set()
        for lv2 in _LEVERS:
            if lv2 != lv:
                others |= set(lever_ids[lv2])
        exclusive_ids[lv] = sorted(set(lever_ids[lv]) - others)

    ranked = sorted(_LEVERS, key=lambda lv: (-len(exclusive_ids[lv]), lv))

    any_named = set()
    for lv in _LEVERS:
        any_named |= set(lever_ids[lv])
    ok_already = sorted(tid for tid in enum_failed_ids if per_task[tid].get("ok") and tid not in any_named)
    other_named_blocker = sorted(
        tid for tid in enum_failed_ids
        if tid not in any_named and tid not in ok_already
        and per_task[tid].get("blockers") and per_task[tid]["blockers"] != ["EMIT_FAILED"])
    unresolved = sorted(tid for tid in enum_failed_ids
                        if per_task[tid].get("entry_resolve_error") is not None
                        or per_task[tid].get("blockers") == ["EMIT_FAILED"])
    residual_none = sorted(set(enum_failed_ids) - any_named - set(ok_already)
                           - set(other_named_blocker) - set(unresolved))

    return {
        "n_gapped_enumerate_failed": len(enum_failed_ids),
        "denominator_note": ("denominator is FULL-R3's own gapped:enumerate_failed "
                             "population (%d/257 = %.1f%% of the 257-task PRIMARY test "
                             "split this run) — the plan's cited 55.3%% is arc-2 FULL's "
                             "figure over its own outcome population, not re-derived "
                             "here; both are reported so a reader never conflates them."
                             % (len(enum_failed_ids), 100.0 * len(enum_failed_ids) / 257)),
        "lever_task_ids": lever_ids,
        "lever_counts": {lv: len(lever_ids[lv]) for lv in _LEVERS},
        "overlap_matrix": overlap,
        "exclusive_task_ids": exclusive_ids,
        "exclusive_counts": {lv: len(exclusive_ids[lv]) for lv in _LEVERS},
        "ranked_by_exclusive_mass": ranked,
        "ok_already_no_named_lever": ok_already,
        "n_ok_already_no_named_lever": len(ok_already),
        "other_named_blocker_no_five_lever": other_named_blocker,
        "n_other_named_blocker": len(other_named_blocker),
        "unresolved_entry_or_emit": unresolved,
        "n_unresolved": len(unresolved),
        "residual_none_of_the_above": residual_none,
        "n_residual_none_of_the_above": len(residual_none),
        "staleness_note": (
            "results/mbpp_blocker_histogram.json reports ZERO RecvMethod:* "
            "blockers across all 427 tasks (measured 2026-07-31); a live "
            "re-run of emit_prog_ir today on task 307's own code (list.append) "
            "returns blockers=['RecvMethod:append'] — the cached histogram "
            "predates domains/prog_ir_emit.py's current _RECV_BLOCKED_METHODS "
            "table. This measurement recomputes ALL FIVE levers FRESH per "
            "task against the CURRENT emitter/ast-walk rather than trust the "
            "cached per_task rows for any of them."),
        "per_task_lever_flags": {str(tid): flags[tid] for tid in enum_failed_ids},
    }


# --------------------------------------------------------------------------- #
#  determinism + main
# --------------------------------------------------------------------------- #
def _sig(obj: Any) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, default=str).encode()).hexdigest()


def main() -> None:
    t0 = time.time()
    with open(FIXTURE_PATH) as f:
        all_tasks = json.load(f)
    with open(PROVENANCE_PATH) as f:
        provenance = json.load(f)
    with open(CEILING_PATH) as f:
        ceiling = json.load(f)
    with open(ENDGAME_PATH) as f:
        endgame = json.load(f)

    all_tasks_by_id = {t["task_id"]: t for t in all_tasks}
    splits = q0_split_tasks(all_tasks)
    train_tasks = splits["train"]
    assert len(train_tasks) == 120

    pool, _emit_rows = roc.build_pool(train_tasks)
    pool_by_id = {ex["task_id"]: ex for ex in pool}

    full_rows = endgame["arms"]["full_r3"]["runnable_rows"]
    enum_failed_ids = sorted(r["task_id"] for r in full_rows
                             if r["outcome"] == "gapped:enumerate_failed")

    population = build_ha3_population(all_tasks_by_id, pool_by_id, ceiling, full_rows)

    # twin run — measurement 1 (SynthEnumerate is pure; the walker/relabel
    # code is pure Python) — proves determinism the same way every other
    # phase in this tree does.
    m1_run1 = measure_backward_ordering(all_tasks_by_id, population)
    m1_run2 = measure_backward_ordering(all_tasks_by_id, population)
    m1_sig1, m1_sig2 = _sig(m1_run1), _sig(m1_run2)

    synth_run1 = measure_synthetic_mechanism_check()
    synth_run2 = measure_synthetic_mechanism_check()
    synth_sig1, synth_sig2 = _sig(synth_run1), _sig(synth_run2)

    m2_run1 = measure_search_reach(all_tasks_by_id, enum_failed_ids)
    m2_run2 = measure_search_reach(all_tasks_by_id, enum_failed_ids)
    m2_sig1, m2_sig2 = _sig(m2_run1), _sig(m2_run2)

    ha3_agg = ha3_aggregate(m1_run1)

    artifact = {
        "_README": (
            "Arc 4 S0 track B — HA3 (data-dependency backward-ordering "
            "probe, driven live against the real SynthEnumerate Term) and "
            "HA4 (search-reach lever sizing, freshly recomputed against the "
            "current emitter — see 'staleness_note'). Pure measurement; no "
            "synthesis/engine/seed code touched."),
        "measured_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "provenance_ref": os.path.relpath(PROVENANCE_PATH, ROOT),
        "provenance": provenance,
        "what_is_simulated_vs_measured": {
            "measurement_1_backward_ordering": "MEASURED, not simulated — "
                "drives the real Rust SynthEnumerate Term (Substrate()._inner."
                "evaluate) on each task's own revealed rows, twice, with the "
                "row-argument dict keys relabelled per ordering (current vs "
                "backward-from-output). `tested` is the engine's own counter. "
                "NOT reproduced: the multi-hole descent tree in "
                "domains/prog_synthesis.py (spawn_subgoal's per-hole "
                "exclude/const-drop scoping) — this drives the FLAT "
                "(whole-spec) SynthEnumerate call only, the same shape "
                "run_enumerate uses for a non-hole accept. The def-use/"
                "data-dependency depth used to build the backward ordering "
                "is computed by this script's own mechanical IR walker "
                "(backward_depth), not by any component of the synthesis "
                "engine.",
            "measurement_2_search_reach": "MEASURED fresh — every lever flag "
                "is read off a live re-run of the CURRENT domains.prog_ir_emit."
                "emit_prog_ir + mbpp_blocker_histogram.py's own ast-walk "
                "helpers (resolve_entry/structural_family/extern_families/"
                "subconstruct_features, imported and reused verbatim) against "
                "each gapped:enumerate_failed task's own reference code — "
                "NOT read from the cached results/mbpp_blocker_histogram.json "
                "artifact, which is demonstrably stale on the mutating-method "
                "axis (see 'staleness_note' in the search_reach block). "
                "'Reachable' here means 'the task's own known-correct "
                "reference solution exhibits this construct' — a NECESSARY-"
                "condition proxy for 'the enumerator/emitter needs this lever "
                "to have any chance', never a sufficient/guaranteed-fix claim "
                "(a task can need MORE than one lever; the overlap matrix and "
                "exclusive-mass split make that visible rather than hiding "
                "it behind a single count).",
        },
        "ha3_backward_ordering_probe": {
            "population": [
                {"task_id": e["task_id"], "source": e["source"], "arity": e["arity"],
                 "provenance": e["provenance"]}
                for e in population],
            "n_population": len(population),
            "rows": m1_run1,
            "aggregate": ha3_agg,
            "determinism": {"identical": m1_sig1 == m1_sig2,
                           "hash_run1": m1_sig1, "hash_run2": m1_sig2},
        },
        "ha3_synthetic_mechanism_check": {
            "note": ("OFF-CORPUS, hand-built multi-hop-dependency hub-IR "
                     "programs (the shape a descent tree's holes already "
                     "produce) — NOT part of the MBPP oracle population or "
                     "its aggregate above. Answers a narrower prior "
                     "question: does the relabelling lever have ANY causal "
                     "power over `tested` when a genuine multi-hop chain "
                     "exists? Driven via the same real Term."),
            "rows": synth_run1,
            "determinism": {"identical": synth_sig1 == synth_sig2,
                           "hash_run1": synth_sig1, "hash_run2": synth_sig2},
        },
        "ha4_search_reach_sizing": dict(m2_run1, determinism={
            "identical": m2_sig1 == m2_sig2, "hash_run1": m2_sig1, "hash_run2": m2_sig2}),
        "environment": {"python": sys.version.split()[0]},
        "elapsed_seconds": round(time.time() - t0, 2),
    }
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w") as f:
        json.dump(artifact, f, indent=1, sort_keys=False)
        f.write("\n")
    print("wrote", OUT_PATH)
    print("HA3 aggregate:", json.dumps(ha3_agg, indent=1))
    print("HA4 exclusive counts:", m2_run1["exclusive_counts"], "ranked:", m2_run1["ranked_by_exclusive_mass"])
    print("elapsed: %.1fs" % artifact["elapsed_seconds"])


if __name__ == "__main__":
    main()

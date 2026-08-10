#!/usr/bin/env python3
"""Extract ACTUAL seed draws from Python source by AST walk + abstract
interpretation.

WHY THIS IS NOT A GREP (VISION_PROTOCOL.md §12): the defect this rung audits was
invisible to any substring scan. The resolution-scale rung declares
`SEED_BLOCK = 79000` at the top of its file and then draws

    for t in range(N_BASE):                        # N_BASE = 50
        rng = random.Random(SEED_BLOCK + 400 + t)  # -> 79400..79449
        probes = video_probes(qs, gs, t, rng, SEED_BLOCK)   # interprocedural
        seed = SEED_BLOCK + 200 + t                # -> 79200..79249

    def video_probes(qs, gs, t, rng, seed):
        for label, off in (("G2c", 700), ("G2t", 800)):
            r2 = np.random.RandomState(seed + off + t)  # -> 79700.., 79800..

Nothing in that file contains the string "79200". Recovering it requires
constant propagation, range() expansion, tuple-unpacking loop targets, integer
folding, and interprocedural argument binding. That is what this module does.

WHAT IT CANNOT SEE -- stated here rather than implied away (prereg §4):

  1. Seeds from CLI args, os.environ, or config files (runtime values).
  2. Seeds derived from data: hash(x), len(pool), timestamps, file contents.
  3. Seeds crossing a MODULE boundary (imported constant seeded elsewhere).
     Interprocedural analysis here is INTRA-FILE only.
  4. Draws inside library/adapter code reached from a script, unless that file
     is itself analysed.
  5. CONSECUTIVE draws from one generator. `default_rng(S)` burns an unbounded
     stream downstream of S; the ledger's unit is the SEED INTEGER and that is
     what is measured. A rung that reserves 1000 integers and seeds once at the
     base draws ONE seed by this measure. This is a DEFINITIONAL choice, not an
     oversight -- see the results doc, which reports both readings.
  6. Non-Python seeds (shell scripts, Rust, notebooks).
  7. Any expression whose abstract value exceeds ENUM_CAP -> reported UNKNOWN.

Every one of those yields UNKNOWN or silence, never a wrong integer. The tool
under-reports; it does not over-report. `unknown_sinks` in the output is the
honest count of sink sites whose value could not be resolved.
"""
from __future__ import annotations

import ast
import json
import os
import sys
from typing import Iterable

# A finite enumerated set larger than this is abandoned as UNKNOWN rather than
# silently truncated -- a truncated set would under-report a real collision.
ENUM_CAP = 20000
FIXPOINT_ROUNDS = 6


class Unknown:
    """Top of the abstract domain. Distinct from the empty set."""

    _inst = None

    def __new__(cls):
        if cls._inst is None:
            cls._inst = super().__new__(cls)
        return cls._inst

    def __repr__(self):
        return "UNKNOWN"


UNKNOWN = Unknown()

# Calls whose first positional argument (or `seed=` keyword) is an RNG seed.
# Matched on the DOTTED PATH SUFFIX of the callee, so `np.random.default_rng`,
# `numpy.random.default_rng` and a `from numpy.random import default_rng` all hit.
SEED_SINKS = {
    "default_rng",
    "RandomState",
    "Random",
    "seed",            # random.seed / np.random.seed
    "manual_seed",     # torch
    "PCG64",
    "MT19937",
    "Philox",
    "SFC64",
    "set_seed",
    "seed_everything",
}

# `seed`-suffixed callees that are NOT RNG seeding, to keep false sinks out.
SINK_DENY = {
    "seed_everything_off",
}


def _dotted(node: ast.AST) -> str | None:
    """Return the dotted path of a callee expression, or None."""
    parts: list[str] = []
    cur = node
    while isinstance(cur, ast.Attribute):
        parts.append(cur.attr)
        cur = cur.value
    if isinstance(cur, ast.Name):
        parts.append(cur.id)
        return ".".join(reversed(parts))
    return None


def _is_sink(callee: str | None) -> bool:
    if not callee:
        return False
    last = callee.rsplit(".", 1)[-1]
    if last in SINK_DENY:
        return False
    if last not in SEED_SINKS:
        return False
    # `self.seed(...)` / `obj.seed(...)` on a non-RNG object still counts: it is
    # more honest to over-collect sinks (they resolve to UNKNOWN or to a real
    # integer) than to miss a real draw.
    return True


def _as_set(v) -> frozenset | None:
    return v if isinstance(v, frozenset) else None


def _cap(vals: Iterable[int]):
    out = set()
    for x in vals:
        out.add(x)
        if len(out) > ENUM_CAP:
            return UNKNOWN
    return frozenset(out)


class FileAnalyser:
    """Abstract interpreter for one module.

    Domain: frozenset[int] (finite, capped) | UNKNOWN. Absence of a binding
    means "not an integer we can reason about" and evaluates to UNKNOWN.
    """

    def __init__(self, path: str, tree: ast.Module):
        self.path = path
        self.tree = tree
        self.funcs: dict[str, ast.FunctionDef] = {}
        # formal-parameter bindings discovered at call sites, unioned
        self.param_env: dict[str, dict[str, object]] = {}
        self.sinks: list[dict] = []
        self.unknown_sinks = 0
        self._collect_funcs(tree)

    def _collect_funcs(self, node):
        for n in ast.walk(node):
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self.funcs[n.name] = n

    # ---- expression evaluation -------------------------------------------

    def ev(self, node, env: dict) -> object:
        if isinstance(node, ast.Constant):
            return frozenset({node.value}) if isinstance(node.value, int) and not isinstance(node.value, bool) else UNKNOWN
        if isinstance(node, ast.Name):
            return env.get(node.id, UNKNOWN)
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
            v = self.ev(node.operand, env)
            s = _as_set(v)
            return _cap(-x for x in s) if s is not None else UNKNOWN
        if isinstance(node, ast.BinOp):
            return self._binop(node, env)
        if isinstance(node, ast.Call):
            callee = _dotted(node.func)
            if callee and callee.rsplit(".", 1)[-1] == "int" and node.args:
                return self.ev(node.args[0], env)
            return UNKNOWN
        if isinstance(node, ast.IfExp):
            a, b = self.ev(node.body, env), self.ev(node.orelse, env)
            sa, sb = _as_set(a), _as_set(b)
            if sa is None or sb is None:
                return UNKNOWN
            return _cap(sa | sb)
        return UNKNOWN

    def _binop(self, node, env):
        lv, rv = self.ev(node.left, env), self.ev(node.right, env)
        ls, rs = _as_set(lv), _as_set(rv)
        if ls is None or rs is None:
            return UNKNOWN
        if len(ls) * len(rs) > ENUM_CAP:
            return UNKNOWN
        op = node.op
        out = set()
        try:
            for a in ls:
                for b in rs:
                    if isinstance(op, ast.Add):
                        out.add(a + b)
                    elif isinstance(op, ast.Sub):
                        out.add(a - b)
                    elif isinstance(op, ast.Mult):
                        out.add(a * b)
                    elif isinstance(op, ast.FloorDiv):
                        if b == 0:
                            return UNKNOWN
                        out.add(a // b)
                    elif isinstance(op, ast.Mod):
                        if b == 0:
                            return UNKNOWN
                        out.add(a % b)
                    elif isinstance(op, ast.Pow):
                        if b < 0 or b > 64 or abs(a) > 1 << 20:
                            return UNKNOWN
                        out.add(a ** b)
                    else:
                        return UNKNOWN
                    if len(out) > ENUM_CAP:
                        return UNKNOWN
        except (OverflowError, ValueError, ZeroDivisionError):
            return UNKNOWN
        return frozenset(out)

    def _iter_values(self, node, env) -> object:
        """Abstract value of the loop VARIABLE for `for <t> in <node>`."""
        if isinstance(node, ast.Call):
            callee = _dotted(node.func)
            if callee and callee.rsplit(".", 1)[-1] == "range":
                args = [self.ev(a, env) for a in node.args]
                if any(_as_set(a) is None for a in args):
                    return UNKNOWN
                sets = [_as_set(a) for a in args]
                out = set()
                if len(sets) == 1:
                    for n in sets[0]:
                        if n > ENUM_CAP:
                            return UNKNOWN
                        out.update(range(n))
                elif len(sets) >= 2:
                    step_set = sets[2] if len(sets) > 2 else {1}
                    for a in sets[0]:
                        for b in sets[1]:
                            for st in step_set:
                                if st == 0 or abs(b - a) > ENUM_CAP:
                                    return UNKNOWN
                                out.update(range(a, b, st))
                    if len(out) > ENUM_CAP:
                        return UNKNOWN
                return _cap(out)
            if callee and callee.rsplit(".", 1)[-1] == "enumerate":
                return UNKNOWN
        if isinstance(node, (ast.Tuple, ast.List, ast.Set)):
            vals = [self.ev(e, env) for e in node.elts]
            sets = [_as_set(v) for v in vals]
            if any(s is None for s in sets):
                return UNKNOWN
            out = set()
            for s in sets:
                out |= s
            return _cap(out)
        if isinstance(node, ast.Name):
            return env.get(node.id, UNKNOWN)
        return UNKNOWN

    def _bind_for_target(self, target, iter_node, env):
        """Bind loop target(s). Handles `for t in range(N)` and the
        tuple-unpacking form `for label, off in (("G2c",700),("G2t",800))`."""
        if isinstance(target, ast.Name):
            env[target.id] = self._iter_values(iter_node, env)
            return
        if isinstance(target, ast.Tuple) and isinstance(
            iter_node, (ast.Tuple, ast.List)
        ):
            # column-wise union over literal rows
            names = [e.id if isinstance(e, ast.Name) else None for e in target.elts]
            cols: list[set] = [set() for _ in names]
            ok = [True] * len(names)
            for row in iter_node.elts:
                if not isinstance(row, (ast.Tuple, ast.List)):
                    ok = [False] * len(names)
                    break
                for i, cell in enumerate(row.elts[: len(names)]):
                    v = self.ev(cell, env)
                    s = _as_set(v)
                    if s is None:
                        ok[i] = False
                    else:
                        cols[i] |= s
            for i, nm in enumerate(names):
                if nm:
                    env[nm] = frozenset(cols[i]) if ok[i] and cols[i] else UNKNOWN
            return
        for n in ast.walk(target):
            if isinstance(n, ast.Name):
                env[n.id] = UNKNOWN

    # ---- statement walking ------------------------------------------------

    def exec_body(self, body, env: dict, depth: int = 0):
        if depth > 12:
            return
        for stmt in body:
            self.exec_stmt(stmt, env, depth)

    def exec_stmt(self, stmt, env: dict, depth: int):
        if isinstance(stmt, ast.Assign):
            val = self.ev(stmt.value, env)
            for tgt in stmt.targets:
                if isinstance(tgt, ast.Name):
                    env[tgt.id] = val
                elif isinstance(tgt, ast.Tuple):
                    for e in tgt.elts:
                        if isinstance(e, ast.Name):
                            env[e.id] = UNKNOWN
            self._scan_calls(stmt.value, env)
            return
        if isinstance(stmt, ast.AnnAssign) and stmt.value is not None:
            if isinstance(stmt.target, ast.Name):
                env[stmt.target.id] = self.ev(stmt.value, env)
            self._scan_calls(stmt.value, env)
            return
        if isinstance(stmt, ast.AugAssign):
            if isinstance(stmt.target, ast.Name):
                env[stmt.target.id] = UNKNOWN
            self._scan_calls(stmt.value, env)
            return
        if isinstance(stmt, ast.For):
            self._scan_calls(stmt.iter, env)
            inner = dict(env)
            self._bind_for_target(stmt.target, stmt.iter, inner)
            self.exec_body(stmt.body, inner, depth + 1)
            self.exec_body(stmt.orelse, inner, depth + 1)
            # after the loop the variable is not reliably known
            for n in ast.walk(stmt.target):
                if isinstance(n, ast.Name):
                    env[n.id] = UNKNOWN
            return
        if isinstance(stmt, (ast.While, ast.If, ast.With, ast.Try)):
            for attr in ("test", "iter"):
                if getattr(stmt, attr, None) is not None:
                    self._scan_calls(getattr(stmt, attr), env)
            if isinstance(stmt, ast.With):
                for item in stmt.items:
                    self._scan_calls(item.context_expr, env)
            # both arms analysed in a COPY: a seed drawn in either arm is a
            # seed the program can draw.
            for sub in ("body", "orelse", "finalbody", "handlers"):
                blk = getattr(stmt, sub, None) or []
                if sub == "handlers":
                    for h in blk:
                        self.exec_body(h.body, dict(env), depth + 1)
                else:
                    self.exec_body(blk, dict(env), depth + 1)
            return
        if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            return  # analysed separately via call-site bindings
        if isinstance(stmt, (ast.Expr, ast.Return)):
            if stmt.value is not None:
                self._scan_calls(stmt.value, env)
            return

    def _scan_calls(self, node, env):
        """Record seed sinks and propagate call-site argument bindings."""
        if node is None:
            return
        for sub in ast.walk(node):
            if not isinstance(sub, ast.Call):
                continue
            callee = _dotted(sub.func)
            if _is_sink(callee):
                self._record_sink(sub, callee, env)
            if callee and callee in self.funcs:
                self._bind_call(self.funcs[callee], sub, env)

    def _record_sink(self, call, callee, env):
        arg = None
        if call.args:
            arg = call.args[0]
        else:
            for kw in call.keywords:
                if kw.arg in ("seed", "seed_value", "random_state"):
                    arg = kw.value
                    break
        if arg is None:
            # e.g. default_rng() with no argument -> nondeterministic, not a
            # ledger draw. Not counted as unknown; it consumes no seed integer.
            return
        val = self.ev(arg, env)
        s = _as_set(val)
        if s is None:
            self.unknown_sinks += 1
            self.sinks.append(
                {"file": self.path, "line": call.lineno, "sink": callee,
                 "seeds": None}
            )
            return
        ints = sorted(x for x in s if isinstance(x, int))
        if not ints:
            self.unknown_sinks += 1
            self.sinks.append(
                {"file": self.path, "line": call.lineno, "sink": callee,
                 "seeds": None}
            )
            return
        self.sinks.append(
            {"file": self.path, "line": call.lineno, "sink": callee,
             "seeds": ints}
        )

    def _bind_call(self, fn, call, env):
        formals = [a.arg for a in fn.args.args]
        binding = self.param_env.setdefault(fn.name, {})
        for i, act in enumerate(call.args):
            if i >= len(formals):
                break
            v = self.ev(act, env)
            prev = binding.get(formals[i])
            binding[formals[i]] = _join(prev, v)
        for kw in call.keywords:
            if kw.arg in formals:
                binding[kw.arg] = _join(binding.get(kw.arg), self.ev(kw.value, env))

    # ---- driver -----------------------------------------------------------

    def run(self) -> dict:
        module_env: dict[str, object] = {}
        # Round 0: module top level, establishing constants and call bindings.
        for _ in range(2):
            self.exec_body(self.tree.body, module_env)
        # Fixpoint over functions: a call site inside a function can bind
        # another function's parameters (video_probes is called from main()).
        for _ in range(FIXPOINT_ROUNDS):
            before = json.dumps(
                {k: sorted(v) if isinstance(v, frozenset) else "U"
                 for k, vv in self.param_env.items() for v in [vv]},
                default=str, sort_keys=True,
            )
            self.sinks = []
            self.unknown_sinks = 0
            self.exec_body(self.tree.body, dict(module_env))
            for name, fn in self.funcs.items():
                env = dict(module_env)
                env.update(self.param_env.get(name, {}))
                # unbound formals are UNKNOWN, never inherited from module scope
                for a in fn.args.args:
                    env.setdefault(a.arg, UNKNOWN)
                    if a.arg not in self.param_env.get(name, {}):
                        env[a.arg] = UNKNOWN
                self.exec_body(fn.body, env, depth=1)
            after = json.dumps(
                {k: sorted(v) if isinstance(v, frozenset) else "U"
                 for k, vv in self.param_env.items() for v in [vv]},
                default=str, sort_keys=True,
            )
            if before == after:
                break
        seeds: set[int] = set()
        for s in self.sinks:
            if s["seeds"]:
                seeds.update(s["seeds"])
        return {
            "file": self.path,
            "seeds": sorted(seeds),
            "sinks": self.sinks,
            "unknown_sinks": self.unknown_sinks,
        }


def _join(prev, v):
    if prev is None:
        return v
    ps, vs = _as_set(prev), _as_set(v)
    if ps is None or vs is None:
        return UNKNOWN
    return _cap(ps | vs)


def analyse_file(path: str) -> dict | None:
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            src = fh.read()
        tree = ast.parse(src, filename=path)
    except (SyntaxError, UnicodeDecodeError, OSError):
        return {"file": path, "seeds": [], "sinks": [], "unknown_sinks": 0,
                "parse_error": True}
    return FileAnalyser(path, tree).run()


def analyse_tree(roots: list[str]) -> dict:
    results, errors = [], 0
    for root in roots:
        if os.path.isfile(root) and root.endswith(".py"):
            paths = [root]
        else:
            paths = []
            for dirpath, dirnames, filenames in os.walk(root):
                dirnames[:] = [d for d in dirnames
                               if d not in {"__pycache__", ".git", "node_modules"}]
                paths.extend(os.path.join(dirpath, f)
                             for f in filenames if f.endswith(".py"))
        for p in sorted(paths):
            r = analyse_file(p)
            if r is None:
                continue
            if r.get("parse_error"):
                errors += 1
            if r["seeds"] or r["unknown_sinks"]:
                results.append(r)
    return {"files": results, "parse_errors": errors}


# ---- the reusable gate ----------------------------------------------------

def measured_seeds(paths: list[str]) -> set[int]:
    """All statically-resolvable seed integers drawn under `paths`."""
    out: set[int] = set()
    for f in analyse_tree(paths)["files"]:
        out.update(f["seeds"])
    return out


def check_block(paths, lo: int, hi: int, *, ledger_floor: int = 1000):
    """THE GATE. Assert declared [lo,hi] is a SUPERSET of what `paths` measurably
    draws, ignoring conventional low seeds below `ledger_floor` (0,1,3,... are
    determinism conveniences, not ledger allocations -- see results doc).

    Returns (ok, outside) where `outside` is the sorted list of ledger-range
    seeds drawn outside [lo, hi]. One line for a future rung:

        ok, bad = check_block(["scripts/my_rung.py"], 82000, 82999)
        assert ok, f"draws outside declared block: {bad}"
    """
    drawn = measured_seeds(paths if isinstance(paths, list) else [paths])
    outside = sorted(s for s in drawn
                     if s >= ledger_floor and not (lo <= s <= hi))
    return (not outside), outside


def main(argv):
    if len(argv) >= 4 and argv[1] == "--check":
        lo, hi = int(argv[2]), int(argv[3])
        ok, bad = check_block(list(argv[4:]), lo, hi)
        print(json.dumps({"declared": [lo, hi], "ok": ok, "outside": bad}))
        return 0 if ok else 1
    roots = argv[1:] or ["scripts"]
    print(json.dumps(analyse_tree(roots), indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

"""rust_rewrite_world — the self-hosting bootstrap WORLD ADAPTER.

The gamma-substrate agent IS Rust + graph (see CLAUDE.md). The Python
under `domains/` is, by the architecture rule, either (a) a thin world
adapter doing mechanical I/O, or (b) agent logic that VIOLATES the rule
and is on the path to being rewritten in Rust / moved to graph data.

The agent could not previously SEE its own Python surface: there was no
impl-substrate self-model, no list of "which of my Python modules are
agent-logic that must become Rust." This world supplies exactly that,
then feeds each agent-logic unit to the EXISTING code-authoring cortex
(`code_writing_cortex.CodeWritingCortex`) that already authors +
validates + installs Rust.

This file is a WORLD ADAPTER, and only that:

  * INGEST  — `enumerate_python_surface` walks the Python tree with the
              `ast` module and writes one `PythonUnit` graph node per
              module / function / method, carrying MECHANICALLY MEASURED
              attrs (line counts + AST signal counts). No decisions.
  * DECISION (graph-resident) — `install_requires_replacement_rule`
              installs a graph Rule (the same shape meta_monitor uses):
              `PythonUnit.requires_replacement = true` iff the AST signals
              say "agent logic" AND it is not a pure world adapter. The
              CLASSIFICATION is a Term the engine evaluates over the
              stored signals; it is NOT a Python if/else.
  * EMIT    — `RustRewriteWorld.convert_one` mints a `ReplacementTarget`
              (+ a `CodeTarget` registry entry so the cortex can read the
              existing source) wired as the cortex's current target, runs
              `cortex.tick()`, and reads back the draft / validation. The
              cortex writes any `.rs`; this adapter only triggers + reads.

Offline (no LLM self-teacher on the agent), the cortex's request_author
step no-ops — the loop reaches a `ReplacementTarget` minted + authoring
requested but NO draft. That is the loop WIRED END-TO-END, awaiting the
teacher, NOT a failure. The honest framing: this world ENABLES the
rewrite as incremental ACCRETION (one unit at a time), it does not
one-shot it.
"""
from __future__ import annotations

import ast
from pathlib import Path
from typing import Iterable

from substrate_rs import Attr, Var, Lit, Gt, And, Or, Eq, IfThenElse


_REPO_ROOT = Path(__file__).resolve().parent.parent

# Node + edge types this world introduces. The `_native.Substrate`
# requires a Production for every (src_type, edge, tgt_type) it will
# ever see; the helper below opens them. (The Python wrapper Substrate
# is permissive, but we open productions anyway so the adapter works on
# either backend — same as the cortex's own install.)
_RR_NODE_TYPES = ("RustRewriteRoot", "PythonUnit")
_RR_EDGE_TYPES = ("has_unit", "rewrites_to")

# AST signal attrs measured per unit (the CLAUDE.md self-correction
# signals, as mechanical counts). The graph Rule reads these.
_SIGNAL_ATTRS = (
    "n_rule_engine_calls",
    "n_substrate_conditionals",
    "n_agent_state_assigns",
    "calls_substrate_io",
    "imports_native",
)

# Names whose call indicates running the Python rule engine (the hard-NO
# in CLAUDE.md). Matched against the call's dotted tail.
_RULE_ENGINE_NAMES = frozenset({
    "run", "_match", "_apply", "make_rule", "graph_rewrite",
    "apply_rule_once", "run_rules", "add_rule",
})
# Substrate / graph references that, when they appear in an if-test,
# make that conditional a DECISION OVER GRAPH STATE (a Rule, per the
# rule) rather than an I/O-boundary classifier.
_SUBSTRATE_REFS = frozenset({
    "substrate", "graph", "node", "nodes", "edges", "attrs",
    "neighbours", "in_neighbours", "node_count", "nodes_where",
})
# Calls that are adapter-shaped: pure mechanical substrate mutation /
# tick. A unit that ONLY does these (zero decision signals) is a world
# adapter and is EXEMPT from rewrite.
_SUBSTRATE_IO_NAMES = frozenset({
    "add_node", "add_edge", "add_edge_unchecked", "set_attr",
    "tick", "add_production", "remove_node", "remove_edge",
})


# --------------------------------------------------------------------------- ingest


def _native(substrate):
    return substrate._inner if hasattr(substrate, "_inner") else substrate


def _open_productions(substrate) -> None:
    """Open the (src, edge, tgt) productions this world needs. Idempotent;
    failures (already-present / permissive backend) are swallowed."""
    pairs = [
        ("RustRewriteRoot", "has_unit", "PythonUnit"),
        ("PythonUnit", "rewrites_to", "ReplacementTarget"),
    ]
    for src_t, et, tgt_t in pairs:
        try:
            substrate.add_production({
                "src": {"type": src_t, "var": "src"},
                "edge_type": et,
                "tgt": {"type": tgt_t, "var": "tgt"},
                "where": None,
                "weight": {"type": "Lit", "value": 1.0},
                "provenance": f"rust_rewrite_world:{et}",
            })
        except Exception:
            pass


def _dotted_tail(node: ast.AST) -> str:
    """Rightmost name of a (possibly attribute-chained) call target.
    `gr.run` -> 'run'; `self.s.add_node` -> 'add_node'; `foo()` -> 'foo'."""
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.Name):
        return node.id
    return ""


def _refs_substrate(test: ast.AST) -> bool:
    """True if an if-test references substrate / graph state — i.e. the
    conditional is a DECISION over the graph, which CLAUDE.md says is a
    Rule, not Python."""
    for sub in ast.walk(test):
        if isinstance(sub, ast.Name) and sub.id in _SUBSTRATE_REFS:
            return True
        if isinstance(sub, ast.Attribute) and sub.attr in _SUBSTRATE_REFS:
            return True
        # `node(x)["attrs"]` — a Call to a substrate accessor.
        if isinstance(sub, ast.Call):
            if _dotted_tail(sub.func) in _SUBSTRATE_REFS:
                return True
    return False


class _UnitScanner(ast.NodeVisitor):
    """Mechanical AST signal counter over one scope (a module body OR a
    single function/method body). Counts the CLAUDE.md violation signals.
    No judgement — just arithmetic over the tree."""

    def __init__(self):
        self.n_rule_engine_calls = 0
        self.n_substrate_conditionals = 0
        self.n_agent_state_assigns = 0
        self.calls_substrate_io = 0
        self.imports_native = 0

    def visit_Call(self, node: ast.Call):
        tail = _dotted_tail(node.func)
        if tail in _RULE_ENGINE_NAMES:
            self.n_rule_engine_calls += 1
        if tail in _SUBSTRATE_IO_NAMES:
            self.calls_substrate_io += 1
        self.generic_visit(node)

    def visit_If(self, node: ast.If):
        if _refs_substrate(node.test):
            self.n_substrate_conditionals += 1
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign):
        # `self.<x> = ...` — Python agent state held on a class instance.
        for tgt in node.targets:
            if (isinstance(tgt, ast.Attribute)
                    and isinstance(tgt.value, ast.Name)
                    and tgt.value.id == "self"):
                self.n_agent_state_assigns += 1
        self.generic_visit(node)

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            if "substrate_rs" in alias.name or "_native" in alias.name:
                self.imports_native += 1
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        mod = node.module or ""
        if "substrate_rs" in mod or "_native" in mod:
            self.imports_native += 1
        self.generic_visit(node)


def _scan_scope(body: Iterable[ast.AST]) -> dict[str, int]:
    sc = _UnitScanner()
    for stmt in body:
        sc.visit(stmt)
    return {a: int(getattr(sc, a)) for a in _SIGNAL_ATTRS}


def _ensure_root(substrate) -> int:
    for n in substrate.nodes("RustRewriteRoot"):
        return n
    return substrate.add_node("RustRewriteRoot", {"origin": "rust_rewrite_world"})


def _find_unit(substrate, root: int, qualname: str) -> int | None:
    for u in substrate.neighbours(root, "has_unit"):
        if substrate.node(u)["attrs"].get("qualname") == qualname:
            return u
    return None


def _upsert_unit(substrate, root: int, attrs: dict) -> int:
    """Create or update the PythonUnit for attrs['qualname']. Idempotent —
    re-enumeration refreshes the measured attrs, never duplicates."""
    existing = _find_unit(substrate, root, attrs["qualname"])
    if existing is not None:
        for k, v in attrs.items():
            substrate.set_attr(existing, k, v)
        return existing
    u = substrate.add_node("PythonUnit", attrs)
    try:
        substrate.add_edge(root, "has_unit", u, {})
    except Exception:
        pass
    return u


def enumerate_python_surface(substrate, roots: tuple[str, ...] = ("domains",),
                             exclude: tuple[str, ...] = (
                                 "rust_rewrite_world.py",),
                             repo_root: Path | None = None) -> int:
    """MECHANICAL ingestion: walk every `*.py` under `roots`, parse with
    `ast`, and write one `PythonUnit` graph node per MODULE and per
    top-level function / method. Each node carries mechanically measured
    attrs (line_count + the AST signal counts in `_SIGNAL_ATTRS`).

    This is the impl-substrate SELF-MODEL the agent lacked: its Python
    surface as graph data. No decisions are made here — the
    requires_replacement marking is a graph Rule (see
    `install_requires_replacement_rule`). Idempotent.

    Returns the number of PythonUnit nodes present after the walk.
    """
    _open_productions(substrate)
    base = Path(repo_root) if repo_root else _REPO_ROOT
    root = _ensure_root(substrate)

    for root_name in roots:
        root_dir = base / root_name
        if not root_dir.is_dir():
            continue
        for path in sorted(root_dir.rglob("*.py")):
            if path.name in exclude:
                continue
            rel = path.relative_to(base)
            module = ".".join(rel.with_suffix("").parts)
            try:
                src = path.read_text()
                tree = ast.parse(src, filename=str(path))
            except (SyntaxError, OSError):
                continue
            path_parts = list(rel.parts)
            module_lines = src.count("\n") + 1

            # Module-level node: signals over the module's top-level body
            # (module imports, module-level ifs, etc.).
            module_signals = _scan_scope(tree.body)
            _upsert_unit(substrate, root, {
                "module": module,
                "qualname": module,
                "kind": "module",
                "path": str(rel),
                "path_parts": path_parts,
                "line_count": int(module_lines),
                "status": "scanned",
                "requires_replacement": False,
                "classify_pending": 1,
                "origin": "rust_rewrite_world",
                **module_signals,
            })

            # One node per top-level function and per method.
            for node in tree.body:
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    _emit_callable_unit(substrate, root, module, path_parts,
                                        node, owner=None)
                elif isinstance(node, ast.ClassDef):
                    for sub in node.body:
                        if isinstance(sub, (ast.FunctionDef,
                                            ast.AsyncFunctionDef)):
                            _emit_callable_unit(substrate, root, module,
                                                path_parts, sub,
                                                owner=node.name)

    return len(list(substrate.neighbours(root, "has_unit")))


def _emit_callable_unit(substrate, root: int, module: str,
                        path_parts: list[str], node: ast.AST,
                        owner: str | None) -> None:
    name = node.name
    qual = f"{module}.{owner}.{name}" if owner else f"{module}.{name}"
    end = getattr(node, "end_lineno", None) or node.lineno
    line_count = int(end - node.lineno + 1)
    signals = _scan_scope(node.body)
    _upsert_unit(substrate, root, {
        "module": module,
        "qualname": qual,
        "kind": "method" if owner else "function",
        "owner": owner or "",
        "path": "/".join(path_parts),
        "path_parts": path_parts,
        "line_count": line_count,
        "status": "scanned",
        "requires_replacement": False,
        "classify_pending": 1,
        "origin": "rust_rewrite_world",
        **signals,
    })


# --------------------------------------------------------------------------- decision (graph Rule)


def install_requires_replacement_rule(substrate) -> dict:
    """Install the agent's CLASSIFICATION as a graph Rule (the same shape
    `meta_monitor.install_meta_issue_rule` uses): for each PythonUnit, set
    `requires_replacement` from the MEASURED signals.

    The decision, as a Term the engine evaluates (NOT a Python if/else):

        agent_logic = (n_rule_engine_calls > 0)
                   OR (n_substrate_conditionals > 0)
                   OR (n_agent_state_assigns > 0)

        is_world_adapter = (calls_substrate_io > 0)
                       AND NOT agent_logic      # pure mechanical I/O

        requires_replacement = agent_logic AND NOT is_world_adapter

    A unit that only does substrate I/O with zero decision signals is a
    world adapter (exempt). A unit with rule-engine calls, graph-state
    conditionals, or agent-state assignment is agent logic the Rust
    runtime must own — flagged for the cortex.

    Returns {'root', 'rule_index'}.
    """
    nat = _native(substrate)
    root = _ensure_root(substrate)
    U = Var("U")

    n_rule = Attr(U, "n_rule_engine_calls")
    n_cond = Attr(U, "n_substrate_conditionals")
    n_state = Attr(U, "n_agent_state_assigns")
    n_io = Attr(U, "calls_substrate_io")
    zero = Lit(0)

    agent_logic = Or(items=(
        Gt(a=n_rule, b=zero),
        Gt(a=n_cond, b=zero),
        Gt(a=n_state, b=zero),
    ))
    # world adapter: does substrate I/O AND is NOT agent logic.
    # Express "NOT agent_logic" as all-three-zero (avoids relying on a
    # Not-of-Or shape).
    no_agent_logic = And(items=(
        Eq(a=n_rule, b=zero),
        Eq(a=n_cond, b=zero),
        Eq(a=n_state, b=zero),
    ))
    is_world_adapter = And(items=(Gt(a=n_io, b=zero), no_agent_logic))
    requires = And(items=(agent_logic,
                          IfThenElse(is_world_adapter, Lit(False), Lit(True))))

    # Gate on a `classify_pending` flag (set at enumeration, cleared by
    # this rule's effect). The engine's `apply_rule_once` fires ONE match
    # per call; the flag lets `classify_surface` walk every still-pending
    # unit exactly once — the same pending-flag pattern meta_monitor uses
    # to drive its judgement rule over every watched Process.
    rule = {
        "name": "mark_requires_replacement",
        "match": [["R", "has_unit", "U"]],
        "where": And(items=(
            Eq(a=Attr(U, "origin"), b=Lit("rust_rewrite_world")),
            Eq(a=Attr(U, "classify_pending"), b=Lit(1)),
        )).to_dict(),
        "effects": [
            ["set_attr", "U", "requires_replacement",
             {"__term__": requires.to_dict()}],
            # Mark world adapters explicitly so the surface map can count
            # them without re-deriving the decision in Python.
            ["set_attr", "U", "world_adapter",
             {"__term__": is_world_adapter.to_dict()}],
            ["set_attr", "U", "classify_pending",
             {"__term__": Lit(0).to_dict()}],
        ],
    }
    return {"root": root, "rule_index": nat.add_rule(rule)}


def classify_surface(substrate, rule_index: int,
                     max_iters: int | None = None) -> int:
    """Fire the graph classification Rule over every still-pending
    PythonUnit. The engine evaluates the requires_replacement Term and
    writes the verdict onto each node; this loop just keeps invoking
    `apply_rule_once` (one match per call) until no unit has
    `classify_pending == 1`. Mechanical driver — the DECISION is the Rule.

    Returns the number of rule applications. `max_iters` defaults to one
    application per PythonUnit (plus slack)."""
    nat = _native(substrate)
    root = _ensure_root(substrate)
    units = list(substrate.neighbours(root, "has_unit"))
    cap = max_iters if max_iters is not None else len(units) + 8

    def _pending() -> bool:
        for u in units:
            if substrate.node(u)["attrs"].get("classify_pending") == 1:
                return True
        return False

    applied = 0
    while applied < cap and _pending():
        nat.apply_rule_once(rule_index)
        applied += 1
    return applied


# --------------------------------------------------------------------------- world


class RustRewriteWorld:
    """World adapter over the agent's Python surface + the code-authoring
    cortex. Holds NO agent state and makes NO decisions — it reads the
    graph (the self-model + the graph Rule's verdicts) and drives the
    existing cortex. Ranking is a pure graph query (documented as such);
    the rewrite decision lives in the installed Rule."""

    def __init__(self, substrate, cortex=None):
        self.s = substrate
        self.cortex = cortex
        self.root = _ensure_root(substrate)

    # -------------------------------------------------------------- self-model

    def _units(self) -> list[int]:
        return list(self.s.neighbours(self.root, "has_unit"))

    def surface_map(self) -> dict:
        """Totals + per-module breakdown of the self-model. Pure query."""
        units = self._units()
        total = len(units)
        requires = world = converted = 0
        per_module: dict[str, dict] = {}
        for u in units:
            a = self.s.node(u)["attrs"]
            mod = a.get("module", "?")
            pm = per_module.setdefault(
                mod, {"units": 0, "requires_replacement": 0,
                      "world_adapter": 0, "converted": 0})
            pm["units"] += 1
            if a.get("requires_replacement"):
                requires += 1
                pm["requires_replacement"] += 1
            if a.get("world_adapter"):
                world += 1
                pm["world_adapter"] += 1
            if a.get("status") == "converted":
                converted += 1
                pm["converted"] += 1
        remaining = requires - converted
        pct = (100.0 * remaining / requires) if requires else 0.0
        return {
            "python_units": total,
            "requires_replacement": requires,
            "world_adapter_exempt": world,
            "converted": converted,
            "pct_remaining": round(pct, 1),
            "per_module": per_module,
        }

    def _signal_density(self, attrs: dict) -> int:
        return (int(attrs.get("n_rule_engine_calls", 0))
                + int(attrs.get("n_substrate_conditionals", 0))
                + int(attrs.get("n_agent_state_assigns", 0)))

    def top_units(self, n: int = 10) -> list[dict]:
        """The n highest-priority requires_replacement units (rank =
        signal_density × line_count). Pure query — used for the
        self-model printout."""
        scored = []
        for u in self._units():
            a = self.s.node(u)["attrs"]
            if not a.get("requires_replacement"):
                continue
            dens = self._signal_density(a)
            score = dens * int(a.get("line_count", 0))
            scored.append((score, dens, u, a))
        scored.sort(key=lambda t: (-t[0], -t[1],
                                   str(self.s.node(t[2])["attrs"].get("qualname"))))
        out = []
        for score, dens, u, a in scored[:n]:
            out.append({
                "qualname": a.get("qualname"),
                "kind": a.get("kind"),
                "line_count": int(a.get("line_count", 0)),
                "score": score,
                "signals": {
                    "rule_engine": int(a.get("n_rule_engine_calls", 0)),
                    "substrate_cond": int(a.get("n_substrate_conditionals", 0)),
                    "agent_state": int(a.get("n_agent_state_assigns", 0)),
                    "substrate_io": int(a.get("calls_substrate_io", 0)),
                },
            })
        return out

    def next_target(self) -> int | None:
        """Highest-priority requires_replacement unit not yet converted.
        Pure graph query (no decision — the requires_replacement marking
        was the decision, made by the Rule). Ranked by
        signal_density × line_count."""
        best = None
        best_key = None
        for u in self._units():
            a = self.s.node(u)["attrs"]
            if not a.get("requires_replacement"):
                continue
            if a.get("status") == "converted":
                continue
            if self.s.neighbours(u, "rewrites_to"):
                continue
            key = (self._signal_density(a) * int(a.get("line_count", 0)),
                   self._signal_density(a))
            if best_key is None or key > best_key:
                best_key, best = key, u
        return best

    # -------------------------------------------------------------- emit (into cortex)

    def _register_code_target(self, attrs: dict) -> None:
        """Mint a CodeTarget registry entry for this unit so the cortex's
        `compose_authoring_question` can read the existing source. Mechanical
        translation of the PythonUnit's measured path into the cortex's
        registry shape. Idempotent by op_name."""
        op = attrs["qualname"]
        for n in self.s.nodes("CodeTarget"):
            if self.s.node(n)["attrs"].get("op_name") == op:
                return
        # The cortex reads existing source from path_parts. For a
        # function/method unit, point at the whole module file (the cortex
        # shows the source to the teacher; the granularity it rewrites is
        # the teacher's to scope from the qualname).
        self.s.add_node("CodeTarget", {
            "op_name": op,
            "path_parts": list(attrs.get("path_parts", [])),
            "requirements": ["ffi_native_substrate", "hot_loops_no_gc"],
            "design_tags": ["agent_logic_rewrite", "graph_resident_decision"],
            "bench": None,
            "origin": "rust_rewrite_world",
            "notes": (f"Agent-logic Python flagged for Rust rewrite: "
                      f"{op}. No benchmark surface — compile-check only "
                      f"offline; cortex declines install without proof."),
        })

    def convert_one(self, cortex) -> dict:
        """Mint a ReplacementTarget for the next unit, wire it as the
        cortex's current_target, tick the cortex, read back draft +
        validation, set the unit's status. EMIT is mechanical — the cortex
        writes any `.rs`."""
        u = self.next_target()
        if u is None:
            return {"status": "surface_exhausted"}
        a = self.s.node(u)["attrs"]
        qual = a.get("qualname")

        # The cortex picks targets from op_stats by default. We mint the
        # target directly (the unit IS the target) + register its source so
        # the cortex's authoring step can compose a real spec.
        self._register_code_target(a)
        baseline = {"total_ms": 0.0, "count": 0}
        tgt = cortex.set_target(qual, baseline=baseline)
        try:
            self.s.add_edge(u, "rewrites_to", tgt, {})
        except Exception:
            pass

        trail = cortex.tick()
        draft = cortex.current_draft()
        validation = None
        status = "awaiting_teacher"
        if draft is not None:
            status = "drafted"
            val = cortex.draft_validation(draft)
            if val is not None:
                validation = val
                if val.get("compile_ok") and val.get("tests_pass") \
                        and val.get("perf_improvement_factor", 0.0) > 1.0:
                    status = "converted"
                else:
                    status = "failed"
        self.s.set_attr(u, "status", status)

        return {
            "qualname": qual,
            "line_count": int(a.get("line_count", 0)),
            "target_nid": str(tgt),
            "tick_trail": trail,
            "draft": draft is not None,
            "validation": validation,
            "status": status,
        }

    def run(self, cortex, limit: int | None = None) -> list[dict]:
        """Traverse the surface, convert_one until limit / exhausted.
        Returns the per-unit log."""
        log: list[dict] = []
        count = 0
        while limit is None or count < limit:
            result = self.convert_one(cortex)
            if result.get("status") == "surface_exhausted":
                break
            log.append(result)
            count += 1
        return log


def next_replacement_target(substrate, attempted=()):
    """Cortex-facing target selector — points the code-authoring cortex at the
    agent's impl-substrate SELF-MODEL instead of the legacy wall-clock op_stats.

    Returns ``(qualname, baseline)`` for the cortex's ``set_target`` (or None):
    the highest-priority Python unit the graph-resident requires_replacement
    Rule flagged as agent-logic-that-should-be-Rust — the CATEGORICAL
    'is-it-Python-in-the-agent' criterion, ranked by signal_density × line_count
    — skipping units already converted / minted / attempted. Registers a
    CodeTarget so the cortex can read the source. Pure graph query over the
    Rule's verdicts + mechanical CodeTarget I/O — the rewrite DECISION was the
    Rule's; this only reads it. None when the surface isn't enumerated, so the
    cortex falls back to op_stats."""
    if not substrate.nodes("PythonUnit"):
        return None
    world = RustRewriteWorld(substrate)
    attempted = set(attempted or ())
    best = best_key = best_attrs = None
    for u in world._units():
        a = substrate.node(u)["attrs"]
        if not a.get("requires_replacement"):
            continue
        if a.get("status") == "converted":
            continue
        if substrate.neighbours(u, "rewrites_to"):
            continue
        if a.get("qualname") in attempted:
            continue
        dens = world._signal_density(a)
        key = (dens * int(a.get("line_count", 0)), dens,
               str(a.get("qualname")))
        if best_key is None or key > best_key:
            best_key, best, best_attrs = key, u, a
    if best is None:
        return None
    world._register_code_target(best_attrs)
    baseline = {
        "total_ms": float(best_key[0]),   # priority = signal_density × lines
        "count": 1,
        "source": "requires_replacement_self_model",
        "qualname": best_attrs.get("qualname"),
    }
    return best_attrs.get("qualname"), baseline


__all__ = [
    "enumerate_python_surface",
    "install_requires_replacement_rule",
    "classify_surface",
    "RustRewriteWorld",
    "next_replacement_target",
]

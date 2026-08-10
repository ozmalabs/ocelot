"""The typed TOOL-USE boundary — the agent KNOWINGLY uses external
processes and libraries as typed, graph-composable operations.

The idea (the user's): don't rewrite arbitrary Python into Rust. Instead
the agent uses a ``use_tool`` boundary that can run external processes and
library calls, KNOWS they are external, and knows the TYPES that cross the
boundary (and what those types are on the Rust side, via
``domains.type_system``). A tool's output is WRAPPED into ingestable graph
data; when that's not possible, into plain text. Because the agent
understands types, it can WORK OUT which tool to call (``select_tool``)
and check that the call is safe (``typecheck`` at the boundary).

Faithful split (``CLAUDE.md``):

  * The TYPE model, the TOOL REGISTRY, and the tool-selection DECISION are
    GRAPH DATA / graph-resident reasoning — ``ToolSpec`` nodes the agent
    queries over typed signatures.
  * The DISPATCH (actually running a subprocess or calling a library
    function) is external I/O = a world-adapter act. Allowed, mechanical,
    Python. The handler registry below is exactly that boundary: it runs
    the instrument and translates its output back into graph mutations.

A ``ToolSpec`` node::

    ToolSpec {
        name, input_types:[type_name], output_type,
        external:true, kind: "process"|"library"|"text",
        wrap: "graph"|"text", handler_key, doc
    }

``use_tool`` resolves the spec, TYPECHECKS the args against ``input_types``
(rejecting on mismatch — the type model is what makes the boundary safe),
dispatches to the handler, WRAPS the output (structured -> a typed
``ToolResult`` graph node; unstructurable -> text on the node), records a
graph-visible ``ToolCall`` node, and returns the typed result with an
explicit ``external`` flag and the Rust-side type.

NOTHING here is an agent decision encoded in Python. ``select_tool`` is a
graph query over typed signatures; ``use_tool`` is a mechanical
typecheck -> run -> wrap -> record pipeline. The agent's reasoning lives in
the graph it queries, not in branching Python.
"""
from __future__ import annotations

import shlex
import subprocess
from typing import Any, Callable

from domains.type_system import (
    install_type_system,
    rust_type_for,
    type_of_value,
    typecheck,
)


TOOLSPEC_NODE_TYPE = "ToolSpec"
TOOLCALL_NODE_TYPE = "ToolCall"
TOOLRESULT_NODE_TYPE = "ToolResult"

# subprocess guards — a tool is an instrument, not an open shell.
_PROC_TIMEOUT = 30.0
_PROC_MAX_OUTPUT = 16_384


# ---------------------------------------------------------------------------
# handler registry — the world-adapter boundary that actually runs a tool
# ---------------------------------------------------------------------------
# A handler_key -> Python callable. The callable IS the external act: it
# runs a subprocess, calls a library function, or returns text. It takes
# the typed positional args and returns a raw Python value (which use_tool
# then wraps). Process handlers are built from a small factory so the argv
# construction (typed args -> a real command line) is uniform.

_HANDLERS: dict[str, Callable[..., Any]] = {}


def register_handler(handler_key: str, fn: Callable[..., Any]) -> None:
    """Register a Python callable as the runner for ``handler_key``.

    This is the world-adapter half — it actually runs the instrument.
    Idempotent; a re-register replaces the callable.
    """
    _HANDLERS[handler_key] = fn


def process_handler(argv_template: list[str],
                    parse: Callable[[str], Any] | None = None
                    ) -> Callable[..., Any]:
    """Build a "process" handler: substitute typed args into an argv
    template, run the real subprocess, capture stdout, and parse it.

    ``argv_template`` uses ``{0}``, ``{1}``, … placeholders for the
    positional args. ``parse`` (optional) turns stdout text into a typed
    value; when omitted, the raw stripped stdout text is returned (the
    text-wrap path). The built handler exposes the resolved ``argv`` on the
    returned value's side channel via the ``_last_argv`` attribute so the
    demo can prove a real shell-out happened.
    """
    def run(*args: Any) -> Any:
        argv = [tok.format(*[str(a) for a in args]) for tok in argv_template]
        proc = subprocess.run(
            argv, capture_output=True, text=True,
            timeout=_PROC_TIMEOUT)
        out = proc.stdout[:_PROC_MAX_OUTPUT]
        run._last_argv = argv  # type: ignore[attr-defined]
        run._last_stderr = proc.stderr  # type: ignore[attr-defined]
        run._last_returncode = proc.returncode  # type: ignore[attr-defined]
        text = out.strip()
        if parse is not None:
            return parse(text)
        return text
    run._last_argv = None  # type: ignore[attr-defined]
    return run


def library_handler(fn: Callable[..., Any]) -> Callable[..., Any]:
    """Wrap a Python library function as a "library" handler.

    The agent treats the wrapped function as an EXTERNAL typed tool — NOT a
    native graph primitive. The wrapper just calls through; the externality
    is carried by the ToolSpec/ToolCall/ToolResult nodes, not the function.
    """
    def run(*args: Any) -> Any:
        return fn(*args)
    return run


# ---------------------------------------------------------------------------
# the typed tool registry — ToolSpec graph nodes
# ---------------------------------------------------------------------------

def install_tool_use(substrate) -> dict[str, Any]:
    """Install the type model + the ToolSpec/ToolCall/ToolResult grammar.

    Returns the Type-node id map from ``install_type_system``. Idempotent.
    """
    type_ids = install_type_system(substrate)
    # Index the registry by name + by output_type so select_tool / resolve
    # are O(1) graph queries rather than scans.
    for attr in ("name", "output_type"):
        try:
            substrate.declare_attr_index(TOOLSPEC_NODE_TYPE, attr)
        except Exception:
            pass
    # Productions so the call-trail edges are Γ-admissible domain claims.
    for src_t, et, tgt_t, prov in [
        (TOOLCALL_NODE_TYPE, "called", TOOLSPEC_NODE_TYPE, "tool_use:call_tool"),
        (TOOLCALL_NODE_TYPE, "produced", TOOLRESULT_NODE_TYPE,
         "tool_use:call_result"),
    ]:
        try:
            substrate.add_production({
                "src": {"type": src_t, "var": "src"},
                "edge_type": et,
                "tgt": {"type": tgt_t, "var": "tgt"},
                "provenance": prov,
            })
        except Exception:
            pass
    return type_ids


def register_tool(substrate, name: str, input_types: list[str],
                  output_type: str, kind: str, handler_key: str,
                  wrap: str = "graph", doc: str = "") -> Any:
    """Register a typed tool as a ``ToolSpec`` graph node.

    ``kind`` is "process" | "library" | "text"; ``wrap`` is "graph" | "text"
    (how ``use_tool`` packages the output). ``handler_key`` names the
    Python runner in the handler registry. ``external`` is always true — a
    tool is, by definition, outside the graph.

    Idempotent on ``name``: a re-register updates the existing node's attrs.
    Returns the ToolSpec node id.
    """
    existing = _find_tool(substrate, name)
    attrs = {
        "name": name,
        "input_types": list(input_types),
        "output_type": output_type,
        "external": True,
        "kind": kind,
        "wrap": wrap,
        "handler_key": handler_key,
        "doc": doc,
    }
    if existing is not None:
        for k, v in attrs.items():
            try:
                substrate.set_attr(existing, k, v)
            except Exception:
                pass
        return existing
    return substrate.add_node(TOOLSPEC_NODE_TYPE, attrs)


def _find_tool(substrate, name: str):
    try:
        hits = substrate.nodes_where(TOOLSPEC_NODE_TYPE, "name", name)
        if hits:
            return hits[0]
    except Exception:
        pass
    try:
        for nid in substrate.nodes(TOOLSPEC_NODE_TYPE):
            if substrate.node(nid)["attrs"].get("name") == name:
                return nid
    except Exception:
        pass
    return None


# ---------------------------------------------------------------------------
# select_tool — the agent's graph-resident choice of which tool to use
# ---------------------------------------------------------------------------

def select_tool(substrate, need: dict) -> str | None:
    """The agent WORKS OUT which tool to call.

    ``need`` is a typed description: ``{output_type, op?, input_types?}``.
    This is a graph query over the registry's typed ToolSpec signatures:

      1. the output_type must match the need's output_type (the type model
         is the primary filter — the boundary is typed);
      2. among those, prefer a name/op-hint match (``op`` substring in the
         tool name) — the operation the agent wants;
      3. when input_types are given, require they typecheck-compatibly
         match arity + types.

    Returns the chosen tool name, or None when nothing in the registry
    satisfies the typed need. No ranking heuristics beyond the typed match
    + the op hint — the SELECTOR is the type signature, exactly as the
    architecture intends.
    """
    want_out = need.get("output_type")
    op = (need.get("op") or "").lower()
    want_in = need.get("input_types")

    candidates: list[tuple[int, str]] = []
    specs = _all_specs(substrate)
    for spec in specs:
        a = spec["attrs"]
        if want_out is not None and a.get("output_type") != want_out:
            continue
        if want_in is not None:
            sig = list(a.get("input_types", []))
            if len(sig) != len(want_in):
                continue
            if any(w != s for w, s in zip(want_in, sig)):
                continue
        name = a.get("name", "")
        # op hint: an exact-name or substring match scores higher.
        score = 0
        if op:
            if op == name.lower():
                score = 2
            elif op in name.lower():
                score = 1
            else:
                # op given but no match — only keep if nothing else; rank low
                score = -1
        candidates.append((score, name))

    if not candidates:
        return None
    # Highest score wins; ties broken by registry order (stable).
    candidates.sort(key=lambda t: -t[0])
    best_score, best_name = candidates[0]
    # If an op hint was given and produced no positive match at all, the
    # agent declines rather than guessing a wrong-operation tool.
    if op and best_score < 0:
        return None
    return best_name


def _all_specs(substrate) -> list[dict]:
    out = []
    for nid in substrate.nodes(TOOLSPEC_NODE_TYPE):
        node = substrate.node(nid)
        out.append({"id": nid, "attrs": dict(node["attrs"])})
    return out


# ---------------------------------------------------------------------------
# use_tool — typecheck -> dispatch -> wrap -> record
# ---------------------------------------------------------------------------

def use_tool(substrate, tool_name: str, args: list) -> dict:
    """Run an external tool as a TYPED, graph-visible boundary operation.

    Steps:
      1. resolve the ToolSpec; TYPECHECK each arg against ``input_types``
         (reject on mismatch — the type model makes the boundary safe);
      2. dispatch to the handler (run the process / call the library);
      3. WRAP the output: structured -> a typed ``ToolResult`` graph node;
         unstructurable -> text on the node;
      4. record a ``ToolCall`` node (tool, args, result, external=true) and
         return the typed result.

    The returned dict is::

        {ok, value, value_type, rust_type, external:true, wrap,
         node, call_node, [error]}

    ``value_type`` -> ``rust_type`` via the type model, so the result is
    EXPLICITLY external and TYPED with its Rust-side form.
    """
    spec_id = _find_tool(substrate, tool_name)
    if spec_id is None:
        return _fail(substrate, tool_name, args,
                     f"no such tool: {tool_name}")
    spec = dict(substrate.node(spec_id)["attrs"])
    input_types = list(spec.get("input_types", []))
    output_type = spec.get("output_type", "Str")
    kind = spec.get("kind", "library")
    wrap = spec.get("wrap", "graph")
    handler_key = spec.get("handler_key")

    # 1. typecheck the boundary — arity + each arg's type.
    if len(args) != len(input_types):
        return _fail(substrate, tool_name, args,
                     f"arity mismatch: expected {len(input_types)} "
                     f"arg(s) {input_types}, got {len(args)}")
    for i, (a, expected) in enumerate(zip(args, input_types)):
        if not typecheck(a, expected):
            got = type_of_value(a)
            return _fail(
                substrate, tool_name, args,
                f"type error at arg {i}: expected {expected} "
                f"({rust_type_for(expected)}), got {got} (value={a!r})")

    # 2. dispatch — the external act (subprocess / library call / text).
    handler = _HANDLERS.get(handler_key)
    if handler is None:
        return _fail(substrate, tool_name, args,
                     f"no handler registered for key: {handler_key}")
    try:
        raw = handler(*args)
    except Exception as e:  # an instrument can fail; surface it typed.
        return _fail(substrate, tool_name, args,
                     f"tool raised: {type(e).__name__}: {e}")

    # 3. wrap the output -> typed graph data, else text.
    if wrap == "text":
        value = raw if isinstance(raw, str) else str(raw)
        value_type = "Str"
    else:
        value = raw
        value_type = output_type
        # Honesty guard: if the handler couldn't produce the declared
        # structured type, fall back to text rather than mis-type it.
        if not typecheck(value, value_type):
            value = str(raw)
            value_type = "Str"
            wrap = "text"

    result_id = substrate.add_node(TOOLRESULT_NODE_TYPE, {
        "value": value,
        "value_type": value_type,
        "rust_type": rust_type_for(value_type),
        "tool": tool_name,
        "external": True,
        "wrap": wrap,
    })

    # 4. record the call as a graph-visible node + trail edges.
    call_id = _record_call(substrate, tool_name, args, value,
                           spec_id, result_id)

    return {
        "ok": True,
        "value": value,
        "value_type": value_type,
        "rust_type": rust_type_for(value_type),
        "external": True,
        "wrap": wrap,
        "node": result_id,
        "call_node": call_id,
    }


def _record_call(substrate, tool_name, args, value, spec_id, result_id):
    """Mint a ToolCall node and wire called/produced trail edges so the
    call is graph-visible. Edges are best-effort (unchecked fallback)."""
    call_id = substrate.add_node(TOOLCALL_NODE_TYPE, {
        "tool": tool_name,
        "args": list(args),
        "result": value,
        "external": True,
    })
    for et, tgt in (("called", spec_id), ("produced", result_id)):
        try:
            substrate.add_edge(call_id, et, tgt)
        except Exception:
            try:
                substrate.add_edge_unchecked(call_id, et, tgt)
            except Exception:
                pass
    return call_id


def _fail(substrate, tool_name, args, msg: str) -> dict:
    """Record a failed (rejected/errored) call too — the boundary is
    graph-visible even when it refuses — and return a typed failure."""
    try:
        call_id = substrate.add_node(TOOLCALL_NODE_TYPE, {
            "tool": tool_name,
            "args": list(args),
            "error": msg,
            "external": True,
            "ok": False,
        })
    except Exception:
        call_id = None
    return {
        "ok": False,
        "value": None,
        "value_type": "Unit",
        "rust_type": "()",
        "external": True,
        "error": msg,
        "node": None,
        "call_node": call_id,
    }


# ---------------------------------------------------------------------------
# REAL tools — the math tower as external typed tools, a real process tool,
# and a text-fallback tool. This is the payoff: the Python the conversation
# depends on (gcd/is_prime/factorial) becomes a typed external boundary the
# agent KNOWS is external — not Python-in-the-agent awaiting an AST rewrite.
# ---------------------------------------------------------------------------

def _is_prime(n) -> bool:
    """is_prime by trial division — the real number-theory function the
    reasoning loop uses (domains.reason._isprime), exposed as a tool."""
    from domains.reason import _isprime
    return _isprime(int(n))


def register_real_tools(substrate) -> dict:
    """Register the math tower (library tools), a process tool, and a text
    tool. Wires the handlers AND the ToolSpec graph nodes. Idempotent.

    Returns ``{tool_name: toolspec_node_id}``.
    """
    import math

    # (a) the math tower as LIBRARY tools — real functions, typed boundary.
    register_handler("lib_gcd", library_handler(lambda a, b: math.gcd(int(a), int(b))))
    register_handler("lib_is_prime", library_handler(_is_prime))
    register_handler("lib_factorial", library_handler(lambda n: math.factorial(int(n))))

    # (b) a real PROCESS tool — uppercase a string via a python3 subprocess.
    #     Proves external-process execution: argv is built from typed args,
    #     stdout is captured + parsed back to a typed Str.
    register_handler("proc_upper", process_handler(
        ["python3", "-c", "import sys; print(sys.argv[1].upper())", "{0}"],
        parse=lambda text: text))

    # (c) a TEXT tool — the host's `uname -a` line: real but unstructurable,
    #     so it's wrapped as plain text.
    register_handler("proc_uname", process_handler(
        ["uname", "-a"], parse=None))

    ids: dict[str, Any] = {}
    ids["gcd"] = register_tool(
        substrate, "gcd", ["Int", "Int"], "Int",
        kind="library", handler_key="lib_gcd", wrap="graph",
        doc="greatest common divisor of two integers (math.gcd)")
    ids["is_prime"] = register_tool(
        substrate, "is_prime", ["Int"], "Bool",
        kind="library", handler_key="lib_is_prime", wrap="graph",
        doc="primality test by trial division (reason._isprime)")
    ids["factorial"] = register_tool(
        substrate, "factorial", ["Int"], "Int",
        kind="library", handler_key="lib_factorial", wrap="graph",
        doc="n! (math.factorial)")
    ids["upper"] = register_tool(
        substrate, "upper", ["Str"], "Str",
        kind="process", handler_key="proc_upper", wrap="graph",
        doc="uppercase a string via a python3 subprocess")
    ids["uname"] = register_tool(
        substrate, "uname", [], "Str",
        kind="text", handler_key="proc_uname", wrap="text",
        doc="host uname line — unstructurable, returned as text")
    return ids


# ---------------------------------------------------------------------------
# NATIVE UseTool — the tool boundary as a first-class engine Term
# ---------------------------------------------------------------------------
# `TermNode::UseTool { tool, args }` (Rust) lets a tool call COMPOSE inside an
# engine-evaluated Term-tree: `s.evaluate({"type":"Plus","items":[
#   {"type":"UseTool","tool":"gcd","args":[Lit 48, Lit 36]}, Lit 1]})` == 13.
# The Rust evaluator evaluates each arg Term to a Value, then dispatches to a
# Python handler registered by tool NAME in the native registry. We register
# the SAME handlers `use_tool` uses (resolved from each ToolSpec's
# handler_key) so the native path and the world-adapter path share one set of
# instruments. This is still the world-adapter boundary in spirit — the
# DISPATCH (running the instrument) is the only Python; the COMPOSITION now
# lives in the engine, not in branching Python.


def use_tool_term(tool: str, arg_terms: list):
    """Build the ``UseTool`` Term — a tool call that COMPOSES inside an
    engine-evaluated Term-tree. Returns a ``substrate_rs.Term`` so it nests
    directly inside ``Plus`` / ``IfThenElse`` / etc. and evaluates via
    ``s.evaluate(...)``.

    ``arg_terms`` are sub-Terms (``substrate_rs.Term`` objects, e.g.
    ``Lit(48)`` or any composed Term) — NOT raw values — because UseTool
    composes inside the engine: each arg is evaluated by the engine before
    the handler is called. The raw wire dict is ``term.to_dict()``:
    ``{"type":"UseTool", "tool":..., "args":[...]}``.
    """
    from substrate_rs import Term
    return Term("UseTool", tool=tool, args=list(arg_terms))


def register_native_handlers(substrate, _native=None) -> int:
    """Register each ToolSpec's handler in the Rust UseTool registry, keyed by
    TOOL NAME, so the native ``UseTool`` dispatches to the same callables
    ``use_tool`` uses. Returns the number of handlers registered.

    The native registry is keyed by tool name; ``_HANDLERS`` is keyed by
    ``handler_key`` — this bridges the two. Idempotent (re-registers replace).
    Skips specs whose handler_key has no registered Python handler.
    """
    if _native is None:
        import substrate_rs._native as _native  # the rebuilt extension
    register = _native.register_tool_handler
    n = 0
    for spec in _all_specs(substrate):
        attrs = spec["attrs"]
        name = attrs.get("name")
        handler_key = attrs.get("handler_key")
        fn = _HANDLERS.get(handler_key)
        if name is None or fn is None:
            continue
        register(name, fn)
        n += 1
    return n


__all__ = [
    "TOOLSPEC_NODE_TYPE",
    "TOOLCALL_NODE_TYPE",
    "TOOLRESULT_NODE_TYPE",
    "install_tool_use",
    "register_tool",
    "register_handler",
    "register_real_tools",
    "register_native_handlers",
    "use_tool_term",
    "process_handler",
    "library_handler",
    "select_tool",
    "use_tool",
]

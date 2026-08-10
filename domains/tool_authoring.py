"""The agent AUTHORS ITS OWN TOOL BOUNDARIES — it specifies a new external
tool from its TYPE MODEL, a mechanical registrar wires the handler, and the
tool is instantly usable in native ``UseTool`` Term-trees. NO Rust emission,
NO rebuild.

The key realization: the native ``TermNode::UseTool { tool, args }`` (built +
live, see ``runners/dsl/src/tools.rs``) dispatches GENERICALLY by tool NAME to
a process-global handler registry. So a new tool is *data* — a typed
``ToolSpec`` graph node plus a mechanically-built handler closure — NOT a new
DSL primitive. Authoring a tool therefore needs no emitted Rust and no
recompile: the agent specifies, a mechanical registrar wires the handler into
both dispatch paths, and the tool composes inside any Term-tree immediately,
in the SAME running process.

Faithful split (``CLAUDE.md``):

  * The SPECIFICATION (which types cross the boundary, the ToolSpec node, the
    handler DESCRIPTOR) and TOOL-SELECTION are GRAPH DATA / graph-resident
    reasoning — exactly like ``domains.tool_use``.
  * BUILDING the handler closure and RUNNING it (subprocess / library call) is
    world-adapter I/O — mechanical, no decisions. ``realize_tool`` is that
    boundary: it reads the agent's spec and wires the instrument.

This is LIGHTER than an emitter/rebuild path. Because ``UseTool`` dispatches
generically, the agent's own tool boundaries are graph data + a mechanical
handler, not emitted Rust. That is the architectural payoff of the generic
``UseTool``: tools are DATA.

Security boundary (honest): a "process" tool runs an external command the
agent specified. For a research substrate this is the intended capability. The
``argv`` is a FIXED TEMPLATE plus typed args (each substituted as ``str(arg)``
into a positional slot) — it is NOT free-form shell (no shell interpretation,
``subprocess.run`` with a list argv), which bounds it. The agent specifies
only in terms of TYPES it understands (validated against the type model) and
knows every result is external + typed.
"""
from __future__ import annotations

import importlib
import json
import subprocess
from typing import Any

from domains import tool_use
from domains.type_system import (
    BASE_TYPES,
    rust_type_for,
    type_of_value,
    typecheck,
)


# A marker node so agent-authored tools are graph-visible as a distinct class
# from the hand-registered ``register_real_tools`` set. One ToolAuthored node
# per authored tool, linked to its ToolSpec by an ``authored`` edge.
TOOLAUTHORED_NODE_TYPE = "ToolAuthored"

# subprocess guards — an authored process tool is an instrument, not a shell.
_PROC_TIMEOUT = 30.0
_PROC_MAX_OUTPUT = 16_384


# ---------------------------------------------------------------------------
# 1. agent_specify_tool — the agent's specification act (GRAPH DATA only)
# ---------------------------------------------------------------------------

def agent_specify_tool(substrate, *, name: str, input_types: list[str],
                       output_type: str, kind: str, handler: dict,
                       wrap: str = "graph", doc: str = "") -> dict:
    """The agent AUTHORS a tool boundary from its TYPE MODEL — graph data only.

    The agent specifies in terms of TYPES it understands: every ``input_type``
    and the ``output_type`` must already exist in the graph type model
    (``Type`` nodes). An unknown type is rejected — the agent cannot author a
    boundary over a type it has no model of. A duplicate tool name is rejected
    too (use a fresh name; idempotency belongs to ``register_tool``'s update
    path, not to authoring a *new* boundary).

    ``kind`` is "process" | "library". ``handler`` is a DESCRIPTOR (data, not
    code):

      * process: ``{"argv": ["cmd", "{0}", "{1}", ...], "stdin"?: "{i}"}`` — a
        template where ``{i}`` is filled by the i-th typed arg (stringified).
        Optionally ``"stdin": "{i}"`` feeds an arg on stdin instead of argv.
        stdout is the result, parsed per output_type / wrap.
      * library: ``{"module": "math", "func": "isqrt"}`` — a dotted import
        target. The function is imported + called with the typed args.

    Creates a ``ToolSpec`` graph node via :func:`tool_use.register_tool`
    (external:true, typed), stores the handler DESCRIPTOR on the spec as a
    ``handler_descriptor`` JSON attr, and mints a ``ToolAuthored`` marker node
    linked by an ``authored`` edge so authored tools are graph-visible.

    Returns the spec info dict. This is the agent authoring a tool boundary;
    NOTHING runs yet — :func:`realize_tool` wires the instrument.
    """
    # --- validate against the TYPE MODEL the agent understands ---
    if kind not in ("process", "library"):
        return {"ok": False, "error": f"unknown kind: {kind!r} "
                "(expected 'process' or 'library')"}
    unknown = [t for t in (list(input_types) + [output_type])
               if not _type_known(substrate, t)]
    if unknown:
        return {"ok": False,
                "error": f"unknown type(s) in spec: {unknown} — the agent "
                         "specifies in terms of types it understands "
                         f"(known base types: {sorted(BASE_TYPES)})"}
    if tool_use._find_tool(substrate, name) is not None:
        return {"ok": False,
                "error": f"tool already exists: {name!r} (authoring a NEW "
                         "boundary requires a fresh name)"}

    # --- validate the handler DESCRIPTOR shape (data, not code) ---
    ok, why = _validate_descriptor(kind, handler, len(input_types))
    if not ok:
        return {"ok": False, "error": why}

    # The handler_key the spec carries is derived mechanically from the name;
    # realize_tool registers the actual closure under it.
    handler_key = f"authored::{name}"

    spec_id = tool_use.register_tool(
        substrate, name, list(input_types), output_type,
        kind=kind, handler_key=handler_key, wrap=wrap, doc=doc)

    # Store the handler DESCRIPTOR (json) on the spec — the registrar reads it.
    try:
        substrate.set_attr(spec_id, "handler_descriptor", json.dumps(handler))
        substrate.set_attr(spec_id, "authored", True)
    except Exception:
        pass

    # Graph-visible marker so authored tools are a queryable class.
    marker_id = substrate.add_node(TOOLAUTHORED_NODE_TYPE, {
        "name": name, "kind": kind, "wrap": wrap,
        "input_types": list(input_types), "output_type": output_type,
        "realized": False,
    })
    for et, tgt in (("authored", spec_id),):
        try:
            substrate.add_edge(marker_id, et, tgt)
        except Exception:
            try:
                substrate.add_edge_unchecked(marker_id, et, tgt)
            except Exception:
                pass

    return {
        "ok": True,
        "name": name,
        "spec_node": spec_id,
        "marker_node": marker_id,
        "input_types": list(input_types),
        "output_type": output_type,
        "rust_output_type": rust_type_for(output_type),
        "kind": kind,
        "wrap": wrap,
        "handler_key": handler_key,
        "external": True,
    }


def _type_known(substrate, name: str) -> bool:
    """Is ``name`` a type the agent has a model of? Base types + concrete
    ``List<elem>`` over a known element count as known; anything else must be a
    ``Type`` node already installed in the graph."""
    if name in BASE_TYPES:
        return True
    if name.startswith("List<") and name.endswith(">"):
        return _type_known(substrate, name[len("List<"):-1])
    # A concrete Type node may have been registered (e.g. register_list_type).
    try:
        hits = substrate.nodes_where("Type", "name", name)
        if hits:
            return True
    except Exception:
        pass
    try:
        for nid in substrate.nodes("Type"):
            if substrate.node(nid)["attrs"].get("name") == name:
                return True
    except Exception:
        pass
    return False


def _validate_descriptor(kind: str, handler: dict, arity: int) -> tuple[bool, str]:
    """Mechanical shape-check of the handler DESCRIPTOR. No decisions about
    behaviour — just that the data is well-formed for the kind."""
    if not isinstance(handler, dict):
        return False, f"handler descriptor must be a dict, got {type(handler).__name__}"
    if kind == "process":
        argv = handler.get("argv")
        if not isinstance(argv, list) or not argv or \
                not all(isinstance(t, str) for t in argv):
            return False, "process handler needs a non-empty list[str] 'argv'"
        stdin = handler.get("stdin")
        if stdin is not None and not isinstance(stdin, str):
            return False, "process handler 'stdin' must be a '{i}' template str"
        return True, ""
    if kind == "library":
        if not isinstance(handler.get("module"), str) or \
                not isinstance(handler.get("func"), str):
            return False, "library handler needs str 'module' and str 'func'"
        return True, ""
    return False, f"unknown kind: {kind!r}"


# ---------------------------------------------------------------------------
# 2. realize_tool — the mechanical REGISTRAR (world-adapter I/O, no decisions)
# ---------------------------------------------------------------------------

def realize_tool(substrate, name: str, _native=None) -> bool:
    """Wire the agent-specified tool's handler into BOTH dispatch paths.

    Reads the ``ToolSpec`` + its ``handler_descriptor``, mechanically builds a
    handler closure (process: fill argv template + run subprocess + parse
    stdout to the typed output; library: import + call), and registers it into:

      * ``tool_use._HANDLERS`` (the world-adapter ``use_tool`` path), AND
      * the native registry via ``register_tool_handler(name, closure)`` (the
        engine ``UseTool`` path).

    Mechanical only — no decisions. Idempotent (re-registering replaces).
    Returns True on success, False if there is no such authored spec.
    """
    spec_id = tool_use._find_tool(substrate, name)
    if spec_id is None:
        return False
    spec = dict(substrate.node(spec_id)["attrs"])
    desc_raw = spec.get("handler_descriptor")
    if not desc_raw:
        return False
    descriptor = json.loads(desc_raw) if isinstance(desc_raw, str) else desc_raw

    kind = spec.get("kind", "library")
    output_type = spec.get("output_type", "Str")
    wrap = spec.get("wrap", "graph")
    handler_key = spec.get("handler_key", f"authored::{name}")
    input_types = list(spec.get("input_types", []))

    if kind == "process":
        closure = _build_process_handler(descriptor, input_types,
                                         output_type, wrap)
    elif kind == "library":
        closure = _build_library_handler(descriptor, input_types,
                                         output_type, wrap)
    else:
        return False

    # Path A: world-adapter use_tool dispatch (keyed by handler_key).
    tool_use.register_handler(handler_key, closure)

    # Path B: native UseTool dispatch (keyed by tool NAME).
    if _native is None:
        import substrate_rs._native as _native
    _native.register_tool_handler(name, closure)

    # Flip the graph-visible realized marker.
    try:
        for mid in substrate.nodes(TOOLAUTHORED_NODE_TYPE):
            if substrate.node(mid)["attrs"].get("name") == name:
                substrate.set_attr(mid, "realized", True)
    except Exception:
        pass
    return True


def _coerce(value: str, output_type: str, wrap: str) -> Any:
    """Parse a stdout / library string to the declared output type. On a
    parse miss, fall back to the raw text (the wrap='text' honesty path the
    use_tool wrapper already enforces downstream)."""
    if wrap == "text" or output_type == "Str":
        return value
    try:
        if output_type == "Int":
            return int(value.strip())
        if output_type == "Float":
            return float(value.strip())
        if output_type == "Bool":
            t = value.strip().lower()
            if t in ("true", "1", "yes"):
                return True
            if t in ("false", "0", "no", ""):
                return False
            return bool(t)
    except (ValueError, TypeError):
        return value
    return value


def _build_process_handler(descriptor: dict, input_types: list[str],
                           output_type: str, wrap: str):
    """Build a process handler: fill the argv template with the typed args,
    run the subprocess (timeout + output cap), parse stdout to output_type.

    The argv is a FIXED template + ``str(arg)`` substitutions — NOT shell;
    ``subprocess.run`` is given a list argv (no shell interpretation), which
    bounds what an authored process tool can do. Exposes ``_last_argv`` /
    ``_last_returncode`` on the closure so a demo can prove a real shell-out."""
    argv_template = list(descriptor["argv"])
    stdin_template = descriptor.get("stdin")

    def run(*args: Any) -> Any:
        # Boundary typecheck (defence in depth — use_tool also checks).
        for i, (a, t) in enumerate(zip(args, input_types)):
            if not typecheck(a, t):
                raise TypeError(
                    f"arg {i}: expected {t}, got {type_of_value(a)} ({a!r})")
        sargs = [str(a) for a in args]
        argv = [tok.format(*sargs) for tok in argv_template]
        stdin_data = stdin_template.format(*sargs) if stdin_template else None
        proc = subprocess.run(
            argv, capture_output=True, text=True,
            input=stdin_data, timeout=_PROC_TIMEOUT)
        out = proc.stdout[:_PROC_MAX_OUTPUT].strip()
        run._last_argv = argv          # type: ignore[attr-defined]
        run._last_returncode = proc.returncode  # type: ignore[attr-defined]
        run._last_stderr = proc.stderr  # type: ignore[attr-defined]
        return _coerce(out, output_type, wrap)

    run._last_argv = None              # type: ignore[attr-defined]
    return run


def _build_library_handler(descriptor: dict, input_types: list[str],
                           output_type: str, wrap: str):
    """Build a library handler: import ``module``, get ``func``, typecheck +
    call with the typed args, return the typed result. The import target is
    resolved ONCE at realize time so a bad module fails realization, not at
    every call."""
    module = importlib.import_module(descriptor["module"])
    fn = getattr(module, descriptor["func"])

    def run(*args: Any) -> Any:
        for i, (a, t) in enumerate(zip(args, input_types)):
            if not typecheck(a, t):
                raise TypeError(
                    f"arg {i}: expected {t}, got {type_of_value(a)} ({a!r})")
        result = fn(*args)
        # A native-string library result wanting a non-Str type goes through
        # the same coercion; otherwise the value is returned as-is and
        # use_tool's wrapper applies the typed/honesty guard.
        if isinstance(result, str) and output_type != "Str" and wrap != "text":
            return _coerce(result, output_type, wrap)
        return result

    return run


# ---------------------------------------------------------------------------
# 3. authored_tools — graph query over the agent's own tool boundaries
# ---------------------------------------------------------------------------

def authored_tools(substrate) -> list[dict]:
    """List the agent-authored tools (a graph query over ``ToolAuthored``
    markers joined to their ``ToolSpec``). Returns one dict per authored tool
    with its typed signature, kind, and realized flag."""
    out: list[dict] = []
    try:
        markers = list(substrate.nodes(TOOLAUTHORED_NODE_TYPE))
    except Exception:
        markers = []
    for mid in markers:
        attrs = dict(substrate.node(mid)["attrs"])
        name = attrs.get("name")
        spec_id = tool_use._find_tool(substrate, name) if name else None
        spec_attrs = dict(substrate.node(spec_id)["attrs"]) if spec_id else {}
        out.append({
            "name": name,
            "kind": attrs.get("kind"),
            "input_types": attrs.get("input_types", []),
            "output_type": attrs.get("output_type"),
            "rust_output_type": rust_type_for(attrs.get("output_type", "Str")),
            "wrap": attrs.get("wrap"),
            "realized": attrs.get("realized", False),
            "external": True,
            "doc": spec_attrs.get("doc", ""),
            "marker_node": mid,
            "spec_node": spec_id,
        })
    out.sort(key=lambda d: d.get("name") or "")
    return out


__all__ = [
    "TOOLAUTHORED_NODE_TYPE",
    "agent_specify_tool",
    "realize_tool",
    "authored_tools",
]

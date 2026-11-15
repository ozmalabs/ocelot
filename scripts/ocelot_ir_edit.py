"""ocelot_ir_edit — authored Python replacements as hub IR, rendered by the
graph renderer and spliced into the lossless Python CST.

THE MODEL. `ocelot_code_edit` edits Python by naming semantic operations over
AST/symbol targets; the replacement text there is still opaque source. This
adapter takes the next step for *authored* code: the replacement code is a hub
`Prog*` Term-JSON tree, rendered to Python by the EXISTING graph renderer
(`domains.render_python.render_ir` over the graph-resident RenderRules in
`seeds/render_python_statements.json`), then spliced into the target's exact
source span through `ozagia.edit.lossless.LosslessText`. There is no second
renderer and no text-patch fallback here.

WHAT IS MECHANICAL / DEV TOOLING (CLAUDE.md admissibility):

  * AST-path resolution, span computation, fixed IR-shape validation, renderer
    invocation, CST splicing, hashing and atomic writes are mechanical. No
    decision over graph state is taken here; the caller (the dev-session
    graph / agent) decides WHICH address and WHICH IR.
  * `fallback_check` is a mechanical coverage probe used by the dispatcher to
    decide between this IR path and the CST fallback. It never edits.
  * This is dev tooling, not the agent runtime: nothing here is loaded by
    `runners/dsl/` or the live substrate.
  * The only Python assembled outside the renderer is the `def` header /
    indentation scaffolding that `render_program` already established (the
    signature is preserved by slicing, and parameters are rendered as
    `ProgDefFnParam` terms — plain identifier names are accepted as a
    convenience); every expression and statement surface comes from the graph
    renderer.

IR COVERAGE (honest, partial by construction). The renderable set is exactly
the python RenderRule seed: the `Prog*` statement variants (Seq, AssignVar,
AugAssign, TupleUnpack, IfStmt, ForEach, While, LoopCtl, Return, TryOr, Raise,
ImportStmt, Subscript/SubscriptSet, AttrGet/AttrSet, ContainerLit,
ComprehensionList/Gen, FString, IsOp, CallExtern, DefFnParam) plus the
expression-grain Terms the seed spells (Lit, Var, comparison/arithmetic/
boolean/IfThenElse/In, ...). Term types the hub engine has but the python seed
does not (e.g. `ProgSlice`, `BitAnd`, `Shl`) are reported as
`render_gap:<head> in python`; renderability refusals from the renderer
(e.g. an f-string literal that would need escaping) are reported verbatim.
Out-of-scope constructs (lambda/with/match/...) are reported as honest
blockers. No partial emit: if any op is blocked, the whole script is refused
and the file is untouched.

SPLICING. The target span comes from the same structural AST-path table the
CST editor uses (`ocelot_code_edit.ast_node_table`), and the replacement is
applied to the lossless leaf structure. Every leaf outside the replaced span
stays byte-identical, so comments/trivia BEFORE and AFTER the span survive
exactly. Comments INSIDE a replaced body/function are part of what was
replaced (the IR does not invent them). The result is re-parsed and compiled
before a preview is returned; apply additionally backs up under
`.ozagia/edits/backups/` and writes atomically.

OPS (v0):
    replace_expression_ir   target (AST path), term (hub IR expression)
    replace_body_ir         target (function/method path), stmts (hub IR list)
    replace_function_ir     target (function path), stmts or term, optional args
    fallback_check          target | term | stmts — renderability probe only
"""
from __future__ import annotations

import ast
import difflib
import re
import tokenize
from dataclasses import dataclass
from functools import lru_cache
from io import StringIO
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from ozagia.edit.code_edit import (
    FORBIDDEN_SCRIPT_KEYS,
    MAX_SOURCE_BYTES,
    CodeEditError,
    _char_col,
    _indent_at,
    _line_end_offset,
    _line_offsets,
    _offset,
    ast_node_table,
)
from ozagia.edit.txn import (
    SourceFile,
    check_base,
    detect_newline,
    encode_text,
    normalize_newlines,
    read_source,
    sha256_bytes,
    write_source,
)
from ozagia.edit.lossless import LosslessError, LosslessText, python_roundtrip

__all__ = ["apply_ir_edit_script", "fallback_check", "SUPPORTED_OPS"]

_NEWLINE_NAMES = {"\n": "lf", "\r\n": "crlf", "\r": "cr"}

SUPPORTED_OPS = ("replace_expression_ir", "replace_body_ir",
                 "replace_function_ir", "fallback_check")

DIFF_NOTE = ("a unified diff is a rendered view for humans; the canonical "
             "record is the hub-IR op list above")

# Raw-text / diff keys are refused in an IR-native op: the replacement must
# be authored as Term-JSON, not smuggled back in as source. `text` is included
# because accepting it would be a silent text-patch fallback.
_FORBIDDEN_OP_KEYS = ("diff", "patch", "unified_diff", "hunk", "text")

# Statement-only heads (the renderer spells these as statements, including the
# two assignment forms). A bare expression Term is ALSO legal in a statement
# list -- that is the emitter's bare-expression-statement shape.
_STATEMENT_HEADS = frozenset({
    "ProgSeq", "ProgAssignVar", "ProgAugAssign", "ProgTupleUnpack",
    "ProgIfStmt", "ProgForEach", "ProgWhile", "ProgLoopCtl", "ProgReturn",
    "ProgTryOr", "ProgRaise", "ProgImportStmt", "ProgAttrSet",
    "ProgSubscriptSet",
})

# Expression-grain heads the python rule set can spell. Deliberately excludes
# ProgAttrSet/ProgSubscriptSet (assignment syntax) and ProgDefFnParam (header
# only), which otherwise share the `Prog*` prefix.
_EXPRESSION_HEADS = frozenset({
    "Lit", "Var", "Eq", "Gt", "Gte", "Lt", "Lte", "Mod", "Minus", "Pow",
    "Div", "Plus", "Times", "And", "Or", "Not", "Neg", "IfThenElse", "In",
    "ProgSubscript", "ProgAttrGet", "ProgContainerLit",
    "ProgComprehensionList", "ProgComprehensionGen", "ProgFString",
    "ProgIsOp", "ProgCallExtern",
})

# Slot schema for the heads this adapter knows how to shape-check. Heads in
# the hub engine but absent here are coverage gaps reported by the renderer's
# own gap check, not shape errors invented by this module.
_SCHEMA: Dict[str, Dict[str, str]] = {
    "Lit": {"value": "literal"},
    "Var": {"name": "scalar"},
    "Eq": {"a": "expr", "b": "expr"},
    "Gt": {"a": "expr", "b": "expr"},
    "Gte": {"a": "expr", "b": "expr"},
    "Lt": {"a": "expr", "b": "expr"},
    "Lte": {"a": "expr", "b": "expr"},
    "Mod": {"a": "expr", "b": "expr"},
    "Minus": {"a": "expr", "b": "expr"},
    "Pow": {"a": "expr", "b": "expr"},
    "Div": {"a": "expr", "b": "expr"},
    "Plus": {"items": "expr_list"},
    "Times": {"items": "expr_list"},
    "And": {"items": "expr_list"},
    "Or": {"items": "expr_list"},
    "Not": {"arg": "expr"},
    "Neg": {"arg": "expr"},
    "IfThenElse": {"cond": "expr", "then": "expr", "other": "expr"},
    "In": {"member": "expr", "container": "expr"},
    "ProgSubscript": {"obj": "expr", "index": "expr"},
    "ProgAttrGet": {"obj": "expr", "attr": "scalar"},
    "ProgContainerLit": {"kind": "scalar", "items": "expr_list"},
    "ProgComprehensionList": {"var": "scalar", "source": "expr",
                              "expr": "expr", "cond": "expr_opt"},
    "ProgComprehensionGen": {"var": "scalar", "source": "expr",
                             "expr": "expr", "cond": "expr_opt"},
    "ProgFString": {"parts": "expr_list"},
    "ProgIsOp": {"a": "expr", "b": "expr", "negated": "scalar"},
    "ProgCallExtern": {"name": "scalar", "recv": "expr_opt",
                       "args": "expr_list"},
    "ProgDefFnParam": {"name": "scalar", "default": "expr_opt"},
    "ProgSeq": {"stmts": "stmt_list"},
    "ProgAssignVar": {"name": "scalar", "value": "expr"},
    "ProgAugAssign": {"name": "scalar", "op": "scalar", "value": "expr"},
    "ProgTupleUnpack": {"targets": "scalar_list", "value": "expr"},
    "ProgIfStmt": {"cond": "expr", "then": "stmt", "orelse": "stmt_opt"},
    "ProgForEach": {"var": "scalar", "iter": "expr", "body": "stmt",
                    "orelse": "stmt_opt"},
    "ProgWhile": {"cond": "expr", "body": "stmt", "orelse": "stmt_opt"},
    "ProgLoopCtl": {"kind": "scalar"},
    "ProgReturn": {"value": "expr_opt"},
    "ProgTryOr": {"body": "stmt", "exc_var": "scalar",
                  "handler": "stmt_opt"},
    "ProgRaise": {"exc": "expr_opt"},
    "ProgImportStmt": {"module": "scalar", "alias": "scalar",
                       "names": "scalar_list"},
    "ProgAttrSet": {"obj": "expr", "attr": "scalar", "value": "expr"},
    "ProgSubscriptSet": {"obj": "expr", "index": "expr", "value": "expr"},
}

# Engine Term types the python seed does not spell, kept here as a fallback
# vocabulary so an honest coverage gap is distinguishable from a typo when the
# DSL mirror cannot be imported.
_EXTRA_ENGINE_HEADS = frozenset({
    "Abs", "Argmax", "Argmin", "Ashr", "Atan2", "BitAnd", "BitOr", "BitXor",
    "Cos", "IDiv", "IRem", "Lshr", "Max", "MaxOver", "Min", "MinOver",
    "Prod", "ProgSlice", "Shl", "Sin", "Sqrt", "Sum",
})


# --------------------------------------------------------------------------- #
#  Renderer substrate + coverage probes (thin wrappers around the seed).
# --------------------------------------------------------------------------- #
def _new_render_substrate():
    """A fresh minimal substrate with the python statement RenderRules
    installed. Fresh per call so render-gap evidence never leaks between
    transactions. Raises CodeEditError when the engine is unavailable."""
    try:
        import substrate_rs as srs
        from domains.render_python import install_python_statement_renderer

        sub = srs.Substrate()
        install_python_statement_renderer(sub)
    except Exception as e:  # pragma: no cover - environment-dependent
        raise CodeEditError(
            f"hub-IR renderer unavailable: {e}; rebuild runners/dsl or use "
            f"the CST fallback") from e
    return sub


@lru_cache(maxsize=1)
def _known_heads() -> frozenset[str]:
    """Every hub Term head this adapter can classify. The DSL mirror is the
    source of truth; the render-rule heads + the local schema are always
    present even if that import is unavailable."""
    heads = set(_SCHEMA)
    try:
        from domains.render_python import build_render_rules
        heads.update(rule["head"] for rule in build_render_rules())
    except Exception:  # pragma: no cover - seed is in-tree
        pass
    try:
        from substrate import dsl
        heads.update(dsl._TERM_REGISTRY)
    except Exception:  # pragma: no cover - fallback vocabulary
        heads.update(_EXTRA_ENGINE_HEADS)
    return frozenset(heads)


def _dedupe(items: Sequence[str]) -> List[str]:
    seen: set[str] = set()
    out: List[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


def _coverage_blockers(sub, ir) -> List[str]:
    """The renderer's own honest refusals: missing RenderRules (render gaps)
    first, then renderability refusals. Mechanical enumeration, no policy."""
    from domains.render_python import (render_gap_check,
                                       renderability_refusals)
    gaps = [f"render_gap:{head} in python"
            for head in render_gap_check(sub, ir)]
    return _dedupe(gaps + list(renderability_refusals(ir)))


# --------------------------------------------------------------------------- #
#  Fixed IR shape validation (invalid IR raises; coverage gaps are blockers).
# --------------------------------------------------------------------------- #
def _term_head(term: Any, where: str) -> str:
    if not isinstance(term, dict):
        raise CodeEditError(
            f"{where}: invalid hub IR term (expected an object, got "
            f"{type(term).__name__})")
    head = term.get("type")
    if not isinstance(head, str) or not head:
        raise CodeEditError(
            f"{where}: invalid hub IR term (missing a string 'type')")
    if head not in _known_heads():
        raise CodeEditError(
            f"{where}: unknown hub IR term type {head!r}; this is not a hub "
            f"Term and would never render")
    return head


def _validate_slot(value: Any, kind: str, where: str) -> None:
    if kind in ("literal", "scalar"):
        return
    if kind == "scalar_list":
        if not isinstance(value, (list, tuple)):
            raise CodeEditError(f"{where}: expected a list of strings")
        for i, item in enumerate(value):
            if not isinstance(item, str):
                raise CodeEditError(
                    f"{where}[{i}]: expected a string, got "
                    f"{type(item).__name__}")
        return
    if kind == "expr":
        _validate_term(value, "expr", where)
    elif kind == "expr_opt":
        if value is not None:
            _validate_term(value, "expr", where)
    elif kind == "expr_list":
        if not isinstance(value, list):
            raise CodeEditError(f"{where}: expected a list of expressions")
        for i, item in enumerate(value):
            _validate_term(item, "expr", f"{where}[{i}]")
    elif kind == "stmt":
        _validate_term(value, "stmt", where)
    elif kind == "stmt_opt":
        if value is not None:
            _validate_term(value, "stmt", where)
    elif kind == "stmt_list":
        if not isinstance(value, list):
            raise CodeEditError(f"{where}: expected a list of statements")
        for i, item in enumerate(value):
            _validate_term(item, "stmt", f"{where}[{i}]")
    else:  # pragma: no cover - the schema table is static
        raise CodeEditError(f"{where}: unknown validation kind {kind!r}")


def _validate_term(term: Any, grain: str, where: str) -> None:
    """Shape/type validation only. A known hub head the python seed cannot
    render is left for `_coverage_blockers` so it is reported as a coverage
    gap, not mislabelled as malformed IR."""
    head = _term_head(term, where)
    if head not in _SCHEMA:
        return
    if grain == "expr" and head not in _EXPRESSION_HEADS:
        raise CodeEditError(
            f"{where}: {head} is not an expression term; use it in a "
            f"statement list (stmts) instead")
    if grain == "header" and head != "ProgDefFnParam":
        raise CodeEditError(
            f"{where}: function arguments must be ProgDefFnParam terms or "
            f"plain parameter-name strings, got {head}")
    if grain == "stmt" and head == "ProgDefFnParam":
        raise CodeEditError(
            f"{where}: ProgDefFnParam belongs in the function header; pass it "
            f"through the op's 'args', not 'stmts'")
    for field, kind in _SCHEMA[head].items():
        if field in term:
            _validate_slot(term[field], kind, f"{where}.{field}")


def _validate_statement_list(stmts: Any, where: str) -> List[Dict[str, Any]]:
    if not isinstance(stmts, list):
        raise CodeEditError(f"{where}: expected a list of hub IR statements")
    for i, stmt in enumerate(stmts):
        _validate_term(stmt, "stmt", f"{where}[{i}]")
    return stmts


# --------------------------------------------------------------------------- #
#  Rendered text (every surface comes from domains.render_python).
# --------------------------------------------------------------------------- #
def _render_expression(sub, term: Dict[str, Any]) -> Tuple[Optional[str],
                                                           List[str]]:
    from domains.render_python import render_ir
    _validate_term(term, "expr", "term")
    blockers = _coverage_blockers(sub, term)
    if blockers:
        return None, blockers
    try:
        text = render_ir(sub, term, indent="")
    except (TypeError, ValueError) as e:
        raise CodeEditError(f"invalid hub IR term: {e}") from e
    if text is None:
        return None, ["render_none"]
    if "\n" in text or "\r" in text or not text.strip():
        return None, ["expression_render_not_single_line"]
    try:
        ast.parse(text, mode="eval")
    except SyntaxError as e:
        raise CodeEditError(
            f"rendered IR is not a Python expression ({text!r}): {e}") from e
    return text, []


def _render_block(sub, stmts: List[Dict[str, Any]],
                  indent: str) -> Tuple[Optional[str], List[str]]:
    """Render a statement list as a block whose FIRST line also carries
    `indent` (the ProgSeq contract leaves the first line unindented; the
    placing container prefixes it). Returns text WITHOUT a trailing newline."""
    from domains.render_python import render_ir
    _validate_statement_list(stmts, "stmts")
    ir = {"type": "ProgSeq", "stmts": stmts}
    blockers = _coverage_blockers(sub, ir)
    if blockers:
        return None, blockers
    try:
        text = render_ir(sub, ir, indent=indent)
    except (TypeError, ValueError) as e:
        raise CodeEditError(f"invalid hub IR statement list: {e}") from e
    if text is None:
        return None, ["render_none"]
    text = text.rstrip("\n")
    if not text.strip():
        return None, ["empty_statement_render"]
    return indent + text, []


def _render_params(sub, args: Any) -> Tuple[Optional[str], List[str]]:
    if isinstance(args, str):
        args = [args]
    if not isinstance(args, list):
        raise CodeEditError("args must be a list of ProgDefFnParam terms or "
                            "plain parameter-name strings")
    from domains.render_python import render_ir
    rendered: List[str] = []
    for i, arg in enumerate(args):
        if isinstance(arg, str):
            if not arg.isidentifier():
                raise CodeEditError(
                    f"args[{i}]: plain arguments must be identifiers, got "
                    f"{arg!r}; use a ProgDefFnParam term for defaults")
            rendered.append(arg)
            continue
        _validate_term(arg, "header", f"args[{i}]")
        blockers = _coverage_blockers(sub, arg)
        if blockers:
            return None, blockers
        try:
            text = render_ir(sub, arg, indent="")
        except (TypeError, ValueError) as e:
            raise CodeEditError(f"invalid hub IR parameter: {e}") from e
        if text is None or "\n" in text:
            return None, [f"param_render_invalid:{i}"]
        rendered.append(text)
    return ", ".join(rendered), []


# --------------------------------------------------------------------------- #
#  AST addressing + exact signature/source spans.
# --------------------------------------------------------------------------- #
_PATH_PART = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)(?:\[(\d+)\])?$")


def _resolve_ast_node(tree: ast.AST, path: str) -> ast.AST:
    if not path:
        return tree
    node: Any = tree
    for part in path.split("."):
        m = _PATH_PART.match(part)
        if not m:
            raise CodeEditError(f"malformed AST path segment {part!r}")
        field, index = m.group(1), m.group(2)
        if not hasattr(node, field):
            raise CodeEditError(
                f"no AST field {field!r} at {part!r} in path {path!r}")
        value = getattr(node, field)
        if index is None:
            if not isinstance(value, ast.AST):
                raise CodeEditError(
                    f"AST field {field!r} is not a node in path {path!r}")
            node = value
        else:
            i = int(index)
            if not isinstance(value, list) or i >= len(value):
                raise CodeEditError(
                    f"AST list {field!r} has no index {i} in path {path!r}")
            node = value[i]
            if not isinstance(node, ast.AST):
                raise CodeEditError(
                    f"AST list {field!r}[{i}] is not a node in path {path!r}")
    return node


def _line_text(source: str, offsets: List[int], lineno: int) -> str:
    start = offsets[max(0, lineno - 1)]
    end = offsets[lineno] if lineno < len(offsets) else len(source)
    return source[start:end]


def _signature_inner_span(source: str, offsets: List[int],
                          node: ast.FunctionDef) -> Tuple[int, int, str]:
    """(inner-start, inner-end, return-suffix) for the signature, found by
    tokenizing (so parens/colons inside defaults and strings are safe). The
    suffix is the exact text between the closing paren and the header colon
    (empty, or e.g. `" -> int"`), so a return annotation survives a rebuild."""
    want_line = node.lineno
    want_col = _char_col(_line_text(source, offsets, node.lineno),
                         node.col_offset)
    depth = 0
    state = 0
    open_end: Optional[int] = None
    close_end: Optional[int] = None
    try:
        tokens = tokenize.generate_tokens(StringIO(source).readline)
        for tok in tokens:
            ttype, text, start, end = tok[0], tok[1], tok[2], tok[3]
            if state == 0:
                if (ttype == tokenize.NAME and text == "def"
                        and start[0] == want_line and start[1] == want_col):
                    state = 1
                continue
            if state == 1:
                if ttype == tokenize.OP and text == "(":
                    open_end = _offset(offsets, end[0], end[1])
                    depth = 1
                    state = 2
                continue
            if state == 2:
                if ttype == tokenize.OP:
                    if text in "([{":
                        depth += 1
                    elif text in ")]}":
                        depth -= 1
                        if depth == 0:
                            close_end = _offset(offsets, end[0], end[1])
                            close_start = _offset(offsets, start[0], start[1])
                            state = 3
                continue
            # state 3: the first depth-0 colon ends the signature; anything
            # before it (return annotation / whitespace) is preserved.
            if ttype == tokenize.OP:
                if text in "([{":
                    depth += 1
                elif text in ")]}":
                    depth -= 1
                elif text == ":" and depth == 0:
                    colon_start = _offset(offsets, start[0], start[1])
                    return open_end, close_start, source[close_end:colon_start]
    except (tokenize.TokenError, IndentationError) as e:
        raise CodeEditError(f"cannot tokenize function signature: {e}") from e
    raise CodeEditError(
        f"cannot locate the signature parentheses of def {node.name!r}")


def _body_edit_span(source: str, offsets: List[int],
                    node: ast.FunctionDef) -> Tuple[int, int, str]:
    """(start, end, newline_prefix) for replacing the body statements.
    The prefix is inserted before the rendered block for a one-line body,
    which must be expanded onto its own lines."""
    body = node.body
    if not body:  # pragma: no cover - syntactically impossible
        raise CodeEditError("function has no body statements")
    first, last = body[0], body[-1]
    end = _line_end_offset(offsets, int(getattr(last, "end_lineno",
                                                last.lineno)), len(source))
    if first.lineno == node.lineno:
        line_start = offsets[first.lineno - 1]
        line_end = (offsets[first.lineno] if first.lineno < len(offsets)
                    else len(source))
        start = line_start + _char_col(source[line_start:line_end],
                                       first.col_offset)
        # Also consume the spaces between the header colon and the one-line
        # body, so the expanded block does not leave trailing whitespace.
        while start > line_start and source[start - 1] in " \t":
            start -= 1
        return start, end, "\n"
    return offsets[first.lineno - 1], end, ""


# --------------------------------------------------------------------------- #
#  Planned edits (computed against the base source, applied bottom-up).
# --------------------------------------------------------------------------- #
@dataclass
class _Edit:
    start: int
    end: int
    text: str
    change: Dict[str, Any]
    check: Optional[Tuple[str, str]] = None


def _normalise_target(target: Any) -> Optional[str]:
    """Accept the same string / {'path': ...} target spelling as
    `ocelot_code_edit`, so the dispatcher can pass either."""
    if isinstance(target, dict):
        target = target.get("path") or target.get("node_id")
    if isinstance(target, str) and target.strip():
        return target.strip()
    return None


def _op_target(op: Dict[str, Any]) -> str:
    target = _normalise_target(op.get("target", op.get("path")))
    if target is None:
        raise CodeEditError(f"{op.get('op')}: missing target AST path")
    return target


def _target_node(source: str, tree: ast.AST, table: Dict[str, Any],
                 path: str) -> Tuple[Any, ast.AST]:
    rec = table.get(path)
    if rec is None:
        available = ", ".join(list(table)[:30])
        raise CodeEditError(
            f"no AST node at path {path!r}; available (first 30): {available}")
    return rec, _resolve_ast_node(tree, path)


def _plan_expression(source: str, tree: ast.AST, table: Dict[str, Any],
                     sub, op: Dict[str, Any]) -> Tuple[List[_Edit],
                                                      List[str]]:
    path = _op_target(op)
    rec, node = _target_node(source, tree, table, path)
    if not isinstance(node, ast.expr) or isinstance(node, (ast.Slice,
                                                           ast.Starred)):
        raise CodeEditError(
            f"replace_expression_ir: target {path!r} is "
            f"{type(node).__name__}, not a replaceable expression")
    # An f-string part is not a standalone expression position: replacing a
    # Constant literal part or a whole FormattedValue would splice rendered
    # EXPRESSION text into quoted f-string text (a silent semantic change).
    # Replace the whole JoinedStr with a ProgFString term, or target the
    # FormattedValue's own `.value` child.
    if rec.parent is not None and rec.field == "values":
        parent = table.get(rec.parent)
        if parent is not None and parent.node_type == "JoinedStr":
            raise CodeEditError(
                f"replace_expression_ir: {path!r} is an f-string part; target "
                f"the FormattedValue.value child or replace the whole string "
                f"expression with a ProgFString term")
    term = op.get("term")
    if term is None:
        raise CodeEditError("replace_expression_ir needs a 'term'")
    text, blockers = _render_expression(sub, term)
    if blockers:
        return [], blockers
    text = normalize_newlines(text, detect_newline(source))
    change = {
        "op": "replace_expression_ir",
        "target": path,
        "type": type(node).__name__,
        "summary": f"replace expression at {path} with hub IR "
                   f"{term.get('type')}",
    }
    return [_Edit(rec.start, rec.end, text, change,
                  check=("expr", path))], []


def _plan_body(source: str, tree: ast.AST, table: Dict[str, Any], sub,
               op: Dict[str, Any]) -> Tuple[List[_Edit], List[str]]:
    path = _op_target(op)
    _, node = _target_node(source, tree, table, path)
    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        raise CodeEditError(
            f"replace_body_ir: target {path!r} is {type(node).__name__}, "
            f"not a function/method")
    stmts = op.get("stmts")
    if not isinstance(stmts, list):
        raise CodeEditError("replace_body_ir needs a 'stmts' list")
    offsets = _line_offsets(source)
    indent = _indent_at(source, offsets, node.lineno) + "    "
    rendered, blockers = _render_block(sub, stmts, indent)
    if blockers:
        return [], blockers
    start, end, prefix = _body_edit_span(source, offsets, node)
    text = normalize_newlines(prefix + rendered + "\n", detect_newline(source))
    change = {
        "op": "replace_body_ir",
        "target": path,
        "type": type(node).__name__,
        "summary": f"replace body of {node.name} with {len(stmts)} hub-IR "
                   f"statement(s)",
    }
    return [_Edit(start, end, text, change,
                  check=("function", path))], []


def _plan_function(source: str, tree: ast.AST, table: Dict[str, Any], sub,
                   op: Dict[str, Any]) -> Tuple[List[_Edit], List[str]]:
    path = _op_target(op)
    _, node = _target_node(source, tree, table, path)
    if isinstance(node, ast.AsyncFunctionDef):
        return [], ["async_function"]
    if not isinstance(node, ast.FunctionDef):
        raise CodeEditError(
            f"replace_function_ir: target {path!r} is "
            f"{type(node).__name__}, not a function/method")
    has_stmts = "stmts" in op and op["stmts"] is not None
    has_term = "term" in op and op["term"] is not None
    if has_stmts == has_term:
        raise CodeEditError(
            "replace_function_ir needs exactly one of 'stmts' or 'term'")
    if has_term:
        stmts = [{"type": "ProgReturn", "value": op["term"]}]
    else:
        if not isinstance(op["stmts"], list):
            raise CodeEditError("replace_function_ir: 'stmts' must be a list")
        stmts = op["stmts"]

    offsets = _line_offsets(source)
    indent = _indent_at(source, offsets, node.lineno)
    body_indent = indent + "    "
    rendered, blockers = _render_block(sub, stmts, body_indent)
    if blockers:
        return [], blockers

    inner_start, inner_end, return_suffix = _signature_inner_span(
        source, offsets, node)
    if op.get("args") is None:
        signature = source[inner_start:inner_end]
    else:
        signature, blockers = _render_params(sub, op["args"])
        if blockers:
            return [], blockers

    start = offsets[node.lineno - 1]          # def line: decorators stay put
    end = _line_end_offset(offsets, int(getattr(node, "end_lineno",
                                               node.lineno)), len(source))
    text = normalize_newlines(
        f"{indent}def {node.name}({signature}){return_suffix}:\n"
        f"{rendered}\n", detect_newline(source))
    change = {
        "op": "replace_function_ir",
        "target": path,
        "type": type(node).__name__,
        "summary": f"replace function {node.name} with {len(stmts)} hub-IR "
                   f"statement(s)",
    }
    return [_Edit(start, end, text, change,
                  check=("function", path))], []


_PLANNERS = {
    "replace_expression_ir": _plan_expression,
    "replace_body_ir": _plan_body,
    "replace_function_ir": _plan_function,
}


def _plan_ops(source: str, tree: ast.AST, table: Dict[str, Any],
              ops: List[Dict[str, Any]]) -> Tuple[List[_Edit], List[str]]:
    sub = None
    edits: List[_Edit] = []
    blockers: List[str] = []
    for op in ops:
        if not isinstance(op, dict):
            raise CodeEditError("each op must be an object")
        kind = op.get("op")
        if not isinstance(kind, str) or not kind.strip():
            raise CodeEditError("each op needs an 'op' name")
        kind = kind.strip()
        if kind == "fallback_check":
            raise CodeEditError(
                "fallback_check must be the only op in a script and is "
                "routed by apply_ir_edit_script(), not mixed with edits")
        if kind not in _PLANNERS:
            raise CodeEditError(
                f"unknown IR edit op {kind!r}; supported: "
                f"{', '.join(SUPPORTED_OPS)}")
        for key in _FORBIDDEN_OP_KEYS:
            if key in op:
                raise CodeEditError(
                    f"raw {key!r} input is refused in an IR edit op: author "
                    f"the replacement as hub IR Term-JSON; a text patch is "
                    f"not an IR-native edit")
        if sub is None:
            sub = _new_render_substrate()
        planned, op_blockers = _PLANNERS[kind](source, tree, table, sub, op)
        edits.extend(planned)
        blockers.extend(op_blockers)
    return edits, _dedupe(blockers)


# --------------------------------------------------------------------------- #
#  Lossless splice + structural verification.
# --------------------------------------------------------------------------- #
def _apply_lossless(source: str, edits: List[_Edit]) -> Tuple[str, dict]:
    try:
        doc = LosslessText.from_python(source)
    except LosslessError as e:
        raise CodeEditError(f"source cannot round-trip through the lossless "
                            f"CST: {e}") from e
    ordered = sorted(edits, key=lambda e: (e.start, e.end))
    roundtrip = doc.render() == source
    previous_end = -1
    for edit in ordered:
        if edit.start < previous_end:
            raise CodeEditError("overlapping edits in one script")
        if edit.start < 0 or edit.end < edit.start or edit.end > len(source):
            raise CodeEditError(
                f"edit span {edit.start}:{edit.end} is outside the source")
        previous_end = edit.end
    # Bottom-up: earlier offsets stay valid because later spans are replaced
    # first. LosslessText preserves every leaf outside the replaced range.
    for edit in reversed(ordered):
        doc.replace(edit.start, edit.end, edit.text)
    new_source = doc.render()

    # Mechanical proof of the lossless contract: every character outside the
    # declared spans is identical in the result.
    src_pos = new_pos = 0
    outside_ok = True
    for edit in ordered:
        unchanged = source[src_pos:edit.start]
        if new_source[new_pos:new_pos + len(unchanged)] != unchanged:
            outside_ok = False
            break
        new_pos += len(unchanged) + len(edit.text)
        src_pos = edit.end
    if outside_ok:
        outside_ok = new_source[new_pos:] == source[src_pos:]
    if not outside_ok:  # pragma: no cover - LosslessText guarantees this
        raise CodeEditError("lossless splice changed text outside the "
                            "target span")
    return new_source, {
        "python_cst": True,
        "roundtrip": roundtrip,
        "outside_spans_unchanged": True,
        "spans": [[e.start, e.end] for e in ordered],
        "leaves": len(doc.leaves),
    }


def _verify_structure(new_source: str, edits: List[_Edit], *,
                      name: str = "<ir-edit>") -> None:
    try:
        tree = ast.parse(new_source)
        compile(new_source, name, "exec")
    except (SyntaxError, ValueError) as e:
        raise CodeEditError(f"edit would not parse: {e}") from e
    for edit in edits:
        if not edit.check:
            continue
        grain, path = edit.check
        try:
            node = _resolve_ast_node(tree, path)
        except CodeEditError as e:
            raise CodeEditError(
                f"edit moved the target path {path!r} out of the tree: {e}"
            ) from e
        if grain == "expr" and not isinstance(node, ast.expr):
            raise CodeEditError(
                f"edit no longer resolves {path!r} to an expression")
        if grain == "function" and not isinstance(
                node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            raise CodeEditError(
                f"edit no longer resolves {path!r} to a function")


# --------------------------------------------------------------------------- #
#  Result contract.
# --------------------------------------------------------------------------- #
def _base_result(file: str, src: SourceFile, ops: List[dict],
                 *, ok: bool, new_source: str, applied: bool,
                 changes: List[dict], blockers: List[str],
                 backup: Optional[str], lossless: dict,
                 diff_view: str = "") -> Dict[str, Any]:
    source = src.text
    new_sha = sha256_bytes(encode_text(src, new_source))
    return {
        "ok": ok,
        "file": file,
        "applied": applied,
        "format": "python",
        "engine": "hub_ir",
        "renderer": "domains.render_python",
        "base_sha256": src.sha256,
        "new_sha256": new_sha,
        "before": {"lines": len(source.splitlines()), "sha256": src.sha256},
        "after": {"lines": len(new_source.splitlines()),
                  "sha256": new_sha},
        "ops": ops,
        "changes": changes,
        "diff_view": diff_view,
        "diff_note": DIFF_NOTE,
        "backup": backup,
        "newline": _NEWLINE_NAMES[src.newline],
        "bom": src.bom,
        "lossless": lossless,
        "graph_stale": bool(applied),
        "blockers": blockers,
    }


def _refused_result(file: str, src: SourceFile, ops: List[dict],
                    blockers: List[str]) -> Dict[str, Any]:
    return _base_result(
        file, src, ops,
        ok=False, new_source=src.text, applied=False, changes=[],
        blockers=_dedupe(blockers), backup=None,
        lossless={"python_cst": True,
                  "roundtrip": python_roundtrip(src.text),
                  "outside_spans_unchanged": True, "spans": []},
        diff_view="")


# --------------------------------------------------------------------------- #
#  fallback_check — coverage probe for the dispatcher / CST fallback.
# --------------------------------------------------------------------------- #
def _fallback_check_ir(source: str, tree: ast.AST, table: Dict[str, Any],
                       sub, op: Dict[str, Any]) -> Tuple[
                           Optional[Dict[str, Any]], List[str], str, str,
                           Optional[str]]:
    """(ir, blockers, grain, node_type, rendered_preview)."""
    target = _normalise_target(op.get("target", op.get("path")))
    has_target = target is not None
    has_term = "term" in op and op["term"] is not None
    has_stmts = "stmts" in op and op["stmts"] is not None
    if sum((has_target, has_term, has_stmts)) != 1:
        raise CodeEditError(
            "fallback_check needs exactly one of 'target', 'term', or "
            "'stmts'")

    if has_term:
        text, blockers = _render_expression(sub, op["term"])
        return op["term"], blockers, "expr", "Term", text

    if has_stmts:
        text, blockers = _render_block(sub, op["stmts"], "")
        ir = {"type": "ProgSeq", "stmts": op["stmts"]}
        return ir, blockers, "stmts", "ProgSeq", text

    assert target is not None
    path = target
    rec, node = _target_node(source, tree, table, path)
    node_type = type(node).__name__
    if isinstance(node, ast.expr) and rec.parent is not None \
            and rec.field == "values":
        parent = table.get(rec.parent)
        if parent is not None and parent.node_type == "JoinedStr":
            return None, ["fstring_part_target"], "expr", node_type, None

    if isinstance(node, ast.FunctionDef):
        offsets = _line_offsets(source)
        start = offsets[node.lineno - 1]
        end = _line_end_offset(offsets, int(getattr(node, "end_lineno",
                                                   node.lineno)), len(source))
        from domains.prog_ir_emit import emit_prog_ir
        try:
            emitted = emit_prog_ir(source[start:end])
        except ValueError as e:
            raise CodeEditError(
                f"cannot emit hub IR from target {path!r}: {e}") from e
        if not emitted.get("ok"):
            return None, list(emitted.get("blockers") or ["emit_blocked"]), \
                "function", node_type, None
        ir = emitted["ir"]
        from domains.render_python import render_program
        try:
            out = render_program(sub, ir, name=node.name)
        except (TypeError, ValueError) as e:
            raise CodeEditError(f"invalid hub IR emitted from {path!r}: "
                                f"{e}") from e
        if not out.get("ok"):
            return ir, list(out.get("refusals") or out.get("render_gaps")
                            or ["render_blocked"]), "function", node_type, None
        return ir, [], "function", node_type, out.get("source")

    # Single expression / statement probe: use the emitter's fixed walk
    # directly so a `return` or `break` need not be wrapped in a synthetic
    # function (which could fail to parse for reasons unrelated to IR).
    from domains.prog_ir_emit import ProgIrEmitter, _AstView  # noqa: PLC2701

    em = ProgIrEmitter(_AstView())
    if isinstance(node, ast.expr) and not isinstance(node, ast.Slice):
        ir = em.emit_expr(node)
        grain = "expr"
        if not em.blockers and not isinstance(ir, dict):
            blockers = ["Other:empty_expression"]
            text = None
        elif not em.blockers:
            text, blockers = _render_expression(sub, ir)
        else:
            text, blockers = None, []
    elif isinstance(node, ast.stmt):
        ir = em.emit_stmt(node)
        grain = "stmt"
        if not em.blockers and not isinstance(ir, dict):
            # `pass` (and a bare annotation) is a legitimate no-op statement.
            if isinstance(node, ast.Pass):
                ir = {"type": "ProgSeq", "stmts": []}
            else:
                ir = None
        if not em.blockers:
            if ir is None:
                text, blockers = None, ["empty_statement"]
            else:
                text, blockers = _render_block(sub, [ir], "")
    else:
        raise CodeEditError(
            f"fallback_check: target {path!r} is {node_type}, which is not "
            f"a function/expression/statement")
    blockers = _dedupe(list(em.blockers) + list(blockers))
    return ir, blockers, grain, node_type, text


def fallback_check(root: str | Path, script: Dict[str, Any]) -> Dict[str, Any]:
    """Report whether a construct (or a supplied Term-JSON tree) is
    IR-renderable. Read-only; never writes. `ok` is the answer: False means
    the dispatcher should use the CST fallback, with `blockers` naming why."""
    if not isinstance(script, dict):
        raise CodeEditError("edit script must be an object")
    for key in FORBIDDEN_SCRIPT_KEYS:
        if key in script:
            raise CodeEditError(
                f"raw {key!r} input is refused: send semantic ops over graph "
                f"targets; a diff is only an output view")
    ops = script.get("ops")
    if not isinstance(ops, list) or len(ops) != 1 \
            or not isinstance(ops[0], dict) or ops[0].get("op") != \
            "fallback_check":
        raise CodeEditError(
            "fallback_check takes a script with exactly one "
            "{'op': 'fallback_check', ...} op")

    root = Path(root).resolve()
    file, path, src = _load_python_file(root, script)
    source = src.text
    tree, table = _parse_source(source)
    sub = _new_render_substrate()
    op = ops[0]
    for key in _FORBIDDEN_OP_KEYS:
        if key in op:
            raise CodeEditError(
                f"raw {key!r} input is refused in an IR edit op: author the "
                f"replacement as hub IR Term-JSON")
    ir, blockers, grain, node_type, rendered = _fallback_check_ir(
        source, tree, table, sub, op)
    blockers = _dedupe(blockers)
    ok = not blockers
    result = _base_result(
        file, src, ops,
        ok=ok, new_source=source, applied=False,
        changes=[{"op": "fallback_check",
                  "target": _normalise_target(
                      op.get("target", op.get("path"))),
                  "summary": "IR-renderable" if ok else
                             "not IR-renderable; use the CST fallback"}],
        blockers=blockers, backup=None,
        lossless={"python_cst": True,
                  "roundtrip": python_roundtrip(source),
                  "outside_spans_unchanged": True, "spans": []},
        diff_view="")
    result.update({
        "check": "fallback_check",
        "renderable": ok,
        "grain": grain,
        "node_type": node_type,
        "ir": ir,
        "rendered": rendered,
    })
    return result


# --------------------------------------------------------------------------- #
#  Public entry point.
# --------------------------------------------------------------------------- #
def _load_python_file(root: Path, script: Dict[str, Any]) -> Tuple[
        str, Path, SourceFile]:
    file = str(script.get("file") or "").strip()
    if not file:
        raise CodeEditError("edit script needs file")
    path = (root / file).resolve()
    try:
        path.relative_to(root)
    except ValueError as e:
        raise CodeEditError("file escapes the repo root") from e
    if path.suffix != ".py":
        raise CodeEditError("v0 IR edits are Python (.py) only; Rust/Lua use "
                            "the CST adapter and hub-IR readers")
    src = read_source(root, file, suffixes=(".py",),
                      max_bytes=MAX_SOURCE_BYTES, error_cls=CodeEditError)
    check_base(src, script.get("base_sha256"), CodeEditError)
    return file, path, src


def _parse_source(source: str) -> Tuple[ast.AST, Dict[str, Any]]:
    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        raise CodeEditError(f"source does not parse: {e}") from e
    return tree, ast_node_table(source)


def apply_ir_edit_script(root: str | Path, script: Dict[str, Any], *,
                         write: bool = False) -> Dict[str, Any]:
    """Validate and optionally apply a hub-IR-native Python edit script.

    `write=False` (default) is a pure preview. `write=True` backs up the
    original under `.ozagia/edits/backups/`, writes atomically, and
    returns the backup path. Refusals raise `CodeEditError`; a well-formed
    script whose IR the renderer cannot spell returns `ok=False` with an
    honest `blockers` list and leaves the file untouched.
    """
    if not isinstance(script, dict):
        raise CodeEditError("edit script must be an object")
    for key in FORBIDDEN_SCRIPT_KEYS:
        if key in script:
            raise CodeEditError(
                f"raw {key!r} input is refused: send semantic ops over graph "
                f"targets; a diff is only an output view")
    ops = script.get("ops")
    if not isinstance(ops, list) or not ops:
        raise CodeEditError("edit script needs a non-empty ops list")
    if any(isinstance(op, dict) and op.get("op") == "fallback_check"
           for op in ops):
        if len(ops) != 1:
            raise CodeEditError(
                "fallback_check must be the only op in a script")
        if write:
            raise CodeEditError("fallback_check is read-only; write must be "
                                "false")
        return fallback_check(root, script)

    root = Path(root).resolve()
    file, path, src = _load_python_file(root, script)
    source = src.text
    tree, table = _parse_source(source)
    edits, blockers = _plan_ops(source, tree, table, ops)
    if blockers:
        return _refused_result(file, src, ops, blockers)

    new_source, lossless = _apply_lossless(source, edits)
    _verify_structure(new_source, edits, name=str(path))

    diff_lines = list(difflib.unified_diff(
        source.splitlines(keepends=True),
        new_source.splitlines(keepends=True),
        fromfile=f"a/{file}", tofile=f"b/{file}",
    ))
    applied = False
    backup = None
    if write:
        backup = write_source(root, src, new_source, error_cls=CodeEditError)
        applied = True

    return _base_result(
        file, src, ops,
        ok=True, new_source=new_source, applied=applied,
        changes=[e.change for e in sorted(edits, key=lambda e: e.start)],
        blockers=[], backup=backup, lossless=lossless,
        diff_view="".join(diff_lines[:400]))

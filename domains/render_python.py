"""render_python — P5 (python frame): statement-grain hub-IR -> Python source,
as graph-resident RenderRules.

PROGRAM_SYNTHESIS_PLAN.md §4-P5 / PROGRAM_SYNTHESIS_PREREG.md §7 (H5), track A.
Companion results doc: PROGRAM_SYNTHESIS_P5_PYTHON.md.

WHAT THIS MODULE IS (CLAUDE.md admissibility):

  * `build_render_rules()` and its template helpers are seed BUILDERS — pure
    data constructors that emit RenderRule graph data (the `_compose_*_rule`
    precedent). The seed of record is `seeds/render_python_statements.json`;
    a gate asserts the file equals the builder output, so the two can never
    drift apart silently.
  * `install_python_statement_renderer` is a mechanical installer — the
    `install_render_rule` shape (RenderRule node + template Term-subgraph +
    has_rule edge), idempotent per head. No decisions over graph state.
  * `render_program` / `render_ir` are the mechanical render walker: they
    hand the IR subtree to the Rust `Render` engine (which dispatches per
    head over the graph-resident RenderRules) and do only the CODE-3
    statement SCAFFOLDING `code_writing.write_function` already set the
    precedent for — the `def` header assembly (params joined, docstring
    slot, base indent prefix) — plus the render-gap precheck that mirrors
    `WorldAdapter.render_in_graph`'s `render_gap:<head>` convention. EVERY
    expression/statement surface comes from the graph renderer; Python
    never assembles an expression.

THE INDENTATION DECISION (the registered hard bit — measured, then chosen):

  Indentation is GRAPH-SIDE. The Rust `Render` evaluator threads ONE shared
  env through nested `render_source_node` calls (rule slots are pushed onto
  the caller's env), so a `Let`-bound `indent` binding is visible to every
  nested statement render: block-introducing rules deepen it with
  `Let("indent", Cat(Slot("indent"), "    "), <render child>)`, and
  `ProgSeq` applies it per line via a `Cat("\n", Slot("indent"))` Join
  separator. Measured live before authoring (see the P5 doc §1): nested
  if-in-if renders at 0/4/8 columns with zero Python indent logic. The
  documented `code_writing._term_to_statements` fallback (a Python
  depth-walker) was NOT needed.

THE SHADOW DISCIPLINE (a real engine fact, measured, and the reason every
child render goes through `_rch`): the shared env means an ABSENT optional
slot (e.g. a nested `ProgIfStmt` with no `orelse`) would fall through to an
ENCLOSING render's same-named binding — measured: an inner else wrongly
inherited the outer orelse. Templates therefore shadow every optional /
variadic slot name with an explicit None (`Let(name, Lit(None), ...)`)
around each child render (`_sh`); a child that HAS the slot re-binds it on
top, one that lacks it sees the falsy shadow. Pure graph data; no engine
change.

RENDERABILITY REFUSALS (`renderability_refusals`) are mechanical validation
of the IR against what the rule set can HONESTLY spell (the render_in_graph
DFS-precheck precedent): f-string literal parts holding characters the
surface cannot carry without an escaping primitive, an aug-assign op outside
the ProgEval native set, a malformed dict literal. Refused, never silently
mis-rendered.
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional, Tuple

SEED_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                         "seeds", "render_python_statements.json")

SEED_ID = "render_python_statements"
SEED_VERSION = "1.0.0"

# --------------------------------------------------------------------------- #
#  Term-JSON constructors (pure data builders — the emission dialect).
# --------------------------------------------------------------------------- #
def S(text):        return {"type": "Surface", "kind": "text", "payload": text}
def SLOT(name):     return {"type": "Slot", "name": name}
def CAT(*items):    return {"type": "Cat", "items": list(items)}
def R(term):        return {"type": "Render", "term": term, "lang": None}
def LET(n, v, b):   return {"type": "Let", "name": n, "value": v, "body": b}
def ITE(c, t, o):   return {"type": "IfThenElse", "cond": c, "then": t, "other": o}
def JOIN(sep, it):  return {"type": "Join", "separator": sep, "items": it}
def LIT(v):         return {"type": "Lit", "value": v}
def VART(n):        return {"type": "Var", "name": n}
def EQT(a, b):      return {"type": "Eq", "a": a, "b": b}
def MAPL(src, var, val):
    return {"type": "MapList", "source": src, "var_name": var, "value": val}
def COUNTT(src):    return {"type": "Count", "source": src}
def TYPEOF(n):      return {"type": "TypeOf", "node": n}
def ATTRT(n, k):    return {"type": "Attr", "node": n, "key": k}
def MODT(a, b):     return {"type": "Mod", "a": a, "b": b}
def PLUST(*items):  return {"type": "Plus", "items": list(items)}
def MKD(*items):    return {"type": "MkDict", "items": list(items)}
def DG(d, k):       return {"type": "DictGet", "dict": d, "key": k}
def FOLD(src, var, acc, init, body):
    return {"type": "Fold", "source": src, "var_name": var,
            "acc_name": acc, "init": init, "body": body}


# The optional / variadic slot names any nested render might read: shadowed
# with an explicit falsy None around every child render so an ABSENT slot on
# the inner node can never leak an outer binding (measured hazard, docstring).
SHADOW_NAMES = ("orelse", "value", "exc", "handler", "default", "recv",
                "cond", "args", "stmts", "items", "parts")


def _sh(body):
    """Shadow all optional/variadic slot names with None around `body`."""
    for n in SHADOW_NAMES:
        body = LET(n, LIT(None), body)
    return body


def _rch(field):
    """Render the child bound at `field`: read the slot BEFORE shadowing
    (Let binds `__sh` in the rule's own frame), then render under shadows."""
    return LET("__sh", SLOT(field), _sh(R(VART("__sh"))))


def _deeper(body):
    """One indentation level deeper (4 spaces — the emitter reads any)."""
    return LET("indent", CAT(SLOT("indent"), S("    ")), body)


def _block(field):
    """A statement child as an indented block body (caller supplies ':\\n')."""
    return _deeper(CAT(SLOT("indent"), _rch(field)))


def _opt_else(field):
    """`else:` block iff the optional `field` child exists."""
    return ITE(SLOT(field),
               CAT(S("\n"), SLOT("indent"), S("else:\n"), _block(field)),
               S(""))


def _rendered_list(field):
    """Each element of a variadic child field rendered under shadows."""
    return MAPL(SLOT(field), "__p", _sh(R(VART("__p"))))


# ProgAugAssign op -> surface (the ProgEval native aug set, P1 §3 / P2 _AUGOP).
AUG_OPS = (("add", "+="), ("sub", "-="), ("mult", "*="), ("div", "/="),
           ("floordiv", "//="), ("mod", "%="), ("pow", "**="),
           ("lshift", "<<="), ("rshift", ">>="), ("bitand", "&="),
           ("bitor", "|="), ("bitxor", "^="))


def _aug_op_surface():
    """Nested ITE chain mapping the op Sym to its surface. Fallback is an
    explicit None — it POISONS the Cat (whole render -> None) so an unknown
    op can never render silently; `renderability_refusals` names it first."""
    out = LIT(None)
    for op, surf in reversed(AUG_OPS):
        out = ITE(EQT(SLOT("op"), LIT(op)), S(" " + surf + " "), out)
    return out


def _dict_pair_fold():
    """Alternating `k: v, k: v` join over the flat kv item list — a Fold
    whose accumulator dict carries the text so far and the item count
    (parity picks ': ' vs ', ')."""
    return DG(
        FOLD(_rendered_list("items"), "__it", "__acc",
             MKD(LIT("t"), LIT(""), LIT("n"), LIT(0)),
             MKD(LIT("t"),
                 CAT(DG(VART("__acc"), LIT("t")),
                     ITE(EQT(DG(VART("__acc"), LIT("n")), LIT(0)),
                         S(""),
                         ITE(EQT(MODT(DG(VART("__acc"), LIT("n")), LIT(2)),
                                 LIT(1)),
                             S(": "), S(", "))),
                     VART("__it")),
                 LIT("n"),
                 PLUST(DG(VART("__acc"), LIT("n")), LIT(1)))),
        LIT("t"))


# --------------------------------------------------------------------------- #
#  The rule set (language: python) — every P1 variant + the IR expression set.
# --------------------------------------------------------------------------- #
def build_render_rules() -> List[Dict[str, Any]]:
    """The full statement-grain python RenderRule set as plain data:
    [{"head", "binding_pattern", "template"}]. The seed file of record is
    written from exactly this (gate: file == builder output)."""
    rules: List[Dict[str, Any]] = []

    def rule(head, template, binding_pattern):
        rules.append({"head": head, "binding_pattern": list(binding_pattern),
                      "template": template})

    # ---- expression grain (the P2 IR expression closure) -------------------
    rule("Lit", CAT({"type": "LitRepr", "value": SLOT("value")}), ["value"])
    rule("Var", CAT(SLOT("name")), ["name"])
    for head, op in (("Eq", " == "), ("Gt", " > "), ("Gte", " >= "),
                     ("Lt", " < "), ("Lte", " <= "), ("Mod", " % "),
                     ("Minus", " - "), ("Pow", " ** "), ("Div", " / ")):
        rule(head, CAT(S("("), _rch("a"), S(op), _rch("b"), S(")")),
             ["a", "b"])
    for head, op in (("Plus", " + "), ("Times", " * "),
                     ("And", " and "), ("Or", " or ")):
        rule(head, CAT(S("("), JOIN(S(op), _rendered_list("items")), S(")")),
             ["items"])
    rule("Not", CAT(S("(not "), _rch("arg"), S(")")), ["arg"])
    rule("Neg", CAT(S("(-"), _rch("arg"), S(")")), ["arg"])
    rule("IfThenElse",
         CAT(S("("), _rch("then"), S(" if "), _rch("cond"),
             S(" else "), _rch("other"), S(")")),
         ["cond", "then", "other"])
    rule("In", CAT(S("("), _rch("member"), S(" in "), _rch("container"), S(")")),
         ["member", "container"])

    # ---- statement grain (all 23 P1 Prog* variants) ------------------------
    # ProgSeq: first line unindented (the placing container prefixes it);
    # every subsequent line at own depth via the separator; empty -> pass.
    rule("ProgSeq",
         ITE(SLOT("stmts"),
             LET("__sh", SLOT("stmts"),
                 _sh(JOIN(CAT(S("\n"), SLOT("indent")), VART("__sh")))),
             S("pass")),
         ["stmts"])
    rule("ProgAssignVar",
         CAT(SLOT("name"), S(" = "), _rch("value")), ["name", "value"])
    rule("ProgAugAssign",
         CAT(SLOT("name"), _aug_op_surface(), _rch("value")),
         ["name", "op", "value"])
    # Always-parenthesized target tuple: `(a, b) = v` / `(a,) = v` — parses
    # to the same Tuple target as the bare spelling; 1-target needs the comma.
    rule("ProgTupleUnpack",
         CAT(S("("), JOIN(S(", "), SLOT("targets")),
             ITE(EQT(COUNTT(SLOT("targets")), LIT(1)), S(","), S("")),
             S(") = "), _rch("value")),
         ["targets", "value"])
    rule("ProgIfStmt",
         CAT(S("if "), _rch("cond"), S(":\n"), _block("then"),
             _opt_else("orelse")),
         ["cond", "then", "orelse"])
    rule("ProgForEach",
         CAT(S("for "), SLOT("var"), S(" in "), _rch("iter"), S(":\n"),
             _block("body"), _opt_else("orelse")),
         ["var", "iter", "body", "orelse"])
    rule("ProgWhile",
         CAT(S("while "), _rch("cond"), S(":\n"), _block("body"),
             _opt_else("orelse")),
         ["cond", "body", "orelse"])
    rule("ProgLoopCtl", CAT(SLOT("kind")), ["kind"])
    rule("ProgReturn",
         ITE(SLOT("value"), CAT(S("return "), _rch("value")), S("return")),
         ["value"])
    # exc_var "" (the emitter's explicit sentinel) -> bare `except:`; a name
    # -> `except Exception as <name>:` (ProgTryOr catches ANY trap — the IR
    # never carries a narrower type, so Exception is the faithful spelling
    # the emitter maps straight back to exc_var).
    rule("ProgTryOr",
         CAT(S("try:\n"), _block("body"), S("\n"), SLOT("indent"),
             ITE(SLOT("exc_var"),
                 CAT(S("except Exception as "), SLOT("exc_var")),
                 S("except")),
             S(":\n"),
             ITE(SLOT("handler"), _block("handler"),
                 _deeper(CAT(SLOT("indent"), S("pass"))))),
         ["body", "exc_var", "handler"])
    rule("ProgRaise",
         ITE(SLOT("exc"), CAT(S("raise "), _rch("exc")), S("raise")),
         ["exc"])
    # names non-empty -> from-import; else plain import; alias "" -> none.
    rule("ProgImportStmt",
         ITE(SLOT("names"),
             CAT(S("from "), SLOT("module"), S(" import "),
                 JOIN(S(", "), SLOT("names")),
                 ITE(SLOT("alias"), CAT(S(" as "), SLOT("alias")), S(""))),
             CAT(S("import "), SLOT("module"),
                 ITE(SLOT("alias"), CAT(S(" as "), SLOT("alias")), S("")))),
         ["module", "alias", "names"])
    rule("ProgSubscript",
         CAT(_rch("obj"), S("["), _rch("index"), S("]")), ["obj", "index"])
    rule("ProgSubscriptSet",
         CAT(_rch("obj"), S("["), _rch("index"), S("] = "), _rch("value")),
         ["obj", "index", "value"])
    rule("ProgAttrGet",
         CAT(_rch("obj"), S("."), SLOT("attr")), ["obj", "attr"])
    rule("ProgAttrSet",
         CAT(_rch("obj"), S("."), SLOT("attr"), S(" = "), _rch("value")),
         ["obj", "attr", "value"])
    # Kind-faithful containers: dict pairs via the parity fold; 1-tuples get
    # the trailing comma; the empty set is spelled set() (there is no {}).
    rule("ProgContainerLit",
         ITE(EQT(SLOT("kind"), LIT("dict")),
             CAT(S("{"), _dict_pair_fold(), S("}")),
             ITE(EQT(SLOT("kind"), LIT("tuple")),
                 ITE(EQT(COUNTT(SLOT("items")), LIT(1)),
                     CAT(S("("), JOIN(S(", "), _rendered_list("items")), S(",)")),
                     CAT(S("("), JOIN(S(", "), _rendered_list("items")), S(")"))),
                 ITE(EQT(SLOT("kind"), LIT("set")),
                     ITE(SLOT("items"),
                         CAT(S("{"), JOIN(S(", "), _rendered_list("items")), S("}")),
                         S("set()")),
                     CAT(S("["), JOIN(S(", "), _rendered_list("items")), S("]"))))),
         ["kind", "items"])
    rule("ProgComprehensionList",
         CAT(S("["), _rch("expr"), S(" for "), SLOT("var"), S(" in "),
             _rch("source"),
             ITE(SLOT("cond"), CAT(S(" if "), _rch("cond")), S("")),
             S("]")),
         ["var", "source", "expr", "cond"])
    rule("ProgComprehensionGen",
         CAT(S("("), _rch("expr"), S(" for "), SLOT("var"), S(" in "),
             _rch("source"),
             ITE(SLOT("cond"), CAT(S(" if "), _rch("cond")), S("")),
             S(")")),
         ["var", "source", "expr", "cond"])
    # f-string: literal parts pass through RAW (the graph reads the part
    # node's own `value` attr — TypeOf discriminates Term.Lit); expression
    # parts render in-language inside {…}. Literal parts that would need
    # escaping are REFUSED up front (renderability_refusals), never bent.
    rule("ProgFString",
         CAT(S('f"'),
             JOIN(S(""),
                  MAPL(SLOT("parts"), "__p",
                       ITE(EQT(TYPEOF(VART("__p")), LIT("Term.Lit")),
                           ATTRT(VART("__p"), "value"),
                           CAT(S("{"), _sh(R(VART("__p"))), S("}"))))),
             S('"')),
         ["parts"])
    rule("ProgIsOp",
         CAT(S("("), _rch("a"),
             ITE(SLOT("negated"), S(" is not "), S(" is ")),
             _rch("b"), S(")")),
         ["a", "b", "negated"])
    rule("ProgCallExtern",
         CAT(ITE(SLOT("recv"),
                 CAT(_rch("recv"), S("."), SLOT("name")),
                 CAT(SLOT("name"))),
             S("("), JOIN(S(", "), _rendered_list("args")), S(")")),
         ["name", "recv", "args"])
    rule("ProgDefFnParam",
         CAT(SLOT("name"),
             ITE(SLOT("default"), CAT(S("="), _rch("default")), S(""))),
         ["name", "default"])

    return rules


def build_seed() -> Dict[str, Any]:
    """The seed manifest (data only; installed by this module's installer)."""
    return {"id": SEED_ID, "version": SEED_VERSION,
            "language": "python",
            "comment": "P5 track A: statement-grain python RenderRules — "
                       "hub Program-IR -> runnable source. Installed by "
                       "domains.render_python.install_python_statement_renderer.",
            "render_rules": build_render_rules()}


def write_seed(path: str = SEED_PATH) -> str:
    """One-shot authoring tool: write the seed file from the builder."""
    with open(path, "w") as fh:
        json.dump(build_seed(), fh, indent=1)
        fh.write("\n")
    return path


def load_seed(path: str = SEED_PATH) -> Dict[str, Any]:
    with open(path) as fh:
        return json.load(fh)


# --------------------------------------------------------------------------- #
#  Installer — mechanical graph-data installation (install_render_rule shape).
# --------------------------------------------------------------------------- #
def _store_native(agent) -> Tuple[Any, Any]:
    """(python-facing store, native handle) for a WorldAdapter or a raw
    substrate_rs.Substrate — pure accessor."""
    store = getattr(agent, "s", agent)
    native = getattr(agent, "inner", None) or getattr(store, "_inner", None) \
        or getattr(agent, "_inner", None)
    return store, native


def _language_node(store, language: str):
    for n in store.nodes("Language"):
        if store.node(n)["attrs"].get("name") == language:
            return n
    return None


def _rules_for(store, native, lang, head: str) -> List[Any]:
    return [r for r in native.neighbours(lang, "has_rule")
            if store.node(r)["attrs"].get("head") == head]


def install_python_statement_renderer(agent, *, language: str = "python",
                                      seed_path: str = SEED_PATH,
                                      skip_heads=()) -> Dict[str, Any]:
    """Install the seed's Language + RenderRule nodes. Idempotent per head
    (a head that already carries a rule in `language` is left alone — the
    established first-rule-wins render dispatch stays deterministic).
    `skip_heads` deliberately withholds heads (the render-gap honesty gate).
    Mechanical installation only."""
    store, native = _store_native(agent)
    seed = load_seed(seed_path)
    lang = _language_node(store, language)
    if lang is None:
        lang = store.add_node("Language", {"name": language,
                                           "surface_kind": "text",
                                           "held_in": "programming_languages"})
    installed, skipped = [], []
    for spec in seed["render_rules"]:
        head = spec["head"]
        if head in set(skip_heads) or _rules_for(store, native, lang, head):
            skipped.append(head)
            continue
        rid = store.add_node("RenderRule",
                             {"head": head,
                              "binding_pattern": tuple(spec["binding_pattern"]),
                              "priority": 0,
                              "provenance": "seed:%s" % SEED_ID})
        troot = native.add_term_subgraph(spec["template"])
        native.add_edge_unchecked(rid, "template", troot)
        native.add_edge_unchecked(lang, "has_rule", rid)
        installed.append(head)
    return {"language": lang, "installed": installed, "skipped": skipped,
            "seed_id": seed.get("id"), "seed_version": seed.get("version")}


# --------------------------------------------------------------------------- #
#  Render-gap precheck + renderability refusals (mechanical walks).
# --------------------------------------------------------------------------- #
def _ir_heads(ir) -> List[str]:
    """Every Term head in an IR JSON tree, first-seen order (mechanical)."""
    seen: List[str] = []

    def walk(t):
        if isinstance(t, dict):
            h = t.get("type")
            if isinstance(h, str) and h not in seen:
                seen.append(h)
            for v in t.values():
                walk(v)
        elif isinstance(t, (list, tuple)):
            for x in t:
                walk(x)
    walk(ir)
    return seen


_FSTRING_UNSPELLABLE = set('{}"\\\n\r')
_AUG_OP_SET = frozenset(op for op, _ in AUG_OPS)
_CONTAINER_KINDS = frozenset({"list", "tuple", "set", "dict"})
_LOOPCTL_KINDS = frozenset({"break", "continue"})


def renderability_refusals(ir) -> List[str]:
    """Facts about an IR tree the rule set cannot HONESTLY spell — refused
    up front, never silently mis-rendered (each names its reason). Pure
    enumeration; the caller reports the list verbatim."""
    out: List[str] = []

    def note(reason):
        if reason not in out:
            out.append(reason)

    def walk(t):
        if isinstance(t, dict):
            h = t.get("type")
            if h == "ProgFString":
                for p in t.get("parts") or []:
                    if isinstance(p, dict) and p.get("type") == "Lit" \
                            and isinstance(p.get("value"), str) \
                            and set(p["value"]) & _FSTRING_UNSPELLABLE:
                        note("fstring_literal_unspellable")
            elif h == "ProgAugAssign" and t.get("op") not in _AUG_OP_SET:
                note("aug_op_unknown:%s" % t.get("op"))
            elif h == "ProgContainerLit":
                if t.get("kind") not in _CONTAINER_KINDS:
                    note("container_kind_unknown:%s" % t.get("kind"))
                elif t.get("kind") == "dict" and len(t.get("items") or []) % 2:
                    note("dict_items_odd")
            elif h == "ProgLoopCtl" and t.get("kind") not in _LOOPCTL_KINDS:
                note("loopctl_kind_unknown:%s" % t.get("kind"))
            elif h == "ProgTupleUnpack" and not (t.get("targets") or []):
                note("tuple_unpack_no_targets")
            for v in t.values():
                walk(v)
        elif isinstance(t, (list, tuple)):
            for x in t:
                walk(x)
    walk(ir)
    return out


def render_gap_check(agent, ir, *, language: str = "python") -> List[str]:
    """The render_in_graph DFS-precheck convention at IR-JSON grain: any
    head with no RenderRule in `language` is recorded as a
    `render_gap:<head> in <language>` question (agent._render_gaps) plus a
    graph-resident Impasse{reason:'render_gap'} node (deduped), and the
    caller must not render. Returns the missing heads."""
    store, native = _store_native(agent)
    lang = _language_node(store, language)
    missing = [h for h in _ir_heads(ir)
               if lang is None or not _rules_for(store, native, lang, h)]
    if missing:
        gaps = getattr(agent, "_render_gaps", None)
        if gaps is None:
            gaps = []
            try:
                agent._render_gaps = gaps
            except AttributeError:
                pass
        existing = {(store.node(i)["attrs"].get("render_gap_head"),
                     store.node(i)["attrs"].get("render_gap_lang"))
                    for i in store.nodes("Impasse")}
        for h in missing:
            q = "render_gap:%s in %s" % (h, language)
            if q not in gaps:
                gaps.append(q)
            if (h, language) not in existing:
                store.add_node("Impasse", {"reason": "render_gap",
                                           "render_gap_head": h,
                                           "render_gap_lang": language,
                                           "question": q})
    return missing


# --------------------------------------------------------------------------- #
#  The render walker — graph renders every surface; Python only scaffolds.
# --------------------------------------------------------------------------- #
def render_ir(agent, ir, *, language: str = "python", indent: str = ""):
    """One IR subtree -> its surface via the Rust Render engine over the
    graph-resident rules. `indent` seeds the graph-side indent binding
    (the statement contract: first line unindented, deeper lines carry
    their own indent). Returns the surface string or None."""
    store, native = _store_native(agent)
    lang = _language_node(store, language)
    if lang is None:
        return None
    root = native.add_term_subgraph(ir)
    out = native.evaluate(
        {"type": "Render", "term": {"type": "Var", "name": "src"},
         "lang": {"type": "Var", "name": "render_lang"}},
        {"src": root, "render_lang": lang, "indent": indent})
    if isinstance(out, bytes):
        out = out.decode("utf-8", "replace")
    return out


def _program_ir(agent, program) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """(ir_json, name) from any accepted-Program spelling: an IR dict, a
    Term-JSON string, or a Program{name, program} node id (the P4 accept
    convention — `program` is the hub-IR Term-JSON string)."""
    if isinstance(program, dict):
        return program, None
    if isinstance(program, str):
        return json.loads(program), None
    store, _ = _store_native(agent)
    attrs = store.node(program)["attrs"]
    raw = attrs.get("program")
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8", "replace")
    name = attrs.get("name")
    if isinstance(name, bytes):
        name = name.decode("utf-8", "replace")
    return (json.loads(raw) if raw else None), name


def render_program(agent, program, *, name: Optional[str] = None,
                   docstring: Optional[str] = None,
                   language: str = "python") -> Dict[str, Any]:
    """Hub Program-IR -> a runnable `def`. The graph renders every param and
    statement surface; this walker does ONLY the write_function-precedent
    scaffolding: split the leading ProgDefFnParam prefix into the header,
    join params with ', ', place the docstring, prefix the base indent.
    Honest outcomes: {"ok": True, "source"} |
    {"ok": False, "render_gaps": [...]} | {"ok": False, "refusals": [...]}."""
    ir, prog_name = _program_ir(agent, program)
    if name is None:
        name = prog_name or "fn"
    if not isinstance(ir, dict) or ir.get("type") != "ProgSeq":
        return {"ok": False, "refusals": ["not_a_program_seq"]}

    refusals = renderability_refusals(ir)
    stmts = list(ir.get("stmts") or [])
    params = []
    while stmts and isinstance(stmts[0], dict) \
            and stmts[0].get("type") == "ProgDefFnParam":
        params.append(stmts.pop(0))
    if any(isinstance(s, dict) and s.get("type") == "ProgDefFnParam"
           for s in stmts):
        refusals.append("param_after_body")
    if refusals:
        return {"ok": False, "refusals": refusals}

    gaps = render_gap_check(agent, ir, language=language)
    if gaps:
        return {"ok": False,
                "render_gaps": ["render_gap:%s in %s" % (h, language)
                                for h in gaps]}

    param_surfaces = []
    for p in params:
        s = render_ir(agent, p, language=language, indent="")
        if s is None:
            return {"ok": False, "refusals": ["param_render_none"]}
        param_surfaces.append(s)

    lines = ["def %s(%s):" % (name, ", ".join(param_surfaces))]
    if docstring:
        lines.append('    """%s"""' % docstring)
    body_ir = {"type": "ProgSeq", "stmts": stmts}
    body = render_ir(agent, body_ir, language=language, indent="    ")
    if body is None:
        return {"ok": False, "refusals": ["body_render_none"]}
    if stmts or not docstring:
        lines.append("    " + body)
    return {"ok": True, "source": "\n".join(lines) + "\n", "name": name}


# --------------------------------------------------------------------------- #
#  Canonical IR — the DOCUMENTED round-trip comparison form (P5 doc §3).
#  Two IR trees mean the same program iff their canonical forms are equal.
#  The allowed deltas (each mechanical, each recorded in the P5 doc):
#    C1 null ≡ absent (the P1 reflect-dialect law, established);
#    C2 ProgSeq flattening — a ProgSeq element directly inside a
#       ProgSeq.stmts list splices inline (the emitter's statement-lift
#       preludes nest; re-reading the flat rendered text cannot);
#    C3 boolop normal form — And/Or fold to the emitter's OWN right-nested
#       IfThenElse operand desugar (re-reading `(a and b)` produces the
#       desugar; only chained comparisons ever emit a bare And);
#    C4 Neg(Lit k) ≡ Lit(-k) for non-bool numerics (Python's parser has no
#       negative literals; synthesized IR may);
#    C5 variadic left-fold — Plus/Times with >2 items left-associate into
#       binary nests (the parse shape).  Nothing else is normalized.
# --------------------------------------------------------------------------- #
def canonical_ir(t):
    if isinstance(t, (list, tuple)):
        return [canonical_ir(x) for x in t]
    if not isinstance(t, dict):
        return t
    h = t.get("type")
    if h == "ProgSeq":                                            # C2
        stmts = []
        for s in (t.get("stmts") or []):
            cs = canonical_ir(s)
            if isinstance(cs, dict) and cs.get("type") == "ProgSeq":
                stmts.extend(cs.get("stmts") or [])
            else:
                stmts.append(cs)
        return {"type": "ProgSeq", "stmts": stmts}
    if h in ("And", "Or"):                                        # C3 (+C1/C5)
        items = [canonical_ir(x) for x in (t.get("items") or [])]
        if len(items) < 2:
            return {"type": h, "items": items}
        out = items[-1]
        for val in reversed(items[:-1]):
            if h == "Or":
                out = {"type": "IfThenElse", "cond": val, "then": val,
                       "other": out}
            else:
                out = {"type": "IfThenElse", "cond": val, "then": out,
                       "other": val}
        return out
    if h == "Neg":                                                # C4
        arg = canonical_ir(t.get("arg"))
        if isinstance(arg, dict) and arg.get("type") == "Lit" \
                and isinstance(arg.get("value"), (int, float)) \
                and not isinstance(arg.get("value"), bool):
            return {"type": "Lit", "value": -arg["value"]}
        return {"type": "Neg", "arg": arg}
    if h in ("Plus", "Times"):                                    # C5
        items = [canonical_ir(x) for x in (t.get("items") or [])]
        while len(items) > 2:
            items = [{"type": h, "items": items[:2]}] + items[2:]
        return {"type": h, "items": items}
    out = {}
    for k, v in t.items():
        if v is None:                                             # C1
            continue
        out[k] = canonical_ir(v)
    return out


__all__ = ["build_render_rules", "build_seed", "write_seed", "load_seed",
           "install_python_statement_renderer", "render_ir", "render_program",
           "render_gap_check", "renderability_refusals", "canonical_ir",
           "SEED_PATH", "SEED_ID", "SEED_VERSION", "SHADOW_NAMES", "AUG_OPS"]

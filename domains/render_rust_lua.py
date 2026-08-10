"""render_rust_lua — statement-grain RUST + LUA rendering of the hub Program
IR (PROGRAM_SYNTHESIS_PLAN.md §4-P5 track B).

The renderers are GRAPH DATA: `seeds/render_rust_statements.json` and
`seeds/render_lua_statements.json` ship one `RenderRule` node per Term head
(template = a Term-JSON subgraph the Rust `Render` engine evaluates —
`term.rs::render_source_node` dispatch, the same machinery the taught Lua
expression renderer uses). This module contributes ONLY mechanical
translation, mirroring the P2 read side (`domains/prog_ir_rust.py` /
`prog_ir_lua.py`, whose tables + handlers are cross-frame maps too — plan §5):

  · `install_renderer` — seed JSON -> Language + RenderRule nodes (find-or-
    create, idempotent, skip-if-head-present).
  · pre-passes — pure, deterministic IR-JSON -> IR-JSON rewrites that run the
    P2 cross-frame maps BACKWARDS before the engine renders:
      rust: first-assignment `decl` marks (the read side conflates let/assign
            into ProgAssignVar; pre-order first assignment = the original
            `let` position).
      lua:  `decl` marks (`local`), the 1-based subscript shift stripped
            (`i - 1` -> `i`), the inclusive-stop numeric-for shift stripped,
            the ipairs counter-desugar folded back to `for k, v in ipairs`,
            the repeat body-duplication folded back to `repeat..until`, and
            Return(IfThenElse) -> ProgIfStmt[return][return] (lua has no if
            expression).
    Each rewrite is the structural inverse of a documented read-side desugar;
    re-reading the render restores the exact original IR (the round-trip
    gates in tests/test_render_rust_lua_migrated.py).
  · `_add_ir` — builds the render-source Term subgraph with the reflect.rs
    conventions (`Term.<head>` node types, `child.<field>` edges, `index`
    edge-attrs on variadic fields) plus the pre-pass annotation attrs
    (`decl`/`repeat`/`ipairs_k`) and children (`nf_start`/`nf_stop`/
    `nf_step`) the templates branch on. The annotated copy is render-input
    only — ProgEval always runs the un-annotated IR.
  · `render_function` — read-record/IR in, source text out (the fn wrapper:
    name + params + the type-annotation defaulting ladder for rust).
  · render gaps — a missing-rule head files a graph-resident Impasse
    (`render_gap:<head> in <language>`, the render_in_graph shape) and, on a
    WorldAdapter, joins `_render_gaps` so the standing render-gap ->
    self-teacher -> `install_render_rule` loop (the taught-Lua precedent)
    can close it. `render_via_teach_loop` drives exactly that loop.

No decisions over graph state anywhere: every conditional here inspects the
IR JSON being translated (a cross-frame map), never the agent's graph.
"""
from __future__ import annotations

import copy
import json
import os
from typing import Any, Dict, List, Optional, Tuple

_SEEDS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                          "seeds")

_SEED_FILES = {"rust": "render_rust_statements.json",
               "lua": "render_lua_statements.json"}

_SEED_CACHE: Dict[str, Dict[str, Any]] = {}


def load_render_seed(language: str) -> Dict[str, Any]:
    """The render seed manifest (cached; the FILE is the source of truth)."""
    if language not in _SEED_CACHE:
        with open(os.path.join(_SEEDS_DIR, _SEED_FILES[language])) as f:
            _SEED_CACHE[language] = json.load(f)
    return _SEED_CACHE[language]


def _parts(sub) -> Tuple[Any, Any]:
    """(node-level substrate, native engine) for either a WorldAdapter or a
    raw substrate_rs.Substrate. Pure attribute plumbing."""
    if hasattr(sub, "inner") and hasattr(sub, "s"):
        return sub.s, sub.inner            # WorldAdapter
    return sub, sub._inner                 # substrate_rs.Substrate


def _find_language(s, native, language: str):
    for n in s.nodes("Language"):
        if s.node(n)["attrs"].get("name") == language:
            return n
    return None


def _rule_heads(s, native, lang_node) -> set:
    heads = set()
    for r in native.neighbours(lang_node, "has_rule"):
        h = s.node(r)["attrs"].get("head")
        if h:
            heads.add(h)
    return heads


def install_renderer(sub, language: str):
    """Install the render seed's RenderRules as graph data (find-or-create
    Language; a head already present is never overwritten — so rules taught
    at runtime keep priority over the shipped seed). Returns the Language
    node. Mechanical seed loading."""
    s, native = _parts(sub)
    seed = load_render_seed(language)
    lang = _find_language(s, native, language)
    if lang is None:
        lang = s.add_node("Language", {
            "name": language, "surface_kind": "text",
            "held_in": "programming_languages",
            "origin": seed["seed"]["id"]})
    present = _rule_heads(s, native, lang)
    for r in seed["render_rules"]:
        if r["head"] in present:
            continue
        rid = s.add_node("RenderRule", {
            "head": r["head"],
            "binding_pattern": tuple(r["binding_pattern"]),
            "priority": 0,
            "origin": seed["seed"]["id"]})
        troot = native.add_term_subgraph(r["template"])
        native.add_edge_unchecked(rid, "template", troot)
        native.add_edge_unchecked(lang, "has_rule", rid)
    return lang


# ---------------------------------------------------------------------------
# IR-JSON helpers (pure).
# ---------------------------------------------------------------------------
_L = lambda v: {"type": "Lit", "value": v}  # noqa: E731


def _is(ir, ty) -> bool:
    return isinstance(ir, dict) and ir.get("type") == ty


def _is_lit(ir, v) -> bool:
    return _is(ir, "Lit") and ir.get("value") == v


def _children(ir):
    """Every sub-term of an IR dict (dict fields + dict-list fields +
    pre-pass `_child_*` extras), in field order."""
    for k, v in ir.items():
        if k == "type" or k.startswith("_attr_"):
            continue
        if isinstance(v, dict):
            yield v
        elif isinstance(v, list):
            for c in v:
                if isinstance(c, dict):
                    yield c


def _heads(ir) -> set:
    out = set()
    stack = [ir]
    while stack:
        n = stack.pop()
        if isinstance(n, dict) and "type" in n:
            out.add(n["type"])
            stack.extend(_children(n))
    return out


def _add_ir(s, native, ir):
    """Build the render-source subgraph with the reflect.rs conventions the
    Render engine binds against: `Term.<head>` types, scalar fields as node
    attrs, single sub-terms as `child.<field>` edges, list fields as indexed
    `child.<field>` edges. Pre-pass annotations ride along: `_attr_<k>` ->
    node attr `<k>`; `_child_<k>` -> a `child.<k>` edge."""
    attrs: Dict[str, Any] = {}
    kids: List[Tuple[str, List[dict], bool]] = []
    for k, v in ir.items():
        if k == "type":
            continue
        if k.startswith("_attr_"):
            attrs[k[len("_attr_"):]] = v
            continue
        if k.startswith("_child_"):
            if isinstance(v, dict):
                kids.append((k[len("_child_"):], [v], False))
            continue
        if isinstance(v, dict):
            kids.append((k, [v], False))
        elif isinstance(v, list):
            if all(isinstance(c, dict) for c in v):
                kids.append((k, v, True))
            else:
                attrs[k] = tuple(v)
        elif v is None:
            continue
        else:
            attrs[k] = v
    nid = s.add_node("Term." + ir["type"], attrs)
    for field, items, variadic in kids:
        for i, c in enumerate(items):
            cid = _add_ir(s, native, c)
            native.add_edge_unchecked(nid, "child." + field, cid,
                                      {"index": i} if variadic else None)
    return nid


def _seq_stmts(ir) -> List[dict]:
    return list(ir["stmts"]) if _is(ir, "ProgSeq") else [ir]


def _stmt_of(stmts: List[dict]) -> dict:
    return stmts[0] if len(stmts) == 1 else {"type": "ProgSeq", "stmts": stmts}


def _split_params(ir) -> Tuple[List[str], dict]:
    """Strip a leading ProgDefFnParam run (the P4 Program convention) into a
    param-name list; the remainder is the body."""
    stmts = _seq_stmts(ir)
    names, rest = [], []
    for st in stmts:
        if _is(st, "ProgDefFnParam") and not rest:
            names.append(st["name"])
        else:
            rest.append(st)
    return names, _stmt_of(rest) if rest else {"type": "ProgSeq", "stmts": []}


# ---------------------------------------------------------------------------
# Pre-passes (pure IR-JSON rewrites; each is a read-side desugar run
# backwards — the structural inverses documented in the seed notes).
# ---------------------------------------------------------------------------
def _mark_decls(ir, declared: set) -> None:
    """First assignment (pre-order) of an undeclared name gets the `decl`
    mark — the original let/local position for read IR (the read side maps
    both declaration and assignment to ProgAssignVar)."""
    if not isinstance(ir, dict):
        return
    if _is(ir, "ProgAssignVar"):
        name = ir.get("name")
        if name not in declared:
            ir["_attr_decl"] = True
            declared.add(name)
    if _is(ir, "ProgForEach"):
        declared.add(ir.get("var"))
        k = ir.get("_attr_ipairs_k")
        if k:
            declared.add(k)
    for c in _children(ir):
        _mark_decls(c, declared)


def _fold_ipairs(stmts: List[dict]) -> List[dict]:
    """[.., AssignVar k=0, ForEach{v, xs, Seq[AugAssign k add 1, ..rest]}, ..]
    -> [.., ForEach{v, xs, rest, ipairs_k=k}, ..] — the lua generic-for
    desugar inverted; re-reading the rendered `for k, v in ipairs(xs)`
    restores the desugared IR exactly."""
    out: List[dict] = []
    i = 0
    while i < len(stmts):
        a = stmts[i]
        b = stmts[i + 1] if i + 1 < len(stmts) else None
        if (b is not None and _is(a, "ProgAssignVar") and _is_lit(a.get("value"), 0)
                and _is(b, "ProgForEach") and _is(b.get("body"), "ProgSeq")):
            body = b["body"]["stmts"]
            if (body and _is(body[0], "ProgAugAssign")
                    and body[0].get("name") == a.get("name")
                    and body[0].get("op") == "add"
                    and _is_lit(body[0].get("value"), 1)):
                folded = dict(b)
                folded["body"] = _stmt_of(body[1:]) if body[1:] else \
                    {"type": "ProgSeq", "stmts": []}
                folded["_attr_ipairs_k"] = a.get("name")
                out.append(folded)
                i += 2
                continue
        out.append(a)
        i += 1
    return out


def _fold_repeat(stmts: List[dict]) -> List[dict]:
    """[.., B.., While{cond: Not C, body == B}, ..] -> [.., While{repeat,
    cond: C, body: B}, ..] — the lua repeat desugar (body emitted twice)
    inverted; re-reading `repeat B until C` restores the duplicated IR."""
    for j, st in enumerate(stmts):
        if not (_is(st, "ProgWhile") and _is(st.get("cond"), "Not")
                and not st.get("_attr_repeat")):
            continue
        body_list = _seq_stmts(st["body"])
        k = len(body_list)
        if k == 0 or j - k < 0:
            continue
        prefix = stmts[j - k:j]
        if json.dumps(prefix, sort_keys=True) != json.dumps(body_list, sort_keys=True):
            continue
        folded = dict(st)
        folded["cond"] = st["cond"]["arg"]
        folded["_attr_repeat"] = True
        return stmts[:j - k] + [folded] + stmts[j + 1:]
    return stmts


def _strip_plus1(ir) -> Optional[dict]:
    if _is(ir, "Plus") and len(ir.get("items", [])) == 2 \
            and _is_lit(ir["items"][1], 1):
        return ir["items"][0]
    return None


def _strip_minus1(ir) -> Optional[dict]:
    if _is(ir, "Minus") and _is_lit(ir.get("b"), 1):
        return ir["a"]
    return None


def _lua_rewrite(ir) -> dict:
    """The lua-frame render rewrites, bottom-up over one IR node (callers
    recurse). Pure structure; every case is a documented inverse."""
    if not isinstance(ir, dict):
        return ir
    # recurse first (children rewritten before this node's own shape tests)
    for k, v in list(ir.items()):
        if k == "type":
            continue
        if isinstance(v, dict):
            ir[k] = _lua_rewrite(v)
        elif isinstance(v, list):
            ir[k] = [_lua_rewrite(c) if isinstance(c, dict) else c for c in v]
    if _is(ir, "ProgSeq"):
        ir["stmts"] = _fold_repeat(_fold_ipairs(ir["stmts"]))
        if len(ir["stmts"]) == 1:
            return ir["stmts"][0]
        return ir
    # Return(IfThenElse) -> ProgIfStmt[return][return] (lua has no if-expr).
    if _is(ir, "ProgReturn") and _is(ir.get("value"), "IfThenElse"):
        ite = ir["value"]
        return {"type": "ProgIfStmt", "cond": ite["cond"],
                "then": {"type": "ProgReturn", "value": ite["then"]},
                "orelse": {"type": "ProgReturn", "value": ite["other"]}}
    # subscript: strip the read-side `i - 1` shift (else add `i + 1`).
    if ir.get("type") in ("ProgSubscript", "ProgSubscriptSet"):
        idx = ir.get("index")
        stripped = _strip_minus1(idx)
        ir["index"] = stripped if stripped is not None else \
            {"type": "Plus", "items": [idx, _L(1)]}
        return ir
    # numeric for: range-extern iter -> nf_* children with the inclusive
    # stop recovered (strip the read-side ±1 shift; else wrap stop-1).
    if _is(ir, "ProgForEach") and not ir.get("_attr_ipairs_k"):
        it = ir.get("iter")
        if (_is(it, "ProgCallExtern") and it.get("name") == "range"
                and it.get("recv") is None and len(it.get("args", [])) in (2, 3)):
            args = it["args"]
            step = args[2] if len(args) == 3 else None
            negative = _is(step, "Neg") or (_is(step, "Lit")
                                            and isinstance(step.get("value"), (int, float))
                                            and step.get("value") < 0)
            stop = args[1]
            if negative:
                stripped = _strip_minus1(stop)
                inclusive = stripped if stripped is not None else \
                    {"type": "Plus", "items": [stop, _L(1)]}
            else:
                stripped = _strip_plus1(stop)
                inclusive = stripped if stripped is not None else \
                    {"type": "Minus", "a": stop, "b": _L(1)}
            ir["_child_nf_start"] = args[0]
            ir["_child_nf_stop"] = inclusive
            if step is not None:
                ir["_child_nf_step"] = step
        return ir
    return ir


def prep_rust(body: dict, param_names: List[str]) -> dict:
    body = copy.deepcopy(body)
    _mark_decls(body, set(param_names))
    return body


def prep_lua(body: dict, param_names: List[str]) -> dict:
    body = copy.deepcopy(body)
    body = _lua_rewrite(body)
    _mark_decls(body, set(param_names))
    return body


_PREP = {"rust": prep_rust, "lua": prep_lua}


# ---------------------------------------------------------------------------
# The rust type-annotation defaulting ladder (task pin: annotations from the
# read-side record when present; synthesized programs default to i64; a param
# used as an iterable/subscript object defaults to Vec<i64>).
# ---------------------------------------------------------------------------
_BOOL_HEADS = {"Eq", "Gt", "Gte", "Lt", "Lte", "And", "Or", "Not", "ProgIsOp"}


def _walk(ir):
    stack = [ir]
    while stack:
        n = stack.pop()
        if isinstance(n, dict) and "type" in n:
            yield n
            stack.extend(_children(n))


def _rust_param_ty(name: str, annotated: str, body: dict) -> str:
    if annotated:
        return annotated
    for n in _walk(body):
        if _is(n, "ProgForEach") and _is(n.get("iter"), "Var") \
                and n["iter"].get("name") == name:
            return "Vec<i64>"
        if n.get("type") in ("ProgSubscript", "ProgSubscriptSet") \
                and _is(n.get("obj"), "Var") and n["obj"].get("name") == name:
            return "Vec<i64>"
    return "i64"


def _rust_ret_ty(body: dict) -> str:
    for n in _walk(body):
        if _is(n, "ProgReturn") and n.get("value") is not None:
            v = n["value"]
            h = v.get("type")
            if h in _BOOL_HEADS:
                return "bool"
            if h == "ProgContainerLit":
                return "Vec<i64>"
            if h == "ProgFString":
                return "String"
            if h == "Lit":
                if isinstance(v.get("value"), bool):
                    return "bool"
                if isinstance(v.get("value"), float):
                    return "f64"
                if isinstance(v.get("value"), str):
                    return "String"
            return "i64"
    return ""


def _rust_param_muts(body: dict, param_names: List[str]) -> set:
    muts = set()
    for n in _walk(body):
        if n.get("type") in ("ProgAssignVar", "ProgAugAssign") \
                and n.get("name") in param_names and not n.get("_attr_decl"):
            muts.add(n["name"])
    return muts


# ---------------------------------------------------------------------------
# Render gaps (graph-resident; the taught-Lua loop's shape).
# ---------------------------------------------------------------------------
def _file_render_gaps(sub, missing: List[str], language: str) -> None:
    """Record each missing head as an Impasse (`render_gap:<head> in <lang>`,
    deduped — render_in_graph's shape) and, on a WorldAdapter, join the
    `_render_gaps` question list the self-teacher drain consumes. Mechanical
    fact recording."""
    s, _native = _parts(sub)
    existing = set()
    for n in s.nodes("Impasse"):
        a = s.node(n)["attrs"]
        if a.get("reason") == "render_gap":
            existing.add((a.get("render_gap_head"), a.get("render_gap_lang")))
    adapter_gaps = None
    if hasattr(sub, "drain_all_taught_threads"):
        adapter_gaps = getattr(sub, "_render_gaps", None)
        if adapter_gaps is None:
            adapter_gaps = sub._render_gaps = []
    for h in missing:
        q = "render_gap:%s in %s" % (h, language)
        if adapter_gaps is not None and q not in adapter_gaps:
            adapter_gaps.append(q)
        if (h, language) not in existing:
            s.add_node("Impasse", {"reason": "render_gap",
                                   "render_gap_head": h,
                                   "render_gap_lang": language,
                                   "question": q})


# ---------------------------------------------------------------------------
# Entry points.
# ---------------------------------------------------------------------------
def _normalize(rec_or_ir, name: Optional[str], params) -> Tuple[str, List[Dict[str, str]], dict]:
    if isinstance(rec_or_ir, dict) and "ir" in rec_or_ir and "type" not in rec_or_ir:
        rec = rec_or_ir
        ir = rec["ir"]
        pnames, body = _split_params(ir)
        rparams = rec.get("params") or [{"name": n, "ty": ""} for n in pnames]
        return rec.get("name") or name or "f", list(rparams), body
    pnames, body = _split_params(rec_or_ir)
    if params is not None:
        rparams = [p if isinstance(p, dict) else {"name": p, "ty": ""} for p in params]
    else:
        rparams = [{"name": n, "ty": ""} for n in pnames]
    return name or "f", rparams, body


def render_body(sub, body_ir: dict, language: str, *, param_names=(),
                install_seed: bool = True) -> Dict[str, Any]:
    """Pre-pass + render ONE body (no fn wrapper). {ok, text, gaps}."""
    s, native = _parts(sub)
    if install_seed:
        lang = install_renderer(sub, language)
    else:
        lang = _find_language(s, native, language)
        if lang is None:
            lang = s.add_node("Language", {"name": language, "surface_kind": "text"})
    prepped = _PREP[language](body_ir, list(param_names))
    missing = sorted(h for h in _heads(prepped)
                     if h not in _rule_heads(s, native, lang))
    if missing:
        _file_render_gaps(sub, missing, language)
        return {"ok": False, "text": None, "gaps": missing, "prepped": prepped}
    root = _add_ir(s, native, prepped)
    text = native.evaluate(
        {"type": "Render", "term": {"type": "Var", "name": "src"},
         "lang": {"type": "Var", "name": "render_lang"}},
        {"src": root, "render_lang": lang})
    if text is None:
        # engine-level gap (a template's guard hit Lit None — e.g. a non-list
        # container kind): file under the offending root head, honestly.
        _file_render_gaps(sub, ["engine:" + prepped.get("type", "?")], language)
        return {"ok": False, "text": None,
                "gaps": ["engine:" + prepped.get("type", "?")], "prepped": prepped}
    return {"ok": True, "text": text, "gaps": [], "prepped": prepped}


def render_function(sub, rec_or_ir, language: str, *, name: Optional[str] = None,
                    params=None, install_seed: bool = True) -> Dict[str, Any]:
    """Render a whole function: a P2 read record ({name, params, ir}) or a
    raw hub IR (P4 Program convention — leading ProgDefFnParam stmts are the
    params). Returns {ok, source, gaps, name}. The wrapper (signature line)
    is assembled mechanically, mirroring the read side which extracts
    name/params outside the IR."""
    fn_name, rparams, body = _normalize(rec_or_ir, name, params)
    out = render_body(sub, body, language, install_seed=install_seed,
                      param_names=[p["name"] for p in rparams])
    if not out["ok"]:
        return {"ok": False, "source": None, "gaps": out["gaps"], "name": fn_name}
    prepped = out["prepped"]
    if language == "rust":
        pnames = [p["name"] for p in rparams]
        muts = _rust_param_muts(prepped, pnames)
        sig_params = ", ".join(
            "%s%s: %s" % ("mut " if p["name"] in muts else "", p["name"],
                          _rust_param_ty(p["name"], p.get("ty", ""), body))
            for p in rparams)
        ret = _rust_ret_ty(body)
        arrow = " -> %s" % ret if ret else ""
        source = "fn %s(%s)%s {\n%s;\n}" % (fn_name, sig_params, arrow, out["text"])
    else:
        sig_params = ", ".join(p["name"] for p in rparams)
        source = "function %s(%s)\n%s\nend" % (fn_name, sig_params, out["text"])
    return {"ok": True, "source": source, "gaps": [], "name": fn_name}


def render_via_teach_loop(wa, rec_or_ir, language: str, *, max_iters: int = 25,
                          name: Optional[str] = None, params=None) -> Dict[str, Any]:
    """Drive the standing render-gap -> self-teacher -> install_render_rule
    loop (tests/test_teach_lua_renderer_migrated.py precedent) at statement
    grain: NO seed install — every rule must arrive through the teacher.
    Iterate render (files gaps) -> master_tick -> drain until convergence."""
    out = None
    for _ in range(max_iters):
        out = render_function(wa, rec_or_ir, language, name=name, params=params,
                              install_seed=False)
        if out["ok"]:
            return out
        wa.master_tick()
        wa.drain_all_taught_threads(timeout=2.0)
    return out


def teachable_specs(language: str) -> Dict[str, Dict[str, Any]]:
    """The seed's teach-grammar rule specs, keyed by head — exactly what a
    self-teacher answers with on `render_gap:<head> in <language>` questions
    (the drain's `learn: [{rule: ...}]` shape). Rules without a `teach_spec`
    exceed `_spec_to_renderer_term`'s grammar (the measured statement-grain
    teach-loop boundary; see PROGRAM_SYNTHESIS_P5_RUST_LUA.md)."""
    out = {}
    for r in load_render_seed(language)["render_rules"]:
        if r.get("teachable"):
            out[r["head"]] = {"language": language, "head": r["head"],
                              "template": r["teach_spec"],
                              "binding_pattern": [b for b in r["binding_pattern"]
                                                  if b not in ("decl", "repeat",
                                                               "ipairs_k", "nf_start",
                                                               "nf_stop", "nf_step")]}
    return out


__all__ = ["install_renderer", "render_function", "render_body",
           "render_via_teach_loop", "load_render_seed", "teachable_specs",
           "prep_rust", "prep_lua"]

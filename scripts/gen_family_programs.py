#!/usr/bin/env python3
"""Emit seeds/family_programs.json (plan P4, 2026-10-10): the two variation
families that have produced production adoptions -- disposition_generalise
(tranche 22) and deep_reader_correct (tranche 23) -- as graph-held Programs.

Each is a Term the agent holds as data (a `FamilyProgram{name, program}` node,
the seeds/programs.json Program convention under its own type so the
improvement-integrity list can protect it) and the VariationOp names it as its
`builder_program` (seeds/variation_ops.json v1.6.0). It reads the concern's
context from the graph itself -- the live StandingConcern for the capability
key, the SelfConcern promoted to it, its turn, that turn's communication
interpretation, the held protected types, adoptable seeds and refuted trials --
and the held rule set from the evaluation environment, and returns the
variant (or an honest abstain) as a value. The rule edits are the P4
rule-edit Terms (runners/dsl/src/term.rs): EditAt (path-addressed set /
append / drop), CharRunSub + StripChars (the identifier slug), and LitRepr
(Python repr, now also of built strings).

Environment (written mechanically by reflective_faculty._compose_from_program):
  key        the concern's capability key (StandingConcern name)
  tag        the experiment tag
  rules      the active rules, export order, as exported
  seed_of    {rule name: seed id} -- each seed manifest's own declaration
  name_rank  {rule name: rank in name order} -- for "the first candidate by
             name"; string order is not a Term comparison (interned strings
             compare by interning order), so the host supplies the rank

Parameter sites (plan P5, operator authorship): each program opens with
Let-bound Lits (GENERALISE_PARAMS / DEEP_READER_PARAMS); their paths are the
FamilyProgram's `parameter_sites` attr, so a proposer
(domains/operator_authorship.py) sets one with the engine's EditAt. The
defaults are the held families exactly.

Parity with the Python builders (_compose_disposition_generalise /
_compose_deep_reader_correct) is gate F4: tests/test_family_programs_migrated.py
and the production shadow run (OZMA_FAMILY_PROGRAM_PARITY=1). Idempotent.
"""
import itertools
import json
from pathlib import Path

P = Path(__file__).resolve().parents[1] / "seeds/family_programs.json"
_ids = itertools.count()


def fresh(p):
    return f"_{p}{next(_ids)}"


def V(n): return {"type": "Var", "name": n}
def L(v): return {"type": "Lit", "value": v}
def A(node, k): return {"type": "Attr", "node": node, "key": k}
def DG(d, k): return {"type": "DictGet", "dict": d, "key": L(k) if isinstance(k, str) else k}
def Eq(a, b): return {"type": "Eq", "a": a, "b": b}
def Not(x): return {"type": "Not", "arg": x}
def And(*xs): return {"type": "And", "items": list(xs)}
def Or(*xs): return {"type": "Or", "items": list(xs)}
def Ite(c, t, o): return {"type": "IfThenElse", "cond": c, "then": t, "other": o}
def Let(n, v, b): return {"type": "Let", "name": n, "value": v, "body": b}
def Count(s): return {"type": "Count", "source": s}
def Gt(a, b): return {"type": "Gt", "a": a, "b": b}
def Gte(a, b): return {"type": "Gte", "a": a, "b": b}
def Minus(a, b): return {"type": "Minus", "a": a, "b": b}
def In(m, c): return {"type": "In", "member": m, "container": c}
def Filter(src, var, pred): return {"type": "Filter", "source": src, "var_name": var, "predicate": pred}
def FilterList(src, var, pred): return {"type": "FilterList", "source": src, "var_name": var, "predicate": pred}
def MapList(src, var, val): return {"type": "MapList", "source": src, "var_name": var, "value": val}
def MapSet(src, var, val): return {"type": "MapSet", "source": src, "var_name": var, "value": val}
def Exists(src, var, pred): return {"type": "Exists", "source": src, "var_name": var, "predicate": pred}
def Argmin(src, var, val): return {"type": "Argmin", "source": src, "var_name": var, "value": val, "default": None}
def Argmax(src, var, val): return {"type": "Argmax", "source": src, "var_name": var, "value": val, "default": None}
def Fold(src, var, acc, init, body):
    return {"type": "Fold", "source": src, "var_name": var, "acc_name": acc, "init": init, "body": body}
def IndexAt(s, i): return {"type": "IndexAt", "seq": s, "index": L(i) if isinstance(i, int) else i}
def Vec(*xs): return {"type": "Vec", "items": list(xs)}
def MkDict(*kv): return {"type": "MkDict", "items": [L(x) if isinstance(x, str) else x for x in kv]}
def Append(s, x): return {"type": "Append", "seq": s, "item": x}
def SC(*parts): return {"type": "StringConcat", "parts": [L(p) if isinstance(p, str) else p for p in parts]}
def Str(x): return {"type": "Str", "value": x}
def Repr(x): return {"type": "LitRepr", "value": x}
def ToJson(x): return {"type": "ToJsonString", "value": x}
def StrIdx(h, n): return {"type": "StringIndexOf", "haystack": h, "needle": n}
def Slice(s, a, b): return {"type": "StringSlice", "s": s, "start": a, "end": b}
def CaseFold(x): return {"type": "CaseFold", "text": x}
def Nodes(t): return {"type": "NodesOfType", "node_type": t}
def Nb(n, e): return {"type": "Neighbours", "node": n, "edge_type": e}
def InNb(n, e): return {"type": "InNeighbours", "node": n, "edge_type": e}
def ByName(n, k): return {"type": "AttrByName", "node": n, "name": k}
def Edit(tree, path, op, arg=None):
    return {"type": "EditAt", "tree": tree, "path": L(path) if isinstance(path, list) else path,
            "op": L(op), "arg": arg if arg is not None else L(None)}
def Slug(x):
    keep = "abcdefghijklmnopqrstuvwxyz0123456789"
    return {"type": "StripChars", "text": {"type": "CharRunSub", "text": x, "keep": L(keep), "repl": L("_")},
            "chars": L("_")}
def NN(x): return Not(Eq(x, L(None)))
def Wall(text): return MkDict("built", L(False), "wall", text if isinstance(text, dict) else L(text))


def build(obj):
    """A Python template -> the Term that constructs it (dict -> MkDict,
    list -> Vec; a Term marked {'__t__': term} is spliced in)."""
    if isinstance(obj, dict) and set(obj) == {"__t__"}:
        return obj["__t__"]
    if isinstance(obj, dict):
        items = []
        for k, v in obj.items():
            items += [L(k), build(v)]
        return {"type": "MkDict", "items": items}
    if isinstance(obj, list):
        return Vec(*[build(x) for x in obj])
    return L(obj)


def t(term): return {"__t__": term}


# --- shared concern context ---------------------------------------------------
KEY, TAG, RULES, SEED_OF, RANK = V("key"), V("tag"), V("rules"), V("seed_of"), V("name_rank")


def live_standing():
    named = Filter(Nodes("StandingConcern"), "s", Eq(A(V("s"), "name"), KEY))
    return Let("_named", named, Let("_live", Filter(V("_named"), "s", Not(Eq(A(V("s"), "status"), L("retired")))),
               Ite(Gt(Count(V("_live")), L(0)), Argmax(V("_live"), "x", V("x")),
                   Ite(Gt(Count(V("_named")), L(0)), Argmax(V("_named"), "x", V("x")), L(None)))))


def promoting_message(standing):
    sc = Argmin(Filter(Nodes("SelfConcern"), "c", In(standing, Nb(V("c"), "promoted_to"))), "x", V("x"))
    return Let("_sc", sc, Ite(Eq(V("_sc"), L(None)), L(None), Argmin(Nb(V("_sc"), "about_message"), "x", V("x"))))


def interpretation(msg):
    return Argmin(Filter(InNb(msg, "interprets"), "i",
                         Eq(A(V("i"), "schema"), L("communication_interpretation.v1"))), "x", V("x"))


PROTECTED = Let("_ii", Argmin(Nodes("ImprovementIntegrity"), "x", V("x")),
                Ite(Eq(V("_ii"), L(None)), L([]), A(V("_ii"), "protected_node_types")))
ADOPTABLE = MapSet(Filter(Nodes("SeedSummary"), "s", Eq(A(V("s"), "skippable"), L(1.0))), "s", A(V("s"), "seed_id"))


def protected(rule):
    """reflective_faculty._rule_names_protected_type: a '"Type"' token in the rule's JSON."""
    js, tv = fresh("js"), fresh("t")
    return Let(js, ToJson(rule), Exists(V("protected_types"), tv,
                                         Gte(StrIdx(V(js), SC('"', V(tv), '"')), L(0))))


MATCH_I = '[["agent","holds_interpretation","i"]]'


def match_i(rule): return Eq(ToJson(DG(rule, "match")), L(MATCH_I))


# --- _guards_on / _relax_guard as Terms ------------------------------------------
def items_of(where):
    return Ite(Eq(DG(where, "type"), L("And")), DG(where, "items"), Vec(where))


def inner(it): return Ite(Eq(DG(it, "type"), L("Not")), DG(it, "arg"), it)
def neg(it): return Eq(DG(it, "type"), L("Not"))


def shape_ok(it):
    n = fresh("n")
    return Let(n, inner(it), And(
        Eq(DG(V(n), "type"), L("Eq")), Eq(DG(DG(V(n), "a"), "type"), L("Attr")),
        Eq(DG(DG(DG(V(n), "a"), "node"), "type"), L("Var")), Eq(DG(DG(V(n), "b"), "type"), L("Lit"))))


def gvar(it): return DG(DG(DG(inner(it), "a"), "node"), "name")
def gkey(it): return DG(DG(inner(it), "a"), "key")
def gval(it): return DG(DG(inner(it), "b"), "value")


def guards_valid(where):
    it = fresh("it")
    return Not(Exists(items_of(where), it, Not(shape_ok(V(it)))))


def guards_i(where):
    it = fresh("it")
    return FilterList(items_of(where), it, Eq(gvar(V(it)), L("i")))


def has_guards(where):
    """_guards_on returned a non-empty list (not None, not [])."""
    return And(guards_valid(where), Gt(Count(guards_i(where)), L(0)))


def set_value(rule, key):
    """The last ["set_attr","i",key,v] effect's v (the Python dict-of-sets read)."""
    e, es = fresh("e"), fresh("es")
    return Let(es, FilterList(DG(rule, "effects"), e, And(
        Eq(Count(V(e)), L(4)), Eq(IndexAt(V(e), 0), L("set_attr")), Eq(IndexAt(V(e), 1), L("i")),
        Eq(IndexAt(V(e), 2), L(key)))),
        Ite(Gt(Count(V(es)), L(0)), IndexAt(IndexAt(V(es), -1), 3), L(None)))


def is_str(x): return And(NN(x), Eq(Str(x), x))


def lit_of(v): return MkDict("type", L("Lit"), "value", v)


def relax_item(it, key, value):
    n = fresh("n")
    match = And(Eq(DG(V(n), "type"), L("Eq")), Eq(DG(DG(V(n), "a"), "type"), L("Attr")),
                Eq(DG(DG(DG(V(n), "a"), "node"), "name"), L("i")), Eq(DG(DG(V(n), "a"), "key"), key))
    return Let(n, inner(it), Ite(match, Ite(neg(it), Edit(it, ["arg", "b"], "set", lit_of(value)),
                                             Edit(it, ["b"], "set", lit_of(value))), it))


def relax(rule, key, value):
    """reflective_faculty._relax_guard(rule, 'i', key, value)."""
    w, it = fresh("w"), fresh("it")
    return Let(w, DG(rule, "where"), Ite(
        Eq(DG(V(w), "type"), L("And")),
        Edit(rule, ["where", "items"], "set", MapList(DG(V(w), "items"), it, relax_item(V(it), key, value))),
        Edit(rule, ["where"], "set", relax_item(V(w), key, value))))


def drop_active(rule):
    d = fresh("d")
    return Let(d, Edit(rule, ["active"], "drop"), Ite(Eq(V(d), L(None)), rule, V(d)))


def set_field(rule, field, value): return Edit(rule, [field], "set", value)


def ends_with(s, suffix):
    n = len(suffix)
    return And(Gte(Count(s), L(n)), Eq(Slice(s, Minus(Count(s), L(n)), Count(s)), L(suffix)))


def concat_lists(head, tail):
    a, x = fresh("acc"), fresh("x")
    return Fold(tail, x, a, head, Append(V(a), V(x)))


# --- disposition_generalise --------------------------------------------------------
FIXED = ["schema", "evidence_schema", "evidence_force", "cognitive_disposition"]


ARBITRATION = Eq(V("p_source_role"), L("arbitration"))


def holds(it, interp):
    """_guard_holds on the turn's interpretation. An ARBITRATION source reads it
    as it stood before arbitration (no disposition yet); a REALISER source
    (P5 parameter site) reads it as arbitrated."""
    k, v, val, eq = fresh("k"), fresh("v"), fresh("val"), fresh("eq")
    return Let(k, gkey(it), Let(v, Ite(And(ARBITRATION, Eq(V(k), L("cognitive_disposition"))), L(None),
                                       ByName(interp, V(k))),
               Let(val, gval(it), Let(eq, Ite(Eq(V(val), L(None)), Eq(V(v), L(None)), Eq(V(v), V(val))),
                                       Ite(neg(it), Not(V(eq)), V(eq))))))


def misses(rule, interp):
    it = fresh("it")
    return FilterList(guards_i(DG(rule, "where")), it, Not(holds(V(it), interp)))


def realisers(basis):
    r2, g, e = fresh("r"), fresh("g"), fresh("e")
    return FilterList(RULES, r2, And(
        has_guards(DG(V(r2), "where")),
        Exists(guards_i(DG(V(r2), "where")), g, And(
            Eq(gkey(V(g)), L("arbitration_basis")), Eq(gval(V(g)), basis), Not(neg(V(g))))),
        Not(protected(V(r2))),
        Exists(DG(V(r2), "effects"), e, And(Eq(IndexAt(V(e), 0), L("add_node")), Eq(IndexAt(V(e), 1), L("reply"))))))


def tried(name):
    e, d = fresh("e"), fresh("d")
    return Exists(Nodes("Experiment"), e, And(
        Eq(A(V(e), "axis_tag"), KEY), In(A(V(e), "outcome"), L(["refuted", "inconclusive"])),
        Exists(Nb(V(e), "has_delta"), d, Eq(Str(Ite(Eq(A(V(d), "generalise_source_rule"), L(None)), L(""),
                                                    A(V(d), "generalise_source_rule"))), name))))


def misses_ok(m):
    """1 <= |misses| <= p_max_miss, none an identity key, none negated
    (p_max_miss = 1 is the tranche-22 'exactly one non-identity guard')."""
    x = fresh("x")
    return And(Gte(Count(m), L(1)), Gte(V("p_max_miss"), Count(m)),
               Not(Exists(m, x, Or(In(gkey(V(x)), L(FIXED)), neg(V(x))))))


def adds_reply(r):
    e = fresh("e")
    return Exists(DG(r, "effects"), e, And(Eq(IndexAt(V(e), 0), L("add_node")), Eq(IndexAt(V(e), 1), L("reply"))))


def generalise_candidate(r):
    m = fresh("m")
    name = DG(r, "name")
    return And(
        match_i(r),
        Ite(set_value(r, "cognitive_disposition"), L(True), L(False)),
        is_str(set_value(r, "arbitration_basis")),
        Not(tried(name)),
        Not(In(name, V("p_exclude_sources"))),
        Not(protected(r)),
        Or(In(DG(SEED_OF, name), V("adoptable")), ends_with(name, "_generalised")),
        has_guards(DG(r, "where")),
        Let(m, misses(r, V("interp")), misses_ok(V(m))),
        Gt(Count(realisers(set_value(r, "arbitration_basis"))), L(0)))


def realiser_candidate(r):
    """P5 source-role site: a held reply rule that realises the turn's OWN
    arbitration basis but misses the arbitrated turn on 1..p_max_miss guards."""
    m, g = fresh("m"), fresh("g")
    name = DG(r, "name")
    return And(
        adds_reply(r),
        has_guards(DG(r, "where")),
        Exists(guards_i(DG(r, "where")), g, And(
            Eq(gkey(V(g)), L("arbitration_basis")), Eq(gval(V(g)), A(V("interp"), "arbitration_basis")),
            Not(neg(V(g))))),
        Not(tried(name)),
        Not(In(name, V("p_exclude_sources"))),
        Not(protected(r)),
        Or(In(DG(SEED_OF, name), V("adoptable")), ends_with(name, "_generalised")),
        Let(m, misses(r, V("interp")), misses_ok(V(m))))


def slug_of(v):
    return Let("_s0", Slug(CaseFold(Str(v))), Ite(Eq(V("_s0"), L("")), L("none"), V("_s0")))


def over_misses(init, acc, body):
    """Fold over the source's misses ("mi"), binding mk / mv for each."""
    return Fold(V("src_misses"), "mi", acc, init,
                Let("mk", gkey(V("mi")), Let("mv", ByName(V("interp"), V("mk")), body)))


def joined(acc, part, sep):
    return Ite(Eq(V(acc), L("")), part, SC(V(acc), sep, part))


# "k1_slug1__k2_slug2" -- for one miss exactly the tranche-22 "<key>_<slug>"
TAGPART = over_misses(L(""), "tp", joined("tp", SC(V("mk"), "_", slug_of(V("mv"))), "__"))
RELAXED_TEXT = over_misses(L(""), "rt", joined("rt", SC("guard i.", V("mk"), " relaxed to ", Repr(V("mv"))), ", "))


def relax_all(rule, only_held=False):
    """Relax every miss key on `rule` (only those it guards, when only_held)."""
    g = fresh("g")
    step = relax(V("ra"), V("mk"), V("mv"))
    if only_held:
        step = Ite(Exists(guards_i(DG(rule, "where")), g, Eq(gkey(V(g)), V("mk"))), step, V("ra"))
    return over_misses(rule, "ra", step)


def generalise_build():
    src, nb = V("src"), V("new_basis")
    arb_effects = Append(MapList(DG(src, "effects"), "e", Ite(
        And(Eq(IndexAt(V("e"), 0), L("set_attr")), Eq(IndexAt(V("e"), 1), L("i")),
            Eq(IndexAt(V("e"), 2), L("arbitration_basis"))),
        Vec(L("set_attr"), L("i"), L("arbitration_basis"), nb), V("e"))),
        Vec(L("set_attr"), L("i"), L("receipt_selected_by_rule"), L("neutral_receipt")))
    arb = set_field(set_field(set_field(drop_active(relax_all(src)), "name",
                                        SC(DG(src, "name"), "__", V("tagpart"), "_generalised")),
                              "effects", arb_effects),
                    "comment", SC("disposition_generalise (tranche 22): ", DG(src, "name"), " with ",
                                  V("relaxed_text"), "; basis ", Repr(nb),
                                  ". Adopted only if the production replay supports it."))
    r = "rr"
    reply = Let("rr0", relax(V(r), L("arbitration_basis"), nb), Let(
        "rr1", relax_all(V("rr0"), only_held=True),
        set_field(drop_active(set_field(V("rr1"), "name", SC(DG(V(r), "name"), "__", V("tagpart"), "_generalised"))),
                  "comment", SC("disposition_generalise (tranche 22): ", DG(V(r), "name"), " keyed on basis ",
                                Repr(nb), "."))))
    replies = MapList(realisers(V("old_basis")), r, reply)
    x = fresh("x")
    return Let("arb", arb, Let("replies", replies, Ite(
        Eq(Count(V("replies")), L(0)),
        Wall(SC("no held reply rule realises basis ", Repr(V("old_basis")), " -- nothing to generalise")),
        Ite(Exists(RULES, x, Eq(DG(V(x), "name"), DG(V("arb"), "name"))),
            Wall(SC(DG(V("arb"), "name"), " is already held")),
            MkDict("built", L(True), "rules", concat_lists(Vec(V("arb")), V("replies")),
                   "source_rule", DG(src, "name"), "guard", V("mkey"), "new_value", V("new_value"),
                   "basis", nb)))))


def realiser_build():
    """P5 source-role 'realiser': copy the reply rule with its missed guards
    relaxed to the turn's values; the arbitration is untouched."""
    src, x = V("src"), fresh("x")
    variant = set_field(drop_active(set_field(relax_all(src), "name",
                                              SC(DG(src, "name"), "__", V("tagpart"), "_generalised"))),
                        "comment", SC("disposition_generalise, realiser source (P5): ", DG(src, "name"), " with ",
                                      V("relaxed_text"), ", for basis ", Repr(A(V("interp"), "arbitration_basis")),
                                      ". Adopted only if the production replay supports it."))
    return Let("variant", variant, Ite(
        Exists(RULES, x, Eq(DG(V(x), "name"), DG(V("variant"), "name"))),
        Wall(SC(DG(V("variant"), "name"), " is already held")),
        MkDict("built", L(True), "rules", Vec(V("variant")), "source_rule", DG(src, "name"),
               "guard", V("mkey"), "new_value", V("new_value"),
               "basis", A(V("interp"), "arbitration_basis"))))


# p_exclude_sources (P5b): source rules the family may not copy -- the
# refinement a proposer derives from its own meta-evaluation (sources whose
# deltas did net harm on the bank)
GENERALISE_PARAMS = (("p_max_miss", 1), ("p_source_role", "arbitration"), ("p_exclude_sources", []))
DEEP_READER_PARAMS = (("p_held_reply", "reply_to_deferred_response_assertion"), ("p_exclude_sources", []))


def with_params(params, body):
    """Parameter sites (P5): each a Let-bound Lit at the program's head, so a
    proposer can set it by path with EditAt; the defaults are the held family."""
    for name, default in reversed(params):
        body = Let(name, L(default), body)
    return body


def param_sites(term, params):
    """{param: {"path": [...], "default": v}} -- the path of each Let's value."""
    out = {}

    def walk(t, path):
        if isinstance(t, dict):
            if t.get("type") == "Let" and t.get("name") in dict(params) and t["name"] not in out:
                out[t["name"]] = {"path": path + ["value"], "default": dict(params)[t["name"]]}
            for k, v in t.items():
                walk(v, path + [k])
        elif isinstance(t, list):
            for i, v in enumerate(t):
                walk(v, path + [i])
    walk(term, [])
    assert set(out) == set(dict(params)), out
    return out


def generalise_program():
    c = fresh("c")
    cand = Ite(ARBITRATION, generalise_candidate(V(c)), realiser_candidate(V(c)))
    # MDL within the family: fewest relaxed guards first, then name order
    # (with p_max_miss = 1 every candidate misses once: exactly name order)
    order = {"type": "Plus", "items": [{"type": "Times", "items": [Count(misses(V("x"), V("interp"))), L(1000000)]},
                                       DG(RANK, DG(V("x"), "name"))]}
    picked = Let("src", Argmin(V("cands"), "x", order),
                 Let("src_misses", misses(V("src"), V("interp")),
                     Let("mkey", gkey(IndexAt(V("src_misses"), 0)),
                         Let("new_value", ByName(V("interp"), V("mkey")),
                             Let("tagpart", TAGPART, Let("relaxed_text", RELAXED_TEXT, Ite(
                                 ARBITRATION,
                                 Let("old_basis", set_value(V("src"), "arbitration_basis"),
                                     Let("new_basis", SC(V("old_basis"), "__", V("tagpart")), generalise_build())),
                                 realiser_build())))))))
    body = Let("cands", FilterList(RULES, c, cand), Ite(
        Eq(Count(V("cands")), L(0)),
        Ite(ARBITRATION,
            Wall("no held arbitration rule selects a disposition for this turn's evidence "
                 "with exactly one non-identity guard changed -- honest abstain"),
            Wall("no held reply rule realises this turn's basis within the allowed guard misses -- honest abstain")),
        picked))
    return with_params(GENERALISE_PARAMS, context(body, "the promoting concern names no unanswered turn",
                                                  "the unanswered turn carries no communication interpretation"))


def context(body, no_msg_wall, no_interp_wall, extra=None):
    """standing -> message -> interpretation, each an honest abstain when absent."""
    inner_body = body if extra is None else extra(body)
    return Let("standing", live_standing(), Ite(
        Eq(V("standing"), L(None)), Wall("no StandingConcern carries this capability key"),
        Let("msg", promoting_message(V("standing")), Ite(
            Eq(V("msg"), L(None)), Wall(no_msg_wall),
            Let("interp", interpretation(V("msg")), Ite(
                Eq(V("interp"), L(None)), Wall(no_interp_wall),
                Let("protected_types", PROTECTED, Let("adoptable", ADOPTABLE, inner_body))))))))


# --- deep_reader_correct ----------------------------------------------------------
def deep_reader_program():
    shallow, deep, fr, basis, tag = V("shallow"), V("deep"), V("first_role"), V("basis"), TAG

    def iattr(k): return {"type": "Attr", "node": {"type": "Var", "name": "i"}, "key": k}

    heard = build({"type": "And", "items": [
        {"type": "Eq", "a": iattr("literal_first_role"), "b": {"type": "Lit", "value": t(fr)}},
        {"type": "Exists", "source": {"type": "Neighbours", "node": {"type": "Var", "name": "i"},
                                      "edge_type": "interprets"},
         "var_name": "drm", "predicate": {"type": "And", "items": [
             {"type": "Eq", "a": {"type": "Attr", "node": {"type": "Var", "name": "drm"}, "key": "comp_kind"},
              "b": {"type": "Lit", "value": t(shallow)}},
             {"type": "Eq", "a": {"type": "Attr", "node": {"type": "Var", "name": "drm"}, "key": "shadow_speech_act"},
              "b": {"type": "Lit", "value": t(deep)}}]}}]})
    variant = set_field(set_field(set_field(drop_active(V("arb")), "name", SC(DG(V("arb"), "name"), "_deepread_", tag)),
                                  "where", build({"type": "And", "items": [t(DG(V("arb"), "where")),
                                                                            {"type": "Not", "arg": t(heard)}]})),
                        "comment", SC("deep_reader_correct (tranche 23): ", DG(V("arb"), "name"),
                                      ", except when the deep reader heard ", Repr(deep),
                                      " where the shallow reader classified ", Repr(shallow), "."))
    nb = V("new_basis")
    receipt_arb = build({
        "name": t(SC("arbitrate_deep_reader_", V("slug"), "_receipt_", tag)),
        "comment": t(SC("deep_reader_correct (tranche 23): a turn the shallow reader classified ", Repr(shallow),
                        " and the deep reader heard ", Repr(deep), " gets the neutral, non-endorsing receipt.")),
        "match": [["agent", "holds_interpretation", "i"]],
        "where": {"type": "And", "items": [
            {"type": "Eq", "a": iattr("schema"), "b": {"type": "Lit", "value": "communication_interpretation.v1"}},
            {"type": "Eq", "a": iattr("cognitive_disposition"), "b": {"type": "Lit", "value": None}},
            {"type": "Eq", "a": iattr("communicative_force"), "b": {"type": "Lit", "value": None}},
            t(heard)]},
        "effects": [["set_attr", "i", "communicative_force", "assertion_or_correction"],
                    ["set_attr", "i", "cognitive_disposition", "defer"],
                    ["set_attr", "i", "cognitive_goal", "update_common_ground"],
                    ["set_attr", "i", "arbitration_basis", t(nb)],
                    ["set_attr", "i", "receipt_selected_by_rule", "neutral_receipt"]]})
    flag = V("flag")
    e = fresh("e")
    kept = FilterList(DG(V("held_reply"), "effects"), e,
                      Not(And(Eq(IndexAt(V(e), 0), L("set_attr")), Eq(IndexAt(V(e), 1), L("m")))))
    receipt_reply = build({
        "name": t(SC("reply_deep_reader_", V("slug"), "_receipt_", tag)),
        "comment": "deep_reader_correct (tranche 23): realises the receipt with the held response-assertion receipt's effects.",
        "match": [["agent", "holds_interpretation", "i"], ["i", "interprets", "m"]],
        "where": {"type": "And", "items": [
            {"type": "Eq", "a": iattr("arbitration_basis"), "b": {"type": "Lit", "value": t(nb)}},
            {"type": "Not", "arg": {"type": "Eq", "a": {"type": "Attr", "node": {"type": "Var", "name": "m"},
                                                        "key": t(flag)},
                                    "b": {"type": "Lit", "value": 1}}}]},
        "effects": t(concat_lists(Vec(Vec(L("set_attr"), L("m"), flag, L(1))), kept))})
    x, ee = fresh("x"), fresh("e")
    arb_pick = FilterList(RULES, x, And(match_i(V(x)), Not(In(DG(V(x), "name"), V("p_exclude_sources"))),
                                        Exists(DG(V(x), "effects"), ee, And(
        Eq(Count(V(ee)), L(4)), Eq(IndexAt(V(ee), 0), L("set_attr")), Eq(IndexAt(V(ee), 1), L("i")),
        Eq(IndexAt(V(ee), 2), L("arbitration_basis")), Eq(IndexAt(V(ee), 3), basis)))))
    y, z = fresh("y"), fresh("z")
    body = Let("basis", A(V("interp"), "arbitration_basis"), Let("first_role", A(V("interp"), "literal_first_role"), Ite(
        Not(Ite(fr, L(True), L(False))),
        Wall("the concern's turn carries no literal_first_role to scope the correction"),
        Let("_arbs", arb_pick, Ite(
            Eq(Count(V("_arbs")), L(0)),
            Wall(SC("no held arbitration rule writes the turn's basis ", Repr(basis))),
            Let("arb", IndexAt(V("_arbs"), 0), Ite(
                Or(protected(V("arb")), Not(In(DG(SEED_OF, DG(V("arb"), "name")), V("adoptable")))),
                Wall(SC(Repr(DG(V("arb"), "name")), " is not an adoptable rule")),
                Let("_hr", FilterList(RULES, y, Eq(DG(V(y), "name"), V("p_held_reply"))), Ite(
                    Eq(Count(V("_hr")), L(0)),
                    Wall("no held neutral-receipt reply rule to realise the correction"),
                    Let("held_reply", IndexAt(V("_hr"), 0),
                        Let("slug", Slug(SC(Str(shallow), "_as_", Str(deep), "_", Str(fr))),
                            Let("new_basis", SC("deep_reader_", V("slug"), "_receipt"),
                                Let("flag", SC("deep_reader_receipt_minted_", tag),
                                    Let("variant", variant, Let("receipt_arb", receipt_arb, Ite(
                                        Exists(RULES, z, In(DG(V(z), "name"),
                                                            Vec(DG(V("variant"), "name"), DG(V("receipt_arb"), "name")))),
                                        Wall("this correction is already held"),
                                        MkDict("built", L(True), "removed_rule", DG(V("arb"), "name"),
                                               "rules", Vec(V("variant"), V("receipt_arb"), receipt_reply),
                                               "shallow", shallow, "deep", deep, "basis", nb)))))))))))))))))

    def with_readers(b):
        return Let("shallow", A(V("msg"), "comp_kind"), Let("deep", A(V("msg"), "shadow_speech_act"), Ite(
            Or(Not(Ite(shallow, L(True), L(False))), Not(Ite(deep, L(True), L(False))), Eq(shallow, deep)),
            Wall("the concern's turn carries no shallow/deep reader disagreement"), b)))

    # the reader disagreement is checked before the interpretation exists (Python order)
    return with_params(DEEP_READER_PARAMS, Let("standing", live_standing(), Ite(
        Eq(V("standing"), L(None)), Wall("no StandingConcern carries this capability key"),
        Let("msg", promoting_message(V("standing")), Ite(
            Eq(V("msg"), L(None)), Wall("the promoting concern names no turn"),
            with_readers(Let("interp", interpretation(V("msg")), Ite(
                Eq(V("interp"), L(None)), Wall("the turn carries no communication interpretation"),
                Let("protected_types", PROTECTED, Let("adoptable", ADOPTABLE, body))))))))))


PROGRAMS = {
    "family_disposition_generalise": (generalise_program(), GENERALISE_PARAMS,
        "disposition_generalise (tranche 22) as a held Program: copy a held arbitration rule that misses the "
        "unanswered turn on exactly one non-identity guard, relax that guard, re-key its reply rules. "
        "Parameter sites (P5): p_max_miss (guards relaxed at most), p_source_role ('arbitration' | 'realiser': "
        "relax the arbitration rule, or the reply rule that realises the turn's own basis)."),
    "family_deep_reader_correct": (deep_reader_program(), DEEP_READER_PARAMS,
        "deep_reader_correct (tranche 23) as a held Program: let the deep reader veto the arbitration that misread "
        "the concern's turn, and answer that disagreement with the neutral receipt. Parameter site (P5): "
        "p_held_reply (the held reply rule whose effects realise the receipt)."),
}

seed = {
    "id": "family_programs",
    "version": "1.2.0",
    "depends_on": [],
    "description": __doc__,
    "nodes": [{"local_id": k, "type": "FamilyProgram", "attrs": {
        "name": name, "program": json.dumps(term, separators=(",", ":")), "description": desc,
        "parameter_sites": json.dumps(param_sites(term, params), separators=(",", ":")),
        "kind": "variation_family_builder"}}
        for k, (name, (term, params, desc)) in enumerate(PROGRAMS.items())],
    "edges": [],
    "productions": [],
    "rules": [],
}
P.write_text(json.dumps(seed, indent=1, ensure_ascii=True) + "\n")
print("family_programs", seed["version"], {n: (len(json.dumps(t_)), param_sites(t_, p_))
                                           for n, (t_, p_, _d) in PROGRAMS.items()})

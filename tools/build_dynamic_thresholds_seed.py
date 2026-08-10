"""Seed authoring tool (deletable; not agent runtime — CLAUDE.md's tools/*
carve-out): extends seeds/reading_aperture.json for the DYNAMIC-THRESHOLDS +
REOPEN + REFORM wave.

  1. Extends every ApertureBudget row with the reading-layer threshold fields
     (trace_capacity_*, max_revisits, max_order_*, widen_step, widen_salience_
     threshold, reform_*_threshold, reform_pressure_factor) — held, per-
     register, revisable data (never a Python literal).
  2. Adds TWO held Program (Term-tree) derivations the Rust engine evaluates
     (native.evaluate): `reading_derive_trace_capacity` and `reading_derive_
     max_order` — editing either Program node changes the derived value with
     ZERO code changes (domains/reading_norms.py only reads/evaluates).
  3. Adds TWO rules: `reading_widen_capacity_once` (the ladder's rung 1 — a
     flow whose ring evicts a high-salience trace widens its capacity ONCE,
     per its own held budget) and `reform_overcomplex_clause` (rung 2 — a
     SentenceParse whose own residual-marker-count/swallowed-ratio measurement
     crosses the held threshold, TIGHTENED once the flow's widen is already
     spent, is marked reform_pending; the mechanical shim in reading_drive.py
     executes read_clause_order_n and marks reform_done).

Run once: `python3 tools/build_dynamic_thresholds_seed.py`. Idempotent by
field/rule NAME (re-running overwrites the same fields/rules, never
duplicates)."""
import json
import os

P = os.path.join(os.path.dirname(__file__), "..", "seeds", "reading_aperture.json")
d = json.load(open(P))

# --------------------------------------------------------------------------- #
#  1. EXTEND every ApertureBudget row.
# --------------------------------------------------------------------------- #
_TIGHT = {  # conversational: bounded chat-turn ring, per the directive's
            # "keep chat turns bounded" constraint.
    "trace_capacity_base": 4.0, "trace_capacity_min": 2.0, "trace_capacity_max": 6.0,
    "max_revisits": 4.0,
    "max_order_base": 2.0, "max_order_max": 3.0,
    "widen_step": 2.0, "widen_salience_threshold": 0.5,
    "reform_eviction_threshold": 2.0, "reform_residual_threshold": 1.0,
    "reform_swallowed_threshold": 0.5, "reform_pressure_factor": 0.5,
}
_GENEROUS = {  # document/narrative registers: matches the PRE-WAVE Python
               # literal defaults exactly (read_scope max_revisits=8,
               # read_paragraph trace_capacity=8, read_clause_order_n
               # max_order=2) so a register whose row already existed keeps
               # byte-identical baseline behaviour; only widen/reform headroom
               # is new.
    "trace_capacity_base": 8.0, "trace_capacity_min": 4.0, "trace_capacity_max": 16.0,
    "max_revisits": 8.0,
    "max_order_base": 2.0, "max_order_max": 4.0,
    "widen_step": 4.0, "widen_salience_threshold": 0.5,
    "reform_eviction_threshold": 3.0, "reform_residual_threshold": 1.0,
    "reform_swallowed_threshold": 0.5, "reform_pressure_factor": 0.5,
}
_TIGHT_REGISTERS = {"conversational", "casual"}

n_budgets = 0
for node in d["nodes"]:
    if node["type"] != "ApertureBudget":
        continue
    reg = node["attrs"].get("register")
    fields = dict(_TIGHT if reg in _TIGHT_REGISTERS else _GENEROUS)
    node["attrs"].update(fields)
    n_budgets += 1

# --------------------------------------------------------------------------- #
#  2. Term-tree helpers.
# --------------------------------------------------------------------------- #
A = lambda n, k: {"type": "Attr", "node": {"type": "Var", "name": n}, "key": k}
V = lambda n: {"type": "Var", "name": n}
Lc = lambda v: {"type": "Lit", "value": v}
Eq = lambda a, b: {"type": "Eq", "a": a, "b": b}
Gte = lambda a, b: {"type": "Gte", "a": a, "b": b}
And = lambda items: {"type": "And", "items": items}
Or = lambda items: {"type": "Or", "items": items}
Not = lambda arg: {"type": "Not", "arg": arg}
IfTE = lambda cond, then, other: {"type": "IfThenElse", "cond": cond, "then": then, "other": other}
Let = lambda name, value, body: {"type": "Let", "name": name, "value": value, "body": body}
Filter = lambda source, var, pred: {"type": "Filter", "source": source, "var_name": var, "predicate": pred}
NodesOfType = lambda t: {"type": "NodesOfType", "node_type": t}
Argmax = lambda source, var, value, default=None: {"type": "Argmax", "source": source, "var_name": var,
                                                     "value": value, "default": default}
Plus = lambda items: {"type": "Plus", "items": items}
Times = lambda items: {"type": "Times", "items": items}
Min = lambda items: {"type": "Min", "items": items}
Max = lambda items: {"type": "Max", "items": items}

# the shared "this flow's own register's ApertureBudget" lookup (mirrors the
# existing escalate_* rules' `budget` Let exactly).
def budget_let(body):
    return Let("budget",
               Argmax(Filter(NodesOfType("ApertureBudget"), "b", Eq(A("b", "register"), A("goal", "register"))),
                       "x", Lc(0), default=None),
               And([Not(Eq(V("budget"), Lc(None))), body]))

# --------------------------------------------------------------------------- #
#  3. Two held Program derivations.
# --------------------------------------------------------------------------- #
capacity_program = {
    "name": "reading_derive_trace_capacity",
    "form": "term_tree",
    "program": json.dumps(Min([
        Max([Plus([V("base"), IfTE(Eq(V("widened"), Lc(1.0)), V("widen_step"), Lc(0.0))]),
             V("min_cap")]),
        V("max_cap"),
    ])),
}
max_order_program = {
    "name": "reading_derive_max_order",
    "form": "term_tree",
    "program": json.dumps(Min([
        Plus([V("base"), IfTE(Gte(V("reform_count"), Lc(1.0)), Lc(1.0), Lc(0.0))]),
        V("max_cap"),
    ])),
}

existing_program_names = {n["attrs"].get("name") for n in d["nodes"] if n["type"] == "Program"}
next_local_id = max((n["local_id"] for n in d["nodes"]), default=0) + 1
for prog in (capacity_program, max_order_program):
    if prog["name"] in existing_program_names:
        for node in d["nodes"]:
            if node["type"] == "Program" and node["attrs"].get("name") == prog["name"]:
                node["attrs"] = dict(prog)
        continue
    d["nodes"].append({"local_id": next_local_id, "type": "Program", "attrs": dict(prog)})
    next_local_id += 1

# --------------------------------------------------------------------------- #
#  4. Two rules: widen-once (ladder rung 1), reform (ladder rung 2).
# --------------------------------------------------------------------------- #
widen_rule = {
    "name": "reading_widen_capacity_once",
    "comment": ("DYNAMIC-THRESHOLDS ladder rung 1 (2026-07-11): a flow whose ring "
                "buffer (reading_scope.enforce_trace_buffer, called per-commit from "
                "coref_entities.read_into_situation_model) just evicted a trace whose "
                "salience reached this flow's own ApertureBudget.widen_salience_"
                "threshold (held, per-register, revisable) widens its effective trace "
                "capacity ONCE (capacity_widened=1 on the flow's Source — read by "
                "domains/reading_norms.effective_trace_capacity's held Program). "
                "Mint-once (the capacity_widened existence guard) — this is the WHOLE "
                "ladder's rung 1; rung 2 (reform_overcomplex_clause below) TIGHTENS "
                "instead of widening again once this has fired, per the directive's "
                "'widen once -> reform' ladder."),
    "match": [["goal", "reads_source", "src"]],
    "where": And([
        Not(Eq(A("src", "capacity_widened"), Lc(1.0))),
        Not(Eq(A("src", "max_evicted_salience"), Lc(None))),
        budget_let(Gte(A("src", "max_evicted_salience"), A("budget", "widen_salience_threshold"))),
    ]),
    "effects": [["set_attr", "src", "capacity_widened", 1.0]],
}

reform_rule = {
    "name": "reform_overcomplex_clause",
    "comment": ("DYNAMIC-THRESHOLDS ladder rung 2 / REFORM (2026-07-11): 'if a "
                "concept is too complex, the human approach is to take it and reform "
                "your own understanding into component shapes' — a SentenceParse whose "
                "own MEASUREMENTS (residual_marker_count — unconsumed order-1 structural "
                "markers; swallowed_ratio — reading_scope.swallowed_ratio, the fraction "
                "of argument roles that swallow a predication; both stamped mechanically "
                "at spine-mint time, domains/reading_drive._mint_sentence_parses) cross "
                "this flow's own ApertureBudget.reform_*_threshold (held, per-register) "
                "is marked reform_pending — the mechanical shim (reading_drive._shim_"
                "monitoring) then executes reading_collapse.read_clause_order_n and "
                "records the decomposed part_of/marker component predications back onto "
                "this SentenceParse, marking reform_done. A SIMPLE clause (both "
                "measurements 0, the common case) never crosses either threshold and "
                "never fires. Once the flow has ALREADY spent its rung-1 widen "
                "(src.capacity_widened=1), the effective threshold is TIGHTENED by the "
                "held reform_pressure_factor (e.g. 0.5 — half the bar) rather than "
                "widening the ring further: 'widen once -> reform' — sustained overflow "
                "pressure makes the SAME flow more willing to decompose, it never forces "
                "a genuinely simple (0/0) clause into reform."),
    "match": [["sp", "is_sentence_parse", "sp"], ["goal", "reads_source", "src"]],
    "where": And([
        Eq(A("sp", "flow"), A("src", "flow")),
        Not(Eq(A("sp", "reform_pending"), Lc(1.0))),
        Not(Eq(A("sp", "reform_done"), Lc(1.0))),
        budget_let(
            Let("factor",
                IfTE(Eq(A("src", "capacity_widened"), Lc(1.0)), A("budget", "reform_pressure_factor"), Lc(1.0)),
                Or([
                    Gte(A("sp", "residual_marker_count"), Times([A("budget", "reform_residual_threshold"), V("factor")])),
                    Gte(A("sp", "swallowed_ratio"), Times([A("budget", "reform_swallowed_threshold"), V("factor")])),
                ]))),
    ]),
    "effects": [
        ["set_attr", "sp", "reform_pending", 1.0],
        ["set_attr", "sp", "reform_reason", {"__term__": IfTE(
            {"type": "Gt", "a": A("sp", "residual_marker_count"), "b": Lc(0.0)},
            Lc("residual_markers"), Lc("swallowed_predication"))}],
    ],
}

existing_rule_names = {r["name"] for r in d["rules"]}
d["rules"] = [r for r in d["rules"] if r["name"] not in (widen_rule["name"], reform_rule["name"])]
d["rules"].append(widen_rule)
d["rules"].append(reform_rule)

json.dump(d, open(P, "w"), indent=2)
print(f"ok: {n_budgets} ApertureBudget rows extended; "
      f"{len(existing_program_names & {'reading_derive_trace_capacity','reading_derive_max_order'})} "
      f"program(s) updated in place, rest added; rules now {[r['name'] for r in d['rules']]}")

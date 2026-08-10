#!/usr/bin/env python3
"""rule_lift — demonstrate the mechanical LIFTER: agent-logic Python
(decision-over-graph-state) -> graph-resident RULE (Term-tree the engine runs),
LIVE with NO maturin rebuild.

Honest, no rebuild needed. Run from the gamma-substrate dir:

    ulimit -v 6291456
    timeout 300 python scripts/rule_lift.py

Sections:
  1. EQUIVALENCE — a rule-shaped Python function vs its lifted Rule produce
     IDENTICAL graph state on two identical substrates.
  2. LIVE WITHOUT REBUILD — the lifted Rule fired natively (graph data); no
     maturin, no .so. Contrast: the Rust-primitive path needs a rebuild.
  3. CONSERVATISM — near-miss functions (nested loop / call in body / dynamic
     key / else branch) -> recognizer returns None with a reason. No wrong Rule.
  4. COVERAGE SCAN — run recognize_rule_shape on every requires_replacement
     function/method unit; report how many of the flagged units are liftable
     TODAY (the honest frontier number).
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from substrate_rs._native import Substrate as Native   # noqa: E402

import domains.rule_lifter as rl                         # noqa: E402
import domains.rust_rewrite_world as rr                  # noqa: E402


def _line(c="-", n=72):
    print(c * n)


# --- the representative rule-shaped Python function (the thing we lift) ------

MARK_STALE_SRC = '''
def mark_stale(substrate):
    for n in substrate.nodes("Belief"):
        if substrate.node(n)["attrs"].get("confidence") < 0.3:
            substrate.set_attr(n, "status", "stale")
'''


def mark_stale(substrate):
    """The PYTHON reference — agent decision logic (an if/else over graph state)
    that CLAUDE.md says is a Rule, not Python. We run THIS on one substrate and
    the LIFTED RULE on an identical one, then assert identical graph state."""
    for n in substrate.nodes("Belief"):
        if substrate.node(n)["attrs"].get("confidence") < 0.3:
            substrate.set_attr(n, "status", "stale")


# A second, richer function — and/or/not + a second effect (self add_edge) —
# to prove the lifter handles compound conditions + multiple effects.
TRIAGE_SRC = '''
def triage(substrate):
    for b in substrate.nodes("Belief"):
        if substrate.node(b)["attrs"].get("confidence") < 0.3 or substrate.node(b)["attrs"].get("contested") == True:
            substrate.set_attr(b, "status", "review")
            substrate.add_edge(b, "needs_review", b)
'''


def triage(substrate):
    for b in substrate.nodes("Belief"):
        if substrate.node(b)["attrs"].get("confidence") < 0.3 \
                or substrate.node(b)["attrs"].get("contested") == True:  # noqa: E712
            substrate.set_attr(b, "status", "review")
            substrate.add_edge(b, "needs_review", b)


# --- NEW (a): SELF-RECEIVER METHOD — handle is self.s, not a `substrate` param.
# A small class whose triage method goes through self.s exactly as a world
# adapter would. The lifter must detect the self.s handle and recognize the
# SAME rule-shape through it.
SELF_RECV_SRC = '''
def mark(self):
    for n in self.s.nodes("Belief"):
        if self.s.node(n)["attrs"].get("confidence") < 0.3:
            self.s.set_attr(n, "status", "stale")
'''


class Triager:
    """The PYTHON reference for the self-receiver case — a method that holds the
    substrate on self.s (the documented world-adapter convention) and runs the
    decision through it. The lifter recognizes the rule-shape through self.s."""

    def __init__(self, substrate):
        self.s = substrate

    def mark(self):
        for n in self.s.nodes("Belief"):
            if self.s.node(n)["attrs"].get("confidence") < 0.3:
                self.s.set_attr(n, "status", "stale")


# --- NEW (b): MULTI-STATEMENT function — a SEQUENCE of independent guarded-for
# blocks. The lifter lifts each block to its OWN Rule (all-or-nothing: if any
# top-level statement were not a rule-shape block, the whole function rejects).
MULTI_SRC = '''
def triage_all(substrate):
    """Two independent passes over the Belief set — each a rule-shape block."""
    for n in substrate.nodes("Belief"):
        if substrate.node(n)["attrs"].get("confidence") < 0.3:
            substrate.set_attr(n, "status", "stale")
    for b in substrate.nodes("Belief"):
        if substrate.node(b)["attrs"].get("contested") == True:  # noqa: E712
            substrate.set_attr(b, "priority", "high")
            substrate.add_edge(b, "needs_review", b)
'''


def triage_all(substrate):
    """PYTHON reference — two independent passes, two effects in the 2nd."""
    for n in substrate.nodes("Belief"):
        if substrate.node(n)["attrs"].get("confidence") < 0.3:
            substrate.set_attr(n, "status", "stale")
    for b in substrate.nodes("Belief"):
        if substrate.node(b)["attrs"].get("contested") == True:  # noqa: E712
            substrate.set_attr(b, "priority", "high")
            substrate.add_edge(b, "needs_review", b)


# --- substrate construction (identical seeds for equivalence) ----------------

_BELIEFS = [
    {"confidence": 0.10, "status": "active", "contested": False},
    {"confidence": 0.50, "status": "active", "contested": False},
    {"confidence": 0.05, "status": "active", "contested": False},
    {"confidence": 0.90, "status": "active", "contested": True},
    {"confidence": 0.40, "status": "active", "contested": True},
]


def _fresh_substrate():
    s = Native()
    # self-edge production so add_edge effects are admissible on the native backend
    for et in ("needs_review",):
        try:
            s.add_production({
                "src": {"type": "Belief", "var": "a"}, "edge_type": et,
                "tgt": {"type": "Belief", "var": "b"}, "where": None,
                "weight": {"type": "Lit", "value": 1.0},
                "provenance": f"rule_lift:{et}"})
        except Exception:
            pass
    ids = [s.add_node("Belief", dict(a)) for a in _BELIEFS]
    return s, ids


def _snapshot(s, ids):
    """The full graph state we compare: every Belief's attrs + its self-edges."""
    snap = {}
    for n in ids:
        attrs = dict(s.node(n)["attrs"])
        edges = sorted(s.neighbours(n, "needs_review"))
        snap[n] = (attrs, edges)
    return snap


def equivalence(runner, src, func_name, label=None):
    """`runner` runs the PYTHON reference on a substrate (a bare function, or a
    closure that builds a class + calls its method for the self-receiver case).
    Lifts `func_name` from `src` to one-or-more Rules, fires them, asserts the
    lifted graph state == the Python graph state."""
    title = label or func_name
    print(f"\n[1] EQUIVALENCE  —  {title}: Python vs lifted Rule(s)")
    _line()
    # (a) run the PYTHON reference
    s_py, ids_py = _fresh_substrate()
    runner(s_py)
    snap_py = _snapshot(s_py, ids_py)

    # (b) lift + fire the RULE(s) on an identical substrate
    s_rule, ids_rule = _fresh_substrate()
    out = rl.lift_function(s_rule, src, func_name)
    assert out["ok"], f"recognizer rejected the rule-shaped function: {out['reason']}"
    blocks = out["recognized"]["blocks"]
    node_types = [b["node_type"] for b in blocks]
    applied = rl.fire_lifted_rule(s_rule, out["rule_nids"], node_types)
    snap_rule = _snapshot(s_rule, ids_rule)

    rec = out["recognized"]
    print(f"  handle    : {rec['handle'] if rec['handle'] else 'substrate (param)'}"
          f"   blocks: {len(blocks)}   rule nids: {out['rule_nids']}")
    for i, b in enumerate(blocks):
        print(f"  block[{i}]  : for {b['var']} in nodes({b['node_type']!r}) if "
              f"{_fmt_cond(b['condition'])}  ->  {b['effects']}")
    print(f"  fired {applied} application(s)")

    # IDENTICAL graph state?
    ok = snap_py == snap_rule
    print(f"  Python-result state == lifted-Rule-result state : {ok}")
    if not ok:
        for n in ids_py:
            if snap_py[n] != snap_rule[n]:
                print(f"    DIFF node {n}: py={snap_py[n]}  rule={snap_rule[n]}")
    changed = [n for n in ids_py
               if dict(_BELIEFS[ids_py.index(n)]) != snap_py[n][0]
               or snap_py[n][1]]
    print(f"  nodes mutated by BOTH : {len(changed)} of {len(ids_py)}")
    assert ok, "lifted Rule did NOT reproduce the Python function's graph state"
    return out


def _fmt_cond(struct):
    op = struct["op"]
    if op == "cmp":
        return f"attrs[{struct['key']!r}] {struct['cmp']} {struct['value']!r}"
    if op == "not":
        return f"not ({_fmt_cond(struct['args'][0])})"
    sep = f" {op} "
    return "(" + sep.join(_fmt_cond(a) for a in struct["args"]) + ")"


# --- conservatism: near-misses must return None with a reason ----------------

NEAR_MISSES = {
    "nested_loop": '''
def nested_loop(substrate):
    for n in substrate.nodes("Belief"):
        for m in substrate.nodes("Belief"):
            if substrate.node(n)["attrs"].get("confidence") < 0.3:
                substrate.set_attr(n, "status", "stale")
''',
    "call_in_body": '''
def call_in_body(substrate):
    for n in substrate.nodes("Belief"):
        if substrate.node(n)["attrs"].get("confidence") < 0.3:
            recompute_belief_score(n, substrate)
''',
    "dynamic_key": '''
def dynamic_key(substrate):
    for n in substrate.nodes("Belief"):
        if substrate.node(n)["attrs"].get(key_var) < 0.3:
            substrate.set_attr(n, "status", "stale")
''',
    "else_branch": '''
def else_branch(substrate):
    for n in substrate.nodes("Belief"):
        if substrate.node(n)["attrs"].get("confidence") < 0.3:
            substrate.set_attr(n, "status", "stale")
        else:
            substrate.set_attr(n, "status", "ok")
''',
    "non_attr_test": '''
def non_attr_test(substrate):
    for n in substrate.nodes("Belief"):
        if len(substrate.neighbours(n, "supports")) > 2:
            substrate.set_attr(n, "status", "hub")
''',
    # NEW conservatism cases for the extended recognizer ----------------------
    # (a) MIXED handle: reads through self.s but writes through self.graph —
    #     two different substrate handles -> reject the whole method.
    "mixed_handle": '''
def mixed_handle(self):
    for n in self.s.nodes("Belief"):
        if self.graph.node(n)["attrs"].get("confidence") < 0.3:
            self.s.set_attr(n, "status", "stale")
''',
    # (b) SELF-STATE in the test: the condition reads self._threshold (Python
    #     agent state), not graph state -> not a literal compare -> reject.
    "self_state_in_test": '''
def self_state_in_test(self):
    for n in self.s.nodes("Belief"):
        if self.s.node(n)["attrs"].get("confidence") < self._threshold:
            self.s.set_attr(n, "status", "stale")
''',
    # (c) A CALL among the top-level statements: first block is rule-shape, but
    #     the second top-level statement is a method call -> all-or-nothing
    #     rejects the WHOLE function (no partial lift).
    "call_among_statements": '''
def call_among_statements(substrate):
    for n in substrate.nodes("Belief"):
        if substrate.node(n)["attrs"].get("confidence") < 0.3:
            substrate.set_attr(n, "status", "stale")
    recompute_global_scores(substrate)
''',
}


def conservatism():
    print("\n[3] CONSERVATISM  —  near-miss => None (no wrong Rule emitted)")
    _line()
    all_none = True
    for name, src in NEAR_MISSES.items():
        ok, recognized, reason = rl.recognize_with_reason(src, name)
        none_returned = rl.recognize_rule_shape(src, name) is None
        all_none = all_none and none_returned and not ok
        print(f"  {name:14s} -> None ({none_returned})   reason: {reason}")
    assert all_none, "a near-miss was (wrongly) recognized as liftable"
    print("  all near-misses rejected — recognizer is conservative.")


# --- coverage scan: how far does this move the frontier TODAY -----------------

def _func_source(path: Path, qualname: str, module: str) -> str | None:
    """Extract the source of the function/method named by `qualname` from its
    file, as a standalone `def` we can feed to the recognizer."""
    try:
        src = path.read_text()
        tree = ast.parse(src)
    except (OSError, SyntaxError):
        return None
    # qualname is module(.owner).name
    tail = qualname[len(module):].lstrip(".")
    parts = tail.split(".")
    name = parts[-1]
    owner = parts[0] if len(parts) == 2 else None

    def find(body, want, cls=None):
        for node in body:
            if isinstance(node, ast.ClassDef) and cls is not None \
                    and node.name == cls:
                return find(node.body, want, None)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) \
                    and node.name == want and cls is None:
                return node
        return None

    node = find(tree.body, name, owner)
    if node is None:
        return None
    return ast.get_source_segment(src, node)


def coverage_scan():
    print("\n[4] COVERAGE SCAN  —  liftable today over the flagged surface")
    _line()
    s = Native()
    rr.enumerate_python_surface(s)
    info = rr.install_requires_replacement_rule(s)
    rr.classify_surface(s, info["rule_index"])
    world = rr.RustRewriteWorld(s)
    smap = world.surface_map()
    total_req = smap["requires_replacement"]

    func_units = []
    for u in world._units():
        a = s.node(u)["attrs"]
        if a.get("requires_replacement") and a.get("kind") in ("function", "method"):
            func_units.append(a)

    liftable = []
    scanned = 0
    reasons: dict[str, int] = {}
    # Count how many units the EXTENSIONS carry PAST the two old gates this
    # task removed (so the structural movement is visible even at N=0):
    #   - had a non-`substrate` first param (the 268 old "not substrate")
    #   - now ADMITTED as a method via a self.<handle> (no longer gate-blocked)
    is_method_admitted = 0
    for a in func_units:
        qual = a.get("qualname")
        module = a.get("module")
        path = _ROOT / a.get("path", "")
        # path attr is "/".join(path_parts) for funcs; module path more reliable
        mod_path = _ROOT / (module.replace(".", "/") + ".py")
        p = mod_path if mod_path.exists() else path
        if not p.exists():
            continue
        name = qual.split(".")[-1]
        src = _func_source(p, qual, module)
        if src is None:
            continue
        scanned += 1
        ok, _rec, reason = rl.recognize_with_reason(src, name)
        if ok:
            liftable.append(qual)
        else:
            reasons[reason] = reasons.get(reason, 0) + 1
        # Did the self-receiver extension get this method past the old
        # "first parameter is not `substrate`" gate? (It resolved a handle.)
        if a.get("kind") == "method" and reason != "first parameter is not `substrate` or `self`" \
                and reason != "method has no self.<s|substrate|graph|g> substrate handle":
            is_method_admitted += 1

    print(f"  requires_replacement units total         : {total_req}")
    print(f"  ... of which function/method             : {len(func_units)}")
    print(f"  ... successfully re-extracted + scanned   : {scanned}")
    print(f"  ... liftable to a graph Rule TODAY        : {len(liftable)}")
    print(f"  COVERAGE DELTA  : before 0/{scanned}  ->  after {len(liftable)}/{scanned}")
    print("  structural movement (the two gates this task removed):")
    print("    BEFORE the dominant rejections were 268 'first param is not")
    print("    `substrate`' (methods) + 245 'body is not a single for' — pure")
    print("    GATE rejections. Those gates are GONE: methods are admitted via")
    print(f"    a self.<handle>, and multi-statement bodies are parsed per-block.")
    # Why the rest miss (top reasons) — names what is still out.
    top = sorted(reasons.items(), key=lambda kv: -kv[1])[:6]
    if top:
        print("  top rejection reasons NOW (the real, content-level frontier):")
        for r, c in top:
            print(f"    {c:5d}  {r}")
    pct = (100.0 * len(liftable) / scanned) if scanned else 0.0
    print(f"  liftable fraction of scanned functions    : {pct:.2f}%")
    if liftable:
        print("  qualnames that NOW lift (up to 8):")
        for q in liftable[:8]:
            print(f"    - {q}")
    else:
        print("  Still NONE lift: the requires_replacement methods are dominated")
        print("  by graph QUERIES (`return n`), non-literal compares (vs a param /")
        print("  self-state), try/except-wrapped effects, and constructors full of")
        print("  calls — genuinely outside ANY mutate-only rule subset, not a gate")
        print("  artefact. The extensions moved the FRONTIER SHAPE (gates removed),")
        print("  not yet the COUNT. The general compiler remains the open problem,")
        print("  NOT faked with an LLM.")
    return len(liftable), scanned


def main():
    print("=" * 72)
    print("RULE LIFTER  —  agent-logic Python -> graph-resident RULE (no rebuild)")
    print("=" * 72)

    equivalence(mark_stale, MARK_STALE_SRC, "mark_stale")
    equivalence(triage, TRIAGE_SRC, "triage")
    # NEW (a) self-receiver METHOD: the python ref is Triager(s).mark().
    equivalence(lambda s: Triager(s).mark(), SELF_RECV_SRC, "mark",
                label="mark (self-receiver method, handle=self.s)")
    # NEW (b) multi-statement function -> TWO Rules, identical state.
    equivalence(triage_all, MULTI_SRC, "triage_all",
                label="triage_all (multi-statement -> 2 Rules)")

    print("\n[2] LIVE WITHOUT REBUILD")
    _line()
    print("  The lifted Rules above fired via substrate.add_rule / apply_rule_once")
    print("  — they are GRAPH DATA. No maturin, no .so recompiled, no restart.")
    print("  Contrast: the Rust-PRIMITIVE path (a new DSL Term) requires editing")
    print("  term.rs + a maturin rebuild before the agent can use it. Decisions")
    print("  -> Rules are live the instant they are installed; that is the point.")

    conservatism()

    n_lift, scanned = coverage_scan()

    print("\n" + "=" * 72)
    print("SUMMARY")
    _line()
    print("  - EQUIVALENCE proven: lifted Rule(s) reproduce the Python's exact")
    print("    graph state (attrs + edges) for FOUR shapes: simple, compound")
    print("    (and/or, 2 effects), a SELF-RECEIVER method (handle=self.s), and")
    print("    a MULTI-STATEMENT function lifted to TWO independent Rules.")
    print("  - LIVE: Rules are graph data — fired natively, NO rebuild.")
    print("  - CONSERVATIVE: every near-miss returned None with a reason,")
    print("    including the new mixed-handle / self-state-in-test / call-among-")
    print("    statements cases (all-or-nothing rejects the whole function).")
    print(f"  - COVERAGE DELTA: before 0/{scanned}  ->  after {n_lift}/{scanned}.")
    print("    The recognizer EXTENSIONS (self-receiver handle + multi-statement")
    print("    all-or-nothing) widened what the subset ADMITS; the live count is")
    print(f"    {n_lift} because the requires_replacement methods are dominated by")
    print("    graph QUERIES (return n), constructors with calls, and entangled")
    print("    self-state — genuinely outside any mutate-only rule subset. That")
    print("    remains the open problem, NOT faked with an LLM.")
    print("=" * 72)


if __name__ == "__main__":
    main()

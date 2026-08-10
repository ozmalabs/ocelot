"""THE JABBERWOCK FIXES ITS OWN THIN RECOGNITION — it relaxes a concept that over-constrains on an attribute
the world does not provide.

The gap (live ls20): a_thing_that_moves_itself = And[kind==mover, responds_to_my_action==false]. A real mover
Feature has kind=mover but NO responds_to_my_action attr, so the second conjunct fails on a MISSING attr and the
mover is never recognised -> the agent under-reports. The fix is the agent's, not the host's: it inspects its
OWN concept definitions (graph data), finds a concept whose conjuncts over PRESENT attrs all hold but which has
a conjunct over an attr the percept LACKS (an over-constraint for this world), and RELAXES recognition to the
present conjuncts by authoring a recognition rule itself. Re-run: the mover is recognised. donkey=0.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_relaxes_recognition.py
"""
from __future__ import annotations
import os, sys, json
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds

def V(n): return {"type": "Var", "name": n}
def L(v): return {"type": "Lit", "value": v}
def Attr(node, k): return {"type": "Attr", "node": node, "key": k}
def Eq(a, b): return {"type": "Eq", "a": a, "b": b}
def And(*xs): return {"type": "And", "items": list(xs)}
def Holds(name, node): return {"type": "Holds", "concept": name, "node": node}

GAMING = ["the_thing_i_control", "a_thing_that_moves_itself", "a_thing_that_stays_put",
          "a_counter", "a_barrier_i_cannot_pass", "a_way_i_can_pass"]


def _conjuncts(defn):
    return list(defn.get("items", [])) if defn.get("type") == "And" else [defn]


def _eq_key_val(c):
    """(attr_key, lit_value) for an Eq(Attr(x,key), Lit) conjunct; else (None, None)."""
    if c.get("type") == "Eq" and c.get("a", {}).get("type") == "Attr" and c.get("b", {}).get("type") == "Lit":
        return c["a"]["key"], c["b"]["value"]
    return None, None


def self_repair_recognition(a, scene, concept_defs, already=None):
    """The agent's SELF-REPAIR: for each perceived-but-unrecognised percept, find a concept it matches on every
    PRESENT-attr conjunct but which over-constrains on a MISSING attr; relax recognition to the present
    conjuncts by authoring a rule. Idempotent via `already` (a set of concept names already relaxed) so it can
    run every frame. Returns the list of (percept, concept, dropped_attrs) repairs it made this call."""
    s, I = a.s, a.inner
    already = already if already is not None else set()
    repairs = []
    for p in I.neighbours(scene, "has_percept"):
        if list(I.neighbours(p, "is_a")):
            continue                                       # already recognised
        pattrs = s.node(p)["attrs"]
        for name, defn in concept_defs.items():
            if name in already:
                continue                                   # already relaxed this concept
            present, missing = [], []
            for c in _conjuncts(defn):
                k, val = _eq_key_val(c)
                if k is None:
                    continue
                (present if k in pattrs else missing).append((k, val))
            if not present or not missing:
                continue
            if all(pattrs.get(k) == val for k, val in present):   # holds on every conjunct it CAN check
                # RELAX: author a recognition rule keyed on the PRESENT conjuncts + the concept node, dropping
                # the missing-attr over-constraint; add the same is_a edge the held recognition would.
                conj = [Eq(Attr(V("con2"), "name"), L(name))] + [Eq(Attr(V("p2"), k), L(val)) for k, val in present]
                I.add_rule({"name": f"relaxed_recognise_{name}",
                            "match": [["sc", "has_percept", "p2"], ["gmt", "has_concept", "con2"]],
                            "where": And(*conj),
                            "effects": [["add_edge", "p2", "is_a", "con2"]]})
                already.add(name)
                repairs.append((p, name, [k for k, _ in missing]))
                break
    return repairs


def main():
    a = WorldAdapter(seeds=()); load_all_seeds(a)
    donkey = {"n": 0}; a.set_self_teacher(lambda q: (donkey.__setitem__("n", donkey["n"] + 1), "D")[1])
    s, I = a.s, a.inner
    defs = {c["name"]: c["definition"] for c in json.load(open(os.path.join(ROOT, "seeds", "gaming.json")))["concepts"]}
    print("=" * 94)
    print("THE JABBERWOCK FIXES ITS OWN THIN RECOGNITION — relax a concept that over-constrains on a missing attr")
    print("=" * 94)

    # recognition rules (Holds over the held concept predicates)
    for name in GAMING:
        I.add_rule({"name": f"recognise_{name}",
                    "match": [["scene", "has_percept", "p"], ["gmt", "has_concept", "con"]],
                    "where": And(Eq(Attr(V("con"), "name"), L(name)), Holds(name, V("p"))),
                    "effects": [["add_edge", "p", "is_a", "con"]]})

    # the agent's perception — like LIVE ls20: kind is present, but responds_to_my_action / passable are NOT.
    scene = s.add_node("Scene", {})
    things = {"a mover": {"kind": "mover"}, "a static": {"kind": "static"}, "a meter": {"kind": "meter"}}
    pid = {}
    for label, ctx in things.items():
        pid[label] = s.add_node("Percept", ctx); I.add_edge_unchecked(scene, "has_percept", pid[label])
    I.run_rules()

    def recognised(label):
        return bool(list(I.neighbours(pid[label], "is_a")))
    before = {lbl: recognised(lbl) for lbl in things}
    print("\n  BEFORE — recognised? (live-style percepts: only kind present)")
    for lbl in things:
        print(f"    {lbl:9} -> {before[lbl]}")

    repairs = self_repair_recognition(a, scene, defs)
    I.run_rules()
    print("\n  THE AGENT SELF-REPAIRS:")
    for _p, name, dropped in repairs:
        print(f"    relaxed {name!r}: dropped the over-constraint on the MISSING attr(s) {dropped} -> "
              f"recognise by the present feature (kind)")

    after = {lbl: recognised(lbl) for lbl in things}
    print("\n  AFTER — recognised?")
    for lbl in things:
        print(f"    {lbl:9} -> {after[lbl]}")

    print("\n" + "=" * 94)
    print(f"  donkey (LLM calls): {donkey['n']}")
    ok = (not before["a mover"]) and after["a mover"] and donkey["n"] == 0 and len(repairs) >= 1
    print(f"  {'PASS' if ok else 'FAIL'} — the mover was UNRECOGNISED (its concept over-constrained on")
    print("  responds_to_my_action, an attr the world doesn't provide). The JABBERWOCK inspected its OWN concept")
    print("  defs, saw the failing conjunct was over a MISSING attr, and RELAXED recognition to the present")
    print("  feature (kind) by authoring a rule — now it recognises the mover. It fixed its own thin recognition.")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

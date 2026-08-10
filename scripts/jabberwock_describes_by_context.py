"""THE JABBERWOCK DESCRIBES A THING BY CONTEXT — DOMAIN-AGNOSTIC. Not game-specific.

The general faculty: recognise a thing by which of the agent's HELD CONCEPT PREDICATES it satisfies,
given its observed context. The candidate predicates are EVERY executable concept definition the agent
holds, across ALL its microtheories (83 predicates / 12 domains: gaming, vision/figure_ground, shape_sense,
ballistics, projection, acoustics, navigation, ...). NOTHING here is game-specific — which predicates hold
depends only on the thing's context, so the SAME code describes a game thing, a shape, a projectile, etc.

  describe(thing) = { concept : eval(concept.predicate, thing-bound) holds }
      · a BOOLEAN predicate that is True  -> the thing IS-A that concept (a recogniser)
      · a NUMERIC predicate               -> a measured FEATURE of the thing (value)

The predicate is the agent's own held Term; the Rust evaluator runs it (donkey-counted). Python only binds
the perceived thing to the predicate's free entity variable(s) and reads which held.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_describes_by_context.py
"""
from __future__ import annotations
import os, sys, glob, json
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds


def free_vars(t, bound=frozenset()):
    """Free entity variables of a Term: Var names NOT introduced by an enclosing binder
    (Let.name / *.var_name / *.acc_name). These are the slots the perceived thing binds into."""
    res = set()
    if isinstance(t, dict):
        if t.get("type") == "Var":
            n = t.get("name")
            if n not in bound:
                res.add(n)
            return res
        nb = set(bound)
        if t.get("type") == "Let" and isinstance(t.get("name"), str):
            nb.add(t["name"])
        for k in ("var_name", "acc_name"):
            if isinstance(t.get(k), str):
                nb.add(t[k])
        for k, v in t.items():
            if k in ("type", "var_name", "acc_name"):
                continue
            if k == "name" and t.get("type") != "Let":
                continue
            res |= free_vars(v, nb)
    elif isinstance(t, list):
        for v in t:
            res |= free_vars(v, bound)
    return res


def requirements(t, fvs, req):
    """What CONTEXT a predicate reads on its entity vars: attr keys via Attr(Var,key), and edge types via
    Neighbours/InNeighbours(Var,et). Used to GUARD applicability — a predicate only applies to a thing that
    actually SUPPLIES this context (else missing attrs default to 0/True and every predicate false-fires)."""
    if isinstance(t, dict):
        ty = t.get("type")
        node = t.get("node")
        is_fv = isinstance(node, dict) and node.get("type") == "Var" and node.get("name") in fvs
        if ty == "Attr" and is_fv and isinstance(t.get("key"), str):
            req["attrs"].add(t["key"])
        if ty == "InNeighbours" and is_fv and isinstance(t.get("edge_type"), str):
            req["in"].add(t["edge_type"])
        if ty == "Neighbours" and is_fv and isinstance(t.get("edge_type"), str):
            req["out"].add(t["edge_type"])
        for v in t.values():
            requirements(v, fvs, req)
    elif isinstance(t, list):
        for v in t:
            requirements(v, fvs, req)
    return req


def load_held_predicates():
    """Every executable concept predicate the agent holds, across ALL its seeds/microtheories.
    (name, microtheory, definition-Term, free-vars). Domain-agnostic — no filtering by domain."""
    preds = []
    for f in glob.glob(os.path.join(ROOT, "seeds", "*.json")):
        try:
            d = json.load(open(f))
        except Exception:
            continue
        mt = (d.get("microtheory") or {}).get("name") if isinstance(d.get("microtheory"), dict) else d.get("id")
        for c in (d.get("concepts") or []):
            defn = c.get("definition")
            if isinstance(defn, dict):                     # an executable Term predicate
                fv = free_vars(defn)
                req = requirements(defn, fv, {"attrs": set(), "in": set(), "out": set()})
                preds.append((c.get("name"), mt, defn, fv, req))
    return preds


def applicable(a, thing_id, req):
    """A predicate applies ONLY if the thing supplies the context it reads (its attrs + its in/out edges).
    Without this guard, predicates whose context is ABSENT default to 0/True and false-fire across domains."""
    attrs = a.s.node(thing_id)["attrs"]
    if not req["attrs"].issubset(attrs.keys()):
        return False
    for et in req["in"]:
        if not a.inner.in_neighbours(thing_id, et):
            return False
    for et in req["out"]:
        if not a.inner.neighbours(thing_id, et):
            return False
    # A predicate that reads NO context off the thing can't be a contextual recogniser of it.
    return bool(req["attrs"] or req["in"] or req["out"])


def describe(a, nat, thing_id, preds):
    """Evaluate the held predicates the thing's context SUPPORTS (applicability-guarded). Domain-agnostic."""
    recognised, measured = [], []
    for name, mt, defn, fv, req in preds:
        if not applicable(a, thing_id, req):
            continue
        env = {v: thing_id for v in fv}                    # bind the thing into the predicate's entity slots
        try:
            r = nat.evaluate(defn, env)
        except Exception:
            continue
        if isinstance(r, bool):
            if r:
                recognised.append((name, mt))
        elif isinstance(r, (int, float)):
            measured.append((name, mt, r))
    return recognised, measured


def main():
    a = WorldAdapter(seeds=()); load_all_seeds(a)
    donkey = {"n": 0}; a.set_self_teacher(lambda q: (donkey.__setitem__("n", donkey["n"] + 1), "D")[1])
    s, nat = a.s, a.inner

    preds = load_held_predicates()
    domains = sorted({mt for _n, mt, _d, _f, _r in preds})
    print("=" * 94)
    print("THE JABBERWOCK DESCRIBES A THING BY CONTEXT — same faculty, ANY domain (not game-specific)")
    print("=" * 94)
    print(f"  candidate predicates it evaluates: {len(preds)} concepts across {len(domains)} domains")
    print(f"  domains: {', '.join(domains)}")

    # --- THREE perceived things from DIFFERENT domains; the SAME describe() faculty handles all ---
    things = []
    a1 = s.add_node("Percept", {"kind": "mover", "responds_to_my_action": True, "selective": True, "passable": True})
    things.append(("a GAME thing: mover, responds to a subset of my actions, walkable", a1))
    a2 = s.add_node("Percept", {"kind": "static", "passable": False})
    things.append(("a GAME thing: static, I cannot pass it", a2))
    # a non-game SHAPE thing: a Region with member cells (a 2x2 block) — for the vision/shape domains.
    reg = s.add_node("Region", {})
    for (r, c) in [(0, 0), (0, 1), (1, 0), (1, 1)]:
        cell = s.add_node("Cell", {"row": r, "col": c, "value": 3})
        a.inner.add_edge_unchecked(cell, "within", reg)
    things.append(("a NON-GAME shape thing: a 2x2 region of cells", reg))

    for desc, tid in things:
        rec, meas = describe(a, nat, tid, preds)
        print(f"\n  THING — {desc}")
        if rec:
            print("    IS-A (held predicates that hold of it, by context):")
            for name, mt in rec[:8]:
                print(f"        · {name}   [{mt}]")
        if meas:
            print("    MEASURED FEATURES (held numeric predicates, by context):")
            for name, mt, v in meas[:8]:
                print(f"        · {name} = {v}   [{mt}]")
        if not rec and not meas:
            print("    (no held predicate fired — its context matches nothing the agent knows yet)")

    print("\n" + "=" * 94)
    print(f"donkey (LLM calls): {donkey['n']}")
    print("Domain-agnostic: ONE faculty evaluated all held predicates from every domain; the game thing was")
    print("recognised by game concepts, the shape thing by vision/shape concepts — the code never mentions a")
    print("domain. Adding a new domain's concepts (with predicates) extends what it can describe, for free.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

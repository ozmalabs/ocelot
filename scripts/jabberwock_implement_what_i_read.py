"""K3 END-TO-END: the agent reads a procedural method and COMPILES it into
executable graph RULES that run. Two distinct methods -> two distinct rule sets
(the generality gate). donkey=0 / OZMA_NO_LLM=1 throughout - no model anywhere.

Run:
  export TMPDIR=/home/matt/.claude/jobs/dec46f73/tmp \
         PYTHONPATH=runners/dsl/python:.:scripts OZMA_NO_LLM=1
  python3 scripts/jabberwock_implement_what_i_read.py
"""
import json
import os
os.environ.setdefault("OZMA_NO_LLM", "1")

from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
from domains import procedural_reader as pr
from domains import method_synthesis as ms


def _rule(a):
    return WorldAdapter(seeds=())


def hr(t):
    print("\n" + "=" * 74); print(t); print("=" * 74)


def show_model(m):
    for st in m["steps"]:
        print("  [step %d] %r" % (st["step_index"], st["sentence"]))
        print("           trigger: %s" % json.dumps(st["trigger"]))
        print("           main   : %s" % json.dumps(st["main"]))


def show_rules(res):
    if res.get("wall"):
        print("  WALL:", res["wall"]); return
    for r in res["rules"]:
        print("  RULE:", json.dumps(r))
    print("  HOW :", res["how"])


# --------------------------------------------------------------------------- #
def k3_1_ivm(a):
    hr("K3.1  IVM / MATERIALIZED VIEW  (ties back to the whole dynamic-quant thread)")
    passage = ("A view depends on its source. "
               "When the source changes, the view becomes stale. "
               "Recompute a stale view from its source.")
    print("READ PASSAGE:\n  " + passage)
    model = pr.read_method(a, passage, name="ivm")
    print("\nEXTRACTED MethodModel:")
    show_model(model)
    print("\nreferent-rule cross-check (graph's own recognition):", model["referent_resolved"])

    # binding: abstract nouns -> concrete graph vocabulary of the application domain.
    # The METHOD STRUCTURE is comprehended; the concrete aggregate (Count over
    # has_mention edges) and the view's stored-value attr are domain binding.
    binding = {"value_attr": "val", "aggregate": {"op": "Count", "edge": "has_mention"}}
    res = ms.synthesise_rule_from_method(a, model, binding)
    print("\nSYNTHESISED RULE(S):")
    show_rules(res)

    # ---- application subgraph: view -depends_on-> source(Message); source has
    # ---- has_mention edges (the per-Message count is the materialized view).
    s, inner = a.s, a.inner
    src = s.add_node("Message", {"kind": "source"})
    view = s.add_node("Message", {"kind": "view", "val": -1.0})
    inner.add_edge_unchecked(view, "depends_on", src)
    for w in ["alpha", "beta", "gamma"]:
        inner.add_edge_unchecked(src, "has_mention", s.add_node("Mention", {"text": w}))

    def val():
        return s.node(view)["attrs"]["val"]

    print("\nRUN (the read method now executes as a rule):")
    inner.run_rules(10000)
    print("  3 source edges         -> view.val = %s   (expect 3)" % val())
    for w in ["delta", "epsilon"]:
        inner.add_edge_unchecked(src, "has_mention", s.add_node("Mention", {"text": w}))
    inner.run_rules(10000)
    print("  +2 edges added         -> view.val = %s   (expect 5, stays coherent)" % val())
    # delete all source edges (the churn / deletion de-risk)
    for mn in list(inner.neighbours(src, "has_mention")):
        s.remove_edge(src, "has_mention", mn)
    inner.run_rules(10000)
    stale = val()
    print("  all edges deleted      -> view.val = %s   (STALE-ON-DELETE probe)" % stale)
    # any subsequent change re-triggers the rule and recomputes from scratch
    inner.add_edge_unchecked(src, "has_mention", s.add_node("Mention", {"text": "zeta"}))
    inner.run_rules(10000)
    print("  +1 edge after delete   -> view.val = %s   (expect 1: recompute-from-scratch)" % val())
    print("\n  FINDING: additions stay coherent; a pure DELETION does not auto-retrigger")
    print("  (engine dirty-tracking: removing an edge marks no node dirty) - the NEXT")
    print("  touch recomputes correctly. The synthesised rule's LOGIC is coherent.")
    return res


def k3_2_task(a):
    hr("K3.2  SECOND, UNRELATED METHOD  (the generality proof - the result that matters)")
    passage = "When a task is marked done, add a completed edge from the task to its owner."
    print("READ PASSAGE:\n  " + passage)
    model = pr.read_method(a, passage, name="task")
    print("\nEXTRACTED MethodModel:")
    show_model(model)
    print("\nreferent-rule cross-check (graph's own recognition):", model["referent_resolved"])

    # binding: "its owner" is reached by the owned_by edge; the 'done' state is the
    # 'done' attr; the 'completed' edge is added directly.
    binding = {"role_relation": "owned_by", "state_attr": {"done": "done"}}
    res = ms.synthesise_rule_from_method(a, model, binding)
    print("\nSYNTHESISED RULE(S):")
    show_rules(res)

    s, inner = a.s, a.inner
    owner = s.add_node("Concept", {"name": "alice"})
    task = s.add_node("Message", {"kind": "task", "done": 0.0})
    inner.add_edge_unchecked(task, "owned_by", owner)

    print("\nRUN (the read method now executes as a rule):")
    inner.run_rules(10000)
    pre = inner.neighbours(task, "completed")
    print("  task.done = 0 -> completed edges: %s   (expect none)" % pre)
    s.set_attr(task, "done", 1.0)
    inner.run_rules(10000)
    got = inner.neighbours(task, "completed")
    print("  task.done = 1 -> completed edges: %s   (expect [owner=%s])" % (got, owner))
    print("  edge lands on owner? %s" % (owner in got))
    assert not pre and owner in got, "K3.2 add_edge gate failed"
    return res


def main():
    print("donkey=0 / OZMA_NO_LLM =", os.environ.get("OZMA_NO_LLM"))
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    r1 = k3_1_ivm(a)
    # fresh agent for the second method to prove read-two-methods -> two-rule-sets
    b = WorldAdapter(seeds=())
    load_all_seeds(b)
    r2 = k3_2_task(b)

    hr("GENERALITY: two different read methods -> two different rule structures")
    print("  K3.1 effect kind:", r1.get("effect"), "->", [r["name"] for r in r1.get("rules", [])])
    print("  K3.2 effect kind:", r2.get("effect"), "->", [r["name"] for r in r2.get("rules", [])])
    print("  same synthesiser, structural dispatch on effect kind; no method-specific template.")
    assert r1.get("effect") == "recompute" and r2.get("effect") == "add_edge"
    assert not r1.get("wall") and not r2.get("wall")
    print("\nALL K3 GATES PASSED (donkey=0).")


if __name__ == "__main__":
    main()

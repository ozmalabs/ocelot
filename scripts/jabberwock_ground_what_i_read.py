"""SELF-GROUNDING "implement what I read": the agent reads a full description
(DEFINITION + MAINTENANCE method), GROUNDS the binding itself from the read text
+ the domain graph (NOTHING hand-supplied), synthesises a running RewriteRule,
installs it, and produces the described effect. donkey=0 / OZMA_NO_LLM=1.

Contrast with scripts/jabberwock_implement_what_i_read.py, where the binding
(aggregate function+edge, value attr, ownership relation, state attr) was passed
by hand. Here derive_binding (domains/binding_resolver.py) resolves every piece.

Run:
  export TMPDIR=/home/matt/.claude/jobs/dec46f73/tmp \
         PYTHONPATH=runners/dsl/python:.:scripts OZMA_NO_LLM=1
  python3 scripts/jabberwock_ground_what_i_read.py
"""
import json
import os
os.environ.setdefault("OZMA_NO_LLM", "1")

from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
from domains import procedural_reader as pr
from domains import method_synthesis as ms
from domains import binding_resolver as br


def hr(t):
    print("\n" + "=" * 74); print(t); print("=" * 74)


def show_model(m):
    for st in m["steps"]:
        print("  [step %d] %r" % (st["step_index"], st["sentence"]))
        print("           trigger: %s" % json.dumps(st["trigger"]))
        print("           main   : %s" % json.dumps(st["main"]))


def show_binding(d):
    print("\nGROUNDED BINDING (nothing hand-supplied):")
    print("  binding = %s" % json.dumps(d["binding"]))
    print("  HOW each piece grounded:")
    for line in d["provenance"]:
        print("    - " + line)
    if d["underspecified"]:
        print("  UNDERSPECIFIED: %s" % d["underspecified"])


def show_rules(res):
    if res.get("wall"):
        print("  WALL:", res["wall"]); return
    for r in res["rules"]:
        print("  RULE:", json.dumps(r))
    print("  HOW :", res["how"])


# --------------------------------------------------------------------------- #
def k_ivm(a):
    hr("IVM / MATERIALIZED VIEW - grounded from a DEFINITION + a MAINTENANCE method")
    # build the application subgraph FIRST (derive_binding grounds against it).
    s, inner = a.s, a.inner
    src = s.add_node("Message", {"kind": "source"})
    view = s.add_node("Message", {"kind": "view", "val": -1.0})
    inner.add_edge_unchecked(view, "depends_on", src)
    for w in ["alpha", "beta", "gamma"]:
        inner.add_edge_unchecked(src, "has_mention", s.add_node("Mention", {"text": w}))

    passage = ("A view holds the count of its source's mentions. "
               "A view depends on its source. "
               "When the source changes, the view becomes stale. "
               "Recompute a stale view from its source.")
    print("READ PASSAGE (definition + method):\n  " + passage)
    model = pr.read_method(a, passage, name="ivm")
    print("\nEXTRACTED MethodModel:")
    show_model(model)
    print("\nreferent-rule cross-check:", model["referent_resolved"])

    grounded = br.derive_binding(a, model)
    show_binding(grounded)

    res = ms.synthesise_rule_from_method(a, model, grounded["binding"])
    print("\nSYNTHESISED RULE(S):")
    show_rules(res)

    def val():
        return s.node(view)["attrs"]["val"]

    print("\nRUN (the read method now executes as a rule):")
    inner.run_rules(10000)
    print("  3 source edges  -> view.val = %s   (expect 3)" % val())
    for w in ["delta", "epsilon"]:
        inner.add_edge_unchecked(src, "has_mention", s.add_node("Mention", {"text": w}))
    inner.run_rules(10000)
    print("  +2 edges added  -> view.val = %s   (expect 5)" % val())
    for mn in list(inner.neighbours(src, "has_mention")):
        s.remove_edge(src, "has_mention", mn)
    inner.add_edge_unchecked(src, "has_mention", s.add_node("Mention", {"text": "zeta"}))
    inner.run_rules(10000)
    print("  reset to 1 edge -> view.val = %s   (expect 1)" % val())
    ok = abs(val() - 1.0) < 1e-9
    print("  COHERENT: %s" % ok)
    return res, grounded, ok


def k_task(a):
    hr("TASK-DONE - grounded possessive relation ('its owner') + trigger state")
    s, inner = a.s, a.inner
    owner = s.add_node("Concept", {"name": "alice"})
    task = s.add_node("Message", {"kind": "task", "done": 0.0})
    inner.add_edge_unchecked(task, "owned_by", owner)

    passage = "When a task is marked done, add a completed edge from the task to its owner."
    print("READ PASSAGE:\n  " + passage)
    model = pr.read_method(a, passage, name="task")
    print("\nEXTRACTED MethodModel:")
    show_model(model)
    print("\nreferent-rule cross-check:", model["referent_resolved"])

    grounded = br.derive_binding(a, model)
    show_binding(grounded)

    res = ms.synthesise_rule_from_method(a, model, grounded["binding"])
    print("\nSYNTHESISED RULE(S):")
    show_rules(res)

    print("\nRUN (the read method now executes as a rule):")
    inner.run_rules(10000)
    pre = inner.neighbours(task, "completed")
    print("  task.done = 0 -> completed edges: %s   (expect none)" % pre)
    s.set_attr(task, "done", 1.0)
    inner.run_rules(10000)
    got = inner.neighbours(task, "completed")
    print("  task.done = 1 -> completed edges: %s   (expect [owner=%s])" % (got, owner))
    ok = (not pre) and (owner in got)
    print("  edge lands on owner: %s" % ok)
    return res, grounded, ok


def main():
    print("donkey=0 / OZMA_NO_LLM =", os.environ.get("OZMA_NO_LLM"))
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    r1, g1, ok1 = k_ivm(a)
    b = WorldAdapter(seeds=())
    load_all_seeds(b)
    r2, g2, ok2 = k_task(b)

    hr("SUMMARY")
    print("  IVM     : binding=%s  coherent=%s  underspecified=%s"
          % (json.dumps(g1["binding"]), ok1, g1["underspecified"]))
    print("  task    : binding=%s  landed=%s  underspecified=%s"
          % (json.dumps(g2["binding"]), ok2, g2["underspecified"]))
    print("  both methods synthesised + ran with NOTHING hand-supplied to the binding.")


if __name__ == "__main__":
    main()

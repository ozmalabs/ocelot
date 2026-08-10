"""SEMANTIC grounding of the read-noun <-> domain-edge link (scratch proof).

Pushes derive_binding past the LEXICAL (character-overlap) bridge: when the
domain names its edges with SEMANTICALLY-RIGHT but LEXICALLY-DIFFERENT words
(ownership = `belongs_to`, mention = `cites`/`references`), the role noun grounds
to the right edge BY MEANING, using the agent's OWN offline WordNet faculty
(donkey=0 / OZMA_NO_LLM=1 — no LLM teacher). The DECISION stays a mechanical
Argmax over a grounded-relatedness count; character overlap remains the fast-path
for rhyming names.

Four cases, each behind a check:
  * renamed-task   : ownership edge `belongs_to` (not owned_by) -> owner grounds
                     semantically -> completed edge lands on owner.
  * renamed-IVM    : mention edge `cites` (not has_mention) -> mentions grounds
                     semantically -> the view recomputes coherently.
  * DISTRACTOR     : a semantically-wrong `created_by` sits alongside the right
                     edge; the Argmax must pick the ownership/mention one.
  * NEGATIVE       : an opaque `rel_42` ownership edge is ungroundable -> DECLINE
                     (underspecified), never fabricated.

Run:
  export TMPDIR=/home/matt/.claude/jobs/dec46f73/tmp \
         PYTHONPATH=runners/dsl/python:.:scripts OZMA_NO_LLM=1
  python3 scripts/jabberwock_ground_by_meaning.py
"""
import json
import os
os.environ.setdefault("OZMA_NO_LLM", "1")

from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
from domains import procedural_reader as pr
from domains import method_synthesis as ms
from domains import binding_resolver as br
from domains import dictionary_lexicon as dl


def hr(t):
    print("\n" + "=" * 74); print(t); print("=" * 74)


def show_binding(d):
    print("GROUNDED BINDING (nothing hand-supplied):")
    print("  binding = %s" % json.dumps(d["binding"]))
    for line in d["provenance"]:
        if any(k in line for k in ("role_relation", "aggregate.edge", "value_attr")):
            print("    - " + line)
    if d["underspecified"]:
        print("  UNDERSPECIFIED: %s" % d["underspecified"])


# --------------------------------------------------------------------------- #
def fresh():
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    return a


def renamed_task():
    hr("CASE 1 - RENAMED TASK: ownership edge is `belongs_to` (+ `created_by` distractor)")
    a = fresh(); s, inner = a.s, a.inner
    owner = s.add_node("Concept", {"name": "alice"})
    maker = s.add_node("Concept", {"name": "bob"})
    task = s.add_node("Message", {"kind": "task", "done": 0.0})
    inner.add_edge_unchecked(task, "belongs_to", owner)      # ownership, RENAMED
    inner.add_edge_unchecked(task, "created_by", maker)      # DISTRACTOR
    passage = "When a task is marked done, add a completed edge from the task to its owner."
    print("READ:", passage)
    model = pr.read_method(a, passage, name="task")
    grounded = br.derive_binding(a, model)
    show_binding(grounded)
    res = ms.synthesise_rule_from_method(a, model, grounded["binding"])
    inner.run_rules(10000)
    pre = inner.neighbours(task, "completed")
    s.set_attr(task, "done", 1.0)
    inner.run_rules(10000)
    got = inner.neighbours(task, "completed")
    ok = (not pre) and (owner in got) and (maker not in got)
    print("RUN: done=1 -> completed edges = %s   (expect [owner=%s], NOT maker=%s)"
          % (got, owner, maker))
    print("RESULT: chose %r ; landed on owner not distractor: %s"
          % (grounded["binding"].get("role_relation"), ok))
    return ok


def renamed_ivm():
    hr("CASE 2 - RENAMED IVM: mention edge is `cites` (+ `created_by` distractor)")
    a = fresh(); s, inner = a.s, a.inner
    src = s.add_node("Message", {"kind": "source"})
    view = s.add_node("Message", {"kind": "view", "val": -1.0})
    inner.add_edge_unchecked(view, "depends_on", src)
    for w in ["alpha", "beta", "gamma"]:
        inner.add_edge_unchecked(src, "cites", s.add_node("Mention", {"text": w}))  # RENAMED
    inner.add_edge_unchecked(src, "created_by", s.add_node("Concept", {"name": "carol"}))  # DISTRACTOR
    passage = ("A view holds the count of its source's mentions. "
               "A view depends on its source. "
               "When the source changes, the view becomes stale. "
               "Recompute a stale view from its source.")
    print("READ:", passage)
    model = pr.read_method(a, passage, name="ivm")
    grounded = br.derive_binding(a, model)
    show_binding(grounded)
    ms.synthesise_rule_from_method(a, model, grounded["binding"])
    val = lambda: s.node(view)["attrs"]["val"]
    inner.run_rules(10000)
    v3 = val()
    for w in ["delta", "epsilon"]:
        inner.add_edge_unchecked(src, "cites", s.add_node("Mention", {"text": w}))
    inner.run_rules(10000)
    v5 = val()
    ok = (grounded["binding"].get("aggregate", {}).get("edge") == "cites"
          and abs(v3 - 3.0) < 1e-9 and abs(v5 - 5.0) < 1e-9)
    print("RUN: 3 cites -> val=%s (expect 3) ; +2 -> val=%s (expect 5)" % (v3, v5))
    print("RESULT: chose %r ; coherent: %s"
          % (grounded["binding"].get("aggregate", {}).get("edge"), ok))
    return ok


def negative_control():
    hr("CASE 3 - NEGATIVE CONTROL: ownership edge is opaque `rel_42` (ungroundable)")
    a = fresh(); s, inner = a.s, a.inner
    owner = s.add_node("Concept", {"name": "alice"})
    task = s.add_node("Message", {"kind": "task", "done": 0.0})
    inner.add_edge_unchecked(task, "rel_42", owner)          # opaque ownership
    passage = "When a task is marked done, add a completed edge from the task to its owner."
    print("READ:", passage)
    model = pr.read_method(a, passage, name="task")
    grounded = br.derive_binding(a, model)
    show_binding(grounded)
    declined = "role_relation" not in grounded["binding"] and "role_relation" in grounded["underspecified"]
    print("RESULT: DECLINED (never fabricated): %s" % declined)
    return declined


def main():
    print("donkey=0 / OZMA_NO_LLM =", os.environ.get("OZMA_NO_LLM"))
    ms_warm = dl.warm_wordnet()
    print("WordNet warmed OFFLINE in %.0f ms (no network); warm now: %s"
          % (ms_warm, dl.is_wordnet_warm()))
    r = {
        "renamed-task (semantic)": renamed_task(),
        "renamed-IVM (semantic)": renamed_ivm(),
        "negative-control (decline)": negative_control(),
    }
    hr("SUMMARY")
    for k, v in r.items():
        print("  %-28s %s" % (k, "PASS" if v else "FAIL"))
    print("  ALL PASS:", all(r.values()))


if __name__ == "__main__":
    main()

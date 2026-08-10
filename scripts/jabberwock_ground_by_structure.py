"""STRUCTURAL grounding of the read-noun <-> domain-edge link (scratch proof).

The THIRD and LAST-resort stage past character (rhyming names) and semantic
(meaning of names). When a domain names its ownership edge with a COINED, OPAQUE
token (`rel_42`) that carries no lexical and no definitional signal, the role
noun still grounds — by the relation's STRUCTURE, i.e. what it CONNECTS. This is
the Jabberwocky principle made mechanical (meaning from Gamma/structure,
separable from lexical content): a nonsense-named relation is grounded by its
ENDPOINT TYPES matching the role's EXPECTED FILLER TYPE, not by its name.

The mechanism (all in domains/binding_resolver.py, a mechanical Argmax; grounding
supplies the pieces, NO hardcoded type map):
  1. role-noun -> expected filler TYPE, from the noun's WordNet HYPERNYM chain
     ("owner" is_a person/individual/...). The agent's OWN offline WordNet
     faculty (donkey=0 / OZMA_NO_LLM=1 - no LLM teacher).
  2. each candidate edge -> its TARGET-node TYPE, read from the domain graph.
  3. Argmax on the semantic relatedness of the target type NAME to the role's
     expected-type region (the semantic stage reused on TYPE names); accept the
     UNIQUELY-best above a floor; DECLINE on a tie (ambiguity).

Three cases, each behind a check:
  * STRUCTURAL PASS   : opaque `rel_42` : Task -> Person. character declines,
                        semantic declines, STRUCTURE grounds owner->rel_42
                        (owner is a person-role; rel_42 is the Task->Person edge)
                        -> completed edge lands on the owner.
  * WRONG-TYPE        : add opaque `rel_99` : Task -> Project (wrong type for a
                        person-role). rel_42 (->Person) must win on type match.
  * AMBIGUOUS DECLINE : two opaque edges `rel_42`, `rel_77` BOTH -> Person.
                        structure cannot disambiguate -> DECLINE honestly.

Run:
  export TMPDIR=/home/matt/.claude/jobs/dec46f73/tmp \
         PYTHONPATH=runners/dsl/python:.:scripts OZMA_NO_LLM=1
  python3 scripts/jabberwock_ground_by_structure.py
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


def fresh():
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    return a


def show_role_type(noun, wn):
    """Print the role noun's inferred expected filler type + which hypernyms."""
    words = sorted(br._role_type_words(noun, wn))
    # name a couple of the salient hypernyms for the 'how' provenance
    salient = [w for w in ("person", "individual", "someone", "entity",
                           "artifact", "document", "cause") if w in words]
    print("  ROLE %r -> expected filler TYPE inferred from WordNet hypernyms: %s%s"
          % (noun, salient or words[:4],
             "  (owner.n -> person.n: the noun's own is_a chain)"))


def show_grounding(a, task, tgt_noun="owner"):
    """Print the per-candidate structural table the resolver computed."""
    gd = a.s.graph_to_dict()
    wn = br._wn()
    show_role_type(tgt_noun, wn)
    rtb = br._role_type_bag(tgt_noun, wn)
    tgt_types = br._tgt_types_by_edge(gd, task)
    print("  CANDIDATE EDGES on the task node (edge -> target node-type -> match score):")
    rows = []
    for c in br._out_edge_types(gd, task):
        tts = tgt_types.get(c, set())
        best_tt, best_s = None, 0
        for tt in tts:
            sc = br._struct_score(rtb, tt, wn)
            if best_tt is None or sc > best_s:
                best_tt, best_s = tt, sc
        rows.append((c, best_tt, best_s))
    for c, tt, sc in sorted(rows, key=lambda x: -x[2]):
        print("      %-8s -> %-10s  score=%d" % (c, tt, sc))
    g = br._ground_edge(gd, task, tgt_noun)
    print("  CHOSEN: edge=%r  via STAGE=%r  (char decl, sem decl, structural decides)"
          % (g["edge"], g["path"]))
    if g.get("reason"):
        print("  DECLINE REASON: %s" % g["reason"])
    return g


# --------------------------------------------------------------------------- #
def structural_pass():
    hr("CASE 1 - STRUCTURAL PASS: opaque `rel_42` : Task -> Person")
    a = fresh(); s, inner = a.s, a.inner
    owner = s.add_node("Person", {"name": "alice"})
    task = s.add_node("Message", {"kind": "task", "done": 0.0})
    inner.add_edge_unchecked(task, "rel_42", owner)          # opaque ownership -> Person
    passage = "When a task is marked done, add a completed edge from the task to its owner."
    print("READ:", passage)
    model = pr.read_method(a, passage, name="task")
    show_grounding(a, task)
    grounded = br.derive_binding(a, model)
    print("  binding = %s" % json.dumps(grounded["binding"]))
    ms.synthesise_rule_from_method(a, model, grounded["binding"])
    inner.run_rules(10000)
    pre = inner.neighbours(task, "completed")
    s.set_attr(task, "done", 1.0)
    inner.run_rules(10000)
    got = inner.neighbours(task, "completed")
    ok = (not pre) and (owner in got) and grounded["binding"].get("role_relation") == "rel_42"
    print("  RUN: done=1 -> completed edges = %s  (expect [owner=%s])" % (got, owner))
    print("  RESULT: grounded opaque `rel_42` by STRUCTURE; completed lands on owner: %s" % ok)
    return ok


def wrong_type_distractor():
    hr("CASE 2 - WRONG-TYPE DISTRACTOR: `rel_42`->Person vs opaque `rel_99`->Project")
    a = fresh(); s, inner = a.s, a.inner
    owner = s.add_node("Person", {"name": "alice"})
    proj = s.add_node("Project", {"name": "apollo"})     # WRONG type for a person-role
    task = s.add_node("Message", {"kind": "task", "done": 0.0})
    inner.add_edge_unchecked(task, "rel_42", owner)          # -> Person  (right)
    inner.add_edge_unchecked(task, "rel_99", proj)           # -> Project (wrong type)
    passage = "When a task is marked done, add a completed edge from the task to its owner."
    print("READ:", passage)
    model = pr.read_method(a, passage, name="task")
    g = show_grounding(a, task)
    grounded = br.derive_binding(a, model)
    print("  binding = %s" % json.dumps(grounded["binding"]))
    ms.synthesise_rule_from_method(a, model, grounded["binding"])
    inner.run_rules(10000)
    s.set_attr(task, "done", 1.0)
    inner.run_rules(10000)
    got = inner.neighbours(task, "completed")
    ok = (g["edge"] == "rel_42") and (owner in got) and (proj not in got)
    print("  RUN: done=1 -> completed edges = %s  (expect [owner=%s], NOT proj=%s)"
          % (got, owner, proj))
    print("  RESULT: chose Person-edge `rel_42` over Project-edge `rel_99`; lands on owner: %s" % ok)
    return ok


def ambiguous_decline():
    hr("CASE 3 - AMBIGUOUS DECLINE: `rel_42` and `rel_77` BOTH -> Person")
    a = fresh(); s, inner = a.s, a.inner
    p1 = s.add_node("Person", {"name": "alice"})
    p2 = s.add_node("Person", {"name": "bob"})
    task = s.add_node("Message", {"kind": "task", "done": 0.0})
    inner.add_edge_unchecked(task, "rel_42", p1)             # -> Person
    inner.add_edge_unchecked(task, "rel_77", p2)             # -> Person  (same type!)
    passage = "When a task is marked done, add a completed edge from the task to its owner."
    print("READ:", passage)
    model = pr.read_method(a, passage, name="task")
    g = show_grounding(a, task)
    grounded = br.derive_binding(a, model)
    print("  binding = %s" % json.dumps(grounded["binding"]))
    declined = ("role_relation" not in grounded["binding"]
                and "role_relation" in grounded["underspecified"]
                and g["edge"] is None and g["path"] is None)
    print("  RESULT: DECLINED on structural ambiguity (never guessed): %s" % declined)
    return declined


def main():
    print("donkey=0 / OZMA_NO_LLM =", os.environ.get("OZMA_NO_LLM"))
    ms_warm = dl.warm_wordnet()
    print("WordNet warmed OFFLINE in %.0f ms (no network); warm now: %s"
          % (ms_warm, dl.is_wordnet_warm()))
    r = {
        "structural-pass (rel_42->Person)": structural_pass(),
        "wrong-type-distractor (rel_99->Project)": wrong_type_distractor(),
        "ambiguous-decline (two ->Person)": ambiguous_decline(),
    }
    hr("SUMMARY")
    for k, v in r.items():
        print("  %-42s %s" % (k, "PASS" if v else "FAIL"))
    print("  ALL PASS:", all(r.values()))


if __name__ == "__main__":
    main()

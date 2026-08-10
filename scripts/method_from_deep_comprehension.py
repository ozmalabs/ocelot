"""method_from_deep_comprehension — PROVE method-sourcing by DEEP-COMPREHENDING a
held procedural definition.

Pipeline (composes existing machinery; nothing new in the loop):
  held concept + definition  (proof it is held, not injected)
    -> RETRIEVE (semantic Argmax over curated concept names, WordNet sense bags)
    -> DEEP-COMPREHEND the definition (comprehension_reader.read_and_comprehend)
    -> situation model (SmEvents) -> MethodModel
       (method_from_comprehension.situation_model_to_method)
    -> synthesise (method_synthesis) -> validate (read_method_draft.validate_by_running)
    -> adopt (read_method_draft.adopt, live) -> the capability RUNS.

donkey=0 (OZMA_NO_LLM=1). Curated seeds only — never seeds/acquired/import_w*.
"""
from __future__ import annotations

import json
import os
import sys

from substrate.world_adapter import WorldAdapter
from domains import comprehension_reader as cr
from domains import method_from_comprehension as mfc
from domains import method_synthesis as ms
from domains import read_method_draft as rmd
from domains import binding_resolver as br

CURATED = ["data_structures_algorithms", "databases_and_storage", "computer_architecture"]
SEEDS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "seeds")


def load_curated_concepts() -> dict:
    """{name: (definition, seed_file)} from the CURATED seeds only (bounded —
    hundreds of concepts; NEVER touches seeds/acquired/import_w*)."""
    out = {}
    for f in CURATED:
        d = json.load(open(os.path.join(SEEDS, f + ".json")))
        for c in d["concepts"]:
            out.setdefault(c["name"], (c["definition"], f))
    return out


def retrieve(gap_topic: str, concepts: dict):
    """Semantic-relatedness Argmax over the curated concept NAMES for the gap
    topic — reuses binding_resolver's WordNet sense-bag relatedness (donkey=0).
    Returns (best_name, score, table). No hardcoded gap->concept map."""
    wn = br._wn()
    if wn is None:
        # offline fallback: character overlap (still a mechanical Argmax, no map)
        scored = sorted(((n, br._score(gap_topic, n)) for n in concepts),
                        key=lambda x: -x[1])
        return scored[0][0], scored[0][1], scored[:5]
    gap_bag = br._sense_bag(gap_topic.replace("_", " "), wn)
    scored = []
    for n in concepts:
        nbag = br._sense_bag(n.replace("_", " "), wn)
        # relatedness = grounded-meaning overlap + a token-identity bonus
        overlap = len(gap_bag & nbag)
        toks_gap = set(gap_topic.lower().replace("_", " ").split())
        toks_n = set(n.lower().replace("_", " ").split())
        scored.append((n, overlap + 3 * len(toks_gap & toks_n)))
    scored.sort(key=lambda x: -x[1])
    return scored[0][0], scored[0][1], scored[:5]


def operation_clauses(concept_name: str, definition: str) -> list:
    """Mechanical text normalisation: resolve the definition's ELIDED subject to
    the definiendum. A curated definition is ABOUT its concept, so a subject-less
    operation clause ('deletes tombstones') has the concept as its implicit
    subject ('Compaction deletes tombstones'). Content-free (no decision) — a
    world-adapter text prep, reported honestly. Returns one 'Subject <clause>.'
    candidate per subject-less clause (first token lowercase in the ORIGINAL
    case = no explicit subject), in text order, for the caller to try in turn."""
    import re
    subj = concept_name.replace("_", " ")
    subj = subj[0].upper() + subj[1:]
    out = []
    # SUBORDINATE-CLAUSE SURFACING (mechanical, no decision): a passive operation is
    # often stated in a subordinate/relative clause ('main memory updated WHEN line
    # is evicted'). Split each top-level clause on a fixed subordinator/relativizer
    # set and, for any resulting sub-span that carries a copula (is/are/was/.../be),
    # emit it as its OWN candidate so the reader sees the passive clause in isolation
    # (the buried-passive that the whole-blob read cannot select). Text prep only —
    # the reader still decides the construction; a false split just yields no event.
    _SUBORD = re.compile(r"\b(?:when|where|which|that|while|until|after|before|"
                         r"once|because|since|as|whenever|whereby)\b", re.I)
    _COP = re.compile(r"\b(?:is|are|was|were|be|been|being|am)\b", re.I)
    _PAREN = re.compile(r"\([^)]*\)")

    def _emit(span: str):
        span = _PAREN.sub("", span).strip().strip(".,;:")
        if not span:
            return
        toks = span.split()
        if toks and toks[0][:1].islower():
            out.append("%s %s." % (subj, span))
        else:
            out.append("%s." % span)

    for clause in re.split(r"[.!?:;,]\s*", definition):
        clause = clause.strip()
        if not clause:
            continue
        toks = clause.split()
        # subject-less iff the clause's first token is lowercase in the source
        if toks and toks[0][:1].islower():
            out.append("%s %s." % (subj, clause))
        # additionally surface any copular subordinate sub-span (buried passive).
        parts = _SUBORD.split(clause)
        if len(parts) > 1:
            for p in parts[1:]:
                if _COP.search(p):
                    _emit(p)
    if not out:                                   # nothing subject-less to resolve
        out.append("%s: %s" % (subj, definition))
    return out


def run_one(gap_topic: str, concepts: dict, *, adopt_live: bool = False,
            verbatim: bool = False) -> dict:
    print("=" * 78)
    print("GAP: the agent lacks the capability named %r" % gap_topic)
    # RETRIEVE
    name, score, table = retrieve(gap_topic, concepts)
    definition, seed_f = concepts[name]
    print("RETRIEVE (semantic Argmax over curated concept names):")
    print("   best match: %r  score=%d   [seed: %s.json]" % (name, score, seed_f))
    print("   top-5: %s" % [(n, s) for n, s in table])
    print("HELD definition (verbatim, proof it is held not injected):")
    print("   %s :: %s" % (name, definition))

    if verbatim:
        candidates = [definition]
        print("DEEP-COMPREHEND (VERBATIM definition):")
    else:
        candidates = operation_clauses(name, definition)
        print("DEEP-COMPREHEND (subject-resolved clauses -> definiendum), scanning %d:"
              % len(candidates))

    wa = None
    model = None
    text = None
    last_events = []
    for cand in candidates:
        wa = WorldAdapter()
        cr.read_and_comprehend(wa, cand)
        events = mfc.read_situation_events(wa)
        last_events = events
        m = mfc.situation_model_to_method(wa, name="deep_" + name)
        print("   try %r" % cand)
        print("      SmEvents: %s"
              % [{"verb": e["verb"], "agent": e["agent"], "theme": e["theme"]} for e in events])
        if not m.get("wall"):
            model, text = m, cand
            break
    if model is None:
        print("MAP -> WALL: no operation clause mapped to an actionable event")
        print("   reason: %s"
              % (m.get("reason") if candidates else "no clauses"))
        return {"name": name, "outcome": "wall_map", "detail": "no actionable event"}
    print("MethodModel (mapped from the situation model):")
    print("   effect=%s  main_event=%s" % (model["effect"], model["main_event"]))
    print("   how: %s" % model["how"])
    for st in model["steps"]:
        print("   step[%s] %s" % (st["step_index"], st["main"]))

    # SYNTHESISE (existing loop; no binding — self-contained model)
    syn = ms.synthesise_rule_from_method(wa, model, binding=None, install=False)
    if syn.get("wall"):
        print("SYNTHESISE -> WALL: %s" % syn["wall"])
        return {"name": name, "outcome": "wall_synth", "detail": syn["wall"]}
    print("SYNTHESISED RewriteRule:")
    print("   %s" % json.dumps(syn["rules"][0], indent=1).replace("\n", "\n   "))

    draft = {"kind": "read_method_rule", "name": model["name"], "model": model,
             "rules": syn["rules"], "effect": syn["effect"], "how": syn["how"]}
    verdict = rmd.validate_by_running(draft)
    print("VALIDATE (run the rule on an isolated instance):")
    print("   compile_ok=%s effect_matches=%s" % (verdict["compile_ok"], verdict["effect_matches"]))
    print("   expected: %s" % verdict["expected"])
    print("   observed: %s" % verdict["observed"])

    outcome = "validated" if verdict["effect_matches"] else "validate_fail"
    if verdict["effect_matches"] and adopt_live:
        res = rmd.adopt(wa, draft, persist=False)
        print("ADOPT (install live, persist=False -> no stray seed file):")
        print("   installed=%s rule=%s" % (res["installed"], res["rule_name"]))
        outcome = "adopted"
        _demo_capability_runs(wa, model)
    return {"name": name, "outcome": outcome, "effect": model["effect"]}


def _demo_capability_runs(wa, model):
    """Show the ADOPTED rule firing on a fresh live instance: build the anchor
    edge (+ the affected edge for del_edge), run the agent's own run_rules, read
    the effect back off the graph."""
    s, inner = wa.s, wa.inner
    rule = None
    for st in model["steps"]:
        if st["main"].get("kind") == "action":
            main = st["main"]
    # reconstruct the match/effect vocabulary from the model
    src_noun = main["roles"]["source"]; tgt_noun = main["roles"]["target"]
    etype = main["edge_type"]
    # find the anchor relation from the relation step
    anchor = next(st["main"]["relation"] for st in model["steps"]
                  if st["main"].get("kind") == "relation")
    a = s.add_node("T", {"kind": src_noun})
    b = s.add_node("T", {"kind": tgt_noun})
    inner.add_edge_unchecked(a, anchor, b)
    if model["effect"] == "del_edge":
        inner.add_edge_unchecked(a, etype, b)
    before = b in inner.neighbours(a, etype)
    inner.run_rules(20000)
    after = b in inner.neighbours(a, etype)
    print("   CAPABILITY RUNS on a live instance: %s -%s-> %s  before=%s after=%s  (%s)"
          % (src_noun, etype, tgt_noun, before, after,
             "edge added" if (model["effect"] == "add_edge" and after and not before)
             else "edge removed" if (model["effect"] == "del_edge" and before and not after)
             else "no change"))


def main():
    concepts = load_curated_concepts()
    print("Loaded %d curated concepts (NO import_w* — memory bounded).\n" % len(concepts))

    print("\n########## HEADLINE: full end-to-end close from a held definition ##########\n")
    run_one("compaction", concepts, adopt_live=True)

    print("\n\n########## VERBATIM (honest: terse technical prose vs the reader) ##########\n")
    run_one("compaction", concepts, adopt_live=False, verbatim=True)

    print("\n\n########## NEGATIVE: a declarative concept -> honest WALL ##########\n")
    run_one("relational_model", concepts, adopt_live=False)

    print("\n\n########## DISTRIBUTION: several procedural concepts ##########\n")
    ledger = []
    for topic in ["compaction", "write_ahead_log", "secondary_index",
                  "B_tree", "hash_table", "garbage_collection"]:
        if topic not in concepts:
            # retrieve maps the gap to the nearest curated concept
            pass
        r = run_one(topic, concepts, adopt_live=False)
        ledger.append(r)
        print()

    print("\n########## LEDGER ##########")
    for r in ledger:
        print("   %-24s -> %-14s (%s)" % (r["name"], r["outcome"], r.get("effect", r.get("detail", ""))))


if __name__ == "__main__":
    main()

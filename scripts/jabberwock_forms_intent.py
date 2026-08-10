#!/usr/bin/env python3
"""jabberwock_forms_intent -- PHASE 1 CONCEPTUALIZER gate, console form.

Companion to tests/test_conceptualizer.py (the fast pytest regression this script's
assertions mirror). Demonstrates, on real booted agents, that the jabberwock now FORMS a
communicative intent (Levelt's conceptualizer -- force + perlocutionary goal -- ahead of the
formulator) and a message SHAPE (the residual vs the audience) BEFORE it formulates an
utterance, instead of jumping comprehend -> produce with no formed intent.

THE WALL, PROVEN FIRST: a 'form a communicative intent (force + perlocutionary goal), shape
it for the audience before speaking' concern grounds to NOTHING in the held vocabulary until
`seeds/conceptualizer.json` is loaded (checked: no existing RelationCue/ComposerCue used the
words 'form' or 'shape' as a relation head before this build).

THE MACHINERY THE JABBERWOCK AUTHORS (`domains.reflective_faculty._compose_conceptualize_rule`,
the SAME Python composer-builder tier as `_compose_communicate_rule`/`_compose_construction_
rule`, dispatched via `induce_concern` -> `ground_concern`, `served_by:'python'` -- the
graph-resident meta-rule tier `composer_audience_produce_graph.json` occupies was judged too
large for phase 1; see `seeds/conceptualizer.json`'s own description for the honest tier
note):

  1. form_intent_<tag>          -- a communicative Goal (-for_audience-> an Interlocutor,
                                    -wants_force-> the ONE held ForceCodebookHub) JOINS the
                                    hub's ForceTemplate children via an Eq-test on
                                    force_kind==kind (the RULE ENGINE picks the template, not
                                    Python) and mints a CommunicativeIntent{force,
                                    perlocutionary_goal, informative_content}.
  2. request_message_shape_<tag> -- once an intent exists, mints a
                                    MessageShapeRequest{status:'requested'} (the SAME
                                    "pending request" idiom domains/audience_production_
                                    dispatch.py already established).

`domains/conceptualizer.py:scan_and_conceptualize` is the ONLY host-side call this script
makes beyond graph I/O -- the mechanical hook that calls
`domains.audience_driven_production.residual_vs_audience` (mints the MessageShape -- `focus`
IS `residual_vs_audience`'s `new`, `ground` IS its `known`, VERBATIM) + `select_utterance`
(the audience-designed FORMULATION) for every pending MessageShapeRequest.
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from substrate.boot_core import boot_core                  # noqa: E402
from substrate.seed_loader import manifest_for              # noqa: E402
import domains.reflective_faculty as rf                     # noqa: E402
import domains.conceptualizer as cc                          # noqa: E402

LEXICON = [
    {"form": "a robot", "concept": "a_robot"},
    {"form": "curious", "concept": "curious"},
    {"form": "asks questions", "concept": "asks_questions"},
    {"form": "learns from mistakes", "concept": "learns_from_mistakes"},
]
MEANING = {"a_robot", "curious", "asks_questions", "learns_from_mistakes"}
SHARED = ["a_robot", "curious"]

FORM_CLAUSE = ["form", "INTENT", "before", "UTTERANCE"]
SHAPE_CLAUSE = ["shape", "MESSAGE", "by", "RESIDUAL"]


class _Agent:
    def __init__(self, s, agent_node):
        self.s = s
        self.inner = s._inner
        self.agent = agent_node


def _base_agent() -> _Agent:
    s, agent_node = boot_core()
    ag = _Agent(s, agent_node)
    ag.s._inner.load_seed_manifest(manifest_for("relation_vocabulary"), ag.agent)
    ag.s._inner.load_seed_manifest(manifest_for("composer_dispatch"), ag.agent)
    ag.s._inner.load_seed_manifest(manifest_for("autonomy"), ag.agent)
    return ag


def _fresh_agent() -> _Agent:
    ag = _base_agent()
    cc.ensure_conceptualizer_seed(ag)
    return ag


def _ground(ag, name_hint):
    ind = rf.induce_concern(ag, [FORM_CLAUSE, SHAPE_CLAUSE], name_hint=name_hint)
    assert ind.get("minted") is True, ind
    g = rf.ground_concern(ag, [ind["capability_key"]])
    assert g.get("grounded") is True and g.get("served_by") == "python", g
    return g


def main() -> int:
    print("=" * 78)
    print("THE CONCEPTUALIZER -- form a communicative intent + shape it for the audience, "
          "BEFORE formulating (graph-authored, CLAUDE.md)")
    print("=" * 78)

    # ---- THE WALL, PROVEN FIRST --------------------------------------------
    print("\n--- THE WALL: 'form an intent, shape it for the audience' grounds to NOTHING "
          "before seeds/conceptualizer.json loads ---")
    ag_wall = _base_agent()
    ind_wall = rf.induce_concern(ag_wall, [FORM_CLAUSE, SHAPE_CLAUSE], name_hint="wall_probe")
    assert ind_wall.get("minted") is True
    res_wall = rf.ground_concern(ag_wall, [ind_wall["capability_key"]])
    print(f"ground_concern -> grounded={res_wall.get('grounded')}  path={res_wall.get('path')}")
    assert res_wall.get("grounded") is False and res_wall.get("path") == "predicate_grounding"

    # ---- THE JABBERWOCK AUTHORS THE TWO RULES ------------------------------
    print("\n--- THE JABBERWOCK AUTHORS form_intent / request_message_shape ---")
    ag = _fresh_agent()
    g = _ground(ag, "conceptualizer_demo")
    print(f"AUTHORED (conceptualize): path={g['path']}  served_by={g['served_by']}")
    for r in g["rules"]:
        print(f"\n  RULE {r['name']!r}")
        print(f"    match : {r['match']}")
        print(f"    where : {r['where']}")
        print(f"    effect: {r['effects']}")

    # ---- FORM THE INTENT (explicit graph data) -----------------------------
    print("\n--- FORM A COMMUNICATIVE INTENT: inform a GROUNDED (observed) audience ---")
    ag_g = _fresh_agent()
    _ground(ag_g, "ci_spouse")
    g_g = cc.mint_communicative_goal(
        ag_g, "inform", MEANING, {"id": "spouse", "observed": True, "known_concepts": SHARED})
    ag_g.inner.run_rules(2000)
    intent_read_g = cc.read_intent(ag_g, g_g)
    print(f"CommunicativeIntent: force={intent_read_g['force']!r}  "
          f"perlocutionary_goal={intent_read_g['perlocutionary_goal']!r}  "
          f"informative_content={sorted(intent_read_g['informative_content'])}")
    assert intent_read_g["force"] == "assertive"
    assert intent_read_g["perlocutionary_goal"] == "hearer_knows"
    assert sorted(intent_read_g["informative_content"]) == sorted(MEANING)

    # ---- FORM THE MESSAGE SHAPE (= the residual) ---------------------------
    print("\n--- FORM THE MESSAGE SHAPE (focus = residual_vs_audience's `new`, "
          "ground = its `known`) ---")
    results_g = cc.scan_and_conceptualize(ag_g, LEXICON)
    residual_g = results_g[0]["residual"]
    ag_g.inner.run_rules(2000)
    shaped_g = cc.read_intent(ag_g, g_g)
    print(f"MessageShape: focus={shaped_g['focus']}  ground={shaped_g['ground']}")
    assert shaped_g["focus"] == residual_g["new"]
    assert shaped_g["ground"] == residual_g["known"]

    # ---- THE SAME PIPELINE FOR AN UNGROUNDED (unobserved) AUDIENCE ---------
    print("\n--- SAME MEANING, AN UNGROUNDED (unobserved) AUDIENCE: a stranger ---")
    ag_u = _fresh_agent()
    _ground(ag_u, "ci_stranger")
    g_u = cc.mint_communicative_goal(ag_u, "inform", MEANING, {"id": "stranger", "observed": False})
    ag_u.inner.run_rules(2000)
    cc.scan_and_conceptualize(ag_u, LEXICON)
    ag_u.inner.run_rules(2000)
    shaped_u = cc.read_intent(ag_u, g_u)
    print(f"MessageShape: focus={shaped_u['focus']}  ground={shaped_u['ground']}")
    assert set(shaped_u["focus"]) == MEANING, "ungrounded -- nothing credited, focus == full meaning"
    assert len(shaped_g["focus"]) < len(shaped_u["focus"]), "grounded audience -> smaller focus"

    # ---- FORMULATE: the audience-designed utterance ------------------------
    print("\n--- FORMULATE (via select_utterance, reused verbatim): grounded -> terse, "
          "ungrounded -> explicit ---")
    print(f"  spouse   (grounded=True ) -> {shaped_g['utterance']!r} "
          f"({len(shaped_g['utterance'].split())} words)")
    print(f"  stranger (grounded=False) -> {shaped_u['utterance']!r} "
          f"({len(shaped_u['utterance'].split())} words)")
    assert shaped_g["grounded_used"] is True
    assert shaped_u["grounded_used"] is False
    assert shaped_g["utterance"] != shaped_u["utterance"]
    assert len(shaped_g["utterance"].split()) < len(shaped_u["utterance"].split())
    for w in ("a robot", "curious"):
        assert w not in shaped_g["utterance"], "grounded utterance never restates shared ground"
    for w in ("a robot", "curious", "asks questions", "learns from mistakes"):
        assert w in shaped_u["utterance"], "ungrounded fallback restates the FULL meaning"

    print("\n" + "=" * 78)
    print("PASS -- the conceptualizer forms an EXPLICIT CommunicativeIntent (force + "
          "perlocutionary_goal) and a MessageShape (focus/ground == residual_vs_audience's "
          "new/known) BEFORE formulating; the formulated utterance is audience-designed "
          "(terse when grounded, explicit when not), entirely from graph-authored rules + "
          "the already-approved audience_driven_production machinery -- no Python decision.")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(main())

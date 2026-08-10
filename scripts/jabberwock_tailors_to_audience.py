#!/usr/bin/env python3
"""jabberwock_tailors_to_audience -- AUDIENCE-DRIVEN PRODUCTION COGNITION gate,
console form.

Companion to tests/test_audience_production_cognition.py (the fast pytest regression
this script's assertions mirror). Demonstrates, on real booted agents, that
`domains/audience_driven_production.py`'s speaker-models-listener midpoint (memory
ozma_two_model_communication) is now a COGNITIVE FACULTY the agent USES, not just a
measurement a host prints: three rules the agent AUTHORS ITSELF via the composer
(`ground_concern([..., "tailor", ...])` -> `seeds/composer_audience_produce_graph.json`'s
meta-rule) --

  1. request_produce_for_audience_<tag> -- recognises a produce_utterance Goal carrying a
                                            for_audience edge and mints a
                                            ProduceForAudienceRequest (the decision to
                                            model-the-audience-and-tailor)
  2. default_explicit_produce_<tag>     -- the DEFAULT: every request defaults to
                                            mode:explicit (the safe fallback)
  3. tailor_when_grounded_<tag>         -- the OVERRIDE: mode:tailor iff the produced
                                            SystemModel of the interlocutor has
                                            grounded==true -- read directly off the graph,
                                            never a host flag

`domains/audience_production_dispatch.py:scan_and_speak_to_audience` is the ONLY
host-side call this script makes beyond graph I/O -- the mechanical hook that calls
`domains.audience_driven_production.audience_model` + `select_utterance` (chains
`system_model.model_system` / `pragmatic_speaker.choose_encoding` / `language.produce`,
all in-process Python that cannot execute inside a Rust rule effect) for every pending
`ProduceForAudienceRequest` and wires `req -has_audience_model-> sm` so the agent's own
rules have something to match.
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
from domains import audience_production_dispatch as apd     # noqa: E402

LEXICON = [
    {"form": "dinner", "concept": "dinner"},
    {"form": "seven pm", "concept": "seven_pm"},
    {"form": "the italian place", "concept": "italian_place"},
    {"form": "a reservation", "concept": "reservation"},
    {"form": "table for two", "concept": "table_for_two"},
]
MEANING = {"dinner", "seven_pm", "italian_place", "reservation", "table_for_two"}
SHARED = ["dinner", "seven_pm", "italian_place"]


class _Agent:
    def __init__(self, s, agent_node):
        self.s = s
        self.inner = s._inner
        self.agent = agent_node


def _fresh_agent() -> _Agent:
    s, agent_node = boot_core()
    ag = _Agent(s, agent_node)
    ag.s._inner.load_seed_manifest(manifest_for("relation_vocabulary"), ag.agent)
    ag.s._inner.load_seed_manifest(manifest_for("composer_dispatch"), ag.agent)
    ag.s._inner.load_seed_manifest(manifest_for("autonomy"), ag.agent)
    return ag


def _ground(ag, cue_clause, name_hint):
    ind = rf.induce_concern(ag, [cue_clause], name_hint=name_hint)
    assert ind.get("minted") is True, ind
    g = rf.ground_concern(ag, [ind["capability_key"]])
    assert g.get("grounded") is True and g.get("served_by") == "graph", g
    return g


def main() -> int:
    print("=" * 78)
    print("AUDIENCE-DRIVEN PRODUCTION -- the graph decides tailor-vs-explicit, "
          "graph-authored (CLAUDE.md)")
    print("=" * 78)

    # ---- THE AGENT AUTHORS THE THREE RULES ---------------------------------
    print("\n--- THE JABBERWOCK AUTHORS request_produce_for_audience / "
          "default_explicit_produce / tailor_when_grounded ---")
    ag = _fresh_agent()
    g = _ground(ag, ["tailor", "UTTERANCE", "to", "AUDIENCE"], "audience_produce_demo")
    print(f"AUTHORED (audience_produce): path={g['path']}  served_by={g['served_by']}")
    for r in g["rules"]:
        print(f"\n  RULE {r['name']!r}")
        print(f"    match : {r['match']}")
        print(f"    where : {r['where']}")
        print(f"    effect: {r['effects']}")

    # ---- GROUNDED (observed) AUDIENCE -> TAILOR, terse ---------------------
    print("\n--- PRODUCE FOR A GROUNDED (observed) AUDIENCE: the spouse ---")
    ag_g = _fresh_agent()
    _ground(ag_g, ["tailor", "UTTERANCE", "to", "AUDIENCE"], "ap_spouse")
    req_g = apd.mint_produce_for_audience_request(
        ag_g, MEANING, {"id": "spouse", "observed": True, "known_concepts": SHARED})
    res_g = apd.scan_and_speak_to_audience(ag_g, LEXICON)[0]["result"]
    sm_g = list(ag_g.inner.neighbours(req_g, "has_audience_model"))[0]
    print(f"SystemModel(spouse): grounded={ag_g.s.node(sm_g)['attrs'].get('grounded')}  "
          f"select_utterance.grounded_used={res_g['grounded_used']}")
    ag_g.inner.run_rules(2000)
    mode_g = ag_g.s.node(req_g)["attrs"]["mode"]
    utt_g = ag_g.s.node(req_g)["attrs"]["utterance"]
    print(f"AGENT'S OWN DECISION: mode={mode_g!r}")
    print(f"UTTERANCE (tailored, terse): {utt_g!r}")
    assert ag_g.s.node(sm_g)["attrs"].get("grounded") is True
    assert mode_g == "tailor"

    # ---- UNGROUNDED (unobserved) AUDIENCE -> EXPLICIT ----------------------
    print("\n--- PRODUCE FOR AN UNGROUNDED (unobserved) AUDIENCE: a stranger ---")
    ag_u = _fresh_agent()
    _ground(ag_u, ["tailor", "UTTERANCE", "to", "AUDIENCE"], "ap_stranger")
    req_u = apd.mint_produce_for_audience_request(
        ag_u, MEANING, {"id": "stranger", "observed": False})
    res_u = apd.scan_and_speak_to_audience(ag_u, LEXICON)[0]["result"]
    sm_u = list(ag_u.inner.neighbours(req_u, "has_audience_model"))[0]
    print(f"SystemModel(stranger): grounded={ag_u.s.node(sm_u)['attrs'].get('grounded')}  "
          f"select_utterance.grounded_used={res_u['grounded_used']}")
    ag_u.inner.run_rules(2000)
    mode_u = ag_u.s.node(req_u)["attrs"]["mode"]
    utt_u = ag_u.s.node(req_u)["attrs"]["utterance"]
    print(f"AGENT'S OWN DECISION: mode={mode_u!r}")
    print(f"UTTERANCE (explicit fallback): {utt_u!r}")
    assert ag_u.s.node(sm_u)["attrs"].get("grounded") is False
    assert mode_u == "explicit"

    # ---- DISCRIMINATIVE CONTRAST --------------------------------------------
    print("\n--- THE SPOUSE-VS-STRANGER CONTRAST, NOW THE AGENT'S OWN DECISION ---")
    print(f"  spouse   (grounded=True ) -> mode={mode_g!r}  {len(utt_g.split())} words: {utt_g!r}")
    print(f"  stranger (grounded=False) -> mode={mode_u!r}  {len(utt_u.split())} words: {utt_u!r}")
    assert mode_g != mode_u
    assert len(utt_g.split()) < len(utt_u.split())

    # ---- THE PRODUCE-GOAL PATH: rule 1 fires autonomously -------------------
    print("\n--- A produce_utterance GOAL CARRYING for_audience AUTONOMOUSLY REQUESTS "
          "modelling (rule 1) ---")
    ag_goal = _fresh_agent()
    _ground(ag_goal, ["tailor", "UTTERANCE", "to", "AUDIENCE"], "ap_goal")
    g_node = ag_goal.s.add_node("Goal", {"kind": "describe_scene"})
    sg = ag_goal.s.add_node("Goal", {"kind": "produce_utterance", "action": "produce_utterance"})
    aud = ag_goal.s.add_node("Interlocutor", {"id": "spouse", "observed": True, "known_concepts": SHARED})
    ag_goal.inner.add_edge_unchecked(g_node, "has_subgoal", sg)
    ag_goal.inner.add_edge_unchecked(sg, "for_audience", aud)
    ag_goal.inner.run_rules(2000)
    reqs = list(ag_goal.s.nodes("ProduceForAudienceRequest"))
    print(f"ProduceForAudienceRequest minted BY THE AGENT'S OWN RULE (no host mint call): "
          f"{len(reqs)} (must be 1)")
    assert len(reqs) == 1

    print("\n" + "=" * 78)
    print("PASS -- audience-driven production is a cognitive faculty: the agent tailors "
          "an utterance to the residual only when its model of the audience is grounded "
          "in observation, and falls back to explicit otherwise, keyed on the "
          "SystemModel.grounded attr it reads off the graph, never a host flag.")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""jabberwock_monitors_before_speaking -- PHASE 2 CONCEPTUALIZER gate, console form.

Companion to tests/test_conceptualizer_monitor.py (the fast pytest regression this script's
assertions mirror). Demonstrates, on real booted agents, that the jabberwock now MONITORS a
formulated utterance -- Levelt's conceptualizer -> formulator -> MONITOR internal loop -- before
it may be committed/emitted: it IMAGINES RECEPTION (decodes its own produced utterance back via
`domains.language.comprehend`, and rechecks the audience's CURRENT credited ground -- a
"reground before committing" step), VERIFIES the CommunicativeIntent's perlocutionary_goal is
actually recoverable, and REVISES (re-formulates more explicitly) if not, looping until a
Verdict clears the COMMITMENT GATE.

THE WALL, PROVEN FIRST: a 'monitor the utterance before committing it, commit only if
recoverable' concern grounds to NOTHING in the held vocabulary until this build extended
`seeds/conceptualizer.json` (checked: no existing RelationCue/ComposerCue used the words
'monitor' or 'commit' as a relation head before this build).

THE MACHINERY THE JABBERWOCK AUTHORS (`domains.reflective_faculty._compose_conceptualize_rule`,
extended -- NOT replaced -- from phase 1, same Python composer-builder tier, dispatched via
`induce_concern` -> `ground_concern`, `served_by:'python'`):

  1. request_monitor_<tag>          -- once a MessageShape exists, mint a
                                        MonitorRequest{status:'requested'}.
  2. commit_if_recoverable_<tag>    -- Eq-tests Verdict.recoverable==true -> mints
                                        Committed{utterance, terseness, grounded_used} --
                                        THE COMMITMENT GATE.
  3. revise_if_not_recoverable_<tag> -- Eq-tests Verdict.recoverable==false -> mints a FRESH
                                        MessageShapeRequest for the SAME intent, re-triggering
                                        scan_and_conceptualize (against the now-current audience
                                        state) and, via rule chaining, request_monitor_<tag>
                                        again -- the "loop until recoverable" IS this rule chain
                                        re-firing inside one run_rules fixpoint, no Python
                                        iteration.

`domains/conceptualizer.py:scan_and_monitor` is the ONLY new host-side call beyond graph I/O --
the mechanical hook that IMAGINES RECEPTION: decodes the formulated utterance via
`domains.language.comprehend` (the agent's OWN comprehension running on its OWN production) and
unions it with a FRESHLY regrounded `audience_driven_production.audience_model` +
`residual_vs_audience` call (against the Interlocutor node's CURRENT attrs, not the snapshot the
shape was formulated from), then writes a `Verdict{recoverable, perlocutionary_goal, missing}`
the authored rules branch on.
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
MONITOR_CLAUSE = ["monitor", "UTTERANCE", "before", "COMMIT"]
COMMIT_CLAUSE = ["commit", "UTTERANCE", "if", "RECOVERABLE"]
ALL_CLAUSES = [FORM_CLAUSE, SHAPE_CLAUSE, MONITOR_CLAUSE, COMMIT_CLAUSE]


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
    ind = rf.induce_concern(ag, ALL_CLAUSES, name_hint=name_hint)
    assert ind.get("minted") is True, ind
    g = rf.ground_concern(ag, [ind["capability_key"]])
    assert g.get("grounded") is True and g.get("served_by") == "python", g
    return g


def main() -> int:
    print("=" * 78)
    print("THE SELF-MONITOR -- imagine the utterance's reception and reground BEFORE "
          "committing (graph-authored, CLAUDE.md)")
    print("=" * 78)

    # ---- THE WALL, PROVEN FIRST --------------------------------------------
    print("\n--- THE WALL: 'monitor the utterance before commit, commit if recoverable' "
          "grounds to NOTHING before this build ---")
    ag_wall = _base_agent()
    ind_wall = rf.induce_concern(ag_wall, [MONITOR_CLAUSE, COMMIT_CLAUSE], name_hint="wall_probe")
    assert ind_wall.get("minted") is True
    res_wall = rf.ground_concern(ag_wall, [ind_wall["capability_key"]])
    print(f"ground_concern -> grounded={res_wall.get('grounded')}  path={res_wall.get('path')}")
    assert res_wall.get("grounded") is False and res_wall.get("path") == "predicate_grounding"

    # ---- THE JABBERWOCK AUTHORS THE THREE MONITOR/COMMIT RULES -------------
    print("\n--- THE JABBERWOCK AUTHORS request_monitor / commit_if_recoverable / "
          "revise_if_not_recoverable ---")
    ag_demo = _fresh_agent()
    g_demo = _ground(ag_demo, "monitor_demo")
    print(f"AUTHORED (conceptualize): path={g_demo['path']}  served_by={g_demo['served_by']}")
    for r in g_demo["rules"]:
        print(f"\n  RULE {r['name']!r}")
        print(f"    match : {r['match']}")
        print(f"    effect: {r['effects']}")

    # ---- SCENARIO A: MONITOR CATCHES + REVISES -----------------------------
    print("\n" + "-" * 78)
    print("SCENARIO A -- an audience's credited ground turns out NOT actually shared by "
          "commit time (a stale/corrected belief); the monitor RE-GROUNDS and catches it.")
    print("-" * 78)
    ag_a = _fresh_agent()
    _ground(ag_a, "ci_catch")
    g_a = cc.mint_communicative_goal(
        ag_a, "inform", MEANING, {"id": "listener_a", "observed": True, "known_concepts": SHARED})
    ag_a.inner.run_rules(2000)
    results_a = cc.scan_and_conceptualize(ag_a, LEXICON)
    initial_a = results_a[0]["result"]["utterance"]
    print(f"formulated (grounded, terse): {initial_a!r}")
    assert results_a[0]["result"]["grounded_used"] is True
    ag_a.inner.run_rules(2000)

    # the world/caller discovers the credited observation doesn't actually hold --
    # flip the Interlocutor node's `observed` attr BEFORE the monitor ever runs.
    intent_a = results_a[0]["intent"]
    aud_node_a = next(iter(ag_a.inner.neighbours(intent_a, "for_audience")))
    print(f"REGROUNDING CORRECTION: interlocutor {ag_a.s.node(aud_node_a)['attrs']['id']!r} "
          f"was NOT actually observed after all -- flipping observed=False")
    ag_a.inner.set_attr(aud_node_a, "observed", False)

    pre_commit_a = cc.read_committed(ag_a, g_a)
    print(f"COMMIT GATE before monitoring: committed={pre_commit_a['committed']}")
    assert pre_commit_a["committed"] is None

    cc.run_pipeline(ag_a, LEXICON, rounds=4)
    committed_a = cc.read_committed(ag_a, g_a)
    print(f"\nINITIAL (terse) utterance:     {initial_a!r}")
    print(f"COMMITTED (revised) utterance: {committed_a['utterance']!r}")
    assert committed_a["committed"] is not None
    assert committed_a["utterance"] != initial_a
    assert committed_a["grounded_used"] is False
    for w in ("a robot", "curious"):
        assert w in committed_a["utterance"]
    verdicts_a = [ag_a.s.node(n)["attrs"] for n in ag_a.s.nodes("Verdict")]
    print(f"Verdicts (in order minted): "
          f"{[(v['recoverable'], v['perlocutionary_goal'], v['missing']) for v in verdicts_a]}")
    assert sorted(v["recoverable"] for v in verdicts_a) == [False, True]

    # ---- SCENARIO B: MONITOR PASSES ----------------------------------------
    print("\n" + "-" * 78)
    print("SCENARIO B -- a genuinely grounded audience: recoverable first try, NO revision.")
    print("-" * 78)
    ag_b = _fresh_agent()
    _ground(ag_b, "ci_pass")
    g_b = cc.mint_communicative_goal(
        ag_b, "inform", MEANING, {"id": "listener_b", "observed": True, "known_concepts": SHARED})
    ag_b.inner.run_rules(2000)
    results_b = cc.scan_and_conceptualize(ag_b, LEXICON)
    initial_b = results_b[0]["result"]["utterance"]
    ag_b.inner.run_rules(2000)
    cc.run_pipeline(ag_b, LEXICON, rounds=4)
    committed_b = cc.read_committed(ag_b, g_b)
    print(f"INITIAL (terse) utterance:      {initial_b!r}")
    print(f"COMMITTED (unrevised) utterance: {committed_b['utterance']!r}")
    assert committed_b["utterance"] == initial_b, "no revision needed"
    assert committed_b["grounded_used"] is True
    assert len(list(ag_b.s.nodes("MessageShapeRequest"))) == 1, "no revise cycle fired"

    # ---- THE CONTRAST -------------------------------------------------------
    print("\n" + "-" * 78)
    print("CONTRAST -- SAME meaning, SAME initial terse formulation:")
    print(f"  grounded (unflipped)   commits TERSE, unrevised: {committed_b['utterance']!r}")
    print(f"  regrounded-ungrounded  commits EXPLICIT after ONE monitor-driven revision: "
          f"{committed_a['utterance']!r}")
    assert initial_a == initial_b
    assert committed_a["utterance"] != committed_b["utterance"]

    print("\n" + "=" * 78)
    print("PASS -- the conceptualizer MONITORS a formulated utterance (imagined reception via "
          "its own comprehend() + a freshly regrounded audience model) BEFORE it may be "
          "committed; a recoverable verdict commits, a non-recoverable one revises and "
          "re-monitors, entirely via graph-authored rules + already-approved machinery -- no "
          "Python decision, nothing emitted before the commit gate clears it.")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(main())

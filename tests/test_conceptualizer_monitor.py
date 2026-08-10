"""test_conceptualizer_monitor — PHASE 2 of the CONCEPTUALIZER: the SELF-MONITOR (Levelt's
conceptualizer -> formulator -> MONITOR internal loop; "imagine the utterance's reception and
reground before committing"). Fast pytest twin of
`scripts/jabberwock_monitors_before_speaking.py` (read that script's module docstring for the
full narrative).

THE MACHINERY (read-only here, never modified except the two files this build brief names):
`domains/audience_driven_production.py` stays exactly as the prior arc left it.
`domains/language.py` (`comprehend`/`produce`) stays exactly as it was — reused verbatim as the
IMAGINE-RECEPTION decode. `domains/conceptualizer.py` gained THREE new functions
(`scan_and_monitor`, `run_pipeline`, `read_committed`) — marshal-only, mirroring
`scan_and_conceptualize`/`read_intent`'s existing tier. `domains/reflective_faculty.py`'s
`_compose_conceptualize_rule` (extended, not replaced) now also authors `request_monitor_<tag>`
/ `commit_if_recoverable_<tag>` / `revise_if_not_recoverable_<tag>` when the concern grounds
'monitor'/'commit' relations — dispatched via `induce_concern`->`ground_concern` exactly like
phase 1's `form_intent_<tag>`/`request_message_shape_<tag>`, gated by TWO new RelationCue/
ComposerCue entries in `seeds/conceptualizer.json` (local_id 10-13).

Per CLAUDE.md's discipline, no test here hand-installs the monitor/commit/revise rules —
every test either (a) proves the 'monitor'/'commit' vocabulary genuinely WALLS before this
build, or (b) drives `induce_concern`->`ground_concern` and reads back what the agent's own
composer authored, or (c) drives the full mint->tick->shape->tick->monitor->tick pipeline on a
real booted agent and reads the graph state back."""
from __future__ import annotations

import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import pytest

pytest.importorskip("substrate_rs")

from substrate.boot_core import boot_core                              # noqa: E402
from substrate.seed_loader import manifest_for                         # noqa: E402
import domains.reflective_faculty as rf                                # noqa: E402
import domains.conceptualizer as cc                                    # noqa: E402

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
    """Minimal duck-typed agent wrapper — identical shape to
    tests/test_conceptualizer.py's own `_Agent` (harness glue only, no source modified)."""
    def __init__(self, s, agent_node):
        self.s = s
        self.inner = s._inner
        self.agent = agent_node


def _base_agent() -> _Agent:
    """A fresh agent with the dispatch machinery loaded but WITHOUT the conceptualizer seed —
    used by the wall-proof test."""
    s, agent_node = boot_core()
    ag = _Agent(s, agent_node)
    ag.s._inner.load_seed_manifest(manifest_for("relation_vocabulary"), ag.agent)
    ag.s._inner.load_seed_manifest(manifest_for("composer_dispatch"), ag.agent)
    ag.s._inner.load_seed_manifest(manifest_for("autonomy"), ag.agent)
    return ag


def _fresh_agent() -> _Agent:
    """A fresh agent with the conceptualizer seed additionally loaded (ForceCodebook + the
    'form'/'shape'/'monitor'/'commit' RelationCue/ComposerCue vocabulary)."""
    ag = _base_agent()
    cc.ensure_conceptualizer_seed(ag)
    return ag


def _ground_all(ag, tag="cim_t"):
    """Ground ALL FOUR conceptualizer clauses in one call — authors all five rules (the two
    phase-1 rules + the three phase-2 monitor/commit rules) onto the same agent."""
    ind = rf.induce_concern(ag, ALL_CLAUSES, name_hint=tag)
    assert ind.get("minted") is True, ind
    g = rf.ground_concern(ag, [ind["capability_key"]])
    assert g.get("grounded") is True and g.get("served_by") == "python", g
    return g


def _formed_and_flipped(tag, flip: bool):
    """Shared scenario builder: mint a communicative Goal to inform an OBSERVED audience that
    shares SHARED concepts, run the phase-1 formation, capture the INITIAL (terse, since the
    audience is grounded) utterance, then optionally FLIP the Interlocutor node's `observed`
    attr to False before the monitor ever runs — simulating a corrected/stale belief ("I
    thought I had observed this audience; I hadn't, or it changed") the monitor must catch on
    RE-grounding. Returns (agent, goal_node, initial_utterance)."""
    ag = _fresh_agent()
    _ground_all(ag, tag)
    g = cc.mint_communicative_goal(
        ag, "inform", MEANING, {"id": tag, "observed": True, "known_concepts": SHARED})
    ag.inner.run_rules(2000)
    results = cc.scan_and_conceptualize(ag, LEXICON)
    assert len(results) == 1
    initial_utterance = results[0]["result"]["utterance"]
    assert results[0]["result"]["grounded_used"] is True, "must start GROUNDED (terse) to be a real catch"
    ag.inner.run_rules(2000)
    if flip:
        intent = results[0]["intent"]
        aud_node = None
        for nb in ag.inner.neighbours(intent, "for_audience"):
            aud_node = nb
            break
        assert aud_node is not None
        ag.inner.set_attr(aud_node, "observed", False)
    return ag, g, initial_utterance


# ===========================================================================
# 1. the 'monitor'/'commit' vocabulary genuinely walls before this change
# ===========================================================================
def test_wall_before_monitor_commit_vocabulary():
    ag = _base_agent()
    ind = rf.induce_concern(ag, [MONITOR_CLAUSE, COMMIT_CLAUSE], name_hint="wall_probe_monitor")
    assert ind.get("minted") is True
    res = rf.ground_concern(ag, [ind["capability_key"]])
    assert res.get("grounded") is False
    assert res.get("path") == "predicate_grounding"


def test_monitor_commit_cues_load_and_dispatch_to_conceptualize_composer():
    ag = _fresh_agent()
    name = rf._pick_composer(ag.s, ag.inner, ag.agent, {"monitor", "commit"})
    assert name == "conceptualize"


# ===========================================================================
# 2. the jabberwock AUTHORS the three monitor/commit rules via the composer
# ===========================================================================
def test_agent_authors_monitor_and_commit_rules_via_graph_composer():
    ag = _fresh_agent()
    ind = rf.induce_concern(ag, ALL_CLAUSES, name_hint="cim_authors")
    key = ind["capability_key"]
    before = ag.inner.rule_count()
    g = rf.ground_concern(ag, [key])
    after = ag.inner.rule_count()

    assert g.get("grounded") is True, g.get("wall")
    assert g.get("served_by") == "python"
    assert g.get("path") == "compose_conceptualize_rule"
    assert after - before == 5, "all five rules authored in one grounding (2 phase-1 + 3 phase-2)"

    by_name = {r["name"]: r for r in g["rules"]}
    assert {"form_intent_" + key, "request_message_shape_" + key, "request_monitor_" + key,
            "commit_if_recoverable_" + key, "revise_if_not_recoverable_" + key} == set(by_name)

    monitor_rule = by_name["request_monitor_" + key]
    assert monitor_rule["match"] == [["req", "for_intent", "intent"], ["req", "has_shape", "shape"]]
    assert monitor_rule["effects"][0][:3] == ["add_node", "mreq", "MonitorRequest"]

    commit_rule = by_name["commit_if_recoverable_" + key]
    assert commit_rule["match"] == [["mreq", "has_verdict", "verdict"], ["mreq", "for_intent", "intent"],
                                     ["mreq", "for_shape", "shape"]]
    assert commit_rule["effects"][0][:3] == ["add_node", "committed", "Committed"]
    assert commit_rule["effects"][1] == ["add_edge", "intent", "has_committed", "committed"]

    revise_rule = by_name["revise_if_not_recoverable_" + key]
    assert revise_rule["match"] == [["mreq", "has_verdict", "verdict"], ["mreq", "for_intent", "intent"]]
    assert revise_rule["effects"][0][:3] == ["add_node", "req2", "MessageShapeRequest"]


def test_re_grounding_monitor_commit_is_idempotent_no_rechurn():
    ag = _fresh_agent()
    ind = rf.induce_concern(ag, ALL_CLAUSES, name_hint="cim_idem")
    key = ind["capability_key"]
    rf.ground_concern(ag, [key])
    rc1 = ag.inner.rule_count()
    rf.ground_concern(ag, [key])
    rc2 = ag.inner.rule_count()
    assert rc1 == rc2


# ===========================================================================
# 3. MONITOR CATCHES + REVISES — a too-terse utterance formulated for a
#    credited-grounded audience, whose credited ground turns out NOT actually
#    shared by the time the monitor RE-grounds it (a stale/corrected belief).
# ===========================================================================
def test_monitor_catches_ungrounded_shift_and_revises_before_commit():
    ag, g, initial_utterance = _formed_and_flipped("cim_catch", flip=True)

    # nothing may be read as committed until the monitor has run at all
    pre = cc.read_committed(ag, g)
    assert pre["committed"] is None and pre["utterance"] is None

    cc.run_pipeline(ag, LEXICON, rounds=4)
    committed = cc.read_committed(ag, g)

    print("INITIAL (terse) utterance:  ", repr(initial_utterance))
    print("COMMITTED (revised) utterance:", repr(committed["utterance"]))

    assert committed["committed"] is not None, "the monitor must clear a committed utterance eventually"
    assert committed["utterance"] != initial_utterance, "the monitor REVISED — committed differs from the initial terse formulation"
    assert committed["grounded_used"] is False, "revision fell back to the honest explicit fallback"
    assert len(committed["utterance"].split()) > len(initial_utterance.split()), "the revision is MORE explicit"
    # the committed utterance restates the ground the initial terse formulation had dropped
    for w in ("a robot", "curious"):
        assert w in committed["utterance"], "the revision RESTATES the ground no longer credited"

    # exactly one revision happened (one extra MessageShapeRequest, one extra MonitorRequest)
    assert len(list(ag.s.nodes("MessageShapeRequest"))) == 2
    assert len(list(ag.s.nodes("MonitorRequest"))) == 2
    verdicts = [ag.s.node(n)["attrs"] for n in ag.s.nodes("Verdict")]
    assert sorted(v["recoverable"] for v in verdicts) == [False, True], "caught, then cleared"


# ===========================================================================
# 4. MONITOR PASSES — a genuinely grounded audience with a terse utterance:
#    recoverable first try, no revision, commits the SAME terse utterance.
# ===========================================================================
def test_monitor_passes_grounded_audience_commits_terse_unrevised():
    ag, g, initial_utterance = _formed_and_flipped("cim_pass", flip=False)

    cc.run_pipeline(ag, LEXICON, rounds=4)
    committed = cc.read_committed(ag, g)

    print("INITIAL (terse) utterance:   ", repr(initial_utterance))
    print("COMMITTED (unrevised) utterance:", repr(committed["utterance"]))

    assert committed["committed"] is not None
    assert committed["utterance"] == initial_utterance, "no revision — committed matches the initial terse formulation"
    assert committed["grounded_used"] is True

    # exactly ONE MessageShapeRequest / MonitorRequest / Verdict — no revise cycle fired
    assert len(list(ag.s.nodes("MessageShapeRequest"))) == 1
    assert len(list(ag.s.nodes("MonitorRequest"))) == 1
    verdicts = [ag.s.node(n)["attrs"] for n in ag.s.nodes("Verdict")]
    assert len(verdicts) == 1 and verdicts[0]["recoverable"] is True


def test_grounded_vs_ungrounded_shift_contrast_same_meaning():
    """Pin the contrast the build brief asks for directly: SAME content, SAME initial terse
    formulation; a grounded (unflipped) audience commits it unrevised, an audience whose
    credited ground turns out NOT to hold commits something more explicit AFTER exactly one
    monitor-driven revision."""
    ag_g, g_g, initial_g = _formed_and_flipped("cim_contrast_g", flip=False)
    ag_u, g_u, initial_u = _formed_and_flipped("cim_contrast_u", flip=True)
    assert initial_g == initial_u, "same meaning, same audience credit at formulation time -> same initial formulation"

    cc.run_pipeline(ag_g, LEXICON, rounds=4)
    cc.run_pipeline(ag_u, LEXICON, rounds=4)
    committed_g = cc.read_committed(ag_g, g_g)
    committed_u = cc.read_committed(ag_u, g_u)

    assert committed_g["utterance"] == initial_g, "grounded stays terse — no revision needed"
    assert committed_u["utterance"] != initial_u, "regrounded-ungrounded revises to explicit"
    assert len(committed_u["utterance"].split()) > len(committed_g["utterance"].split())


# ===========================================================================
# 5. GOAL-KEYED — the verdict is keyed on the perlocutionary_goal, not a
#    bare cost/score (asserted directly on the Verdict data, per the build
#    brief's honest fallback).
# ===========================================================================
def test_verdict_is_keyed_on_perlocutionary_goal():
    ag, g, _ = _formed_and_flipped("cim_goalkey", flip=True)
    read = cc.read_intent(ag, g)
    assert read["perlocutionary_goal"] == "hearer_knows"

    cc.run_pipeline(ag, LEXICON, rounds=4)
    verdicts = [ag.s.node(n)["attrs"] for n in ag.s.nodes("Verdict")]
    assert len(verdicts) == 2
    # every verdict carries (and the rule engine's Eq-join branches on) the SAME
    # perlocutionary_goal the intent itself carries -- the check is keyed on the GOAL, not
    # a bare cost/score the two branches happen to agree on.
    for v in verdicts:
        assert v["perlocutionary_goal"] == "hearer_knows"
    # the discriminating field the commit/revise rules Eq-test on is `recoverable`, and it
    # DIFFERS between the two verdicts even though `perlocutionary_goal` is identical on both
    # -- proof the branch is a function of recoverability-toward-that-goal, not the goal label
    # itself and not a re-derived cost.
    assert {v["recoverable"] for v in verdicts} == {True, False}


# ===========================================================================
# 6. COMMIT GATE — nothing is emitted/committed until the monitor clears it.
# ===========================================================================
def test_commit_gate_blocks_until_monitored():
    ag = _fresh_agent()
    _ground_all(ag, "cim_gate")
    g = cc.mint_communicative_goal(
        ag, "inform", MEANING, {"id": "gate_audience", "observed": True, "known_concepts": SHARED})
    ag.inner.run_rules(2000)

    # formed the intent, but never shaped/formulated/monitored -- no Committed node anywhere.
    assert cc.read_committed(ag, g)["committed"] is None
    assert list(ag.s.nodes("Committed")) == []

    # shape it (formulate), tick, but DO NOT monitor -- still no Committed node: the shape
    # existing is not enough, only a cleared Verdict commits.
    cc.scan_and_conceptualize(ag, LEXICON)
    ag.inner.run_rules(2000)
    assert cc.read_committed(ag, g)["committed"] is None, "an un-monitored intent has no Committed utterance"

    # now monitor -- a recoverable verdict clears the gate.
    cc.scan_and_monitor(ag, LEXICON)
    ag.inner.run_rules(2000)
    committed = cc.read_committed(ag, g)
    assert committed["committed"] is not None, "a monitored (recoverable) intent DOES have a Committed utterance"
    assert committed["utterance"]


# ===========================================================================
# 7. NO PYTHON DECISION — source audit (extends phase 1's audit to the new
#    functions: scan_and_monitor / run_pipeline / read_committed).
# ===========================================================================
_ALLOWED_IF_PATTERNS = [
    re.compile(r"if native is None:"),
    re.compile(r"if ag_node is None:"),
    re.compile(r"if not sub\.node\(n\)\[.attrs.\]\.get\(.is_class.\):"),
    re.compile(r"if sub\.node\(n\)\[.attrs.\]\.get\(.id.\) == _SEED_ID:"),
    re.compile(r"if hub is not None:"),
    re.compile(r"if ag_node is not None:"),
    re.compile(r"if at\.get\(.status.\) != .requested.:"),
    re.compile(r"if intent is None:"),
    re.compile(r"if bundle\[.system_model.\] is not None:"),
    re.compile(r"if shape_node is not None else"),
    re.compile(r"if committed_node is not None else"),
    re.compile(r"if intent_node is None:"),
    re.compile(r"if not utterance:"),
    re.compile(r"if __name__"),
]


def test_no_python_decision_source_audit():
    """Grep `domains/conceptualizer.py`: every `if` present is mechanical bookkeeping (None-
    guards, a re-scan idempotency skip, an empty-utterance decode guard) — never a decision
    that picks recoverable/revise/commit from graph state. Those come from `scan_and_monitor`'s
    reused set-algebra (`audience_driven_production`/`language.comprehend`, already-approved,
    read-only) feeding a `Verdict.recoverable` boolean, and `commit_if_recoverable_<tag>` /
    `revise_if_not_recoverable_<tag>` (an Eq-join over that boolean, entirely in the rule
    engine) — never a new Python conditional in this module."""
    path = os.path.join(ROOT, "domains", "conceptualizer.py")
    with open(path) as f:
        lines = f.readlines()
    offending = []
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if not re.match(r"^\s*if\b.*:$", line.rstrip()):
            continue
        if any(p.search(stripped) for p in _ALLOWED_IF_PATTERNS):
            continue
        offending.append((i, stripped))
    assert offending == [], f"unexpected conditional(s) in conceptualizer.py: {offending}"
    text = "".join(lines)
    assert "elif" not in text
    assert re.search(r'"force"\s*:\s*"', text) is None, "force must never be a Python literal"
    assert re.search(r'"perlocutionary_goal"\s*:\s*"', text) is None
    assert re.search(r'"recoverable"\s*:\s*(True|False)\s*[,}]', text) is None, \
        "recoverable must never be a Python literal — only the computed boolean"


def test_conceptualizer_never_imports_python_rule_engine():
    path = os.path.join(ROOT, "domains", "conceptualizer.py")
    with open(path) as f:
        text = f.read()
    for forbidden in ("graph_rewrite", "gr.make_rule", "gr.run", "gr._match", "gr._apply"):
        assert forbidden not in text

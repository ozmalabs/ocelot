"""test_proposition_beliefs_migrated — BLIND-SPOT CLOSURE R9 (proposition-
grain belief content, 2026-07-12).

Today a modeled Level-2 belief/goal is HEAD-GRAIN: "I think the new
scheduler is faster" grounds a nested belief-world SmEntity named per
(character, referent-HEAD) — `referent == "new_scheduler"` — so
`reflective_faculty._run_interlocutor_model` renders "I model you as likely
believing new_scheduler" instead of the FULL proposition the reader's own
clause parse already produced (`read_clause` grounds
`["is_a", "new_scheduler", "faster"]` for the complement — the whole triple
was sitting right there).

THE CLOSURE: `character_tom._nested_entity`/`_ground_attitude_complement`
mechanically stamp the complement's FULL predication (`proposition`, json)
and verbatim span (`proposition_span`, "the new scheduler is faster") onto
the Level-2 node — unconditional mechanical mint, the same discipline
`situation_model_reader.ingest_predication` already uses for every other
node attr. A graph RULE (`mark_attitude_proposition_capture`,
seeds/proposition_capture.json) is the DECISION surface: it flags the node
`proposition_capture=1` once it carries a `proposition_span`; the render
prefers the full proposition ONLY when that flag is set, so ablating the
rule reverts every render to the pre-closure head-grain text even though the
richer data is still sitting on the node.
"""
from __future__ import annotations

import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from substrate.world_adapter import WorldAdapter                       # noqa: E402
from substrate.boot_all import load_all_seeds                          # noqa: E402
from domains import character_tom as ctom                              # noqa: E402
from domains.reflective_faculty import reflect                         # noqa: E402

jd = pytest.importorskip("jabberwock_daemon")


def _agent():
    a = WorldAdapter(seeds=(), shadow_read=True)
    load_all_seeds(a)
    return a


def _active_party(a):
    for n in a.s.nodes("Interlocutor"):
        if a.s.node(n)["attrs"].get("active"):
            return n
    return None


def _level2_for(a, party_name, *, kind="belief"):
    if kind == "desire":
        for n in a.s.nodes("SmEvent"):
            at = a.s.node(n)["attrs"]
            if at.get("verb") == "want" and at.get("idx_protagonist") == party_name:
                return n, at
        return None, None
    for n in a.s.nodes("SmEntity"):
        at = a.s.node(n)["attrs"]
        if at.get("nested") and at.get("belief_holder") == party_name:
            return n, at
    return None, None


def _has_rule(a, name):
    return any(r.get("name") == name for r in a.inner.export_rules())


# --------------------------------------------------------------------------- #
#  THE CLOSURE: the Level-2 node carries the FULL proposition.
# --------------------------------------------------------------------------- #
def test_belief_level2_carries_full_proposition():
    a = _agent()
    a.converse("Hi, I'm Uma.", speech_act="statement")
    a.converse("I think the new scheduler is faster.", speech_act="statement")
    n, at = _level2_for(a, "Uma")
    assert n is not None, "the reused character_tom construction must mint the nested belief"
    assert at.get("referent") == "new_scheduler", "head-grain field stays byte-identical"
    assert at.get("proposition_capture") == 1.0, at
    prop = json.loads(at.get("proposition"))
    assert prop == ["is_a", "new_scheduler", "faster"], prop
    assert at.get("proposition_span") == "the new scheduler is faster", at


def test_desire_level2_also_carries_the_full_proposition():
    a = _agent()
    a.converse("Hi, I'm Hank.", speech_act="statement")
    a.converse("I want the daemon to be faster.", speech_act="statement")
    n, at = _level2_for(a, "Hank", kind="desire")
    assert n is not None
    assert at.get("proposition_capture") == 1.0, at
    assert at.get("proposition_span"), at
    assert "daemon" in at["proposition_span"] and "faster" in at["proposition_span"], at


# --------------------------------------------------------------------------- #
#  THE RENDER: full proposition, not the bare head.
# --------------------------------------------------------------------------- #
def test_interlocutor_model_renders_the_full_proposition():
    a = _agent()
    a.converse("Hi, I'm Uma.", speech_act="statement")
    a.converse("I think the new scheduler is faster.", speech_act="statement")
    state = reflect("interlocutor_model", None, a.s)
    assert state["known"] is True
    b = state["beliefs"][0]
    assert b["modeled_content"] == "the new scheduler is faster", b
    assert "believing the new scheduler is faster" in state["note"], state["note"]
    assert "believing new_scheduler" not in state["note"], state["note"]


def test_live_daemon_shaped_transcript_renders_full_proposition():
    a = _agent()
    a.converse("Hi, I'm Uma.", speech_act="statement")
    a.converse("I think the new scheduler is faster.", speech_act="statement")
    a.converse("I want the tests to run in parallel.", speech_act="statement")
    reply = a.converse("What do you know about me?", speech_act="question")
    assert "You said" in reply
    assert "the new scheduler is faster" in reply, reply


# --------------------------------------------------------------------------- #
#  PARITY — untouched surfaces stay byte-identical.
# --------------------------------------------------------------------------- #
def test_hedged_confidence_math_unaffected():
    """The confidence computation (reliability * hedge discount) reads
    nothing this closure touches; only `modeled_content`'s SOURCE field
    changed."""
    a = _agent()
    a.converse("Hi, I'm Kim.", speech_act="statement")
    a.converse("I think the moon is made of cheese.", speech_act="statement")
    n, at = _level2_for(a, "Kim")
    plain_conf = at.get("confidence")
    a2 = _agent()
    a2.converse("Hi, I'm Lin.", speech_act="statement")
    a2.converse("I think, maybe, the moon is made of cheese.", speech_act="statement")
    n2, at2 = _level2_for(a2, "Lin")
    hedged_conf = at2.get("confidence")
    assert plain_conf is not None and hedged_conf is not None
    assert hedged_conf < plain_conf


def test_sally_anne_narrative_reading_unaffected():
    """character_tom's own narrative reading path (tests/test_character_tom.py's
    18-case suite is the full regression gate; this is a spot check the SAME
    nested-belief-world semantics survive the new attrs being present)."""
    from substrate.boot_core import boot_core

    class _A:
        def __init__(self, s, node):
            self.s = s
            self.inner = s._inner
            self.agent = node

    s, node = boot_core()
    a = _A(s, node)
    text = "Sally thinks the ball is in the basket. The ball is in the box."
    out = ctom.read_character_tom(a, text)
    kinds = [r["kind"] for r in out["results"]]
    assert kinds == ["attitude", "factual"]
    belief = ctom.character_belief_world(a, "sally")
    assert belief["ball"].get("in_basket") == 1
    assert "in_box" not in belief["ball"]
    # the new attrs are present but additive -- they never displace the
    # existing head-grain semantics character_belief_world's callers rely on.
    assert "proposition" in belief["ball"] or "proposition_span" in belief["ball"]


# --------------------------------------------------------------------------- #
#  CLOSURE PROOF (agent-in-control): ablating the rule reverts to the OLD
#  head-grain render, even though the richer data is still on the node.
# --------------------------------------------------------------------------- #
def test_ablating_the_rule_reverts_to_head_grain_render():
    a = _agent()
    a.converse("Hi, I'm Uma.", speech_act="statement")
    assert _has_rule(a, "mark_attitude_proposition_capture")
    idx = None
    for i, r in enumerate(a.inner.export_rules()):
        if isinstance(r, dict) and r.get("active", True) and \
                r.get("name") == "mark_attitude_proposition_capture":
            idx = i
            break
    assert idx is not None, "the rendering-eligibility decision must be a live, removable rule"
    assert a.inner.remove_rule(idx) is True

    a.converse("I think the new scheduler is faster.", speech_act="statement")
    n, at = _level2_for(a, "Uma")
    # the mechanical mint is UNCHANGED by ablating the rule -- the data is
    # still there, just never marked eligible.
    assert at.get("proposition_span") == "the new scheduler is faster", at
    assert at.get("proposition_capture") is None, (
        "ablating the rule must mean the eligibility flag is never set", at)

    state = reflect("interlocutor_model", None, a.s)
    b = state["beliefs"][0]
    assert b["modeled_content"] == "new_scheduler", (
        "ablating the rule must revert the RENDER to head-grain, not just weaken it", b)
    assert "believing new_scheduler" in state["note"], state["note"]
    # the Level-1 verbatim quote ("You said: ...") still legitimately contains
    # the full sentence -- only the Level-2 MODELED clause must revert.
    assert "believing the new scheduler is faster" not in state["note"], state["note"]


# --------------------------------------------------------------------------- #
#  Seed structure + canon round-trip + refreshability.
# --------------------------------------------------------------------------- #
def test_seed_structure_and_canon_round_trip():
    d = json.load(open(os.path.join(ROOT, "seeds", "proposition_capture.json")))
    assert d["depends_on"] == []
    names = {r["name"] for r in d["rules"]}
    assert names == {"mark_attitude_proposition_capture"}
    assert d["id"] in jd._REFRESHABLE_SEEDS
    for r in d["rules"]:
        body = jd._canon_rule_body(r)
        assert body, "must round-trip through the Rust rule serializer cleanly"


def test_boot_installs_proposition_capture_idempotently():
    a = _agent()
    a.converse("Hi, I'm Zed.", speech_act="statement")
    r1 = len(a.inner.export_rules())
    a.converse("I think the sky is blue.", speech_act="statement")
    ctom.ensure_seeds(a)
    ctom.ensure_seeds(a)
    r2 = len(a.inner.export_rules())
    names = [r.get("name") for r in a.inner.export_rules()]
    assert names.count("mark_attitude_proposition_capture") == 1


if __name__ == "__main__":
    a = _agent()
    a.converse("Hi, I'm Uma.", speech_act="statement")
    a.converse("I think the new scheduler is faster.", speech_act="statement")
    a.converse("I want the tests to run in parallel.", speech_act="statement")
    print(a.converse("What do you know about me?", speech_act="question"))

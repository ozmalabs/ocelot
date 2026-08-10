"""test_self_process_introspection — OPERATIONAL self-knowledge for "how do you X"
process questions.

THE GAP this closes: the long tail of self-questions DEFLECTED instead of
answering. "How do you learn something new?" -> "I can't say precisely how I
learn." (honest but shallow). The agent IS its own process knowledge as graph
data, but it did not INTROSPECT how it OPERATES — its reflective faculties
answered how it IS (self_organisation / microtheories) and how it is SHAPED
(self_shape / meta-shapes), but not its PROCESSES (learning, perceiving,
world-attachment).

THE FIX: a `self_process` operational-introspection path. A reflexive
"how do you <verb>" process-question the agent HOLDS a true self-account for
(a taught `SelfProcess` node) is routed (comprehend_text `_detect_self_process`
-> the `self_process` reader in domains/self_model.py) to that held account,
rendered through the normal `_surface_self_state` prose path. The accounts are
TAUGHT DATA (scripts/teach_self_processes.py -> seeds/self_processes.json via the
recurring `domains.teach` facility), grounded in the REAL architecture:

  * learning         = the collapse loop  (predict -> surprise/residual -> grow)
  * perceiving       = the sd decode loop (decode against held shapes; residual
                       mints a quantum)
  * world-attachment = the world adapter  (ingest events as graph mutations;
                       run rules; emit)

HONEST FLOOR preserved: a process the agent GENUINELY has no self-account for
(dreaming) keeps the honest "I can't say precisely" — never a fabricated
mechanism.

Every assertion drives the REAL chat path (`agent.answer_question`), the same
discipline test_self_model.py uses.
"""
from __future__ import annotations

import pytest

from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
from domains import self_model as sm


@pytest.fixture(scope="module")
def agent():
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    return a


@pytest.fixture(scope="module")
def agent_no_selfproc():
    """The BEFORE agent: booted WITHOUT the taught self-process accounts (skip the
    self_processes seed) — so it exhibits the OLD honest-floor deflection. This is
    the discriminative control: the substantive answers below come from the HELD
    accounts, not from anything hardcoded in the answer path."""
    a = WorldAdapter(seeds=())
    load_all_seeds(a, skip=("self_processes",))
    return a


# ---------------------------------------------------------------------------
# HEADLINE — "how do you learn" is SUBSTANTIVE (was the deflection). Verbatim
# before -> after.
# ---------------------------------------------------------------------------
def test_learn_before_is_the_deflection(agent_no_selfproc):
    assert agent_no_selfproc.answer_question("How do you learn something new?") == \
        "I can't say precisely how I learn."


def test_learn_after_is_substantive(agent):
    ans = agent.answer_question("How do you learn something new?")
    assert not ans.lower().startswith("i can't say precisely")     # NOT the deflection
    assert "hold the rule" not in ans                              # NOT the machinery dump
    assert "organised into" not in ans                            # NOT the domain list


def test_learn_short_form_also_substantive(agent):
    ans = agent.answer_question("How do you learn?")
    assert not ans.lower().startswith("i can't say precisely")
    assert len(ans) > 80                                           # a real account, not a stub


# ---------------------------------------------------------------------------
# TRUTHFUL / GROUNDED — the answer reflects the REAL architecture (taught from
# it, not invented): learning = the collapse loop (predict / surprise-where-wrong
# / grow-to-explain); world-attachment = the adapter ingesting events as graph
# mutations.
# ---------------------------------------------------------------------------
def test_learn_answer_is_the_collapse_loop(agent):
    ans = agent.answer_question("How do you learn?").lower()
    assert "collapse" in ans
    assert "predict" in ans
    assert "surprise" in ans or "residual" in ans
    assert "grow" in ans and "graph" in ans


def test_second_process_world_attach_is_substantive_and_grounded(agent):
    ans = agent.answer_question("How does a world attach to you?")
    assert not ans.lower().startswith("i can't say precisely")
    low = ans.lower()
    assert "adapter" in low
    assert "ingest" in low
    assert "graph" in low


def test_third_process_perceive_is_substantive_not_machinery_dump(agent):
    # 'how do you perceive?' used to fast-path to the self_design MACHINERY DUMP
    # ('I modify the rule, hold the rule ...'); now it reads the true self-account.
    ans = agent.answer_question("How do you perceive?")
    assert not ans.lower().startswith("i can't say precisely")
    assert "hold the rule" not in ans
    assert "decod" in ans.lower()


# ---------------------------------------------------------------------------
# TEACH-PERSISTENCE — the self-fact survives a REBOOT (it was persisted to a
# seed by teach(); a fresh load_all_seeds boot re-reads it from disk and the
# agent still holds it and answers substantively).
# ---------------------------------------------------------------------------
def test_self_process_persisted_across_reboot():
    fresh = WorldAdapter(seeds=())
    load_all_seeds(fresh)                                          # a brand-new boot from disk
    held = {fresh.s.node(n)["attrs"].get("process") for n in fresh.s.nodes("SelfProcess")}
    assert {"learning", "perceiving", "world_attachment"} <= held
    ans = fresh.answer_question("How do you learn?")
    assert "collapse" in ans.lower()


# ---------------------------------------------------------------------------
# HONEST FLOOR preserved — a process the agent GENUINELY has no self-account for
# stays the honest deflection (never a fabricated mechanism). Discriminative: it
# is NOT a self-account, NOT the machinery dump, NOT the domain list.
# ---------------------------------------------------------------------------
def test_honest_floor_preserved_for_genuine_gap(agent):
    ans = agent.answer_question("How do you dream?")
    assert ans == "I can't say precisely how I dream."


def test_find_self_process_is_honest_for_absent_process(agent):
    # the boundary classifier only fires on a genuinely-held account.
    assert sm.find_self_process(agent.s, {"how", "do", "you", "dream"}) is None
    assert sm.find_self_process(agent.s, {"how", "do", "you", "learn"}) == "learning"


def test_reader_is_honest_when_key_unheld(agent):
    st = sm.run_self_process(agent.s, "dream")
    assert st.get("found") is False
    assert st.get("note", "").lower().startswith("i can't say precisely")


# ---------------------------------------------------------------------------
# NO REGRESSION — the how-it-IS / how-it's-SHAPED / identity / rule self-model
# answers are UNCHANGED by the new operational path.
# ---------------------------------------------------------------------------
def test_self_organisation_unchanged(agent):
    ans = agent.answer_question("How are you organised?")
    assert "organised into" in ans.lower()


def test_self_structure_still_reaches_self_organisation(agent):
    ans = agent.answer_question("can you describe how you're put together?")
    assert "organised into" in ans.lower()


def test_self_shape_unchanged(agent):
    ans = agent.answer_question("What shape are you?")
    assert "meta-shape" in ans.lower() or "meta shape" in ans.lower()


def test_self_identity_unchanged(agent):
    ans = agent.answer_question("What are you?")
    assert isinstance(ans, str) and ans.strip()
    assert not ans.lower().startswith("i can't say precisely")

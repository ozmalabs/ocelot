"""CLAUSE-GRAIN COMPREHENSION ANALYSIS (2026-07-12).

A real article sentence is multi-clause and RUN-ON; a single whole-sentence
read mangles it, so the passive/agent-deletion annotators only ever saw the
FIRST clause. The reading pipeline now persists the parser's (graph-native,
lattice-decoded) clause recognition as first-class `ClauseParse` graph nodes at
ingest (`sp -has_clause-> cp`, `clause_words` = the lattice-decoded word-list),
and the meaning_inference re-read stage iterates those nodes -- reading each
clause's word-list STRAIGHT through read_clause's word-list path (tokenization
happens exactly once, graph-native, at ingest; never re-run on a re-joined
string). Clauses are read BEFORE the whole-sentence fallback so the precise
per-clause fact wins the annotators' (verb,patient) idempotency.

These gates lock in:
 1. a run-on sentence decomposes into ClauseParse graph nodes;
 2. passive/agent-deletion analysis fires on EVERY clause (not just the first);
 3. the by-phrase agent of a later clause is captured (AGENT NAMED), while a
    genuinely agentless later clause stays AGENT DELETED -- the clause-first
    read order is what makes the precise reading win.

All decisions stay in the seeded rules the annotators load; this file only
drives read_and_comprehend and reads graph state back out.

Run: PYTHONPATH=runners/dsl/python:.:scripts OZMA_NO_LLM=1 python3 -m pytest \
    tests/test_clause_grain_analysis_migrated.py -p no:randomly -q
"""
from __future__ import annotations

import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from substrate.boot_core import boot_core            # noqa: E402
from domains import dictionary_lexicon as dl          # noqa: E402
from domains import comprehension_reader as cr        # noqa: E402


class _Agent:
    def __init__(self, s, node):
        self.s = s
        self.inner = s._inner
        self.agent = node


@pytest.fixture()
def agent():
    dl.warm_wordnet("en")
    s, node = boot_core()
    return _Agent(s, node)


def _clauses_of(a):
    """Every SentenceParse's recognised clause texts, as a flat list."""
    out = []
    for sp in a.s.nodes("SentenceParse"):
        for cp in a.s.neighbours(sp, "has_clause"):
            out.append(a.s.node(cp)["attrs"].get("clause_text"))
    return out


def _passives(a):
    rows = []
    for pp in a.s.nodes("PassivePredication"):
        at = a.s.node(pp)["attrs"]
        rows.append((at.get("verb"), at.get("patient"),
                     at.get("agent") or "", float(at.get("agent_filled") or 0.0)))
    return rows


# --------------------------------------------------------------------------- #
#  1. run-on -> ClauseParse graph nodes
# --------------------------------------------------------------------------- #
def test_run_on_sentence_decomposes_into_clause_parse_nodes(agent):
    cr.read_and_comprehend(
        agent,
        "The village was destroyed and hundreds were displaced, "
        "though the ministry insisted no order had been given.")
    clauses = _clauses_of(agent)
    # three recognised clauses from the one run-on sentence
    assert "the village was destroyed" in clauses, clauses
    assert "hundreds were displaced" in clauses, clauses
    assert any("ministry" in (c or "") for c in clauses), clauses


# --------------------------------------------------------------------------- #
#  2. passive analysis fires on EVERY clause, not just the first
# --------------------------------------------------------------------------- #
def test_passive_analysis_fires_on_later_clauses(agent):
    cr.read_and_comprehend(
        agent,
        "The findings were suppressed, but the report was leaked "
        "and the emails were published.")
    verbs = {v for (v, _p, _a, _f) in _passives(agent)}
    # the first clause's passive alone would give only {suppress}; later
    # clauses must contribute their own passives.
    assert "suppress" in verbs, verbs
    assert "publish" in verbs, verbs
    assert len(verbs) >= 2, verbs


# --------------------------------------------------------------------------- #
#  3. by-agent capture vs agent-deletion, discriminated per clause
# --------------------------------------------------------------------------- #
def test_by_agent_of_later_clause_is_captured_not_deleted(agent):
    # In ONE run-on sentence: the clause carrying a by-phrase reads AGENT NAMED,
    # while a genuinely agentless later clause reads AGENT DELETED. The leading
    # "but" of the second clause is dropped (contrast-coordinator MarkerClass +
    # the leading-coordinator drop), so the patient is clean "emails", not
    # "but_emails".
    cr.read_and_comprehend(
        agent,
        "The findings were suppressed by the committee, "
        "but the emails were published.")
    by_patient = {p: (a, f) for (_v, p, a, f) in _passives(agent)}
    # "suppressed by the committee" -> agent NAMED (clause-first read wins the
    # precise by-phrase reading over the whole-sentence agent-blind mangle).
    assert "findings" in by_patient, by_patient
    agent_name, filled = by_patient["findings"]
    assert filled == 1.0, by_patient
    assert agent_name == "committee", by_patient
    # "the emails were published" -> genuinely agentless: AGENT DELETED, and the
    # leading "but" did NOT leak into the patient.
    assert "emails" in by_patient, by_patient
    assert "but_emails" not in by_patient, by_patient
    assert by_patient["emails"][1] == 0.0, by_patient


def test_leading_contrast_coordinator_is_dropped_from_clause(agent):
    # A leading 'but' opening an independent clause after a comma is dropped as
    # opener glue (contrast-coordinator MarkerClass, leading-drop) -- while an
    # intra-clause contrast keeps its 'but' (disclaimer cue survives).
    from domains import reading_collapse as rc
    clauses = [" ".join(c) for c in
               (rc.decompose_sentence(agent,
                "The report failed, but the appeal was granted.") or {}).get("clauses") or []]
    assert "the appeal was granted" in clauses, clauses
    assert not any(c.startswith("but ") for c in clauses), clauses
    # intra-clause contrast is preserved whole (mid-clause 'but' left alone).
    whole = [" ".join(c) for c in
             (rc.decompose_sentence(agent, "He was not angry but calm.") or {}).get("clauses") or []]
    assert whole == ["he was not angry but calm"], whole


# --------------------------------------------------------------------------- #
#  4. a single-clause sentence yields exactly one ClauseParse (no change)
# --------------------------------------------------------------------------- #
def test_single_clause_sentence_has_one_clause_parse(agent):
    cr.read_and_comprehend(agent, "The report was buried.")
    clauses = _clauses_of(agent)
    assert clauses == ["the report was buried"], clauses


def test_conflicting_goals_auto_fires_on_read(agent):
    # The disclaimer goal layer fires on a plain read_and_comprehend with NO
    # per-analysis teach: the default DisclaimerCue codebook + method self-load,
    # and the agent AUTHORS the classify-by-join rule from the held method.
    from domains import actor_goals as ag
    cr.read_and_comprehend(agent, "I am not racist, but I do not want them here.")
    readings = ag.held_conflicting_goals(agent)
    assert any(r["phrase"] == "not racist but" for r in readings), readings


def test_plain_read_flags_no_conflicting_goals(agent):
    from domains import actor_goals as ag
    cr.read_and_comprehend(agent, "The council approved the budget on Tuesday.")
    assert ag.held_conflicting_goals(agent) == []


def test_auto_fire_authors_the_rule_never_ships_it(agent):
    # The auto-fire path must still author the rule (not ship it) -- the same
    # invariant the per-analysis suite guards.
    import json
    import pathlib
    cr.read_and_comprehend(agent, "With all due respect, that plan is wrong.")
    seeds = pathlib.Path(__file__).resolve().parent.parent / "seeds"
    for p in seeds.glob("*.json"):
        try:
            m = json.loads(p.read_text())
        except Exception:
            continue
        # `seeds/` holds one git-tracked file whose JSON root is a bare LIST of
        # rule objects, not a manifest (`_recovered_f16_rules.json`), and
        # `boot_all._read_seeds` SKIPS it (`if not isinstance(d, dict): continue`)
        # — so the agent never boots with it and it ships nothing. This scan did
        # not guard, and raised `'list' object has no attribute 'get'`. MATCH THE
        # LOADER: what a gate over seeds/ means is what the loader loads.
        if not isinstance(m, dict):
            continue
        for r in m.get("rules", []) or []:
            for eff in r.get("effects", []) or []:
                if isinstance(eff, list) and len(eff) >= 3 and \
                        eff[0] == "add_node" and eff[2] == "ConflictingGoalsReading":
                    raise AssertionError(f"a ConflictingGoalsReading rule ships in {p.name}")


def test_surface_inversion_auto_fires_on_read(agent):
    from domains import actor_goals as ag
    cr.read_and_comprehend(agent, "He repeated the disgusting notion that they are inferior.")
    readings = ag.held_surface_inversions(agent)
    assert any(r["phrase"] == "the disgusting notion that" for r in readings), readings


def test_temporal_and_trope_auto_fire_on_read(agent):
    from domains import actor_goals as ag
    cr.read_and_comprehend(
        agent,
        "The technology was funded by the oil company. "
        "The technology was opposed by the oil company.")
    temporal = ag.held_temporal_conflicts(agent)
    assert any(r["pair_key"] == "fund|oppose" for r in temporal), temporal
    tropes = ag.held_trope_readings(agent)
    assert any(r["trope"] == "Trojan Horse" for r in tropes), tropes


def test_partitive_quantifier_subject_keeps_the_passive(agent):
    # 'hundreds of protesters were detained' -- the collective-quantifier
    # partitive ('hundreds OF') is glue on the quantified noun phrase, so the
    # clause reads as the passive on that phrase, NOT an OF-attributive that
    # swallows the verb (the pre-fix behaviour lost 'detained' entirely).
    from domains import reading_collapse as rc
    out = rc.read_clause(agent, ["hundreds", "of", "protesters", "were", "detained"], write=True)
    assert out.get("construction") == "passive", out
    preds = out.get("predications") or []
    assert preds and preds[0][0] == "detain", preds
    # a bare SVO with a partitive subject also keeps its verb.
    out2 = rc.read_clause(agent, ["thousands", "of", "people", "fled", "the", "city"], write=True)
    assert out2.get("construction") == "event", out2
    assert (out2.get("predications") or [[None]])[0][0] == "fled", out2

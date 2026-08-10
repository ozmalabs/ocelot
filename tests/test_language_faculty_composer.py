"""test_language_faculty_composer — the composer AUTHORS a LANGUAGE-FACULTY Program.

The prior consumption-quality fix filtered clause fragments with ADAPTER LOGIC
(consumption_quality.is_nominal) "because the composer does not yet author a
POS-Program." This closes that frontier: the jabberwock, from a framed LANGUAGE
concern ("keep only nominal spans"), AUTHORS the nominal-filter Program ITSELF via
the composer (induce_concern -> ground_concern -> _compose_language_faculty),
gated by admissibility_gate + #2 self_verification, and it WORKS — the SAME
fragment-drop the adapter is_nominal got, now COMPOSER-AUTHORED.

  LEAF EQUIVALENCE : the graph-resident nominal-head Term reproduces is_nominal
                     exactly on the labelled control (clause fails, nominal passes).
  WALL PROVEN      : "keep only nominal spans" grounds to NOTHING before this build
                     (minimal seed set, no language cue) — the composer can't reach it.
  AUTHORS PROGRAM  : with the language cue, the composer authors the nominal-filter
                     Program (a Filter chaining the nominal-head leaf), installed.
  VERIFY-GATED     : the authored Program passed #2 (discriminative; keep-everything
                     twin FAILS); a FAKE (keep-everything) is REJECTED.
  IT WORKS         : the authored Program drops the Photosynthesis clause fragments +
                     keeps the nominals — byte-identical to the adapter is_nominal.

Donkey=0 — no LM. The nominal decision is the graph Term the composer authored; the
POS LOOKUP that measures a span's features is the honest held-faculty call boundary.
"""
from __future__ import annotations

import io
import contextlib

import pytest

from domains import language_faculty_ops as lfo
from domains import consumption_quality as cq


# ---------------------------------------------------------------------------
# agents: a MINIMAL one (no language cue -> the wall) and a FULL one (all seeds).
# ---------------------------------------------------------------------------
def _wall_agent():
    """A minimal agent with the RelationCue lexicon + composer dispatch but WITHOUT
    the language_faculty_cue seed — the pre-build state the wall is proven against."""
    buf = io.StringIO()
    with contextlib.redirect_stderr(buf):
        from substrate.world_adapter import WorldAdapter
        from substrate.seed_loader import manifest_for
        a = WorldAdapter(seeds=())
        a.inner.load_seed_manifest(manifest_for("relation_vocabulary"), a.agent)
        a.inner.load_seed_manifest(manifest_for("composer_dispatch"), a.agent)
    return a


def _author_agent():
    """The minimal agent PLUS the language_faculty_cue seed — this build's addition."""
    buf = io.StringIO()
    with contextlib.redirect_stderr(buf):
        a = _wall_agent()
        from substrate.seed_loader import manifest_for
        a.inner.load_seed_manifest(manifest_for(lfo.LANGUAGE_FACULTY_CUE_SEED), a.agent)
    return a


@pytest.fixture(scope="module")
def full_agent():
    buf = io.StringIO()
    with contextlib.redirect_stderr(buf):
        from substrate.world_adapter import WorldAdapter
        from substrate.boot_all import load_all_seeds
        a = WorldAdapter(seeds=())
        load_all_seeds(a)
    return a


_CONCERN = [["filter", "keep", "NOMINAL", "spans"], ["nominal", "SPAN", "by", "HEAD"]]


def _wiki_present() -> bool:
    try:
        from domains import wiki_local as wl
        return wl.present()
    except Exception:
        return False


# ===========================================================================
# LEAF — the graph-resident nominal-head Term reproduces is_nominal exactly.
# ===========================================================================

def test_nominal_head_leaf_matches_is_nominal():
    prog = lfo.nominal_filter_program()
    cases = [s for s, _ in cq.NOMINAL_CONTROL] + [s for s, _ in cq.NOMINAL_PRIOR]
    keeps = lfo.run_filter_program(prog, cases)
    for surface, keep in zip(cases, keeps):
        assert keep == cq.is_nominal(surface), surface
    # discriminative: every clause fragment drops, every nominal keeps.
    verdict = dict(zip([s for s, _ in cq.NOMINAL_CONTROL],
                       lfo.run_filter_program(prog, [s for s, _ in cq.NOMINAL_CONTROL])))
    for surface, expected in cq.NOMINAL_CONTROL:
        assert verdict[surface] is expected, (surface, expected)


def test_keep_everything_fake_keeps_all():
    fake = lfo.keep_everything_program()
    cases = [s for s, _ in cq.NOMINAL_CONTROL]
    assert all(lfo.run_filter_program(fake, cases))   # no teeth: keeps every fragment


# ===========================================================================
# WALL — "keep only nominal spans" grounds to NOTHING before this build.
# ===========================================================================

def test_wall_concern_grounds_to_nothing_without_the_cue():
    from domains import reflective_faculty as rf
    a = _wall_agent()
    ind = rf.induce_concern(a, _CONCERN, name_hint="nf_wall")
    assert ind.get("minted") is True
    g = rf.ground_concern(a, [ind["capability_key"]])
    # the composer cannot reach it: the residual predicates ground to no held relation.
    assert g.get("grounded") is False
    assert g.get("path") == "predicate_grounding"
    assert "filter" in str(g.get("residual_predicates")) or "nominal" in str(g.get("residual_predicates"))


# ===========================================================================
# AUTHORS — with the cue, the composer authors the nominal-filter Program.
# ===========================================================================

def test_composer_authors_the_nominal_filter_program():
    from domains import reflective_faculty as rf
    a = _author_agent()
    ind = rf.induce_concern(a, _CONCERN, name_hint="nf_auth")
    assert ind.get("minted") is True
    g = rf.ground_concern(a, [ind["capability_key"]])
    assert g.get("grounded") is True
    assert g.get("path") == "compose_language_faculty"
    assert g.get("program_name") == lfo.NOMINAL_FILTER_PROGRAM
    # the authored artefact is a real Filter Program Term-tree, installed as graph data.
    prog = g.get("program")
    assert isinstance(prog, dict) and prog.get("type") == "Filter"
    assert prog["predicate"]["type"] == "And"   # the nominal-head leaf (And-of-Nots)
    assert rf._load_program(a, lfo.NOMINAL_FILTER_PROGRAM) is not None   # installed live
    # the honest leaf boundary is reported.
    assert "POS LOOKUP" in g.get("held_faculty_call", "")


# ===========================================================================
# VERIFY-GATED — the authored Program passed #2; a FAKE is REJECTED.
# ===========================================================================

def test_authored_program_is_verify_gated():
    from domains import reflective_faculty as rf
    a = _author_agent()
    ind = rf.induce_concern(a, _CONCERN, name_hint="nf_verify")
    g = rf.ground_concern(a, [ind["capability_key"]])
    v = g.get("verified") or {}
    assert v.get("accepted") and v.get("discriminates") and v.get("grounded")
    assert v.get("twin_pass") is False   # the keep-everything twin FAILS the control
    assert "ADMITTED" in g.get("gate_reason", "")   # admissibility gate admitted it


def test_keep_everything_fake_rejected_by_number_two(full_agent):
    from domains import self_verification as sv

    def fake_keep_all(case):
        _surface, expected = case
        return True == expected   # keeps everything -> wrong on every fragment

    v = sv.verify_claim(full_agent, sv.Claim(
        "FAKE keep-everything language filter", mechanism=fake_keep_all,
        control_cases=cq.NOMINAL_CONTROL, fake_twin=fake_keep_all,
        prior_cases=cq.NOMINAL_PRIOR, ground_support=cq._ground_reference))
    assert v["accepted"] is False and v["discriminates"] is False


# ===========================================================================
# IT WORKS — the authored Program == the adapter is_nominal on Photosynthesis.
# ===========================================================================

@pytest.mark.skipif(not _wiki_present(), reason="wiki_local slab not present")
def test_authored_program_drops_fragments_keeps_reals(full_agent):
    from domains import gap_driven_acquisition as gda
    buf = io.StringIO()
    with contextlib.redirect_stderr(buf):
        src = gda.read_source(full_agent, "photosynthesis", source_title="Photosynthesis")
        ex = gda.extract_microtheory("photosynthesis", src, max_concepts=40)
    concepts = ex["concepts"]
    # the COMPOSER-AUTHORED Program filter, agent-driven.
    kept_p, dropped_p = cq.nominal_filter_program(full_agent, concepts)
    # the is_nominal adapter reference (the prior fix).
    kept_r, dropped_r = cq.nominal_filter(concepts)
    kp = {c["name"] for c in kept_p}
    dp = {c["name"] for c in dropped_p}
    # byte-identical to the adapter is_nominal — SAME before/after.
    assert kp == {c["name"] for c in kept_r}
    assert dp == {c["name"] for c in dropped_r}
    # the four named clause fragments are DROPPED (verbatim).
    for frag in ["producing_oxygen_gas", "rather_than_water",
                 "releases_three-carbon_sugars", "catalyzed_by_rubisco"]:
        assert frag in dp, frag
    # the real concepts are KEPT (verbatim).
    for real in ["calvin_cycle", "glucose", "carbon_fixation"]:
        assert real in kp, real


def test_nominal_filter_program_authored_idempotent(full_agent):
    # a second author call short-circuits on the held Program (no re-churn).
    from domains import reflective_faculty as rf
    cq.ensure_nominal_filter_program(full_agent)
    rec = cq.ensure_nominal_filter_program(full_agent)
    assert rec.get("already") is True and rec.get("authored") is True
    progs = [n for n in full_agent.s.nodes("Program")
             if full_agent.s.node(n)["attrs"].get("name") == lfo.NOMINAL_FILTER_PROGRAM]
    assert len(progs) == 1   # exactly one installed Program, no duplicate

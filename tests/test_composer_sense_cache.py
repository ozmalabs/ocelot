"""test_composer_sense_cache — the composer AUTHORS the SENSE-select + CACHE-aside
Programs (the last two adapter-side fixes from the cycle-solves-extract build).

Parallel to test_language_faculty_composer (the nominal-filter precedent). Two
frontiers the consumption-quality fix surfaced honestly are closed here — the
jabberwock, from a framed concern, AUTHORS the Program ITSELF via the composer,
admissibility-gated + #2-verified, and it WORKS byte-identical to the adapter.

  SENSE (FIX 1): concern "pick the sense that fits the context" -> the composer
    authors a SELECT Program (Argmax over a word's candidate senses by context-fit
    score). Reproduces dictionary_lexicon.pick_sense's winner byte-identically
    (water -> the SUBSTANCE sense water.n.03, not the Devon hamlet).

  CACHE (FIX 2): concern "cache/memoize this consult" -> the composer authors a
    CACHE-ASIDE serve Program over a graph-resident hot store. A warm repeat is a
    HIT served from the store, byte-identical to the uncached value, faster (timed).

  WALL PROVEN  : each concern grounds to NOTHING before its cue seed (predicate_grounding).
  AUTHORS      : with the cue, the composer authors the Program (installed).
  VERIFY-GATED : #2 accepts (discriminative); the context-blind SENSE twin + the
                 no-store CACHE twin FAIL.

Donkey=0 — no LM. The SCORE+ARGMAX (sense) and the SERVE (cache) are the graph
Terms the composer authored; the WordNet enumeration / underlying lookup + raw
store put are the honest held-faculty call boundary.
"""
from __future__ import annotations

import io
import contextlib
import time

import pytest

from domains import language_faculty_ops as lfo
from domains import memory_faculty_ops as mfo
from domains import consumption_quality as cq


# ---------------------------------------------------------------------------
# agents: a MINIMAL one (no cue -> the wall) and cue-loaded AUTHOR ones.
# ---------------------------------------------------------------------------
def _wall_agent():
    buf = io.StringIO()
    with contextlib.redirect_stderr(buf):
        from substrate.world_adapter import WorldAdapter
        from substrate.seed_loader import manifest_for
        a = WorldAdapter(seeds=())
        a.inner.load_seed_manifest(manifest_for("relation_vocabulary"), a.agent)
        a.inner.load_seed_manifest(manifest_for("composer_dispatch"), a.agent)
    return a


def _author_agent(seed_id):
    buf = io.StringIO()
    with contextlib.redirect_stderr(buf):
        a = _wall_agent()
        from substrate.seed_loader import manifest_for
        a.inner.load_seed_manifest(manifest_for(seed_id), a.agent)
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


_SENSE_CONCERN = [["disambiguate", "pick", "SENSE", "by", "context"],
                  ["sense", "WORD", "fits", "meaning"]]
_CACHE_CONCERN = [["cache", "memoize", "a", "consult"],
                  ["store", "VALUE", "by", "KEY"]]


# ===========================================================================
# SENSE — the leaf reproduces pick_sense; wall; authors; verify-gated; works.
# ===========================================================================

def test_sense_select_leaf_matches_pick_sense():
    prog = lfo.sense_select_program()
    for head, ctx, slot, gold in cq.SENSE_CONTROL + cq.SENSE_PRIOR:
        r = lfo.run_sense_select_program(prog, head, slot, list(ctx))
        assert r is not None, head
        gloss = (r.get("sense") or "").lower()
        assert any(g in gloss for g in gold), (head, r.get("synset"), gloss)
    # water -> the SUBSTANCE sense, byte-identical to sense_in_context.
    ref = cq.sense_in_context("water", "strip electrons from suitable substances such as water")
    got = lfo.run_sense_select_program(
        prog, "water", "patient",
        cq.context_words("strip electrons from suitable substances such as water"))
    assert got["synset"] == ref["synset"] == "water.n.03"


def test_sense_blind_twin_gets_context_cases_wrong():
    blind = lfo.sense_select_blind_program()

    def fits(program, case):
        head, ctx, slot, gold = case
        r = lfo.run_sense_select_program(program, head, slot, list(ctx))
        g = (r.get("sense") or "").lower() if r else ""
        return any(k in g for k in gold)

    # the context-blind twin fails a context-dependent case (mole / cell).
    misses = [c[0] for c in cq.SENSE_CONTROL if not fits(blind, c)]
    assert misses, "the context-blind twin must miss at least one context case"


def test_sense_wall_grounds_to_nothing_without_the_cue():
    from domains import reflective_faculty as rf
    a = _wall_agent()
    ind = rf.induce_concern(a, _SENSE_CONCERN, name_hint="sense_wall")
    assert ind.get("minted") is True
    g = rf.ground_concern(a, [ind["capability_key"]])
    assert g.get("grounded") is False
    assert g.get("path") == "predicate_grounding"


def test_composer_authors_the_sense_select_program():
    from domains import reflective_faculty as rf
    a = _author_agent(lfo.LANGUAGE_FACULTY_CUE_SEED)
    ind = rf.induce_concern(a, _SENSE_CONCERN, name_hint="sense_auth")
    g = rf.ground_concern(a, [ind["capability_key"]])
    assert g.get("grounded") is True
    assert g.get("path") == "compose_sense_select"
    assert g.get("program_name") == lfo.SENSE_SELECT_PROGRAM
    prog = g.get("program")
    assert isinstance(prog, dict) and prog.get("type") == "Argmax"
    assert rf._load_program(a, lfo.SENSE_SELECT_PROGRAM) is not None
    assert "WordNet SENSE ENUMERATION" in g.get("held_faculty_call", "")


def test_sense_program_is_verify_gated():
    from domains import reflective_faculty as rf
    a = _author_agent(lfo.LANGUAGE_FACULTY_CUE_SEED)
    ind = rf.induce_concern(a, _SENSE_CONCERN, name_hint="sense_verify")
    g = rf.ground_concern(a, [ind["capability_key"]])
    v = g.get("verified") or {}
    assert v.get("accepted") and v.get("discriminates") and v.get("grounded")
    assert v.get("twin_pass") is False   # context-blind twin FAILS the control
    assert "ADMITTED" in g.get("gate_reason", "")


def test_sense_in_context_via_authored_program_byte_identical(full_agent):
    for surf, sent in [("water", "strip electrons from suitable substances such as water"),
                       ("mole", "a skin mole with pigment melanin benign growth lesion"),
                       ("cell", "the cell membrane surrounds the nucleus organelle tissue biology organism")]:
        ref = cq.sense_in_context(surf, sent)                 # boot sense_selection rule
        got = cq.sense_in_context(surf, sent, agent=full_agent)   # authored SELECT program
        assert got == ref, (surf, got, ref)


# ===========================================================================
# CACHE — the leaf serves byte-identically; wall; authors; verify-gated; faster.
# ===========================================================================

_CACHE_SENT = {
    "water": "strip electrons from suitable substances such as water",
    "cell": "the cell membrane surrounds the nucleus organelle tissue biology",
    "mole": "a skin mole with pigment melanin benign growth lesion",
    "glucose": "glucose sugar energy metabolism carbohydrate",
    "volcano": "the volcano erupted lava magma ash eruption",
}


def _sense_leaf(word):
    return cq.sense_in_context(word, _CACHE_SENT[word])


def test_cache_serve_leaf_hit_is_byte_identical():
    serve = mfo.cache_serve_program()
    store = mfo.HotStore()
    for w in _CACHE_SENT:
        cold = _sense_leaf(w)
        filled = mfo.cached_call(serve, store, w, _sense_leaf)   # miss -> compute+store
        assert filled == cold
        warm = mfo.cached_call(serve, store, w, _sense_leaf)     # HIT -> served
        assert warm == cold
    assert store.stats()["hits"] == len(_CACHE_SENT)


def test_no_store_twin_never_hits():
    fake = mfo.never_serve_program()
    store = mfo.HotStore()
    for _ in range(2):
        for w in _CACHE_SENT:
            mfo.cached_call(fake, store, w, _sense_leaf)
    assert store.stats()["hits"] == 0   # a cache with no store has no teeth


def test_cache_wall_grounds_to_nothing_without_the_cue():
    from domains import reflective_faculty as rf
    a = _wall_agent()
    ind = rf.induce_concern(a, _CACHE_CONCERN, name_hint="cache_wall")
    assert ind.get("minted") is True
    g = rf.ground_concern(a, [ind["capability_key"]])
    assert g.get("grounded") is False
    assert g.get("path") == "predicate_grounding"


def test_composer_authors_the_cache_serve_program():
    from domains import reflective_faculty as rf
    a = _author_agent(mfo.MEMORY_FACULTY_CUE_SEED)
    ind = rf.induce_concern(a, _CACHE_CONCERN, name_hint="cache_auth")
    g = rf.ground_concern(a, [ind["capability_key"]])
    assert g.get("grounded") is True
    assert g.get("path") == "compose_memory_faculty"
    assert g.get("program_name") == mfo.CACHE_SERVE_PROGRAM
    prog = g.get("program")
    assert isinstance(prog, dict) and prog.get("type") == "Attr"   # serve = Attr(Pick(Filter(...)))
    assert rf._load_program(a, mfo.CACHE_SERVE_PROGRAM) is not None
    assert "RAW STORE PUT" in g.get("held_faculty_call", "")


def test_cache_program_is_verify_gated():
    from domains import reflective_faculty as rf
    a = _author_agent(mfo.MEMORY_FACULTY_CUE_SEED)
    ind = rf.induce_concern(a, _CACHE_CONCERN, name_hint="cache_verify")
    g = rf.ground_concern(a, [ind["capability_key"]])
    v = g.get("verified") or {}
    assert v.get("accepted") and v.get("discriminates") and v.get("grounded")
    assert v.get("twin_pass") is False   # no-store twin FAILS the control
    assert "ADMITTED" in g.get("gate_reason", "")


def test_authored_cache_warm_faster_than_cold(full_agent):
    gc = cq.GraphGroundingCache(full_agent)
    assert gc.authored
    words = list(_CACHE_SENT)
    seq = words * 4
    # byte-identity: every cached value equals the uncached lookup (checked ONCE,
    # outside the timed loops so recompute cost never pollutes the warm timing).
    for w in words:
        assert gc.sense(w, _CACHE_SENT[w]) == cq.sense_in_context(w, _CACHE_SENT[w])
    # cold: recompute the (expensive) sense lookup every time.
    t0 = time.perf_counter()
    for w in seq:
        cq.sense_in_context(w, _CACHE_SENT[w])
    cold = time.perf_counter() - t0
    # warm: the authored cache-aside serves every repeat from the graph store.
    gc2 = cq.GraphGroundingCache(full_agent)
    for w in words:      # fill
        gc2.sense(w, _CACHE_SENT[w])
    t0 = time.perf_counter()
    for w in seq:
        gc2.sense(w, _CACHE_SENT[w])
    warm = time.perf_counter() - t0
    assert warm < cold, (warm, cold)

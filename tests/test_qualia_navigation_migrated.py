"""Qualia-as-navigation — coherence intuition tests.

See docs/research/psychology_affect/QUALIA_NAVIGATION_COHERENCE_PREREG.md and
scripts/qualia_navigation_measure.py. Commonsense-shared-associate coherence
on the real substrate dynamics, NOT the Mednick free-association RAT.
"""

import sys

sys.path.insert(0, "runners/dsl/python")
sys.path.insert(0, ".")

import substrate_rs as sr
from domains import qualia_navigation as qn


def _coherent_triad():
    """cat/dog/tree -> shared associate 'backyard' (field 3.0), plus a decoy
    'fence' shared by 2 (2.0) and 'symphony' by 1 (1.0)."""
    s = sr.Substrate()
    edges = [("cat", "backyard", 1.0), ("dog", "backyard", 1.0),
             ("tree", "backyard", 1.0), ("cat", "fence", 1.0),
             ("dog", "fence", 1.0), ("cat", "symphony", 1.0)]
    return qn.build_triad(s, ["cat", "dog", "tree"], edges, held_out="backyard")


def _incoherent_triad():
    """3 cues with NO shared target — each -> its own private node (field 1)."""
    s = sr.Substrate()
    edges = [("velvet", "n0", 1.0), ("proton", "n1", 1.0),
             ("ledger", "n2", 1.0)]
    return qn.build_triad(s, ["velvet", "proton", "ledger"], edges,
                          held_out=None)


# ---- CLAIM 1: coherence-before-retrieval, CI-separated ------------------

def test_coherence_before_retrieval_separates():
    coh = qn.coherence_signal(_coherent_triad())
    inc = qn.coherence_signal(_incoherent_triad())
    assert coh["coherence"] > inc["coherence"], (coh, inc)
    assert coh["coherence"] == 3.0
    assert inc["coherence"] == 1.0


def test_coherence_read_does_not_localise():
    """The coherence-before-retrieval read must NOT commit to a node."""
    r = qn.coherence_signal(_coherent_triad())
    assert r["localised"] is None


def test_commitment_dark_pull_lit():
    """Felt pull lit, commitment (identity_field) dark = the hunch."""
    r = qn.coherence_signal(_coherent_triad())
    assert r["pull"] == 3.0
    assert r["commitment"] == 0.0


# ---- CLAIM 2: perturbation reverses (Topolinski) ------------------------

def test_perturbation_drop_edge_reverses():
    t = _coherent_triad()
    before = qn.coherence_signal(t)["coherence"]
    qn.perturb(t, drop_edge=("tree", "backyard"))
    after = qn.coherence_signal(t)["coherence"]
    assert after < before, (before, after)
    assert after == 2.0  # lost one converging cue


def test_perturbation_cue_scale_reverses():
    t = _coherent_triad()
    before = qn.coherence_signal(t)["coherence"]
    qn.perturb(t, cue_scale=0.5)
    after = qn.coherence_signal(t)["coherence"]
    assert after < before
    assert after == 1.5


# ---- CLAIM 3: aperture-graded knows-that -> knows-what ------------------

def test_aperture_coarse_knows_that_fine_knows_what():
    s = sr.Substrate()
    inner = s._inner
    obs_coarse = inner.add_node("Observer",
                                {"name": "c", "grain": {qn.PULL_AXIS: 8.0}})
    obs_fine = inner.add_node("Observer",
                              {"name": "f", "grain": {qn.PULL_AXIS: 0.5}})
    edges = [("cat", "backyard", 1.0), ("dog", "backyard", 1.0),
             ("tree", "backyard", 1.0), ("cat", "p0", 1.0),
             ("dog", "p1", 1.0), ("tree", "p2", 1.0)]
    t = qn.build_triad(s, ["cat", "dog", "tree"], edges, held_out="backyard")
    coarse = qn.localise(t, observer=obs_coarse)
    fine = qn.localise(t, observer=obs_fine)
    # coarse: candidates tie after quotient (no localisation) but raw_peak
    # still signals solvable (knows-THAT).
    assert coarse["localised"] is None
    assert coarse["raw_peak"] > 1.0
    # fine: localises the true associate (knows-WHAT).
    assert fine["localised"] == "backyard"


# ---- CLAIM 4: Metcalfe near/far dissociation ----------------------------

def test_metcalfe_near_localises_true():
    """NEAR: true associate is the clear peak -> warmth localises correctly."""
    t = _coherent_triad()
    assert qn.localise(t)["localised"] == "backyard"


def test_metcalfe_far_false_warmth_on_decoy():
    """FAR (constructed): a decoy wired denser than the true associate ->
    the field peaks on the WRONG node = false-warmth. Demonstrates the
    mechanism produces false-warmth when structure favours a wrong attractor;
    the density is CONSTRUCTED, not an emergent slab property."""
    s = sr.Substrate()
    edges = [("a", "decoy", 1.0), ("b", "decoy", 1.0),  # decoy: 2 cues (2.0)
             ("c", "true_assoc", 1.0)]                    # assoc: 1 cue (1.0)
    t = qn.build_triad(s, ["a", "b", "c"], edges, held_out="true_assoc")
    loc = qn.localise(t)["localised"]
    assert loc == "decoy", loc  # false-warmth on the wrong attractor


# ---- Anti-faking: held-out audit ---------------------------------------

def test_held_out_audit_passes():
    assert qn.assert_held_out(_coherent_triad()) is True


def test_read_functions_take_no_answer_argument():
    import inspect
    for fn in (qn.coherence_signal, qn.localise, qn._convergent_field):
        assert "held_out" not in inspect.signature(fn).parameters


# ---- default == today ---------------------------------------------------

def test_default_equals_today_observer_none():
    """observer=None (default) reads the raw, un-quotiented field — the
    navigator changes nothing about the existing qualia surface when not
    invoked; this asserts the None-aperture read is the plain field."""
    r = qn.coherence_signal(_coherent_triad(), observer=None)
    assert r["field"]["backyard"] == 3.0  # un-quotiented
    assert r["raw_peak"] == r["coherence"] == 3.0

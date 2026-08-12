"""LEARNING-PROGRESS-GATED DECAY + THE COMMIT-NET (seed block 202000).

Runs the mechanical measure (`scripts/learning_progress_measure.py`) and pins
the mechanism-level claims. Every decision under test is a graph RULE under
`run_rules()`; the measure only submits observations and reads attributes.

  * G1  THE NOISY TV — learning-progress-gated attention LEAVES the noisy
        source (interest decays) and stays on the learnable; the RAW-SURPRISE
        falsifier TRAPS on the noise (able to fail: a gated arm that keeps
        noisy interest high, or a naive arm that lets it go).
  * G2  LEAVE-THE-UNRESOLVED — decay the RESOLVED and the INTRACTABLE, HOLD the
        progressing; the discriminator is PROGRESS, not surprise-magnitude.
  * G3  COMMIT-NET — the naive/passive arms never terminate (paralysis); the
        calibrated commit cuts at the marginal-value = cost crossing; the
        impulsive arm fires prematurely.
  * G4  INTEGER-NATIVE decay/commit bookkeeping, DEFAULT-OFF byte-identity, and
        a graph-resident source audit (no decision written by Python).

Prereg: VISION_LEARNING_PROGRESS_PREREG.md.
"""
import importlib
import json
import os

import pytest

# OPTIONAL DEPENDENCY (red-test triage 2026-08-12): absent 'matplotlib' is a SKIP with a
# named reason, never a red. See tests/optional_deps.py.
from optional_deps import importorskip as _optional_importorskip  # noqa: E402
_optional_importorskip('matplotlib')


M = importlib.import_module("scripts.learning_progress_measure")


@pytest.fixture(scope="module")
def res():
    M.main()
    with open(os.path.join(M.RESULTS, "learning_progress.json")) as fh:
        return json.load(fh)


def test_G1_noisy_tv(res):
    c = res["criteria"]
    assert c["G1a_gated_leaves_noisy"], res["G1"]
    assert c["G1b_gated_to_learnable"], res["G1"]
    assert c["G1c_naive_traps"], res["G1"]
    assert c["G1_headline"], res["G1"]
    g1 = res["G1"]
    # gated leaves the noisy TV; naive stays pinned to it
    assert g1["gated_noisy_late"] < 0.5 * g1["gated_noisy_early"]
    assert g1["naive_noisy_late"] >= 0.8 * g1["naive_noisy_early"]
    # and the learnable dominates late attention under the gate
    assert g1["gated_learnable_late"] > 2 * g1["gated_noisy_late"]
    # per-draw robustness: the gate leaves on the large majority of noise draws
    assert g1["per_seed_gated_leaves"] >= (3 * g1["n_ensemble"]) // 4


def test_G2_leave_the_unresolved(res):
    c = res["criteria"]
    assert c["G2a_resolved_decays"], res["G2"]
    assert c["G2b_intractable_decays"], res["G2"]
    assert c["G2c_progressing_held"], res["G2"]
    assert c["G2d_progress_not_surprise"], res["G2"]
    g2 = res["G2"]
    # the discriminator is PROGRESS, not surprise: resolved has the LOWEST mean
    # surprise, intractable the HIGHEST, yet BOTH decay while the progressing
    # (intermediate-surprise) item is held.
    assert g2["resolved_surprise"] < g2["progressing_surprise"] < g2["intractable_surprise"]
    assert g2["progressing_late"] > g2["resolved_late"]
    assert g2["progressing_late"] > g2["intractable_late"]


def test_G3_commit_net(res):
    c = res["criteria"]
    assert c["G3a_paralysis"], res["G3"]
    assert c["G3b_calibrated_at_crossing"], res["G3"]
    assert c["G3c_impulsive"], res["G3"]
    assert c["G3d_passive_paralysis"], res["G3"]
    arms = res["G3"]["arms"]
    # paralysis: no commit-net -> no termination
    assert arms["naive"]["commit_step"] is None
    assert arms["passive"]["commit_step"] is None
    # calibrated cut at the analytic marginal=cost crossing; impulsive premature
    assert arms["calibrated"]["commit_step"] == res["G3"]["analytic_crossing"]
    assert arms["impulsive"]["commit_step"] <= 1


def test_G4_integer_default_off_source(res):
    c = res["criteria"]
    assert c["G4a_integer_native"], res["G4"]
    assert c["G4b_default_off_byte_identical"], res["G4"]
    assert c["G4c_source_graph_resident"], res["G4"]
    g4 = res["G4"]
    assert g4["noninteger_cells"] == 0
    assert g4["bad_float"] == {}
    # default-OFF: no curiosity attr written with no params node / enabled=0
    assert g4["changed_noparams"] == {}
    assert g4["changed_disabled"] == {}
    # source audit: the adapter never set_attr a decision key
    assert g4["bad_setattr"] == []
    assert g4["self_load_only"] is True

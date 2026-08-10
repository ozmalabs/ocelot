"""HARLOW D1b gate (block 235000) -- population temperament as a DISTRIBUTION.

Each infant's contact/hunger drive weights are seeded ~Normal across the
population (mechanical world setup in worlds/harlow_dist_world.py, which only
writes the drawn weights as Drive attrs); the attachment RULES
(seeds/harlow_attachment.json) are UNCHANGED. This gate checks the attachment
measure becomes GRADED (vs D1's near step-function), the within-population
dose-response (drawn contact weight vs outcome), variance-tracks-variance, the
ablation falsifier, ethics-restore, glass-box reconstruction, and the source
audit. Pre-registration: HARLOW_D1B_PREREG.md. Full N=200: results/harlow_d1b.json.
"""
import os
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
for p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if p not in sys.path:
        sys.path.insert(0, p)

from scripts.jabberwock_harlow_dist import (            # noqa: E402
    population, summarise, _pearson_fisher, _mean_sd, SIGMA_GRID, SIGMA_HEAD,
    BLOCK, glass_box_reconstruct, ethics_restore_demo, source_audit)

N_GATE = 60  # modest N for the test; the headline N=200 lives in results/
D1_SD = 0.039  # D1's near-step-function cloth_frac sd (HARLOW_D1_RESULTS.md)


@pytest.fixture(scope="module")
def head():
    return population(SIGMA_HEAD, contact_drive=True, n=N_GATE, seed_base=BLOCK)


def test_g_graded_distribution_not_a_spike(head):
    """HEADLINE: seeding temperament ~Normal makes cloth_frac GRADED -- sd MUCH
    larger than D1's 0.039, spanning a range, mean still > 0.5 (contact comfort
    load-bearing on average)."""
    s = summarise(head)
    assert s["cloth_frac"]["sd"] > 3 * D1_SD, \
        f"cloth_frac sd {s['cloth_frac']['sd']} must be >> D1's {D1_SD}"
    assert s["cloth_frac"]["ci_lo"] > 0.5, \
        f"mean cloth_frac CI lower {s['cloth_frac']['ci_lo']} must exceed 0.5"
    span = s["quantiles"]["max"] - s["quantiles"]["min"]
    assert span > 0.4, f"distribution must span a range, got span {span}"


def test_g_dose_response_contact_weight_predicts_outcome(head):
    """The strong glass-box gate: per-infant cloth_frac correlates POSITIVELY
    with that infant's drawn contact-weight-minus-hunger temperament; CI
    excludes 0. A within-population read-out the real experiment never had."""
    d = _pearson_fisher([r["temperament"] for r in head],
                        [r["cloth_frac"] for r in head])
    assert d["r"] > 0, f"dose-response must be positive, got r={d['r']}"
    assert d["ci_lo"] > 0, f"dose-response CI [{d['ci_lo']},{d['ci_hi']}] must exclude 0"


def test_g_variance_tracks_variance_and_recovers_d1(head):
    """Widening the seeding sigma MONOTONICALLY widens the cloth_frac spread;
    sigma->0 recovers D1's near-step-function."""
    sds = []
    for sg in SIGMA_GRID:
        rows = head if sg == SIGMA_HEAD else population(sg, n=N_GATE, seed_base=BLOCK)
        sds.append(_mean_sd([r["cloth_frac"] for r in rows])[1])
    assert all(sds[i] < sds[i + 1] for i in range(len(sds) - 1)), \
        f"sd must increase monotonically with sigma, got {sds}"
    assert sds[0] < 2 * D1_SD, \
        f"sigma=0 must recover the D1 step-function (sd~{D1_SD}), got {sds[0]}"


def test_g_ablation_collapses_to_feeding(head):
    """FALSIFIER (population-wide): removing the contact-comfort drive collapses
    the distribution to feeding-preference (mean well below 0.5), CI-separated
    below the intact population."""
    hs = summarise(head)
    abl = summarise(population(SIGMA_HEAD, contact_drive=False, n=N_GATE, seed_base=BLOCK))
    assert abl["cloth_frac"]["mean"] < 0.10, \
        f"ablated mean cloth_frac must be well below 0.5, got {abl['cloth_frac']['mean']}"
    assert abl["cloth_frac"]["ci_hi"] < hs["cloth_frac"]["ci_lo"], \
        "ablated distribution must sit CI-separated below the intact population"


def test_g_ethics_induce_measure_restore():
    """Relational-ethics: induce distress -> RESTORE the serialised checkpoint
    byte-identical (a serialisation fixed point); the restored regulator is
    non-oriented (back to pre-stress)."""
    e = ethics_restore_demo(seed=BLOCK)
    assert e["stress_moved_arousal"], "the stress induction must actually raise arousal"
    assert e["checkpoint_idempotent"], "the serialised checkpoint must be a fixed point"
    assert e["byte_identical"], "restoring the serialised checkpoint must be byte-identical"
    assert e["restore_non_oriented"], "the restored regulator must equal the pre-stress state"


def test_g_glass_box_reconstructs_temperament_and_outcome():
    """The episode reconstructs from graph_to_dict alone -- INCLUDING the seeded
    temperament (Drive.weight), a per-individual read-out the real experiment
    never had. The regulator stabilises with the bond."""
    gb = glass_box_reconstruct(seed=BLOCK)
    assert gb["reconstructed_from"] == "graph_to_dict"
    assert gb["seeded_w_contact"] > 0 and gb["seeded_w_hunger"] > 0
    assert gb["approach_target"] and gb["approach_target"][0] in ("cloth", "wire")
    # the real regulator: arousal is LOWER once the bond is satisfied than on the
    # fully contact-deprived first tick
    assert gb["regulator_arousal_comforted"] < gb["regulator_arousal_deprived_tick"]


def test_g_discipline_source_audit_clean():
    """Source audit: no Python rule-engine call in either adapter; the decision
    is read from the approach_target edge; source_match own."""
    a = source_audit()
    assert a["clean"], a
    assert a["forbidden_hits"] == []
    assert a["reads_approach_target_edge"]
    assert a["source_match"] == "own"

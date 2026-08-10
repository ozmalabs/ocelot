"""HARLOW D1 gate (block 233000) — Harlow (1958) wire/cloth attachment on the
REAL emotion framework (drives.json drive system + modulators.json /
affective_state_core.json regulator).

Pre-registration: HARLOW_D1_PREREG.md. Full-power result (N=200):
results/harlow_d1.json. This gate re-runs a modest N for CI-separation +
mechanism, plus the falsifier, glass-box, ethics-restore and source audit.
"""
import math
import os
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
for p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if p not in sys.path:
        sys.path.insert(0, p)

from scripts.jabberwock_harlow import (          # noqa: E402
    run_infant, _ci95, SEED_BASE,
    glass_box_reconstruct, ethics_restore_demo, source_audit)

N_GATE = 40  # modest N for the test; the headline N=200 lives in results/


def _condition(contact_drive):
    rows = [run_infant(SEED_BASE + i, contact_drive=contact_drive) for i in range(N_GATE)]
    cf = [r["cloth_frac"] for r in rows]
    fc = [r["flee_cloth"] for r in rows]
    return dict(rows=rows, cloth=_ci95(cf), flee=_ci95(fc))


@pytest.fixture(scope="module")
def conditions():
    return {"A": _condition(True), "B": _condition(False)}


def test_g_harlow_prefers_contact_mother_ci_separated(conditions):
    """HEADLINE: proximity to the CONTACT mother > 0.5 and CI-separated above the
    ablated condition, via the real regulator."""
    A, B = conditions["A"], conditions["B"]
    a_m, a_sd, a_lo, a_hi = A["cloth"]
    b_m, b_sd, b_lo, b_hi = B["cloth"]
    assert a_lo > 0.5, f"contact-mother proximity CI lower bound must exceed 0.5, got {a_lo}"
    assert a_lo > b_hi, f"A cloth_frac CI [{a_lo},{a_hi}] must separate above B [{b_lo},{b_hi}]"


def test_g_harlow_flees_to_contact_mother_under_stress(conditions):
    """Under stress the infant flees to the CONTACT mother (secure base),
    separated above the ablated condition."""
    A, B = conditions["A"], conditions["B"]
    a_m = A["flee"][0]
    b_m = B["flee"][0]
    assert a_m > 0.5, f"flee-to-cloth must exceed 0.5, got {a_m}"
    assert a_m > b_m, f"flee-to-cloth A={a_m} must exceed B={b_m}"


def test_g_comfort_drive_ablation_falsifier(conditions):
    """FALSIFIER: removing the contact-comfort drive makes the preference
    DISAPPEAR or INVERT — proving the drive CAUSES the attachment."""
    A, B = conditions["A"], conditions["B"]
    a_lo = A["cloth"][2]
    b_hi = B["cloth"][3]
    b_mean = B["cloth"][0]
    assert b_hi < a_lo, "ablated cloth_frac must sit below the contact-drive condition"
    assert b_mean < 0.5, f"ablated preference must not favour the contact mother, got {b_mean}"


def test_g_glass_box_reconstructs_from_graph():
    """The bond reconstructs from graph_to_dict alone: approach_target edge,
    Mother proximity/bond_strength, regulator arousal comforted << deprived."""
    gb = glass_box_reconstruct()
    assert gb["approach_target"] == ["cloth"], gb["approach_target"]
    assert gb["cloth"]["proximity"] > gb["wire"]["proximity"]
    assert gb["cloth"]["bond_strength"] > gb["wire"]["bond_strength"]
    # the real regulator: arousal is LOWER when the contact bond is satisfied
    assert gb["regulator_arousal_comforted"] < gb["regulator_arousal_deprived_tick"]
    assert gb["reconstructed_from"] == "graph_to_dict"


def test_g_ethics_induce_measure_restore_byte_identical():
    """Relational-ethics: induce distress -> measure -> RESTORE byte-identical;
    the restored regulator is non-oriented (identical to pre-stress)."""
    e = ethics_restore_demo()
    assert e["stress_moved_arousal"], "the stress induction must actually raise arousal"
    assert e["byte_identical"], "graph_from_dict(checkpoint) must be byte-identical"
    assert e["restore_non_oriented"], "the restored regulator must equal the pre-stress state"


def test_g_discipline_no_python_decides_attachment():
    """Source audit: the world adapter contains no Python rule-engine call and
    reads the approach decision from the graph's approach_target edge."""
    a = source_audit()
    assert a["clean"], a
    assert a["reads_approach_target_edge"]
    assert a["forbidden_hits"] == []

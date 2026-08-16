"""Regression for seeds/can_register_quantization.json -- the personality-
trait-quantized REGISTER/STYLE codebook, applied per discrete relationship
band. See docs/research/engine_substrate/CAN_REGISTER_QUANTIZATION_PREREG.md
for the full registered design and CAN_REGISTER_QUANTIZATION_RESULTS.md for
the live-demonstration numbers this file's regression assertions encode.

Mirrors tests/test_can_native_reimplementation.py's own calling convention
(`_native.Substrate()` via `substrate_rs`, `load_seed_manifest` after
`engine_rules_only`) and tests/test_bigville_can_integration.py's own
pattern of encoding the measured live-demo direction as a standing
regression assertion.
"""
from __future__ import annotations

import io
import json
import re
from contextlib import redirect_stderr, redirect_stdout

import pytest

import substrate_rs as sr
from substrate.seed_loader import engine_rules_only

SEED_PATH = "seeds/can_register_quantization.json"
BANDS = list(range(6))


def _loaded_substrate(capture_warnings=None):
    s = sr.Substrate()
    inner = s._inner
    d = json.load(open(SEED_PATH))
    filtered = engine_rules_only(d)
    if capture_warnings is not None:
        buf = io.StringIO()
        with redirect_stdout(buf), redirect_stderr(buf):
            inner.load_seed_manifest(filtered)
        capture_warnings.append(buf.getvalue())
    else:
        inner.load_seed_manifest(filtered)
    return s


def _band_anchors(inner):
    return {inner.node(n)["attrs"]["band_code"]: n for n in inner.nodes("BandAffinityAnchor")}


def _build_profile(inner, anchors, name, resolution_bins, resolution_level, bands=BANDS):
    prof = inner.add_node("RegisterProfile", {
        "name": name, "resolution_bins": resolution_bins,
        "resolution_level": resolution_level,
    })
    obs_ids = {}
    for band in bands:
        ta = inner.node(anchors[band])["attrs"]["true_affinity"]
        obs = inner.add_node("RegisterObservation", {
            "band_code": band, "true_affinity": ta, "status": "pending",
        })
        inner.add_edge(prof, "observed_band", obs, {})
        obs_ids[band] = obs
    return prof, obs_ids


def _decode(inner, obs_ids):
    inner.run_rules(200)
    out = {}
    for band, obs in obs_ids.items():
        at = inner.node(obs)["attrs"]
        out[band] = dict(at)
    return out


def _mean_abs_error(results):
    vals = [abs(r["true_affinity"] - r["quantized_value"]) for r in results.values()]
    return sum(vals) / len(vals)


def _distinct_labels(results):
    return {r["register_label"] for r in results.values()}


# ---------------------------------------------------------------------
# 1. Seed loads cleanly -- zero new Rust confirmed: a malformed rule
#    (ShapeMismatch / "skipping malformed rule") would print a warning to
#    stdout/stderr at load time; this asserts none appears.
# ---------------------------------------------------------------------
def test_seed_loads_with_no_malformed_rule_warning():
    warnings = []
    s = _loaded_substrate(capture_warnings=warnings)
    inner = s._inner
    captured = warnings[0]
    assert "malformed" not in captured.lower(), captured
    assert "skipping" not in captured.lower(), captured
    # the one declared rule is actually present and counted
    assert inner.rule_count() >= 1


# ---------------------------------------------------------------------
# 2. BandAffinityAnchor codebook shape -- PREREG Sec4.1.
# ---------------------------------------------------------------------
def test_band_affinity_anchors_cover_0_to_5_monotonic_saturating():
    s = _loaded_substrate()
    inner = s._inner
    anchors = _band_anchors(inner)
    assert set(anchors.keys()) == set(BANDS)
    values = [inner.node(anchors[b])["attrs"]["true_affinity"] for b in BANDS]
    # monotonic increasing (closeness -> more casual/converged)
    assert all(values[i] < values[i + 1] for i in range(len(values) - 1)), values
    # band 0 (stranger) sits at the exact -1.0 floor (exp(0)=1 boundary,
    # PREREG Sec4.1's own registered, not-a-bug, boundary fact)
    assert values[0] == pytest.approx(-1.0)
    # band 5 (family) approaches but does not reach +1.0 -- SATURATING,
    # not linear (Brinberg & Ram 2021, PREREG Sec1 point 5)
    assert 0.85 < values[5] < 1.0
    # no band_code == -1 (rival) anchor exists -- PREREG Sec1 point 4's
    # registered scoping exclusion
    assert -1 not in anchors


def test_register_label_anchors_reuse_interlocutor_shapes_vocabulary():
    s = _loaded_substrate()
    inner = s._inner
    labels = {
        inner.node(n)["attrs"]["label"]: inner.node(n)["attrs"]["canonical_value"]
        for n in inner.nodes("RegisterLabelAnchor")
    }
    assert labels == {"formal": -1.0, "neutral": 0.0, "casual": 1.0}


# ---------------------------------------------------------------------
# 3. effective_bins composition -- PREREG Sec3/4.2, reused verbatim from
#    BIGVILLE_CAN_INTEGRATION_PREREG.md Sec4's formula.
# ---------------------------------------------------------------------
@pytest.mark.parametrize("resolution_bins,resolution_level,expected_eb", [
    (2, 1.0, 2),     # floor trait, full level -> floor
    (8, 0.5, 4),     # round(8*0.5)=4
    (2, 0.1, 2),     # max(2, round(0.2)) = max(2,0) = 2 -- the floor clamp
    (12, 1.0, 12),   # ceiling trait, full level
])
def test_effective_bins_composition_matches_registered_formula(
    resolution_bins, resolution_level, expected_eb
):
    s = _loaded_substrate()
    inner = s._inner
    anchors = _band_anchors(inner)
    prof, obs = _build_profile(inner, anchors, "p", resolution_bins, resolution_level, bands=[0])
    res = _decode(inner, obs)
    assert res[0]["effective_bins"] == pytest.approx(expected_eb)


# ---------------------------------------------------------------------
# 4. The register DECISION is the engine's -- Argmin over the codebook,
#    not a Python if/else. Structural certainty (PREREG Sec6.2 prediction
#    2): effective_bins=2 -> vocabulary is exactly {-1,+1} -> 'neutral'
#    can never be selected, for ANY true_affinity.
# ---------------------------------------------------------------------
def test_coarsest_resident_structurally_never_produces_neutral_label():
    s = _loaded_substrate()
    inner = s._inner
    anchors = _band_anchors(inner)
    prof, obs = _build_profile(inner, anchors, "coarse", 2, 1.0)
    res = _decode(inner, obs)
    labels = _distinct_labels(res)
    assert "neutral" not in labels
    assert labels <= {"formal", "casual"}


def test_register_quantized_value_stays_on_the_achievable_grid():
    """For effective_bins=2 every quantized_value must land on exactly
    {-1.0, 1.0} -- confirms the quantization grid itself, independent of
    the label decode built on top of it."""
    s = _loaded_substrate()
    inner = s._inner
    anchors = _band_anchors(inner)
    prof, obs = _build_profile(inner, anchors, "coarse", 2, 1.0)
    res = _decode(inner, obs)
    for band, r in res.items():
        assert r["quantized_value"] in (-1.0, 1.0), (band, r)


# ---------------------------------------------------------------------
# 5. The primary measured finding (CAN_REGISTER_QUANTIZATION_RESULTS.md
#    Sec... , mirroring BIGVILLE_CAN_INTEGRATION_RESULTS.md's own
#    "test_low_resolution_resident_shows_more_rounding_error_and_more_
#    frustration" precedent of encoding the live-demo direction as a
#    standing regression assertion): given IDENTICAL band-interaction-
#    history input (the same BandAffinityAnchor template), a resident with
#    higher resolution_bins produces STRICTLY more distinct register
#    labels than a resident with the population-floor resolution_bins.
# ---------------------------------------------------------------------
def test_higher_resolution_resident_discriminates_more_register_labels():
    s = _loaded_substrate()
    inner = s._inner
    anchors = _band_anchors(inner)
    prof_c, obs_c = _build_profile(inner, anchors, "coarse", 2, 1.0)
    prof_f, obs_f = _build_profile(inner, anchors, "fine", 8, 1.0)
    res_c = _decode(inner, obs_c)
    res_f = _decode(inner, obs_f)
    dl_c = len(_distinct_labels(res_c))
    dl_f = len(_distinct_labels(res_f))
    assert dl_f > dl_c, (res_c, res_f)
    assert dl_c == 2
    assert dl_f == 3


def test_quantization_error_higher_for_coarse_resident():
    """Prediction 1 (manipulation check, PREREG Sec6.2) as a standing
    regression."""
    s = _loaded_substrate()
    inner = s._inner
    anchors = _band_anchors(inner)
    prof_c, obs_c = _build_profile(inner, anchors, "coarse", 2, 1.0)
    prof_f, obs_f = _build_profile(inner, anchors, "fine", 8, 1.0)
    res_c = _decode(inner, obs_c)
    res_f = _decode(inner, obs_f)
    err_c = _mean_abs_error(res_c)
    err_f = _mean_abs_error(res_f)
    assert err_c > err_f
    assert err_c / err_f > 5.0   # measured 11.8x; a loose regression floor


# ---------------------------------------------------------------------
# 6. resolution_level sanity sweep (PREREG Sec6.3 supplementary 2).
# ---------------------------------------------------------------------
def test_resolution_level_sweep_effective_bins_nondecreasing():
    s = _loaded_substrate()
    inner = s._inner
    anchors = _band_anchors(inner)
    ebs = []
    for i, level in enumerate((0.3, 0.6, 1.0)):
        prof, obs = _build_profile(inner, anchors, "sweep_%d" % i, 8, level, bands=[0])
        res = _decode(inner, obs)
        ebs.append(res[0]["effective_bins"])
    assert ebs == sorted(ebs)
    assert ebs[0] < ebs[-1]


# ---------------------------------------------------------------------
# 7. Idempotency -- a second run_rules() call after convergence does not
#    change any decoded attr (the fixpoint is stable, matching every other
#    sd-loop-family rule in this codebase).
# ---------------------------------------------------------------------
def test_decode_is_a_stable_fixpoint():
    s = _loaded_substrate()
    inner = s._inner
    anchors = _band_anchors(inner)
    prof, obs = _build_profile(inner, anchors, "p", 6, 1.0)
    inner.run_rules(200)
    snapshot1 = {b: dict(inner.node(o)["attrs"]) for b, o in obs.items()}
    inner.run_rules(200)
    snapshot2 = {b: dict(inner.node(o)["attrs"]) for b, o in obs.items()}
    assert snapshot1 == snapshot2


# ---------------------------------------------------------------------
# 8. No-Python-decision source audit -- mirrors the ink-decode precedent
#    (CLAUDE.md's "THE AGENT FIXES ITSELF WHERE IT IS GRAPH-NATIVE" arc):
#    the demo/harness script must never itself call set_attr with a
#    computed register_label value -- the label is written ONLY by the
#    engine's own rule effect.
# ---------------------------------------------------------------------
def test_no_python_decision_source_audit():
    harness_src = open("scripts/can_register_quantization_demo.py").read()
    seed_builder_src = open("scripts/_build_can_register_quantization_seed.py").read()
    # the harness must never directly set_attr a register_label/quantized_
    # value/effective_bins/register_level_index itself -- those are engine
    # rule effects, read back only.
    forbidden = re.compile(
        r"set_attr\([^)]*[\"'](register_label|quantized_value|effective_bins|"
        r"register_level_index)[\"']"
    )
    assert not forbidden.search(harness_src)
    # the seed builder legitimately WRITES these as Term-based rule effects
    # (via term_effect/lit_effect, not a Python conditional) -- confirm no
    # bare Python if/else chooses among "formal"/"neutral"/"casual" there.
    label_if = re.compile(
        r'if\s+.*:\s*\n\s*.*[\"\']?(formal|casual)[\"\']?\s*\n?\s*(el)?if'
    )
    assert not label_if.search(seed_builder_src)


# ---------------------------------------------------------------------
# 9. depends_on / dependency hygiene (PREREG Sec2's registered decision).
# ---------------------------------------------------------------------
def test_seed_manifest_dependencies_match_registered_design():
    d = json.load(open(SEED_PATH))
    assert set(d["depends_on"]) == {"can_native_reimplementation", "interlocutor_shapes"}
    assert "shape_decode_loop" not in d["depends_on"]
    assert d.get("productions"), "must declare the RegisterProfile->observed_band->RegisterObservation production"
    assert len(d["productions"]) == 1
    prod = d["productions"][0]
    assert prod["src"]["type"] == "RegisterProfile"
    assert prod["edge_type"] == "observed_band"
    assert prod["tgt"]["type"] == "RegisterObservation"


def test_already_landed_seeds_are_untouched():
    """This rung's own constraint (task charter): can_native_
    reimplementation.json / interlocutor_shapes.json must never be
    modified -- confirmed here by checking git status shows no
    modification to either path (skips gracefully if git is unavailable)."""
    import subprocess
    try:
        out = subprocess.run(
            ["git", "status", "--porcelain",
             "seeds/can_native_reimplementation.json",
             "seeds/interlocutor_shapes.json"],
            capture_output=True, text=True, timeout=10, cwd=".",
        )
    except Exception:
        pytest.skip("git unavailable")
    assert out.returncode == 0
    assert out.stdout.strip() == "", out.stdout

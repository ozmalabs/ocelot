"""Gates for the ARC5 numerics/DSP float audit (Corpus 1: this repo's own
audio/shape-verdict/quantization stack; Corpus 2: classic numerics).

Named `_migrated` per this tree's convention for the regression bench
(`pytest -k migrated`), even though this audit is a measurement script
rather than agent-decision code -- it lives alongside the other ARC5
float-necessity gates (arc5_float_necessity_audit / arc5_exact_recovery)
and should run with them.

These tests re-run the audit's own builder (not just re-load the JSON)
so a stale results file can never mask a code change, then check:
  - schema shape;
  - every site's class is in {A, B, C, D} and the four classes partition
    the site list with no leftovers;
  - the (D) list is exactly the D-classified sites (the headline, either
    way -- see PROGRAM_SYNTHESIS_ARC5_NUMERICS_FLOATS.md);
  - aggregate counts are internally consistent (sums, by-corpus split);
  - every site that cites a repo file is actually verified against real
    source (no fabricated evidence line);
  - >=3 pinned per-site classifications are spot-checked directly against
    the actual source text (independent of the audit script's own
    verification, so a bug in `verify_site` can't hide a wrong claim).
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
RESULTS_PATH = REPO_ROOT / "results" / "arc5_numerics_float_audit.json"

import sys
sys.path.insert(0, str(REPO_ROOT / "scripts"))
import arc5_numerics_float_audit as audit_mod  # noqa: E402


@pytest.fixture(scope="module")
def audit():
    return audit_mod.build_audit()


@pytest.fixture(scope="module")
def persisted():
    assert RESULTS_PATH.exists(), (
        "results/arc5_numerics_float_audit.json missing -- run "
        "scripts/arc5_numerics_float_audit.py"
    )
    return json.loads(RESULTS_PATH.read_text())


# --- schema -----------------------------------------------------------------

def test_schema_top_level_keys(audit):
    for key in ("meta", "sites", "aggregates", "d_list", "unverified_site_ids",
                "sharp_question", "tolerance_audit", "verdict", "verdict_note"):
        assert key in audit, f"missing top-level key {key!r}"


def test_schema_per_site_keys(audit):
    required = {"id", "corpus", "cls", "file", "symbol", "evidence_needle",
                "justification", "verification"}
    for s in audit["sites"]:
        missing = required - set(s.keys())
        assert not missing, f"site {s.get('id')} missing keys {missing}"


def test_persisted_file_matches_fresh_build(audit, persisted):
    """The committed results JSON must not be stale relative to the script
    that produces it (ids + classes must match exactly)."""
    fresh_by_id = {s["id"]: s["cls"] for s in audit["sites"]}
    persisted_by_id = {s["id"]: s["cls"] for s in persisted["sites"]}
    assert fresh_by_id == persisted_by_id


# --- class-partition completeness -------------------------------------------

def test_every_site_has_a_valid_class(audit):
    for s in audit["sites"]:
        assert s["cls"] in {"A", "B", "C", "D"}, f"{s['id']} has invalid class {s['cls']!r}"


def test_class_partition_is_exhaustive_and_disjoint(audit):
    """Every site belongs to exactly one of A/B/C/D (trivially true of a
    single `cls` field, but this locks the CONTRACT: aggregates['by_class']
    must sum to the total site count, so a future refactor that adds a
    multi-class site or drops one from the count is caught)."""
    total = len(audit["sites"])
    by_class_sum = sum(audit["aggregates"]["by_class"].values())
    assert by_class_sum == total


def test_aggregates_are_internally_consistent(audit):
    agg = audit["aggregates"]
    assert agg["total_sites"] == len(audit["sites"])
    assert agg["corpus1_sites"] + agg["corpus2_sites"] == agg["total_sites"]
    c1 = sum(agg["by_class_corpus1"].values())
    c2 = sum(agg["by_class_corpus2"].values())
    assert c1 == agg["corpus1_sites"]
    assert c2 == agg["corpus2_sites"]
    for k in ("A", "B", "C", "D"):
        assert agg["by_class"][k] == agg["by_class_corpus1"][k] + agg["by_class_corpus2"][k]


def test_d_list_is_exactly_the_d_classified_sites(audit):
    """The headline, either way: the (D) list must be derived, never
    hand-curated separately from the site classifications."""
    expected_ids = {s["id"] for s in audit["sites"] if s["cls"] == "D"}
    actual_ids = {s["id"] for s in audit["d_list"]}
    assert expected_ids == actual_ids


def test_verdict_reflects_d_list(audit):
    """REFUTED iff the (D) list is non-empty; this is the one piece of
    logic in the whole audit that must never be fudged by hand."""
    if audit["d_list"]:
        assert audit["verdict"] == "REFUTED"
    else:
        assert audit["verdict"] in ("UPHELD", "UPHELD_WITH_QUALIFICATION")


def test_d_list_is_empty_and_this_is_stated_loudly(audit):
    """As measured: zero genuinely-irreducible in-frame reals were found in
    either corpus. This test exists so a future site added with cls='D'
    is impossible to land silently -- it must also update the verdict."""
    assert audit["d_list"] == []
    assert audit["verdict"] == "UPHELD_WITH_QUALIFICATION"


# 2026-08-01: two class-C sites the audit DOCUMENTED have since been
# REMEDIATED (c1-12 acoustic band energies -> fixed-point; c1-14 Fisher
# discriminant -> sqrt-free reformulation, both verdict-identity gated in
# tests/test_exact_invariant_migrated.py). The `audit` fixture re-runs
# verification against LIVE source, so those two sites' pinned evidence
# snippets no longer match — which is the audit correctly noticing its own
# findings were acted on. The FROZEN artifact stays authoritative for the
# state it measured (`persisted` still shows both verified_near_line and an
# empty unverified list, asserted below); only the LIVE re-verification
# tolerates these two ids.
_REMEDIATED_SITE_IDS = {"c1-12", "c1-14"}

def test_no_unverified_sites(audit, persisted):
    """Every site that cites a repo file must have been found in that file
    by the script's own verification pass (no fabricated evidence)."""
    # The frozen artifact — authoritative for the state it measured.
    assert persisted["unverified_site_ids"] == []
    # Live: only the two remediated sites may fail to re-verify.
    live_unverified = set(audit["unverified_site_ids"])
    assert live_unverified <= _REMEDIATED_SITE_IDS, (
        f"sites with unverifiable evidence: {sorted(live_unverified - _REMEDIATED_SITE_IDS)}")


def test_all_file_sites_verified_status(audit):
    for s in audit["sites"]:
        if s["id"] in _REMEDIATED_SITE_IDS:
            continue  # see _REMEDIATED_SITE_IDS above
        if s["file"] is not None:
            assert s["verification"]["status"] in (
                "verified_near_line", "verified_elsewhere"
            ), f"{s['id']}: {s['verification']}"
        else:
            assert s["verification"]["status"] == "external"


def test_class_c_sites_are_the_headline_avoidable_cases(audit):
    """The three class-C sites this audit's report leans on for the
    'upheld WITH QUALIFICATION' verdict must actually be present and
    actually be class C (not silently reclassified)."""
    by_id = {s["id"]: s for s in audit["sites"]}
    for sid in ("c1-12", "c1-14", "c2-07"):
        assert sid in by_id, f"expected headline site {sid} missing"
        assert by_id[sid]["cls"] == "C"


# --- pinned spot-checks against ACTUAL source (independent of the script's
# own verify_site, so a bug there can't hide a wrong claim) -----------------

def _read(rel_path: str) -> str:
    return (REPO_ROOT / rel_path).read_text(errors="replace")


def test_spotcheck_space_quantize_is_float_free_except_qdist_sentinel():
    """c1-10: space_quantize.rs should contain the qdist float sentinel and
    otherwise be free of f32/f64 -- the cleanest positive confirmation in
    the corpus. This independently re-derives the f32/f64 count rather than
    trusting the audit's prose."""
    src = _read("runners/dsl/src/space_quantize.rs")
    assert "attrs.insert(syms.qdist, Value::Float(-1.0));" in src
    float_lines = [ln for ln in src.splitlines() if "f32" in ln or "f64" in ln]
    assert float_lines == [], (
        f"expected space_quantize.rs to have zero f32/f64 literals, found: {float_lines}"
    )


def test_spotcheck_discriminative_invention_sqrt_and_fisher_rule():
    """c1-14 — SITE FIXED 2026-08-01, and this gate now pins the FIX.

    The audit classified this as class C: `std = var**0.5` persisted as a
    graph attr and read by a graph-native `Gt` rule — a specification
    choice (the textbook Fisher-ratio formula), not a requirement. It has
    since been reformulated sqrt-free by isolating and squaring each root:

        K = D/T - eps;  K > 0  AND  K**2 - a_var - b_var > 0
                        AND  (K**2 - a_var - b_var)**2 > 4*a_var*b_var

    Verdict-identity against the original formula is gated on 160 cases
    spanning and straddling the threshold in
    `tests/test_exact_invariant_migrated.py`. This assertion is therefore
    INVERTED: the decision path must no longer contain the root."""
    src = _read("domains/discriminative_invention.py")
    assert "_fisher_separates_term" in src, (
        "the sqrt-free Fisher reformulation should be present")
    assert "var ** 0.5" not in src.split("def _fisher_separates_term")[-1], (
        "the sqrt-free decision path must not reintroduce a root")


def test_spotcheck_acoustic_bands_are_raw_float_set_attr():
    """c1-12 — SITE FIXED 2026-08-01, and this gate now pins the FIX.

    The audit classified this as class C: raw band-energy means persisted
    as float attrs read only by ORDER predicates over an exactly-rational
    quantity. They are now stored fixed-point (`round(v * 2**32)`), which
    is order-preserving under a uniform positive rescale; every consumer
    was audited as order-only / ArgMax / scale-invariant-ratio, and
    ordering identity is gated on 80 trajectories in
    `tests/test_exact_invariant_migrated.py`. Assertion INVERTED."""
    src = _read("domains/acoustic_resolution.py")
    assert "2 ** 32" in src or "2**32" in src, (
        "the fixed-point band representation should be present")


def test_spotcheck_rotate_term_is_self_documented_cross_frame():
    """c1-07/c1-08: term.rs's Rotate evaluator returns Float coordinates,
    and continuous_pose.json's own comment names it a cross-frame generator
    'NEVER an in-frame coordinate' -- pin both halves of that claim."""
    term_src = _read("runners/dsl/src/term.rs")
    assert "TermNode::Rotate { vec, angle } => {" in term_src
    assert "Value::Float(x * c - y * s), Value::Float(x * s + y * c)" in term_src
    seed_src = _read("seeds/continuous_pose.json")
    assert "NEVER an in-frame coordinate" in seed_src


def test_spotcheck_strokes_quantize_rounds_to_int_before_persisting():
    """c1-11: internal f64 geometry is rounded to i64 before being wrapped
    as a graph relation -- the map/in-frame boundary is exactly where the
    audit claims it is."""
    src = _read("runners/dsl/src/strokes.rs")
    assert "fn quantize_signed_angle(deg: f64, bins: i64) -> i64 {" in src
    assert 'pose_x_q = Some(x.round() as i64)' in src
    assert 'Value::Int(sx)' in src or "Value::Int(sx)" in src


# --- sharp question / tolerance audit are present and non-trivial ----------

def test_sharp_question_is_answered_not_dodged(audit):
    sq = audit["sharp_question"]
    assert "PRECISION TRACKING" in sq["answer"]
    assert "Pentium" in sq["answer"] or "FDIV" in sq["answer"]
    assert len(sq["answer"]) > 200


def test_tolerance_audit_present(audit):
    ta = audit["tolerance_audit"]
    assert "finding" in ta and len(ta["finding"]) > 100
    # Must name at least one site that DOES track tolerance and concede the
    # DSP layer mostly does not (the honest, non-vacuous answer).
    assert "df_eps" in ta["finding"] or "cp_angles" in ta["finding"]
    assert "1e-10" in ta["finding"] or "numerical-stability" in ta["finding"]

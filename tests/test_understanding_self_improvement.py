"""test_understanding_self_improvement — the jabberwock DIAGNOSES an understanding
defect's SHAPE and ROUTES it to the fitting composer-authored fix ITSELF (donkey=0,
DISCRIMINATIVE).

Two genuine understanding defects (a leaked clause fragment; a context-blind word
sense) were each fixed BY HAND once (consumption_quality). Now the jabberwock runs
the SAME perceive->diagnose->select->verify->apply cycle it runs on EFFICIENCY, and
the fix CHOICE comes OUT of the graph — a fragment-shaped gap routes to nominal_filter,
a mis-sense-shaped gap routes to sense_select, from the SAME two Programs.

Each gate would FAIL if the mechanism were fake:

  · PERCEIVE — each defect mints an understanding CapabilityGap carrying its measured
    error-features. (Fails if no gap / no error-features.)
  · DIAGNOSE (graph decision) — the Programs return non-nominal-extraction->nominal_
    filter for the fragment gap AND context-blind-sense->sense_select for the sense
    gap: SAME Programs, DIFFERENT error-features, DIFFERENT fix. (Fails if fixed.)
  · DIAGNOSIS MATTERS (discriminative) — the WRONG fix FAILS its control: nominal_
    filter does NOT clean a context-blind-sense gap; sense_select does NOT clean a
    non-nominal-extraction gap. (Fails if "apply all fixes" would do.)
  · FIX COMPOSER-AUTHORED + APPLIED — the selected fix dispatches to ensure_*_program
    (the composer authors it) and cleans the defect (fragment dropped / water->
    substance byte-identical to the direct fix). (Fails if the fix did nothing.)
  · VERIFY-GATED — the right fix passes #2; a fake no-op FAILS. (Fails if #2 had no
    teeth.)
  · AUTONOMOUS — diagnose/select_fix carry NO fix/shape literal and there is NO
    hardcoded gap->fix map; the fix name comes out of the graph. (Source audit.)
"""
from __future__ import annotations

import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)


def _require():
    pytest.importorskip("substrate_rs")


def _fresh_agent():
    from substrate.world_adapter import WorldAdapter
    from substrate.boot_all import load_all_seeds
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    return a


# ===========================================================================
# PERCEIVE — the two defects each mint an understanding gap carrying error-features.
# ===========================================================================
def test_perceive_mints_gaps_with_error_features():
    _require()
    from domains import understanding_self_improvement as usi
    a = _fresh_agent()
    perc = usi.perceive_understanding_gaps(a)
    gaps = perc["gaps"]
    assert len(gaps) == 2, f"both defects must mint a gap: {gaps}"

    by_fac = {a.s.node(g)["attrs"]["faculty"]: a.s.node(g)["attrs"] for g in gaps}
    frag = by_fac["nominal_extraction"]
    miss = by_fac["context_sense"]
    print("\nPERCEIVE — understanding gaps with error-features:")
    for name, at in (("fragment", frag), ("mis-sense", miss)):
        print(f"  {name:<10} kind={at.get('kind')} head_is_nominal={at.get('head_is_nominal')} "
              f"sense_fits_context={at.get('sense_fits_context')}")

    assert frag.get("kind") == "understanding"
    # the fragment defect: its head is NOT a nominal (0), the sense is fine (1).
    assert float(frag.get("head_is_nominal")) == 0.0
    assert float(frag.get("sense_fits_context")) == 1.0
    # the mis-sense defect: the head IS a nominal (1), the blind sense does NOT fit (0).
    assert float(miss.get("head_is_nominal")) == 1.0
    assert float(miss.get("sense_fits_context")) == 0.0


# ===========================================================================
# DIAGNOSE — the graph decision, proven data-driven (both outcomes, verbatim).
# ===========================================================================
def test_diagnose_is_a_real_graph_decision():
    _require()
    from domains import understanding_self_improvement as usi
    a = _fresh_agent()

    # SAME Programs, DIFFERENT error-features -> DIFFERENT fix.
    frag = usi.diagnose_and_select(a, head_is_nominal=0.0, sense_fits_context=1.0)
    miss = usi.diagnose_and_select(a, head_is_nominal=1.0, sense_fits_context=0.0)

    from domains import reflective_faculty as rf
    print("\nDIAGNOSE (graph Programs understand_diagnose + understand_fix_pick):")
    print("  understand_diagnose  =", rf._load_program(a.s, "understand_diagnose"))
    print("  understand_fix_pick  =", rf._load_program(a.s, "understand_fix_pick"))
    print("  fragment gap  head_is_nominal=0 sense_fits_context=1  -> %r" % frag)
    print("  mis-sense gap head_is_nominal=1 sense_fits_context=0  -> %r" % miss)

    assert frag["shape"] == "non-nominal-extraction" and frag["fix"] == "nominal_filter"
    assert miss["shape"] == "context-blind-sense" and miss["fix"] == "sense_select"
    # a clean gap routes to NO fix (the discriminative null).
    clean = usi.diagnose_and_select(a, 1.0, 1.0)
    assert clean["shape"] == "clean" and clean["fix"] is None


# ===========================================================================
# DIAGNOSIS MATTERS — the WRONG fix FAILS its control (routing is required).
# ===========================================================================
def test_diagnosis_matters_wrong_fix_fails():
    _require()
    from domains import understanding_self_improvement as usi
    a = _fresh_agent()

    right_nf = usi.verify_fix_cleans(a, "nominal_filter", "non-nominal-extraction")
    wrong_nf = usi.verify_fix_cleans(a, "nominal_filter", "context-blind-sense")
    right_ss = usi.verify_fix_cleans(a, "sense_select", "context-blind-sense")
    wrong_ss = usi.verify_fix_cleans(a, "sense_select", "non-nominal-extraction")

    print("\nDIAGNOSIS MATTERS (discriminative — the WRONG fix fails its control):")
    print("  nominal_filter on non-nominal-extraction  accepted=%s (real_pass=%s)"
          % (right_nf["accepted"], right_nf["real_pass"]))
    print("  nominal_filter on context-blind-sense     accepted=%s (real_pass=%s)  <- WRONG"
          % (wrong_nf["accepted"], wrong_nf["real_pass"]))
    print("  sense_select   on context-blind-sense     accepted=%s (real_pass=%s)"
          % (right_ss["accepted"], right_ss["real_pass"]))
    print("  sense_select   on non-nominal-extraction  accepted=%s (real_pass=%s)  <- WRONG"
          % (wrong_ss["accepted"], wrong_ss["real_pass"]))

    assert right_nf["accepted"] is True and right_ss["accepted"] is True
    # the WRONG fix cannot clean the other shape's defect: control does NOT survive.
    assert wrong_nf["accepted"] is False and wrong_nf["real_pass"] is False
    assert wrong_ss["accepted"] is False and wrong_ss["real_pass"] is False


# ===========================================================================
# FIX COMPOSER-AUTHORED + APPLIED — the selected fix cleans the defect.
# ===========================================================================
def test_fix_composer_authored_and_applied():
    _require()
    from domains import understanding_self_improvement as usi
    from domains import consumption_quality as cq
    a = _fresh_agent()

    ap_nf = usi.apply_fix(a, "nominal_filter")
    ap_ss = usi.apply_fix(a, "sense_select")
    print("\nFIX COMPOSER-AUTHORED + APPLIED:")
    print("  nominal_filter  authored=%s  dropped=%s  kept=%s"
          % (ap_nf["authored"], ap_nf["dropped"], ap_nf["kept"]))
    print("  sense_select    authored=%s  water -> synset=%s  gloss=%r"
          % (ap_ss["authored"], ap_ss["synset"], ap_ss["sense"]))

    # the composer AUTHORED both Programs.
    assert ap_nf["authored"] is True and ap_ss["authored"] is True
    # nominal_filter cleaned the fragment defect: fragment dropped, nominal kept.
    assert usi.FRAGMENT_SURFACE in ap_nf["dropped"]
    assert usi.NOMINAL_SURFACE in ap_nf["kept"]
    # sense_select re-grounded 'water' to the SUBSTANCE sense — byte-identical to the
    # direct fix (SAME candidate set, SAME score Term).
    direct = cq._sense_in_context_uncached(
        "water", cq.context_words(usi.WATER_SENTENCE), "patient", "en")
    assert ap_ss["synset"] == direct["synset"]
    assert ap_ss["synset"] and ap_ss["synset"].startswith("water.")


# ===========================================================================
# VERIFY-GATED — the right fix passes #2; a fake no-op FAILS.
# ===========================================================================
def test_verify_gated():
    _require()
    from domains import understanding_self_improvement as usi
    a = _fresh_agent()

    ok = usi.verify_fix_cleans(a, "nominal_filter", "non-nominal-extraction")
    fake = usi.verify_fix_cleans(a, "none", "non-nominal-extraction")   # no-op
    print("\nVERIFY-GATED:")
    print("  nominal_filter accepted =", ok["accepted"], "|", ok["reason"])
    print("  fake(no-op)    accepted =", fake["accepted"], "|", fake["reason"])
    assert ok["accepted"] is True and ok["discriminates"] and ok["grounded"]
    assert fake["accepted"] is False


# ===========================================================================
# AUTONOMOUS — the decision is the graph's; no hardcoded fix, no gap->fix map.
# ===========================================================================
def test_autonomous_source_audit():
    _require()
    from domains import understanding_self_improvement as usi
    import inspect

    # the DECISION functions carry NO fix/shape literal — they only run the Programs.
    for fn in (usi.diagnose, usi.select_fix):
        body = inspect.getsource(fn)
        code = body.split('"""')[2] if body.count('"""') >= 2 else body
        for lit in ("nominal_filter", "sense_select", "non-nominal-extraction",
                    "context-blind-sense"):
            assert lit not in code, \
                f"decision fn {fn.__name__} must not hardcode {lit!r} (it is the graph's)"

    # the fix name comes OUT of the graph decision (not passed in / constant).
    a = _fresh_agent()
    frag_shape = usi.diagnose(a, 0.0, 1.0)
    frag_fix = usi.select_fix(a, frag_shape)
    miss_shape = usi.diagnose(a, 1.0, 0.0)
    miss_fix = usi.select_fix(a, miss_shape)
    print("\nAUTONOMOUS: graph decision "
          "fragment (%r -> %r) | mis-sense (%r -> %r)"
          % (frag_shape, frag_fix, miss_shape, miss_fix))
    assert frag_fix == "nominal_filter" and miss_fix == "sense_select"


# ===========================================================================
# NO REGRESSION — the reused faculties still import + expose their entry points.
# ===========================================================================
def test_no_regression_siblings_import():
    _require()
    from domains import consumption_quality as cq
    from domains import self_capability_collapse as scc
    from domains import self_verification as sv
    from domains import performance_self_improvement as psi
    assert callable(cq.ensure_nominal_filter_program)
    assert callable(cq.ensure_sense_select_program)
    assert callable(scc.perceive_capability_gaps)
    assert callable(sv.verify_claim)
    assert callable(psi.optimize)

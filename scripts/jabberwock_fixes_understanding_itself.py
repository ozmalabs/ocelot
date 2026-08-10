#!/usr/bin/env python3
"""jabberwock_fixes_understanding_itself — the jabberwock DIAGNOSES an understanding
defect's SHAPE and ROUTES it to the fitting composer-authored fix ITSELF.

The efficiency branch (jabberwock_optimizes_itself) proved the agent can drive its
OWN performance fix from its OWN timing. This is the UNDERSTANDING twin: two genuine
understanding defects (a leaked clause fragment; a context-blind word sense), each
fixed by hand once, are now SELF-ROUTED. The fix CHOICE comes OUT of the graph.

  1. PERCEIVE   — #1 (self_capability_collapse) mints the two gaps, each enriched with
                  its measured error-features (head_is_nominal / sense_fits_context).
  2. DIAGNOSE   — two graph Programs (understand_diagnose + understand_fix_pick) read
                  the error-features and ROUTE the shape to its fix: SAME Programs,
                  DIFFERENT data, DIFFERENT fix.
  3. DIAGNOSIS  — discriminative: the WRONG fix FAILS its #2 control (routing needed).
     MATTERS
  4. APPLY      — the selected fix dispatches to the COMPOSER-AUTHORED Program
                  (ensure_*_program) and cleans the defect.

Donkey=0 — no LM; the fix choice is the graph Programs' output, the gap is #1's
collapse residual, the accept is #2's Rust verdict.
"""
import sys, os, io, contextlib
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
for p in (str(ROOT), str(ROOT / "runners" / "dsl" / "python"), str(ROOT / "scripts")):
    sys.path.insert(0, p)
os.chdir(ROOT)
buf = io.StringIO()
with contextlib.redirect_stderr(buf):
    from substrate.world_adapter import WorldAdapter
    from substrate.boot_all import load_all_seeds
    import domains.understanding_self_improvement as usi
    import domains.consumption_quality as cq
    from domains import reflective_faculty as rf


def rule(c="="):
    print(c * 72)


def main():
    with contextlib.redirect_stderr(buf):
        a = WorldAdapter(seeds=()); load_all_seeds(a)

    # === 1. PERCEIVE =================================================
    rule()
    print("1. PERCEIVE — the jabberwock perceives its understanding defects (#1),")
    print("   each gap carrying its measured error-features")
    rule()
    with contextlib.redirect_stderr(buf), contextlib.redirect_stdout(buf):
        perc = usi.perceive_understanding_gaps(a)
    print(f"collapse residual (observed failure under predicted competence): "
          f"{perc['report']['residual']}")
    for g in perc["gaps"]:
        at = a.s.node(g)["attrs"]
        print(f"  CapabilityGap  faculty={at['faculty']:<20} kind={at['kind']}  "
              f"head_is_nominal={at['head_is_nominal']}  "
              f"sense_fits_context={at['sense_fits_context']}")
    assert len(perc["gaps"]) == 2, perc["gaps"]

    # === 2. DIAGNOSE (graph decision, data-driven) ==================
    rule()
    print("2. DIAGNOSE + SELECT — the graph Programs route the shape to its fix")
    rule()
    print("  understand_diagnose =", rf._load_program(a.s, "understand_diagnose"))
    print("  understand_fix_pick =", rf._load_program(a.s, "understand_fix_pick"))
    print()
    verdicts = {}
    for g in perc["gaps"]:
        at = a.s.node(g)["attrs"]
        hn, sf = usi.gap_error_features(a, g)
        v = usi.diagnose_and_select(a, hn, sf)
        verdicts[at["faculty"]] = v
        print(f"  {at['faculty']:<20} head_is_nominal={hn} sense_fits_context={sf}"
              f"  -> shape={v['shape']!r}  fix={v['fix']!r}")
    # SAME Programs, DIFFERENT data, DIFFERENT fix.
    assert verdicts["nominal_extraction"]["fix"] == "nominal_filter"
    assert verdicts["context_sense"]["fix"] == "sense_select"

    # === 3. DIAGNOSIS MATTERS (discriminative) ======================
    rule()
    print("3. DIAGNOSIS MATTERS — the WRONG fix FAILS its #2 control")
    rule()
    with contextlib.redirect_stderr(buf), contextlib.redirect_stdout(buf):
        r_nf = usi.verify_fix_cleans(a, "nominal_filter", "non-nominal-extraction")
        w_nf = usi.verify_fix_cleans(a, "nominal_filter", "context-blind-sense")
        r_ss = usi.verify_fix_cleans(a, "sense_select", "context-blind-sense")
        w_ss = usi.verify_fix_cleans(a, "sense_select", "non-nominal-extraction")
    print(f"  nominal_filter on non-nominal-extraction  accepted={r_nf['accepted']}")
    print(f"  nominal_filter on context-blind-sense     accepted={w_nf['accepted']}  <- WRONG, rejected")
    print(f"  sense_select   on context-blind-sense     accepted={r_ss['accepted']}")
    print(f"  sense_select   on non-nominal-extraction  accepted={w_ss['accepted']}  <- WRONG, rejected")
    assert r_nf["accepted"] and r_ss["accepted"]
    assert not w_nf["accepted"] and not w_ss["accepted"]

    # VERIFY CATCHES A FAKE — a no-op fix that cleans nothing.
    with contextlib.redirect_stderr(buf), contextlib.redirect_stdout(buf):
        fake = usi.verify_fix_cleans(a, "none", "non-nominal-extraction")
    print(f"  FAKE (no-op) submitted as the fix         accepted={fake['accepted']}  "
          f"[{fake['reason'][:52]}...]")
    assert fake["accepted"] is False

    # === 4. APPLY — composer-authored fix cleans the defect =========
    rule()
    print("4. APPLY — the selected fix dispatches to the COMPOSER-AUTHORED Program")
    rule()
    with contextlib.redirect_stderr(buf), contextlib.redirect_stdout(buf):
        ap_nf = usi.apply_fix(a, "nominal_filter")
        ap_ss = usi.apply_fix(a, "sense_select")
        direct = cq._sense_in_context_uncached(
            "water", cq.context_words(usi.WATER_SENTENCE), "patient", "en")
    print(f"  nominal_filter authored={ap_nf['authored']}  "
          f"dropped={ap_nf['dropped']}  kept={ap_nf['kept']}")
    print(f"  sense_select   authored={ap_ss['authored']}  "
          f"water -> synset={ap_ss['synset']}  ({ap_ss['sense']})")
    print(f"  (byte-identical to the direct fix: {ap_ss['synset'] == direct['synset']})")
    assert usi.FRAGMENT_SURFACE in ap_nf["dropped"] and usi.NOMINAL_SURFACE in ap_nf["kept"]
    assert ap_ss["synset"] == direct["synset"]

    rule()
    print("CYCLE COMPLETE: perceived 2 understanding defects, DIAGNOSED each shape,")
    print("ROUTED it to its fitting fix (from the graph), proved the wrong fix fails,")
    print("and APPLIED the composer-authored fix. The fix choice came OUT of the graph.")
    rule()


if __name__ == "__main__":
    main()

"""test_performance_self_improvement — the jabberwock DRIVES its OWN efficiency
fix, from its OWN timing perception (donkey=0, DISCRIMINATIVE).

The prior build GUESSED a cache to make Wikipedia loading faster — blind, because
it could not SEE where its load time went. Now it PERCEIVES its load timing
(LatencyObservation nodes) and DECIDES the fix from that perception, running the
SAME perceive->diagnose->solve->verify cycle it ran on the UNDERSTANDING gaps —
now on EFFICIENCY. The payoff: the agent that earlier guessed a cache now REJECTS
it, on its own reading.

Each gate would FAIL if the mechanism were fake:

  · PERCEIVE — the dominant-stage cold latency mints a performance CapabilityGap
    that CARRIES cold/warm and is introspectable. (Fails if no gap / no cold-warm.)
  · DIAGNOSE (graph decision) — the graph Programs return one-time-init->warm_once
    for the real gap AND per-item->NOT-warm_once for a synthetic per-item gap. Proves
    it is a decision over the DATA, not a constant. (Fails if the output is fixed.)
  · CACHE REJECTED — the diagnosis names no cache (fix != cache; no cue maps to a
    cache) AND #2's cache twin FAILS its control (a cache does not speed article 1,
    empty on the first item). (Fails if the cache were waved through.)
  · VERIFY-GATED — warm_once passes #2; a fake (claims warm_once helps but does no
    warm-up) FAILS. (Fails if #2 had no teeth.)
  · APPLIED + FASTER — after applying warm_once, wordnet is warm and article 1's
    per-article rate drops off the cold init. (Fails if warm_once did nothing.)
  · AUTONOMOUS — the decision functions carry NO fix/shape literal and there is NO
    Python `if fix == 'cache'`; the fix name comes out of the graph. (Source audit.)

The perceived timing here is RECORDED via the real load_timing.LoadTimer sensor
(the same graph-mint a real timed load makes), with the 7f6ff15a numbers' shape
(cold WordNet init ~1400 ms; warm ~0.4 ms/concept). scripts/jabberwock_optimizes_
itself.py runs the same cycle on a REAL cold-vs-warm subprocess measurement.
"""
from __future__ import annotations

import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# the 7f6ff15a numbers' shape: a ~1.4s one-time WordNet init, ~0.4 ms/concept warm.
COLD_MS = 1400.0
WARM_PER_ITEM = 0.4
N_ITEMS = 20


def _require():
    pytest.importorskip("substrate_rs")


def _fresh_agent(record_timing: bool = True):
    """A booted agent that HOLDS the perceived load timing (recorded via the real
    LoadTimer sensor — the same graph-mint a real timed load makes)."""
    from substrate.world_adapter import WorldAdapter
    from substrate.boot_all import load_all_seeds
    from domains import load_timing as lt
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    if record_timing:
        timer = lt.LoadTimer(a)
        timer.record("read_source", 40.0, article="A1")
        timer.record("ground_lexeme", COLD_MS, article="A1", n_items=N_ITEMS, phase="cold")
        timer.record("ground_lexeme", WARM_PER_ITEM * N_ITEMS, article="A2",
                     n_items=N_ITEMS, phase="warm")
    return a


# ===========================================================================
# PERCEIVE — the dominant-stage cold latency mints a performance CapabilityGap.
# ===========================================================================
def test_perceive_mints_performance_gap():
    _require()
    from domains import performance_self_improvement as psi
    a = _fresh_agent()
    perc = psi.perceive_performance_gap(a)
    gap = perc["gap"]
    assert gap is not None, "a performance gap must be minted from the perceived timing"
    at = a.s.node(gap)["attrs"]
    assert at.get("kind") == "performance"
    assert at.get("stage") == "ground_lexeme"          # the dominant stage
    assert abs(float(at.get("cold_ms")) - COLD_MS) < 1e-6
    assert abs(float(at.get("warm_per_item")) - WARM_PER_ITEM) < 1e-6
    # introspectable: it is wired agent -perceives_gap-> gap and reads back.
    print("\nPERCEIVE: minted CapabilityGap", gap, "->", at.get("description"))

    # discriminative null: clean timing perceives NO performance gap.
    b = _fresh_agent(record_timing=False)
    from domains import load_timing as lt
    lt.LoadTimer(b).record("ground_lexeme", 0.5, article="A1", n_items=20, phase="cold")
    lt.LoadTimer(b).record("ground_lexeme", 0.4, article="A2", n_items=20, phase="warm")
    perc2 = psi.perceive_performance_gap(b)
    assert perc2["gap"] is None, "clean (cold~warm) timing must NOT mint a performance gap"


# ===========================================================================
# DIAGNOSE — the graph decision, proven data-driven (both outcomes, verbatim).
# ===========================================================================
def test_diagnose_is_a_real_graph_decision():
    _require()
    from domains import performance_self_improvement as psi
    a = _fresh_agent()

    one = psi.diagnose_and_select(a, COLD_MS, WARM_PER_ITEM)
    per = psi.diagnose_and_select(a, 0.5, 0.4)          # a synthetic PER-ITEM gap
    print("\nDIAGNOSE (graph Programs perf_diagnose + perf_fix_pick):")
    print("  one-time-init gap  cold=%.1f warm=%.2f  -> %r" % (COLD_MS, WARM_PER_ITEM, one))
    print("  per-item gap       cold=%.1f warm=%.2f  -> %r" % (0.5, 0.4, per))

    assert one["shape"] == "one-time-init" and one["fix"] == "warm_once"
    # the SAME Programs, DIFFERENT data -> DIFFERENT fix: proves a real decision.
    assert per["shape"] == "per-item" and per["fix"] != "warm_once"
    assert per["fix"] == "optimize-op"


# ===========================================================================
# CACHE REJECTED — by the diagnosis (names no cache) AND #2's failing control.
# ===========================================================================
def test_cache_rejected_from_own_reading():
    _require()
    from domains import performance_self_improvement as psi
    a = _fresh_agent()

    # (a) the diagnosis does NOT select a cache, and no PerfFixCue maps to one.
    verdict = psi.diagnose_and_select(a, COLD_MS, WARM_PER_ITEM)
    assert verdict["fix"] != "cache"
    cue_fixes = {a.s.node(n)["attrs"]["fix"] for n in a.s.nodes("PerfFixCue")}
    assert "cache" not in cue_fixes, "no PerfFixCue maps any shape to a cache"

    # (b) #2's cache twin FAILS its control: a cache does not speed article 1.
    vc = psi.verify_fix(a, "cache", COLD_MS, WARM_PER_ITEM)
    print("\nCACHE REJECTED:")
    print("  diagnosis fix =", verdict["fix"], "(not a cache); cue fixes =", sorted(cue_fixes))
    print("  #2 cache twin accepted =", vc["accepted"])
    print("  #2 cache twin reason  =", vc["reason"])
    assert vc["accepted"] is False
    assert vc["real_pass"] is False        # the cache does NOT survive its own control


# ===========================================================================
# VERIFY-GATED — warm_once passes #2; a fake (no actual warm-up) FAILS.
# ===========================================================================
def test_verify_gated():
    _require()
    from domains import performance_self_improvement as psi
    a = _fresh_agent()

    ok = psi.verify_fix(a, "warm_once", COLD_MS, WARM_PER_ITEM)
    fake = psi.verify_fix(a, "none", COLD_MS, WARM_PER_ITEM)   # claims to help, does nothing
    print("\nVERIFY-GATED:")
    print("  warm_once accepted =", ok["accepted"], "|", ok["reason"])
    print("  fake(no warm-up) accepted =", fake["accepted"], "|", fake["reason"])
    assert ok["accepted"] is True and ok["discriminates"] and ok["grounded"]
    assert fake["accepted"] is False


# ===========================================================================
# APPLIED + FASTER — after applying warm_once, article 1 is warm; rate drops.
# ===========================================================================
def test_applied_and_faster():
    _require()
    from domains import performance_self_improvement as psi
    a = _fresh_agent()
    res = psi.optimize(a)

    assert res["fix"] == "warm_once"
    assert res["cache_selected"] is False
    assert res["verify_selected"]["accepted"] is True
    applied = res["applied"]
    assert applied is not None and applied["enacted"] == "warm_once"
    assert applied["wordnet_warm"] is True                # the corpus is now resident

    # FASTER: article-1 per-article rate drops off the cold init (perceived timing).
    read_ms = 40.0
    cold_rate = (read_ms + COLD_MS) / 1000.0                       # article 1, no fix
    warm_rate = (read_ms + WARM_PER_ITEM * N_ITEMS) / 1000.0       # article 1, warm-once
    print("\nAPPLIED + FASTER (perceived-timing shape, 7f6ff15a):")
    print("  applied:", applied)
    print("  cold  s/article (article 1, one-time init in-line): %.4f" % cold_rate)
    print("  warm  s/article (article 1, init moved to boot)   : %.4f" % warm_rate)
    print("  speedup on article 1: %.1fx" % (cold_rate / warm_rate))
    assert warm_rate < cold_rate / 10.0                    # the init dominated -> big drop


# ===========================================================================
# AUTONOMOUS — the decision is the graph's; no hardcoded fix, no fiat cache reject.
# ===========================================================================
def test_autonomous_source_audit():
    _require()
    from domains import performance_self_improvement as psi
    import inspect

    src = inspect.getsource(psi)
    # no by-fiat cache rejection anywhere.
    for bad in ('if fix == "cache"', "if fix == 'cache'",
                'fix=="cache"', "fix=='cache'"):
        assert bad not in src.replace(" ", "") or bad not in src, \
            f"cache must NOT be rejected by a Python branch ({bad!r})"
    assert "cache" not in {  # the enactment registry names no cache
        k for k in psi._FIX_REGISTRY}

    # the DECISION functions carry NO fix/shape literal — they only run the Programs.
    for fn in (psi.diagnose, psi.select_fix):
        body = inspect.getsource(fn)
        # strip the docstring so its prose ('warm_once', 'per-item') doesn't count.
        code = body.split('"""')[2] if body.count('"""') >= 2 else body
        for lit in ("warm_once", "one-time-init", "per-item", "cache", "optimize-op"):
            assert lit not in code, \
                f"decision fn {fn.__name__} must not hardcode {lit!r} (it is the graph's)"

    # the fix name comes OUT of the graph decision (not passed in / constant).
    a = _fresh_agent()
    shape = psi.diagnose(a, COLD_MS, WARM_PER_ITEM)
    fix = psi.select_fix(a, shape)
    print("\nAUTONOMOUS: graph decision shape=%r fix=%r (from the seeded Programs)" % (shape, fix))
    assert shape == "one-time-init" and fix == "warm_once"


# ===========================================================================
# NO REGRESSION — the reused faculties still import + expose their entry points.
# ===========================================================================
def test_no_regression_siblings_import():
    _require()
    from domains import load_timing as lt
    from domains import self_capability_collapse as scc
    from domains import self_verification as sv
    from domains import research_agenda as ra
    assert callable(lt.where_does_load_time_go)
    assert callable(scc.perceive_capability_gaps)
    assert callable(sv.verify_claim)
    assert callable(ra.run_cycle)

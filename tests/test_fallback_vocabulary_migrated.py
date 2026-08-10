"""Gates for the FALLBACK VOCABULARY.

The rung's whole risk is the one this project has been bitten by seven times:
**a marker that always fires and a marker that never fires both score perfectly
on one half of the gate.** So the conjunction is tested here in BOTH directions,
and every "it did not fire" assertion is paired with a positive control proving
the machinery COULD have fired.

See `VISION_FALLBACK_VOCAB_PREREG.md` (committed before implementation) and
`VISION_FALLBACK_VOCAB_RESULTS.md`.
"""
from __future__ import annotations

import pytest

pytest.importorskip("numpy")

from domains.fallback_readout import (  # noqa: E402
    ABSENCE_TYPE,
    ACTIVITY_TYPE,
    DEFAULTED_TYPE,
    EDGE_ACTIVITY,
    EDGE_DEFAULTED,
    REPORT_TYPE,
    mint_report,
    read_statuses,
    surface,
)

PROBE_SEED = 62002
SEEDS = ["vision_waves", "vision_lateral", "vision_onoff", "fallback_vocabulary"]


def _probe(drop: str | None = None):
    """Boot the audit's 3-seed probe pipeline, optionally withholding a seed's
    rules by the same in-process manifest filter the redundancy audit used.
    Nothing on disk is touched."""
    import substrate.boot_core as bc
    import substrate.seed_loader as sl

    _mf = getattr(sl, "_orig_manifest_for", None) or sl.manifest_for
    sl._orig_manifest_for = _mf

    def manifest_for(sid, *a, **k):
        m = _mf(sid, *a, **k)
        if drop and str(sid) == drop and isinstance(m, dict) and m.get("rules"):
            m = dict(m)
            m["rules"] = []
        return m

    sl.manifest_for = manifest_for
    bc.manifest_for = manifest_for
    try:
        import domains.seed_registry  # noqa: F401
        from domains.lateral_world import add_lateral_retina, set_lat_params
        from domains.wave_world import WaveWorld
        from substrate.boot_core import boot_core, load_seeds_into

        s, ag = boot_core()
        load_seeds_into(s, ag, SEEDS)
        wp = s.nodes("WaveParams")[0]
        s.set_attr(wp, "propagate", 1.0)
        s.set_attr(wp, "oja", 1.0)
        s.set_attr(wp, "oja_eta", 0.0)
        w = WaveWorld(s, h=16, w=16, seed=PROBE_SEED)
        anat = add_lateral_retina(w)
        set_lat_params(w, lateral=1.0, learn_gain=1.0, radius2=1.0,
                       lat_eta=2e-3, lat_gmax=2.0, frozen=0.0)
        s._inner.fallback_trace_reset()
        for i in range(40):
            w.step(ignite_k=1 if i % 5 == 0 else 0)
        return s, w, anat
    finally:
        sl.manifest_for = _mf
        bc.manifest_for = _mf


# --------------------------------------------------------------------------
# THE CONJUNCTION GATE — both halves, because either alone is worthless.
# --------------------------------------------------------------------------

def test_marker_does_NOT_fire_in_healthy_baseline():
    """Half (b). An unablated run must leave NO defaulted-read marker.

    Paired with its positive control below: the instrument is proven to be
    counting (over a million Attr evaluations pass through it) so this zero is
    a measured zero and not a dead instrument scoring a perfect floor (§1
    clause 4 — the failure mode that killed rung 8B).
    """
    s, _w, _anat = _probe(drop=None)
    assert s._inner.defaulted_reads() == [], \
        "a marker that fires on a healthy run is a false-positive generator"


def test_the_instrument_is_ALIVE_on_that_same_baseline():
    """The positive control for the test above. A silent instrument and a
    healthy system are indistinguishable unless this passes."""
    import substrate_rs

    substrate_rs._native.Substrate.fallback_count_totals(True)
    try:
        s, _w, _anat = _probe(drop=None)
        attr_evals, attr_defaulted = s._inner.fallback_attr_totals()
        assert attr_evals > 100_000, (
            f"the Attr counter saw only {attr_evals} evaluations — the "
            f"instrument is not on the path it claims to instrument")
        assert attr_defaulted == 0
        live = [n for (n, _m, _c, p) in s._inner.rule_costs() if p > 0]
        assert len(live) >= 5, f"the ARM is dead, not the marker: {live}"
    finally:
        substrate_rs._native.Substrate.fallback_count_totals(False)


@pytest.mark.parametrize("target", ["vision_lateral", "vision_waves"])
def test_half_a_FAILED__the_measured_negative(target):
    """Half (a) of the pre-registered conjunction gate **FAILED**, and this test
    records the failure rather than hiding it (§7: report negatives as results).

    These are the ONLY two ablations `VISION_REDUNDANCY_RESULTS.md` Arm 4
    measured as degraded-and-non-crashing. The gate required a marker on both.
    **Neither produces one**, on either hypothesis.

    THE DIAGNOSIS — established by `test_ablation_leaves_state_STALE_not_ABSENT`
    below, which is the reason this is a finding and not a bug: the vision
    arc's graph state is **eagerly initialised by the adapter at wiring time**,
    so removing a producer rule leaves its outputs **stale**, never **absent**.
    A stale read is a `.get()` HIT. Both hypotheses are built on absence, and
    absence never occurs here — it was destroyed before the rules ever ran.

    The instrument is NOT dead: `test_the_mechanism_is_sound_on_genuine_absence`
    and `test_absence_branch_instrument_is_alive` positive-control both
    counters, and the baseline pushes over a million Attr evaluations through
    this exact code path. This is a real zero, not a silent one.
    """
    s, _w, _anat = _probe(drop=target)
    assert s._inner.defaulted_reads() == [], (
        "H1 now fires on a whole-seed ablation. That CONTRADICTS this rung's "
        "measured result and the stale-not-absent diagnosis — re-open "
        "VISION_FALLBACK_VOCAB_RESULTS.md before changing this assertion.")
    assert s._inner.absence_branches() == [], (
        "H2 now fires on a whole-seed ablation — same instruction as above.")


@pytest.mark.parametrize("target", ["vision_lateral", "vision_waves"])
def test_the_ablation_ITSELF_works__positive_control_for_the_negative(target):
    """The negative above is worthless unless the ablation demonstrably bit.

    This is the control that makes "no marker fired" mean something: the
    ablation must actually remove rules and actually degrade the pipeline. It
    reproduces the audit's own cliff.
    """
    base, _w, _a = _probe(drop=None)
    live_base = sum(1 for (_n, _m, _c, p) in base._inner.rule_costs() if p > 0)
    s, _w, _anat = _probe(drop=target)
    live_abl = sum(1 for (_n, _m, _c, p) in s._inner.rule_costs() if p > 0)
    assert live_abl < live_base, (
        f"ablating {target} did not reduce the live-rule count "
        f"({live_base} -> {live_abl}) — the ablation did not take effect, so "
        f"the absence of a marker proves nothing")


def test_ablation_leaves_state_STALE_not_ABSENT__the_diagnosis():
    """THE FINDING. Why both hypotheses are structurally blind here.

    The attribute KEY SET on the affected nodes is **identical** with and
    without the ablation: `h1`, `h2`, `resid`, `g1`, `g2` all still exist after
    `vision_lateral`'s rules are withheld, holding the values the adapter
    initialised them to and that nothing ever updated.

    So the confident `channels_on` 51.976 -> 0.000 that the audit could not
    explain is **not** a defaulted read. It is a **stale read of an initialised
    zero** — and no absence-based marker can see it, because the architecture's
    own first-class "unknown = absence" was overwritten at wiring time.
    """
    base, _w, _a = _probe(drop=None)
    abl, _w2, _a2 = _probe(drop="vision_lateral")
    kb = set(base.node(base.nodes("HCell")[0])["attrs"].keys())
    ka = set(abl.node(abl.nodes("HCell")[0])["attrs"].keys())
    assert kb == ka, f"key sets diverged: only-baseline={kb - ka} only-ablated={ka - kb}"
    assert {"h1", "h2", "resid"} <= ka, (
        "lateral's own outputs are absent after ablation — that would make the "
        "defaulted-read marker viable and CONTRADICT this rung's diagnosis")


def test_the_mechanism_is_sound_on_genuine_absence():
    """H1's instrument is correct; it is the STATE MODEL that defeats it.

    When a rule genuinely reads an attribute nobody wrote, the engine records
    it and names both the rule and the key. This is what makes the negative
    above a finding about the vision arc's state, not about the instrument.
    """
    import substrate_rs

    s = substrate_rs.Substrate()
    s.add_production({"src": {"type": "P", "var": "a"}, "edge_type": "feeds",
                      "tgt": {"type": "C", "var": "b"}, "provenance": "gate"})
    p = s.add_node("P", {"written": 1.0})
    c = s.add_node("C", {"out": 0.0})
    s.add_edge(p, "feeds", c)
    s._inner.add_rule({
        "name": "gate_reads_absent", "match_type": "C",
        "match": [["a", "feeds", "b"]],
        "where": {"type": "Lt",
                  "a": {"type": "Attr", "node": {"type": "Var", "name": "b"}, "key": "out"},
                  "b": {"type": "Lit", "value": 1.0}},
        "effects": [["set_attr", "b", "out", {"__term__": {"type": "Plus", "items": [
            {"type": "Lit", "value": 1.0},
            {"type": "Attr", "node": {"type": "Var", "name": "a"}, "key": "never_written"}]}}]],
    })
    s._inner.fallback_trace_reset()
    s._inner.run_rules()
    assert s._inner.defaulted_reads() == [("gate_reads_absent", "never_written", 1)]
    # And the disease itself, demonstrated: the absent value contributed
    # silently to an arithmetic result. The rule produced a confident number
    # from something that did not exist.
    assert s.node(c)["attrs"]["out"] == 1.0


def test_absence_branch_instrument_is_alive():
    """H2's counter is positive-controlled too, so "H2 never fired" is a
    measurement and not a dead arm (§1.1 — a dead arm scores a perfect floor,
    which is exactly how a never-firing marker fakes half (b) of the gate)."""
    import substrate_rs

    s = substrate_rs.Substrate()
    s.add_production({"src": {"type": "P", "var": "a"}, "edge_type": "feeds",
                      "tgt": {"type": "C", "var": "b"}, "provenance": "gate"})
    s.add_production({"src": {"type": "C", "var": "a"}, "edge_type": "evidence",
                      "tgt": {"type": "E", "var": "b"}, "provenance": "gate"})
    p = s.add_node("P", {})
    c = s.add_node("C", {"out": 0.0})
    s.add_edge(p, "feeds", c)
    s._inner.add_rule({
        "name": "gate_absence_branch", "match_type": "C",
        "match": [["a", "feeds", "b"]],
        "where": {"type": "And", "items": [
            {"type": "Lt",
             "a": {"type": "Attr", "node": {"type": "Var", "name": "b"}, "key": "out"},
             "b": {"type": "Lit", "value": 1.0}},
            {"type": "Not", "arg": {"type": "Exists",
                "source": {"type": "Neighbours", "node": {"type": "Var", "name": "b"},
                           "edge_type": "evidence", "any_type": False},
                "var_name": "e", "predicate": {"type": "Lit", "value": True}}}]},
        "effects": [["set_attr", "b", "out", 1.0]],
    })
    s._inner.fallback_trace_reset()
    s._inner.run_rules()
    assert s._inner.absence_branches() == [("gate_absence_branch", 1)]


def test_the_vision_seeds_Not_Exists_guards_are_CLOCK_BARRIERS_not_fallbacks():
    """Why H2 is the wrong shape, measured rather than argued.

    The pre-registration predicted H2 would FALSE-POSITIVE on baseline, because
    the vision seeds' `Not(Exists(..))` guards are clock barriers that pass on
    every healthy step. **That prediction was wrong in an informative way**: the
    instrument discriminates *empty source* from *predicate never matched*, and
    the barriers' sources are NON-empty (there ARE presynaptic bipolars; they
    are simply not behind the clock). So H2 does not false-positive — it is
    simply never true here, on healthy or ablated runs alike.
    """
    s, _w, _anat = _probe(drop=None)
    assert s._inner.absence_branches() == []


# --------------------------------------------------------------------------
# THE SEPARABILITY SPLIT — the deliverable's real content.
# --------------------------------------------------------------------------

def test_healthy_and_silent_are_DISTINGUISHED_on_a_baseline_run():
    """The distinction the redundancy audit could not make.

    Its Arm 1 census found 38 rules installed into every vision-bench substrate
    that never fire once, and its Arm 5 verdict ("the reflexes are subroutines,
    not a layer") turned on the fact that apparent independence was measured
    against machinery that was never running. Both readings look like "no test
    loss" to an ablation harness. Here they are two different words.
    """
    s, _w, _anat = _probe(drop=None)
    mint_report(s)
    counts = surface(s)["counts"]
    assert counts.get("healthy", 0) > 0, "nothing ran on real inputs — arm dead"
    assert counts.get("silent", 0) > 0, (
        "no rule was classified as silent, yet the audit's census found 38 "
        "never-firing rules on this bench — the split is not being made")
    assert counts.get("healthy", 0) + counts.get("silent", 0) == len(read_statuses(s))


def test_every_RuleActivity_gets_a_status_from_the_RULES_not_from_python():
    """The classification must be total and must come from the graph.

    `mint_report` deliberately never writes `status`; if the seed rules did not
    fire, every status would be None and this fails.
    """
    s, _w, _anat = _probe(drop=None)
    mint_report(s)
    rows = read_statuses(s)
    assert rows, "nothing minted"
    unclassified = [r for r in rows if r["status"] is None]
    assert not unclassified, (
        f"{len(unclassified)} RuleActivity nodes carry no status — the seed "
        f"rules did not classify them")
    assert set(r["status"] for r in rows) <= {"healthy", "degraded", "silent"}


def test_the_degraded_rule_CAN_fire__positive_control():
    """A gate you have only ever seen pass is not a gate (§12.3), and the same
    is true of a rule you have only ever seen decline to fire.

    `fv_status_degraded` never fires on a healthy baseline, which is correct
    but leaves it untested. This drives it directly: mint a RuleActivity with
    progress > 0 and a DefaultedRead hung off it, and require the RULE to
    classify it degraded.
    """
    s, _w, _anat = _probe(drop=None)
    rep = s.add_node(REPORT_TYPE, {"name": "positive_control"})
    ra = s.add_node(ACTIVITY_TYPE, {"rule": "synthetic", "progress": 7, "count": 7})
    s.add_edge(rep, EDGE_ACTIVITY, ra)
    dr = s.add_node(DEFAULTED_TYPE, {"rule": "synthetic", "key": "h1", "hits": 3})
    s.add_edge(ra, EDGE_DEFAULTED, dr)
    s._inner.run_rules()
    got = [r for r in read_statuses(s) if r["rule"] == "synthetic"]
    assert got and got[0]["status"] == "degraded", (
        f"fv_status_degraded did not fire on a hand-built degraded case: {got}")


def test_markers_are_typed_graph_objects_not_prose():
    """Requirement 1. The redundancy audit's own marker regex matched the
    seeds' DOCUMENTATION COMMENTS and would have inverted its Arm 4 result.
    Nothing here is discoverable by a regex over prose: the markers are node
    TYPES with numeric attributes.

    Driven off the hand-built degraded case, because — per the measured
    negative above — no real vision ablation reaches this class.
    """
    s, _w, _anat = _probe(drop=None)
    rep = s.add_node(REPORT_TYPE, {"name": "typed_marker_check"})
    ra = s.add_node(ACTIVITY_TYPE, {"rule": "synthetic", "progress": 2, "count": 2})
    s.add_edge(rep, EDGE_ACTIVITY, ra)
    dr = s.add_node(DEFAULTED_TYPE, {"rule": "synthetic", "key": "h1", "hits": 3})
    s.add_edge(ra, EDGE_DEFAULTED, dr)
    assert s.nodes(DEFAULTED_TYPE), "no typed marker minted"
    for nid in s.nodes(DEFAULTED_TYPE):
        attrs = s.node(nid)["attrs"]
        assert isinstance(attrs.get("hits"), int)
        assert isinstance(attrs.get("key"), str)
        # No free-text field a prose regex could latch onto.
        assert "comment" not in attrs and "description" not in attrs


# --------------------------------------------------------------------------
# §9 — the instrument cannot move a verdict.
# --------------------------------------------------------------------------

def test_the_seed_ships_INERT():
    """Loading the vocabulary must not change graph state on its own: it mints
    no RuleActivity, so its three rules have nothing to match until a reader
    explicitly asks for a report."""
    s, _w, _anat = _probe(drop=None)
    assert s.nodes(ACTIVITY_TYPE) == [], "seed is not inert — it minted activity"
    assert s.nodes(DEFAULTED_TYPE) == []
    assert s.nodes(ABSENCE_TYPE) == []


def test_the_hit_path_denominator_is_OFF_by_default():
    """The one part of the instrument that costs anything on the healthy path
    is gated, and the gate defaults closed. A 0 denominator therefore means
    NOT MEASURED and must never be divided by."""
    s, _w, _anat = _probe(drop=None)
    attr_evals, _ = s._inner.fallback_attr_totals()
    assert attr_evals == 0, (
        "the hit-path counter ran without being asked — that is the overhead "
        "this rung promised not to impose by default")

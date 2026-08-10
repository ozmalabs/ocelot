"""GATE — the `DimInfer` argument-recording instrument and what it measured.

`VISION_DIM_INFER_ARGS_PREREG.md` (committed `a04758ee` before the instrument
existed). Every control here has GROUND TRUTH KNOWN BY CONSTRUCTION, because a
DISTINCTNESS statistic has two opposite failure modes and each one FAKES one of
the rung's two hypotheses:

    encoding carries something incidental -> distinct == calls always
                                          -> fakes IRREDUCIBLE
    encoding collapses a real determinant -> distinct == 1 always
                                          -> fakes RE-DERIVATION

Neither is caught by any "is it non-zero?" gate, and NEITHER IS CAUGHT BY G5 ON
THE N / K / PATH AXES -- on N and K the honest answer is a CONSTANT, so a broken
counter and a correct one read identically there. That is why the rung added a
DISTINCTNESS axis.

These are the twins of `shape_decode.rs::dim_infer_tests`' D-controls, run
against the SHIPPED ENGINE -- the stronger location, since it is the binary that
produced every reported number. (Those Rust tests DO run in this tree; see the
results doc §6 -- the `cargo test` link failure recorded by three predecessors
is escapable on a box with a shared libpython.)
"""
from __future__ import annotations

import json

import pytest

pytest.importorskip("substrate_rs")

from scripts.scale_split_measure import AUDIT, counters  # noqa: E402
from scripts.dim_infer_args import (  # noqa: E402
    CALLS, ORD, UNORD, I_COUNTER, DT, TROMINO, ROT_K1,
    d_red, d_green, d_codebook, d_sweep, series, point_S, _d_boot, _di, _shift,
)

SEED_FILE = "seeds/shape_decode_loop.json"


# --------------------------------------------------------------------------- #
# THE FOUR DECLARED CONTROLS (prereg §3)
# --------------------------------------------------------------------------- #
def test_d_red_identical_arguments_collapse_to_one():
    """A counter reading 7 here records something that is not an argument, and
    would report IRREDUCIBLE no matter what the engine did."""
    r = d_red()
    assert r["calls"] == 7
    assert r["distinct_ordered"] == 1
    assert r["distinct_unordered"] == 1


def test_d_green_different_goals_are_seven_distinct():
    """A counter reading 1 here has collapsed a real determinant and would
    report re-derivation that is not there."""
    r = d_green()
    assert r["calls"] == 7
    assert r["distinct_ordered"] == 7
    assert r["distinct_unordered"] == 7


def test_d_codebook_growth_is_seen_by_the_encoder():
    """THE CONTROL THAT LICENSES THE READING. The irreducibility hypothesis's
    entire content is "a decode mints graph state, so the next invocation sees
    something different". An encoder blind to codebook growth would pass D-RED
    and D-GREEN and still report re-derivation that was not there."""
    r = d_codebook()
    assert r["calls"] == 7
    assert r["distinct_ordered"] == 7
    assert r["distinct_unordered"] == 7


def test_d_sweep_is_responsive_under_g5():
    """G5 on the distinctness axis, verdict handed to `runners/dsl/src/g5.rs`."""
    sw = d_sweep()
    s = series(sw["rows"], ORD)
    c = series(sw["control"], ORD)
    assert s == [1, 2, 3, 4, 5, 6, 7]
    assert AUDIT.scale_audit_g5_verdict(s, c) == "RESPONSIVE"


# --------------------------------------------------------------------------- #
# THE SITE IS WHERE THE RUNG CLAIMS IT IS (prereg §3.1)
# --------------------------------------------------------------------------- #
def test_calls_equals_the_invocation_counter():
    """`dim_infer_arg_calls` MUST equal `term_eval:DimInfer`. If it does not,
    the recording site is not on the path the invocation counter counts and the
    whole comparison to `I` is meaningless."""
    for kw in (dict(n_cells=58, k_codebook=1, path="exact"),
               dict(n_cells=58, k_codebook=1, path="novel"),
               dict(n_cells=58, k_codebook=8, path="exact")):
        c, _ = point_S(**kw)
        assert int(c[CALLS]) == int(c[I_COUNTER]), kw


def test_the_site_is_silent_while_the_audit_is_off():
    """PROTOCOL §9 — a recording site that counted on the default path would
    contaminate every committed result."""
    s, ag, native = _d_boot()
    AUDIT.scale_audit_reset()
    AUDIT.scale_audit_set_enabled(False)
    for _ in range(5):
        _di(native, ROT_K1)
    c = counters()
    assert int(c.get(CALLS, 0)) == 0
    assert int(c.get(ORD, 0)) == 0
    assert int(c.get(UNORD, 0)) == 0


# --------------------------------------------------------------------------- #
# THE MEASUREMENT (prereg §5)
# --------------------------------------------------------------------------- #
def test_the_headline_reproduces():
    """`I` = 17, `distinct` = 10, at the exact point the identity-cost rung
    measured `I` = 17. REDUCIBLE by the pre-registered decision rule."""
    c, status = point_S(142, k_codebook=1, path="exact")
    assert status == "recognized_transformed", "a floor score from a dead arm is not a measurement"
    assert int(c[I_COUNTER]) == 17
    assert int(c[CALLS]) == 17
    assert int(c[ORD]) == 10
    assert int(c[UNORD]) == 10


def test_the_novel_path_has_no_redundancy():
    """`I` = 2 and `distinct` = 2 — every invocation on the failing path is
    already distinct. The redundancy is a property of RECOGNITION."""
    c, status = point_S(58, k_codebook=1, path="novel")
    assert status == "minted"
    assert int(c[I_COUNTER]) == 2
    assert int(c[ORD]) == 2


def test_distinct_is_invariant_in_N_and_K():
    """`I` does not vary with problem size, and neither does `distinct` — which
    is the first hint that `I` is not a scheduling quantity at all."""
    for n in (12, 58, 142):
        c, _ = point_S(n, k_codebook=1, path="exact")
        assert (int(c[I_COUNTER]), int(c[ORD])) == (17, 10), n
    for k in (1, 8, 16):
        c, _ = point_S(58, k_codebook=k, path="exact")
        assert (int(c[I_COUNTER]), int(c[ORD])) == (17, 10), k


# --------------------------------------------------------------------------- #
# THE MECHANISM (the "name it, do not fix it" half of the brief)
# --------------------------------------------------------------------------- #
def test_I_is_the_seed_s_own_DimInfer_SITE_COUNT():
    """**`I` = 17 IS NOT A SCHEDULING CONSTANT — IT IS A COUNT OF TERM SITES IN
    A JSON FILE**, and `distinct` = 10 is the number of DISTINCT `field`
    selectors among them.

    An AST walk over the seed's own structure (never a substring selector):
    every `{"type": "DimInfer", ...}` node, counted by its `field`. The
    per-field multiset must equal the per-tuple call-count multiset the trace
    records — an exact structural reconciliation, not a coincidence of totals.
    """
    import collections
    seed = json.load(open(SEED_FILE))
    fields = collections.Counter()

    def walk(o):
        if isinstance(o, dict):
            if o.get("type") == "DimInfer":
                fields[o.get("field")] += 1
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)

    walk(seed)
    assert sum(fields.values()) == 17, "seventeen DimInfer Term sites in the seed"
    assert len(fields) == 10, "ten distinct field selectors among them"

    # the trace's per-tuple call counts must be the SAME multiset
    from scripts.dim_infer_args_diagnose import run_point, trace_summary
    _c, trace, _encs, status = run_point(142, 1, "exact")
    assert status == "recognized_transformed"
    ts = trace_summary(trace)
    got = sorted(ts["per_tuple_call_count"].values(), reverse=True)
    want = sorted(fields.values(), reverse=True)
    assert got == want, f"trace {got} != seed site census {want}"


def test_only_the_field_selector_varies_across_the_invocations():
    """**THE MECHANISM.** Every determinant of the DECODE — the codebook, the
    generators, the goal, `max_dims` — is CONSTANT across all seventeen
    invocations. The only thing that differs is `field`, which
    `shape_decode.rs::finish` applies to an ALREADY-COMPUTED result and which
    therefore cannot affect one unit of the decode's work.

    So the seventeen invocations are ONE decode computed seventeen times, read
    off ten different ways — and the pre-registered statistic (10) UNDER-STATES
    the redundancy, because `field` is a real determinant of the RETURN VALUE
    but not of the WORK. That the registered statistic was the conservative one
    is the point: it was fixed before any of this was visible.
    """
    from scripts.dim_infer_args_diagnose import run_point, which_fields_differ
    _c, _trace, encs, status = run_point(142, 1, "exact")
    assert status == "recognized_transformed"
    fd = which_fields_differ(encs)
    assert fd["md"]["constant"], "max_dims varies — the mechanism is not what was reported"
    assert fd["parts"]["constant"], "the codebook varies — decodes would be genuinely distinct"
    assert fd["gens"]["constant"], "the generators vary"
    assert fd["goal"]["constant"], "the residual varies"
    assert not fd["fd"]["constant"], "the field selector must be the one that moves"
    assert fd["fd"]["distinct_values"] == 10

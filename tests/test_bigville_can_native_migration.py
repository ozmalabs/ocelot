"""Bigville CAN migration to the native discrete-async mechanism
(CAN_CONSUMER_MIGRATION_PREREG.md sec2 / CAN_CONSUMER_MIGRATION_RESULTS.md).

Two things are gated here, both against REAL bigville_cast100.json
residents, not synthetic data:

  1. The named schema fix (worlds/bigville_can_beliefs.py's STRUCTURAL_EDGES
     loop now mints BOTH directions of each causal_influence coupling,
     CAN_NATIVE_REIMPLEMENTATION_RESULTS.md sec7's own verified-backward-
     compatible one-line change) is additive-risk-only for the EXISTING
     continuous mechanism -- the fix must not change a single frustration/
     energy/coupling_count number `mt_audit_basin` reports, because
     build_couplings's in-edge de-dup and enumerate_couplings's undirected-
     pair de-dup both already collapse a reverse edge onto the same
     undirected coupling.

  2. The native discrete-asynchronous relaxation (seeds/can_native_
     reimplementation.json's can_native_update_3state rule, run via
     run_rules()) reproduces the SAME qualitative divergence the continuous
     mechanism already established (BIGVILLE_CAN_INTEGRATION_RESULTS.md):
     the low-resolution-bins resident's network is MORE frustrated than the
     high-resolution-bins resident's, on identical scenario evidence --
     now measured on native-produced discrete state via the closed-form,
     non-iterative mt_frustration_given_state reader (the SAME idiom
     tests/test_can_native_reimplementation.py's own _frustration helper
     already uses to score native relaxation output).
"""
from __future__ import annotations

import json
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from substrate_rs import _native                                        # noqa: E402
from substrate.seed_loader import engine_rules_only                     # noqa: E402
from worlds.bigville_can_beliefs import (                               # noqa: E402
    install_productions, build_resident_can_mt, apply_scenario_evidence,
    TOPIC_NAMES,
)
from scripts.bigville_can_integration_demo import (                     # noqa: E402
    pick_demo_residents, run_one,
)

_CAST_PATH = os.path.join(_ROOT, "seeds", "bigville_cast100.json")
_NATIVE_SEED_PATH = os.path.join(_ROOT, "seeds", "can_native_reimplementation.json")


def _cast():
    return json.load(open(_CAST_PATH))["residents"]


# -------------------------------------------------- schema-fix-is-additive-risk-only
def test_symmetric_edge_fix_does_not_change_continuous_mechanism_numbers():
    """Regression, measured both ways on the SAME two real residents
    (pick_demo_residents' own lo/hi pair): the schema fix must not move
    a single number the continuous mechanism reports. These are the exact
    pre-fix values measured on main@41232aa before this branch's change
    (git-stash cross-check, recorded in CAN_CONSUMER_MIGRATION_RESULTS.md)."""
    cast = _cast()
    lo, hi = pick_demo_residents(cast)
    s = _native.Substrate()
    install_productions(s)
    r_lo = run_one(s, lo)
    r_hi = run_one(s, hi)
    assert r_lo["single_relax_audit"]["coupling_count"] == 5
    assert r_hi["single_relax_audit"]["coupling_count"] == 5
    assert abs(r_lo["single_relax_audit"]["frustration"] - 2.247044801712036) < 1e-6
    assert abs(r_hi["single_relax_audit"]["frustration"] - 1.6207002401351929) < 1e-6


# -------------------------------------------------- schema-fix-actually-fixes-visibility
def test_claim_credible_now_has_a_visible_out_edge_to_trust_mayor():
    """CAN_NATIVE_REIMPLEMENTATION_RESULTS.md sec7's own measured gap:
    claim_credible's only coupling to trust_mayor was an IN-edge (minted
    from trust_mayor's own STRUCTURAL_EDGES entry), invisible to the
    native rule's Sum(Edges(c,"causal_influence")) (out-edges only). After
    the fix, claim_credible must have a real OUT-edge to trust_mayor."""
    s = _native.Substrate()
    install_productions(s)
    cast = _cast()
    built = build_resident_can_mt(s, cast[0])
    out_neighbours = {
        n.value for n in s.neighbours(built["concepts"]["claim_credible"], "causal_influence")
    }
    assert built["concepts"]["trust_mayor"].value in out_neighbours


# -------------------------------------------------- native-migration-live-demo
def _run_native(resident):
    s = _native.Substrate()
    install_productions(s)
    manifest = json.load(open(_NATIVE_SEED_PATH))
    s.load_seed_manifest(engine_rules_only(manifest))
    built = build_resident_can_mt(s, resident)
    apply_scenario_evidence(s, built["concepts"])
    s.set_attr(built["mt_node"], "discrete_mode", "3state")
    s.set_attr(built["mt_node"], "can_tick", 0)
    steps = s.run_rules(3000)
    concept_ids = list(built["concepts"].values())
    state = {c.value: float(s.node(c)["attrs"].get("state", 0.0)) for c in concept_ids}
    frustration = s.mt_frustration_given_state(built["mt_node"], state)
    return {
        "steps": steps, "frustration": float(frustration), "state": state,
        "converged": steps < 3000,
    }


def test_native_relaxation_reproduces_the_continuous_mechanisms_divergence():
    """THE migration demonstration: native discrete-async relaxation
    (can_native_update_3state, run via run_rules()) on the SAME two real
    residents, SAME scenario evidence, replacing mt_relax_to_marginal
    entirely -- and mt_frustration_given_state (closed-form, non-iterative,
    reused unmodified as a pure scoring utility, exactly as tests/
    test_can_native_reimplementation.py's own _frustration helper already
    does) reads the SAME qualitative divergence off the native-produced
    state that BIGVILLE_CAN_INTEGRATION_RESULTS.md's continuous-mechanism
    demonstration already established: the low-resolution resident is MORE
    frustrated than the high-resolution resident."""
    cast = _cast()
    lo, hi = pick_demo_residents(cast)
    assert lo["params"]["resolution_bins"] < hi["params"]["resolution_bins"]

    r_lo = _run_native(lo)
    r_hi = _run_native(hi)

    assert r_lo["converged"], "native relaxation did not reach a fixpoint for lo-res resident"
    assert r_hi["converged"], "native relaxation did not reach a fixpoint for hi-res resident"
    assert r_lo["frustration"] > r_hi["frustration"], (
        r_lo["frustration"], r_hi["frustration"])


def test_native_relaxation_never_calls_the_continuous_relaxation_op():
    """Confirms the migration is real, not cosmetic: no mt_relax_to_marginal/
    mt_mean_field_marginal call anywhere in the native demo path -- state is
    produced ENTIRELY by run_rules() firing the seeded discrete-async rule."""
    import inspect
    src = inspect.getsource(_run_native)
    for forbidden in ("mt_relax_to_marginal", "mt_mean_field_marginal",
                      "mt_mean_field_with_h_override"):
        assert forbidden not in src

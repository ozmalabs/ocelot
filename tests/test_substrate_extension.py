"""test_substrate_extension — SELF-IMPROVEMENT #4: the agent extends its OWN
substrate as far as its held primitives reach, and SPECS the residual it cannot.

Gates, discriminative, donkey=0:

  COMPOSE (headline) — a CapabilityGap solvable by COMPOSITION becomes a WHOLE
    FACULTY: a multi-rule CHAIN (> 1 rule, a real composition) the agent's composer
    authors + installs, and the gap's challenge (an unhandled item) now SUCCEEDS.

  SPEC (the honest boundary) — a CapabilityGap that CANNOT be expressed by held
    primitives becomes a PrimitiveRequest with a well-formed spec (name / operation /
    inputs / outputs / why-uncomposable / example), instead of a silent wall or a fake.

  DISCRIMINATIVE — the SAME loop routes a composable gap to a composition and a
    primitive-needing gap to a spec (the discriminator is the grounding result).

  VERIFY-BEFORE-TRUST — a COMPLETE faculty is accepted (control discriminates, no
    regression, grounded); an INCOMPLETE faculty that does NOT fill the gap is
    REJECTED (the control has teeth).

  GRAPH-NATIVE — the authored faculty is graph data (live exportable rules); the
    PrimitiveRequest is a graph node; the loop routes through the held composer +
    held verifier (source/spy audit), not a Python decision.

  NO REGRESSION — the existing single-rule composers still author their one rule.
"""
from __future__ import annotations

import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from substrate.world_adapter import WorldAdapter
import domains.reflective_faculty as rf
from domains import substrate_extension as se


# ---------------------------------------------------------------------------
# harness — mechanical graph I/O, no agent decisions.
# ---------------------------------------------------------------------------
def _fresh():
    return WorldAdapter(seeds=())


def _compose_gap(a, faculty="input_handling"):
    """A gap whose observation names a MULTI-STAGE need (classify -> route ->
    finalize) — solvable by a composition of held primitives."""
    return a.s.add_node("CapabilityGap", {
        "faculty": faculty,
        "observation": [["classify the item", "self", "input"],
                        ["route to a handler", "input", "handler"],
                        ["mark handled", "handler", "done"]],
        "status": "perceived",
    })


def _partial_gap(a, faculty="partial_pipe"):
    """A gap that grounds to only classify + route (NO finalize) — the authored
    faculty is a real composition (2 rules) but does NOT fill the gap."""
    return a.s.add_node("CapabilityGap", {
        "faculty": faculty,
        "observation": [["classify the item", "self", "input"],
                        ["route to a handler", "input", "handler"]],
        "status": "perceived",
    })


def _spectral_gap(a, faculty="colour_perception"):
    """A COMPUTATIONAL gap: it needs a new spectral-value primitive (a pure transform
    signal -> per-frequency-bin magnitude, log-scaled). The residual grounds to NO held
    RULE relation (it WALLS) — but it is a computation the agent can CONSTRUCT as a
    native Term-tree, so the corrected cycle BUILDS it (not a human hand-off)."""
    return a.s.add_node("CapabilityGap", {
        "faculty": faculty,
        "observation": [["spectral_value", "signal", "magnitude"],
                        ["log_scale", "magnitude", "value"]],
        "needed_primitive": "spectral_value",
        "n_samples": 32, "test_frequencies": [3, 7, 11],
        "inputs": ["signal"], "outputs": ["spectrum"],
        "example": "colour as a frequency+amplitude frame: a per-bin log-magnitude",
        "status": "perceived",
    })


def _world_io_gap(a, faculty="hearing"):
    """A WORLD-I/O gap: a new SENSOR — a boundary to external reality. No Term reads a
    microphone, so this is the GENUINE residual the agent cannot build and must SPEC."""
    return a.s.add_node("CapabilityGap", {
        "faculty": faculty,
        "observation": [["read_microphone", "acoustic_reality", "audio_buffer"]],
        "needed_primitive": "microphone_read", "primitive_kind": "world_io",
        "inputs": ["acoustic_reality"], "outputs": ["audio_buffer"],
        "example": "read live acoustic pressure from the microphone into an audio buffer",
        "status": "perceived",
    })


def _probe_item_handled(a, raw="probe"):
    """Add a hub-fed item, run the installed rules, read back whether it was handled."""
    hub = a.s.add_node("Hub", {})
    it = a.s.add_node("Item", {"raw": raw})
    a.inner.add_edge_unchecked(hub, "has_item", it)
    a.inner.run_rules()
    return a.s.node(it)["attrs"].get("handled")


# ===========================================================================
# COMPOSE — the headline: a multi-rule faculty is authored, installed, fills gap.
# ===========================================================================
def test_compose_authors_multi_rule_faculty():
    a = _fresh()
    gap = _compose_gap(a)
    res = se.extend_for_gap(a, gap)
    assert res["outcome"] == "composed"
    # a genuine COMPOSITION: more than one rule (not a single rule).
    assert res["composition"] is True
    assert res["n_rules"] > 1
    assert len(res["rules"]) == res["n_rules"] >= 3
    # it is the agent's COMPOSER that authored it (the migration ledger).
    assert res["served_by"] in ("graph", "python")
    assert res["path"] == "compose_faculty_pipeline"


def test_composed_faculty_fills_the_gap_before_after():
    a = _fresh()
    # BEFORE: no faculty -> an unhandled item stays unhandled.
    assert _probe_item_handled(a, "before") in (None,)
    # compose + install the faculty.
    res = se.extend_for_gap(a, _compose_gap(a))
    assert res["outcome"] == "composed"
    # AFTER: a fresh unhandled item is now handled by the installed chain.
    assert _probe_item_handled(a, "after") == 1.0


def test_composed_rules_chain_each_stage_consumes_prior():
    # the composition is a genuine CHAIN: route consumes classify's output
    # (stage==classified), finalize consumes route's (routed_to + stage==routed).
    a = _fresh()
    res = se.extend_for_gap(a, _compose_gap(a))
    by = {r["name"].rsplit("_gap_", 1)[0] if "_gap_" in r["name"] else r["name"]: r
          for r in res["rules"]}
    names = [r["name"] for r in res["rules"]]
    assert any(n.startswith("pl_classify_") for n in names)
    assert any(n.startswith("pl_route_") for n in names)
    assert any(n.startswith("pl_finalize_") for n in names)
    route = next(r for r in res["rules"] if r["name"].startswith("pl_route_"))
    fin = next(r for r in res["rules"] if r["name"].startswith("pl_finalize_"))
    # route's where reads stage == 'classified' (stage 1's output).
    assert route["where"]["b"]["value"] == "classified"
    # finalize matches the routed_to edge stage 2 minted.
    assert ["it", "routed_to", "h"] in fin["match"]


# ===========================================================================
# BUILD (headline) — a computational gap at the wall -> a REAL native Term-tree
# primitive, constructed + admitted + verified + installed, that ACTUALLY COMPUTES.
# ===========================================================================
def test_build_real_primitive_headline():
    a = _fresh()
    res = se.extend_for_gap(a, _spectral_gap(a))
    # the wall did NOT hand off to a human — the agent BUILT the primitive.
    assert res["outcome"] == "built_primitive"
    assert res["name"] == "spectral_value"
    assert res["admitted"] is True and res["accepted"] is True
    # it is a REAL native Term-tree (a composition of held constructors), not a stub.
    term = res["term_tree"]
    assert term["type"] == "Log"                            # log-scaled magnitude
    _types = _term_types(term)
    for t in ("Sum", "Cos", "Sin", "Nth", "Sqrt", "Pow"):   # composed from held Terms
        assert t in _types, f"expected {t} in the constructed Term-tree"
    # it is graph-resident (materialised via add_term_subgraph) + INSTALLED.
    assert res["term_root"]
    held = [a.s.node(n)["attrs"] for n in a.s.nodes("HeldPrimitive")]
    assert any(h.get("name") == "spectral_value" and h.get("status") == "installed"
               for h in held)


def test_built_primitive_actually_computes():
    # NOT a hardcoded answer: evaluate the built term natively — a pure tone at bin f
    # must peak at bin f (energy in the correct frequency bin).
    a = _fresh()
    res = se.extend_for_gap(a, _spectral_gap(a))
    assert res["object_props"] == {"peak_bin@3": 3, "peak_bin@7": 7, "peak_bin@11": 11}
    # the printed test-eval is a REAL spectrum whose argmax is the input tone.
    te = res["test_eval"]
    spec = te["spectrum"]
    assert spec[te["tone"]] == max(spec)                    # peak at the tone's own bin
    # re-run the installed native term directly on a fresh tone -> correct bin.
    import math
    Ns = te["n_samples"]
    for f in (5, 9):
        samp = [(float(n), math.cos(2 * math.pi * f * n / Ns)) for n in range(Ns)]
        vals = [float(a.inner.evaluate(res["term_tree"],
                {"sig": samp, "k": float(kk), "N": float(Ns)})) for kk in range(Ns // 2 + 1)]
        assert vals.index(max(vals)) == f


def test_admissibility_gate_rejects_wrong_primitive(monkeypatch):
    # a WRONG construction (a non-selective DC magnitude that ignores the frequency bin)
    # does NOT reproduce the gap's stated constraint -> REJECTED by the gate, NOT installed.
    a = _fresh()
    monkeypatch.setattr(se, "_spectral_logmag_term", se._spectral_nonselective_term)
    res = se.extend_for_gap(a, _spectral_gap(a))
    assert res["outcome"] == "rejected_primitive"
    assert res["stage"] == "admissibility"
    assert res["admitted"] is False
    # the wrong term put every tone's energy in one constant bin (no selectivity).
    assert set(res["object_props"].values()) == {0}
    # nothing was installed — the wall stands honestly.
    assert list(a.s.nodes("HeldPrimitive")) == []
    assert a.s.node(_only_gap(a))["attrs"].get("status") == "primitive_rejected"


def _term_types(term) -> set:
    """Collect every Term `type` in a raw-dict Term-tree (mechanical walk)."""
    out = set()
    def walk(t):
        if isinstance(t, dict):
            if "type" in t:
                out.add(t["type"])
            for v in t.values():
                walk(v)
        elif isinstance(t, (list, tuple)):
            for v in t:
                walk(v)
    walk(term)
    return out


# ===========================================================================
# SPEC — the honest boundary SHRINKS to WORLD-I/O: a sensor/effector -> a spec.
# ===========================================================================
def test_spec_mints_well_formed_primitive_request():
    a = _fresh()
    gap = _world_io_gap(a)
    res = se.extend_for_gap(a, gap)
    assert res["outcome"] == "primitive_request"
    assert res["residual_kind"] == "world_io"               # a genuine boundary to reality
    spec = res["spec"]
    # every spec field is present + well-formed.
    assert spec["name"] == "microphone_read"
    assert spec["operation"]
    assert list(spec["inputs"]) == ["acoustic_reality"]
    assert list(spec["outputs"]) == ["audio_buffer"]
    assert spec["example"]
    # WHY-uncomposable is READ OFF the actual grounding wall (not fabricated).
    assert "ground" in spec["why_uncomposable"].lower()
    # it is a real graph node the host can act on.
    node = se.is_primitive_request(a, "microphone_read")
    assert node is not None
    assert a.s.node(node)["attrs"].get("for_host") is True


def test_spec_primitive_request_idempotent():
    a = _fresh()
    se.extend_for_gap(a, _world_io_gap(a))
    n_before = len(list(a.s.nodes("PrimitiveRequest")))
    # re-running the same gap does not mint a duplicate request.
    se.extend_for_gap(a, _world_io_gap(a))
    assert len(list(a.s.nodes("PrimitiveRequest"))) == n_before


# ===========================================================================
# DISCRIMINATIVE — one loop, THREE honest outcomes, by the wall's kind:
# composable -> compose ; computational -> BUILD ; world-I/O -> SPEC.
# ===========================================================================
def test_discriminative_compose_build_spec():
    a = _fresh()
    rc = se.extend_for_gap(a, _compose_gap(a))
    rb = se.extend_for_gap(a, _spectral_gap(a))
    rp = se.extend_for_gap(a, _world_io_gap(a))
    assert rc["outcome"] == "composed"
    assert rb["outcome"] == "built_primitive"               # computational -> BUILT
    assert rp["outcome"] == "primitive_request"             # world-I/O -> SPEC
    # each path produced only its own artefact — the discriminator separates them.
    assert "primitive_request" not in rc and "primitive_request" not in rb
    assert "rules" not in rb and "rules" not in rp
    assert "term_tree" not in rp


# ===========================================================================
# VERIFY-BEFORE-TRUST — complete accepted; incomplete rejected (teeth).
# ===========================================================================
def test_verify_accepts_complete_faculty():
    a = _fresh()
    res = se.extend_for_gap(a, _compose_gap(a))
    v = res["verified"]
    assert res["accepted"] is True
    assert v["discriminates"] is True
    assert v["no_regression"] is True
    assert v["grounded"] is True
    assert a.s.node(_only_gap(a))["attrs"].get("status") == "accepted"


def test_verify_has_teeth_rejects_incomplete_faculty():
    # a FRESH agent (no complete faculty installed) — an incomplete classify+route
    # faculty is a genuine 2-rule composition but never sets handled, so the
    # control's positive case fails: REJECTED.
    a = _fresh()
    res = se.extend_for_gap(a, _partial_gap(a))
    assert res["outcome"] == "composed"
    assert res["composition"] is True and res["n_rules"] == 2   # still a real composition
    assert res["accepted"] is False                              # but it does NOT fill the gap
    assert res["verified"]["real_pass"] is False
    assert a.s.node(_only_gap(a))["attrs"].get("status") == "rejected"


def _only_gap(a):
    return next(iter(a.s.nodes("CapabilityGap")))


# ===========================================================================
# GRAPH-NATIVE audit — authored faculty is live graph data; the loop routes
# through the held composer + held verifier, not a Python decision.
# ===========================================================================
def test_authored_faculty_is_live_graph_data():
    a = _fresh()
    res = se.extend_for_gap(a, _compose_gap(a))
    live = {r.get("name") for r in a.inner.export_rules() if isinstance(r, dict)}
    for r in res["rules"]:
        assert r["name"] in live                                # the rules are LIVE in the graph
        # each is a well-formed graph rule (match/where/effects).
        assert set(("name", "match", "where", "effects")) <= set(r)


def test_primitive_request_is_a_graph_node():
    a = _fresh()
    se.extend_for_gap(a, _world_io_gap(a))
    nodes = list(a.s.nodes("PrimitiveRequest"))
    assert len(nodes) == 1
    at = a.s.node(nodes[0])["attrs"]
    for k in ("name", "operation", "inputs", "outputs", "why_uncomposable", "example"):
        assert k in at


def test_loop_routes_through_held_composer(monkeypatch):
    # SPY: prove extend_for_gap authors via the held composer (rf.ground_concern),
    # not a bespoke Python authoring path.
    a = _fresh()
    seen = {}
    real = rf.ground_concern

    def spy(agent, keys, **kw):
        seen["called"] = True
        return real(agent, keys, **kw)

    monkeypatch.setattr(rf, "ground_concern", spy)
    se.extend_for_gap(a, _compose_gap(a))
    assert seen.get("called") is True


def test_loop_routes_through_held_verifier(monkeypatch):
    # SPY: the accept decision is the held self_verification's, not this module's.
    from domains import self_verification as sv
    a = _fresh()
    seen = {}
    real = sv.verify_claim

    def spy(agent, claim):
        seen["called"] = True
        return real(agent, claim)

    monkeypatch.setattr(sv, "verify_claim", spy)
    se.extend_for_gap(a, _compose_gap(a))
    assert seen.get("called") is True


# ===========================================================================
# NO REGRESSION — the existing single-rule composers still author their rule.
# ===========================================================================
@pytest.mark.parametrize("composer,keys,rels,rp", [
    ("control", ["nr1"], [("control", "X", "Y")], {"control"}),
    ("attention", ["nr2"], [("watch", "X", "Y")], {"watch"}),
    ("communicate", ["nr3"],
     [("source", "X", "Y"), ("decompose", "X", "Y"), ("communicate", "X", "Y")],
     {"source", "decompose", "communicate"}),
])
def test_single_rule_composers_unbroken(composer, keys, rels, rp):
    a = _fresh()
    builder = rf._COMPOSER_REGISTRY[composer]
    res = builder(a, keys, rels)
    assert res.get("grounded") is True


def test_pipeline_composer_registered():
    # the new composer is registered WITHOUT displacing the existing ones.
    assert "pipeline" in rf._COMPOSER_REGISTRY
    for name in ("control", "grouping", "decision", "communicate", "experiment",
                 "attention", "conceptualize"):
        assert name in rf._COMPOSER_REGISTRY

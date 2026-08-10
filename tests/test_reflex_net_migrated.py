"""Reflex nets — the primal layer: a constructed net evaluated NATIVELY
inside the graph, gated by a basin check EXTERNAL to the net, toggled by
a held knob (optional), adopted/ablated by the EXISTING rule machinery.

The design (see REFLEX_NET_DESIGN.md):

  * A reflex net is ordinary graph data — a `NetworkAssemblage` (+ its
    `WeightTensor` children) that the `NetForward` Rust Term evaluates
    at native speed. No torch, authored-not-trained, exact.
  * The FAST PATH is an ordinary Rule whose `where` gates on (a) a
    residual/basin membership EXTERNAL to the net and (b) an `enabled`
    knob, so the confidently-wrong-outside-basin failure is caught by a
    grounded gate the net cannot fake, and the whole layer is OFF by
    default (optional) and reconfigurable with zero code (tweakable).
  * Because the fast path IS a Rule, adopt/ablate/tweak reuse the
    substrate's rule spine (`add_rule`/`remove_rule` + `TunableParameter`)
    with no new executor.

This gate proves the keystone first: `NetForward` computes byte-for-byte
what the Python `code_writing_cortex.forward()` computes.
"""
from __future__ import annotations

import pytest
from substrate_rs import _native
from domains.code_writing_cortex import CodeWritingCortex


# ---------------------------------------------------------------------------
# Minimal open-substrate harness (mirrors tests/test_gadgets.py) — enough
# productions to let the cortex build a NetworkAssemblage from a gadget.
# ---------------------------------------------------------------------------

_NODE_TYPES = (
    "Microtheory", "Concept", "DesignPattern", "DesignExclusion",
    "CodeTarget", "ProgrammingLanguage", "LanguageExclusion",
    "LanguageScoringConfig", "CodeWritingCortex", "CodeAuthoringRoot",
    "Reflex", "ReplacementTarget", "CodeDraft", "ValidationResult",
    "CodeInstallation", "NetworkAssemblage", "AssemblageStep",
    "WeightTensor",
    # reflex-net layer
    "ReflexNet", "ReflexQuery", "ReflexTrial", "TunableParameter", "Agent",
    "ReflexNetPolicy", "ShapeSignature", "Observation",
    "RustExtensionSpec", "ExtensionProposal", "TrainingJob",
    "ReflexObservation",
)
_EDGE_TYPES = (
    "genlMt", "has_concept", "owns_microtheory", "owns_root",
    "has_reflex", "current_target", "has_draft", "validated_by",
    "installed_as", "authored_in", "uses_pattern", "subClassOf",
    "in_category", "has_assemblage", "has_step", "has_weight",
    # reflex-net layer
    "for_net", "net_assemblage", "has_tunable", "judges", "proposed_from",
    "validates", "for_reflex", "train_for", "trained_net", "observes",
)


def _fresh_substrate():
    s = _native.Substrate()
    for src_t in _NODE_TYPES:
        for tgt_t in _NODE_TYPES:
            for et in _EDGE_TYPES:
                s.add_production({
                    "src": {"type": src_t, "var": "src"},
                    "edge_type": et,
                    "tgt": {"type": tgt_t, "var": "tgt"},
                    "where": None,
                    "weight": {"type": "Lit", "value": 1.0},
                    "provenance": "test:open",
                })
    return s


def _seed_parents(s):
    s.add_node("Microtheory", {"name": "compiler_theory"})
    s.add_node("Microtheory", {"name": "neural_networks"})
    s.add_node("Microtheory", {"name": "code_authoring"})


class _A:
    def op_stats(self):
        return {}


def _install_policy(s, *, hot_ms_threshold=0.05, default_basin_threshold=0.25):
    """Install the tweakable ReflexNetPolicy singleton (what the seed ships
    in its `nodes`). auto_propose_reflex_net reads its thresholds."""
    return s.add_node("ReflexNetPolicy", {
        "kind": "reflex_net_policy",
        "hot_ms_threshold": float(hot_ms_threshold),
        "default_basin_threshold": float(default_basin_threshold),
    })


def _build_square_net(s):
    """Construct the square_pwl_signed_gadget net (abs + 10-seg PWL square)
    — a real multi-step assemblage, the hardest parity case."""
    from substrate.boot_all import load_one_seed

    _seed_parents(s)
    cortex = CodeWritingCortex(s, agent=_A()).install()
    load_one_seed(s, "gadgets")

    target = s.add_node("ReplacementTarget", {
        "op_name": "compute_square", "baseline_total_ms": 100.0,
        "baseline_count": 1000, "baseline_mean_ms": 0.1, "selected_at": 0.0,
    })
    root = cortex._ensure_root()
    s.add_edge(root, "current_target", target, {})
    top = next(n for n in s.nodes("DesignPattern")
               if s.node(n)["attrs"].get("name") == "square_pwl_signed_gadget")
    s.add_edge(target, "uses_pattern", top, {})

    assemblage = cortex.assemble_network(target)
    cortex.construct_weights(assemblage)
    return cortex, assemblage


def _native_forward(s, assemblage, inputs):
    """Evaluate the net via the native `NetForward` Term. The assemblage
    node is bound through `env` (a NodeID isn't JSON-serialisable inside
    the term itself); only plain floats live in the term as a Lit."""
    term = {
        "type": "NetForward",
        "assemblage": {"type": "Var", "name": "a"},
        "inputs": {"type": "Lit", "value": [float(v) for v in inputs]},
    }
    out = s.evaluate(term, {"a": assemblage})
    return [float(v) for v in out]


# ---------------------------------------------------------------------------
# KEYSTONE: native NetForward == Python forward(), byte-for-byte.
# ---------------------------------------------------------------------------

def test_netforward_matches_python_forward_square():
    s = _fresh_substrate()
    cortex, assemblage = _build_square_net(s)

    xs = (0.0, 0.1, 0.2, 0.3, 0.5, 0.7, 0.9,
          -0.1, -0.3, -0.5, -0.7, -0.9,
          -0.95, -0.55, -0.05, 0.05, 0.55, 0.95)
    for x in xs:
        py = cortex.forward(assemblage, [x])
        nat = _native_forward(s, assemblage, [x])
        assert len(py) == len(nat), f"len mismatch at x={x}: {py} vs {nat}"
        for a, b in zip(py, nat):
            assert abs(a - b) < 1e-12, (
                f"NetForward({x})={nat} != forward()={py} (native parity)")


def test_netforward_computes_square_within_tolerance():
    """Independent of parity: the native forward actually computes x²
    (exact at breakpoints, ≤0.25% elsewhere) — proves it isn't just
    echoing the Python bug-for-bug on a degenerate net."""
    s = _fresh_substrate()
    _, assemblage = _build_square_net(s)
    for x in (0.0, 0.1, 0.2, 0.3, 0.5, 0.7, 0.9):
        out = _native_forward(s, assemblage, [x])
        assert abs(out[0] - x * x) < 1e-9, f"native square({x})={out[0]}"
    # PWL secant overshoots x² by at most 1/(4N²)=0.0025 at each segment
    # midpoint (x=-0.95 is exactly one) — bound matches test_gadgets.
    for x in (-0.95, -0.55, 0.05, 0.55, 0.95):
        out = _native_forward(s, assemblage, [x])
        assert abs(out[0] - x * x) <= 0.0026, f"native square({x})={out[0]}"


def _nid(x):
    return x.value if hasattr(x, "value") else int(x)


def test_direct_net_forward_serve_matches_term_path():
    """The FAST serve path: substrate.net_forward(nid, [x]) is a direct
    native forward that skips the evaluate() term-parse. It returns
    byte-identical results to the NetForward Term path (and to Python
    forward) — same core, no marshalling. This is the hot-loop serve
    method a world adapter uses; rules still compose the Term."""
    s = _fresh_substrate()
    cortex, asm = _build_square_net(s)
    for x in (0.0, 0.3, -0.7, 0.95, -0.95):
        direct = s.net_forward(_nid(asm), [float(x)])
        term = _native_forward(s, asm, [x])
        py = cortex.forward(asm, [x])
        assert direct == pytest.approx(term), f"direct != term at {x}"
        assert direct == pytest.approx(py), f"direct != python at {x}"

    # graceful on a non-net node (identity pass-through, no panic).
    lone = s.add_node("Concept", {"name": "x"})
    assert s.net_forward(_nid(lone), [1.0, 2.0]) == [1.0, 2.0]


def test_batch_net_forward_is_ordered_scalar_semantics():
    """One graph weight load and FFI crossing, with no semantic shortcut."""
    s = _fresh_substrate()
    cortex, asm = _build_square_net(s)
    nid = _nid(asm)
    rows = [[x] for x in (0.0, 0.3, -0.7, 0.95, -0.95)]

    batch = s.net_forward_batch(nid, rows)
    scalar = [s.net_forward(nid, row) for row in rows]
    term = [_native_forward(s, asm, row) for row in rows]
    python = [cortex.forward(asm, row) for row in rows]

    assert batch == scalar
    for got, term_row, python_row in zip(batch, term, python):
        assert got == pytest.approx(term_row)
        assert got == pytest.approx(python_row)


def _untrained_net(s, hidden=120, seed=1):
    """Fixed random ReLU features + a ZERO readout — predicts 0 until it
    trains itself."""
    import numpy as np
    rng = np.random.default_rng(seed)
    asm = s.add_node("NetworkAssemblage", {"input_dim": 1, "output_dim": 1})
    sid = s.add_node("AssemblageStep", {"order": 0, "dim_behavior": "transform"})
    s.add_edge(asm, "has_step", sid, {})
    w = {"W1": (rng.standard_normal((hidden, 1)) * 2.0).tolist(),
         "b1": (rng.standard_normal(hidden)).tolist(),
         "W2": [[0.0] * hidden], "b2": [0.0]}
    for role, dat in w.items():
        wt = s.add_node("WeightTensor", {"role": role, "data": dat})
        s.add_edge(sid, "has_weight", wt, {})
    return asm


def test_reflex_net_self_trains_from_surprise():
    """THE CORRECTION: a reflex net trains ITSELF via collapse and surprise,
    not an external optimizer. net_collapse_step: predict -> surprise
    (target-prediction) -> collapse the readout toward reducing it. From a
    ZERO readout, feeding only (x, x^2) observations drives surprise down
    and predictions to the target — no fit, no gradient lib, no batch solve."""
    s = _fresh_substrate()
    asm = _untrained_net(s)
    nid = _nid(asm)
    tgt = lambda x: x * x
    xs = [i / 20.0 for i in range(-20, 21)]
    test = [-0.85, -0.4, 0.1, 0.55, 0.9]

    # Starts predicting ~0 (maximally surprised).
    assert abs(s.net_forward(nid, [0.5])[0]) < 1e-9, "zero readout predicts 0"

    err0 = max(abs(s.net_forward(nid, [x])[0] - tgt(x)) for x in test)
    first_surprise = s.net_collapse_step(nid, [0.9], [tgt(0.9)], 0.5)
    assert first_surprise > 0, "a wrong prediction is surprised"

    # Self-train: surprise-driven collapse over observations (annealed).
    for epoch in range(150):
        eta = 0.5 / (1.0 + 0.03 * epoch)
        for x in xs:
            s.net_collapse_step(nid, [x], [tgt(x)], eta)

    err1 = max(abs(s.net_forward(nid, [x])[0] - tgt(x)) for x in test)
    assert err1 < 0.08, f"self-trained net should be accurate, got {err1}"
    assert err1 < err0, "training reduced error"

    # A single collapse step reduces THIS point's surprise (local descent).
    s2 = _fresh_substrate()
    a2 = _nid(_untrained_net(s2, seed=3))
    before = s2.net_collapse_step(a2, [0.7], [0.49], 0.5)
    after = s2.net_collapse_step(a2, [0.7], [0.49], 0.5)
    assert after < before, "one collapse step reduces surprise on the same point"


def test_ordered_batch_collapse_is_sequentially_equivalent():
    """Batch collapse is online order, not a simultaneous gradient sum."""
    scalar = _fresh_substrate()
    batch = _fresh_substrate()
    scalar_nid = _nid(_untrained_net(scalar, hidden=24, seed=91))
    batch_nid = _nid(_untrained_net(batch, hidden=24, seed=91))
    rows = [[x] for x in (-0.8, -0.25, 0.1, 0.55, 0.9)]
    targets = [[row[0] * row[0]] for row in rows]
    eta = 0.4

    scalar_surprise = [
        scalar.net_collapse_step(scalar_nid, row, target, eta)
        for row, target in zip(rows, targets)
    ]
    batch_surprise = batch.net_collapse_batch_ordered(
        batch_nid, rows, targets, eta)

    assert batch_surprise == scalar_surprise
    probes = [[x] for x in (-0.7, 0.0, 0.4, 0.95)]
    assert batch.net_forward_batch(batch_nid, probes) == [
        scalar.net_forward(scalar_nid, row) for row in probes
    ]
    with pytest.raises(ValueError, match="input rows"):
        batch.net_collapse_batch_ordered(
            batch_nid, rows, targets[:-1], eta)


def test_self_train_multiclass_classification():
    """The mechanism behind the real-reader-task demo: a self-training net
    learns a MULTI-CLASS decision (one-hot targets, argmax read-off) by
    surprise-driven collapse. Here a 3-class rule over feature vectors —
    the same shape as reproducing the reader's (kind, focus) verdict."""
    import numpy as np
    rng = np.random.default_rng(0)
    # 3 classes, each a distinct feature signature + noise.
    protos = [np.array([1., 0., 0., 1.]), np.array([0., 1., 0., 1.]),
              np.array([0., 0., 1., 0.])]
    def sample():
        c = int(rng.integers(3))
        return (protos[c] + rng.normal(0, 0.15, 4)).tolist(), c
    data = [sample() for _ in range(90)]
    train, test = data[:70], data[70:]

    s = _fresh_substrate()
    hidden = 80
    asm = s.add_node("NetworkAssemblage", {"input_dim": 4, "output_dim": 3})
    sid = s.add_node("AssemblageStep", {"order": 0, "dim_behavior": "transform"})
    s.add_edge(asm, "has_step", sid, {})
    w = {"W1": (rng.standard_normal((hidden, 4)) * 1.2).tolist(),
         "b1": (rng.standard_normal(hidden) * 0.3).tolist(),
         "W2": [[0.0] * hidden for _ in range(3)], "b2": [0.0, 0.0, 0.0]}
    for role, dat in w.items():
        wt = s.add_node("WeightTensor", {"role": role, "data": dat})
        s.add_edge(sid, "has_weight", wt, {})
    nid = _nid(asm)

    def onehot(c):
        y = [0.0, 0.0, 0.0]; y[c] = 1.0; return y
    def acc(rows):
        return sum(int(np.argmax(s.net_forward(nid, f)) == c) for f, c in rows) / len(rows)

    acc0 = acc(test)
    for epoch in range(120):
        eta = 0.5 / (1.0 + 0.03 * epoch)
        for f, c in train:
            s.net_collapse_step(nid, f, onehot(c), eta)
    acc1 = acc(test)
    assert acc1 >= 0.85, f"self-trained multiclass held-out acc {acc1}"
    assert acc1 > acc0, "training improved held-out accuracy"


def test_self_training_runs_inside_the_engine():
    """WIRED IN AT THE ENGINE LEVEL: the surprise-driven collapse fires
    INSIDE run_rules via the net_collapse effect — the adapter only ingests
    ReflexObservation nodes and ticks; Python never calls net_collapse_step.
    A self_training net wrapping a zero-readout assemblage trains itself as
    the graph collapses, and the engine records the rolling surprise on the
    net (the signal reflex_self_train_converged reads)."""
    s = _fresh_substrate()
    asm = _untrained_net(s)
    nid = _nid(asm)
    _install(s, _seed_rules()["reflex_net_self_train_step"])
    tgt = lambda x: x * x
    xs = [i / 20.0 for i in range(-20, 21)]
    test = [-0.8, -0.3, 0.4, 0.9]

    rn = s.add_node("ReflexNet", {"name": "sq", "status": "self_training",
                                  "enabled": 0.0, "eta": 0.5})
    s.add_edge(rn, "net_assemblage", asm, {})
    # Ingest observations as graph nodes — mechanical, like any ingest.
    obs = []
    for x in xs:
        o = s.add_node("ReflexObservation",
                       {"status": "pending", "input_vec": [x], "target": [tgt(x)]})
        s.add_edge(o, "observes", rn, {})
        obs.append(o)

    err0 = max(abs(s.net_forward(nid, [x])[0] - tgt(x)) for x in test)
    # Each run_rules() = one epoch: every pending observation fires ONE
    # collapse inside the engine, then marks itself consumed. Python does
    # NOT call net_collapse_step — the engine's run_rules does.
    for epoch in range(150):
        s.set_attr(rn, "eta", 0.5 / (1.0 + 0.03 * epoch))
        for o in obs:
            s.set_attr(o, "status", "pending")
        s.run_rules()
    err1 = max(abs(s.net_forward(nid, [x])[0] - tgt(x)) for x in test)

    assert err1 < 0.08, f"engine-trained net err {err1}"
    assert err1 < err0, "training reduced error"
    # The engine recorded the (EMA) surprise on the net — the convergence signal.
    assert s.node(rn)["attrs"]["surprise"] < 0.05, "engine recorded falling surprise"
    # Observations were consumed (fired once each) by the engine.
    assert all(s.node(o)["attrs"]["status"] == "consumed" for o in obs)


def test_self_train_convergence_is_a_graph_decision():
    """The STOP decision is graph-native: a self-training net whose recorded
    surprise falls below its converge_tol knob is marked 'trained' by the
    rule (ready for the judge). The per-observation collapse is the
    mechanical op; deciding it has converged is a rule."""
    s = _fresh_substrate()
    _, asm = _build_square_net(s)
    _install(s, _seed_rules()["reflex_self_train_converged"])
    rn = _mk_reflex_net(s, asm, enabled=0.0, basin_threshold=0.5)
    s.set_attr(rn, "status", "self_training")
    s.set_attr(rn, "converge_tol", 0.01)

    # Still surprised -> stays self_training.
    s.set_attr(rn, "surprise", 0.05)
    s.run_rules()
    assert s.node(rn)["attrs"]["status"] == "self_training"

    # Surprise fell below tol -> the rule marks it trained.
    s.set_attr(rn, "surprise", 0.004)
    s.run_rules()
    assert s.node(rn)["attrs"]["status"] == "trained", "converged -> trained"


def test_netforward_missing_net_is_graceful():
    """A NetForward over a node that is not an assemblage returns the
    input passed through (identity) — never a panic. This is the
    out-of-basin safety floor at the Term level."""
    s = _fresh_substrate()
    lone = s.add_node("Concept", {"name": "not_a_net"})
    term = {
        "type": "NetForward",
        "assemblage": {"type": "Var", "name": "a"},
        "inputs": {"type": "Lit", "value": [1.0, 2.0, 3.0]},
    }
    out = [float(v) for v in s.evaluate(term, {"a": lone})]
    assert out == [1.0, 2.0, 3.0]


# ---------------------------------------------------------------------------
# The reflex-net layer as graph data: a basin-gated fast-path Rule, an
# `enabled` knob (optional), a `basin_threshold` knob (tweakable), and the
# faster-AND-regression-free judge — all shipped in seeds/reflex_net.json.
# ---------------------------------------------------------------------------

import json
import os

_SEED = os.path.join(os.path.dirname(__file__), "..", "seeds", "reflex_net.json")


def _seed_rules():
    with open(_SEED) as f:
        return {r["name"]: r for r in json.load(f)["rules"]}


def _install(s, rule):
    """Install a seed rule via the same add_rule seam the adopt spine uses.
    Returns the rule index (for remove_rule / ablation)."""
    return s.add_rule(rule)


def _mk_reflex_net(s, assemblage, *, enabled, basin_threshold):
    rn = s.add_node("ReflexNet", {
        "name": "square_reflex", "enabled": float(enabled),
        "basin_threshold": float(basin_threshold),
    })
    s.add_edge(rn, "net_assemblage", assemblage, {})
    # The two knobs, discoverable via has_tunable (zero-code tweakable).
    for attr, lo, hi, step in (("enabled", 0.0, 1.0, 1.0),
                               ("basin_threshold", 0.0, 10.0, 0.05)):
        tp = s.add_node("TunableParameter", {
            "attr_name": attr, "min": lo, "max": hi, "step": step,
            "description": f"reflex-net {attr}",
        })
        s.add_edge(rn, "has_tunable", tp, {})
    return rn


def _mk_query(s, rn, input_vec, residual):
    q = s.add_node("ReflexQuery", {
        "status": "pending", "residual": float(residual),
        "input_vec": [float(v) for v in input_vec],
    })
    s.add_edge(q, "for_net", rn, {})
    return q


def _status(s, q):
    return s.node(q)["attrs"].get("status")


def test_reflex_net_off_by_default_is_optional():
    """enabled=0 (default) => the fast path never fires; the query stays
    pending and falls through to cognition. The layer is optional."""
    s = _fresh_substrate()
    _, asm = _build_square_net(s)
    _install(s, _seed_rules()["reflex_net_serve"])

    rn = _mk_reflex_net(s, asm, enabled=0.0, basin_threshold=1.0)
    q = _mk_query(s, rn, [0.3], residual=0.0)
    s.run_rules()
    assert _status(s, q) == "pending", "disabled reflex net must not serve"
    assert "answer" not in s.node(q)["attrs"]


def test_reflex_net_serves_natively_within_basin():
    """enabled=1 AND residual<basin_threshold => the fast path fires and
    writes the native NetForward answer (≈x²). No Python decided this —
    run_rules did."""
    s = _fresh_substrate()
    cortex, asm = _build_square_net(s)
    _install(s, _seed_rules()["reflex_net_serve"])

    rn = _mk_reflex_net(s, asm, enabled=1.0, basin_threshold=0.5)
    q = _mk_query(s, rn, [0.3], residual=0.1)
    s.run_rules()

    assert _status(s, q) == "served"
    assert s.node(q)["attrs"].get("served_by") == "reflex_net"
    answer = [float(v) for v in s.node(q)["attrs"]["answer"]]
    # matches both the net's own forward AND x².
    assert abs(answer[0] - 0.09) < 0.0026
    assert answer == pytest.approx(cortex.forward(asm, [0.3]))


def test_reflex_net_defers_outside_basin_gate_is_external():
    """residual >= basin_threshold => the fast path DEFERS even though the
    net is enabled — the basin gate is external to the net (a grounded
    residual the rule reads), not the net's own confidence."""
    s = _fresh_substrate()
    _, asm = _build_square_net(s)
    _install(s, _seed_rules()["reflex_net_serve"])

    rn = _mk_reflex_net(s, asm, enabled=1.0, basin_threshold=0.5)
    q = _mk_query(s, rn, [0.3], residual=0.9)  # out of basin
    s.run_rules()
    assert _status(s, q) == "pending", "out-of-basin query must defer"


def test_basin_threshold_is_tweakable_zero_code():
    """Widening basin_threshold (one attr edit, zero code) makes a
    previously out-of-basin query serve. The knob is graph data."""
    s = _fresh_substrate()
    _, asm = _build_square_net(s)
    _install(s, _seed_rules()["reflex_net_serve"])

    rn = _mk_reflex_net(s, asm, enabled=1.0, basin_threshold=0.5)
    q = _mk_query(s, rn, [0.3], residual=0.9)
    s.run_rules()
    assert _status(s, q) == "pending"

    # Widen the basin — pure node edit, no code change.
    s.set_attr(rn, "basin_threshold", 1.0)
    s.run_rules()
    assert _status(s, q) == "served", "widened basin must now serve"


def test_reflex_judge_supported_iff_faster_and_regression_free():
    """The judge combinator: supported iff regression<tolerance AND
    reflex faster. Two measured trials, opposite verdicts."""
    s = _fresh_substrate()
    _install(s, _seed_rules()["reflex_trial_judge"])
    _install(s, _seed_rules()["reflex_trial_refuted"])
    ag = s.add_node("Agent", {"name": "self"})

    # regression-free AND faster -> supported
    good = s.add_node("ReflexTrial", {
        "status": "measured", "regression": 0.001, "tolerance": 0.01,
        "reflex_ms": 1.0, "slow_ms": 5.0,
    })
    # regresses -> refuted (even though faster)
    bad = s.add_node("ReflexTrial", {
        "status": "measured", "regression": 0.5, "tolerance": 0.01,
        "reflex_ms": 1.0, "slow_ms": 5.0,
    })
    # regression-free but SLOWER -> refuted
    slow = s.add_node("ReflexTrial", {
        "status": "measured", "regression": 0.001, "tolerance": 0.01,
        "reflex_ms": 9.0, "slow_ms": 5.0,
    })
    for t in (good, bad, slow):
        s.add_edge(ag, "judges", t, {})
    s.run_rules()

    assert s.node(good)["attrs"]["verdict"] == "supported"
    assert s.node(good)["attrs"]["adopt_ready"] == 1.0
    assert s.node(bad)["attrs"]["verdict"] == "refuted"
    assert s.node(slow)["attrs"]["verdict"] == "refuted"


def test_reflex_fast_path_adopts_and_ablates_via_existing_rule_spine():
    """The fast path IS a Rule, so remove_rule ablates it and add_rule
    re-adopts it — the existing rule machinery covers reflex nets with no
    new executor. Ablated => an in-basin, enabled query no longer serves."""
    s = _fresh_substrate()
    _, asm = _build_square_net(s)
    idx = _install(s, _seed_rules()["reflex_net_serve"])

    rn = _mk_reflex_net(s, asm, enabled=1.0, basin_threshold=0.5)
    q1 = _mk_query(s, rn, [0.3], residual=0.1)
    s.run_rules()
    assert _status(s, q1) == "served", "sanity: fires while installed"

    # Ablate the fast path (tombstone via the standard rule primitive).
    s.remove_rule(idx)
    q2 = _mk_query(s, rn, [0.3], residual=0.1)
    s.run_rules()
    assert _status(s, q2) == "pending", "ablated fast path must not serve"

    # Re-adopt it — same seam perform_adoptions uses.
    s.add_rule(_seed_rules()["reflex_net_serve"])
    q3 = _mk_query(s, rn, [0.3], residual=0.1)
    s.run_rules()
    assert _status(s, q3) == "served", "re-adopted fast path serves again"


def test_mint_builder_produces_a_working_reflex_net():
    """The mechanical builder domains/reflex_net.py mints a reflex net
    OFF by default; flipping `enabled` (the adopt decision) makes the
    generic serve rule fire — no per-net rule authoring."""
    from domains.reflex_net import mint_reflex_net, mint_reflex_query

    s = _fresh_substrate()
    cortex, asm = _build_square_net(s)
    _install(s, _seed_rules()["reflex_net_serve"])

    rn = mint_reflex_net(s, asm, name="square", basin_threshold=0.5)
    assert s.node(rn)["attrs"]["enabled"] == 0.0, "minted OFF (optional)"
    # idempotent
    assert mint_reflex_net(s, asm, name="square", basin_threshold=0.5) == rn

    q = mint_reflex_query(s, rn, [0.3], residual=0.1)
    s.run_rules()
    assert _status(s, q) == "pending", "off by default: no serve"

    # Adopt = flip the enabled knob (zero code), then it serves natively.
    s.set_attr(rn, "enabled", 1.0)
    q2 = mint_reflex_query(s, rn, [0.3], residual=0.1)
    s.run_rules()
    assert _status(s, q2) == "served"
    ans = [float(v) for v in s.node(q2)["attrs"]["answer"]]
    assert ans == pytest.approx(cortex.forward(asm, [0.3]))


def test_agent_auto_proposes_reflex_net_for_hot_op_with_a_net():
    """THE MINT, graph-native: run_rules proposes a reflex net (OFF) for a
    hot op that already has a constructed net — once, dedup-guarded. The
    agent proposes its own reflex nets; no Python decided it."""
    s = _fresh_substrate()
    cortex, asm = _build_square_net(s)   # builds target -has_assemblage-> asm
    _install_policy(s)
    _install(s, _seed_rules()["auto_propose_reflex_net"])
    _install(s, _seed_rules()["reflex_net_serve"])

    assert len(s.nodes("ReflexNet")) == 0
    s.run_rules()

    nets = s.nodes("ReflexNet")
    assert len(nets) == 1, "hot op with a net -> exactly one proposal"
    rn = nets[0]
    a = s.node(rn)["attrs"]
    assert a["status"] == "proposed" and a["enabled"] == 0.0, "proposed OFF"
    # wired to the assemblage + its two knobs.
    assert asm in s.neighbours(rn, "net_assemblage")
    knob_attrs = {s.node(tp)["attrs"]["attr_name"]
                  for tp in s.neighbours(rn, "has_tunable")}
    assert knob_attrs == {"enabled", "basin_threshold"}

    # Dedup: running again mints no second proposal.
    s.run_rules()
    assert len(s.nodes("ReflexNet")) == 1, "once-guarded"

    # The proposal is inert until adopted: a query defers while OFF...
    q = _mk_query(s, rn, [0.3], residual=0.0)
    s.run_rules()
    assert _status(s, q) == "pending"
    # ...and serves once the adopt decision flips enabled (proposal -> adopt).
    s.set_attr(rn, "enabled", 1.0)
    q2 = _mk_query(s, rn, [0.3], residual=0.0)
    s.run_rules()
    assert _status(s, q2) == "served"
    assert [float(v) for v in s.node(q2)["attrs"]["answer"]] == pytest.approx(
        cortex.forward(asm, [0.3]))


def test_cold_op_gets_no_reflex_proposal():
    """The propose rule is hot-gated: an op below the hot floor gets no
    reflex net (don't cache what isn't worth caching)."""
    s = _fresh_substrate()
    cortex = CodeWritingCortex(s, agent=_A()).install()
    from substrate.boot_all import load_one_seed
    _seed_parents(s)
    load_one_seed(s, "gadgets")
    # A COLD target (baseline_mean_ms below the 0.05 floor) with a net.
    target = s.add_node("ReplacementTarget", {
        "op_name": "compute_square", "baseline_total_ms": 1.0,
        "baseline_count": 1000, "baseline_mean_ms": 0.001, "selected_at": 0.0,
    })
    root = cortex._ensure_root()
    s.add_edge(root, "current_target", target, {})
    top = next(n for n in s.nodes("DesignPattern")
               if s.node(n)["attrs"].get("name") == "square_pwl_signed_gadget")
    s.add_edge(target, "uses_pattern", top, {})
    asm = cortex.assemble_network(target)
    cortex.construct_weights(asm)

    _install_policy(s)
    _install(s, _seed_rules()["auto_propose_reflex_net"])
    s.run_rules()
    assert len(s.nodes("ReflexNet")) == 0, "cold op must not be proposed"


def test_propose_thresholds_are_tweakable_via_policy():
    """The propose-trigger thresholds live on the ReflexNetPolicy singleton.
    Raising hot_ms_threshold above the op's cost suppresses the proposal;
    the minted net's basin_threshold comes from the policy too — both
    tweakable, zero code."""
    s = _fresh_substrate()
    _, asm = _build_square_net(s)  # target baseline_mean_ms = 0.1
    pol = _install_policy(s, hot_ms_threshold=0.5, default_basin_threshold=0.4)
    _install(s, _seed_rules()["auto_propose_reflex_net"])

    # 0.1 < hot_ms_threshold 0.5 -> not hot -> no proposal.
    s.run_rules()
    assert len(s.nodes("ReflexNet")) == 0, "raised threshold suppresses propose"

    # Lower the threshold (zero-code edit) -> now hot -> proposed, and the
    # minted net inherits the policy's default_basin_threshold.
    s.set_attr(pol, "hot_ms_threshold", 0.05)
    s.run_rules()
    nets = s.nodes("ReflexNet")
    assert len(nets) == 1, "lowered threshold now proposes"
    assert s.node(nets[0])["attrs"]["basin_threshold"] == 0.4, \
        "minted net inherits policy default_basin_threshold"


def test_explicit_request_proposes_even_a_cold_op():
    """The NL/host-instruction path: an explicit cache_requested=1 proposes
    a reflex net even for a COLD op (an explicit 'cache this' overrides the
    hot heuristic). The flag is what a world adapter sets when it
    understands a 'cache this op' instruction — the DECISION stays in the
    rule."""
    s = _fresh_substrate()
    cortex = CodeWritingCortex(s, agent=_A()).install()
    from substrate.boot_all import load_one_seed
    _seed_parents(s)
    load_one_seed(s, "gadgets")
    target = s.add_node("ReplacementTarget", {
        "op_name": "compute_square", "baseline_total_ms": 1.0,
        "baseline_count": 1000, "baseline_mean_ms": 0.001,  # COLD
        "selected_at": 0.0, "cache_requested": 1.0,          # but requested
    })
    root = cortex._ensure_root()
    s.add_edge(root, "current_target", target, {})
    top = next(n for n in s.nodes("DesignPattern")
               if s.node(n)["attrs"].get("name") == "square_pwl_signed_gadget")
    s.add_edge(target, "uses_pattern", top, {})
    asm = cortex.assemble_network(target)
    cortex.construct_weights(asm)

    _install_policy(s)
    _install(s, _seed_rules()["auto_propose_reflex_net"])
    s.run_rules()
    assert len(s.nodes("ReflexNet")) == 1, "explicit request proposes a cold op"


def _seed_basin_codebook(s):
    """A tiny ShapeSignature quantum codebook = the reflex net's basin."""
    s.add_node("ShapeSignature", {"name": "p_move", "kind": "authored",
               "signature": json.dumps([["move", "X", "by", "D"]])})
    s.add_node("ShapeSignature", {"name": "p_stop", "kind": "authored",
               "signature": json.dumps([["stop", "X"]])})


def test_basin_residual_is_grounded_by_shapedecode_not_caller_supplied():
    """THE NEXT SLICE: the query's basin residual is COMPUTED by the graph
    from the sd-loop decode against the held quantum codebook — a raw query
    is grounded (residual = count of uncovered relations) before the serve
    gate reads it. In-basin (fully covered) => residual 0 => serves;
    novel input => residual > 0 => defers. The gate is grounded."""
    s = _fresh_substrate()
    cortex, asm = _build_square_net(s)
    _seed_basin_codebook(s)
    _install(s, _seed_rules()["reflex_ground_residual"])
    _install(s, _seed_rules()["reflex_net_serve"])

    # basin_threshold 1.0 => serve iff grounded residual < 1 (i.e. == 0).
    rn = _mk_reflex_net(s, asm, enabled=1.0, basin_threshold=1.0)

    # In-basin: every relation is covered by the codebook.
    q_in = s.add_node("ReflexQuery", {
        "status": "raw", "input_vec": [0.3],
        "signature": [["move", "X", "by", "D"], ["stop", "X"]],
    })
    s.add_edge(q_in, "for_net", rn, {})
    # Out-of-basin: one novel relation the codebook does not hold.
    q_out = s.add_node("ReflexQuery", {
        "status": "raw", "input_vec": [0.3],
        "signature": [["move", "X", "by", "D"], ["zzznew", "X"]],
    })
    s.add_edge(q_out, "for_net", rn, {})

    s.run_rules()

    # The residuals were COMPUTED (grounded), not supplied.
    assert s.node(q_in)["attrs"]["grounded_residual"] == 1.0
    assert s.node(q_in)["attrs"]["residual"] == 0, "in-basin decodes clean"
    assert s.node(q_out)["attrs"]["residual"] == 1, "one novel relation"

    # ...and the GROUNDED residual gates serve vs defer.
    assert _status(s, q_in) == "served", "in-basin serves on grounded residual"
    assert [float(v) for v in s.node(q_in)["attrs"]["answer"]] == pytest.approx(
        cortex.forward(asm, [0.3]))
    assert _status(s, q_out) == "pending", "novel input defers to cognition"


def test_agent_records_its_codebook_scope_extension_proposal():
    """'The jabberwock builds the Rust affordance' — faithfully: the agent
    AUTHORS a RustExtensionSpec naming the residual its DSL could not
    express (per-net basin scoping), and an ExtensionProposal recording the
    honest install boundary (an engine change in shape_decode.rs, OUTSIDE
    rung-4's ALLOWED_INSTALL_FILES, so human-authored under directive and
    gated — the join-index precedent). The DECISION is the agent's graph
    data; the build is the gated host step."""
    from domains.reflex_net_extension import agent_propose_codebook_scope

    s = _fresh_substrate()
    spec_id, prop_id = agent_propose_codebook_scope(s, installed=True)

    spec = s.node(spec_id)["attrs"]
    assert spec["name"] == "shapedecode_codebook_scope"
    assert spec["compiled"] is True
    assert "per-net" in spec["motivating_residual"].lower()
    assert "codebook" in spec["why_new"].lower()

    prop = s.node(prop_id)["attrs"]
    assert prop["installed"] is True
    assert prop["live_tree_untouched"] is False  # the affordance IS live now
    assert "outside_rung4" in prop["install_surface"]
    # linked spec<-proposal
    assert spec_id in s.neighbours(prop_id, "validates")

    # idempotent on the spec name
    spec_id2, _ = agent_propose_codebook_scope(s, installed=True)
    assert spec_id2 == spec_id
    assert len(s.nodes("RustExtensionSpec")) == 1


def test_per_net_basins_via_codebook_scope():
    """The agent-proposed, human-built ShapeDecode `codebook_scope`
    affordance: two reflex nets over the SAME shared ShapeSignature
    codebook hold DIFFERENT basins (each scoped to its own basin_parts).
    The same input is in-basin for the net that holds its relation and
    out-of-basin for the net that does not."""
    s = _fresh_substrate()
    cortex, asm = _build_square_net(s)
    # Shared codebook: two quanta.
    s.add_node("ShapeSignature", {"name": "p_move", "kind": "authored",
               "signature": json.dumps([["move", "X", "by", "D"]])})
    s.add_node("ShapeSignature", {"name": "p_stop", "kind": "authored",
               "signature": json.dumps([["stop", "X"]])})
    _install(s, _seed_rules()["reflex_ground_residual"])
    _install(s, _seed_rules()["reflex_net_serve"])

    # Net A's basin = {p_move}; Net B's basin = {p_stop}.
    rn_a = _mk_reflex_net(s, asm, enabled=1.0, basin_threshold=1.0)
    s.set_attr(rn_a, "basin_parts", ["p_move"])
    rn_b = _mk_reflex_net(s, asm, enabled=1.0, basin_threshold=1.0)
    s.set_attr(rn_b, "basin_parts", ["p_stop"])

    # The SAME input signature: a single 'move' relation.
    def _q(rn):
        q = s.add_node("ReflexQuery", {
            "status": "raw", "input_vec": [0.3],
            "signature": [["move", "X", "by", "D"]],
        })
        s.add_edge(q, "for_net", rn, {})
        return q
    qa, qb = _q(rn_a), _q(rn_b)
    s.run_rules()

    # Net A holds 'move' -> residual 0 -> serves. Net B does not -> residual 1 -> defers.
    assert s.node(qa)["attrs"]["residual"] == 0, "in Net A's basin"
    assert s.node(qb)["attrs"]["residual"] == 1, "outside Net B's basin"
    assert _status(s, qa) == "served"
    assert _status(s, qb) == "pending"


def test_numeric_basin_residual_is_grounded_by_fit_range():
    """THE NUMERIC GRADE: a float net's basin is its fit range [fit_lo,
    fit_hi]; the grounded residual is distance-outside-range (0 inside,
    growing with extrapolation) — the numeric twin of the symbolic
    ShapeDecode residual. In-range serves; extrapolated defers."""
    s = _fresh_substrate()
    cortex, asm = _build_square_net(s)   # square_pwl fit over [-1, 1]
    _install(s, _seed_rules()["reflex_ground_numeric_residual"])
    _install(s, _seed_rules()["reflex_net_serve"])

    rn = _mk_reflex_net(s, asm, enabled=1.0, basin_threshold=0.5)
    s.set_attr(rn, "fit_lo", -1.0)
    s.set_attr(rn, "fit_hi", 1.0)

    # In fit range -> residual 0 -> serves the native answer.
    q_in = s.add_node("ReflexQuery", {"status": "raw_numeric", "input_vec": [0.3]})
    s.add_edge(q_in, "for_net", rn, {})
    # Far outside the fit range -> residual = 5 - 1 = 4 -> defers.
    q_out = s.add_node("ReflexQuery", {"status": "raw_numeric", "input_vec": [5.0]})
    s.add_edge(q_out, "for_net", rn, {})

    s.run_rules()

    assert s.node(q_in)["attrs"]["residual"] == 0.0, "in fit range decodes clean"
    assert s.node(q_out)["attrs"]["residual"] == pytest.approx(4.0), "extrapolation distance"
    assert _status(s, q_in) == "served", "in-basin numeric serves"
    assert [float(v) for v in s.node(q_in)["attrs"]["answer"]] == pytest.approx(
        cortex.forward(asm, [0.3]))
    assert _status(s, q_out) == "pending", "extrapolated input defers to cognition"


def test_approximate_grade_adopted_only_within_tolerance():
    """THE TRAINED/APPROXIMATE GRADE, at the decision level. A net whose
    answer is APPROXIMATE (here the square_pwl's real ≤0.0025 PWL error at
    a segment midpoint) is a fuzzy cache: the regression-free-AND-faster
    judge adopts it only when its error is within tolerance. Same
    machinery a gradient-trained head would reuse — the residual gate +
    this judge are exactly what make a fuzzy cache safe. (Training the
    weights is offline torch; the SAFETY decision is here and graph-native.)"""
    s = _fresh_substrate()
    cortex, asm = _build_square_net(s)
    _install(s, _seed_rules()["reflex_trial_judge"])
    _install(s, _seed_rules()["reflex_trial_refuted"])
    ag = s.add_node("Agent", {"name": "self"})

    x = -0.95  # segment midpoint: worst-case PWL error ~0.0025
    approx = _native_forward(s, asm, [x])[0]     # the reflex (approximate) answer
    exact = x * x                                 # the slow/exact answer
    regression = abs(approx - exact)              # adapter measures it (I/O)
    assert regression == pytest.approx(0.0025, abs=1e-4), "real PWL error"

    def _trial(tol):
        t = s.add_node("ReflexTrial", {
            "status": "measured", "regression": regression, "tolerance": tol,
            "reflex_ms": 1.0, "slow_ms": 5.0,
        })
        s.add_edge(ag, "judges", t, {})
        return t

    lenient = _trial(0.003)   # tolerance above the error -> regression-free enough
    strict = _trial(0.001)    # tolerance below the error -> regresses
    s.run_rules()

    assert s.node(lenient)["attrs"]["verdict"] == "supported", \
        "approximate net within tolerance + faster -> adopt"
    assert s.node(strict)["attrs"]["verdict"] == "refuted", \
        "same net, tighter tolerance -> its approximation is a regression"


class _Ag:
    """Minimal agent shim: training_dispatch reads agent.s + agent.inner;
    over a raw open substrate both point at it."""
    def __init__(self, s):
        self.s = s
        self.inner = s


def test_agent_decides_to_train_on_a_refuted_trial():
    """THE DECISION TO TRAIN, graph-native. A refuted ReflexTrial linked to
    its net -> run_rules mints a TrainingJob (trace_pending), once. The
    agent deciding to improve itself by training — a rule, not Python."""
    s = _fresh_substrate()
    _, asm = _build_square_net(s)
    _install(s, _seed_rules()["reflex_request_training"])
    ag = s.add_node("Agent", {"name": "self"})
    rn = _mk_reflex_net(s, asm, enabled=0.0, basin_threshold=0.5)

    trial = s.add_node("ReflexTrial", {"verdict": "refuted", "status": "judged"})
    s.add_edge(ag, "judges", trial, {})
    s.add_edge(trial, "for_reflex", rn, {})

    s.run_rules()
    jobs = s.nodes("TrainingJob")
    assert len(jobs) == 1, "refuted trial -> exactly one training job"
    assert s.node(jobs[0])["attrs"]["status"] == "trace_pending"
    assert rn in s.neighbours(jobs[0], "train_for")

    s.run_rules()
    assert len(s.nodes("TrainingJob")) == 1, "once-guarded per trial"


def test_training_runs_as_a_background_process_end_to_end(tmp_path):
    """THE HEADLINE: the agent trains a reflex net as a BACKGROUND process,
    end to end. Mint a job with (x, x^2) traces, dispatch (spawns a DETACHED
    child, non-blocking), poll to completion, ingest the trained weights as
    a NetForward-readable net wrapped by a disabled ReflexNet, then
    measure->judge->adopt via the existing spine. Real subprocess, real fit."""
    import time
    from domains.training_dispatch import (
        mint_training_job, scan_and_train,
    )

    s = _fresh_substrate()
    ag = _Ag(s)
    runs = tmp_path / "train_runs"

    # The (input, verdict) traces active cognition collected for x -> x^2.
    xs = [i / 20.0 for i in range(-20, 21)]           # [-1, 1]
    traces = [(x, x * x) for x in xs]
    job = mint_training_job(ag, name="square", traces=traces,
                            fit_lo=-1.0, fit_hi=1.0, hidden_dim=64, seed=0)
    assert s.node(job)["attrs"]["status"] == "requested"

    # Dispatch: spawns the detached trainer, returns immediately (background).
    scan_and_train(ag, str(runs))
    assert s.node(job)["attrs"]["status"] == "running", "spawned, not blocked"

    # Poll to completion (the agent would keep ticking; here we just wait).
    for _ in range(200):
        scan_and_train(ag, str(runs))
        if s.node(job)["attrs"]["status"] in ("done", "failed"):
            break
        time.sleep(0.05)
    assert s.node(job)["attrs"]["status"] == "done", "background training finished"

    # Ingested: a disabled ReflexNet wrapping a NetForward-readable trained net.
    nets = s.neighbours(job, "trained_net")
    assert len(nets) == 1
    rn = nets[0]
    assert s.node(rn)["attrs"]["enabled"] == 0.0, "trained net minted OFF"
    asm = s.neighbours(rn, "net_assemblage")[0]

    # The trained net actually approximates x^2 (real fit, low error).
    cortex = CodeWritingCortex(s, agent=_A())          # for forward parity helper
    for x in (-0.8, -0.3, 0.4, 0.9):
        got = _native_forward(s, asm, [x])[0]
        assert abs(got - x * x) < 0.02, f"trained net({x})={got}"

    # measure -> judge -> adopt via the EXISTING spine.
    _install(s, _seed_rules()["reflex_net_serve"])
    _install(s, _seed_rules()["reflex_trial_judge"])
    _install(s, _seed_rules()["reflex_trial_refuted"])
    regression = max(abs(_native_forward(s, asm, [x])[0] - x * x)
                     for x in (-0.8, -0.3, 0.4, 0.9))
    trial = s.add_node("ReflexTrial", {
        "status": "measured", "regression": regression, "tolerance": 0.05,
        "reflex_ms": 1.0, "slow_ms": 5.0,
    })
    s.add_edge(ag.s.add_node("Agent", {"name": "self"}), "judges", trial, {})
    s.run_rules()
    assert s.node(trial)["attrs"]["verdict"] == "supported", \
        "trained net is regression-free-and-faster -> adopt"

    # Adopt = flip enabled; then it serves natively in its numeric basin.
    s.set_attr(rn, "enabled", 1.0)
    q = s.add_node("ReflexQuery", {"status": "raw_numeric", "input_vec": [0.4]})
    s.add_edge(q, "for_net", rn, {})
    _install(s, _seed_rules()["reflex_ground_numeric_residual"])
    s.run_rules()
    assert _status(s, q) == "served", "adopted trained net serves"
    assert abs(s.node(q)["attrs"]["answer"][0] - 0.16) < 0.02


def test_seed_file_is_valid_and_ships_the_layer():
    """The seed carries the productions + the three rules + the knobs'
    documentation, so a fresh boot has the reflex-net layer available
    (and OFF)."""
    with open(_SEED) as f:
        d = json.load(f)
    assert d["id"] == "reflex_net"
    rule_names = {r["name"] for r in d["rules"]}
    assert {"reflex_net_serve", "reflex_trial_judge", "reflex_trial_refuted",
            "auto_propose_reflex_net"} <= rule_names
    prod_edges = {p["edge_type"] for p in d["productions"]}
    assert {"for_net", "net_assemblage", "has_tunable", "judges"} <= prod_edges
    # ships the tweakable policy singleton
    assert any(n.get("type") == "ReflexNetPolicy" for n in d["nodes"])

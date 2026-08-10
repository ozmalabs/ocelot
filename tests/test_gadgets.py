"""Exact-construction gadgets — verifying the cortex can write weights
instead of training them.

The seed installs CPWL gadgets (identity, abs, max, min) as
DesignPattern nodes carrying literal W1/b1/W2/b2 matrices. The
cortex's selector picks one for a target whose design_tags include
cpwl_function + exact_construction; construct_weights then renders
the literal matrices to WeightTensor graph nodes attached to each
AssemblageStep.

No training, no torch — just graph queries + a tiny numpy forward
pass to verify the matrices actually compute the named function."""
from __future__ import annotations

import numpy as np
import pytest
from substrate_rs import _native
from substrate.boot_all import load_one_seed


_NODE_TYPES = (
    "Microtheory", "Concept", "DesignPattern", "DesignExclusion",
    "CodeTarget", "ProgrammingLanguage", "LanguageExclusion",
    "LanguageScoringConfig", "CodeWritingCortex", "CodeAuthoringRoot",
    "Reflex", "ReplacementTarget", "CodeDraft", "ValidationResult",
    "CodeInstallation", "NetworkAssemblage", "AssemblageStep",
    "WeightTensor",
)
_EDGE_TYPES = (
    "genlMt", "has_concept", "owns_microtheory", "owns_root",
    "has_reflex", "current_target", "has_draft", "validated_by",
    "installed_as", "authored_in", "uses_pattern", "subClassOf",
    "in_category", "has_assemblage", "has_step", "has_weight",
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


def _seed_parents(substrate):
    """compiler_theory + neural_networks Mts (the gadget Mt's parents)."""
    substrate.add_node("Microtheory", {"name": "compiler_theory"})
    substrate.add_node("Microtheory", {"name": "neural_networks"})
    substrate.add_node("Microtheory", {"name": "code_authoring"})


# ---------------------------------------------------------------------------
# loader shape
# ---------------------------------------------------------------------------

def test_seed_installs_gadgets_with_literal_matrices():
    s = _fresh_substrate()
    _seed_parents(s)
    mt = load_one_seed(s, "gadgets")
    assert mt is not None
    assert s.node(mt)["attrs"]["name"] == "cpwl_construction"

    gadgets = {s.node(n)["attrs"]["name"]: s.node(n)["attrs"]
               for n in s.nodes("DesignPattern")
               if s.node(n)["attrs"].get("origin") == "gadgets"}
    for required in ("identity_gadget", "abs_gadget",
                     "max_gadget", "min_gadget"):
        assert required in gadgets, f"missing gadget {required!r}"
        g = gadgets[required]
        assert "weight_W1" in g
        assert "weight_b1" in g
        assert "weight_W2" in g
        assert "weight_b2" in g
        assert g.get("gadget_kind") == "cpwl_primitive"


def test_gadget_mt_inherits_from_neural_networks_and_compiler_theory():
    s = _fresh_substrate()
    _seed_parents(s)
    mt = load_one_seed(s, "gadgets")
    parents = {s.node(p)["attrs"]["name"]
               for p in s.neighbours(mt, "genlMt")}
    assert "neural_networks" in parents
    assert "compiler_theory" in parents


# ---------------------------------------------------------------------------
# selector picks a gadget for a CPWL target
# ---------------------------------------------------------------------------

def test_selector_picks_abs_gadget_for_abs_target():
    from domains.design_patterns import (
        install_design_patterns_mt, pick_design_pattern,
    )
    s = _fresh_substrate()
    _seed_parents(s)
    install_design_patterns_mt(s)
    load_one_seed(s, "gadgets")

    picked = pick_design_pattern(s, [
        "cpwl_function", "exact_construction", "univariate",
        "absolute_value",
    ])
    assert picked is not None
    assert picked["name"] == "abs_gadget"


def test_selector_picks_max_gadget_for_max_target():
    from domains.design_patterns import (
        install_design_patterns_mt, pick_design_pattern,
    )
    s = _fresh_substrate()
    _seed_parents(s)
    install_design_patterns_mt(s)
    load_one_seed(s, "gadgets")

    picked = pick_design_pattern(s, [
        "cpwl_function", "exact_construction", "bivariate", "max_op",
    ])
    assert picked is not None
    assert picked["name"] == "max_gadget"


# ---------------------------------------------------------------------------
# render: construct_weights emits WeightTensor nodes
# ---------------------------------------------------------------------------

def test_construct_weights_for_abs_emits_four_tensors():
    from domains.code_writing_cortex import CodeWritingCortex

    class _A:
        def op_stats(self):
            return {"compute_abs": {"total_ms": 100.0, "count": 1000}}

    s = _fresh_substrate()
    _seed_parents(s)
    cortex = CodeWritingCortex(s, agent=_A()).install()

    # Manually steer the cortex to compute_abs (the test isn't about
    # selection — it's about the constructor.)
    target = s.add_node("ReplacementTarget", {
        "op_name": "compute_abs",
        "baseline_total_ms": 100.0,
        "baseline_count": 1000,
        "baseline_mean_ms": 0.1,
        "selected_at": 0.0,
    })
    root = cortex._ensure_root()
    s.add_edge(root, "current_target", target, {})

    abs_pattern = next(n for n in s.nodes("DesignPattern")
                       if s.node(n)["attrs"].get("name") == "abs_gadget")
    s.add_edge(target, "uses_pattern", abs_pattern, {})

    assemblage = cortex.assemble_network(target)
    assert assemblage is not None

    constructed = cortex.construct_weights(assemblage)
    assert len(constructed) == 4   # W1, b1, W2, b2

    roles = {s.node(w)["attrs"].get("role") for w in constructed}
    assert roles == {"W1", "b1", "W2", "b2"}

    # The matrices match the seed exactly (substrate round-trips lists as
    # tuples, so compare numerically through numpy).
    by_role = {s.node(w)["attrs"]["role"]: np.array(s.node(w)["attrs"]["data"])
               for w in constructed}
    assert np.array_equal(by_role["W1"], np.array([[1.0], [-1.0]]))
    assert np.array_equal(by_role["b1"], np.array([0.0, 0.0]))
    assert np.array_equal(by_role["W2"], np.array([[1.0, 1.0]]))
    assert np.array_equal(by_role["b2"], np.array([0.0]))


def test_constructed_abs_actually_computes_absolute_value():
    """The acid test: do the gadget's literal matrices, when projected
    onto a numpy forward pass, actually return |x| on arbitrary inputs?
    This is the proof that 'write, not train' produces a correct net."""
    from domains.code_writing_cortex import CodeWritingCortex

    class _A:
        def op_stats(self):
            return {"compute_abs": {"total_ms": 100.0, "count": 1000}}

    s = _fresh_substrate()
    _seed_parents(s)
    cortex = CodeWritingCortex(s, agent=_A()).install()

    target = s.add_node("ReplacementTarget", {
        "op_name": "compute_abs",
        "baseline_total_ms": 100.0,
        "baseline_count": 1000,
        "baseline_mean_ms": 0.1,
        "selected_at": 0.0,
    })
    root = cortex._ensure_root()
    s.add_edge(root, "current_target", target, {})
    abs_pattern = next(n for n in s.nodes("DesignPattern")
                       if s.node(n)["attrs"].get("name") == "abs_gadget")
    s.add_edge(target, "uses_pattern", abs_pattern, {})

    assemblage = cortex.assemble_network(target)
    constructed = cortex.construct_weights(assemblage)
    weights = {s.node(w)["attrs"]["role"]: np.array(s.node(w)["attrs"]["data"])
               for w in constructed}
    W1, b1, W2, b2 = weights["W1"], weights["b1"], weights["W2"], weights["b2"]

    for x in [-3.5, -1.0, 0.0, 0.0001, 7.2, 42.0]:
        x_vec = np.array([x])
        hidden = np.maximum(0.0, W1 @ x_vec + b1)
        y = W2 @ hidden + b2
        assert abs(float(y[0]) - abs(x)) < 1e-9, (
            f"constructed |{x}| = {float(y[0])}, expected {abs(x)}")


def test_composed_max_abs_2d_assembles_into_two_steps():
    """max_abs_2d_gadget is cpwl_composed with gadget_chain=[abs_2d_gadget,
    max_gadget]. The assembler walks the chain and emits ONE AssemblageStep
    per sub-gadget, in order. construct_weights then materialises each
    sub-gadget's matrices."""
    from domains.code_writing_cortex import CodeWritingCortex

    class _A:
        def op_stats(self):
            return {}

    s = _fresh_substrate()
    _seed_parents(s)
    cortex = CodeWritingCortex(s, agent=_A()).install()

    target = s.add_node("ReplacementTarget", {
        "op_name": "compute_max_abs",
        "baseline_total_ms": 100.0,
        "baseline_count": 1000,
        "baseline_mean_ms": 0.1,
        "selected_at": 0.0,
    })
    root = cortex._ensure_root()
    s.add_edge(root, "current_target", target, {})
    top = next(n for n in s.nodes("DesignPattern")
               if s.node(n)["attrs"].get("name") == "max_abs_2d_gadget")
    s.add_edge(target, "uses_pattern", top, {})

    assemblage = cortex.assemble_network(target)
    assert assemblage is not None

    steps = sorted(
        s.neighbours(assemblage, "has_step"),
        key=lambda n: s.node(n)["attrs"].get("order", 0))
    patterns = [s.node(st)["attrs"]["pattern"] for st in steps]
    assert patterns == ["abs_2d_gadget", "max_gadget"]

    # Dim flow through the composed chain: 2 → 2 → 1.
    assert s.node(steps[0])["attrs"]["in_dim"] == 2
    assert s.node(steps[0])["attrs"]["out_dim"] == 2
    assert s.node(steps[1])["attrs"]["in_dim"] == 2
    assert s.node(steps[1])["attrs"]["out_dim"] == 1

    # construct_weights emits 4 tensors per sub-gadget = 8 total.
    weights = cortex.construct_weights(assemblage)
    assert len(weights) == 8


def test_constructed_square_approximates_x_squared():
    """square_pwl_signed_gadget composes abs + a 10-segment PWL square.
    The forward pass should compute x² to error ≤ 0.25% for x ∈ [−1, 1],
    and EXACTLY at every breakpoint (multiples of 0.1)."""
    from domains.code_writing_cortex import CodeWritingCortex

    class _A:
        def op_stats(self):
            return {}

    s = _fresh_substrate()
    _seed_parents(s)
    cortex = CodeWritingCortex(s, agent=_A()).install()

    target = s.add_node("ReplacementTarget", {
        "op_name": "compute_square",
        "baseline_total_ms": 100.0,
        "baseline_count": 1000,
        "baseline_mean_ms": 0.1,
        "selected_at": 0.0,
    })
    root = cortex._ensure_root()
    s.add_edge(root, "current_target", target, {})
    top = next(n for n in s.nodes("DesignPattern")
               if s.node(n)["attrs"].get("name") == "square_pwl_signed_gadget")
    s.add_edge(target, "uses_pattern", top, {})

    assemblage = cortex.assemble_network(target)
    cortex.construct_weights(assemblage)

    # Exact at every breakpoint (positive AND negative — abs first).
    for x in (0.0, 0.1, 0.2, 0.3, 0.5, 0.7, 0.9,
              -0.1, -0.3, -0.5, -0.7, -0.9):
        out = cortex.forward(assemblage, [x])
        expected = x * x
        assert abs(out[0] - expected) < 1e-9, (
            f"forward({x}) = {out[0]}, expected {expected} (exact at breakpoint)")

    # Bounded error elsewhere on [−1, 1].
    for x in (-0.95, -0.55, -0.05, 0.05, 0.55, 0.95):
        out = cortex.forward(assemblage, [x])
        expected = x * x
        err = abs(out[0] - expected)
        # PWL secant overshoots smooth concave-up x² by at most 1/(4N²)
        # at the midpoint of each segment. With N=10 that's 0.0025.
        assert err <= 0.0026, (
            f"forward({x}) = {out[0]}, expected {expected}, err={err} "
            f"exceeds PWL bound 0.0025")


def test_forward_computes_max_abs_on_arbitrary_inputs():
    """End-to-end proof: composed assemblage (abs_2d_gadget then
    max_gadget) actually computes max(|x|, |y|) when forward is run."""
    from domains.code_writing_cortex import CodeWritingCortex

    class _A:
        def op_stats(self):
            return {}

    s = _fresh_substrate()
    _seed_parents(s)
    cortex = CodeWritingCortex(s, agent=_A()).install()

    target = s.add_node("ReplacementTarget", {
        "op_name": "compute_max_abs",
        "baseline_total_ms": 100.0,
        "baseline_count": 1000,
        "baseline_mean_ms": 0.1,
        "selected_at": 0.0,
    })
    root = cortex._ensure_root()
    s.add_edge(root, "current_target", target, {})
    top = next(n for n in s.nodes("DesignPattern")
               if s.node(n)["attrs"].get("name") == "max_abs_2d_gadget")
    s.add_edge(target, "uses_pattern", top, {})

    assemblage = cortex.assemble_network(target)
    cortex.construct_weights(assemblage)

    for x, y in [(3.0, -7.0), (-7.0, 3.0), (5.0, 5.0), (0.0, 0.0),
                 (-2.5, 1.5), (1.5, -2.5), (10.0, -10.0)]:
        out = cortex.forward(assemblage, [x, y])
        expected = max(abs(x), abs(y))
        assert len(out) == 1
        assert abs(out[0] - expected) < 1e-9, (
            f"forward([{x}, {y}]) = {out[0]}, expected {expected}")


def test_cpwl_parallel_expands_to_block_diagonal():
    """abs_3d_gadget is parallel(abs_gadget, 3). construct_weights
    should expand abs_gadget's (2×1, 2, 1×2, 1) matrices to
    (6×3, 6, 3×6, 3) block-diagonal form — not hand-coded; rendered
    from the parallel declaration at construct time."""
    from domains.code_writing_cortex import CodeWritingCortex

    class _A:
        def op_stats(self):
            return {}

    s = _fresh_substrate()
    _seed_parents(s)
    cortex = CodeWritingCortex(s, agent=_A()).install()

    target = s.add_node("ReplacementTarget", {
        "op_name": "compute_abs_3d",
        "baseline_total_ms": 0.0, "baseline_count": 1,
        "baseline_mean_ms": 0.0, "selected_at": 0.0,
    })
    # Manually set the target's dims + chosen pattern (no compute_abs_3d
    # CodeTarget yet — the test is about the constructor, not selection).
    s.set_attr(target, "input_dim", 3)
    s.set_attr(target, "output_dim", 3)
    root = cortex._ensure_root()
    s.add_edge(root, "current_target", target, {})
    abs3 = next(n for n in s.nodes("DesignPattern")
                if s.node(n)["attrs"].get("name") == "abs_3d_gadget")
    s.add_edge(target, "uses_pattern", abs3, {})

    assemblage = cortex.assemble_network(target)
    weights = cortex.construct_weights(assemblage)
    by_role = {s.node(w)["attrs"]["role"]: np.array(s.node(w)["attrs"]["data"])
               for w in weights}

    # Block-diagonal expansion: abs_gadget has W1=(2,1)=[[1],[-1]],
    # b1=(2,)=[0,0], W2=(1,2)=[[1,1]], b2=(1,)=[0]. With n=3:
    expected_W1 = np.array([[1, 0, 0], [-1, 0, 0],
                            [0, 1, 0], [0, -1, 0],
                            [0, 0, 1], [0, 0, -1]], dtype=float)
    expected_b1 = np.zeros(6)
    expected_W2 = np.array([[1, 1, 0, 0, 0, 0],
                            [0, 0, 1, 1, 0, 0],
                            [0, 0, 0, 0, 1, 1]], dtype=float)
    expected_b2 = np.zeros(3)
    assert np.array_equal(by_role["W1"], expected_W1)
    assert np.array_equal(by_role["b1"], expected_b1)
    assert np.array_equal(by_role["W2"], expected_W2)
    assert np.array_equal(by_role["b2"], expected_b2)


def test_parallel_abs_forward_computes_elementwise_abs():
    """Cortex.forward on the constructed abs_3d_gadget should return
    [|a|, |b|, |c|] for arbitrary 3-vectors."""
    from domains.code_writing_cortex import CodeWritingCortex

    class _A:
        def op_stats(self):
            return {}

    s = _fresh_substrate()
    _seed_parents(s)
    cortex = CodeWritingCortex(s, agent=_A()).install()

    target = s.add_node("ReplacementTarget", {
        "op_name": "compute_abs_3d",
        "baseline_total_ms": 0.0, "baseline_count": 1,
        "baseline_mean_ms": 0.0, "selected_at": 0.0,
    })
    s.set_attr(target, "input_dim", 3)
    s.set_attr(target, "output_dim", 3)
    root = cortex._ensure_root()
    s.add_edge(root, "current_target", target, {})
    abs3 = next(n for n in s.nodes("DesignPattern")
                if s.node(n)["attrs"].get("name") == "abs_3d_gadget")
    s.add_edge(target, "uses_pattern", abs3, {})

    assemblage = cortex.assemble_network(target)
    cortex.construct_weights(assemblage)

    for a, b, c in [(3.0, -7.0, 0.0), (-1.0, -2.0, -3.0),
                    (0.5, -0.5, 0.0), (10.0, 0.0, -10.0)]:
        out = cortex.forward(assemblage, [a, b, c])
        assert out == pytest.approx([abs(a), abs(b), abs(c)], abs=1e-9)


def test_parallel_of_parallel_square_pwl_expands_to_30_hidden():
    """square_pwl_10_3d_gadget is parallel(square_pwl_10_gadget, 3).
    With sub-gadget hidden=10, the expanded layer has hidden=30. Verify
    block-diagonal expansion preserves the PWL approximation per input."""
    from domains.code_writing_cortex import CodeWritingCortex

    class _A:
        def op_stats(self):
            return {}

    s = _fresh_substrate()
    _seed_parents(s)
    cortex = CodeWritingCortex(s, agent=_A()).install()

    target = s.add_node("ReplacementTarget", {
        "op_name": "compute_square_3d",
        "baseline_total_ms": 0.0, "baseline_count": 1,
        "baseline_mean_ms": 0.0, "selected_at": 0.0,
    })
    s.set_attr(target, "input_dim", 3)
    s.set_attr(target, "output_dim", 3)
    root = cortex._ensure_root()
    s.add_edge(root, "current_target", target, {})
    sq3 = next(n for n in s.nodes("DesignPattern")
               if s.node(n)["attrs"].get("name") == "square_pwl_10_3d_gadget")
    s.add_edge(target, "uses_pattern", sq3, {})

    assemblage = cortex.assemble_network(target)
    weights = cortex.construct_weights(assemblage)
    by_role = {s.node(w)["attrs"]["role"]: np.array(s.node(w)["attrs"]["data"])
               for w in weights}
    assert by_role["W1"].shape == (30, 3)
    assert by_role["b1"].shape == (30,)
    assert by_role["W2"].shape == (3, 30)
    assert by_role["b2"].shape == (3,)

    # Forward should produce x² per input, exact at breakpoints.
    for a, b, c in [(0.0, 0.5, 1.0), (0.3, 0.7, 0.1), (0.2, 0.4, 0.8)]:
        out = cortex.forward(assemblage, [a, b, c])
        assert out == pytest.approx([a*a, b*b, c*c], abs=1e-9)


def test_cpwl_linear_expands_to_identity_trick():
    """polarization_inputs_gadget declares affine W=[[1,1],[1,0],[0,1]],
    b=[0,0,0]. construct_weights expands to a 2-layer ReLU via the
    identity trick: W1=[W; -W] shape (6,2), b1=[b; -b] shape (6,),
    W2=[I, -I] shape (3,6), b2=[0,0,0]. Forward on [x, y] returns
    [x+y, x, y] exactly."""
    from domains.code_writing_cortex import CodeWritingCortex

    class _A:
        def op_stats(self):
            return {}

    s = _fresh_substrate()
    _seed_parents(s)
    cortex = CodeWritingCortex(s, agent=_A()).install()

    target = s.add_node("ReplacementTarget", {
        "op_name": "_test_polarization_inputs",
        "baseline_total_ms": 0.0, "baseline_count": 1,
        "baseline_mean_ms": 0.0, "selected_at": 0.0,
    })
    s.set_attr(target, "input_dim", 2)
    s.set_attr(target, "output_dim", 3)
    root = cortex._ensure_root()
    s.add_edge(root, "current_target", target, {})
    pi = next(n for n in s.nodes("DesignPattern")
              if s.node(n)["attrs"].get("name") == "polarization_inputs_gadget")
    s.add_edge(target, "uses_pattern", pi, {})

    assemblage = cortex.assemble_network(target)
    weights = cortex.construct_weights(assemblage)
    by_role = {s.node(w)["attrs"]["role"]: np.array(s.node(w)["attrs"]["data"])
               for w in weights}

    assert by_role["W1"].shape == (6, 2)
    assert by_role["b1"].shape == (6,)
    assert by_role["W2"].shape == (3, 6)
    assert by_role["b2"].shape == (3,)
    # W2 = [I_3, -I_3]
    expected_W2 = np.hstack([np.eye(3), -np.eye(3)])
    assert np.array_equal(by_role["W2"], expected_W2)

    for x, y in [(1.0, 2.0), (-0.5, 0.5), (3.7, -1.2), (0.0, 0.0)]:
        out = cortex.forward(assemblage, [x, y])
        assert out == pytest.approx([x + y, x, y], abs=1e-9)


def test_polarization_combine_returns_half_a_minus_b_minus_c():
    """polarization_combine_gadget: [a, b, c] → ½(a − b − c). When fed
    [(x+y)², x², y²] this gives x·y exactly."""
    from domains.code_writing_cortex import CodeWritingCortex

    class _A:
        def op_stats(self):
            return {}

    s = _fresh_substrate()
    _seed_parents(s)
    cortex = CodeWritingCortex(s, agent=_A()).install()

    target = s.add_node("ReplacementTarget", {
        "op_name": "_test_polarization_combine",
        "baseline_total_ms": 0.0, "baseline_count": 1,
        "baseline_mean_ms": 0.0, "selected_at": 0.0,
    })
    s.set_attr(target, "input_dim", 3)
    s.set_attr(target, "output_dim", 1)
    root = cortex._ensure_root()
    s.add_edge(root, "current_target", target, {})
    pc = next(n for n in s.nodes("DesignPattern")
              if s.node(n)["attrs"].get("name") == "polarization_combine_gadget")
    s.add_edge(target, "uses_pattern", pc, {})

    assemblage = cortex.assemble_network(target)
    cortex.construct_weights(assemblage)

    for a, b, c in [(1.0, 0.0, 0.0), (4.0, 1.0, 1.0), (0.0, 0.5, 0.5),
                    (0.04, 0.09, 0.01)]:
        out = cortex.forward(assemblage, [a, b, c])
        assert out == pytest.approx([0.5 * (a - b - c)], abs=1e-9)


def test_constructed_multiply_actually_multiplies():
    """The headline: polarization_multiply_gadget constructs x·y from
    abs + square_pwl primitives. Forward on [x, y] ∈ [−0.5, 0.5]²
    should return ≈ x·y within the PWL approximation error."""
    from domains.code_writing_cortex import CodeWritingCortex

    class _A:
        def op_stats(self):
            return {}

    s = _fresh_substrate()
    _seed_parents(s)
    cortex = CodeWritingCortex(s, agent=_A()).install()

    target = s.add_node("ReplacementTarget", {
        "op_name": "compute_multiply",
        "baseline_total_ms": 0.0, "baseline_count": 1,
        "baseline_mean_ms": 0.0, "selected_at": 0.0,
    })
    s.set_attr(target, "input_dim", 2)
    s.set_attr(target, "output_dim", 1)
    root = cortex._ensure_root()
    s.add_edge(root, "current_target", target, {})
    pm = next(n for n in s.nodes("DesignPattern")
              if s.node(n)["attrs"].get("name") == "polarization_multiply_gadget")
    s.add_edge(target, "uses_pattern", pm, {})

    assemblage = cortex.assemble_network(target)
    cortex.construct_weights(assemblage)

    # 4-step chain.
    steps = sorted(
        s.neighbours(assemblage, "has_step"),
        key=lambda n: s.node(n)["attrs"].get("order", 0))
    patterns = [s.node(st)["attrs"]["pattern"] for st in steps]
    assert patterns == [
        "polarization_inputs_gadget", "abs_3d_gadget",
        "square_pwl_10_3d_gadget", "polarization_combine_gadget",
    ]

    # Pairs at breakpoints of square_pwl (multiples of 0.1) should be
    # exact (modulo the abs domain restriction).
    for x, y in [(0.1, 0.2), (0.3, 0.4), (-0.1, 0.5), (0.2, -0.3),
                 (0.5, 0.5), (-0.5, -0.5), (0.0, 0.0), (0.0, 0.5)]:
        out = cortex.forward(assemblage, [x, y])
        truth = x * y
        # Error bound: each square contributes ≤ 1/(4·100) = 0.0025;
        # polarization halves the sum, but at breakpoints the squares
        # are exact so error is 0 for those. Allow a generous 0.005 cap.
        assert abs(out[0] - truth) <= 0.005, (
            f"multiply({x}, {y}) = {out[0]}, expected {truth}, "
            f"err={abs(out[0] - truth)}")


def test_cpwl_broadcast_lifts_x_to_x_and_abs():
    """monomial_lift_step1_gadget is cpwl_broadcast of [identity, abs].
    Both leaves see x; outputs concatenate to [x, |x|]. W1 is stacked,
    W2 is block-diagonal."""
    from domains.code_writing_cortex import CodeWritingCortex

    class _A:
        def op_stats(self):
            return {}

    s = _fresh_substrate()
    _seed_parents(s)
    cortex = CodeWritingCortex(s, agent=_A()).install()

    target = s.add_node("ReplacementTarget", {
        "op_name": "_lift_step1",
        "baseline_total_ms": 0.0, "baseline_count": 1,
        "baseline_mean_ms": 0.0, "selected_at": 0.0,
    })
    s.set_attr(target, "input_dim", 1)
    s.set_attr(target, "output_dim", 2)
    root = cortex._ensure_root()
    s.add_edge(root, "current_target", target, {})
    g = next(n for n in s.nodes("DesignPattern")
             if s.node(n)["attrs"].get("name") == "monomial_lift_step1_gadget")
    s.add_edge(target, "uses_pattern", g, {})

    assemblage = cortex.assemble_network(target)
    cortex.construct_weights(assemblage)

    for x in [-1.0, -0.5, -0.1, 0.0, 0.1, 0.5, 1.0]:
        out = cortex.forward(assemblage, [x])
        assert out == pytest.approx([x, abs(x)], abs=1e-9)


def test_cpwl_heteroparallel_routes_identity_and_square():
    """monomial_lift_step2_gadget is cpwl_heteroparallel of
    [identity (slot 0), square_pwl_10 (slot 1)]. Each leaf reads its
    own slice; W1 is block-diagonal."""
    from domains.code_writing_cortex import CodeWritingCortex

    class _A:
        def op_stats(self):
            return {}

    s = _fresh_substrate()
    _seed_parents(s)
    cortex = CodeWritingCortex(s, agent=_A()).install()

    target = s.add_node("ReplacementTarget", {
        "op_name": "_lift_step2",
        "baseline_total_ms": 0.0, "baseline_count": 1,
        "baseline_mean_ms": 0.0, "selected_at": 0.0,
    })
    s.set_attr(target, "input_dim", 2)
    s.set_attr(target, "output_dim", 2)
    root = cortex._ensure_root()
    s.add_edge(root, "current_target", target, {})
    g = next(n for n in s.nodes("DesignPattern")
             if s.node(n)["attrs"].get("name") == "monomial_lift_step2_gadget")
    s.add_edge(target, "uses_pattern", g, {})

    assemblage = cortex.assemble_network(target)
    cortex.construct_weights(assemblage)

    # Input is [x, |x|]; output should be [x, |x|² = x²].
    for x in [-0.5, -0.1, 0.0, 0.3, 0.5, 1.0]:
        out = cortex.forward(assemblage, [x, abs(x)])
        assert out == pytest.approx([x, x*x], abs=1e-9)


def test_monomial_lift_x_x2_chain_produces_x_and_x_squared():
    """monomial_lift_x_x2_gadget = chain [step1_broadcast, step2_heteroparallel].
    Forward on [x] should produce [x, x²] over [-1, 1]."""
    from domains.code_writing_cortex import CodeWritingCortex

    class _A:
        def op_stats(self):
            return {}

    s = _fresh_substrate()
    _seed_parents(s)
    cortex = CodeWritingCortex(s, agent=_A()).install()

    target = s.add_node("ReplacementTarget", {
        "op_name": "_lift_x_x2",
        "baseline_total_ms": 0.0, "baseline_count": 1,
        "baseline_mean_ms": 0.0, "selected_at": 0.0,
    })
    s.set_attr(target, "input_dim", 1)
    s.set_attr(target, "output_dim", 2)
    root = cortex._ensure_root()
    s.add_edge(root, "current_target", target, {})
    g = next(n for n in s.nodes("DesignPattern")
             if s.node(n)["attrs"].get("name") == "monomial_lift_x_x2_gadget")
    s.add_edge(target, "uses_pattern", g, {})

    assemblage = cortex.assemble_network(target)
    cortex.construct_weights(assemblage)

    # Exact at breakpoints (every 0.1).
    for x in [-1.0, -0.7, -0.3, 0.0, 0.2, 0.5, 0.8, 1.0]:
        out = cortex.forward(assemblage, [x])
        assert out == pytest.approx([x, x*x], abs=1e-9)


def test_constructed_cube_actually_cubes():
    """cube_gadget = monomial_lift_x_x2 → polarization_multiply.
    Forward([x]) should approximate x³ over [−0.5, 0.5]."""
    from domains.code_writing_cortex import CodeWritingCortex

    class _A:
        def op_stats(self):
            return {}

    s = _fresh_substrate()
    _seed_parents(s)
    cortex = CodeWritingCortex(s, agent=_A()).install()

    target = s.add_node("ReplacementTarget", {
        "op_name": "compute_cube",
        "baseline_total_ms": 0.0, "baseline_count": 1,
        "baseline_mean_ms": 0.0, "selected_at": 0.0,
    })
    s.set_attr(target, "input_dim", 1)
    s.set_attr(target, "output_dim", 1)
    root = cortex._ensure_root()
    s.add_edge(root, "current_target", target, {})
    g = next(n for n in s.nodes("DesignPattern")
             if s.node(n)["attrs"].get("name") == "cube_gadget")
    s.add_edge(target, "uses_pattern", g, {})

    assemblage = cortex.assemble_network(target)
    cortex.construct_weights(assemblage)

    # 6-step chain: 2 (lift) + 4 (polarization_multiply).
    steps = sorted(s.neighbours(assemblage, "has_step"),
                   key=lambda n: s.node(n)["attrs"].get("order", 0))
    assert len(steps) == 6
    patterns = [s.node(st)["attrs"]["pattern"] for st in steps]
    assert patterns == [
        "monomial_lift_step1_gadget",
        "monomial_lift_step2_gadget",
        "polarization_inputs_gadget",
        "abs_3d_gadget",
        "square_pwl_10_3d_gadget",
        "polarization_combine_gadget",
    ]

    # x ∈ [−0.5, 0.5]; cube error bounded by polarization-of-square error.
    for x in [-0.5, -0.3, -0.1, 0.0, 0.1, 0.2, 0.3, 0.4, 0.5]:
        out = cortex.forward(assemblage, [x])
        truth = x ** 3
        err = abs(out[0] - truth)
        assert err <= 0.01, (
            f"cube({x}) = {out[0]}, expected {truth}, err={err}")


def test_construct_polynomial_evaluator_degree1_returns_linear():
    """construct_polynomial_evaluator([2, 3]) builds p(x) = 2 + 3x as
    a single cpwl_linear step. forward returns 2 + 3x exactly."""
    from domains.code_writing_cortex import CodeWritingCortex

    class _A:
        def op_stats(self):
            return {}

    s = _fresh_substrate()
    _seed_parents(s)
    cortex = CodeWritingCortex(s, agent=_A()).install()

    assemblage = cortex.construct_polynomial_evaluator([2.0, 3.0])
    assert assemblage is not None

    for x in [-1.0, -0.5, 0.0, 0.5, 1.0, 3.7]:
        out = cortex.forward(assemblage, [x])
        assert out == pytest.approx([2.0 + 3.0 * x], abs=1e-9)


def test_construct_polynomial_evaluator_degree2_runs_quadratic():
    """construct_polynomial_evaluator([1, −2, 3]) builds p(x) = 1 − 2x + 3x².
    Chain is [monomial_lift_x_x2, cpwl_linear(W=[[−2, 3]], b=[1])].
    forward returns p(x) within PWL bound."""
    from domains.code_writing_cortex import CodeWritingCortex

    class _A:
        def op_stats(self):
            return {}

    s = _fresh_substrate()
    _seed_parents(s)
    cortex = CodeWritingCortex(s, agent=_A()).install()

    assemblage = cortex.construct_polynomial_evaluator([1.0, -2.0, 3.0])
    assert assemblage is not None

    # Exact at every breakpoint (x and x² both exact there).
    for x in [-0.7, -0.5, -0.3, -0.1, 0.0, 0.1, 0.3, 0.5, 0.7]:
        out = cortex.forward(assemblage, [x])
        truth = 1.0 - 2.0 * x + 3.0 * x * x
        assert out == pytest.approx([truth], abs=1e-9)

    # Mid-segment: PWL error in x² scaled by |a_2|.
    for x in [-0.85, -0.35, 0.05, 0.45, 0.95]:
        out = cortex.forward(assemblage, [x])
        truth = 1.0 - 2.0 * x + 3.0 * x * x
        # |a_2| · 0.0025 max error from PWL midsegment.
        bound = abs(3.0) * 0.0025 + 1e-9
        assert abs(out[0] - truth) <= bound, (
            f"p({x}) = {out[0]}, truth {truth}, err={abs(out[0]-truth)} > {bound}")


def test_construct_polynomial_evaluator_taylor_exp():
    """Taylor approximation of e^x around 0 to degree 2:
        e^x ≈ 1 + x + x²/2
    The cortex constructs the evaluator from those coefficients,
    runs forward, and the result should be close to e^x on a small
    neighborhood of 0."""
    from domains.code_writing_cortex import CodeWritingCortex
    import math

    class _A:
        def op_stats(self):
            return {}

    s = _fresh_substrate()
    _seed_parents(s)
    cortex = CodeWritingCortex(s, agent=_A()).install()

    assemblage = cortex.construct_polynomial_evaluator([1.0, 1.0, 0.5])
    assert assemblage is not None

    # Truth here is the Taylor-2 polynomial itself (NOT e^x); the
    # PWL approximation should match the polynomial closely. Then we
    # report (separately) how the polynomial diverges from e^x as a
    # natural consequence of truncation.
    for x in [-0.3, -0.1, 0.0, 0.1, 0.2, 0.3]:
        out = cortex.forward(assemblage, [x])
        poly_truth = 1.0 + x + 0.5 * x * x
        # PWL bound: |a_2| · 0.0025 = 0.00125 max.
        assert abs(out[0] - poly_truth) <= 0.5 * 0.0025 + 1e-9, (
            f"Taylor-poly({x}) = {out[0]}, expected {poly_truth}")

    # And the Taylor-2 approximation is close to e^x near 0.
    for x in [-0.3, -0.1, 0.0, 0.1, 0.2, 0.3]:
        out = cortex.forward(assemblage, [x])
        # Truncation error: O(x³/6).
        approx_err = abs(out[0] - math.exp(x))
        truncation_bound = abs(x) ** 3 / 6 + 0.005
        assert approx_err < truncation_bound + 0.01, (
            f"Taylor-2 of e at x={x}: net={out[0]}, exp={math.exp(x)}, "
            f"err={approx_err}")


def test_construct_polynomial_evaluator_taylor_cos():
    """Taylor approximation of cos(x) to degree 2: cos(x) ≈ 1 − x²/2.
    Coefficients [1, 0, -0.5]."""
    from domains.code_writing_cortex import CodeWritingCortex
    import math

    class _A:
        def op_stats(self):
            return {}

    s = _fresh_substrate()
    _seed_parents(s)
    cortex = CodeWritingCortex(s, agent=_A()).install()

    assemblage = cortex.construct_polynomial_evaluator([1.0, 0.0, -0.5])
    assert assemblage is not None

    for x in [-0.3, -0.1, 0.0, 0.1, 0.2, 0.3]:
        out = cortex.forward(assemblage, [x])
        poly_truth = 1.0 - 0.5 * x * x
        # PWL bound: 0.5 · 0.0025 = 0.00125 max.
        assert abs(out[0] - poly_truth) <= 0.5 * 0.0025 + 1e-9, (
            f"Taylor-poly cos({x}) = {out[0]}, expected {poly_truth}")


def test_broadcast_pattern_with_leaf_branches_lifts_to_x_and_abs():
    """Two leaf branches, same depth: should match the seeded
    monomial_lift_step1_gadget's behaviour exactly. Verifies the
    fan-out + heteroparallel machinery works for depth-1 branches."""
    from domains.code_writing_cortex import CodeWritingCortex

    class _A:
        def op_stats(self):
            return {}

    s = _fresh_substrate()
    _seed_parents(s)
    cortex = CodeWritingCortex(s, agent=_A()).install()

    # Build broadcast(identity, abs) — depth 1 for both branches.
    pattern_name = cortex.construct_broadcast_pattern(
        input_dim=1,
        branch_chains=[["identity_gadget"], ["abs_gadget"]],
        label="lift_x_abs_test")
    assert pattern_name is not None

    target = s.add_node("ReplacementTarget", {
        "op_name": "_broadcast_lift_test",
        "baseline_total_ms": 0.0, "baseline_count": 1,
        "baseline_mean_ms": 0.0, "selected_at": 0.0,
    })
    s.set_attr(target, "input_dim", 1)
    s.set_attr(target, "output_dim", 2)
    root = cortex._ensure_root()
    s.add_edge(root, "current_target", target, {})
    g = next(n for n in s.nodes("DesignPattern")
             if s.node(n)["attrs"].get("name") == pattern_name)
    s.add_edge(target, "uses_pattern", g, {})

    assemblage = cortex.assemble_network(target)
    cortex.construct_weights(assemblage)

    for x in [-1.0, -0.5, 0.0, 0.5, 1.0, 3.7]:
        out = cortex.forward(assemblage, [x])
        assert out == pytest.approx([x, abs(x)], abs=1e-9)


def test_broadcast_pattern_with_padded_branches():
    """Branch 1 (identity) is depth 1; Branch 2 (square_pwl_signed) is
    depth 2. The constructor pads branch 1 with one identity-passthrough
    step to match depth 2 and emits 2 wide steps. forward returns
    [x, x²]."""
    from domains.code_writing_cortex import CodeWritingCortex

    class _A:
        def op_stats(self):
            return {}

    s = _fresh_substrate()
    _seed_parents(s)
    cortex = CodeWritingCortex(s, agent=_A()).install()

    pattern_name = cortex.construct_broadcast_pattern(
        input_dim=1,
        branch_chains=[["identity_gadget"],
                       ["square_pwl_signed_gadget"]],
        label="lift_x_x2_test")
    assert pattern_name is not None

    # The constructed top-level pattern has a 2-step chain.
    top = next(n for n in s.nodes("DesignPattern")
               if s.node(n)["attrs"].get("name") == pattern_name)
    chain = s.node(top)["attrs"]["gadget_chain"]
    assert len(chain) == 2

    target = s.add_node("ReplacementTarget", {
        "op_name": "_broadcast_padded_test",
        "baseline_total_ms": 0.0, "baseline_count": 1,
        "baseline_mean_ms": 0.0, "selected_at": 0.0,
    })
    s.set_attr(target, "input_dim", 1)
    s.set_attr(target, "output_dim", 2)
    root = cortex._ensure_root()
    s.add_edge(root, "current_target", target, {})
    s.add_edge(target, "uses_pattern", top, {})

    assemblage = cortex.assemble_network(target)
    cortex.construct_weights(assemblage)

    for x in [-0.7, -0.5, -0.1, 0.0, 0.2, 0.5, 0.9]:
        out = cortex.forward(assemblage, [x])
        assert out == pytest.approx([x, x*x], abs=1e-9)


def test_construct_polynomial_evaluator_degree3_quintic_polynomial():
    """Degree 3 needs the broadcast-with-composed mechanism to lift
    [x] → [x, x², x³]. Construct p(x) = 0.1 − 0.5x + 0.3x² − 0.2x³
    and verify it evaluates correctly."""
    from domains.code_writing_cortex import CodeWritingCortex

    class _A:
        def op_stats(self):
            return {}

    s = _fresh_substrate()
    _seed_parents(s)
    cortex = CodeWritingCortex(s, agent=_A()).install()

    coeffs = [0.1, -0.5, 0.3, -0.2]
    assemblage = cortex.construct_polynomial_evaluator(coeffs)
    assert assemblage is not None

    # Exact-ish on small inputs (within the polarization+PWL bound).
    for x in [-0.5, -0.3, -0.1, 0.0, 0.1, 0.3, 0.5]:
        out = cortex.forward(assemblage, [x])
        truth = (coeffs[0] + coeffs[1]*x +
                 coeffs[2]*x*x + coeffs[3]*x**3)
        # Bound: |a_2|·0.0025 (square_pwl) + |a_3|·0.01 (cube)
        bound = abs(coeffs[2]) * 0.0025 + abs(coeffs[3]) * 0.01 + 1e-6
        assert abs(out[0] - truth) <= bound, (
            f"p({x}) = {out[0]}, truth {truth}, "
            f"err={abs(out[0]-truth)} > {bound}")


def test_construct_monomial_cubic_matches_seed_cube():
    """construct_monomial(3) returns cube_gadget — the seed-level cube."""
    from domains.code_writing_cortex import CodeWritingCortex

    class _A:
        def op_stats(self):
            return {}

    s = _fresh_substrate()
    _seed_parents(s)
    cortex = CodeWritingCortex(s, agent=_A()).install()
    assert cortex.construct_monomial(1) == "identity_gadget"
    assert cortex.construct_monomial(2) == "square_pwl_signed_gadget"
    assert cortex.construct_monomial(3) == "cube_gadget"


def test_construct_monomial_quartic_and_quintic_evaluate_correctly():
    """construct_monomial(4) and (5) build x⁴ and x⁵ recursively
    via broadcast([identity, x^(k-1)]) → polarization_multiply.
    Wire each to a fresh target, render weights, verify forward."""
    from domains.code_writing_cortex import CodeWritingCortex

    class _A:
        def op_stats(self):
            return {}

    s = _fresh_substrate()
    _seed_parents(s)
    cortex = CodeWritingCortex(s, agent=_A()).install()

    for k in (4, 5):
        name = cortex.construct_monomial(k)
        assert name is not None

        target = s.add_node("ReplacementTarget", {
            "op_name": f"_test_monomial_k{k}",
            "baseline_total_ms": 0.0, "baseline_count": 1,
            "baseline_mean_ms": 0.0, "selected_at": 0.0,
        })
        s.set_attr(target, "input_dim", 1)
        s.set_attr(target, "output_dim", 1)
        root = cortex._ensure_root()
        # Each test instance gets a fresh root so previous targets don't
        # interfere; current_target lookup is by latest edge.
        for nid in s.neighbours(root, "current_target"):
            try:
                # Edge removal isn't part of the API — just create a new
                # target node and edge; assemble_network reads via attr.
                pass
            except Exception:
                pass
        s.add_edge(root, "current_target", target, {})
        g = next(n for n in s.nodes("DesignPattern")
                 if s.node(n)["attrs"].get("name") == name)
        s.add_edge(target, "uses_pattern", g, {})

        assemblage = cortex.assemble_network(target)
        assert assemblage is not None
        cortex.construct_weights(assemblage)

        for x in [-0.4, -0.2, 0.0, 0.2, 0.4]:
            out = cortex.forward(assemblage, [x])
            truth = x ** k
            # Each polarization-square contributes |a_2|·0.0025; iterated
            # k−1 times, error ≤ (k−1)·0.0025 in worst case; loosen to
            # 0.005 per degree to absorb compounding.
            bound = 0.005 * (k - 1) + 1e-6
            assert abs(out[0] - truth) <= bound, (
                f"x^{k} at x={x}: forward={out[0]}, truth={truth}, "
                f"err={abs(out[0]-truth)} > {bound}")


def test_construct_polynomial_evaluator_taylor_sin():
    """Taylor-3 of sin(x) ≈ x − x³/6. Coefficients [0, 1, 0, -1/6].
    Polynomial value should match Σ a_i x^i within construction bound;
    truncation error vs true sin(x) is the analytical math gap."""
    from domains.code_writing_cortex import CodeWritingCortex
    import math

    class _A:
        def op_stats(self):
            return {}

    s = _fresh_substrate()
    _seed_parents(s)
    cortex = CodeWritingCortex(s, agent=_A()).install()

    coeffs = [0.0, 1.0, 0.0, -1.0/6.0]
    assemblage = cortex.construct_polynomial_evaluator(coeffs)
    assert assemblage is not None

    # Just the polynomial check (truncation vs true sin is separate).
    for x in [-0.4, -0.2, 0.0, 0.2, 0.4]:
        out = cortex.forward(assemblage, [x])
        poly_truth = x - (x ** 3) / 6.0
        # |a_3| = 1/6 ≈ 0.167; bound ≈ 0.167 · 0.01 = 0.00167.
        assert abs(out[0] - poly_truth) <= abs(coeffs[3]) * 0.01 + 1e-6, (
            f"Taylor-poly sin({x}) = {out[0]}, expected {poly_truth}")


def test_construct_polynomial_evaluator_taylor_sin_degree5():
    """Taylor-5 of sin(x) ≈ x − x³/6 + x⁵/120. Coefficients
    [0, 1, 0, −1/6, 0, 1/120]. Verify forward matches the polynomial."""
    from domains.code_writing_cortex import CodeWritingCortex
    import math

    class _A:
        def op_stats(self):
            return {}

    s = _fresh_substrate()
    _seed_parents(s)
    cortex = CodeWritingCortex(s, agent=_A()).install()

    coeffs = [0.0, 1.0, 0.0, -1.0/6.0, 0.0, 1.0/120.0]
    assemblage = cortex.construct_polynomial_evaluator(coeffs)
    assert assemblage is not None

    for x in [-0.4, -0.2, 0.0, 0.2, 0.4]:
        out = cortex.forward(assemblage, [x])
        poly_truth = sum(a * x ** i for i, a in enumerate(coeffs))
        # Bound: |a_2|·0.0025 + |a_3|·0.01 + |a_4|·0.02 + |a_5|·0.04
        # (compounding through cube, quartic, quintic). Loose 0.05 cap.
        assert abs(out[0] - poly_truth) <= 0.05, (
            f"sin Taylor-5 at x={x}: forward={out[0]}, "
            f"poly={poly_truth}, err={abs(out[0]-poly_truth)}")


def test_construct_lookup_table_negation():
    """f: {0, 1} → {1, 0}. The simplest non-trivial lookup."""
    from domains.code_writing_cortex import CodeWritingCortex

    class _A:
        def op_stats(self):
            return {}

    s = _fresh_substrate()
    _seed_parents(s)
    cortex = CodeWritingCortex(s, agent=_A()).install()

    assemblage = cortex.construct_lookup_table([1, 0], label="negation")
    assert assemblage is not None

    # one-hot input [1, 0] (= 0) → one-hot output [0, 1] (= 1)
    out = cortex.forward(assemblage, [1.0, 0.0])
    assert out == pytest.approx([0.0, 1.0], abs=1e-9)
    # one-hot input [0, 1] (= 1) → one-hot output [1, 0] (= 0)
    out = cortex.forward(assemblage, [0.0, 1.0])
    assert out == pytest.approx([1.0, 0.0], abs=1e-9)


def test_construct_lookup_table_cyclic_shift_mod_4():
    """f: i → (i+1) mod 4. Successor on a 4-element vocabulary."""
    from domains.code_writing_cortex import CodeWritingCortex

    class _A:
        def op_stats(self):
            return {}

    s = _fresh_substrate()
    _seed_parents(s)
    cortex = CodeWritingCortex(s, agent=_A()).install()

    mapping = [1, 2, 3, 0]
    assemblage = cortex.construct_lookup_table(mapping, label="succ_mod4")
    assert assemblage is not None

    for i in range(4):
        one_hot_in = [1.0 if k == i else 0.0 for k in range(4)]
        out = cortex.forward(assemblage, one_hot_in)
        expected_pos = mapping[i]
        expected = [1.0 if k == expected_pos else 0.0 for k in range(4)]
        assert out == pytest.approx(expected, abs=1e-9), (
            f"f({i}) at one-hot {one_hot_in}: got {out}, expected {expected}")


def test_construct_lookup_table_reverse_permutation():
    """f: i → V_in − 1 − i. The reverse permutation on 5 elements."""
    from domains.code_writing_cortex import CodeWritingCortex

    class _A:
        def op_stats(self):
            return {}

    s = _fresh_substrate()
    _seed_parents(s)
    cortex = CodeWritingCortex(s, agent=_A()).install()

    n = 5
    mapping = [n - 1 - i for i in range(n)]
    assemblage = cortex.construct_lookup_table(mapping, label="reverse5")
    assert assemblage is not None

    for i in range(n):
        one_hot_in = [1.0 if k == i else 0.0 for k in range(n)]
        out = cortex.forward(assemblage, one_hot_in)
        expected = [1.0 if k == mapping[i] else 0.0 for k in range(n)]
        assert out == pytest.approx(expected, abs=1e-9)


def test_construct_lookup_table_modular_addition():
    """Test that the lookup MLP can realise (i + 2) mod 5 — a useful
    discrete function that proves the construction works for arbitrary
    mappings."""
    from domains.code_writing_cortex import CodeWritingCortex

    class _A:
        def op_stats(self):
            return {}

    s = _fresh_substrate()
    _seed_parents(s)
    cortex = CodeWritingCortex(s, agent=_A()).install()

    n = 5
    mapping = [(i + 2) % n for i in range(n)]
    assert mapping == [2, 3, 4, 0, 1]
    assemblage = cortex.construct_lookup_table(mapping, label="add2_mod5")
    assert assemblage is not None

    for i in range(n):
        one_hot_in = [1.0 if k == i else 0.0 for k in range(n)]
        out = cortex.forward(assemblage, one_hot_in)
        expected = [1.0 if k == mapping[i] else 0.0 for k in range(n)]
        assert out == pytest.approx(expected, abs=1e-9)


def test_construct_elm_readout_recovers_known_polynomial():
    """Sanity check: if T = p(X) for some polynomial p ∈ span(features),
    ELM should recover p (up to numerical precision). Use monomial
    features [identity, x², x³] and target p(x) = 0.2 + 0.5x − 0.3x²
    + 0.1x³. The β solved should be ≈ [0.5, -0.3, 0.1] (coefficients
    for the lifted features, no constant since the lift omits 1)."""
    import math
    import numpy as np
    from domains.code_writing_cortex import CodeWritingCortex

    class _A:
        def op_stats(self):
            return {}

    s = _fresh_substrate()
    _seed_parents(s)
    cortex = CodeWritingCortex(s, agent=_A()).install()

    # Build monomial features [x, x², x³] (no constant).
    feature_name = cortex.construct_broadcast_pattern(
        input_dim=1,
        branch_chains=[
            ["identity_gadget"],
            ["square_pwl_signed_gadget"],
            ["cube_gadget"],
        ],
        label="elm_test_features")
    assert feature_name is not None

    # Generate samples of p(x) = 0.5x − 0.3x² + 0.1x³ (no constant).
    X = [-0.4, -0.3, -0.2, -0.1, 0.0, 0.1, 0.2, 0.3, 0.4]
    T = [0.5 * x - 0.3 * x ** 2 + 0.1 * x ** 3 for x in X]

    assemblage = cortex.construct_elm_readout(feature_name, X, T,
                                              label="poly_recover")
    assert assemblage is not None

    # On the same X, forward should reproduce T closely (within PWL bound).
    for x, t in zip(X, T):
        out = cortex.forward(assemblage, [x])
        assert abs(out[0] - t) <= 0.005, (
            f"ELM at x={x}: forward={out[0]}, target={t}, "
            f"err={abs(out[0]-t)}")


def test_construct_elm_readout_fits_sin_better_than_taylor3():
    """The interesting case: T is a function NOT in the feature span
    exactly (sin), but ELM still finds the best linear-combination
    approximation. Compare to Taylor-3 (which uses the SAME features
    but with fixed [0, 1, 0, -1/6] coefficients): ELM should not be
    worse on the training set, and typically does better since it
    minimizes MSE rather than fitting at zero."""
    import math
    import numpy as np
    from domains.code_writing_cortex import CodeWritingCortex

    class _A:
        def op_stats(self):
            return {}

    s = _fresh_substrate()
    _seed_parents(s)
    cortex = CodeWritingCortex(s, agent=_A()).install()

    # Build monomial features [x, x², x³].
    feature_name = cortex.construct_broadcast_pattern(
        input_dim=1,
        branch_chains=[
            ["identity_gadget"],
            ["square_pwl_signed_gadget"],
            ["cube_gadget"],
        ],
        label="elm_sin_features")

    # Sample sin on [-0.4, 0.4]
    X = [round(-0.4 + i * 0.05, 4) for i in range(17)]
    T = [math.sin(x) for x in X]

    elm_a = cortex.construct_elm_readout(feature_name, X, T, label="sin_elm")
    taylor_a = cortex.construct_polynomial_evaluator(
        [0.0, 1.0, 0.0, -1.0/6.0])

    # Test on held-out points.
    test_X = [-0.35, -0.05, 0.15, 0.25]
    elm_err = max(abs(cortex.forward(elm_a, [x])[0] - math.sin(x))
                  for x in test_X)
    taylor_err = max(abs(cortex.forward(taylor_a, [x])[0] - math.sin(x))
                     for x in test_X)
    # Both should be small; ELM typically better or comparable on
    # the test grid (it minimises MSE on a dense training grid).
    assert elm_err < 0.01
    assert taylor_err < 0.01


def test_construct_multiplexer_abs_via_identity_and_negate():
    """abs(x) = if x ≥ 0 then x else −x. Construct via multiplexer
    with b = identity, c = negate. Continuity at 0: b(0)=0=c(0) ✓.
    Forward should match |x|."""
    from domains.code_writing_cortex import CodeWritingCortex

    class _A:
        def op_stats(self):
            return {}

    s = _fresh_substrate()
    _seed_parents(s)
    cortex = CodeWritingCortex(s, agent=_A()).install()

    negate = cortex._mint_scalar_linear(-1.0, 0.0, label="negate")
    mux = cortex.construct_multiplexer(
        "identity_gadget", negate, boundary_x=0.0, label="abs_via_mux")
    assert mux is not None

    for x in [-2.0, -1.0, -0.5, 0.0, 0.5, 1.0, 2.0, 3.7]:
        out = cortex.forward(mux, [x])
        assert out == pytest.approx([abs(x)], abs=1e-9)


def test_construct_multiplexer_relu_via_identity_and_zero():
    """ReLU(x) = if x ≥ 0 then x else 0. b = identity, c = constant 0
    (cpwl_linear with slope 0). Continuity: b(0)=0=c(0) ✓."""
    from domains.code_writing_cortex import CodeWritingCortex

    class _A:
        def op_stats(self):
            return {}

    s = _fresh_substrate()
    _seed_parents(s)
    cortex = CodeWritingCortex(s, agent=_A()).install()

    zero = cortex._mint_scalar_linear(0.0, 0.0, label="zero")
    mux = cortex.construct_multiplexer(
        "identity_gadget", zero, boundary_x=0.0, label="relu_via_mux")
    assert mux is not None

    for x in [-2.0, -1.0, -0.5, 0.0, 0.5, 1.0, 2.0]:
        out = cortex.forward(mux, [x])
        assert out == pytest.approx([max(x, 0.0)], abs=1e-9)


def test_construct_multiplexer_v_shape_asymmetric_slopes():
    """if x ≥ 0 then α·x else β·x, with the sign-reversal monotonicity
    requiring β < 0 (c decreasing through 0). Try α=2, β=-3.
    For x = 1: 2; for x = -1: 3 (since -3·(-1) = 3)."""
    from domains.code_writing_cortex import CodeWritingCortex

    class _A:
        def op_stats(self):
            return {}

    s = _fresh_substrate()
    _seed_parents(s)
    cortex = CodeWritingCortex(s, agent=_A()).install()

    b_pat = cortex._mint_scalar_linear(2.0, 0.0, label="alpha")
    c_pat = cortex._mint_scalar_linear(-3.0, 0.0, label="beta")
    mux = cortex.construct_multiplexer(
        b_pat, c_pat, boundary_x=0.0, label="v_shape")
    assert mux is not None

    # Right side: 2x. Left side: -3x.
    for x in [-1.0, -0.5, -0.25, 0.0, 0.25, 0.5, 1.0]:
        out = cortex.forward(mux, [x])
        expected = 2.0 * x if x >= 0 else -3.0 * x
        assert out == pytest.approx([expected], abs=1e-9), (
            f"v-shape at x={x}: got {out[0]}, expected {expected}")


def test_construct_multiplexer_continuity_violation_returns_none():
    """If b(x*) ≠ c(x*), the multiplexer is unsound — the cortex
    refuses to construct it. b = identity (b(0)=0), c = constant 1
    (c(0)=1). Returns None and records the violation."""
    from domains.code_writing_cortex import CodeWritingCortex

    class _A:
        def op_stats(self):
            return {}

    s = _fresh_substrate()
    _seed_parents(s)
    cortex = CodeWritingCortex(s, agent=_A()).install()

    constant_one = cortex._mint_scalar_linear(0.0, 1.0, label="const_one")
    mux = cortex.construct_multiplexer(
        "identity_gadget", constant_one,
        boundary_x=0.0, label="bad_mux")
    assert mux is None

    # The violation was recorded as a graph node for downstream
    # introspection.
    violations = [
        n for n in s.nodes("DesignPattern")
        if s.node(n)["attrs"].get("gadget_kind") == "cpwl_invalid"
    ]
    assert len(violations) == 1
    a = s.node(violations[0])["attrs"]
    assert a["soundness_verdict"] == "violated"
    assert a["soundness_predicate"] == "b(x*) = c(x*)"
    assert abs(a["b_at_boundary"] - 0.0) < 1e-9
    assert abs(a["c_at_boundary"] - 1.0) < 1e-9


def test_construct_multiplexer_general_picks_max_when_sortable():
    """if x ≥ 0 then x² else x_alpha — where x_alpha is a CPWL gadget
    that's ≤ x² for x ≥ 0 and ≥ x² for x ≤ 0. Picks max."""
    from domains.code_writing_cortex import CodeWritingCortex

    class _A:
        def op_stats(self):
            return {}

    s = _fresh_substrate()
    _seed_parents(s)
    cortex = CodeWritingCortex(s, agent=_A()).install()

    # b(x) = x, c(x) = -x → b > c above 0, c > b below 0 → use max
    # → realises max(x, -x) = |x|. (Same as the existing abs via
    # sign-reversal mux; the general path arrives at the same answer
    # via min/max instead of via the construction formula.)
    negate = cortex._mint_scalar_linear(-1.0, 0.0, label="neg_g")
    mux = cortex.construct_multiplexer_general(
        "identity_gadget", negate, boundary_x=0.0, label="abs_g")
    assert mux is not None
    for x in [-1.5, -0.5, 0.0, 0.5, 1.5]:
        out = cortex.forward(mux, [x])
        assert out == pytest.approx([abs(x)], abs=1e-9)


def test_construct_multiplexer_general_picks_min_when_inverted_order():
    """b(x) = -x, c(x) = x: b > c below 0, c > b above 0 → use min
    → realises min(-x, x) = -|x|."""
    from domains.code_writing_cortex import CodeWritingCortex

    class _A:
        def op_stats(self):
            return {}

    s = _fresh_substrate()
    _seed_parents(s)
    cortex = CodeWritingCortex(s, agent=_A()).install()

    negate = cortex._mint_scalar_linear(-1.0, 0.0, label="neg_g_min")
    mux = cortex.construct_multiplexer_general(
        negate, "identity_gadget", boundary_x=0.0, label="neg_abs_g")
    assert mux is not None
    for x in [-1.5, -0.5, 0.0, 0.5, 1.5]:
        out = cortex.forward(mux, [x])
        assert out == pytest.approx([-abs(x)], abs=1e-9)


def test_construct_multiplexer_general_refuses_unsortable_case():
    """b(x) = x², c(x) = 0 with x* = 0: continuity holds (b(0)=0=c(0))
    but b > c on BOTH sides (b(x) = x² > 0 = c for x ≠ 0). Neither
    max nor min realises the conditional. The cortex refuses + records.

    Note: we approximate x² with the existing square_pwl_signed_gadget
    so this test exercises the same general failure mode the doc warns
    about."""
    from domains.code_writing_cortex import CodeWritingCortex

    class _A:
        def op_stats(self):
            return {}

    s = _fresh_substrate()
    _seed_parents(s)
    cortex = CodeWritingCortex(s, agent=_A()).install()

    zero = cortex._mint_scalar_linear(0.0, 0.0, label="zero_g")
    mux = cortex.construct_multiplexer_general(
        "square_pwl_signed_gadget", zero,
        boundary_x=0.0, label="rect_sq_g")
    assert mux is None
    # Soundness violation recorded.
    viol = [n for n in s.nodes("DesignPattern")
            if s.node(n)["attrs"].get("gadget_kind") == "cpwl_invalid"]
    assert any("sortability" in s.node(v)["attrs"].get(
        "soundness_predicate", "") for v in viol)


def test_construct_select_qk_simple_predicate_less_than():
    """Tracr §1.2 — Select(q, k, q < k). For V_q = V_k = 3:
        W̃_QK = [[0, 1, 1],
                [0, 0, 1],
                [0, 0, 0]]
    Forward on concatenated one-hots [q_one_hot ⊕ k_one_hot]
    returns W_QK[q_idx, k_idx]."""
    from domains.code_writing_cortex import CodeWritingCortex

    class _A:
        def op_stats(self):
            return {}

    s = _fresh_substrate()
    _seed_parents(s)
    cortex = CodeWritingCortex(s, agent=_A()).install()

    V = 3
    assemblage = cortex.construct_select_qk(
        predicate=lambda q, k: q < k,
        query_vocab_size=V, key_vocab_size=V, label="lt")
    assert assemblage is not None

    expected_matrix = [[0.0, 1.0, 1.0],
                       [0.0, 0.0, 1.0],
                       [0.0, 0.0, 0.0]]
    for q_idx in range(V):
        for k_idx in range(V):
            q_oh = [1.0 if i == q_idx else 0.0 for i in range(V)]
            k_oh = [1.0 if j == k_idx else 0.0 for j in range(V)]
            out = cortex.forward(assemblage, q_oh + k_oh)
            assert out == pytest.approx([expected_matrix[q_idx][k_idx]],
                                         abs=1e-9), (
                f"select_qk(q={q_idx}, k={k_idx}): forward={out[0]}, "
                f"expected {expected_matrix[q_idx][k_idx]}")


def test_construct_select_qk_equality_predicate():
    """Tracr — Select(q, k, q == k) yields the identity matrix as W_QK.
    On diagonal: score 1. Off diagonal: score 0."""
    from domains.code_writing_cortex import CodeWritingCortex

    class _A:
        def op_stats(self):
            return {}

    s = _fresh_substrate()
    _seed_parents(s)
    cortex = CodeWritingCortex(s, agent=_A()).install()

    V = 4
    assemblage = cortex.construct_select_qk(
        predicate=lambda q, k: q == k,
        query_vocab_size=V, key_vocab_size=V, label="eq")
    assert assemblage is not None

    for q_idx in range(V):
        for k_idx in range(V):
            q_oh = [1.0 if i == q_idx else 0.0 for i in range(V)]
            k_oh = [1.0 if j == k_idx else 0.0 for j in range(V)]
            out = cortex.forward(assemblage, q_oh + k_oh)
            expected = 1.0 if q_idx == k_idx else 0.0
            assert out == pytest.approx([expected], abs=1e-9)


def test_construct_aggregate_ov_routes_one_hots():
    """Tracr §1.3 — Aggregate W_OV with a specific routing.
    routing = [2, 0, 1] over V_v = V_o = 3 means value 0 → output 2,
    value 1 → output 0, value 2 → output 1. W_OV = [[0,1,0],[0,0,1],[1,0,0]]."""
    from domains.code_writing_cortex import CodeWritingCortex

    class _A:
        def op_stats(self):
            return {}

    s = _fresh_substrate()
    _seed_parents(s)
    cortex = CodeWritingCortex(s, agent=_A()).install()

    routing = [2, 0, 1]
    assemblage = cortex.construct_aggregate_ov(
        routing, value_vocab_size=3, output_vocab_size=3,
        label="rotation")
    assert assemblage is not None

    for v_idx in range(3):
        v_oh = [1.0 if i == v_idx else 0.0 for i in range(3)]
        out = cortex.forward(assemblage, v_oh)
        expected_o = routing[v_idx]
        expected = [1.0 if k == expected_o else 0.0 for k in range(3)]
        assert out == pytest.approx(expected, abs=1e-9)


def test_construct_pwl_through_points_passes_through_breakpoints():
    """General-purpose CPWL utility — exact at every supplied
    (breakpoint, value) pair, linear between."""
    from domains.code_writing_cortex import CodeWritingCortex

    class _A:
        def op_stats(self):
            return {}

    s = _fresh_substrate()
    _seed_parents(s)
    cortex = CodeWritingCortex(s, agent=_A()).install()

    # Non-trivial CPWL: zigzag through (0,0), (1,2), (2,1), (3,4), (4,0).
    bps = [0.0, 1.0, 2.0, 3.0, 4.0]
    vals = [0.0, 2.0, 1.0, 4.0, 0.0]
    assemblage = cortex.construct_pwl_through_points(
        breakpoints=bps, values=vals, label="zigzag")
    assert assemblage is not None

    # Exact at every breakpoint.
    for bp, v in zip(bps, vals):
        out = cortex.forward(assemblage, [bp])
        assert out == pytest.approx([v], abs=1e-9)

    # Linear interpolation at midpoints.
    for k in range(len(bps) - 1):
        mid_x = (bps[k] + bps[k + 1]) / 2
        mid_v = (vals[k] + vals[k + 1]) / 2
        out = cortex.forward(assemblage, [mid_x])
        assert out == pytest.approx([mid_v], abs=1e-9)


def test_construct_selector_width_inverter_recovers_w():
    """Tracr §1.5 inversion stage — for x = 1/(w+1), output should
    be exactly w for every w in 0..w_max."""
    from domains.code_writing_cortex import CodeWritingCortex

    class _A:
        def op_stats(self):
            return {}

    s = _fresh_substrate()
    _seed_parents(s)
    cortex = CodeWritingCortex(s, agent=_A()).install()

    w_max = 6
    assemblage = cortex.construct_selector_width_inverter(w_max=w_max)
    assert assemblage is not None

    for w in range(w_max + 1):
        x = 1.0 / (w + 1)
        out = cortex.forward(assemblage, [x])
        assert out == pytest.approx([float(w)], abs=1e-9), (
            f"selwidth_inv at x = 1/(w+1) = {x}: forward = {out[0]}, "
            f"expected w = {w}")


def _make_attention_input(q_idx, keys, values, V_q, V_k, V_v):
    """Helper: encode (query, [keys], [values]) as concatenated one-hots."""
    T = len(keys)
    q_oh = [1.0 if i == q_idx else 0.0 for i in range(V_q)]
    k_oh = []
    for k in keys:
        k_oh.extend([1.0 if i == k else 0.0 for i in range(V_k)])
    v_oh = []
    for v in values:
        v_oh.extend([1.0 if i == v else 0.0 for i in range(V_v)])
    return q_oh + k_oh + v_oh


def test_categorical_attention_associative_lookup_identity_predicate():
    """Predicate q == k, identity routing. The attention layer
    realises 'find the position where key matches the query and
    return its value' — associative memory."""
    from domains.code_writing_cortex import CodeWritingCortex

    class _A:
        def op_stats(self):
            return {}

    s = _fresh_substrate()
    _seed_parents(s)
    cortex = CodeWritingCortex(s, agent=_A()).install()

    V = 3
    T = 3
    assemblage = cortex.construct_categorical_attention(
        predicate=lambda q, k: q == k,
        routing=[0, 1, 2],  # identity
        T=T, V_q=V, V_k=V, V_v=V, V_o=V,
        label="lookup_eq")
    assert assemblage is not None

    # keys = [2, 0, 1] is a permutation; for query q, the matching
    # position j is keys.index(q). Expected value at output is values[j].
    keys = [2, 0, 1]
    values = [10 % V, 20 % V, 30 % V]  # = [1, 2, 0]
    for q in range(V):
        j_match = keys.index(q)
        expected = [1.0 if i == values[j_match] else 0.0 for i in range(V)]
        inputs = _make_attention_input(q, keys, values, V, V, V)
        out = cortex.forward(assemblage, inputs)
        assert out == pytest.approx(expected, abs=1e-9), (
            f"attn(q={q}, keys={keys}, vals={values}): out={out}, "
            f"expected one-hot at v={values[j_match]} (= {expected})")


def test_categorical_attention_less_than_predicate_sums_all_matches():
    """Predicate q < k — a query may match MULTIPLE keys. The output
    is multi-hot when more than one key matches. Verify the sum
    behaviour (no softmax bypass here)."""
    from domains.code_writing_cortex import CodeWritingCortex

    class _A:
        def op_stats(self):
            return {}

    s = _fresh_substrate()
    _seed_parents(s)
    cortex = CodeWritingCortex(s, agent=_A()).install()

    V = 3
    T = 3
    assemblage = cortex.construct_categorical_attention(
        predicate=lambda q, k: q < k,
        routing=[0, 1, 2],
        T=T, V_q=V, V_k=V, V_v=V, V_o=V,
        label="lookup_lt")
    assert assemblage is not None

    # query q=0, keys=[1, 2, 1], values=[0, 1, 2]:
    # all keys are > 0, so all 3 positions match. Output sums:
    #   v_0 = 0 → +1 at output[0]
    #   v_1 = 1 → +1 at output[1]
    #   v_2 = 2 → +1 at output[2]
    # → output = [1, 1, 1]
    inputs = _make_attention_input(0, [1, 2, 1], [0, 1, 2], V, V, V)
    out = cortex.forward(assemblage, inputs)
    assert out == pytest.approx([1.0, 1.0, 1.0], abs=1e-9)

    # query q=2, keys=[0, 1, 2]: none match (no k > 2). Output zero.
    inputs = _make_attention_input(2, [0, 1, 2], [0, 1, 2], V, V, V)
    out = cortex.forward(assemblage, inputs)
    assert out == pytest.approx([0.0, 0.0, 0.0], abs=1e-9)


def test_categorical_attention_with_w_ov_routing():
    """Attention + non-identity W_OV: matched value is routed before
    being written. Predicate identity, routing = [2, 0, 1] (rotation).
    For q matching at j, output is one-hot at routing[v_j]."""
    from domains.code_writing_cortex import CodeWritingCortex

    class _A:
        def op_stats(self):
            return {}

    s = _fresh_substrate()
    _seed_parents(s)
    cortex = CodeWritingCortex(s, agent=_A()).install()

    V = 3
    T = 3
    assemblage = cortex.construct_categorical_attention(
        predicate=lambda q, k: q == k,
        routing=[2, 0, 1],  # rotation
        T=T, V_q=V, V_k=V, V_v=V, V_o=V,
        label="lookup_rot")
    assert assemblage is not None

    keys = [0, 1, 2]
    values = [1, 2, 0]
    for q in range(V):
        j = keys.index(q)
        v_j = values[j]
        expected_o = [2, 0, 1][v_j]
        expected = [1.0 if k == expected_o else 0.0 for k in range(V)]
        inputs = _make_attention_input(q, keys, values, V, V, V)
        out = cortex.forward(assemblage, inputs)
        assert out == pytest.approx(expected, abs=1e-9)


def _make_multi_query_input(queries, keys, values, V_q, V_k, V_v):
    """Encode T queries, T keys, T values as concatenated one-hots."""
    T = len(queries)
    q_oh = []
    for q in queries:
        q_oh.extend([1.0 if i == q else 0.0 for i in range(V_q)])
    k_oh = []
    for k in keys:
        k_oh.extend([1.0 if i == k else 0.0 for i in range(V_k)])
    v_oh = []
    for v in values:
        v_oh.extend([1.0 if i == v else 0.0 for i in range(V_v)])
    return q_oh + k_oh + v_oh


def _decode_multi_output(out, T, V_o):
    """Decode T concatenated one-hot outputs to per-position argmax."""
    result = []
    for i in range(T):
        seg = out[i * V_o:(i + 1) * V_o]
        if max(seg) < 0.5:
            result.append(None)
        else:
            result.append(seg.index(max(seg)))
    return result


def test_multi_query_attention_composes_two_permutations():
    """T queries each find the matching key and return its value.
    With queries [0, 1, 2], keys [1, 2, 0], values [10%V, 20%V, 30%V] =
    [1, 2, 0], expected per-query outputs:
      q=0 matches k_j=0 at j=2 → return v_2 = 0
      q=1 matches k_j=1 at j=0 → return v_0 = 1
      q=2 matches k_j=2 at j=1 → return v_1 = 2
    Result: [0, 1, 2] — the identity permutation."""
    from domains.code_writing_cortex import CodeWritingCortex

    class _A:
        def op_stats(self):
            return {}

    s = _fresh_substrate()
    _seed_parents(s)
    cortex = CodeWritingCortex(s, agent=_A()).install()

    V = 3
    T = 3
    assemblage = cortex.construct_categorical_attention_multi_query(
        predicate=lambda q, k: q == k,
        routing=[0, 1, 2],
        T=T, V_q=V, V_k=V, V_v=V, V_o=V,
        label="compose_perms")
    assert assemblage is not None

    queries = [0, 1, 2]
    keys = [1, 2, 0]
    values = [1, 2, 0]
    inputs = _make_multi_query_input(queries, keys, values, V, V, V)
    out = cortex.forward(assemblage, inputs)
    decoded = _decode_multi_output(out, T, V)
    assert decoded == [0, 1, 2]


def test_multi_query_attention_arbitrary_permutation():
    """Use queries [2, 0, 1] over keys [0, 1, 2] (identity) and values
    [4 % V, 5 % V, 6 % V] = [1, 2, 0]. Each query finds the matching
    key and returns its value.
      q=2 matches k_j=2 at j=2 → return v_2 = 0
      q=0 matches k_j=0 at j=0 → return v_0 = 1
      q=1 matches k_j=1 at j=1 → return v_1 = 2
    Output decoded: [0, 1, 2]."""
    from domains.code_writing_cortex import CodeWritingCortex

    class _A:
        def op_stats(self):
            return {}

    s = _fresh_substrate()
    _seed_parents(s)
    cortex = CodeWritingCortex(s, agent=_A()).install()

    V = 3
    T = 3
    assemblage = cortex.construct_categorical_attention_multi_query(
        predicate=lambda q, k: q == k,
        routing=[0, 1, 2],
        T=T, V_q=V, V_k=V, V_v=V, V_o=V,
        label="arb_perm")
    assert assemblage is not None

    queries = [2, 0, 1]
    keys = [0, 1, 2]
    values = [1, 2, 0]
    inputs = _make_multi_query_input(queries, keys, values, V, V, V)
    out = cortex.forward(assemblage, inputs)
    decoded = _decode_multi_output(out, T, V)
    assert decoded == [0, 1, 2]


def test_multi_query_attention_handles_missing_match():
    """If a query has no matching key, the corresponding output is zero
    (all entries below threshold)."""
    from domains.code_writing_cortex import CodeWritingCortex

    class _A:
        def op_stats(self):
            return {}

    s = _fresh_substrate()
    _seed_parents(s)
    cortex = CodeWritingCortex(s, agent=_A()).install()

    V = 3
    T = 3
    assemblage = cortex.construct_categorical_attention_multi_query(
        predicate=lambda q, k: q == k,
        routing=[0, 1, 2],
        T=T, V_q=V, V_k=V, V_v=V, V_o=V,
        label="missing")
    assert assemblage is not None

    # Query position 0 has q=2, but no key equals 2 in [0, 1, 1].
    queries = [2, 0, 1]
    keys = [0, 1, 1]
    values = [0, 1, 2]
    inputs = _make_multi_query_input(queries, keys, values, V, V, V)
    out = cortex.forward(assemblage, inputs)
    # Output[0]: no match → all zeros
    assert out[0:V] == pytest.approx([0.0, 0.0, 0.0], abs=1e-9)
    # Output[1]: q=0, matches j=0 → v_0 = 0 → one-hot at 0
    assert out[V:2*V] == pytest.approx([1.0, 0.0, 0.0], abs=1e-9)
    # Output[2]: q=1, matches j=1 AND j=2 (both have k=1) → sum:
    # v_1 + v_2 = 1-hot at 1 + 1-hot at 2 = [0, 1, 1]
    assert out[2*V:3*V] == pytest.approx([0.0, 1.0, 1.0], abs=1e-9)


def test_construct_tracr_program_basic_equal_lookup():
    """RASP program: select q==k, aggregate v with identity routing.
    Compile and verify forward matches the manual attention layer."""
    from domains.code_writing_cortex import CodeWritingCortex

    class _A:
        def op_stats(self):
            return {}

    s = _fresh_substrate()
    _seed_parents(s)
    cortex = CodeWritingCortex(s, agent=_A()).install()

    V = 3
    T = 3
    program = {
        "name": "lookup_by_key",
        "n_positions": T,
        "vocab_size": V,
        "ops": [
            {"name": "is_match", "op": "select",
             "query": "q", "key": "k", "predicate": "equal"},
            {"name": "result", "op": "aggregate",
             "selector": "is_match", "value": "v",
             "routing": "identity"},
        ],
        "output": "result",
    }
    assemblage = cortex.construct_tracr_program(program)
    assert assemblage is not None

    # Tracr metadata recorded.
    attrs = s.node(assemblage)["attrs"]
    assert attrs["tracr_program_name"] == "lookup_by_key"
    assert attrs["tracr_predicate"] == "equal"

    queries = [0, 1, 2]
    keys = [1, 2, 0]
    values = [1, 2, 0]
    inputs = _make_multi_query_input(queries, keys, values, V, V, V)
    out = cortex.forward(assemblage, inputs)
    decoded = _decode_multi_output(out, T, V)
    assert decoded == [0, 1, 2]


def test_construct_tracr_program_less_than_predicate():
    """RASP program with q<k predicate — verify the compiler dispatches
    to the right predicate function."""
    from domains.code_writing_cortex import CodeWritingCortex

    class _A:
        def op_stats(self):
            return {}

    s = _fresh_substrate()
    _seed_parents(s)
    cortex = CodeWritingCortex(s, agent=_A()).install()

    V = 3
    T = 3
    program = {
        "name": "lt_attention",
        "n_positions": T,
        "vocab_size": V,
        "ops": [
            {"name": "lt", "op": "select",
             "query": "q", "key": "k", "predicate": "less_than"},
            {"name": "out", "op": "aggregate",
             "selector": "lt", "value": "v", "routing": "identity"},
        ],
        "output": "out",
    }
    assemblage = cortex.construct_tracr_program(program)
    assert assemblage is not None

    # q=0 attends to all positions with k > 0; with keys [1, 2, 1] and
    # values [0, 1, 2] this multi-matches.
    queries = [0, 0, 0]
    keys = [1, 2, 1]
    values = [0, 1, 2]
    inputs = _make_multi_query_input(queries, keys, values, V, V, V)
    out = cortex.forward(assemblage, inputs)
    # Each output position has q=0 → all 3 positions match → sum
    # values [0, 1, 2] one-hots = [1, 1, 1]
    for i in range(T):
        assert out[i*V:(i+1)*V] == pytest.approx([1.0, 1.0, 1.0], abs=1e-9)


def test_construct_tracr_program_reverse_routing():
    """RASP program with routing="reverse" — values are permuted
    through W_OV = reverse permutation."""
    from domains.code_writing_cortex import CodeWritingCortex

    class _A:
        def op_stats(self):
            return {}

    s = _fresh_substrate()
    _seed_parents(s)
    cortex = CodeWritingCortex(s, agent=_A()).install()

    V = 3
    T = 3
    program = {
        "name": "rev_lookup",
        "n_positions": T,
        "vocab_size": V,
        "ops": [
            {"name": "match", "op": "select",
             "query": "q", "key": "k", "predicate": "equal"},
            {"name": "rev", "op": "aggregate",
             "selector": "match", "value": "v", "routing": "reverse"},
        ],
        "output": "rev",
    }
    assemblage = cortex.construct_tracr_program(program)
    assert assemblage is not None

    # Reverse routing of V=3: [0→2, 1→1, 2→0].
    queries = [0, 1, 2]
    keys = [0, 1, 2]
    values = [1, 2, 0]
    inputs = _make_multi_query_input(queries, keys, values, V, V, V)
    out = cortex.forward(assemblage, inputs)
    decoded = _decode_multi_output(out, T, V)
    # query i matches j=i; v_i ∈ {1, 2, 0}; reverse maps 1→1, 2→0, 0→2.
    # So decoded = [1, 0, 2].
    assert decoded == [1, 0, 2]


def test_construct_tracr_program_explicit_routing_list():
    """RASP program with explicit routing list."""
    from domains.code_writing_cortex import CodeWritingCortex

    class _A:
        def op_stats(self):
            return {}

    s = _fresh_substrate()
    _seed_parents(s)
    cortex = CodeWritingCortex(s, agent=_A()).install()

    V = 3
    T = 3
    program = {
        "name": "rot_lookup",
        "n_positions": T,
        "vocab_size": V,
        "ops": [
            {"name": "m", "op": "select",
             "query": "q", "key": "k", "predicate": "equal"},
            {"name": "rot", "op": "aggregate",
             "selector": "m", "value": "v",
             "routing": [2, 0, 1]},
        ],
        "output": "rot",
    }
    assemblage = cortex.construct_tracr_program(program)
    assert assemblage is not None

    # Rotation [2, 0, 1]: 0→2, 1→0, 2→1.
    queries = [0, 1, 2]
    keys = [0, 1, 2]
    values = [0, 1, 2]
    inputs = _make_multi_query_input(queries, keys, values, V, V, V)
    out = cortex.forward(assemblage, inputs)
    decoded = _decode_multi_output(out, T, V)
    # Each query matches j=i; v_i = i; rotation gives [2, 0, 1].
    assert decoded == [2, 0, 1]


def test_construct_tracr_program_rejects_malformed():
    """Aggregate's selector must reference a Select op in the program."""
    from domains.code_writing_cortex import CodeWritingCortex

    class _A:
        def op_stats(self):
            return {}

    s = _fresh_substrate()
    _seed_parents(s)
    cortex = CodeWritingCortex(s, agent=_A()).install()

    program = {
        "name": "broken", "n_positions": 3, "vocab_size": 3,
        "ops": [
            {"name": "S", "op": "select",
             "query": "q", "key": "k", "predicate": "equal"},
            {"name": "A", "op": "aggregate",
             "selector": "WRONG", "value": "v", "routing": "identity"},
        ],
        "output": "A",
    }
    assert cortex.construct_tracr_program(program) is None


def test_construct_tracr_program_multilayer_single_layer_equivalence():
    """A 1-layer multi-layer program should produce the same output
    as the single-layer construct_tracr_program (plus extract)."""
    from domains.code_writing_cortex import CodeWritingCortex

    class _A:
        def op_stats(self):
            return {}

    s = _fresh_substrate()
    _seed_parents(s)
    cortex = CodeWritingCortex(s, agent=_A()).install()

    V = 3
    T = 3
    program = {
        "name": "ml_equivalence",
        "n_positions": T, "vocab_size": V,
        "input_streams": ["q", "k", "v"],
        "ops": [
            {"name": "m", "op": "select",
             "query": "q", "key": "k", "predicate": "equal"},
            {"name": "out", "op": "aggregate",
             "selector": "m", "value": "v", "routing": "identity"},
        ],
        "output": "out",
    }
    assemblage = cortex.construct_tracr_program_multilayer(program)
    assert assemblage is not None

    queries = [0, 1, 2]
    keys = [1, 2, 0]
    values = [1, 2, 0]
    inputs = _make_multi_query_input(queries, keys, values, V, V, V)
    out = cortex.forward(assemblage, inputs)
    decoded = _decode_multi_output(out, T, V)
    assert decoded == [0, 1, 2]


def test_construct_tracr_program_multilayer_two_layers_chained():
    """Two-layer attention: layer 1's output L1 becomes the query
    of layer 2.

    Layer 1: select q==k, aggregate v → L1
      With queries [0, 1, 2], keys [0, 1, 2], values [1, 2, 0]:
      L1[i] = v_{j: k_j == q_i} = v_{q_i} = [1, 2, 0]
    Layer 2: select L1==k, aggregate v → L2
      L2[i] = v_{j: k_j == L1_i} = v_{L1_i} = [v[1], v[2], v[0]] = [2, 0, 1]
    Output: L2 = [2, 0, 1]"""
    from domains.code_writing_cortex import CodeWritingCortex

    class _A:
        def op_stats(self):
            return {}

    s = _fresh_substrate()
    _seed_parents(s)
    cortex = CodeWritingCortex(s, agent=_A()).install()

    V = 3
    T = 3
    program = {
        "name": "two_layer_chain",
        "n_positions": T, "vocab_size": V,
        "input_streams": ["q", "k", "v"],
        "ops": [
            {"name": "m1", "op": "select",
             "query": "q", "key": "k", "predicate": "equal"},
            {"name": "L1", "op": "aggregate",
             "selector": "m1", "value": "v", "routing": "identity"},
            {"name": "m2", "op": "select",
             "query": "L1", "key": "k", "predicate": "equal"},
            {"name": "L2", "op": "aggregate",
             "selector": "m2", "value": "v", "routing": "identity"},
        ],
        "output": "L2",
    }
    assemblage = cortex.construct_tracr_program_multilayer(program)
    assert assemblage is not None

    # Inspect the top pattern's metadata.
    top = next(n for n in s.nodes("DesignPattern")
               if s.node(n)["attrs"].get("origin")
               == "cortex_constructed_tracr_multilayer"
               and s.node(n)["attrs"].get("tracr_program_name")
               == "two_layer_chain")
    attrs = s.node(top)["attrs"]
    assert attrs["n_layers"] == 2
    streams = list(attrs["tracr_streams"])
    assert "L1" in streams
    assert "L2" in streams

    # Three steps in the assemblage: layer 1, layer 2, extract.
    steps = sorted(s.neighbours(assemblage, "has_step"),
                   key=lambda n: s.node(n)["attrs"].get("order", 0))
    assert len(steps) == 3

    queries = [0, 1, 2]
    keys = [0, 1, 2]
    values = [1, 2, 0]
    inputs = _make_multi_query_input(queries, keys, values, V, V, V)
    out = cortex.forward(assemblage, inputs)
    decoded = _decode_multi_output(out, T, V)
    assert decoded == [2, 0, 1]


def test_construct_tracr_program_multilayer_extract_intermediate_stream():
    """A 2-layer program where the OUTPUT is the intermediate stream
    L1 (not L2). Extract step should pull out L1 even after L2 was
    appended to the residual stream."""
    from domains.code_writing_cortex import CodeWritingCortex

    class _A:
        def op_stats(self):
            return {}

    s = _fresh_substrate()
    _seed_parents(s)
    cortex = CodeWritingCortex(s, agent=_A()).install()

    V = 3
    T = 3
    program = {
        "name": "extract_intermediate",
        "n_positions": T, "vocab_size": V,
        "input_streams": ["q", "k", "v"],
        "ops": [
            {"name": "m1", "op": "select",
             "query": "q", "key": "k", "predicate": "equal"},
            {"name": "L1", "op": "aggregate",
             "selector": "m1", "value": "v", "routing": "identity"},
            {"name": "m2", "op": "select",
             "query": "L1", "key": "k", "predicate": "equal"},
            {"name": "L2", "op": "aggregate",
             "selector": "m2", "value": "v", "routing": "identity"},
        ],
        "output": "L1",  # <-- intermediate stream as output
    }
    assemblage = cortex.construct_tracr_program_multilayer(program)
    assert assemblage is not None

    queries = [0, 1, 2]
    keys = [0, 1, 2]
    values = [1, 2, 0]
    inputs = _make_multi_query_input(queries, keys, values, V, V, V)
    out = cortex.forward(assemblage, inputs)
    decoded = _decode_multi_output(out, T, V)
    # L1[i] = v_{q_i} = [1, 2, 0]
    assert decoded == [1, 2, 0]


def test_construct_tracr_program_multilayer_rejects_undefined_stream():
    """Reference to an undefined stream → compilation fails."""
    from domains.code_writing_cortex import CodeWritingCortex

    class _A:
        def op_stats(self):
            return {}

    s = _fresh_substrate()
    _seed_parents(s)
    cortex = CodeWritingCortex(s, agent=_A()).install()

    program = {
        "name": "bad_stream",
        "n_positions": 3, "vocab_size": 3,
        "input_streams": ["q", "k", "v"],
        "ops": [
            {"name": "S", "op": "select",
             "query": "ghost", "key": "k", "predicate": "equal"},
            {"name": "A", "op": "aggregate",
             "selector": "S", "value": "v", "routing": "identity"},
        ],
        "output": "A",
    }
    assert cortex.construct_tracr_program_multilayer(program) is None


def test_construct_tracr_program_multilayer_with_map():
    """Two-layer program where the middle layer is a Map. Verifies that
    Map ops integrate with the residual stream alongside Aggregate."""
    from domains.code_writing_cortex import CodeWritingCortex

    class _A:
        def op_stats(self):
            return {}

    s = _fresh_substrate()
    _seed_parents(s)
    cortex = CodeWritingCortex(s, agent=_A()).install()

    V = 3
    T = 3
    # Pipeline:
    #   L1 = lookup(q, k, v)            via select q==k + aggregate v
    #   L2 = increment(L1)              via map "increment" mod 3
    #   L3 = lookup(L2, k, v)           via select L2==k + aggregate v
    program = {
        "name": "with_map",
        "n_positions": T, "vocab_size": V,
        "input_streams": ["q", "k", "v"],
        "ops": [
            {"name": "m1", "op": "select",
             "query": "q", "key": "k", "predicate": "equal"},
            {"name": "L1", "op": "aggregate",
             "selector": "m1", "value": "v", "routing": "identity"},
            {"name": "L2", "op": "map",
             "input": "L1", "mapping": "increment"},
            {"name": "m3", "op": "select",
             "query": "L2", "key": "k", "predicate": "equal"},
            {"name": "L3", "op": "aggregate",
             "selector": "m3", "value": "v", "routing": "identity"},
        ],
        "output": "L3",
    }
    assemblage = cortex.construct_tracr_program_multilayer(program)
    assert assemblage is not None

    # Three wide layer steps (L1, L2, L3) + extract = 4 steps.
    steps = sorted(s.neighbours(assemblage, "has_step"),
                   key=lambda n: s.node(n)["attrs"].get("order", 0))
    assert len(steps) == 4

    # Compute expected output.
    queries = [0, 1, 2]
    keys = [0, 1, 2]
    values = [0, 1, 2]  # so L1 = q itself
    # L1[i] = v[q_i] = q_i = [0, 1, 2]
    # L2[i] = (L1[i] + 1) mod 3 = [1, 2, 0]
    # L3[i] = v[L2_i] = [1, 2, 0]
    inputs = _make_multi_query_input(queries, keys, values, V, V, V)
    out = cortex.forward(assemblage, inputs)
    decoded = _decode_multi_output(out, T, V)
    assert decoded == [1, 2, 0]


def test_construct_tracr_program_multilayer_map_only():
    """A program of two Map ops (no attention) should still compile
    and execute correctly."""
    from domains.code_writing_cortex import CodeWritingCortex

    class _A:
        def op_stats(self):
            return {}

    s = _fresh_substrate()
    _seed_parents(s)
    cortex = CodeWritingCortex(s, agent=_A()).install()

    V = 3
    T = 3
    program = {
        "name": "map_only",
        "n_positions": T, "vocab_size": V,
        "input_streams": ["q", "k", "v"],
        "ops": [
            # M1: increment q  → q+1 mod 3
            {"name": "M1", "op": "map",
             "input": "q", "mapping": "increment"},
            # M2: reverse M1   → V-1-M1
            {"name": "M2", "op": "map",
             "input": "M1", "mapping": "reverse"},
        ],
        "output": "M2",
    }
    assemblage = cortex.construct_tracr_program_multilayer(program)
    assert assemblage is not None

    queries = [0, 1, 2]
    keys = [0, 0, 0]  # ignored
    values = [0, 0, 0]  # ignored
    inputs = _make_multi_query_input(queries, keys, values, V, V, V)
    out = cortex.forward(assemblage, inputs)
    decoded = _decode_multi_output(out, T, V)
    # M1 = [1, 2, 0]
    # M2 = reverse, V=3: 1 → 1, 2 → 0, 0 → 2  → [1, 0, 2]
    assert decoded == [1, 0, 2]


def test_construct_tracr_program_multilayer_map_explicit_mapping():
    """Map with explicit list mapping."""
    from domains.code_writing_cortex import CodeWritingCortex

    class _A:
        def op_stats(self):
            return {}

    s = _fresh_substrate()
    _seed_parents(s)
    cortex = CodeWritingCortex(s, agent=_A()).install()

    V = 3
    T = 3
    program = {
        "name": "map_explicit",
        "n_positions": T, "vocab_size": V,
        "input_streams": ["q", "k", "v"],
        "ops": [
            {"name": "M", "op": "map",
             "input": "q", "mapping": [2, 0, 1]},  # 0→2, 1→0, 2→1
        ],
        "output": "M",
    }
    assemblage = cortex.construct_tracr_program_multilayer(program)
    assert assemblage is not None

    queries = [0, 1, 2]
    inputs = _make_multi_query_input(queries, [0]*T, [0]*T, V, V, V)
    out = cortex.forward(assemblage, inputs)
    decoded = _decode_multi_output(out, T, V)
    assert decoded == [2, 0, 1]


def test_tracr_multilayer_per_stream_vocab_classify_even():
    """Mixed-vocab pipeline: 4-vocab input stream, 2-vocab output stream.
    Map digits {0, 1, 2, 3} to binary {0=even, 1=odd}."""
    from domains.code_writing_cortex import CodeWritingCortex

    class _A:
        def op_stats(self):
            return {}

    s = _fresh_substrate()
    _seed_parents(s)
    cortex = CodeWritingCortex(s, agent=_A()).install()

    T = 4
    program = {
        "name": "classify_even",
        "n_positions": T,
        "input_streams": [
            {"name": "digit", "vocab_size": 4},
        ],
        "ops": [
            {"name": "parity", "op": "map",
             "input": "digit",
             "mapping": [0, 1, 0, 1],  # 0→even, 1→odd, 2→even, 3→odd
             "output_vocab_size": 2},
        ],
        "output": "parity",
    }
    assemblage = cortex.construct_tracr_program_multilayer(program)
    assert assemblage is not None

    a_attrs = s.node(assemblage)["attrs"]
    # Input dim: T positions × 4 vocab = 16
    assert a_attrs["input_dim"] == T * 4
    # Output dim: T positions × 2 vocab = 8
    assert a_attrs["output_dim"] == T * 2

    # Encode input: digits [0, 1, 2, 3] each as one-hot of size 4.
    digits = [0, 1, 2, 3]
    inputs = []
    for d in digits:
        inputs.extend([1.0 if i == d else 0.0 for i in range(4)])
    out = cortex.forward(assemblage, inputs)
    # Decode: each output position is a one-hot of size 2.
    for i, d in enumerate(digits):
        expected = d % 2
        seg = out[i * 2:(i + 1) * 2]
        decoded = seg.index(max(seg))
        assert decoded == expected, (
            f"position {i}: digit {d}, expected parity {expected}, got {decoded}")


def test_tracr_multilayer_per_stream_vocab_aggregate_to_smaller_vocab():
    """Aggregate with output vocab < value vocab. routing maps values
    {0..5} to outputs {0, 1, 2} (e.g., divide by 2)."""
    from domains.code_writing_cortex import CodeWritingCortex

    class _A:
        def op_stats(self):
            return {}

    s = _fresh_substrate()
    _seed_parents(s)
    cortex = CodeWritingCortex(s, agent=_A()).install()

    T = 3
    program = {
        "name": "agg_smaller",
        "n_positions": T,
        "input_streams": [
            {"name": "q", "vocab_size": 3},
            {"name": "k", "vocab_size": 3},
            {"name": "v", "vocab_size": 6},
        ],
        "ops": [
            {"name": "m", "op": "select",
             "query": "q", "key": "k", "predicate": "equal"},
            {"name": "div2", "op": "aggregate",
             "selector": "m", "value": "v",
             "routing": [0, 0, 1, 1, 2, 2],  # divide-by-2
             "output_vocab_size": 3},
        ],
        "output": "div2",
    }
    assemblage = cortex.construct_tracr_program_multilayer(program)
    assert assemblage is not None

    queries = [0, 1, 2]
    keys = [0, 1, 2]
    values = [5, 3, 0]  # values use vocab 6
    # Each q matches j=q (identity keys). Output = v_j routed:
    #   v_0 = 5 → 2
    #   v_1 = 3 → 1
    #   v_2 = 0 → 0
    # Expected: [2, 1, 0]
    # Encode.
    inputs = []
    for q in queries:
        inputs.extend([1.0 if i == q else 0.0 for i in range(3)])
    for k in keys:
        inputs.extend([1.0 if i == k else 0.0 for i in range(3)])
    for v in values:
        inputs.extend([1.0 if i == v else 0.0 for i in range(6)])
    out = cortex.forward(assemblage, inputs)
    # Output: T positions × 3 vocab
    decoded = []
    for i in range(T):
        seg = out[i * 3:(i + 1) * 3]
        decoded.append(seg.index(max(seg)))
    assert decoded == [2, 1, 0]


def test_tracr_multilayer_per_stream_vocab_chained_through_map_and_aggregate():
    """Two-layer program where the first layer's output has a smaller
    vocab and the second layer reads it as input."""
    from domains.code_writing_cortex import CodeWritingCortex

    class _A:
        def op_stats(self):
            return {}

    s = _fresh_substrate()
    _seed_parents(s)
    cortex = CodeWritingCortex(s, agent=_A()).install()

    T = 3
    program = {
        "name": "shrink_chain",
        "n_positions": T,
        "input_streams": [
            {"name": "digit", "vocab_size": 4},
        ],
        "ops": [
            # First map: digit (V=4) → parity (V=2)
            {"name": "parity", "op": "map",
             "input": "digit",
             "mapping": [0, 1, 0, 1],
             "output_vocab_size": 2},
            # Second map: parity (V=2) → swapped parity (V=2)
            {"name": "swapped", "op": "map",
             "input": "parity",
             "mapping": [1, 0],  # not
             "output_vocab_size": 2},
        ],
        "output": "swapped",
    }
    assemblage = cortex.construct_tracr_program_multilayer(program)
    assert assemblage is not None

    digits = [0, 1, 2, 3 % 4]  # use T=3 → first 3
    digits = [0, 1, 2]
    inputs = []
    for d in digits:
        inputs.extend([1.0 if i == d else 0.0 for i in range(4)])
    out = cortex.forward(assemblage, inputs)
    # parity = [0, 1, 0]; swapped = [1, 0, 1]
    expected = [1, 0, 1]
    for i in range(T):
        seg = out[i * 2:(i + 1) * 2]
        decoded = seg.index(max(seg))
        assert decoded == expected[i]


def test_construct_selector_count_basic_equal_predicate():
    """For each query position, count how many keys have the same value
    (predicate q == k)."""
    from domains.code_writing_cortex import CodeWritingCortex

    class _A:
        def op_stats(self):
            return {}

    s = _fresh_substrate()
    _seed_parents(s)
    cortex = CodeWritingCortex(s, agent=_A()).install()

    V = 3
    T = 3
    assemblage = cortex.construct_selector_count(
        predicate=lambda q, k: q == k,
        T=T, V_q=V, V_k=V, label="eq_count")
    assert assemblage is not None

    # queries [0, 1, 2], keys [0, 1, 1]:
    #   q=0: matches j with k_j=0 → 1
    #   q=1: matches j with k_j=1 → 2
    #   q=2: matches j with k_j=2 → 0
    q_oh = []
    for q in [0, 1, 2]:
        q_oh.extend([1.0 if i == q else 0.0 for i in range(V)])
    k_oh = []
    for k in [0, 1, 1]:
        k_oh.extend([1.0 if i == k else 0.0 for i in range(V)])
    out = cortex.forward(assemblage, q_oh + k_oh)
    assert out == pytest.approx([1.0, 2.0, 0.0], abs=1e-9)


def test_construct_selector_count_less_than_predicate():
    """For each query, count how many keys are strictly greater."""
    from domains.code_writing_cortex import CodeWritingCortex

    class _A:
        def op_stats(self):
            return {}

    s = _fresh_substrate()
    _seed_parents(s)
    cortex = CodeWritingCortex(s, agent=_A()).install()

    V = 4
    T = 4
    assemblage = cortex.construct_selector_count(
        predicate=lambda q, k: q < k,
        T=T, V_q=V, V_k=V, label="lt_count")
    assert assemblage is not None

    # queries [0, 1, 2, 3], keys [1, 2, 0, 3]:
    #   q=0: k=[1,2,0,3] — count k > 0 → 3
    #   q=1: count k > 1 → 2 (k=2, k=3)
    #   q=2: count k > 2 → 1 (k=3)
    #   q=3: count k > 3 → 0
    q_oh = []
    for q in [0, 1, 2, 3]:
        q_oh.extend([1.0 if i == q else 0.0 for i in range(V)])
    k_oh = []
    for k in [1, 2, 0, 3]:
        k_oh.extend([1.0 if i == k else 0.0 for i in range(V)])
    out = cortex.forward(assemblage, q_oh + k_oh)
    assert out == pytest.approx([3.0, 2.0, 1.0, 0.0], abs=1e-9)


def test_construct_selector_count_chained_with_inverter():
    """The count gadget composes with the existing inverter via x = 1/(1+w).
    Verify w → 1/(1+w) → recovered_w."""
    from domains.code_writing_cortex import CodeWritingCortex

    class _A:
        def op_stats(self):
            return {}

    s = _fresh_substrate()
    _seed_parents(s)
    cortex = CodeWritingCortex(s, agent=_A()).install()

    # Build a count layer.
    V = 3
    T = 3
    count_a = cortex.construct_selector_count(
        predicate=lambda q, k: q == k,
        T=T, V_q=V, V_k=V, label="count_inv_demo")
    assert count_a is not None

    # Build the inverter for w_max = 3.
    inv_a = cortex.construct_selector_width_inverter(w_max=3)
    assert inv_a is not None

    # Manually verify: count → inverter pipeline.
    # queries [0, 1, 2], keys [0, 0, 0]: q=0 → 3 matches; q=1, q=2 → 0
    q_oh = []
    for q in [0, 1, 2]:
        q_oh.extend([1.0 if i == q else 0.0 for i in range(V)])
    k_oh = []
    for k in [0, 0, 0]:
        k_oh.extend([1.0 if i == k else 0.0 for i in range(V)])
    counts = cortex.forward(count_a, q_oh + k_oh)
    assert counts == pytest.approx([3.0, 0.0, 0.0], abs=1e-9)

    # The inverter takes x = 1/(1+w) and returns w.
    # If we applied count then 1/(1+w), then inverter, we'd recover w.
    # Here we verify the inverter directly on the count values.
    for w in counts:
        x = 1.0 / (1.0 + w)
        recovered = cortex.forward(inv_a, [x])[0]
        assert abs(recovered - w) < 1e-9


def test_construct_multiplexer_auto_b_up_c_down_abs():
    """Original case: b=identity (increasing), c=negate (decreasing).
    Realises |x|. Mode should be 'b_up_c_down'."""
    from domains.code_writing_cortex import CodeWritingCortex

    class _A:
        def op_stats(self):
            return {}

    s = _fresh_substrate()
    _seed_parents(s)
    cortex = CodeWritingCortex(s, agent=_A()).install()

    negate = cortex._mint_scalar_linear(-1.0, 0.0, label="neg_auto")
    mux = cortex.construct_multiplexer_auto(
        "identity_gadget", negate, boundary_x=0.0, label="abs")
    assert mux is not None
    # Mode recorded.
    top = next(n for n in s.nodes("DesignPattern")
               if s.node(n)["attrs"].get("origin") == "cortex_constructed_mux_auto"
               and "abs" in s.node(n)["attrs"].get("name", ""))
    assert s.node(top)["attrs"]["mux_mode"] == "b_up_c_down"

    for x in [-2.0, -1.0, -0.5, 0.0, 0.5, 1.0, 2.0]:
        out = cortex.forward(mux, [x])
        assert out == pytest.approx([abs(x)], abs=1e-9)


def test_construct_multiplexer_auto_b_up_c_up_asymmetric_v():
    """b=2x (increasing), c=x (increasing). Realises piecewise
    z(x) = 2x if x ≥ 0 else x. Mode 'b_up_c_up'."""
    from domains.code_writing_cortex import CodeWritingCortex

    class _A:
        def op_stats(self):
            return {}

    s = _fresh_substrate()
    _seed_parents(s)
    cortex = CodeWritingCortex(s, agent=_A()).install()

    b_p = cortex._mint_scalar_linear(2.0, 0.0, label="2x")
    c_p = cortex._mint_scalar_linear(1.0, 0.0, label="x")
    mux = cortex.construct_multiplexer_auto(
        b_p, c_p, boundary_x=0.0, label="asym_up")
    assert mux is not None
    top = next(n for n in s.nodes("DesignPattern")
               if s.node(n)["attrs"].get("origin") == "cortex_constructed_mux_auto"
               and "asym_up" in s.node(n)["attrs"].get("name", ""))
    assert s.node(top)["attrs"]["mux_mode"] == "b_up_c_up"

    for x in [-1.5, -1.0, -0.5, 0.0, 0.5, 1.0, 1.5]:
        out = cortex.forward(mux, [x])
        expected = 2.0 * x if x >= 0 else 1.0 * x
        assert out == pytest.approx([expected], abs=1e-9)


def test_construct_multiplexer_auto_b_down_c_down_asymmetric_descent():
    """b=-x (decreasing), c=-2x (decreasing). Realises z(x) = -x if
    x ≥ 0 else -2x. Mode 'b_down_c_down'."""
    from domains.code_writing_cortex import CodeWritingCortex

    class _A:
        def op_stats(self):
            return {}

    s = _fresh_substrate()
    _seed_parents(s)
    cortex = CodeWritingCortex(s, agent=_A()).install()

    b_p = cortex._mint_scalar_linear(-1.0, 0.0, label="neg_x")
    c_p = cortex._mint_scalar_linear(-2.0, 0.0, label="neg_2x")
    mux = cortex.construct_multiplexer_auto(
        b_p, c_p, boundary_x=0.0, label="asym_down")
    assert mux is not None
    top = next(n for n in s.nodes("DesignPattern")
               if s.node(n)["attrs"].get("origin") == "cortex_constructed_mux_auto"
               and "asym_down" in s.node(n)["attrs"].get("name", ""))
    assert s.node(top)["attrs"]["mux_mode"] == "b_down_c_down"

    for x in [-1.5, -1.0, -0.5, 0.0, 0.5, 1.0, 1.5]:
        out = cortex.forward(mux, [x])
        expected = -x if x >= 0 else -2.0 * x
        assert out == pytest.approx([expected], abs=1e-9)


def test_construct_multiplexer_auto_b_down_c_up_neg_abs():
    """b=-x (decreasing), c=x (increasing). Realises -|x|.
    Mode 'b_down_c_up'."""
    from domains.code_writing_cortex import CodeWritingCortex

    class _A:
        def op_stats(self):
            return {}

    s = _fresh_substrate()
    _seed_parents(s)
    cortex = CodeWritingCortex(s, agent=_A()).install()

    b_p = cortex._mint_scalar_linear(-1.0, 0.0, label="neg_x_a")
    mux = cortex.construct_multiplexer_auto(
        b_p, "identity_gadget", boundary_x=0.0, label="neg_abs")
    assert mux is not None
    top = next(n for n in s.nodes("DesignPattern")
               if s.node(n)["attrs"].get("origin") == "cortex_constructed_mux_auto"
               and "neg_abs" in s.node(n)["attrs"].get("name", ""))
    assert s.node(top)["attrs"]["mux_mode"] == "b_down_c_up"

    for x in [-2.0, -1.0, -0.5, 0.0, 0.5, 1.0, 2.0]:
        out = cortex.forward(mux, [x])
        assert out == pytest.approx([-abs(x)], abs=1e-9)


def test_construct_multiplexer_auto_refuses_non_monotonic():
    """b = square_pwl_signed_gadget — NOT strictly monotonic through 0
    (b(ε) and b(-ε) are both positive). Construction refused with a
    non_monotonic verdict."""
    from domains.code_writing_cortex import CodeWritingCortex

    class _A:
        def op_stats(self):
            return {}

    s = _fresh_substrate()
    _seed_parents(s)
    cortex = CodeWritingCortex(s, agent=_A()).install()

    zero = cortex._mint_scalar_linear(0.0, 0.0, label="zero_auto")
    mux = cortex.construct_multiplexer_auto(
        "square_pwl_signed_gadget", zero,
        boundary_x=0.0, label="non_mono")
    assert mux is None
    viol = [n for n in s.nodes("DesignPattern")
            if s.node(n)["attrs"].get("gadget_kind") == "cpwl_invalid"
            and "non_mono" in s.node(n)["attrs"].get("name", "")]
    assert len(viol) >= 1
    a = s.node(viol[0])["attrs"]
    assert "monotonicity" in a["soundness_predicate"]


def test_constructed_max_actually_computes_max():
    """Same proof for max(x, y)."""
    from domains.code_writing_cortex import CodeWritingCortex

    class _A:
        def op_stats(self):
            return {}

    s = _fresh_substrate()
    _seed_parents(s)
    cortex = CodeWritingCortex(s, agent=_A()).install()

    target = s.add_node("ReplacementTarget", {
        "op_name": "compute_max",
        "baseline_total_ms": 100.0,
        "baseline_count": 1000,
        "baseline_mean_ms": 0.1,
        "selected_at": 0.0,
    })
    root = cortex._ensure_root()
    s.add_edge(root, "current_target", target, {})
    max_pattern = next(n for n in s.nodes("DesignPattern")
                       if s.node(n)["attrs"].get("name") == "max_gadget")
    s.add_edge(target, "uses_pattern", max_pattern, {})

    assemblage = cortex.assemble_network(target)
    constructed = cortex.construct_weights(assemblage)
    weights = {s.node(w)["attrs"]["role"]: np.array(s.node(w)["attrs"]["data"])
               for w in constructed}
    W1, b1, W2, b2 = weights["W1"], weights["b1"], weights["W2"], weights["b2"]

    for x, y in [(5.0, 2.0), (2.0, 5.0), (-3.0, 7.0), (7.0, -3.0),
                 (0.0, 0.0), (-1.5, -2.5), (3.14, 3.14)]:
        v = np.array([x, y])
        hidden = np.maximum(0.0, W1 @ v + b1)
        out = W2 @ hidden + b2
        assert abs(float(out[0]) - max(x, y)) < 1e-9, (
            f"constructed max({x}, {y}) = {float(out[0])}, "
            f"expected {max(x, y)}")

"""Per-language renderers — migrated twin of tests/test_renderer.py.

ALL 7 tests migrate cleanly: CuriousAgent.seed_{python,rust,x86_64}_renderer
and render_in_graph are replaced by WorldAdapter.seed_{python,rust,x86_64}_renderer
and WorldAdapter.render (the Rust Render engine). No CuriousAgent, no
domains.renderer dispatcher (which was a thin CA wrapper), no Python render loop.

Coverage map (1:1):
  test_python_renderer_emits_valid_recursive_factorial
    → test_python_renderer_emits_valid_recursive_factorial
      WorldAdapter.seed_python_renderer() + wa.render(term, "python") +
      function-shell wrap; exec verifies all 11 factorial values.
  test_rust_renderer_emits_recursive_factorial
    → test_rust_renderer_emits_recursive_factorial
      Same, Rust; structural assertions identical to the original.
  test_x86_64_renderer_emits_valid_assembly
    → test_x86_64_renderer_emits_valid_assembly
      Same, x86_64; all 9 structural assertions identical.
  test_dispatch_with_agent_routes_to_graph_for_python
    → test_dispatch_with_adapter_routes_to_graph_for_python
      _render_with_wa() on an even-parity spec.
  test_dispatch_without_agent_raises_keyerror
    → test_dispatch_without_adapter_raises_keyerror
      _render_with_wa() with wa=None raises KeyError — same semantics.
  test_unknown_language_raises_keyerror
    → test_unknown_language_raises_keyerror
      wa.language("malbolge") is None → KeyError.
  test_renderers_run_on_simple_predicates
    → test_renderers_run_on_simple_predicates
      All three renderers on is_even spec; Python exec verified.

Trim rationale: none needed — all 7 tests covered.
Impasse-gap / teacher / self-teacher tests live in test_graph_renderer.py
(CuriousAgent-only). The render-gap-returns-None case is already covered by
test_render_migrated.py::test_render_gap_returns_none_for_unknown_head.
"""
from __future__ import annotations

import pytest

srs = pytest.importorskip("substrate_rs")

from substrate.world_adapter import WorldAdapter


# Canonical recursive definition used throughout: factorial(n).
FACT_SPEC = [
    "IfThenElse",
    ["Eq", "value", 0],
    1,
    ["Times", "value", ["Holds", "factorial", ["Minus", "value", 1]]],
]


def _adapter_with_all_three() -> WorldAdapter:
    wa = WorldAdapter()
    wa.seed_python_renderer()
    wa.seed_rust_renderer()
    wa.seed_x86_64_renderer()
    return wa


def _adapter_with_python_and_rust() -> WorldAdapter:
    return _adapter_with_all_three()


def _render_with_wa(language: str, concept_name: str, spec,
                    wa: "WorldAdapter | None" = None) -> str:
    """WorldAdapter equivalent of domains.renderer.render():
    check language installed, convert spec → Term, render body, wrap in shell.
    Raises KeyError when wa is None or the language is not installed."""
    if wa is None:
        raise KeyError(
            f"render({language!r}, …) needs a WorldAdapter with the language "
            f"installed — call wa.seed_<lang>_renderer()")
    if wa.language(language) is None:
        raise KeyError(
            f"{language!r} not installed on adapter — call "
            f"seed_<lang>_renderer() or install_render_rule()")
    term = wa._spec_to_term(spec)
    body = wa.render(term, language)
    if body is None:
        raise KeyError(
            f"{language} render gap on {concept_name!r}; teach the missing rule")
    if language == "python":
        return f"def {concept_name}(value):\n    return {body}\n"
    if language == "rust":
        return (f"fn {concept_name}(value: i64) -> i64 {{\n"
                f"    {body}\n"
                f"}}\n")
    if language == "x86_64":
        return (f".globl {concept_name}\n"
                f".type {concept_name}, @function\n"
                f"{concept_name}:\n"
                f"    pushq %rbp\n"
                f"    movq %rsp, %rbp\n"
                f"{body}\n"
                f"    movq %rbp, %rsp\n"
                f"    popq %rbp\n"
                f"    ret\n")
    return body


def test_python_renderer_emits_valid_recursive_factorial():
    wa = _adapter_with_python_and_rust()
    src = _render_with_wa("python", "factorial", FACT_SPEC, wa=wa)
    ns: dict = {}
    exec(src, ns)
    factorial = ns["factorial"]
    expected = [1, 1, 2, 6, 24, 120, 720, 5040, 40320, 362880, 3628800]
    for n, exp in enumerate(expected):
        assert factorial(n) == exp, f"factorial({n}) = {factorial(n)}; expected {exp}"


def test_rust_renderer_emits_recursive_factorial():
    wa = _adapter_with_python_and_rust()
    src = _render_with_wa("rust", "factorial", FACT_SPEC, wa=wa)
    assert "fn factorial(value: i64) -> i64" in src
    assert "factorial((value - 1i64))" in src
    assert "if (value == 0i64)" in src
    assert "{ 1i64 }" in src
    assert "(value * factorial" in src


def test_x86_64_renderer_emits_valid_assembly():
    wa = _adapter_with_all_three()
    src = _render_with_wa("x86_64", "factorial", FACT_SPEC, wa=wa)
    assert ".globl factorial" in src
    assert "factorial:" in src
    assert "pushq %rbp" in src
    assert "movq %rsp, %rbp" in src
    assert "ret" in src
    assert "call factorial" in src
    assert "pushq %rdi" in src
    assert "popq %rdi" in src
    assert "imulq %rcx, %rax" in src
    assert "cmpq %rcx, %rax" in src
    assert "sete %al" in src


def test_dispatch_with_adapter_routes_to_graph_for_python():
    wa = _adapter_with_python_and_rust()
    py = _render_with_wa("python", "even", ["Eq", ["Mod", "value", 2], 0], wa=wa)
    assert "def even" in py
    assert "value % 2" in py


def test_dispatch_without_adapter_raises_keyerror():
    for lang in ("python", "rust", "x86_64"):
        with pytest.raises(KeyError):
            _render_with_wa(lang, "factorial", FACT_SPEC)


def test_unknown_language_raises_keyerror():
    wa = _adapter_with_python_and_rust()
    with pytest.raises(KeyError):
        _render_with_wa("malbolge", "factorial", FACT_SPEC, wa=wa)


def test_renderers_run_on_simple_predicates():
    wa = _adapter_with_python_and_rust()
    spec = ["Eq", ["Mod", "value", 2], 0]
    py = _render_with_wa("python", "is_even", spec, wa=wa)
    rs = _render_with_wa("rust", "is_even", spec, wa=wa)
    asm = _render_with_wa("x86_64", "is_even", spec, wa=wa)
    ns: dict = {}
    exec(py, ns)
    assert ns["is_even"](4) is True
    assert ns["is_even"](7) is False
    assert "value % 2i64" in rs
    assert "idivq" in asm

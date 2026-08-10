"""CodeWritingCortex — migrated twin (no CuriousAgent).

All tests from test_code_writing_cortex.py, rewritten to boot on the
seed-booted WorldAdapter instead of a raw _native.Substrate().  The
`_MockAgent` stub (op_stats only) is the ONLY agent surface the
CodeWritingCortex touches — it is a thin I/O provider, not CuriousAgent
cognition, and is preserved here as-is.

Migration: raw `_native.Substrate()` -> `WorldAdapter().s`.  The cortex
itself is unchanged; the productions it needs are either already admitted
by `boot_core` or installed by CodeWritingCortex.install() — no per-test
production hand-wiring needed.
"""
from __future__ import annotations

import pytest

pytest.importorskip("substrate_rs")

from substrate.world_adapter import WorldAdapter


class _MockAgent:
    """Thin op-stats provider (the only agent surface CodeWritingCortex
    reads). NOT CuriousAgent — just a plain Python object with one method."""
    def __init__(self, op_stats: dict, self_teacher=None):
        self._op_stats = dict(op_stats)
        self._self_teacher = self_teacher

    def op_stats(self):
        return dict(self._op_stats)


# ---------------------------------------------------------------------------
# install
# ---------------------------------------------------------------------------

def test_install_creates_cortex_node_and_reflexes():
    from domains.code_writing_cortex import CodeWritingCortex
    wa = WorldAdapter()
    cortex = CodeWritingCortex(wa.s).install()
    assert cortex.cortex_nid is not None

    cortex_nodes = wa.s.nodes("CodeWritingCortex")
    assert len(cortex_nodes) == 1

    reflexes = wa.s.neighbours(cortex.cortex_nid, "has_reflex")
    reflex_names = {wa.s.node(r)["attrs"]["name"] for r in reflexes}
    assert reflex_names == {
        "cw_identify_target",
        "cw_select_design_pattern",
        "cw_mechanical_draft",
        "cw_request_author",
        "cw_drain_teacher",
        "cw_validate",
        "cw_install_if_better",
    }


def test_install_is_idempotent():
    from domains.code_writing_cortex import CodeWritingCortex
    wa = WorldAdapter()
    CodeWritingCortex(wa.s).install()
    CodeWritingCortex(wa.s).install()
    assert len(wa.s.nodes("CodeWritingCortex")) == 1


def test_install_wires_genlMt_to_compiler_theory_when_present():
    """If compiler_theory Mt is already installed, the code_authoring
    Mt inherits from it via genlMt — so the agent's compiler-theory
    knowledge is in scope when code-authoring reasoning fires."""
    from domains.code_writing_cortex import CodeWritingCortex
    wa = WorldAdapter()
    wa.s.add_node("Microtheory", {"name": "compiler_theory"})
    CodeWritingCortex(wa.s).install()
    mts = {wa.s.node(n)["attrs"].get("name") for n in wa.s.nodes("Microtheory")}
    assert {"code_authoring", "compiler_theory"} <= mts


# ---------------------------------------------------------------------------
# reflex 1: identify_target
# ---------------------------------------------------------------------------

def test_tick_with_no_agent_does_nothing():
    from domains.code_writing_cortex import CodeWritingCortex
    wa = WorldAdapter()
    cortex = CodeWritingCortex(wa.s).install()
    audit = cortex.tick()
    assert audit == []


def test_tick_with_empty_stats_picks_no_target():
    from domains.code_writing_cortex import CodeWritingCortex
    wa = WorldAdapter()
    cortex = CodeWritingCortex(wa.s, agent=_MockAgent({})).install()
    audit = cortex.tick()
    assert "cw_identify_target" not in audit
    assert cortex.current_target() is None


def test_tick_picks_most_expensive_op_as_target():
    """The cortex's identification reflex reads op_stats and picks
    the most-expensive op by total_ms."""
    from domains.code_writing_cortex import CodeWritingCortex
    wa = WorldAdapter()
    cortex = CodeWritingCortex(wa.s, agent=_MockAgent({
        "cheap_op":      {"count": 100, "total_ms":   5.0},
        "evaluate_term": {"count": 100, "total_ms": 500.0},
        "medium_op":     {"count": 100, "total_ms":  50.0},
    })).install()
    cortex.tick()
    target = cortex.current_target()
    assert target is not None
    assert wa.s.node(target)["attrs"]["op_name"] == "evaluate_term"


# ---------------------------------------------------------------------------
# reflex 2 + 3: request_author + drain_teacher with a mock teacher
# ---------------------------------------------------------------------------

def test_cortex_consults_self_teacher_when_target_set(tmp_path):
    """With a target and a self-teacher, the request reflex composes
    the question and calls the teacher.  The drained payload becomes
    a CodeDraft attached to the target."""
    from domains.code_writing_cortex import CodeWritingCortex

    fake_repo = tmp_path
    (fake_repo / "runners" / "dsl" / "src").mkdir(parents=True)
    fake_src = fake_repo / "runners" / "dsl" / "src" / "term.rs"
    fake_src.write_text("// existing slow evaluator\nfn evaluate() {}\n")

    teacher_calls = []

    def mock_teacher(q):
        teacher_calls.append(q)
        return {"answer": "fn evaluate() -> i64 { 0 }\n"}

    wa = WorldAdapter()
    cortex = CodeWritingCortex(
        wa.s,
        agent=_MockAgent({"evaluate_term": {"count": 10, "total_ms": 100.0}},
                         self_teacher=mock_teacher),
        repo_root=fake_repo,
    ).install()
    cortex.tick()

    assert len(teacher_calls) == 1
    q = teacher_calls[0]
    assert "evaluate_term" in q
    assert "constant folding" in q
    assert "// existing slow evaluator" in q

    drafts = wa.s.nodes("CodeDraft")
    assert len(drafts) == 1
    src = wa.s.node(drafts[0])["attrs"]["source"]
    assert "fn evaluate() -> i64 { 0 }" in src


# ---------------------------------------------------------------------------
# reflex 4 + 5: validate + install
# ---------------------------------------------------------------------------

def test_validation_rejects_garbage_rust(tmp_path):
    """If the teacher returns code that doesn't compile, the validate
    reflex records compile_ok=False; install_if_better discards the
    target and moves on."""
    from domains.code_writing_cortex import CodeWritingCortex

    fake_repo = tmp_path
    (fake_repo / "runners" / "dsl" / "src").mkdir(parents=True)
    (fake_repo / "runners" / "dsl" / "src" / "term.rs").write_text(
        "fn original() {}\n")

    def garbage_teacher(q):
        return {"answer": "fn this_does_not_compile -> ???"}

    wa = WorldAdapter()
    cortex = CodeWritingCortex(
        wa.s,
        agent=_MockAgent({"evaluate_term": {"count": 10, "total_ms": 100.0}},
                         self_teacher=garbage_teacher),
        repo_root=fake_repo,
    ).install()
    cortex.tick()

    draft = next(iter(wa.s.nodes("CodeDraft")), None)
    if draft is not None:
        val = cortex.draft_validation(draft)
        if val is not None:
            assert val["compile_ok"] is False

    assert len(wa.s.nodes("CodeInstallation")) == 0


# ---------------------------------------------------------------------------
# integration: the full loop runs to fixed point in one tick
# ---------------------------------------------------------------------------

def test_full_loop_fires_all_reflexes_in_order(tmp_path):
    """The headline test: with a valid teacher response and a target,
    one `tick()` should drive identify_target -> request_author ->
    drain_teacher -> validate -> (install_if_better or discard)."""
    import shutil
    if shutil.which("cargo") is None:
        pytest.skip("cargo not available")

    from domains.code_writing_cortex import CodeWritingCortex

    fake_repo = tmp_path
    (fake_repo / "runners" / "dsl" / "src").mkdir(parents=True)
    (fake_repo / "runners" / "dsl" / "src" / "term.rs").write_text(
        "// original\nfn evaluate() -> i64 { 0 }\n")

    valid_replacement = (
        "// rewritten\n"
        "pub fn evaluate() -> i64 { 42 }\n"
    )

    def teacher(q):
        return {"answer": valid_replacement}

    wa = WorldAdapter()
    cortex = CodeWritingCortex(
        wa.s,
        agent=_MockAgent({"evaluate_term": {"count": 10, "total_ms": 100.0}},
                         self_teacher=teacher),
        repo_root=fake_repo,
    ).install()

    audit = cortex.tick()

    assert audit[0] == "cw_identify_target"
    assert "cw_request_author" in audit
    assert "cw_drain_teacher" in audit
    assert "cw_validate" in audit
    assert "cw_install_if_better" in audit


# ---------------------------------------------------------------------------
# the principle: the cortex's reasoning is graph-resident, not Python
# ---------------------------------------------------------------------------

def test_reflexes_are_first_class_graph_nodes():
    """The cortex's reflexes ARE graph nodes (queryable, introspectable,
    modifiable) — they're not opaque Python state."""
    from domains.code_writing_cortex import CodeWritingCortex
    wa = WorldAdapter()
    cortex = CodeWritingCortex(wa.s).install()
    reflexes = wa.s.neighbours(cortex.cortex_nid, "has_reflex")
    for r in reflexes:
        attrs = wa.s.node(r)["attrs"]
        assert attrs["origin"] == "code_authoring"
        assert attrs["stimulus_desc"]
        assert isinstance(attrs["priority"], int)


def test_pattern_library_languages_targets_are_all_graph_resident():
    """Every piece of authoring data the cortex consults lives as graph
    nodes — patterns, language models, target catalogue, exclusion
    pairs, scoring weights."""
    from domains.code_writing_cortex import CodeWritingCortex
    wa = WorldAdapter()
    CodeWritingCortex(wa.s).install()

    assert len(wa.s.nodes("DesignPattern")) >= 8
    assert len(wa.s.nodes("DesignExclusion")) >= 2

    assert len(wa.s.nodes("ProgrammingLanguage")) >= 6
    assert len(wa.s.nodes("LanguageExclusion")) >= 2
    assert len(wa.s.nodes("LanguageScoringConfig")) == 1

    assert len(wa.s.nodes("CodeTarget")) >= 3
    target_ops = {wa.s.node(n)["attrs"]["op_name"]
                  for n in wa.s.nodes("CodeTarget")}
    assert "evaluate_polynomial" in target_ops


def test_design_pattern_selection_is_a_graph_query():
    """The cortex's design step reads patterns from the graph and
    picks one — no hardcoded library."""
    from domains.code_writing_cortex import CodeWritingCortex
    from domains.design_patterns import pick_design_pattern
    wa = WorldAdapter()
    CodeWritingCortex(wa.s).install()

    wa.s.add_node("DesignPattern", {
        "name": "synthetic_perfect_match",
        "applies_when": ["very_specific_tag_a", "very_specific_tag_b"],
        "expected_speedup": 99.0,
        "category": "denotational_equivalence",
        "origin": "test",
    })

    chosen = pick_design_pattern(wa.s, ["very_specific_tag_a",
                                        "very_specific_tag_b"])
    assert chosen is not None
    assert chosen["name"] == "synthetic_perfect_match"


def test_microtheory_is_inheritance_anchored_in_compiler_theory():
    """The agent's code-authoring reasoning happens UNDER the
    code_authoring Mt; that Mt inherits from compiler_theory."""
    from domains.code_writing_cortex import CodeWritingCortex
    wa = WorldAdapter()
    wa.s.add_node("Microtheory", {"name": "compiler_theory"})
    cortex = CodeWritingCortex(wa.s).install()

    code_mt = next(n for n in wa.s.nodes("Microtheory")
                   if wa.s.node(n)["attrs"]["name"] == "code_authoring")
    ancestors = {wa.s.node(n)["attrs"]["name"]
                 for n in wa.s.neighbours(code_mt, "genlMt")}
    assert "compiler_theory" in ancestors

"""test_text_segmentation_by_recognition — READING AN INSTRUCTION IS COGNITION,
ALL THE WAY DOWN TO THE WORD.

The user's correction (non-negotiable): understanding text is cognition, not I/O —
AND whitespace is NOT the delimiter. So domains/operational_planning + the new
domains/instruction_reading carry NO regex and NO whitespace-as-delimiter: the ONLY
I/O is raw text -> a CHARACTER stream in the graph, and WORD boundaries EMERGE from
RECOGNITION (lexicon decode + forward_segmentation TP-troughs), the same
segmentation-by-recognition the agent uses for ink/speech. The clause boundary is a
graph VERB-HEAD Term. These gates are DISCRIMINATIVE (donkey=0).

Run: PYTHONPATH=runners/dsl/python:.:scripts pytest \
     tests/test_text_segmentation_by_recognition.py -p no:randomly
"""
from __future__ import annotations

import ast
import io
import contextlib

import pytest


CAPSTONE = (
    "Bulk load Wikipedia. "
    "Measure the load timing and judge whether it is sufficiently fast; "
    "if it is not fast enough, warm up wordnet. "
    "Then perceive the other gaps and prioritize them; "
    "for each gap you find, if it is worth fixing, fix it. "
    "Stop when the rest is sufficient. "
    "Finally report what was loaded and which gaps were fixed."
)


@pytest.fixture(scope="module")
def agent():
    buf = io.StringIO()
    with contextlib.redirect_stderr(buf), contextlib.redirect_stdout(buf):
        from substrate.world_adapter import WorldAdapter
        from substrate.boot_all import load_all_seeds
        a = WorldAdapter(seeds=())
        load_all_seeds(a)
    return a


@pytest.fixture(scope="module")
def op():
    import domains.operational_planning as _op
    return _op


@pytest.fixture(scope="module")
def ir():
    import domains.instruction_reading as _ir
    return _ir


def _quiet(fn, *a, **k):
    buf = io.StringIO()
    with contextlib.redirect_stderr(buf), contextlib.redirect_stdout(buf):
        return fn(*a, **k)


def _binds(agent, parsed):
    return [agent.s.node(s)["attrs"].get("binding_key") for s in parsed["steps"]]


def _kinds(agent, parsed):
    return [agent.s.node(s)["attrs"].get("kind") for s in parsed["steps"]]


# ===========================================================================
# 1. ZERO REGEX + ZERO WHITESPACE-DELIMITER (headline source audit).
# ===========================================================================
def _audit_module(modname: str) -> list:
    import importlib, inspect
    mod = importlib.import_module(modname)
    src = inspect.getsource(mod)
    tree = ast.parse(src)
    findings = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for n in node.names:
                if n.name.split(".")[0] == "re":
                    findings.append(f"import {n.name}")
        if isinstance(node, ast.ImportFrom):
            if (node.module or "").split(".")[0] == "re":
                findings.append(f"from {node.module} import ...")
        # re.<anything>
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) \
                and node.value.id == "re":
            findings.append(f"re.{node.attr}")
        # <expr>.split(...) call — the whitespace tokeniser we forbid
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) \
                and node.func.attr in ("split", "rsplit", "splitlines"):
            findings.append(f".{node.func.attr}() call")
    return findings


def test_zero_regex_zero_whitespace_delimiter_source_audit():
    audited = {}
    for m in ("domains.operational_planning", "domains.instruction_reading"):
        audited[m] = _audit_module(m)
    print("\n=== ZERO-REGEX + ZERO-WHITESPACE SOURCE AUDIT ===")
    for m, f in audited.items():
        print(f"  {m}: {'CLEAN (no re, no .split())' if not f else f}")
    for m, f in audited.items():
        assert f == [], (m, f)


# ===========================================================================
# 2. MISSING-WHITESPACE ROBUSTNESS (the headline capability): a run-together /
#    mis-spaced instruction segments to the CORRECT words via RECOGNITION; the
#    whitespace .split() baseline produces WRONG tokens.
# ===========================================================================
def test_missing_whitespace_robustness(agent, op, ir):
    op._ensure_seed(agent)
    mis = "bulkload wikipedia. measuretiming and judge whether it is fast"
    recognised = _quiet(ir.segment, agent, mis)["words"]
    baseline = mis.split()   # the whitespace tokeniser we replaced
    print("\n=== MISSING-WHITESPACE ROBUSTNESS ===")
    print(f"  instruction        : {mis!r}")
    print(f"  RECOGNITION (right): {recognised}")
    print(f"  .split()   (WRONG) : {baseline}")
    # recognition recovers the joined words
    for w in ("bulk", "load", "wikipedia", "measure", "timing", "judge"):
        assert w in recognised, (w, recognised)
    # the whitespace baseline fuses them WRONG
    assert "bulkload" in baseline and "bulk" not in baseline
    assert "measuretiming" in baseline and "measure" not in baseline
    # so the two disagree exactly where recognition wins
    assert recognised != [b.strip(".") for b in baseline]


# ===========================================================================
# 3. CAPSTONE FIXED (graph-native): the exact whole-cycle instruction -> the
#    correct plan (measure_timing + judge_sufficiency SEPARATE from the ifthen;
#    ifthen(not-fast->warm) SEPARATE; foreach(gaps){ifthen->fix}; stop; report ONE
#    step, NO phantom perceive_gaps, report LAST).
# ===========================================================================
def test_capstone_fixed(agent, op):
    parsed = _quiet(op.parse_instruction, agent, CAPSTONE)
    binds = _binds(agent, parsed)
    kinds = _kinds(agent, parsed)
    print("\n=== CAPSTONE PLAN (after) ===")
    print(f"  n_steps = {parsed['n_steps']}")
    print(f"  binds   = {binds}")
    print(f"  kinds   = {kinds}")
    assert parsed["n_steps"] == 9, binds
    # the exact ordered, separated plan
    assert binds == ["bulk_load", "measure_timing", "judge_sufficiency", None,
                     "perceive_gaps", "prioritize", None, "stop", "report"], binds
    assert kinds == ["act", "act", "act", "ifthen", "act", "act", "foreach",
                     "stop", "act"], kinds
    # the ifthen at index 3 is SEPARATE and guards warm (not-fast -> warm)
    ift = parsed["steps"][3]
    subs = agent.inner.neighbours(ift, "substep")
    assert any(agent.s.node(c)["attrs"].get("binding_key") == "warm" for c in subs)
    # measure_timing + judge_sufficiency are NOT folded into that ifthen
    assert agent.s.node(parsed["steps"][1])["attrs"].get("kind") == "act"
    assert agent.s.node(parsed["steps"][2])["attrs"].get("kind") == "act"
    # the foreach nests an ifthen that guards fix
    fe = parsed["steps"][6]
    fsub = agent.inner.neighbours(fe, "substep")
    assert any(agent.s.node(c)["attrs"].get("kind") == "ifthen" for c in fsub)
    ift2 = next(c for c in fsub if agent.s.node(c)["attrs"].get("kind") == "ifthen")
    assert any(agent.s.node(c)["attrs"].get("binding_key") == "fix"
               for c in agent.inner.neighbours(ift2, "substep"))
    # report is the LAST step and matched report, NOT a phantom perceive_gaps
    assert binds[-1] == "report"
    assert "perceive_gaps" not in binds[7:]   # no phantom after prioritize's block


# ===========================================================================
# 4. GRAPH-NATIVE / SEGMENTATION-BY-RECOGNITION (audit): words come from the Char
#    stream via lexicon recognition + forward_segmentation TP-troughs, not
#    whitespace; the clause boundary is the verb-head Term.
# ===========================================================================
def test_segmentation_is_by_recognition(agent, op, ir):
    op._ensure_seed(agent)
    seg = _quiet(ir.segment, agent, "Measure the load timing.")
    print("\n=== SEGMENTATION-BY-RECOGNITION ===")
    print(f"  char stream nodes  : {len(seg['char_nodes'])} Char nodes (the only I/O)")
    print(f"  lexicon size       : {seg['lexicon_size']} known words")
    print(f"  lexicon matches    : {seg['lexicon_matches']}")
    print(f"  words              : {seg['words']}")
    # THE ONLY I/O: one Char node per character.
    assert len(seg["char_nodes"]) == len("Measure the load timing.")
    # the words are RECOGNISED lexicon matches (not a whitespace split)
    for w in ("measure", "the", "load", "timing"):
        assert w in seg["lexicon_matches"], (w, seg["lexicon_matches"])
    # RECOGNITION splits a joined KNOWN-word span (a high-TP run per known word,
    # boundary at the junction) — NOT whitespace. The words emerge from the lexicon
    # decode over the Char stream.
    joined = _quiet(ir.segment, agent, "loadtiming")["words"]
    print(f"  recognition of joined 'loadtiming' -> {joined}")
    assert joined == ["load", "timing"], joined
    # forward_segmentation is the boundary machinery reused for the OOV residual — the
    # graph-resident TP-trough boundary Term the agent evaluates natively over the
    # Char stream's Transition nodes. Demonstrate the graph path RUNS (returns a
    # boundary set); for a genuinely OOV span the split quality is bounded by the
    # lexicon's char-bigram structure (an honest, stated residual).
    from domains import forward_segmentation as fs
    assert hasattr(fs, "find_boundaries_via_graph")
    lex = ir.gather_lexicon(agent)
    lextp = ir._lex_char_tp(lex)
    pieces = ir._oov_tp_split(agent, "loadtiming", lextp)   # runs the graph boundary Term
    print(f"  forward_segmentation TP-trough path over OOV 'loadtiming' -> {pieces} "
          f"(quality bounded by lexicon char-bigram structure — honest residual)")
    assert isinstance(pieces, list) and pieces   # the graph-resident path ran


# ===========================================================================
# 5. DISCRIMINATIVE (verb-head faculty): the SAME 'and', a DIFFERENT split, via the
#    graph verb-head Term. Both-verb-headed -> TWO steps; mixed -> ONE step.
# ===========================================================================
def test_verb_head_discriminates_the_and(agent, op, ir):
    two = _quiet(op.parse_instruction, agent, "Warm up wordnet and measure the timing.")
    one = _quiet(op.parse_instruction, agent,
                 "Report what was loaded and which gaps were fixed.")
    print("\n=== VERB-HEAD DISCRIMINATION (same 'and', different split) ===")
    print(f"  'Warm up wordnet and measure the timing' -> {_binds(agent, two)}")
    print(f"  'Report what was loaded and which gaps were fixed' -> {_binds(agent, one)}")
    print(f"  verb_headed('warm up wordnet')      = {ir.is_verb_headed('warm up wordnet')}")
    print(f"  verb_headed('measure the timing')   = {ir.is_verb_headed('measure the timing')}")
    print(f"  verb_headed('what was loaded')      = {ir.is_verb_headed('what was loaded')}")
    print(f"  verb_headed('which gaps were fixed')= {ir.is_verb_headed('which gaps were fixed')}")
    # both sides verb-headed -> the 'and' IS a clause boundary -> TWO steps
    assert two["n_steps"] == 2, _binds(agent, two)
    assert _binds(agent, two) == ["warm", "measure_timing"]
    # right side NOT verb-headed ('which …') -> the 'and' is NOT a boundary -> ONE step
    assert one["n_steps"] == 1, _binds(agent, one)
    assert _binds(agent, one) == ["report"]
    # the discriminator IS the verb-head Term
    assert ir.is_verb_headed("warm up wordnet") and ir.is_verb_headed("measure the timing")
    assert not ir.is_verb_headed("which gaps were fixed")


# ===========================================================================
# 6. NO REGRESSION: the existing 3-sentence / data-driven plans still parse.
# ===========================================================================
def test_no_regression_existing_plans(agent, op):
    p1 = _quiet(op.parse_instruction, agent,
                "Do a bulk load of Wikipedia. Identify if it is sufficiently fast. "
                "Identify if there are other gaps.")
    assert _binds(agent, p1)[:3] == ["bulk_load", "judge_sufficiency", "perceive_gaps"]
    p2 = _quiet(op.parse_instruction, agent,
                "Warm up wordnet. Then measure timing. Finally summarize.")
    assert _binds(agent, p2) == ["warm", "measure_timing", "report"]

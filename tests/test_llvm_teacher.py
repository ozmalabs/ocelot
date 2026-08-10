"""LLVM teacher — static LLVM IR knowledge in the impasse-resolver chain.

In-memory hash lookups; no external corpus to install. Tests cover the
lookup table, alias routing, payload shape, the callable's hit/miss
behaviour, fallback chaining, and that the payloads install the right
Microtheory + binding_pattern when the agent absorbs them.
"""
from __future__ import annotations

import pytest

from domains.llvm_teacher import (
    LLVMTeacher, LLVMEntry, entry_to_answer, entry_to_payload, lookup,
    _ENTRIES, _ALIASES,
)


# ---------------------------------------------------------------------------
# lookup
# ---------------------------------------------------------------------------

def test_lookup_finds_structural_concept():
    e = lookup("llvm function")
    assert e is not None
    assert e.phrase == "llvm function"
    assert "named code unit" in e.description.lower()


def test_lookup_finds_instruction():
    e = lookup("add")
    assert e is not None
    assert e.binding_pattern == "function_of_two_subjects"
    assert "integer addition" in e.description.lower()


def test_lookup_via_alias_canonicalises():
    # gep is the standard abbreviation; should route to getelementptr
    e = lookup("gep")
    assert e is not None
    assert e.phrase == "getelementptr"


def test_lookup_via_type_alias():
    # i32 / i64 / iN all route to integer type
    assert lookup("i32").phrase == "integer type"
    assert lookup("i64").phrase == "integer type"
    assert lookup("iN").phrase == "integer type"


def test_lookup_via_concept_alias():
    assert lookup("undefined value").phrase == "poison value"
    assert lookup("ssa form").phrase == "ssa"
    assert lookup("dominance").phrase == "dominator"


def test_lookup_case_insensitive():
    assert lookup("LLVM IR").phrase == "llvm ir"
    assert lookup("Llvm Function").phrase == "llvm function"
    assert lookup("PHI").phrase == "phi"


def test_lookup_strips_whitespace():
    assert lookup("  add  ").phrase == "add"
    assert lookup("\tphi\n").phrase == "phi"


def test_lookup_miss_returns_none():
    assert lookup("nonexistent llvm thing") is None
    assert lookup("quantum supercomputer") is None


def test_all_aliases_route_to_real_entries():
    canonical_phrases = {e.phrase for e in _ENTRIES}
    orphans = [target for target in _ALIASES.values()
               if target not in canonical_phrases]
    assert orphans == [], f"orphan alias targets: {orphans}"


def test_no_duplicate_canonical_phrases():
    phrases = [e.phrase for e in _ENTRIES]
    assert len(phrases) == len(set(phrases)), \
        "duplicate canonical phrases in _ENTRIES"


def test_phase_1_coverage_threshold():
    # The LLVM_LEARNING.md curriculum projects ~50 phrases for Phase 1.
    # We've established a comfortable margin above that. Bumping this
    # threshold as the table grows would prevent silent shrinkage.
    assert len(_ENTRIES) >= 50
    assert len(_ALIASES) >= 60


def test_phase_2_instruction_set_coverage():
    """Phase 2 of the LLVM_LEARNING.md curriculum is the full instruction
    set. Verify the categories from LangRef are represented."""
    canonical = {e.phrase for e in _ENTRIES}
    # Arithmetic — integer
    for op in ["add", "sub", "mul", "udiv", "sdiv", "urem", "srem"]:
        assert op in canonical, f"missing arithmetic op: {op}"
    # Arithmetic — floating point
    for op in ["fneg", "fadd", "fsub", "fmul", "fdiv", "frem"]:
        assert op in canonical, f"missing fp arithmetic op: {op}"
    # Bitwise
    for op in ["and", "or", "xor", "shl", "lshr", "ashr"]:
        assert op in canonical, f"missing bitwise op: {op}"
    # Comparison
    for op in ["icmp", "fcmp"]:
        assert op in canonical, f"missing comparison op: {op}"
    # Memory
    for op in ["alloca", "load", "store", "getelementptr"]:
        assert op in canonical, f"missing memory op: {op}"
    # Atomic memory
    for op in ["atomicrmw", "cmpxchg", "fence", "memory ordering"]:
        assert op in canonical, f"missing atomic op: {op}"
    # Conversion
    for op in ["trunc", "zext", "sext", "bitcast", "ptrtoint", "inttoptr",
               "sitofp", "uitofp", "fptosi", "fptoui",
               "fptrunc", "fpext", "addrspacecast"]:
        assert op in canonical, f"missing conversion op: {op}"
    # Control flow
    for op in ["br", "switch", "ret", "unreachable", "invoke",
               "indirectbr", "callbr", "resume"]:
        assert op in canonical, f"missing control flow op: {op}"
    # Aggregate
    for op in ["extractvalue", "insertvalue"]:
        assert op in canonical, f"missing aggregate op: {op}"
    # Vector
    for op in ["extractelement", "insertelement", "shufflevector"]:
        assert op in canonical, f"missing vector op: {op}"
    # Other
    for op in ["phi", "select", "call", "freeze"]:
        assert op in canonical, f"missing other op: {op}"
    # Exception handling (Windows SEH + Itanium ABI)
    for op in ["landingpad", "catchpad", "cleanuppad", "catchret",
               "cleanupret"]:
        assert op in canonical, f"missing exception op: {op}"


# ---------------------------------------------------------------------------
# entry → answer / payload
# ---------------------------------------------------------------------------

def test_entry_to_answer_returns_description():
    e = lookup("phi")
    a = entry_to_answer(e)
    assert "SSA merge" in a or "ssa" in a.lower()
    # Not a stringified object
    assert "LLVMEntry" not in a


def test_entry_to_payload_shape():
    e = lookup("llvm function")
    p = entry_to_payload(e, subject="llvm function")
    assert set(p.keys()) == {"answer", "learn"}
    assert isinstance(p["learn"], list)
    assert len(p["learn"]) == 1


def test_entry_to_payload_lands_in_llvm_ir_microtheory():
    e = lookup("add")
    p = entry_to_payload(e, subject="add")
    entry = p["learn"][0]
    assert entry["microtheory"] == "llvm_ir"
    assert entry["genl_mt"] == "compiler_ir"
    assert entry["source"] == "llvm_langref"


def test_entry_to_payload_preserves_binding_pattern():
    # Structural concept → predicate_of_subject
    p_fn = entry_to_payload(lookup("llvm function"), subject="llvm function")
    assert p_fn["learn"][0]["binding_pattern"] == "predicate_of_subject"
    # Binary op → function_of_two_subjects
    p_add = entry_to_payload(lookup("add"), subject="add")
    assert p_add["learn"][0]["binding_pattern"] == "function_of_two_subjects"
    # Unary op → function_of_subject
    p_trunc = entry_to_payload(lookup("trunc"), subject="trunc")
    assert p_trunc["learn"][0]["binding_pattern"] == "function_of_subject"


# ---------------------------------------------------------------------------
# teacher callable
# ---------------------------------------------------------------------------

def test_teacher_hits_known_concept():
    t = LLVMTeacher()
    p = t("what is an llvm function")
    assert p is not None
    assert "named code unit" in p["answer"].lower()
    assert t.hits == 1
    assert t.misses == 0


def test_teacher_strips_interrogative_prefixes():
    t = LLVMTeacher()
    # extract_subject (shared with wiki_teacher) drops the leading "what is"
    p = t("what is the phi instruction")
    assert p is not None
    assert "ssa merge" in p["answer"].lower() or "predecessor" in p["answer"].lower()


def test_teacher_strips_trailing_punctuation():
    t = LLVMTeacher()
    p = t("describe getelementptr.")
    assert p is not None
    assert "pointer" in p["answer"].lower() or "address" in p["answer"].lower()


def test_teacher_recognises_aliases_in_question():
    t = LLVMTeacher()
    p = t("what is gep")
    assert p is not None
    # gep → getelementptr
    assert "address" in p["answer"].lower() or "navigate" in p["answer"].lower()


def test_teacher_miss_returns_none():
    t = LLVMTeacher()
    p = t("what is quantum entanglement")
    assert p is None
    assert t.misses == 1


def test_teacher_falls_through_to_fallback_on_miss():
    fallback_called: list[str] = []

    def fb(q):
        fallback_called.append(q)
        return {"answer": "llm answer", "learn": []}

    t = LLVMTeacher(fallback=fb)
    p = t("what is quantum entanglement")
    assert p == {"answer": "llm answer", "learn": []}
    assert fallback_called == ["what is quantum entanglement"]


def test_teacher_does_not_call_fallback_on_hit():
    fallback_calls: list[str] = []
    t = LLVMTeacher(fallback=lambda q: fallback_calls.append(q))
    p = t("what is llvm ir")
    assert p is not None
    assert fallback_calls == []


def test_teacher_tracks_last_subject_and_entry():
    t = LLVMTeacher()
    t("what is the load instruction")
    assert t.last_subject is not None
    assert "load" in t.last_subject.lower()
    assert t.last_entry is not None
    assert t.last_entry.phrase == "load"
